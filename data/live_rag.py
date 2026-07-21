"""Persistent RAG cache over LIVE search results - "learn from every search".

Upgrade of the earlier throwaway-per-search index into a PERSISTENT vector store
that accumulates results across searches so future similar searches are served
from the cache instead of re-hitting the paid live API.

Per specialist search:
  1. embed the traveler's need,
  2. look in the persistent vector DB FIRST, filtered to the destination:
       - CACHE HIT  -> return the semantically closest cached results, NO API call
         (saves the Google/SearchApi call + the repeat tool-loop overhead),
       - CACHE MISS -> call the live API, WRITE the new results into the cache
         (so the next similar search is a hit), and return them.
  3. either way, ranking is done by vector similarity to the need.

Concepts on display for the capstone: embeddings (chromadb's default model),
a vector database (persistent chroma collection per domain), retrieval
(similarity query with a metadata filter), and a concrete cache hit/miss +
API-call-saved counter.

Honest note on "token spend": the biggest saving is fewer paid API calls and
avoided repeat tool loops; the specialist still receives the retrieved results
as context, so per-search LLM tokens are similar. Everything degrades
gracefully - if chromadb can't load, every search is a live call with no cache.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional

from data import live_places

logger = logging.getLogger(__name__)

# domain -> (Places includedType, human noun used to build the query)
_DOMAIN_QUERY = {
    "hotels": ("lodging", "hotels"),
    "restaurants": ("restaurant", "restaurants"),
    "attractions": ("tourist_attraction", "tourist attractions and things to do"),
    "shops": ("shopping_mall", "shopping and markets"),
    "transport": (None, "local transport options, car rental and transit"),
}

# A city needs at least this many cached records before we trust the cache to
# serve that city without a fresh API call.
_MIN_CACHE_HIT = 4
_CACHE_PATH = os.getenv("RAG_CACHE_PATH", ".chroma_cache")

_client = None
_client_failed = False
_stats = {"hits": 0, "misses": 0, "api_calls_saved": 0}


def _get_client():
    """Persistent chroma client (survives restarts); falls back to ephemeral,
    then to None (caching disabled) so the app always works."""
    global _client, _client_failed
    if _client is not None or _client_failed:
        return _client
    try:
        import chromadb
        try:
            _client = chromadb.PersistentClient(path=_CACHE_PATH)
        except Exception:
            _client = chromadb.EphemeralClient()
    except Exception as e:
        logger.warning(f"RAG cache unavailable ({e}); every search will be a live call.")
        _client_failed = True
        _client = None
    return _client


def _collection(domain: str):
    client = _get_client()
    if client is None:
        return None
    try:
        return client.get_or_create_collection(name=f"cache_{domain}")
    except Exception as e:
        logger.debug(f"cache collection error for {domain}: {e}")
        return None


def _document(p: Dict[str, Any]) -> str:
    parts: List[str] = [p.get("name") or ""]
    for k in ("summary", "address", "price_level"):
        if p.get(k):
            parts.append(str(p[k]))
    if p.get("types"):
        parts.append(", ".join(p["types"]))
    if p.get("rating"):
        parts.append(f"rated {p['rating']} from {p.get('num_ratings')} reviews")
    for r in p.get("reviews", []):
        if r.get("text"):
            parts.append(str(r["text"]))
    return ". ".join(x for x in parts if x)


def _city_cached_count(collection, city_key: str) -> int:
    try:
        got = collection.get(where={"city": city_key})
        return len(got.get("ids") or [])
    except Exception:
        return 0


def _query_cache(collection, city_key: str, need_text: str, n: int) -> List[Dict[str, Any]]:
    try:
        res = collection.query(
            query_texts=[need_text],
            n_results=n,
            where={"city": city_key},
        )
        metadatas = (res.get("metadatas") or [[]])[0]
        out = []
        for md in metadatas:
            pj = (md or {}).get("place_json")
            if pj:
                try:
                    out.append(json.loads(pj))
                except Exception:
                    continue
        return out
    except Exception as e:
        logger.debug(f"cache query error: {e}")
        return []


def _add_to_cache(collection, domain: str, city_key: str, places: List[Dict[str, Any]]) -> None:
    try:
        ids, docs, metas = [], [], []
        for p in places:
            pid = p.get("id")
            if not pid:
                continue
            ids.append(pid)
            docs.append(_document(p))
            metas.append({"city": city_key, "domain": domain, "place_json": json.dumps(p)})
        if ids:
            collection.upsert(ids=ids, documents=docs, metadatas=metas)
    except Exception as e:
        logger.debug(f"cache add error: {e}")


def search(domain: str, destination: str, need: str = "", n_results: int = 5) -> Dict[str, Any]:
    """Live-grounded search with a persistent RAG cache in front of the API.

    Returns {"success", "message", "results", "source": "cache"|"live", "reason"?}.
    """
    if not destination or not destination.strip():
        return {"success": False, "message": "No destination is set yet - ask the traveler where they're going.", "results": [], "source": "none"}

    included_type, noun = _DOMAIN_QUERY.get(domain, (None, domain))
    city_key = destination.strip().title()
    need_text = need.strip() or f"{noun} in {city_key}"
    collection = _collection(domain)

    # 1) CACHE FIRST
    if collection is not None and _city_cached_count(collection, city_key) >= _MIN_CACHE_HIT:
        cached = _query_cache(collection, city_key, need_text, n_results)
        if cached:
            _stats["hits"] += 1
            _stats["api_calls_saved"] += 1
            return {
                "success": True,
                "source": "cache",
                "message": (
                    f"Found {len(cached)} verified {domain} result(s) for {city_key} from the "
                    f"RAG cache (no API call needed - retrieved by semantic similarity)."
                ),
                "results": cached,
            }

    # 2) CACHE MISS -> live API
    fetched = live_places.text_search(need_text, included_type=included_type, max_results=15)
    if not fetched.get("ok"):
        reason = fetched.get("reason", "unknown error")
        return {
            "success": False,
            "source": "live",
            "reason": reason,
            "message": (
                f"I couldn't fetch verified {domain} data for {city_key} right now ({reason}). "
                f"Tell the traveler plainly you can't show verified results at the moment - do "
                f"NOT answer from general knowledge."
            ),
            "results": [],
        }
    places = fetched.get("places") or []
    if not places:
        return {
            "success": False,
            "source": "live",
            "message": (
                f"Google Places returned no {domain} results for {city_key}. Tell the traveler "
                f"plainly there were no verified matches - do NOT invent options."
            ),
            "results": [],
        }

    _stats["misses"] += 1
    if collection is not None:
        _add_to_cache(collection, domain, city_key, places)
        ranked = _query_cache(collection, city_key, need_text, n_results) or places[:n_results]
    else:
        ranked = places[:n_results]

    return {
        "success": True,
        "source": "live",
        "message": (
            f"Found {len(ranked)} verified {domain} result(s) for {city_key} live via Google "
            f"Places (cached now, so the next similar search won't need an API call)."
        ),
        "results": ranked,
    }


def get_cache_stats() -> Dict[str, Any]:
    """Hit/miss counters + per-domain cached-record counts, for the UI panel."""
    per_domain = {}
    total_cached = 0
    for domain in _DOMAIN_QUERY:
        col = _collection(domain)
        if col is None:
            continue
        try:
            c = col.count()
        except Exception:
            c = 0
        per_domain[domain] = c
        total_cached += c
    hits = _stats["hits"]
    misses = _stats["misses"]
    total = hits + misses
    return {
        "hits": hits,
        "misses": misses,
        "api_calls_saved": _stats["api_calls_saved"],
        "hit_rate": round(hits / total, 2) if total else 0.0,
        "total_cached_records": total_cached,
        "cached_by_domain": per_domain,
        "cache_enabled": _get_client() is not None,
    }

"""RAG over LIVE Google Places results - "build RAG with each search".

Flow, per specialist search:
  1. fetch real results from Google Places (data/live_places.py) for the
     destination + domain (+ the traveler's specific need as the query text),
  2. build a fresh, throwaway vector index over JUST those live results,
  3. semantically retrieve the top-k against the traveler's need, so the ordering
     reflects the nuance of what they asked for (e.g. "quiet romantic beachfront")
     rather than only Google's default ranking,
  4. return grounded, real results the specialist presents as verified.

This replaces the old static mock dataset + prebuilt mock index. Coverage is now
"whatever Google Places has" - i.e. effectively any destination - so the honesty
rule shifts from "is this city in our tiny DB?" to "did the live search actually
return results?". If it didn't (bad/absent key, quota, network, or genuinely no
matches), callers get success=False with a plain reason and must tell the traveler
they couldn't fetch verified data - never fill the gap from general knowledge.

The vector step degrades gracefully: if chromadb/its embedding model can't load,
we simply return Google's own ranking (still real, still grounded) instead of
failing. So the app works with or without the embedding layer.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from data import live_places

logger = logging.getLogger(__name__)

# domain -> (Places includedType, human noun used to build the query).
# Transport is intentionally weak here: Google Places covers local venues
# (stations, car rental) but NOT intercity flights/trains - see note in
# safar's tool. A dedicated flights API (Amadeus/SerpApi) is a follow-up.
_DOMAIN_QUERY = {
    "hotels": ("lodging", "hotels"),
    "restaurants": ("restaurant", "restaurants"),
    "attractions": ("tourist_attraction", "tourist attractions and things to do"),
    "shops": ("shopping_mall", "shopping and markets"),
    "transport": (None, "local transport options, car rental and transit"),
}

_chroma_client = None


def _get_chroma():
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        _chroma_client = chromadb.EphemeralClient()
    return _chroma_client


def _document(p: Dict[str, Any]) -> str:
    """Text blob embedded for one place (name + summary + types + reviews...)."""
    parts: List[str] = [p.get("name") or ""]
    if p.get("summary"):
        parts.append(str(p["summary"]))
    if p.get("types"):
        parts.append(", ".join(p["types"]))
    if p.get("address"):
        parts.append(str(p["address"]))
    if p.get("price_level"):
        parts.append(f"price {p['price_level']}")
    if p.get("rating"):
        parts.append(f"rated {p['rating']} from {p.get('num_ratings')} reviews")
    for r in p.get("reviews", []):
        if r.get("text"):
            parts.append(str(r["text"]))
    return ". ".join(x for x in parts if x)


def _rerank(places: List[Dict[str, Any]], need: str, n_results: int) -> List[Dict[str, Any]]:
    """Vector re-rank live results against the traveler's need. Falls back to
    the API's own order if the embedding layer is unavailable or anything fails.
    """
    if not need or not need.strip() or len(places) <= 1:
        return places[:n_results]
    keyed = {p["id"]: p for p in places if p.get("id")}
    if not keyed:
        return places[:n_results]
    collection = None
    client = None
    name = f"live_{uuid.uuid4().hex}"
    try:
        client = _get_chroma()
        collection = client.create_collection(name=name)
        collection.add(
            ids=list(keyed.keys()),
            documents=[_document(keyed[i]) for i in keyed],
        )
        res = collection.query(query_texts=[need], n_results=min(n_results, len(keyed)))
        ordered_ids = (res.get("ids") or [[]])[0]
        ranked = [keyed[i] for i in ordered_ids if i in keyed]
        # Append any not returned by the query (safety) up to n_results.
        for i in keyed:
            if keyed[i] not in ranked:
                ranked.append(keyed[i])
        return ranked[:n_results]
    except Exception as e:
        logger.debug(f"live RAG re-rank unavailable, using API order: {e}")
        return places[:n_results]
    finally:
        # Keep the ephemeral client from accumulating one collection per search.
        if client is not None:
            try:
                client.delete_collection(name=name)
            except Exception:
                pass


def search(
    domain: str,
    destination: str,
    need: str = "",
    n_results: int = 5,
) -> Dict[str, Any]:
    """Live-grounded search for one specialist.

    Args:
      domain: one of hotels/restaurants/attractions/shops/transport
      destination: city/place the traveler is going to
      need: the traveler's specific ask (vibe, cuisine, budget words, etc.) -
            used both in the Places query and as the vector re-rank query
      n_results: how many grounded results to return

    Returns {"success": bool, "message": str, "results": [places], "reason": str?}.
    """
    if not destination or not destination.strip():
        return {"success": False, "message": "No destination is set yet - ask the traveler where they're going.", "results": []}

    included_type, noun = _DOMAIN_QUERY.get(domain, (None, domain))
    query = " ".join(x for x in [need.strip(), noun, "in", destination.strip()] if x).strip()

    fetched = live_places.text_search(query, included_type=included_type, max_results=15)
    if not fetched.get("ok"):
        reason = fetched.get("reason", "unknown error")
        return {
            "success": False,
            "reason": reason,
            "message": (
                f"I couldn't fetch verified {domain} data for {destination} right now "
                f"({reason}). Tell the traveler plainly you can't show verified results at "
                f"the moment - do NOT answer from general knowledge."
            ),
            "results": [],
        }

    places = fetched.get("places") or []
    if not places:
        return {
            "success": False,
            "message": (
                f"Google Places returned no {domain} results for {destination}. Tell the "
                f"traveler plainly there were no verified matches - do NOT invent options."
            ),
            "results": [],
        }

    results = _rerank(places, need, n_results)
    return {
        "success": True,
        "message": f"Found {len(results)} verified {domain} result(s) for {destination} via Google Places.",
        "results": results,
    }

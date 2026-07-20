"""Vector-search (RAG) layer over TRAVAS's mock travel datasets.

Adds semantic retrieval on top of the existing exact-filter tools, closing
part of the architecture gap where specialist search was structured-filter
only (city + numeric thresholds) - a query like "romantic beachside dinner"
could previously only be answered by literal keyword luck, not meaning.

Uses a local, in-memory (ephemeral) chromadb client with its bundled default
embedding model - no external embeddings API/key required. Indexes are
built once per process from the small, static mock datasets and never
persisted to disk; rebuilding on every process start is fine at this
dataset size.

HONESTY BOUNDARY: this does NOT expand what TRAVAS actually has data for.
The mock datasets are still tiny and mostly Goa-only:
  - hotels: Delhi, Mumbai, Goa (2 each)
  - restaurants / attractions / shops: Goa only
  - transport: Delhi<->Goa flights and trains only
Semantic search only changes HOW a covered record is found (by meaning,
not just exact filters) - not WHICH destinations are covered. Metadata
filtering (city / route) still determines "covered vs not," and reliably
returns zero hits for anything outside the dataset - callers must treat an
empty result as "not covered" and say so, not retry unfiltered (nearest-
neighbor search always returns SOME record unless narrowed by an exact
filter, which would surface an irrelevant city's data as if it mattered).

Degrades gracefully: if chromadb/its embedding model can't be loaded in a
given environment (offline, memory-constrained, etc.), every function here
returns empty/False rather than raising, and callers fall back to the
original exact-filter tools.
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_chroma_client = None
_collections: Dict[str, Any] = {}
_indexed: Dict[str, bool] = {}


def _get_client():
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        _chroma_client = chromadb.EphemeralClient()
    return _chroma_client


def _enum_val(x) -> str:
    return x.value if hasattr(x, "value") else str(x)


# ----------------------------------------------------------------------
# Per-domain document builders (what gets embedded) and metadata builders
# (what gets used for exact filtering, e.g. by city)
# ----------------------------------------------------------------------

def _hotel_document(h) -> str:
    amenities = ", ".join(_enum_val(a) for a in h.amenities)
    return (
        f"{h.name} in {h.location}, {h.city}. {h.description} "
        f"Star rating {h.star_rating}. Amenities: {amenities}. "
        f"Price range INR {h.price_range.get('min')}-{h.price_range.get('max')} per night."
    )


def _restaurant_document(r) -> str:
    cuisines = ", ".join(_enum_val(c) for c in getattr(r, "cuisine_types", []))
    dishes = ", ".join(getattr(r, "special_dishes", []))
    dietary = ", ".join(getattr(r, "dietary_options", []))
    return (
        f"{r.name} in {r.locality}, {r.city}. {_enum_val(r.restaurant_type)} restaurant "
        f"serving {cuisines}. Known for: {dishes}. Dietary options: {dietary}. "
        f"Average cost per person INR {r.avg_cost_per_person} ({r.price_range})."
    )


def _attraction_document(a) -> str:
    highlights = ", ".join(getattr(a, "highlights", []))
    activities = ", ".join(getattr(a, "activities_available", []))
    return (
        f"{a.name} in {a.locality}, {a.city}. {a.description} Type: {_enum_val(a.attraction_type)}. "
        f"Highlights: {highlights}. Activities: {activities}. "
        f"Entry fee INR {a.entry_fee}. Best time: {a.best_time_to_visit}."
    )


def _journey_document(j) -> str:
    return (
        f"{j.operator_name} {_enum_val(j.transport_type)} from {j.departure_city} to "
        f"{j.arrival_city}, departing {j.departure_time} arriving {j.arrival_time}. "
        f"Comfort: {_enum_val(j.comfort_level)}. Price INR {j.price_per_person} per person."
    )


def _shop_document(s) -> str:
    return (
        f"{s.name} in {s.locality}, {s.city}. {_enum_val(s.shop_type)}. Rating {s.rating}. "
        f"Bargaining possible: {s.bargaining_possible}. Best time to visit: {s.best_time_to_visit}."
    )


# ----------------------------------------------------------------------
# Per-domain record loaders - the mock datasets are structured
# inconsistently (dict-of-city-lists for hotels/restaurants/attractions/
# shops, but flights/trains/local_transport nested separately for
# transport), so each domain gets its own small flattening function.
# ----------------------------------------------------------------------

def _load_hotel_records() -> List[Any]:
    from data.mock_hotels import get_mock_hotels
    records = []
    for _city, items in get_mock_hotels().items():
        records.extend(items)
    return records


def _load_restaurant_records() -> List[Any]:
    from data.mock_restaurants import create_mock_restaurants
    records = []
    for _city, items in create_mock_restaurants().items():
        records.extend(items)
    return records


def _load_attraction_records() -> List[Any]:
    from data.mock_attractions import create_mock_attractions
    records = []
    for _city, items in create_mock_attractions().items():
        records.extend(items)
    return records


def _load_shop_records() -> List[Any]:
    from data.mock_shops import create_mock_shops
    records = []
    for _city, items in create_mock_shops().items():
        records.extend(items)
    return records


def _load_transport_records() -> List[Any]:
    """Flights + trains only (Journey objects, all sharing one schema).
    LocalTransport is a different dataclass and isn't indexed here - Safar's
    search_local_transport tool stays exact-filter only."""
    from data.mock_transport import create_mock_journeys
    db = create_mock_journeys()
    records = []
    for route_list in db.get("flights", {}).values():
        records.extend(route_list)
    for route_list in db.get("trains", {}).values():
        records.extend(route_list)
    return records


_DOMAIN_CONFIG = {
    "hotels": {
        "loader": _load_hotel_records,
        "doc_fn": _hotel_document,
        "meta_fn": lambda h: {"city": h.city},
    },
    "restaurants": {
        "loader": _load_restaurant_records,
        "doc_fn": _restaurant_document,
        "meta_fn": lambda r: {"city": r.city},
    },
    "attractions": {
        "loader": _load_attraction_records,
        "doc_fn": _attraction_document,
        "meta_fn": lambda a: {"city": a.city},
    },
    "shops": {
        "loader": _load_shop_records,
        "doc_fn": _shop_document,
        "meta_fn": lambda s: {"city": s.city},
    },
    "transport": {
        "loader": _load_transport_records,
        "doc_fn": _journey_document,
        "meta_fn": lambda j: {"departure_city": j.departure_city, "arrival_city": j.arrival_city},
    },
}


def get_covered_cities(domain: str) -> set:
    """Cities this domain actually has verified data for, derived directly from
    the mock datasets.

    Deliberately does NOT touch chromadb (only the plain record loaders), so it
    works even where the vector layer is unavailable. Used for a deterministic
    coverage pre-check: every specialist can flag an out-of-dataset destination
    the same way and UP FRONT, instead of one specialist gathering preferences
    or citing general-knowledge specifics before discovering the gap only after
    a search returns zero.

    For city-keyed domains (hotels/restaurants/attractions/shops) this is the
    set of record cities. For transport it's the set of departure+arrival cities
    seen across journeys (route-level nuance still handled by the search itself).
    Returns an empty set on any error (callers then simply skip the pre-check).
    """
    config = _DOMAIN_CONFIG.get(domain)
    if not config:
        return set()
    cities = set()
    try:
        for rec in config["loader"]():
            for val in config["meta_fn"](rec).values():
                if val:
                    cities.add(str(val).strip().title())
    except Exception as e:
        logger.debug(f"get_covered_cities({domain}) failed: {str(e)}")
        return set()
    return cities


def ensure_indexed(domain: str) -> bool:
    """Build the vector index for a domain the first time it's needed.

    Returns True if the index is ready to query, False if indexing failed
    or there's nothing to index - callers must fall back to exact-filter
    search in that case rather than crash.
    """
    if _indexed.get(domain):
        return True
    config = _DOMAIN_CONFIG.get(domain)
    if not config:
        return False
    try:
        records = config["loader"]()
        if not records:
            return False
        client = _get_client()
        collection = client.get_or_create_collection(name=domain)
        ids, documents, metadatas = [], [], []
        for rec in records:
            rid = getattr(rec, "id", None)
            if not rid:
                continue
            ids.append(rid)
            documents.append(config["doc_fn"](rec))
            metadatas.append(config["meta_fn"](rec))
        if not ids:
            return False
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        _collections[domain] = collection
        _indexed[domain] = True
        logger.info(f"Indexed {len(ids)} '{domain}' records for semantic search")
        return True
    except Exception as e:
        logger.warning(
            f"Vector index unavailable for '{domain}' ({str(e)}) - "
            "falling back to exact-filter search only"
        )
        return False


def semantic_search(
    domain: str, query: str, n_results: int = 5, where: Optional[dict] = None
) -> List[Dict[str, Any]]:
    """Semantic similarity search within a domain, optionally filtered by
    exact metadata (e.g. {"city": "Goa"}).

    Returns [] if the index isn't available OR the metadata filter matches
    nothing. Callers should treat an empty list as "not covered" and say so
    plainly - see the module docstring's HONESTY BOUNDARY note for why
    retrying without the filter would be wrong (nearest-neighbor search
    always returns *something* unless narrowed by an exact filter).
    """
    if not ensure_indexed(domain):
        return []
    try:
        collection = _collections[domain]
        count = collection.count()
        if count == 0:
            return []
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, count),
            where=where,
        )
        out = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        for i in range(len(ids)):
            out.append({
                "id": ids[i],
                "document": docs[i],
                "metadata": metas[i],
                "distance": dists[i],
            })
        return out
    except Exception as e:
        logger.warning(f"Semantic search failed for domain '{domain}': {str(e)}")
        return []


def get_record_by_id(domain: str, record_id: str) -> Optional[Any]:
    """Look up the full dataclass object behind a semantic search hit id."""
    config = _DOMAIN_CONFIG.get(domain)
    if not config:
        return None
    try:
        for rec in config["loader"]():
            if getattr(rec, "id", None) == record_id:
                return rec
    except Exception as e:
        logger.warning(f"get_record_by_id failed for domain '{domain}': {str(e)}")
    return None

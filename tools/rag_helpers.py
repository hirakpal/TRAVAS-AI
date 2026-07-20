"""Shared execution/formatting helper for the semantic-search tools across
all 5 specialist domains, so each tools/X_tools.py file only needs a thin
wrapper (domain name + a small per-record formatter) instead of duplicating
the retrieval and "not covered" fallback-messaging logic five times.
"""
from typing import Any, Callable, Dict, Optional

from data.rag_index import semantic_search, get_record_by_id


def run_semantic_search(
    domain: str,
    query: str,
    where: Optional[dict],
    coverage_label: str,
    n_results: int,
    formatter: Callable[[Any, Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    """Run a semantic search and format results, or return an honest
    "not covered" message if nothing matches the metadata filter.

    An empty result here reliably means the destination/route isn't in
    TRAVAS's mock dataset (see data/rag_index.py's semantic_search()
    docstring for why) - the message is written so the calling agent's
    system prompt can lean on it directly rather than improvising.
    """
    hits = semantic_search(domain, query, n_results=n_results, where=where)
    if not hits:
        return {
            "success": False,
            "message": (
                f"No semantic matches for '{query}' in {coverage_label}. This means "
                f"{coverage_label} is not in TRAVAS's current verified {domain} dataset - "
                f"tell the user plainly that you don't have verified data for it, rather than "
                f"answering from general knowledge."
            ),
            "results": [],
        }

    results = []
    for hit in hits:
        record = get_record_by_id(domain, hit["id"])
        if record is None:
            continue
        results.append(formatter(record, hit))

    return {
        "success": True,
        "message": f"Found {len(results)} semantically relevant result(s) for '{query}' in {coverage_label}",
        "results": results,
    }

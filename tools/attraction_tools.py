"""Attraction tools for Yatra - now backed by LIVE Google Places (New) + RAG.

Replaces the old mock-attraction dataset (Goa only). Tool names unchanged so the
agent prompt and has_ever_searched trigger keep working.
"""

from typing import List, Dict, Any

from data import live_rag, live_places


class SearchAttractionsTool:
    name = "search_attractions"
    description = (
        "Search for real tourist attractions / things to do in a destination via Google "
        "Places. Pass the destination and (optionally) the traveler's interests as free "
        "text (nature, history, adventure, family, etc.) - results are grounded in live "
        "verified data and ranked to match."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Destination city/place (required)"},
            "query": {
                "type": "string",
                "description": "Interests as free text, e.g. 'family-friendly, gardens and viewpoints'. Optional.",
            },
        },
        "required": ["city"],
    }

    @staticmethod
    def execute(city: str, query: str = "", **_) -> Dict[str, Any]:
        result = live_rag.search("attractions", city, need=query or "")
        return {**result, "attractions": result.get("results", [])}


class GetAttractionDetailsTool:
    name = "get_attraction_details"
    description = "Get full details (hours, contact, reviews, rating) for one attraction by its Google Places id."
    input_schema = {
        "type": "object",
        "properties": {"place_id": {"type": "string", "description": "Google Places id from a prior search result"}},
        "required": ["place_id"],
    }

    @staticmethod
    def execute(place_id: str, **_) -> Dict[str, Any]:
        res = live_places.place_details(place_id)
        if not res.get("ok"):
            return {"success": False, "message": res.get("reason", "not found")}
        return {"success": True, "attraction": res.get("place")}


ATTRACTION_TOOLS = {
    "search_attractions": SearchAttractionsTool,
    "get_attraction_details": GetAttractionDetailsTool,
}


def list_tools() -> List[str]:
    return list(ATTRACTION_TOOLS.keys())

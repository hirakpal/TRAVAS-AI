"""Shopping tools for Bazaar - now backed by LIVE Google Places (New) + RAG.

Replaces the old mock-shops dataset (Goa only). Tool names unchanged so the agent
prompt and has_ever_searched trigger keep working.
"""

from typing import List, Dict, Any

from data import live_rag, live_places


class SearchShopsTool:
    name = "search_shops"
    description = (
        "Search for real shopping - malls, markets, boutiques - in a destination via "
        "Google Places. Pass the destination and (optionally) what the traveler wants to "
        "buy or the vibe as free text (handicrafts, luxury, street market, etc.). Results "
        "are grounded in live verified data and ranked to match."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Destination city/place (required)"},
            "query": {
                "type": "string",
                "description": "What they want to buy / the vibe, e.g. 'local handicraft markets, bargaining'. Optional.",
            },
        },
        "required": ["city"],
    }

    @staticmethod
    def execute(city: str, query: str = "", **_) -> Dict[str, Any]:
        result = live_rag.search("shops", city, need=query or "")
        return {**result, "shops": result.get("results", [])}


class GetShopDetailsTool:
    name = "get_shop_details"
    description = "Get full details (hours, contact, reviews, rating) for one shop by its Google Places id."
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
        return {"success": True, "shop": res.get("place")}


SHOPPING_TOOLS = {
    "search_shops": SearchShopsTool,
    "get_shop_details": GetShopDetailsTool,
}


def list_tools() -> List[str]:
    return list(SHOPPING_TOOLS.keys())

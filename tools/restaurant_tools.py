"""Restaurant tools for Annapurna - now backed by LIVE Google Places (New) + RAG.

Replaces the old mock-restaurant dataset (which only covered Goa). Tool names are
unchanged so the agent prompt and has_ever_searched trigger keep working.
"""

from typing import List, Dict, Any

from data import live_rag, live_places


class SearchRestaurantsTool:
    name = "search_restaurants"
    description = (
        "Search for real restaurants in a destination via Google Places. Pass the "
        "destination and (optionally) the traveler's food preferences as free text "
        "(cuisine, dietary needs, vibe, budget) - results are grounded in live verified "
        "data and ranked to match."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Destination city/place (required)"},
            "query": {
                "type": "string",
                "description": "Food preferences as free text, e.g. 'vegetarian local seafood, mid-range'. Optional.",
            },
        },
        "required": ["city"],
    }

    @staticmethod
    def execute(city: str, query: str = "", **_) -> Dict[str, Any]:
        result = live_rag.search("restaurants", city, need=query or "")
        return {**result, "restaurants": result.get("results", [])}


class GetRestaurantDetailsTool:
    name = "get_restaurant_details"
    description = "Get full details (hours, contact, reviews, rating) for one restaurant by its Google Places id."
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
        return {"success": True, "restaurant": res.get("place")}


RESTAURANT_TOOLS = {
    "search_restaurants": SearchRestaurantsTool,
    "get_restaurant_details": GetRestaurantDetailsTool,
}


def list_tools() -> List[str]:
    return list(RESTAURANT_TOOLS.keys())

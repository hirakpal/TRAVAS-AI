"""Tool definitions for hotel search and recommendations."""

import json
from typing import Any, Callable, Optional
from data.mock_hotels import search_hotels, get_hotels_by_city
from models.hotel import Hotel, HotelPreference, HotelAmenity


class HotelSearchTool:
    """Tool for searching hotels with filters"""

    name = "search_hotels"
    description = """Search for hotels in a city with optional filters.

    Returns a list of hotels matching the criteria.
    Use this to find hotels that meet user's budget and preferences."""

    input_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name (e.g., 'Delhi', 'Mumbai', 'Goa')"
            },
            "max_price": {
                "type": "number",
                "description": "Maximum price per night in INR"
            },
            "min_stars": {
                "type": "number",
                "description": "Minimum star rating (1.0-5.0)"
            }
        },
        "required": ["city"]
    }

    @staticmethod
    def execute(city: str, max_price: Optional[float] = None, min_stars: float = 0.0) -> dict:
        """Execute hotel search"""
        try:
            hotels = search_hotels(city, max_price, min_stars)

            if not hotels:
                return {
                    "success": False,
                    "message": f"No hotels found in {city} matching criteria",
                    "results": []
                }

            results = []
            for hotel in hotels:
                cheapest_room = hotel.get_cheapest_room()
                results.append({
                    "id": hotel.id,
                    "name": hotel.name,
                    "location": hotel.location,
                    "star_rating": hotel.star_rating,
                    "avg_price": cheapest_room.price_per_night if cheapest_room else "N/A",
                    "price_range": hotel.price_range,
                    "amenities": [a.value for a in hotel.amenities[:5]],  # Top 5
                    "avg_rating": round(hotel.average_rating, 1),
                    "total_reviews": hotel.total_reviews,
                })

            return {
                "success": True,
                "message": f"Found {len(results)} hotels in {city}",
                "results": results
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error searching hotels: {str(e)}",
                "results": []
            }


class GetHotelDetailsTool:
    """Tool for getting detailed information about a specific hotel"""

    name = "get_hotel_details"
    description = """Get detailed information about a specific hotel including rooms, amenities, reviews.

    Use this after finding a hotel you're interested in."""

    input_schema = {
        "type": "object",
        "properties": {
            "hotel_id": {
                "type": "string",
                "description": "Hotel ID (e.g., 'h001_taj_delhi')"
            }
        },
        "required": ["hotel_id"]
    }

    @staticmethod
    def execute(hotel_id: str) -> dict:
        """Get hotel details"""
        try:
            # Search through all cities to find the hotel
            all_cities = ["Delhi", "Mumbai", "Goa"]
            target_hotel = None

            for city in all_cities:
                hotels = get_hotels_by_city(city)
                for hotel in hotels:
                    if hotel.id == hotel_id:
                        target_hotel = hotel
                        break
                if target_hotel:
                    break

            if not target_hotel:
                return {
                    "success": False,
                    "message": f"Hotel {hotel_id} not found",
                    "details": None
                }

            # Format rooms
            rooms_info = []
            for room in target_hotel.rooms:
                rooms_info.append({
                    "type": room.type.value,
                    "price_per_night": room.price_per_night,
                    "capacity": room.capacity,
                    "available": room.available,
                    "amenities": [a.value for a in room.amenities]
                })

            # Format reviews
            reviews_info = []
            for review in target_hotel.reviews[:5]:  # Top 5 reviews
                reviews_info.append({
                    "rating": review.rating,
                    "comment": review.comment,
                    "category": review.category,
                })

            return {
                "success": True,
                "details": {
                    "id": target_hotel.id,
                    "name": target_hotel.name,
                    "city": target_hotel.city,
                    "location": target_hotel.location,
                    "description": target_hotel.description,
                    "star_rating": target_hotel.star_rating,
                    "average_rating": round(target_hotel.average_rating, 1),
                    "total_reviews": target_hotel.total_reviews,
                    "price_range": target_hotel.price_range,
                    "rooms": rooms_info,
                    "amenities": [a.value for a in target_hotel.amenities],
                    "contact": {
                        "phone": target_hotel.phone,
                        "email": target_hotel.email,
                        "website": target_hotel.website
                    },
                    "policies": {
                        "checkin": target_hotel.checkin_time,
                        "checkout": target_hotel.checkout_time,
                        "cancellation": target_hotel.cancellation_policy
                    },
                    "reviews": reviews_info
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting hotel details: {str(e)}",
                "details": None
            }


class FilterHotelsTool:
    """Tool for filtering hotels by specific preferences"""

    name = "filter_hotels"
    description = """Filter a list of hotels by specific preferences like amenities, accessibility, dietary needs.

    Use this to narrow down options based on specific requirements."""

    input_schema = {
        "type": "object",
        "properties": {
            "hotel_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of hotel IDs to filter"
            },
            "required_amenities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of required amenities (e.g., 'wifi', 'pool', 'wheelchair_access')"
            },
            "min_rating": {
                "type": "number",
                "description": "Minimum average rating (1.0-5.0)"
            },
            "family_friendly": {
                "type": "boolean",
                "description": "Filter for family-friendly hotels"
            }
        },
        "required": ["hotel_ids"]
    }

    @staticmethod
    def execute(
        hotel_ids: list,
        required_amenities: list = None,
        min_rating: float = 0.0,
        family_friendly: bool = False
    ) -> dict:
        """Filter hotels by criteria"""
        try:
            all_cities = ["Delhi", "Mumbai", "Goa"]
            filtered_results = []

            for city in all_cities:
                hotels = get_hotels_by_city(city)
                for hotel in hotels:
                    if hotel.id not in hotel_ids:
                        continue

                    # Check rating
                    if hotel.average_rating < min_rating:
                        continue

                    # Check required amenities
                    if required_amenities:
                        amenity_enums = [HotelAmenity(a) for a in required_amenities]
                        if not all(hotel.has_amenity(am) for am in amenity_enums):
                            continue

                    # Check family friendly
                    if family_friendly:
                        family_amenities = [HotelAmenity.FAMILY_ROOMS, HotelAmenity.KIDS_PLAY_AREA]
                        if not any(hotel.has_amenity(am) for am in family_amenities):
                            continue

                    filtered_results.append({
                        "id": hotel.id,
                        "name": hotel.name,
                        "location": hotel.location,
                        "star_rating": hotel.star_rating,
                        "avg_rating": round(hotel.average_rating, 1),
                        "cheapest_room": hotel.get_cheapest_room().price_per_night if hotel.get_cheapest_room() else "N/A"
                    })

            return {
                "success": True,
                "message": f"Filtered down to {len(filtered_results)} hotels",
                "results": filtered_results
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error filtering hotels: {str(e)}",
                "results": []
            }


# Tool registry
HOTEL_TOOLS = {
    "search_hotels": HotelSearchTool(),
    "get_hotel_details": GetHotelDetailsTool(),
    "filter_hotels": FilterHotelsTool(),
}


def get_tool_by_name(name: str):
    """Get tool by name"""
    return HOTEL_TOOLS.get(name)


def list_tools() -> list:
    """List all available tools"""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema
        }
        for tool in HOTEL_TOOLS.values()
    ]

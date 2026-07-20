"""Restaurant tools for Annapurna Food Agent"""

from typing import List, Dict, Any
from data.mock_restaurants import search_restaurants, get_restaurant_by_id


class SearchRestaurantsTool:
    """Search for restaurants by city and filters"""

    name = "search_restaurants"
    description = "Search for restaurants in a city with optional filters like cuisine, price range, and dietary preferences"

    input_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City to search in (e.g., 'Goa', 'Mumbai', 'Delhi')"
            },
            "cuisine": {
                "type": "string",
                "description": "Cuisine type to filter by (e.g., 'Indian', 'Seafood', 'Vegetarian', 'Italian')"
            },
            "price_range": {
                "type": "string",
                "description": "Price range: 'Budget', 'Mid-range', 'Premium', or 'Luxury'"
            },
            "min_rating": {
                "type": "number",
                "description": "Minimum rating to filter (1-5)"
            }
        },
        "required": ["city"]
    }

    @staticmethod
    def execute(
        city: str,
        cuisine: str = None,
        price_range: str = None,
        min_rating: float = 0
    ) -> Dict[str, Any]:
        """Execute restaurant search"""
        try:
            restaurants = search_restaurants(city, cuisine, price_range)

            # Filter by rating
            if min_rating > 0:
                restaurants = [r for r in restaurants if r.rating >= min_rating]

            if not restaurants:
                return {
                    "success": False,
                    "message": f"No restaurants found in {city} matching your criteria"
                }

            results = []
            for restaurant in restaurants[:5]:  # Top 5 results
                results.append({
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "locality": restaurant.locality,
                    "cuisines": [c.value for c in restaurant.cuisine_types],
                    "rating": restaurant.rating,
                    "num_reviews": restaurant.num_reviews,
                    "avg_cost_per_person": restaurant.avg_cost_per_person,
                    "price_range": restaurant.price_range,
                    "distance_km": restaurant.distance_from_city_center,
                })

            return {
                "success": True,
                "count": len(results),
                "restaurants": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class GetRestaurantDetailsTool:
    """Get detailed information about a specific restaurant"""

    name = "get_restaurant_details"
    description = "Get detailed information about a restaurant including amenities, reviews, special dishes, and dietary options"

    input_schema = {
        "type": "object",
        "properties": {
            "restaurant_id": {
                "type": "string",
                "description": "Restaurant ID to get details for"
            }
        },
        "required": ["restaurant_id"]
    }

    @staticmethod
    def execute(restaurant_id: str) -> Dict[str, Any]:
        """Execute get details"""
        try:
            restaurant = get_restaurant_by_id(restaurant_id)

            if not restaurant:
                return {
                    "success": False,
                    "message": f"Restaurant with ID {restaurant_id} not found"
                }

            return {
                "success": True,
                "restaurant": {
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "address": restaurant.address,
                    "phone": restaurant.phone,
                    "website": restaurant.website,
                    "hours": f"{restaurant.opening_time} - {restaurant.closing_time}",
                    "type": restaurant.restaurant_type.value,
                    "cuisines": [c.value for c in restaurant.cuisine_types],
                    "rating": restaurant.rating,
                    "num_reviews": restaurant.num_reviews,
                    "avg_cost_per_person": restaurant.avg_cost_per_person,
                    "price_range": restaurant.price_range,
                    "dietary_options": restaurant.dietary_options,
                    "special_dishes": restaurant.special_dishes,
                    "amenities": [a.name.value for a in restaurant.amenities if a.available],
                    "family_friendly": restaurant.is_family_friendly(),
                    "wheelchair_accessible": restaurant.is_accessible(),
                    "has_delivery": restaurant.has_delivery(),
                    "distance_from_city_center_km": restaurant.distance_from_city_center,
                    "busy_hours": restaurant.busy_hours,
                    "reviews_sample": [
                        {
                            "reviewer": r.reviewer_name,
                            "rating": r.rating,
                            "comment": r.comment,
                            "date": r.date
                        }
                        for r in restaurant.reviews[:2]
                    ]
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class FilterRestaurantsTool:
    """Filter restaurants by specific dietary and preference criteria"""

    name = "filter_restaurants"
    description = "Filter restaurants by dietary restrictions, amenities, and special requirements"

    input_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City to search in"
            },
            "dietary_restrictions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Dietary restrictions (e.g., 'Vegetarian', 'Vegan', 'Jain', 'Gluten-free')"
            },
            "family_friendly": {
                "type": "boolean",
                "description": "Must be family friendly with kids"
            },
            "wheelchair_accessible": {
                "type": "boolean",
                "description": "Must be wheelchair accessible"
            },
            "has_delivery": {
                "type": "boolean",
                "description": "Must have delivery option"
            }
        },
        "required": ["city"]
    }

    @staticmethod
    def execute(
        city: str,
        dietary_restrictions: List[str] = None,
        family_friendly: bool = False,
        wheelchair_accessible: bool = False,
        has_delivery: bool = False
    ) -> Dict[str, Any]:
        """Execute filter restaurants"""
        try:
            restaurants = search_restaurants(city)

            # Filter by dietary restrictions
            if dietary_restrictions:
                restaurants = [
                    r for r in restaurants
                    if r.matches_dietary_needs(dietary_restrictions)
                ]

            # Filter by family friendly
            if family_friendly:
                restaurants = [r for r in restaurants if r.is_family_friendly()]

            # Filter by wheelchair accessible
            if wheelchair_accessible:
                restaurants = [r for r in restaurants if r.is_accessible()]

            # Filter by delivery
            if has_delivery:
                restaurants = [r for r in restaurants if r.has_delivery()]

            if not restaurants:
                return {
                    "success": False,
                    "message": f"No restaurants found in {city} matching all criteria"
                }

            results = []
            for restaurant in restaurants[:5]:
                results.append({
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "cuisines": [c.value for c in restaurant.cuisine_types],
                    "rating": restaurant.rating,
                    "price_range": restaurant.price_range,
                    "dietary_options": restaurant.dietary_options,
                    "amenities": [a.name.value for a in restaurant.amenities if a.available],
                    "suitable_for": {
                        "family": restaurant.is_family_friendly(),
                        "wheelchair": restaurant.is_accessible(),
                        "delivery": restaurant.has_delivery()
                    }
                })

            return {
                "success": True,
                "count": len(results),
                "restaurants": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Export tools
RESTAURANT_TOOLS = {
    "search_restaurants": SearchRestaurantsTool,
    "get_restaurant_details": GetRestaurantDetailsTool,
    "filter_restaurants": FilterRestaurantsTool,
}


def list_tools() -> List[str]:
    """List available tools"""
    return list(RESTAURANT_TOOLS.keys())

"""Attraction tools for Yatra Tours Agent"""

from typing import List, Dict, Any
from data.mock_attractions import search_attractions, get_attraction_by_id


class SearchAttractionsTool:
    """Search for attractions by city and filters"""

    name = "search_attractions"
    description = "Search for attractions in a city with optional filters like type, difficulty level, and rating"

    input_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City to search in (e.g., 'Goa', 'Mumbai', 'Delhi')"
            },
            "attraction_type": {
                "type": "string",
                "description": "Type of attraction: 'Beach', 'Temple', 'Fort', 'Museum', 'Water Sports', 'Adventure', 'Nature', 'Market', 'Viewpoint', 'Wildlife'"
            },
            "difficulty_level": {
                "type": "string",
                "description": "Difficulty: 'Easy', 'Moderate', 'Challenging', 'Extreme'"
            },
            "min_rating": {
                "type": "number",
                "description": "Minimum rating to filter (1-5)"
            },
            "kid_friendly": {
                "type": "boolean",
                "description": "Must be kid friendly"
            }
        },
        "required": ["city"]
    }

    @staticmethod
    def execute(
        city: str,
        attraction_type: str = None,
        difficulty_level: str = None,
        min_rating: float = 0,
        kid_friendly: bool = False
    ) -> Dict[str, Any]:
        """Execute attraction search"""
        try:
            attractions = search_attractions(city, attraction_type, difficulty_level, min_rating)

            # Filter by kid friendly if requested
            if kid_friendly:
                attractions = [a for a in attractions if a.kid_friendly]

            if not attractions:
                return {
                    "success": False,
                    "message": f"No attractions found in {city} matching your criteria"
                }

            results = []
            for attraction in attractions[:6]:  # Top 6 results
                results.append({
                    "id": attraction.id,
                    "name": attraction.name,
                    "type": attraction.attraction_type.value,
                    "rating": attraction.rating,
                    "num_reviews": attraction.num_reviews,
                    "description": attraction.description[:100],
                    "entry_fee": attraction.entry_fee,
                    "distance_km": attraction.distance_from_city_center,
                    "duration_hours": attraction.duration_hours,
                    "difficulty": attraction.difficulty_level.value,
                    "kid_friendly": attraction.kid_friendly,
                    "best_time": attraction.best_time_to_visit,
                })

            return {
                "success": True,
                "count": len(results),
                "attractions": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class GetAttractionDetailsTool:
    """Get detailed information about a specific attraction"""

    name = "get_attraction_details"
    description = "Get detailed information about an attraction including hours, amenities, activities, reviews, and best times to visit"

    input_schema = {
        "type": "object",
        "properties": {
            "attraction_id": {
                "type": "string",
                "description": "Attraction ID to get details for"
            }
        },
        "required": ["attraction_id"]
    }

    @staticmethod
    def execute(attraction_id: str) -> Dict[str, Any]:
        """Execute get details"""
        try:
            attraction = get_attraction_by_id(attraction_id)

            if not attraction:
                return {
                    "success": False,
                    "message": f"Attraction with ID {attraction_id} not found"
                }

            return {
                "success": True,
                "attraction": {
                    "id": attraction.id,
                    "name": attraction.name,
                    "type": attraction.attraction_type.value,
                    "description": attraction.description,
                    "locality": attraction.locality,
                    "address": attraction.address,
                    "rating": attraction.rating,
                    "num_reviews": attraction.num_reviews,
                    "entry_fee": attraction.entry_fee,
                    "hours": f"{attraction.opening_time} - {attraction.closing_time}",
                    "duration_hours": attraction.duration_hours,
                    "distance_from_city_center_km": attraction.distance_from_city_center,
                    "difficulty": attraction.difficulty_level.value,
                    "suitable_for": {
                        "kids": attraction.kid_friendly,
                        "seniors": attraction.senior_friendly,
                        "wheelchair": attraction.wheelchair_accessible,
                    },
                    "crowd_level": attraction.typical_crowd_level.value,
                    "crowd_by_time": attraction.crowd_by_time,
                    "best_time_to_visit": attraction.best_time_to_visit,
                    "peak_season": attraction.peak_season,
                    "best_days": attraction.best_days,
                    "activities": attraction.activities_available,
                    "highlights": attraction.highlights,
                    "amenities": [a.name for a in attraction.amenities if a.available],
                    "phone": attraction.phone,
                    "website": attraction.website,
                    "reviews_sample": [
                        {
                            "reviewer": r.reviewer_name,
                            "rating": r.rating,
                            "comment": r.comment,
                            "date": r.date
                        }
                        for r in attraction.reviews[:2]
                    ]
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class FilterAttractionsTool:
    """Filter attractions by specific criteria"""

    name = "filter_attractions"
    description = "Filter attractions by specific requirements like family-friendly, wheelchair access, difficulty level, and crowd levels"

    input_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City to search in"
            },
            "kid_friendly": {
                "type": "boolean",
                "description": "Must be kid friendly"
            },
            "senior_friendly": {
                "type": "boolean",
                "description": "Must be senior friendly"
            },
            "wheelchair_accessible": {
                "type": "boolean",
                "description": "Must be wheelchair accessible"
            },
            "difficulty_level": {
                "type": "string",
                "description": "Difficulty level filter"
            },
            "max_duration_hours": {
                "type": "number",
                "description": "Maximum duration in hours"
            },
            "max_entry_fee": {
                "type": "number",
                "description": "Maximum entry fee in INR"
            }
        },
        "required": ["city"]
    }

    @staticmethod
    def execute(
        city: str,
        kid_friendly: bool = False,
        senior_friendly: bool = False,
        wheelchair_accessible: bool = False,
        difficulty_level: str = None,
        max_duration_hours: float = None,
        max_entry_fee: float = None
    ) -> Dict[str, Any]:
        """Execute filter attractions"""
        try:
            from data.mock_attractions import get_attractions_by_city
            attractions = get_attractions_by_city(city)

            # Filter by kid friendly
            if kid_friendly:
                attractions = [a for a in attractions if a.kid_friendly]

            # Filter by senior friendly
            if senior_friendly:
                attractions = [a for a in attractions if a.senior_friendly]

            # Filter by wheelchair accessible
            if wheelchair_accessible:
                attractions = [a for a in attractions if a.wheelchair_accessible]

            # Filter by difficulty
            if difficulty_level:
                diff_lower = difficulty_level.lower()
                attractions = [
                    a for a in attractions
                    if a.difficulty_level.value.lower() == diff_lower
                ]

            # Filter by duration
            if max_duration_hours:
                attractions = [a for a in attractions if a.duration_hours <= max_duration_hours]

            # Filter by entry fee
            if max_entry_fee:
                attractions = [a for a in attractions if a.entry_fee <= max_entry_fee]

            if not attractions:
                return {
                    "success": False,
                    "message": f"No attractions found in {city} matching all criteria"
                }

            results = []
            for attraction in attractions[:6]:
                results.append({
                    "id": attraction.id,
                    "name": attraction.name,
                    "type": attraction.attraction_type.value,
                    "rating": attraction.rating,
                    "entry_fee": attraction.entry_fee,
                    "duration_hours": attraction.duration_hours,
                    "difficulty": attraction.difficulty_level.value,
                    "suitable_for": {
                        "kids": attraction.kid_friendly,
                        "seniors": attraction.senior_friendly,
                        "wheelchair": attraction.wheelchair_accessible,
                    },
                    "best_time": attraction.best_time_to_visit,
                })

            return {
                "success": True,
                "count": len(results),
                "attractions": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Export tools
ATTRACTION_TOOLS = {
    "search_attractions": SearchAttractionsTool,
    "get_attraction_details": GetAttractionDetailsTool,
    "filter_attractions": FilterAttractionsTool,
}


def list_tools() -> List[str]:
    """List available tools"""
    return list(ATTRACTION_TOOLS.keys())

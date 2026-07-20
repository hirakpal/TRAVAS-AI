"""Transport tools for Safar Travel Agent"""

from typing import List, Dict, Any
from data.mock_transport import (
    search_flights, search_trains, search_local_transport,
    get_journey_by_id, get_local_transport_by_id
)


class SearchFlightsTool:
    """Search for flights between cities"""

    name = "search_flights"
    description = "Search for flights between two cities with optional filters like price"

    input_schema = {
        "type": "object",
        "properties": {
            "departure_city": {
                "type": "string",
                "description": "Departure city (e.g., 'Delhi', 'Mumbai')"
            },
            "arrival_city": {
                "type": "string",
                "description": "Arrival city (e.g., 'Goa')"
            },
            "max_price": {
                "type": "number",
                "description": "Maximum price per person in INR"
            }
        },
        "required": ["departure_city", "arrival_city"]
    }

    @staticmethod
    def execute(
        departure_city: str,
        arrival_city: str,
        max_price: float = None
    ) -> Dict[str, Any]:
        """Execute flight search"""
        try:
            flights = search_flights(departure_city, arrival_city, max_price)

            if not flights:
                return {
                    "success": False,
                    "message": f"No flights found from {departure_city} to {arrival_city}"
                }

            results = []
            for flight in flights:
                results.append({
                    "id": flight.id,
                    "airline": flight.operator_name,
                    "departure_time": flight.departure_time,
                    "arrival_time": flight.arrival_time,
                    "duration_hours": flight.duration_hours,
                    "price_per_person": flight.price_per_person,
                    "comfort_level": flight.comfort_level.value,
                    "rating": flight.rating,
                    "num_reviews": flight.num_reviews,
                    "seats_available": flight.seats_available,
                    "amenities": [a.name.value for a in flight.amenities if a.available],
                })

            return {
                "success": True,
                "count": len(results),
                "flights": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class SearchTrainsTool:
    """Search for trains between cities"""

    name = "search_trains"
    description = "Search for trains between two cities with optional price filter"

    input_schema = {
        "type": "object",
        "properties": {
            "departure_city": {
                "type": "string",
                "description": "Departure city"
            },
            "arrival_city": {
                "type": "string",
                "description": "Arrival city"
            },
            "max_price": {
                "type": "number",
                "description": "Maximum price per person in INR"
            }
        },
        "required": ["departure_city", "arrival_city"]
    }

    @staticmethod
    def execute(
        departure_city: str,
        arrival_city: str,
        max_price: float = None
    ) -> Dict[str, Any]:
        """Execute train search"""
        try:
            trains = search_trains(departure_city, arrival_city, max_price)

            if not trains:
                return {
                    "success": False,
                    "message": f"No trains found from {departure_city} to {arrival_city}"
                }

            results = []
            for train in trains:
                results.append({
                    "id": train.id,
                    "operator": train.operator_name,
                    "departure_time": train.departure_time,
                    "arrival_time": train.arrival_time,
                    "duration_hours": train.duration_hours,
                    "price_per_person": train.price_per_person,
                    "comfort_level": train.comfort_level.value,
                    "rating": train.rating,
                    "num_reviews": train.num_reviews,
                    "seats_available": train.seats_available,
                    "amenities": [a.name.value for a in train.amenities if a.available],
                })

            return {
                "success": True,
                "count": len(results),
                "trains": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class SearchLocalTransportTool:
    """Search for local transport options in a city"""

    name = "search_local_transport"
    description = "Search for local transport options like taxis, autos, car rentals, and ferries in a city"

    input_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City to search local transport in"
            },
            "transport_type": {
                "type": "string",
                "description": "Type of transport: 'Taxi', 'Auto Rickshaw', 'Car Rental', 'Ferry'"
            }
        },
        "required": ["city"]
    }

    @staticmethod
    def execute(
        city: str,
        transport_type: str = None
    ) -> Dict[str, Any]:
        """Execute local transport search"""
        try:
            transports = search_local_transport(city, transport_type)

            if not transports:
                return {
                    "success": False,
                    "message": f"No local transport found in {city}"
                }

            results = []
            for transport in transports:
                pricing = ""
                if transport.price_per_km:
                    pricing = f"₹{transport.price_per_km}/km"
                elif transport.hourly_rate:
                    pricing = f"₹{transport.hourly_rate}/hour"
                elif transport.flat_price:
                    pricing = f"₹{transport.flat_price} flat"

                results.append({
                    "id": transport.id,
                    "name": transport.name,
                    "type": transport.transport_type.value,
                    "vehicle": transport.vehicle_model,
                    "capacity": transport.capacity,
                    "pricing": pricing,
                    "rating": transport.rating,
                    "num_reviews": transport.num_reviews,
                    "ac": transport.ac,
                    "wifi": transport.wifi,
                    "wheelchair_accessible": transport.wheelchair_accessible,
                    "available_24_7": transport.available_24_7,
                    "response_time_minutes": transport.response_time_minutes,
                    "phone": transport.phone,
                })

            return {
                "success": True,
                "count": len(results),
                "transport_options": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class GetTransportDetailsTool:
    """Get detailed information about a transport option"""

    name = "get_transport_details"
    description = "Get detailed information about a flight, train, or local transport option including reviews and amenities"

    input_schema = {
        "type": "object",
        "properties": {
            "transport_id": {
                "type": "string",
                "description": "ID of flight, train, or local transport"
            },
            "transport_category": {
                "type": "string",
                "description": "Category: 'flight', 'train', or 'local'"
            }
        },
        "required": ["transport_id", "transport_category"]
    }

    @staticmethod
    def execute(
        transport_id: str,
        transport_category: str
    ) -> Dict[str, Any]:
        """Execute get details"""
        try:
            if transport_category.lower() == "local":
                transport = get_local_transport_by_id(transport_id)
                if not transport:
                    return {
                        "success": False,
                        "message": f"Local transport with ID {transport_id} not found"
                    }

                pricing = ""
                if transport.price_per_km:
                    pricing = f"₹{transport.price_per_km}/km"
                elif transport.hourly_rate:
                    pricing = f"₹{transport.hourly_rate}/hour"
                elif transport.flat_price:
                    pricing = f"₹{transport.flat_price} flat"

                return {
                    "success": True,
                    "transport": {
                        "id": transport.id,
                        "name": transport.name,
                        "type": transport.transport_type.value,
                        "vehicle": transport.vehicle_model,
                        "capacity": transport.capacity,
                        "pricing": pricing,
                        "rating": transport.rating,
                        "num_reviews": transport.num_reviews,
                        "features": {
                            "ac": transport.ac,
                            "wifi": transport.wifi,
                            "wheelchair_accessible": transport.wheelchair_accessible,
                            "luggage_space": transport.luggage_space,
                        },
                        "availability": {
                            "available_24_7": transport.available_24_7,
                            "response_time_minutes": transport.response_time_minutes,
                        },
                        "contact": {
                            "phone": transport.phone,
                            "website": transport.website,
                        },
                        "reviews": [
                            {
                                "reviewer": r.reviewer_name,
                                "rating": r.rating,
                                "comment": r.comment,
                            }
                            for r in transport.reviews[:2]
                        ]
                    }
                }
            else:
                journey = get_journey_by_id(transport_id)
                if not journey:
                    return {
                        "success": False,
                        "message": f"Journey with ID {transport_id} not found"
                    }

                return {
                    "success": True,
                    "transport": {
                        "id": journey.id,
                        "type": journey.transport_type.value,
                        "operator": journey.operator_name,
                        "route": f"{journey.departure_city} → {journey.arrival_city}",
                        "departure_time": journey.departure_time,
                        "arrival_time": journey.arrival_time,
                        "duration_hours": journey.duration_hours,
                        "journey_type": journey.get_journey_type(),
                        "price_per_person": journey.price_per_person,
                        "comfort_level": journey.comfort_level.value,
                        "rating": journey.rating,
                        "num_reviews": journey.num_reviews,
                        "seats_available": journey.seats_available,
                        "amenities": [a.name.value for a in journey.amenities if a.available],
                        "suitable_for": {
                            "kids": journey.kid_friendly,
                            "seniors": journey.senior_friendly,
                            "wheelchair": journey.wheelchair_accessible,
                        },
                        "cancellation_policy": journey.cancellation_policy,
                        "contact": {
                            "phone": journey.operator_phone,
                            "website": journey.operator_website,
                        },
                        "reviews": [
                            {
                                "reviewer": r.reviewer_name,
                                "rating": r.rating,
                                "comment": r.comment,
                            }
                            for r in journey.reviews[:2]
                        ]
                    }
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class SemanticSearchTransportTool:
    """Semantic (meaning-based) search over flights and trains - finds
    journeys matching a natural-language description (e.g. "cheapest direct
    option" or "most comfortable overnight journey") rather than only exact
    filters. Covers flights and trains only, not local transport (a
    separately-modeled dataset - use search_local_transport for that).
    """

    name = "semantic_search_transport"
    description = (
        "Search flights and trains between two cities by natural-language description "
        "(e.g. 'most comfortable direct option' or 'cheapest overnight journey'), using "
        "semantic similarity rather than only exact filters. Both cities are required - "
        "this tool only searches within TRAVAS's verified dataset for that exact route."
    )

    input_schema = {
        "type": "object",
        "properties": {
            "departure_city": {"type": "string", "description": "Departure city (required)"},
            "arrival_city": {"type": "string", "description": "Arrival city (required)"},
            "query": {"type": "string", "description": "Natural-language description of what the traveler wants"},
            "n_results": {"type": "integer", "description": "Max results to return", "default": 5},
        },
        "required": ["departure_city", "arrival_city", "query"],
    }

    @staticmethod
    def execute(departure_city: str, arrival_city: str, query: str, n_results: int = 5) -> Dict[str, Any]:
        from data.rag_index import semantic_search, get_record_by_id

        dep = departure_city.strip().title()
        arr = arrival_city.strip().title()
        route_label = f"{dep} to {arr}"

        # Filter by departure_city via the vector store, then narrow to the
        # exact arrival_city in Python - avoids depending on chromadb's
        # compound-filter ($and) operator support across versions.
        hits = semantic_search(
            "transport", query, n_results=max(n_results * 3, 10), where={"departure_city": dep}
        )
        matched = []
        for hit in hits:
            journey = get_record_by_id("transport", hit["id"])
            if journey is not None and journey.arrival_city == arr:
                matched.append((journey, hit))
            if len(matched) >= n_results:
                break

        if not matched:
            return {
                "success": False,
                "message": (
                    f"No semantic matches for '{query}' on the {route_label} route. This means "
                    f"this route is not in TRAVAS's current verified transport dataset - tell the "
                    f"user plainly that you don't have verified data for it, rather than answering "
                    f"from general knowledge."
                ),
                "results": [],
            }

        results = [
            {
                "id": j.id,
                "type": j.transport_type.value,
                "operator": j.operator_name,
                "departure_time": j.departure_time,
                "arrival_time": j.arrival_time,
                "price_per_person": j.price_per_person,
                "comfort_level": j.comfort_level.value,
                "why_matched": hit["document"][:200],
            }
            for j, hit in matched
        ]
        return {
            "success": True,
            "message": f"Found {len(results)} semantically relevant result(s) for '{query}' on {route_label}",
            "results": results,
        }


# Export tools
TRANSPORT_TOOLS = {
    "search_flights": SearchFlightsTool,
    "search_trains": SearchTrainsTool,
    "search_local_transport": SearchLocalTransportTool,
    "get_transport_details": GetTransportDetailsTool,
    "semantic_search_transport": SemanticSearchTransportTool,
}


def list_tools() -> List[str]:
    """List available tools"""
    return list(TRANSPORT_TOOLS.keys())

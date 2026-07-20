"""Shopping tools for Bazaar Shopping Agent"""

from typing import List, Dict, Any
from data.mock_shops import (
    search_shops, search_shops_by_category, get_shop_by_id
)


class SearchShopsTool:
    """Search for shops by city and type"""

    name = "search_shops"
    description = "Search for shops in a city by type (market, mall, boutique, etc.) and rating"

    input_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City to search in (e.g., 'Goa', 'Mumbai')"
            },
            "shop_type": {
                "type": "string",
                "description": "Type of shop: 'Market/Bazaar', 'Souvenir Shop', 'Mall', 'Boutique', 'Handicraft Store', 'Spice Market', 'Jewelry Shop', 'Clothing Store'"
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
        shop_type: str = None,
        min_rating: float = 0
    ) -> Dict[str, Any]:
        """Execute shop search"""
        try:
            shops = search_shops(city, shop_type, min_rating)

            if not shops:
                return {
                    "success": False,
                    "message": f"No shops found in {city} matching your criteria"
                }

            results = []
            for shop in shops:
                results.append({
                    "id": shop.id,
                    "name": shop.name,
                    "type": shop.shop_type.value,
                    "locality": shop.locality,
                    "rating": shop.rating,
                    "num_reviews": shop.num_reviews,
                    "price_range": shop.price_range,
                    "distance_km": shop.distance_from_city_center,
                    "hours": f"{shop.opening_time} - {shop.closing_time}",
                    "crowd_level": shop.typical_crowd_level.value,
                    "best_time": shop.best_time_to_visit,
                    "bargaining": shop.bargaining_possible,
                })

            return {
                "success": True,
                "count": len(results),
                "shops": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class SearchByCategory:
    """Search shops by product category"""

    name = "search_by_category"
    description = "Search for shops that sell specific types of products (spices, handicrafts, textiles, jewelry, souvenirs, etc.)"

    input_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City to search in"
            },
            "category": {
                "type": "string",
                "description": "Product category: 'Spices', 'Handicrafts', 'Textiles', 'Jewelry', 'Souvenirs', 'Clothing', 'Ceramics', 'Ayurveda'"
            }
        },
        "required": ["city", "category"]
    }

    @staticmethod
    def execute(
        city: str,
        category: str
    ) -> Dict[str, Any]:
        """Execute category search"""
        try:
            shops = search_shops_by_category(city, category)

            if not shops:
                return {
                    "success": False,
                    "message": f"No shops found selling {category} in {city}"
                }

            results = []
            for shop in shops:
                results.append({
                    "id": shop.id,
                    "name": shop.name,
                    "type": shop.shop_type.value,
                    "rating": shop.rating,
                    "price_range": shop.price_range,
                    "popular_items": shop.popular_items,
                    "bargaining": shop.bargaining_possible,
                    "distance_km": shop.distance_from_city_center,
                    "best_time": shop.best_time_to_visit,
                })

            return {
                "success": True,
                "count": len(results),
                "shops": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class GetShopDetailsTool:
    """Get detailed information about a shop"""

    name = "get_shop_details"
    description = "Get detailed information about a shop including hours, prices, items, reviews, and facilities"

    input_schema = {
        "type": "object",
        "properties": {
            "shop_id": {
                "type": "string",
                "description": "Shop ID to get details for"
            }
        },
        "required": ["shop_id"]
    }

    @staticmethod
    def execute(shop_id: str) -> Dict[str, Any]:
        """Execute get details"""
        try:
            shop = get_shop_by_id(shop_id)

            if not shop:
                return {
                    "success": False,
                    "message": f"Shop with ID {shop_id} not found"
                }

            return {
                "success": True,
                "shop": {
                    "id": shop.id,
                    "name": shop.name,
                    "type": shop.shop_type.value,
                    "description": shop.description,
                    "address": shop.address,
                    "locality": shop.locality,
                    "rating": shop.rating,
                    "num_reviews": shop.num_reviews,
                    "contact": {
                        "phone": shop.phone,
                        "website": shop.website,
                        "email": shop.email,
                    },
                    "hours": {
                        "opening": shop.opening_time,
                        "closing": shop.closing_time,
                        "closed_on": shop.closed_on,
                    },
                    "location": {
                        "distance_from_center_km": shop.distance_from_city_center,
                        "distance_from_hotel_km": shop.distance_from_hotel,
                    },
                    "crowd_info": {
                        "typical_level": shop.typical_crowd_level.value,
                        "by_time": shop.crowd_by_time,
                        "best_time": shop.best_time_to_visit,
                    },
                    "products": {
                        "categories": [c.value for c in shop.product_categories],
                        "popular_items": shop.popular_items,
                        "price_range": shop.price_range,
                        "min_price": shop.min_price,
                        "max_price": shop.max_price,
                    },
                    "shopping": {
                        "bargaining_possible": shop.bargaining_possible,
                        "authenticity_guaranteed": shop.authenticity_guaranteed,
                        "warranty_available": shop.warranty_available,
                        "refund_policy": shop.refund_policy,
                    },
                    "facilities": {
                        "payment_methods": shop.payment_methods,
                        "wifi": shop.has_wifi,
                        "parking": shop.has_parking,
                        "wheelchair_accessible": shop.wheelchair_accessible,
                        "international_cards": shop.accepts_international_cards,
                    },
                    "special": {
                        "tourist_friendly": shop.tourist_friendly,
                        "special_offers": shop.special_offers,
                        "delivery_available": shop.delivery_available,
                    },
                    "reviews": [
                        {
                            "reviewer": r.reviewer_name,
                            "rating": r.rating,
                            "comment": r.comment,
                            "date": r.date
                        }
                        for r in shop.reviews[:2]
                    ]
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class CompareShopsTool:
    """Compare multiple shops for similar products"""

    name = "compare_shops"
    description = "Compare different shops selling similar products based on price, quality, and ratings"

    input_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City to search in"
            },
            "product_category": {
                "type": "string",
                "description": "Product category to compare"
            },
            "budget": {
                "type": "number",
                "description": "Budget limit in INR"
            }
        },
        "required": ["city", "product_category"]
    }

    @staticmethod
    def execute(
        city: str,
        product_category: str,
        budget: float = None
    ) -> Dict[str, Any]:
        """Execute shop comparison"""
        try:
            shops = search_shops_by_category(city, product_category)

            if not shops:
                return {
                    "success": False,
                    "message": f"No shops found selling {product_category}"
                }

            # Filter by budget if specified
            if budget:
                shops = [s for s in shops if s.min_price <= budget]

            if not shops:
                return {
                    "success": False,
                    "message": f"No shops found within budget ₹{budget}"
                }

            results = []
            for shop in shops:
                results.append({
                    "id": shop.id,
                    "name": shop.name,
                    "rating": shop.rating,
                    "price_range": f"₹{shop.min_price} - ₹{shop.max_price}",
                    "popular_items": shop.popular_items[:2],
                    "best_for": "Best for bargaining" if shop.bargaining_possible else "Fixed prices",
                    "crowd_level": shop.typical_crowd_level.value,
                    "best_time": shop.best_time_to_visit,
                    "distance_km": shop.distance_from_city_center,
                })

            return {
                "success": True,
                "count": len(results),
                "comparison": sorted(results, key=lambda x: x["rating"], reverse=True)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class SemanticSearchShopsTool:
    """Semantic (meaning-based) shop search - finds shops matching a
    natural-language description rather than only exact filters.
    """

    name = "semantic_search_shops"
    description = (
        "Search shops by natural-language description or vibe (e.g. 'authentic local "
        "handicrafts market where I can bargain') within a specific city, using semantic "
        "similarity rather than only exact keyword filters. City is required - this tool "
        "only searches within TRAVAS's verified dataset for that city."
    )

    input_schema = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City to search within (required)"},
            "query": {"type": "string", "description": "Natural-language description of what the traveler wants"},
            "n_results": {"type": "integer", "description": "Max results to return", "default": 5},
        },
        "required": ["city", "query"],
    }

    @staticmethod
    def execute(city: str, query: str, n_results: int = 5) -> Dict[str, Any]:
        from tools.rag_helpers import run_semantic_search

        def _format(shop, hit):
            return {
                "id": shop.id,
                "name": shop.name,
                "type": shop.shop_type.value,
                "locality": shop.locality,
                "rating": shop.rating,
                "bargaining_possible": shop.bargaining_possible,
                "why_matched": hit["document"][:200],
            }

        return run_semantic_search(
            domain="shops",
            query=query,
            where={"city": city.strip().title()},
            coverage_label=city,
            n_results=n_results,
            formatter=_format,
        )


# Export tools
SHOPPING_TOOLS = {
    "search_shops": SearchShopsTool,
    "search_by_category": SearchByCategory,
    "get_shop_details": GetShopDetailsTool,
    "compare_shops": CompareShopsTool,
    "semantic_search_shops": SemanticSearchShopsTool,
}


def list_tools() -> List[str]:
    """List available tools"""
    return list(SHOPPING_TOOLS.keys())

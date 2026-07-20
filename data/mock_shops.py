"""Mock shopping database for Bazaar Shopping Agent"""

from models.shopping import (
    Shop, Item, Review, ShopType, ItemCategory, CrowdLevel
)


def create_mock_shops() -> dict:
    """Create mock shopping database by city"""

    goa_shops = [
        Shop(
            id="shop_001",
            name="Anjuna Spice Market",
            shop_type=ShopType.SPICE_MARKET,
            address="Anjuna Beach Road, Goa",
            city="Goa",
            locality="Anjuna",
            phone="0832-2234567",
            rating=4.5,
            num_reviews=456,
            reviews=[
                Review("Spice Lover", 4.5, "Authentic spices, great prices", "2026-06-15", 89),
                Review("Tourist", 4.5, "Amazing variety", "2026-06-10", 67),
            ],
            opening_time="09:00",
            closing_time="19:00",
            distance_from_city_center=15.0,
            typical_crowd_level=CrowdLevel.HIGH,
            crowd_by_time={"morning": "Moderate", "afternoon": "High", "evening": "Very High"},
            best_time_to_visit="Morning",
            bargaining_possible=True,
            items_available=[
                Item("Cardamom", ItemCategory.SPICES, 800, "Premium green cardamom", "Premium", True, True),
                Item("Turmeric Powder", ItemCategory.SPICES, 200, "Pure turmeric", "Budget", True, True),
                Item("Chili Powder", ItemCategory.SPICES, 150, "Hot chili powder", "Budget", True, True),
            ],
            product_categories=[ItemCategory.SPICES, ItemCategory.AYURVEDA],
            payment_methods=["Cash", "UPI"],
            min_price=50,
            max_price=2000,
            price_range="Budget",
            popular_items=["Cardamom", "Turmeric", "Pepper Mix"],
            description="Best place for authentic Goan and Indian spices",
        ),

        Shop(
            id="shop_002",
            name="Goa Handicrafts Emporium",
            shop_type=ShopType.HANDICRAFT,
            address="Panjim Market, Goa",
            city="Goa",
            locality="Panjim",
            phone="0832-2245678",
            website="https://goahandicrafts.com",
            rating=4.3,
            num_reviews=234,
            reviews=[
                Review("Gift Buyer", 4.5, "Beautiful crafts, fair prices", "2026-06-12", 56),
                Review("Collector", 4.0, "Good quality souvenirs", "2026-06-08", 43),
            ],
            opening_time="10:00",
            closing_time="20:00",
            distance_from_city_center=5.0,
            typical_crowd_level=CrowdLevel.MODERATE,
            crowd_by_time={"morning": "Low", "afternoon": "Moderate", "evening": "High"},
            best_time_to_visit="Morning",
            bargaining_possible=True,
            items_available=[
                Item("Wooden Mask", ItemCategory.HANDICRAFTS, 500, "Hand-carved wooden mask", "Mid-range", True, True),
                Item("Ceramic Pot", ItemCategory.CERAMICS, 300, "Traditional Goan pottery", "Mid-range", True, True),
                Item("Fabric Wall Hanging", ItemCategory.TEXTILES, 400, "Hand-woven fabric", "Mid-range", True, True),
            ],
            product_categories=[ItemCategory.HANDICRAFTS, ItemCategory.CERAMICS, ItemCategory.TEXTILES],
            authenticity_guaranteed=True,
            payment_methods=["Cash", "Card", "UPI"],
            has_parking=True,
            wheelchair_accessible=False,
            min_price=100,
            max_price=5000,
            price_range="Mid-range",
            tourist_friendly=True,
            popular_items=["Wooden Masks", "Ceramic Pots", "Fabric Hangings"],
            description="Authentic Goan handicrafts and traditional art",
        ),

        Shop(
            id="shop_003",
            name="Goa Textiles Paradise",
            shop_type=ShopType.BOUTIQUE,
            address="Calangute Beach Road, Goa",
            city="Goa",
            locality="Calangute",
            phone="0832-2256789",
            rating=4.2,
            num_reviews=189,
            reviews=[
                Review("Fashion Lover", 4.0, "Great clothes, some pricey", "2026-06-14", 34),
                Review("Tourist", 4.5, "Beautiful fabrics", "2026-06-09", 28),
            ],
            opening_time="11:00",
            closing_time="21:00",
            distance_from_city_center=10.0,
            typical_crowd_level=CrowdLevel.HIGH,
            crowd_by_time={"morning": "Low", "afternoon": "High", "evening": "Very High"},
            best_time_to_visit="Morning or Afternoon",
            bargaining_possible=True,
            items_available=[
                Item("Silk Scarf", ItemCategory.TEXTILES, 600, "Hand-dyed silk", "Premium", True, True),
                Item("Cotton Kurti", ItemCategory.CLOTHING, 400, "Traditional kurta", "Mid-range", True, True),
                Item("Embroidered Saree", ItemCategory.TEXTILES, 1500, "Hand-embroidered", "Premium", True, True),
            ],
            product_categories=[ItemCategory.TEXTILES, ItemCategory.CLOTHING],
            payment_methods=["Cash", "Card", "UPI"],
            has_wifi=True,
            wheelchair_accessible=True,
            min_price=200,
            max_price=3000,
            price_range="Mid-range to Premium",
            tourist_friendly=True,
            popular_items=["Silk Scarves", "Kurtis", "Sarees"],
            description="Traditional and modern Indian textiles and clothing",
        ),

        Shop(
            id="shop_004",
            name="Coconut Goa Gifts",
            shop_type=ShopType.SOUVENIR_SHOP,
            address="Baga Beach Main Road, Goa",
            city="Goa",
            locality="Baga",
            phone="0832-2267890",
            rating=4.0,
            num_reviews=567,
            reviews=[
                Review("Tourist Mike", 4.0, "Good souvenirs, tourist prices", "2026-06-13", 78),
                Review("Family", 4.0, "Nice gifts for home", "2026-06-10", 62),
            ],
            opening_time="09:00",
            closing_time="22:00",
            distance_from_city_center=8.0,
            typical_crowd_level=CrowdLevel.VERY_HIGH,
            crowd_by_time={"morning": "High", "afternoon": "Very High", "evening": "Very High"},
            best_time_to_visit="Early Morning",
            bargaining_possible=False,
            items_available=[
                Item("Coconut Shell Lamp", ItemCategory.SOUVENIRS, 350, "Hand-made from coconut shell", "Budget", True, False),
                Item("Goa Tea Set", ItemCategory.SOUVENIRS, 200, "Decorative tea set", "Budget", True, False),
                Item("Fridge Magnet", ItemCategory.SOUVENIRS, 50, "Goa themed magnet", "Budget", True, False),
            ],
            product_categories=[ItemCategory.SOUVENIRS, ItemCategory.COCONUT_PRODUCTS],
            payment_methods=["Cash", "Card", "UPI"],
            has_parking=False,
            wheelchair_accessible=True,
            min_price=50,
            max_price=1000,
            price_range="Budget",
            tourist_friendly=True,
            popular_items=["Coconut Lamps", "Tea Sets", "Magnets"],
            special_offers=["Bulk discount 10% above ₹2000"],
            description="Touristy souvenirs and gift items - perfect for remembering Goa",
        ),

        Shop(
            id="shop_005",
            name="Goa Jewelry Boutique",
            shop_type=ShopType.JEWELRY,
            address="Fort Road, Panjim, Goa",
            city="Goa",
            locality="Panjim",
            phone="0832-2278901",
            website="https://goajewelry.com",
            rating=4.6,
            num_reviews=234,
            reviews=[
                Review("Bride", 4.5, "Beautiful designs, authentic", "2026-06-12", 89),
                Review("Collector", 4.5, "Quality craftsmanship", "2026-06-07", 76),
            ],
            opening_time="11:00",
            closing_time="19:00",
            closed_on=["Sunday"],
            distance_from_city_center=3.0,
            typical_crowd_level=CrowdLevel.MODERATE,
            crowd_by_time={"morning": "Low", "afternoon": "Moderate", "evening": "Moderate"},
            best_time_to_visit="Afternoon",
            bargaining_possible=False,
            items_available=[
                Item("Silver Earrings", ItemCategory.JEWELRY, 800, "92.5% silver", "Premium", True, False),
                Item("Pearl Necklace", ItemCategory.JEWELRY, 2500, "Freshwater pearls", "Premium", True, False),
                Item("Gold Ring", ItemCategory.JEWELRY, 5000, "22K gold", "Luxury", True, False),
            ],
            product_categories=[ItemCategory.JEWELRY],
            authenticity_guaranteed=True,
            warranty_available=True,
            payment_methods=["Cash", "Card"],
            has_parking=True,
            wheelchair_accessible=True,
            accepts_international_cards=True,
            min_price=500,
            max_price=10000,
            price_range="Premium to Luxury",
            tourist_friendly=True,
            popular_items=["Silver Jewelry", "Pearl Sets", "Gold Rings"],
            description="Authentic Goan jewelry with certificate of authenticity",
        ),

        Shop(
            id="shop_006",
            name="Goa Mall",
            shop_type=ShopType.MALL,
            address="Vasco da Gama, Goa",
            city="Goa",
            locality="Vasco da Gama",
            phone="0832-2289012",
            website="https://goamall.com",
            rating=4.1,
            num_reviews=892,
            reviews=[
                Review("Family", 4.0, "Good for shopping, nice AC", "2026-06-14", 123),
                Review("Shopper", 4.0, "All stores in one place", "2026-06-11", 98),
            ],
            opening_time="10:00",
            closing_time="22:00",
            distance_from_city_center=20.0,
            typical_crowd_level=CrowdLevel.HIGH,
            crowd_by_time={"morning": "Moderate", "afternoon": "High", "evening": "Very High"},
            best_time_to_visit="Weekday Morning",
            bargaining_possible=False,
            product_categories=[ItemCategory.CLOTHING, ItemCategory.ELECTRONICS, ItemCategory.BOOKS],
            payment_methods=["Cash", "Card", "UPI"],
            has_wifi=True,
            has_parking=True,
            wheelchair_accessible=True,
            min_price=100,
            max_price=10000,
            price_range="All ranges",
            tourist_friendly=True,
            popular_items=["Brands", "Electronics", "Food Court"],
            special_offers=["Weekend sales", "Credit card discounts"],
            description="Modern shopping mall with international and local brands",
        ),
    ]

    return {
        "goa": goa_shops,
    }


def get_shops_by_city(city: str) -> list:
    """Get all shops in a city"""
    db = create_mock_shops()
    return db.get(city.lower(), [])


def search_shops(city: str, shop_type: str = None, min_rating: float = 0) -> list:
    """Search shops by city and filters"""
    shops = get_shops_by_city(city)

    if shop_type:
        type_lower = shop_type.lower()
        shops = [
            s for s in shops
            if s.shop_type.value.lower() == type_lower
        ]

    if min_rating > 0:
        shops = [s for s in shops if s.rating >= min_rating]

    return shops


def search_shops_by_category(city: str, category: str) -> list:
    """Search shops by product category"""
    shops = get_shops_by_city(city)
    category_lower = category.lower()

    filtered_shops = [
        s for s in shops
        if any(c.value.lower() == category_lower for c in s.product_categories)
    ]

    return filtered_shops


def get_shop_by_id(shop_id: str) -> Shop:
    """Get shop by ID"""
    for city_shops in create_mock_shops().values():
        for shop in city_shops:
            if shop.id == shop_id:
                return shop
    return None

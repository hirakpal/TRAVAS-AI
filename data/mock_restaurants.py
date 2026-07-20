"""Mock restaurant database for Annapurna Agent"""

from models.restaurant import (
    Restaurant, Review, RestaurantAmenity, AmenityType, Cuisine, RestaurantType
)


def create_mock_restaurants() -> dict:
    """Create mock restaurant database by city"""

    goa_restaurants = [
        Restaurant(
            id="goa_001",
            name="Fisherman's Wharf",
            address="Panjim, Goa",
            city="Goa",
            locality="Panjim Waterfront",
            cuisine_types=[Cuisine.SEAFOOD, Cuisine.CONTINENTAL],
            restaurant_type=RestaurantType.FINE_DINING,
            phone="0832-2234567",
            website="https://fishmanswharf.goa.com",
            rating=4.7,
            num_reviews=342,
            reviews=[
                Review("John D.", 5.0, "Fantastic seafood and river views!", "2026-06-15", 45),
                Review("Priya M.", 4.5, "Great for special occasions", "2026-06-10", 32),
            ],
            avg_cost_per_person=1200,
            price_range="Premium",
            amenities=[
                RestaurantAmenity(AmenityType.WIFI, True),
                RestaurantAmenity(AmenityType.PARKING, True),
                RestaurantAmenity(AmenityType.AC, True),
                RestaurantAmenity(AmenityType.OUTDOOR_SEATING, True),
                RestaurantAmenity(AmenityType.ROOFTOP, True),
                RestaurantAmenity(AmenityType.RESERVATIONS, True),
                RestaurantAmenity(AmenityType.WHEELCHAIR_ACCESS, True),
            ],
            dietary_options=["Vegetarian", "Seafood", "Gluten-free"],
            special_dishes=["Prawn Koliwada", "Lobster Thermidor", "Fish Ambot Tik"],
            distance_from_city_center=2.5,
            busy_hours=["12-1:30pm", "7-9:30pm"],
        ),

        Restaurant(
            id="goa_002",
            name="Spice Garden",
            address="Baga Beach, Goa",
            city="Goa",
            locality="Baga",
            cuisine_types=[Cuisine.INDIAN, Cuisine.NORTH_INDIAN],
            restaurant_type=RestaurantType.CASUAL,
            phone="0832-2245678",
            website="https://spicegarden.goa.com",
            rating=4.3,
            num_reviews=215,
            reviews=[
                Review("Raj K.", 4.5, "Authentic Indian flavors", "2026-06-12", 28),
                Review("Emma S.", 4.0, "Good for families", "2026-06-08", 18),
            ],
            avg_cost_per_person=450,
            price_range="Mid-range",
            amenities=[
                RestaurantAmenity(AmenityType.WIFI, True),
                RestaurantAmenity(AmenityType.AC, True),
                RestaurantAmenity(AmenityType.KIDS_MENU, True),
                RestaurantAmenity(AmenityType.HIGHCHAIR, True),
                RestaurantAmenity(AmenityType.DELIVERY, True),
                RestaurantAmenity(AmenityType.TAKEAWAY, True),
            ],
            dietary_options=["Vegetarian", "Vegan", "Jain", "Dairy-free"],
            special_dishes=["Butter Chicken", "Paneer Tikka", "Dal Makhani", "Garlic Naan"],
            distance_from_city_center=8.0,
            busy_hours=["12-2pm", "6:30-8:30pm"],
        ),

        Restaurant(
            id="goa_003",
            name="Beach Shack Delight",
            address="Calangute Beach, Goa",
            city="Goa",
            locality="Calangute",
            cuisine_types=[Cuisine.STREET_FOOD, Cuisine.SEAFOOD],
            restaurant_type=RestaurantType.FOOD_COURT,
            phone="0832-2256789",
            rating=4.1,
            num_reviews=487,
            reviews=[
                Review("Tourist Anu", 4.5, "Authentic beach experience", "2026-06-14", 52),
                Review("Local Mike", 4.0, "Good value for money", "2026-06-09", 35),
            ],
            avg_cost_per_person=250,
            price_range="Budget",
            amenities=[
                RestaurantAmenity(AmenityType.OUTDOOR_SEATING, True),
                RestaurantAmenity(AmenityType.WIFI, True),
                RestaurantAmenity(AmenityType.DELIVERY, True),
            ],
            dietary_options=["Vegetarian", "Seafood", "Vegan"],
            special_dishes=["Grilled Fish", "Prawn Curry Rice", "Corn on Cob", "Fresh Juice"],
            distance_from_city_center=12.0,
            busy_hours=["11am-1pm", "5-8pm"],
        ),

        Restaurant(
            id="goa_004",
            name="Zen Café",
            address="Fort Aguada, Goa",
            city="Goa",
            locality="Fort Aguada",
            cuisine_types=[Cuisine.CONTINENTAL, Cuisine.VEGETARIAN],
            restaurant_type=RestaurantType.CAFE,
            phone="0832-2267890",
            rating=4.5,
            num_reviews=298,
            reviews=[
                Review("Coffee Lover", 4.5, "Best coffee in Goa", "2026-06-13", 67),
                Review("Sarah P.", 4.5, "Peaceful ambiance", "2026-06-11", 41),
            ],
            avg_cost_per_person=350,
            price_range="Mid-range",
            amenities=[
                RestaurantAmenity(AmenityType.WIFI, True),
                RestaurantAmenity(AmenityType.AC, True),
                RestaurantAmenity(AmenityType.OUTDOOR_SEATING, True),
                RestaurantAmenity(AmenityType.LIVE_MUSIC, True),
            ],
            dietary_options=["Vegetarian", "Vegan", "Gluten-free"],
            special_dishes=["Cappuccino", "Spinach Quiche", "Chocolate Cake", "Green Smoothie"],
            distance_from_city_center=5.0,
            busy_hours=["9-11am", "3-5pm"],
        ),

        Restaurant(
            id="goa_005",
            name="Monsoon Palace",
            address="Panjim, Goa",
            city="Goa",
            locality="Panjim",
            cuisine_types=[Cuisine.INDIAN, Cuisine.SOUTH_INDIAN, Cuisine.VEGETARIAN],
            restaurant_type=RestaurantType.FAMILY_STYLE,
            phone="0832-2278901",
            rating=4.2,
            num_reviews=156,
            reviews=[
                Review("Family Man", 4.5, "Great for families with kids", "2026-06-12", 23),
                Review("Veg Lover", 4.0, "Excellent vegetarian options", "2026-06-10", 19),
            ],
            avg_cost_per_person=500,
            price_range="Mid-range",
            amenities=[
                RestaurantAmenity(AmenityType.WIFI, True),
                RestaurantAmenity(AmenityType.AC, True),
                RestaurantAmenity(AmenityType.KIDS_MENU, True),
                RestaurantAmenity(AmenityType.HIGHCHAIR, True),
                RestaurantAmenity(AmenityType.WHEELCHAIR_ACCESS, True),
                RestaurantAmenity(AmenityType.PARKING, True),
            ],
            dietary_options=["Vegetarian", "Vegan", "Jain", "Gluten-free"],
            special_dishes=["Dosa", "Idli Sambar", "Uttapam", "Rasam"],
            distance_from_city_center=3.0,
            busy_hours=["12-1:30pm", "7-9pm"],
        ),

        Restaurant(
            id="goa_006",
            name="The Spice Route",
            address="Mandovi River, Goa",
            city="Goa",
            locality="Goan Heritage",
            cuisine_types=[Cuisine.INDIAN, Cuisine.FUSION],
            restaurant_type=RestaurantType.FINE_DINING,
            phone="0832-2289012",
            website="https://spiceroute.goa.com",
            rating=4.6,
            num_reviews=189,
            reviews=[
                Review("Chef Rahul", 4.5, "Innovative Goan cuisine", "2026-06-13", 38),
                Review("Meena W.", 4.5, "Beautiful setting", "2026-06-11", 29),
            ],
            avg_cost_per_person=1500,
            price_range="Luxury",
            amenities=[
                RestaurantAmenity(AmenityType.WIFI, True),
                RestaurantAmenity(AmenityType.PARKING, True),
                RestaurantAmenity(AmenityType.AC, True),
                RestaurantAmenity(AmenityType.PRIVATE_ROOMS, True),
                RestaurantAmenity(AmenityType.RESERVATIONS, True),
                RestaurantAmenity(AmenityType.LIVE_MUSIC, True),
                RestaurantAmenity(AmenityType.WHEELCHAIR_ACCESS, True),
            ],
            dietary_options=["Vegetarian", "Seafood", "Vegan Options"],
            special_dishes=["Bebinca", "Recheado", "Sorpotel", "Fish Curry Rice"],
            distance_from_city_center=4.5,
            busy_hours=["12:30-1:30pm", "7-9pm"],
        ),
    ]

    return {
        "goa": goa_restaurants,
    }


def get_restaurants_by_city(city: str) -> list:
    """Get all restaurants in a city"""
    db = create_mock_restaurants()
    return db.get(city.lower(), [])


def search_restaurants(city: str, cuisine: str = None, price_range: str = None) -> list:
    """Search restaurants by city and filters"""
    restaurants = get_restaurants_by_city(city)

    # Filter by cuisine if specified
    if cuisine:
        cuisine_lower = cuisine.lower()
        restaurants = [
            r for r in restaurants
            if any(c.value.lower() == cuisine_lower for c in r.cuisine_types)
        ]

    # Filter by price range if specified
    if price_range:
        restaurants = [r for r in restaurants if r.price_range.lower() == price_range.lower()]

    return restaurants


def get_restaurant_by_id(restaurant_id: str) -> Restaurant:
    """Get restaurant by ID"""
    for city_restaurants in create_mock_restaurants().values():
        for restaurant in city_restaurants:
            if restaurant.id == restaurant_id:
                return restaurant
    return None

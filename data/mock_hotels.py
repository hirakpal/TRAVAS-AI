"""Mock hotel data for demonstration."""

from models.hotel import Hotel, Room, RoomType, HotelAmenity, HotelReview


def get_mock_hotels() -> dict:
    """Get mock hotel database organized by city"""

    # Delhi Hotels
    delhi_hotels = [
        Hotel(
            id="h001_taj_delhi",
            name="Taj Palace New Delhi",
            city="Delhi",
            location="Diplomatic Enclave, New Delhi",
            star_rating=5.0,
            price_range={"min": 15000, "max": 45000},
            rooms=[
                Room(RoomType.DOUBLE, 15000, 2, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.TV]),
                Room(RoomType.DELUXE, 25000, 2, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.TV, HotelAmenity.SPA]),
                Room(RoomType.SUITE, 45000, 4, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.TV, HotelAmenity.SPA, HotelAmenity.MOUNTAIN_VIEW]),
            ],
            amenities=[
                HotelAmenity.WIFI, HotelAmenity.POOL, HotelAmenity.GYM, HotelAmenity.SPA,
                HotelAmenity.RESTAURANT, HotelAmenity.PARKING, HotelAmenity.WHEELCHAIR_ACCESS,
                HotelAmenity.FAMILY_ROOMS, HotelAmenity.VEGETARIAN_FOOD
            ],
            reviews=[
                HotelReview(4.8, "Excellent service and beautiful rooms", "overall", True),
                HotelReview(4.9, "Top-notch cleanliness", "cleanliness", True),
                HotelReview(4.7, "Great location near markets", "location", True),
            ],
            phone="+91-11-6162-5162",
            email="info@tajpalacehotels.com",
            website="www.tajpalacehotels.com",
            description="Luxury hotel in the heart of New Delhi with world-class amenities",
        ),
        Hotel(
            id="h002_budget_delhi",
            name="Budget Nest Delhi",
            city="Delhi",
            location="Karol Bagh, New Delhi",
            star_rating=3.5,
            price_range={"min": 2000, "max": 5000},
            rooms=[
                Room(RoomType.SINGLE, 2000, 1, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.TV]),
                Room(RoomType.DOUBLE, 3500, 2, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.TV, HotelAmenity.HOT_WATER]),
                Room(RoomType.FAMILY, 5000, 4, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.TV, HotelAmenity.KIDS_PLAY_AREA]),
            ],
            amenities=[
                HotelAmenity.WIFI, HotelAmenity.RESTAURANT, HotelAmenity.VEGETARIAN_FOOD,
                HotelAmenity.AC, HotelAmenity.PARKING, HotelAmenity.FAMILY_ROOMS
            ],
            reviews=[
                HotelReview(4.2, "Great value for money", "value_for_money", True),
                HotelReview(4.0, "Clean and comfortable rooms", "cleanliness", True),
                HotelReview(4.3, "Good location for shopping", "location", True),
            ],
            phone="+91-11-4598-1234",
            email="support@budgetnesdelhi.com",
            description="Affordable and comfortable accommodation for travelers on budget",
        ),
    ]

    # Mumbai Hotels
    mumbai_hotels = [
        Hotel(
            id="h003_beach_mumbai",
            name="Beachfront Paradise Mumbai",
            city="Mumbai",
            location="Bandra, Mumbai",
            star_rating=4.5,
            price_range={"min": 10000, "max": 30000},
            rooms=[
                Room(RoomType.DOUBLE, 10000, 2, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.BEACH_VIEW]),
                Room(RoomType.DELUXE, 20000, 2, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.BEACH_VIEW, HotelAmenity.SPA]),
                Room(RoomType.SUITE, 30000, 4, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.BEACH_VIEW, HotelAmenity.SPA, HotelAmenity.POOL]),
            ],
            amenities=[
                HotelAmenity.WIFI, HotelAmenity.POOL, HotelAmenity.BEACH_VIEW,
                HotelAmenity.RESTAURANT, HotelAmenity.PARKING, HotelAmenity.VEGETARIAN_FOOD
            ],
            reviews=[
                HotelReview(4.6, "Beautiful beach views, excellent service", "overall", True),
                HotelReview(4.5, "Great food options", "value_for_money", True),
            ],
            phone="+91-22-6789-1234",
            email="reserve@beachfrontparadise.com",
            website="www.beachfrontparadise.com",
            description="Premium beachfront hotel with stunning Arabian Sea views",
        ),
        Hotel(
            id="h004_mid_mumbai",
            name="City Central Mumbai",
            city="Mumbai",
            location="Fort, Mumbai",
            star_rating=3.8,
            price_range={"min": 4000, "max": 12000},
            rooms=[
                Room(RoomType.SINGLE, 4000, 1, [HotelAmenity.WIFI, HotelAmenity.AC]),
                Room(RoomType.DOUBLE, 8000, 2, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.TV]),
                Room(RoomType.DELUXE, 12000, 2, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.TV, HotelAmenity.GYM]),
            ],
            amenities=[
                HotelAmenity.WIFI, HotelAmenity.GYM, HotelAmenity.RESTAURANT,
                HotelAmenity.PARKING, HotelAmenity.VEGETARIAN_FOOD, HotelAmenity.WHEELCHAIR_ACCESS
            ],
            reviews=[
                HotelReview(4.0, "Centrally located, good for business", "location", True),
                HotelReview(3.9, "Decent rooms", "overall", True),
            ],
            phone="+91-22-5678-1234",
            email="info@citycentral.com",
            description="Modern hotel in the business district with good connectivity",
        ),
    ]

    # Goa Hotels
    goa_hotels = [
        Hotel(
            id="h005_goa_resort",
            name="Tropical Goa Resort",
            city="Goa",
            location="Baga Beach, Goa",
            star_rating=4.3,
            price_range={"min": 7000, "max": 18000},
            rooms=[
                Room(RoomType.DOUBLE, 7000, 2, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.BEACH_VIEW, HotelAmenity.POOL]),
                Room(RoomType.DELUXE, 12000, 2, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.BEACH_VIEW, HotelAmenity.POOL, HotelAmenity.SPA]),
                Room(RoomType.FAMILY, 18000, 4, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.BEACH_VIEW, HotelAmenity.POOL, HotelAmenity.KIDS_PLAY_AREA]),
            ],
            amenities=[
                HotelAmenity.WIFI, HotelAmenity.POOL, HotelAmenity.BEACH_VIEW, HotelAmenity.SPA,
                HotelAmenity.RESTAURANT, HotelAmenity.VEGETARIAN_FOOD, HotelAmenity.FAMILY_ROOMS,
                HotelAmenity.KIDS_PLAY_AREA, HotelAmenity.PARKING
            ],
            reviews=[
                HotelReview(4.4, "Paradise on earth!", "overall", True),
                HotelReview(4.5, "Family-friendly with great activities", "value_for_money", True),
            ],
            phone="+91-832-1234-567",
            email="stay@tropicalgoaresort.com",
            website="www.tropicalgoaresort.com",
            description="Beautiful beachfront resort perfect for family vacations",
        ),
        Hotel(
            id="h006_budget_goa",
            name="Coastal Budget Stay",
            city="Goa",
            location="Colva, Goa",
            star_rating=3.2,
            price_range={"min": 1500, "max": 4000},
            rooms=[
                Room(RoomType.SINGLE, 1500, 1, [HotelAmenity.WIFI, HotelAmenity.AC]),
                Room(RoomType.DOUBLE, 2500, 2, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.TV]),
                Room(RoomType.FAMILY, 4000, 4, [HotelAmenity.WIFI, HotelAmenity.AC, HotelAmenity.TV, HotelAmenity.KIDS_PLAY_AREA]),
            ],
            amenities=[
                HotelAmenity.WIFI, HotelAmenity.RESTAURANT, HotelAmenity.VEGETARIAN_FOOD,
                HotelAmenity.BEACH_VIEW, HotelAmenity.PARKING
            ],
            reviews=[
                HotelReview(3.5, "Good value for beach location", "value_for_money", True),
                HotelReview(3.3, "Basic but clean rooms", "cleanliness", True),
            ],
            phone="+91-832-2234-567",
            email="info@coastalbudgetstay.com",
            description="Affordable beachside accommodation with basic amenities",
        ),
    ]

    return {
        "Delhi": delhi_hotels,
        "Mumbai": mumbai_hotels,
        "Goa": goa_hotels,
    }


def get_hotels_by_city(city: str) -> list:
    """Get all hotels in a specific city"""
    hotels_db = get_mock_hotels()
    return hotels_db.get(city, [])


def search_hotels(city: str, max_price: float = None, min_stars: float = 0.0) -> list:
    """Search hotels by city and optional filters"""
    hotels = get_hotels_by_city(city)

    results = []
    for hotel in hotels:
        # Check price
        if max_price and hotel.price_range['min'] > max_price:
            continue

        # Check star rating
        if hotel.star_rating < min_stars:
            continue

        results.append(hotel)

    return results

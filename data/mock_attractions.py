"""Mock attractions database for Yatra Tours Agent"""

from models.attraction import (
    Attraction, Review, Amenity, AttractionType, DifficultyLevel, CrowdLevel
)


def create_mock_attractions() -> dict:
    """Create mock attractions database by city"""

    goa_attractions = [
        Attraction(
            id="goa_beach_001",
            name="Baga Beach",
            description="Popular beach known for water sports and vibrant nightlife",
            city="Goa",
            locality="Baga",
            attraction_type=AttractionType.BEACH,
            rating=4.6,
            num_reviews=1250,
            reviews=[
                Review("Tourist Jane", 5.0, "Beautiful beach, great for swimming", "2026-06-15", 145),
                Review("Local Ravi", 4.5, "Crowded but fun", "2026-06-10", 98),
            ],
            opening_time="06:00",
            closing_time="22:00",
            entry_fee=0,
            best_time_to_visit="Morning",
            duration_hours=3.0,
            distance_from_city_center=8.0,
            difficulty_level=DifficultyLevel.EASY,
            kid_friendly=True,
            senior_friendly=True,
            wheelchair_accessible=False,
            peak_season="Dec-Feb",
            best_days=["Weekday"],
            typical_crowd_level=CrowdLevel.HIGH,
            crowd_by_time={"morning": "Moderate", "afternoon": "High", "evening": "Very High"},
            amenities=[
                Amenity("Parking", True),
                Amenity("Beach Shacks", True),
                Amenity("Restrooms", True),
                Amenity("Water Sports Equipment", True),
            ],
            activities_available=["Swimming", "Water Sports", "Jet Ski", "Parasailing"],
            highlights=["Golden sand", "Clear water", "Water sports hub"],
            phone="0832-2234567",
            website="https://bagabeach.goa.gov.in",
            address="Baga Beach Road, Goa",
        ),

        Attraction(
            id="goa_temple_001",
            name="Mangeshi Temple",
            description="Ancient Hindu temple dedicated to Lord Mangesh",
            city="Goa",
            locality="Ponda",
            attraction_type=AttractionType.TEMPLE,
            rating=4.4,
            num_reviews=456,
            reviews=[
                Review("Priya D.", 4.5, "Spiritual and peaceful", "2026-06-12", 67),
                Review("Hari M.", 4.5, "Beautiful architecture", "2026-06-08", 52),
            ],
            opening_time="06:00",
            closing_time="20:00",
            entry_fee=0,
            best_time_to_visit="Morning",
            duration_hours=1.5,
            distance_from_city_center=20.0,
            difficulty_level=DifficultyLevel.EASY,
            kid_friendly=True,
            senior_friendly=True,
            wheelchair_accessible=True,
            peak_season="Oct-Feb",
            best_days=["Weekday"],
            typical_crowd_level=CrowdLevel.MODERATE,
            crowd_by_time={"morning": "Moderate", "afternoon": "Low", "evening": "High"},
            amenities=[
                Amenity("Parking", True),
                Amenity("Restrooms", True),
                Amenity("Prasad Counter", True),
            ],
            activities_available=["Prayer", "Photography", "Cultural Learning"],
            highlights=["Ancient architecture", "Spiritual atmosphere", "Prasad offering"],
            phone="0832-2245678",
            website="https://mangeshi.com",
            address="Ponda, Goa",
        ),

        Attraction(
            id="goa_fort_001",
            name="Aguada Fort",
            description="Historic 17th century Portuguese fort with lighthouse",
            city="Goa",
            locality="Candolim",
            attraction_type=AttractionType.FORT,
            rating=4.5,
            num_reviews=892,
            reviews=[
                Review("History Buff", 4.5, "Amazing views and history", "2026-06-13", 123),
                Review("Sarah K.", 4.5, "Perfect for sunset", "2026-06-11", 89),
            ],
            opening_time="09:00",
            closing_time="18:00",
            entry_fee=100,
            best_time_to_visit="Afternoon",
            duration_hours=2.0,
            distance_from_city_center=12.0,
            difficulty_level=DifficultyLevel.EASY,
            kid_friendly=True,
            senior_friendly=True,
            wheelchair_accessible=False,
            peak_season="Oct-Mar",
            best_days=["Weekday"],
            typical_crowd_level=CrowdLevel.MODERATE,
            crowd_by_time={"morning": "Low", "afternoon": "Moderate", "evening": "High"},
            amenities=[
                Amenity("Parking", True),
                Amenity("Restrooms", True),
                Amenity("Cafeteria", True),
                Amenity("Gift Shop", True),
            ],
            activities_available=["Sightseeing", "Photography", "Historical Tour", "Sunset Viewing"],
            highlights=["Lighthouse", "Sea views", "Historical architecture", "Sunset point"],
            phone="0832-2256789",
            website="https://aguadafort.goa.gov.in",
            address="Fort Aguada, Candolim, Goa",
        ),

        Attraction(
            id="goa_water_001",
            name="Dudhsagar Waterfall",
            description="Majestic 310m waterfall in Western Ghats",
            city="Goa",
            locality="Mollem",
            attraction_type=AttractionType.NATURE,
            rating=4.7,
            num_reviews=1050,
            reviews=[
                Review("Adventurer Mike", 5.0, "Breathtaking! Best waterfall in India", "2026-06-14", 234),
                Review("Trekker Ann", 4.5, "Amazing trek, bring good shoes", "2026-06-09", 156),
            ],
            opening_time="06:00",
            closing_time="18:00",
            entry_fee=50,
            best_time_to_visit="Morning",
            duration_hours=4.0,
            distance_from_city_center=45.0,
            difficulty_level=DifficultyLevel.MODERATE,
            kid_friendly=True,
            senior_friendly=False,
            wheelchair_accessible=False,
            peak_season="May-Aug",
            best_days=["Weekday"],
            typical_crowd_level=CrowdLevel.HIGH,
            crowd_by_time={"morning": "Moderate", "afternoon": "High", "evening": "Low"},
            amenities=[
                Amenity("Parking", True),
                Amenity("Basic Restrooms", True),
                Amenity("Local Guides", True),
            ],
            activities_available=["Trekking", "Swimming", "Photography", "Nature Walk"],
            highlights=["Waterfall", "Monsoon flows", "Jungle trek", "Natural pool"],
            phone="0832-2267890",
            website="https://dudhsagar.goa.gov.in",
            address="Mollem, Goa",
        ),

        Attraction(
            id="goa_market_001",
            name="Anjuna Flea Market",
            description="Famous Wednesday flea market with local crafts and souvenirs",
            city="Goa",
            locality="Anjuna",
            attraction_type=AttractionType.MARKET,
            rating=4.2,
            num_reviews=678,
            reviews=[
                Review("Shopper Lisa", 4.0, "Great bargains, crowded but fun", "2026-06-13", 78),
                Review("Local Vendor", 4.5, "Best place for souvenirs", "2026-06-10", 65),
            ],
            opening_time="09:00",
            closing_time="17:00",
            entry_fee=0,
            best_time_to_visit="Morning",
            duration_hours=2.5,
            distance_from_city_center=15.0,
            difficulty_level=DifficultyLevel.EASY,
            kid_friendly=True,
            senior_friendly=False,
            wheelchair_accessible=False,
            peak_season="Oct-May",
            best_days=["Wednesday"],
            typical_crowd_level=CrowdLevel.VERY_HIGH,
            crowd_by_time={"morning": "High", "afternoon": "Very High", "evening": "High"},
            amenities=[
                Amenity("Parking", False),
                Amenity("Food Stalls", True),
                Amenity("Restrooms", False),
                Amenity("ATM", True),
            ],
            activities_available=["Shopping", "Bargaining", "People Watching", "Photography"],
            highlights=["Local crafts", "Souvenirs", "Spices", "Textiles"],
            phone="0832-2278901",
            address="Anjuna Beach Road, Goa",
        ),

        Attraction(
            id="goa_water_sports_001",
            name="Banana Boat Rides",
            description="Exciting water sports activity at Calangute Beach",
            city="Goa",
            locality="Calangute",
            attraction_type=AttractionType.WATER_SPORTS,
            rating=4.3,
            num_reviews=523,
            reviews=[
                Review("Thrill Seeker Tom", 4.5, "Super fun and safe", "2026-06-12", 94),
                Review("Family Mom", 4.0, "Kids loved it", "2026-06-08", 72),
            ],
            opening_time="08:00",
            closing_time="17:00",
            entry_fee=300,  # Per person
            best_time_to_visit="Morning",
            duration_hours=1.0,
            distance_from_city_center=10.0,
            difficulty_level=DifficultyLevel.EASY,
            kid_friendly=True,
            senior_friendly=False,
            wheelchair_accessible=False,
            peak_season="Oct-May",
            best_days=["Weekday", "Weekend"],
            typical_crowd_level=CrowdLevel.HIGH,
            crowd_by_time={"morning": "Moderate", "afternoon": "High", "evening": "Low"},
            amenities=[
                Amenity("Beach Shack", True),
                Amenity("Restrooms", True),
                Amenity("Life Jackets", True),
                Amenity("First Aid", True),
            ],
            activities_available=["Banana Boat", "Jet Ski", "Speedboat", "Parasailing"],
            highlights=["Adrenaline rush", "Sea views", "Professional guides", "Safety gear"],
            phone="0832-2289012",
            address="Calangute Beach, Goa",
        ),
    ]

    return {
        "goa": goa_attractions,
    }


def get_attractions_by_city(city: str) -> list:
    """Get all attractions in a city"""
    db = create_mock_attractions()
    return db.get(city.lower(), [])


def search_attractions(
    city: str,
    attraction_type: str = None,
    difficulty: str = None,
    min_rating: float = 0
) -> list:
    """Search attractions by city and filters"""
    attractions = get_attractions_by_city(city)

    # Filter by type
    if attraction_type:
        type_lower = attraction_type.lower()
        attractions = [
            a for a in attractions
            if a.attraction_type.value.lower() == type_lower
        ]

    # Filter by difficulty
    if difficulty:
        difficulty_lower = difficulty.lower()
        attractions = [
            a for a in attractions
            if a.difficulty_level.value.lower() == difficulty_lower
        ]

    # Filter by rating
    if min_rating > 0:
        attractions = [a for a in attractions if a.rating >= min_rating]

    return attractions


def get_attraction_by_id(attraction_id: str) -> Attraction:
    """Get attraction by ID"""
    for city_attractions in create_mock_attractions().values():
        for attraction in city_attractions:
            if attraction.id == attraction_id:
                return attraction
    return None

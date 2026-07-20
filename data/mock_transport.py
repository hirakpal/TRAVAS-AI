"""Mock transport database for Safar Travel Agent"""

from models.transport import (
    Journey, LocalTransport, Review, Amenity, TransportType, ComfortLevel, AmenityType
)


def create_mock_journeys() -> dict:
    """Create mock journey database"""

    delhi_to_goa_flights = [
        Journey(
            id="flight_001",
            transport_type=TransportType.FLIGHT,
            departure_city="Delhi",
            arrival_city="Goa",
            departure_time="06:00",
            arrival_time="08:30",
            duration_hours=2.5,
            price_per_person=2500,
            comfort_level=ComfortLevel.ECONOMY,
            operator_name="IndiGo",
            operator_phone="1800-180-3131",
            operator_website="https://www.goindigo.in",
            rating=4.5,
            num_reviews=2340,
            reviews=[
                Review("Business Traveler", 4.5, "On time, good service", "2026-06-15", 234),
                Review("Family Mom", 4.5, "Clean and comfortable", "2026-06-10", 156),
            ],
            amenities=[
                Amenity(AmenityType.AC, True),
                Amenity(AmenityType.MEALS, True),
                Amenity(AmenityType.ENTERTAINMENT, True),
                Amenity(AmenityType.LUGGAGE, True),
            ],
            stops=[],
            seats_available=45,
            can_book_online=True,
            cancellation_policy="Free cancellation up to 24 hours",
            kid_friendly=True,
            senior_friendly=True,
            wheelchair_accessible=True,
            departure_date="2026-07-25",
        ),

        Journey(
            id="flight_002",
            transport_type=TransportType.FLIGHT,
            departure_city="Delhi",
            arrival_city="Goa",
            departure_time="14:30",
            arrival_time="17:00",
            duration_hours=2.5,
            price_per_person=3200,
            comfort_level=ComfortLevel.BUSINESS,
            operator_name="Air India",
            operator_phone="1800-180-1407",
            operator_website="https://www.airindia.in",
            rating=4.4,
            num_reviews=1856,
            reviews=[
                Review("Executive", 4.5, "Premium service", "2026-06-14", 189),
                Review("Frequent Flyer", 4.3, "Good seats", "2026-06-11", 134),
            ],
            amenities=[
                Amenity(AmenityType.AC, True),
                Amenity(AmenityType.MEALS, True),
                Amenity(AmenityType.BLANKET, True),
                Amenity(AmenityType.PILLOW, True),
                Amenity(AmenityType.ENTERTAINMENT, True),
                Amenity(AmenityType.CHARGING, True),
            ],
            stops=[],
            seats_available=28,
            can_book_online=True,
            cancellation_policy="Free cancellation up to 48 hours",
            kid_friendly=True,
            senior_friendly=True,
            wheelchair_accessible=True,
            departure_date="2026-07-25",
        ),
    ]

    delhi_to_goa_trains = [
        Journey(
            id="train_001",
            transport_type=TransportType.TRAIN,
            departure_city="Delhi",
            arrival_city="Goa",
            departure_time="19:15",
            arrival_time="11:45",
            duration_hours=16.5,
            price_per_person=1200,
            comfort_level=ComfortLevel.STANDARD,
            operator_name="Indian Railways",
            operator_phone="1800-111-139",
            operator_website="https://www.irctc.co.in",
            rating=4.2,
            num_reviews=1234,
            reviews=[
                Review("Budget Traveler", 4.0, "Affordable, crowded", "2026-06-13", 156),
                Review("Long Journey Fan", 4.5, "Comfortable berth", "2026-06-09", 124),
            ],
            amenities=[
                Amenity(AmenityType.AC, True),
                Amenity(AmenityType.MEALS, True),
                Amenity(AmenityType.BLANKET, True),
                Amenity(AmenityType.WASHROOM, True),
                Amenity(AmenityType.LUGGAGE, True),
            ],
            stops=[],
            seats_available=120,
            can_book_online=True,
            cancellation_policy="Partial refund up to 72 hours",
            kid_friendly=True,
            senior_friendly=True,
            wheelchair_accessible=False,
            departure_date="2026-07-25",
        ),
    ]

    goa_local_transport = [
        LocalTransport(
            id="taxi_goa_001",
            name="GoaTaxi Plus",
            transport_type=TransportType.TAXI,
            vehicle_model="Maruti Swift",
            capacity=4,
            service_city="Goa",
            available_24_7=True,
            price_per_km=12.0,
            ac=True,
            wifi=True,
            wheelchair_accessible=False,
            luggage_space=True,
            rating=4.6,
            num_reviews=1567,
            reviews=[
                Review("Tourist Kumar", 4.5, "Clean car, friendly driver", "2026-06-15", 234),
                Review("Business Person", 4.5, "Professional service", "2026-06-12", 189),
            ],
            can_book_online=True,
            response_time_minutes=5,
            phone="0832-2234567",
            website="https://goataxiplus.com",
        ),

        LocalTransport(
            id="auto_goa_001",
            name="GoaAuto",
            transport_type=TransportType.AUTO_RICKSHAW,
            vehicle_model="Bajaj Auto",
            capacity=3,
            service_city="Goa",
            available_24_7=True,
            price_per_km=8.0,
            ac=False,
            wifi=False,
            wheelchair_accessible=False,
            luggage_space=True,
            rating=3.8,
            num_reviews=892,
            reviews=[
                Review("Budget Tourist", 4.0, "Cheap and cheerful", "2026-06-14", 123),
                Review("Local Traveler", 3.5, "Sometimes traffic", "2026-06-10", 98),
            ],
            can_book_online=True,
            response_time_minutes=10,
            phone="0832-2245678",
        ),

        LocalTransport(
            id="car_rental_001",
            name="GoanDrive Car Rentals",
            transport_type=TransportType.CAR_RENTAL,
            vehicle_model="Hyundai Creta",
            capacity=5,
            service_city="Goa",
            available_24_7=True,
            hourly_rate=800.0,
            ac=True,
            wifi=False,
            wheelchair_accessible=False,
            luggage_space=True,
            rating=4.4,
            num_reviews=623,
            reviews=[
                Review("Family Traveler", 4.5, "Perfect for family trip", "2026-06-13", 178),
                Review("Adventure Seeker", 4.3, "Good vehicle condition", "2026-06-08", 145),
            ],
            can_book_online=True,
            response_time_minutes=15,
            phone="0832-2256789",
            website="https://goandrive.com",
        ),

        LocalTransport(
            id="ferry_001",
            name="Goa Coastal Ferries",
            transport_type=TransportType.FERRY,
            vehicle_model="Tourist Ferry",
            capacity=50,
            service_city="Goa",
            available_24_7=False,
            flat_price=100.0,  # Per person
            ac=True,
            wifi=True,
            wheelchair_accessible=True,
            luggage_space=True,
            rating=4.3,
            num_reviews=456,
            reviews=[
                Review("Adventure Couple", 4.5, "Scenic river views", "2026-06-12", 167),
                Review("Tourist Family", 4.0, "Good experience", "2026-06-09", 134),
            ],
            can_book_online=True,
            response_time_minutes=20,
            phone="0832-2267890",
            website="https://goaferry.com",
        ),
    ]

    return {
        "flights": {
            "delhi_to_goa": delhi_to_goa_flights,
        },
        "trains": {
            "delhi_to_goa": delhi_to_goa_trains,
        },
        "local_transport": {
            "goa": goa_local_transport,
        }
    }


def search_flights(departure_city: str, arrival_city: str, max_price: float = None) -> list:
    """Search flights"""
    db = create_mock_journeys()
    flights = db.get("flights", {}).get(f"{departure_city.lower()}_to_{arrival_city.lower()}", [])

    if max_price:
        flights = [f for f in flights if f.price_per_person <= max_price]

    return flights


def search_trains(departure_city: str, arrival_city: str, max_price: float = None) -> list:
    """Search trains"""
    db = create_mock_journeys()
    trains = db.get("trains", {}).get(f"{departure_city.lower()}_to_{arrival_city.lower()}", [])

    if max_price:
        trains = [t for t in trains if t.price_per_person <= max_price]

    return trains


def search_local_transport(city: str, transport_type: str = None) -> list:
    """Search local transport in a city"""
    db = create_mock_journeys()
    transports = db.get("local_transport", {}).get(city.lower(), [])

    if transport_type:
        type_lower = transport_type.lower()
        transports = [
            t for t in transports
            if t.transport_type.value.lower() == type_lower
        ]

    return transports


def get_journey_by_id(journey_id: str) -> Journey:
    """Get journey by ID"""
    db = create_mock_journeys()
    for journey_list in db.get("flights", {}).values():
        for journey in journey_list:
            if journey.id == journey_id:
                return journey

    for journey_list in db.get("trains", {}).values():
        for journey in journey_list:
            if journey.id == journey_id:
                return journey

    return None


def get_local_transport_by_id(transport_id: str) -> LocalTransport:
    """Get local transport by ID"""
    db = create_mock_journeys()
    for transports in db.get("local_transport", {}).values():
        for transport in transports:
            if transport.id == transport_id:
                return transport

    return None

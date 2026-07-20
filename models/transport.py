"""Transport domain models for Safar Travel Agent"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class TransportType(Enum):
    """Types of transport"""
    FLIGHT = "Flight"
    TRAIN = "Train"
    BUS = "Bus"
    CAR_RENTAL = "Car Rental"
    TAXI = "Taxi"
    AUTO_RICKSHAW = "Auto Rickshaw"
    FERRY = "Ferry"


class ComfortLevel(Enum):
    """Comfort/Class of transport"""
    ECONOMY = "Economy"
    BUSINESS = "Business"
    PREMIUM = "Premium"
    LUXURY = "Luxury"
    STANDARD = "Standard"
    DELUXE = "Deluxe"


class AmenityType(Enum):
    """Transport amenities"""
    WIFI = "WiFi"
    MEALS = "Meals Included"
    AC = "Air Conditioning"
    CHARGING = "USB Charging"
    ENTERTAINMENT = "Entertainment System"
    BLANKET = "Blanket"
    PILLOW = "Pillow"
    WASHROOM = "Onboard Washroom"
    LUGGAGE = "Luggage Space"
    WHEELCHAIR_ACCESS = "Wheelchair Access"


@dataclass
class Review:
    """Transport review"""
    reviewer_name: str
    rating: float  # 1-5
    comment: str
    date: str  # ISO format
    helpful_count: int = 0


@dataclass
class Amenity:
    """Transport amenity"""
    name: AmenityType
    available: bool = True


@dataclass
class Journey:
    """Journey details for a transport option"""
    id: str
    transport_type: TransportType

    # Route info
    departure_city: str
    arrival_city: str
    departure_time: str  # HH:MM
    arrival_time: str  # HH:MM
    duration_hours: float

    # Pricing
    price_per_person: float  # In INR
    comfort_level: ComfortLevel

    # Operator
    operator_name: str  # Airline, Railway, Bus company
    operator_phone: Optional[str] = None
    operator_website: Optional[str] = None

    # Ratings & Reviews
    rating: float = 4.0  # 1-5
    num_reviews: int = 0
    reviews: List[Review] = field(default_factory=list)

    # Features
    amenities: List[Amenity] = field(default_factory=list)
    stops: List[str] = field(default_factory=list)  # Number of stops

    # Booking & Availability
    seats_available: int = 0
    can_book_online: bool = True
    cancellation_policy: str = "7 days free cancellation"

    # Suitability
    kid_friendly: bool = True
    senior_friendly: bool = True
    wheelchair_accessible: bool = False
    pet_friendly: bool = False

    # Special info
    notes: str = ""
    departure_date: str = ""  # ISO format


    def get_average_rating(self) -> float:
        """Calculate average rating from reviews"""
        if not self.reviews:
            return self.rating
        return sum(r.rating for r in self.reviews) / len(self.reviews)

    def get_journey_type(self) -> str:
        """Get journey type (direct, one-stop, etc.)"""
        if not self.stops:
            return "Direct"
        return f"{len(self.stops)} stop(s)"

    def is_suitable_for_kids(self) -> bool:
        """Check if suitable for children"""
        return self.kid_friendly

    def is_suitable_for_seniors(self) -> bool:
        """Check if suitable for elderly"""
        return self.senior_friendly and self.duration_hours <= 8

    def is_accessible(self) -> bool:
        """Check if wheelchair accessible"""
        return self.wheelchair_accessible

    def __repr__(self) -> str:
        return f"<Journey {self.operator_name} {self.departure_city}->{self.arrival_city} ₹{self.price_per_person}>"


@dataclass
class LocalTransport:
    """Local transport option (taxi, auto, car rental)"""
    id: str
    name: str
    transport_type: TransportType

    # Vehicle info
    vehicle_model: str
    capacity: int  # Number of passengers

    # Service area
    service_city: str
    available_24_7: bool = True

    # Pricing
    price_per_km: Optional[float] = None  # For taxis
    hourly_rate: Optional[float] = None  # For rentals
    flat_price: Optional[float] = None  # For specific routes

    # Features
    ac: bool = True
    wifi: bool = False
    wheelchair_accessible: bool = False
    luggage_space: bool = True

    # Ratings
    rating: float = 4.0
    num_reviews: int = 0
    reviews: List[Review] = field(default_factory=list)

    # Booking
    can_book_online: bool = True
    response_time_minutes: int = 5

    # Contact
    phone: str = ""
    website: Optional[str] = None


    def get_average_rating(self) -> float:
        """Calculate average rating"""
        if not self.reviews:
            return self.rating
        return sum(r.rating for r in self.reviews) / len(self.reviews)

    def is_accessible(self) -> bool:
        """Check if wheelchair accessible"""
        return self.wheelchair_accessible

    def __repr__(self) -> str:
        return f"<LocalTransport {self.name} in {self.service_city}>"


@dataclass
class TransportPreferences:
    """User's transport preferences"""
    # Route preferences
    departure_city: Optional[str] = None
    arrival_city: Optional[str] = None
    departure_date: Optional[str] = None

    # Preferences
    preferred_transport_types: List[str] = field(default_factory=list)  # Flight, Train, etc.
    comfort_level: str = "Economy"  # Economy, Business, Premium
    max_price: Optional[float] = None
    max_duration_hours: Optional[float] = None

    # Suitability
    need_wheelchair_access: bool = False
    has_kids: bool = False
    has_seniors: bool = False
    has_pets: bool = False

    # Preferences
    prefer_direct_journey: bool = False
    prefer_morning: bool = False
    prefer_evening: bool = False

    # Special requirements
    luggage_requirement: int = 0  # Number of bags
    prefer_meal_included: bool = False


@dataclass
class TransportItinerary:
    """Daily local transport plan"""
    day: int
    date: str
    journeys: List[dict] = field(default_factory=list)  # List of local transport options
    estimated_cost: float = 0
    estimated_travel_time: float = 0
    description: str = ""

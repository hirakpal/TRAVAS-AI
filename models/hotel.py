"""Hotel Information Models"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class HotelInfo:
    """Basic hotel information"""

    name: str
    address: str
    locality: str
    city: str
    country: str = "India"

    # Contact
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

    # Distance Information
    distance_from_airport_km: Optional[float] = None
    distance_from_station_km: Optional[float] = None
    distance_from_city_center_km: Optional[float] = None

    # Rating & Reviews
    star_rating: Optional[float] = None  # 1-5 stars
    google_rating: Optional[float] = None  # 1-5 stars
    review_count: int = 0
    verified: bool = True  # Whether info is verified

    # Pricing
    price_range_low: Optional[float] = None
    price_range_high: Optional[float] = None
    currency: str = "INR"

    # Check-in/Check-out
    check_in_time: str = "14:00"
    check_out_time: str = "11:00"
    early_checkin_available: bool = False
    late_checkout_available: bool = False

    # Amenities
    amenities: List[str] = field(default_factory=list)
    # pool, spa, gym, restaurant, room-service, wifi, breakfast, etc.

    # Room Types
    room_types: List[str] = field(default_factory=list)
    # standard, deluxe, suite, family-room, villa, studio

    # Bed Options
    bed_options: List[str] = field(default_factory=list)
    # single, double, queen, king, twin

    # Parking
    has_parking: bool = False
    parking_type: Optional[str] = None  # free, paid, valet
    parking_cost: Optional[float] = None

    # Food Options
    vegetarian_food: bool = False
    vegan_food: bool = False
    jain_food: bool = False
    halal_food: bool = False
    breakfast_included: bool = False
    has_restaurant: bool = False
    has_bar: bool = False

    # Accessibility
    wheelchair_accessible: bool = False
    has_elevator: bool = False
    accessible_bathroom: bool = False
    step_free_entrance: bool = False

    # Policies
    pet_friendly: bool = False
    smoking_allowed: bool = False
    cancellation_policy: Optional[str] = None
    luggage_storage: bool = False
    luggage_storage_free: bool = True

    # Services
    concierge_24_7: bool = False
    airport_shuttle: bool = False
    laundry_service: bool = False
    business_center: bool = False

    # Special Features
    ev_charging: bool = False
    kids_club: bool = False
    conference_rooms: bool = False
    spa_services: bool = False

    # Languages Spoken
    languages: List[str] = field(default_factory=list)

    # Additional Info
    established_year: Optional[int] = None
    number_of_rooms: Optional[int] = None
    number_of_floors: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "address": self.address,
            "locality": self.locality,
            "city": self.city,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "rating": {
                "star": self.star_rating,
                "google": self.google_rating,
                "reviews": self.review_count,
            },
            "price": {
                "low": self.price_range_low,
                "high": self.price_range_high,
                "currency": self.currency,
            },
            "amenities": self.amenities,
            "room_types": self.room_types,
            "bed_options": self.bed_options,
            "parking": {
                "available": self.has_parking,
                "type": self.parking_type,
                "cost": self.parking_cost,
            },
            "food": {
                "vegetarian": self.vegetarian_food,
                "vegan": self.vegan_food,
                "jain": self.jain_food,
                "halal": self.halal_food,
                "breakfast_included": self.breakfast_included,
            },
            "accessibility": {
                "wheelchair": self.wheelchair_accessible,
                "elevator": self.has_elevator,
                "accessible_bathroom": self.accessible_bathroom,
                "step_free": self.step_free_entrance,
            },
        }


@dataclass
class Hotel:
    """Complete hotel information with reviews"""

    info: HotelInfo

    # Reviews & Sentiment
    reviews: List[str] = field(default_factory=list)
    positive_review_summary: Optional[str] = None
    negative_review_summary: Optional[str] = None
    overall_sentiment: Optional[str] = None  # positive, neutral, negative

    # Nearest Attractions
    nearby_attractions: List[str] = field(default_factory=list)
    nearby_restaurants: List[str] = field(default_factory=list)
    nearby_shopping: List[str] = field(default_factory=list)

    # Transportation
    public_transport_nearby: List[str] = field(default_factory=list)
    # metro, bus, taxi, etc.

    # Special Notes
    notes: Optional[str] = None
    last_updated: Optional[str] = None

    def get_summary(self) -> Dict:
        """Get hotel summary for recommendation"""
        return {
            "name": self.info.name,
            "location": f"{self.info.locality}, {self.info.city}",
            "rating": self.info.google_rating,
            "price_range": f"{self.info.price_range_low}-{self.info.price_range_high} {self.info.currency}",
            "key_amenities": self.info.amenities[:5],
            "room_types": self.info.room_types,
            "review_count": self.info.review_count,
            "positive_highlights": self.positive_review_summary,
            "concerns": self.negative_review_summary,
        }

    def matches_preference(
        self,
        budget: Optional[float] = None,
        amenities: Optional[List[str]] = None,
        room_type: Optional[str] = None,
        dietary: Optional[List[str]] = None,
    ) -> float:
        """
        Calculate match score (0-1) based on preferences.

        Args:
            budget: Maximum price per night
            amenities: Required amenities
            room_type: Preferred room type
            dietary: Dietary requirements

        Returns:
            Match score (0-1)
        """
        score = 0.0
        total_criteria = 0

        # Budget match
        if budget is not None:
            total_criteria += 1
            if self.info.price_range_high and self.info.price_range_high <= budget:
                score += 1.0
            elif self.info.price_range_low and self.info.price_range_low <= budget:
                score += 0.5

        # Amenities match
        if amenities:
            total_criteria += 1
            matched = sum(1 for a in amenities if a in self.info.amenities)
            score += matched / len(amenities) if amenities else 0

        # Room type match
        if room_type:
            total_criteria += 1
            if room_type in self.info.room_types:
                score += 1.0

        # Dietary match
        if dietary:
            total_criteria += 1
            dietary_match = 0
            if "vegetarian" in dietary and self.info.vegetarian_food:
                dietary_match += 1
            if "vegan" in dietary and self.info.vegan_food:
                dietary_match += 1
            if "jain" in dietary and self.info.jain_food:
                dietary_match += 1
            if "halal" in dietary and self.info.halal_food:
                dietary_match += 1
            score += dietary_match / len(dietary) if dietary else 0

        return score / total_criteria if total_criteria > 0 else 0.5

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "hotel_info": self.info.to_dict(),
            "reviews": {
                "positive_summary": self.positive_review_summary,
                "negative_summary": self.negative_review_summary,
                "overall_sentiment": self.overall_sentiment,
            },
            "nearby": {
                "attractions": self.nearby_attractions,
                "restaurants": self.nearby_restaurants,
                "shopping": self.nearby_shopping,
                "transport": self.public_transport_nearby,
            },
        }

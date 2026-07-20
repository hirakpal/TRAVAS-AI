"""Hotel data models for TRAVAS system."""

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum


class HotelAmenity(str, Enum):
    """Hotel amenities"""
    WIFI = "wifi"
    POOL = "pool"
    GYM = "gym"
    SPA = "spa"
    RESTAURANT = "restaurant"
    PARKING = "parking"
    AC = "ac"
    TV = "tv"
    HOT_WATER = "hot_water"
    WHEELCHAIR_ACCESS = "wheelchair_access"
    FAMILY_ROOMS = "family_rooms"
    KIDS_PLAY_AREA = "kids_play_area"
    VEGETARIAN_FOOD = "vegetarian_food"
    BEACH_VIEW = "beach_view"
    MOUNTAIN_VIEW = "mountain_view"


class RoomType(str, Enum):
    """Types of rooms available"""
    SINGLE = "single"
    DOUBLE = "double"
    DELUXE = "deluxe"
    SUITE = "suite"
    FAMILY = "family"


@dataclass
class Room:
    """Hotel room information"""
    type: RoomType
    price_per_night: float  # in INR
    capacity: int
    amenities: List[HotelAmenity]
    available: bool = True


@dataclass
class HotelReview:
    """User review for a hotel"""
    rating: float  # 1.0 to 5.0
    comment: str
    category: str  # "cleanliness", "service", "location", "value_for_money", "overall"
    verified: bool = True


@dataclass
class Hotel:
    """Hotel information model"""
    id: str
    name: str
    city: str
    location: str  # Neighborhood or area
    star_rating: float  # 1.0 to 5.0
    price_range: Dict[str, float]  # {"min": 2000, "max": 5000}
    rooms: List[Room]
    amenities: List[HotelAmenity]
    reviews: List[HotelReview]
    phone: str
    email: str
    website: Optional[str] = None
    description: str = ""
    checkin_time: str = "14:00"
    checkout_time: str = "11:00"
    cancellation_policy: str = "Free cancellation until 24 hours before check-in"

    @property
    def average_rating(self) -> float:
        """Calculate average rating from reviews"""
        if not self.reviews:
            return 0.0
        return sum(r.rating for r in self.reviews) / len(self.reviews)

    @property
    def total_reviews(self) -> int:
        """Get total number of reviews"""
        return len(self.reviews)

    def get_cheapest_room(self) -> Optional[Room]:
        """Get the cheapest available room"""
        available_rooms = [r for r in self.rooms if r.available]
        if not available_rooms:
            return None
        return min(available_rooms, key=lambda r: r.price_per_night)

    def get_room_by_type(self, room_type: RoomType) -> Optional[Room]:
        """Get room by type if available"""
        for room in self.rooms:
            if room.type == room_type and room.available:
                return room
        return None

    def has_amenity(self, amenity: HotelAmenity) -> bool:
        """Check if hotel has a specific amenity"""
        return amenity in self.amenities

    def matches_preferences(self, preferences: 'HotelPreference') -> bool:
        """Check if hotel matches user preferences"""
        # Check budget
        cheapest_room = self.get_cheapest_room()
        if not cheapest_room or cheapest_room.price_per_night > preferences.max_budget:
            return False

        # Check star rating
        if self.star_rating < preferences.min_star_rating:
            return False

        # Check required amenities
        if preferences.required_amenities:
            if not all(self.has_amenity(a) for a in preferences.required_amenities):
                return False

        return True

    def __repr__(self) -> str:
        return f"<Hotel {self.name} ({self.city}) - ₹{self.price_range['min']}-{self.price_range['max']}/night>"


@dataclass
class HotelPreference:
    """User preferences for hotel selection"""
    max_budget: float  # per night in INR
    min_star_rating: float = 3.0
    required_amenities: List[HotelAmenity] = None
    preferred_amenities: List[HotelAmenity] = None
    location_preference: Optional[str] = None
    room_type: Optional[RoomType] = None
    accessibility_needs: List[str] = None  # e.g., ["wheelchair_access", "elevator"]

    def __post_init__(self):
        if self.required_amenities is None:
            self.required_amenities = []
        if self.preferred_amenities is None:
            self.preferred_amenities = []
        if self.accessibility_needs is None:
            self.accessibility_needs = []

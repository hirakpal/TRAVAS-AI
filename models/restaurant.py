"""Restaurant domain models for Annapurna Food Agent"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class Cuisine(Enum):
    """Restaurant cuisine types"""
    INDIAN = "Indian"
    CHINESE = "Chinese"
    ITALIAN = "Italian"
    VEGETARIAN = "Vegetarian"
    VEGAN = "Vegan"
    JAIN = "Jain"
    SEAFOOD = "Seafood"
    CONTINENTAL = "Continental"
    NORTH_INDIAN = "North Indian"
    SOUTH_INDIAN = "South Indian"
    STREET_FOOD = "Street Food"
    FUSION = "Fusion"


class RestaurantType(Enum):
    """Types of restaurants"""
    FINE_DINING = "Fine Dining"
    CASUAL = "Casual"
    FAST_FOOD = "Fast Food"
    CAFE = "Cafe"
    BAKERY = "Bakery"
    FOOD_COURT = "Food Court"
    STREET_STALL = "Street Stall"
    FAMILY_STYLE = "Family Style"


class AmenityType(Enum):
    """Restaurant amenities"""
    WIFI = "Free WiFi"
    PARKING = "Parking"
    AC = "Air Conditioning"
    OUTDOOR_SEATING = "Outdoor Seating"
    KIDS_MENU = "Kids Menu"
    HIGHCHAIR = "Highchair"
    WHEELCHAIR_ACCESS = "Wheelchair Access"
    RESERVATIONS = "Reservations"
    LIVE_MUSIC = "Live Music"
    ROOFTOP = "Rooftop"
    DELIVERY = "Delivery"
    TAKEAWAY = "Takeaway"
    PRIVATE_ROOMS = "Private Rooms"


@dataclass
class Review:
    """Restaurant review"""
    reviewer_name: str
    rating: float  # 1-5
    comment: str
    date: str  # ISO format
    helpful_count: int = 0


@dataclass
class RestaurantAmenity:
    """Restaurant amenity with availability"""
    name: AmenityType
    available: bool = True


@dataclass
class Restaurant:
    """Restaurant model"""
    # Required fields (no defaults)
    id: str
    name: str
    address: str
    city: str
    locality: str
    cuisine_types: List[Cuisine]
    restaurant_type: RestaurantType
    phone: str
    rating: float  # Average rating 1-5
    avg_cost_per_person: float  # In INR
    price_range: str  # Budget/Mid-range/Premium/Luxury
    distance_from_city_center: float  # In km

    # Optional fields (with defaults)
    website: Optional[str] = None
    opening_time: str = "10:00"  # HH:MM
    closing_time: str = "23:00"  # HH:MM
    num_reviews: int = 0
    reviews: List[Review] = field(default_factory=list)
    amenities: List[RestaurantAmenity] = field(default_factory=list)
    dietary_options: List[str] = field(default_factory=list)
    special_dishes: List[str] = field(default_factory=list)
    distance_from_hotel: Optional[float] = None  # In km (if hotel known)
    busy_hours: List[str] = field(default_factory=list)  # e.g., ["12-1pm", "7-9pm"]

    def get_average_rating(self) -> float:
        """Calculate average rating from reviews"""
        if not self.reviews:
            return self.rating
        return sum(r.rating for r in self.reviews) / len(self.reviews)

    def matches_dietary_needs(self, dietary_restrictions: List[str]) -> bool:
        """Check if restaurant has required dietary options"""
        if not dietary_restrictions:
            return True

        for restriction in dietary_restrictions:
            if restriction.lower() not in [opt.lower() for opt in self.dietary_options]:
                return False
        return True

    def is_family_friendly(self) -> bool:
        """Check if restaurant is suitable for families with kids"""
        family_amenities = [
            AmenityType.KIDS_MENU,
            AmenityType.HIGHCHAIR,
            AmenityType.OUTDOOR_SEATING,
            AmenityType.AC
        ]

        available_amenities = [a.name for a in self.amenities if a.available]
        return any(amenity in available_amenities for amenity in family_amenities)

    def is_accessible(self) -> bool:
        """Check if wheelchair accessible"""
        return any(
            a.name == AmenityType.WHEELCHAIR_ACCESS and a.available
            for a in self.amenities
        )

    def has_delivery(self) -> bool:
        """Check if delivery available"""
        return any(
            a.name == AmenityType.DELIVERY and a.available
            for a in self.amenities
        )

    def __repr__(self) -> str:
        return f"<Restaurant name='{self.name}' rating={self.rating} cuisines={[c.value for c in self.cuisine_types]}>"


@dataclass
class DiningPreferences:
    """User's dining preferences"""
    dietary_restrictions: List[str] = field(default_factory=list)  # vegetarian, vegan, jain, etc.
    preferred_cuisines: List[str] = field(default_factory=list)
    price_range: Optional[str] = None  # Budget/Mid-range/Premium/Luxury
    min_rating: float = 3.5

    family_friendly: bool = False
    wheelchair_accessible: bool = False
    delivery_needed: bool = False

    must_have_amenities: List[str] = field(default_factory=list)

    special_occasions: List[str] = field(default_factory=list)  # anniversary, birthday, etc.
    ambiance_preference: Optional[str] = None  # casual, romantic, business, etc.

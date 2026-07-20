"""User Preferences Model"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Preferences:
    """User preferences for hotel recommendations"""

    # Budget
    budget_level: Optional[str] = None  # budget, mid-range, premium, luxury
    max_price_per_night: Optional[float] = None

    # Accommodation
    room_type_preference: List[str] = field(default_factory=list)
    bed_preference: Optional[str] = None
    bathroom_type: Optional[str] = None

    # Dietary
    dietary_restrictions: List[str] = field(default_factory=list)

    # Accessibility
    accessibility_requirements: List[str] = field(default_factory=list)

    # Location
    location_preference: Optional[str] = None
    nearness_to_landmark: Optional[str] = None

    # Hotel Type
    hotel_style_preference: List[str] = field(default_factory=list)

    # Services
    require_parking: bool = False
    require_wifi: bool = True
    require_breakfast: bool = False
    require_spa: bool = False
    require_gym: bool = False
    require_pool: bool = False
    require_restaurant: bool = False
    require_business_center: bool = False

    # Special Requirements
    pet_friendly: bool = False
    kids_friendly: bool = False
    quiet_location: bool = False
    non_smoking: bool = False
    need_early_checkin: bool = False
    need_late_checkout: bool = False

    # Trip Characteristics
    trip_duration: Optional[int] = None  # number of nights
    group_size: Optional[int] = None
    trip_type: Optional[str] = None  # business, leisure, family, etc.

    # Language
    preferred_language: str = "en"

    # Additional
    importance_scores: dict = field(default_factory=dict)
    # Define importance: {"price": 0.5, "location": 0.8, etc}

    def to_dict(self) -> dict:
        """Convert preferences to dictionary"""
        return {
            "budget": {
                "level": self.budget_level,
                "max_per_night": self.max_price_per_night,
            },
            "accommodation": {
                "room_types": self.room_type_preference,
                "bed_preference": self.bed_preference,
                "bathroom_type": self.bathroom_type,
            },
            "dietary": self.dietary_restrictions,
            "accessibility": self.accessibility_requirements,
            "location": {
                "preference": self.location_preference,
                "near_landmark": self.nearness_to_landmark,
            },
            "hotel_style": self.hotel_style_preference,
            "services": {
                "parking": self.require_parking,
                "wifi": self.require_wifi,
                "breakfast": self.require_breakfast,
                "spa": self.require_spa,
                "gym": self.require_gym,
                "pool": self.require_pool,
                "restaurant": self.require_restaurant,
                "business_center": self.require_business_center,
            },
            "special": {
                "pet_friendly": self.pet_friendly,
                "kids_friendly": self.kids_friendly,
                "quiet": self.quiet_location,
                "non_smoking": self.non_smoking,
                "early_checkin": self.need_early_checkin,
                "late_checkout": self.need_late_checkout,
            },
            "trip": {
                "duration": self.trip_duration,
                "group_size": self.group_size,
                "type": self.trip_type,
            },
        }

    def get_priority_amenities(self) -> List[str]:
        """Get amenities based on preferences"""
        amenities = []

        if self.require_parking:
            amenities.append("parking")
        if self.require_wifi:
            amenities.append("wifi")
        if self.require_breakfast:
            amenities.append("breakfast")
        if self.require_spa:
            amenities.append("spa")
        if self.require_gym:
            amenities.append("gym")
        if self.require_pool:
            amenities.append("pool")
        if self.require_restaurant:
            amenities.append("restaurant")
        if self.require_business_center:
            amenities.append("business-center")
        if self.pet_friendly:
            amenities.append("pet-friendly")
        if self.kids_friendly:
            amenities.append("kids-club")

        return amenities

"""Guest Profile Model"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date


@dataclass
class GuestProfile:
    """Represents a guest's profile and preferences"""

    # Basic Information
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    # Travel Details
    destination: Optional[str] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None

    # Party Composition
    num_adults: int = 1
    num_children: int = 0
    num_infants: int = 0
    num_rooms: int = 1

    # Budget
    budget_level: Optional[str] = None  # budget, mid-range, premium, luxury
    max_price_per_night: Optional[float] = None

    # Preferences
    room_type: Optional[str] = None  # Standard, Deluxe, Suite, etc.
    bed_preference: Optional[str] = None  # King, Queen, Twin, etc.
    bathroom_type: Optional[str] = None  # Indian, Western, Both

    # Dietary Needs
    dietary_restrictions: List[str] = field(default_factory=list)
    # vegetarian, vegan, jain, halal, kosher, gluten-free

    # Accessibility
    accessibility_needs: List[str] = field(default_factory=list)
    # wheelchair-accessible, elevator, etc.

    # Location Preferences
    locality_preference: Optional[str] = None
    # city-centre, near-airport, near-station, beach, business-district
    nearby_landmarks: List[str] = field(default_factory=list)

    # Hotel Style
    hotel_style: Optional[str] = None
    # boutique, heritage, resort, business, eco-friendly, luxury

    # Special Requirements
    needs_parking: bool = False
    needs_early_checkin: bool = False
    needs_late_checkout: bool = False
    needs_luggage_storage: bool = False

    # Trip Purpose
    trip_purpose: Optional[str] = None
    # leisure, business, family-vacation, honeymoon, solo-trip, adventure

    # Amenities
    desired_amenities: List[str] = field(default_factory=list)
    # pool, spa, gym, kids-club, pet-friendly, wifi, breakfast, etc.

    # Guest Type/Persona
    persona: Optional[str] = None
    # couple, family, solo, senior, business, adventure, etc.

    # Metadata
    language: str = "en"
    timezone: Optional[str] = None
    conversation_context: dict = field(default_factory=dict)

    def get_party_size(self) -> int:
        """Get total party size"""
        return self.num_adults + self.num_children + self.num_infants

    def get_nights(self) -> Optional[int]:
        """Get number of nights"""
        if self.check_in_date and self.check_out_date:
            return (self.check_out_date - self.check_in_date).days
        return None

    def is_family_trip(self) -> bool:
        """Check if this is a family trip"""
        return self.num_children > 0 or self.num_infants > 0

    def is_solo_trip(self) -> bool:
        """Check if this is a solo trip"""
        return self.get_party_size() == 1

    def is_couple_trip(self) -> bool:
        """Check if this is a couple trip"""
        return self.get_party_size() == 2 and self.num_children == 0

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "destination": self.destination,
            "check_in": self.check_in_date.isoformat() if self.check_in_date else None,
            "check_out": self.check_out_date.isoformat() if self.check_out_date else None,
            "party_size": self.get_party_size(),
            "budget": self.budget_level,
            "preferences": {
                "room_type": self.room_type,
                "bed_preference": self.bed_preference,
                "bathroom_type": self.bathroom_type,
                "locality": self.locality_preference,
                "hotel_style": self.hotel_style,
            },
            "requirements": {
                "dietary": self.dietary_restrictions,
                "accessibility": self.accessibility_needs,
                "amenities": self.desired_amenities,
            }
        }

"""Attraction domain models for Yatra Tours Agent"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class AttractionType(Enum):
    """Types of attractions"""
    BEACH = "Beach"
    TEMPLE = "Temple"
    FORT = "Historical Fort"
    MUSEUM = "Museum"
    WATER_SPORTS = "Water Sports"
    ADVENTURE = "Adventure Activity"
    NATURE = "Nature/Trekking"
    CULTURAL = "Cultural Site"
    MARKET = "Market/Bazaar"
    VIEWPOINT = "Viewpoint"
    WILDLIFE = "Wildlife/Sanctuary"
    PILGRIMAGE = "Pilgrimage Site"


class DifficultyLevel(Enum):
    """Physical difficulty of activity"""
    EASY = "Easy"
    MODERATE = "Moderate"
    CHALLENGING = "Challenging"
    EXTREME = "Extreme"


class CrowdLevel(Enum):
    """Expected crowd levels at different times"""
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    VERY_HIGH = "Very High"


@dataclass
class Review:
    """Attraction review"""
    reviewer_name: str
    rating: float  # 1-5
    comment: str
    date: str  # ISO format
    helpful_count: int = 0


@dataclass
class Amenity:
    """Attraction amenity"""
    name: str  # "Parking", "Restrooms", "Food", "WiFi", etc.
    available: bool = True


@dataclass
class Attraction:
    """Attraction model"""
    # Required fields
    id: str
    name: str
    description: str
    city: str
    locality: str
    attraction_type: AttractionType

    # Ratings & Reviews
    rating: float  # 1-5
    num_reviews: int = 0
    reviews: List[Review] = field(default_factory=list)

    # Practical Info
    opening_time: str = "09:00"  # HH:MM
    closing_time: str = "18:00"  # HH:MM
    entry_fee: float = 0  # In INR, 0 if free
    best_time_to_visit: str = "Morning"  # Morning/Afternoon/Evening/Anytime
    duration_hours: float = 2.0  # How long to spend
    distance_from_city_center: float = 0

    # Difficulty & Suitability
    difficulty_level: DifficultyLevel = DifficultyLevel.EASY
    kid_friendly: bool = True
    senior_friendly: bool = True
    wheelchair_accessible: bool = False

    # Crowd Info
    peak_season: str = "Dec-Feb"  # Busiest time
    best_days: List[str] = field(default_factory=list)  # Weekday/Weekend
    typical_crowd_level: CrowdLevel = CrowdLevel.MODERATE
    crowd_by_time: dict = field(default_factory=dict)  # {"morning": "Low", "afternoon": "High"}

    # Features
    amenities: List[Amenity] = field(default_factory=list)
    activities_available: List[str] = field(default_factory=list)
    highlights: List[str] = field(default_factory=list)

    # Contact
    phone: Optional[str] = None
    website: Optional[str] = None

    # Address
    address: str = ""
    google_maps_link: Optional[str] = None

    def get_average_rating(self) -> float:
        """Calculate average rating from reviews"""
        if not self.reviews:
            return self.rating
        return sum(r.rating for r in self.reviews) / len(self.reviews)

    def is_suitable_for_kids(self) -> bool:
        """Check if suitable for children"""
        return self.kid_friendly and self.difficulty_level != DifficultyLevel.EXTREME

    def is_suitable_for_seniors(self) -> bool:
        """Check if suitable for elderly"""
        return (self.senior_friendly and
                self.difficulty_level in [DifficultyLevel.EASY, DifficultyLevel.MODERATE])

    def is_accessible(self) -> bool:
        """Check if wheelchair accessible"""
        return self.wheelchair_accessible

    def get_crowd_at_time(self, time_period: str) -> str:
        """Get crowd level at specific time"""
        return self.crowd_by_time.get(time_period, "Unknown")

    def __repr__(self) -> str:
        return f"<Attraction name='{self.name}' type={self.attraction_type.value} rating={self.rating}>"


@dataclass
class ActivityPreferences:
    """User's activity preferences"""
    preferred_types: List[str] = field(default_factory=list)  # Beach, Temple, etc.
    difficulty_level: str = "Easy"
    include_kids: bool = False
    include_seniors: bool = False
    wheelchair_accessible: bool = False

    budget_per_activity: Optional[float] = None
    duration_preference: str = "Half-day"  # Half-day, Full-day, Multiple days

    peak_season_ok: bool = True
    prefer_crowd_level: str = "Low"  # Low/Moderate/High

    avoid_activities: List[str] = field(default_factory=list)


@dataclass
class Itinerary:
    """Daily itinerary for attractions"""
    day: int
    date: str  # ISO format
    attractions: List[dict] = field(default_factory=list)  # [{attraction_id, time, duration}]
    estimated_cost: float = 0
    estimated_travel_time: float = 0
    difficulty_level: str = "Easy"
    description: str = ""

    def add_attraction(self, attraction_id: str, time: str, duration: float):
        """Add attraction to itinerary"""
        self.attractions.append({
            "id": attraction_id,
            "time": time,
            "duration": duration
        })

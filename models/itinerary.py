"""Itinerary domain models for Yojana Planning Agent"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class FlexibilityLevel(Enum):
    """Activity flexibility"""
    RIGID = "Rigid"  # Cannot move (flight, hotel checkout)
    SEMI_FLEXIBLE = "Semi-flexible"  # Preferred time but movable
    FLEXIBLE = "Flexible"  # Can move to any time/day


class ActivityType(Enum):
    """Activity categories"""
    HOTEL = "Hotel"
    BREAKFAST = "Breakfast"
    LUNCH = "Lunch"
    DINNER = "Dinner"
    SNACK = "Snack"
    ATTRACTION = "Attraction"
    SHOPPING = "Shopping"
    TRANSPORT = "Transport"
    REST = "Rest"
    ADVENTURE = "Adventure"


@dataclass
class ScheduledActivity:
    """Single scheduled activity in itinerary"""
    id: str
    name: str
    activity_type: ActivityType
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    duration_minutes: int
    location: str
    description: str = ""

    # Logistics
    flexibility: FlexibilityLevel = FlexibilityLevel.FLEXIBLE
    travel_time_minutes: int = 0  # From previous activity
    travel_mode: str = ""  # Taxi, walking, etc.
    cost: float = 0  # In INR

    # Details
    source_agent: str = ""  # Which agent recommended (Atithi, Annapurna, etc.)
    notes: str = ""
    booking_required: bool = False
    operating_hours: str = ""  # e.g. "10:00-18:00"

    # Alternatives
    alternatives: List[str] = field(default_factory=list)  # IDs of alternatives


@dataclass
class DayPlan:
    """Single day itinerary"""
    day_number: int
    date: str  # ISO format
    theme: str  # e.g. "Beach & Culture"

    activities: List[ScheduledActivity] = field(default_factory=list)

    # Metrics
    total_activity_time_hours: float = 0
    total_travel_time_minutes: int = 0
    daily_cost: float = 0
    activity_count: int = 0
    pace: str = "Comfortable"  # Comfortable, Moderate, Busy, Exhausting

    # Notes
    morning_theme: str = ""
    afternoon_theme: str = ""
    evening_theme: str = ""
    special_notes: List[str] = field(default_factory=list)

    flexibility_score: float = 0.0  # 0-100, how flexible is this day

    def add_activity(self, activity: ScheduledActivity):
        """Add activity to day"""
        self.activities.append(activity)
        self.activity_count += 1


@dataclass
class TravelItinerary:
    """Complete travel itinerary"""
    id: str
    destination: str
    start_date: str  # ISO format
    end_date: str  # ISO format
    num_travelers: int

    days: List[DayPlan] = field(default_factory=list)

    # Overall metrics
    total_duration_days: int = 0
    total_cost: float = 0
    total_activities: int = 0
    average_daily_pace: str = ""
    budget_remaining: float = 0

    # Status
    status: str = "DRAFT"  # DRAFT, APPROVED, EXECUTING, COMPLETED
    created_at: str = ""
    last_updated: str = ""

    # Metadata
    user_notes: str = ""
    special_requirements: List[str] = field(default_factory=list)
    version: int = 1
    previous_versions: List[str] = field(default_factory=list)  # Store history

    # Validation
    is_validated: bool = False
    validation_issues: List[str] = field(default_factory=list)

    def get_day(self, day_number: int) -> Optional[DayPlan]:
        """Get specific day plan"""
        for day in self.days:
            if day.day_number == day_number:
                return day
        return None

    def add_day(self, day_plan: DayPlan):
        """Add day to itinerary"""
        self.days.append(day_plan)
        self.total_duration_days = len(self.days)


@dataclass
class PlanChange:
    """Track changes to itinerary"""
    change_type: str  # "ADD", "REMOVE", "MODIFY", "MOVE", "SWAP"
    activity_id: str
    day_from: Optional[int] = None
    day_to: Optional[int] = None
    timestamp: str = ""
    reason: str = ""
    impact_summary: str = ""

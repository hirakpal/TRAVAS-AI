"""User preference models for travel planning."""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date


@dataclass
class TravelPreferences:
    """Comprehensive travel preferences"""
    destination: str
    checkin_date: date
    checkout_date: date
    num_travelers: int = 1
    budget_per_night: float = 5000.0  # INR

    # Specific preferences
    travel_style: str = "balanced"  # "budget", "balanced", "luxury"
    dietary_restrictions: List[str] = field(default_factory=list)  # e.g., ["vegetarian", "vegan"]
    accessibility_needs: List[str] = field(default_factory=list)  # e.g., ["wheelchair", "visual_impairment"]
    preferred_activities: List[str] = field(default_factory=list)  # e.g., ["beach", "hiking", "culture"]

    # Travel group
    traveling_with_family: bool = False
    traveling_with_kids: bool = False
    kid_ages: List[int] = field(default_factory=list)

    # Preferences
    preferred_neighborhoods: List[str] = field(default_factory=list)
    avoid_areas: List[str] = field(default_factory=list)

    # Transport preferences
    prefer_public_transport: bool = True
    have_car_rental: bool = False

    @property
    def duration_days(self) -> int:
        """Calculate trip duration in days"""
        return (self.checkout_date - self.checkin_date).days

    @property
    def total_budget(self) -> float:
        """Calculate total hotel budget for the trip"""
        return self.budget_per_night * self.duration_days

    def __repr__(self) -> str:
        return (
            f"<TravelPreferences {self.destination} "
            f"({self.duration_days} days, ₹{self.budget_per_night}/night)>"
        )

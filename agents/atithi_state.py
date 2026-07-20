"""Conversation state for Atithi agent with LangGraph"""

from typing import TypedDict, Optional, List


class AtithiConversationState(TypedDict):
    """State tracking for three-phase hotel search conversation"""

    # Phase tracking
    phase: int  # 1 (dates), 2 (budget), 3 (search)

    # Phase 1: Essential information (REQUIRED before phase 2)
    destination: Optional[str]
    checkin_date: Optional[str]
    checkout_date: Optional[str]
    num_adults: Optional[int]
    num_children: Optional[int]
    num_rooms: Optional[int]

    # Phase 2: Preferences (REQUIRED before phase 3)
    budget: Optional[float]
    room_preferences: Optional[List[str]]
    must_have_amenities: Optional[List[str]]
    accessibility_needs: Optional[List[str]]

    # Conversation tracking
    messages: List[dict]  # Full conversation history
    last_response: str  # Most recent agent response
    phase_complete_flags: dict  # Track which fields are filled


def create_initial_state() -> AtithiConversationState:
    """Create initial conversation state"""
    return AtithiConversationState(
        phase=1,
        destination=None,
        checkin_date=None,
        checkout_date=None,
        num_adults=None,
        num_children=None,
        num_rooms=None,
        budget=None,
        room_preferences=None,
        must_have_amenities=None,
        accessibility_needs=None,
        messages=[],
        last_response="",
        phase_complete_flags={
            "phase_1": False,
            "phase_2": False,
            "phase_3": False,
        }
    )

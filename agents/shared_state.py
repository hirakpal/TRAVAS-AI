"""Shared conversation state for all agents in TRAVAS system"""

from typing import TypedDict, Optional, List, Any
from datetime import datetime
import json


def format_budget(value: Any) -> str:
    """Safely format a budget value as a rupee string.

    Defensive against the value being a string, None, or otherwise
    non-numeric (e.g. if an LLM-based extractor ever returns "20000 INR"
    instead of a plain number) so formatting never raises and silently
    swallows a real specialist response inside a try/except.
    """
    if value is None:
        return "Not specified"
    try:
        return f"₹{float(value):,.0f}"
    except (ValueError, TypeError):
        return f"₹{value}"


def build_context_summary(prefs: dict) -> str:
    """Build a single, consistent context summary string from shared-state
    travel preferences, for injecting into a specialist's user message.

    This is the single source of truth for "what does the shared state know
    so far" - every specialist calls this same function instead of each
    hand-rolling its own subset of fields. Previously each of the 5
    specialist agents built its own slightly different field list (e.g.
    Annapurna never included trip duration, Yatra never included the
    accommodation area, Bazaar never included traveler counts), which meant
    a fact captured while talking to one specialist could still be invisible
    to another. Including ALL known fields here removes that drift - each
    specialist's own system prompt is responsible for using only what's
    relevant to its domain and ignoring the rest.

    Returns an empty string if nothing is known yet.
    """
    parts = []
    if prefs.get("source_city"):
        parts.append(f"Departing from: {prefs['source_city']}")
    if prefs.get("destination"):
        parts.append(f"Destination: {prefs['destination']}")
    if prefs.get("accommodation_area"):
        parts.append(f"Accommodation area: {prefs['accommodation_area']}")
    if prefs.get("checkin_date"):
        parts.append(f"Check-in: {prefs['checkin_date']}")
    if prefs.get("checkout_date"):
        parts.append(f"Check-out: {prefs['checkout_date']}")
    if prefs.get("num_days"):
        parts.append(f"Trip duration: {prefs['num_days']} days")
    if prefs.get("num_adults") or prefs.get("num_children"):
        travelers = f"{prefs.get('num_adults', 0)} adults"
        if prefs.get("num_children"):
            travelers += f", {prefs['num_children']} children"
        parts.append(f"Travelers: {travelers}")
    if prefs.get("num_rooms"):
        parts.append(f"Rooms needed: {prefs['num_rooms']}")
    if prefs.get("budget"):
        parts.append(f"Budget: {format_budget(prefs['budget'])}")
    if prefs.get("dietary_restrictions"):
        parts.append(f"Dietary restrictions: {', '.join(prefs['dietary_restrictions'])}")
    if prefs.get("accessibility_needs"):
        parts.append(f"Accessibility needs: {', '.join(prefs['accessibility_needs'])}")
    if prefs.get("preferred_activities"):
        parts.append(f"Stated interests: {', '.join(prefs['preferred_activities'])}")

    return " | ".join(parts)


def enrich_message_with_context(user_message: str, prefs: dict) -> str:
    """Wrap a user message with the standard context block, if any context
    is known yet. Used identically by every specialist agent's chat().
    """
    summary = build_context_summary(prefs)
    if not summary:
        return user_message
    return f"CONTEXT FROM EARLIER CONVERSATION:\n{summary}\n\nUSER REQUEST:\n{user_message}"


# Markers that appear in Yojana's own "I can't build a draft yet" refusal
# text (its correct, designed behavior when specialist input is too thin).
# Shared between yojana_agent.py (to decide whether to attempt structured
# submission) and streamlit_app.py (to decide whether the itinerary panel
# has a real draft) so the two can't drift out of sync on what counts as
# "real."
REFUSAL_MARKERS = [
    "insufficient specialist input",
    "cannot produce a meaningful draft",
    "there is no itinerary to validate",
]


def is_real_itinerary(text: str) -> bool:
    """True if Yojana actually produced a draft, False if it refused."""
    if not text:
        return False
    lower = text.lower()
    return not any(marker in lower for marker in REFUSAL_MARKERS)


class TravelPreferences(TypedDict):
    """Shared travel preferences across all agents"""
    destination: Optional[str]
    source_city: Optional[str]  # Departure/origin city
    accommodation_area: Optional[str]  # Area/neighborhood for accommodation (e.g., Candolim, Anjuna)
    checkin_date: Optional[str]
    checkout_date: Optional[str]
    num_adults: Optional[int]
    num_children: Optional[int]
    num_rooms: Optional[int]
    budget: Optional[float]
    dietary_restrictions: Optional[List[str]]
    accessibility_needs: Optional[List[str]]
    preferred_activities: Optional[List[str]]
    num_days: Optional[int]


class ConversationPhase(TypedDict):
    """Track which agent is handling and what phase"""
    current_agent: str  # "atithi", "annapurna", "yatra", "safar", "bazaar"
    phase: int  # 1, 2, 3, etc (different for each agent)
    status: str  # "gathering_info", "processing", "ready_to_recommend"


class SharedConversationState(TypedDict):
    """Shared state that all agents can read/write"""

    # Conversation metadata
    session_id: str  # Unique session ID
    timestamp: str  # ISO format timestamp
    conversation_history: List[dict]  # Full history of all turns

    # Shared travel preferences (updated by any agent)
    travel_preferences: TravelPreferences

    # Multi-agent tracking
    active_agents: List[str]  # Which agents are involved
    agent_responses: dict  # {agent_name: last_response}
    orchestrator_active: bool  # Is Sanchalak routing?

    # Current phase info
    current_phase: ConversationPhase

    # Recommendations (shared across agents)
    hotel_recommendations: Optional[List[dict]]
    food_recommendations: Optional[List[dict]]
    tour_recommendations: Optional[List[dict]]
    transport_recommendations: Optional[List[dict]]
    shopping_recommendations: Optional[List[dict]]

    # Metadata
    last_update: str  # When was state last updated
    metadata: dict  # Flexible metadata for any agent


class StateManager:
    """Manage shared conversation state for all agents"""

    def __init__(self, session_id: str):
        """Initialize state manager"""
        self.session_id = session_id
        self.state = self._create_initial_state(session_id)

    def _create_initial_state(self, session_id: str) -> SharedConversationState:
        """Create initial shared state"""
        return SharedConversationState(
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            conversation_history=[],
            travel_preferences=TravelPreferences(
                destination=None,
                source_city=None,
                accommodation_area=None,
                checkin_date=None,
                checkout_date=None,
                num_adults=None,
                num_children=None,
                num_rooms=None,
                budget=None,
                dietary_restrictions=None,
                accessibility_needs=None,
                preferred_activities=None,
                num_days=None,
            ),
            active_agents=[],
            agent_responses={},
            orchestrator_active=False,
            current_phase=ConversationPhase(
                current_agent="",
                phase=1,
                status="gathering_info"
            ),
            hotel_recommendations=None,
            food_recommendations=None,
            tour_recommendations=None,
            transport_recommendations=None,
            shopping_recommendations=None,
            last_update=datetime.now().isoformat(),
            metadata={},
        )

    def add_message(self, role: str, content: str, agent: Optional[str] = None):
        """Add message to shared history"""
        message = {
            "role": role,
            "content": content,
            "agent": agent,
            "timestamp": datetime.now().isoformat()
        }
        self.state["conversation_history"].append(message)
        self._update_timestamp()

    # List-type preference fields are MERGED with existing values rather than
    # overwritten. An LLM-based extractor only returns what's new/mentioned in
    # the current message, so overwriting would silently drop previously
    # captured facts - e.g. mentioning "gluten-free" in a later turn would
    # otherwise erase an earlier "vegetarian" dietary restriction.
    LIST_PREFERENCE_FIELDS = {"dietary_restrictions", "accessibility_needs", "preferred_activities"}

    def update_preferences(self, updates: dict):
        """Update travel preferences.

        Keys not present in TravelPreferences are silently dropped by design
        (the TypedDict is the schema contract), but we log them so a future
        schema mismatch (e.g. an LLM extractor returning "days" instead of
        "num_days") is discoverable instead of silently vanishing.
        """
        unknown_keys = []
        for key, value in updates.items():
            if key not in self.state["travel_preferences"]:
                unknown_keys.append(key)
                continue

            if key in self.LIST_PREFERENCE_FIELDS and isinstance(value, list):
                existing = self.state["travel_preferences"].get(key) or []
                merged = list(existing)
                for item in value:
                    if item not in merged:
                        merged.append(item)
                self.state["travel_preferences"][key] = merged
            else:
                self.state["travel_preferences"][key] = value
        if unknown_keys:
            import logging
            logging.getLogger(__name__).debug(
                f"update_preferences: ignoring unknown keys not in TravelPreferences schema: {unknown_keys}"
            )
        self._update_timestamp()

    def set_active_agent(self, agent_name: str):
        """Mark an agent as active"""
        if agent_name not in self.state["active_agents"]:
            self.state["active_agents"].append(agent_name)
        self.state["current_phase"]["current_agent"] = agent_name
        self._update_timestamp()

    def update_agent_response(self, agent_name: str, response: str):
        """Store agent's last response"""
        self.state["agent_responses"][agent_name] = response
        self._update_timestamp()

    def update_recommendations(self, agent_type: str, recommendations: List[dict]):
        """Update recommendations from any agent"""
        if agent_type == "atithi":
            self.state["hotel_recommendations"] = recommendations
        elif agent_type == "annapurna":
            self.state["food_recommendations"] = recommendations
        elif agent_type == "yatra":
            self.state["tour_recommendations"] = recommendations
        elif agent_type == "safar":
            self.state["transport_recommendations"] = recommendations
        elif agent_type == "bazaar":
            self.state["shopping_recommendations"] = recommendations
        self._update_timestamp()

    def get_state(self) -> SharedConversationState:
        """Get current state"""
        return self.state

    def get_preferences(self) -> TravelPreferences:
        """Get current preferences"""
        return self.state["travel_preferences"]

    def get_agent_context(self, agent_name: str) -> dict:
        """Get context relevant to an agent"""
        return {
            "preferences": self.state["travel_preferences"],
            "history": self.state["conversation_history"],
            "active_agents": self.state["active_agents"],
            "other_agent_responses": {
                k: v for k, v in self.state["agent_responses"].items()
                if k != agent_name
            },
            "recommendations": {
                "hotels": self.state["hotel_recommendations"],
                "food": self.state["food_recommendations"],
                "tours": self.state["tour_recommendations"],
                "transport": self.state["transport_recommendations"],
                "shopping": self.state["shopping_recommendations"],
            }
        }

    def set_phase(self, agent: str, phase: int, status: str):
        """Update phase info"""
        self.state["current_phase"]["current_agent"] = agent
        self.state["current_phase"]["phase"] = phase
        self.state["current_phase"]["status"] = status
        self._update_timestamp()

    def add_metadata(self, key: str, value: Any):
        """Add custom metadata"""
        self.state["metadata"][key] = value
        self._update_timestamp()

    def _update_timestamp(self):
        """Update last_update timestamp"""
        self.state["last_update"] = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Export state as dict"""
        return dict(self.state)

    def to_json(self) -> str:
        """Export state as JSON"""
        return json.dumps(dict(self.state), indent=2)

    def reset(self):
        """Reset state"""
        self.state = self._create_initial_state(self.session_id)


# Global state manager instance
_state_manager: Optional[StateManager] = None


def initialize_state_manager(session_id: str) -> StateManager:
    """Initialize the global state manager"""
    global _state_manager
    _state_manager = StateManager(session_id)
    return _state_manager


def get_state_manager() -> StateManager:
    """Get the current state manager"""
    global _state_manager
    if _state_manager is None:
        # Create a default one if not initialized
        import uuid
        _state_manager = StateManager(str(uuid.uuid4()))
    return _state_manager


def reset_state_manager():
    """Reset the global state manager"""
    global _state_manager
    if _state_manager:
        _state_manager.reset()

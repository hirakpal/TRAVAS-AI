"""Shared conversation state for all agents in TRAVAS system"""

from typing import TypedDict, Optional, List, Any
from datetime import datetime
import json


class TravelPreferences(TypedDict):
    """Shared travel preferences across all agents"""
    destination: Optional[str]
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

    def update_preferences(self, updates: dict):
        """Update travel preferences"""
        for key, value in updates.items():
            if key in self.state["travel_preferences"]:
                self.state["travel_preferences"][key] = value
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

"""Example: How agents use shared state"""

from agents.shared_state import get_state_manager


class AgentWithSharedState:
    """Base class for agents that use shared state"""

    def __init__(self, agent_name: str, api_key: str):
        """Initialize agent with shared state"""
        self.name = agent_name
        self.api_key = api_key
        self.state_manager = get_state_manager()

    def chat(self, message: str) -> str:
        """Process message using shared state"""

        # 1. Add user message to shared history
        self.state_manager.add_message("user", message, self.name)

        # 2. Mark this agent as active
        self.state_manager.set_active_agent(self.name)

        # 3. Get context relevant to this agent
        context = self.state_manager.get_agent_context(self.name)

        # 4. Build prompt using shared preferences
        prefs = context["preferences"]
        prompt = f"""
Current travel preferences:
- Destination: {prefs["destination"]}
- Dates: {prefs["checkin_date"]} to {prefs["checkout_date"]}
- Travelers: {prefs["num_adults"]} adults, {prefs["num_children"]} children
- Budget: {prefs["budget"]}
- Dietary: {prefs["dietary_restrictions"]}

User message: {message}
"""

        # 5. Get response (implementation specific to each agent)
        response = self._get_response(prompt)

        # 6. Update shared state with response
        self.state_manager.add_message("assistant", response, self.name)
        self.state_manager.update_agent_response(self.name, response)

        return response

    def _get_response(self, prompt: str) -> str:
        """Override in subclass"""
        raise NotImplementedError

    def update_preferences(self, **kwargs):
        """Update shared preferences"""
        self.state_manager.update_preferences(kwargs)

    def get_other_agent_responses(self) -> dict:
        """Get what other agents said"""
        context = self.state_manager.get_agent_context(self.name)
        return context["other_agent_responses"]

    def get_shared_preferences(self) -> dict:
        """Get current shared preferences"""
        return dict(self.state_manager.get_preferences())

    def get_other_recommendations(self) -> dict:
        """Get recommendations from other agents"""
        context = self.state_manager.get_agent_context(self.name)
        return context["recommendations"]

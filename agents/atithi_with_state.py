"""Atithi agent with LangGraph state management for three-phase conversation"""

import os
from typing import Optional
from langgraph.graph import StateGraph, END

from agents.atithi_agent import AtithiAgent
from agents.atithi_state import AtithiConversationState, create_initial_state
from utils.logger import get_logger

logger = get_logger(__name__)


class AtithiWithState:
    """Atithi agent wrapped with LangGraph state management"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize agent with state management"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.agent = AtithiAgent(api_key=self.api_key)
        self.state = create_initial_state()
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build the conversation flow graph"""
        graph = StateGraph(AtithiConversationState)

        # Add nodes for each phase
        graph.add_node("phase_1", self._phase_1_node)
        graph.add_node("phase_2", self._phase_2_node)
        graph.add_node("phase_3", self._phase_3_node)

        # Set entry point
        graph.set_entry_point("phase_1")

        # Conditional edges: stay in phase or move to next
        graph.add_conditional_edges(
            "phase_1",
            self._check_phase_1_complete,
            {
                "stay": "phase_1",
                "next": "phase_2"
            }
        )

        graph.add_conditional_edges(
            "phase_2",
            self._check_phase_2_complete,
            {
                "stay": "phase_2",
                "next": "phase_3"
            }
        )

        # Phase 3 ends
        graph.add_edge("phase_3", END)

        return graph.compile()

    def _phase_1_node(self, state: AtithiConversationState) -> AtithiConversationState:
        """Phase 1: Gather destination, dates, travelers"""

        system_msg = """
You are in PHASE 1 of the conversation. Your ONLY job is to gather:
1. Destination city
2. Check-in date
3. Check-out date
4. Number of adults
5. Number of children

Ask for any missing information. When you have ALL 5 items, end your response with: "PHASE_1_COMPLETE"

Do NOT ask about budget, amenities, or preferences yet.
Do NOT search for hotels.
"""

        # Get response from agent
        response = self.agent.chat(system_msg)
        state["messages"].append({"role": "assistant", "content": response})
        state["last_response"] = response
        state["phase"] = 1

        logger.info(f"Phase 1 response: {response[:100]}...")

        return state

    def _phase_2_node(self, state: AtithiConversationState) -> AtithiConversationState:
        """Phase 2: Gather budget and preferences"""

        system_msg = f"""
You are in PHASE 2 of the conversation. The user has provided:
- Destination: {state['destination']}
- Dates: {state['checkin_date']} to {state['checkout_date']}
- Travelers: {state['num_adults']} adults, {state['num_children']} children

Now gather:
1. Budget per night (in INR)
2. Preferred room types
3. Must-have amenities
4. Any accessibility needs

When you have all 4 items, end your response with: "PHASE_2_COMPLETE"

Do NOT search for hotels yet.
"""

        response = self.agent.chat(system_msg)
        state["messages"].append({"role": "assistant", "content": response})
        state["last_response"] = response
        state["phase"] = 2

        logger.info(f"Phase 2 response: {response[:100]}...")

        return state

    def _phase_3_node(self, state: AtithiConversationState) -> AtithiConversationState:
        """Phase 3: Search and recommend hotels"""

        # Now we have everything - search!
        system_msg = f"""
Perfect! Now I'll search for hotels based on all the information:
- Destination: {state['destination']}
- Dates: {state['checkin_date']} to {state['checkout_date']}
- Travelers: {state['num_adults']} adults, {state['num_children']} children
- Rooms: {state['num_rooms']}
- Budget: {state['budget']} per night
- Preferences: {state['room_preferences']}
- Amenities: {state['must_have_amenities']}

Search and provide recommendations.
"""

        response = self.agent.chat(system_msg)
        state["messages"].append({"role": "assistant", "content": response})
        state["last_response"] = response
        state["phase"] = 3
        state["phase_complete_flags"]["phase_3"] = True

        logger.info(f"Phase 3 response: {response[:100]}...")

        return state

    def _check_phase_1_complete(self, state: AtithiConversationState) -> str:
        """Check if Phase 1 is complete"""
        if "PHASE_1_COMPLETE" in state["last_response"]:
            state["phase_complete_flags"]["phase_1"] = True
            logger.info("Phase 1 complete - moving to Phase 2")
            return "next"
        logger.info("Phase 1 incomplete - staying in Phase 1")
        return "stay"

    def _check_phase_2_complete(self, state: AtithiConversationState) -> str:
        """Check if Phase 2 is complete"""
        if "PHASE_2_COMPLETE" in state["last_response"]:
            state["phase_complete_flags"]["phase_2"] = True
            logger.info("Phase 2 complete - moving to Phase 3")
            return "next"
        logger.info("Phase 2 incomplete - staying in Phase 2")
        return "stay"

    def chat(self, user_input: str) -> str:
        """Process user input through the graph"""
        # Add user message to history
        self.state["messages"].append({"role": "user", "content": user_input})

        # Add user input to agent's context
        self.agent.add_to_history("user", user_input)

        # Run the graph (will execute appropriate phase node)
        self.state = self.graph.invoke(self.state)

        # Return the last response
        return self.state["last_response"]

    def get_status(self) -> dict:
        """Get current conversation status"""
        return {
            "phase": self.state["phase"],
            "phase_1_complete": self.state["phase_complete_flags"]["phase_1"],
            "phase_2_complete": self.state["phase_complete_flags"]["phase_2"],
            "destination": self.state["destination"],
            "budget": self.state["budget"],
            "messages_count": len(self.state["messages"])
        }

    def reset(self) -> None:
        """Reset conversation"""
        self.state = create_initial_state()
        self.agent.reset()
        logger.info("Conversation reset")

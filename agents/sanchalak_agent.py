"""Sanchalak Agent - Master Orchestrator

Sanchalak (संचालक) means "Conductor/Orchestrator" in Hindi.
Routes travel queries to appropriate specialist agents using shared state.
"""

import os
from typing import Optional, Dict, List
from agents.atithi_agent import AtithiAgent
from agents.shared_state import get_state_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class SanchalakAgent:
    """Master orchestrator that routes queries to specialist agents"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Sanchalak with available agents and shared state

        Args:
            api_key: Anthropic API key
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        # Initialize available agents
        self.agents = {
            "atithi": AtithiAgent(api_key=self.api_key),
            # Future agents will be added here
            # "annapurna": AnnapurnaAgent(api_key=self.api_key),
            # "yatra": YatraAgent(api_key=self.api_key),
            # "safar": SafarAgent(api_key=self.api_key),
            # "bazaar": BazaarAgent(api_key=self.api_key),
        }

        # Track which agent was used
        self.last_agent_used = None
        self.conversation_history = []

        # Initialize shared state manager
        self.state_manager = get_state_manager()

    def identify_intent(self, message: str) -> str:
        """
        Simple intent recognition based on keywords

        Args:
            message: User message

        Returns:
            agent_name: Name of agent to handle this
        """
        message_lower = message.lower()

        # Keywords for each agent
        keywords = {
            "atithi": [
                "hotel", "accommodation", "stay", "room",
                "where to stay", "booking", "lodge",
                "resort", "motel", "hostel", "guest house"
            ],
            # Add more agents as they're built
            # "annapurna": ["restaurant", "food", "eat", "dining", "cafe", "cuisine"],
            # "yatra": ["attraction", "tour", "visit", "sightseeing", "itinerary", "place"],
            # "safar": ["flight", "train", "bus", "transport", "travel", "taxi"],
            # "bazaar": ["shopping", "shop", "mall", "market", "buy", "store"],
        }

        # Check which keywords match
        for agent_name, agent_keywords in keywords.items():
            for keyword in agent_keywords:
                if keyword in message_lower:
                    logger.info(f"Intent identified: {agent_name} (matched keyword: {keyword})")
                    return agent_name

        # Default to Atithi if no match
        logger.info("Intent unclear, defaulting to Atithi")
        return "atithi"

    def route_query(self, message: str) -> Dict:
        """
        Route user query to appropriate agent with shared state tracking

        Args:
            message: User message

        Returns:
            response: Agent response with metadata
        """
        # Mark Sanchalak as orchestrating in shared state
        self.state_manager.add_message("user", message, agent="sanchalak")
        self.state_manager.set_active_agent("sanchalak")
        self.state_manager.state["orchestrator_active"] = True

        # Identify which agent should handle this
        agent_name = self.identify_intent(message)
        logger.info(f"Sanchalak routing to {agent_name}")

        # Get the agent
        if agent_name not in self.agents:
            error_msg = f"Agent '{agent_name}' not available"
            self.state_manager.add_message("assistant", error_msg, agent="sanchalak")
            return {
                "success": False,
                "message": error_msg,
                "agent": None
            }

        agent = self.agents[agent_name]
        self.last_agent_used = agent_name

        # Route to agent (agent will update shared state on its own)
        try:
            response_text = agent.chat(message)

            # Track conversation locally
            self.conversation_history.append({
                "user_message": message,
                "agent_used": agent_name,
                "agent_response": response_text
            })

            # Store routing decision in shared state
            self.state_manager.add_metadata("last_routing", {
                "orchestrator": "sanchalak",
                "routed_to": agent_name,
                "user_message": message
            })

            return {
                "success": True,
                "message": response_text,
                "agent": agent_name,
                "history_count": agent.get_history_count()
            }

        except Exception as e:
            logger.error(f"Agent {agent_name} error: {str(e)}")
            error_response = f"Error from {agent_name}: {str(e)}"
            self.state_manager.add_message("assistant", error_response, agent="sanchalak")
            return {
                "success": False,
                "message": error_response,
                "agent": agent_name
            }

    def chat(self, message: str) -> str:
        """
        Simple chat interface - main entry point

        Args:
            message: User message

        Returns:
            response: Agent response
        """
        response = self.route_query(message)

        if response["success"]:
            return response["message"]
        else:
            return response["message"]

    def get_orchestrator_info(self) -> Dict:
        """Get orchestrator status"""
        return {
            "name": "Sanchalak",
            "role": "Master Orchestrator",
            "available_agents": list(self.agents.keys()),
            "last_agent_used": self.last_agent_used,
            "conversation_turns": len(self.conversation_history),
            "agents_status": {
                agent_name: agent.get_agent_info()
                for agent_name, agent in self.agents.items()
            }
        }

    def get_shared_preferences(self) -> Dict:
        """Get current travel preferences from shared state."""
        return dict(self.state_manager.get_preferences())

    def get_conversation_context(self) -> Dict:
        """Get full conversation context from shared state."""
        return self.state_manager.get_agent_context("sanchalak")

    def get_active_agents(self) -> List[str]:
        """Get list of active agents from shared state."""
        return self.state_manager.get_state()["active_agents"]

    def get_all_agent_responses(self) -> Dict:
        """Get responses from all agents."""
        return self.state_manager.get_state()["agent_responses"]

    def reset(self) -> None:
        """Reset all agents and history"""
        for agent in self.agents.values():
            agent.reset()
        self.last_agent_used = None
        self.conversation_history = []
        self.state_manager.state["orchestrator_active"] = False
        logger.info("Sanchalak orchestrator reset")

    def __repr__(self) -> str:
        return f"<SanchalakAgent agents={len(self.agents)} last_used={self.last_agent_used} with_shared_state=True>"

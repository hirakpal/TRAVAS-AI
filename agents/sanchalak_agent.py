"""Sanchalak Agent - Master Orchestrator

Sanchalak (संचालक) means "Conductor/Orchestrator" in Hindi.
Routes travel queries to appropriate specialist agents.
"""

import os
from typing import Optional, Dict, List
from agents.atithi_agent import AtithiAgent
from utils.logger import get_logger

logger = get_logger(__name__)


class SanchalakAgent:
    """Master orchestrator that routes queries to specialist agents"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Sanchalak with available agents

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
        Route user query to appropriate agent

        Args:
            message: User message

        Returns:
            response: Agent response with metadata
        """
        # Identify which agent should handle this
        agent_name = self.identify_intent(message)

        # Get the agent
        if agent_name not in self.agents:
            return {
                "success": False,
                "message": f"Agent '{agent_name}' not available",
                "agent": None
            }

        agent = self.agents[agent_name]
        self.last_agent_used = agent_name

        # Get response from agent
        try:
            response_text = agent.chat(message)

            # Track conversation
            self.conversation_history.append({
                "user_message": message,
                "agent_used": agent_name,
                "agent_response": response_text
            })

            return {
                "success": True,
                "message": response_text,
                "agent": agent_name,
                "history_count": agent.get_history_count()
            }

        except Exception as e:
            logger.error(f"Agent {agent_name} error: {str(e)}")
            return {
                "success": False,
                "message": f"Error from {agent_name}: {str(e)}",
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

    def reset(self) -> None:
        """Reset all agents and history"""
        for agent in self.agents.values():
            agent.reset()
        self.last_agent_used = None
        self.conversation_history = []
        logger.info("Sanchalak orchestrator reset")

    def __repr__(self) -> str:
        return f"<SanchalakAgent agents={len(self.agents)} last_used={self.last_agent_used}>"

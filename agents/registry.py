from typing import Dict, Optional
from agents.atithi_agent import AtithiAgent


class AgentRegistry:
    """Registry for all available agents"""

    _agents: Dict[str, type] = {
        "atithi": AtithiAgent,
    }

    @classmethod
    def register(cls, name: str, agent_class: type):
        """Register a new agent"""
        cls._agents[name.lower()] = agent_class

    @classmethod
    def get(cls, name: str, **kwargs):
        """Get an agent instance"""
        agent_class = cls._agents.get(name.lower())
        if not agent_class:
            raise ValueError(f"Agent '{name}' not found")
        return agent_class(**kwargs)

    @classmethod
    def list_agents(cls):
        """List all available agents"""
        return list(cls._agents.keys())

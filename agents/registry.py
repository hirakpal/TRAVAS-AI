"""Agent Registry - Factory for creating and managing agents"""

from typing import Dict, Optional, Type
from agents.atithi_agent import AtithiAgent
from agents.annapurna_agent import AnnapurnaAgent
from agents.yatra_agent import YatraAgent
from agents.safar_agent import SafarAgent
from agents.bazaar_agent import BazaarAgent
from agents.yojana_agent import YojanaAgent
from agents.parikshak_agent import ParikshakAgent


class AgentRegistry:
    """Registry for all available agents - Singleton factory pattern"""

    _agents: Dict[str, Type] = {
        "atithi": AtithiAgent,
        "annapurna": AnnapurnaAgent,
        "yatra": YatraAgent,
        "safar": SafarAgent,
        "bazaar": BazaarAgent,
        "yojana": YojanaAgent,
        "parikshak": ParikshakAgent,
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

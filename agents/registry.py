"""Agent Registry and Factory

Manages registration and creation of agents.
"""

from typing import Dict, Type, Optional, Any
from agents.base_agent import BaseAgent
from agents.atithi_agent import AtithiAgent
import logging

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for managing available agents.

    Supports dynamic agent registration and factory creation.
    """

    # Class-level registry
    _registry: Dict[str, Type[BaseAgent]] = {}

    @classmethod
    def register(cls, agent_name: str, agent_class: Type[BaseAgent]) -> None:
        """
        Register an agent class.

        Args:
            agent_name: Unique identifier for the agent
            agent_class: The agent class to register
        """
        if not issubclass(agent_class, BaseAgent):
            raise TypeError(f"{agent_class} must inherit from BaseAgent")

        cls._registry[agent_name] = agent_class
        logger.info(f"Registered agent: {agent_name}")

    @classmethod
    def unregister(cls, agent_name: str) -> None:
        """
        Unregister an agent.

        Args:
            agent_name: Name of agent to unregister
        """
        if agent_name in cls._registry:
            del cls._registry[agent_name]
            logger.info(f"Unregistered agent: {agent_name}")

    @classmethod
    def get(cls, agent_name: str) -> Optional[Type[BaseAgent]]:
        """
        Get a registered agent class.

        Args:
            agent_name: Name of the agent

        Returns:
            The agent class or None if not found
        """
        return cls._registry.get(agent_name)

    @classmethod
    def create(
        cls,
        agent_name: str,
        **kwargs: Any
    ) -> Optional[BaseAgent]:
        """
        Create an instance of a registered agent.

        Args:
            agent_name: Name of the agent to create
            **kwargs: Arguments to pass to agent constructor

        Returns:
            Agent instance or None if agent not found
        """
        agent_class = cls.get(agent_name)
        if not agent_class:
            logger.error(f"Agent not found: {agent_name}")
            return None

        try:
            agent = agent_class(**kwargs)
            logger.info(f"Created agent instance: {agent_name}")
            return agent
        except Exception as e:
            logger.error(f"Error creating agent {agent_name}: {e}")
            return None

    @classmethod
    def list_agents(cls) -> Dict[str, Type[BaseAgent]]:
        """
        Get all registered agents.

        Returns:
            Dictionary of agent names to classes
        """
        return cls._registry.copy()

    @classmethod
    def list_agent_names(cls) -> list:
        """
        Get names of all registered agents.

        Returns:
            List of agent names
        """
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, agent_name: str) -> bool:
        """
        Check if an agent is registered.

        Args:
            agent_name: Name to check

        Returns:
            True if registered, False otherwise
        """
        return agent_name in cls._registry


# Register built-in agents
AgentRegistry.register("atithi", AtithiAgent)


# Convenience function
def get_agent(
    agent_name: str,
    **kwargs: Any
) -> Optional[BaseAgent]:
    """
    Get or create an agent.

    Args:
        agent_name: Name of the agent
        **kwargs: Agent initialization arguments

    Returns:
        Agent instance or None
    """
    return AgentRegistry.create(agent_name, **kwargs)

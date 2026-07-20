"""Atithi Agent - Hotel Concierge Assistant

A warm, culturally-aware hotel recommendation assistant that helps travelers
discover the most suitable hotels based on their preferences.
"""

from typing import Optional, List, Dict
from agents.base_agent import BaseAgent
from config.prompts import ATITHI_SYSTEM_PROMPT
from llm.client import LLMClient


class AtithiAgent(BaseAgent):
    """
    Atithi Hotel Concierge Agent

    A specialized agent for warm, personalized hotel recommendations.
    Never makes bookings, processes payments, or invents hotel information.
    """

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        Initialize Atithi Agent.

        Args:
            provider: LLM provider (openai, anthropic, gemini)
            api_key: API key for the provider
            model: Model name (uses default if not specified)
            temperature: LLM temperature for creativity
            max_tokens: Maximum response tokens
        """
        super().__init__(
            name="Atithi",
            provider=provider,
            api_key=api_key,
            system_prompt=ATITHI_SYSTEM_PROMPT
        )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize LLM client
        self.llm_client = LLMClient(
            provider=provider,
            api_key=api_key,
            model=model
        )

    def chat(self, user_message: str) -> str:
        """
        Chat with Atithi Agent.

        Args:
            user_message: User's hotel inquiry

        Returns:
            Agent's recommendation or response
        """
        # Add user message to history
        self.add_to_history("user", user_message)

        # Get LLM response
        response = self._get_response()

        # Add assistant response to history
        self.add_to_history("assistant", response)

        return response

    def _get_response(self) -> str:
        """
        Get response from LLM.

        Returns:
            The agent's response
        """
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        messages.extend(self._format_messages_for_llm())

        response = self.llm_client.call(
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        return response

    def get_guest_profile(self) -> Dict:
        """
        Extract guest profile from conversation history.

        Returns:
            Dictionary with extracted guest preferences
        """
        profile = {
            "destination": None,
            "check_in_date": None,
            "check_out_date": None,
            "adults": None,
            "children": None,
            "budget": None,
            "room_type": None,
            "bed_preference": None,
            "dietary_needs": [],
            "accessibility_needs": [],
            "amenities": [],
            "locality_preference": None,
            "hotel_style": None,
            "purpose": None
        }

        # This would be enhanced with actual extraction logic
        # For now, it's a template for future implementation
        return profile

    def get_recommendations_context(self) -> Dict:
        """
        Prepare context for generating recommendations.

        Returns:
            Dictionary with context for recommendations
        """
        return {
            "conversation_length": self.get_history_count(),
            "guest_profile": self.get_guest_profile(),
            "conversation_history": self.get_history()
        }

    def validate_hotel_info(self, hotel_data: Dict) -> bool:
        """
        Validate that hotel information is verified and not invented.

        Args:
            hotel_data: Hotel information dictionary

        Returns:
            True if data is valid and verified
        """
        required_fields = ["name", "address", "price_range"]
        for field in required_fields:
            if field not in hotel_data or not hotel_data[field]:
                return False

        # Check for verification markers
        if hotel_data.get("verified") is False:
            return False

        return True

    def reset(self) -> None:
        """
        Reset agent state and conversation history.
        """
        super().reset()

    def __repr__(self) -> str:
        return (
            f"<AtithiAgent provider='{self.provider}' "
            f"model='{self.model}' history={self.get_history_count()}>"
        )


# Convenience function for quick usage
def create_atithi_agent(
    provider: str = "openai",
    api_key: Optional[str] = None
) -> AtithiAgent:
    """
    Create an Atithi Agent instance.

    Args:
        provider: LLM provider
        api_key: API key for provider

    Returns:
        Initialized AtithiAgent instance
    """
    return AtithiAgent(
        provider=provider,
        api_key=api_key
    )

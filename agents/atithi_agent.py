"""Atithi Agent - Hotel recommendation specialist.

The Atithi (guest) agent provides personalized hotel recommendations
with warmth and cultural awareness. Uses shared state for multi-agent coordination.
"""

import json
import os
from typing import Optional, List, Dict, Generator, Any
from datetime import datetime
import anthropic

from agents.base_agent import BaseAgent, Message
from agents.shared_state import get_state_manager
from tools.hotel_tools import HOTEL_TOOLS, list_tools
from models.preferences import TravelPreferences
from utils.logger import get_logger
from utils.validators import validate_hotel_preferences

logger = get_logger(__name__)


class AtithiAgent(BaseAgent):
    """Hotel recommendation agent powered by Claude."""

    SYSTEM_PROMPT = """Hotel Concierge Agent – System Prompt

You are Hotel Concierge Agent, an intelligent hotel recommendation assistant whose purpose is to help travelers discover the most suitable hotels based on their preferences.

Your role is to act like an experienced hotel concierge—not a booking engine or travel agency.

PRIMARY OBJECTIVE
Help travelers choose the best hotel for their trip by understanding their needs and recommending hotels that best match those requirements.

CRITICAL: THREE-PHASE CONVERSATION FLOW
You MUST follow this exact sequence and NEVER skip or rush phases:

PHASE 1: COLLECT ESSENTIAL DATES & TRAVELERS (REQUIRED - DO NOT SEARCH YET)
You MUST gather these before any hotel search:
- Destination city
- Check-in date
- Check-out date
- Number of adults
- Number of children (if any)
- Number of rooms needed

Ask these questions naturally across 1-3 turns. Do NOT call search_hotels until you have ALL of Phase 1.

PHASE 2: COLLECT PREFERENCES & BUDGET (REQUIRED - STILL NO SEARCH)
After Phase 1, ask for:
- Budget per night (or Budget tier: Budget/Mid-range/Premium/Luxury)
- Room preferences
- Must-have amenities
- Accessibility needs
- Any other specific requirements

Ask these across 1-2 turns. Do NOT call search_hotels until Phase 1 + Phase 2 complete.

PHASE 3: SEARCH & RECOMMEND (NOW USE TOOLS)
Only after Phases 1 & 2 are complete:
- Call search_hotels with gathered information
- Filter by preferences
- Get hotel details
- Provide 2-3 recommendations with clear reasoning

You must NOT:
- Make hotel bookings
- Process payments
- Ask users to complete reservations
- Invent hotel information, amenities, policies, or reviews
- Call any search tools before completing Phases 1 & 2

Always explain why a recommendation is suitable.

CONVERSATION STYLE
Be:
- Warm
- Friendly
- Professional
- Knowledgeable
- Conversational

Avoid sounding like a booking website. Guide the traveler naturally. Never overwhelm users with long questionnaires. Ask only for information that is still missing.

IMPORTANT CONVERSATION RULES:
- Phase 1 (Dates & Travelers): Ask 2-3 questions per turn. Acknowledge what you learned. Keep asking naturally until you have all Phase 1 info.
- Phase 2 (Preferences & Budget): Once Phase 1 complete, ask about budget and preferences. Do NOT mention searching yet.
- Phase 3 (Search): Only after both phases, say "Let me search for options" and use tools.
- Do NOT apologize for gathering information - it's necessary and professional.

UNDERSTANDING THE TRAVELER
Collect information progressively through natural conversation.

Required Information:
- Destination city
- Check-in date
- Check-out date
- Number of adults, children, infants
- Number of rooms

Optional Preferences (ask only if relevant):
- Budget (Budget/Mid-range/Premium/Luxury or max price per night)
- Room Type (Standard/Deluxe/Family/Suite/etc.)
- Bed Preference (King/Queen/Twin/etc.)
- Bathroom Type (Indian/European/Both/No Preference)
- Food Preference (Vegetarian/Vegan/Jain/Halal/Kosher/Gluten-Free/No Preference)
- Hotel Style (Boutique/Heritage/Resort/Business/Eco-friendly/Luxury/Family-friendly/etc.)
- Preferred Locality (City Centre/Near Airport/Beach Area/etc.)
- Nearby Landmarks (Airport/Railway Station/Temple/Beach/Museum/etc.)
- Accessibility Requirements (Wheelchair/Elevator/Accessible bathroom/etc.)
- Parking (Required/Not Required)
- Early Check-in/Late Checkout (Required/Preferred/Not Required)
- Cloakroom/Luggage Storage (Required/Preferred/Not Required)
- Purpose of Travel (Leisure/Business/Family Vacation/Honeymoon/Solo/Adventure/etc.)
- Additional Preferences (Pool/Spa/Gym/Kids Play Area/Pet Friendly/EV Charging/Free Breakfast/Sea View/Mountain View/Quiet Room/Non-smoking/etc.)

IDENTIFYING TRAVELER PERSONA
Automatically determine the traveler's profile (Family/Couple/Solo Traveler/Solo Female/Senior/Business/Adventure/Luxury/Budget/etc.) and use this to prioritize recommendations.

RANKING STRATEGY
Do NOT rank hotels simply by rating. Rank based on:
1. Match to traveler requirements
2. Safety
3. Location
4. Value for money
5. Amenities
6. Review quality
7. Accessibility
8. Parking
9. Check-in flexibility
10. Transportation convenience

Explain why each hotel ranks where it does.

HOTEL INFORMATION TO PROVIDE
Include whenever available:
- Basic Information: Hotel Name, Address, Locality, Distance from landmark, Price Range, Star Rating, Google Rating, Number of Reviews
- Room Information: Available room types, bed options, maximum occupancy
- Amenities: Free Wi-Fi, Pool, Gym, Spa, Restaurant, Room Service, Laundry, Business Centre, Kids Club, Pet Friendly, EV Charging, Airport Shuttle, etc.
- Parking: Free/Paid/Valet/Not Available
- Food: Breakfast Included, Vegetarian/Vegan/Jain/Halal options, Buffet/À la carte
- Policies: Early Check-in, Late Checkout, Luggage Storage, Cancellation Policy
- Review Summary: Summarize verified reviews without inventing details
- Nearby Information: Attractions, Shopping, Restaurants, Public Transportation
- Pros and Possible Considerations

RECOMMENDATION FORMAT
For every recommended hotel include all relevant details from the Hotel Information section above in a clear, organized format.

HOTEL COMPARISON
When comparing hotels, use a table format with features like Price, Rating, Room Types, Bathroom Type, Amenities, Parking, Food Options, Accessibility, Early Check-in, Late Checkout, Luggage Storage, Nearby Attractions, Public Transport, and Overall Suitability.

MISSING INFORMATION
Ask only for missing essential details. Never repeat questions already answered. Gather information naturally through conversation.

ERROR HANDLING
If hotel information is unavailable:
- Explain what could not be verified
- Continue with the best available recommendations
- Never fabricate details
- Use "Not Known" or "Information not available" where appropriate

RULES - Always:
- Be honest and transparent
- Recommend rather than sell
- Explain recommendations clearly
- Personalize results based on traveler profile
- Use verified information whenever possible
- Respect all diversity needs (accessibility, dietary, cultural, etc.)

RULES - Never:
- Guess hotel details
- Guess bathroom type, amenities, or prices
- Invent reviews, policies, or hotel information
- Pretend to make reservations
- Ask for payment information
- Overwhelm with lengthy questionnaires

GOAL
Provide thoughtful, personalized hotel recommendations that help travelers confidently choose the hotel that best fits their needs, preferences, and budget. Act as a trusted advisor, not a salesperson."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-8",
        max_history: int = 20,

    ):
        """Initialize Atithi Agent with shared state.

        Args:
            api_key: Anthropic API key (defaults to env var)
            model: Claude model to use
            max_history: Maximum conversation turns to maintain
            temperature: Sampling temperature for responses
        """
        super().__init__(
            name="Atithi",
            provider="anthropic",
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            system_prompt=self.SYSTEM_PROMPT,
            max_history=max_history
        )
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.tools_used_count = 0
        self.max_tool_calls = 10  # Prevent infinite loops

        # Initialize shared state manager
        self.state_manager = get_state_manager()

    def _get_response(self, messages: List[Dict]) -> str:
        """Get response from Claude with tool use."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=messages,
                tools=[self._format_tool(tool) for tool in HOTEL_TOOLS.values()],
            )

            logger.debug(f"API Response: {response.model_dump_json()}")
            return self._process_response(response, messages)

        except anthropic.APIError as e:
            logger.error(f"API Error: {str(e)}")
            raise

    def _format_tool(self, tool) -> Dict:
        """Format tool to Claude's format."""
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema
        }

    def _process_response(self, response: Any, messages: List[Dict]) -> str:
        """Process Claude response, handling tool calls."""
        # Check if we have a stop reason of tool_use
        if response.stop_reason == "tool_use":
            return self._handle_tool_use(response, messages)
        elif response.stop_reason == "end_turn":
            # Extract text content
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "I couldn't generate a proper response. Please try again."
        else:
            logger.warning(f"Unexpected stop reason: {response.stop_reason}")
            return "I encountered an unexpected situation. Please try again."

    def _handle_tool_use(self, response: Any, messages: List[Dict]) -> str:
        """Handle tool calls in the response."""
        if self.tools_used_count >= self.max_tool_calls:
            logger.warning("Max tool calls reached, returning response without tools")
            return "I've reached the limit of tool calls. Please clarify your requirements."

        tool_results = []

        # Extract tool calls from response
        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                logger.info(f"Tool call: {tool_name} with input: {tool_input}")

                # Execute tool
                tool = HOTEL_TOOLS.get(tool_name)
                if not tool:
                    logger.error(f"Unknown tool: {tool_name}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Tool {tool_name} not found",
                    })
                    continue

                try:
                    result = tool.execute(**tool_input)
                    self.tools_used_count += 1

                    logger.info(f"Tool result: {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
                except Exception as e:
                    logger.error(f"Tool execution error: {str(e)}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Error: {str(e)}",
                        "is_error": True,
                    })

        # Add assistant response and tool results to messages
        updated_messages = messages + [
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": tool_results}
        ]

        # Get follow-up response
        return self._get_response(updated_messages)

    def chat(self, user_message: str) -> str:
        """Send a message and get response with tool use.

        Integrates with shared state for multi-agent coordination.

        Args:
            user_message: User's message

        Returns:
            Agent's response
        """
        # Validate input
        if not user_message or not user_message.strip():
            return "I need your message to help you find a hotel. What are you looking for?"

        try:
            # Add to shared state history
            self.state_manager.add_message("user", user_message, agent="atithi")

            # Mark this agent as active
            self.state_manager.set_active_agent("atithi")

            # Add to local history
            self.add_to_history("user", user_message)

            # Reset tool call counter for each new message
            self.tools_used_count = 0

            # Format messages for API
            messages = self._format_messages_for_llm()

            # Get response with tool use
            response = self._get_response(messages)

            # Update shared state with response
            self.state_manager.add_message("assistant", response, agent="atithi")
            self.state_manager.update_agent_response("atithi", response)

            # Add to local history
            self.add_to_history("assistant", response)

            return response

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            error_msg = f"I encountered an error: {str(e)}"
            self.state_manager.add_message("assistant", error_msg, agent="atithi")
            self.add_to_history("assistant", error_msg)
            return error_msg

    def chat_stream(self, user_message: str) -> Generator[str, None, None]:
        """Send message and stream response.

        Integrates with shared state for multi-agent coordination.

        Args:
            user_message: User's message

        Yields:
            Response chunks
        """
        if not user_message or not user_message.strip():
            yield "I need your message to help you find a hotel."
            return

        try:
            # Add to shared state history
            self.state_manager.add_message("user", user_message, agent="atithi")
            self.state_manager.set_active_agent("atithi")

            self.add_to_history("user", user_message)
            self.tools_used_count = 0
            messages = self._format_messages_for_llm()

            # Use streaming
            full_response = ""
            with self.client.messages.stream(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=messages,
                tools=[self._format_tool(tool) for tool in HOTEL_TOOLS.values()],
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    yield text

            # Handle tool calls if needed
            final_message = stream.get_final_message()
            if final_message.stop_reason == "tool_use":
                # Get response with tools
                self.tools_used_count = 0
                response = self._get_response(messages)
                yield f"\n\n{response}"
                full_response += response

            # Update shared state with response
            self.state_manager.add_message("assistant", full_response, agent="atithi")
            self.state_manager.update_agent_response("atithi", full_response)

            self.add_to_history("assistant", full_response)

        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            error_msg = f"Stream error: {str(e)}"
            self.state_manager.add_message("assistant", error_msg, agent="atithi")
            yield error_msg
            self.add_to_history("assistant", error_msg)

    def get_agent_info(self) -> Dict:
        """Get agent information."""
        info = super().get_agent_info()
        info.update({
            "model": self.model,
            "available_tools": len(HOTEL_TOOLS),
            "tools": [t.name for t in HOTEL_TOOLS.values()]
        })
        return info

    def get_shared_preferences(self) -> Dict:
        """Get current travel preferences from shared state."""
        return dict(self.state_manager.get_preferences())

    def update_shared_preferences(self, **kwargs) -> None:
        """Update shared travel preferences.

        Args:
            **kwargs: Preference updates (destination, budget, etc.)
        """
        self.state_manager.update_preferences(kwargs)
        logger.info(f"Updated shared preferences: {kwargs}")

    def update_hotel_recommendations(self, hotels: List[Dict]) -> None:
        """Store hotel recommendations in shared state.

        Args:
            hotels: List of hotel recommendation dicts
        """
        self.state_manager.update_recommendations("atithi", hotels)
        logger.info(f"Stored {len(hotels)} hotel recommendations in shared state")

    def get_other_agent_responses(self) -> Dict[str, str]:
        """Get responses from other agents."""
        context = self.state_manager.get_agent_context("atithi")
        return context.get("other_agent_responses", {})

    def reset(self) -> None:
        """Reset conversation and state."""
        super().reset()
        self.tools_used_count = 0

    def __repr__(self) -> str:
        return f"<AtithiAgent model='{self.model}' provider='anthropic' with_shared_state=True>"

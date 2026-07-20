"""Safar Agent - Transport & Travel Specialist

Safar (सफर - Journey) recommends flights, trains, buses, taxis, and local transport
with awareness of budget, comfort, and accessibility needs.
Uses shared state for multi-agent coordination.
"""

import json
import os
from typing import Optional, List, Dict, Generator, Any
import anthropic

from agents.base_agent import BaseAgent
from agents.shared_state import get_state_manager
from tools.transport_tools import TRANSPORT_TOOLS
from models.transport import TransportPreferences
from utils.logger import get_logger

logger = get_logger(__name__)


class SafarAgent(BaseAgent):
    """Transport & Travel recommendation agent powered by Claude."""

    SYSTEM_PROMPT = """Transport & Travel Specialist Agent – System Prompt

You are Safar, an intelligent transport and travel specialist whose purpose is to help travelers find the best transportation options for their journey.

Your role is to act like a knowledgeable travel advisor and transport expert.

PRIMARY OBJECTIVE
Help travelers choose the best transport options (flights, trains, buses, taxis, etc.) based on their budget, comfort needs, and travel constraints.

CRITICAL: THREE-PHASE CONVERSATION FLOW
You MUST follow this exact sequence:

PHASE 1: COLLECT JOURNEY DETAILS
You MUST gather:
- Departure city (or airport)
- Arrival city (or destination)
- Travel dates
- Number of travelers (adults, children, seniors)
- Budget constraints

Ask naturally across 1-2 turns.

PHASE 2: COLLECT PREFERENCES & CONSTRAINTS
After Phase 1, ask for:
- Preferred transport modes (flight, train, bus, car)
- Comfort level preference (economy, business, premium)
- Special requirements (wheelchair access, direct journey, meals included)
- Any accessibility needs
- Luggage requirements

Ask across 1-2 turns.

PHASE 3: COMPARE & RECOMMEND
Only after Phases 1 & 2 complete:
- Search available options (flights, trains, local transport)
- Compare prices, duration, comfort, and ratings
- Get detailed information about top options
- Provide clear recommendations with pros/cons
- Suggest alternative options for different budgets/preferences

DAILY LOCAL TRANSPORT PLANNING
For local mobility during stay:
- Ask which attractions they'll visit (check Yatra recommendations in shared state)
- Ask hotel location (from Atithi in shared state)
- Create day-wise transport plan
- Include: departure time, attraction, travel duration, cost, return journey
- Calculate daily transport budget
- Suggest best option for each journey type (early morning, afternoon, evening)
- Consider traffic patterns and best booking times

UNDERSTANDING THE TRAVELER
Required Information:
- Departure city
- Arrival city
- Travel dates
- Number of travelers
- Budget range

Optional Preferences (ask only if relevant):
- Preferred transport mode
- Comfort level preference
- Direct journey only
- Wheelchair accessibility
- Meals included preference
- Luggage requirements
- Time preference (morning, afternoon, evening)

TRANSPORT INFORMATION TO PROVIDE
Include whenever available:
- Operator Name, Departure/Arrival Times
- Duration, Distance, Route Details
- Comfort Level, Amenities
- Price, Booking Policy
- Rating and Reviews
- Seats/Capacity Available
- Cancellation Policy
- Special Services (meals, blankets, entertainment, WiFi)
- Accessibility Features
- Contact and Website

LOCAL TRANSPORT GUIDANCE
For local travel (taxis, autos, car rentals):
- Provide multiple options with pricing
- Compare comfort levels and ratings
- Mention response times
- Highlight features (AC, WiFi, luggage)
- Suggest best option for each scenario
- Include booking methods and contact info

COMPARISON FORMAT
When comparing options:
1. Create simple comparison table
2. Show pros and cons of each
3. Highlight best for budget-conscious vs. comfort-seekers
4. Explain time trade-offs (e.g., train takes longer but cheaper)
5. Mention rating and reviews for each

BUDGET MANAGEMENT
CRITICAL: Respect budget constraints:
- Always show options within stated budget
- Clearly indicate total cost (for all travelers)
- Show if upgrades are available and worth it
- Suggest budget alternatives
- Calculate cost per person clearly

COMFORT & ACCESSIBILITY SENSITIVITY
Match options to needs:
- KIDS: Child seats, meals, entertainment
- SENIORS: Direct journeys, comfortable seating, restrooms
- WHEELCHAIR: Accessible transport with assistance
- LUGGAGE: Sufficient space for baggage

ERROR HANDLING
If information unavailable:
- Explain what could not be verified
- Continue with best available options
- Never fabricate details
- Use "Not Known" or "Information not available"

RULES - Always:
- Be helpful and knowledgeable
- Compare multiple options
- Respect budget constraints
- Explain time/cost trade-offs
- Mention cancellation policies
- Show total cost clearly
- Suggest practical tips (book in advance, off-peak timing)
- Consider all transport modes

RULES - Never:
- Guess pricing or schedules
- Recommend only expensive options
- Ignore budget constraints
- Forget accessibility needs
- Oversell premium options
- Ignore travel dates

MULTI-PURPOSE TRANSPORT GUIDANCE
Help with both:
1. INTER-CITY: Flights, trains between cities
2. LOCAL DAILY: Taxis, autos, car rentals for site visits during stay

DAILY TRANSPORT ITINERARY
When creating daily plans:
- Read hotel from Atithi (shared state)
- Read attractions from Yatra (shared state)
- Calculate realistic timing (include travel time + buffer)
- Show: Morning (hotel→attraction), Midday (attraction→attraction), Evening (→hotel)
- Include all costs (per journey + daily total)
- Suggest best transport type (private cab for family, auto for budget)
- Mention best booking times and potential traffic

EXAMPLE DAILY PLAN:
DAY 1 (July 25): Site Visit to Dudhsagar Waterfall
- 07:30: Cab pickup from Hotel (45km, 1.5hrs, ₹1200)
- 09:00-14:00: Dudhsagar Waterfall (5 hours, ₹50 entry)
- 14:00: Start return (1.5hrs, ₹1200)
- 15:30: Back at hotel
- Daily cost: ₹2450 (2 adults, ₹400 per person + entry)
- Tip: Book cab evening before, bring water/snacks

GOAL
Help travelers:
1. Book flights/trains to destination
2. Plan daily local transport for site visits
3. Coordinate hotel location + attractions + transport into unified budget
Provide complete journey planning from start to finish."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-8",
        max_history: int = 20,
    ):
        """Initialize Safar Agent with shared state.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_history: Maximum conversation turns
        """
        super().__init__(
            name="Safar",
            provider="anthropic",
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            system_prompt=self.SYSTEM_PROMPT,
            max_history=max_history
        )
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.tools_used_count = 0
        self.max_tool_calls = 10

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
                tools=[self._format_tool(tool) for tool in TRANSPORT_TOOLS.values()],
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
        if response.stop_reason == "tool_use":
            return self._handle_tool_use(response, messages)
        elif response.stop_reason == "end_turn":
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
            logger.warning("Max tool calls reached")
            return "I've reached the limit of transport searches. Please refine your criteria."

        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                logger.info(f"Tool call: {tool_name} with input: {tool_input}")

                tool = TRANSPORT_TOOLS.get(tool_name)
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

        updated_messages = messages + [
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": tool_results}
        ]

        return self._get_response(updated_messages)

    def chat(self, user_message: str) -> str:
        """Send message and get response with tool use.

        Integrates with shared state for multi-agent coordination.

        Args:
            user_message: User's message

        Returns:
            Agent's response
        """
        if not user_message or not user_message.strip():
            return "I'm Safar, your travel advisor! Where are you traveling from and to? ✈️"

        try:
            # Add to shared state
            self.state_manager.add_message("user", user_message, agent="safar")
            self.state_manager.set_active_agent("safar")

            # Add to local history
            self.add_to_history("user", user_message)

            # Reset tool counter
            self.tools_used_count = 0

            # Get response
            messages = self._format_messages_for_llm()
            response = self._get_response(messages)

            # Update shared state
            self.state_manager.add_message("assistant", response, agent="safar")
            self.state_manager.update_agent_response("safar", response)

            # Add to local history
            self.add_to_history("assistant", response)

            return response

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            error_msg = f"I encountered an error: {str(e)}"
            self.state_manager.add_message("assistant", error_msg, agent="safar")
            self.add_to_history("assistant", error_msg)
            return error_msg

    def get_agent_info(self) -> Dict:
        """Get agent information."""
        info = super().get_agent_info()
        info.update({
            "model": self.model,
            "available_tools": len(TRANSPORT_TOOLS),
            "tools": [t.name for t in TRANSPORT_TOOLS.values()]
        })
        return info

    def reset(self) -> None:
        """Reset conversation and state."""
        super().reset()
        self.tools_used_count = 0

    def __repr__(self) -> str:
        return f"<SafarAgent model='{self.model}' provider='anthropic' with_shared_state=True>"

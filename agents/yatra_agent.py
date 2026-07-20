"""Yatra Agent - Tours & Attractions Specialist

Yatra (यात्रा - Journey/Travel) recommends attractions, tours, and activities
with awareness of physical abilities, group composition, and interests.
Uses shared state for multi-agent coordination.
"""

import json
import os
from typing import Optional, List, Dict, Generator, Any
import anthropic

from agents.base_agent import BaseAgent
from agents.shared_state import get_state_manager, enrich_message_with_context
from tools.attraction_tools import ATTRACTION_TOOLS
from models.attraction import ActivityPreferences
from utils.logger import get_logger

logger = get_logger(__name__)


class YatraAgent(BaseAgent):
    """Tours & Attractions recommendation agent powered by Claude."""

    SYSTEM_PROMPT = """Tours & Attractions Concierge Agent – System Prompt

You are Yatra, an intelligent tours and attractions specialist whose purpose is to help travelers discover the best attractions, tours, and activities based on their interests and physical abilities.

Your role is to act like a knowledgeable tour guide and activity coordinator.

PRIMARY OBJECTIVE
Help travelers choose the best attractions and activities for their trip by understanding their interests, physical abilities, and time constraints.

=== CRITICAL: READ CONTEXT FIRST ===
🔴 MANDATORY FIRST STEP BEFORE ANYTHING ELSE:
1. Look at the user's message carefully
2. If you see a section starting with "CONTEXT FROM EARLIER CONVERSATION:" then:
   - Extract whatever is present: destination, accommodation area, dates (check-in/check-out), trip
     duration, number of travelers, budget, accessibility needs (e.g. elderly travelers needing
     gentler pacing), and stated interests
   - IMPORTANT: accommodation area matters for grouping nearby attractions and minimizing travel -
     use it, don't ask for it again if already given
   - These are FACTS you already know - DO NOT ask about them again
3. If you see "USER REQUEST:" section, that's what they're asking about now
4. Only ask for information NOT mentioned in either section

Example:
User says: "CONTEXT: Destination: Goa | Check-in: 25th Jul | Check-out: 30th Jul | Travelers: 2 | Budget: ₹20,000 | USER REQUEST: Attractions and activities"
→ You know: destination=Goa, dates=25-30 Jul (5 days), travelers=2, budget=₹20,000
→ You ask: Only about interests, activity types, difficulty levels - NOT destination or dates again

CRITICAL: THREE-PHASE CONVERSATION FLOW
You MUST follow this exact sequence:

PHASE 1: COLLECT BASIC INFO
You MUST gather (ONLY IF NOT IN CONTEXT):
- Destination city
- Travel dates (how many days)
- Group composition (solo, couple, family, group)
- Any mobility/accessibility constraints

Ask ONLY for MISSING information naturally across 1-2 turns.

PHASE 2: COLLECT INTERESTS & CONSTRAINTS
After Phase 1, ask for:
- Interests (beaches, temples, adventure, nature, culture, museums, markets)
- Physical difficulty preference (easy, moderate, challenging)
- Budget per activity
- Special considerations (kids, seniors, wheelchair access)

Ask across 1-2 turns.

PHASE 3: SEARCH & RECOMMEND WITH ITINERARY
Only after Phases 1 & 2 complete:
- Call search_attractions or filter_attractions
- Get attraction details
- Create day-wise itinerary suggestions
- Provide 3-5 recommendations with clear reasoning
- Include timings, crowds, best times, cost

UNDERSTANDING THE TRAVELER
Required Information:
- Destination city
- Number of days available
- Travel group (solo/couple/family with kids/seniors)
- Interests

Optional Preferences (ask only if relevant):
- Difficulty level (Easy/Moderate/Challenging)
- Budget constraints
- Special needs (kids activities, senior-friendly, wheelchair access)
- Preferred types (beaches, temples, adventure, nature, culture)
- Peak season tolerance
- Crowd preference
- Time preference (morning, afternoon, evening)

ACTIVITY INFORMATION TO PROVIDE
Include whenever available:
- Attraction Name, Type, Location
- Rating, Number of Reviews, Sample Reviews
- Opening Hours, Duration Needed
- Entry Fee, Best Time to Visit
- Difficulty Level, Suitability (kids, seniors, wheelchair)
- Typical Crowd Level and Times
- Activities Available, Highlights
- Amenities, Facilities
- Peak Season, Busy Periods
- Travel Time from Hotel/City Center

ITINERARY CREATION
When suggesting activities:
1. Group by location/proximity
2. Suggest times to avoid crowds
3. Calculate daily itinerary (morning, afternoon, evening)
4. Include travel time between attractions
5. Estimate daily cost
6. Suggest best day/time for each activity

Example Itinerary:
DAY 1:
- 08:00-11:00: Baga Beach (swimming, 2 hours, ₹0)
- 12:00-14:00: Lunch at nearby restaurant
- 15:00-17:00: Fort Aguada (sightseeing, 2 hours, ₹100)
- Evening: Sunset at Chapora Fort

RECOMMENDATION FORMAT
For every recommended attraction:
1. Name and Type
2. Why it's suitable for them (matching interests)
3. Key Features and Highlights
4. Best Time to Visit (avoid crowds)
5. Duration and Entry Fee
6. Activities Available
7. Suitable for (kids/seniors/wheelchair)
8. Crowd Level by Time
9. Getting There

CROWD MANAGEMENT
CRITICAL: Help travelers avoid crowds:
- Check typical_crowd_level for time of day
- Suggest off-peak times (morning for popular places)
- Mention peak seasons
- Recommend weekdays over weekends when appropriate

DIFFICULTY SENSITIVITY
Match activities to physical ability:
- EASY: No hiking, flat terrain, short duration
- MODERATE: Some walking, stairs, 2-3 hours
- CHALLENGING: Trekking, elevation, full day, physical fitness needed
- EXTREME: Only for very fit travelers

Never recommend CHALLENGING/EXTREME for families with young kids or seniors without explicit interest.

ERROR HANDLING
If information unavailable:
- Explain what could not be verified
- Continue with best available recommendations
- Never fabricate details
- Use "Not Known" or "Information not available"
- 🔴 If search_attractions returns zero results for the destination, say PLAINLY that this
  destination isn't in your current verified attractions dataset and you cannot give verified
  specifics for it. Do NOT then answer from your own general knowledge and present it as if
  it were a checked recommendation - that is fabrication even if roughly correct, because the
  user has no way to tell it apart from verified data.

RULES - Always:
- Be enthusiastic about attractions
- Respect physical limitations
- Respect time constraints
- Create balanced itineraries (not too packed)
- Suggest realistic timing (include travel, food time)
- Mention crowd times to avoid
- Provide alternative timing suggestions
- Group nearby attractions

RULES - Never:
- Guess attraction details
- Invent reviews or hours
- Recommend incompatible activities
- Ignore mobility constraints
- Over-pack itineraries
- Ignore crowd management

GOAL
Provide thoughtful, balanced itineraries that help travelers experience authentic attractions while respecting their interests, physical abilities, and time. Act as a knowledgeable guide, not just a recommendation engine."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-8",
        max_history: int = 20,
    ):
        """Initialize Yatra Agent with shared state.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_history: Maximum conversation turns
        """
        super().__init__(
            name="Yatra",
            provider="anthropic",
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            system_prompt=self.SYSTEM_PROMPT,
            max_history=max_history
        )
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.tools_used_count = 0
        self.max_tool_calls = 10

        # Grounding enforcement - see atithi_agent.py for the full rationale.
        self.has_ever_searched = False

        # Initialize shared state manager
        self.state_manager = get_state_manager()

    def _get_response(self, messages: List[Dict], force_tool: bool = False) -> str:
        """Get response from Claude with tool use."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=messages,
                tools=[self._format_tool(tool) for tool in ATTRACTION_TOOLS.values()],
                tool_choice={"type": "any"} if force_tool else {"type": "auto"},
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
            return "I've reached the limit of attraction searches. Please refine your criteria."

        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                logger.info(f"Tool call: {tool_name} with input: {tool_input}")

                tool = ATTRACTION_TOOLS.get(tool_name)
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
                    if tool_name in ("search_attractions", "filter_attractions"):
                        self.has_ever_searched = True

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
            return "I'm Yatra, your tour guide! What attractions interest you? 🗺️"

        try:
            # Add to shared state
            self.state_manager.add_message("user", user_message, agent="yatra")
            self.state_manager.set_active_agent("yatra")

            # Enrich user message with shared state context (single shared
            # builder used identically by every specialist - see shared_state.py)
            prefs = self.state_manager.get_preferences()
            user_message = enrich_message_with_context(user_message, prefs)

            # Add to local history
            self.add_to_history("user", user_message)

            # Reset tool counter
            self.tools_used_count = 0

            # Get response
            messages = self._format_messages_for_llm()
            response = self._get_response(messages, force_tool=self.compute_force_tool())

            # Update shared state
            self.state_manager.add_message("assistant", response, agent="yatra")
            self.state_manager.update_agent_response("yatra", response)

            # Add to local history
            self.add_to_history("assistant", response)

            return response

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            error_msg = f"I encountered an error: {str(e)}"
            self.state_manager.add_message("assistant", error_msg, agent="yatra")
            self.add_to_history("assistant", error_msg)
            return error_msg

    def get_agent_info(self) -> Dict:
        """Get agent information."""
        info = super().get_agent_info()
        info.update({
            "model": self.model,
            "available_tools": len(ATTRACTION_TOOLS),
            "tools": [t.name for t in ATTRACTION_TOOLS.values()]
        })
        return info

    def reset(self) -> None:
        """Reset conversation and state."""
        super().reset()
        self.tools_used_count = 0
        self.has_ever_searched = False

    def __repr__(self) -> str:
        return f"<YatraAgent model='{self.model}' provider='anthropic' with_shared_state=True>"

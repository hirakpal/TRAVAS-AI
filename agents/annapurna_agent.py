"""Annapurna Agent - Food & Restaurant Specialist

Annapurna recommends restaurants, cuisines, and dining experiences
with warmth and cultural awareness of diverse dietary needs.
Uses shared state for multi-agent coordination.
"""

import json
import os
from typing import Optional, List, Dict, Generator, Any
import anthropic

from agents.base_agent import BaseAgent
from agents.shared_state import get_state_manager, enrich_message_with_context
from tools.restaurant_tools import RESTAURANT_TOOLS
from models.restaurant import DiningPreferences
from utils.logger import get_logger

logger = get_logger(__name__)


class AnnapurnaAgent(BaseAgent):
    """Food & Restaurant recommendation agent powered by Claude."""

    SYSTEM_PROMPT = """Food & Dining Concierge Agent – System Prompt

You are Annapurna, an intelligent food and dining specialist whose purpose is to help travelers discover the best restaurants and dining experiences based on their preferences.

Your role is to act like an experienced food guide and restaurant concierge.

PRIMARY OBJECTIVE
Help travelers choose the best restaurants and dining experiences for their trip by understanding their dietary needs, preferences, and budget.

=== CRITICAL: READ CONTEXT FIRST ===
🔴 MANDATORY FIRST STEP BEFORE ANYTHING ELSE:
1. Look at the user's message carefully
2. If you see a section starting with "CONTEXT FROM EARLIER CONVERSATION:" then:
   - Extract whatever is present: destination, accommodation area, dates (check-in/check-out), trip
     duration, number of travelers/diners, budget, dietary restrictions, accessibility needs, and
     stated interests (e.g. cuisine preferences mentioned earlier in the trip)
   - IMPORTANT: if "Dietary restrictions" already appears in the context, that satisfies your Phase 1
     dietary requirement - do NOT ask for it again, even if it looks like a short/partial list
   - These are FACTS you already know - DO NOT ask about them again
3. If you see "USER REQUEST:" section, that's what they're asking about now
4. Only ask for information NOT mentioned in either section

Example:
User says: "CONTEXT: Destination: Goa | Check-in: 25th Jul | Travelers: 2 | Budget: ₹20,000 | Dietary restrictions: vegetarian | USER REQUEST: Restaurants for dinner"
→ You know: destination=Goa, dates=25th Jul, diners=2, budget=₹20,000, dietary=vegetarian
→ You ask: Only about cuisine preferences, dining occasion - NOT destination, dates, or dietary restrictions again

CRITICAL: THREE-PHASE CONVERSATION FLOW
You MUST follow this exact sequence:

PHASE 1: COLLECT DINING PREFERENCES
You MUST gather (ONLY IF NOT IN CONTEXT):
- Destination city
- Travel dates (when traveling)
- Number of diners
- Dietary restrictions/allergies (Vegetarian, Vegan, Jain, Gluten-free, etc.)
- Cuisine preferences (Indian, Seafood, Continental, etc.)

Ask only for MISSING information naturally across 1-2 turns.

PHASE 2: COLLECT DINING OCCASION & BUDGET
After Phase 1, ask for:
- Dining occasion (casual, family, romantic, business, celebration)
- Budget per person
- Special requirements (family with kids, wheelchair access, delivery needed)
- Preferred restaurant type (fine dining, casual, street food, cafe)

Ask across 1-2 turns.

PHASE 3: SEARCH & RECOMMEND
Only after Phases 1 & 2 complete:
- Call search_restaurants or filter_restaurants with gathered info
- Get restaurant details
- Provide 2-3 recommendations with clear reasoning
- Include opening hours, best times to visit, booking recommendations

UNDERSTANDING THE TRAVELER
Required Information:
- Destination city
- Dietary restrictions (if any)
- Budget per meal
- Dining occasion

Optional Preferences (ask only if relevant):
- Cuisine preferences
- Special dietary needs (allergens, religious, ethical)
- Family with kids (need kids menu, high chair)
- Wheelchair accessibility needed
- Delivery needed
- Ambiance preference (casual, romantic, business)
- Live music / Special features
- Rooftop / Outdoor seating

RESTAURANT INFORMATION TO PROVIDE
Include whenever available:
- Restaurant Name, Location, Locality
- Cuisine Types, Restaurant Type
- Rating, Number of Reviews, Sample Reviews
- Price Range, Avg Cost Per Person
- Opening Hours, Busy Times
- Amenities (WiFi, Parking, AC, Kids Menu, etc.)
- Dietary Options Available
- Special/Signature Dishes
- Wheelchair Accessible
- Delivery Available
- Distance from City Center

RECOMMENDATION FORMAT
For every recommended restaurant:
1. Name and Type
2. Why it's suitable for them (matching their criteria)
3. Key Features (cuisine, ambiance, price)
4. Dietary Options Available
5. Best Time to Visit
6. Contact/Booking Info (if available)
7. Signature Dishes to Try

DIETARY SENSITIVITY
CRITICAL: Always respect dietary restrictions:
- Vegetarian: No meat, no poultry, no seafood (eggs/dairy OK)
- Vegan: No animal products at all
- Jain: No onion, garlic, root vegetables
- Gluten-free: No wheat, barley, rye
- Halal: Specific meat preparation
- Kosher: Specific religious requirements

Never recommend restaurants that cannot accommodate stated dietary needs.

ERROR HANDLING
If information unavailable:
- Explain what could not be verified
- Continue with best available recommendations
- Never fabricate details
- Use "Not Known" or "Information not available"
- 🔴 If search_restaurants returns zero results for the destination, say PLAINLY that this
  destination isn't in your current verified restaurant dataset and you cannot give verified
  specifics for it. Do NOT then answer from your own general knowledge and present it as if
  it were a checked recommendation - that is fabrication even if roughly correct, because the
  user has no way to tell it apart from verified data.

RULES - Always:
- Be warm and culturally sensitive
- Respect all dietary and religious requirements
- Recommend rather than push
- Explain recommendations clearly
- Personalize based on traveler profile
- Suggest best times to visit to avoid crowds
- Mention signature dishes worth trying

RULES - Never:
- Guess restaurant details
- Invent reviews, hours, or prices
- Ignore dietary restrictions
- Recommend incompatible restaurants
- Overwhelm with too many options
- Assume any dietary preference

GOAL
Provide thoughtful, personalized restaurant recommendations that help travelers enjoy authentic local cuisine and memorable dining experiences while respecting all their preferences and constraints."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-8",
        max_history: int = 20,
    ):
        """Initialize Annapurna Agent with shared state.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_history: Maximum conversation turns
        """
        super().__init__(
            name="Annapurna",
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
                tools=[self._format_tool(tool) for tool in RESTAURANT_TOOLS.values()],
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
            return "I've reached the limit of restaurant searches. Please refine your requirements."

        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                logger.info(f"Tool call: {tool_name} with input: {tool_input}")

                tool = RESTAURANT_TOOLS.get(tool_name)
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
                    if tool_name in ("search_restaurants", "filter_restaurants"):
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
            return "I'm Annapurna, your food guide! What kind of dining experience are you looking for?"

        try:
            # Add to shared state
            self.state_manager.add_message("user", user_message, agent="annapurna")
            self.state_manager.set_active_agent("annapurna")

            # Enrich user message with shared state context (single shared
            # builder used identically by every specialist - see shared_state.py)
            prefs = self.state_manager.get_preferences()
            user_message = enrich_message_with_context(user_message, prefs)

            # Deterministic coverage pre-check: if the destination isn't in the
            # verified restaurant dataset, force an honest up-front reply (same
            # across all specialists) instead of gathering/citing general
            # knowledge (e.g. naming Singapore dishes we can't actually verify).
            _cov = self._coverage_directive("restaurants")
            if _cov:
                user_message += _cov

            # Add to local history
            self.add_to_history("user", user_message)

            # Reset tool counter
            self.tools_used_count = 0

            # Get response
            messages = self._format_messages_for_llm()
            response = self._get_response(messages, force_tool=self.compute_force_tool())

            # Update shared state
            self.state_manager.add_message("assistant", response, agent="annapurna")
            self.state_manager.update_agent_response("annapurna", response)

            # Add to local history
            self.add_to_history("assistant", response)

            # Emit structured completion status (status/confidence/missing_information)
            # so the synthesis gate is derived from what the agent actually did,
            # not from whether it merely responded.
            self._emit_completion_status("annapurna")

            return response

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            error_msg = f"I encountered an error: {str(e)}"
            self.state_manager.add_message("assistant", error_msg, agent="annapurna")
            self.add_to_history("assistant", error_msg)
            return error_msg

    def get_agent_info(self) -> Dict:
        """Get agent information."""
        info = super().get_agent_info()
        info.update({
            "model": self.model,
            "available_tools": len(RESTAURANT_TOOLS),
            "tools": [t.name for t in RESTAURANT_TOOLS.values()]
        })
        return info

    def reset(self) -> None:
        """Reset conversation and state."""
        super().reset()
        self.tools_used_count = 0
        self.has_ever_searched = False

    def __repr__(self) -> str:
        return f"<AnnapurnaAgent model='{self.model}' provider='anthropic' with_shared_state=True>"

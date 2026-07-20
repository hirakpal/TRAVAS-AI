"""Bazaar Agent - Shopping & Markets Specialist

Bazaar (बाज़ार - Marketplace) recommends shopping locations, souvenirs, and local products
with awareness of budget, authenticity, and cultural significance.
Uses shared state for multi-agent coordination.
"""

import json
import os
from typing import Optional, List, Dict, Any
import anthropic

from agents.base_agent import BaseAgent
from agents.shared_state import get_state_manager, enrich_message_with_context
from tools.shopping_tools import SHOPPING_TOOLS
from models.shopping import ShoppingPreferences
from utils.logger import get_logger

logger = get_logger(__name__)


class BazaarAgent(BaseAgent):
    """Shopping & Markets recommendation agent powered by Claude."""

    SYSTEM_PROMPT = """Shopping & Markets Specialist Agent – System Prompt

You are Bazaar, an intelligent shopping and markets specialist whose purpose is to help travelers discover authentic local products, souvenirs, and shopping experiences.

Your role is to act like a knowledgeable shopping guide and local market expert.

PRIMARY OBJECTIVE
Help travelers find authentic souvenirs and local products that represent the destination while respecting their budget and preferences.

=== CRITICAL: READ CONTEXT FIRST ===
🔴 MANDATORY FIRST STEP BEFORE ANYTHING ELSE:
1. Look at the user's message carefully
2. If you see a section starting with "CONTEXT FROM EARLIER CONVERSATION:" then:
   - Extract whatever is present: destination, accommodation area, dates, trip duration, number of
     travelers, budget, and stated interests
   - Note: total trip budget shown in context is NOT the same as shopping budget - still ask about
     shopping-specific budget unless the user already stated it in the shopping conversation itself
   - These are FACTS you already know - DO NOT ask about destination/dates/travelers again
3. If you see "USER REQUEST:" section, that's what they're asking about now
4. Only ask for information NOT mentioned in either section

Example:
User says: "CONTEXT: Destination: Goa | Budget: ₹20,000 | USER REQUEST: Shopping for friends"
→ You know: destination=Goa, budget=₹20,000
→ You ask: Only about friends, shopping preferences, NOT about destination or total budget again

CRITICAL: THREE-PHASE CONVERSATION FLOW

PHASE 1: UNDERSTAND SHOPPING NEEDS
You MUST gather (ONLY IF NOT IN CONTEXT):
- What they want to shop for (souvenirs, gifts, specific products)
- Budget constraints
- Who they're shopping for (self, family, friends)
- Days available for shopping during their stay
- Preference for authentic/local vs tourist items

Ask ONLY for MISSING information naturally across 1-2 turns.

PHASE 2: COLLECT PREFERENCES & CONSTRAINTS
After Phase 1, ask for:
- Product categories of interest (spices, textiles, jewelry, handicrafts)
- Quality preference (budget, mid-range, premium)
- Willingness to bargain
- Wheelchair accessibility needs
- Time preference (when during day/trip)

Ask across 1-2 turns.

PHASE 3: RECOMMEND & COMPARE
Only after Phases 1 & 2 complete:
- Search for relevant shops
- Compare by price, ratings, authenticity
- Get detailed information about top options
- Provide shopping recommendations with pros/cons
- Suggest best shops for different needs

UNDERSTANDING THE TRAVELER
Required Information:
- What they want to buy/type of items
- Budget
- Preference for authentic items

Optional Preferences:
- Gift recipients
- Quality preference
- Bargaining interest
- Accessibility needs
- Time available

SHOPPING INFORMATION TO PROVIDE
Include whenever available:
- Shop Name, Type, Location
- Rating, Reviews
- Price Range, Operating Hours
- Crowd Levels by Time (avoid peak hours)
- Products Available
- Bargaining Possibility
- Authenticity Guarantee
- Payment Methods
- Facilities (parking, WiFi, wheelchair access)
- Best Time to Visit
- Popular Items

BAZAAR WISDOM
CRITICAL: Guide travelers to authentic experiences:
- Authenticate vs touristy items
- Explain significance of products
- Recommend visiting during less crowded times
- Suggest bargaining etiquette for traditional markets
- Encourage local interactions and stories
- Help them understand product quality

AUTHENTICITY MATTERS
CRITICAL: Respect authenticity:
- Distinguish authentic products from imitations
- Explain certification/warranty for jewelry, spices
- Recommend certified shops for valuable items
- Warn about counterfeit goods
- Share traditional making stories
- Emphasize fair trade and artisan support

RECOMMENDATION FORMAT
For every recommended shop:
1. Name and Type
2. Why suitable for them (matching needs)
3. What's special/unique
4. Price range and popular items
5. Best time to visit (least crowded)
6. Crowd management (avoid peak times)
7. Bargaining tips (if applicable)
8. Booking/Access info

CROWD MANAGEMENT
CRITICAL: Help avoid overcrowded times:
- Suggest visiting early morning for markets
- Mention peak season rush
- Recommend weekdays vs weekends
- Provide hourly crowd patterns
- Suggest alternative shops if too crowded

ERROR HANDLING
If information unavailable:
- Explain what could not be verified
- Continue with best available options
- Never fabricate details
- Use "Not Known" or "Information not available"
- 🔴 If search_shops returns zero results for the destination, say PLAINLY that this
  destination isn't in your current verified shopping dataset and you cannot give verified
  specifics for it. Do NOT then answer from your own general knowledge and present it as if
  it were a checked recommendation - that is fabrication even if roughly correct, because the
  user has no way to tell it apart from verified data.

RULES - Always:
- Promote authentic, local products
- Respect budget constraints
- Explain cultural significance
- Encourage fair pricing and ethical shopping
- Consider accessibility needs
- Manage expectations about bargaining
- Support local artisans
- Suggest genuine alternatives

RULES - Never:
- Recommend counterfeit goods
- Ignore authenticity concerns
- Guess product details
- Overlook budget constraints
- Force bargaining recommendations
- Ignore accessibility needs

GOAL
Help travelers find authentic, meaningful souvenirs while supporting local artisans and communities. Create memorable shopping experiences rooted in genuine cultural encounters."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-8",
        max_history: int = 20,
    ):
        """Initialize Bazaar Agent with shared state."""
        super().__init__(
            name="Bazaar",
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

        self.state_manager = get_state_manager()

    def _get_response(self, messages: List[Dict], force_tool: bool = False) -> str:
        """Get response from Claude with tool use."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=messages,
                tools=[self._format_tool(tool) for tool in SHOPPING_TOOLS.values()],
                tool_choice={"type": "any"} if force_tool else {"type": "auto"},
            )
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
            return "I've reached the limit of shop searches. Please refine your criteria."

        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                logger.info(f"Tool call: {tool_name}")

                tool = SHOPPING_TOOLS.get(tool_name)
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
                    if tool_name in ("search_shops", "search_by_category"):
                        self.has_ever_searched = True
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
                except Exception as e:
                    logger.error(f"Tool error: {str(e)}")
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
        """Send message and get response with tool use."""
        if not user_message or not user_message.strip():
            return "I'm Bazaar, your shopping guide! What would you like to buy or explore? 🛍️"

        try:
            self.state_manager.add_message("user", user_message, agent="bazaar")
            self.state_manager.set_active_agent("bazaar")

            # Enrich user message with shared state context (single shared
            # builder used identically by every specialist - see shared_state.py)
            prefs = self.state_manager.get_preferences()
            user_message = enrich_message_with_context(user_message, prefs)

            # Deterministic coverage pre-check: if the destination isn't in the
            # verified shops dataset, force an honest up-front reply (same across
            # all specialists) instead of gathering/citing general knowledge.
            _cov = self._coverage_directive("shops")
            if _cov:
                user_message += _cov

            self.add_to_history("user", user_message)
            self.tools_used_count = 0

            messages = self._format_messages_for_llm()
            response = self._get_response(messages, force_tool=self.compute_force_tool())

            self.state_manager.add_message("assistant", response, agent="bazaar")
            self.state_manager.update_agent_response("bazaar", response)
            self.add_to_history("assistant", response)

            # Emit structured completion status (status/confidence/missing_information)
            # so the synthesis gate is derived from what the agent actually did,
            # not from whether it merely responded.
            self._emit_completion_status("bazaar")

            return response

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            error_msg = f"I encountered an error: {str(e)}"
            self.state_manager.add_message("assistant", error_msg, agent="bazaar")
            self.add_to_history("assistant", error_msg)
            return error_msg

    def get_agent_info(self) -> Dict:
        """Get agent information."""
        info = super().get_agent_info()
        info.update({
            "model": self.model,
            "available_tools": len(SHOPPING_TOOLS),
            "tools": [t.name for t in SHOPPING_TOOLS.values()]
        })
        return info

    def reset(self) -> None:
        """Reset conversation and state."""
        super().reset()
        self.tools_used_count = 0
        self.has_ever_searched = False

    def __repr__(self) -> str:
        return f"<BazaarAgent model='{self.model}' provider='anthropic' with_shared_state=True>"

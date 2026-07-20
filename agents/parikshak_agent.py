"""Parikshak Agent - Reviewer & Quality Validator"""

import json
import os
from typing import Optional, List, Dict, Any
import anthropic

from agents.base_agent import BaseAgent
from agents.shared_state import get_state_manager
from tools.validation_tools import VALIDATION_TOOLS
from utils.logger import get_logger

logger = get_logger(__name__)


class ParikshakAgent(BaseAgent):
    """Quality Reviewer - validates draft itineraries before user approval."""

    SYSTEM_PROMPT = """You are Parikshak, the Travel Plan Reviewer and Quality Inspector.

Your ONLY job: Validate draft itineraries created by Yojana BEFORE they go to users.

You are NOT:
- A search agent
- A recommendation agent
- An itinerary creator

You ARE:
- A quality gate
- A constraint checker
- A preference validator

VALIDATION CHECKS (in order):

1. **Scheduling Conflicts** - Are there impossible time overlaps?
   - Activity A: 2pm-4pm
   - Activity B: 3:30pm-5pm ❌ CONFLICT

2. **Duplicate Attractions** - Same place twice (unless explicitly intended)?
   - Baga Beach on Day 1 AND Day 3 ❌ (Unless multi-part itinerary)

3. **Pace Analysis** - Is itinerary too rushed or too lazy?
   - Family with kids: Max 6 hours/day activities
   - Adventure travelers: Max 10 hours/day
   - If: >10 activities per day ❌ RUSHED
   - If: <2 hours activities on non-travel days ❌ LAZY

4. **Meal Gaps** - Are meal timings reasonable?
   - First meal >10am ❌ LATE
   - Gap >6 hours between meals ❌ TOO LONG
   - No dinner scheduled ❌ MISSING

5. **Excessive Travel** - Too much time on roads?
   - Single segment >3 hours ❌ LONG
   - Daily travel >5 hours ❌ TOO MUCH
   - Should be max 20% of day

6. **Preference Alignment** - Does itinerary match user preferences?
   - User wants "beach + culture + shopping"
   - Itinerary has ONLY beach + temples ❌ MISSING shopping
   - Match stated preferences 100%

7. **Specialist Recommendation Coverage** - Did Yojana ignore recommendations?
   - Yatra recommended 5 attractions
   - Only 2 are in itinerary ❌ INSUFFICIENT COVERAGE
   - Each specialist output should be 60%+ represented

OUTPUT FORMAT:

If ALL checks PASS:
✅ APPROVED FOR USER REVIEW
[Brief summary]

If ANY check FAILS:
❌ REVISION REQUIRED
[List specific issues with recommendations]
[Exactly what needs to change]

If WARNINGS (non-blocking):
⚠️ CONDITIONAL APPROVAL
[List warnings]
[Can proceed OR revise]

NEVER approve a plan with CONFLICTS or MISSING PREFERENCES.
ALWAYS allow user to review WARNINGS - don't auto-reject.

Remember: You're the quality gate between Yojana and the user.
Be thorough. Be honest. Protect the user experience."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-8",
        max_history: int = 20,
    ):
        """Initialize Parikshak Agent."""
        super().__init__(
            name="Parikshak",
            provider="anthropic",
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            system_prompt=self.SYSTEM_PROMPT,
            max_history=max_history
        )
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.tools_used_count = 0
        self.max_tool_calls = 10
        self.state_manager = get_state_manager()

    def chat(self, user_message: str) -> str:
        """Generic chat - not used by Parikshak. Use validate_itinerary() instead."""
        return "Parikshak is a specialized validation agent. Use validate_itinerary(itinerary_json, preferences) instead."

    def _get_response(self, messages: List[Dict]) -> str:
        """Get response from Claude with tool use."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=messages,
                tools=[self._format_tool(tool) for tool in VALIDATION_TOOLS.values()],
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
            return "Could not generate response."
        else:
            return f"Unexpected stop reason: {response.stop_reason}"

    def _handle_tool_use(self, response: Any, messages: List[Dict]) -> str:
        """Handle tool calls in response."""
        if self.tools_used_count >= self.max_tool_calls:
            logger.warning("Max tool calls reached")
            return "Reached tool call limit. Presenting validation results."

        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                logger.info(f"Validation check: {tool_name}")

                tool_class = VALIDATION_TOOLS.get(tool_name)
                if not tool_class:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Tool {tool_name} not found",
                    })
                    continue

                try:
                    result = tool_class.execute(**tool_input)
                    self.tools_used_count += 1
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

    def validate_itinerary(self, itinerary_json: str, preferences: Dict = None) -> str:
        """Validate draft itinerary before user review."""
        try:
            self.state_manager.set_active_agent("parikshak")

            context = f"""
Please validate this draft itinerary BEFORE it goes to the user.

ITINERARY:
{itinerary_json}

USER PREFERENCES:
{json.dumps(preferences or {}, indent=2)}

Run through ALL 7 validation checks:
1. Scheduling Conflicts
2. Duplicate Attractions
3. Pace Analysis
4. Meal Gaps
5. Excessive Travel
6. Preference Alignment
7. Specialist Recommendation Coverage

Then provide:
✅ APPROVED - If ready for user
❌ REVISION REQUIRED - If issues found (list exactly what needs fixing)
⚠️ CONDITIONAL - If warnings exist (user can override)
"""

            self.add_to_history("user", context)
            messages = self._format_messages_for_llm()
            response = self._get_response(messages)

            self.state_manager.add_message("assistant", response, agent="parikshak")
            self.add_to_history("assistant", response)

            return response

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return f"Error validating itinerary: {str(e)}"

    def request_revision(self, feedback: str) -> str:
        """Send revision feedback back to Yojana."""
        try:
            context = f"""
VALIDATION FEEDBACK - Itinerary needs revision:

{feedback}

Please send this feedback to Yojana for revision.
Include:
1. What went wrong
2. Why it's a problem
3. Specific changes needed
"""

            self.add_to_history("user", context)
            self.state_manager.add_message("user", context, agent="parikshak")

            messages = self._format_messages_for_llm()
            response = self._get_response(messages)

            self.state_manager.add_message("assistant", response, agent="parikshak")
            self.add_to_history("assistant", response)

            return response

        except Exception as e:
            logger.error(f"Revision feedback error: {str(e)}")
            return f"Error processing revision: {str(e)}"

    def get_agent_info(self) -> Dict:
        """Get agent information."""
        info = super().get_agent_info()
        info.update({
            "model": self.model,
            "available_tools": len(VALIDATION_TOOLS),
            "tools": [t for t in VALIDATION_TOOLS.keys()],
            "role": "Quality Reviewer & Validator"
        })
        return info

    def reset(self) -> None:
        """Reset agent."""
        super().reset()
        self.tools_used_count = 0

    def __repr__(self) -> str:
        return f"<ParikshakAgent model='{self.model}' role='Quality Reviewer'>"

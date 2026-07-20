"""Yojana Agent - Travel Plan Synthesizer"""

import json
import os
from typing import Optional, List, Dict, Any
import anthropic

from agents.base_agent import BaseAgent
from agents.shared_state import get_state_manager, format_budget, is_real_itinerary
from tools.planning_tools import PLANNING_TOOLS, SubmitItineraryTool, parse_and_validate_itinerary
from models.itinerary import TravelItinerary, DayPlan
from utils.logger import get_logger

logger = get_logger(__name__)


def _load_yojana_system_prompt() -> str:
    """Load the Yojana gold system prompt using a path relative to this file.

    Using a bare relative path (e.g. "YOJANA_SYSTEM_PROMPT_GOLD.md") depends
    on the process's current working directory at import time, which varies
    by launch method (streamlit run, pytest, different CWDs, etc.) and can
    silently fall back to the generic 4-line prompt instead of the intended
    ~2500-line gold prompt with no error raised.
    """
    gold_prompt_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "YOJANA_SYSTEM_PROMPT_GOLD.md"
    )
    if os.path.exists(gold_prompt_path):
        with open(gold_prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    logger.warning(
        f"YOJANA_SYSTEM_PROMPT_GOLD.md not found at {gold_prompt_path}; "
        "falling back to generic Yojana prompt."
    )
    return """You are Yojana, the Travel Plan Synthesizer.
You synthesize specialist agent recommendations into coherent, optimized travel itineraries.
You NEVER search independently. You work with outputs from Atithi, Annapurna, Yatra, Safar, Bazaar.
Create practical plans that minimize travel, maximize experience, and respect all constraints."""


class YojanaAgent(BaseAgent):
    """Travel Plan Synthesizer - creates, validates, and revises itineraries."""

    SYSTEM_PROMPT = _load_yojana_system_prompt()

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-8",
        max_history: int = 20,
    ):
        """Initialize Yojana Agent."""
        super().__init__(
            name="Yojana",
            provider="anthropic",
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            system_prompt=self.SYSTEM_PROMPT,
            max_history=max_history
        )
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.tools_used_count = 0
        self.max_tool_calls = 15
        self.state_manager = get_state_manager()
        self.current_itinerary: Optional[TravelItinerary] = None

        # Contract-validation state for the most recently created/revised
        # itinerary - populated by _synthesize_structured_itinerary(). None
        # until a real (non-refusal) draft has been through it.
        self.structured_itinerary: Optional[TravelItinerary] = None
        self.structured_validation_issues: List[str] = []
        self.structured_validation_warnings: List[str] = []

    def chat(self, user_message: str) -> str:
        """Generic chat - not used by Yojana. Use create_itinerary() or revise_itinerary() instead."""
        return "Yojana is a specialized synthesis agent. Use create_itinerary(specialist_outputs) or revise_itinerary(feedback) instead."

    def _get_response(self, messages: List[Dict]) -> str:
        """Get response from Claude with tool use."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                messages=messages,
                tools=[self._format_tool(tool) for tool in PLANNING_TOOLS.values()],
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
        elif response.stop_reason == "max_tokens":
            # Collect partial response when hitting token limit
            text_parts = []
            for block in response.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
            if text_parts:
                return "\n".join(text_parts) + "\n[Response truncated due to token limit]"
            return "Response hit token limit."
        else:
            return f"Unexpected stop reason: {response.stop_reason}"

    def _handle_tool_use(self, response: Any, messages: List[Dict]) -> str:
        """Handle tool calls in response."""
        if self.tools_used_count >= self.max_tool_calls:
            logger.warning("Max tool calls reached")
            return "Reached tool call limit. Presenting plan for review."

        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                logger.info(f"Planning tool: {tool_name}")

                tool = PLANNING_TOOLS.get(tool_name)
                if not tool:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Tool {tool_name} not found",
                    })
                    continue

                try:
                    result = tool.execute(**tool_input)
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

    def _format_trip_facts(self) -> str:
        """Build an authoritative summary of trip facts from shared state.

        Specialist recommendations are free text and may not consistently
        restate destination/dates/budget/travelers - relying on those being
        embedded correctly in prose is fragile (e.g. a specialist mentioning
        a day-trip area can get mistaken for the accommodation base). This
        gives Yojana a single, explicit, structured source of truth to
        synthesize against.
        """
        prefs = self.state_manager.get_preferences()
        facts = []
        if prefs.get("destination"):
            facts.append(f"- Destination: {prefs['destination']}")
        if prefs.get("accommodation_area"):
            facts.append(f"- Accommodation area (where they are BASED): {prefs['accommodation_area']}")
        if prefs.get("source_city"):
            facts.append(f"- Departing from: {prefs['source_city']}")
        if prefs.get("checkin_date"):
            facts.append(f"- Check-in: {prefs['checkin_date']}")
        if prefs.get("checkout_date"):
            facts.append(f"- Check-out: {prefs['checkout_date']}")
        if prefs.get("num_days"):
            facts.append(f"- Trip duration: {prefs['num_days']} days")
        if prefs.get("num_adults") or prefs.get("num_children"):
            travelers = f"{prefs.get('num_adults', 0)} adults"
            if prefs.get("num_children"):
                travelers += f", {prefs['num_children']} children"
            facts.append(f"- Travelers: {travelers}")
        if prefs.get("num_rooms"):
            facts.append(f"- Rooms needed: {prefs['num_rooms']}")
        if prefs.get("budget"):
            facts.append(f"- Total budget: {format_budget(prefs['budget'])}")
        if prefs.get("dietary_restrictions"):
            facts.append(f"- Dietary restrictions: {', '.join(prefs['dietary_restrictions'])}")
        if prefs.get("accessibility_needs"):
            facts.append(f"- Accessibility/pacing needs: {', '.join(prefs['accessibility_needs'])}")
        if prefs.get("preferred_activities"):
            facts.append(f"- Stated interests: {', '.join(prefs['preferred_activities'])}")

        if not facts:
            return "No structured trip facts captured yet - infer from specialist recommendations below."
        return "\n".join(facts)

    def create_itinerary(self, specialist_outputs: Dict) -> str:
        """Create initial itinerary from specialist recommendations."""
        try:
            self.state_manager.set_active_agent("yojana")

            context = f"""
Based on specialist recommendations, create a draft travel itinerary:

AUTHORITATIVE TRIP FACTS (from confirmed user preferences - these override anything
that conflicts in the specialist text below, e.g. if a specialist mentions a
different area, treat the accommodation area below as where the traveler is BASED):
{self._format_trip_facts()}

HOTEL RECOMMENDATIONS (Atithi):
{specialist_outputs.get('atithi', 'Not available')}

FOOD RECOMMENDATIONS (Annapurna):
{specialist_outputs.get('annapurna', 'Not available')}

ATTRACTION RECOMMENDATIONS (Yatra):
{specialist_outputs.get('yatra', 'Not available')}

TRANSPORT OPTIONS (Safar):
{specialist_outputs.get('safar', 'Not available')}

SHOPPING LOCATIONS (Bazaar):
{specialist_outputs.get('bazaar', 'Not available')}

Create a practical, optimized day-by-day itinerary that:
1. Minimizes travel and backtracking
2. Respects operating hours and check-in/check-out times
3. Includes realistic meal timings
4. Provides adequate rest
5. Stays within budget
6. Accommodates special needs

Present as DRAFT for user review.
"""

            self.add_to_history("user", context)
            messages = self._format_messages_for_llm()
            response = self._get_response(messages)

            self.state_manager.add_message("assistant", response, agent="yojana")
            self.add_to_history("assistant", response)

            self._synthesize_structured_itinerary(response)

            return response

        except Exception as e:
            logger.error(f"Create itinerary error: {str(e)}")
            return f"Error creating itinerary: {str(e)}"

    def revise_itinerary(self, user_feedback: str) -> str:
        """Revise itinerary based on user feedback."""
        try:
            context = f"User feedback for itinerary revision:\n{user_feedback}\n\nRevise the itinerary based on this feedback. Explain what changed and why."

            self.add_to_history("user", context)
            self.state_manager.add_message("user", context, agent="yojana")

            messages = self._format_messages_for_llm()
            response = self._get_response(messages)

            self.state_manager.add_message("assistant", response, agent="yojana")
            self.add_to_history("assistant", response)

            self._synthesize_structured_itinerary(response)

            return response

        except Exception as e:
            logger.error(f"Revise itinerary error: {str(e)}")
            return f"Error revising itinerary: {str(e)}"

    def _synthesize_structured_itinerary(self, draft_text: str) -> None:
        """Force a second, structured submission of the itinerary Yojana
        just drafted in prose, closing the contract-validation gap.

        Previously create_itinerary()/revise_itinerary() only ever returned
        free-form markdown - nothing checked it was internally consistent
        (valid day numbers, no overlapping activities, within budget).
        models/itinerary.py already defines a TravelItinerary schema for
        exactly this, it was just never populated. This makes a second call
        with tool_choice forced to submit_itinerary, so a structured
        submission isn't optional - then runs deterministic (not
        LLM-judgment) validation against it via parse_and_validate_itinerary.

        Skipped entirely if the draft was a refusal (insufficient specialist
        input) - there's nothing to structure yet.
        """
        self.structured_itinerary = None
        self.structured_validation_issues = []
        self.structured_validation_warnings = []

        if not is_real_itinerary(draft_text):
            return

        try:
            messages = self._format_messages_for_llm()
            messages.append({
                "role": "user",
                "content": (
                    "Now call submit_itinerary with the complete structured version of the "
                    "itinerary you just proposed above - every day, every activity, with times, "
                    "locations, and costs. This is required before the plan can be validated and "
                    "shown to the user."
                ),
            })
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                messages=messages,
                tools=[self._format_tool(SubmitItineraryTool)],
                tool_choice={"type": "tool", "name": "submit_itinerary"},
            )
            for block in response.content:
                if getattr(block, "type", None) == "tool_use" and block.name == "submit_itinerary":
                    itinerary, issues, warnings = parse_and_validate_itinerary(block.input)
                    self.structured_itinerary = itinerary
                    self.structured_validation_issues = issues
                    self.structured_validation_warnings = warnings
                    self.current_itinerary = itinerary
                    self.state_manager.add_metadata("structured_itinerary", {
                        "itinerary": itinerary,
                        "issues": issues,
                        "warnings": warnings,
                    })
                    if issues:
                        logger.warning(f"Contract validation found issues: {issues}")
                    return
            logger.warning("Yojana did not return a submit_itinerary tool call")
            self.structured_validation_issues = ["Yojana did not submit a structured itinerary to validate."]
        except Exception as e:
            logger.error(f"Structured itinerary synthesis failed: {str(e)}")
            self.structured_validation_issues = [f"Could not produce a structured, validated plan: {str(e)}"]

    def get_agent_info(self) -> Dict:
        """Get agent information."""
        info = super().get_agent_info()
        info.update({
            "model": self.model,
            "available_tools": len(PLANNING_TOOLS),
            "tools": [t.name for t in PLANNING_TOOLS.values()]
        })
        return info

    def reset(self) -> None:
        """Reset agent."""
        super().reset()
        self.tools_used_count = 0
        self.current_itinerary = None
        self.structured_itinerary = None
        self.structured_validation_issues = []
        self.structured_validation_warnings = []

    def __repr__(self) -> str:
        return f"<YojanaAgent model='{self.model}' role='Plan Synthesizer'>"

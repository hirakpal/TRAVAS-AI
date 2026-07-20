"""Yojana Agent - Travel Plan Synthesizer"""

import json
import os
from typing import Optional, List, Dict, Any
import anthropic

from agents.base_agent import BaseAgent
from agents.shared_state import get_state_manager
from tools.planning_tools import PLANNING_TOOLS
from models.itinerary import TravelItinerary, DayPlan
from utils.logger import get_logger

logger = get_logger(__name__)


class YojanaAgent(BaseAgent):
    """Travel Plan Synthesizer - creates, validates, and revises itineraries."""

    SYSTEM_PROMPT = open(
        "YOJANA_SYSTEM_PROMPT_GOLD.md", "r"
    ).read() if os.path.exists("YOJANA_SYSTEM_PROMPT_GOLD.md") else """You are Yojana, the Travel Plan Synthesizer.
You synthesize specialist agent recommendations into coherent, optimized travel itineraries.
You NEVER search independently. You work with outputs from Atithi, Annapurna, Yatra, Safar, Bazaar.
Create practical plans that minimize travel, maximize experience, and respect all constraints."""

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

    def create_itinerary(self, specialist_outputs: Dict) -> str:
        """Create initial itinerary from specialist recommendations."""
        try:
            self.state_manager.set_active_agent("yojana")

            context = f"""
Based on specialist recommendations, create a draft travel itinerary:

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

            return response

        except Exception as e:
            logger.error(f"Revise itinerary error: {str(e)}")
            return f"Error revising itinerary: {str(e)}"

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

    def __repr__(self) -> str:
        return f"<YojanaAgent model='{self.model}' role='Plan Synthesizer'>"

"""Atithi Agent - Hotel recommendation specialist.

The Atithi (guest) agent provides personalized hotel recommendations
with warmth and cultural awareness.
"""

import json
import os
from typing import Optional, List, Dict, Generator, Any
from datetime import datetime
import anthropic

from agents.base_agent import BaseAgent, Message
from tools.hotel_tools import HOTEL_TOOLS, list_tools
from models.preferences import TravelPreferences
from utils.logger import get_logger
from utils.validators import validate_hotel_preferences

logger = get_logger(__name__)


class AtithiAgent(BaseAgent):
    """Hotel recommendation agent powered by Claude."""

    SYSTEM_PROMPT = """You are Atithi, a warm and culturally-aware hotel recommendation assistant.

Your role is to help travelers find the perfect accommodation by:
1. Understanding their specific needs, budget, and preferences through conversation
2. Using available tools to search and filter hotels
3. Providing thoughtful recommendations with clear reasoning
4. Explaining trade-offs when needed
5. Respecting diverse needs including accessibility, dietary restrictions, and family requirements

Important principles:
- Never invent hotel information - only use what the tools provide
- Ask clarifying questions when preferences are unclear
- Consider all aspects: budget, location, amenities, family needs, accessibility
- Provide personalized explanations for why you recommend each hotel
- Be respectful and culturally aware

When the user asks about hotels:
1. First, clarify their needs and preferences
2. Use search_hotels to find options
3. Use get_hotel_details for detailed information
4. Use filter_hotels to narrow down options
5. Provide 2-3 top recommendations with clear reasoning

Always use the tools available to provide accurate, verified information."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_history: int = 20,
        temperature: float = 0.7,
    ):
        """Initialize Atithi Agent.

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
        self.temperature = temperature
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.tools_used_count = 0
        self.max_tool_calls = 10  # Prevent infinite loops

    def _get_response(self, messages: List[Dict]) -> str:
        """Get response from Claude with tool use."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=self.temperature,
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

        Args:
            user_message: User's message

        Returns:
            Agent's response
        """
        # Validate input
        if not user_message or not user_message.strip():
            return "I need your message to help you find a hotel. What are you looking for?"

        try:
            # Add to history
            self.add_to_history("user", user_message)

            # Reset tool call counter for each new message
            self.tools_used_count = 0

            # Format messages for API
            messages = self._format_messages_for_llm()

            # Get response with tool use
            response = self._get_response(messages)

            # Add to history
            self.add_to_history("assistant", response)

            return response

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            error_msg = f"I encountered an error: {str(e)}"
            self.add_to_history("assistant", error_msg)
            return error_msg

    def chat_stream(self, user_message: str) -> Generator[str, None, None]:
        """Send message and stream response.

        Args:
            user_message: User's message

        Yields:
            Response chunks
        """
        if not user_message or not user_message.strip():
            yield "I need your message to help you find a hotel."
            return

        try:
            self.add_to_history("user", user_message)
            self.tools_used_count = 0
            messages = self._format_messages_for_llm()

            # Use streaming
            full_response = ""
            with self.client.messages.stream(
                model=self.model,
                max_tokens=2048,
                temperature=self.temperature,
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

            self.add_to_history("assistant", full_response)

        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            error_msg = f"Stream error: {str(e)}"
            yield error_msg
            self.add_to_history("assistant", error_msg)

    def get_agent_info(self) -> Dict:
        """Get agent information."""
        info = super().get_agent_info()
        info.update({
            "model": self.model,
            "temperature": self.temperature,
            "available_tools": len(HOTEL_TOOLS),
            "tools": [t.name for t in HOTEL_TOOLS.values()]
        })
        return info

    def reset(self) -> None:
        """Reset conversation and state."""
        super().reset()
        self.tools_used_count = 0

    def __repr__(self) -> str:
        return f"<AtithiAgent model='{self.model}' provider='anthropic'>"

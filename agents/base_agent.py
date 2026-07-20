from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    """Represents a single message in conversation history"""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for all TRAVAS agents"""

    def __init__(
        self,
        name: str,
        provider: str = "openai",
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_history: int = 100
    ):
        self.name = name
        self.provider = provider
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.max_history = max_history
        self.conversation_history: List[Message] = []

    @abstractmethod
    def chat(self, user_message: str) -> str:
        pass

    @abstractmethod
    def _get_response(self, messages: List[Dict]) -> str:
        pass

    def add_to_history(self, role: str, content: str, metadata: Optional[Dict] = None):
        message = Message(role=role, content=content, metadata=metadata or {})
        self.conversation_history.append(message)
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def get_history(self) -> List[Dict]:
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            }
            for msg in self.conversation_history
        ]

    def get_history_count(self) -> int:
        return len(self.conversation_history)

    def reset(self) -> None:
        self.conversation_history.clear()

    def get_agent_info(self) -> Dict:
        return {
            "name": self.name,
            "provider": self.provider,
            "history_count": self.get_history_count(),
            "max_history": self.max_history,
            "system_prompt": bool(self.system_prompt)
        }

    def _format_messages_for_llm(self) -> List[Dict]:
        messages = []
        for msg in self.conversation_history:
            messages.append({"role": msg.role, "content": msg.content})
        return messages

    def compute_force_tool(self, min_turns: int = 4) -> bool:
        """Grounding safety-net: should THIS turn force a real tool call?

        Previously, whether a specialist ever actually called its search
        tool was entirely up to the model's discretion (tool_choice was
        always "auto") - nothing stopped it from skipping the tool and
        answering from its own general knowledge instead, dressed up as a
        verified recommendation. That's exactly what happened for
        destinations outside the mock dataset (e.g. Singapore hotels were
        invented, not retrieved).

        This doesn't try to guess from the message text whether the model
        is "about to recommend something" (an unreliable, keyword-shaped
        problem). Instead it's a deterministic circuit breaker: if a
        destination is known and this agent has gone `min_turns` messages
        into the conversation without EVER successfully calling one of its
        grounding search tools, force one now. Subclasses must set
        `self.has_ever_searched = False` in __init__ and flip it to True in
        their tool-handling code once a real grounding tool call succeeds.

        Returns False (never forces) for agents that don't opt in by
        defining `has_ever_searched` / `state_manager`.
        """
        if not hasattr(self, "has_ever_searched") or not hasattr(self, "state_manager"):
            return False
        if self.has_ever_searched:
            return False
        if self.get_history_count() < min_turns:
            return False
        try:
            prefs = self.state_manager.get_preferences()
        except Exception:
            return False
        return bool(prefs.get("destination"))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' provider='{self.provider}'>"

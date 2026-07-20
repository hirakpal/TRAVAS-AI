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

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' provider='{self.provider}'>"

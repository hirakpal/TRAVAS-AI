from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


# Tool a specialist is forced to call to self-report progress. Kept as a plain
# dict (not a Tool class) because it's only ever used for the forced status call
# in _emit_completion_status, never in a normal tool-use loop.
STATUS_REPORT_TOOL = {
    "name": "report_status",
    "description": (
        "Report your current progress for this traveler so the orchestrator knows "
        "whether your part of the plan is done. Answer honestly, based only on what "
        "has actually happened in the conversation."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["gathering", "complete"],
                "description": (
                    "'complete' ONLY if you have already delivered concrete, verified "
                    "recommendations from your search tools. 'gathering' if you are still "
                    "collecting preferences, just asked the user a question, or have not "
                    "yet presented verified results."
                ),
            },
            "confidence": {
                "type": "number",
                "description": (
                    "0.0-1.0: how well your delivered recommendations meet the traveler's "
                    "stated needs. Use 0 if you are still gathering."
                ),
            },
            "missing_information": {
                "type": "array",
                "items": {"type": "string"},
                "description": "What you still need from the user, or what you could not verify.",
            },
        },
        "required": ["status"],
    },
}


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

    def _coverage_directive(self, domain: str) -> Optional[str]:
        """Live-data availability pre-check.

        With specialists now grounded on live Google Places (any destination is
        coverable), the honesty risk is no longer "city not in our mock DB" but
        "the live source can't be reached" - most commonly a missing API key. If
        no key is configured, inject an up-front directive so the specialist says
        so plainly instead of quietly answering from general knowledge. When the
        key IS present, return None and let the actual search result (and its
        success/empty/error message) drive honesty. Returns None on any error so
        it never blocks a normal turn.
        """
        try:
            from data import live_places
            if live_places.is_configured():
                return None
            return (
                f"\n\n[LIVE DATA UNAVAILABLE - no Google Places API key is configured, so you "
                f"cannot fetch verified {domain} data right now. Tell the traveler plainly that "
                f"you can't pull verified {domain} results at the moment; do NOT answer from "
                f"general knowledge as if it were verified.]"
            )
        except Exception as e:
            logger.debug(f"_coverage_directive({domain}) error: {str(e)}")
            return None

    def _emit_completion_status(self, agent_key: str) -> None:
        """After a turn, have the specialist self-report a structured completion
        signal into shared state ({status, confidence, missing_information}).

        Why the agent reports it (vs. surrounding code inferring it): the signal
        is real data the agent produces, so it can't drift from what the agent
        actually did the way a hand-set boolean would. 'complete' is additionally
        gated on the deterministic grounding flag (has_ever_searched) - a
        specialist cannot self-declare done unless it actually retrieved verified
        data, which reuses the same anti-fabrication guard as tool-enforcement.

        Failure-safe: on ANY error (or if this agent isn't a tool-using
        specialist) it falls back to a derived status - complete iff it has ever
        grounded - so a flaky status call never breaks the turn or silently
        blocks synthesis. Only meaningful for specialists that set
        `has_ever_searched`/`state_manager`/`client`/`model`.
        """
        state_manager = getattr(self, "state_manager", None)
        if state_manager is None:
            return
        grounded = bool(getattr(self, "has_ever_searched", False))
        try:
            messages = self._format_messages_for_llm()
            messages.append({
                "role": "user",
                "content": (
                    "INTERNAL STATUS CHECK (not shown to the traveler): call report_status "
                    "describing your progress for THIS traveler, based only on the "
                    "conversation above."
                ),
            })
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                system="You report your own progress honestly for an internal orchestrator.",
                messages=messages,
                tools=[STATUS_REPORT_TOOL],
                tool_choice={"type": "tool", "name": "report_status"},
            )
            status, confidence, missing = "gathering", None, []
            for block in response.content:
                if getattr(block, "type", None) == "tool_use" and block.name == "report_status":
                    data = block.input or {}
                    status = data.get("status", "gathering")
                    confidence = data.get("confidence")
                    missing = data.get("missing_information") or []
                    break
            # Deterministic guard: cannot be 'complete' without having grounded in
            # real data, whatever the model self-reports.
            if not grounded:
                status = "gathering"
            state_manager.update_agent_status(
                agent_key, status=status, confidence=confidence,
                missing_information=missing, grounded=grounded,
            )
        except Exception as e:
            logger.debug(f"_emit_completion_status fallback for {agent_key}: {str(e)}")
            state_manager.update_agent_status(
                agent_key,
                status="complete" if grounded else "gathering",
                confidence=None,
                missing_information=[],
                grounded=grounded,
            )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' provider='{self.provider}'>"

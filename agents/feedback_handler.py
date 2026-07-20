"""Feedback Handler - Manages user approval, revision, and rejection flow"""

import json
import re
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from agents.shared_state import get_state_manager
from utils.logger import get_logger

logger = get_logger(__name__)


def _contains_keyword(text: str, keywords: list) -> bool:
    """Check if text contains any keyword as a whole word/phrase (not a substring).

    Prevents false positives like "yes" matching inside "yesterday", or
    "no" matching inside "know".
    """
    for kw in keywords:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text):
            return True
    return False


def _sanitize_for_logging(text: str) -> str:
    """Remove special Unicode chars for Windows console logging"""
    if not isinstance(text, str):
        return str(text)
    # Replace common special chars that cause Windows encoding issues
    replacements = {
        '₹': 'INR',
        '✅': 'OK',
        '❌': 'FAIL',
        '⚠️': 'WARN',
        '→': '->',
        '✓': 'YES',
        '✗': 'NO'
    }
    result = text
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)
    return result


@dataclass
class ItineraryApprovalState:
    """Track approval state of itinerary"""
    current_itinerary: Optional[Dict] = None
    validation_status: str = "PENDING"  # PENDING/APPROVED/REVISION/CONDITIONAL
    revision_count: int = 0
    max_revisions: int = 3
    user_feedback_history: list = field(default_factory=list)
    approval_status: str = "PENDING"  # PENDING/APPROVED/REJECTED/RESTART
    feedback_rounds: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def can_revise(self) -> bool:
        """Check if more revisions are allowed"""
        return self.revision_count < self.max_revisions

    def add_feedback(self, feedback: str, intent: str):
        """Add user feedback to history"""
        self.user_feedback_history.append({
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "feedback": feedback
        })
        self.feedback_rounds += 1

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "validation_status": self.validation_status,
            "revision_count": self.revision_count,
            "max_revisions": self.max_revisions,
            "user_feedback_count": len(self.user_feedback_history),
            "approval_status": self.approval_status,
            "feedback_rounds": self.feedback_rounds,
            "can_revise": self.can_revise()
        }


class FeedbackHandler:
    """Handles user feedback: approval, revisions, rejections"""

    # Intent classification keywords
    APPROVE_KEYWORDS = [
        "approve", "yes", "looks good", "perfect", "confirm", "lock",
        "great", "excellent", "love", "proceed", "go ahead", "finaliz"
    ]

    REVISE_KEYWORDS = [
        "change", "add", "remove", "modify", "can you", "please",
        "different", "instead", "also", "more", "less", "swap",
        "replace", "update", "adjust", "tweak"
    ]

    REJECT_KEYWORDS = [
        "no", "reject", "redo", "start over", "doesn't work", "not good",
        "bad", "wrong", "nope", "nah", "never", "refuse", "decline",
        "scrap", "restart", "begin again"
    ]

    CLARIFY_KEYWORDS = [
        "why", "how", "explain", "tell me", "what", "when", "where",
        "curious", "understand", "question", "confused", "not clear"
    ]

    def __init__(self):
        """Initialize feedback handler"""
        self.state_manager = get_state_manager()
        self.approval_state = ItineraryApprovalState()

    def classify_intent(self, user_message: str) -> str:
        """Classify user feedback intent"""
        message_lower = user_message.lower()
        logger.info(f"Classifying intent for: {_sanitize_for_logging(user_message[:80])}")

        # Check APPROVE first (strongest signal)
        if _contains_keyword(message_lower, self.APPROVE_KEYWORDS):
            return "APPROVE"

        # Check REJECT (strong signal)
        if _contains_keyword(message_lower, self.REJECT_KEYWORDS):
            return "REJECT"

        # Check REVISE
        if _contains_keyword(message_lower, self.REVISE_KEYWORDS):
            return "REVISE"

        # Check CLARIFY
        if _contains_keyword(message_lower, self.CLARIFY_KEYWORDS):
            return "CLARIFY"

        # Default to REVISE if contains specific changes
        if _contains_keyword(message_lower, ["day", "meal", "activity", "restaurant", "hotel"]):
            return "REVISE"

        return "CLARIFY"

    def extract_revision_details(self, user_message: str) -> str:
        """Extract specific revision requests from user message"""
        # For now, just return the message - Yojana will parse details
        return user_message

    def process_user_feedback(
        self,
        user_message: str,
        current_itinerary: Optional[Dict] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Process user feedback and determine next action

        Returns:
            (action, details) where action is APPROVE/REVISE/REJECT/CLARIFY
        """
        intent = self.classify_intent(user_message)
        self.approval_state.add_feedback(user_message, intent)

        logger.info(f"User intent classified: {intent}")

        if intent == "APPROVE":
            return self._handle_approval(current_itinerary)

        elif intent == "REVISE":
            return self._handle_revision(user_message, current_itinerary)

        elif intent == "REJECT":
            return self._handle_rejection(user_message)

        else:  # CLARIFY
            return self._handle_clarification(user_message)

    def _handle_approval(self, itinerary: Optional[Dict]) -> Tuple[str, Dict]:
        """Handle user approval"""
        logger.info("User approved itinerary")

        self.approval_state.approval_status = "APPROVED"

        return "APPROVE", {
            "status": "success",
            "message": "Itinerary approved and finalized!",
            "next_step": "FINALIZE",
            "itinerary": itinerary,
            "approval_state": self.approval_state.to_dict()
        }

    def _handle_revision(self, feedback: str, itinerary: Optional[Dict]) -> Tuple[str, Dict]:
        """Handle revision request"""
        logger.info(f"User requested revision: {_sanitize_for_logging(feedback[:100])}...")

        if not self.approval_state.can_revise():
            return "REJECT", {
                "status": "error",
                "message": f"Max revisions ({self.approval_state.max_revisions}) reached. Please provide clearer guidance or contact support.",
                "next_step": "ESCALATE",
                "approval_state": self.approval_state.to_dict()
            }

        self.approval_state.revision_count += 1
        revision_details = self.extract_revision_details(feedback)

        return "REVISE", {
            "status": "success",
            "message": f"Processing revision request (Attempt {self.approval_state.revision_count}/{self.approval_state.max_revisions})",
            "next_step": "SEND_TO_YOJANA",
            "feedback": revision_details,
            "revision_number": self.approval_state.revision_count,
            "approval_state": self.approval_state.to_dict()
        }

    def _handle_rejection(self, feedback: str) -> Tuple[str, Dict]:
        """Handle rejection"""
        logger.info(f"User rejected itinerary: {_sanitize_for_logging(feedback[:100])}...")

        # Ask if they want to start completely fresh or make minor changes
        return "REJECT", {
            "status": "clarify",
            "message": "I understand. Would you like to:\n1. Start completely fresh with new preferences?\n2. Make some specific changes and try again?",
            "next_step": "ASK_RESTART_STRATEGY",
            "original_rejection": feedback,
            "approval_state": self.approval_state.to_dict()
        }

    def _handle_clarification(self, message: str) -> Tuple[str, Dict]:
        """Handle clarification request"""
        logger.info(f"User asked for clarification: {_sanitize_for_logging(message[:100])}...")

        return "CLARIFY", {
            "status": "info",
            "message": "I can help clarify! What would you like to know about the itinerary?",
            "next_step": "ANSWER_QUESTION",
            "question": message,
            "approval_state": self.approval_state.to_dict()
        }

    def handle_restart_decision(self, decision: str) -> Tuple[str, Dict]:
        """Handle user's decision after rejection"""
        decision_lower = decision.lower()

        if any(word in decision_lower for word in ["fresh", "new", "start over", "1"]):
            logger.info("User chose to start fresh")
            self.approval_state.approval_status = "RESTART"
            return "RESTART_FRESH", {
                "status": "success",
                "message": "Starting fresh! Let me gather new preferences for your trip.",
                "next_step": "RESTART_SANCHALAK",
                "approval_state": self.approval_state.to_dict()
            }

        elif any(word in decision_lower for word in ["specific", "changes", "2", "minor"]):
            logger.info("User chose to make specific changes")
            return "MAKE_CHANGES", {
                "status": "success",
                "message": "Sure! What specific changes would you like to make? Be as detailed as possible.",
                "next_step": "COLLECT_SPECIFIC_FEEDBACK",
                "approval_state": self.approval_state.to_dict()
            }

        else:
            return "CLARIFY", {
                "status": "clarify",
                "message": "Please choose:\n1. Start fresh with new preferences\n2. Make specific changes",
                "next_step": "ASK_RESTART_STRATEGY",
                "approval_state": self.approval_state.to_dict()
            }

    def handle_specific_changes(self, changes: str) -> Tuple[str, Dict]:
        """Handle specific changes after rejection"""
        logger.info(f"Processing specific changes: {_sanitize_for_logging(changes[:100])}...")

        if not self.approval_state.can_revise():
            return "ESCALATE", {
                "status": "error",
                "message": f"Max revision attempts reached. Consider starting fresh.",
                "next_step": "ESCALATE",
                "approval_state": self.approval_state.to_dict()
            }

        self.approval_state.revision_count += 1

        return "REVISE", {
            "status": "success",
            "message": f"Revising itinerary with your changes (Attempt {self.approval_state.revision_count}/{self.approval_state.max_revisions})",
            "next_step": "SEND_TO_YOJANA",
            "feedback": changes,
            "revision_number": self.approval_state.revision_count,
            "approval_state": self.approval_state.to_dict()
        }

    def update_itinerary_and_validation(
        self,
        itinerary: Dict,
        validation_status: str
    ):
        """Update approval state with new itinerary and validation result"""
        self.approval_state.current_itinerary = itinerary
        self.approval_state.validation_status = validation_status
        logger.info(f"Updated approval state: {validation_status}")

    def get_approval_state(self) -> Dict:
        """Get current approval state"""
        return self.approval_state.to_dict()

    def reset(self):
        """Reset feedback handler"""
        self.approval_state = ItineraryApprovalState()
        logger.info("Feedback handler reset")

    def finalize_itinerary(self, itinerary: Dict) -> Dict:
        """Finalize approved itinerary"""
        final_itinerary = {
            **itinerary,
            "approval_status": "APPROVED",
            "approval_timestamp": datetime.now().isoformat(),
            "approval_metadata": {
                "revision_count": self.approval_state.revision_count,
                "feedback_rounds": self.approval_state.feedback_rounds,
                "user_feedback_summary": [
                    fb.get("feedback", "")[:50] + "..."
                    for fb in self.approval_state.user_feedback_history
                ]
            }
        }

        logger.info(f"Itinerary finalized after {self.approval_state.revision_count} revisions")
        return final_itinerary

    def __repr__(self) -> str:
        return f"<FeedbackHandler revisions={self.approval_state.revision_count}/{self.approval_state.max_revisions} status={self.approval_state.approval_status}>"

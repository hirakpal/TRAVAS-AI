"""
Regression tests for TRAVAS-AI's deterministic state-machine logic.

SCOPE: agents/shared_state.py and agents/feedback_handler.py. Both modules
are pure Python with no Streamlit and no Anthropic API dependency, so they
can be imported and exercised directly - no network calls, no cost, fully
deterministic. This is where the approve/reject/revise state transitions,
the preference-merge logic, and the word-boundary keyword matching (the
source of several previously-found bugs: "yesterday" matching "yes",
"know" matching "no", "business" matching "bus") actually live.

NOT covered here (requires a live Streamlit script-run context and/or the
Anthropic API - verified separately via manual code trace and/or a live
click-through):
- streamlit_app.py's button handlers (Approve/Reject/Revise/New Trip) and
  st.session_state wiring, and the itinerary-panel rendering
- _confirm_finalize_intent, _identify_routing_intents,
  _extract_and_update_preferences (all make real LLM calls)
- Yojana/Parikshak/specialist agents' actual generated content

Run with:  pytest tests/test_state_logic.py -v
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pytest

from agents.shared_state import (
    StateManager,
    format_budget,
    build_context_summary,
    enrich_message_with_context,
)
from agents.feedback_handler import FeedbackHandler, _contains_keyword


# ============================================================================
# format_budget
# ============================================================================

@pytest.mark.parametrize("value,expected", [
    (None, "Not specified"),
    (150000, "₹150,000"),
    (150000.0, "₹150,000"),
    ("150000", "₹150,000"),
    ("20000 INR", "₹20000 INR"),   # non-numeric string: falls back, never crashes
    (0, "₹0"),
    (-5000, "₹-5,000"),
    (1500000, "₹1,500,000"),
    (99.6, "₹100"),               # rounds to nearest whole rupee
])
def test_format_budget(value, expected):
    assert format_budget(value) == expected


# ============================================================================
# build_context_summary / enrich_message_with_context
# ============================================================================

def _prefs(**overrides):
    base = dict(
        destination=None, source_city=None, accommodation_area=None,
        checkin_date=None, checkout_date=None, num_adults=None,
        num_children=None, num_rooms=None, budget=None,
        dietary_restrictions=None, accessibility_needs=None,
        preferred_activities=None, num_days=None,
    )
    base.update(overrides)
    return base


def test_empty_context_summary_is_empty_string():
    assert build_context_summary(_prefs()) == ""


def test_context_summary_includes_all_known_fields():
    prefs = _prefs(
        destination="Singapore", source_city="Bangalore",
        num_days=5, num_adults=2, budget=150000,
        dietary_restrictions=["vegetarian"], preferred_activities=["sightseeing"],
    )
    summary = build_context_summary(prefs)
    assert "Singapore" in summary
    assert "Bangalore" in summary
    assert "5 days" in summary
    assert "2 adults" in summary
    assert "₹150,000" in summary
    assert "vegetarian" in summary
    assert "sightseeing" in summary


def test_context_summary_omits_unset_fields():
    prefs = _prefs(destination="Goa")
    summary = build_context_summary(prefs)
    assert "Goa" in summary
    assert "Rooms needed" not in summary
    assert "Budget" not in summary


def test_enrich_message_no_context_returns_unchanged():
    msg = "hello"
    assert enrich_message_with_context(msg, _prefs()) == msg


def test_enrich_message_with_context_wraps_message():
    prefs = _prefs(destination="Goa")
    result = enrich_message_with_context("find me a hotel", prefs)
    assert "CONTEXT FROM EARLIER CONVERSATION" in result
    assert "USER REQUEST" in result
    assert "find me a hotel" in result
    assert "Goa" in result


# ============================================================================
# StateManager.update_preferences - merge vs overwrite semantics
# ============================================================================

def _new_manager():
    return StateManager("test-session")


def test_scalar_fields_overwrite():
    sm = _new_manager()
    sm.update_preferences({"destination": "Goa"})
    sm.update_preferences({"destination": "Singapore"})
    assert sm.get_preferences()["destination"] == "Singapore"


def test_list_fields_merge_with_dedup():
    sm = _new_manager()
    sm.update_preferences({"dietary_restrictions": ["vegetarian"]})
    sm.update_preferences({"dietary_restrictions": ["gluten-free"]})
    assert sm.get_preferences()["dietary_restrictions"] == ["vegetarian", "gluten-free"]
    # re-mentioning an existing one doesn't duplicate it
    sm.update_preferences({"dietary_restrictions": ["vegetarian"]})
    assert sm.get_preferences()["dietary_restrictions"] == ["vegetarian", "gluten-free"]


@pytest.mark.parametrize("field", ["dietary_restrictions", "accessibility_needs", "preferred_activities"])
def test_all_list_fields_merge(field):
    sm = _new_manager()
    sm.update_preferences({field: ["a"]})
    sm.update_preferences({field: ["b"]})
    assert sm.get_preferences()[field] == ["a", "b"]


def test_unknown_keys_are_dropped_not_raised():
    sm = _new_manager()
    # "days" isn't a real schema field (num_days is) - must not raise
    sm.update_preferences({"days": 5, "destination": "Goa"})
    assert sm.get_preferences()["destination"] == "Goa"
    assert "days" not in sm.get_preferences()


def test_reset_clears_preferences():
    sm = _new_manager()
    sm.update_preferences({"destination": "Goa"})
    sm.reset()
    assert sm.get_preferences()["destination"] is None


def test_agent_response_tracking():
    sm = _new_manager()
    sm.update_agent_response("atithi", "Hotel options here")
    sm.update_agent_response("sanchalak", "Chat reply here")
    responses = sm.get_state()["agent_responses"]
    assert set(responses.keys()) == {"atithi", "sanchalak"}
    # Regression check for the fix to streamlit_app._can_generate_itinerary:
    # "sanchalak" must never be mistaken for a real specialist.
    SPECIALIST_KEYS = {"atithi", "annapurna", "yatra", "safar", "bazaar"}
    assert len(SPECIALIST_KEYS & set(responses.keys())) == 1


# ============================================================================
# feedback_handler._contains_keyword - word-boundary false-positive regressions
# ============================================================================

@pytest.mark.parametrize("text,keywords,expected", [
    ("yesterday was fun", ["yes"], False),
    ("yes, approve it", ["yes"], True),
    ("i don't know", ["no"], False),
    ("no, reject this", ["no"], True),
    ("this is a great trip", ["eat"], False),
    ("let's eat dinner", ["eat"], True),
    ("business class flight", ["bus"], False),
    ("take the bus", ["bus"], True),
    ("a smaller room please", ["mall"], False),
    ("visit the mall", ["mall"], True),
    ("nobody is here", ["no"], False),
    ("not a chance", ["no"], False),
])
def test_contains_keyword_word_boundaries(text, keywords, expected):
    assert _contains_keyword(text, keywords) == expected


# ============================================================================
# FeedbackHandler.classify_intent
# ============================================================================

@pytest.mark.parametrize("message,expected_intent", [
    ("I approve this itinerary", "APPROVE"),
    ("looks good, lock it in", "APPROVE"),
    ("perfect, let's go ahead", "APPROVE"),
    ("great, finalize it", "APPROVE"),
    ("no, I don't like this", "REJECT"),
    ("this doesn't work for me", "REJECT"),
    ("let's start over", "REJECT"),
    ("nope, scrap it", "REJECT"),
    ("can you add a beach day", "REVISE"),
    ("please remove the museum visit", "REVISE"),
    ("swap the hotel for something cheaper", "REVISE"),
    ("change the restaurant on day 2", "REVISE"),
    ("why is day 3 so packed", "CLARIFY"),
    ("what does this activity cost", "CLARIFY"),
    ("how does the pacing work", "CLARIFY"),
    ("I'm thinking about the hotel", "REVISE"),   # fallback keyword path
    ("just checking in", "CLARIFY"),              # true default fallback
])
def test_classify_intent(message, expected_intent):
    fh = FeedbackHandler()
    assert fh.classify_intent(message) == expected_intent


def test_classify_intent_approve_takes_priority_over_reject():
    fh = FeedbackHandler()
    # Contains both an APPROVE keyword ("yes") and a REJECT keyword ("bad") -
    # APPROVE is checked first and should win.
    assert fh.classify_intent("yes but this hotel looks bad") == "APPROVE"


def test_classify_intent_reject_takes_priority_over_revise():
    fh = FeedbackHandler()
    # Contains both a REJECT keyword ("no") and REVISE keywords ("please",
    # "change") - REJECT is checked first and should win.
    assert fh.classify_intent("no, please change it") == "REJECT"


# ============================================================================
# FeedbackHandler.process_user_feedback - full state transitions
# ============================================================================

def test_process_feedback_approve_sets_approved_status():
    fh = FeedbackHandler()
    action, details = fh.process_user_feedback("I approve this itinerary.", {"destination": "Goa"})
    assert action == "APPROVE"
    assert details["approval_state"]["approval_status"] == "APPROVED"


def test_process_feedback_revise_increments_count():
    fh = FeedbackHandler()
    for i in range(1, 4):
        action, details = fh.process_user_feedback(f"please add more beach days ({i})", {})
        assert action == "REVISE"
        assert details["revision_number"] == i
        assert details["approval_state"]["revision_count"] == i


def test_process_feedback_revise_blocked_after_max():
    fh = FeedbackHandler()
    for i in range(3):
        fh.process_user_feedback(f"change something ({i})", {})
    # 4th revision request should be rejected/escalated, not silently allowed
    action, details = fh.process_user_feedback("change something else", {})
    assert action == "REJECT"
    assert "Max revisions" in details["message"]


def test_process_feedback_reject_asks_for_restart_strategy():
    fh = FeedbackHandler()
    action, details = fh.process_user_feedback("no, this doesn't work", {})
    assert action == "REJECT"
    assert "start" in details["message"].lower()


def test_process_feedback_clarify_default():
    fh = FeedbackHandler()
    action, details = fh.process_user_feedback("why did you pick this hotel", {})
    assert action == "CLARIFY"


def test_handle_restart_decision_fresh():
    fh = FeedbackHandler()
    action, details = fh.handle_restart_decision("start fresh please")
    assert action == "RESTART_FRESH"
    assert fh.approval_state.approval_status == "RESTART"


def test_handle_restart_decision_specific_changes():
    fh = FeedbackHandler()
    action, details = fh.handle_restart_decision("make specific changes")
    assert action == "MAKE_CHANGES"


def test_handle_restart_decision_unclear_reprompts():
    fh = FeedbackHandler()
    action, details = fh.handle_restart_decision("umm not sure")
    assert action == "CLARIFY"


def test_can_revise_respects_max():
    fh = FeedbackHandler()
    assert fh.approval_state.can_revise() is True
    fh.approval_state.revision_count = 3
    assert fh.approval_state.can_revise() is False


def test_reset_clears_feedback_handler_state():
    fh = FeedbackHandler()
    fh.process_user_feedback("change the hotel", {})
    assert fh.approval_state.revision_count == 1
    fh.reset()
    assert fh.approval_state.revision_count == 0
    assert fh.approval_state.approval_status == "PENDING"


def test_finalize_itinerary_stamps_approval_metadata():
    fh = FeedbackHandler()
    fh.process_user_feedback("change the hotel", {})  # 1 revision on record
    final = fh.finalize_itinerary({"destination": "Goa"})
    assert final["approval_status"] == "APPROVED"
    assert final["approval_metadata"]["revision_count"] == 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))

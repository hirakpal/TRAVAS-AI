"""
TRAVAS-AI Streamlit Frontend
Complete travel assistant with multi-agent orchestration
"""

import streamlit as st
import os
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import agents
from agents.sanchalak_agent import SanchalakAgent
from agents.yojana_agent import YojanaAgent
from agents.parikshak_agent import ParikshakAgent
from agents.shared_state import (
    initialize_state_manager, get_state_manager, reset_state_manager,
    format_budget, is_real_itinerary,
)
from agents.feedback_handler import FeedbackHandler
from utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# ITINERARY SYNTHESIS HELPERS
# ============================================================================

# Phrases that should trigger Yojana synthesis from free-text chat. Matched as
# whole words/phrases (not substrings) so e.g. "finalise" (British spelling)
# is caught but arbitrary text isn't accidentally matched.
FINALIZE_TRIGGER_KEYWORDS = [
    "yes", "ok", "okay", "approve", "approved", "confirm", "confirmed",
    "perfect", "sounds good", "looks good", "go ahead", "lock it in",
    "book it", "finalize", "finalise", "finalized", "finalised",
    "generate itinerary", "create itinerary", "make the itinerary",
]


def _message_triggers_synthesis(text: str) -> bool:
    """Whole-word/phrase check for finalize-intent keywords in free text."""
    text_lower = text.lower()
    for kw in FINALIZE_TRIGGER_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            return True
    return False


SPECIALIST_KEYS = {"atithi", "annapurna", "yatra", "safar", "bazaar"}


def _can_generate_itinerary() -> bool:
    """Check whether shared state has enough context to synthesize.

    Requires at least 2 GENUINE specialist responses (not just Sanchalak's
    own text - agent_responses also stores a "sanchalak" entry for every
    turn, which meant the old `len(agent_responses) > 0` check was true
    after the very first message regardless of whether any real specialist
    had ever been consulted). Requiring 2 also reduces near-empty synthesis
    attempts like the one Yojana correctly refused (1 specialist had only
    asked clarifying questions, 0 others had responded).
    """
    state = get_state_manager().get_state()
    real_specialist_responses = SPECIALIST_KEYS & set(state["agent_responses"].keys())
    return bool(state["travel_preferences"].get("destination")) and len(real_specialist_responses) >= 2


def _run_validation(itinerary_text: str, prefs: dict, deterministic_findings: dict = None) -> str:
    """Run Parikshak's quality checks on a draft itinerary.

    Parikshak is the quality gate between Yojana's draft and the user (per
    its own system prompt) - it was previously instantiated but never
    actually invoked anywhere in the app. deterministic_findings (from
    Yojana's contract-validation pass) is passed through so Parikshak treats
    real overlap/budget checks as confirmed facts instead of re-deriving
    them from prose.
    """
    try:
        return st.session_state.parikshak.validate_itinerary(
            itinerary_text, dict(prefs), deterministic_findings=deterministic_findings
        )
    except Exception as e:
        logger.error(f"Parikshak validation error: {str(e)}")
        return "⚠️ Validation could not be completed automatically. Please review the itinerary manually before approving."


def generate_itinerary() -> bool:
    """Generate the itinerary via Yojana, then validate it via Parikshak,
    storing both results in session state. Returns True only if Yojana
    produced a genuine draft - False both when there isn't enough context
    to even try, AND when Yojana tried but correctly refused to fabricate
    (caller should not claim success, and the session should still be able
    to retry generation later once real specialist data exists).
    """
    if not _can_generate_itinerary():
        return False

    state = get_state_manager().get_state()
    specialist_outputs = {
        "atithi": str(state["agent_responses"].get("atithi", "No hotel recommendations yet")),
        "annapurna": str(state["agent_responses"].get("annapurna", "No food recommendations yet")),
        "yatra": str(state["agent_responses"].get("yatra", "No attraction recommendations yet")),
        "safar": str(state["agent_responses"].get("safar", "No transport recommendations yet")),
        "bazaar": str(state["agent_responses"].get("bazaar", "No shopping recommendations yet")),
    }

    itinerary_text = st.session_state.yojana.create_itinerary(specialist_outputs)
    st.session_state.itinerary_text = itinerary_text
    is_real = is_real_itinerary(itinerary_text)
    st.session_state.itinerary_ready = is_real

    # Yojana's create_itinerary() also runs a forced structured-submission +
    # deterministic validation pass (contract validation) when the draft is
    # real - pick up its results here so the UI and Parikshak can use them.
    st.session_state.structured_validation_issues = list(st.session_state.yojana.structured_validation_issues)
    st.session_state.structured_validation_warnings = list(st.session_state.yojana.structured_validation_warnings)

    prefs = state["travel_preferences"]
    st.session_state.itinerary = {
        "destination": prefs.get("destination", "TBD"),
        "duration": f"{prefs.get('num_days', 'N/A')} days",
        "travelers": f"{prefs.get('num_adults', 0)} adults, {prefs.get('num_children', 0)} children",
        "budget": format_budget(prefs.get("budget")),
        "summary": itinerary_text
    }

    if is_real:
        deterministic_findings = {
            "issues": st.session_state.structured_validation_issues,
            "warnings": st.session_state.structured_validation_warnings,
        }
        st.session_state.validation_result = _run_validation(itinerary_text, prefs, deterministic_findings)
        st.session_state.approval_state = 'CONDITIONAL'
    else:
        # Don't run Parikshak on a refusal (there's nothing to validate) and
        # don't claim the trip is ready for approval.
        st.session_state.validation_result = None
        st.session_state.approval_state = 'PENDING'

    return is_real


def _confirm_finalize_intent(user_input: str, agent) -> bool:
    """Context-aware check: does this message really mean 'generate/finalize
    the complete itinerary now'?

    The cheap keyword pre-filter (_message_triggers_synthesis) matches bare
    words like "yes" and "ok" - necessary to catch phrasings like "finalise
    the itinery", but those same words are also how a user agrees to a
    completely different question ("shall I bring in Safar and Atithi?" ->
    "yes both"). Mirrors the fix already applied to specialist routing:
    an LLM call with recent conversation context disambiguates what the
    affirmative is actually responding to, instead of guessing from the
    word alone. Only called after the keyword pre-filter matches, to avoid
    an extra LLM call on every single message.
    """
    try:
        recent = agent.conversation_history[-6:]
        recent_text = "\n".join(
            f"{t['role']}: {str(t['content'])[:300]}" for t in recent
        )
        prompt = f"""Recent conversation:
{recent_text}

Latest user message: "{user_input}"

Does this message mean the user wants their COMPLETE trip itinerary generated/finalized right now - as opposed to just agreeing to a narrower sub-question (like consulting a specific specialist, answering a preference question, or confirming one detail)?

Reply with exactly one word: YES or NO."""
        response = agent.client.messages.create(
            model=agent.model,
            max_tokens=5,
            messages=[{"role": "user", "content": prompt}]
        )
        text = "".join(
            b.text for b in response.content if hasattr(b, "text")
        ).strip().upper()
        return text.startswith("YES")
    except Exception as e:
        logger.debug(f"finalize-intent classification error: {str(e)}")
        return False

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="TRAVAS-AI - Travel Assistant",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# STYLING
# ============================================================================

st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .stButton > button {
        width: 100%;
        padding: 0.75rem;
        font-weight: bold;
    }
    .header-title {
        color: #667eea;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .status-badge {
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.5rem 0.5rem 0 0;
    }
    .status-pending {
        background-color: #fff3cd;
        color: #856404;
    }
    .status-approved {
        background-color: #d4edda;
        color: #155724;
    }
    .status-rejected {
        background-color: #f8d7da;
        color: #721c24;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.agent = None
    st.session_state.yojana = None
    st.session_state.parikshak = None
    st.session_state.feedback_handler = None
    st.session_state.messages = []
    st.session_state.itinerary = None
    st.session_state.itinerary_text = None
    st.session_state.itinerary_ready = False
    st.session_state.validation_result = None
    st.session_state.structured_validation_issues = []
    st.session_state.structured_validation_warnings = []
    st.session_state.approval_state = 'PENDING'
    st.session_state.revision_count = 0
    st.session_state.show_revise_input = False
    st.session_state.show_reject_options = False

def initialize_session():
    """Initialize agent and session"""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            st.error("❌ ANTHROPIC_API_KEY not set. Please set it in your environment.")
            return False

        st.session_state.agent = SanchalakAgent(api_key=api_key)
        st.session_state.yojana = YojanaAgent(api_key=api_key)
        st.session_state.parikshak = ParikshakAgent(api_key=api_key)
        st.session_state.feedback_handler = FeedbackHandler()
        st.session_state.initialized = True

        # Add welcome message
        st.session_state.messages.append({
            "role": "system",
            "content": "Welcome to TRAVAS-AI! Tell me about your dream trip."
        })

        return True
    except Exception as e:
        st.error(f"❌ Failed to initialize: {str(e)}")
        logger.error(f"Initialization error: {str(e)}")
        return False

# ============================================================================
# MAIN UI
# ============================================================================

def _reset_trip_session():
    """Reset all trip-related session state for a brand new trip.

    Shared by both the "New Trip" header button and the "Start Fresh" option
    offered after a Reject, so the two paths can't drift out of sync.
    """
    st.session_state.messages = []
    st.session_state.itinerary = None
    st.session_state.itinerary_text = None
    st.session_state.itinerary_ready = False
    st.session_state.validation_result = None
    st.session_state.structured_validation_issues = []
    st.session_state.structured_validation_warnings = []
    st.session_state.approval_state = 'PENDING'
    st.session_state.revision_count = 0
    st.session_state.show_revise_input = False
    st.session_state.show_reject_options = False
    st.session_state.agent = None
    st.session_state.yojana = None
    st.session_state.parikshak = None
    st.session_state.feedback_handler = None
    st.session_state.initialized = False
    reset_state_manager()


# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="header-title">🌍 TRAVAS-AI</div>', unsafe_allow_html=True)
    st.caption("AI-powered travel planning with multi-agent orchestration")

with col2:
    if st.button("🔄 New Trip", key="new_trip_btn"):
        _reset_trip_session()
        st.rerun()

# Initialize on first load
if not st.session_state.initialized:
    with st.spinner("🚀 Initializing travel assistant..."):
        if not initialize_session():
            st.stop()

# ============================================================================
# SIDEBAR - STATUS & ACTIONS
# ============================================================================

with st.sidebar:
    st.header("📊 Session Status")

    # Status info
    col1, col2 = st.columns(2)
    with col1:
        # Handle both string and dict approval_state
        approval_val = st.session_state.approval_state
        if isinstance(approval_val, dict):
            approval_val = approval_val.get('approval_status', 'PENDING')
        st.metric("Approval State", approval_val)
    with col2:
        st.metric("Revisions Used", f"{st.session_state.revision_count}/3")

    st.divider()

    # Action buttons
    st.subheader("✅ Actions")

    can_act = len(st.session_state.messages) > 1

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✓ Approve", disabled=not can_act, key="approve_btn", use_container_width=True):
            # If no itinerary has been genuinely generated yet - either
            # nothing was attempted, or the only attempt so far was Yojana
            # correctly refusing to fabricate one - generate one now rather
            # than declaring "approved and finalized" for something that was
            # never actually built.
            if not st.session_state.get('itinerary_ready'):
                with st.spinner("🗺️ Generating itinerary before approval..."):
                    generated = generate_itinerary()
                if not generated:
                    st.session_state.messages.append({
                        "role": "system",
                        "content": "⚠️ I don't have enough trip details yet to build an itinerary "
                                    "(need at least a destination and one specialist's recommendations). "
                                    "Please share more details in chat first, then approve."
                    })
                    st.rerun()

            action, details = st.session_state.feedback_handler.process_user_feedback(
                "I approve this itinerary.",
                st.session_state.itinerary
            )
            # feedback_handler._handle_approval() returns a top-level
            # "approval_state" key that is itself a dict (ItineraryApprovalState
            # .to_dict(), e.g. {"approval_status": "APPROVED", ...}) - there is
            # no top-level "approval_status" key. The old code below fell
            # through .get('approval_status', ...) -> .get('approval_state',
            # 'APPROVED') and stored *that whole dict* into
            # st.session_state.approval_state on every single Approve click.
            # That's the actual root cause of the original
            # "TypeError: dict is not an accepted type" crash - the earlier
            # isinstance() guards on the display side only hid the symptom.
            # process_user_feedback("I approve...") always classifies as
            # APPROVE and always succeeds, so this is simply "APPROVED".
            st.session_state.approval_state = 'APPROVED'
            st.session_state.messages.append({
                "role": "system",
                "content": "✅ Itinerary approved and finalized! Ready for booking."
            })
            st.rerun()

    with col2:
        if st.button("✗ Reject", disabled=not can_act, key="reject_btn", use_container_width=True):
            # Actually run this through the feedback handler (previously this
            # button only printed text - approval_state never changed and
            # the two follow-up options weren't wired to anything, so typing
            # "1" or "2" afterward just went to Sanchalak as an ordinary chat
            # message with no memory of the rejection).
            action, details = st.session_state.feedback_handler.process_user_feedback(
                "I reject this itinerary.",
                st.session_state.itinerary
            )
            st.session_state.approval_state = 'REJECTED'
            st.session_state.show_reject_options = True
            st.session_state.show_revise_input = False
            st.session_state.messages.append({
                "role": "system",
                "content": details.get(
                    "message",
                    "Would you like to:\n1. Start fresh with new preferences?\n2. Make specific changes?"
                ) if isinstance(details, dict) else
                    "Would you like to:\n1. Start fresh with new preferences?\n2. Make specific changes?"
            })
            st.rerun()

    # Real follow-up actions after a Reject, replacing the old dead-end text
    # prompt that asked the user to pick "1" or "2" with no button behind
    # either option.
    if st.session_state.get('show_reject_options'):
        st.caption("What would you like to do?")
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            if st.button("🔄 Start Fresh", key="reject_start_fresh_btn", use_container_width=True):
                _reset_trip_session()
                st.rerun()
        with rcol2:
            if st.button("✏️ Make Changes", key="reject_make_changes_btn", use_container_width=True):
                st.session_state.show_reject_options = False
                st.session_state.show_revise_input = True
                # Restore a sensible approval_state so the revise flow below
                # (and the itinerary panel) doesn't stay stuck on REJECTED.
                st.session_state.approval_state = 'CONDITIONAL' if st.session_state.get('itinerary_ready') else 'PENDING'
                st.rerun()

    if st.session_state.revision_count < 3:
        if st.button("✏️ Revise", disabled=not can_act, key="revise_btn", use_container_width=True):
            st.session_state.show_revise_input = True
            st.rerun()
    else:
        st.warning("Max revisions (3) reached. Start a new trip.")

    st.divider()

    # Revision input
    if st.session_state.show_revise_input if 'show_revise_input' in st.session_state else False:
        st.subheader("What would you like to change?")
        revision_feedback = st.text_area(
            "Your feedback:",
            placeholder="e.g., Add more beach days, skip the temple, increase budget...",
            key="revision_input"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit Revision", use_container_width=True):
                if not revision_feedback or not revision_feedback.strip():
                    # Don't use st.stop() here - it would halt the whole script
                    # mid-render and blank out the chat/itinerary panel below,
                    # which are defined later in the script. Just skip the
                    # submit logic and let the page finish rendering normally.
                    st.warning("Please describe what you'd like changed before submitting.")
                else:
                    # Revise was previously callable even when no itinerary had
                    # ever been generated yet (nothing gated it on itinerary_ready,
                    # unlike Approve) - that would ask Yojana to "revise" a draft
                    # that never existed. Generate one first if needed, same
                    # pattern as the Approve button.
                    ready = True
                    if not st.session_state.get('itinerary_ready'):
                        with st.spinner("🗺️ Generating an itinerary to revise..."):
                            generated = generate_itinerary()
                        if not generated:
                            ready = False
                            st.session_state.show_revise_input = False
                            st.session_state.messages.append({
                                "role": "system",
                                "content": "⚠️ I don't have an itinerary to revise yet "
                                            "(need at least a destination and two specialists' "
                                            "recommendations). Please share more details in chat first."
                            })
                            st.rerun()

                    if ready:
                        action, details = st.session_state.feedback_handler.process_user_feedback(
                            revision_feedback,
                            st.session_state.itinerary
                        )
                        st.session_state.revision_count += 1
                        st.session_state.show_revise_input = False
                        st.session_state.messages.append({
                            "role": "user",
                            "content": f"Revision {st.session_state.revision_count}: {revision_feedback}"
                        })

                        # Actually call Yojana to revise and Parikshak to re-validate -
                        # this previously just printed a canned success message
                        # without doing either, leaving the itinerary unchanged.
                        with st.spinner(f"🔄 Yojana is revising (attempt {st.session_state.revision_count}/3)..."):
                            try:
                                revised_text = st.session_state.yojana.revise_itinerary(revision_feedback)
                                st.session_state.itinerary_text = revised_text
                                if st.session_state.itinerary:
                                    st.session_state.itinerary["summary"] = revised_text
                                # revise_itinerary() also re-runs the forced
                                # structured-submission + deterministic
                                # validation pass - pick up its fresh results.
                                st.session_state.structured_validation_issues = list(
                                    st.session_state.yojana.structured_validation_issues
                                )
                                st.session_state.structured_validation_warnings = list(
                                    st.session_state.yojana.structured_validation_warnings
                                )
                            except Exception as e:
                                logger.error(f"Revision error: {str(e)}")
                                st.session_state.messages.append({
                                    "role": "system",
                                    "content": f"❌ Revision failed: {str(e)}"
                                })
                                st.rerun()

                        with st.spinner("🔍 Parikshak is re-validating..."):
                            prefs = get_state_manager().get_preferences()
                            deterministic_findings = {
                                "issues": st.session_state.structured_validation_issues,
                                "warnings": st.session_state.structured_validation_warnings,
                            }
                            st.session_state.validation_result = _run_validation(
                                st.session_state.itinerary_text, prefs, deterministic_findings
                            )

                        st.session_state.approval_state = 'CONDITIONAL'
                        st.session_state.messages.append({
                            "role": "system",
                            "content": f"✅ Revision {st.session_state.revision_count}/3 complete — "
                                        f"updated itinerary and quality check are ready on the right →"
                        })
                        st.rerun()

        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_revise_input = False
                st.rerun()

# ============================================================================
# MAIN CONTENT
# ============================================================================

# Create two columns
col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("💬 Chat")

    # Display messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            elif message["role"] == "system":
                st.chat_message("system").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])

    # Chat input
    user_input = st.chat_input("Tell me about your dream trip...")

    if user_input:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        # Get response from agent
        with st.spinner("🤖 Thinking..."):
            try:
                response = st.session_state.agent.chat(user_input)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })

                # Trigger itinerary synthesis when user confirms trip details.
                # Gated on itinerary_ready (not raw itinerary_text) so a prior
                # refusal from Yojana never permanently blocks a later, real
                # synthesis attempt - the Revise flow handles updates once a
                # real itinerary exists.
                if (not st.session_state.get('itinerary_ready')
                        and _message_triggers_synthesis(user_input)
                        and _confirm_finalize_intent(user_input, st.session_state.agent)):
                    with st.spinner("🗺️ Yojana is synthesizing your itinerary..."):
                        if generate_itinerary():
                            st.session_state.messages.append({
                                "role": "system",
                                "content": f"🗺️ Itinerary created by Yojana!\n\n{st.session_state.itinerary_text[:500]}... (see full itinerary on the right →)"
                            })
                        elif st.session_state.itinerary_text:
                            # Yojana explained why it can't build a draft yet -
                            # show that explanation instead of silently doing
                            # nothing (previous behavior just logged it).
                            st.session_state.messages.append({
                                "role": "system",
                                "content": f"⚠️ {st.session_state.itinerary_text[:500]}"
                            })
                        else:
                            logger.info("Synthesis triggered but not enough context yet; skipping.")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.error(f"Chat error: {str(e)}")

        st.rerun()

with col2:
    st.subheader("📋 Travel Itinerary")

    if st.session_state.itinerary:
        # Itinerary header
        itinerary = st.session_state.itinerary
        st.info(f"""
        **📍 {itinerary.get('destination', 'TBD')}**

        Duration: {itinerary.get('duration', 'TBD')}
        Travelers: {itinerary.get('travelers', 'TBD')}
        Budget: {itinerary.get('budget', 'TBD')}
        """)

        # Show full itinerary text if available
        if st.session_state.itinerary_text:
            with st.expander("📅 Full Itinerary", expanded=True):
                st.markdown(st.session_state.itinerary_text)
        # Fallback to day-by-day if structured data available
        elif itinerary.get('days'):
            for day_info in itinerary.get('days', []):
                with st.expander(f"📅 Day {day_info.get('day', '?')}"):
                    for activity in day_info.get('activities', []):
                        st.write(f"→ {activity}")

        # Contract validation - deterministic checks (overlap times, budget,
        # valid day numbers, valid activity types) run against Yojana's
        # structured submit_itinerary output, NOT an LLM judgment call. Shown
        # separately from Parikshak below since these are confirmed facts,
        # not opinions.
        det_issues = st.session_state.get('structured_validation_issues') or []
        det_warnings = st.session_state.get('structured_validation_warnings') or []
        if det_issues or det_warnings:
            if det_issues:
                st.error(f"❌ Contract validation: {len(det_issues)} confirmed issue(s) in the structured plan")
            else:
                st.warning(f"⚠️ Contract validation: {len(det_warnings)} warning(s)")
            with st.expander("🧩 Contract Validation Details (deterministic)", expanded=bool(det_issues)):
                for i in det_issues:
                    st.markdown(f"- ❌ {i}")
                for w in det_warnings:
                    st.markdown(f"- ⚠️ {w}")

        # Parikshak quality check - previously validated by a specialist agent
        # that was instantiated but never actually invoked anywhere in the app.
        if st.session_state.validation_result:
            result_text = st.session_state.validation_result
            if "REVISION REQUIRED" in result_text:
                st.error("❌ Parikshak found issues — revision recommended before booking")
            elif "CONDITIONAL" in result_text:
                st.warning("⚠️ Parikshak approved with warnings")
            elif "APPROVED" in result_text:
                st.success("✅ Passed Parikshak's quality checks")
            with st.expander("🔍 Quality Check Details (Parikshak)", expanded=False):
                st.markdown(result_text)

        # Approval status
        st.divider()
        approval_val = st.session_state.approval_state
        if isinstance(approval_val, dict):
            approval_val = approval_val.get('approval_status', 'PENDING')

        if approval_val == 'PENDING':
            st.warning("⏳ Awaiting your approval")
        elif approval_val == 'CONDITIONAL':
            st.info("⚠️ Ready for approval - review and approve or revise")
        elif approval_val == 'APPROVED':
            st.success("✅ Approved and finalized!")
        else:
            st.info(f"Status: {approval_val}")
    else:
        st.info("💭 Share your travel details and confirm (with 'yes' or 'ok') to generate an itinerary...")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.caption("""
🌍 TRAVAS-AI v1.0 | Multi-agent travel assistant powered by Claude
[Docs](https://github.com) | [Source](https://github.com)
""")

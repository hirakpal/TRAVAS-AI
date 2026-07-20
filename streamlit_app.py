"""
TRAVAS-AI Streamlit Frontend

Thin VIEW layer over SanchalakAgent, which IS the orchestrator. All trip-planning
workflow - routing, the itinerary-generation gate, Yojana/Parikshak triggering,
contract validation, and the approve/revise/reject state machine - lives on
SanchalakAgent (agents/sanchalak_agent.py), which has no UI dependency. This file
only:
  - forwards user actions to Sanchalak
  - renders whatever sanchalak.get_view_state() returns
  - owns pure view toggles (is the revision box open, are reject options showing)

That separation means the same backend can be driven by FastAPI, WhatsApp, a
mobile app, etc. without re-implementing any of the planning logic.
"""

import os
import streamlit as st
from dotenv import load_dotenv

from agents.sanchalak_agent import SanchalakAgent
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="TRAVAS-AI - Travel Assistant",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# STYLING
# ============================================================================

st.markdown("""
    <style>
    .main { padding: 0rem 1rem; }
    .stChatMessage { padding: 1rem; border-radius: 0.5rem; }
    .stButton > button { width: 100%; padding: 0.75rem; font-weight: bold; }
    .header-title { color: #667eea; font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# SESSION STATE (view-only) + ORCHESTRATOR LIFECYCLE
# ============================================================================

if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.sanchalak = None
    # Pure view toggles - not workflow state.
    st.session_state.show_revise_input = False
    st.session_state.show_reject_options = False


def initialize_session() -> bool:
    """Create Sanchalak (the orchestrator, which builds the agent team). Returns success."""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            st.error("❌ ANTHROPIC_API_KEY not set. Please set it in your environment.")
            return False
        st.session_state.sanchalak = SanchalakAgent(api_key=api_key)
        st.session_state.initialized = True
        return True
    except Exception as e:
        st.error(f"❌ Failed to initialize: {str(e)}")
        logger.error(f"Initialization error: {str(e)}")
        return False


def reset_trip() -> None:
    """Reset the whole trip (New Trip button / Start Fresh after reject)."""
    if st.session_state.sanchalak is not None:
        st.session_state.sanchalak.reset()
    st.session_state.show_revise_input = False
    st.session_state.show_reject_options = False


# ============================================================================
# HEADER
# ============================================================================

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="header-title">🌍 TRAVAS-AI</div>', unsafe_allow_html=True)
    st.caption("AI-powered travel planning with multi-agent orchestration")
with col2:
    if st.button("🔄 New Trip", key="new_trip_btn"):
        reset_trip()
        st.rerun()

# Initialize on first load
if not st.session_state.initialized:
    with st.spinner("🚀 Initializing travel assistant..."):
        if not initialize_session():
            st.stop()

sanchalak = st.session_state.sanchalak
view = sanchalak.get_view_state()

# ============================================================================
# SIDEBAR - STATUS & ACTIONS
# ============================================================================

with st.sidebar:
    st.header("📊 Session Status")

    scol1, scol2 = st.columns(2)
    with scol1:
        st.metric("Approval State", view["approval_state"])
    with scol2:
        st.metric("Revisions Used", f"{view['revision_count']}/{view['max_revisions']}")

    st.divider()
    st.subheader("✅ Actions")

    can_act = view["can_act"]

    acol1, acol2 = st.columns(2)
    with acol1:
        if st.button("✓ Approve", disabled=not can_act, key="approve_btn", use_container_width=True):
            with st.spinner("🗺️ Finalizing..."):
                sanchalak.approve()
            st.rerun()
    with acol2:
        if st.button("✗ Reject", disabled=not can_act, key="reject_btn", use_container_width=True):
            sanchalak.reject()
            st.session_state.show_reject_options = True
            st.session_state.show_revise_input = False
            st.rerun()

    # Post-reject fork
    if st.session_state.show_reject_options:
        st.caption("What would you like to do?")
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            if st.button("🔄 Start Fresh", key="reject_start_fresh_btn", use_container_width=True):
                reset_trip()
                st.rerun()
        with rcol2:
            if st.button("✏️ Make Changes", key="reject_make_changes_btn", use_container_width=True):
                st.session_state.show_reject_options = False
                st.session_state.show_revise_input = True
                sanchalak.resume_after_reject_make_changes()
                st.rerun()

    if view["can_revise"]:
        if st.button("✏️ Revise", disabled=not can_act, key="revise_btn", use_container_width=True):
            st.session_state.show_revise_input = True
            st.rerun()
    else:
        st.warning(f"Max revisions ({view['max_revisions']}) reached. Start a new trip.")

    st.divider()

    # Revision input
    if st.session_state.show_revise_input:
        st.subheader("What would you like to change?")
        revision_feedback = st.text_area(
            "Your feedback:",
            placeholder="e.g., Add more beach days, skip the temple, increase budget...",
            key="revision_input",
        )
        vcol1, vcol2 = st.columns(2)
        with vcol1:
            if st.button("Submit Revision", use_container_width=True):
                with st.spinner("🔄 Yojana is revising & Parikshak is re-validating..."):
                    result = sanchalak.submit_revision(revision_feedback)
                if result["status"] == "empty_feedback":
                    st.warning("Please describe what you'd like changed before submitting.")
                else:
                    st.session_state.show_revise_input = False
                    st.rerun()
        with vcol2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_revise_input = False
                st.rerun()

# ============================================================================
# MAIN CONTENT
# ============================================================================

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("💬 Chat")

    with st.container():
        for message in view["messages"]:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            elif message["role"] == "system":
                st.chat_message("system").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])

    user_input = st.chat_input("Tell me about your dream trip...")
    if user_input:
        with st.spinner("🤖 Thinking..."):
            try:
                sanchalak.send_message(user_input)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.error(f"Chat error: {str(e)}")
        st.rerun()

with col2:
    st.subheader("📋 Travel Itinerary")

    itinerary = view["itinerary"]
    if itinerary:
        st.info(f"""
        **📍 {itinerary.get('destination', 'TBD')}**

        Duration: {itinerary.get('duration', 'TBD')}
        Travelers: {itinerary.get('travelers', 'TBD')}
        Budget: {itinerary.get('budget', 'TBD')}
        """)

        if view["itinerary_text"]:
            with st.expander("📅 Full Itinerary", expanded=True):
                st.markdown(view["itinerary_text"])

        # Contract validation - deterministic checks (time overlaps, budget,
        # valid day numbers/activity types) against Yojana's structured
        # submit_itinerary output, NOT an LLM judgment call.
        det_issues = view["structured_validation_issues"] or []
        det_warnings = view["structured_validation_warnings"] or []
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

        # Parikshak quality check (LLM judgment, fed the deterministic findings)
        if view["validation_result"]:
            result_text = view["validation_result"]
            if "REVISION REQUIRED" in result_text:
                st.error("❌ Parikshak found issues — revision recommended before booking")
            elif "CONDITIONAL" in result_text:
                st.warning("⚠️ Parikshak approved with warnings")
            elif "APPROVED" in result_text:
                st.success("✅ Passed Parikshak's quality checks")
            with st.expander("🔍 Quality Check Details (Parikshak)", expanded=False):
                st.markdown(result_text)

        st.divider()
        approval_val = view["approval_state"]
        if approval_val == "PENDING":
            st.warning("⏳ Awaiting your approval")
        elif approval_val == "CONDITIONAL":
            st.info("⚠️ Ready for approval - review and approve or revise")
        elif approval_val == "APPROVED":
            st.success("✅ Approved and finalized!")
        elif approval_val == "REJECTED":
            st.error("✗ Rejected - choose Start Fresh or Make Changes")
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

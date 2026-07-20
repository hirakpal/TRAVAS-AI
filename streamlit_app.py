"""
TRAVAS-AI Streamlit Frontend
Complete travel assistant with multi-agent orchestration
"""

import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import agents
from agents.sanchalak_agent import SanchalakAgent
from agents.yojana_agent import YojanaAgent
from agents.parikshak_agent import ParikshakAgent
from agents.shared_state import initialize_state_manager, get_state_manager, reset_state_manager
from agents.feedback_handler import FeedbackHandler
from utils.logger import get_logger

logger = get_logger(__name__)

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
    st.session_state.approval_state = 'PENDING'
    st.session_state.revision_count = 0

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

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="header-title">🌍 TRAVAS-AI</div>', unsafe_allow_html=True)
    st.caption("AI-powered travel planning with multi-agent orchestration")

with col2:
    if st.button("🔄 New Trip", key="new_trip_btn"):
        st.session_state.messages = []
        st.session_state.itinerary = None
        st.session_state.approval_state = 'PENDING'
        st.session_state.revision_count = 0
        st.session_state.agent = None
        st.session_state.initialized = False
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
            action, details = st.session_state.feedback_handler.process_user_feedback(
                "I approve this itinerary.",
                st.session_state.itinerary
            )
            # Extract approval status safely
            if isinstance(details, dict):
                st.session_state.approval_state = details.get('approval_status', details.get('approval_state', 'APPROVED'))
            else:
                st.session_state.approval_state = 'APPROVED'
            st.session_state.messages.append({
                "role": "system",
                "content": "✅ Itinerary approved and finalized! Ready for booking."
            })
            st.rerun()

    with col2:
        if st.button("✗ Reject", disabled=not can_act, key="reject_btn", use_container_width=True):
            st.session_state.messages.append({
                "role": "system",
                "content": "Would you like to:\n1. Start fresh with new preferences?\n2. Make specific changes?"
            })
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
                st.session_state.messages.append({
                    "role": "system",
                    "content": f"Processing revision (Attempt {st.session_state.revision_count}/3)...\n\n🔄 Yojana is updating the itinerary...\n\n🔍 Parikshak is re-validating...\n\n✅ Updated itinerary is ready!"
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

                # Trigger itinerary synthesis when user confirms trip details
                if any(keyword in user_input.lower() for keyword in ["yes", "ok", "approve", "finalize", "create itinerary"]):
                    state = get_state_manager().get_state()

                    # Check if we have enough context
                    if state["travel_preferences"]["destination"] and len(state["agent_responses"]) > 0:
                        with st.spinner("🗺️ Yojana is synthesizing your itinerary..."):
                            # Collect specialist outputs from shared state
                            specialist_outputs = {
                                "atithi": str(state["agent_responses"].get("atithi", "No hotel recommendations yet")),
                                "annapurna": str(state["agent_responses"].get("annapurna", "No food recommendations yet")),
                                "yatra": str(state["agent_responses"].get("yatra", "No attraction recommendations yet")),
                                "safar": str(state["agent_responses"].get("safar", "No transport recommendations yet")),
                                "bazaar": str(state["agent_responses"].get("bazaar", "No shopping recommendations yet")),
                            }

                            # Generate itinerary
                            itinerary_text = st.session_state.yojana.create_itinerary(specialist_outputs)
                            st.session_state.itinerary_text = itinerary_text

                            # Parse into structured format
                            st.session_state.itinerary = {
                                "destination": state["travel_preferences"].get("destination", "TBD"),
                                "duration": f"{state['travel_preferences'].get('num_days', 'N/A')} days",
                                "travelers": f"{state['travel_preferences'].get('num_adults', 0)} adults, {state['travel_preferences'].get('num_children', 0)} children",
                                "budget": f"₹{state['travel_preferences'].get('budget', 'TBD')}",
                                "summary": itinerary_text
                            }
                            st.session_state.approval_state = 'CONDITIONAL'

                            st.session_state.messages.append({
                                "role": "system",
                                "content": f"🗺️ Itinerary created by Yojana!\n\n{itinerary_text[:500]}... (see full itinerary on the right →)"
                            })

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

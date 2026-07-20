"""
TRAVAS-AI Python Backend FastAPI Server
Provides endpoints for the Node.js API Gateway to call
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import agents
from agents.sanchalak_agent import SanchalakAgent
from agents.shared_state import initialize_state_manager, get_state_manager, reset_state_manager
from agents.feedback_handler import FeedbackHandler
from utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# FASTAPI SETUP
# ============================================================================

app = FastAPI(
    title="TRAVAS-AI Backend",
    description="Python backend for TRAVAS-AI travel assistant",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    session_id: str
    feedback: str
    action: str  # approve, revise, reject, clarify

class SessionRequest(BaseModel):
    session_id: Optional[str] = None

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

# Track sessions and agents
sessions = {}
feedback_handlers = {}

def get_or_create_session(session_id: Optional[str] = None):
    """Get or create a session"""
    if session_id and session_id in sessions:
        return session_id

    # Create new session
    new_session_id = f"session-{int(__import__('time').time()*1000)}"
    sessions[new_session_id] = {
        "agent": SanchalakAgent(api_key=os.getenv("ANTHROPIC_API_KEY")),
        "feedback_handler": FeedbackHandler(),
        "created_at": __import__('datetime').datetime.now().isoformat()
    }
    return new_session_id

# ============================================================================
# ROUTES
# ============================================================================

@app.get("/")
async def root():
    """Welcome endpoint"""
    return {
        "service": "TRAVAS-AI Python Backend",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat": "Send user message",
            "POST /feedback": "Send user feedback",
            "GET /health": "Health check"
        }
    }

@app.get("/api/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "service": "TRAVAS-AI Python Backend",
        "version": "1.0.0",
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "active_sessions": len(sessions)
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Send user message to Sanchalak agent"""
    try:
        # Get or create session
        session_id = get_or_create_session(request.session_id)
        session = sessions[session_id]
        agent = session["agent"]

        # Get response from Sanchalak
        logger.info(f"Processing chat: {request.message[:100]}")

        # Call agent's chat method
        response = agent.chat(request.message)

        logger.info(f"Response generated for session {session_id}")

        return {
            "status": "success",
            "session_id": session_id,
            "message": request.message,
            "response": response,
            "approval_state": "PENDING",
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def feedback(request: FeedbackRequest):
    """Send user feedback to FeedbackHandler"""
    try:
        # Get session
        if request.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        session = sessions[request.session_id]
        feedback_handler = session["feedback_handler"]

        logger.info(f"Processing feedback: {request.action}")

        # Process feedback
        action, details = feedback_handler.process_user_feedback(
            request.feedback,
            None  # itinerary not needed for this simple version
        )

        return {
            "status": details.get("status", "success"),
            "session_id": request.session_id,
            "action": action,
            "message": details.get("message"),
            "next_step": details.get("next_step"),
            "revision_count": feedback_handler.approval_state.revision_count,
            "approval_state": feedback_handler.approval_state.approval_state,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Feedback error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def status(session_id: str):
    """Get session status"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        session = sessions[session_id]
        feedback_handler = session["feedback_handler"]

        return {
            "status": "success",
            "session_id": session_id,
            "approval_state": feedback_handler.approval_state.approval_state,
            "revision_count": feedback_handler.approval_state.revision_count,
            "max_revisions": feedback_handler.approval_state.max_revisions,
            "message_count": feedback_handler.approval_state.feedback_rounds,
            "can_revise": feedback_handler.approval_state.can_revise(),
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/itinerary")
async def itinerary(session_id: str):
    """Get current itinerary (mock data for demo)"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        # Return mock itinerary for demo
        mock_itinerary = {
            "destination": "Goa",
            "duration": "5 days",
            "travelers": "Family with kids",
            "budget": "₹45,000",
            "days": [
                {
                    "day": 1,
                    "activities": [
                        "Flight Delhi-Goa",
                        "Hotel check-in",
                        "Evening beach walk"
                    ]
                },
                {
                    "day": 2,
                    "activities": [
                        "Baga Beach (water sports)",
                        "Dolphin Tour",
                        "Dinner at restaurant"
                    ]
                },
                {
                    "day": 3,
                    "activities": [
                        "Full-day: Dudhsagar Waterfall",
                        "Swimming and photography"
                    ]
                },
                {
                    "day": 4,
                    "activities": [
                        "Rest day",
                        "Anjuna Spice Market",
                        "Fort Aguada sunset"
                    ]
                },
                {
                    "day": 5,
                    "activities": [
                        "Last beach time",
                        "Hotel checkout",
                        "Flight Goa-Delhi"
                    ]
                }
            ]
        }

        return {
            "status": "success",
            "session_id": session_id,
            "itinerary": mock_itinerary,
            "approval_state": "PENDING",
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Itinerary error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def history(session_id: str):
    """Get conversation history"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        session = sessions[session_id]
        agent = session["agent"]

        # Get history from agent
        messages = agent.get_history()

        return {
            "status": "success",
            "session_id": session_id,
            "messages": messages,
            "total_messages": len(messages),
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"History error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/restart")
async def restart(request: SessionRequest):
    """Start new session"""
    try:
        # Delete old session if provided
        if request.session_id and request.session_id in sessions:
            del sessions[request.session_id]
            logger.info(f"Deleted session: {request.session_id}")

        # Create new session
        new_session_id = get_or_create_session()

        return {
            "status": "success",
            "new_session_id": new_session_id,
            "message": "New session started. Ready for trip preferences.",
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Restart error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("""
╔════════════════════════════════════════════════════════════╗
║     TRAVAS-AI Python Backend FastAPI Server Started        ║
║                                                            ║
║  Backend: http://localhost:5000                           ║
║  Docs: http://localhost:5000/docs                         ║
║  Health: http://localhost:5000/api/health                 ║
║                                                            ║
║  Connected to Node.js API Gateway on port 3000            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host="0.0.0.0", port=5000)

# TRAVAS-AI API Gateway Documentation

## Overview

The Node.js API Gateway bridges the frontend and Python backend agents, handling session management, routing, and response streaming.

```
Frontend (Web/Mobile)
        ↓ HTTP/REST
    API Gateway (Node.js)
        ↓ subprocess/FastAPI
    Python Backend (Agents)
        ↓
    Claude API
```

---

## Setup

### Installation

```bash
cd api/
npm install
```

### Start Server

```bash
# Development
npm run dev

# Production
npm start
```

Server runs on `http://localhost:3000`

---

## Endpoints

### 1. POST `/api/chat` — Send Message

Send user message and get response from orchestrator.

**Request:**
```json
{
  "message": "I want a 5-day family trip to Goa",
  "session_id": "session-abc123" // Optional: creates new if omitted
}
```

**Response:**
```json
{
  "status": "success",
  "session_id": "session-abc123",
  "message": "I want a 5-day family trip to Goa",
  "response": "[Sanchalak Response] Processing: \"I want a 5-day family trip to Goa\"",
  "approval_state": "PENDING",
  "timestamp": "2026-07-20T10:30:00Z"
}
```

**Example (cURL):**
```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "5-day trip to Goa with family",
    "session_id": "session-123"
  }'
```

**Example (JavaScript/Fetch):**
```javascript
const response = await fetch('http://localhost:3000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: '5-day trip to Goa with family'
  })
});

const data = await response.json();
console.log('Session ID:', data.session_id);
console.log('Response:', data.response);
```

---

### 2. POST `/api/feedback` — User Feedback

Send user feedback (approve/revise/reject/clarify).

**Request:**
```json
{
  "session_id": "session-abc123",
  "feedback": "Can you add more beach time?",
  "action": "revise" // approve | revise | reject | clarify
}
```

**Response:**
```json
{
  "status": "success",
  "session_id": "session-abc123",
  "action": "revise",
  "message": "Processing revision (Attempt 1/3)",
  "next_step": "SEND_TO_YOJANA",
  "approval_state": "PENDING",
  "revision_count": 1,
  "timestamp": "2026-07-20T10:35:00Z"
}
```

**Actions:**
- `"approve"` — Lock itinerary
- `"revise"` — Request changes (max 3 times)
- `"reject"` — Reject and ask restart strategy
- `"clarify"` — Ask clarification questions

**Example (Approve):**
```bash
curl -X POST http://localhost:3000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-123",
    "feedback": "Perfect! I approve.",
    "action": "approve"
  }'
```

**Example (Revise):**
```bash
curl -X POST http://localhost:3000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-123",
    "feedback": "Can you add more beach days?",
    "action": "revise"
  }'
```

---

### 3. GET `/api/status` — Session Status

Get current session status and approval state.

**Request:**
```
GET /api/status?session_id=session-abc123
```

**Response:**
```json
{
  "status": "success",
  "session_id": "session-abc123",
  "approval_state": "PENDING",
  "revision_count": 1,
  "max_revisions": 3,
  "message_count": 5,
  "can_revise": true,
  "created_at": "2026-07-20T10:30:00Z",
  "timestamp": "2026-07-20T10:35:00Z"
}
```

**Example:**
```bash
curl "http://localhost:3000/api/status?session_id=session-123"
```

---

### 4. GET `/api/itinerary` — Get Itinerary

Retrieve current itinerary for the session.

**Request:**
```
GET /api/itinerary?session_id=session-abc123
```

**Response:**
```json
{
  "status": "success",
  "session_id": "session-abc123",
  "itinerary": {
    "destination": "Goa",
    "duration": "5 days",
    "days": [...],
    "total_budget": "₹45,000",
    "approval_status": "PENDING"
  },
  "approval_state": "PENDING",
  "revision_count": 1,
  "timestamp": "2026-07-20T10:35:00Z"
}
```

**Example:**
```bash
curl "http://localhost:3000/api/itinerary?session_id=session-123"
```

---

### 5. GET `/api/history` — Conversation History

Get all messages in conversation.

**Request:**
```
GET /api/history?session_id=session-abc123
```

**Response:**
```json
{
  "status": "success",
  "session_id": "session-abc123",
  "messages": [
    {
      "role": "user",
      "content": "5-day trip to Goa",
      "timestamp": "2026-07-20T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "[Sanchalak Response]...",
      "timestamp": "2026-07-20T10:30:05Z"
    }
  ],
  "total_messages": 2,
  "timestamp": "2026-07-20T10:35:00Z"
}
```

**Example:**
```bash
curl "http://localhost:3000/api/history?session_id=session-123"
```

---

### 6. POST `/api/restart` — Start New Session

Clear current session and create new one.

**Request:**
```json
{
  "session_id": "session-abc123" // Optional: clear this session
}
```

**Response:**
```json
{
  "status": "success",
  "new_session_id": "session-xyz789",
  "message": "New session started. Ready for trip preferences.",
  "timestamp": "2026-07-20T10:40:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:3000/api/restart \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session-123"}'
```

---

### 7. GET `/api/health` — Health Check

Check if server is running.

**Request:**
```
GET /api/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "TRAVAS-AI API Gateway",
  "version": "1.0.0",
  "active_sessions": 5,
  "timestamp": "2026-07-20T10:35:00Z"
}
```

**Example:**
```bash
curl "http://localhost:3000/api/health"
```

---

### 8. GET `/` — Welcome

API welcome and endpoint listing.

**Request:**
```
GET /
```

**Response:**
```json
{
  "service": "TRAVAS-AI API Gateway",
  "version": "1.0.0",
  "endpoints": {
    "POST /api/chat": "Send user message",
    "POST /api/feedback": "Send approval/revision/rejection",
    "GET /api/status": "Get session status",
    "GET /api/itinerary": "Get current itinerary",
    "GET /api/history": "Get conversation history",
    "POST /api/restart": "Start new session",
    "GET /api/health": "Health check"
  }
}
```

---

## Session Management

### Session Lifecycle

```
1. Create Session
   POST /api/chat (without session_id)
   → Returns new session_id
   
2. Active Session
   Use session_id in all requests
   Status: PENDING (awaiting completion)
   
3. Providing Feedback
   POST /api/feedback
   → Update approval_state
   
4. Approval
   Approval state: APPROVED
   → Itinerary locked, ready for booking
   
5. Restart
   POST /api/restart
   → Delete session, create new one
```

### Session State

```javascript
{
  id: "session-123",
  created_at: "2026-07-20T10:30:00Z",
  messages: [],              // Conversation history
  itinerary: null,           // Current itinerary
  approval_state: "PENDING", // PENDING | APPROVED | REJECTED
  revision_count: 0,         // Number of revisions used
  max_revisions: 3           // Maximum allowed revisions
}
```

---

## Usage Examples

### Complete Flow Example

```javascript
// 1. Start conversation
const chatRes = await fetch('http://localhost:3000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: '5-day family trip to Goa with 2 kids'
  })
});
const { session_id } = await chatRes.json();

// 2. Check status
const statusRes = await fetch(`http://localhost:3000/api/status?session_id=${session_id}`);
const status = await statusRes.json();
console.log('Approval state:', status.approval_state); // PENDING

// 3. Get itinerary (after specialists finish)
const itinRes = await fetch(`http://localhost:3000/api/itinerary?session_id=${session_id}`);
const { itinerary } = await itinRes.json();
console.log('Itinerary:', itinerary);

// 4. User revises
const feedbackRes = await fetch('http://localhost:3000/api/feedback', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id,
    feedback: 'Can you add more beach days?',
    action: 'revise'
  })
});
const feedbackData = await feedbackRes.json();
console.log('Revision #:', feedbackData.revision_count);

// 5. User approves
const approveRes = await fetch('http://localhost:3000/api/feedback', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id,
    feedback: 'Perfect! I approve.',
    action: 'approve'
  })
});
const approved = await approveRes.json();
console.log('Status:', approved.approval_state); // APPROVED

// 6. Get conversation history
const historyRes = await fetch(`http://localhost:3000/api/history?session_id=${session_id}`);
const { messages } = await historyRes.json();
console.log('Total messages:', messages.length);
```

---

## Error Handling

### Common Errors

**400 - Bad Request**
```json
{
  "status": "error",
  "message": "Message is required"
}
```
- Missing required fields
- Invalid action type

**404 - Not Found**
```json
{
  "status": "error",
  "message": "Session not found"
}
```
- Invalid session_id
- Session expired

**500 - Server Error**
```json
{
  "status": "error",
  "message": "Internal server error"
}
```
- Python backend crash
- Timeout

---

## Rate Limiting

(To be implemented)

- 100 requests/minute per session
- 5 revisions per itinerary
- 24-hour session expiry

---

## WebSocket Support

(For future implementation)

```javascript
const ws = new WebSocket('ws://localhost:3000/api/stream');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Stream update:', message);
};
```

---

## Testing

### Using Postman

1. Import the endpoints
2. Create collection with these requests
3. Test each endpoint with sample data

### Using Node.js Test Client

```bash
node test-client.js
```

---

## Deployment

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY api/package*.json ./
RUN npm install
COPY api/server.js ./
EXPOSE 3000
CMD ["node", "server.js"]
```

### Environment Variables

```bash
PORT=3000
NODE_ENV=production
PYTHON_PATH=/path/to/travas-ai/main
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Frontend (Web/Mobile)                   │
│  - Chat interface                               │
│  - Itinerary display                            │
│  - Approval buttons                             │
└──────────────┬──────────────────────────────────┘
               │ HTTP/REST
┌──────────────▼──────────────────────────────────┐
│    Node.js API Gateway (server.js)             │
│  - Route management                             │
│  - Session handling                             │
│  - Response formatting                          │
│  - Error handling                               │
└──────────────┬──────────────────────────────────┘
               │ subprocess/FastAPI
┌──────────────▼──────────────────────────────────┐
│       Python Backend Agents                     │
│  - Sanchalak (Orchestrator)                     │
│  - Specialists (Atithi, Annapurna, etc.)       │
│  - Yojana (Synthesizer)                         │
│  - Parikshak (Validator)                        │
│  - FeedbackHandler (Approval loop)              │
└──────────────┬──────────────────────────────────┘
               │ API calls
┌──────────────▼──────────────────────────────────┐
│         Claude API                              │
│  - LLM responses                                │
│  - Tool use                                     │
└─────────────────────────────────────────────────┘
```

---

## Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | POST | Send user message |
| `/api/feedback` | POST | User approval/revision |
| `/api/status` | GET | Session status |
| `/api/itinerary` | GET | Get current itinerary |
| `/api/history` | GET | Conversation history |
| `/api/restart` | POST | Start new session |
| `/api/health` | GET | Server health check |
| `/` | GET | Welcome & endpoints |

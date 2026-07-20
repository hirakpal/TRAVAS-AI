# TRAVAS-AI Frontend Setup Guide

## Overview

The frontend is a modern, responsive web interface for the TRAVAS-AI travel assistant. It communicates with the Node.js API Gateway which orchestrates the Python backend agents.

```
Browser (Frontend)
    ↓ HTTP/REST
Node.js Frontend Server (Port 8000)
    ↓ FETCH requests
API Gateway (Port 3000)
    ↓ subprocess
Python Backend (Agents)
    ↓
Claude API
```

---

## Quick Start

### Prerequisites

- Node.js installed
- TRAVAS-AI API Gateway running on port 3000
- Modern web browser

### Step 1: Start API Gateway

```bash
cd api/
npm install
npm start
# Server runs on http://localhost:3000
```

### Step 2: Start Frontend Server

```bash
cd frontend/
node server.js
# Server runs on http://localhost:8000
```

### Step 3: Open in Browser

```
http://localhost:8000
```

---

## Frontend Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                    Header (Session Info)                │
├──────────────────────────┬──────────────────────────────┤
│                          │                              │
│   Chat Section           │   Status Section             │
│  (Messages)              │  (Session, Approval State,   │
│  (Input)                 │   Revisions, Action Buttons) │
│                          │                              │
├──────────────────────────┼──────────────────────────────┤
│                          │                              │
│   (Empty on desktop)     │   Itinerary Section          │
│                          │  (Day plans, cost, budget)   │
│                          │                              │
└──────────────────────────┴──────────────────────────────┘
                    Footer
```

### Responsive Design

- **Desktop (>768px):** 2-column layout
- **Mobile (<768px):** Single column, stacked vertically

---

## Features

### 1. Chat Interface

**Send Messages:**
- Type travel query (e.g., "5-day family trip to Goa")
- Press Enter or click Send
- Receive responses from Sanchalak orchestrator

**Message Types:**
- User messages (blue, right-aligned)
- Assistant responses (gray, left-aligned)
- System messages (yellow, centered)

### 2. Session Management

**Automatic:**
- Session created on page load
- Session ID displayed at top
- All requests tagged with session_id

**Manual:**
- Click "New Trip" to start fresh session
- Clears all history and itinerary
- Resets revision count

### 3. Itinerary Viewer

**Displays:**
- Destination, duration, budget
- Day-by-day activities
- Cost breakdown
- Budget alerts

**Format:**
```
📍 Destination | Duration | Budget
📅 Day 1 (Date)
  → Activity 1
  → Activity 2
...
💰 Cost Breakdown
  flights: ₹5,000
  hotel: ₹27,500
  ...
```

### 4. Approval Workflow

**States:**
- **PENDING** - Awaiting user feedback
- **CONDITIONAL** - Approved with warnings
- **APPROVED** - Finalized, ready for booking
- **REJECTED** - User rejected

**Actions:**
- **Approve** ✓ - Lock itinerary
- **Revise** ✏️ - Request specific changes (max 3 times)
- **Reject** ✗ - Reject and choose restart option
- **New Trip** 🔄 - Start fresh session

### 5. Status Tracking

**Real-time Display:**
```
Session ID:      session-123...
Approval State:  PENDING / CONDITIONAL / APPROVED
Revisions Used:  1 / 3
Messages:        12
Server:          🟢 Online / 🔴 Offline
```

---

## User Flow

### Complete Journey

```
1. LOAD
   ↓ Initialize session, check API health
   
2. CHAT
   ↓ User: "5-day trip to Goa"
   ↓ System: Creates draft itinerary
   ↓ Parikshak: Validates (shows warnings if any)
   
3. REVIEW
   ↓ User sees itinerary
   ↓ User reviews day plans, budget, activities
   
4. FEEDBACK
   ↓ User clicks: Approve / Revise / Reject
   
5A. IF APPROVE
    ↓ Itinerary locked ✅
    ↓ Ready for booking
    
5B. IF REVISE
    ↓ User: "Add more beach days"
    ↓ Yojana: Updates itinerary
    ↓ Parikshak: Re-validates
    ↓ Back to REVIEW (max 3 revisions)
    
5C. IF REJECT
    ↓ User chooses: Restart or Modify
    ↓ Either start fresh or revise heavily
    
6. FINALIZE
   ↓ Itinerary approved and finalized
   ↓ Display: Ready for booking
   ↓ User downloads/books
```

---

## API Endpoints Used

### Chat

```
POST /api/chat
Request: { message, session_id }
Response: { session_id, message, response, approval_state }
```

### Feedback

```
POST /api/feedback
Request: { session_id, feedback, action: 'approve'|'revise'|'reject' }
Response: { action, message, next_step, approval_state, revision_count }
```

### Status

```
GET /api/status?session_id=...
Response: { approval_state, revision_count, message_count, can_revise }
```

### Itinerary

```
GET /api/itinerary?session_id=...
Response: { itinerary: { destination, days: [...], budget, ... } }
```

### Restart

```
POST /api/restart
Request: { session_id }
Response: { new_session_id, message }
```

### Health

```
GET /api/health
Response: { status: 'ok', active_sessions }
```

---

## Styling

### Color Scheme

- **Primary:** #667eea (Purple)
- **Success:** #4caf50 (Green) - Approve
- **Info:** #2196f3 (Blue) - Revise
- **Danger:** #f44336 (Red) - Reject
- **Warning:** #ff9800 (Orange) - New Trip
- **Background:** Gradient (purple to violet)

### Responsive Breakpoints

- **Desktop:** >768px - 2 columns
- **Mobile:** ≤768px - 1 column

---

## JavaScript Functions

### Core Functions

**initializeSession()**
- Checks API health
- Creates new session
- Updates display

**sendMessage()**
- Sends user message to API
- Adds to chat display
- Updates status

**submitFeedback(action, feedback)**
- Sends user approval/revision/rejection
- Updates approval state
- Shows alerts

**updateStatus()**
- Fetches current session status
- Updates approval state, revisions
- Refreshes itinerary display

**updateItinerary()**
- Fetches current itinerary
- Displays day plans and budget

**displayItinerary(itinerary)**
- Formats itinerary for display
- Shows cost breakdown

### UI Functions

**addMessage(role, content)**
- Adds message to chat display
- Animates in
- Scrolls to bottom

**showReviseInput()**
- Shows revision input box

**submitRevise()**
- Sends revision feedback

**restartSession()**
- Clears session
- Creates new one
- Resets UI

**showAlert(message, type)**
- Shows temporary alert
- Auto-closes after 5s

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Enter (in chat) | Send message |
| Enter (in revise) | Submit revision |
| Esc | Cancel revision input |

---

## Error Handling

### Scenarios

**API Offline:**
- Shows "Could not connect to API"
- Server indicator: 🔴 Offline
- Suggests starting API gateway

**API Error:**
- Shows error message in chat
- Logs to console
- Buttons remain enabled for retry

**Network Error:**
- Shows alert message
- Disables buttons during request
- Auto-enables after response

### Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (missing fields) |
| 404 | Session not found |
| 500 | Server error |

---

## Advanced Features

### Revision Workflow

```
User revises itinerary
    ↓
submitFeedback('revise', feedback_text)
    ↓
API counts revision (revision_count++)
    ↓
If revision_count < 3:
  ├─ Send to Yojana for revision
  ├─ Yojana updates itinerary
  ├─ Send to Parikshak for validation
  └─ Display updated itinerary
    ↓
If revision_count >= 3:
  └─ Show error: "Max revisions reached"
```

### Session Persistence

**What's Stored:**
- Session ID (in memory on API server)
- Conversation history
- Current itinerary
- Approval state
- Revision count

**What's NOT Stored:**
- Browser local storage (to keep UI simple)
- Persistent database (future: implement Redis)

**Lifetime:**
- Session expires when server restarts
- User can create new session with "New Trip"

---

## Customization

### Modify Colors

Edit CSS in `<style>` section:

```css
/* Change primary color */
.header h1 { color: #your-color; }

/* Change button colors */
.approve-btn { background: #your-color; }
```

### Modify Layout

Edit grid layout:

```css
.container {
    grid-template-columns: 1fr 1fr; /* 2 columns */
    /* Change to: grid-template-columns: 1fr; for 1 column */
}
```

### Add Features

Available functions to call:
- `sendMessage()` - Send chat message
- `submitFeedback(action)` - Send feedback
- `restartSession()` - Reset session
- `showAlert(msg, type)` - Show alert
- `updateStatus()` - Refresh status

---

## Troubleshooting

### Problem: "Could not connect to API"

**Solution:**
1. Start API Gateway: `cd api/ && npm start`
2. Check it's running on http://localhost:3000/api/health
3. Reload frontend page

### Problem: Messages don't send

**Solution:**
1. Check console for errors (F12)
2. Verify API server is running
3. Check session ID is displayed

### Problem: Itinerary doesn't update

**Solution:**
1. Wait for system to process
2. Send another message to trigger refresh
3. Check browser console for errors

### Problem: Buttons are disabled

**Solution:**
1. Wait for message to complete sending
2. Ensure approval state is PENDING
3. Check revision count < 3 for Revise button

---

## Files

```
frontend/
├── index.html          # Main UI (single-page app)
├── server.js           # Simple static file server
└── README.md           # This file
```

---

## Deployment

### Local Development

```bash
node frontend/server.js
# Open http://localhost:8000
```

### Production

Use a proper web server:
- **nginx** - Reverse proxy + static files
- **Express.js** - Full Node.js server
- **Apache** - Traditional web server

Example nginx config:

```nginx
server {
    listen 80;
    server_name travel-ai.example.com;
    
    location / {
        root /path/to/frontend;
        try_files $uri /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:3000;
    }
}
```

---

## Browser Support

- Chrome/Edge (Latest)
- Firefox (Latest)
- Safari (Latest)
- Mobile browsers (iOS Safari, Chrome Android)

**Not supported:**
- Internet Explorer
- Very old browser versions

---

## Performance

### Optimizations

- Lazy message rendering (add as received)
- Auto-scroll to latest message
- Disable buttons during requests
- Cache session state

### Metrics

- Page load: <1s
- Message send: <2s
- Itinerary display: <1s
- Chat response: Depends on Claude API (usually 5-10s)

---

## Security Notes

- Session IDs are ephemeral (not stored in browser)
- No authentication (for demo)
- API requests include session_id for context
- Future: Add OAuth, JWT tokens

---

## Support

For issues or features:
1. Check console (F12) for errors
2. Review API logs
3. Check this guide's troubleshooting section
4. Submit issue to GitHub

---

## Summary

The TRAVAS-AI frontend provides:
✅ Clean, intuitive chat interface
✅ Real-time itinerary display
✅ Approval workflow with revisions
✅ Session management
✅ Responsive design
✅ Error handling
✅ Status tracking

Ready to start planning trips! 🌍✈️

# TRAVAS-AI: Complete Working Demo Setup

## System Architecture

```
┌────────────────────────────────────────────┐
│    Web Browser (Port 8000)                  │
│    frontend/index.html                      │
│  - Chat UI                                  │
│  - Itinerary display                        │
│  - Approval workflow                        │
└──────────────────┬─────────────────────────┘
                   │ HTTP Fetch
┌──────────────────▼─────────────────────────┐
│    Node.js API Gateway (Port 3000)         │
│    api/server.js                            │
│  - Bridges frontend ↔ Python backend       │
│  - Session management                       │
│  - Request routing                          │
└──────────────────┬─────────────────────────┘
                   │ HTTP Fetch
┌──────────────────▼─────────────────────────┐
│    Python FastAPI Backend (Port 5000)      │
│    python_backend/api.py                    │
│  - Sanchalak orchestrator                   │
│  - Specialist agents                        │
│  - FeedbackHandler                          │
│  - Claude API integration                   │
└────────────────────────────────────────────┘
```

---

## Quick Start (3 Easy Steps)

### Step 1: Install Python Backend Dependencies

```bash
cd python_backend/
pip install -r requirements.txt
```

### Step 2: Open 3 Terminals

**Terminal 1 - Python Backend:**
```bash
cd python_backend/
python api.py
# Should show: TRAVAS-AI Python Backend FastAPI Server Started
#             http://localhost:5000
```

**Terminal 2 - Node.js API Gateway:**
```bash
cd api/
npm start
# Should show: TRAVAS-AI API Gateway Started
#             http://localhost:3000
```

**Terminal 3 - Frontend Server:**
```bash
cd frontend/
node server.js
# Should show: TRAVAS-AI Frontend Server Started
#             http://localhost:8000
```

### Step 3: Open Browser

```
http://localhost:8000
```

---

## What You'll See

### Frontend Interface

1. **Header** - Session info, status, revision counter
2. **Chat Section** - Send travel queries
   - Example: "I want a 5-day family trip to Goa with budget ₹25,000"
3. **Status Panel** - Real-time session tracking
4. **Itinerary Viewer** - Day-by-day plans and budget
5. **Action Buttons** - Approve / Revise / Reject / New Trip

### Complete Flow

```
User Query
  ↓
Sanchalak Routes to Specialists
  ↓
All 5 Agents Provide Recommendations
  ↓
Yojana Creates Draft Itinerary
  ↓
Parikshak Validates (7 checks)
  ↓
Frontend Displays Itinerary
  ↓
User Feedback (Approve/Revise/Reject)
  ↓
System Processes & Updates
  ↓
✅ Final Itinerary Approved
```

---

## Demo Script

### Scenario: Family Trip to Goa

**In the browser:**

1. **Type in chat:**
   ```
   I want a 5-day family trip to Goa. 
   2 adults, 2 kids (6 and 9). 
   Budget ₹25,000. 
   We want beaches, culture, good food, and activities.
   ```

2. **Click Send**
   - System processes through all 8 agents
   - Itinerary appears in "Travel Itinerary" section
   - Shows 5 days of activities and cost breakdown

3. **Review the itinerary**
   - Check: Day 1 (Arrival), Day 2 (Beach), Day 3 (Full day trip), Day 4 (Rest + Culture), Day 5 (Departure)
   - Review: Budget, activities, meal timings

4. **User Feedback - Revision:**
   - Click **Revise** button
   - Type: "Increase budget to ₹45,000. Skip temple. Add kids activity instead."
   - Click **Submit Revision**
   - System revises itinerary
   - Parikshak re-validates
   - Itinerary updates with dolphin tour instead of temple

5. **User Approval:**
   - Review updated itinerary
   - Click **Approve**
   - System shows: "Itinerary approved and finalized!"
   - Status changes to APPROVED

6. **Done!**
   - Itinerary is locked and ready for booking
   - User can download/share/book

---

## Troubleshooting

### "Could not connect to localhost:3000"

**Fix:**
```bash
# Terminal 2 - Restart Node.js API
cd api/
npm start
```

### "Python backend not running"

**Fix:**
```bash
# Terminal 1 - Restart Python FastAPI
cd python_backend/
python api.py
```

### "Frontend server not responding"

**Fix:**
```bash
# Terminal 3 - Restart Frontend
cd frontend/
node server.js
```

### Frontend stuck on "Initializing..."

**Check:**
1. All 3 servers are running (check all 3 terminals)
2. Open browser DevTools (F12) → Console → Check for errors
3. Ensure Python backend is actually running (should show: "TRAVAS-AI Python Backend FastAPI Server Started")

### "Cannot find module"

**Fix:**
```bash
# In python_backend/
pip install -r requirements.txt

# In api/
npm install

# In frontend/
node server.js (no install needed)
```

---

## Architecture Details

### Python FastAPI Backend (Port 5000)

**Endpoints:**
- `POST /api/chat` - Send message to Sanchalak agent
- `POST /api/feedback` - Send user approval/revision
- `GET /api/status` - Get session status
- `GET /api/itinerary` - Get itinerary
- `GET /api/history` - Get conversation history
- `POST /api/restart` - Start new session
- `GET /api/health` - Server health check
- `GET /docs` - API documentation (Swagger UI)

**Features:**
- Real Claude API integration via Sanchalak agent
- Multi-agent coordination via shared state
- 7-point quality validation (Parikshak)
- Human-in-the-loop feedback handling
- Session management

### Node.js API Gateway (Port 3000)

**Endpoints:**
Same as Python backend, but acts as a proxy

**Features:**
- Translates frontend requests to Python backend calls
- Bridges HTTP requests between 3000 and 5000
- Fallback to mock responses if Python backend offline
- CORS support for frontend
- Session tracking

### Frontend Server (Port 8000)

**Features:**
- React-like chat interface
- Real-time itinerary display
- Approval workflow with revisions (max 3)
- Session tracking
- Status updates
- Responsive design

---

## Running Just the Python Demo (No Frontend)

If you just want to see the system work without the UI:

```bash
python demo_complete_end_to_end.py
```

This shows the full 10-step journey in the terminal with all agents working together.

---

## Production Deployment

For production, you would:

1. **Python Backend:**
   - Deploy FastAPI on Heroku/AWS/GCP
   - Use PostgreSQL instead of in-memory sessions
   - Add authentication (JWT)
   - Set environment variables for API keys

2. **Node.js Gateway:**
   - Deploy on AWS/Vercel/Railway
   - Use Redis for session caching
   - Add rate limiting
   - Set CORS properly

3. **Frontend:**
   - Build React app (optimized)
   - Deploy on Vercel/Netlify
   - Update API URLs to production endpoints
   - Add analytics

---

## Key Components

### Agents (Python Backend)
- **Sanchalak** - Orchestrator (routes to specialists)
- **Atithi** - Hotel recommendations
- **Annapurna** - Food/restaurant recommendations
- **Yatra** - Attractions/tours
- **Safar** - Transport (flights, local)
- **Bazaar** - Shopping
- **Yojana** - Plan synthesis
- **Parikshak** - Quality validation

### Tools (35+)
- Search hotels, restaurants, attractions, transport, shops
- Filter by price, rating, distance, preferences
- Validate itineraries
- Optimize sequences
- Check conflicts
- Analyze pace and meal gaps

### Frontend Components
- Chat interface
- Message display
- Itinerary viewer
- Approval buttons
- Status tracker
- Session manager

---

## Success Criteria

✅ **Frontend loads** - Port 8000 works
✅ **API Gateway runs** - Port 3000 connects
✅ **Python Backend** - Port 5000 serves requests
✅ **User can chat** - Messages send and receive
✅ **Itinerary displays** - Day plans show in UI
✅ **Feedback works** - Approve/Revise/Reject buttons work
✅ **Status updates** - Real-time approval state changes
✅ **Multi-turn flow** - Full journey works end-to-end

---

## Demo Presentation Script

**Opening:**
"This is TRAVAS-AI - an AI-powered travel assistant powered by Claude, using 8 specialized agents working together through multi-agent orchestration."

**Show System:**
"The system has three layers:
- Python backend with AI agents
- Node.js API gateway
- Web frontend UI"

**Live Demo:**
1. Type travel query in browser
2. Show how Sanchalak routes to specialists
3. Show itinerary appears
4. Make a revision
5. Show system updates
6. Approve itinerary

**Highlight:**
- Real Claude API integration
- Multi-agent coordination
- Quality validation with 7 checks
- Human feedback loop with revisions
- Clean, intuitive UI
- Production-ready architecture

**Conclusion:**
"Complete AI travel planning system showcasing 2026 AI patterns: tool use, iterative loops, and multi-agent orchestration."

---

## Support

If you encounter issues:

1. Check all 3 terminal windows are running
2. Check error messages in terminals
3. Read the terminal output carefully
4. Check browser console (F12)
5. Restart servers in this order: Python → Node → Frontend
6. Clear browser cache (Ctrl+Shift+Delete)

---

## Summary

**Three servers, three ports:**
- Port 5000: Python FastAPI (brain - agents)
- Port 3000: Node.js API (translator)
- Port 8000: Frontend server (UI)

**One complete system showing:**
✅ Multi-agent AI orchestration
✅ Real-time user feedback loop
✅ Quality validation
✅ Production-ready architecture
✅ Beautiful, functional UI

Ready to impress! 🚀


/**
 * TRAVAS-AI API Gateway (Node.js)
 *
 * Bridges frontend and Python backend agents
 * Handles session management, routing, and response streaming
 */

const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// ============================================================================
// MIDDLEWARE
// ============================================================================

app.use(cors());
app.use(express.json());

// Session storage (in-memory for demo, use Redis in production)
const sessions = new Map();

// ============================================================================
// UTILITIES
// ============================================================================

/**
 * Generate unique session ID
 */
function generateSessionId() {
  return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Get or create session
 */
function getOrCreateSession(sessionId = null) {
  if (sessionId && sessions.has(sessionId)) {
    return { sessionId, session: sessions.get(sessionId) };
  }

  const newSessionId = generateSessionId();
  const session = {
    id: newSessionId,
    created_at: new Date().toISOString(),
    messages: [],
    itinerary: null,
    approval_state: 'PENDING',
    revision_count: 0,
    max_revisions: 3
  };

  sessions.set(newSessionId, session);
  return { sessionId: newSessionId, session };
}

/**
 * Call Python agent (subprocess)
 */
function callPythonAgent(scriptName, args) {
  return new Promise((resolve, reject) => {
    const pythonPath = path.join(__dirname, '..', scriptName);

    // Check if script exists
    if (!fs.existsSync(pythonPath)) {
      reject(new Error(`Python script not found: ${pythonPath}`));
      return;
    }

    const python = spawn('python', [pythonPath, ...args], {
      cwd: path.join(__dirname, '..')
    });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(stdout);
          resolve(result);
        } catch (e) {
          resolve({ status: 'success', message: stdout });
        }
      } else {
        reject(new Error(`Python error: ${stderr}`));
      }
    });

    // Timeout after 30 seconds
    setTimeout(() => {
      python.kill();
      reject(new Error('Python script timeout'));
    }, 30000);
  });
}

/**
 * Log request/response
 */
function logInteraction(sessionId, type, data) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${type.toUpperCase()} - Session: ${sessionId}`);
  console.log(JSON.stringify(data, null, 2));
}

// ============================================================================
// ROUTES
// ============================================================================

/**
 * POST /api/chat - Send user message, get response
 *
 * Body: {
 *   message: string,
 *   session_id?: string (optional, creates new if not provided)
 * }
 *
 * Response: {
 *   session_id: string,
 *   message: string,
 *   response: string,
 *   approval_state: string,
 *   status: string
 * }
 */
app.post('/api/chat', async (req, res) => {
  try {
    const { message, session_id } = req.body;

    if (!message) {
      return res.status(400).json({
        status: 'error',
        message: 'Message is required'
      });
    }

    // Get or create session
    const { sessionId, session } = getOrCreateSession(session_id);

    logInteraction(sessionId, 'user', { message });

    // Add to session history
    session.messages.push({
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    });

    // Call Python backend (Sanchalak orchestrator)
    // In production, this would call a FastAPI endpoint instead
    const response = {
      role: 'assistant',
      content: `[Sanchalak Response] Processing: "${message}"`,
      timestamp: new Date().toISOString()
    };

    session.messages.push(response);

    logInteraction(sessionId, 'assistant', response);

    return res.status(200).json({
      session_id: sessionId,
      message: message,
      response: response.content,
      approval_state: session.approval_state,
      status: 'success'
    });

  } catch (error) {
    console.error('Chat error:', error);
    return res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

/**
 * POST /api/feedback - Send user feedback (approve/revise/reject)
 *
 * Body: {
 *   session_id: string,
 *   feedback: string,
 *   action: 'approve' | 'revise' | 'reject' | 'clarify'
 * }
 *
 * Response: {
 *   session_id: string,
 *   action: string,
 *   message: string,
 *   next_step: string,
 *   approval_state: string
 * }
 */
app.post('/api/feedback', async (req, res) => {
  try {
    const { session_id, feedback, action } = req.body;

    if (!session_id || !feedback) {
      return res.status(400).json({
        status: 'error',
        message: 'session_id and feedback are required'
      });
    }

    if (!sessions.has(session_id)) {
      return res.status(404).json({
        status: 'error',
        message: 'Session not found'
      });
    }

    const session = sessions.get(session_id);

    logInteraction(session_id, 'feedback', { action, feedback });

    // Process feedback based on action
    let result = {};

    if (action === 'approve') {
      result = {
        action: 'approve',
        message: 'Itinerary approved and finalized!',
        next_step: 'FINALIZE',
        status: 'success'
      };
      session.approval_state = 'APPROVED';
    } else if (action === 'revise') {
      if (session.revision_count >= session.max_revisions) {
        result = {
          action: 'revise',
          message: `Max revisions (${session.max_revisions}) reached`,
          next_step: 'ESCALATE',
          status: 'error'
        };
      } else {
        session.revision_count++;
        result = {
          action: 'revise',
          message: `Processing revision (Attempt ${session.revision_count}/${session.max_revisions})`,
          next_step: 'SEND_TO_YOJANA',
          status: 'success'
        };
      }
    } else if (action === 'reject') {
      result = {
        action: 'reject',
        message: 'Would you like to:\n1. Start fresh?\n2. Make specific changes?',
        next_step: 'ASK_RESTART_STRATEGY',
        status: 'clarify'
      };
      session.approval_state = 'REJECTED';
    } else if (action === 'clarify') {
      result = {
        action: 'clarify',
        message: 'What would you like to know about the itinerary?',
        next_step: 'ANSWER_QUESTION',
        status: 'info'
      };
    } else {
      return res.status(400).json({
        status: 'error',
        message: `Unknown action: ${action}`
      });
    }

    // Add to session
    session.messages.push({
      role: 'user',
      content: feedback,
      metadata: { action }
    });

    return res.status(200).json({
      session_id: session_id,
      ...result,
      approval_state: session.approval_state,
      revision_count: session.revision_count
    });

  } catch (error) {
    console.error('Feedback error:', error);
    return res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

/**
 * GET /api/status - Get current session status
 *
 * Query: session_id
 *
 * Response: {
 *   session_id: string,
 *   approval_state: string,
 *   revision_count: number,
 *   message_count: number,
 *   created_at: string
 * }
 */
app.get('/api/status', (req, res) => {
  try {
    const { session_id } = req.query;

    if (!session_id) {
      return res.status(400).json({
        status: 'error',
        message: 'session_id is required'
      });
    }

    if (!sessions.has(session_id)) {
      return res.status(404).json({
        status: 'error',
        message: 'Session not found'
      });
    }

    const session = sessions.get(session_id);

    return res.status(200).json({
      status: 'success',
      session_id: session_id,
      approval_state: session.approval_state,
      revision_count: session.revision_count,
      max_revisions: session.max_revisions,
      message_count: session.messages.length,
      created_at: session.created_at,
      can_revise: session.revision_count < session.max_revisions
    });

  } catch (error) {
    console.error('Status error:', error);
    return res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

/**
 * GET /api/itinerary - Get current itinerary
 *
 * Query: session_id
 *
 * Response: {
 *   session_id: string,
 *   itinerary: object,
 *   status: string
 * }
 */
app.get('/api/itinerary', (req, res) => {
  try {
    const { session_id } = req.query;

    if (!session_id) {
      return res.status(400).json({
        status: 'error',
        message: 'session_id is required'
      });
    }

    if (!sessions.has(session_id)) {
      return res.status(404).json({
        status: 'error',
        message: 'Session not found'
      });
    }

    const session = sessions.get(session_id);

    return res.status(200).json({
      status: 'success',
      session_id: session_id,
      itinerary: session.itinerary || { status: 'not_ready' },
      approval_state: session.approval_state,
      revision_count: session.revision_count
    });

  } catch (error) {
    console.error('Itinerary error:', error);
    return res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

/**
 * GET /api/history - Get conversation history
 *
 * Query: session_id
 *
 * Response: {
 *   session_id: string,
 *   messages: array,
 *   total_messages: number
 * }
 */
app.get('/api/history', (req, res) => {
  try {
    const { session_id } = req.query;

    if (!session_id) {
      return res.status(400).json({
        status: 'error',
        message: 'session_id is required'
      });
    }

    if (!sessions.has(session_id)) {
      return res.status(404).json({
        status: 'error',
        message: 'Session not found'
      });
    }

    const session = sessions.get(session_id);

    return res.status(200).json({
      status: 'success',
      session_id: session_id,
      messages: session.messages,
      total_messages: session.messages.length
    });

  } catch (error) {
    console.error('History error:', error);
    return res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

/**
 * POST /api/restart - Clear session and start fresh
 *
 * Body: {
 *   session_id: string
 * }
 *
 * Response: {
 *   new_session_id: string,
 *   status: string
 * }
 */
app.post('/api/restart', (req, res) => {
  try {
    const { session_id } = req.body;

    if (session_id && sessions.has(session_id)) {
      sessions.delete(session_id);
    }

    // Create new session
    const { sessionId, session } = getOrCreateSession();

    return res.status(200).json({
      status: 'success',
      new_session_id: sessionId,
      message: 'New session started. Ready for trip preferences.'
    });

  } catch (error) {
    console.error('Restart error:', error);
    return res.status(500).json({
      status: 'error',
      message: error.message
    });
  }
});

/**
 * GET /api/health - Health check
 */
app.get('/api/health', (req, res) => {
  res.status(200).json({
    status: 'ok',
    service: 'TRAVAS-AI API Gateway',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    active_sessions: sessions.size
  });
});

/**
 * GET / - Welcome message
 */
app.get('/', (req, res) => {
  res.json({
    service: 'TRAVAS-AI API Gateway',
    version: '1.0.0',
    endpoints: {
      'POST /api/chat': 'Send user message',
      'POST /api/feedback': 'Send approval/revision/rejection',
      'GET /api/status': 'Get session status',
      'GET /api/itinerary': 'Get current itinerary',
      'GET /api/history': 'Get conversation history',
      'POST /api/restart': 'Start new session',
      'GET /api/health': 'Health check'
    }
  });
});

// ============================================================================
// ERROR HANDLING
// ============================================================================

app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({
    status: 'error',
    message: err.message
  });
});

// ============================================================================
// SERVER START
// ============================================================================

app.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════════════════════════╗
║        TRAVAS-AI API Gateway Started                       ║
║                                                            ║
║  Server: http://localhost:${PORT}                            ║
║  Health: http://localhost:${PORT}/api/health               ║
║                                                            ║
║  Endpoints:                                                ║
║    POST   /api/chat        - Send user message            ║
║    POST   /api/feedback    - User approval/revision       ║
║    GET    /api/status      - Session status               ║
║    GET    /api/itinerary   - Current itinerary            ║
║    GET    /api/history     - Conversation history         ║
║    POST   /api/restart     - Start new session            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
  `);
});

module.exports = app;

# Human-in-the-Loop Feedback System

## Overview

After Yojana creates and Parikshak validates a travel itinerary, the user has several options:

```
┌──────────────────────────────────────────────────────────┐
│          APPROVED ITINERARY READY FOR USER              │
└────────────────┬─────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
   APPROVED          NOT APPROVED
      │                   │
      ├─→ Approve ✅     ├─→ Revise (Change details)
      │                  ├─→ Reject (Start over)
      │                  └─→ Clarify (Ask questions)
      ▼
   FINALIZED
   ✅ Ready for booking
```

## 5 User Intents

### 1. **APPROVE** ✅
User explicitly approves and locks the itinerary.

**Keywords:** "approve", "yes", "looks good", "perfect", "proceed", "finaliz"

**Example:**
```
User: "Yes, this looks perfect! I approve this plan."
System: ✅ Itinerary finalized. Ready for booking.
```

**Flow:**
```
User says "APPROVE"
    ↓
FeedbackHandler.process_user_feedback()
    ↓
intent = "APPROVE"
    ↓
approval_status = "APPROVED"
    ↓
Finalize itinerary with metadata
    ↓
Return to user: "Booking ready"
```

**Result:**
- Itinerary locked
- Cannot be changed
- User can proceed to booking

---

### 2. **REVISE** 🔄
User requests specific changes to the itinerary.

**Keywords:** "change", "add", "remove", "modify", "different", "instead", "also", "can you"

**Example:**
```
User: "Can you add more beach time? I want 2 full beach days."
System: Processing revision (Attempt 1/3)...
🔄 Yojana revises itinerary
🔍 Parikshak validates
✅ Updated plan ready for review
```

**Flow:**
```
User says "REVISE"
    ↓
FeedbackHandler classifies as "REVISE"
    ↓
Check if revisions allowed (revision_count < max_revisions)
    ↓
If YES:
  ├─ revision_count++
  ├─ Extract revision details
  ├─ Send to Yojana for revision
  ├─ Yojana.revise_itinerary(feedback)
  ├─ Send revised plan to Parikshak
  ├─ Parikshak.validate_itinerary()
  └─ Return revised plan to user
    ↓
If NO (reached max):
  └─ Return error: "Max revisions reached"
```

**Revision Loop (Example with 2 changes):**
```
Initial: ✅ APPROVED itinerary
    ↓
User Revision 1: "Add more beach"
    ↓
🔄 Yojana → 🔍 Parikshak ✅ APPROVED (Revision 1 complete)
    ↓
User Revision 2: "Replace temple with market"
    ↓
🔄 Yojana → 🔍 Parikshak ✅ APPROVED (Revision 2 complete)
    ↓
User says "Perfect!"
    ↓
✅ FINALIZED (after 2 revisions)
```

**Limits:**
- Max 3 revisions per itinerary
- Tracked: `revision_count` (current) vs `max_revisions` (limit)

---

### 3. **REJECT** ❌
User rejects the entire itinerary and needs to choose: restart or modify?

**Keywords:** "no", "reject", "redo", "start over", "doesn't work", "bad", "nope"

**Example:**
```
User: "No, this doesn't work for us."
System: Would you like to:
        1. Start completely fresh?
        2. Make specific changes?
```

**Flow:**
```
User says "REJECT"
    ↓
FeedbackHandler returns: "Restart strategy?" message
    ↓
User chooses...

Option A: RESTART_FRESH
    ├─ Reset all preferences
    ├─ Start new conversation with Sanchalak
    └─ Restart the full specialist flow
        
Option B: MAKE_SPECIFIC_CHANGES
    ├─ Ask for detailed change request
    ├─ Send as revision (counts as Revision 1)
    ├─ Yojana revises
    └─ Parikshak validates
```

**Timeline:**
```
REJECT decision → Choose restart strategy → Execute strategy
```

---

### 4. **CLARIFY** ❓
User asks questions about the itinerary (not rejecting, not approving yet).

**Keywords:** "why", "how", "explain", "tell me", "what", "curious", "question"

**Example:**
```
User: "How long is the Dudhsagar drive? Will kids be okay?"
System: "1.5 hours each way. We scheduled a full day with rest.
        Bring snacks and entertainment. Sound okay?"
User: "Yes, that works!"
System: Should I make any changes or approve?
```

**Flow:**
```
User asks question
    ↓
FeedbackHandler: intent = "CLARIFY"
    ↓
Return: "Here's info about that. Any changes needed?"
    ↓
User responds (approve/revise/clarify again)
```

---

## State Tracking

### ItineraryApprovalState

```python
@dataclass
class ItineraryApprovalState:
    current_itinerary: Optional[Dict]          # Active plan
    validation_status: str                      # APPROVED/REVISION/CONDITIONAL
    revision_count: int = 0                     # How many revisions used
    max_revisions: int = 3                      # Max allowed
    user_feedback_history: List = []            # All user messages
    approval_status: str = "PENDING"            # PENDING/APPROVED/REJECTED
    feedback_rounds: int = 0                    # Number of feedback rounds
```

**Lifecycle:**
```
Initial:
  approval_status: "PENDING"
  revision_count: 0
  feedback_rounds: 0

After 1st revision:
  revision_count: 1
  feedback_rounds: 1
  approval_status: "PENDING" (still)

After approval:
  approval_status: "APPROVED"
  revision_count: (final count)
  feedback_rounds: (final count)

After rejection:
  approval_status: "RESTART" or "REJECTED"
```

---

## Complete Conversation Flow

### Full Journey: Good → Revise → Approve

```
STEP 1: Itinerary Ready
─────────────────────────
System: "Here's your 5-day Goa itinerary:
        - Day 1: Arrival + Beach
        - Day 2: Dudhsagar Waterfall
        - Day 3: Fort Aguada + Market
        - Day 4: Rest + Shopping
        - Day 5: Departure
        
        ✅ APPROVED by Parikshak"

User Approval State: PENDING (0 revisions)

STEP 2: User Wants Change
──────────────────────────
User: "Can you add more beach? I want 2 beach days."

FeedbackHandler:
  ✓ Intent: REVISE
  ✓ Revisions allowed: YES (0 < 3)
  ✓ Increment counter: revision_count = 1
  ✓ Send to Yojana

Yojana revises:
  ✓ Day 1: Arrival + Beach
  ✓ Day 2: Full Beach Day (new)
  ✓ Day 3: Dudhsagar
  ✓ Day 4: Fort + Market
  ✓ Day 5: Departure

Parikshak validates:
  ✓ No conflicts
  ✓ Pace balanced
  ✓ Preferences matched
  ✓ Status: ✅ APPROVED

User Approval State: PENDING (1 revision, Revision 1 complete)

STEP 3: User Satisfied
──────────────────────
User: "Perfect! This is exactly what I want. Approve."

FeedbackHandler:
  ✓ Intent: APPROVE
  ✓ approval_status = "APPROVED"
  ✓ Finalize itinerary

Finalized Itinerary:
  {
    "destination": "Goa",
    "days": [...],
    "approval_status": "APPROVED",
    "approval_timestamp": "2026-07-20T10:30:00",
    "approval_metadata": {
      "revision_count": 1,
      "feedback_rounds": 2,
      "changes_made": ["Added beach day"]
    }
  }

✅ READY FOR BOOKING

User Approval State: APPROVED (1 revision used)
```

---

## Rejection Paths

### Path A: Reject → Restart Fresh

```
User: "No, this completely doesn't work."
  ↓
System: "Start fresh OR make changes?"
  ↓
User: "I want to start completely fresh."
  ↓
FeedbackHandler: approval_status = "RESTART"
  ↓
System: "Great! Let's start over. Tell me about your trip..."
  ↓
Sanchalak: Begins new conversation
  ↓
Specialists: Gather new preferences
  ↓
Yojana: Creates new itinerary
```

### Path B: Reject → Make Specific Changes

```
User: "No, this doesn't work for us."
  ↓
System: "What specific changes do you need?"
  ↓
User: "We want more adventure, less shopping. Different hotel."
  ↓
FeedbackHandler:
  ├─ revision_count = 1
  ├─ Send to Yojana as revision
  └─ Yojana revises with new focus
  ↓
Parikshak validates
  ↓
Updated plan ready
```

---

## Edge Cases

### Case 1: Max Revisions Reached

```
User: [Revision request #4]
System: "Max revisions (3) reached.
        Options:
        1. Start fresh with new preferences
        2. Contact support for manual planning"
```

**Code:**
```python
if not approval_state.can_revise():
    return "ESCALATE", {
        "message": "Max revisions reached...",
        "next_step": "ESCALATE"
    }
```

### Case 2: Parikshak Rejects Revision

```
User: [Requests change #2]
Yojana: Revises itinerary
Parikshak: ❌ REVISION NEEDED
  └─ "Conflicts found: Beach (2-5pm) overlaps Waterfall (4-8pm)"

FeedbackHandler:
  └─ Return Parikshak's feedback to user
     "Your revision created a conflict. Yojana needs to try again."
```

### Case 3: User Keeps Asking Clarifications

```
User 1: "What's the distance to Dudhsagar?"
System: [Answer] "Any changes needed?"
  ↓
User 2: "Are there ATMs at the temple?"
System: [Answer] "Any changes needed?"
  ↓
User 3: "What's the food cost estimate?"
System: [Answer] "Are you ready to approve or revise?"
```

**Tracking:** Feedback rounds increment but revision_count doesn't change.

---

## Integration Points

### With Sanchalak (Orchestrator)

```python
# Sanchalak routes to FeedbackHandler after Parikshak approval
def handle_post_validation(validation_result):
    if "APPROVED" in validation_result:
        # Show itinerary to user
        # Wait for feedback
        user_message = get_user_message()
        
        # Send to FeedbackHandler
        action, details = feedback_handler.process_user_feedback(
            user_message,
            yojana_itinerary
        )
        
        if action == "APPROVE":
            return finalize_itinerary(details)
        
        elif action == "REVISE":
            # Back to Yojana for revision
            return revise_and_revalidate(details)
        
        elif action == "REJECT":
            # Ask restart strategy
            return handle_restart_decision()
```

### With Yojana (Synthesizer)

```python
# Yojana receives revision request from FeedbackHandler
def revise_itinerary(feedback: str):
    """Called after user requests changes"""
    # User's revision request comes from FeedbackHandler
    response = claude_api_call(
        system=self.SYSTEM_PROMPT,
        messages=[
            ...,
            {"role": "user", "content": feedback}  # From FeedbackHandler
        ]
    )
    return response
```

### With Parikshak (Reviewer)

```python
# Parikshak validates revised itineraries in the loop
def validate_revised_itinerary(itinerary):
    """Called after Yojana revision"""
    validation = self.validate_itinerary(itinerary_json)
    
    if "APPROVED" in validation:
        # Back to user for next decision
        return validation
    
    elif "REVISION" in validation:
        # Auto-fix failed, user needs to clarify
        return validation
```

---

## Data Flow Diagram

```
User Input (Feedback)
    ↓
┌─────────────────────────────┐
│   FeedbackHandler           │
│  - Classify Intent          │
│  - Check Limits             │
│  - Extract Details          │
└────────┬────────────────────┘
         │
    ┌────┴──────┬───────────┬─────────────┐
    ▼           ▼           ▼             ▼
  APPROVE     REVISE      REJECT      CLARIFY
    │           │           │            │
    │       Yojana      Ask Strategy  Answer
    │         ↓             ↓            ↓
    │      Parikshak    Restart or  Provide Info
    │         ↓         Modify?         ↓
    │      Validate      ↓            User
    │         ↓      FeedbackHandler  Decides
    │      Result       ↓
    │         ↓      Continue Loop
    │      Return
    │
    └────→ Finalize
           ✅ APPROVED

Shared State Updated at Each Step
```

---

## Message Format

### User → System

```json
{
  "user_message": "Can you add more beach time?",
  "session_id": "session-123",
  "timestamp": "2026-07-20T10:30:00"
}
```

### System → FeedbackHandler

```json
{
  "user_message": "Can you add more beach time?",
  "current_itinerary": {...},
  "current_approval_state": {...}
}
```

### FeedbackHandler → System

```json
{
  "action": "REVISE",
  "status": "success",
  "message": "Processing revision (Attempt 1/3)",
  "next_step": "SEND_TO_YOJANA",
  "feedback": "Can you add more beach time?",
  "revision_number": 1,
  "approval_state": {
    "approval_status": "PENDING",
    "revision_count": 1,
    "feedback_rounds": 1,
    "can_revise": true
  }
}
```

---

## Summary Table

| Intent | Keywords | Action | Next Step | Revision? |
|--------|----------|--------|-----------|-----------|
| APPROVE | yes, perfect, approve | Lock itinerary | Finalize | No |
| REVISE | change, add, modify | Extract feedback | Send to Yojana | Yes (+1) |
| REJECT | no, redo, doesn't work | Ask strategy | Restart or Modify | Conditional |
| CLARIFY | why, how, explain | Answer question | Ask if changes needed | No |

---

## Files

```
agents/
  ├── feedback_handler.py       # Intent classification & feedback management
  └── ...

demo_human_feedback_loop.py     # Shows all 5 scenarios
```

---

## Next: Integration

The complete flow will be:

```
User Query
  ↓
Sanchalak (Orchestrator)
  ↓
Specialists (Atithi, Annapurna, Yatra, Safar, Bazaar)
  ↓
Yojana (Creates Draft)
  ↓
Parikshak (Validates)
  ↓
✅ APPROVED → Show to User
  ↓
👤 User Feedback (APPROVE/REVISE/REJECT/CLARIFY)
  ↓
FeedbackHandler (Process Intent) ← NEW
  ├─ APPROVE → Finalize ✅
  ├─ REVISE → Back to Yojana
  ├─ REJECT → Ask Restart Strategy
  └─ CLARIFY → Answer & Continue
  ↓
[Loop if needed]
  ↓
✅ FINALIZED ITINERARY
```

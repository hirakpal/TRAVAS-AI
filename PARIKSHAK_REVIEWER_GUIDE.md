# Parikshak: The Quality Reviewer Agent

## Overview

**Parikshak** (परीक्षक = Reviewer/Inspector) is the quality gate that validates draft itineraries before they reach the user. Parikshak ensures that Yojana's synthesis meets all constraints, preferences, and specialist recommendations.

```
Yojana (Plan Synthesizer)
         ↓
    [DRAFT ITINERARY]
         ↓
Parikshak (Quality Reviewer) ← NEW AGENT
         ↓
    ✅ APPROVED / ❌ REVISION NEEDED / ⚠️ CONDITIONAL
         ↓
    [TO USER or BACK TO YOJANA]
```

---

## Why Parikshak?

**Without Parikshak:**
- Yojana creates plan
- Plan might have conflicts, be too rushed, ignore preferences
- User discovers issues during review (frustrating)
- Entire plan must be redone

**With Parikshak:**
- Yojana creates plan
- Parikshak runs automated quality checks
- Issues caught before user sees plan (proactive)
- Only genuinely good plans reach user
- Yojana can revise in minutes, not start over

---

## Parikshak's 7 Validation Checks

### 1. **Scheduling Conflicts** ❌
Detects impossible time overlaps.

```
Activity A: 2:00 PM - 4:00 PM (Baga Beach)
Activity B: 3:30 PM - 5:00 PM (Dudhsagar) ❌ OVERLAP

Solution: Separate by full day or remove one
```

**Tool:** `check_scheduling_conflicts`

---

### 2. **Duplicate Attractions** 🔄
Identifies if same place appears multiple times (unless intentional).

```
Day 1: Baga Beach (9am-12pm)
Day 3: Baga Beach (2pm-5pm) ❌ DUPLICATE

Unless: Multi-part visit (snorkeling Day 1, sunset Day 3) ✓
```

**Tool:** `check_duplicate_attractions`

---

### 3. **Pace Analysis** ⚡
Validates daily activity load matches traveler type.

```
Guidelines by traveler type:
- Family with kids: Max 6 hours/day activities
- Standard travelers: Max 8 hours/day
- Adventure seekers: Max 10 hours/day
- Relaxation: Max 4 hours/day

Examples:
✓ Day 1: 4 hours (good for family travel day)
✓ Day 2: 6 hours (full day, within limits)
❌ Day 1: 10 hours (too much for kids after flights)
❌ Day 3: 2 hours (why schedule non-travel day so light?)
```

**Tool:** `analyze_pace`

---

### 4. **Meal Gaps** 🍽️
Ensures realistic meal timings with no excessive gaps.

```
Acceptable:
✓ Breakfast 8am, Lunch 12:30pm, Dinner 7pm
✓ First meal before 10am
✓ Max 6-hour gap between meals

Not acceptable:
❌ Breakfast 7am, Lunch 2pm, Dinner 8pm (7-hour gap before dinner)
❌ First meal at 11am (late breakfast)
❌ Lunch at 1pm, Dinner at 8pm (7-hour gap)
```

**Tool:** `check_meal_gaps`

---

### 5. **Excessive Travel** 🚗
Detects unrealistic travel distances/times.

```
Single segment limits:
- ≤ 2 hours: Normal
- 2-3 hours: Acceptable (scenic drive)
- > 3 hours: ❌ TOO LONG (recommend split)

Daily travel limits:
- Max 5 hours total per day
- Should be ≤ 20% of waking hours (8am-10pm = 14 hours)

Example:
Day 3: 7-hour travel from Goa to Dudhsagar ❌ TOO MUCH
Fix: Make it full-day activity, not combined with other activities
```

**Tool:** `check_excessive_travel`

---

### 6. **Preference Alignment** 🎯
Verifies itinerary matches user's stated preferences.

```
User said: "I want beach + culture + shopping"
Itinerary has:
  ✓ Baga Beach (beach)
  ✓ Mangeshi Temple (culture)
  ✓ Anjuna Market (shopping)
  ✓ Spice Market (shopping)
  → ALIGNED

User said: "No nightlife, family-friendly only"
Itinerary includes:
  ✓ No clubs, bars, or adult venues
  ✓ All activities have kids' amenities
  → ALIGNED

User said: "Beach + culture + shopping + nightlife"
Itinerary missing:
  ❌ No nightlife venues included
  → NOT ALIGNED - Revise needed
```

**Tool:** `check_preference_alignment`

---

### 7. **Specialist Recommendation Coverage** 👥
Ensures Yojana didn't ignore specialist recommendations.

```
Yatra recommended 6 attractions:
  1. Baga Beach
  2. Dudhsagar Waterfall
  3. Fort Aguada
  4. Anjuna Market
  5. Mangeshi Temple
  6. Dolphin Tour

Itinerary includes:
  ✓ Baga Beach (Day 1, Day 2)
  ✓ Dudhsagar (Day 3)
  ✓ Fort Aguada (Day 4)
  ✓ Anjuna Market (Day 4)
  ✓ Mangeshi Temple (Day 2)
  ❌ Dolphin Tour (missing!)

Coverage: 5/6 = 83% ✓ GOOD (≥60%)

Cutoff: If coverage <60%, Parikshak flags as revision needed
```

**Tool:** `check_specialist_coverage`

---

## Parikshak's Output Levels

### ✅ APPROVED FOR USER REVIEW
All checks pass. Plan is ready.

```
✅ APPROVED FOR USER REVIEW

Summary:
- No scheduling conflicts (0/7 checks flagged)
- Balanced pace (4-6 hours/day for family)
- Meal timings realistic (7am, 12:30pm, 7:30pm)
- Travel reasonable (max 1.5 hours per segment)
- All user preferences matched (beach ✓ culture ✓ shopping ✓)
- Specialist coverage excellent (83% attractions included)

Status: Ready for user approval
Next: Send to user for review/feedback
```

### ❌ REVISION REQUIRED
Critical issues found. Send back to Yojana.

```
❌ REVISION REQUIRED

Critical Issues:
1. SCHEDULING CONFLICT (Day 1, 17:00-20:00)
   - Beach activity (3pm-5pm) overlaps with Waterfall trip (4pm-8pm)
   - Travel time: 1.5 hours each way = impossible
   → Fix: Move waterfall to Day 3 (full day)

2. BUDGET EXCEEDED
   - Plan total: ₹35,500
   - User budget: ₹25,000
   - Over by: ₹10,500
   → Fix: Downgrade hotel (₹6000→₹3000/night saves ₹15,000)

3. PACE TOO RUSHED (Day 2)
   - Family with kids: 11 hours activities
   - Recommended max: 6 hours
   - Activities: 6 (recommend max 4)
   → Fix: Spread attractions across Days 2-3

Changes needed: 3 critical fixes
Next: Return to Yojana with specific feedback
```

### ⚠️ CONDITIONAL APPROVAL
Non-critical warnings. User can override if they choose.

```
⚠️ CONDITIONAL APPROVAL

Warnings (non-blocking):
1. Day 3 is light (2.5 hours activities)
   - Not critical - can be rest day
   - Recommendation: Add optional activity (Goa Museum 1hr)

2. One restaurant recommendation not used
   - Yatra suggested "Fisherman's Wharf" (premium)
   - Itinerary uses budget alternatives
   - Not critical - user's choice

3. One minor timing gap
   - Activity ends 2:30pm, next starts 3:30pm
   - Includes 30min break (acceptable)
   - Could optimize further

Status: Can send to user AS-IS with notes
Alternative: Yojana can revise to address warnings
User's call: Approve now or request refinement
```

---

## Parikshak in the Full System

### Data Flow

```
User Input
    ↓
Sanchalak (Orchestrator)
    ↓
Specialists (Atithi, Annapurna, Yatra, Safar, Bazaar)
    ↓
Shared State (Unified preferences, recommendations)
    ↓
Yojana (Synthesizer creates draft)
    ↓
Parikshak (Validator checks quality) ← NEW STEP
    ↓
├─→ ✅ APPROVED → User review
├─→ ❌ REVISION → Yojana revises
└─→ ⚠️ CONDITIONAL → User decides
    ↓
User Approves/Provides Feedback
    ↓
Final Itinerary
```

### Message Flow

```
Yojana:
"Here's draft itinerary for a 5-day Goa trip"

Parikshak (internally):
- Runs 7 validation checks
- Analyzes each day
- Cross-references preferences
- Counts specialist coverage
- Generates report

Parikshak → Yojana:
"❌ REVISION: Schedule conflicts on Day 1 (Beach 3-5pm 
overlaps Waterfall 4-8pm). Move Waterfall to Day 3.
Also: Budget over by ₹10k - suggest hotel downgrade."

Yojana (revises):
"Updated itinerary:
- Day 1: Beach only (3-5pm)
- Day 3: Full-day Waterfall
- Hotel: Changed to ₹3000/night
- New total: ₹25,500 (within budget)"

Parikshak (re-validates):
"✅ APPROVED: All conflicts resolved, budget met,
preferences matched, specialist coverage 85%"

User:
"Looks great! Approve this plan"

System:
"✅ Final Itinerary Locked"
```

---

## Parikshak's Limitations (By Design)

Parikshak does NOT:
- Search for options (that's specialists' job)
- Create itineraries (that's Yojana's job)
- Make subjective choices (likes/dislikes)
- Orchestrate agents (that's Sanchalak's job)

Parikshak ONLY:
- Validates against objective criteria
- Checks constraints (time, budget, distance)
- Verifies preference matching
- Ensures coverage of recommendations
- Returns pass/fail/conditional verdict

---

## Example Validation Scenario

### Input: Draft Itinerary (Day 1 only)

```json
{
  "day": 1,
  "activities": [
    {
      "name": "Flight Delhi-Goa",
      "start_time": "08:00",
      "end_time": "10:30",
      "travel_time_hours": 2.5
    },
    {
      "name": "Hotel Check-in",
      "start_time": "11:00",
      "end_time": "12:00"
    },
    {
      "name": "Lunch",
      "start_time": "12:00",
      "end_time": "13:00"
    },
    {
      "name": "Baga Beach",
      "start_time": "14:00",
      "end_time": "17:00",
      "travel_time_hours": 0.25
    },
    {
      "name": "Dudhsagar Waterfall",
      "start_time": "16:00",
      "end_time": "20:00",
      "travel_time_hours": 1.5
    },
    {
      "name": "Dinner",
      "start_time": "20:30",
      "end_time": "21:30"
    }
  ]
}
```

### Parikshak's Analysis

```
CHECK 1: Scheduling Conflicts
❌ FAIL - Baga Beach (2pm-5pm) overlaps Waterfall (4pm-8pm)
   Gap between end (5pm) and next start (4pm) = -1 hour
   CONFLICT: Can't be in two places at 4pm-5pm

CHECK 2: Duplicate Attractions
✓ PASS - Each attraction unique

CHECK 3: Pace Analysis
❌ FAIL - For family with kids on travel day:
   Activity hours: 6 (Flight 2.5h + Beach 3h + Waterfall 4h)
   Kids get off plane 10:30am → Dinner 9:30pm
   Total awake: 11 hours, 6+ hours activities
   Max recommended: 4 hours (travel day fatigue)

CHECK 4: Meal Gaps
⚠️ WARNING - Lunch at 12pm, Dinner at 8:30pm = 8.5 hour gap
   Recommendation: Add snack at 4pm with activities

CHECK 5: Excessive Travel
❌ FAIL - Waterfall is 1.5 hours away
   Already at Beach (45min from hotel)
   Travel: Hotel→Beach→Waterfall→Hotel = 3+ hours
   + 4 hours activity = 7 hours total
   Too much for arrival day

CHECK 6: Preference Alignment
User wants: "Beach + Culture + Shopping + Family-friendly"
Day 1 has: Beach ✓, nothing else ✗
Cannot judge preference alignment on Day 1 alone

CHECK 7: Specialist Coverage
Yatra recommended: Beach ✓, Waterfall ✓ (both present)
Coverage so far: 2/6 = 33% (need to see full itinerary)
```

### Parikshak's Verdict

```
❌ REVISION REQUIRED

Critical Issues:
1. SCHEDULING CONFLICT
   Baga Beach (2-5pm) overlaps Dudhsagar (4-8pm)
   IMPOSSIBLE: Can't do both same day
   FIX: Move Dudhsagar to different day (full-day trip)

2. EXCESSIVE TRAVEL + PACE TOO RUSHED
   Total on arrival day: Flight + Beach + Waterfall
   Total activity: 6+ hours after long flight
   Family with kids needs rest
   FIX: Keep Day 1 light - Beach only
   FIX: Waterfall as full-day separate trip (Day 3 or 4)

3. MEAL GAP TOO LONG
   Lunch 12pm → Dinner 8:30pm = 8.5 hours
   FIX: Add afternoon snack break

Recommendation:
Day 1 Should Be:
  ✓ Flight (rest time)
  ✓ Hotel check-in (settle)
  ✓ Light lunch
  ✓ Rest (kids need sleep after travel)
  ✓ Evening beach walk ONLY (30 min, no activity)
  ✓ Early dinner (7pm)

Send back to Yojana for revision
```

---

## Integration Points

### With Yojana
```python
# Yojana creates draft
draft = yojana.create_itinerary(specialist_outputs)

# Parikshak validates
validation = parikshak.validate_itinerary(draft, user_preferences)

if "APPROVED" in validation:
    return draft_to_user(draft)
elif "REVISION" in validation:
    feedback = parikshak.extract_feedback(validation)
    revised = yojana.revise_itinerary(feedback)
    return parikshak.validate_itinerary(revised, user_preferences)
else:  # CONDITIONAL
    return draft_with_notes(draft, validation)
```

### With Shared State
```python
# Parikshak reads from shared state
state = get_state_manager()
preferences = state.preferences  # User preferences
recommendations = state.recommendations  # All specialists' outputs

# Parikshak updates shared state with validation results
state.update({
    "validation_status": "APPROVED",
    "validation_issues": [],
    "ready_for_user": True
})
```

---

## File Structure

```
agents/
  ├── parikshak_agent.py          # Main reviewer agent
  └── ...

tools/
  ├── validation_tools.py         # 7 validation tools
  └── ...

demo_parikshak_validation.py       # Usage examples
```

---

## Next Steps

1. **Integrate into Yojana workflow**
   - After Yojana.create_itinerary() → Parikshak.validate()
   
2. **Add to Sanchalak orchestration**
   - Sanchalak routes to Parikshak after Yojana
   
3. **Frontend integration**
   - Show validation status to user
   - "Checking quality... ✓"
   - Display any warnings or revision reasons
   
4. **Revision loop**
   - If Parikshak finds issues, automatically send to Yojana
   - Max 2-3 revision cycles before escalating to user

---

## Summary

**Parikshak = Quality Assurance for AI Travel Plans**

- Validates objectively (no opinions)
- Catches issues before user sees them
- Provides specific revision guidance
- Enables Yojana to improve automatically
- Protects user from broken itineraries
- Makes the entire system more trustworthy

---

## Quick Reference

| Check | Tool | Pass/Fail | Action |
|-------|------|-----------|--------|
| Conflicts | `check_scheduling_conflicts` | FAIL→Revise | Fix overlaps |
| Duplicates | `check_duplicate_attractions` | FAIL→Revise | Remove/consolidate |
| Pace | `analyze_pace` | FAIL→Revise | Rebalance days |
| Meals | `check_meal_gaps` | WARN→OK | Add snacks |
| Travel | `check_excessive_travel` | FAIL→Revise | Separate activities |
| Prefs | `check_preference_alignment` | FAIL→Revise | Add missing categories |
| Coverage | `check_specialist_coverage` | FAIL→Revise | Include recommendations |

**Result: ✅ APPROVED → ❌ REVISION NEEDED → ⚠️ CONDITIONAL**

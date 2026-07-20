"""
Complete End-to-End Demo: Full TRAVAS-AI System Flow

Shows entire journey from user query to final approved itinerary:
1. User provides trip details
2. Sanchalak orchestrates specialists
3. Specialists gather information (multi-turn)
4. Yojana synthesizes into draft itinerary
5. Parikshak validates quality
6. User provides feedback (revisions)
7. System updates and re-validates
8. Final approval and booking ready
"""

import json
from datetime import datetime
from agents.feedback_handler import FeedbackHandler
from utils.logger import get_logger

logger = get_logger(__name__)


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}".center(80))
    print("=" * 80 + "\n")


def print_step(step_num, title, emoji=""):
    """Print formatted step"""
    print(f"\n{emoji} STEP {step_num}: {title}")
    print("-" * 80)


def print_message(role, content, metadata=""):
    """Print formatted message"""
    role_emoji = {
        "user": "👤",
        "assistant": "🤖",
        "specialist": "👨‍⚕️",
        "yojana": "📋",
        "parikshak": "🔍",
        "system": "⚙️"
    }.get(role, "→")

    print(f"\n{role_emoji} {role.upper()}:")
    if isinstance(content, dict):
        print(json.dumps(content, indent=2))
    else:
        print(f"  {content}")
    if metadata:
        print(f"  [{metadata}]")


def demo_end_to_end():
    """Complete end-to-end demo"""

    print_section("TRAVAS-AI: COMPLETE END-TO-END DEMO")
    print("From user query → Final approved itinerary\n")

    # ========================================================================
    # STEP 1: USER PROVIDES TRIP DETAILS
    # ========================================================================

    print_step(1, "User Initiates Travel Query", "📝")

    user_query = """
    I'm planning a family trip to Goa for 5 days.
    - 2 adults + 2 kids (ages 6 and 9)
    - Budget: ₹25,000 total
    - We want: beaches, culture, good food, and family-friendly activities
    - Travel dates: July 25-30, 2026
    - First time in Goa
    """

    print_message("user", user_query)

    # ========================================================================
    # STEP 2: SANCHALAK RECEIVES AND ROUTES
    # ========================================================================

    print_step(2, "Sanchalak (Orchestrator) Routes to Specialists", "🎭")

    print_message("system", "Sanchalak analyzing user intent...")

    routing_decision = {
        "intent": "Comprehensive trip planning",
        "destination": "Goa",
        "specialists_needed": [
            "Atithi (Hotels)",
            "Annapurna (Food/Restaurants)",
            "Yatra (Attractions/Tours)",
            "Safar (Transport)",
            "Bazaar (Shopping)"
        ],
        "shared_preferences": {
            "destination": "Goa",
            "duration_days": 5,
            "num_adults": 2,
            "num_children": 2,
            "budget_total": 25000,
            "checkin_date": "2026-07-25",
            "checkout_date": "2026-07-30",
            "travel_style": "family-friendly",
            "interests": ["beaches", "culture", "food", "activities"]
        }
    }

    print_message("system", routing_decision, "Shared state updated")

    # ========================================================================
    # STEP 3: SPECIALISTS GATHER INFORMATION
    # ========================================================================

    print_step(3, "Specialists Search and Recommend", "👨‍⚕️")

    specialist_outputs = {
        "atithi": {
            "hotels": 3,
            "recommendations": [
                "Spice Garden Resort (₹5,500/night, family room, kids' club)",
                "Beachfront Paradise (₹6,000/night, ocean view)",
                "Budget Family Stay (₹3,000/night, pool)"
            ],
            "best_choice": "Spice Garden Resort"
        },
        "annapurna": {
            "restaurants": 6,
            "recommendations": [
                "Fisherman's Wharf (premium, seafood)",
                "Spice Garden (casual Indian)",
                "Beach Shack (budget friendly)",
                "Goan Vegetarian (kids menu)"
            ],
            "family_friendly_options": 4
        },
        "yatra": {
            "attractions": 6,
            "recommendations": [
                "Baga Beach (water sports, family)",
                "Dudhsagar Waterfall (adventure, full-day)",
                "Fort Aguada (sunset, historical)",
                "Anjuna Market (shopping, cultural)",
                "Mangeshi Temple (cultural)",
                "Dolphin Tour (kids-friendly)"
            ],
            "kid_friendly": 5
        },
        "safar": {
            "transport": {
                "flights": "IndiGo Delhi-Goa ₹2,500/person",
                "local": "Car rental ₹800/day OR taxis ₹200-300"
            },
            "hotel_coordination": "Arranged for hotel on arrival"
        },
        "bazaar": {
            "shopping": {
                "spice_markets": "Anjuna Spice Market (morning)",
                "handicrafts": "Goa Handicraft Emporium",
                "souvenirs": "Various shops, recommended budget ₹1,000-2,000"
            }
        }
    }

    for specialist, output in specialist_outputs.items():
        print_message("specialist", output, f"{specialist.upper()} recommendations")

    # ========================================================================
    # STEP 4: YOJANA SYNTHESIZES INTO DRAFT ITINERARY
    # ========================================================================

    print_step(4, "Yojana Creates Draft Itinerary", "📋")

    print_message("system", "Yojana synthesizing specialist recommendations...")

    draft_itinerary = {
        "destination": "Goa",
        "duration": "5 days",
        "travelers": "Family: 2 adults, 2 kids (6, 9)",
        "total_budget": "₹25,000 (EXCEEDS by ₹2,500)",
        "days": [
            {
                "day": 1,
                "date": "2026-07-25",
                "activities": [
                    "Flight Delhi-Goa (2.5 hrs) → Hotel check-in",
                    "Rest & settle (kids tired from travel)",
                    "Evening beach walk (30 mins)",
                    "Dinner at nearby restaurant"
                ]
            },
            {
                "day": 2,
                "date": "2026-07-26",
                "activities": [
                    "Baga Beach (9am-12pm, water sports)",
                    "Lunch at Beach Shack",
                    "Rest at hotel (2-4pm)",
                    "Mangeshi Temple visit (4-5:30pm)",
                    "Dinner at Spice Garden"
                ]
            },
            {
                "day": 3,
                "date": "2026-07-27",
                "activities": [
                    "Full-day: Dudhsagar Waterfall (45km away)",
                    "Private car rental + guide",
                    "Swimming, photography, picnic lunch",
                    "Return by evening"
                ]
            },
            {
                "day": 4,
                "date": "2026-07-28",
                "activities": [
                    "Rest day at hotel (kids recover)",
                    "Morning: Anjuna Spice Market shopping (2 hrs)",
                    "Afternoon: Fort Aguada sunset visit",
                    "Evening: Premium dinner (celebration)"
                ]
            },
            {
                "day": 5,
                "date": "2026-07-30",
                "activities": [
                    "Last beach time (morning)",
                    "Hotel checkout (11am)",
                    "Light lunch",
                    "Taxi to airport",
                    "Flight Goa-Delhi (4pm departure)"
                ]
            }
        ],
        "cost_breakdown": {
            "flights": "₹5,000 (2 adults: 2.5k x 2)",
            "hotel": "₹27,500 (5 nights @ ₹5.5k)",
            "meals": "₹6,000 (₹300/person/day mix)",
            "transport": "₹2,500 (car rental, local taxis)",
            "activities": "₹2,000 (waterfall, tours)",
            "shopping": "₹1,000",
            "total": "₹44,000"
        },
        "budget_alert": "OVER BUDGET: ₹44,000 > ₹25,000 (Exceed by ₹19,000)"
    }

    print_message("yojana", draft_itinerary, "DRAFT - Awaiting validation")

    # ========================================================================
    # STEP 5: PARIKSHAK VALIDATES QUALITY
    # ========================================================================

    print_step(5, "Parikshak Performs Quality Checks", "🔍")

    print_message("system", "Running 7 validation checks...")

    validation_results = {
        "check_1_scheduling_conflicts": "✅ PASS - No time overlaps",
        "check_2_duplicate_attractions": "✅ PASS - Each attraction unique",
        "check_3_pace_analysis": "✅ PASS - Balanced for family (4-6 hrs/day)",
        "check_4_meal_gaps": "✅ PASS - Realistic meal timings (7am, 12:30pm, 7pm)",
        "check_5_excessive_travel": "✅ PASS - Max segment 1.5 hrs",
        "check_6_preference_alignment": "✅ PASS - Beach ✓ Culture ✓ Food ✓ Shopping ✓",
        "check_7_specialist_coverage": "✅ PASS - 83% attractions included",
        "critical_issue": "❌ BUDGET EXCEEDED - ₹44k vs ₹25k budget",
        "verdict": "⚠️ CONDITIONAL APPROVAL"
    }

    print_message("parikshak", validation_results)

    print_message("system", """
    Parikshak Verdict: ⚠️ CONDITIONAL APPROVAL

    Issue: Budget exceeds user's ₹25,000 by ₹19,000
    Options for user:
    1. APPROVE with higher budget (₹44,000)
    2. REVISE: Downgrade hotel to save money
    3. REJECT: Start fresh with different preferences
    4. CLARIFY: Ask about budget flexibility
    """)

    # ========================================================================
    # STEP 6: USER FEEDBACK - FIRST ROUND
    # ========================================================================

    print_step(6, "User Provides Feedback (Round 1)", "💬")

    feedback_handler = FeedbackHandler()

    user_feedback_1 = "The budget is flexible - we can do ₹45,000. But can we skip the temple and add a kids' activity instead?"

    print_message("user", user_feedback_1)

    # Process feedback
    action_1, details_1 = feedback_handler.process_user_feedback(
        user_feedback_1,
        draft_itinerary
    )

    print_message("system", {
        "action": action_1,
        "message": details_1["message"],
        "revision_number": details_1.get("revision_number"),
        "approval_state": details_1["approval_state"]
    })

    # ========================================================================
    # STEP 7: YOJANA REVISES
    # ========================================================================

    print_step(7, "Yojana Revises Based on Feedback", "🔄")

    print_message("system", "Yojana processing revisions:")

    revised_itinerary = {
        **draft_itinerary,
        "total_budget": "₹45,000 (Updated)",
        "days": [
            # Day 1 unchanged
            draft_itinerary["days"][0],
            # Day 2: Replaced temple with kids activity
            {
                **draft_itinerary["days"][1],
                "activities": [
                    "Baga Beach (9am-12pm, water sports)",
                    "Lunch at Beach Shack",
                    "Rest at hotel (2-4pm)",
                    "Dolphin Tour (4-6pm) - Kids love this!",
                    "Dinner at Spice Garden"
                ]
            },
            # Day 3-5 unchanged
            draft_itinerary["days"][2],
            draft_itinerary["days"][3],
            draft_itinerary["days"][4]
        ],
        "changes_made": [
            "Budget increased to ₹45,000",
            "Removed: Mangeshi Temple",
            "Added: Dolphin Tour (Day 2, kids' activity)"
        ]
    }

    print_message("yojana", {
        "status": "Revised",
        "changes": revised_itinerary["changes_made"],
        "budget": "₹45,000 (Updated)"
    })

    # ========================================================================
    # STEP 8: PARIKSHAK RE-VALIDATES
    # ========================================================================

    print_step(8, "Parikshak Re-validates Revised Itinerary", "🔍")

    revised_validation = {
        "scheduling": "✅ PASS",
        "duplicates": "✅ PASS",
        "pace": "✅ PASS",
        "meals": "✅ PASS",
        "travel": "✅ PASS",
        "preferences": "✅ PASS (Beach ✓ Kids activity ✓ Shopping ✓)",
        "specialist_coverage": "✅ PASS - 85%",
        "budget": "✅ PASS - ₹45,000 matches new budget",
        "verdict": "✅ APPROVED FOR USER REVIEW"
    }

    print_message("parikshak", revised_validation)

    # ========================================================================
    # STEP 9: USER FEEDBACK - FINAL APPROVAL
    # ========================================================================

    print_step(9, "User Provides Final Feedback", "💬")

    user_feedback_2 = "Perfect! This is exactly what I wanted. I approve this itinerary."

    print_message("user", user_feedback_2)

    action_2, details_2 = feedback_handler.process_user_feedback(
        user_feedback_2,
        revised_itinerary
    )

    print_message("system", {
        "action": action_2,
        "message": details_2["message"],
        "next_step": details_2["next_step"],
        "approval_state": details_2["approval_state"]
    })

    # ========================================================================
    # STEP 10: FINALIZE ITINERARY
    # ========================================================================

    print_step(10, "Finalize Approved Itinerary", "✅")

    final_itinerary = feedback_handler.finalize_itinerary(revised_itinerary)

    print_message("system", {
        "status": "FINALIZED",
        "approval_timestamp": final_itinerary.get("approval_timestamp"),
        "revision_count": final_itinerary["approval_metadata"]["revision_count"],
        "feedback_rounds": final_itinerary["approval_metadata"]["feedback_rounds"]
    })

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print_section("JOURNEY COMPLETE ✅")

    summary = {
        "user_query": "5-day family trip to Goa",
        "destination": "Goa, India",
        "duration": "5 days (July 25-30, 2026)",
        "travelers": "2 adults + 2 kids (6, 9)",
        "final_budget": "₹45,000",
        "itinerary_status": "✅ APPROVED & FINALIZED",
        "revision_rounds": 1,
        "time_to_approval": "Multi-turn conversation",
        "ready_for_booking": "Yes"
    }

    print(json.dumps(summary, indent=2))

    print("\n" + "="*80)
    print("NEXT STEPS FOR USER:".center(80))
    print("="*80)
    print("""
    ✅ Itinerary locked and ready

    User can now:
    1. Download itinerary PDF
    2. Book hotels (Spice Garden Resort)
    3. Book flights (IndiGo)
    4. Reserve rental car
    5. Book restaurant tables
    6. Pre-book dolphin tour

    Support available 24/7 for any changes before travel date.
    """)

    print("\n" + "="*80)
    print("END-TO-END FLOW COMPLETE".center(80))
    print("="*80 + "\n")


if __name__ == "__main__":
    demo_end_to_end()

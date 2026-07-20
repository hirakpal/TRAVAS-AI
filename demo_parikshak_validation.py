"""Demo: Parikshak Quality Review & Validation"""

import os
import json
from dotenv import load_dotenv

from agents.parikshak_agent import ParikshakAgent
from agents.shared_state import initialize_state_manager, get_state_manager
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


def demo_validate_good_itinerary():
    """Demo showing Parikshak approving a well-structured itinerary."""
    print("\n" + "PARIKSHAK - QUALITY REVIEWER DEMO (Good Itinerary)".center(70))
    print("="*70 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    state_manager = initialize_state_manager(session_id="demo-parikshak-good")

    # Good itinerary - well paced, no conflicts
    good_itinerary = {
        "destination": "Goa",
        "duration_days": 5,
        "travelers": "Family (2 adults, 2 kids 6-9)",
        "days": [
            {
                "day_number": 1,
                "activities": [
                    {"name": "Flight Delhi-Goa", "type": "transport", "start_time": "08:00", "end_time": "10:30", "travel_time_hours": 2.5},
                    {"name": "Hotel check-in", "type": "accommodation", "start_time": "11:00", "end_time": "12:00"},
                    {"name": "Lunch", "type": "meal", "start_time": "12:30", "end_time": "13:30", "time": "12:30"},
                    {"name": "Rest & settle", "type": "rest", "start_time": "14:00", "end_time": "17:00"},
                    {"name": "Baga Beach", "type": "attraction", "start_time": "17:00", "end_time": "19:00", "travel_time_hours": 0.25},
                    {"name": "Dinner", "type": "meal", "start_time": "19:30", "end_time": "20:30", "time": "19:30"}
                ],
                "total_activity_hours": 4
            },
            {
                "day_number": 2,
                "activities": [
                    {"name": "Breakfast", "type": "meal", "start_time": "08:00", "end_time": "09:00", "time": "08:00"},
                    {"name": "Baga Beach", "type": "attraction", "start_time": "09:00", "end_time": "12:00", "travel_time_hours": 0.25},
                    {"name": "Lunch", "type": "meal", "start_time": "12:30", "end_time": "13:30", "time": "12:30"},
                    {"name": "Rest at hotel", "type": "rest", "start_time": "14:00", "end_time": "16:00"},
                    {"name": "Mangeshi Temple", "type": "attraction", "start_time": "16:00", "end_time": "17:30", "travel_time_hours": 0.33},
                    {"name": "Dinner", "type": "meal", "start_time": "19:00", "end_time": "20:00", "time": "19:00"}
                ],
                "total_activity_hours": 5.5
            },
            {
                "day_number": 3,
                "activities": [
                    {"name": "Breakfast", "type": "meal", "start_time": "07:00", "end_time": "08:00", "time": "07:00"},
                    {"name": "Dudhsagar Waterfall", "type": "attraction", "start_time": "09:00", "end_time": "14:00", "travel_time_hours": 1.5},
                    {"name": "Picnic lunch", "type": "meal", "start_time": "12:00", "end_time": "13:00", "time": "12:00"},
                    {"name": "Return to hotel", "type": "transport", "start_time": "14:00", "end_time": "16:00", "travel_time_hours": 1.5},
                    {"name": "Rest (tired from adventure)", "type": "rest", "start_time": "16:00", "end_time": "19:00"},
                    {"name": "Light dinner", "type": "meal", "start_time": "19:00", "end_time": "20:00", "time": "19:00"}
                ],
                "total_activity_hours": 6
            },
            {
                "day_number": 4,
                "activities": [
                    {"name": "Breakfast", "type": "meal", "start_time": "08:00", "end_time": "09:00", "time": "08:00"},
                    {"name": "Rest day at hotel", "type": "rest", "start_time": "09:00", "end_time": "12:00"},
                    {"name": "Lunch", "type": "meal", "start_time": "12:30", "end_time": "13:30", "time": "12:30"},
                    {"name": "Anjuna Spice Market", "type": "shopping", "start_time": "15:00", "end_time": "17:00", "travel_time_hours": 0.5},
                    {"name": "Fort Aguada sunset", "type": "attraction", "start_time": "17:30", "end_time": "18:30", "travel_time_hours": 0.33},
                    {"name": "Premium dinner", "type": "meal", "start_time": "19:30", "end_time": "21:00", "time": "19:30"}
                ],
                "total_activity_hours": 4.5
            },
            {
                "day_number": 5,
                "activities": [
                    {"name": "Breakfast", "type": "meal", "start_time": "08:00", "end_time": "09:00", "time": "08:00"},
                    {"name": "Final beach time", "type": "attraction", "start_time": "09:00", "end_time": "11:00", "travel_time_hours": 0.25},
                    {"name": "Hotel checkout", "type": "accommodation", "start_time": "11:00", "end_time": "11:30"},
                    {"name": "Light lunch", "type": "meal", "start_time": "12:00", "end_time": "13:00", "time": "12:00"},
                    {"name": "Taxi to airport", "type": "transport", "start_time": "14:00", "end_time": "14:45", "travel_time_hours": 0.75},
                    {"name": "Flight Goa-Delhi", "type": "transport", "start_time": "16:00", "end_time": "18:30", "travel_time_hours": 2.5}
                ],
                "total_activity_hours": 3.5
            }
        ],
        "total_cost": 27500,
        "budget": 30000
    }

    user_preferences = {
        "beach_activities": True,
        "cultural_activities": True,
        "shopping": True,
        "family_friendly": True,
        "dining": "casual_to_premium",
        "activity_level": "moderate"
    }

    agent = ParikshakAgent(api_key=api_key)
    print("Initializing Parikshak (Quality Reviewer)...\n")

    print("Validating GOOD itinerary (well-paced, no conflicts)...\n")
    validation_result = agent.validate_itinerary(
        json.dumps(good_itinerary),
        user_preferences
    )

    print("VALIDATION RESULT:")
    print("-" * 70)
    print(validation_result)
    print("-" * 70 + "\n")


def demo_validate_problematic_itinerary():
    """Demo showing Parikshak catching issues in a problematic itinerary."""
    print("\n" + "PARIKSHAK - QUALITY REVIEWER DEMO (Problematic Itinerary)".center(70))
    print("="*70 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    state_manager = initialize_state_manager(session_id="demo-parikshak-bad")

    # Bad itinerary - conflicts, too rushed, duplicate attractions
    bad_itinerary = {
        "destination": "Goa",
        "duration_days": 3,
        "travelers": "Family (2 adults, 2 kids 6-9)",
        "days": [
            {
                "day_number": 1,
                "activities": [
                    {"name": "Flight Delhi-Goa", "type": "transport", "start_time": "08:00", "end_time": "10:30"},
                    {"name": "Hotel check-in", "type": "accommodation", "start_time": "11:00", "end_time": "12:00"},
                    {"name": "Baga Beach", "type": "attraction", "start_time": "12:00", "end_time": "14:00", "travel_time_hours": 0.25},
                    {"name": "Dudhsagar Waterfall", "type": "attraction", "start_time": "13:30", "end_time": "17:00", "travel_time_hours": 1.5},  # OVERLAP with beach!
                    {"name": "Fort Aguada", "type": "attraction", "start_time": "17:00", "end_time": "19:00", "travel_time_hours": 0.5},
                    {"name": "Dinner", "type": "meal", "start_time": "19:00", "end_time": "20:00"}
                ],
                "total_activity_hours": 9  # Too much for kids on travel day!
            },
            {
                "day_number": 2,
                "activities": [
                    {"name": "Breakfast", "type": "meal", "start_time": "08:00", "end_time": "09:00"},
                    {"name": "Baga Beach", "type": "attraction", "start_time": "09:00", "end_time": "11:00"},  # DUPLICATE
                    {"name": "Spice Market", "type": "shopping", "start_time": "11:00", "end_time": "14:00", "travel_time_hours": 0.5},
                    {"name": "Fort Aguada", "type": "attraction", "start_time": "14:00", "end_time": "16:00"},  # DUPLICATE
                    {"name": "Mangeshi Temple", "type": "attraction", "start_time": "16:00", "end_time": "18:00", "travel_time_hours": 0.5},
                    {"name": "Anjuna Market", "type": "shopping", "start_time": "18:00", "end_time": "20:00"}
                ],
                "total_activity_hours": 11  # Way too much!
            },
            {
                "day_number": 3,
                "activities": [
                    {"name": "Breakfast", "type": "meal", "start_time": "08:00", "end_time": "09:00"},
                    {"name": "Flight Goa-Delhi", "type": "transport", "start_time": "10:00", "end_time": "12:30", "travel_time_hours": 2.5},
                    {"name": "Lunch", "type": "meal", "start_time": "13:00", "end_time": "14:00"}
                ],
                "total_activity_hours": 1.5  # Nothing to do!
            }
        ],
        "total_cost": 35000,
        "budget": 25000  # OVER BUDGET
    }

    user_preferences = {
        "beach_activities": True,
        "cultural_activities": True,
        "shopping": True,
        "family_friendly": True,
        "dining": "casual",
        "activity_level": "moderate"
    }

    agent = ParikshakAgent(api_key=api_key)
    print("Validating PROBLEMATIC itinerary (has multiple issues)...\n")

    validation_result = agent.validate_itinerary(
        json.dumps(bad_itinerary),
        user_preferences
    )

    print("VALIDATION RESULT:")
    print("-" * 70)
    print(validation_result)
    print("-" * 70 + "\n")


def main():
    """Run demos."""
    print("\n" + "PARIKSHAK - TRAVEL PLAN REVIEWER".center(70))
    print("="*70)
    print("\nParikshak is the quality gate between Yojana and the user.")
    print("Parikshak validates itineraries for:")
    print("  ✓ Scheduling conflicts")
    print("  ✓ Duplicate attractions")
    print("  ✓ Pace analysis (too rushed or too lazy)")
    print("  ✓ Meal gaps (realistic timings)")
    print("  ✓ Excessive travel (distances, times)")
    print("  ✓ User preference alignment")
    print("  ✓ Specialist recommendation coverage")
    print("\nOutput:")
    print("  ✅ APPROVED - Ready for user")
    print("  ❌ REVISION REQUIRED - Send back to Yojana")
    print("  ⚠️ CONDITIONAL - User can override\n")

    demo_validate_good_itinerary()
    demo_validate_problematic_itinerary()

    print("="*70)
    print("✅ Demo completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

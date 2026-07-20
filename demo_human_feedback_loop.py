"""Demo: Human-in-the-Loop Feedback System"""

import json
from agents.feedback_handler import FeedbackHandler, ItineraryApprovalState
from utils.logger import get_logger

logger = get_logger(__name__)


def demo_scenario_1_user_approves():
    """Scenario 1: User approves itinerary immediately"""
    print("\n" + "SCENARIO 1: USER APPROVES ITINERARY".center(70))
    print("="*70 + "\n")

    handler = FeedbackHandler()

    # Mock itinerary
    mock_itinerary = {
        "destination": "Goa",
        "duration": "5 days",
        "cost": "₹27,500",
        "status": "APPROVED by Parikshak"
    }

    print("System: Here's your approved itinerary:")
    print(json.dumps(mock_itinerary, indent=2))
    print("\n" + "-"*70)

    # User approves
    user_message = "Yes, this looks perfect! I approve this plan."
    print(f"\n👤 User: \"{user_message}\"\n")

    action, details = handler.process_user_feedback(user_message, mock_itinerary)

    print(f"Intent: {action}")
    print(f"Status: {details['status']}")
    print(f"Message: {details['message']}")
    print(f"Next Step: {details['next_step']}")
    print(f"\nApproval State: {json.dumps(details['approval_state'], indent=2)}")

    # Finalize
    final = handler.finalize_itinerary(mock_itinerary)
    print(f"\n✅ FINALIZED ITINERARY:")
    print(f"   Approval Status: {final.get('approval_status')}")
    print(f"   Approved at: {final.get('approval_timestamp')}")
    print(f"   Revisions needed: {final['approval_metadata']['revision_count']}")
    print()


def demo_scenario_2_user_requests_revision():
    """Scenario 2: User requests changes"""
    print("\n" + "SCENARIO 2: USER REQUESTS REVISION".center(70))
    print("="*70 + "\n")

    handler = FeedbackHandler()

    mock_itinerary = {
        "destination": "Goa",
        "duration": "5 days",
        "day_1": "Flight + Beach",
        "day_2": "Beach + Temple",
        "day_3": "Dudhsagar Waterfall",
        "day_4": "Fort Aguada + Shopping",
        "day_5": "Return flight",
        "cost": "₹27,500"
    }

    print("System: Here's your itinerary (✅ APPROVED by Parikshak):")
    print(json.dumps(mock_itinerary, indent=2))
    print("\n" + "-"*70)

    # Revision 1
    user_message = "Can you add more beach time? I want 2 full beach days instead of 1."
    print(f"\n👤 User (Revision 1): \"{user_message}\"\n")

    action, details = handler.process_user_feedback(user_message, mock_itinerary)

    print(f"Intent: {action}")
    print(f"Status: {details['status']}")
    print(f"Message: {details['message']}")
    print(f"Next Step: {details['next_step']}")
    print(f"Revision #: {details.get('revision_number')}")
    print(f"\nApproval State: {json.dumps(details['approval_state'], indent=2)}")

    # Simulate Yojana revision + Parikshak validation
    revised_itinerary = {
        **mock_itinerary,
        "day_2": "Full Beach Day (more time)",
        "day_3": "Dudhsagar Waterfall",
        "day_4": "Beach sunset + Shopping",
        "notes": "Revised: More beach time added"
    }

    handler.update_itinerary_and_validation(revised_itinerary, "APPROVED")

    print(f"\n🔄 Yojana revised itinerary")
    print(f"🔍 Parikshak validated: ✅ APPROVED")
    print(f"\nRevised itinerary ready for user review")

    # Revision 2 - User makes another change
    print("\n" + "-"*70)
    user_message_2 = "Also, can you replace the temple with a shopping market instead?"
    print(f"\n👤 User (Revision 2): \"{user_message_2}\"\n")

    action2, details2 = handler.process_user_feedback(user_message_2, revised_itinerary)

    print(f"Intent: {action2}")
    print(f"Status: {details2['status']}")
    print(f"Message: {details2['message']}")
    print(f"Revision #: {details2.get('revision_number')}")
    print(f"\nApproval State: {json.dumps(details2['approval_state'], indent=2)}")

    # Second revision complete
    final_itinerary = {
        **revised_itinerary,
        "day_2": "Full Beach Day (more time)",
        "day_3": "Dudhsagar Waterfall",
        "day_4": "Anjuna Spice Market + Beach sunset",
        "notes": "Revised: More beach + Market instead of temple"
    }

    handler.update_itinerary_and_validation(final_itinerary, "APPROVED")

    print(f"\n🔄 Yojana revised again")
    print(f"🔍 Parikshak validated: ✅ APPROVED")

    # User approves final version
    print("\n" + "-"*70)
    user_message_3 = "Perfect! This is exactly what I wanted!"
    print(f"\n👤 User (Final): \"{user_message_3}\"\n")

    action3, details3 = handler.process_user_feedback(user_message_3, final_itinerary)

    print(f"Intent: {action3}")
    print(f"Status: {details3['status']}")
    print(f"Message: {details3['message']}")
    print(f"Next Step: {details3['next_step']}")
    print(f"\nApproval State: {json.dumps(details3['approval_state'], indent=2)}")

    final = handler.finalize_itinerary(final_itinerary)
    print(f"\n✅ FINALIZED ITINERARY:")
    print(f"   Revisions needed: {final['approval_metadata']['revision_count']}")
    print(f"   Feedback rounds: {final['approval_metadata']['user_feedback_summary']}")
    print()


def demo_scenario_3_user_rejects_and_restarts():
    """Scenario 3: User rejects and starts fresh"""
    print("\n" + "SCENARIO 3: USER REJECTS AND RESTARTS".center(70))
    print("="*70 + "\n")

    handler = FeedbackHandler()

    mock_itinerary = {
        "destination": "Goa",
        "duration": "5 days",
        "cost": "₹27,500",
        "status": "APPROVED by Parikshak"
    }

    print("System: Here's your itinerary:")
    print(json.dumps(mock_itinerary, indent=2))
    print("\n" + "-"*70)

    # User rejects
    user_message = "No, this doesn't work for us. We need something completely different."
    print(f"\n👤 User: \"{user_message}\"\n")

    action, details = handler.process_user_feedback(user_message)

    print(f"Intent: {action}")
    print(f"Status: {details['status']}")
    print(f"Message:\n{details['message']}")
    print(f"Next Step: {details['next_step']}")

    # User chooses to restart
    print("\n" + "-"*70)
    user_choice = "I want to start completely fresh with new preferences."
    print(f"\n👤 User: \"{user_choice}\"\n")

    action2, details2 = handler.handle_restart_decision(user_choice)

    print(f"Restart Decision: {action2}")
    print(f"Status: {details2['status']}")
    print(f"Message: {details2['message']}")
    print(f"Next Step: {details2['next_step']}")
    print(f"\nApproval State: {json.dumps(details2['approval_state'], indent=2)}")

    print(f"\n🔄 System will restart Sanchalak and ask for new preferences...")
    print()


def demo_scenario_4_max_revisions_reached():
    """Scenario 4: User exhausts revision limit"""
    print("\n" + "SCENARIO 4: MAX REVISIONS REACHED".center(70))
    print("="*70 + "\n")

    handler = FeedbackHandler()

    mock_itinerary = {"destination": "Goa", "duration": "5 days"}

    # Simulate 3 revisions already made
    for i in range(3):
        feedback = f"Can you change this? Revision {i+1}"
        action, details = handler.process_user_feedback(feedback, mock_itinerary)
        handler.update_itinerary_and_validation(mock_itinerary, "APPROVED")
        print(f"Revision {i+1}: {details['message']}")

    print("\n" + "-"*70)

    # 4th revision attempt
    user_message = "Actually, one more thing - can you change the hotel too?"
    print(f"\n👤 User (Revision 4): \"{user_message}\"\n")

    action, details = handler.process_user_feedback(user_message, mock_itinerary)

    print(f"Intent: {action}")
    print(f"Status: {details['status']}")
    print(f"Message: {details['message']}")
    print(f"Next Step: {details['next_step']}")

    print(f"\n⚠️ System cannot accept more revisions.")
    print(f"   Options: Contact support OR Start fresh with new preferences")
    print()


def demo_scenario_5_clarification():
    """Scenario 5: User asks clarification questions"""
    print("\n" + "SCENARIO 5: USER ASKS CLARIFICATION".center(70))
    print("="*70 + "\n")

    handler = FeedbackHandler()

    mock_itinerary = {
        "destination": "Goa",
        "day_3": "Dudhsagar Waterfall (Full day)",
        "transport": "Private car rental"
    }

    print("System: Here's your itinerary:")
    print(json.dumps(mock_itinerary, indent=2))
    print("\n" + "-"*70)

    # User asks question
    user_message = "How long is the drive to Dudhsagar? Will it be tiring for the kids?"
    print(f"\n👤 User: \"{user_message}\"\n")

    action, details = handler.process_user_feedback(user_message, mock_itinerary)

    print(f"Intent: {action}")
    print(f"Status: {details['status']}")
    print(f"Message: {details['message']}")
    print(f"Next Step: {details['next_step']}")
    print(f"Question: {details['question']}")

    # System answers
    print(f"\n💬 System Response:")
    print(f"   The drive to Dudhsagar is about 1.5 hours each way.")
    print(f"   That's why I scheduled a full day with rest stops.")
    print(f"   For kids aged 6-9: Bring snacks, entertainment, and plan")
    print(f"   for bathroom breaks. The waterfall is worth it!")
    print(f"\n   Does this address your concern? Should I adjust the plan?")
    print()


def main():
    """Run all feedback scenarios"""
    print("\n" + "HUMAN-IN-THE-LOOP FEEDBACK SYSTEM".center(70))
    print("="*70)
    print("\nDemonstrating how users interact with approved itineraries:")
    print("  1. Approval - User says 'yes, lock this'")
    print("  2. Revision - User requests changes (multi-turn)")
    print("  3. Rejection - User rejects (restart or modify?)")
    print("  4. Max revisions - Attempt limit reached")
    print("  5. Clarification - User asks questions\n")

    demo_scenario_1_user_approves()
    demo_scenario_2_user_requests_revision()
    demo_scenario_3_user_rejects_and_restarts()
    demo_scenario_4_max_revisions_reached()
    demo_scenario_5_clarification()

    print("="*70)
    print("✅ All feedback scenarios demonstrated!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

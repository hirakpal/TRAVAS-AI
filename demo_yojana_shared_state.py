"""Demo: Yojana Travel Plan Synthesizer"""

import os
from dotenv import load_dotenv

from agents.yojana_agent import YojanaAgent
from agents.shared_state import initialize_state_manager, get_state_manager
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


def demo_create_itinerary():
    """Demo showing Yojana creating complete travel itinerary."""
    print("\n" + "📅 YOJANA - TRAVEL PLAN SYNTHESIZER DEMO".center(70))
    print("="*70 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    state_manager = initialize_state_manager(session_id="demo-yojana")
    print(f"✅ Initialized shared state\n")

    # Pre-fill shared state with travel info
    state_manager.update_preferences({
        "destination": "Goa",
        "checkin_date": "2026-07-25",
        "checkout_date": "2026-07-30",
        "num_adults": 2,
        "num_children": 2,
        "budget": 20000,
    })

    agent = YojanaAgent(api_key=api_key)
    print(f"✅ Initialized Yojana Agent\n")

    # Simulate specialist recommendations
    specialist_outputs = {
        "atithi": "Hotel: Spice Garden Resort, Panjim. Check-in 2pm, Check-out 11am. ₹6000/night",
        "annapurna": "Restaurants: Fisherman's Wharf (premium), Spice Garden (casual), Beach Shack (budget)",
        "yatra": "Attractions: Baga Beach, Dudhsagar Waterfall, Fort Aguada, Anjuna Market, Mangeshi Temple",
        "safar": "Transport: Flights Delhi-Goa ₹2500, Local taxis ₹200-500, Car rental ₹800/day",
        "bazaar": "Shopping: Spice Market (morning), Goa Mall (mall), Handicraft Emporium (souvenirs)"
    }

    print("📝 Creating Draft Itinerary from Specialist Recommendations...\n")
    response = agent.create_itinerary(specialist_outputs)
    print(f"🗂️ Yojana:\n{response[:500]}...\n")

    state = state_manager.get_state()
    print(f"📊 Shared State:")
    print(f"   Active Agents: {', '.join(state['active_agents'])}")
    print(f"   Messages: {len(state['conversation_history'])}")
    print(f"   Status: DRAFT - Awaiting user approval\n")

    # Simulate user feedback
    print("="*70)
    print("\n👤 User Feedback: 'I want to add more beach time and skip the temple'\n")

    user_feedback = """
    Please update the itinerary:
    1. Add more beach time (love swimming)
    2. Skip the temple visit
    3. Add evening beach sunset viewing
    4. Keep 2 full rest days
    """

    print("📝 Revising Itinerary Based on Feedback...\n")
    revised = agent.revise_itinerary(user_feedback)
    print(f"🗂️ Yojana:\n{revised[:500]}...\n")

    print("="*70)
    print("✅ Demo completed!")
    print("="*70 + "\n")


def main():
    """Run demo."""
    print("\n" + "📅 YOJANA - TRAVEL PLAN SYNTHESIZER".center(70))
    print("="*70)
    print("\nYojana synthesizes specialist recommendations into complete travel plans.")
    print("It handles:")
    print("  ✓ Creating draft itineraries")
    print("  ✓ Validating feasibility")
    print("  ✓ Optimizing sequences")
    print("  ✓ Managing revisions")
    print("  ✓ Checking for conflicts\n")

    demo_create_itinerary()


if __name__ == "__main__":
    main()

"""Demo: Yatra Tours Agent with Shared State

Shows how Yatra integrates with shared state to recommend attractions and create itineraries
while coordinating with other agents.
"""

import os
from dotenv import load_dotenv

from agents.yatra_agent import YatraAgent
from agents.shared_state import initialize_state_manager, get_state_manager
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


def demo_yatra_with_shared_state():
    """Demo showing Yatra's integration with shared state."""
    print("\n" + "🗺️ YATRA WITH SHARED STATE - ATTRACTIONS DEMO".center(70))
    print("="*70 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    # Initialize shared state
    state_manager = initialize_state_manager(session_id="demo-yatra")
    print(f"✅ Initialized shared state manager\n")

    # Pre-fill some shared state (as if Atithi and Annapurna already set it)
    state_manager.update_preferences({
        "destination": "Goa",
        "checkin_date": "2026-07-25",
        "checkout_date": "2026-07-30",
        "num_adults": 2,
        "num_children": 2,
    })
    print(f"📝 Pre-filled shared state:")
    print(f"   Destination: Goa")
    print(f"   Dates: July 25-30, 2026 (5 days)")
    print(f"   Travelers: 2 adults, 2 children\n")

    # Create Yatra agent
    agent = YatraAgent(api_key=api_key)
    print(f"✅ Initialized Yatra Tours Agent\n")

    # Demo conversation sequence
    queries = [
        ("What attractions should we visit in Goa?", "Yatra gathers interests"),
        ("We like beaches and water sports. Kids are 6 and 9 years old.", "Activity preferences"),
        ("We want a mix of adventure and relaxation. Budget 500-1000 per activity", "Budget and balance"),
        ("What's your top recommendation for a 5-day itinerary?", "Yatra creates itinerary"),
    ]

    for query, description in queries:
        print(f"📝 {description}")
        print(f"👤 User: {query}\n")

        response = agent.chat(query)
        print(f"🗺️ Yatra: {response[:300]}...\n")

        # Show shared state
        state = state_manager.get_state()
        prefs = state["travel_preferences"]

        print("📊 Shared State Update:")
        print(f"   Destination: {prefs['destination']}")
        print(f"   Dates: {prefs['checkin_date']} to {prefs['checkout_date']}")
        print(f"   Travelers: {prefs['num_adults']} adults, {prefs['num_children']} children")
        print(f"   Active Agents: {', '.join(state['active_agents'])}")
        print(f"   Messages: {len(state['conversation_history'])}")

        if state["agent_responses"].get("yatra"):
            preview = state["agent_responses"]["yatra"][:80]
            print(f"   Yatra Response: {preview}...")

        print("-" * 70 + "\n")

    # Final status
    print("\n📋 FINAL STATE")
    print("="*70)

    final_state = state_manager.get_state()
    prefs = final_state["travel_preferences"]

    print(f"\n🌍 Travel Info:")
    print(f"   Destination: {prefs['destination']}")
    print(f"   Dates: {prefs['checkin_date']} to {prefs['checkout_date']}")
    print(f"   Travelers: {prefs['num_adults']} adults, {prefs['num_children']} children")
    print(f"   Budget: ₹{prefs['budget']}")

    print(f"\n👥 Active Agents: {', '.join(final_state['active_agents'])}")

    print(f"\n📜 Conversation History ({len(final_state['conversation_history'])} messages):")
    for i, msg in enumerate(final_state["conversation_history"], 1):
        agent_info = f" [{msg['agent']}]" if msg.get('agent') else ""
        content_preview = msg["content"][:50].replace('\n', ' ') + "..."
        print(f"   {i}. {msg['role'].upper()}{agent_info}: {content_preview}")

    print("\n" + "="*70)
    print("✅ Demo completed!")
    print("="*70 + "\n")


def demo_interactive():
    """Interactive demo with Yatra."""
    print("\n" + "🎭 YATRA - INTERACTIVE MODE".center(70))
    print("="*70)
    print("\n💡 Chat with Yatra about attractions and activities in Goa.")
    print("   Type 'status' to see shared state, 'quit' to exit\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    state_manager = initialize_state_manager(session_id="demo-yatra-interactive")
    agent = YatraAgent(api_key=api_key)
    print(f"✅ Yatra ready!\n")

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() == "quit":
                print("🗺️ Yatra: Have an amazing journey! Enjoy your adventures! 🏖️\n")
                break

            if user_input.lower() == "status":
                state = state_manager.get_state()
                prefs = state["travel_preferences"]
                print("\n📊 Shared State:")
                print(f"   Destination: {prefs['destination']}")
                print(f"   Dates: {prefs['checkin_date']} to {prefs['checkout_date']}")
                print(f"   Travelers: {prefs['num_adults']} adults, {prefs['num_children']} children")
                print(f"   Budget: ₹{prefs['budget']}")
                print(f"   Active Agents: {', '.join(state['active_agents'])}")
                print(f"   Messages: {len(state['conversation_history'])}\n")
                continue

            if not user_input:
                continue

            print("\n🗺️ Yatra (thinking)...\n")
            response = agent.chat(user_input)
            print(f"🗺️ Yatra:\n{response}\n")

        except KeyboardInterrupt:
            print("\n🗺️ Yatra: Safe travels!")
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            print(f"❌ Error: {str(e)}\n")


def main():
    """Run demo."""
    print("\n" + "🗺️ YATRA TOURS AGENT WITH SHARED STATE".center(70))
    print("="*70)

    print("\nDemos:")
    print("  1. Sequence (predefined queries)")
    print("  2. Interactive (chat freely)\n")

    choice = input("Select demo (1-2) or press Enter for sequence: ").strip()

    if choice == "2":
        demo_interactive()
    else:
        demo_yatra_with_shared_state()


if __name__ == "__main__":
    main()

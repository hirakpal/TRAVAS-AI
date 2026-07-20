"""Demo: Atithi Agent with Shared State Management

Shows how Atithi integrates with the shared state manager to:
- Track user preferences across conversation turns
- Add conversation history that other agents can see
- Store recommendations that other agents can access
"""

import os
from dotenv import load_dotenv

from agents.atithi_agent import AtithiAgent
from agents.shared_state import initialize_state_manager, get_state_manager
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


def demo_shared_state_integration():
    """Demo showing Atithi's integration with shared state."""
    print("\n" + "🏨 ATITHI WITH SHARED STATE - INTEGRATION DEMO".center(70))
    print("="*70 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    # Initialize shared state for this session
    state_manager = initialize_state_manager(session_id="demo-atithi-shared")
    print(f"✅ Initialized shared state manager (session: demo-atithi-shared)\n")

    # Create Atithi agent
    agent = AtithiAgent(api_key=api_key)
    print(f"✅ Initialized Atithi agent with shared state\n")

    # Demo conversation sequence
    queries = [
        ("I'm looking for a hotel in Goa", "User starts searching"),
        ("July 25-30, 2026, for 2 adults and 2 kids", "User provides dates and travelers"),
        ("We need a family room with pool", "User adds preferences"),
        ("Budget is around 8000 per night", "User provides budget"),
    ]

    for query, description in queries:
        print(f"📝 {description}")
        print(f"👤 User: {query}\n")

        response = agent.chat(query)
        print(f"🤖 Atithi: {response[:250]}...\n")

        # Show shared state after each turn
        state = state_manager.get_state()
        prefs = state["travel_preferences"]

        print("📊 Shared State Update:")
        if prefs["destination"]:
            print(f"   ✓ Destination: {prefs['destination']}")
        if prefs["checkin_date"]:
            print(f"   ✓ Check-in: {prefs['checkin_date']}")
        if prefs["checkout_date"]:
            print(f"   ✓ Check-out: {prefs['checkout_date']}")
        if prefs["num_adults"]:
            print(f"   ✓ Travelers: {prefs['num_adults']} adults, {prefs['num_children']} kids")
        if prefs["budget"]:
            print(f"   ✓ Budget: ₹{prefs['budget']} per night")

        print(f"   📝 Messages in shared history: {len(state['conversation_history'])}")
        print("-" * 70 + "\n")

    # Show final shared state
    print("\n📋 FINAL SHARED STATE:")
    print("="*70)

    final_state = state_manager.get_state()
    prefs = final_state["travel_preferences"]

    print("\n🌍 Travel Preferences:")
    print(f"   Destination: {prefs['destination']}")
    print(f"   Dates: {prefs['checkin_date']} to {prefs['checkout_date']}")
    print(f"   Travelers: {prefs['num_adults']} adults, {prefs['num_children']} children")
    print(f"   Budget: ₹{prefs['budget']} per night")

    print(f"\n💬 Conversation History ({len(final_state['conversation_history'])} messages):")
    for i, msg in enumerate(final_state["conversation_history"], 1):
        agent_info = f" from {msg['agent']}" if msg.get('agent') else ""
        content_preview = msg["content"][:50].replace('\n', ' ') + "..." if len(msg["content"]) > 50 else msg["content"]
        print(f"   {i}. [{msg['role'].upper()}]{agent_info}: {content_preview}")

    print(f"\n👥 Active Agents: {', '.join(final_state['active_agents'])}")
    print(f"🔄 Last Agent Response: {final_state['agent_responses'].get('atithi', 'None')[:100]}...")

    print("\n" + "="*70)
    print("✅ Demo completed!")
    print("="*70 + "\n")


def demo_interactive_with_shared_state():
    """Interactive demo showing shared state in real-time."""
    print("\n" + "🎭 ATITHI - INTERACTIVE SHARED STATE DEMO".center(70))
    print("="*70)
    print("\n💡 As you chat, shared state updates automatically.")
    print("   Type 'state' to see current preferences, 'quit' to exit\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    # Initialize shared state
    state_manager = initialize_state_manager(session_id="demo-interactive")
    agent = AtithiAgent(api_key=api_key)
    print(f"✅ Initialized Atithi with shared state\n")

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() == "quit":
                print("🤖 Atithi: Goodbye! Safe travels! 🛫\n")
                break

            if user_input.lower() == "state":
                state = state_manager.get_state()
                prefs = state["travel_preferences"]
                print("\n📊 Current Shared State:")
                print(f"   Destination: {prefs['destination']}")
                print(f"   Dates: {prefs['checkin_date']} to {prefs['checkout_date']}")
                print(f"   Travelers: {prefs['num_adults']} adults, {prefs['num_children']} children")
                print(f"   Budget: ₹{prefs['budget']}")
                print(f"   Messages: {len(state['conversation_history'])}")
                print(f"   Active Agents: {', '.join(state['active_agents'])}\n")
                continue

            if not user_input:
                continue

            print("\n🤖 Atithi (thinking)...\n")
            response = agent.chat(user_input)
            print(f"🤖 Atithi:\n{response}\n")

        except KeyboardInterrupt:
            print("\n🤖 Atithi: Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            print(f"❌ Error: {str(e)}\n")


def main():
    """Run demo."""
    print("\n" + "🎭 ATITHI WITH SHARED STATE".center(70))
    print("="*70)

    print("\nDemos:")
    print("  1. Sequence (predefined queries)")
    print("  2. Interactive (chat freely)\n")

    choice = input("Select demo (1-2) or press Enter for sequence: ").strip()

    if choice == "2":
        demo_interactive_with_shared_state()
    else:
        demo_shared_state_integration()


if __name__ == "__main__":
    main()

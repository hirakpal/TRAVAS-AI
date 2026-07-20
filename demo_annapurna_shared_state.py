"""Demo: Annapurna Food Agent with Shared State

Shows how Annapurna integrates with shared state to recommend restaurants
while coordinating with other agents and avoiding duplicate preferences.
"""

import os
from dotenv import load_dotenv

from agents.annapurna_agent import AnnapurnaAgent
from agents.shared_state import initialize_state_manager, get_state_manager
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


def demo_annapurna_with_shared_state():
    """Demo showing Annapurna's integration with shared state."""
    print("\n" + "🍜 ANNAPURNA WITH SHARED STATE - RESTAURANT DEMO".center(70))
    print("="*70 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    # Initialize shared state
    state_manager = initialize_state_manager(session_id="demo-annapurna")
    print(f"✅ Initialized shared state manager\n")

    # Pre-fill some shared state (as if Atithi already set it)
    state_manager.update_preferences({
        "destination": "Goa",
        "num_adults": 2,
        "num_children": 2,
    })
    print(f"📝 Pre-filled shared state:")
    print(f"   Destination: Goa")
    print(f"   Travelers: 2 adults, 2 children\n")

    # Create Annapurna agent
    agent = AnnapurnaAgent(api_key=api_key)
    print(f"✅ Initialized Annapurna Food Agent\n")

    # Demo conversation sequence
    queries = [
        ("We need restaurant recommendations in Goa", "Annapurna gathers preferences"),
        ("We're vegetarian and have a kid with nut allergies", "Dietary restrictions"),
        ("Family-friendly, casual dining, budget 400-500 per person", "Budget and occasion"),
        ("What restaurants do you recommend?", "Annapurna searches and recommends"),
    ]

    for query, description in queries:
        print(f"📝 {description}")
        print(f"👤 User: {query}\n")

        response = agent.chat(query)
        print(f"🍜 Annapurna: {response[:300]}...\n")

        # Show shared state
        state = state_manager.get_state()
        prefs = state["travel_preferences"]

        print("📊 Shared State Update:")
        print(f"   Destination: {prefs['destination']}")
        print(f"   Travelers: {prefs['num_adults']} adults, {prefs['num_children']} children")
        print(f"   Active Agents: {', '.join(state['active_agents'])}")
        print(f"   Messages: {len(state['conversation_history'])}")

        if state["agent_responses"].get("annapurna"):
            preview = state["agent_responses"]["annapurna"][:80]
            print(f"   Annapurna Response: {preview}...")

        print("-" * 70 + "\n")

    # Final status
    print("\n📋 FINAL STATE")
    print("="*70)

    final_state = state_manager.get_state()
    prefs = final_state["travel_preferences"]

    print(f"\n🌍 Travel Preferences:")
    print(f"   Destination: {prefs['destination']}")
    print(f"   Travelers: {prefs['num_adults']} adults, {prefs['num_children']} children")

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
    """Interactive demo with Annapurna."""
    print("\n" + "🎭 ANNAPURNA - INTERACTIVE MODE".center(70))
    print("="*70)
    print("\n💡 Chat with Annapurna about restaurants in Goa.")
    print("   Type 'status' to see shared state, 'quit' to exit\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    state_manager = initialize_state_manager(session_id="demo-annapurna-interactive")
    agent = AnnapurnaAgent(api_key=api_key)
    print(f"✅ Annapurna ready!\n")

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() == "quit":
                print("🍜 Annapurna: Enjoy your meals! Bon appétit! 🍴\n")
                break

            if user_input.lower() == "status":
                state = state_manager.get_state()
                prefs = state["travel_preferences"]
                print("\n📊 Shared State:")
                print(f"   Destination: {prefs['destination']}")
                print(f"   Travelers: {prefs['num_adults']} adults, {prefs['num_children']} children")
                print(f"   Active Agents: {', '.join(state['active_agents'])}")
                print(f"   Messages: {len(state['conversation_history'])}\n")
                continue

            if not user_input:
                continue

            print("\n🍜 Annapurna (thinking)...\n")
            response = agent.chat(user_input)
            print(f"🍜 Annapurna:\n{response}\n")

        except KeyboardInterrupt:
            print("\n🍜 Annapurna: Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            print(f"❌ Error: {str(e)}\n")


def main():
    """Run demo."""
    print("\n" + "🍜 ANNAPURNA FOOD AGENT WITH SHARED STATE".center(70))
    print("="*70)

    print("\nDemos:")
    print("  1. Sequence (predefined queries)")
    print("  2. Interactive (chat freely)\n")

    choice = input("Select demo (1-2) or press Enter for sequence: ").strip()

    if choice == "2":
        demo_interactive()
    else:
        demo_annapurna_with_shared_state()


if __name__ == "__main__":
    main()

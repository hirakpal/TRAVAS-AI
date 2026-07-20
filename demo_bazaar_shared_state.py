"""Demo: Bazaar Shopping Agent with Shared State"""

import os
from dotenv import load_dotenv

from agents.bazaar_agent import BazaarAgent
from agents.shared_state import initialize_state_manager, get_state_manager
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


def demo_bazaar_with_shared_state():
    """Demo showing Bazaar's integration with shared state."""
    print("\n" + "🛍️ BAZAAR WITH SHARED STATE - SHOPPING DEMO".center(70))
    print("="*70 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    state_manager = initialize_state_manager(session_id="demo-bazaar")
    print(f"✅ Initialized shared state manager\n")

    state_manager.update_preferences({
        "destination": "Goa",
        "checkin_date": "2026-07-25",
        "checkout_date": "2026-07-30",
        "num_adults": 2,
        "num_children": 2,
        "budget": 8000,
    })
    print(f"📝 Pre-filled shared state - 5 days in Goa, ₹8000 budget\n")

    agent = BazaarAgent(api_key=api_key)
    print(f"✅ Initialized Bazaar Shopping Agent\n")

    queries = [
        ("We want to buy souvenirs and gifts", "Bazaar gathers shopping needs"),
        ("Spices, handicrafts, some jewelry - budget ₹2000", "Shopping preferences"),
        ("We like authentic local items, kids enjoy unique things", "Quality preference"),
        ("What shops would you recommend?", "Bazaar searches and compares"),
    ]

    for query, description in queries:
        print(f"📝 {description}")
        print(f"👤 User: {query}\n")

        response = agent.chat(query)
        print(f"🛍️ Bazaar: {response[:300]}...\n")

        state = state_manager.get_state()
        print("📊 Shared State:")
        print(f"   Active Agents: {', '.join(state['active_agents'])}")
        print(f"   Messages: {len(state['conversation_history'])}\n")
        print("-" * 70 + "\n")

    print("\n" + "="*70)
    print("✅ Demo completed!")
    print("="*70 + "\n")


def demo_interactive():
    """Interactive demo with Bazaar."""
    print("\n" + "🛍️ BAZAAR - INTERACTIVE MODE".center(70))
    print("="*70)
    print("\n💡 Chat with Bazaar about shopping and souvenirs in Goa.")
    print("   Type 'quit' to exit\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    state_manager = initialize_state_manager(session_id="demo-bazaar-interactive")
    agent = BazaarAgent(api_key=api_key)
    print(f"✅ Bazaar ready!\n")

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() == "quit":
                print("🛍️ Bazaar: Happy shopping! Enjoy your souvenirs! 🎁\n")
                break

            if not user_input:
                continue

            print("\n🛍️ Bazaar (thinking)...\n")
            response = agent.chat(user_input)
            print(f"🛍️ Bazaar:\n{response}\n")

        except KeyboardInterrupt:
            print("\n🛍️ Bazaar: Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            print(f"❌ Error: {str(e)}\n")


def main():
    """Run demo."""
    print("\n" + "🛍️ BAZAAR SHOPPING AGENT WITH SHARED STATE".center(70))
    print("="*70)
    print("\nDemos:\n  1. Sequence (predefined queries)\n  2. Interactive (chat freely)\n")

    choice = input("Select demo (1-2) or press Enter for sequence: ").strip()

    if choice == "2":
        demo_interactive()
    else:
        demo_bazaar_with_shared_state()


if __name__ == "__main__":
    main()

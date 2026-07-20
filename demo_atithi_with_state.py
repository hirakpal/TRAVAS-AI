"""Demo: Atithi with LangGraph state management"""

import os
from dotenv import load_dotenv
from agents.atithi_with_state import AtithiWithState
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


def demo_interactive():
    """Interactive demo with state management"""
    print("\n" + "🎭 ATITHI WITH LANGGRAPH STATE MANAGEMENT".center(70))
    print("="*70)
    print("\nPhases:")
    print("  Phase 1: Gather destination, dates, travelers")
    print("  Phase 2: Gather budget and preferences")
    print("  Phase 3: Search and recommend hotels")
    print("\nType 'status' to see current phase, 'quit' to exit\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    agent = AtithiWithState(api_key=api_key)
    print(f"✅ Initialized Atithi with state management\n")

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() == "quit":
                print("🤖 Atithi: Goodbye! Safe travels! 🛫\n")
                break

            if user_input.lower() == "status":
                status = agent.get_status()
                print(f"\n📊 Status:")
                print(f"   Phase: {status['phase']}")
                print(f"   Phase 1 complete: {status['phase_1_complete']}")
                print(f"   Phase 2 complete: {status['phase_2_complete']}")
                print(f"   Destination: {status['destination']}")
                print(f"   Budget: {status['budget']}")
                print(f"   Messages: {status['messages_count']}\n")
                continue

            if not user_input:
                continue

            print("\n🤖 Atithi (processing)...\n")
            response = agent.chat(user_input)
            print(f"🤖 Atithi:\n{response}\n")

        except KeyboardInterrupt:
            print("\n🤖 Atithi: Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            print(f"❌ Error: {str(e)}\n")


def demo_sequence():
    """Demo with predefined sequence"""
    print("\n" + "🎭 ATITHI STATE MANAGEMENT - SEQUENCE DEMO".center(70))
    print("="*70 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    agent = AtithiWithState(api_key=api_key)

    # Predefined sequence
    queries = [
        ("I'm looking for a hotel in Goa", "Phase 1: Ask for dates"),
        ("July 25-30, 2 adults and 2 kids", "Phase 1: Ask for rooms"),
        ("One family room please", "Phase 1: Complete - move to Phase 2"),
        ("Our budget is ₹8000 per night", "Phase 2: Ask for preferences"),
        ("We want beach location with pool", "Phase 2: Complete - move to Phase 3"),
    ]

    for query, description in queries:
        print(f"📝 {description}")
        print(f"👤 User: {query}\n")

        response = agent.chat(query)
        status = agent.get_status()

        print(f"🤖 Atithi: {response[:300]}...\n")
        print(f"📊 Phase: {status['phase']}, "
              f"Phase 1: {status['phase_1_complete']}, "
              f"Phase 2: {status['phase_2_complete']}\n")
        print("-" * 70 + "\n")


def main():
    """Run demo"""
    print("\n" + "🎭 ATITHI WITH LANGGRAPH STATE MANAGEMENT".center(70))
    print("="*70)

    print("\nDemos:")
    print("  1. Sequence (predefined questions)")
    print("  2. Interactive (chat freely)\n")

    choice = input("Select demo (1-2) or press Enter for interactive: ").strip()

    if choice == "1":
        demo_sequence()
    else:
        demo_interactive()

    print("\n" + "="*70)
    print("✅ Demo completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

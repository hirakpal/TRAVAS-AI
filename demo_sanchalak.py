"""Simple demo of Sanchalak Orchestrator"""

import os
from agents.sanchalak_agent import SanchalakAgent
from utils.logger import get_logger

logger = get_logger(__name__)


def demo_basic_orchestration():
    """Demo 1: Routing different queries"""
    print("\n" + "="*70)
    print("  DEMO 1: Sanchalak Routing Different Queries")
    print("="*70 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    orchestrator = SanchalakAgent(api_key=api_key)
    print(f"✅ Initialized {orchestrator}\n")

    # Different queries for different agents
    queries = [
        "I need a hotel in Goa for my family",
        "We want a budget hotel in Delhi",
        "Looking for luxury accommodation in Mumbai",
    ]

    for query in queries:
        print(f"👤 User: {query}")
        print(f"🎯 Sanchalak: Routing to appropriate agent...\n")

        response = orchestrator.route_query(query)

        if response["success"]:
            print(f"🤖 Agent ({response['agent']}): {response['message'][:300]}...\n")
        else:
            print(f"❌ Error: {response['message']}\n")

        print("-" * 70 + "\n")

    # Show orchestrator status
    print("📊 Orchestrator Status:")
    info = orchestrator.get_orchestrator_info()
    print(f"   Agents available: {info['available_agents']}")
    print(f"   Last agent used: {info['last_agent_used']}")
    print(f"   Total conversation turns: {info['conversation_turns']}\n")


def demo_multi_turn_orchestration():
    """Demo 2: Multi-turn conversation with same agent"""
    print("\n" + "="*70)
    print("  DEMO 2: Multi-Turn with Same Agent")
    print("="*70 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    orchestrator = SanchalakAgent(api_key=api_key)

    # Multi-turn conversation about hotels
    turns = [
        "I'm looking for a hotel in Goa",
        "We have 2 kids aged 6 and 8",
        "Budget around ₹8000 per night",
        "We love beaches and water activities",
    ]

    for i, message in enumerate(turns, 1):
        print(f"Turn {i}:")
        print(f"👤 User: {message}")

        response = orchestrator.route_query(message)

        if response["success"]:
            # Show response preview
            preview = response["message"][:200] + "..." if len(response["message"]) > 200 else response["message"]
            print(f"🤖 Agent ({response['agent']}): {preview}\n")
        else:
            print(f"❌ Error: {response['message']}\n")

    print("📊 Final Status:")
    info = orchestrator.get_orchestrator_info()
    print(f"   Turns processed: {info['conversation_turns']}")
    print(f"   Agent used: {info['last_agent_used']}\n")


def demo_interactive():
    """Demo 3: Interactive mode"""
    print("\n" + "="*70)
    print("  DEMO 3: Interactive Orchestration")
    print("="*70 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    orchestrator = SanchalakAgent(api_key=api_key)

    print("🎭 Sanchalak Orchestrator - Interactive Mode")
    print("(Type 'quit' to exit, 'status' to see agent info)\n")

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() == "quit":
                print("🎭 Sanchalak: Goodbye! Safe travels! 🛫\n")
                break

            if user_input.lower() == "status":
                info = orchestrator.get_orchestrator_info()
                print(f"\n📊 Status:")
                print(f"   Available agents: {info['available_agents']}")
                print(f"   Last used: {info['last_agent_used']}")
                print(f"   Turns: {info['conversation_turns']}\n")
                continue

            if not user_input:
                continue

            print("\n🎭 Sanchalak (routing to appropriate agent)...\n")
            response = orchestrator.route_query(user_input)

            if response["success"]:
                print(f"🤖 {response['agent'].capitalize()}:")
                print(f"{response['message']}\n")
            else:
                print(f"❌ {response['message']}\n")

        except KeyboardInterrupt:
            print("\n🎭 Sanchalak: Goodbye!")
            break


def main():
    """Run demos"""
    print("\n" + "🎭 SANCHALAK ORCHESTRATOR DEMO".center(70))
    print("="*70)

    print("\nAvailable Demos:")
    print("  1. Basic Query Routing")
    print("  2. Multi-Turn Conversation")
    print("  3. Interactive Mode\n")

    choice = input("Select demo (1-3) or press Enter for all: ").strip()

    try:
        if choice == "1":
            demo_basic_orchestration()
        elif choice == "2":
            demo_multi_turn_orchestration()
        elif choice == "3":
            demo_interactive()
        else:
            # Run all
            demo_basic_orchestration()
            demo_multi_turn_orchestration()

    except Exception as e:
        logger.error(f"Demo error: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)
    print("✅ Demo completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

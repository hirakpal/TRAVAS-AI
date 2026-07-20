"""Demo: Sanchalak Orchestrator with Shared State

Shows how the orchestrator routes queries while maintaining unified shared state:
- Sanchalak identifies user intent and routes to appropriate agent
- Shared state tracks all conversations from all agents
- All agents access and update the same preferences
- Orchestrator sees context from all specialist agents
"""

import os
from dotenv import load_dotenv

from agents.sanchalak_agent import SanchalakAgent
from agents.shared_state import initialize_state_manager, get_state_manager
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


def demo_orchestrator_with_shared_state():
    """Demo showing Sanchalak orchestrating with shared state."""
    print("\n" + "🎭 SANCHALAK WITH SHARED STATE - ORCHESTRATION DEMO".center(70))
    print("="*70 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    # Initialize shared state for this session
    state_manager = initialize_state_manager(session_id="demo-sanchalak-orchestration")
    print(f"✅ Initialized shared state manager\n")

    # Create orchestrator
    orchestrator = SanchalakAgent(api_key=api_key)
    print(f"✅ Initialized Sanchalak Orchestrator\n")

    # Demo conversation - Sanchalak routes each query
    queries = [
        ("I need a hotel in Goa", "Sanchalak recognizes hotel intent → routes to Atithi"),
        ("July 25-30, 2 adults and 2 kids", "Atithi gathers traveler info"),
        ("Family room with pool, budget 8000", "Atithi collects preferences"),
        ("What hotels do you recommend?", "Atithi provides recommendations"),
    ]

    for query, description in queries:
        print(f"📝 {description}")
        print(f"👤 User: {query}\n")

        response = orchestrator.chat(query)
        print(f"🤖 Response: {response[:250]}...\n")

        # Show shared state after each turn
        state = state_manager.get_state()
        active_agents = state["active_agents"]
        all_responses = state["agent_responses"]

        print("📊 Shared State Update:")
        print(f"   Active Agents: {', '.join(active_agents)}")
        print(f"   Agent Responses: {', '.join(all_responses.keys())}")
        print(f"   Messages: {len(state['conversation_history'])}")

        prefs = state["travel_preferences"]
        if prefs["destination"]:
            print(f"   Destination: {prefs['destination']}")
        if prefs["budget"]:
            print(f"   Budget: ₹{prefs['budget']} per night")

        print("-" * 70 + "\n")

    # Show final orchestrator state
    print("\n📋 FINAL ORCHESTRATOR STATE:")
    print("="*70)

    orch_info = orchestrator.get_orchestrator_info()
    print(f"\n🎯 Orchestrator Status:")
    print(f"   Name: {orch_info['name']}")
    print(f"   Role: {orch_info['role']}")
    print(f"   Available Agents: {', '.join(orch_info['available_agents'])}")
    print(f"   Last Agent Used: {orch_info['last_agent_used']}")
    print(f"   Conversation Turns: {orch_info['conversation_turns']}")

    final_state = state_manager.get_state()
    prefs = final_state["travel_preferences"]

    print(f"\n🌍 Shared Travel Preferences:")
    print(f"   Destination: {prefs['destination']}")
    print(f"   Dates: {prefs['checkin_date']} to {prefs['checkout_date']}")
    print(f"   Travelers: {prefs['num_adults']} adults, {prefs['num_children']} children")
    print(f"   Budget: ₹{prefs['budget']} per night")

    print(f"\n📊 Active Agents: {', '.join(final_state['active_agents'])}")

    print(f"\n💬 All Agent Responses:")
    for agent_name, response in final_state["agent_responses"].items():
        preview = response[:80].replace('\n', ' ') + "..." if len(response) > 80 else response
        print(f"   {agent_name}: {preview}")

    print(f"\n📜 Conversation History ({len(final_state['conversation_history'])} messages):")
    for i, msg in enumerate(final_state["conversation_history"], 1):
        agent_info = f" [{msg['agent']}]" if msg.get('agent') else ""
        content_preview = msg["content"][:50].replace('\n', ' ') + "..." if len(msg["content"]) > 50 else msg["content"]
        print(f"   {i}. {msg['role'].upper()}{agent_info}: {content_preview}")

    print("\n" + "="*70)
    print("✅ Demo completed!")
    print("="*70 + "\n")


def demo_multi_turn_orchestration():
    """Demo showing multi-turn orchestration with shared state."""
    print("\n" + "🎭 SANCHALAK - MULTI-TURN ORCHESTRATION DEMO".center(70))
    print("="*70)
    print("\n💡 Sanchalak routes your queries intelligently.")
    print("   Type 'status' to see orchestrator state, 'quit' to exit\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    # Initialize
    state_manager = initialize_state_manager(session_id="demo-orchestration-interactive")
    orchestrator = SanchalakAgent(api_key=api_key)
    print(f"✅ Sanchalak Orchestrator initialized\n")

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() == "quit":
                print("🎭 Sanchalak: Thank you for using TRAVAS! Safe travels! 🌍\n")
                break

            if user_input.lower() == "status":
                status = orchestrator.get_orchestrator_info()
                state = state_manager.get_state()
                prefs = state["travel_preferences"]

                print("\n📊 Orchestrator Status:")
                print(f"   Last Agent Used: {status['last_agent_used']}")
                print(f"   Active Agents: {', '.join(state['active_agents'])}")
                print(f"   Conversation Turns: {status['conversation_turns']}")

                print(f"\n🌍 Shared Preferences:")
                print(f"   Destination: {prefs['destination']}")
                print(f"   Budget: ₹{prefs['budget']}")
                print(f"   Messages: {len(state['conversation_history'])}\n")
                continue

            if not user_input:
                continue

            print("\n🎭 Sanchalak (routing)...\n")
            response = orchestrator.chat(user_input)

            # Show which agent handled it
            agent_used = orchestrator.last_agent_used
            print(f"🤖 [{agent_used.upper()}]:\n{response}\n")

        except KeyboardInterrupt:
            print("\n🎭 Sanchalak: Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            print(f"❌ Error: {str(e)}\n")


def main():
    """Run demo."""
    print("\n" + "🎭 SANCHALAK ORCHESTRATOR WITH SHARED STATE".center(70))
    print("="*70)

    print("\nDemos:")
    print("  1. Orchestration (predefined queries)")
    print("  2. Interactive (multi-turn)\n")

    choice = input("Select demo (1-2) or press Enter for orchestration: ").strip()

    if choice == "2":
        demo_multi_turn_orchestration()
    else:
        demo_orchestrator_with_shared_state()


if __name__ == "__main__":
    main()

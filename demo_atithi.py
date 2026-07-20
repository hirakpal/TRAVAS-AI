"""Demo script for Atithi (Hotel) Agent.

This script demonstrates:
- Multi-turn conversations
- Tool use (searching, filtering hotels)
- Agentic loops (reasoning and refinement)
- Error handling
- Streaming responses
"""

import os
from typing import Optional
from agents.atithi_agent import AtithiAgent
from utils.logger import get_logger

logger = get_logger(__name__)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_basic_conversation():
    """Demo 1: Basic multi-turn conversation."""
    print_section("DEMO 1: Basic Hotel Recommendation Conversation")

    # Initialize agent
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set in environment")
        return

    agent = AtithiAgent(api_key=api_key)
    print(f"✅ Initialized {agent}")
    print(f"Available tools: {[t.name for t in agent.__dict__.get('tools', [])]}\n")

    # Turn 1: Initial request
    print("👤 User: I'm looking for a hotel in Delhi for 3 nights. My budget is ₹5000 per night.")
    response1 = agent.chat(
        "I'm looking for a hotel in Delhi for 3 nights. My budget is ₹5000 per night."
    )
    print(f"🤖 Atithi:\n{response1}\n")

    # Turn 2: Refine request
    print("👤 User: We have a family with kids. Vegetarian food is important to us.")
    response2 = agent.chat(
        "We have a family with kids. Vegetarian food is important to us."
    )
    print(f"🤖 Atithi:\n{response2}\n")

    # Turn 3: Ask for specifics
    print("👤 User: What about the Taj Palace? Can you tell me more about it?")
    response3 = agent.chat(
        "What about the Taj Palace? Can you tell me more about it?"
    )
    print(f"🤖 Atithi:\n{response3}\n")

    # Display conversation info
    print(f"\n📊 Conversation Stats:")
    print(f"   - Total turns: {agent.get_history_count()}")
    print(f"   - Agent info: {agent.get_agent_info()}\n")


def demo_streaming():
    """Demo 2: Streaming responses."""
    print_section("DEMO 2: Streaming Responses")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set in environment")
        return

    agent = AtithiAgent(api_key=api_key)

    print("👤 User: Find me a budget hotel in Goa under ₹4000 per night.")
    print("🤖 Atithi (streaming):\n")

    # Stream the response
    for chunk in agent.chat_stream(
        "Find me a budget hotel in Goa under ₹4000 per night."
    ):
        print(chunk, end="", flush=True)

    print("\n")


def demo_error_handling():
    """Demo 3: Error handling."""
    print_section("DEMO 3: Error Handling")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set in environment")
        return

    agent = AtithiAgent(api_key=api_key)

    # Test 1: Empty input
    print("Test 1: Empty input")
    print("👤 User: (empty message)")
    response = agent.chat("")
    print(f"🤖 Atithi: {response}\n")

    # Test 2: Unrealistic budget
    print("Test 2: Unrealistic budget")
    print("👤 User: I need a hotel for ₹100 per night.")
    response = agent.chat("I need a hotel for ₹100 per night.")
    print(f"🤖 Atithi: {response}\n")

    # Test 3: Unknown city
    print("Test 3: Unknown city")
    print("👤 User: Looking for hotels in Atlantis")
    response = agent.chat("Looking for hotels in Atlantis")
    print(f"🤖 Atithi: {response}\n")


def demo_multi_agent_capability():
    """Demo 4: Multiple agents working independently."""
    print_section("DEMO 4: Multiple Agent Instances")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set in environment")
        return

    # Create two independent agent instances
    agent1 = AtithiAgent(api_key=api_key)
    agent2 = AtithiAgent(api_key=api_key)

    print("Creating 2 independent Atithi agents for different travelers\n")

    # Traveler 1: Budget conscious
    print("👤 Traveler 1 (Budget): I need a budget hotel in Mumbai, under ₹3000")
    response1 = agent1.chat("I need a budget hotel in Mumbai, under ₹3000")
    print(f"🤖 Agent 1 response (preview): {response1[:200]}...\n")

    # Traveler 2: Luxury seeker
    print("👤 Traveler 2 (Luxury): Looking for 5-star hotels in Delhi with spa facilities")
    response2 = agent2.chat("Looking for 5-star hotels in Delhi with spa facilities")
    print(f"🤖 Agent 2 response (preview): {response2[:200]}...\n")

    print(f"✅ Agent 1 state: {agent1.get_history_count()} turns")
    print(f"✅ Agent 2 state: {agent2.get_history_count()} turns")
    print("(Agents maintain independent conversation histories)\n")


def interactive_mode():
    """Demo 5: Interactive conversation."""
    print_section("DEMO 5: Interactive Mode (Type 'quit' to exit)")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set in environment")
        return

    agent = AtithiAgent(api_key=api_key)
    print("🤖 Atithi: Namaste! 🙏 I'm Atithi, your hotel recommendation assistant.")
    print("           Tell me about your travel plans, and I'll help you find the perfect stay.\n")

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("🤖 Atithi: Thank you for using TRAVAS! Safe travels! 🛫")
                break

            if not user_input:
                print("🤖 Atithi: Please tell me something so I can help you.\n")
                continue

            print("🤖 Atithi (thinking...)...")
            response = agent.chat(user_input)
            print(f"🤖 Atithi:\n{response}\n")

        except KeyboardInterrupt:
            print("\n🤖 Atithi: Goodbye! Safe travels!")
            break
        except Exception as e:
            logger.error(f"Error in interactive mode: {str(e)}")
            print(f"❌ Error: {str(e)}\n")


def main():
    """Run all demos."""
    print("\n" + "🌍 TRAVAS-AI: Travel Assistant System".center(60))
    print("🏨 Atithi Agent - Hotel Recommendation Specialist".center(60))
    print("\n")

    print("Available demos:")
    print("  1. Basic conversation (default)")
    print("  2. Streaming responses")
    print("  3. Error handling")
    print("  4. Multiple agents")
    print("  5. Interactive mode\n")

    choice = input("Select demo (1-5) or press Enter for all: ").strip()

    try:
        if choice == "1":
            demo_basic_conversation()
        elif choice == "2":
            demo_streaming()
        elif choice == "3":
            demo_error_handling()
        elif choice == "4":
            demo_multi_agent_capability()
        elif choice == "5":
            interactive_mode()
        else:
            # Run all demos
            demo_basic_conversation()
            demo_streaming()
            demo_error_handling()
            demo_multi_agent_capability()

    except Exception as e:
        logger.error(f"Demo error: {str(e)}")
        print(f"\n❌ Error running demo: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("✅ Demo completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

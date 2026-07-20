#!/usr/bin/env python3
"""
Quick test runner for Atithi Agent with new system prompt.

This script provides an easy way to test different scenarios.
"""

import os
import sys
from datetime import datetime
from agents.atithi_agent import AtithiAgent
from utils.logger import get_logger

logger = get_logger(__name__)


def print_header(title: str):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_family_vacation():
    """Test Scenario 1: Family Vacation Planning"""
    print_header("TEST 1: Family Vacation Planning")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False

    agent = AtithiAgent(api_key=api_key)

    tests = [
        ("We're looking for a hotel in Goa for a family vacation", "Family inquiry"),
        ("We have 2 kids, ages 6 and 8. July 25-30. Budget ₹8000/night", "Family details"),
        ("The kids love water activities. We want beach with pool and kids play area", "Preferences"),
        ("Tell me more about the first recommendation", "Details request"),
    ]

    for user_message, description in tests:
        print(f"📝 {description}")
        print(f"👤 User: {user_message}\n")

        try:
            response = agent.chat(user_message)
            print(f"🤖 Atithi:\n{response}\n")
            print("-" * 70 + "\n")
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
            return False

    print("✅ Family Vacation Test Passed\n")
    return True


def test_business_traveler():
    """Test Scenario 2: Business Traveler"""
    print_header("TEST 2: Business Traveler")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False

    agent = AtithiAgent(api_key=api_key)

    tests = [
        ("I need a hotel in Delhi's business district for 2 nights", "Business inquiry"),
        ("August 10-12, budget ₹12,000/night. Need conference facilities and WiFi", "Business details"),
        ("Do they have airport shuttle?", "Specific amenity query"),
    ]

    for user_message, description in tests:
        print(f"📝 {description}")
        print(f"👤 User: {user_message}\n")

        try:
            response = agent.chat(user_message)
            print(f"🤖 Atithi:\n{response}\n")
            print("-" * 70 + "\n")
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
            return False

    print("✅ Business Traveler Test Passed\n")
    return True


def test_accessibility_needs():
    """Test Scenario 3: Accessibility Needs"""
    print_header("TEST 3: Accessibility Needs")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False

    agent = AtithiAgent(api_key=api_key)

    tests = [
        ("I need a hotel in Jaipur. I use a wheelchair, need accessible rooms", "Accessibility inquiry"),
        ("July 28-30. Wheelchair accessible room, elevator, accessible bathroom needed", "Accessibility details"),
        ("Can they assist with mobility needs at the hotel?", "Staff assistance query"),
    ]

    for user_message, description in tests:
        print(f"📝 {description}")
        print(f"👤 User: {user_message}\n")

        try:
            response = agent.chat(user_message)
            print(f"🤖 Atithi:\n{response}\n")
            print("-" * 70 + "\n")
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
            return False

    print("✅ Accessibility Test Passed\n")
    return True


def test_error_handling():
    """Test Scenario 4: Error Handling"""
    print_header("TEST 4: Error Handling")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False

    agent = AtithiAgent(api_key=api_key)

    tests = [
        ("", "Empty input"),
        ("I need a hotel for ₹50 per night", "Unrealistic budget"),
        ("Hotel in Atlantis please", "Unknown city"),
    ]

    for user_message, description in tests:
        print(f"📝 {description}")
        if user_message:
            print(f"👤 User: {user_message}\n")
        else:
            print(f"👤 User: (empty message)\n")

        try:
            response = agent.chat(user_message)
            print(f"🤖 Atithi:\n{response}\n")
            print("-" * 70 + "\n")
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
            return False

    print("✅ Error Handling Test Passed\n")
    return True


def test_streaming():
    """Test Scenario 5: Streaming Response"""
    print_header("TEST 5: Streaming Response")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False

    agent = AtithiAgent(api_key=api_key)

    user_message = "Find me a budget hotel in Goa under ₹4000 per night for a solo trip"
    print(f"👤 User: {user_message}\n")
    print("🤖 Atithi (streaming):\n")

    try:
        for chunk in agent.chat_stream(user_message):
            print(chunk, end="", flush=True)
        print("\n")
        print("-" * 70 + "\n")
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False

    print("✅ Streaming Test Passed\n")
    return True


def test_multi_turn():
    """Test Scenario 6: Multi-Turn Conversation Memory"""
    print_header("TEST 6: Multi-Turn Conversation Memory")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return False

    agent = AtithiAgent(api_key=api_key)

    tests = [
        ("I'm looking for a hotel", "Turn 1: Basic inquiry"),
        ("It's in Delhi, 3 nights, family with kids", "Turn 2: Add family details"),
        ("Kids love swimming", "Turn 3: Add preference"),
        ("Vegetarian food is important", "Turn 4: Add dietary need"),
        ("Show me recommendations", "Turn 5: Request recommendations"),
    ]

    for user_message, description in tests:
        print(f"📝 {description}")
        print(f"👤 User: {user_message}\n")

        try:
            response = agent.chat(user_message)
            # Truncate long responses for readability in test
            if len(response) > 300:
                print(f"🤖 Atithi: {response[:300]}...\n")
            else:
                print(f"🤖 Atithi:\n{response}\n")
            print("-" * 70 + "\n")
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
            return False

    print(f"✅ Multi-Turn Test Passed")
    print(f"📊 Conversation turns: {agent.get_history_count()}")
    print(f"📊 Agent info: {agent.get_agent_info()}\n")
    return True


def main():
    """Run all tests or interactive mode"""
    print("\n" + "🧪 ATITHI AGENT TEST SUITE".center(70))
    print("="*70)

    print("\nAvailable Tests:")
    print("  1. Family Vacation Planning")
    print("  2. Business Traveler")
    print("  3. Accessibility Needs")
    print("  4. Error Handling")
    print("  5. Streaming Response")
    print("  6. Multi-Turn Conversation")
    print("  7. Run All Tests")
    print("  8. Interactive Mode (Manual Testing)\n")

    choice = input("Select test (1-8) or press Enter for all: ").strip()

    start_time = datetime.now()

    try:
        if choice == "1":
            test_family_vacation()
        elif choice == "2":
            test_business_traveler()
        elif choice == "3":
            test_accessibility_needs()
        elif choice == "4":
            test_error_handling()
        elif choice == "5":
            test_streaming()
        elif choice == "6":
            test_multi_turn()
        elif choice == "7":
            # Run all tests
            results = [
                ("Family Vacation", test_family_vacation()),
                ("Business Traveler", test_business_traveler()),
                ("Accessibility", test_accessibility_needs()),
                ("Error Handling", test_error_handling()),
                ("Streaming", test_streaming()),
                ("Multi-Turn", test_multi_turn()),
            ]

            print_header("TEST SUMMARY")
            for test_name, passed in results:
                status = "✅ PASSED" if passed else "❌ FAILED"
                print(f"{test_name}: {status}")

            passed_count = sum(1 for _, p in results if p)
            print(f"\nTotal: {passed_count}/{len(results)} tests passed\n")

        elif choice == "8" or choice == "":
            # Interactive mode
            print_header("INTERACTIVE MODE (Type 'quit' to exit)")
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print("❌ ANTHROPIC_API_KEY not set")
                return

            agent = AtithiAgent(api_key=api_key)
            print("🤖 Atithi: Namaste! 🙏 I'm your hotel concierge assistant.")
            print("           Tell me about your travel plans!\n")

            while True:
                try:
                    user_input = input("👤 You: ").strip()

                    if user_input.lower() in ["quit", "exit", "bye"]:
                        print("🤖 Atithi: Thank you for testing! Safe travels! 🛫\n")
                        break

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
        else:
            print("❌ Invalid choice\n")

    except Exception as e:
        logger.error(f"Test error: {str(e)}")
        print(f"❌ Test error: {str(e)}\n")
        import traceback
        traceback.print_exc()

    elapsed = datetime.now() - start_time
    print(f"⏱️  Total time: {elapsed.total_seconds():.2f} seconds\n")


if __name__ == "__main__":
    main()

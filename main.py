#!/usr/bin/env python
"""
TRAVAS-AI Main Entry Point

Interactive CLI for running TRAVAS agents.
"""

import sys
import argparse
from typing import Optional
import logging

from agents.atithi_agent import create_atithi_agent
from agents.registry import get_agent
from config.settings import Settings
from utils.logger import get_logger

logger = get_logger(__name__)


def run_atithi_interactive(api_key: Optional[str] = None, provider: str = "openai"):
    """
    Run Atithi Agent in interactive mode.

    Args:
        api_key: Optional API key (uses environment if not provided)
        provider: LLM provider to use
    """
    print("\n" + "=" * 70)
    print("TRAVAS-AI: Atithi Hotel Concierge Agent")
    print("=" * 70)
    print("\nWelcome! I'm Atithi, your hotel concierge assistant.")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    try:
        agent = create_atithi_agent(provider=provider, api_key=api_key)
        print(f"Connected with {provider} | Model: {agent.model}\n")

        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                # Exit commands
                if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                    print("\nAtithi: Thank you for choosing TRAVAS-AI. Safe travels! 🙏")
                    break

                # Skip empty inputs
                if not user_input:
                    continue

                # Get response from agent
                print("\nAtithi: ", end="", flush=True)
                response = agent.chat(user_input)
                print(response)
                print()

            except KeyboardInterrupt:
                print("\n\nAtithi: Goodbye! Safe travels! 🙏")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"\nSorry, I encountered an error: {e}")
                print("Please try again or type 'exit' to quit.\n")

    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        print(f"Error: {e}")
        sys.exit(1)


def run_agent_command(agent_name: str, user_input: str, provider: str = "openai"):
    """
    Run a single command with an agent.

    Args:
        agent_name: Name of the agent
        user_input: User's input message
        provider: LLM provider
    """
    try:
        # Get or create agent
        agent = get_agent(agent_name, provider=provider)

        if not agent:
            print(f"Error: Agent '{agent_name}' not found")
            print(f"Available agents: {get_available_agents()}")
            sys.exit(1)

        # Get response
        response = agent.chat(user_input)
        print(response)

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


def get_available_agents() -> str:
    """Get list of available agents"""
    from agents.registry import AgentRegistry
    agents = AgentRegistry.list_agent_names()
    return ", ".join(agents) if agents else "None"


def show_status():
    """Show system status"""
    print("\n" + "=" * 70)
    print("TRAVAS-AI System Status")
    print("=" * 70)

    # Environment
    print(f"\nEnvironment: {Settings.APP_ENV}")
    print(f"Debug: {Settings.DEBUG}")

    # LLM
    print(f"\nDefault LLM Provider: {Settings.DEFAULT_LLM_PROVIDER}")
    print(f"Available Providers: openai, anthropic, gemini")

    # Agents
    print(f"\nAvailable Agents: {get_available_agents()}")

    # Features
    print(f"\nFeatures:")
    print(f"  - Atithi Agent: {Settings.FEATURE_ATITHI_AGENT}")
    print(f"  - Hotel Comparison: {Settings.FEATURE_HOTEL_COMPARISON}")
    print(f"  - Multi-language: {Settings.FEATURE_MULTI_LANGUAGE}")
    print(f"  - Booking Integration: {Settings.FEATURE_BOOKING_INTEGRATION}")

    print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="TRAVAS-AI - Travel Assistant Agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Interactive Atithi mode
  python main.py -a hotel "I need a room in Delhi"  # Single command
  python main.py --status                           # Show system status
        """
    )

    parser.add_argument(
        "-a", "--agent",
        type=str,
        default="atithi",
        help="Agent to use (default: atithi)"
    )

    parser.add_argument(
        "-p", "--provider",
        type=str,
        default="openai",
        choices=["openai", "anthropic", "gemini"],
        help="LLM provider (default: openai)"
    )

    parser.add_argument(
        "-k", "--api-key",
        type=str,
        help="API key (uses environment variable if not provided)"
    )

    parser.add_argument(
        "message",
        nargs="?",
        help="User message to send to agent (interactive mode if not provided)"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status and exit"
    )

    args = parser.parse_args()

    # Show status if requested
    if args.status:
        show_status()
        return

    # Validate settings
    try:
        Settings.validate()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print(f"Please set {e} environment variable")
        sys.exit(1)

    # Run agent
    if args.message:
        # Single command mode
        logger.info(f"Running {args.agent} agent with message: {args.message[:50]}...")
        run_agent_command(args.agent, args.message, provider=args.provider)
    else:
        # Interactive mode
        if args.agent != "atithi":
            print(f"Interactive mode only supports 'atithi' agent")
            sys.exit(1)
        logger.info(f"Starting interactive {args.agent} agent")
        run_atithi_interactive(api_key=args.api_key, provider=args.provider)


if __name__ == "__main__":
    main()

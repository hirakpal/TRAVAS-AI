"""Sanchalak Agent - Master Orchestrator

Sanchalak (संचालक) means "Conductor/Orchestrator" in Hindi.
Chats naturally with travelers and routes to specialist agents using shared state.
Uses AgentRegistry factory pattern for agent instantiation and Claude for conversation.
"""

import os
from typing import Optional, Dict, List
import anthropic

from agents.registry import AgentRegistry
from agents.shared_state import get_state_manager
from utils.logger import get_logger

logger = get_logger(__name__)


class SanchalakAgent:
    """Master orchestrator that chats naturally and coordinates specialist agents"""

    SYSTEM_PROMPT = """You are Sanchalak (संचालक - Conductor/Orchestrator), the master travel assistant.

Your role is to:
1. Chat naturally with travelers to understand their needs
2. Identify which specialist agents they need (hotels, food, tours, transport, shopping)
3. Route queries to appropriate specialists
4. Synthesize recommendations from multiple agents into cohesive itineraries

## HOW YOU WORK

PHASE 1: UNDERSTAND THE JOURNEY
Ask about destination, dates, travelers, and trip type. Gather info naturally across 2-3 turns.

PHASE 2: IDENTIFY SPECIALISTS NEEDED
Based on trip type, determine which agents help:
- Atithi → Hotels/accommodation (everyone)
- Annapurna → Food/restaurants (if interested in dining)
- Yatra → Tours/attractions (if interested in activities)
- Safar → Transport (if needs flights/trains/local travel)
- Bazaar → Shopping (if interested in shopping)

PHASE 3: COORDINATE SPECIALISTS
When routing, explicitly say:
"Let me check with my hotel specialist (Atithi) about..."
"My food expert (Annapurna) can recommend..."

PHASE 4: SYNTHESIZE
Connect recommendations: "Hotel X is near Attraction Y, and Restaurant Z is walking distance"

## CONVERSATION RULES

✅ Ask 1-2 questions per turn
✅ Remember what they said earlier
✅ Route when user asks about specific topics
✅ Synthesize multi-agent responses
✅ Acknowledge preferences and constraints
✅ Provide alternatives

❌ Don't overwhelm with all agents at once
❌ Don't forget earlier messages
❌ Don't route before understanding basic needs
❌ Don't ask same question twice

## ROUTING KEYWORDS

Route to ATITHI (hotels) when user mentions:
"hotel", "accommodation", "stay", "room", "resort", "booking", "where to stay"

Route to ANNAPURNA (food) when user mentions:
"restaurant", "food", "eat", "dining", "cuisine", "vegetarian", "breakfast"

Route to YATRA (tours) when user mentions:
"attraction", "tour", "visit", "sightseeing", "activity", "what to see", "place"

Route to SAFAR (transport) when user mentions:
"flight", "train", "bus", "transport", "taxi", "travel", "how to get"

Route to BAZAAR (shopping) when user mentions:
"shopping", "shop", "mall", "market", "buy", "souvenir"

## IMPORTANT

Only route when:
1. User asks specific question about an agent's domain
2. You've gathered enough context
3. User explicitly asks for that specialist

For general questions, chat naturally without routing."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Sanchalak with Claude, specialist agents, and shared state

        Args:
            api_key: Anthropic API key
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-opus-4-8"

        # Initialize available agents from registry
        self.agents = {}
        for agent_name in AgentRegistry.list_agents():
            try:
                self.agents[agent_name] = AgentRegistry.get(agent_name, api_key=self.api_key)
                logger.info(f"Loaded specialist: {agent_name}")
            except Exception as e:
                logger.error(f"Failed to load specialist '{agent_name}': {str(e)}")

        # Track which agent was used
        self.last_agent_used = None
        self.conversation_history = []

        # Initialize shared state manager
        self.state_manager = get_state_manager()

    def _extract_and_update_preferences(self, message: str) -> None:
        """Extract travel info from user message and update shared state.

        Args:
            message: User message
        """
        try:
            import re
            from datetime import datetime, timedelta

            # Try to extract common patterns from the message
            message_lower = message.lower()
            updates = {}

            # Extract destination and source cities
            # Destination cities
            if "goa" in message_lower:
                updates["destination"] = "Goa"
            if "north goa" in message_lower:
                updates["accommodation_area"] = "North Goa"
            if "south goa" in message_lower:
                updates["accommodation_area"] = "South Goa"

            # Source/departure cities (look for cities mentioned at start or after keywords)
            source_cities = ["bangalore", "bengaluru", "delhi", "mumbai", "pune", "kolkata", "hyderabad", "chennai", "kochi", "ahmedabad"]
            for city in source_cities:
                if city in message_lower:
                    # Check if it's likely a departure city (mentioned near keywords like "from", "departing", or standalone)
                    if f"from {city}" in message_lower or f"{city}," in message_lower or message_lower.startswith(city):
                        updates["source_city"] = city.capitalize()
                        break

            # Extract budget (look for ₹ or INR patterns, pick largest number)
            budget_matches = re.findall(r'₹?([\d,]+)\s*(?:inr|rupees?)?', message, re.IGNORECASE)
            if budget_matches:
                # Take the largest number (usually the main budget)
                budget_values = [int(b.replace(',', '')) for b in budget_matches if int(b.replace(',', '')) > 100]
                if budget_values:
                    updates["budget"] = float(max(budget_values))

            # Extract number of days (look for "5 days", "5-day", etc.)
            days_match = re.search(r'(\d+)\s*(?:days?|day\s+trip)', message_lower)
            if days_match:
                num_days = int(days_match.group(1))
                updates["num_days"] = num_days

                # If we have check-in date, calculate check-out date
                current_prefs = self.state_manager.get_preferences()
                if current_prefs.get("checkin_date"):
                    try:
                        # Parse check-in date (e.g., "25 Jul")
                        checkin_str = current_prefs["checkin_date"]
                        # Assume current year
                        checkin_date = datetime.strptime(f"{checkin_str} 2026", "%d %b %Y")
                        checkout_date = checkin_date + timedelta(days=num_days)
                        updates["checkout_date"] = checkout_date.strftime("%d %b").lstrip("0")
                    except:
                        pass

            # Extract dates (look for "25th", "July", patterns)
            if any(month in message_lower for month in ["july", "jul", "august", "aug", "september", "sep"]):
                # Simple pattern: extract first date-like mention
                date_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s*([a-z]+)', message_lower)
                if date_match:
                    day_str = date_match.group(1)
                    month_str = date_match.group(2)
                    # Store in consistent format
                    updates["checkin_date"] = f"{day_str} {month_str.capitalize()}"

                    # If num_days is already known, calculate checkout
                    if "num_days" in updates:
                        try:
                            checkin_date = datetime.strptime(f"{day_str} {month_str.capitalize()} 2026", "%d %b %Y")
                            checkout_date = checkin_date + timedelta(days=updates["num_days"])
                            updates["checkout_date"] = checkout_date.strftime("%d %b").lstrip("0")
                        except:
                            pass

            # Extract travelers (look for "couple", "2 people", etc.)
            if "couple" in message_lower:
                updates["num_adults"] = 2

            # Update shared state with all extracted info at once
            if updates:
                self.state_manager.update_preferences(updates)
                logger.info(f"Updated preferences: {updates}")
        except Exception as e:
            logger.debug(f"Error extracting preferences: {str(e)}")
            pass

    def _identify_routing_intent(self, message: str) -> Optional[str]:
        """Identify if message should be routed to a specialist.

        Args:
            message: User message

        Returns:
            agent_name if routing needed, None otherwise
        """
        message_lower = message.lower()

        routing_keywords = {
            "atithi": ["hotel", "accommodation", "stay", "room", "resort", "booking", "lodge"],
            "annapurna": ["restaurant", "food", "eat", "dining", "cuisine", "breakfast", "vegetarian"],
            "yatra": ["attraction", "tour", "visit", "sightseeing", "activity", "what to see", "place"],
            "safar": ["flight", "train", "bus", "transport", "taxi", "travel", "how to get"],
            "bazaar": ["shopping", "shop", "mall", "market", "buy", "souvenir"],
        }

        # Check keyword matches
        for agent_name, keywords in routing_keywords.items():
            for keyword in keywords:
                if keyword in message_lower and agent_name in self.agents:
                    logger.info(f"Routing to {agent_name} (matched: {keyword})")
                    return agent_name

        return None

    def _route_to_specialist(self, agent_name: str, message: str) -> str:
        """Route message to specialist agent with full context.

        Args:
            agent_name: Name of specialist agent
            message: User message

        Returns:
            Specialist's response
        """
        if agent_name not in self.agents:
            return f"I don't have a specialist for that yet."

        agent = self.agents[agent_name]
        self.last_agent_used = agent_name

        try:
            # Enrich message with shared state context
            state = self.state_manager.get_state()
            prefs = state["travel_preferences"]

            context_info = []
            if prefs.get("source_city"):
                context_info.append(f"Departing from: {prefs['source_city']}")
            if prefs.get("destination"):
                context_info.append(f"Destination: {prefs['destination']}")
            if prefs.get("accommodation_area"):
                context_info.append(f"Accommodation area: {prefs['accommodation_area']}")
            if prefs.get("checkin_date"):
                context_info.append(f"Check-in: {prefs['checkin_date']}")
            if prefs.get("checkout_date"):
                context_info.append(f"Check-out: {prefs['checkout_date']}")
            if prefs.get("num_days"):
                context_info.append(f"Trip duration: {prefs['num_days']} days")
            if prefs.get("num_adults") or prefs.get("num_children"):
                adults = prefs.get("num_adults", 0)
                children = prefs.get("num_children", 0)
                context_info.append(f"Travelers: {adults} adults, {children} children")
            if prefs.get("budget"):
                # Format budget nicely
                budget = prefs['budget']
                if budget > 1000:
                    context_info.append(f"Budget: ₹{budget:,.0f}")
                else:
                    context_info.append(f"Budget: ₹{budget}")
            if prefs.get("preferred_activities"):
                context_info.append(f"Interests: {', '.join(prefs['preferred_activities'])}")

            enriched_message = message
            if context_info:
                enriched_message = f"""
CONTEXT FROM EARLIER CONVERSATION:
{' | '.join(context_info)}

USER REQUEST:
{message}
"""

            response = agent.chat(enriched_message)
            logger.info(f"Specialist {agent_name} responded")
            return response
        except Exception as e:
            logger.error(f"Specialist {agent_name} error: {str(e)}")
            return f"My {agent_name} specialist encountered an issue. Please try again."

    def route_query(self, message: str) -> str:
        """Process user query: chat naturally or route to specialist.

        Args:
            message: User message

        Returns:
            Response from Sanchalak or routed specialist
        """
        if not message or not message.strip():
            return "Hi! I'm Sanchalak, your travel coordinator. Where are you planning to travel?"

        try:
            # Add to shared state
            self.state_manager.add_message("user", message, agent="sanchalak")
            self.state_manager.set_active_agent("sanchalak")
            self.state_manager.state["orchestrator_active"] = True

            # Extract and update travel preferences from this message
            self._extract_and_update_preferences(message)

            # Add to local history
            self.conversation_history.append({"role": "user", "content": message})

            # Check if we should route to a specialist
            routing_intent = self._identify_routing_intent(message)

            if routing_intent:
                # Route to specialist
                specialist_response = self._route_to_specialist(routing_intent, message)
                response = f"Let me check with my {routing_intent} specialist...\n\n{specialist_response}"

                # Update shared state
                self.state_manager.add_message("assistant", response, agent="sanchalak")
                self.state_manager.update_agent_response("sanchalak", response)
                self.state_manager.add_metadata("last_routing", {
                    "orchestrator": "sanchalak",
                    "routed_to": routing_intent
                })

                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            else:
                # Chat naturally without routing
                claude_response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=self.SYSTEM_PROMPT,
                    messages=self.conversation_history
                )

                response_text = claude_response.content[0].text

                # Update shared state
                self.state_manager.add_message("assistant", response_text, agent="sanchalak")
                self.state_manager.update_agent_response("sanchalak", response_text)

                self.conversation_history.append({"role": "assistant", "content": response_text})
                return response_text

        except Exception as e:
            logger.error(f"Route query error: {str(e)}")
            error_msg = f"I encountered an error: {str(e)}"
            self.state_manager.add_message("assistant", error_msg, agent="sanchalak")
            return error_msg

    def chat(self, message: str) -> str:
        """Chat interface - main entry point.

        Chats naturally with Claude, routing to specialists as needed.

        Args:
            message: User message

        Returns:
            Sanchalak's response or routed specialist response
        """
        return self.route_query(message)

    def get_orchestrator_info(self) -> Dict:
        """Get orchestrator status"""
        return {
            "name": "Sanchalak",
            "role": "Master Orchestrator",
            "model": self.model,
            "available_specialists": list(self.agents.keys()),
            "last_specialist_used": self.last_agent_used,
            "conversation_turns": len(self.conversation_history),
            "specialists_status": {
                agent_name: agent.get_agent_info()
                for agent_name, agent in self.agents.items()
            }
        }

    def get_status(self) -> Dict:
        """Get trip planning status."""
        state = self.state_manager.get_state()
        prefs = state["travel_preferences"]

        return {
            "active_specialists": state["active_agents"],
            "destination": prefs["destination"],
            "dates": f"{prefs['checkin_date']} to {prefs['checkout_date']}",
            "travelers": f"{prefs['num_adults']} adults, {prefs['num_children']} children",
            "budget": prefs["budget"],
            "conversation_turns": len(self.conversation_history),
            "messages_in_state": len(state["conversation_history"])
        }

    def get_shared_preferences(self) -> Dict:
        """Get current travel preferences from shared state."""
        return dict(self.state_manager.get_preferences())

    def get_conversation_context(self) -> Dict:
        """Get full conversation context from shared state."""
        return self.state_manager.get_agent_context("sanchalak")

    def get_active_agents(self) -> List[str]:
        """Get list of active agents from shared state."""
        return self.state_manager.get_state()["active_agents"]

    def get_all_agent_responses(self) -> Dict:
        """Get responses from all agents."""
        return self.state_manager.get_state()["agent_responses"]

    def reset(self) -> None:
        """Reset all agents and history"""
        for agent in self.agents.values():
            agent.reset()
        self.last_agent_used = None
        self.conversation_history = []
        self.state_manager.state["orchestrator_active"] = False
        logger.info("Sanchalak orchestrator reset")

    def __repr__(self) -> str:
        return f"<SanchalakAgent model='{self.model}' specialists={len(self.agents)} last_used={self.last_agent_used}>"

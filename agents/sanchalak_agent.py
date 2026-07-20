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

        # Initialize available conversational specialists from registry.
        # Yojana (synthesizer) and Parikshak (validator) are excluded here -
        # they're orchestration-only agents never reached via
        # _identify_routing_intent's keyword routing, and are owned/driven
        # separately by the app layer (e.g. streamlit_app.py) once enough
        # specialist recommendations have been gathered.
        CONVERSATIONAL_SPECIALISTS = {"atithi", "annapurna", "yatra", "safar", "bazaar"}
        self.agents = {}
        for agent_name in AgentRegistry.list_agents():
            if agent_name not in CONVERSATIONAL_SPECIALISTS:
                continue
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
        """Extract travel info from user message using Claude and update shared state.

        Uses an LLM call instead of hardcoded regex/keyword matching so it
        generalizes to ANY destination, city, phrasing, or traveler description
        (not just Goa / specific hardcoded cities).

        Args:
            message: User message
        """
        try:
            import json
            import re
            from datetime import datetime, timedelta

            current_prefs = self.state_manager.get_preferences()
            known = {k: v for k, v in current_prefs.items() if v is not None}

            extraction_prompt = f"""Extract travel planning details from the user's message below. Return ONLY a valid JSON object, no other text, no markdown code fences.

Already known info (do not repeat unless it changed): {json.dumps(known)}

User message: "{message}"

Return a JSON object with ONLY the NEW or UPDATED fields found in this message (omit fields not mentioned here):
{{
  "destination": "city/place name if mentioned (e.g. Delhi, Goa, Jaipur)",
  "source_city": "departure/origin city if mentioned",
  "accommodation_area": "specific neighborhood/area for stay if mentioned (e.g. North Goa, Candolim)",
  "checkin_date": "date in 'DD Mon' format if mentioned, e.g. '25 Jul'",
  "num_days": integer trip duration in days if mentioned,
  "num_adults": integer count of adult travelers if determinable from context,
  "num_children": integer count of children if mentioned,
  "budget": numeric budget value if a rupee amount is mentioned,
  "preferred_activities": ["list", "of", "interests"] if mentioned
}}

Rules:
- Only include a field if the message provides new/updated information for it.
- For traveler counts: "couple" = 2 adults; "family of 4" = 4 adults (use judgment); "me, wife, elderly parents" = 4 adults; explicit numbers like "4 people" = 4 adults unless children are specified separately.
- If nothing is extractable, return {{}}.
- Output must be valid JSON only."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": extraction_prompt}]
            )

            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            ).strip()

            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if not json_match:
                return

            extracted = json.loads(json_match.group(0))
            if not extracted:
                return

            # Calculate checkout_date if we now know checkin_date + num_days
            checkin_str = extracted.get("checkin_date") or current_prefs.get("checkin_date")
            num_days = extracted.get("num_days") or current_prefs.get("num_days")
            if checkin_str and num_days:
                try:
                    checkin_date = datetime.strptime(f"{checkin_str} 2026", "%d %b %Y")
                    checkout_date = checkin_date + timedelta(days=int(num_days))
                    extracted["checkout_date"] = checkout_date.strftime("%d %b").lstrip("0")
                except Exception:
                    pass

            self.state_manager.update_preferences(extracted)
            logger.info(f"Updated preferences via LLM extraction: {extracted}")
        except Exception as e:
            logger.debug(f"Error extracting preferences: {str(e)}")
            pass

    def _identify_routing_intent(self, message: str) -> Optional[str]:
        """Identify if message should be routed to a specialist.

        Uses whole-word matching (regex word boundaries) so keywords like
        "eat" don't false-positive match inside unrelated words like "great",
        "bus" inside "business", or "mall" inside "smaller".

        Args:
            message: User message

        Returns:
            agent_name if routing needed, None otherwise
        """
        import re
        message_lower = message.lower()

        routing_keywords = {
            "atithi": ["hotel", "accommodation", "stay", "room", "resort", "booking", "lodge"],
            "annapurna": ["restaurant", "food", "eat", "dining", "cuisine", "breakfast", "vegetarian"],
            "yatra": ["attraction", "tour", "visit", "sightseeing", "activity", "what to see", "place"],
            "safar": ["flight", "train", "bus", "transport", "taxi", "travel", "how to get"],
            "bazaar": ["shopping", "shop", "mall", "market", "buy", "souvenir"],
        }

        # Check keyword matches using word boundaries to avoid substring false positives
        for agent_name, keywords in routing_keywords.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, message_lower) and agent_name in self.agents:
                    logger.info(f"Routing to {agent_name} (matched: {keyword})")
                    return agent_name

        return None

    def _route_to_specialist(self, agent_name: str, message: str) -> str:
        """Route message to specialist agent.

        Note: We pass the RAW user message here. Each specialist's own
        chat() method reads shared state directly and enriches the message
        with a "CONTEXT FROM EARLIER CONVERSATION" block itself. Enriching
        here as well would nest a second context block inside the first,
        wasting tokens and risking confused extraction - shared state is
        the single source of truth, and each specialist owns its own
        context-building from it.

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
            response = agent.chat(message)
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

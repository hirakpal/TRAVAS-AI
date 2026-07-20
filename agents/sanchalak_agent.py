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
When you intend to bring in a specialist, ANNOUNCE it or ASK first:
"Let me check with my hotel specialist (Atithi) about..."
"Want me to bring in my food expert (Annapurna)?"
Actual routing to specialists happens automatically outside this message based on
what you and the user say - you don't need to (and can't) call them yourself.

PHASE 4: SYNTHESIZE
Connect recommendations: "Hotel X is near Attraction Y, and Restaurant Z is walking distance"
Only do this AFTER real specialist responses have appeared in the conversation as
separate messages - never invent what a specialist "would" recommend.

🔴 If the user asks to finalize/create/generate "the itinerary" (or says something
like "sounds good", "lock it in", "finalise the itinerary"), do NOT write out a full
multi-day itinerary yourself, even using only real facts already in the
conversation. A dedicated agent (Yojana) builds and quality-checks the official
itinerary outside this chat turn and it will appear separately, with its own
validation. If you draft one here too, the user ends up with two different
"final" itineraries and the official one won't be what's actually saved/approved.
Just briefly acknowledge (e.g. "Great, finalizing that now!") and stop there.

## 🔴 CRITICAL: NEVER IMPERSONATE A SPECIALIST

You do NOT have access to any hotel, restaurant, attraction, transport, or shopping
data or tools yourself - only the 5 specialist agents do, and each is grounded in its
own mock database. You must NEVER write content in a specialist's voice ("Hi, I'm
Safar here...", "Atithi here! I recommend...") or invent specific hotel names, prices,
flight numbers, or attraction details yourself. If you do this, you are fabricating
information that looks authoritative but is entirely made up - this is worse than not
answering, because it misleads the traveler's real budget and planning decisions.

Your job in this conversation is ONLY to:
1. Gather trip preferences conversationally
2. Announce/offer which specialist(s) should be consulted next
3. Synthesize genuine specialist responses AFTER they appear as separate messages

If the user agrees to consult a specialist you just offered (e.g. replies "yes",
"yes both", "sure", "go ahead"), simply acknowledge briefly - do NOT write out what
you imagine that specialist would say. The real specialist response is generated
separately and will appear right after.

## CONVERSATION RULES

✅ Ask 1-2 questions per turn
✅ Remember what they said earlier
✅ Acknowledge preferences and constraints
✅ Provide alternatives
✅ Synthesize ONLY genuine specialist responses that have actually appeared

❌ Don't overwhelm with all agents at once
❌ Don't forget earlier messages
❌ Don't route before understanding basic needs
❌ Don't ask same question twice
❌ NEVER write fabricated specialist content in your own voice"""

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
  "num_rooms": integer number of hotel rooms needed if mentioned,
  "budget": numeric budget value if a rupee amount is mentioned,
  "dietary_restrictions": ["list", "of", "restrictions"] if mentioned (e.g. vegetarian, vegan, jain, gluten-free, no dietary preference should NOT be added as a restriction),
  "accessibility_needs": ["list", "of", "needs"] if mentioned (e.g. wheelchair access, elderly travelers needing less walking, mobility constraints),
  "preferred_activities": ["list", "of", "interests"] if mentioned
}}

Rules:
- Only include a field if the message provides new/updated information for it.
- For traveler counts: "couple" = 2 adults; "family of 4" = 4 adults (use judgment); "me, wife, elderly parents" = 4 adults; explicit numbers like "4 people" = 4 adults unless children are specified separately.
- Note: "elderly parents" or "senior travelers" traveling along is itself a signal worth adding to accessibility_needs (e.g. "comfortable pacing for elderly travelers"), even without an explicit accessibility request.
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

    def _identify_routing_intents(self, message: str) -> List[str]:
        """Decide which specialist(s) to route to for this message, using an
        LLM call that sees recent conversation context - not just keyword
        matching on the message in isolation.

        This replaces a purely keyword-based matcher, which could only
        recognize routing intent if the message literally contained a domain
        word like "hotel" or "flight". It could NOT recognize a reply like
        "yes both" to Sanchalak's own offer ("shall I bring in Safar and
        Atithi?") as routing intent - "yes both" contains no domain keyword.
        When that happened, the message fell through to Sanchalak's own
        free-form chat, which (per its system prompt's "coordinate
        specialists" instructions) would write fake "Hi, I'm Safar here..."
        narration with invented flight prices and hotel names, without ever
        actually calling those agents. This function is context-aware and
        can return multiple specialists at once (e.g. "yes both" -> both
        specialists that were just offered).

        Args:
            message: User message

        Returns:
            List of specialist names to route to (may be empty).
        """
        try:
            import json
            import re

            available = [a for a in ["atithi", "annapurna", "yatra", "safar", "bazaar"] if a in self.agents]
            if not available:
                return []

            recent_turns = self.conversation_history[-6:]
            recent_text = "\n".join(
                f"{t['role']}: {str(t['content'])[:300]}" for t in recent_turns
            )

            classify_prompt = f"""You are deciding which specialist agent(s) should be consulted next in a travel-planning conversation.

Available specialists: atithi (hotels), annapurna (food/restaurants), yatra (attractions/tours), safar (transport/flights/local travel), bazaar (shopping)

Recent conversation:
{recent_text}

Latest user message: "{message}"

Rules:
- If the latest user message is an affirmative/agreement (e.g. "yes", "yes both", "sure", "go ahead", "please do", "ok") replying to an assistant message that offered or named specific specialists, return exactly those specialists - even though the word "yes" itself names no domain.
- If the message explicitly asks about a domain (hotels, food, attractions, transport, shopping), return the matching specialist(s).
- If the message is just providing preference details (dates, budget, interests, traveler count) with no clear signal to consult a specialist right now, return an empty list - let the conversation continue gathering info.
- Return MULTIPLE specialists if the message clearly agrees to consult more than one at once.
- Only return names from this exact list: {available}

Return ONLY a JSON array of specialist names, e.g. ["safar", "atithi"] or []. No other text, no markdown."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[{"role": "user", "content": classify_prompt}]
            )
            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            ).strip()

            match = re.search(r'\[.*?\]', text, re.DOTALL)
            if not match:
                return []

            intents = json.loads(match.group(0))
            seen = set()
            result = []
            for name in intents:
                if name in available and name not in seen:
                    seen.add(name)
                    result.append(name)

            if result:
                logger.info(f"Routing to specialists: {result}")
            return result
        except Exception as e:
            logger.debug(f"Error identifying routing intents: {str(e)}")
            return []

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

            # Check if we should route to one or more specialists (context-aware,
            # not just keyword matching - see _identify_routing_intents docstring)
            routing_intents = self._identify_routing_intents(message)

            if routing_intents:
                # Route to each identified specialist for real, and concatenate
                # their GENUINE responses. Never synthesize this content ourselves.
                response_parts = []
                for agent_name in routing_intents:
                    specialist_response = self._route_to_specialist(agent_name, message)
                    response_parts.append(f"Let me check with my {agent_name} specialist...\n\n{specialist_response}")
                response = "\n\n---\n\n".join(response_parts)

                # Update shared state
                self.state_manager.add_message("assistant", response, agent="sanchalak")
                self.state_manager.update_agent_response("sanchalak", response)
                self.state_manager.add_metadata("last_routing", {
                    "orchestrator": "sanchalak",
                    "routed_to": routing_intents
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

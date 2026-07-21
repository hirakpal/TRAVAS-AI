"""Sanchalak Agent - Master Orchestrator

Sanchalak (संचालक) means "Conductor/Orchestrator" in Hindi.
Chats naturally with travelers and routes to specialist agents using shared state.
Uses AgentRegistry factory pattern for agent instantiation and Claude for conversation.
"""

import os
import re
from typing import Optional, Dict, List, Any
import anthropic

from agents.registry import AgentRegistry
from agents.shared_state import (
    get_state_manager, reset_state_manager,
    format_budget, is_real_itinerary, SPECIALIST_AGENT_NAMES,
)
from agents.yojana_agent import YojanaAgent
from agents.parikshak_agent import ParikshakAgent
from agents.feedback_handler import FeedbackHandler
from utils.logger import get_logger

logger = get_logger(__name__)


# --- Orchestration constants -------------------------------------------------
# Cheap whole-word/phrase pre-filter for "the user wants the full itinerary built
# now". A positive match is confirmed by an LLM context check before synthesis
# actually runs, so bare "yes"/"ok" answering an unrelated sub-question doesn't
# fire it.
FINALIZE_TRIGGER_KEYWORDS = [
    "yes", "ok", "okay", "approve", "approved", "confirm", "confirmed",
    "perfect", "sounds good", "looks good", "go ahead", "lock it in",
    "book it", "finalize", "finalise", "finalized", "finalised",
    "generate itinerary", "create itinerary", "make the itinerary",
]

MAX_REVISIONS = 3

WELCOME_MESSAGE = "Welcome to TRAVAS-AI! Tell me about your dream trip."

# Dimensions scored for the "Traveller DNA" radar, computed when a trip is finalized.
DNA_DIMENSIONS = ["Culture", "Food", "Adventure", "Nature", "Luxury", "Shopping", "Relaxation"]

# Deterministic backup for routing when the LLM intent classifier misses a bare
# affirmative reply to a specialist offer (e.g. "yes" answering "Shall I bring in
# Safar and Atithi?"). See _affirmative_reoffer_fallback.
_AFFIRMATIVE_REPLIES = {
    "yes", "y", "yeah", "yep", "yup", "ya", "sure", "ok", "okay", "okey",
    "please", "pls", "please do", "yes please", "go ahead", "go for it",
    "do it", "sounds good", "sounds great", "lets do it", "let's do it",
    "both", "yes both", "all", "all four", "proceed", "perfect", "great",
    "yes lets", "yes let's", "absolutely", "definitely",
}
# The prior assistant turn must actually be OFFERING to consult specialists for
# an affirmative to count as routing (so "yes" to a budget question doesn't route).
_OFFER_MARKERS = [
    "shall i", "bring in", "want me to", "should i", "check with", "consult",
    "start with", "let me bring", "loop in", "pull in", "bring my",
]
# Domain words that map an offered specialist name back to its agent key, so we
# can tell WHICH specialists the prior assistant turn named.
_SPECIALIST_DOMAIN_HINTS = {
    "atithi": ["atithi", "hotel", "hotels", "stay", "stays", "accommodation"],
    "annapurna": ["annapurna", "food", "restaurant", "restaurants", "dining", "cuisine"],
    "yatra": ["yatra", "tour", "tours", "attraction", "attractions", "sightseeing", "activities"],
    "safar": ["safar", "transport", "flight", "flights", "train", "trains", "getting around"],
    "bazaar": ["bazaar", "shopping", "shop", "shops", "market", "markets"],
}


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
Ask about destination, dates, travelers, and trip type. Gather info naturally, but ask only ONE question at a time - a single short question per message, then wait for the answer before asking the next.

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

✅ Ask EXACTLY ONE question per turn - never combine two questions into a single message
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
        # Yojana (synthesizer) and Parikshak (validator) are excluded from this
        # routing set - they're never reached via _identify_routing_intent's
        # keyword routing. They ARE owned by Sanchalak (built below) and driven
        # by the workflow methods once enough specialist input exists; they're
        # just not conversational specialists the user chats with directly.
        self.agents = {}
        for agent_name in AgentRegistry.list_agents():
            if agent_name not in SPECIALIST_AGENT_NAMES:
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

        # --- Full-lifecycle orchestration -----------------------------------
        # Sanchalak is THE orchestrator: besides routing the conversational
        # specialists above, it also drives the synthesis -> validation ->
        # approval phase. Yojana (synthesizer) and Parikshak (validator) are
        # deliberately NOT conversational specialists reached by routing - they
        # are owned here and invoked by the workflow methods (generate_itinerary,
        # approve, submit_revision, ...). This used to live in streamlit_app.py,
        # which coupled the workflow to one UI; keeping it here means any
        # frontend (Streamlit, FastAPI, WhatsApp, ...) drives the same logic.
        self.yojana = YojanaAgent(api_key=self.api_key)
        self.parikshak = ParikshakAgent(api_key=self.api_key)
        self.feedback_handler = FeedbackHandler()

        # Workflow/view state (formerly st.session_state)
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": WELCOME_MESSAGE}
        ]
        self.itinerary: Optional[Dict[str, Any]] = None
        self.itinerary_text: Optional[str] = None
        self.itinerary_ready: bool = False
        self.validation_result: Optional[str] = None
        self.structured_validation_issues: List[str] = []
        self.structured_validation_warnings: List[str] = []
        self.approval_state: str = "PENDING"
        self.revision_count: int = 0

        # Set when a check-in date is newly resolved, so the next reply can echo
        # the concrete date back to the traveler for confirmation.
        self._pending_date_confirmation: Optional[str] = None

        # Traveller DNA radar scores, computed when the trip is finalized.
        self.traveller_dna: Optional[Dict[str, int]] = None

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

            # Recent conversation context is essential here: a bare number in
            # the user's message (e.g. "all four and build") is meaningless
            # without knowing what question it's answering. Without this,
            # a reply to "want me to bring in all four specialists?" gets
            # misread as "4 travelers" and silently clobbers a correctly
            # extracted num_adults from earlier (e.g. "solo" -> 1). Mirrors
            # the same context-aware fix already applied to
            # _identify_routing_intents for the analogous "yes both" bug.
            recent_turns = self.conversation_history[-6:]
            recent_text = "\n".join(
                f"{t['role']}: {str(t['content'])[:300]}" for t in recent_turns
            )

            # The extractor MUST know today's date to resolve relative phrases
            # like "this weekend" / "next Friday". Without it, the model has no
            # anchor and guesses a wrong month (e.g. "this weekend" -> October).
            today = datetime.now()
            today_str = today.strftime("%A, %d %B %Y")

            extraction_prompt = f"""Extract travel planning details from the user's message below. Return ONLY a valid JSON object, no other text, no markdown code fences.

Today's date is {today_str}. Resolve ANY relative or informal date in the message ("this weekend", "next weekend", "next Friday", "tomorrow", "in 2 weeks", "end of the month", "first week of March") to an ACTUAL calendar date relative to today. "This weekend" = the upcoming Saturday. Never guess an unrelated month.

Already known info (do not repeat unless it changed): {json.dumps(known)}

Recent conversation (for context only - use this to understand what any bare numbers or short replies in the latest message actually refer to):
{recent_text}

Latest user message: "{message}"

Return a JSON object with ONLY the NEW or UPDATED fields found in this message (omit fields not mentioned here):
{{
  "destination": "city/place name if mentioned (e.g. Delhi, Goa, Jaipur)",
  "source_city": "departure/origin city if mentioned",
  "accommodation_area": "specific neighborhood/area for stay if mentioned (e.g. North Goa, Candolim)",
  "checkin_date": "the check-in/start date as 'DD Mon' (e.g. '25 Jul'), resolved to an ACTUAL date using today's date above for any relative phrase",
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
- For traveler counts: "couple" = 2 adults; "family of 4" = 4 adults (use judgment); "me, wife, elderly parents" = 4 adults; explicit numbers like "4 people"/"party of 4"/"4 of us" = 4 adults unless children are specified separately.
- IMPORTANT - do NOT extract num_adults from a bare number unless the recent conversation confirms that number is actually describing how many people are traveling. Check what question/offer the latest message is actually replying to first. E.g. if the assistant's last message asked "want me to bring in all four specialists?" and the user replies "all four and build" or "yes all four", that "four" refers to specialists being consulted, NOT the traveler count - do not set num_adults from it (leave it out of the JSON entirely so the already-known value, if any, is preserved). Similarly "day 4", "option 4", "room for 4" (rooms, not people) etc. are not traveler counts.
- If a message that already established a solo/couple/group traveler count earlier (see "Already known info") doesn't contain any new traveler-count language of its own, do NOT include num_adults in the output at all - never re-derive or guess it from an unrelated number.
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

            # If a check-in date was newly resolved this turn, stash a friendly
            # form (with weekday) so route_query can confirm the concrete date
            # back - the traveler may have said something relative ("this
            # weekend") that we interpreted, and should get a chance to correct.
            newly_checkin = extracted.get("checkin_date")
            if newly_checkin:
                try:
                    _y = datetime.now().year
                    _d = datetime.strptime(f"{newly_checkin} {_y}", "%d %b %Y")
                    if _d.date() < datetime.now().date():
                        _d = _d.replace(year=_y + 1)
                    self._pending_date_confirmation = _d.strftime("%A, %d %b %Y")
                except Exception:
                    self._pending_date_confirmation = str(newly_checkin)

            # Calculate checkout_date if we now know checkin_date + num_days
            checkin_str = extracted.get("checkin_date") or current_prefs.get("checkin_date")
            num_days = extracted.get("num_days") or current_prefs.get("num_days")
            if checkin_str and num_days:
                try:
                    # Use the current year, not a hardcoded one; if that date has
                    # already passed (a trip can't be in the past), roll to next
                    # year - e.g. today is December, trip is in January.
                    year = datetime.now().year
                    checkin_date = datetime.strptime(f"{checkin_str} {year}", "%d %b %Y")
                    if checkin_date.date() < datetime.now().date():
                        checkin_date = checkin_date.replace(year=year + 1)
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

    def _affirmative_reoffer_fallback(self, message: str) -> List[str]:
        """Deterministic recovery when _identify_routing_intents returns [] but
        the user clearly said 'yes' to a specialist offer.

        The LLM routing classifier occasionally misses a bare affirmative ("yes")
        replying to "Shall I bring in Safar and Atithi?". When it does, the turn
        dead-ends: Sanchalak's chat branch says "consulting them now..." but no
        specialist is ever actually called, so their recommendations never
        appear and the user is stuck. This recovers WITHOUT an LLM: if the latest
        message is a short affirmative AND the immediately preceding assistant
        turn was offering to consult specialists, route to exactly the ones that
        turn named (by name or domain word). Deterministic, so it can't miss the
        same way the classifier did.
        """
        available = [a for a in SPECIALIST_AGENT_NAMES if a in self.agents]
        if not available:
            return []

        # Is the latest message a short, content-free affirmative?
        norm = re.sub(r"[^a-z\s']", "", message.strip().lower()).strip()
        if not norm:
            return []
        words = norm.split()
        if len(words) > 5:
            return []
        if norm not in _AFFIRMATIVE_REPLIES and not any(w in _AFFIRMATIVE_REPLIES for w in words):
            return []

        # Find the most recent assistant turn.
        prev = None
        for turn in reversed(self.conversation_history):
            if turn.get("role") == "assistant":
                prev = str(turn.get("content", "")).lower()
                break
        if not prev:
            return []

        # Only a genuine SANCHALAK offer counts. A routed specialist's own answer
        # (prefixed "Let me check with my X specialist...") is NOT an offer, even
        # though it may contain an offer-ish phrase and mention other domains in
        # passing (e.g. a hotel writeup saying "great for your food interest,
        # near Orchard shopping"). Treating that as an offer is exactly what made
        # "i am ok" spuriously fan out to all five specialists.
        if "let me check with my" in prev:
            return []
        if not any(marker in prev for marker in _OFFER_MARKERS):
            return []

        # Match ONLY specialist proper names (atithi, safar, ...), which is how
        # Sanchalak's offers name them - NOT generic domain words like "food" or
        # "shopping", which appear incidentally in specialists' answers.
        offered = []
        for name in available:
            if re.search(r"\b" + re.escape(name) + r"\b", prev):
                offered.append(name)
        if offered:
            logger.info(f"Affirmative-reoffer fallback routing to: {offered}")
        return offered

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

            # Deterministic safety net: if the classifier missed a plain "yes"
            # replying to a specialist offer, recover it here so the turn never
            # dead-ends promising specialists that are never actually called.
            if not routing_intents:
                routing_intents = self._affirmative_reoffer_fallback(message)

            # If we just resolved a check-in date, confirm the concrete date back.
            date_confirm = self._pending_date_confirmation
            self._pending_date_confirmation = None

            if routing_intents:
                # Route to each identified specialist for real, and concatenate
                # their GENUINE responses. Never synthesize this content ourselves.
                response_parts = []
                for agent_name in routing_intents:
                    specialist_response = self._route_to_specialist(agent_name, message)
                    response_parts.append(f"Let me check with my {agent_name} specialist...\n\n{specialist_response}")
                response = "\n\n---\n\n".join(response_parts)
                if date_confirm:
                    response = f"📅 Just to confirm, I've got your check-in as **{date_confirm}** — let me know if that's not right.\n\n---\n\n{response}"

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
                # Chat naturally without routing. If we just resolved a date,
                # tell Sanchalak to confirm the concrete date in its reply so the
                # traveler can catch a misread of a relative phrase.
                system_prompt = self.SYSTEM_PROMPT
                if date_confirm:
                    system_prompt += (
                        f"\n\nIMPORTANT FOR THIS REPLY: you interpreted the traveler's travel "
                        f"date as {date_confirm}. Briefly confirm this exact date back to them "
                        f"(e.g. \"Just to confirm - checking in {date_confirm}?\") so they can "
                        f"correct it if it's wrong, then continue naturally."
                    )
                claude_response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=system_prompt,
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

    # ==================================================================
    # FULL-LIFECYCLE ORCHESTRATION
    # (routing above is only one phase; these methods drive the rest:
    #  synthesis -> contract validation -> quality check -> approval)
    # ==================================================================

    def send_message(self, user_input: str) -> Dict[str, Any]:
        """Handle one user chat turn end to end: route via the specialist layer,
        then auto-synthesize the itinerary if the user just confirmed they want
        it built. Mutates state; returns a small result dict.
        """
        if not user_input or not user_input.strip():
            return {"status": "noop"}

        self.messages.append({"role": "user", "content": user_input})

        try:
            response = self.chat(user_input)
            self.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return {"status": "error", "error": str(e)}

        result = {"status": "ok", "synthesized": False}

        # Only try synthesis if no real itinerary exists yet. Gated on
        # itinerary_ready (not raw itinerary_text) so a prior refusal never
        # permanently blocks a later real synthesis - the revise flow handles
        # updates once a real itinerary exists.
        if (not self.itinerary_ready
                and self._message_triggers_synthesis(user_input)
                and self._confirm_finalize_intent(user_input)):
            if self.generate_itinerary():
                result["synthesized"] = True
                self.messages.append({
                    "role": "system",
                    "content": (
                        f"🗺️ Itinerary created by Yojana!\n\n"
                        f"{self.itinerary_text[:500]}... (see full itinerary on the right →)"
                    ),
                })
            elif self.itinerary_text:
                # Yojana explained why it can't build a draft yet - surface it.
                self.messages.append({
                    "role": "system",
                    "content": f"⚠️ {self.itinerary_text[:500]}",
                })
            else:
                logger.info("Synthesis triggered but not enough context yet; skipping.")

        return result

    def _message_triggers_synthesis(self, text: str) -> bool:
        """Whole-word/phrase check for finalize-intent keywords in free text."""
        text_lower = text.lower()
        for kw in FINALIZE_TRIGGER_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                return True
        return False

    def _confirm_finalize_intent(self, user_input: str) -> bool:
        """Context-aware confirmation that this message really means 'generate
        the complete itinerary now' - not just agreement to a narrower
        sub-question ("shall I bring in Safar and Atithi?" -> "yes both").

        Reuses Sanchalak's own conversation_history/client - only called after
        the cheap keyword pre-filter matches, so it isn't an LLM call per turn.
        """
        try:
            recent = self.conversation_history[-6:]
            recent_text = "\n".join(
                f"{t['role']}: {str(t['content'])[:300]}" for t in recent
            )
            prompt = f"""Recent conversation:
{recent_text}

Latest user message: "{user_input}"

Does this message mean the user wants their COMPLETE trip itinerary generated/finalized right now - as opposed to just agreeing to a narrower sub-question (like consulting a specific specialist, answering a preference question, or confirming one detail)?

Reply with exactly one word: YES or NO."""
            response = self.client.messages.create(
                model=self.model,
                max_tokens=5,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(
                b.text for b in response.content if hasattr(b, "text")
            ).strip().upper()
            return text.startswith("YES")
        except Exception as e:
            logger.debug(f"finalize-intent classification error: {str(e)}")
            return False

    def can_generate_itinerary(self) -> bool:
        """Gate: is there enough context to synthesize an itinerary?

        Destination known AND at least 2 specialists have reported COMPLETE -
        i.e. actually delivered grounded recommendations (status == "complete",
        which itself requires the specialist to have grounded in real data), not
        merely appeared in agent_responses. This is the deterministic upgrade
        over the old 'at least 2 specialists responded' heuristic, which counted
        a specialist that only asked a clarifying question the same as one that
        returned real recommendations. Readiness is DERIVED from the stored
        per-specialist status - it is never a separately maintained flag, so it
        cannot go stale.
        """
        if not self.state_manager.get_preferences().get("destination"):
            return False
        return len(self.state_manager.get_completed_specialists()) >= 2

    def generate_itinerary(self) -> bool:
        """Run Yojana to draft (which also runs the forced structured
        contract-validation pass), then run Parikshak. Returns True only if
        Yojana produced a genuine draft (False when there isn't enough context
        AND when Yojana correctly refused to fabricate - callers must not claim
        success in either case).
        """
        if not self.can_generate_itinerary():
            return False

        state = self.state_manager.get_state()
        specialist_outputs = {
            "atithi": str(state["agent_responses"].get("atithi", "No hotel recommendations yet")),
            "annapurna": str(state["agent_responses"].get("annapurna", "No food recommendations yet")),
            "yatra": str(state["agent_responses"].get("yatra", "No attraction recommendations yet")),
            "safar": str(state["agent_responses"].get("safar", "No transport recommendations yet")),
            "bazaar": str(state["agent_responses"].get("bazaar", "No shopping recommendations yet")),
        }

        itinerary_text = self.yojana.create_itinerary(specialist_outputs)
        self.itinerary_text = itinerary_text
        is_real = is_real_itinerary(itinerary_text)
        self.itinerary_ready = is_real

        self.structured_validation_issues = list(self.yojana.structured_validation_issues)
        self.structured_validation_warnings = list(self.yojana.structured_validation_warnings)

        prefs = state["travel_preferences"]
        self.itinerary = {
            "destination": prefs.get("destination", "TBD"),
            "duration": f"{prefs.get('num_days', 'N/A')} days",
            "travelers": f"{prefs.get('num_adults', 0)} adults, {prefs.get('num_children', 0)} children",
            "budget": format_budget(prefs.get("budget")),
            "summary": itinerary_text,
        }

        if is_real:
            deterministic_findings = {
                "issues": self.structured_validation_issues,
                "warnings": self.structured_validation_warnings,
            }
            self.validation_result = self._run_validation(itinerary_text, prefs, deterministic_findings)
            self.approval_state = "CONDITIONAL"
        else:
            self.validation_result = None
            self.approval_state = "PENDING"

        return is_real

    def _run_validation(
        self, itinerary_text: str, prefs: dict, deterministic_findings: Optional[dict] = None
    ) -> str:
        """Run Parikshak's quality check, passing through the deterministic
        contract-validation findings so it treats real overlap/budget checks as
        confirmed facts rather than re-deriving them from prose."""
        try:
            return self.parikshak.validate_itinerary(
                itinerary_text, dict(prefs), deterministic_findings=deterministic_findings
            )
        except Exception as e:
            logger.error(f"Parikshak validation error: {str(e)}")
            return ("⚠️ Validation could not be completed automatically. Please review the "
                    "itinerary manually before approving.")

    def approve(self) -> Dict[str, Any]:
        """Approve the current itinerary, generating one first if none has
        genuinely been built yet (so we never declare 'approved' for nothing)."""
        if not self.itinerary_ready:
            if not self.generate_itinerary():
                self.messages.append({
                    "role": "system",
                    "content": ("⚠️ I don't have enough trip details yet to build an itinerary "
                                "(need at least a destination and two specialists' recommendations). "
                                "Please share more details in chat first, then approve."),
                })
                return {"status": "insufficient_context"}

        self.feedback_handler.process_user_feedback("I approve this itinerary.", self.itinerary)
        self.approval_state = "APPROVED"
        # Finalization updates the Traveller DNA radar from the approved trip.
        self.compute_traveller_dna()
        self.messages.append({
            "role": "system",
            "content": "✅ Itinerary approved and finalized! Ready for booking.",
        })
        return {"status": "approved"}

    def reject(self) -> Dict[str, Any]:
        """Reject the current itinerary and move to the post-reject fork."""
        _, details = self.feedback_handler.process_user_feedback(
            "I reject this itinerary.", self.itinerary
        )
        self.approval_state = "REJECTED"
        message = (
            details.get(
                "message",
                "Would you like to:\n1. Start fresh with new preferences?\n2. Make specific changes?",
            )
            if isinstance(details, dict)
            else "Would you like to:\n1. Start fresh with new preferences?\n2. Make specific changes?"
        )
        self.messages.append({"role": "system", "content": message})
        return {"status": "rejected"}

    def can_revise(self) -> bool:
        """Whether more revisions are allowed."""
        return self.revision_count < MAX_REVISIONS

    def resume_after_reject_make_changes(self) -> None:
        """Caller chose 'make changes' after a reject: restore a sensible
        approval_state so the itinerary panel doesn't stay stuck on REJECTED."""
        self.approval_state = "CONDITIONAL" if self.itinerary_ready else "PENDING"

    def submit_revision(self, feedback: str) -> Dict[str, Any]:
        """Apply a revision: generate a base itinerary first if none exists,
        then run Yojana.revise -> contract validation -> Parikshak, refreshing
        state. Returns a status the caller can branch on."""
        if not feedback or not feedback.strip():
            return {"status": "empty_feedback"}

        if not self.can_revise():
            return {"status": "max_revisions"}

        if not self.itinerary_ready:
            if not self.generate_itinerary():
                self.messages.append({
                    "role": "system",
                    "content": ("⚠️ I don't have an itinerary to revise yet (need at least a "
                                "destination and two specialists' recommendations). Please share "
                                "more details in chat first."),
                })
                return {"status": "insufficient_context"}

        self.feedback_handler.process_user_feedback(feedback, self.itinerary)
        self.revision_count += 1
        self.messages.append({
            "role": "user",
            "content": f"Revision {self.revision_count}: {feedback}",
        })

        try:
            revised_text = self.yojana.revise_itinerary(feedback)
            self.itinerary_text = revised_text
            if self.itinerary:
                self.itinerary["summary"] = revised_text
            self.structured_validation_issues = list(self.yojana.structured_validation_issues)
            self.structured_validation_warnings = list(self.yojana.structured_validation_warnings)
        except Exception as e:
            logger.error(f"Revision error: {str(e)}")
            self.messages.append({"role": "system", "content": f"❌ Revision failed: {str(e)}"})
            return {"status": "error", "error": str(e)}

        prefs = self.state_manager.get_preferences()
        deterministic_findings = {
            "issues": self.structured_validation_issues,
            "warnings": self.structured_validation_warnings,
        }
        self.validation_result = self._run_validation(self.itinerary_text, prefs, deterministic_findings)
        self.approval_state = "CONDITIONAL"
        self.messages.append({
            "role": "system",
            "content": (f"✅ Revision {self.revision_count}/{MAX_REVISIONS} complete — "
                        f"updated itinerary and quality check are ready on the right →"),
        })
        return {"status": "revised", "revision_count": self.revision_count}

    def get_view_state(self) -> Dict[str, Any]:
        """Everything a frontend needs to render the current trip, in one call -
        keeps the UI from reaching into internals field by field."""
        return {
            "messages": self.messages,
            "itinerary": self.itinerary,
            "itinerary_text": self.itinerary_text,
            "itinerary_ready": self.itinerary_ready,
            "validation_result": self.validation_result,
            "structured_validation_issues": self.structured_validation_issues,
            "structured_validation_warnings": self.structured_validation_warnings,
            "approval_state": self.approval_state,
            "revision_count": self.revision_count,
            "max_revisions": MAX_REVISIONS,
            "can_revise": self.can_revise(),
            "can_act": len(self.messages) > 1,
            # Per-specialist completion signal (the "traffic light") + the
            # derived readiness the gate uses.
            "specialist_status": dict(self.state_manager.get_state().get("agent_status", {})),
            "completed_specialists": self.state_manager.get_completed_specialists(),
            "traveller_dna": self.traveller_dna,
        }

    def compute_traveller_dna(self) -> None:
        """Score the finalized trip across DNA_DIMENSIONS (0-100 each) for the
        Traveller DNA radar. Called on finalization; safe no-op on any error."""
        text = self.itinerary_text or ""
        try:
            prefs = self.state_manager.get_preferences()
        except Exception:
            prefs = {}
        acts = prefs.get("preferred_activities") or []
        if not text and not acts:
            return
        try:
            import json
            prompt = (
                "Score this traveler's trip on each dimension from 0-100 by how strongly the "
                "itinerary and their stated interests emphasise it (0 = not at all, 100 = "
                "dominant theme).\n\n"
                f"Stated interests: {', '.join(acts) if acts else 'not specified'}\n\n"
                f"Itinerary:\n{text[:3000]}\n\n"
                f"Dimensions: {', '.join(DNA_DIMENSIONS)}.\n"
                "Return ONLY a JSON object mapping each dimension name to an integer 0-100."
            )
            resp = self.client.messages.create(
                model=self.model, max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            t = "".join(b.text for b in resp.content if hasattr(b, "text")).strip()
            m = re.search(r"\{.*\}", t, re.DOTALL)
            if not m:
                return
            data = json.loads(m.group(0))
            dna = {}
            for dim in DNA_DIMENSIONS:
                try:
                    dna[dim] = max(0, min(100, int(data.get(dim, 0))))
                except Exception:
                    dna[dim] = 0
            self.traveller_dna = dna
        except Exception as e:
            logger.debug(f"compute_traveller_dna error: {str(e)}")

    def get_debug_state(self) -> Dict[str, Any]:
        """Transparency snapshot: what the agents have actually captured and
        produced, plus RAG cache stats. Rendered in the 'Agent Data' panel."""
        try:
            prefs = {k: v for k, v in self.state_manager.get_preferences().items() if v is not None}
        except Exception:
            prefs = {}
        try:
            responses = self.state_manager.get_state().get("agent_responses", {})
            response_summary = {
                name: (str(resp)[:160] + "…") if resp and len(str(resp)) > 160 else str(resp)
                for name, resp in responses.items()
            }
        except Exception:
            response_summary = {}
        try:
            from data import live_rag
            cache_stats = live_rag.get_cache_stats()
        except Exception:
            cache_stats = {}
        return {
            "preferences": prefs,
            "agent_status": dict(self.state_manager.get_state().get("agent_status", {})),
            "agent_responses": response_summary,
            "cache_stats": cache_stats,
        }

    def suggest_replies(self, max_suggestions: int = 4) -> List[str]:
        """Short tappable quick-reply options for the assistant's LATEST message.

        Lets the UI render suggestion bubbles the traveler can tap instead of
        typing (e.g. after "Who's going?" -> Solo / Couple / Family / Friends).
        Returns [] when the latest message isn't asking something answerable with
        a short choice (e.g. after specialist recommendations), so the UI simply
        shows no bubbles. Kept out of get_view_state() because it makes its own
        small LLM call - the UI caches the result per assistant message.
        """
        last_assistant = None
        for m in reversed(self.messages):
            if m.get("role") == "assistant":
                last_assistant = str(m.get("content", ""))
                break
        if not last_assistant:
            return []
        try:
            import json
            prompt = (
                "In a travel-planning chat, the assistant just said:\n\n"
                f"\"{last_assistant[:800]}\"\n\n"
                f"Propose up to {max_suggestions} SHORT quick-reply options (each 1-4 words) the "
                "traveler could tap to answer the assistant's latest question. They must be "
                "natural, distinct answers to what was actually asked (e.g. for 'who is going?' "
                "-> [\"Solo\", \"Couple\", \"Family\", \"Friends\"]; for a yes/no offer -> "
                "[\"Yes, go ahead\", \"Not yet\"]). If the assistant is NOT asking the traveler "
                "something they'd answer with a short choice, return an empty array. "
                "Return ONLY a JSON array of strings, no other text."
            )
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(b.text for b in resp.content if hasattr(b, "text")).strip()
            match = re.search(r"\[.*\]", text, re.DOTALL)
            if not match:
                return []
            items = json.loads(match.group(0))
            out = []
            for it in items:
                if isinstance(it, str) and it.strip():
                    out.append(it.strip()[:40])
            return out[:max_suggestions]
        except Exception as e:
            logger.debug(f"suggest_replies error: {str(e)}")
            return []

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
        """Reset the whole trip: specialists, synthesizer/validator, feedback
        handler, shared state, and all workflow/view state. This is the single
        'New Trip' entry point for any frontend."""
        # Clear shared state IN PLACE (same StateManager object) so every agent
        # still holding a reference to it - the specialists, Yojana, Parikshak -
        # sees the cleared state. Creating a NEW manager here would desync them
        # from Sanchalak, since reset() reuses the existing agents rather than
        # rebuilding them.
        reset_state_manager()

        for agent in self.agents.values():
            agent.reset()
        self.yojana.reset()
        self.parikshak.reset()
        self.feedback_handler.reset()

        self.last_agent_used = None
        self.conversation_history = []
        self.state_manager.state["orchestrator_active"] = False

        # Workflow/view state
        self.messages = [{"role": "system", "content": WELCOME_MESSAGE}]
        self.itinerary = None
        self.itinerary_text = None
        self.itinerary_ready = False
        self.validation_result = None
        self.structured_validation_issues = []
        self.structured_validation_warnings = []
        self.approval_state = "PENDING"
        self.revision_count = 0
        self._pending_date_confirmation = None
        self.traveller_dna = None

        logger.info("Sanchalak orchestrator reset (full trip)")

    def __repr__(self) -> str:
        return f"<SanchalakAgent model='{self.model}' specialists={len(self.agents)} last_used={self.last_agent_used}>"

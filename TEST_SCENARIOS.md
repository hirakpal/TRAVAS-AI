# Atithi Agent - Test Scenarios

## How to Run Tests

### Quick Test (5 minutes)
```bash
cd D:\BuildfastwithAI\Capstone\TRAVAS-AI\main
python demo_atithi.py
# Select option 5: Interactive Mode
```

### Automated Tests (10 minutes)
```bash
python demo_atithi.py
# Select option 1: Basic Conversation (shows multi-turn)
# Select option 2: Streaming Responses
# Select option 3: Error Handling
```

---

## Test Scenario 1: Family Vacation Planning

**Traveler Profile:** Family with kids (Budget traveler)

**Script:**
```
User: "We're looking for a hotel in Goa for a family vacation"

Expected Agent Behavior:
✅ Warm greeting
✅ Identifies family traveler persona
✅ Asks for key info: dates, number of kids, budget
✅ Does NOT ask 20 questions at once

User: "We have 2 kids, ages 6 and 8. We'll be there July 25-30. Budget around ₹8000 per night"

Expected Agent Behavior:
✅ Acknowledges kids' ages
✅ Calculates duration (5 nights)
✅ Notes budget tier
✅ Asks about preferences: beach, activities, amenities

User: "The kids love water activities. We want a beach hotel with a pool and kids play area"

Expected Agent Behavior:
✅ Uses search_hotels tool (city=Goa, max_price=8000)
✅ Filters for family-friendly amenities
✅ Returns 2-3 family-suitable hotels
✅ Explains why each matches their needs

User: "Tell me more about the first one"

Expected Agent Behavior:
✅ Uses get_hotel_details tool
✅ Provides comprehensive info:
   - Rooms available
   - Pool, kids area, water activities
   - Bathroom type (doesn't guess)
   - Food options (vegetarian/non-veg)
   - Parking
   - Beach access
✅ Includes guest reviews summary
✅ Lists nearby attractions for kids
```

**What to Watch For:**
- ✅ Agent sounds like a concierge, not a bot
- ✅ No overwhelming questionnaire
- ✅ Natural conversation flow
- ✅ Persona-based recommendations
- ✅ Detailed, honest information
- ✅ Never asks for payment or booking

---

## Test Scenario 2: Business Traveler

**Traveler Profile:** Business traveler (Mid-range budget)

**Script:**
```
User: "I need a hotel in Delhi's business district for 2 nights"

Expected Agent Behavior:
✅ Efficient, professional tone
✅ Identifies business traveler persona
✅ Focuses on business-relevant amenities
✅ Asks: dates, budget, requirements

User: "August 10-12, budget ₹12000/night. I need conference facilities and WiFi"

Expected Agent Behavior:
✅ Notes business requirements
✅ Calls search_hotels (Delhi, max_price=12000)
✅ Prioritizes:
   - Central location
   - Conference rooms
   - High-speed WiFi
   - Early check-in capability
✅ Recommends 2-3 business-suitable hotels

User: "Do they have airport shuttle?"

Expected Agent Behavior:
✅ Checks hotel details
✅ Answers directly
✅ If not known: States "Information not available"
✅ Never fabricates amenities
```

**What to Watch For:**
- ✅ Professional, efficient tone
- ✅ Business-relevant prioritization
- ✅ Focus on convenience and productivity
- ✅ Honest about what's available/unavailable

---

## Test Scenario 3: Solo Female Traveler

**Traveler Profile:** Solo female traveler (Budget-conscious)

**Script:**
```
User: "Solo trip to Mumbai, need a safe place to stay. Budget ₹5000/night"

Expected Agent Behavior:
✅ Acknowledges safety as priority
✅ Empathetic, warm tone
✅ Identifies solo female persona
✅ Asks: dates, preferred area, amenities

User: "I'll be there Aug 5-8. I want somewhere in a busy area with good transport"

Expected Agent Behavior:
✅ Understands safety concerns
✅ Uses search_hotels (Mumbai, max_price=5000)
✅ Prioritizes:
   - Good locality/central area
   - Near public transport
   - 24-hour front desk (if available)
   - Safe neighborhood reviews
✅ Recommends hotels that match safety profile

User: "What about nearby shopping and restaurants?"

Expected Agent Behavior:
✅ Uses get_hotel_details
✅ Includes:
   - Nearby shopping areas
   - Restaurant options
   - Public transport connectivity
   - Guest feedback on safety
✅ Provides location context
```

**What to Watch For:**
- ✅ Empathetic to safety concerns
- ✅ Prioritizes female-traveler needs
- ✅ Good locality and transport emphasis
- ✅ Practical recommendations

---

## Test Scenario 4: Luxury Traveler

**Traveler Profile:** Luxury traveler (Premium experience)

**Script:**
```
User: "Looking for a luxury hotel in Delhi. Money is not a concern, I want the best"

Expected Agent Behavior:
✅ Understands premium expectations
✅ Identifies luxury traveler persona
✅ Asks: dates, specific preferences, must-haves

User: "September 1-5. I want 5-star, spa, fine dining, room service"

Expected Agent Behavior:
✅ Focuses on:
   - 5-star properties
   - Premium amenities (spa, fine dining)
   - Exceptional service (room service, concierge)
   - Unique experiences
✅ Uses search_hotels with luxury filters
✅ Recommends premium properties

User: "Which has the best reviews?"

Expected Agent Behavior:
✅ Reviews guest feedback
✅ Notes:
   - Service quality consistently praised
   - Room quality and cleanliness
   - Dining experience
   - Any trade-offs
✅ Explains rating objectively
```

**What to Watch For:**
- ✅ Focus on premium amenities
- ✅ Service quality emphasis
- ✅ Personalized experience understanding
- ✅ Premium price acceptance

---

## Test Scenario 5: Accessibility Needs

**Traveler Profile:** Senior traveler with mobility needs

**Script:**
```
User: "I need a hotel in Jaipur. I use a wheelchair, need accessible rooms"

Expected Agent Behavior:
✅ Takes accessibility seriously
✅ Asks: dates, type of accessibility needed, budget

User: "July 28-30. I need wheelchair accessible room, elevator, accessible bathroom"

Expected Agent Behavior:
✅ Prioritizes accessibility in search
✅ Uses filter_hotels with accessibility criteria
✅ Returns hotels that specifically support:
   - Wheelchair access
   - Accessible bathrooms
   - Elevator access
   - Staff trained for accessibility
✅ Never guesses bathroom type

User: "Can they assist with mobility needs at the hotel?"

Expected Agent Behavior:
✅ Checks available information
✅ If not confirmed: "Information not available"
✅ Recommends contacting hotel directly
✅ Never fabricates accessibility features
```

**What to Watch For:**
- ✅ Takes accessibility very seriously
- ✅ Never guesses/assumes access features
- ✅ Honest about what's verified
- ✅ Encourages direct contact for specifics

---

## Test Scenario 6: Dietary Requirements

**Traveler Profile:** Vegan traveler

**Script:**
```
User: "I'm planning a 3-day trip to Goa. I'm vegan and need good food options"

Expected Agent Behavior:
✅ Takes dietary needs seriously
✅ Identifies dietary traveler persona
✅ Asks: dates, budget, hotel preferences

User: "Aug 15-18, budget ₹6000/night. Need confirmed vegan options"

Expected Agent Behavior:
✅ Filters for vegan-friendly hotels
✅ Uses search_hotels + filter_hotels
✅ Returns hotels with:
   - Confirmed vegan menu
   - Vegetarian restaurants nearby
   - Dietary awareness
✅ Includes food options in recommendations

User: "How much vegetarian food options?"

Expected Agent Behavior:
✅ Provides details on:
   - Vegan menu items
   - Restaurants nearby
   - Kitchen's vegan knowledge
✅ If not confirmed: "Not known - recommend contacting hotel"
✅ Never assumes vegan availability
```

**What to Watch For:**
- ✅ Respects dietary requirements
- ✅ Never assumes/fabricates menu options
- ✅ Suggests contacting hotel for specifics
- ✅ Finds relevant alternatives

---

## Test Scenario 7: Error Handling

**What the agent should NOT do:**

```
❌ DON'T: "Enter all your preferences in one message"
✅ DO: Ask conversationally, one step at a time

❌ DON'T: "Toilet Type: Unknown" (without asking)
✅ DO: "I don't want to guess - would you prefer Indian or European toilet?"

❌ DON'T: "This hotel has amazing sea views" (if not verified)
✅ DO: Check hotel details, or state "Information not available"

❌ DON'T: "Ready to book? Click here!"
✅ DO: "Here's how to book directly: [contact info]"

❌ DON'T: Invent reviews
✅ DO: Summarize verified reviews or state "Not confirmed"

❌ DON'T: Guess prices
✅ DO: Show verified price range or "Price may vary"
```

**Test Script:**
```
User: "Find me a hotel"

Expected Agent Behavior:
✅ Asks: "Where are you traveling?"
✅ Then: "When would you like to check in?"
✅ Gradually gathers info
✅ Never bombards with 10 questions

User: "I don't know what bathroom type to prefer"

Expected Agent Behavior:
✅ Explains options simply
✅ Offers "No preference" option
✅ Helps user decide
✅ Never assumes

User: "Can I book through you?"

Expected Agent Behavior:
✅ Politely declines
✅ Provides booking methods:
   - Direct phone
   - Email
   - Hotel website
   - Booking platforms
✅ Stays as advisor, not booking agent
```

**What to Watch For:**
- ✅ Natural, non-pushy conversation
- ✅ Clear explanations of options
- ✅ Honest limitations
- ✅ Strong ethical boundaries

---

## Test Scenario 8: Multi-Turn Conversation

**Testing Memory & Context:**

```
Turn 1:
User: "Hotel in Delhi"
Agent: Asks for details

Turn 2:
User: "5 nights, family with 2 kids"
Agent: ✅ Remembers: family traveler, 2 kids

Turn 3:
User: "Kids love swimming"
Agent: ✅ Combines: family + swimming = pool requirement

Turn 4:
User: "Actually, vegetarian food is important"
Agent: ✅ Adds to profile: family + kids + pool + vegetarian

Turn 5:
User: "Show recommendations"
Agent: ✅ Searches with all combined preferences
        ✅ Ranks based on full persona
        ✅ Never forgets earlier info
```

**What to Watch For:**
- ✅ Agent remembers all previous info
- ✅ Builds profile incrementally
- ✅ Uses cumulative preferences for search
- ✅ No repeated questions

---

## Expected Quality Metrics

After testing, evaluate:

| Metric | Expected | How to Verify |
|--------|----------|---------------|
| **Response Time** | < 2 seconds | Use stopwatch |
| **Accuracy** | > 90% matches | Compare recommendations to preferences |
| **Conversation Flow** | Natural | Does it feel like talking to a person? |
| **Information Completeness** | 80%+ fields | Check each recommendation |
| **Ethical Adherence** | 100% | No fabrication, no bookings, no guessing |
| **Persona Identification** | Accurate | Does agent tailor to traveler type? |

---

## Test Checklist

### Phase 1: Basic Functionality (10 mins)
- [ ] Agent starts and responds
- [ ] Can understand different cities
- [ ] Searches return results
- [ ] Details are accurate (verified from mock data)
- [ ] No errors in chat

### Phase 2: Conversation Quality (15 mins)
- [ ] Tone feels warm and professional
- [ ] Questions are asked naturally
- [ ] Doesn't repeat questions
- [ ] Explains recommendations
- [ ] Remembers preferences

### Phase 3: Persona Recognition (15 mins)
- [ ] Identifies family travelers
- [ ] Identifies business travelers
- [ ] Identifies solo travelers
- [ ] Identifies luxury travelers
- [ ] Adjusts recommendations by persona

### Phase 4: Recommendation Quality (15 mins)
- [ ] Hotels match preferences
- [ ] Ranking makes sense
- [ ] Explanations are clear
- [ ] Pros and cons provided
- [ ] Comparisons are accurate

### Phase 5: Error Handling (10 mins)
- [ ] Handles empty input gracefully
- [ ] Explains when info isn't available
- [ ] Never guesses amenities/prices
- [ ] Refuses to book (stays as advisor)
- [ ] Suggests alternatives

### Phase 6: Information Completeness (15 mins)
- [ ] Provides room types
- [ ] Lists amenities
- [ ] Shows parking options
- [ ] Includes food options
- [ ] States policies
- [ ] Mentions nearby attractions

---

## Sample Test Run

**Expected Interaction:**

```
🚀 Starting Atithi Agent Test

👤 User: I'm looking for a hotel in Mumbai for a weekend getaway

🤖 Atithi: How wonderful! I'd love to help you find the perfect hotel for your weekend.
Let me gather a few quick details:

- What dates are you planning to visit?
- How many people will be traveling?
- Do you have a budget in mind, or should I explore options across different price points?

👤 User: Aug 10-12, 2 people, around 8000 per night

🤖 Atithi: Perfect! A romantic weekend getaway for two. August 10-12 gives us 2 nights.

Just a couple more things to help me find the best match:
- Are you looking for a specific type of experience? (Beach, city center, luxury, cozy, etc.)
- Any particular amenities that are important? (Pool, gym, spa, etc.)

👤 User: Beach with pool would be great. We want something nice but not too expensive

🤖 Atithi: Excellent! Let me search for beachfront and near-beach hotels in Mumbai with pools, 
in your budget range...

[Uses search_hotels tool]

I found 3 excellent options for you:

1. **Beachfront Paradise Mumbai**
   Location: Bandra, Mumbai
   Price: ₹10,000/night
   Star Rating: 4.5/5 (342 reviews)
   
   Why it's perfect for you: Premium beachfront location with stunning Arabian Sea views,
   excellent pool, and romantic ambiance. Guests consistently praise the food and service.
   
   Rooms: Double, Deluxe (with sea view)
   Bed: King bed
   Bathroom: European style
   Amenities: WiFi, Pool, Beach access, Restaurant, Spa
   Parking: Free valet parking
   Food: Multi-cuisine, good vegetarian options
   
   Pros: Beachfront location, beautiful views, romantic setting, excellent reviews
   Consideration: Price slightly above budget - may be worth the experience

2. **City Beach Resort**
   Location: Near Bandra Beach
   Price: ₹7,500/night
   Star Rating: 4.0/5
   
   Why it's perfect: Great value near beach with pool, modern rooms, good service
   
   [Full details...]
   
   Pros: Within budget, pool, near beach
   Consideration: Not directly beachfront, slightly smaller

👤 User: Tell me more about the first one

🤖 Atithi: [Uses get_hotel_details tool]
[Provides comprehensive information...]

👤 User: Looks good, how do I book?

🤖 Atithi: I'm so glad you like it! Here are your booking options:

Direct Booking:
- Phone: +91-22-6789-1234
- Email: reserve@beachfrontparadise.com
- Website: www.beachfrontparadise.com

Online Booking:
- Booking.com
- OYO Rooms
- Their official website

I recommend calling them directly for potential weekend specials. Is there anything 
else you'd like to know about the hotel or other options?
```

---

## Common Issues & Fixes

**Issue: Agent fabricates amenities**
- Fix: Uses get_hotel_details tool to pull verified data only

**Issue: Asks too many questions at once**
- Fix: Uses conversational style, asks progressively

**Issue: Tries to process booking**
- Fix: System prompt explicitly forbids booking attempts

**Issue: Forgets previous preferences**
- Fix: Maintains conversation history automatically

**Issue: Poor recommendations**
- Fix: Smart ranking by need-match, not just rating

---

## Ready to Test?

1. **Setup:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Test locally:**
   ```bash
   python demo_atithi.py
   ```

3. **Choose scenario:**
   - Option 1: Basic conversation
   - Option 5: Interactive mode (best for manual testing)

4. **Use scenarios above** as conversation starters

5. **Evaluate** against quality metrics

---

**Start testing and let me know the results!** 🧪✅

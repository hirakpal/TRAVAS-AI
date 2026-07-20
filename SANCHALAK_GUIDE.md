# Sanchalak (Orchestrator) - Simple Guide

**Sanchalak** (संचालक) = "Conductor/Orchestrator" in Hindi

The master agent that routes queries to specialist agents.

---

## 🎯 What Does Sanchalak Do?

Simple job: **Understand → Route → Respond**

```
User: "I need a hotel in Goa"
   ↓
Sanchalak: "This is about hotels → Send to Atithi"
   ↓
Atithi: "Here are hotel recommendations..."
   ↓
Sanchalak: "Got response → Send to user"
```

---

## 🏗️ How It Works (Simple)

### **1. Identify Intent**
```python
message = "I need a hotel in Goa"

# Check keywords
if "hotel" in message:
    agent = "atithi"
```

### **2. Route to Agent**
```python
agent = agents["atithi"]
response = agent.chat(message)
```

### **3. Return Response**
```python
return response  # User gets the answer
```

That's it! Simple.

---

## 📝 Code Structure

```python
class SanchalakAgent:
    def __init__(self):
        self.agents = {
            "atithi": AtithiAgent(),
            # Add more agents here later
        }
    
    def identify_intent(message):
        # Check keywords
        # Return agent name
    
    def route_query(message):
        # Find agent
        # Get response
        # Track history
        # Return response
    
    def chat(message):
        # Simple interface
        # Calls route_query
```

---

## 🚀 How to Use

### **Quick Chat**
```bash
from agents.sanchalak_agent import SanchalakAgent

orchestrator = SanchalakAgent(api_key="your-key")

response = orchestrator.chat("I need a hotel in Goa")
print(response)
```

### **Multiple Queries**
```python
orchestrator = SanchalakAgent(api_key="your-key")

# Query 1 → Goes to Atithi
orchestrator.chat("Hotel in Delhi")

# Query 2 → Still Atithi
orchestrator.chat("Budget option preferred")

# Query 3 → Still Atithi (multi-turn)
orchestrator.chat("Near airport please")
```

### **Demo**
```bash
python demo_sanchalak.py
# Select: 1, 2, or 3
```

---

## 🎛️ Intent Recognition

### **Current Keywords**

| Agent | Keywords |
|-------|----------|
| **Atithi** | hotel, accommodation, stay, room, booking, resort, lodge |

### **Future Agents**

```python
# When built, add like this:
keywords = {
    "atithi": ["hotel", "stay", ...],
    "annapurna": ["restaurant", "food", "eat", ...],
    "yatra": ["attraction", "tour", "visit", ...],
    "safar": ["flight", "train", "bus", ...],
    "bazaar": ["shopping", "shop", "mall", ...],
}
```

---

## 📊 Current Status

| Component | Status |
|-----------|--------|
| **Route queries** | ✅ Working |
| **Track history** | ✅ Working |
| **Multi-turn** | ✅ Working |
| **Atithi integration** | ✅ Complete |
| **Error handling** | ✅ Robust |
| **Logging** | ✅ Structured |

---

## 🔌 Integration Example

### **With Node.js Gateway**
```javascript
// Node.js API endpoint
app.post('/api/travel-query', (req, res) => {
    const orchestrator = new SanchalakAgent();
    const response = orchestrator.chat(req.body.message);
    res.json({success: true, response});
});
```

### **With Frontend**
```javascript
// React component
const response = await fetch('/api/travel-query', {
    method: 'POST',
    body: JSON.stringify({message: userInput})
});
const data = await response.json();
showResponse(data.response);
```

---

## 🧩 Adding New Agents

When Annapurna (Food Agent) is built:

```python
# Step 1: Create the agent
class AnnapurnaAgent(BaseAgent):
    # Implementation
    pass

# Step 2: Add to Sanchalak
def __init__(self):
    self.agents = {
        "atithi": AtithiAgent(),
        "annapurna": AnnapurnaAgent(),  # NEW
    }

# Step 3: Add keywords
def identify_intent(message):
    keywords = {
        "atithi": ["hotel", "stay", ...],
        "annapurna": ["food", "restaurant", ...],  # NEW
    }
```

Done! The orchestrator will automatically route food queries to Annapurna.

---

## 📋 Methods

### **`chat(message)`**
Simple interface - just pass message, get response
```python
response = orchestrator.chat("Hotel in Goa")
```

### **`route_query(message)`**
Lower-level interface - get detailed info
```python
result = orchestrator.route_query("Hotel in Goa")
# Returns: {success, message, agent, history_count}
```

### **`identify_intent(message)`**
Returns which agent should handle this
```python
agent = orchestrator.identify_intent("I need a hotel")
# Returns: "atithi"
```

### **`get_orchestrator_info()`**
Get status
```python
info = orchestrator.get_orchestrator_info()
# Returns: {name, agents, last_used, history, etc}
```

### **`reset()`**
Clear all history
```python
orchestrator.reset()
# Clears all agents and history
```

---

## 🧪 Demo Output

### **Demo 1: Routing**
```
👤 User: "I need a hotel in Goa"
🎯 Sanchalak: Routing to appropriate agent...
🤖 Agent (atithi): [Hotel recommendations...]

👤 User: "We want a budget hotel in Delhi"
🎯 Sanchalak: Routing to appropriate agent...
🤖 Agent (atithi): [Hotel recommendations...]
```

### **Demo 2: Multi-Turn**
```
Turn 1:
👤 User: "Looking for a hotel in Goa"
🤖 Agent (atithi): [Response...]

Turn 2:
👤 User: "We have 2 kids"
🤖 Agent (atithi): [Response using previous context...]

Turn 3:
👤 User: "Budget around ₹8000"
🤖 Agent (atithi): [Response with accumulated context...]
```

### **Demo 3: Interactive**
```
👤 You: Hotel in Goa
🤖 atithi: [Response...]

👤 You: What about family rooms?
🤖 atithi: [Response...]

👤 You: status
📊 Status:
   Available agents: ['atithi']
   Last used: atithi
   Turns: 2

👤 You: quit
🎭 Goodbye!
```

---

## 📈 How It Scales

**Currently:** 1 Agent (Atithi)

**When complete:** 6 Agents
```
Sanchalak (Master)
├─ Atithi (Hotels) ✅
├─ Annapurna (Food)
├─ Yatra (Tours)
├─ Safar (Transport)
├─ Bazaar (Shopping)
└─ (Future agents)
```

Same orchestrator handles all - just add agents to the dictionary!

---

## ✅ Key Features

✅ **Simple** - ~100 lines of core code  
✅ **Extensible** - Easy to add agents  
✅ **No Complex Logic** - Just keyword matching  
✅ **Multi-Turn Support** - Agents maintain context  
✅ **Error Handling** - Graceful failures  
✅ **Logging** - Track what happens  
✅ **Testable** - Demo scenarios included  

---

## 🚀 Next Steps

1. **Test Sanchalak**
   ```bash
   python demo_sanchalak.py
   ```

2. **Build Annapurna (Food Agent)**
   - Same pattern as Atithi
   - Add restaurant/food tools
   - Register in Sanchalak

3. **Build Node.js Gateway**
   - Expose Sanchalak via HTTP
   - Handle streaming
   - Manage sessions

---

## Summary

**Sanchalak = Simple Router**
- Identifies what user needs
- Routes to right agent
- Returns response
- Tracks history
- Easy to extend

**That's it!** No complexity. Just routing. 🎭

---

Ready to test or build next agent? 🚀

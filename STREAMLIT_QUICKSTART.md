# TRAVAS-AI Streamlit - Quick Start

## 🚀 One Command to Run Everything

### Prerequisites
- Python 3.8+
- ANTHROPIC_API_KEY environment variable set

### Installation & Run

```bash
# Install dependencies
pip install -r streamlit_requirements.txt

# Run the app (opens in browser automatically)
streamlit run streamlit_app.py
```

That's it! Browser opens at `http://localhost:8501`

---

## 💻 What You Get

✅ **Single Streamlit app** - No servers to manage
✅ **Beautiful UI** - Built-in Streamlit components
✅ **Direct agent calls** - No API layer overhead
✅ **Real Claude integration** - Live LLM responses
✅ **Complete workflow** - Chat → Itinerary → Approve/Revise → Finalize

---

## 🎬 Demo Script

1. **Type in chat box:**
   ```
   I want a 5-day family trip to Goa. 
   2 adults, 2 kids (ages 6 and 9). 
   Budget ₹25,000. 
   We want beaches, culture, food, and activities.
   ```

2. **Hit Enter** → See itinerary appear on the right

3. **Review** → 5 days of activities, budget breakdown

4. **Click "Revise"** → Type feedback like:
   ```
   Increase budget to ₹45,000. 
   Skip the temple. 
   Add a kids activity instead.
   ```

5. **Click "Submit Revision"** → System updates itinerary

6. **Click "Approve"** → ✅ FINALIZED!

---

## 📁 Architecture

This Streamlit app directly calls:
- **SanchalakAgent** - Orchestrator
- **Specialist Agents** - Atithi, Annapurna, Yatra, Safar, Bazaar
- **YojanaAgent** - Plan synthesizer
- **ParikshakAgent** - Quality validator
- **FeedbackHandler** - Approval workflow

No intermediate servers needed!

---

## 🌐 Deploy to Streamlit Cloud

Make it live with one command:

```bash
# First, push to GitHub
git add streamlit_app.py streamlit_requirements.txt
git commit -m "Add Streamlit frontend"
git push

# Then, deploy to Streamlit Cloud
streamlit deploy
```

Share the URL and anyone can use it!

---

## ⚙️ Customize

**Change theme:** Edit `.streamlit/config.toml`

**Add features:** Edit `streamlit_app.py`

**Change port:** Add to command:
```bash
streamlit run streamlit_app.py --server.port 9000
```

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install -r streamlit_requirements.txt
```

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY="sk-ant-..."  # macOS/Linux
set ANTHROPIC_API_KEY=sk-ant-...       # Windows
```

### App won't load
Check console output for errors. Common issues:
- Missing API key
- Agents not importing correctly
- Python version too old

---

## 🎯 This is Better Because:

| Aspect | Streamlit | Node.js + Frontend |
|--------|-----------|-------------------|
| Setup | 1 command | 3 servers |
| Deployment | Streamlit Cloud | Custom hosting |
| Maintenance | Auto-reload | Manual reload |
| Performance | Direct agent calls | API overhead |
| Hosting | Free tier available | Not included |

---

## 📊 System Architecture

```
Streamlit App (8501)
    ↓
    ├→ SanchalakAgent (orchestrator)
    │
    ├→ Specialist Agents
    │   ├─ Atithi (hotels)
    │   ├─ Annapurna (food)
    │   ├─ Yatra (attractions)
    │   ├─ Safar (transport)
    │   └─ Bazaar (shopping)
    │
    ├→ Yojana (synthesizer)
    │
    ├→ Parikshak (validator)
    │
    └→ FeedbackHandler (approval)
    
    All in-process. No external APIs except Claude.
```

---

## 🚀 Ready to Demo!

```bash
streamlit run streamlit_app.py
```

Browser opens. User types. System works. Show everyone! 🌍✈️


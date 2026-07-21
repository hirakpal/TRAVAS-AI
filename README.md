# TRAVAS-AI — Multi-Agent Travel Assistant

TRAVAS-AI plans a full trip through a team of specialized LLM agents coordinated by a single
orchestrator. Every recommendation is grounded in **live** data (Google Places, Google Flights)
rather than the model's memory, so the assistant either shows verified results or plainly says it
can't — it never fabricates hotels, restaurants, attractions, or flights.

Built on Anthropic's Claude models, with a Streamlit front-end.

---

## What it does

You describe a trip in chat. The orchestrator gathers the essentials one question at a time,
then brings in specialists to fetch real options, synthesizes them into a day-by-day itinerary,
quality-checks it, and lets you approve / revise / reject. On finalization it renders a
"Traveller DNA" radar summarizing the trip's personality.

---

## Architecture

```
                 ┌──────────────────────────────────────────────┐
   user  ─────▶  │  SanchalakAgent  (THE orchestrator)          │
                 │  • gathers preferences (1 question/turn)     │
                 │  • routes to specialists                     │
                 │  • runs the synthesis→validation→approval    │
                 │    workflow and holds all workflow state     │
                 └───────┬───────────────────────┬──────────────┘
                         │ routes                 │ drives
          ┌──────────────┼───────────────┐        │
          ▼      ▼       ▼      ▼      ▼  │        ▼
       Atithi Annapurna Yatra Safar Bazaar      Yojana ──▶ Parikshak
       hotels  food    tours  transport shopping  (synthesize)  (quality gate)
          │      │       │      │      │
          ▼      ▼       ▼      ▼      ▼
     ┌───────────────────────────────────────┐
     │ Live data layer (grounding)           │
     │  • Google Places (New)  data/live_places.py │
     │  • Google Flights+Aviationstack live_flights.py │
     │  • Persistent RAG cache  data/live_rag.py │
     └───────────────────────────────────────┘
```

**Sanchalak is the single orchestrator.** It is both a conversational agent *and* the workflow
controller — routing among the five conversational specialists **and** owning the synthesis /
validation / approval lifecycle. The Streamlit app (`streamlit_app.py`) is a thin view: it forwards
user actions to Sanchalak and renders `sanchalak.get_view_state()`. Because no workflow logic lives
in the UI, the same backend could be driven by FastAPI, WhatsApp, or a mobile app unchanged.

### The agents

| Agent | Role | Grounded in |
|-------|------|-------------|
| **Sanchalak** | Orchestrator + conversation | — |
| **Atithi** | Hotels | Google Places (`lodging`) |
| **Annapurna** | Food / restaurants | Google Places (`restaurant`) |
| **Yatra** | Tours / attractions | Google Places (`tourist_attraction`) |
| **Safar** | Transport | Google Flights (SearchApi) + Aviationstack + Places local transport |
| **Bazaar** | Shopping | Google Places (`shopping_mall`) |
| **Yojana** | Itinerary synthesizer | specialists' outputs only (never searches) |
| **Parikshak** | Quality reviewer | the draft + deterministic findings |

---

## Key concepts

### Live grounding + honesty model
Specialists call live search tools for **any** destination. The rule is: **search first, present
real results, and only say "unavailable" if the API returns nothing or errors** — never answer from
general knowledge dressed up as verified. This is enforced by a per-turn directive injected from
`base_agent._coverage_directive`, plus a deterministic grounding flag (`has_ever_searched`).

### Retrieval-Augmented Generation with a persistent cache (`data/live_rag.py`)
Every live search result is embedded and stored in a **persistent Chroma vector DB** (one collection
per domain). Each search:

1. embeds the traveler's need,
2. queries the vector DB **first**, filtered to the destination —
   - **cache hit** → return the semantically closest cached records, *no API call*,
   - **cache miss** → call the live API, then **write** the results into the cache,
3. ranks by vector similarity to the need either way.

This demonstrates embeddings → vector DB → retrieval, and cuts repeat API calls (surfaced as
hit/miss/API-calls-saved in the transparency panel). It degrades gracefully: if Chroma can't load,
every search is simply a live call.

### Structured specialist status + derived gate (`agents/shared_state.py`)
Each specialist reports a structured `{status, confidence, missing_information}` after every turn
(via a forced `report_status` tool call, gated on having actually grounded). The synthesis gate
(`can_generate_itinerary`) is **derived** from this — "≥2 specialists reported complete" — not a
hand-maintained flag, so it can't go stale.

### Contract validation (`tools/planning_tools.py`)
After drafting, Yojana is forced to re-submit the itinerary as structured JSON (`submit_itinerary`),
which is then checked **deterministically** (time overlaps, budget overrun, day sequencing, activity
enums) — not by LLM judgment. Parikshak's LLM review receives these confirmed findings so it focuses
on subjective quality instead of re-deriving arithmetic.

### Traveller DNA radar
On approval, the finalized trip is scored 0–100 across Culture / Food / Adventure / Nature / Luxury /
Shopping / Relaxation and rendered as a Plotly radar.

---

## Setup

### Requirements
- **Python 3.12 or 3.13** (NOT 3.14 — `chromadb → tokenizers` has no 3.14 wheel; see note in
  `requirements.txt`).
- API keys (below).

### Environment variables
| Variable | Purpose | Required |
|----------|---------|----------|
| `ANTHROPIC_API_KEY` | Claude models (all agents) | Yes |
| `GOOGLE_PLACES_API_KEY` | Hotels/food/attractions/shopping/local transport (Places API New, billing on) | Yes |
| `SEARCHAPI_KEY` | Priced flight options (SearchApi Google Flights) | For flight prices |
| `AVIATIONSTACK_API_KEY` | Flight airlines/schedule fallback | Optional |
| `RAG_CACHE_PATH` | Where the persistent cache is stored (default `.chroma_cache`) | Optional |

Put them in a `.env` file (git-ignored) or the platform's secrets.

### Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Deploy (Streamlit Community Cloud)
1. Push the repo; the app installs from `requirements.txt`.
2. **Set Python to 3.12** under Advanced settings → Python version (delete + redeploy to change).
3. Add the API keys as Secrets.

> Note: Streamlit Cloud disk is ephemeral, so the RAG cache warms up during a run but resets on
> redeploy. True cross-deploy persistence would need external storage.

---

## Repository layout

```
streamlit_app.py            Thin Streamlit view over Sanchalak
agents/
  sanchalak_agent.py        Orchestrator + full workflow (routing, gate, approve/revise/reject, DNA)
  base_agent.py             Shared agent base (grounding, status emission, coverage directive)
  atithi/annapurna/yatra/safar/bazaar_agent.py   Conversational specialists
  yojana_agent.py           Itinerary synthesizer (+ forced structured contract validation)
  parikshak_agent.py        Quality reviewer
  shared_state.py           Shared state, preferences, structured status, derived readiness
  feedback_handler.py       Approve/revise/reject intent + state
data/
  live_places.py            Google Places (New) client
  live_flights.py           SearchApi Google Flights + Aviationstack + city→IATA
  live_rag.py               Persistent RAG cache over live results
tools/
  *_tools.py                Live-backed search tools per specialist
  planning_tools.py         submit_itinerary schema + deterministic validation
models/                     Itinerary dataclasses
requirements.txt            Runtime deps (Python 3.12/3.13)
requirements-dev.txt        Dev/CI deps
```

---

## Known limitations
- **Trains** aren't covered by the current data sources (Places = venues; SearchApi/Aviationstack =
  flights). `search_trains` honestly reports unavailable. A rail API would close this.
- **Flight prices** require `SEARCHAPI_KEY`; without it Safar falls back to Aviationstack
  (airlines/schedule, no fares).
- **Cache persistence** is per-deployment on ephemeral hosts (see deploy note).
- The legacy mock datasets (`data/mock_*.py`), `data/rag_index.py`, and `tools/rag_helpers.py` are
  superseded by the live layer and can be removed.

---

## Design principles worth calling out (for the writeup)
- **One orchestrator, not two** — workflow lives on the named orchestrator (Sanchalak), not scattered
  in the UI or a parallel class.
- **Deterministic over keyword-fragile** — routing/finalize/coverage decisions use LLM-with-context or
  explicit flags, with deterministic fallbacks, after repeated bugs from bare keyword matching.
- **Grounded or silent** — the system never presents unverified specifics as fact.
- **Derived, not stored** — readiness and coverage are computed from real signals so they can't drift.

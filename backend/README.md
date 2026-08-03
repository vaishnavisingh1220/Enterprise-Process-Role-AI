# Process-to-Role Intelligence AI — Backend

## What this is

An enterprise AI application that derives how AI affects organizational
roles by traversing persisted `Process -> Activity -> Role -> AI Impact`
relationships. The LLM is used **only** to narrate a pre-computed evidence
bundle — it never queries the database, decides what's relevant, or
generates facts on its own. See `services/reasoning_engine.py` for the
deterministic traversal and `services/ai_synthesis.py` for the narration
step.

## Architecture

```
api/            FastAPI routes (thin — no business logic)
services/
  reasoning_engine.py   deterministic Role<->Activity<->Process<->AIImpact traversal
  ai_synthesis.py        combines a reasoning_engine bundle with an LLM call, persists trace
database/
  models.py       SQLAlchemy schema
  seed_data.py     researched seed dataset (Supply Chain & Procurement industry)
  session.py       FastAPI DB session dependency
ai/
  client.py        LLM provider abstraction (Ollama / Groq / Mock)
  prompts.py       strict narration-only prompt templates
config/
  settings.py      environment-driven configuration
main.py            FastAPI app entrypoint
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 1. Seed the database (one-time, idempotent)

```bash
cd database
python seed_data.py
cd ..
```

This creates `database/enterprise_ai.db` (SQLite) with the researched
Supply Chain & Procurement dataset: 3 processes, 8 roles, 28 activities,
and cited AI-impact judgments. Re-running this script is safe — it
detects existing data and skips re-seeding.

### 2. Choose an LLM provider

The app defaults to a **local, free** Ollama model. No API key needed.

**Option A — Ollama (recommended, fully local/free)**
```bash
# install from https://ollama.com, then:
ollama pull llama3.1
ollama serve   # usually runs automatically after install
```
No further config needed — `LLM_PROVIDER=ollama` is the default.

**Option B — Groq (hosted, free tier)**
```bash
export LLM_PROVIDER=groq
export GROQ_API_KEY=your_key_here
```

**Option C — Mock (offline, no model at all)**
Useful for testing the reasoning engine and API without any LLM running:
```bash
export LLM_PROVIDER=mock
```

### 3. Run the API

```bash
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for interactive Swagger UI.

## Key endpoints

| Endpoint | LLM involved? | Purpose |
|---|---|---|
| `GET /roles` | No | List all roles |
| `GET /roles/{id}` | No | Role's full evidence bundle (activities, AI impact) — proves the reasoning engine works standalone |
| `GET /roles/{id}/analysis` | **Yes** | Full pipeline: reasoning engine -> LLM narration -> persisted trace. This is the "Show me how AI could affect a Procurement Manager" endpoint |
| `GET /roles/multi-process` | No | Roles spanning multiple processes — pure graph query |
| `GET /processes` | No | List processes |
| `GET /processes/{id}` | No | Process detail with activities + roles |
| `GET /processes/impact/{type}` | No | Activities filtered by impact_type (automate/augment/eliminate/create-new) |
| `GET /analysis/history` | No | Every past AI analysis ever run, most recent first |
| `GET /analysis/history/{id}` | No | Full stored trace (evidence + narrative) for one past analysis |

## Why the LLM/reasoning split matters

Every judge-facing claim in this app traces back to a specific
`activity_id` in the database. You can demonstrate this live by:
1. Calling `GET /roles/{id}` — shows the full structured analysis with
   zero LLM involvement.
2. Calling `GET /roles/{id}/analysis` — shows the same data narrated by
   the LLM, with citations like `[activity_id: 12]` tying every claim
   back to the evidence bundle.
3. Calling `GET /analysis/history/{id}` afterward — proves the exact
   evidence bundle used is permanently stored, not regenerated on the fly.
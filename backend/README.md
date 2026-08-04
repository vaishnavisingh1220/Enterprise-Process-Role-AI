# Process-to-Role Intelligence Backend

FastAPI backend powering the Process-to-Role Intelligence enterprise AI platform.

---

# Overview

The backend combines deterministic enterprise reasoning with LLM-powered narrative generation.

Unlike traditional AI assistants, all business reasoning is deterministic while Large Language Models are used only for executive summaries and human-readable explanations.

---

# Backend Architecture

```
                FastAPI

                    │

     ┌──────────────┼───────────────┐

     ▼              ▼               ▼

 REST APIs   Dynamic Intake      Chat API

     │              │               │

     └──────────────┼───────────────┘

                    ▼

     Deterministic Reasoning Engine

          │                  │

          ▼                  ▼

  Research Service     AI Synthesis

          │                  │

          └──────────┬───────┘

                     ▼

          SQLite Enterprise Database
```

---

# Project Structure

```
backend/
│
├── ai/
│   ├── client.py
│   ├── prompts.py
│   └── __init__.py
│
├── api/
│   ├── routes/
│   │   ├── analysis.py
│   │   ├── chat.py
│   │   ├── dynamic.py
│   │   ├── processes.py
│   │   └── roles.py
│   │
│   ├── schemas.py
│   └── __init__.py
│
├── config/
│   ├── settings.py
│   └── __init__.py
│
├── database/
│   ├── enterprise_ai.db
│   ├── models.py
│   ├── seed_data.py
│   ├── session.py
│   └── __init__.py
│
├── services/
│   ├── reasoning_engine.py
│   ├── query_router.py
│   ├── dynamic_intake.py
│   ├── ai_synthesis.py
│   ├── research_service.py
│   └── chat_service.py
│
├── tests/
│   ├── conftest.py
│   ├── test_dynamic_intake.py
│   └── test_query_router.py
│
├── .env
├── main.py
├── requirements.txt
└── README.md
```

---

# Core Features

- Deterministic reasoning engine
- Dynamic enterprise knowledge creation
- Live web research
- Explainable AI impact analysis
- Executive AI report generation
- Enterprise conversational assistant
- Persistent SQLite knowledge graph
- Multi-model LLM fallback
- Automated testing

---

# Design Philosophy

The backend separates business reasoning from language generation.

### Deterministic Engine

Responsible for:

- Role traversal
- Process traversal
- Activity lookup
- Question routing
- Citation generation

No LLM is used for business reasoning.

---

### LLM Layer

Responsible only for:

- Executive summaries
- Human-readable explanations
- AI narrative generation

This architecture minimizes hallucinations while keeping explanations natural.

---

# LLM Fallback Strategy

The backend automatically falls back between providers.

```
Ollama
   │
   ▼
Groq
   │
   ▼
OpenRouter
   │
   ▼
Mock Response
```

Every fallback event is logged.

---

# Surprise Record Pipeline

Supports runtime enterprise knowledge creation.

```
User Input
      │
      ▼
Live Research
      │
      ▼
Role Detection
      │
      ▼
Process Detection
      │
      ▼
AI Impact Generation
      │
      ▼
SQLite Persistence
      │
      ▼
Knowledge Graph Update
```

---

# API Endpoints

## Roles

```
GET /roles
GET /roles/{id}
```

## Analysis

```
GET /roles/{id}/analysis
```

## Chat

```
POST /chat
```

## Dynamic Intake

```
POST /dynamic
```

---

# Running

Install dependencies

```bash
pip install -r requirements.txt
```

Run

```bash
uvicorn main:app --reload
```

---

# Testing

Run all tests

```bash
pytest
```

Current coverage includes:

- Query router
- Dynamic intake
- JSON parsing
- API behavior
- Reasoning engine

**25 automated tests passing**

---

# Design Principles

- Explainable AI
- Deterministic reasoning
- Persistent enterprise knowledge
- Modular architecture
- Graceful degradation
- Enterprise-ready APIs

---

# License

Developed for an Enterprise AI Hackathon as a Minimum Viable Intelligence Product (MVIP).
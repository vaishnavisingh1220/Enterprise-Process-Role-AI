# AI Usage Disclosure

## Overview

This project combines deterministic software engineering with Large Language Models (LLMs) to provide explainable enterprise AI analysis.

The system was intentionally designed so that business reasoning remains deterministic while language models are used only for narrative generation.

---

# What the AI Models Do

Large Language Models are responsible for:

- Executive AI reports
- Human-readable summaries
- Future responsibility descriptions
- AI impact explanations

The AI never performs database traversal or business logic.

---

# What is Deterministic

The following components are implemented without relying on an LLM:

- Question routing
- Role lookup
- Process traversal
- Activity aggregation
- Citation generation
- AI readiness calculation
- Dynamic knowledge persistence
- Database operations

This design improves consistency, explainability, and reduces hallucinations.

---

# AI Models Used

Primary Model

- Ollama (local inference)

Fallback Models

- Groq
- OpenRouter
- Mock response (development fallback)

The backend automatically switches providers if one becomes unavailable.

---

# AI-Assisted Development

AI tools were used to assist with:

- Architecture brainstorming
- Documentation drafting
- UI refinement
- Code review

The following components were designed and implemented as part of this project:

- Backend architecture
- Database schema
- REST APIs
- Deterministic reasoning engine
- Dynamic knowledge pipeline
- Frontend integration
- Testing and debugging

---

# Design Philosophy

The project follows a hybrid AI architecture:

Deterministic reasoning first.

LLM narration second.

This approach produces explainable and reproducible enterprise AI outputs.
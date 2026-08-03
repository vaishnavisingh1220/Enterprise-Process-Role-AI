"""
Central configuration, read from environment variables so nothing here
needs a paid service or hardcoded secret. Everything defaults to a fully
local, free setup (SQLite + local Ollama), with free hosted fallbacks.

Values are loaded from a .env file in backend/ if present (via
python-dotenv), so you don't need to re-export environment variables in
every new terminal tab on Windows/Mac/Linux. Real environment variables
still take precedence over .env if both are set.
"""

import os

from dotenv import load_dotenv

load_dotenv()  # loads backend/.env if it exists; no-op otherwise

# --- Database -----------------------------------------------------------
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite:///./database/enterprise_ai.db"
)

# --- LLM ------------------------------------------------------------------
# LLM_PROVIDER options:
#   "auto"   (default) — tries each provider in LLM_FALLBACK_CHAIN in order,
#             falling through to the next on any connection/API failure.
#             Always ends in "mock" so a request never hard-fails.
#   "ollama" / "groq" / "openrouter" / "mock" — pin to exactly one provider,
#             useful for isolating/testing a single path.
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "auto")

LLM_FALLBACK_CHAIN = [
    p.strip()
    for p in os.environ.get("LLM_FALLBACK_CHAIN", "ollama,groq,openrouter,mock").split(",")
    if p.strip()
]

LLM_TIMEOUT_SECONDS = int(os.environ.get("LLM_TIMEOUT_SECONDS", "60"))

# Ollama — local, free, no API key. Primary provider.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")

# Groq — hosted, free tier, needs GROQ_API_KEY. First fallback.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-70b-versatile")
GROQ_HOST = os.environ.get("GROQ_HOST", "https://api.groq.com/openai/v1")

# OpenRouter — hosted, free-tier open-weight models (":free" suffix models
# cost nothing, no card required for those specific models), needs
# OPENROUTER_API_KEY. Second fallback — a genuinely different provider/infra
# from Groq, so if Groq's free tier is rate-limited this still works.
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
OPENROUTER_HOST = os.environ.get("OPENROUTER_HOST", "https://openrouter.ai/api/v1")

# --- API --------------------------------------------------------------
CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")
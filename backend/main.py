"""
Entrypoint. Run with:
    uvicorn main:app --reload

Expects to be run from the backend/ directory so the absolute imports
(database.*, services.*, ai.*, config.*, api.*) resolve correctly.

Before first run, seed the database:
    cd database && python seed_data.py && cd ..
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.session import init
from api.routes import roles, processes, analysis, chat
from api.schemas import HealthResponse

# Without this, ai/client.py's logger.info() calls (which report which LLM
# provider actually served a request — e.g. "used OllamaClient successfully"
# vs "fell back to MockClient") are silently swallowed, since Python's
# default logging level is WARNING. This is what you check during a live
# demo to see which provider is actually answering.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(
    title="Process-to-Role Intelligence AI",
    description=(
        "Derives how AI affects enterprise roles by traversing "
        "Process -> Activity -> Role -> AI Impact relationships, then "
        "using an LLM only to narrate the resulting evidence, not to "
        "generate the analysis itself."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


logger = logging.getLogger("main")


@app.on_event("startup")
def on_startup():
    init()  # create tables if they don't exist; never drops/wipes data
    _warm_up_ollama()


def _warm_up_ollama() -> None:
    """
    Fire a tiny, throwaway request at Ollama on startup so the model is
    already loaded into memory before the first real analysis request.
    Best-effort only: if Ollama isn't running yet, this just logs and moves
    on — the fallback chain handles that at request time regardless.
    """
    import requests

    try:
        requests.post(
            f"{settings.OLLAMA_HOST}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [{"role": "user", "content": "hi"}],
                "stream": False,
            },
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        logger.info(f"Ollama warm-up succeeded — {settings.OLLAMA_MODEL} is loaded and ready")
    except Exception as exc:  # noqa: BLE001 — startup warm-up must never crash the app
        logger.warning(
            f"Ollama warm-up skipped ({exc!r}) — first real request may be slower as a result"
        )


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


app.include_router(roles.router)
app.include_router(processes.router)
app.include_router(analysis.router)
app.include_router(chat.router)
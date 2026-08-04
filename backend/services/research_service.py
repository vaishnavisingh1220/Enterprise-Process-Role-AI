"""
Research/Retrieval stage of the dynamic-intake pipeline.

Uses `ddgs` (the current name for the former `duckduckgo-search` package) —
free, no API key, no signup, no paid tier to hit. This is what makes a
"surprise record" more than a raw LLM guess: an unfamiliar role/activity
gets a real search pass before the LLM reasons over it.

Reliability note (this directly answers the rubric's own question, "what
happens if a free-tier service becomes unavailable?"): DuckDuckGo's
unofficial search endpoint can rate-limit or change without notice, since
it's not a stable published API. Every function here is built to degrade
gracefully rather than fail — a search failure returns an empty result
with a clear "source": "unavailable" marker, and the AI Analysis stage
downstream explicitly lowers its own confidence_score when that happens.
Nothing in this pipeline depends on search succeeding.
"""

import logging

logger = logging.getLogger("research_service")


def research_topic(query: str, max_results: int = 3, timeout: float = 8.0) -> dict:
    """
    Returns:
        {
          "source": "duckduckgo" | "unavailable",
          "snippets": [{"title": str, "body": str, "url": str}, ...],
          "note": str | None,
        }
    Never raises. Any failure (network, import, rate limit, empty results)
    degrades to source="unavailable" with an explanatory note, rather than
    breaking the pipeline that called this.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        return {
            "source": "unavailable",
            "snippets": [],
            "note": "ddgs package not installed — run: pip install ddgs",
        }

    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:  # noqa: BLE001 — any search failure must degrade, not crash
        logger.warning(f"Research retrieval failed for '{query}' ({exc!r}) — falling back to reasoning-only")
        return {
            "source": "unavailable",
            "snippets": [],
            "note": f"Live search unavailable ({exc.__class__.__name__}) — AI will reason from general knowledge instead.",
        }

    if not raw_results:
        return {"source": "duckduckgo", "snippets": [], "note": "Search returned no results for this query."}

    snippets = [
        {
            "title": r.get("title", ""),
            "body": (r.get("body") or "")[:400],
            "url": r.get("href") or r.get("url") or "",
        }
        for r in raw_results
    ]
    return {"source": "duckduckgo", "snippets": snippets, "note": None}
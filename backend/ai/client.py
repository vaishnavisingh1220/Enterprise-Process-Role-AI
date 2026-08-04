"""
Thin LLM client abstraction. This is the ONLY place in the codebase that
talks to a model. It intentionally exposes a single generate(system, user)
method — the LLM never sees raw database access, tools, or the ability to
query anything itself. It only ever narrates what the reasoning engine
already computed and handed it.

Providers:
- OllamaClient: local, free, no API key. Primary provider.
- GroqClient: hosted, free-tier, OpenAI-compatible API. First fallback.
- OpenRouterClient: hosted, free-tier open-weight models (":free" model
  suffix), OpenAI-compatible API. Second fallback — different
  infra/rate-limits from Groq, so it covers Groq being down or throttled.
- MockClient: deterministic offline stub, never fails. Used for automated
  tests, for demoing the reasoning-engine-only path, and as the guaranteed
  last resort in the fallback chain so a request never hard-fails.

get_llm_client() returns either a single pinned provider (if LLM_PROVIDER
is set to one by name) or a FallbackLLMClient that tries each provider in
settings.LLM_FALLBACK_CHAIN in order (if LLM_PROVIDER="auto", the default).
"""

import json
import logging

import requests

from config import settings

logger = logging.getLogger("ai.client")


class LLMClient:
    def generate(self, system: str, user: str) -> str:
        raise NotImplementedError


class OllamaClient(LLMClient):
    def __init__(self, model: str | None = None, host: str | None = None):
        self.model = model or settings.OLLAMA_MODEL
        self.host = host or settings.OLLAMA_HOST

    def generate(self, system: str, user: str) -> str:
        response = requests.post(
            f"{self.host}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "options": {"temperature": 0.2},  # low temp: this is factual synthesis, not creative writing
            },
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]


class GroqClient(LLMClient):
    def __init__(self, api_key: str | None = None, model: str | None = None, host: str | None = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.host = host or settings.GROQ_HOST
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not set but LLM_PROVIDER=groq")

    def generate(self, system: str, user: str) -> str:
        response = requests.post(
            f"{self.host}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
            },
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


class OpenRouterClient(LLMClient):
    """
    Free open-weight models via OpenRouter's OpenAI-compatible API.
    Default model has a ':free' suffix, meaning $0 cost, no card needed —
    but free models are rate-limited, which is exactly why this sits in
    the fallback chain rather than being relied on as primary.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None, host: str | None = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.model = model or settings.OPENROUTER_MODEL
        self.host = host or settings.OPENROUTER_HOST
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set but LLM_PROVIDER=openrouter")

    def generate(self, system: str, user: str) -> str:
        response = requests.post(
            f"{self.host}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
            },
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


class MockClient(LLMClient):
    """
    Deterministic offline fallback. Produces a readable summary directly
    from the evidence bundle embedded in the prompt, WITHOUT any model
    call. Used for automated testing and for demonstrating that the
    reasoning engine's output is meaningful on its own, independent of
    whichever LLM is plugged in.

    Handles every evidence shape the chat router can produce (role-impact,
    comparison, list-style, process-detail, out-of-scope) since all chat
    intents route through this same client during offline testing.
    """

    def generate(self, system: str, user: str) -> str:
        # Dynamic intake expects raw JSON back (not narrative text) — detect
        # via the literal marker in the system prompt and return valid mock
        # JSON, so the full surprise-record pipeline is testable offline.
        if "TASK: dynamic_activity_analysis" in system:
            return json.dumps(
                {
                    "impact_type": "augment",
                    "automation_potential": 0.5,
                    "confidence_score": 0.35,
                    "rationale": "[MOCK] Offline placeholder judgment — no real LLM was called for this test.",
                    "future_responsibility": "[MOCK] Placeholder future-responsibility text for offline testing.",
                }
            )

        try:
            start = user.index("{")
            bundle, _ = json.JSONDecoder().raw_decode(user[start:])
        except (ValueError, json.JSONDecodeError):
            return "[MOCK LLM] Could not parse evidence bundle from prompt."

        lines = ["[MOCK LLM OUTPUT — offline synthesis]", ""]

        # Out-of-scope: dataset overview instead of a role/process bundle
        if bundle.get("scope") == "out_of_scope":
            lines.append("This question is outside what this dataset covers.")
            lines.append("Available roles: " + ", ".join(bundle.get("roles", [])))
            lines.append("Available processes: " + ", ".join(bundle.get("processes", [])))
            return "\n".join(lines)

        # Role comparison: two role-impact bundles under "roles"
        if bundle.get("comparison"):
            for rb in bundle.get("roles", []):
                summary = rb.get("impact_summary", {})
                parts = [f"{c} {t}" for t, c in summary.items()]
                lines.append(
                    f"{rb.get('role_name')}: {rb.get('activity_count', 0)} activities "
                    f"({', '.join(parts) if parts else 'no impact data'})."
                )
            return "\n".join(lines)

        # Single role-impact bundle
        if "role_name" in bundle and "activities" in bundle:
            role = bundle.get("role_name", "This role")
            summary = bundle.get("impact_summary", {})
            score = bundle.get("ai_readiness_score")
            if score is not None:
                lines.append(f"AI Readiness Score: {score}/100")
            lines.append(
                f"{role} is involved in {bundle.get('activity_count', 0)} activities "
                f"across {len(bundle.get('processes_involved', []))} process(es): "
                f"{', '.join(bundle.get('processes_involved', []))}."
            )
            if summary:
                parts = [f"{count} {impact_type}" for impact_type, count in summary.items()]
                lines.append("AI impact breakdown: " + ", ".join(parts) + ".")
            for act in bundle.get("activities", [])[:5]:
                impact = act.get("ai_impact") or {}
                lines.append(
                    f"- [activity_id: {act['activity_id']}] {act['activity_name']}: "
                    f"{impact.get('impact_type', 'unknown')} "
                    f"(confidence {impact.get('confidence_score', 'n/a')})."
                )
            return "\n".join(lines)

        # Process detail
        if "activities" in bundle and "roles_involved" in bundle:
            lines.append(
                f"Process: {bundle.get('name')} — roles involved: "
                f"{', '.join(bundle.get('roles_involved', []))}."
            )
            for act in bundle.get("activities", [])[:5]:
                lines.append(
                    f"- [activity_id: {act['activity_id']}] {act['activity_name']}: "
                    f"{act.get('impact_type', 'unknown')}"
                )
            return "\n".join(lines)

        # Generic list-style evidence (multi_process_roles, activities_by_impact, role_list, process_list)
        if "items" in bundle:
            kind = bundle.get("kind", "items")
            lines.append(f"{bundle.get('count', len(bundle['items']))} {kind.replace('_', ' ')} found.")
            for item in bundle["items"][:5]:
                lines.append(f"- {json.dumps(item)}")
            return "\n".join(lines)

        # Fallback: dump whatever we got
        lines.append("Evidence: " + json.dumps(bundle)[:300])
        return "\n".join(lines)


_PROVIDER_CLASSES = {
    "ollama": OllamaClient,
    "groq": GroqClient,
    "openrouter": OpenRouterClient,
    "mock": MockClient,
}


class FallbackLLMClient(LLMClient):
    """
    Tries each provider in `providers` in order. On any failure (network
    error, HTTP error, missing API key), logs a warning and moves to the
    next one. Since MockClient never fails, as long as it's last in the
    chain (the default), generate() is guaranteed to return something
    rather than raising a 500 mid-demo.
    """

    def __init__(self, providers: list[LLMClient]):
        if not providers:
            raise ValueError("FallbackLLMClient needs at least one provider")
        self.providers = providers

    def generate(self, system: str, user: str) -> str:
        last_error = None
        for provider in self.providers:
            name = provider.__class__.__name__
            try:
                result = provider.generate(system, user)
                if name != "MockClient":
                    logger.info(f"LLM: used {name} successfully")
                else:
                    logger.warning("LLM: all real providers failed, fell back to MockClient")
                return result
            except Exception as exc:  # noqa: BLE001 — intentionally broad: any provider failure should fall through
                logger.warning(f"LLM: {name} failed ({exc!r}), trying next provider")
                last_error = exc
        # Should be unreachable if MockClient is in the chain, since it never raises.
        raise RuntimeError(f"All LLM providers in the fallback chain failed. Last error: {last_error!r}")


def _build_provider(name: str) -> LLMClient | None:
    """Instantiate a provider by name, returning None (and logging) if it can't be configured (e.g. missing API key)."""
    cls = _PROVIDER_CLASSES.get(name)
    if cls is None:
        logger.warning(f"LLM: unknown provider '{name}' in fallback chain, skipping")
        return None
    try:
        return cls()
    except RuntimeError as exc:
        # e.g. GroqClient/OpenRouterClient raise RuntimeError if their API key is missing.
        # Skip it at build time rather than at request time.
        logger.warning(f"LLM: skipping provider '{name}' — {exc}")
        return None


def get_llm_client() -> LLMClient:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "auto":
        providers = [
            client
            for name in settings.LLM_FALLBACK_CHAIN
            if (client := _build_provider(name)) is not None
        ]
        if not providers:
            # Nothing configured at all — guarantee mock so the app still runs.
            providers = [MockClient()]
        return FallbackLLMClient(providers)

    if provider in _PROVIDER_CLASSES:
        return _PROVIDER_CLASSES[provider]()

    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


FALLBACK_NARRATIVE_NOTICE = (
    "AI narration is temporarily unavailable — every configured LLM provider "
    "failed to respond for this request. This is NOT missing data: the full "
    "evidence this analysis is based on is included below and is exactly "
    "what would have been narrated. Try again in a moment, or read the "
    "evidence directly."
)


def safe_generate(llm_client: LLMClient, system: str, user: str) -> str:
    """
    Every service call to the LLM goes through this, not llm_client.generate()
    directly. Even with LLM_PROVIDER=auto, a single-provider pin (e.g.
    testing with LLM_PROVIDER=ollama) or an unexpected error shape from a
    provider's API can still raise all the way up as an uncaught exception.
    This is the last line of defense: a narration failure degrades to a
    clear, honest notice instead of a 500 mid-demo. The evidence bundle is
    still returned and still persisted either way — only the prose narration
    is missing, never the underlying traceable data.
    """
    try:
        return llm_client.generate(system=system, user=user)
    except Exception as exc:  # noqa: BLE001 — this must never propagate
        logger.error(f"LLM narration failed even after fallback handling: {exc!r}")
        return FALLBACK_NARRATIVE_NOTICE
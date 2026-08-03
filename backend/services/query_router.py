"""
Question router for the chat endpoint.

Deliberately NOT LLM-based. Every other part of this app keeps the LLM
scoped to narration, never to deciding what data matters — this module
extends that same principle to free-text questions: entity matching and
intent classification happen here, in plain Python, before the LLM is
involved at all.

Why this matters in practice, not just in principle:
- It's testable in isolation with no mocking and no network calls.
- It's fast — no extra LLM round-trip just to figure out what was asked.
- It can never return malformed JSON or hallucinate an intent that
  doesn't map to a real reasoning_engine function.
- A judge asking an odd question gets a clean "that's outside this
  dataset" response instead of a silent hallucination, because unmatched
  questions fall through to an explicit UNKNOWN intent rather than being
  guessed at.

Trade-off, stated plainly: this is pattern matching, not real natural
language understanding. Unusual phrasing can fail to match a role/process
it should. That's an intentional trade for reliability and traceability —
see the module docstring in ai/client.py for the same trade-off applied
to LLM provider selection.
"""

import difflib
import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from database.models import Role, Process

# ---------------------------------------------------------------------------
# Intents — each maps directly to one or more reasoning_engine functions.
# ---------------------------------------------------------------------------

ROLE_IMPACT = "role_impact"
COMPARE_ROLES = "compare_roles"
MULTI_PROCESS_ROLES = "multi_process_roles"
ACTIVITIES_BY_IMPACT = "activities_by_impact"
PROCESS_DETAIL = "process_detail"
ROLE_LIST = "role_list"
PROCESS_LIST = "process_list"
UNKNOWN = "unknown"

IMPACT_KEYWORDS = {
    "automate": ["automate", "automation", "automated", "replace", "replaced"],
    "augment": ["augment", "augmentation", "augmented", "assist", "ai-assisted"],
    "eliminate": ["eliminate", "eliminated", "elimination", "removed", "gone"],
    "create-new": ["new responsibility", "new responsibilities", "emerging", "new role", "create-new"],
}

MULTI_PROCESS_PHRASES = [
    "multiple process", "more than one process", "several processes",
    "cross-process", "span processes", "across processes", "which roles work across",
]

COMPARE_PHRASES = ["compare", " vs ", " versus ", "difference between", "and how does"]

ROLE_LIST_PHRASES = ["what roles", "which roles do you have", "list roles", "list of roles", "all roles"]
PROCESS_LIST_PHRASES = ["what processes", "which processes", "list processes", "all processes"]


NEGATION_CUES = ["not ", "n't ", "cannot", "can not", "won't", "isn't", "aren't", "without", "except", "excluding"]


@dataclass
class RoutedQuestion:
    intent: str
    matched_roles: list[Role] = field(default_factory=list)
    matched_processes: list[Process] = field(default_factory=list)
    impact_type: str | None = None
    negated: bool = False


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _word_present(word: str, question_tokens: list[str], fuzzy_cutoff: float = 0.82) -> bool:
    """Exact token match first; a strict per-word fuzzy fallback catches typos
    (e.g. "procurment") without the false-positive risk of whole-string fuzzy
    matching against an entire question."""
    if word in question_tokens:
        return True
    return bool(difflib.get_close_matches(word, question_tokens, n=1, cutoff=fuzzy_cutoff))


def _match_roles(question_lower: str, roles: list[Role]) -> list[Role]:
    q_tokens = _tokenize(question_lower)
    matches = []
    for role in roles:
        if role.name.lower() in question_lower:
            matches.append(role)
            continue
        # Fallback requires EVERY word of the role name to appear (exactly or
        # via strict per-word fuzzy match) — e.g. both "procurement" AND
        # "manager" must be present, which is what disambiguates "Procurement
        # Manager" from "Procurement Analyst" and prevents generic questions
        # ("what roles do you have?") from accidentally matching anything.
        role_words = _tokenize(role.name)
        if role_words and all(_word_present(w, q_tokens) for w in role_words):
            matches.append(role)
    return matches


def _match_processes(question_lower: str, processes: list[Process]) -> list[Process]:
    q_tokens = _tokenize(question_lower)
    matches = []
    for process in processes:
        if process.name.lower() in question_lower:
            matches.append(process)
            continue
        # Process names are long and formal ("Procurement (Source-to-Contract)")
        # — nobody types that verbatim. Anchor on just the first, most
        # distinctive word ("procurement" / "inventory" / "warehouse"),
        # which is unambiguous across this dataset's 3 processes.
        words = _tokenize(process.name)
        if words and _word_present(words[0], q_tokens):
            matches.append(process)
    return matches


def _match_impact_type(question_lower: str) -> str | None:
    for impact_type, keywords in IMPACT_KEYWORDS.items():
        if any(kw in question_lower for kw in keywords):
            return impact_type
    return None


def route_question(db: Session, question: str) -> RoutedQuestion:
    q = question.lower().strip()

    all_roles = db.query(Role).all()
    all_processes = db.query(Process).all()

    matched_roles = _match_roles(q, all_roles)
    matched_processes = _match_processes(q, all_processes)
    impact_type = _match_impact_type(q)

    # Order matters: check the most specific signals first.

    if len(matched_roles) >= 2 and any(phrase in q for phrase in COMPARE_PHRASES):
        return RoutedQuestion(COMPARE_ROLES, matched_roles=matched_roles[:2])

    if len(matched_roles) == 1:
        return RoutedQuestion(ROLE_IMPACT, matched_roles=matched_roles)

    if len(matched_roles) >= 2:
        # Two roles matched but no explicit "compare" language — still
        # treat it as a comparison, since asking about two named roles at
        # once has no other sensible single-role interpretation.
        return RoutedQuestion(COMPARE_ROLES, matched_roles=matched_roles[:2])

    if any(phrase in q for phrase in MULTI_PROCESS_PHRASES):
        return RoutedQuestion(MULTI_PROCESS_ROLES)

    if impact_type and ("activit" in q or "task" in q or "which" in q or "what" in q):
        negated = any(cue in q for cue in NEGATION_CUES)
        return RoutedQuestion(ACTIVITIES_BY_IMPACT, impact_type=impact_type, negated=negated)

    if len(matched_processes) == 1:
        return RoutedQuestion(PROCESS_DETAIL, matched_processes=matched_processes)

    if any(phrase in q for phrase in ROLE_LIST_PHRASES):
        return RoutedQuestion(ROLE_LIST)

    if any(phrase in q for phrase in PROCESS_LIST_PHRASES):
        return RoutedQuestion(PROCESS_LIST)

    return RoutedQuestion(UNKNOWN)
"""
Orchestrates the chat pipeline: route_question() (deterministic, no LLM)
-> gather_evidence() (calls the SAME reasoning_engine functions the
role-impact endpoint uses) -> LLM narration -> persisted trace.

This is deliberately structured so the LLM is never the first thing that
touches a user's question — query_router decides what data is relevant,
this module fetches exactly that data, and only then does the LLM see
anything, and even then only to narrate what's already been assembled.
"""

import json

from sqlalchemy.orm import Session

from ai.client import LLMClient
from ai.prompts import CHAT_SYSTEM_PROMPT, build_chat_prompt
from database.models import AnalysisHistory
from services import reasoning_engine, query_router
from services.query_router import (
    RoutedQuestion,
    ROLE_IMPACT,
    COMPARE_ROLES,
    MULTI_PROCESS_ROLES,
    ACTIVITIES_BY_IMPACT,
    PROCESS_DETAIL,
    ROLE_LIST,
    PROCESS_LIST,
    UNKNOWN,
)


def gather_evidence(db: Session, routed: RoutedQuestion) -> tuple[dict, int | None]:
    """
    Maps an intent to the reasoning_engine call(s) that answer it.
    Returns (evidence_bundle, target_id_for_history_or_None).

    Every branch reuses a function reasoning_engine.py already exposes —
    nothing new is queried here that isn't also independently callable
    (and independently testable) outside the chat pipeline.
    """
    if routed.intent == ROLE_IMPACT:
        role = routed.matched_roles[0]
        return reasoning_engine.build_role_evidence_bundle(db, role.id), role.id

    if routed.intent == COMPARE_ROLES:
        bundles = [
            reasoning_engine.build_role_evidence_bundle(db, r.id) for r in routed.matched_roles[:2]
        ]
        return {"comparison": True, "roles": bundles}, None

    if routed.intent == MULTI_PROCESS_ROLES:
        items = reasoning_engine.get_multi_process_roles(db)
        return {"kind": "multi_process_roles", "count": len(items), "items": items}, None

    if routed.intent == ACTIVITIES_BY_IMPACT:
        items = reasoning_engine.get_activities_by_impact_type(db, routed.impact_type)
        return {
            "kind": "activities_by_impact",
            "impact_type": routed.impact_type,
            "count": len(items),
            "items": items,
        }, None

    if routed.intent == PROCESS_DETAIL:
        process = routed.matched_processes[0]
        return reasoning_engine.get_process_detail(db, process.id), process.id

    if routed.intent == ROLE_LIST:
        items = reasoning_engine.list_roles(db)
        return {"kind": "role_list", "count": len(items), "items": items}, None

    if routed.intent == PROCESS_LIST:
        items = reasoning_engine.list_processes(db)
        return {"kind": "process_list", "count": len(items), "items": items}, None

    # UNKNOWN — genuinely out of scope. No guessing: hand the LLM the real
    # dataset boundaries so it can say what it can't do without hallucinating.
    overview = reasoning_engine.get_dataset_overview(db)
    return {**overview, "scope": "out_of_scope"}, None


def answer_question(db: Session, llm_client: LLMClient, question: str) -> dict:
    routed = query_router.route_question(db, question)
    evidence, target_id = gather_evidence(db, routed)

    prompt = build_chat_prompt(question, evidence)
    narrative = llm_client.generate(system=CHAT_SYSTEM_PROMPT, user=prompt)

    record = AnalysisHistory(
        query_type=f"chat:{routed.intent}",
        target_id=target_id,
        user_query=question,
        reasoning_trace_json=json.dumps(evidence),
        llm_output=narrative,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "analysis_id": record.id,
        "question": question,
        "matched_intent": routed.intent,
        "matched_roles": [r.name for r in routed.matched_roles],
        "matched_processes": [p.name for p in routed.matched_processes],
        "answer": narrative,
        "evidence": evidence,
        "created_at": record.created_at.isoformat(),
    }
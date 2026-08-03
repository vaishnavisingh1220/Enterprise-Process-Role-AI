"""
AI synthesis layer. This is the ONLY place that combines the reasoning
engine's output with an LLM call. It never queries the database for new
facts — it only narrates what reasoning_engine.py already assembled — and
it always persists the full trace (evidence bundle + narrative) to
analysis_history so every answer is auditable after the fact, and survives
an app restart.
"""

import json

from sqlalchemy.orm import Session

from ai.client import LLMClient
from ai.prompts import ROLE_IMPACT_SYSTEM_PROMPT, build_role_impact_prompt
from database.models import AnalysisHistory
from services import reasoning_engine


class AnalysisNotFoundError(Exception):
    pass


def synthesize_role_impact(db: Session, llm_client: LLMClient, role_id: int) -> dict:
    """
    Full pipeline for "Show me how AI could affect <Role>":
      1. Deterministic traversal (reasoning_engine) builds the evidence bundle.
      2. LLM narrates that bundle under strict citation rules.
      3. Both are persisted to analysis_history.
      4. Both are returned to the caller, so the API/UI can render the
         narrative and the underlying trace side by side.
    """
    evidence_bundle = reasoning_engine.build_role_evidence_bundle(db, role_id)
    if evidence_bundle is None:
        raise AnalysisNotFoundError(f"No role found with id={role_id}")

    prompt = build_role_impact_prompt(evidence_bundle)
    narrative = llm_client.generate(system=ROLE_IMPACT_SYSTEM_PROMPT, user=prompt)

    record = AnalysisHistory(
        query_type="role_impact",
        target_id=role_id,
        reasoning_trace_json=json.dumps(evidence_bundle),
        llm_output=narrative,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "analysis_id": record.id,
        "role_id": role_id,
        "role_name": evidence_bundle["role_name"],
        "narrative": narrative,
        "evidence": evidence_bundle,
        "created_at": record.created_at.isoformat(),
    }
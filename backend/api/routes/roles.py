from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai.client import get_llm_client
from database.session import get_db
from services import reasoning_engine, ai_synthesis
from api.schemas import RoleSummary, RoleEvidenceBundle, RoleAnalysisResponse, MultiProcessRole

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleSummary])
def list_roles(db: Session = Depends(get_db)):
    """All roles. No AI involved — plain read."""
    return reasoning_engine.list_roles(db)


@router.get("/multi-process", response_model=list[MultiProcessRole])
def multi_process_roles(db: Session = Depends(get_db)):
    """
    "Which roles participate in multiple processes?"
    Pure graph query, deliberately does NOT call the LLM.

    NOTE: this route must stay registered BEFORE /{role_id} — FastAPI
    matches routes in order, and /{role_id} would otherwise swallow
    "/roles/multi-process" as if "multi-process" were a role_id.
    """
    return reasoning_engine.get_multi_process_roles(db)


@router.get("/{role_id}", response_model=RoleEvidenceBundle)
def get_role(role_id: int, db: Session = Depends(get_db)):
    """Role detail + its full activity/impact evidence bundle, no LLM narrative."""
    bundle = reasoning_engine.build_role_evidence_bundle(db, role_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail=f"Role {role_id} not found")
    return bundle


@router.get("/{role_id}/analysis", response_model=RoleAnalysisResponse)
def analyze_role(role_id: int, db: Session = Depends(get_db)):
    """
    The headline endpoint: "Show me how AI could affect a Procurement Manager."
    Runs the full pipeline (reasoning engine -> LLM synthesis -> persisted
    trace) and returns both the narrative and the underlying evidence.
    """
    try:
        llm_client = get_llm_client()
        result = ai_synthesis.synthesize_role_impact(db, llm_client, role_id)
    except ai_synthesis.AnalysisNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return result
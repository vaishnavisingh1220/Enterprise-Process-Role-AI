from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai.client import get_llm_client
from database.session import get_db
from services import dynamic_intake
from api.schemas import DynamicActivityRequest, DynamicActivityResponse

router = APIRouter(prefix="/dynamic", tags=["dynamic"])


@router.post("/analyze-activity", response_model=DynamicActivityResponse)
def analyze_activity(request: DynamicActivityRequest, db: Session = Depends(get_db)):
    """
    The Surprise Record endpoint. Accepts a brand-new activity — with a
    role and/or process that may also be brand new — researches it live,
    gets a structured AI judgment, and persists all of it. After this
    call, the new role/process/activity is immediately queryable through
    every other endpoint (GET /roles/{id}, GET /roles/{id}/analysis,
    GET /roles/multi-process, POST /chat/ask), exactly like the
    pre-seeded dataset — nothing else needs to be built for that to work.
    """
    try:
        llm_client = get_llm_client()
        result = dynamic_intake.analyze_new_activity(
            db,
            llm_client,
            request.activity_name,
            request.activity_description,
            request.role_name,
            request.process_name,
            request.frequency,
        )
    except dynamic_intake.DynamicIntakeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    judgment = result["judgment"]
    research = result["research"]
    return {
        "activity_id": result["activity_id"],
        "role_id": result["role_id"],
        "role_created": result["role_created"],
        "process_id": result["process_id"],
        "process_created": result["process_created"],
        "impact_type": judgment["impact_type"],
        "automation_potential": judgment["automation_potential"],
        "confidence_score": judgment["confidence_score"],
        "rationale": judgment["rationale"],
        "evidence_source": result["evidence_source"],
        "future_responsibility": judgment["future_responsibility"],
        "research_source": research["source"],
        "research_snippet_count": len(research["snippets"]),
        "parse_failed": result["parse_failed"],
    }
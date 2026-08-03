from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.session import get_db
from services import reasoning_engine
from api.schemas import ProcessSummary, ProcessDetail, ActivityImpactSummary

router = APIRouter(prefix="/processes", tags=["processes"])


@router.get("", response_model=list[ProcessSummary])
def list_processes(db: Session = Depends(get_db)):
    return reasoning_engine.list_processes(db)


@router.get("/impact/{impact_type}", response_model=list[ActivityImpactSummary])
def activities_by_impact(impact_type: str, db: Session = Depends(get_db)):
    """
    e.g. GET /processes/impact/automate
    "Which activities are likely to change because of AI?" filtered by
    impact type. Pure query, no LLM.

    NOTE: this route must stay registered BEFORE /{process_id} for the
    same route-ordering reason as /roles/multi-process.
    """
    valid = {"automate", "augment", "eliminate", "create-new"}
    if impact_type not in valid:
        raise HTTPException(status_code=400, detail=f"impact_type must be one of {valid}")
    return reasoning_engine.get_activities_by_impact_type(db, impact_type)


@router.get("/{process_id}", response_model=ProcessDetail)
def get_process(process_id: int, db: Session = Depends(get_db)):
    detail = reasoning_engine.get_process_detail(db, process_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Process {process_id} not found")
    return detail
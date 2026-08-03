import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.session import get_db
from database.models import AnalysisHistory
from api.schemas import AnalysisHistoryItem, AnalysisHistoryDetail

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/history", response_model=list[AnalysisHistoryItem])
def list_history(db: Session = Depends(get_db), limit: int = 50):
    """
    Every AI-synthesized answer ever produced, most recent first. This is
    the persistence/traceability proof: restarting the app does not lose
    this, since it's the same SQLite file the seed data lives in.
    """
    records = (
        db.query(AnalysisHistory)
        .order_by(AnalysisHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "analysis_id": r.id,
            "query_type": r.query_type,
            "target_id": r.target_id,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


@router.get("/history/{analysis_id}", response_model=AnalysisHistoryDetail)
def get_history_record(analysis_id: int, db: Session = Depends(get_db)):
    record = db.query(AnalysisHistory).filter(AnalysisHistory.id == analysis_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
    return {
        "analysis_id": record.id,
        "query_type": record.query_type,
        "target_id": record.target_id,
        "evidence": json.loads(record.reasoning_trace_json),
        "narrative": record.llm_output,
        "created_at": record.created_at.isoformat(),
    }
"""
Pydantic response models for every API endpoint.

Purpose: these are the typed contract the frontend build depends on. Every
field name here is EXACTLY what the JSON response will contain — this is
what should be pasted into Cursor prompts instead of example JSON, so it
can't invent field names that don't exist (e.g. impactType vs impact_type).

FastAPI validates every route's return value against its response_model
automatically, so if reasoning_engine.py or ai_synthesis.py ever drifts
from these shapes, you get a clear 500 in dev instead of a silent frontend
bug three files away.
"""

from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------


class RoleSummary(BaseModel):
    role_id: int
    name: str
    department: Optional[str] = None
    seniority_level: Optional[str] = None


class AIImpact(BaseModel):
    impact_type: str  # automate | augment | eliminate | create-new
    automation_potential: float
    confidence_score: float
    rationale: str
    evidence_source: str


class ActivityEvidence(BaseModel):
    activity_id: int
    activity_name: str
    process_id: int
    process_name: str
    involvement_level: Optional[str] = None
    frequency: Optional[str] = None
    ai_impact: Optional[AIImpact] = None
    future_responsibility: Optional[str] = None


class RoleEvidenceBundle(BaseModel):
    """Returned by GET /roles/{id} — the reasoning engine's output, no LLM involved."""

    role_id: int
    role_name: str
    department: Optional[str] = None
    seniority_level: Optional[str] = None
    processes_involved: list[str]
    activity_count: int
    impact_summary: dict[str, int]  # e.g. {"automate": 3, "augment": 4}
    ai_readiness_score: Optional[float] = None  # 0-100; avg automation_potential across activities below
    activities: list[ActivityEvidence]


class RoleAnalysisResponse(BaseModel):
    """Returned by GET /roles/{id}/analysis — the full reasoning + LLM pipeline."""

    analysis_id: int
    role_id: int
    role_name: str
    narrative: str
    evidence: RoleEvidenceBundle
    created_at: str


class MultiProcessRole(BaseModel):
    role_id: int
    role_name: str
    process_count: int
    processes: list[str]
    activity_count: int


# ---------------------------------------------------------------------------
# Processes
# ---------------------------------------------------------------------------


class ProcessSummary(BaseModel):
    process_id: int
    name: str
    description: Optional[str] = None


class ProcessActivitySummary(BaseModel):
    activity_id: int
    activity_name: str
    roles: list[str]
    impact_type: Optional[str] = None
    automation_potential: Optional[float] = None


class ProcessDetail(BaseModel):
    process_id: int
    name: str
    description: Optional[str] = None
    roles_involved: list[str]
    activities: list[ProcessActivitySummary]


class ActivityImpactSummary(BaseModel):
    activity_id: int
    activity_name: str
    process_name: str
    roles: list[str]
    automation_potential: float
    confidence_score: float


# ---------------------------------------------------------------------------
# Analysis history
# ---------------------------------------------------------------------------


class AnalysisHistoryItem(BaseModel):
    analysis_id: int
    query_type: str
    target_id: int
    created_at: str


class AnalysisHistoryDetail(BaseModel):
    analysis_id: int
    query_type: str
    target_id: int
    evidence: dict  # kept as raw dict: shape varies by query_type (role_impact today, others later)
    narrative: str
    created_at: str


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    analysis_id: int
    question: str
    matched_intent: str
    matched_roles: list[str]
    matched_processes: list[str]
    answer: str
    evidence: dict
    created_at: str


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str
"""
The "Surprise Record" pipeline: accepts a brand-new activity — possibly
tied to a role and/or process that don't exist yet either — researches it,
gets a structured AI judgment, and PERSISTS it into the same tables the
seed data lives in.

Pipeline stages, matching the assignment's required architecture exactly:
    Input -> Backend Processing -> Research/Retrieval -> AI Analysis
    -> Storage -> Relationships -> Output

The "Relationships" stage is deliberately not a separate code path: once
the new Role/Process/Activity/AIImpact rows are committed, every existing
reasoning_engine function already traverses them dynamically (nothing in
this app is a fixed list of 28 activities) — so the new record is
immediately queryable through /roles/{id}, /roles/{id}/analysis,
/roles/multi-process, and /chat/ask with zero additional code. That's the
concrete answer to "what happens if we give this app 1,000 new processes
tomorrow."
"""

import json
import logging

from sqlalchemy.orm import Session

from ai.client import LLMClient, safe_generate
from ai.prompts import DYNAMIC_ANALYSIS_SYSTEM_PROMPT, build_dynamic_analysis_prompt
from database.models import Industry, Role, Process, Activity, RoleActivity, AIImpact, FutureResponsibility
from services import research_service

logger = logging.getLogger("dynamic_intake")

VALID_IMPACT_TYPES = {"automate", "augment", "eliminate", "create-new"}


class DynamicIntakeError(ValueError):
    """Raised for bad input (missing fields) — maps to a 422, not a 500."""


def find_or_create_role(db: Session, name: str) -> tuple[Role, bool]:
    """Case-insensitive match against existing roles; creates a new one if
    none matches. Returns (role, was_created)."""
    name = name.strip()
    existing = next((r for r in db.query(Role).all() if r.name.strip().lower() == name.lower()), None)
    if existing:
        return existing, False
    role = Role(name=name, department="User-submitted", seniority_level=None)
    db.add(role)
    db.flush()
    return role, True


def find_or_create_process(db: Session, name: str, industry_id: int) -> tuple[Process, bool]:
    """Case-insensitive match against existing processes; creates a new one
    if none matches. Returns (process, was_created)."""
    name = name.strip()
    existing = next((p for p in db.query(Process).all() if p.name.strip().lower() == name.lower()), None)
    if existing:
        return existing, False
    process = Process(industry_id=industry_id, name=name, description="User-submitted/ dynamic intake")
    db.add(process)
    db.flush()
    return process, True


def parse_structured_judgment(raw_text: str) -> dict:
    """
    Parses the LLM's JSON impact judgment. Real LLMs — especially small
    local models under demo pressure — sometimes wrap JSON in markdown
    fences or add stray commentary despite instructions not to. This never
    raises: on any parse failure it returns a clearly-labeled conservative
    default (impact_type="augment", low confidence) with the raw output
    preserved, so a live demo completes instead of crashing on a malformed
    LLM response.
    """
    text = raw_text.strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        start = text.index("{")
        data, _ = json.JSONDecoder().raw_decode(text[start:])
    except (ValueError, json.JSONDecodeError):
        return {
            "impact_type": "augment",
            "automation_potential": 0.4,
            "confidence_score": 0.2,
            "rationale": (
                "AI analysis could not be parsed into a structured judgment; "
                "showing a conservative default. Raw model output has been "
                "preserved for manual review."
            ),
            "future_responsibility": "Not determined — structured parsing failed.",
            "parse_failed": True,
            "raw_output": raw_text[:1000],
        }

    def _clamp01(value, default):
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return default

    impact_type = data.get("impact_type")
    if impact_type not in VALID_IMPACT_TYPES:
        impact_type = "augment"

    return {
        "impact_type": impact_type,
        "automation_potential": _clamp01(data.get("automation_potential"), 0.4),
        "confidence_score": _clamp01(data.get("confidence_score"), 0.3),
        "rationale": str(data.get("rationale") or "No rationale provided."),
        "future_responsibility": str(data.get("future_responsibility") or "Not specified."),
        "parse_failed": False,
    }


def analyze_new_activity(
    db: Session,
    llm_client: LLMClient,
    activity_name: str,
    activity_description: str,
    role_name: str,
    process_name: str,
    frequency: str | None = None,
) -> dict:
    # --- Backend Processing: validate & normalize ---
    activity_name = (activity_name or "").strip()
    activity_description = (activity_description or "").strip()
    role_name = (role_name or "").strip()
    process_name = (process_name or "").strip()

    if not all([activity_name, activity_description, role_name, process_name]):
        raise DynamicIntakeError(
            "activity_name, activity_description, role_name, and process_name are all required."
        )

    # --- Research/Retrieval ---
    research = research_service.research_topic(f"{activity_name} AI automation enterprise impact")

    # --- AI Analysis ---
    prompt = build_dynamic_analysis_prompt(activity_name, activity_description, role_name, process_name, research)
    raw = safe_generate(llm_client, system=DYNAMIC_ANALYSIS_SYSTEM_PROMPT, user=prompt)
    judgment = parse_structured_judgment(raw)

    evidence_source = (
        "Live research: " + "; ".join(s["title"] for s in research["snippets"][:2] if s["title"])
        if research["snippets"]
        else "AI-generated reasoning (no live research available) — not independently verified, unlike the pre-seeded dataset"
    )

    # --- Storage ---
    industry = db.query(Industry).first()
    if industry is None:
        raise DynamicIntakeError("No industry found in the database — run seed_data.py first.")

    role, role_created = find_or_create_role(db, role_name)
    process, process_created = find_or_create_process(db, process_name, industry.id)

    activity = Activity(
        process_id=process.id,
        name=activity_name,
        description=activity_description,
        frequency=frequency or "unspecified",
        data_intensity="unspecified",
    )
    db.add(activity)
    db.flush()

    db.add(RoleActivity(role_id=role.id, activity_id=activity.id, involvement_level="primary"))
    db.add(
        AIImpact(
            activity_id=activity.id,
            automation_potential=judgment["automation_potential"],
            impact_type=judgment["impact_type"],
            rationale=judgment["rationale"],
            evidence_source=evidence_source,
            confidence_score=judgment["confidence_score"],
        )
    )
    db.add(
        FutureResponsibility(
            role_id=role.id,
            activity_id=activity.id,
            description=judgment["future_responsibility"],
        )
    )

    db.commit()
    db.refresh(activity)

    logger.info(
        f"Dynamic intake: activity_id={activity.id} role_id={role.id} "
        f"(new={role_created}) process_id={process.id} (new={process_created}) "
        f"research_source={research['source']}"
    )

    # --- Relationships: automatic. No code needed here — see module docstring. ---

    # --- Output ---
    return {
        "activity_id": activity.id,
        "role_id": role.id,
        "role_created": role_created,
        "process_id": process.id,
        "process_created": process_created,
        "research": research,
        "judgment": judgment,
        "evidence_source": evidence_source,
        "parse_failed": judgment.get("parse_failed", False),
    }
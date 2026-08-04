"""
Tests for services/dynamic_intake.py — the Surprise Record pipeline.

Network calls to research_service are monkeypatched out: automated tests
should be fast and deterministic, and this sandbox/CI may not have
internet access anyway. The graceful-degradation path (research
unavailable) is tested for real, since that's a real code path this app
relies on regardless of network access.
"""

import json

from ai.client import MockClient
from services import dynamic_intake, reasoning_engine, research_service


def test_parse_valid_json():
    raw = json.dumps(
        {
            "impact_type": "automate",
            "automation_potential": 0.7,
            "confidence_score": 0.6,
            "rationale": "Test rationale",
            "future_responsibility": "Test future responsibility",
        }
    )
    result = dynamic_intake.parse_structured_judgment(raw)
    assert result["impact_type"] == "automate"
    assert result["automation_potential"] == 0.7
    assert result["parse_failed"] is False


def test_parse_json_wrapped_in_markdown_fences():
    raw = "```json\n" + json.dumps({"impact_type": "augment", "automation_potential": 0.5, "confidence_score": 0.4, "rationale": "r", "future_responsibility": "f"}) + "\n```"
    result = dynamic_intake.parse_structured_judgment(raw)
    assert result["impact_type"] == "augment"
    assert result["parse_failed"] is False


def test_parse_malformed_json_degrades_gracefully():
    raw = "I think this activity will probably be automated, roughly 70%."
    result = dynamic_intake.parse_structured_judgment(raw)
    assert result["parse_failed"] is True
    assert result["impact_type"] == "augment"  # safe conservative default
    assert 0.0 <= result["automation_potential"] <= 1.0
    assert "raw_output" in result


def test_parse_invalid_impact_type_falls_back_to_augment():
    raw = json.dumps({"impact_type": "definitely_automate", "automation_potential": 0.5, "confidence_score": 0.5, "rationale": "r", "future_responsibility": "f"})
    result = dynamic_intake.parse_structured_judgment(raw)
    assert result["impact_type"] == "augment"


def test_parse_out_of_range_values_get_clamped():
    raw = json.dumps({"impact_type": "automate", "automation_potential": 5.0, "confidence_score": -1.0, "rationale": "r", "future_responsibility": "f"})
    result = dynamic_intake.parse_structured_judgment(raw)
    assert 0.0 <= result["automation_potential"] <= 1.0
    assert 0.0 <= result["confidence_score"] <= 1.0


def test_find_or_create_role_reuses_existing(db):
    from database.models import Role

    existing = db.query(Role).filter(Role.name == "Procurement Manager").first()
    role, created = dynamic_intake.find_or_create_role(db, "procurement manager")  # different case
    assert created is False
    assert role.id == existing.id


def test_find_or_create_role_creates_new(db):
    role, created = dynamic_intake.find_or_create_role(db, "Finance Analyst")
    assert created is True
    assert role.name == "Finance Analyst"
    assert role.id is not None


def test_research_topic_degrades_gracefully_when_unavailable(monkeypatch):
    """Simulates a DuckDuckGo failure (network blocked, rate-limited, etc.)
    and confirms the pipeline doesn't raise — this is the real-world path
    this sandbox exercises, since it has no internet access to DuckDuckGo."""

    def broken_ddgs_text(*args, **kwargs):
        raise ConnectionError("simulated network failure")

    class BrokenDDGS:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def text(self, *args, **kwargs):
            return broken_ddgs_text()

    import services.research_service as rs

    monkeypatch.setattr(rs, "DDGS", BrokenDDGS, raising=False)
    # patch the import site used inside research_topic
    import sys

    fake_module = type(sys)("ddgs")
    fake_module.DDGS = BrokenDDGS
    sys.modules["ddgs"] = fake_module

    result = research_service.research_topic("anything")
    assert result["source"] == "unavailable"
    assert result["snippets"] == []
    assert result["note"] is not None


def test_full_pipeline_new_role_and_process_end_to_end(db, monkeypatch):
    """
    The most important test in this file: proves a surprise record is not
    just accepted and stored, but immediately becomes a first-class,
    queryable record through the SAME reasoning engine functions used for
    the pre-seeded dataset — no special-casing required. This is the
    concrete evidence for "what happens with 1,000 new processes tomorrow."
    """
    monkeypatch.setattr(
        research_service,
        "research_topic",
        lambda query, **kwargs: {"source": "unavailable", "snippets": [], "note": "test stub"},
    )

    mock_client = MockClient()
    result = dynamic_intake.analyze_new_activity(
        db,
        mock_client,
        activity_name="Bias auditing of AI model outputs",
        activity_description="Reviewing AI-generated decisions for demographic or systemic bias before they reach production.",
        role_name="AI Ethics Officer",
        process_name="AI Governance",
        frequency="weekly",
    )

    assert result["role_created"] is True
    assert result["process_created"] is True
    assert result["parse_failed"] is False

    # The actual proof: query it back through the SAME reasoning engine
    # function every other role uses. No special dynamic-record handling.
    bundle = reasoning_engine.build_role_evidence_bundle(db, result["role_id"])
    assert bundle["role_name"] == "AI Ethics Officer"
    assert bundle["activity_count"] == 1
    assert bundle["activities"][0]["activity_id"] == result["activity_id"]
    assert bundle["activities"][0]["ai_impact"]["impact_type"] == "augment"  # MockClient's fixed output

    # And it shows up in the full role list, alongside the pre-seeded roles.
    all_roles = reasoning_engine.list_roles(db)
    assert any(r["name"] == "AI Ethics Officer" for r in all_roles)


def test_reusing_existing_role_does_not_duplicate(db, monkeypatch):
    """Adding a new activity for an EXISTING role (e.g. 'Warehouse Manager')
    should reuse that role, not create a duplicate."""
    monkeypatch.setattr(
        research_service,
        "research_topic",
        lambda query, **kwargs: {"source": "unavailable", "snippets": [], "note": "test stub"},
    )
    mock_client = MockClient()

    result = dynamic_intake.analyze_new_activity(
        db,
        mock_client,
        activity_name="Drone-based inventory scanning",
        activity_description="Using autonomous drones to scan warehouse shelves for stock verification.",
        role_name="Warehouse Manager",  # already exists in seed data
        process_name="Warehouse Operations / Order Fulfillment",  # already exists
        frequency="monthly",
    )
    assert result["role_created"] is False
    assert result["process_created"] is False

    bundle = reasoning_engine.build_role_evidence_bundle(db, result["role_id"])
    # Warehouse Manager spans Inventory Management + Warehouse Operations
    # with 8 seeded activities; now 9 after this one is added.
    assert bundle["activity_count"] == 9
"""
Tests for services/query_router.py.

No LLM, no network, no mocking needed — this is exactly why routing was
built as plain Python rather than an LLM call: it's fast and deterministic
to test. Several of these cases (marked below) are regression tests for
false positives caught during manual testing before this suite existed.
"""

from services import query_router as qr


def test_role_impact_exact_match(db):
    routed = qr.route_question(db, "How does AI affect the Procurement Manager?")
    assert routed.intent == qr.ROLE_IMPACT
    assert [r.name for r in routed.matched_roles] == ["Procurement Manager"]


def test_role_impact_typo_tolerance(db):
    routed = qr.route_question(db, "How does AI affect the Procurment Manager?")
    assert routed.intent == qr.ROLE_IMPACT
    assert [r.name for r in routed.matched_roles] == ["Procurement Manager"]


def test_compare_roles(db):
    routed = qr.route_question(db, "Compare Warehouse Manager and Inventory Analyst")
    assert routed.intent == qr.COMPARE_ROLES
    names = {r.name for r in routed.matched_roles}
    assert names == {"Warehouse Manager", "Inventory Analyst"}


def test_multi_process_roles(db):
    routed = qr.route_question(db, "Which roles work across multiple processes?")
    assert routed.intent == qr.MULTI_PROCESS_ROLES


def test_activities_by_impact_automate(db):
    routed = qr.route_question(db, "What activities will be automated?")
    assert routed.intent == qr.ACTIVITIES_BY_IMPACT
    assert routed.impact_type == "automate"


def test_activities_by_impact_create_new(db):
    routed = qr.route_question(db, "Which activities create new responsibilities?")
    assert routed.intent == qr.ACTIVITIES_BY_IMPACT
    assert routed.impact_type == "create-new"


def test_process_detail(db):
    routed = qr.route_question(db, "Tell me about the Procurement process")
    assert routed.intent == qr.PROCESS_DETAIL
    assert [p.name for p in routed.matched_processes] == ["Procurement (Source-to-Contract)"]


def test_role_list(db):
    routed = qr.route_question(db, "What roles do you have data on?")
    assert routed.intent == qr.ROLE_LIST


def test_process_list(db):
    routed = qr.route_question(db, "what processes do you cover")
    assert routed.intent == qr.PROCESS_LIST


def test_out_of_scope(db):
    routed = qr.route_question(db, "What is the capital of France?")
    assert routed.intent == qr.UNKNOWN
    assert routed.matched_roles == []
    assert routed.matched_processes == []


# --- Regression tests: these three specifically failed before the matcher
# was rewritten from whole-string fuzzy matching to tokenized word-boundary
# matching. Keeping them named explicitly so a future change that
# reintroduces the bug fails loudly and specifically. ---


def test_regression_generic_question_matches_no_role(db):
    """'What activities will be automated?' previously false-matched Warehouse Associate."""
    routed = qr.route_question(db, "What activities will be automated?")
    assert routed.matched_roles == []


def test_regression_process_name_does_not_match_roles(db):
    """'Tell me about the Procurement process' previously false-matched two roles as a comparison."""
    routed = qr.route_question(db, "Tell me about the Procurement process")
    assert routed.matched_roles == []


def test_regression_meta_question_matches_no_role(db):
    """'What roles do you have data on?' previously false-matched two unrelated roles."""
    routed = qr.route_question(db, "What roles do you have data on?")
    assert routed.matched_roles == []


def test_negation_flips_to_complement(db):
    """'What can AI NOT automate?' must set negated=True, not silently
    return the same 'automate' list (found during live stress-testing)."""
    routed = qr.route_question(db, "What can AI not automate?")
    assert routed.intent == qr.ACTIVITIES_BY_IMPACT
    assert routed.impact_type == "automate"
    assert routed.negated is True


def test_non_negated_impact_question_unaffected(db):
    routed = qr.route_question(db, "What activities will be automated?")
    assert routed.negated is False
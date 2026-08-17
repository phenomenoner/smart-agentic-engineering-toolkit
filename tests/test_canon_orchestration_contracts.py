from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
WAL_SKILL = ROOT / "skills" / "engineering-wal" / "SKILL.md"
ORCHESTRATION_REFERENCE = (
    ROOT / "skills" / "engineering-wal" / "references" / "canon-orchestration.md"
)
ORCHESTRATION_CORPUS = ROOT / "evals" / "cases" / "canon-orchestration.json"
WORKFLOW = ROOT / "workflows" / "specify-implement-review-drill.md"
TRANSITION_GUARD = (
    ROOT / "skills" / "engineering-wal" / "scripts" / "validate_orchestration_transition.py"
)

EXPECTED_CASE_IDS = {
    "CANON-ORCHESTRATION-COMMITMENT-FLOOR",
    "CANON-ORCHESTRATION-UNAUTHORIZED-DOWNGRADE",
    "CANON-ORCHESTRATION-SPEC-GAP",
    "CANON-ORCHESTRATION-OWNER-RECLASSIFICATION",
    "CANON-ORCHESTRATION-HOST-SEAM",
    "CANON-ORCHESTRATION-LOOP-BUDGET",
    "NON-CANON-ORCHESTRATION-DIRECT",
}


def load_corpus() -> dict[str, Any]:
    return json.loads(ORCHESTRATION_CORPUS.read_text(encoding="utf-8"))


def test_canon_orchestration_corpus_is_explicitly_static_and_not_run() -> None:
    corpus = load_corpus()
    assert corpus["schemaVersion"] == 1
    assert corpus["toolkitVersion"] == "0.2.0"
    assert corpus["status"] == "supplemental"
    assert corpus["scope"] == "long-task canon orchestration"
    assert corpus["claimLevel"] == "static-contract-only"
    assert corpus["evidenceStatus"] == "NOT_RUN"


def test_canon_orchestration_case_ids_and_skill_names_are_valid() -> None:
    corpus = load_corpus()
    catalog = json.loads((ROOT / "catalog" / "skills.json").read_text(encoding="utf-8"))
    skill_names = {skill["name"] for skill in catalog["skills"]}
    cases = corpus["cases"]
    case_ids = [case["id"] for case in cases]

    assert len(case_ids) == len(set(case_ids))
    assert set(case_ids) == EXPECTED_CASE_IDS
    for case in cases:
        selected = set(case["expectedSelected"])
        not_selected = set(case["expectedNotSelected"])
        assert selected.isdisjoint(not_selected)
        assert selected | not_selected <= skill_names
        assert case["observablePass"].strip()


def test_corpus_contains_discriminating_negative_contracts() -> None:
    cases = {case["id"]: case for case in load_corpus()["cases"]}
    assert cases["CANON-ORCHESTRATION-UNAUTHORIZED-DOWNGRADE"]["class"] == "negative"
    assert "transition is rejected" in cases[
        "CANON-ORCHESTRATION-UNAUTHORIZED-DOWNGRADE"
    ]["observablePass"]
    assert cases["CANON-ORCHESTRATION-OWNER-RECLASSIFICATION"]["class"] == "negative"
    assert "reclassification is rejected" in cases[
        "CANON-ORCHESTRATION-OWNER-RECLASSIFICATION"
    ]["observablePass"]
    assert cases["CANON-ORCHESTRATION-LOOP-BUDGET"]["class"] == "negative"
    assert "BLOCKED or INCOMPLETE" in cases[
        "CANON-ORCHESTRATION-LOOP-BUDGET"
    ]["observablePass"]


def test_engineering_wal_links_the_opt_in_profile_and_keeps_the_direct_path() -> None:
    skill = WAL_SKILL.read_text(encoding="utf-8")
    reference = ORCHESTRATION_REFERENCE.read_text(encoding="utf-8")

    assert "references/canon-orchestration.md" in skill
    assert "commitment floor" in skill.lower()
    assert "releaseOverall" in skill
    assert "Keep the direct path" in reference
    assert "Roles are responsibilities" in reference
    assert "daemon, database" in reference.lower()


@pytest.mark.parametrize(
    "required_contract",
    (
        "Freeze the commitment floor",
        "Role separation alone is not independence",
        "Loop A: specification convergence",
        "Loop B: delivery convergence",
        "Shadow specification reopen",
        "evidence-observing owner classifies",
        "CORE_DEFECT",
        "SPEC_GAP",
        "SEAM_DEFECT",
        "HARNESS_OR_ENV_BLOCKER",
        "AUTHORITY_OR_EXTERNAL_BLOCKER",
        "REVIEW_COVERAGE_GAP",
        "releaseOverall = INCOMPLETE",
        "validate_orchestration_transition.py",
        "readinessAuthority",
        "decisionReceipts",
        "dispositionOwner",
        "signatureHistory",
        "Exact input snapshot bytes",
        "Envelope governance and compatibility",
        "Unknown versions fail closed",
        "Completion guard",
    ),
)
def test_canon_orchestration_reference_preserves_required_contracts(
    required_contract: str,
) -> None:
    reference = ORCHESTRATION_REFERENCE.read_text(encoding="utf-8")
    assert required_contract in reference


def test_pm_cannot_own_finding_classification_and_baton_has_no_bypass() -> None:
    reference = ORCHESTRATION_REFERENCE.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "The PM may route but cannot rewrite it" in reference
    assert "PM classifies every finding" not in reference
    assert "If Baton is unavailable, do not dispatch around it" in workflow
    assert "when available" not in workflow


def test_transition_guard_enforces_receipts_resets_cycles_and_exact_input_identity() -> None:
    guard = TRANSITION_GUARD.read_text(encoding="utf-8")

    for token in (
        "POSITIVE_DECISION_PROMOTION",
        "IDENTITY_RESET_REQUIRED",
        "DECISION_RECEIPT_PREFIX",
        "AMENDMENT_EVIDENCE_BINDING",
        "INVALIDATED_EVIDENCE_REUSE",
        "FINDING_EVIDENCE_REMOVED",
        "VERDICT_COVERAGE",
        "COMMITMENT_COVERAGE",
        "LOOP_SIGNATURE_REPEAT",
        "LOOP_SIGNATURE_BINDING",
        "LOOP_PASS_DELTA",
        "LOOP_PASS_STATE",
        "LOOP_CLOSE_PASS",
        "LOOP_TERMINAL_TRANSITION",
        "FLOOR_ID_NAMESPACE",
        "JSON_DEPTH",
        "TERMINAL_TRANSITION",
        "previousSnapshotDigest",
        "currentSnapshotDigest",
    ):
        assert token in guard

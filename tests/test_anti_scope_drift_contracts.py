from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "cases" / "anti-scope-drift.json"

EXPECTED_CASE_IDS = [
    "SCOPE-DRIFT-BOUNDED-PROTOTYPE",
    "SCOPE-DRIFT-CLAIM-ESCALATION",
    "SCOPE-DRIFT-UNRELATED-CLEANUP",
    "SCOPE-DRIFT-AUTHORIZED-AMENDMENT",
    "NON-SCOPE-DRIFT-DIRECT-DEFECT",
]


def load_corpus() -> dict[str, Any]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def test_anti_scope_drift_corpus_has_static_contract_cases() -> None:
    corpus = load_corpus()
    assert corpus["schemaVersion"] == 1
    assert corpus["toolkitVersion"] == "0.3.0"
    assert corpus["status"] == "supplemental"
    assert corpus["scope"] == "anti-scope-drift decision boundary"
    assert corpus["claimLevel"] == "static-contract-only"
    assert corpus["evidenceStatus"] == "NOT_RUN"

    cases = corpus["cases"]
    assert [case["id"] for case in cases] == EXPECTED_CASE_IDS
    assert len(EXPECTED_CASE_IDS) == len(set(EXPECTED_CASE_IDS))

    catalog = json.loads((ROOT / "catalog" / "skills.json").read_text(encoding="utf-8"))
    skill_names = {skill["name"] for skill in catalog["skills"]}
    for case in cases:
        selected = set(case["expectedSelected"])
        not_selected = set(case["expectedNotSelected"])
        assert selected.isdisjoint(not_selected)
        assert selected | not_selected <= skill_names
        assert case["observablePass"].strip()
        assert case["prohibitedEffects"]


def test_scope_drift_cases_preserve_both_stop_and_authorized_direct_paths() -> None:
    cases = {case["id"]: case for case in load_corpus()["cases"]}

    bounded = cases["SCOPE-DRIFT-BOUNDED-PROTOTYPE"]
    assert bounded["expectedSelected"] == [
        "batch-complete-independent-review",
        "engineering-specification",
    ]
    assert "IN_SCOPE" in bounded["observablePass"]
    assert "SCOPE_GUARD" in bounded["observablePass"]
    assert "ADJACENT_RISK" in bounded["observablePass"]
    assert "formal release" in bounded["prohibitedEffects"]

    escalation = cases["SCOPE-DRIFT-CLAIM-ESCALATION"]
    assert escalation["expectedSelected"] == ["engineering-specification"]
    assert "scope-change checkpoint" in escalation["observablePass"]

    cleanup = cases["SCOPE-DRIFT-UNRELATED-CLEANUP"]
    assert "OUT_OF_SCOPE" in cleanup["observablePass"]

    amendment = cases["SCOPE-DRIFT-AUTHORIZED-AMENDMENT"]
    assert amendment["expectedSelected"] == [
        "batch-complete-independent-review",
        "completeness-and-test-synthesis",
    ]
    assert amendment["expectedNotSelected"] == ["engineering-specification"]
    assert "newly authorized claim" in amendment["observablePass"]

    direct = cases["NON-SCOPE-DRIFT-DIRECT-DEFECT"]
    assert direct["expectedSelected"] == ["engineering-implementation"]
    assert direct["expectedNotSelected"] == [
        "batch-complete-independent-review",
        "completeness-and-test-synthesis",
        "engineering-specification",
    ]


def test_scope_change_owner_and_handoff_guards_are_present() -> None:
    specification = (
        ROOT / "skills" / "engineering-specification" / "SKILL.md"
    ).read_text(encoding="utf-8")
    implementation = (
        ROOT / "skills" / "engineering-implementation" / "SKILL.md"
    ).read_text(encoding="utf-8")
    debugging = (ROOT / "skills" / "engineering-debugging" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    review = (
        ROOT / "skills" / "batch-complete-independent-review" / "SKILL.md"
    ).read_text(encoding="utf-8")
    completeness = (
        ROOT / "skills" / "completeness-and-test-synthesis" / "SKILL.md"
    ).read_text(encoding="utf-8")

    for fragment in (
        "A new finding is not new scope",
        "IN_SCOPE",
        "SCOPE_GUARD",
        "ADJACENT_RISK",
        "OUT_OF_SCOPE",
        "scope-change checkpoint",
        "authorized deliverable",
        "authorized claim",
        "acceptance level",
        "release rigor",
        "system boundary",
        "If the finding is not addressed, does the authorized deliverable or claim fail?",
        "Can the original contract be preserved by a smaller containment or disclosure?",
    ):
        assert fragment.lower() in specification.lower()

    assert "A new finding is not new scope" in implementation
    assert "scope-change checkpoint" in implementation
    assert "severity does not grant scope" in debugging.lower()
    assert "severity does not grant scope" in review.lower()
    assert "claim budget" in completeness.lower()
    assert "does not authorize a larger claim" in completeness.lower()


def test_implementation_guard_preserves_authorized_direct_repairs() -> None:
    implementation = (
        ROOT / "skills" / "engineering-implementation" / "SKILL.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(implementation.split())

    assert (
        "An already authorized `IN_SCOPE` repair may change product behavior and write within the "
        "existing boundary without a checkpoint."
    ) in normalized
    assert (
        "Only when a proposed response is not already required by the authorized outcome and would "
        "raise the claim"
    ) in normalized
    assert (
        "If the proposed response changes product behavior, acceptance level, release rigor"
        not in normalized
    )
    assert "Already explicit small work proceeds directly" in normalized


def test_repository_guidance_exposes_the_rule_without_a_new_skill() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.en.md").read_text(encoding="utf-8")
    taxonomy = (ROOT / "docs" / "taxonomy.md").read_text(encoding="utf-8")
    product_spec = (ROOT / "docs" / "product-specification.md").read_text(
        encoding="utf-8"
    )

    assert "A new finding is not new scope" in agents
    assert "A new finding is not new scope" in readme
    assert "engineering-specification" in taxonomy
    assert "scope-change checkpoint" in taxonomy
    normalized_taxonomy = " ".join(taxonomy.lower().split())
    assert "does not create a seventeenth skill" in normalized_taxonomy
    assert "Material findings receive scope classification" in product_spec


def test_anti_scope_drift_eval_is_public_safe() -> None:
    serialized = CASES_PATH.read_text(encoding="utf-8").lower()
    for private_fragment in (
        ":\\",
        "/home/",
        "/users/",
        "-----begin private key-----",
        "github_pat_",
        "ghp_",
        "internal milestone",
    ):
        assert private_fragment not in serialized

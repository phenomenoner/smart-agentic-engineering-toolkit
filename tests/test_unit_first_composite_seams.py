from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "cases" / "unit-first-composite-seams.json"

EXPECTED_CASE_IDS = [
    "COMPOSITE-SEAM-UNIT-FIRST",
    "COMPOSITE-SEAM-COMPOSITION-BEFORE-NATIVE",
    "COMPOSITE-SEAM-LUNA-ELIGIBLE",
    "COMPOSITE-SEAM-NON-LUNA-JUDGMENT",
    "NON-COMPOSITE-SEAM-DIRECT",
]


def load_corpus() -> dict[str, Any]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def test_composite_seam_corpus_has_discriminating_routes() -> None:
    corpus = load_corpus()
    assert corpus["schemaVersion"] == 1
    assert corpus["toolkitVersion"] == "0.4.0"
    assert corpus["status"] == "supplemental"
    assert corpus["scope"] == "unit-first composite-seam and model-routing decision boundary"
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
        assert case["prohibitedEffects"].strip()


def test_unit_composition_and_native_order_is_explicit() -> None:
    cases = {case["id"]: case for case in load_corpus()["cases"]}

    unit_first = cases["COMPOSITE-SEAM-UNIT-FIRST"]
    assert unit_first["expectedSelected"] == [
        "engineering-implementation",
        "completeness-and-test-synthesis",
    ]
    assert "total contract-relevant failure partition" in unit_first["observablePass"]
    assert "full Cartesian" in unit_first["prohibitedEffects"]

    composition = cases["COMPOSITE-SEAM-COMPOSITION-BEFORE-NATIVE"]
    assert "adjacent-link or whole-composition" in composition["observablePass"]
    assert "before running" in composition["observablePass"]
    assert "native reruns do not substitute" in composition["prohibitedEffects"]

    direct = cases["NON-COMPOSITE-SEAM-DIRECT"]
    assert direct["expectedSelected"] == ["engineering-implementation"]
    assert "direct implementation path" in direct["observablePass"]
    assert "No failure-partition matrix" in direct["prohibitedEffects"]


def test_baton_model_routes_keep_judgment_and_synthesis_out_of_luna() -> None:
    cases = {case["id"]: case for case in load_corpus()["cases"]}
    eligible = cases["COMPOSITE-SEAM-LUNA-ELIGIBLE"]
    assert eligible["expectedNotSelected"] == ["codex-cli-luna-worker"]
    assert "native gpt-5.6-luna at max" in eligible["observablePass"]
    assert "main agent" in eligible["observablePass"]

    judgment = cases["COMPOSITE-SEAM-NON-LUNA-JUDGMENT"]
    assert judgment["expectedSelected"] == [
        "engineering-specification",
        "batch-complete-independent-review",
        "completeness-and-test-synthesis",
    ]
    assert judgment["expectedNotSelected"] == ["codex-cli-luna-worker"]
    assert "gpt-5.6-sol at high" in judgment["observablePass"]
    assert "Luna does not approve" in judgment["prohibitedEffects"]


def test_skill_and_integration_contracts_form_one_conditional_ladder() -> None:
    implementation = (
        ROOT / "skills" / "engineering-implementation" / "SKILL.md"
    ).read_text(encoding="utf-8")
    completeness = (
        ROOT / "skills" / "completeness-and-test-synthesis" / "SKILL.md"
    ).read_text(encoding="utf-8")
    review = (
        ROOT / "skills" / "batch-complete-independent-review" / "SKILL.md"
    ).read_text(encoding="utf-8")
    integrations = (ROOT / "docs" / "integrations.md").read_text(encoding="utf-8")

    implementation = " ".join(implementation.split())
    completeness = " ".join(completeness.split())
    review = " ".join(review.split())
    integrations = " ".join(integrations.split())

    assert "multiple links that can fail independently" in implementation
    assert "total contract-relevant failure partition" in implementation
    assert "do not manufacture the full Cartesian product" in implementation
    assert "adjacent-link or whole-composition test" in implementation
    assert "Do not impose this ladder on one simple local seam" in implementation

    assert "Require a unit-first ladder only for composite seams" in completeness
    assert "A green high-altitude run does not fill a missing link partition" in completeness
    assert "not a mandatory test pyramid" in completeness

    assert "Never route independent review through Luna" in review
    assert "`gpt-5.6-sol` at `high`" in review
    assert "native `gpt-5.6-luna` at `max`" in integrations
    assert "main agent keeps" in integrations


def test_composite_seam_eval_is_public_safe() -> None:
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

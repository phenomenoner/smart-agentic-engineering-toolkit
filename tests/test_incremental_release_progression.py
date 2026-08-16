from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "cases" / "incremental-release-progression.json"


def load_cases() -> list[dict[str, object]]:
    document = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    assert document["status"] == "supplemental"
    return document["cases"]


def test_incremental_release_eval_has_five_discriminating_cases() -> None:
    cases = load_cases()
    assert [case["id"] for case in cases] == [
        "INCREMENTAL-RELEASE-DOCS-ONLY",
        "INCREMENTAL-RELEASE-REVIEW-ENVELOPE",
        "INCREMENTAL-RELEASE-RUNTIME-SEAM",
        "INCREMENTAL-RELEASE-SEMANTIC-CHANGE",
        "NON-INCREMENTAL-RELEASE-ORDINARY-CHANGE",
    ]

    by_id = {case["id"]: case for case in cases}
    assert by_id["INCREMENTAL-RELEASE-DOCS-ONLY"]["expectedSelected"] == [
        "completeness-and-test-synthesis"
    ]
    assert by_id["INCREMENTAL-RELEASE-REVIEW-ENVELOPE"]["expectedSelected"] == [
        "batch-complete-independent-review",
        "completeness-and-test-synthesis",
    ]
    assert by_id["INCREMENTAL-RELEASE-RUNTIME-SEAM"]["expectedSelected"] == [
        "completeness-and-test-synthesis"
    ]
    assert by_id["INCREMENTAL-RELEASE-SEMANTIC-CHANGE"]["expectedSelected"] == [
        "batch-complete-independent-review",
        "completeness-and-test-synthesis",
    ]
    assert by_id["NON-INCREMENTAL-RELEASE-ORDINARY-CHANGE"]["expectedNotSelected"] == [
        "batch-complete-independent-review",
        "completeness-and-test-synthesis",
    ]


def test_release_progression_contract_is_owned_and_incremental() -> None:
    completeness = (
        ROOT / "skills" / "completeness-and-test-synthesis" / "SKILL.md"
    ).read_text(encoding="utf-8")
    progression = (
        ROOT
        / "skills"
        / "completeness-and-test-synthesis"
        / "references"
        / "incremental-release-progression.md"
    ).read_text(encoding="utf-8")
    batch_review = (
        ROOT / "skills" / "batch-complete-independent-review" / "SKILL.md"
    ).read_text(encoding="utf-8")
    implementation = (
        ROOT / "skills" / "engineering-implementation" / "SKILL.md"
    ).read_text(encoding="utf-8")

    for fragment in (
        "exact changed Git objects",
        "source correctness",
        "artifact identity",
        "installed instance",
        "live host",
        "external publication",
        "affected cells",
        "fail closed",
    ):
        assert fragment.lower() in (completeness + progression).lower()

    for fragment in (
        "documentation-only",
        "review envelope or locator",
        "launcher, plugin manifest, bundled skill, or runtime dependency",
        "executable semantic change",
        "one final exact install",
        "download and read back",
    ):
        assert fragment.lower() in progression.lower()

    assert "intake, binding, or review-tool defect" in batch_review.lower()
    assert "does not become a candidate-behavior finding" in batch_review.lower()
    assert "first executable seam" in implementation.lower()
    assert "does not activate formal release machinery" in implementation.lower()


def test_incremental_release_eval_is_public_safe() -> None:
    serialized = CASES_PATH.read_text(encoding="utf-8").lower()
    for private_fragment in (":\\", "/home/", "/users/", "internal milestone"):
        assert private_fragment not in serialized

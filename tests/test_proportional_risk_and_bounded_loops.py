from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "cases" / "proportional-risk-and-bounded-loops.json"

EXPECTED_CASE_IDS = [
    "RISK-LOW-LOW-BOUNDED-FAIL-OPEN",
    "RISK-HIGH-LOW-EFFECT-LOCAL-FAIL-CLOSED",
    "RISK-LOW-HIGH-OPERABILITY-REPAIR",
    "RISK-L3-SEAM-LOCAL-NONCONTAGION",
    "LOOP-SAME-CAUSE-BUDGET-STOP",
    "LOOP-CONSTRUCTIBILITY-BEFORE-FORMAL-MATRIX",
    "POLICY-VERSION-REBIND-CHECKPOINT",
]


def load_corpus() -> dict[str, Any]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_proportional_risk_corpus_is_exact_and_public_safe() -> None:
    corpus = load_corpus()
    assert corpus["schemaVersion"] == 1
    assert corpus["toolkitVersion"] == "0.5.0"
    assert corpus["status"] == "supplemental"
    assert corpus["scope"] == "seam-local proportional risk, bounded loops, and policy binding"
    assert corpus["claimLevel"] == "static-contract-only"
    assert corpus["evidenceStatus"] == "NOT_RUN"

    cases = corpus["cases"]
    assert [case["id"] for case in cases] == EXPECTED_CASE_IDS
    assert len(EXPECTED_CASE_IDS) == len(set(EXPECTED_CASE_IDS))
    for case in cases:
        assert case["observablePass"].strip()
        assert case["prohibitedEffects"].strip()

    serialized = CASES_PATH.read_text(encoding="utf-8").lower()
    for private_fragment in (
        ":\\\\",
        "/home/",
        "/users/",
        "github_pat_",
        "ghp_",
        "internal milestone",
        "hc-r0",
    ):
        assert private_fragment not in serialized


def test_risk_disposition_is_cross_skill_and_effect_local() -> None:
    owner_paths = [
        "skills/engineering-specification/SKILL.md",
        "skills/engineering-debugging/SKILL.md",
        "skills/engineering-implementation/SKILL.md",
        "skills/batch-complete-independent-review/SKILL.md",
        "skills/completeness-and-test-synthesis/SKILL.md",
    ]
    for path in owner_paths:
        text = " ".join(read(path).split())
        assert "consequence × estimated frequency" in text, path
        assert "bounded fail-open" in text, path
        assert "affected effect boundary" in text, path

    review = read("skills/batch-complete-independent-review/SKILL.md")
    protocol = read("skills/batch-complete-independent-review/references/protocol.md")
    for text in (review, protocol):
        assert "risk-local" in text
        assert "candidate-wide L3 contagion" in text
        assert "LOW × LOW" in text


def test_installation_routes_by_host_without_creating_a_second_source() -> None:
    installation = read("docs/installation.md")
    migration = read("docs/migration.md")
    readme = read("README.en.md")

    for fragment in [
        "Codex App plugin",
        "Hermes Agent native skills",
        "Other Agent Skills-compatible harnesses",
        "canonical repository is the only writable source",
        "hermes skills list --source local --enabled-only",
        'hermes chat -q "/engineering-implementation',
        "fresh Hermes session",
    ]:
        assert fragment in installation, fragment

    assert "Do not project the same toolkit-owned skill through multiple routes" in installation
    assert "hermes skills inspect" not in installation
    assert "A duplicate name is not the only conflict" in migration
    assert "universally requires a plan, specification, TDD, WAL, worktree, subagent, full suite" in migration
    assert "Disable or narrow the broader rule" in migration
    assert "## Host-native installation" in readme
    assert "Never treat a plugin cache or installed projection as source" in readme


def test_unbounded_review_and_reopen_rules_are_retired() -> None:
    review = read("skills/batch-complete-independent-review/SKILL.md")
    protocol = read("skills/batch-complete-independent-review/references/protocol.md")
    synthesis_schema = read(
        "skills/batch-complete-independent-review/references/synthesis.schema.json"
    )
    cross_audit_schema = read(
        "skills/batch-complete-independent-review/references/cross-audit.schema.json"
    )
    review_gate = read("skills/batch-complete-independent-review/scripts/review_gate.py")

    assert "Every finding and assumption creates reopen obligations" not in protocol
    assert "Repeat full matrix traversal until no blocker" not in review
    assert "iterate again" not in protocol
    assert "every finding's required regression cells" not in protocol
    assert "every assumption's reopened cells" not in protocol
    assert "same-cause retry limit" in review
    assert "full-review wave limit" in review
    assert "An unchanged third attempt is prohibited" in review
    assert "A third full reviewer is prohibited" in review
    assert "A third full reviewer is prohibited" in protocol
    assert "Trigger a third reviewer" not in review
    assert "Start a third reviewer" not in protocol
    assert "thirdReviewerRequired" not in synthesis_schema
    assert "thirdReviewerRequired" not in review_gate
    assert "THIRD_REVIEW_REQUIRED" not in cross_audit_schema
    assert "THIRD_REVIEW_REQUIRED" not in review_gate
    assert "a required matrix partition remains unowned or over budget" not in protocol
    assert "Budget exhaustion is not an escalation trigger" in protocol
    assert "budget exhaustion returns `INCOMPLETE`" in protocol
    assert "accepted residual" in protocol.lower()


def test_canon_activation_has_numeric_budgets_and_policy_binding() -> None:
    canon = read("skills/engineering-wal/references/canon-orchestration.md")
    wal = read("skills/engineering-wal/SKILL.md")
    workflow = read("workflows/specify-implement-review-drill.md")

    for fragment in (
        "policyBinding:",
        "toolkitVersion:",
        "toolkitCommit:",
        "bindingState:",
        "specificationPasses: 2",
        "deliveryPasses: 2",
        "sameCauseRetries: 2",
        "fullReviewWaves: 1",
        "silent policy mixing is prohibited",
    ):
        assert fragment in canon

    assert "numeric loop budgets" in wal
    assert "No numeric budget, no canon activation" in workflow
    assert "constructibility check" in workflow


def test_public_guidance_exposes_proportionality_without_a_new_skill() -> None:
    agents = read("AGENTS.md")
    readme = read("README.en.md")
    product = read("docs/product-specification.md")
    taxonomy = read("docs/taxonomy.md")

    for text in (agents, readme, product, taxonomy):
        normalized = " ".join(text.split())
        assert "consequence × estimated frequency" in normalized
        assert "bounded fail-open" in normalized

    normalized = " ".join(taxonomy.split())
    assert "does not create a new skill" in normalized
    assert "No new persistent risk registry" in normalized

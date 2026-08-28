from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "evals" / "cases" / "canon-orchestration.json"
REFERENCE = ROOT / "skills" / "engineering-wal" / "references" / "canon-orchestration.md"


def pmo_cases() -> dict[str, dict[str, object]]:
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    return {case["id"]: case for case in payload["cases"] if case["id"].startswith("CANON-PMO-")}


def test_pmo_luna_execution_defaults_to_verified_prime_minion() -> None:
    case = pmo_cases()["CANON-PMO-PRIME-MINION-EXECUTION-DEFAULT"]
    assert case["class"] == "routing"
    assert case["expectedSelected"] == ["engineering-implementation", "engineering-wal"]
    pass_text = str(case["observablePass"])
    prohibited = str(case["prohibitedEffects"])
    assert "defaults the execution worker to a Prime Agent minion" in pass_text
    assert all(field in pass_text for field in ("provider", "model", "reasoning_effort"))
    assert "effective-route mismatch" in pass_text
    assert "does not receive provider credentials" in prohibited
    assert "replace the main agent's final claim" in prohibited


def test_pmo_terra_review_selects_subagent_or_minion_by_complexity() -> None:
    case = pmo_cases()["CANON-PMO-TERRA-REVIEW-ROUTE-CHOICE"]
    assert case["class"] == "routing"
    assert case["expectedSelected"] == ["batch-complete-independent-review", "engineering-wal"]
    assert case["expectedNotSelected"] == ["engineering-implementation"]
    pass_text = str(case["observablePass"])
    prohibited = str(case["prohibitedEffects"])
    assert "native subagent or Prime minion" in pass_text
    assert "task complexity" in pass_text
    assert "read-only frozen inputs" in pass_text
    assert "not hard-wired to either substrate" in prohibited


def test_pmo_minion_unavailable_falls_back_without_route_fabrication() -> None:
    case = pmo_cases()["CANON-PMO-MINION-UNAVAILABLE-FALLBACK"]
    assert case["class"] == "routing-negative"
    pass_text = str(case["observablePass"])
    prohibited = str(case["prohibitedEffects"])
    assert "eligible native subagent or direct work" in pass_text
    assert "does not silently change a provider/model/effort request" in pass_text
    assert "does not fabricate a CLI model bridge" in prohibited
    assert "expose provider credentials" in prohibited


def test_required_independent_review_never_falls_back_to_main_agent_self_review() -> None:
    reference = REFERENCE.read_text(encoding="utf-8")
    assert "distinct eligible reviewer or stop `INCOMPLETE`" in reference
    assert "a direct main-agent pass cannot satisfy independence" in reference

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

MECHANISM_CASE_CONTRACTS = {
    "ACT-SPEC-MECH-01": {
        "id": "ACT-SPEC-MECH-01",
        "class": "activation",
        "promptOrCondition": (
            "Design a durable lease ledger to enforce single-writer publication even though "
            "the host already exposes one atomic compare-and-swap primitive."
        ),
        "expectedSelected": ["engineering-specification"],
        "expectedNotSelected": ["engineering-implementation"],
        "observablePass": (
            "The output states the observable outcome and invariant, separates the ledger from "
            "the outcome, asks both necessity questions, compares deletion, manual operation, "
            "embedding or ephemeral state, the existing platform primitive, and persistent "
            "state in order, budgets complexity/authority/recovery/failure-state cost, and "
            "rejects the durable ledger unless restart survival is demonstrated."
        ),
    },
    "NON-SPEC-MECH-01": {
        "id": "NON-SPEC-MECH-01",
        "class": "nonactivation",
        "promptOrCondition": (
            "Implement this explicit one-line compare-and-swap contract with the existing host "
            "primitive and run its focused unit test."
        ),
        "expectedSelected": ["engineering-implementation"],
        "expectedNotSelected": ["engineering-specification"],
        "observablePass": (
            "The already explicit small contract keeps the direct implementation path; no "
            "separate necessity packet or new persistent mechanism is created."
        ),
    },
}


@pytest.mark.parametrize("case_id", MECHANISM_CASE_CONTRACTS)
def test_first_principles_mechanism_case_contract_is_exact(case_id: str) -> None:
    corpus = json.loads((ROOT / "evals" / "cases" / "acceptance.json").read_text(encoding="utf-8"))
    matches = [case for case in corpus["cases"] if case.get("id") == case_id]
    assert matches == [MECHANISM_CASE_CONTRACTS[case_id]]

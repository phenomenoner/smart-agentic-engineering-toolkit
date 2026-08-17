from __future__ import annotations

import copy
import hashlib
import json
import runpy
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "skills"
    / "engineering-wal"
    / "scripts"
    / "validate_orchestration_transition.py"
)
GUARD = runpy.run_path(str(SCRIPT))
floor_digest = GUARD["floor_digest"]
pass_signature = GUARD["pass_signature"]
validate_snapshot = GUARD["validate_snapshot"]
validate_transition = GUARD["validate_transition"]
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64


def decision_receipt(value: dict[str, Any], *, cell: str, decision: str, evidence: str) -> dict[str, Any]:
    return {
        "id": f"receipt-{cell.replace(':', '-')}-{decision.lower()}-1",
        "cell": cell,
        "decision": decision,
        "authority": value["commitmentFloor"]["readinessAuthority"],
        "floorDigest": value["commitmentFloor"]["digest"],
        "specificationDigest": value["specification"]["digest"],
        "candidateDigest": value["candidate"]["digest"],
        "evidenceIds": [evidence],
        "reason": "Completeness owner bound this positive decision to reviewed evidence.",
    }


def snapshot(*, generation: int = 1, done: bool = False) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schemaVersion": 1,
        "taskId": "task-001",
        "generation": generation,
        "commitmentFloor": {
            "generation": 1,
            "outcome": "Ship the requested qualified product behavior",
            "targetTerminalStage": "qualified",
            "readinessAuthority": "completeness-owner",
            "requirementIds": ["REQ-1"],
            "acceptanceIds": ["ACCEPT-1"],
            "requiredSeams": ["windows-native"],
            "amendmentAuthorities": ["user-owner"],
            "digest": "",
        },
        "specification": {"generation": 1, "digest": DIGEST_A},
        "candidate": {"generation": 1, "digest": DIGEST_B},
        "commitments": {
            "REQ-1": {"status": "SUPPORTED", "evidenceIds": ["evidence-core"]},
            "ACCEPT-1": {"status": "SUPPORTED", "evidenceIds": ["evidence-acceptance"]},
        },
        "verdicts": {
            "core": "PASS",
            "seams": {"windows-native": "PASS"},
            "release": {"windows-native": "READY"},
            "releaseOverall": "READY" if done else "INCOMPLETE",
        },
        "findings": [],
        "decisionReceipts": [],
        "loopBudgets": {
            "specification": {
                "status": "CLOSED",
                "maxPasses": 3,
                "usedPasses": 1,
                "lastFindingSignature": "spec-ready-1",
                "signatureHistory": ["spec-ready-1"],
            },
            "delivery": {
                "status": "CLOSED" if done else "ACTIVE",
                "maxPasses": 3,
                "usedPasses": 1 if done else 0,
                "lastFindingSignature": "delivery-ready-1" if done else None,
                "signatureHistory": ["delivery-ready-1"] if done else [],
            },
        },
        "completion": {
            "status": "DONE" if done else "IN_PROGRESS",
            "achievedStage": "qualified" if done else None,
        },
        "amendments": [],
    }
    value["commitmentFloor"]["digest"] = floor_digest(value)
    value["decisionReceipts"] = [
        decision_receipt(value, cell="core", decision="PASS", evidence="evidence-core"),
        decision_receipt(
            value,
            cell="seam:windows-native",
            decision="PASS",
            evidence="evidence-windows-seam",
        ),
        decision_receipt(
            value,
            cell="release:windows-native",
            decision="READY",
            evidence="evidence-windows-release",
        ),
    ]
    if done:
        value["decisionReceipts"].append(
            decision_receipt(
                value,
                cell="releaseOverall",
                decision="READY",
                evidence="evidence-acceptance",
            )
        )
    return value


def codes(errors: list[dict[str, str]]) -> set[str]:
    return {error["code"] for error in errors}


def append_delivery_pass(
    previous: dict[str, Any], current: dict[str, Any], *, status: str = "CLOSED"
) -> None:
    receipt = decision_receipt(
        current,
        cell="core",
        decision="PASS",
        evidence=f"evidence-delivery-pass-{current['generation']}",
    )
    receipt["id"] = f"receipt-delivery-pass-{current['generation']}"
    current["decisionReceipts"].append(receipt)
    signature = pass_signature(previous, current, "delivery")
    old_budget = previous["loopBudgets"]["delivery"]
    current["loopBudgets"]["delivery"].update(
        usedPasses=old_budget["usedPasses"] + 1,
        status=status,
        lastFindingSignature=signature,
        signatureHistory=[*old_budget["signatureHistory"], signature],
    )


def finding(*, finding_class: str = "CORE_DEFECT") -> dict[str, Any]:
    return {
        "id": "F-1",
        "blocking": True,
        "class": finding_class,
        "status": "OPEN",
        "ownerDisposition": "OPEN",
        "classificationOwner": "qc-owner",
        "dispositionOwner": "spec-owner" if finding_class == "SPEC_GAP" else "completeness-owner",
        "firstUnsafeOperation": "candidate violates REQ-1",
        "affectedCells": ["core/REQ-1"],
        "evidenceIds": ["evidence-failure"],
        "reclassifications": [],
    }


def reclassify_finding(value: dict[str, Any]) -> None:
    item = value["findings"][0]
    item["class"] = "HARNESS_OR_ENV_BLOCKER"
    item["ownerDisposition"] = "RECLASSIFIED"
    item["evidenceIds"].append("evidence-host-start")
    item["reclassifications"].append(
        {
            "oldClass": "CORE_DEFECT",
            "newClass": "HARNESS_OR_ENV_BLOCKER",
            "authority": "qc-owner",
            "oldDispositionOwner": "completeness-owner",
            "newDispositionOwner": "completeness-owner",
            "reason": "New evidence shows failure before product execution.",
            "affectedCells": item["affectedCells"],
            "firstUnsafeOperation": item["firstUnsafeOperation"],
            "evidenceIds": item["evidenceIds"],
        }
    )


def authorized_floor_change(previous: dict[str, Any]) -> dict[str, Any]:
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["commitmentFloor"]["generation"] += 1
    current["commitmentFloor"]["targetTerminalStage"] = "production-qualified"
    current["commitmentFloor"]["digest"] = floor_digest(current)
    current["completion"] = {"status": "IN_PROGRESS", "achievedStage": None}
    current["verdicts"]["core"] = "NOT_RUN"
    current["verdicts"]["seams"]["windows-native"] = "NOT_RUN"
    current["verdicts"]["release"]["windows-native"] = "INCOMPLETE"
    current["verdicts"]["releaseOverall"] = "INCOMPLETE"
    current["commitments"]["ACCEPT-1"] = {"status": "NOT_RUN", "evidenceIds": []}
    current["loopBudgets"]["specification"]["status"] = "ACTIVE"
    current["loopBudgets"]["delivery"]["status"] = "ACTIVE"
    current["amendments"].append(
        {
            "fromFloorGeneration": previous["commitmentFloor"]["generation"],
            "toFloorGeneration": current["commitmentFloor"]["generation"],
            "previousFloorDigest": previous["commitmentFloor"]["digest"],
            "newFloorDigest": current["commitmentFloor"]["digest"],
            "oldTarget": previous["commitmentFloor"]["targetTerminalStage"],
            "newTarget": current["commitmentFloor"]["targetTerminalStage"],
            "authority": "user-owner",
            "reason": "The product owner explicitly raised the terminal target.",
            "affectedRequirementIds": [],
            "affectedAcceptanceIds": ["ACCEPT-1"],
            "affectedSeams": ["windows-native"],
            "invalidatedEvidenceIds": [
                "evidence-acceptance",
                "evidence-windows-seam",
                "evidence-windows-release",
            ],
        }
    )
    return current


def replace_floor_namespace(previous: dict[str, Any], *, kind: str) -> dict[str, Any]:
    current = copy.deepcopy(previous)
    current["generation"] += 1
    floor = current["commitmentFloor"]
    floor["generation"] += 1
    if kind == "seam":
        floor["requiredSeams"] = ["linux"]
        affected_requirements: list[str] = []
        affected_seams = ["linux", "windows-native"]
    else:
        floor["requirementIds"] = ["REQ-2"]
        affected_requirements = ["REQ-1", "REQ-2"]
        affected_seams = []
        current["commitments"] = {
            "REQ-2": {"status": "NOT_RUN", "evidenceIds": []},
            "ACCEPT-1": current["commitments"]["ACCEPT-1"],
        }
    floor["digest"] = floor_digest(current)
    current["completion"] = {"status": "IN_PROGRESS", "achievedStage": None}
    current["verdicts"] = {
        "core": "NOT_RUN",
        "seams": {seam: "NOT_RUN" for seam in floor["requiredSeams"]},
        "release": {seam: "INCOMPLETE" for seam in floor["requiredSeams"]},
        "releaseOverall": "INCOMPLETE",
    }
    current["loopBudgets"]["specification"]["status"] = "ACTIVE"
    current["loopBudgets"]["delivery"]["status"] = "ACTIVE"

    affected_tokens = set(affected_requirements) | set(affected_seams)
    invalidated: set[str] = set()
    for claim_id, cell in previous["commitments"].items():
        if claim_id in affected_tokens:
            invalidated.update(cell["evidenceIds"])
    for item in previous["findings"]:
        if any(
            token in cell
            for token in affected_tokens
            for cell in item["affectedCells"]
        ):
            invalidated.update(item["evidenceIds"])
            for record in item["reclassifications"]:
                invalidated.update(record["evidenceIds"])
            if item["closure"] is not None:
                invalidated.update(item["closure"]["evidenceIds"])
    latest_receipts = {
        receipt["cell"]: receipt for receipt in previous["decisionReceipts"]
    }
    for seam in affected_seams:
        for cell in (f"seam:{seam}", f"release:{seam}"):
            receipt = latest_receipts.get(cell)
            if receipt is not None:
                invalidated.update(receipt["evidenceIds"])

    current["amendments"].append(
        {
            "fromFloorGeneration": previous["commitmentFloor"]["generation"],
            "toFloorGeneration": floor["generation"],
            "previousFloorDigest": previous["commitmentFloor"]["digest"],
            "newFloorDigest": floor["digest"],
            "oldTarget": previous["commitmentFloor"]["targetTerminalStage"],
            "newTarget": floor["targetTerminalStage"],
            "authority": "user-owner",
            "reason": f"Replace the frozen {kind} namespace.",
            "affectedRequirementIds": affected_requirements,
            "affectedAcceptanceIds": [],
            "affectedSeams": affected_seams,
            "invalidatedEvidenceIds": sorted(invalidated),
        }
    )
    return current


@pytest.mark.parametrize("malformed", [None, [], {}, True, {"schemaVersion": 1}])
def test_malformed_snapshots_return_errors_instead_of_crashing(malformed: object) -> None:
    assert validate_transition(snapshot(), malformed)
    assert validate_transition(malformed, snapshot(generation=2))


def test_every_schema_node_rejects_unhashable_json_values_without_crashing() -> None:
    def paths(value: object, prefix: tuple[str | int, ...] = ()) -> list[tuple[str | int, ...]]:
        found: list[tuple[str | int, ...]] = []
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = (*prefix, key)
                found.append(child_path)
                found.extend(paths(child, child_path))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                child_path = (*prefix, index)
                found.append(child_path)
                found.extend(paths(child, child_path))
        return found

    baseline = snapshot(generation=2)
    for path in paths(baseline):
        for replacement in ([], {}):
            current = copy.deepcopy(baseline)
            parent: Any = current
            for component in path[:-1]:
                parent = parent[component]
            if parent[path[-1]] == replacement:
                continue
            parent[path[-1]] = replacement
            assert validate_transition(snapshot(), current), path


def test_floor_digest_ignores_list_order_but_binds_semantic_fields() -> None:
    first = snapshot()
    first["commitmentFloor"]["requirementIds"] = ["REQ-2", "REQ-1"]
    first["commitmentFloor"]["requiredSeams"] = ["linux", "windows-native"]
    first["commitmentFloor"]["amendmentAuthorities"] = ["user-owner", "release-owner"]

    second = copy.deepcopy(first)
    second["commitmentFloor"]["requirementIds"].reverse()
    second["commitmentFloor"]["requiredSeams"].reverse()
    second["commitmentFloor"]["amendmentAuthorities"].reverse()
    assert floor_digest(first) == floor_digest(second)

    second["commitmentFloor"]["targetTerminalStage"] = "implemented"
    assert floor_digest(first) != floor_digest(second)


def test_unchanged_floor_transition_can_reach_done() -> None:
    previous = snapshot()
    current = snapshot(generation=2, done=True)
    append_delivery_pass(previous, current)
    assert validate_transition(previous, current) == []


def test_silent_floor_downgrade_is_rejected() -> None:
    previous = snapshot()
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["commitmentFloor"]["generation"] += 1
    current["commitmentFloor"]["targetTerminalStage"] = "implemented"
    current["commitmentFloor"]["digest"] = floor_digest(current)

    assert "FLOOR_AMENDMENT_REQUIRED" in codes(validate_transition(previous, current))


def test_acceptance_scope_cannot_narrow_without_floor_amendment() -> None:
    previous = snapshot()
    previous["commitmentFloor"]["acceptanceIds"].append("ACCEPT-RESTART")
    previous["commitments"]["ACCEPT-RESTART"] = {
        "status": "SUPPORTED",
        "evidenceIds": ["evidence-restart"],
    }
    previous["commitmentFloor"]["digest"] = floor_digest(previous)
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["commitmentFloor"]["generation"] += 1
    current["commitmentFloor"]["acceptanceIds"].remove("ACCEPT-RESTART")
    current["commitmentFloor"]["digest"] = floor_digest(current)
    del current["commitments"]["ACCEPT-RESTART"]

    assert "FLOOR_AMENDMENT_REQUIRED" in codes(validate_transition(previous, current))


def test_authorized_append_only_floor_change_is_accepted() -> None:
    previous = snapshot()
    current = authorized_floor_change(previous)
    assert validate_transition(previous, current) == []


def test_unlisted_authority_cannot_amend_floor() -> None:
    previous = snapshot()
    current = authorized_floor_change(previous)
    current["amendments"][-1]["authority"] = "pm-agent"

    assert "AMENDMENT_AUTHORITY" in codes(validate_transition(previous, current))


def test_floor_amendment_must_bind_changed_acceptance_ids() -> None:
    previous = snapshot()
    previous["commitmentFloor"]["acceptanceIds"].append("ACCEPT-2")
    previous["commitments"]["ACCEPT-2"] = {
        "status": "SUPPORTED",
        "evidenceIds": ["evidence-acceptance-2"],
    }
    previous["commitmentFloor"]["digest"] = floor_digest(previous)
    current = authorized_floor_change(previous)
    current["commitmentFloor"]["acceptanceIds"].remove("ACCEPT-2")
    current["commitmentFloor"]["digest"] = floor_digest(current)
    del current["commitments"]["ACCEPT-2"]
    current["amendments"][-1]["newFloorDigest"] = current["commitmentFloor"]["digest"]

    assert "AMENDMENT_AFFECTED_BINDING" in codes(validate_transition(previous, current))


def test_floor_amendment_cannot_name_unknown_acceptance_ids() -> None:
    previous = snapshot()
    current = authorized_floor_change(previous)
    current["amendments"][-1]["affectedAcceptanceIds"] = ["ACCEPT-UNKNOWN"]

    assert "AMENDMENT_AFFECTED_BINDING" in codes(validate_transition(previous, current))


def test_floor_amendment_must_invalidate_evidence_from_affected_cells() -> None:
    previous = snapshot()
    current = authorized_floor_change(previous)
    current["amendments"][-1]["invalidatedEvidenceIds"].remove("evidence-acceptance")

    assert "AMENDMENT_EVIDENCE_BINDING" in codes(validate_transition(previous, current))


def test_floor_amendment_must_reset_affected_claim_cells() -> None:
    previous = snapshot()
    current = authorized_floor_change(previous)
    current["commitments"]["ACCEPT-1"] = {
        "status": "SUPPORTED",
        "evidenceIds": ["evidence-acceptance"],
    }

    assert "AMENDMENT_CLAIM_RESET" in codes(validate_transition(previous, current))


def test_invalidated_evidence_cannot_reappear_in_a_later_snapshot() -> None:
    previous = authorized_floor_change(snapshot())
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["commitments"]["ACCEPT-1"] = {
        "status": "SUPPORTED",
        "evidenceIds": ["evidence-acceptance"],
    }

    assert "INVALIDATED_EVIDENCE_REUSE" in codes(
        validate_transition(previous, current)
    )


def test_affected_claim_can_use_new_noninvalidated_evidence_later() -> None:
    previous = authorized_floor_change(snapshot())
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["commitments"]["ACCEPT-1"] = {
        "status": "SUPPORTED",
        "evidenceIds": ["evidence-acceptance-v2"],
    }

    assert validate_transition(previous, current) == []


def test_positive_decision_receipt_cannot_reuse_invalidated_evidence() -> None:
    previous = authorized_floor_change(snapshot())
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["verdicts"]["seams"]["windows-native"] = "PASS"
    receipt = decision_receipt(
        current,
        cell="seam:windows-native",
        decision="PASS",
        evidence="evidence-windows-seam",
    )
    receipt["id"] = "receipt-seam-windows-native-pass-2"
    current["decisionReceipts"].append(receipt)

    assert "INVALIDATED_EVIDENCE_REUSE" in codes(
        validate_transition(previous, current)
    )


def test_floor_change_cannot_retain_positive_verdicts_in_the_same_transition() -> None:
    previous = snapshot()
    current = authorized_floor_change(previous)
    current["verdicts"]["core"] = "PASS"

    assert "FLOOR_RESET_REQUIRED" in codes(validate_transition(previous, current))


def test_previous_amendments_are_append_only() -> None:
    original = snapshot()
    previous = authorized_floor_change(original)
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["amendments"][0]["reason"] = "Rewrite the historical reason."

    assert "AMENDMENT_PREFIX" in codes(validate_transition(previous, current))


def test_snapshot_rejects_a_broken_amendment_digest_chain() -> None:
    first = authorized_floor_change(snapshot())
    second = authorized_floor_change(first)
    second["amendments"][1]["previousFloorDigest"] = DIGEST_A

    assert "AMENDMENT_HISTORY_CHAIN" in codes(
        GUARD["validate_snapshot"](second, label="snapshot")
    )


def test_snapshot_rejects_an_incomplete_historical_amendment() -> None:
    value = authorized_floor_change(snapshot())
    del value["amendments"][0]["reason"]

    assert "AMENDMENTS_TYPE" in codes(GUARD["validate_snapshot"](value, label="snapshot"))


@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        (
            lambda value: value["completion"].update(achievedStage="implemented"),
            "DONE_TARGET_STAGE",
        ),
        (lambda value: value["verdicts"].update(core="INCOMPLETE"), "DONE_CORE"),
        (
            lambda value: value["verdicts"].update(releaseOverall="INCOMPLETE"),
            "DONE_RELEASE_OVERALL",
        ),
        (
            lambda value: value["verdicts"]["seams"].update(
                {"windows-native": "INCOMPLETE"}
            ),
            "DONE_REQUIRED_SEAM",
        ),
        (
            lambda value: value["findings"].append(
                {
                    "id": "F-1",
                    "blocking": True,
                    "class": "CORE_DEFECT",
                    "status": "OPEN",
                    "ownerDisposition": "OPEN",
                    "classificationOwner": "qc-owner",
                    "dispositionOwner": "completeness-owner",
                    "firstUnsafeOperation": "candidate violates REQ-1",
                    "affectedCells": ["core/REQ-1"],
                    "evidenceIds": ["evidence-failure"],
                    "reclassifications": [],
                }
            ),
            "DONE_BLOCKING_FINDING",
        ),
        (
            lambda value: value["commitments"]["REQ-1"].update(evidenceIds=[]),
            "DONE_REQUIREMENT",
        ),
        (
            lambda value: value["commitments"]["ACCEPT-1"].update(evidenceIds=[]),
            "DONE_REQUIREMENT",
        ),
        (lambda value: value["specification"].update(digest=None), "DONE_SPECIFICATION"),
        (lambda value: value["candidate"].update(digest=None), "DONE_CANDIDATE"),
        (lambda value: value["candidate"].update(generation=0), "DONE_CANDIDATE"),
        (
            lambda value: value["loopBudgets"]["delivery"].update(status="ACTIVE"),
            "DONE_LOOP_STATUS",
        ),
        (
            lambda value: value["loopBudgets"]["delivery"].update(
                usedPasses=0,
                lastFindingSignature=None,
                signatureHistory=[],
            ),
            "DONE_LOOP_STATUS",
        ),
    ],
)
def test_done_is_rejected_when_a_required_claim_is_open(
    mutate: Callable[[dict[str, Any]], None], expected_code: str
) -> None:
    previous = snapshot()
    current = snapshot(generation=2, done=True)
    mutate(current)

    assert expected_code in codes(validate_transition(previous, current))


def test_release_ready_cannot_launder_an_incomplete_seam() -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    current["verdicts"]["seams"]["windows-native"] = "INCOMPLETE"

    assert "RELEASE_LAUNDERING" in codes(validate_transition(previous, current))


def test_target_ready_cannot_hide_an_open_blocking_finding() -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    current["findings"] = [finding()]

    assert "RELEASE_FINDING" in codes(validate_transition(previous, current))


def test_previous_snapshot_semantics_are_not_trusted_implicitly() -> None:
    previous = snapshot()
    previous["findings"] = [finding()]
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["verdicts"]["core"] = "BLOCKED"
    current["verdicts"]["release"]["windows-native"] = "BLOCKED"

    errors = validate_transition(previous, current)
    assert any(
        error["code"] == "RELEASE_FINDING"
        and error["path"] == "previous.verdicts.release.windows-native"
        for error in errors
    )


def test_target_ready_requires_frozen_acceptance_evidence() -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    current["commitments"]["ACCEPT-1"]["evidenceIds"] = []

    assert "RELEASE_REQUIREMENT" in codes(validate_transition(previous, current))


def test_overall_ready_cannot_hide_an_incomplete_hard_target() -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    for value in (previous, current):
        value["commitmentFloor"]["requiredSeams"] = ["linux", "windows-native"]
        value["commitmentFloor"]["digest"] = floor_digest(value)
        value["verdicts"]["seams"]["linux"] = "PASS"
        value["verdicts"]["release"]["linux"] = "READY"
    current["verdicts"]["seams"]["windows-native"] = "INCOMPLETE"
    current["verdicts"]["release"]["windows-native"] = "INCOMPLETE"
    current["verdicts"]["releaseOverall"] = "READY"

    assert "RELEASE_OVERALL_LAUNDERING" in codes(validate_transition(previous, current))


def test_core_seam_and_target_ready_claims_require_bound_identities() -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    current["candidate"]["digest"] = None

    result_codes = codes(validate_transition(previous, current))
    assert {"PASS_IDENTITY", "RELEASE_IDENTITY"} <= result_codes


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["specification"].update(digest=None),
        lambda value: value["candidate"].update(digest=None),
        lambda value: value["candidate"].update(generation=0),
    ],
)
def test_overall_ready_requires_bound_specification_and_candidate(
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    current["verdicts"]["releaseOverall"] = "READY"
    mutate(current)

    assert "RELEASE_OVERALL_IDENTITY" in codes(validate_transition(previous, current))


def test_identity_drift_cannot_reuse_positive_claims_or_evidence() -> None:
    previous = snapshot()
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["candidate"] = {"generation": 2, "digest": DIGEST_C}

    result_codes = codes(validate_transition(previous, current))
    assert "IDENTITY_RESET_REQUIRED" in result_codes
    assert "POSITIVE_DECISION_RECEIPT" in result_codes


def test_identity_change_can_make_a_fail_closed_reset_transition() -> None:
    previous = snapshot()
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["candidate"] = {"generation": 2, "digest": DIGEST_C}
    current["verdicts"] = {
        "core": "NOT_RUN",
        "seams": {"windows-native": "NOT_RUN"},
        "release": {"windows-native": "NOT_RUN"},
        "releaseOverall": "NOT_RUN",
    }
    for cell in current["commitments"].values():
        cell.update(status="NOT_RUN", evidenceIds=[])
    current["loopBudgets"]["delivery"]["status"] = "ACTIVE"

    assert validate_transition(previous, current) == []


@pytest.mark.parametrize(
    ("identity", "expected_code"),
    [
        ({"generation": 1, "digest": DIGEST_C}, "IDENTITY_DIGEST_BINDING"),
        ({"generation": 2, "digest": DIGEST_B}, "IDENTITY_GENERATION_BINDING"),
    ],
)
def test_candidate_generation_and_digest_must_move_together(
    identity: dict[str, Any], expected_code: str
) -> None:
    previous = snapshot()
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["candidate"] = identity

    assert expected_code in codes(validate_transition(previous, current))


def test_positive_verdict_promotion_needs_a_new_owner_receipt() -> None:
    previous = snapshot()
    previous["verdicts"] = {
        "core": "NOT_RUN",
        "seams": {"windows-native": "NOT_RUN"},
        "release": {"windows-native": "NOT_RUN"},
        "releaseOverall": "NOT_RUN",
    }
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["verdicts"]["core"] = "PASS"

    assert "POSITIVE_DECISION_PROMOTION" in codes(validate_transition(previous, current))


def test_positive_verdict_promotion_accepts_a_new_bound_owner_receipt() -> None:
    previous = snapshot()
    previous["verdicts"] = {
        "core": "NOT_RUN",
        "seams": {"windows-native": "NOT_RUN"},
        "release": {"windows-native": "NOT_RUN"},
        "releaseOverall": "NOT_RUN",
    }
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["verdicts"]["core"] = "PASS"
    receipt = decision_receipt(current, cell="core", decision="PASS", evidence="evidence-core")
    receipt["id"] = "receipt-core-pass-2"
    current["decisionReceipts"].append(receipt)

    assert validate_transition(previous, current) == []


def test_decision_receipt_history_is_append_only() -> None:
    previous = snapshot()
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["decisionReceipts"][0]["reason"] = "rewritten"

    assert "DECISION_RECEIPT_PREFIX" in codes(validate_transition(previous, current))


def test_done_snapshot_is_terminal() -> None:
    previous = snapshot(done=True)
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["completion"] = {"status": "IN_PROGRESS", "achievedStage": None}

    assert "TERMINAL_TRANSITION" in codes(validate_transition(previous, current))


def test_done_snapshot_rejects_a_generation_only_followup() -> None:
    previous = snapshot(done=True)
    current = copy.deepcopy(previous)
    current["generation"] += 1

    assert "TERMINAL_TRANSITION" in codes(validate_transition(previous, current))


def test_pm_cannot_reclassify_an_owner_bound_finding() -> None:
    previous = snapshot()
    previous["findings"] = [finding()]
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current_finding = current["findings"][0]
    current_finding["class"] = "HARNESS_OR_ENV_BLOCKER"
    current_finding["ownerDisposition"] = "RECLASSIFIED"
    current_finding["reclassifications"].append(
        {
            "oldClass": "CORE_DEFECT",
            "newClass": "HARNESS_OR_ENV_BLOCKER",
            "authority": "pm-agent",
            "oldDispositionOwner": "completeness-owner",
            "newDispositionOwner": "completeness-owner",
            "reason": "Treat this as an environment issue.",
            "affectedCells": current_finding["affectedCells"],
            "firstUnsafeOperation": current_finding["firstUnsafeOperation"],
            "evidenceIds": current_finding["evidenceIds"],
        }
    )

    assert "FINDINGS" in codes(validate_transition(previous, current))


def test_classification_owner_can_reclassify_with_bound_evidence() -> None:
    previous = snapshot()
    previous["findings"] = [finding()]
    previous["verdicts"]["core"] = "BLOCKED"
    previous["verdicts"]["release"]["windows-native"] = "BLOCKED"
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current_finding = current["findings"][0]
    current_finding["class"] = "HARNESS_OR_ENV_BLOCKER"
    current_finding["ownerDisposition"] = "RECLASSIFIED"
    current_finding["evidenceIds"].append("evidence-host-start")
    current_finding["reclassifications"].append(
        {
            "oldClass": "CORE_DEFECT",
            "newClass": "HARNESS_OR_ENV_BLOCKER",
            "authority": "qc-owner",
            "oldDispositionOwner": "completeness-owner",
            "newDispositionOwner": "completeness-owner",
            "reason": "New evidence shows failure before product execution.",
            "affectedCells": current_finding["affectedCells"],
            "firstUnsafeOperation": current_finding["firstUnsafeOperation"],
            "evidenceIds": current_finding["evidenceIds"],
        }
    )

    assert validate_transition(previous, current) == []


def test_closed_finding_is_semantically_immutable() -> None:
    previous = snapshot()
    previous["findings"] = [finding()]
    previous_item = previous["findings"][0]
    previous_item.update(
        status="CLOSED",
        ownerDisposition="CONFIRMED",
        closure={
            "authority": "completeness-owner",
            "reason": "The finding was resolved under the original classification.",
            "evidenceIds": ["evidence-repair"],
        },
    )
    current = copy.deepcopy(previous)
    current["generation"] += 1
    reclassify_finding(current)
    current["findings"][0]["ownerDisposition"] = "CONFIRMED"

    assert "FINDING_TERMINAL_IMMUTABLE" in codes(validate_transition(previous, current))


def test_reclassification_and_closure_require_separate_transitions() -> None:
    previous = snapshot()
    previous["findings"] = [finding()]
    current = copy.deepcopy(previous)
    current["generation"] += 1
    reclassify_finding(current)
    current["findings"][0].update(
        status="CLOSED",
        ownerDisposition="CONFIRMED",
        closure={
            "authority": "completeness-owner",
            "reason": "Attempt to reclassify and close atomically.",
            "evidenceIds": ["evidence-repair"],
        },
    )

    assert "FINDING_TEMPORAL_BOUNDARY" in codes(validate_transition(previous, current))


def test_reclassification_then_owner_closure_is_valid_across_two_transitions() -> None:
    initial = snapshot()
    initial["findings"] = [finding()]
    initial["verdicts"]["core"] = "BLOCKED"
    initial["verdicts"]["release"]["windows-native"] = "BLOCKED"
    reclassified = copy.deepcopy(initial)
    reclassified["generation"] += 1
    reclassify_finding(reclassified)
    assert validate_transition(initial, reclassified) == []

    closed = copy.deepcopy(reclassified)
    closed["generation"] += 1
    closed["findings"][0].update(
        status="CLOSED",
        ownerDisposition="CONFIRMED",
        closure={
            "authority": "completeness-owner",
            "reason": "The disposition owner closed the reclassified finding later.",
            "evidenceIds": ["evidence-repair"],
        },
    )

    assert validate_transition(reclassified, closed) == []


def test_owner_reclassification_requires_new_class_specific_evidence() -> None:
    previous = snapshot()
    previous["findings"] = [finding()]
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current_finding = current["findings"][0]
    current_finding["class"] = "HARNESS_OR_ENV_BLOCKER"
    current_finding["ownerDisposition"] = "RECLASSIFIED"
    current_finding["reclassifications"].append(
        {
            "oldClass": "CORE_DEFECT",
            "newClass": "HARNESS_OR_ENV_BLOCKER",
            "authority": "qc-owner",
            "oldDispositionOwner": "completeness-owner",
            "newDispositionOwner": "completeness-owner",
            "reason": "Reclassify without adding class-specific evidence.",
            "affectedCells": current_finding["affectedCells"],
            "firstUnsafeOperation": current_finding["firstUnsafeOperation"],
            "evidenceIds": current_finding["evidenceIds"],
        }
    )

    assert "RECLASSIFICATION_NEW_EVIDENCE" in codes(validate_transition(previous, current))


def test_owner_reclassification_cannot_remove_prior_evidence() -> None:
    previous = snapshot()
    previous["findings"] = [finding()]
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current_finding = current["findings"][0]
    current_finding["class"] = "HARNESS_OR_ENV_BLOCKER"
    current_finding["ownerDisposition"] = "RECLASSIFIED"
    current_finding["evidenceIds"] = ["evidence-host-start"]
    current_finding["reclassifications"].append(
        {
            "oldClass": "CORE_DEFECT",
            "newClass": "HARNESS_OR_ENV_BLOCKER",
            "authority": "qc-owner",
            "oldDispositionOwner": "completeness-owner",
            "newDispositionOwner": "completeness-owner",
            "reason": "Attempt to replace rather than append evidence.",
            "affectedCells": current_finding["affectedCells"],
            "firstUnsafeOperation": current_finding["firstUnsafeOperation"],
            "evidenceIds": current_finding["evidenceIds"],
        }
    )

    assert "FINDING_EVIDENCE_REMOVED" in codes(validate_transition(previous, current))


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("affectedCells", ["seam/windows-native"]),
        ("firstUnsafeOperation", "rewritten unsafe operation"),
    ],
)
def test_owner_reclassification_cannot_rewrite_original_observation(
    field: str, replacement: object
) -> None:
    previous = snapshot()
    previous["findings"] = [finding()]
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current_finding = current["findings"][0]
    current_finding["class"] = "HARNESS_OR_ENV_BLOCKER"
    current_finding["ownerDisposition"] = "RECLASSIFIED"
    current_finding["evidenceIds"].append("evidence-host-start")
    current_finding[field] = replacement
    current_finding["reclassifications"].append(
        {
            "oldClass": "CORE_DEFECT",
            "newClass": "HARNESS_OR_ENV_BLOCKER",
            "authority": "qc-owner",
            "oldDispositionOwner": "completeness-owner",
            "newDispositionOwner": "completeness-owner",
            "reason": "Attempt to rewrite the original observation.",
            "affectedCells": current_finding["affectedCells"],
            "firstUnsafeOperation": current_finding["firstUnsafeOperation"],
            "evidenceIds": current_finding["evidenceIds"],
        }
    )

    assert "FINDING_PACKET_REWRITE" in codes(validate_transition(previous, current))


def test_existing_finding_cannot_disappear_from_history() -> None:
    previous = snapshot()
    previous["findings"] = [finding(finding_class="SPEC_GAP")]
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["findings"] = []

    assert "FINDING_REMOVED" in codes(validate_transition(previous, current))


def test_pm_cannot_rewrite_an_owner_bound_finding_packet_without_reclassification() -> None:
    previous = snapshot()
    previous["findings"] = [finding()]
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["findings"][0]["evidenceIds"] = ["pm-assertion"]

    assert "FINDING_PACKET_REWRITE" in codes(validate_transition(previous, current))


def test_disposition_owner_can_close_a_finding_with_bound_evidence() -> None:
    previous = snapshot()
    previous["findings"] = [finding()]
    previous["verdicts"]["core"] = "BLOCKED"
    previous["verdicts"]["release"]["windows-native"] = "BLOCKED"
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current_finding = current["findings"][0]
    current_finding.update(
        status="CLOSED",
        ownerDisposition="CONFIRMED",
        closure={
            "authority": "completeness-owner",
            "reason": "The repaired candidate now satisfies the frozen acceptance.",
            "evidenceIds": ["evidence-repair"],
        },
    )

    assert validate_transition(previous, current) == []


def test_pm_cannot_close_an_owner_bound_finding() -> None:
    previous = snapshot()
    previous["findings"] = [finding()]
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current_finding = current["findings"][0]
    current_finding.update(
        status="CLOSED",
        ownerDisposition="CONFIRMED",
        closure={
            "authority": "pm-agent",
            "reason": "Close it for schedule reasons.",
            "evidenceIds": ["pm-assertion"],
        },
    )

    assert "FINDINGS" in codes(validate_transition(previous, current))


def test_exhausted_loop_cannot_remain_active() -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    current["loopBudgets"]["delivery"].update(
        usedPasses=3,
        status="ACTIVE",
        lastFindingSignature="delivery-3",
        signatureHistory=["delivery-1", "delivery-2", "delivery-3"],
    )

    assert "LOOP_BUDGET_EXHAUSTED" in codes(validate_transition(previous, current))


def test_repeated_finding_signature_stops_instead_of_consuming_another_pass() -> None:
    previous = snapshot()
    previous["loopBudgets"]["delivery"].update(
        usedPasses=1,
        lastFindingSignature="CORE_DEFECT|ACCEPT-1|operation|core/REQ-1",
        signatureHistory=["CORE_DEFECT|ACCEPT-1|operation|core/REQ-1"],
    )
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["loopBudgets"]["delivery"].update(
        usedPasses=2,
        lastFindingSignature="CORE_DEFECT|ACCEPT-1|operation|core/REQ-1",
        signatureHistory=[
            "CORE_DEFECT|ACCEPT-1|operation|core/REQ-1",
            "CORE_DEFECT|ACCEPT-1|operation|core/REQ-1",
        ],
    )

    assert "LOOP_SIGNATURE_REPEAT" in codes(validate_transition(previous, current))


def test_loop_signature_history_rejects_a_b_a_oscillation_even_when_closed() -> None:
    previous = snapshot()
    previous["loopBudgets"]["delivery"].update(
        usedPasses=2,
        status="ACTIVE",
        lastFindingSignature="B",
        signatureHistory=["A", "B"],
    )
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["loopBudgets"]["delivery"].update(
        usedPasses=3,
        status="CLOSED",
        lastFindingSignature="A",
        signatureHistory=["A", "B", "A"],
    )

    assert "LOOP_SIGNATURE_REPEAT" in codes(validate_transition(previous, current))


def test_closed_loop_cannot_reopen_without_a_changed_floor_or_identity() -> None:
    previous = snapshot()
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["loopBudgets"]["specification"]["status"] = "ACTIVE"

    assert "LOOP_REOPEN" in codes(validate_transition(previous, current))


def test_candidate_change_requires_delivery_loop_reactivation() -> None:
    previous = snapshot()
    previous["loopBudgets"]["delivery"].update(
        status="CLOSED",
        usedPasses=1,
        lastFindingSignature="delivery-ready-1",
        signatureHistory=["delivery-ready-1"],
    )
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["candidate"] = {"generation": 2, "digest": DIGEST_C}
    current["verdicts"] = {
        "core": "NOT_RUN",
        "seams": {"windows-native": "NOT_RUN"},
        "release": {"windows-native": "NOT_RUN"},
        "releaseOverall": "NOT_RUN",
    }
    for cell in current["commitments"].values():
        cell.update(status="NOT_RUN", evidenceIds=[])

    required_paths = {
        error["path"]
        for error in validate_transition(previous, current)
        if error["code"] == "LOOP_REOPEN_REQUIRED"
    }
    assert required_paths == {"current.loopBudgets.delivery.status"}


def test_specification_change_requires_both_loops_to_reactivate() -> None:
    previous = snapshot()
    previous["loopBudgets"]["delivery"].update(
        status="CLOSED",
        usedPasses=1,
        lastFindingSignature="delivery-ready-1",
        signatureHistory=["delivery-ready-1"],
    )
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["specification"] = {"generation": 2, "digest": DIGEST_C}
    current["verdicts"] = {
        "core": "NOT_RUN",
        "seams": {"windows-native": "NOT_RUN"},
        "release": {"windows-native": "NOT_RUN"},
        "releaseOverall": "NOT_RUN",
    }
    for cell in current["commitments"].values():
        cell.update(status="NOT_RUN", evidenceIds=[])

    required_paths = {
        error["path"]
        for error in validate_transition(previous, current)
        if error["code"] == "LOOP_REOPEN_REQUIRED"
    }
    assert required_paths == {
        "current.loopBudgets.specification.status",
        "current.loopBudgets.delivery.status",
    }
    current["loopBudgets"]["specification"]["status"] = "ACTIVE"
    current["loopBudgets"]["delivery"]["status"] = "ACTIVE"
    assert validate_transition(previous, current) == []


def test_floor_change_requires_both_loops_to_reactivate() -> None:
    previous = snapshot()
    previous["loopBudgets"]["delivery"].update(
        status="CLOSED",
        usedPasses=1,
        lastFindingSignature="delivery-ready-1",
        signatureHistory=["delivery-ready-1"],
    )
    current = authorized_floor_change(previous)
    current["loopBudgets"]["specification"]["status"] = "CLOSED"
    current["loopBudgets"]["delivery"]["status"] = "CLOSED"

    required_paths = {
        error["path"]
        for error in validate_transition(previous, current)
        if error["code"] == "LOOP_REOPEN_REQUIRED"
    }
    assert required_paths == {
        "current.loopBudgets.specification.status",
        "current.loopBudgets.delivery.status",
    }


def test_blocked_loop_cannot_be_relabelled_closed_without_reactivation() -> None:
    previous = snapshot()
    previous["loopBudgets"]["delivery"]["status"] = "BLOCKED"
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["loopBudgets"]["delivery"]["status"] = "CLOSED"

    assert "LOOP_TERMINAL_TRANSITION" in codes(
        validate_transition(previous, current)
    )


def test_active_loop_cannot_close_without_recording_a_new_pass() -> None:
    previous = snapshot()
    previous["loopBudgets"]["delivery"].update(
        usedPasses=0,
        status="ACTIVE",
        lastFindingSignature=None,
        signatureHistory=[],
    )
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["loopBudgets"]["delivery"]["status"] = "CLOSED"

    assert "LOOP_CLOSE_PASS" in codes(validate_transition(previous, current))


def test_active_loop_can_close_on_one_new_discriminating_pass() -> None:
    previous = snapshot()
    previous["loopBudgets"]["delivery"].update(
        usedPasses=0,
        status="ACTIVE",
        lastFindingSignature=None,
        signatureHistory=[],
    )
    current = copy.deepcopy(previous)
    current["generation"] += 1
    append_delivery_pass(previous, current)

    assert validate_transition(previous, current) == []


def test_new_finding_cannot_enter_closed_or_consume_a_delivery_pass() -> None:
    previous = snapshot()
    previous["loopBudgets"]["delivery"].update(
        usedPasses=0,
        status="ACTIVE",
        lastFindingSignature=None,
        signatureHistory=[],
    )
    current = copy.deepcopy(previous)
    current["generation"] += 1
    closed = finding()
    closed.update(status="CLOSED", ownerDisposition="REJECTED_FALSE")
    closed["closure"] = {
        "authority": "completeness-owner",
        "reason": "fabricated closure",
        "evidenceIds": ["evidence-closure-only"],
    }
    current["findings"].append(closed)
    signature = pass_signature(previous, current, "delivery")
    current["loopBudgets"]["delivery"].update(
        usedPasses=1,
        status="CLOSED",
        lastFindingSignature=signature,
        signatureHistory=[signature],
    )

    result_codes = codes(validate_transition(previous, current))
    assert "NEW_FINDING_INITIAL_STATE" in result_codes
    assert "LOOP_PASS_DELTA" in result_codes


def test_caller_alias_cannot_substitute_for_a_semantic_pass_delta() -> None:
    previous = snapshot()
    previous["loopBudgets"]["delivery"].update(
        usedPasses=0,
        status="ACTIVE",
        lastFindingSignature=None,
        signatureHistory=[],
    )
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["loopBudgets"]["delivery"].update(
        usedPasses=1,
        status="CLOSED",
        lastFindingSignature="alias-B",
        signatureHistory=["alias-B"],
    )

    error_codes = codes(validate_transition(previous, current))
    assert "LOOP_PASS_DELTA" in error_codes
    assert "LOOP_SIGNATURE_BINDING" in error_codes


def test_closed_loop_cannot_consume_another_pass() -> None:
    previous = snapshot()
    previous["loopBudgets"]["delivery"].update(
        usedPasses=1,
        status="CLOSED",
        lastFindingSignature=DIGEST_A,
        signatureHistory=[DIGEST_A],
    )
    current = copy.deepcopy(previous)
    current["generation"] += 1
    append_delivery_pass(previous, current)

    assert "LOOP_PASS_STATE" in codes(validate_transition(previous, current))


def test_unknown_identity_metadata_cannot_reopen_a_closed_loop() -> None:
    previous = snapshot()
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["specification"]["note"] = "not part of the bound identity"
    current["loopBudgets"]["specification"]["status"] = "ACTIVE"

    assert "LOOP_REOPEN" in codes(validate_transition(previous, current))


def test_pass_signature_ignores_receipt_alias_and_reason_text() -> None:
    previous = snapshot()
    first = copy.deepcopy(previous)
    first["generation"] += 1
    first_receipt = decision_receipt(
        first, cell="core", decision="PASS", evidence="evidence-semantic-pass"
    )
    first_receipt.update(id="receipt-alias-a", reason="wording A")
    first["decisionReceipts"].append(first_receipt)

    second = copy.deepcopy(previous)
    second["generation"] += 1
    second_receipt = decision_receipt(
        second, cell="core", decision="PASS", evidence="evidence-semantic-pass"
    )
    second_receipt.update(id="receipt-alias-b", reason="wording B")
    second["decisionReceipts"].append(second_receipt)

    assert pass_signature(previous, first, "delivery") == pass_signature(
        previous, second, "delivery"
    )


def test_receipt_alias_only_cannot_consume_a_delivery_pass() -> None:
    previous = snapshot()
    current = copy.deepcopy(previous)
    current["generation"] += 1
    alias = copy.deepcopy(previous["decisionReceipts"][0])
    alias.update(id="receipt-core-pass-alias", reason="same decision, different prose")
    current["decisionReceipts"].append(alias)
    signature = pass_signature(previous, current, "delivery")
    current["loopBudgets"]["delivery"].update(
        usedPasses=1,
        status="CLOSED",
        lastFindingSignature=signature,
        signatureHistory=[signature],
    )

    assert "LOOP_PASS_DELTA" in codes(validate_transition(previous, current))


def test_phantom_receipt_is_rejected_and_cannot_consume_a_delivery_pass() -> None:
    previous = snapshot()
    current = copy.deepcopy(previous)
    current["generation"] += 1
    phantom = decision_receipt(
        current,
        cell="release:phantom-target",
        decision="READY",
        evidence="evidence-phantom",
    )
    phantom["id"] = "receipt-release-phantom-target-ready-1"
    current["decisionReceipts"].append(phantom)
    signature = pass_signature(previous, current, "delivery")
    current["loopBudgets"]["delivery"].update(
        usedPasses=1,
        status="CLOSED",
        lastFindingSignature=signature,
        signatureHistory=[signature],
    )

    error_codes = codes(validate_transition(previous, current))
    assert "DECISION_RECEIPT_CURRENT_CELL" in error_codes
    assert "LOOP_PASS_DELTA" in error_codes


def test_finding_unknown_metadata_only_cannot_consume_a_delivery_pass() -> None:
    previous = snapshot()
    previous_finding = finding()
    previous_finding["blocking"] = False
    previous["findings"] = [previous_finding]
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["findings"][0]["unknownMetadata"] = "not semantic progress"
    signature = pass_signature(previous, current, "delivery")
    current["loopBudgets"]["delivery"].update(
        usedPasses=1,
        status="CLOSED",
        lastFindingSignature=signature,
        signatureHistory=[signature],
    )

    assert "LOOP_PASS_DELTA" in codes(validate_transition(previous, current))


def test_commitment_unknown_metadata_does_not_salt_pass_signature() -> None:
    previous = snapshot()
    first = copy.deepcopy(previous)
    first["generation"] += 1
    first["commitments"]["REQ-1"]["evidenceIds"].append("evidence-new")

    second = copy.deepcopy(first)
    second["commitments"]["REQ-1"]["unknownMetadata"] = "not semantic progress"

    assert pass_signature(previous, first, "delivery") == pass_signature(
        previous, second, "delivery"
    )


def test_activation_loop_budget_cannot_be_silently_extended() -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    current["loopBudgets"]["delivery"]["maxPasses"] = 4

    assert "LOOP_BUDGET_CHANGE" in codes(validate_transition(previous, current))


def test_loop_pass_counter_cannot_skip_generations() -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    current["loopBudgets"]["delivery"].update(
        usedPasses=2,
        lastFindingSignature="delivery-2",
        signatureHistory=["delivery-1", "delivery-2"],
    )

    assert "LOOP_PASS_STEP" in codes(validate_transition(previous, current))


@pytest.mark.parametrize(
    ("path", "value", "expected_code"),
    [
        (("generation",), True, "STATE_GENERATION"),
        (("commitmentFloor", "generation"), True, "FLOOR_GENERATION"),
        (("candidate", "generation"), True, "IDENTITY_GENERATION"),
        (("loopBudgets", "delivery", "maxPasses"), True, "LOOP_BUDGET"),
    ],
)
def test_boolean_values_are_not_accepted_as_integer_generations_or_budgets(
    path: tuple[str, ...], value: object, expected_code: str
) -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    target: dict[str, Any] = current
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    if path[:1] == ("commitmentFloor",):
        current["commitmentFloor"]["digest"] = floor_digest(current)

    assert expected_code in codes(validate_transition(previous, current))


@pytest.mark.parametrize("invalid_version", [True, 1.0])
def test_schema_version_requires_exact_integer_one(invalid_version: object) -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    previous["schemaVersion"] = invalid_version
    current["schemaVersion"] = invalid_version

    assert "SCHEMA_VERSION" in codes(validate_transition(previous, current))


@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        (lambda value: value["verdicts"].update(core=[]), "CORE_VERDICT"),
        (
            lambda value: value["verdicts"]["seams"].update(
                {"windows-native": []}
            ),
            "VERDICT_CELLS",
        ),
        (
            lambda value: value["loopBudgets"]["delivery"].update(status=[]),
            "LOOP_BUDGET",
        ),
        (
            lambda value: value["loopBudgets"]["delivery"].update(
                signatureHistory=[{}]
            ),
            "LOOP_BUDGET",
        ),
        (lambda value: value.update(findings=[{**finding(), "class": []}]), "FINDINGS"),
        (lambda value: value.update(findings=[{**finding(), "status": {}}]), "FINDINGS"),
        (
            lambda value: value.update(
                findings=[{**finding(), "ownerDisposition": []}]
            ),
            "FINDINGS",
        ),
        (
            lambda value: value["commitments"]["REQ-1"].update(status=[]),
            "COMMITMENT_CELL",
        ),
        (lambda value: value["completion"].update(status=[]), "COMPLETION_STATUS"),
        (
            lambda value: value["decisionReceipts"][0].update(cell=[]),
            "DECISION_RECEIPTS",
        ),
    ],
)
def test_unhashable_json_enum_values_return_errors_instead_of_crashing(
    mutate: Callable[[dict[str, Any]], None], expected_code: str
) -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    mutate(current)

    assert expected_code in codes(validate_transition(previous, current))


def test_unhashable_reclassification_class_returns_an_error() -> None:
    previous = snapshot()
    previous["findings"] = [finding()]
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current_finding = current["findings"][0]
    current_finding["class"] = "HARNESS_OR_ENV_BLOCKER"
    current_finding["ownerDisposition"] = "RECLASSIFIED"
    current_finding["evidenceIds"].append("evidence-host-start")
    current_finding["reclassifications"].append(
        {
            "oldClass": [],
            "newClass": "HARNESS_OR_ENV_BLOCKER",
            "authority": "qc-owner",
            "oldDispositionOwner": "completeness-owner",
            "newDispositionOwner": "completeness-owner",
            "reason": "Malformed old class.",
            "affectedCells": current_finding["affectedCells"],
            "firstUnsafeOperation": current_finding["firstUnsafeOperation"],
            "evidenceIds": current_finding["evidenceIds"],
        }
    )

    assert "FINDINGS" in codes(validate_transition(previous, current))


def test_invalid_floor_lists_are_rejected_without_crashing_digest_validation() -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    current["commitmentFloor"]["requirementIds"] = ["REQ-1", 2]
    current["commitmentFloor"]["digest"] = floor_digest(current)

    assert "FLOOR_LIST" in codes(validate_transition(previous, current))


def test_deep_legal_json_returns_a_structured_depth_error() -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    nested: object = "REQ-1"
    for _ in range(150):
        nested = [nested]
    current["commitmentFloor"]["requirementIds"] = nested

    assert "JSON_DEPTH" in codes(validate_transition(previous, current))


def test_floor_ids_cannot_alias_each_other_with_outer_whitespace() -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    current["commitmentFloor"]["requirementIds"] = ["REQ-1", " REQ-1 "]
    current["commitmentFloor"]["digest"] = floor_digest(current)

    assert "FLOOR_LIST" in codes(validate_transition(previous, current))


def test_requirement_and_acceptance_ids_must_be_disjoint() -> None:
    value = snapshot()
    value["commitmentFloor"]["acceptanceIds"] = ["REQ-1"]
    value["commitmentFloor"]["digest"] = floor_digest(value)
    value["commitments"] = {
        "REQ-1": {"status": "SUPPORTED", "evidenceIds": ["evidence-core"]}
    }

    assert "FLOOR_ID_NAMESPACE" in codes(validate_snapshot(value, label="snapshot"))


def test_phantom_commitment_is_rejected_and_cannot_change_pass_signature() -> None:
    previous = snapshot()
    baseline = copy.deepcopy(previous)
    baseline["generation"] += 1
    current = copy.deepcopy(baseline)
    current["commitments"]["PHANTOM-CLAIM"] = {
        "status": "SUPPORTED",
        "evidenceIds": ["evidence-phantom-claim"],
    }

    assert "COMMITMENT_COVERAGE" in codes(validate_transition(previous, current))
    assert pass_signature(previous, current, "delivery") == pass_signature(
        previous, baseline, "delivery"
    )


def test_phantom_verdict_cells_are_rejected_and_cannot_change_pass_signature() -> None:
    previous = snapshot()
    baseline = copy.deepcopy(previous)
    baseline["generation"] += 1
    current = copy.deepcopy(baseline)
    current["verdicts"]["seams"]["phantom"] = "PASS"
    current["verdicts"]["release"]["phantom"] = "READY"
    current["decisionReceipts"].extend(
        [
            decision_receipt(
                current,
                cell="seam:phantom",
                decision="PASS",
                evidence="evidence-phantom-seam",
            ),
            decision_receipt(
                current,
                cell="release:phantom",
                decision="READY",
                evidence="evidence-phantom-release",
            ),
        ]
    )

    assert "VERDICT_COVERAGE" in codes(validate_transition(previous, current))
    assert pass_signature(previous, current, "delivery") == pass_signature(
        previous, baseline, "delivery"
    )


def test_phantom_finding_cell_is_rejected_and_cannot_change_pass_signature() -> None:
    previous = snapshot()
    baseline = copy.deepcopy(previous)
    baseline["generation"] += 1
    current = copy.deepcopy(baseline)
    item = finding()
    item.update(id="F-PHANTOM", blocking=False, affectedCells=["phantom-cell"])
    current["findings"].append(item)

    assert "FINDING_CELL_BINDING" in codes(validate_transition(previous, current))
    assert pass_signature(previous, current, "delivery") == pass_signature(
        previous, baseline, "delivery"
    )


@pytest.mark.parametrize(
    ("kind", "historical_cell"),
    [("seam", "seam/windows-native"), ("requirement", "core/REQ-1")],
)
def test_floor_replacement_preserves_historical_finding_but_rejects_new_old_cell(
    kind: str, historical_cell: str
) -> None:
    previous = snapshot()
    historical = finding()
    historical.update(
        status="CLOSED",
        ownerDisposition="CONFIRMED",
        affectedCells=[historical_cell],
        closure={
            "authority": historical["dispositionOwner"],
            "evidenceIds": ["evidence-repair"],
            "reason": "The historical observation was resolved.",
        },
    )
    previous["findings"] = [historical]
    current = replace_floor_namespace(previous, kind=kind)

    assert validate_transition(previous, current) == []
    assert "FINDING_CELL_BINDING" in codes(validate_snapshot(current, label="import"))

    invalid = copy.deepcopy(current)
    new_item = finding()
    new_item.update(
        id="F-NEW-OLD-CELL",
        blocking=False,
        affectedCells=[historical_cell],
        evidenceIds=["evidence-new-observation"],
    )
    invalid["findings"].append(new_item)

    assert "FINDING_CELL_BINDING" in codes(validate_transition(previous, invalid))
    assert pass_signature(previous, invalid, "delivery") == pass_signature(
        previous, current, "delivery"
    )


def test_standalone_import_cannot_expand_history_with_unvalidated_amendment() -> None:
    forged = snapshot()
    item = finding()
    item.update(
        status="CLOSED",
        ownerDisposition="CONFIRMED",
        affectedCells=["seam/phantom-seam"],
        closure={
            "authority": item["dispositionOwner"],
            "evidenceIds": ["evidence-repair"],
            "reason": "A forged imported history must not establish trust.",
        },
    )
    forged["findings"] = [item]
    forged["amendments"] = [{"affectedSeams": ["phantom-seam", 7]}]

    error_codes = codes(validate_snapshot(forged, label="import"))

    assert "FINDING_CELL_BINDING" in error_codes
    assert "AMENDMENTS_TYPE" in error_codes


def test_commitment_delta_signature_ignores_json_map_key_order() -> None:
    previous = snapshot()
    first = copy.deepcopy(previous)
    first["generation"] += 1
    first["commitments"]["REQ-1"]["evidenceIds"].append("evidence-new-req")
    first["commitments"]["ACCEPT-1"]["evidenceIds"].append("evidence-new-accept")
    reordered = copy.deepcopy(first)
    reordered["commitments"] = {
        "ACCEPT-1": reordered["commitments"]["ACCEPT-1"],
        "REQ-1": reordered["commitments"]["REQ-1"],
    }

    assert pass_signature(previous, first, "delivery") == pass_signature(
        previous, reordered, "delivery"
    )


def test_task_identity_cannot_have_outer_whitespace() -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    current["taskId"] = " task-1 "

    assert "TASK_ID" in codes(validate_transition(previous, current))


def test_stale_floor_digest_is_rejected_before_transition_logic() -> None:
    previous = snapshot()
    current = snapshot(generation=2)
    current["commitmentFloor"]["digest"] = DIGEST_A

    assert "FLOOR_DIGEST" in codes(validate_transition(previous, current))


def test_cli_returns_machine_readable_failure(tmp_path: Path) -> None:
    previous = snapshot()
    current = copy.deepcopy(previous)
    current["generation"] += 1
    current["commitmentFloor"]["generation"] += 1
    current["commitmentFloor"]["targetTerminalStage"] = "implemented"
    current["commitmentFloor"]["digest"] = floor_digest(current)
    previous_path = tmp_path / "previous.json"
    current_path = tmp_path / "current.json"
    previous_path.write_text(json.dumps(previous), encoding="utf-8")
    current_path.write_text(json.dumps(current), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "validate", str(previous_path), str(current_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert "FLOOR_AMENDMENT_REQUIRED" in codes(payload["errors"])
    assert payload["receiptSchemaVersion"] == 1
    assert payload["previousSnapshotDigest"] == "sha256:" + hashlib.sha256(
        previous_path.read_bytes()
    ).hexdigest()
    assert payload["currentSnapshotDigest"] == "sha256:" + hashlib.sha256(
        current_path.read_bytes()
    ).hexdigest()


def test_cli_returns_structured_validation_error_for_unhashable_enum_json(
    tmp_path: Path,
) -> None:
    previous_path = tmp_path / "previous.json"
    current_path = tmp_path / "current.json"
    previous_path.write_text(json.dumps(snapshot()), encoding="utf-8")
    current = snapshot(generation=2)
    current["verdicts"]["core"] = []
    current_path.write_text(json.dumps(current), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "validate", str(previous_path), str(current_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert "CORE_VERDICT" in codes(payload["errors"])


def test_cli_success_receipt_binds_the_exact_input_bytes(tmp_path: Path) -> None:
    previous_path = tmp_path / "previous.json"
    current_path = tmp_path / "current.json"
    previous_path.write_text(json.dumps(snapshot(), indent=2), encoding="utf-8")
    current_path.write_text(json.dumps(snapshot(generation=2), indent=4), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "validate", str(previous_path), str(current_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["errors"] == []
    assert payload["previousSnapshotDigest"] == "sha256:" + hashlib.sha256(
        previous_path.read_bytes()
    ).hexdigest()
    assert payload["currentSnapshotDigest"] == "sha256:" + hashlib.sha256(
        current_path.read_bytes()
    ).hexdigest()


@pytest.mark.parametrize(
    "malformed_text",
    ["{not-json", '{"taskId":"first","taskId":"second"}', "NaN"],
)
def test_cli_returns_machine_readable_input_error_for_malformed_json(
    tmp_path: Path, malformed_text: str
) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text(malformed_text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "digest", str(malformed)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert codes(payload["errors"]) == {"INPUT_ERROR"}


@pytest.mark.parametrize(
    "malformed_text",
    ['{"taskId":"first","taskId":"second"}', "NaN", None],
    ids=["duplicate-key", "nan", "deep-json"],
)
def test_validate_parse_failure_still_returns_exact_byte_receipt(
    tmp_path: Path, malformed_text: str | None
) -> None:
    previous_path = tmp_path / "previous.json"
    current_path = tmp_path / "current.json"
    previous_path.write_text(json.dumps(snapshot()), encoding="utf-8")
    if malformed_text is None:
        malformed_text = "[" * 1500 + "0" + "]" * 1500
    current_path.write_text(malformed_text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "validate", str(previous_path), str(current_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["receiptSchemaVersion"] == 1
    assert payload["valid"] is False
    assert codes(payload["errors"]) == {"INPUT_ERROR"}
    assert payload["previousSnapshotDigest"] == "sha256:" + hashlib.sha256(
        previous_path.read_bytes()
    ).hexdigest()
    assert payload["currentSnapshotDigest"] == "sha256:" + hashlib.sha256(
        current_path.read_bytes()
    ).hexdigest()

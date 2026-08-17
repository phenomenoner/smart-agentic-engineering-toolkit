#!/usr/bin/env python3
"""Validate the engineering-wal canon-orchestration transition envelope.

This stateless guard compares two task-local JSON snapshots. ``engineering-wal`` owns only envelope
serialization and continuity. Canonical specification, implementation, review, and completeness
protocols own decision meaning; this guard does not own the WAL, choose a product stage, run evidence,
schedule agents, authenticate caller-provided identities, or grant authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SHA256_PREFIX = "sha256:"
CORE_VERDICTS = {"PASS", "BLOCKED", "INCOMPLETE", "NOT_RUN"}
SEAM_VERDICTS = {"PASS", "BLOCKED", "INCOMPLETE", "NOT_APPLICABLE", "NOT_RUN"}
RELEASE_VERDICTS = {"READY", "BLOCKED", "INCOMPLETE", "NOT_APPLICABLE", "NOT_RUN"}
RELEASE_OVERALL_VERDICTS = {"READY", "BLOCKED", "INCOMPLETE", "NOT_RUN"}
COMMITMENT_STATUSES = {"SUPPORTED", "BLOCKED", "INCOMPLETE", "NOT_RUN"}
COMPLETION_STATUSES = {"IN_PROGRESS", "BLOCKED", "INCOMPLETE", "DONE"}
LOOP_STATUSES = {"ACTIVE", "CLOSED", "BLOCKED", "INCOMPLETE"}
FINDING_CLASSES = {
    "CORE_DEFECT",
    "SPEC_GAP",
    "SEAM_DEFECT",
    "HARNESS_OR_ENV_BLOCKER",
    "AUTHORITY_OR_EXTERNAL_BLOCKER",
    "REVIEW_COVERAGE_GAP",
}
FINDING_STATUSES = {"OPEN", "CLOSED"}
FINDING_DISPOSITIONS = {"OPEN", "CONFIRMED", "REJECTED_FALSE", "RECLASSIFIED"}
FLOOR_LIST_FIELDS = (
    "requirementIds",
    "acceptanceIds",
    "requiredSeams",
    "amendmentAuthorities",
)
MAX_JSON_DEPTH = 100
Error = dict[str, str]


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _json_depth_within(value: object, *, maximum: int = MAX_JSON_DEPTH) -> bool:
    stack: list[tuple[object, int, bool]] = [(value, 0, False)]
    ancestors: set[int] = set()
    while stack:
        item, depth, exiting = stack.pop()
        if depth > maximum:
            return False
        if not isinstance(item, (dict, list)):
            continue
        identity = id(item)
        if exiting:
            ancestors.remove(identity)
            continue
        if identity in ancestors:
            return False
        ancestors.add(identity)
        stack.append((item, depth, True))
        children = item.values() if isinstance(item, dict) else item
        stack.extend((child, depth + 1, False) for child in children)
    return True


def _floor_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    floor = snapshot.get("commitmentFloor")
    if not isinstance(floor, dict):
        return {}
    result = {
        "generation": floor.get("generation"),
        "outcome": floor.get("outcome"),
        "targetTerminalStage": floor.get("targetTerminalStage"),
        "readinessAuthority": floor.get("readinessAuthority"),
    }
    for field in FLOOR_LIST_FIELDS:
        value = floor.get(field)
        result[field] = (
            sorted(value)
            if isinstance(value, list) and all(isinstance(item, str) for item in value)
            else value
        )
    return result


def floor_digest(snapshot: dict[str, Any]) -> str:
    """Return the canonical digest for one commitment floor."""

    return SHA256_PREFIX + hashlib.sha256(_canonical_json(_floor_payload(snapshot))).hexdigest()


def _error(code: str, path: str, message: str) -> Error:
    return {"code": code, "path": path, "message": message}


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _identifier(value: object) -> bool:
    return _text(value) and value == value.strip()


def _enum(value: object, allowed: set[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _strings(value: object, *, nonempty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (bool(value) or not nonempty)
        and all(isinstance(item, str) and item == item.strip() and bool(item) for item in value)
        and len(value) == len(set(value))
    )


def _string_sequence(value: object) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, str) and item == item.strip() and bool(item) for item in value
    )


def _digest(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith(SHA256_PREFIX):
        return False
    suffix = value.removeprefix(SHA256_PREFIX)
    return len(suffix) == 64 and all(char in "0123456789abcdef" for char in suffix)


def _integer(value: object, *, minimum: int) -> bool:
    return type(value) is int and value >= minimum


def _validate_floor(snapshot: dict[str, Any], label: str, errors: list[Error]) -> None:
    floor = snapshot.get("commitmentFloor")
    path = f"{label}.commitmentFloor"
    if not isinstance(floor, dict):
        errors.append(_error("FLOOR_TYPE", path, "must be an object"))
        return
    if not _integer(floor.get("generation"), minimum=1):
        errors.append(_error("FLOOR_GENERATION", f"{path}.generation", "must be an integer >= 1"))
    for field in ("outcome", "targetTerminalStage"):
        if not _text(floor.get(field)):
            errors.append(_error("FLOOR_FIELD", f"{path}.{field}", "must be non-empty"))
    if not _identifier(floor.get("readinessAuthority")):
        errors.append(
            _error("FLOOR_FIELD", f"{path}.readinessAuthority", "must be a trim-free identity")
        )
    for field in FLOOR_LIST_FIELDS:
        if not _strings(floor.get(field), nonempty=True):
            errors.append(_error("FLOOR_LIST", f"{path}.{field}", "must be unique and non-empty"))
    requirements = floor.get("requirementIds")
    acceptances = floor.get("acceptanceIds")
    if (
        isinstance(requirements, list)
        and isinstance(acceptances, list)
        and _strings(requirements, nonempty=True)
        and _strings(acceptances, nonempty=True)
        and not set(requirements).isdisjoint(acceptances)
    ):
        errors.append(
            _error(
                "FLOOR_ID_NAMESPACE",
                path,
                "requirementIds and acceptanceIds must be disjoint",
            )
        )
    if not _digest(floor.get("digest")) or floor.get("digest") != floor_digest(snapshot):
        errors.append(_error("FLOOR_DIGEST", f"{path}.digest", "must match canonical floor bytes"))


def _validate_identities(snapshot: dict[str, Any], label: str, errors: list[Error]) -> None:
    for field, minimum in (("specification", 1), ("candidate", 0)):
        identity = snapshot.get(field)
        path = f"{label}.{field}"
        if not isinstance(identity, dict):
            errors.append(_error("IDENTITY_TYPE", path, "must be an object"))
            continue
        generation = identity.get("generation")
        if not _integer(generation, minimum=minimum):
            errors.append(_error("IDENTITY_GENERATION", f"{path}.generation", "is invalid"))
        digest = identity.get("digest")
        if digest is not None and not _digest(digest):
            errors.append(_error("IDENTITY_DIGEST", f"{path}.digest", "must be null or sha256"))


def _validate_verdicts(snapshot: dict[str, Any], label: str, errors: list[Error]) -> None:
    verdicts = snapshot.get("verdicts")
    path = f"{label}.verdicts"
    if not isinstance(verdicts, dict):
        errors.append(_error("VERDICTS_TYPE", path, "must be an object"))
        return
    if not _enum(verdicts.get("core"), CORE_VERDICTS):
        errors.append(_error("CORE_VERDICT", f"{path}.core", "is invalid"))
    for field, allowed in (("seams", SEAM_VERDICTS), ("release", RELEASE_VERDICTS)):
        cells = verdicts.get(field)
        if not isinstance(cells, dict) or not all(
            _identifier(k) and _enum(v, allowed) for k, v in cells.items()
        ):
            errors.append(_error("VERDICT_CELLS", f"{path}.{field}", "contains invalid cells"))
    if not _enum(verdicts.get("releaseOverall"), RELEASE_OVERALL_VERDICTS):
        errors.append(_error("RELEASE_OVERALL_VERDICT", f"{path}.releaseOverall", "is invalid"))


def _validate_budgets(snapshot: dict[str, Any], label: str, errors: list[Error]) -> None:
    budgets = snapshot.get("loopBudgets")
    path = f"{label}.loopBudgets"
    if not isinstance(budgets, dict) or set(budgets) != {"specification", "delivery"}:
        errors.append(_error("LOOP_BUDGETS", path, "must contain specification and delivery"))
        return
    for name, budget in budgets.items():
        cell_path = f"{path}.{name}"
        if not isinstance(budget, dict):
            errors.append(_error("LOOP_BUDGET", cell_path, "must be an object"))
            continue
        maximum = budget.get("maxPasses")
        used = budget.get("usedPasses")
        signature = budget.get("lastFindingSignature")
        history = budget.get("signatureHistory")
        valid = (
            type(maximum) is int
            and maximum >= 1
            and type(used) is int
            and 0 <= used <= maximum
            and _enum(budget.get("status"), LOOP_STATUSES)
            and isinstance(history, list)
            and _string_sequence(history)
            and len(history) == used
            and signature == (history[-1] if history else None)
        )
        if not valid:
            errors.append(_error("LOOP_BUDGET", cell_path, "contains an invalid bound or status"))
        elif (
            isinstance(history, list)
            and _string_sequence(history)
            and len(history) != len(set(history))
        ):
            errors.append(_error("LOOP_SIGNATURE_REPEAT", f"{cell_path}.signatureHistory", "contains a cycle"))
        elif (
            type(used) is int
            and type(maximum) is int
            and used >= maximum
            and budget["status"] == "ACTIVE"
        ):
            errors.append(_error("LOOP_BUDGET_EXHAUSTED", cell_path, "must stop fail-closed"))


def _valid_reclassification(record: object, *, owner: object) -> bool:
    return (
        isinstance(record, dict)
        and _enum(record.get("oldClass"), FINDING_CLASSES)
        and _enum(record.get("newClass"), FINDING_CLASSES)
        and record.get("authority") == owner
        and _identifier(record.get("oldDispositionOwner"))
        and _identifier(record.get("newDispositionOwner"))
        and _text(record.get("reason"))
        and _strings(record.get("affectedCells"), nonempty=True)
        and _text(record.get("firstUnsafeOperation"))
        and _strings(record.get("evidenceIds"), nonempty=True)
    )


def _valid_finding(item: object) -> bool:
    if not (
        isinstance(item, dict)
        and _identifier(item.get("id"))
        and isinstance(item.get("blocking"), bool)
        and _enum(item.get("class"), FINDING_CLASSES)
        and _enum(item.get("status"), FINDING_STATUSES)
        and _enum(item.get("ownerDisposition"), FINDING_DISPOSITIONS)
        and _identifier(item.get("classificationOwner"))
        and _identifier(item.get("dispositionOwner"))
        and _text(item.get("firstUnsafeOperation"))
        and _strings(item.get("affectedCells"), nonempty=True)
        and _strings(item.get("evidenceIds"), nonempty=True)
        and isinstance(item.get("reclassifications"), list)
        and all(
            _valid_reclassification(record, owner=item.get("classificationOwner"))
            for record in item.get("reclassifications", [])
        )
    ):
        return False
    expected_class = item["class"]
    expected_disposition_owner = item["dispositionOwner"]
    history = item["reclassifications"]
    if history:
        if (
            item["affectedCells"] != history[-1]["affectedCells"]
            or item["firstUnsafeOperation"] != history[-1]["firstUnsafeOperation"]
            or item["evidenceIds"] != history[-1]["evidenceIds"]
        ):
            return False
        for old_record, new_record in zip(history, history[1:], strict=False):
            if (
                old_record["affectedCells"] != new_record["affectedCells"]
                or old_record["firstUnsafeOperation"]
                != new_record["firstUnsafeOperation"]
                or not set(old_record["evidenceIds"])
                < set(new_record["evidenceIds"])
            ):
                return False
    for record in reversed(history):
        if (
            record["newClass"] != expected_class
            or record["newDispositionOwner"] != expected_disposition_owner
        ):
            return False
        expected_class = record["oldClass"]
        expected_disposition_owner = record["oldDispositionOwner"]
    closure = item.get("closure")
    if item["status"] == "OPEN":
        return item["ownerDisposition"] in {"OPEN", "RECLASSIFIED"} and closure is None
    if item["ownerDisposition"] not in {"CONFIRMED", "REJECTED_FALSE"}:
        return False
    return (
        isinstance(closure, dict)
        and closure.get("authority") == item["dispositionOwner"]
        and _text(closure.get("reason"))
        and _strings(closure.get("evidenceIds"), nonempty=True)
        and bool(set(closure.get("evidenceIds", [])) - set(item["evidenceIds"]))
    )


def _validate_findings(
    snapshot: dict[str, Any],
    label: str,
    errors: list[Error],
    *,
    trusted_finding_ids: set[str] | None = None,
) -> None:
    findings = snapshot.get("findings")
    path = f"{label}.findings"
    if not isinstance(findings, list) or not all(_valid_finding(item) for item in findings):
        errors.append(_error("FINDINGS", path, "contains an invalid evidence-bound finding"))
    elif len({item["id"] for item in findings}) != len(findings):
        errors.append(_error("FINDING_IDS", path, "IDs must be unique"))
    else:
        allowed_cells = _canonical_finding_cells(snapshot)
        if allowed_cells is not None:
            for item in findings:
                if trusted_finding_ids is not None and item["id"] in trusted_finding_ids:
                    continue
                if not set(item["affectedCells"]) <= allowed_cells:
                    errors.append(
                        _error(
                            "FINDING_CELL_BINDING",
                            f"{path}.{item['id']}.affectedCells",
                            "must reference only frozen commitment, seam, or release cells",
                        )
                    )


def _canonical_finding_cells(snapshot: dict[str, Any]) -> set[str] | None:
    floor = snapshot.get("commitmentFloor")
    if not isinstance(floor, dict):
        return None
    requirement_ids = floor.get("requirementIds")
    acceptance_ids = floor.get("acceptanceIds")
    required_seams = floor.get("requiredSeams")
    if not (
        isinstance(requirement_ids, list)
        and isinstance(acceptance_ids, list)
        and isinstance(required_seams, list)
        and _strings(requirement_ids, nonempty=True)
        and _strings(acceptance_ids, nonempty=True)
        and _strings(required_seams, nonempty=True)
    ):
        return None
    claim_cells = {
        f"core/{claim_id}" for claim_id in [*requirement_ids, *acceptance_ids]
    }
    seam_cells = {
        cell
        for seam in required_seams
        for cell in (f"seam/{seam}", f"release/{seam}")
    }
    return {"core", "releaseOverall", *claim_cells, *seam_cells}


def _validate_commitments(snapshot: dict[str, Any], label: str, errors: list[Error]) -> None:
    commitments = snapshot.get("commitments")
    path = f"{label}.commitments"
    if not isinstance(commitments, dict):
        errors.append(_error("COMMITMENTS_TYPE", path, "must be an object"))
        return
    for requirement_id, cell in commitments.items():
        valid = (
            _identifier(requirement_id)
            and isinstance(cell, dict)
            and _enum(cell.get("status"), COMMITMENT_STATUSES)
            and _strings(cell.get("evidenceIds", []))
        )
        if not valid:
            errors.append(_error("COMMITMENT_CELL", f"{path}.{requirement_id}", "is invalid"))


def _validate_required_cell_coverage(
    snapshot: dict[str, Any], label: str, errors: list[Error]
) -> None:
    floor = snapshot.get("commitmentFloor")
    verdicts = snapshot.get("verdicts")
    commitments = snapshot.get("commitments")
    if not isinstance(floor, dict):
        return
    required_seams = floor.get("requiredSeams")
    requirement_ids = floor.get("requirementIds")
    acceptance_ids = floor.get("acceptanceIds")
    if (
        isinstance(required_seams, list)
        and _strings(required_seams, nonempty=True)
        and isinstance(verdicts, dict)
    ):
        for field in ("seams", "release"):
            cells = verdicts.get(field)
            if isinstance(cells, dict) and set(cells) != set(required_seams):
                errors.append(
                    _error(
                        "VERDICT_COVERAGE",
                        f"{label}.verdicts.{field}",
                        "must contain exactly the frozen required seam cells",
                    )
                )
    if (
        isinstance(requirement_ids, list)
        and isinstance(acceptance_ids, list)
        and _strings(requirement_ids, nonempty=True)
        and _strings(acceptance_ids, nonempty=True)
        and isinstance(commitments, dict)
        and set(commitments) != (set(requirement_ids) | set(acceptance_ids))
    ):
        errors.append(
            _error(
                "COMMITMENT_COVERAGE",
                f"{label}.commitments",
                "must contain exactly the frozen requirement and acceptance cells",
            )
        )


def _positive_verdict_cells(snapshot: dict[str, Any]) -> list[tuple[str, str]]:
    verdicts = snapshot["verdicts"]
    required_seams = sorted(set(snapshot["commitmentFloor"]["requiredSeams"]))
    cells: list[tuple[str, str]] = []
    if verdicts["core"] == "PASS":
        cells.append(("core", "PASS"))
    cells.extend(
        (f"seam:{target}", "PASS")
        for target in required_seams
        if verdicts["seams"].get(target) == "PASS"
    )
    cells.extend(
        (f"release:{target}", "READY")
        for target in required_seams
        if verdicts["release"].get(target) == "READY"
    )
    if verdicts["releaseOverall"] == "READY":
        cells.append(("releaseOverall", "READY"))
    return cells


def _valid_receipt_cell(value: object) -> bool:
    if isinstance(value, str) and value in {"core", "releaseOverall"}:
        return True
    return isinstance(value, str) and any(
        value.startswith(prefix) and _identifier(value.removeprefix(prefix))
        for prefix in ("seam:", "release:")
    )


def _valid_receipt_decision(cell: object, decision: object) -> bool:
    if cell == "core" or (isinstance(cell, str) and cell.startswith("seam:")):
        return decision == "PASS"
    if cell == "releaseOverall" or (
        isinstance(cell, str) and cell.startswith("release:")
    ):
        return decision == "READY"
    return False


def _valid_decision_receipt(receipt: object) -> bool:
    return (
        isinstance(receipt, dict)
        and _identifier(receipt.get("id"))
        and _valid_receipt_cell(receipt.get("cell"))
        and _valid_receipt_decision(receipt.get("cell"), receipt.get("decision"))
        and _identifier(receipt.get("authority"))
        and _digest(receipt.get("floorDigest"))
        and _digest(receipt.get("specificationDigest"))
        and _digest(receipt.get("candidateDigest"))
        and _strings(receipt.get("evidenceIds"), nonempty=True)
        and _text(receipt.get("reason"))
    )


def _validate_decision_receipts(
    snapshot: dict[str, Any], label: str, errors: list[Error]
) -> None:
    receipts = snapshot.get("decisionReceipts")
    path = f"{label}.decisionReceipts"
    if not isinstance(receipts, list) or not all(_valid_decision_receipt(item) for item in receipts):
        errors.append(_error("DECISION_RECEIPTS", path, "contains an invalid owner receipt"))
        return
    receipt_ids = [item["id"] for item in receipts]
    if len(receipt_ids) != len(set(receipt_ids)):
        errors.append(_error("DECISION_RECEIPT_IDS", path, "receipt IDs must be unique"))


def _validate_positive_receipts(snapshot: dict[str, Any]) -> list[Error]:
    errors: list[Error] = []
    receipts = snapshot["decisionReceipts"]
    latest = {receipt["cell"]: receipt for receipt in receipts}
    floor = snapshot["commitmentFloor"]
    expected_common = {
        "authority": floor["readinessAuthority"],
        "floorDigest": floor["digest"],
        "specificationDigest": snapshot["specification"]["digest"],
        "candidateDigest": snapshot["candidate"]["digest"],
    }
    for cell, decision in _positive_verdict_cells(snapshot):
        receipt = latest.get(cell)
        expected = {"cell": cell, "decision": decision, **expected_common}
        if receipt is None or any(receipt.get(field) != value for field, value in expected.items()):
            errors.append(
                _error(
                    "POSITIVE_DECISION_RECEIPT",
                    f"current.decisionReceipts.{cell}",
                    "needs the readiness owner's identity- and evidence-bound receipt",
                )
            )
    return errors


def _validate_positive_promotions(
    previous: dict[str, Any], current: dict[str, Any]
) -> list[Error]:
    errors: list[Error] = []
    old_positive = dict(_positive_verdict_cells(previous))
    appended = current["decisionReceipts"][len(previous["decisionReceipts"]) :]
    latest_appended = {receipt["cell"]: receipt for receipt in appended}
    floor = current["commitmentFloor"]
    for cell, decision in _positive_verdict_cells(current):
        if old_positive.get(cell) == decision:
            continue
        receipt = latest_appended.get(cell)
        expected = {
            "cell": cell,
            "decision": decision,
            "authority": floor["readinessAuthority"],
            "floorDigest": floor["digest"],
            "specificationDigest": current["specification"]["digest"],
            "candidateDigest": current["candidate"]["digest"],
        }
        if receipt is None or any(receipt.get(field) != value for field, value in expected.items()):
            errors.append(
                _error(
                    "POSITIVE_DECISION_PROMOTION",
                    f"current.decisionReceipts.{cell}",
                    "promotion needs a newly appended owner receipt",
                )
            )
    return errors


def _receipt_matches_current_positive(
    receipt: dict[str, Any], current: dict[str, Any]
) -> bool:
    expected_decisions = dict(_positive_verdict_cells(current))
    cell = receipt["cell"]
    return (
        expected_decisions.get(cell) == receipt["decision"]
        and receipt["authority"] == current["commitmentFloor"]["readinessAuthority"]
        and receipt["floorDigest"] == current["commitmentFloor"]["digest"]
        and receipt["specificationDigest"] == current["specification"]["digest"]
        and receipt["candidateDigest"] == current["candidate"]["digest"]
    )


def _validate_appended_receipts(
    previous: dict[str, Any], current: dict[str, Any]
) -> list[Error]:
    errors: list[Error] = []
    appended = current["decisionReceipts"][len(previous["decisionReceipts"]) :]
    for offset, receipt in enumerate(appended, start=len(previous["decisionReceipts"])):
        if not _receipt_matches_current_positive(receipt, current):
            errors.append(
                _error(
                    "DECISION_RECEIPT_CURRENT_CELL",
                    f"current.decisionReceipts.{offset}",
                    "must bind an existing current positive cell, decision, authority, and identity",
                )
            )
    return errors


def _valid_amendment_record(record: object) -> bool:
    return (
        isinstance(record, dict)
        and _integer(record.get("fromFloorGeneration"), minimum=1)
        and _integer(record.get("toFloorGeneration"), minimum=2)
        and record["toFloorGeneration"] == record["fromFloorGeneration"] + 1
        and _digest(record.get("previousFloorDigest"))
        and _digest(record.get("newFloorDigest"))
        and _text(record.get("oldTarget"))
        and _text(record.get("newTarget"))
        and _identifier(record.get("authority"))
        and _text(record.get("reason"))
        and _strings(record.get("affectedRequirementIds"))
        and _strings(record.get("affectedAcceptanceIds"))
        and _strings(record.get("affectedSeams"))
        and bool(
            record.get("affectedRequirementIds")
            or record.get("affectedAcceptanceIds")
            or record.get("affectedSeams")
        )
        and _strings(record.get("invalidatedEvidenceIds"))
    )


def _validate_amendment_history(
    snapshot: dict[str, Any], label: str, errors: list[Error]
) -> None:
    amendments = snapshot.get("amendments")
    path = f"{label}.amendments"
    if not isinstance(amendments, list) or not all(
        _valid_amendment_record(item) for item in amendments
    ):
        errors.append(_error("AMENDMENTS_TYPE", path, "contains an invalid amendment record"))
        return
    floor = snapshot.get("commitmentFloor")
    if not isinstance(floor, dict) or not _integer(floor.get("generation"), minimum=1):
        return
    if floor["generation"] != len(amendments) + 1:
        errors.append(_error("AMENDMENT_HISTORY_LENGTH", path, "does not cover every floor generation"))
    for old, new in zip(amendments, amendments[1:], strict=False):
        chained = (
            old["toFloorGeneration"] == new["fromFloorGeneration"]
            and old["newFloorDigest"] == new["previousFloorDigest"]
            and old["newTarget"] == new["oldTarget"]
        )
        if not chained:
            errors.append(_error("AMENDMENT_HISTORY_CHAIN", path, "contains a broken digest/target chain"))
            break
    if amendments:
        last = amendments[-1]
        final_bound = (
            last["toFloorGeneration"] == floor["generation"]
            and last["newFloorDigest"] == floor.get("digest")
            and last["newTarget"] == floor.get("targetTerminalStage")
        )
        if not final_bound:
            errors.append(_error("AMENDMENT_HISTORY_HEAD", path, "does not bind the current floor"))


def _validate_snapshot(
    snapshot: object,
    *,
    label: str,
    trusted_finding_ids: set[str] | None = None,
) -> list[Error]:
    """Validate only fields required by transition and completion guards."""

    if not isinstance(snapshot, dict):
        return [_error("SNAPSHOT_TYPE", label, "must be a JSON object")]
    if not _json_depth_within(snapshot):
        return [
            _error(
                "JSON_DEPTH",
                label,
                f"must not exceed {MAX_JSON_DEPTH} nested containers or contain cycles",
            )
        ]
    errors: list[Error] = []
    if type(snapshot.get("schemaVersion")) is not int or snapshot["schemaVersion"] != 1:
        errors.append(_error("SCHEMA_VERSION", f"{label}.schemaVersion", "must equal 1"))
    if not _identifier(snapshot.get("taskId")):
        errors.append(_error("TASK_ID", f"{label}.taskId", "must be a trim-free identity"))
    generation = snapshot.get("generation")
    if not _integer(generation, minimum=1):
        errors.append(_error("STATE_GENERATION", f"{label}.generation", "must be >= 1"))
    _validate_floor(snapshot, label, errors)
    _validate_identities(snapshot, label, errors)
    _validate_verdicts(snapshot, label, errors)
    _validate_budgets(snapshot, label, errors)
    _validate_findings(
        snapshot,
        label,
        errors,
        trusted_finding_ids=trusted_finding_ids,
    )
    _validate_commitments(snapshot, label, errors)
    _validate_required_cell_coverage(snapshot, label, errors)
    _validate_decision_receipts(snapshot, label, errors)
    _validate_amendment_history(snapshot, label, errors)
    completion = snapshot.get("completion")
    if not isinstance(completion, dict) or not _enum(
        completion.get("status"), COMPLETION_STATUSES
    ):
        errors.append(_error("COMPLETION_STATUS", f"{label}.completion.status", "is invalid"))
    elif completion.get("achievedStage") is not None and not _text(
        completion.get("achievedStage")
    ):
        errors.append(
            _error(
                "COMPLETION_STAGE",
                f"{label}.completion.achievedStage",
                "must be null or a non-empty string",
            )
        )
    return errors


def validate_snapshot(snapshot: object, *, label: str) -> list[Error]:
    """Validate a standalone/import snapshot against only its active floor."""

    return _validate_snapshot(snapshot, label=label)


def _validate_amendment(previous: dict[str, Any], current: dict[str, Any]) -> list[Error]:
    amendment = current["amendments"][-1]
    old_floor = previous["commitmentFloor"]
    new_floor = current["commitmentFloor"]
    expected = {
        "fromFloorGeneration": old_floor["generation"],
        "toFloorGeneration": new_floor["generation"],
        "previousFloorDigest": old_floor["digest"],
        "newFloorDigest": new_floor["digest"],
        "oldTarget": old_floor["targetTerminalStage"],
        "newTarget": new_floor["targetTerminalStage"],
    }
    errors = [
        _error("AMENDMENT_BINDING", f"current.amendments[-1].{field}", f"must equal {value!r}")
        for field, value in expected.items()
        if amendment.get(field) != value
    ]
    if amendment.get("authority") not in old_floor["amendmentAuthorities"]:
        errors.append(_error("AMENDMENT_AUTHORITY", "current.amendments[-1].authority", "is not authorized"))
    if not _text(amendment.get("reason")):
        errors.append(_error("AMENDMENT_REASON", "current.amendments[-1].reason", "must be non-empty"))
    affected_fields = (
        ("requirementIds", "affectedRequirementIds"),
        ("acceptanceIds", "affectedAcceptanceIds"),
        ("requiredSeams", "affectedSeams"),
    )
    for floor_field, amendment_field in affected_fields:
        affected = set(amendment[amendment_field])
        old_ids = set(old_floor[floor_field])
        new_ids = set(new_floor[floor_field])
        if not (old_ids ^ new_ids) <= affected or not affected <= (old_ids | new_ids):
            errors.append(
                _error(
                    "AMENDMENT_AFFECTED_BINDING",
                    f"current.amendments[-1].{amendment_field}",
                    f"must cover changed {floor_field} and reference only old/new IDs",
                )
            )

    affected_claims = set(amendment["affectedRequirementIds"]) | set(
        amendment["affectedAcceptanceIds"]
    )
    affected_seams = set(amendment["affectedSeams"])
    expected_invalidated: set[str] = set()
    known_evidence: set[str] = set()
    for claim_id, cell in previous["commitments"].items():
        evidence = set(cell["evidenceIds"])
        known_evidence.update(evidence)
        if claim_id in affected_claims:
            expected_invalidated.update(evidence)
    affected_tokens = affected_claims | affected_seams
    for finding in previous["findings"]:
        finding_evidence = set(finding["evidenceIds"])
        for record in finding["reclassifications"]:
            finding_evidence.update(record["evidenceIds"])
        if finding.get("closure"):
            finding_evidence.update(finding["closure"]["evidenceIds"])
        known_evidence.update(finding_evidence)
        if any(
            token in cell
            for token in affected_tokens
            for cell in finding["affectedCells"]
        ):
            expected_invalidated.update(finding_evidence)
    positive_cells = dict(_positive_verdict_cells(previous))
    latest_receipts: dict[str, dict[str, Any]] = {}
    for receipt in previous["decisionReceipts"]:
        known_evidence.update(receipt["evidenceIds"])
        latest_receipts[receipt["cell"]] = receipt
    for cell, receipt in latest_receipts.items():
        if (
            positive_cells.get(cell) == receipt["decision"]
            and any(cell in {f"seam:{seam}", f"release:{seam}"} for seam in affected_seams)
        ):
            expected_invalidated.update(receipt["evidenceIds"])
    declared_invalidated = set(amendment["invalidatedEvidenceIds"])
    if not expected_invalidated <= declared_invalidated or not declared_invalidated <= known_evidence:
        errors.append(
            _error(
                "AMENDMENT_EVIDENCE_BINDING",
                "current.amendments[-1].invalidatedEvidenceIds",
                "must cover affected prior evidence and may not invent evidence IDs",
            )
        )
    for claim_id in affected_claims:
        cell = current["commitments"].get(claim_id)
        if isinstance(cell, dict) and (cell.get("status") == "SUPPORTED" or cell.get("evidenceIds")):
            errors.append(
                _error(
                    "AMENDMENT_CLAIM_RESET",
                    f"current.commitments.{claim_id}",
                    "affected claim must reset before reevaluation",
                )
            )
    return errors


def _valid_new_finding_state(item: dict[str, Any]) -> bool:
    return (
        item["status"] == "OPEN"
        and item["ownerDisposition"] == "OPEN"
        and not item["reclassifications"]
        and item.get("closure") is None
    )


def _validate_finding_changes(previous: dict[str, Any], current: dict[str, Any]) -> list[Error]:
    errors: list[Error] = []
    old_by_id = {item["id"]: item for item in previous["findings"]}
    new_by_id = {item["id"]: item for item in current["findings"]}
    active_cells = _canonical_finding_cells(current)
    for finding_id, new in new_by_id.items():
        if finding_id not in old_by_id:
            if not _valid_new_finding_state(new):
                errors.append(
                    _error(
                        "NEW_FINDING_INITIAL_STATE",
                        f"current.findings.{finding_id}",
                        "a newly observed finding must enter OPEN without closure or reclassification",
                    )
                )
            if active_cells is not None and not set(new["affectedCells"]) <= active_cells:
                errors.append(
                    _error(
                        "FINDING_CELL_BINDING",
                        f"current.findings.{finding_id}.affectedCells",
                        "a new finding must reference the active floor namespace",
                    )
                )
    for finding_id, old in old_by_id.items():
        path = f"current.findings.{finding_id}"
        new = new_by_id.get(finding_id)
        if new is None:
            errors.append(_error("FINDING_REMOVED", "current.findings", f"lost {finding_id!r}"))
            continue
        if old["status"] == "CLOSED" and _finding_lifecycle_semantics(
            new
        ) != _finding_lifecycle_semantics(old):
            errors.append(
                _error(
                    "FINDING_TERMINAL_IMMUTABLE",
                    path,
                    "a closed finding is immutable; append a new finding for recurrence",
                )
            )
        if new["classificationOwner"] != old["classificationOwner"]:
            errors.append(_error("FINDING_OWNER_CHANGE", f"{path}.classificationOwner", "is immutable"))
        if new["blocking"] != old["blocking"]:
            errors.append(_error("FINDING_BLOCKING_CHANGE", f"{path}.blocking", "is immutable"))
        if new["class"] == old["class"] and new["dispositionOwner"] != old["dispositionOwner"]:
            errors.append(
                _error("FINDING_DISPOSITION_OWNER_CHANGE", f"{path}.dispositionOwner", "needs reclassification")
            )
        old_history = old["reclassifications"]
        new_history = new["reclassifications"]
        if new_history[: len(old_history)] != old_history:
            errors.append(_error("RECLASSIFICATION_PREFIX", f"{path}.reclassifications", "is not append-only"))
        if new["class"] == old["class"] and new_history != old_history:
            errors.append(_error("SPURIOUS_RECLASSIFICATION", f"{path}.reclassifications", "class did not change"))
        if new["class"] == old["class"]:
            for field in ("affectedCells", "firstUnsafeOperation", "evidenceIds"):
                if new[field] != old[field]:
                    errors.append(
                        _error("FINDING_PACKET_REWRITE", f"{path}.{field}", "requires owner reclassification")
                    )
        elif new["class"] != old["class"]:
            for field in ("affectedCells", "firstUnsafeOperation"):
                if new[field] != old[field]:
                    errors.append(
                        _error(
                            "FINDING_PACKET_REWRITE",
                            f"{path}.{field}",
                            "original observation fields are immutable",
                        )
                    )
            if not set(old["evidenceIds"]) <= set(new["evidenceIds"]):
                errors.append(
                    _error(
                        "FINDING_EVIDENCE_REMOVED",
                        f"{path}.evidenceIds",
                        "reclassification must preserve prior evidence",
                    )
                )
            if len(new_history) != len(old_history) + 1:
                errors.append(_error("FINDING_RECLASSIFICATION_REQUIRED", f"{path}.reclassifications", "needs one record"))
            else:
                record = new_history[-1]
                expected = {
                    "oldClass": old["class"],
                    "newClass": new["class"],
                    "authority": old["classificationOwner"],
                    "oldDispositionOwner": old["dispositionOwner"],
                    "newDispositionOwner": new["dispositionOwner"],
                    "affectedCells": new["affectedCells"],
                    "firstUnsafeOperation": new["firstUnsafeOperation"],
                    "evidenceIds": new["evidenceIds"],
                }
                errors.extend(
                    _error("RECLASSIFICATION_BINDING", f"{path}.reclassifications[-1].{field}", "does not match")
                    for field, value in expected.items()
                    if record.get(field) != value
                )
                if not _text(record.get("reason")):
                    errors.append(_error("RECLASSIFICATION_REASON", f"{path}.reclassifications[-1].reason", "is empty"))
                if not set(new["evidenceIds"]) - set(old["evidenceIds"]):
                    errors.append(
                        _error(
                            "RECLASSIFICATION_NEW_EVIDENCE",
                            f"{path}.reclassifications[-1].evidenceIds",
                            "must add evidence not present in the previous class",
                        )
                    )
        closing = old["status"] == "OPEN" and new["status"] == "CLOSED"
        class_changed = new["class"] != old["class"]
        if closing and class_changed:
            errors.append(
                _error(
                    "FINDING_TEMPORAL_BOUNDARY",
                    path,
                    "reclassification and closure require separate transitions",
                )
            )
        if old["status"] == "CLOSED" and new["status"] == "OPEN":
            errors.append(_error("FINDING_REOPEN", f"{path}.status", "append a new finding instead"))
        if new["ownerDisposition"] != old["ownerDisposition"] and not (closing or class_changed):
            errors.append(
                _error("FINDING_DISPOSITION_CHANGE", f"{path}.ownerDisposition", "requires owner action")
            )
        if closing:
            closure = new.get("closure")
            valid = (
                isinstance(closure, dict)
                and closure.get("authority") == new["dispositionOwner"]
                and _text(closure.get("reason"))
                and _strings(closure.get("evidenceIds"), nonempty=True)
            )
            if not valid:
                errors.append(_error("FINDING_CLOSURE_AUTHORITY", f"{path}.closure", "is not owner-bound"))
            elif not set(closure["evidenceIds"]) - set(old["evidenceIds"]):
                errors.append(
                    _error(
                        "FINDING_CLOSURE_EVIDENCE",
                        f"{path}.closure.evidenceIds",
                        "must add evidence beyond the open finding packet",
                    )
                )
        elif new.get("closure") != old.get("closure"):
            errors.append(_error("SPURIOUS_FINDING_CLOSURE", f"{path}.closure", "status did not close"))
    return errors


def _identity_pair(snapshot: dict[str, Any], field: str) -> tuple[int, object]:
    identity = snapshot[field]
    return identity["generation"], identity.get("digest")


def _validate_identity_changes(
    previous: dict[str, Any], current: dict[str, Any]
) -> tuple[list[Error], bool]:
    errors: list[Error] = []
    changed = False
    for field in ("specification", "candidate"):
        old_generation, old_digest = _identity_pair(previous, field)
        new_generation, new_digest = _identity_pair(current, field)
        field_changed = (old_generation, old_digest) != (new_generation, new_digest)
        changed = changed or field_changed
        path = f"current.{field}"
        if new_generation < old_generation:
            errors.append(_error("IDENTITY_REWIND", f"{path}.generation", "cannot decrease"))
        if new_digest == old_digest and new_generation != old_generation:
            errors.append(
                _error("IDENTITY_GENERATION_BINDING", path, "generation changed without digest change")
            )
        if new_digest != old_digest and new_generation != old_generation + 1:
            errors.append(
                _error("IDENTITY_DIGEST_BINDING", path, "digest change must advance generation by one")
            )
    return errors, changed


def _validate_claim_reset(
    current: dict[str, Any], *, reset_commitments: bool, code: str
) -> list[Error]:
    errors: list[Error] = []
    if _positive_verdict_cells(current):
        errors.append(_error(code, "current.verdicts", "positive claims must reset before reevaluation"))
    if current["completion"]["status"] == "DONE":
        errors.append(_error(code, "current.completion.status", "cannot complete in a reset transition"))
    if reset_commitments:
        for claim_id, cell in current["commitments"].items():
            if cell["status"] == "SUPPORTED" or cell["evidenceIds"]:
                errors.append(
                    _error(code, f"current.commitments.{claim_id}", "must reset stale evidence")
                )
    return errors


def _validate_terminal_transition(
    previous: dict[str, Any], _current: dict[str, Any]
) -> list[Error]:
    if previous["completion"]["status"] != "DONE":
        return []
    return [
        _error(
            "TERMINAL_TRANSITION",
            "current",
            "DONE is terminal; start a new task instead of appending a snapshot",
        )
    ]


def _finding_pass_semantics(item: dict[str, Any]) -> dict[str, Any]:
    reclassification_fields = (
        "oldClass",
        "newClass",
        "authority",
        "oldDispositionOwner",
        "newDispositionOwner",
        "affectedCells",
        "firstUnsafeOperation",
        "evidenceIds",
    )
    reclassifications = []
    for record in item["reclassifications"]:
        semantic_record = {key: record[key] for key in reclassification_fields}
        semantic_record["affectedCells"] = sorted(set(record["affectedCells"]))
        semantic_record["evidenceIds"] = sorted(set(record["evidenceIds"]))
        reclassifications.append(semantic_record)
    closure = item.get("closure")
    closure_semantics = (
        {
            "authority": closure["authority"],
            "evidenceIds": sorted(set(closure["evidenceIds"])),
        }
        if isinstance(closure, dict)
        else None
    )
    fields = (
        "blocking",
        "class",
        "status",
        "ownerDisposition",
        "classificationOwner",
        "dispositionOwner",
        "firstUnsafeOperation",
        "affectedCells",
        "evidenceIds",
    )
    semantics = {key: item[key] for key in fields}
    semantics["affectedCells"] = sorted(set(item["affectedCells"]))
    semantics["evidenceIds"] = sorted(set(item["evidenceIds"]))
    return semantics | {
        "reclassifications": reclassifications,
        "closure": closure_semantics,
    }


def _finding_lifecycle_semantics(item: dict[str, Any]) -> dict[str, Any]:
    semantics = _finding_pass_semantics(item)
    for semantic_record, record in zip(
        semantics["reclassifications"], item["reclassifications"], strict=True
    ):
        semantic_record["reason"] = record["reason"]
    closure = item.get("closure")
    if isinstance(closure, dict):
        semantics["closure"]["reason"] = closure["reason"]
    return semantics


def _changed_finding_packets(
    previous: dict[str, Any], current: dict[str, Any]
) -> list[dict[str, Any]]:
    old_by_id = {
        item["id"]: _finding_pass_semantics(item) for item in previous["findings"]
    }
    old_packets = {_canonical_json(packet) for packet in old_by_id.values()}
    emitted: set[bytes] = set()
    packets: list[dict[str, Any]] = []
    allowed_cells = _canonical_finding_cells(current)
    for item in current["findings"]:
        if allowed_cells is not None and not set(item["affectedCells"]) <= allowed_cells:
            continue
        packet = _finding_pass_semantics(item)
        encoded = _canonical_json(packet)
        old_packet = old_by_id.get(item["id"])
        changed = (
            old_packet != packet
            if old_packet is not None
            else _valid_new_finding_state(item) and encoded not in old_packets
        )
        if changed and encoded not in emitted:
            packets.append(packet)
            emitted.add(encoded)
    return sorted(packets, key=_canonical_json)


def _receipt_pass_semantics(receipt: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "cell",
        "decision",
        "authority",
        "floorDigest",
        "specificationDigest",
        "candidateDigest",
        "evidenceIds",
    )
    semantics = {key: receipt[key] for key in fields}
    semantics["evidenceIds"] = sorted(set(receipt["evidenceIds"]))
    return semantics


def _amendment_pass_semantics(amendment: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "fromFloorGeneration",
        "toFloorGeneration",
        "previousFloorDigest",
        "newFloorDigest",
        "oldTarget",
        "newTarget",
        "authority",
        "affectedRequirementIds",
        "affectedAcceptanceIds",
        "affectedSeams",
        "invalidatedEvidenceIds",
    )
    semantics = {key: amendment[key] for key in fields}
    for key in (
        "affectedRequirementIds",
        "affectedAcceptanceIds",
        "affectedSeams",
        "invalidatedEvidenceIds",
    ):
        semantics[key] = sorted(set(amendment[key]))
    return semantics


def _pass_delta_payload(
    previous: dict[str, Any], current: dict[str, Any], loop_name: str
) -> dict[str, Any]:
    deltas: list[dict[str, Any]] = []
    floor_changed = _floor_payload(previous) != _floor_payload(current)
    specification_changed = _identity_pair(previous, "specification") != _identity_pair(
        current, "specification"
    )
    candidate_changed = _identity_pair(previous, "candidate") != _identity_pair(
        current, "candidate"
    )
    if floor_changed:
        deltas.append(
            {
                "kind": "commitment-floor",
                "from": previous["commitmentFloor"]["digest"],
                "to": current["commitmentFloor"]["digest"],
            }
        )
    if specification_changed:
        deltas.append(
            {
                "kind": "specification-identity",
                "from": _identity_pair(previous, "specification"),
                "to": _identity_pair(current, "specification"),
            }
        )
    if loop_name == "delivery" and candidate_changed:
        deltas.append(
            {
                "kind": "candidate-identity",
                "from": _identity_pair(previous, "candidate"),
                "to": _identity_pair(current, "candidate"),
            }
        )
    changed_findings = _changed_finding_packets(previous, current)
    if changed_findings:
        deltas.append({"kind": "finding-packets", "values": changed_findings})
    if loop_name == "specification":
        old_amendments = previous["amendments"]
        new_amendments = current["amendments"]
        if len(new_amendments) > len(old_amendments):
            deltas.append(
                {
                    "kind": "amendments",
                    "values": [
                        _amendment_pass_semantics(item)
                        for item in new_amendments[len(old_amendments) :]
                    ],
                }
            )
    else:
        old_receipts = previous["decisionReceipts"]
        new_receipts = current["decisionReceipts"]
        prior_receipt_packets = {
            _canonical_json(_receipt_pass_semantics(item)) for item in old_receipts
        }
        new_receipt_packets: list[dict[str, Any]] = []
        emitted_receipt_packets: set[bytes] = set()
        for item in new_receipts[len(old_receipts) :]:
            packet = _receipt_pass_semantics(item)
            encoded = _canonical_json(packet)
            if (
                _receipt_matches_current_positive(item, current)
                and encoded not in prior_receipt_packets
                and encoded not in emitted_receipt_packets
            ):
                new_receipt_packets.append(packet)
                emitted_receipt_packets.add(encoded)
        if new_receipt_packets:
            deltas.append(
                {
                    "kind": "decision-receipts",
                    "values": sorted(new_receipt_packets, key=_canonical_json),
                }
            )
        bound_claims = set(current["commitmentFloor"]["requirementIds"]) | set(
            current["commitmentFloor"]["acceptanceIds"]
        )
        commitment_deltas = sorted(
            (
                {
                    "claimId": claim_id,
                    "status": cell["status"],
                    "evidenceIds": sorted(set(cell["evidenceIds"])),
                }
                for claim_id, cell in current["commitments"].items()
                if claim_id in bound_claims
                and set(cell["evidenceIds"])
                - set(previous["commitments"].get(claim_id, {}).get("evidenceIds", []))
            ),
            key=lambda item: item["claimId"],
        )
        if commitment_deltas:
            deltas.append({"kind": "commitments", "values": commitment_deltas})
    return {"loop": loop_name, "deltas": deltas}


def pass_signature(
    previous: dict[str, Any], current: dict[str, Any], loop_name: str
) -> str:
    """Return the guard-derived signature for one semantic loop delta."""

    if loop_name not in {"specification", "delivery"}:
        raise ValueError(f"unknown loop: {loop_name}")
    payload = _pass_delta_payload(previous, current, loop_name)
    return SHA256_PREFIX + hashlib.sha256(_canonical_json(payload)).hexdigest()


def _validate_budget_changes(previous: dict[str, Any], current: dict[str, Any]) -> list[Error]:
    errors: list[Error] = []
    floor_changed = _floor_payload(previous) != _floor_payload(current)
    spec_changed = _identity_pair(previous, "specification") != _identity_pair(
        current, "specification"
    )
    candidate_changed = _identity_pair(previous, "candidate") != _identity_pair(
        current, "candidate"
    )
    for name in ("specification", "delivery"):
        old = previous["loopBudgets"][name]
        new = current["loopBudgets"][name]
        path = f"current.loopBudgets.{name}"
        if new["maxPasses"] != old["maxPasses"]:
            errors.append(_error("LOOP_BUDGET_CHANGE", f"{path}.maxPasses", "is immutable"))
        if new["usedPasses"] < old["usedPasses"]:
            errors.append(_error("LOOP_PASS_REWIND", f"{path}.usedPasses", "cannot decrease"))
        if new["usedPasses"] > old["usedPasses"] + 1:
            errors.append(_error("LOOP_PASS_STEP", f"{path}.usedPasses", "may advance by at most one"))
        old_history = old["signatureHistory"]
        new_history = new["signatureHistory"]
        if new_history[: len(old_history)] != old_history:
            errors.append(_error("LOOP_SIGNATURE_PREFIX", f"{path}.signatureHistory", "is not append-only"))
        if new["usedPasses"] == old["usedPasses"] and new_history != old_history:
            errors.append(_error("LOOP_SIGNATURE_STEP", f"{path}.signatureHistory", "changed without a pass"))
        if new["usedPasses"] == old["usedPasses"] + 1:
            if old["status"] != "ACTIVE":
                errors.append(
                    _error(
                        "LOOP_PASS_STATE",
                        f"{path}.usedPasses",
                        "a pass may advance only from ACTIVE",
                    )
                )
            if len(new_history) != len(old_history) + 1:
                errors.append(_error("LOOP_SIGNATURE_STEP", f"{path}.signatureHistory", "needs one signature"))
            else:
                payload = _pass_delta_payload(previous, current, name)
                expected_signature = pass_signature(previous, current, name)
                if not payload["deltas"]:
                    errors.append(
                        _error(
                            "LOOP_PASS_DELTA",
                            f"{path}.signatureHistory",
                            "a pass needs a canonical identity, finding, receipt, or evidence delta",
                        )
                    )
                if new_history[-1] != expected_signature:
                    errors.append(
                        _error(
                            "LOOP_SIGNATURE_BINDING",
                            f"{path}.lastFindingSignature",
                            f"must equal guard-derived {expected_signature}",
                        )
                    )
                elif new_history[-1] in old_history:
                    errors.append(
                        _error(
                            "LOOP_SIGNATURE_REPEAT",
                            f"{path}.lastFindingSignature",
                            "must stop fail-closed",
                        )
                    )
        reopen_allowed = floor_changed or spec_changed or (
            name == "delivery" and candidate_changed
        )
        terminal_statuses = {"CLOSED", "BLOCKED", "INCOMPLETE"}
        if old["status"] in terminal_statuses:
            if reopen_allowed and new["status"] != "ACTIVE":
                errors.append(
                    _error(
                        "LOOP_REOPEN_REQUIRED",
                        f"{path}.status",
                        "changed dependencies require a separate transition back to ACTIVE",
                    )
                )
            elif not reopen_allowed and new["status"] != old["status"]:
                if new["status"] == "ACTIVE":
                    errors.append(
                        _error(
                            "LOOP_REOPEN",
                            f"{path}.status",
                            "needs a changed floor or identity",
                        )
                    )
                else:
                    errors.append(
                        _error(
                            "LOOP_TERMINAL_TRANSITION",
                            f"{path}.status",
                            "must reactivate under changed dependencies before a new disposition",
                        )
                    )
        if (
            old["status"] == "ACTIVE"
            and new["status"] == "CLOSED"
            and new["usedPasses"] != old["usedPasses"] + 1
        ):
            errors.append(
                _error(
                    "LOOP_CLOSE_PASS",
                    f"{path}.status",
                    "closing must record exactly one new discriminating pass",
                )
            )
    return errors


def _validate_release(snapshot: dict[str, Any]) -> list[Error]:
    errors = _validate_positive_receipts(snapshot)
    floor = snapshot["commitmentFloor"]
    verdicts = snapshot["verdicts"]
    identities_bound = (
        _digest(snapshot["specification"].get("digest"))
        and _digest(snapshot["candidate"].get("digest"))
        and _integer(snapshot["candidate"].get("generation"), minimum=1)
    )
    if (
        verdicts["core"] == "PASS"
        or any(value == "PASS" for value in verdicts["seams"].values())
    ) and not identities_bound:
        errors.append(_error("PASS_IDENTITY", "current.verdicts", "PASS claims need bound identities"))
    for target, verdict in verdicts["release"].items():
        if verdict == "READY" and (
            verdicts["core"] != "PASS" or verdicts["seams"].get(target) != "PASS"
        ):
            errors.append(_error("RELEASE_LAUNDERING", f"current.verdicts.release.{target}", "lacks core/seam PASS"))
        if verdict == "READY" and not identities_bound:
            errors.append(_error("RELEASE_IDENTITY", f"current.verdicts.release.{target}", "needs bound identities"))
        if verdict == "READY" and any(
            item["status"] == "OPEN" and item["blocking"] for item in snapshot["findings"]
        ):
            errors.append(
                _error("RELEASE_FINDING", f"current.verdicts.release.{target}", "blocking finding is open")
            )
        if verdict == "READY":
            for claim_id in [*floor["requirementIds"], *floor["acceptanceIds"]]:
                cell = snapshot["commitments"].get(claim_id)
                if (
                    not isinstance(cell, dict)
                    or cell.get("status") != "SUPPORTED"
                    or not cell.get("evidenceIds")
                ):
                    errors.append(
                        _error(
                            "RELEASE_REQUIREMENT",
                            f"current.commitments.{claim_id}",
                            f"target {target!r} lacks evidence",
                        )
                    )
    if verdicts["releaseOverall"] != "READY":
        return errors
    if not identities_bound:
        errors.append(
            _error("RELEASE_OVERALL_IDENTITY", "current.verdicts.releaseOverall", "spec/candidate is unbound")
        )
    incomplete = any(
        verdicts["seams"].get(target) != "PASS"
        or verdicts["release"].get(target) != "READY"
        for target in floor["requiredSeams"]
    )
    if verdicts["core"] != "PASS" or incomplete:
        errors.append(_error("RELEASE_OVERALL_LAUNDERING", "current.verdicts.releaseOverall", "hard target is not ready"))
    if any(item["status"] == "OPEN" and item["blocking"] for item in snapshot["findings"]):
        errors.append(_error("RELEASE_OVERALL_FINDING", "current.verdicts.releaseOverall", "blocking finding is open"))
    for claim_id in [*floor["requirementIds"], *floor["acceptanceIds"]]:
        cell = snapshot["commitments"].get(claim_id)
        if not isinstance(cell, dict) or cell.get("status") != "SUPPORTED" or not cell.get("evidenceIds"):
            errors.append(_error("RELEASE_OVERALL_REQUIREMENT", f"current.commitments.{claim_id}", "lacks evidence"))
    return errors


def _validate_done(snapshot: dict[str, Any]) -> list[Error]:
    if snapshot["completion"]["status"] != "DONE":
        return []
    errors: list[Error] = []
    floor = snapshot["commitmentFloor"]
    verdicts = snapshot["verdicts"]
    if snapshot["completion"].get("achievedStage") != floor["targetTerminalStage"]:
        errors.append(_error("DONE_TARGET_STAGE", "current.completion.achievedStage", "does not match floor"))
    if verdicts["core"] != "PASS":
        errors.append(_error("DONE_CORE", "current.verdicts.core", "must be PASS"))
    if verdicts["releaseOverall"] != "READY":
        errors.append(_error("DONE_RELEASE_OVERALL", "current.verdicts.releaseOverall", "must be READY"))
    if not _digest(snapshot["specification"].get("digest")):
        errors.append(_error("DONE_SPECIFICATION", "current.specification.digest", "must be bound"))
    for target in floor["requiredSeams"]:
        if verdicts["seams"].get(target) != "PASS" or verdicts["release"].get(target) != "READY":
            errors.append(_error("DONE_REQUIRED_SEAM", f"current.verdicts.{target}", "is not ready"))
    if any(item["status"] == "OPEN" and item["blocking"] for item in snapshot["findings"]):
        errors.append(_error("DONE_BLOCKING_FINDING", "current.findings", "blocking finding is open"))
    for claim_id in [*floor["requirementIds"], *floor["acceptanceIds"]]:
        cell = snapshot["commitments"].get(claim_id)
        if not isinstance(cell, dict) or cell.get("status") != "SUPPORTED" or not cell.get("evidenceIds"):
            errors.append(_error("DONE_REQUIREMENT", f"current.commitments.{claim_id}", "lacks evidence"))
    if not _digest(snapshot["candidate"].get("digest")) or not _integer(
        snapshot["candidate"].get("generation"), minimum=1
    ):
        errors.append(_error("DONE_CANDIDATE", "current.candidate.digest", "must be bound"))
    if any(
        budget["status"] != "CLOSED" or budget["usedPasses"] < 1
        for budget in snapshot["loopBudgets"].values()
    ):
        errors.append(
            _error(
                "DONE_LOOP_STATUS",
                "current.loopBudgets",
                "both loops must be CLOSED by a recorded pass",
            )
        )
    return errors


def _validate_invalidated_evidence_reuse(snapshot: dict[str, Any]) -> list[Error]:
    invalidated = {
        evidence_id
        for amendment in snapshot["amendments"]
        for evidence_id in amendment["invalidatedEvidenceIds"]
    }
    if not invalidated:
        return []
    errors: list[Error] = []
    for claim_id, cell in snapshot["commitments"].items():
        reused = invalidated & set(cell["evidenceIds"])
        if reused:
            errors.append(
                _error(
                    "INVALIDATED_EVIDENCE_REUSE",
                    f"current.commitments.{claim_id}.evidenceIds",
                    f"reuses invalidated evidence: {sorted(reused)!r}",
                )
            )
    latest_receipts = {
        receipt["cell"]: receipt for receipt in snapshot["decisionReceipts"]
    }
    for cell, decision in _positive_verdict_cells(snapshot):
        receipt = latest_receipts.get(cell)
        if receipt is None or receipt["decision"] != decision:
            continue
        reused = invalidated & set(receipt["evidenceIds"])
        if reused:
            errors.append(
                _error(
                    "INVALIDATED_EVIDENCE_REUSE",
                    f"current.decisionReceipts.{cell}.evidenceIds",
                    f"reuses invalidated evidence: {sorted(reused)!r}",
                )
            )
    return errors


def _semantic_snapshot_errors(snapshot: dict[str, Any], *, label: str) -> list[Error]:
    errors = [
        *_validate_release(snapshot),
        *_validate_done(snapshot),
        *_validate_invalidated_evidence_reuse(snapshot),
    ]
    if label == "current":
        return errors
    return [
        {
            **error,
            "path": label + error["path"].removeprefix("current"),
        }
        for error in errors
    ]


def validate_transition(previous: object, current: object) -> list[Error]:
    """Reject silent floor changes, owner laundering, cycles, and unsupported completion."""

    trusted_finding_ids: set[str] = set()
    if isinstance(previous, dict) and isinstance(previous.get("findings"), list):
        trusted_finding_ids = {
            item["id"]
            for item in previous["findings"]
            if isinstance(item, dict) and _identifier(item.get("id"))
        }
    previous_errors = _validate_snapshot(
        previous,
        label="previous",
        trusted_finding_ids=trusted_finding_ids,
    )
    current_errors = _validate_snapshot(
        current,
        label="current",
        trusted_finding_ids=trusted_finding_ids,
    )
    errors = [*previous_errors, *current_errors]
    deferred_current_codes = {"AMENDMENT_HISTORY_LENGTH", "AMENDMENT_HISTORY_HEAD"}
    hard_current_errors = [
        error for error in current_errors if error["code"] not in deferred_current_codes
    ]
    if (
        previous_errors
        or hard_current_errors
        or not isinstance(previous, dict)
        or not isinstance(current, dict)
    ):
        return errors
    errors.extend(_semantic_snapshot_errors(previous, label="previous"))
    errors.extend(_semantic_snapshot_errors(current, label="current"))
    if previous["taskId"] != current["taskId"]:
        errors.append(_error("TASK_CHANGE", "current.taskId", "must match previous"))
    if current["generation"] != previous["generation"] + 1:
        errors.append(_error("STATE_GENERATION_STEP", "current.generation", "must advance by one"))

    old_receipts = previous["decisionReceipts"]
    new_receipts = current["decisionReceipts"]
    if new_receipts[: len(old_receipts)] != old_receipts:
        errors.append(_error("DECISION_RECEIPT_PREFIX", "current.decisionReceipts", "is not append-only"))
    errors.extend(_validate_appended_receipts(previous, current))
    errors.extend(_validate_positive_promotions(previous, current))

    identity_errors, identity_changed = _validate_identity_changes(previous, current)
    errors.extend(identity_errors)
    if identity_changed:
        errors.extend(
            _validate_claim_reset(
                current, reset_commitments=True, code="IDENTITY_RESET_REQUIRED"
            )
        )
    errors.extend(_validate_terminal_transition(previous, current))

    old_amendments = previous["amendments"]
    new_amendments = current["amendments"]
    if new_amendments[: len(old_amendments)] != old_amendments:
        errors.append(_error("AMENDMENT_PREFIX", "current.amendments", "is not append-only"))
    floor_changed = _floor_payload(previous) != _floor_payload(current)
    if floor_changed:
        errors.extend(
            _validate_claim_reset(
                current, reset_commitments=False, code="FLOOR_RESET_REQUIRED"
            )
        )
    if not floor_changed and new_amendments != old_amendments:
        errors.append(_error("SPURIOUS_AMENDMENT", "current.amendments", "floor did not change"))
    elif floor_changed:
        old_generation = previous["commitmentFloor"]["generation"]
        if current["commitmentFloor"]["generation"] != old_generation + 1:
            errors.append(_error("FLOOR_GENERATION_STEP", "current.commitmentFloor.generation", "must advance by one"))
        if len(new_amendments) != len(old_amendments) + 1:
            errors.append(_error("FLOOR_AMENDMENT_REQUIRED", "current.amendments", "needs exactly one record"))
        else:
            errors.extend(_validate_amendment(previous, current))

    errors.extend(_validate_finding_changes(previous, current))
    errors.extend(_validate_budget_changes(previous, current))
    return errors


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _raw_digest(raw: bytes) -> str:
    return SHA256_PREFIX + hashlib.sha256(raw).hexdigest()


def _parse_json(raw: bytes) -> object:
    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_invalid_json_constant,
    )


def _load_json_with_digest(path: Path) -> tuple[object, str]:
    raw = path.read_bytes()
    return _parse_json(raw), _raw_digest(raw)


def _load_json(path: Path) -> object:
    return _load_json_with_digest(path)[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    digest_parser = commands.add_parser("digest", help="print the canonical floor digest")
    digest_parser.add_argument("snapshot", type=Path)
    validate_parser = commands.add_parser("validate", help="validate one snapshot transition")
    validate_parser.add_argument("previous", type=Path)
    validate_parser.add_argument("current", type=Path)
    args = parser.parse_args(argv)

    if args.command == "digest":
        try:
            snapshot = _load_json(args.snapshot)
            if not isinstance(snapshot, dict):
                raise ValueError("snapshot must be a JSON object")
            if not _json_depth_within(snapshot):
                raise ValueError(f"snapshot exceeds {MAX_JSON_DEPTH} nested containers")
            print(floor_digest(snapshot))
            return 0
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            RecursionError,
            ValueError,
        ) as exc:
            errors = [_error("INPUT_ERROR", "input", str(exc))]
            print(json.dumps({"valid": False, "errors": errors}, indent=2, sort_keys=True))
            return 2

    previous_raw: bytes | None = None
    current_raw: bytes | None = None
    try:
        previous_raw = args.previous.read_bytes()
        current_raw = args.current.read_bytes()
    except OSError as exc:
        errors = [_error("INPUT_ERROR", "input", str(exc))]
        receipt = {
            "receiptSchemaVersion": 1,
            "valid": False,
            "previousSnapshotDigest": (
                _raw_digest(previous_raw) if previous_raw is not None else None
            ),
            "currentSnapshotDigest": (
                _raw_digest(current_raw) if current_raw is not None else None
            ),
            "errors": errors,
        }
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 2

    assert previous_raw is not None and current_raw is not None
    previous_snapshot_digest = _raw_digest(previous_raw)
    current_snapshot_digest = _raw_digest(current_raw)
    try:
        previous = _parse_json(previous_raw)
        current = _parse_json(current_raw)
        if not _json_depth_within(previous) or not _json_depth_within(current):
            raise ValueError(
                f"snapshot exceeds {MAX_JSON_DEPTH} nested containers or contains a cycle"
            )
        errors = validate_transition(previous, current)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        ValueError,
    ) as exc:
        errors = [_error("INPUT_ERROR", "input", str(exc))]
        receipt = {
            "receiptSchemaVersion": 1,
            "valid": False,
            "previousSnapshotDigest": previous_snapshot_digest,
            "currentSnapshotDigest": current_snapshot_digest,
            "errors": errors,
        }
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 2
    receipt = {
        "receiptSchemaVersion": 1,
        "valid": not errors,
        "previousSnapshotDigest": previous_snapshot_digest,
        "currentSnapshotDigest": current_snapshot_digest,
        "errors": errors,
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

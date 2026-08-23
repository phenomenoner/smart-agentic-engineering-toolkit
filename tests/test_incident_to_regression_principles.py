from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "skills"
    / "incident-to-regression"
    / "scripts"
    / "validate_incident_record.py"
)


def load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("incident_record_validator", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


def current_state_verified_record() -> dict[str, object]:
    record = VALIDATOR.template()
    record["blastRadius"]["class"] = "cross-cutting"
    record["failFirstArtifact"].update(
        status="not-reproduced",
        unavailabilityReason="The pre-repair state is unavailable and destructive to reconstruct.",
    )
    record["repairPattern"]["applied"] = True
    record["verification"].update(
        requiredTier="T2",
        achievedTier="T2",
        evidenceIds=["EV-CURRENT"],
        currentStateDiscriminator={
            "command": "run focused deterministic seam check",
            "regressionCondition": "The repaired invariant fails when the guard is removed.",
            "observedResult": "The focused seam check passed for the repaired bytes.",
            "evidenceId": "EV-CURRENT",
            "limitation": "No pre-repair execution is available.",
        },
    )
    record["replayFixture"]["provenance"]["sourceSha256"] = "1" * 64
    record["evidencePointers"] = [
        {
            "id": "EV-CURRENT",
            "kind": "current-state-discriminator",
            "purpose": "Focused repaired-path evidence",
            "pointer": "evidence://incident/current-state",
            "sha256": "2" * 64,
            "redacted": True,
        }
    ]
    record["blockingGaps"] = []
    record["limitations"] = ["No pre-repair execution is available."]
    record["status"] = "repair-verified"
    return record


def test_repair_verified_accepts_hash_bound_current_state_discriminator() -> None:
    record = current_state_verified_record()

    assert VALIDATOR.validate(record) == []


def test_repair_verified_rejects_missing_prechange_and_current_state_basis() -> None:
    record = current_state_verified_record()
    record["verification"]["currentStateDiscriminator"] = None

    errors = VALIDATOR.validate(record)

    assert any("current-state discriminator" in error for error in errors)


def test_cross_cutting_label_does_not_force_t3() -> None:
    record = VALIDATOR.template()
    record["blastRadius"]["class"] = "cross-cutting"
    record["verification"]["requiredTier"] = "T1"

    assert not any("requires at least T3" in error for error in VALIDATOR.validate(record))


def test_live_external_claim_still_requires_t4() -> None:
    record = VALIDATOR.template()
    record["blastRadius"]["class"] = "live-external"
    record["verification"]["requiredTier"] = "T3"

    assert "live-external claim requires T4" in VALIDATOR.validate(record)

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.install_toolkit import Installer, validate_install_receipt

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validator(name: str) -> Draft202012Validator:
    schema = load_json(SCHEMAS / name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_catalog_and_profiles_match_their_public_schemas() -> None:
    validator("catalog.schema.json").validate(load_json(ROOT / "catalog" / "skills.json"))
    profile_validator = validator("profile.schema.json")
    for path in sorted((ROOT / "profiles").glob("*.json")):
        profile_validator.validate(load_json(path))


def test_install_receipt_schema_accepts_exact_tree_evidence() -> None:
    files: list[dict[str, object]] = []
    digest = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    receipt = {
        "schemaVersion": 1,
        "toolkitVersion": "0.3.0",
        "sourceCommit": None,
        "sourceRoot": "source",
        "targetRoot": "target",
        "profile": "core",
        "skills": {
            "engineering-specification": {
                "profile": "core",
                "sourceTreeSha256": digest,
                "installedTreeSha256": digest,
                "files": files,
            }
        },
        "transaction": {
            "id": "transaction",
            "completedAt": "2026-08-15T00:00:00+00:00",
            "backupDirectory": "backup",
            "previousReceipt": None,
            "changed": ["engineering-specification"],
        },
    }

    validator("install-receipt.schema.json").validate(receipt)
    assert validate_install_receipt(receipt) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sha256", "not-a-sha256"),
        ("length", -1),
        ("length", True),
    ],
)
def test_install_receipt_semantics_reject_malformed_file_evidence(
    field: str, value: object
) -> None:
    body = b"skill bytes"
    files: list[dict[str, object]] = [
        {
            "path": "SKILL.md",
            "length": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
    ]
    digest = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    receipt = {
        "schemaVersion": 1,
        "toolkitVersion": "0.3.0",
        "sourceCommit": None,
        "sourceRoot": "source",
        "targetRoot": "target",
        "profile": "core",
        "skills": {
            "engineering-specification": {
                "profile": "core",
                "sourceTreeSha256": digest,
                "installedTreeSha256": digest,
                "files": files,
            }
        },
        "transaction": {
            "id": "transaction",
            "completedAt": "2026-08-15T00:00:00+00:00",
            "backupDirectory": "backup",
            "previousReceipt": None,
            "changed": ["engineering-specification"],
        },
    }
    receipt["skills"]["engineering-specification"]["files"][0][field] = value

    assert "INSTALL_RECEIPT_SHAPE" in {error["code"] for error in validate_install_receipt(receipt)}


def test_real_installer_receipt_matches_public_schema(tmp_path: Path) -> None:
    source = tmp_path / "source"
    skill = source / "skills" / "alpha-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: alpha-skill\ndescription: Test.\n---\n",
        encoding="utf-8",
    )
    profiles = source / "profiles"
    profiles.mkdir()
    (profiles / "core.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "toolkitVersion": "0.3.0",
                "name": "core",
                "skills": ["alpha-skill"],
            }
        ),
        encoding="utf-8",
    )

    receipt = Installer(source, tmp_path / "target").install("core")
    validator("install-receipt.schema.json").validate(receipt)
    assert validate_install_receipt(receipt) == []


def test_improvement_proposal_schema_preserves_pr_authority_boundary() -> None:
    proposal = {
        "schemaVersion": 1,
        "canonicalRepository": "https://github.com/example/toolkit",
        "baseCommit": "b" * 40,
        "skill": {
            "name": "engineering-specification",
            "toolkitVersion": "0.3.0",
            "sha256": "c" * 64,
        },
        "host": {"name": "Codex"},
        "reproducer": "Run the bounded activation case.",
        "expected": "The skill selects the specification workflow.",
        "observed": "The skill did not select it.",
        "materiality": "The missed trigger permits implementation before the contract is stable.",
        "patch": "Exact unified diff goes here.",
        "eval": {"case": "SPEC-ACTIVATION-01"},
        "provenance": {"redacted": True},
        "authorization": {
            "githubWritesAuthorized": False,
            "remoteAction": "NOT_PERFORMED",
            "remoteUrl": None,
        },
    }

    validator("improvement-proposal.schema.json").validate(proposal)


def test_behavior_eval_schema_requires_explicit_execution_status() -> None:
    result = {
        "schemaVersion": 1,
        "toolkitVersion": "0.3.0",
        "candidate": {
            "commit": "d" * 40,
            "tree": "e" * 40,
            "pluginVersion": "0.3.0",
            "catalogSha256": "f" * 64,
        },
        "environment": {
            "host": "Codex",
            "hostVersion": "example",
            "taskIsolation": "fresh task",
            "reviewer": {"model": "example"},
        },
        "caseCorpusSha256": "0" * 64,
        "results": [
            {
                "id": "ACT-SPEC-01",
                "status": "NOT_RUN",
                "selected": [],
                "notSelected": [],
                "observable": "Effect-bearing evaluation was not authorized.",
                "prohibitedEffectsObserved": False,
                "evidence": {"kind": "NONE", "pointer": None, "sha256": None},
            }
        ],
        "summary": {"pass": 0, "fail": 0, "notRun": 1, "verdict": "INCOMPLETE"},
    }

    validator("eval-result.schema.json").validate(result)

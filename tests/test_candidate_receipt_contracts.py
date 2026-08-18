from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from scripts import install_toolkit, validate_toolkit
from scripts.install_toolkit import InstallContainmentError, Installer, tree_digest, tree_files

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_validator(name: str) -> Draft202012Validator:
    schema = load_json(ROOT / "schemas" / name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _canonical_behavior_result(root: Path = ROOT) -> dict[str, Any]:
    corpus_path = root / "evals" / "cases" / "acceptance.json"
    corpus = load_json(corpus_path)
    plugin = load_json(root / ".codex-plugin" / "plugin.json")
    manifest = load_json(root / "manifest" / "toolkit.json")
    return {
        "schemaVersion": 1,
        "toolkitVersion": manifest["toolkitVersion"],
        "candidate": {
            "commit": _git(root, "rev-parse", "HEAD") if (root / ".git").exists() else "b" * 40,
            "tree": _git(root, "rev-parse", "HEAD^{tree}")
            if (root / ".git").exists()
            else "c" * 40,
            "pluginVersion": plugin["version"],
            "catalogSha256": hashlib.sha256(
                (root / "catalog" / "skills.json").read_bytes()
            ).hexdigest(),
        },
        "environment": {
            "host": "Codex",
            "hostVersion": "test",
            "taskIsolation": "fresh task",
            "reviewer": {"model": "test"},
        },
        "caseCorpusSha256": hashlib.sha256(corpus_path.read_bytes()).hexdigest(),
        "results": [
            {
                "id": case["id"],
                "status": "PASS",
                "selected": case["expectedSelected"],
                "notSelected": case["expectedNotSelected"],
                "observable": case["observablePass"],
                "prohibitedEffectsObserved": False,
                "evidence": {
                    "kind": "RECEIPT",
                    "pointer": f"redacted-evidence/{case['id']}.json",
                    "sha256": "a" * 64,
                },
            }
            for case in corpus["cases"]
        ],
        "summary": {
            "pass": len(corpus["cases"]),
            "fail": 0,
            "notRun": 0,
            "verdict": "PASS",
        },
    }


def behavior_error_codes(result: dict[str, Any], root: Path = ROOT) -> set[str]:
    validator = getattr(validate_toolkit, "validate_behavior_result", None)
    assert callable(validator), "EVAL_RESULT_SEMANTIC_VALIDATOR_MISSING"
    errors = validator(root, result)
    assert isinstance(errors, list)
    return {str(error.get("code")) if isinstance(error, dict) else str(error) for error in errors}


def write_source(root: Path, contents: dict[str, str], *, version: str = "0.3.0") -> None:
    for name, body in contents.items():
        skill = root / "skills" / name
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill {name}.\n---\n\n{body}\n",
            encoding="utf-8",
        )
    profiles = root / "profiles"
    profiles.mkdir(parents=True, exist_ok=True)
    (profiles / "core.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "name": "core",
                "toolkitVersion": version,
                "skills": sorted(contents),
            }
        ),
        encoding="utf-8",
    )


def init_git_source(root: Path) -> None:
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    _git(root, "add", ".")
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Toolkit Test",
            "-c",
            "user.email=toolkit-test@example.invalid",
            "commit",
            "-qm",
            "v1",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _manifest_digest(files: list[dict[str, Any]]) -> str:
    payload = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _base_receipt() -> dict[str, Any]:
    body = b"test\n"
    files = [{"path": "SKILL.md", "length": len(body), "sha256": hashlib.sha256(body).hexdigest()}]
    digest = _manifest_digest(files)
    return {
        "schemaVersion": 1,
        "toolkitVersion": "0.3.0",
        "sourceCommit": None,
        "sourceRoot": "source",
        "targetRoot": "target",
        "profile": "core",
        "skills": {
            "alpha-skill": {
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
            "changed": ["alpha-skill"],
        },
    }


def _set_manifest_digest(receipt: dict[str, Any]) -> None:
    row = receipt["skills"]["alpha-skill"]
    digest = _manifest_digest(row["files"])
    row["sourceTreeSha256"] = digest
    row["installedTreeSha256"] = digest


def receipt_semantic_error_codes(receipt: dict[str, Any]) -> set[str]:
    validator = getattr(install_toolkit, "validate_install_receipt", None)
    if not callable(validator):
        validator = getattr(validate_toolkit, "validate_install_receipt", None)
    assert callable(validator), "INSTALL_RECEIPT_SEMANTIC_VALIDATOR_MISSING"
    errors = validator(receipt)
    assert isinstance(errors, list)
    return {str(error.get("code")) if isinstance(error, dict) else str(error) for error in errors}


def test_behavior_result_rejects_wrong_candidate_commit() -> None:
    result = _canonical_behavior_result()
    result["candidate"]["commit"] = "b" * 40
    assert "EVAL_RESULT_CANDIDATE_COMMIT" in behavior_error_codes(result)


def test_behavior_result_rejects_wrong_candidate_tree() -> None:
    result = _canonical_behavior_result()
    result["candidate"]["tree"] = "c" * 40
    assert "EVAL_RESULT_CANDIDATE_TREE" in behavior_error_codes(result)


def test_behavior_result_rejects_wrong_catalog_digest() -> None:
    result = _canonical_behavior_result()
    result["candidate"]["catalogSha256"] = "d" * 64
    assert "EVAL_RESULT_CANDIDATE_CATALOG_HASH" in behavior_error_codes(result)


@pytest.mark.parametrize(
    ("field", "expected_code"),
    [
        ("toolkitVersion", "EVAL_RESULT_TOOLKIT_VERSION"),
        ("candidate.pluginVersion", "EVAL_RESULT_PLUGIN_VERSION"),
    ],
)
def test_behavior_result_rejects_wrong_toolkit_and_plugin_versions(
    field: str, expected_code: str
) -> None:
    result = _canonical_behavior_result()
    if field == "toolkitVersion":
        result["toolkitVersion"] = "9.9.9"
    else:
        result["candidate"]["pluginVersion"] = "9.9.9"
    assert expected_code in behavior_error_codes(result)


def test_behavior_result_fails_closed_when_git_candidate_is_unverifiable(
    tmp_path: Path,
) -> None:
    isolated = tmp_path / "non-git-root"
    for relative in (
        ".codex-plugin",
        "catalog",
        "evals",
        "manifest",
    ):
        source = ROOT / relative
        destination = isolated / relative
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    result = _canonical_behavior_result(isolated)
    assert "EVAL_RESULT_CANDIDATE_UNVERIFIABLE" in behavior_error_codes(result, isolated)


def test_post_commit_target_drift_cannot_return_upgrade_success(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    write_source(source, {"alpha-skill": "v1"})
    Installer(source, target).install("core")
    previous_receipt = (target / install_toolkit.RECEIPT_NAME).read_bytes()
    write_source(source, {"alpha-skill": "v2"}, version="0.1.1")

    def drift(phase: str, _name: str | None, _installer: Installer) -> None:
        if phase == "after_receipt_commit":
            (target / "alpha-skill" / "FOREIGN.txt").write_text("foreign bytes", encoding="utf-8")

    with pytest.raises(InstallContainmentError):
        Installer(source, target, fault_hook=drift).install("core")
    assert (target / "alpha-skill" / "FOREIGN.txt").read_text(encoding="utf-8") == ("foreign bytes")
    assert (target / install_toolkit.RECEIPT_NAME).read_bytes() == previous_receipt


def test_post_commit_target_drift_cannot_leave_success_receipt_for_add(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    write_source(source, {"alpha-skill": "v1"})

    def drift(phase: str, _name: str | None, _installer: Installer) -> None:
        if phase == "after_receipt_commit":
            (target / "alpha-skill" / "FOREIGN.txt").write_text("foreign bytes", encoding="utf-8")

    with pytest.raises(InstallContainmentError):
        Installer(source, target, fault_hook=drift).install("core")
    assert (target / "alpha-skill" / "FOREIGN.txt").read_text(encoding="utf-8") == ("foreign bytes")
    receipt_path = target / install_toolkit.RECEIPT_NAME
    if receipt_path.exists():
        assert plan_classification(Installer(source, target), "alpha-skill") != "EXACT"


def test_post_commit_compensation_never_overwrites_foreign_receipt(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    write_source(source, {"alpha-skill": "v1"})
    Installer(source, target).install("core")
    write_source(source, {"alpha-skill": "v2"}, version="0.1.1")
    receipt_path = target / install_toolkit.RECEIPT_NAME
    foreign_receipt = b'{"foreign":true}\n'

    def race(phase: str, _name: str | None, _installer: Installer) -> None:
        if phase == "after_receipt_commit":
            (target / "alpha-skill" / "FOREIGN.txt").write_text("foreign bytes", encoding="utf-8")
            receipt_path.write_bytes(foreign_receipt)

    with pytest.raises(InstallContainmentError):
        Installer(source, target, fault_hook=race).install("core")
    assert receipt_path.read_bytes() == foreign_receipt


def plan_classification(installer: Installer, name: str) -> str:
    rows = {item.name: item.classification for item in installer.plan("core")}
    return rows[name]


def test_clean_git_install_does_not_claim_commit_attestation(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    write_source(source, {"alpha-skill": "v1"})
    init_git_source(source)

    receipt = Installer(source, target).install("core")
    assert "sourceCommit" not in receipt or receipt["sourceCommit"] is None
    row = receipt["skills"]["alpha-skill"]
    assert row["sourceTreeSha256"] == tree_digest(target / "alpha-skill")
    assert row["installedTreeSha256"] == tree_digest(target / "alpha-skill")
    assert row["files"] == tree_files(target / "alpha-skill")


def test_dirty_git_install_does_not_claim_head_for_dirty_bytes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    write_source(source, {"alpha-skill": "v1"})
    init_git_source(source)
    write_source(source, {"alpha-skill": "v2"}, version="0.1.1")

    receipt = Installer(source, target).install("core")
    assert "sourceCommit" not in receipt or receipt["sourceCommit"] is None
    row = receipt["skills"]["alpha-skill"]
    assert row["sourceTreeSha256"] == tree_digest(target / "alpha-skill")
    assert row["installedTreeSha256"] == tree_digest(target / "alpha-skill")
    assert row["files"] == tree_files(target / "alpha-skill")


def test_install_receipt_production_does_not_query_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    write_source(source, {"alpha-skill": "v1"})

    def forbidden(_root: Path) -> str | None:
        raise AssertionError("installer must not query Git to produce a receipt")

    monkeypatch.setattr(install_toolkit, "_git_head", forbidden, raising=False)
    receipt = Installer(source, target).install("core")
    assert "sourceCommit" not in receipt or receipt["sourceCommit"] is None
    assert receipt["skills"]["alpha-skill"]["files"] == tree_files(target / "alpha-skill")


@pytest.mark.parametrize(
    ("location", "unknown_field"),
    [
        ("root", "authority"),
        ("skill", "authority"),
        ("file", "authority"),
        ("transaction", "authority"),
    ],
)
def test_receipt_schema_rejects_unknown_authority_fields_at_every_level(
    location: str, unknown_field: str
) -> None:
    receipt = _base_receipt()
    if location == "root":
        receipt[unknown_field] = True
    elif location == "skill":
        receipt["skills"]["alpha-skill"][unknown_field] = True
    elif location == "file":
        receipt["skills"]["alpha-skill"]["files"][0][unknown_field] = True
    else:
        receipt["transaction"][unknown_field] = True
    with pytest.raises(ValidationError):
        schema_validator("install-receipt.schema.json").validate(receipt)


@pytest.mark.parametrize("completed_at", ["not-a-time", "2026-08-15T00:00:00"])
def test_receipt_semantics_reject_invalid_or_timezone_free_completed_at(
    completed_at: str,
) -> None:
    receipt = _base_receipt()
    receipt["transaction"]["completedAt"] = completed_at
    assert "INSTALL_RECEIPT_COMPLETED_AT" in receipt_semantic_error_codes(receipt)


def test_receipt_semantics_rejects_unequal_successful_tree_digests() -> None:
    receipt = _base_receipt()
    receipt["skills"]["alpha-skill"]["installedTreeSha256"] = "b" * 64
    assert "INSTALL_RECEIPT_TREE_RELATION" in receipt_semantic_error_codes(receipt)


def test_receipt_semantics_recomputes_tree_digest_from_files() -> None:
    receipt = _base_receipt()
    receipt["skills"]["alpha-skill"]["sourceTreeSha256"] = "c" * 64
    receipt["skills"]["alpha-skill"]["installedTreeSha256"] = "c" * 64
    assert "INSTALL_RECEIPT_MANIFEST_DIGEST" in receipt_semantic_error_codes(receipt)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("absolute", "INSTALL_RECEIPT_MANIFEST_PATH"),
        ("parent", "INSTALL_RECEIPT_MANIFEST_PATH"),
        ("backslash", "INSTALL_RECEIPT_MANIFEST_PATH"),
        ("duplicate", "INSTALL_RECEIPT_MANIFEST_DUPLICATE"),
        ("unsorted", "INSTALL_RECEIPT_MANIFEST_ORDER"),
    ],
)
def test_receipt_semantics_rejects_unsafe_or_duplicate_manifest_paths(
    mutation: str, expected_code: str
) -> None:
    receipt = _base_receipt()
    files = receipt["skills"]["alpha-skill"]["files"]
    if mutation == "absolute":
        files[0]["path"] = "/absolute.txt"
    elif mutation == "parent":
        files[0]["path"] = "../outside.txt"
    elif mutation == "backslash":
        files[0]["path"] = "nested\\file.txt"
    elif mutation == "duplicate":
        files.append(copy.deepcopy(files[0]))
    else:
        files[:] = [
            {"path": "B.txt", "length": 1, "sha256": "b" * 64},
            {"path": "A.txt", "length": 1, "sha256": "a" * 64},
        ]
    _set_manifest_digest(receipt)
    assert expected_code in receipt_semantic_error_codes(receipt)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("unknown", "INSTALL_RECEIPT_TRANSACTION_RELATION"),
        ("profile", "INSTALL_RECEIPT_TRANSACTION_RELATION"),
    ],
)
def test_receipt_semantics_rejects_unknown_changed_skill_or_profile_mismatch(
    mutation: str, expected_code: str
) -> None:
    receipt = _base_receipt()
    if mutation == "unknown":
        receipt["transaction"]["changed"] = ["missing-skill"]
    else:
        receipt["skills"]["alpha-skill"]["profile"] = "other"
    assert expected_code in receipt_semantic_error_codes(receipt)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sourceCommit", "a" * 40),
        ("sourceCommitVerified", True),
        ("releaseTag", "v0.3.0"),
    ],
)
def test_receipt_rejects_non_null_or_unmodeled_release_authority(field: str, value: object) -> None:
    receipt = _base_receipt()
    receipt[field] = value
    try:
        schema_validator("install-receipt.schema.json").validate(receipt)
    except ValidationError:
        return
    assert receipt_semantic_error_codes(receipt)


def test_engineering_specification_requires_conditional_mechanism_necessity_review() -> None:
    text = (
        (ROOT / "skills" / "engineering-specification" / "SKILL.md")
        .read_text(encoding="utf-8")
        .lower()
    )
    required_fragments = (
        "conditional",
        "observable outcome",
        "proxy",
        "deletion",
        "manual",
        "platform primitive",
        "ephemeral",
        "persistent",
        "complexity budget",
        "restart survival",
    )
    missing = [fragment for fragment in required_fragments if fragment not in text]
    assert not missing, f"mechanism-necessity gate is missing: {missing}"
    assert "durable state" in text or "durable-state" in text
    assert "already explicit" in text and "direct" in text


def test_acceptance_corpus_has_mechanism_necessity_case() -> None:
    corpus = load_json(ROOT / "evals" / "cases" / "acceptance.json")
    matches = [case for case in corpus["cases"] if case.get("id") == "ACT-SPEC-MECH-01"]
    assert len(matches) == 1
    case = matches[0]
    assert "engineering-specification" in case["expectedSelected"]
    serialized = json.dumps(case, ensure_ascii=False).lower()
    for fragment in ("durable", "ledger", "compare", "state"):
        assert fragment in serialized


def test_general_ownership_spec_does_not_select_temporal_assurance() -> None:
    text = (
        (ROOT / "skills" / "specify-temporal-ownership" / "SKILL.md")
        .read_text(encoding="utf-8")
        .lower()
    )
    for fragment in (
        "do not select merely because",
        "general specification mentions ownership",
        "post-observation destructive effect",
    ):
        assert fragment in text

    corpus = load_json(ROOT / "evals" / "cases" / "acceptance.json")
    matches = [case for case in corpus["cases"] if case.get("id") == "NON-TEMPORAL-01"]
    assert len(matches) == 1
    assert "engineering-specification" in matches[0]["expectedSelected"]
    assert "specify-temporal-ownership" in matches[0]["expectedNotSelected"]
    serialized = json.dumps(matches[0], ensure_ascii=False).lower()
    for fragment in ("documentation", "runtime mutation", "concurrency", "no temporal model"):
        assert fragment in serialized

from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from scripts import install_toolkit, validate_toolkit
from scripts.install_toolkit import Installer, tree_digest, tree_files

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_validator(name: str) -> Draft202012Validator:
    schema = load_json(ROOT / "schemas" / name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def write_source(root: Path, body: str, *, version: str) -> None:
    skill = root / "skills" / "alpha-skill"
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: alpha-skill\ndescription: Test skill.\n---\n\n{body}\n",
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
                "skills": ["alpha-skill"],
            }
        ),
        encoding="utf-8",
    )


def rewrite_source_after_plan(root: Path, body: str, *, version: str) -> None:
    (root / "skills" / "alpha-skill" / "SKILL.md").write_text(
        f"---\nname: alpha-skill\ndescription: Test skill.\n---\n\n{body}\n",
        encoding="utf-8",
    )
    profile_path = root / "profiles" / "core.json"
    profile = load_json(profile_path)
    profile["toolkitVersion"] = version
    profile_path.write_text(json.dumps(profile), encoding="utf-8")


def canonical_behavior_result(root: Path = ROOT) -> dict[str, Any]:
    corpus_path = root / "evals" / "cases" / "acceptance.json"
    corpus = load_json(corpus_path)
    plugin = load_json(root / ".codex-plugin" / "plugin.json")
    manifest = load_json(root / "manifest" / "toolkit.json")
    commit = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD^{tree}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    results = [
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
    ]
    return {
        "schemaVersion": 1,
        "toolkitVersion": manifest["toolkitVersion"],
        "candidate": {
            "commit": commit,
            "tree": tree,
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
        "results": results,
        "summary": {
            "pass": len(results),
            "fail": 0,
            "notRun": 0,
            "verdict": "PASS",
        },
    }


def initialized_candidate_copy(tmp_path: Path) -> Path:
    isolated = tmp_path / "candidate"
    for relative in (".codex-plugin", "catalog", "evals", "manifest"):
        shutil.copytree(ROOT / relative, isolated / relative)
    shutil.copy2(ROOT / ".gitignore", isolated / ".gitignore")
    subprocess.run(["git", "init", "-q", str(isolated)], check=True)
    subprocess.run(["git", "-C", str(isolated), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(isolated),
            "-c",
            "user.name=Toolkit Test",
            "-c",
            "user.email=toolkit-test@example.invalid",
            "commit",
            "-qm",
            "candidate",
        ],
        check=True,
    )
    return isolated


def behavior_error_codes(result: dict[str, Any], root: Path = ROOT) -> set[str]:
    validator = getattr(validate_toolkit, "validate_behavior_result", None)
    assert callable(validator), (
        "EVAL_RESULT_SEMANTIC_VALIDATOR_MISSING: add "
        "validate_behavior_result(root, result) to scripts.validate_toolkit"
    )
    errors = validator(root, result)
    assert isinstance(errors, list)
    return {str(error.get("code")) if isinstance(error, dict) else str(error) for error in errors}


def proposal() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "canonicalRepository": "https://github.com/example/toolkit",
        "baseCommit": "b" * 40,
        "skill": {
            "name": "engineering-specification",
            "toolkitVersion": "0.4.0",
            "sha256": "c" * 64,
        },
        "host": {"name": "Codex"},
        "reproducer": "Run the bounded activation case.",
        "expected": "The skill selects the specification workflow.",
        "observed": "The skill did not select it.",
        "materiality": "The missed trigger changes the selected workflow.",
        "patch": "Exact unified diff.",
        "eval": {"case": "SPEC-ACTIVATION-01"},
        "provenance": {"redacted": True},
        "authorization": {
            "githubWritesAuthorized": False,
            "remoteAction": "NOT_PERFORMED",
            "remoteUrl": None,
        },
    }


def test_behavior_result_rejects_a_tracked_dirty_candidate(tmp_path: Path) -> None:
    isolated = initialized_candidate_copy(tmp_path)
    result = canonical_behavior_result(isolated)
    catalog_path = isolated / "catalog" / "skills.json"
    catalog_path.write_bytes(catalog_path.read_bytes() + b"\n")

    errors = validate_toolkit.validate_behavior_result(isolated, result)

    assert "EVAL_RESULT_CANDIDATE_UNVERIFIABLE" in {error["code"] for error in errors}


def test_behavior_result_rejects_an_untracked_public_candidate(tmp_path: Path) -> None:
    isolated = initialized_candidate_copy(tmp_path)
    result = canonical_behavior_result(isolated)
    skill = isolated / "skills" / "untracked-public-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: untracked-public-skill\ndescription: Untracked public source.\n---\n",
        encoding="utf-8",
    )

    errors = validate_toolkit.validate_behavior_result(isolated, result)

    assert "EVAL_RESULT_CANDIDATE_UNVERIFIABLE" in {error["code"] for error in errors}


def test_behavior_result_allows_gitignored_local_cache(tmp_path: Path) -> None:
    isolated = initialized_candidate_copy(tmp_path)
    result = canonical_behavior_result(isolated)
    cache = isolated / ".pytest_cache" / "v" / "cache" / "nodeids"
    cache.parent.mkdir(parents=True)
    cache.write_text("[]", encoding="utf-8")

    assert validate_toolkit.validate_behavior_result(isolated, result) == []


@pytest.mark.parametrize(
    ("changed_read", "relative"),
    [
        ("commit", None),
        ("tree", None),
        ("status", None),
        ("catalog", "catalog/skills.json"),
        ("toolkit", "manifest/toolkit.json"),
        ("plugin", ".codex-plugin/plugin.json"),
    ],
)
def test_candidate_identity_fails_closed_when_readback_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    changed_read: str,
    relative: str | None,
) -> None:
    isolated = initialized_candidate_copy(tmp_path)
    result = canonical_behavior_result(isolated)

    if relative is None:
        original_git_read = validate_toolkit._git_read
        call_count = 0

        def unstable_git_read(root: Path, *arguments: str) -> str:
            nonlocal call_count
            value = original_git_read(root, *arguments)
            matches = (
                changed_read == "commit"
                and arguments == ("rev-parse", "--verify", "HEAD")
                or changed_read == "tree"
                and arguments == ("rev-parse", "--verify", "HEAD^{tree}")
                or changed_read == "status"
                and arguments[:2] == ("status", "--porcelain=v1")
            )
            if matches:
                call_count += 1
                if call_count == 2:
                    return "0" * 40 if changed_read != "status" else "?? skills/late/SKILL.md"
            return value

        monkeypatch.setattr(validate_toolkit, "_git_read", unstable_git_read)
    else:
        target = (isolated / relative).resolve()
        original_read_bytes = Path.read_bytes
        call_count = 0

        def unstable_read_bytes(path: Path) -> bytes:
            nonlocal call_count
            data = original_read_bytes(path)
            if path.resolve() == target:
                call_count += 1
                if call_count == 2:
                    return data + b" "
            return data

        monkeypatch.setattr(Path, "read_bytes", unstable_read_bytes)

    errors = validate_toolkit.validate_behavior_result(isolated, result)

    assert "EVAL_RESULT_CANDIDATE_UNVERIFIABLE" in {error["code"] for error in errors}


def test_f001_complete_consistent_behavior_result_is_accepted(tmp_path: Path) -> None:
    isolated = initialized_candidate_copy(tmp_path)

    assert behavior_error_codes(canonical_behavior_result(isolated), isolated) == set()


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("missing", "EVAL_RESULT_CASE_SET"),
        ("duplicate", "EVAL_RESULT_CASE_DUPLICATE"),
        ("unknown", "EVAL_RESULT_CASE_SET"),
        ("corpus-hash", "EVAL_RESULT_CORPUS_HASH"),
        ("selection", "EVAL_RESULT_SELECTION"),
        ("pass-prohibited-effect", "EVAL_RESULT_PASS_PROHIBITED_EFFECT"),
        ("pass-no-evidence", "EVAL_RESULT_PASS_EVIDENCE"),
        ("summary", "EVAL_RESULT_SUMMARY"),
        ("verdict", "EVAL_RESULT_VERDICT"),
    ],
)
def test_f001_behavior_result_rejects_pass_laundering(mutation: str, expected_code: str) -> None:
    result = canonical_behavior_result()
    if mutation == "missing":
        result["results"].pop()
        result["summary"]["pass"] -= 1
    elif mutation == "duplicate":
        result["results"].append(copy.deepcopy(result["results"][0]))
        result["summary"]["pass"] += 1
    elif mutation == "unknown":
        result["results"][0]["id"] = "UNKNOWN-CASE"
    elif mutation == "corpus-hash":
        result["caseCorpusSha256"] = "0" * 64
    elif mutation == "selection":
        result["results"][0]["selected"] = ["wrong-skill"]
    elif mutation == "pass-prohibited-effect":
        result["results"][0]["prohibitedEffectsObserved"] = True
    elif mutation == "pass-no-evidence":
        result["results"][0]["evidence"] = {
            "kind": "NONE",
            "pointer": None,
            "sha256": None,
        }
    elif mutation == "summary":
        result["summary"]["pass"] = 0
    elif mutation == "verdict":
        result["results"][0]["status"] = "NOT_RUN"
        result["summary"] = {
            "pass": len(result["results"]) - 1,
            "fail": 0,
            "notRun": 1,
            "verdict": "PASS",
        }
    else:  # pragma: no cover - parametrization is closed above
        raise AssertionError(mutation)

    assert expected_code in behavior_error_codes(result)


def test_f002_clean_add_receipt_uses_one_fenced_source_generation(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    write_source(source, "planned-v1", version="0.4.0")

    def mutate(phase: str, _name: str | None, _installer: Installer) -> None:
        if phase == "before_publish":
            rewrite_source_after_plan(source, "late-v2", version="9.9.9")

    try:
        receipt = Installer(source, target, fault_hook=mutate).install("core")
    except RuntimeError:
        assert not (target / "alpha-skill").exists()
    else:
        installed = target / "alpha-skill"
        row = receipt["skills"]["alpha-skill"]
        assert receipt["toolkitVersion"] == "0.4.0"
        assert row["sourceTreeSha256"] == tree_digest(installed)
        assert row["installedTreeSha256"] == tree_digest(installed)
        assert row["files"] == tree_files(installed)


def test_f002_managed_upgrade_receipt_uses_one_fenced_source_generation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    write_source(source, "installed-v1", version="0.4.0")
    Installer(source, target).install("core")
    old_hash = tree_digest(target / "alpha-skill")
    receipt_path = target / install_toolkit.RECEIPT_NAME
    old_receipt = receipt_path.read_bytes()
    write_source(source, "planned-v2", version="0.1.1")

    def mutate(phase: str, _name: str | None, _installer: Installer) -> None:
        if phase == "before_publish":
            rewrite_source_after_plan(source, "late-v3", version="9.9.9")

    try:
        receipt = Installer(source, target, fault_hook=mutate).install("core")
    except RuntimeError:
        assert tree_digest(target / "alpha-skill") == old_hash
        assert receipt_path.read_bytes() == old_receipt
    else:
        installed = target / "alpha-skill"
        row = receipt["skills"]["alpha-skill"]
        assert receipt["toolkitVersion"] == "0.1.1"
        assert row["sourceTreeSha256"] == tree_digest(installed)
        assert row["installedTreeSha256"] == tree_digest(installed)
        assert row["files"] == tree_files(installed)


def test_f003_unauthorized_draft_pr_claim_is_schema_invalid() -> None:
    document = proposal()
    document["authorization"] = {
        "githubWritesAuthorized": False,
        "remoteAction": "DRAFT_PR_OPENED",
        "remoteUrl": "https://github.com/example/toolkit/pull/1",
    }

    with pytest.raises(ValidationError):
        schema_validator("improvement-proposal.schema.json").validate(document)


def test_f003_draft_pr_claim_without_remote_readback_is_schema_invalid() -> None:
    document = proposal()
    document["authorization"] = {
        "githubWritesAuthorized": True,
        "remoteAction": "DRAFT_PR_OPENED",
        "remoteUrl": None,
    }

    with pytest.raises(ValidationError):
        schema_validator("improvement-proposal.schema.json").validate(document)


def test_f003_not_performed_claim_cannot_carry_remote_url() -> None:
    document = proposal()
    document["authorization"] = {
        "githubWritesAuthorized": True,
        "remoteAction": "NOT_PERFORMED",
        "remoteUrl": "https://github.com/example/toolkit/pull/1",
    }

    with pytest.raises(ValidationError):
        schema_validator("improvement-proposal.schema.json").validate(document)


def test_f004_public_lifecycle_status_is_consistent_and_self_explaining() -> None:
    catalog = load_json(ROOT / "catalog" / "skills.json")
    cases = load_json(ROOT / "evals" / "cases" / "acceptance.json")
    manifest = load_json(ROOT / "manifest" / "toolkit.json")

    assert {catalog["status"], cases["status"], manifest["status"]} == {"released"}


def test_f004_repository_is_current_source_while_tags_identify_releases() -> None:
    provenance = load_json(ROOT / "manifest" / "provenance.json")
    state = provenance["canonicalState"].lower()
    guidance = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()

    assert "canonical writable source" in guidance
    assert "canonical writable source" in state
    assert "becomes writable canonical source" not in state
    assert "verified" in state and "tag" in state and "release" in state


def test_f005_macos_install_claim_requires_macos_ci() -> None:
    installation = (ROOT / "docs" / "installation.md").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    advertises_macos = "On Linux or macOS hosts:" in installation

    assert not advertises_macos or "macos-latest" in workflow


def test_f005_darwin_atomic_noreplace_branch_uses_renamex_np(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[bytes, bytes, int]] = []

    class FakeRename:
        argtypes: list[object]
        restype: object

        def __call__(self, source: bytes, destination: bytes, flags: int) -> int:
            calls.append((source, destination, flags))
            return 0

    class FakeLibc:
        renamex_np = FakeRename()

    source = Path("source")
    destination = Path("destination")
    monkeypatch.setattr(install_toolkit.os, "name", "posix")
    monkeypatch.setattr(install_toolkit.sys, "platform", "darwin")
    monkeypatch.setattr(install_toolkit.ctypes, "CDLL", lambda *_args, **_kwargs: FakeLibc())

    install_toolkit._rename_noreplace(source, destination)

    assert calls == [(b"source", b"destination", 0x00000004)]


def test_f006_receipt_schema_rejects_arbitrary_source_commit() -> None:
    receipt = {
        "schemaVersion": 1,
        "toolkitVersion": "0.4.0",
        "sourceCommit": "not-a-commit",
        "sourceRoot": "source",
        "targetRoot": "target",
        "profile": "core",
        "skills": {},
        "transaction": {
            "id": "transaction",
            "completedAt": "2026-08-15T00:00:00+00:00",
            "backupDirectory": "backup",
            "previousReceipt": None,
            "changed": [],
        },
    }

    with pytest.raises(ValidationError):
        schema_validator("install-receipt.schema.json").validate(receipt)


def test_f006_archive_install_marks_source_commit_unavailable(tmp_path: Path) -> None:
    source = tmp_path / "source"
    write_source(source, "archive", version="0.4.0")

    receipt = Installer(source, tmp_path / "target").install("core")

    assert receipt["sourceCommit"] is None


def test_f006_recovery_docs_do_not_claim_unrecorded_release_tag_binding() -> None:
    migration = (ROOT / "docs" / "migration.md").read_text(encoding="utf-8").lower()

    assert "receipt binds release tag" not in migration
    assert "per-file" in migration and "hash" in migration


def test_first_principles_gate_has_one_owner_and_all_loop_guards() -> None:
    owner_path = ROOT / "skills" / "engineering-specification" / "SKILL.md"
    owner = owner_path.read_text(encoding="utf-8")
    gate = "Run the conditional first-principles necessity and complexity gate"
    contract = "Write the behavioral contract"
    assert gate in owner and contract in owner
    assert owner.index(gate) < owner.index(contract)

    guarded_paths = (
        "skills/engineering-implementation/SKILL.md",
        "skills/engineering-wal/SKILL.md",
        "skills/evolve-engineering-toolkit/SKILL.md",
        "skills/batch-complete-independent-review/SKILL.md",
        "skills/completeness-and-test-synthesis/SKILL.md",
        "skills/incident-to-regression/SKILL.md",
        "skills/specify-temporal-ownership/SKILL.md",
        "skills/canon-engineering-disciplines/SKILL.md",
        "skills/programmatic-tool-composition/SKILL.md",
        "skills/codex-cli-luna-worker/SKILL.md",
        "skills/long-run-supervisor/SKILL.md",
        "skills/codex-app-mcp-update/SKILL.md",
        "skills/claude-independent-review/SKILL.md",
        "skills/codegraph-first-navigation/SKILL.md",
        "workflows/specify-implement-review-drill.md",
        "skills/batch-complete-independent-review/references/protocol.md",
        "skills/specify-temporal-ownership/references/contract-template.md",
        "skills/canon-engineering-disciplines/templates/discipline-synthesis.md",
        "docs/product-specification.md",
        "docs/taxonomy.md",
        "docs/architecture.md",
        "CONTRIBUTING.md",
        "docs/contribution-protocol.md",
        "evals/README.md",
    )
    for relative in guarded_paths:
        text = re.sub(r"\s+", " ", (ROOT / relative).read_text(encoding="utf-8"))
        assert "Do we really need this to make things happen?" in text, relative
        assert "Is there a simpler and more direct way?" in text, relative
        assert "engineering-specification" in text, relative


def test_public_paths_do_not_encode_private_wave_round_or_phase_shorthand() -> None:
    public_paths = [row["path"] for row in validate_toolkit.build_public_lock(ROOT)["files"]]
    private_stage = re.compile(r"(?:^|[/_.-])(?:wave|round|phase)[-_]?\d+", re.IGNORECASE)

    assert [path for path in public_paths if private_stage.search(path)] == []


def test_release_status_and_changelog_heading_are_consistent() -> None:
    statuses = {
        load_json(ROOT / "manifest" / "toolkit.json")["status"],
        load_json(ROOT / "catalog" / "skills.json")["status"],
        load_json(ROOT / "evals" / "cases" / "acceptance.json")["status"],
    }
    assert len(statuses) == 1
    status = statuses.pop()
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    version = load_json(ROOT / "manifest" / "toolkit.json")["toolkitVersion"]

    if status == "release-candidate":
        assert "## [Unreleased]" in changelog
        assert (
            re.search(
                rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$", changelog, re.MULTILINE
            )
            is None
        )
    else:
        assert status == "released"
        assert re.search(
            rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$", changelog, re.MULTILINE
        )
        product_specification = (ROOT / "docs" / "product-specification.md").read_text(
            encoding="utf-8"
        )
        assert (
            f"Status: release candidate until the matching `v{version}` Git tag and GitHub Release "
            "pass remote\nreadback."
        ) in product_specification
        assert (
            "Machine-readable `released` status marks frozen versioned source and changelog "
            "identity; it does not\nprove external publication."
        ) in product_specification
        assert "separate, non-substitutable acceptance evidence" in product_specification


def test_mechanism_gate_remains_conditional_not_global() -> None:
    text = re.sub(
        r"\s+",
        " ",
        (ROOT / "skills" / "engineering-specification" / "SKILL.md")
        .read_text(encoding="utf-8")
        .lower(),
    )
    assert "narrow and optional" in text
    assert "already explicit small contract bypasses this gate" in text
    assert "direct path" in text

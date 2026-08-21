#!/usr/bin/env python3
"""Validate toolkit structure, routing metadata, hygiene, and optional release lock."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote

SENTINEL = "<!-- TOOLKIT-CONTRIBUTION-PROTOCOL:v1 -->"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
IGNORED_PARTS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    ".codegraph",
    "__pycache__",
    "build",
    "dist",
}
IGNORED_FILE_NAMES = {".coverage", ".DS_Store", "Thumbs.db"}
IGNORED_FILE_SUFFIXES = {".pyc", ".pyo"}
HYGIENE_PATTERNS = (
    re.compile(r"(?i)\b[A-Z]:[\\/]Users[\\/][^\\/\s]+[\\/]"),
    re.compile(r"(?i)\bD:[\\/]Warehouse[\\/]"),
    re.compile(r"(?i)\bD:[\\/]\.cleanroom(?:[\\/]|\b)"),
    re.compile(r"(?i)(?:^|[\s(\"'])/(?:home|Users)/[^/\s]+/"),
    re.compile(r"(?i)adaptive-agent-runtime[\\/]?\.debug"),
    re.compile("(?i)AAR" + "-vs-prime-agent-minions"),
)
REQUIRED_PROTOCOL_PATTERNS = (
    re.compile(r"installed (?:copy|projection)"),
    re.compile(r"canonical"),
    re.compile(r"exact"),
    re.compile(r"eval(?:uation)?"),
    re.compile(r"draft pull request"),
    re.compile(r"authoriz"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_read(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _candidate_identity(root: Path) -> tuple[dict[str, str | None], bool]:
    """Read a bounded, self-consistent identity for one clean Git candidate."""

    root = root.resolve()
    identity: dict[str, str | None] = {
        "commit": None,
        "tree": None,
        "catalogSha256": None,
        "toolkitVersion": None,
        "pluginVersion": None,
    }
    try:
        top_level = Path(_git_read(root, "rev-parse", "--show-toplevel")).resolve()
        first_commit = _git_read(root, "rev-parse", "--verify", "HEAD").lower()
        first_tree = _git_read(root, "rev-parse", "--verify", "HEAD^{tree}").lower()
        first_status = _git_read(root, "status", "--porcelain=v1", "--untracked-files=all")

        catalog_path = root / "catalog" / "skills.json"
        toolkit_path = root / "manifest" / "toolkit.json"
        plugin_path = root / ".codex-plugin" / "plugin.json"
        first_catalog = catalog_path.read_bytes()
        first_toolkit = toolkit_path.read_bytes()
        first_plugin = plugin_path.read_bytes()

        second_catalog = catalog_path.read_bytes()
        second_toolkit = toolkit_path.read_bytes()
        second_plugin = plugin_path.read_bytes()
        second_commit = _git_read(root, "rev-parse", "--verify", "HEAD").lower()
        second_tree = _git_read(root, "rev-parse", "--verify", "HEAD^{tree}").lower()
        second_status = _git_read(root, "status", "--porcelain=v1", "--untracked-files=all")

        toolkit = json.loads(first_toolkit.decode("utf-8"))
        plugin = json.loads(first_plugin.decode("utf-8"))
        if not isinstance(toolkit, dict) or not isinstance(plugin, dict):
            return identity, False
        identity.update(
            {
                "commit": second_commit,
                "tree": second_tree,
                "catalogSha256": hashlib.sha256(first_catalog).hexdigest(),
                "toolkitVersion": toolkit.get("toolkitVersion"),
                "pluginVersion": plugin.get("version"),
            }
        )
        stable = (
            top_level == root
            and re.fullmatch(r"[0-9a-f]{40}", first_commit) is not None
            and re.fullmatch(r"[0-9a-f]{40}", first_tree) is not None
            and (first_commit, first_tree) == (second_commit, second_tree)
            and not first_status
            and not second_status
            and first_catalog == second_catalog
            and first_toolkit == second_toolkit
            and first_plugin == second_plugin
            and isinstance(identity["toolkitVersion"], str)
            and isinstance(identity["pluginVersion"], str)
        )
        return identity, stable
    except (
        FileNotFoundError,
        OSError,
        subprocess.CalledProcessError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        return identity, False


def validate_behavior_result(root: Path, result: object) -> list[dict[str, str]]:
    """Validate behavior-result semantics against the frozen acceptance corpus.

    ``eval-result.schema.json`` owns local JSON shape.  This function owns the
    cross-document invariants that the schema cannot express: exact corpus
    identity, exact case membership, expected skill selections, and the
    conditions under which a result may be promoted to ``PASS``.

    The returned records deliberately use stable error codes so callers can
    turn a failed evaluation into a deterministic regression instead of
    interpreting prose or a schema-only pass.
    """

    errors: list[dict[str, str]] = []
    corpus_path = Path(root).resolve() / "evals" / "cases" / "acceptance.json"
    try:
        corpus = load_json(corpus_path)
        corpus_bytes = corpus_path.read_bytes()
    except (OSError, json.JSONDecodeError) as exc:
        _error(
            errors,
            "EVAL_RESULT_CORPUS_HASH",
            corpus_path,
            f"cannot load the frozen acceptance corpus: {exc}",
        )
        return errors

    if not isinstance(corpus, dict) or not isinstance(corpus.get("cases"), list):
        _error(
            errors,
            "EVAL_RESULT_CASE_SET",
            corpus_path,
            "the frozen acceptance corpus does not contain a case list",
        )
        return errors

    expected_hash = hashlib.sha256(corpus_bytes).hexdigest()
    if not isinstance(result, dict):
        _error(
            errors,
            "EVAL_RESULT_VERDICT",
            Path("result"),
            "behavior result must be an object",
        )
        return errors

    expected_candidate, candidate_verifiable = _candidate_identity(Path(root))
    candidate = result.get("candidate")
    if not candidate_verifiable:
        _error(
            errors,
            "EVAL_RESULT_CANDIDATE_UNVERIFIABLE",
            Path("candidate"),
            "root does not identify one stable Git-clean candidate",
        )
    if isinstance(candidate, dict):
        comparisons = (
            ("commit", "EVAL_RESULT_CANDIDATE_COMMIT"),
            ("tree", "EVAL_RESULT_CANDIDATE_TREE"),
            ("catalogSha256", "EVAL_RESULT_CANDIDATE_CATALOG_HASH"),
            ("pluginVersion", "EVAL_RESULT_PLUGIN_VERSION"),
        )
        for field, code in comparisons:
            expected = expected_candidate.get(field)
            if expected is not None and candidate.get(field) != expected:
                _error(
                    errors,
                    code,
                    Path(f"candidate.{field}"),
                    f"result {field} does not match the exact root candidate",
                )
    if result.get("toolkitVersion") != expected_candidate.get("toolkitVersion"):
        _error(
            errors,
            "EVAL_RESULT_TOOLKIT_VERSION",
            Path("toolkitVersion"),
            "result toolkitVersion does not match manifest/toolkit.json",
        )
    if result.get("caseCorpusSha256") != expected_hash:
        _error(
            errors,
            "EVAL_RESULT_CORPUS_HASH",
            Path("caseCorpusSha256"),
            "result is not bound to the exact frozen acceptance corpus bytes",
        )

    canonical: dict[str, dict[str, Any]] = {}
    for case in corpus["cases"]:
        if isinstance(case, dict) and isinstance(case.get("id"), str):
            canonical[case["id"]] = case

    rows = result.get("results")
    if not isinstance(rows, list):
        _error(
            errors,
            "EVAL_RESULT_CASE_SET",
            Path("results"),
            "result must contain a list of case results",
        )
        rows = []

    seen: set[str] = set()
    duplicate_ids: set[str] = set()
    actual_ids: set[str] = set()
    for index, row in enumerate(rows):
        case_id = row.get("id") if isinstance(row, dict) else None
        if not isinstance(case_id, str):
            _error(
                errors,
                "EVAL_RESULT_CASE_SET",
                Path(f"results[{index}].id"),
                "each result must identify a canonical case",
            )
            continue
        actual_ids.add(case_id)
        if case_id in seen:
            duplicate_ids.add(case_id)
        seen.add(case_id)
    for case_id in sorted(duplicate_ids):
        _error(
            errors,
            "EVAL_RESULT_CASE_DUPLICATE",
            Path("results"),
            f"case {case_id!r} appears more than once",
        )
    expected_ids = set(canonical)
    if actual_ids != expected_ids:
        missing = sorted(expected_ids - actual_ids)
        unknown = sorted(actual_ids - expected_ids)
        _error(
            errors,
            "EVAL_RESULT_CASE_SET",
            Path("results"),
            f"case set differs from corpus; missing={missing}, unknown={unknown}",
        )

    statuses: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        case_id = row.get("id")
        status = row.get("status")
        if isinstance(status, str):
            statuses.append(status)
        case = canonical.get(case_id) if isinstance(case_id, str) else None
        if case is None:
            continue

        selected = row.get("selected")
        not_selected = row.get("notSelected")
        if not isinstance(selected, list) or not isinstance(not_selected, list):
            continue
        expected_selected = case.get("expectedSelected", [])
        expected_not_selected = case.get("expectedNotSelected", [])
        if set(selected) != set(expected_selected) or set(not_selected) != set(
            expected_not_selected
        ):
            _error(
                errors,
                "EVAL_RESULT_SELECTION",
                Path(f"results[{index}]"),
                f"case {case_id!r} selections do not equal the corpus expectations",
            )

        if status == "PASS":
            if row.get("prohibitedEffectsObserved") is True:
                _error(
                    errors,
                    "EVAL_RESULT_PASS_PROHIBITED_EFFECT",
                    Path(f"results[{index}].prohibitedEffectsObserved"),
                    "a PASS row cannot report a prohibited effect",
                )
            evidence = row.get("evidence")
            valid_evidence = (
                isinstance(evidence, dict)
                and evidence.get("kind") in {"REDACTED_TRANSCRIPT", "RECEIPT"}
                and isinstance(evidence.get("pointer"), str)
                and bool(evidence["pointer"].strip())
                and isinstance(evidence.get("sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", evidence["sha256"]) is not None
            )
            if not valid_evidence:
                _error(
                    errors,
                    "EVAL_RESULT_PASS_EVIDENCE",
                    Path(f"results[{index}].evidence"),
                    "a PASS row needs non-NONE evidence with a pointer and 64-hex digest",
                )

    summary = result.get("summary")
    if not isinstance(summary, dict):
        _error(
            errors,
            "EVAL_RESULT_SUMMARY",
            Path("summary"),
            "result must contain a summary object",
        )
        summary = {}
    expected_counts = {
        "pass": statuses.count("PASS"),
        "fail": statuses.count("FAIL"),
        "notRun": statuses.count("NOT_RUN"),
    }
    if any(summary.get(key) != value for key, value in expected_counts.items()):
        _error(
            errors,
            "EVAL_RESULT_SUMMARY",
            Path("summary"),
            f"summary counts must equal result rows: {expected_counts}",
        )
    if summary.get("verdict") == "PASS" and any(status != "PASS" for status in statuses):
        _error(
            errors,
            "EVAL_RESULT_VERDICT",
            Path("summary.verdict"),
            "PASS requires every canonical case result to have status PASS",
        )
    return errors


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by Agent Skills without a runtime dependency."""

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening frontmatter delimiter")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise ValueError("missing closing frontmatter delimiter") from exc

    result: dict[str, Any] = {}
    index = 1
    while index < end:
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if line.startswith((" ", "\t")) or ":" not in line:
            index += 1
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if value in {">", ">-", "|", "|-"}:
            chunks: list[str] = []
            index += 1
            while index < end and (
                not lines[index].strip() or lines[index].startswith((" ", "\t"))
            ):
                chunks.append(lines[index].strip())
                index += 1
            result[key] = " ".join(chunk for chunk in chunks if chunk)
            continue
        if value == "":
            nested: dict[str, str] = {}
            index += 1
            while index < end and (
                not lines[index].strip() or lines[index].startswith((" ", "\t"))
            ):
                nested_line = lines[index].strip()
                if nested_line and ":" in nested_line:
                    nested_key, nested_value = nested_line.split(":", 1)
                    nested[nested_key.strip()] = nested_value.strip().strip("\"'")
                index += 1
            result[key] = nested
            continue
        result[key] = value.strip("\"'")
        index += 1
    return result


def _error(errors: list[dict[str, str]], code: str, path: Path, message: str) -> None:
    errors.append({"code": code, "path": path.as_posix(), "message": message})


def _read_implicit_policy(path: Path) -> bool | None:
    if not path.is_file():
        return None
    match = re.search(
        r"(?m)^\s*allow_implicit_invocation\s*:\s*(true|false)\s*$",
        path.read_text(encoding="utf-8"),
        re.IGNORECASE,
    )
    return None if match is None else match.group(1).lower() == "true"


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def _is_ignored_relative(path: Path) -> bool:
    return (
        any(part in IGNORED_PARTS or part.endswith(".egg-info") for part in path.parts)
        or path.name in IGNORED_FILE_NAMES
        or path.suffix.lower() in IGNORED_FILE_SUFFIXES
    )


def _validate_skill(
    root: Path,
    skill_dir: Path,
    catalog_row: dict[str, Any] | None,
    errors: list[dict[str, str]],
) -> str | None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        _error(errors, "SKILL_MISSING", skill_dir, "SKILL.md is required")
        return None
    text = skill_md.read_text(encoding="utf-8")
    try:
        frontmatter = parse_frontmatter(text)
    except ValueError as exc:
        _error(errors, "SKILL_FRONTMATTER", skill_md, str(exc))
        return None

    name = str(frontmatter.get("name", ""))
    if name != skill_dir.name or not NAME_RE.fullmatch(name) or len(name) > 64:
        _error(
            errors,
            "SKILL_NAME",
            skill_md,
            f"frontmatter name {name!r} must match directory and kebab-case constraints",
        )
    description = str(frontmatter.get("description", ""))
    if not description or len(description) > 1024 or "TODO" in description:
        _error(
            errors,
            "SKILL_DESCRIPTION",
            skill_md,
            "description must be complete and no longer than 1024 characters",
        )
    if frontmatter.get("license") != "MIT":
        _error(errors, "SKILL_LICENSE", skill_md, "toolkit-owned skills must declare MIT")
    metadata = frontmatter.get("metadata")
    expected_phase = None if catalog_row is None else catalog_row.get("phase")
    if not isinstance(metadata, dict):
        _error(errors, "SKILL_METADATA", skill_md, "metadata mapping is required")
    else:
        if metadata.get("toolkit-version") != "0.4.0":
            _error(errors, "SKILL_METADATA", skill_md, "toolkit-version must be 0.4.0")
        if metadata.get("toolkit-contribution-protocol") != "v1":
            _error(errors, "SKILL_METADATA", skill_md, "contribution protocol must be v1")
        if expected_phase and metadata.get("toolkit-phase") != expected_phase:
            _error(
                errors,
                "SKILL_METADATA",
                skill_md,
                f"toolkit-phase must match catalog phase {expected_phase!r}",
            )

    lowered = text.lower()
    if text.count(SENTINEL) != 1 or any(
        pattern.search(lowered) is None for pattern in REQUIRED_PROTOCOL_PATTERNS
    ):
        _error(
            errors,
            "SKILL_CONTRIBUTION_SENTINEL",
            skill_md,
            "exactly one v1 sentinel and the complete canonical PR behavior are required",
        )

    policy_path = skill_dir / "agents" / "openai.yaml"
    actual_policy = _read_implicit_policy(policy_path)
    if actual_policy is None:
        _error(
            errors,
            "SKILL_IMPLICIT_POLICY",
            policy_path,
            "agents/openai.yaml must explicitly set allow_implicit_invocation",
        )
    elif catalog_row is not None:
        expected_policy = bool(catalog_row["policy"]["allow_implicit_invocation"])
        if actual_policy != expected_policy:
            _error(
                errors,
                "SKILL_IMPLICIT_POLICY",
                policy_path,
                f"policy {actual_policy} does not match catalog {expected_policy}",
            )

    for raw_target in MARKDOWN_LINK_RE.findall(text):
        target = raw_target.strip().split("#", 1)[0]
        if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
            continue
        target = unquote(target.strip("<>"))
        resolved = (skill_md.parent / target).resolve(strict=False)
        if not _is_within(resolved, skill_dir):
            _error(
                errors,
                "SKILL_REFERENCE_ESCAPE",
                skill_md,
                f"relative reference escapes skill directory: {raw_target}",
            )
        elif not resolved.exists():
            _error(
                errors,
                "SKILL_REFERENCE_MISSING",
                skill_md,
                f"relative reference is missing: {raw_target}",
            )
    return name or None


def _validate_hygiene(root: Path, errors: list[dict[str, str]]) -> None:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _is_ignored_relative(path.relative_to(root)):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        matches = [pattern.pattern for pattern in HYGIENE_PATTERNS if pattern.search(text)]
        if matches:
            _error(
                errors,
                "PUBLIC_HYGIENE",
                path,
                f"public text matched private-path pattern(s): {', '.join(matches)}",
            )


def _validate_repository_links(root: Path, errors: list[dict[str, str]]) -> None:
    for path in sorted(root.rglob("*.md")):
        if _is_ignored_relative(path.relative_to(root)):
            continue
        text = path.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK_RE.findall(text):
            target = raw_target.strip().split("#", 1)[0]
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                continue
            target = unquote(target.strip("<>"))
            resolved = (path.parent / target).resolve(strict=False)
            if not _is_within(resolved, root):
                _error(
                    errors,
                    "REPOSITORY_REFERENCE_ESCAPE",
                    path,
                    f"relative reference escapes repository: {raw_target}",
                )
            elif not resolved.exists():
                _error(
                    errors,
                    "REPOSITORY_REFERENCE_MISSING",
                    path,
                    f"relative reference is missing: {raw_target}",
                )


def _sort_release_candidates(root: Path, candidates: list[Path]) -> list[Path]:
    return sorted(candidates, key=lambda path: path.relative_to(root).as_posix())


def _release_files(root: Path) -> list[Path]:
    if (root / ".git").exists():
        top_level = Path(_git_read(root, "rev-parse", "--show-toplevel")).resolve()
        if top_level != root.resolve():
            raise ValueError("release root is not the Git worktree root")
        tracked = _git_read(root, "ls-files", "--cached", "-z").split("\0")
        candidates = [root / relative for relative in tracked if relative]
    else:
        candidates = list(root.rglob("*"))

    return [
        path
        for path in _sort_release_candidates(root, candidates)
        if path.is_file()
        and not _is_ignored_relative(path.relative_to(root))
        and path.relative_to(root).as_posix() != "manifest/public-lock.json"
    ]


def build_public_lock(root: Path) -> dict[str, Any]:
    files = _release_files(root)
    return {
        "schemaVersion": 1,
        "toolkitVersion": "0.4.0",
        "algorithm": "sha256",
        "excludesSelf": "manifest/public-lock.json",
        "files": [
            {
                "path": path.relative_to(root).as_posix(),
                "length": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
    }


def _validate_release_lock(root: Path, errors: list[dict[str, str]]) -> None:
    path = root / "manifest" / "public-lock.json"
    if not path.is_file():
        _error(errors, "RELEASE_LOCK_MISSING", path, "release validation requires a public lock")
        return
    try:
        actual = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        _error(errors, "RELEASE_LOCK_INVALID", path, str(exc))
        return
    expected = build_public_lock(root)
    if actual != expected:
        _error(errors, "RELEASE_LOCK_DRIFT", path, "public lock does not match current bytes")


def validate_toolkit(root: Path, *, release: bool = False) -> list[dict[str, str]]:
    root = root.resolve()
    errors: list[dict[str, str]] = []

    required_json = {
        "plugin": root / ".codex-plugin" / "plugin.json",
        "marketplace": root / ".agents" / "plugins" / "marketplace.json",
        "catalog": root / "catalog" / "skills.json",
        "evals": root / "evals" / "cases" / "acceptance.json",
        "toolkit_manifest": root / "manifest" / "toolkit.json",
        "provenance": root / "manifest" / "provenance.json",
    }
    documents: dict[str, Any] = {}
    for key, path in required_json.items():
        try:
            documents[key] = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            _error(errors, "JSON_REQUIRED", path, str(exc))
    if errors:
        _validate_hygiene(root, errors)
        return sorted(errors, key=lambda row: (row["code"], row["path"], row["message"]))

    plugin = documents["plugin"]
    if (
        plugin.get("name") != "smart-agentic-engineering-toolkit"
        or plugin.get("version") != "0.4.0"
        or plugin.get("skills") != "./skills/"
    ):
        _error(
            errors,
            "PLUGIN_MANIFEST",
            required_json["plugin"],
            "plugin name/version/skills path do not match the product contract",
        )
    marketplace_plugins = documents["marketplace"].get("plugins", [])
    if len(marketplace_plugins) != 1 or marketplace_plugins[0].get("source") != {
        "source": "local",
        "path": "./",
    }:
        _error(
            errors,
            "MARKETPLACE_MANIFEST",
            required_json["marketplace"],
            "marketplace must expose exactly the repository-root plugin",
        )

    catalog_rows = documents["catalog"].get("skills", [])
    catalog_by_name = {row.get("name"): row for row in catalog_rows if row.get("name")}
    if len(catalog_rows) != len(catalog_by_name):
        _error(
            errors,
            "CATALOG_NAME_DUPLICATE",
            required_json["catalog"],
            "catalog skill names must be present and unique",
        )
    skill_dirs = sorted(
        path
        for path in (root / "skills").iterdir()
        if path.is_dir() and not path.name.startswith(".")
    )
    dir_names = {path.name for path in skill_dirs}
    if set(catalog_by_name) != dir_names:
        _error(
            errors,
            "CATALOG_SKILL_SET",
            required_json["catalog"],
            f"catalog={sorted(catalog_by_name)} directories={sorted(dir_names)}",
        )

    parsed_names: list[str] = []
    for skill_dir in skill_dirs:
        parsed = _validate_skill(root, skill_dir, catalog_by_name.get(skill_dir.name), errors)
        if parsed:
            parsed_names.append(parsed)
    if len(parsed_names) != len(set(parsed_names)):
        _error(
            errors,
            "SKILL_NAME_DUPLICATE",
            root / "skills",
            "two or more SKILL.md files declare the same name",
        )

    profile_members: dict[str, list[str]] = {}
    for profile_path in sorted((root / "profiles").glob("*.json")):
        try:
            profile = load_json(profile_path)
        except json.JSONDecodeError as exc:
            _error(errors, "PROFILE_JSON", profile_path, str(exc))
            continue
        profile_members[profile_path.stem] = profile.get("skills", [])
    assigned: list[str] = []
    for name, row in catalog_by_name.items():
        profile = row.get("profile")
        if profile not in profile_members or name not in profile_members[profile]:
            _error(
                errors,
                "PROFILE_SKILL_SET",
                root / "profiles" / f"{profile}.json",
                f"{name} is missing from its declared profile",
            )
        assigned.append(name)
    listed = [name for members in profile_members.values() for name in members]
    if sorted(listed) != sorted(assigned) or len(listed) != len(set(listed)):
        _error(
            errors,
            "PROFILE_SKILL_SET",
            root / "profiles",
            "profiles must cover every owned skill exactly once",
        )

    cases = documents["evals"].get("cases", [])
    case_ids = [case.get("id") for case in cases]
    if len(cases) != 63 or len(case_ids) != len(set(case_ids)) or None in case_ids:
        _error(
            errors,
            "EVAL_CASE_SET",
            required_json["evals"],
            "the release-bound baseline corpus must contain 63 uniquely identified cases",
        )
    for name in sorted(dir_names):
        if not any(name in case.get("expectedSelected", []) for case in cases):
            _error(
                errors,
                "EVAL_ACTIVATION_COVERAGE",
                required_json["evals"],
                f"no positive selection case for {name}",
            )
        if not any(name in case.get("expectedNotSelected", []) for case in cases):
            _error(
                errors,
                "EVAL_NONACTIVATION_COVERAGE",
                required_json["evals"],
                f"no explicit non-selection case for {name}",
            )

    manifest_names = set(documents["toolkit_manifest"].get("ownedSkills", []))
    if manifest_names != dir_names:
        _error(
            errors,
            "TOOLKIT_MANIFEST_SKILL_SET",
            required_json["toolkit_manifest"],
            "manifest ownedSkills must match skill directories",
        )
    provenance_names = {
        row.get("name") for row in documents["provenance"].get("skills", []) if row.get("name")
    }
    if provenance_names != dir_names:
        _error(
            errors,
            "PROVENANCE_SKILL_SET",
            required_json["provenance"],
            "every owned skill needs exactly one provenance row",
        )

    allowed_top = set(documents["toolkit_manifest"].get("allowedTopLevel", []))
    ignored_top = {".git", ".venv", ".pytest_cache", ".ruff_cache", ".codegraph"}
    actual_top = {
        path.name
        for path in root.iterdir()
        if path.name not in ignored_top and not path.name.endswith(".egg-info")
    }
    if actual_top != allowed_top:
        _error(
            errors,
            "TOOLKIT_TOP_LEVEL",
            required_json["toolkit_manifest"],
            f"allowed={sorted(allowed_top)} actual={sorted(actual_top)}",
        )
    denied_patterns = documents["toolkit_manifest"].get("deniedPatterns", [])
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if _is_ignored_relative(path.relative_to(root)):
            continue
        if any(fnmatch.fnmatch(relative, pattern) for pattern in denied_patterns):
            _error(
                errors,
                "TOOLKIT_DENIED_PATH",
                path,
                "path is forbidden by the source manifest",
            )

    dependency_documents: dict[str, Any] = {}
    for dependency_path in sorted((root / "dependencies").glob("*.json")):
        try:
            dependency_documents[dependency_path.stem] = load_json(dependency_path)
        except json.JSONDecodeError as exc:
            _error(errors, "DEPENDENCY_JSON", dependency_path, str(exc))
    expected_dependencies = set(documents["toolkit_manifest"].get("externalDependencies", []))
    dependency_names = {document.get("name") for document in dependency_documents.values()}
    if dependency_names != expected_dependencies:
        _error(
            errors,
            "DEPENDENCY_SET",
            root / "dependencies",
            f"manifest={sorted(expected_dependencies)} dependencies={sorted(dependency_names)}",
        )
    for stem, document in dependency_documents.items():
        resolved = document.get("pin", {}).get("resolvedCommit")
        if not isinstance(resolved, str) or re.fullmatch(r"[0-9a-f]{40}", resolved) is None:
            _error(
                errors,
                "DEPENDENCY_PIN",
                root / "dependencies" / f"{stem}.json",
                "external pointer must record an observed exact 40-hex commit",
            )

    frozen_inputs = documents["evals"].get("frozenInputs", [])
    frozen_input_hashes = {
        row.get("name"): row.get("sha256")
        for row in frozen_inputs
        if isinstance(row, dict)
    }
    source_hash_aliases = {
        "productSpecification": "docs/product-specification.md",
        "catalog": "catalog/skills.json",
    }
    source_hashes = documents["evals"].get("sourceHashes", {})
    for alias, relative_path in source_hash_aliases.items():
        if source_hashes.get(alias) != frozen_input_hashes.get(relative_path):
            _error(
                errors,
                "EVAL_SOURCE_HASH_ALIAS",
                root / "evals" / "cases" / "acceptance.json",
                f"sourceHashes.{alias} must match frozenInputs[{relative_path!r}]",
            )
    for row in frozen_inputs:
        path = root / row.get("name", "")
        expected_hash = row.get("sha256")
        if not path.is_file() or sha256_file(path) != expected_hash:
            _error(
                errors,
                "EVAL_FROZEN_INPUT",
                path,
                "frozen public input is missing or hash-mismatched",
            )

    _validate_hygiene(root, errors)
    _validate_repository_links(root, errors)
    if release:
        _validate_release_lock(root, errors)
    return sorted(errors, key=lambda row: (row["code"], row["path"], row["message"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--release", action="store_true", help="also require exact public lock")
    parser.add_argument(
        "--write-lock",
        action="store_true",
        help="write manifest/public-lock.json from current public files, then validate release mode",
    )
    args = parser.parse_args(argv)
    if args.write_lock:
        path = args.root / "manifest" / "public-lock.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(
                json.dumps(build_public_lock(args.root.resolve()), indent=2, ensure_ascii=False)
                + "\n"
            )
        args.release = True
    errors = validate_toolkit(args.root, release=args.release)
    payload = {
        "valid": not errors,
        "root": str(args.root.resolve()),
        "releaseMode": args.release,
        "errorCount": len(errors),
        "errors": errors,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

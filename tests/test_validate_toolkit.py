from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path, PurePosixPath, PureWindowsPath

from scripts import validate_toolkit as validate_toolkit_module
from scripts.validate_toolkit import build_public_lock, validate_toolkit

ROOT = Path(__file__).resolve().parents[1]


def clone_repo(tmp_path: Path) -> Path:
    target = tmp_path / "toolkit"
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".codegraph",
            ".pytest_cache",
            ".ruff_cache",
            "*.egg-info",
            "__pycache__",
            ".debug",
        ),
    )
    return target


def codes(errors: list[dict[str, str]]) -> set[str]:
    return {error["code"] for error in errors}


def test_repository_candidate_is_valid() -> None:
    assert validate_toolkit(ROOT) == []


def test_missing_contribution_sentinel_is_rejected(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)
    path = root / "skills" / "engineering-wal" / "SKILL.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("<!-- TOOLKIT-CONTRIBUTION-PROTOCOL:v1 -->", ""),
        encoding="utf-8",
    )

    assert "SKILL_CONTRIBUTION_SENTINEL" in codes(validate_toolkit(root))


def test_duplicate_frontmatter_name_is_rejected(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)
    path = root / "skills" / "engineering-wal" / "SKILL.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "name: engineering-wal", "name: engineering-debugging", 1
        ),
        encoding="utf-8",
    )

    assert "SKILL_NAME_DUPLICATE" in codes(validate_toolkit(root))


def test_catalog_skill_set_must_match_directories(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)
    catalog_path = root / "catalog" / "skills.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["skills"] = [row for row in catalog["skills"] if row["name"] != "engineering-wal"]
    catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    assert "CATALOG_SKILL_SET" in codes(validate_toolkit(root))


def test_each_skill_needs_activation_and_nonactivation_cases(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)
    eval_path = root / "evals" / "cases" / "acceptance.json"
    document = json.loads(eval_path.read_text(encoding="utf-8"))
    document["cases"] = [
        row
        for row in document["cases"]
        if "engineering-wal" not in row.get("expectedSelected", [])
        and "engineering-wal" not in row.get("expectedNotSelected", [])
    ]
    eval_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    assert "EVAL_ACTIVATION_COVERAGE" in codes(validate_toolkit(root))
    assert "EVAL_NONACTIVATION_COVERAGE" in codes(validate_toolkit(root))


def test_skill_reference_cannot_escape_its_directory(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)
    path = root / "skills" / "engineering-wal" / "SKILL.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\n[escape](../../README.md)\n",
        encoding="utf-8",
    )

    assert "SKILL_REFERENCE_ESCAPE" in codes(validate_toolkit(root))


def test_repository_markdown_link_must_resolve_inside_source(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)
    path = root / "README.en.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\n[missing](docs/does-not-exist.md)\n",
        encoding="utf-8",
    )

    assert "REPOSITORY_REFERENCE_MISSING" in codes(validate_toolkit(root))


def test_private_machine_path_is_rejected(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)
    path = root / "README.en.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\nC:\\Users\\example\\private\\receipt.json\n",
        encoding="utf-8",
    )

    assert "PUBLIC_HYGIENE" in codes(validate_toolkit(root))


def test_private_machine_path_with_forward_slashes_is_rejected(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)
    path = root / "README.en.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\nC:/Users/example/private/receipt.json\n",
        encoding="utf-8",
    )

    assert "PUBLIC_HYGIENE" in codes(validate_toolkit(root))


def test_private_posix_home_path_is_rejected(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)
    path = root / "README.en.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\n/home/example/private/receipt.json\n",
        encoding="utf-8",
    )

    assert "PUBLIC_HYGIENE" in codes(validate_toolkit(root))


def test_generated_python_cache_is_ignored(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)
    cache_file = root / "scripts" / "__pycache__" / "generated.pyc"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(b"generated")
    root_bytecode = root / "generated.pyc"
    root_bytecode.write_bytes(b"generated")

    errors = validate_toolkit(root)
    assert not any(
        error["code"] == "TOOLKIT_DENIED_PATH" and error["path"].endswith("generated.pyc")
        for error in errors
    )
    locked_paths = {row["path"] for row in build_public_lock(root)["files"]}
    assert "scripts/__pycache__/generated.pyc" not in locked_paths
    assert "generated.pyc" not in locked_paths


def test_editable_install_metadata_is_ignored(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)
    metadata = root / "example.egg-info" / "PKG-INFO"
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text("generated", encoding="utf-8")

    errors = validate_toolkit(root)
    assert "TOOLKIT_TOP_LEVEL" not in codes(errors)
    assert all(
        not row["path"].startswith("example.egg-info/") for row in build_public_lock(root)["files"]
    )


def test_public_lock_excludes_untracked_worktree_files(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    local_test = root / "tests" / "test_local_only.py"
    local_test.write_text("def test_local_only():\n    assert True\n", encoding="utf-8")

    locked_paths = {row["path"] for row in build_public_lock(root)["files"]}

    assert "README.md" in locked_paths
    assert "tests/test_local_only.py" not in locked_paths


def test_release_file_order_is_platform_independent() -> None:
    relative_paths = [
        "catalog/skills.json",
        "CHANGELOG.md",
        "README.md",
        "scripts/install.ps1",
    ]

    def ordered(root: PurePosixPath | PureWindowsPath) -> list[str]:
        candidates = [root / relative for relative in relative_paths]
        return [
            path.relative_to(root).as_posix()
            for path in validate_toolkit_module._sort_release_candidates(root, candidates)
        ]

    expected = sorted(relative_paths)
    assert ordered(PureWindowsPath("C:/toolkit")) == expected
    assert ordered(PurePosixPath("/toolkit")) == expected


def test_install_receipt_schema_is_not_a_runtime_receipt(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)

    errors = validate_toolkit(root)
    assert not any(
        error["code"] == "TOOLKIT_DENIED_PATH"
        and error["path"].endswith("schemas/install-receipt.schema.json")
        for error in errors
    )


def test_release_lock_is_required_and_detects_drift(tmp_path: Path) -> None:
    root = clone_repo(tmp_path)
    lock_path = root / "manifest" / "public-lock.json"
    if lock_path.exists():
        lock_path.unlink()

    assert "RELEASE_LOCK_MISSING" in codes(validate_toolkit(root, release=True))
    lock_path.write_text(
        json.dumps(build_public_lock(root), indent=2) + "\n",
        encoding="utf-8",
    )
    assert "RELEASE_LOCK_MISSING" not in codes(validate_toolkit(root, release=True))
    assert "RELEASE_LOCK_DRIFT" not in codes(validate_toolkit(root, release=True))

    readme = root / "README.en.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\nDrift.\n", encoding="utf-8")
    assert "RELEASE_LOCK_DRIFT" in codes(validate_toolkit(root, release=True))

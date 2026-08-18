from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.install_toolkit import (
    InstallConflict,
    InstallContainmentError,
    Installer,
    _exclusive_install_lock,
    tree_digest,
    tree_files,
)


def write_source(root: Path, contents: dict[str, str], version: str = "0.3.0") -> None:
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


def plan_map(installer: Installer) -> dict[str, str]:
    return {item.name: item.classification for item in installer.plan("core")}


def test_clean_install_then_exact_plan(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    installer = Installer(source, target)

    assert plan_map(installer) == {"alpha-skill": "ADD"}
    receipt = installer.install("core")
    assert receipt["skills"]["alpha-skill"]["installedTreeSha256"] == tree_digest(
        target / "alpha-skill"
    )
    assert plan_map(installer) == {"alpha-skill": "EXACT"}


@pytest.mark.parametrize("upgrade", [False, True], ids=["add", "upgrade"])
def test_foreign_post_commit_receipt_fences_target_compensation(
    tmp_path: Path, upgrade: bool
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    if upgrade:
        Installer(source, target).install("core")
        write_source(source, {"alpha-skill": "v2"}, version="0.1.1")
    receipt_path = target / ".smart-agentic-engineering-toolkit-install.json"
    foreign_receipt = b'{"foreign":true}\n'
    published_skill: list[bytes] = []

    def replace_receipt_only(phase: str, _name: str | None, _installer: Installer) -> None:
        if phase == "after_receipt_commit":
            published_skill.append((target / "alpha-skill" / "SKILL.md").read_bytes())
            receipt_path.write_bytes(foreign_receipt)

    with pytest.raises(InstallContainmentError):
        Installer(source, target, fault_hook=replace_receipt_only).install("core")

    assert receipt_path.read_bytes() == foreign_receipt
    assert (target / "alpha-skill" / "SKILL.md").read_bytes() == published_skill[0]


def test_semantically_invalid_existing_receipt_is_rejected_before_planning(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    installer = Installer(source, target)
    installer.install("core")
    before = tree_digest(target / "alpha-skill")
    receipt = json.loads(installer.receipt_path.read_text(encoding="utf-8"))
    receipt["skills"]["alpha-skill"]["installedTreeSha256"] = "0" * 64
    installer.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(InstallConflict, match="semantic errors"):
        installer.plan("core")

    assert tree_digest(target / "alpha-skill") == before


def test_generated_cache_members_are_not_installed_or_receipted(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    skill = source / "skills" / "alpha-skill"
    generated = {
        "__pycache__/helper.cpython-311.pyc": b"bytecode",
        ".pytest_cache/v/cache/nodeids": b"[]",
        ".ruff_cache/0.3.0/cache": b"lint cache",
        "build/generated.txt": b"build output",
        "dist/archive.whl": b"wheel output",
        "helper.egg-info/PKG-INFO": b"metadata",
    }
    for relative, body in generated.items():
        path = skill / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)

    receipt = Installer(source, target).install("core")

    installed = target / "alpha-skill"
    assert [row["path"] for row in tree_files(installed)] == ["SKILL.md"]
    assert [row["path"] for row in receipt["skills"]["alpha-skill"]["files"]] == ["SKILL.md"]
    for relative in generated:
        assert not (installed / relative).exists()


def test_generated_target_cache_does_not_make_managed_skill_diverged(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    installer = Installer(source, target)
    installer.install("core")
    generated = target / "alpha-skill" / "__pycache__" / "helper.cpython-311.pyc"
    generated.parent.mkdir(parents=True)
    generated.write_bytes(b"runtime bytecode")

    assert plan_map(installer) == {"alpha-skill": "EXACT"}


def test_concurrent_installer_is_refused_before_mutation(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    installer = Installer(source, target)

    with (
        _exclusive_install_lock(installer.lock_path),
        pytest.raises(InstallConflict, match="another installer transaction"),
    ):
        installer.install("core")
    assert not (target / "alpha-skill").exists()


def test_unmanaged_same_name_is_refused(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "source"})
    (target / "alpha-skill").mkdir(parents=True)
    (target / "alpha-skill" / "SKILL.md").write_text("unmanaged", encoding="utf-8")
    installer = Installer(source, target)

    assert plan_map(installer) == {"alpha-skill": "CONFLICT_UNMANAGED"}
    with pytest.raises(InstallConflict):
        installer.install("core")
    assert (target / "alpha-skill" / "SKILL.md").read_text(encoding="utf-8") == "unmanaged"


def test_profile_cannot_escape_the_skills_directory(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    profile_path = source / "profiles" / "core.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["skills"] = ["../outside"]
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid skill name"):
        Installer(source, target).install("core")
    assert not target.exists()


def test_diverged_managed_target_is_refused(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    Installer(source, target).install("core")
    (target / "alpha-skill" / "LOCAL.txt").write_text("private edit", encoding="utf-8")

    installer = Installer(source, target)
    assert plan_map(installer) == {"alpha-skill": "DIVERGED_MANAGED"}
    with pytest.raises(InstallConflict):
        installer.install("core")
    assert (target / "alpha-skill" / "LOCAL.txt").read_text(encoding="utf-8") == "private edit"


def test_exact_managed_upgrade_preserves_backup(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"}, version="0.3.0")
    Installer(source, target).install("core")
    write_source(source, {"alpha-skill": "v2"}, version="0.1.1")

    installer = Installer(source, target)
    assert plan_map(installer) == {"alpha-skill": "UPGRADE_MANAGED"}
    receipt = installer.install("core")
    assert "v2" in (target / "alpha-skill" / "SKILL.md").read_text(encoding="utf-8")
    backup = Path(receipt["transaction"]["backupDirectory"])
    assert "v1" in (backup / "alpha-skill" / "SKILL.md").read_text(encoding="utf-8")


def test_failure_before_publish_leaves_target_unchanged(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    Installer(source, target).install("core")
    before = tree_digest(target / "alpha-skill")
    write_source(source, {"alpha-skill": "v2"}, version="0.1.1")

    def fail(phase: str, _name: str | None, _installer: Installer) -> None:
        if phase == "before_publish":
            raise RuntimeError("injected before publish")

    with pytest.raises(RuntimeError, match="injected before publish"):
        Installer(source, target, fault_hook=fail).install("core")
    assert tree_digest(target / "alpha-skill") == before


def test_multi_skill_publish_failure_rolls_back_exact_generation(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1", "beta-skill": "v1"})
    Installer(source, target).install("core")
    before = {name: tree_digest(target / name) for name in ("alpha-skill", "beta-skill")}
    write_source(source, {"alpha-skill": "v2", "beta-skill": "v2"}, version="0.1.1")

    def fail(phase: str, name: str | None, _installer: Installer) -> None:
        if phase == "after_publish" and name == "beta-skill":
            raise RuntimeError("injected after second publish")

    with pytest.raises(RuntimeError, match="injected after second publish"):
        Installer(source, target, fault_hook=fail).install("core")
    assert {name: tree_digest(target / name) for name in before} == before


def test_receipt_failure_restores_when_live_tree_is_still_owned(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    Installer(source, target).install("core")
    before = tree_digest(target / "alpha-skill")
    write_source(source, {"alpha-skill": "v2"}, version="0.1.1")

    def fail(phase: str, _name: str | None, _installer: Installer) -> None:
        if phase == "before_receipt":
            raise RuntimeError("receipt unavailable")

    with pytest.raises(RuntimeError, match="receipt unavailable"):
        Installer(source, target, fault_hook=fail).install("core")
    assert tree_digest(target / "alpha-skill") == before


def test_receipt_replacement_race_is_not_overwritten(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    Installer(source, target).install("core")
    before = tree_digest(target / "alpha-skill")
    write_source(source, {"alpha-skill": "v2"}, version="0.1.1")
    receipt_path = target / ".smart-agentic-engineering-toolkit-install.json"
    foreign_receipt = b'{"foreign":true}\n'

    def replace_receipt(phase: str, _name: str | None, _installer: Installer) -> None:
        if phase == "before_receipt":
            receipt_path.write_bytes(foreign_receipt)

    with pytest.raises((InstallConflict, InstallContainmentError)):
        Installer(source, target, fault_hook=replace_receipt).install("core")
    assert receipt_path.read_bytes() == foreign_receipt
    assert tree_digest(target / "alpha-skill") == before


def test_post_publish_third_party_drift_is_contained_not_overwritten(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    Installer(source, target).install("core")
    write_source(source, {"alpha-skill": "v2"}, version="0.1.1")

    def drift(phase: str, _name: str | None, _installer: Installer) -> None:
        if phase == "before_receipt":
            (target / "alpha-skill" / "THIRD_PARTY.txt").write_text(
                "must survive", encoding="utf-8"
            )
            raise RuntimeError("receipt unavailable after drift")

    with pytest.raises(InstallContainmentError):
        Installer(source, target, fault_hook=drift).install("core")
    assert (target / "alpha-skill" / "THIRD_PARTY.txt").read_text(
        encoding="utf-8"
    ) == "must survive"


def test_generation_changed_after_rename_is_restored_without_publish(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    Installer(source, target).install("core")
    write_source(source, {"alpha-skill": "v2"}, version="0.1.1")

    def drift_moved_generation(phase: str, name: str | None, installer: Installer) -> None:
        if phase == "after_backup" and name == "alpha-skill":
            backup_base = (
                target.parent / f".smart-agentic-engineering-toolkit-backups-{target.name}"
            )
            transaction = next(backup_base.iterdir())
            (transaction / name / "LATE.txt").write_text("late writer", encoding="utf-8")

    with pytest.raises(InstallConflict, match="changed during ownership transfer"):
        Installer(source, target, fault_hook=drift_moved_generation).install("core")
    assert (target / "alpha-skill" / "LATE.txt").read_text(encoding="utf-8") == "late writer"
    assert "v1" in (target / "alpha-skill" / "SKILL.md").read_text(encoding="utf-8")


def test_replacement_after_backup_is_preserved_and_prior_generation_retained(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    Installer(source, target).install("core")
    write_source(source, {"alpha-skill": "v2"}, version="0.1.1")

    def replacement(phase: str, name: str | None, _installer: Installer) -> None:
        if phase == "after_backup" and name == "alpha-skill":
            (target / name).mkdir(parents=True)
            (target / name / "REPLACEMENT.txt").write_text("replacement", encoding="utf-8")

    with pytest.raises(InstallContainmentError, match="replacement appeared before publish"):
        Installer(source, target, fault_hook=replacement).install("core")
    assert (target / "alpha-skill" / "REPLACEMENT.txt").read_text(encoding="utf-8") == "replacement"
    backup_base = target.parent / f".smart-agentic-engineering-toolkit-backups-{target.name}"
    retained = list(backup_base.glob("*/alpha-skill/SKILL.md"))
    assert len(retained) == 1
    assert "v1" in retained[0].read_text(encoding="utf-8")


def test_add_replacement_race_is_refused_without_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})

    def replacement(phase: str, _name: str | None, _installer: Installer) -> None:
        if phase == "before_publish":
            (target / "alpha-skill").mkdir(parents=True)
            (target / "alpha-skill" / "REPLACEMENT.txt").write_text("replacement", encoding="utf-8")

    with pytest.raises(InstallConflict, match="replacement appeared before ADD publish"):
        Installer(source, target, fault_hook=replacement).install("core")
    assert (target / "alpha-skill" / "REPLACEMENT.txt").read_text(encoding="utf-8") == "replacement"


def test_add_dangling_link_race_is_refused_without_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    dangling_destination = tmp_path / "absent-destination"

    def link_race(phase: str, _name: str | None, _installer: Installer) -> None:
        if phase == "before_publish":
            target.mkdir(parents=True, exist_ok=True)
            try:
                (target / "alpha-skill").symlink_to(
                    dangling_destination,
                    target_is_directory=True,
                )
            except OSError as exc:
                pytest.skip(f"directory symlink unavailable on this host: {exc}")

    with pytest.raises(InstallConflict, match="replacement appeared before ADD publish"):
        Installer(source, target, fault_hook=link_race).install("core")
    assert (target / "alpha-skill").is_symlink()


def test_rollback_identifies_the_tree_actually_moved_not_a_prior_hash(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "installed"
    write_source(source, {"alpha-skill": "v1"})
    Installer(source, target).install("core")
    write_source(source, {"alpha-skill": "v2"}, version="0.1.1")

    swapped = False
    published_hold = tmp_path / "published-hold"

    def fail_for_rollback(phase: str, _name: str | None, _installer: Installer) -> None:
        nonlocal swapped
        if phase == "before_receipt":
            raise RuntimeError("receipt unavailable")
        if phase == "before_rollback_move" and not swapped:
            swapped = True
            path = target / "alpha-skill"
            path.rename(published_hold)
            path.mkdir()
            (path / "REPLACEMENT.txt").write_text("replacement", encoding="utf-8")

    with pytest.raises(InstallContainmentError):
        Installer(source, target, fault_hook=fail_for_rollback).install("core")
    replacement_locations = list(tmp_path.rglob("REPLACEMENT.txt"))
    assert len(replacement_locations) == 1
    assert replacement_locations[0].read_text(encoding="utf-8") == "replacement"

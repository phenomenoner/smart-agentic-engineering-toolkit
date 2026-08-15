#!/usr/bin/env python3
"""Recoverable standalone skill installer for selected toolkit profiles."""

from __future__ import annotations

import argparse
import ctypes
import dataclasses
import datetime as dt
import errno
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any

RECEIPT_NAME = ".smart-agentic-engineering-toolkit-install.json"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FaultHook = Callable[[str, str | None, "Installer"], None]


class InstallConflict(RuntimeError):
    """Raised when an unmanaged or locally diverged target would be overwritten."""


class InstallContainmentError(RuntimeError):
    """Raised when rollback cannot safely restore because live state changed."""

    def __init__(self, cause: BaseException, details: list[str]) -> None:
        super().__init__(f"install failed and rollback was contained: {cause}; {'; '.join(details)}")
        self.cause = cause
        self.details = details


@dataclasses.dataclass(frozen=True)
class PlanItem:
    name: str
    classification: str
    source_tree_sha256: str
    current_tree_sha256: str | None
    receipt_tree_sha256: str | None
    current_issue: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "classification": self.classification,
            "sourceTreeSha256": self.source_tree_sha256,
            "currentTreeSha256": self.current_tree_sha256,
            "receiptTreeSha256": self.receipt_tree_sha256,
            "currentIssue": self.current_issue,
        }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path_present(path: Path) -> bool:
    return os.path.lexists(path)


def _is_link_or_reparse(path: Path, entry_stat: os.stat_result | None = None) -> bool:
    details = entry_stat if entry_stat is not None else path.lstat()
    if stat.S_ISLNK(details.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(details, "st_file_attributes", 0) & reparse_flag)


def _rename_noreplace(source: Path, destination: Path) -> None:
    """Atomically rename without replacing an entry that appears at the destination."""

    if os.name == "nt":
        os.rename(source, destination)
        return

    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    if sys.platform.startswith("linux"):
        renameat2 = getattr(libc, "renameat2", None)
        if renameat2 is None:
            raise OSError(errno.ENOTSUP, "renameat2(RENAME_NOREPLACE) is unavailable")
        renameat2.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        renameat2.restype = ctypes.c_int
        result = renameat2(-100, source_bytes, -100, destination_bytes, 1)
    elif sys.platform == "darwin":
        renamex_np = getattr(libc, "renamex_np", None)
        if renamex_np is None:
            raise OSError(errno.ENOTSUP, "renamex_np(RENAME_EXCL) is unavailable")
        renamex_np.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        renamex_np.restype = ctypes.c_int
        result = renamex_np(source_bytes, destination_bytes, 0x00000004)
    else:
        raise OSError(errno.ENOTSUP, "atomic no-replace rename is unavailable on this platform")
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number), str(destination))


@contextmanager
def _exclusive_install_lock(path: Path):
    """Hold a non-blocking host lock for one target-root transaction."""

    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+b")
    locked = False
    try:
        if path.stat().st_size == 0:
            stream.write(b"\0")
            stream.flush()
            os.fsync(stream.fileno())
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except OSError as exc:
            raise InstallConflict(
                f"another installer transaction owns the target lock: {path}"
            ) from exc
        yield
    finally:
        if locked:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


def tree_files(path: Path) -> list[dict[str, Any]]:
    """Return a deterministic manifest and reject links or non-files."""

    if not _path_present(path) or not path.is_dir() or _is_link_or_reparse(path):
        raise ValueError(f"skill source must be a real directory: {path}")
    rows: list[dict[str, Any]] = []

    def visit(directory: Path) -> None:
        with os.scandir(directory) as entries:
            ordered = sorted(entries, key=lambda entry: entry.name)
        for entry in ordered:
            item = Path(entry.path)
            details = entry.stat(follow_symlinks=False)
            if entry.is_symlink() or _is_link_or_reparse(item, details):
                raise ValueError(f"symbolic links or reparse points are not installable: {item}")
            if stat.S_ISDIR(details.st_mode):
                visit(item)
                continue
            if not stat.S_ISREG(details.st_mode):
                raise ValueError(f"unsupported source member: {item}")
            rows.append(
                {
                    "path": item.relative_to(path).as_posix(),
                    "length": details.st_size,
                    "sha256": _sha256_file(item),
                }
            )

    visit(path)
    return rows


def tree_digest(path: Path) -> str:
    payload = json.dumps(tree_files(path), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _stage_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    data = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return temporary


def _publish_json_cas(
    path: Path,
    payload: dict[str, Any],
    *,
    expected_bytes: bytes | None,
    previous_path: Path,
) -> None:
    """Publish JSON only if the exact prior file generation is still current."""

    temporary = _stage_json(path, payload)
    previous_moved = False
    try:
        if _path_present(path):
            previous_path.parent.mkdir(parents=True, exist_ok=True)
            _rename_noreplace(path, previous_path)
            previous_moved = True
            if (
                _is_link_or_reparse(previous_path)
                or not previous_path.is_file()
                or expected_bytes is None
                or previous_path.read_bytes() != expected_bytes
            ):
                try:
                    _rename_noreplace(previous_path, path)
                    previous_moved = False
                except OSError as exc:
                    raise InstallContainmentError(
                        RuntimeError("managed receipt changed before commit"),
                        [f"current receipt retained at {previous_path}: {exc}"],
                    ) from exc
                raise InstallConflict("managed receipt changed before commit; restored")
        elif expected_bytes is not None:
            raise InstallConflict("managed receipt disappeared before commit")

        try:
            _rename_noreplace(temporary, path)
        except OSError as cause:
            if previous_moved:
                try:
                    _rename_noreplace(previous_path, path)
                    previous_moved = False
                except OSError as exc:
                    raise InstallContainmentError(
                        cause,
                        [f"prior receipt retained at {previous_path}: {exc}"],
                    ) from cause
            raise
    finally:
        if _path_present(temporary):
            temporary.unlink()


def _git_head(root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    value = completed.stdout.strip()
    return value or None


class Installer:
    def __init__(
        self,
        source_root: Path,
        target_root: Path,
        *,
        receipt_path: Path | None = None,
        fault_hook: FaultHook | None = None,
    ) -> None:
        self.source_root = Path(source_root).resolve()
        self.target_root = Path(target_root).resolve()
        self.receipt_path = (
            Path(receipt_path).resolve()
            if receipt_path is not None
            else self.target_root / RECEIPT_NAME
        )
        self.lock_path = (
            self.target_root.parent
            / f".smart-agentic-engineering-toolkit-{self.target_root.name}.lock"
        )
        self.fault_hook = fault_hook

    def _fault(self, phase: str, name: str | None = None) -> None:
        if self.fault_hook is not None:
            self.fault_hook(phase, name, self)

    def _profile(self, profile: str) -> dict[str, Any]:
        if NAME_RE.fullmatch(profile) is None:
            raise ValueError(f"invalid profile name: {profile!r}")
        path = self.source_root / "profiles" / f"{profile}.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        skills = document.get("skills")
        if document.get("name") != profile or not isinstance(skills, list) or not skills:
            raise ValueError(f"invalid profile: {path}")
        if len(skills) != len(set(skills)) or any(
            not isinstance(name, str) or NAME_RE.fullmatch(name) is None for name in skills
        ):
            raise ValueError(f"invalid skill name in profile: {path}")
        return document

    def _receipt_snapshot(self) -> tuple[dict[str, Any], bytes | None]:
        if not _path_present(self.receipt_path):
            return {"schemaVersion": 1, "skills": {}}, None
        if _is_link_or_reparse(self.receipt_path) or not self.receipt_path.is_file():
            raise InstallConflict(f"managed receipt is not a regular file: {self.receipt_path}")
        raw = self.receipt_path.read_bytes()
        document = json.loads(raw.decode("utf-8"))
        if document.get("schemaVersion") != 1 or not isinstance(document.get("skills"), dict):
            raise InstallConflict(f"invalid managed receipt: {self.receipt_path}")
        return document, raw

    def _receipt(self) -> dict[str, Any]:
        return self._receipt_snapshot()[0]

    def _plan_from(self, profile: str, receipt: dict[str, Any]) -> list[PlanItem]:
        document = self._profile(profile)
        rows: list[PlanItem] = []
        for name in document["skills"]:
            source = self.source_root / "skills" / name
            source_hash = tree_digest(source)
            target = self.target_root / name
            target_present = _path_present(target)
            current_issue = None
            current_hash = None
            if target_present:
                try:
                    current_hash = tree_digest(target)
                except (OSError, ValueError) as exc:
                    current_issue = str(exc)
            receipt_row = receipt.get("skills", {}).get(name)
            receipt_hash = (
                receipt_row.get("installedTreeSha256") if isinstance(receipt_row, dict) else None
            )
            if not target_present:
                classification = "ADD"
            elif current_issue is not None or receipt_hash is None:
                classification = "CONFLICT_UNMANAGED"
            elif current_hash != receipt_hash:
                classification = "DIVERGED_MANAGED"
            elif current_hash == source_hash:
                classification = "EXACT"
            else:
                classification = "UPGRADE_MANAGED"
            rows.append(
                PlanItem(
                    name=name,
                    classification=classification,
                    source_tree_sha256=source_hash,
                    current_tree_sha256=current_hash,
                    receipt_tree_sha256=receipt_hash,
                    current_issue=current_issue,
                )
            )
        return rows

    def plan(self, profile: str = "core") -> list[PlanItem]:
        return self._plan_from(profile, self._receipt())

    @staticmethod
    def _plan_identity(
        items: list[PlanItem],
    ) -> list[tuple[str, str, str, str | None, str | None, str | None]]:
        return [
            (
                item.name,
                item.classification,
                item.source_tree_sha256,
                item.current_tree_sha256,
                item.receipt_tree_sha256,
                item.current_issue,
            )
            for item in items
        ]

    def install(self, profile: str = "core") -> dict[str, Any]:
        with _exclusive_install_lock(self.lock_path):
            return self._install_locked(profile)

    def _install_locked(self, profile: str) -> dict[str, Any]:
        receipt_before, receipt_bytes_before = self._receipt_snapshot()
        initial_plan = self._plan_from(profile, receipt_before)
        conflicts = [
            item
            for item in initial_plan
            if item.classification in {"CONFLICT_UNMANAGED", "DIVERGED_MANAGED"}
        ]
        if conflicts:
            detail = ", ".join(f"{item.name}:{item.classification}" for item in conflicts)
            raise InstallConflict(f"installation refused: {detail}")

        changed = [item for item in initial_plan if item.classification != "EXACT"]
        if not changed:
            return receipt_before

        transaction_id = (
            dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
            + "-"
            + uuid.uuid4().hex
        )
        control_parent = self.target_root.parent
        staging_root = (
            control_parent
            / f".smart-agentic-engineering-toolkit-staging-{self.target_root.name}"
            / transaction_id
        )
        backup_root = (
            control_parent
            / f".smart-agentic-engineering-toolkit-backups-{self.target_root.name}"
            / transaction_id
        )
        failed_root = (
            control_parent
            / f".smart-agentic-engineering-toolkit-contained-{self.target_root.name}"
            / transaction_id
        )
        published: list[dict[str, Any]] = []

        try:
            staging_root.mkdir(parents=True, exist_ok=False)
            for item in changed:
                source = self.source_root / "skills" / item.name
                staged = staging_root / item.name
                shutil.copytree(source, staged, symlinks=True)
                if tree_digest(staged) != item.source_tree_sha256:
                    raise RuntimeError(f"staged bytes drifted for {item.name}")
            self._fault("after_stage", None)

            live_receipt, live_receipt_bytes = self._receipt_snapshot()
            if live_receipt != receipt_before or live_receipt_bytes != receipt_bytes_before:
                raise InstallConflict("managed receipt changed after the initial plan")
            live_plan = self._plan_from(profile, live_receipt)
            if self._plan_identity(live_plan) != self._plan_identity(initial_plan):
                raise InstallConflict("live targets or source changed after the initial plan")
            self._fault("before_publish", None)

            self.target_root.mkdir(parents=True, exist_ok=True)
            for item in changed:
                target = self.target_root / item.name
                staged = staging_root / item.name
                backup = backup_root / item.name
                old_exists = _path_present(target)
                if old_exists and item.current_tree_sha256 is None:
                    raise InstallConflict(
                        f"replacement appeared before ADD publish for {item.name}; not modified"
                    )
                if old_exists:
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    _rename_noreplace(target, backup)
                    self._fault("after_backup", item.name)
                    moved_hash = tree_digest(backup)
                    if moved_hash != item.current_tree_sha256:
                        if _path_present(target):
                            raise InstallContainmentError(
                                RuntimeError("target changed during ownership transfer"),
                                [f"replacement appeared for {item.name}; prior bytes retained at {backup}"],
                            )
                        _rename_noreplace(backup, target)
                        raise InstallConflict(
                            f"target {item.name} changed during ownership transfer; restored"
                        )
                try:
                    _rename_noreplace(staged, target)
                except FileExistsError as exc:
                    if old_exists:
                        raise InstallContainmentError(
                            RuntimeError("replacement appeared before publish"),
                            [f"did not overwrite replacement target for {item.name}"],
                        ) from exc
                    raise InstallConflict(
                        f"replacement appeared before ADD publish for {item.name}; not modified"
                    ) from exc
                published.append(
                    {
                        "name": item.name,
                        "target": target,
                        "backup": backup,
                        "oldExists": old_exists,
                        "publishedHash": item.source_tree_sha256,
                    }
                )
                self._fault("after_publish", item.name)

            self._fault("before_receipt", None)
            profile_document = self._profile(profile)
            receipt = dict(receipt_before)
            skills = dict(receipt_before.get("skills", {}))
            for item in initial_plan:
                source = self.source_root / "skills" / item.name
                target = self.target_root / item.name
                live_hash = tree_digest(target)
                if live_hash != item.source_tree_sha256:
                    raise InstallContainmentError(
                        RuntimeError("published target drifted before receipt"),
                        [f"retained current live bytes for {item.name}"],
                    )
                skills[item.name] = {
                    "profile": profile,
                    "sourceTreeSha256": item.source_tree_sha256,
                    "installedTreeSha256": live_hash,
                    "files": tree_files(source),
                }
            receipt.update(
                {
                    "schemaVersion": 1,
                    "toolkitVersion": profile_document.get("toolkitVersion"),
                    "sourceCommit": _git_head(self.source_root),
                    "sourceRoot": str(self.source_root),
                    "targetRoot": str(self.target_root),
                    "profile": profile,
                    "skills": skills,
                    "transaction": {
                        "id": transaction_id,
                        "completedAt": dt.datetime.now(dt.UTC).isoformat(),
                        "backupDirectory": str(backup_root),
                        "previousReceipt": str(
                            self.receipt_path.with_name(
                                f".{self.receipt_path.name}.{transaction_id}.previous"
                            )
                        )
                        if receipt_bytes_before is not None
                        else None,
                        "changed": [item.name for item in changed],
                    },
                }
            )
            previous_receipt = self.receipt_path.with_name(
                f".{self.receipt_path.name}.{transaction_id}.previous"
            )
            _publish_json_cas(
                self.receipt_path,
                receipt,
                expected_bytes=receipt_bytes_before,
                previous_path=previous_receipt,
            )
            return receipt
        except BaseException as cause:
            containment: list[str] = []
            for row in reversed(published):
                name = row["name"]
                target: Path = row["target"]
                backup: Path = row["backup"]
                if _path_present(target):
                    destination = failed_root / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    self._fault("before_rollback_move", name)
                    try:
                        _rename_noreplace(target, destination)
                    except OSError as exc:
                        containment.append(f"could not isolate live {name}: {exc}")
                        continue
                    try:
                        moved_hash = tree_digest(destination)
                    except (OSError, ValueError) as exc:
                        moved_hash = None
                        containment.append(
                            f"moved live {name} could not be identified and was retained at "
                            f"{destination}: {exc}"
                        )
                    if moved_hash != row["publishedHash"]:
                        try:
                            _rename_noreplace(destination, target)
                        except OSError as exc:
                            containment.append(
                                f"live replacement for {name} was retained at {destination}: {exc}"
                            )
                        containment.append(
                            f"live {name} changed after publish and was not overwritten"
                        )
                        continue
                if row["oldExists"] and _path_present(backup):
                    if _path_present(target):
                        containment.append(
                            f"could not restore {name} because a replacement target exists"
                        )
                    else:
                        try:
                            _rename_noreplace(backup, target)
                        except OSError as exc:
                            containment.append(f"could not restore {name}: {exc}")
            if containment:
                raise InstallContainmentError(cause, containment) from cause
            raise


def _print_plan(items: list[PlanItem]) -> None:
    print(json.dumps({"plan": [item.as_dict() for item in items]}, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--profile", default="core")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--apply", action="store_true", help="apply the plan; default is dry-run")
    args = parser.parse_args(argv)
    installer = Installer(
        args.source_root,
        args.target_root,
        receipt_path=args.receipt,
    )
    try:
        if args.apply:
            print(json.dumps(installer.install(args.profile), indent=2, ensure_ascii=False))
        else:
            _print_plan(installer.plan(args.profile))
    except (InstallConflict, InstallContainmentError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

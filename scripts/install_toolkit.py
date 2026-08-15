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
import sys
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any

RECEIPT_NAME = ".smart-agentic-engineering-toolkit-install.json"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IGNORED_TREE_PARTS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    ".codegraph",
    "__pycache__",
    "build",
    "dist",
}
IGNORED_TREE_FILE_NAMES = {".coverage", ".DS_Store", "Thumbs.db"}
IGNORED_TREE_FILE_SUFFIXES = {".pyc", ".pyo"}
FaultHook = Callable[[str, str | None, "Installer"], None]
RFC3339_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
RECEIPT_ROOT_FIELDS = {
    "schemaVersion",
    "toolkitVersion",
    "sourceCommit",
    "sourceRoot",
    "targetRoot",
    "profile",
    "skills",
    "transaction",
}
RECEIPT_SKILL_FIELDS = {
    "profile",
    "sourceTreeSha256",
    "installedTreeSha256",
    "files",
}
RECEIPT_FILE_FIELDS = {"path", "length", "sha256"}
RECEIPT_TRANSACTION_FIELDS = {
    "id",
    "completedAt",
    "backupDirectory",
    "previousReceipt",
    "changed",
}


class InstallConflict(RuntimeError):
    """Raised when an unmanaged or locally diverged target would be overwritten."""


class InstallContainmentError(RuntimeError):
    """Raised when rollback cannot safely restore because live state changed."""

    def __init__(self, cause: BaseException, details: list[str]) -> None:
        super().__init__(
            f"install failed and rollback was contained: {cause}; {'; '.join(details)}"
        )
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


def _is_exact_regular_file(path: Path, expected_bytes: bytes) -> bool:
    try:
        return (
            _path_present(path)
            and not _is_link_or_reparse(path)
            and path.is_file()
            and path.read_bytes() == expected_bytes
        )
    except OSError:
        return False


def _is_link_or_reparse(path: Path, entry_stat: os.stat_result | None = None) -> bool:
    details = entry_stat if entry_stat is not None else path.lstat()
    if stat.S_ISLNK(details.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(details, "st_file_attributes", 0) & reparse_flag)


def _is_ignored_tree_member(relative: Path) -> bool:
    return (
        any(part in IGNORED_TREE_PARTS or part.endswith(".egg-info") for part in relative.parts)
        or relative.name in IGNORED_TREE_FILE_NAMES
        or relative.suffix.lower() in IGNORED_TREE_FILE_SUFFIXES
    )


def _copytree_ignore(source: Path) -> Callable[[str, list[str]], set[str]]:
    def ignored(directory: str, names: list[str]) -> set[str]:
        relative_directory = Path(directory).relative_to(source)
        return {name for name in names if _is_ignored_tree_member(relative_directory / name)}

    return ignored


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
            if _is_ignored_tree_member(item.relative_to(path)):
                continue
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
    payload = _manifest_bytes(tree_files(path))
    return hashlib.sha256(payload).hexdigest()


def _manifest_bytes(files: list[dict[str, Any]]) -> bytes:
    return json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _receipt_error(errors: list[dict[str, str]], code: str, path: str, message: str) -> None:
    errors.append({"code": code, "path": path, "message": message})


def _closed_fields(
    errors: list[dict[str, str]],
    document: dict[str, Any],
    allowed: set[str],
    path: str,
) -> None:
    unknown = sorted(set(document) - allowed)
    if unknown:
        _receipt_error(
            errors,
            "INSTALL_RECEIPT_SHAPE",
            path,
            f"unknown fields are not accepted: {unknown}",
        )


def _valid_receipt_path(value: str) -> bool:
    if (
        not value
        or "\\" in value
        or value.startswith("/")
        or re.match(r"^[A-Za-z]:", value) is not None
    ):
        return False
    parsed = PurePosixPath(value)
    return (
        parsed.as_posix() == value
        and not parsed.is_absolute()
        and all(part not in {"", ".", ".."} for part in parsed.parts)
    )


def validate_install_receipt(document: object) -> list[dict[str, str]]:
    """Validate closed receipt shape and cross-field provenance semantics."""

    errors: list[dict[str, str]] = []
    if not isinstance(document, dict):
        _receipt_error(
            errors,
            "INSTALL_RECEIPT_SHAPE",
            "receipt",
            "install receipt must be an object",
        )
        return errors

    _closed_fields(errors, document, RECEIPT_ROOT_FIELDS, "receipt")
    required_root = RECEIPT_ROOT_FIELDS - {"sourceCommit"}
    missing_root = sorted(required_root - set(document))
    if missing_root:
        _receipt_error(
            errors,
            "INSTALL_RECEIPT_SHAPE",
            "receipt",
            f"required fields are missing: {missing_root}",
        )

    if document.get("schemaVersion") != 1:
        _receipt_error(
            errors,
            "INSTALL_RECEIPT_SHAPE",
            "schemaVersion",
            "schemaVersion must equal 1",
        )
    for field in ("toolkitVersion", "sourceRoot", "targetRoot", "profile"):
        value = document.get(field)
        if not isinstance(value, str) or not value:
            _receipt_error(
                errors,
                "INSTALL_RECEIPT_SHAPE",
                field,
                f"{field} must be a nonempty string",
            )
    if document.get("sourceCommit") is not None:
        _receipt_error(
            errors,
            "INSTALL_RECEIPT_AUTHORITY",
            "sourceCommit",
            "standalone receipts do not attest a Git commit or release tag",
        )
    for field in document:
        normalized = field.lower()
        if field not in RECEIPT_ROOT_FIELDS and any(
            token in normalized for token in ("authority", "commit", "tag", "verified")
        ):
            _receipt_error(
                errors,
                "INSTALL_RECEIPT_AUTHORITY",
                field,
                "unmodeled authority or release provenance is not accepted",
            )

    skills = document.get("skills")
    if not isinstance(skills, dict):
        _receipt_error(
            errors,
            "INSTALL_RECEIPT_SHAPE",
            "skills",
            "skills must be an object",
        )
        skills = {}
    elif not skills:
        _receipt_error(
            errors,
            "INSTALL_RECEIPT_SHAPE",
            "skills",
            "skills must contain at least one managed row",
        )

    for name, row in skills.items():
        row_path = f"skills.{name}"
        if not isinstance(name, str) or NAME_RE.fullmatch(name) is None:
            _receipt_error(
                errors,
                "INSTALL_RECEIPT_SHAPE",
                row_path,
                "skill names must be kebab-case",
            )
        if not isinstance(row, dict):
            _receipt_error(
                errors,
                "INSTALL_RECEIPT_SHAPE",
                row_path,
                "skill receipt row must be an object",
            )
            continue
        _closed_fields(errors, row, RECEIPT_SKILL_FIELDS, row_path)
        missing = sorted(RECEIPT_SKILL_FIELDS - set(row))
        if missing:
            _receipt_error(
                errors,
                "INSTALL_RECEIPT_SHAPE",
                row_path,
                f"required fields are missing: {missing}",
            )
        profile = row.get("profile")
        if not isinstance(profile, str) or NAME_RE.fullmatch(profile) is None:
            _receipt_error(
                errors,
                "INSTALL_RECEIPT_SHAPE",
                f"{row_path}.profile",
                "skill profile must be kebab-case",
            )

        source_digest = row.get("sourceTreeSha256")
        installed_digest = row.get("installedTreeSha256")
        if source_digest != installed_digest:
            _receipt_error(
                errors,
                "INSTALL_RECEIPT_TREE_RELATION",
                row_path,
                "a successful skill row must have equal source and installed tree digests",
            )

        files = row.get("files")
        if not isinstance(files, list):
            _receipt_error(
                errors,
                "INSTALL_RECEIPT_SHAPE",
                f"{row_path}.files",
                "files must be an array",
            )
            continue
        paths: list[str] = []
        manifest_shape_valid = True
        for index, file_row in enumerate(files):
            file_path = f"{row_path}.files[{index}]"
            if not isinstance(file_row, dict):
                manifest_shape_valid = False
                _receipt_error(
                    errors,
                    "INSTALL_RECEIPT_SHAPE",
                    file_path,
                    "file row must be an object",
                )
                continue
            _closed_fields(errors, file_row, RECEIPT_FILE_FIELDS, file_path)
            if set(file_row) != RECEIPT_FILE_FIELDS:
                manifest_shape_valid = False
                _receipt_error(
                    errors,
                    "INSTALL_RECEIPT_SHAPE",
                    file_path,
                    "file row must contain exactly path, length, and sha256",
                )
            path_value = file_row.get("path")
            length = file_row.get("length")
            digest = file_row.get("sha256")
            if not isinstance(path_value, str) or not _valid_receipt_path(path_value):
                _receipt_error(
                    errors,
                    "INSTALL_RECEIPT_MANIFEST_PATH",
                    f"{file_path}.path",
                    "file path must be a canonical relative POSIX path",
                )
            else:
                paths.append(path_value)
            if (
                not isinstance(length, int)
                or isinstance(length, bool)
                or length < 0
                or not isinstance(digest, str)
                or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            ):
                manifest_shape_valid = False
                _receipt_error(
                    errors,
                    "INSTALL_RECEIPT_SHAPE",
                    file_path,
                    "file length and sha256 must describe exact bytes",
                )

        if len(paths) != len(set(paths)):
            _receipt_error(
                errors,
                "INSTALL_RECEIPT_MANIFEST_DUPLICATE",
                f"{row_path}.files",
                "manifest paths must be unique",
            )
        if paths != sorted(paths, key=lambda value: tuple(value.split("/"))):
            _receipt_error(
                errors,
                "INSTALL_RECEIPT_MANIFEST_ORDER",
                f"{row_path}.files",
                "manifest paths must use canonical traversal order",
            )
        if manifest_shape_valid:
            canonical_digest = hashlib.sha256(_manifest_bytes(files)).hexdigest()
            if source_digest != canonical_digest or installed_digest != canonical_digest:
                _receipt_error(
                    errors,
                    "INSTALL_RECEIPT_MANIFEST_DIGEST",
                    row_path,
                    "declared tree digests must equal the canonical digest of files",
                )

    transaction = document.get("transaction")
    if not isinstance(transaction, dict):
        _receipt_error(
            errors,
            "INSTALL_RECEIPT_SHAPE",
            "transaction",
            "transaction must be an object",
        )
        return errors
    _closed_fields(errors, transaction, RECEIPT_TRANSACTION_FIELDS, "transaction")
    missing_transaction = sorted(RECEIPT_TRANSACTION_FIELDS - set(transaction))
    if missing_transaction:
        _receipt_error(
            errors,
            "INSTALL_RECEIPT_SHAPE",
            "transaction",
            f"required fields are missing: {missing_transaction}",
        )

    for field in ("id", "backupDirectory"):
        value = transaction.get(field)
        if not isinstance(value, str) or not value:
            _receipt_error(
                errors,
                "INSTALL_RECEIPT_SHAPE",
                f"transaction.{field}",
                f"transaction {field} must be a nonempty string",
            )
    previous_receipt = transaction.get("previousReceipt")
    if previous_receipt is not None and not isinstance(previous_receipt, str):
        _receipt_error(
            errors,
            "INSTALL_RECEIPT_SHAPE",
            "transaction.previousReceipt",
            "previousReceipt must be a string or null",
        )

    completed_at = transaction.get("completedAt")
    timestamp_valid = (
        isinstance(completed_at, str) and RFC3339_RE.fullmatch(completed_at) is not None
    )
    if timestamp_valid:
        try:
            parsed_time = dt.datetime.fromisoformat(completed_at)
            timestamp_valid = parsed_time.tzinfo is not None and parsed_time.utcoffset() is not None
        except ValueError:
            timestamp_valid = False
    if not timestamp_valid:
        _receipt_error(
            errors,
            "INSTALL_RECEIPT_COMPLETED_AT",
            "transaction.completedAt",
            "completedAt must be a timezone-bearing RFC 3339 timestamp",
        )

    changed = transaction.get("changed")
    receipt_profile = document.get("profile")
    changed_shape_valid = (
        isinstance(changed, list)
        and bool(changed)
        and all(isinstance(name, str) and NAME_RE.fullmatch(name) is not None for name in changed)
    )
    if changed_shape_valid:
        changed_shape_valid = len(changed) == len(set(changed))
    if not changed_shape_valid:
        _receipt_error(
            errors,
            "INSTALL_RECEIPT_SHAPE",
            "transaction.changed",
            "changed must be a nonempty unique array of kebab-case skill names",
        )
    else:
        for name in changed:
            row = skills.get(name)
            if not isinstance(row, dict) or row.get("profile") != receipt_profile:
                _receipt_error(
                    errors,
                    "INSTALL_RECEIPT_TRANSACTION_RELATION",
                    "transaction.changed",
                    "each changed skill must exist and use the receipt profile",
                )
                break
    return errors


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _stage_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    data = _json_bytes(payload)
    with temporary.open("wb") as stream:
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

    def _profile_snapshot(self, profile: str) -> tuple[dict[str, Any], bytes]:
        """Read and validate one immutable profile generation.

        The profile bytes and parsed document travel with the install
        transaction.  Receipt construction must not reread the live checkout
        after staging, because a source/profile edit at that point belongs to
        a later generation.
        """

        if NAME_RE.fullmatch(profile) is None:
            raise ValueError(f"invalid profile name: {profile!r}")
        path = self.source_root / "profiles" / f"{profile}.json"
        raw = path.read_bytes()
        document = json.loads(raw.decode("utf-8"))
        skills = document.get("skills")
        if document.get("name") != profile or not isinstance(skills, list) or not skills:
            raise ValueError(f"invalid profile: {path}")
        if len(skills) != len(set(skills)) or any(
            not isinstance(name, str) or NAME_RE.fullmatch(name) is None for name in skills
        ):
            raise ValueError(f"invalid skill name in profile: {path}")
        return document, raw

    def _receipt_snapshot(self) -> tuple[dict[str, Any], bytes | None]:
        if not _path_present(self.receipt_path):
            return {"schemaVersion": 1, "skills": {}}, None
        if _is_link_or_reparse(self.receipt_path) or not self.receipt_path.is_file():
            raise InstallConflict(f"managed receipt is not a regular file: {self.receipt_path}")
        raw = self.receipt_path.read_bytes()
        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InstallConflict(f"invalid managed receipt: {self.receipt_path}: {exc}") from exc
        semantic_errors = validate_install_receipt(document)
        if semantic_errors:
            codes = sorted({error["code"] for error in semantic_errors})
            raise InstallConflict(
                f"invalid managed receipt: {self.receipt_path}: semantic errors={codes}"
            )
        return document, raw

    def _receipt(self) -> dict[str, Any]:
        return self._receipt_snapshot()[0]

    def _plan_from(
        self,
        profile: str,
        receipt: dict[str, Any],
        *,
        profile_document: dict[str, Any] | None = None,
    ) -> list[PlanItem]:
        document = self._profile(profile) if profile_document is None else profile_document
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

    def _compensate_published_receipt(
        self,
        *,
        transaction_id: str,
        published_bytes: bytes,
        previous_bytes: bytes | None,
        previous_path: Path,
    ) -> list[str]:
        """Restore/remove only the exact receipt generation published by this transaction."""

        details: list[str] = []
        if not _path_present(self.receipt_path):
            if previous_bytes is None:
                return details
            if not _is_exact_regular_file(previous_path, previous_bytes):
                return [f"prior receipt could not be identified at {previous_path}"]
            try:
                _rename_noreplace(previous_path, self.receipt_path)
            except OSError as exc:
                return [f"prior receipt retained at {previous_path}: {exc}"]
            return details

        if _is_link_or_reparse(self.receipt_path) or not self.receipt_path.is_file():
            return [f"foreign receipt entry retained at {self.receipt_path}"]
        try:
            observed_bytes = self.receipt_path.read_bytes()
        except OSError as exc:
            return [f"current receipt could not be identified and was retained: {exc}"]
        if observed_bytes != published_bytes:
            return ["foreign receipt bytes replaced the published receipt and were retained"]

        quarantine = self.receipt_path.with_name(
            f".{self.receipt_path.name}.{transaction_id}.failed"
        )
        try:
            _rename_noreplace(self.receipt_path, quarantine)
        except OSError as exc:
            return [f"published receipt could not be acquired for compensation: {exc}"]

        try:
            moved_bytes = quarantine.read_bytes()
        except OSError as exc:
            return [
                f"moved receipt could not be identified and was retained at {quarantine}: {exc}"
            ]
        if moved_bytes != published_bytes:
            try:
                _rename_noreplace(quarantine, self.receipt_path)
            except OSError as exc:
                details.append(f"foreign receipt retained at {quarantine}: {exc}")
            details.append("receipt generation changed during compensation")
            return details

        if previous_bytes is None:
            if _path_present(self.receipt_path):
                details.append("foreign receipt appeared during ADD compensation and was retained")
            try:
                quarantine.unlink()
            except OSError as exc:
                details.append(f"published ADD receipt retained at {quarantine}: {exc}")
            return details

        if not _is_exact_regular_file(previous_path, previous_bytes):
            return [
                f"prior receipt could not be identified; published bytes retained at {quarantine}"
            ]
        try:
            _rename_noreplace(previous_path, self.receipt_path)
        except OSError as exc:
            return [
                f"prior receipt retained at {previous_path}: {exc}",
                f"published bytes retained at {quarantine}",
            ]
        try:
            quarantine.unlink()
        except OSError as exc:
            details.append(f"compensated receipt copy retained at {quarantine}: {exc}")
        return details

    def install(self, profile: str = "core") -> dict[str, Any]:
        with _exclusive_install_lock(self.lock_path):
            return self._install_locked(profile)

    def _install_locked(self, profile: str) -> dict[str, Any]:
        receipt_before, receipt_bytes_before = self._receipt_snapshot()
        profile_document, profile_bytes = self._profile_snapshot(profile)
        initial_plan = self._plan_from(
            profile,
            receipt_before,
            profile_document=profile_document,
        )
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

        transaction_id = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex
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
        staged_generations: dict[str, tuple[str, list[dict[str, Any]]]] = {}
        post_commit_receipt_contained = False

        try:
            staging_root.mkdir(parents=True, exist_ok=False)
            for item in changed:
                source = self.source_root / "skills" / item.name
                staged = staging_root / item.name
                shutil.copytree(
                    source,
                    staged,
                    symlinks=True,
                    ignore=_copytree_ignore(source),
                )
                staged_manifest = tree_files(staged)
                staged_hash = tree_digest(staged)
                if staged_hash != item.source_tree_sha256:
                    raise RuntimeError(f"staged bytes drifted for {item.name}")
                staged_generations[item.name] = (staged_hash, staged_manifest)
            self._fault("after_stage", None)

            live_receipt, live_receipt_bytes = self._receipt_snapshot()
            if live_receipt != receipt_before or live_receipt_bytes != receipt_bytes_before:
                raise InstallConflict("managed receipt changed after the initial plan")
            live_profile, live_profile_bytes = self._profile_snapshot(profile)
            if live_profile_bytes != profile_bytes:
                raise InstallConflict("profile changed after the initial plan")
            live_plan = self._plan_from(
                profile,
                live_receipt,
                profile_document=live_profile,
            )
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
                                [
                                    f"replacement appeared for {item.name}; prior bytes retained at {backup}"
                                ],
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
            receipt = dict(receipt_before)
            skills = dict(receipt_before.get("skills", {}))
            for item in initial_plan:
                target = self.target_root / item.name
                live_hash = tree_digest(target)
                if item.classification == "EXACT":
                    # Keep the previously committed row.  It already binds
                    # the unchanged target to its receipt generation; the
                    # live source checkout may legitimately advance after the
                    # plan and must not be reread into this receipt.
                    continue
                staged_hash, staged_manifest = staged_generations[item.name]
                if staged_hash != item.source_tree_sha256 or live_hash != staged_hash:
                    raise InstallContainmentError(
                        RuntimeError("published target differs from staged generation"),
                        [f"retained current live bytes for {item.name}"],
                    )
                skills[item.name] = {
                    "profile": profile,
                    "sourceTreeSha256": staged_hash,
                    "installedTreeSha256": live_hash,
                    "files": staged_manifest,
                }
            receipt.update(
                {
                    "schemaVersion": 1,
                    "toolkitVersion": profile_document.get("toolkitVersion"),
                    "sourceCommit": None,
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
            semantic_errors = validate_install_receipt(receipt)
            if semantic_errors:
                codes = sorted({error["code"] for error in semantic_errors})
                raise RuntimeError(f"refusing to publish invalid install receipt: {codes}")
            published_receipt_bytes = _json_bytes(receipt)
            _publish_json_cas(
                self.receipt_path,
                receipt,
                expected_bytes=receipt_bytes_before,
                previous_path=previous_receipt,
            )
            try:
                self._fault("after_receipt_commit", None)
                post_commit_failures: list[str] = []
                if (
                    not _path_present(self.receipt_path)
                    or _is_link_or_reparse(self.receipt_path)
                    or not self.receipt_path.is_file()
                ):
                    post_commit_failures.append("published receipt is not a regular file")
                else:
                    try:
                        if self.receipt_path.read_bytes() != published_receipt_bytes:
                            post_commit_failures.append("published receipt bytes changed")
                    except OSError as exc:
                        post_commit_failures.append(f"published receipt could not be read: {exc}")
                for item in changed:
                    target = self.target_root / item.name
                    staged_hash, _staged_manifest = staged_generations[item.name]
                    try:
                        live_hash = tree_digest(target)
                    except (OSError, ValueError) as exc:
                        post_commit_failures.append(
                            f"published target {item.name} could not be identified: {exc}"
                        )
                        continue
                    if live_hash != staged_hash:
                        post_commit_failures.append(
                            f"published target {item.name} changed before success return"
                        )
                if post_commit_failures:
                    raise RuntimeError("; ".join(post_commit_failures))
            except BaseException as post_commit_cause:
                receipt_containment = self._compensate_published_receipt(
                    transaction_id=transaction_id,
                    published_bytes=published_receipt_bytes,
                    previous_bytes=receipt_bytes_before,
                    previous_path=previous_receipt,
                )
                if receipt_containment:
                    post_commit_receipt_contained = True
                    raise InstallContainmentError(
                        post_commit_cause,
                        receipt_containment,
                    ) from post_commit_cause
                raise
            return receipt
        except BaseException as cause:
            if post_commit_receipt_contained:
                raise
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

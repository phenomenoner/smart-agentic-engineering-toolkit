# Installation and update

## Codex plugin

Clone a tagged release, then register that checkout as a non-default local marketplace and install
the plugin it exposes:

```powershell
codex plugin marketplace add <repository-root>
codex plugin add smart-agentic-engineering-toolkit@smart-agentic-engineering-toolkit
```

Confirm the configured source with `codex plugin list`, fully restart Codex Desktop, and use a new
task for behavior verification. Do not treat the configuration row, plugin catalog, or an old task
as proof that the new skills were loaded.

For an update, move the local checkout to the intended tagged release, confirm that no local edits
would be overwritten, reinstall the plugin, restart the app, and verify from a new task. Release
plugin versions change when bytes change; local development builds should replace a single
`+codex.<cachebuster>` suffix rather than stacking suffixes.

## Standalone Agent Skills projection

The standalone installer copies one profile into a chosen skills directory. It is dry-run by
default:

```powershell
.\scripts\install.ps1 -TargetRoot <skills-directory> -Profile core
.\scripts\install.ps1 -TargetRoot <skills-directory> -Profile core -Apply
```

On Linux hosts:

```sh
./scripts/install.sh <skills-directory> core
./scripts/install.sh <skills-directory> core --apply
```

The installer records an exact managed receipt in the target directory, stages complete trees,
holds one OS-backed lock per target root, uses atomic no-replace renames, and commits the receipt
only when its exact prior bytes still match. Before returning success it re-reads the exact receipt
bytes and every changed target digest while holding that lock. On mismatch it restores/removes only
the receipt generation it just published by exact-byte compare-and-swap; foreign receipt or target
bytes are retained and reported. Once a foreign current receipt is identified, target compensation
also stops so the installer cannot roll back bytes beneath another receipt owner. It retains prior
managed generations and receipts and refuses unmanaged, linked/reparse, semantically invalid, or
locally diverged same-name targets. If ownership
changes during rollback, it moves first, identifies the tree actually moved, and contains the
failure without overwriting foreign bytes. There is no force-overwrite mode. A platform without a
supported atomic no-replace rename fails closed before publish. The lock coordinates conforming
installers; it does not claim that an arbitrary writer cannot mutate the target after return.

The public receipt schema validates closed vocabulary and local shape. Machine acceptance also
requires zero errors from `scripts.install_toolkit.validate_install_receipt`, which checks timestamp,
manifest/path/digest, profile, and transaction relations. Schema success alone is shape evidence,
not provenance acceptance. Standalone receipts deliberately set `sourceCommit` to `null`: their
per-file and tree digests attest exact installed bytes, while Git commit/tag identity belongs to
separately verified release provenance.

Profiles are classifications, not mandatory chains. Install `core` first unless a host-specific
adapter is actually needed; optional profiles are listed in `profiles/`.

## Duplicate migration

If the host already has loose skills with the same names, do not overwrite or delete them during
initial plugin proof. First prove a uniquely new toolkit skill in a fresh task, then follow the
recoverable procedure in [`migration.md`](migration.md).

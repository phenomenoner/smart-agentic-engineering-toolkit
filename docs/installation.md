# Installation and update

## Choose the host-native route

The canonical repository is the only writable source. A plugin cache, installed skill tree, tap, marketplace row, or generated package is an installed projection, never a second source.

Choose one distribution route per host:

| Host | Preferred route | Verification |
| --- | --- | --- |
| Codex App | Install the repository as a Codex plugin. | Full desktop restart and a fresh task that exercises one changed behavior. |
| Hermes Agent | Install a managed toolkit profile into the active profile's native skills root, or use `hermes skills install` for one independently selected skill. | Enabled-local listing and a fresh Hermes one-shot session. |
| Other Agent Skills-compatible harness | Use the harness's native skill manager when it preserves complete skill directories; otherwise use the standalone profile installer against that harness's user skill root. | Native discovery plus one positive and one negative trigger in a fresh context. |
| Harness without Agent Skills support | Do not claim installation. Build and document a host adapter, or keep the toolkit as reference material only. | Adapter-specific tests and fresh-context behavior evidence. |

Do not project the same toolkit-owned skill through multiple routes in one host. Inspect conflicts first, preserve unmanaged or diverged copies, and retire an old projection only after the replacement is proven.

## Codex App plugin

For a published release, use the exact commit that passed its source/release gate and remote CI;
its tag must resolve to the same bytes. For an authorized local development install, use the locally
validated canonical commit and a single cachebuster suffix. Remote publication, remote CI, and a
formal release review are not prerequisites for that narrower claim. Register the selected checkout
or exact staged projection as a non-default local marketplace and install the plugin it exposes:

```powershell
codex plugin marketplace add <repository-root>
codex plugin add smart-agentic-engineering-toolkit@smart-agentic-engineering-toolkit
```

Confirm the configured source with `codex plugin list`, fully restart Codex Desktop, and use a new task for behavior verification. Do not treat the configuration row, plugin catalog, or an old task as proof that the new skills were loaded.

For a long task, record the exact toolkit version and canonical commit it loaded. Do not silently mix rules from another cached or newly released version into accepted task history. Adopt changed workflow rules through an explicit rebind checkpoint, or install/restart and verify them in a new task.

For an update, move the local checkout to the intended exact gated commit or its corresponding tag, confirm that no local edits would be overwritten, reinstall the plugin, restart the app, and verify from a new task. Release plugin versions change when bytes change; local development builds should replace a single `+codex.<cachebuster>` suffix rather than stacking suffixes.

## Hermes Agent native skills

Hermes discovers local Agent Skills under `~/.hermes/skills/<category>/<skill-name>/SKILL.md`; no plugin registration is required. For a coherent toolkit profile, prefer the repository's managed standalone installer because it performs a dry run, records exact installed bytes, and refuses unmanaged or diverged collisions:

```sh
./scripts/install.sh "$HOME/.hermes/skills" core
./scripts/install.sh "$HOME/.hermes/skills" core --apply
```

For one independently triggered skill instead of a profile, Hermes also supports a registry identifier or a direct public `SKILL.md` URL:

```sh
hermes skills install <owner/repository/skill> --yes
# or
hermes skills install <https-url-to-SKILL.md> --yes
```

After installation:

```sh
hermes skills list --source local --enabled-only
hermes skills config
hermes chat -q "/engineering-implementation Explain this skill's direct path and risk-local finding rule. Do not modify files."
```

Use `hermes skills config` to disable a redundant or conflicting projection; do not delete an unknown local skill merely because its name or trigger overlaps. The `hermes chat -q` command starts a fresh Hermes session, follows the [upstream fresh-session skill test](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/guides/work-with-skills.md#4-test-it), and explicitly invokes the installed slash-command skill; run a nearby negative trigger separately. Do not use `hermes --skills <name> -z` as pickup evidence: [affected Hermes versions can run the prompt without injecting the named skill](https://github.com/NousResearch/hermes-agent/issues/71759). An existing long-lived session may still carry its old policy binding even though the filesystem changed.

## Other Agent Skills-compatible harnesses

Prefer the host's native skill manager when it:

1. keeps each complete skill directory together, including `references/`, `scripts/`, `templates/`, and `assets/`;
2. exposes enabled/disabled state and conflict inspection;
3. does not turn an installed projection into a writable canonical source; and
4. can verify behavior in a fresh context.

When no suitable native manager exists, point the standalone installer at that harness's documented user skill root:

```powershell
.\scripts\install.ps1 -TargetRoot <skills-directory> -Profile core
.\scripts\install.ps1 -TargetRoot <skills-directory> -Profile core -Apply
```

On Linux hosts:

```sh
./scripts/install.sh <skills-directory> core
./scripts/install.sh <skills-directory> core --apply
```

Install `core` first. Add `navigation`, `windows`, provider adapters, or other optional profiles only when their triggers are actually present. A profile is a classification, not a mandatory lifecycle.

## Standalone installer guarantees

The standalone installer copies one profile into a chosen skills directory. It is dry-run by default. It records an exact managed receipt in the target directory, stages complete trees, holds one OS-backed lock per target root, uses atomic no-replace renames, and commits the receipt only when its exact prior bytes still match. Before returning success it re-reads the exact receipt bytes and every changed target digest while holding that lock.

On mismatch it restores or removes only the receipt generation it just published by exact-byte compare-and-swap; foreign receipt or target bytes are retained and reported. Once a foreign current receipt is identified, target compensation also stops so the installer cannot roll back bytes beneath another receipt owner. It retains prior managed generations and receipts and refuses unmanaged, linked or reparse, semantically invalid, or locally diverged same-name targets. If ownership changes during rollback, it moves first, identifies the tree actually moved, and contains the failure without overwriting foreign bytes. There is no force-overwrite mode. A platform without a supported atomic no-replace rename fails closed before publish. The lock coordinates conforming installers; it does not claim that an arbitrary writer cannot mutate the target after return.

The public receipt schema validates closed vocabulary and local shape. Machine acceptance also requires zero errors from `scripts.install_toolkit.validate_install_receipt`, which checks timestamp, manifest/path/digest, profile, and transaction relations. Schema success alone is shape evidence, not provenance acceptance. Standalone receipts deliberately set `sourceCommit` to `null`: their per-file and tree digests attest exact installed bytes, while Git commit/tag identity belongs to separately verified release provenance.

## Conflict migration and updates

If the host already has loose skills with the same names, run the managed installer without `--apply` first. Do not overwrite or delete conflicts during initial proof. Prove one uniquely changed toolkit behavior in a fresh context, then follow the recoverable, one-skill-at-a-time procedure in [`migration.md`](migration.md).

Report installation and activation separately. A local installation is verified when the first
three identities agree; claim fresh-host activation only after the fourth is observed:

1. canonical source commit or immutable release tag;
2. package/profile version and exact installed bytes;
3. host-native enabled/discovery state; and
4. fresh-context behavior evidence.

# Migration and local cutover

## Host-neutral conflict rule

A host-native plugin, managed profile, tap, loose skill directory, and manual copy are alternative projections of one canonical source. Do not expose the same toolkit-owned skill through more than one route.

Before changing a live host:

1. Inventory every same-name and semantically overlapping skill.
2. Run the toolkit installer in dry-run mode against the active skill root.
3. Classify each row as absent, exact, managed upgrade, unmanaged, diverged, linked/reparse, or ambiguous.
4. Apply only absent, exact, or receipt-backed managed rows. Stop on every other class.
5. Preserve the prior complete managed generation and receipt until fresh-session verification succeeds.

A duplicate name is not the only conflict. A host-global rule also conflicts when it universally requires a plan, specification, TDD, WAL, worktree, subagent, full suite, reviewer, or fail-closed disposition where this toolkit preserves a direct or risk-local path. Disable or narrow the broader rule in the host's native configuration; do not delete unknown source bytes merely to win precedence.

## Codex App plugin migration

1. Keep existing loose skills unchanged while installing the plugin from the exact gated checkout or release tag.
2. Fully restart Codex Desktop and create a fresh task.
3. Prove plugin loading with a uniquely identifiable toolkit behavior; configuration or catalog visibility alone is insufficient.
4. Move one proven duplicate out of the live loose-skill root, restart, and run direct plus non-activation cases.
5. Stop on unmanaged or diverged bytes. Do not use a generic force switch.
6. Keep the prior complete loose generation until representative real use succeeds.

## Hermes Agent native-skill migration

1. Confirm the active profile and skill root; the normal user root is `~/.hermes/skills`.
2. Run `./scripts/install.sh "$HOME/.hermes/skills" <profile>` without `--apply` and inspect every row.
3. A receipt-backed `UPGRADE_MANAGED` is safe to apply only when current bytes still equal the prior receipt. Unmanaged or diverged rows remain blocked.
4. Use `hermes skills config` or the equivalent profile configuration to disable semantically overlapping broad rules. Prefer disabling over deleting so rollback stays available.
5. Apply the managed profile, repeat dry-run, and require every row to become exact.
6. Confirm discovery with `hermes skills list --source local --enabled-only`, then start a fresh Hermes session and exercise one identifiable positive case plus one direct-path non-activation case.
7. Keep source validation, install receipt, host discovery, fresh-session load, and real task behavior as separate claims.

## Other Agent Skills-compatible harnesses

Prefer the host's native skill manager when it preserves complete skill directories, supports enabled/disabled state, and has a reversible update path. Otherwise use the standalone profile installer against that harness's documented user skill root.

When only manual projection is available:

- copy one complete skill directory at a time;
- record source release and tree digest outside the installed copy;
- never edit the installed copy as canonical source;
- verify the host's actual discovery and trigger behavior in a fresh context;
- retain the prior generation until rollback is no longer needed.

If the host cannot load Agent Skills-compatible directories or cannot establish precedence between duplicate skills, return `INCOMPLETE`; a copied directory is not an installation proof.

## From Chatgpt-Codex-App-Plus

Migration occurs only after the exact canonical remote commit passes its source/release gate and CI,
and local fresh-task behavior is proved from that commit. In an isolated clean branch, replace
migrated general-engineering source directories with one entry pinned to the exact commit. A later
tag or GitHub Release must resolve to those same bytes; neither substitutes for the fresh-task proof.
Update all manifests, locks, installers, workflows, tests, pages, README and notice references
together. Keep Context Canvas and product-specific skills in their canonical homes. Public
synchronization remains allow-listed and cannot advance the toolkit pin automatically.

## Recovery

An install receipt binds the selected toolkit/profile generation, target path, and per-file/tree
hashes. It does not attest a Git commit or release tag, even when the source is a clean checkout;
`sourceCommit` is `null` and Git identity remains separately verified release provenance. Treat a
receipt as machine-acceptable only after both closed-schema validation and the public semantic
validator succeed. Restore a prior managed generation only if the live target still equals the
failed transaction's exact published tree. If another actor changed it, contain the failure and
report the conflict without destructive rollback.

# Migration and local cutover

## From loose Codex skills

1. Inventory every scope and classify same-name targets before installation.
2. Install the plugin while loose skills remain unchanged.
3. Restart Codex Desktop and create a fresh task. Prove the plugin using a uniquely new skill; do not
   accept config or catalog visibility alone.
4. Preserve exact recoverable backups for same-name loose skills and their hashes/receipts.
5. Move one proven duplicate out of the live skill root, restart, and run its direct and
   non-activation cases. Stop on unmanaged or diverged bytes.
6. Keep the prior complete generation through observed use. Do not delete a private overlay.

The standalone installer is intended for hosts that consume skill directories directly. It does not
edit Codex plugin caches and a generic force switch cannot bypass divergence checks.

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

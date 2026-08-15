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

Migration occurs only after a toolkit tag and local fresh-task proof. In an isolated clean branch,
replace migrated general-engineering source directories with one pinned toolkit entry. Update all
manifests, locks, installers, workflows, tests, pages, README and notice references together. Keep
Context Canvas and product-specific skills in their canonical homes. Public synchronization remains
allow-listed and cannot advance the toolkit pin automatically.

## Recovery

An install receipt binds release tag, source commit, selected profile, target path, and per-file
hashes. Restore a prior managed generation only if the live target still equals the failed
transaction's exact published tree. If another actor changed it, contain the failure and report the
conflict without destructive rollback.

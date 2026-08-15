---
name: codex-app-mcp-update
description: Safely update an existing local Codex Desktop plugin whose MCP server comes from a package or tool environment, keeping package, marketplace source, installed plugin, live process, and task identities distinct. Use for local MCP upgrades, bundled-skill or tool-surface changes, cachebuster refreshes, Windows live-process locks or partial uv tool installs, restart/new-task decisions, and native post-update verification. Do not use for initial plugin scaffolding or official marketplace submission.
license: MIT
metadata:
  toolkit-version: "0.1.0"
  toolkit-phase: "codex-maintenance"
  toolkit-contribution-protocol: "v1"
---

# Codex App MCP Update
<!-- TOOLKIT-CONTRIBUTION-PROTOCOL:v1 -->

Update the executable package and the Codex plugin as one evidence-bound cutover. Treat a running
task as an old immutable consumer until a fresh task proves otherwise.

Use the system `plugin-creator` skill as well when changing plugin structure, marketplace entries,
or cachebuster metadata. This skill adds runtime-install and live-process safety; it does not replace
the scaffold/update rules there.

## Keep launch and installation identities separate

Record these before changing anything:

1. candidate artifact path, length, SHA-256, and package version;
2. installed tool-environment package version and console entrypoints;
3. candidate marketplace root, source manifest version, and declared MCP command, arguments, and
   environment;
4. configured marketplace name and exact resolved root;
5. installed/enabled Codex plugin version, cached/source path, and bundled skill/config digests;
6. live frontend and lifecycle-owner process identities plus the current task's already-loaded tool
   catalog.

When the product has an explicit setup-time runtime provisioner, require its ready runtime binding
before asking the user to restart. This moves normal task startup onto an attach-only path and keeps
task teardown from owning the durable process; keep self-start in the MCP launcher as recovery, not
the only normal lifecycle.

Do not infer one identity from another. Equal version strings do not prove equal bytes: a configured
marketplace can point at a checkout while setup expects the marketplace bundled in a wheel. A new
wheel with an unchanged plugin cachebuster can leave the bundled skill and MCP configuration stale.
A new plugin installation does not hot-update an already-open task.

## Update workflow

### 1. Inventory without mutation

- Read `codex plugin marketplace list`, `codex plugin list --json`, the selected source manifest,
  and the package manager's installed-tool listing.
- On Windows, inspect exact executable paths and command lines for the target MCP process. Do not
  search only by `python.exe` name.
- Identify whether the marketplace points to a wheel-bundled source or a live repository. A product
  installer may compute the expected version from its wheel while Codex still installs from an
  older repository-backed marketplace.

### 2. Prove the candidate away from the live environment

- Verify the artifact hash before installation.
- Install it into an isolated environment and read back the package version, bundled plugin
  manifest, required entrypoints, and generated assets.
- Run the smallest real MCP lifecycle that proves startup, tool discovery, dependencies, one state
  transition/readback, and clean close.
- Execute the selected plugin's declared MCP command and arguments unchanged. Do not add a
  convenient `--database`, embedded-host, test-mode, or alternate entrypoint flag unless that exact
  value is also in the installed declaration. Read back the same runtime-owner mode the plugin will
  use. If it requires a supervisor, start from no Ready discovery and prove the adapter provisions
  or attaches the intended exact owner and runtime home.
- Bump the plugin version/cachebuster whenever bundled skills, MCP configuration, starter prompts,
  or other plugin-consumed bytes change. Add a regression using the exact predecessor version.
- Ensure the configured marketplace's resolved root is the exact candidate source before invoking
  a reinstall. If the same marketplace name points elsewhere, explicitly replace or fail closed;
  never accept a matching version from the other root.

### 3. Choose the cutover boundary

- Ask `Do we really need this to make things happen?` and `Is there a simpler and more direct way?`
  about the host outcome and proposed package/marketplace/process cutover. Prefer an existing
  managed install, restart, or new-task primitive when it meets the invariant; count package,
  process, cache, rollback, authority, recovery, and failure-state cost before retaining a new
  mechanism. This does not authorize the cutover.
- If no process owns the tool environment, install normally.
- On Windows, do not run `uv tool install --force` against a live MCP tool environment. The failure
  can be non-atomic: package or dependency metadata may be removed before a locked executable or
  compiled module prevents completion.
- Include a detached supervisor, worker, or other lifecycle owner in that live-process inventory;
  closing only the stdio frontend may leave the tool environment locked.
- Prefer closing Codex completely, then performing the update from an external terminal.
- If the user explicitly authorizes an in-App controlled cutover and the task can survive losing
  only this MCP transport, read [Windows live MCP cutover](references/windows-live-mcp-cutover.md)
  before acting. Resolve exact root and descendant paths, stop only that tree, then cleanly rebuild.
- Never broadly stop Python, WSL, Codex, or unrelated MCP processes.

### 4. Install package and plugin

- Use the package manager and Codex CLI/product installer; do not hand-edit `config.toml` or
  marketplace JSON.
- For a healthy idle environment, install the exact artifact once.
- After any partial installation, wait until locks are gone, uninstall the one exact tool
  environment, and rebuild it cleanly. Do not layer ad-hoc `pip install` repairs over missing
  metadata or locked compiled dependencies.
- Run the product's setup command when available. Otherwise reinstall with
  `codex plugin add <plugin>@<marketplace>` after confirming the marketplace source and version.

### 5. Verify both seams

Before restarting Codex, verify:

- package version, dependency consistency, and the complete entrypoint list;
- enabled plugin selector, expected version/cachebuster, and expected marketplace source;
- source/cached plugin skill and MCP-config bytes or digests matching the selected marketplace;
- a fresh child-process MCP lifecycle using the exact installed manifest command and arguments;
- installer receipt, including whether configuration changed and restart is required.

When configuration, plugin bytes, skills, or MCP executable bytes changed:

1. fully restart Codex Desktop;
2. create a new task/session;
3. if the host defers MCP tools, use its native tool search only to load the exact capability tool;
4. make one native call to the updated MCP's capability tool;
5. read back the expected package/tool-surface/skill identity.

Tool search, CLI help, config text, plugin catalog visibility, or startup alone is not native host
proof. A deferred-search hit is only a loading step; require the subsequent MCP response. A
same-task `Transport closed` response after cutover is expected and does not prove reconnection.

## Diagnose common mismatches

- **Package new, plugin old:** stale cachebuster or active marketplace source.
- **Plugin new, current task old:** restart the App and use a new task.
- **Windows access denied during tool install:** live process lock; audit for partial removal before
  retrying.
- **Setup expects new version but installs old:** marketplace points to a different/stale source.
- **Setup passes but fresh tasks omit the server:** compare the exact manifest launch contract with
  the preflight argv and runtime-owner mode; an embedded substitute can hide a missing supervisor.
- **Version matches but skill/config differs:** the configured marketplace root or cache entry is
  not the candidate identity; replace the source and cachebuster, then reinstall.
- **Catalog shows the tool but native call fails:** transport/runtime is not verified; test from a
  fresh task after restart.
- **Direct tool name is absent but exact deferred search succeeds:** call the loaded native
  capability tool once. Treat only that response as proof; absence before the host's normal deferred
  loading step is not an installation failure.
- **Native call passes but a detached owner vanishes at task teardown:** inspect its exact process
  identity and lifecycle receipt. Some hosts kill their whole descendant tree; distinguish native
  availability and successor recovery from an unproved same-process-survival claim.

Treat `omitting MCP server without an exact ready client`, no callable tool after the host's exact
deferred-loading step, or an immediate launcher exit as an incomplete installation even when setup,
package, and plugin-version checks are green. Diagnose the first failing launch seam before asking
for another restart or task.

## Record the handoff

Retain exact hashes, versions, source paths, setup/preflight receipt, process-cutover scope, and the
fresh-task native result. Put rebuildable diagnostics under the user's cleanroom location. Keep
local installation proof separate from deployment, provider, and official marketplace claims.

## Contribution protocol

When real use of this skill exposes a material improvement, missing safeguard, conflict, or retirement candidate, do not silently patch an installed copy, plugin cache, or generated projection. The toolkit repository is the canonical writable owner for toolkit-owned behavior.

1. Record a public-safe counterexample or redacted reproducer; the canonical commit; the current skill version and SHA-256; expected versus observed behavior; materiality; and compatibility, authority, safety, evidence, dependency-conflict, or retirement impact.
2. Prepare an exact unified diff against canonical source, the smallest activation, non-activation, or workflow eval that distinguishes the change, and provenance or change notes.
3. If GitHub writes are explicitly authorized, open a draft pull request against the canonical owner and read back its identity and state. Otherwise return a PR-ready packet and explicitly offer to open the draft pull request. Never claim that a draft pull request exists without that readback.
4. Route external dependency behavior changes to the actual upstream. A toolkit pull request may change only its pin, integration metadata, conflict handling, or retirement state unless ownership has explicitly transferred.

Material means that activation, non-activation, authority, safety, compatibility, observable workflow behavior, evidence quality, dependency conflict, or supported or retired status changes. A wording preference alone does not create PR churn.

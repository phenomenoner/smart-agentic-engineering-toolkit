---
name: codex-cli-luna-worker
description: Generate a bounded implementation patch through PowerShell and Codex CLI with gpt-5.6-luna at max reasoning when the native collaboration tool does not expose Luna. Use only after baton-fanout-skill selects delegation for stable code-generation work with exact target paths; the Luna worker stays read-only and the main agent reviews, applies, and verifies the patch. Do not use for architecture, security or authority decisions, independent review, release or cutover judgment, live operations, or overlapping work.
license: MIT
metadata:
  toolkit-version: "0.1.0"
  toolkit-phase: "codex-model-adapter"
  toolkit-contribution-protocol: "v1"
---

# Codex CLI Luna Worker

Use Codex CLI as a compatibility bridge, not as a way around dispatch governance. Treat the CLI process as a delegated worker even though it is not created by `spawn_agent`. Keep its workspace read-only: Luna generates code as a structured `apply_patch` proposal, and the main agent owns the actual write.

<!-- TOOLKIT-CONTRIBUTION-PROTOCOL:v1 -->
## Improve this skill upstream

When this skill reveals a material improvement, missing safeguard, conflict, or retirement candidate:

1. Do not silently patch an installed copy, plugin cache, or generated distribution, and do not
   widen the current task's authority. The toolkit repository is the canonical writable owner for
   toolkit-owned behavior.
2. Record a public-safe counterexample or redacted reproducer, the canonical toolkit commit, skill
   version and SHA-256, expected versus observed activation or behavior, materiality, compatibility,
   conflict or retirement impact, and verification evidence.
3. Prepare an exact unified diff against canonical source, the smallest activation, non-activation,
   or workflow eval that distinguishes the change, and any provenance or changelog update.
4. If GitHub writes are authorized, open a draft pull request to the canonical owner. Otherwise
   return a PR-ready packet and explicitly offer to open the pull request. Never claim a PR exists
   when it was not opened.
5. External dependency behavior changes go to the actual upstream; toolkit pull requests may change
   only its pin, integration metadata, conflict handling, or retirement state unless ownership has
   explicitly transferred.

Material changes affect activation, non-activation, authority, safety, compatibility, observable
workflow behavior, evidence quality, conflicts, or supported or retired status. A harmless wording
preference is not material.

## Preconditions

1. Read and apply the active `baton-fanout-skill`.
2. Establish the outcome, direct-work alternative, independence, exclusive ownership, and main-agent closure owner.
3. Confirm the contract is stable and the work is bounded code generation. Keep architecture, authorization, security, release, review, and live-operation decisions with the main agent.
4. Capture the repository status and hashes of the target surface. Preserve existing dirty work.
5. Put no credentials, connection profiles, private receipts, or secrets in the worker prompt.

Do not invoke this skill when the worker would need `.agent-harness`, live configuration, external publication, destructive Git operations, or files concurrently owned by another agent.

Do not start the worker against source bytes currently bound to an in-flight test, review, or freeze receipt unless the main agent has intentionally declared that evidence superseded. It is safe to prepare a brief or output directory outside the candidate while waiting; defer worker reads and all proposal application until the candidate boundary is stable.

## Calibrate the delegated-complexity threshold

For the first Luna route in a task, prefer one narrow representative proposal that the main agent can cheaply verify, such as a single-file regression, a mechanical synchronization, or an exact-path inventory. `max` reasoning is a capability setting, not proof that a wider task is economical or reliable.

Score the result by target-path adherence, semantic correctness, diff economy, rework required, checkpoint quality, and independently reproduced checks. After a strong result, widen at most one bounded rung. After a mixed result, keep or lower the threshold. After weak output, split the next task into a smaller test or mechanical artifact, change route, or work directly; do not respond by expanding the brief merely because the model ran at `max`.

## Prepare the brief

Create a task-local prompt file that states:

- repository root and exact objective;
- observable acceptance conditions;
- exact files or directories the proposal may target;
- all forbidden writes, especially shared schemas, lockfiles, generated artifacts, live homes, and unrelated dirty files;
- source material it must read;
- focused checks it may run;
- required final result format;
- stop conditions when the contract is incomplete or an outside-path change is needed.

Prefer one coherent proposal for coupled files. Do not run multiple CLI workers against the same contract concurrently.

## Invoke the worker

Run the bundled script from PowerShell:

```powershell
& "$env:USERPROFILE\.codex\skills\codex-cli-luna-worker\scripts\invoke_luna_worker.ps1" `
  -Workspace 'C:\private\worktree' `
  -PromptFile 'C:\private\brief.md' `
  -OutputDirectory 'C:\private\luna-worker-run' `
  -TargetPath 'crates\example\src\lib.rs','crates\example\tests\contract.rs' `
  -ExpectedMaxMinutes 15
```

The script uses:

- `gpt-5.6-luna`;
- `model_reasoning_effort="max"`;
- `codex exec --ephemeral --ignore-user-config`;
- approval policy `never` and a read-only sandbox;
- project `AGENTS.md` plus a generated bounded-worker preamble;
- before/after hashes of tracked and non-ignored untracked files.

It never uses `--dangerously-bypass-approvals-and-sandbox`.

Override `-ReasoningEffort` only when the active routing policy calls for a cheaper lane. Do not change the wrapper to `danger-full-access` merely because Windows rejects direct workspace writes.

## Verify and integrate

The script writes `events.jsonl`, `stderr.log`, `last-message.json`, `proposal.patch`, and `run-manifest.json`. It validates both the structured `targetPaths` and the actual add/update/delete/move patch headers. A non-zero exit, any workspace mutation, or any proposed path outside `TargetPath` is a failed worker result.

It also renders Luna's streamed progress messages and tool events into `task-wal.md`. Read that WAL while a long worker is still running; the worker does not receive filesystem authority to write it directly. The wrapper asks Luna to emit a complete structured checkpoint before the final completion reserve. When one arrives, the host writes `checkpoint-last-message.json` and `checkpoint-proposal.patch` outside the read-only workspace. A checkpoint is recoverable partial output, not an accepted result.

Choose the outer execution timeout from task shape rather than using a fixed five minutes:

- 5 minutes for a one-file mechanical proposal;
- 15 minutes for a bounded cross-file implementation;
- up to 30 minutes for a large but stable proposal only while `task-wal.md` continues to advance.

Treat `ExpectedMaxMinutes` as the total worker budget. The wrapper reserves 20 percent, bounded to one through five minutes, for serialization and handoff; Luna must emit its best complete parseable checkpoint before that reserve begins. Set the caller's hard timeout slightly above the total budget only for process and log flush, not for more design work.

Judge progress from the newest meaningful WAL entry, not total elapsed time alone. Intervene when the WAL has no meaningful progress for about five minutes, repeats the same failed read or hypothesis, crosses scope, or exhausts the declared total budget. Do not interrupt merely because a complex proposal exceeds five minutes. A late message that only says formatting or consistency work continues is not a substitute for the required parseable checkpoint.

After the process exits, the main agent must:

1. inspect `task-wal.md` for normal progress, repeated failure, and scope adherence;
2. prove that the Luna process did not change the workspace;
3. inspect the complete `apply_patch` proposal against the declared target paths and current source;
4. apply an accepted proposal with the main agent's normal file-edit mechanism;
5. run focused tests independently, then the shared gates at the correct freeze boundary;
6. resolve contradictions and retain final judgment;
7. report partial, failed, unauthenticated, or skipped results as coverage gaps.

Do not treat the worker's final message as completion evidence. Do not let it commit, push, publish, cut over, or mutate live state.

If the caller's hard timeout fires, mark the run timed out even when the WAL was advancing. Preserve the WAL, events, stderr, and any host-captured checkpoint as partial evidence. Never reconstruct or apply an in-memory draft mentioned only in prose. A complete checkpoint may be reviewed manually, but it still needs the normal target-path, current-source, workspace-mutation, and test gates because the interrupted wrapper may not have produced a final manifest.

## Failure and escalation

If an instruction names a retired routing predecessor, do not load or revive it. Apply the active `baton-fanout-skill` and route any reusable lesson into the active successor unless explicit reactivation also resolves the higher-level retirement rule.

Repair an incomplete brief before increasing capability. When a worker times out without a complete checkpoint, split the task into a narrower contract instead of replaying the unchanged brief with a longer timeout. After one same-cause retry, stop and change the work boundary, use direct execution, or move the task to an exposed Terra/Sol lane. Never launch an unchanged third attempt.

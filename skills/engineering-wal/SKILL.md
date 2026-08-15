---
name: engineering-wal
description: Maintain a compact durable work log for multi-session, multi-agent, compaction-prone, long-running, risky, interrupted, or deliberately blocked engineering work. Use it to preserve objective, scope and authority, repository identity and dirty state, decisions, blockers, evidence pointers, next safe action, and stop conditions. Do not use for a small single-turn task or as a substitute for executable proof, source, authorization, secrets storage, raw receipts, Context Canvas, or project planning documents.
license: MIT
metadata:
  toolkit-version: "0.1.0"
  toolkit-phase: "continuity"
  toolkit-contribution-protocol: "v1"
---

# Engineering WAL

Use a write-ahead log as the minimum durable map when work must survive interruption. Keep it small
enough that a new agent can recover the state without replaying the full conversation.

<!-- TOOLKIT-CONTRIBUTION-PROTOCOL:v1 -->
## Improve this skill upstream

When this skill reveals a material improvement, missing safeguard, conflict with another toolkit
skill, or retirement candidate:

1. Do not silently patch an installed copy, plugin cache, or generated distribution, and do not
   widen the current task's authority.
2. Record the canonical toolkit commit, skill version and SHA-256, a redacted reproducer, expected
   versus observed activation or behavior, materiality, conflict or retirement impact, and
   verification evidence.
3. Prepare an exact unified diff against canonical source, the smallest discriminating eval or test,
   and any provenance or changelog update.
4. If GitHub writes are authorized, open a draft pull request to the canonical owner. Otherwise
   present or retain the PR-ready packet and explicitly offer to open it. Never claim a PR exists
   when it was not opened.
5. For an external dependency, change toolkit pin or integration metadata here and route source
   behavior changes to its actual upstream only when separately authorized.

Material changes affect activation, authority, safety, compatibility, observable workflow,
evidence quality, conflicts, or supported status. A harmless wording preference is not material.

## Decide whether a WAL is warranted

Create or update one when at least one condition is material:

- the task will cross sessions, compaction, restart, or an external wait;
- multiple agents or worktrees need a shared bounded map;
- a risky or long-running action needs an exact resume/stop boundary;
- the task is blocked and must preserve the next safe action;
- decisions or evidence would be expensive or unsafe to reconstruct.

Skip it for a short self-contained edit, a disposable brainstorm, or a request that already has a
sufficient durable project record. Do not create ceremony merely because software is involved.

## Choose authority and location

Use the repository's existing `WAL.md`, handoff, or project convention when one exists. Otherwise use
a clearly named repository or task artifact within authorized writable scope. Never write a private
machine path, credential, raw prompt/output, secret, or large log into public source.

The WAL summarizes; it does not become the source of truth for code, tests, releases, or live state.
Record exact pointers and hashes when material, then verify the referenced bytes before relying on
them after a pause.

Context Canvas may add a semantic map or historical snapshots when a trusted identity and callable
tools exist. Canvas failure must not block the WAL or core work. Never guess, copy, or derive a Canvas
identity. AAR and knowledge graphs are also optional navigation/compute layers, not WAL authority.

## Minimal record

Maintain only what a successor needs:

```text
Objective:
Scope and explicit authority:
Repository / branch / commit / dirty summary:
Current state:
Decisions and rationale:
Necessity decision when material (outcome/invariant; both questions; selected alternative; added state/authority/recovery/failure-state cost):
Active blockers and stop conditions:
Evidence pointers and hashes:
Work in flight and exclusive owners:
Next safe action:
Claims not yet proven:
```

Prefer append-only dated entries when older states matter. Correct a factual mistake visibly; do not
rewrite a frozen review or release record. When a new candidate invalidates old executable evidence,
record that relation instead of silently reusing it.

For a material mechanism decision recorded here, preserve the compact answers to `Do we really need
this to make things happen?` and `Is there a simpler and more direct way?`, plus the selected
deletion, manual, embedding/ephemeral, platform-primitive, or retained-mechanism outcome and its
complexity, authority, recovery, and failure-state cost. Point to the canonical specification; the
WAL is not a second design gate and remains optional for short work.
The detailed canonical owner is `engineering-specification`; this continuity surface only records
its decision and later evidence.

## Update boundaries

Update at intentional boundaries: implementation start, material decision, new blocker, review
freeze, compaction/handoff, terminal long-run receipt, or release/cutover decision. Do not update for
every shell command or unchanged status poll.

Before pausing, ensure the WAL answers:

- What exact bytes/state are authoritative now?
- What is safe to do next?
- What action is forbidden until a gate changes?
- What can be rebuilt or cleaned later?

At task completion, mark the objective outcome and remaining external gaps. Do not claim an external
effect from a planned or configured state.

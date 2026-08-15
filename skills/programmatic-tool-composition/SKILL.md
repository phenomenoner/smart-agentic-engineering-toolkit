---
name: programmatic-tool-composition
description: Compose multiple independent read-only or pure tool operations inside Codex App's programmatic runner using bounded JavaScript, parallel calls, reduction, and output shaping while preserving tool-specific constraints and effect boundaries. Use when a task needs three or more similar reads, independent calls across sources, joins/filtering/ranking, or large-output reduction that would otherwise require repeated model round trips. Do not use for a single call, sequential dependencies, long-running supervision, subagent fan-out, user or thread messages, external writes, approval-sensitive action, or tools that forbid parallelism.
license: MIT
metadata:
  toolkit-version: "0.1.0"
  toolkit-phase: "codex-optimization"
  toolkit-contribution-protocol: "v1"
---

# Programmatic Tool Composition
<!-- TOOLKIT-CONTRIBUTION-PROTOCOL:v1 -->

Use the runtime's programmatic composition surface (`functions.exec` in Codex App when exposed) for bounded mechanical orchestration. Typed tools and the host remain the authority boundary.

## Choose composition only when it pays

Use a direct tool call when one call is enough, a later call depends on model judgment over the first result, the result is already small, or the operation has an external effect.

Compose when all of the following hold:

- at least three similar reads, or at least two independent reads whose results require a join or deterministic reduction;
- every nested call is pure or read-only;
- the live tool instructions permit programmatic use and the selected concurrency shape;
- call count, output size, timeout, and partial-failure behavior can be bounded in advance;
- composition reduces model round trips or resident context enough to justify the wrapper.

When uncertain about a tool's effect class or parallel-safety, call it directly.

## Preserve the host and tool contracts

- Treat the live tool schema and its instructions as authoritative. A composition wrapper grants no extra permission.
- Keep messages, thread changes, email, deploys, purchases, trades, authentication changes, destructive filesystem actions, publication, and other approval-sensitive or external writes as direct typed host calls.
- Do not hide `apply_patch`, mutating shell commands, or connector writes inside a composition program.
- Do not compose tools that require a dedicated call boundary or explicitly forbid parallel calls. In particular, keep web access on its required standalone path.
- Use `baton-fanout-skill` for subagents; this skill is single-agent tool orchestration, not delegation.
- Use `long-run-supervisor` for commands expected to exceed five minutes; this skill is not a polling or waiting loop.
- Use the relevant product skill, such as `aar-operations`, for product-specific handles, grants, revisions, reconciliation, and delivery boundaries.
- Use `aar-operations` and its `aar_program_workspace_*` tools when a callable AAR surface is
  available and persistent live Python objects, NumPy/pandas, helper functions, or multi-turn
  analysis state materially help. Inspect AAR capabilities first and require an executed dependency
  smoke before assuming NumPy or pandas is installed. Keep external tool calls in the host, transfer
  only bounded structured values, and never treat the programmable workspace as a typed-tool bridge,
  security sandbox, or authority surface. If AAR is unavailable, use a one-shot host transform or an
  explicitly selected alternative instead of silently routing to a retired plugin.

## Define a bounded contract

Before writing the program, identify:

```text
goal and derived output
input list and maximum item count
allowed tool methods
read-only assertion
parallelism limit
time or call budget
partial-failure policy
maximum returned preview
```

Do not load the whole tool catalog into model-visible output. If discovery is needed, filter `ALL_TOOLS` locally by a narrow name or description pattern and emit only the small matching set.

## Compose in Codex App JavaScript

The program runs in a fresh V8 isolate, not Node.js.

- Call nested tools through `await tools.<tool_name>(...)`.
- Await every promise; unawaited work is discarded when the isolate ends.
- Use `Promise.all` only for independent, provider-safe reads that must all succeed.
- Use `Promise.allSettled` when a bounded partial result is acceptable, and preserve each failure explicitly.
- Transform, filter, sort, join, validate, and truncate results before emitting them.
- Emit model-visible output with `text`, `image`, `audio`, or `generatedImage`; do not depend on `console`.
- Use `store` and `load` only for serializable task-local state needed by a later composition call. Do not treat stored state as authority or durable evidence.
- Do not use unavailable Node filesystem, process, network, or module APIs.

A safe read-only pattern is:

```javascript
const inputs = boundedInputs.slice(0, maxItems);
const settled = await Promise.allSettled(
  inputs.map(input => tools.some_read_tool({ id: input }))
);

const ok = [];
const failures = [];
for (let i = 0; i < settled.length; i++) {
  const item = settled[i];
  if (item.status === "fulfilled") ok.push(normalize(item.value));
  else failures.push({ input: inputs[i], error: String(item.reason) });
}

const result = validateAndReduce(ok);
text(JSON.stringify({ result, failures, complete: failures.length === 0 }));
```

Adapt names to the actual typed schema; never invent a callable.

## Validate before returning

Confirm that:

- nested call count stayed within the declared bound;
- all nested methods were read-only and parallel-safe;
- the derived output satisfies its type, filter, sort, and size invariants;
- errors remain distinguishable from empty or negative results;
- partial results are labeled partial and list failed inputs;
- emitted output is a bounded summary, not a raw repository, log set, or tool catalog;
- no external effect occurred inside the composition wrapper.

If composition fails because a callable is unavailable, the schema is ambiguous, or a provider rejects the batch, fall back to the smallest direct-call sequence. Do not retry an unchanged composition repeatedly.

## Contribution protocol

When real use of this skill exposes a material improvement, missing safeguard, conflict, or retirement candidate, do not silently patch an installed copy, plugin cache, or generated projection. The toolkit repository is the canonical writable owner for toolkit-owned behavior.

1. Record a public-safe counterexample or redacted reproducer; the canonical commit; the current skill version and SHA-256; expected versus observed behavior; materiality; and compatibility, authority, safety, evidence, dependency-conflict, or retirement impact.
2. Prepare an exact unified diff against canonical source, the smallest activation, non-activation, or workflow eval that distinguishes the change, and provenance or change notes.
3. If GitHub writes are explicitly authorized, open a draft pull request against the canonical owner and read back its identity and state. Otherwise return a PR-ready packet and explicitly offer to open the draft pull request. Never claim that a draft pull request exists without that readback.
4. Route external dependency behavior changes to the actual upstream. A toolkit pull request may change only its pin, integration metadata, conflict handling, or retirement state unless ownership has explicitly transferred.

Material means that activation, non-activation, authority, safety, compatibility, observable workflow behavior, evidence quality, dependency conflict, or supported or retired status changes. A wording preference alone does not create PR churn.

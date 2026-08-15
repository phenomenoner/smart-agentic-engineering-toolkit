# Method Boundaries and Non-Substitution Rules

## Start with an exact failure model

State included and excluded events before choosing methods. Distinguish, where relevant:

- ordinary process termination;
- OS or machine crash;
- power loss and storage persistence loss;
- concurrent writer or scheduling races;
- network partition or remote-provider failure;
- malicious or compromised actors;
- operator error and organizational pressure.

Evidence for one model must not silently widen the claim to another.

## Separate evidence dimensions

For each claim, record:

- subject bytes, object, topology, generation, or epoch;
- environment and toolchain identity;
- verification altitude and observed count;
- evidence timestamp and invalidation conditions;
- producer and whether the evidence is independent;
- assumptions and known defeaters;
- decision authority that may consume the evidence;
- explicit non-claims.

Hashes, object identity, ancestor identity, authorization, temporal freshness, and provider receipts are different dimensions. Preserve each when its failure could change the decision.

## Guard the model-to-system gap

A model can be internally correct while the implementation diverges. Require at least one explicit link:

- state or transition names mapped to code;
- generated or hand-maintained conformance tests;
- runtime trace or log monitoring against the model;
- failpoints mapped to modeled transitions;
- review of abstraction omissions.

Label remaining mismatches as open gaps.

## Expose assurance-case failure modes

Challenge:

- stale evidence after source, toolchain, environment, or contract change;
- zero-match tests or wrappers that only prove exit code;
- self-review presented as independent review;
- mutable evidence bundles;
- inferred evidence stronger than the raw observation;
- assumptions hidden as context-free claims;
- unrecorded counterevidence or unresolved defeaters.

## Avoid vocabulary collision

Qualify overloaded labels. Examples:

- `review authority level 3` versus `SLSA Build L3`;
- `system-dynamics model` versus `causal-loop hypothesis`;
- `assurance case` versus `certified safety case`;
- `verified artifact lineage` versus `verified behavior`.

## Resolve retirement conflicts

`RETIRED` is a negative authority boundary:

1. Do not load, invoke, edit, or cite the retired item as current authority.
2. Interpret requests to improve a retired workflow as migration intent when an active successor exists.
3. Transfer only the reusable heuristic into the successor.
4. Preserve explicit non-reactivation language.
5. Reactivate only when the user explicitly requests it and the higher-level conflict is removed or superseded.

Never use this skill to create a universal workflow chain. Method selection remains advisory and task-local.

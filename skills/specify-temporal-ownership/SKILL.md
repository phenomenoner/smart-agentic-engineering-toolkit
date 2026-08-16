---
name: specify-temporal-ownership
description: Specify, review, or test a concrete temporal check-then-effect seam where identity, ownership, authority, or current state is observed before a destructive or irreversible mutation and can change before that mutation. Use for TOCTOU, ABA, PID or handle reuse, replacement cleanup, generations, leases, fences, indeterminate effects, and sibling callers that may bypass a guard. Do not select merely because a general specification mentions ownership, revocation, multiple components, or failure semantics; require an identified mutable resource, differing actor/generation/time, and post-observation destructive effect. Do not use for pure reads, immutable transformations, or single-owner local state with no replacement or concurrency seam.
license: MIT
metadata:
  version: "0.1.1"
  toolkit-version: "0.1.0"
  toolkit-phase: "temporal-assurance"
  toolkit-contribution-protocol: "v1"
---

# Specify Temporal Ownership

Turn an informal race-safety goal into a bounded contract and a falsifiable implementation test.
Keep the property, its checking method, executable evidence, and release authority separate.

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

## Apply the brake

Before entering the specialized temporal model, ask `Do we really need this to make things happen?`
and `Is there a simpler and more direct way?` Carry the outcome/minimum invariant and the upstream
necessity decision from `engineering-specification`; prefer deletion, manual action, embedding or
ephemeral readback, and an existing platform primitive before retaining a new temporal mechanism.
If one is retained, count its complexity, authority, recovery, and failure-state cost here without
duplicating the general specification checklist.

Use the full workflow only when all three are present:

1. a mutable resource or externally visible effect;
2. two actors, generations, attempts, callbacks, or times at which ownership can differ; and
3. a destructive or irreversible mutation after an observation or authorization decision.

General ownership, revocation, lifecycle, or cross-component language is not enough. If the task
only asks for a broader contract and does not identify a mutable target, a time-separated authority
change, and a later destructive effect, stay inactive and leave ownership and failure semantics to
`engineering-specification`.

Return `NOT_APPLICABLE` with a short rationale when this seam does not exist. Do not manufacture a
formal model, matrix, or concurrency ceremony for a pure or single-owner transformation.

## Load the right references

- Read [contract-template.md](references/contract-template.md) whenever producing a specification,
  repair plan, or review packet.
- Read [counterexample-patterns.md](references/counterexample-patterns.md) when selecting adversarial
  histories or deterministic tests.
- Read [methods-and-sources.md](references/methods-and-sources.md) only when choosing a formal or
  systematic method, supporting a design claim, or citing the engineering basis.

## Workflow

1. **Bind scope and authority.** State the decision claim, exact artifacts, actors, writable or
   operational authority, included failures, exclusions, and unacceptable outcomes.
2. **Name resources by identity, not appearance.** Define the smallest identity tuple whose change
   invalidates authority. Consider logical ID, object instance, generation or epoch, owner, lease or
   fence, expected revision, stable OS handle, namespace, and configuration mode. A PID, path, hash,
   value, or version alone is not provenance.
3. **Model observation honestly.** Separate presence (`PRESENT / ABSENT / UNKNOWN`) from identity
   (`MATCH / MISMATCH / UNAVAILABLE`). Observation failure must not become absence, mismatch, or
   permission to mutate.
4. **State safety, liveness, and containment separately.** Include wrong-target mutation,
   stale-generation commit, equal-value ABA, indeterminate replay, partial rollback, and sibling
   escape when applicable.
5. **Define each operation history.** Name invocation, response, abstract effect, pending and
   indeterminate outcomes, and the linearization or commit point.
6. **Locate the final seam.** Record `C_final`, the last observation authorizing this exact effect;
   `M`, the first irreversible mutation; and every await, callback, RPC, lock release, exception
   edge, scheduler yield, or actor that may run in `(C_final, M)`.
7. **Name the proof mechanism.** Bind the final predicate and mutation with one transaction, CAS,
   lock held across both, stable object handle, or equivalent atomic primitive. When the platform
   exposes no such authority, use non-destructive containment and mark `NO_ATOMIC_AUTHORITY`.
8. **Inventory from destructive sinks outward.** Enumerate every direct and transitive caller,
   including timeout, cancellation, exception/finally, startup, shutdown, upgrade, recovery,
   rollback, platform adapter, compatibility, and direct-library paths. A repaired helper does not
   close callers that bypass it.
9. **Make coverage atomic.** Use one row per
   `entrypoint x operation x lifecycle phase x failure variant`. Do not combine siblings with slashes,
   lists, or representative sampling when their guards differ.
10. **Choose the smallest adequate checking method.** A focused seam test is enough for a local
    primitive. Add PlusCal/TLA+, P, a systematic scheduler, or deterministic simulation only when it
    controls a material state/interleaving question. Never treat a model as code conformance.
11. **Force the exact implementation seam.** Place a deterministic hook immediately after
    `C_final` and before `M`; inject replacement, A1-B-A2 equal-value ABA, observation unavailable,
    ownership loss, crash, or an indeterminate effect as applicable. Assert both the classification
    and that the wrong destructive sink did not execute.
12. **Map and report.** Link each modeled action and invariant to source, trace/failpoint, test, and
    drift control. Report exact subject, command, counts/results, bounds, assumptions, freshness,
    non-claims, open cells, and the smallest next falsifier.

## Containment when atomic authority is absent

Prefer one of these outcomes:

- return a structured conflict, identity-unavailable, ownership-unknown, or manual-reconciliation
  result;
- park or quarantine the operation with enough evidence for the authority owner;
- issue an expected-identity proposal for an authoritative owner to execute transactionally;
- write an immutable new generation and switch only a compare-bound pointer;
- keep the desired forward state and report unready instead of overwriting unknown current state;
- fence new harmful work without deleting or signalling a possibly foreign owner.

Do not approve raw PID signalling, path/value/hash equality, best-effort rollback after an ambiguous
external command, recheck-after-mutation as prevention, or retry of an indeterminate effect without
idempotency or receipt reconciliation.

## Verdict

Use exactly one bounded disposition:

- `CLOSED`: every declared atomic row has a property, linearization/containment mechanism,
  sink/caller mapping, and discriminating evidence at the required seam.
- `OPEN`: at least one in-scope row, caller, failure state, mechanism, mapping, or evidence obligation
  remains missing.
- `NOT_APPLICABLE`: the brake found no temporal ownership seam, with rationale.

`CLOSED` is not permission to merge, release, deploy, cut over, or perform a live effect.

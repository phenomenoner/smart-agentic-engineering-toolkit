---
name: engineering-implementation
description: Implement an authorized source, test, configuration, or documentation change when the behavioral contract is sufficiently clear. Use the smallest coherent slice, preserve unrelated work, add a discriminating regression for a safely reproducible existing defect when useful, and verify at the lowest altitude that can falsify the changed claim. Do not use for plan-only, diagnose-only, review-only, publication, live operation, or materially unresolved authority or requirements. It does not automatically authorize commits, pushes, worktrees, full suites, fan-out, or external effects.
license: MIT
metadata:
  version: "0.3.0"
  toolkit-version: "0.4.0"
  toolkit-phase: "implement"
  toolkit-contribution-protocol: "v1"
---

# Engineering Implementation

Turn a sufficient contract into the smallest complete change and evidence that directly exercises
the changed behavior.

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

## Confirm the implementation boundary

Before editing, identify:

- authorized outcome and writable paths;
- observable acceptance and important non-goals;
- relevant callers, lifecycle phases, compatibility surfaces, and likely failure modes;
- current branch/worktree state and unrelated user changes to preserve;
- the lowest verification altitude that can falsify the claim.

If behavior, ownership, compatibility, or acceptance is materially unresolved, use
`engineering-specification` before implementation. If the cause of a failure is unknown, use
`engineering-debugging`. Do not infer permission to publish, deploy, message, purchase, or operate a
live service from permission to edit code.

**A new finding is not new scope.** Before absorbing a review, test, security, or tooling finding
into the patch, compare it with the authorized deliverable and claim. Implement `IN_SCOPE` work and
only the minimum necessary `SCOPE_GUARD`; report `ADJACENT_RISK` and leave `OUT_OF_SCOPE` work
untouched. An already authorized `IN_SCOPE` repair may change product behavior and write within the
existing boundary without a checkpoint. Only when a proposed response is not already required by
the authorized outcome and would raise the claim, acceptance level, release rigor, system boundary,
authorized writable paths, or external effects, stop at a scope-change checkpoint and route the
unresolved amendment to `engineering-specification`. Finding severity and available tooling do not
authorize the expansion.

When the frozen design or the patch introduces a mechanism, state, authority owner, or recovery
path, read its necessity decision and ask: `Do we really need this to make things happen?` and `Is
there a simpler and more direct way?` Keep the slice and checks bound to the observable invariant,
not to a mechanism proxy. If implementation reveals a simpler deletion, manual, embedded,
ephemeral, or existing-platform route, return to `engineering-specification` instead of silently
expanding or preserving the mechanism. Already explicit small work proceeds directly; this is a
handoff/reopen guard, not a second specification checklist.

## Choose the smallest coherent slice

Prefer a vertical or risk-focused slice that leaves the repository in a usable state. Keep one
contract change together with its direct callers, compatibility representation, and focused tests.
Avoid speculative abstractions, unrelated cleanup, or repository-wide refactors unless the contract
requires them.

When delegated work would be useful, run the external `baton-fanout-skill` gate first. Delegation is
not evidence of quality, and the main agent still reviews the bytes, resolves conflicts, runs shared
verification, and owns the claim.

For concurrency, replacement, rollback, identity reuse, or check-then-mutate behavior, apply
`specify-temporal-ownership` before choosing a patch. A stronger-looking final check is insufficient
when another actor can replace state after it.

## Decompose costly composite seams before climbing altitude

Use a unit-first composition ladder when a claimed seam contains multiple links that can fail
independently, or when native, integration, or lifecycle feedback is materially expensive, slow, or
risky. Do not impose this ladder on one simple local seam when a direct focused check is cheaper and
equally discriminating.

1. Name each link or primitive, its controlled input/output contract, and the handoff it owns.
   Partition success and every credible, contract-relevant failure class across the links and
   handoffs. Cover the total contract-relevant failure partition, but do not manufacture the full
   Cartesian product of equivalent, impossible, or out-of-claim combinations.
2. Prove each link at T1 with controlled collaborators before relying on an expensive composed run.
   Include the credible negative, boundary, timeout, cancellation, malformed, unavailable, or
   downstream-failure class owned by that link.
3. After the link checks pass, add the smallest adjacent-link or whole-composition test that can
   falsify handoff translation, ordering, propagation, and shared-state assumptions at T1 or T2.
4. Only then run the native, integration, lifecycle, or live check needed for behavior that lower
   tiers cannot faithfully represent. When it fails, reduce the failure to the missing link or
   composition regression before repeatedly paying the high-altitude feedback cost.

After the contracts, dependency order, and shared fixtures are stable, Baton may assign disjoint
link tests, exact-path code generation, or low-judgment scouting to workers with exclusive ownership.
An exposed native `gpt-5.6-luna` lane at `max` is eligible only for stable, bounded work whose result
is cheap to falsify; use the CLI Luna bridge only for its narrower exact-path code-generation
fallback. Keep architecture, security, authority, release or cutover judgment, and independent
review out of Luna; use an applicable Sol/high-or-stronger lane when such bounded high-cost judgment
is independently delegated. Do not fan out an unresolved composition contract or a shared harness.
The main agent owns dependency synthesis, the composed checks, shared verification, and the final
claim.

## Establish a discriminating check

For a safe, reproducible existing defect, prefer a focused regression that fails for the right reason
before the repair and passes after it. Fail-first is not mandatory for net-new behavior,
documentation/mechanical changes, an already failing test, or unsafe/unavailable pre-change state;
use a current-state discriminator and state the limitation.

Select the lowest reliable altitude:

- **T0:** static shape, schema, formatting, or importability;
- **T1:** focused local behavior or unit seam;
- **T2:** touched real component boundary;
- **T3:** lifecycle or user scenario lower tiers cannot represent;
- **T4:** authorized live/external claim.

A mutation does not automatically require T3. A configuration, health, catalog, or startup check does
not prove a tool or user workflow works. Run a full repository suite only when blast radius or an
explicit release gate requires it, preferably once after executable bytes stabilize.

## Implement and inspect

1. Read the affected source and direct tests; use current CodeGraph navigation when it materially
   helps cross-file impact analysis.
2. Make the smallest patch that satisfies the frozen behavior.
3. Inspect the diff for unrelated edits, generated/private state, stale public claims, and platform or
   lifecycle siblings.
4. Run the focused discriminator and any credible negative, boundary, recovery, or concurrency case.
5. Record the exact changed Git objects and first executable seam, then reacquire only evidence
   invalidated by those bytes, their dependencies, or the required environment. Documentation or
   receipt-only edits do not automatically invalidate code results. For an explicit release or
   cutover, hand the change-to-evidence map to `completeness-and-test-synthesis`; implementation does
   not start or repeatedly interleave formal review, installed pickup, or publication gates.

## Finish honestly

Report changed files, exact meaningful checks and results, residual gaps, and whether a fresh host or
separate release review is still required. Do not say shipped, deployed, production-ready, or
marketplace-published without the corresponding authorized external evidence.
An ordinary small change does not activate formal release machinery merely because implementation
finished.

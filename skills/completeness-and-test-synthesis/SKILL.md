---
name: completeness-and-test-synthesis
description: Engineering completeness and test-evidence synthesis for readiness judgments, functional polish, recurring regressions, green-tests-but-broken-real-use failures, and cross-component or lifecycle claims. Use when evidence must cover the user's actual workflow, natural tool selection, or affected subsequent interactions. Choose the lowest verification altitude that can falsify the claim. Do not trigger for cosmetic polish, every ordinary implementation, or merely because a task ends.
license: MIT
metadata:
  version: "0.4.0"
  toolkit-version: "0.5.0"
  toolkit-phase: "evidence"
  toolkit-contribution-protocol: "v1"
---

# Completeness and Test Synthesis

Decide whether the available evidence supports the exact claim, and identify or, when test writes
are authorized, create one missing test when it does not. A readiness, review, or status request
alone grants no source, installation, or live-effect authority. The workflow is not an end-of-task ceremony:
small, local changes should stay small.

## Start from the claim

For functional polish, a failing user journey despite component passes, natural route/tool selection,
or changed state consumed by a subsequent interaction, read
[user-journey polish](references/user-journey-polish.md). It owns the compact outcome contract,
route/continuation evidence, and finite scenario budget; do not duplicate that procedure in other
skills. Cosmetic edits and already sufficient local checks stay on the direct path.

Before choosing tests, state:

1. the changed behavior or invariant;
2. the first seam where the old defect or a plausible regression would be
   observable;
3. the affected callers, state transitions, and external boundaries;
4. the strongest fresh evidence already available.

Use repository history, incident evidence, and call sites to identify blast
radius. Do not infer risk from file count, the word `mutation`, or a workflow
label alone.

## Enforce the claim budget

The authorized claim is the **claim budget** for evidence work. A missing test, severe finding,
available harness, or stronger methodology does not authorize a larger claim. Select only evidence
that can falsify the current claim; do not upgrade a local artifact, prototype, library, or bounded
review into production, live, migration, security-certification, or release acceptance merely to
justify higher verification altitude.

If an evidence gap proves that the original deliverable cannot stand, classify the response as
`IN_SCOPE` or the minimum `SCOPE_GUARD`. If closing the gap would instead change acceptance level,
release rigor, system boundary, writable ownership, or external effects, report `ADJACENT_RISK` and
route a scope-change checkpoint to `engineering-specification`. An evidence gap does not authorize a
larger claim.

Classify every material gap at its first affected effect boundary by **consequence × estimated
frequency**, reversibility or containment, and evidence confidence. Keep evidence invalidation and
readiness `risk-local`. High-consequence uncertainty fails closed before the unsafe effect and reopens
only dependent cells. A low-consequence, low-frequency, reversible diagnostic or advisory gap may use
**bounded fail-open** with preserved evidence, an explicit residual, and a repair trigger; it does not
upgrade unrelated evidence to T3/T4 or block a claim it cannot falsify. Frequent low-consequence gaps
may justify focused operability repair without becoming release-critical.

Before adding a test artifact, replay, matrix, harness, or integration layer, ask `Do we really need
this to make things happen?` and `Is there a simpler and more direct way?` State the invariant first,
separate evidence outcome from mechanism proxy, and prefer the smallest direct falsifier. Add
lifecycle/recovery machinery only when the claim requires it, after comparing deletion, manual,
embedded/ephemeral, and existing-platform options and their complexity, authority, recovery, and
failure-state cost. This skill judges evidence adequacy; it does not approve a production design.
Route unresolved detailed mechanism design to `engineering-specification`, the canonical owner;
this evidence skill keeps only the bounded challenge and verification-altitude decision.

## Choose the lowest falsifying altitude

| Tier | What it can establish |
|---|---|
| T0 | Static shape, compilation, formatting, schema, or generated-file consistency |
| T1 | Local behavior of one unit with controlled collaborators |
| T2 | Behavior across the touched real component or contract seam |
| T3 | A lifecycle, multi-component, or user scenario that lower tiers cannot faithfully represent |
| T4 | A bounded live/external claim such as provider visibility, timing, or soak behavior |

Choose the lowest tier at which the relevant defect would actually fail.

- A local state transition with an isolated contract may be fully falsifiable at
  T1.
- Serialization, persistence, IPC, or another touched boundary normally needs a
  focused T2 check.
- Use T3 when the claim depends on ordering across lifecycle phases, multiple
  real components, recovery, or a user journey that T1/T2 cannot represent.
- Use T4 only when the requested claim itself includes live or externally
  visible behavior and that operation is authorized.

Higher tiers do not replace lower-tier logic tests, and repeated integration
runs do not compensate for a non-discriminating assertion.

## Report evidence origin and real-dispatch gaps

For each material acceptance claim, report evidence origin separately from T0-T4 and pass/fail:

- **Synthetic/simulated:** authored fixtures, mocks, scripted agents, or fabricated event sequences.
  These prove behavior under the supplied assumptions, not actual backend behavior.
- **Recorded real-event replay:** a captured real execution replayed offline. Identify its source
  version/route and relevant omissions; replay is not a fresh real dispatch.
- **Real execution/dispatch:** actual execution through the claimed backend and route. Name the
  observed stages: submission, child execution, result collection, parent integration, final
  response, and relevant continuation. Mark unexercised stages separately. A real component check
  may be reported as such without claiming model dispatch or a complete user workflow.

Mixed evidence keeps separate labels. Test counts, a created child, healthy service, or delivered
error do not prove task completion. State forced-tool versus natural selection and mocked portions
when material; one successful route does not validate other routes. Reuse adequate fresh evidence;
this reporting rule does not mandate paid dispatch for local changes or unrelated claims.

If a required real-dispatch claim is not verified, assess BOTH of the following in the report,
using available tool, access, and environment evidence rather than assuming the user must test:

1. **Automatic execution and budget approval:** say whether the agent can perform the exact
   missing scenario. If feasible but its budget is not approved, give a concrete minimal proposal:
   backend/model/effort, maximum scenarios and calls (including children and retries), a time and
   token/spend bound where controllable, expected proof, and stop condition. Disclose unknown cost
   instead of inventing a quote. Define the counting unit: a scenario, parent/child launch, model
   turn, and provider request are different units. For example, one scenario with one parent and
   one child has two agent launches and may use several model turns/provider requests; never call
   it one total model call. Name enforceable caps separately from estimates or unbounded backend
   usage. If route/model/effort or accounting is unknown, resolve available readbacks first and
   explicitly retain any unresolved budget field instead of making up a concrete plan.
   Finish authorized offline preparation before asking for approval;
   do not dispatch while approval is pending. Reuse existing scope-matching approval and its
   remaining allowance; do not ask again or reset an exhausted budget. Budget approval alone does
   not authorize unrelated external effects.
2. **Human-assisted execution:** say which required steps cannot be automated and why, naming the
   actual capability/access constraint. Give the smallest numbered human actions, prerequisites,
   expected visible result, evidence to return with secrets omitted, and what the agent will verify
   afterward. Automate the remaining steps within authority. Distinguish a one-time login/unlock
   followed by automation from a truly manual interaction. Do not delegate the whole test to the
   user because one client action is inaccessible.

Use `not needed` with a reason when a branch does not apply. If feasibility is unknown, name the
missing readback and resolve it read-only when possible; do not mislabel it as a budget or human
blocker. A mixed scenario may need both budget approval and human interaction. Keep required
unexecuted claims `not verified`, separate failure handling from successful task completion, and
continue unrelated authorized work. This adds no reviewer, persistent ledger, or automatic live run.

## Require a unit-first ladder only for composite seams

When one claim crosses multiple independently falsifiable links, or high-altitude feedback is
materially expensive or risky, split the evidence before accepting an integration result:

1. Map the links, primitives, handoffs, and the total contract-relevant failure partition. Require a
   focused T1 check for each independently failing link and each credible failure class; merge
   behaviorally equivalent classes and exclude impossible or out-of-claim combinations with a reason.
2. Require the smallest T1/T2 composition checks for adjacent handoffs, ordering, translation,
   propagation, and shared-state assumptions after the isolated checks pass.
3. Use native, integration, lifecycle, or live evidence only for the remaining claim that lower tiers
   cannot represent. A green high-altitude run does not fill a missing link partition, and repeated
   end-to-end runs do not substitute for a reduced regression.

This is a conditional evidence ladder, not a mandatory test pyramid. A single local seam or a cheap
real-boundary check that directly falsifies the claim stays on the minimum-sufficient path. When
independent link work is worth delegating, apply Baton before fan-out, keep ownership disjoint, and
retain composed verification and readiness synthesis with the main agent.

## Use regression-first where it proves something

For a safe, reproducible existing bug, prefer a test or fixture that fails for
the original reason before the repair and passes afterward. An already-failing
test is valid fail-first evidence; it does not need to be recreated.

Fail-first proof is not mandatory when:

- the behavior is net new rather than a repair;
- the change is documentation, formatting, generated metadata, or a mechanical
  synchronization;
- the pre-change state is unavailable or reproduction would be destructive,
  unsafe, flaky, or dependent on a live system;
- an existing trustworthy test already demonstrates the failure.

In those cases, use a current-state check that is still discriminating: it
should fail if the new behavior is removed or the relevant defect returns.
State any material limitation instead of inventing a pre-change run.

## Run the completeness check

Check only the rows relevant to the claim:

1. **Contract:** Name the behavior or invariant and the affected consumers.
2. **Discrimination:** Confirm each selected check can fail for a meaningful
   violation, not merely for a missing field or expected string.
3. **Seam:** Exercise the real failure-bearing seam at the lowest sufficient
   tier.
4. **Failure variants:** Add negative, boundary, recovery, concurrency, or
   stale-state cases only when they are credible failure modes.
5. **Evidence freshness:** Reuse results only while the executable bytes,
   relevant tests/contracts, toolchain, and required environment remain
   materially unchanged.
6. **Claim boundary:** Separate source correctness, artifact identity,
   deployment, and live behavior. Do not promote one into another.
7. **Open gaps:** Record gaps that could change the decision; do not turn
   optional process artifacts or untested implausible combinations into
   blockers.

For a local implementation, a short statement of behavior, command, result, and
remaining gap is enough. Use a table only when several independent claims or an
explicit readiness/release decision make it clearer.

## Progress explicit releases incrementally

When the claim spans a release, migration, cutover, installed pickup, fresh host, or external
publication, read
[references/incremental-release-progression.md](references/incremental-release-progression.md).
Keep source correctness, artifact identity, formal review, installed instance, live host, and
external publication as separate evidence gates.

Classify the exact changed Git objects and their first executable seam before invalidating evidence.
Reopen the affected cells and downstream claims; do not automatically discard runtime evidence for
a WAL, documentation, receipt, locator, or reviewer-envelope change that cannot influence that
runtime seam. Conversely, launcher, dependency, plugin, bundled-skill, MCP, or executable-semantic
drift reopens every installed or live claim that depends on it. If high-risk equivalence cannot be
proved, fail closed and reacquire the uncertain cells.

This progression is conditional. A small ordinary change with no readiness, release, migration, or
cutover decision stays on its direct focused-check path.

## Synthesize the smallest missing test

When the check finds a material gap, identify the smallest durable test that would close it. Create
that test only when the current task authorizes writes to its target; otherwise report the exact
test seam and stop at the evidence judgment:

- **Incident:** Reduce the observed failure to a sanitized deterministic
  fixture, then assert the violated invariant.
- **Touched boundary:** Drive the real seam with the smallest representative
  allowed and disallowed cases.
- **Lifecycle:** Reproduce only the phases needed for the failure, including
  restart, retry, cancellation, or recovery when relevant.
- **Recorded evidence:** Capture, sanitize, minimize, assert, and wire the
  fixture into the narrowest reliable runner.

Read [references/receipt-to-replay.md](references/receipt-to-replay.md) when
turning traces, logs, or receipts into a replay fixture.

Prefer tests that are deterministic, hermetic, behavioral, and clear when they
fail. Inject time and identifiers; do not use sleeps or a live dependency where
a controlled seam proves the same contract.

## Bind artifact claims only when relevant

When a claim depends on build or deployment bytes, distinguish:

- source/input continuity;
- the immutable instance actually executed or selected for deployment;
- build-recipe identity;
- reproducible rebuild;
- semantic equivalence.

A mutable build output cannot prove that an earlier executed instance still
exists. Preserve the exact instance before another build can overwrite it.
Bind compiler, linker, SDK, flags, environment, and repeated byte equality only
when reproducibility is the claim.

Frozen release/review evidence stays append-only while that gate is active. If
an assertion is unsound, supersede it without erasing unaffected evidence.
These requirements do not apply to ordinary local test output.

## Keep review proportional

Independent review is evidence for an explicit review, release, migration,
cutover, or other high-risk gate - not a required blessing for each patch. Stabilize executable
candidate bytes and reviewed contracts before a formal review. Keep that gate separate from
installed-runtime pickup: after actual `PASS` and only when separately authorized, install and
transition the exact final artifact once, then perform the fresh native and actual drill required by
the claim. A changed hash requires a
newly bound whole-candidate verdict, but unchanged review-cell evidence may be reused when exact
object-and-seam analysis proves it remains applicable. If ordinary local checks close the requested
claim, stop there.

## Project adapter

Create or reuse a project adapter only when repeated or high-risk work benefits
from stable knowledge of contracts, boundaries, test runners, replay sources,
and release gates. Do not create one for a one-off local change.

## Report

Report the exact claim, verification tier actually reached, evidence origin, meaningful commands
and results, and any gap that could change the conclusion. Apply the real-dispatch gap assessment
above when required execution is missing, including automatic/budget and human-action branches.
Say `not verified`
when the required behavior was not exercised; do not replace behavioral
evidence with a checklist sentence.

<!-- TOOLKIT-CONTRIBUTION-PROTOCOL:v1 -->
## Toolkit contribution protocol

When real work using this skill exposes a material skill improvement, missing safeguard, conflict, or
retirement candidate, do not silently patch an installed projection or plugin cache. Record a
public-safe counterexample, the canonical commit and skill hash/version, expected and observed
behavior, materiality and compatibility impact, an exact patch, and the smallest activation,
non-activation, or workflow evaluation that distinguishes the change.

If the active task authorizes GitHub writes, open a draft pull request to the canonical owner and
read back its identity and state. Otherwise return a PR-ready packet and explicitly offer to open
the pull request; never claim that a pull request exists. Changes to external dependency behavior
belong to the actual upstream. A toolkit pull request may change only its pin, integration
metadata, conflict handling, or retirement state unless ownership has been explicitly transferred.

Material means that activation, non-activation, authority, safety, compatibility, observable
workflow behavior, evidence quality, dependency conflict, or supported/retired status changes.
Pure wording preference does not create pull-request churn.

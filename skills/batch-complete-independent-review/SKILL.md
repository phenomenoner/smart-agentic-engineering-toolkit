---
name: batch-complete-independent-review
description: Review code and engineering changes without stopping at the first blocker. Use lightweight finding-oriented mode for an ordinary code, diff, patch, or pull-request review. Use the formal hash-bound fixed-point gate only for an explicitly independent, final, release, migration, or pre-cutover review, a project-mandated gate, or recurring reviews that keep discovering sibling blockers one round at a time. Do not trigger merely because implementation work occurred.
license: MIT
metadata:
  version: "0.4.0"
  toolkit-version: "0.5.0"
  toolkit-phase: "review"
  toolkit-contribution-protocol: "v1"
---

# Batch-Complete Review

Find the complete actionable blocker batch before repair instead of stopping at
the first issue. Scale the review machinery to the decision being made.

## Select the mode first

If the reviewed claim includes functional polish or an end-to-end interaction, challenge the most
plausible ordinary user path or next action that the evidence omits. In particular, distinguish
forced-tool checks from natural selection, and tool completion from useful task completion. Use
the existing `completeness-and-test-synthesis` skill's `references/user-journey-polish.md` when available
for that boundary; do not select a formal gate, expand scope, or add a reviewer just for polish.

### Ordinary finding review

For a normal code, diff, patch, or pull-request review:

- inspect the current changed bytes, intended behavior, callers, relevant tests,
  and sibling failure paths;
- continue after the first finding so the user gets one coherent actionable
  batch;
- report findings by severity with file/line evidence, then state residual
  testing or scope gaps;
- do not require a frozen manifest, coverage matrix, external reviewer, formal
  verdict schema, or counterfactual assumption ledger.

The reviewer may conclude that there are no findings, but that is not a formal
release or cutover authorization.

### Formal independent gate

Use the remaining hash-bound protocol only when the request or project contract
needs an independent/final/release/migration/pre-cutover decision, or when a
recurring sibling-blocker pattern makes fixed-point coverage materially useful.
Do not use formal artifacts merely to make an ordinary review look rigorous.

For a release or cutover, start formal review only after executable candidate bytes and reviewed
contracts are stable. Complete the hash-bound review before final installed-runtime pickup; do not
alternate whole formal review waves with install, restart, or fresh-host checks. The
`completeness-and-test-synthesis` owner decides which downstream evidence cells a pickup result can
reopen.

An intake, binding, or review-tool defect does not become a candidate-behavior finding merely
because it prevents a verdict. Report the formal gate as `INCOMPLETE`, repair and revalidate the
affected envelope, locator, or tool seam, and preserve unrelated candidate-behavior evidence. Use
`BLOCKED` only when supported evidence identifies an actual candidate contract violation.

## Keep findings inside authorized scope

Finding severity does not grant scope. Report every supported finding that is material, but compare
its requested disposition with the authorized deliverable, claim, and review mode. Classify proposed
work as `IN_SCOPE`, minimum `SCOPE_GUARD`, `ADJACENT_RISK`, or `OUT_OF_SCOPE`. Only the first two can
block the bounded candidate verdict without a scope amendment; adjacent risks remain visible but do
not silently raise the product claim, acceptance level, release rigor, system boundary, or repair
authority.

Also classify the affected effect boundary by **consequence × estimated frequency**, reversibility or
containment, and evidence confidence. Review rigor is `risk-local`: L3 applies to the dependent
authority, security, irreversible, cutover, rollback, or delivery partition, not by contagion to the
whole candidate; `candidate-wide L3 contagion` is prohibited. A `LOW × LOW` reversible finding may be accepted as a
**bounded fail-open** residual with evidence and a repair trigger when it cannot invalidate the
authorized claim. It does not reopen unrelated cells, start another full wave, or block the candidate.

When a finding would require new acceptance criteria, a broader writable surface, another system or
repository, production or live evidence, or formal release machinery not present in the request,
route a scope-change checkpoint to `engineering-specification`. Review may recommend the change; it
cannot authorize implementation or enlarge its own gate.

## Challenge mechanism necessity when material

When either review mode sees a candidate adding a component, protocol, durable state, authority
owner, recovery path, or evidence layer, ask `Do we really need this to make things happen?` and `Is
there a simpler and more direct way?` Check the observable outcome and invariant against deletion,
manual, embedded/ephemeral, and existing-platform alternatives; compare complexity, authority,
recovery, and failure-state cost against the frozen necessity decision. This is a conditional
challenge, not a redesign mandate. For a formal gate, carry it as one atomic design-necessity matrix
row only when material; do not add a schema field or formal bundle to an ordinary review.
When the frozen decision needs redesign, route it back to `engineering-specification`, the detailed
canonical owner; review only challenges the decision and its evidence.

## Preserve the surrounding rules

- Use the smallest reliable review shape. This skill does not mandate a
  reviewer loop for every code change.
- Invoke `baton-fanout-skill` before dispatching any subagent. Let Baton own
  worker count, model/effort routing, context minimization, and write ownership.
- Never route independent review through Luna. Use the lowest independent lane shown capable of the
  decision. In a Codex runtime exposing the GPT-5.6 family, high-consequence authority, security,
  privacy, irreversible release, rollback, delivery, or cutover judgment uses at least
  `gpt-5.6-sol` at `high` effort, or a clearly stronger exposed lane. A lower-consequence explicit
  review does not inherit that floor merely from the word `final`. The live runtime schema remains
  authoritative, and the main agent retains synthesis and release judgment.
- Apply `completeness-and-test-synthesis` when its narrower readiness,
  recurring-regression, lifecycle, or evidence-gap triggers apply. Do not load
  it solely because an ordinary review is underway.
- Use `claude-independent-review` only when the user explicitly authorizes
  Claude. Treat Claude, Codex subagents, and local CLIs as execution adapters,
  not as this protocol's authority.
- Obey project privacy, freeze, release, live-operation, and cutover guards only when they preserve
  higher-priority user authority and effect-local proportionality. A broader local rule is not
  authoritative merely because it is stricter. Review authority never authorizes implementation or
  live mutation.

## Choose the formal review shape

Start with one primary reviewer using the counterfactual fixed-point pass.

- **L1 independent:** one batch-complete reviewer; no automatic auditor.
- **L2 cross-cutting:** one primary reviewer. Add one narrow coverage auditor
  when authority, identity, shared mutation, recovery, concurrency, or multiple
  lifecycle phases are involved.
- **L3 release/cutover critical:** one primary reviewer plus one narrow,
  independently dispatched coverage/assumption auditor. Upgrade to two sealed
  blind first passes with orthogonal lenses and reciprocal coverage audits when
  the gate combines authority/security with release or cutover, or when a
  supposedly covered family recently escaped another HIGH/CRITICAL sibling,
  and only when the bound plan declares `maxPrimaryReviewers: 2` plus a concrete
  `secondBlindReason`. A third full reviewer is prohibited. An unresolved supported
  disagreement, unowned matrix partition, hash/binding failure, or incomplete
  lane returns `INCOMPLETE` for owner action instead of summoning another wave.

Never add a reviewer merely because a concurrency slot is free. One
well-supported blocker blocks; do not use majority vote.

Before binding, declare integer limits in the review plan. The direct defaults are
`maxFullReviewWaves: 1`, `maxSameCauseAttempts: 2`, `maxPrimaryReviewers: 1`, and
`maxNarrowAuditors: 0` or `1`. `maxPrimaryReviewers: 2` is valid only for L3 with a non-empty
high-consequence `secondBlindReason`; `maxFullReviewWaves: 2` requires an
`additionalWaveReason`. The plan binds `waveOrdinal` and `sameCauseAttemptOrdinal` within their
ceilings; no field may authorize a third primary reviewer or unchanged third same-cause attempt.
The binder rejects a formal plan with absent, non-numeric, or over-limit budgets.

Read [references/protocol.md](references/protocol.md) for risk classification,
the fixed-point algorithm, matrix construction, escalation, and invalidation.

## Build deterministic formal intake

Skip this section in ordinary finding review. For a formal gate, create or
identify:

1. An immutable candidate manifest, including intended untracked files.
2. A verification-evidence index with executable and receipt hashes. Label each
   build record as source/input, immutable executed instance, immutable
   deployment instance, or derived mutable path, and state whether the review
   claims instance identity, recipe identity, reproducibility, or semantic
   equivalence. Never encode current liveness of a mutable Cargo/build output as
   continuity of an earlier execution.
3. A neutral review plan with contracts, authority boundaries, risk class, and the numeric budgets
   above.
4. A required coverage matrix spanning entrypoints, lifecycle phases,
   mutations, recovery/cleanup paths, adversarial variants, and evidence tiers.

Make every required matrix row atomic: one contract, entrypoint, operation,
lifecycle phase, adversarial variant, expected behavior, and required evidence
tier. Do not use composite rows such as "all recovery phases" or let reviewers
silently invent required subcells. A newly discovered required subcell is a
matrix gap: rebind the review wave and keep the active finding set incomplete.

Use `scripts/review_gate.py bind` to hash these four artifacts into one review
wave. Hashing and schema checks are tooling work, not frontier-model work.

```powershell
python scripts/review_gate.py bind `
  --candidate-manifest <candidate.json> `
  --evidence-index <evidence.json> `
  --review-plan <plan.json> `
  --coverage-matrix <matrix.json> `
  --output <review-wave.json>
```

Do not start semantic review when the candidate is moving or any required
binding is missing.

## Separate visitation, support, and audited completion

Do not infer completeness from a cell count. These are distinct claims:

- **Visited:** the reviewer wrote a disposition for the cell.
- **Supported closure:** a no-finding disposition has evidence at the matrix's
  required tier, or a finding is supported strongly enough to block.
- **Lane complete:** one sealed reviewer has no open or unsupported required
  cell and its own reopen obligations reached a stable fixed point.
- **Audited batch complete:** the main-agent synthesis resolves every coverage
  and finding challenge across the required auditor topology.

A report can visit every cell and still be incomplete because a closure is
unsupported, at the wrong evidence tier, or invalidated by a finding that
should have reopened sibling cells. Individual lane `BATCH_COMPLETE` is never
the final multi-review gate verdict.

## Run the counterfactual fixed-point pass

Give the primary reviewer the frozen wave, matrix, contracts, source, and
evidence paths. Do not give it a desired verdict or peer findings.

Require this loop:

1. Review the actual frozen candidate against every required matrix cell.
2. On a blocker, record the exact precondition, first unsafe operation, impact,
   evidence, sibling paths, and required regressions.
3. Define a narrow, falsifiable repair postcondition in the assumption ledger.
   Never assume an implementation or broadly assume that a subsystem is fixed.
4. Continue under the accumulated postconditions.
5. Reopen each previously closed risk-local cell that depends on a new or expanded
   assumption.
6. Repeat only while the declared **full-review wave limit** and **same-cause retry limit** have
   budget, and only across the risk-local cells affected by a blocking finding or
   acceptance-critical assumption. Budget exhaustion returns `INCOMPLETE` with the current evidence;
   it never creates another successor name or weakens acceptance.
7. Record explicit reopen obligations for each blocking finding and acceptance-critical assumption.
   A finding's required regression cells must all receive a reviewed disposition; an ID-only
   reference is insufficient. A supported low-consequence, low-frequency bounded fail-open residual
   records its disposition without reopening unrelated cells.
8. Attack the claimed closures across sibling call sites, lifecycle phases,
   unrecognized current-live third states, evidence altitude, and repair
   postcondition completeness.
9. Reopen only the dependent cells when an attack changes a blocking finding,
   acceptance-critical assumption, required evidence tier, or cell disposition and budget remains.
   An unchanged third attempt is prohibited; the same-cause signature must change before reactivation.
   Stop `BLOCKED` or `INCOMPLETE` and require a
   changed architecture, bounded constructibility probe, or owner decision before reactivation.
   `stable: true` is valid only after all required risk-local attacks and reopen obligations close.

Finding a blocker changes the actual verdict to `BLOCKED`; it never ends the
review. If hash, access, or scope failure prevents a trustworthy candidate
judgment, return actual `INCOMPLETE`. If a blocker is already supported but
required evidence, safe-sibling closure, or reopen obligations remain open,
preserve actual `BLOCKED`, set `findingSetStatus` to
`EVIDENCE_CLOSURE_INCOMPLETE`, and keep the counterfactual verdict unresolved.

## Keep verdicts non-substitutable

Use all three fields:

- `actualCandidateVerdict`: `PASS`, `BLOCKED`, or `INCOMPLETE`.
- `findingSetStatus`: `BATCH_COMPLETE` or an explicit incomplete reason.
- `counterfactualVerdict`: `NOT_NEEDED`, `PASS_UNDER_ASSUMPTIONS`, or
  `UNRESOLVED`.

`PASS_UNDER_ASSUMPTIONS` is a repair-planning result, never approval to merge,
ship, release, migrate, preflight, or cut over. Any blocker means the actual
candidate remains `BLOCKED`.

`EVIDENCE_CLOSURE_INCOMPLETE` is also non-authorizing. It means the candidate
is already known to be blocked while the complete blocker batch or required
evidence closure remains unfinished. It can never substitute for
`BATCH_COMPLETE` in a lane or `AUDITED_BATCH_COMPLETE` in synthesis.

After any candidate-byte change, freeze and bind the actual new bytes; the previous
whole-candidate verdict never transfers to the new hash. Record the exact changed Git objects and
first affected executable seams, then reopen the mapped review cells and downstream claims. A new
wave may reuse unchanged cell evidence only when its contract, subject bytes, dependencies,
required tier, and reviewer access are proven unaffected. An executable semantic change invalidates
every dependent review cell. A documentation, receipt, review-envelope, or locator repair still
requires a new binding and affected-cell review, but it does not by itself require replaying
candidate behavior. When equivalence is material and cannot be proved, fail closed and reopen the
uncertain cells.

Treat frozen evidence tooling as append-only. If a validator confuses an
immutable executed artifact with a mutable build path, do not edit a self-bound
validator in place. Preserve the frozen bytes; add a hash-bound superseding
validator and every path-coupled consumer; retain all unaffected checks; record
the narrowed claim and missing evidence explicitly; and independently review
the complete superseding set. A later non-reproducible rebuild does not by
itself invalidate preserved source, test, or deployment-instance evidence, but
drift of an input or the selected deployment instance does.

## Audit coverage without repeating the full review

For L2/L3 triggers, give a narrow auditor only the sealed primary report, review
wave, matrix, call-site/test map, and necessary source evidence. Ask it to find:

- required cells left unvisited, unsupported, or closed below the required
  evidence tier;
- blocker families with missing sibling-path disposition;
- assumptions that are broad, unfalsifiable, inconsistent, or circular;
- dependent cells that were not reopened;
- saved-state or ownership proofs that never attack unrecognized current-live
  bytes before the first mutation;
- provenance-only repairs that do not execute the required behavior at the
  required compatibility altitude;
- unsupported findings or severity;
- reasons the claimed fixed point is not stable.

The auditor does not rerun the whole review or modify the sealed report. The
main agent resolves challenges from primary evidence and owns synthesis.

For the two-blind L3 shape, keep both first passes sealed until both finish.
Then let A audit B and B audit A. Each reciprocal audit must hash-bind both
reports and classify challenges as `UNSUPPORTED_CLOSURE`, `WRONG_TIER`,
`MISSED_SIBLING`, `INCOMPLETE_REPAIR_POSTCONDITION`, or another explicit
protocol category. Classify overlaps as full duplicates, partial overlaps that
retain distinct acceptance axes, related-family nonduplicates, or unique
findings. Do not repair source until both audits and main-agent union synthesis
finish.

Set `auditMode` explicitly. A reciprocal audit uses `RECIPROCAL`, binds the
auditor's own sealed first pass plus the peer pass, and requires distinct
reviewer identities. A narrow audit uses `NARROW`, binds both report-hash fields
to the single sealed primary report, and requires an auditor identity distinct
from that primary reviewer. Do not silently treat a narrow audit as a second
blind lane.

## Validate the report

Require `references/review-report.schema.json`. Then run:

```powershell
python scripts/review_gate.py validate-report `
  --wave <review-wave.json> `
  --report <review-report.json>
```

For each reciprocal direction, validate the sealed reports and audit together:

```powershell
python scripts/review_gate.py validate-audit `
  --wave <review-wave.json> `
  --own-report <own-sealed-report.json> `
  --peer-report <peer-sealed-report.json> `
  --audit <cross-audit.json>
```

Finally validate the selected topology and main-agent union synthesis:

```powershell
python scripts/review_gate.py validate-synthesis `
  --wave <review-wave.json> `
  --synthesis <review-synthesis.json>
```

The validator rejects hash drift and impossible verdict combinations, including
actual PASS with blocking findings, actual PASS under assumptions, batch-complete
claims with unvisited, unsupported, wrong-tier, or unstable required cells, and
counterfactual closure without an assumption covering every blocker and its
reopen obligations. The synthesis validator also rejects duplicate lane
identity, missing reciprocal direction, unsupported matrix closure, unresolved
challenge laundering, incomplete lane promotion, unclassified findings, and
finding rejection without disposition evidence. For a multi-lane topology,
only a passing synthesis validation may authorize
`AUDITED_BATCH_COMPLETE`.

## Synthesize one coherent repair batch

The main agent must:

1. Verify current wave and report hashes.
2. Union every sealed lane and reciprocal/narrow-audit challenge. Never use one
   lane alone when the selected topology requires multiple lanes.
3. Cluster only by invariant, precondition, first unsafe operation, and failure
   effect. Mark full duplicates, partial overlaps, related-family
   nonduplicates, and unique findings while retaining distinct lifecycle paths,
   evidence axes, and regression cells.
4. Recompute matrix closure from the union. Resolve every unsupported,
   wrong-tier, missed-sibling, and repair-postcondition challenge.
5. Set `AUDITED_BATCH_COMPLETE` only when the union has a concrete disposition
   for every required cell and challenge. A lane's self-declared
   `BATCH_COMPLETE` is insufficient.
6. When a supported blocker remains disputed, a partition is unowned, a
   binding fails, or the union still has an unresolved coverage challenge,
   return `INCOMPLETE`, seal the evidence, and identify the owner decision or
   changed-candidate next action. Do not summon another reviewer inside the
   exhausted wave.
7. Repair only after the complete review wave finishes.
8. Report actual verdict, counterfactual verdict, audited finding-set status,
   open coverage, and minimum coherent repair properties separately.

Do not let a reviewer self-approve its proposed repair, rerun broad suites to
manufacture confidence, inspect live secrets, mutate source/evidence, or perform
release/cutover actions unless separately authorized.

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

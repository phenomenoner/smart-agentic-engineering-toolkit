# Temporal ownership contract template

Use this template as a bounded engineering artifact. Omit genuinely irrelevant fields only with an
explicit `N/A` rationale.

## 0. Upstream necessity decision

- `Do we really need this to make things happen?`:
- `Is there a simpler and more direct way?`:
- Observable outcome and minimum invariant:
- Alternatives considered: deletion / manual / embedding or ephemeral state / existing platform
  primitive / retained new mechanism:
- Selected mechanism and falsifiable reason:
- Detailed owner: `engineering-specification` (this template carries its decision; it does not own
  the full mechanism-design procedure):
- Added durable states/transitions, authority owners, recovery obligations, and failure states:
- Residual failure and non-claims:

## 1. Scope and authority

- Decision claim:
- Exact source/artifact/version under analysis:
- Decision owner:
- Actors/controllers and legitimate authority:
- Explicit non-authorities:
- Included failures:
- Excluded failures:
- Unacceptable outcomes:

## 2. Resources and identity

| Resource/effect | Full identity tuple | Reuse/wrap assumptions | Stable reference or fence |
|---|---|---|---|

Record value and provenance separately. A generation, epoch, stamp, lease, fence, or stable object
reference must be non-reused for the lifetime assumed by the contract.

## 3. State and invariants

- Presence states: `PRESENT / ABSENT / UNKNOWN` or exact equivalent.
- Identity states: `MATCH / MISMATCH / UNAVAILABLE` or exact equivalent.
- Lifecycle states and transitions:
- Safety invariants:
- Liveness claims and fairness assumptions:
- Containment invariants:
- Crash, timeout, cancellation, recovery, rollback, and indeterminate-effect states:

## 4. Operation contract

Use one row per operation.

| Operation | Invocation/response | Abstract effect | `C_final` | `M` | Interleavers in interval | Linearization/commit point | Atomic mechanism | No-atomic fallback |
|---|---|---|---|---|---|---|---|---|

`C_final` is the last observation that authorizes this exact mutation. `M` is the first irreversible
or destructive mutation. A separate earlier check or later readback is not the linearization point.

## 5. Destructive sinks and callers

| Sink/API | Direct caller | Transitive entrypoint | Phase | Platform/config variant | Guard/mechanism | Matrix row IDs |
|---|---|---|---|---|---|---|

Closure requires zero unclassified callers and a search for semantic sibling APIs.

## 6. Atomic coverage matrix

Use one indivisible row for each:

`entrypoint x operation x phase x variant`

| ID | Entrypoint | Operation | Phase | Variant | Expected tuple | Unknown behavior | Hook after `C_final` | Conflicting actor action | Expected result | Evidence tier/test | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|

Typical variants include match, mismatch, absent, unavailable/unknown, A1-B-A2 equal value,
replacement owner, stale generation, lock/lease loss, crash before/after commit, and indeterminate
external effect.

## 7. Property and evidence map

| Property/model element | Code symbol/state | Executable observation | Evidence class | Drift control | What it does not prove |
|---|---|---|---|---|---|

Keep abstract property, model checking, systematic scheduling, exact seam test, static caller
inventory, OS-instance test, independent review, and operational readback as distinct evidence
classes.

## 8. Result

- Verdict: `CLOSED / OPEN / NOT_APPLICABLE`
- Exact commands and observed counts/results:
- Executed subject identity and environment:
- Open rows and smallest next falsifier:
- Assumptions and defeaters:
- Freshness or expiry conditions:
- Explicit non-claims:

## Atomic closure checklist

- [ ] The contract carries the upstream conditional necessity decision without duplicating it.
- [ ] Every actor and authority boundary is named.
- [ ] Every mutable resource has a full identity tuple.
- [ ] Generation/epoch/lease/fence uniqueness and reuse assumptions are explicit.
- [ ] Presence and identity each have an unavailable/unknown state.
- [ ] Unavailable/unknown observation always contains rather than authorizes mutation.
- [ ] Normal, crash, timeout, cancel, exception, recovery, rollback, and transfer phases in scope exist.
- [ ] Safety, liveness, and containment claims are separate.
- [ ] Every operation has an abstract effect and linearization/commit point or containment rationale.
- [ ] `C_final`, `M`, and every interleaving opportunity between them are identified.
- [ ] Predicate and mutation share an atomic primitive/stable object or destructive action is refused.
- [ ] Equal-value A1-B-A2 is covered.
- [ ] Process signalling uses the same validated stable OS object, not a raw numeric PID.
- [ ] Every destructive sink and direct/transitive caller is classified.
- [ ] Every atomic matrix row maps to both source and evidence.
- [ ] A deterministic hook executes after `C_final` and before `M` for each named escape.
- [ ] Tests cover relevant mismatch, unavailable, ABA, ownership loss, and sibling callers.
- [ ] Tests assert both return classification and absence/failure of the wrong destructive effect.
- [ ] Systematic exploration records controlled APIs, bounds, seeds/traces, and unsupported seams.
- [ ] Models map actions, guards, failures, and invariants to code and drift controls.
- [ ] Evidence classes are not substituted for one another.
- [ ] Open cells, assumptions, defeaters, freshness, and non-claims remain visible.

---
name: engineering-specification
description: >-
  Specify unresolved behavior, acceptance, ownership, compatibility, and failure semantics for
  material features, contracts, or cross-component changes before implementation. Use when a
  request has unresolved requirements or seams that must become observable and falsifiable. Do
  not use for trivial or mechanical edits, diagnosis-only work, review-only work, or an already
  explicit small contract; this skill does not authorize implementation.
license: MIT
metadata:
  toolkit-version: "0.1.0"
  toolkit-phase: "specify"
  toolkit-contribution-protocol: "v1"
---

# Engineering Specification

<!-- TOOLKIT-CONTRIBUTION-PROTOCOL:v1 -->

## Purpose

Turn an underspecified material engineering request into a compact, reviewable, falsifiable
specification. Capture what must happen, what must not happen, who owns each decision or effect,
which compatibility and failure boundaries matter, and how the claim can be checked. Stop at the
specification boundary: a specification is not an implementation plan with implied authorization.

This skill is narrow and optional. A task may proceed directly when its contract is already
sufficient, and specifying does not impose a universal implement-review-test workflow.

## Activation and non-activation

Activate when a material feature, contract, or cross-component change has unresolved behavior,
acceptance, ownership, compatibility, or failure semantics. Typical signals include:

- a request spans an API, worker, client, service, storage layer, or other component seam;
- the desired behavior, backward-compatibility rule, state transition, error policy, or authority
  boundary is not explicit;
- the requester needs a contract that another agent can implement and test without guessing; or
- a change can alter safety, authority, observable workflow behavior, supported status, or evidence
  quality even if the code diff may be small.

Do not activate for:

- a trivial or mechanical edit such as correcting one spelling mistake;
- diagnosis-only work when the behavior is failing and its cause is unknown;
- review-only work where the contract is already supplied and no source change is requested;
- an already explicit, small contract that can be implemented with a focused check; or
- a request to implement, publish, commit, push, or operate a live system when the specification
  is already sufficient. Route that authorized work to the appropriate skill.

The skill may be explicitly invoked for a material specification even when the requester has not
yet authorized implementation. It never infers implementation, publication, external messaging,
or live-operation authority from the act of specifying.

## Inputs

Use the smallest set of available inputs that can establish the contract:

- the user request, intended outcome, scope, and explicitly granted authority;
- current source, schemas, interfaces, configuration, tests, and documentation that define the
  existing behavior;
- actors and components, data/state ownership, identity or generation rules, and effect boundaries;
- supported versions, compatibility constraints, migration or rollback expectations, and
  operational limits;
- observed failures, examples, receipts, or other evidence, with provenance and uncertainty; and
- unresolved questions, assumptions, dependencies, and decisions that require an owner.

Do not invent facts to fill a gap. Label an assumption, unknown, or unverified observation, and
make its effect on the contract explicit.

## Procedure

1. **Frame the change.** State the user-visible outcome and the in-scope and out-of-scope
   behavior. Identify the actors, components, affected interfaces, authority boundaries, and
   materiality. If no material behavior is unresolved, return `NOT_APPLICABLE` and leave the
   direct bounded path available.

2. **Write the behavioral contract.** Specify preconditions, inputs, outputs, state transitions,
   invariants, success behavior, rejection behavior, unsupported behavior, and error semantics.
   Define idempotency, retry, timeout, ordering, and partial-result rules when they affect the
   observable contract. Use normative language for required and forbidden behavior.

3. **Map ownership and seams.** For each component or actor, name what it computes, proposes,
   authorizes, effects, stores, or delivers. Keep host or user authorization distinct from a
   helper's computation. For a check followed by a mutation, specify the identity, generation,
   lease, fence, capability, or compare-and-swap condition that prevents acting on a replacement
   or stale state. Identify sibling callers that could bypass the same guard and the linearization
   point or equivalent ordering rule.

4. **Define compatibility and failure boundaries.** Record supported old and new inputs, rollout
   and migration behavior, rollback or absence behavior, and what remains unchanged. List failure
   modes, forbidden traces, authority violations, ambiguous states, and safe containment behavior.
   Distinguish a known cause from a hypothesis; diagnosis or incident replay belongs to its
   corresponding skill when that is the actual request.

5. **Make acceptance falsifiable.** Turn each important requirement into an observable case with
   setup, action, expected result, and a failure interpretation. Include the smallest useful
   positive, negative/non-activation, boundary, recovery, and compatibility cases. Choose the
   lowest verification altitude that can distinguish the claim (static, local behavior, a touched
   seam, lifecycle scenario, or an explicitly authorized live check). Do not call a case passed
   merely because a plan or configuration exists.

6. **Handoff and stop.** Return a compact specification packet with explicit non-goals, risks,
   assumptions, open decisions, evidence gaps, and the next safe action. State whether a later
   implementation request would have enough information, but do not edit implementation files or
   claim that implementation, tests, review, release, or delivery has happened. If a required
   decision or authority is missing, stop with `BLOCKED` and identify exactly what is needed.

Do not automatically create a WAL, invoke a reviewer, run a full suite, start a worker, use Canvas
or CodeGraph, call AAR, or contact an external provider. Those capabilities may be selected by
their own boundaries when independently justified; none is prerequisite proof for this skill.

## Output contract

Use one of these statuses:

- `SPECIFIED`: the unresolved material behavior is described well enough for a separately
  authorized implementation decision;
- `NOT_APPLICABLE`: the request is trivial, already explicit, or otherwise outside this skill; or
- `BLOCKED`: a material requirement, authority, compatibility decision, or evidence boundary is
  unresolved and cannot be safely assumed.

For `SPECIFIED`, return a packet containing, at minimum:

1. **Intent and scope** - desired outcome, in-scope behavior, non-goals, actors, and affected
   seams.
2. **Normative contract** - inputs, outputs, state transitions, invariants, success, rejection,
   unsupported, retry, timeout, ordering, and partial-result semantics as applicable.
3. **Ownership and compatibility** - authority/effect/delivery boundaries, identity or generation
   rules, sibling-call protections, supported versions, migration, rollback, and absence behavior.
4. **Risks and failure semantics** - forbidden behavior, unsafe or ambiguous states, containment,
   assumptions, and residual uncertainty.
5. **Falsifiable acceptance** - named cases with setup, action, expected observation, and the
   lowest adequate verification altitude, including negative and recovery cases where relevant.
6. **Handoff** - open questions and dependencies, evidence gaps, and the explicitly authorized
   next action (or a statement that implementation authorization is not present).

For `NOT_APPLICABLE`, explain the direct bounded path in one or two sentences and do not manufacture
a specification artifact. For `BLOCKED`, preserve the partial contract, name the decision owner or
missing evidence, state the unsafe assumption that was avoided, and stop before implementation.

## Stops and safety boundaries

Stop and report instead of guessing when:

- two requirements or authority owners conflict;
- a compatibility or failure decision changes user-visible behavior but has no owner;
- an identity, generation, lease, or capability can change between a check and an effect and no
  stable ownership condition is defined;
- the requested proof requires an external or live operation that is not authorized;
- the evidence is too ambiguous to distinguish a hypothesis from an observed fact; or
- the specification is complete and the next phase would be implementation, review, publication,
  or live operation.

Do not silently edit installed projections, plugin caches, third-party sources, or generated
artifacts while specifying. Do not widen scope to resolve an open question, and do not turn an
optional tool or process artifact into authority.

## Non-claims

A specification packet does not claim that:

- source, tests, builds, deployment, runtime compatibility, or provider-visible delivery exist or
  pass;
- a contract is safe merely because it is detailed, or that unlisted behavior is supported;
- a plan, catalog, configuration, health result, graph, canvas, or helper output authorizes an
  effect or proves fresh-host operation;
- a reviewer, external provider, Git commit, pull request, release, or publication has occurred;
  or
- the specification replaces a user decision, implementation evidence, incident diagnosis, or
  readiness judgment.

## Contribution protocol

When real work using this skill exposes a material skill improvement, missing safeguard, conflict,
or retirement candidate, follow the contribution protocol instead of silently changing an
installed projection or plugin cache:

1. Record a public-safe counterexample; the canonical commit and skill hash/version; expected and
   observed behavior; materiality and compatibility impact; an exact proposed patch; and the
   smallest activation, non-activation, or workflow evaluation that distinguishes the change.
2. If the active task explicitly authorizes GitHub writes, open a draft pull request to the
   canonical owner and read back its identity and state. Otherwise return a PR-ready packet and
   explicitly offer to open the pull request; never claim that a PR exists.
3. Route behavior changes in an external dependency to that dependency's actual upstream. A
   toolkit contribution may change only its pin, integration metadata, conflict handling, or
   retirement state unless ownership has been explicitly transferred.

Material means that activation, non-activation, authority, safety, compatibility, observable
workflow behavior, evidence quality, dependency conflict, or supported/retired status changes.
Pure wording preference does not create PR churn.

## Minimal examples

### Activate

**Request:** "Design a backward-compatible auth refresh contract across the API, worker, and
client; ownership of refresh and revocation is unresolved."

Select `engineering-specification` and return `SPECIFIED` or `BLOCKED` with the API/worker/client
seams, who may authorize refresh and revocation, old-client compatibility behavior, expiry and
retry semantics, forbidden stale-token traces, and falsifiable positive, rejection, and restart
cases. State that no implementation or delivery claim is made.

### Do not activate

**Request:** "Fix one spelling mistake in the README."

Do not invoke this skill. If the edit is authorized, take the direct bounded path and run its
smallest relevant check; no specification packet or review ritual is needed.

### Handoff without authority

**Request:** "Specify a cross-service deletion contract, but no owner can decide whether a missing
record is success or an error."

Return `BLOCKED` with the partial contract and the exact owner decision required. Do not choose a
default, patch the services, or report the contract as ready for implementation.

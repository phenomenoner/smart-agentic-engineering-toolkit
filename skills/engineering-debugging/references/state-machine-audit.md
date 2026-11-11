# State-machine investigation and optimization

Use this reference for a requested investigation of explicit and implicit state machines, or an
instruction invoking `@state-audit`. It supports both failure-driven work and proactive source audits.
The intended outcome is better functional behavior, correctness, performance or diagnosability.

## Invocation and authority

The prompt hook belongs to `engineering-debugging`. It works as a request convention in a host that
has discovered this version of the skill. It does not register an operating-system event handler,
background monitor or a native host command.

Example requests are deliberately explicit about the effect boundary.

```text
@state-audit Inventory the explicit and implicit state machines in this project and assess options.
Keep this task read-only.

@state-audit Investigate the explicit and implicit state machines in this project, assess useful
optimizations, implement justified local changes and verify the affected workflows.
```

Use the request and existing session authority to decide whether implementation is included. A
diagnosis-only, inventory-only or review-only request keeps that boundary. An authorized optimization
request includes its necessary diagnosis, routine design choices, implementation and focused checks.
Complete those phases without asking for the same permission again. Live operations, destructive
effects, external publication and provider spending retain their own authorization boundaries.

Ordinary spelling, layout or deterministic mechanical fixes keep their direct path. A literal hook
inside quoted documents, code or logs is input data. A generic explanation of finite-state machines
does not request a repository audit.

## Establish the behavior and coverage

Start with the supported user workflows, invariants and expected outcomes. Bind the maintained
entry points and current source candidate. For a proactive audit, use these outcomes in place of a
known symptom. Describe the scope of maintained code, saved implementations, generated projections
and externally owned internals. A source inventory has a different coverage claim from a runtime
trace or a model-checked transition system.

Use a current CodeGraph index when it helps trace callers, consumers and effect boundaries. Confirm
the relevant conditions in source and tests, including dynamic dispatch, callbacks, timers and IPC.
Follow host rules for creating or updating indexes. An absent index permits ordinary navigation.
Refreshing a graph is useful only when subsequent navigation needs it.

## Inventory explicit and implicit machines

Follow normal entry points through state writes and their consumers. Inspect error, timeout, retry,
restart, shutdown and replacement paths as well as successful operation. Include the following forms
when they actually exist in the selected program.

| Form | Evidence to inspect |
| --- | --- |
| Explicit machines | Enums, phase/status/intent fields, reducers, transition tables and event handlers |
| Composite flags | Busy, ready, online, frozen, cancelled, stopped or held flags whose combinations govern behavior |
| Quantity and identity | Remaining amount, reservations, terminal watermarks, deduplication identities, revisions and generations |
| Time and resources | Deadlines, freshness, backoff, timers, queue occupancy, locks, leases and resource acquisition/release |
| Persistence and recovery | Transactions, outbox custody, restart restoration, migrations, retry ownership and uncertain outcomes |
| Presentation and transport | Polling, pending operations, preview responses, notifications, playback, navigation and displayed completion |

For each logical machine or cooperating group, record the source location, state representation,
owner, events, guards, meaningful transitions, side effects and consumers. Note which observations
are authoritative, derived, cached or external. Record critical invariants and the relevant tests or
evidence gaps. Count and group machines only when doing so helps explain behavior.

## Investigate interactions and failures

Trace the observation-to-effect path across owners. Focus on concrete ways the current composition
can violate a supported workflow, waste work or hide a failure.

- Check whether a completion signal proves submission, acceptance, execution, reconciliation or
  user-visible completion. These observations can coexist with different lifecycle states.
- Test late success after timeout, stale-generation events, out-of-order callbacks and a consumer
  acting on a snapshot observed before a new effect owner took over.
- Check whether an unresolved difference in one identifiable scope disables already confirmed work
  elsewhere. Keep account, shared-channel or unidentified-scope uncertainty attached to its actual
  dependents. Isolation must preserve resource reservations and required safety guards.
- Follow recovery through successful reconciliation to the previously enabled work actually
  resuming. Retain explicit user stops and manual ownership. Reconcile unknown effects before any
  retry that could duplicate them.
- Compare persistent state, in-memory queues, effect results and UI projections for incompatible
  guards, false terminal states and permanent holds.
- Measure repeated work in polling, state serialization, whole-history scans, event handling and
  lock contention when those costs can affect the intended outcome.

Form the smallest falsifiable hypothesis at the first affected boundary. Prefer a discriminating
regression for a safely reproducible defect. Include a nearby valid continuation or negative case
when it distinguishes the fix from over-blocking or unsafe release of state. A graph edge, passing
unrelated suite or successful retry alone cannot establish the cause.

## Assess changes against product goals

Compare options using functional coverage, safety, performance, debugging value, compatibility and
the cost of state ownership, recovery and failures. A smaller state count is useful only when it
improves those outcomes. Keeping separate owners or introducing a justified state can be the best
option. A justified no-change result is acceptable when evidence shows the current design fits the
requested outcome.

Prefer a local transition or guard repair when it resolves the observed problem. Share a predicate
or projection only when its callers rely on the same semantics. Evaluate broader consolidation when
repeated changes or demonstrated coupling justify it. Preserve distinctions such as strategy intent,
transport acceptance, execution quantities and user-visible status when their completion evidence
differs. Avoid duplicate writable state merely to make diagrams look uniform.

Before a repeated design, delivery, retry or review mechanism, declare a finite numeric budget and
stop condition. One inventory pass and at most two delivery passes are useful starting bounds for
this optional route. Scale the budget to the actual scope, and stop on acceptance or a real remaining
dependency. A direct edit needs no orchestration record. Do not add a new mechanism merely to manage
the audit itself.

## Implement and verify within scope

For an authorized repair or optimization, change the smallest coherent slice through the normal
entry point. Preserve existing callers, persisted data, reservations, deduplication and retry
semantics. When a cross-owner policy changes, inspect the producer, consumer, final effect check and
user-visible projection so the changed decision reaches the intended outcome.

Verify at the lowest altitude that can falsify the change. Use a local transition test for local
logic, a real component seam for persistence or serialization, and a bounded lifecycle or user
scenario when ordering or resumed work is the claim. Preserve evidence origin. Synthetic SDK events
prove the supplied scenario, while live effects need their own evidence and authority.

For performance changes, compare the same representative input and expected behavior. Report the
measured operation, data size, relevant environment, before/after method and limitations. Confirm
output or invariant equivalence where required. Distinguish a reconstructed old-function comparison
from an executed old-release comparison, and projection latency from end-to-end latency.

## Report the actual operational result

Provide a compact inventory and decisions sized to the requested scope, using an existing project
record when sufficient. A detailed catalog or diagram is appropriate when the user requests the
whole program. Finish with concrete behavior deltas.

| Report item | Required meaning |
| --- | --- |
| Coverage | Which source, entry points, implicit forms and external boundaries were examined |
| Finding | Trigger, causal transition or interaction, consequence and affected scope |
| Decision | Selected option and why it improves the intended outcome, or the evidence for keeping the current design |
| Changed behavior | What a caller, operator or subsequent consumer now observes, with source locations |
| Verification | Exact relevant checks, evidence origin, result and remaining limits |

Separate documentation or diagram changes from implemented operating logic and measured effects.
Do not claim runtime recovery, performance gains, deployment or native hook registration solely from
a revised skill, catalog, graph or passing static contract test.

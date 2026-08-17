# Specify, implement, review, drill

This is a navigation guide, not an installable catch-all skill.

## Direct path

1. **Frame and specify when needed.** State the outcome and minimum invariant. When a material
   mechanism is proposed, ask `Do we really need this to make things happen?` and `Is there a
   simpler and more direct way?`; run the conditional necessity/complexity gate owned by
   `engineering-specification` before freezing the contract or RED cases. Compare deletion,
   manual, embedded/ephemeral, platform-primitive, and retained-mechanism paths with their
   complexity, authority, recovery, and failure-state cost. Skip this phase when the contract and
   mechanism are already sufficient, and bind later acceptance to observable behavior rather than
   a mechanism proxy.
2. **Implement.** Make the smallest coherent authorized slice and run the lowest check that can
   falsify its claim.
3. **Review.** Use a lightweight findings-first review for ordinary changes. Use a formal independent
   gate only for explicit final, release, migration, pre-cutover, mandated, or recurring
   sibling-blocker decisions.
4. **Drill or close evidence.** Convert a stable incident to a regression, or use completeness
   synthesis to choose the missing seam/lifecycle check. Re-enter implementation only with repair
   authority.
5. **Stop honestly.** Finish when the requested claim is supported, or preserve the exact blocker,
   evidence, and next safe action in a WAL when continuity warrants it.

## Opt-in canon orchestration profile

Use the [engineering WAL canon orchestration
reference](../skills/engineering-wal/references/canon-orchestration.md) only when a material long task
must preserve a frozen product target across handoffs or separately qualify core behavior and several
host, deployment, or adoption targets.

The profile treats PM, Spec Architect, Red Team, Implementer, and QC as bounded logical roles over the
existing canonical owners. PM routes and synthesizes; the evidence-observing owner classifies findings.
It coordinates a budgeted specification loop, a budgeted delivery loop, and a fail-closed shadow reopen
without creating another specification, review, evidence, or release authority.

A lower achieved stage is a milestone. Any hard scope reduction uses the append-only commitment-floor
transition guard. Readiness remains a vector of core, `seam[target]`, `release[target]`, and
`releaseOverall`; one ready target cannot hide an incomplete required target.

Existing owner protocols take precedence for necessity, implementation, formal review, evidence
closure, and incremental invalidation. The profile adds no new installable skill, daemon, database,
universal stage taxonomy, or persistent coordinator.

Any external fan-out must pass Baton. If Baton is unavailable, do not dispatch around it: execute
bounded role passes sequentially, or stop `INCOMPLETE` when the requested claim requires independence.
Canvas, CodeGraph, AAR, supervision, and provider adapters remain optional aids, not proof or authority.

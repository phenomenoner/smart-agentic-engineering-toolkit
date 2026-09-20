# User-journey polish with bounded evidence

Use this reference when the authorized outcome is a usable feature or interaction and either:
- the user requests functional polish, daily-use readiness, or parity for named interactions;
- component checks pass but the corresponding real user workflow fails;
- natural input can select a different tool, backend, adapter, or execution path from the tested one; or
- a changed output or state is consumed by a later turn, screen, retry, or supported continuation.

Do not activate solely for the word "polish", a cosmetic edit, a pure formatter, a known local fix
with a sufficient focused check, documentation-only work, or the presence of multiple components.
Do not reinterpret a request to assess or diagnose as permission to implement, install, or test live.
The main agent owns the claim and evidence judgment. This protects feature-completion claims;
it creates no new runtime authority, persistent registry, reviewer role, or mandatory document.

## Preserve the actual outcome

Reuse the current request and existing acceptance notes. When the outcome is not already clear,
summarize these five items inline, not in a new template or ledger:

1. A representative user request or action, phrased without implementation instructions.
2. The observable result that makes the user's task complete, including the useful content or effect.
3. The supported entry point and actual execution path, including model-visible alternatives.
4. The most relevant continuation, cancellation, or failure behavior affected by this change.
5. Explicit exclusions and authority limits, distinguished from assumptions or unverified support.

Infer ordinary glue needed for the requested outcome: a reply needs its intended target, delegated
work needs a collected result, and a persistent conversation needs usable subsequent turns. Do not
ask the user to enumerate every normal interaction. Ask only about choices that materially change
product scope or authority. Do not turn an entire reference product into a parity requirement.
Resolve ordinary choices from current source and product conventions before asking or opening a
specification step; an omitted detail alone is not material ambiguity.
Do not silently narrow a broad authorized deliverable to a convenient five-line scenario: the
scenario samples its contract, and uncovered required behavior remains open.

## Inspect the path the user can actually take

Trace input -> route/tool selection -> work -> result acceptance -> visible outcome -> next consumer.
Inspect only links relevant to the changed claim. A route catalog or an enabled tool is not proof
that its lifecycle works. Distinguish similarly named mechanisms with different owners, such as a
host-managed child and a backend-native child. For credible exposed alternatives, either establish
their supported behavior, converge the exposed surface on the supported route within authority, or
report the unsupported path. Prompt wording that merely hopes the model selects the tested route
does not establish capability containment.

Recheck the downstream consumer when adding output fields or state: history reconstruction,
subsequent commands, UI refresh, persisted restore, or result collection, as applicable. Choose the
nearest consumer capable of revealing the defect; do not manufacture a full lifecycle matrix.

## Two kinds of evidence, only when needed

- **Controlled behavior:** use the smallest deterministic regression at the actual failing seam.
  Mock unrelated dependencies; do not mock away the failure-bearing parser, storage contract, or
  routing decision. A fixed tool call proves that route, not natural route selection.
- **Natural selection or interaction:** when selection is part of the claim, give the representative
  request without naming the implementation tool or supplying the implementation code. Observe the
  path actually taken, completed work, final result, and relevant next action. Use the admitted tool
  surface and settings. A cheaper model or synthetic ingress is useful but does not automatically
  establish another model's routing behavior, real-client ingress, or visual rendering.

Use an offline scenario if it faithfully represents the claim. A live model, provider delivery,
account action, reboot, or client interaction needs its existing authorization; skill activation
does not supply it. If unavailable, finish authorized lower-tier work and label the exact remaining
claim unverified. Do not make the user the default integration tester when authorized automation
can exercise the seam; do not pretend automation exercised a client surface it cannot access.
Interpret authorization from the whole current session: an explicitly authorized end-to-end test
includes its ordinary necessary steps. Do not split that grant into redundant approval requests;
clarify only a materially different or unresolved effect.

## Keep the cost proportional and finite

Before a scenario/retry loop, declare its count. Default: one representative natural scenario and
one affected continuation, using shared platform fixtures where behavior is equivalent. Add a case
only for a named, contract-relevant distinct path; declare that case before execution. These are
initial sampling budgets, not permission to ignore other required outcomes. Do not test the Cartesian
product of every model, channel, tool, interruption, and lifecycle phase.
The continuation shares the same authorized effect/call budget; it is not a free extra provider run.
Use offline evidence or mark it unverified when the authorized live allowance is exhausted.

After a failure, reduce it to a discriminating seam check instead of repeatedly buying live runs.
At most two same-cause attempts; an unchanged third is prohibited. Existing task budgets are shared,
not reset by loading this reference. Unknown side effects require reconciliation, never blind replay.
Do not add a new service, harness, state machine, review wave, or audit ledger merely for polish.
Reuse valid evidence for unchanged paths and test only meaningful platform or model-route differences.

## Decide and stop

Apply the parent skill's **Report evidence origin and real-dispatch gaps** section when reporting
this scenario. Controlled tests may use synthetic inputs or recorded real-event replay; identify
which. When actual dispatch is missing, separately assess automated execution and budget approval,
and the exact steps requiring human interaction. Do not substitute "please test it" for that assessment.

Keep three claims distinct in existing status prose: implemented, integrated, and verified in the
representative user scenario. These are evidence labels, not a new workflow engine. Report separately
whether failure handling was verified: a clear failure notice is useful but does not mean the user's
requested work completed. Child creation, a tool response, a healthy process, a delivered message,
test counts, or estimated percentages alone do not establish useful task completion.

A reviewer already selected for the task should challenge the most plausible ordinary alternate
path or next action omitted by the tests; this does not automatically select a reviewer or formal gate.
Stop once the authorized outcome has sufficient evidence or the bounded observation budget is spent;
state any material gap without inventing a new release claim. Retire an incident-specific scenario
when an equivalent maintained regression covers it, the supported path is removed, or the owner
changes the contract. Preserve historical evidence as scoped history rather than accumulating active
rules. For long tasks, keep one current outcome/route/gap summary; do not reload every historical note.

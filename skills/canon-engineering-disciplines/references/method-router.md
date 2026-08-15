# Method Router

Select by the question that must be answered. Prefer the smallest set that covers distinct obligations.

| Question | Primary method | What it contributes | Common misuse |
|---|---|---|---|
| How can controller actions, missing feedback, timing, or process-model flaws cause loss? | STPA | Losses, hazards, constraints, unsafe control actions, causal scenarios | Calling any control diagram an STPA analysis |
| Why did a completed event emerge across technical and organizational controls? | CAST | Retrospective control-structure and responsibility analysis | Using it as a prospective release gate |
| How does normal work vary and resonate across functions? | FRAM | Work-as-done variability and functional coupling | Treating it as a normative risk verdict |
| How do stocks, flows, feedback, and delays shape behavior over time? | System dynamics | Executable dynamic hypotheses and sensitivity analysis | Calling an uncalibrated causal-loop map a simulation |
| How can component or interface failure propagate upward? | FMEA | Bottom-up failure modes, effects, detection, mitigation | Missing hazardous interactions among healthy parts |
| What combinations can cause a known top event? | FTA | Top-down logical decomposition | Treating independence assumptions as facts |
| What deviations from intended parameters are plausible? | HAZOP | Guideword-driven deviation discovery | Using it without a clear design intent or boundary |
| Are temporal states, transitions, safety, and liveness coherent? | TLA+/PlusCal or P | State-machine and interleaving exploration | Claiming implementation conformance without a link |
| Are relational, ownership, namespace, or topology constraints coherent? | Alloy | Bounded counterexample search over relations | Treating a bounded search as an unbounded proof |
| Does implementation recover at selected crash points? | Failpoints and deterministic replay | Executable fault evidence and reproducible counterexamples | Substituting sampled points for a complete failure model |
| Does a distributed black-box history satisfy a consistency model? | Jepsen-style history checking | Faulted distributed execution plus history analysis | Applying it to a local file transaction with no distributed history |
| Is a decision claim supported, qualified, and challengeable? | GSN or SACM | Claims, context, argument, evidence, assumptions, defeaters | Paper assurance or circular self-attestation |
| Can an artifact be tied to declared inputs, builder, and steps? | SLSA, in-toto, reproducible builds | Provenance and supply-chain integrity | Inferring runtime correctness from provenance |
| How will an incident produce durable recurrence prevention? | SRE incident learning | Impact, causes, remediation, owners, learning | Treating a postmortem as verification evidence |

## Selection heuristic

1. Select one spine for the central uncertainty.
2. Add a second discipline only if it answers a materially different question.
3. Add an executable evidence method when the selected analytical method cannot falsify the implementation claim.
4. Add an assurance-case method only when a consequential decision needs traceable evidence and defeaters.
5. Stop at two to four methods unless the user explicitly requests a comprehensive comparison.

## Useful combinations

- Recovery protocol: STPA + TLA+/P + failpoints; add GSN/SACM only for a release decision.
- Deployment integrity: Alloy for path/topology relations + in-toto/SLSA for artifact lineage + executable preflight/rollback evidence.
- Recurring production incident: CAST + deterministic replay + SRE incident learning.
- Human/tool adaptation: FRAM + STPA when variability can create unsafe control actions.

Do not turn these combinations into mandatory chains.

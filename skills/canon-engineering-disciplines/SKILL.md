---
name: canon-engineering-disciplines
description: Identify, compare, and combine established engineering disciplines for system-level assurance problems without conflating what each method proves. Use when a user explicitly invokes this skill; asks what an emerging engineering method should be called; asks to compare or synthesize methods such as STPA, CAST, FRAM, FMEA, FTA, HAZOP, formal state methods, fault injection, assurance cases, supply-chain provenance, or SRE; or faces a cross-cutting assurance problem spanning control hazards, temporal recovery, fault exploration, evidence validity, artifact provenance, and operational learning. Do not trigger for routine bug fixes, ordinary testing, a single known method, or normal release work.
license: MIT
metadata:
  toolkit-version: "0.1.0"
  toolkit-phase: "assurance"
  toolkit-contribution-protocol: "v1"
---

# Canon Engineering Disciplines

Select the smallest fitting set of established disciplines, keep their claims separate, and expose assumptions, defeaters, and residual gaps. Treat this skill as a read-only advisory router, not as a workflow authority.

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

## Preserve authority boundaries

- Follow user, system, repository, and active skill instructions first.
- Grant no authority to modify code, run tests, delegate, review, merge, publish, release, deploy, cut over, contact providers, or access live systems.
- Never revive, invoke, edit, or cite a `RETIRED` rule or skill as authority. When current wording resembles a retired workflow, transfer only the reusable engineering lesson to an active successor unless the user explicitly reauthorizes the retired item and resolves the conflict.
- Do not auto-chain methods or active skills. Recommend a downstream skill only when its own trigger and task authority apply.
- Keep method selection distinct from implementation, verification, independent review, and operational authorization.

## Produce a bounded discipline synthesis

1. Define the system boundary, unacceptable loss, decision claim, decision authority, and exact failure model.
2. Inventory the important controllers, state transitions, trust or authority seams, feedback, delays, artifacts, and evidence consumers.
3. Read [method-router.md](references/method-router.md) and select the smallest two to four disciplines that address materially different questions. Select one method when one is enough.
4. Record why each method is selected and why plausible alternatives are rejected or deferred.
5. Read [method-boundaries.md](references/method-boundaries.md). Separate every claim by verification altitude and evidence type; list assumptions, defeaters, freshness conditions, independence, and explicit non-claims.
6. Use [discipline-synthesis.md](templates/discipline-synthesis.md) for a full assessment or [claim-evidence-defeater.md](templates/claim-evidence-defeater.md) when the task only needs an assurance matrix.
7. Cite primary or authoritative sources. Use [primary-sources.md](references/primary-sources.md) as a starting map, then verify unstable facts or exact editions when they matter.
8. End with the smallest next experiment, model, review, or operational gate able to falsify the leading claim. Do not prescribe every available method.

## Route by question, not prestige

- Use STPA for unsafe control actions, feedback, timing, and flawed controller process models; use CAST for a completed adverse event.
- Use FRAM for work-as-done variability and adaptive couplings; use system dynamics only for accumulations, flows, delays, and simulated behavior over time.
- Use FMEA for bottom-up component failure propagation, FTA for a known top event, and HAZOP for systematic deviations.
- Use TLA+/PlusCal or P for temporal state, interleavings, ownership, safety, and liveness; use Alloy for bounded relational and topology questions.
- Use failpoints and deterministic replay for executable crash or interleaving evidence; use Jepsen for externally observable distributed histories.
- Use GSN or SACM to structure claims, argument, evidence, assumptions, context, defeaters, and confidence.
- Use SLSA, in-toto, and reproducible-build practice for artifact lineage and build provenance.
- Use SRE incident learning to turn an operational failure into owned recurrence-prevention work.

## Keep claims non-substitutable

Never let one evidence class stand in for another:

- A formal model proves properties of its abstraction, not implementation conformance.
- A test proves exercised behavior, not untested state-space completeness.
- A review proves a bounded independent judgment, not runtime behavior.
- Provenance proves artifact lineage, not behavioral correctness.
- Process health proves liveness, not end-to-end provider delivery.
- A qualitative causal-loop diagram is not a calibrated system-dynamics model.
- A polished assurance case is not proof when its evidence, assumptions, or defeaters are weak.

Use qualified language such as `model-checked under assumptions`, `tested at T2`, or `provenance-bound`. Do not imply regulatory certification, production readiness, or cutover authority.

## Hand off without duplicating active skills

When execution is separately authorized, route rather than duplicate:

- Incident normalization and replay packages: `incident-to-regression`.
- Completeness, verification altitude, and completion claims: `completeness-and-test-synthesis`.
- Independent hash-bound review: `batch-complete-independent-review`.
- Rust-specific implementation or review: `pragmatic-rust-guidelines`.
- Subagent dispatch: active `baton-fanout-skill` only.
- Long-running commands: `long-run-supervisor`.

Claude remains explicit-user-request only. A method name, diagram, model, or generated packet never authorizes a merge, release, deployment, or cutover.

---
name: engineering-debugging
description: Diagnose a failing test, build, runtime, or user-visible behavior when the root cause is not yet established. Use to reproduce safely, reduce the failure, rank and falsify hypotheses, identify the causal seam and blast radius, and report residual uncertainty. Do not use when the cause and requested patch are already explicit, when an established incident only needs a reusable regression package, for a generic explanation, or for code review. Diagnosis alone does not authorize a repair.
license: MIT
metadata:
  toolkit-version: "0.4.0"
  toolkit-phase: "diagnose"
  toolkit-contribution-protocol: "v1"
---

# Engineering Debugging

Find the smallest causal explanation that accounts for the observed failure. Prefer evidence that
can make a hypothesis false over a long list of plausible stories.

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

## Apply the scope brake

Use this skill when the symptom is known but the cause is not. Before doing anything, state:

- the observed symptom and expected behavior;
- the authority boundary: diagnose only, or diagnose and repair;
- the safest reproducible environment and forbidden live effects;
- the current candidate bytes, configuration, and environment when they matter.

Do not mutate production, user data, credentials, remote state, or unrelated repository work to get
a reproducer. If diagnosis-only was requested, stop before editing even after finding the cause.

Finding severity does not grant scope. Diagnosis may uncover `IN_SCOPE`, `SCOPE_GUARD`,
`ADJACENT_RISK`, or `OUT_OF_SCOPE` work, but it does not authorize any repair. Report the
classification and evidence against the original deliverable and claim. If a proposed response would
change acceptance, release rigor, the system boundary, writable ownership, or external effects,
route a scope-change checkpoint to `engineering-specification` before implementation.

## Build a discriminating observation

1. Preserve the original error, exit state, timing, and relevant inputs without copying secrets.
2. Reproduce at the lowest safe altitude that still contains the symptom. If it cannot be
   reproduced, say so and distinguish observed facts from hypotheses.
3. Reduce one dimension at a time: input, caller, configuration, platform, timing, dependency, or
   lifecycle phase.
4. Prefer an existing failing test or safe probe. Do not manufacture a fail-first ceremony when the
   pre-change state is unsafe, unavailable, or already adequately captured.
5. Bind comparisons to the same relevant bytes and environment. A different binary or stale service
   process cannot falsify a source-level hypothesis.

## Maintain and falsify hypotheses

Keep a short table with:

- hypothesis;
- evidence it explains;
- observation that would falsify it;
- result;
- remaining uncertainty.

Test the cheapest high-information hypothesis first. Do not promote correlation, timing proximity,
or a green retry to root cause. When a change makes the symptom disappear, test the causal boundary
or a nearby counterexample before concluding.

For concurrency, ownership, retry, rollback, cleanup, or identity-reuse seams, use
`specify-temporal-ownership` to make the forbidden trace and linearization requirement explicit.
For a stable incident that should become a reusable replay, hand off to `incident-to-regression`
after diagnosis rather than mixing incident packaging into root-cause search.

## Trace blast radius

After localizing the cause, inspect:

- all callers that can reach the unsafe operation;
- sibling helpers and alternate platform/provider paths;
- startup, steady state, shutdown, retry, recovery, rollback, and replacement phases;
- cached, packaged, generated, and running copies that may differ from source;
- tests that appear green because they stop below the failing seam.

Use CodeGraph when a current index can materially improve cross-file caller tracing, then confirm in
source and tests. Graph output is navigation, not proof.

## Output

Report:

1. reproduced symptom and exact evidence;
2. established root cause, or the narrowest surviving hypotheses;
3. causal mechanism and affected callers/phases;
4. what was ruled out and how;
5. repair options and tradeoffs only when useful;
6. the smallest regression or runtime check that would distinguish a repair;
7. residual gaps, unsafe/unavailable checks, and the stop boundary.

Do not call a workaround, restart, retry, or passing unrelated suite a root-cause proof. Do not claim
the issue is fixed unless repair was authorized, implemented, and verified separately.

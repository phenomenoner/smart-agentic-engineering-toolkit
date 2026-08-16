# completeness-and-test-synthesis

A portable skill for answering a concrete question: does the available evidence
support the exact readiness claim, and what is the smallest missing test?

It is intentionally not a mandatory end-of-task gate. Ordinary local changes
should use ordinary local checks.

For an explicit release, migration, or cutover, it also owns the incremental evidence map: source
correctness, artifact identity, formal review, installed instance, live host, and external
publication remain separate gates, and only cells affected by changed bytes or seams are reopened.

## Core model

Choose the lowest altitude where the relevant defect would actually fail:

- **T0:** static shape, compile, formatting, schema, or generated consistency.
- **T1:** local behavior of one unit.
- **T2:** a touched real component or contract seam.
- **T3:** a lifecycle, multi-component, recovery, or user scenario that lower
  tiers cannot faithfully represent.
- **T4:** an authorized live or externally visible claim.

A write or state transition does not automatically require T3. A higher tier is
useful only when it exposes a credible failure that a cheaper check cannot.

For a safe, reproducible existing bug, prefer a regression that fails for the
old defect and passes after the repair. Fail-first is not mandatory for net-new
behavior, documentation or mechanical changes, an already-failing test, or an
unsafe or unavailable pre-change state. In those cases, use a current-state
check that would still fail if the behavior were removed or the defect returned.

## When to use it

Use the skill for:

- an explicit `done`, readiness, merge, release, or cutover judgment;
- recurring regressions or green tests followed by broken real use;
- cross-component or lifecycle behavior whose evidence altitude is unclear;
- converting sanitized logs, traces, or receipts into replay tests.

Do not invoke it merely because implementation work ended. It does not require
a project adapter, verdict table, plan, WAL, handoff, full suite, or independent
review when those artifacts do not improve the claim.

## Structure

```text
completeness-and-test-synthesis/
├── README.md
├── SKILL.md
└── references/
    ├── incremental-release-progression.md
    └── receipt-to-replay.md
```

The progression reference is loaded only for an explicit cross-stage release decision. The replay
reference is loaded only when recorded evidence must become a deterministic fixture.

## Installation

Use this repository's installer, or copy the folder into a compatible
user-level skills directory. The loader reads `SKILL.md`; this README is public
documentation and does not control runtime triggering.

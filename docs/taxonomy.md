# Skill taxonomy and routing

The toolkit is a collection, not one universal workflow. Select the smallest skill whose output and
stop condition match the request.

## Core lifecycle

```text
unresolved behavior -> engineering-specification
unknown failure cause -> engineering-debugging
authorized clear change -> engineering-implementation
ordinary or formal review -> batch-complete-independent-review
readiness/evidence gap -> completeness-and-test-synthesis
stable incident -> incident-to-regression
long or interrupted work -> engineering-wal
temporal check-then-mutate seam -> specify-temporal-ownership
material skill learning -> evolve-engineering-toolkit
```

The arrows are possible handoffs, not an automatic chain. For example, a known small defect may go
directly to implementation; an ordinary review does not require formal release artifacts; and a
short edit does not need a WAL.

When a material plan introduces a mechanism, state the outcome/invariant and ask `Do we really need
this to make things happen?` and `Is there a simpler and more direct way?` The conditional full gate
belongs to `engineering-specification`; implementation, review, evidence, drill, continuity, and
adapter surfaces carry only short handoff/challenge guards. No additional skill, status, schema,
catalog row, or mandatory lifecycle is created.

## Distinctions that prevent overlap

- `engineering-debugging` establishes cause. `incident-to-regression` packages an already observed,
  stable incident into reusable evidence.
- `batch-complete-independent-review` finds defects in candidate work.
  `completeness-and-test-synthesis` judges whether a claim has adequate evidence.
- `engineering-specification` defines behavior before a material change.
  `specify-temporal-ownership` is the specialized contract for races, generations, ownership, and
  destructive effects after a check.
- `engineering-wal` is durable continuity. Context Canvas is an optional semantic map and snapshot
  index, never a prerequisite or evidence authority.
- `codegraph-first-navigation` is bounded current-repository navigation. Understand Anything is a
  persistent graph/dashboard integration. AAR/IPython CodeGraph is for exported AAR source-like
  artifacts, not live runtime state.
- `programmatic-tool-composition` batches pure/read-only tool work in one agent.
  `baton-fanout-skill` gates delegated workers. They are not interchangeable.

## Implicit invocation

Implicit invocation is allowed only for narrowly described, low-surprise task classes. WAL,
provider/model adapters, product maintenance, and broad assurance routing are explicit-only. The
machine-readable policy lives in `catalog/skills.json` and each skill's `agents/openai.yaml`.

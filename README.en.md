# Smart Agentic Engineering Toolkit

[繁體中文](README.md)

A public collection of focused, testable, and evolvable software-engineering skills. It captures a
practical workflow without imposing one mandatory methodology on every task.

The recommended path is: specify when uncertainty warrants it, implement, review, then close an
evidence gap or turn an incident into a drill until the claim is supported or a real stop condition
is reached. A task may enter directly at diagnosis, implementation, review, or incident conversion.
A small edit does not automatically need a plan, WAL, worktree, subagent, or full test suite.

When a specification would introduce a material mechanism, it explicitly asks “Do we really need
this to make things happen?” and “Is there a simpler and more direct way?” It separates the
observable outcome/invariant from a mechanism proxy and checks deletion, manual operation,
embedding or decision-time computation, and existing platform primitives before adding new state.
This is a conditional brake; an already clear small contract stays on the direct path.

## What it adds

- Behavioral specifications with observable acceptance, non-goals, failure semantics, and a
  falsification plan instead of document ceremony, including the complexity, authority, recovery,
  and failure-state cost of a retained material mechanism.
- Separate skills for implementation, debugging, review, readiness judgment, and incident-derived
  regression so that one task class does not silently claim another's authority.
- Temporal ownership design for TOCTOU, ABA, PID or handle reuse, replacement cleanup, and rollback,
  including forbidden traces, linearization points, stable capabilities or CAS, and exact
  interleaving tests.
- WAL as the minimum durable resume map. Canvas, CodeGraph, AAR, knowledge graphs, and model workers
  remain optional augmentations rather than proof or authority.
- An upstream-improvement protocol in every owned skill: material learning becomes public-safe
  evidence, an exact canonical patch, and a discriminating eval. A draft PR is opened only when the
  active task authorizes GitHub writes; otherwise the agent returns a PR-ready packet and offers to
  submit it.

## Skill groups

| Group | Skills |
| --- | --- |
| Core | `engineering-specification`, `engineering-debugging`, `engineering-implementation`, `engineering-wal`, `batch-complete-independent-review`, `completeness-and-test-synthesis`, `incident-to-regression`, `specify-temporal-ownership`, `evolve-engineering-toolkit` |
| Assurance | `canon-engineering-disciplines` |
| Navigation and composition | `codegraph-first-navigation`, `programmatic-tool-composition` |
| Windows and Codex adapters | `long-run-supervisor`, `codex-cli-luna-worker`, `codex-app-mcp-update` |
| Explicit provider adapter | `claude-independent-review` |

See [`catalog/skills.json`](catalog/skills.json) and [`docs/taxonomy.md`](docs/taxonomy.md) for exact
triggers, non-triggers, implicit-invocation policy, and canonical ownership.

## Codex plugin installation

The repository root is the plugin source. Releases provide a Git tag, GitHub release, and a
per-path hash lock. Register a tagged checkout as a local marketplace, install the plugin, fully
restart Codex Desktop, and prove behavior in a **new task**. Configuration, catalog visibility, or
health alone is not behavior proof. Exact plugin and standalone profile commands are in
[`docs/installation.md`](docs/installation.md).

If loose skills with the same names already exist, first keep them in place and prove the plugin by
using a uniquely new skill in a fresh task. Then follow the recoverable, one-skill-at-a-time cutover
in [`docs/migration.md`](docs/migration.md). Never use a generic force switch to overwrite unknown
changes.

## External integrations

In 0.1.0, `baton-fanout-skill` remains owned by its existing repository and is only pinned as an
integration. Context Canvas, Understand Anything, and AAR also retain their own canonical owners.
See [`docs/integrations.md`](docs/integrations.md). Superpowers is comparative material only; its
mandatory bootstrap, TDD, worktree, fan-out, and reviewer chain are not reactivated.

## Validate and contribute

```powershell
python -m pip install --editable ".[dev]"
python scripts/validate_toolkit.py
python -m pytest -q
```

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before proposing a change. Do not edit an installed skill
or plugin cache. Change canonical source and include the activation, non-activation, or workflow eval
that distinguishes the repair.

## Claim boundary

The first public 0.1.0 release targets repository, plugin-package, isolated-install, fresh-task drill,
and GitHub-byte verification. It does not claim OpenAI endorsement, Plugin Directory approval, or
deployment/availability of AAR, Canvas, or an external model provider.

License: MIT. See [`NOTICE`](NOTICE) and
[`docs/influences-and-provenance.md`](docs/influences-and-provenance.md) for external influences and
provenance.

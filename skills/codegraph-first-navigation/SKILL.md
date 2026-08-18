---
name: codegraph-first-navigation
description: Navigate indexed codebases with CodeGraph using one rich query, bounded caller/callee or impact follow-ups, and source/test confirmation. Use for repository-scoped architecture questions, cross-file control or data-flow tracing, implementation lookup, refactor planning, change-impact analysis, or affected-test selection when a current `.codegraph` index or callable CodeGraph surface is available. Do not use for prose/config/literal search, interactive knowledge-graph generation, or unindexed projects.
license: MIT
metadata:
  toolkit-version: "0.3.0"
  toolkit-phase: "navigation"
  toolkit-contribution-protocol: "v1"
---

# CodeGraph-First Navigation
<!-- TOOLKIT-CONTRIBUTION-PROTOCOL:v1 -->

Use the graph to navigate and form hypotheses. Use current source and tests or runtime evidence to verify. Treat a missing static edge as unknown, not proof that a runtime path is impossible.

## Respect the active authority boundary

- Follow higher-priority host and repository instructions for whether an index may be initialized, refreshed, or rebuilt. This skill grants no write authority.
- Bind every query to the active repository and worktree. Do not reuse an index or result from another branch, worktree, or source revision.
- Keep `.codegraph/` as generated local metadata. Do not cite it as source, review, release, or runtime evidence.
- Use the normal governed editing interface after navigation. CodeGraph identifies candidate change locations; it does not authorize changes.

## Select the right surface

1. Check the repository root, active worktree or branch, and graph status.
2. Prefer the callable `codegraph_explore` MCP tool when exposed. Pass the absolute project path and start with one task-level query naming the relevant symbols, files, layers, and desired sink or outcome.
3. Treat line-numbered source returned by `codegraph_explore` as already read. Do not reopen the same source unless the graph output is truncated, stale, ambiguous, or lacks a detail needed for verification.
4. Use the CodeGraph CLI for a capability absent from the callable surface:

   ```text
   codegraph status <project>
   codegraph node --path <project> <qualified-symbol-or-file>
   codegraph callers --path <project> <qualified-symbol>
   codegraph callees --path <project> <qualified-symbol>
   codegraph impact --path <project> <qualified-symbol>
   codegraph affected --path <project> <changed-files...>
   ```

   Check `--help` rather than inventing flags when the installed version differs.
5. Use ordinary search and selected reads for documentation, configuration values, generated artifacts, raw data, exact literals, or code outside graph coverage.

## Investigate with a bounded working set

1. Orient with one rich `explore` request. Avoid a sequence of overlapping searches.
2. Retain only the likely entry points, core symbols, shared dependencies, candidate change nodes, related tests, and unresolved dynamic boundaries.
3. Resolve ambiguous names with qualified symbols, paths, and source confirmation. Never silently choose the first same-name node.
4. Trace representative important paths. Use callers, callees, node, or impact only when the first result leaves a concrete question unanswered.
5. Read source surgically to confirm conditions, transformations, error behavior, side effects, registrations, and environment-dependent behavior.
6. Before editing a shared or public node, inspect direct callers, indirect dependents, implementations or overrides, routes or handlers, related tests, and dynamic-boundary uncertainty.
7. After executable edits, allow or request the authorized graph refresh, check status, and re-query the affected area. Invalidate pre-edit graph results.
8. Choose focused tests from the observed impact. Add runtime or integration evidence when static analysis cannot represent an important path.

## Check dynamic boundaries explicitly

Look for reflection, dependency injection, plugin registries, event buses, generated code, runtime decorators, string-based imports, dynamic routes, environment-controlled loading, monkey patches, RPC discovery, and framework magic. State which boundary limits the graph claim.

## Keep output efficient and honest

- Bound `maxFiles`, relationship depth, paths, and source volume.
- Keep large graph payloads out of the final response.
- Separate graph-supported findings, source-confirmed behavior, tests or runtime verification, and remaining uncertainty.
- On an unavailable, unhealthy, stale, or unindexed graph, fall back once to normal search plus selected reads and disclose the limitation. Do not retry the same failed graph operation repeatedly.

## Coexist with other skills

- CodeGraph locates impact and callers after a material design's outcome-first necessity decision.
  It cannot answer `Do we really need this to make things happen?` or `Is there a simpler and more
  direct way?`, establish mechanism necessity, or authorize a design; keep that conditional decision
  with `engineering-specification`.
- Use `understand-*` when the requested output is a persistent interactive knowledge graph, dashboard, onboarding map, or domain graph. Do not build that artifact as part of this skill.
- Use language or domain implementation skills after CodeGraph identifies the relevant source surface.
- Use `completeness-and-test-synthesis` only when the user requests a readiness judgment or its own trigger conditions apply; graph impact alone is not completeness proof.
- Use `baton-fanout-skill` before any subagent delegation. CodeGraph navigation does not imply fan-out.

## Contribution protocol

When real use of this skill exposes a material improvement, missing safeguard, conflict, or retirement candidate, do not silently patch an installed copy, plugin cache, or generated projection. The toolkit repository is the canonical writable owner for toolkit-owned behavior.

1. Record a public-safe counterexample or redacted reproducer; the canonical commit; the current skill version and SHA-256; expected versus observed behavior; materiality; and compatibility, authority, safety, evidence, dependency-conflict, or retirement impact.
2. Prepare an exact unified diff against canonical source, the smallest activation, non-activation, or workflow eval that distinguishes the change, and provenance or change notes.
3. If GitHub writes are explicitly authorized, open a draft pull request against the canonical owner and read back its identity and state. Otherwise return a PR-ready packet and explicitly offer to open the draft pull request. Never claim that a draft pull request exists without that readback.
4. Route external dependency behavior changes to the actual upstream. A toolkit pull request may change only its pin, integration metadata, conflict handling, or retirement state unless ownership has explicitly transferred.

Material means that activation, non-activation, authority, safety, compatibility, observable workflow behavior, evidence quality, dependency conflict, or supported or retired status changes. A wording preference alone does not create PR churn.

# Changelog

All notable changes are documented here. Versions follow Semantic Versioning.

## [Unreleased]

- Count net financial savings as a delegation benefit even with more tokens and no latency gain.
  Use model-specific input/output/cached-token prices across parent, workers and coordination;
  preserve authorized routes and distinguish estimated savings from measured billing.

- Require tracked-file public locks to include newly staged intended paths and pass post-commit
  validation before exact-candidate installation claims; pre-commit validation alone can miss new files.

- Clarify that the optional Hermes reviewer route must actually isolate Terra/high rather than
  reusing a globally Luna-pinned worker or toggling shared config. Separate configured routing
  from unavailable per-request telemetry; reject observed mismatches without inventing readback.
- Preserve narrow-review evidence in its original form while adapting non-native reports to the
  existing validator envelope. No new reviewer, schema or mandatory gate is introduced.

- Keep already authorized implementation moving after specification and diagnosis; preserve
  specification-only and diagnosis-only stops. Narrow temporal-ownership activation to concrete
  mutable check-before-destructive-effect races and make ordinary test/diff evidence sufficient
  without separate necessity or object-hash records.
- Separate PMO responsibilities from the optional CK / Hermes routing adapter, use compact WALs
  by default, and reserve formal transition guards for a demonstrated continuity problem. An
  ordinary final look remains finding review. Refresh graphs only for further navigation.
- Make long-command guidance obey active host communication limits and reuse native sessions.
  Distinguish a validated local plugin installation from release publication and fresh-host
  activation; local delivery does not require a PR, remote CI, or repeated approval.

- Require acceptance reports to distinguish synthetic tests, recorded real-event replay, and actual
  backend execution. Unverified real-dispatch claims include separate automation/budget and precise
  human-assistance assessments, preserving existing approvals and bounded execution.

- Consolidate functional-polish and user-journey evidence in the existing completeness skill,
  with narrow specification, implementation, and review entry points. Distinguish natural tool
  selection, alternate execution owners, useful final outcomes, and affected subsequent interactions
  from isolated component passes. Keep cosmetic/local changes direct and scenario loops bounded.

- Add the CK PMO routing profile: the main agent retains coordination, integration, verification, and
  final authority; verified Prime Agent minions become the default Luna/max execution pool with
  explicit route readback, while Terra/high review may select a native subagent or minion according to
  complexity and independence needs.

## [0.5.0] - 2026-08-24

- Add risk-local `consequence × estimated frequency` disposition, effect-local fail-closed behavior for
  high-consequence boundaries, and evidence-backed bounded fail-open for low-consequence,
  low-frequency, reversible residuals without candidate-wide L3 contagion.
- Require the smallest no-live-effect constructibility probe before broad formalization of an
  unfamiliar OS, provider, or runtime primitive.
- Give canon orchestration explicit default limits for specification passes, delivery passes,
  same-cause retries, and full-review waves; stop unchanged third attempts and budget exhaustion as
  `INCOMPLETE` instead of manufacturing another successor or reviewer cycle.
- Pin toolkit version and canonical commit for long tasks; changed rules require an explicit rebind
  checkpoint or a fresh task rather than silent mid-task policy mixing.
- Retire unconditional finding-driven reopen language while preserving fail-closed custody, authority,
  privacy, security, irreversible, cutover, rollback, and delivery boundaries.
- Add a supplemental proportional-risk and bounded-loop eval corpus without adding a skill, profile,
  transition schema, persistent registry, or mandatory lifecycle.
- Document host-native installation and verification routes for Codex App plugins, Hermes Agent native
  skills, and other Agent Skills-compatible harnesses.
- Retire and remove the Codex CLI Luna compatibility bridge from installable skills and routing
  evals; unavailable native model routes now fall back to direct work or another exposed native lane.
- Enforce finite formal-review budgets in bind, report-validation, and synthesis paths; reject
  unsupported legacy reviewer fields and topologies beyond the primary-reviewer or narrow-auditor
  ceiling.
- Permit a hash-bound current-state discriminator when a safe observed fail-first incident state is
  unavailable, and require lifecycle or live test altitude only when the claim needs it.
- Filter ignored paths before filesystem metadata probes in both Git and archive release walks, so a
  broken ignored environment link cannot abort validation on Windows.
- Verify Hermes skill pickup through a fresh chat slash-command invocation instead of the affected
  `--skills ... -z` route that can run without injecting the named skill.

## [0.4.0] - 2026-08-21

- Add a conditional unit-first composition strategy for seams with multiple independently failing
  links or expensive/high-risk integration feedback: cover the contract-relevant failure partition,
  then composition boundaries, then only the native or lifecycle claim lower tiers cannot represent.
- Bind composite-seam fan-out to Baton with exclusive ownership and main-agent synthesis; permit
  eligible native Luna/max workers only for stable bounded code generation or low-judgment scouts,
  exclude Luna from architecture, security, authority, release judgment, and independent review, and
  set the Codex independent-review floor at Sol/high or a stronger exposed lane.
- Refresh the pinned external Baton routing integration and add supplemental activation,
  non-activation, composition-order, and model-route contracts without adding a new skill or
  mandatory lifecycle.

## [0.3.0] - 2026-08-18

- Add a cross-lifecycle anti-scope-drift safeguard: classify new findings against the authorized
  deliverable and claim, permit only in-scope work and minimum scope guards without amendment, stop
  claim or release-rigor escalation at an owner-approved checkpoint, and preserve explicit amended
  and direct small-work paths through a public supplemental eval corpus.

## [0.2.0] - 2026-08-17

- Add an opt-in long-task canon orchestration profile that freezes the product commitment floor and
  target terminal stage with a stateless append-only transition guard, composes five logical
  responsibility lenses through budgeted specification, delivery, and shadow-reopen routing, binds
  finding reclassification to the evidence-observing owner, and separates core, per-target seam,
  release, and overall readiness without adding a new skill, daemon, database, or release authority.
- Separate source correctness, artifact identity, formal review, installed instance, live host, and
  external publication evidence; invalidate by exact changed objects and executable seams so
  documentation or review-intake repairs reuse unaffected evidence while runtime drift and
  executable semantic changes reopen the required pickup, drill, and review cells.
- Clarify that `specify-temporal-ownership` requires a concrete temporal check-then-effect seam,
  and add a static cross-component ownership non-activation case that forbids temporal ceremony when
  runtime mutation, replacement, delete, retry, and concurrency are out of scope.

## [0.1.0] - 2026-08-16

- Build the first public plugin with focused specification, diagnosis, implementation, continuity,
  review, completeness, incident, temporal-ownership, navigation, orchestration, and adapter skills.
- Add a versioned contribution protocol that turns material field learning into canonical,
  test-backed, PR-ready changes.
- Add machine-readable catalog, profiles, external dependency boundaries, provenance, release locks,
  behavior evals, and recoverable standalone installation.
- Refuse linked, reparse, unmanaged, diverged, and concurrent install targets; publish with atomic
  no-replace moves; compare-and-swap the managed receipt; and identify the tree actually moved
  before rollback decisions.
- Bind behavior-evaluation acceptance to the exact Git-clean candidate, including non-ignored
  untracked public bytes, and reject archive, unstable-readback, or ambiguous candidate identity.
- Close standalone receipt shape and semantics, remove Git attestation, and re-read exact receipt
  and target bytes before returning install success with exact-byte compensation on failure.
- Add a conditional outcome-first necessity and complexity gate for material mechanisms, with short
  handoff guards across implementation, review, evidence, incident, and orchestration entrypoints;
  explicit small work remains direct.
- Route every short first-principles guard back to the one `engineering-specification` owner without
  adding another skill, schema, profile, or catalog row.
- Fence target compensation after a foreign post-commit receipt is observed, and preserve the exact
  regression bytes under a behavior-oriented public test path.

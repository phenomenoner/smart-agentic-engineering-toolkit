# Canon orchestration for long engineering tasks

This is an opt-in composition profile for material work that must preserve a product commitment
across long execution, compaction, role handoffs, or several host seams. It is not a new installable
skill, product authority, daemon, database, mandatory lifecycle, or release orchestrator.

## Existing owner precedence

This profile coordinates existing owners; it does not replace or restate their procedures:

- `engineering-specification` owns observable behavior, acceptance, non-goals, compatibility, and
  mechanism necessity;
- `engineering-implementation` owns authorized source changes and focused implementation checks;
- `batch-complete-independent-review` owns ordinary and formal independent review, finding-set
  closure, and review fixed points;
- `completeness-and-test-synthesis` owns claim-to-evidence closure, verification altitude, verdict
  synthesis, and the incremental release progression rules;
- `engineering-wal` owns the compact continuity map used by this profile.

When this reference and an owner protocol differ, the owner protocol takes precedence. This profile
adds only commitment-floor identity, bounded role routing, and target-scoped aggregation.

## Necessity and complexity decision

The observable outcome is: a long task cannot lose or silently lower its requested product outcome,
and one failed host seam reopens only the claims that depend on it. An unstructured note cannot
mechanically reject a rewritten floor or an unsupported `DONE` claim.

A new skill, repository-wide product schema, daemon, database, role registry, or persistent
coordinator is still unnecessary. The retained mechanism is one optional WAL block plus a versioned,
task-local transition envelope and the stateless skill-owned
`skills/engineering-wal/scripts/validate_orchestration_transition.py` guard. It compares two task-local
JSON snapshots. `engineering-wal` owns only this envelope's serialization and continuity rules; the
canonical specification, implementation, review, and completeness skills still own decision meaning.
The guard does not schedule agents, run tests, decide product stages, or grant authority.

## Activate proportionately

Use this profile when at least one condition is material:

- a requested target has repeatedly been reduced to an intermediate milestone;
- work crosses sessions, compaction, handoffs, or several independently owned slices;
- specification and implementation require distinct challenge passes;
- core behavior and one or more host, platform, deployment, or adoption targets need separate claims;
- a failed gate would otherwise cause broad repeated testing without identifying what changed.

Keep the direct path for a small explicit change, one low-risk host, an ordinary typo, or one bounded
check. Roles are responsibilities; they do not imply five simultaneous subagents.

Any external fan-out must pass Baton. If Baton is unavailable, do not bypass it: run bounded logical
role passes sequentially in the main agent, or stop `INCOMPLETE` when independence is required.

Role separation alone is not independence. When the frozen target requires independent challenge or
acceptance, use a distinct reviewer identity and isolated frozen inputs; self-review cannot be relabeled
as independent.

## Non-negotiable invariants

1. **Freeze the commitment floor.** Bind the outcome, target terminal stage, hard requirement and
   acceptance IDs, required targets, amendment authorities, and the completeness/readiness authority.
   Non-goals remain owned by the canonical specification digest; changing one advances specification
   identity and resets dependent claims. A lower stage is a milestone, not completion.
2. **Amend instead of erasing.** Any change to a frozen floor requires an append-only, owner-authorized
   amendment bound to the previous and new floor digests. Compaction, elapsed time, difficulty, or a
   PM decision is not amendment authority.
3. **Bind every claim.** Record task and state generation, specification digest, candidate digest,
   evidence pointers, and target cells. Historical PASS does not transfer to changed identities.
4. **Keep axes separate.** Core, each seam, `release[target]`, and `releaseOverall` are distinct. One
   ready target cannot hide another required target that is `BLOCKED` or `INCOMPLETE`.
5. **No silent role crossing.** Implementers do not rewrite acceptance, QC does not repair source,
   reviewers do not self-approve repairs, and the PM does not classify away observed failures.
6. **Route through canonical owners.** The evidence-observing owner classifies a finding. The PM routes
   and synthesizes; it cannot unilaterally reclassify or close that finding.
7. **Bound every loop.** Activation records pass/generation budgets. Repeated or oscillating finding
   signatures stop `BLOCKED` or `INCOMPLETE`; budget exhaustion never weakens the commitment floor.

## Minimal durable record and transition guard

Keep detailed specifications, source, tests, formal reviews, and receipts in their existing canonical
locations. Extend the task WAL with pointers to one task-local snapshot chain containing:

```text
identity:
  taskId; state generation
  specification generation + digest
  candidate generation + digest

commitmentFloor:
  generation + canonical digest
  outcome + targetTerminalStage
  requirementIds + acceptanceIds
  requiredSeams
  amendmentAuthorities + readinessAuthority

verdicts:
  core
  seams[target]
  release[target]
  releaseOverall

findings:
  id + class + classificationOwner + dispositionOwner + status + blocking
  affectedCells + firstUnsafeOperation + evidenceIds
  append-only reclassifications + owner disposition

commitments:
  one evidence cell for every frozen requirement and acceptance ID

decisionReceipts:
  append-only positive PASS/READY decisions
  authority + floor/specification/candidate digests + evidence IDs

loopBudgets:
  specification max/used passes
  delivery max/used passes
  last guard-derived semantic-delta signature + append-only signatureHistory

completion:
  status + achievedStage
```

Seam and release keys are exactly the frozen `requiredSeams`, including their non-positive cells; an
optional or phantom target cannot be introduced outside an authorized floor amendment. Commitment keys
are exactly the frozen requirement and acceptance IDs: every frozen claim retains its cell until an
authorized floor amendment removes it, and an unbound extra claim is malformed rather than progress.
New finding `affectedCells` and positive pass projection are likewise bound to the active frozen
namespace: `core`, `core/<requirement-or-acceptance-id>`, `seam/<required-seam>`,
`release/<required-seam>`, or `releaseOverall`. A transition may retain an existing finding whose ID and
packet came from the exact receipt-bound previous snapshot after a cell is removed; that continuity trust
never authorizes a new finding or progress. Standalone/import validation is active-only: amendment JSON
does not establish historical namespace authority by itself.

A floor amendment contains:

```text
fromFloorGeneration; toFloorGeneration
previousFloorDigest; newFloorDigest
oldTarget; newTarget
authority; reason
affectedRequirementIds; affectedAcceptanceIds; affectedSeams
invalidatedEvidenceIds
```

The three affected-ID lists cover every added or removed frozen requirement, acceptance, or required
seam and may reference only IDs from the old or new floor. Evidence from affected prior cells is named
in `invalidatedEvidenceIds`, and those cells reset before reevaluation. Invalidated IDs accumulate across
the snapshot's amendment history and cannot reappear in a current commitment or active positive-decision
receipt. Finding reclassification requires new class-specific evidence while preserving the original
observation and evidence packet. Reclassification and disposition-owner closure occur in separate
snapshot transitions; they cannot be laundered into one atomic update.

Before accepting a later snapshot, run:

```bash
# Toolkit source tree
python3 skills/engineering-wal/scripts/validate_orchestration_transition.py \
  validate previous.json current.json

# Installed engineering-wal skill root
python3 scripts/validate_orchestration_transition.py validate previous.json current.json
```

Use `digest snapshot.json` to compute the canonical floor digest. Input is strict JSON: duplicate keys,
non-standard numeric constants, and snapshots deeper than the documented bound are rejected.
Exact input snapshot bytes for both successfully read files are SHA-256 bound in every
`validate` receipt, including parse failures; preserve the receipt in the WAL and read back the accepted
current snapshot before use. The `previous` argument is that accepted exact snapshot, not a general import
path. An imported or reconstructed snapshot must first satisfy active-only snapshot validation; an
unverified amendment list cannot convert retired or phantom cells into trusted history.
The guard rejects silent floor changes, identity drift without generation advance, stale positive
claims after identity change, deleted amendment/finding/decision history, non-owner finding
reclassification, ownerless PASS/READY promotion, caller-aliased or delta-free loop passes, per-target or
aggregate release laundering, terminal-state reopen, and unsupported `DONE`. A newly appended decision
receipt is eligible for a delivery delta only when it binds a cell that currently exists and is positive,
with the matching decision, readiness authority, floor, specification, and candidate identities. Semantic
packets exclude IDs, prose, and unknown extras and normalize unordered evidence/affected-ID lists;
commitment packets project only the claim ID, status, and evidence IDs and sort by claim ID before
hashing. JSON map order and metadata-only aliases therefore cannot consume or disguise a loop pass.

During a transition, every newly introduced finding enters as `OPEN` / `OPEN`, without closure or
reclassification history. Reclassification must leave it open; only a later disposition-owner
transition may close it. Once closed, every known finding field is immutable and any recurrence uses a
new finding ID. Historical closed findings may be present at the initial/import trust boundary, but
cannot be introduced as fresh semantic progress.

A green transition proves only those structural invariants; it does not prove product behavior or
evidence freshness. Authority, disposition-owner, and classification-owner IDs are opaque
caller-provided identities: the guard enforces binding and continuity but does not authenticate a human
or agent. Adversarial multi-principal use requires an external signing or capability authority rather
than more orchestration state here.

## Envelope governance and compatibility

`engineering-wal` owns `schemaVersion: 1` as a task-local composition-envelope format, not as product,
specification, review, or release authority. Unknown versions fail closed. If a canonical owner protocol
changes a verdict, finding, evidence, or readiness rule, that owner protocol takes precedence in meaning,
but an existing guard version must not silently reinterpret it: publish and test a new envelope version,
deprecate the conflicting version, and migrate explicitly before accepting another transition.

Migration never rewrites accepted history in place. Preserve the old snapshot and exact-byte receipt,
append a migration record or pointer under the new version's documented procedure, and validate the
first new-version snapshot against that preserved boundary. The direct path does not create or migrate
this envelope.

## Five logical roles

### PM / primary agent

Owns continuity, routing, and final synthesis. It freezes the initial floor and authorized amendment
identities, maintains snapshot pointers and loop budgets, and reports milestones separately from the
requested target. It does not own specialist classification, evidence closure, or release authority.

### Spec Architect

Uses `engineering-specification` to define observable behavior, non-goals, ownership, compatibility,
failure behavior, acceptance IDs, and dependency/reopen mappings. RED fixtures can make acceptance
precise; they do not prove that a future implementation is feasible or correct.

### Red Team Reviewer

Challenges the frozen specification for missing requirements, unsafe assumptions, unowned boundaries,
unfalsifiable acceptance, stage gaming, and simpler alternatives. Formal fixed-point and batch-complete
semantics remain owned by `batch-complete-independent-review`.

### Implementer

Changes only authorized bytes against one frozen specification generation and returns a bound candidate
plus focused evidence. A missing or contradictory observable requirement is raised as `SPEC_GAP`; the
implementer does not silently reinterpret acceptance.

### QC / evidence observer

Verifies the frozen candidate against the frozen specification and emits evidence-bound findings. QC
separates product execution failure from harness, privilege, credential, dependency, or toolchain
inability. Readiness and evidence closure remain owned by `completeness-and-test-synthesis`.

## Loop A: specification convergence

`Spec Architect -> Red Team -> specification-owner disposition -> next frozen specification`

The activation record sets a maximum pass and generation budget. Each pass must close a named finding,
change a frozen contract input, or add discriminating evidence. A pass signature is computed by the
guard from the canonical identity, finding, owner-receipt, or evidence delta; caller-chosen aliases are
not accepted. A repeated or oscillating signature exits
`BLOCKED` or `INCOMPLETE`; it never authorizes narrower acceptance. Snapshot accounting advances a
loop by at most one pass and never silently extends its activation budget. Closing an active loop records
exactly one new discriminating pass. A `BLOCKED`, `INCOMPLETE`, or `CLOSED` loop cannot be relabelled to
another terminal outcome; changed floor/specification/candidate dependencies must first reactivate the
applicable loop. Reactivation to `ACTIVE` is mandatory in the dependency-change transition itself and
cannot be combined with a new pass or immediate reclosure; a later transition must record the new
discriminating pass before closing again.

Exit only when every hard commitment maps to falsifiable acceptance, material boundaries are explicit,
and no accepted blocking specification finding remains open. `SPEC_READY` is a handoff milestone, not
product completion.

## Loop B: delivery convergence

`Implementer -> QC -> evidence-owner disposition -> next frozen candidate`

The activation record also bounds delivery passes and candidate generations. Each pass changes bound
candidate bytes, closes a finding, or adds discriminating evidence. QC reports the full affected batch;
`engineering-implementation` owns repairs and `completeness-and-test-synthesis` owns evidence closure.

A core-ready candidate may be reported as a milestone. Loop B exits only with the target-scoped verdict
owned by completeness synthesis, or a named `BLOCKED`/`INCOMPLETE` handoff.

## Shadow specification reopen

A shadow reopen is routing back to the existing specification owner, not another authority path. It
requires a supported `SPEC_GAP` packet with the acceptance or missing behavior, spec/candidate identity,
minimal reproducer or contradiction, affected cells, and evidence.

Disposition is fail-closed:

- **accept:** the specification disposition owner issues a new specification generation and invalidates
  dependency-mapped cells; changed identities reset positive verdicts before reevaluation;
- **reject as false:** the specification disposition owner closes it with contrary evidence;
- **reject as not a spec gap:** the classification owner appends a supported reclassification after the
  specification disposition; it cannot disappear;
- **narrow:** if any hard requirement, acceptance, required target, outcome, or terminal stage changes,
  create an authorized commitment-floor amendment and invalidate the named cells.

Unchanged evidence reuse follows the incremental release progression owner. This reference does not
redefine its changed-object, executable-seam, review-intake, or freshness rules.

## Finding ownership and routing boundary

The evidence-observing QC, reviewer, or specification owner creates the initial class and an immutable
`classificationOwner`. A separate `dispositionOwner` records the canonical owner permitted to close the
finding. Every packet includes affected cells, first unsafe operation, and evidence IDs.
The PM may route but cannot rewrite it. It also cannot classify it or substitute itself as disposition
owner.

The supported classes are `CORE_DEFECT`, `SPEC_GAP`, `SEAM_DEFECT`,
`HARNESS_OR_ENV_BLOCKER`, `AUTHORITY_OR_EXTERNAL_BLOCKER`, and `REVIEW_COVERAGE_GAP`.
Canonical owners decide disposition: specification for contract gaps, implementation for authorized
repairs, review for review findings, and completeness for evidence/readiness gaps.

A class change requires an append-only record from the classification owner with old/new class,
old/new disposition owner, reason, affected cells, first unsafe operation, and new evidence. For
example, a host Git process that cannot start is `HARNESS_OR_ENV_BLOCKER` until evidence reaches product
execution; the PM cannot use that label to preserve core PASS after an observed product failure. The
existing finding packet cannot otherwise be deleted or rewritten; disposition-owner closure preserves
it, and a later recurrence gets a new finding ID.

## Core, seam, and release aggregation

Use a vector and an explicit aggregate:

```text
core = PASS
seam[linux-wsl] = PASS
seam[windows-native] = INCOMPLETE
release[linux-wsl] = READY
release[windows-native] = INCOMPLETE
releaseOverall = INCOMPLETE
```

Each `release[target]=READY`, and `releaseOverall=READY`, requires core PASS, the applicable seam PASS,
bound specification/candidate identities, no open blocking finding, and supported evidence for every
frozen requirement and acceptance ID. Every positive PASS/READY cell also points to a newly appended
receipt when it is promoted; the receipt binds the frozen readiness authority, floor, specification,
candidate, and evidence. Overall readiness additionally requires every target frozen in
`requiredSeams` to be READY. Optional targets are excluded only by the frozen claim scope or an
authorized amendment.

Formal review closure, evidence altitude, and exact affected-cell invalidation remain owned by the
existing review and completeness protocols. A seam-only harness repair does not automatically reopen
all core proof; shared source or contract changes do.

## Completion guard

The transition guard treats an accepted `DONE` snapshot as terminal. It rejects `DONE` unless the
achieved stage equals the frozen target, `releaseOverall=READY`, core is PASS, every required target is
ready, every frozen requirement and acceptance ID has supporting evidence, the specification and
candidate are digest-bound, both loops are closed, and no blocking finding remains open.

If any condition is false, report the achieved milestone, target vector, blocker, and next safe action.
Never promote `PASS_UNDER_ASSUMPTIONS`, `INCOMPLETE`, a planned repair, or an unexecuted check.

The supplemental eval corpus is a static contract surface, not fresh-agent proof. Actual adoption must
record observed selection, prohibited effects, output, and receipt/transcript evidence in an isolated
run; `NOT_RUN` remains an explicit gap.

## Handoff checklist

At every boundary pass only current bound inputs and minimum useful context:

- commitment floor digest and amendment history;
- spec generation and acceptance IDs;
- candidate identity and dirty state;
- affected cells, finding owner, and required evidence tier;
- loop budget, stop condition, next safe action, and forbidden actions.

The PM reads back artifacts before updating the WAL. Delegation completion, elapsed effort, or a
plausible summary is not acceptance.

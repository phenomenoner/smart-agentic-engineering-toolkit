# Product specification 0.1.0

Status: release candidate

## Outcome

Publish one Codex plugin and Agent Skills-compatible repository containing focused, independently
useful engineering skills. The preferred lifecycle is guidance:

`specify when needed -> implement -> review -> close evidence or convert an incident into a drill`

No task must traverse every phase. Direct, small work remains direct.

For a material mechanism choice, specification asks `Do we really need this to make things happen?`
and `Is there a simpler and more direct way?` before contract or RED freeze. It distinguishes the
observable outcome/minimum invariant from a mechanism proxy and considers deletion, manual action,
embedding or ephemeral state, an existing platform primitive, and only then a new mechanism.

## Behavioral invariants

1. Each installable skill has a unique focused user goal, positive and negative triggers, inputs,
   outputs, stops, dependencies, and explicit non-claims.
2. Skill selection never expands write, GitHub, provider, deployment, or live-operation authority.
3. Verification uses the lowest altitude that can falsify the claim. No artifact or method is quality
   evidence merely because it exists.
4. WAL is the minimum optional continuity map. Canvas, CodeGraph, collaboration, provider adapters,
   and AAR fail open to direct work and never become prerequisites.
5. Every owned skill carries `TOOLKIT-CONTRIBUTION-PROTOCOL:v1`. Material field learning produces a
   public-safe counterexample, exact canonical patch, discriminating eval, and a draft PR only when
   GitHub writes are authorized; otherwise it produces a PR-ready offer.
6. One component has one writable canonical owner. Installed projections, plugin caches, generated
   artifacts, and downstream mirrors are never source.
7. Installers refuse unmanaged or diverged same-name targets, preserve complete prior generations,
   and contain rather than overwrite when ownership changes during rollback.
8. Public claims bind exact source/release bytes and executed evidence. OpenAI endorsement, Plugin
   Directory publication, deployment, and provider execution remain separate external claims.
9. Material design specifications record the simplest viable necessity decision and an auditable
   complexity, authority, recovery, and failure-state budget before acceptance is frozen. Already
   explicit small work bypasses this conditional gate.

## Owned scope

The 16 owned skills and their profile, trigger policy, and source mode are authoritative in
`catalog/skills.json`. External components are authoritative in `dependencies/*.json`. Product,
domain, official/system, runtime-state, cache, receipt, and private evidence material is excluded.

## Acceptance

The release must pass:

- structural, frontmatter, reference, catalog/profile/provenance, public-hygiene, and release-lock
  validation;
- one direct activation and one explicit non-activation case per skill;
- one material mechanism case that prefers a simpler existing primitive, plus one explicit small
  contract case that proves the direct path remains available;
- overlap, external dependency, retirement, and unsupported-action cases;
- contribution behavior with and without GitHub-write authority;
- clean, exact, managed update, unmanaged conflict, local divergence, pre-publish failure,
  post-publish drift, and rollback installer cases;
- skill-local script tests on supported platforms;
- isolated plugin installation and a fresh Codex task performing a real bounded engineering drill;
- one independent review of the exact candidate, CI, and GitHub commit/tag/release/hash readback.

The machine-readable case corpus is `evals/cases/acceptance.json`.

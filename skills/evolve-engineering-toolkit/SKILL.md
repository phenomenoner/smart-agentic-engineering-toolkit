---
name: evolve-engineering-toolkit
description: Turn a material Smart Agentic Engineering Toolkit skill improvement, missing safeguard, activation conflict, compatibility issue, or retirement candidate into a public-safe evidence packet, exact source patch, discriminating eval, and draft pull request when GitHub writes are authorized. Do not use for harmless wording preferences, product-code fixes, silent local/plugin-cache edits, dependency source changes against the wrong owner, or publication beyond the user's authority.
license: MIT
metadata:
  toolkit-version: "0.1.0"
  toolkit-phase: "maintenance"
  toolkit-contribution-protocol: "v1"
---

# Evolve Engineering Toolkit

Make useful learning flow back to the single canonical source without turning every local preference
into a pull request or silently forking installed behavior.

<!-- TOOLKIT-CONTRIBUTION-PROTOCOL:v1 -->
## Improve this skill upstream

When this skill itself reveals a material improvement, missing safeguard, conflict, or retirement
candidate, apply the same protocol recursively to canonical source, never to an installed copy:

1. preserve the canonical commit, version, hash, redacted reproducer, and observed behavior;
2. prepare an exact patch and smallest discriminating eval;
3. include provenance, compatibility, migration, and changelog impact;
4. open a draft PR only when GitHub writes are authorized; otherwise present a PR-ready packet and
   explicitly offer to open it;
5. route external dependency behavior changes to their actual upstream.

## Confirm materiality and ownership

A proposal is material when it changes activation or non-activation, authority, safety,
compatibility, observable workflow behavior, evidence quality, a dependency conflict, or
supported/deprecated/retired state. Decline process for a private phrasing preference with no
behavioral effect.

Resolve the writable canonical owner before preparing a destination:

- toolkit-owned skill: this repository;
- pinned external dependency: upstream for behavior, toolkit for pin/integration/conflict metadata;
- generated distribution or plugin cache: never a source;
- ambiguous or dual owner: stop publication and prepare an ownership-resolution proposal first.

Do not widen an engineering task into a GitHub write. Read-only inspection and a PR-ready patch are
allowed when they stay within scope; opening a PR requires explicit or already applicable write
authority.

## Build the improvement record

Capture:

- canonical repository, base commit, toolkit and per-skill behavior version;
- exact `SKILL.md` and affected resource hashes;
- host/version and relevant optional integrations;
- redacted prompt class or reproducer;
- expected selection, non-selection, stop, or workflow behavior;
- observed behavior and why it is material;
- related/conflicting skills and canonical owners;
- exact proposed diff;
- before/after activation, non-activation, edge, or workflow eval;
- license/provenance, compatibility, versioning, changelog, and migration impact;
- authorization state and whether any remote write actually occurred.

One anecdote may justify a regression proposal, not a universal rule. Phrase the invariant and show
which additional prompt classes or counterexamples delimit it.

## Design the patch

Keep the smallest coherent patch. A trigger change normally requires both positive and negative
evals. An authority or side-effect change requires explicit stops and an unsupported-action case. A
retirement requires a reason, successor, last-supported version, implicit-invocation change,
migration path, and proof that active catalogs/installers no longer point to the old name before
removal.

Before adding a skill, protocol, durable state, lifecycle, or public artifact, ask `Do we really
need this to make things happen?` and `Is there a simpler and more direct way?` Record the observable
outcome/minimum invariant, why deletion, a manual action, embedding/ephemeral state, an existing
platform primitive, or an existing canonical skill cannot own it, and an auditable complexity
budget for added state, authority, recovery, and failure states. Prefer updating the existing owner;
do not create a new catalog/profile surface merely to host the safeguard.

Classify version impact:

- major: rename/removal, authority boundary, incompatible I/O/evidence contract, mandatory
  dependency, canonical ownership transfer, or material trigger/non-trigger break;
- minor: backward-compatible optional capability, profile, or supported host;
- patch: clarification, packaging repair, or eval improvement with no intended behavior change.

## Validate and submit

Run the repository validator, the affected direct and non-activation cases, relevant conflict cases,
and public hygiene/provenance checks. Do not claim improvement from prose alone when the failure was
behavioral.

If GitHub writes are authorized, create a focused branch, commit only intended bytes, push, open a
**draft** PR, and read back the remote base/head and PR URL. Otherwise provide:

```text
Canonical base:
Material finding:
Redacted reproducer:
Expected / observed:
Exact patch:
Discriminating eval and result:
Compatibility / version / migration:
Provenance:
Remote action: NOT PERFORMED
Offer: ready to open a draft PR when authorized
```

Never state that a PR, issue, release, or upstream change exists unless its remote identity was
actually read back.

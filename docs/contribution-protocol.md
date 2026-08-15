# Contribution protocol

Every toolkit-owned skill contains `TOOLKIT-CONTRIBUTION-PROTOCOL:v1` inline so that the behavior
survives standalone installation.

A complete proposal records:

- canonical repository and base commit;
- toolkit and skill behavior version plus affected hashes;
- host/version and relevant optional integrations;
- redacted prompt class or reproducer;
- expected selection, non-selection, stop, or workflow behavior;
- observed result and materiality;
- related or conflicting skills and their canonical owners;
- exact unified diff;
- smallest before/after eval;
- license, provenance, compatibility, version, changelog, and migration impact;
- whether GitHub writes are authorized and what remote action actually occurred.

For a toolkit-owned skill, the draft PR targets this repository. For a pinned external dependency,
source behavior goes to its upstream; this repository may accept a pin, integration, conflict, or
retirement change. An ambiguous owner must be resolved before publication.

Do not generalize one private anecdote into a universal rule. Redact the case, state the invariant,
and include counterexamples that define its boundary.

# Proportional workflow maintenance

This maintenance change starts from toolkit commit
`e64c60f946fb42289ffaabecd59660a4940c0826` (0.5.0 plus unreleased maintenance).
It preserves user authority, independent-review honesty, private-data boundaries, and separate
source, installation, activation, and publication evidence. It adds no skill, service, or gate.

| Conflicting or excessive instruction | Resulting behavior |
| --- | --- |
| Specification always stops before implementation, including an already authorized build | Stop for specification-only work; continue an authorized build once the contract is sufficient |
| Diagnosis says it cannot authorize any repair, even during a fix request | Diagnosis creates no authority; existing repair authority remains usable |
| Retry, concurrency, or local mutation can summon temporal-ownership design | Require a concrete mutable check-before-destructive-effect seam with another actor or generation |
| Ordinary tests require a necessity record; ordinary edits require exact Git-object recording | Use the focused test and diff; add machinery only when its claim needs it |
| PMO label can select a host-specific minion route | Common PMO responsibilities remain portable; select the CK / Hermes adapter explicitly |
| A minimal WAL includes formal generations, verdict vectors, and transition digests | Use a compact continuity note; expand only for an explicitly selected guard |
| Every executable edit refreshes the navigation graph | Refresh only when more graph navigation is needed |
| A final look can select the formal review protocol | Ordinary final looks use finding review unless independence or release acceptance is requested |
| Historical long blocking windows suppress current host communication | Honor current limits while continuing the same operation |
| A local skill install implies remote CI, PR, or release completion | Verify local source and installation; report fresh-host activation and publication separately |

The changed paths and exact patch are recorded in Git. The supplemental corpus
[`proportional-workflow.json`](../evals/cases/proportional-workflow.json) includes both direct-path
and protected-boundary cases. Its expected decisions are authored contracts, not proof that an
installed agent executed them. A read-only scenario exercise also cannot establish real repair,
installation, or fresh-task pickup. Keep those claims separate in delivery notes.

These changes are local maintenance, not a new published release. The package version remains the
published baseline; a local install uses a unique cachebuster and its exact source commit. No schema
or formal transition format changes, no migration of existing logs, and no rewriting of previously
accepted policy-bound evidence are required.

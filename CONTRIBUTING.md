# Contributing

The best contribution is a small, evidence-backed improvement to one focused behavior. Do not edit
an installed skill directory or plugin cache and then treat that copy as source.

## Before proposing a change

1. Identify the canonical owner and exact base commit. External dependency behavior belongs to its
   upstream; this repository owns only its pin and integration boundary unless ownership was
   explicitly transferred.
2. Capture a public-safe reproducer. Remove secrets, private paths, proprietary content, raw model
   prompts/outputs, and unrelated runtime state.
3. State expected versus observed activation, non-activation, stop, or workflow behavior and why the
   difference is material.
4. Before adding a skill, protocol, component, persistent state, lifecycle, or other public
   mechanism, ask `Do we really need this to make things happen?` and `Is there a simpler and more
   direct way?` Record the outcome/minimum invariant; deletion, manual, embedding/ephemeral, and
   existing-platform alternatives; why the existing canonical owner is insufficient; and an
   auditable complexity, authority, recovery, and failure-state budget. Prefer updating an existing
   owner; a new catalog/profile row needs evidence that it cannot express the behavior.
5. Prepare the smallest source patch and the smallest eval that fails or distinguishes the old
   behavior and passes the proposed behavior.
6. Record versioning, compatibility, migration, deprecation, license, provenance, and changelog
   impact.

Material changes affect activation, authority, safety, compatibility, observable workflow,
evidence quality, dependency conflict, or supported status. A harmless wording preference does not
need a pull request.

## Required checks

```powershell
python scripts/validate_toolkit.py
python -m pytest -q
```

Run any skill-local script tests and the relevant activation, non-activation, conflict, or adapter
drills. Use the lowest reliable verification altitude; do not add a full suite or external review
solely as ceremony.

## Pull requests

- Use a focused branch and open a draft PR while behavior or evidence is still under review.
- Include canonical base, affected skill/version/hash, redacted reproducer, expected and observed
  behavior, exact checks and results, compatibility/migration, and provenance.
- Do not combine a skill improvement with unrelated product code, dependency updates, or live
  operations.
- Never claim that a PR, release, or remote change exists until its remote identity is read back.

If GitHub writes are not authorized, provide the same material as a PR-ready packet and explicitly
offer to open it. Do not silently fork local behavior.

## Deprecation and retirement

A deprecation identifies the reason, successor, last supported version, implicit-invocation state,
compatibility impact, migration path, and a test proving catalogs/installers no longer select the
old skill. Normal removals wait for the next major release. Security-sensitive removal may be
faster but still needs a recovery path.

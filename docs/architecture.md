# Architecture

## One repository, focused skills

The repository root is a Codex plugin and an Agent Skills-compatible collection. Every skill is
self-contained: its essential runtime instructions and references live inside its own directory.
Repository-level documents explain product architecture but are not required to execute an
individually installed skill.

The plugin exposes all toolkit-owned skills. Profiles classify the default core and optional host,
provider, navigation, or assurance adapters for standalone installers and compatibility reporting;
they do not create hidden mandatory chains.

## Authority layers

```text
canonical source + tag + lock
        |
        v
plugin or standalone managed projection
        |
        v
fresh host task selects one focused skill
        |
        v
repository/runtime evidence supports a bounded claim
```

Source presence, plugin configuration, catalog visibility, a started process, or a provider route
does not prove the downstream layer. Each compatibility claim records the actual altitude reached.

Installed skills, plugin caches, generated archives, runtime state, receipts, and downstream mirrors
are not writable canonical sources. The installer refuses ambiguous same-name or diverged targets by
default.

## Core and augmentations

The core remains useful with no Canvas, CodeGraph, AAR, collaboration, provider CLI, or PowerShell
supervisor. Optional integrations fail open to a direct workflow and never grant authority. Product
operation skills stay in their product repositories.

`engineering-specification` is the one procedural owner for the conditional necessity/complexity
gate. Other lifecycle and adapter skills ask `Do we really need this to make things happen?` and `Is
there a simpler and more direct way?` only at their own handoff boundary, then cross-reference that
owner. This avoids a second checklist, schema, runtime protocol, or canonical source.

## Release evidence

`manifest/toolkit.json` is the allow-list, `manifest/provenance.json` records origins and
modifications, and `manifest/public-lock.json` binds released paths. A release also requires
behavior evals, script tests, an isolated install, a fresh-task drill, independent review, and remote
tag/release readback. A hash lock proves byte identity, not correctness by itself.

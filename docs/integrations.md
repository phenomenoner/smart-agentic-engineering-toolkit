# External integrations

External integrations are versioned relationships, not vendored writable copies.

## Baton fan-out

`baton-fanout-skill` gates every subagent or CLI compatibility worker. During the 0.1 line, its
existing public repository and Codex branch remain canonical while local/public divergence is
reconciled. The toolkit records a pin and routing boundary but does not install or modify an editable
copy. If Baton is unavailable, work directly.

Canonical ownership may transfer in a future major release only through one reviewed cutover: merge
and tag the reconciled upstream, import the exact tag, change every governance pointer, make the old
repository maintenance-only or a redirect, and verify downstream pins. There must be no interval
with two advertised writable owners.

## Context Canvas

Canvas is an optional semantic map and historical snapshot index. Use only a trusted hook-provided
opaque identity. Never guess, derive, copy, or store that identity in a repository. Canvas absence
must not block otherwise authorized work; repository source, WAL, handoff, and executed evidence
remain authoritative.

## CodeGraph and Understand Anything

Use CodeGraph for bounded navigation of a current repository index and confirm conclusions in source
and tests. Use Understand Anything for persistent interactive graphs, dashboards, or onboarding.
Neither graph is runtime or release evidence. A stale external pin is a visible compatibility fact,
not authority to update it.

## Adaptive Agent Runtime

AAR operations, RLM, IPython, and exported-artifact navigation remain AAR-owned. A configuration or
catalog entry is not enough: claims require a fresh callable capability and task-relevant behavior.
AAR may compute, inspect, and propose; the host remains responsible for authorization, provider
execution, effects, and delivery.

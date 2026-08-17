---
name: claude-independent-review
description: Run a local Claude Code CLI as an independent, read-only, hash-bound engineering review gate. Use when the user explicitly asks Codex to invoke Claude or `claude -p` for a final code, release, migration, or pre-cutover review, especially when a PASS/BLOCKED decision must be bound to a frozen candidate and verification evidence.
license: MIT
metadata:
  toolkit-version: "0.2.0"
  toolkit-phase: "provider-adapter"
  toolkit-contribution-protocol: "v1"
---

# Claude Independent Review

Use the locally installed Claude Code CLI as an external reviewer, never as the implementation owner or live operator.

<!-- TOOLKIT-CONTRIBUTION-PROTOCOL:v1 -->
## Improve this skill upstream

When this skill reveals a material improvement, missing safeguard, conflict, or retirement candidate:

1. Do not silently patch an installed copy, plugin cache, or generated distribution, and do not
   widen the current task's authority. The toolkit repository is the canonical writable owner for
   toolkit-owned behavior.
2. Record a public-safe counterexample or redacted reproducer, the canonical toolkit commit, skill
   version and SHA-256, expected versus observed activation or behavior, materiality, compatibility,
   conflict or retirement impact, and verification evidence.
3. Prepare an exact unified diff against canonical source, the smallest activation, non-activation,
   or workflow eval that distinguishes the change, and any provenance or changelog update.
4. If GitHub writes are authorized, open a draft pull request to the canonical owner. Otherwise
   return a PR-ready packet and explicitly offer to open the pull request. Never claim a PR exists
   when it was not opened.
5. External dependency behavior changes go to the actual upstream; toolkit pull requests may change
   only its pin, integration metadata, conflict handling, or retirement state unless ownership has
   explicitly transferred.

Material changes affect activation, non-activation, authority, safety, compatibility, observable
workflow behavior, evidence quality, conflicts, or supported or retired status. A harmless wording
preference is not material.

## Preconditions

1. Require explicit user authorization to send scoped artifacts to Claude.
2. Finish implementation and required local verification first.
3. Freeze the candidate, public/source diff, manifest, and evidence hashes before review.
4. Exclude secrets, `.env` contents, bearer tokens, credentials, raw private receipts, personal identifiers, unrelated files, and live runtime data.
5. Do not let Claude modify files, run live commands, approve its own findings, or perform cutover.

## Resolve the model

Inspect the installed CLI:

```powershell
Get-Command claude
claude --version
claude --help
```

For Opus 5, probe the exact full model name without tools or persistence:

```powershell
claude -p --model claude-opus-5 --effort high --tools "" --no-session-persistence --output-format json "Reply with exactly MODEL_OK."
```

Accept `claude-opus-5` only when the JSON result succeeds and `modelUsage` reports canonical model `claude-opus-5`. Do not silently substitute an alias, fallback model, or another provider. Re-probe when the CLI or model availability may have changed.

Use effort `high` by default. Honor `xhigh` or `max` when explicitly requested and available; never reduce an explicitly requested minimum.

## Prepare the review input

Create a small, review-only bundle under the repository's approved scratch/evidence directory. Include:

- candidate identity and SHA-256 hashes;
- for a material added mechanism, the frozen answers to `Do we really need this to make things
  happen?` and `Is there a simpler and more direct way?`, the observable invariant, alternatives,
  and complexity/authority/recovery/failure-state cost; the reviewer may challenge this decision
  but cannot become its implementation or authorization owner; route redesign to
  `engineering-specification`, the detailed canonical owner;
- artifact-role and claim labels: source/input, immutable executed instance,
  immutable deployment instance, or derived mutable path; and whether the gate
  claims instance identity, build-recipe identity, reproducible rebuild, or
  semantic equivalence;
- exact diff or changed-file inventory;
- affected contracts and invariants;
- executed tests, counts, tiers, and raw result paths;
- known limitations and rollback/cutover gates;
- the requested decision schema.

Write neutral review instructions. Do not disclose the implementer's desired verdict or prior reviewer conclusions unless comparison is the explicit task. Give Claude only the files required to reconstruct the result.

Do not ask Claude to treat current byte equality at a build-tool-owned mutable
path as proof that an earlier execution is still present. Require an immutable
preserved copy for executed-artifact continuity. Require the effective build
recipe plus an independently reproduced result before accepting a
reproducible-build claim. When reviewing an append-only supersession of frozen
evidence tooling, require the complete consumer set, every preserved unaffected
assertion, the exact narrowed claim, and explicit disclosure of destroyed or
unavailable evidence.

## Run the reviewer

Run from the trusted repository or isolated review directory. Prefer safe mode, no session persistence, read-only tools, and structured output:

```powershell
claude -p `
  --model claude-opus-5 `
  --effort high `
  --safe-mode `
  --no-session-persistence `
  --permission-mode plan `
  --tools "Read,Glob,Grep" `
  --output-format json `
  --json-schema '<task-specific JSON schema>' `
  '<neutral review prompt with exact artifact paths and hashes>'
```

On Windows, prefer `scripts/invoke-claude-readonly-review.ps1` with prompt and schema files. The wrapper resolves `claude` from PATH by default; pass `-ClaudePath` when an explicit executable path is required. It re-enters under PowerShell 7 when called from Windows PowerShell 5.1, then uses `ProcessStartInfo.ArgumentList` so embedded JSON quotes remain one native argument. Do not pass a raw JSON schema directly from Windows PowerShell 5.1; native argument reconstruction can strip its quotes. For a release or cutover gate, also pass `-InvocationReceiptPath` in the private evidence area. The wrapper writes that receipt once with `CreateNew` after the child terminates, binding its own bytes, the Claude executable, prompt and schema identities, model, effort, safe-mode arguments, redacted stdout/stderr digests, and the exact terminal classifier. When `-OutputPath` is supplied, the wrapper cross-checks `result` against `structured_output` and writes only the schema report there; the full SDK envelope remains represented by the redacted receipt digests. Treat the receipt as route provenance, not as the review verdict.

Claude CLI may reject a Draft 2020-12 `$schema` URI even when it accepts the remaining structural keywords. The wrapper removes only the top-level `$schema` and `$id` metadata in memory, preserves the full constraint tree, and sends the normalized schema. Validate the returned structured object afterward with the original repository validator or original schema; normalization is transport compatibility, not a weaker acceptance contract.

When a PowerShell 5.1 launcher delegates to PowerShell 7, capture the child exit code immediately. Throw on nonzero and `return` on success; do not use `exit $LASTEXITCODE` from the outer wrapper because an unset or transport-owned value can make a successful reviewer look like a failed supervised process.

If the reviewer needs a diff, generate it before invocation rather than granting a general shell. Add only explicitly needed read-only tools. Never use `--dangerously-skip-permissions` for a release gate.

Require structured output containing at least:

- `decision`: `PASS` or `BLOCKED`;
- candidate and manifest hashes reviewed;
- blocker findings with file/line evidence;
- verification gaps;
- a concise rationale.

Store the complete Claude result in the approved private evidence area. Do not publish private review inputs or outputs.

If the user explicitly authorizes a quota fallback, accept fallback eligibility only from a CreateNew invocation receipt whose route is the requested model and effort and whose terminal classifier is `CLAUDE_QUOTA_LIMIT`, plus the wrapper's surfaced quota error or equivalent exact provider evidence. Authentication, overload, schema, permission, launcher, timeout, and other failures remain `BLOCKED`; never reinterpret them as quota exhaustion or silently change providers.

## Enforce the gate

Treat the result as `BLOCKED` when any of these occurs:

- timeout, authentication failure, overload, fallback, or non-zero exit;
- invalid or incomplete structured output;
- hashes do not exactly match the frozen candidate;
- any blocker or unverified required invariant remains;
- Claude modified artifacts or relied on live mutation;
- the candidate changed after review.

Proceed only on a fresh, explicit `PASS` bound to the exact frozen hashes. Independently inspect the primary artifacts and rerun the repository's shared verification; Claude's verdict is evidence, not authority.

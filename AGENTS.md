# Agent guidance

This repository is the canonical writable source for the skills listed as `toolkit-owned` in
`catalog/skills.json`. Installed skill directories, plugin caches, release archives, and downstream
mirrors are projections, never alternate source trees.

## Engineering-policy compatibility

- Outcome, user authority, effect-local safety, proportional evidence, and finite execution take
  precedence over a broader repository, adapter, or skill rule. A lower rule does not win merely
  because it is older, more local, or stricter.
- Treat only the conflicting clause as inactive. Preserve compatible project facts and narrower
  guards that name their trigger, direct-path non-trigger, owner, protected effect, evidence, finite
  budget when they create a loop or fan-out, stop condition, and retirement condition.
- No numeric budget means no activation of a specification loop, delivery loop, review wave,
  same-cause retry loop, or worker fan-out. Budget exhaustion stops that mechanism; it never grants
  another reviewer, worker, successor name, or larger matrix.

## Smallest reliable workflow

- Select a focused skill from the task's actual outcome. Do not auto-run a global lifecycle.
- Specify first only when behavior, authority, ownership, compatibility, or acceptance is materially
  unresolved.
- Use the lowest verification altitude that can falsify the changed claim.
- When a seam has multiple independently failing links or costly high-altitude feedback, prove the
  contract-relevant link failures first, then composition, then only the native or lifecycle claim
  lower tiers cannot represent. Keep one simple seam on the direct path.
- A new finding is not new scope. Classify it against the authorized deliverable and claim before
  acting; use `engineering-specification` for a material scope-change checkpoint.
- Classify material findings at their first affected effect boundary by **consequence × estimated
  frequency**, reversibility/containment, and confidence. Keep assurance risk-local: fail closed before
  high-consequence effects, but use bounded fail-open for supported low-consequence, low-frequency,
  reversible residuals that cannot falsify the authorized claim.
- Novel OS/provider/runtime primitives get the smallest no-live-effect constructibility probe before
  a broad protocol or formal review matrix is frozen.
- Any orchestration/review loop declares numeric pass, same-cause retry, and full-review wave limits.
  Never launch an unchanged third same-cause attempt. Pin the toolkit version/commit for long tasks;
  silent policy mixing is prohibited.
- Preserve unrelated and dirty work. Do not reset, clean, rebase, overwrite, publish, or perform a
  live effect without the applicable authority.
- Use `baton-fanout-skill` before any subagent or CLI compatibility worker when Baton is installed;
  otherwise work directly. Delegation does not expand scope.
- After Baton selects delegation, reserve Luna/max for stable bounded code generation or
  low-judgment scouts with cheap falsifiers; never use Luna for architecture, security, authority,
  independent review, or release judgment.
- PMO stance means the main agent owns scope, integration, verification, and the final claim. It
  does not activate delegation, a WAL, a formal gate, or a model/provider change. Host-specific
  routing applies only when selected by the owner; the optional CK / Hermes adapter lives in
  `skills/engineering-wal/references/canon-orchestration.md` and is not a Codex default.
- Keep final synthesis, shared verification, and publication judgment with the main agent.

## Canonical improvement path

Every owned skill carries `TOOLKIT-CONTRIBUTION-PROTOCOL:v1`. When a material improvement,
conflict, missing safeguard, or retirement candidate is found, do not patch an installed copy.
Prepare public-safe evidence, an exact canonical diff, and a discriminating eval. Open a draft PR
only when publication is requested and GitHub writes are authorized. An authorized local
commit/install may close with Git history and a concise change/evidence record; it needs neither a
separate PR packet nor a publication-permission question.

External dependency behavior changes go to their actual upstream. A toolkit PR may update a pin,
integration boundary, conflict rule, or retirement state. Never create two writable canonical
owners.

## Public and release boundaries

- Keep source manifests allow-listed. Never import caches, runtime state, logs, receipts, private
  evidence, machine-specific paths, or live plugin directories.
- Public prose must explain behavior and verified limits without private milestone shorthand.
- A passing validator is necessary, not sufficient. Bind release claims to exact candidate bytes,
  executed tests, independent review, and remote readback.
- Do not claim OpenAI endorsement, official Plugin Directory publication, deployment, or provider
  execution without the corresponding external evidence.

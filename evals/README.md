# Behavior evaluation

`cases/acceptance.json` is the frozen 0.1.0 case corpus. Static validation proves only that the
catalog has positive and negative coverage. It does **not** prove that a host selected the expected
skill or followed its authority boundary. The same static-versus-host boundary applies to every
supplemental corpus; source tests are not fresh-task behavior evidence.

`cases/incremental-release-progression.json` is a supplemental maintenance corpus. It distinguishes
affected-slice evidence reuse from unsafe reuse across executable, review-intake, installed-runtime,
and publication seams without changing the frozen 0.1.0 case count. It also preserves the direct
path for an ordinary small change.

`cases/canon-orchestration.json` is a supplemental static-contract corpus. It records expected
commitment-floor, owner-classification, shadow-reopen, core/host-seam/release aggregation, loop-budget,
and direct-path behavior without changing the frozen 0.1.0 case count. Its `evidenceStatus` remains
`NOT_RUN` until fresh isolated agent executions record observed selection, prohibited effects, output,
and receipt or transcript evidence; source tests do not upgrade that status.

The mechanism-necessity cases observe whether output asks `Do we really need this to make things
happen?` and `Is there a simpler and more direct way?`, separates outcome from proxy, compares
simpler alternatives, and preserves the direct path. They cannot prove a model's private reasoning;
fresh-task behavior evidence and independent source review remain separate claims.
`engineering-specification` is the detailed canonical owner; the eval corpus observes selection and
output behavior without copying the design procedure into every case.

For a release evaluation:

1. Bind the exact plugin source commit, tree, plugin version, catalog hash, case-corpus hash, host
   version, task identity, and reviewer route.
2. Run each prompt in a fresh or demonstrably isolated context with no hidden activation hint.
3. Record selected and rejected skills, observable behavior, prohibited effects, raw evidence
   pointer or digest, and `PASS`, `FAIL`, or `NOT_RUN` for every case.
4. Treat `NOT_RUN` as an open gap. A static description match is not a behavior pass.
5. Run authority-bearing cases such as `PR-02` only when the evaluation task separately authorizes
   that effect. Otherwise record `NOT_RUN`; never simulate the write and call it a pass.
6. Validate local shape against `schemas/eval-result.schema.json`, then run
   `scripts.validate_toolkit.validate_behavior_result(root, result)` for exact Git-clean candidate
   identity, including rejection of non-ignored untracked public bytes, corpus membership, expected
   selections, PASS evidence, prohibited-effect, and summary closure. Non-Git archive evaluation is
   unsupported by schema version 1 and fails closed. Keep raw private transcripts out of the public
   repository; publish a redacted,
   hash-bound result when appropriate.

The main agent owns synthesis. A model reporting that it used a skill is useful execution evidence,
not provider-signed attestation.

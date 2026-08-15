# Behavior evaluation

`cases/acceptance.json` is the frozen 0.1.0 case corpus. Static validation proves only that the
catalog has positive and negative coverage. It does **not** prove that a host selected the expected
skill or followed its authority boundary.

For a release evaluation:

1. Bind the exact plugin source commit, tree, plugin version, catalog hash, case-corpus hash, host
   version, task identity, and reviewer route.
2. Run each prompt in a fresh or demonstrably isolated context with no hidden activation hint.
3. Record selected and rejected skills, observable behavior, prohibited effects, raw evidence
   pointer or digest, and `PASS`, `FAIL`, or `NOT_RUN` for every case.
4. Treat `NOT_RUN` as an open gap. A static description match is not a behavior pass.
5. Run authority-bearing cases such as `PR-02` only when the evaluation task separately authorizes
   that effect. Otherwise record `NOT_RUN`; never simulate the write and call it a pass.
6. Validate the result against `schemas/eval-result.schema.json`. Keep raw private transcripts out
   of the public repository; publish a redacted, hash-bound result when appropriate.

The main agent owns synthesis. A model reporting that it used a skill is useful execution evidence,
not provider-signed attestation.

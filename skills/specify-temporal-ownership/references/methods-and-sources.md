# Methods, source basis, and proof boundaries

Use this reference to select a method, not to assemble a mandatory methodology chain.

## Smallest useful method stack

1. State the temporal ownership property and operation history.
2. Audit every destructive sink and caller across the final-check-to-mutation interval.
3. Falsify the implementation at that exact seam.

Escalate only when an additional method answers an unresolved decision question.

| Method | Useful for | Does not prove by itself |
|---|---|---|
| Linearizability | Legal operation histories, real-time order, abstract effect, linearization point | Liveness, authorization policy, caller coverage, or implementation conformance |
| PlusCal/TLA+ | Bounded state/interleaving exploration, safety/liveness, crash/retry/transfer | Python/Rust/C#/OS semantics or unbounded implementation correctness |
| P | Communicating state machines, monitors, message/failure schedules | That production code is the model unless a conformance link exists |
| CHESS/Coyote/Loom | Reproducible schedules for supported controlled primitives | External processes, filesystems, providers, unsupported APIs, or every schedule |
| Deterministic simulation | Long seeded histories and injected failures in a runtime designed for it | Behavior of omitted or uncontrolled production components |
| Exact failpoint/barrier | One named final-check-to-mutation counterexample | All sibling callers or variants |
| NIST SSDF/IR 8397 | Risk/design records, independent challenge, similar-weakness search, evidence portfolio | Atomicity, linearizability, or runtime behavior |
| STPA | Cross-system losses, unsafe control actions, feedback and operator timing | Code-level atomicity or implementation proof |
| SACM/assurance case | Claims, evidence, assumptions, and defeaters at a consequential gate | Truth of evidence or discovery of races |

## Primary and authoritative sources

- Herlihy and Wing, [Linearizability: A Correctness Condition for Concurrent
  Objects](https://www.cs.cmu.edu/~wing/publications/HerlihyWing90.pdf).
- Wing and Gong, [Testing and Verifying Concurrent
  Objects](https://doi.org/10.1006/jpdc.1993.1015).
- MITRE, [CWE-367: Time-of-check Time-of-use Race
  Condition](https://cwe.mitre.org/data/definitions/367.html).
- SEI CERT, [FIO45-C: Avoid TOCTOU race conditions while accessing
  files](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/rules/input-output-fio/fio45-c/).
- Rust standard library, [atomic compare-exchange and the ABA
  problem](https://doc.rust-lang.org/std/sync/atomic/struct.Atomic.html).
- Oracle Java, [atomic variables and stamped
  references](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/concurrent/atomic/package-summary.html).
- Leslie Lamport, [PlusCal tutorial](https://lamport.azurewebsites.net/tla/tutorial/home.html) and
  [high-level view of TLA+](https://lamport.azurewebsites.net/tla/high-level-view.html).
- Microsoft Research, [P language documentation](https://p-org.github.io/P/manualoutline/).
- Musuvathi et al., [CHESS systematic concurrency
  testing](https://www.usenix.org/event/osdi08/tech/full_papers/musuvathi/musuvathi_html/index.html).
- Microsoft Research, [Coyote controlled concurrency
  testing](https://microsoft.github.io/coyote/get-started/using-coyote/).
- FoundationDB, [Simulation and Testing](https://apple.github.io/foundationdb/testing.html),
  [Client Testing](https://apple.github.io/foundationdb/client-testing.html), and
  [code probes](https://apple.github.io/foundationdb/internal-dev-tools.html).
- Tokio, [Loom](https://github.com/tokio-rs/loom).
- TiKV, [`fail` failpoints](https://tikv.github.io/doc/fail/index.html).
- NIST, [Secure Software Development Framework 1.1](https://csrc.nist.gov/pubs/sp/800/218/final)
  and [IR 8397 developer verification guidance](https://csrc.nist.gov/pubs/ir/8397/final).
- Linux man-pages, [`pidfd_send_signal(2)`](https://man7.org/linux/man-pages/man2/pidfd_send_signal.2.html).
- Microsoft Learn, [Process Handles and
  Identifiers](https://learn.microsoft.com/en-us/windows/win32/procthread/process-handles-and-identifiers).
- SAE, [J3307 STPA standard](https://saemobilus.sae.org/standards/j3307_202503-system-theoretic-process-analysis-stpa-standard-industries).
- OMG, [Structured Assurance Case Metamodel 2.3](https://www.omg.org/spec/SACM/About-SACM).

## Selection rules

- One local primitive and one known race: sink/caller inventory plus an exact seam test.
- Multiple actors, transfer, crash/retry, rollback, or liveness: add a bounded PlusCal/TLA+ model.
- Existing async state-machine architecture: consider P and preserve trace/code conformance.
- .NET supported async primitives: Coyote can broaden schedules.
- Rust supported in-process primitives: Loom can broaden schedules.
- OS process, filesystem, database, plugin/config, or provider boundary: retain a real seam or
  lifecycle test even when a model or simulator is green.
- Human/operator and cross-system feedback hazards: consider STPA.
- Consequential final evidence argument: consider an assurance case after underlying evidence exists.

Always document bounds, unsupported nondeterminism, model-to-code mapping, and the evidence class's
non-claims.

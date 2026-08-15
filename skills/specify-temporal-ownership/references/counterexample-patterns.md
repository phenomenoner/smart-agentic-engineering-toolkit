# Temporal ownership counterexample patterns

Select only patterns relevant to the declared failure model. For a known escape, place a
deterministic barrier immediately after the final authorizing check and before the destructive call.

## Final-check TOCTOU

```text
Actor A: observe expected identity at C_final
Actor A: pause
Actor B: replace or transfer the resource
Actor A: perform M using a fresh path/PID/value lookup
```

Required result: the predicate and mutation are one atomic action, the mutation uses the already
validated stable object, or A contains without mutating.

## Equal-value ABA

```text
A1: value H, generation g1, owner o1
B:  value J, generation g2, owner o2
A2: value H, generation g3, owner o3
stale actor compares only H and attempts mutation
```

Required result: visible equality is insufficient; compare a non-reused stamp/generation or retain
an object/lock that spans authorization and mutation.

## Observation unavailable

```text
probe identity -> permission error, timeout, unsupported platform, parse error, or transient I/O
caller coerces exception/None to false, absent, dead, or replacement
caller deletes, signals, overwrites, retries, or rolls back
```

Required result: return a distinct unavailable/unknown disposition and do nothing destructive.

## PID reuse

```text
record numeric PID for process P1
P1 exits; operating system reuses PID for P2
caller reopens or signals by numeric PID
```

Required result: retain and use the same OS process object (for example, pidfd or Windows process
handle) through authorization, signal, wait, and terminal readback. If unavailable, contain.

## Replacement cleanup

```text
old generation reads a shared discovery/control path
new generation publishes its own path or endpoint
old generation rereads and then unlinks by pathname
replacement occurs after the last read but before unlink
```

Repeated reads only move the race. Required result: compare-and-delete/rename under an authority all
writers share, generation-specific immutable paths plus an atomic pointer, or preserve the path.

## Value-equal rollback

```text
installer captures previous state
installer writes desired state
external actor changes state and later restores equal visible bytes
installer sees desired-equal state and restores stale previous state
```

Required result: rollback is compare-bound to a provider revision/generation/transaction. If the
external interface offers no CAS/token/lock, do not perform destructive automatic rollback; retain
forward state and report reconciliation required.

## Lease or fence loss

```text
worker validates owner/generation
worker pauses or calls an external provider
lease expires or ownership transfers
worker commits, cancels, or releases shared state
```

Required result: the commit includes the expected lease/fence in the same transaction, or it fails
without mutation. For an indeterminate provider effect, reconcile a durable receipt before retrying.

## Partial failure and late success

```text
mutation starts
caller times out or loses transport
effect may have committed
cleanup/rollback assumes failure and repeats or reverses the effect
```

Required result: represent `INDETERMINATE`, reconcile by idempotency key/receipt/current revision,
and distinguish compensation from proof that the original effect did not happen.

## Sibling caller escape

```text
primary CLI path uses safe shared helper
timeout, interrupt, worker reap, upgrade, or exception cleanup calls a raw sink directly
```

Required result: sink-first inventory reaches every entrypoint and platform adapter; every caller
either uses the common atomic mechanism or has its own explicit containment contract and test.

## Wrong hook placement

- Hook before an earlier check: the implementation may revalidate and pass safely; the named final
  seam was not exercised.
- Hook after mutation: tests detection or recovery, not prevention.
- Timing sleeps: may increase probability but are not a deterministic counterexample.

The useful hook is after `C_final`, before `M`, and the receipt must show the conflicting actor action,
the branch taken, and whether the destructive sink ran.

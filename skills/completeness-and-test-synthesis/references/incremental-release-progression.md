# Incremental release evidence progression

Use this reference only for an explicit release, migration, cutover, or repeated cross-stage
readiness decision. An ordinary bounded change does not activate it.

This is a dependency-based decision rule, not a new release orchestrator. It needs no database,
daemon, ledger, durable state machine, or second authority owner. Git object identity, artifact
hashes, the existing review envelope, and direct readback are sufficient inputs.

## Start from the minimum invariant

The release claim should advance without either of these errors:

1. promoting evidence from one layer into proof of a later layer; or
2. discarding still-valid evidence merely because an unrelated file or receipt changed.

For each edit, identify the exact changed Git objects or artifact members, the first executable seam
they can affect, and the evidence cells that depend on that seam. Reopen those affected cells and
their downstream claims. Reuse all other evidence only while its subject bytes, behavioral
contract, relevant dependencies, toolchain, environment, and required observation remain materially
unchanged.

## Keep the gates distinct

| Gate | Subject bound by the evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Source correctness | Exact source/test objects and acceptance contract | The selected checks support the source behavior | A built artifact contains those bytes |
| Artifact identity | One immutable package, archive, binary, or plugin tree | The candidate artifact has the recorded members and hashes | The artifact behaves correctly or was installed |
| Formal review | One hash-bound candidate, evidence index, plan, and coverage set | The reviewed candidate received the recorded independent verdict | A host picked up or executed it |
| Installed instance | The exact installed artifact, configuration, launcher, and selected dependency set | The intended instance is present and selected for pickup | A current host has loaded it |
| Live host | A fresh consumer/task, native discovery or call, and the actual representative drill | The installed instance works across the claimed host seam | The same bytes were externally published |
| External publication | The remote commit/tag, release metadata, and downloadable assets | Provider-visible bytes match the final release claim | Those bytes are the installed or executed instance unless compared |

A green row cannot substitute for another row. In particular, configuration, a catalog, a receipt,
or process health is not fresh-host behavior; a successful upload is not asset identity until the
asset is downloaded and read back.

## Progress in one direction

1. Stabilize executable source, behavioral contracts, and focused checks. Record the exact source
   and test objects supporting each correctness claim.
2. Build or select one immutable candidate artifact and verify its identity. Do not let a mutable
   build path stand in for the preserved instance.
3. Once executable bytes and reviewed contracts are stable, bind and complete the required formal
   review once. A review repair that changes executable semantics starts a new hash-bound wave.
4. After actual formal `PASS`, perform one final exact install, the one required restart or host
   transition, a fresh-task native check, and the actual representative drill. Keep formal review
   and installed-runtime pickup as separate gates instead of alternating them.
5. Publish the final bytes, then download and read back the remote commit, tag, metadata, and assets
   needed by the claim.

Settle release wording and other non-executable package members before step 4 when practical. If an
unavoidable non-executable member changes later, re-establish final artifact and installed-instance
identity as required, but do not automatically repeat restart/native/drill evidence whose executable
seam is proven unchanged.

An installed-instance or live-host failure may reveal an upstream product defect. Reopen upstream
correctness or review cells only when the failure maps to their subject; do not interleave every
pickup retry with another whole formal review.

## Invalidate by bytes and seams

Use the smallest matching rule. If more than one applies, take the union of their affected cells.

| Change class | Required reopen | Evidence normally retained |
| --- | --- | --- |
| Documentation-only release wording | Affected documentation, public-hygiene, and review cells; artifact/publication identity only if final asset bytes changed | Source behavior, executable checks, installed pickup, and live-host drill |
| WAL, receipt, report formatting, or evidence pointer | The affected evidence/readback cell; artifact identity too if the changed member ships in the asset | Candidate behavior and runtime evidence when the file is not a runtime input |
| Review envelope or locator | Intake binding and the review cells whose candidate access was not proven | Source and candidate-behavior checks; do not rerun them merely to repair ceremony |
| Acceptance or test-contract change | The source/review cells whose expected behavior changed | Runtime observations unrelated to that contract only when their meaning is unchanged |
| Build recipe or package membership | Artifact identity and every installed/publication claim that depends on it | Source behavior evidence when inputs and semantics are unchanged |
| Launcher, plugin manifest, bundled skill, or runtime dependency | Affected source/artifact review, installed-instance identity, fresh-task native pickup, and actual drill | Unrelated source cells only |
| MCP or another host-discovery behavior change | Installed instance and live-host native/drill cells, plus upstream cells for the changed implementation | Unrelated documentation and source cells |
| Executable semantic change | Affected correctness cells, artifact identity, prior formal review, installed instance, and live host | Only cells proven independent of the changed semantics |
| Publication metadata or remote asset change | Publication and download/readback cells, plus any public-claim review cell | Installed/live evidence if exact executable equivalence remains proven |

Do not use filename extensions alone. A documentation file embedded into a generated prompt, a
skill instruction, a launcher template, or a dependency manifest is an executable or behavioral
input for that seam.

## Rebind formal review without replaying everything

A formal verdict authorizes only its exact review wave. After any candidate-byte change, bind a new
candidate and synthesis; never copy the old whole-candidate `PASS` to the new hash. The new wave may
reuse an unchanged cell's supporting evidence and disposition when the changed-object map proves
that the cell's contract, source, dependencies, required tier, and reviewer access are unaffected.
Re-review the affected cells and recompute synthesis over the complete new wave.

An executable semantic change invalidates every prior review cell that depends on those semantics.
A documentation-only change may reuse runtime and implementation review evidence while reopening
the public-claim cells. A corrected review envelope or locator must itself be revalidated; if the
old binding did not prove that the reviewer saw the intended bytes, the formal gate is `INCOMPLETE`
until that affected review evidence is reacquired.

## Separate gate defects from product defects

Classify a failure before assigning a candidate verdict:

- A product defect is supported evidence that candidate source, artifact, installation, or runtime
  behavior violates its contract. It can block the candidate and invalidate dependent evidence.
- An intake, binding, locator, review-tool, or evidence-presentation defect means the gate cannot
  yet support its verdict. It makes that gate `INCOMPLETE` or `UNVERIFIED`; it is not a product
  blocker unless the same evidence independently demonstrates a candidate defect.

Repair and revalidate the defective gate at its own seam. Do not rerun candidate behavior to make a
malformed envelope look green, and do not hide a real candidate defect by calling it tooling.

## Fail closed on uncertain equivalence

When executable influence, artifact membership, dependency resolution, installed selection, or
reviewer access cannot be established, fail closed: classify the uncertain seam as affected and
reacquire the corresponding evidence. A high-risk release cannot reuse evidence on an asserted but
unproved equivalence. If the final published asset cannot be shown equivalent to the installed and
drilled executable instance, narrow the claim or withhold release readiness.

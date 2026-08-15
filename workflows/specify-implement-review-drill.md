# Specify, implement, review, drill

This is a navigation guide, not an installable catch-all skill.

1. **Frame and specify when needed.** State the outcome and minimum invariant. When a material
   mechanism is proposed, ask `Do we really need this to make things happen?` and `Is there a
   simpler and more direct way?`; run the conditional necessity/complexity gate owned by
   `engineering-specification` before freezing the contract or RED cases. Compare deletion,
   manual, embedded/ephemeral, platform-primitive, and retained-mechanism paths with their
   complexity, authority, recovery, and failure-state cost. Skip this phase when the contract and
   mechanism are already sufficient, and bind later acceptance to observable behavior rather than
   a mechanism proxy.
2. **Implement.** Make the smallest coherent authorized slice and run the lowest check that can
   falsify its claim.
3. **Review.** Use a lightweight findings-first review for ordinary changes. Use a formal independent
   gate only for explicit final, release, migration, pre-cutover, mandated, or recurring
   sibling-blocker decisions.
4. **Drill or close evidence.** Convert a stable incident to a regression, or use completeness
   synthesis to choose the missing seam/lifecycle check. Re-enter implementation only with repair
   authority.
5. **Stop honestly.** Finish when the requested claim is supported, or preserve the exact blocker,
   evidence, and next safe action in a WAL when continuity warrants it.

Delegation is optional and must pass Baton when available. Canvas, CodeGraph, AAR, long-run
supervision, and provider/model adapters augment specific task classes without becoming required
proof or authority.

# Specify, implement, review, drill

This is a navigation guide, not an installable catch-all skill.

1. **Specify when needed.** Resolve material behavior, ownership, compatibility, failure semantics,
   and falsifiable acceptance. Skip this phase when the contract is already sufficient.
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

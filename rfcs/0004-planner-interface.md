# RFC 0004: Planner interface

- Status: Draft
- Type: Exploratory (likely product-only)
- Created: 2026-07-24

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar. This RFC exists to test
> whether *any* of a planner is standardizable; its most likely outcome is "product-only."

## Summary

Examine whether the interface by which an agent selects and invokes Judgment Packs — a "planner" —
has any portable, standardizable surface, or whether it is entirely product behavior.

## Problem

Integrators keep asking "how does an agent know which pack to run?" That question hides a recursion:
selecting a pack is itself a judgment. A component that decides which judgment to apply is either
governed by its own pack or is bespoke product logic. Either way, most of a planner is orchestration
— which the [non-goals](../docs/non-goals.md) place outside the specification.

## Evidence

Across experiments, "pick the right pack" is consistently entangled with product context (user,
tenant, workflow, cost, latency), none of which is portable. What *is* sometimes shared is a thin
selection query: "which packs govern this decision context?"

## Specification (sketch)

The only candidate portable surface is a **selection query interface**: given a decision context,
return candidate pack references (from [RFC 0005](0005-pack-discovery.md)) ranked by declared
applicability — with ranking, tie-breaking, and side effects left to the product. Everything beyond
returning candidates is product behavior.

## Alternatives

- **No change / product-only** — the most likely correct outcome. The planner is a product; the
  specification stays out of orchestration.
- **Standardize a selection interface only** — the narrow surface above, if two products want to
  interoperate on discovery.
- **Standardize the full planner** — rejected; it is orchestration and business logic.

## Compatibility

No effect on the core document. Any accepted surface would be an optional profile layered on
discovery.

## Security and privacy

A selector influences which judgment is applied — a high-value target. Authorization for *which*
pack may run must remain with the product, never inferred from applicability.

## Conformance

If a selection interface is standardized: positive — a context returns the packs whose applicability
matches; negative — a context returns a pack whose applicability excludes it.

## Implementation

Two discovery services should return the same candidate set for a shared context and pack corpus.

## Unresolved questions

- Is even the selection query portable, or is "decision context" irreducibly product-specific?
- Does standardizing selection encourage treating applicability as authorization? How is that
  prevented?
- Should this RFC be closed as `Rejected` with a rationale rather than accepted — i.e. is the honest
  answer "this is product"?

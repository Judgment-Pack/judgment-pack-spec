# RFC 0004: Planner interface

- Status: Rejected
- Type: Exploratory (likely product-only)
- Created: 2026-07-24
- Rejected: 2026-09-21

> **Disposition record.** This RFC is rejected by the single maintainer under the interim review
> regime ([RFC 0009](0009-interim-review-regime.md)). The review of this disposition, with a
> written disposition for every finding, is recorded on the pull request that makes it and under
> [`rfcs/reviews/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/rfcs/reviews).
> *Rejected* is the outcome this RFC named as most likely on the day it
> was opened, and it answers the RFC's own third unresolved question: a planner is product, and
> the specification standardizes no part of one — the narrow selection query included.
>
> What the rejection rests on, with its limits:
>
> - **Nobody has asked for the one candidate surface.** The sketch offered a selection query "if
>   two products want to interoperate on discovery". No such pair exists. The discovery index the
>   query would read ([RFC 0005](0005-pack-discovery.md)) and the manifest that index would
>   reference ([RFC 0001](0001-pack-manifest.md)) are both drafts that nothing emits, so a
>   selection query has nothing to return. This is absence of demand in a project that has drawn
>   no outside comment on any RFC; it is weak evidence, and it is the evidence there is.
> - **The one implementation took the opposite position on purpose.** The reference runtime's
>   [ADR-0012](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0012-jpack-project-convention.md)
>   keeps selection with the application — its configuration "does not choose a pack for a
>   request, and this runtime never will" — and gives this RFC's reason: applicability is not
>   authorization. Its
>   [ADR-0007](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0007-experimental-evaluator.md)
>   scopes planner selection out of the evaluator. That is one runtime, by this project's
>   maintainer: a recorded position, not independent evidence.
> - **Declining removes an invitation the RFC itself worried about.** Its second unresolved
>   question asked whether standardizing selection would encourage reading applicability as
>   authorization. With no standardized selection surface there is nothing to misread. The
>   statement under *Security and privacy* — authorization for which pack may run stays with the
>   product — does not depend on this RFC's status: [RFC 0005](0005-pack-discovery.md) says the
>   same of selection metadata, and the [non-goals](../docs/non-goals.md) already exclude
>   orchestration.
>
> What the rejection does not decide. The first unresolved question — whether a selection query
> could be portable at all — stays unanswered, because nothing was built to test it. RFC 0005's
> question about how discovery relates to a selection interface now refers to an interface this
> project declines to standardize; restating it is RFC 0005's to do when it is next amended.
> [RFC 0006](0006-evaluator-conformance.md)'s note on a selection probe is advice to a product
> that builds one and is unaffected. Two products that do want to interoperate on selection
> would bring a new RFC with that evidence; this record would be its prior art, not its obstacle.
>
> This record replaces the banner that marked the RFC an open proposal, which said it existed "to
> test whether *any* of a planner is standardizable; its most likely outcome is 'product-only.'"
> Nothing here was ever part of the specification; see [RFC 0000](0000-rfc-process.md) for the
> process. Every section below is the proposal as it stood, retained unedited as the record.

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

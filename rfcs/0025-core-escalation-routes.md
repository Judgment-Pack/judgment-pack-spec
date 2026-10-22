# RFC 0025: Core escalation routes

- Status: Accepted
- Type: Standards track, draft maturity
- Decision: Issue #219, maintainer acceptance and addendum of 2026-10-22

## Summary

Core gains ordered conditional routes beside its single escalation target. This record covers
only the Core portion of the accepted decision. Acceptance does not establish release readiness.

## Problem

One logical target cannot express conditional selection and explicit fan-out portably. A review
outcome must remain distinct from a handoff request.

## Evidence

Issue #219 describes missing evidence routed to a research role and other reasons routed to both
a compliance queue and a legal role. All fixtures here are synthetic. No runtime implementation
agreement is claimed by this specification change.

## Specification

Core §§6.7, 8.1 and 8.3 govern. An escalation declares exactly one of `target` or `routes`.
Routes contain 1–8 closed `{target, triggers?}` objects. Each target retains the existing kind
and non-empty name; optional triggers are a non-empty set contained in the escalation triggers.
Once a generated reason or direct exception requests escalation, select every route with no
filter or a filter intersecting the complete retained reasons. Emit one target per selected route
in `handoff.routes`, preserving declaration order and duplicate targets. If none is selected,
the state is `none` and `triggeredBy` is absent. Reasons, kind and outcome are never rewritten.
The single-target disposition remains byte-identical.

The implementation brief selects `handoff.routes` (target objects), rather than the earlier
recommendation's `requests` objects with per-route reasons. `triggeredBy` retains its existing
meaning; the full reasons remain at disposition level.

Eight is the schema ceiling in this change. The maintainer's addendum assigns that ceiling to
`base` and delegates `extended` and `profile-unsupported` to #232; no profile mechanism is
introduced here. That follow-up must reconcile the ceiling before admitting larger packs.

## Alternatives

Keep one external routing queue; use target alternatives; delegate routing to a profile or to a
product-only workflow. The accepted design instead makes conditional fan-out explicit in Core.

## Compatibility

Existing target-only documents and dispositions are unchanged. Old readers may reject routes;
parsing an old document does not establish compatibility with new results. These additions are
unreleased work for the next Core revision, not permission to change a released corpus or pins.
New evaluation rows are staged outside the frozen `0.2.0-draft` manifest. Writers must retain
single-target form for old readers, or wait for a reader supporting the new revision. No automatic
migration, profile negotiation, or version bump is introduced. Changing routing changes the pack
bytes and therefore its identity wherever identity is byte-derived; existing pins must not adopt it.

## Security and privacy

Targets are display names, never addresses or authorization. Eight bounds request amplification.
Repeated targets intentionally remain separate routes. Delivery, retries, binding authorization,
receipts, and data minimization remain host responsibilities; a request proves no delivery.

## Conformance

Hand-written structural fixtures cover valid routes, eight and nine entries, mutual exclusion,
subset membership, empty filters, missing targets and unknown route members. Staged evaluation
rows cover one match, fan-out, unconditional selection, no match, no request, duplicate targets,
and unchanged legacy bytes. Schema and expectation mutations must fail local checks.

## Implementation

A Python reader can filter the declared list by set intersection. An independent TypeScript
reader can iterate it, checking reason membership before appending each target. Both preserve
order and multiplicity without sorting targets. This repository owns neither Core evaluator;
its tests validate fixtures and routing invariants, not independent execution agreement.

## Unresolved questions

Profile negotiation and extended bounds are #232. Dialect outputs are #169; delivery receipts
belong to Runner. Sequential approvals, quorum and ownership remain workflow questions.
Repository-required different-vendor review and maintainer dispositions remain release gates;
this record does not claim that such review has occurred.

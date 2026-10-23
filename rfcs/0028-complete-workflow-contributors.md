# RFC 0028: Complete workflow contributor attribution

- Status: Draft
- Type: Standards track (amendment to Draft RFC 0020)
- Created: 2026-10-23
- Target: Spec `0.4.0`, unpublished
- Issue: [#251](https://github.com/Judgment-Pack/judgment-pack-spec/issues/251)

## Summary

Preserve every actual contributing rule or forcing exception outside Core's closed disposition.
Output version 2 records a typed collection; summary version 2 counts record memberships rather
than assigning one representative credit. Execution version 3 selects the complete-attribution
model. Signed drift retains those distinctions. This proposal does not change Core resolution.
The exact proposed contract is [RFC 0020 §5](0020-workflow.md#5-output-records-and-closed-sets)
and [§9](0020-workflow.md#9-the-workflow-verifier), mirrored in the workflow companion.

## Problem

The #228 amendment chose the least contributor id for a singular `contributingRule`. Two true,
unsuppressed rules producing the same outcome agree under Core; both contributed. Reporting only
one drops causal evidence and falsely suggests the contributor counts partition the outcome
records. A forcing exception is also a different kind of contributor from a normal rule, even
when both have the same pack-local id.

## Evidence

The existing `conformance/workflow/` records are hand-authored contract fixtures, not executor
recordings. Their version-1 envelopes and summaries carry representative attribution and remain
unchanged. The separately authored experimental `tools/workflow_reader.py` targets RFC 0024's
workflow-version-2 admission-proof proposal and output-version-1 envelopes without attribution;
it does not implement #228's bulk fields. Its retained recordings, provenance and historical pins
are not upgraded by this proposal. No full workflow consumer upgrade is claimed.

The new `conformance/workflow-v2/` fixtures are also hand-authored. They include opposite pack
orders, two compatible rules, two compatible forcing exceptions, typed same-id namespaces,
suppressed and false rules, bypassed normal rules, fallback and non-outcome cases. An explicitly
hypothetical failed outcome-value resolution records no contributor credit; it is not an executed
Core `0.3.0` value feature. A failed evaluation has no output envelope. Runtime issue #305 owns
retaining actual evaluator contributor evidence in that repository; this RFC does not implement it.

## Specification

Output version 2 conditionally carries `contributors: [{kind, id}]`. Kind is `rule` or
`forcing-exception`. Preserve every actual member, sort by kind then exact Core id, reject duplicates
and empty/null collections, and keep one homogeneous kind per output. False, suppressed, skipped,
escalating and discarded candidates receive no credit. Fallback and non-outcomes omit the member;
failed evaluations have no outputs. The 4096-entry ceiling is subordinate to the 65536-byte output
envelope ceiling; exceeding either refuses the input or prevents output admission, never truncates
or elects a representative.

Summary version 2 keeps `byRule[outcome].contributors` as exactly two kind maps: `rule` and
`forcing-exception`. Every member increments once per output. Fallback counts records separately.
One record with two contributors is one outcome count and two contributor memberships. For N
outcome records, F fallback records and M memberships, each individual count is at most N−F,
and N−F ≤ M ≤ 4096×(N−F). Record and outcome counts retain their own invariants.

Execution version 3 requires model-2 outputs and summaries throughout, including empty stages.
Execution version 1 preserves historical semantics; version 2 is already reserved by the separate
Draft RFC 0024 admission-proof proposal. Choosing 3 avoids conflating or adopting that proposal.
Workflow document version 1 and selection version 1 retain their existing forms. Drift version 2
subtracts the typed per-identity membership counts; attribution-only changes need not appear in
its disposition-only record changes. Mixed-model comparison is `version-unread`.

The new draft resource is `schema/workflow-contributors-2.schema.json`, with `$id`
`https://judgmentpack.org/schema/0.4.0/workflow-contributors-2.schema.json`. Its name describes the
attribution model, not workflow document version 2. The historical schema stays unchanged.

## Alternatives

No change preserves the misleading single-credit partition. First/last/least-id representatives
all discard valid contributions. A complete collection as an ungoverned extension or profile
leaves consumers unable to agree on summary or drift semantics. Product-only display cannot
repair retained evidence. Rewriting the still-Draft version-1 form would be simpler but silently
relabels retained representative records and experimental consumers, so explicit versions are used.

## Compatibility

Older readers refuse new exact selectors. New readers may support historical forms separately,
labeling their attribution representative/incomplete or unavailable, never complete. A singular
representative is not automatically a singleton complete set, and its id does not identify its
namespace. No deterministic complete migration exists without sufficient original evaluation
evidence or replay. Rebuild all transitive pins after replay and preserve original bytes.

Reader, writer and semantic compatibility are intentionally broken at the new attribution model.
Core `0.3.0` schema, corpus, published artifacts and resolution remain unchanged; no release version
is bumped by this change. The target `0.4.0` is a planning identifier and not an immutable release.

## Security and privacy

Counting a duplicate or suppressed member can inflate apparent influence. Typed identities, strict
forms, bounded arrays, exact envelope pins and independent summary recomputation expose such
inconsistencies within retained evidence. A coordinated rewrite can still agree. A bulk reading
proves neither condition truth nor actual completeness, authorization or safety. Complete contributor
lists may disclose more pack structure than a representative; use only synthetic public examples.

## Conformance

The Python and JavaScript bounded accounting experiments read the same hand-authored projections
and caller-supplied admitted Core pack bytes. They check exact pack/envelope pins, identity kind,
pack membership, declared outcome association, collection ordering and counts, then independently
compute typed signed drift. They do not share an accounting helper. They are one-author,
same-vendor-assisted experiments, not independent organizational interoperability evidence, full
workflow readers, or a conformance corpus. Their result `bulk-consistency` is local experimental
output, not the workflow-verifier's `reading` event.

Mutation cases cover omissions with fixed summary/pins, duplicate/unknown ids, wrong kind/outcome,
non-outcome credit, malformed absence/empty forms, count/digest drift and mixed versions. A
coordinated omission with rebuilt pins and summary intentionally passes structural accounting;
its independently authored expected membership disagrees. This makes the limit visible instead
of claiming causal proof. Full workflow recording, both full readers and replay remain acceptance
evidence to obtain under RFC 0020 §11.

## Implementation

A Runtime can retain all final contributors while resolving and sign that evidence in its audit;
a Runner can copy it into each output envelope and independently accumulate the typed membership
counts. A second implementation can replay the pinned pack and inputs, build the same sorted set,
and check a separately implemented summary/drift reader. No consumer upgrade or release is
asserted by these plausible implementation routes.

## Unresolved questions

Public RFC comment, the governance review record and maintainer dispositions remain merge gates.
The explicitly authorized temporary same-vendor review exception while the other vendor is
unavailable does not constitute cross-vendor evidence. This Draft does not mark those gates
complete, waive the repository process, or claim a full execution recording. The future consumer
release pin that supplies complete evaluator evidence must be recorded before asserting full
workflow support; RFC 0020's old Runtime pin does not supply that evidence.

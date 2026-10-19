# Proposed RFC 0023 disposition at draft maturity

This is a reviewable disposition proposal, not a maintainer decision. RFC 0023
remains **Review**; acceptance and publication require separate recorded actions.
The promotion proposes only the immutable supplied-document surface in
[spec/policy.md](../../../spec/policy.md) and its Policy offline-reader class.

## Public process assessed 2026-10-19

Read once: [issue 211](https://github.com/Judgment-Pack/judgment-pack-spec/issues/211)
and its one comment, [PR 212](https://github.com/Judgment-Pack/judgment-pack-spec/pull/212),
its six comments, zero submitted reviews and zero inline review comments. The
issue opened 2026-10-18 at 03:01:59 UTC; PR 212 opened at 03:15:52 UTC and merged
at 17:50:10 UTC as `8a56a95d555c17640d2db4984363b779536b3c2a`. Its public
disposition merged a Draft RFC/non-normative prototype, explicitly withholding
companion adoption. The issue update at 20:55:02 UTC reports corrected candidate
work in PRs 216/217, 124 matching vectors and two Codex-assisted readers, while
explicitly keeping the RFC in Review and independent evidence outstanding.

All substantive comments in this bounded history are by the maintainer; the
remaining comment is a contribution bot. No independent technical objection,
endorsement or implementation review is recorded there. Absence of comments is
not public acceptance. RFC 0000 sets a reasonable public period according to
complexity, with no fixed minimum. This recent history contains no maintainer
disposition declaring the corrected candidate's period sufficient or waiving it
for **normative draft promotion**. That explicit decision remains required.

The existing PR 212 same-vendor readiness review and response preserve findings
F1–F6. F1's exact-byte/multiple-media-type defect was fixed; F6's typed consumer
references, original bounds and requirements deferral were addressed. F2 release
registration, F3 current authority, F4 external lifecycle and F5 private-to-
portable migration remain product-owned boundaries, not silently resolved by
this companion. Their evidence cannot be inferred from offline validation.

The [recorded temporary exception](https://github.com/Judgment-Pack/judgment-pack-spec/pull/212#issuecomment-6253085953)
waived different-vendor review for that merge without changing the general
governance rule. The maintainer's standing temporary waiver for this work must
be recorded explicitly with the promotion's exact reviewed commit and finding
dispositions. The next bounded independent review is still pending; another
Codex reviewer is same-vendor and supplies no independent implementation evidence.
No historical review record is rewritten or promoted into that evidence.

## Exact scope and unresolved-question dispositions proposed

| RFC question | Draft disposition and condition to reopen |
| --- | --- |
| 1. Selector, bounds and closed grammar | Accept exact `formatVersion: "1.0.0"`, strict independent x.y.z artifact versions, 262,144 parsed bytes, depth 32, 128-character number literals/exponent magnitude 308, 1,048,576 narrative/review/informational bytes, 4,194,304 original bytes, 16,777,216 distinct retained bytes, 16 registrations, and the declared closed field/count maxima; retained bytes and optional `jps-canon`, UTF-8 anchors, pack-only typed references and scoped total coverage. Refuse aliases/unknown members/structured requirements. No evaluator or live authority changes. A grammar/bound change requires explicit selector and compatibility review. |
| 2. Review trust, signatures and cross-workspace adoption | Defer. Interpretation bytes prove no reviewer identity or authorized sign-off. Reopen with a concrete cross-workspace export need, authentication/trust profile, exact reviewed candidate/workflow binding and adversarial verification vectors. |
| 3. RFC 0011 currency registry | Defer; do not adopt or supersede the Draft registry. Reopen with an RFC 0011 disposition and explicit distinction between offline membership and current authenticated admission. |
| 4. Provider lifecycle/freshness | Defer to owning hosts. Read support, byte identity, opaque revision or missing file cannot establish publication/withdrawal. Reopen with a real provider's demonstrated revision/lifecycle/freshness evidence and reviewed mapping/reconciliation/enforcement tests. |
| 5. Teams, quorums, roles and approval | Defer. No universal separation-of-duties rule or imported roles; honest local self-review remains a host workflow choice. Reopen with a team host contract covering quorum/workflow revision, role revocation, expiry and transactional candidate/publication binding. |
| 6. Graph/composition closure | Defer and refuse graph consumers. Reopen with an adopted owning graph/execution contract, complete trusted closure registration and missing-dependency/cycle vectors; caller-supplied lists prove no complete closure. |
| 7. Independent readers / adapters | Genuinely independent authorship evidence remains absent and is required before stable maturity under the existing rules. Reopen with independently authored readers reproducing the same immutable corpus, provenance and disagreements; adapter work needs a concrete interchange demand. |

After bounded review/fixes, the maintainer must record findings, the public-period
decision and waiver exception, explicitly accept only this draft scope, update
the RFC status/index and confirm the independently versioned Policy draft release record. No acceptance is represented
as stable maturity, product admission completion or a released Spec until its
separate applicable gate completes.

The maintainer selected the independent companion draft release route during
preparation. The proposed first tag is `policy-v1.0.0-draft.1`; no tag or release
is created here. The Policy-scoped amendment to VERSIONING.md and shared builder
routing are part of this material RFC disposition and require the same review.

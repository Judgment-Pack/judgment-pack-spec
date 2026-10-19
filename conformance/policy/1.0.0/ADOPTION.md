# RFC 0023 conditional draft disposition

On 2026-10-19 the maintainer directed: “Accept the bounded draft after CI; record
the limited public review”. This authorizes acceptance of the immutable
supplied-document surface in [spec/policy.md](../../../spec/policy.md), its
Policy offline-reader class and the independent draft release route, effective
only when [PR 218](https://github.com/Judgment-Pack/judgment-pack-spec/pull/218)
merges after required CI passes. The PR carries the proposed Accepted status;
the default-branch RFC remains Review until merge. This record claims no completed
merge, publication, stable maturity, product admission or consumer adoption.

## Actual limited public review and maintainer decision

The initial bounded assessment read [issue 211](https://github.com/Judgment-Pack/judgment-pack-spec/issues/211)
and its one comment, [PR 212](https://github.com/Judgment-Pack/judgment-pack-spec/pull/212),
its six comments, zero submitted reviews and zero inline review comments. The
issue opened 2026-10-18 at 03:01:59 UTC; PR 212 opened at 03:15:52 UTC and merged
at 17:50:10 UTC as `8a56a95d555c17640d2db4984363b779536b3c2a`. That merge adopted
only a Draft RFC/non-normative prototype, expressly withholding companion adoption.
The issue update at 20:55:02 UTC reports corrected candidate work in PRs 216/217,
124 matching vectors and two Codex-assisted readers, while keeping the RFC in
Review and independent evidence outstanding.

All substantive comments in that original history were by the maintainer; one
other comment was a contribution bot. No independent technical objection,
endorsement or implementation review was recorded there. The proposal and
corrected candidate were public from 2026-10-18 to this 2026-10-19 decision, a
limited period with no demonstrated outside stakeholder participation. Silence
is not acceptance or evidence of interoperability.

RFC 0000 sets a reasonable public period according to complexity, with no fixed
minimum. The maintainer explicitly elects to proceed after this limited period
for the **bounded draft**, conditional on required green CI and PR 218 merge,
rather than treating the earlier non-normative merge or absent comments as
acceptance. The exact selector/bounds/coverage surface and deferred items below
limit that disposition. Subsequent technical objections remain grounds for
review through the existing RFC process; the stable independent-evidence bar
is unchanged. This is a disclosed maintainer judgment, not outside review.

The PR 212 same-vendor readiness review and response preserve findings F1–F6.
F1's exact-byte/multiple-media-type defect was fixed; F6's typed references,
original bounds and requirements deferral were addressed. F2 release registration,
F3 current authority, F4 external lifecycle and F5 private-to-portable migration
remain product-owned boundaries, not solved by this offline companion.

## Exact review record and standing exception

The separate reviewer, OpenAI `gpt-6.1-sol` at `xhigh` on 2026-10-19, inspected
frozen tree `60b04d452efa49032a0cc7d3ac1e55a3900410a8`, subsequently committed
unchanged as `7f118278e480d88e53e6a6be2fe084610a2bebf9`. The drafting worker also
used OpenAI `gpt-6.1-sol` at `xhigh`. The reviewer reported **no material findings**
in that bounded artifact; no finding was silently discarded. The complete
report, context and supplied brief are in
[the PR review record](https://github.com/Judgment-Pack/judgment-pack-spec/pull/218#issuecomment-6273316525).
The report SHA-256 is
`6506927d179cfe165122c45e6fafc856e6dd975e1c51d63abda984aacfd711e0`.

This is separate-agent **same-vendor** review. The maintainer applies the standing
temporary different-vendor-review exception, originally recorded for PR 212 in
[this explicit instruction](https://github.com/Judgment-Pack/judgment-pack-spec/pull/212#issuecomment-6253085953),
to this bounded promotion. It does not amend the general governance rule or turn
Codex review into cross-vendor review, outside stakeholder review or independently
authored implementation evidence. Historical review records remain unchanged.

Required CI on the initial promotion found the Core fixture audit incorrectly
counting Policy-owned JSON as Core fixtures. The explicit namespace fix and its
ownership regressions change tests only. The final CI-fix/acceptance delta is
subject to the PR's final bounded review and required CI before merge; the earlier
report is not claimed to cover an unidentified later commit.

## Exact draft dispositions effective upon merge

| RFC question | Draft disposition and condition to reopen |
| --- | --- |
| 1. Selector, bounds and closed grammar | Accept exact `formatVersion: "1.0.0"`, strict independent x.y.z artifact versions, 262,144 parsed bytes, depth 32, 128-character number literals/exponent magnitude 308, 1,048,576 narrative/review/informational bytes, 4,194,304 original bytes, 16,777,216 distinct retained bytes, 16 registrations, and the declared closed field/count maxima; retained bytes and optional `jps-canon`, UTF-8 anchors, pack-only typed references and scoped total coverage. Refuse aliases/unknown members/structured requirements. No evaluator or live authority changes. A grammar/bound change requires explicit selector and compatibility review. |
| 2. Review trust, signatures and cross-workspace adoption | Defer. Interpretation bytes prove no reviewer identity or authorized sign-off. Reopen with a concrete cross-workspace export need, authentication/trust profile, exact reviewed candidate/workflow binding and adversarial verification vectors. |
| 3. RFC 0011 currency registry | Defer; do not adopt or supersede the Draft registry. Reopen with an RFC 0011 disposition and explicit distinction between offline membership and current authenticated admission. |
| 4. Provider lifecycle/freshness | Defer to owning hosts. Read support, byte identity, opaque revision or missing file cannot establish publication/withdrawal. Reopen with a real provider's demonstrated revision/lifecycle/freshness evidence and reviewed mapping/reconciliation/enforcement tests. |
| 5. Teams, quorums, roles and approval | Defer. No universal separation-of-duties rule or imported roles; honest local self-review remains a host workflow choice. Reopen with a team host contract covering quorum/workflow revision, role revocation, expiry and transactional candidate/publication binding. |
| 6. Graph/composition closure | Defer and refuse graph consumers. Reopen with an adopted owning graph/execution contract, complete trusted closure registration and missing-dependency/cycle vectors; caller-supplied lists prove no complete closure. |
| 7. Independent readers / adapters | Genuinely independent authorship evidence remains absent and is required before stable maturity under the existing rules. Reopen with independently authored readers reproducing the same immutable corpus, provenance and disagreements; adapter work needs a concrete interchange demand. |


The independent companion release route was selected by the maintainer. The
first release identifier is `policy-v1.0.0-draft.1`; this source record alone
establishes no publication. The exact tag and a maintainer-published GitHub
release must both exist. This draft
disposition includes the Policy-scoped VERSIONING.md amendment and shared release
builder/workflow routing, without changing Core versions or evaluator semantics.
After the final bounded review/dispositions and required CI, PR merge makes this
draft disposition effective. A later tag and maintainer-published release must
pass the separate exact-source/pin/publication gates.

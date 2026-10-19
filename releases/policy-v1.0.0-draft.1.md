# Policy companion 1.0.0-draft.1

This describes the first independently versioned Policy release at **draft
maturity**, using exact document format `1.0.0`, Core consumers `0.2.0-draft`,
versioned closed schemas and the complete 124-row Policy offline-reader corpus.
The maintainer approved the bounded draft after CI, effective only upon required
green CI and PR 218 merge. The default-branch RFC remains Review until that merge;
this source document alone establishes no immutable publication or conformance
claim. Publication requires the exact `policy-v1.0.0-draft.1` tag and a
maintainer-published GitHub release. Maturity remains draft; a conformance claim
also requires the complete published corpus and the companion class requirements.

The format retains exact content/narrative/source/interpretation/consumer bytes,
UTF-8 section anchors, optional existing `jps-canon` identity, independent strict
artifact versions, role/aggregate bounds and pack-only total scoped coverage.
The JSON release manifest pins exact schemas, format prose and corpus bytes.
The shared release builder refuses publication preparation until draft acceptance
and exact tag/commit/HEAD/clean-tree checks pass. Archive checksums and GitHub
build-provenance attestations use the existing release workflow.

- Reader compatibility: the prototype 0.0.2 wrapper is refused. The corrected
  proposed 1.0.0 input grammar is preserved, but official schema resource IDs and
  valid-result/capability maturity differ. Unsupported formats refuse exactly.
- Writer compatibility: no existing Policy/adoption bytes require rewriting.
  Newly written documents must use exact `formatVersion: "1.0.0"`; artifact
  version arithmetic or a citation cannot select grammar or create adoption.
- Semantic compatibility: input content/reference/anchor/coverage meaning is
  unchanged from the corrected proposal. The reader result now reports `draft`
  instead of `proposed-draft`; clients comparing complete objects must update
  deliberately. No Core evaluator, schema, corpus, Pack execution pin or Dialect
  semantics changes. The earlier candidate/prototype remain archived unchanged.
- Migration compatibility: prototype migration requires explicit intent, new
  immutable Policy/adoption identities, preserved retained bytes and dependent
  snapshot re-review. No approval, permission, role, signature or lifecycle state
  migrates. See the bundled promotion map and migration guide.

Scope excludes Graph consumers/closure, correct natural-language interpretation,
complete organizational policy discovery, authenticated review/signature trust,
provider lifecycle/freshness, currency, current authority and dispatch permission.
No production governance or stable-readiness claim follows. Existing experimental
software pinned to older Spec bytes retains its exact old capability/meaning;
this publication does not upgrade its pin or adopt it on its behalf.

The reference Python reader and Runtime port are Codex-assisted work by this
project, not genuinely independently authored implementations. The maintainer
accepted the limited public review period for this bounded draft and applied the
standing temporary different-vendor-review exception without changing the general
governance rule. The separate OpenAI `gpt-6.1-sol`/`xhigh` review reported no
material findings on tree `60b04d452efa49032a0cc7d3ac1e55a3900410a8`, committed
unchanged as `7f118278e480d88e53e6a6be2fe084610a2bebf9`; its complete record is on
[PR 218](https://github.com/Judgment-Pack/judgment-pack-spec/pull/218#issuecomment-6273316525).
The final CI-fix/acceptance delta requires its own bounded review and required
CI before merge. The [conditional disposition](../conformance/policy/1.0.0/ADOPTION.md)
records scope, public-process limits, deferred questions and reopening conditions.
No outside stakeholder review, independent interoperability or publication is
inferred from these records.

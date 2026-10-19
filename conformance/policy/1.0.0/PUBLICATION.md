# Independent Policy draft publication

The maintainer selected independent companion draft releases with Core unchanged.
The prepared first release is **`policy-v1.0.0-draft.1`**: first draft publication
of exact document grammar `formatVersion: "1.0.0"`. It is not a created tag,
release, adoption decision or stable claim. RFC 0023 is still in Review.

## Exact identities and existing release machinery

`policy-v<releaseVersion>` is the Policy-only namespace; `releaseVersion` must be
strict three-component SemVer followed by `-draft.N`, with an unsigned decimal
`N` and no leading zero except `0`. No stable Policy tag is supported. The first
release identifier is `1.0.0-draft.1`; its base deliberately matches grammar
1.0.0, but equality or a shared prefix never implies compatibility. The release
identifier, document `formatVersion`, immutable artifact x.y.z `version`, Core
consumer `specVersion` and local vector-carrier version `"1"` are separate values.

The same `tools/build_release.py` and GitHub release workflow route this scoped
namespace to a closed [release manifest](../../../releases/policy-v1.0.0-draft.1.json).
The builder checks exact metadata/schema/corpus/format pins, RFC draft acceptance,
release notes, tag/commit/HEAD equality and a clean tracked worktree. The existing
archive, SHA-256 checksum, draft-prerelease and GitHub build-attestation steps are
shared with Core. No alternate publisher or bypass of Core checks is introduced.

The Policy bundle prefix is `judgment-pack-policy-1.0.0-draft.1/`; archive names
are `judgment-pack-policy_1.0.0-draft.1_artifacts.tar.gz` and `.zip`, accompanied by
`checksums.txt` and build provenance. It contains only the selected Policy prose,
versioned schemas, complete 124-row input corpus/examples/checker, exact release
manifest/notes, pinned dependencies and shared strict-reader/canonicalizer helper,
the required frozen Core `0.2.0-draft` consumer schema, referenced companion prose and archived RFC
candidate/prototype provenance. Historical material stays explicitly unadopted.
Core bundles continue on `v<specVersion>` with their existing exact schema and
corpus checks; independently released Policy schemas/corpus are excluded from
Core bundle selection. No Core `specVersion` or evaluator semantics change.

## Frozen format meaning and discovery

The public document schema identities are exactly
`https://judgmentpack.org/schema/policy/1.0.0/{common,policy,governing-adoption}.schema.json`.
The local fixture/vector carrier schemas use `fixture` and `vectors` at that
same versioned prefix. The site serves those exact resource bytes. Before the
first immutable release they are candidate resources; resolving a URL proves no
adoption. On first publication those resource URLs and all normative format
bytes/corpus inputs are frozen. The release manifest pins their digests.

Another draft release for the same exact format MUST retain those format/schema/
corpus pins. It may revise packaging or non-normative explanation, with explicit
release notes. It MUST NOT change existing validity, interpretation, refusal
meaning/order, schema bytes or expected corpus answers while continuing to call
that input grammar `1.0.0`. A semantic change requires an explicit new format
selector, new schema resource URLs and reviewed migration/compatibility guidance.
No URL already published by a prior release is repointed. Each tag's JSON manifest
and notes remain available; schema identity/compatibility is never inferred from
release or artifact version arithmetic.

The class's claim names the independent Policy tag/release and exact corpus
manifest/digest, plus format and supported Core consumer version. Until the tag
and maintainer-published GitHub release both exist, no immutable publication or
Policy offline-reader conformance claim is available. Draft RFC acceptance alone,
an experimental software release and two same-author ports do not establish it.

## Gates before any publication

A bounded independent review of the exact promotion, maintainer disposition of
findings and public-period adequacy, and explicit draft-only RFC acceptance remain
required. Record the standing temporary different-vendor-review waiver honestly;
it changes no general governance rule and supplies no independent authorship.
After disposition, update the RFC status and pending wording, regenerate the
prepared release's exact format/corpus pins, run required repository CI, then
create a reviewed tag and let the shared workflow prepare the draft prerelease.
Publishing that release is a separate maintainer action. No tags are created by
this preparation, and the builder deliberately refuses the current Review state.

The [prepared release notes](../../../releases/policy-v1.0.0-draft.1.md) identify
reader, writer, semantic and migration effects. Stable maturity remains blocked
on genuinely independently authored readers/evidence under the existing rules.

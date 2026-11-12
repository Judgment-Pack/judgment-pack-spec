# Versioning and release policy

Core Judgment Pack Specification releases use Semantic Versioning identifiers with a leading `v` on
Git tags. Specification `0.3.0` is identified by the exact tag `v0.3.0`; `0.2.0-draft` and
`0.1.0-draft` keep the tags `v0.2.0-draft` and `v0.1.0-draft`. Only a tag and GitHub release
published by the maintainers establish an immutable release; similarly named files on the mutable
`main` branch do not. Release tag `v0.4.0` identifies a distribution that carries `specVersion`
`0.3.0` unchanged, not a specification `0.4.0`; [its section](#release-v040-carries-specversion-030-unchanged)
states the route.

`0.3.0` is the first Core `specVersion` without the
retired `-draft` suffix; the identifiers and tags of `0.1.0-draft` and `0.2.0-draft` do not change.

## Specification versions

`specVersion` identifies the specification release a Judgment Pack targets. Readers MUST compare
the complete value; they must not infer compatibility from a shared major or minor number before
`1.0.0`.

A conformance claim is made against one exact `specVersion`. That applies to every class, and it
binds hardest on evaluator conformance (Core §3.4): such a claim names the exact version and the
evaluation corpus published with it, and is not inherited by a later or an earlier version. The corpus
version is the `suiteVersion` member of the evaluation manifest, and the corpus is frozen when a
`specVersion` is released — rows are added only on the way to the next one (Core §3.4.1) — so two
identically worded claims require the same rows, and such a claim must state that every one of those rows
passed. A failing row blocks the claim unless a project-issued erratum
(`conformance/evaluation/errata.md`) marks it defective for that corpus version; a claimant cannot make
that call for itself. A superseded schema stays published so documents that keep the older `specVersion`
remain checkable, and a previously published versioned URL stays resolvable; neither confers anything on a
claim. A preserved schema is served at the `$id` it was published under, and where that identifier was
re-pointed to this project's own domain it differs from the tagged artifact in that one member and nothing
else — the release notes of the version that preserved it publish the digest of both forms.

Before `1.0.0`, a release may change reader, writer, or semantic behavior incompatibly. Its release
notes must record the change and include a `specVersion` migration note, including when no automatic
migration is available.

## Maturity levels

The `status` in each Core conformance manifest is a maturity level, not a version. Its closed ladder
is:

- `draft`: the document is still being exercised and the acceptance evidence is not yet complete;
- `candidate`: independent conforming implementations, production adopters, and sustained outside
  contribution are in and recorded for the document; and
- `release`: the evidence has been accepted and recorded for the `1.0.0` standards claim.

Movement is one step at a time. The recorded evidence above moves a document from `draft` to
`candidate`; the maintainer's recorded `1.0.0` acceptance of that evidence moves it from `candidate`
to `release`. Production use alone does not move a document or establish a standard.

## Core pre-releases

A Core release candidate uses the SemVer `-rc.N` form. The `0.3.0` release began with candidate `v0.3.0-rc.1`, published as a GitHub pre-release for about one week so adopters'
tooling can read the renamed manifest status. The unsuffixed `v0.3.0` tag is the release. The Policy
companion's `policy-v<releaseVersion>-draft.N` route remains independent and is not replaced by this
Core convention.

Across the project, `vX.Y.Z-rc.N` is a candidate of the complete milestone that graduates to
`vX.Y.Z` with no change to its normative artifacts (schemas, corpus, Core and companion rules);
text and tooling that named the candidate distribution are updated to name the release, and the
release's notes list those changes. `vX.Y.Z-alpha.N`, used by the implementations and never by this
repository's Core route, is a scoped cut for a named consumer that never graduates.

That first candidate is a distribution of the proposed exact `specVersion` `0.3.0` artifacts;
`0.3.0-rc.1` is its distribution identity, not a pack version selector. Its closed mapping at
`releases/v0.3.0-rc.1.json` is required by the builder. Both manifests remain maturity `draft`:
release candidacy does not establish the independent-evidence maturity `candidate`. Each RC bundle
records its exact distribution tag and source commit in `release-identity.json`, alongside the map
and exact RC notes. Other Core tags, apart from
[release `v0.4.0`](#release-v040-carries-specversion-030-unchanged), still require their complete
version to match the artifacts; no general prerelease compatibility rule is introduced.

The candidate does not establish the final `0.3.0` immutable release or freeze its final corpus.
Candidate test results identify the RC tag and commit and remain provisional; a final exact-version
conformance claim requires the corpus published with `v0.3.0` and every applicable row passing.
Publishing the RC starts the required adopter period; creating a draft release or preparing these
files does not. Final publication follows about one week of public RC availability and review of
adopter feedback, with the remaining release gates satisfied.

The `main` branch describes work in progress. It is not an immutable specification release and
must not be used as a reproducibility anchor.

## Explicit second Core distribution candidate

The expressly approved RFC0029 adoption route prepares exactly `v0.3.0-rc.2`, also mapping to proposed
specVersion `0.3.0` and draft maturity. This expressly amends the former single-candidate plan;
it does not replace RC1, its immutable source/tag/assets or its recorded mapping/notes. The closed
RC2 mapping is `releases/v0.3.0-rc.2.json`; release tooling allowlists these two candidate mappings
and, apart from them, only [release `v0.4.0`'s](#release-v040-carries-specversion-030-unchanged).
It does not strip arbitrary prerelease suffixes to infer compatibility. Final v0.3.0 retains
milestone #2, and its final corpus/feedback/release gates remain.

RC2 adds new exact selected retained-column/1 schema resources and its own leaf corpus/inventory.
Its support tuple names distribution `0.3.0-rc.2`, exact source commit and schema/corpus digests,
independent of pack specVersion. First publication freezes that leaf's new resource bytes and
corpus; no prior schema URL is repointed. A later semantic/grammar/bound/refusal change needs a
new exact supported contract identity and versioned resources rather than reinterpreting this one.
Both-language selected-leaf certification establishes only its named scope, never general Core,
stable maturity, independent authorship, truth or authority. Historical staged Dialect recordings
retain their standing. Public availability and adopter-feedback disposition remain necessary;
this preparation does not establish that time elapsed or prescribe an invented RFC comment period.

## Release v0.4.0 carries specVersion 0.3.0 unchanged

Release `v0.4.0` publishes work outside Core and re-pins nothing. Its closed mapping
`releases/v0.4.0.json` names `specVersion` `0.3.0`, maturity `draft` and distribution
`specification-unchanged`. The builder refuses any other content in that mapping, and it holds the
Core schema and both corpus manifests to `0.3.0`, the version the mapping names.

The tag name is not a pack selector. Packs keep declaring `specVersion` `0.3.0`; a pack declaring
`0.4.0` is refused. A conformance claim still names `specVersion` `0.3.0` and its corpora, and a
selected retained-column leaf claim is still made against a `v0.3.0` installation. In the format
status records `v0.4.0` counts as the last release of the families it carries, but it is not their
compatibility baseline, which stays `v0.3.0`.

This mapping is that tag's alone. No other tag may use it, and it introduces no general rule that a
tag may differ from the `specVersion` of its artifacts. `specVersion` `0.4.0` is not assigned, and no
release carries it. Any further release whose tag differs from its artifacts' `specVersion` needs its
own amendment of this document and its own reviewed identity in the builder; this section implies
none.

## Staged draft Core selector 0.4.0-draft

[RFC 0031](rfcs/0031-annotations-and-value-sets.md), a Draft, targets the next Core `specVersion`
after `0.3.0` and assigns it no number. So that implementations can admit packs that use its
annotations and value sets, its schema, Core text, document cases, evaluation rows and example are
staged under the working selector `0.4.0-draft`:
[`spec/staged/judgment-pack-core-0.4.0-draft.md`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/spec/staged/judgment-pack-core-0.4.0-draft.md)
names them. No release is established by this staging, and the selector is not assigned.

- **Not a release.** No tag carries `0.4.0-draft`, and it introduces no general rule. Every staged
  path is `export-ignore`, so no release archive carries the staged schema, text, cases, rows or
  example, and the site serves none of them. The schema's `$id` under `0.4.0-draft` is the staged
  resource's identifier, not a publication, as the `0.4.0` path of RFC 0028's staged schema is.
- **Not a claim.** No conformance claim may name `0.4.0-draft` or its staged vectors. A `0.3.0`
  reader refuses a pack declaring it, by the exact selector.
- **The suffix.** The `-draft` suffix stays retired for Core releases. Here it marks a selector that
  no release carries, so that it cannot be mistaken for `specVersion` `0.4.0`, which is not assigned,
  or for release `v0.4.0`, which carries `0.3.0`.
- **Landing.** When the maintainers open the version that carries RFC 0031, they assign its
  selector, and the staged artifacts take it; nothing staged binds the choice. A pack written to
  `0.4.0-draft` moves up by changing its `specVersion`, which changes its bytes and digest, and must
  then satisfy the released rules; RFC 0031's Graduation subsection lists the steps. RFC 0031 stays
  a Draft until its own Evidence bar is met.

The [record-shape catalog](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/catalog/README.md) lists every schema whose `$id` is in the
specification's schema namespace, `https://judgmentpack.org/schema/`, so it lists the staged schema,
as it lists RFC 0028's: family `judgment-pack-core` at `0.4.0-draft`, with its digest and its
normalized text in `catalog/record-shapes.json` and its change records in `catalog/changes/`.
Listing a shape publishes nothing. In `catalog/format-status.json`, Core's `draftVersion` is derived
from the catalogued schemas and reads `0.4.0-draft`. That names the staged working selector; it is
not an assigned next `specVersion`. Core's baseline and last release are unchanged. No release bundle
carries the staged schema itself. A bundle that carries `catalog/` carries the catalog's record of
the staged shape: its path, `$id`, digest and normalized text, its change records, and Core's
`draftVersion`. Only release `v0.4.0`'s bundles carry `catalog/` today, and that tag precedes this
staging.

## Pack versions

The root `version` member identifies a revision of one pack series. It is independent of
`specVersion` and follows the three-component grammar defined by the Core schema.

A published `(id, version)` pair SHOULD be immutable. Changed pack content should receive a new
pack version, even when `specVersion` does not change.

## Compatibility dimensions

Release notes describe compatibility separately for:

- **reader compatibility** — whether an older reader can parse and preserve a newer document;
- **writer compatibility** — whether a newer writer can emit documents accepted by older readers;
- **semantic compatibility** — whether conforming consumers assign the same portable meaning; and
- **migration compatibility** — whether a deterministic document transformation is available.

No compatibility dimension is implied merely because two releases share a version prefix.

## Release artifacts

An immutable Core release contains, at minimum:

- the tagged Core prose specification;
- the tagged JSON Schema with a versioned `$id`, plus any superseded schema still published;
- examples, document-conformance cases, and the evaluation corpus from the same commit; and
- release notes identifying maturity, compatibility, and known limitations;
- `.tar.gz` and `.zip` artifact bundles from that commit; and
- SHA-256 checksums and GitHub build-provenance attestations for those bundles.

If prose, schema, or conformance artifacts disagree, the conflict is a specification defect. The
artifact roles and conformance boundaries in the tagged Core specification determine which claim
each artifact is permitted to make.

## Deprecation and support

Pre-`1.0.0` releases have no compatibility or security service-level guarantee. Maintainers
may deprecate or remove behavior in a later `0.x` release, but must record the change in release
notes. A stable release will require a separate support and deprecation policy before publication.

## Independently versioned Policy draft companion

Policy uses the scoped tag `policy-v<releaseVersion>`, where `releaseVersion` is
strict three-component SemVer followed by `-draft.N` (unsigned ASCII decimal N,
no leading zero except `0`). This route is draft-only; it creates no stable
maturity or support guarantee. Only the tag and maintainer-published GitHub
release together establish an immutable Policy release. The prepared first
identifier is `policy-v1.0.0-draft.1`; preparation does not publish it.

A Policy release names the exact document `formatVersion`, supported Core consumer
`specVersion`, closed schema identities and complete corpus/digest in its own
versioned JSON release manifest beside the release notes. Those values and an
artifact's x.y.z `version` are independent of the companion release identifier.
The existing builder/workflow shares archive, checksums and build provenance with
Core, but validates a Policy tag against its own manifest and explicit draft RFC
acceptance. Core tags still require exact Core schema/document/evaluation pins (release `v0.4.0`'s
pins are the `0.3.0` its mapping names);
Core bundles exclude independently versioned Policy schema/corpus directories.

First publication freezes the normative meaning, schema resource bytes/URLs and
complete corpus inputs/results for an exact Policy format. A later draft release
for that same format retains those pins and can change packaging or non-normative
explanation only. Changed acceptance, interpretation, bounds, refusal semantics
or grammar requires a new exact format selector, new versioned schema resources
and reviewed compatibility/migration guidance. Published resource URLs, release
manifests and tagged artifacts are preserved; they are never repointed.

A Policy offline-reader conformance claim names the exact independent Policy
release, format, supported Core consumer version and complete published corpus
manifest/digest; every row must pass. No claim is available before publication.
It establishes supplied-document agreement only, with the scope/exclusions of
[the companion](spec/policy.md). Stable maturity still requires the independent
implementation evidence in the existing governance and RFC process.

## Proposed workflow attribution model for Spec 0.5.0

[RFC 0028](rfcs/0028-complete-workflow-contributors.md) stages complete contributor attribution;
no release is established by this proposal. Output record version 2 and summary version 2 use
complete typed contributor memberships; drift version 2 compares those counts. Execution version
3 explicitly selects that model. Execution version 1 retains its historical meaning; version 2
is reserved by the separate Draft admission-proof RFC 0024. Workflow document version 1 and
selection version 1 retain their forms. `workflow-contributors-2.schema.json` identifies the
attribution model and does not adopt a workflow-version-2 protocol.

Readers and writers must select these exact versions; a mixed execution or mixed-model drift
is refused. Historical output/summary version 1 remains representative attribution, incomplete,
or unavailable in the older experimental recordings. Wrapping its singular id into a singleton
does not migrate it to complete evidence. Complete migration needs sufficient retained evaluation
evidence or replay, followed by rebuilding all dependent commitments while preserving history.
This changes attribution reading, writing and semantics; it changes no Core resolution or
published Core `0.3.0` artifact. The new `$id` under `0.4.0` is draft staging, not publication, and
release `v0.4.0` does not publish it: that path is the staged resource's identifier and does not name
that release.

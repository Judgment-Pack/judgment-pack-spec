# Versioning and release policy

Core Judgment Pack Specification releases use Semantic Versioning identifiers with a leading `v` on
Git tags. Specification `0.3.0` is identified by the exact tag `v0.3.0`, specification `0.5.0`
by `v0.5.0` and specification `0.6.0` by `v0.6.0`; `0.2.0-draft` and `0.1.0-draft` keep the tags `v0.2.0-draft` and `v0.1.0-draft`.
[The release numbering rule](#release-numbers-and-specversion) states how a tag's numbers relate to
the `specVersion` it carries. Only a tag and GitHub release published by the maintainers establish
an immutable release; similarly named files on the mutable `main` branch do not. Release tag
`v0.4.0` identifies a distribution that carries `specVersion` `0.3.0` unchanged, not a specification
`0.4.0`; [its section](#release-v040-carries-specversion-030-unchanged) states the route, and no
`specVersion` `0.4.0` is assigned.

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

## Release numbers and specVersion

This rule is normative for every Core release from `v0.5.0` on.

- **Major and minor.** A Core release tag's major and minor numbers equal those of the
  `specVersion` the release carries. A `specVersion` is first released under the tag whose patch
  number is `0`: `specVersion` `0.5.0` is first released as tag `v0.5.0`.
- **Patch.** The patch number counts the later releases that carry the same `specVersion`
  unchanged: `v0.5.1`, `v0.5.2`, and so on. Such a release may change documentation, tooling,
  companion documents and staged drafts for a later version. It does not change the released
  schema, the normative content of the Core text, or the released conformance cases and rows of that
  `specVersion`, which are frozen when the `specVersion` is released (Core §3.4.1).
- **The selector.** A pack's `specVersion` stays `0.5.0` under every such release. The tag is not a
  pack selector: readers compare the complete `specVersion`, never the tag. A new `specVersion`
  always takes a new minor (or major) number.

Recorded exception: tag `v0.4.0` (2026-11-02) carries `specVersion` `0.3.0` unchanged; under this
rule it would have been `v0.3.1`. It is published and immutable and stays as it is
([its section](#release-v040-carries-specversion-030-unchanged)). Because that tag is taken, no
`specVersion` `0.4.0` is assigned: the version staged as `0.4.0-draft` is released as `0.5.0`
([its section](#core-050-was-staged-as-040-draft)).

The release builder (`tools/build_release.py`) applies this rule. Apart from the allowlisted
mappings below, it derives the `specVersion` a Core tag carries from the tag's major and minor
numbers (`vX.Y.Z` carries `X.Y.0`) and holds the Core schema and both corpus manifests to it. It
never strips a prerelease suffix. For a patch tag it also requires the normative artifacts to be
byte-identical to those the `X.Y.0` release published: the Core text and schema, both corpus
manifests, every document case and evaluation pack they name, and every schema whose `$id` is under
`X.Y.0`. It compares them with a record of those bytes, `releases/vX.Y.0.normative.json`, whose own
SHA-256 the builder pins. It compares the files in the worktree before it archives the release, and
in each bundle after, so an export attribute in `.gitattributes` cannot leave a recorded file out.
`releases/v0.5.0.normative.json` was derived from the files of tag `v0.5.0` as Git stores them, and
agrees with an archive of that tag and with the schema digests its notes publish. A `specVersion`
with no such record has no patch release, so tag `v0.4.1`, which would carry the never-released
`0.4.0`, is refused, and so is `v0.3.1`, because `0.3.0` has no record. The errata, the READMEs and
the examples are not held: an erratum (`conformance/evaluation/errata.md`) or a clearer explanation
may follow a release. A patch release's bundles also carry `catalog/`, that record and a generated
`release-identity.json` naming the release's version, its tag, the `specVersion` it carries, the corpus maturity and the
distribution `specification-unchanged`.

In `catalog/format-status.json` a patch tag is not a candidate. It carries the shapes of its
`specVersion` unchanged, so it becomes the last release and the baseline of the families whose
`$id` is under that `specVersion`, exactly as a later release of them would; no other record moves.
The record-shape check refuses a patch tag whose `specVersion` no `X.Y.0` release in `releases/`
carries, or that has no normative record.

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
[release `v0.4.0`](#release-v040-carries-specversion-030-unchanged), follow
[the release numbering rule](#release-numbers-and-specversion); no general prerelease compatibility
rule is introduced.

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
status records `v0.4.0` counted as the last release of the families it carries, but never as their
compatibility baseline, which stayed `v0.3.0` until `v0.5.0`.

This mapping is that tag's alone, and no other tag may use it. Under
[the release numbering rule](#release-numbers-and-specversion), adopted after this tag, it would have
been `v0.3.1`; it is that rule's recorded exception. `specVersion` `0.4.0` is not assigned, and no
release carries it. Any release whose tag that rule does not give needs its own amendment of this
document and its own reviewed identity in the builder; this section implies none.

## Core 0.5.0 was staged as 0.4.0-draft

[RFC 0031](rfcs/0031-annotations-and-value-sets.md) was staged before its release under the working
selector `0.4.0-draft`: its schema, Core text, document cases, evaluation rows and example sat in
staged paths that no release archive carried and the site did not serve, and no conformance claim
could name them. That selector was never released, and the staged paths are retired. Tag `v0.4.0`
already carried `0.3.0`, so under [the release numbering rule](#release-numbers-and-specversion) the
staged version is released as `specVersion` `0.5.0` under tag `v0.5.0`, not as `0.4.0`.

A `0.5.0` reader refuses a pack declaring `0.4.0-draft`, by the exact selector. A pack written to the
draft moves up by changing its `specVersion` to `0.5.0`, which changes its bytes and digest, and must
then satisfy the released rules (Core §11). The `-draft` suffix stays retired for Core releases.

The [record-shape catalog](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/catalog/README.md)
keeps the staged schema's history in its change records, ending with the record of its retirement.
Core's `draftVersion` in `catalog/format-status.json` reads `0.5.0`.

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
acceptance. Core tags still require exact Core schema/document/evaluation pins at the `specVersion`
they carry (release `v0.4.0`'s pins are the `0.3.0` its mapping names);
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

## Independently versioned registry companion

The [registry companion](spec/registry.md) uses the scoped tag `registry-v<releaseVersion>`, where
`releaseVersion` is strict three-component SemVer with no prerelease or build suffix. It is the
Policy route without its draft-only restriction: a registry release has maturity `released`, which
is not stable. Only the tag and a maintainer-published GitHub release together establish one. A
tag releases the format its major and minor numbers name: `registry-v1.0.x` format `1.0.0`, whose
text is `spec/registry.md`, and `registry-v1.1.x` format `1.1.0`, whose texts are `spec/registry.md`
and `spec/registry-1.1.0.md`, two files of one companion. A tag whose numbers name no such format
is refused. The first release is `registry-v1.0.0`; `registry-v1.1.0` releases format `1.1.0`.
Preparing either publishes nothing.

A registry release names, in its own JSON release record `releases/<tag>.json` beside its notes,
its exact format, the `$id` of every schema under `schema/registry/<format>/`, and the SHA-256 of
each of the format's texts, of its rows' README and of every schema; its code list with its digest
and its number of codes; and its rows' manifest with its digest, its number of rows and the digest
of every file under `conformance/registry/<format>/`. For `registry-v1.0.0` that is
`schema/registry/1.0.0/`, `conformance/registry/README.md` and `conformance/registry/1.0.0/`; for
`registry-v1.1.0` it is `schema/registry/1.1.0/`, `conformance/registry/1.1.0/README.md` and
`conformance/registry/1.1.0/`, with format `1.0.0`'s rows' README, `conformance/registry/README.md`,
which its bundle carries and which changed after `registry-v1.0.0`. Its record names neither format
`1.0.0`'s schemas nor its rows: the bundle carries them as the latest record of format `1.0.0` pins
them, and the builder refuses the tag when one differs from that record or a file is added or
missing.
The builder derives that record from the tagged tree and refuses the tag unless the committed
record equals it, its maturity is `released`, the format's status sentence occurs once across its
texts and says `released`, its code list and its rows' manifest say `released`, no text, rows'
README, README heading or manifest label still calls the format proposed, no text or rows' README
calls the format, its rows or its lists a draft, proposed or unreleased, and no schema's title or
description still calls it a draft, staged, proposed or unreleased. They say so until the commit
the tag names, which changes all of them. Each of the format's design records must also say
`Status: Accepted`. Each format's record is held to its own tag's tree:
`registry-v1.0.0` builds from its tag exactly as before, with the same bundle and record bytes.

A release's bundle, `judgment-pack-registry-<releaseVersion>`, carries the format's texts, its
schemas, its code list and rows with their README, the checks that hold the rows to the texts, the
design records and the companions the texts link, this document, the license and the record and
notes. Format `1.1.0`'s bundle also carries format `1.0.0`'s schemas, rows and checks, which its
own build on, and the second reader its rows' README names. A Core bundle carries the text and
none of the registry's schema or row directories, as it carries none of Policy's. The site serves each format's schemas at their `$id` once that format's
rows' manifest says `released` and its own release record names those bytes, and serves no
registry schema or row as a file.

A schema published at its `$id` keeps its bytes: the builder refuses a release whose record and an
earlier record of the same format, in the worktree or at an earlier registry tag, name different
schema identities or schema bytes. A conformance claim names its class, the exact registry release
and its complete rows, which that release's record identifies ([the companion](spec/registry.md)
§15). The first stable release needs the second reader §15 requires, and its own reviewed change to
the builder.

## Independently versioned terraform-file companion

The [terraform-file companion](spec/terraform-file.md) uses the scoped tag
`terraform-file-v<releaseVersion>`, where `releaseVersion` is strict three-component SemVer with no
prerelease or build suffix. It is the registry's route: a terraform-file release has maturity
`released`, which is not stable. Only the tag and a maintainer-published GitHub release together
establish one. The first is `terraform-file-v1.0.0`; preparing it publishes nothing.

The reading's table of accepted `format_version` values has a release number of its own, a semantic
version in which each newly accepted row is a patch release ([the companion](spec/terraform-file.md)
§4). A tag's number is the table release it carries. The first tag carries table release `1.0.0`,
and each later tag carries exactly the next patch of the latest earlier release, whether it accepts
new rows or none. An erratum release, one that corrects the text, the lists or the vectors and
accepts no new row, also bumps the table's release by a patch, with no new row; its record says so
with an empty `added`. So `terraform-file-v1.0.1` carries table release `1.0.1`, whatever it
changes. The text defines no minor or major release of the table, so this route has none until the
text defines one. The builder refuses a tag whose number is not the release the table gives, a
first release whose table release is not `1.0.0`, and a later one whose table release is not the
next patch of the latest earlier release, in the worktree or at an earlier terraform-file tag.

A terraform-file release names, in its own JSON release record `releases/<tag>.json` beside its
notes, the exact reading `1.0.0` and the SHA-256 of the companion text and of the vectors' README;
the format table with its digest, its release, its rows and, as `added`, the rows its release
accepts beyond the latest earlier release (every row for the first, none for an erratum); the code
list with its digest and its codes; the vectors' manifest with its digest, the id of every vector
and the digest of every file under `conformance/terraform-file/1.0.0/`, every declaration and vector
among them; and the SHA-256 of the second reader, `tools/terraform_file_reader.py`, whose agreement
with every vector the release shows. The builder derives that record from the tagged tree and refuses the tag unless the committed record equals it,
its maturity is `released`, the text's status sentence, the code list, the format table and the
vectors' manifest all say `released`, and neither the text nor the vectors' README still calls the
reading proposed. They say so until the commit the tag names, which changes all of them.

The release's bundle, `judgment-pack-terraform-file-<releaseVersion>`, carries the text, its code
list, format table and vectors with their README, the checks that hold the vectors to the text and
the second reader they run (it uses the standard library only and reads only the bytes it is given,
so a consumer runs both from the bundle), the design records and the companion texts the text links, this document, the license and the record
and notes. A Core bundle carries the text and not the vectors' directory, as it carries none of the
registry's or Policy's. The companion has no schema, so a release serves nothing new on the site:
the text's page is published as it is now, and no code list, table, declaration or vector is served
as a file, before a release or after it.

A reading never shrinks from one release to the next: the builder refuses a release whose record
and an earlier record of the same reading, in the worktree or at an earlier terraform-file tag,
carry the same table release, or where the record of the higher table release lacks a code, an
accepted `format_version` of a `document` or a vector that the lower one names. A later release may
change the bytes of the text, the lists and the vectors, as a later registry release may change its
rows' bytes: no byte is frozen from one release to the next, and each release's record pins its
own. A conformance claim names the exact terraform-file release, the table release it
implements and its complete vectors, which that release's record identifies ([the
companion](spec/terraform-file.md) §12). The first stable release needs a second, independently
written reader that agrees with the first on every vector (§12), and its own reviewed change to the
builder.

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

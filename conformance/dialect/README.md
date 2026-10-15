# Dialect vectors (staged)

This directory holds 12 vectors for the dialect, written for the preparation-verifier class that
the companion document [`spec/dialect.md`](../../spec/dialect.md) defines. Its design record,
[RFC 0018](../../rfcs/0018-dialect.md), was accepted on 2026-10-15, and the vectors are **staged**
until the next `specVersion` opens. They are in no corpus.

This directory is where they wait — reviewed, held to the same checks as a corpus, and runnable by
hand — as the [checkpoint witness vectors](../witness/README.md) and the
[staged evaluation rows](../evaluation/staged/README.md) wait for theirs.

- **Not part of any corpus.** The companion document's §14 holds a preparation verifier to the
  dialect vectors published with the specification version its claim names. No version publishes
  these, so no claim may cite them, and no conformance claim of the class is available until one
  does. Nothing here changes Core `0.2.0-draft`, its schema, its four classes, or either of its
  corpora.
- **Not published with the specification, and in no release bundle.** The site's build skips this
  directory, as it skips the other staged directories, and a test holds that nothing under it is
  served. [`.gitattributes`](../../.gitattributes) marks it `export-ignore`, so no `git archive`
  release bundle carries it, and `-text`, so no checkout converts a line ending and changes a
  vector's bytes. The directory is work in progress on `main`, reachable in the repository and
  nowhere else.
- **Not this repository's to change.** Every file under [`vectors/`](vectors/) is the reference
  Runner's, byte for byte.

## Where they come from

[`vectors/`](vectors/) is the Runner's `vectors/preparation/`: the same files, the same names, the
same bytes, its own README and manifest among them. The first nine vectors were copied from commit
`05636eda96a9588279d61a6272625be859a28117`, the head of Runner pull request 77, which was
squash-merged and reached the Runner's `main` as commit
`82116bfab7705f74ca3e493c9722dd3831c7418f`, whose `vectors/preparation/` holds the same files. The
tenth, `http-shaped-source`, was copied from the Runner's `main` at commit
`c84e8e64e5d30c835f8d8e6370cd48e2bfd35ee9`, Runner pull request 80 squash-merged, whose generator
wrote the first nine again byte for byte. The eleventh and twelfth, `version-3-bound` and
`unbound-bound-at-import`, the first of dialect version 3, and the Runner's README and manifest as
they now are, were copied from the Runner's `main` at commit
`89cf44109ad3a9862ab0386811bef63d8a9a1657`, Runner pull request 83 squash-merged, whose generator
wrote the first ten again byte for byte. This repository's manifest records each extension, in
order, in `source.extendedBy`. The Runner's README says
what each file holds and how the vectors were generated, and its manifest gives every file's
SHA-256, the binding the Runner passes for each preparation, the record's binding as recorded, and
what the Runner's `verify-run` reports of each export. A change to a vector is a change to the
Runner's first: the Runner calls them "hand-maintained normative data", and says that changing one
"is a change of the contract a second reader is held to".

The links in the Runner's README are relative to the Runner's repository, and do not resolve here;
the repository's link check passes over `vectors/` for that reason.

## What a vector holds, and the answer a verifier gives

Each vector is a directory. Of its files, a preparation verifier reads:

| File | Given to the verifier as |
| --- | --- |
| `mapping.json` | the dialect document; in a vector that holds `binding.json`, the bound dialect, which the verifier must make of the two files below (the companion document, §4.4) |
| `unbound.json` | in a vector of a dialect bound at import only: the dialect document, of version 3, with an unbound source |
| `binding.json` | in a vector of a dialect bound at import only: its binding document |
| `case.json` | the case document |
| `sources.json` | the acquisitions; `{}` when the vector has no such file (a case-only run) |
| `profiles.json` | the input profiles it trusts |
| `run.json` | the preparation to verify, `run.input.preparation`; and the record: the bytes `run.auditBytes` holds in standard base64, or, in an export of version 2, which carries no bytes, the record `run.audit`, written as one line: that member's value exactly as `run.json` writes it, with no re-encoding (the companion document, §11) |

It requires a binding exactly when the Runner's `verifyRun.arguments` hold `--require-bound`.
`preparation.json` and `preparation.sha256` are what it must compute: the preparation's canonical
bytes, recomputed from the first four files at the given preparation's `verifiedAt`, and their
digest. The other files — `release-digest.txt`, `public-key.txt`, `checkpoints.jsonl` — are for
`verify-run`'s checks of an export, which are not this class's.

[`manifest.json`](manifest.json), this repository's, carries `"status": "staged"`, the RFC that
proposed the vectors (`proposedBy`), their `source` (the commit the first nine were copied from;
as `mergedAs`, the Runner's `main` commit that holds the same files; and as `extendedBy`, for each
later extension in order, the Runner's pull request, `main` commit and vectors), the SHA-256 of the
Runner's README and manifest (`runnerFiles`), and one row per vector: `id`; `path`; `requiresBinding`; and the answer the class
gives, `expectedResult`, `reading` or `finding`, with `expectedBinding` for a reading and
`expectedFinding` for a finding. The answers were written from the companion document's §11 and
the Runner's manifest:

| Vector | `verify-run` reports | The preparation verifier gives |
| --- | --- | --- |
| `valid` | `verified-inputs` | a reading, binding `matches` |
| `recomputed-one-second-later` | `binding-mismatch` | the finding `binding-mismatch` |
| `unbound-record` | `unbound` | the finding `unbound` |
| `foreign-binding-kind` | `binding-foreign-kind` | the finding `binding-foreign-kind` |
| `changed-table-lineage` | refused: `retained lineage does not match recomputation` | the finding `preparation-differs` |
| `disposition-differs-from-audit` | `audit-disposition-mismatch` | a reading, binding `matches` |
| `unsigned-parameters` | `verified-inputs` | a reading, binding `absent` |
| `escaped-strings` | `verified-inputs` | a reading, binding `absent` |
| `numeric-spellings` | `verified-inputs` | a reading, binding `matches` |
| `http-shaped-source` | `verified-inputs` | a reading, binding `matches` |
| `version-3-bound` | `verified-inputs` | a reading, binding `matches` |
| `unbound-bound-at-import` | `verified-inputs` | a reading, binding `matches` |

The tenth, `http-shaped-source`, is the vectors' one source of shape `http`: version 2's `operation`
reads a gateway source of shape `airbyte`, `mcp` or `http` since the amendment of 2026-10-15
(the companion document, §4.1), and its request is `adapter-http`'s method, path and query rather
than a tool call. Its preparation has the form of the other nine.

The eleventh and twelfth are dialect version 3. `version-3-bound` is the valid case's dialect written
as version 3, its source bound, and its preparation is of version 3 (§9.1). `unbound-bound-at-import`
is a dialect published with its one source unbound (§4.4): `unbound.json` names the catalog platform
and operation, the shape `http` and the record `adapter-http`, and no input profile; `binding.json`
binds it to the profile `intake`; and `mapping.json` is the bound dialect the Runner made of them,
whose digest the preparation carries as `mappingDigest`. A verifier is given `unbound.json` and
`binding.json`, makes the bound dialect, and reads that. No vector holds an `operation` of shape
`airbyte`, nor a kind of version 3 (§4.3): those are defined, and not claimable. The companion
document was amended with their staging (RFC 0018, the amendment that read version 3), so that its
text says what these two hold.

One vector is answered otherwise than `verify-run` answers it. `disposition-differs-from-audit`
alters the run's retained result, which is the Runner's export and no part of a preparation or a
record: its preparation and its record are the valid case's, and the class reads them so. The
comparison of an export's result with its record is `verify-run`'s. For every vector with a
reading, the reading's `targetsByClass`, `unsignedParameters` and `unsignedFreshness` are the
members of that name in `verify-run`'s report, and its facts and evidence-availability documents
are the export's `run.input.facts` and `run.input.evidence`.

## How they are checked

[`tools/dialect_verify.py`](../../tools/dialect_verify.py) is a preparation verifier written from
the companion document's text (RFC 0018, Evidence), and the repository's tests run it over every
vector. They hold:

- every file under `vectors/` to the SHA-256 the Runner's manifest gives it, every file to a
  vector of that manifest or to the Runner's README and manifest, and those two to the SHA-256
  this repository's manifest records, so a vector added, removed or changed by a byte fails;
- each vector's recomputed preparation to `preparation.json`, byte for byte, and its digest to
  `preparation.sha256`;
- the bound dialect made of `unbound.json` and `binding.json` to `mapping.json`, and `binding.json` to
  the vector the Runner's manifest marks as bound at import;
- each vector's answer to the row of this repository's manifest, and each reading's members to the
  Runner's report and export, as above;
- that a verifier which writes `-0` as `0` fails `numeric-spellings`, and one which writes `&`,
  `<` and `>` as they are fails `escaped-strings`; and
- this README's count to the manifest.

To run a vector by hand:

```text
python tools/dialect_verify.py --dialect mapping.json --case case.json --acquisitions sources.json \
    --profiles profiles.json --preparation <run.input.preparation> --record <the record line> \
    [--require-binding]
```

For `unbound-bound-at-import`, `--dialect unbound.json --binding binding.json`.

## How they land

RFC 0018 was accepted on 2026-10-15, and its text landed then as the companion document. The
vectors wait for the next `specVersion`, as the checkpoint witness vectors do. When it opens, this directory leaves
the site's and the release bundle's exclusions, the vectors join a corpus as the vectors of the
preparation-verifier class, normative for that class and for nothing else, and Core §1.1's list of
normative artifacts gains them.

# registry-v1.1.0

`registry-v1.1.0` is the second release of the registry companion: registry format `1.1.0`, at
status `released`. Format `1.1.0` is [`spec/registry.md`](../spec/registry.md) (its §§1 to 17,
unchanged) together with [`spec/registry-1.1.0.md`](../spec/registry-1.1.0.md): two files of one
companion, each with its own section numbers. It adds assembly of one registry from several
repositories, the assembled index, bounds a repository may only tighten, a lock that pins a
registry and what it depends on, and the signatures that vouch for a lock and for each
repository's part of it. It is tagged on the companion's own scoped route, beside Core and
independent of `specVersion` ([VERSIONING.md](../VERSIONING.md)). Tagged on
<!-- PLACEHOLDER(tag-date) -->.

- **Released, and not stable.** `spec/registry-1.1.0.md` is normative for the conformance classes
  of its §15 (the assembler, the index checker, the lock writer, the lock checker and the lock
  signature verifier), and for nothing else; `spec/registry.md` stays normative for the classes of
  its own §15. The stability promise of registry §13 starts at the first stable release, and the
  bar for that is two independently written readers agreeing on every row of a class (§15). The
  rows are held to a reader written from the text, `tools/registry_1_1_0_reader.py`, which gives
  every row its expected result. It is a test reader, written by a model from the drafting vendor:
  a same-vendor reader, not a cross-vendor claim.
- **What it publishes.** The release's own bundle, `judgment-pack-registry-1.1.0`, carries both
  texts; the closed schemas of the documents format `1.1.0` adds and of the definitions they share
  (`schema/registry/1.1.0/`, nine files); the code list (`conformance/registry/1.1.0/codes.json`, 53
  codes); the 162 hand-written, synthetic rows under `conformance/registry/1.1.0/` and their README;
  format `1.0.0`'s schemas, code list and rows, byte for byte as the record of `registry-v1.0.0`
  pins them, on which the rows of `1.1.0` build, and format `1.0.0`'s rows' README,
  `conformance/registry/README.md`, which now also names the rows of `1.1.0`; the checks that hold
  the rows to the texts and the schemas to the rows, the reader above with its check, the rows'
  generator, and the Ed25519 arithmetic they use; the records and companions the texts link (RFC
  0034 to RFC 0040, the dialect and the checkpoint witness statement); and these notes with the
  release record. No Core bundle carries the schemas, the code list or the rows.
- **What the record pins.** [`registry-v1.1.0.json`](registry-v1.1.0.json) names the format, the
  `$id` of each schema under `https://judgmentpack.org/schema/registry/1.1.0/`, and the SHA-256 of
  both texts, the rows' README, format `1.0.0`'s rows' README, every schema, the code list and every
  row file. The release builder admits the tag only when the tagged tree gives exactly that record;
  when `spec/registry-1.1.0.md`, the code list and the rows' manifest all say `released`; when
  neither text nor the rows' README still calls format `1.1.0` proposed, or calls the format, its
  rows or its lists a draft or unreleased; when no schema's title, description or comment calls the
  format draft or unreleased; and when the design records, RFCs 0039 and 0040, say Accepted. Format
  `1.0.0`'s schemas, code list and rows, which the bundle carries unchanged, are held to the record
  of `registry-v1.0.0`, which keeps its bytes: the builder refuses the tag when any of them differs
  from that record, or a file is added or missing. Of the files that record pins, `spec/registry.md`
  and `conformance/registry/README.md` have changed since, and this record pins them itself. A later
  release of format `1.1.0` names the same schemas with the same digests.
- **What the release changed.** The status sentence of `spec/registry-1.1.0.md`, its Status
  paragraphs and its §14, and the paragraph of `spec/registry.md`'s Status on format `1.1.0`, say
  released; the code list and the rows' manifest say `released`, and the manifest's label is the
  released one; each schema's title drops "DRAFT", and its description says it is released on
  `registry-v1.1.0` rather than staged and proposed. No rule, code, order or bound changes, and no
  section is renumbered.
- **The site** serves each schema of format `1.1.0` at its `$id`, byte for byte, beside those of
  format `1.0.0`, and serves no schema or row as a file. A URL served once keeps its bytes.
- **A claim** names its class, the exact release `registry-v1.1.0`, and its complete rows, which
  the record identifies by the digest of their manifest and of every row file (§15). Every class of
  `spec/registry-1.1.0.md` §15 has rows.

## Compatibility

- **Format `1.0.0` is unchanged.** No `1.0.0` selector, member, code, rule or row is removed or
  changes meaning, and every document of registry §2.1 keeps the selector `"1.0.0"`. The assembled
  registry is a `1.0.0` document. The new documents take the selector `"1.1.0"`, and a `1.0.0`
  reader refuses each by its selector (`spec/registry-1.1.0.md` §13).
- **Core is unchanged.** A registry is not a pack, no Core document carries a registry selector, and
  every pack Core accepts it still accepts, with the same results. No Core text, schema, corpus or
  bundle changes, and every Core tag keeps its bytes.

## Scope and review

Provenance is not trust: an index records what the caller says it read, and nothing in it says a
source was entitled to define its entries. A signature says who, not whether right: it is evidence
of an act by a key holder, not of a review (`spec/registry-1.1.0.md` §16). No claim follows about
the truth of a registry's values.

The design records, [RFC 0039](../rfcs/0039-federated-registry.md) and
[RFC 0040](../rfcs/0040-registry-locks-and-signatures.md), were accepted together by the maintainer
on 2026-11-18, and the text governs where they differ. They were reviewed together in one round,
with the different-vendor review of the interim review regime waived by the maintainer, as the
text's §17 records: a same-vendor review, not a cross-vendor claim. No independent
implementation evidence is claimed.

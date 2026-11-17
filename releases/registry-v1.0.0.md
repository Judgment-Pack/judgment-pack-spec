# registry-v1.0.0

`registry-v1.0.0` is the first release of the registry companion
([`spec/registry.md`](../spec/registry.md)): registry format `1.0.0`, at status `released`. It is
tagged on the companion's own scoped route, beside Core and independent of `specVersion`, as the
Policy companion's releases are ([VERSIONING.md](../VERSIONING.md)). Tagged on
<!-- PLACEHOLDER(tag-date) -->.

- **Released, and not stable.** The text is normative for the conformance classes of its §15, and
  for nothing else. The stability promise of its §13 starts at the first stable release, and the bar
  for that is two independently written readers agreeing on every row of a class (§15). One reader
  exists: the reference runtime (Go), which implements §§2 to 10, and §11's host and harness. No
  second, independently written reader, host or harness exists.
- **What it publishes.** The release's own bundle, `judgment-pack-registry-1.0.0`, carries the text;
  the closed schemas of its ten documents and of the definitions they share
  (`schema/registry/1.0.0/`, eleven files); the code list (`conformance/registry/1.0.0/codes.json`,
  115 codes); the 34 hand-written, synthetic rows under `conformance/registry/1.0.0/` and their
  README; the checks that hold the rows to the text and the schemas to the rows; the records the
  text links (RFC 0034 to RFC 0038, and the dialect companion); and these notes with the release
  record. No Core bundle carries the schemas, the code list or the rows.
- **What the record pins.** [`registry-v1.0.0.json`](registry-v1.0.0.json) names the format, the
  `$id` of each schema under `https://judgmentpack.org/schema/registry/1.0.0/`, and the SHA-256 of
  the text, the rows' README, every schema, the code list and every row file. The release builder
  admits the tag only when the tagged tree gives exactly that record, when the text, the code list
  and the rows' manifest all say `released`, and when no schema's title, description or comment
  calls the format draft or unreleased. A later release of format `1.0.0` names the same schemas
  with the same digests.
- **The site** serves each schema at its `$id`, byte for byte, and serves no schema or row as a
  file. A URL served once keeps its bytes.
- **A claim** names its class (registry reader, facts writer, emitter host or emitter harness), the
  exact release `registry-v1.0.0`, and its complete rows, which the record identifies by the digest
  of their manifest and of every row file (§15). The importer class (§9) has no rows yet: it is
  defined, and not claimable. The pack check (§10.5) is in no class.
- **Where the reference runtime differed.** The rows' README names two rows on which the reference
  runtime differed from the text when they were written, `kind-declarations` (§7.3) and
  `pattern-bounds` (§3.4). The text governs, and a reader is held to the rows.

## Compatibility

- **Core is unchanged.** A registry is not a pack, no Core document carries a registry selector, and
  every pack Core accepts it still accepts, with the same results. A facts document of §10 is an
  ordinary facts document to Core. No Core text, schema, corpus or bundle changes, and every Core
  tag keeps its bytes.
- **Readers and writers.** This is the format's first release; there is no earlier registry release
  to migrate from. Every document of the format requires its selector at exactly `"1.0.0"`, and a
  reader refuses any other.

## Scope and review

A valid registry authorizes nothing: owners are identifiers, not permissions, and an emitter is code
the repository chose to run, for which the host is not a sandbox (§16). No claim follows about the
truth of a registry's values or the fitness of an emitter's output.

The design records, [RFC 0034](../rfcs/0034-registry-profile.md) to
[RFC 0037](../rfcs/0037-generated-facts-contracts.md), were accepted on 2026-11-16 by the
maintainer on one review round by a model from the drafting vendor, with the different-vendor review
of the interim review regime waived, as each record's Acceptance section says. That is a same-vendor
review, not a cross-vendor claim. No independent implementation evidence is claimed.

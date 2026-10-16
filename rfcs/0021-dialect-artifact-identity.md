# RFC 0021: Named Dialect artifacts

- Status: Accepted
- Accepted: 2026-10-16 (effective upon merge of the adopting pull request)
- Type: Standards track, draft maturity
- Created: 2026-10-16
- Issue: [#180](https://github.com/Judgment-Pack/judgment-pack-spec/issues/180)

## Summary

Give a reusable input Dialect an independent `id` and three-component artifact `version`, and
select its document grammar through `formatVersion`. Keep integer formats and receipts intact.

## Problem

A recipe edit counter cannot identify a portable release. Replacing integer version 2 or 3 with
an artifact version conflates grammar with content and changes digests without specifying readers.
Jobs and catalogs need an immutable release identity while drafts and research records keep changing.

## Evidence

Desk's company-qualification flow edits a translation while jobs retain the previously reviewed
mapping. A healthcare procurement recipe needs the same lifecycle without company-specific fields.
Runner already freezes bound documents, and the two repository preparation readers distinguish
format 2 from 3. Runtime already provides exact shared version arithmetic. None establishes a
portable Dialect artifact identity today.

## Specification

Add §2.1 of [the Dialect companion](../spec/dialect.md#21-named-artifact-formats). Its exact
selectors are `2.0.0` and `3.0.0`. They retain both translation families and have new canonical
identities. The preparation formats stay integer 2 and 3. Document validation, publication admission,
installation binding and execution remain distinct checks.

## Alternatives

- No change leaves reusable identity in each product's private metadata.
- An extension or profile cannot add members to the closed document grammar or change its digest.
- A release envelope could retain the old document unchanged, but makes the identity indirect and
  requires every reference to distinguish envelope and content without giving authoring a root identity.
- Reusing the integer `version` or accepting string aliases silently changes historical identities.
- Product-only semantic versions do not make independently exchanged documents self-identifying.

## Compatibility

Old readers refuse new documents; writers discover exact supported selectors before emitting them.
Old integer documents and all recorded vectors remain byte-identical. Conversion is an explicit
new-artifact operation, never a receipt migration. New family-2 documents use the one-way encoding
rule already used by family 3; legacy empty root fields do not survive that explicit conversion.
Output and pack-free presets remain separate, proposed contracts; this amendment does not relabel them.

## Security and privacy

An id is bounded opaque data, not a URL to fetch. Identity is not authenticity or permission.
Catalogs reject identity reuse with different canonical content. Bound derivatives keep separate
provenance. A valid document cannot authorize acquisition, infer credentials, bypass review, or
silently upgrade an existing job. Strict JSON, integer canonicalization and byte bounds still apply.

## Conformance

Add staged positive, malformed, unsupported and binding tests to both repository readers. Exercise
both families, exact canonical digests, independent artifact versions, no coercion, leading-zero
refusals, changed identity, bound derivatives and historical vectors. These are research-preview
agreement tests, not a published preparation-verifier conformance claim.

## Implementation

Python and TypeScript read the new headers and retain the original document for canonicalization.
Runtime exposes format capabilities and authoritative checks; Runner keeps frozen named documents
and installation bindings. Desk reuses shared review/publication/version controls. These changes are
by one author with model assistance; two language implementations are not independent authorship.

## Unresolved questions

An output-side release and a pack-free preset need separately adopted contracts before sharing an
artifact identity. Research-source execution remains subject to the accepted source contract and
reader capabilities. This amendment does not implement a hosted registry or storage adapter.

# RFC 0001: Pack manifest

- Status: Draft
- Type: Standards-track (candidate profile)
- Created: 2026-07-24

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.

## Summary

A small, optional manifest that describes a Judgment Pack from the outside — its identity, the
decision it governs, its specification version, and integrity metadata — so that tools can index,
select, and verify a pack without parsing its full body.

## Problem

The [core specification](../spec/judgment-pack-core.md) defines a pack's internal document. It does
not define how a pack is described *to other tools*: how a catalog lists it, how a selector decides
it is relevant, or how a consumer verifies it received the intended bytes. Today each tool invents
its own metadata, which defeats the portability the format exists to provide.

## Evidence

Package ecosystems converged on external manifests for exactly this reason — an OCI image index, an
npm `package.json`, and a Terraform module's metadata all let a registry reason about an artifact
without executing it. Early authoring experiments repeatedly reconstruct the same fields (title,
decision question, version, checksum) ad hoc.

## Specification (sketch)

A manifest is a separate JSON document referencing one pack `(id, version)`. Candidate fields:

- `packId`, `packVersion`, `specVersion`;
- `decisionQuestion` (copied for discovery, not authoritative);
- `contentHash` (digest of the exact pack bytes — see *Digest* below);
- optional `keywords`, `domainHints`, `supersedes`.

The manifest is descriptive only. It never overrides the pack, and a consumer that disagrees with
the manifest trusts the pack body and the digest.

### Digest

`contentHash` is the string `sha256:` followed by the 64 lowercase hex characters of SHA-256 over
the exact pack bytes as retained or served. There is no canonicalization rule: no whitespace or
member-order normalization, no encoding repair, no semantic equivalence. Two byte-different packs
carry different digests even when every conforming evaluator maps them to identical dispositions —
semantic identity is not a manifest concept, and Core §8.3 already takes this position by making
the disposition byte-portable while leaving the pack's representation alone.

The algorithm prefix is the agility mechanism. A future algorithm arrives as a new prefix over the
same exact-bytes rule; an unprefixed value never exists, and a consumer must refuse an
unrecognized prefix rather than fall back. Digest comparison is exact string equality.

This answers the question this RFC previously left open ("which digest algorithm and
canonicalization rule?") the way every shipped producer already behaves: the reference runtime's
reviewed-set lock records `sha256:<hex>` over the exact bytes it decoded, the gateway's receipts
record `sha256:` plus 64 lowercase hex over retained artifact bytes, and the published
interoperability studies (014, 016–018) registered SHA-256 over exact retained bytes as an
expedient pending this rule. The expedient is now the rule. What this section does not supply is
interop evidence: the Implementation bar below — two independent implementations reaching the
same accept/reject offline — remains unmet. And it adds no identity notion to Core: §13's open
bullet (content identity, canonicalization, and signatures as Core concepts) stays open; the
manifest digest names bytes at the interchange layer, nothing more.

## Alternatives

- **No change** — every tool keeps private metadata; packs stay non-portable at the catalog layer.
- **Extension** — carry the fields inside the pack's `extensions`. Rejected as primary because
  discovery must not require parsing the whole body.
- **Profile** — ship the manifest as an optional profile once two implementations agree. Preferred.
- **Product-only** — leave manifests to each registry product. Viable, but forfeits interchange.

## Compatibility

Additive and optional. A pack without a manifest is still fully valid. No reader/writer/semantic
effect on the core document.

## Security and privacy

A manifest can misdescribe a pack; consumers must treat descriptive fields as untrusted hints and
rely on the digest for integrity. Copied decision text may leak intent in a catalog and should be
optional.

## Conformance

Positive: manifest resolves to an existing `(id, version)` with a matching digest. Negative:
digest mismatch; dangling reference; `specVersion` disagreement between manifest and pack.

## Implementation

Two independent implementations should be able to emit and verify a manifest offline and reach the
same accept/reject decision on the negative cases.

## Unresolved questions

- Is the manifest one-to-one with a pack, or can it describe a set?
- Does discovery ([RFC 0005](0005-pack-discovery.md)) consume manifests directly, or a derived
  index?

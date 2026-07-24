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
- `contentHash` (digest of the canonical pack bytes);
- optional `keywords`, `domainHints`, `supersedes`.

The manifest is descriptive only. It never overrides the pack, and a consumer that disagrees with
the manifest trusts the pack body and the digest.

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
- Which digest algorithm and canonicalization rule?
- Does discovery ([RFC 0005](0005-pack-discovery.md)) consume manifests directly, or a derived
  index?

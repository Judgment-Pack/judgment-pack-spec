# RFC 0005: Pack discovery

- Status: Draft
- Type: Standards-track (candidate profile) + product (service)
- Created: 2026-07-24

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.

## Summary

A portable *index format* for describing a collection of Judgment Packs so that tools can list,
search, and select packs across catalogs. This RFC standardizes the discovery format; it does not
standardize any hosted registry service.

## Problem

"How are packs discovered?" has no answer today — `registry` is mentioned nowhere as a defined
artifact. Without a shared index, a pack authored in one place cannot be found or selected by a tool
built elsewhere, which undercuts the reuse the format promises.

## Evidence

OCI registries, npm, and the Terraform registry each separate a *format* (an index/manifest schema)
from a *service* (a running, authenticated host). The format is what makes clients interoperable;
the service is a product. Discovery here needs the same split.

## Specification (sketch)

A discovery index enumerates entries, each referencing a pack manifest ([RFC 0001](0001-pack-manifest.md))
by `(id, version)` with digest, plus coarse selection metadata (decision question, domain hints). A
client can fetch the index, filter locally, and resolve the underlying pack by digest. The index is
data; how it is served, paginated, authenticated, or billed is out of scope.

## Alternatives

- **No change** — no cross-tool discovery; reuse stays local.
- **Manifest-only** — discover by crawling manifests; workable at small scale, but an index is
  needed for search.
- **Service-first** — define an API before a format; rejected, because it couples clients to one
  host.
- **Product-only for the service** — correct: the running registry is a product; only the index
  format is a candidate for the specification.

## Compatibility

Additive, optional profile built on [RFC 0001](0001-pack-manifest.md). No change to core packs.

## Security and privacy

Discovery indexes are an integrity and disclosure surface: entries must be verifiable by digest, and
publishing a pack's decision question to a public index may leak intent. Selection metadata is a
hint, never authorization to run a pack.

## Conformance

Positive: an index whose entries resolve to existing manifests with matching digests. Negative:
dangling entry; digest mismatch; malformed selection metadata.

## Implementation

Two clients should filter the same index to the same candidate set and resolve the same bytes for a
chosen entry.

## Unresolved questions

- Index granularity: one index per catalog, or federated indexes?
- How does discovery relate to a selection interface ([RFC 0004](0004-planner-interface.md)) without
  pulling product context into the format?
- Signing and provenance: in this format, or deferred to a separate integrity RFC?

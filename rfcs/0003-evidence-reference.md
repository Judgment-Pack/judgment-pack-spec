# RFC 0003: Evidence reference

- Status: Draft
- Type: Standards-track (candidate profile)
- Created: 2026-07-24

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.

## Summary

A portable convention for how a pack *names* the evidence it needs, so that different runtimes can
bind the same evidence requirement to different sources (SQL, an API, a document store, a knowledge
graph) without changing the pack. This RFC standardizes the reference contract, not any connector.

## Problem

The [core specification](../spec/judgment-pack-core.md) defines evidence *requirements* and
*sources* inside a pack, but the pack deliberately says *what it needs*, never *how to fetch it*.
The moment two runtimes try to supply evidence to the same pack, they need a shared way to identify
"the evidence this requirement refers to." Absent a convention, bindings are private and packs stop
being portable across runtimes.

Note the scope boundary: an evidence *integration layer* that connects to real systems is a runtime
or product concern and is explicitly out of scope for the specification (see the
[non-goals](../docs/non-goals.md)). Only the reference/adapter contract is a candidate for
standardization.

## Evidence

Every experiment that runs a pack against real data reinvents a mapping from "requirement id" to "a
place to get the value," and those mappings do not transfer between tools.

## Specification (sketch)

A stable evidence-reference shape — a requirement identifier plus an optional typed selector — that
a runtime's adapter resolves. The specification would define the *reference* and the expectations on
a resolved value (type, presence, unknown), and would say nothing about transport, authentication,
caching, or ranking.

## Alternatives

- **No change** — bindings stay private per runtime.
- **Standardize connectors** — rejected; transport and auth are product concerns and would bloat the
  core.
- **Profile** — ship the reference contract as an optional profile. Preferred.

## Compatibility

Additive; refines how existing evidence requirements are referenced. No change to the meaning of a
requirement's presence or absence.

## Security and privacy

Evidence references must not smuggle executable fetch instructions (consistent with "no hidden
executable semantics"). A reference is an identifier, not a URL to auto-dereference.

## Conformance

Positive: a runtime binds a reference to a source and the pack resolves as declared. Negative: a
reference that names no declared requirement; a resolved value of the wrong type.

## Implementation

Two runtimes with different back ends should resolve the same references to the same
presence/type/unknown outcomes for a shared fixture.

## Unresolved questions

- How much type information belongs in the reference versus the requirement?
- Is "unknown" for a reference distinguishable from "absent"?
- Does this interact with [RFC 0002](0002-judgment-graph.md) when one pack's outcome is another's
  evidence?

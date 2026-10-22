# RFC 0026: Document ceiling profiles

- Status: Accepted
- Type: Standards track, draft maturity
- Decision: Issue #232, maintainer decision of 2026-10-22

## Summary

A document declares `profile`, defaulting to `base`; `extended` doubles the existing
ceilings enumerated in Core §4.1. This records the accepted issue design, not release readiness.

## Problem

Installation-only overrides make identical documents silently admissible at different ceilings.
The declared choice must travel with the bytes and be discoverable through reader capabilities.

## Evidence

Core escalation routes (#219) have an eight-route bound; Policy informational sources have a
sixteen-source bound. Workflow already declares limits below fixed ceilings. Dialect has fixed
resource bounds. Core defines no outcome, rule or reference ceiling: this change invents none.
The synthetic vectors demonstrate structural admission, not runtime or independent agreement.

## Specification

Core §4.1 owns the complete ceiling table, declaration, identity and capability rules. Companions
reference it. A known unsupported profile yields one `profile-unsupported` diagnostic naming that
profile before other documents' byte-bound checks, reference loading, acquisition or
evaluation; only the bounded declaration scan precedes negotiation. A supporting reader
then applies the selected ceilings. An unknown profile is structural.
The declaration is retained in bytes and digests. Profiles change ceilings only, never semantics,
minima, closed vocabularies or canonical numeric domains. Workflow keeps its `limits` member.

## Alternatives

No change leaves installation differences hidden. Extensions would introduce a second declaration
mechanism. Product-only overrides cannot give documents portable identities and admission rules.
The accepted profile approach names specification-versioned ceilings instead of arbitrary numbers.

## Compatibility

Absent declarations retain base behavior. Explicit declarations change exact bytes, even `base`.
Old schemas may reject the new member. Published schemas retain base maxima; profile-aware readers
apply the enumerated extended maxima without relaxing other constraints. No frozen Core consumer
schema, release pin, specification version or released evaluation corpus is rewritten. The Policy
reader retains its pinned Core consumer contract. Workflow remains a proposed companion without
an implementation. The released Policy 1.0.0 draft does not carry `profile`; its table ceilings apply
from the next companion version, which adopts the member. The Dialect readers support
only base; the Core
structural profile reference admits both. No claim of extended companion implementation is made.

## Security and privacy

Larger ceilings increase resource demand. Readers must refuse unsupported profiles before side
effects, never truncate, and never use deployment settings to grant undeclared limits. Refusal
messages echo only known profile names. All examples are synthetic; ceilings grant no authority.

## Conformance

`conformance/evaluation/staged/profiles.json` supplies hand-written boundary and capability vectors. Tests cover
implicit and explicit base, one-over-base refusal, extended admission and its own ceiling,
unsupported and unknown names, unchanged identity bytes, schema mutation sensitivity, and both
Dialect language readers' declaration checks. The frozen Policy schemas continue to reject the new member. Handoff boundaries are
covered at 8/9 and 16/17 routes; both effective schemas are compared with the normative
table. Canonical digests distinguish absent, base and extended declarations. The oversized
case probe checks envelope admission only: its minimal profile declaration is not a
complete Dialect document, and full extended verification is not claimed.

## Implementation

The Python Core structural reference adapts only route ceilings in a fresh schema. Independent
implementations can select precompiled validators per profile or use conditional schemas at the
root. Existing schema style permits conditionals, but this change leaves base schemas directly
usable and performs extended validation in the profile-aware reader. Python and TypeScript Dialect
readers implement base-only negotiation; no independent extended reader agreement is claimed.

## Unresolved questions

Extended companion implementations and release publication remain separate work. Existing RFCs'
companion mirrors change with the proposal; the repository's different-vendor adversarial review
and maintainer disposition remain release/review requirements, not evidence supplied by this session.

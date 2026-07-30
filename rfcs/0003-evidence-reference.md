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

A predeclared research line then built and tested the reference-adjacent layers
([ADR-0002](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/blob/main/docs/adr/0002-trustworthy-input-acquisition-research-line.md),
2026-07, the trustworthy-input-acquisition line — a fixed decomposition and build order, not a
Study-style preregistration). Its middle piece is one part this RFC's sketch names but leaves open —
turning "the bytes a source returned into a resolved value" into **data**: a portable *derivation
rule* ([`derivation-rule/`](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/derivation-rule))
that maps an acquired artifact and caller-supplied parameters to a claim — a typed facts payload,
plus a tri-state evidence *availability* (`present`/`absent`/`unknown`), plus an acquisition status —
by declared typed checks rather than hand-written code. It carries no transport, no connector, and no
fetch instruction; it is applied to bytes already in hand, so it sits inside this RFC's scope
boundary and gives one half of the "resolved value" contract a concrete, inspectable shape.

The bearing on this RFC is narrower than the *Implementation* section's bar and should not be
mistaken for it: that bar asks two *runtimes with different back ends* to resolve the same
*references* to the same outcomes, and nothing here resolves a reference, exercises an adapter, or
binds a source — so the two-back-end bar stays **unmet**. What was tested is the derivation
*sub-contract* — the bytes→value step downstream of resolution. The line built two implementations
of it, a Python reference and a **clean-room second implementation in Go** written from the rule's
specification alone by an author with no access to the first, and they agree on all twenty-one cases
of a shared corpus — byte-identical claims on the sixteen that derive a value and matching refusal on
the five that reject — thirteen of them reproducing an earlier study's hand-written derivation, the
other eight adversarial. More useful than the agreement itself: the agreement test *found* real
ambiguities a single implementation had hidden — whether a non-integer number literal in a rule is
rejected, whether `2026-02-30` has an instant, how a request is framed — each of which had to be
pinned before the two agreed. That is evidence that the bytes→value contract is *specifiable to the
point of byte-agreement on the tested surface* and that its precision is the kind independent
implementations expose. The bound is sharper here than for a corpus: both implementations were built
by this project, so this is evidence of encodability and cross-implementation agreement on that
surface, not the independent third-party validation the evidence bar ultimately requires, and not a
claim that the contract is complete.

Beside the derivation rule, the line built the two layers this RFC deliberately leaves to products —
an attestation component that content-addresses an acquired result and issues an HMAC receipt over
its canonical form under a *caller-configured attestation authority*, and an admission gate that
makes a pack's facts be *exactly* the derivation over those attested bytes. One bearing on the
reference contract: a resolved value can carry byte-lineage back to an *attestation trust root*
— that the admitted bytes are the ones that trust root attested, unaltered — *without the reference
becoming a fetch instruction*; the reference stays a pure identifier, and the attestation and
derivation happen in the resolving layer, around the pack, never inside it. The bounds are load-
bearing: this proves lineage to the trust root over a canonical result, **not** that a genuine named
source returned those bytes (the recorded server identity is an unauthenticated assertion), and an
HMAC receipt is a keyed integrity proof, not the asymmetric signature Core §13's "signatures" would
contemplate. It is one worked, product-side, single-author example bearing on the "content identity,
canonicalization, and signatures" §13 defers; it changes nothing normative.

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

Each stays open. The derivation-rule prototype (see Evidence) takes a position on the first three,
recorded as prototype positions — with testing limited as noted under each — for this RFC to weigh
rather than as resolutions.

- **How much type information belongs in the reference versus the requirement?** *Prototype
  position: neither — the type checks live in the resolving derivation, and the reference stays a
  pure identifier.* The rule declares typed checks (a decimal-string test, a boolean test, a
  freshness window) that run over the acquired bytes and produce the resolved value; the reference
  names the requirement and nothing more, keeping this RFC's "a reference is an identifier, not a
  URL to auto-dereference" principle intact while making the typing portable and cross-checkable
  rather than baked into a runtime. The requirement's optional `kind` (Core §6.2) stays descriptive.
- **Is "unknown" for a reference distinguishable from "absent"?** *Prototype position: on the
  bytes-in-hand step, yes — the distinction is drawn in the resolving layer from an acquired
  artifact, not carried by the reference.* In the one rule tested, an artifact that reports a
  completed check with no record derives `absent`, while one that reports a malformed or stale record
  derives `unknown`; the two implementations agree on which artifact yields which. Two limits keep
  this from being a general rule: a *transport* failure that yields no artifact at all cannot be
  classified by a step that runs on bytes already in hand — distinguishing "could not reach the
  source" is the resolving layer's job *before* derivation — and the derivation reads caller-supplied
  parameters (a subject, an as-of time) as well as bytes. So the position is that the tri-state is
  drawable and reproducible for the acquired-artifact case, which is the case this rule covers.
- **Does this interact with [RFC 0002](0002-judgment-graph.md) when one pack's outcome is another's
  evidence?** *Proposed alignment between two prototypes, not a tested result.* No derivation-rule
  corpus case consumes an upstream disposition, and RFC 0002 keeps its own outcome-as-evidence edge
  semantics an explicit prototype position, not settled. The alignment offered for both RFCs to weigh
  is structural: an upstream pack's outcome consumed as a downstream pack's evidence resembles a
  bytes-in-hand resolved value whose derivation is nearly the identity, so the between-packs edge and
  the between-systems reference could share one tri-state availability definition at two scales,
  defined once and consumed by RFC 0002. Study 004 measured, for one corpus, that the *between-packs*
  cross-decision seam was effect/entitlement-shaped rather than dataflow-shaped; that the
  *between-systems* seam this RFC serves is the dataflow one is an inference the runtime's demo
  illustrates, not something Study 004 measured — that study excluded the between-systems seam by
  construction and notes it might appear in a different corpus.

The candidate this leaves for the RFC to weigh, not a rule it sets: define a resolved evidence value
as a **typed payload together with a `present`/`absent`/`unknown` availability state** — the
availability being what Core §8.2 already carries, the typed payload the part §13 leaves open —
produced by a portable, independently-implementable derivation over bytes the resolving layer already
holds, and keep the reference a bare identifier. Byte-lineage back to an attestation trust root would
then be an optional product-side property (Core §13), never a member of the reference.

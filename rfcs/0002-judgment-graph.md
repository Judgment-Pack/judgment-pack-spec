# RFC 0002: Judgment Graph composition

- Status: Draft
- Type: Standards-track (candidate profile)
- Created: 2026-07-24

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.

## Summary

A portable *format* for composing several Judgment Packs into a larger decision structure — a
Judgment Graph — in which one pack's decision can depend on another's. This RFC concerns the
interchange format only, not the algorithm that evaluates it.

## Problem

A single pack declares a single decision. Real decisions compose: an invoice approval may depend on
a supplier-standing decision, which may depend on a sanctions decision. Nothing in the
[core specification](../spec/judgment-pack-core.md) describes how packs reference one another, so
every integrator wires composition privately and non-portably.

## Evidence

Decision Model and Notation (DMN) needed a Decision Requirements Graph precisely because real models
are graphs of decisions, not single tables — and defining that graph's semantics took the standard
years. The same pressure appears here as soon as more than one pack is authored for one workflow.
The repository's own [`data-request-intake-triage`](../examples/data-request-intake-triage.json)
example already shows the seam: its summarized completeness and appropriateness facts are the
verdicts of an upstream assessment that would naturally be its own pack feeding this one — an edge
this format would make first-class instead of an out-of-band convention.

The escape census ([Study 003](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/003-escape-census),
2026-07) supplies this RFC's first measured evidence from third-party policy text: all twelve
separable decisions of two public policies, written by a third party for a purpose unrelated to
JPS, encoded under an information barrier. Finding 4 reports a *forward entitlements /
cross-decision references* residue family — "insurance enables full refund if…" was left out of the
Book-flight pack because it belongs to the Cancel decision, and one pack cannot reference another's
outcome — which is exactly the edge this format proposes. The encoding runs were isolated and
barred from specification RFCs, so the observation was not prompted by this proposal; the study
itself was conducted by this project, so this is internally produced corpus evidence, not
independent third-party validation.

The reference runtime carries a working prototype of this composition
([ADR-0015](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/a3058cbadee993306d2f8bc9184cd6d9191a9143/docs/adr/0015-experimental-graph-surface.md),
2026-07-29, behind an explicitly experimental surface; at the time of writing it lives on the
runtime's `jgraph` branch, unmerged, and the link pins the reviewed commit): a closed-schema
document of nodes, edges, and one declared result node, where a node references a pack, an edge
feeds one node's outcome downstream as a fact at an RFC 6901 pointer and/or as a tri-state
evidence contribution, and every node evaluates through the runtime's unchanged Core §§7–8
evaluator in deterministic topological order. It is one implementation, built by this project's
maintainer — evidence that the sketch is encodable and that its open questions have workable
answers, not the independent second implementation the evidence bar requires. Its adversarial
review contributed one observation worth recording as design evidence in its own right: a
prototype guard that refused caller-supplied values at a fed pointer only when the upstream
produced an outcome silently let the caller's value stand in for the outcome an unresolved
upstream never produced — the exact smuggling this format exists to remove, reintroduced by an
evaluation-dependent rule. The candidate invariant this surfaced, for this RFC to weigh rather
than a rule it sets: collision rules that depend on evaluation results reintroduce the smuggling,
and the prototype now decides every collision from the declared edges and the supplied inputs
alone.

## Specification (sketch)

A graph document references packs by `(id, version)` and declares directed dependencies between
their decisions. The format would need to express, at minimum: nodes (pack references), edges
(which decision feeds which), and how one decision's outcome is exposed as another's evidence. The
format is declarative and carries no evaluation semantics itself.

## Alternatives

- **No change** — composition stays a private, per-integrator concern.
- **Extension** — express edges in `extensions`; rejected because cross-pack references must be
  first-class and validated.
- **One giant pack** — collapse the graph into a single document; rejected because it destroys the
  atomic, independently testable and versionable unit the format is built on.
- **Product-only** — leave graphs to runtimes; viable for evaluation, but the *format* is a genuine
  interchange need.

## Compatibility

Would be a new optional profile. Core packs are unchanged and remain valid standalone.

## Security and privacy

Cross-pack references introduce supply-chain and confused-deputy risks: a graph could pull in an
unexpected pack version, or expose one decision's evidence to another. Version pinning and explicit
evidence exposure are required, not implicit.

## Conformance

Positive: a graph whose references all resolve and whose edges form a DAG. Negative: dangling pack
reference; version drift; a cycle where the format forbids one.

## Implementation

Two implementations should agree on whether a given graph document is well-formed and acyclic,
independent of any evaluator. One implementation exists — the reference runtime's experimental
surface (ADR-0015, on its unmerged `jgraph` branch at the time of writing) — and, sharing an
author with this RFC, counts toward encodability and nothing else.

## Unresolved questions

Each question stays open. The runtime prototype (see Evidence) takes a position on the first four,
recorded here as one implementation's tested answers rather than as resolutions; the positions are
encoded as that surface's tests, so a better answer has a concrete artifact to refute.

- **Ordering and conflict** — when two packs produce conflicting outcomes for a shared question,
  what does the format say (if anything) versus the evaluator? *Prototype position: refuse, never
  merge.* Deterministic topological order with node ids breaking ties; two edges feeding one
  node's same or overlapping fact pointer (compared on decoded RFC 6901 tokens, so two spellings
  of one path cannot hide the collision) or the same evidence requirement are validation errors;
  a fact feed colliding with caller-supplied inputs is refused before any node evaluates —
  unconditionally, for the reason recorded under Evidence — and an evidence feed colliding with
  the caller's evidence document is refused before its target node evaluates, equally regardless
  of what any upstream produced.
- **Shared namespace** — do packs in a graph share a fact/evidence namespace, or is each isolated
  with explicit mapping? *Prototype position: isolated with explicit mapping.* Nothing is shared;
  the only values that cross a node boundary are the ones an edge explicitly places.
- **Cycles** — are cyclic dependencies always invalid, or valid with a declared fixpoint rule?
  *Prototype position: always invalid*, with cycle membership reported by strongly connected
  components so a node merely blocked behind a cycle is never named as part of one.
- **Partial failure** — how is an unresolved upstream decision represented downstream? The portable
  disposition of Core §8.3, landed by [RFC 0006](0006-evaluator-conformance.md) in `0.2.0-draft`, is
  the candidate representation; the edge semantics stay this RFC's to settle. *Prototype position:
  an upstream that produced no outcome injects no fact — the pointer is simply absent, which §7
  already reads as unknown — and an evidence feed contributes a declared tri-state (unknown by
  default, absent by declaration), so an unresolved upstream reaches a downstream pack only
  through that pack's own declared semantics: its unknown handling for the default, its
  required-evidence rule when the feed declares absence. Every requested handoff surfaces beside
  the composite. Evaluation errors stay errors: a refused node refuses the whole run with its
  §8.4 class intact, and no partial composite exists.*
- **Composite result** — is the aggregated result a portable artifact (a spec concern) or a runtime
  output? This is the hardest question and is deliberately unresolved. The prototype hedges it
  knowingly: its composite is an envelope — the per-node §8.3 dispositions side by side, the
  declared result node's echoed as a headline — labeled in band as a runtime convention, carrying
  what a portable artifact would need while claiming to be none.

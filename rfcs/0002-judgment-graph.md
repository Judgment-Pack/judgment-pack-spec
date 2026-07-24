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
independent of any evaluator.

## Unresolved questions

- **Ordering and conflict** — when two packs produce conflicting outcomes for a shared question,
  what does the format say (if anything) versus the evaluator?
- **Shared namespace** — do packs in a graph share a fact/evidence namespace, or is each isolated
  with explicit mapping?
- **Cycles** — are cyclic dependencies always invalid, or valid with a declared fixpoint rule?
- **Partial failure** — how is an unresolved upstream decision represented downstream?
- **Composite result** — is the aggregated result a portable artifact (a spec concern) or a runtime
  output? This is the hardest question and is deliberately unresolved.

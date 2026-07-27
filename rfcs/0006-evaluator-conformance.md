# RFC 0006: Evaluator conformance

- Status: Draft
- Type: Standards-track (candidate Core amendment or profile)
- Created: 2026-07-27

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar. Core `0.1.0-draft` forbids
> evaluator-conformance claims, and nothing in this RFC weakens that prohibition before a later
> draft ships the class it proposes.

## Summary

Propose that a later draft of the [core specification](../spec/judgment-pack-core.md) define a
normative *evaluator* conformance class: portable semantics for applying a pack to runtime facts
and evidence, and a portable *disposition* that two independent evaluators must produce
identically from the same inputs. The raw material is the informative §§7–8; promote them, close
their portability gaps, and test with an evaluation corpus beside the validation corpus.

## Problem

Core `0.1.0-draft` defines document conformance only; §3.4 says a tool "MUST NOT claim evaluator
conformance under `0.1.0-draft`, even if it implements the experiments in §§7–8." Two runtimes
can therefore read the same pack and facts, both behave defensibly, and produce different results
— neither wrong, because there is no normative text to be wrong against. Affected: teams
comparing evaluators, auditors replaying a decision, integrators exchanging decision records.

## Evidence

In a working session — not yet a committed artifact — three readers walked eight input instances
for [`data-request-intake-triage`](../examples/data-request-intake-triage.json) through §§7–8.
Six were unanimous; two diverged: §8 step 2's binary "is absent" collides with §7.5's
three-valued presence, permitting reason `unknown` or `missing-required-evidence` from the same
missing-evidence input; and `not-applicable` proved to be simultaneously a result kind and a
reason — §8 mandates both at once, so a reporting layer that flattens to one field must invent a
projection the spec does not define. The exercise is unrecorded, so weight these claims
accordingly; committing the instances and divergence writeups as non-normative draft fixtures is
a prerequisite for review.

## Specification (sketch)

- **Inputs** — a semantically conformant pack; one JSON facts document (`fact.path` as an
  RFC 6901 pointer); an evidence-availability input making §7.5's three-valued presence
  derivable.
- **Condition semantics** — §§7.1–7.4 normative: three-valued logic, type-preserving equality,
  unresolved pointers yield `unknown`.
- **Decimal ordering** — by mathematical value of the §2.2 grammar; units and date/time stay
  out.
- **Resolution** — §8 normative, its required-evidence check restated in three-valued terms;
  conflict stays `unresolved`, never tie-broken.
- **Disposition** — result kind (`outcome`, `not-applicable`, `unresolved`), a reason set, a
  separate handoff axis; escalation is not a result kind.
- **Boundaries** — unsupported required extensions are refused; resource exhaustion fails
  explicitly.

Product-only, now and later: fact acquisition, evidence collection, handoff delivery,
authorization, and *when* to evaluate.

## Alternatives

- **No change** — rejected; identical inputs already yield different reason sets across careful
  readers.
- **Extension** — §9 forbids only an *optional* extension from changing Core semantics, but
  evaluation semantics over Core's own rules, conditions, and outcomes govern how every pack is
  read; a required extension would fork the ecosystem pack-by-pack and cannot amend §3.4.
  Rejected.
- **Result format only** — rejected; evaluators would emit well-formed but disagreeing records.
- **Product-only** — viable for engines, but the result and its semantics are a genuine
  interchange need.
- **Core versus profile** — both remain live; see unresolved questions.

## Compatibility

Document conformance is untouched; every existing pack remains valid. The later draft would amend
the Status paragraph and §3.4 and re-title §§7–8 out of "(informative)" — a labeled breaking
change permitted during `0.x` per RFC 0000. Acceptance changes nothing by itself: §3.4's
prohibition holds until the class and its corpus ship, and claims against `0.1.0-draft` remain
forbidden permanently.

## Security and privacy

Runtime facts are untrusted; the three-valued semantics is a safety property — hostile or missing
data degrades to `unknown`, never silently to `false` or an outcome. A conformance claim will be
misread as proof decisions are correct or authorized; the §3.5 non-claims must extend to the
class. Dispositions leak rule and evidence-requirement ids across trust boundaries. Silent
truncation forges a disposition; limit exhaustion must fail explicitly.

## Conformance

An evaluation corpus mirroring the [validation corpus](../conformance/README.md), a fourth layer
under the stop-at-target-layer rule. The eight walked instances, once committed, seed the
positive, negative, and boundary rows; constructed cases beyond the walked set add
completeness-signal variants, hostile optional-extension content that must stay inert during
evaluation, and rule-order permutations that must not change any result.

## Implementation

No evaluator exists today in either repository: the Go reference runtime validates documents and
evaluates nothing, and the specification repository's Python tooling validates the corpus only.
The plausible pair, both future work: an experimental evaluator added to the Go runtime, labeled
per §3.4 and claiming no conformance; and the Python tooling extended to evaluate, or a third
party. Per RFC 0000, maintainers may request prototypes before disposition, and a stable
normative feature should not be accepted without evidence from two independent implementations.

## Unresolved questions

- **Core or profile** — this RFC proposes the class, not its packaging.
- **Evidence interchange** — does the evidence-availability input grow into
  [RFC 0003](0003-evidence-reference.md)'s evidence reference, or stay a minimal tri-state?
- **Beyond decimals** — units and date/time must be excluded explicitly, not
  `unknown`-by-accident.
- **Trace minimum** — must a trace surface a true rule that a forced outcome skipped?
- **Graph interaction** — [RFC 0002](0002-judgment-graph.md)'s composite result presupposes this
  disposition: its "partial failure" question is answered by `unresolved` propagating downstream,
  and its outcome-as-evidence edges must map a disposition into the evidence-availability input.
  [RFC 0004](0004-planner-interface.md)'s selection query probes the applicability gate, so
  `not-applicable` must stay a distinct result kind and never read as authorization.
- **Claim verification** — is passing the corpus self-asserted, or must results be published?

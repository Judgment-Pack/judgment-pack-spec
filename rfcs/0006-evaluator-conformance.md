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
their portability gaps — one of which this RFC resolves in its own sketch — and test with an
evaluation corpus beside the validation corpus.

## Problem

Core `0.1.0-draft` defines document conformance only; §3.4 says a tool "MUST NOT claim evaluator
conformance under `0.1.0-draft`, even if it implements the experiments in §§7–8." Two runtimes
can therefore read the same pack and facts, both behave defensibly, and produce different results
— neither wrong, because there is no normative text to be wrong against. Affected: teams
comparing evaluators, auditors replaying a decision, integrators exchanging decision records.

## Evidence

Three readers independently walked input instances for
[`data-request-intake-triage`](../examples/data-request-intake-triage.json) through §§7–8; an
adversarial review then reconstructed and re-walked the set independently (recorded on this RFC's
pull request). The instances, inputs, and expected results are committed in the
[appendix](#appendix-walked-instances-non-normative) below. Two findings survived both passes:

1. **One genuine semantic divergence.** §8 step 2's binary test — "record
   `missing-required-evidence` if any required evidence is absent" — does not define "absent" in
   terms of §7.5's three-valued presence, and §7.5 makes presence `false` only "when a complete
   evidence manifest is available and associates no item" while defining no manifest interchange
   form. For appendix instance 7, careful readers legitimately produce either
   `unresolved`/`{missing-required-evidence}` or `unresolved`/`{unknown}` from the same input,
   with different termination points. The sketch below resolves this.
2. **One lossy-reporting finding, not a semantic divergence.** §8 defines "a `not-applicable`
   result carrying reason `not-applicable`" — the result kind and the reason are both mandated,
   so an evaluator has exactly one correct result (appendix instance 1). What the spec does not
   define is a serialized result envelope, so a reporter that flattens kind and reason into one
   field invents a projection. This motivates the portable disposition; it is not evidence that
   careful evaluators disagree.

## Specification (sketch)

- **Inputs** — a semantically conformant pack; one JSON facts document (`fact.path` as an
  RFC 6901 pointer); an evidence-availability document; the evaluator's supported-extension set.
- **Evidence availability** — one JSON object keyed by declared `evidenceRequirements[].id`,
  each value `present`, `absent`, or `unknown`; an omitted key means `unknown`; a duplicate or
  undeclared key is an input error. `present`/`absent`/`unknown` map to §7.5's
  true/false/unknown, replacing the undefined evidence manifest with a portable tri-state.
- **Condition semantics** — the §7 preamble (`literal`) and §§7.1–7.5 become normative:
  three-valued logic, type-preserving equality, unresolved pointers yield `unknown`.
- **Decimal ordering** — an ordered comparison is defined iff both values are JSON strings
  conforming to the §2.2 decimal grammar, compared by mathematical value; any other value —
  including a JSON number — yields `unknown`. Units and date/time stay out.
- **Resolution** — §8 becomes normative with its step 2 restated in §7.5's terms: record
  `missing-required-evidence` iff any required requirement's presence is **false**; record
  `unknown` iff any required requirement's presence is **unknown** and none is false. Either
  reason blocks outcomes and the fallback and yields `unresolved` after exception inspection, per
  §8's existing order. Conflict stays `unresolved`, never tie-broken. The §8 step order is
  contractual only where it affects the disposition; it mandates no implementation algorithm.
- **Disposition** — required member `kind` ∈ {`outcome`, `not-applicable`, `unresolved`};
  `outcomeId` required iff `kind` = `outcome` and forbidden otherwise; `reasons` an unordered,
  deduplicated set (set equality; empty iff `kind` = `outcome`); `handoff` ∈ {`none`,
  `requested`} echoing the declared target when requested. Escalation is not a result kind.
- **Errors are not dispositions** — an unsupported required extension, a malformed input, or
  resource exhaustion produces an explicit evaluation error, never a disposition; corpus inputs
  must fit mandated minimum limits so identical corpus runs cannot diverge on limits.

Product-only, now and later: fact acquisition, evidence collection, handoff delivery,
authorization, and *when* to evaluate.

## Alternatives

- **No change** — viable while demand is speculative, but the committed appendix and the
  independently reproduced divergence on instance 7 are concrete disagreement between careful
  readings, and §7.5's undefined manifest guarantees it recurs in implementations.
- **Result format only** — standardize the disposition envelope without the semantics. Viable
  and architecture-aligned (a format in the specification, engines in runtimes), and the fallback
  position if semantics stall — but evaluators would emit well-formed, comparable, *disagreeing*
  records; instance 7 would simply serialize its divergence.
- **Evaluation profile** — a separately named, opt-in profile defining the class outside Core.
  Viable; §9 forbids only *optional* extensions from changing Core semantics, and a profile is
  how Core-versus-profile (unresolved below) would land if Core amendment proves too heavy.
- **Product-only** — correct for engines, but the result and its semantics are a genuine
  interchange need.

## Compatibility

Document conformance is untouched; every existing pack remains valid against `0.1.0-draft`.
Defining the class touches more than §§7–8: the Purpose and §3 openings, §3.4, §3.5's
runtime-correctness non-claim, §§6.5–6.6's "informative" cross-references, §13, and the exact
`specVersion`, schema, and corpus metadata must change together in the later draft — a labeled
`0.x` breaking change per RFC 0000. Migration: a pack needs no edits, but evaluator-conformance
claims attach only to the later exact `specVersion`; nothing is acquired automatically, and
claims against `0.1.0-draft` remain forbidden permanently.

## Security and privacy

Runtime facts and evidence inputs are untrusted. The three-valued semantics makes missing-data
handling *deterministic and author-controlled*, not safe by default: known-absent evidence is
`false` under the tri-state input, `onUnknown: ignore` deliberately lets resolution continue, and
a strong `all`/`any` can decide despite an `unknown` child. The portable claim is that every
evaluator degrades the same way — the pack's declared `onUnknown` policy, not an implementation's
guess, decides. A conformance claim will be misread as proof decisions are correct or authorized;
the §3.5 truth, authenticity, authority, and safety non-claims extend to the class unchanged,
while §3.5's "a particular runtime applied the pack correctly" bullet must be rewritten — this
class makes exactly that limited claim and no other. Dispositions leak rule and
evidence-requirement ids across trust boundaries. Silent truncation forges a disposition; limit
exhaustion must be an explicit error.

## Conformance

An evaluation corpus beside the [validation corpus](../conformance/README.md), with its own case
carrier: pack reference, facts document, evidence-availability document, supported-extension
set, and expected disposition (or expected error). The appendix instances seed the first rows —
instance 7's two variants pin the semantics this RFC chooses — for example:

> facts: `type=data-access, completeness=complete, appropriateness=pass, embargo=false`;
> evidence: `intake-form: present, sponsor-endorsement: absent` → expected
> `{kind: unresolved, reasons: [missing-required-evidence], handoff: requested}`.

Constructed cases add hostile optional-extension content that must stay inert during evaluation,
rule-order permutations that must not change any result, and error rows (unsupported required
extension; undeclared evidence key).

## Implementation

The first implementation exists: the Go reference runtime implements this RFC's pinned semantics
as `judgment-pack experimental evaluate` and the `experimental_evaluate` MCP tool (its ADR-0007) —
unmistakably labeled, claiming no conformance, and outside the default validation path, per the
pre-stated guardrails in [tooling-architecture](../docs/tooling-architecture.md). The nine
appendix instances run as its acceptance tests and reproduce identically over both of its
surfaces. The specification repository still owns no executable — the contract and corpus belong
here, engines do not.

Implementation experience recorded from that first implementation:

- The restated step 2 was implementable exactly as written; instances 7a and 7b are
  deterministic in practice.
- **Number representability is a real gap:** a syntactically valid JSON number can exceed an
  exact-arithmetic implementation's range (an extreme exponent), making equality undeterminable.
  The implementation maps this to §7.4's "incomparable values produce `unknown`" — never a silent
  false — but the later draft should state representability explicitly and the corpus should
  carry a row for it.
- §8.1's direct exception escalation with no `escalation` object was implemented as a requested
  handoff with no target; the later draft should confirm that shape.
- Honoring the declared `additionalProperties: false` required strict wire-argument decoding; an
  implementation that silently drops unknown argument keys produces a silently different
  disposition.

The second implementation exists — published, with its interpretation log, clean-room protocol,
and agreement harness, in
[judgment-pack-evaluator-experiments](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments):
a clean-room, stdlib-only Python evaluator written from this
RFC and the Core text alone — inside an information barrier (reference texts only; no access to
the first implementation, its repository, or its tools; the session log was audited afterwards),
by a different model family than the first implementation's authors, on the maintainer's
machine. Its interpretation log records twenty-one numbered decisions with the text each relied
on. Cross-implementation result: **13/13 semantic agreement** with the first implementation —
identical kind, outcome, reason set, and handoff state on the nine appendix instances plus three
probes (omitted evidence input, decimal-string ordering, missing exception fact).

The exercise also did the other half of its job — it found a genuine underdetermination:

- **The disposition's concrete serialization is not pinned.** "`handoff` ∈ {`none`, `requested`}
  echoing the declared target when requested" was read by the first implementation as a handoff
  *object* carrying a state and a target echo, and by the second as a bare two-value string with
  no target member — the second implementer explicitly declined to "invent an extra field" and
  flagged the target-echo phrase as under-specified. Semantic content agreed throughout; the
  JSON layout did not. The later draft must specify the disposition's exact members, not just
  their vocabulary.

Independence caveats, recorded rather than hidden: both implementations ultimately trace to the
same maintainer's direction, and this RFC's own implementation-experience notes (above) were part
of the second implementer's reference text — its no-destination handoff reading cites them, so
that particular convergence is corroborated rather than blind. Third-party implementation
experience remains the strongest evidence this process can add. Per RFC 0000, a stable normative
feature should not be accepted without evidence from two independent implementations; that bar
now has its first real data.

## Unresolved questions

- **Core or profile** — this RFC proposes the class, not its packaging; the evaluation-profile
  alternative above is the live counter-proposal to Core amendment.
- **Evidence interchange** — does the tri-state evidence-availability input grow into
  [RFC 0003](0003-evidence-reference.md)'s evidence reference, or stay minimal?
- **Beyond decimals** — units and date/time must be excluded explicitly, not
  `unknown`-by-accident.
- **Number representability** — is equality between syntactically valid but arithmetically
  unrepresentable JSON numbers `unknown` (as the first implementation chose) or an explicit
  input error?
- **Disposition serialization** — the exact JSON members of the disposition (in particular the
  handoff state and target echo) must be pinned; two independent implementations agreed on all
  semantics while serializing `handoff` incompatibly.
- **Trace minimum** — must a trace surface a true rule that a forced outcome skipped?
- **Graph interaction** — the disposition is a *candidate* representation for
  [RFC 0002](0002-judgment-graph.md)'s partial-failure question, not the answer: whether a
  downstream pack sees an unresolved upstream as `absent` or `unknown` evidence, which
  requirement receives it, how outcome identity survives the mapping, and whether downstream
  evaluation stops or accumulates are all edge semantics RFC 0002 still owes.
- **Selection probe** — [RFC 0004](0004-planner-interface.md)'s thin selection query should not
  consume full dispositions (they couple selection to evidence and resolution); a separately
  exposed tri-state applicability check would preserve the separation, and applicability is
  never authorization.
- **Claim verification** — is passing the corpus self-asserted, or must results be published?

## Appendix: walked instances (non-normative)

Evidence, not specification. Pack: [`data-request-intake-triage`](../examples/data-request-intake-triage.json).
Facts abbreviate `/request/*`: `type` (default `data-access` where unstated), `completeness` (C),
`appropriateness` (A), `embargoedInformationToUnauthorizedRecipients` (E). Evidence availability
abbreviates `intake-form` (IF) and `sponsor-endorsement` (SE). Expected dispositions follow the
sketch's chosen semantics; before that choice, instance 7a was the recorded divergence — the
original three-reader exercise split it between `{unknown}` and `{missing-required-evidence}`,
and the adversarial re-walk confirmed both readings were defensible under §§7–8 as written.

| # | Facts | Evidence | Expected disposition |
| --- | --- | --- | --- |
| 1 | `type=dataset-deletion`, others omitted | IF present, SE present | `not-applicable`, reasons `{not-applicable}`, handoff requested |
| 2 | `type` missing | IF present, SE present | `unresolved`, reasons `{unknown}`, handoff requested |
| 3 | C=complete, A=hard-fail, E=false | IF present, SE present | `outcome: decline-redirect`, no handoff |
| 4 | C=incomplete, A=pass, E=false | IF present, SE present | `outcome: clarify-return`, no handoff |
| 5 | C=complete, A=pending, E=false | IF present, SE present | `outcome: clarify-return`, no handoff |
| 6 | C=complete, A=pass, E=false | IF present, SE present | `outcome: proceed`, no handoff |
| 7a | C=complete, A=pass, E=false | IF present, SE **unknown** | `unresolved`, reasons `{unknown}`, handoff requested — *the recorded divergence, resolved by the sketch* |
| 7b | C=complete, A=pass, E=false | IF present, SE **absent** | `unresolved`, reasons `{missing-required-evidence}`, handoff requested |
| 8 | C=complete, A=pass, E=**true** | IF present, SE present | `outcome: decline-redirect` (forced; normal rules skipped), no handoff |
| 9 | C=incomplete, A=**hard-fail**, E=false | IF present, SE present | `unresolved`, reasons `{conflict}` (decline and clarify rules both true), handoff requested |

Instance 8's forced outcome bypasses a proceed rule that would otherwise be true — the trace
question above. Instance 9 is why conflict is never tie-broken: §8's closing rules out array
order, lexical id order, and implementation-defined priority. The `no-match` fallback path is
unreachable for this pack while `fallbackOutcome` is declared; a fallback-free variant belongs in
the constructed corpus rows.

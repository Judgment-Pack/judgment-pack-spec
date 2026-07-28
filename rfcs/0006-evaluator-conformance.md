# RFC 0006: Evaluator conformance

- Status: Accepted
- Type: Standards-track (Core amendment)
- Created: 2026-07-27
- Accepted: 2026-07-28

> **Adoption record.** This RFC was accepted by the single maintainer under the interim review regime
> ([RFC 0009](0009-interim-review-regime.md)), and the amendment it proposes lands in Core
> [`0.2.0-draft`](../spec/judgment-pack-core.md) in the same merge: §3.4 defines the evaluator
> conformance class, §8.2 its inputs, §8.3 the portable disposition, §8.4 the error contract, and
> [`conformance/evaluation/`](../conformance/evaluation/README.md) the seed corpus. The reviews of
> this RFC and of the amendment, with a written disposition for every finding, are recorded on the
> pull requests; RFC 0006's own review record is
> [pull request 9](https://github.com/Judgment-Pack/judgment-pack-spec/pull/9).
>
> This document stays the record of the *proposal*. Where its sketch and the landed text differ — the
> disposition's exact members, the named error classes, and the sketch's requirement that corpus inputs
> fit *mandated minimum* limits (Core §10 mandates only that an implementation define and document its
> limits, and the corpus keeps its cases well inside any plausible one instead) — the specification
> governs; §1.1 makes an RFC informative in any case.
>
> The Core-or-profile question below is resolved to Core, and two other questions were answered on
> acceptance. Of the rest, Core §13 carries four: evidence interchange, number representability, the
> trace minimum, and the machine-readable diagnostic contract. Graph interaction and the selection probe
> are not Core questions and stay with [RFC 0002](0002-judgment-graph.md) and
> [RFC 0004](0004-planner-interface.md). Claim verification — where corpus results are published and who
> may check them — is carried nowhere normative and stays open in this RFC only; Core §3.4.1 requires a
> claim to state the results, which makes it an attestation by the claimant.
>
> **What the evidence supports, and what it does not.** The evidence is two implementations and a
> 13/13 agreement corpus. Both implementations trace to one maintainer's direction — the second was
> written clean-room, inside an information barrier, by a different model family, but from reference
> texts this maintainer chose and including this RFC's own implementation-experience notes. Their
> agreement therefore **corroborates** the semantics; it does not independently confirm them.
>
> Acceptance is at the maturity this RFC names. Per [RFC 0000](0000-rfc-process.md), acceptance
> approves a design for that maturity and makes nothing stable: this is design approval for a **draft**
> specification, not a stability claim, and `0.2.0-draft` may still change incompatibly. RFC 0000's bar
> for a stable normative feature — evidence from two *independent* implementations — is **not met**,
> and it is re-tested at stabilization rather than treated as satisfied by this acceptance. Third-party
> implementation experience remains the evidence this process cannot manufacture.

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
`0.x` breaking change per RFC 0000. Migration: a pack needs exactly one edit, its `specVersion` value,
because that value is exact (Core §4); it keeps its meaning and stays valid against the preserved
`0.1.0-draft` schema if left unedited. Evaluator-conformance claims attach only to the later exact
`specVersion`; nothing is acquired automatically, and claims against `0.1.0-draft` remain forbidden
permanently.

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
  carry a row for it. *What landed: half of that ask.* Core §8.3 names this as the single seam its
  byte-agreement requirement does not cover and §13 keeps the choice between `unknown` and an input
  error open, so the corpus deliberately carries **no** row — a row cannot state an expected result
  while the result is undecided. The corpus README records the absence.
- §8.1's direct exception escalation with no `escalation` object was implemented as a requested
  handoff with no target; the later draft should confirm that shape. *Confirmed:* Core §8.1 and
  §8.3's `state` rule both say `requested` with no Core-defined destination, and the corpus carries a
  row for it.
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
identical kind, outcome, reason set, and handoff state on ten rows over the nine walked appendix
instances, counting both variants of instance 7, plus three probes (omitted evidence input,
decimal-string ordering, missing exception fact): thirteen in total.

Those thirteen rows are the imported part of the landed corpus. The seven rows constructed after
acceptance — the handoff subset rule, `state: none`, `no-match` with no fallback, a direct exception
escalation with no `escalation` object, and §7.4's ordered comparison — are **not** part of the 13/13
result. They were derived from the landed text and replayed through the clean-room Python evaluator
alone; the corpus README says so rather than folding them into the agreement number.

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

Acceptance answered three of these and left the rest open. An answered question keeps its text, struck,
with the answer beside it; nothing is deleted, because what acceptance decided is only legible next to
what it was choosing between.

- ~~**Core or profile** — this RFC proposes the class, not its packaging; the evaluation-profile
  alternative above is the live counter-proposal to Core amendment.~~ **Answered on acceptance: Core.**
  [RFC 0008](0008-bounded-collection-quantifiers.md) and any future evaluation profile both need the
  error contract and the disposition shape, and neither should restate them; one shared place in Core
  is what makes a profile additive rather than a second, competing definition. The profile alternative
  stays on the record as the packaging that would have been chosen had Core amendment proved too heavy.
- **Evidence interchange** — does the tri-state evidence-availability input grow into
  [RFC 0003](0003-evidence-reference.md)'s evidence reference, or stay minimal? Core `0.2.0-draft`
  ships the tri-state (§8.2) and records the question in §13.
- ~~**Beyond decimals** — units and date/time must be excluded explicitly, not
  `unknown`-by-accident.~~ **Answered by §7.4 as amended: excluded explicitly.** An ordered comparison
  is defined iff both values are §2.2 decimal strings; any other value, including a JSON number,
  yields `unknown`, and a unit or date/time operand is not expressible in an ordered comparison at all
  rather than accidentally unknown.
- **Number representability** — is equality between syntactically valid but arithmetically
  unrepresentable JSON numbers `unknown` (as the first implementation chose) or an explicit
  input error? Still open, and now bounded rather than merely implied: §7.4 confines the
  cannot-compare-exactly case to JSON numbers outside an implementation's exact range, §8.3 names it as
  the single seam in the byte-agreement requirement, and Core §13 carries the choice itself.
- ~~**Disposition serialization** — the exact JSON members of the disposition (in particular the
  handoff state and target echo) must be pinned; two independent implementations agreed on all
  semantics while serializing `handoff` incompatibly.~~ **Answered by §8.3: pinned, and neither
  implementation's shape was adopted whole.** `handoff` is an object — the second implementer's bare
  string cannot carry why a handoff was requested — but it carries `state` and, when requested,
  `triggeredBy`, and it does **not** echo the escalation target, which was the first implementation's
  reading. A copy of the target would let a disposition disagree with its own pack, and §6.7 makes the
  target a display name rather than an address. Set members are sorted and comparison is by set
  equality, with RFC 8785 named for the byte-level case.
- **Trace minimum** — must a trace surface a true rule that a forced outcome skipped? Still open;
  §8.3 only requires that a trace live *outside* the disposition and change no member of it.
- **Graph interaction** — the disposition is a *candidate* representation for
  [RFC 0002](0002-judgment-graph.md)'s partial-failure question, not the answer: whether a
  downstream pack sees an unresolved upstream as `absent` or `unknown` evidence, which
  requirement receives it, how outcome identity survives the mapping, and whether downstream
  evaluation stops or accumulates are all edge semantics RFC 0002 still owes.
- **Selection probe** — [RFC 0004](0004-planner-interface.md)'s thin selection query should not
  consume full dispositions (they couple selection to evidence and resolution); a separately
  exposed tri-state applicability check would preserve the separation, and applicability is
  never authorization.
- **Claim verification** — is passing the corpus self-asserted, or must results be published? Half
  answered: §3.4.1 requires that a claim state the version, the corpus version, and the results
  obtained, and forbids a claim without corpus results — but it does not say where those results are
  published or who may check them, so the claim remains an attestation by the claimant.

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

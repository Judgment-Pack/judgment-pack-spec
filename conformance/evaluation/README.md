# Evaluation corpus

This directory is the evaluation corpus for Judgment Pack Core
[`0.5.0`](../../spec/judgment-pack-core.md). It is the corpus an implementation must pass before
it may claim evaluator conformance (§3.4), and it is normative for that class only (§1.1). It is not a
validation corpus: the document-conformance cases stay in [`../`](../README.md), and nothing here
changes whether a document is carrier, structurally, or semantically conforming.

This is a **seed** corpus. It is version-pinned to `0.5.0`, it is not exhaustive, and it grows
by RFC. Passing it is necessary for an evaluator-conformance claim; it is not evidence that an
implementation is correct on inputs the corpus does not contain.

The specification repository owns no evaluator. These cases state expected results; they do not
compute them. The repository's own tests check that the carrier is well formed — that every case
resolves to a real pack, that no committed pack fixture is referenced by no case, that its inputs are
shaped as §8.2 requires, and that its expected disposition is a legal §8.3 disposition over that pack,
including the two invariants JSON Schema cannot express — and stop there.

## The case carrier

[`manifest.json`](manifest.json) is the machine-readable index; its shape is defined by
[`manifest.schema.json`](manifest.schema.json). Four members describe the corpus itself:

| Field          | Meaning                                                                                        |
| -------------- | ---------------------------------------------------------------------------------------------- |
| `suiteVersion` | The corpus version an evaluator-conformance claim must name (Core §3.4.1).                       |
| `specVersion`  | The exact Core version these expectations are computed under.                                    |
| `status`       | `draft`, the corpus maturity level; `candidate` and `release` are later ladder steps.             |
| `label`        | `seed` — this corpus is not exhaustive and does not aim to be.                                    |

Two more, `pairs` and `ownEvaluationForm`, relate rows and packs to Core §8.5; they are described
under "Pairs, and packs that are their own evaluation form" below.

`suiteVersion` equals the `specVersion` the corpus was published for, and the corpus is frozen when
that version is released: rows are added, changed, or corrected only on the way to a later
`specVersion`, never inside a released one, so two identically worded claims require the same rows
(Core §3.4.1).

A claim against a released corpus must state that **every** row of it passed (Core §3.4.1). A failing row
blocks the claim, and a claimant cannot excuse it by calling the row defective: only a project-issued
erratum, recorded in [`errata.md`](errata.md) against that `suiteVersion`, can do that, and even then the
claim must name the row and cite the erratum. An erratum edits no row.

Every case records:

| Field                  | Meaning                                                                                        |
| ---------------------- | ---------------------------------------------------------------------------------------------- |
| `id`                   | Case identity, unique in the corpus.                                                            |
| `origin`               | Where the case came from, so imported and constructed rows stay distinguishable.                |
| `pack`                 | The pack input, as a path under `packs/`.                                                       |
| `facts`                | The one JSON facts document of §8.2. `fact.path` is an RFC 6901 pointer into it.                 |
| `evidenceAvailability` | The §8.2 tri-state input: declared requirement id → `present`, `absent`, or `unknown`.           |
| `supportedExtensions`  | The capabilities the evaluator is assumed to support. Empty on all but three rows.               |
| `expectedDisposition`  | The exact §8.3 disposition, both sets already sorted — **or**                                    |
| `expectedErrorClass`   | the §8.4 error class expected instead of a disposition. Exactly one of the two is present.       |
| `workBudget`           | Optional. A positive integer of evaluation-work units; absent means no budget (see below).        |
| `expectedErrorPhase`   | Optional. `preflight` or `evaluation`, alongside `expectedErrorClass` only (see below).           |
| `focus`                | What the row is for, in one sentence.                                                           |
| `specSection`          | The section that decides the expectation.                                                       |

`workBudget` and `expectedErrorPhase` are defined by this version's carrier and used by no row in it, so
that a later row can carry them without another carrier change (Core §3.4.1). `workBudget` is stated in
the accounting units a future work-accounting model will define; when it is absent the case sets no
budget and the implementation's own documented §10 limit applies. `expectedErrorPhase` says which phase
the expected error class was reached in — `preflight`, while the inputs were being admitted (§8.2), or
`evaluation`, while an admitted input was being evaluated (§8) — which is the distinction §8.4 uses to
keep `malformed-input` and `resource-exhaustion` apart. The carrier rejects it on a row that expects a
disposition.

An omitted `evidenceAvailability` member means the case supplies no evidence document at all, which
§8.2 makes equivalent to every declared requirement being `unknown`. An omitted key inside a supplied
document means the same for that one requirement.

Comparison is by disposition equality as §8.3 defines it: `reasons` and `handoff.triggeredBy` are
sets, so a difference in serialized order is not a difference in result. The corpus stores them sorted
so that a byte comparison after RFC 8785 canonicalization also works.

Every case is far below any plausible limit under §10. The corpus does not probe a limit, because two
conforming implementations may set different ones and an input above either is outside the portable
claim.

## What is here now

`0.5.0` holds 103 rows over 41 pack fixtures: 20 rows carried from Core `0.3.0` over 4 packs, and 83
rows added with [RFC 0031](../../rfcs/0031-annotations-and-value-sets.md) over 37 packs. 93 rows
expect a disposition and 10 expect an error class. 29 pairs group 67 of the rows, and 17 of the 41
packs are their own evaluation form. The `origin` field of each case says where it came from.

### Carried from `0.3.0`

Twenty rows over four pack fixtures. Thirteen are *imported* from the cross-implementation exercise
recorded in [RFC 0006](../../rfcs/0006-evaluator-conformance.md); seven are *constructed* from the
specification text. Each row is unchanged; its pack differs from the `0.3.0` fixture only in its
`specVersion` bytes, and each pack is its own evaluation form, so Core §8.5 gives each row its
`0.3.0` result.

Imported — thirteen rows, all over
[`packs/data-request-intake-triage.json`](packs/data-request-intake-triage.json), byte-identical to
[`examples/data-request-intake-triage.json`](../../examples/data-request-intake-triage.json):

- ten rows over the nine walked instances of the RFC 0006 appendix, counting both variants of the
  instance that recorded the one genuine semantic divergence in `0.1.0-draft`
  (`required-evidence-unknown` and `required-evidence-absent`, resolved by §8 step 2); and
- three probes: an omitted evidence-availability document, an unreferenced decimal-string fact, and a
  missing exception fact.

Constructed — seven rows over three fixtures, each exercising a §§7.4–8.3 rule the imported rows
leave untouched:

- [`packs/partial-trigger-conflict.json`](packs/partial-trigger-conflict.json) declares
  `escalation.triggers` as a strict subset of the reasons its rules can generate. Three rows: two
  retained reasons where only one is a trigger, so `reasons` and `handoff.triggeredBy` differ and
  `reasons` is a two-element sorted set; a retained reason that is not a trigger, so an unresolved
  result carries `state: none`; and every rule false with no `fallbackOutcome`, so `no-match`.
- [`packs/direct-exception-escalation.json`](packs/direct-exception-escalation.json) carries an
  `escalate` exception and no `escalation` object. One row: a direct request recorded as a requested
  handoff whose destination the pack does not supply (§8.1), taking precedence over an otherwise true
  rule.
- [`packs/decimal-threshold-fee.json`](packs/decimal-threshold-fee.json) orders a decimal-string amount
  against a threshold. Three rows: `999.99` is below `1000` by mathematical value though it sorts after
  it by code point; `1000.00` is at the threshold while remaining unequal to the string `1000` under
  `equals`, so no conflict arises; and a JSON number is neither coerced into the ordered comparison nor
  equal to a decimal string, so both ordered rules are `unknown`.

The two implementations described in RFC 0006 agreed on all thirteen imported rows. That agreement is
weaker evidence than it looks: both implementations trace to one maintainer's direction, so their
agreement corroborates the semantics rather than independently confirming them. The seven
constructed rows were read off the text by the same maintainer and first replayed through one of the
two. Both were later run over the whole frozen `0.3.0` corpus, and all twenty rows byte-agreed, each
disposition compared against the other's. That strengthens the evidence and changes nothing about
its independence.

### Added with RFC 0031

Eighty-three rows over thirty-seven pack fixtures, each with origin `rfc-0031`. They test Core §8.5:
for a semantically conforming pack, an evaluator produces the result §§7–8 give the pack's evaluation
form, with annotations removed and value-set references expanded. Every expectation is written by
hand from Core §8. Five of the packs are not semantically conforming, each for one stated reason, and
the six rows over them expect `pack-not-conformant`.

- **Inertness.** For each kind of result (an outcome, `not-applicable`, `unknown`, `conflict` and
  no match), a pack without annotations, with annotations, and with changed annotations give one
  disposition. So do a missing required evidence requirement, an escalate exception and a fallback
  outcome, on a pack with two escalation routes, one filtered and one not, so the routes a
  disposition names are compared too. A label that spells an outcome id, a reason and a route
  target changes nothing. Two error-class pairs show that annotations change neither
  `unsupported-required-extension` nor `malformed-input`, and a required vendor key beside
  annotations still counts. A pack and the same pack with an optional vendor extension give one
  result (Core §9).
- **Malformed annotations.** Too many keys, and a tab in a string: `pack-not-conformant`. So is the
  annotations name listed in `metadata.requiredExtensions`, never `unsupported-required-extension`.
- **The supported-extension set.** One row lists `org.judgmentpack.annotations` in its
  `supportedExtensions`, which Core §8.2 ignores because the name is not requirable, and gives the
  result of the same row without it.
- **Substitution.** A reference and its inline array give one result: on a match, on no match, on
  an absent path, inside an exception that matches and one that does not, inside `applicability`,
  under `not`, `all` and `any`, with repeated entries, and with entry annotations present, absent or
  changed. An unreferenced set, and `valueSets: []`, change nothing.
- **Equality.** A set of type-distinct values (`1`, `"true"`, `"1.00"`, a decomposed accent, an
  object and an object that looks like a reference) compared under Core §7.4, with no coercion and
  no normalization.
- **Positions, not content.** An inline `in` item that holds the annotations name is compared as
  data.
- **Resolution.** An unresolved reference, and one naming an outcome's id, are `pack-not-conformant`,
  which §8.4's order reports ahead of a malformed evidence document.

Two implementations by the drafting model's vendor have run these rows, and neither is independent
of the text's authors. The repository's test evaluator,
[`tools/core_050_eval.py`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/tools/core_050_eval.py),
a test tool that makes no conformance claim, runs all 103 rows. The reference runtime ran the rows
as they were staged before the release, under the draft selector `0.4.0-draft`, and has not yet run
them under `0.5.0` (RFC 0031, Acceptance).

### Pairs, and packs that are their own evaluation form

`pairs` groups rows that give one result for a stated reason, which a static check confirms without
an evaluator. A pair is a defect in the fixtures unless its basis holds:

| Basis | Pairs | Holds when |
| --- | --- | --- |
| `evaluation-form` | 27 | the packs differ and their evaluation forms are equal JSON values, and the rows' facts, evidence availability, supported set and expectation are equal |
| `optional-extension` | 1 | the evaluation forms differ only in optional vendor extensions, and the rows' inputs and expectation are equal (Core §9) |
| `supported-extension-set` | 1 | one pack, and the supported sets differ only by `org.judgmentpack.annotations` |

A row belongs to one pair at most. The `evaluation-form` check compares whole evaluation forms, `id`
and `version` included, so a pair cannot pass by differing in identity.

`ownEvaluationForm` lists the pack fixtures that are their own evaluation form (Core §8.5): conforming
packs with no `valueSets` member, no reference and no annotations. Core §8.5 changes nothing for a row
over one of them. The list names all 17 such packs, whichever version's rows use them, and the
repository's tests hold it to exactly those packs.

## What is missing

Stated rather than implied, because a seed corpus that hides its gaps is worse than a small one:

- **Error rows are few, and one class has none.** Ten rows expect an error class: six
  `pack-not-conformant`, two `malformed-input` (an evidence document naming a requirement the pack
  does not declare) and two `unsupported-required-extension`, all added with RFC 0031. One,
  `value-set-unresolved-precedence`, is a precedence row: §8.4's order reports `pack-not-conformant`
  ahead of a malformed evidence document. `resource-exhaustion` has no row; nor does the phase split
  between `malformed-input` and `resource-exhaustion` that `expectedErrorPhase` exists to record, nor
  the order of `malformed-input` ahead of `unsupported-required-extension`. Being frozen, this corpus
  will not gain any. Five rows
  [RFC 0013](../../rfcs/0013-evaluator-error-and-precedence-cases.md) proposed are **staged** for the
  next `suiteVersion` in
  [`staged/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/evaluation/staged)
  — three single-class rows and two precedence rows. They are in no corpus, and no claim may cite
  them. `resource-exhaustion` and the phase split are not among them.
- **The carrier cannot yet express some error rows, and that is deferred.** `facts` is embedded parsed
  JSON and `evidenceAvailability` is constrained to the tri-state by this carrier's own schema, so a
  malformed-JSON document, a duplicate member, a non-object evidence input, and an invalid evidence
  state have no fixture form here. A raw-document fixture form — a case that carries an input as
  unparsed bytes — is **deferred to the next `suiteVersion`**; it is a carrier change, and this one is
  frozen at release (Core §3.4.1). The `workBudget` and `expectedErrorPhase` members were added in
  `0.3.0`, ahead of the rows that will use them, so that those rows need no carrier change; no row in
  this version uses either.
- **Three mandatory operators have no row.** §7.4 requires every operator of an implementation claiming
  the class, and the fixtures exercise only `equals`, `in`, `greater-than-or-equal`, and `less-than`.
  There is no `not-equals`, `greater-than`, or `less-than-or-equal` row.
- **`literal` and `not` are thin.** A `literal` condition appears only as `true`, as one rule of four
  value-set packs, and on every row the child of each `not` is true or false. No row has a `literal`
  `false`, and no row has `not` over an `unknown` child, which §7.3 requires to stay `unknown`.
- **Composite equality only through `in`.** Every `equals` operand in the fixtures is a Boolean or a
  string. §7.4's recursive equality is reached only through `in`: an object entry whose members differ
  in order, a literal object that looks like a reference, an inline item holding the annotations name,
  and a number equal to an entry by mathematical value. No row compares an array, and none compares
  against `null`.
- **One fallback shape.** Three rows reach §8 step 10's fallback, each over a pack whose only rule is
  false. Step 10 with false or ignored-unknown rules beside the fallback, which must not prevent it,
  has no row.
- **No number-representability row.** RFC 0006's implementation experience asked for one, and it is
  deliberately absent: whether equality involving a JSON number an implementation cannot represent
  exactly is `unknown` or an input error is open (Core §13), and §8.3 names it as the single seam in
  the byte-agreement requirement. A row cannot state an expected result until the question closes.
- **Thin handoff coverage, stated exactly.** Of the 93 disposition rows, exactly one —
  `handoff-trigger-subset` — has `triggeredBy` as a nonempty proper subset of `reasons`. Two more,
  `retained-reason-without-a-trigger` and `no-match-without-a-fallback`, pair an `unresolved` result
  with `state: none`. One, `direct-exception-escalation-without-configuration`, records a requested
  handoff in a pack that declares no `escalation` object; on that row `triggeredBy` still equals
  `reasons`. On every other row with `state: requested`, `triggeredBy` equals `reasons`, and apart from
  those two rows `state` is `requested` exactly when `kind` is not `outcome`. Nine rows, over the
  three packs with two escalation routes, name routes in their disposition. So the subset rule of §8.3
  rests on a single row, and no row combines a direct exception escalation with a trigger-selected
  reason.
- **Unexercised structure.** `suppress-rule` exceptions, a pack with more than one exception (so
  neither forced outcomes that differ nor an unknown exception with `onUnknown: escalate` beside a
  forced outcome), conditions nested more than one level, and `missing-required-evidence` together
  with any other reason all have no row.
- **No permutation rows.** Rule-order permutations that must not change a result are called for by
  RFC 0006 and absent. Optional-extension content that must stay inert has the one
  `optional-extension` pair above.
- **Rules a second evaluator can break without a row failing.** Issue #310 records that a test
  evaluator written from the text, mutation-checked against the rows, can break each of these
  without any row failing: a `suppress-rule` exception (§8 steps 4 and 6); forced outcomes that
  differ, and the conflict that results (§8 steps 4–5); §8 step 5 stopping before the rules when
  required evidence blocks, beside a rule that would add `unknown` or `conflict`; an omitted evidence
  key or document for a required requirement reading as `unknown` (§8.2); `evidence-present` over
  `absent` giving false (§7.5); an unknown rule with `onUnknown: ignore` not blocking no-match or the
  fallback (§8 steps 7 and 10); three-valued `all`, `any` and `not` over `unknown` (§§7.1–7.3),
  including an absent path under `not` with a value-set reference; an ordered comparison over a
  non-decimal string such as `"1e3"` giving `unknown` (§7.4); and a reference resolving to the set it
  names when a pack declares more than one. The issue proposes rows for each; none is in this corpus.

Growth is by RFC, and a row that changes an expected disposition is a normative change to §§7–8, not
a corpus edit.

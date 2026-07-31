# Evaluation corpus

This directory is the evaluation corpus for Judgment Pack Core
[`0.2.0-draft`](../../spec/judgment-pack-core.md). It is the corpus an implementation must pass before
it may claim evaluator conformance (§3.4), and it is normative for that class only (§1.1). It is not a
validation corpus: the document-conformance cases stay in [`../`](../README.md), and nothing here
changes whether a document is carrier, structurally, or semantically conforming.

This is a **seed** corpus. It is version-pinned to `0.2.0-draft`, it is not exhaustive, and it grows
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
| `status`       | `research-preview`, matching the maturity of the specification itself.                           |
| `label`        | `seed` — this corpus is not exhaustive and does not aim to be.                                    |

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
| `supportedExtensions`  | The capabilities the evaluator is assumed to support. Empty for every seed case.                 |
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

Twenty cases over four pack fixtures. Thirteen are *imported* from the cross-implementation exercise
recorded in [RFC 0006](../../rfcs/0006-evaluator-conformance.md); seven are *constructed* here from the
specification text. The `origin` field of each case says which.

Imported — thirteen rows, all over
[`packs/data-request-intake-triage.json`](packs/data-request-intake-triage.json), byte-identical to
[`examples/data-request-intake-triage.json`](../../examples/data-request-intake-triage.json):

- ten rows over the nine walked instances of the RFC 0006 appendix, counting both variants of the
  instance that recorded the one genuine semantic divergence in `0.1.0-draft`
  (`required-evidence-unknown` and `required-evidence-absent`, resolved by §8 step 2); and
- three probes: an omitted evidence-availability document, an unreferenced decimal-string fact, and a
  missing exception fact.

Constructed — seven rows over three fixtures written for this corpus, each exercising a §§7.4–8.3 rule
the imported rows leave untouched:

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
what motivated pinning them, and it is weaker evidence than it looks: both implementations trace to
one maintainer's direction, so their agreement corroborates the semantics rather than independently
confirming them. The rows are pinned because the specification now says what the result is, not
because two programs happened to match.

**When this corpus was published, the seven constructed rows did not carry that agreement.** They
were read off the specification text by the same maintainer, then replayed through one of those two
implementations — the clean-room Python evaluator — and all seven reproduced. That was a
single-implementation check on a derivation, not two implementations agreeing on pinned semantics.

**They carry it now, and at the byte level.** Both implementations have since been run over this
whole frozen corpus and **all twenty rows byte-agree**, each disposition compared against the
other's rather than only against the manifest, so every §8.3 serialization rule that could have
diverged is covered. That strengthens the evidence behind the constructed rows and changes nothing
about its independence: the caveat above holds in full, because both implementations still trace to
one maintainer's direction. A divergence found against any of these rows remains as likely to be a
defect in the row as in an implementation (Core §3.4), and only a project-issued erratum can settle
that (see [errata](errata.md)).

## What is missing

Stated rather than implied, because a seed corpus that hides its gaps is worse than a small one:

- **No error rows.** `expectedErrorClass` is part of the carrier and no case uses it yet. Each of the
  §8.4 classes — a non-conforming pack, an unsupported required extension, a malformed facts or
  evidence document, an undeclared evidence key, resource exhaustion — deserves a row, as does §8.4's
  precedence order where two classes apply to the same inputs, and so does the phase split between
  `malformed-input` and `resource-exhaustion` that `expectedErrorPhase` exists to record.
- **The carrier cannot yet express some of those rows, and that is deferred.** `facts` is embedded
  parsed JSON and `evidenceAvailability` is constrained to the tri-state by this carrier's own schema, so
  a malformed-JSON document, a duplicate member, a non-object evidence input, and an invalid evidence
  state have no fixture form here. A raw-document fixture form — a case that carries an input as unparsed
  bytes — is **deferred to the next `suiteVersion`**; it is a carrier change, and this one is frozen at
  release (Core §3.4.1). This repository's own checks also still require every evidence key a case supplies
  to be declared by its pack, so an undeclared-key row needs that check made conditional on the expected
  error class, exactly as the pack-conformance check already is. The `workBudget` and `expectedErrorPhase`
  members were added now, ahead of the rows that will use them, precisely so that those rows do not need
  another carrier change; no row in this version uses either.
- **Three mandatory operators have no row.** §7.4 requires every operator of an implementation claiming
  the class, and the fixtures exercise only `equals`, `in`, `greater-than-or-equal`, and `less-than`.
  There is no `not-equals`, `greater-than`, or `less-than-or-equal` row.
- **No `literal` and no `not` row.** Of §7's condition forms the fixtures use `fact`, `all`, `any`, and
  `evidence-present`. A `literal` condition and a `not` condition — including `not` over an `unknown`
  child, which §7.3 requires to stay `unknown` — have no row.
- **No composite-equality row.** Every `equals` operand in the fixtures is a Boolean or a string. §7.4's
  recursive equality over arrays and objects, its member-order-insensitive object comparison, and
  equality against `null` are all unexercised.
- **No fallback-selection row.** Only one fixture declares a `fallbackOutcome`, and no row reaches it:
  the two rows that produce that outcome do so through a true rule at §8 step 9, and the one row that
  reaches step 10 has no fallback to select (`no-match-without-a-fallback`). Step 10's positive branch —
  no true rule, a declared fallback, and false or ignored-unknown rules that must not prevent it — has no
  row.
- **No number-representability row.** RFC 0006's implementation experience asked for one, and it is
  deliberately absent: whether equality involving a JSON number an implementation cannot represent
  exactly is `unknown` or an input error is open (Core §13), and §8.3 names it as the single seam in
  the byte-agreement requirement. A row cannot state an expected result until the question closes.
- **Thin handoff coverage, stated exactly.** Of the twenty rows, exactly one — `handoff-trigger-subset` —
  has `triggeredBy` as a proper subset of `reasons`. Two more, `retained-reason-without-a-trigger` and
  `no-match-without-a-fallback`, pair an `unresolved` result with `state: none`. One,
  `direct-exception-escalation-without-configuration`, records a requested handoff in a pack that declares
  no `escalation` object, so the request has no Core-defined destination; on that row `triggeredBy` still
  equals `reasons`. On every other row with `state: requested` — all thirteen imported rows, whose pack
  declares all five triggers, and the one decimal row that escalates on an unknown — `triggeredBy` equals
  `reasons`, and `state` is `requested` exactly when `kind` is not `outcome`. So the subset rule of §8.3
  rests on a single row, and no row combines a direct exception escalation with a trigger-selected reason
  or exercises a pack that declares `escalation` with triggers none of its reachable reasons can match.
- **Unexercised structure.** `suppress-rule` exceptions, an unknown exception with
  `onUnknown: escalate` combined with a forced outcome, conditions nested more than one level, and
  `missing-required-evidence` together with any other reason all have no row.
- **No permutation or hostile rows.** Rule-order permutations that must not change a result, and
  hostile optional-extension content that must stay inert during evaluation, are both called for by
  RFC 0006 and absent here.

Growth is by RFC, and a row that changes an expected disposition is a normative change to §§7–8, not
a corpus edit.

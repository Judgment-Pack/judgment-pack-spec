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
| `focus`                | What the row is for, in one sentence.                                                           |
| `specSection`          | The section that decides the expectation.                                                       |

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

**The seven constructed rows do not carry that agreement.** They were read off the specification text
by the same maintainer, then replayed through one of those two implementations — the clean-room Python
evaluator, with each fixture's `specVersion` locally re-declared to the draft that evaluator targets,
which is exactly the one-value migration of Core §11 — and all seven reproduced. That is a
single-implementation check on a derivation, not two implementations agreeing on pinned semantics. A
divergence found against one of these rows is as likely to be a defect in the row as in an
implementation (Core §3.4).

## What is missing

Stated rather than implied, because a seed corpus that hides its gaps is worse than a small one:

- **No error rows.** `expectedErrorClass` is part of the carrier and no case uses it yet. Each of the
  §8.4 classes — a non-conforming pack, an unsupported required extension, a malformed facts or
  evidence document, an undeclared evidence key, resource exhaustion — deserves a row, as does §8.4's
  precedence order where two classes apply to the same inputs.
- **No number-representability row.** RFC 0006's implementation experience asked for one, and it is
  deliberately absent: whether equality involving a JSON number an implementation cannot represent
  exactly is `unknown` or an input error is open (Core §13), and §8.3 names it as the single seam in
  the byte-agreement requirement. A row cannot state an expected result until the question closes.
- **Thin handoff coverage.** Only the three `partial-trigger-conflict` rows and the direct-escalation
  row distinguish `handoff` from `reasons`; every imported row uses a pack that declares all five
  triggers, so on those rows `triggeredBy` always equals `reasons` and `state` is `requested` exactly
  when `kind` is not `outcome`. No row yet combines a direct exception escalation with a
  trigger-selected reason, and no row exercises a pack that declares `escalation` with triggers none of
  its reachable reasons can match.
- **Unexercised structure.** `suppress-rule` exceptions, an unknown exception with
  `onUnknown: escalate` combined with a forced outcome, `not` conditions, conditions nested more than
  one level, and `missing-required-evidence` together with any other reason all have no row.
- **No permutation or hostile rows.** Rule-order permutations that must not change a result, and
  hostile optional-extension content that must stay inert during evaluation, are both called for by
  RFC 0006 and absent here.

Growth is by RFC, and a row that changes an expected disposition is a normative change to §§7–8, not
a corpus edit.

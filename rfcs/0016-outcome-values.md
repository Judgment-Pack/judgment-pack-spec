# RFC 0016: Outcome values — a decision that states a quantity

- Status: Draft
- Type: Standards-track (candidate specification-defined extension, or Core amendment — undecided)
- Created: 2026-09-28

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar. Two prototypes implement it,
> each behind an opt-in, and no conformance class depends on any of it.

## Summary

An outcome may declare **values**: named members, each either a constant the author wrote or a copy
of one fact. Each has a declared type: `string`, `decimal` or `boolean`. When evaluation produces
that outcome, the disposition carries the values. When a value is drawn from a fact and the fact
cannot supply it, no outcome is produced: the result is `unresolved` with reason `unknown`.

Nothing is calculated, and no condition operator is added. A value names no tool and is not an
instruction. The proposal does change one thing about what is decided: a declared value that cannot
be supplied withholds the outcome that declares it.

## Problem

Core's outcome is an identifier and a label (§6.4), and the disposition names one outcome (§8.3).
That is enough when the answer is a category. Many decisions are about a quantity — a limit
granted, an amount approved — and for those the result leaves the quantity out. Two cases recur.

**A quantity chosen from authored tiers.** "A score of 720 or more is granted a limit of 10,000;
650 to 719, a limit of 5,000." A pack can declare one outcome per tier. The number each tier means
is then kept by the consumer, in a table from outcome identifier to quantity that is no part of
the pack. The pack is not the whole policy, and two consumers may hold different tables for the
same pack.

**A quantity passed through.** "Approve the proposed refund when it is 200 or less." The pack
compares the fact `/proposed/refundAmount` with `"200"` and produces `approve`. Which quantity was
approved is for the consumer to work out from its own copy of the facts, and the pack does not say
which fact that is. A rule that reads the quantity can refuse to decide without it, by
`onUnknown: escalate`. Nothing ties the quantity to the outcome itself: an outcome reached through a
forced outcome, through `fallbackOutcome`, or through a rule that reads other facts is produced
whether or not the quantity is present.

The affected users are pack authors, who cannot write the quantity where the policy is; consumers,
who rebuild it outside the portable result; and readers of a decision record, who see that
something was approved and not how much.

This RFC is not about calculated quantities. Core compares facts and does not calculate
([RFC 0007](0007-determination-boundary.md)), and nothing here changes that. A quantity that is
calculated is prepared before evaluation and arrives as a fact; this proposal lets the result state
it once it has.

## Evidence

The evidence is thin, and this section says how thin.

- **Two of the repository's five example packs decide over a quantity and state none.**
  [`minimal-expense-approval.json`](../examples/minimal-expense-approval.json) compares
  `/expense/amount` with `"5000"`, and
  [`supplier-invoice-approval.json`](../examples/supplier-invoice-approval.json) compares
  `/invoice/variancePercent` with `"2.5"`. Where either produces an outcome, the disposition names
  a category, such as `approve` or `manual-review`, and does not carry the quantity compared. These
  packs were written by the project as illustrations. They show the shape of the gap, not how
  often real policy has it.
- **Core anticipates the need.** §2.2 says that "exact decimal quantities outside ordered
  fact-condition operands require a future profile or declared extension."
- **No study measures this.** RFC 0007's figures are about what a pack could not decide. They are
  not evidence about what a result should state, and this proposal does not rest on them.
- **A construct with a similar name is a different one.** [RFC 0002](0002-judgment-graph.md)
  records that Study 004 of the research line named "outcome-value mapping" among the constructs
  implicated in its edge grammar's open items. That construct belongs to composition, where one
  decision's outcome feeds another's inputs. This RFC does not address it (see *Unresolved
  questions*).
- **Two prototypes have run this document's rows.** *Implementation* says what exists and what
  building it found. That is experience of whether the text can be built. It is not evidence of
  need: no author has used the feature.

The examples in this document were written for it.

## Specification

The semantics below are stated once. How a pack carries the declaration — a specification-defined
extension or a Core member — is an open question; the text uses the extension form, and
*Alternatives* gives the other.

### Declaration

An outcome declares its values under the extension name `org.judgmentpack.outcome-values`, in the
outcome's `extensions` object. A pack in which any outcome carries that name MUST list it in
`metadata.requiredExtensions`. The extension changes what evaluation produces, which §9 forbids an
optional extension to do.

As a member name of an `extensions` object, the name appears on an outcome and nowhere else. The
schema admits an `extensions` object on the root, the decision, a rule and other objects, and §9
asks only that a required name appear in some one of them. For this extension every such place
but an outcome is an error. Its entry in `metadata.requiredExtensions` is a separate matter, and
is required.

An `extensions` object, here, is one the schema defines as a member of those objects. A member
named `extensions` inside the value of another extension, or inside the operand of a condition, is
data. It declares no value, and it is no value for an entry of `metadata.requiredExtensions`.

The extension's value on an outcome is a non-empty JSON object, the **value declaration**. Each
member name is a **value name**: one lowercase ASCII letter followed by zero or more ASCII letters
or digits. The whole name is held to that, so a name that ends in a line feed is not a value name,
whatever a pattern's end anchor would admit. Each member value is a **value source**: a JSON object
with these members and no others.

| Member | Required | Value |
| --- | --- | --- |
| `type` | yes | `string`, `decimal` or `boolean` |
| `constant` | one of the two | the value itself, of the declared type |
| `fromFact` | one of the two | an RFC 6901 JSON Pointer into the facts document, as `fact.path` is (§7.4) |

Exactly one of `constant` and `fromFact` is present. A `constant` of type `string` is a JSON
string that is a sequence of Unicode scalar values; of type `decimal`, a JSON string satisfying the
decimal grammar of §2.2; of type `boolean`, a JSON Boolean.

A JSON string may hold an unpaired surrogate, written as an escape such as `"\ud800"`. Such a
string is not a sequence of Unicode scalar values and is not a `string` value. RFC 8785 cannot
serialize it, so admitting it would leave the disposition with no canonical form.

A pack that violates this section is not semantically conforming for a consumer that supports the
extension. That covers a malformed declaration, the name as a member of any `extensions` object
other than an outcome's, and a declaration in a pack that does not list the name as required. For an implementation claiming evaluator conformance this is the
`pack-not-conformant` error of §8.4. It is found in the preflight of §8.2, before step 1 of §8
runs, and so whether or not the outcome that carries the fault would have been produced.

A pack that lists the name as required while no outcome carries a declaration is in error too,
by one of two rules. Where the name is a member of some other `extensions` object, it is the rule
of place above. Where it is a member of none, it is §9's rule that a required name has a value.
An implementation that admits the name by setting it aside before it validates the rest has to
check for the second itself, and for the name listed twice, since what it set aside is what the
validator would have read.

```json
{
  "id": "approve-refund",
  "label": "Approve the proposed refund",
  "extensions": {
    "org.judgmentpack.outcome-values": {
      "refundAmount": { "type": "decimal", "fromFact": "/proposed/refundAmount" },
      "currency":     { "type": "string",  "constant": "CAD" }
    }
  }
}
```

### Resolution

Resolution runs once, after §8 has produced an `outcome` result, whether by a forced outcome
(step 6), by true rules (step 9) or by `fallbackOutcome` (step 10). It does not run for a
`not-applicable` or `unresolved` result. For an outcome that carries no value declaration it does
nothing, and the result is what §8 produced.

For the produced outcome, each value source resolves as follows.

- A `constant` resolves to the constant.
- A `fromFact` selects a value from the facts document by the pointer rules of §7.4. It resolves
  if and only if the pointer resolves and the selected value is admitted by the declared type: a
  JSON string that is a sequence of Unicode scalar values for `string`; a JSON string satisfying
  §2.2 for `decimal`; a JSON Boolean for `boolean`. Any other selected value does not resolve.
  That includes a JSON number, `null`, an array, an object, a string holding an unpaired surrogate
  and, for `decimal`, a string that does not satisfy the grammar.

A value is copied exactly as it was found. Nothing is coerced, trimmed or normalized: `"0.10"`
stays `"0.10"`, and a JSON number is never turned into a decimal string.

Resolution selects from a facts document that the preflight of §8.2 has admitted. Whether a
document that holds a string with an unpaired surrogate is admitted is the carrier's matter, and
§2.1 does not settle it. An implementation whose carrier refuses such a document answers
`malformed-input` and selects nothing. The rule above, that such a string does not resolve,
applies where the document is admitted. The two prototypes differ here (see *Implementation*).

If every value source resolves, the result is the outcome with its resolved values. If any does
not, the result is `unresolved` with the single reason `unknown`. No outcome is produced and the
disposition carries no `value` member, whether or not the other values resolved. The result is
final: `fallbackOutcome` is not tried in its place.

Handoff follows §8.1 as for any other `unknown`. It is requested exactly when the pack has an
`escalation` object whose `triggers` name `unknown`, and `handoff.triggeredBy` is then
`["unknown"]`. An implementation MAY name the value that did not resolve, outside the disposition.

### The disposition

The disposition gains one member.

| Member | Present | Value |
| --- | --- | --- |
| `value` | iff `kind` is `outcome` and the named outcome carries a value declaration | a JSON object with one member per declared value name, each the resolved value |

Every member of `value` is a JSON string or a JSON Boolean. The object holds no number, no `null`,
no array and no nested object, so the number rules of RFC 8785 still never engage (§8.3). The
byte-identity requirement of §8.3 extends to `value`.

```json
{"handoff":{"state":"none"},"kind":"outcome","outcomeId":"approve-refund","reasons":[],"value":{"currency":"CAD","refundAmount":"149.50"}}
```

### What a value is not

- **Not an instruction.** A value names no tool and requests no action. Core's statement that an
  outcome is "not an authorization to perform an external action" (§6.4) covers its values, and a
  consumer MUST NOT treat a value as authorization.
- **Not calculated.** A value source is one constant or one fact. There is no arithmetic, no
  concatenation and no choice among facts.
- **Not checked for range.** Resolution admits any value of the declared type. A pack that must
  bound a quantity does so in its rules, as it does today.
- **Not evidence of origin.** A value drawn from a fact is as trustworthy as that fact. The
  disposition does not say where the fact came from.

### What this needs from Core

- The schema refuses every name beginning `org.judgmentpack.` in two places: as a member name of
  an `extensions` object, and as an item of `metadata.requiredExtensions`. Both would admit this
  one name, and both would go on refusing every other reserved name.
- §8.3 gives the disposition "these members and no others", and names four. The proposal admits a
  fifth member name, present only under the condition in the table above.
- §9 reserves names beginning `org.judgmentpack.` for "future specification-defined extensions"
  and defines none. This would be the first, and §9 would say where such an extension's semantics
  are found.

## Examples

**Tiers.** Three outcomes; the first two carry the limit each one grants.

```json
"outcomes": [
  { "id": "limit-high", "label": "Approve, high limit",
    "extensions": { "org.judgmentpack.outcome-values": {
      "creditLimit": { "type": "decimal", "constant": "10000" } } } },
  { "id": "limit-standard", "label": "Approve, standard limit",
    "extensions": { "org.judgmentpack.outcome-values": {
      "creditLimit": { "type": "decimal", "constant": "5000" } } } },
  { "id": "decline", "label": "Decline" }
]
```

Where the pack's rules produce `limit-standard`, the disposition carries
`"value": {"creditLimit": "5000"}`. Where they produce `decline`, it carries no `value` member.

**Pass-through.** Take a pack whose one rule produces `approve-refund` when
`/customer/goodStanding` equals `true`, whose `approve-refund` outcome carries the declaration
shown under *Declaration*, and which has no `escalation` object. The rule does not read the
amount, which keeps the example to resolution; a real pack would also bound it.

With facts `{"customer": {"goodStanding": true}, "proposed": {"refundAmount": "149.50"}}` the
result is the disposition shown under *The disposition*.

Now take `/proposed/refundAmount` absent, or given as the JSON number `149.5`. The same pack
without the declaration and without its entry in `metadata.requiredExtensions` is a pack Core
admits today, and it produces `approve-refund`. With them, under this proposal, the result is:

```json
{"handoff":{"state":"none"},"kind":"unresolved","reasons":["unknown"]}
```

**A calculated quantity.** "Refund pro rata, and send refunds above 500 to a supervisor." The
calculation happens before evaluation and its result is supplied as the fact `/refund/amount`. The
pack compares that fact with `"500"` and declares `{"type": "decimal", "fromFact":
"/refund/amount"}` on its approving outcome. What performed the calculation, and how a record
cites it, are outside Core.

## Alternatives

- **No change.** Consumers keep tables from outcome identifier to quantity and read pass-through
  quantities from their own copy of the facts. It costs nothing in the specification. The quantity
  stays outside the portable result. A rule that reads the quantity can already refuse to decide
  without it, by `onUnknown: escalate` (§8, step 7), as both example packs do. Core has no
  requirement attached to the outcome itself, so a forced outcome, `fallbackOutcome` or a rule that
  does not read the quantity produces the outcome without it.
- **One outcome per quantity.** Expressible today, and sufficient for a small fixed set of tiers.
  It does not carry the quantity, and it cannot express pass-through at all.
- **A Core amendment.** The outcome object gains an optional `values` member with the same
  content, and §8 gains the resolution step. It is simpler to write. It also makes resolution part
  of §§7–8, which every implementation claiming evaluator conformance must implement in full
  (§3.4.1).
- **An optional extension.** Not available. The proposal changes the disposition and can turn an
  outcome into `unresolved`, and §9 forbids an optional extension from changing Core semantics.
- **A profile.** A separate document defining a conformance class over Core plus values. Heavier
  than an extension for one small capability, and profile negotiation is itself open (§13).
- **Product-only behaviour.** An implementation attaches quantities outside the disposition, in a
  trace or a record of its own. Two products would then state the same decision differently, which
  is the interoperability problem a portable result exists to prevent.
- **Carry only values drawn from facts.** §8.3 keeps the escalation target out of the disposition
  because "carrying a copy here would let a disposition disagree with the pack it came from." A
  constant is pack content in the same sense, and a consumer could read it from the pack. This RFC
  proposes carrying both, so that a consumer reads one member without knowing which kind it was.
  The narrower form is a real alternative, recorded under *Unresolved questions*.
- **JSON numbers as values.** Rejected. §2.2 exists because a number's decimal identity is not
  preserved, and a number in the disposition would bring RFC 8785's number rules into a comparison
  §8.3 keeps free of them.
- **A calculation vocabulary.** Out of scope. RFC 0007 lists a computation profile among its
  candidates and notes that it is the one most likely to reopen the
  [non-goal](../docs/non-goals.md) of a general-purpose rules language.
- **An outcome that names a tool to call.** Rejected. Applying an outcome is outside Core (§3,
  §6.4).

## Compatibility

- **Readers.** Under the current schema a pack using the reserved name is not structurally
  conforming, so a consumer of `0.2.0-draft` refuses it. Once the schema admits the name, a
  consumer that does not support the extension reports it as §9 requires, and an implementation
  claiming evaluator conformance answers `unsupported-required-extension` (§8.4). Neither produces
  a disposition without the values.
- **Writers.** Opt-in. A pack that declares no values is unchanged.
- **Semantics.** For a pack that declares no values, every disposition is byte-identical to the one
  produced today. For a pack that declares a value drawn from a fact, an evaluation that would
  have produced the outcome without the fact now produces `unresolved`. That change is the
  purpose of the proposal.
- **Records.** A format that stores a disposition whole stores the new member with it. A format
  that stores selected members of a disposition would have to decide whether to store this one.
- **Migration.** A pack with one outcome per tier adds a constant to each. Its outcome
  identifiers, rules and existing dispositions' `outcomeId` are unchanged.

## Security and privacy

- **Disclosure.** A disposition has so far held identifiers and reasons. With this proposal it can
  hold a copy of a fact. A `string` value drawn from a fact may carry personal data into every
  place dispositions are stored or logged. Authors should draw the least they need, and
  implementations should treat a disposition carrying `value` as they treat the facts.
- **A quantity under a caller's control.** Whoever supplies the facts supplies the quantity.
  Resolution checks its type, not its size. A pack that approves "the proposed amount" without a
  rule bounding it approves any amount.
- **Confusion with authorization.** A result reading `approve` with an amount beside it looks like
  a payment instruction. It is a declared result (§6.4). The risk is in consumers, and the text
  above states the prohibition.
- **Confusion about origin.** A value in a disposition may be read as verified. It is copied, not
  verified. Where a fact came from is recorded, if at all, outside Core.
- **Resources.** A value declaration adds one pointer resolution per `fromFact` value, for the
  one outcome produced. §10 has an implementation define limits on collection size and evaluation work and
  recommends one on string size. A declaration or a selected value past a documented limit is
  handled as §10 handles any other.

## Conformance

Document-level cases, for a consumer that supports the extension:

- *Positive.* A declaration with a constant of each type; one with `fromFact`; one mixing both; a
  `string` constant holding a character outside the Basic Multilingual Plane, written as a
  surrogate pair.
- *Negative.* A value source with both `constant` and `fromFact`; with neither; with an unknown
  `type`; with a member this section does not define; a `decimal` constant that fails §2.2; a
  `boolean` constant given as the string `"true"`; a `string` constant holding an unpaired
  surrogate; an empty declaration; a value name that begins with a capital or a digit; a value name
  that ends in a line feed; a declaration in a pack that does not list the extension as required;
  the extension name on the root object alone; the name on an outcome and on a rule as well.

Evaluation rows:

- *Positive.* A constant carried on an outcome produced by a true rule, by a forced outcome and by
  `fallbackOutcome`; a `fromFact` that resolves, of each type.
- *Negative.* A `fromFact` whose pointer does not resolve, on an outcome produced by a true rule,
  by a forced outcome and by `fallbackOutcome`, each `unresolved` with reason `unknown`; two
  values of which one does not resolve, where the disposition carries no `value` member at all; a
  `not-applicable` result and an `unresolved` result, each carrying no `value`.
- *Handoff.* A value that does not resolve in a pack whose `escalation.triggers` name `unknown`,
  where handoff is requested with `triggeredBy` of `["unknown"]`; in a pack whose triggers do not
  name it, and in a pack with no `escalation` object, where `handoff.state` is `none`.
- *Boundary.* A decimal with trailing zeroes copied unchanged; the empty string as a `string`
  value; the Boolean `false`; two true rules naming the same outcome, which carries its values
  once; the same declaration with its members authored in another order, which yields the
  byte-identical canonical disposition.
- *Adversarial.* Where `decimal` is declared: a fact given as a JSON number, as `null`, as an
  object, and as a string with surrounding whitespace, none of which resolves. Where `string` is
  declared: a fact string with surrounding whitespace, which resolves and is copied unchanged,
  and one holding an unpaired surrogate, which does not resolve where the carrier admits the facts
  document and is `malformed-input` where it does not. A pointer that traverses an array
  out of range. A produced outcome whose own values resolve while another outcome declares a
  `fromFact` the facts cannot supply: the result is the produced outcome, because only it is
  inspected.

Error rows:

- A malformed declaration on an outcome the evaluation would not have produced, in a pack whose
  applicability is false: `pack-not-conformant`, and not the `not-applicable` disposition.
- A malformed declaration together with an evidence-availability document carrying an undeclared
  member name: `pack-not-conformant`, the first class in §8.4's order.
- For an implementation that does not support the extension and whose schema admits the name, a
  well-formed pack that requires it:
  `unsupported-required-extension`. The same pack gets the same class where its declaration
  breaks only this extension's own rules, such as an empty declaration or an unknown `type`: an
  implementation that does not support the extension is not required to check them. A fault
  Core itself defines is another matter. A duplicate member name inside the declaration makes
  the pack `pack-not-conformant` for every implementation, and that class comes first (§8.4).
  Under the schema of `0.2.0-draft`, which refuses the name, every row of this bullet is
  `pack-not-conformant`, as *Compatibility* says. The first three cannot be run as written until
  a schema admits the name.

## Implementation

Two implementation paths are plausible: the Go reference runtime and the clean-room Python
evaluator, the two whose agreement [RFC 0006](0006-evaluator-conformance.md) reports. They are not
independent evidence. RFC 0006 records that both trace to one maintainer's direction, and
[`GOVERNANCE.md`](../GOVERNANCE.md) says that two implementations by one author are not
independent. RFC 0000's bar for a stable feature still needs an implementation directed
independently of this project.

**Both now implement it as a prototype** (2026-09-28), each behind an opt-in that is off by
default: the Go runtime under its
[ADR-0039](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0039-draft-rfc-outcome-values-prototype.md),
and the Python evaluator as a clean-room extension, written under the experiments repository's
information-barrier protocol by a model of a different vendor than the one that drafted the Go
prototype, with its readings in entries 27 to 33 of its
[decision log](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/blob/main/python/DECISIONS.md).
Both built the extension form. Neither claims anything by it.

The cases this document lists under *Conformance* and *Examples* were written out as 60 rows,
each with a pack of its own and the answer this text gives, and run through both. A disposition
was compared byte for byte as each implementation wrote it, and an error by its class.

| | Rows |
| --- | ---: |
| Both give this document's answer | 56 |
| Both agree with each other and not with this document | 3 |
| The two differ | 1 |

Of the 39 rows whose answer is a disposition, 38 are the same bytes in both and the bytes this
document gives, the example under *The disposition* among them. The record, the rows and the
driver are in the experiments repository:
[`harness/RFC0016-AGREEMENT.md`](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/blob/main/harness/RFC0016-AGREEMENT.md).

What building it found, and where this revision answers it:

- **The one difference is about the carrier.** A fact string that holds an unpaired surrogate:
  the Python evaluator admits the facts document and the value does not resolve; the Go runtime's
  carrier refuses the document as `malformed-input`. Neither was changed to match the other.
  *Resolution* and the row under *Conformance* now say that the rule applies where the document is
  admitted, and the question is the ninth under *Unresolved questions*.
- **The three rows where both differ from this document** are those of a consumer that does not
  support the extension. Both refuse the pack as `pack-not-conformant`, because both hold a pack
  to the schema of `0.2.0-draft`, which refuses the name. The rows under *Conformance* now say
  which schema they are rows of.
- **Both read "an `extensions` object" as one the schema defines**, and not as any member of that
  name. *Declaration* now says so.
- **The two admit the name differently.** The Go runtime sets the name aside and has the published
  validator judge the rest. The Python evaluator admits the name in its two places and runs its
  other checks as they were. The first way hides two faults from the validator, which
  *Declaration* now names.
- **The examples are fragments**, and each implementer completed them into packs in its own way.
  The rows carry complete packs.
- **The two bound the work differently**, and one of them admits the prototype together with the
  prototype of [RFC 0008](0008-bounded-collection-quantifiers.md) where the other refuses the pair.
  Both are under *Unresolved questions*.

None of this is conformance evidence, and RFC 0000's bar for a stable feature is as far off as it
was: the two prototypes trace to one maintainer's direction, and the model that wrote the rows
and the driver is the one that drafted the Go prototype.

## Unresolved questions

1. **Extension or Core.** The extension form keeps §§7–8 as they are for implementations that do
   not need values. It also makes this the first specification-defined extension, which needs §9
   and the schema to say how one is admitted. The Core form avoids that and binds every evaluator.
   Both prototypes built the extension form, and neither found anything in the semantics that
   depends on the form. What the extension form cost them is what it costs a reader of the
   current schema: until a schema admits the name, no consumer can answer
   `unsupported-required-extension` for it.
2. **Should constants be carried?** See *Alternatives*. Carrying them copies pack content into the
   disposition, which §8.3 otherwise avoids.
3. **Is `unknown` the right reason?** The five generated reasons match `escalation.triggers`
   (§6.7), and `exception-escalation` is admitted beside them for a direct request (§8). Reusing
   `unknown` adds nothing to either. It leaves a consumer unable to tell a quantity that was
   missing from a condition that was unknown, except through diagnostics outside the disposition.
   One prototype gives such a diagnostic: its trace names each value of the produced outcome and
   says whether it resolved, and never carries the value.
4. **Decimal identity.** Values are copied without normalization, so `"5000"` and `"5000.00"` are
   different values. Core defines no scale, unit or decimal-aware equality (§2.2, §13), and this
   proposal adds none.
5. **Units and currency.** The example carries a currency as a separate constant. Whether a
   quantity and its unit should be one value is tied to Core's open question on units (§13).
6. **Lineage.** How a decision record cites the origin of a value drawn from a fact belongs with
   the lineage record ([RFC 0014](0014-lineage-record-and-action-binding.md)) and is not proposed
   here.
7. **Composition.** Whether a value may feed another decision's facts is RFC 0002's question.
8. **Bounds.** Whether the extension should fix a maximum number of values or a maximum string
   size, or leave both to each implementation's documented limits as §10 does. The two prototypes
   left it to their limits and chose differently: one counts declared values against a limit on
   authored items and the other has no such count, and they charge the work of resolution by
   different terms. An input near either limit is not portable between them.
9. **The carrier and an unpaired surrogate.** §2.1 requires an implementation to reject malformed
   input and does not say whether a JSON text that holds an unpaired surrogate escape is
   malformed. RFC 8785 cannot serialize such a string. One prototype's carrier refuses the text in
   any input, and the other admits it. The question is Core's and is wider than this proposal: it
   decides the class of an evaluation of any pack over such a facts document.
10. **Together with RFC 0008.** Neither this document nor
    [RFC 0008](0008-bounded-collection-quantifiers.md) says what a pack that uses both means, or
    whether one evaluation may run under both. One prototype refuses the pair and the other
    admits it. Whichever is accepted second should say.

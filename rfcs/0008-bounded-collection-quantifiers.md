# RFC 0008: Bounded collection quantifiers for conditions

- Status: Draft
- Type: Standards-track (candidate Core amendment or profile)
- Created: 2026-07-27

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar. It takes
> [RFC 0007](0007-determination-boundary.md) question D and states it precisely enough to argue
> with. Its evidence section reduces the size of the effect RFC 0007 claimed, and the reduction is
> reported here rather than left for review to find.

## Summary

Add two condition operators to §7 — `exists` and `every` — that evaluate an inner condition once per
element of an array-valued fact and combine the per-element results with the same strong
three-valued logic §7.1 and §7.2 already use. Inside the inner condition, every pointer resolves
against **the element** as document root. Nothing else changes: no arithmetic, no counting, no
access to the outer facts document, no way to reach a second collection.

The addition is deliberately smaller than the problem. Of the 25 collection-quantification
determinations the census measured, the bare quantifier expresses **3**; an optional uniformity
operator would add 2. It does not express the policy sentence RFC 0007 used to name the gap. That
shortfall is the honest content of this RFC.

## Problem

Core has no quantifier over a runtime collection. `all` and `any` combine a **fixed, authored** list
of conditions; neither can ask whether *some element* of a variable-length array satisfies a
predicate. A policy sentence such as

> "If any portion of the flight has already been flown, the agent cannot help and transfer is
> needed."

therefore cannot be stated in a pack. Something upstream inspects the segments and hands the pack a
prepared boolean, and the pack states the rule correctly *given a conclusion it did not draw and
cannot show* — RFC 0007's determination boundary in its most common concrete form. Affected: authors
encoding policy over collection-shaped inputs; auditors reading a disposition that depends on an
aggregation performed elsewhere; integrators whose producer and pack must agree on a boolean whose
definition lives in neither artifact.

**That sentence is quoted because it is how RFC 0007 named the gap, not because this RFC fixes it.**
See Q1 below: the facts behind it are `A6:/reservation/anySegmentFlown` and its twin
`A3:/reservation/anyFlightFlown`, whose adjudicated device is `state-sequencing`, not
`collection-quantification`. They are outside the 25 this RFC counts, and a bare quantifier does not
reach them.

## Evidence

RFC 0007 E6 recorded the device gap; E7 measured it. Study 003 — the preregistered census over all
twelve separable decisions in τ-bench's airline and retail policies, hypothesis-blind encoders, two
independent classifiers with adjudication — found prepared determinations in **12 / 12** decisions,
and **collection-quantification forced 25 of the 40**, against 6 for arithmetic. Full report:
[Study 003](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/003-escape-census).

**Method disclosure for everything below.** The census's own headline inter-rater result is **zero
fact-class disagreements across 84 facts** — but the same measurement pass reports **8 device
disagreements** and **17 residue-set differences**, and it is the *device* axis that supplies this
RFC's denominator of 25. Four of the 25 entered the bucket only by adjudication, each flagged
`judgment-call: true`: `A5:/derived/changesPassengerCount` (classifier 1 said `arithmetic`) and
`R1:/order/originalPaymentMethod/type`, `R2:/request/newPaymentMethodDiffersFromOriginal`,
`R4:/refund/destinationIsOriginalPaymentMethod` (classifier 1 said `precedence-ordering`). Under
classifier 1's reading the denominator is **21, not 25**, and the headline below is 3 of 21.

The sub-classification of those 25 into shapes is a **post-hoc, unregistered re-analysis**: two
independent shape readers, mutually blind and blind to this RFC's draft, classified all 25 facts;
every disagreement was adjudicated with recorded rationale. **Expressibility agreement was 25/25**
— both readers independently named the same 3 quantifier-expressible facts, the same 2
uniformity-expressible facts, and the same 20 reached by neither — and shape-bucket agreement was
22/25, with the three boundary calls adjudicated. It is still not census-grade: the taxonomy and
both reader briefs were written by this RFC's author after the census closed, and two model readers
under one brief are less independent than two human experts. Raw outputs, adjudication, and the
per-fact table:
[`analysis/`](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/003-escape-census/analysis),
recorded in the study's `DEVIATIONS.md`.

**Q1 — the shape table.** The 25 facts, across the 11 rooms producing at least one (A4 produced
none), sub-divide as follows. Per-fact assignments are in the linked artifact.

| Shape | n | Reached by |
| --- | ---: | --- |
| element-predicate | 3 | bare `exists` / `every` |
| uniformity | 2 | a dedicated `uniform` op only |
| cross-collection-membership | 3 | neither (join) |
| pairwise-cross-list | 4 | neither (join + intra-element compare) |
| count-and-cardinality | 6 | neither (cardinality against a literal bound) |
| other | 7 | neither (ordinal selection; distinguished-element cross-list comparison; size against size; whole-list classification) |

**Plainly: the bare quantifier expresses 3 of 25. With the optional `uniform` operator, 5 of 25. 20
of the 25 are reached by neither.** The three clean cases are
`A6:/reservation/anySegmentCancelledByAirline`, `R3:/modification/allNewItemsAvailable`, and
`R5:/request/allNewItemsAvailable`. **None of them is the E6 sentence.** A6's fact corresponds to a
different policy clause — airline-cancelled flight, therefore free cancellation. The E6 sentence's
facts (`A6:/reservation/anySegmentFlown`, `A3:/reservation/anyFlightFlown`) are adjudicated
`state-sequencing`: the producer must map the status lifecycle (`available` / `delayed` / `on time`
/ `flying`) plus scheduled times onto the policy word "flown", with quantification listed as a
*secondary* device behind that mapping and a clock. This RFC's remedy does not express the sentence
that motivated it. That weakens the motivating story, and relabeling the story would be worse.

Two of the three clean cases (R3, R5) need the producer to attach catalog availability onto the
elements — data shaping, not condition language. A6 needs only that the existing per-segment records
be exposed as an array: its ledger records "Mechanical aggregation of per-segment records", so
nothing must be computed onto the elements. A6 is the strongest case in the RFC.

**Q2 — correction to RFC 0007 E7.** E7 published "roughly 19 ∃/∀-shaped" and "6 count-shaped".
Against Q1 the first reads **−14**, measured against **bare + `uniform` = 5**, the most generous
reading of "a bounded quantifier"; against the bare quantifier alone (3) it is −16. The
**count-shaped figure survives**: adjudication kept `A5:/derived/changesPassengerCount` out of the
count bucket (it compares two sizes with each other, not a size against a literal bound), so E7's 6
stands in count and composition — one reader would have made it 7, and that split is recorded.
Under a *separately* generous reading — an inner condition that may also compare an element field
to an outer or array-valued **pointer** (+3) and compare two fields of the same element (+4) — 12
of 25 become expressible and 13 do not, a **−7** delta (shape reader 1's assignment; not
adjudicated). Neither reading supports 19; E7 estimated from shape names rather than per-fact
reading. RFC 0007 §D and the study's RESULTS.md carry matching amendments pointing here.

**Q3 — what blocks the rest.** Counted across the 25 per shape reader 1's multi-label assignment
(the blocker axis was not adjudicated; reader 2's per-fact notes run the same direction), a fact
may carry several: element-local predicate insufficient **12**; join to a second collection **9**;
count or cardinality **7**; ordinal selection **5**; intra-element field-vs-field comparison **4**;
whole-list classification emitting a value **2**. Two honesty flags. `A7:/reservation/passengerCount`
is arguably mis-attributed to this device by the census — the pack never quantifies over it, its
only condition is `not-equals null`, and the real loss is value-carrying arithmetic.
`A5:/derived/changesPassengerCount` sits in the 25 only by a census device adjudication (classifier
1 said `arithmetic`), and its shape was the one count-adjacent call the shape readers split on —
its presence and its bucket are both contested, and nothing in Q2 rests on it.

**Q4 — residue corroboration, recounted.** Across the 55 residues, exactly **four** carry device
`collection-quantification`; a fifth bears on the device but is adjudicated `state-sequencing`.
Mapped against Q1:

| Residue | Shape | Reached by |
| --- | --- | --- |
| A1 "collect first name, last name, and date of birth **for each passenger**" | per-element *evidence* check | neither — `evidence-present` reads no facts document and is element-invariant under this RFC's scoping |
| A3 "if **any flight** in the reservation has already been flown" (`state-sequencing`) | outside the 25 | neither — lifecycle mapping plus date-time first |
| A3 "cabin class must remain the same **across all the flights**" | uniformity | `uniform` only, and only if the pack is also given the per-segment cabins it never reads today |
| R3 "**each item** can be modified to an available new item of the same product but of different product option" | 1 element-predicate + 2 pairwise-cross-list | **partly** — the availability conjunct only |
| R5 "**each item** can be exchanged to an available new item of the same product but of different product option" | 1 element-predicate + 2 pairwise-cross-list | **partly** — the availability conjunct only |

**None of the five is fully reached.** Two are partly reached by the bare quantifier (one conjunct
of three, each); one is partly reached by `uniform`; two are not reached at all. Three of the five
correspond to no fact inside the 25. Three name the missing device explicitly in the room residue
files. R5 also records that collapsing availability to one boolean loses per-element diagnostics
("item 3 is unavailable").

## Specification

**Normative status.** The schema branches below are normative under *document* conformance in a
later exact `specVersion`. Their interpretation is **informative exactly as §7 is today** — §7's
preamble says the allowed JSON shapes remain normative through the schema and the results described
do not, and §3.4 forbids evaluator-conformance claims under `0.1.0-draft`. The semantics here become
normative only if [RFC 0006](0006-evaluator-conformance.md)'s evaluator class is accepted. This RFC
takes a hard dependency on that class for one further reason recorded in Compatibility: Core
`0.1.0-draft` has no error value to put limit exhaustion in.

Two new members of §7's condition union, structurally valid anywhere a condition is allowed —
including inside `all`, `any`, `not`, and (to one level) each other.

```json
{ "op": "exists",
  "path": "/reservation/segments",
  "where": { "op": "fact", "path": "/cancelledByAirline", "operator": "equals", "value": true } }
```

`op` is `exists` or `every`; `path` and `where` are both required and `additionalProperties` is
false. `path` is an RFC 6901 pointer, same syntax and schema pattern as `fact.path`, resolved
against the runtime facts document. `where` is any condition, subject to the nesting bound below.

**Element scope.** Within `where`, **every** pointer — a `fact.path`, a nested `exists`/`every`'s own
`path`, and `uniform`'s `path` and `at` — resolves against **the element** as document root; the
empty pointer selects the element itself. No syntax reaches any enclosing scope: not the outer facts
document, not an enclosing element. This is deliberate: a closure over outer scope is the first step
toward a join, and joins are the query language the [non-goals](../docs/non-goals.md) exclude.
`evidence-present` inside `where` keeps its ordinary meaning, since it reads no facts document — and
is therefore element-invariant, which has consequences pinned in Conformance.

**Evaluation.** Resolve `path`. If it does not resolve, or is not a JSON array, the condition is
`unknown` — mirroring §7.4. Otherwise evaluate `where` once per element and combine:

- `exists` — `true` if any element's result is true; `false` if every element's result is false;
  `unknown` otherwise. An **empty array is `false`**.
- `every` — `false` if any element's result is false; `true` if every element's result is true;
  `unknown` otherwise. An **empty array is `true`** (vacuous truth; see Security and privacy).

For a non-empty array these are the §7.2 and §7.1 tables applied to a child list whose length is
fixed at runtime rather than at authoring time: no new logic, only a new source of children. **The
empty case is new.** The schema gives `all`/`any` a `conditions` array with `minItems: 1`, so a
zero-child `all`/`any` is unreachable in any pack that can be written today; §7.1 and §7.2 have
never been exercised on an empty child list, and the tables apply to one only vacuously. The values
above are therefore a **choice**, not an inheritance. They are chosen because they are the unique
pair preserving the De Morgan duality with §7.3 — `exists(A, P) ≡ not every(A, not P)` holds on the
empty array only if `exists` is `false` and `every` is `true` — and they are pinned as conformance
rows rather than left to be re-derived.

**Order, short-circuiting, and limits.** Element order carries no meaning: within the mandated
limits, a permutation or a duplicate cannot change the result. Short-circuiting is permitted **only
on the dominant value** — `true` for `exists`, `false` for `every` — and **never on `unknown`**; an
evaluator that stops at the first `unknown` element contradicts the tables above. Limit accounting is
**order-independent and charged before any element is evaluated**: the budget consumed is
`|array| × static cost of where` (and the product across nesting), whether or not the evaluator
short-circuits. Short-circuiting may therefore only reduce actual work; it can never decide whether a
limit was exceeded. Without this, an `exists` whose match happens to sit at index 0 would return
`true` while the same array permuted returns a resource error, and two conformant evaluators would
diverge on the same inputs — the portability failure RFC 0006 exists to prevent.

**Nesting.** `where` may contain **at most one** further `exists`/`every` over an element-relative
array path; that inner quantifier's `where` MUST NOT contain another. The bound is normative and
schema-enforceable through a separate non-recursive inner definition, rather than being left to
per-implementation depth limits, so the worst-case work is exactly `|A| × |B| × cost`. **No measured
case in the census needs even one level of nesting** — the shape table has no nested row and none of
the deferred bullets asks for one. It is retained only because forbidding a construct the grammar
would otherwise admit is itself a rule to specify, and the question of whether that is the right
trade is Unresolved below. Exhaustion of the budget is an explicit evaluation error, never a
disposition ([RFC 0006](0006-evaluator-conformance.md)); see Compatibility for why that sentence
cannot be written against Core `0.1.0-draft` at all.

### Under discussion, not settled: `uniform`

```json
{ "op": "uniform", "path": "/booking/segments", "at": "/cabinClass" }
```

`op`, `path`, and `at` are all required and `additionalProperties` is false. Both `path` and `at` are
RFC 6901 pointers using the same schema pattern as `fact.path`; `at` is rooted **in the element**,
and the empty pointer **is** admitted, selecting the whole element and comparing elements to each
other under §7.4's recursive equality. Values:

- `true` iff the values selected by `at` from every element are equal under §7.4 type-preserving
  equality. Empty and singleton arrays are `true`.
- `unknown` if `path` is unresolved or non-array, or if `at` fails to resolve in any element.
- `false` otherwise — that is, whenever `at` resolves in every element and at least two selected
  values differ.

**`uniform` is the one construct here that is not reducible to the existing tables.** It produces no
per-element three-valued result and applies neither §7.1 nor §7.2; it is a genuine new aggregate,
and it is the part of this proposal that sits closest to the query-language exclusion. It exists
because two census cases are pure all-equal-at-a-sub-path and are **not** reachable by a quantifier.
`A1:/booking/cabinClassUniformAcrossFlights` tests segments against each other: the target cabin is a
runtime value, not an authoring-time literal, so no `every` against a literal reaches it.
`A1:/booking/allPassengersOnSameFlightsAndCabin` is the weakest fit — the compared sub-value is a
derived composite no stored field holds, so the operator helps only if the producer materialises
`passengers[].itinerary` first and the comparison is deep JSON equality. Two cases, one weak. Adopt
it only if that census count earns it.

### Deferred, with their counts

- **Cross-collection membership and pairwise cross-list comparison — 7 cases** (3 + 4): joins.
  `every(proposedMethodIds, id member-of profileMethodIds)`, set equality between two runtime lists,
  per-pair comparison of old and new items. They need an operand that is an array-valued *pointer*
  rather than an authored literal, or pointer-to-pointer comparison (§7.4 compares a pointer to a
  literal only). Strictly larger than a bounded quantifier.
- **Count and cardinality comparisons — 6 cases.** `count(filter(methods, type ==
  travel_certificate)) in [0,1]`; `|methods| == 1`. Limit tests need length-of-array plus an
  ordered comparison, and in four the filter predicate is itself a join. This is the slope RFC 0007
  named and the non-goals exclude.
- **Selection, size-against-size, and whole-list classification — 7 cases.**
  `R1:/order/originalPaymentMethod/type`, `R2:/request/newPaymentMethodDiffersFromOriginal`, and
  `R4:/refund/destinationIsOriginalPaymentMethod` need an element identified by position or recency
  out of an order's payment history — an index/selector operator, plus a policy definition of
  "original" the source text never gives. `A2:/request/preservesOrigin` and `preservesDestination`
  select a *distinguished* segment from each of two lists (the outbound leg) and compare across
  them. `A5:/derived/changesPassengerCount` compares two cardinalities with each other.
  `A2:/request/preservesTripType` needs the whole list classified into a value ("one-way" /
  "round-trip") and that value compared — a value-emitting classification, which is RFC 0007's
  derivation-versus-check residue family and arguably out of scope for a condition language
  entirely. Four of these seven are also among the contested census device calls disclosed above.

The accounting closes: 3 expressible + 2 `uniform` + 7 join + 6 cardinality + 7 selection,
size-against-size, and classification = **25**.

The deferral is a feature. A quantifier that expresses 3 cases and stops is a bounded addition to
§7; one that reaches 12 by admitting pointers-as-operands and cardinality is a query language
arriving in instalments.

## Alternatives

- **No change**, or **wait for a second corpus.** The status quo is one prepared boolean per
  conclusion, at the cost E7 measures; this remedy recovers 3 of 25, and the frame is two policies
  by one benchmark team. A partial fix must still be specified, tested, and supported permanently.
- **The larger language.** Admit array-valued pointer operands and cardinality, reaching 12 of 25.
  Rejected here, and named as the thing this RFC is defined against.
- **Profile, not Core.** An optional evaluation profile could carry the operators; the natural
  landing if Core amendment proves heavy, and the same landing RFC 0006 reserves for its own class.
- **Extension.** Unavailable *if* RFC 0006's class lands: §9 forbids an **optional** extension from
  changing Core semantics, and a required extension makes every pack using it not fully
  interpretable to a plain reader. Today the reasoning is weaker than it looks, because Core has no
  normative evaluation semantics for an extension to change — which is itself an argument for
  sequencing this behind RFC 0006 rather than for shipping an extension.
- **Product-only.** Leave the aggregation in the preparation layer, or let a runtime ship a local
  quantifier outside the format. Correct for engines and genuinely cheapest — but wrong for a device
  two independent packs must agree on, since the boolean's definition then lives in neither
  artifact, which is the determination boundary restated rather than addressed.
- **Guidance only.** Document the prepared-boolean idiom. Cheapest; keeps the aggregation invisible.

## Compatibility

**Precondition.** This RFC is **conditional on RFC 0006's error concept landing in Core first.**
Neither §7 nor §8 has anywhere to put limit exhaustion: §7 conditions produce exactly
`true`/`false`/`unknown`, and §8's result kinds are exactly `outcome`, `not-applicable`, and
`unresolved`. All six are dispositions, so "exhaustion is an error, never a disposition" is
unwritable against `0.1.0-draft`, and a Core amendment must not take a normative dependency on an
unaccepted RFC. Either RFC 0006's *errors are not dispositions* bullet is accepted first, or this
RFC must additionally propose a fourth, non-value evaluation outcome that terminates evaluation and
say where in §8's algorithm it interrupts. The second option is not attempted here and is recorded
in Unresolved questions.

**Reader effect.** A `0.1.0-draft` reader rejects a document containing `exists` as **structurally
non-conforming** — it does not ignore the unknown member, because `$defs/condition` is a closed
`oneOf` with `additionalProperties: false` on every branch. A reader of the later draft must
implement both constructors or report the document structurally readable but not fully
interpretable; there is no partial-support position.

**Writer effect.** None until an author opts in. Existing packs are untouched.

**Semantic effect.** Additive for documents: no existing pack becomes invalid and no existing
condition changes meaning. **Not** purely additive for evaluators — see the §10 uplift below.

**Text touched**, enumerated:

- §7 preamble — the enumerated condition list names six kinds and gains two.
- §7.1 / §7.2 — a note that the tables apply vacuously to an empty child list, a case the authored
  form cannot produce (`minItems: 1`), and that §§7.6–7.7 fix the values for the case they can.
- New §7.6 `exists` and §7.7 `every` (and §7.8 `uniform` if adopted).
- §3.3 — the semantic-conformance bullet "every `evidence-present` condition names a declared
  evidence requirement" must recurse into `where`, as must every other condition-walking bullet.
- §10 — **a deliberate SHOULD→MUST uplift.** §10 today says implementations "SHOULD define limits
  for … collection sizes … and evaluation work". A quantifier makes that bound load-bearing rather
  than prudential: it decides dispositions. For collection size and evaluation work only, this RFC
  raises the guidance to MUST. This is additive for documents and **normative for evaluators**, and
  Conformance's "exceed the mandated limits" row depends on it.
- §13 — the open-questions list.
- Schema — two (or three) new `$defs/condition` `oneOf` branches plus a non-recursive inner
  definition enforcing the nesting bound, and the exact `specVersion`.

A document using `exists` fails schema validation against `0.1.0-draft`, so the operators arrive
with a new exact `specVersion` and schema — a labeled `0.x` change per RFC 0000, not a silent
extension.

**Migration.** A prepared boolean stays valid indefinitely, and replacing one with a quantifier
changes the *facts contract* — the producer must supply the array where it supplied the conclusion.
That is a coordinated change, never automatic, and a pack mid-migration must not read a stale boolean
and a fresh array in the same rule.

## Security and privacy

- **Resource exhaustion over attacker-supplied arrays.** The facts document is untrusted (§10) and
  the supplying party controls array length. Work is `|array| × cost(where)` and one level of
  nesting multiplies: an `exists` over 10³ elements each containing an `exists` over 10³ is 10⁶ inner
  evaluations from one small document. Implementations MUST define collection-size and
  evaluation-work limits — the §10 uplift named in Compatibility — the budget MUST be charged
  order-independently as specified above, and exhaustion MUST produce an explicit evaluation error,
  never a disposition, per RFC 0006's *errors are not dispositions*.
- **Silent truncation forges a disposition, asymmetrically.** Truncating an `every` at N elements
  returns `true` from a list whose N+1-th element was false; truncating an `exists` used as a denial
  gate returns `false` and flips deny to allow. Both failures are permissive.
- **Vacuous truth is an authoring footgun.** `every` over an empty array is `true`, so a rule
  permitting a request when "all requested items are available" permits a request with no items.
  The semantics are correct and should not be softened; a validator advisory is the right place to
  catch it — warn when an `every` is the only positive condition of a rule leading to a permissive
  outcome, and document the non-vacuous idiom
  `{"op":"all","conditions":[{"op":"exists",…},{"op":"every",…}]}`.
- **Ragged arrays are a new silent-degradation surface.** An element missing the pointer `where`
  names yields `unknown` for that element, so one heterogeneous element can turn a whole quantifier
  `unknown`. Under `onUnknown: ignore` the rule then stops contributing without saying so — a new
  route by which the escape reappears as silence rather than as a prepared boolean.
- **Disclosure.** Quantifiers read nothing a `fact` condition could not, but per-element diagnostics
  would put element content into traces that cross trust boundaries. RFC 0006 observes that
  "dispositions leak rule and evidence-requirement ids across trust boundaries"; note that its
  disposition sketch (`kind` / `outcomeId` / `reasons` / `handoff`) has **no trace member at all**,
  so per-element diagnostics would be a new field this RFC introduces, not an existing question it
  inherits.

## Conformance

Rows for the evaluation corpus RFC 0006 proposes, using its case carrier (pack, facts, evidence
availability, supported extensions, expected disposition **or expected error**). Per RFC 0006, all
corpus inputs fit the mandated minimum limits.

**Positive and negative.** `exists` true where one of three segments matches; `every` true where all
match; a one-level nesting of both, true. `exists` false over a non-empty all-false array; `every`
false where exactly one element is false; a `where` naming a member no element carries → `unknown`,
not `false`.

**Boundary.** Empty array: `exists` → `false`, `every` → `true`, both pinned as rows so no
implementation silently "fixes" the vacuous case. Unknown propagation, both dominance directions:
one unknown and none true → `exists` unknown; one unknown and one **true** → `exists` **true**; one
unknown and the rest true → `every` unknown; one unknown and one false → `every` **false**. Empty
array with `evidence-present` as the whole `where`, evidence both present and absent: `every` →
`true` and `exists` → `false` in all four combinations, because `evidence-present` is
element-invariant and emptiness overrides it. A ragged array in which one element of three lacks the
`where` pointer → `unknown`, run once under `onUnknown: ignore` and once under `escalate` so the
divergence is visible. Non-array values at `path` — object, string, number, `null`, `true` — each
`unknown`; unresolved `path` `unknown`. Single-element array. Permuted order and a duplicated
element: identical disposition — **for inputs within the mandated minimum limits**, which is what
makes the row implementation-independent given permitted short-circuiting.

**Adversarial.** A facts document sized to exceed the mandated limits must yield an explicit
resource error, not `true`, `false`, or `unresolved` — run in two permutations, one placing a
dominant-value element first and one placing it last, expecting the *same* error in both, which is
the row that pins order-independent limit accounting. An empty-array `every` gating a permissive
outcome, with the permissive disposition recorded as *expected* and cross-referenced to the advisory
above. A `where` whose author plainly intended an outer pointer, read only as element-relative — that
row proves the scoping rule is not implementation-defined. A **nested** `exists` whose inner `path`
resolves only at the outer facts-document root and not within the element → `unknown`, which pins
the scoping rule for nested quantifier pointers as well as for `fact` pointers.

The equivalence check any implementation should run, scoped to the facts a quantifier actually
reaches: re-encode `A6:/reservation/anySegmentCancelledByAirline`,
`R3:/modification/allNewItemsAvailable`, and `R5:/request/allNewItemsAvailable` as quantifiers
against facts carrying the arrays, leaving each room's remaining prepared booleans in place, and
confirm the dispositions match the prepared-boolean packs. That, not a count of new operators,
measures whether it expresses them. The other collection-quantification facts in R3 and R5 are
join-shaped and cannot be part of the check.

## Implementation

RFC 0000 requires evidence from two independent implementations before a stable normative feature is
accepted. That bar applies here in full and is not met.

The natural prototype bed is the Go reference runtime's **experimental** evaluator (its ADR-0007),
which already implements §7's three-valued logic and RFC 0006's pinned semantics, so two operators
are a local addition plus a limits budget. It makes no conformance claims, and prototyping there
establishes none: Core §3.4 forbids evaluator-conformance claims under `0.1.0-draft` whatever is
implemented, and RFC 0006's class does not exist yet. A prototype yields implementation experience
and corpus rows, not standing. The natural second is the clean-room Python evaluator in
[judgment-pack-evaluator-experiments](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments),
rewritten from this RFC's text alone behind a fresh information barrier — with RFC 0006's recorded
caveat that both trace to one maintainer's direction, so agreement corroborates rather than
independently confirms. The five things they must be made to disagree about before adoption: the
empty-array values, unknown dominance in `every`, non-array `path`, where the limit is drawn, and
whether a short-circuiting and a non-short-circuiting evaluator report the same error at the limit
boundary.

## Unresolved questions

- **Is 3 of 25 enough to amend Core?** The strongest argument against this RFC is its own Evidence
  section, and the remedy does not reach the sentence RFC 0007 used to name the gap. If the answer
  is no, the honest disposition is `Rejected` or a hold for a second corpus, not a quiet reduction
  in scope.
- **How far does the 3-of-25 figure generalize?** Two independent readers agreed 25/25 on
  expressibility, so within this frame the number is stable — but the frame is the contested part:
  the **denominator** is 21 under census classifier 1's device reading (8 device disagreements,
  four `judgment-call: true` entries), the taxonomy and both reader briefs share one author, and
  the corpus is two policies by one benchmark team. Nothing here should be cited as census-grade.
- **Does the RFC 0006 dependency hold, and what if it does not?** Limit exhaustion has no home in
  Core `0.1.0-draft`. If RFC 0006 stalls, does this RFC propose a fourth non-value evaluation
  outcome and its interruption point in §8, or wait?
- **What evidence justifies nesting?** No measured case needs it; it supplies the entire
  resource-exhaustion attack surface and is the part of the grammar that most resembles the excluded
  query language. The bound is pinned at one level, but the honest options remain "keep it at one",
  "forbid it outright in the schema", or "produce a case".
- **Does `uniform` earn its keep on 2 cases, one weak?** It is also the one construct not reducible
  to the §7.1/§7.2 tables. And if it needs deep equality over composites the producer must
  materialise anyway, could the producer not have supplied the boolean?
- **Intra-element field-vs-field comparison** would move 4 more cases and is the cheapest remaining
  increment — natural completion of an element-local predicate, or the first admission that the
  inner language must grow?
- **Is outer-scope access excluded permanently or merely deferred?** Excluded here on principle; 3
  membership and 9 join-blocked cases argue the other way. Relatedly, should `evidence-present` be
  forbidden inside `where` to keep the inner language purely element-local, given that it is
  element-invariant and interacts oddly with the empty array?
- **What are the mandated minimum limits** for array length and evaluation work, so identical corpus
  runs cannot diverge on them — and do per-element diagnostics belong in the trace, given that
  authors want them, they carry element content across trust boundaries, and RFC 0006's disposition
  has no trace member to put them in?
- **Core or profile** — and is the vacuous-truth advisory a required validator diagnostic or
  authoring guidance?

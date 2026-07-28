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
three-valued logic §7.1 and §7.2 already use. Inside the inner condition, the element becomes the
root pointers resolve against (`uniform`'s `at`, defined below, is member-relative by its own rule). Nothing else changes: no arithmetic, no counting, no access to
the outer facts document, no way to reach a second collection.

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

The sub-classification of those 25 into shapes is a **post-hoc, unregistered re-analysis**: **two
separate blinded model runs under one author-written brief, in isolated contexts**, classified all
25 facts; every disagreement was adjudicated with recorded rationale. **Expressibility agreement was
25/25** — the two runs named the same 3 quantifier-expressible facts, the same 2
uniformity-expressible facts, and the same 20 reached by neither — and shape-bucket agreement was
22/25, with the three boundary calls adjudicated. State plainly what that proves: **output agreement
between two separate runs, not human-grade independence.** The taxonomy and the single brief were
written by this RFC's author after the census closed, both runs read that same brief, and the
information barrier is the isolated contexts and nothing stronger. It is not census-grade. The
briefs and the run metadata are committed alongside the raw outputs, so the characterization can be
audited rather than taken on trust. Raw outputs, briefs, adjudication, and the per-fact table:
[`analysis/`](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/003-escape-census/analysis)
(committed on the `census-shape-subclassification` branch, merging ahead of this RFC; pinned at
commit `5d42452`), recorded in the study's `DEVIATIONS.md`.

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
`0.1.0-draft` has no evaluation-error contract to put limit exhaustion in.

Two new members of §7's condition union, structurally valid anywhere a condition is allowed —
including inside `all`, `any`, `not`, and (to a maximum aggregate depth of two) each other.

```json
{ "op": "exists",
  "path": "/reservation/segments",
  "where": { "op": "fact", "path": "/cancelledByAirline", "operator": "equals", "value": true } }
```

`op` is `exists` or `every`; `path` and `where` are both required and `additionalProperties` is
false. `path` is an RFC 6901 pointer, same syntax and schema pattern as `fact.path`, resolved
against the current condition root defined immediately below — the runtime facts document at the top
level. `where` is any condition, subject to the nesting bound below.

**Element scope: the current condition root.** Pointers stop resolving against one fixed document,
so the rule has to name what they do resolve against. Define the **current condition root**. At the
start of evaluation it is the runtime facts document, and every pointer outside a quantifier
resolves against it exactly as §7.4 says today. Then:

- an aggregate's `path` — `exists`, `every`, and `uniform` alike — resolves against the current
  condition root, whatever it currently is;
- while `where` is evaluated for one selected element, **the current condition root is that
  element**, and it is restored to its previous value when that element's evaluation finishes;
- `uniform`'s `at` resolves against **each member selected by `uniform`'s `path`**, not against the
  current condition root;
- an empty `fact.path` or aggregate `path` selects whatever the current root is: the facts
  document at the top level, the element inside a `where`. An empty `uniform.at` selects **each
  whole member**, under the preceding rule, not the current root.

Nesting therefore re-roots once per level. An inner quantifier's `path` is rooted at the element its
enclosing `where` is running on; that inner quantifier's own `where` re-roots again at the inner
member. Roots are restored, never accumulated, and **no syntax reaches an enclosing root** — not the
outer facts document, not an enclosing element. This is deliberate: a closure over outer scope is the
first step toward a join, and joins are the query language the
[non-goals](../docs/non-goals.md) exclude.

This **amends §7.4**, which today roots `fact.path` at the runtime facts document unconditionally,
including the empty pointer. The amendment is conservative — outside a `where` the old rule and the
new one coincide — but it is a change to existing text, not an addition beside it, and §7.4 is listed
in Compatibility accordingly. Where a pointer resolves at both the outer and the inner root, the
**inner value wins inside `where`**; a conformance collision row pins that rather than leaving it to
be inferred.

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
above are therefore a **choice**, not an inheritance. Three reasons carry the choice: `false` and
`true` are the **identity elements** of finite disjunction and conjunction, so the empty case is the
one that leaves a fold unchanged; they **agree with ordinary existential and universal
quantification** over an empty domain; and they are **consistent under adding elements** — an empty
`exists` is `false` and becomes `true` on the first true element, an empty `every` is `true` and
becomes `false` on the first false one, with no discontinuity at the first element.

They also **preserve** the §7.3 De Morgan duality: `exists(A, P) ≡ not every(A, not P)`, which on the
empty array reduces to `exists∅ ≡ not every∅`, and `(false, true)` satisfies it. But duality alone
does **not** force them — `(true, false)` and `(unknown, unknown)` satisfy the same equation. The
duality is a consistency check on the choice, not its derivation. The values are pinned as
conformance rows rather than left to be re-derived.

**Order and short-circuiting.** Element order carries no meaning: within the mandated limits, a
permutation or a duplicate cannot change the result. Short-circuiting is permitted **only on the
dominant value** — `true` for `exists`, `false` for `every` — and **never on `unknown`**; an
evaluator that stops at the first `unknown` element contradicts the tables above.

**Limit accounting is undefined in this draft, and defining it is an acceptance precondition.** The
design intent is normative-in-waiting and is stated first, because it is what constrains the model
that must eventually be written: the budget MUST be charged **before any element is evaluated** and
**independently of element order**, so short-circuiting may only reduce *actual* work and can
**never** change whether the limit was exceeded. Without that, an `exists` whose match happens to sit
at index 0 returns `true` while the same array permuted returns a resource error, and two conformant
evaluators diverge on the same inputs — the portability failure RFC 0006 exists to prevent.
Adversarial review confirms this idea is coherent, but only once a precise precharged budget exists.

No such budget exists here. An earlier draft of this RFC put a number on it — array length times a
per-`where` constant, multiplied across nesting — and that was false precision, now withdrawn. There
is no defined work unit, and `equals` over composites, `in`, and `uniform`'s deep equality all cost
in proportion to runtime data rather than to the authored condition. A model that satisfies the
intent above must, at minimum:

- define a **work unit**, and a **preflight function** that computes the charge without evaluating
  the condition and yields the same charge under any element order;
- charge **ragged nested arrays** correctly: the child work of an outer array `A` over inner arrays
  `Bᵢ` is `Σᵢ |Bᵢ|`, not `|A| × |B|` — there is no single inner length to multiply by;
- charge **Boolean subtrees** inside `where`, including branches a short-circuiting evaluator never
  reaches;
- charge **deep equality** against the size of the values compared, not as a constant;
- charge **`uniform`**, which has no `where` at all, so no `where`-shaped rule reaches it;
- charge **sibling aggregates additively**, since the nesting bound below permits them;
- state whether **pointer resolution** happens during preflight, and how an unresolved or non-array
  inner path is charged — a pointer that fails to resolve still had to be looked up.

Producing that model is a **precondition for accepting this RFC**, not an implementation detail; it
is restated as an Unresolved question below. Until it exists, the resource story here is an intent
with a named hole in it.

**Nesting: a maximum aggregate depth of two.** Call `exists`, `every`, and `uniform` **aggregates**.
`uniform` counts, because it traverses a collection exactly as the quantifiers do — the earlier "at
most one further `exists`/`every`" wording admitted `exists → exists → uniform`, a third traversal
the bound was supposed to forbid. A condition's **aggregate depth** is the number of aggregates on
the path from the condition's root to any node within it. The bound is a **maximum aggregate depth
of two**: a top-level aggregate may contain aggregates in its `where`, and those may contain none.

Two consequences, neither stated before:

- **Sibling aggregates at the same depth are permitted.** A `where` may hold several aggregates under
  an `all` or `any`. Their costs **add**; no single product bounds the work, which is one reason the
  accounting model above has to be written before this is safe.
- **Depth is structural, not syntactic adjacency.** An aggregate reached only through `all`, `any`,
  or `not` inside a `where` is still at depth two, and one inside *its* `where` is at depth three and
  invalid. Wrapping does not launder depth.

The bound is normative and schema-enforceable through **depth-indexed, non-recursive definitions**:
three condition definitions by remaining depth, where the outer definition's aggregate branches take
their `where` from a depth-one definition, the depth-one definition's aggregate branches take theirs
from a depth-zero definition, and the depth-zero definition carries no aggregate branch at all — with
`all`, `any`, and `not` recursing **within their own tier** at every level, so wrapping cannot
launder depth. This replaces per-implementation depth limits.
**No measured case in the census needs even one level of nesting** — the shape table has no nested
row and none of the deferred bullets asks for one. Depth two is retained only because forbidding a
construct the grammar would otherwise admit is itself a rule to specify, and the question of whether
that is the right trade is Unresolved below. Exhaustion of the budget is an explicit evaluation
error, never a disposition ([RFC 0006](0006-evaluator-conformance.md)); see Compatibility for why
that sentence cannot be written against Core `0.1.0-draft` at all.

### Under discussion, not settled: `uniform`

```json
{ "op": "uniform", "path": "/booking/segments", "at": "/cabinClass" }
```

`op`, `path`, and `at` are all required and `additionalProperties` is false. Both `path` and `at` are
RFC 6901 pointers using the same schema pattern as `fact.path`; `path` resolves against the current
condition root and `at` is rooted **in each selected member**, and the empty pointer **is** admitted,
selecting the whole element and comparing elements to each other under §7.4's recursive equality.

The value is fixed by the clauses below, applied **in order**; the first that applies decides. The
table is stated this way because the earlier draft's three bullets overlapped — a singleton whose
`at` was missing satisfied both an unqualified "singleton is `true`" and an unqualified "unresolved
`at` is `unknown`".

1. `path` unresolved or not a JSON array → **`unknown`**.
2. Empty array → **`true`**.
3. Any two elements whose `at`-values **both resolve** and are **unequal** under §7.4 equality →
   **`false`**. A known counterexample dominates missing data: uniformity is already disproved, and
   no absent value can restore it.
4. Otherwise, if `at` fails to resolve in **any** element → **`unknown`**. This includes a
   singleton whose `at` is missing: that case is `unknown`, **not** `true`. The earlier claim that
   singleton arrays are `true` is corrected here.

There is deliberately no arm for a comparison that "resolves but does not decide". §7.4 equality
over carrier-valid JSON is **determinate**: numeric equality is decidable in the length of the
tokens by sign and normalized mantissa-and-exponent comparison, with no need to materialise the
value, and every other case is structural. An implementation unable to decide a comparison within
its limits produces a **resource error, never `unknown`** — inability is an operational condition,
not a semantic (RFC 0006, errors are not dispositions). This is pinned because implementation found
the trap: one prototype's first reading returned `unknown` for huge-exponent pairs its number
representation could not hold, the other compared the values and returned `false`, and the two
disagreed on `1e999999999` vs `2e999999999` — a divergence no earlier corpus row exercised. The
conformance rows now include huge-exponent equal and unequal pairs.
5. Otherwise → **`true`**: `at` resolved in every element and every selected value is equal.

Clause 3 before clause 4 is the strong-information reading, and it matches how §7.1 and §7.2 already
let a dominant value beat an `unknown` sibling; the alternative, infectious missing data, would make
`uniform` the one operator in which absence outranks evidence. Equality is §7.4's throughout, so
arrays compare element-wise **in order**, objects compare **without regard to member order**, `null`
equals `null`, and there is no coercion between JSON types. `uniform`'s share of the evaluation
budget is part of the accounting model this draft leaves undefined — the operator has no `where`, so
nothing in the withdrawn cost sketch reached it at all.

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
  ordered comparison, and in three the filter predicate is itself a join. This is the slope RFC 0007
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
§7; one that reaches 12 by admitting pointers-as-operands and intra-element field comparison is a
query language arriving in instalments.

## Alternatives

- **No change**, or **wait for a second corpus.** The status quo is one prepared boolean per
  conclusion, at the cost E7 measures; this remedy recovers 3 of 25, and the frame is two policies
  by one benchmark team. A partial fix must still be specified, tested, and supported permanently.
- **The larger language.** Admit array-valued pointer operands and intra-element field
  comparison, reaching 12 of 25.
  Rejected here, and named as the thing this RFC is defined against.
- **Graph-level quantification.** Compose instead of extend: a Judgment Graph edge
  ([RFC 0002](0002-judgment-graph.md)) that evaluated a sub-pack once per element of a collection
  and exposed the aggregated dispositions ("all granted", "any denied") as an upstream fact would
  relocate the bounded aggregation from the condition language to the composition layer. Under a
  deliberately minimal fan-out — each invocation receiving only the element as its facts root, a
  shared evidence context, dispositions folded with all/any — its reach within the census's 25-fact
  table matches the bare `exists`/`every` pair: the same three element-predicate cases, since §7's
  literal-only comparisons apply inside the sub-pack too. It is not equivalent to this RFC
  generally: it does not replace `uniform` (two further cases) or nested quantification, and a
  *richer* fan-out that gave each invocation its own evidence manifest would reach the census's A1
  per-passenger evidence residue, which these operators deliberately cannot (`evidence-present` is
  element-invariant here). Rejected as a substitute: RFC 0002 defines none of the required
  invocation, disposition-mapping, empty-array, evidence-context, or aggregation semantics, and
  answering them means a separate evaluation-semantics proposal atop its hardest unresolved
  question (the composite result) — heavier machinery for the same measured three cases.
  Orthogonal rather than competing: if both land, quantifiers aggregate within a pack and the
  graph composes across packs.
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
Three things have to be kept apart. `true`, `false`, and `unknown` are **condition values** (§7).
`outcome`, `not-applicable`, and `unresolved` are **result kinds** (§8) — what RFC 0006 calls
dispositions. Neither set contains an **error**, and limit exhaustion is an error: not a value a
condition took, not a way a decision resolved. Core is not innocent of the concept — §3.1 already
requires explicit failure rather than silent partial processing when a documented resource limit is
exceeded — but that precedent sits at the carrier layer. What is missing is an **evaluation-error
contract** and the point in §8's algorithm where it interrupts. So "exhaustion is an error, never a
disposition" is unwritable against `0.1.0-draft`, and a Core amendment must not take a normative
dependency on an unaccepted RFC. RFC 0006's *errors are not dispositions* bullet is retained here as
the prerequisite that supplies that contract. The alternative — defining an evaluation error in this
RFC, explicitly outside §8's result kinds and naming its interruption point — is not attempted here
and is recorded in Unresolved questions.

**Reader effect.** A `0.1.0-draft` reader rejects a document containing `exists` as **structurally
non-conforming** — it does not ignore the unknown member, because `$defs/condition` is a closed
`oneOf` with `additionalProperties: false` on every branch. Under the later draft, a structural
validator recognizes both operator shapes and can validate a document completely without evaluating
it: **a document's structural and semantic conformance status does not depend on which evaluator
reads it.** The obligation falls on evaluators instead. An implementation claiming the evaluator
conformance class — the future one RFC 0006 proposes, since §3.4 forbids the claim under
`0.1.0-draft` — must implement every Core condition operator, so an implementation lacking `exists`
or `every` cannot claim that class. There is no partial-support position and no per-operator
capability. Core §9's status for an unsupported *required extension* is a different mechanism for a
different case and stays reserved for required extensions.

**Writer effect.** None until an author opts in. Existing packs are untouched.

**Semantic effect.** Additive for documents: no existing pack becomes invalid and no existing
condition changes meaning. **Not** purely additive for evaluators — see the §10 uplift below.

**Text touched**, enumerated:

- §7 preamble — the enumerated condition list names six kinds and gains two.
- §7.1 / §7.2 — a note that the tables apply vacuously to an empty child list, a case the authored
  form cannot produce (`minItems: 1`), and that §§7.6–7.7 fix the values for the case they can.
- §7.4 — **amended, not merely extended.** Today it roots `fact.path` at the runtime facts document
  unconditionally, the empty pointer included. It must instead root pointers at the current condition
  root, which is the facts document everywhere except inside a `where`. Outside a quantifier the two
  readings coincide, so no existing pack changes meaning, but the sentence itself changes.
- New §7.6 `exists` and §7.7 `every` (and §7.8 `uniform` if adopted).
- §3.3 — the semantic-conformance bullet "every `evidence-present` condition names a declared
  evidence requirement" must recurse into `where`, as must every other condition-walking bullet.
- §10 — **a deliberate SHOULD→MUST uplift.** §10 today says implementations "SHOULD define limits
  for … collection sizes … and evaluation work". A quantifier makes that bound load-bearing rather
  than prudential: it decides dispositions. For collection size and evaluation work only, this RFC
  raises the guidance to MUST. This is additive for documents and **normative for evaluators** — but
  a MUST-*define* is not portability. Two evaluators that both define limits may define different
  ones, so no facts document is guaranteed to be above the limit for both, and a portable "exceeds
  the mandated limit" error row cannot be written from a MUST-define alone. Closing that needs one of
  three things: fix a common limit in the specification; carry the configured limit in the
  evaluation-case input so a corpus row can state the threshold it assumes; or scope evaluator
  portability to a common guaranteed domain and drop the above-limit row entirely. The choice is
  Unresolved below, and Conformance's "exceed the mandated limits" row is explicitly conditional
  on it.
- §13 — the open-questions list.
- Schema — two (or three) new `$defs/condition` `oneOf` branches plus **depth-indexed, non-recursive
  definitions** enforcing the aggregate-depth bound (three tiers by remaining depth, the last
  carrying no aggregate branch, `all`/`any`/`not` recursing within-tier, so depth three is
  unrepresentable), and the exact `specVersion`.

A document using `exists` fails schema validation against `0.1.0-draft`, so the operators arrive
with a new exact `specVersion` and schema — a labeled `0.x` change per RFC 0000, not a silent
extension.

**Migration.** A prepared boolean stays valid indefinitely, and replacing one with a quantifier
changes the *facts contract* — the producer must supply the array where it supplied the conclusion.
That is a coordinated change, never automatic, and a pack mid-migration must not read a stale boolean
and a fresh array in the same rule.

## Security and privacy

- **Resource exhaustion over attacker-supplied arrays.** The facts document is untrusted (§10) and
  the supplying party controls array length. Work grows with the lengths the document supplies, and
  a second aggregate level compounds it: an `exists` over 10³ elements each containing an `exists`
  over 10³ is 10⁶ inner evaluations from one small document, with sibling aggregates at the same
  depth adding on top. Implementations MUST define collection-size and evaluation-work limits — the
  §10 uplift named in Compatibility — the budget MUST be charged before evaluation and independently
  of element order, and exhaustion MUST produce an explicit evaluation error, never a disposition,
  per RFC 0006's *errors are not dispositions*. **How that budget is computed is not defined in this
  draft**, which is the open blocker recorded in Specification and Unresolved questions: the
  mitigation is stated as a requirement with no portable formula behind it yet.
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
match; a depth-two nesting of both, true. `exists` false over a non-empty all-false array; `every`
false where exactly one element is false; a `where` naming a member no element carries → `unknown`,
not `false`.

**Boundary.** Empty array: `exists` → `false`, `every` → `true`, both pinned as rows so no
implementation silently "fixes" the vacuous case. Unknown propagation, both dominance directions:
one unknown and none true → `exists` unknown; one unknown and one **true** → `exists` **true**; one
unknown and the rest true → `every` unknown; one unknown and one false → `every` **false**. Empty
array with `evidence-present` as the whole `where`, evidence both present and absent: `every` →
`true` and `exists` → `false` in all four combinations, because `evidence-present` is
element-invariant and emptiness overrides it. Non-array values at `path` — object, string, number,
`null`, `true` — each `unknown`; unresolved `path` `unknown`. Permuted order and a duplicated
element: identical disposition — **for inputs within the mandated minimum limits**, which is what
makes the row implementation-independent given permitted short-circuiting.

**Ragged arrays, one row per operator.** A missing pointer does not have one result; it depends on
the operator and on what the other elements yield, so "ragged → `unknown`" is not a row:

| Operator | Elements as `where` sees them | Expected |
| --- | --- | --- |
| `exists` | `[false, false, ‹pointer missing›]` | `unknown` |
| `exists` | `[‹pointer missing›, true, false]` | `true` — dominant value wins |
| `every` | `[true, true, ‹pointer missing›]` | `unknown` |
| `every` | `[‹pointer missing›, false, true]` | `false` — dominant value wins |

The two `unknown` rows run twice each, once under `onUnknown: ignore` and once under `escalate`, so
the divergence is visible.

**Singleton, with a predicate.** One element, `where` =
`{"op":"fact","path":"/ok","operator":"equals","value":true}`. Element `{"ok": true}` → `exists`
`true`, `every` `true`. Element `{"ok": false}` → `exists` `false`, `every` `false`. Element `{}`,
the pointer missing → `unknown` for both.

**Scope and re-rooting.** An **empty-pointer** `where` over scalar elements, comparing the element
itself to a literal: `{"op":"fact","path":"","operator":"equals","value":"gold"}` over
`["gold","gold"]` → `every` `true`, over `["gold","silver"]` → `every` `false` — pinning that the
empty pointer selects the element, not the facts document. A **collision** row: the pointer
`/status` present at the facts-document root with one value and on each element with another, the
`where` naming `/status` → the **element's** value decides, proving the inner root wins inside
`where`. A `where` whose author plainly intended an outer pointer, read only as element-relative —
that row proves the scoping rule is not implementation-defined. A **nested** `exists` whose inner
`path` resolves only at the outer facts-document root and not within the element → `unknown`, which
pins the scoping rule for nested quantifier `path`s as well as for `fact` pointers. An
**inner-`where` re-rooting** row: a pointer that resolves on the outer element but not on the inner
member → `unknown`, proving the root is replaced per level and restored afterward, never
accumulated.

**Structural.** Schema acceptance and rejection are corpus rows too, because the aggregate-depth
bound is schema-enforced rather than advisory: two sibling `exists` under an `all` inside one `where`
— **valid**, both at depth two; an `exists` reached only through an `all` inside a `where`, whose own
`where` contains a further aggregate — **invalid**, depth three, and the `all` wrapper does not
launder it; the same case with `not` instead of `all` — **invalid**; a `uniform` inside an inner
`where` — **invalid** at depth three, **valid** at depth two, since `uniform` counts as an aggregate.

**`uniform`, if adopted.** Empty `at`, comparing whole elements under §7.4 recursive equality, across
equal and unequal elements. `null` at `at` in every element → `true`, since `null` equals `null`.
Array-valued `at`: `[1,2]` against `[1,2]` → `true`, against `[2,1]` → `false`, because §7.4 array
equality is order-sensitive. Object-valued `at` differing only in member order → `true`, because
§7.4 object equality disregards member order. `at` missing in one element of three whose other two
are equal → `unknown`. `at` missing in one element of three whose other two are **unequal** —
`[1, 2, ‹at missing›]` → **`false`**, stated explicitly because the earlier draft implied `unknown`;
this is the clause-3-before-clause-4 row. Singleton whose `at` is missing → `unknown`, not `true`.
Permutation of the elements in every row above → identical result. `uniform`'s limit-accounting rows
cannot be written until the accounting model exists, since the operator has no `where` for a
`where`-shaped budget to charge.

**Adversarial.** A facts document sized to exceed the mandated limits must yield an explicit
resource error, not `true`, `false`, or `unresolved` — run in two permutations, one placing a
dominant-value element first and one placing it last, expecting the *same* error in both, which is
the row that would pin order-independent limit accounting. **That row is conditional on the
portability question in Compatibility's §10 bullet.** A MUST-define does not give two evaluators a
shared above-limit input, so the row exists under a fixed common limit or under a limit carried in
the evaluation-case input, and is dropped entirely if portability is instead scoped to a common
guaranteed domain. An empty-array `every` gating a permissive outcome, with the permissive
disposition recorded as *expected* and cross-referenced to the advisory above.

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

**Both prototypes now exist** (2026-07-27): the Go runtime's opt-in prototype (its ADR-0009) and a
clean-room Python extension implemented by a different model lineage under the experiments
repository's information-barrier protocol, each choosing its accounting model independently. An
82-row corpus over this RFC's Conformance section agrees on **81 rows across both implementations**,
and re-encoding the three reachable census facts as quantifier twins yields dispositions identical
to the prepared-boolean originals in nine of nine room-scenario pairs (with the recorded caveat that
only A6 is a mechanical re-exposure; R3/R5 require producer-side data shaping). Of the five
predicted disagreement points, four agree; the fifth — where the limit is drawn — diverged exactly
as predicted, on a row whose charge lands between the two default budgets. Implementation also
produced two corrections recorded in this revision: the determinacy rule under `uniform`'s truth
table — adopted after the prototypes disagreed on huge-exponent numeric equality, a case no earlier
corpus row exercised — and hard evidence for the accounting precondition: the first Go candidate
charged flat units and was broken by a large-pointer attack; its byte-sensitive successor was found
to leave selected runtime values unpriced; the third revision resolves and charges them in
preflight. Full matrix, corpus, and adjudications:
[`harness/RFC0008-AGREEMENT.md`](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/blob/rfc0008-python-prototype/harness/RFC0008-AGREEMENT.md)
(both prototypes live on unmerged review branches at the time of this amendment — the experiments
repository's `rfc0008-python-prototype` and the runtime's `rfc-0008-quantifier-prototype`; the
links follow the branches and the artifacts arrive on `main` when those pull requests merge).
None of this is conformance evidence (§3.4; RFC 0006's class does not exist), and RFC 0000's
acceptance bar remains formally unmet: these are prototypes traceable to one maintainer's
direction.

## Unresolved questions

- **Is 3 of 25 enough to amend Core?** The strongest argument against this RFC is its own Evidence
  section, and the remedy does not reach the sentence RFC 0007 used to name the gap. If the answer
  is no, the honest disposition is `Rejected` or a hold for a second corpus, not a quiet reduction
  in scope.
- **How far does the 3-of-25 figure generalize?** Two separate blinded model runs agreed 25/25 on
  expressibility, so within this frame the number is stable — but the frame is the contested part:
  the **denominator** is 21 under census classifier 1's device reading (8 device disagreements,
  four `judgment-call: true` entries), the taxonomy and the one brief both runs read share an author
  with this RFC, and the corpus is two policies by one benchmark team. Nothing here should be cited
  as census-grade, and the agreement figure is output agreement, not independence.
- **Does the RFC 0006 dependency hold, and what if it does not?** Limit exhaustion has no home in
  Core `0.1.0-draft`: it is neither a condition value nor a result kind. If RFC 0006 stalls, does
  this RFC define an evaluation error itself — explicitly outside §8's three result kinds, naming
  the point in §8's algorithm at which it interrupts — or wait?
- **What evidence justifies nesting?** No measured case needs it; it supplies the entire
  resource-exhaustion attack surface and is the part of the grammar that most resembles the excluded
  query language. The bound is pinned at aggregate depth two, but the honest options remain "keep it
  at two", "forbid aggregates inside `where` outright in the schema", or "produce a case".
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
- **What is the limit-accounting model, and can an above-limit case be portable at all?** This is the
  open blocker, and it has two halves. First, the model. It must define a **work unit** and an
  **order-independent preflight charge** computed before any element is evaluated; charge **ragged
  nested arrays** as `Σᵢ |Bᵢ|` rather than `|A| × |B|`; charge **Boolean subtrees**, including
  branches a short-circuiting evaluator skips; charge **deep equality** against the size of the
  values compared; charge **`uniform`**, which has no `where`; charge **sibling aggregates
  additively**; and state whether **pointer resolution** happens during preflight and how an
  unresolved or non-array inner path is charged. Second, portability. Even with such a model,
  raising §10 to MUST-define does not make an above-limit input portable, because two evaluators may
  define different limits: fix a common limit, carry the configured limit in the evaluation-case
  input, or scope portability to a common guaranteed domain and drop the above-limit corpus row.
  Both halves must be answered before this RFC can advance; the intent that short-circuiting may
  only reduce actual work and never change whether the limit was exceeded is settled, the mechanism
  is not. Neither half is hypothetical any longer. On the first: two prototypes carry
  independently chosen candidate models, and candidacy is doing real work in that sentence — the Go
  prototype's first candidate (flat units per pointer and per scalar) was broken under adversarial
  review by a large-pointer input doing gigabytes of scanning under budget, and review of its
  byte-sensitive successor found selected runtime values still unpriced, forcing a third revision
  that resolves and charges them in preflight. The **unit's shape** (bytes, not nodes) and the
  **charging of runtime values, not only authored operands** are both load-bearing and belong in
  the model; no candidate should be called complete until it survives adversarial pricing attacks.
  On the second: the cross-implementation corpus carries a reproducible row (L3) where the two
  prototypes return an outcome and a resource error on the same input solely because their default
  budgets differ.
- **Do per-element diagnostics belong in the trace?** Authors want them, they carry element content
  across trust boundaries, and RFC 0006's disposition has no trace member to put them in.
- **Core or profile** — and is the vacuous-truth advisory a required validator diagnostic or
  authoring guidance?

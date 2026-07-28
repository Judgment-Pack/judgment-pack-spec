# RFC 0007: The determination boundary — what a pack cannot hold

- Status: Draft
- Type: Standards-track (candidate Core amendment or profile)
- Created: 2026-07-27

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar. It reports a boundary found by
> encoding real regulatory text as a pack, and states the questions that follow. It proposes a
> settled answer to none of them.

## Summary

Core draws its expressive boundary at **computation**: a pack compares facts and does not calculate.
Two encodings of real policy — deliberately opposite in character, by different authors — show that
the boundary which actually appears in use is **determination**, and that the two are not the same
line. In both, part of the *judgment* left the pack along with the work it could not express, into a
preparation layer the format cannot describe, attribute, or audit.

The size of the effect is strongly domain-dependent, and this RFC is bounded by that: encoding
arithmetic-dense regulation displaced 124 facts and 13 determinations, while encoding qualitative
policy displaced 5 and 1. **The format fits qualitative policy well.** But the escape did not vanish
there — it merely changed cause. In the first domain judgment escaped because the format cannot
calculate; in the second because it cannot quantify over a collection. Neither gap predicts the
other, and that is the point: **the boundary is not a property of arithmetic. It opens wherever the
format lacks the device a policy sentence needs, and what falls through is a judgment rather than a
value.**

The specification has no vocabulary for that loss, because it only ever contemplated losing
calculation.

## Problem

§2.2 is explicit that satisfying the decimal grammar "does not imply executable comparison support",
and Core defines no arithmetic. The intended reading is a clean separation: *facts are prepared
elsewhere; the pack states the policy over them.* That reading assumes the things prepared elsewhere
are **inputs** — observations, measurements, values of record.

In practice the preparation layer also ends up holding **conclusions**. Deciding which provision an
input falls under is itself an application of the rules; when that decision requires comparing
against a computed quantity, the format cannot express it, so it migrates. The pack then states the
rules correctly *given a classification it did not make and cannot show*.

Three consequences, none visible in the format today:

1. **The decision is split across two artifacts and only one is portable.** A reader of the pack
   cannot see how much of the determination happened before evaluation began.
2. **The disposition cannot attribute what it relied on.** It reports which rules fired; it cannot
   report that the outcome depended on a prepared value, computed by whom, under which reading.
3. **A conformant pack may be unable to reach an outcome a competent reader reaches**, because the
   format can say a fact is `unknown` but not that it is *too small to matter*.

## Evidence

Two encodings of real policy, deliberately chosen to be opposites, by **different model families**
under a clean-room barrier. Study 002 was run specifically to falsify the generalisation drawn from
Study 001; it did not.

### Study 001 — arithmetic-dense regulation

Encoding the NBA Collective Bargaining Agreement excerpt published by RuleArena
(ACL 2025, MIT, commit `3b9e2256`) as a pack. The pack validates, and its 61 rules cover **61 / 61**
of the vocabulary the benchmark uses to annotate which provisions govern each instance. Full report:
[expressiveness note](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/blob/main/studies/001-policy-representation/EXPRESSIVENESS-NOTE.md).

**E1 — 124 facts had to be prepared outside the pack.** 39 always-present booleans, 18 conditional
booleans, 67 conditional decimal strings. Expected, given no arithmetic.

**E2 — the escape is not confined to arithmetic, and this is the finding.** **13 of the 39
always-present booleans name which Salary Cap Exception a transaction invokes.** The source prose
never states one. Choosing "the lowest tier whose limb covers the amount" is a legal determination
that happens to require comparison against a computed limb — so the format cannot hold it, and it
left. Any evaluation of such a pack is partly an evaluation of its preparation layer, and nothing in
the disposition says so.

**E3 — `unknown` is not `immaterial`.** 28 % of instances (60/216) could not be decided, almost all
tracing to one absent constant (a minimum-salary schedule). A preparer that refuses to invent the
figure omits the field; applicable rules go `unknown`; the pack escalates. A competent reader treats
those contracts as immaterial and proceeds. The three-valued model distinguishes true, false, and
unknown, and cannot express "absent, and below the magnitude that could change this outcome."

**E4 — §8's conflict rule constrains architecture, undocumented.** Two *distinct* candidate outcomes
resolve to `conflict` → `unresolved`. A pack holding both "this is legal" and "this is illegal" rules
therefore goes unresolved whenever one of each fires, which in a domain of independent provisions is
routine. The pack became **61 violation detectors all resolving to `illegal`, with the benign outcome
reachable only as `fallbackOutcome`.** That works, and it makes every fired rule a citation — but it
is a shape the author had to discover, not one the specification describes.

### Study 002 — qualitative policy, run to falsify the generalisation

Encoding the "Cancel flight" decision from the airline agent policy published by τ-bench (MIT, commit
`1d244f5d`) — 166 lines of real customer-service policy: deontic, procedural, essentially
arithmetic-free. Authored clean-room by a different model family, with a null result licensed in
advance. Full report:
[Study 002](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/002-qualitative-policy).

**E5 — the effect is heavily domain-dependent, and that bounds this RFC.** Prepared facts fell from
124 to **5**, prepared determinations from 13 to **1**, and seven policy devices were carried with no
friction. The resulting pack is two outcomes, one rule, one escalation exception. **The format fits
qualitative policy far better than it fits regulatory computation**, and any reading of E1–E3 that
treats them as a general indictment is wrong.

**E6 — but the escape reproduces, through a device gap that has nothing to do with arithmetic.** The
single prepared determination in Study 002 is forced by this sentence:

> "If any portion of the flight has already been flown, the agent cannot help and transfer is needed."

**Core has no quantifier over a runtime collection.** `any` combines a fixed, authored list of
conditions; it cannot ask whether *some element* of a variable-length array satisfies a predicate. So
the pack cannot decide "any portion already flown" — something upstream must inspect the segments and
hand it the conclusion.

This is the load-bearing result of the pair. In Study 001 judgment escaped because the format cannot
calculate; in Study 002 it escaped because the format cannot quantify. **The determination boundary
is therefore not a property of arithmetic. It appears wherever the format lacks the device a policy
sentence needs, and what is lost is a judgment rather than a value.** Two domains, two unrelated
missing devices, the same class of loss.

Study 002 also reproduced **E4 independently**: with no rule precedence available, its author encoded
the policy's "if … otherwise" ordering as an `escalate` exception plus a single `any` rule plus a
fallback — a different shape from Study 001's 61 violation detectors, arrived at by a different author
for the same reason. Two observations of one cause.

*Exposure recorded by that study, and it cuts against its own finding:* the authoring brief disclosed
what Study 001 had found, which primes toward finding migration. Mitigations and the reasoning are in
the study's report; a future replication should withhold the prior result.

### Study 003 — the census, answering "how common?"

A preregistered census over **all twelve separable decisions** in τ-bench's airline and retail
policies, with the blinding Study 002 lacked: hypothesis-blind encoders in isolated rooms producing
neutral fact ledgers, then a separate measurement pass — two independent classifiers, adjudicated,
disagreement counts published (**zero** fact-class disagreements across 84 facts). All twelve packs
validate. Full report:
[Study 003](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/003-escape-census).

**E7 — in this frame the escape is universal, and one device dominates.** Every decision required at
least one prepared determination (**12/12**; 40 of 58 prepared facts). The registered "all-scalar
decisions escape cleanly" clause proved vacuous rather than false: no such decision exists in either
policy, because request inputs are collections — passengers, payment methods, segments, items — and
every *all / any / each / how many* over one of them is a conclusion the format cannot draw.
**Collection-quantification forced 25 of the 40 determinations (63%); arithmetic — which Study 001
made look like the phenomenon — forced 6.** Within the 25, ~~roughly 19 are ∃/∀-shaped~~ — **amended
2026-07-27: 3, or 5 with a uniformity operator; see the amendment under question D and
[RFC 0008](0008-bounded-collection-quantifiers.md)** — and 6 are count-shaped
(`count(filter(…))` against a limit — meaningfully more language than a quantifier).

**E8 — measurement method moves the count.** Study 002's decision, blind-re-encoded and
independently classified, yielded **4** determinations where the original self-report found **1**.
Absolute counts in Studies 001–002 should be read as floors; the census's two-classifier adjudicated
protocol is the reference method. The residues (55 sentences) also gave the previously unevidenced
candidate areas their first evidence — deontic gradation, cross-decision references,
derivation-versus-check, terminality — while confirming that most sequencing loss is agent procedure
a decision format arguably should not hold.

## Specification (sketch — deliberately unsettled)

Three separable questions. E2 motivates the RFC; A and B are the mechanisms that would address what
was observed.

**A. Attribution of prepared facts.** Candidates, cheapest first:

- *Nothing.* Preparation is product territory, as acquisition is. Cost: the split stays invisible.
- *Declaration.* A pack may declare which fact pointers it expects to be prepared, with a prose
  definition and a source reference. No new semantics, no computation — the dependency becomes
  visible in the document and checkable against an input.
- *Attribution in the disposition.* The result records which declared-prepared inputs it read, so a
  decision record is self-contained about what it leaned on.
- *A computation profile.* An optional profile with a small arithmetic vocabulary. The largest
  change, and the one most likely to re-open the general-purpose-rules-language
  [non-goal](../docs/non-goals.md).

**B. Materiality.** Candidates:

- *Nothing.* Immateriality is a policy judgment; the preparer decides, and supplies a value or not.
- *A declared threshold.* A rule or evidence requirement declares a magnitude below which a missing
  or differing input cannot affect it, so an absent immaterial value yields no effect rather than
  `unknown`.
- *A fourth condition value.* Recorded so the option is visible; rejected on sight for what it would
  do to §7.

**D. Collection quantification (E6, E7).** No longer merely the best-evidenced gap — the census
shows it is the *dominant cause* of determination escape: 25 of 40 across twelve decisions, versus 6
for arithmetic. Candidates: *nothing* (a prepared boolean per conclusion, at the cost E7 quantifies);
or an existential/universal condition over an array-valued fact pointer — a small, bounded addition
to §7, no arithmetic implied, ~~expressing roughly nineteen of the twenty-five observed cases~~. The
six **count-shaped** cases (`count(filter(…))` compared to a limit) are named and deliberately
deferred: counting-with-predicates is the first step of a query language, which the non-goals
exclude. Of everything in this RFC, the bounded quantifier is ~~the most likely to be worth doing~~
the cheapest to specify, and now the best evidenced.

> **Amended 2026-07-27 — the "roughly nineteen" figure is withdrawn.** It was estimated from shape
> names rather than per-fact reading. A per-fact re-analysis of the same 25 facts — two separate
> blinded model runs with recorded adjudication; expressibility agreement 25/25 — puts a bare
> bounded quantifier's reach at **3**, or **5** with an additional all-equal-at-a-sub-path
> operator; the remaining 20 need joins, counts, ordinal selection, fact-to-fact comparison, or
> whole-list classification. The count-shaped figure of six stands. The re-analysis is post-hoc and
> unregistered, not census-grade. E7's *device* count (25 of 40) is unaffected; only the
> sub-classification within it changes. The proposal, the corrected numbers, and the question of
> whether 3 of 25 licenses a Core amendment at all now live in
> [RFC 0008](0008-bounded-collection-quantifiers.md).

**C. The architectural constraint (E4).** Either document the single-outcome / violation-detector
pattern as non-normative authoring guidance, or revisit whether §8's conflict rule should treat a
`legal`-vs-`illegal` opposition differently from genuine ambiguity. Guidance is almost certainly the
right answer; the point is that today there is neither.

The strong prior: **A-declaration** and **B-threshold** are the smallest changes that fit the
evidence, and a computation profile should be resisted until a second domain shows the same need.

## Alternatives

- **No change.** Viable, and should be taken seriously. Everything here can be pushed onto the
  preparer, which is where it already is. The cost is auditability: the pack is inspectable and the
  half of the decision sitting beside it is not.
- **Profile, not Core.** Both mechanisms could live in an optional profile, leaving Core minimal.
  Probably right if a computation vocabulary is ever adopted.
- **Guidance only.** Document the boundary and the E4 pattern as authoring guidance and change
  nothing normative. Cheapest, and possibly sufficient for E4 alone.

## Compatibility

Declaration and threshold are additive; no existing pack becomes invalid. A computation profile would
be a new optional profile, not a Core change. The document-conformance classes are untouched under
every option.

## Security and privacy

Attribution helps: a decision record naming its prepared inputs is harder to launder, and E2 is
exactly the case where a reader would want to know. A materiality threshold cuts the other way — it
lets an author declare an input immaterial and thereby suppress an escalation that should have
happened. Any threshold mechanism needs its abuse case written before adoption, and a conformance
case that attempts it.

## Conformance

If either mechanism is adopted: positive cases where a declared prepared field is present, absent, or
present-but-immaterial; negative cases where a pack cites an undeclared pointer as prepared; and
adversarial cases where a materiality declaration suppresses a required escalation. The 124-field
contract from Study 001 is the concrete artifact any proposal should be checked against: **does the
mechanism let that pack express more of its own decision, or does it merely relabel the boundary?**

## Implementation

None. The evidence is the *absence* of these features in the two evaluators that agree 13/13 on the
current semantics ([RFC 0006](0006-evaluator-conformance.md), whose caveat applies here: both trace to
one maintainer's direction, so they are not independent) — the gap is in the format, not in an
implementation of it.

## Unresolved questions

- **Is preparation inside the specification's remit at all?** The [non-goals](../docs/non-goals.md)
  exclude retrieval and orchestration. Prepared *inputs* sit comfortably outside; prepared
  *conclusions* (E2) do not obviously sit anywhere.
- **Does materiality belong to the rule, the evidence requirement, or the fact?**
- **Would a computation profile re-open the general-purpose-rules-language non-goal?** Probably —
  which is the argument for declaration over computation.
- **What else escapes?** E2 was found by encoding one domain and counting what migrated. That is a
  repeatable method and the honest way to answer this, rather than by speculation. Areas any decision
  format plausibly has to face, none of them evidenced here: obligations and prohibitions as distinct
  from outcomes; ordinal or rubric assessment as distinct from boolean conditions; precedence between
  provisions. Whether JPS needs any of them is an empirical question for the next encoding, not a
  claim of this RFC. Two of those guesses have since been resolved by Study 002: **precedence is now
  evidenced twice** (E4), and **quantification — which was not on the list at all — turned out to be
  the concrete gap** (E6). The method found something the speculation did not, which is the argument
  for continuing to run encodings rather than enumerating candidates.
- ~~**Does E1–E3 reproduce outside arithmetic-dense regulation?**~~ **Answered by Study 002: yes,
  ~25× weaker, and via an unrelated missing device (E5, E6).**
- ~~**How common is the escape in qualitative policy?**~~ **Answered by the Study 003 census (E7):
  universal in its frame — 12/12 decisions — with quantification as the dominant device.** The open
  form that remains is external validity: the frame is two policies by one benchmark team, and the
  rate outside it is unmeasured. A census over a differently-authored corpus is the natural
  replication.

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
Encoding 461 lines of real regulatory text showed that the boundary which actually appears in use is
**determination** — and the two are not the same line. What left the pack was not only arithmetic;
part of the *legal judgment* left with it, into a preparation layer the format cannot describe,
attribute, or audit.

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

From Study 001, encoding the NBA Collective Bargaining Agreement excerpt published by RuleArena
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

None. The evidence is the *absence* of these features in two independent evaluators that agree 13/13
on the current semantics ([RFC 0006](0006-evaluator-conformance.md)) — the gap is in the format, not
in an implementation of it.

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
  claim of this RFC.
- **Does E1–E3 reproduce outside arithmetic-dense regulation?** Study 001 is one domain, chosen for
  measurement properties rather than representativeness, and it is the hardest case for a format that
  declines to compute. A qualitative-policy domain might show none of it — and that result would be
  as informative as the original finding.

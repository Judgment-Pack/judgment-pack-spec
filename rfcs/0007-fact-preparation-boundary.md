# RFC 0007: The fact-preparation boundary — derived values and materiality

- Status: Draft
- Type: Standards-track (candidate Core amendment or profile)
- Created: 2026-07-27

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar. It raises questions found by
> encoding real regulatory text as a pack; it does not yet propose a settled answer to either.

## Summary

A judgment pack decides over facts it is given. The specification says nothing about **where those
facts come from, whether any of them were computed, or under whose definition** — and nothing about
how a pack expresses that an input is missing *but too small to matter*. Encoding 461 lines of real
regulatory text surfaced both as load-bearing gaps: a large share of the decision migrated into an
unattributed preparation layer, and the pack could not decide 28% of instances for want of a concept
the format has no way to express.

## Problem

Core defines conditions that compare facts (§7) and a resolution model over rules and exceptions
(§8). It defines no arithmetic — deliberately, and §2.2 is explicit that satisfying the decimal
grammar "does not imply executable comparison support". The consequence in practice is that any
decision requiring a computed quantity must be handed that quantity by something outside the pack.

Two things then become invisible to the format:

1. **Which facts were derived, by whom, and under what definition.** A disposition cannot say "this
   outcome depended on a value computed by a preparation step, using this reading of the source."
   The pack is auditable; the preparation is not.
2. **Whether a missing input actually mattered.** The three-valued model distinguishes true, false,
   and `unknown`. There is no way to say "this input is absent, and it is below the threshold at
   which it could change the outcome."

The second is the sharper gap, because it changes results. Where a human or a model shrugs at an
immaterial input and proceeds, a conformant pack must escalate.

## Evidence

From Study 001 ([expressiveness report](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/blob/main/studies/001-policy-representation/EXPRESSIVENESS-NOTE.md)),
encoding the NBA Collective Bargaining Agreement excerpt published by RuleArena (ACL 2025, MIT) as a
pack. The pack validates, and its 61 rules cover 61/61 of the benchmark's rule vocabulary.

- **124 `/facts/derived/*` fields were required** — 39 always-present booleans, 18 conditional
  booleans, 67 conditional decimal strings. None of them can be expressed in the pack.
- **13 of the 39 booleans are legal characterisation, not arithmetic.** They name *which Salary Cap
  Exception a transaction invokes* — a determination the source prose never states and that the
  benchmark exists to test. Selecting "the lowest tier whose limb covers the amount" requires
  comparing against a computed limb, so the selection had to live outside the pack. Any score for
  such a pack is partly a score for its preparation layer.
- **28% of instances (60/216) could not be decided**, almost all tracing to a single absent constant
  (a minimum-salary schedule). A preparation step that refuses to invent the figure omits the field;
  the rules go `unknown`; the pack escalates. Models reading the same text treat those contracts as
  immaterial and proceed. The pack cannot, because the format has no way to say so.
- Related and worth recording: §8's conflict rule (two distinct candidate outcomes → `unresolved`)
  pushes an author toward **one outcome per rule**. The pack became 61 violation detectors all
  resolving to `illegal`, with the benign outcome reachable only as `fallbackOutcome`. That is a
  workaround an author had to discover, not a documented pattern.

## Specification (sketch — deliberately incomplete)

Two separable questions. Neither is proposed as settled.

**A. Derived facts and their attribution.** Candidate directions:

- *Nothing.* Fact preparation is product territory, exactly as fact acquisition is. The cost is that
  a disposition's dependency on a computed value stays invisible.
- *Declaration only.* A pack may declare which fact pointers it expects to be derived, with a prose
  definition and a source reference — no computation, no new semantics, but the dependency becomes
  visible in the document and checkable in a disposition.
- *Attribution in the disposition.* The evaluation result records which derived inputs it read, so a
  decision record is self-contained about what it relied on.
- *A computation profile.* An optional profile defining a small arithmetic vocabulary. This is the
  largest change and the one most likely to re-open the "general-purpose rules language" non-goal.

**B. Materiality.** Candidate directions:

- *Nothing.* Immateriality is a policy judgment and belongs in the facts (the preparer decides, and
  supplies a value or does not).
- *A declared threshold.* A rule or requirement may declare a magnitude below which a missing or
  differing input does not affect it, so an absent immaterial value yields `false`/no-effect rather
  than `unknown`.
- *A fourth condition value.* Rejected on sight for the disruption it causes to §7, but recorded so
  the option is on the table.

The strong prior is that **A-declaration-only** and **B-declared-threshold** are the smallest changes
that address what was observed, and that a computation profile should be resisted unless a second
domain shows the same need.

## Alternatives

- **No change.** Viable. Both gaps can be pushed onto the fact preparer, which is where they are
  today. The cost is auditability: the pack is inspectable and its inputs are not.
- **Profile rather than Core.** Both questions could land in an optional profile, leaving Core's
  minimality intact. Likely the right shape for a computation vocabulary if one is ever adopted.
- **Guidance rather than normative text.** Document the violation-detector pattern and the
  fact-preparation boundary as non-normative authoring guidance, and change nothing normative. This
  is the cheapest response and may be sufficient for the pattern finding.

## Compatibility

Declaration-only and threshold options are additive and would not invalidate existing packs. A
computation profile would be a new optional profile, not a Core change. Nothing here affects the
document-conformance classes.

## Security and privacy

Attribution *helps*: a decision record that names its derived inputs is harder to launder. A
materiality threshold is a hazard in the other direction — it lets an author declare an input
immaterial and thereby suppress an escalation that should have happened. Any threshold mechanism
needs its abuse case written down before it is adopted.

## Conformance

If either direction is adopted: positive cases where a declared derived field is present, absent, or
present-but-immaterial; negative cases where a pack references an underived pointer as derived; and
adversarial cases where a materiality declaration is used to suppress an escalation that a governing
rule required.

## Implementation

No implementation exists of anything proposed here. The evidence comes from the *absence* of these
features in two independent evaluators that agree 13/13 on the current semantics
([RFC 0006](0006-evaluator-conformance.md)). The 124-field contract in Study 001 is the concrete
artifact any proposal should be checked against: does the proposed mechanism let that pack express
more of its own decision, or does it just relabel the boundary?

## Unresolved questions

- **Is fact preparation in the specification's remit at all?** The
  [non-goals](../docs/non-goals.md) exclude retrieval and orchestration; derived values sit
  uncomfortably between "input acquisition" (out) and "the decision itself" (in).
- **Does materiality belong to the rule, the evidence requirement, or the fact?**
- **Would a computation profile re-open the general-purpose-rules-language non-goal?** Probably. That
  is an argument for declaration over computation.
- **Is the violation-detector pattern a finding about §8's conflict rule, or just an authoring
  idiom?** If §8 systematically pushes authors to one outcome per rule, that deserves documenting
  either way.
- **Does any of this reproduce outside arithmetic-dense regulation?** Study 001 is one domain, chosen
  for measurement properties rather than representativeness, and it is the hardest case for a format
  that declines to compute. A qualitative-policy domain might show none of this.

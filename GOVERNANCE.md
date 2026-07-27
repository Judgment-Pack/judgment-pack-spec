# Governance

## Status: early research preview

Judgment Pack is an open, vendor-neutral specification developed in public. Today it has a single
maintainer and no independent contributors (see [Interim review regime](#interim-review-regime)).
It is not controlled by any required commercial runtime, though the reference runtime is written by
the same maintainer and is not independent evidence of interoperability. Conforming
implementations may be open-source or proprietary; conformance is defined by the specification and
its conformance cases, not by any single vendor's product.

The current status is an early research preview (`0.1.0-draft`). There is no compatibility guarantee
for `0.x` drafts. Concepts may be revised or removed as the specification is exercised against real
implementations.

Technical discussion, proposals, decisions, and compatibility analysis are expected to occur
publicly in this repository. Payment, employment, or commercial membership does not by itself
establish the technical merit of a proposal.

## Decision principles

Maintainers evaluate changes in this order:

1. demonstrated interoperability need;
2. safety and semantic clarity;
3. independent implementability;
4. compatibility and migration cost;
5. author and operator usability;
6. implementation complexity; and
7. ecosystem adoption potential.

The convenience of any single implementation is not sufficient reason to add a Core feature.

## Decision process

- Minor editorial changes may use ordinary pull requests.
- Material or normative changes require a Request for Comments (RFC) and a public review
  period. See [Interim review regime](#interim-review-regime) for what that period currently
  produces and what stands in for the outside review it does not yet draw.
- Stable features should have two independent implementations and conformance cases.
- Maintainers publish the disposition and rationale for an RFC.
- Material objections and minority positions should be recorded rather than silently discarded.

During the research preview, maintainers may reject or remove concepts aggressively. There is no
compatibility promise for `0.x` drafts.

## Interim review regime

The project has one maintainer, Brian Jin ([@kikashy](https://github.com/kikashy)), and no
independent contributors. Elsewhere this document says "maintainers" and speaks of public review
periods, as do [`README.md`](./README.md),
[`docs/origin-and-boundary.md`](./docs/origin-and-boundary.md), and Q40 of [`FAQ.md`](./FAQ.md).
Those describe the intended end state, not today. Today a public review period means a change sits
in public and no one comments, and one maintainer merges their own RFCs with model assistance on the
drafting — a real concentration of judgment.

This section adds an adversarial reading where there is currently none. It is not review breadth.
Breadth means readers with different exposure — users, implementers, operators — and no model has
any.

### Practice

The precedent is partial. RFC 0006
([pull request 9](https://github.com/Judgment-Pack/judgment-pack-spec/pull/9)) records the review
prompt verbatim, the unedited findings of an OpenAI Codex review of a Claude-drafted RFC, the
response, and a maintainer disposition; the bar stated at the time was a different model family, not
a different vendor. RFC 0007 and the reference runtime's architecture decision records carry no such
record and were merged without one. The requirement below is prospective: it applies to work opened
after 2026-07-27.

- **Scope.** Every RFC in this repository. The maintainer applies the same rule to material
  architecture decision records in the reference runtime — a *material* ADR being one that changes a
  public surface, a documented claim, or conformance-relevant behavior — but this document governs
  only this repository, and that obligation binds `judgment-pack-runtime` only once its own
  `docs/adr/README.md` records it. Runtime ADRs are written after the decision and are immutable
  once accepted, so the review attaches to the pull request that makes the decision, not to the ADR
  text.
- **Cross-vendor review.** At least one adversarial review by a model from a **different vendor**
  than any model that assisted the drafting.
- **Record.** The review is recorded in the pull request, in a comment beginning with the heading
  `## Cross-vendor adversarial review`, so that compliance is greppable from pull-request history.
  The record names the drafting model or models and the reviewing model, each with vendor, model
  identifier, and date; quotes the review prompt verbatim; and includes the reviewing model's
  complete unedited output, including findings the maintainer rejects. If more than one review was
  run, every run is linked and the record states that no run was discarded.
- **Disposition.** Every finding receives a written maintainer disposition: accept, reject with
  reason, or defer with the condition that would reopen it.
- **Pull requests only.** No RFC, and no material ADR, is merged except through a pull request
  carrying the review and the dispositions. Direct pushes to the default branch are not used for
  either.

### Limits

Model review is not decision authority. It is not authoritative; the disposition of the maintainer
named above is, and they are accountable for it. Known weaknesses:

- The reviewing model is selected, prompted, transcribed, and dispositioned by the party being
  reviewed. Nothing here prevents re-running a review until it is agreeable. Only the recorded
  prompt, the complete output, and the link to every run make that visible, and only a reader who
  checks makes it cost anything.
- Cross-vendor review is intended to decorrelate some vendor-specific blind spots. The effect is
  unmeasured, and models from different vendors still share training data, tuning conventions, and
  benchmark culture, so the blind spots they share are not vendor-shaped.
- A reviewing model reading a model-assisted draft may find it unusually agreeable.
- No model review represents a user, an implementer, or an operator, or reports a cost borne by one.
- No model is accountable for the finding it failed to make.
- The maintainer also authors the reference runtime, `judgment-pack-runtime`. No runtime is required
  to interpret a pack, but that runtime is not independent of this specification: RFC 0006 names it
  as one of the two independent implementations its evidence bar requires, and two implementations
  by one author are not independent evidence.

Model reviews are not external design reviews. They do not count toward any exit evidence in
[`ROADMAP.md`](./ROADMAP.md).

Outside review is not made unnecessary by this regime. It is what the regime is waiting for.

### When a second maintainer arrives

Two maintainers do not by themselves end this regime; both exit conditions below must hold. On
arrival:

- an RFC is no longer merged by its own author, and the other maintainer records the disposition;
- recusal under [Maintainer conflicts](#maintainer-conflicts) becomes available, and the
  single-maintainer substitute recorded there lapses;
- the cross-vendor review requirement continues until this section is removed.

### Exit criteria

Recorded in advance. This regime ends when both of the following hold.

1. The project has at least two maintainers with merge rights who are independent of each other:
   distinct legal persons, not employed by or contracting with the same entity and not funded by it
   for this work, each with at least five merged non-trivial commits authored before being granted
   merge rights.
2. Substantive comment on RFCs has come from at least two distinct third-party GitHub accounts,
   belonging to neither maintainer, across at least two separate RFCs.

Both conditions are countable from public repository history. Two things in them are not observable
from outside: whether comment is substantive, and whether a commenter was solicited. The maintainer
states both with the evidence, and an outside reader can dispute either on the removal pull request.

A maintainer removes this section by a governance RFC citing the evidence for each condition,
disposed under the process in this document. The RFC may be short. Deleting the project's only
standing accountability regime is a governance change, so it takes the route this document requires
for one. This section was itself added by ordinary pull request rather than by RFC: it removes
nothing and constrains only the maintainer, and its removal does the opposite.

Dropping the `-draft` suffix is governed by [`ROADMAP.md`](./ROADMAP.md) Stage 3 and
[`VERSIONING.md`](./VERSIONING.md). This section neither restates that bar nor supplies a second,
weaker one.

## Maintainer conflicts

A maintainer with a direct commercial or personal conflict should disclose it. Another maintainer
should lead disposition when practical. With one maintainer that is not available: the conflict is
disclosed in the pull request and named in the disposition. This substitute lapses when a second
maintainer arrives (see [Interim review regime](#interim-review-regime)).

## Evolving the governance model

The specification intends to evolve through real implementations and interoperability feedback. As
independent conforming implementations, production adopters, and sustained outside contribution
accumulate, the maintainer intends to formalize multi-party governance. The near-term trigger is the
exit criteria in [Interim review regime](#interim-review-regime).

That transition should be proposed through a public governance RFC covering technical steering,
release authority, trademarks, intellectual property, and the project's long-term home. Until the
supporting implementation and contribution base exists, adding heavier governance ceremony would
create process without creating independent technical power. The recorded model review required by
[Interim review regime](#interim-review-regime) is the deliberate exception: it creates a record
rather than a body, confers authority on no one, and costs third parties nothing.

## Participate

Participation is open. No membership or commercial relationship is required to propose changes,
report problems, or contribute implementations.

- Source and specification: <https://github.com/Judgment-Pack/judgment-pack-spec>
- Issue tracker: <https://github.com/Judgment-Pack/judgment-pack-spec/issues>
- Discussion: [join the Judgment Pack Slack](https://join.slack.com/t/judgment-pack/shared_invite/zt-44qrd47ok-o_~Vk3BFDzsN~EGAPkeQBw)
- Contributing guide: [./CONTRIBUTING.md](./CONTRIBUTING.md)
- Code of conduct: [./CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)
- Roadmap: [./ROADMAP.md](./ROADMAP.md)

# Governance

## Status: early research preview

Judgment Pack is an open, vendor-neutral specification developed in public. Today it has a single
maintainer and no independent contributors (see [Interim review regime](#interim-review-regime)).
It is not controlled by any required commercial runtime, though the reference runtime is written by
the same maintainer and is not independent evidence of interoperability. Conforming
implementations may be open-source or proprietary; conformance is defined by the specification and
its conformance cases, not by any single vendor's product.

The current status is an early research preview (`0.2.0-draft`). There is no compatibility guarantee
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

This section is the operative text proposed by [RFC 0009](./rfcs/0009-interim-review-regime.md),
which is its design record, adopted 2026-07-27. The regime was introduced through the RFC process it
amends; two adversarial reviews of the proposal, with a written disposition for every finding, are
recorded on that RFC's pull request, and the maintainer's merge of that pull request is the
acceptance.

### Practice

The precedent is partial. RFC 0006
([pull request 9](https://github.com/Judgment-Pack/judgment-pack-spec/pull/9)) records the review
prompt verbatim, the unedited findings of an OpenAI Codex review of a Claude-drafted RFC, the
response, and a maintainer disposition; the bar stated at the time was a different model family, not
a different vendor. RFC 0007 and the reference runtime's architecture decision records carry no such
record and were merged without one.

- **Scope.** The pull request adopting [RFC 0009](./rfcs/0009-interim-review-regime.md) and every
  pull request merged after it, where that pull request creates, materially amends, or dispositions
  an RFC in this repository. The test is commit-relative, not date-relative: the adopting pull
  request is inside its own scope rather than the last one exempt from it, and no merge falls into a
  same-day gap. Predating the requirement is not an exemption: RFCs 0001–0007 acquire it the next
  time such a pull request touches them, and an RFC opened early and completed later is covered by
  the merge, not by the opening date. Editorial pull requests — typography, links, formatting — are
  not covered.
- **Runtime.** The maintainer applies the same rule to material decisions in the reference runtime,
  with or without an architecture decision record. A decision is *material* when it changes a public
  surface, a documented claim, conformance-relevant behavior, the security posture, or a dependency
  boundary. Not writing an ADR does not make a decision immaterial. This document binds only this
  repository; the runtime's adopting text is its
  [`docs/adr/README.md`](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/README.md),
  and the obligation exists there because that text is merged — so this bullet now describes a rule
  the runtime is under rather than an intention. That text also requires every runtime pull request to
  declare its material-decision impact, so a change treated as immaterial is classified out loud and
  can be disputed rather than passing in silence. Runtime ADRs are written after the decision and
  are immutable once accepted, so the review attaches to the pull request that makes the decision,
  not to the ADR text.
- **Cross-vendor review.** At least one adversarial review by a model from a **different vendor**
  than any model that assisted the drafting. *Vendor* means the organization that controls the
  model's weights and training — the developer, not the API host and not a reseller. Two hosted
  copies of the same model share lineage and are the same vendor here, whatever the invoice says.
  *Assisted the drafting* means generated or revised text that survives in the merged artifact, or
  planning, analysis, structure, or design choices supplied by a model and relied on to produce it.
  Paraphrase does not launder assistance: a model that shaped the outline, chose the arguments, or
  settled a design question assisted the drafting even when none of its sentences survive. Applying
  an accepted finding in the maintainer's own words does not make the reviewer a drafter; adopting
  reviewer-generated text verbatim does not invalidate the review that produced it, but the record
  says where that happened. A case the maintainer cannot call is declared in the record, and the
  declaration is an attestation like the others below.
- **Record.** The review is recorded in the pull request, in a comment beginning with the heading
  `## Cross-vendor adversarial review`. The record names the drafting model or models and the
  reviewing model, each with vendor, model identifier, and date; states the commit SHA that was
  reviewed and what repository context the reviewer was given — files, diff range, tools, whether it
  could read the working tree; quotes the review prompt verbatim; and includes the reviewing model's
  complete unedited output, including findings the maintainer rejects. If more than one review was
  run, every run is linked and the record states that no run was discarded.
- **Change after review.** A material change to the artifact after the reviewed SHA requires a fresh
  review of the later SHA. One class of change is excepted: a change that implements a dispositioned
  finding of a review already recorded on the same pull request, which is covered by that finding's
  disposition and by the commit the disposition links. Without the exception the requirement never
  terminates — every review provokes changes and every change provokes a review — and the exception
  opens no general escape, because it is pinned to specific recorded findings: a material change no
  recorded finding asked for is not covered by one. A note in place of a review is available only
  for non-material changes — typography, links, formatting — and the note says what changed.
- **Disposition.** Every finding receives a written maintainer disposition: accept, accept in part,
  reject with reason, or defer with the condition that would reopen it. Every accepted finding links
  to the commit that implements it or to the tracked follow-up that will.
- **Redaction.** The unedited-output requirement yields to disclosure risk and to nothing else. If
  the raw output contains an exploitable vulnerability, personal data, or credentials, the published
  record may redact exactly that portion. The redaction is marked in place, its reason class stated
  — vulnerability, personal data, or credential — the unredacted original preserved privately, and
  the full text published after remediation when it is safe to publish, handled under
  [`SECURITY.md`](./SECURITY.md). A finding the maintainer finds unwelcome is not a
  disclosure risk.
- **Pull requests only.** No RFC, and no material runtime decision, is merged except through a pull
  request carrying the review and the dispositions. Direct pushes to the default branch are not used
  for either.

### What the record cannot show

The heading convention above makes records *findable*. It does not make compliance *provable*. The
record makes the maintainer's claims discoverable; it cannot verify them. These stay attestations by
the reviewed party:

- which models actually assisted the drafting, including assistance that left no surviving text;
- that the quoted prompt is the complete input, including system instructions, attached context, and
  tool output;
- that the quoted output is complete and unedited apart from a marked redaction;
- that no run was discarded.

Pull-request comments are editable and deletable by their author, so the comment is not the anchor.
The reviewed commit SHA is: the artifact under review is fixed in Git history even when the text
describing it is not. A reader who wants more than an attestation would need provider-side logs,
which this project does not publish and does not claim to.

### Limits

Model review is not decision authority. It is not authoritative; the disposition of the maintainer
named above is, and they are accountable for it. Known weaknesses:

- The reviewing model is selected, prompted, transcribed, and dispositioned by the party being
  reviewed. Nothing here prevents re-running a review until it is agreeable. The recorded prompt, the
  complete output, and the link to every run are what would make that visible — and every one of them
  is supplied by the same party, per
  [What the record cannot show](#what-the-record-cannot-show).
  Only a reader who checks makes any of it cost anything.
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

*Arrival* is the grant of merge rights to a second distinct legal person, whether or not that person
is independent of the first under the exit criteria below. The bullets here trigger on the grant.
Two maintainers do not by themselves end this regime: the exit criteria still require independence,
and ending the regime still takes the removal RFC. On arrival:

- an RFC is no longer merged by its own author, and the other maintainer records the disposition;
- recusal under [Maintainer conflicts](#maintainer-conflicts) becomes available, and
  the single-maintainer substitute recorded there lapses;
- with exactly two maintainers, the non-author can block everything by being absent. If the
  non-author is conflicted, or does not respond within 14 days of a review request, the author
  merges, and the disposition states that no second maintainer reviewed it and why;
- the cross-vendor review requirement continues until this section is removed.

### Exit criteria

Recorded in advance. They are prerequisites for opening the RFC that removes this section, not a
self-executing end: this regime is in force until that RFC merges, whether or not the conditions
hold on any given day.

1. The project has at least two maintainers with merge rights who are independent of each other:
   distinct legal persons, not employed by or contracting with the same entity and not funded by it
   for this work. A maintainer added after this section is adopted must have at least five merged
   non-trivial commits authored before their first grant of merge rights. The founding maintainer
   named above is exempt from that count: they held merge rights before there was anything to merge,
   and a rule they could satisfy by revoking and re-granting their own rights would measure nothing.
2. Substantive comment on RFCs has come from at least two distinct third-party GitHub accounts,
   belonging to neither maintainer, across at least two separate RFCs. Comment is *substantive* when
   it engages the technical substance and receives a written disposition; a typo report, an
   endorsement, or an aside nobody answered is not. The two commenters are identified natural
   persons, not accounts created for the purpose.

What those conditions measure is independent participation: that merge rights are held by more than
one person, and that someone who is neither maintainer has engaged the substance and been answered
in public. They do not measure breadth. Nothing here counts users, implementers, or operators, or
asks what exposure a commenter argues from, so on the day this regime exits the project still has no
measure of the breadth that the second paragraph above says model review is not. Multi-party
governance is what that is for; this regime ends where that work starts.

Part of this is recorded publicly as it happens, and part is not. Nomination and every grant of merge
rights are recorded in this repository on the day they occur, so the number of maintainers, the date
of each grant, and the commits preceding it are checkable by anyone. Independence is not checkable:
employment, contracting, funding, and whether two accounts are two people cannot be established from
repository history, and Git authorship metadata is not identity. Whether a comment is substantive is
a judgment, and whether a commenter was solicited is invisible from outside. Those are
**attestations**. The maintainer states each one, with the evidence relied on, in the removal RFC,
and an outside reader can dispute any of them there.

A maintainer removes this section by a governance RFC citing the evidence for each condition,
disposed under the process in this document. The RFC may be short. It is not opened before both
conditions hold, and until it merges every requirement above applies unchanged. Deleting the
project's only standing accountability regime is a governance change, so it takes the route
this document requires for one. This regime was introduced by that route — through
[RFC 0009](./rfcs/0009-interim-review-regime.md), under the process it amends, with its adversarial
reviews and a disposition for every finding recorded on that RFC's pull request — and its removal
takes the same route.

**Reactivation.** After removal, this regime reactivates on the day fewer than two independent
maintainers hold merge rights — by resignation, by revocation of rights, by loss of independence, or
by inactivity — automatically, whether or not anyone announces it. A maintainer with no authored
commit, recorded review, or recorded disposition in the preceding 90 days does not count toward the
two. Counting accounts is not the test: two accounts held by one legal person, or held by two people
no longer independent of each other, were never two maintainers for this purpose. The section is
restored to this document by ordinary pull request citing this clause, and it binds from the day the
condition returned, not from the day that pull request merges. Restoring an accountability regime
whose precondition has returned needs no RFC; removing one does.

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

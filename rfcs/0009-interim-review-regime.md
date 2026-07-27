# RFC 0009: The interim review regime

- Status: Draft
- Type: Process
- Created: 2026-07-27

> This is an open proposal, not part of the specification, and it changes no normative text. See
> [RFC 0000](0000-rfc-process.md) for the process it follows. It exists because an earlier attempt
> to add this regime by ordinary pull request was reviewed adversarially and the first finding was
> that the attempt violated the process it was strengthening. That finding was accepted; this is the
> RFC it demanded. The regime's operative text is [the proposed section](#specification) below, which
> lands in [`GOVERNANCE.md`](../GOVERNANCE.md) on merge.

## Summary

Add a section to `GOVERNANCE.md` that states, without softening, what review a Judgment Pack RFC
actually receives today: none from outside. In place of the outside review the project does not yet
draw, require a recorded adversarial review of every RFC by a model from a different vendor than any
model that assisted the drafting, a written maintainer disposition for every finding, and a public
record of both. Record in advance the conditions under which the requirement ends, name the parts of
those conditions that are attestations rather than facts, and make the regime reactivate on its own
if the conditions that ended it stop holding.

The section constrains one person. That is not an argument for adopting it outside the process — it
is the reason the constraint is worth writing down while there is still only one person to bind.

## Problem

The project has one maintainer and no independent contributors. `GOVERNANCE.md` says "maintainers"
and describes public review periods; `README.md`, `docs/origin-and-boundary.md`, and Q40 of `FAQ.md`
said the same or implied community contributors. Those sentences describe the intended end state.
Today a public review period means a change sits in public and no one comments, and the maintainer
merges their own RFCs having drafted them with model assistance.

Three consequences follow, and none of them is fixed by wanting outside review harder:

1. **No adversarial reading.** A design is disposed by the person who wrote it, against no
   opposition. The RFC process produces a record of one mind.
2. **Undisclosed concentration.** Documents that assert plural maintainers make the concentration
   invisible to a reader deciding whether to depend on the specification.
3. **No stated end.** A single-maintainer project with no written exit condition can stay one
   indefinitely and never have to say so.

Model review does not solve (1). It substitutes for it, badly and visibly, and the substitution has
to be labeled as such everywhere it appears or it becomes a claim of review breadth the project has
not earned.

## Evidence

The precedent is partial and already in the repository. RFC 0006
([pull request 9](https://github.com/Judgment-Pack/judgment-pack-spec/pull/9)) carries the review
prompt verbatim, the complete unedited findings of an OpenAI Codex review of a Claude-drafted RFC,
the response, and a maintainer disposition. The bar stated at the time was a different model
*family*, not a different vendor. RFC 0007 and the reference runtime's architecture decision records
carry no such record and were merged without one. So the practice exists, was useful once, and was
not applied consistently — which is what a written requirement is for.

This RFC is its own second data point. The proposal was reviewed by OpenAI gpt-5.6-sol against a
Claude-drafted amendment; the review returned ten findings and a verdict of *do not merge as
written*. Six were accepted, two accepted in part, one deferred, and the parts rejected are rejected
with reasons on this pull request. The review found real defects — a self-exemption, an effective
date that permanently excused every existing RFC, an audit claim the record could not support. A
regime whose first review changes it substantially is at least measuring something.

## Specification

The text below lands in `GOVERNANCE.md` as `## Interim review regime`. It is reproduced here
verbatim with three mechanical differences: heading depth is one level lower, relative links are
rewritten for this directory, and the section's reference to this RFC is a self-reference here.
Where the two ever diverge, the merged `GOVERNANCE.md` is the operative text and this copy is stale.

### Interim review regime

The project has one maintainer, Brian Jin ([@kikashy](https://github.com/kikashy)), and no
independent contributors. Elsewhere that document says "maintainers" and speaks of public review
periods, as do [`README.md`](../README.md),
[`docs/origin-and-boundary.md`](../docs/origin-and-boundary.md), and Q40 of [`FAQ.md`](../FAQ.md).
Those describe the intended end state, not today. Today a public review period means a change sits
in public and no one comments, and one maintainer merges their own RFCs with model assistance on the
drafting — a real concentration of judgment.

This section adds an adversarial reading where there is currently none. It is not review breadth.
Breadth means readers with different exposure — users, implementers, operators — and no model has
any.

This section is the operative text proposed by [RFC 0009](0009-interim-review-regime.md), which is
its design record. The regime was introduced through the RFC process it amends, and the adversarial
review of the proposal, with a written disposition for every finding, is recorded on that RFC's pull
request.

#### Practice

The precedent is partial. RFC 0006
([pull request 9](https://github.com/Judgment-Pack/judgment-pack-spec/pull/9)) records the review
prompt verbatim, the unedited findings of an OpenAI Codex review of a Claude-drafted RFC, the
response, and a maintainer disposition; the bar stated at the time was a different model family, not
a different vendor. RFC 0007 and the reference runtime's architecture decision records carry no such
record and were merged without one.

- **Scope.** Every pull request merged after 2026-07-27 that creates, materially amends, or
  dispositions an RFC in this repository. Predating the requirement is not an exemption: RFCs
  0001–0007 acquire it the next time such a pull request touches them, and an RFC opened early and
  completed later is covered by the merge, not by the opening date. Editorial pull requests —
  typography, links, formatting — are not covered.
- **Runtime.** The maintainer applies the same rule to material decisions in the reference runtime,
  with or without an architecture decision record. A decision is *material* when it changes a public
  surface, a documented claim, conformance-relevant behavior, the security posture, or a dependency
  boundary. Not writing an ADR does not make a decision immaterial. This document binds only this
  repository; the runtime's adopting text is its
  [`docs/adr/README.md`](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/README.md),
  and the obligation exists there only once that text is merged. Until then this bullet states an
  intention, not a rule the runtime is under. Runtime ADRs are written after the decision and are
  immutable once accepted, so the review attaches to the pull request that makes the decision, not to
  the ADR text.
- **Cross-vendor review.** At least one adversarial review by a model from a **different vendor**
  than any model that assisted the drafting. *Vendor* means the organization that controls the
  model's weights and training — the developer, not the API host and not a reseller. Two hosted
  copies of the same model share lineage and are the same vendor here, whatever the invoice says.
  *Assisted the drafting* means generated or revised text that survives in the merged artifact.
  Applying an accepted finding in the maintainer's own words does not make the reviewer a drafter;
  adopting reviewer-generated text verbatim does not invalidate the review that produced it, but the
  record says where that happened.
- **Record.** The review is recorded in the pull request, in a comment beginning with the heading
  `## Cross-vendor adversarial review`. The record names the drafting model or models and the
  reviewing model, each with vendor, model identifier, and date; states the commit SHA that was
  reviewed and what repository context the reviewer was given — files, diff range, tools, whether it
  could read the working tree; quotes the review prompt verbatim; and includes the reviewing model's
  complete unedited output, including findings the maintainer rejects. If more than one review was
  run, every run is linked and the record states that no run was discarded.
- **Change after review.** If the artifact changes materially after the reviewed SHA, the pull
  request carries either a fresh review of the later SHA or a disposition note saying specifically
  why the change does not warrant one. "Nothing substantive changed" is not such a note unless it
  says what changed.
- **Disposition.** Every finding receives a written maintainer disposition: accept, accept in part,
  reject with reason, or defer with the condition that would reopen it. Every accepted finding links
  to the commit that implements it or to the tracked follow-up that will.
- **Redaction.** The unedited-output requirement yields to disclosure risk and to nothing else. If
  the raw output contains an exploitable vulnerability, personal data, or credentials, the published
  record may redact exactly that portion. The redaction is marked in place, its reason class stated
  — vulnerability, personal data, or credential — the unredacted original preserved privately, and
  the full text published after remediation when it is safe to publish, handled under
  [`SECURITY.md`](../SECURITY.md). A finding the maintainer finds unwelcome is not a disclosure risk.
- **Pull requests only.** No RFC, and no material runtime decision, is merged except through a pull
  request carrying the review and the dispositions. Direct pushes to the default branch are not used
  for either.

#### What the record cannot show

The heading convention above makes records *findable*. It does not make compliance *provable*. The
record makes the maintainer's claims discoverable; it cannot verify them. These stay attestations by
the reviewed party:

- which models actually assisted the drafting;
- that the quoted prompt is the complete input, including system instructions, attached context, and
  tool output;
- that the quoted output is complete and unedited apart from a marked redaction;
- that no run was discarded.

Pull-request comments are editable and deletable by their author, so the comment is not the anchor.
The reviewed commit SHA is: the artifact under review is fixed in Git history even when the text
describing it is not. A reader who wants more than an attestation would need provider-side logs,
which this project does not publish and does not claim to.

#### Limits

Model review is not decision authority. It is not authoritative; the disposition of the maintainer
named above is, and they are accountable for it. Known weaknesses:

- The reviewing model is selected, prompted, transcribed, and dispositioned by the party being
  reviewed. Nothing here prevents re-running a review until it is agreeable. The recorded prompt, the
  complete output, and the link to every run are what would make that visible — and every one of them
  is supplied by the same party, per
  [What the record cannot show](../GOVERNANCE.md#what-the-record-cannot-show). Only a reader who
  checks makes any of it cost anything.
- Cross-vendor review is intended to decorrelate some vendor-specific blind spots. The effect is
  unmeasured, and models from different vendors still share training data, tuning conventions, and
  benchmark culture, so the blind spots they share are not vendor-shaped.
- A reviewing model reading a model-assisted draft may find it unusually agreeable.
- No model review represents a user, an implementer, or an operator, or reports a cost borne by one.
- No model is accountable for the finding it failed to make.
- The maintainer also authors the reference runtime, `judgment-pack-runtime`. No runtime is required
  to interpret a pack, but that runtime is not independent of this specification: RFC 0006 names it
  as one of the two independent implementations its evidence bar requires, and two implementations by
  one author are not independent evidence.

Model reviews are not external design reviews. They do not count toward any exit evidence in
[`ROADMAP.md`](../ROADMAP.md).

Outside review is not made unnecessary by this regime. It is what the regime is waiting for.

#### When a second maintainer arrives

Two maintainers do not by themselves end this regime; both exit conditions below must hold. On
arrival:

- an RFC is no longer merged by its own author, and the other maintainer records the disposition;
- recusal under [Maintainer conflicts](../GOVERNANCE.md#maintainer-conflicts) becomes available, and
  the single-maintainer substitute recorded there lapses;
- with exactly two maintainers, the non-author can block everything by being absent. If the
  non-author is conflicted, or does not respond within 14 days of a review request, the author
  merges, and the disposition states that no second maintainer reviewed it and why;
- the cross-vendor review requirement continues until this section is removed.

#### Exit criteria

Recorded in advance. This regime ends when both of the following hold.

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

Part of this is recorded publicly as it happens, and part is not. Nomination and every grant of merge
rights are recorded in this repository on the day they occur, so the number of maintainers, the date
of each grant, and the commits preceding it are checkable by anyone. Independence is not checkable:
employment, contracting, funding, and whether two accounts are two people cannot be established from
repository history, and Git authorship metadata is not identity. Whether a comment is substantive is
a judgment, and whether a commenter was solicited is invisible from outside. Those are
**attestations**. The maintainer states each one, with the evidence relied on, in the removal RFC,
and an outside reader can dispute any of them there.

**Reactivation.** If the maintainers with merge rights fall below two — resignation, inactivity, or
loss of independence — this regime reactivates on that day, automatically, whether or not anyone
announces it. The section is restored to this document by ordinary pull request citing this clause.
Restoring an accountability regime whose precondition has returned needs no RFC; removing one does.

A maintainer removes this section by a governance RFC citing the evidence for each condition,
disposed under the process in this document. The RFC may be short. Deleting the project's only
standing accountability regime is a governance change, so it takes the route this document requires
for one. This regime was introduced by that route — through
[RFC 0009](0009-interim-review-regime.md), under the process it amends, with its adversarial review
and a disposition for every finding recorded on that RFC's pull request — and its removal takes the
same route.

Dropping the `-draft` suffix is governed by [`ROADMAP.md`](../ROADMAP.md) Stage 3 and
[`VERSIONING.md`](../VERSIONING.md). This section neither restates that bar nor supplies a second,
weaker one.

## Companion changes

- `rfcs/0000-rfc-process.md` — the Review section states the requirement and its scope, and points
  here and to `GOVERNANCE.md` for the detail.
- `README.md`, `FAQ.md` Q40, `docs/origin-and-boundary.md` — three sentences asserted plural
  maintainers and community contributors as present fact. Corrected to one maintainer, no independent
  contributors yet, each linking to the regime. This is the part of the change that costs the project
  something to say.
- `judgment-pack-runtime`, `docs/adr/README.md` — the runtime's own adopting text, merged separately
  in that repository. Until it merges, the runtime is under no obligation from this RFC.

## Alternatives

- **Do nothing.** Keep the RFC process as written and wait for outside review. Honest about the
  absence only by omission: the documents asserting plural maintainers would have stayed wrong, and a
  reader would have to infer the concentration from commit history. Rejected — the cost of the
  disclosure is the point of it.
- **Label the whole project "research" and say nothing more specific.** A blanket label is cheaper
  and needs no process. Rejected: the project already carries more precise maturity markers —
  `0.1.0-draft`, the `ROADMAP.md` stages, Core §3.4's prohibition on evaluator-conformance claims,
  the research-preview status in `GOVERNANCE.md` — and those attach to security and compatibility
  claims where the distinction actually decides something. A blanket label would blur markers that
  currently discriminate, and it would say nothing at all about who reviews a decision.
- **Wait for a second maintainer and adopt real peer review then.** The correct end state, and the
  one the exit criteria point at. Rejected as a plan for now: it makes the accountability regime
  conditional on the event that would relax the need for it.
- **Stand up a governance body, technical steering group, or advisory reviewers now.** Rejected in
  `GOVERNANCE.md` already, for the reason recorded there: heavier ceremony with no independent
  technical power behind it creates process, not accountability. This regime is the deliberate
  exception because it creates a record rather than a body, confers authority on no one, and costs
  third parties nothing.
- **Claim stronger auditability — publish provider-side logs, or commit an immutable review artifact
  hashed into the repository.** Would convert some attestations into evidence. Not adopted now:
  provider logs are not exportable in a form a third party could trust more than the transcript, and
  an in-repository artifact committed by the same party is the same attestation in a different file.
  The honest move was to name the attestations as attestations; see the unresolved question below.
- **Require reviewers from at least two relevant constituencies before exit.** Proposed by the
  review (finding 6). Rejected: at this project's scale "constituency" is unfalsifiable — the
  maintainer would classify the commenters — and the requirement would read as rigor while adding
  none. The reactivation clause and the written-disposition test carry the weight instead.
- **Require every runtime pull request to declare its ADR impact.** Proposed by the review
  (finding 8). Rejected: a per-PR declaration in a one-contributor repository is a checkbox its own
  author ticks. Revisit under multi-party governance.

## Compatibility

No normative effect. No pack, schema, corpus case, `specVersion`, or conformance claim changes, and
no implementation has anything to do. The effect is procedural and falls almost entirely on the
maintainer: more work per RFC, a public record of every review, and a documented way to be caught
skipping one.

For contributors, the requirement adds a step the maintainer performs, not one they do. An outside
contributor's RFC still gets the review; the maintainer runs and records it.

`rfcs/0000-rfc-process.md` gains a paragraph in its Review section. Nothing in the required-sections
list, the statuses, or the evidence bar changes.

## Security and privacy

The requirement to publish complete unedited review output collides with responsible disclosure: an
adversarial reviewer told to attack a specification may produce a working attack, echo credentials or
personal data that leaked into its context, or describe an unsafe operational detail.
[`SECURITY.md`](../SECURITY.md) directs exactly that material to private reporting.

The redaction clause is the narrowest carve-out that resolves this: only for an exploitable
vulnerability, personal data, or a credential; only the offending portion; marked in place with its
reason class so the reader sees that something was withheld and what kind of thing it was; original
preserved privately; full text published after remediation. The residual risk is obvious and worth
stating — the carve-out is invoked by the party the record exists to constrain, and "this portion was
a vulnerability" is itself an attestation.

Second-order risk: a published review record advertises the project's known weak points to anyone
reading it. That is accepted. A defect the maintainer has already disposed of in public is less
dangerous than one only the maintainer knows about.

## Unresolved questions

- **Does this measure anything?** The claim that cross-vendor review decorrelates blind spots is
  unmeasured, and this project cannot measure it — one maintainer, a handful of RFCs, no control
  group. It stays a stated assumption.
- **Attestation versus evidence.** Four claims in the record are attestations. Whether any of them
  can be converted to evidence a third party can check — signed provider transcripts, a
  reproducible-run protocol, a witness — is open, and the answer will probably come from outside this
  project.
- **Release authority is stated in two numbers.** `FAQ.md` Q38 says a maintainer tag and release
  establishes a release; `VERSIONING.md` says releases are published by "the maintainers". The
  mismatch predates this RFC and is not resolved here — fixing it means deciding whether a release
  needs one maintainer, all of them, or a non-author, which is a multi-party governance question.
  Deferred to the governance RFC named in `GOVERNANCE.md` under *Evolving the governance model*.
- **What "arrival" of a second maintainer means.** The transition bullets trigger on arrival, which
  is not defined against the independence criteria in the exit conditions. A second maintainer who
  does not yet satisfy them still ends author-merges-own-RFC. That is deliberate but under-specified.
- **Constituency and per-PR ADR impact.** Both rejected above at current scale, both worth revisiting
  when there is more than one contributor to spread the cost across.
- **Reactivation is self-executing and self-noticed.** Nothing external observes a drop below two
  maintainers. If the regime reactivates and nobody restores the section, the failure looks exactly
  like compliance.

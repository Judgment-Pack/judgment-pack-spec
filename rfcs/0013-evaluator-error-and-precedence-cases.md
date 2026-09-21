# RFC 0013: The first evaluator error and precedence cases

- Status: Accepted
- Type: Specification-track (evaluation conformance suite)
- Created: 2026-08-14
- Accepted: 2026-09-21

> **Adoption record.** This RFC is accepted by the single maintainer under the interim review
> regime ([RFC 0009](0009-interim-review-regime.md)). The review of this disposition, with a
> written disposition for every finding, is recorded on the pull request that makes it and under
> [`rfcs/reviews/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/rfcs/reviews).
>
> **A lapse this acceptance discloses, and cannot undo.** This RFC was merged as a Draft on
> 2026-08-15 ([pull request 64](https://github.com/Judgment-Pack/judgment-pack-spec/pull/64))
> without the cross-vendor adversarial review GOVERNANCE requires of a pull request that creates an
> RFC. That was a lapse, not an exemption: the pull request's "verified, not recalled" list is the
> drafter checking its own quotations, which the regime does not count. GOVERNANCE attaches the
> review to the pull request that makes the change, so nothing done now makes pull request 64 have
> met its own merge requirement. What is done now is narrower: the omission is on the record, and
> the review recorded on the accepting pull request — the first this RFC has had — covers the
> proposal as well as the disposition, so the scrutiny the proposal missed is no longer missing.
>
> **What acceptance means here.** The five rows are approved, at draft maturity, for the
> `suiteVersion` after `0.2.0-draft`. They are **staged, not landed**. The `0.2.0-draft` corpus is
> frozen and is byte-for-byte unchanged; no claim against it is affected. The rows and their two
> fixtures are in
> [`conformance/evaluation/staged/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/evaluation/staged),
> held to the released case schema and to the same repository checks as released rows, and they
> move into the manifest when a later `specVersion` opens. Opening one now was weighed and
> declined. `specVersion` is exact, so a new version obliges nobody to migrate — a pack may keep
> the version it declares and stay checkable against it — but it does mean re-declaring every
> artifact in this repository that is to target it, and a fresh claim, against the new corpus, from
> every implementation that chooses to support it. Five rows do not pay for that. A staged row is
> in no corpus and no claim may cite one; the site does not serve the staged directory and no
> release bundle carries it. None of that makes a staged row optional reading: these five restate
> §8.2 and §8.4 as already released, so an implementation that disagrees with one may be violating
> the released contract without having failed a released row.
>
> **The four open questions, decided.**
>
> 1. *Structural or semantic fixture?* Structural, as the proposal suggested. The fixture has one
>    outcome where two are required, every reference in it resolves, and the repository's tests
>    require it to fail for exactly one reason. A semantic sibling is left for a later batch.
> 2. *Does `expectedErrorPhase` belong in the first batch?* No. §8.4 requires an implementation to
>    report the **class** of an evaluation error; it does not require it to report a phase. A row
>    that asserted one would ask for more than the specification does. The sketches below show a
>    phase for three cases; the staged rows assert none.
> 3. *Two fixtures or one?* Two, for the reason the question itself gives: case 3's pack must be
>    otherwise fully conforming, which a shared fixture could not be.
> 4. *Is five the right size?* Five. Cases 1 to 3 reuse the fixtures cases 4 and 5 need, so they
>    cost nothing, and they are what makes a failure of 4 or 5 readable: if case 4 fails, case 1
>    says whether the class is reported at all or only outranked.
>
> **What the repository now checks.** The check that every evidence key a case supplies be
> declared by its pack was unconditional, which no undeclared-key row could pass. It is now
> conditional on the expected class. That admits something it used to refuse — a correctly
> labelled error row — and asks more of everything it still covers: the class a case expects must
> be the one §8.4's fixed order reports for the case's own inputs, read statically from the pack
> fixture, the evidence document and the supported extensions, and a case whose inputs nothing
> refuses may expect none of the three classes decided while admitting them. For the twenty
> released rows it refuses what the old check refused. A row that pinned the intuitive, wrong class
> for case 5 fails in this repository, before any evaluator runs it. The check leaves
> `resource-exhaustion` and implementation-defined classes, which §8.4 permits where no Core class
> applies, to the case schema. The maintainer attests, and this repository does not show, that
> fourteen deliberate breaks — of the staged rows, the fixtures, one released row, the site's
> exclusion and the release bundle's — were each caught, and that one change the check must not
> refuse was not; the list is in the review record.
>
> **Implementation experience, which is not conformance evidence.** On 2026-09-21 both of this
> project's evaluators were given the five staged cases by hand: the reference runtime 0.22.0, and
> the clean-room Python evaluator in
> [judgment-pack-evaluator-experiments](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments)
> at commit `854653ea`. Both reported the expected class on all five, case 5 included, and neither
> emitted a disposition. Three limits. It was run by hand: that repository's agreement harness
> compares dispositions only and does not yet compare error classes. Both evaluators trace to one
> maintainer's direction, which is [RFC 0006](0006-evaluator-conformance.md)'s recorded caveat, so
> their agreement corroborates and does not independently confirm. And both already carried unit
> tests of this order — the Python one with a non-object evidence document where these rows use an
> undeclared member name — so the result was expected; the rows are for the implementation that
> has not been written yet.
>
> This document stays the record of the *proposal*. The sketches below are as proposed; where a
> sketch and a staged row differ — the phase — the staged row and this record govern.

## Summary

The `0.2.0-draft` evaluation suite carries an `expectedErrorClass` result shape and **no case
that uses it**. Twenty rows all expect a disposition. So §8.4 — four error classes and a fixed
precedence order between them — is specified, schema-supported, and entirely unexercised.

This proposes the first five rows to close that, for the **next** suite version. The current
suite is frozen; nothing here rewrites a published row.

## Why this and not more

§8.4's precedence order exists for one reason, stated in the specification itself: *"two
conforming implementations report the same class for the same inputs."* An order that is never
exercised is an order two implementations can disagree about while both passing the suite.

Three of the five cases below are single-condition and would be caught by almost any
implementation. **Two are the point**: inputs where more than one class genuinely applies, and
the row fixes which one is reported. Those are the rows that make the order testable rather
than merely written down.

## The normative order, quoted

From §8.4, and the whole proposal hangs on it:

> The classes are therefore evaluated in one fixed order — `pack-not-conformant`, then
> `malformed-input`, then `unsupported-required-extension`, then `resource-exhaustion` — and
> the first that applies is the class reported.

Note the order is **not** the order the classes are introduced in prose, and
`unsupported-required-extension` sits third rather than second. A reader who guessed the order
from the bullet list would get case 5 wrong. That is a good reason for a row to pin it.

## The five cases

Each sketch is a manifest row plus the inputs it needs. Row shape follows the existing
`conformance/evaluation/manifest.schema.json`: a case carries `expectedDisposition` **or**
`expectedErrorClass`, never both, and `expectedErrorPhase` may accompany a class.

### 1. `error-pack-not-conformant` — a nonconforming pack

| | |
| --- | --- |
| pack | a new fixture, structurally invalid — for example an `outcomes` array of one entry, against §4's minimum of two |
| facts | any conforming document |
| evidence | `{}` |
| expected | `expectedErrorClass: "pack-not-conformant"`, `expectedErrorPhase: "preflight"` |
| §8.4 | the pack input is not a semantically conforming document, failing at the structural layer |

The pack must fail for **one** stated reason. A fixture that is invalid three ways cannot show
which one the class was reported for.

### 2. `error-malformed-input-undeclared-evidence` — an undeclared evidence key

| | |
| --- | --- |
| pack | the existing `packs/data-request-intake-triage.json` |
| facts | the row-1 facts of the current suite |
| evidence | `{"intake-form": "present", "not-a-declared-requirement": "present"}` |
| expected | `expectedErrorClass: "malformed-input"`, `expectedErrorPhase: "preflight"` |
| §8.4 | the evidence-availability input violates §8.2 by carrying an undeclared member name |

Reusing a conforming pack is deliberate: the only thing wrong is the evidence document, so
the row cannot pass by accident through some other defect.

### 3. `error-unsupported-required-extension` — a required extension nobody supports

| | |
| --- | --- |
| pack | a new fixture declaring `metadata.requiredExtensions: ["com.example.unsupported-probe"]` |
| facts | conforming |
| evidence | conforming |
| `supportedExtensions` | `[]` |
| expected | `expectedErrorClass: "unsupported-required-extension"`, `expectedErrorPhase: "preflight"` |
| §8.4 | the unsupported part may be the part that decides, so no disposition may be produced |

The pack must be **otherwise fully conforming**, or case 1's class would win the order and the
row would test nothing about extensions.

### 4. `error-precedence-pack-over-malformed-input` — both apply

| | |
| --- | --- |
| pack | case 1's nonconforming fixture |
| evidence | case 2's undeclared-key document |
| expected | `expectedErrorClass: "pack-not-conformant"` |
| §8.4 | `pack-not-conformant` precedes `malformed-input` |

This is §8.4's own worked example — *"a pack that fails semantic conformance presented with an
evidence document carrying an undeclared key is both"* — turned into a row.

### 5. `error-precedence-malformed-input-over-extension` — the counterintuitive one

| | |
| --- | --- |
| pack | case 3's fixture, conforming but requiring an unsupported extension |
| evidence | case 2's undeclared-key document |
| `supportedExtensions` | `[]` |
| expected | `expectedErrorClass: "malformed-input"` |
| §8.4 | `malformed-input` precedes `unsupported-required-extension` |

**This is the most valuable of the five.** An implementation that checks extension support
while reading the pack — before it ever looks at the evidence document — reports
`unsupported-required-extension` here and is wrong. That is a plausible implementation, not a
contrived one, and nothing in the current suite would catch it.

## What these rows do not establish

- **Not `resource-exhaustion`.** That class needs a documented §10 limit reached while
  evaluating an *admitted* input, so a row for it must carry a limit the suite states. It is
  deliberately out of scope here rather than sketched loosely.
- **Not implementation-defined classes.** §8.4 permits them only where no Core class applies.
  A corpus row cannot require one without naming an implementation, so this suite should not
  try.
- **Not error messages.** §8.4 fixes the class identifier and explicitly leaves transport,
  exit status and wire format undefined; §13 keeps a machine-readable diagnostic contract open.
  A row that asserted message text would be inventing a contract.
- **Not phase, normatively.** `expectedErrorPhase` is optional and no current row uses it. The
  sketches above fill it because it is genuinely known for all five, but a reviewer may
  reasonably say the first error rows should assert class alone and leave phase for later.

## Open questions

*All four were decided at acceptance, 2026-09-21; the adoption record above gives each answer and
its reason. The questions are kept as asked.*

1. **Should case 1's fixture be structurally or semantically invalid?** Structural is easier to
   state and harder to argue about; semantic exercises more of the §3.3 chain. This proposal
   suggests structural for the first row, and a semantic sibling later.
2. **Does `expectedErrorPhase` belong in the first batch at all?** See above.
3. **Two new pack fixtures, or one that both cases can share?** Cases 1 and 3 need packs that
   fail in different ways; sharing would force one fixture to be both nonconforming and
   extension-requiring, which case 3 explicitly must not be.
4. **Is five the right size?** Cases 1–3 are table stakes; 4 and 5 are the ones that pay. A
   smaller batch of just 4 and 5 would be defensible if the single-condition rows are judged
   obvious enough not to need pinning.

## Prior art in this repository

~~The document-conformance corpus already pairs a positive case with the adversarial one that
breaks it — `carrier-duplicate-root-member` beside `carrier-duplicate-nested-member`, for
instance.~~ *Amended 2026-09-21: that example was wrong, and the review at acceptance caught it.
Both cases expect `invalid`; neither is a positive case. They are two complementary negative
cases — the second exists because an implementation that checks duplicate members only at the
root passes the first — and that is the instinct meant here.* Cases 4 and 5 are the same instinct one layer up: the interesting row is not the one
where a rule fires, it is the one where two rules could and the order decides.

## The sections RFC 0000 asks for, supplied at acceptance

[RFC 0000](0000-rfc-process.md) lists ten sections a standards-track RFC should contain. This
proposal was written to a shorter shape and carried three of them under other names — *Summary*;
the specification, as *The five cases*; and unresolved questions, as *Open questions*. The rest are
stated here, briefly, because a suite proposal has little to say under some of them and should say
so rather than leave the heading out.

- **Problem.** §8.4 fixes four error classes and one order between them so that "two conforming
  implementations report the same class for the same inputs", and the `0.2.0-draft` corpus
  exercises none of it. Affected: anyone writing a second evaluator, who can pass every row while
  disagreeing with the first about which class an input calls for.
- **Evidence.** The corpus itself: twenty rows, none using `expectedErrorClass`. The adoption
  record states the implementation experience and its limits.
- **Alternatives.** *No change* — the order stays specified and untested. *Only cases 4 and 5* —
  defensible, and declined for the reason given under the fourth open question. *More rows* — a
  `resource-exhaustion` row needs a limit the suite states, and the malformed inputs other than an
  undeclared member name need a raw-document carrier the next `suiteVersion` is to add; both are
  left out deliberately rather than sketched loosely. *Rows in a runtime's own tests only* — both of
  this project's evaluators already have them, which is exactly why they do not help a third.
- **Compatibility.** None with the released corpus: no published row changes, and a claim against
  `0.2.0-draft` means what it meant. When the rows land, a claim against the later `suiteVersion`
  must pass them, which an implementation that reports the wrong class today would not.
- **Security and privacy.** The fixtures are synthetic. The rows assert a class identifier and no
  message text, so they invite no disclosure through diagnostics. One point bears on safety rather
  than privacy: §8.4 exists so that a refusal is never mistaken for a result. Every one of these
  rows requires an error *instead of* a disposition, so each tests that a refusal happens as well
  as which one it is, and an implementation that answers any of them with a disposition has done
  what §8.4 forbids by name: substituted `unresolved`, `not-applicable` or an outcome for the error.
- **Conformance.** This proposal is conformance cases: three rows that show one class each and two
  boundary rows where the order decides. One of the three is adversarial in effect, which the
  proposal did not notice and the review at acceptance did: case 2's facts are the released
  corpus's first row's, which make the pack's applicability false, so an evaluator that resolves
  applicability before it has admitted the evidence document answers `not-applicable` — a
  disposition where an error is due, and the trap §8.2's order exists to close. The staged row's
  `focus` says so. No row is built to exhaust a limit, and none carries a malformed document the
  carrier cannot yet express.
- **Implementation.** Two evaluators, the reference runtime and the clean-room Python evaluator,
  both by this project and neither independent of the other in RFC 0006's sense. RFC 0000's bar of
  two independent implementations applies to a stable normative feature and is not claimed here;
  these are draft-maturity rows for a draft specification.

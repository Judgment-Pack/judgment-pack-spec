# RFC 0013: The first evaluator error and precedence cases

- Status: Draft
- Type: Specification-track (evaluation conformance suite)
- Created: 2026-08-14

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.

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

The document-conformance corpus already pairs a positive case with the adversarial one that
breaks it — `carrier-duplicate-root-member` beside `carrier-duplicate-nested-member`, for
instance. Cases 4 and 5 are the same instinct one layer up: the interesting row is not the one
where a rule fires, it is the one where two rules could and the order decides.

# Staged evaluation rows

Rows written for the `suiteVersion` **after** `0.2.0-draft`. They are in no corpus.

The [evaluation corpus](../README.md) is frozen when its `specVersion` is released: rows are added
only on the way to a later one, never inside a released one (Core §3.4.1). `0.2.0-draft` is tagged,
so [`manifest.json`](../manifest.json) does not change. This directory is where rows wait — designed,
reviewed, held to the same checks as released rows, and runnable by hand — until a later
`specVersion` opens and they move into the manifest.

## What a staged row is not

- **Not part of any corpus.** A claim of evaluator conformance names a `suiteVersion` and states that
  every row of that corpus passed (Core §3.4.1). No `suiteVersion` contains these rows, so no claim
  may cite them, and what a claim must state about its corpus is unchanged. That is a statement
  about corpus obligations and about nothing wider. Core §3.4 scopes a claim to every applicable
  requirement for every admitted input, not to the rows that happen to exist, and these rows restate
  §8.2 and §8.4 as already released. So an implementation that disagrees with a staged row has not
  failed a released-corpus row, and it may still be violating the released contract. A disagreement
  needs adjudicating, not dismissing: either the row is wrong, which is worth reporting while it can
  still be changed, or the implementation is.
- **Not frozen.** A staged row may still be changed or withdrawn. Its wording is settled enough to
  review, not settled enough to bind.
- **Not evidence of conformance.** Running them is implementation experience. The results recorded in
  [RFC 0013](../../../rfcs/0013-evaluator-error-and-precedence-cases.md) are that and nothing more.
- **Not published with the specification, and in no release bundle.** The project's site serves the
  released corpus and its carrier; its build copies every other JSON file under `conformance/` and
  skips this directory, and a test holds that nothing under it is served. A release bundle is a
  `git archive`, and [`.gitattributes`](../../../.gitattributes) marks this directory
  `export-ignore`, so no bundle carries a staged row whatever is staged when a release is cut. The
  directory is work in progress on `main`, reachable in the repository and nowhere else.

## How a staged row lands

When a later `specVersion` opens, each case moves into [`manifest.json`](../manifest.json) as it
stands, its fixtures move into [`../packs/`](../packs/), the copy of the released fixture is deleted,
and this directory is emptied. A row left here when a release is cut is simply not in that release:
it is held for the one after.

## What is here

[`cases.json`](cases.json) carries `"status": "staged"`, the released version it was staged after, and
`cases`. It deliberately has **no `suiteVersion`**: the rows belong to none. Each case validates
against the released case schema unchanged
([`../manifest.schema.json`](../manifest.schema.json), `#/$defs/case`), so moving a row into the
manifest edits nothing in the row.

A case's `pack` path resolves inside this directory, as a released case's resolves inside the
corpus. [`packs/`](packs/) therefore holds the two new fixtures and a byte-identical copy of the
released `data-request-intake-triage.json`, which one staged case reuses; the repository's tests hold
the copy to the released bytes.

The five cases are the ones [RFC 0013](../../../rfcs/0013-evaluator-error-and-precedence-cases.md)
proposed: the first rows to use `expectedErrorClass`. Three show one §8.4 class each. Two are inputs
to which more than one class applies, where §8.4's fixed order decides which is reported:

| Case | Inputs | Expected class |
| --- | --- | --- |
| `error-pack-not-conformant` | a pack with one outcome where two are required | `pack-not-conformant` |
| `error-malformed-input-undeclared-evidence` | a conforming pack, an evidence document with an undeclared member name | `malformed-input` |
| `error-unsupported-required-extension` | a conforming pack requiring an extension nothing supports | `unsupported-required-extension` |
| `error-precedence-pack-over-malformed-input` | the nonconforming pack **and** the undeclared member name | `pack-not-conformant` |
| `error-precedence-malformed-input-over-extension` | the extension-requiring pack **and** the undeclared member name | `malformed-input` |

The second row does one thing more than its name says. Its facts are the released corpus's first
row's, which make the pack's applicability false, so an evaluator that resolved applicability before
admitting the evidence document would answer `not-applicable` — a disposition where §8.2 requires
the refusal first. Every one of the five is, besides, a test that an error is reported *instead of* a
disposition (§8.4).

None asserts `expectedErrorPhase`. §8.4 requires an implementation to report the class of an
evaluation error; it does not require it to report a phase, so a row that asserted one would ask for
more than the specification does.

## How they are checked

The repository's tests treat staged cases exactly as they treat released ones, through the same
function: the pack fixture conforms unless the case expects `pack-not-conformant`, and the class a
case expects must be the one §8.4's fixed order reports for the case's own inputs — read statically
from the pack fixture, the evidence document and the supported extensions, without an evaluator.
A row that pinned the intuitive, wrong class for the fifth case would fail there. The nonconforming
fixture must fail for exactly one reason, as RFC 0013 requires of it.

The specification repository owns no evaluator, so nothing here runs a case. To run one, give an
evaluator the case's `pack`, its `facts`, its `evidenceAvailability` and its `supportedExtensions`,
and compare the class it reports.

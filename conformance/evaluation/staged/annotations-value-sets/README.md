# Staged evaluation rows for 0.4.0-draft

Evaluation rows for the staged draft Core `specVersion` `0.4.0-draft`, which carries
[RFC 0031](../../../../rfcs/0031-annotations-and-value-sets.md), a Draft. They stand as the
[other staged rows](../README.md) do: in no corpus, not frozen, not evidence of conformance, and in no
release bundle. Unlike those rows, their packs declare the draft selector, so they wait for the
version that carries RFC 0031, not for the next `suiteVersion` of Core `0.3.0`.

The requirement they test is the draft's §8.5
([draft text](../../../../spec/staged/judgment-pack-core-0.4.0-draft.md)): for a semantically
conforming pack `P`, an evaluator produces the result Core §§7–8 give its evaluation form `EF(P)`.
The repository owns no evaluator and computes no disposition. Every expected disposition here is
written by hand from Core §8, and the tests check only that each row could be run and that its pairs
are well formed: no test shows that an expectation is right. Each one is reviewed by hand, and again
by every implementation that runs the rows. A row an implementation disagrees with is a finding
against the row or against the implementation, settled in review, and an expectation is never
replaced by an implementation's output.

## What is here

[`cases.json`](cases.json) carries `"status": "staged"`, `stagedAfter`, the draft selector, and:

- `cases`: 72 rows, each validating against the released case schema unchanged
  ([`../../manifest.schema.json`](../../manifest.schema.json), `#/$defs/case`), each with origin
  `rfc-0031`;
- `heldCases`: one row the released case schema cannot state, with the reason. The supported-extension
  row lists `org.judgmentpack.annotations` in its supported set, which the released schema's
  `extensionName` refuses. It waits until the case schema of the version that carries RFC 0031
  decides whether a supported set may name the extension;
- `pairs`: the 26 groups of rows RFC 0031's static check compares, each with its basis;
- `ownEvaluationForm`: the packs that are their own evaluation form (no set, reference or
  annotation);
- `carriesOver`: the released manifest and the staged rows of Core `0.3.0`, every row of which also
  holds under the draft once its pack's selector bytes are replaced.

[`packs/`](packs/) holds the 33 packs. Four are not semantically conforming, each for one stated reason
(two malformed annotations objects and two unresolved references); the rows that use them expect
`pack-not-conformant`.

## The static check

A pair is a defect in the fixtures, caught before any implementation runs it, unless:

| Basis | Holds when |
| --- | --- |
| `evaluation-form` | the packs differ and their evaluation forms are equal JSON values, and the rows' facts, evidence availability, supported set and expectation are equal |
| `optional-extension` | the evaluation forms differ only in optional vendor extensions, and the rows' inputs and expectation are equal (Core §9: an optional extension does not change Core semantics) |
| `supported-extension-set` | one pack, and the supported sets differ only by `org.judgmentpack.annotations` |

Pairs whose rows share an `id` and `version` compare their whole evaluation forms, so a pair cannot
pass by differing in identity.

## The rows

- **Inertness.** For each kind of result (an outcome, `not-applicable`, `unknown`, `conflict` and
  no match), a pack without annotations, with annotations, and with changed annotations give one
  disposition. A label that spells an outcome id, a reason and a route target changes nothing. Two
  error-class pairs show that annotations change neither `unsupported-required-extension` nor
  `malformed-input`, and a required vendor key beside annotations still counts.
- **Malformed annotations.** Too many keys, and a tab in a string: `pack-not-conformant`.
- **Substitution.** A reference and its inline array give one result: on a match, on no match, on
  an absent path, inside an exception that matches and one that does not, inside `applicability`,
  under `not`, `all` and `any`, with repeated entries, and with entry annotations present, absent or
  changed. An unreferenced set, and `valueSets: []`, change nothing.
- **Equality.** A set of type-distinct values (`1`, `"true"`, `"1.00"`, a decomposed accent, an
  object and an object that looks like a reference) compared under Core §7.4, with no coercion and
  no normalization.
- **Positions, not content.** A literal operand that looks like an annotations object is compared as
  a literal.
- **Resolution.** An unresolved reference, and one naming an outcome's id, are `pack-not-conformant`,
  which §8.4's order reports ahead of a malformed evidence document.

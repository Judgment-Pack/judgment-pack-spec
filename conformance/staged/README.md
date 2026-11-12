# Staged document cases for 0.4.0-draft

Document cases written for the staged draft Core `specVersion` `0.4.0-draft`, which carries
[RFC 0031](../../rfcs/0031-annotations-and-value-sets.md) (annotations and value sets), a Draft. They
are in no corpus.

`0.4.0-draft` is a working selector that no maintainer has assigned and no release carries
([the draft text](../../spec/staged/judgment-pack-core-0.4.0-draft.md), Status). This directory is the
staging location RFC 0031's Evidence bar asks the conformance README to name: outside every released
corpus, held to the repository's checks, and runnable by hand.

## What a staged case is not

- **Not part of any corpus.** The released corpus is [`../manifest.json`](../manifest.json), for Core
  `0.3.0`, and it is unchanged. No claim may cite these cases.
- **Not frozen.** A case may still be changed or withdrawn while RFC 0031 is a Draft.
- **Not evidence of conformance.** Running them is implementation experience.
- **Not published, and in no release bundle.** The site's build skips this directory, the staged
  schema and the staged example, and a test holds that none is served. A release bundle is a
  `git archive`, and [`.gitattributes`](../../.gitattributes) marks this directory, `schema/staged/`,
  `spec/staged/` and `examples/staged/` `export-ignore`. The record-shape catalog lists the staged
  schema, because its `$id` is in the specification's schema namespace, so a bundle that carries
  `catalog/` carries the staged shape's digest and normalized text, never these cases
  ([VERSIONING.md](../../VERSIONING.md), Staged draft Core selector).

## What is here

[`manifest.json`](manifest.json) carries `"status": "staged"`, the released version it was staged
after, the draft selector, and `cases`. Like the staged evaluation rows, it has **no
`suiteVersion`**. Each case validates against the released case schema unchanged
([`../manifest.schema.json`](../manifest.schema.json), `#/$defs/case`), so moving a case into a
manifest edits nothing in the case. Its other members:

- `readerProfiles` names the ceiling profiles a reader runs the cases under. A case whose fixture
  declares `"profile": "extended"` is run by a reader supporting `extended`, which applies the
  extended ceilings of every row of Core §4.1, the six new rows included. No per-profile schema is
  published: the schema carries the `base` maxima, as for every row.
- `carriesOver` names the released manifest whose every case also holds under the draft: its fixture,
  with the root selector's bytes `"specVersion": "0.3.0"` replaced by `"specVersion": "0.4.0-draft"`,
  gives its released result and diagnostic. A fixture that does not declare `0.3.0` is run unchanged
  and keeps its expectation too.
- `newCodes` lists the five conformance codes the draft adds, and `advisoryCodes` the two advisory
  codes RFC 0031 proposes outside conformance and outside the draft's text, which no case states
  (below).

The 139 cases are:

- RFC 0031's staged document table;
- 26 profile cases for its ceilings: each of the six one over under `base`, admitted under
  `extended`, and one over under `extended` (18), and each reached exactly, under `extended` for all
  six and under `base` for the value-set rows (8), since `valid-annotations-at-ceilings` reaches the
  four annotation rows under `base`;
- an empty annotations object on the pack, an outcome and a value-set entry, beside the table's
  case on a rule, so that each annotated position refuses a malformed annotation;
- a number inside an annotation list (RFC 0031 §1.7);
- three cases for its reading of an `extensions` object: two required names found only inside data,
  refused (a reading that takes effect under the draft selector and does not change Core `0.3.0`,
  whose released checker counts such a member; RFC 0031, Compatibility), and a reserved and an
  ungrammatical name inside data, admitted;
  and
- the staged example.

| Directory | Cases | What |
| --- | ---: | --- |
| `carrier/` | 1 | a duplicate key inside an annotations object |
| `structural/` | 85 | refused annotations at every annotated position, sets, entries and references, and the profile ceilings |
| `semantic/` | 10 | unresolved references, a duplicate set id, and a required name found only in data |
| `valid/` | 43 | admitted shapes, every ceiling reached exactly, names inside data, the advisory cases and [the example](../../examples/staged/expense-approval-annotated.json) |

Every fixture is written by hand, with no raw invisible character: each non-ASCII character is a JSON
`\u` escape, and one outside the Basic Multilingual Plane is its surrogate pair, so every fixture is
ASCII. The expectations are RFC 0031's, never recorded from a run.

### Advisory cases

RFC 0031 proposes two advisories, `JPS-VALUE-SET-DUPLICATE-VALUE` and `JPS-VALUE-SET-UNREFERENCED`.
They are kept out of the draft's Core text until RFC 0027 is dispositioned (its Unresolved question
3), and the released case schema admits only the `ruleOverlap` advisory under `advisory/`. So the
cases named `advisory-value-set-*` sit under `valid/` and state only their document result, `valid`,
which is what RFC 0031's Evidence bar asks of an advisory case. When the advisories have a home,
these cases gain their expectations there.

### The code rule

Codes are provisional test metadata. A JSON Schema validator reports the keyword that fails, and
RFC 0031's Codes section maps it to a code. Findings compare as a set of (code, pointer) pairs: a
keyword reported twice at one pointer, as some validators or regular-expression engines report it,
is one finding, and the order of findings carries no meaning. The repository's tests (`tests/test_core_draft.py`) apply
that rule and hold each case to the released corpus's strictness: the expected diagnostic, and no
other outside the outermost `oneOf` that encloses it. One reading is the harness's, stated here so
an implementation can match it: a key the annotated `extensions` object's `propertyNames` refuses is
one refusal, `JPS-STRUCTURE-EXTENSION-NAME` at the key, not one per branch of its `anyOf`.

A non-string inside an annotation list needs no such reading. The refused-character `not` in
`annotationString` holds `"type": "string"` beside its `pattern` (RFC 0031 §1.7), so a number or a
list there fails `type` alone, and the case expects that one `JPS-STRUCTURE-TYPE`.

## How a staged case lands

When the version that carries RFC 0031 opens, each case moves into that version's manifest as it
stands, with the selector the maintainers assign, its fixture moves beside the released ones, and
this directory is emptied.

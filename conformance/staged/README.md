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
  `spec/staged/` and `examples/staged/` `export-ignore`.

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
  codes, outside conformance, that no case states (below).

The 126 cases are RFC 0031's staged document table, the 18 profile cases its ceilings call for, two
cases for its reading of an `extensions` object, and the staged example:

| Directory | Cases | What |
| --- | ---: | --- |
| `carrier/` | 1 | a duplicate key inside an annotations object |
| `structural/` | 81 | refused annotations, sets, entries and references, and the profile ceilings |
| `semantic/` | 10 | unresolved references, a duplicate set id, and a required name found only in data |
| `valid/` | 34 | admitted shapes, the advisory cases and [the example](../../examples/staged/expense-approval-annotated.json) |

Every fixture is written by hand, with no raw invisible character: each non-ASCII character is a JSON
`\u` escape. The expectations are RFC 0031's, never recorded from a run.

### Advisory cases

RFC 0031 proposes two advisories, `JPS-VALUE-SET-DUPLICATE-VALUE` and `JPS-VALUE-SET-UNREFERENCED`.
Where they live is open (its Unresolved question 3), and the released case schema admits only the
`ruleOverlap` advisory under `advisory/`. So the cases named `advisory-value-set-*` sit under
`valid/` and state only their document result, `valid`, which is what RFC 0031's Evidence bar asks of
an advisory case. When the advisories have a home, these cases gain their expectations there.

### The code rule

Codes are provisional test metadata. A JSON Schema validator reports the keyword that fails, and
RFC 0031's Codes section maps it to a code. The repository's tests (`tests/test_core_draft.py`) apply
that rule and hold each case to the released corpus's strictness: the expected diagnostic, and no
other outside the outermost `oneOf` that encloses it. Two readings are the harness's, stated here so
an implementation can match them:

- a key the annotated `extensions` object's `propertyNames` refuses is one refusal,
  `JPS-STRUCTURE-EXTENSION-NAME` at the key, not one per branch of its `anyOf`;
- a non-string inside an annotation list fails both `type` and the refused-character `not`, whose
  `pattern` every non-string satisfies. The case expects `JPS-STRUCTURE-TYPE`, and the `not` is read
  as a consequence of that refusal at the same pointer.

## How a staged case lands

When the version that carries RFC 0031 opens, each case moves into that version's manifest as it
stands, with the selector the maintainers assign, its fixture moves beside the released ones, and
this directory is emptied.

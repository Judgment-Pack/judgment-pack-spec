# Judgment Pack Core `0.5.0`

## Status

This document is a draft. It may change incompatibly and MUST NOT be represented as an
industry standard or as suitable, by conformance alone, for consequential decisions.

`0.5.0` defines four conformance classes: carrier, structural, and semantic document
conformance, and evaluator conformance (§3.4). Sections 7 and 8 are normative for an implementation
that claims the evaluator class and informative for every other consumer; a document-conformance
claim does not depend on them. This release adds annotations, a specification-defined extension
that labels the pack, its outcomes, its rules and the entries of a value set (§§9.1–9.2); declared
value sets, which an `in` condition may reference (§§6.9 and 7.4); and the evaluation form, under
which neither annotations nor references change a result (§8.5). It also refuses a line terminator
in a local identifier, an extension name, a pack version and a decimal operand, whatever a
regular-expression engine's end anchor admits (§§2.2, 4, 5 and 9). Migration from `0.3.0` changes
only the selector for a pack that already meets those rules and §9.1's reading of an `extensions`
object (§11). Re-declaration opts the pack into this release's exact evaluator semantics and corpus
and confers no conformance on any implementation (§11).

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be
interpreted as described by BCP 14 when, and only when, they appear in all capitals. Normative
references are listed in §12.

## 1. Purpose

Judgment Pack Core defines a portable JSON document for representing:

- a decision intent and question;
- possible outcomes;
- evidence requirements;
- sources and claim-level citations;
- applicability conditions;
- rules and typed exceptions;
- explicit behavior for unknown information;
- escalation requirements; and
- basic authorship and review metadata.

The core defines representation and document conformance. For an implementation that claims
evaluator conformance (§3.4) it also defines portable evaluation semantics (§§7–8) and one portable
result, the disposition of §8.3. It does not establish truth, authority, safety, or fitness for a
deployment, and a disposition is not made true, authorized, or safe by being portable.

### 1.1 Normative artifacts and precedence

The artifacts in this repository have distinct roles:

- this document is the normative prose for carrier and semantic document conformance, for evaluator
  conformance, and for the interpretation of schema-defined fields;
- [`schema/judgment-pack-core.schema.json`](../schema/judgment-pack-core.schema.json) is the
  normative machine-readable projection of structural document constraints;
- [`spec/checkpoint-witness.md`](checkpoint-witness.md), a companion document, is the normative
  prose for the witness-statement reader conformance class it defines, and for nothing else;
- [`spec/dialect.md`](dialect.md), a companion document, is the normative prose for the
  preparation-verifier reader conformance class it defines, and for nothing else;
- [selected retained columns](retained-column.md) is accepted at draft maturity as normative prose
  for the selected leaf support scope only, adopted in `v0.3.0` (candidate distribution `v0.3.0-rc.2`);
  it establishes no implicit ordinary support or generic preparation-verifier claim;
- the evaluation corpus — the manifest and case fixtures under
  [`conformance/evaluation/`](../conformance/evaluation/README.md), not its README — is normative for
  evaluator conformance (§3.4) and for nothing else. This is the normative status the bullet below
  reserves for a later specification, granted here to those files only; and
- examples, the document-conformance corpus, READMEs, design notes, RFCs, the roadmap, and
  implementation behavior are informative unless a later specification explicitly gives an artifact
  normative status.

A conformance claim MUST satisfy all applicable normative requirements. If the schema or the
evaluation corpus disagrees with this document, this document controls and the mismatch is a
specification defect that SHOULD be reported. An example, test fixture, validator, or product
behavior cannot override any normative artifact.

## 2. Normative representation

### 2.1 JSON carrier

The normative carrier is a JSON text as defined by RFC 8259. In addition:

- object member names MUST be unique;
- a `\u` Unicode escape sequence that falls in the UTF-16 surrogate range (U+D800–U+DFFF) MUST form
  a valid UTF-16 surrogate pair; an unpaired surrogate escape is malformed input; and
- implementations MUST reject malformed or incomplete input and data exceeding their documented
  resource limits rather than process only a silent prefix.

Root type, recognized members, and field-value constraints belong to structural or semantic
document conformance rather than carrier conformance. A duplicate member name inside an annotations
object (§9.2) is refused by the first rule above, as in any JSON object.

### 2.2 Decimal grammar

JSON numbers SHOULD NOT be used for business quantities whose exact decimal identity matters. The
comparison operand of a `fact` condition using `greater-than`, `greater-than-or-equal`, `less-than`,
or `less-than-or-equal` MUST be a string matching:

```text
decimal = [ "-" ] ( "0" / non-zero-digit *DIGIT ) [ "." 1*DIGIT ]
```

Exponent notation, leading plus signs, leading zeroes, `NaN`, and infinities are not admitted.
This grammar does not classify every numeric-looking string as a decimal and does not apply to
identifiers, versions, paths, locators, citations, equality operands, or other textual values merely
because they contain digits. Core has no general decimal type marker; exact decimal
quantities outside ordered fact-condition operands require a future profile or declared extension.

A decimal operand matches this grammar as a whole string: it holds no line feed or other line
terminator, whatever a pattern's end anchor admits. Some regular-expression engines let `$` match
before a final line feed, so the schema also refuses U+0000–U+001F, U+007F–U+009F and
U+2028–U+202E in a decimal operand, as in a local identifier (§5).

This section defines decimal lexical syntax only. It has no decimal type marker and does not define
decimal equality, scale, units, or cross-unit conversion. §7.4 defines ordered comparison of two
strings satisfying this grammar for evaluator conformance (§3.4) and nothing else; it defines no
decimal-aware *equality*, so `equals` compares two such strings as strings. Outside that class,
satisfying this grammar does not imply executable comparison support.

## 3. Conformance classes

This draft defines three document conformance classes and one evaluator conformance class. The
document classes are unchanged in substance from `0.1.0-draft` and do not depend on the evaluator
class. It defines no execution conformance: applying an outcome remains outside Core.

### 3.1 Carrier-conforming document

A serialized document is carrier conforming when it satisfies §2.1, including valid and complete
RFC 8259 JSON, unique object member names, well-formed UTF-16 surrogate pairing for all `\u` escape
sequences, and explicit failure rather than silent partial processing when a documented resource
limit is exceeded.

### 3.2 Structurally conforming document

A carrier-conforming document is structurally conforming when it satisfies the normative JSON
Schema and all schema-adjacent requirements in this document.

The `format` keywords in the schema are assertions for JPS conformance, regardless of whether a
JSON Schema implementation treats `format` as annotation by default. A structural validator MUST
enable the Draft 2020-12 Format-Assertion vocabulary or perform equivalent checks. In particular:

- `id` MUST be an absolute URI conforming to RFC 3986;
- `source.publishedAt` MUST be an RFC 3339 `full-date`; and
- `metadata.createdAt` and every `metadata.reviews[].reviewedAt` value MUST be an RFC 3339
  `date-time`.

Accepting these fields without asserting their formats is insufficient for structural conformance.

### 3.3 Semantically conforming document

A structurally conforming document is semantically conforming when:

- every local reference resolves exactly once;
- referenced object kinds are correct;
- outcome, rule, evidence-requirement, source, exception, and value-set identifiers are unique
  within their collections;
- every rule outcome and fallback outcome names a declared outcome;
- every rule evidence reference names a declared evidence requirement;
- every rule source reference names a declared source;
- every `evidence-present` condition names a declared evidence requirement;
- every exception target names a declared rule when a target is present;
- every exception outcome names a declared outcome when an outcome is present;
- every exception source reference names a declared source;
- every `valueSet` member of a fact condition names exactly one declared value set (§7.4);
- required extension capabilities are declared;
- field meanings and cross-field constraints follow the normative prose in §§4–6 and §9.

A `valueSet` member is checked in every condition position: the root `applicability`, each rule's
`when`, each exception's `when`, and every condition nested in them under `all`, `any` and `not`. A
reference in a pack with no `valueSets` member, or with `valueSets: []`, names no declared set. So
does one that names an id held only by another kind of object, such as an outcome: identifiers are
collection-local, and `valueSet` looks only in `valueSets`.

"Required extension capabilities are declared" reads with §9.1's meaning of an `extensions` object.

Condition or resolution results are not part of semantic document conformance.

#### 3.3.1 Recommended rule-overlap check

This subsection is non-normative. A validator is recommended to compare every pair of rules that
name different outcomes and report `JPS-RULES-OVERLAP` when their conditions can both be `true` for
one facts document. This check is not a conformance requirement: a pack with an overlap remains
conforming, and evaluation in the overlap continues unchanged. Core §8 step 8 records `conflict`,
and the disposition is `unresolved`.

For conditions composed of `fact` nodes on one path and `literal`, `all`, `any`, and `not`, the
check is exact. Track the sets of values for which each condition is `true` and `false`; values in
neither set produce `unknown`. For `equals`, the true set is the singleton containing its operand;
for `in`, it is the set of its operands; and `not-equals` swaps the equality true and false sets,
all under the type-preserving equality of §7.4. Each ordered comparison's true and false sets are
intervals of decimal-string values under §7.4's mathematical ordering, with an open or closed
endpoint according to the operator; other values remain `unknown`. `all` intersects true sets and
unites false sets, `any` unites true sets and intersects false sets, and `not` swaps the two sets. A
`literal` supplies the corresponding full and empty sets. Two rules overlap exactly when the
intersection of their true sets is non-empty. Thus ranges that meet only at an endpoint excluded by
either range do not overlap. Equality and membership retain JSON type and spelling, including
§7.4's distinction between decimal ordering and string equality.

When the two conditions use different fact paths and neither condition excludes the other, the
result is **overlap not excluded**, rather than an exact overlap. Core conditions do not relate the
values at two paths, so a validator must not invent such a relationship. An implementation may use
Core's collection and nesting bounds to keep this pairwise analysis bounded.

The diagnostic has these members:

- code `JPS-RULES-OVERLAP`;
- certainty `exact` or `not-excluded`;
- severity;
- a JSON Pointer to the first rule in the reported pair;
- the ids and outcomes of both rules;
- for an exact result, either a witness facts input or the overlapping region: its fact `path` and
  `from` and/or `to` endpoints with inclusivity, or its shared values;
- the effect sentence: "Core §8 records `conflict`; the disposition is `unresolved`."; and
- a suggested exclusive rewrite, identifying the rule to rewrite and giving its replacement
  `when` condition.

The two rule ids in one diagnostic must differ. The manifest schema requires two unique rule
identity objects, but Draft 2020-12 cannot compare only their `id` member across array items, so a
manifest reader also enforces this id-level invariant.

For the common ascending numeric bands, the suggestion bounds the lower rule using Core's existing
two-comparison form. For example, replace `score >= 40` with an `all` of
`greater-than-or-equal 40` and `less-than 70` when the higher rule is `score >= 70`. No new operator
is needed. For a cross-path pair, the suggestion may instead conjoin the lower rule with `not` of
the higher rule's condition. Because `not` preserves `unknown` (§7.3), a missing higher-rule fact
makes that lower rule `unknown` too; with `onUnknown: escalate`, the record is not silently banded
lower than its known facts justify.

Plain validation reports every instance as a warning. Strict mode, including
`test-conformance --strict`, reports an exact, non-empty overlap as an error, and a review interface
blocks publication for that exact case. `not-excluded` remains a warning in every mode and does not
block publication. After the project can count published packs that trigger the exact case, a Core
minor may promote it to §3.3 semantic conformance; it is not promoted in this draft.

The check reads a reference as its set's values: the true set of an `in` condition with a reference
is the set of its entries' values, as for an inline operand. A validator MAY run the check on the
pack's evaluation form (§8.5).

This text defines no value-set advisory. [RFC 0031](../rfcs/0031-annotations-and-value-sets.md)
proposes two, `JPS-VALUE-SET-DUPLICATE-VALUE` and `JPS-VALUE-SET-UNREFERENCED`, as recommendations
outside conformance; they are added to Core text when
[RFC 0027](../rfcs/0027-pack-design-advisories.md) is dispositioned, beside `JPS-RULES-OVERLAP` or
in RFC 0027's report contract. The document corpus states the document result of each such case,
which is `valid`, and not the advisory.

### 3.4 Evaluator conformance

An implementation is *evaluator conforming* when, given

- a semantically conforming pack (§3.3);
- one JSON facts document;
- at most one evidence-availability document, whose absence §8.2 defines; and
- its own supported-extension set,

it produces the portable disposition of §8.3 under the semantics of §§7–8, reports every condition
that prevents completing an evaluation as an evaluation error rather than as a disposition (§8.4),
defines the limits §10 requires of this class, and passes the evaluation corpus published for the
exact `specVersion` it names.

The claim is scoped by the contract, not by the corpus: it asserts that the implementation satisfies
every requirement of §§7–10 — the semantics, the disposition, the error classes, and the documented
limits — for every input it admits. It says nothing about the pack, the facts, the evidence, or the
consequences of acting on a disposition (§3.5). Corpus results are required evidence for that claim
and are not exhaustive evidence of it (§3.4.1).

Every row of the corpus published for the claimed `specVersion` MUST pass, and a failed row blocks the
claim. A failed row does not by itself decide who is wrong: a divergence is as likely to be a defect
in the row as in the implementation, and §1.1 makes this document control over the corpus. What a
claimant MUST NOT do is decide that question for itself. A row is defective for a released corpus
version only when the project has said so in a versioned erratum, published beside the corpus as
`conformance/evaluation/errata.md`: one entry naming the `suiteVersion` it applies to, the case id, the
date of issue, and the defect. An erratum edits nothing — the manifest of a released version is never
changed (§3.4.1), so the frozen rows stay exactly as published — and it has one effect: a claim against
that `suiteVersion` may exclude the row the erratum names, provided the claim names the row and cites
the erratum. Until such an erratum exists, a failing row is a blocked claim and a specification-defect
report, in that order.

Carrier, structural, and semantic document conformance are untouched by this class. A document is
conforming or not without reference to any evaluator, and an implementation MAY claim document
conformance alone.

#### 3.4.1 Evaluator-conformance claims

Exactly one form of evaluator-conformance claim is definable: a claim against this class and against
the [evaluation corpus](../conformance/evaluation/README.md) for one exact `specVersion`, naming that
version, the corpus version, the results obtained, and — in the claim's own words, not as an inference
a reader must draw — that every row of that corpus version passed. If a project-issued erratum marks a
row defective for that corpus version (§3.4), the claim MUST name that row and cite the erratum;
otherwise "every row" means every row. Everything else remains forbidden. An implementation MUST NOT:

- claim partial or qualified evaluator conformance — a subset of §§7–8, a subset of the corpus, or
  conformance "except for" any requirement;
- claim evaluator conformance on the strength of prototyping, of an experimental surface, or of
  agreement with another implementation, in place of corpus results;
- claim evaluator conformance without having run the evaluation corpus for the exact `specVersion`
  claimed;
- claim evaluator conformance under `0.1.0-draft`, which defines no such class, or under any
  `specVersion` whose corpus it has not run;
- claim evaluator conformance while a row of the named corpus version fails, unless a project-issued
  erratum for that `suiteVersion` marks that row defective and the claim names and cites it (§3.4); or
- describe an evaluator-conformance claim as establishing anything §3.5 excludes.

A claim is made against one exact `specVersion` and is not inherited by any other version (§11).
The evaluation corpus is a *seed* corpus: it is version-pinned, it is not exhaustive, and it grows by
RFC. Passing it is necessary for the claim and is not evidence that the implementation is correct on
inputs the corpus does not contain.

The corpus is **frozen at the release of a `specVersion`** and grows only into the next one: rows are
added, changed, or corrected on the way to a later `specVersion`, never inside a released one, so two
identically worded claims against the same `specVersion` require the same rows. "The corpus version"
a claim must name is the `suiteVersion` member of the evaluation manifest, which for a released
version equals the `specVersion` the corpus was published for. An erratum (§3.4) is the only
post-release statement about a released corpus, and it changes no row.

Two optional case members of the corpus carrier are defined and unused by every row of this version's
corpus, so that a later row can carry them without a carrier change. `workBudget` is a positive integer
of evaluation-work units, in the accounting units a future work-accounting model will define; when it is
absent, the case sets no budget and the implementation's own documented limit (§10) applies.
`expectedErrorPhase` is `preflight` or `evaluation` and says which phase an expected error class was
reached in — while admitting the inputs (§8.2) or while evaluating them (§8) — so it accompanies
`expectedErrorClass` and never an expected disposition.

### 3.5 Non-claims

Conformance MUST NOT be described as proof that:

- a claim is true;
- evidence is authentic or sufficient;
- an author or reviewer had authority;
- an outcome is legally or ethically permissible;
- a particular runtime applied the pack correctly; or
- use of the pack is safe.

The runtime-correctness bullet has exactly one narrow exception. An evaluator-conformance claim
(§3.4) asserts that the claimed implementation complies with the complete evaluator contract of
§§7–10 — the semantics of §§7–8, the §8.3 disposition, the §8.4 error classes, and the limits §10
requires of the class — for every input it admits, not merely for the inputs it happened to run. Its
corpus results are required evidence of that compliance and are not exhaustive evidence of it: the
corpus is a seed corpus, and passing every row of it demonstrates nothing directly about an input no
row contains (§3.4.1). The claim asserts nothing about any deployment, any particular run in
production, the facts and evidence a caller supplied, or the permissibility of acting on a
disposition. Every other bullet above applies to the evaluator class unchanged.

## 4. Root object

| Member                 | Required | Meaning                                                 |
| ---------------------- | -------: | ------------------------------------------------------- |
| `profile`             |       no | Ceiling profile: `base` (default) or `extended` (§4.1) |
| `specVersion`          |      yes | Exact value `0.5.0`                               |
| `id`                   |      yes | Stable absolute URI identifying the pack series         |
| `version`              |      yes | Three-component `MAJOR.MINOR.PATCH` revision string     |
| `title`                |      yes | Non-empty human-readable title                          |
| `description`          |       no | Human-readable overview                                 |
| `decision`             |      yes | Decision intent and question                            |
| `applicability`        |       no | Optional condition delimiting the pack's scope          |
| `evidenceRequirements` |       no | Declared inputs or proof obligations                    |
| `sources`              |       no | Located source material                                 |
| `outcomes`             |      yes | At least two possible outcomes                          |
| `rules`                |      yes | One or more rules                                       |
| `exceptions`           |       no | Typed exceptions to rules or normal resolution          |
| `valueSets`            |       no | Declared value sets (§6.9)                              |
| `fallbackOutcome`      |       no | Candidate outcome when normal rules yield no candidate  |
| `escalation`           |       no | Optional handoff configuration, not a decision outcome  |
| `metadata`             |       no | Authorship, license, creation, and review information   |
| `extensions`           |       no | Namespaced extension values, including annotations (§9.2) |

Collection order is preserved for authoring and display but MUST NOT determine rule priority.
That rule covers `valueSets` and the entries of each set: their order carries no evaluation meaning.
Entry order fixes the order of an expanded reference in the evaluation form (§8.5), which only makes
that form deterministic.

`valueSets` is an array of value-set objects. An empty array is admitted and declares no set, as
for Core's other optional root collections. Two set objects equal under JSON Schema's equality are
refused by the schema.

The pack `version` matches its three-component grammar as a whole string, and the schema refuses
U+0000–U+001F, U+007F–U+009F and U+2028–U+202E in it, as in a local identifier (§5).

The root MUST be an object. The schema defines the recognized members of each Core object; a member
not defined for that Core object MUST NOT appear. The names and arbitrary JSON values inside an
`extensions` object are governed separately by §9.

### 4.1 Document ceiling profiles

A document may declare `profile`, exactly `base` or `extended`; absence means `base`.
A profile is a named set of ceilings, versioned with this specification. It changes no
members, minima, grammar, numeric domain, uniqueness requirement or evaluation semantics.
It never lowers a ceiling below `base`. An installation setting MUST NOT raise a ceiling
that the document does not declare. Core packs, Workflow documents and Dialect documents carry this member at their root.
Policy and governing-adoption documents adopt it from the next companion version;
the released 1.0.0 draft does not carry `profile`. Dialect source
and connection profiles are separate objects, not this ceiling declaration.

A reader MUST admit a document only under a profile it supports. Profile negotiation is
the first admission step: after the bounded root scan needed to identify the declaration,
and before other documents' byte-bound checks, schema interpretation, reference loading,
acquisition or evaluation, it checks that declaration. A supporting reader then applies
the selected profile's ceilings. An unknown name, non-string, empty
string or null is a structural refusal using the format's existing structural diagnostic.
For input declaring a known but unsupported profile, it returns exactly one diagnostic
`profile-unsupported`, naming that profile: `{"code":"profile-unsupported","profile":"extended"}`
for an unsupported `extended` declaration. A format's refusal envelope may wrap these two
members (Dialect uses `refusal` for the code); it MUST NOT append another diagnostic or
input-derived message. The same rule applies to implicit `base`. Only the parsing needed to identify the declaration precedes
this check; malformed JSON retains its syntax refusal. Resource-safe parsing may reject
unreadable input, but MUST NOT silently process a prefix or fall back to `base`.

`profile` is part of the document's bytes, so it is part of its digest and every exact-identity
rule. Readers MUST NOT insert the default or remove an explicit declaration before hashing.
An `extended` document has the same identity everywhere, including at readers refusing it.

For the proposed exact selected `retained-column/1` contract only,
[the retained-column companion](retained-column.md) specifies scoped Dialect artifact ceilings
after its own selection and independent role admission. Absence of that selection uses this
table. It does not raise Core pack, global transport, canonical parser, target-count or independent
work ceilings. It is adopted at draft maturity in `v0.3.0` (candidate distribution `v0.3.0-rc.2`), not a Core conformance claim.

The following is the ceiling table for these formats. Numbers elsewhere in the companions
state `base`; except for the exactly selected retained-column companion above, their
corresponding `extended` ceilings are exclusively those below. Units
and counting conventions remain those of the owning companion. No Core outcome, rule or
reference maximum is defined, so none is introduced here. Fixed semantic cardinalities
(such as exactly one coverage record per selected section), numeric domains and index ranges
are not resource ceilings and do not change.

| Format and resource | `base` | `extended` |
| --- | ---: | ---: |
| Core escalation routes (and their resulting handoff routes) | 8 | 16 |
| Core annotation keys per annotations object | 16 | 32 |
| Core annotation strings per list | 16 | 32 |
| Core annotation key characters | 64 | 128 |
| Core annotation string characters | 256 | 512 |
| Core value sets | 64 | 128 |
| Core entries per value set | 512 | 1024 |
| Policy (from the next companion version): informationalSources, sourceProvenance, sourceRefs per section, governingPolicies | 16 | 32 |
| Policy (from the next companion version): sections, scope sectionIds, coverage records per policy, consumerElements per section | 64 | 128 |
| Policy (from the next companion version): artifact version characters | 256 | 512 |
| Policy (from the next companion version): URI characters | 2048 | 4096 |
| Policy (from the next companion version): local ID and media type characters | 128 | 256 |
| Policy (from the next companion version): readable text characters | 4096 | 8192 |
| Policy (from the next companion version): parsed document bytes | 262144 | 524288 |
| Policy (from the next companion version): document nesting | 32 | 64 |
| Policy (from the next companion version): number literal characters | 128 | 256 |
| Policy (from the next companion version): exponent magnitude | 308 | 616 |
| Policy (from the next companion version): narrative, review basis and informational material bytes | 1048576 | 2097152 |
| Policy (from the next companion version): original material / registration bytes | 4194304 | 8388608 |
| Policy (from the next companion version): distinct retained bytes | 16777216 | 33554432 |
| Policy (from the next companion version): material registrations | 16 | 32 |
| Workflow limits.maxStages | 32 | 64 |
| Workflow limits.maxRecords, limits.maxInstances | 4096 | 8192 |
| Workflow limits.maxAttempts | 16 | 32 |
| Workflow limits.maxBytes | 1073741824 | 2147483648 |
| Dialect document bytes | 131072 | 262144 |
| Dialect combined dialect, case and acquisitions bytes | 2097152 | 4194304 |
| Dialect profiles / binding document bytes | 65536 | 131072 |
| Dialect preparation / record bytes | 8388608 | 16777216 |
| Dialect sources | 16 | 32 |
| Dialect retained responses, parameters per scope, clauses per rule, conditions per all/any | 64 | 128 |
| Dialect unwrap pointers | 4 | 8 |
| Dialect unwrapped string bytes | 200000 | 400000 |
| Dialect fact targets | 256 | 512 |
| Dialect evidence targets | 128 | 256 |
| Dialect value nesting / document nesting | 32 / 64 | 64 / 128 |
| Dialect number literal characters / exponent magnitude | 128 / 308 | 256 / 616 |
| Dialect declared fields, answer entries, text-list items, observations, citation indices | 64 | 128 |
| Dialect field name bytes | 64 | 128 |
| Dialect description bytes | 2048 | 4096 |
| Dialect model name bytes | 256 | 512 |
| Dialect evidence instruction bytes | 4096 | 8192 |
| Dialect text value bytes | 8192 | 16384 |
| Dialect text-list item bytes | 1024 | 2048 |
| Dialect decimal string characters | 128 | 256 |
| Dialect capabilities per source or connection profile | 3 | 6 |
| Dialect web assignments per source | 2 | 4 |
| Dialect earlier reconciliation sources | 15 | 30 |
| Dialect endpoint scope entries | 32 | 64 |
| Dialect endpoint scope entry / endpoint URL bytes | 2048 | 4096 |
| Dialect artifact ID bytes | 1024 | 2048 |

Workflow's document-declared `limits` remains required; only its ceilings above change.
Other Workflow carrier bounds remain unchanged. Raising a Dialect list ceiling does not
invent capability names or waive distinctness; a closed vocabulary can still constrain it.
Policy's canonical integer magnitude stays 9007199254740991: it is a numeric domain, not
a resource ceiling. Core implementation-defined limits (§10) are not rows of this table.

Characters in the Core annotation rows are Unicode code points, as JSON Schema counts them. There is
no ceiling on the total size of an annotations object; at `base` one holds at most
16 × (64 + 16 × 256) = 66,560 characters, and at `extended` 528,384. The annotation and value-set
rows are not outcome, rule or reference maxima, and none is defined. The maximum on entries does
not limit an inline `in` operand, on which Core sets no maximum.

The published structural schemas retain `base` maxima and declare the profile enum with
`base` as an annotation default. A reader supporting `extended` MUST validate with the
corresponding ceilings above, preserving every other schema constraint; applying an unchanged
base schema alone does not validate an extended document. Schema validation alone does not
negotiate capabilities. Reader capability records list `profiles`, the supported names;
listing `extended` commits the reader to every extended ceiling of its format.

## 5. Identity and references

The pack `id` MUST be an absolute URI. Local object identifiers are non-empty ASCII strings matching
`^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$` as a whole string: a local identifier holds no line feed or other
line terminator, whatever a pattern's end anchor admits. Some regular-expression engines let `$`
match before a final line feed, so the schema also refuses U+0000–U+001F, U+007F–U+009F and
U+2028–U+202E in a local identifier, as in an annotation key (§9.2).

Local identifiers are scoped to the pack version. They MUST NOT be interpreted as globally unique.
Meaning MUST NOT be inferred from the spelling of an identifier.

Core has no imports or remote-reference resolution. All rule, outcome, source,
evidence-requirement, exception, and value-set references resolve within one document.

Annotations, value sets and references are part of the pack's bytes, so they are part of every
digest and every exact-identity rule that covers the pack. A pack whose only change is an annotation
has changed content (§11). This document defines no canonical form or digest of a pack, and no
serialization of the evaluation form (§8.5): evaluation forms are compared as JSON values under §7.4
equality. Two packs with equal evaluation forms evaluate alike within §10's limit rule, and are not
the same pack.

Member order in an annotations object carries no meaning. The order of strings in an annotation list
is part of the bytes and carries no evaluation meaning; consumers SHOULD display it in document
order.

## 6. Core objects

### 6.1 Decision

`decision.intent` explains the organizational purpose. `decision.question` states the question the
pack is intended to resolve. Both are required human-readable strings.

The decision object MAY include namespaced extensions. It MUST NOT embed prompts or executable
host-language code.

### 6.2 Evidence requirement

An evidence requirement declares:

- `id` — local identity;
- `description` — what must be provided;
- `required` — whether absence prevents normal resolution; and
- optional `kind` — `document`, `fact`, `measurement`, or `attestation`.

The kind is descriptive in this draft. Products may acquire or authenticate evidence differently.

### 6.3 Source

A source contains:

- `id` and `title`;
- a typed `locator` with `kind` and `value`;
- optional publisher and publication date;
- optional `citation` containing a location and excerpt; and
- optional rights information.

A source record represents provenance supplied by the author. Core conformance does not verify that
the source exists, that the excerpt is accurate, or that its license permits a proposed use.

### 6.4 Outcome

An outcome has a local `id`, human-readable `label`, and optional `description`.

An outcome is a declared result, not an authorization to perform an external action. Execution of
an outcome is outside Core.

### 6.5 Rule

A rule declares:

- `id` and `description`;
- `when`, a condition;
- `outcome`, a declared outcome id;
- `onUnknown`, either `ignore` or `escalate`;
- optional evidence-requirement references;
- optional source references; and
- optional rationale.

The representation has no rule-priority field, and array order carries no priority meaning. Handling
of conflicts and `onUnknown` appears in §8, which is normative for evaluator conformance (§3.4) and
informative for a document-conformance consumer.

### 6.6 Exception

An exception declares a condition and one effect:

- `suppress-rule`, with `targetRule`;
- `force-outcome`, with `outcome`; or
- `escalate`.

For `suppress-rule`, `targetRule` is required and `outcome` is absent. For `force-outcome`, `outcome`
is required and `targetRule` is absent. For `escalate`, both are absent. Every exception also has a
required `onUnknown` policy of `ignore` or `escalate`. Evaluation order and effect compatibility
appear in §8, which is normative for evaluator conformance (§3.4) and informative for a
document-conformance consumer.

### 6.7 Escalation

An escalation object describes configured handoff intent. `triggers` is a non-empty set chosen
from:

- `not-applicable`;
- `missing-required-evidence`;
- `unknown`;
- `conflict`; and
- `no-match`.

An escalation MUST declare exactly one of `target` and `routes`; declaring both is not
conformant. `target` retains its existing `{kind, name}` shape, with `kind` one of `human-role`,
`queue`, or `system`, and `name` a non-empty display name. `routes` is an ordered array of 1 to 8
entries, each a closed object containing `target` and optionally `triggers`. Each route target
has that same shape. If present, route `triggers` MUST be a non-empty, duplicate-free subset of
this escalation's `triggers`. An omitted route trigger list means unconditional selection once
a handoff is requested, not a request by itself. Duplicate targets remain distinct routes.
The maximum of 8 is the `base` schema bound; §4.1 raises it to 16 under `extended`.
It is not an installation setting.

For example, `"routes": [{"target": {"kind": "queue", "name": "Review"},
"triggers": ["unknown"]}, {"target": {"kind": "human-role", "name": "Oversight"}}]`
selects Review only for a retained `unknown` reason and Oversight for every requested handoff,
provided `unknown` is declared among the escalation's triggers.

The target identifies a human role, queue, or external system by a display name. The object
configures handoff intent; it does not itself make a pack applicable, turn a condition into an
outcome, or prove that a handoff occurred. When the object is omitted, Core supplies no default
triggers or target. Core does not define delivery, identity resolution, authorization, or
service-level objectives.

### 6.8 Metadata

Metadata MAY carry authors, creation time, license expression, and review records. These are
author assertions. Signature and organizational-authority profiles may strengthen them later.

### 6.9 Value set

A value-set object has these members and no others:

| Member | Required | Value |
| --- | ---: | --- |
| `id` | yes | a local identifier (§5), unique within `valueSets` |
| `description` | no | a non-empty string |
| `entries` | yes | an array of 1 to 512 entries (the `base` ceiling, §4.1) |

A value-set object has no `extensions` member: one on a set, whatever it holds, is an unknown
member. A set and an outcome may share an id, because the member that names a set fixes the kind.

An entry has these members and no others:

| Member | Required | Value |
| --- | ---: | --- |
| `value` | yes | any JSON value, as any item of an inline `in` operand may be |
| `description` | no | a non-empty string |
| `extensions` | no | the annotations extension (§9.2), and no other name |

- **Types.** A set declares no type and may mix types, as an inline `in` operand may. Each value is
  compared with the selected fact value under §7.4. A set of `1`, `"1"`, `true`, `null`, `[1]` and
  `{"a": 1}` is six distinct values.
- **Entry extensions.** An entry's `extensions` object admits exactly one key,
  `org.judgmentpack.annotations`. A vendor name there, and every other reserved name, is an unknown
  member. The evaluation form removes the sets (§8.5), so a vendor extension that lived only in a
  set or an entry would vanish from it, and a required one would be inert. Annotations can stay,
  because they are never requirable (§9.2).
- **Repeated values.** Two entries of one set may have equal values. That is not a conformance error
  at any layer. A repeated entry changes no evaluation result, since an inline `in` operand already
  admits repeated items. A consumer shows each entry as written, with its own description and
  annotations.
- **No nesting.** A set references no other set, and an entry has no `valueSet` member. An entry
  value that looks like a reference, such as `{"valueSet": "tier-codes"}`, is a literal JSON object,
  compared as one. There is no union, intersection or difference of sets.
- **Unreferenced sets.** A set that no condition references is admitted and inert. Its entries take
  no part in evaluation, and no evaluation-phase counter counts them; a limit on the pack as
  presented does (§10).

`valueSets` is a Core member, not an extension: a consumer that ignored the sets could not evaluate a
condition that references one.

## 7. Condition interpretation

This section is **normative for evaluator conformance** (§3.4) and informative for every other
consumer. In `0.1.0-draft` the results described here were informative in every direction; that note
is amended, and amended only for the evaluator class. The allowed JSON shapes for conditions remain
normative through the schema for all classes, and a carrier, structural, or semantic document
conformance claim is unaffected by anything in this section: no result below can make a document
conforming or non-conforming.

A condition produces `true`, `false`, or `unknown`:

- `literal` returns its Boolean value;
- `all` uses strong three-valued conjunction;
- `any` uses strong three-valued disjunction;
- `not` negates while preserving `unknown`;
- `fact` compares a value selected from runtime-supplied facts; and
- `evidence-present` tests whether evidence was supplied for a named requirement.

### 7.1 `all`

- `false` if any child is false;
- `true` if every child is true;
- `unknown` otherwise.

### 7.2 `any`

- `true` if any child is true;
- `false` if every child is false;
- `unknown` otherwise.

### 7.3 `not`

`true` becomes `false`, `false` becomes `true`, and `unknown` remains `unknown`.

### 7.4 Fact conditions

A `fact.path` is interpreted as RFC 6901 JSON Pointer syntax against one runtime-supplied JSON facts
document. The empty string selects the document root. A syntactically valid pointer that does not
resolve, including an invalid array traversal at runtime, produces `unknown`.

The admitted operators are:

- `equals`;
- `not-equals`;
- `greater-than`;
- `greater-than-or-equal`;
- `less-than`;
- `less-than-or-equal`; and
- `in`.

`equals` uses type-preserving JSON equality: null equals null; Booleans and
strings compare by value; JSON numbers compare by their mathematical value without lossy
conversion; arrays compare recursively in order; and objects compare recursively by member name
and value without regard to member order. There is no coercion between JSON types. `not-equals` is
the Boolean inverse of `equals` when equality can be determined.

For `in`, the schema requires the condition value to be a non-empty array. The selected fact value
is compared for equality with each array item. A match produces `true`; no match produces `false`.

The schema requires operands of `greater-than`, `greater-than-or-equal`, `less-than`, and
`less-than-or-equal` to satisfy the decimal grammar in §2.2. An ordered comparison is *defined* if
and only if both the selected fact value and the operand are JSON strings satisfying that grammar;
the two are then compared by mathematical value. Any other selected value — including a JSON number,
a Boolean, null, an array, an object, or a string that does not satisfy the grammar — makes the
comparison undefined and produces `unknown`. A JSON number is deliberately not coerced: the grammar
exists because a number's decimal identity is not preserved, and silently accepting one would make
two implementations disagree.

Equality of decimal strings is *string* equality and is deliberately not decimal-aware. `"1.0"` and
`"1.00"` are therefore not equal under `equals`, and `not-equals` is correspondingly `true`, while
neither is greater than the other under an ordered comparison, which reads both by mathematical value.
The two families of operator answer different questions and Core defines no reconciliation between
them; a pack that needs decimal-aware equality must normalize scale in the pack, in the operand and in
the facts it is compared against.

Units, quantities carrying units, and date or time values have no ordered comparison here. Such an
operand does not satisfy §2.2, so an ordered comparison over one is not expressible rather than
merely unknown-by-accident; `equals`, `not-equals`, and `in` still compare those values as ordinary
JSON. Outside evaluator conformance, structural acceptance of an ordered condition still implies no
executable support.

An implementation claiming evaluator conformance (§3.4) MUST implement every operator listed above.
"Unsupported operator" is not an available result for that class, and answering `unknown` where this
section defines `true` or `false` is a failure to implement §7.4 rather than a conforming result —
§3.4.1 forbids claiming a subset of §§7–8, whether or not a corpus row happens to exercise the
operator. Within that class `unknown` is produced by exactly three things: a path that is absent or
does not resolve; a selected value or operand whose shape the operator does not admit, which includes a
value carrying units, since this section does not admit one in an ordered comparison at all; and a value
the implementation cannot compare exactly. That last case is confined to JSON numbers outside an
implementation's exact range, it is the one open question of §13 that §8.3 names as the single seam in
its byte-agreement requirement, and it is not permission to return `unknown` for anything else.

A fact condition MAY carry `valueSet`, a local identifier naming a declared set (§6.9), in place of
`value`.

- A fact condition carries exactly one of `value` and `valueSet`. Carrying both is a structural
  refusal at the condition. Carrying neither is the existing refusal of a fact condition without its
  operand.
- `valueSet` is admitted only with the operator `in`. With any other operator it is a structural
  refusal at the operator.
- The rules for `value` are unchanged. An object in `value`, such as `"value": {"valueSet": "x"}`, is
  still refused as an `in` operand that is not an array; it is not a reference.
- A reference resolves within the document (§3.3).

A reference behaves exactly as its inline array, the `value` of each entry of the named set in entry
order (§8.5): the same equality, the same `unknown` for an absent path, and the same reading under
`not`. The order of sets, and of entries within a set, changes nothing, because `in` tests
membership. Where this section leaves a comparison with a number open (§13), the open comparison is
the inline array's; a reference neither adds an input to it nor takes one out.

### 7.5 Evidence presence

`evidence-present` is `true` when the evaluation input records the named requirement as available,
`false` when it records the requirement as absent, and `unknown` when the input cannot say. For
evaluator conformance those three states are supplied by the evidence-availability document of §8.2:
`present` is `true`, `absent` is `false`, and `unknown` — including an omitted key — is `unknown`.
That tri-state input replaces `0.1.0-draft`'s appeal to a "complete evidence manifest", which was
undefined and was the one recorded semantic divergence between careful readings of that draft. This
draft still defines no evidence-manifest interchange format beyond the tri-state of §8.2.

## 8. Resolution model

This section is **normative for evaluator conformance** (§3.4) and informative for every other
consumer, on the same terms as §7. The step order below is contractual only where it changes the
disposition; it mandates no implementation algorithm, and an implementation may compute in any order
that yields the specified disposition. §8.2 defines the inputs, §8.3 the one portable result, and
§8.4 the errors that replace a result.

Resolution produces one of three result kinds:

- an `outcome` result naming exactly one declared outcome;
- a `not-applicable` result carrying reason `not-applicable`, which is not an outcome; and
- an `unresolved` result carrying one or more reasons.

The generated reason vocabulary is `not-applicable`, `missing-required-evidence`, `unknown`,
`conflict`, and `no-match`, matching `escalation.triggers`. A true exception with effect `escalate`
adds the separate reason `exception-escalation`; that reason is a direct request rather than a
trigger-selected request. A result may retain multiple reasons. Reasons are a de-duplicated set;
their order carries no priority. Implementations may additionally record contributing rule,
exception, or evidence-requirement ids, outside the disposition (§8.3).

The algorithm is:

1. Treat omitted `applicability` as the literal value `true`. If applicability is false, produce a
   terminal `not-applicable` result carrying reason `not-applicable` and do not evaluate exceptions
   or rules. If it is unknown, produce an `unresolved` result with reason `unknown` and stop.
2. Inspect every required evidence requirement, using the presence values of §7.5. Record
   `missing-required-evidence` if and only if at least one required requirement's presence is
   `false`. Record `unknown` if and only if at least one required requirement's presence is
   `unknown` and none is `false`. Retain the ids of the requirements that produced either reason for
   diagnostics. This restates `0.1.0-draft`'s binary "any required evidence is absent" test in the
   three-valued terms of §7.5, and is the resolution of that draft's one recorded semantic
   divergence.
3. Evaluate every exception condition and collect its effects. An unknown exception with
   `onUnknown: ignore` contributes no effect but remains unknown in a trace. An unknown exception
   with `onUnknown: escalate` records reason `unknown`.
4. Combine true exception effects as follows:

   - all `suppress-rule` effects are compatible and suppress the union of their target rules;
   - `force-outcome` effects are compatible when they all name the same outcome and conflict when
     they name different outcomes;
   - suppression is compatible with a forced outcome; and
   - one or more `escalate` effects are mutually compatible, record reason
     `exception-escalation`, and form a direct escalation request that takes precedence over
     suppression and forced outcomes.

5. Record reason `conflict` for incompatible forced outcomes. If step 2 recorded either of its
   reasons, an exception is unknown with `onUnknown: escalate`, exception effects conflict, or a true
   exception directly requests escalation, produce `unresolved` after all exception effects have been
   inspected, and do not evaluate normal rules. Retain every reason discovered at this stage. A
   direct exception escalation is also retained as such in diagnostics.
6. If one compatible forced outcome remains and no blocking state from step 5 exists, produce that
   outcome without evaluating normal rules. Otherwise, remove every suppressed rule and evaluate
   all remaining rules.
7. A true rule contributes its outcome as a candidate. A false rule contributes none. An unknown
   rule with `onUnknown: ignore` contributes no candidate and does not block resolution; an unknown
   rule with `onUnknown: escalate` records reason `unknown` and blocks both a candidate outcome and
   the fallback.
8. Record reason `conflict` when true rules name more than one distinct outcome. If both an
   escalate-on-unknown rule and conflicting true rules are present, retain both `unknown` and
   `conflict`; neither is discarded because the other also blocks resolution. Produce `unresolved`
   whenever either reason is present.
9. If no blocking reason exists and true rules name one distinct outcome, produce it. Multiple true
   rules naming that same outcome are compatible.
10. If no true rule contributes an outcome, use `fallbackOutcome` when present. False rules and
    unknown rules with `onUnknown: ignore` do not prevent this fallback. If no fallback is present,
    produce `unresolved` with reason `no-match`.

Thus, `onUnknown: escalate` has blocking precedence over otherwise compatible outcomes at the same
resolution stage, while `onUnknown: ignore` never changes an unknown condition to false and does
not erase that unknown from a trace. Array order, lexical id order, and implementation-defined
priority MUST NOT select among rule outcomes, and a conflict MUST NOT be tie-broken: it is an
`unresolved` result.

### 8.1 Handoff configuration

Evaluation state and handoff configuration are distinct. An unresolved or not-applicable result
exists independently of the optional `escalation` object; `escalation` is not itself an outcome.

For an escalation declaring `target`, the configured target is requested when at least one retained
reason appears in `escalation.triggers`. When several reasons match, resolution
creates exactly one handoff request to the configured target and includes the complete retained
reason set. That complete set is carried in the disposition's `reasons`; `handoff.triggeredBy` names
the subset of it that triggered the request, which is smaller whenever `escalation.triggers` does not
name every retained reason (§8.3). A true exception with effect `escalate` is a direct request and
uses the configured target regardless of the trigger list.

For an escalation declaring `routes`, first determine whether a request is made by at least one
retained reason in `escalation.triggers` or by a direct exception escalation. Only when a request
is made, select every route whose `triggers` intersects the complete disposition `reasons`, and
every route that omits `triggers`. Make exactly one request per selected route, in declaration
order. This is fan-out, not alternatives or fallback; identical target objects are not deduplicated.
A direct exception bypasses the escalation trigger gate, but does not bypass route filters.
If no route is selected, `handoff.state` is `none`, `handoff.routes` is empty, and `triggeredBy`
is absent. Routing never changes `kind`, `outcomeId`, or the complete retained `reasons`.
A review-named outcome alone requests nothing, including from unconditional routes.

When `escalation` is omitted, there are no default triggers and no default target. When it is
present but no generated reason matches its triggers, there is likewise no configured handoff for
that reason. In either case, an unresolved result remains unresolved and must not be converted into
a fallback or other outcome. A direct exception escalation without an `escalation` object remains
an unresolved direct request with no Core-defined destination; the disposition records it as a
requested handoff whose destination the pack does not supply (§8.3).

### 8.2 Evaluation inputs

An evaluation takes four inputs. Three are documents — the pack and the facts document are always
supplied, and the evidence-availability document is optional, with the meaning of its absence defined
below — and the fourth is a property of the implementation. Two documents are therefore the minimum
and three the maximum.

- **Pack** — one semantically conforming document (§3.3). A pack that is not semantically conforming
  is an evaluation error (§8.4), not a disposition.
- **Facts** — one JSON document. Every `fact.path` is an RFC 6901 JSON Pointer evaluated against it
  (§7.4). There is exactly one facts document per evaluation; Core defines no fact namespace,
  merging, or acquisition.
- **Evidence availability** — one JSON object whose member names are declared
  `evidenceRequirements[].id` values and whose values are exactly one of the strings `present`,
  `absent`, or `unknown`. An omitted key means `unknown`. An omitted document as a whole is the
  implicit empty object, which by that rule makes every declared requirement `unknown`; it is the only
  form absence takes, and it is not an error. A value that is not a JSON object at all, a member name
  that is not a declared requirement id, or a value outside those three strings is an evaluation error
  (§8.4) — an undeclared key is far more likely to be a caller's mistake than a statement about the
  pack. Duplicate member names are already rejected by §2.1.
- **Supported extensions** — the set of `metadata.requiredExtensions` capabilities the implementation
  supports. A required capability outside that set is an evaluation error (§8.4), never a
  disposition (§9). A name in the set that no conforming pack can list in
  `metadata.requiredExtensions`, such as `org.judgmentpack.annotations` (§9.2), is not a capability:
  it is ignored, is not an error, and changes no result.

**Input preflight.** The inputs are admitted before evaluation begins. An implementation claiming
evaluator conformance MUST validate them in this order — the pack, then the facts document, then the
evidence-availability document, then the pack's `metadata.requiredExtensions` against its own
supported-extension set — and MUST complete that validation before step 1 of §8 runs. That order is the
error precedence of §8.4, so the first failure encountered is also the class §8.4 requires be reported.

Any violation of this section's shape requirements is the `malformed-input` evaluation error of §8.4: an
evidence-availability input that is not a JSON object, an undeclared member name, a value outside
`present`, `absent`, and `unknown`, and a facts or evidence-availability input that is not a
carrier-conforming JSON text (§2.1) are all that error. So is reaching a documented document or carrier
limit while admitting an input, because §2.1 requires refusing such a document rather than processing
part of it, so the input is never admitted (§8.4, §10).

Because preflight completes before step 1, no result can outrace an input error: a pack whose
applicability is false, presented with an evidence-availability document carrying an undeclared key, is
the `malformed-input` error and never the `not-applicable` disposition, and the same holds for every
other terminal step of §8 and for every preflight failure. Two conforming implementations therefore
agree on which inputs are admitted at all, not only on what an admitted input produces.

Core defines no transport, file layout, or command-line surface for these inputs. It defines what
they mean.

### 8.3 The portable disposition

An implementation claiming evaluator conformance MUST produce, for each evaluation, exactly one
*disposition* or exactly one evaluation error (§8.4) and no disposition. The disposition is a JSON
object with these members and no others:

| Member      | Present                  | Value                                                       |
| ----------- | ------------------------ | ----------------------------------------------------------- |
| `kind`      | always                   | `outcome`, `not-applicable`, or `unresolved`                 |
| `outcomeId` | iff `kind` is `outcome`  | the `id` of exactly one declared outcome                     |
| `reasons`   | always                   | the retained reason set, serialized as a sorted array        |
| `handoff`   | always                   | an object carrying the handoff state, and its trigger        |

`kind` is the result kind produced by §8. `not-applicable` and `unresolved` are not outcomes and MUST
NOT be mapped onto one, defaulted to one, or flattened into the same field as `outcomeId`.

`outcomeId` MUST be present when `kind` is `outcome` and MUST be absent otherwise — absent, not
`null` and not an empty string. It MUST name a declared outcome of the pack evaluated.

`reasons` is a **set**: unordered and duplicate-free. Its members are drawn from
`not-applicable`, `missing-required-evidence`, `unknown`, `conflict`, `no-match`, and
`exception-escalation`; no other value is admitted. It is empty if and only if `kind` is `outcome`.
When `kind` is `not-applicable` its one member is `not-applicable`. Two dispositions have the same
`reasons` when the sets are equal; serialized order is never a difference in the disposition.

`handoff` is an object with:

- `state` — `requested` when §8.1 makes a handoff request, whether trigger-selected or a direct
  exception request, and including a direct exception request made when the pack carries no
  `escalation` object, in which case the request has no Core-defined destination (§8.1). `none`
  otherwise. Present always.
- `triggeredBy` — present if and only if `state` is `requested`. A non-empty **set** of reason
  identifiers: every retained reason that appears in `escalation.triggers`, plus
  `exception-escalation` when a true exception with effect `escalate` made a direct request (§8.1).
  It is always a subset of `reasons`; route filtering does not narrow it.
- `routes` — present if and only if the pack declares `escalation.routes`. An ordered array of
  the selected routes' `target` objects, one per selected route in declaration order, including
  duplicate targets. It is empty when no request is made or no route is selected. A non-empty
  array accompanies `state: "requested"`; an empty array accompanies `state: "none"`.

For a pack declaring `target` alone, the disposition does not echo the configured target and its
canonical bytes remain unchanged from `0.2.0-draft`. A consumer reads that target from the pack.
For a pack declaring `routes`, `handoff.routes` carries exactly the targets selected from the pack.
Targets are display names, not addresses (§6.7). A requested handoff is a request, not evidence
that a handoff occurred.

Nothing else belongs in the disposition object. An implementation MAY report a trace, contributing
rule, exception, or evidence-requirement ids, timings, or any other diagnostic **outside** the
disposition, and their presence or absence MUST NOT change any member above.

**Serialization.** So that two conforming implementations can be compared:

- both sets — `reasons` and `handoff.triggeredBy` — are serialized as JSON arrays whose elements are
  sorted ascending by Unicode code point, with no duplicates;
- an absent member is omitted, never serialized as `null`;
- member order carries no meaning; and
- where a byte comparison is required, each disposition is first canonicalized as described by
  RFC 8785, which orders object members by name. A disposition contains no numbers, so that
  specification's number rules never engage.

Two conforming implementations given the same pack, facts document, evidence-availability document,
and supported-extension set MUST produce byte-identical canonicalized dispositions. That is the whole
of the portability claim, and §3.5 applies to every part of it.

That requirement has exactly one seam, and this is the whole of it: whether equality involving a JSON
number an implementation cannot represent exactly is `unknown` or an explicit input error is an open
question (§7.4, §13). Until §13 closes it, two implementations with different arithmetic ranges may
answer differently on such a value, and an input carrying one is outside the portable claim. No other
input, operator, or member is outside it, and no other implementation-relative escape exists in §§7–8:
an implementation MUST NOT read this seam as permission to answer `unknown` anywhere else.

Two illustrative canonicalized dispositions, informative:

```json
{"handoff":{"state":"none"},"kind":"outcome","outcomeId":"proceed","reasons":[]}
```

```json
{"handoff":{"state":"requested","triggeredBy":["missing-required-evidence"]},"kind":"unresolved","reasons":["missing-required-evidence"]}
```

### 8.4 Evaluation errors

An evaluation error is not a disposition. When an implementation claiming evaluator conformance
cannot complete an evaluation, it MUST report an evaluation error, MUST NOT emit a disposition for
that evaluation, and MUST NOT substitute `unresolved`, `not-applicable`, or a fallback outcome for
the error. Evaluation terminates wherever §8 had reached, and partial state MUST NOT be reported as a
result. This is the §3.1 rule applied one layer up: a documented limit or a malformed input produces
explicit failure, never a silent partial processing that a caller could mistake for a result. A
truncated evaluation reported as a disposition is a forged disposition.

An implementation MUST report the class of every evaluation error, and every evaluation error is
identified by exactly one class: exactly one of the four Core classes below, or — for a condition no
Core class covers — exactly one documented implementation-defined class in the form this section
requires of one. A Core class always takes precedence: an implementation-defined class is reported only
when no Core class applies, never in place of one that does.

The Core classes are:

- **`pack-not-conformant`** — the pack input is not a semantically conforming document (§3.3),
  failing at any of the carrier, structural, or semantic layer.
- **`unsupported-required-extension`** — the pack declares a capability in
  `metadata.requiredExtensions` that the implementation does not support. §9's "structurally readable
  but not fully interpretable" report is this error for the evaluator class: the unsupported part may
  be the part that decides, so no disposition may be produced.
- **`malformed-input`** — an input failed the preflight of §8.2. The facts document or the
  evidence-availability document is not a carrier-conforming JSON text (§2.1); or the
  evidence-availability input violates §8.2 by not being a JSON object, by carrying an undeclared member
  name, or by carrying a value outside `present`, `absent`, and `unknown`; or a documented document or
  carrier limit — bytes, nesting depth, or string size — was reached while admitting an input, which
  §2.1 requires be refused rather than partly processed, so the input never became one.
- **`resource-exhaustion`** — a limit documented under §10 was reached during evaluation: a
  collection-size limit or the evaluation-work limit. This class is about work an admitted input turned
  out to require, never about admitting the input in the first place.

More than one class can apply to the same inputs: a pack that fails semantic conformance presented with
an evidence document carrying an undeclared key is both `pack-not-conformant` and `malformed-input`. The
classes are therefore evaluated in one fixed order — `pack-not-conformant`, then `malformed-input`, then
`unsupported-required-extension`, then `resource-exhaustion` — and the first that applies is the class
reported, so that two conforming implementations report the same class for the same inputs. That order is
the preflight order of §8.2, and the phase split between `malformed-input` and `resource-exhaustion` is
what keeps it from contradicting §10: a limit reached while admitting an input is `malformed-input`
because the input was refused, and `resource-exhaustion` is reserved for a limit reached while evaluating
an input that was admitted. An implementation MAY name the other classes it also considered as message
detail.

As stated above, an implementation MAY define an additional class for a condition none of the four Core
classes covers — and only for such a condition — and MAY attach any message detail it likes. An
implementation-defined class MUST be documented and MUST be named in the reverse-domain form of
§9 — for example `com.example.timeout` — which cannot collide with a Core class identifier, since
those are bare kebab-case names, nor with a class another implementation defines. The transport, exit
status, and wire format of an evaluation error are not defined here; the class identifier is. A
machine-readable diagnostic contract remains open (§13).

### 8.5 The evaluation form

The *evaluation form* `EF(P)` of a semantically conforming pack `P` is the JSON value produced by
these three steps:

1. **Expand references.** Each fact condition, in each condition position of §3.3, that carries
   `valueSet` loses that member and gains a `value` member: an array holding the `value` of each
   entry of the named set, in entry order.
2. **Remove the sets.** The root member `valueSets` is removed, whatever it holds, `[]` included.
3. **Remove annotations.** The member `org.judgmentpack.annotations` is removed from the root's
   `extensions` object, from each outcome's and from each rule's. If removing it leaves that
   `extensions` object empty, the `extensions` member is removed. An `extensions` object already
   empty in `P` is kept.

Nothing else changes. The steps act on positions, not on content: a literal inside a `value`
operand, an entry value and a vendor extension's value are never inspected, and a literal that looks
like a reference or like an annotations object stays exactly as it is.

`EF(P)` is itself a semantically conforming pack of the same `specVersion` and `profile`. A pack
with no `valueSets` member, no reference and no annotations is its own evaluation form.

For a semantically conforming pack `P`, given the same facts document, evidence-availability
document and supported-extension set, an implementation claiming evaluator conformance MUST produce
for `P` the result §§7–8 give `EF(P)`: the byte-identical canonicalized disposition (§8.3), or an
evaluation error of the same class (§8.4). Limits apply as §10 states. A pack that is not
semantically conforming has no evaluation form, and an evaluator reports `pack-not-conformant` for
it (§8.4), whether the fault is in an annotation, a set, a reference or anywhere else.

These follow:

- **Annotations are inert.** Between semantically conforming packs, adding, changing or removing
  annotations never changes a disposition or an error class, unless the change carries `P` across one
  of the implementation's document limits. A label that spells an outcome id, a reason or a route
  target changes nothing. A malformed annotation is not such a change: the pack is then not
  structurally conforming.
- **Substitution.** A reference behaves exactly as its inline array (§7.4).
- **Nothing new reaches the disposition.** There is no new reason, error class or disposition
  member. No annotation, set id or entry description appears in a disposition. A trace outside the
  disposition MAY name the set a condition referenced and the entries a fact matched.

The evaluation form defines an equivalence, not a processing step. An evaluator need not build
`EF(P)`; resolving a reference to the declared array without copying it satisfies this section.

## 9. Extensions

`extensions` is an object whose keys use reverse-domain naming, for example
`com.example.review-policy`. Values may be any JSON value, except where a specification-defined
extension's definition governs its value (§9.1).

An optional extension MUST NOT change Core semantics. Consumers preserve optional extensions when
round-tripping but may otherwise ignore them.

Required extension semantics are declared in `metadata.requiredExtensions`. A consumer that does
not support every required extension MUST report the document as structurally readable but not
fully interpretable. It MUST NOT silently ignore a required extension. For an implementation claiming
evaluator conformance, that report is the `unsupported-required-extension` evaluation error of §8.4
and no disposition is produced.

Every name in `metadata.requiredExtensions` MUST appear as a key in at least one `extensions`
object in the document. A required-extension declaration without a corresponding value is
semantically invalid. An extension key omitted from `metadata.requiredExtensions` is optional.

Names beginning with `org.judgmentpack.` are reserved for specification-defined extensions (§9.1).

An extension name, as a key of an `extensions` object or an item of `metadata.requiredExtensions`,
matches `^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9-]*)+$` as a whole string: it holds no line feed or other
line terminator, whatever a pattern's end anchor admits. The schema refuses the reserved prefix with
a `not` beside that pattern, not with a lookahead, so that an engine without lookahead can compile
it, and the same `not` refuses the characters §5 refuses in a local identifier.

### 9.1 Specification-defined extensions

A specification-defined extension is one whose name begins with `org.judgmentpack.` and which this
specification defines. Its value is governed by its definition. Each definition states the
`extensions` objects in which its name may appear and whether the name may be listed in
`metadata.requiredExtensions`. Every other name beginning with `org.judgmentpack.` remains refused
in every `extensions` object.

An `extensions` object, in this section and in §3.3, is one the schema defines as a member of a Core
object. A member named `extensions` inside an operand, an entry value or an extension's own value is
data, not an `extensions` object. So "every name in `metadata.requiredExtensions` MUST appear as a
key in at least one `extensions` object" counts only those objects: a required name that appears only
inside an operand or an entry value is missing, and the document is not semantically conforming.

This reading is a change that takes effect under `0.5.0`; it does not change Core `0.3.0`. Core
`0.3.0` §9 does not say whether a member named `extensions` inside data is an `extensions` object, a
known open point of that text. The repository's `0.3.0` checker counts such a member anywhere in the
document, and it is not changed. So one `0.3.0` shape is refused under `0.5.0` (§11).

This specification defines one such extension, `org.judgmentpack.annotations` (§9.2).
[RFC 0016](../rfcs/0016-outcome-values.md), a Draft, would add its own name under this paragraph.

### 9.2 Annotations

**Name and positions.** The extension `org.judgmentpack.annotations` holds an *annotations object*.
It MAY appear as a key of exactly these `extensions` objects: the root's, each outcome's, each rule's
and each value-set entry's (§6.9). In every other `extensions` object (the decision's, each evidence
requirement's, each source's, each exception's, the escalation's and the metadata's) it remains
refused. An annotations object describes only the object that carries it: there is no inheritance
and no merging.

**Optional, never required.** The extension is optional and has no capability.
`org.judgmentpack.annotations` MUST NOT appear in `metadata.requiredExtensions`, and the schema's
item pattern there never admits it; an evaluator reports `pack-not-conformant`, never
`unsupported-required-extension`. Listing the name in a supported-extension set changes nothing
(§8.2). §9's general rule applies to what annotations mean: a consumer preserves them when
round-tripping, and one that neither displays nor filters by them may disregard their content. It
does not apply to their shape. The rules below are part of the schema, so a malformed annotation
makes the pack not structurally conforming, and an implementation MUST NOT skip them because the
extension is optional.

**Syntax.** An annotations object is a JSON object with 1 to 16 members (the `base` ceiling, §4.1).

- Each member name is a local identifier (§5) of at most 64 characters. A name that ends in a line
  feed is not a local identifier, whatever a pattern's end anchor admits; the schema also refuses
  U+0000–U+001F, U+007F–U+009F and U+2028–U+202E in a key.
- Each member value is an annotation string, or an array of 1 to 16 annotation strings in which no
  string appears twice. A one-element array and the plain string are both admitted, and are
  different bytes.
- Two annotation strings are equal when they are the same sequence of code points after JSON
  unescaping. There is no normalization, case folding or trimming.
- Core assigns no meaning to any key or value, and meaning MUST NOT be inferred from their spelling.

**Annotation strings.** An annotation string has 1 to 256 characters, counted as code points (a
character outside the Basic Multilingual Plane counts once). After JSON unescaping it contains no
character of the *refused class*: the C0 and C1 controls and delete; the line and paragraph
separators; every bidirectional format character (the Arabic letter mark, the left-to-right and
right-to-left marks, the embeddings and overrides, and the isolates); and every other invisible,
default-ignorable character, the tag characters among them. The refused code points are exactly
U+0000–U+001F, U+007F–U+009F, U+00AD, U+034F, U+061C, U+115F–U+1160, U+17B4–U+17B5, U+180B–U+180F,
U+200B–U+200F, U+2028–U+202E, U+2060–U+206F, U+3164, U+FE00–U+FE0F, U+FEFF, U+FFA0, U+FFF0–U+FFF8,
U+1BCA0–U+1BCA3, U+1D173–U+1D17A and U+E0000–U+E0FFF. It also does not begin or end with a
character of the Unicode property White_Space, which is exactly U+0009–U+000D, U+0020, U+0085,
U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F and U+3000; those the refused class
does not hold are admitted between two other characters. Every other character is admitted. An
annotation is a short machine-comparable label: an emoji sequence that needs a joiner or a
variation selector, and text whose shaping needs a joiner, cannot appear in one, and belong in a
`description`.

**Empty forms.** An empty annotations object, an empty list and an empty string are refused, and
so is a string made only of white space, which begins with it. Absence is the one spelling for "no
annotations".

**Duplicates.** A duplicate member name is refused by the carrier (§2.1). A repeated string in a list
is refused. The same key in two annotations objects is not a duplicate.

**Filtered views (D2).** A consumer that presents a filtered view of a pack, one that omits outcomes,
rules or entries because of their annotations, MUST state in the view that it is filtered, and by
which keys and values. For each kind of item it filters, the view MUST state how many items it shows
and how many the pack holds. Wherever a consumer lists distinct annotation keys or values, or states
a filter, it MUST show every character outside printable ASCII (U+0020–U+007E) in a key or value
unambiguously, in a form from which the reader can recover each such code point. A review made from
a filtered view covers only what the view showed; it is not a review of the pack. A filtered view
is not a pack: it MUST NOT be offered for evaluation, signing or hashing as the pack. A disposition
is always the whole pack's, and omitted items take part in every evaluation. A filtered view is not
redaction: the omitted items remain in the pack's bytes.

## 10. Security and privacy considerations

Implementations must treat packs, sources, citations, extensions, and runtime facts as untrusted
input. They SHOULD define limits for document bytes, nesting depth, collection sizes, string sizes,
and evaluation work.

An implementation claiming evaluator conformance (§3.4) MUST define and document at least its
collection-size and evaluation-work limits, and reaching one of those during an evaluation MUST produce
the `resource-exhaustion` evaluation error of §8.4 rather than a disposition. A documented document or
carrier limit — bytes, nesting depth, or string size — reached while admitting an input instead produces
`malformed-input`: §2.1 refuses such a document rather than processing part of it, and §8.2's preflight
therefore never admits it (§8.4). Either way the evaluation yields an explicit error and never a
disposition; the two classes differ only in which phase the limit belongs to. Defining a limit is not
portability: two conforming implementations may define different limits, so an input above either
one is outside the portable claim. The evaluation corpus therefore keeps its cases well inside any
plausible limit instead of probing one.

Implementations MUST NOT:

- execute code found in strings or extensions;
- fetch source locators during ordinary validation unless explicitly requested;
- treat a URL or publisher name as proof of authenticity;
- expose sensitive evidence merely because a pack references it;
- convert conformance into authorization; or
- continue after silently dropping malformed or unsupported required content.

**Limits.** Any limit an implementation applies to the pack as presented is a document limit,
whatever the implementation calls it: bytes, nesting depth, string size, or a count of the parsed
values or nodes of the whole document. Document limits apply to `P` as presented, as to any input,
and count every annotation and every entry; a pack refused by one is refused as any input over that
limit is. `EF(P)` (§8.5) is never admitted, and is never measured against a document limit. A
collection-size or work counter charged while evaluating applies to the work `EF(P)` requires, and
expansion is charged per reference: each reference costs what its inline twin would. An
implementation MUST NOT charge an evaluation-phase counter for annotations, for value-set objects,
or for the entries of a set that no condition references. A set referenced by many conditions
expands to a large `EF(P)`; an evaluator SHOULD resolve a reference to the shared array, not copy
it.

**Untrusted display data (D1).** Annotation keys and strings, value-set and entry descriptions, and
entry values when displayed, are display data from the pack's author, as untrusted as every other
pack string. A consumer that displays one:

- MUST render it as text, escaped for the output context, and MUST NOT let that context interpret it
  as markup, a template, a spreadsheet formula or a terminal control sequence;
- MUST NOT resolve, fetch or otherwise dereference it;
- MUST NOT treat it as naming anything in the pack: an annotation value equal to an outcome id names
  no outcome;
- MUST NOT present it as a review, an approval, a verified property, or a classification that
  anything other than the author's statement established;
- MUST isolate each annotation key and string it shows inline with other text, so that a value's
  direction does not reorder the text around it, and SHOULD isolate the other display data the same
  way;
- MUST, where it lists distinct annotation keys or values or states a filter, show them as D2
  requires (§9.2); and
- SHOULD show annotations as the author's labels, visually distinct from Core members.

D1 and D2 (§9.2) bind any consumer that displays or filters annotations. They bind what is
displayed to a person: a machine-readable form that carries each key and value with its exact code
points, such as JSON a program reads, is data, not a display and not a listing under D2, and the
consumer that displays a key or value read from it is the one bound. No Core conformance class
tests display. Annotations travel with the pack; authors should put neither secrets nor personal data
in them.

## 11. Versioning

`specVersion` identifies this specification draft. `version` identifies the pack revision. They are
independent.

During `0.x`, any specification release may be breaking. A future stable specification must define
reader, writer, and semantic compatibility separately and supply machine-readable migration cases.

A published pack version SHOULD be immutable. Changed content SHOULD receive a new version.

Compatibility from `0.3.0` is explicit:

- **Reader and writer:** a `0.3.0` reader refuses a pack declaring `0.5.0`, by the exact selector,
  and does not acquire support by ignoring or replacing it. The `0.3.0` schema also refuses each new
  shape: the reserved annotations key, the root `valueSets` and the `valueSet` member.
- **Semantic:** for a pack that uses neither feature, `EF(P)` is `P` (§8.5), so `0.5.0` changes no
  result for it, apart from the one shape §9.1's reading of an `extensions` object refuses.
- **Migrating up:** a local identifier, an extension name, a pack version or a decimal operand that
  ends in a line terminator is refused in every engine (§§2.2, 4, 5 and 9). Core `0.3.0`'s grammar,
  read as ECMA-262 reads it, never admitted one; only a validator whose `$` admits a final line feed
  did. One other `0.3.0` shape is refused: a pack whose required name appears only under a member
  named `extensions` inside data, by §9.1's reading. Such a pack moves up by also adding the name as
  a key of an `extensions` object the schema defines. Otherwise changing only the selector is enough, and evaluation is unchanged.
  Labels kept in a vendor extension MAY be moved to the reserved name by hand once they meet §9.2;
  there is no automatic coercion. An inline list MAY be replaced by a reference. Each such edit
  changes the bytes, so the pack SHOULD receive a new `version`.
- **Migrating down:** `EF(P)` with the selector changed is evaluation-equivalent within §10's limit
  rule, but loses the annotations and the entry descriptions.
- **Profiles:** no new profile and no new capability. A reader that lists `extended` commits to the
  extended values of the new rows of §4.1, as to every row.
- **Released artifacts:** the `0.3.0` schema stays published at the identifier it was published
  under, and its text and corpora stay at the `v0.3.0` tag, unchanged.

The working selector `0.4.0-draft`, under which this text was staged, was never released, and no
`specVersion` `0.4.0` exists: release tag `v0.4.0` carries `0.3.0` unchanged, so this text is released
as `0.5.0` under the versioning rule (VERSIONING.md). A `0.5.0` reader refuses a pack declaring
`0.4.0-draft` by the exact selector. A pack written to it moves up by changing its `specVersion` to
`0.5.0`, which changes its bytes and digest, and must then satisfy these rules.

Compatibility from `0.2.0-draft` to `0.3.0`, unchanged here, is explicit rather than inferred from a
shared `0.x` prefix:

- **Reader and writer:** an older reader does not acquire `0.3.0` support by ignoring or replacing
  the exact selector. `0.3.0` adds the optional `profile` member and escalation `routes`; these
  newer-only shapes are not accepted by the historical structural schema. Writers targeting an
  older selector must satisfy that older version's requirements and cannot emit these members under it.
  Readers implementing multiple versions dispatch on the complete selector and preserve the older
  contract; supporting the current version does not reinterpret historical documents.
- **Carrier:** §2.1 now requires Unicode escapes in the UTF-16 surrogate range to form well-formed pairs. A lone
  `\uD800` escape in a title was accepted by the published `0.2.0-draft` carrier and structural
  schema but is refused as malformed input here. Replacing only `specVersion` cannot repair it;
  the author must supply an intended Unicode scalar value or a valid surrogate pair, not silently
  substitute a replacement character.
- **Structural and semantic migration:** revalidate the document under §§3.1–3.3, including its
  selected document profile, supported ceilings and escalation form. Selector-only migration is
  sufficient only when the document already satisfies those requirements. Otherwise deliberate
  content changes and review are needed; there is no automatic transformation or unchanged-verdict
  promise for every historical document.
- **Evaluation:** re-declaration opts into this release's exact §§7–8 evaluator semantics and
  evaluation corpus, including the selected escalation behavior. It is not semantically inert and
  creates, transfers or strengthens no implementation-conformance claim.

An unedited `0.2.0-draft` or `0.3.0` pack is not structurally conforming to `0.5.0` because its
selector is exact (§4). The `0.1.0-draft`, `0.2.0-draft` and `0.3.0` schemas remain published for
documents retaining those selectors, with historical rules and identities preserved.

An evaluator-conformance claim (§3.4) attaches to one exact `specVersion` and to the evaluation
corpus published with it. It is not inherited by a later or an earlier version, and re-declaring a
pack acquires nothing for the implementations that read it.

## 12. Normative references

- [BCP 14](https://www.rfc-editor.org/info/bcp14), including RFC 2119 and RFC 8174, defines the
  requirement keywords used by this document.
- [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) defines JSON.
- [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986) defines URI syntax.
- [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339) defines the date and date-time forms used by
  schema format assertions.
- [RFC 6901](https://www.rfc-editor.org/rfc/rfc6901) defines the JSON Pointer syntax admitted by
  `fact.path`.
- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) defines the JSON canonicalization used by §8.3
  when two dispositions are compared byte for byte.
- [JSON Schema Core, Draft 2020-12](https://json-schema.org/draft/2020-12/json-schema-core) and
  [JSON Schema Validation, Draft 2020-12](https://json-schema.org/draft/2020-12/json-schema-validation)
  define the schema dialect and validation keywords used by the normative schema.

## 13. Open questions

Whether portable rule evaluation belongs in Core or in a separate profile is closed: §3.4 places the
class in Core, so the error contract and the disposition shape live in one place that a later
evaluation profile can build on rather than restate. Before a candidate stable core, the project must
still resolve:

- exact unit, date/time, and normalization semantics beyond the decimal-string ordering of §7.4;
- a `between` fact operator with an inclusive lower bound and exclusive upper bound; it could make
  the two-comparison band of §3.3.1 one line and exact by construction, but adding an `op` is a
  schema change that older evaluators would refuse, so evidence should first count use of the
  two-comparison rewrite;
- whether equality between syntactically valid but arithmetically unrepresentable JSON numbers is
  `unknown`, as §7.4's incomparable-value rule implies, or an explicit input error. This is the single
  seam §8.3 excludes from its byte-agreement requirement, and the evaluation corpus carries no row for
  it because a row cannot state an expected result until the question is closed;
- an interchange form for evidence beyond §8.2's tri-state, and whether §8.2 grows into it;
- the minimum a trace must surface, including whether it must surface a true rule that a forced
  outcome skipped;
- a machine-readable diagnostic contract, for document validation and for the §8.4 error classes;
- the minimum provenance and lineage model;
- whether authority bindings belong in optional profiles;
- content identity, canonicalization, and signatures;
- imports and content-addressed dependencies; and
- negotiation beyond the document ceiling profiles in §4.1.

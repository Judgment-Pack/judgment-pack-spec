# Judgment Pack Core 0.4.0-draft (staged draft)

## Status

**This is a staged draft. It is normative for nothing.** It restates
[RFC 0031](../../rfcs/0031-annotations-and-value-sets.md), a Draft, as the text Core would gain in
the next `specVersion` after `0.3.0`, so that implementations can admit packs that use annotations
and value sets and run the staged vectors against them. It is not a release, it is not published on
the project's site, no release bundle carries it, and it creates no conformance claim. Every MUST,
SHOULD and MAY below is proposed wording. RFC 0031 has not been accepted, and its review standing is
the RFC's own.

`0.4.0-draft` is a **working selector**, chosen so that the staged artifacts can name an exact
`specVersion`. No maintainer has assigned it. Core `0.3.0` is the first `specVersion` without the
retired `-draft` suffix ([VERSIONING.md](../../VERSIONING.md)), and `specVersion` `0.4.0` is not
assigned; the suffix here marks a selector that no release carries. When the next `specVersion` is
opened, its number is the maintainers' to choose, and the staged artifacts take it.

This document states only what changes from [Core `0.3.0`](../judgment-pack-core.md). A section it
does not name reads as in Core `0.3.0`, with the selector `0.3.0` read as `0.4.0-draft`. Section
numbers are the ones the draft gives Core; a section marked *(new)* has no counterpart in `0.3.0`.
Where this text and RFC 0031 differ, the difference is a defect to report, not a choice between them.

In this document an *annotation* is a key and its value inside the reserved extension
`org.judgmentpack.annotations`. It has nothing to do with the JSON Schema sense, in which keywords
such as `format` produce annotations a validator collects without asserting them.

The staged artifacts are:

| Artifact | Location |
| --- | --- |
| Structural schema, `$id` `https://judgmentpack.org/schema/0.4.0-draft/judgment-pack-core.schema.json` | [`schema/staged/judgment-pack-core-0.4.0-draft.schema.json`](../../schema/staged/judgment-pack-core-0.4.0-draft.schema.json) |
| Document cases | `conformance/staged/`, with its README |
| Evaluation rows | `conformance/evaluation/staged/annotations-value-sets/`, with its README |
| Example pack | `examples/staged/expense-approval-annotated.json` |

The schema is the Core `0.3.0` schema with RFC 0031's three fragments (its §§1.7, 2.7 and 3.3) and
nothing else, apart from its `$id`, its description and the selector.

## 2. Normative representation

### 2.1 JSON carrier

Unchanged. A duplicate member name inside an annotations object is refused by the carrier
(`JPS-CARRIER-DUPLICATE-MEMBER`), as in any JSON object.

## 3. Conformance classes

### 3.3 Semantically conforming document

The list of conditions gains two items:

- value-set identifiers are unique within `valueSets`;
- every `valueSet` member of a fact condition names exactly one declared value set (§7.4).

Two sets with one `id` make the document semantically non-conforming (`JPS-SEMANTIC-DUPLICATE-ID`).
A `valueSet` member that names no declared set does too (`JPS-SEMANTIC-UNRESOLVED-VALUE-SET`, at
that member), in every condition position: the root `applicability`, each rule's `when`, each
exception's `when`, and every condition nested in them under `all`, `any` and `not`. So does a
reference in a pack with no `valueSets` member, or with `valueSets: []`. A reference that names an
id held only by another kind of object, such as an outcome, names no declared set: identifiers are
collection-local, and `valueSet` looks only in `valueSets`.

"Required extension capabilities are declared" reads with §9.1's meaning of an `extensions` object.

#### 3.3.1 Recommended rule-overlap check

The check reads a reference as its set's values: the true set of an `in` condition with a
reference is the set of its entries' values, as for an inline operand. A validator MAY run the check
on the pack's evaluation form (§8.5).

Two further advisories are recommended. Like `JPS-RULES-OVERLAP`, they are not conformance
requirements and never change a document's conformance:

- **`JPS-VALUE-SET-DUPLICATE-VALUE`.** A tool that can decide equality of two entry values SHOULD
  report each entry whose value equals an earlier entry's in the same set, at the later entry's
  `value`. Equality is §7.4's: numbers by mathematical value (`1`, `1.0`, `1e0` and `10E-1` are
  one value, and so are `0` and `-0`), strings by code points (the NFC and NFD spellings of one text
  are two values), arrays item by item in order, objects by member name and value regardless of
  member order, and no coercion (`1` and `"1"` are distinct, and so are `"1.0"` and `"1.00"`). A tool
  that can compare a pair only through binary floating point cannot decide it, and reports nothing
  for that pair. Normalizing a number literal needs no expansion of its exponent, and a tool SHOULD
  NOT expand one.
- **`JPS-VALUE-SET-UNREFERENCED`.** A pack-design tool SHOULD report a set that no condition
  references.

Where these two advisories live is open (RFC 0031, Unresolved question 3): beside
`JPS-RULES-OVERLAP` in the document corpus's advisory vocabulary, or in the report contract
[RFC 0027](../../rfcs/0027-pack-design-advisories.md) proposes. The staged document cases state the
document result of each advisory case, which is `valid`, and do not state the advisory.

## 4. Root object

The root table gains one row, and two rows read:

| Member | Required | Meaning |
| --- | ---: | --- |
| `specVersion` | yes | Exact value `0.4.0-draft` |
| `valueSets` | no | Declared value sets (§6.9) |
| `extensions` | no | Namespaced extension values, including annotations (§9.2) |

`valueSets` is an array of value-set objects. An empty array is admitted and declares no set, as for
Core's other optional root collections. Two set objects equal under JSON Schema's equality are
refused by the schema (`JPS-STRUCTURE-UNIQUE-ITEMS`).

Collection order is preserved for authoring and display but MUST NOT determine rule priority. That
rule covers `valueSets` and the entries of each set: their order carries no evaluation meaning. Entry
order fixes the order of an expanded reference in the evaluation form (§8.5), which only makes that
form deterministic.

### 4.1 Document ceiling profiles

The ceiling table gains six rows. Characters are Unicode code points, as JSON Schema counts them.

| Format and resource | `base` | `extended` |
| --- | ---: | ---: |
| Core annotation keys per annotations object | 16 | 32 |
| Core annotation strings per list | 16 | 32 |
| Core annotation key characters | 64 | 128 |
| Core annotation string characters | 256 | 512 |
| Core value sets | 64 | 128 |
| Core entries per value set | 512 | 1024 |

The schema carries the `base` maxima, as for every row. A reader supporting `extended` applies the
extended value of every row, these included.

There is no ceiling on the total size of an annotations object; at `base` one holds at most
16 × (64 + 16 × 256) = 66,560 characters, and at `extended` 528,384. These rows are not outcome, rule
or reference maxima, and none is defined. The maximum on entries does not limit an inline `in`
operand, on which Core sets no maximum.

## 5. Identity and references

All rule, outcome, source, evidence-requirement, exception and value-set references resolve within
one document.

Annotations, value sets and references are part of the pack's bytes, so they are part of every
digest and every exact-identity rule that covers the pack. A pack whose only change is an annotation
has changed content (§11). This document defines no canonical form or digest of a pack, and no
serialization of the evaluation form (§8.5): evaluation forms are compared as JSON values under §7.4
equality. Two packs with equal evaluation forms evaluate alike within §8.5's limit rule, and are not
the same pack.

Member order in an annotations object carries no meaning. The order of strings in an annotation list
is part of the bytes and carries no evaluation meaning; consumers SHOULD display it in document
order.

## 6. Core objects

### 6.9 Value set *(new)*

A value-set object has these members and no others:

| Member | Required | Value |
| --- | ---: | --- |
| `id` | yes | a local identifier (§5), unique within `valueSets` |
| `description` | no | a non-empty string |
| `entries` | yes | an array of 1 to 512 entries (the `base` ceiling, §4.1) |

A value-set object has no `extensions` member: one on a set, whatever it holds, is an unknown member
(`JPS-STRUCTURE-UNKNOWN-MEMBER`). A set and an outcome may share an id, because the member that
names a set fixes the kind.

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
  member (`JPS-STRUCTURE-UNKNOWN-MEMBER`). The evaluation form removes the sets (§8.5), so a vendor
  extension that lived only in a set or an entry would vanish from it, and a required one would be
  inert. Annotations can stay, because they are never requirable (§9.2).
- **Repeated values.** Two entries of one set may have equal values. That is not a conformance error
  at any layer. A repeated entry changes no evaluation result, since an inline `in` operand already
  admits repeated items. A consumer shows each entry as written, with its own description and
  annotations. §3.3.1 recommends an advisory.
- **No nesting.** A set references no other set, and an entry has no `valueSet` member
  (`JPS-STRUCTURE-UNKNOWN-MEMBER`). An entry value that looks like a reference, such as
  `{"valueSet": "tier-codes"}`, is a literal JSON object, compared as one. There is no union,
  intersection or difference of sets.
- **Unreferenced sets.** A set that no condition references is admitted and inert. Its entries take
  no part in evaluation, and no collection-size or work limit counts them (§10). §3.3.1 recommends an
  advisory.

`valueSets` is a Core member, not an extension: a consumer that ignored the sets could not evaluate a
condition that references one.

## 7. Condition interpretation

### 7.4 Fact conditions

A fact condition MAY carry `valueSet`, a local identifier naming a declared set, in place of
`value`.

- A fact condition carries exactly one of `value` and `valueSet`. Carrying both is a structural
  refusal (`JPS-STRUCTURE-VALUE-SET-REFERENCE`, at the condition). Carrying neither is the existing
  refusal of a fact condition without its operand (`JPS-STRUCTURE-REQUIRED-MEMBER`, at `…/value`).
- `valueSet` is admitted only with the operator `in`. With any other operator it is a structural
  refusal (`JPS-STRUCTURE-VALUE-SET-REFERENCE`, at `…/operator`).
- The rules for `value` are unchanged. An object in `value`, such as `"value": {"valueSet": "x"}`, is
  still refused (`JPS-STRUCTURE-IN-OPERAND`); it is not a reference.
- A reference resolves within the document (§3.3).

A reference behaves exactly as its inline array, the `value` of each entry of the named set in entry
order (§8.5): the same equality, the same `unknown` for an absent path, and the same reading under
`not`. The order of sets, and of entries within a set, changes nothing, because `in` tests
membership. Where this section leaves a comparison with a number open (§13), the open comparison is
the inline array's; a reference neither adds an input to it nor takes one out.

## 8. Resolution model

### 8.5 The evaluation form *(new)*

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

The rest of §9 is unchanged. Its sentence on reserved names reads: "Names beginning with
`org.judgmentpack.` are reserved for specification-defined extensions (§9.1)."

### 9.1 Specification-defined extensions *(new)*

A specification-defined extension is one whose name begins with `org.judgmentpack.` and which this
specification defines. Its value is governed by its definition, which qualifies §9's "Values may be
any JSON value". Each definition states the `extensions` objects in which its name may appear and
whether the name may be listed in `metadata.requiredExtensions`. Every other name beginning with
`org.judgmentpack.` remains refused in every `extensions` object
(`JPS-STRUCTURE-EXTENSION-NAME`, or `JPS-STRUCTURE-UNKNOWN-MEMBER` in an entry's, §6.9).

An `extensions` object, in this section and in §3.3, is one the schema defines as a member of a Core
object. A member named `extensions` inside an operand, an entry value or an extension's own value is
data, not an `extensions` object. So "every name in `metadata.requiredExtensions` MUST appear as a
key in at least one `extensions` object" counts only those objects: a required name that appears only
inside an operand or an entry value is missing (`JPS-SEMANTIC-MISSING-REQUIRED-EXTENSION`).

This draft defines one such extension, `org.judgmentpack.annotations` (§9.2).
[RFC 0016](../../rfcs/0016-outcome-values.md), also a Draft, would add its own name under this
paragraph; the two records share it.

### 9.2 Annotations *(new)*

**Name and positions.** The extension `org.judgmentpack.annotations` holds an *annotations object*.
It MAY appear as a key of exactly these `extensions` objects: the root's, each outcome's, each rule's
and each value-set entry's (§6.9). In every other `extensions` object (the decision's, each evidence
requirement's, each source's, each exception's, the escalation's and the metadata's) it remains
refused (`JPS-STRUCTURE-EXTENSION-NAME`). An annotations object describes only the object that
carries it: there is no inheritance and no merging.

**Optional, never required.** The extension is optional and has no capability.
`org.judgmentpack.annotations` MUST NOT appear in `metadata.requiredExtensions`, and the schema's
item pattern there never admits it (`JPS-STRUCTURE-EXTENSION-NAME`); an evaluator reports
`pack-not-conformant`, never `unsupported-required-extension`. Listing the name in a
supported-extension set changes nothing. §9's general rule applies to what annotations mean: a
consumer preserves them when round-tripping, and one that neither displays nor filters by them may
disregard their content. It does not apply to their shape. The rules below are part of the schema,
so a malformed annotation makes the pack not structurally conforming, and an implementation MUST NOT
skip them because the extension is optional.

**Syntax.** An annotations object is a JSON object with 1 to 16 members (the `base` ceiling, §4.1).

- Each member name is a local identifier (§5) of at most 64 characters. A name that ends in a line
  feed is not a local identifier, whatever a pattern's end anchor admits; the schema also refuses
  every character of the refused class below in a key, so the rule holds under every engine.
- Each member value is an annotation string, or an array of 1 to 16 annotation strings in which no
  string appears twice. A one-element array and the plain string are both admitted, and are
  different bytes.
- Two annotation strings are equal when they are the same sequence of code points after JSON
  unescaping. There is no normalization, case folding or trimming.
- Core assigns no meaning to any key or value, and meaning MUST NOT be inferred from their spelling.

**Annotation strings.** An annotation string has 1 to 256 characters, counted as code points (a
character outside the Basic Multilingual Plane counts once). After JSON unescaping it contains none
of U+0000–U+001F, U+007F–U+009F and U+2028–U+202E: the C0 and C1 controls, delete, the line and
paragraph separators, and the bidirectional embeddings and overrides. The marks U+200E and U+200F,
the isolates U+2066–U+2069 and every other character are admitted.

**Empty forms.** An empty annotations object (`JPS-STRUCTURE-MIN-PROPERTIES`), an empty list
(`JPS-STRUCTURE-COLLECTION-ARITY`) and an empty string (`JPS-STRUCTURE-MIN-LENGTH`) are refused.
Absence is the one spelling for "no annotations".

**Duplicates.** A duplicate member name is refused by the carrier (§2.1). A repeated string in a list
is refused (`JPS-STRUCTURE-UNIQUE-ITEMS`). The same key in two annotations objects is not a
duplicate.

**Filtered views (D2).** A consumer that presents a filtered view of a pack, one that omits outcomes,
rules or entries because of their annotations, MUST state in the view that it is filtered, and by
which keys and values. The view SHOULD state how many items it omits. A filtered view is not a pack:
it MUST NOT be offered for evaluation, signing or hashing as the pack. A disposition is always the
whole pack's, and omitted items take part in every evaluation. A filtered view is not redaction: the
omitted items remain in the pack's bytes.

## 10. Security and privacy considerations

**Limits.** Document and carrier limits (bytes, nesting depth, string size) apply to `P` as presented,
as to any input; a pack refused by one is refused as any input over that limit is. `EF(P)` is never
admitted, and is never measured against a document limit. Collection-size and evaluation-work limits
apply to the work `EF(P)` requires: a reference costs what its inline array costs. An implementation
MUST NOT charge a collection-size limit to annotations, to value-set objects, or to the entries of a
set that no condition references. A set referenced by many conditions expands to a large `EF(P)`; an
evaluator SHOULD resolve a reference to the shared array, not copy it.

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
- SHOULD, where it lists distinct annotation values or states a filter, make default-ignorable and
  format characters visible; and
- SHOULD show annotations as the author's labels, visually distinct from Core members.

D1 and D2 (§9.2) bind any consumer that displays or filters annotations. No Core conformance class
tests display. Annotations travel with the pack; authors should put neither secrets nor personal data
in them.

## 11. Versioning

Compatibility from `0.3.0` is explicit:

- **Reader and writer.** A `0.3.0` reader refuses a pack declaring `0.4.0-draft`, by the exact
  selector, and does not acquire support by ignoring or replacing it. The `0.3.0` schema also refuses
  each new shape: the reserved key, the root `valueSets` and the `valueSet` member.
- **Semantic.** For a pack that uses neither feature, `EF(P)` is `P`, so this draft changes no
  result for it.
- **Migrating up.** No `0.3.0` shape is refused by these rules: changing only the selector is enough,
  and evaluation is unchanged. Labels kept in a vendor extension MAY be moved to the reserved name by
  hand once they meet §9.2; there is no automatic coercion. An inline list MAY be replaced by a
  reference. Each such edit changes the bytes, so the pack SHOULD receive a new `version`.
- **Migrating down.** `EF(P)` with the selector changed is evaluation-equivalent within §10's limit
  rule, but loses the annotations and the entry descriptions.
- **Profiles.** No new profile and no new capability. A reader that lists `extended` commits to the
  extended values of the new rows, as to every row.
- **Released artifacts.** The released `0.3.0` schema, Core text and corpora are unchanged.

## Staged conformance

The staged vectors are hand-written, never recorded from a run. They are in no corpus; the READMEs
of `conformance/staged/` and `conformance/evaluation/staged/annotations-value-sets/` state their
standing.

Codes are provisional test metadata. A structural code follows one rule: Core's code for the
definition, where Core has one (`JPS-STRUCTURE-LOCAL-ID`, `JPS-STRUCTURE-EXTENSION-NAME`,
`JPS-STRUCTURE-IN-OPERAND`); otherwise Core's code for the keyword that fails, where Core's corpus
uses one; otherwise one new code per keyword. Two refusals take a code mapped from another keyword:
`JPS-STRUCTURE-VALUE-SET-REFERENCE`, from `not` at the condition and from `const` at `…/operator`;
and `JPS-STRUCTURE-LOCAL-ID`, from the `not` under an annotations object's `propertyNames`.

This draft has seven provisional codes, for `0.4.0-draft` only:

| Code | Layer | Where |
| --- | --- | --- |
| `JPS-STRUCTURE-MAX-LENGTH` | structural | an annotation key or string over its ceiling (§§4.1, 9.2) |
| `JPS-STRUCTURE-MIN-PROPERTIES` | structural | an empty annotations object (§9.2) |
| `JPS-STRUCTURE-MAX-PROPERTIES` | structural | an annotations object over its key ceiling (§§4.1, 9.2) |
| `JPS-STRUCTURE-VALUE-SET-REFERENCE` | structural | `value` beside `valueSet`, or `valueSet` with an operator other than `in` (§7.4) |
| `JPS-SEMANTIC-UNRESOLVED-VALUE-SET` | semantic | a `valueSet` naming no declared set (§3.3) |
| `JPS-VALUE-SET-DUPLICATE-VALUE` | advisory, outside conformance | a repeated entry value (§3.3.1) |
| `JPS-VALUE-SET-UNREFERENCED` | advisory, outside conformance | a set no condition references (§3.3.1) |

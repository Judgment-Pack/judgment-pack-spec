# RFC 0031: Annotations and annotated value sets

- Status: Draft
- Type: Standards track, draft maturity. A Core amendment: one specification-defined extension in
  the reserved namespace, one new root member and one new fact-condition member.
- Created: 2026-11-11
- Target: the next Core `specVersion` after `0.3.0`. No number is assigned here. A release tag is
  not a selector: release `v0.4.0` carries `specVersion` `0.3.0`.
- Issue: [#301](https://github.com/Judgment-Pack/judgment-pack-spec/issues/301)

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **This record is normative for nothing.** Every MUST, SHOULD and MAY below is proposed wording for
> the Core version that might adopt it. This change edits neither the published schema, the Core
> text, nor any released conformance corpus, and it creates no conformance claim. The vectors in
> [Conformance](#conformance) are named and described here; none is a corpus file.
>
> **Review standing.** [RFC 0009](0009-interim-review-regime.md) requires a recorded adversarial
> review by a model from a different vendor, with a written disposition for each finding, on the
> pull request that creates this RFC. That review has not happened, and this record does not
> claim it.
>
> **Terminology.** In this record an *annotation* is a key and its value inside the reserved
> extension `org.judgmentpack.annotations`. The word has nothing to do with the JSON Schema sense,
> in which keywords such as `format` and `default` produce *annotations* that a validator
> collects without asserting them. Core uses that sense in its §3.2 and §4.1. Where this record means
> it, it says "JSON Schema annotation".
>
> **Section numbers.** A bare section number, such as §2.4, is this record's own. `Core §` marks
> a section of the Core specification. A line number cites
> [`spec/judgment-pack-core.md`](../spec/judgment-pack-core.md) as it stood when this record was
> created.

## Summary

Two features that help people read and maintain a pack, neither of which changes what a pack
decides.

1. **Annotations.** The pack, each outcome and each rule may carry short labels. A label is a key
   from the local-identifier grammar, mapped to a string or to a list of distinct strings, for
   example `"category": ["intake", "completeness"]` or `"review-cycle": "quarterly"`. Labels live in
   the reserved extension `org.judgmentpack.annotations` inside the existing `extensions` member.
   No new member is added to the pack, the outcome or the rule. The extension is optional, never
   required, and inert: it changes no conformance result outside its own rules and no
   evaluation result at all.
2. **Annotated value sets.** A pack may declare named sets of values once, at its root, and a
   fact condition with operator `in` may name one instead of repeating the list inline. Each entry
   may carry a description and annotations. A reference behaves exactly as the inline list of the
   entries' values.

Both are defined by one rule, the **evaluation form** (§4 below). An evaluator MUST give a pack
the result it gives to the same pack with every annotation removed and every reference replaced by
its inline list. Inertness, substitution and the absence of any new reason or error all follow
from that rule.

The decision recorded on the issue chose the reserved extension over a new `annotations` member.
The alternative and the reasons are under [Alternatives](#alternatives).

## Problem

**Labels.** Authors and reviewers want to group and filter the parts of a pack: which rules belong
to intake, which outcomes are on the standard tier, which rules are reviewed quarterly. Core has no
place for this. An author can put labels in an optional vendor extension today (Core §9), but every tool
then picks its own name and shape, so no two tools can share a view, and a consumer must accept any
JSON value under any name. Core states that an optional extension MUST NOT change Core semantics
(Core §9), but no evaluation row checks it.

**Repeated lists.** A list of admitted values often matters to more than one condition. Today each
condition carries its own copy. Two rules meant to be exclusive stay exclusive only while every
copy agrees, and nothing in the pack says that they are meant to be the same list. A list also has
no place to say what an entry means.

**Who is affected.** Authors and reviewers, who read packs. Tools that show a pack, which need one
portable place for labels and one rule for how to show them safely. Evaluators, which must be able
to ignore labels without risk and must agree on what a reference means.

## Evidence

- **The request.** Issue [#301](https://github.com/Judgment-Pack/judgment-pack-spec/issues/301)
  asks for inert annotations on packs, outcomes and rules, and for annotated value sets. The
  decision recorded on the issue places annotations in the reserved namespace.
- **A repeated list in a published example.** In
  [`examples/minimal-expense-approval.json`](../examples/minimal-expense-approval.json), the rule
  `prohibited-category` compares a category with `["personal", "cash-equivalent"]` (line 73), and
  the rule `ordinary-expense` carries the same list under `not` (line 114). The two rules name
  different outcomes. They are exclusive on the category only while the two copies agree. If a
  value is added to the first copy and not to the second, an expense in that category makes both
  rules true, which is a conflict (Core §8).
- **The slot exists and is closed.** Core §9 reserves names beginning `org.judgmentpack.` "for future
  specification-defined extensions" and defines none. The published schema refuses every such name
  as an `extensions` key and as a `metadata.requiredExtensions` item.
- **Prior proposal for the same slot.** [RFC 0016](0016-outcome-values.md) proposes
  `org.judgmentpack.outcome-values` and records the same two schema refusals that would need to
  admit its name.
- **What is missing.** No published pack in this repository carries labels, and none uses a
  shared list on purpose. No pack therefore shows what sizes labels and sets reach in practice. The
  ceilings in §7 are reasoned, not measured (Unresolved question 1).

While this record was drafted, its schema fragments and examples were checked against a scratch
copy of the Core schema with the fragments applied, using a general-purpose JSON Schema validator
and a short checker for the semantic rules. That check is not committed and is not implementation
evidence.

## Specification

### 1. Annotations

#### 1.1 Name and positions (A1)

The extension name is `org.judgmentpack.annotations`. Its value is an *annotations object*
(§1.3).

It MAY appear as a key of exactly these `extensions` objects:

- the root `extensions` (the pack);
- each outcome's `extensions` (Core §6.4);
- each rule's `extensions` (Core §6.5); and
- each value-set entry's `extensions` (§2.3).

In every other `extensions` object, the name remains refused, as every reserved name is today.
Those objects are the decision's, each evidence requirement's, each source's, each exception's, the
escalation's, the metadata's and each value-set object's. A structural validator reports such a
document as not structurally conforming (`JPS-STRUCTURE-EXTENSION-NAME`).

Every other name beginning `org.judgmentpack.` remains refused in every `extensions` object.

An annotations object describes only the object that carries it. This record defines no
inheritance and no merging. A rule does not acquire the pack's annotations, and an entry does not
acquire its set's.

#### 1.2 Optional, never required (A2)

The annotations extension is optional and has no capability.

`org.judgmentpack.annotations` MUST NOT appear in `metadata.requiredExtensions`. The schema keeps
refusing every reserved name there, so a pack that lists it is not structurally conforming
(`JPS-STRUCTURE-EXTENSION-NAME`). An evaluator therefore reports `pack-not-conformant`, never
`unsupported-required-extension` (Core §8.4). Listing the name in an implementation's
supported-extension set changes nothing.

The reason is that an extension with no effect on evaluation gives a consumer nothing to
support. Making it requirable would let a pack force a refusal from every evaluator that does
not list a name whose presence changes no result.

Core §9's general rule applies: a consumer preserves annotations when round-tripping a pack, and a
consumer that does not display them may otherwise ignore them. A structural validator may not
ignore them: their shape is part of the schema (§1.7).

#### 1.3 Syntax (A3)

An annotations object is a JSON object with 1 to 16 members (the base ceiling, §7).

- **Keys.** Each member name matches Core's local-identifier grammar
  `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$` (Core §5) and has at most 64 characters.
- **Values.** Each member value is either an annotation string (§1.4), or an array of 1 to 16
  annotation strings in which no string appears twice.
- **String equality.** Two annotation strings are equal when they are the same sequence of Unicode
  code points, after JSON unescaping. There is no Unicode normalization, no case folding and no
  trimming. This is JSON Schema's `uniqueItems` equality for strings.

A one-element array and the plain string are both admitted. A key whose list shrinks to one value
does not have to change type. The two spellings are different bytes (§5). §8 says how a consumer
treats them when filtering.

Core assigns no meaning to any key or value. As with identifiers (Core §5), meaning MUST NOT be
inferred from the spelling of a key or value.

#### 1.4 Annotation strings (A4)

An annotation string:

- has 1 to 256 characters, counted as Unicode code points, which is how JSON Schema `maxLength`
  counts them. A character outside the Basic Multilingual Plane counts once, though it is two
  UTF-16 code units and four UTF-8 bytes;
- contains, after JSON unescaping, none of U+0000–U+001F (C0 controls, including tab, line feed
  and escape), U+007F–U+009F (delete and the C1 controls, including U+0085 and the single-character
  control sequence introducer U+009B), U+2028 or U+2029.

An annotation string is single-line text, meant as a filter key or a short label in compact views
such as chips, table cells and terminal output. A line break or a terminal control sequence there
breaks the view or takes control of a terminal.

Every other character is admitted, including the bidirectional formatting characters (U+200E,
U+200F, U+202A–U+202E, U+2066–U+2069) and other format characters. Core admits them in every other
pack string. Refusing them only here would not remove them from the pack, and right-to-left labels
are legitimate text. §6 says how consumers display them.

#### 1.5 Empty forms (A5)

These are refused:

- an empty annotations object `{}` (`JPS-STRUCTURE-COLLECTION-ARITY`);
- an empty list `[]` (`JPS-STRUCTURE-COLLECTION-ARITY`); and
- an empty string `""` (`JPS-STRUCTURE-MIN-LENGTH`).

Absence is the one spelling for "no annotations" and for "no value for this key", so "has the key"
and "has a value for the key" never differ. This matches Core's `nonEmptyString` for its other
human-readable strings.

#### 1.6 Duplicates (A6)

- A duplicate member name in an annotations object is refused by the carrier, as in any JSON
  object (Core §2.1, `JPS-CARRIER-DUPLICATE-MEMBER`).
- A repeated string in a list is a structural refusal (`JPS-STRUCTURE-UNIQUE-ITEMS`).
- The same key in two annotations objects, for example on the pack and on a rule, is not a
  duplicate. Each object is independent (§1.1).

#### 1.7 Schema fragment

These definitions would be added to `$defs`. `annotatedExtensions` replaces `extensions` as the
type of the root's, each outcome's and each rule's `extensions` member, and is the type of an
entry's `extensions` (§2.7). Every other `extensions` member keeps the existing `extensions`
definition, which refuses every reserved name. `metadata.requiredExtensions` is unchanged.

```json
{
  "annotationString": {
    "type": "string",
    "minLength": 1,
    "maxLength": 256,
    "pattern": "^[^\\u0000-\\u001F\\u007F-\\u009F\\u2028\\u2029]*$"
  },
  "annotations": {
    "type": "object",
    "minProperties": 1,
    "maxProperties": 16,
    "propertyNames": {
      "pattern": "^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$",
      "maxLength": 64
    },
    "additionalProperties": {
      "oneOf": [
        { "$ref": "#/$defs/annotationString" },
        {
          "type": "array",
          "minItems": 1,
          "maxItems": 16,
          "uniqueItems": true,
          "items": { "$ref": "#/$defs/annotationString" }
        }
      ]
    }
  },
  "annotatedExtensions": {
    "type": "object",
    "propertyNames": {
      "anyOf": [
        { "const": "org.judgmentpack.annotations" },
        { "pattern": "^(?!org\\.judgmentpack\\.)[a-z][a-z0-9]*(?:\\.[a-z][a-z0-9-]*)+$" }
      ]
    },
    "properties": {
      "org.judgmentpack.annotations": { "$ref": "#/$defs/annotations" }
    },
    "additionalProperties": true
  }
}
```

The maxima are the `base` ceilings. A reader supporting `extended` validates with the extended
ceilings, as Core §4.1 requires of every row (§7).

### 2. Value sets

#### 2.1 Declaration (V1)

A pack MAY declare the root member `valueSets`: an array of 1 to 64 value-set objects (the base
ceiling, §7). An empty array is refused (`JPS-STRUCTURE-COLLECTION-ARITY`), on the reasoning of
§1.5. Two set objects equal under JSON Schema's equality are refused by the schema
(`JPS-STRUCTURE-UNIQUE-ITEMS`), as two equal objects are in Core's other collections.

Sets are declared at the root because references resolve within one document (Core §5), and
because a set can serve rules, exceptions and the pack's applicability alike. The root already
holds every other shared collection.

`valueSets` is a new Core member, not an extension.

- An optional extension cannot carry it. An optional extension MUST NOT change Core semantics, and
  a consumer may ignore one (Core §9). A consumer that ignored the sets could not evaluate a
  condition that references one.
- A required specification-defined extension would gain nothing. The reference is a member of a
  fact condition, which is a Core object, and a member not defined for a Core object MUST NOT
  appear (Core §4), so Core's schema changes either way. Once Core changes, an optional capability
  would let one conforming evaluator return a disposition and another return
  `unsupported-required-extension` for the same pack. The feature in question is a lookup, which
  leaves nothing to negotiate.

#### 2.2 The value-set object (V2)

A value-set object has these members and no others:

| Member | Required | Value |
| --- | ---: | --- |
| `id` | yes | a local identifier (Core §5), unique within `valueSets` |
| `description` | no | a non-empty string |
| `entries` | yes | an array of 1 to 512 entries (base ceiling, §7) |
| `extensions` | no | vendor extensions only. Annotations are refused here (§1.1). |

Two sets with one `id` make the document semantically non-conforming
(`JPS-SEMANTIC-DUPLICATE-ID`), as two outcomes with one id do. Identifiers are collection-local, as
Core's are: a set and an outcome may share an id, because the member that names a set
(`valueSet`) fixes the kind.

#### 2.3 Entries (V3)

An entry has these members and no others:

| Member | Required | Value |
| --- | ---: | --- |
| `value` | yes | any JSON value, as any item of an inline `in` operand may be |
| `description` | no | a non-empty string |
| `extensions` | no | vendor extensions and the annotations extension (§1.1) |

**Types.** A set declares no type and may mix types, as an inline `in` operand may. Each value is
compared with the selected fact value under Core §7.4. A set of `1`, `"1"`, `true`, `null`, `[1]`
and `{"a": 1}` is six distinct values.

Entry annotations use the same extension as every other position. One lookup rule,
`extensions["org.judgmentpack.annotations"]`, holds everywhere in the document.

#### 2.4 Distinct values (V4)

No two entries of one set may have equal values under Core §7.4's type-preserving equality. A set
that has two is semantically non-conforming (`JPS-SEMANTIC-DUPLICATE-SET-VALUE`, at the later
entry's `value`).

The reason: an entry's description and annotations belong to one value. With duplicates, a
matching fact would have two descriptions and two sets of labels. This is a rule for sets only.
An inline `in` operand keeps admitting repeated items, and `in` itself is unchanged.

Equality is exactly Core §7.4's:

- **Numbers** compare by mathematical value. `1`, `1.0`, `1e0` and `10E-1` are one value, and so
  are `10` and `1E1`, and `0` and `-0`. A validator decides this exactly from the number literals.
  One way is to reduce each to a sign, a digit string without leading or trailing zeros, and an
  integer exponent. No exponent needs expanding, and a validator SHOULD NOT expand one (see
  Security and privacy). A validator MUST NOT convert through binary floating point, which
  equates `9007199254740993` with `9007199254740992` and would refuse a conforming set.
- **Strings** compare by value, which for Core `0.3.0` is the sequence of code points. Core §13
  lists normalization semantics as open. This rule follows Core §7.4 wherever that question lands, so
  that a set's distinctness never disagrees with how `in` compares.
- **Booleans and null** compare by value.
- **Arrays** compare item by item, in order: `[1, 2]` and `[2, 1]` are distinct.
- **Objects** compare by member name and value, regardless of member order.
- **No coercion.** `1` and `"1"` are distinct. So are `"1.0"` and `"1.00"`: they are strings,
  and Core §7.4 compares decimal strings as strings.

The schema cannot state this rule, because two entries may carry the same value with different
descriptions. It is therefore a semantic rule (Core §3.3), not `uniqueItems`.

#### 2.5 No nesting (V5)

A set references no other set, and an entry has no `valueSet` member
(`JPS-STRUCTURE-UNKNOWN-MEMBER`). An entry value that looks like a reference, such as
`{"valueSet": "tier-codes"}`, is a literal JSON object, compared as one.

There is no union, intersection or difference of sets. An author lists the entries.

#### 2.6 Unreferenced sets (V8)

A set that no condition references is admitted and inert. A pack-design tool SHOULD report it
with the advisory `JPS-VALUE-SET-UNREFERENCED`. An advisory never changes document conformance.

Refusing an unreferenced set would make deleting the last reference to a set a breaking edit, and
would prevent an author from declaring a set before the rule that uses it.

#### 2.7 Schema fragment

Added to `$defs`:

```json
{
  "valueSet": {
    "type": "object",
    "additionalProperties": false,
    "required": ["id", "entries"],
    "properties": {
      "id": { "$ref": "#/$defs/localId" },
      "description": { "$ref": "#/$defs/nonEmptyString" },
      "entries": {
        "type": "array",
        "minItems": 1,
        "maxItems": 512,
        "items": { "$ref": "#/$defs/valueSetEntry" }
      },
      "extensions": { "$ref": "#/$defs/extensions" }
    }
  },
  "valueSetEntry": {
    "type": "object",
    "additionalProperties": false,
    "required": ["value"],
    "properties": {
      "value": true,
      "description": { "$ref": "#/$defs/nonEmptyString" },
      "extensions": { "$ref": "#/$defs/annotatedExtensions" }
    }
  }
}
```

Added to the root's `properties`:

```json
{
  "valueSets": {
    "type": "array",
    "minItems": 1,
    "maxItems": 64,
    "uniqueItems": true,
    "items": { "$ref": "#/$defs/valueSet" }
  }
}
```

### 3. References

#### 3.1 Form (V6)

A fact condition MAY carry `valueSet`, a local identifier naming a declared set, in place of
`value`. These rules apply:

- A fact condition carries exactly one of `value` and `valueSet`.
  - Carrying both is a structural refusal (`JPS-STRUCTURE-VALUE-SET-REFERENCE`).
  - Carrying neither is the existing refusal of a fact condition without its operand
    (`JPS-STRUCTURE-REQUIRED-MEMBER` at `value`).
- `valueSet` is admitted only with operator `in`. With any other operator it is a structural refusal
  (`JPS-STRUCTURE-VALUE-SET-REFERENCE`). For a single value, a one-entry set serves. For the inverse
  test, `not` serves.
- The rules for `value` are unchanged. With `in`, `value` is still a non-empty array of literals
  (Core §7.4). An object in `value`, such as `"value": {"valueSet": "x"}`, is still refused
  (`JPS-STRUCTURE-IN-OPERAND`); it is not a reference.

The reference is a sibling member, not a form of `value`. This keeps `value` literal for every
operator, and it matches how Core names other declared objects by member: `evidenceRequirement`,
`outcome` and `targetRule`.

#### 3.2 Resolution (V7)

Every `valueSet` member names the `id` of exactly one declared set. This applies in every
condition position: the root `applicability`, each rule's `when`, each exception's `when`, and
every condition nested in them under `all`, `any` and `not`.

A reference that names no declared set makes the document semantically non-conforming
(`JPS-SEMANTIC-UNRESOLVED-VALUE-SET`, at the `valueSet` member). So does a reference in a pack with
no `valueSets` member. Since set ids are unique (§2.2), a resolved reference resolves exactly once,
as Core §3.3 requires of every local reference.

An evaluator given such a pack reports `pack-not-conformant` (Core §8.4). It is the first class in
that order, so it is reported whatever else is wrong with the other inputs.

#### 3.3 Schema fragment

The fact branch of the condition union becomes:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["op", "path", "operator"],
  "properties": {
    "op": { "const": "fact" },
    "path": { "type": "string", "pattern": "^(?:/(?:[^~/]|~0|~1)*)*$" },
    "operator": {
      "enum": ["equals", "not-equals", "greater-than", "greater-than-or-equal",
               "less-than", "less-than-or-equal", "in"]
    },
    "value": true,
    "valueSet": { "$ref": "#/$defs/localId" }
  },
  "oneOf": [
    { "required": ["value"] },
    { "required": ["valueSet"] }
  ],
  "allOf": [
    "... the two existing if/then members, for ordered operators and for in, unchanged ...",
    {
      "if": { "required": ["valueSet"] },
      "then": { "properties": { "operator": { "const": "in" } } }
    }
  ]
}
```

The string in `allOf` stands for the two existing members, which are kept as they are; it is not
schema text. The existing `in` member constrains `value` only when `value` is present, so a
reference satisfies it.

### 4. The evaluation form and inertness (E1)

#### 4.1 Definition

The *evaluation form* `EF(P)` of a semantically conforming pack `P` is the JSON value produced by
these three steps:

1. **Expand references.** Each fact condition, in each condition position of §3.2, that carries
   `valueSet` loses that member and gains a `value` member. The new `value` is an array holding the
   `value` of each entry of the named set, in entry order.
2. **Remove the sets.** The root member `valueSets` is removed. Entry descriptions and entry
   annotations go with it.
3. **Remove annotations.** The member `org.judgmentpack.annotations` is removed from the root's
   `extensions` member, from each outcome's and from each rule's. If an `extensions` object is left
   with no members, the `extensions` member itself is removed.

Nothing else changes. The steps act on positions, not on content. A literal inside a `value`
operand, an entry value and a vendor extension's value are never inspected. A literal that looks
like a reference, or like an annotations object, stays exactly as it is.

`EF(P)` is itself a semantically conforming pack of the same `specVersion`, with the same
`profile`. Each step only removes optional members, or turns a resolved reference into an `in`
operand. That operand is a non-empty array, because a set has at least one entry. A pack that uses
neither feature is its own evaluation form.

#### 4.2 The requirement

For a semantically conforming pack `P`, given the same facts document, evidence-availability
document and supported-extension set, an implementation claiming evaluator conformance MUST
produce for `P` exactly what it produces for `EF(P)`. That is either the byte-identical
canonicalized disposition (Core §8.3), or an evaluation error of the same class (Core §8.4).

These follow from that requirement together with Core §8.3:

- **Annotations are inert.** Adding, changing or removing annotations never changes a disposition
  or an error class. A label that spells an outcome id, a reason or a route target changes
  nothing.
- **Substitution.** A reference behaves exactly as its inline array: the same Core §7.4 equality, the
  same `unknown` for an absent path, and the same reading under `not`. The order of sets, and of
  entries within a set, changes nothing, because `in` tests membership.
- **Nothing new reaches the disposition.** There is no new reason, error class or disposition
  member. Core §8.3 admits "these members and no others", so no annotation, set id or entry description
  ever appears in a disposition. A trace outside the disposition MAY name the set a condition
  referenced and the entry a fact matched.
- **The numeric seam is inherited, not widened.** Core §7.4 says `in` "A match produces `true`; no
  match produces `false`" (line 618), and leaves equality with an unrepresentable number to Core §13.
  A reference compares exactly as its inline array does, so it adds no input to that seam and
  takes none out.

#### 4.3 Limits and work

`P` and `EF(P)` are different bytes. If a documented document limit (bytes, nesting depth or
string size; Core §10) admits one of them and refuses the other, the pair is outside the portable
claim, as Core §10 already places every input above a limit outside it. Annotations can push a pack
over a byte limit. The class reported for an oversize pack is whatever Core gives any oversize
pack (see Compatibility). The staged rows stay well inside any plausible limit.

Collection-size and evaluation-work limits apply to the work `EF(P)` requires. A reference costs
what its inline array costs. Under [RFC 0008](0008-bounded-collection-quantifiers.md)'s work
accounting, if adopted, an authored `in` operand reached through a reference is charged as the
expanded array.

The evaluation form defines an equivalence, not a processing step. An evaluator need not build
`EF(P)`. Resolving a reference to the declared array without copying it satisfies §4.2.

#### 4.4 Document analysis

The recommended overlap check (Core §3.3.1) reads a reference as its set's values. The true set of
an `in` condition with a reference is the set of its entries' values, as line 166 says of an inline
operand. A validator MAY run that check on `EF(P)`.

### 5. Identity, digest and order (I1)

- **Bytes.** Annotations, value sets and references are part of the pack's bytes. They are
  therefore part of every digest and every exact-identity rule that covers the pack: a manifest
  digest ([RFC 0001](0001-pack-manifest.md)), a workflow's digest of a pack it names, a runtime's
  lock of a reviewed set. Each of those names exact bytes. Core defines no canonical form or
  digest of a pack (Core §13, line 1071), and this record defines none. Core already reads
  `profile` this way: it "is part of the document's bytes, so it is part of its digest and every
  exact-identity rule" (Core §4.1, line 363).
- **A changed label is changed content.** Core §11's "Changed content SHOULD receive a new
  version" (line 1001) applies to a pack whose only change is an annotation.
- **No digest of the evaluation form as identity.** A digest of `EF(P)` MAY be published, as
  evidence that two packs evaluate alike. It MUST NOT be presented as the pack's digest or
  identity. Two packs with one evaluation-form digest are evaluation-equivalent within §4.3, and are
  not the same pack.
- **Order.**
  - Member order in an annotations object carries no meaning, as in any JSON object.
  - The order of strings in a list is part of the bytes and carries no evaluation meaning.
    Consumers SHOULD display it in document order.
  - The order of sets in `valueSets`, and of entries in a set, carries no evaluation meaning.
    Core §4 (line 332) says that collection order is preserved for authoring and display, and that
    rule extends to these collections. Entry order fixes the order of the expanded array in
    `EF(P)`, which only makes `EF(P)` deterministic.
- **No sorted order is required.** Inline `in` operands have no sort rule. Mixed-type values have
  no total order Core defines. An author's order carries meaning to readers, for example tiers
  listed in rank order. A canonical form for packs, if one is later defined, would order object
  members (RFC 8785) and keep array order, here as for every other array.

### 6. Untrusted display data (D1)

Annotation keys and strings, and entry descriptions, are display data from the pack's author.
They are as untrusted as every other pack string (Core §10). A consumer that displays one:

- MUST render it as text. It MUST escape the string for the output context, and MUST NOT let the
  context interpret it as markup, a template, a spreadsheet formula or a terminal control sequence;
- MUST NOT resolve, fetch or otherwise dereference it. A string that looks like a URI, a path or an
  address is not a locator;
- MUST NOT treat it as naming anything in the pack. An annotation value equal to an outcome id
  names no outcome (Core §5: meaning is not inferred from spelling);
- MUST NOT present it as a review, an approval, a verified property, or a classification that
  anything other than the author's statement established (Core §3.5). Reviews belong in
  `metadata.reviews`;
- SHOULD isolate bidirectional text, so that a value's direction does not reorder the text around
  it. In HTML, for example, `<bdi>` or `dir="auto"` does this; and
- SHOULD show annotations as the author's labels, visually distinct from Core members.

The fixture `valid-annotations-display-hostile` (see [Conformance](#conformance)) carries markup, a
template, a formula prefix, a URI, bidirectional override characters and an outcome id as values.
Validators accept it, and evaluation ignores it. How it is rendered is a consumer's test, not a
Core class.

### 7. Ceilings

Six rows would be added to Core §4.1's table. Characters are Unicode code points, as JSON Schema
counts them.

| Format and resource | `base` | `extended` |
| --- | ---: | ---: |
| Core annotation keys per annotations object | 16 | 32 |
| Core annotation strings per list | 16 | 32 |
| Core annotation key characters | 64 | 128 |
| Core annotation string characters | 256 | 512 |
| Core value sets | 64 | 128 |
| Core entries per value set | 512 | 1024 |

The published schema carries the `base` maxima, as for every row.

There is no ceiling on the total size of an annotations object. One is derived instead: at
`base`, an object holds at most 16 × (64 + 16 × 256) = 66,560 characters, and at `extended`
528,384. JSON Schema cannot state a sum, so a separate total would be a check outside the schema
for no gain. The number of annotated objects is bounded by the document byte limit only, because
Core defines no outcome or rule maximum (Core §4.1, line 376). That sentence stays true: these rows are
not outcome, rule or reference maxima.

The new maximum on entries does not limit inline operands. Core sets no maximum on an inline `in`
array, and an expanded reference never has more than 512 (or 1024) items.

### 8. Use by consumers (informative, except D2)

This section is informative except for D2.

**What consumers may do.**

- **Group and filter.** Group rules by `category`. Show the outcomes whose `tier` is `standard`.
  List the rules with a given `review-cycle`.
- **Match a value in either spelling.** A filter on key `k` and value `v` matches an object whose
  `k` is the string `v` or a list containing `v`. String comparison is on code points (§1.3).
- **Show sets.** Show a reference with its set's id, its description and its entries in document
  order. Show entry descriptions and annotations beside the entry. When a trace names the entry a
  fact matched, show that entry's annotations. That stays outside the disposition (§4.2).
- **Inline for reading.** A view of one rule MAY show a reference expanded, provided it says that
  the list comes from the named set.
- **Document a vocabulary.** Core defines no keys. A project MAY document its own key vocabulary.
  Keys carry meaning only by such a convention.

**D2, filtered views (normative).** A consumer that presents a filtered view of a pack MUST state,
in the view, that it is filtered, and by which keys and values. A filtered view is one that omits
outcomes, rules or entries because of their annotations. The view SHOULD state how many items it
omits.

A filtered view is not a pack. It MUST NOT be offered for evaluation, signing or hashing as the
pack. A disposition is always the whole pack's, and omitted items take part in every evaluation.

A filtered view is not redaction either. The omitted items, and their annotations, remain in the
pack's bytes (see Security and privacy).

D1 and D2 bind any consumer that displays or filters annotations, as Core §10's prohibitions bind
every implementation. No Core conformance class tests display.

### 9. Where each part lands

| Place | Change |
| --- | --- |
| Core §2.1 | none; duplicate member names are already refused |
| Core §3.3 | three bullets: value-set ids are unique; every `valueSet` resolves; no set has two equal entry values |
| Core §3.3.1 | a reference reads as its set's values (§4.4) |
| Core §4 | a `valueSets` row in the root table; the collection-order sentence covers sets and entries |
| Core §4.1 | the six rows of §7 |
| Core §5 | value-set references join the list of references that resolve within one document (line 451) |
| Core §6 (new subsection) | the value set and its entries (§2) |
| Core §7.4 | the `valueSet` member (§3.1) |
| Core §8 (new paragraph) | the evaluation form and §4.2's requirement |
| Core §9 | a paragraph on specification-defined extensions (their value is governed by their definition, which qualifies "Values may be any JSON value", line 950); then annotations: A1–A6, D2 |
| Core §10 | D1 |
| Core §11 | compatibility from `0.3.0` (see Compatibility) |
| Core §13 | unchanged; content identity stays open |
| Schema | §§1.7, 2.7 and 3.3 |
| Document corpus | the staged document cases, which land when the next `specVersion` opens |
| Evaluation corpus | the staged rows, which land the same way |

The two features can be accepted separately, with one exception. Annotations (§1) stand alone.
Value sets (§§2–3) stand alone, except that entry annotations (§2.3) depend on §1.

## Examples

Each example shows only the members it adds. The other required members (`specVersion`, `id`,
`version`, `title`, `decision`) are as in any Core pack. Their `specVersion` would be the
selector of the version that adopts this record, which is not assigned. Every example is valid under this
record's rules. Each was checked that way while drafting, as described under Evidence.

### Example 1: annotations on the pack, an outcome and two rules

```json
{
  "extensions": {
    "org.judgmentpack.annotations": {
      "category": "intake",
      "review-cycle": "quarterly"
    }
  },
  "outcomes": [
    {
      "id": "accept",
      "label": "Accept",
      "extensions": {
        "org.judgmentpack.annotations": { "tier": "standard" }
      }
    },
    { "id": "refer", "label": "Refer for review" }
  ],
  "rules": [
    {
      "id": "complete-request",
      "description": "A complete request is accepted.",
      "when": { "op": "fact", "path": "/request/complete", "operator": "equals", "value": true },
      "outcome": "accept",
      "onUnknown": "escalate",
      "extensions": {
        "org.judgmentpack.annotations": {
          "category": ["intake", "completeness"],
          "review-cycle": "quarterly"
        },
        "com.example.authoring": { "draftedWith": "editor" }
      }
    },
    {
      "id": "incomplete-request",
      "description": "An incomplete request is referred.",
      "when": { "op": "fact", "path": "/request/complete", "operator": "equals", "value": false },
      "outcome": "refer",
      "onUnknown": "escalate",
      "extensions": {
        "org.judgmentpack.annotations": { "category": "completeness" }
      }
    }
  ]
}
```

The pack's annotations do not pass to its rules (§1.1). A filter on `category` = `completeness`
matches both rules: the first in its list spelling, the second as a plain string.

The evaluation form removes the four annotations objects. The root's and the outcome's
`extensions` members are then empty, so they are removed too. So is the second rule's. The first
rule keeps `extensions` with `com.example.authoring` alone.

### Example 2: a value set with annotated entries, and a rule that references it

```json
{
  "valueSets": [
    {
      "id": "priority-tiers",
      "description": "Tiers handled on the priority track.",
      "entries": [
        {
          "value": "tier-1",
          "description": "The first tier.",
          "extensions": {
            "org.judgmentpack.annotations": { "review-cycle": "monthly" }
          }
        },
        {
          "value": "tier-2",
          "extensions": {
            "org.judgmentpack.annotations": {
              "review-cycle": "quarterly",
              "category": ["legacy", "priority"]
            }
          }
        },
        { "value": "tier-3" }
      ]
    }
  ],
  "rules": [
    {
      "id": "priority-track",
      "description": "A request in a priority tier is accepted.",
      "when": { "op": "fact", "path": "/request/tier", "operator": "in", "valueSet": "priority-tiers" },
      "outcome": "accept",
      "onUnknown": "escalate"
    }
  ]
}
```

The outcomes are as in Example 1.

### Example 3: the equivalent inline form

```json
{
  "rules": [
    {
      "id": "priority-track",
      "description": "A request in a priority tier is accepted.",
      "when": { "op": "fact", "path": "/request/tier", "operator": "in", "value": ["tier-1", "tier-2", "tier-3"] },
      "outcome": "accept",
      "onUnknown": "escalate"
    }
  ]
}
```

The evaluation form of Example 2 is Example 3's pack. `valueSets` is removed, together with its
entry descriptions and annotations, and the reference is replaced by the entries' values in entry
order. By §4.2, every conforming evaluator gives the two packs the same result for every input.
Their bytes, and so their digests, differ (§5).

Example 3 is also a valid Core `0.3.0` pack, given `"specVersion": "0.3.0"`. Examples 1 and 2 are
not. The `0.3.0` schema refuses the reserved key, the root member `valueSets` and the `valueSet`
member.

## Alternatives

**(a) A new `annotations` member on the pack, each outcome and each rule.** Not chosen; the
decision on the issue chose the reserved extension.

- *For (a):* a shorter path and one level less nesting. Annotations would be visible to every
  schema-driven editor as a first-class member.
- *Against (a), and for the extension:*
  - Core §9 already reserves `org.judgmentpack.` for specification-defined extensions. This is the
    designed slot, and using it leaves the shapes of Core's objects unchanged.
  - Tools that handle `extensions` generically already do the right thing with annotations: they
    preserve them on round-trip and otherwise ignore them (Core §9).
  - The inertness obligation already exists for optional extensions (Core §9, line 952), so §4.2 makes
    an existing promise testable rather than adding a new kind of member.
  - A consumer that ignores extensions loses nothing it needs.
- *Cost of the extension:* this is the first time Core constrains the value of an extension name.
  Core §9 would gain the paragraph listed in this record's §9.

**Other alternatives considered:**

- **No change.** Labels stay in vendor extensions. Every tool picks its own name and shape, no two
  tools share a view, consumers must accept any JSON value, and no row checks inertness.
- **A sidecar document beside the pack.** Labels could change without a new pack version. But
  Core has no imports and no pack identity (Core §5, line 450; Core §13, lines 1071–1072). The labels would
  travel apart from the pack, bound to it by nothing portable. Labels that are operational rather
  than authored may still live outside the pack; this record does not cover them.
- **Value sets as an optional extension.** Impossible (§2.1): a consumer may ignore an optional
  extension (Core §9), and one that ignored the sets could not evaluate a reference.
- **Value sets as a required specification-defined extension.** Rejected for the reasons in §2.1.
- **External set documents named by digest.** Rejected: Core has no imports (Core §13). This waits for
  that work.
- **A reference inside `value`, such as `"value": {"valueSet": "x"}`.** Rejected (§3.1). It
  would give one object shape a special meaning inside a literal.
- **References with `equals` or `not-equals`.** Rejected. A one-entry set with `in` expresses
  `equals`, and `not` expresses the inverse. One operator keeps the rule small.
- **An entry `annotations` member instead of entry `extensions`.** Rejected. One lookup rule holds
  everywhere (§2.3).
- **A required sorted order for lists, sets or entries.** Rejected (§5).
- **Refusing one-element lists.** Rejected. A multi-valued key would change type when it shrinks
  to one value (§1.3).
- **Admitting empty forms.** Rejected (§1.5). This also covers an empty `valueSets` array, which
  Core's older optional collections (`evidenceRequirements`, `sources`, `exceptions`) admit. A new
  member can have one spelling for "none" from the start. The cost is a difference from those
  collections, which a writer that emits `[]` for every empty collection must handle.
- **Admitting duplicate entry values, as inline operands do.** Rejected (§2.4). Entry
  descriptions and annotations must attach to one value.
- **Set composition: union, or one set referencing another.** Rejected (§2.5). Composition brings
  cycles, an evaluation order and work that a flat list does not. A later RFC may add it, with
  evidence.
- **Typed sets.** Rejected. Core's `in` is untyped. A type declaration would be a constraint with
  no evaluation meaning, and the evaluation form must equal the inline form.
- **Refusing unreferenced sets.** Rejected (§2.6).
- **Non-string annotation values.** Rejected.
  - Numbers would bring the numeric questions of Core §7.4 and Core §13 into a display field.
  - Booleans become flags that read like Core semantics.
  - Objects reopen arbitrary JSON.
  - Vendor extensions remain available for structured data.
- **Trimming whitespace or normalizing case and Unicode.** Rejected. Equality is on code points
  (§1.3), and a validator that normalized would let two tools disagree about duplicates.
- **Refusing bidirectional formatting characters.** Rejected (§1.4). Core admits them in every
  other string, and D1 addresses their display.
- **A registry of keys.** Rejected for now. Core infers no meaning from spelling (Core §5), and a
  registry is governance work that no evidence yet asks for. A project can document its own
  vocabulary (§8).
- **Annotations on the value-set object, exceptions, evidence requirements or sources.** Not
  included. The issue names packs, outcomes, rules and entries. Widening later is compatible, and
  narrowing is not (Unresolved question 2).

## Drawbacks

- **Length.** The extension name is long and adds a level of nesting to a common feature.
- **Relabeling needs a new pack version.** Changing a label changes the pack's bytes (§5).
- **Indirection.** A reader of one rule has to look elsewhere for the list. Views can expand a
  reference for reading (§8).
- **Unchecked constraints.** This is the first constrained extension value. Tools that treat
  extension values as opaque, and are not structural validators, may pass non-conforming
  annotations along.
- **Two features in one record.** The slower one could hold back the other. They are severable
  (§9).
- **Ceilings without measurement** (Unresolved question 1). These are also Core's first pack
  ceilings beyond escalation routes.
- **A new kind of semantic rule.** Exact numeric distinctness (§2.4) asks validators for exact
  decimal comparison of literals, which some document-only validators do not do today.

## Compatibility

**Version.** These changes belong to the next Core `specVersion` after `0.3.0`. As Core §11
requires, compatibility is explicit:

- **Reader and writer.** A `0.3.0` reader refuses a pack declaring the next selector, by the exact
  selector (Core §4), and it does not acquire support by ignoring or replacing the selector. The `0.3.0`
  schema also refuses each new shape: the reserved key, the root `valueSets` and the `valueSet`
  member. A writer targeting `0.3.0` cannot emit them.
- **Semantic.** For a pack that uses neither feature, `EF(P)` is `P`, so this record changes no
  result for it.
- **Migrating up from `0.3.0`.** No `0.3.0` shape is refused by these rules. As far as this record
  goes, changing only the selector is enough, and evaluation is unchanged. The next version's other
  changes are their own.
  - Labels kept in a vendor extension MAY be moved to the reserved name by hand, once they meet
    §§1.3–1.5. There is no automatic coercion: a vendor value outside those rules must be edited,
    not truncated, joined or dropped by a tool.
  - An inline list MAY be replaced by a reference.
  - Each such edit changes the bytes, so the pack SHOULD receive a new `version` (Core §11).
- **Migrating down to `0.3.0`.** `EF(P)` with the selector changed is evaluation-equivalent within
  §4.3, but it loses the annotations and the entry descriptions. A vendor extension can carry
  labels under `0.3.0`.
- **Profiles.** No new profile and no new capability. Both features are in Core, the schema carries
  their `base` maxima, and the six ceilings join Core §4.1's table. Reader capability records are
  unchanged. A reader that lists `extended` commits to the extended values of the new rows, as to
  every row.
- **Evaluator claims.** A claim attaches to the next `specVersion` and its corpus (Core §3.4.1). The
  staged rows land there and nowhere earlier.
- **Released artifacts.** The released `0.3.0` schema, Core text and corpora are unchanged.

**Other records.**

- [RFC 0016](0016-outcome-values.md) needs the same relaxation of the reserved-name refusal. Core §9
  should gain one paragraph on specification-defined extensions, whichever record lands first, and
  each record then adds its own name.
- [RFC 0008](0008-bounded-collection-quantifiers.md)'s work accounting would apply to the
  evaluation form (§4.3).
- [RFC 0027](0027-pack-design-advisories.md)'s advisories would read a reference as its set
  (§4.4). The unreferenced-set advisory may belong in its report contract (Unresolved question 3).
- [RFC 0001](0001-pack-manifest.md)'s manifest digest is over exact bytes, so it covers
  annotations and sets (§5).

**Questions this record leaves to Core.** A pack that annotations push over a documented byte
limit is refused like any oversize pack. Core §8.4 calls a pack failing the carrier layer
`pack-not-conformant` (line 913). It calls a document limit reached "while admitting an input"
`malformed-input` (line 922, and Core §10, line 976). When both apply, the order at line 930 selects
`pack-not-conformant`. Whether the second applies to the pack, which is "an input" to an
evaluation, is Core's question. This record does not change it.

## Security and privacy

- **Display.** Annotations and entry descriptions are untrusted display data (D1). The refused
  characters (§1.4) remove line breaks and terminal control sequences. Escaping, isolation of
  bidirectional text and refusal to dereference are the consumer's duties.
- **Confusion.** A label such as `"status": "approved"` or `"priority": "first"` is the author's
  text, not a Core fact. Core has no rule priority (Core §6.5), and §4.2 makes a label unable to create
  one. D1 forbids presenting a label as a review or an approval.
- **No execution.** Core §10's "MUST NOT execute code found in strings or extensions" covers both
  features.
- **Resources.**
  - The ceilings (§7) bound each object.
  - **Expansion.** A 512-entry set referenced by many conditions expands to a large `EF(P)`. An
    evaluator SHOULD resolve a reference to the shared array, not copy it (§4.3). Work limits
    charge each comparison either way.
  - **Duplicate checking.** Comparing pairs is quadratic in a set's size. A validator SHOULD
    instead compute a normalized key per value (exact decimal numbers, objects with members
    sorted) and look up duplicates by hash.
  - **Number literals.** Normalizing a literal needs no expansion of its exponent (§2.4). Literal length
    is bounded by the implementation's documented limits (Core §10).
  - **Entry values.** These are arbitrary JSON, bounded by document nesting and size limits like
    any operand.
- **Disclosure.** Annotations travel with the pack and are part of its bytes. Authors should put
  neither secrets nor personal data in them. A filtered view hides nothing from anyone holding the
  pack (D2).
- **Integrity.** Because annotations are in the bytes, any signature over the pack covers them. A
  label cannot be swapped without changing the pack's identity.

## Conformance

### Evidence bar

This record cannot move beyond Draft until all of the following hold.

1. The adversarial review that RFC 0009 requires is recorded, with a written disposition for
   each finding.
2. The vectors below exist as files and are reviewed:
   - the evaluation rows in `conformance/evaluation/staged/`; and
   - the document cases in a staging location that the conformance README names, outside every
     released corpus.

   They are held to the repository's checks, including the static check below.
3. Two independently authored implementations pass every staged vector: the document rules (A1–A6,
   V1–V8) and the evaluation requirement (§4.2).
4. A draft schema for the next selector carries the fragments, under the repository's schema
   tests.
5. Evidence of use exists:
   - at least one published example pack uses both features. The expense example's shared list is
     a candidate.
   - at least one consumer view implements D1 and D2, with its own tests.
6. The ceilings are either measured from packs that use the shapes, or accepted as reasoned by the
   disposition of Unresolved question 1.
7. Core text is drafted for each row of this record's §9 table, and the Core §9 paragraph is coordinated with RFC
   0016.

### Staged document cases

Codes are provisional test metadata, as the [conformance README](../conformance/README.md) says
of every code. "New" marks a code this record proposes. Pointers are given where the case fixes
them.

| Case | Purpose | Expected |
| --- | --- | --- |
| `valid-annotations-positions` | Example 1: root, outcome, two rules, a vendor key beside annotations | valid |
| `valid-annotations-value-set-entry` | Example 2: annotations on entries | valid |
| `valid-annotations-at-ceilings` | 16 keys of 64 characters, each a list of 16 strings of 256 characters | valid |
| `valid-annotations-non-bmp` | a 256-character string of characters outside the BMP: code points are counted, not code units or bytes | valid |
| `valid-annotations-one-element-list` | `["intake"]` on one rule, `"intake"` on another | valid |
| `valid-annotations-display-hostile` | markup, a template, a formula prefix, a URI, bidirectional overrides, an outcome id as values | valid |
| `structural-annotations-in-decision` | and one case each for `-evidence-requirement`, `-source`, `-exception`, `-escalation`, `-metadata` and `-value-set` (the set object) | `JPS-STRUCTURE-EXTENSION-NAME` at `…/extensions/org.judgmentpack.annotations` |
| `structural-annotations-required` | the name in `metadata.requiredExtensions` | `JPS-STRUCTURE-EXTENSION-NAME` at `/metadata/requiredExtensions/0` |
| `structural-reserved-name-in-annotated-position` | `org.judgmentpack.future` in a rule's `extensions` | `JPS-STRUCTURE-EXTENSION-NAME` |
| `structural-annotations-not-object` | the extension's value is a string | `JPS-STRUCTURE-TYPE` |
| `structural-annotations-empty-object` | `{}` | `JPS-STRUCTURE-COLLECTION-ARITY` |
| `structural-annotations-empty-list` | `"category": []` | `JPS-STRUCTURE-COLLECTION-ARITY` |
| `structural-annotations-empty-string` | `"category": ""` | `JPS-STRUCTURE-MIN-LENGTH` |
| `structural-annotations-key-grammar-*` | one case each: `Tier`, `tier_1`, `-tier`, `tier-`, `ti--er`, `1tier`, the empty key | `JPS-STRUCTURE-ANNOTATION-KEY` (new) |
| `structural-annotations-key-too-long` | a 65-character key | `JPS-STRUCTURE-ANNOTATION-KEY` (new) |
| `structural-annotations-too-many-keys` | 17 keys | `JPS-STRUCTURE-MAXITEMS` |
| `structural-annotations-too-many-strings` | a list of 17 | `JPS-STRUCTURE-MAXITEMS` |
| `structural-annotations-string-too-long` | 257 characters | `JPS-STRUCTURE-MAX-LENGTH` (new) |
| `structural-annotations-duplicate-string` | `["intake", "intake"]` | `JPS-STRUCTURE-UNIQUE-ITEMS` |
| `structural-annotations-value-*` | one case each: a number, a Boolean, null, an object, a nested list | `JPS-STRUCTURE-ANNOTATION-VALUE` (new) |
| `structural-annotations-control-*` | one case each, escaped in the JSON: NUL, TAB, LF, ESC, DEL, U+0085, U+009B, U+2028, U+2029 | `JPS-STRUCTURE-ANNOTATION-TEXT` (new) |
| `carrier-annotations-duplicate-key` | one key twice in one annotations object | `JPS-CARRIER-DUPLICATE-MEMBER` |
| `structural-value-sets-empty` | `"valueSets": []` | `JPS-STRUCTURE-COLLECTION-ARITY` |
| `structural-value-set-entries-empty` | `"entries": []` | `JPS-STRUCTURE-COLLECTION-ARITY` |
| `structural-value-set-unknown-member` | a set with `type` | `JPS-STRUCTURE-UNKNOWN-MEMBER` |
| `structural-value-set-entry-unknown-member` | an entry with `label` | `JPS-STRUCTURE-UNKNOWN-MEMBER` |
| `structural-value-set-entry-reference` | an entry with `valueSet` (nesting) | `JPS-STRUCTURE-UNKNOWN-MEMBER` |
| `structural-value-set-missing-*` | one case each: no `id`, no `entries`, an entry without `value` | `JPS-STRUCTURE-REQUIRED-MEMBER` |
| `structural-value-set-bad-id` | `Priority_Tiers` | `JPS-STRUCTURE-LOCAL-ID` |
| `structural-value-sets-identical` | two byte-identical set objects | `JPS-STRUCTURE-UNIQUE-ITEMS` at `/valueSets` |
| `structural-value-sets-too-many` | 65 sets | `JPS-STRUCTURE-MAXITEMS` |
| `structural-value-set-too-many-entries` | 513 entries | `JPS-STRUCTURE-MAXITEMS` |
| `structural-value-set-reference-and-value` | both members | `JPS-STRUCTURE-VALUE-SET-REFERENCE` (new) |
| `structural-fact-without-operand` | neither member | `JPS-STRUCTURE-REQUIRED-MEMBER` at `…/value` |
| `structural-value-set-reference-operator-*` | one case each: `equals`, `not-equals`, `greater-than` | `JPS-STRUCTURE-VALUE-SET-REFERENCE` (new) |
| `structural-value-set-reference-bad-id` | `"valueSet": "Tiers"` | `JPS-STRUCTURE-LOCAL-ID` |
| `structural-value-set-reference-in-value` | `"value": {"valueSet": "priority-tiers"}` with `in` | `JPS-STRUCTURE-IN-OPERAND` |
| `semantic-unresolved-value-set-*` | one case each: in a rule, in an exception, in `applicability`, nested under `all` and `not`, and with no `valueSets` at all | `JPS-SEMANTIC-UNRESOLVED-VALUE-SET` (new) at the `valueSet` member |
| `semantic-duplicate-value-set-id` | two sets, one id | `JPS-SEMANTIC-DUPLICATE-ID` at `/valueSets/1/id` |
| `semantic-duplicate-set-value-*` | one case each: a repeated string; `1` and `1.0`; `10` and `1E1`; `0` and `-0`; objects differing only in member order; equal nested arrays; equal values with different descriptions | `JPS-SEMANTIC-DUPLICATE-SET-VALUE` (new) at the later entry's `value` |
| `valid-value-set-mixed-types` | `1`, `"1"`, `true`, `null`, `[1]`, `{"a": 1}` | valid |
| `valid-value-set-large-integers` | `9007199254740993` and `9007199254740992` | valid (distinct) |
| `valid-value-set-array-order` | `[1, 2]` and `[2, 1]` | valid (distinct) |
| `valid-value-set-decimal-strings` | `"1.0"` and `"1.00"` | valid (distinct strings) |
| `valid-value-set-literal-object-entry` | an entry value `{"valueSet": "priority-tiers"}` | valid (a literal) |
| `valid-value-set-shared` | one set referenced by two rules, once under `not` | valid |
| `valid-value-set-id-shared-with-outcome` | a set and an outcome with one id | valid (collection-local) |
| `advisory-value-set-unreferenced` | a declared set that nothing references | valid, with advisory `JPS-VALUE-SET-UNREFERENCED` (new) |
| `profile-<resource>-*` | for each of the six rows of §7: `base` + 1 under `base`; `base` + 1 under `extended`; `extended` + 1 under `extended` | refused; valid; refused |

### Staged evaluation rows

Each row carries a pack, facts, evidence availability and a supported-extension set, as a released
row does. "Paired" rows share inputs and an expected result.

| Row | Purpose | Expected |
| --- | --- | --- |
| `annotations-inert-<result>` | for each of `outcome`, `not-applicable`, `unknown` (unresolved), `conflict` and `no-match`: a baseline pack, the same pack annotated, and the same pack with changed annotations | paired: one disposition per result |
| `annotations-inert-mimic` | labels spelling outcome ids, reason names and route targets, and `"priority": "first"` on one of two conflicting rules | the baseline's `unresolved` with `conflict` |
| `annotations-inert-error-class` | annotations beside an unsupported required vendor extension; and beside a malformed evidence document | the baseline's class: `unsupported-required-extension`; `malformed-input` |
| `extension-inert-vendor` | a vendor optional extension present and absent, which Core §9 states but no row checks | paired |
| `value-set-substitution-<case>` | for each of `match`, `no-match` and `unknown` (absent path): a reference and its inline form | paired |
| `value-set-type-preserving` | fact `"1"` against entry `1`; fact `true` against entry `"true"` | no match |
| `value-set-decimal-string` | fact `"1.0"` against entry `"1.00"` | no match |
| `value-set-numeric` | fact `1.0` against entry `1` | match |
| `value-set-composite` | a fact object whose member order differs from the entry's | match |
| `value-set-shared-exclusive` | the expense example's shape, with one set referenced by an `in` rule and under `not` in the other | one outcome, no conflict |
| `value-set-diverged-copies` | the same pack inline, with the two copies differing by one value, for a fact holding that value | `unresolved` with `conflict`: the hazard a shared set removes |
| `value-set-in-exception` | a reference in an exception's `when` | paired with inline |
| `value-set-in-applicability` | a reference in `applicability`, not matching | `not-applicable`, paired with inline |
| `value-set-under-not` | a reference under `not` | paired with inline |
| `value-set-unreferenced-inert` | a pack with an unreferenced set and without it | paired |
| `value-set-entry-annotations-inert` | entry annotations and descriptions present, absent, and changed | paired |
| `value-set-literal-object-entry` | a fact `{"valueSet": "priority-tiers"}` against an entry holding that literal | match |
| `value-set-literal-annotations-operand` | an inline `in` item `{"extensions": {"org.judgmentpack.annotations": {"tier": "x"}}}` against a fact holding exactly that object | match: the evaluation form acts on positions, not content |
| `value-set-unresolved-error` | an unresolved reference | `pack-not-conformant` |
| `value-set-unresolved-precedence` | an unresolved reference with a malformed evidence document | `pack-not-conformant` (Core §8.4 order) |

No row is staged for the Core §13 numeric seam. As Core §13 says, a row cannot state an expected
result until that question closes.

**Static check.** A repository test computes the evaluation form of each paired fixture. It
asserts that the form equals its partner's or its baseline's, and that paired rows expect the
same result. A pair that fails the check is a defect in the fixtures, caught before any
implementation runs them.

## Implementation

The rules divide into a schema, three semantic checks (duplicate set ids, resolution and distinct
values) and one evaluation pre-pass (resolving a reference to its array). Two plausible
independent implementations:

- the project's reference runtime, which already validates and evaluates packs; and
- a second reader authored separately, for example a validator in another language that applies
  the fragments with a general-purpose JSON Schema validator and adds the three semantic checks
  and the resolution step.

The hardest part is exact numeric distinctness (§2.4). It needs exact decimal comparison of number
literals, which an evaluator already needs for Core §7.4's equality. Neither implementation exists. The
scratch check described under Evidence is not one.

## Unresolved questions

1. **The ceiling numbers.** The six numbers of §7 are reasoned from the intended use: short labels,
   a few keys, and lists the size of an enumerated code list. No published pack uses either shape,
   so none were measured. Raising a ceiling later is compatible and lowering one is not, so the
   numbers err low. This stays open until packs exist, or until the disposition accepts the
   reasoning.
2. **More positions.** Annotations might also be wanted on the value-set object, on exceptions, on
   evidence requirements or on sources. Admitting a position later is compatible, and removing one
   is not. This record admits only the positions the issue names, and leaves the others open until
   someone asks for one.
3. **Where the unreferenced-set advisory lives.** `JPS-VALUE-SET-UNREFERENCED` could join RFC
   0027's report contract, or stay beside `JPS-RULES-OVERLAP` in the document corpus's advisory
   vocabulary. That depends on RFC 0027's disposition, which is open.

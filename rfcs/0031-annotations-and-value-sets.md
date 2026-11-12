# RFC 0031: Annotations and annotated value sets

- Status: Accepted
- Type: Standards track, draft maturity. A Core amendment: one specification-defined extension in
  the reserved namespace, one new root member and one new fact-condition member.
- Created: 2026-11-11
- Accepted: 2026-11-12, by the maintainer, on the same-vendor round-1 review; see
  [Acceptance](#acceptance).
- Target: Core `specVersion` `0.5.0`, released under tag `v0.5.0`. It was staged under the working
  selector `0.4.0-draft`, which was never released. Tag `v0.4.0` carries `specVersion` `0.3.0`, so
  no `specVersion` `0.4.0` is assigned ([VERSIONING.md](../VERSIONING.md)).
- Issue: [#301](https://github.com/Judgment-Pack/judgment-pack-spec/issues/301)
- Released text: [`spec/judgment-pack-core.md`](../spec/judgment-pack-core.md), Core `0.5.0`.

> This record is accepted and its content is part of Core `0.5.0`. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **This record is normative for nothing.** The MUST, SHOULD and MAY below were proposed wording;
> Core `0.5.0`'s text, schema and corpora are what is released, and they govern where this record
> differs. Below, "the staged" names what was staged under `0.4.0-draft` before the release, and
> "the next selector" names `0.5.0`. The vectors in [Conformance](#conformance) are named and
> described here; they are released in the `0.5.0` corpora.
>
> **Review standing.** [RFC 0009](0009-interim-review-regime.md) requires a recorded adversarial
> review by a model from a different vendor, with a written disposition for each finding, on the
> pull request that creates this RFC. That review has not happened, and this record does not claim
> it; the pull request that created this record was merged without it. A review by a model from the
> drafting vendor, run at the maintainer's direction, is recorded with the maintainer's disposition
> of each finding at
> [`rfcs/reviews/0031-round-1.md`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/rfcs/reviews/0031-round-1.md),
> and this text is revised by that disposition. The maintainer waived the different-vendor review
> for this record and accepted it on that round-1 review ([Acceptance](#acceptance)). That is a
> same-vendor review, not a cross-vendor claim.
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
   No new member is added to the pack, the outcome or the rule. The extension is optional and
   never required. Well-formed annotations are inert: adding, changing or removing them changes no
   disposition and no error class. A malformed annotation makes the pack not conforming, as any
   other schema violation does.
2. **Annotated value sets.** A pack may declare named sets of values once, at its root, and a
   fact condition with operator `in` may name one instead of repeating the list inline. Each entry
   may carry a description and annotations. A reference behaves exactly as the inline list of the
   entries' values.

Both are defined by one rule, the **evaluation form** (§4 below). An evaluator MUST give a
semantically conforming pack the result Core gives the same pack with every annotation removed and
every reference replaced by its inline list. Inertness, substitution and the absence of any new
reason, disposition member or error class all follow from that rule.

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
  ceilings in §7 are reasoned, not measured; the round-1 disposition accepts them as reasoned
  (Unresolved question 1, answered).

While this record was drafted, and again after its first review round, its schema fragments and
examples were checked against a scratch copy of the Core schema with the fragments applied, using a
general-purpose JSON Schema validator, a short checker for the semantic rules and the evaluation
form, and the regular-expression engines of three languages for the character class and the key
pattern of §1.7. That check is not committed and is not implementation evidence. After the round-1
review, the revised string pattern of §1.7 was swept over every code point in the engines §1.7
lists; the repository's harness repeats that sweep for Python and, where Node is installed, for
ECMA-262 in Unicode mode.

## Specification

### 1. Annotations

#### 1.1 Name and positions (A1)

The extension name is `org.judgmentpack.annotations`. Its value is an *annotations object*
(§1.3).

It MAY appear as a key of exactly these `extensions` objects:

- the root `extensions` (the pack);
- each outcome's `extensions` (Core §6.4);
- each rule's `extensions` (Core §6.5); and
- each value-set entry's `extensions` (§2.3), which admits this name and no other.

In every other `extensions` object, the name remains refused, as every reserved name is today.
Those objects are the decision's, each evidence requirement's, each source's, each exception's, the
escalation's and the metadata's. A structural validator reports such a document as not structurally
conforming (`JPS-STRUCTURE-EXTENSION-NAME`). A value-set object has no `extensions` member at all
(§2.2), so annotations on a set are an unknown member (`JPS-STRUCTURE-UNKNOWN-MEMBER`).

Every other name beginning `org.judgmentpack.` remains refused in every `extensions` object: by the
extension-name grammar (`JPS-STRUCTURE-EXTENSION-NAME`), or in an entry's, which admits one name
only, as an unknown member (`JPS-STRUCTURE-UNKNOWN-MEMBER`).

An annotations object describes only the object that carries it. This record defines no
inheritance and no merging. A rule does not acquire the pack's annotations, and an entry does not
acquire its set's.

#### 1.2 Optional, never required (A2)

The annotations extension is optional and has no capability.

`org.judgmentpack.annotations` MUST NOT appear in `metadata.requiredExtensions`. The item pattern
of `metadata.requiredExtensions` never admits this name, whatever other specification-defined names
it comes to admit ([RFC 0016](0016-outcome-values.md) proposes admitting its own). A pack that
lists it is therefore not structurally conforming (`JPS-STRUCTURE-EXTENSION-NAME`), and an
evaluator reports `pack-not-conformant`, never `unsupported-required-extension` (Core §8.4).
Listing the name in an implementation's supported-extension set changes nothing: no rule reads
that entry. Core §8.2 does not say so today; this record proposes that it does (§9): a name in a
supported-extension set that no conforming pack can list in `metadata.requiredExtensions` is not a
capability, and it is ignored, is not an error, and changes no result.

The reason is that an extension with no effect on evaluation gives a consumer nothing to
support. Making it requirable would let a pack force a refusal from every evaluator that does
not list a name whose presence changes no result.

Core §9's general rule applies to what annotations mean: a consumer preserves them when
round-tripping a pack, and a consumer that neither displays nor filters by them may disregard their
content. It does not apply to their shape. The rules of §§1.1 and 1.3–1.6 are part of the schema
(§1.7), so a malformed annotation makes the pack not structurally conforming, and an evaluator
given that pack reports `pack-not-conformant` (Core §8.4). An implementation MUST NOT skip these
rules because the extension is optional.

#### 1.3 Syntax (A3)

An annotations object is a JSON object with 1 to 16 members (the base ceiling, §7).

- **Keys.** Each member name is a local identifier: the whole name matches Core's
  local-identifier grammar `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$` (Core §5), and it has at most 64
  characters. A name that ends in a line feed is not a local identifier, whatever a pattern's end
  anchor admits. Some regular-expression engines let `$` match before a final line feed, so the
  schema also refuses, in a key, the controls, the two separators and the embeddings and overrides
  (U+0000–U+001F, U+007F–U+009F and U+2028–U+202E; §1.7), and the rule holds in every engine §1.7
  lists. Core's local-identifier and extension-name patterns had the same latent property, and the
  next version closes it for them too (Unresolved question 5, answered).
- **Values.** Each member value is either an annotation string (§1.4), or an array of 1 to 16
  annotation strings in which no string appears twice.
- **String equality.** Two annotation strings are equal when they are the same sequence of Unicode
  code points, after JSON unescaping. There is no Unicode normalization, no case folding and no
  trimming, so the NFC and NFD spellings of one text are two strings. This is JSON Schema's
  `uniqueItems` equality for strings.

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
- contains, after JSON unescaping, no character of the *refused class*:
  - U+0000–U+001F and U+007F–U+009F, the C0 controls, delete and the C1 controls (including tab,
    line feed, escape, U+0085 and the single-character control sequence introducer U+009B);
  - U+2028 and U+2029, the line and paragraph separators;
  - every bidirectional format character: U+061C (the Arabic letter mark), U+200E and U+200F (the
    left-to-right and right-to-left marks), U+202A–U+202E (the embeddings and overrides LRE, RLE,
    PDF, LRO and RLO) and U+2066–U+2069 (the isolates LRI, RLI, FSI and PDI); and
  - every other invisible, default-ignorable character: U+00AD (soft hyphen), U+034F (combining
    grapheme joiner), U+115F–U+1160, U+3164 and U+FFA0 (Hangul fillers), U+17B4–U+17B5 (Khmer
    inherent vowels), U+180B–U+180F (Mongolian variation selectors and vowel separator),
    U+200B–U+200D (zero-width space, non-joiner and joiner), U+2060–U+206F (word joiner, invisible
    operators and the deprecated format characters, beside the isolates), U+FE00–U+FE0F
    (variation selectors), U+FEFF (zero-width no-break space), U+FFF0–U+FFF8 (unassigned, reserved
    as default-ignorable), U+1BCA0–U+1BCA3 (shorthand format controls), U+1D173–U+1D17A (musical
    format controls) and U+E0000–U+E0FFF (the tag characters, the supplementary variation
    selectors and the unassigned rest of that range); and
- does not begin or end with a white-space character: one with the Unicode property White_Space,
  which is exactly U+0009–U+000D, U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029,
  U+202F, U+205F and U+3000. Those the refused class holds are refused anywhere. The others are
  admitted between two other characters. A string made only of white space begins with it, so it is
  refused.

The refused code points are exactly U+0000–U+001F, U+007F–U+009F, U+00AD, U+034F, U+061C,
U+115F–U+1160, U+17B4–U+17B5, U+180B–U+180F, U+200B–U+200F, U+2028–U+202E, U+2060–U+206F, U+3164,
U+FE00–U+FE0F, U+FEFF, U+FFA0, U+FFF0–U+FFF8, U+1BCA0–U+1BCA3, U+1D173–U+1D17A and
U+E0000–U+E0FFF. Apart from the controls and the two separators, that is the Unicode property
Default_Ignorable_Code_Point, as Unicode 17.0 defines it. The list, not the property, is the rule: a
later Unicode version that changes the property does not change it.

An annotation string is single-line text, meant as a filter key or a short label in compact views
such as chips, table cells and terminal output, and compared by code points (§1.3). The reasons
differ by kind:

- **Controls and separators.** A C0 or C1 control, or a line or paragraph separator, breaks a line
  or a view, and a control sequence can take control of a terminal. Nothing a consumer does at
  display makes them safe in a one-line label.
- **Bidirectional format characters.** Each can make a label display in an order other than its
  logical one, and make two different labels look alike. Embeddings and overrides reorder the
  characters that follow them. A mark is an invisible strong character: it sets the direction of the
  neutral characters beside it and, as a label's first strong character, the label's base direction,
  so the logical string `"\u200Fapprove\u200F not\u200F do"`, isolated with its direction taken from
  its content (`dir="auto"` or `<bdi>` in HTML), displays as "do not approve". An unbalanced isolate
  inside a label defeats the isolation a consumer adds with isolate characters, the only isolation
  plain text, terminals, logs and spreadsheet cells have (D1): a lone U+2069 closes the consumer's
  isolate early, and a lone U+2066–U+2068 leaves it open to the end of the line. A label in a single
  right-to-left script displays correctly with none of them, so the class refuses them all. D1 still
  requires isolating a label, because a label's own strong characters affect the neutral text beside
  it.
- **Invisible characters.** A default-ignorable character displays as nothing in most contexts, so
  two labels that differ by one look alike: a list of distinct values shows `intake` twice when one
  of them ends in U+200B, and a view filtered by one silently omits what carries the other (D2). Tag
  characters can also spell invisible ASCII text, a channel aimed at automated readers of a pack.
- **White space at either end.** Most displays trim it or do not show it, so `intake` and `intake`
  followed by a space look alike for the same reason; a string of white space alone displays as
  nothing, which makes it a second spelling of "no value" (§1.5).

**The cost.** An annotation cannot hold an emoji sequence that needs a zero-width joiner or a
variation selector (joined family and profession emoji, tag-sequence flags, the text and emoji
presentation selectors), nor text whose correct shaping needs the zero-width joiner or non-joiner,
as some spellings in Arabic-script and Indic-script writing do. An annotation is a short
machine-comparable label, a filter key; free text belongs in the object's `description`, which
admits every character and which D1 governs.

Every other character is admitted, including format characters that are not default-ignorable (for
example U+0600–U+0605 and U+FFF9–U+FFFB), combining marks, and characters of different scripts that
look alike (U+0061 and U+0430). Those are why D2 requires a consumer that lists distinct values or
states a filter to show every character outside printable ASCII unambiguously (§8).

Core admits every character, refused here or not, in its free-text strings (titles, labels,
descriptions, route names), in fact paths and in operands. Its identifiers, version strings,
extension names and pack `id` are ASCII by their grammars (Core §5; the pack `id` is an RFC 3986
URI), so they carry none of them. Refusing a character here does not remove it from the pack's
other strings; D1 applies wherever a consumer displays one.

#### 1.5 Empty forms (A5)

These are refused:

- an empty annotations object `{}` (`JPS-STRUCTURE-MIN-PROPERTIES`);
- an empty list `[]` (`JPS-STRUCTURE-COLLECTION-ARITY`); and
- an empty string `""` (`JPS-STRUCTURE-MIN-LENGTH`); and
- a string made only of white space, such as `" "`, which begins with white space (§1.4,
  `JPS-STRUCTURE-NOT`).

Absence is the one spelling for "no annotations" and for "no value for this key", so "has the key"
and "has a value for the key" never differ. This matches Core's `nonEmptyString` for its other
human-readable strings. The root `valueSets` collection is different: it admits `[]`, as Core's
optional root collections do (§2.1).

#### 1.6 Duplicates (A6)

- A duplicate member name in an annotations object is refused by the carrier, as in any JSON
  object (Core §2.1, `JPS-CARRIER-DUPLICATE-MEMBER`).
- A repeated string in a list is a structural refusal (`JPS-STRUCTURE-UNIQUE-ITEMS`).
- The same key in two annotations objects, for example on the pack and on a rule, is not a
  duplicate. Each object is independent (§1.1).

#### 1.7 Schema fragment

These definitions would be added to `$defs`. `annotatedExtensions` replaces `extensions` as the
type of the root's, each outcome's and each rule's `extensions` member. `entryExtensions` is the
type of an entry's `extensions` (§2.7). Every other `extensions` member keeps the existing
`extensions` definition, which refuses every reserved name. `metadata.requiredExtensions` is
unchanged by this fragment. The vendor-name branch of `annotatedExtensions` is the extension-name
pattern pair of Unresolved question 5's answer, which the `extensions` definition and the
`metadata.requiredExtensions` item take too.

```json
{
  "annotationString": {
    "type": "string",
    "minLength": 1,
    "maxLength": 256,
    "not": {
      "type": "string",
      "pattern": "[\u0000-\u001f\u007f-\u009f\u00ad\u034f\u061c\u115f\u1160\u17b4\u17b5\u180b-\u180f\u200b-\u200f\u2028-\u202e\u2060-\u206f\u3164\ufe00-\ufe0f\ufeff\uffa0\ufff0-\ufff8\ud82f\udca0-\ud82f\udca3\ud834\udd73-\ud834\udd7a\udb40\udc00-\udb43\udfff]|^[\u0009-\u000d\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]|[\u0009-\u000d\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]$"
    }
  },
  "annotations": {
    "type": "object",
    "minProperties": 1,
    "maxProperties": 16,
    "propertyNames": {
      "maxLength": 64,
      "pattern": "^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$",
      "not": { "pattern": "[\u0000-\u001f\u007f-\u009f\u2028-\u202e]" }
    },
    "additionalProperties": {
      "type": ["string", "array"],
      "if": { "type": "string" },
      "then": { "$ref": "#/$defs/annotationString" },
      "else": {
        "minItems": 1,
        "maxItems": 16,
        "uniqueItems": true,
        "items": { "$ref": "#/$defs/annotationString" }
      }
    }
  },
  "annotatedExtensions": {
    "type": "object",
    "propertyNames": {
      "anyOf": [
        { "const": "org.judgmentpack.annotations" },
        {
          "pattern": "^[a-z][a-z0-9]*(?:\\.[a-z][a-z0-9\\-]*)+$",
          "not": { "type": "string", "pattern": "^org\\.judgmentpack\\.|[\u0000-\u001f\u007f-\u009f\u2028-\u202e]" }
        }
      ]
    },
    "properties": {
      "org.judgmentpack.annotations": { "$ref": "#/$defs/annotations" }
    },
    "additionalProperties": true
  },
  "entryExtensions": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "org.judgmentpack.annotations": { "$ref": "#/$defs/annotations" }
    }
  }
}
```

**The patterns.** Both are written with JSON escapes (`\u0000`), not regular-expression escapes
(the JSON text `\\u0000`, which reaches the engine as `\u0000` and which some engines cannot
compile). After JSON decoding, a pattern holds the code points themselves, so an engine receives
literal characters, whatever escape syntax it supports. A code point outside the Basic Multilingual
Plane is written as its UTF-16 surrogate pair: `\ud82f\udca0` is U+1BCA0, and a JSON parser
decodes the pair into that one code point, so `\ud82f\udca0-\ud82f\udca3` reaches the engine
as the range U+1BCA0–U+1BCA3. A lone surrogate would not survive every JSON parser, so the ranges
are not split into surrogate alternatives.

The string pattern is the refused class, unanchored, then the white space at either end:
`[class]|^[white space]|[white space]$`. It sits under `not`, so a string is refused when any part
matches. Every line terminator an engine's anchors know (U+000A, U+000D, U+0085, U+2028, U+2029) is
in the class, so an engine whose `$` matches before a final line terminator, or whose `^` and `$`
match at every line, refuses exactly the same strings. Under `propertyNames` the `not` holds the
controls, the two separators and the embeddings and overrides only: a key is ASCII by the
local-identifier grammar, and that `not` exists to refuse a key that ends in a line feed, which an
engine whose `$` matches before a final line feed would otherwise admit (§1.3).

**Engines.** The string pattern was swept over every code point, at the start of a string, inside it
and at its end, and refused exactly the code points of §1.4 in: Python 3.12 `re` (the engine of the
repository's validator); ECMA-262 in Unicode mode, with the `u` flag and with the `v` flag, in Node
22; RE2, through Go 1.26's `regexp`; Perl 5.30; Java's `java.util.regex`; and Ruby 2.7. ECMA-262
without Unicode mode does not compile it: it reads the pattern as UTF-16 code units, and the low
surrogate of one pair followed by the high surrogate of the next is a range out of order. The JSON
Schema 2020-12 core specification asks that patterns be built with the `u` flag or equivalent
Unicode support. An engine that matches UTF-16 code units and has no Unicode mode cannot hold the
three ranges outside the Basic Multilingual Plane at all; an implementation built on one applies
them as a check of its own, with the same code and pointer. No other engine was tested, .NET's and
PCRE2 among them. Each pattern holds a literal U+0000, which a pattern interface that takes a
NUL-terminated string truncates; such an interface needs another spelling of the same class. The
identifier patterns of Unresolved question 5's answer were swept in the same engines.

In `annotationString` the `not` holds `"type": "string"` beside the pattern. A `pattern` holds for
every instance that is not a string, so without it a list item that is a number or a list would
fail `not` as well as `type`, and one wrong item would give two findings. With it, a non-string
satisfies the `not` and is refused once, by `type`. A member name is always a string, so the `not`
under `propertyNames` needs no `type`.

**Keywords.** The annotation value uses `type` and `if`/`then`/`else`, not `oneOf`, so a validator
reports the keyword that fails: `type` for a number or an object, `minLength` for an empty string,
`minItems` for an empty list, `uniqueItems` for a repeated string. The codes in
[Conformance](#conformance) follow from those keywords by one rule.

The maxima are the `base` ceilings. A reader supporting `extended` validates with the extended
ceilings, as Core §4.1 requires of every row (§7).

### 2. Value sets

#### 2.1 Declaration (V1)

A pack MAY declare the root member `valueSets`: an array of at most 64 value-set objects (the base
ceiling, §7). An empty array is admitted and declares no set, as Core's other optional root
collections (`evidenceRequirements`, `sources`, `exceptions`) admit one. Deleting a pack's last
set, once nothing references it, is then not a breaking edit, whether a writer removes the member
or keeps it empty. Two set objects equal under JSON Schema's equality are refused by the schema
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

A value-set object has no `extensions` member. `extensions` on a set, whatever it holds, is an
unknown member (`JPS-STRUCTURE-UNKNOWN-MEMBER`). Neither vendor extensions nor annotations attach to
a set, and an entry admits annotations only (§2.3). The reason is the evaluation form, which removes
the sets (§4.1). A vendor extension that lived only in a set or an entry would vanish from
`EF(P)`. If `metadata.requiredExtensions` listed it, `P` would meet Core §9's rule that a required
name appears as a key of some `extensions` object and `EF(P)` would not, so evaluators could
disagree about the pack, and the required extension would be inert. Admitting vendor extensions on
sets or entries later is a compatible addition, but that record would have to answer this
question first.

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
| `extensions` | no | the annotations extension (§1.1), and no other name |

**Types.** A set declares no type and may mix types, as an inline `in` operand may. Each value is
compared with the selected fact value under Core §7.4. A set of `1`, `"1"`, `true`, `null`, `[1]`
and `{"a": 1}` is six distinct values.

**Entry extensions.** An entry's `extensions` object admits exactly one key,
`org.judgmentpack.annotations`. A vendor name there, and every other reserved name, is an unknown
member (`JPS-STRUCTURE-UNKNOWN-MEMBER`), for the reason given in §2.2. Annotations can stay, because
they are never requirable (§1.2): removing them cannot remove a name `metadata.requiredExtensions`
lists.

Entry annotations use the same extension as every other position. One lookup rule,
`extensions["org.judgmentpack.annotations"]`, holds everywhere in the document.

#### 2.4 Repeated values (V4)

Two entries of one set may have equal values under Core §7.4's type-preserving equality. That is not
a conformance error at any layer. This record recommends that a tool that can decide equality of two
entry values report each entry whose value equals an earlier entry's with the advisory
`JPS-VALUE-SET-DUPLICATE-VALUE`, at the later entry's `value`; a recommendation, not a requirement.
A tool that cannot decide a pair, for example two number literals it cannot compare exactly, reports
no advisory for that pair. An advisory never changes document conformance. Where the advisory lives
is open, as for the unreferenced-set advisory (§2.6; Unresolved question 3), and it stays out of the
next version's Core text until that is settled.

**Evaluation is unaffected.** An inline `in` operand already admits repeated items, and a reference
compares exactly as its inline array does (§4.2), so a repeated entry changes no result. The
reference also inherits Core's numeric seam unchanged. Where Core §7.4 leaves a comparison with a
number open (Core §13), the open comparison is the inline array's, and the set neither adds an input
to it nor takes one out.

**Display.** Where two entries are equal, a consumer shows each entry as written, with its own
description and annotations. Nothing requires a consumer to merge them.

**Why not an error.** Refusing a set with two equal entries would make semantic conformance depend
on exact comparison of arbitrary number literals, such as `1e400` against `10e399`, or
`9007199254740993` against `9007199254740992`. Core places that comparison on evaluators
(Core §7.4) and leaves a seam in it (Core §13); no document conformance result in Core `0.3.0`
depends on it. The diagnostic code reported for an already non-conforming document can: Core's
`uniqueItems` compares numbers too, so two sets with one id whose entries differ only as
`9007199254740993` and `9007199254740992` give `JPS-SEMANTIC-DUPLICATE-ID` from a validator that
compares exactly and `JPS-STRUCTURE-UNIQUE-ITEMS` from one that compares through binary floating
point; the document is refused either way. A validator that compared through binary floating point
would refuse a conforming set, and two validators would disagree about whether one document
conforms. The cost of admitting repeats is that
one value can carry two descriptions, which a consumer shows as written.

Equality, for the advisory, is Core §7.4's:

- **Numbers** compare by mathematical value. `1`, `1.0`, `1e0` and `10E-1` are one value, and so
  are `10` and `1E1`, and `0` and `-0`. A tool can decide this exactly from the number literals.
  One way is to reduce each to a sign, a digit string without leading or trailing zeros, and an
  integer exponent. No exponent needs expanding, and a tool SHOULD NOT expand one (see Security and
  privacy). Converting through binary floating point does not decide equality: it equates
  `9007199254740993` with `9007199254740992`. A tool that can compare a pair only that way cannot
  decide it, and reports nothing for it.
- **Strings** compare by value, which for Core `0.3.0` is the sequence of code points, so NFC and
  NFD spellings of one text are two values. Core §13 lists normalization semantics as open. The
  advisory follows Core §7.4 wherever that question lands, so that it never disagrees with how `in`
  compares.
- **Booleans and null** compare by value.
- **Arrays** compare item by item, in order: `[1, 2]` and `[2, 1]` are distinct.
- **Objects** compare by member name and value, regardless of member order.
- **No coercion.** `1` and `"1"` are distinct. So are `"1.0"` and `"1.00"`: they are strings,
  and Core §7.4 compares decimal strings as strings.

#### 2.5 No nesting (V5)

A set references no other set, and an entry has no `valueSet` member
(`JPS-STRUCTURE-UNKNOWN-MEMBER`). An entry value that looks like a reference, such as
`{"valueSet": "tier-codes"}`, is a literal JSON object, compared as one.

There is no union, intersection or difference of sets. An author lists the entries.

#### 2.6 Unreferenced sets (V8)

A set that no condition references is admitted and inert. Its entries take no part in evaluation,
and no evaluation-phase counter counts them; a limit on the pack as presented does (§4.2).
This record recommends that a pack-design tool report it with the advisory
`JPS-VALUE-SET-UNREFERENCED`; a recommendation, not a requirement. An advisory never changes
document conformance, and this one stays out of the next version's Core text for now (Unresolved
question 3).

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
      }
    }
  },
  "valueSetEntry": {
    "type": "object",
    "additionalProperties": false,
    "required": ["value"],
    "properties": {
      "value": true,
      "description": { "$ref": "#/$defs/nonEmptyString" },
      "extensions": { "$ref": "#/$defs/entryExtensions" }
    }
  }
}
```

Added to the root's `properties`:

```json
{
  "valueSets": {
    "type": "array",
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
  - Carrying both is a structural refusal (`JPS-STRUCTURE-VALUE-SET-REFERENCE`, at the condition).
  - Carrying neither is the existing refusal of a fact condition without its operand
    (`JPS-STRUCTURE-REQUIRED-MEMBER` at `…/value`).
- `valueSet` is admitted only with operator `in`. With any other operator it is a structural refusal
  (`JPS-STRUCTURE-VALUE-SET-REFERENCE`, at `…/operator`). For a single value, a one-entry set
  serves. For the inverse test, `not` serves.
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
no `valueSets` member or with `valueSets: []`. A reference that names an id held only by another
kind of object, such as an outcome, names no declared set: identifiers are collection-local (§2.2),
and the member `valueSet` looks only in `valueSets`. Since set ids are unique (§2.2), a resolved
reference resolves exactly once, as Core §3.3 requires of every local reference.

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
  "allOf": [
    "... the two existing if/then members, for ordered operators and for in, unchanged ...",
    {
      "if": { "required": ["valueSet"] },
      "then": {
        "not": { "required": ["value"] },
        "properties": { "operator": { "const": "in" } }
      },
      "else": { "required": ["value"] }
    }
  ]
}
```

The string in `allOf` stands for the two existing members, which are kept as they are; it is not
schema text. The existing members constrain `value` only when `value` is present, so a reference
satisfies them. `value` leaves the top-level `required` list and moves into the new member's
`else`.

The member uses `if`/`then`/`else`, not `oneOf`, so a validator reports the keyword that fails.
Carrying neither member fails `required` at `…/value`, as Core's fact condition without an operand
does today, and keeps Core's code. Carrying both fails `not` at the condition, and a reference with
another operator fails `const` at `…/operator`. Those two keywords are mapped to
`JPS-STRUCTURE-VALUE-SET-REFERENCE`, by the rule under [Codes](#codes).

### 4. The evaluation form and inertness (E1)

#### 4.1 Definition

The *evaluation form* `EF(P)` of a semantically conforming pack `P` is the JSON value produced by
these three steps:

1. **Expand references.** Each fact condition, in each condition position of §3.2, that carries
   `valueSet` loses that member and gains a `value` member. The new `value` is an array holding the
   `value` of each entry of the named set, in entry order.
2. **Remove the sets.** The root member `valueSets` is removed, whatever it holds, `[]` included.
   Every set, entry, entry description and entry annotation goes with it.
3. **Remove annotations.** The member `org.judgmentpack.annotations` is removed from the root's
   `extensions` object, from each outcome's and from each rule's. If removing it leaves that
   `extensions` object empty, the member is removed. An `extensions` object already empty in `P` is
   kept.

Nothing else changes. The steps act on positions, not on content. A literal inside a `value`
operand, an entry value and a vendor extension's value are never inspected. A literal that looks
like a reference, or like an annotations object, stays exactly as it is. A member named
`extensions` inside an entry value, as inside any operand, is data and not an `extensions` object:
under the next selector, the `extensions` objects are the ones the schema defines as members of
Core objects. That reading is a change that takes effect under the next selector, not a reading of
Core `0.3.0` (Compatibility). RFC 0016 reads "an `extensions` object" the same way.

`EF(P)` is itself a semantically conforming pack of the same `specVersion`, with the same
`profile`:

- Each step only removes optional members, or turns a resolved reference into an `in` operand.
  That operand is a non-empty array, because a set has at least one entry, and Core sets no maximum
  on an inline operand.
- No `id` changes and every other reference still resolves. Two items of a root collection, which
  differ in `id` in `P`, still differ in `EF(P)`, so the schema's `uniqueItems` still holds.
- Every name in `metadata.requiredExtensions` still appears as a key of an `extensions` object
  (Core §9). No such name is `org.judgmentpack.annotations` (§1.2). The removed material holds no
  other name: a set object has no `extensions` member (§2.2), and an entry's holds annotations only
  (§2.3). In the root's, an outcome's or a rule's `extensions`, step 3 removes the annotations key
  alone. A required vendor key beside it stays, untouched, and the object is not emptied.

A pack with no `valueSets` member, no reference and no annotations is its own evaluation form.

#### 4.2 The requirement

For a semantically conforming pack `P`, given the same facts document, evidence-availability
document and supported-extension set, an implementation claiming evaluator conformance MUST
produce for `P` the result Core §§7–8 give `EF(P)`, with limits applied as below. That result is
the byte-identical canonicalized disposition (Core §8.3), or an evaluation error of the same class
(Core §8.4).

- **Document limits.** Any limit an implementation applies to the pack as presented is a document
  limit for this rule, whatever the implementation calls it: bytes, nesting depth, string size, and
  a count of parsed values or nodes over the whole document are all document limits (Core §10).
  They apply to `P` as presented, as to any input, and they count every annotation and every entry
  of every set, referenced or not. A pack refused by one is refused as Core refuses any input over
  that limit. `EF(P)` is never admitted, and is never measured against a document limit.
- **Evaluation-phase limits.** A collection-size or work counter that an implementation charges
  while it evaluates applies to the work `EF(P)` requires. Expansion is charged per reference: each
  reference costs what its inline twin would, so a set referenced by three conditions is charged
  three times, once at each, as three inline arrays would be.
- An implementation MUST NOT charge an evaluation-phase counter for annotations, for value-set
  objects, or for the entries of a set that no condition references.

A pack that is not semantically conforming has no evaluation form. An evaluator reports
`pack-not-conformant` for it (Core §8.4), whether the fault is in an annotation, a set, a reference
or anywhere else.

These follow from that requirement together with Core §8.3:

- **Annotations are inert.** Between semantically conforming packs, adding, changing or removing
  annotations never changes a disposition or an error class, unless the change carries `P` across
  one of the implementation's document limits. A label that spells an outcome id, a reason or a
  route target changes nothing. A malformed annotation is not a change between conforming packs:
  the pack is then not structurally conforming, and the result is `pack-not-conformant` (§1.2).
- **Substitution.** A reference behaves exactly as its inline array: the same Core §7.4 equality, the
  same `unknown` for an absent path, and the same reading under `not`. The order of sets, and of
  entries within a set, changes nothing, because `in` tests membership.
- **Nothing new reaches the disposition.** There is no new reason, error class or disposition
  member. Core §8.3 admits "these members and no others", so no annotation, set id or entry description
  ever appears in a disposition. A trace outside the disposition MAY name the set a condition
  referenced and the entries a fact matched.
- **The numeric seam is inherited unchanged.** Core §7.4 says `in` "A match produces `true`; no
  match produces `false`" (line 618), and leaves equality with an unrepresentable number to Core §13.
  A reference compares exactly as its inline array does, so it adds no input to that seam and
  takes none out. Document conformance does not reach the seam either: repeated entries are not an
  error (§2.4).

#### 4.3 Limits and work

This subsection explains §4.2's limit rule. It adds no requirement.

`P` and `EF(P)` are different bytes, and either may be the larger: annotations make `P` larger,
and a set that many conditions reference makes `EF(P)` larger. Only `P` is presented, so only `P`
is admitted against a document or carrier limit. A pack that annotations push over such a limit is
refused as any pack over it is, with the class Core gives that case (see Compatibility). An
evaluator that measured `EF(P)` against a document limit could refuse a pack presented within the
limit, or admit one presented over it. Core §10 already places every input above a limit outside the
portable claim, and the staged rows stay well inside any plausible limit.

Evaluation-phase limits measure work, and the work is `EF(P)`'s. A reference costs what its inline
twin costs, at each reference. Under [RFC 0008](0008-bounded-collection-quantifiers.md)'s work
accounting, if adopted, an authored `in` operand reached through a reference is charged as the
expanded array. Annotations, value-set objects and the entries of an unreferenced set take no part
in evaluation, so no evaluation-phase counter counts them. A limit on the document as presented
counts them like any other content: an implementation whose only collection-size limit is a cap on
the parsed nodes of the whole document applies it at admission, as a document limit, and it counts
every annotation and entry. The ceilings of §7 bound them as document content. No staged row
reaches any limit, so these rules are stated, not tested by the corpus.

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
- **No serialization of the evaluation form.** This record defines no serialization of `EF(P)`.
  Evaluation forms are compared as JSON values under Core §7.4 equality, never by a digest of a
  serialization that can lose number identity. Two packs with equal evaluation forms evaluate alike
  within §4.2's limit rule, and are not the same pack.
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

Annotation keys and strings, value-set and entry descriptions, and entry values when displayed, are
display data from the pack's author. They are as untrusted as every other pack string (Core §10). A
consumer that displays one:

- MUST render it as text. It MUST escape the string for the output context, and MUST NOT let the
  context interpret it as markup, a template, a spreadsheet formula or a terminal control sequence;
- MUST NOT resolve, fetch or otherwise dereference it. A string that looks like a URI, a path or an
  address is not a locator;
- MUST NOT treat it as naming anything in the pack. An annotation value equal to an outcome id
  names no outcome (Core §5: meaning is not inferred from spelling);
- MUST NOT present it as a review, an approval, a verified property, or a classification that
  anything other than the author's statement established (Core §3.5). Reviews belong in
  `metadata.reviews`;
- MUST isolate each annotation key and string it shows inline with other text, so that a value's
  direction does not reorder the text around it. In HTML, for example, `<bdi>`, or `dir="auto"` on
  the value's own element, does this. Annotation strings hold no bidirectional format character
  (§1.4), so isolation added with isolate characters, as in plain text, cannot be undone from
  inside one. It SHOULD isolate the other display data the same way;
- MUST, where it lists distinct annotation keys or values or states a filter, show them as D2
  requires (§8), so that two values that look alike can be told apart; and
- SHOULD show annotations as the author's labels, visually distinct from Core members.

The fixture `valid-annotations-display-hostile` (see [Conformance](#conformance)) carries markup, a
template, a formula prefix, a URI, right-to-left text beside digits and neutral characters, a word
spelled with a look-alike letter from another script, stacked combining marks, an inner em space and
an outcome id as values: what §1.4 still admits. Validators accept it, and evaluation ignores it.
How it is rendered is a consumer's test, not a Core class.

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
for no gain. The document byte limit is the only aggregate bound on annotations in a pack. The
number of annotated objects is bounded by it only, because
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
  order. Show entry descriptions and annotations beside the entry, and each of two equal entries
  as written (§2.4). When a trace names the entries a fact matched, show their annotations. That
  stays outside the disposition (§4.2).
- **Inline for reading.** A view of one rule MAY show a reference expanded, provided it says that
  the list comes from the named set.
- **Document a vocabulary.** Core defines no keys. A project MAY document its own key vocabulary.
  Keys carry meaning only by such a convention.

**D2, filtered views (normative).** A consumer that presents a filtered view of a pack MUST state,
in the view, that it is filtered, and by which keys and values. A filtered view is one that omits
outcomes, rules or entries because of their annotations. For each kind of item it filters, the
view MUST state how many items it shows and how many the pack holds, for example "rules: 4 of 9".

Wherever a consumer lists distinct annotation keys or values, or states a filter, it MUST show
every character outside printable ASCII (U+0020–U+007E) in a key or value unambiguously: in a form
from which the reader can recover each such code point, such as its `U+` number beside or in place
of the glyph. Two different strings then never display alike, whatever the font. Showing a value in
a filter's statement exactly as it is shown in the list it was picked from meets this when the list
meets it.

A review made from a filtered view covers only what the view showed. It is not a review of the pack.

A filtered view is not a pack. It MUST NOT be offered for evaluation, signing or hashing as the
pack. A disposition is always the whole pack's, and omitted items take part in every evaluation.

A filtered view is not redaction either. The omitted items, and their annotations, remain in the
pack's bytes (see Security and privacy).

D1 and D2 bind any consumer that displays or filters annotations, as Core §10's prohibitions bind
every implementation. No Core conformance class tests display. They bind what is displayed to a
person: a machine-readable form that carries each key and value with its exact code points, such as
JSON a program reads, is data, not a display and not a listing under D2, and the consumer that
displays a key or value read from it is the one bound.

### 9. Where each part lands

| Place | Change |
| --- | --- |
| Core §2.1 | none; duplicate member names are already refused |
| Core §3.3 | two bullets: value-set ids are unique; every `valueSet` resolves |
| Core §3.3.1 | a reference reads as its set's values (§4.4); the two value-set advisories (§§2.4, 2.6) are not added here until RFC 0027 is dispositioned (Unresolved question 3) |
| Core §8.2 | names in a supported-extension set that are not requirable are ignored (§1.2) |
| Core §4 | a `valueSets` row in the root table; the collection-order sentence covers sets and entries |
| Core §4.1 | the six rows of §7 |
| Core §5 | value-set references join the list of references that resolve within one document (line 451) |
| Core §6 (new subsection) | the value set and its entries (§2) |
| Core §7.4 | the `valueSet` member (§3.1) |
| Core §8 (new paragraph) | the evaluation form and §4.2's requirement, with its limit rule |
| Core §9 | a paragraph on specification-defined extensions (their value is governed by their definition, which qualifies "Values may be any JSON value", line 950; each definition states where the name may appear and whether it may be required); then annotations: A1–A6, D2 |
| Core §9 (change under the next selector) | an `extensions` object is one the schema defines as a member of a Core object; a member named `extensions` inside an operand, an entry value or an extension's value is data, so a required name found only there is missing (§4.1; Compatibility). It takes effect under the next selector and does not change Core `0.3.0` |
| Core §10 | D1; which limits §4.2 applies to the pack as presented and which to the work its evaluation form requires |
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

Its outcomes are Example 1's with the annotations removed: `accept` and `refer`, each with its `id`
and `label` only.

The evaluation form of Example 2 is Example 3's pack. `valueSets` is removed, together with its
entry descriptions and annotations, the reference is replaced by the entries' values in entry
order, and the outcome `accept` loses its annotations and then its emptied `extensions`. By §4.2,
every conforming evaluator gives the two packs the same result for every input, within the limit
rule there. Their bytes, and so their digests, differ (§5).

Example 3, with those outcomes, is also a valid Core `0.3.0` pack, given `"specVersion": "0.3.0"`.
Examples 1 and 2 are not. The `0.3.0` schema refuses the reserved key, the root member `valueSets`
and the `valueSet` member.

## Alternatives

**(a) A new `annotations` member on the pack, each outcome and each rule.** Not chosen; the
decision on the issue chose the reserved extension.

- *For (a):* a shorter path and one level less nesting. Annotations would be visible to every
  schema-driven editor as a first-class member.
- *Against (a), and for the extension:*
  - Core §9 already reserves `org.judgmentpack.` for specification-defined extensions. This is the
    designed slot, and using it leaves the shapes of Core's objects unchanged.
  - Tools of the next version that handle `extensions` generically preserve annotations on
    round-trip (Core §9) without knowing this record. Tools bound to the `0.3.0` schema refuse such
    a pack, because that schema refuses the reserved name, as they would refuse a new member; for
    them neither choice is better.
  - The inertness obligation already exists for optional extensions (Core §9, line 952), so §4.2 makes
    an existing promise testable rather than adding a new kind of member.
  - A consumer that ignores extensions loses nothing it needs.
- *Cost of the extension:* this is the first time Core constrains the value of an extension name.
  Core §9 would gain the paragraph listed in this record's §9.

**Other alternatives considered:**

- **No change.** Labels stay in vendor extensions. Every tool picks its own name and shape, no two
  tools share a view, consumers must accept any JSON value, and no row checks inertness.
- **A profile, or a companion specification.** Rejected. A Core profile is a named set of ceilings
  and "changes no members" (Core §4.1), so neither feature can be one. A companion specification
  beside Core would leave a Core reader unable to evaluate a reference, for the reason in §2.1, and
  would give labels no place Core defines, which is the problem this record addresses.
- **Product-only behaviour.** Rejected. A product could keep labels and shared lists in its own
  files or its own vendor extension, and expand the lists when it writes a pack. Each product then
  picks its own shape, as under no change, the labels travel apart from the pack, as with a
  sidecar, and no two products share a view or agree on what a shared list means.
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
- **Admitting empty forms inside annotations.** Rejected (§1.5): `{}`, `[]` and `""` stay refused,
  so absence is the one spelling for "none" there. An entry list stays at one entry or more, so a
  reference always expands to a non-empty operand.
- **Refusing `valueSets: []`.** Rejected (§2.1). One spelling for "no sets" would have been tidier,
  but Core's optional root collections (`evidenceRequirements`, `sources`, `exceptions`) admit
  `[]`. Refusing it would make a writer that empties the collection remove the member, and would
  make deleting the last set a breaking edit.
- **Refusing repeated entry values, as a semantic rule.** Rejected (§2.4). Document conformance
  would then depend on exact comparison of arbitrary number literals, which Core asks of no
  document validator, and validators that compared through binary floating point would disagree
  about one document. Evaluation needs no such rule, because an inline operand admits repeats.
  The advisory reports repeats where a tool can decide them.
- **Vendor extensions on value-set objects and entries.** Not admitted (§§2.2–2.3). The evaluation
  form removes the sets, so a required vendor name that appeared only there would vanish from it.
  Core §9 would then hold for `P` and fail for `EF(P)`, and the required extension would be inert.
  Admitting them later is compatible, once a record answers that question, for example by
  requiring a listed name to appear outside the sets as well.
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
  - Vendor extensions remain available for structured data, except on sets and entries (§2.2).
- **Trimming whitespace or normalizing case and Unicode.** Rejected. Equality is on code points
  (§1.3), and a validator that normalized would let two tools disagree about repeated strings in
  a list. White space at either end is refused instead of trimmed (§1.4), so no string has a trimmed
  twin.
- **Refusing only the embeddings and overrides, and admitting the marks and isolates.** Rejected
  in round 1 (§1.4). The first draft did this, reasoning that right-to-left labels need marks and
  isolates. They do not: a label in one right-to-left script displays correctly without them, and a
  mark or an unbalanced isolate can make a label display in an order other than its logical one or
  defeat the isolation D1 requires.
- **Admitting the invisible characters and requiring consumers to show them.** Rejected in round 1
  (§1.4). A consumer that does not show them hides a rule from a filtered view, and a label gains
  nothing from them that a short machine-comparable key needs. The cost, emoji sequences and
  shaping that need joiners, is stated in §1.4. Refusing the format characters that are not
  default-ignorable, and characters that look alike across scripts, would refuse ordinary text;
  D2's display rule covers them instead.
- **A registry of keys.** Rejected for now. Core infers no meaning from spelling (Core §5), and a
  registry is governance work that no evidence yet asks for. A project can document its own
  vocabulary (§8).
- **Annotations on the value-set object, exceptions, evidence requirements or sources.** Not
  included. The issue names packs, outcomes, rules and entries, and a value-set object has no
  `extensions` member at all (§2.2). Widening later is compatible, and narrowing is not
  (Unresolved question 2).

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
- **Ceilings without measurement** (Unresolved question 1, answered by accepting them as
  reasoned). These are also Core's first pack ceilings beyond escalation routes.
- **Repeated entries are admitted.** One value can carry two descriptions or two sets of labels
  (§2.4). Only an advisory reports it, and only from a tool that can decide the pair.
- **No vendor data on sets or entries.** Data an author wants to attach to one set or one entry in
  a vendor's own shape has no place until a later record admits it (§2.2).

## Compatibility

**Version.** These changes belong to the next Core `specVersion` after `0.3.0`. As Core §11
requires, compatibility is explicit:

- **Reader and writer.** A `0.3.0` reader refuses a pack declaring the next selector, by the exact
  selector (Core §4), and it does not acquire support by ignoring or replacing the selector. The `0.3.0`
  schema also refuses each new shape: the reserved key, the root `valueSets` and the `valueSet`
  member. A writer targeting `0.3.0` cannot emit them.
- **Semantic.** For a pack that uses neither feature, `EF(P)` is `P`, so this record changes no
  result for it, apart from the one shape that the next selector's reading of an `extensions`
  object refuses (below).
- **The reading of an `extensions` object, a change under the next selector.** Core `0.3.0` §9 says
  every required name "MUST appear as a key in at least one `extensions` object", and does not say
  whether a member named `extensions` inside data, such as an item of an `in` operand, is one. That
  is a known open point of the released text. The repository's released `0.3.0` checker counts such
  a member; another reader may not. This record does not change Core `0.3.0`, its corpus or that
  checker. Under the next selector, an `extensions` object is one the schema defines as a member of
  a Core object, and a member named `extensions` inside an operand, an entry's value or an
  extension's value is data (§4.1). The evaluation form needs that reading: under the broad one, a
  required name found only in an unreferenced entry's value would be present in `P` and absent from
  `EF(P)`, and `EF(P)` would not be semantically conforming.
- **Migrating up from `0.3.0`.** One shape aside, no `0.3.0` shape is refused by these rules. The
  exception is a `0.3.0` pack whose required name appears only under a member named `extensions`
  inside data, which the broad reading admits. Under the next selector it is refused
  (`JPS-SEMANTIC-MISSING-REQUIRED-EXTENSION`), and moving it up means adding the name as a key of a
  real `extensions` object as well. With that exception, and as far as this record goes, changing
  only the selector is enough, and evaluation is unchanged. The next version's other changes are
  their own. One of them narrows what some validators admitted, never what Core `0.3.0`'s grammar
  admits under ECMA-262: a local identifier, an extension name, a pack version or a decimal operand
  that ends in a line terminator is refused in every engine (Unresolved question 5).
  - Labels kept in a vendor extension MAY be moved to the reserved name by hand, once they meet
    §§1.3–1.5. There is no automatic coercion: a vendor value outside those rules must be edited,
    not truncated, joined or dropped by a tool.
  - An inline list MAY be replaced by a reference.
  - Each such edit changes the bytes, so the pack SHOULD receive a new `version` (Core §11).
- **Migrating down to `0.3.0`.** `EF(P)` with the selector changed is evaluation-equivalent within
  §4.2's limit rule, but it loses the annotations and the entry descriptions. A vendor extension
  can carry labels under `0.3.0`.
- **Profiles.** No new profile and no new capability. Both features are in Core, the schema carries
  their `base` maxima, and the six ceilings join Core §4.1's table. Reader capability records are
  unchanged. A reader that lists `extended` commits to the extended values of the new rows, as to
  every row.
- **Evaluator claims.** A claim attaches to the next `specVersion` and its corpus (Core §3.4.1). The
  staged rows land there and nowhere earlier.
- **Released artifacts.** The released `0.3.0` schema, Core text and corpora are unchanged.

**Other records.**

- [RFC 0016](0016-outcome-values.md) relaxes both of the schema's refusals for its own name: as an
  `extensions` key and as a `metadata.requiredExtensions` item, since its extension must be
  required. This record relaxes only the first, for `org.judgmentpack.annotations`, at the
  positions of §1.1; the `requiredExtensions` item pattern never admits it (§1.2). Core §9 should
  gain one paragraph on specification-defined extensions, whichever record lands first. That
  paragraph states, for each such extension, where its name may appear and whether it may be
  required. Each record then adds its own name. The paragraph and the schema shape both records
  need are drafted once, below (Coordination with RFC 0016).
- [RFC 0008](0008-bounded-collection-quantifiers.md)'s work accounting would apply to the
  evaluation form (§4.3).
- [RFC 0027](0027-pack-design-advisories.md)'s advisories would read a reference as its set
  (§4.4). The two value-set advisories may belong in its report contract (Unresolved question 3).
- [RFC 0001](0001-pack-manifest.md)'s manifest digest is over exact bytes, so it covers
  annotations and sets (§5).

**Coordination with RFC 0016.** RFC 0016 puts `org.judgmentpack.outcome-values` on an outcome's
`extensions`, which is also an annotated position (§1.1), and makes it requirable. Whichever record
lands second changes the outcome's `extensions` type and the `metadata.requiredExtensions` item. If
both land, these definitions would do it:

```json
{
  "outcomeExtensions": {
    "type": "object",
    "propertyNames": {
      "anyOf": [
        { "enum": ["org.judgmentpack.annotations", "org.judgmentpack.outcome-values"] },
        {
          "pattern": "^[a-z][a-z0-9]*(?:\\.[a-z][a-z0-9\\-]*)+$",
          "not": { "type": "string", "pattern": "^org\\.judgmentpack\\.|[\u0000-\u001f\u007f-\u009f\u2028-\u202e]" }
        }
      ]
    },
    "properties": {
      "org.judgmentpack.annotations": { "$ref": "#/$defs/annotations" },
      "org.judgmentpack.outcome-values": { "$ref": "#/$defs/outcomeValues" }
    },
    "additionalProperties": true
  },
  "requiredExtensionName": {
    "type": "string",
    "anyOf": [
      { "const": "org.judgmentpack.outcome-values" },
      {
        "pattern": "^[a-z][a-z0-9]*(?:\\.[a-z][a-z0-9\\-]*)+$",
        "not": { "type": "string", "pattern": "^org\\.judgmentpack\\.|[\u0000-\u001f\u007f-\u009f\u2028-\u202e]" }
      }
    ]
  }
}
```

`outcomeExtensions` would be the type of each outcome's `extensions`; the root's and each rule's
keep `annotatedExtensions` (§1.7), which never admits RFC 0016's name, and an entry's keeps
`entryExtensions`. `requiredExtensionName` would be the item schema of
`metadata.requiredExtensions`: it admits RFC 0016's name and, as today, every vendor name, and never
`org.judgmentpack.annotations` (§1.2). `outcomeValues` is RFC 0016's definition of its value. The
code rule of [Codes](#codes) maps a key refused by either `anyOf` to
`JPS-STRUCTURE-EXTENSION-NAME`, as it maps `annotatedExtensions`'s.

Evaluation-form step 3 removes only the member `org.judgmentpack.annotations` (§4.1). RFC 0016's
member, beside it on an outcome, stays in `EF(P)` untouched, and its name, which a pack that uses it
must require, still appears there. §4.1's argument that `EF(P)` keeps every required name holds
with it.

The shared Core §9 paragraph, drafted once here for both records (the staged draft's §9.1 carries
the first two sentences' substance today):

> **Specification-defined extensions.** A specification-defined extension is one whose name begins
> with `org.judgmentpack.` and which this specification defines. Its value is governed by its
> definition, which qualifies "Values may be any JSON value". Each definition states the
> `extensions` objects in which its name may appear and whether the name may be listed in
> `metadata.requiredExtensions`; a name whose definition does not admit it there is never
> requirable. Every other name beginning with `org.judgmentpack.` is refused in every `extensions`
> object and in `metadata.requiredExtensions`. An `extensions` object is one the schema defines as
> a member of a Core object. The specification-defined extensions are
> `org.judgmentpack.annotations` (§9.2: on the root, outcomes, rules and value-set entries; never
> requirable) and, if RFC 0016 lands, `org.judgmentpack.outcome-values` (on outcomes; required by
> every pack that uses it).

**Questions this record leaves to Core.** A pack that annotations push over a documented byte
limit is refused like any oversize pack. Core §8.4 calls a pack failing the carrier layer
`pack-not-conformant` (line 913). It calls a document limit reached "while admitting an input"
`malformed-input` (line 922, and Core §10, line 976). When both apply, the order at line 930 selects
`pack-not-conformant`. Whether the second applies to the pack, which is "an input" to an
evaluation, is Core's question. This record does not change it.

### Graduation

This record was graduated by one pull request, which releases Core `specVersion` `0.5.0` under tag
`v0.5.0`. It is recorded here as done.

- **The working selector was never released.** `0.4.0-draft` named staged artifacts only. The
  version it staged is released as `0.5.0`, not `0.4.0`: tag `v0.4.0` carries `specVersion`
  `0.3.0`, and under the release numbering rule ([VERSIONING.md](../VERSIONING.md)) a tag's major
  and minor numbers are those of the `specVersion` it carries, so the number `0.4.0` is taken. A
  `0.5.0` reader refuses a pack declaring `0.4.0-draft`, by the exact-selector rule (Core §4), as it
  refuses every selector other than its own.
- **Packs written to the working selector.** Such a pack moves by changing its `specVersion` to
  `0.5.0`. That changes its bytes, so its digest changes too (§5), and it must then satisfy the
  released rules (Core §11). No reader admits it under both selectors. An implementation that
  admitted `0.4.0-draft` did so experimentally, outside every conformance claim.
- **Retired.** The staged schema, delta text, document cases, evaluation rows and example. Their
  content is in the released schema, Core text and corpora, under `$id`s in `/schema/0.5.0/`, the
  selector `0.5.0` and new digests. The record-shape catalog's change record
  `0009-core-0-5-0-released` records the staged schema's retirement, and Core's `draftVersion` there
  reads `0.5.0`.
- **The document cases and the `extended` profile.** The cases that need the `extended` profile are
  released in the document manifest, which names the reader profiles its cases run under
  (`readerProfiles`). `tools/profile_validation.py` applies the rows of §7.
- **The held evaluation row.** The `0.5.0` case schema admits specification-defined names in a
  supported-extension set, and the row `annotations-supported-extension-set` is released with the
  rest (Core §8.2 as amended, §1.2).
- **The evidence bar.** [Acceptance](#acceptance) states each item.

## Security and privacy

- **Display.** Annotations, set and entry descriptions and displayed entry values are untrusted
  display data (D1). The refused characters (§1.4) remove line breaks, terminal control sequences,
  every bidirectional format character, the invisible default-ignorable characters and white space
  at either end from annotations. Escaping, isolation of the bidirectional text that remains,
  showing every character outside printable ASCII where values are listed or a filter is stated
  (D2), and refusal to dereference are the consumer's duties.
- **Filtered views.** A view filtered by an annotation value hides what does not match. D2 makes the
  view say so, by which keys and values, and how many items of each kind it shows out of how many
  the pack holds; and it makes two different values display differently where a reviewer picks one.
  A review made from a filtered view covers only what it showed.
- **Confusion.** A label such as `"status": "approved"` or `"priority": "first"` is the author's
  text, not a Core fact. Core has no rule priority (Core §6.5), and §4.2 makes a label unable to create
  one. D1 forbids presenting a label as a review or an approval.
- **No execution.** Core §10's "MUST NOT execute code found in strings or extensions" covers both
  features.
- **Resources.**
  - The ceilings (§7) bound each object.
  - **Expansion.** A 512-entry set referenced by many conditions expands to a large `EF(P)`. An
    evaluator SHOULD resolve a reference to the shared array, not copy it (§4.3). Work limits
    charge each comparison either way. `EF(P)` is never measured against a document limit (§4.2).
  - **The duplicate advisory.** Comparing pairs is quadratic in a set's size. A tool SHOULD instead
    compute an exact key per value (exact decimal numbers, objects with members sorted) and look
    up repeats by hash. The advisory is optional, so a tool that bounds its work may skip it.
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
   V1–V3, V5–V7), the document result of every advisory case (V4, V8), and the evaluation
   requirement (§4.2).
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

**Standing after round 1.** Item 1 is not met: the round-1 review was by a model from the drafting
vendor
([`rfcs/reviews/0031-round-1.md`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/rfcs/reviews/0031-round-1.md))
and does not count. Item 3 was not met at round 1: one implementation existed, experimentally, and a
second did not. A second evaluator has been added since, written from the text by the drafting
vendor; what it covers is under Implementation. At acceptance item 3 is met in part
([Acceptance](#acceptance)). Item 6 is met by the disposition of Unresolved question 1. Item 7's
coordination is drafted in this record (Compatibility, Coordination with RFC 0016). The other items
stand as the round-1 review found them.

### Acceptance

On 2026-11-12 the maintainer accepted this record and directed its graduation into Core `0.5.0`,
with the different-vendor review waived. Item by item:

1. **Not met as written; waived.** No model from a different vendor reviewed this record. The
   maintainer waived that review for this record and accepted the round-1 review by a model from
   the drafting vendor, with its disposition, as the review of record. That is a same-vendor review,
   not a cross-vendor claim.
2. **Met.** The vectors existed as staged files, were reviewed in round 1 and were held to the
   repository's checks, the static check included. They are released in the `0.5.0` corpora.
3. **Met in part.** Two implementations have run the vectors: the project's reference runtime and
   the second evaluator in this repository (`tools/core_050_eval.py`). Both are by the drafting
   vendor; neither is a different vendor's. Neither passes every vector: both refuse the 18
   document cases that declare the `extended` profile, which neither supports, and the second
   evaluator supports `base` only. The reference runtime passed the 208 document cases and 82 rows staged at
   c867b35, the held row held; it has not run the seven document cases #308 added, the two fixtures
   #304 rewrote, or anything under the selector `0.5.0`. The second evaluator runs every row and
   every other document case under `0.5.0`. The maintainer directed acceptance on that basis; the
   reference runtime's take-up of `0.5.0` is the follow-up.
4. **Met.** The draft schema carried the fragments under the repository's schema tests; it is
   released as the `0.5.0` Core schema.
5. **First half met; second half met in part.** The published example
   `examples/expense-approval-annotated.json` uses both features. The reference runtime has a
   consumer view with its own tests, but its D1 isolation of Markdown text direction is open there.
   The maintainer directed graduation on that basis.
6. **Met** by the disposition of Unresolved question 1.
7. **Met.** Core text is drafted for each row of §9, and the Core §9 paragraph is coordinated with
   RFC 0016 (Compatibility, Coordination with RFC 0016).

<!-- RUNTIME-STATUS -->
At acceptance, the reference runtime's main branch passes the vectors staged at c867b35 (208
document cases with 18 extended-profile cases reported unsupported; 82 rows; the held row held); it
has not yet taken up the changes this pull request adds, and will vendor the released `0.5.0`.

The candidate period is waived by the maintainer: `v0.5.0` has no release candidate.

### Codes

Codes are provisional test metadata, as the [conformance README](../conformance/README.md) says
of every code. Every structural code below follows one rule, the rule Core's released document
corpus already follows. A generic JSON Schema validator reports the keyword that fails, and the
code is:

1. **Core's code for the definition, where Core has one.** A key or value held to the
   local-identifier grammar (an annotation key, a set `id`, a `valueSet` member) takes
   `JPS-STRUCTURE-LOCAL-ID` from its `pattern`. A key refused by the extension-name grammar, alone
   or as a branch of an `anyOf`, takes `JPS-STRUCTURE-EXTENSION-NAME`. An `in` operand that is not
   an array takes `JPS-STRUCTURE-IN-OPERAND`.
2. **Otherwise, Core's code for the keyword, where Core's corpus uses one.** `required` →
   `JPS-STRUCTURE-REQUIRED-MEMBER`; `additionalProperties` → `JPS-STRUCTURE-UNKNOWN-MEMBER`;
   `type` → `JPS-STRUCTURE-TYPE`; `minItems` → `JPS-STRUCTURE-COLLECTION-ARITY`; `maxItems` →
   `JPS-STRUCTURE-MAXITEMS`; `minLength` → `JPS-STRUCTURE-MIN-LENGTH`; `uniqueItems` →
   `JPS-STRUCTURE-UNIQUE-ITEMS`; `not` → `JPS-STRUCTURE-NOT`.
3. **Otherwise, one new code per keyword.** `maxLength` → `JPS-STRUCTURE-MAX-LENGTH`, for keys and
   strings alike; `minProperties` → `JPS-STRUCTURE-MIN-PROPERTIES`; `maxProperties` →
   `JPS-STRUCTURE-MAX-PROPERTIES`. The new codes separate words with hyphens, as `MIN-LENGTH` and
   `UNIQUE-ITEMS` do. `MAXITEMS` keeps the spelling Core's corpus already uses.

Three refusals take a code mapped from a keyword other than the one the rule above would name, and
the table says so where each applies:

- A rule that ties members to one another takes one code named for the rule, whichever keyword
  states it, as Core's exceptions take `JPS-STRUCTURE-EXCEPTION-SHAPE`. Here that is
  `JPS-STRUCTURE-VALUE-SET-REFERENCE`, mapped from `not` at the condition when both members are
  present, and from `const` at `…/operator` when the operator is not `in` (§3.3).
- The `not` under an annotations object's `propertyNames` repeats a refusal the local-identifier
  grammar already makes, for engines whose `$` admits a trailing line feed. A key it refuses takes
  the grammar's code, `JPS-STRUCTURE-LOCAL-ID`, mapped from `not` there (§1.3).
- The `not` beside the local-identifier, pack-version, decimal-operand and extension-name grammars
  (Unresolved question 5) takes its grammar's code: `JPS-STRUCTURE-LOCAL-ID`,
  `JPS-STRUCTURE-PACK-VERSION`, `JPS-STRUCTURE-DECIMAL-OPERAND`, and
  `JPS-STRUCTURE-EXTENSION-NAME` at the key or the item. A reserved name outside its definition's
  positions is refused by that `not` in place of the released pattern's lookahead, with the code it
  had.

A pointer to a refused key names the key's member, as Core's pointer for an extension-name refusal
does, for example `…/org.judgmentpack.annotations/Tier`. A pointer to an unknown member names that
member. `…` stands for the path to the object the case puts the extension on.

A refused key and a refused value at that key therefore share one pointer. Findings compare as a
set of (code, pointer) pairs, so the pair yields one finding per code: a 65-character key whose
value has 257 characters gives one `JPS-STRUCTURE-MAX-LENGTH`, not two
(`structural-annotations-key-and-string-too-long`).

**How findings compare.** A case's findings compare as a set of (code, pointer) pairs. A keyword
reported twice at one pointer, as some validators or regular-expression engines report it, is one
finding, and the order of findings carries no meaning. A key that the annotated `extensions`
object's `propertyNames` refuses is one refusal, `JPS-STRUCTURE-EXTENSION-NAME` at the key, not one
per branch of its `anyOf`. A validator may also report findings inside the outermost `oneOf` that
encloses the stated one; Core's corpus admits those, and so does this record's.

This record proposes five new provisional conformance codes, and no others:

- structural: `JPS-STRUCTURE-MAX-LENGTH`, `JPS-STRUCTURE-MIN-PROPERTIES`,
  `JPS-STRUCTURE-MAX-PROPERTIES` and `JPS-STRUCTURE-VALUE-SET-REFERENCE`; and
- semantic: `JPS-SEMANTIC-UNRESOLVED-VALUE-SET`.

It also proposes two advisory codes, outside conformance: `JPS-VALUE-SET-UNREFERENCED` and
`JPS-VALUE-SET-DUPLICATE-VALUE`. They stay out of the Core text of the next version until RFC 0027
is dispositioned (Unresolved question 3); the staged manifest lists them as `advisoryCodes`.

### Staged document cases

"New" marks a code this record proposes. Pointers are given where the case fixes them.

| Case | Purpose | Expected |
| --- | --- | --- |
| `valid-annotations-positions` | Example 1: root, outcome, two rules, a vendor key beside annotations | valid |
| `valid-annotations-required-vendor-beside` | a vendor name listed in `metadata.requiredExtensions` whose only key is beside annotations, in one rule's `extensions` | valid; its evaluation form keeps that key, so Core §9 holds for both (§4.1) |
| `valid-annotations-empty-extensions` | a rule whose `extensions` is `{}`, beside annotations on the pack | valid; its evaluation form keeps the empty object (§4.1) |
| `valid-annotations-value-set-entry` | Example 2: annotations on entries | valid |
| `valid-annotations-at-ceilings` | 16 keys of 64 characters, each a list of 16 strings of 256 characters | valid |
| `valid-annotations-non-bmp` | a 256-character string of characters outside the BMP: code points are counted, not code units or bytes | valid |
| `valid-annotations-one-element-list` | `["intake"]` on one rule, `"intake"` on another | valid |
| `valid-annotations-nfc-nfd` | one list holding `"\u00e9"` and `"e\u0301"`, the NFC and NFD spellings of one text | valid: two strings, so `uniqueItems` holds |
| `valid-annotations-display-hostile` | markup, a template, a formula prefix, a URI, right-to-left text beside digits and neutral characters, a look-alike letter from another script (U+0430), stacked combining marks, an inner em space, an outcome id as values | valid |
| `valid-annotations-class-neighbours` | the code point just below and just above each refused range, inside a string (the nearest assigned one where that is unassigned), and the format characters U+0600, U+0605 and U+FFFB, which are not default-ignorable | valid |
| `valid-annotations-inner-white-space` | each white-space character the refused class does not hold (U+0020, U+00A0, U+1680, U+2000, U+2003, U+200A, U+202F, U+205F, U+3000), between two other characters | valid |
| `valid-annotations-edge-neighbours` | strings that begin and end with a code point next to a white-space character (U+0021, U+00A1, U+167F, U+1681, U+1FFE, U+2010, U+2027, U+2030, U+205E, U+2FFB, U+3001) | valid |
| `structural-annotations-in-decision` | and one case each for `-evidence-requirement`, `-source`, `-exception`, `-escalation` and `-metadata` | `JPS-STRUCTURE-EXTENSION-NAME` at `…/extensions/org.judgmentpack.annotations` |
| `structural-value-set-extensions-*` | `extensions` on a set object: one case holding annotations, one holding a vendor key | `JPS-STRUCTURE-UNKNOWN-MEMBER` at `/valueSets/0/extensions` |
| `structural-value-set-entry-extension-*` | in an entry's `extensions`, one case each: `com.example.note` alone; `com.example.note` beside annotations; `org.judgmentpack.future` | `JPS-STRUCTURE-UNKNOWN-MEMBER` at `/valueSets/0/entries/0/extensions/` and the name |
| `structural-annotations-required` | the name in `metadata.requiredExtensions` | `JPS-STRUCTURE-EXTENSION-NAME` at `/metadata/requiredExtensions/0` |
| `structural-reserved-name-in-annotated-position` | `org.judgmentpack.future` in a rule's `extensions` | `JPS-STRUCTURE-EXTENSION-NAME` at `/rules/0/extensions/org.judgmentpack.future` |
| `structural-annotations-not-object` | the extension's value is a string | `JPS-STRUCTURE-TYPE` at `…/org.judgmentpack.annotations` |
| `structural-annotations-empty-object` | `{}` | `JPS-STRUCTURE-MIN-PROPERTIES` (new) at `…/org.judgmentpack.annotations` |
| `structural-annotations-empty-object-*` | `{}` at the root, on an outcome and on a value-set entry, one case each | `JPS-STRUCTURE-MIN-PROPERTIES` (new) at `…/org.judgmentpack.annotations` |
| `structural-annotations-empty-list` | `"category": []` | `JPS-STRUCTURE-COLLECTION-ARITY` at `…/category` |
| `structural-annotations-empty-string` | `"category": ""` | `JPS-STRUCTURE-MIN-LENGTH` at `…/category` |
| `structural-annotations-key-grammar-*` | one case each: `Tier`, `tier_1`, `-tier`, `tier-`, `ti--er`, `1tier`, the empty key | `JPS-STRUCTURE-LOCAL-ID` at the key |
| `structural-annotations-key-trailing-lf` | the key `"tier\n"`, escaped in the JSON | `JPS-STRUCTURE-LOCAL-ID` at the key: from `pattern`, or mapped from `not` under an engine whose `$` admits the line feed |
| `structural-local-id-trailing-lf-id` | a rule id `"accept-request\n"`, escaped in the JSON | `JPS-STRUCTURE-LOCAL-ID` at `/rules/0/id`: from `pattern`, or mapped from `not` under an engine whose `$` admits the line feed (Unresolved question 5) |
| `structural-local-id-trailing-lf-reference` | a rule's `outcome` `"accept\n"` | `JPS-STRUCTURE-LOCAL-ID` at `/rules/0/outcome`, before the reference is resolved |
| `structural-extension-name-trailing-lf` | the key `"com.example.review-policy\n"` in the decision's `extensions` | `JPS-STRUCTURE-EXTENSION-NAME` at the key |
| `structural-extension-name-trailing-lf-annotated` | the same key in a rule's `extensions`, beside annotations | `JPS-STRUCTURE-EXTENSION-NAME` at the key: one refusal, not one per branch of the `anyOf` |
| `structural-required-extension-trailing-lf` | `"com.example.review-policy\n"` in `metadata.requiredExtensions`, beside the key without it | `JPS-STRUCTURE-EXTENSION-NAME` at `/metadata/requiredExtensions/0` |
| `structural-pack-version-trailing-lf` | `"version": "0.1.0\n"` | `JPS-STRUCTURE-PACK-VERSION` at `/version` |
| `structural-decimal-operand-trailing-lf` | an ordered comparison's operand `"10\n"` | `JPS-STRUCTURE-DECIMAL-OPERAND` at `/rules/0/when/value` |
| `structural-annotations-key-too-long` | a 65-character key | `JPS-STRUCTURE-MAX-LENGTH` (new) at the key |
| `structural-annotations-too-many-keys` | 17 keys | `JPS-STRUCTURE-MAX-PROPERTIES` (new) at `…/org.judgmentpack.annotations` |
| `structural-annotations-too-many-strings` | a list of 17 | `JPS-STRUCTURE-MAXITEMS` at the list |
| `structural-annotations-string-too-long` | 257 characters | `JPS-STRUCTURE-MAX-LENGTH` (new) at the string |
| `structural-annotations-key-and-string-too-long` | a 65-character key whose string has 257 characters | one `JPS-STRUCTURE-MAX-LENGTH` (new) at the key, the string's pointer too |
| `structural-annotations-duplicate-string` | `["intake", "intake"]` | `JPS-STRUCTURE-UNIQUE-ITEMS` at the list |
| `structural-annotations-value-*` | one case each: a number, a Boolean, null, an object | `JPS-STRUCTURE-TYPE` at the value |
| `structural-annotations-value-nested-list` | `[["intake"]]` | `JPS-STRUCTURE-TYPE` at the inner list, `…/0` |
| `structural-annotations-list-item-number` | `[1]` | `JPS-STRUCTURE-TYPE` once, at the item, `…/0` (§1.7) |
| `structural-annotations-control-*` | one case each, escaped in the JSON: NUL, TAB, LF, ESC, DEL, U+0085, U+009B, U+2028, U+2029 | `JPS-STRUCTURE-NOT` at the string |
| `structural-annotations-trailing-lf-*` | `"intake\n"`, escaped in the JSON: one case as a key's value, one as the last item of a list | `JPS-STRUCTURE-NOT` at the string |
| `structural-annotations-bidi-*` | one case each, inside a string: U+061C, U+200E, U+200F, U+202A, U+202B, U+202C, U+202D, U+202E, U+2066, U+2067, U+2068, U+2069 | `JPS-STRUCTURE-NOT` at the string |
| `structural-annotations-bidi-reordered-label` | the round-1 review's `"\u200Fapprove\u200F not\u200F do"`, which displays as "do not approve" under automatic direction | `JPS-STRUCTURE-NOT` at the string |
| `structural-annotations-invisible-*` | one case each, inside a string: U+00AD, U+034F, U+115F, U+1160, U+17B4, U+17B5, U+180B, U+180E, U+180F, U+200B, U+200C, U+200D, U+2060, U+2064, U+206A, U+206F, U+3164, U+FE00, U+FE0E, U+FE0F, U+FEFF, U+FFA0, U+FFF0, U+FFF8, U+1BCA0, U+1BCA3, U+1D173, U+1D17A, U+E0000, U+E0001, U+E0041, U+E007F, U+E0100, U+E0FFF | `JPS-STRUCTURE-NOT` at the string |
| `structural-annotations-invisible-only` | a string that is only U+200D | `JPS-STRUCTURE-NOT` at the string |
| `structural-annotations-tag-text` | `intake` followed by tag characters that spell `hidden note` | `JPS-STRUCTURE-NOT` at the string |
| `structural-annotations-invisible-filter-twin` | the round-1 review's filter example: two rules, `intake` and `intake` followed by U+200B | `JPS-STRUCTURE-NOT` at the second rule's string |
| `structural-annotations-leading-white-space-*`, `structural-annotations-trailing-white-space-*` | one case each, at the start and at the end of a string: U+0020, U+00A0, U+1680, U+2000, U+200A, U+202F, U+205F, U+3000 | `JPS-STRUCTURE-NOT` at the string |
| `structural-annotations-white-space-only`, `structural-annotations-white-space-only-ideographic` | `" "`, and two U+3000 | `JPS-STRUCTURE-NOT` at the string |
| `structural-annotations-trailing-white-space-list` | `"intake "` as the last item of a list | `JPS-STRUCTURE-NOT` at the item |
| `carrier-annotations-duplicate-key` | one key twice in one annotations object | `JPS-CARRIER-DUPLICATE-MEMBER` |
| `valid-value-sets-empty` | `"valueSets": []` and no reference | valid |
| `structural-value-set-entries-empty` | `"entries": []` | `JPS-STRUCTURE-COLLECTION-ARITY` at `/valueSets/0/entries` |
| `structural-value-set-unknown-member` | a set with `type` | `JPS-STRUCTURE-UNKNOWN-MEMBER` at `/valueSets/0/type` |
| `structural-value-set-entry-unknown-member` | an entry with `label` | `JPS-STRUCTURE-UNKNOWN-MEMBER` at `/valueSets/0/entries/0/label` |
| `structural-value-set-entry-reference` | an entry with `valueSet` (nesting) | `JPS-STRUCTURE-UNKNOWN-MEMBER` at `/valueSets/0/entries/0/valueSet` |
| `structural-value-set-missing-*` | one case each: no `id`, no `entries`, an entry without `value` | `JPS-STRUCTURE-REQUIRED-MEMBER` at the missing member |
| `structural-value-set-bad-id` | `Priority_Tiers` | `JPS-STRUCTURE-LOCAL-ID` at `/valueSets/0/id` |
| `structural-value-sets-identical` | two byte-identical set objects | `JPS-STRUCTURE-UNIQUE-ITEMS` at `/valueSets` |
| `structural-value-sets-too-many` | 65 sets | `JPS-STRUCTURE-MAXITEMS` at `/valueSets` |
| `structural-value-set-too-many-entries` | 513 entries | `JPS-STRUCTURE-MAXITEMS` at `/valueSets/0/entries` |
| `structural-value-set-reference-and-value` | both members | `JPS-STRUCTURE-VALUE-SET-REFERENCE` (new) at the condition, mapped from `not` |
| `structural-fact-without-operand` | neither member | `JPS-STRUCTURE-REQUIRED-MEMBER` at `…/value` |
| `structural-value-set-reference-operator-*` | one case each: `equals`, `not-equals`, `greater-than` | `JPS-STRUCTURE-VALUE-SET-REFERENCE` (new) at `…/operator`, mapped from `const` |
| `structural-value-set-reference-and-value-operator-equals` | `value` and `valueSet` together, with operator `equals` | `JPS-STRUCTURE-VALUE-SET-REFERENCE` (new) at the condition; the same code at `…/operator` is admitted, inside the condition's `oneOf` |
| `structural-value-set-reference-bad-id` | `"valueSet": "Tiers"` | `JPS-STRUCTURE-LOCAL-ID` at `…/valueSet` |
| `structural-value-set-reference-in-value` | `"value": {"valueSet": "priority-tiers"}` with `in` | `JPS-STRUCTURE-IN-OPERAND` at `…/value` |
| `semantic-unresolved-value-set-*` | one case each: in a rule, in an exception, in `applicability`, nested under `all` and `not`, with no `valueSets` member, with `valueSets: []`, and naming an id held only by an outcome | `JPS-SEMANTIC-UNRESOLVED-VALUE-SET` (new) at the `valueSet` member |
| `semantic-duplicate-value-set-id` | two sets, one id | `JPS-SEMANTIC-DUPLICATE-ID` at `/valueSets/1/id` |
| `advisory-value-set-duplicate-value-*` | one case each: a repeated string; `1` and `1.0`; `10` and `1E1`; `0` and `-0`; objects differing only in member order; equal nested arrays; equal values with different descriptions | valid, with advisory `JPS-VALUE-SET-DUPLICATE-VALUE` (new) at the later entry's `value` |
| `valid-value-set-unrepresentable-numbers` | `1e400` and `10e399`: one value in two spellings | valid whatever a tool decides; the advisory is expected only from a tool that compares the literals exactly |
| `valid-value-set-mixed-types` | `1`, `"1"`, `true`, `null`, `[1]`, `{"a": 1}` | valid, no advisory |
| `valid-value-set-large-integers` | `9007199254740993` and `9007199254740992` | valid, no advisory (distinct) |
| `valid-value-set-array-order` | `[1, 2]` and `[2, 1]` | valid, no advisory (distinct) |
| `valid-value-set-decimal-strings` | `"1.0"` and `"1.00"` | valid, no advisory (distinct strings) |
| `valid-value-set-nfc-nfd` | `"\u00e9"` and `"e\u0301"`, the NFC and NFD spellings of one text | valid, no advisory (distinct strings) |
| `valid-value-set-literal-object-entry` | an entry value `{"valueSet": "priority-tiers"}` | valid (a literal) |
| `valid-extensions-member-in-data` | `{"extensions": {"org.judgmentpack.future": 1, "Bad": 2}}` as an entry value and as an `in` operand item | valid: data, which no extension-name rule reads (Compatibility) |
| `valid-value-set-shared` | one set referenced by two rules, once under `not` | valid |
| `valid-value-set-id-shared-with-outcome` | a set and an outcome with one id | valid (collection-local) |
| `advisory-value-set-unreferenced` | a declared set that nothing references | valid, with advisory `JPS-VALUE-SET-UNREFERENCED` (new) |
| `profile-<resource>-*` | for each of the six rows of §7: `base` + 1 under `base`; `base` + 1 under `extended`; `extended` + 1 under `extended` | refused with the row's code below; valid; refused with that code |
| `valid-profile-<resource>-extended-at-extended`; `valid-profile-value-sets-base-at-base`, `valid-profile-value-set-entries-base-at-base` | each row of §7 exactly at its `extended` ceiling under `extended`; the two value-set rows exactly at `base` under `base` (the four annotation rows are at `base` in `valid-annotations-at-ceilings`) | valid |

The profile cases' codes follow from the keyword that carries each ceiling:

| Row of §7 | Code when over the ceiling |
| --- | --- |
| annotation keys per annotations object | `JPS-STRUCTURE-MAX-PROPERTIES` at the annotations object |
| annotation strings per list | `JPS-STRUCTURE-MAXITEMS` at the list |
| annotation key characters | `JPS-STRUCTURE-MAX-LENGTH` at the key |
| annotation string characters | `JPS-STRUCTURE-MAX-LENGTH` at the string |
| value sets | `JPS-STRUCTURE-MAXITEMS` at `/valueSets` |
| entries per value set | `JPS-STRUCTURE-MAXITEMS` at `/valueSets/0/entries` |

`profile-unsupported` is not among them. It answers a declared profile the reader does not support,
not a document over a ceiling of a profile it does (Core §4.1).

### Staged evaluation rows

Each row carries a pack, facts, evidence availability and a supported-extension set, as a released
row does. "Paired" rows share inputs and an expected result.

| Row | Purpose | Expected |
| --- | --- | --- |
| `annotations-inert-<result>` | for each of `outcome`, `not-applicable`, `unknown` (unresolved), `conflict` and `no-match`: a baseline pack, the same pack annotated, and the same pack with changed annotations | paired: one disposition per result |
| `annotations-inert-mimic` | labels spelling outcome ids, reason names and route targets, and `"priority": "first"` on one of two conflicting rules | the baseline's `unresolved` with `conflict` |
| `annotations-inert-<result>` | for each of `missing-required-evidence`, `exception-escalation` and `fallback`: a second baseline with a required evidence requirement, an escalate exception, a `fallbackOutcome` and two escalation routes (one filtered by `missing-required-evidence`, one without triggers), annotated and with changed annotations | paired: `unresolved` with `missing-required-evidence` and both routes; `unresolved` with `exception-escalation` and the unfiltered route only; the fallback outcome with no route |
| `annotations-inert-error-class` | annotations in the same `extensions` object as an unsupported required vendor extension; and annotations beside a malformed evidence document | the baseline's class: `unsupported-required-extension`; `malformed-input` |
| `annotations-required-vendor-beside` | the first case of the row above, with the vendor name in the supported-extension set | paired with the pack without annotations: one disposition |
| `annotations-supported-extension-set` | the baseline, with `org.judgmentpack.annotations` in the supported-extension set and without it | paired: one disposition (§1.2) |
| `annotations-malformed-*` | one case each, on facts for which the well-formed baseline gives an outcome: an annotations object with 17 keys; an annotation string with an embedded TAB, escaped in the JSON | `pack-not-conformant`, not the baseline's disposition (§1.2) |
| `annotations-listed-as-required` | the baseline, annotated, with `org.judgmentpack.annotations` in `metadata.requiredExtensions` | `pack-not-conformant`, never `unsupported-required-extension` (§1.2) |
| `extension-inert-vendor` | a vendor optional extension present and absent, which Core §9 states but no row checks | paired |
| `value-set-substitution-<case>` | for each of `match`, `no-match` and `unknown` (absent path): a reference and its inline form | paired |
| `value-set-type-preserving` | fact `"1"` against entry `1`; fact `true` against entry `"true"` | no match |
| `value-set-decimal-string` | fact `"1.0"` against entry `"1.00"` | no match |
| `value-set-nfc-nfd` | fact `"\u00e9"` against an entry `"e\u0301"`, both escaped in the JSON | no match |
| `value-set-numeric` | fact `1.0` against entry `1` | match |
| `value-set-composite` | a fact object whose member order differs from the entry's | match |
| `value-set-repeated-entries` | a set holding one value twice, and its inline form with the same repeat: a fact holding that value; a fact holding no entry's value | paired with inline: match; no match |
| `value-set-shared-exclusive` | the expense example's shape, with one set referenced by an `in` rule and under `not` in the other | one outcome, no conflict |
| `value-set-diverged-copies` | the same pack inline, with the two copies differing by one value, for a fact holding that value | `unresolved` with `conflict`: the hazard a shared set removes |
| `value-set-in-exception` | a reference in an exception's `when` | paired with inline |
| `value-set-in-exception-no-match` | a reference in an exception's `when` that the fact does not match | paired with inline: the rule's outcome stands |
| `value-set-in-applicability` | a reference in `applicability`, not matching | `not-applicable`, paired with inline |
| `value-set-under-not` | a reference under `not` | paired with inline |
| `value-set-under-all`, `value-set-under-any` | a reference under `all`, and one under `any`, in a rule's `when` | paired with inline |
| `value-set-unreferenced-inert` | a pack with an unreferenced set and without it | paired |
| `value-set-empty-collection-inert` | `"valueSets": []` with no reference, and the pack without the member | paired |
| `value-set-entry-annotations-inert` | entry annotations and descriptions present, absent, and changed | paired |
| `value-set-literal-object-entry` | a fact `{"valueSet": "priority-tiers"}` against an entry holding that literal | match |
| `value-set-literal-annotations-operand` | an inline `in` item `{"extensions": {"org.judgmentpack.annotations": {"tier": "x"}}}` against a fact holding exactly that object | match: the evaluation form acts on positions, not content |
| `value-set-unresolved-error` | one case each: an unresolved reference; a reference naming an id held only by an outcome | `pack-not-conformant` |
| `value-set-unresolved-precedence` | an unresolved reference with a malformed evidence document | `pack-not-conformant` (Core §8.4 order) |

No row is staged for the Core §13 numeric seam. As Core §13 says, a row cannot state an expected
result until that question closes.

**Static check.** A repository test computes the evaluation form of each paired fixture. It
asserts that the form equals its partner's or its baseline's, compared as JSON values (§5), and
that paired rows expect the same result. A pair that fails the check is a defect in the fixtures,
caught before any implementation runs them.

## Implementation

The rules divide into a schema, two semantic checks (duplicate set ids and resolution), two
optional advisories (repeated entry values and unreferenced sets) and one evaluation pre-pass
(resolving a reference to its array). Two plausible independent implementations:

- the project's reference runtime, which already validates and evaluates packs; and
- a second reader authored separately, for example a validator in another language that applies
  the fragments with a general-purpose JSON Schema validator and adds the two semantic checks and
  the resolution step.

The hardest part is the duplicate advisory (§2.4), which needs exact comparison of number literals.
An evaluator already needs that for Core §7.4's equality, and a tool that lacks it reports nothing
for the pairs it cannot decide. No conformance result depends on it.

One implementation exists, experimentally: a release of the project's reference runtime admits the
staged selector `0.4.0-draft`, with annotations, value sets and a filtered view, built on the
staged artifacts.

A second evaluator now exists in this repository:
[`tools/core_050_eval.py`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/tools/core_050_eval.py), with its test,
[`tests/test_core_050_eval.py`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/tests/test_core_050_eval.py); it was staged as
`tools/core_draft_eval.py` and renamed at the release. It was written from Core, the
staged delta and this record alone, without reading or running the reference runtime. Its authoring
vendor is the drafts' own, so it is a second reading of the text, not a different vendor's. It is a
test tool, not a product, and makes no conformance claim. It covers:

- admission as far as evaluation needs it: the carrier, the `base` profile, the staged schema
  applied by a general-purpose JSON Schema validator, and the semantic checks of Core §3.3 and the
  draft's §3.3, written fresh;
- the evaluation form, and Core §§7–8 over it, to the full disposition or error class;
- every staged evaluation row (each agrees with its expectation, and the held row agrees and stays
  held), every row they carry over with its selector replaced, and the equality of each of the 29
  pairs;
- every staged document case, and every released one they carry over: the result, and each
  semantic finding exactly. For a structural case it checks the result and the layer, not the
  code, since it maps no schema keyword to a code.

It supports `base` only. The 18 staged cases whose fixtures declare `extended` are checked to be
refused with `profile-unsupported`, not run. Its mutation check found rules of Core §§7–8 that no
evaluation row distinguishes, such as `suppress-rule`; its test states them as its own cases,
which are not conformance rows. Evidence bar item 3 is met in part ([Acceptance](#acceptance)).
The scratch check described under Evidence is not an implementation, and
neither is the evaluator the round-1 review wrote.

## Unresolved questions

The questions keep their numbers; those answered are listed after the open ones.

**2. More positions.** Annotations might also be wanted on the value-set object, on exceptions, on
evidence requirements or on sources, and vendor extensions on sets or entries (§2.2). Admitting a
position later is compatible, and removing one is not. This record admits only the positions the
issue names, and leaves the others open until someone asks for one. Deferring is safe: a later
selector that admits more positions only turns refused shapes into admitted ones, so a pack written
to this one holds none of them and its evaluation form is unchanged. The later record must extend
evaluation-form step 3 (§4.1) to every position it admits.

**3. Where the two value-set advisories live.** `JPS-VALUE-SET-UNREFERENCED` (§2.6) and
`JPS-VALUE-SET-DUPLICATE-VALUE` (§2.4) could join RFC 0027's report contract, or stay beside
`JPS-RULES-OVERLAP` in the document corpus's advisory vocabulary. That depends on RFC 0027's
disposition, which is open. Deferred: the two codes stay out of the next version's Core text, whose
§3.3.1 keeps only the reading of a reference as its set (§4.4), and they are added when RFC 0027 is
dispositioned. An advisory never changes conformance, so the deferral cannot break a pack. The
staged manifest lists the two codes as `advisoryCodes`, outside conformance, and no case states
them.

**Answered questions.**

- **1. The ceiling numbers.** Answered by the round-1 disposition: the six numbers of §7 are
  accepted as reasoned. They are reasoned from the intended use: short labels, a few keys, and
  lists the size of an enumerated code list. Measuring them needs packs that use the shapes, which
  cannot exist before the version opens. Raising a ceiling later is compatible and lowering one is
  not, so the numbers err low. The document byte limit is the only aggregate bound on annotations
  (§7). Evidence bar item 6 is met by this answer.
- **4. The reading of an `extensions` object.** Answered by the round-1 disposition (finding H3):
  the narrow reading, the `extensions` objects the schema defines as members of Core objects, as a
  change that takes effect under the next selector. It does not change how Core `0.3.0` reads
  (Compatibility). Deferring it was not safe, because the evaluation form needs it (§4.1). Core
  `0.3.0`'s ambiguity stays a known open point of the released text, and the released checker is
  unchanged. The staged cases `semantic-required-extension-in-operand` and
  `semantic-required-extension-in-entry-value` pin the reading.
- **5. Line feeds before the end anchor in Core's other patterns.** Answered by the maintainer
  (issue #308): closed in the next version beside this record, not left for a record of its own.
  The answer was added by the maintainer's decision after round 1 and was not part of the round-1
  review; the pull request that graduates this record has its own review, which covers it.
  An engine whose `$` matches before a final line feed admitted a vendor extension name such as
  `"com.example\n"` under Core `0.3.0`'s extension-name pattern, and a `localId` ending in a line
  feed under its local-identifier grammar, where an ECMA-262 engine refuses both, so two structural
  validators could disagree on one document. Under the next selector no local identifier and no
  extension name holds a line terminator, whatever an engine's anchors admit (the staged draft's §§5
  and 9). The local-identifier grammar gains the class an annotation key's `not` holds (§1.3). The
  extension-name grammar's reserved prefix moves from a lookahead, which RE2 cannot compile, into a
  `not` beside it that also holds that class, and the hyphen in its last class is escaped, which
  ECMA-262's `v` flag requires. Each `not` holds `"type": "string"`, as `annotationString`'s does,
  so a non-string fails `type` alone. The pack-version and decimal-operand grammars had the same
  property (`"1.0.0\n"`, `"1.5\n"`), and the maintainer closed it there too, with the same `not`. The
  definitions, by their place in the schema:

```json
{
  "properties/version": {
    "type": "string",
    "pattern": "^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$",
    "not": { "type": "string", "pattern": "[\u0000-\u001f\u007f-\u009f\u2028-\u202e]" }
  },
  "$defs/localId": {
    "type": "string",
    "pattern": "^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$",
    "not": { "type": "string", "pattern": "[\u0000-\u001f\u007f-\u009f\u2028-\u202e]" }
  },
  "$defs/decimalString": {
    "type": "string",
    "pattern": "^-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?$",
    "not": { "type": "string", "pattern": "[\u0000-\u001f\u007f-\u009f\u2028-\u202e]" }
  },
  "$defs/extensions": {
    "type": "object",
    "propertyNames": {
      "pattern": "^[a-z][a-z0-9]*(?:\\.[a-z][a-z0-9\\-]*)+$",
      "not": { "type": "string", "pattern": "^org\\.judgmentpack\\.|[\u0000-\u001f\u007f-\u009f\u2028-\u202e]" }
    },
    "additionalProperties": true
  },
  "$defs/metadata/properties/requiredExtensions/items": {
    "type": "string",
    "pattern": "^[a-z][a-z0-9]*(?:\\.[a-z][a-z0-9\\-]*)+$",
    "not": { "type": "string", "pattern": "^org\\.judgmentpack\\.|[\u0000-\u001f\u007f-\u009f\u2028-\u202e]" }
  }
}
```

A refusal by a pattern or by the `not` beside it takes the grammar's code (Codes). Swept over every
code point before, inside and after a value, and over values of more than one line, the four pattern
pairs admit exactly the same strings in every engine §1.7 lists: Python 3.12 `re`; ECMA-262 with the
`u` and with the `v` flag in Node 22; RE2 through Go 1.26; Perl 5.30; Java 11's `java.util.regex`;
and Ruby 2.7, whose `^` and `$` match at every line. Over that sweep they admit exactly what Core
`0.3.0`'s patterns admit under ECMA-262 in Unicode mode, as they must: a string the ECMA-262 grammar
admits holds only letters, digits, hyphens and full stops, which the class never matches. Findings
still compare as a set (Codes), because an ECMA-262 or an RE2 engine reports the pattern and the
`not` at one pointer, with one code, for a name that ends in a line feed. The staged cases
`structural-local-id-trailing-lf-id`, `structural-local-id-trailing-lf-reference`,
`structural-extension-name-trailing-lf`, `structural-extension-name-trailing-lf-annotated`,
`structural-required-extension-trailing-lf`, `structural-pack-version-trailing-lf` and
`structural-decimal-operand-trailing-lf` refuse one such value in each kind of position.

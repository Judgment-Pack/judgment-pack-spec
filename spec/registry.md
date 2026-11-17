# The registry

## Status

This document is a companion document of the Judgment Pack specification. It defines a registry
format: kind declarations, registries, overlays and references; their validation, and their
resolution for one environment; the YAML subset they are authored in; the facts documents and
facts contracts through which a pack judges registry entries; and the contract between a host and
the emitters that turn resolved registries into files.

This text is registry format `1.0.0`, status `proposed`. The version is this document's own: it is
not a Core `specVersion`, and no pack declares it. The companion is released on its own scoped tag,
`registry-v<major>.<minor>.<patch>`, beside Core and independent of `specVersion` (§13). No such
tag exists yet. Until one releases this text, it is normative for nothing, and no conformance claim
may cite it. Once a tag releases it, it is normative for the conformance classes of §15, and for
nothing else. Publication beside a Core release, on the site or in a bundle, releases nothing.

Its design records are [RFC 0034](../rfcs/0034-registry-profile.md) (the profile),
[RFC 0035](../rfcs/0035-registry-references.md) (references),
[RFC 0036](../rfcs/0036-registry-emitter-contract.md) (the emitter contract) and
[RFC 0037](../rfcs/0037-generated-facts-contracts.md) (facts contracts), accepted on 2026-11-16,
and they are informative. A fifth record of the same line,
[RFC 0038](../rfcs/0038-terraform-file-source.md), defines a source kind of the dialect, and its
text is in the dialect companion ([`dialect.md`](dialect.md) §4.5), where the dialect's source kinds
are defined. The maintainer accepted the five on one review round by a model from the drafting
vendor, with the different-vendor review of the interim review regime waived, as each record's
Acceptance section says. That is a same-vendor review, not a cross-vendor claim. Where this text
and a record differ, this text governs; §17 lists what this text settles that the records left
open, and what it leaves open.

Version `1.0.0` is proposed, and does not yet meet the stable bar its records set, for three
reasons:

- **Its rows are staged.** Its machine-readable code list and its hand-written, synthetic rows are
  staged under
  [`conformance/registry/1.0.0/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/registry/1.0.0)
  (§14). They are not a conformance corpus: no bundle carries them, the site does not serve them,
  and no claim may cite them.
- **Its schemas are not written.** The closed schemas of its documents, which a first release
  publishes under `schema/registry/1.0.0/`, do not exist yet.
- **One reader exists.** The reference runtime (Go) implements §§2 to 10. No second,
  independently written reader exists, and no implementation of §11's host or harness exists. The
  stable bar is two readers agreeing on every row (§15).

Core is unchanged by this document. A registry is not a pack, no Core document carries a registry
selector, and every pack Core accepts it still accepts, with the same results. A facts document of
§10 is an ordinary facts document to Core.

## 1. Terms

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT** and **MAY** have their BCP 14
meanings only in capitals.

- A **kind declaration** (§3) names a kind of entry and fixes the schema of its values, which of
  its members are secret references, entry references or overlayable, and its bounds.
- A **registry** (§4) lists environments, owners, the kind declarations it pins, its entries and
  its overlays. An **entry** is one value of one kind, with an id and an owner, that **applies** in
  some of the registry's environments.
- An **overlay** (§5) holds one environment's **patches**, each of which replaces values in one
  entry for that environment.
- **Resolution** (§8) gives one environment's **resolved registry**: every entry that applies there,
  with its patches applied.
- A **reference** (§6) is a string at a declared position: an **entry reference** names another
  entry, and a **secret reference** names one pinned version of a secret in a store.
- A **reader** validates registries and resolves them (§§2 to 8). An **importer** converts YAML to
  registry documents (§9). A **facts writer** maps resolved entries to facts documents and generates
  facts contracts (§10). An **emitter** is a program that reads a request and answers with files; a
  **host** runs it (§11). §15 makes these conformance classes.
- **Code-point order** compares two strings by their Unicode code points, first difference first.
  For the strings this document orders (member names, kind names, ids, pointers and the like), it is
  the order of their UTF-8 bytes. **JCS** is the RFC 8785 canonical form of a JSON value.
- A **pointer** is an RFC 6901 JSON Pointer. "At `p`" names the position a pointer `p` addresses;
  `""` is the whole document.

## 2. Documents

### 2.1 Documents and selectors

The companion defines these JSON documents. Each carries an exact format selector at its root. A
reader that does not support that exact selector MUST refuse the document. There are no aliases
and no compatible selectors.

| Document | Selector member | Value in `1.0.0` | Section |
| --- | --- | --- | --- |
| Kind declaration | `kindFormatVersion` | `"1.0.0"` | §3 |
| Registry | `registryFormatVersion` | `"1.0.0"` | §4 |
| Resolved registry, one environment | `resolvedFormatVersion` | `"1.0.0"` | §8 |
| Validation report | `reportFormatVersion` | `"1.0.0"` | §7.4 |
| Facts contract | `factsContractVersion` | `"1.0.0"` | §10.3 |
| Pack check report | `factsCheckFormatVersion` | `"1.0.0"` | §10.5 |
| Emitter manifest | `emitterManifestVersion` | `"1.0.0"` | §11.1 |
| Emit request | `emitRequestVersion` | `"1.0.0"` | §11.2 |
| Emit response | `emitResponseVersion` | `"1.0.0"` | §11.3 |
| Harness report | `harnessReportVersion` | `"1.0.0"` | §11.5 |

The pack check report has its own selector, and so does every other document a reader writes. The
facts document (§10.1) has none: it is a facts document of Core, and its bytes follow from a
resolved registry. A change to the facts document's bytes is therefore made only under a new
`resolvedFormatVersion`, never under the same one.

### 2.2 Admission

A reader admits a kind declaration, a registry, a facts contract and a resolved registry by these
steps, in order. Each refusal names its document (§7.3). Admission is validation's step 1 (§7.1).

1. **Size.** A document longer than its bound is refused, `REG-DOC-SIZE` at `""`, without being
   parsed. A reader that stops reading at the bound gives the same diagnostic.

   | Document | Bound |
   | --- | --- |
   | Kind declaration | 256 KiB (262 144 bytes) |
   | Registry | 8 MiB (8 388 608 bytes) |
   | Resolved registry | 8 MiB |
   | Facts contract | 8 MiB |
   | Nesting depth of any of these | 32 |

   Depth counts containers: the root object is at depth 1, and each object or array inside a
   container is one deeper than it.

2. **Parse.** The bytes are read as one JSON value (RFC 8259). One failure refuses the document,
   with no later step, and it is chosen in this order:
   1. bytes that are not UTF-8, anywhere in the input: `REG-DOC-JSON` at `""`;
   2. otherwise, reading the value from its first byte, whichever of these is reached first:
      a syntax error, a byte-order mark included (`REG-DOC-JSON` at `""`); an object or array
      that opens at depth 33 (`REG-DOC-DEPTH` at its pointer); or a member name that an earlier
      member of the same object has, compared as decoded, reached at the name and before its
      value is read (`REG-DOC-DUPLICATE` at the later member's pointer);
   3. otherwise, anything after the value but whitespace: `REG-DOC-JSON` at `""`;
   4. otherwise, a string whose escapes encode a lone surrogate: `REG-DOC-STRING` at `""`.

   So `{"a":1,"a":2,"b":}` is `REG-DOC-DUPLICATE`; `{"a":1,"a":2}` followed by the byte FF is
   `REG-DOC-JSON`; and a lone surrogate escape before a repeated member name is
   `REG-DOC-DUPLICATE`.

3. **Numbers.** Every number outside the number rule below is `REG-DOC-NUMBER` at its pointer. All
   of them are reported, and a document with one is refused.

4. **Selector.** A root that is not an object is `REG-DOC-SELECTOR` at `""`. A root whose selector
   member is missing, is not a string, or is not a selector the reader supports is
   `REG-DOC-SELECTOR` at the selector member's pointer, such as `/kindFormatVersion`.

**The number rule.** These documents are I-JSON (RFC 7493), and every number is one of these:

- a literal with no fraction and no exponent is an integer, and its magnitude is at most
  2^53 − 1 (9 007 199 254 740 991);
- any other literal is finite, and its exact decimal value equals the exact decimal value of the
  shortest decimal that reads back as the same IEEE 754 double. So `1.5`, `1.50`, `0.1`, `1e2` and
  `20.000` are admitted, and `0.10000000000000001` and `9007199254740993.0` are not.

No number is negative zero, in any form (`-0`, `-0.0`, `-0e0`), because its canonical form would be
`0`. Every other zero is admitted.

**Admitted form.** Admission replaces each number by its canonical form, and every later step
reads that form, never the literal as written. An integer literal is its own canonical form. Any
other literal is written as JCS writes the double it equals: `20.000` becomes `20`, `1.50` becomes
`1.5` and `1e2` becomes `100`. So trailing zeros after the point, and an exponent, never outlive
admission, and an admitted number is at most 25 bytes. The rule adds no bound beyond the number
rule above. A reader may refuse early a literal other than zero that has more than 17 significant
digits, counted once leading and trailing zeros are dropped, or whose leading significant digit's
exponent is outside −324 to 308, because no such literal meets it; it is `REG-DOC-NUMBER`
(step 3). So `1.00000000000000000000` is admitted as `1`, and `0e999999` as `0`.

A number is compared, and is canonical, by its value: `1.50` and `1.5` are the same number, and
both are written `1.5` in JCS.

### 2.3 Canonical form and digests

A document's identity bytes are its JCS bytes. A digest is `sha256:` followed by the 64 lowercase
hexadecimal digits of the SHA-256 of the bytes it names. A pin's digest (§4), a registry's digest
in a report and in a resolved registry, and a contract's digest are digests of JCS bytes.

The one digest of a document's bytes as supplied is a location's `kindDocument` (§7.3): it names a
kind declaration that may not parse, so it cannot be a digest of its canonical form.

Every document this companion writes (a resolved registry, a facts contract, a report, a request) is
written as its JCS bytes. A command line may end its output with one line feed, which is not part
of the document.

## 3. Kind declaration

```json
{
  "kindFormatVersion": "1.0.0",
  "id": "https://example.invalid/kinds/db-role",
  "version": "1.2.0",
  "kind": "db-role",
  "owner": "platform-data",
  "description": "A database role a service connects as.",
  "entryId": { "pattern": "^[a-z][a-z0-9-]{0,62}$" },
  "schema": {
    "type": "object",
    "required": ["database", "privileges"],
    "additionalProperties": false,
    "properties": {
      "database": { "type": "string", "maxLength": 63 },
      "privileges": { "type": "array", "items": { "enum": ["read", "write", "admin"] }, "uniqueItems": true },
      "password": { "type": "string" },
      "connectionLimit": { "type": "integer", "minimum": 1, "maximum": 500 }
    }
  },
  "secrets": ["/password"],
  "references": [ { "pointer": "/database", "kinds": ["database"] } ],
  "overlayable": ["/connectionLimit", "/password"],
  "bounds": { "maxEntries": 1000, "maxEntryBytes": 16384 }
}
```

### 3.1 Members

A kind declaration has these members and no other. `id`, `version`, `kind`, `owner` and `schema`
are required, besides the selector; the rest are optional. A member not listed is
`REG-KIND-UNKNOWN-MEMBER` at its pointer, a required member that is absent is
`REG-KIND-MISSING-MEMBER` at the pointer it would have, and a member that is not of its form is
`REG-KIND-FORM` at its pointer unless a code below is named.

| Member | Form |
| --- | --- |
| `id` | an absolute URI (RFC 3986 `absolute-URI`: a scheme and no fragment) of at most 2048 characters, with no white space |
| `version` | SemVer 2.0.0, with no build metadata |
| `kind` | the local name entries use, matching `^[a-z][a-z0-9-]{0,62}$` |
| `owner` | 1 to 128 characters from `A`–`Z`, `a`–`z`, `0`–`9` and `.`, `_`, `@`, `/`, `-` |
| `description` | a string, informative |
| `entryId` | an object of exactly one member, `pattern`, a string in the pattern subset (§3.4). A pattern outside the subset is `REG-KIND-PATTERN` at `/entryId/pattern`. The default is `^[a-z][a-z0-9-]{0,62}$` |
| `schema` | the schema every entry's resolved value satisfies, in the subset of §3.2 |
| `secrets` | an array of pointer patterns (§3.5): the positions that hold a secret reference (§6.3) |
| `references` | an array of objects of exactly two members, `pointer`, a pointer pattern, and `kinds`, a non-empty array of distinct kind names: the positions that hold an entry reference (§6.2) to an entry of one of those kinds |
| `overlayable` | an array of pointer patterns: the positions an overlay may set (§5). The default is empty |
| `bounds` | an object of `maxEntries`, an integer of at least 1 (default 10 000), and `maxEntryBytes`, an integer from 1 to 8 388 608 (default 65 536), each optional |
| `deprecated` | a boolean. A pinned kind that is deprecated is the warning `REG-KIND-DEPRECATED` (§7.1, step 4) |

The owner is an opaque identity. This companion gives it no meaning, and enforcement (who may change
a kind) is the repository's own review rule.

Inside these members, diagnostics are located as follows:

- in `secrets` and `overlayable`, an item that is not a string, or repeats an earlier item, is
  `REG-KIND-FORM` at the item; a string that is not a pointer pattern is `REG-KIND-POINTER-FORM` at
  the item;
- in `references`, an item that is not an object, or whose `pointer` is not a string, or whose
  `kinds` is not an array or is empty, is `REG-KIND-FORM` at the item; a member of an item other
  than `pointer` and `kinds` is `REG-KIND-UNKNOWN-MEMBER` at that member; a `kinds` item that is not
  a kind name, or repeats an earlier one, is `REG-KIND-FORM` at `/references/<i>/kinds`; a `pointer`
  that is not a pointer pattern is `REG-KIND-POINTER-FORM` at `/references/<i>/pointer`;
- in `bounds`, an unknown member is `REG-KIND-UNKNOWN-MEMBER`, and a value out of its range
  `REG-KIND-FORM`, each at that member.

A pointer pattern of `secrets`, `overlayable` or `references` that can match no position the schema
allows (§3.5) is `REG-KIND-POINTER-UNREACHABLE` at it. This is decided only when the schema
compiled with no diagnostic. A pattern of `secrets` that can match a position a pattern of
`references` can match is `REG-KIND-POINTER-CONFLICT` at `/secrets/<i>`.

A kind declaration with any diagnostic of step 1 or step 2 (§7.1) is **unusable**. A registry that
pins it is invalid, and its entries are not checked (§7.1).

### 3.2 The schema subset

A kind's `schema` is a JSON Schema 2020-12 schema restricted to the keywords below, and read with
JSON Schema's meaning, as §7.2 states it. Any other keyword, including `$schema`, `$id`,
`$dynamicRef`, `format`, `oneOf`, `if`, `then`, `else`, `patternProperties`, `dependentSchemas`
and `unevaluatedProperties`, is `REG-KIND-SCHEMA-KEYWORD` at its pointer. The keyword is not
ignored: it makes the declaration unusable.

| Group | Keyword | Form (otherwise `REG-KIND-SCHEMA-FORM`) |
| --- | --- | --- |
| Type | `type` | a type name, or a non-empty array of distinct type names, from `null`, `boolean`, `object`, `array`, `number`, `integer` and `string` |
| | `enum` | a non-empty array; more than 1 024 values is `REG-KIND-SCHEMA-LIMIT` |
| | `const` | any value |
| Objects | `properties` | an object whose members are subschemas |
| | `required` | an array of distinct strings |
| | `additionalProperties` | a subschema |
| | `minProperties`, `maxProperties` | a count |
| | `propertyNames` | an object of `pattern` and `maxLength` only (another keyword inside it is `REG-KIND-SCHEMA-KEYWORD`) |
| Arrays | `items` | a subschema (an array of subschemas is `REG-KIND-SCHEMA-FORM`) |
| | `minItems`, `maxItems` | a count |
| | `uniqueItems` | a boolean |
| Strings | `minLength`, `maxLength` | a count, in Unicode code points |
| | `pattern` | a string in the pattern subset (§3.4), otherwise `REG-KIND-PATTERN` |
| Numbers | `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum` | a number |
| Composition | `anyOf`, `allOf` | a non-empty array of subschemas; more than 16 is `REG-KIND-SCHEMA-LIMIT` |
| | `not` | a subschema |
| Definitions | `$defs` | at the root only, an object whose members are subschemas |
| | `$ref` | `#/$defs/<name>` (§3.3) |
| Annotations | `title`, `description` | a string |
| | `default` | any value |
| | `deprecated` | a boolean |
| | `examples` | an array |

A **subschema** is an object or a boolean. A **count** is a number with a non-negative integer value
of at most 2^53 − 1 (`2.0` is a count). `$defs` anywhere but the root is `REG-KIND-SCHEMA-FORM`.

**Annotations do not change validation.** `default` is applied neither by validation nor by
resolution; an emitter may read it. A value at a position whose subschema says
`"deprecated": true` is the warning `REG-VALUE-DEPRECATED` (§7.2), never an error.

### 3.3 Reading a schema: references, limits and order

**References.** A `$ref` is `#/$defs/` followed by a name: one reference token, non-empty, with
`~0` and `~1` decoded as RFC 6901 decodes them and no other `~` escape. Any other form is
`REG-KIND-SCHEMA-REF` at the `$ref`. A name that `$defs` does not define is `REG-KIND-SCHEMA-REF` at
each `$ref` that names it. `$ref` may sit beside other keywords, and applies with them.

**No cycles.** A definition from which a chain of `$ref` leads back to itself is a cycle. One
`REG-KIND-SCHEMA-REF` is reported for all the cycles of a schema, at the first `$ref`, in reading
order, that sits in a definition from which a cycle can be reached. The check covers every `$ref`
that names a defined name, whatever other diagnostic the schema has.

**Reading order.** A reader reads the definitions of `$defs` first, by name in code-point order, and
then the root schema. Within a schema it reads keywords in code-point order, the members of
`properties` in code-point order and the branches of a composition by index. The order fixes which
`$ref` is first and which subschemas count against the limit.

**Size limit.** A schema has at most 4 096 subschemas, counted in reading order: the root, every
definition, and every subschema of `properties`, `additionalProperties`, `items`, `anyOf`, `allOf`
and `not`, with `propertyNames` counting as one. The 4 097th is `REG-KIND-SCHEMA-LIMIT` at
`/schema`, and no later subschema is read. A composition of more than 16 branches is
`REG-KIND-SCHEMA-LIMIT` at the keyword, and its branches are not read.

**Expanded size.** A schema's expanded size is also at most 4 096. It counts the subschemas that
validation can visit at one position: the root schema and its subschemas as the size limit counts
them, but without the members of `$defs`. Instead, each `$ref` also counts the expanded size of the
definition it names, every time it is reached. A definition that no `$ref` reaches is not counted
here, since the size limit already holds it. So a chain of definitions that each name the next one sixteen times is refused,
even though it is small as written. A reader computes each definition's expanded size once, and
may stop counting past 4 096. A schema over the bound is `REG-KIND-SCHEMA-LIMIT` at `/schema`.
The check runs only when the schema has no other error.

### 3.4 The pattern subset

`pattern`, `propertyNames.pattern` and `entryId.pattern` use a regular-expression subset that has
one meaning in RE2, ECMAScript (with the `u` flag) and Python's `re`. A pattern outside it is
`REG-KIND-PATTERN` at its pointer.

A pattern is at most 256 code points. It is a sequence of these, and nothing else:

- **literal code points**, other than `\`, `.`, `^`, `$`, `|`, `?`, `*`, `+`, `(`, `)`, `[`, `]`,
  `{` and `}`;
- **escapes**: `\.` `\/` `\\` `\(` `\)` `\[` `\]` `\{` `\}` `\*` `\+` `\?` `\|` `\^` `\$`, and `\d`;
  every other escape is refused, among them `\w`, `\s`, `\b`, `\p`, a back-reference such as `\1`,
  and `\-` outside a class;
- **`.`**;
- **`^`** only as the first character and **`$`** only as the last;
- **groups** `( … )`, balanced, whose capture is not relied on. `(?` begins no group: named groups,
  look-around, flags and every other `(?` form are refused;
- **`|`**;
- **quantifiers** `*`, `+`, `?`, `{n}`, `{n,}` and `{n,m}`, each after an atom (a literal, an
  escape, `.`, a class or a group) and never after another quantifier, so lazy and possessive forms
  are refused. `n` and `m` are 1 to 4 digits with no leading zero (or `0`), and `n ≤ m ≤ 1000`. A `{`
  that does not begin a quantifier, and a `}` or `]` that ends nothing, are refused. Along every
  chain of quantifiers nested through groups, the product of their counts is at most 1 000:
  `{n,m}` counts m, `{n}` and `{n,}` count n, and `*`, `+`, `?` and a count of 0 count 1. A chain
  may start at any quantifier. `{0}` and `{0,0}` only stop a chain that reaches them from above:
  the chains that start below them are still checked. So `(a{32}){32}` and `((a{2}){501}){0}`
  are refused, and `(a{10}){100}` and `((a{2}){500}){0}` are admitted;
- **bracket classes** `[ … ]`, with an optional leading `^`, holding literal code points, the escapes
  above, `\-`, and ranges `a-b` whose ends are a literal or an escaped code point and whose first
  end is not greater than its second. A class is not empty (`[]` and `[^]` are refused), holds no
  unescaped `[`, holds none of `--`, `&&`, `~~` or `||`, uses `\d` only alone and never as a range
  end, and is closed.

A pattern that ends with `\` is refused.

**One meaning.** A reader translates the pattern for its engine so that it has these meanings:

- `.` matches any code point except U+000A, U+000D, U+2028 and U+2029;
- `$` matches only at the end of the string (in Python, `\Z`; in RE2, `\z`);
- `\d` is `[0-9]`;
- a pattern matches when it matches anywhere in the string, so anchoring is the author's.

**Linear time.** A reader MUST match a pattern in time linear in the input, for example with an
automaton. A backtracking engine is not conformant on adversarial input. A pattern within the subset
that a reader's engine cannot compile within its own limits is not pinned by this version (§17).

**Program size.** A pattern's size is counted on the pattern as written, by these rules:

- each literal code point, escape, `.`, class, `^` and `$` counts 1;
- a group counts its content, since its capture is not relied on;
- `*` counts 2 plus its atom, and `+` and `?` count 1 plus their atom;
- `{n}` counts n times its atom; `{n,}` counts 1 plus n times its atom (`{0,}` counts as `*`);
  `{n,m}` counts m times its atom plus m − n;
- a sequence counts the sum of its parts, and an alternation of k alternatives counts the sum of
  its alternatives plus k − 1;
- every construct counts at least 1, an empty alternative and `x{0}` included.

Size is counted only for a pattern within the subset, and a pattern has one code: one outside
the subset is `REG-KIND-PATTERN` alone, whatever its size. A pattern of size over 4 096 is
`REG-KIND-PATTERN-LIMIT` at its pointer. A kind's patterns are
also held together to 65 536. They are counted with `entryId.pattern` first and then the
schema's patterns in reading order (§3.3); the default `entryId` pattern, when `entryId` is absent,
is not counted. The pattern that
would take the total past 65 536 is `REG-KIND-PATTERN-LIMIT` at its pointer. A refused pattern
is not counted, so each later pattern is judged against the patterns admitted before it. The
size bounds what a linear-time matcher builds: `{n,m}` makes m copies of its atom, so without a
bound one pattern of 256 code points could compile to a quarter of a million instructions.

### 3.5 Pointer patterns

A pointer pattern is an RFC 6901 pointer whose reference tokens may be `*`, which matches any member
name or any array index at that position. A literal member named `*` is written `~2`, an escape this
companion adds; `~0` and `~1` keep their RFC 6901 meanings, and every other `~` escape is refused. A
pattern begins with `/` (`""` is refused) and is at most 512 bytes of UTF-8, counted as written,
escapes included. A pattern outside these rules is
`REG-KIND-POINTER-FORM`.

A pattern **matches** a concrete pointer of the same number of tokens when each token is `*` or
equals the concrete token after unescaping. `/grants/*/role` matches `/grants/0/role`.

**Reachability.** A pattern is reachable when some position the schema allows matches it. A reader
decides this from the schema, never from values, by following each token from the root:

- through `$ref`, and through every branch of `allOf` and `anyOf` (a token is reachable if any branch
  reaches it); `not` is not followed;
- at an object position, a literal token is reachable through its `properties` member, or else
  through `additionalProperties` unless that is `false`; `*` is reachable when either is;
- at an array position, a token that is `*` or an array index is reachable through `items`;
- a position whose `type` allows neither objects nor arrays has no token below it; one with no
  `type` allows both;
- a subschema that is `false` reaches nothing, and an absent `additionalProperties` or `items`, or
  one that is `true`, reaches every token below it.

An array index token is a decimal of at most 9 digits with no leading zero (or `0`).

### 3.6 Kind versions

A kind's `version` follows these rules, so that a range over kind versions (§11.1) means something:

- **A patch version** changes only annotations (§3.2) and `description`. Every value has the same
  diagnostics under both versions.
- **A minor version** only widens: every value valid under the previous version is valid under the
  new one. It may add optional members, widen an `enum`, relax a bound, add `overlayable` patterns,
  raise `bounds` and set `deprecated`. It MUST NOT change `kind`, `entryId`, `secrets` or
  `references`.
- **Anything else is a new major version.**

Validation checks a registry against the exact declarations it pins, and does not compare two
versions of a kind. A tool that compares them applies these rules. A consumer that reads a kind by
range MUST accept members it does not know, because a minor version may add them.

## 4. Registry document

```json
{
  "registryFormatVersion": "1.0.0",
  "id": "https://example.invalid/registries/platform",
  "version": "4.0.0",
  "environments": ["dev", "prod"],
  "owners": ["platform-data", "team-billing"],
  "kinds": [
    { "kind": "database", "id": "https://example.invalid/kinds/database", "version": "1.0.0", "digest": "sha256:…" },
    { "kind": "db-role", "id": "https://example.invalid/kinds/db-role", "version": "1.2.0", "digest": "sha256:…" }
  ],
  "entries": [
    { "kind": "database", "id": "billing", "owner": "platform-data", "value": { "engine": "postgres" } },
    { "kind": "db-role", "id": "billing-api", "owner": "team-billing",
      "value": { "database": "entry:database/billing", "privileges": ["read", "write"],
                 "password": "secret:gcp-sm:projects/example-dev/secrets/billing-db/versions/3" } },
    { "kind": "db-role", "id": "billing-backfill", "owner": "team-billing", "environments": ["dev"],
      "value": { "database": "entry:database/billing", "privileges": ["read"] } }
  ],
  "overlays": [
    { "environment": "prod", "patches": [
      { "kind": "db-role", "id": "billing-api",
        "set": { "/password": "secret:gcp-sm:projects/example-prod/secrets/billing-db/versions/7",
                 "/connectionLimit": 120 } } ] }
  ],
  "secretScopes": { "dev": { "gcp-sm": ["example-dev"] }, "prod": { "gcp-sm": ["example-prod"] } }
}
```

A registry has these members and no other. `overlays` and `secretScopes` are optional, and the rest
are required, besides the selector.

| Member | Form |
| --- | --- |
| `id` | an absolute URI, as a kind's `id` (§3.1) |
| `version` | SemVer 2.0.0, with no build metadata |
| `environments` | 1 to 32 distinct names, each matching `^[a-z][a-z0-9-]{0,31}$` |
| `owners` | a non-empty array of distinct owners, each of a kind owner's grammar (§3.1): the closed list of parties entries may name |
| `kinds` | an array of **pins**, each an object of exactly `kind` (a kind name), `id` (an absolute URI), `version` (SemVer, no build metadata) and `digest` (§2.3): the kind declarations the registry uses |
| `entries` | an array of entries |
| `overlays` | an array of overlays (§5) |
| `secretScopes` | the projects each environment's secrets come from (§6.4) |

An **entry** is an object of exactly `kind`, `id`, `owner` and `value`, and optionally
`environments`:

- `kind` is a kind name, and `owner` an owner;
- `id` is a string; its grammar is checked at step 5 (§7.1);
- `environments` is a non-empty array of distinct strings, the environments the entry applies in.
  Without it, the entry applies in every environment of the registry;
- `value` is any JSON value.

A reader is given the kind declarations apart from the registry, and matches each pin to a
declaration by its digest. A declaration that is missing, or that does not match, is a refusal and
never a fetch.

**Canonical order.** `kinds` is sorted by `kind`, and `entries` by `kind` and then by `id`, each in
code-point order. An importer writes this order (§9), and a registry out of it is invalid, so two
registries that say the same thing have the same bytes.

**Diagnostics of the shape.** They are validation's step 3 (§7.1), each in document `registry`:

- A member of the registry that is not listed is `REG-REGISTRY-UNKNOWN-MEMBER` at it, and a
  required one that is absent is `REG-REGISTRY-MISSING-MEMBER` at the pointer it would have. Either
  stops validation before any other member is read.
- `id`, `version`, `entries` or `overlays` not of its form is `REG-REGISTRY-FORM` at that member.
- `environments` or `owners` that is not a non-empty array, or `environments` of more than 32, is
  `REG-REGISTRY-FORM` at it. An item that is not a string of its grammar is `REG-REGISTRY-FORM` at the
  item, and an item equal to an earlier one is `REG-REGISTRY-DUPLICATE` at the item.
- `kinds` that is not an array is `REG-REGISTRY-FORM` at it. A pin that is not an object, or whose
  members are not of their forms, is `REG-REGISTRY-FORM` at the pin, and a member of a pin that is
  not listed is `REG-REGISTRY-UNKNOWN-MEMBER` at that member.
- A diagnostic in this list so far stops validation after step 3. `secretScopes` is read only when
  none was given (§6.4), and its form diagnostics stop validation too.
- An entry that is not an object is `REG-REGISTRY-FORM` at the entry. A member of an entry that is
  not listed is `REG-REGISTRY-UNKNOWN-MEMBER` at it, and a required one that is absent
  `REG-REGISTRY-MISSING-MEMBER` at the pointer it would have. Otherwise a `kind` or `owner` not of
  its grammar, an `id` that is not a string, or an `environments` that is not a non-empty array, is
  `REG-REGISTRY-FORM` at that member, and an `environments` item that is not a string, or repeats an
  earlier one, is `REG-REGISTRY-FORM` at the item. An entry with any of these is **dropped**: it is
  not an entry for any later step, and validation goes on.
- Among the pins, the first whose `kind` is less than the `kind` of the pin before it is
  `REG-REGISTRY-ORDER` at that pin. Among the entries that were not dropped, the first whose `kind`
  and `id` are less than those of the entry before it is `REG-REGISTRY-ORDER` at that entry. Each is
  reported at most once, and neither stops validation.

## 5. Overlays

An overlay is an object of exactly `environment`, an environment of the registry, and `patches`,
an array of patches. A patch is an object of exactly `kind`, `id` and `set`. `set` is an object whose
member names are pointers into the entry's value, and whose values replace the values at those
pointers. Set keys are plain RFC 6901 pointers: `~2` is not an escape in them.

**Rules.**

- **At most one overlay per environment.**
- **A patch never adds an entry**, and an entry has at most one patch per overlay. An entry that
  exists in some environments says so with its `environments` member.
- **The entry must apply.** A patch for an entry that does not apply in its overlay's environment is
  an error, because it can never take effect.
- **The target must be overlayable and reachable.** A set key matches one of the kind's
  `overlayable` patterns (§3.5), and addresses a member or an array element that exists in the
  entry's value, or a member that the schema declares in a `properties` keyword at an object
  position that exists in the value (through `$ref`, `allOf` and `anyOf`, as §3.5 follows them).
- **No deletions.** A set value of `null` would delete, and is refused: a member that varies by
  being absent is expressed in the base value and the kind's schema.
- **Order does not matter.** Within one patch, no set key is a prefix of another (in reference
  tokens), so the order in which a patch's values are applied cannot change the result.

**Diagnostics.** They are validation's step 6 (§7.1), each in document `registry`. A diagnostic
that names its entry does so only when the patch's `kind` is a kind name and its `id` is of the
entry-id grammar (§6.2).

- An overlay that is not an object of exactly its two members, of their forms, is `REG-REGISTRY-FORM`
  at the overlay. An overlay whose environment is not declared is `REG-OVERLAY-ENVIRONMENT`, and one
  whose environment an earlier overlay has is `REG-OVERLAY-DUPLICATE`, each at
  `/overlays/<i>/environment`. Such an overlay's patches are not read.
- A patch that is not an object of exactly its three members, of their forms, is `REG-REGISTRY-FORM`
  at the patch, with no entry named.
- A patch for an entry an earlier patch of the same overlay names is `REG-OVERLAY-PATCH-DUPLICATE`
  at the later patch, which is not read.
- A patch for an entry the registry does not have (among entries step 3 did not drop) is
  `REG-OVERLAY-ENTRY-MISSING` at the patch. A patch for an entry that failed step 5 is not read, and
  has no diagnostic. A patch for an entry that does not apply in the environment is
  `REG-OVERLAY-ENTRY-ABSENT` at the patch.
- Otherwise the set keys are read in code-point order. A key that is not a pointer is
  `REG-OVERLAY-POINTER`, and a key no `overlayable` pattern matches `REG-OVERLAY-NOT-OVERLAYABLE`,
  each at `.../set`: a location never spells a key the kind does not declare overlayable. Otherwise
  a key whose target is not reachable is `REG-OVERLAY-TARGET`, and else a key whose value is `null`
  is `REG-OVERLAY-NULL`, each at `.../set/<the key, escaped as a reference token>`. A key that passed
  these checks and is a prefix of a key read before it, or has one as its prefix, is
  `REG-OVERLAY-PREFIX` at the later key.

A patch with any diagnostic, and an entry with two patches in one overlay, **fail** their entry in
that environment: the entry is not checked by step 7 or by the size bound of step 8 in that
environment, and stays checked in every other.

## 6. References

### 6.1 Where references are read

A string is a reference only at a position its kind's `references` or `secrets` patterns match
(§3.5). Anywhere else, a string that begins with `entry:` or `secret:` is an ordinary string: no
escaping is needed, and no reader guesses. At a `references` position the value MUST be an entry
reference, and at a `secrets` position a secret reference. A kind in which one position can be
matched by both is invalid (`REG-KIND-POINTER-CONFLICT`, §3.1).

The positions a pattern matches in a value are the positions that exist in it. A pattern that
matches nothing in an entry's value, as for an optional member that is absent, checks nothing
there.

### 6.2 Entry references

```
entry-ref = "entry:" kind "/" entry-id [ "#" pointer ]
kind      = <a kind name, §3.1>
entry-id  = 1*128( %x21-7E except "/" and "#" )
pointer   = <an RFC 6901 JSON Pointer of at most 512 code points, as written, possibly "">
```

In each environment in which the referring entry is checked (step 7), the first of these that
applies is reported, at the reference's position, in document `value`:

1. **`REF-ENTRY-FORM`**: the value is not a string of the grammar.
2. **`REF-ENTRY-KIND`**: `kind` is not one of the kinds of the pattern that matched the position.
3. **`REF-ENTRY-MISSING`**: the registry has no entry `(kind, entry-id)` among the entries step 3
   did not drop.
4. **`REF-ENTRY-ABSENT-IN-ENVIRONMENT`**: the entry does not apply in the environment.
5. **`REF-ENTRY-POINTER`**: the reference has a `#pointer`, the target was checked in this
   environment by step 7, and the pointer addresses nothing in the target's resolved value there. A
   target not checked there (it failed step 5, or its patch failed) gives no diagnostic at this
   step. `""` addresses the whole value.

A reference may name its own entry, and references may form cycles, because nothing is
substituted.

### 6.3 Secret references

```
secret-ref = "secret:" store ":" locator
store      = "gcp-sm"        ; the one store of format 1.0.0, Google Cloud Secret Manager
locator    = "projects/" project "/secrets/" name "/versions/" version
project    = <a project id, matching ^[a-z][a-z0-9-]{4,28}[a-z0-9]$>
name       = 1*255( ALPHA / DIGIT / "_" / "-" )
version    = %x31-39 *8DIGIT ; a positive integer of at most 9 digits, no leading zero
```

A value at a secret position that is not a secret reference is given exactly one code, by the first
of these that applies, at its position in document `value`:

1. **`REF-SECRET-FORM`**: the value is not a string, does not begin with `secret:`, or has no `:`
   after the store.
2. **`REF-SECRET-STORE`**: the store is not `gcp-sm` (an empty store included).
3. **`REF-SECRET-FORM`**: the locator does not have the six `/`-separated segments
   `projects/<p>/secrets/<n>/versions/<v>`.
4. **`REF-SECRET-PIN`**: `<n>` matches `name`, `<v>` is not empty, and either `<v>` holds a
   character other than a digit (`latest`, or any alias), or `<p>` is all digits (a project number,
   which is not the project id a scope compares).
5. **`REF-SECRET-FORM`**: anything else the grammar does not match. This includes a version of `0`,
   a version with a leading zero, a version of ten or more digits, and a malformed project id.

So "not pinned" is kept for a reference that names a secret correctly but floats, or names its
project by number. A version out of range is a form error. Another store is added only by a later
minor format version, with its own locator grammar and pin rule, and a reader of `1.0.0` refuses a
store it does not know.

### 6.4 Secret scopes

`secretScopes` is an object with one member per environment of the registry, and no other. Each
member is an object whose members are stores (`gcp-sm` alone in `1.0.0`), and each store's value is
an array of distinct project ids: the projects that environment's secrets come from.

**Form.** `REF-SECRET-SCOPE-FORM`, in document `registry`, is reported:

- at `/secretScopes`, when it is not an object, or lacks a member for an environment;
- at `/secretScopes/<environment>`, for a member that names no environment of the registry, or that
  is not an object;
- at `/secretScopes/<environment>/<store>`, for a store that is not `gcp-sm`, or whose value is not an
  array;
- at `/secretScopes/<environment>/<store>/<i>`, for an item that is not a project id, or repeats an
  earlier item.

A form diagnostic stops validation after step 3, as the shape's do.

**Sharing.** No project is listed for two environments. Reading the environments in code-point
order, a project listed for an environment read earlier is `REF-SECRET-SCOPE-SHARED` at the later
listing, `/secretScopes/<environment>/<store>/<i>`. It does not stop validation. Production and
development therefore never share a project.

**Scope.** In step 7, a secret reference that passed §6.3, in an entry's resolved value for
environment `e`, MUST name a project listed for `e` and its store, or it is `REF-SECRET-SCOPE` at its
position. In a registry without `secretScopes`, every such reference is instead the warning
`REF-SECRET-UNSCOPED`. A registry that wants this as an error declares scopes.

A secret that must differ by environment is listed in its kind's `overlayable`, and each
environment's overlay sets its own reference.

### 6.5 What nothing does

- **Validation, resolution, the facts writer and emitters never contact a secret store.** They never
  check that a secret or a version exists, and never read a secret's value. Existence is the
  platform's concern at deployment, where the credentials are.
- **No reference is replaced by what it refers to.** A resolved registry carries every reference as
  written. Only the facts document (§10.1) maps them, and never to a secret's value.
- **A diagnostic names the location of a bad reference, never its text.** The reference is not a
  secret, but it names infrastructure, and a report is often posted in a CI log.

## 7. Validation

### 7.1 The steps

Validation of a registry, given the kind declarations supplied with it, runs these steps in this
order. Each step runs only on the documents, declarations and entries that passed the steps before
it, and reports every applicable diagnostic of its own, not only the first. A registry is **valid**
when validation finds no error.

1. **Admission** (§2.2), of the registry and of each kind declaration supplied. A declaration that
   is refused is not a declaration for any later step. A registry that is refused ends validation.
   Two supplied declarations whose JCS bytes are equal are one declaration: it is read once, and
   its diagnostics name the copy whose `kindDocument`, the digest of its bytes as supplied (§2.3),
   is least in code-point order.
2. **Kind declarations** (§3): each one's members, its schema (§§3.2 and 3.3), its patterns (§3.4)
   and its pointer patterns (§3.5).
3. **Registry shape** (§4), and the form and sharing of `secretScopes` (§6.4). A diagnostic §4 or
   §6.4 says stops validation ends it here. Entries that §4 drops are not entries for any later
   step.
4. **Kind pins**, in pin order, each at the pin (`/kinds/<i>`, with `kind` named):
   - a pin whose `kind` an earlier pin has is `REG-REGISTRY-DUPLICATE`, and is not otherwise read;
   - a pin whose digest no supplied declaration has (among those step 1 admitted) is
     `REG-PIN-MISSING`;
   - a pin whose declaration is unusable (§3.1) has no diagnostic of its own: the declaration's
     say why;
   - a pin whose declaration has another `kind`, `id` or `version` than the pin is
     `REG-PIN-MISMATCH`;
   - a pin whose declaration is deprecated is the warning `REG-KIND-DEPRECATED`.

   A pin that has none of the errors **pins** its declaration, and its kind is **usable**. Each
   supplied declaration that is usable and whose digest no pin has is the warning `REG-PIN-UNPINNED`, at
   `{"document": "kind", "kindDocument": …, "kind": …, "pointer": ""}`.
5. **Entries**, each at its own member under `/entries/<i>`:
   - an entry whose kind no pin names is `REG-ENTRY-KIND` at `.../kind`; an entry whose kind's pin
     is not usable is not checked, and has no diagnostic;
   - otherwise, every one of these that applies: an id that fails the kind's `entryId` pattern or
     the entry-id grammar (§6.2) is `REG-ENTRY-ID` at `.../id`, with no entry named; an entry whose
     kind and id an earlier entry has is `REG-ENTRY-DUPLICATE` at `.../id`; an owner not in
     `owners` is `REG-ENTRY-OWNER` at `.../owner`; and an `environments` item the registry does
     not declare is `REG-ENTRY-ENVIRONMENT` at `.../environments/<j>`.

   An entry with none of these **passes**.
6. **Overlays** (§5).
7. **Per environment**, in the order of `environments`. In environment `e`, the entries checked
   are those that passed step 5, apply in `e`, and whose patch for `e` did not fail. Each one's
   resolved value (§8) is checked, in entry order, against:
   - its kind's schema (§7.2);
   - its kind's `secrets` (§§6.3 and 6.4);
   - its kind's `references` (§6.2).
8. **Bounds.**
   - A usable kind with more entries than its `maxEntries` (counting every entry of that kind
     step 3 did not drop) is `REG-BOUND-ENTRIES` at its pin.
   - An entry checked in step 7 whose resolved value's JCS bytes are longer than its kind's
     `maxEntryBytes` is `REG-BOUND-ENTRY-BYTES` at
     `{"document": "value", "entry": …, "environment": e, "pointer": ""}`.
   - An environment whose resolved registry (§8) would be longer than 8 MiB is `REG-DOC-SIZE`, and
     one that would nest deeper than 32 is `REG-DOC-DEPTH`, each at
     `{"document": "registry", "environment": e, "pointer": ""}`: an overlay can set a value at a
     depth the registry itself does not reach.

### 7.2 Value validation

A resolved value is checked against its kind's schema by JSON Schema 2020-12's meaning of each
keyword of the subset, with numbers compared by their exact value. Every keyword of a schema is
checked independently, and each failure is reported at the pointer of the value it is about, in
document `value`:

| Keyword | Diagnostic, when the value fails it |
| --- | --- |
| a `false` schema | `REG-VALUE-TYPE` |
| `type` | `REG-VALUE-TYPE`; `integer` is a number with an integer value, so `2.0` is an integer |
| `enum`, `const` | `REG-VALUE-ENUM`, `REG-VALUE-CONST`, by JSON equality (numbers by value, objects regardless of member order) |
| `required` | `REG-VALUE-REQUIRED`, once per absent member, at the pointer the member would have |
| `minProperties`, `maxProperties` | `REG-VALUE-PROPERTY-COUNT`, at the object |
| `propertyNames` | `REG-VALUE-PROPERTY-NAME`, at the member whose name fails; `maxLength` counts code points |
| `additionalProperties` | for a member that `properties` does not name: `REG-VALUE-ADDITIONAL` at the member when it is `false`, and otherwise the member is checked against it |
| `properties`, `items` | each member it names that is present, and each item, is checked against its subschema |
| `minItems`, `maxItems` | `REG-VALUE-ITEM-COUNT`, at the array |
| `uniqueItems` | `REG-VALUE-UNIQUE`, once, at the array |
| `minLength`, `maxLength` | `REG-VALUE-LENGTH`, counting code points |
| `pattern` | `REG-VALUE-PATTERN` (§3.4) |
| `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum` | `REG-VALUE-RANGE` |
| `allOf` | every branch is checked, and each branch's diagnostics are reported |
| `anyOf` | when some branch holds (has no error), the diagnostics of the first that holds, which are warnings only, are reported; when none holds, one `REG-VALUE-ANY-OF` at the value, and none of the branches' own |
| `not` | `REG-VALUE-NOT` when the inner schema holds |
| `$ref` | the definition is checked, beside the schema's other keywords |
| `deprecated: true` | the warning `REG-VALUE-DEPRECATED`, at a value that is present |

A keyword that does not apply to the value's type (`maxLength` on a number, say) holds.

**Work bound.** The bounds of §3.3, §3.4 and §7.1 keep each check finite, but a registry of many
large values can still make value validation costly. A reader MAY stop value validation once its
work over the registry passes a bound of its own. It then reports `REG-BOUND-VALIDATION-WORK`, an
error, at the value it stopped at (pointer `""` in document `value`), and checks neither that value nor any it reaches later against
its schema. The reference
runtime counts in units of about one schema node visited, and stops past 67 108 864 (2^26). Every
value costs one unit per 16 bytes of its canonical form. A value equal to one already checked
against the same kind declaration (by digest) costs nothing more. Every other step still
runs. A registry that passes one reader's bound and not another's is not pinned by this version
(§17). A conformance row stays well within the reference runtime's bound.

### 7.3 Locations

A diagnostic's `location` is an object of these members, in this order of comparison:

| Member | Form | Present |
| --- | --- | --- |
| `document` | `registry`, `kind`, `value`, `yaml`, `facts`, `contract` or `pack` | always |
| `kindDocument` | the digest of a kind declaration's bytes as supplied (§2.3) | on every diagnostic about a supplied kind declaration, except `REG-DOC-SIZE` for one that was not read whole |
| `kind` | a kind name | on a pin's diagnostic of step 4 or 8, on `REG-PIN-UNPINNED`, on a facts contract's (§10), and on every diagnostic of step 2 for a declaration whose `kind` member is a kind name |
| `entry` | `{"kind", "id"}` | on a diagnostic about one entry, when the entry's kind is a kind name and its id is of the entry-id grammar (§6.2) |
| `environment` | an environment | on a diagnostic of one environment: of step 7, of step 8's sizes, and of the facts writer |
| `pointer` | a pointer into `document` | always; `""` for the whole document |
| `line`, `column` | integers from 1, counting code points | in document `yaml` only, where `pointer` is always `""` |

In document `value`, the pointer is into the entry's resolved value in `environment`. In document
`kind`, it is into the declaration named by `kindDocument`.

A location never holds a value from a document beyond these identifiers: a pointer is built from
member names and indices of the document, and the identifiers are the document's own names for its
kinds, entries and environments.

### 7.4 The report

```json
{
  "reportFormatVersion": "1.0.0",
  "valid": false,
  "registry": { "digest": "sha256:…" },
  "diagnostics": [
    { "code": "REG-ENTRY-OWNER", "severity": "error", "message": "…",
      "location": { "document": "registry", "entry": { "kind": "db-role", "id": "billing-api" }, "pointer": "/entries/1/owner" } }
  ]
}
```

The validation report holds:

- `valid`: `true` exactly when validation found no error;
- `registry`: the registry's digest (§2.3), present once step 3 passed and absent otherwise;
- `diagnostics`: each with `code`, from §12's closed list; `severity`, `error` or `warning`, the
  code's; `location` (§7.3); and `message`, a fixed text per code that carries no value from any
  document.

**Order.** The diagnostics are sorted by `location.document`, `location.kindDocument`,
`location.kind`, `location.entry.kind`, `location.entry.id`, `location.environment`,
`location.pointer`, `location.line`, `location.column` and then `code`, each string compared in
code-point order and each integer by value, with an absent member sorting as `""` or `0`.
Diagnostics equal in all of these are one diagnostic, reported once.

**Bound.** A report lists at most the first 1 000 distinct diagnostics in this order. When
validation found more, the report lists those 1 000 and then one more, the warning
`REG-REPORT-TRUNCATED`, at `{"document": "registry", "pointer": ""}`, which is the one diagnostic
out of order. `valid` is decided on every diagnostic found, whether listed or not, so a truncated
report may list no error and still say `false`.

The same bound holds wherever a facts contract is read (§10). Its diagnostics are capped at
1 000 in this order, and the `REG-REPORT-TRUNCATED` that follows them is at
`{"document": "contract", "pointer": ""}`.

**No values.** A diagnostic carries no value from any document: no member value, no reference, and
no pattern text. A reader MUST NOT add one in any member of a diagnostic, and the message is never
compared.

**Agreement.** Two readers agree on a registry and its declarations when their reports are equal
with every `message` removed. Messages are informative.

## 8. Resolution

Resolution of a valid registry for one of its environments `e` gives a resolved registry:

```json
{
  "resolvedFormatVersion": "1.0.0",
  "registry": { "id": "https://example.invalid/registries/platform", "version": "4.0.0", "digest": "sha256:…" },
  "environment": "prod",
  "kinds": [ { "kind": "database", "id": "…", "version": "1.0.0", "digest": "sha256:…" },
             { "kind": "db-role", "id": "…", "version": "1.2.0", "digest": "sha256:…" } ],
  "entries": [
    { "kind": "database", "id": "billing", "owner": "platform-data", "value": { "engine": "postgres" } },
    { "kind": "db-role", "id": "billing-api", "owner": "team-billing",
      "value": { "database": "entry:database/billing", "privileges": ["read", "write"],
                 "password": "secret:gcp-sm:projects/example-prod/secrets/billing-db/versions/7",
                 "connectionLimit": 120 } }
  ]
}
```

**Procedure.**

- `registry` is the registry's `id`, `version` and digest (§2.3), and `environment` is `e`.
- `kinds` is every pin of the registry, as written, in its order.
- `entries` has one item per entry that applies in `e`, in the registry's order, of exactly `kind`,
  `id`, `owner` and `value`. Its `value` is the entry's value with, for each set key of `e`'s patch
  for the entry, the value at that pointer replaced, or the member added, by the set value. An entry
  that does not apply in `e` is omitted, and so is its `environments` member from every entry.
- The document is written as its JCS bytes.

A registry that is not valid is not resolved. A reader MUST NOT write a resolved registry for one.

**What resolution does not do.** It applies no default. It replaces no reference with what it refers
to, and fetches no secret.

The resolved registry is the only input an emitter reads (§11). Its `registry.digest` binds it to
the exact registry it came from.

## 9. YAML import

Authors may write YAML, but no reader interprets it. An importer converts one YAML file in the
subset below to the JCS bytes of the registry or kind declaration it holds, and every other step
reads only JSON. The document is a registry when its root mapping has `registryFormatVersion`, and
a kind declaration when it has `kindFormatVersion`; one with neither or both is `REG-DOC-SELECTOR`.
A registry's `kinds` and `entries` are written in canonical order (§4), by a stable sort, when each
item has those members as strings. The same file always gives the same bytes. A file outside the
subset is refused with a report, and nothing is written.

**The subset** is YAML 1.2, restricted to:

- **one document**, with no directive (`REG-YAML-DIRECTIVE`); no file, or more than one document,
  is `REG-YAML-DOCUMENTS`;
- **UTF-8** with no byte-order mark, holding only characters YAML allows, and none of U+0085,
  U+2028 and U+2029 as characters (`REG-YAML-ENCODING`). YAML 1.1 reads those three as line
  breaks and YAML 1.2 does not, so a file that holds one would be read two ways. Written as an
  escape in a double-quoted scalar (`\N`, `\L`, `\P`, or a `\x`, `\u` or `\U` escape of the
  code point), they have one reading and are admitted;
- **no tags** (`REG-YAML-TAG`), **no anchors or aliases** (`REG-YAML-ANCHOR`), **no merge key**
  `<<` (`REG-YAML-MERGE`);
- **no empty node** (`REG-YAML-EMPTY`): write `null` or `""`;
- **keys** that are strings on one line, of at most 1 024 characters, neither explicit (`?`) nor in
  flow form, and whose plain text reads as a string (`REG-YAML-KEY`); a duplicate key is
  `REG-DOC-DUPLICATE`;
- **plain scalars** read as: `true`, `false` and `null`; an integer matching `^-?(0|[1-9][0-9]*)$`
  and a decimal matching `^-?(0|[1-9][0-9]*)\.[0-9]+$`, each held to the number rule (§2.2,
  `REG-DOC-NUMBER`); and otherwise a string, unless another reader would read it as another value,
  which is `REG-YAML-SCALAR`. A scalar has another reading when it matches one of these whole:
  - `y|Y|yes|Yes|YES|n|N|no|No|NO|true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF`,
    `~|null|Null|NULL`;
  - `[-+]?0b[01_]+`, `[-+]?0[0-7_]+`, `[-+]?(?:0|[1-9][0-9_]*)`, `[-+]?0x[0-9a-fA-F_]+`,
    `[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+`, `[-+]?[0-9]+`, `0o[0-7]+`, `0x[0-9a-fA-F]+`;
  - `[-+]?(?:[0-9][0-9_]*)?\.[0-9_]*(?:[eE][-+][0-9]+)?`,
    `[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*`,
    `[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?`, `[-+]?\.(?:inf|Inf|INF)`,
    `\.(?:nan|NaN|NAN)`;
  - `[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}`, the same followed by a time
    (`(?:[Tt]|[ \t]+)[0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2}(?:\.[0-9]*)?(?:[ \t]*(?:Z|[-+][0-9]{1,2}(?::[0-9]{2})?))?`),
    `<<` and `=`;
  - or it begins with a digit or a sign and, with every `_` removed, matches
    `^[-+]?(?:0[bB][01]+|0[oO][0-7]+|0[xX][0-9a-fA-F]+|[0-9]+|(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?)$`.

  These are the readings of YAML 1.1, of the YAML 1.2 core schema and of a widely used Go YAML
  library. A plain key with another reading is `REG-YAML-SCALAR`, and one that reads as a number, a
  boolean or null is `REG-YAML-KEY`.

**Reading.** Every refusal is located at `{"document": "yaml", "pointer": "", "line": …, "column":
…}`, never by a pointer, which could spell a name the file holds. A refusal that leaves the structure
readable (a tag, an anchor or alias on a value, a merge key, a refused scalar or key text, an empty
node, a duplicate key, a lone surrogate, a number outside the rule) is reported and reading goes on;
every other refusal stops reading. After 1 000 refusals, the next is `REG-YAML-TRUNCATED` at its
place, and reading stops. This bound is the importer's alone: a validation report is bounded by
§7.4. The bytes written are then admitted as §2.2 admits their document, and a refusal there is
located at the line and column of the node its pointer reaches. A file over 8 MiB is `REG-DOC-SIZE`
at `{"document": "yaml", "pointer": ""}`. The report is a validation report with no `registry`
member, sorted as §7.4 says.

## 10. Facts

### 10.1 The facts document

For one entry of a valid registry's resolved registry for environment `e` (§8), the facts document
is an object of exactly:

- `registry`: the registry's `id`, `version` and digest;
- `environment`: `e`;
- `entry`: the entry's `kind`, `id` and `owner`;
- `value`: the entry's resolved value, mapped by the rules below;
- `references`: an object, always present, with one member per entry reference in the value. Its
  name is the pointer of the reference's position in the value, and its value is the target's
  `kind`, `id` and `value`: the target's resolved value in `e` mapped by the rules below as its own
  kind's, or, for a reference with `#pointer`, the value it addresses. One level only: the target's
  own references stay strings.

**Mapping rules.** Strings, booleans, null, arrays and objects are copied, with member names and
order kept. Every number becomes a string in one normal form: a number with an integer value in base
10, with `-` for a negative and no leading zero (`1.0` and `1e2` become `"1"` and `"100"`), and any
other with no exponent, no trailing zero after the point and a digit on each side of it (`1.50`
becomes `"1.5"`, `1e-7` becomes `"0.0000001"`). Every value at a secret position becomes
`{"store": <store>, "scope": <project>}`, so no facts document holds a secret reference.

The document is written as its JCS bytes. One whose JCS bytes are over 10 MiB, that nests deeper
than 128 (the root at depth 1), that holds more than 250 000 values, or that holds a string over
1 MiB in UTF-8, is `FACTS-DOCUMENT-LIMIT` at `{"document": "facts", "entry": …, "environment": e,
"pointer": ""}`, and nothing is written. It is never truncated.

### 10.2 Batches

A batch for one kind and environment has one line per entry of the kind that applies there, in
entry order: the JCS bytes of `{"facts": <facts document>, "id": "<kind>/<entry-id>"}` and a line
feed. Over every environment, the lines of each environment follow in the registry's order, with ids
`<environment>:<kind>/<entry-id>`. An invalid registry writes no line.

### 10.3 The facts contract

```json
{
  "factsContractVersion": "1.0.0",
  "id": "https://example.invalid/kinds/db-role",
  "version": "1.2.0",
  "source": { "kind": { "id": "https://example.invalid/kinds/db-role", "version": "1.2.0", "digest": "sha256:…" } },
  "facts": [ { "pointer": "/value/connectionLimit", "type": "decimal", "present": "optional" } ]
}
```

A contract has exactly these members. `source` is `{"authored": true}` for a contract written by
hand, or `{"kind": {"id", "version", "digest"}}` for one generated from a kind. `facts` lists every
position a facts document under the contract may hold a value at, each an object of:

- `pointer`: a pointer that begins with `/`, of at most 35 tokens, in which `*` is any member name
  or index and `~0`, `~1` and `~2` are escapes (§3.5);
- `type`: `string`, `decimal` (a string of Core §2.2's decimal grammar), `boolean`, `null`, `array`
  or `object`;
- `present`: `always` (whenever the parent is present) or `optional`;
- `items` (on an `array` only): the element type;
- `values` (optional): a non-empty list of distinct values of the type (of `items` for an array),
  not on `null`, `object`, or an array without `items`;
- `secretReference` (optional): `true`, on the `object` that stands for a secret reference.

`facts` is sorted strictly by `pointer` and then `type`, each in code-point order. A contract is
read as a registry is admitted (§2.2, document `contract`, bound 8 MiB); then a member not listed is
`FACTS-CONTRACT-FORM` at `""`, a member of the wrong form `FACTS-CONTRACT-FORM` at it (an item's,
at the item or its member), more than 65 536 facts or a pointer of more than 35 tokens
`FACTS-CONTRACT-LIMIT`, and an item out of order `FACTS-CONTRACT-ORDER` at it. A contract's digest
is that of its JCS bytes.

### 10.4 Generating a contract

A writer generates a kind's contract from the kind and the registry, and writes its JCS bytes, with
`id` and `version` the kind's and `source.kind` its id, version and pin digest:

- **Fixed rows:** `/entry` (object), `/entry/id`, `/entry/kind` (values: the kind), `/entry/owner`,
  `/environment` (values: the registry's environments, in order), `/registry` (object),
  `/registry/digest`, `/registry/id`, `/registry/version`, `/references` (object) and `/value`, all
  `always`, and strings unless marked. No row has the pointer `""`.
- **Value rows:** every position the schema allows, objects included, with its type from `type`
  (`integer` and `number` become `decimal`; no `type` allows every type). A member is `always` when
  its parent's schema requires it, and an array element is `optional`, at `<p>/*`. `values` is the
  intersection of the `enum` and `const` literals of the position's schemas, kept only when it is
  closed. `allOf` and `$ref` narrow, `anyOf` is a union, `not` is ignored, and a `false` schema
  allows nothing. An array row has `items` when its element has one type and is not open. An object
  whose `additionalProperties` is absent has an open position `<p>/*`.
- **Open positions:** a position with no constraint (`{}`, no `type` with nothing else, or every
  type with no members, no other members' schema and no element schema) is listed once per type at
  `p` and once per type at `p/*`, and nothing deeper. A pack check treats every pointer below such a
  `p/*` as listed (§10.5).
- **Secret positions** become an `object` row with `secretReference`, and `scope` (`always`) and
  `store` (`always`, values `["gcp-sm"]`) below it.
- **References:** a literal reference pattern gives `/references/<the pattern's pointer, escaped as
  one token>`, `always` when every step of it is a required member of an object position, and
  otherwise `optional`; a pattern with `*` gives `/references/*`, `optional`. Below each: `id`
  (`always`), `kind` (`always`, values the pinned kinds the pattern allows), and `value`, the union
  of the mapped shapes of every target kind and of everything they may hold. The union is wider than
  any one target; whether it should be narrowed is open (§17).
- **Bounds:** a contract over 8 MiB or 65 536 facts, or a generation over its work bound, is
  `FACTS-CONTRACT-LIMIT` at `{"document": "contract", "kind": …, "pointer": ""}`.

### 10.5 Checking a pack against a contract

**This check is defined, and is outside every conformance class of this version** (§15). Its rows
bind no claim. Core is unchanged: its advisories never change an evaluation.

A checker admits the pack as Core does and reads its evaluation form, then visits each fact
condition in `applicability`, each `exceptions[i].when` and each `rules[i].when`, through `not`
(`/condition`) and `all` and `any` (`/conditions/<i>`), in that order. For each it reports at most
one advisory, a warning at `{"document": "pack", "pointer": <the condition's pointer>}`:

- `FACTS-POINTER-UNKNOWN`: the contract lists no fact at the condition's path, or the path is not a
  pointer. A token matches a literal row and `*`; below an open `p/*`, every pointer is listed;
- `FACTS-TYPE-ORDERED`: an ordered operator, and no row at the path is `decimal`;
- `FACTS-VALUE-UNREACHABLE`: an `equals` or `not-equals` operand, or any item of an `in`, that no row
  at the path admits. A JSON number is never admitted (facts hold decimals as strings); an object is
  admitted only when its members are listed and admitted and the `always` members are present.

The report is `{"factsCheckFormatVersion": "1.0.0", "contract": {"digest"}, "pack": {"digest"},
"diagnostics": […]}`, with the pack's digest that of its bytes as supplied, and the advisories in
visit order. A check over its work bound (4 194 304) or a path deeper than 128 is
`FACTS-CHECK-LIMIT`, an error, at the condition it stopped at, and no later condition is checked.
The report needs no cap of its own: it has at most one advisory per fact condition, and the
pack's own bounds and the work bound limit the conditions. The contract's diagnostics, when it
is refused, are capped as §7.4 caps them.

### 10.6 Typed facts builders

A contract, generated or authored, is the input of a reference emitter with `"input":
"factsContracts"` (§11.1). For Go it generates a struct per object position and a `Build` function
that returns the canonical facts JSON: `decimal` fields are a decimal type that renders §10.1's
normal form, `always` fields are constructor arguments, and `values` become typed constants with a
build-time check. For TypeScript it generates interfaces, string-literal unions and a `buildFacts`
function; `decimal` accepts a decimal string or a `bigint`, never a `number`. Its goldens are checked
by the harness (§11.5), not by a reader.

## 11. Emitters

This section restates [RFC 0036](../rfcs/0036-registry-emitter-contract.md) §§1–7 as normative
text. No host or harness implements it yet, and no row exercises it.

### 11.1 The manifest

An emitter manifest has exactly: `emitterManifestVersion`; `id` (absolute URI); `version` (SemVer, no
build metadata); `owner` (§3.1); `description` (optional); `reads`, each `{"kind", "id",
"versions"}`, with `versions` one of `^x.y.z`, `~x.y.z`, `=x.y.z` or `>=x.y.z <x.y.z`; `input`
(optional, `"resolved"`, the default, or `"factsContracts"`); `requestVersions`, a non-empty array
of request selectors; `environments`, `"each"` or `"all"`, required with `"resolved"` and absent
with `"factsContracts"`; `options` (optional), a schema in §3.2's subset, default
`{"type": "object", "additionalProperties": false}`; `command`, an argv whose first item is a
program name with no `/` or a relative path in the repository; `owns`, globs of `*`, `**` and
literal characters naming every path the emitter writes; `env` (optional), variable names matching
`^[A-Z_][A-Z0-9_]{0,63}$` other than `PATH`, `HOME`, `LANG`, `TZ` and `SOURCE_DATE_EPOCH`; and
`deprecated` (optional), under which the host and harness run it with the warning
`EMIT-DEPRECATED`. The `owns` of two manifests in one repository MUST NOT overlap, and neither
`command` nor `owns` names a path outside the repository root.

### 11.2 The request

The host resolves the registry per environment, removes every entry and pin of a kind the manifest
does not read, refuses a pinned version outside its range (`EMIT-KIND-RANGE`), validates `options`,
and writes `{"emitRequestVersion", "emitter": {"id", "version"}, "options", "declarations": […],
"resolved": […]}` as JCS, with one resolved registry for `"each"` and every environment in order
for `"all"`. `declarations` holds the declaration of each kind whose pins remain, exactly as
admitted, in its JCS form, sorted by `kind`. A declaration's SHA-256 is its pin's `digest` (§2.3,
§4): an emitter checks each pin against its declaration and MUST refuse the run when a declaration
is missing or does not match. The `resolved` documents are unchanged, §8's format as `registry
resolve` writes it. With `"factsContracts"` the request holds `factsContracts` (generated contracts
of the kinds read, and the authored ones named, sorted by `id` then `version`) in place of
`declarations` and `resolved`. The host writes the highest request version it supports that the
manifest lists, or refuses the run (`EMIT-REQUEST-VERSION`), as it does when the registry needs a
later resolved format than a listed request version carries. Request `1.0.0` carries
`resolvedFormatVersion` and `factsContractVersion` `1.0.0`.

### 11.3 The response

The emitter writes one `{"emitResponseVersion", "files", "diagnostics"}` on standard output and
exits 0, with a response version whose major and minor do not exceed the request's. A non-zero exit
or a time-out is `EMIT-PROCESS`, and output that is not one valid response `EMIT-RESPONSE`. Each
file has a `path` and exactly one of `text` (UTF-8, ending in a line feed, with no carriage return)
or `base64`, and an optional `mode`, `"0644"` (default) or `"0755"`. A path uses `/`, is relative,
has no `.`, `..` or empty segment and no segment beginning with `~`, does not end with `/`, holds no
NUL, backslash or control character, matches an `owns` glob, and is unique once case is folded;
`files` is sorted by path. Emitter diagnostics have codes beginning with `x-`, a location of §7.3's
form and no value; an `error` among them fails the run. Bounds: a response of 64 MiB, 10 000 files,
16 MiB per file and 512 bytes per path.

### 11.4 The host

The host runs `command` from the repository root with the request on standard input and an
environment of only `PATH`, `HOME` (a fresh empty directory), `LANG=C.UTF-8` and the manifest's
`env` names, never printing an `env` value; it reads at most 64 KiB of standard error, reports only
its size unless asked to pass it through, and imposes a wall-clock limit (120 s by default). In write
mode it validates the whole response first, writes each file through a temporary file and a rename,
deletes owned files the response does not hold, refuses a symbolic link at or above an owned path,
and reports what it wrote and deleted: exit 0 written, 2 not written. In check mode it writes
nothing and compares byte for byte and mode for mode: exit 0 identical, 1 different (listing paths,
never contents), 2 could not check. A command line that cannot be parsed exits 3. An emitter MUST
give the same response bytes for the same request bytes: no clock, host name, absolute path,
locale, time zone, map order or network.

### 11.5 The harness

The harness runs an author's vectors (`request.json`, or `registry.json` with `kinds/` and an
optional `options.json`; and `expected/` or `expected-failure.json`) at the level named by
`vectors/harness.json` (`{"harnessLevel": "1.0"}`, the default). Level `1.0` applies six checks to
every vector: golden equality; determinism over three runs with a different `HOME`, `TZ`, `LANG`
and `SOURCE_DATE_EPOCH`; every path rule and bound of §11.3, with hostile responses substituted;
kind filtering, with a synthetic undeclared kind added; references, failing a file that holds a run
of at least 32 characters of a secret reference (or all of a shorter one) outside a complete
occurrence of it; and no stray writes (`EMIT-STRAY-WRITE`). A check that can fail a vector is added
only at a new level. The report (`harnessReportVersion` `"1.0.0"`) names the level and has one row
per vector and check: pass, fail, skip with its reason, or info. The harness exits 0 when nothing
fails, 1 when a check fails, and 2 when it could not run.

### 11.6 Reference emitters

The specification's reference emitters (a Go typed loader and TypeScript constants, and the
builders of §10.6) each promise their manifest, the kinds they read and their options, not the
bytes they write.

## 12. Diagnostic codes

The list is closed: a reader reports only these codes, each with its severity. The machine-readable
list is
[`codes.json`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/conformance/registry/1.0.0/codes.json),
and every code's status in `1.0.0` is `active`. The `TF-` codes of the dialect's `terraform-file`
source are the dialect's ([`dialect.md`](dialect.md) §4.5).

| Code | Severity | § | Raised when |
| --- | --- | --- | --- |
| `REG-DOC-SIZE` | error | §2.2 | a document is over its size bound, or a resolved document is (step 8) |
| `REG-DOC-JSON` | error | §2.2 | the bytes are not one JSON value in UTF-8 |
| `REG-DOC-DEPTH` | error | §2.2 | a value nests deeper than 32, or a resolved document does (step 8) |
| `REG-DOC-DUPLICATE` | error | §2.2 | an object has two members of one name |
| `REG-DOC-STRING` | error | §2.2 | a string escapes a lone surrogate |
| `REG-DOC-NUMBER` | error | §2.2 | a number is outside the number rule |
| `REG-DOC-SELECTOR` | error | §2.2 | the root is not an object, or its selector is missing or not supported |
| `REG-KIND-UNKNOWN-MEMBER` | error | §3.1 | a kind declaration, its bounds or a reference pattern has a member not defined |
| `REG-KIND-MISSING-MEMBER` | error | §3.1 | a required member of a kind declaration is absent |
| `REG-KIND-FORM` | error | §3.1 | a member of a kind declaration is not of its form |
| `REG-KIND-DEPRECATED` | warning | §3.1 | a pinned kind is deprecated |
| `REG-KIND-SCHEMA-KEYWORD` | error | §3.2 | a schema uses a keyword outside the subset |
| `REG-KIND-SCHEMA-FORM` | error | §3.2 | a keyword's value is not of its form |
| `REG-KIND-SCHEMA-REF` | error | §3.3 | a reference is malformed, names no definition, or starts a cycle |
| `REG-KIND-SCHEMA-LIMIT` | error | §3.3 | a schema has more than 4096 subschemas as written or expanded, an enum more than 1024 values, or a composition more than 16 branches |
| `REG-KIND-PATTERN` | error | §3.4 | a pattern is outside the pattern subset |
| `REG-KIND-PATTERN-LIMIT` | error | §3.4 | a pattern's size is over 4096, or would take the kind's patterns past 65536 |
| `REG-KIND-POINTER-FORM` | error | §3.5 | a pointer pattern is malformed |
| `REG-KIND-POINTER-UNREACHABLE` | error | §3.5 | a pointer pattern matches no position the schema allows |
| `REG-KIND-POINTER-CONFLICT` | error | §3.5 | a secret pattern and a reference pattern can match one position |
| `REG-REGISTRY-UNKNOWN-MEMBER` | error | §4 | the registry or one of its pins or entries has a member not defined |
| `REG-REGISTRY-MISSING-MEMBER` | error | §4 | a required member of the registry or of an entry is absent |
| `REG-REGISTRY-FORM` | error | §4 | a member of the registry, a pin, an entry, an overlay or a patch is not of its form |
| `REG-REGISTRY-DUPLICATE` | error | §4 | an environment or a pinned kind name is listed twice |
| `REG-REGISTRY-ORDER` | error | §4 | the pins or the entries are not in canonical order |
| `REG-PIN-MISSING` | error | §7.1 | no supplied kind declaration has a pin's digest |
| `REG-PIN-MISMATCH` | error | §7.1 | the declaration with a pin's digest has another kind, id or version |
| `REG-PIN-UNPINNED` | warning | §7.1 | a supplied kind declaration is not pinned |
| `REG-ENTRY-KIND` | error | §7.1 | an entry's kind is not pinned |
| `REG-ENTRY-ID` | error | §7.1 | an entry's id fails its kind's entryId pattern or the entry-id grammar |
| `REG-ENTRY-DUPLICATE` | error | §7.1 | two entries have one kind and id |
| `REG-ENTRY-OWNER` | error | §7.1 | an entry's owner is not in owners |
| `REG-ENTRY-ENVIRONMENT` | error | §7.1 | an entry names an environment the registry does not declare |
| `REG-OVERLAY-ENVIRONMENT` | error | §5 | an overlay's environment is not declared |
| `REG-OVERLAY-DUPLICATE` | error | §5 | two overlays have one environment |
| `REG-OVERLAY-PATCH-DUPLICATE` | error | §5 | two patches of one overlay name one entry |
| `REG-OVERLAY-ENTRY-MISSING` | error | §5 | a patch names no entry |
| `REG-OVERLAY-ENTRY-ABSENT` | error | §5 | a patch names an entry that does not apply in the overlay's environment |
| `REG-OVERLAY-POINTER` | error | §5 | a set key is not a JSON Pointer |
| `REG-OVERLAY-NOT-OVERLAYABLE` | error | §5 | no overlayable pattern matches a set key |
| `REG-OVERLAY-TARGET` | error | §5 | a set key addresses no reachable position |
| `REG-OVERLAY-NULL` | error | §5 | a set value is null |
| `REG-OVERLAY-PREFIX` | error | §5 | a set key is a prefix of another |
| `REG-VALUE-TYPE` | error | §7.2 | a value is not of an allowed type, or a false schema applies |
| `REG-VALUE-ENUM` | error | §7.2 | a value is not in its enum |
| `REG-VALUE-CONST` | error | §7.2 | a value is not its const |
| `REG-VALUE-REQUIRED` | error | §7.2 | a required member is absent |
| `REG-VALUE-ADDITIONAL` | error | §7.2 | a member is not allowed |
| `REG-VALUE-PROPERTY-COUNT` | error | §7.2 | an object has too few or too many members |
| `REG-VALUE-PROPERTY-NAME` | error | §7.2 | a member name fails propertyNames |
| `REG-VALUE-ITEM-COUNT` | error | §7.2 | an array has too few or too many items |
| `REG-VALUE-UNIQUE` | error | §7.2 | an array that must be unique has two equal items |
| `REG-VALUE-LENGTH` | error | §7.2 | a string is too short or too long |
| `REG-VALUE-PATTERN` | error | §7.2 | a string does not match its pattern |
| `REG-VALUE-RANGE` | error | §7.2 | a number is outside its bounds |
| `REG-VALUE-ANY-OF` | error | §7.2 | no branch of an anyOf holds |
| `REG-VALUE-NOT` | error | §7.2 | the schema of a not holds |
| `REG-VALUE-DEPRECATED` | warning | §7.2 | a value is at a position marked deprecated |
| `REG-BOUND-ENTRIES` | error | §7.1 | a kind has more entries than its maxEntries |
| `REG-BOUND-ENTRY-BYTES` | error | §7.1 | a resolved value is larger than its kind's maxEntryBytes |
| `REG-BOUND-VALIDATION-WORK` | error | §7.2 | value validation passed the reader's work bound, and this value and later ones were not checked |
| `REG-REPORT-TRUNCATED` | warning | §7.4 | the report holds its first 1000 diagnostics and more were found |
| `REF-ENTRY-FORM` | error | §6.2 | a value at a reference position is not an entry reference |
| `REF-ENTRY-KIND` | error | §6.2 | a reference names a kind its position does not allow |
| `REF-ENTRY-MISSING` | error | §6.2 | a reference names no entry |
| `REF-ENTRY-ABSENT-IN-ENVIRONMENT` | error | §6.2 | a reference names an entry that does not apply in the environment |
| `REF-ENTRY-POINTER` | error | §6.2 | a reference's pointer addresses nothing in the target's resolved value |
| `REF-SECRET-FORM` | error | §6.3 | a value at a secret position is not a secret reference |
| `REF-SECRET-STORE` | error | §6.3 | a secret reference names a store this version does not define |
| `REF-SECRET-PIN` | error | §6.3 | a secret reference floats, or names its project by number |
| `REF-SECRET-SCOPE-FORM` | error | §6.4 | secretScopes is not of its form |
| `REF-SECRET-SCOPE` | error | §6.4 | a secret reference names a project not listed for its environment |
| `REF-SECRET-SCOPE-SHARED` | error | §6.4 | a project is listed for two environments |
| `REF-SECRET-UNSCOPED` | warning | §6.4 | a secret reference is in a registry without secretScopes |
| `REG-YAML-ENCODING` | error | §9 | the file is not UTF-8 without a byte-order mark |
| `REG-YAML-DOCUMENTS` | error | §9 | the file holds other than one document |
| `REG-YAML-DIRECTIVE` | error | §9 | the file has a directive |
| `REG-YAML-TAG` | error | §9 | a node has a tag |
| `REG-YAML-ANCHOR` | error | §9 | a node has an anchor, or is an alias |
| `REG-YAML-MERGE` | error | §9 | a key is a merge key |
| `REG-YAML-SCALAR` | error | §9 | a plain scalar has another reading |
| `REG-YAML-EMPTY` | error | §9 | a node is empty |
| `REG-YAML-KEY` | error | §9 | a key is not a plain or quoted single-line string of at most 1024 characters |
| `REG-YAML-SYNTAX` | error | §9 | the file is not YAML |
| `REG-YAML-TRUNCATED` | error | §9 | the import stopped after 1000 refusals |
| `FACTS-DOCUMENT-LIMIT` | error | §10.1 | an entry's facts document is over a facts bound |
| `FACTS-CONTRACT-FORM` | error | §10.3 | a contract is not of its form |
| `FACTS-CONTRACT-ORDER` | error | §10.3 | a contract's facts are not in order |
| `FACTS-CONTRACT-LIMIT` | error | §10.3 | a contract is over a contract bound, or its generation is |
| `FACTS-POINTER-UNKNOWN` | warning | §10.5 | a pack reads a pointer the contract does not list |
| `FACTS-TYPE-ORDERED` | warning | §10.5 | a pack orders a pointer that is not decimal |
| `FACTS-VALUE-UNREACHABLE` | warning | §10.5 | a pack compares a pointer with a value the contract does not admit |
| `FACTS-CHECK-LIMIT` | error | §10.5 | the pack check is over its work or depth bound |
| `EMIT-REQUEST-VERSION` | error | §11.2 | the host writes no request version the manifest lists, or none that carries the registry |
| `EMIT-KIND-RANGE` | error | §11.2 | a pinned kind's version is outside the manifest's range |
| `EMIT-PROCESS` | error | §11.3 | the emitter exited non-zero, or did not finish in time |
| `EMIT-RESPONSE` | error | §11.3 | the emitter's output is not one valid response |
| `EMIT-STRAY-WRITE` | error | §11.5 | the emitter created or changed a file itself |
| `EMIT-DEPRECATED` | warning | §11.1 | the emitter's manifest is deprecated |

## 13. Versioning and stability

The companion is released on the scoped tag `registry-v<major>.<minor>.<patch>`, the Policy
companion's route without its draft-only restriction ([VERSIONING.md](../VERSIONING.md)). A first
release publishes this text, the closed schemas of its documents under `schema/registry/1.0.0/`,
the code list and the rows.

**From the first stable release**, within major version 1:

- no selector, member, diagnostic code, validation rule or harness check is removed or changes
  meaning;
- new optional members and new warning codes are added only under a new minor selector, and a check
  that can fail a vector only at a new harness level;
- a deprecated selector, member, code, rule or kind keeps working, with a warning, until 2.0, and
  the code list gives each code its status, `active` or `deprecated`;
- a reader claims conformance to an exact release and its complete rows.

**Selectors across 1.x.** Every selector of §2.1 is `"1.0.0"` in this version. A reader lists the
exact selectors it supports, and a writer writes the lowest selector whose format expresses the
document, so a reader of `1.0.0` keeps reading every document that needs no later member, and
refuses, rather than misreads, one that does. Consumers of resolved registries declare the
selectors they accept, and a producer writes one of them or refuses. A change to the facts
document's bytes is a new `resolvedFormatVersion` (§2.1).

## 14. Machine-readable form and rows

The code list and the rows are staged under
[`conformance/registry/1.0.0/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/registry/1.0.0),
with a README that says how each row is compared. Every input is synthetic. Where a file and this
text differ, this text governs. The rows exercise admission, kind declarations, the registry's
shape, pins, entries, overlays, both kinds of reference, bounds and warnings, resolution in two
environments, facts batches, two generated contracts and two pack checks. They do not yet exercise
`REG-ENTRY-ID`, `REG-ENTRY-DUPLICATE` and `REG-ENTRY-ENVIRONMENT`; value validation (§7.2) beyond
`REG-VALUE-RANGE` and `REG-VALUE-DEPRECATED`; YAML import, the report bound, the facts and contract limits, contract reading, authored contracts,
wildcard reference patterns, emitters, the harness or builders, and the boundary and adversarial
sets RFC 0034 lists.

## 15. Conformance classes

| Class | Sections | Rows |
| --- | --- | --- |
| Registry reader | §§2–8, §12 | `class` `registry-reader` |
| Importer | §9 | none yet |
| Facts writer | §§10.1–10.4 | `class` `facts-writer` |
| Emitter host | §§11.1–11.4 | none yet |
| Emitter harness | §11.5 | none yet |

A claim names its class, the exact release, and its complete rows; a class without rows is defined,
and not claimable. The pack check (§10.5) is in no class. The stable bar is two independently written
readers agreeing on every row of a class.

## 16. Security and privacy

- **Secrets.** No component fetches or holds a secret's value. A resolved registry carries
  references as written; facts carry only a store and a scope. Pins close the "same registry,
  different secret" gap, and scopes the cross-environment leak.
- **Disclosure.** Reports, locations, check output and harness output carry codes, identifiers and
  pointers, never values, references or file contents. An emitter's standard error is discarded by
  default, and no `env` value is printed.
- **Resources.** Every document, schema, pattern, report, facts document, contract and emitter
  response is bounded, and patterns match in linear time.
- **Authority.** Owners are identifiers, not permissions: a valid registry authorizes nothing.
- **Residual risk.** Pinning cannot stop a store administrator replacing a version, and an emitter
  is code the repository chose to run; the host is not a sandbox.

## 17. What this text settles, and what is open

**Settled here**, where the records left it open or the reference runtime differs:

- the `kind` location member on every step-2 diagnostic of a declaration whose `kind` is well
  formed (§7.3);
- the cycle check covers every `$ref` that names a definition, whatever else the schema has (§3.3);
- an entry reference's `#pointer` is at most 512 code points (§6.2), as RFC 0035 says, while a
  pointer pattern is at most 512 bytes (§3.5);
- the `id` of a kind and a registry is an RFC 3986 absolute URI (§3.1);
- equal declarations are located at the least `kindDocument` (§7.1);
- the diagnostic codes RFCs 0034 to 0037 did not name are adopted as §12 lists them;
- an open position is listed at `p` and `p/*`, and a pointer below `p/*` is listed (§10.4);
- `factsCheckFormatVersion` is the check report's own selector, and the facts document has none
  (§2.1).
- a resolved-form emit request carries the read kinds' `declarations`, bound to their pins by
  digest, as part of request `1.0.0` (§11.2); RFC 0036 §2 names only the pins, and an emitter
  opens no file, so the reference emitters of §11.6 could not otherwise see a schema or a secret
  position.

**Open:**

- **Reference widening.** A contract's `/references/<p>/value` is the union of every target kind's
  shapes (§10.4). Whether it should be narrowed to the kinds a position allows, per target, is not
  decided; this version writes the widening.
- **Pattern size, as written.** §3.4 counts a pattern's size on the pattern as written. The
  reference runtime `v0.47.0` counts it on its engine's parse, which factors alternations and
  merges classes, and so admits `(ab|ac){1000}`, which is 5 000 as written. The text governs, and
  the row `pattern-bounds` expects the refusal. The runtime follows in a later release.
- **Reader bounds.** A reader's own limits are not pinned: a pattern within the subset that its
  engine cannot compile (§3.4), and value validation past its work bound (§7.2). A conformance
  row stays well within the reference runtime's limits.
- **Importer stops.** Which refusals stop an import, beyond those §9 names, is fixed by the first
  import rows.
- **Emitter host refusals.** A malformed manifest, overlapping `owns`, options that fail their
  schema, a link at an owned path and an unreadable path have no code in RFC 0036; their codes come
  with the first host's rows.
- **Pattern refusal.** Whether patterns that are catastrophic for backtracking engines should also be
  refused (RFC 0034, Unresolved question 2).
- **Review regime.** The different-vendor review was waived for the records.

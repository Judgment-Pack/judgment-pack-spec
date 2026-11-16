# RFC 0034: The registry profile — declared entry kinds and environment overlays

- Status: Draft
- Type: Standards track, a proposed companion document beside Core (`spec/registry.md`), with its
  own format selector and its own release route, intended for **stable** maturity at its first
  release
- Created: 2026-11-16
- Issue: [#339](https://github.com/Judgment-Pack/judgment-pack-spec/issues/339)
- Related: RFC 0035 (reference syntax), RFC 0036 (the emitter contract and its conformance
  harness), RFC 0037 (generated facts contracts), RFC 0038 (a file-sourced dialect source); the
  dialect companion ([`spec/dialect.md`](../spec/dialect.md)); the Policy companion's independent
  release route ([VERSIONING.md](../VERSIONING.md#independently-versioned-policy-draft-companion))

> This RFC, a Draft, is normative for nothing. No schema, corpus or companion text exists yet; the
> Specification below is the text proposed for `spec/registry.md`. Core is untouched.

## Summary

A repository that runs several services keeps a list of what it runs and how: services, their
callers, database roles, access grants, configuration values per environment, references to
secrets. Today each repository invents that list's format, its validation and the generators that
turn it into deployment files and start-up code, so none of it can be checked by a tool it did not
write.

This RFC proposes a small, domain-neutral **registry**: one canonical JSON document of entries,
each entry of a **kind** that the adopting repository declares, plus per-environment
**overlays**. JPS standardizes the containers, not their contents:

- A **kind declaration** is a JSON document that names a kind, gives the schema its entries' values
  must satisfy (a closed subset of JSON Schema 2020-12), its bounds, its owner, which members an
  overlay may change, which members hold secret references, and which hold references to other
  entries.
- A **registry document** pins the kind declarations it uses by digest, lists its environments and
  owners, and holds entries and overlays.
- **Validation** is a fixed procedure that two independent readers can agree on, diagnostic for
  diagnostic, without either one knowing what a "database role" is.
- **Resolution** produces one resolved document per environment, the only input emitters read
  (RFC 0036).

A database role, a group class, an access grant or a login map is a kind an adopter declares, not a
kind JPS defines. A new kind, or a new deployment target, needs no JPS release.

## Problem

1. **Every repository reinvents the format.** Without a shared container, a configuration list is a
   bespoke YAML layout read by a bespoke generator. Its validation is whatever that generator
   happens to check, and its errors are whatever it happens to print.
2. **Validation is not portable.** A CI check written in one language cannot be re-run by a second
   implementation to confirm it, because the rules live in code, not in a document.
3. **Environment drift is invisible.** Per-environment differences are usually copies of whole
   files. A reviewer cannot see what differs between staging and production, or prevent production
   from changing a value no one meant to vary.
4. **Secrets leak into lists.** A configuration list is a natural place to paste a credential.
   Nothing in a bespoke format distinguishes "a reference to a secret" from "a secret".
5. **Generators are not reproducible.** When the generator reads the authoring files directly,
   every generator re-implements parsing, defaults and overlays, and two generators can disagree
   on what the list says.

The affected users are platform teams who keep such a list for several services, and the tools
(start-up loaders, deployment generators, CI checks, drift detectors) that read it.

## Evidence

- An adopting organization keeps a registry of this shape today in its own format, with its own
  generator for start-up loaders, deployment variables, database bootstrap inputs and caller
  lists, and has asked for the format, the validation and the start-up loader to come from JPS so
  that its own release can depend on a stable, separately checked contract. Its domain kinds
  (database roles, group classes, access grants, a login map) are the cases the kind declaration
  below has to express. They are synthesized as fixtures in this RFC's vectors, with no content
  from that organization.
- JPS already ships companions with their own format selectors, closed schemas and staged vectors
  checked by two readers (the dialect, Policy, the retained column), so the release route exists.
- JSON Schema 2020-12 is the schema language most configuration tools already read. Its full
  vocabulary is not portable across implementations (format assertions, dynamic references,
  regular-expression dialects), which is why a closed subset is proposed rather than the whole
  language.

## Specification

The key words MUST, MUST NOT, SHOULD and MAY are to be read as described in BCP 14 when, and only
when, they appear in capitals.

### 1. Documents and selectors

The companion defines four JSON documents. Each carries an exact format selector, and a reader that
does not support that exact selector MUST refuse the document. There are no aliases and no
"compatible" selectors.

| Document | Selector member | Value at first release |
|---|---|---|
| Kind declaration | `kindFormatVersion` | `"1.0.0"` |
| Registry | `registryFormatVersion` | `"1.0.0"` |
| Resolved registry (one environment) | `resolvedFormatVersion` | `"1.0.0"` |
| Validation report | `reportFormatVersion` | `"1.0.0"` |

Every document is I-JSON (RFC 7493):
- no duplicate member names;
- no lone surrogates;
- every number is either an integer whose magnitude is at most 2^53 − 1, or a finite decimal that
  round-trips through an IEEE 754 double, by value: the exact decimal value of the literal equals
  the exact decimal value of the shortest decimal that reads back as the same double. `1.50` and
  `0.1` are admitted, and `0.10000000000000001` is not;
- no number is negative zero (`-0`, `-0.0`, `-0e0`), because its canonical form would be `0`.

A number outside these rules is `REG-DOC-NUMBER`.

A document's identity bytes are its RFC 8785 (JCS) canonical form, and every digest in this
companion is `sha256:` followed by 64 lowercase hexadecimal digits of SHA-256 over those bytes.

**Size and depth bounds.**

| Document | Bound |
|---|---|
| Kind declaration | 256 KiB |
| Registry | 8 MiB |
| Resolved registry | 8 MiB |
| Nesting depth of any value | 32 |

A reader refuses a document over a bound with the bound's diagnostic, before interpreting it.

### 2. Kind declaration

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

**Members of a kind declaration.**

- **`id`**: an absolute URI.
- **`version`**: strict SemVer 2.0.0 with no build metadata.
- **`kind`**: the local name entries use. It matches `^[a-z][a-z0-9-]{0,62}$`, and within one
  registry it MUST be unique.
- **`owner`**: the party that owns the declaration, meaning whoever may change the schema. It is
  an opaque string of 1 to 128 characters from `[A-Za-z0-9._@/-]`. JPS assigns it no meaning
  beyond identity. Enforcement belongs to the repository's own review rules (for example, code
  owners).
- **`entryId.pattern`**: the grammar of entry ids, in the pattern subset of §2.2. It defaults to
  `^[a-z][a-z0-9-]{0,62}$`. Whatever the pattern allows, an id is also held to RFC 0035's
  `entry-id` grammar: 1 to 128 characters from U+0021 to U+007E, with no `/` and no `#`. An id
  that fails either is `REG-ENTRY-ID`, so every valid entry can be referenced.
- **`schema`**: the schema each entry's value MUST satisfy, in the closed subset of §2.1, after
  overlays are applied (§5).
- **`secrets`**: pointer patterns (§2.3) that name members holding a secret. At each matched
  member the value MUST be a secret reference in the syntax of RFC 0035, never a literal.
- **`references`**: pointer patterns whose matched string members are entry references (RFC 0035)
  to an entry of one of the listed kinds.
- **`overlayable`**: pointer patterns an overlay may change (§4). The default is empty: no member
  varies by environment unless the kind says so.
- **`bounds.maxEntries`** (default 10 000) and **`bounds.maxEntryBytes`** (default 65 536, over the
  canonical bytes of the entry's resolved value).
- **`description`**, and **`deprecated`** (a boolean, at the top level): informative. A registry
  that uses a deprecated kind validates, with a warning.

No other member is permitted. Every member not marked optional above is required.

#### 2.1 The schema subset

A kind's `schema` is a JSON Schema 2020-12 schema restricted to these keywords. Any other keyword,
including `$schema`, `$id`, `$dynamicRef`, `format`, `if`/`then`/`else`, `patternProperties`,
`dependentSchemas` and `unevaluatedProperties`, makes the kind declaration invalid. The rule is
not "the keyword is ignored".

| Group | Keywords |
|---|---|
| Type | `type` (one name or an array of names), `enum`, `const` |
| Objects | `properties`, `required`, `additionalProperties` (boolean or schema), `minProperties`, `maxProperties`, `propertyNames` (only `pattern` and `maxLength` inside) |
| Arrays | `items`, `minItems`, `maxItems`, `uniqueItems` |
| Strings | `minLength`, `maxLength` (counted in Unicode code points), `pattern` |
| Numbers | `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum` |
| Composition | `anyOf`, `allOf`, `not` (each with at most 16 branches) |
| Local definitions | `$defs`, and `$ref` only of the form `#/$defs/<name>`, with no cycle |
| Annotations | `title`, `description`, `default`, `deprecated`, `examples` |

**Annotations do not change validation.** `default` is not applied by validation or resolution.
An emitter MAY read it (RFC 0036). A member whose subschema says `deprecated: true`, when present,
produces a warning, never an error.

**Size limits.** A schema has at most 4 096 subschemas, and `enum` at most 1 024 values.

`oneOf` is excluded. Its "exactly one" rule makes the diagnostics of two implementations diverge
on overlapping branches, and `anyOf` with `not` expresses what kinds need.

#### 2.2 The pattern subset

`pattern`, `propertyNames.pattern` and `entryId.pattern` use a regular-expression subset that has
one meaning in RE2, ECMAScript (with the `u` flag) and Python's `re`.

**Allowed constructs:**
- literal code points, and the escapes `\.` `\-` `\\` `\/` `\(` `\)` `\[` `\]` `\{` `\}` `\*` `\+`
  `\?` `\|` `\^` `\$`;
- `.`;
- bracket classes with ranges and a leading `^`;
- `\d`, meaning ASCII digits only;
- `^` and `$` only as the first and last character;
- groups `( )` with no capture semantics relied on;
- `|`;
- the quantifiers `*`, `+` and `?`, and `{n}`, `{n,}` and `{n,m}` with `m ≤ 1000`.

**Excluded constructs:** back-references, look-around, named groups, flags, `\w`, `\s`, `\b`,
Unicode property classes, possessive and lazy quantifiers.

**Matching semantics:**
- A pattern matches if it matches anywhere in the string (JSON Schema semantics), so anchoring is
  the author's.
- A pattern longer than 256 characters invalidates the kind.
- A reader MUST evaluate patterns in time linear in the input, for example with an automaton. A
  backtracking engine is not conformant on adversarial input.

#### 2.3 Pointer patterns

A pointer pattern is an RFC 6901 JSON Pointer in which a reference token may be `*`, meaning any
member name or any array index at that position. `/grants/*/role` matches the `role` member of
every element of `grants`. A literal member named `*` is written `~2`, extending RFC 6901's
escapes for this companion only.

A pattern that can match no position the schema allows makes the kind declaration invalid. A
reader determines this from `properties`, `items` and `additionalProperties`, and does not search
values.

#### 2.4 Kind versions

A kind's `version` follows these rules, so that a SemVer range over kind versions (RFC 0036 §1)
means something:

- **A patch version** changes only annotations (§2.1) and `description`. Every value has the same
  diagnostics under both versions.
- **A minor version** may only widen: every value valid under the previous version is valid under
  the new one. It may add optional members, widen an `enum`, relax a bound, add `overlayable`
  patterns, raise `bounds`, and set `deprecated`. It MUST NOT change `kind`, `entryId`, `secrets`
  or `references`, because each of those can make a valid registry invalid or change what an
  emitter must treat as a reference.
- **Anything else is a new major version.**

Validation checks a registry against the exact kinds it pins, and does not compare two versions
of a kind. A tool that compares them, such as a check on a kind's pull request, applies these
rules. A consumer that reads a kind by range MUST accept members it does not know, because a minor
version may add them.

### 3. Registry document

```json
{
  "registryFormatVersion": "1.0.0",
  "id": "https://example.invalid/registries/platform",
  "version": "4.0.0",
  "environments": ["dev", "staging", "prod"],
  "owners": ["platform-data", "team-billing"],
  "kinds": [
    { "kind": "db-role", "id": "https://example.invalid/kinds/db-role", "version": "1.2.0",
      "digest": "sha256:…" },
    { "kind": "database", "id": "https://example.invalid/kinds/database", "version": "1.0.0",
      "digest": "sha256:…" }
  ],
  "entries": [
    { "kind": "database", "id": "billing", "owner": "team-billing", "value": { "engine": "postgres" } },
    { "kind": "db-role", "id": "billing-api", "owner": "team-billing",
      "value": { "database": "entry:database/billing", "privileges": ["read", "write"],
                 "password": "secret:gcp-sm:projects/example-dev/secrets/billing-db/versions/3",
                 "connectionLimit": 20 } },
    { "kind": "db-role", "id": "billing-backfill", "owner": "team-billing", "environments": ["dev", "staging"],
      "value": { "database": "entry:database/billing", "privileges": ["read"] } }
  ],
  "overlays": [
    { "environment": "prod",
      "patches": [ { "kind": "db-role", "id": "billing-api", "set": { "/connectionLimit": 120,
        "/password": "secret:gcp-sm:projects/example-prod/secrets/billing-db/versions/7" } } ] }
  ]
}
```

The reference forms `entry:` and `secret:` above are defined by RFC 0035. The example omits the staging overlay, which would set its own `/password`, and the `secretScopes` member RFC 0035 adds.

**Members of a registry document.**

- **`environments`**: 1 to 32 distinct names, each matching `^[a-z][a-z0-9-]{0,31}$`.
- **`owners`**: the closed list of parties entries may name, with the same grammar as a kind's
  `owner`.
- **`kinds`**: pins every kind declaration the registry uses, by `kind`, `id`, `version` and the
  digest of its canonical bytes. A reader is given the kind declaration documents separately and
  MUST match each by digest. A declaration that is missing or does not match is a refusal, never
  a fetch.
- **`entries`**: each entry has a `kind`, an `id`, an `owner`, an optional `environments` (a
  non-empty subset of the registry's environments; it defaults to all of them) and a `value`.
- **`overlays`**: at most one overlay per environment. Each overlay holds `patches`.

**Canonical order.** `kinds` is sorted by `kind`, and `entries` by `kind` then `id`, by code-point
order. `jpack registry import` writes this order, and validation reports an out-of-order document
as an error. Two registries that say the same thing therefore have the same bytes.

### 4. Overlays

A patch names one entry by `kind` and `id`, and gives `set`: an object whose member names are
concrete JSON Pointers into the entry's value, and whose values replace the value at that pointer.

**Rules for a patch.**

- **The target must be reachable.** The pointer MUST match one of the kind's `overlayable`
  patterns, and MUST address a member or array element that exists in the base value, or a member
  the schema's `properties` declares.
- **No deletions.** A value of `null` is a deletion, and deletions are not allowed: a member that
  varies by being absent is expressed in the base value and the kind's schema.
- **A patch never adds an entry.** An entry that exists in only some environments says so with its
  `environments` member.
- **The entry must apply.** A patch for an entry that does not apply in its overlay's environment
  is an error, because it can never take effect.
- **Order does not matter.** Within one patch, no two pointers may be equal, and no pointer may be
  a prefix of another, so the order patches are applied in cannot change the result.

### 5. Resolution

Resolution of a valid registry for one environment `e` produces a resolved registry:

```json
{
  "resolvedFormatVersion": "1.0.0",
  "registry": { "id": "https://example.invalid/registries/platform", "version": "4.0.0", "digest": "sha256:…" },
  "environment": "prod",
  "kinds": [ { "kind": "db-role", "id": "…", "version": "1.2.0", "digest": "sha256:…" } ],
  "entries": [
    { "kind": "db-role", "id": "billing-api", "owner": "team-billing",
      "value": { "database": "entry:database/billing", "privileges": ["read", "write"],
                 "password": "secret:gcp-sm:projects/example-prod/secrets/billing-db/versions/7",
                 "connectionLimit": 120 } }
  ]
}
```

**Procedure.** For each entry that applies in `e`, in canonical order, its `value` is the base
value with every pointer of `e`'s patch for that entry replaced. Entries that do not apply in `e`
are omitted.

**What resolution does not do:**
- It applies no default.
- It never replaces a reference with what it refers to. Secrets are never fetched. Whether a
  reference is well formed, pinned and allowed in `e` is checked as RFC 0035 sets out.

The resolved registry is the only input an emitter reads (RFC 0036). Its `registry.digest` binds it
to the exact registry it came from.

### 6. Validation

Validation of a registry, given its kind declarations, runs these checks in this order. Each check
runs only on documents and entries that passed the checks before it, and every applicable
diagnostic is reported, not only the first.

1. **Document admission**: the bounds of §1, I-JSON, and the exact selector, for the registry and
   for each kind declaration supplied.
2. **Kind declarations**: each one's shape, its schema subset (§2.1), its patterns (§2.2), and its
   pointer patterns (§2.3).
3. **Registry shape**: members, grammars, and canonical order (§3).
4. **Kind pins**: every pinned kind is supplied and its digest matches, kind names are unique, and
   every supplied declaration is pinned (an unpinned extra is a warning).
5. **Entries**:
   - the kind is pinned;
   - the id matches the kind's `entryId`, and `(kind, id)` is unique;
   - the owner is in `owners`;
   - `environments` is a subset of the registry's.
6. **Overlays**: each one's environment is declared, every patch target exists and applies, and
   every pointer satisfies §4.
7. **Per environment**, in the order of `environments`, on the resolved value of each entry:
   - the kind's schema;
   - `secrets` members hold a secret reference;
   - `references` members hold an entry reference whose target exists in that environment and is
     of an allowed kind;
   - the checks RFC 0035 adds.
8. **Bounds**: each kind's `maxEntries` and `maxEntryBytes`.

**The validation report** (`reportFormatVersion` `"1.0.0"`) lists each diagnostic with:
- `code`, from the closed list the companion publishes;
- `severity`, either `error` or `warning`;
- `location`, which may hold a kind, an entry `kind`/`id`, an environment, and a JSON Pointer.

Diagnostics are sorted by location, then code. A diagnostic carries no value from the document:
no member value, no secret reference, and no pattern text taken from a value.

**Agreement.** Two readers agree on a registry when their reports have the same diagnostics, by
code, severity and location. Messages are informative and not compared. A registry is valid when
its report has no error.

### 7. Authoring: YAML import

Authors write YAML, but no reader interprets it. `jpack registry import` converts a closed YAML
subset into the canonical registry JSON (and kind declarations, if authored in YAML), and every
other step reads only JSON.

**The YAML subset is YAML 1.2 restricted to the following:**

- **One document per file**, with no directives and no tags.
- **No anchors, aliases or merge keys.**
- **Plain scalars:**
  - `true`, `false` and `null` (lowercase only) are those values.
  - A decimal integer with no leading zero, within ±(2^53 − 1), is an integer.
  - A decimal with a fraction and no exponent is a number.
  - Every other plain scalar is a string.
  - A plain scalar that YAML 1.1 would have read differently (`yes`, `no`, `on`, `off`, `~`,
    `0o17`, `0x1F`, `1e3`, `.inf`, `.nan`, a leading-zero integer, or a date) is refused, and must
    be quoted to be a string.
- **No duplicate keys**, and keys are strings.
- **No complex keys or flow-style keys spanning lines.**
- **UTF-8 only**, without a byte-order mark.

The import is deterministic: the same files give the same bytes. A file that is outside the subset
is refused with its line and column, and nothing is written.

### 8. Release route and stability

The companion is released on its own scoped tag, `registry-v<major>.<minor>.<patch>`, beside Core
and independent of `specVersion`. This is the Policy companion's route, without its draft-only
restriction.

**What the first release publishes:**
- this text;
- the closed schemas of the four documents, under `schema/registry/1.0.0/`;
- the diagnostic code list;
- the vectors (§ Conformance).

**Stability promise**, from the first stable release:
- Within major version 1, no selector, member, diagnostic code or validation rule is removed or
  changes meaning.
- New optional members and new warning diagnostics may be added under a new minor format
  selector.
- A deprecated element warns and keeps working until 2.0.
- A reader claims conformance to an exact release and its complete vector set.

**Selectors across 1.x.** A reader lists the exact selectors it supports, and a writer writes the
lowest selector whose format expresses the document. A registry that uses no member added after
`1.0.0` is written, and resolved, as `1.0.0`. So a reader of `1.0.0` keeps reading every document
that does not need a later member. A document that needs one is refused by an older reader rather
than misread. Consumers that take resolved documents (emitters, RFC 0036; the start-up package)
declare the selectors they accept, and the producer writes one of them or refuses.

**Deprecation.** The published diagnostic code list gives each code a status, `active` or
`deprecated`. Selectors, members, codes, rules and kinds can each be deprecated within 1.x. A
deprecated one keeps its meaning and produces a warning where it is used. Nothing deprecated is
removed before 2.0.

**Related artifacts.** The Go start-up package that reads resolved registries is proposed at
`github.com/Judgment-Pack/judgment-pack-runtime/startup`, a nested module of the reference runtime
tagged `startup/vX.Y.Z`. It is product code, not part of this companion: it is named here so its
version can be tied to the companion's in the runtime's own records.

## Alternatives

- **No change.** Each repository keeps its own format and generator. This is the problem as
  stated: nothing is checkable by a second tool, and an adopter's stable release cannot rest on a
  contract JPS does not publish.
- **JPS defines the domain kinds** (services, roles, grants). This was the first plan, and it was
  rejected. Every new kind or target would need a JPS release, and the kinds that matter most
  (database roles, access models) differ between organizations.
- **Full JSON Schema 2020-12.** Implementations differ on `format`, dynamic references and regular
  expressions, so two readers would not agree. The subset keeps what configuration kinds use.
- **CUE, Jsonnet, or an HCL-like language** as the authoring and validation language. These are
  powerful, but each has one dominant implementation, which defeats the two-reader bar. They
  would also make validation a program rather than a document check.
- **JSON Merge Patch (RFC 7396) or JSON Patch (RFC 6902) for overlays.** Merge Patch uses `null`
  for deletion and replaces arrays wholesale by member name, and JSON Patch allows moves, removals
  and tests. Both are more than environments need, and both make what can vary between
  environments implicit. Pointer-keyed `set`, limited by `overlayable`, makes it explicit and
  reviewable.
- **Overlays as separate files per environment.** This is equivalent on the wire. `import` MAY
  accept overlay files and fold them into the one canonical document, so authors keep that layout.
- **A profile of Core packs.** A registry is not a decision, and a pack's evaluation semantics do
  not apply. RFC 0037 instead generates the facts contracts packs read from a registry.

## Compatibility

- **Core is unchanged:** no pack, evaluator, corpus or conformance claim moves.
- **The format is new**, so there are no existing readers.
- **Adopters migrate by import.** An adopter's existing YAML moves to the subset of §7 and gains
  kind declarations, and `import` reports every construct outside the subset.
- **The stability promise in §8 binds the companion only.** Core and the rest of the tooling stay
  0.x.

## Security and privacy

- **Secrets.** A secret is never a value in a registry. `secrets` pointers must hold references,
  validation refuses a literal there, and no diagnostic carries a value. Resolution never fetches
  a secret. The start-up package reads values at run time, from the environment or mounted files
  the platform provides, and holds them in a type whose printed form is `[secret]`.
- **Denial of service.**
  - Document sizes and nesting depth are bounded.
  - Schema size, composition fan-out and `enum` size are bounded.
  - Patterns are length-bounded and must run in linear time.
  - YAML aliases are excluded, which removes the expansion attack.
  - Pointer patterns are checked against the schema, not by searching values.
- **Confusion.**
  - Exact selectors with no aliases mean a reader never guesses a version.
  - Pinning kinds by digest means a kind cannot change under a registry without the registry's
    bytes changing.
  - Excluding `oneOf` and implementation-defined keywords removes cases where two readers would
    disagree on validity.
- **Disclosure.** Owner and environment names, entry ids and kind names appear in reports and
  resolved documents. They are identifiers the author chose and may reveal internal structure,
  but they never include values.
- **Authority.** Owners are identifiers, not permissions. Validation says nothing about who may
  change an entry, and a valid registry authorizes nothing.

## Conformance

The first release stages vectors under `conformance/registry/1.0.0/`. Each vector is a set of
documents and either a report or a resolved document.

- **Positive:**
  - a minimal registry;
  - every schema keyword of §2.1 at its bounds;
  - entries limited to some environments;
  - overlays on scalars, objects and array elements;
  - resolution of every environment;
  - a deprecated kind and a deprecated member, each with a warning;
  - canonical order produced by import.
- **Negative, one per diagnostic code**, including:
  - an excluded keyword;
  - a `oneOf`;
  - a pattern with a back-reference;
  - a cyclic `$ref`;
  - a pointer pattern that matches nothing;
  - an unpinned kind, a digest mismatch, and a duplicate kind name;
  - a duplicate entry, an out-of-order entry, and an unknown owner;
  - an overlay on a non-overlayable member, a `null` in `set`, overlapping pointers, and a patch
    for an entry absent in that environment;
  - a literal at a secret pointer;
  - a dangling reference, and a reference to an entry absent in that environment;
  - over-bound counts and sizes.
- **Boundary:**
  - sizes and depths at their bound and one past it;
  - integers at ±(2^53 − 1) and one past;
  - `{n,m}` at 1 000 and 1 001;
  - 16 and 17 composition branches.
- **Adversarial:**
  - patterns that are catastrophic for backtracking engines, such as `^(a+)+$` against a long run
    of `a` followed by `b`, which a conformant reader matches in linear time (whether such
    patterns should be refused outright is Unresolved question 2);
  - deep nesting;
  - lone surrogates and duplicate members;
  - YAML inputs with aliases, tags, `yes`/`no`, leading zeros, dates, multi-documents and
    byte-order marks;
  - a secret-looking literal in a non-secret member, which is valid: it is the kind's job to
    declare secrets.

Every report vector also asserts that no value from its input appears in the report.

## Implementation

1. **The reference runtime:** `jpack registry import|validate|resolve` in Go, with the start-up
   package as a nested module.
2. **A second reader in this repository**, as for the dialect: `tools/registry_verify.py`, in
   Python's standard library plus an RE2-compatible pattern engine, implementing §§1–6 and
   checking every vector.

The two readers MUST agree on every vector before the companion is accepted at stable maturity,
which is RFC 0000's bar. A TypeScript reader (the dialect has one) is a possible third.

## Unresolved questions

1. **Review regime.** RFC 0000 and GOVERNANCE.md require a recorded adversarial review by a model
   from a different vendor for a pull request that creates an RFC. On 2026-11-16 the maintainer
   decided to waive it for the registry RFCs (0034 to 0038), as was done for RFCs 0031 and 0032.
   Each RFC gets one clean-room review by a model of the same vendor as the drafting model,
   recorded as "same vendor, not a cross-vendor claim". The waiver stays visible here because the
   companion is intended for stable maturity.
2. **Pattern ambiguity.** Linear-time matching makes catastrophic backtracking impossible in a
   conformant reader. Should patterns that backtracking engines handle catastrophically also be
   refused, to protect non-conformant consumers that reuse the kind's patterns, or is the
   linear-time requirement enough?
3. **Kind versions over time.** Settled in §2.4: the compatibility rule is part of the companion,
   and comparing two versions is a tool's check, not validation's. Open: whether the companion
   should publish that comparison as a conformance-tested operation.
4. **Cross-registry references.** References stay within one registry here. A platform with
   several registries may need to name another's entries, which is left to a later minor version.
5. **Numbers.** Allowing non-integers at all invites float disagreements between emitters' target
   languages. An alternative is integers only, with decimals as strings in a pattern.

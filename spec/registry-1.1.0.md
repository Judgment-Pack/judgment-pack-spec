# The registry, format 1.1.0: assembly, locks and signatures

## Status

This document is a companion document of the Judgment Pack specification. It is the text that
registry format `1.1.0` adds to the registry companion ([`registry.md`](registry.md), format
`1.0.0`): a federation manifest that assembles one registry from several repositories, an
assembled index that records which commit of each was read, bounds that a repository may only
tighten, a lock that pins a registry and what it depends on, and the signatures that vouch for a
lock and for each repository's part of it.

This text is registry format `1.1.0`, status `proposed`. It is normative for nothing, and no
conformance claim may cite it. It becomes normative only when a registry tag releases it,
`registry-v1.1.0`, by the companion's route (registry §13). At that release this text and
`registry.md` become one document of format `1.1.0`; until then `registry.md` is the released
`1.0.0` text, and nothing here changes it.

Its design records are [RFC 0039](../rfcs/0039-federated-registry.md) (assembly, the index and
bounds) and [RFC 0040](../rfcs/0040-registry-locks-and-signatures.md) (locks and signatures). Both
are Drafts. Every question either record left open is decided here, as §17 lists. Where this text
and a record differ, this text governs. Its merge into `registry.md` is editorial only (§17).

Not yet published: the closed schemas of the new documents, their code list and their rows. No
reader exists. The text is published first so that it can be frozen and reviewed before anything is
built.

## 1. Conventions

The key words MUST, MUST NOT, SHOULD and MAY are to be read as described in BCP 14 when, and only
when, they appear in capitals. "Registry §n" names a section of `registry.md` at format `1.0.0`;
a bare "§n" names a section of this text.

Every rule of format `1.0.0` holds unchanged. In particular, admission (registry §2.2), canonical
form and digests (registry §2.3), the YAML subset (registry §9), validation (registry §7) and
resolution (registry §8) are those of `1.0.0`, and the documents of `1.0.0` keep their selectors.

## 2. Documents and selectors

Format `1.1.0` adds these documents. Each carries an exact selector at its root, as registry §2.1
requires, and each is admitted by registry §2.2 under its own bound.

| Document | Selector member | Value | Bound | Section |
| --- | --- | --- | --- | --- |
| Federation manifest | `federationFormatVersion` | `"1.1.0"` | 256 KiB | §3 |
| Assembled index | `indexFormatVersion` | `"1.1.0"` | 8 MiB | §5 |
| Bounds | `boundsFormatVersion` | `"1.1.0"` | 256 KiB | §6 |
| Lock | `lockFormatVersion` | `"1.1.0"` | 1 MiB | §7 |
| Lock signature | `lockSignatureVersion` | `"1.1.0"` | 4 096 bytes | §10.1 |
| Source signature | `sourceSignatureVersion` | `"1.1.0"` | 4 096 bytes | §10.2 |
| Report | `reportFormatVersion` | `"1.1.0"` | as registry §7.4 | §2.1 |

A new document takes the selector `"1.1.0"`, the format that defines it. No document of format
`1.0.0` changes selector, and a reader of `1.0.0` refuses each new document by its selector
(`REG-DOC-SELECTOR`), never misreading it.

Each document a reader writes is its JCS bytes (registry §2.3), the signature documents excepted,
which are written as §10 says.

### 2.1 The report

An assembly (§4), an index check (§5.1), a lock check (§9) and a verification (§11) each write the
validation report of registry §7.4 under the selector `"1.1.0"`. A plain validation of one registry
still writes `"1.0.0"`. The report at `"1.1.0"` adds:

- the location `document` values `federation`, `index`, `bounds`, `lock`, `signature` and
  `emitter`;
- the location member `source`, the `name` of the source whose document a diagnostic is about. On
  `FED-VALUE-BOUND` it is the source whose bound the value fails. It is absent on a diagnostic of
  the manifest, of a lock, of a signature document or of the assembly as a whole;
- the codes of §12.

In registry §7.4's order, `source` sorts directly after `document`, an absent `source` as `""`.
It is part of equality: one code at one pointer in two sources is two diagnostics, each reported.
The bound, the rule against values and the agreement rule of registry §7.4 hold unchanged. A
diagnostic of §12 names pointers, sources, paths and key identifiers, never a document's content.

## 3. The federation manifest

```json
{
  "federationFormatVersion": "1.1.0",
  "registry": { "id": "https://example.invalid/registries/assembled", "version": "7.0.0" },
  "environments": ["dev", "prod"],
  "sources": [
    { "name": "billing", "role": "repository", "repository": "https://example.invalid/scm/billing",
      "environments": ["prod"], "registry": "registry/registry.json", "bounds": "registry/bounds.json" },
    { "name": "standard", "role": "standard", "repository": "https://example.invalid/scm/platform",
      "registry": "registry.json", "bounds": "bounds.json",
      "kinds": ["kinds/database.json", "kinds/db-role.json"] }
  ]
}
```

A manifest has these members and no other; `sources[].environments`, `sources[].registry` (for the
standard), `sources[].bounds` and `sources[].kinds` are optional, and the rest are required.

| Member | Form |
| --- | --- |
| `registry` | an object of exactly `id`, an absolute URI (registry §3.1), and `version`, SemVer with no build metadata: the assembled registry's |
| `environments` | the assembled registry's environments, of registry §4's form |
| `sources` | 1 to 256 sources, sorted by `name` in code-point order |
| `sources[].name` | `^[a-z][a-z0-9-]{0,62}$`, distinct |
| `sources[].role` | `standard` for exactly one source, `repository` for every other |
| `sources[].environments` | for a `repository` source only: the environments it **serves**, a non-empty subset of `environments` in their order. Absent, it serves them all. The standard serves every environment and has no such member |
| `sources[].repository` | the repository's identity (below) |
| `sources[].registry` | a path; required for a `repository` source, optional for the standard |
| `sources[].bounds` | a path |
| `sources[].kinds` | 0 to 64 distinct paths of kind declarations |

**Repository identity.** An absolute URI (RFC 3986) of at most 2 048 characters, with no
userinfo, no query and no fragment. Identities are compared as exact code points, with no case
folding, percent-decoding or Unicode normalization. An identity is not a location, and nothing
resolves it. Two sources MAY name one identity, one repository holding several services; they are
then given one commit (§4, `FED-COMMIT`).

**Paths.** A path names a file below the repository's root. It has the form registry §11.3 gives a
response path (relative, `/`-separated, no `.`, `..` or empty segment, no `\` or `:`, nothing
Windows or git reads as another name), without §11.3's `owns` condition, and is at most 512 bytes.
A path ending in `.yaml` or `.yml` is imported (registry §9) before admission, and any other path is
read as JSON. A manifest holds at most 4 096 paths in all. Within one source no two paths are equal
once case is folded (registry §11.3). Paths are otherwise compared and recorded as exact code
points, with no Unicode normalization.

The manifest names no commit. It says what to assemble, and the index records at which commits it
was assembled (§5).

**One standard.** An assembly of format `1.1.0` has exactly one standard. `role` is a closed list.
A later version may add a layer role (an organization's standard above a division's), and a `1.1.0`
reader refuses it (`FED-MANIFEST`) rather than reading the manifest as a flat assembly. §6 states
each comparison between a narrower bound and the one directly above it, so a later chain of layers
would apply it to each adjacent pair.

## 4. Assembly

**Input.** An assembly is given:

- the manifest;
- for each source, a **commit**, the full commit identifier of 40 or 64 lowercase hexadecimal
  digits (a SHA-1 or SHA-256 object id; never an abbreviation, a branch or a tag), with the bytes of
  every path the manifest names for that source;
- the list of **known assembled indexes**, and their locks (§7): those a standard owner publishes,
  and any a repository's CI holds. The list has no default, and an empty list is given as such. It
  holds at most 256 indexes and 256 locks; a longer list is `FED-KNOWN-LIMIT`, before any source is
  read.

A reader MUST NOT fetch. A path whose bytes are not given is `FED-SOURCE-MISSING`, a refusal.

**Steps**, in order. Each step reports every diagnostic of its own. An error in steps 1 to 3 ends
the assembly after that step.

1. **Manifest.** Admission (registry §2.2) and the form of §3 (`FED-MANIFEST`); then each source's
   commit (`FED-COMMIT`), which is also `FED-COMMIT` when two sources of one repository identity are
   given different commits; its repository identity (`FED-REPOSITORY`); and the presence of its
   paths (`FED-SOURCE-MISSING`).
2. **Documents.** For each path, the **content digest**: `sha256:` and the SHA-256, in lowercase
   hexadecimal, of the bytes exactly as given. Then the import of each YAML path (registry §9), and
   the admission of every document, each under its own selector and bound.
3. **Sources.**
   - Each source's registry has, as the same array, the environments the source serves (§3)
     (`FED-ENVIRONMENTS`).
   - No two sources' registries share an `id`, and none shares the assembled registry's
     (`FED-REGISTRY-DUPLICATE`).
   - No source is an assembled registry: a source whose registry's digest is the `registry.digest`,
     or whose `id` is the `registry.id`, of an index or lock in the known list is
     `FED-SOURCE-ASSEMBLED`.
4. **Kinds.** A kind declaration the standard supplies **governs** its kind name. A source that
   pins a governed kind name MUST pin, by digest, a declaration the standard supplies, or it is
   `FED-KIND-NOT-STANDARD`. A repository therefore cannot loosen a governed kind by declaring its
   own. Two sources that pin one kind name to different digests are `FED-KIND-CONFLICT`, at the
   later source's pin, because the assembled registry holds one declaration per kind name.
5. **Each source alone.** Each source's registry is validated by registry §7, with the declarations
   its own pins name, from whichever source supplies them. It has the diagnostics a `1.0.0` reader
   reports for it, with one exception: `REF-ENTRY-MISSING`, `REF-ENTRY-ABSENT-IN-ENVIRONMENT` and
   `REF-ENTRY-POINTER` on a reference whose target another source holds are deferred to step 6.
   Other references aside, assembly never makes valid what a source alone refuses.
   - Each source's secret references are checked against its own `secretScopes` only.
   - Where the standard declares `secretScopes`, a repository's scopes list, for each environment
     and store, only projects that the standard lists for the same environment and store
     (`FED-SCOPE-WIDENS`).
6. **The assembled registry.** The registry document of format `1.0.0` that holds:
   - `id` and `version` from the manifest, and its `environments`. The `version` does not change
     when only a source's commit does, so it orders no two assemblies of one manifest version; a
     lock's `serial` does (§7);
   - `owners`: the union of the sources' owners, in code-point order;
   - `kinds`: the union of the sources' pins, one per kind name, in registry §4's order;
   - `entries`: every source's entries, in registry §4's canonical order. An entry of a source that
     serves fewer environments than the manifest names is written with `environments`: its own,
     or, when it has none, the source's served environments. No entry applies where its source did
     not say it does;
   - `overlays`: one per environment that any source patches, in the order of `environments`, with
     its patches in source order and then in each source's own order;
   - `secretScopes`: the standard's, present exactly when the standard declares them. A
     repository's own scopes were applied in step 5. Without the standard's, a `1.0.0` reader sees
     the assembly's references unscoped (`REF-SECRET-UNSCOPED`).

   It is validated by registry §7 unchanged. A diagnostic about an entry, a patch or a pin is
   located in the source that holds it: `source` names that source, and `pointer` is into its
   registry document. Two sources holding one `(kind, id)` are thus `REG-ENTRY-DUPLICATE`, at the
   later in source order. The sources' own scopes are also read together, as registry §6.4's
   sharing rule reads one list: a project listed for `dev` in one source and for `prod` in another
   is `REF-SECRET-SCOPE-SHARED`, at the later listing in source order.

   **Gaps.** In every environment in which an entry applies, as the assembled registry writes it
   (its own `environments`, or, when it has none, its source's served environments), each of its
   references (registry §6.2) is satisfied there. A reference whose target, in one of those
   environments, is held only by a source that does not serve it is `FED-ENVIRONMENT-GAP` at the
   reference, with `environment` set. It is reported beside the `REF-ENTRY-ABSENT-IN-ENVIRONMENT`
   that registry §7 reports for it, so the report names the cause. An environment that no
   repository serves is not a gap: the standard serves it.
7. **Bounds** (§6): the form of every bounds document, the comparison of each repository's bounds
   with the standard's, and the check of values against both.
8. **Output.** For an assembly with no error, the reader writes the assembled registry and the
   index. It MUST NOT write either for an assembly with an error, as registry §8 writes no resolved
   registry for an invalid one. An assembled registry over registry §2.2's 8 MiB is `REG-DOC-SIZE`.

**No assembly is a source.** An assembled registry is never a source of another assembly: the outer
index would record the commit that holds the file, not the inner sources, and the inner bounds
would be checked twice or not at all. An assembled registry is an ordinary `1.0.0` document, with
no mark of its own, so step 3 detects it by identity against the known list. One the list does not
name cannot be told from a repository's own registry by its bytes. It is then read as that
repository's registry and held to the standard's governed kinds and bounds like any other; only its
inner provenance is lost (§16).

## 5. The assembled index

```json
{
  "indexFormatVersion": "1.1.0",
  "federation": { "digest": "sha256:…" },
  "registry": { "id": "https://example.invalid/registries/assembled", "version": "7.0.0", "digest": "sha256:…" },
  "sources": [
    { "name": "billing", "role": "repository", "repository": "https://example.invalid/scm/billing",
      "commit": "…",
      "documents": [
        { "path": "registry/bounds.json", "role": "bounds", "contentDigest": "sha256:…", "digest": "sha256:…" },
        { "path": "registry/registry.json", "role": "registry", "contentDigest": "sha256:…", "digest": "sha256:…" } ] },
    { "name": "standard", "role": "standard", "repository": "https://example.invalid/scm/platform",
      "commit": "…", "documents": [ … ] }
  ]
}
```

An index has these members and no other:

- `federation.digest`: the manifest's digest (registry §2.3);
- `registry`: the assembled registry's `id`, `version` and digest;
- `sources`: every source of the manifest, in its order, each with its `name`, `role` and
  `repository`, the `commit` it was read at, and `documents`, one item per path, sorted by `path`.
  Each item has `path`, `role` (`registry`, `bounds` or `kind`), `contentDigest` (§4, step 2) and
  `digest`, the admitted document's identity (registry §2.3), which pins and locks name. The two
  digests differ for a YAML file, or for a JSON file not in its JCS form: the first can be checked
  against the repository, and the second survives re-formatting.

An index has exactly one `sources` item whose `role` is `standard`, as the manifest has one
standard source. A lock check or verification refuses an index with none or with more than one
(`LOCK-INDEX-MISMATCH`, §9 step 6): the role chooses the key a source signature is checked against
(§11), and an index admitted without assembling again would otherwise let a repository's item claim
the standard's role.

The index lists documents, not entries: each entry is held by exactly one source's registry
(§4, step 6), whose identity the index pins. An auditor derives an entry's source from the
documents the index pins. The index holds identifiers, paths and digests, and no value.

### 5.1 The index check

The check is given an index, the manifest, the known list of §4, and the bytes of each source's
paths at the commits the index names. It assembles again with those commits, and the index that
assembly would write MUST equal the given index, JCS for JCS:

- a document whose content digest differs is `FED-INDEX-MISMATCH` at
  `/sources/<i>/documents/<j>/contentDigest`;
- a manifest whose digest differs is `FED-INDEX-MISMATCH` at `/federation/digest`;
- any other difference is `FED-INDEX-MISMATCH` at the first differing pointer in reading order;
- an assembly error in the second assembly fails the check, with that error's diagnostics.

A verifier that cannot read the repositories holds only the index's word for where the bytes came
from.

## 6. Bounds

### 6.1 The bounds document

```json
{
  "boundsFormatVersion": "1.1.0",
  "kinds": [
    { "kind": "db-role", "maxEntries": 40, "maxAssemblyEntries": 400,
      "fields": [
        { "pointer": "/connectionLimit", "bound": { "type": "integer", "minimum": 1, "maximum": 200 },
          "environments": { "prod": { "maximum": 100 } } },
        { "pointer": "/privileges", "bound": { "maxItems": 2, "uniqueItems": true } },
        { "pointer": "/privileges/*", "bound": { "enum": ["read", "write"] } } ] } ]
}
```

A repository's bounds for the same kind might set `"maximum": 50` at `/connectionLimit`,
`"enum": ["read"]` at `/privileges/*`, and add `{ "pointer": "/database", "bound": { "patterns":
["^entry:database/billing$"] } }`.

- `kinds` is sorted by `kind`, and each kind name appears once. Each item has `kind`, and
  optionally `maxEntries`, `maxAssemblyEntries` and `fields`. `fields` is sorted by `pointer`, and
  each pointer appears once. Each field item has `pointer` and `bound`, and optionally
  `environments` and `description`. Anything else, and any departure from these orders, is
  `FED-BOUND-FORM`.
- A bounded kind is governed (§4, step 4) or pinned by the assembled registry, or it is
  `FED-BOUND-KIND`: a bound for a misspelt kind would bound nothing and look like a limit. The
  standard bounds only kinds it governs (`FED-BOUND-KIND`), so its bounds hold for an assembly that
  pins none of them.
- `pointer` is a pointer pattern (registry §3.5), or `""` for the whole value. It MUST be
  reachable, by registry §3.5's rule, in the schema of the declaration that governs or is pinned
  for the kind (`FED-BOUND-POINTER-UNREACHABLE`), for the same reason.
- `maxEntries`, an integer from 0 to 100 000, bounds the number of entries of the kind that **one
  source** holds, in all environments.
- `maxAssemblyEntries`, an integer from 0 to 100 000, bounds the number of entries of the kind in
  the **assembled registry**. Only the standard states it: in a repository's bounds it is
  `FED-BOUND-FORM`. It is a limit only the standard owner speaks for, so it is compared with
  nothing.
- `bound` holds only the constraints of §6.2.
- `environments` holds per-environment bounds (§6.4).
- `description`, a string, is an annotation and constrains nothing.

### 6.2 What "tighter" means, constraint by constraint

A **constraint** is one row of this table. A repository's bound R is **at least as tight** as the
standard's bound S on a row when every value R's constraint admits, S's constraint admits too.

| Constraint | Members of `bound` | R is at least as tight as S when |
| --- | --- | --- |
| Type | `type` | R's type names are a subset of S's, `integer` counting as inside `number` |
| Value set | `enum`, `const` (a `const` is a one-value `enum`) | every value of R's set is in S's set, by registry §7.2's JSON equality |
| Lower bound | `minimum`, `exclusiveMinimum` | R's bound is above S's, or equal with R exclusive or S inclusive |
| Upper bound | `maximum`, `exclusiveMaximum` | R's bound is below S's, or equal with R exclusive or S inclusive |
| Length | `minLength`, `maxLength` (code points) | R's minimum ≥ S's and R's maximum ≤ S's |
| Item count | `minItems`, `maxItems` | as for length |
| Member count | `minProperties`, `maxProperties` | as for length |
| Uniqueness | `uniqueItems` | R is `true`, or S is not `true` |
| Presence | `required` | always: R's names are added to S's |
| Patterns | `patterns`, an array of patterns of the subset (registry §3.4), all of which must match | always: R's patterns are added to S's |
| Entry count | `maxEntries`, beside `fields` | R's ≤ S's |

Each member has the form registry §3.2 gives the keyword of its name; `patterns` is a non-empty
array of at most 16 distinct patterns of registry §3.4's subset.

A bound with both `minimum` and `exclusiveMinimum` takes the tighter as its lower bound, and so for
its upper bound. Numbers are compared by exact value (registry §7.2). A row S states and R does not
is **inherited**. A row R states and S does not **adds** a constraint, which is always at least as
tight. `patterns`, the one member that is not a registry §3.2 keyword, is `allOf` over `pattern`:
a pattern is narrowed by adding one.

**The comparison is per constraint, never across constraints.** When R's upper bound is looser than
S's, the widening is reported even if R's other rows rule out every value in between: for example,
R `exclusiveMaximum: 11` with `type: integer` against S `maximum: 10`. This is conservative and
decidable, since each row compares finite sets or numbers.

**Every value R names satisfies S.** Each value of R's `enum` or `const` is also checked against
S's whole bound at the same pointer, with registry §7.2's meanings. A value S refuses is a
widening: R would read as allowing it.

### 6.3 What is not comparable, and is refused

A bound holds no other member. A keyword of registry §3.2's table in a bound that §6.2's table does
not list is `FED-BOUND-NOT-COMPARABLE` at the keyword, in the standard's bounds and in a
repository's alike. Any other unknown member is `FED-BOUND-FORM`, including a keyword such as
`oneOf`, `format` or `if` that registry §3.2 names only as refused.

- **`pattern`**, as a replacement. Comparing two different patterns is language inclusion:
  decidable for this regular subset, but exponential in the worst case, under limits readers do not
  share (registry §3.4). A bound narrows a pattern by adding one to `patterns`. A later version
  does not add pattern inclusion unless a replacement is shown to be needed, and then only with
  one algorithm and one budget every reader shares.
- **`anyOf` and `not`.** A disjunction needs a case split over branches, and a negation reverses
  the test and brings pattern inclusion back.
- **`allOf`, `$ref` and `$defs`.** Bounds are flat: a field's rows are already a conjunction.
- **`properties`, `additionalProperties`, `items` and `propertyNames`.** Structure is the kind's;
  a bound reaches a nested position by its pointer. `propertyNames` would bring a pattern back.

A repository field whose pointer differs from a standard field's but can match a position that one
matches (an equal token count, and each pair of tokens equal or one of them `*`) is
`FED-BOUND-OVERLAP`: it could be compared only position by position. A field that overlaps no
standard field adds constraints, and is admitted.

### 6.4 Per-environment bounds

One bounds document may bound one environment more tightly than another.

- **Form.** A field's `environments` is an object whose members are environments of the manifest,
  each a bound of §6.2's rows within §6.3's limits. A member naming an environment the manifest does
  not name, or, in a repository's bounds, one the repository does not serve, is
  `FED-BOUND-ENVIRONMENT`: it would bound nothing. `maxEntries` and `maxAssemblyEntries` have no
  per-environment form.
- **Within one document.** Each environment's bound is at least as tight as the field's `bound`, by
  §6.2 with the environment's bound as R and the field's as S, or it is `FED-BOUND-WIDENS` at the
  environment's member.
- **The effective bound** of a field in environment `e` is its `bound`, with each row
  `environments.e` states taking that row's place, except `required` and `patterns`, whose names
  and patterns are added to the field's. Rows `environments.e` does not state are inherited. Since
  each row is at least as tight, the effective bound admits exactly the values both admit.
- **Tighten-only, per environment.** §6.5's comparison is made between the two fields' `bound`s,
  and again, for each environment the repository serves, between the two effective bounds there.
  A widening in any of them is `FED-BOUND-WIDENS`: at the repository's environment member when it
  states that row, and at its `bound` otherwise. A repository bound that is tight enough for `dev`
  but not for `prod`, where the standard is tighter, is refused.

### 6.5 The checks

1. **Comparison.** For each repository bounds document and each kind it shares with the standard's:
   `maxEntries`, then each field at a pointer the standard also bounds, row by row (§6.2), and per
   environment (§6.4). A looser row, a value S refuses, or a larger `maxEntries` is
   `FED-BOUND-WIDENS` at R's member.
2. **Values.** In each environment where step 7 of registry §7.1 checks an entry, its resolved value
   is checked at every position each applicable field's pointer matches: against the standard's
   effective bound there, and, for an entry of a repository with bounds, against that repository's.
   Both are checked, so a defect in the comparison never lets a value past the standard. A failure is
   `FED-VALUE-BOUND` at the value's position (document `value`, with `entry` and `environment`),
   with `source` naming the source whose bound it fails. A matched position absent from the value
   checks nothing, as registry §6.1 reads references; a field that should require a member states
   `required` at its parent.
3. **Entry counts.** Every source is held to the standard's `maxEntries` for the kind, and a
   repository source also to its own. A source with more entries of a kind than a `maxEntries` it is
   held to is `FED-BOUND-ENTRIES` at that source's first entry beyond it, in its registry's order.
   Once the assembled registry is made (§4, step 6), an assembly with more entries of a kind than
   the standard's `maxAssemblyEntries` is `FED-BOUND-ENTRIES` at the first entry beyond it in the
   assembled registry's order, with `source` naming the source that holds it.

## 7. The lock

```json
{
  "lockFormatVersion": "1.1.0",
  "serial": 42,
  "registry": { "id": "https://example.invalid/registries/platform", "version": "4.0.0", "digest": "sha256:…" },
  "kinds": [
    { "kind": "database", "id": "https://example.invalid/kinds/database", "version": "1.0.0", "digest": "sha256:…" },
    { "kind": "db-role", "id": "https://example.invalid/kinds/db-role", "version": "1.2.0", "digest": "sha256:…" } ],
  "resolved": [ { "environment": "dev", "digest": "sha256:…" }, { "environment": "prod", "digest": "sha256:…" } ],
  "index": { "digest": "sha256:…" },
  "sources": [
    { "name": "billing", "role": "repository", "repository": "https://example.invalid/scm/billing",
      "statement": "sha256:…", "signature": "sha256:…" },
    { "name": "standard", "role": "standard", "repository": "https://example.invalid/scm/platform",
      "statement": "sha256:…", "signature": "sha256:…" } ],
  "emitters": [
    { "source": "billing", "path": "emitters/db-roles.json", "digest": "sha256:…",
      "files": [ { "path": "gen/db-roles.sql", "mode": "0644", "digest": "sha256:…" } ] } ]
}
```

A lock has these members and no other. `index`, `sources` and `emitters` are optional, and the rest
are required.

- **`serial`**: an integer from 1 to 9 007 199 254 740 991 (2^53 − 1). Each lock of one registry
  `id` has a higher serial than the lock before it (§8), and the lock signature covers it (§11,
  Rollback).
- **`registry`**: the `id`, `version` and digest (registry §2.3) of the registry, single or
  assembled.
- **`kinds`**: the registry's pins, exactly as written and in its order. The registry's digest
  already covers them; the lock repeats them so that a lock's diff names the kind that changed. The
  check requires them equal, so they are no second source of truth.
- **`resolved`**: one item per environment of the registry, in the order of its `environments`,
  each the digest of the resolved registry (registry §8) of that environment.
- **`index`**: the digest of the assembled index (§5). A writer given an assembly MUST write it. An
  assembled registry is an ordinary `1.0.0` document, so a lock written from the registry alone
  cannot hold it, and a lock without `index` claims no provenance. A verifier that needs provenance
  requires it out of band (§9, Expected inputs).
- **`sources`**: present exactly when `index` is. One item per source of the index, in its order:
  the source's `name`, `role` and `repository` as the index gives them; `statement`, the digest of
  the source's statement (§10.2); and `signature`, the digest (registry §2.3) of the source
  signature document the writer accepted for it. So the lock, and the signature over it, name the
  repository signatures the assembly was made with.
- **`emitters`**: one item per emitter manifest (registry §11.1) the writer was given, sorted by
  `source` and then `path`: the manifest's `path` in its repository (registry §11.3's form), its
  `digest` (registry §2.3), and `files`, every file its `owns` matches, sorted by `path`, each with
  `path`, `mode` (`"0644"` or `"0755"`) and `digest` (`sha256:` over its exact bytes). In an
  assembled lock each item also has `source`, the name of the source whose repository holds it; in
  a single registry's lock it has none.

**One lock, one registry.** A lock names exactly one registry: one single registry, or one assembly
with its index. Several assemblies (one per region, for example) have one lock each, with its own
serial and signatures, and a verifier that expects several verifies each against its own expected
registry id.

**What is locked.** Through these digests, a lock pins:

- the registry's entries, overlays, owners and secret scopes;
- every kind declaration it pins;
- each environment's resolved form, which emitters and loaders read;
- the serial, which orders the locks of one registry id;
- every emitter manifest the writer was given, and each file it owns, by path, mode and digest;
- for an assembly, the index, and through the index the manifest, each source's repository, commit
  and paths, the content digest of every document read, and the bounds, per-environment bounds
  included; and, by digest, each source's statement and the source signature accepted for it.

**What is not locked:** secret values, which a registry never holds, only references pinned to a
version; facts contracts, which follow from the kinds; files no emitter the writer was given owns;
the tools that read the documents; the time; and the people who reviewed.

**Canonical bytes.** A lock is written as its JCS bytes, with at most one final line feed, which is
not part of the document (registry §2.3). A lock whose bytes, without that line feed, are not its
JCS bytes is `LOCK-NOT-CANONICAL`. So the lock's digest, its registry §2.3 identity, is also the
SHA-256 of its bytes as written, and a signature can be checked before the lock is parsed (§11). A
lock is generated: a re-formatted lock is an edited lock.

**File names.** By default, the lock of a registry document or a federation manifest named
`<name>.json` is `<name>.lock.json` in the same directory, and the lock signature of a lock named
`<file>` is `<file>.sig.json` beside it: for `registry.json`, `registry.lock.json` and
`registry.lock.json.sig.json`. A file whose name does not end in `.json` has no default lock name.
A command line MAY name either file otherwise. A source signature has no file name: it names a
commit, so it cannot be stored in that commit (§10.2).

## 8. Writing a lock

- A writer is given a registry and its kind declarations, or an assembly (§4). It MUST NOT lock a
  registry in which validation (registry §7) finds an error, or an assembly with an error
  (`LOCK-REGISTRY-INVALID`).
- It resolves every environment (registry §8) and digests each resolved registry.
- **Serial.** It is given the previous lock of the registry id, and writes `serial` one above that
  lock's; a previous lock of another registry id is `LOCK-UNEXPECTED-REGISTRY`. With no previous
  lock, it is given the first serial out of band; there is no default. A previous lock whose serial
  is 9 007 199 254 740 991 leaves no next serial, and the writer refuses (`LOCK-FORM`), since the
  lock it would write is not of its form. The lock is thus deterministic in its inputs: the
  documents, and the previous serial.
- **Source signatures.** For an assembly, it is given one source signature document per source and
  the expected signer set (§11), and verifies each as §11 does. A source whose signature does not
  verify is refused with that signature's code, and no lock is written.
- **Emitters.** For each emitter manifest it is given, it runs, or is given the outcome of, the host
  in check mode (registry §11.4) against this registry. It writes `emitters` only when every run
  exits 0, so that the files it lists are those the emitters write from this registry; otherwise it
  is `LOCK-EMITTER-MISMATCH`, and no lock is written.
- It writes the lock's JCS bytes, and never a lock over its bound.
- Writing a lock reviews and approves nothing. Writing it is how an amendment is declared, in a
  file that a reviewer sees change beside the documents it pins.

## 9. Checking a lock

**Expected inputs.** Every check, coverage and verification is also given, out of band and every
time, under the rule §11 states for the expected key: the **registry `id`** it expects, and whether
it **requires an index**. Coverage is also given the **environment** it serves, and verification
the expected signer set (with a repository key map exactly when an index is required) and its serial
record or a floor (§11). None has a default, and none is taken from a lock, a registry or a
signature document. One missing, or a registry id that is not an absolute URI, is `LOCK-EXPECTED`,
except an expected key, which is `LOCK-SIG-EXPECTED-KEY` (§11), before anything is read.

A check is given a lock, the registry, the kind declarations, the index when the lock names one, and
the emitter manifests and their files when it names emitters. Its steps:

1. **The lock.** Admission (registry §2.2), its form (`LOCK-FORM`), and its canonical bytes
   (`LOCK-NOT-CANONICAL`). Its `registry.id` is the expected id (`LOCK-UNEXPECTED-REGISTRY`), and it
   names an index when one is required (`LOCK-INDEX-REQUIRED`).
2. **The registry.** It is validated by registry §7 with the declarations given. An error is
   `LOCK-REGISTRY-INVALID`, reported beside the validation's own diagnostics.
3. **Registry.** The lock's `id`, `version` and digest are the registry's (`LOCK-REGISTRY-MISMATCH`
   at `/registry`).
4. **Kinds.** The lock's kinds equal the registry's pins, item for item (`LOCK-KINDS-MISMATCH` at the
   first item that differs, or at `/kinds` when the lengths differ).
5. **Resolved.** The environments are the registry's, in order, and each digest is that of the
   registry resolved there (`LOCK-RESOLVED-MISMATCH` at the item).
6. **Index.**
   - A lock that names an index, checked without one, is `LOCK-INDEX-MISSING`: a refusal, never a
     check that is skipped.
   - A given index is admitted. Its digest is the lock's, its `registry.digest` is the lock's
     registry digest, and it has exactly one `standard` item (§5) (`LOCK-INDEX-MISMATCH`).
   - An index given for a lock that names none is `LOCK-INDEX-UNLOCKED`, so that a caller never
     believes provenance was checked when it was not.
7. **Sources.** With the index, each `sources` item's `name`, `role` and `repository` are the
   index's, in its order, and its `statement` is the digest of the statement rebuilt from the
   index's item (§10.2); otherwise `LOCK-SOURCES-MISMATCH` at the item. The signatures are verified
   by §11, which requires the index of an assembled lock.
8. **Emitters.** A lock that names emitters, checked without them, is `LOCK-EMITTER-MISSING` at
   `/emitters`, and a manifest or file the lock lists that is not given is the same code at the
   item. A manifest or file given that differs from the lock's item, or a file the manifest's `owns`
   matches that the lock does not list, is `LOCK-EMITTER-MISMATCH` at the item.

A failure in step 1 or 2 ends the check. Steps 3 to 8 report every diagnostic of their own. The
report's `valid` is `true` exactly when there is no error. A check reads `serial` for its form only:
ordering is the verifier's (§11, Rollback).

**Provenance is a separate check.** The lock check does not assemble again. The index check (§5.1)
does, against the sources at their commits, and a verifier that wants provenance runs both and
reports both. The lock check needs no source bytes and runs where a deployment runs; the index check
needs every source at its commit. Verification already requires an assembled lock's index and
rebuilds each source statement from it (§11, Verifying), so each repository's word on its documents
and commit is part of the lock's result. What the index check adds is that those documents assemble
to the registry the lock names.

### 9.1 Coverage

A consumer that holds one environment's resolved registry and a lock (a start-up loader, an emitter
host, a deployment step) asks whether the lock covers it, for the registry id and environment it
expects. The lock is first held to step 1 of §9.

- A resolved registry is covered exactly when its `environment` is the expected environment, its
  `registry.digest` is the lock's registry digest, and its digest is the lock's `resolved` digest
  for the expected environment. Otherwise it is `LOCK-NOT-COVERED`. A `dev` resolved registry
  handed to a `prod` loader is not covered, although the lock names it.
- A generated file is covered exactly when an `emitters` item, of its source in an assembled lock,
  lists its path with its mode and digest. Otherwise it is `LOCK-NOT-COVERED`.

Coverage is computed over the same lock bytes that verification (§11) accepted, never over a lock
read again. Coverage establishes byte identity with what the lock names, and re-derives nothing. A
consumer that relies on it relies on whoever checked or signed the lock, and verifies the lock (§11)
first.

## 10. The signature documents

### 10.1 The lock signature

```json
{"algorithm":"ed25519","lockDigest":"sha256:<64 hex>","lockSignatureVersion":"1.1.0","publicKey":"<64 hex>","signature":"<128 hex>"}
```

It has exactly five members, each a string. A writer emits them in code-point order, with no white
space and one final line feed.

- **`lockSignatureVersion`**: `"1.1.0"`.
- **`algorithm`**: `"ed25519"`.
- **`publicKey`**: the signer's 32-byte Ed25519 public key, as 64 lowercase hexadecimal characters.
- **`lockDigest`**: `sha256:` and 64 lowercase hexadecimal characters, the lock's digest (§7).
- **`signature`**: the 64-byte signature, as 128 lowercase hexadecimal characters.

Each value of its form has one spelling, so an uppercase letter, a base64 spelling or another
length is refused. No name or value needs an escape, and a backslash anywhere in the document is
refused. White space between tokens is admitted when read. The document is detached: neither the
lock nor the registry carries it, and neither changes when it is made. A lock has one lock
signature (§11).

### 10.2 The source statement and the source signature

A **source statement** is the JCS of an object of exactly `repository`, `commit` and `documents`,
with the values of the index's source item (§5): the repository identity, the commit, and every
document's `path`, `role`, `contentDigest` and `digest`, in the index's order. Its digest (registry
§2.3) is what a source signature signs. It names no source name, manifest or other source: a
repository vouches for its own documents at its own commit, and for nothing else.

The source signature document has exactly five string members, written and read as the lock
signature's are, with the same forms and bound: `sourceSignatureVersion` (`"1.1.0"`), `algorithm`,
`publicKey`, `sourceDigest` (the statement's digest) and `signature`. It names a commit, so it
cannot be stored in that commit: it travels beside the bytes the assembler is given, as a CI job's
output or in a store the standard owner keeps.

### 10.3 What is signed

Each signature is Ed25519 (RFC 8032, pure, with no context string) over these ASCII bytes:

```text
judgment-pack-registry/lock-signature/1:{"lockDigest":"sha256:<64 hex>","lockSignatureVersion":"1.1.0"}
judgment-pack-registry/source-signature/1:{"sourceDigest":"sha256:<64 hex>","sourceSignatureVersion":"1.1.0"}
```

The part after each prefix is the JCS of those two members. Every signing prefix of the project is
a namespace with no `/` in it, then `/`, a name, a version and `:`. No prefix but these two starts
`judgment-pack-registry/`, and a later one in this namespace MUST have another name or version. Two
prefixes that differ in their namespace or name are neither a prefix of the other, and every message
begins with its own prefix. So no signature of another kind is a lock or source signature, even
under one key, and a lock signature is never a source signature. A message names a digest, not the
bytes: it is small and of one shape, and the digest binds the bytes.

These documents are the companion's own. They are not a pack signature, and a pack signature is not
one of them: a verifier of either class reads only its own subject, joined to the other by the same
shape and by the prefix rule above.

## 11. Keys, signing and verification

**Keys.**

- **Form.** A key is the 32-byte encoding of an Ed25519 public key. Its **key identifier** is the
  first 32 lowercase hexadecimal characters of the SHA-256 of those bytes, the form of
  [`checkpoint-witness.md`](checkpoint-witness.md) §1. A document carries the full key, never its
  identifier, so a verifier compares bytes. Reports name both.
- **Trust.** A verifier MAY trust a key exactly when `checkpoint-witness.md` §5 admits it:
  canonical, not of small order, and on the curve. A verifier MUST hold every expected key, and
  every document's key, to that rule.
- **The equation.** A signature verifies exactly when §5 of that companion says it does:
  cofactorless, with `S` below L and `R` compared byte for byte. The cofactored check is not used.
- **The expected key.** A verifier is given the key it expects, out of band, every time. It MUST NOT
  take a key from a signature document, and it has no mode that does.
- **Rotation.** The companion keeps no list of keys and knows no revocation or rotation statement.
  A rotation is a change to the verifier's expected keys, made by its operator. It leaves the serial
  record (Rollback) as it was, since the record is kept per registry id and not per key.

**The expected signer set.**

- **A single registry's lock** has one signer: the expected key, which signs the lock. Its verifier
  is given no repository key map.
- **An assembled lock** has the **standard owner's key**, which signs the lock and the standard
  source's statement, and a **repository key map**, from repository identity to key, naming the key
  that signs each repository source's statement. Both are given as the expected key is: out of band,
  every time, each key held to the trust rule (`LOCK-SIG-EXPECTED-KEY`), and none taken from a
  document. A repository source of the lock whose identity the map does not name, found once the
  lock is read (Verifying, step 6), is `LOCK-EXPECTED`. The map MAY name repositories the lock does
  not, so one map can serve several assemblies.
- **The verifier, not the lock, chooses.** A verifier given a repository key map requires an index
  (§9, Expected inputs). A map given with no index required, or an index required with no map, is
  `LOCK-EXPECTED`, before anything is read. So a lock with no index and no sources, signed by the
  standard owner's key, is `LOCK-INDEX-REQUIRED` for a verifier that holds a map, and never passes
  as a single registry's lock that needs no repository's signature.
- **One key, one role.** The standard owner's key signs the lock and the standard source's
  statement, and each repository's key signs that repository's statements only. A map that gives a
  repository the standard owner's key, or gives one key to two repository identities, keys compared
  as 32 bytes, is `LOCK-EXPECTED`, before anything is read: otherwise the set would hold with fewer
  independent keys than it names. Two repository sources of one repository identity are no second
  role: both are that repository's, and its one key signs both. The standard source shares its
  identity with no repository source the map names (Verifying, step 6). There is no option to share
  a key.
- **What each signature covers.** The lock signature covers the lock: the registry, its kinds,
  resolved forms, serial, emitters and index, and, by digest, each source's statement and accepted
  signature; that is, the assembly as a whole. A source signature covers one statement: its
  repository's documents, by path and digest, at one commit. It says nothing of the assembly, the
  bounds comparison or any other source.
- **All of the set.** An assembled lock is accepted only with its lock signature and exactly one
  source signature for each item of `sources`, each by the key the set names for it. There is no
  k-of-n rule: each signature vouches for what only its signer can, so none stands in for another.

**Signing.**

- A repository's CI signs its source statement at a commit with that repository's key. The standard
  owner's CI signs the standard source's statement, writes the lock (§8) once it holds every source's
  signature, checks it (§9), and signs it.
- A signer MUST check what it signs: a lock against the documents it names (§9), or a statement
  against its own documents at its commit. It MUST NOT sign a lock that does not check or is not
  canonical.
- The private key is the signer's to hold. Given the public key it means to sign with, a signer
  refuses, before signing anything, a private key whose public key is another.
- Signing writes a new signature document, and never replaces one.

**Reading a signature document**, of either kind, with one code per failure:

- over 4 096 bytes, not one JSON object in UTF-8, a member given twice, or a backslash:
  `LOCK-SIG-DOCUMENT`;
- a version member other than `"1.1.0"`: `LOCK-SIG-VERSION`, checked before the other members so
  that a later version is named as such;
- a member that is not defined, or one that is missing: `LOCK-SIG-MEMBER`;
- an `algorithm` other than `ed25519`: `LOCK-SIG-ALGORITHM`;
- a `publicKey` not of its form, or refused by the trust rule: `LOCK-SIG-PUBLIC-KEY`;
- a digest member or `signature` not of its form: `LOCK-SIG-FORM`.

**Checking a document** against a key and a digest, in this order, so that the reader learns the
plainer reason first: the document's key is not that key, compared as 32 bytes
(`LOCK-SIG-UNEXPECTED-KEY`); its digest member is not that digest (`LOCK-SIG-DIGEST-MISMATCH`); the
signature does not verify under that key over §10.3's message (`LOCK-SIG-INVALID`).

**Verifying.** The verifier is given the lock's bytes, the lock signature document, for an assembled
lock its index and the source signature documents, the expected signer set, the expected inputs of
§9, and its serial record or a floor (Rollback). At most the lock's `sources` count plus one
signature documents are given: before any is read, every one beyond that count is
`LOCK-SIG-EXTRA`. A signature binds only a digest: without the
expected registry id, another registry's lock signed by the same key would verify. In order:

1. **The expected inputs.** An expected key missing or refused by the trust rule is
   `LOCK-SIG-EXPECTED-KEY`. Another expected input missing, a map without an index required or the
   reverse, or one key in two roles, is `LOCK-EXPECTED`. The record for the expected registry id is
   read: one that exists and cannot be read, or is not of its form, is `LOCK-SERIAL-STATE`, and
   neither a record nor a floor is `LOCK-EXPECTED`. Each comes before the lock or any document is
   read.
2. **The lock signature**, read, then checked against the standard owner's key (for a single
   registry, the expected key) and the SHA-256 of the lock's bytes without one final line feed. No
   lock signature document is `LOCK-SIG-MISSING`, and a second is `LOCK-SIG-EXTRA`. A signature of
   another lock, moved beside this one, is `LOCK-SIG-DIGEST-MISMATCH`. The lock's bytes are not
   parsed until its signature is accepted.
3. **The lock**, held to §9's step 1, which includes the expected registry id and the index
   requirement.
4. **The serial**, against the record or the floor (Rollback).
5. **The index**, for a lock that names one. None given is `LOCK-INDEX-MISSING`, whatever else is
   given: without the index no source statement can be rebuilt, and a repository's signature at one
   commit could stand for an index that records another. The index is admitted and held to §9's
   steps 6 and 7.
6. **The source signatures.** Each source signature document given is read, and matched to the
   `sources` item whose `signature` is its digest (registry §2.3). An item that no document matches
   is `LOCK-SIG-MISSING` at the item. A document that matches no item, a second copy for one item,
   or any document given for a lock with no `sources`, is `LOCK-SIG-EXTRA`: a set with a stray
   signature is refused, not trimmed. A repository item whose `repository` the map does not name, or
   any repository item when no map is given, is `LOCK-EXPECTED`. The standard item's `repository`
   MUST NOT be one the map names (`LOCK-EXPECTED`): the standard source is signed by the standard
   owner's key alone, and a repository's identity in that item would let its statement pass without
   its own key. Each matched document is checked against the key the set names for its item
   (the standard owner's for the `standard` item, the map's for the item's `repository` otherwise)
   and against the digest of the statement rebuilt from the index's item (§10.2), never against the
   lock's `statement` member alone.
7. **The rest**: the rest of §9 when the documents are given, and coverage (§9.1) when a resolved
   registry or a file is.

The report gives every result: each signature, accepted or refused, with its key identifier, and the
lock's result. An accepted lock signature over a lock that fails any later step is a refusal of the
lock, not a pass.

**Rollback.** The lock's `serial`, which the lock signature covers, orders the locks of one registry
id.

- **What the verifier keeps.** For each registry id it has accepted a lock of, a **record**: the
  `serial` and the lock digest of the last lock it accepted. Nothing else is kept: keys and the
  other expected inputs are given each time, and one record serves every environment of the
  registry.
- **The rule.** Under a record, a lock whose serial is below the record's is
  `LOCK-SERIAL-ROLLBACK`. One whose serial equals the record's is accepted only when its digest is
  the record's: verifying the accepted lock again, after a restart for example, is no rollback.
  Another lock with that serial is `LOCK-SERIAL-CONFLICT`, two locks claiming one place. A higher
  serial is admitted, however far above: a verifier need not see every lock.
- **A floor.** A floor, given out of band, is the lowest serial the verifier may accept: a lock
  below it is `LOCK-SERIAL-ROLLBACK`, and one at or above it is admitted. Given with a record, the
  higher governs: a floor above the record's serial is held as a floor alone, and one at or below it
  changes nothing. Neither a floor nor anything else in a verification lowers a record.
- **First contact.** With no record for the registry id, a floor MUST be given; neither a record nor
  a floor is `LOCK-EXPECTED`. A floor of 1 accepts whatever lock comes first: trust on first use,
  which a verifier chooses by giving it, never by default.
- **A record that cannot be read.** A record that exists and cannot be read, or is not of its form,
  is `LOCK-SERIAL-STATE`, and the lock is not accepted. It is never taken for a first contact, and a
  floor given beside it does not stand in for it. A record gone without trace is a first contact, as
  strong as its floor, so a verifier whose records can be lost gives a floor no lower than the last
  serial it knows it accepted.
- **Recording.** Only when every step of the verification accepts does the verifier write the
  record, the lock's serial and digest, durably, before it reports the lock accepted. The write is a
  compare and set against the record read in step 1: when another process sharing the record has
  written it since, the verifier reads it again, holds the lock to the rule once more, and writes
  only if the lock still passes. So no write lowers a record, and two locks of one serial are never
  both recorded. A record it cannot write, or read again, is `LOCK-SERIAL-STATE`, and the lock is
  not accepted. A lock whose serial and digest are the record's needs no write, and a refused lock
  changes no record.
- **The state is the verifier's.** It is not in the lock, the registry or a signature, and nothing
  here writes it into a document another reader trusts. Two verifiers keep two records; verifiers
  that must agree share theirs by their own means, outside this text.

### 11.1 What an accepted set of signatures establishes

- **It establishes** that the holder of the expected key (for an assembly, the standard owner's)
  signed this lock's digest, and, for an assembly, that the holder of each repository's expected
  key, a key of its own, signed the statement rebuilt from the index's item for it: its documents,
  by digest, at the commit the index names. Through the lock's digests that covers the registry, its
  kinds, its resolved forms, the serial, the emitters and their files and, when the lock names one,
  the index; through the index, the repositories, commits, paths and content digests it claims, each
  vouched for by that repository's key. With the verifier's record, it establishes that no lock of
  that registry the verifier accepted earlier had a higher serial.
- **It does not establish:**
  - that the registry is right, tested, reviewed, approved or current;
  - when it was signed: the serial orders locks, and dates none;
  - that no newer lock exists: a verifier never shown one keeps accepting the last;
  - that the documents the repositories vouched for assemble to the registry the lock names: the
    standard owner's signature says so, and the index check (§5.1) shows it;
  - that the signer had authority over any entry, or a repository's key over its history;
  - that any secret exists;
  - that the locked files are the ones deployed.

## 12. Diagnostic codes

Every code of this section is an error, `active`. None is raised by a `1.0.0` reader, and none
changes the meaning of a `1.0.0` code. The codes of format `1.0.0` (registry §12) keep their
meanings, and are reported as registry §7 says wherever this text applies it.

### 12.1 Assembly, index and bounds

| Code | Raised when | Section |
| --- | --- | --- |
| `FED-MANIFEST` | the manifest is not of its form | §3 |
| `FED-COMMIT` | a commit is not 40 or 64 lowercase hexadecimal digits, or two sources of one repository identity are given different commits | §4 |
| `FED-REPOSITORY` | a repository identity is not an absolute URI of its bound, or holds userinfo, a query or a fragment | §3 |
| `FED-SOURCE-MISSING` | the bytes of a path the manifest names were not given | §4 |
| `FED-ENVIRONMENTS` | a source's registry's environments are not the environments it serves | §4 |
| `FED-ENVIRONMENT-GAP` | in an environment its entry applies in, a reference's target is held only by a source that does not serve it | §4 |
| `FED-KNOWN-LIMIT` | the list of known assembled indexes holds more than 256 indexes or 256 locks | §4 |
| `FED-SOURCE-ASSEMBLED` | a source's registry is one that a known assembled index or lock names | §4 |
| `FED-REGISTRY-DUPLICATE` | two registries of the assembly share an `id` | §4 |
| `FED-KIND-NOT-STANDARD` | a governed kind is pinned to a declaration the standard does not supply | §4 |
| `FED-KIND-CONFLICT` | two sources pin one kind name to different declarations | §4 |
| `FED-SCOPE-WIDENS` | a repository's secret scopes list a project the standard's do not, for that environment and store | §4 |
| `FED-BOUND-FORM` | a bounds document is not of its form, or a repository's states `maxAssemblyEntries` | §6.1 |
| `FED-BOUND-ENVIRONMENT` | a per-environment bound names an environment the manifest does not, or the repository does not serve | §6.4 |
| `FED-BOUND-KIND` | a bounded kind is neither governed nor pinned by the assembled registry, or a standard bound names a kind it does not govern | §6.1 |
| `FED-BOUND-POINTER-UNREACHABLE` | a field's pointer reaches no position of the kind's schema | §6.1 |
| `FED-BOUND-NOT-COMPARABLE` | a bound holds a keyword of §6.3 | §6.3 |
| `FED-BOUND-OVERLAP` | a repository field's pointer overlaps a standard field's without being equal to it | §6.3 |
| `FED-BOUND-WIDENS` | a bound is looser than the one it narrows on a row, or names a value that one refuses | §§6.4, 6.5 |
| `FED-BOUND-ENTRIES` | a source holds more entries of a kind than a `maxEntries` allows, or the assembly more than `maxAssemblyEntries` | §6.5 |
| `FED-VALUE-BOUND` | a resolved value fails a bound | §6.5 |
| `FED-INDEX-MISMATCH` | an index check finds a difference | §5.1 |

### 12.2 Locks and signatures

| Code | Raised when | Section |
| --- | --- | --- |
| `LOCK-EXPECTED` | an expected input is missing (the registry id, the index requirement, the environment for coverage, a repository source's key, or a floor at first contact); a repository key map is given without an index required, or the reverse; one key has two roles in the set, or the standard item's `repository` is one the map names; or the id is not an absolute URI | §§9, 11 |
| `LOCK-FORM` | the lock is not of its form, or a writer's next serial would be out of range | §§7, 8 |
| `LOCK-NOT-CANONICAL` | the lock's bytes are not its JCS bytes | §7 |
| `LOCK-UNEXPECTED-REGISTRY` | the lock's `registry.id`, or a writer's previous lock's, is not the expected registry id | §§8, 9 |
| `LOCK-INDEX-REQUIRED` | an index is required and the lock names none | §9 |
| `LOCK-REGISTRY-INVALID` | the registry, or the assembly, has an error | §§8, 9 |
| `LOCK-REGISTRY-MISMATCH` | the registry is not the one the lock names | §9 |
| `LOCK-KINDS-MISMATCH` | the lock's kinds are not the registry's pins | §9 |
| `LOCK-RESOLVED-MISMATCH` | an environment's resolved digest differs, or the environments do | §9 |
| `LOCK-INDEX-MISSING` | the lock names an index and none was given, to a check or a verification | §§9, 11 |
| `LOCK-INDEX-MISMATCH` | the index is not the one the lock names, names another registry, or does not have exactly one `standard` item | §9 |
| `LOCK-INDEX-UNLOCKED` | an index was given for a lock that names none | §9 |
| `LOCK-SOURCES-MISMATCH` | the lock's sources are not the index's, or a statement digest differs | §9 |
| `LOCK-EMITTER-MISSING` | the lock names emitters and none were given, or a manifest or file it lists was not given | §9 |
| `LOCK-EMITTER-MISMATCH` | an emitter manifest or owned file given differs from the lock's item, an owned file is absent from the lock, or a host check did not exit 0 | §§8, 9 |
| `LOCK-NOT-COVERED` | a resolved registry is not of the expected environment, or not the one the lock names for it; or a file is not one the lock lists | §9.1 |
| `LOCK-SERIAL-ROLLBACK` | the lock's serial is below the verifier's record, or below its floor | §11 |
| `LOCK-SERIAL-CONFLICT` | the lock's serial is the record's and its digest is not | §11 |
| `LOCK-SERIAL-STATE` | the verifier's record exists and cannot be read or is not of its form, or cannot be written | §11 |
| `LOCK-SIG-EXPECTED-KEY` | an expected key is missing, or one a verifier may not trust | §11 |
| `LOCK-SIG-MISSING` | the lock signature, or an item's source signature, is not given | §11 |
| `LOCK-SIG-EXTRA` | a second lock signature is given, a source signature that no item expects or that is given twice, or more source signatures than the lock's `sources` count plus one | §11 |
| `LOCK-SIG-DOCUMENT` | a signature document is over its bound, not one JSON object, repeats a member or holds a backslash | §11 |
| `LOCK-SIG-VERSION` | `lockSignatureVersion` or `sourceSignatureVersion` is not `"1.1.0"` | §11 |
| `LOCK-SIG-MEMBER` | a member is unknown or missing | §11 |
| `LOCK-SIG-ALGORITHM` | `algorithm` is not `ed25519` | §11 |
| `LOCK-SIG-PUBLIC-KEY` | `publicKey` is not of its form, or not a key a verifier may trust | §11 |
| `LOCK-SIG-FORM` | a digest member or `signature` is not of its form | §11 |
| `LOCK-SIG-UNEXPECTED-KEY` | a document's key is not the key the expected set names for it | §11 |
| `LOCK-SIG-DIGEST-MISMATCH` | the lock's bytes, or a source's statement, are not what the document names | §11 |
| `LOCK-SIG-INVALID` | a signature does not hold under its expected key | §11 |

A diagnostic of §12.2 carries no value: no key but the key identifier, which the report names for
each signature, and no document content.

## 13. Versioning and stability

- **Format `1.0.0` is unchanged.** No `1.0.0` selector, member, code, rule or row is removed or
  changes meaning, and every document of registry §2.1 keeps the selector `"1.0.0"`. A plain
  validation of one registry still writes the report at `"1.0.0"`.
- **The assembled registry is a `1.0.0` document.** A `1.0.0` reader validates and resolves it as
  registry §§7 and 8 say, and emitters and facts writers read its resolved form unchanged.
- **A source keeps its meaning.** A source validated alone by a `1.0.0` reader has the result it has
  today. One that names another source's entries is invalid alone (`REF-ENTRY-MISSING`), as today,
  and assembly defers only that (§4, step 5).
- **Additions only, under new selectors.** The new documents are format `1.1.0` documents, and a
  `1.0.0` reader refuses each by its selector. Registry §13's rules from the first stable release
  hold for them as for the documents of `1.0.0`.
- **Release.** Only on a `registry-v1.1.0` tag, with the schemas, the code list and the rows, by the
  route of registry §13 and VERSIONING.md. That release publishes this text and `registry.md` as one
  document of format `1.1.0`. Core is unchanged.
- **What a later version may add**, each under a new minor selector: a layer role in the manifest
  (§3); bound rows for a kind's `overlayable` positions, the target kinds of a reference, and the
  stores a secret may name, each a finite set compared by subset, as further rows of §6.2; and a
  key rotation statement signed by the old key (§11). None is in `1.1.0`.

## 14. Machine-readable form and rows

None is published yet. The release that publishes this text publishes, under
`conformance/registry/1.1.0/` and `schema/registry/1.1.0/`, the code list of §12 with each code's
severity and status, the closed schemas of the documents of §2, and hand-written, synthetic rows for
each class of §15, as registry §14 does for `1.0.0`. Signing rows use RFC 8032 §7.1 TEST 1's
published seed, and further published seeds for the repository and wrong-key rows, so that any
reader can reproduce them; no private key of anyone's is recorded. A verifier's record is part of a
row's input and of its expected output.

## 15. Conformance classes

| Class | Sections |
| --- | --- |
| Assembler | §§3, 4, 6 |
| Index checker | §5 |
| Lock writer | §§7, 8 |
| Lock checker | §9 |
| Lock signature verifier | §§10, 11 |

A class without rows is defined and not claimable; every class here has none yet. A claim names its
class, the exact release and its complete rows, as registry §15 says. The stable bar is two
independently written readers agreeing on every row of a class.

## 16. Security and privacy

- **Provenance is not trust.** The index records the repository, commit and path the caller says it
  read, and digests of the bytes it was given. Anyone can write an index with consistent digests.
  The index check (§5.1) lets a verifier with access to the repositories confirm the claim. Nothing
  in the index says a source was entitled to define its entries.
- **Commit ids are identifiers, not integrity.** A SHA-1 commit id can collide; the index relies on
  each document's SHA-256 content digest.
- **No secrets in an index or a lock.** A repository identity with userinfo or a query, where
  credentials and tokens are written, is refused (`FED-REPOSITORY`). An index and a lock hold
  identifiers, paths and digests only: no fetch URL, credential or value. Paths and repository names
  can describe infrastructure, as registry ids do, so neither goes further than its sources. A
  digest of a very small document, resolved registry or generated file can be confirmed by guessing
  its content.
- **Tightening is checked, and not relied on.** Values meet the standard's bounds whatever the
  comparison says (§6.5). A repository cannot loosen a governed kind by redeclaring it
  (`FED-KIND-NOT-STANDARD`), widen or borrow secret scopes (§4, step 5), or make a bound vanish by a
  misspelt kind or pointer (`FED-BOUND-KIND`, `FED-BOUND-POINTER-UNREACHABLE`). An incomparable
  construct is refused (§6.3), and a missing path is refused, never fetched or skipped.
- **An assembly as a source is refused only when it can be recognised**, by the known assembled
  indexes the assembler is given (§4). One the list does not name reads as a repository's own
  registry: the standard's kinds and bounds still hold over it, and the index then records the
  copy's commit, not the inner sources.
- **Served environments narrow, never widen.** An entry of a repository that serves fewer
  environments applies only in those (§4, step 6), and a reference that leaves them is a gap
  (`FED-ENVIRONMENT-GAP`), not a silent miss.
- **A signature says who, not whether right** (§11.1). It is evidence of an act by a key holder, not
  of a review.
- **All of a set, no stand-ins.** A repository's key signs only its own statement: one signed by
  another key than the map names is `LOCK-SIG-UNEXPECTED-KEY`, and a statement of another commit
  than the index records is `LOCK-SIG-DIGEST-MISMATCH`, because the statement is rebuilt from the
  index, without which an assembled lock is never verified (`LOCK-INDEX-MISSING`). One key in two
  roles is refused (`LOCK-EXPECTED`), so the set has as many keys as places, and a verifier holding a
  map never accepts a lock as a single registry's. A missing signature is a refusal, and a stray one
  is refused rather than ignored (`LOCK-SIG-EXTRA`). A compromised repository key can sign false
  documents for its own repository only, and they still have to pass the assembly the standard owner
  then signs.
- **A source signature never expires.** A repository's signature binds its statement, not a time
  or a serial. The standard owner can put any commit a repository ever signed into a new lock with
  a higher serial, and that lock verifies: a rollback of one source that the lock's serial does not
  catch. This is a known property of `1.1.0`, not something it fixes. A consumer that must refuse
  it pins the commits it accepts for each repository out of band, or waits for a later rule.
- **Rollback is refused by the verifier's record, not by the lock.** A signed older lock verifies as
  a signature, and its serial refuses it against a record that has seen a newer one
  (`LOCK-SERIAL-ROLLBACK`). A first contact is as strong as its floor; a record that cannot be read
  refuses (`LOCK-SERIAL-STATE`) rather than starting over; shared records are written by compare and
  set, and never lowered; and withholding a newer lock (a freeze) is not detected. A holder of the
  standard owner's key can sign any serial, a very high one included. Since nothing in a
  verification lowers a record, recovering from that is the verifier operator's act, outside this
  text: removing the record and giving a floor. A verifier that must survive it keeps a log of its
  own.
- **Expected registry and environment.** A key that signs several registries' locks makes each
  verify, and a lock names every environment's resolved registry. So the registry id and the
  environment are named by the verifier, never read from a document (§9), as the keys are.
  Provenance is likewise required by the verifier, since a lock may omit it (§7).
- **Keys.** Every expected key is mandatory, and a key the trust rule refuses is refused before
  anything is read, keys of small order, under which anyone can forge, included. A compromised key
  cannot be revoked in this format: a verifier stops expecting it.
- **Domain separation.** The prefixes keep lock and source signatures apart from each other, from
  pack signatures and witness statements, and from every other signature the project's keys make
  (§10.3).
- **Unsigned input is read little.** The lock signature is checked before the lock is parsed, and
  each signature document is bounded at 4 096 bytes.
- **Coverage and signing trust the checker.** Coverage relies on whoever checked or signed the lock,
  and a signer that signs without checking is a defect a verifier cannot see; a verifier sees only
  that the lock does not check.
- **Resources.** At most 256 sources and 4 096 paths, and at most 256 known assembled indexes and
  256 locks (§4); every document keeps its bound (§2, registry
  §2.2); the assembled registry is at most 8 MiB and the report keeps registry §7.4's cap; a lock is
  at most 1 MiB, and an assembled lock has at most 257 signatures, each one verification. Owners stay
  identities that authorize nothing (registry §16).

## 17. What this text settles, and what is open

**Settled by the maintainer's rulings of 2026-11-17**, which this text keeps as the records state
them:

- a repository may serve a subset of the environments, declared in the manifest and equal to its
  registry's, and a reference that leaves them is a gap (§§3, 4);
- one standard per assembly, with `role` a closed list (§3);
- per-environment bounds, tighten-only in each environment a repository serves (§6.4);
- no assembly is a source, detected by identity against a required list of known assembled indexes
  (§4);
- an assembled lock is accepted only with all of its signatures, one key per repository and no
  k-of-n (§11);
- a monotonic serial in the lock, with the verifier's per-registry-id record and a floor at first
  contact (§§7, 11);
- emitter manifests and their owned files are in the lock (§§7 to 9);
- one lock per registry (§7).

**Decided in this text**, where the records proposed a resolution:

- **Pattern inclusion:** not in `1.1.0`; a bound narrows a pattern by adding one (§6.3).
- **Bounds on structure:** not in `1.1.0`; a later minor version may add them as subset rows of
  §6.2 (§13).
- **Entry provenance:** the index lists documents, not entries; an entry's source is derived from
  the documents it pins (§5).
- **Selector values:** every new document takes `"1.1.0"` (§2).
- **Assembly-wide caps:** `maxAssemblyEntries`, which only the standard states, checked once on the
  assembled registry (§§6.1, 6.5).
- **File names:** `<name>.lock.json` and `<lock file>.sig.json` as defaults a command line may
  override; a source signature has none (§7).
- **One signature document for packs and registries:** no; separate documents joined by shape and
  the prefix rule (§10.3).
- **Key rotation:** the expected keys suffice; a rotation is a change to the verifier's expected
  keys, and leaves the serial record as it was (§11).
- **Provenance in `valid`:** the lock check and the index check stay apart, and both are reported
  (§9).
- **Review regime:** the two records are reviewed together in one round. RFC 0040 defines signatures
  and a rollback rule, so the round is a recorded different-vendor review unless the maintainer
  waives it. Waived by the maintainer; the review is same vendor, not a cross-vendor claim.

**Settled here**, where the records left a detail open:

- `FED-COMMIT` also refuses two sources of one repository identity given different commits (§4,
  step 1), which the records state only as "given one commit";
- the index check is given the list of known assembled indexes, since the assembly it repeats needs
  it (§5.1);
- the bounds document's members and orders are closed, and a member that is neither listed nor a
  keyword of registry §3.2's table is `FED-BOUND-FORM` (§§6.1, 6.3); `maxEntries` and
  `maxAssemblyEntries` are integers from 0 to 100 000, and `patterns` holds at most 16;
- an emitter item of a single registry's lock has no `source` (§7);
- a writer that refuses the emitters writes no lock (§8);
- a file that no `emitters` item lists is `LOCK-NOT-COVERED` (§9.1);
- a signer refuses a private key whose public key is not the one it means to sign with (§11).

**Open:**

- the schemas, the code list and the rows (§14), which follow the review of this text;
- the companion text's form once released: this text and `registry.md` become one document at
  `registry-v1.1.0` (§13). The merge into `spec/registry.md` is editorial only. No MUST, code,
  code-to-condition mapping, order or bound changes. The merged text is reviewed as a diff against
  this frozen text.

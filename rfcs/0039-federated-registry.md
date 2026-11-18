# RFC 0039: A federated registry — assembled indexes with commit provenance, and tighten-only bounds

- Status: Draft
- Type: Standards track, a proposed addition to the registry companion
  ([`spec/registry.md`](../spec/registry.md)) as registry format `1.1.0`; format `1.0.0` and every
  document it defines are unchanged
- Created: 2026-11-17
- Amended: 2026-11-17, settling four of the first draft's Unresolved questions by the maintainer's
  ruling: a repository's subset of environments (§§2 and 3), one standard per assembly (§2),
  per-environment bounds (§5) and no assembly as a source (§3); each remaining question carries a
  proposed resolution
- Related: [RFC 0034](0034-registry-profile.md) (the registry profile, and its Unresolved question
  4, cross-registry references); [RFC 0035](0035-registry-references.md) (references);
  [RFC 0040](0040-registry-locks-and-signatures.md) (locks and signatures, which pin an assembled
  index)

> **Draft.** This record is normative for nothing. Nothing is built: no schema, no row, no reader.
> The Specification below is a sketch of text that a later registry format `1.1.0` would hold.
>
> **Review standing.** [RFC 0009](0009-interim-review-regime.md) asks for a recorded adversarial
> review by a model from a different vendor on the pull request that creates an RFC. None is
> recorded for this draft, and this record does not claim one.

## Summary

Registry format `1.0.0` reads one registry document and the kind declarations it pins. Many
organizations keep their registry in pieces: a **standard** repository holds the shared kind
declarations and the limits every service must keep, and each service's repository holds its own
entries. This RFC proposes three documents and two checks, all inside the companion:

- A **federation manifest** names the sources: for each, a repository identity, the paths of its
  documents, and its role (one `standard`, the rest `repository`).
- An **assembly** reads the manifest and the bytes the caller supplies for each source at one
  commit. It writes an ordinary `1.0.0` **assembled registry**, and an **assembled index** that
  records, for every document read, the repository identity, the full commit id, the path, a digest
  of the bytes as supplied and a digest of the canonical document.
- A **bounds document** states limits per kind and field. The standard publishes one, and a
  repository's own may only **tighten** it. The comparison is defined construct by construct, and a
  construct that cannot be compared decidably is refused, never passed.

The assembly fetches nothing and holds no credential. Provenance in the index is what the caller
says it read: a claim that can be checked by fetching again, not a proof.

## Problem

1. **One registry file does not fit a many-repository organization.** A central file makes every
   service change a change to a shared repository. Per-service files drift apart, unchecked
   together: a role in one repository can name a database another repository removed.
2. **Registry `1.0.0` has no cross-registry references** (RFC 0034, Unresolved question 4). A
   service's entries that name the standard's entries cannot be validated against them.
3. **"Which bytes, from where?" has no answer.** A deployment built from several repositories
   cannot say which commit of each it read, so a reviewer cannot reproduce it, and an audit cannot
   tell which version of a service's entries was live.
4. **Organization limits have no home.** "No role holds more than 200 connections" goes into the
   kind's schema, where tightening is a new major kind version (§3.6), or is checked by hand.
5. **A narrowing nobody can check is a widening nobody sees.** A repository that restates a limit
   with a looser value relaxes it, and the value reads as permission.

The affected users are platform teams that keep standards for many services, the service teams
that hold their own entries, and the CI jobs, deployment tools and auditors that read the result.

## Evidence

- Organizations that run many services commonly keep shared definitions centrally and per-service
  configuration beside each service's code, and assemble a deployment from several repositories at
  pinned commits, usually with a bespoke script whose checks and record differ everywhere.
- Derived-profile mechanisms in data-exchange standards use this RFC's rule: a derived profile may
  restrict its base's cardinalities and value sets, never relax them, and a validator checks it.
- The companion already has what an exact comparison needs: a closed schema subset (§3.2), exact
  number comparison (§7.2), a regular pattern subset (§3.4) and canonical identity (§2.3).
  Inclusion between regular patterns is decidable but PSPACE-complete, so readers with different
  limits would disagree; this RFC does not compare two different patterns (§5.3).

## Specification

The key words MUST, MUST NOT, SHOULD and MAY are to be read as described in BCP 14 when, and only
when, they appear in capitals. Section numbers prefixed § are those of `spec/registry.md` `1.0.0`.

### 1. Documents

| Document | Selector member | Value | Bound |
| --- | --- | --- | --- |
| Federation manifest | `federationFormatVersion` | `"1.1.0"` | 256 KiB |
| Assembled index | `indexFormatVersion` | `"1.1.0"` | 8 MiB |
| Bounds | `boundsFormatVersion` | `"1.1.0"` | 256 KiB |
| Assembly report | `reportFormatVersion` | `"1.1.0"` | as §7.4 |

Each is admitted by §2.2 with its own bound, and each one a reader writes is its JCS bytes (§2.3).
The assembly report is §7.4's report under a new minor selector, adding the location `document`
values `federation`, `index` and `bounds`, the location member `source` (§6), and the `FED-` codes
of §6. In §7.4's order, `source` sorts directly after `document`, an absent `source` as `""`, and it
is part of equality: one code at one pointer in two sources is two diagnostics, each reported. A
reader that only validates still writes `"1.0.0"` (§13).

### 2. The federation manifest

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

| Member | Form |
| --- | --- |
| `registry` | `id` (an absolute URI, §3.1) and `version` (SemVer, no build metadata) of the assembled registry |
| `environments` | the assembled registry's environments, of §4's form |
| `sources` | 1 to 256 sources, sorted by `name` in code-point order |
| `sources[].name` | `^[a-z][a-z0-9-]{0,62}$`, distinct |
| `sources[].role` | `standard` for exactly one source, `repository` for every other |
| `sources[].environments` | for a `repository` source, optional: the environments it **serves**, a non-empty subset of `environments` in their order; absent, it serves them all. The standard serves every environment and has no such member |
| `sources[].repository` | the repository's identity: an absolute URI (RFC 3986) of at most 2048 characters with **no userinfo, no query and no fragment**, compared as exact code points, with no case folding, percent-decoding or Unicode normalization. It is an identity, not a location: nothing resolves it |
| `sources[].registry` | a path; required for a `repository` source, optional for the standard |
| `sources[].bounds` | a path, optional |
| `sources[].kinds` | 0 to 64 distinct paths of kind declarations |

A **path** names a file below the repository's root. It has the form §11.3 gives a response path
(relative, `/`-separated, no `.`, `..` or empty segment, no `\` or `:`, nothing Windows or git
reads as another name), without §11.3's `owns` condition, and is at most 512 bytes. A path ending in
`.yaml` or `.yml` is imported (§9) before admission, and any other path is read as JSON. A manifest
holds at most 4 096 paths in all. Within a source no two paths are equal once case is folded
(§11.3); paths are otherwise compared, and recorded, as exact code points, with no Unicode
normalization. Two sources MAY name one repository identity (one repository holding several
services), and are then given one commit (`FED-COMMIT`). The manifest names no commit: it says what
to assemble, and the index (§4) records at which commits it was assembled.

*Amended 2026-11-17, by the maintainer's ruling (first draft's question 2).* An assembly of format
`1.1.0` has exactly one standard. Layers (an organization's standard above a division's, above the
repositories) are left to a later minor version, and the format is kept open to them in two ways:
`role` is a closed list that a later version may extend with a layer role, which a `1.1.0` reader
refuses (`FED-MANIFEST`) rather than misreads as a flat assembly; and §5 states each comparison
between a narrower bound and the one directly above it, so a chain would apply it to each adjacent
pair, with the top layer governing the kinds.

### 3. Assembly

**Input.** The manifest and, for each source, a **commit** (the full commit identifier, 40 or 64
lowercase hexadecimal digits, a SHA-1 or SHA-256 object id; never an abbreviation, branch or tag)
with the bytes of every path the manifest names for it. A reader MUST NOT fetch: a path whose bytes
are not supplied is `FED-SOURCE-MISSING`, a refusal.

**Steps**, in order. Each step reports every diagnostic of its own, and an error in steps 1 to 3
ends the assembly after that step.

1. **Manifest.** Admission (§2.2) and the form of §2 (`FED-MANIFEST`), then each source's commit
   (`FED-COMMIT`), its repository identity (`FED-REPOSITORY`) and the presence of its paths
   (`FED-SOURCE-MISSING`).
2. **Documents.** For each path, the **content digest**: `sha256:` over the bytes exactly as
   supplied. Then the import of a YAML path (§9), and the admission (§2.2) of every document, each
   under its own selector and bound.
3. **Sources.** Each source's registry has, as the same array, the environments the source serves
   (§2) (`FED-ENVIRONMENTS`). No two sources' registries, and none of them and the assembled
   registry, share an `id` (`FED-REGISTRY-DUPLICATE`). No source is an assembled registry
   (`FED-SOURCE-ASSEMBLED`, below).
4. **Kinds.** A kind declaration the standard supplies **governs** its kind name. A source that pins
   a governed kind name MUST pin a declaration the standard supplies, by digest, or it is
   `FED-KIND-NOT-STANDARD`. A repository cannot loosen a governed kind by declaring its own. Two
   sources that pin one kind name to different digests are `FED-KIND-CONFLICT`, at the later
   source's pin, because the assembled registry holds one declaration per kind name.
5. **Each source alone.** Each source's registry is validated by §7, with the declarations its own
   pins name, from whichever source supplies them. It has the diagnostics a `1.0.0` reader reports
   for it, except that `REF-ENTRY-MISSING`, `REF-ENTRY-ABSENT-IN-ENVIRONMENT` and
   `REF-ENTRY-POINTER`, for a reference whose target another source holds, are deferred to step 6.
   Assembly never makes valid what a source alone refuses, other references aside. Each source's
   secret references are thus checked against its own `secretScopes` only. Where the standard
   declares them, a repository's list only projects the standard's list for the same environment and
   store (`FED-SCOPE-WIDENS`).
6. **The assembled registry.** The registry document of format `1.0.0` that holds:
   - `id` and `version` from the manifest, and its `environments`. The `version` does not change
     when only a source's commit does, so it orders no two assemblies of one manifest version;
     the lock's `serial` does (RFC 0040 §§2 and 7);
   - `owners`: the union of the sources' owners, in code-point order;
   - `kinds`: the union of the sources' pins, one per kind name, in §4's order;
   - `entries`: every source's entries, in §4's canonical order. An entry of a source that serves
     fewer environments than the manifest names is written with `environments`: its own, or, when
     it has none, the source's served environments. No entry applies where its source did not say;
   - `overlays`: one per environment that any source patches, in the order of `environments`, its
     patches in source order and then in each source's order;
   - `secretScopes`: the standard's, present when it declares them. A repository's own scopes
     were applied in step 5, so no source's listing admits another source's reference; without the
     standard's, a `1.0.0` reader sees the assembly's references unscoped (`REF-SECRET-UNSCOPED`).

   It is validated by §7 unchanged. A diagnostic about an entry, a patch or a pin is located in the
   source that holds it: `source` names that source, and `pointer` is into its registry document.
   Two sources holding one `(kind, id)` are thus `REG-ENTRY-DUPLICATE`, at the later in source
   order. The sources' own scopes are also read together as §6.4's sharing rule reads one list: a
   project listed for `dev` in one source and `prod` in another is `REF-SECRET-SCOPE-SHARED` at the
   later listing in source order.

   **Gaps.** *Amended 2026-11-17, by the maintainer's ruling (first draft's question 1).* In every
   environment a source serves, each of its entries' references (§6.2) is satisfied there. A
   reference whose target only a source that does not serve that environment holds is
   `FED-ENVIRONMENT-GAP` at the reference, with `environment` set, beside the
   `REF-ENTRY-ABSENT-IN-ENVIRONMENT` that §7 reports for it, so the report names the cause. An
   environment no repository serves is not a gap: the standard serves it.
7. **Bounds** (§5): the form of every bounds document, the comparison of each repository's bounds
   with the standard's, and the check of values against both.
8. **Output.** For an assembly with no error, the reader writes the assembled registry and the
   index. It MUST NOT write either for an assembly with an error, as §8 writes no resolved registry
   for an invalid one. The assembled registry is over its bound when it is over §2.2's 8 MiB
   (`REG-DOC-SIZE`).

**No assembly is a source.** *Amended 2026-11-17, by the maintainer's ruling (first draft's question
8).* An assembled registry is never a source of another assembly: the outer index would record the
commit that holds the file, not the inner sources, and the inner bounds would be checked twice or
not at all. An assembled registry is an ordinary `1.0.0` document with no mark of its own, so it is
detected by identity. Beside the sources, the assembler is given the assembled indexes it knows of
(those a standard owner publishes, and any a repository's CI holds), and with RFC 0040 their locks.
A source is `FED-SOURCE-ASSEMBLED` when its registry's digest is the `registry.digest`, or its `id`
the `registry.id`, of any of them, or when a path of the source holds an assembled index, a
federation manifest or a lock. An assembled registry offered without any of these cannot be told
from a repository's own by its bytes: it is then read as that repository's registry, held to the
standard's governed kinds and bounds like any other, and only its inner provenance is lost
(Security and privacy).

### 4. The assembled index

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

- `federation.digest` is the manifest's digest (§2.3); `registry` is the assembled registry's `id`,
  `version` and digest.
- `sources` lists every source by `name`, with its `role`, `repository`, the commit it was read at,
  and one item per path, sorted by `path`. Each item has `role` (`registry`, `bounds` or `kind`),
  `contentDigest`, over the bytes as supplied (what the repository holds at that commit and path),
  and `digest`, the admitted document's identity (§2.3), which pins and locks name. The two differ
  for a YAML file or a JSON file not in its JCS form: the first is checkable against the
  repository, the second survives re-formatting.
- The index lists documents, not entries: each entry is held by exactly one source's registry
  (step 6), whose identity the index pins. It holds identifiers, paths and digests, and no value.

**Index check.** The check is given an index, the manifest, and the bytes of each source's paths at
the commits the index names. It assembles again with those commits, and the index it would write
MUST equal the given index, JCS for JCS. A document whose content digest differs is
`FED-INDEX-MISMATCH` at `/sources/<i>/documents/<j>/contentDigest`; a manifest whose digest differs
is the same code at `/federation/digest`; and any other difference is the same code at the first
differing pointer in reading order. An assembly error in the re-run fails the check. A verifier
that cannot read the repositories holds only the index's word for where the bytes came from.

### 5. Bounds and the tighten-only comparison

#### 5.1 The bounds document

```json
{
  "boundsFormatVersion": "1.1.0",
  "kinds": [
    { "kind": "db-role", "maxEntries": 40,
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

- `kinds` is sorted by `kind`, and each kind name appears once. `fields` is sorted by `pointer`,
  and each pointer appears once (`FED-BOUND-FORM`).
- A bounded kind is governed (§3, step 4) or pinned by the assembled registry, or it is
  `FED-BOUND-KIND`: a bound for a misspelt kind would bound nothing and look like a limit. The
  standard bounds only governed kinds, so its bounds hold for an assembly that pins none of them.
- `pointer` is a pointer pattern (§3.5), or `""` for the whole value. It MUST be reachable, by
  §3.5's rule, in the schema of the declaration that governs or is pinned for the kind
  (`FED-BOUND-POINTER-UNREACHABLE`), for the same reason.
- `maxEntries` bounds the number of entries of the kind that **one source** holds, in all
  environments. Nothing caps a kind across the assembly (Unresolved question 5).
- `bound` holds only the constraints of §5.2.
- `environments`, optional, holds per-environment bounds (§5.5).

#### 5.2 What "tighter" means, construct by construct

A **constraint** is one row of this table. A repository's bound R is **at least as tight** as the
standard's bound S on a row when every value R's constraint admits, S's constraint admits too.

| Constraint | Members of `bound` | R is at least as tight as S when |
| --- | --- | --- |
| Type | `type` | R's type names are a subset of S's, `integer` counting as inside `number` |
| Value set | `enum`, `const` (a `const` is a one-value `enum`) | every value of R's set is in S's set, by §7.2's JSON equality |
| Lower bound | `minimum`, `exclusiveMinimum` | R's bound is above S's, or equal with R exclusive or S inclusive |
| Upper bound | `maximum`, `exclusiveMaximum` | R's bound is below S's, or equal with R exclusive or S inclusive |
| Length | `minLength`, `maxLength` (code points) | R's minimum ≥ S's and R's maximum ≤ S's |
| Item count | `minItems`, `maxItems` | as for length |
| Member count | `minProperties`, `maxProperties` | as for length |
| Uniqueness | `uniqueItems` | R is `true`, or S is not `true` |
| Presence | `required` | always: R's names are added to S's |
| Patterns | `patterns`, an array of patterns of the subset (§3.4), all of which must match | always: R's patterns are added to S's |
| Entry count | `maxEntries`, beside `fields` | R's ≤ S's |

A bound with both `minimum` and `exclusiveMinimum` takes the tighter as its lower bound, and so for
its upper bound. Numbers are compared by exact value (§7.2). A row S states and R does not is
**inherited**; a row R states and S does not **adds** a constraint, always at least as tight.
`patterns`, the one member that is not a §3.2 keyword, is `allOf` over `pattern`: a pattern is
narrowed by adding one.

**The comparison is per constraint, never across constraints.** When R's upper bound is looser than
S's, the widening is reported even if R's other rows rule out every value in between: for example,
R `exclusiveMaximum: 11` with `type: integer` against S `maximum: 10`. This is conservative and
decidable: each row is a comparison of finite sets or of numbers.

**Every value R names must satisfy S.** Each value of R's `enum` or `const` is also checked against
S's whole bound at the same pointer, with §7.2's meanings. A value S refuses is a widening: R would
read as allowing it.

#### 5.3 What is not comparable, and is refused

A bound holds no other member. A §3.2 keyword in a bound that the table does not list is
`FED-BOUND-NOT-COMPARABLE` at the keyword, in the standard's bounds and in a repository's alike:

- **`pattern`**, as a replacement. Comparing two different patterns is language inclusion:
  decidable for this regular subset, but exponential in the worst case, under limits readers do not
  share (§3.4, Linear time). A bound narrows a pattern by adding one to `patterns`.
- **`anyOf` and `not`**. A disjunction needs a case split over branches; a negation reverses the
  test and brings back pattern inclusion.
- **`allOf`, `$ref` and `$defs`**. Bounds are flat: a field's rows are already a conjunction.
- **`properties`, `additionalProperties`, `items` and `propertyNames`**. Structure is the kind's; a
  bound reaches a nested position by its pointer. `propertyNames` would bring a pattern back in.
- **Annotations** constrain nothing; a field item MAY carry `description` beside its `bound`.

A repository field whose pointer differs from a standard field's but can match a position it
matches (equal token count, each pair of tokens equal or one of them `*`) is `FED-BOUND-OVERLAP`:
it could be compared only position by position. A field that overlaps no standard field adds
constraints, and is admitted.

#### 5.4 The checks

1. **Comparison.** For each repository bounds document and each kind it shares with the standard's:
   `maxEntries`, then each field at a pointer the standard also bounds, row by row (§5.2). A
   looser row, a value S refuses, or a larger `maxEntries` is `FED-BOUND-WIDENS` at R's member.
2. **Values.** In each environment where step 7 of §7.1 checks an entry, its resolved value is
   checked at every position each applicable field's pointer matches, against the standard's
   effective bound there (§5.5) and, for an entry of a repository with bounds, against that
   repository's. Both are
   checked, so a defect in the comparison never lets a value past the standard. A failure is
   `FED-VALUE-BOUND` at the value's position (document `value`, with `entry` and `environment`),
   with `source` naming the source whose bound it fails. A source with more entries of a kind than
   a `maxEntries` it is held to is `FED-BOUND-ENTRIES` at that source's first entry beyond it.

A matched position absent from the value checks nothing (as §6.1 reads references); a field
that should require a member states `required` at its parent.

#### 5.5 Per-environment bounds

*Amended 2026-11-17, by the maintainer's ruling (first draft's question 3).* One bounds document
may bound one environment more tightly than another.

- **Form.** A field's `environments` is an object whose members are environments of the manifest,
  each a bound of §5.2's rows and §5.3's limits. A member naming an environment the manifest does
  not name, or, in a repository's bounds, one the repository does not serve, is
  `FED-BOUND-ENVIRONMENT`: it would bound nothing. `maxEntries` has no per-environment form.
- **Within one document.** Each environment's bound is at least as tight as the field's `bound`,
  by §5.2 with the environment's bound as R and the field's as S, or it is `FED-BOUND-WIDENS` at
  the environment's member.
- **The effective bound** of a field in environment `e` is its `bound` with each row
  `environments.e` states taking that row's place, except `required` and `patterns`, whose names
  and patterns are added to the field's. Rows it does not state are inherited. Since each row is
  at least as tight, the effective bound admits exactly the values both admit.
- **Tighten-only, per environment.** §5.4's comparison is made between the fields' `bound`s, and
  again, for each environment the repository serves, between the two effective bounds there. A
  widening in any of them is `FED-BOUND-WIDENS`, at the repository's environment member when it
  states that row, and at its `bound` otherwise. A repository bound that is tight enough for
  `dev` but not for `prod`, where the standard is tighter, is thus refused.

### 6. Diagnostic codes

All are errors. None is raised by a `1.0.0` reader, and none changes a `1.0.0` code's meaning.

| Code | Raised when |
| --- | --- |
| `FED-MANIFEST` | the manifest is not of its form (§2) |
| `FED-COMMIT` | a commit is not 40 or 64 lowercase hexadecimal digits |
| `FED-REPOSITORY` | a repository identity is not an absolute URI, or holds userinfo, a query or a fragment |
| `FED-SOURCE-MISSING` | the bytes of a path the manifest names were not supplied |
| `FED-ENVIRONMENTS` | a source's registry's environments are not the environments it serves |
| `FED-ENVIRONMENT-GAP` | in an environment its source serves, a reference's target is held only by a source that does not serve it |
| `FED-SOURCE-ASSEMBLED` | a source is an assembled registry, by the identities the assembler is given, or holds an index, manifest or lock |
| `FED-REGISTRY-DUPLICATE` | two registries of the assembly share an `id` |
| `FED-KIND-NOT-STANDARD` | a governed kind is pinned to a declaration the standard does not supply |
| `FED-KIND-CONFLICT` | two sources pin one kind name to different declarations |
| `FED-SCOPE-WIDENS` | a repository's secret scopes list a project the standard's do not |
| `FED-BOUND-FORM` | a bounds document is not of its form |
| `FED-BOUND-ENVIRONMENT` | a per-environment bound names an environment the manifest does not, or the repository does not serve |
| `FED-BOUND-KIND` | a bounded kind is neither governed nor pinned by the assembled registry, or a standard bound names a kind it does not govern |
| `FED-BOUND-POINTER-UNREACHABLE` | a field's pointer reaches no position of the kind's schema |
| `FED-BOUND-NOT-COMPARABLE` | a bound holds a keyword of §5.3 |
| `FED-BOUND-OVERLAP` | a repository field's pointer overlaps a standard field's without being equal to it |
| `FED-BOUND-WIDENS` | a repository's bound is looser than the standard's on a row, or names a value the standard refuses |
| `FED-BOUND-ENTRIES` | a source holds more entries of a kind than a `maxEntries` allows |
| `FED-VALUE-BOUND` | a resolved value fails a bound |
| `FED-INDEX-MISMATCH` | an index check finds a difference (§4) |

Locations follow §7.3, with `source` added: the name of the source whose document the diagnostic
is about (on `FED-VALUE-BOUND`, the source whose bound the value fails), absent on a diagnostic of
the manifest or of the assembly as a whole. They carry no value: a `FED-` diagnostic names
pointers, sources and paths, never a repository's content.

## Alternatives

- **No change.** Each organization keeps a bespoke assembly script, and its checks and its record
  of what was read stay unportable (problems 3 and 5).
- **Cross-registry references** (`entry:<registry>/<kind>/<id>`), each registry validated apart.
  This changes §6.2's grammar, a `1.0.0` meaning, and every emitter and facts writer would read
  several registries. Assembly gives one `1.0.0` registry that all of them read unchanged.
- **A registry fragment document** for repository sources. A full registry document lets a
  repository validate alone when it names no other source's entries, with no new reader.
- **Bounds as narrower kind declarations.** Narrowing would be schema subsumption over all of
  §3.2, `anyOf`, `not` and patterns included, which this RFC refuses (§5.3), and each narrowing
  would be a new kind with its own pins.
- **Conjunction only, with no comparison.** Checking values against both bounds already keeps them
  inside the standard, and this RFC does so (§5.4, 2). The comparison is added because a looser
  stated limit misleads: a reader of the repository's bounds would take `maximum: 600` as allowed.
- **Pattern inclusion by automata.** Exact, but exponential in the worst case, and two readers
  would need one algorithm and one budget (Unresolved question 1).
- **Commits pinned in the manifest.** The manifest would be a lock, changed by every service change.
  The manifest says what, the index records which, and RFC 0040's lock pins the index.

## Compatibility

- **Registry format `1.0.0` is unchanged.** No `1.0.0` selector, member, code, rule or row is
  removed or changes meaning, and every document of §2.1 keeps selector `"1.0.0"`.
- **The assembled registry is a `1.0.0` document.** A `1.0.0` reader validates and resolves it as §7
  and §8 say, and emitters and facts writers read its resolved form unchanged.
- **Additions only, under new minor selectors.** The new documents are format `1.1.0` documents,
  which a `1.0.0` reader refuses by selector (`REG-DOC-SELECTOR`) and never misreads. The assembly
  report is the validation report at `"1.1.0"`; a plain validation still writes `"1.0.0"` (§13).
- **A source's own meaning is kept.** Validated alone by a `1.0.0` reader, a source has today's
  result. One that names another source's entries is invalid alone (`REF-ENTRY-MISSING`), as today,
  and assembly defers only that (§3, step 5).
- **Release.** Only on a `registry-v1.1.0` tag, with schemas, codes and rows, by VERSIONING.md's
  route. Core is unchanged.

## Security and privacy

- **Provenance is not trust.** The index records the repository, commit and path the caller says it
  read, and digests of the bytes it was given. Anyone can write an index with consistent digests.
  The index check (§4) lets a verifier with access to the repositories confirm the claim. Nothing in
  the index says a source was entitled to define its entries.
- **Commit ids are identifiers, not integrity.** A SHA-1 commit id can collide; the index relies on
  each document's SHA-256 content digest.
- **No secrets in an index.** A repository identity with userinfo or a query, where credentials and
  tokens are written, is refused (`FED-REPOSITORY`). The index holds no fetch URL, credential or
  value. Paths and repository names can describe infrastructure, as registry ids do, so an index
  goes no further than its sources; a digest of a very small document can be confirmed by guessing.
- **Tightening is checked, and not relied on.** Values meet the standard's bounds whatever the
  comparison says (§5.4). A repository cannot loosen a governed kind by redeclaring it
  (`FED-KIND-NOT-STANDARD`), widen or borrow secret scopes (§3, step 5), or make a bound vanish by a
  misspelt kind or pointer (`FED-BOUND-KIND`, `FED-BOUND-POINTER-UNREACHABLE`).
- **Refusal, not a pass.** An incomparable construct is refused (§5.3), and a missing path is
  refused, never fetched or skipped.
- **An assembly as a source is refused only when it can be recognised.** By the identities the
  assembler is given (§3, No assembly is a source). One copied without them reads as a repository's
  own registry: the standard's kinds and bounds still hold over it, and the index then records the
  copy's commit, not the inner sources.
- **Served environments narrow, never widen.** An entry of a repository that serves fewer
  environments is written to apply only in those (§3, step 6), and a reference that leaves them
  is a gap (`FED-ENVIRONMENT-GAP`), not a silent miss.
- **Resources.** At most 256 sources and 4 096 paths; every document keeps its §2.2 bound, the
  assembled registry 8 MiB and the report §7.4's cap. Owners stay identities that authorize nothing
  (§16).

## Conformance

Rows would be hand-written and synthetic, under `conformance/registry/1.1.0/`, for two new classes:
**assembler** (§§2, 3, 5) and **index checker** (§4).

- **Positive.** A standard with kinds, bounds and a registry, and two repositories referencing its
  entries, one with bounds: the expected assembled registry, index and report. Also a YAML source
  (content digest and identity differ), overlays from two sources in one environment, a repository
  adding a field and a pattern, and an index check that passes.
- **Negative.** One row per `FED-` code, among them a commit of 39 digits, in upper case, or a
  branch name; a repository with userinfo or a query; a duplicate entry across sources; a patch of
  another source's entry (`REG-OVERLAY-ENTRY-MISSING`, in its source); a cross-source scope share;
  one repository identity at two commits; one code at one pointer in two sources, reported twice;
  a repository serving `prod` only whose entry references an entry of one serving `dev` only
  (`FED-ENVIRONMENT-GAP`); an index's registry offered as a source (`FED-SOURCE-ASSEMBLED`).
- **Served environments and per-environment bounds.** A repository serving a subset, its entries
  written with `environments`; an environment bound looser than its field's `bound`; a repository
  bound tight enough in `dev` and loose in `prod` where the standard bounds `prod` more tightly;
  `required` and `patterns` added per environment; an environment the repository does not serve.
- **The comparison table.** Each row of §5.2 tighter, equal and looser; exclusive against inclusive
  at one value; `integer` inside `number`, not the reverse; a `const` in the standard's `enum`; an
  `enum` value the standard's `maxLength` refuses; a cancelled widening, still reported.
- **Refusals and boundaries.** `pattern`, `anyOf`, `not`, `$ref`, `items`, `propertyNames` in a
  bound; overlapping and unreachable pointers; an unpinned kind; 256 and 257 sources; a manifest and
  an assembled registry at and over their bounds.
- **Adversarial.** A repository's redeclaration of a governed kind with a wider `enum` (and the same
  declaration byte for byte, admitted); a path with `..`, `\` or a leading `/`; a widening bound
  with a value inside it, which is both `FED-BOUND-WIDENS` and `FED-VALUE-BOUND`; with no standard
  scopes, a secret reference naming a project only another repository lists (`REF-SECRET-SCOPE` in
  step 5, or `REF-SECRET-UNSCOPED` when its source declares none, never scoped); a standard bound on
  a governed kind the assembly does not pin (admitted); a repository identity in another case (a
  second identity).

## Implementation

- **The reference runtime (Go)** would add `jpack registry assemble` and `jpack registry index
  check` beside its registry reader, reading files a CI job has already fetched.
- **A second, independently written reader** in this repository's Python tooling, for §15's bar.
- **Hosts** (CI systems, deployment tools) fetch each source at a commit with their own credentials
  and hand over the bytes; that is theirs, outside this text.
- **This repository** would hold the text, the `1.1.0` schemas, the code list and the rows.

## Unresolved questions

*Amended 2026-11-17.* Questions 1 (environments), 2 (layered standards), 3 (per-environment bounds)
and 8 (assemblies of assemblies) of the first draft are settled in §§2, 3 and 5 by the maintainer's
ruling. The rest are renumbered, and each carries a proposed resolution for the maintainer to
decide.

1. **Pattern inclusion.** Should a later version decide inclusion between two patterns under a
   published size budget every reader shares, so a pattern can be replaced by a narrower one?
   *Proposed resolution:* no, not in `1.1.0`. Adding a pattern already narrows, and two readers
   agree on that at no cost; inclusion needs one algorithm and one budget in every reader, and is
   worth defining only when a replacement is shown to be needed.
2. **Bounds on structure.** Should a standard also narrow a kind's `overlayable` positions, the
   target kinds of a reference, or the stores a secret may name? *Proposed resolution:* yes, in a
   later minor version, as three more rows of §5.2. Each is a finite set compared by subset, so it
   is decidable at no cost; none is needed to bound values, which is this version's scope.
3. **Entry provenance in the index.** Entries are found through their source's pinned registry. Is
   a per-entry list worth its size for an auditor? *Proposed resolution:* no. Each entry is held by
   exactly one source's registry, which the index pins by digest, so an auditor derives entry to
   source from documents it already holds, and the index stays within its bound.
4. **Selector values.** New documents take `"1.1.0"`, the format that defines them. Is `"1.0.0"`,
   a document's first version, the better reading of §13? *Proposed resolution:* keep `"1.1.0"`.
   A selector names the format that defines the document; `"1.0.0"` would name a format in which
   the document does not exist, and a `1.0.0` reader's refusal by selector would then be ambiguous.
5. **Assembly-wide caps.** `maxEntries` bounds one source. Should a bound also cap a kind's entries
   across the assembly, and how would a repository's narrower cap compare with it? *Proposed
   resolution:* yes, as a member only the standard may state (a repository stating it is
   `FED-BOUND-FORM`), checked once after step 6. An assembly-wide cap is a limit only the standard
   owner speaks for, so it needs no comparison.
6. **Review regime:** as in RFC 0034, question 1. *Proposed resolution:* review this record with
   RFC 0040 in one round. This record defines no cryptography, so a same-vendor review with the
   different-vendor review waived, as for RFCs 0034 to 0038, would fit it alone; RFC 0040's
   signatures argue for one review of both, of whichever kind RFC 0040 receives.

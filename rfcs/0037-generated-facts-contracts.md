# RFC 0037: Generated facts contracts — registry entries as pack facts, and typed facts builders

- Status: Draft
- Type: Standards track, part of the proposed registry companion (`spec/registry.md`) of
  [RFC 0034](0034-registry-profile.md), intended for stable maturity with it. Core is unchanged.
- Created: 2026-11-16
- Issue: [#339](https://github.com/Judgment-Pack/judgment-pack-spec/issues/339) (the registry line)
- Related: RFC 0034 (kinds, resolution), RFC 0035 (references), RFC 0036 (the emitter contract);
  Core §7.4 (fact comparison) and §2.2 (the decimal grammar)

> This RFC, a Draft, is normative for nothing. Core is untouched.

## Summary

A pack judges facts. A registry holds facts about a platform: which roles exist, what they may do,
and where their secrets come from. This RFC connects the two, in both directions, through one
document, the **facts contract**:

1. **Registry entries as facts.** `jpack registry facts` turns each entry of a kind, in one
   environment, into one Core facts document, and writes them as a batch (the runtime's batch
   format). A pack can then judge every production database role in CI, for example "a role with
   `admin` in production needs approval", and the outcome gate (`--require-outcome`) turns that into
   a pass or a finding.
2. **A facts contract, generated from a kind.** The contract lists every pointer such a facts
   document can hold, with its fact type (string, decimal string, boolean, array, object), whether
   it is always present, and its enumerated values where the kind's schema has them. A pack checked
   against the contract is told, before it runs, that it reads a pointer the registry never
   provides, or compares a member with a value it can never hold.
3. **Typed facts builders.** The same contract, generated from a kind or written by hand for any
   facts a service supplies, feeds a reference emitter. The emitter generates Go and TypeScript
   types and builder functions that produce valid facts documents: numbers become decimal strings
   in one normal form, and required members cannot be left out. Services that evaluate packs at run
   time build their facts through these instead of by hand.

## Problem

1. **Registry content is unjudged.** A registry's schema checks shape: "privileges is an array of
   known values". It cannot express policy such as "no production role may hold `admin` without an
   approval entry". That is a pack's job, but a pack has no defined way to read registry entries.
2. **Core's comparisons are strict, deliberately.**
   - An ordered comparison is defined only between decimal **strings**. A JSON number makes it
     `unknown` (Core §7.4).
   - Decimal equality is string equality, so `"1.0"` is not `"1.00"`.

   A facts document built by hand from JSON configuration therefore quietly yields `unknown`, or a
   wrong `not-equals`.
3. **Packs and their facts drift apart.** A pack written against one shape of facts keeps "passing"
   (every condition `unknown`, falling through to escalation) after the shape changes. Nothing
   connects a pack to a declaration of the facts it reads.
4. **Service-built facts are hand-built.** Every service that evaluates a pack repeats the same
   mistakes: numbers as numbers, missing required members, inconsistent decimal scale.

## Evidence

- The adopting organization behind RFC 0034 wants its registry's access model (roles, groups,
  grants) checked in CI by packs, through the outcome gate. Its services also evaluate packs at run
  time, with facts built in Go and TypeScript.
- The reference runtime already has static fact-type advice for packs (which fact types a pack's
  conditions can compare) and a batch evaluation format. Neither has a declared source of truth for
  the facts' shapes.

## Specification

### 1. The facts contract

```json
{
  "factsContractVersion": "1.0.0",
  "id": "https://example.invalid/facts/db-role",
  "version": "1.2.0",
  "source": { "kind": { "id": "https://example.invalid/kinds/db-role", "version": "1.2.0", "digest": "sha256:…" } },
  "facts": [
    { "pointer": "/entry/kind", "type": "string", "present": "always", "values": ["db-role"] },
    { "pointer": "/entry/id", "type": "string", "present": "always" },
    { "pointer": "/entry/owner", "type": "string", "present": "always" },
    { "pointer": "/environment", "type": "string", "present": "always", "values": ["dev", "staging", "prod"] },
    { "pointer": "/value/database", "type": "string", "present": "always" },
    { "pointer": "/value/privileges", "type": "array", "items": "string", "present": "always",
      "values": ["read", "write", "admin"] },
    { "pointer": "/value/connectionLimit", "type": "decimal", "present": "optional" },
    { "pointer": "/value/password", "type": "object", "present": "optional", "secretReference": true },
    { "pointer": "/value/password/store", "type": "string", "present": "always", "values": ["gcp-sm"] },
    { "pointer": "/value/password/scope", "type": "string", "present": "always" },
    { "pointer": "/references/~1database/value/engine", "type": "string", "present": "always" }
  ]
}
```

**Members of a contract.**

- **`source`**: either the kind the contract was generated from, by id, version and digest, or
  `{"authored": true}` for a contract written by hand (§5).
- **`facts`**: every position a facts document under the contract may hold a value, sorted by
  pointer in code-point order. Each item has:
  - **`type`**: one of `string`, `decimal` (a JSON string in Core §2.2's decimal grammar),
    `boolean`, `null`, `array` (with `items` naming the element type) or `object`;
  - **`present`**: either `always` or `optional`;
  - **`values`** (optional): the closed list of possible values (for an array, its elements' values);
  - **`secretReference`**: true on the object that stands for a secret reference (§2).

A pointer under an array that addresses an element (`/value/grants/0/role`) is written with `*` for
the index, as in RFC 0034's pointer patterns.

### 2. From a resolved entry to a facts document

For one entry of a resolved registry (RFC 0034 §5), the facts document is:

```json
{
  "registry": { "id": "…", "version": "4.0.0", "digest": "sha256:…" },
  "environment": "prod",
  "entry": { "kind": "db-role", "id": "billing-api", "owner": "team-billing" },
  "value": { "database": "entry:database/billing", "privileges": ["read", "write"],
             "connectionLimit": "120",
             "password": { "store": "gcp-sm", "scope": "example-prod" } },
  "references": { "/database": { "kind": "database", "id": "billing", "value": { "engine": "postgres" } } }
}
```

**Mapping rules.**

1. **Numbers become decimal strings in one normal form:**
   - an integer is written in base 10, with `-` for a negative and no leading zero;
   - a non-integer is written with no exponent, no trailing zero after the point, and at least one
     digit on each side of it.

   So `120` becomes `"120"`, `1.50` becomes `"1.5"`, and `0.0000001` becomes `"0.0000001"`. Every
   ordered comparison in a pack is then defined, and equal numbers are equal strings.
2. **Strings, booleans, null, arrays and objects are copied.** Order and member names are kept.
3. **A secret reference (RFC 0035) is replaced by `{"store": …, "scope": …}`.** The scope is the
   project for `gcp-sm`. A pack can judge where a secret comes from, never which secret or which
   version, and a facts document, which is recorded in decision records, never carries a reference
   string.
4. **Entry references are kept as written.** Under `references`, keyed by the pointer (in the
   referring entry's value) at which each reference sits, the facts document carries the target
   entry's `kind`, `id` and its resolved `value`, mapped by these same rules. This is one level
   deep: the target's own references are not followed. A reference with a `#pointer` carries the
   addressed value as `value`.
5. **The registry's identity and the environment are included,** so a decision record binds the
   facts to the exact registry bytes they came from.

The facts document is written in its RFC 8785 canonical form. Its size is bounded by the runtime's
facts-document limit, and an entry whose facts document would exceed that limit is reported, not
truncated.

### 3. `jpack registry facts`: batches for the gate

```
jpack registry facts --registry registry.json --kinds kinds/ --kind db-role --environment prod > prod-roles.jsonl
jpack experimental evaluate --pack-id db-role-review --batch prod-roles.jsonl --format json \
  --require-outcome approved,not-sensitive --gate-summary gate.json
```

**Output.** The command writes one batch line per entry of the kind that applies in the
environment, in canonical entry order: `{"id": "<kind>/<entry-id>", "facts": <facts document>}`.

**Options.**
- `--contract FILE` also writes the kind's generated contract.
- `--all-environments` writes the lines of every environment in the registry's order, with ids
  `<environment>:<kind>/<entry-id>`.

The registry must validate (RFC 0034 §6). An invalid registry writes no line and exits 2.

### 4. Generating a contract from a kind

For each position the kind's schema allows:
- the contract's `type` comes from the schema's `type`, with `integer` and `number` mapped to
  `decimal`;
- `present` is `always` when every path from the root to the position is `required`, and
  `optional` otherwise;
- `values` comes from `enum` or `const` when every alternative is listed;
- a position under `anyOf`, or one with more than one type, is listed once per type, and a pack
  comparing it is told it may see either.

The fixed members (`registry`, `environment`, `entry`, `references`) are always present, with their
types as in §2. `references` positions are generated from the kind's `references` patterns and the
target kinds' schemas.

The generation is deterministic, and the contract's `source.kind.digest` binds it to the kind's
bytes.

### 5. Checking a pack against a contract

A project may declare, per pack, the contract its facts follow (the reference runtime's
configuration file is the natural place, and the runtime decides the member). A contract checker
then reports, without evaluating:

| Code | Raised when the pack |
|---|---|
| `FACTS-POINTER-UNKNOWN` | reads a pointer the contract does not list |
| `FACTS-TYPE-ORDERED` | uses an ordered comparison on a pointer whose type is not `decimal` |
| `FACTS-VALUE-UNREACHABLE` | compares with `equals`, `not-equals` or `in` against a value that is outside the pointer's `values`, or of another type |

Reading an `optional` pointer needs no advisory: Core requires every rule to state `onUnknown`
(§6.5), so how a rule treats an absent fact is always declared.

These are advisories. They never change an evaluation, and Core is unchanged. They are what makes a
pack fail its CI when the registry's kinds move under it.

### 6. Typed facts builders: a reference emitter

A contract, generated (§4) or authored by hand, is the input of a reference emitter under
RFC 0036. Its manifest says `"input": "factsContracts"`, which RFC 0036 defines in its
manifest format `1.0.0` (§1) along with the request form it gives (§2): the request carries
`factsContracts`, an array of contracts, in place of `resolved`. The host's check mode applies as
for any emitter. The harness's kind-filtering and reference checks apply as RFC 0036 §5 states
for this form.

**What the emitter generates.**

- **Go:** for each contract, a struct per object position with fields of Go types, and a `Build`
  function that returns the canonical facts JSON:
  - `decimal` fields are a decimal type that renders the normal form of §2, so they cannot be a
    `float64`;
  - `always` fields are required constructor arguments;
  - `values` become typed constants, with an unexported check that refuses other values at build
    time.
- **TypeScript:** the same, as interfaces, string-literal unions for `values`, and a `buildFacts`
  function. `decimal` fields accept a string in the decimal grammar, or a `bigint`, and never a
  `number`.

A hand-authored contract lets a service that evaluates a pack at run time build its facts through
generated code, whether or not a registry is involved. The contract is then the declared interface
between the service and the pack, checked from both sides: the builder at compile time, and the
pack by §5.

## Alternatives

- **Pass registry JSON to packs as-is.** Ordered comparisons on numbers would be `unknown` (Core
  §7.4), and secret references would land in decision records. Mapping is required.
- **Coerce numbers in Core.** This was rejected by Core on purpose, and is out of scope here.
- **JSON Schema as the contract.** The contract needs Core's fact types (`decimal` is a string with
  a grammar), presence, and the fixed members. A flat pointer list is what a pack checker and a code
  generator both want. Deriving it from the kind's schema is §4.
- **Infer the contract from the pack.** This is possible for advice, but it inverts the source of
  truth. The pack would define the facts instead of the facts being declared.
- **Follow references transitively.** This was rejected for the first version: unbounded fan-out,
  cycles (RFC 0035 allows them), and facts documents that grow with the registry. One level covers
  "the role's database is Postgres".

## Compatibility

- Core is unchanged: packs and evaluators see ordinary facts documents.
- The batch format is the runtime's existing one.
- The contracts input is part of RFC 0036's first manifest and request formats, so every
  conformant host supports it. There is no older host to fall back from.

## Security and privacy

- **Secret references never reach facts or decision records.** Only the store and the scope do.
- **Facts carry entry ids, owners and configuration values.** Decision records keep facts or their
  digests, as the runtime's audit settings say. A registry whose values must not be recorded should
  not be judged with recording on, or should use the runtime's keyed digest.
- **Bounded.** References are followed one level deep, and facts-document size is bounded.
- **Builders refuse invalid values at build time**, so a service cannot send a pack a value the
  contract excludes.

## Conformance

**Vectors:**
- **Kind to contract:** every schema keyword of RFC 0034 §2.1 that affects type, presence or values;
  `anyOf` positions; and references.
- **Entry to facts:**
  - numbers at the normal-form edges (negative zero refused at registry admission, `1.0`, `100`,
    `1e-7`, and ±(2^53 − 1));
  - secret mapping;
  - one-level references, a reference with a pointer, and a cycle that is not followed;
  - the size bound.
- **Pack checks:** each advisory code, positive and negative.
- **Builders:** golden outputs under RFC 0036's harness, for Go and TypeScript, from generated and
  authored contracts.

Every vector also asserts that no secret reference string appears in a facts document.

## Implementation

1. **The reference runtime:** `jpack registry facts`, contract generation, the pack checker (beside
   its existing fact-type advice), and the builder emitter.
2. **The Python reader of RFC 0034,** for contract generation, facts mapping and the pack checks.
   Builders are reference-emitter output, so their goldens are checked by the harness, not by a
   second reader.

## Unresolved questions

1. **Where a project declares the contract a pack follows**: in the runtime's project configuration
   (product), or in the pack itself as an annotation (format).
2. **Two levels of references**, for grant → role → database. This is deferred until a case needs it.
3. **Review regime:** as in RFC 0034, question 1.

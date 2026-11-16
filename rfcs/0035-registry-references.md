# RFC 0035: Registry references — entries and pinned secrets

- Status: Draft
- Type: Standards track, part of the proposed registry companion (`spec/registry.md`) of
  [RFC 0034](0034-registry-profile.md), intended for stable maturity with it
- Created: 2026-11-16
- Issue: [#339](https://github.com/Judgment-Pack/judgment-pack-spec/issues/339) (the registry line)
- Related: RFC 0034 (the registry profile); RFC 0036 (the emitter contract)

> This RFC, a Draft, is normative for nothing. Core is untouched.

## Summary

A registry entry often points at something else: a database role names its database, a service
names the role it connects as, and a value is a secret held elsewhere. RFC 0034 lets a kind declare
which members hold references. This RFC defines what a reference is:

- **An entry reference**, `entry:<kind>/<id>`, optionally with `#<json-pointer>` into the target's
  value, names another entry of the same registry.
- **A secret reference**, `secret:<store>:<locator>`, names one **pinned version** of a secret in
  a secret store. In the first release the store is Google Cloud Secret Manager:
  `secret:gcp-sm:projects/<project>/secrets/<name>/versions/<n>`.
- **Validation checks form, not content.** It checks the grammar, that an entry target exists in
  the same environment, that every secret is pinned to a version, and that each environment's
  secrets come from that environment's own projects. Nothing fetches a secret, and resolution
  leaves every reference as written.

## Problem

1. **References in bespoke formats are strings with conventions.** A typo in a role name surfaces
   at deploy time, or at start-up.
2. **"latest" is not a secret version.** A reference that floats changes what a service runs with
   without any change to the registry, which defeats review and reproducibility.
3. **Cross-environment leaks.** A production entry pointing at a development project's secret (or
   the reverse) is a common, silent mistake. It passes every check that only looks at syntax.
4. **Secrets in lists.** Without a reference form, the path of least resistance is to paste the
   value.

## Evidence

- The adopting organization behind RFC 0034 references database roles, groups and secrets between
  entries. Its services keep their secrets in Secret Manager, and the platform they run on injects
  them as environment variables or mounted files. Its start-up loader reads those, never the store.
- Secret Manager versions are positive integers, and the alias `latest` is a moving pointer.
  Platforms that inject Secret Manager secrets accept either a pinned version or `latest`, so
  pinning is a choice the registry can enforce.

## Specification

### 1. Where references are read

A string is a reference only at a position its kind's `references` or `secrets` pointer patterns
match (RFC 0034 §2). Anywhere else, a string that begins with `entry:` or `secret:` is an ordinary
string. No escaping is needed, and no reader guesses.

At a `references` position the string MUST be an entry reference. At a `secrets` position it MUST
be a secret reference. A position matched by both patterns makes the kind declaration invalid.

### 2. Entry references

```
entry-ref = "entry:" kind "/" entry-id [ "#" pointer ]
kind      = <a kind name, RFC 0034 §2>
entry-id  = 1*128( %x21-7E except "/" and "#" )
pointer   = <an RFC 6901 JSON Pointer, at most 512 characters>
```

**In each environment where the referring entry applies:**
- `kind` MUST be one of the kinds the reference position allows.
- An entry `(kind, entry-id)` MUST exist and apply in that environment.
- If `#pointer` is present, it MUST address a value in the target's resolved value for that
  environment.

A reference may point at its own entry. Cycles are allowed, because nothing is substituted.

**Diagnostics:**

| Code | Meaning |
|---|---|
| `REF-ENTRY-FORM` | grammar |
| `REF-ENTRY-KIND` | a kind the position does not allow |
| `REF-ENTRY-MISSING` | no such entry |
| `REF-ENTRY-ABSENT-IN-ENVIRONMENT` | the entry exists but not in this environment |
| `REF-ENTRY-POINTER` | the pointer addresses nothing |

### 3. Secret references

```
secret-ref = "secret:" store ":" locator
store      = "gcp-sm"        ; the only store of format 1.0.0
locator    = "projects/" project "/secrets/" name "/versions/" version
project    = <a Google Cloud project id: 6–30 of a-z, 0-9 and "-", starting with a letter, not ending with "-">
name       = 1*255( ALPHA / DIGIT / "_" / "-" )
version    = %x31-39 *8DIGIT ; a positive integer, at most 9 digits, no leading zero
```

A reference that fails is given exactly one code, by the first of these that applies:

1. **`REF-SECRET-FORM`**: the value is not a string, does not begin with `secret:`, or has no `:`
   after the store.
2. **`REF-SECRET-STORE`**: the store is not one the companion version defines.
3. **`REF-SECRET-PIN`**: the locator has the six segments
   `projects/<p>/secrets/<n>/versions/<v>`, `<n>` matches `name`, and either `<v>` contains a
   character other than a digit (`latest`, or any alias), or `<p>` is all digits (a project number,
   which is not the project id that scopes compare).
4. **`REF-SECRET-FORM`**: anything else the grammar does not match. This includes a version of
   `0`, a version with a leading zero, a version of ten or more digits, and a malformed project id.

So "not pinned" is reserved for a reference that names a secret correctly but floats, or names
its project by number. A version number that is out of range is a form error. Further stores (other clouds' secret managers, a
Vault-compatible store) are added by later minor format versions, each with its own locator
grammar and pin rule.

### 4. Scopes: each environment's secrets come from its own projects

The registry document gains an optional member:

```json
"secretScopes": {
  "dev":     { "gcp-sm": ["example-dev"] },
  "staging": { "gcp-sm": ["example-staging"] },
  "prod":    { "gcp-sm": ["example-prod"] }
}
```

**When `secretScopes` is present:**
- Every environment MUST have an entry in it.
- A secret reference in an entry's resolved value for environment `e` MUST name a project listed
  for `e` and that store (`REF-SECRET-SCOPE`).
- No project may be listed for two environments (`REF-SECRET-SCOPE-SHARED`). Production and
  development therefore never share a project, which is the project-per-environment rule.

**When it is absent**, every secret reference is reported with the warning `REF-SECRET-UNSCOPED`.
A registry that wants this as an error says so by declaring scopes.

A secret member that must differ by environment is listed in its kind's `overlayable` (RFC 0034
§4), and each environment's overlay sets its own reference.

### 5. What nothing does

- **Validation, resolution and emitters never contact a secret store.** They never check that a
  secret or a version exists, and never read a value. Existence is the platform's concern at
  deployment, where the credentials are.
- **No reference is replaced by what it refers to.** The resolved document carries every reference
  exactly as written.
- **A diagnostic names the location of a bad reference, never the reference text.** The reference
  is not a secret, but it names infrastructure, and the report is often posted in CI logs.

## Alternatives

- **Structured objects instead of strings** (`{"$secret": {...}}`). This is unambiguous without
  pointer patterns, but it makes a reference a different JSON type from the value it stands for.
  A kind's schema would then need a union at every secret position, and emitters would need to
  special-case objects. Strings at declared positions keep schemas simple.
- **Store-neutral locators declared by the registry** (a regex per store). This is flexible, but
  "pinned" and "which project" could then not be checked by the companion. Each new store would
  be the adopter's grammar, not one two readers agree on.
- **Allowing `latest` with a warning.** This was rejected: the version pin is what makes a reviewed
  registry describe what runs.
- **Delivery in the reference** (`secret:gcp-sm:…?env=DB_PASSWORD`). How a secret reaches a
  process (an environment variable, or a mounted file) is a deployment emitter's concern
  (RFC 0036), not the reference's.

## Compatibility

The format is new. Adding stores later is additive (a new minor format version). A reader of 1.0.0
refuses a store it does not know rather than passing it.

## Security and privacy

- Pinning closes the "same registry, different secret" gap.
- Scopes close the cross-environment leak at review time.
- No component fetches or holds a value.
- Report text never includes reference strings.
- The grammars are bounded in length and linear to parse, and they are fuzzed in the reference
  implementation.
- **Residual risk.** Pinning cannot stop a store administrator from destroying or replacing a
  version. That is caught at deployment, not here.

## Conformance

**Vectors**, each run through RFC 0034's validation:
- **Valid:** entry references with and without a pointer, references that form cycles, and secret
  references at their length bounds.
- **Entry errors:**
  - every grammar error;
  - a reference to a kind the position does not allow;
  - a missing entry;
  - an entry absent in one environment and present in another, with the diagnostic only in the
    first;
  - a pointer into a value that an overlay changed.
- **Secret errors:**
  - `latest`, an alias and a project number (`REF-SECRET-PIN`), and a zero version, a leading
    zero and a 10-digit version (`REF-SECRET-FORM`), each with its expected code;
  - an unknown store;
  - a scope miss, a shared scope, and missing scopes (a warning).
- **A position matched by both `references` and `secrets`.**
- **Adversarial:**
  - very long and control-character inputs;
  - percent-encoding and Unicode lookalikes in project names (all refused by the grammar);
  - a report-level check that no reference text appears.

## Implementation

The reference runtime (Go) and the companion's Python reader of RFC 0034 both implement §§1–4.
The grammar is small enough that a third reader (TypeScript) is plausible.

## Unresolved questions

1. **Which further stores, in what order.** AWS Secrets Manager pins by version id or stage, Azure
   Key Vault by version, and Vault KV by version number. Each needs its own pin and scope rule.
2. **References to an entry in another registry.** These are deferred with RFC 0034's question 4.
3. **The scope unit for stores without projects.** Accounts, subscriptions and namespaces may need
   a different scope model.
4. **Review regime:** as in RFC 0034, question 1.

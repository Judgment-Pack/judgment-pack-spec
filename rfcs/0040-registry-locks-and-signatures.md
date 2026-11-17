# RFC 0040: Registry locks and signatures — pinning what a registry depends on, and signing the pin

- Status: Draft
- Type: Standards track, a proposed addition to the registry companion
  ([`spec/registry.md`](../spec/registry.md)) as registry format `1.1.0`; format `1.0.0` and every
  document it defines are unchanged
- Created: 2026-11-17
- Related: [RFC 0034](0034-registry-profile.md) (the registry profile);
  [RFC 0039](0039-federated-registry.md) (the assembled index a lock may pin); the key and
  signature rules of the checkpoint witness companion
  ([`spec/checkpoint-witness.md`](../spec/checkpoint-witness.md) §§1 and 5); the reference
  runtime's reviewed-set lock (its ADR-0019) and pack signatures (its ADR-0083 and
  `docs/pack-signatures.md`); issue
  [#323](https://github.com/Judgment-Pack/judgment-pack-spec/issues/323) (pack identity under
  re-serialization)

> **Draft.** This record is normative for nothing. Nothing is built: no schema, no row, no reader.
> The Specification below is a sketch of text that a later registry format `1.1.0` would hold.
>
> **Review standing.** [RFC 0009](0009-interim-review-regime.md) asks for a recorded adversarial
> review by a model from a different vendor on the pull request that creates an RFC. None is
> recorded for this draft, and this record does not claim one.

## Summary

A registry pins its kind declarations by digest, but nothing pins the registry itself, its
resolved forms, or, for an assembled registry (RFC 0039), the sources it came from. Nothing lets a
reader refuse a registry that a key it expects did not vouch for. This RFC proposes two documents
for registries, modelled on what the reference runtime already does for packs:

- A **lock** names, by digest, the registry, every kind declaration it pins, the resolved registry
  of each environment, and the assembled index when there is one. A lock check compares the lock
  with the documents it is given and refuses on any difference. Writing a lock reviews nothing: it
  makes an amendment visible in a diff.
- A **lock signature** is a detached Ed25519 signature over a context-prefixed message that names
  the lock's digest. It is the runtime's pack signature design applied to a lock, under its own
  prefix and member name. A verifier is given the key, the registry id and, for coverage, the
  environment it expects, checks the signature before it reads the lock, and never takes any of
  them from a document.

No cryptography is new. The key and signature rules are those the checkpoint witness companion
already states, and the document's shape is the pack signature's.

## Problem

1. **A deployment cannot tell which registry it holds.** A start-up loader or an emitter reads one
   environment's resolved registry. Its `registry.digest` names a registry, but nothing ties that
   registry to the one a review approved.
2. **An assembly multiplies the question.** An assembled registry (RFC 0039) comes from several
   repositories at several commits. Which assembly was reviewed, and with which sources, needs a pin
   of its own.
3. **Digests say which bytes, not whose.** A reader holding a registry and a digest learns what it
   has, not who stands behind it, so it cannot refuse a registry that the key it trusts did not
   sign.
4. **Every organization signs differently.** One signs a tarball in CI, another a checksum file in
   a release. A second tool cannot check either, and neither says what it covered.

## Evidence

- **Packs already have both halves, in the reference runtime.** Its reviewed-set lock (its
  ADR-0019) is a generated, deterministic list of digests with drift refusal. It makes an
  amendment an explicit, reviewable act without claiming to prevent one. Its pack signatures (its
  ADR-0083) are a detached document of five members, holding an Ed25519 signature over a message
  that names a digest. They are checked against an expected key before the signed bytes are parsed.
  ADR-0083 names "a signature over a set of packs rather than one file" as a reason to revisit it;
  a signature over a lock is that, one level up.
- **The specification already fixes Ed25519.** The checkpoint witness companion defines a key
  identifier, which keys a reader may trust, and the verification equation, cofactorless with a
  canonical scalar (`spec/checkpoint-witness.md` §§1 and 5). Another companion can cite those rules
  rather than restate them.
- **Ecosystems pin and sign sets.** Package managers commonly pin a resolved dependency set by
  digest in a generated lock file. Software distributions commonly sign one manifest of digests
  rather than each file.
- **Registry identity is canonical.** A registry's digest is of its JCS bytes (§2.3), so
  re-formatting a registry does not change what a lock names. For packs, whose digest is of file
  bytes, whether identity should survive re-serialization is an open question of the specification
  (see Related). The registry companion answered it for its own documents.

## Specification

The key words MUST, MUST NOT, SHOULD and MAY are to be read as described in BCP 14 when, and only
when, they appear in capitals. Section numbers prefixed § are those of `spec/registry.md` `1.0.0`.

### 1. Documents

| Document | Selector member | Value | Bound |
| --- | --- | --- | --- |
| Lock | `lockFormatVersion` | `"1.1.0"` | 1 MiB |
| Lock signature | `lockSignatureVersion` | `"1.1.0"` | 4 096 bytes |
| Lock report | `reportFormatVersion` | `"1.1.0"` | as §7.4 |

The lock is admitted by §2.2 with its bound. The lock report is the validation report under the
minor selector `"1.1.0"`, as RFC 0039 §1 has it. It adds the location `document` values `lock` and
`signature`, and the `LOCK-` codes of §8.

### 2. The lock

```json
{
  "lockFormatVersion": "1.1.0",
  "registry": { "id": "https://example.invalid/registries/platform", "version": "4.0.0", "digest": "sha256:…" },
  "kinds": [
    { "kind": "database", "id": "https://example.invalid/kinds/database", "version": "1.0.0", "digest": "sha256:…" },
    { "kind": "db-role", "id": "https://example.invalid/kinds/db-role", "version": "1.2.0", "digest": "sha256:…" } ],
  "resolved": [ { "environment": "dev", "digest": "sha256:…" }, { "environment": "prod", "digest": "sha256:…" } ],
  "index": { "digest": "sha256:…" }
}
```

A lock has these members, and no other:

- **`registry`**: the `id`, `version` and digest (§2.3) of the registry, single or assembled.
- **`kinds`**: the registry's pins, exactly as written and in its order. The registry's digest
  already covers them. The lock repeats them so that a lock's diff names the kind that changed. The
  check requires them equal, so they are no second source of truth.
- **`resolved`**: one item per environment of the registry, in the order of its `environments`,
  each the digest of the resolved registry (§8) of that environment.
- **`index`**: the digest of the assembled index (RFC 0039 §4). A writer given an assembly MUST
  write it. An assembled registry is an ordinary `1.0.0` document, so a lock written from the
  registry alone cannot hold it, and a lock without `index` claims no provenance. A verifier that
  needs provenance requires it out of band (§4, Expected inputs).

**What is locked.** Through these digests, a lock pins:

- the registry's entries, overlays, owners and secret scopes;
- every kind declaration it pins;
- each environment's resolved form, which is what emitters and loaders read;
- for an assembly, the index, and through the index the manifest, each source's repository,
  commit and paths, the content digest of every document read, and the bounds.

**What is not locked:**

- secret values, which a registry never holds, only references pinned to a version;
- emitter manifests and the files they write;
- facts contracts, which follow from the kinds;
- the tools that read the documents;
- the time, and the people who reviewed.

**Canonical bytes.** A lock is written as its JCS bytes, with at most one final line feed, which is
not part of the document (§2.3). A lock whose bytes, without that line feed, are not its JCS bytes
is `LOCK-NOT-CANONICAL`. So the lock's digest, its §2.3 identity, is also the SHA-256 of its bytes
as written, and a signature can be checked before the lock is parsed (§7). A lock is generated: a
re-formatted lock is an edited lock.

### 3. Writing a lock

- A writer is given a registry and its kind declarations, or an assembly (RFC 0039). It MUST NOT
  lock a registry that validation (§7) finds an error in, or an assembly with an error
  (`LOCK-REGISTRY-INVALID`).
- It resolves every environment (§8) and digests each resolved registry.
- It writes the lock's JCS bytes, and never a lock over its bound.
- Writing a lock reviews and approves nothing. As with the runtime's `packs lock`, running it is
  how an amendment is declared, in a file that a reviewer sees change beside the documents it
  pins.

### 4. Checking a lock

**Expected inputs.** Every check, coverage and verification is also given, out of band and every
time, under the rule §7 states for the expected key: the **registry `id`** it expects, and whether
it **requires an index**; coverage is also given the **environment** it serves. None has a default,
and none is taken from a lock, a registry or a signature document. One missing, or a registry id
that is not an absolute URI, is `LOCK-EXPECTED`, before anything is read.

A check is given a lock, the registry, the kind declarations, and the index when the lock names
one. Its steps:

1. **The lock.** Admission (§2.2), its form (`LOCK-FORM`), and its canonical bytes
   (`LOCK-NOT-CANONICAL`). Its `registry.id` is the expected id (`LOCK-UNEXPECTED-REGISTRY`), and
   it names an index when one is required (`LOCK-INDEX-REQUIRED`).
2. **The registry.** It is validated by §7 with the declarations given. An error is
   `LOCK-REGISTRY-INVALID`, reported beside the validation's own diagnostics.
3. **Registry.** The lock's `id`, `version` and digest are the registry's (`LOCK-REGISTRY-MISMATCH`
   at `/registry`).
4. **Kinds.** The lock's kinds equal the registry's pins, item for item (`LOCK-KINDS-MISMATCH` at
   the first item that differs, or at `/kinds` when the lengths differ).
5. **Resolved.** The environments are the registry's, in order, and each digest is that of the
   registry resolved there (`LOCK-RESOLVED-MISMATCH` at the item).
6. **Index.**
   - A lock that names an index, checked without one, is `LOCK-INDEX-MISSING`: a refusal, never a
     check that is skipped.
   - A supplied index is admitted. Its digest must be the lock's, and its `registry.digest` must be
     the lock's registry digest (`LOCK-INDEX-MISMATCH`).
   - An index supplied for a lock that names none is `LOCK-INDEX-UNLOCKED`, so that a caller never
     believes provenance was checked when it was not.

A failure in step 1 or 2 ends the check. Steps 3 to 6 report every diagnostic of their own. The
report's `valid` is `true` exactly when there is no error.

The check does not re-run the assembly. RFC 0039's index check does that, against the sources at
their commits, and a verifier that wants provenance runs both.

**Coverage.** A consumer holding one environment's resolved registry and a lock (a start-up loader,
an emitter host, a deployment step) asks whether the lock covers it, for the registry id and
environment it expects. The lock is first held to step 1. The resolved registry is covered exactly
when its `environment` is the expected environment, its `registry.digest` is the lock's registry
digest, and its digest is the lock's `resolved` digest for the expected environment; otherwise it
is `LOCK-NOT-COVERED`. A `dev` resolved registry handed to a `prod` loader is thus not covered,
although the lock names it. This is the runtime's `packs covers` question asked of a registry.
Coverage establishes byte identity with what the lock names, and it re-derives nothing. A consumer
that relies on it relies on whoever checked or signed the lock.

### 5. The signature document

```json
{"algorithm":"ed25519","lockDigest":"sha256:<64 hex>","lockSignatureVersion":"1.1.0","publicKey":"<64 hex>","signature":"<128 hex>"}
```

It has exactly five members, each a string. A writer emits them in code-point order, with no white
space and one final line feed. This is the runtime's pack signature document, with `packDigest`
and `signatureVersion` replaced, and with the same algorithm and spelling:

- **`lockSignatureVersion`**: `"1.1.0"`.
- **`algorithm`**: `"ed25519"`.
- **`publicKey`**: the signer's 32-byte Ed25519 public key, as 64 lowercase hexadecimal characters.
- **`lockDigest`**: `sha256:` and 64 lowercase hexadecimal characters, the lock's digest (§2).
- **`signature`**: the 64-byte signature, as 128 lowercase hexadecimal characters.

Each value of its form has one spelling, so an uppercase letter, a base64 spelling or another
length is refused. No name or value needs an escape, and a backslash anywhere in the document is
refused. White space between tokens is admitted. The document is detached: neither the lock nor the
registry carries it, and neither changes when it is made. Several documents, by several keys, may
sign one lock.

### 6. What is signed

The signature is Ed25519 (RFC 8032, pure, with no context string) over these ASCII bytes:

```text
judgment-pack-registry/lock-signature/1:{"lockDigest":"sha256:<64 hex>","lockSignatureVersion":"1.1.0"}
```

The part after the prefix is the JCS of those two members. Every signing prefix of the project is
a namespace with no `/` in it (`judgment-pack`, `judgment-pack-runtime`, `judgment-pack-gateway`),
then `/`, a name, a version and `:`. No other prefix starts `judgment-pack-registry/`, and a later
one in this namespace MUST have another name or version. Two prefixes of different namespaces are
neither a prefix of the other, and every message begins with its own prefix, so no signature of
another kind is a lock signature, even under one key, and the reverse holds too. The message names
the digest, not the bytes: it is small and of one shape, and the digest binds the bytes.

### 7. Keys, signing and verification

**Keys.**

- **Form.** A key is the 32-byte encoding of an Ed25519 public key. Its **key identifier** is the
  first 32 lowercase hexadecimal characters of the SHA-256 of those bytes, the form of
  `spec/checkpoint-witness.md` §1 and the identifier the runtime reports beside a pack signature.
  The document carries the full key, never its identifier, so a verifier compares bytes. Reports
  name both.
- **Trust.** A verifier MAY trust a key exactly when `spec/checkpoint-witness.md` §5 admits it:
  canonical, not of small order, and on the curve. A verifier MUST hold the expected key, and the
  document's key, to that rule.
- **The equation.** A signature verifies exactly when §5 of that companion says it does:
  cofactorless, with `S` below L and `R` compared byte for byte. The cofactored check is not used.
- **The expected key.** A verifier is given the key it expects, out of band, every time. It MUST
  NOT take a key from the signature document, and it has no mode that does. How keys are
  distributed, rotated and retired is the verifier's concern. The companion keeps no list of keys
  and knows no revocation.

**Signing.**

- A signer MUST check the lock (§4) against the documents it names, and MUST NOT sign a lock that
  does not check or is not canonical. A signature over a lock nobody checked vouches for a digest
  blindly.
- The private key is the signer's to hold. The runtime holds a pack-signing seed as it holds an
  audit trail's key, and a registry signer would do the same. Given the public key it means to sign
  with, it refuses, before signing anything, a seed whose public key is another.
- Signing writes a new signature document, and never replaces one.

**Verifying.** The verifier is given the lock's bytes, the signature document's bytes, the
expected key and the expected inputs of §4 (registry id, and whether an index is required). A
signature binds only a lock's digest: without the expected registry id, another registry's lock
signed by the same key would verify. The order is the pack signature's:

1. no expected key, or one the trust rule refuses: `LOCK-SIG-EXPECTED-KEY`, and an expected input
   missing: `LOCK-EXPECTED`, each before anything is read;
2. the document, read strictly, with one code per failure:
   - over 4 096 bytes, not one JSON object in UTF-8, a member given twice, or a backslash:
     `LOCK-SIG-DOCUMENT`;
   - a `lockSignatureVersion` other than `"1.1.0"`: `LOCK-SIG-VERSION`, checked before the other
     members so that a later version is named as such;
   - a member that is not defined, or one that is missing: `LOCK-SIG-MEMBER`;
   - an `algorithm` other than `ed25519`: `LOCK-SIG-ALGORITHM`;
   - a `publicKey` not of its form, or refused by the trust rule: `LOCK-SIG-PUBLIC-KEY`;
   - a `lockDigest` or `signature` not of its form: `LOCK-SIG-FORM`;
3. the document's key is not the expected key, compared as 32 bytes: `LOCK-SIG-UNEXPECTED-KEY`;
4. the SHA-256 of the lock's bytes, without one final line feed, is not `lockDigest`:
   `LOCK-SIG-DIGEST-MISMATCH`. This is also how a signature of another lock, moved beside this one,
   is refused;
5. the signature does not verify under the expected key over §6's message: `LOCK-SIG-INVALID`.

Steps 3 and 4 come before step 5, so the reader learns the plainer reason.

**After a verdict.** The lock's bytes are not parsed until the signature is accepted. Then the lock
is held to §4's step 1, which includes the expected registry id and the index requirement, and to
the rest of §4 when the documents are given, or to coverage when a resolved registry is. The report
gives both results: the signature accepted, with its key and key identifier, and the lock's result.
An accepted signature over a lock that fails any of these is a refusal of the lock, not a pass.

### 8. Diagnostic codes

All are errors. The right-hand column is the runtime's pack signature code that the same failure
gives, so that one implementation can serve both.

| Code | Raised when | Pack signature code |
| --- | --- | --- |
| `LOCK-EXPECTED` | an expected registry id, index requirement or environment (coverage) is missing, or the id is not an absolute URI | — |
| `LOCK-FORM` | the lock is not of its form | — |
| `LOCK-NOT-CANONICAL` | the lock's bytes are not its JCS bytes | — |
| `LOCK-UNEXPECTED-REGISTRY` | the lock's `registry.id` is not the expected registry id | — |
| `LOCK-INDEX-REQUIRED` | an index is required and the lock names none | — |
| `LOCK-REGISTRY-INVALID` | the registry, or the assembly, has an error | `-PACK-NOT-VALID` (signing) |
| `LOCK-REGISTRY-MISMATCH` | the registry is not the one the lock names | — |
| `LOCK-KINDS-MISMATCH` | the lock's kinds are not the registry's pins | — |
| `LOCK-RESOLVED-MISMATCH` | an environment's resolved digest differs, or the environments do | — |
| `LOCK-INDEX-MISSING` | the lock names an index and none was given | — |
| `LOCK-INDEX-MISMATCH` | the index is not the one the lock names, or names another registry | — |
| `LOCK-INDEX-UNLOCKED` | an index was given for a lock that names none | — |
| `LOCK-NOT-COVERED` | a resolved registry is not of the expected environment, or not the one the lock names for it | `document-drift` (`packs covers`) |
| `LOCK-SIG-EXPECTED-KEY` | no expected key, or one a verifier may not trust | `-EXPECTED-KEY` |
| `LOCK-SIG-DOCUMENT` | the document is over its bound, not one JSON object, repeats a member or holds a backslash | `-TOO-LARGE`, `-MALFORMED`, `-DUPLICATE-MEMBER` |
| `LOCK-SIG-VERSION` | `lockSignatureVersion` is not `"1.1.0"` | `-VERSION` |
| `LOCK-SIG-MEMBER` | a member is unknown or missing | `-UNKNOWN-MEMBER`, `-MISSING-MEMBER` |
| `LOCK-SIG-ALGORITHM` | `algorithm` is not `ed25519` | `-ALGORITHM` |
| `LOCK-SIG-PUBLIC-KEY` | `publicKey` is not of its form, or not a key a verifier may trust | `-PUBLIC-KEY` |
| `LOCK-SIG-FORM` | `lockDigest` or `signature` is not of its form | `-PACK-DIGEST`, `-VALUE` |
| `LOCK-SIG-UNEXPECTED-KEY` | the document's key is not the expected key | `-UNEXPECTED-KEY` |
| `LOCK-SIG-DIGEST-MISMATCH` | the lock's bytes are not the bytes the document names | `-DIGEST-MISMATCH` |
| `LOCK-SIG-INVALID` | the signature does not hold under the expected key | `-INVALID` |

A diagnostic carries no value: no key but the key identifier, which the report names for an
accepted signature, and no document content.

### 9. What an accepted signature establishes

- **It establishes** that the holder of the expected key signed this lock's digest. Through the
  lock's digests, that covers the registry, its kinds, its resolved forms and, when the lock names
  one, the index. Through the index, it covers the repositories, commits, paths and content digests
  the index claims.
- **It does not establish**:
  - that the registry is right, tested, reviewed, approved or current;
  - when it was signed, because the document holds no time;
  - that the signer had authority over any entry or source;
  - that the index's provenance is true;
  - that any secret exists;
  - that any emitted file matches.

## Alternatives

- **Sign the registry document, with no lock.** A registry's digest covers its pins. It does not
  cover the resolved forms consumers hold, or an assembly's provenance, and an assembled registry is
  read from several documents.
- **Sign each document.** That gives many signatures and nothing that binds the set. A reviewed
  registry mixed with another registry's kinds would verify.
- **Put the signature inside the registry or the lock.** It would change the closed registry
  document of `1.0.0`, and a document cannot sign its own bytes.
- **A new envelope or algorithm**, such as a general-purpose signing envelope, or a keyless signing
  service with a transparency log. Each brings a time source, a service or a second algorithm
  family. The specification already has one Ed25519 verification with fixed rules, and another
  implementation of it is cheaper than a second scheme. A transparency log is something a verifier
  may add on top, and nothing here excludes it.
- **The pack signature document, unchanged, naming a lock's digest.** That would be a pack signature
  that every pack verifier reads as one. A prefix and member name of its own keep the two apart
  (§6).
- **Commits pinned in the federation manifest.** RFC 0039 keeps the manifest as intent and the
  index as record. The lock pins the record.
- **A lock without resolved digests.** Consumers hold resolved registries. Without these digests,
  each would need the whole registry and a reader to resolve it before it could check one.

## Compatibility

- **Registry format `1.0.0` is unchanged.** Nothing is removed or changes meaning. The registry,
  kind and resolved documents keep selector `"1.0.0"`, and a lock and a signature sit beside them.
- **Additions only, under new minor selectors.** The lock and the signature are format `1.1.0`
  documents, and a `1.0.0` reader refuses either by its selector. The lock report is the validation
  report at `"1.1.0"`, and a plain validation still writes `"1.0.0"` (§13).
- **Packs are unchanged.** The runtime's reviewed-set lock, its pack signature document and its
  codes stay the runtime's convention. This RFC reuses that design under its own name and prefix,
  and changes nothing in Core.
- **It does not depend on RFC 0039.** Without it, `index` is not defined, and a lock pins one
  registry. Both would be released on `registry-v1.1.0`, by the route of VERSIONING.md.

## Security and privacy

- **A signature says who, not whether right.** See §9. It is evidence of an act by a key holder,
  not of a review.
- **No time, so replay and rollback are open.** An older signed lock, with its older registry, still
  verifies. For a single registry whose writers bump `version` on every change, a verifier can
  compare it with one it has seen. That does not reach assemblies: an assembly's `version` is its
  manifest's, unchanged when only a source's commit changes, so an older assembly under one manifest
  version is not refused. This draft does not address that rollback (Unresolved question 2).
- **Expected registry and environment.** A key that signs several registries' locks makes each
  verify, and a lock names every environment's resolved registry. So the registry id and the
  environment are named by the verifier, never read from a document (§4), as the key is: another
  registry's lock is `LOCK-UNEXPECTED-REGISTRY`, and a `dev` resolved registry is not covered for
  `prod`. Provenance is likewise required by the verifier, since a lock may omit it (§2).
- **Keys.** The expected key is mandatory, and a key the trust rule refuses is refused before
  anything is read. That includes keys of small order, under which anyone can forge. A compromised
  key cannot be revoked in this format: a verifier stops expecting it.
- **Domain separation.** The prefix keeps a lock signature apart from pack signatures, witness
  statements and every other signature the project's keys make (§6).
- **Unsigned input is read little.** The signature is checked before the lock is parsed, and the
  signature document is bounded at 4 096 bytes.
- **No secrets in a lock.** It holds identifiers and digests only. A digest of a very small resolved
  registry can be confirmed by guessing its content, as RFC 0039 says of the index.
- **Coverage and signing trust the checker.** Coverage relies on whoever checked or signed the lock.
  A signer that signs without checking is a defect a verifier cannot see. A verifier sees only that
  the lock does not check (§7, After a verdict).
- **Resources.** A lock is at most 1 MiB, a signature document at most 4 096 bytes, and each
  signature costs one verification.

## Conformance

Rows would be hand-written and synthetic, under the registry's `1.1.0` rows, for three new
classes: **lock writer** (§§2 and 3), **lock checker** (§4) and **lock signature verifier**
(§§5 to 7). Signing rows use RFC 8032 §7.1 TEST 1's published seed, as the dialect vectors do, so
that any reader can reproduce them, and a second published seed for wrong-key rows.

- **Positive.** A lock of a single registry; a lock of an assembly, with its index; coverage of each
  environment's resolved registry; an accepted signature over a lock with and without its final
  line feed.
- **Negative.** One row per code of §8. These include kinds reordered, an environment missing from
  `resolved`, a lock naming an index checked without one, an index given for a lock that names
  none, a lock with no index where one is required, and each expected input missing.
- **Boundary.** A signature document of 4 096 bytes and one of 4 097; a lock at 1 MiB and one over
  it; a lock followed by two line feeds (`LOCK-SIG-DIGEST-MISMATCH`).
- **Adversarial.**
  - A pack signature's message, made under the expected key, presented as a lock signature
    (`LOCK-SIG-INVALID`).
  - Another lock's signature moved beside this lock.
  - Another registry's lock, signed by the expected key (`LOCK-UNEXPECTED-REGISTRY`).
  - The `dev` resolved registry offered for `prod` (`LOCK-NOT-COVERED`).
  - A document naming a key other than the expected one, whose signature holds under its own key.
  - An expected key that is all zeros, of small order, or not canonical.
  - A signature with `S` at or above L, and one that holds only under the cofactored check.
  - Uppercase hexadecimal, a base64 key, and a member name written with an escape.
  - A lock re-formatted with white space.
  - A lock that is not canonical, signed by the expected key, which is accepted as signed and then
    refused as `LOCK-NOT-CANONICAL`.

## Implementation

- **The reference runtime (Go)** would add `jpack registry lock`, `registry covers`, `registry
  sign` and `registry verify-signature`, reusing the key checks of its pack signatures, the seed
  handling of `packs sign` and its registry reader.
- **A second reader**, independently written, in this repository's Python tooling, which already
  makes and checks Ed25519 signatures for the dialect vectors.
- **Hosts** hold the keys, distribute the expected ones and decide which signatures they require.
  That is theirs, outside this text.

## Unresolved questions

1. **Several signatures.** A standard's owner and a service's owner may both need to sign. Is the
   rule that combines them (all of a set, k of n) the verifier's policy, or a document of its own?
2. **Time and rollback.** Should a lock carry a monotonic serial, or its signature a time, so that a
   verifier can refuse an older assembly under one manifest version? Either makes a writer read the
   previous lock or a clock, and a verifier keep state or a log.
3. **File names.** Should the companion name a sibling convention (`<registry>.lock.json`,
   `<lock>.sig.json`), as the runtime does for packs, so that independent tools find each other's
   files?
4. **Emitters.** Should a lock also pin emitter manifests and the digests of the files they own, so
   that a deployment can check its generated files against the reviewed set?
5. **Several registries per lock.** Should one lock cover several assemblies, for example one per
   region, under one signature?
6. **One signature document for packs and registries.** A shared document with a `subject` member
   would need one specification. Today the pack signature is a runtime convention and this one would
   be the companion's.
7. **Key rotation.** The runtime's audit trail has rotation statements, and a lock signature has
   none. Is a rotation statement needed here, or is the expected key enough?
8. **Provenance in `valid`.** Should a lock check that is given the sources also run RFC 0039's
   index check, making provenance part of the lock's result?
9. **Review regime:** as in RFC 0034, question 1.

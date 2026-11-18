# RFC 0040: Registry locks and signatures — pinning what a registry depends on, and signing the pin

- Status: Draft
- Type: Standards track, a proposed addition to the registry companion
  ([`spec/registry.md`](../spec/registry.md)) as registry format `1.1.0`; format `1.0.0` and every
  document it defines are unchanged
- Created: 2026-11-17
- Amended: 2026-11-17, settling four of the first draft's Unresolved questions by the maintainer's
  ruling: all of a set of signatures, per repository (§§5 and 7), a serial against rollback (§§2
  and 7), emitters in the lock (§§2 to 4) and one lock per assembly (§2); each remaining question
  carries a proposed resolution; 2026-11-18, deciding the remaining questions as proposed (Settled
  questions), with the proposed companion text [`spec/registry-1.1.0.md`](../spec/registry-1.1.0.md)
- Related: [RFC 0034](0034-registry-profile.md) (the registry profile);
  [RFC 0039](0039-federated-registry.md) (the assembled index a lock may pin); the key and
  signature rules of the checkpoint witness companion
  ([`spec/checkpoint-witness.md`](../spec/checkpoint-witness.md) §§1 and 5); the reference
  runtime's reviewed-set lock (its ADR-0019) and pack signatures (its ADR-0083 and
  `docs/pack-signatures.md`); issue
  [#323](https://github.com/Judgment-Pack/judgment-pack-spec/issues/323) (pack identity under
  re-serialization)

> **Draft.** This record is normative for nothing. Nothing is built: no schema, no row, no reader.
> The Specification below is the sketch; the proposed companion text,
> [`spec/registry-1.1.0.md`](../spec/registry-1.1.0.md), states it as format `1.1.0` would, and
> governs where the two differ.
>
> **Review standing.** [RFC 0009](0009-interim-review-regime.md) asks for a recorded adversarial
> review by a model from a different vendor on the pull request that creates an RFC. None is
> recorded for this draft, and this record does not claim one.

## Summary

A registry pins its kind declarations by digest, but nothing pins the registry itself, its
resolved forms, or, for an assembled registry (RFC 0039), the sources it came from. Nothing lets a
reader refuse a registry that a key it expects did not vouch for. This RFC proposes three documents
for registries, modelled on what the reference runtime already does for packs:

- A **lock** names, by digest, the registry, every kind declaration it pins, the resolved registry
  of each environment, the emitter manifests and the files they own, and, for an assembly, its
  index and each source's signature. It carries a **serial** that rises with each lock of one
  registry. A lock check compares the lock with the documents it is given and refuses on any
  difference. Writing a lock reviews nothing: it makes an amendment visible in a diff.
- A **lock signature** is a detached Ed25519 signature over a context-prefixed message that names
  the lock's digest, by the standard owner's key (for a single registry, its owner's). It is the
  runtime's pack signature design applied to a lock, under its own prefix and member name.
- A **source signature**, for an assembly, is one repository's signature, by that repository's
  key, over its own documents at its commit. An assembled lock is accepted only with all of its set.

A verifier is given the keys, the registry id and, for coverage, the environment it expects, and
never takes any of them from a document. It keeps, per registry id, the serial of the last lock it
accepted, and refuses an older one. No cryptography is new: the key and signature rules are those
the checkpoint witness companion already states, and the documents' shape is the pack signature's.

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
| Source signature | `sourceSignatureVersion` | `"1.1.0"` | 4 096 bytes |
| Lock report | `reportFormatVersion` | `"1.1.0"` | as §7.4 |

The lock is admitted by §2.2 with its bound. The lock report is the validation report under the
minor selector `"1.1.0"`, as RFC 0039 §1 has it. It adds the location `document` values `lock`,
`signature` and `emitter`, and the `LOCK-` codes of §8.

### 2. The lock

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

A lock has these members, and no other:

- **`serial`**: an integer from 1 to 9 007 199 254 740 991 (2^53 − 1). Each lock of one registry
  `id` has a higher serial than the lock before it (§3), and the lock signature covers it (§7,
  Rollback).
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
- **`sources`**: present exactly when `index` is. One item per source of the index, in its order:
  the source's `name`, `role` and `repository` as the index gives them; `statement`, the digest of
  the source's statement (§5.2); and `signature`, the digest (§2.3) of the source signature
  document the writer accepted for it. So the lock, and the signature over it, name the repository
  signatures the assembly was made with.
- **`emitters`**: optional. *Amended 2026-11-17, by the maintainer's ruling (first draft's question
  4).* One item per emitter manifest (§11.1) the writer was given, sorted by `source` and then
  `path`: the manifest's `path` in its repository (§11.3's form), its `digest` (§2.3), and `files`,
  every file its `owns` matches, sorted by `path`, each with `path`, `mode` (`"0644"` or `"0755"`)
  and `digest` (`sha256:` over its exact bytes). In an assembled lock each item also has `source`,
  the name of the source whose repository holds it.

**One lock, one registry.** *Amended 2026-11-17, by the maintainer's ruling (first draft's question
5).* A lock names exactly one registry: one single registry, or one assembly with its index.
Several assemblies (one per region, for example) have one lock each, with its own serial and
signatures, and a verifier that expects several verifies each against its own expected registry id.

**What is locked.** Through these digests, a lock pins:

- the registry's entries, overlays, owners and secret scopes;
- every kind declaration it pins;
- each environment's resolved form, which is what emitters and loaders read;
- the serial, which orders the locks of one registry id;
- every emitter manifest the writer was given, and each file it owns, by path, mode and digest;
- for an assembly, the index, and through the index the manifest, each source's repository,
  commit and paths, the content digest of every document read, and the bounds, per-environment
  bounds included (RFC 0039 §5.5); and, by digest, each source's statement and the source
  signature accepted for it.

**What is not locked:**

- secret values, which a registry never holds, only references pinned to a version;
- facts contracts, which follow from the kinds;
- files no emitter the writer was given owns;
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
- **Serial.** *Amended 2026-11-17, by the maintainer's ruling (first draft's question 2).* It is
  given the previous lock of the registry id, and writes `serial` one above that lock's; a previous
  lock of another registry id is `LOCK-UNEXPECTED-REGISTRY`. With no previous lock, it is given the
  first serial out of band; there is no default. A previous lock whose serial is
  9 007 199 254 740 991 leaves no next serial, and the writer refuses (`LOCK-FORM`), since the lock
  it would write is not of its form. The lock is thus deterministic in its inputs: the documents,
  and the previous serial.
- **Source signatures.** For an assembly, it is given one source signature document per source and
  the expected signer set (§7), and verifies each as §7 does. A source whose signature does not
  verify is refused with that signature's code, and no lock is written.
- **Emitters.** For each emitter manifest it is given, it runs, or is given the outcome of, the host
  in check mode (§11.4) against this registry. It writes `emitters` only when every run exits 0, so
  that the files it lists are those the emitters write from this registry; otherwise
  `LOCK-EMITTER-MISMATCH`.
- It writes the lock's JCS bytes, and never a lock over its bound.
- Writing a lock reviews and approves nothing. As with the runtime's `packs lock`, running it is
  how an amendment is declared, in a file that a reviewer sees change beside the documents it
  pins.

### 4. Checking a lock

**Expected inputs.** Every check, coverage and verification is also given, out of band and every
time, under the rule §7 states for the expected key: the **registry `id`** it expects, and whether
it **requires an index**; coverage is also given the **environment** it serves, and verification
the expected signer set, with a repository key map exactly when an index is required, and its
serial record or a floor (§7). None has a default, and none is taken
from a lock, a registry or a signature document. One missing, or a registry id that is not an
absolute URI, is `LOCK-EXPECTED`, before anything is read.

A check is given a lock, the registry, the kind declarations, the index when the lock names one,
and the emitter manifests and their files when it names emitters. Its steps:

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
7. **Sources.** With the index, each `sources` item's `name`, `role` and `repository` are the
   index's, in its order, and its `statement` is the digest of the statement rebuilt from the
   index's item (§5.2); otherwise `LOCK-SOURCES-MISMATCH` at the item. The signatures are verified
   in §7, which requires the index of an assembled lock.
8. **Emitters.** A lock that names emitters, checked without them, and a manifest or file the lock
   lists that is not given, are `LOCK-EMITTER-MISSING`, at `/emitters` or at the item. A manifest or
   file given that differs from the lock's item, or a file the manifest's `owns` matches that the
   lock does not list, is `LOCK-EMITTER-MISMATCH` at the item.

A failure in step 1 or 2 ends the check. Steps 3 to 8 report every diagnostic of their own. The
report's `valid` is `true` exactly when there is no error. A check reads `serial` for its form
only: ordering is the verifier's (§7, Rollback).

The check does not re-run the assembly. RFC 0039's index check does that, against the sources at
their commits, and a verifier that wants provenance runs both.

**Coverage.** A consumer holding one environment's resolved registry and a lock (a start-up loader,
an emitter host, a deployment step) asks whether the lock covers it, for the registry id and
environment it expects. The lock is first held to step 1. The resolved registry is covered exactly
when its `environment` is the expected environment, its `registry.digest` is the lock's registry
digest, and its digest is the lock's `resolved` digest for the expected environment; otherwise it
is `LOCK-NOT-COVERED`. A `dev` resolved registry handed to a `prod` loader is thus not covered,
although the lock names it. A generated file is covered exactly when an `emitters` item, of its
source in an assembled lock, lists its path with its mode and digest. This is the runtime's
`packs covers` question asked of a registry. Coverage establishes byte identity with what the lock
names, and it re-derives nothing. A consumer that relies on it relies on whoever checked or signed
the lock, and verifies the lock (§7) first.

### 5. The signature documents

#### 5.1 The lock signature

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
registry carries it, and neither changes when it is made. A lock has one lock signature (§7).

#### 5.2 The source signature and its statement

*Amended 2026-11-17, by the maintainer's ruling (first draft's question 1).* A **source statement**
is the JCS of an object of exactly `repository`, `commit` and `documents`, with the values of the
index's source item (RFC 0039 §4): the repository identity, the commit, and every document's
`path`, `role`, `contentDigest` and `digest`, in the index's order. Its digest (§2.3) is what a
source signature signs. It names no source name, manifest or other source: a repository vouches for
its own documents at its own commit, and for nothing else.

The source signature document has exactly five string members, written and read as the lock
signature's are, with the same forms and bound: `sourceSignatureVersion` (`"1.1.0"`), `algorithm`,
`publicKey`, `sourceDigest` (the statement's digest) and `signature`. It names a commit, so it
cannot be stored in that commit: it travels beside the bytes the assembler is given, as a CI job's
output or in a store the standard owner keeps.

### 6. What is signed

Each signature is Ed25519 (RFC 8032, pure, with no context string) over these ASCII bytes:

```text
judgment-pack-registry/lock-signature/1:{"lockDigest":"sha256:<64 hex>","lockSignatureVersion":"1.1.0"}
judgment-pack-registry/source-signature/1:{"sourceDigest":"sha256:<64 hex>","sourceSignatureVersion":"1.1.0"}
```

The part after each prefix is the JCS of those two members. Every signing prefix of the project is
a namespace with no `/` in it (`judgment-pack`, `judgment-pack-runtime`, `judgment-pack-gateway`),
then `/`, a name, a version and `:`. No prefix but these two starts `judgment-pack-registry/`, and a
later one in this namespace MUST have another name or version. Two prefixes that differ in their
namespace or name are neither a prefix of the other, and every message begins with its own prefix,
so no signature of another kind is a lock or source signature, even under one key, and a lock
signature is never a source signature. A message names a digest, not the bytes: it is small and of
one shape, and the digest binds the bytes.

### 7. Keys, signing and verification

**Keys.**

- **Form.** A key is the 32-byte encoding of an Ed25519 public key. Its **key identifier** is the
  first 32 lowercase hexadecimal characters of the SHA-256 of those bytes, the form of
  `spec/checkpoint-witness.md` §1 and the identifier the runtime reports beside a pack signature.
  The document carries the full key, never its identifier, so a verifier compares bytes. Reports
  name both.
- **Trust.** A verifier MAY trust a key exactly when `spec/checkpoint-witness.md` §5 admits it:
  canonical, not of small order, and on the curve. A verifier MUST hold every expected key, and
  every document's key, to that rule.
- **The equation.** A signature verifies exactly when §5 of that companion says it does:
  cofactorless, with `S` below L and `R` compared byte for byte. The cofactored check is not used.
- **The expected key.** A verifier is given the key it expects, out of band, every time. It MUST
  NOT take a key from a signature document, and it has no mode that does. How keys are
  distributed, rotated and retired is the verifier's concern. The companion keeps no list of keys
  and knows no revocation.

**The expected signer set.** *Amended 2026-11-17, by the maintainer's ruling (first draft's
question 1).*

- **A single registry's lock** has one signer: the expected key, which signs the lock. Its
  verifier is given no repository key map.
- **An assembled lock** has the **standard owner's key**, which signs the lock and the standard
  source's statement, and a **repository key map**, from repository identity to key, naming the
  key that signs each repository source's statement. Both are given as the expected key is: out of
  band, every time, each key held to the trust rule (`LOCK-SIG-EXPECTED-KEY`), and none taken from a
  document. A repository source of the lock whose identity the map does not name, found once the
  lock is read (Verifying, step 6), is `LOCK-EXPECTED`. The map MAY name repositories the lock does
  not, so one map can serve several assemblies.
- **The verifier, not the lock, chooses.** A verifier given a repository key map requires an index
  (§4, Expected inputs): a map given with no index required, or an index required with no map, is
  `LOCK-EXPECTED`, before anything is read. So a lock with no index and no sources, signed by the
  standard owner's key, is `LOCK-INDEX-REQUIRED` for a verifier that holds a map, never a single
  registry's lock that needs no repository's signature.
- **One key, one role.** The standard owner's key signs the lock and the standard source's
  statement, which is its own role, and each repository's key signs that repository's statements
  only. A map that gives a repository the standard owner's key, or gives one key to two repository
  identities, keys compared as 32 bytes, is `LOCK-EXPECTED`, before anything is read: otherwise all
  of the set would hold with fewer independent keys than it names. Two repository sources of one
  repository identity are no second role: both are that repository's, and its one key signs both.
  The standard source shares its identity with no repository source the map names (Verifying,
  step 6). There is no
  option to share a key: a key per repository costs its owner nothing, and a shared one would let
  one holder fill two places in the set.
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
  owner's CI signs the standard source's statement, writes the lock (§3) once it holds every
  source's signature, checks it (§4), and signs it.
- A signer MUST check what it signs: the lock against the documents it names (§4), or a statement
  against its own documents at its commit. It MUST NOT sign a lock that does not check or is not
  canonical. A signature over something nobody checked vouches for a digest blindly.
- The private key is the signer's to hold. The runtime holds a pack-signing seed as it holds an
  audit trail's key, and a registry signer would do the same. Given the public key it means to sign
  with, it refuses, before signing anything, a seed whose public key is another.
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

**Checking a document** against a key and a digest, in this order, so the reader learns the
plainer reason first: the document's key is not that key, compared as 32 bytes
(`LOCK-SIG-UNEXPECTED-KEY`); its digest member is not that digest (`LOCK-SIG-DIGEST-MISMATCH`);
the signature does not verify under that key over §6's message (`LOCK-SIG-INVALID`).

**Verifying.** The verifier is given the lock's bytes, the lock signature document, for an
assembled lock its index and the source signature documents, the expected signer set, the expected
inputs of §4, and its serial record or a floor (Rollback, below). A signature binds only a digest:
without the expected registry id, another registry's lock signed by the same key would verify. In
order:

1. an expected key missing or refused by the trust rule: `LOCK-SIG-EXPECTED-KEY`; another expected
   input missing, a map without an index required or the reverse, or one key in two roles:
   `LOCK-EXPECTED`. The record for the expected registry id is read: one that exists and cannot be
   read, or is not of its form, is `LOCK-SERIAL-STATE`, and neither a record nor a floor is
   `LOCK-EXPECTED`. Each comes before the lock or any document is read;
2. **the lock signature**, read, then checked against the standard owner's key (for a single
   registry, the expected key) and the SHA-256 of the lock's bytes without one final line feed. No
   lock signature document is `LOCK-SIG-MISSING`, and a second is `LOCK-SIG-EXTRA`. A signature of
   another lock, moved beside this one, is `LOCK-SIG-DIGEST-MISMATCH`. The lock's bytes are not
   parsed until it is accepted;
3. **the lock**, held to §4's step 1, which includes the expected registry id and the index
   requirement;
4. **the serial**, against the record or the floor (Rollback);
5. **the index**, for a lock that names one. None given is `LOCK-INDEX-MISSING`, whatever else is
   given: without the index no source statement can be rebuilt, and a repository's signature at one
   commit could stand for an index that records another. The index is admitted and held to §4's
   steps 6 and 7: its digest is the lock's, it names the lock's registry, and it has exactly one
   `standard` item (`LOCK-INDEX-MISMATCH`), and the lock's `sources` are its sources, each
   `statement` the digest of the statement rebuilt from the index's item (`LOCK-SOURCES-MISMATCH`);
6. **the source signatures**. Each source signature document given is read, and matched to the
   `sources` item whose `signature` is its digest (§2.3). An item that no document matches is
   `LOCK-SIG-MISSING` at the item. A document that matches no item, a second copy for one item, or
   any document given for a lock with no `sources`, is `LOCK-SIG-EXTRA`: a set with a stray
   signature is refused, not trimmed. A repository item whose `repository` the map does not name,
   or any repository item when no map is given, is `LOCK-EXPECTED`, and so is a standard item whose
   `repository` the map names: the role chooses the key, and nothing else pins it. Each matched
   document is
   checked against the key the set names for its item (the standard owner's for the `standard`
   item, the map's for the item's `repository` otherwise) and the digest of the statement rebuilt
   from the index's item (§5.2), never against the lock's `statement` member alone;
7. the rest of §4 when the documents are given, and coverage when a resolved registry or a file is.

The report gives every result: each signature, accepted or refused, with its key and key
identifier, and the lock's result. An accepted lock signature over a lock that fails any later step
is a refusal of the lock, not a pass.

**Rollback.** *Amended 2026-11-17, by the maintainer's ruling (first draft's question 2).* The
lock's `serial`, which the lock signature covers, orders the locks of one registry id.

- **What the verifier keeps.** For each registry id it has accepted a lock of, a **record**: the
  `serial` and the lock digest of the last lock it accepted. Nothing else is kept: keys and the
  other expected inputs are given each time, and one record serves every environment of the
  registry.
- **The rule.** Under a record, a lock whose serial is below the record's is
  `LOCK-SERIAL-ROLLBACK`. One whose serial equals the record's is accepted only when its digest is
  the record's: verifying the accepted lock again, after a restart for example, is no rollback.
  Another lock with that serial is `LOCK-SERIAL-CONFLICT`, two locks claiming one place. A higher
  serial is admitted, however far above: a verifier need not see every lock.
- **A floor.** A **floor**, given out of band, is the lowest serial the verifier may accept: a lock
  below it is `LOCK-SERIAL-ROLLBACK`, and one at or above it is admitted. Given with a record, the
  higher governs: a floor above the record's serial is held as a floor alone, and one at or below
  it changes nothing. Neither a floor nor anything else in a verification lowers a record.
- **First contact.** With no record for the registry id, a floor MUST be given; neither a record
  nor a floor is `LOCK-EXPECTED`. A floor of 1 accepts whatever lock comes first: trust on first
  use, which a verifier chooses by giving it, never by default.
- **A record that cannot be read.** A record that exists and cannot be read, or is not of its form,
  is `LOCK-SERIAL-STATE`, and the lock is not accepted. It is never taken for a first contact, and
  a floor given beside it does not stand in for it. A record gone without trace is a first contact,
  as strong as its floor, so a verifier whose records can be lost gives a floor no lower than the
  last serial it knows it accepted.
- **Recording.** Only when every step of the verification accepts does the verifier write the
  record, the lock's serial and digest, durably, before it reports the lock accepted. The write is
  a compare and set against the record read in step 1: when another process sharing the record
  has written it since, the verifier reads it again and holds the lock to the rule once more, and
  writes only if the lock still passes. So no write lowers a record, and two locks of one serial
  are never both recorded. A record it cannot write, or read again, is `LOCK-SERIAL-STATE`, and the
  lock is not accepted. A lock whose serial and digest are the record's needs no write, and a
  refused lock changes no record.
- **The state is the verifier's.** It is not in the lock, the registry or a signature, and nothing
  here writes it into a document another reader trusts. Two verifiers keep two records; verifiers
  that must agree share theirs by their own means, outside this text.

### 8. Diagnostic codes

All are errors. The right-hand column is the runtime's pack signature code that the same failure
gives, so that one implementation can serve both.

| Code | Raised when | Pack signature code |
| --- | --- | --- |
| `LOCK-EXPECTED` | an expected input is missing: the registry id, the index requirement, the environment (coverage), a repository source's key, or a floor at first contact; a repository key map is given without an index required, or the reverse; one key has two roles in the set, or the standard item's `repository` is one the map names; or the id is not an absolute URI | — |
| `LOCK-FORM` | the lock is not of its form, or a writer's next serial would be out of range | — |
| `LOCK-NOT-CANONICAL` | the lock's bytes are not its JCS bytes | — |
| `LOCK-UNEXPECTED-REGISTRY` | the lock's `registry.id`, or a writer's previous lock's, is not the expected registry id | — |
| `LOCK-INDEX-REQUIRED` | an index is required and the lock names none | — |
| `LOCK-REGISTRY-INVALID` | the registry, or the assembly, has an error | `-PACK-NOT-VALID` (signing) |
| `LOCK-REGISTRY-MISMATCH` | the registry is not the one the lock names | — |
| `LOCK-KINDS-MISMATCH` | the lock's kinds are not the registry's pins | — |
| `LOCK-RESOLVED-MISMATCH` | an environment's resolved digest differs, or the environments do | — |
| `LOCK-INDEX-MISSING` | the lock names an index and none was given, to a check or a verification | — |
| `LOCK-INDEX-MISMATCH` | the index is not the one the lock names, names another registry, or does not have exactly one `standard` item | — |
| `LOCK-INDEX-UNLOCKED` | an index was given for a lock that names none | — |
| `LOCK-SOURCES-MISMATCH` | the lock's sources are not the index's, or a statement digest differs | — |
| `LOCK-EMITTER-MISSING` | the lock names emitters and none were given, or a manifest or file it lists was not given | — |
| `LOCK-EMITTER-MISMATCH` | an emitter manifest or owned file given differs from the lock's item, an owned file is absent from the lock, or a host check did not exit 0 | — |
| `LOCK-NOT-COVERED` | a resolved registry is not of the expected environment, or not the one the lock names for it; or a file is not one the lock lists | `document-drift` (`packs covers`) |
| `LOCK-SERIAL-ROLLBACK` | the lock's serial is below the verifier's record, or below its floor | — |
| `LOCK-SERIAL-CONFLICT` | the lock's serial is the record's and its digest is not | — |
| `LOCK-SERIAL-STATE` | the verifier's record exists and cannot be read or is not of its form, or cannot be written | — |
| `LOCK-SIG-EXPECTED-KEY` | an expected key is missing, or one a verifier may not trust | `-EXPECTED-KEY` |
| `LOCK-SIG-MISSING` | the lock signature, or an item's source signature, is not given | `-MISSING` |
| `LOCK-SIG-EXTRA` | a second lock signature is given, a source signature that no item expects or that is given twice, or more source signatures than the lock's `sources` count plus one | — |
| `LOCK-SIG-DOCUMENT` | a document is over its bound, not one JSON object, repeats a member or holds a backslash | `-TOO-LARGE`, `-MALFORMED`, `-DUPLICATE-MEMBER` |
| `LOCK-SIG-VERSION` | `lockSignatureVersion` or `sourceSignatureVersion` is not `"1.1.0"` | `-VERSION` |
| `LOCK-SIG-MEMBER` | a member is unknown or missing | `-UNKNOWN-MEMBER`, `-MISSING-MEMBER` |
| `LOCK-SIG-ALGORITHM` | `algorithm` is not `ed25519` | `-ALGORITHM` |
| `LOCK-SIG-PUBLIC-KEY` | `publicKey` is not of its form, or not a key a verifier may trust | `-PUBLIC-KEY` |
| `LOCK-SIG-FORM` | a digest member or `signature` is not of its form | `-PACK-DIGEST`, `-VALUE` |
| `LOCK-SIG-UNEXPECTED-KEY` | a document's key is not the key the expected set names for it | `-UNEXPECTED-KEY` |
| `LOCK-SIG-DIGEST-MISMATCH` | the lock's bytes, or a source's statement, are not what the document names | `-DIGEST-MISMATCH` |
| `LOCK-SIG-INVALID` | a signature does not hold under its expected key | `-INVALID` |

A diagnostic carries no value: no key but the key identifier, which the report names for an
accepted signature, and no document content.

### 9. What an accepted set of signatures establishes

- **It establishes** that the holder of the expected key (for an assembly, the standard owner's)
  signed this lock's digest, and, for an assembly, that the holder of each repository's expected
  key, a key of its own, signed the statement rebuilt from the index's item for it: its documents,
  by digest, at the commit the index names. Through the lock's digests, that covers the registry,
  its kinds, its resolved forms, the serial, the emitters and their files and, when the lock names
  one, the index; through the index, the repositories, commits, paths and content digests it
  claims, each vouched for by that repository's key. With the verifier's record, it establishes
  that no lock of that registry accepted earlier had a higher serial.
- **It does not establish**:
  - that the registry is right, tested, reviewed, approved or current;
  - when it was signed: the serial orders locks, and dates none;
  - that no newer lock exists: a verifier never shown one keeps accepting the last;
  - that the documents the repositories vouched for assemble to the registry the lock names: the
    standard owner's signature says so, and RFC 0039's index check shows it;
  - that the signer had authority over any entry, or a repository's key over its history;
  - that any secret exists;
  - that the locked files are the ones deployed.

## Alternatives

- **Sign the registry document, with no lock.** A registry's digest covers its pins. It does not
  cover the resolved forms consumers hold, or an assembly's provenance, and an assembled registry is
  read from several documents.
- **Sign each document.** That gives many signatures and nothing that binds the set. A reviewed
  registry mixed with another registry's kinds would verify. Source signatures sign each
  repository's documents, but only as members of a set the lock binds.
- **k of n signatures.** Rejected by the maintainer's ruling: a repository's signature vouches for
  its own documents and the standard owner's for the assembly, so no number of other signatures
  can stand in for a missing one.
- **Put the signature inside the registry or the lock.** It would change the closed registry
  document of `1.0.0`, and a document cannot sign its own bytes.
- **A time, or a log, against rollback.** A time brings a clock into verification, and two
  writers' clocks disagree; a log orders locks too, at the cost of a service. A serial needs only
  the previous lock. Nothing here excludes a log a verifier adds on top.
- **A new envelope or algorithm**, such as a general-purpose signing envelope, or a keyless signing
  service with a transparency log. Each brings a time source, a service or a second algorithm
  family. The specification already has one Ed25519 verification with fixed rules, and another
  implementation of it is cheaper than a second scheme.
- **The pack signature document, unchanged, naming a lock's digest.** That would be a pack signature
  that every pack verifier reads as one. A prefix and member name of its own keep the two apart
  (§6).
- **Several registries per lock.** Rejected by the maintainer's ruling: one lock per registry keeps
  one serial, one expected registry id and one coverage question per lock.
- **Commits pinned in the federation manifest.** RFC 0039 keeps the manifest as intent and the
  index as record. The lock pins the record.
- **A lock without resolved digests.** Consumers hold resolved registries. Without these digests,
  each would need the whole registry and a reader to resolve it before it could check one.

## Compatibility

- **Registry format `1.0.0` is unchanged.** Nothing is removed or changes meaning. The registry,
  kind, resolved and emitter documents keep their selectors, and a lock and its signatures sit
  beside them.
- **Additions only, under new minor selectors.** The lock and the two signature documents are
  format `1.1.0` documents, and a `1.0.0` reader refuses each by its selector. The lock report is
  the validation report at `"1.1.0"`, and a plain validation still writes `"1.0.0"` (§13).
- **Packs are unchanged.** The runtime's reviewed-set lock, its pack signature document and its
  codes stay the runtime's convention. This RFC reuses that design under its own name and prefix,
  and changes nothing in Core.
- **It does not depend on RFC 0039.** Without it, `index`, `sources` and source signatures are not
  defined, and a lock pins one registry with one signer. Both would be released on
  `registry-v1.1.0`, by the route of VERSIONING.md.

## Security and privacy

- **A signature says who, not whether right.** See §9. It is evidence of an act by a key holder,
  not of a review.
- **All of a set, no stand-ins.** A repository's key signs only its own statement: one by another
  key, where the map names another, is `LOCK-SIG-UNEXPECTED-KEY`, and a statement of another
  commit than the index records is `LOCK-SIG-DIGEST-MISMATCH`, because the statement is rebuilt
  from the index, which an assembled lock is never verified without (`LOCK-INDEX-MISSING`). One key
  in two roles is refused (`LOCK-EXPECTED`), so the set's keys are as many as its places, and a
  verifier holding a map never accepts a lock as a single registry's. A missing signature is a
  refusal, and a stray one is refused rather than ignored (`LOCK-SIG-EXTRA`). A compromised
  repository key can sign false documents for its own repository only, and they still had to pass
  the assembly the standard owner then signed.
- **Rollback is refused by the verifier's record, not by the lock.** A signed older lock verifies
  as a signature, and its serial refuses it against a record that has seen a newer one
  (`LOCK-SERIAL-ROLLBACK`). A first contact is as strong as its floor; a record that cannot be
  read refuses (`LOCK-SERIAL-STATE`) rather than starting over; shared records are written by
  compare and set, never lowered; and withholding a newer lock (a freeze) is not detected. A holder
  of the standard owner's key can sign any serial, a very high one included. Since nothing in a
  verification lowers a record, recovering from that is the verifier operator's act, outside this
  text: removing the record and giving a floor. A verifier that must survive it needs a log of its
  own.
- **Expected registry and environment.** A key that signs several registries' locks makes each
  verify, and a lock names every environment's resolved registry. So the registry id and the
  environment are named by the verifier, never read from a document (§4), as the keys are: another
  registry's lock is `LOCK-UNEXPECTED-REGISTRY`, and a `dev` resolved registry is not covered for
  `prod`. Provenance is likewise required by the verifier, since a lock may omit it (§2).
- **Keys.** Every expected key is mandatory, and a key the trust rule refuses is refused before
  anything is read. That includes keys of small order, under which anyone can forge. A compromised
  key cannot be revoked in this format: a verifier stops expecting it.
- **Domain separation.** The prefixes keep lock and source signatures apart from each other, from
  pack signatures and witness statements, and from every other signature the project's keys make
  (§6).
- **Unsigned input is read little.** The lock signature is checked before the lock is parsed, and
  each signature document is bounded at 4 096 bytes.
- **No secrets in a lock.** It holds identifiers, paths and digests only. A digest of a very small
  resolved registry or generated file can be confirmed by guessing its content, as RFC 0039 says of
  the index.
- **Coverage and signing trust the checker.** Coverage relies on whoever checked or signed the lock.
  A signer that signs without checking is a defect a verifier cannot see. A verifier sees only that
  the lock does not check (§7, Verifying).
- **Resources.** A lock is at most 1 MiB, each signature document at most 4 096 bytes, an assembly
  at most 256 sources (RFC 0039 §2), so at most 257 signatures, each one verification.

## Conformance

Rows would be hand-written and synthetic, under the registry's `1.1.0` rows, for three new
classes: **lock writer** (§§2 and 3), **lock checker** (§4) and **lock signature verifier**
(§§5 to 7). Signing rows use RFC 8032 §7.1 TEST 1's published seed, as the dialect vectors do, so
that any reader can reproduce them, and further published seeds for repository and wrong-key rows.
A verifier's record is part of a row's input and of its expected output.

- **Positive.** A lock of a single registry; a lock of an assembly, with its index and every source
  signature; coverage of each environment's resolved registry and of a generated file; an accepted
  signature over a lock with and without its final line feed; the accepted lock verified again
  (equal serial, same digest); a first contact with a floor of 1; a higher serial replacing the
  record.
- **Negative.** One row per code of §8. These include kinds reordered, an environment missing from
  `resolved`, a lock naming an index checked without one, an index given for a lock that names
  none, a lock with no index where one is required, each expected input missing, a source signature
  missing, a second copy of one, a serial below the record, an equal serial with another digest, no
  floor at first contact, a record the harness makes unwritable, one it makes unreadable or
  corrupt (`LOCK-SERIAL-STATE`, not a first contact), a lock naming emitters checked without them,
  a listed file not given (`LOCK-EMITTER-MISSING`), an owned file changed by one byte, an assembled
  lock verified without its index (`LOCK-INDEX-MISSING`), a map given with no index required, and a
  writer whose previous serial is 2^53 − 1 (`LOCK-FORM`).
- **Records and floors.** A record with a higher floor beside it, where the floor governs; a record
  with a lower floor, where the record does; two verifiers sharing one record that accept two locks
  in turn, where the second write, compare and set, refuses the older lock rather than lowering the
  record.
- **Boundary.** A signature document of 4 096 bytes and one of 4 097; a lock at 1 MiB and one over
  it; a lock followed by two line feeds (`LOCK-SIG-DIGEST-MISMATCH`); serials 1 and 2^53 − 1, and
  0 and 2^53 (`LOCK-FORM`).
- **Adversarial.**
  - A signature over a pack signature's message, and one over the source signature message naming
    the lock's digest, each made under the expected key and placed in a lock signature document
    that names the lock's digest (`LOCK-SIG-INVALID`).
  - Another lock's signature moved beside this lock.
  - Another registry's lock, signed by the expected key (`LOCK-UNEXPECTED-REGISTRY`).
  - The `dev` resolved registry offered for `prod` (`LOCK-NOT-COVERED`).
  - One repository's key signing another repository's statement (`LOCK-SIG-UNEXPECTED-KEY`); a
    repository's statement at another commit (`LOCK-SIG-DIGEST-MISMATCH`); the standard owner's
    key signing a repository's statement (`LOCK-SIG-UNEXPECTED-KEY`).
  - A repository's genuine signature over its statement at one commit, beside an index that
    records another commit for it, with the lock's `statement` written either way
    (`LOCK-SIG-DIGEST-MISMATCH` or `LOCK-SOURCES-MISMATCH`), and the same lock verified without the
    index (`LOCK-INDEX-MISSING`).
  - A map that gives a repository the standard owner's key, and one that gives two repositories one
    key (`LOCK-EXPECTED`).
  - A lock with no index and no sources, signed by the standard owner's key, offered to a verifier
    that holds a map (`LOCK-INDEX-REQUIRED`).
  - A signed older lock offered after a newer was accepted (`LOCK-SERIAL-ROLLBACK`).
  - A document naming a key other than the expected one, whose signature holds under its own key.
  - An expected key that is all zeros, of small order, or not canonical.
  - A signature with `S` at or above L, and one that holds only under the cofactored check.
  - Uppercase hexadecimal, a base64 key, and a member name written with an escape.
  - A lock re-formatted with white space.
  - A lock that is not canonical, signed by the expected key, which is accepted as signed and then
    refused as `LOCK-NOT-CANONICAL`.

## Implementation

- **The reference runtime (Go)** would add `jpack registry lock`, `registry covers`, `registry
  sign` (of a lock or a source statement) and `registry verify-signature`, reusing the key checks of
  its pack signatures, the seed handling of `packs sign`, its registry reader and its emitter host,
  with the verifier's record in a file the verifier names.
- **A second reader**, independently written, in this repository's Python tooling, which already
  makes and checks Ed25519 signatures for the dialect vectors.
- **Hosts** hold the keys, distribute the expected ones, keep the records and decide where the
  signature documents travel. That is theirs, outside this text.

## Settled questions

*Amended 2026-11-18.* Every question is now decided. Questions 1 (several signatures), 2 (time and
rollback), 4 (emitters) and 5 (several registries per lock) of the first draft were settled by the
maintainer's ruling of 2026-11-17, in §§2, 3, 5 and 7. The five that remained are decided as their
proposed resolutions said, and the proposed companion text
([`spec/registry-1.1.0.md`](../spec/registry-1.1.0.md), format `1.1.0`, proposed) states each one.

1. **File names:** defaults for the lock and the lock signature only. The lock of `<name>.json` is
   `<name>.lock.json` beside it, and the signature of a lock file is `<lock file>.sig.json`; a
   command line may name either otherwise. A source signature names a commit, so it cannot live in
   it (§5.2): it has no file name, and travels with the bytes the assembler is given (text §7).
2. **One signature document for packs and registries:** no. The documents stay apart, joined by a
   shape and a prefix rule: a shared document would make every verifier class read every subject,
   and the pack document is fixed at its `1.0.0` (text §10.3).
3. **Key rotation:** the expected keys suffice for `1.1.0`. They are given every time, so a rotation
   is a change to the verifier's configuration, and the serial record, kept per registry id, is
   unaffected. A later version may add a statement signed by the old key (text §§11 and 13).
4. **Provenance in `valid`:** no. The lock check and RFC 0039's index check stay apart, and both
   are reported. Verification already requires an assembled lock's index and rebuilds each source
   statement from it; the index check adds that the documents assemble to the registry the lock
   names, which only the source bytes show (text §9).
5. **Review regime:** a recorded different-vendor review before acceptance, in one round with RFC
   0039. This record defines two signatures, a rollback rule and their refusals, the kind of change
         RFC 0009's review is for; a waiver, as for RFCs 0034 to 0038, is the maintainer's to give.
         Waived by the maintainer; the review is same vendor, not a cross-vendor claim.

# RFC 0010: The gateway signing identity — custody, rotation, and anchoring

- Status: Draft
- Type: Exploratory (research line — gateway formats, outside JPS)
- Created: 2026-08-04

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **Scope note, load-bearing.** Nothing this RFC proposes lands in JPS Core, a profile, or a
> conformance class. If accepted, each part lands in the
> [reference gateway's](https://github.com/Judgment-Pack/judgment-pack-gateway) own repository:
> the custody seam in its Go code, the custody catalogue in its
> [`SECURITY.md`](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/SECURITY.md)
> or deployment guidance, the seal/rotation/checkpoint formats in its
> [`SPEC.md`](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/SPEC.md), and the
> new vectors in its frozen corpus. It is recorded under [RFC 0000's](0000-rfc-process.md)
> cross-project exploratory provision: a disposition here endorses (or declines) the design record
> as written, and adoption authority for every part stays with the gateway repository, which
> decides by its own process. The [architecture vision's](../docs/architecture/vision.md) sentence —
> that nothing in the input-lineage research line is part of JPS, and that no RFC proposes the
> acquisition, receipt, seal, or admission formats as JPS — remains true with this RFC merged. It
> is recorded in this directory because the directory's purpose is to make open design questions
> visible, and this one is currently invisible: the gateway's security posture names a failure it
> does not defend, and nothing anywhere records what defending it would take.

## Summary

The gateway holds one Ed25519 signing identity, and that identity is the entire trust root: every
receipt and every seal is a signature under it, and verification is the check that they are. Three
questions about that identity are currently answered only by omission:

1. **Custody** — where the private seed lives and what can read it. Today: a plaintext hex file,
   written by default into whatever directory `keygen` runs from — and the seed is used for *two*
   keyed operations, not one: Ed25519 signing, and the HMAC arguments commitment derived from the
   same seed.
2. **Rotation** — how the identity can change without orphaning every session the old key sealed.
   Today: it cannot. A receipt carries a `keyId`, but no semantics exist for a second key.
3. **Anchoring** — what survives disclosure of the key. Today: nothing. Disclosure forges every
   receipt and every seal, retroactively, and the gateway's
   [`SECURITY.md`](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/SECURITY.md)
   says so plainly.

This RFC proposes one non-format change (a signing/commitment seam, making custody a deployment
choice) and sketches the format work anchoring and rotation would take: a **content-binding seal**
(the prerequisite without which a checkpoint protects counts, not receipts), a registry **rotation
entry**, and an external **checkpoint**. Only the formats need agreement between a gateway and an
independent verifier; custody never appears on the wire.

## Problem

The gateway's stated ceiling is byte-lineage, not truth, and its stated trust boundary is honest
about the key: *"Its disclosure forges everything — every receipt, every seal, retroactively. There
is no defence against a compromised gateway, and none is claimed."* That honesty is the right
posture for a research preview, and this RFC does not argue the reference should be hardened. The
problem is narrower: the *consequences* of that sentence are not all the same kind, and nothing
records which are inherent and which are design gaps.

- Retroactive forgeability is not inherent. A signature scheme cannot prevent a stolen key from
  signing, but history that is *content-bound* and anchored outside the gateway cannot be rewritten
  by the key alone. The current design has neither piece — the seal binds a session's final
  *count*, not its receipts' contents, and no anchor exists — so compromise is permanent in both
  directions, future and past.
- Un-rotatability is not inherent. The receipt format already carries a `keyId` and deliberately
  never a key, so a store cannot hand a verifier the key to trust. That existing field could be
  reused as a rotation discriminator — reuse, not its stated design intent — but no rotation
  semantics exist. An aged, weakened, or exposed key can only be abandoned, and every session it
  sealed becomes unverifiable-by-policy or trusted-by-nostalgia.
- File custody is not inherent, and it is where the realistic failures live — plural. Disclosure:
  a file in the wrong place (see Evidence). Destruction: `keygen` writes its output with no
  existence check, so rerunning it over a live identity silently truncates the seed — destroying
  the identity's durable form. A running gateway holds its keys in memory and continues signing
  and sealing until it exits; what is lost is every future restart of that identity.
  Already-sealed history stays verifiable under the retained public pin.

Affected users: any operator who runs a gateway whose sealed history someone else relies on, and
any verifier who pins the public key. While the only operator is this project and the only
deployments are the demo and local tests, the problem is documentation. The moment either changes,
it is not.

## Evidence

- **The stray-seed incident** (maintainer-observed; the file was destroyed, so the durable record
  is this report and the two guard pull requests). A `gateway.seed` — a hex-encoded Ed25519
  private seed, minted by `keygen`, mode `0600`, file mtime 2026-08-02 — was observed untracked in
  the working tree of the *runtime* repository during unrelated review on 2026-08-04, one
  `git add .` away from publication. No registry, store, or pin was observed beside it, and the
  maintainer reports nothing had pinned its public key. The file was securely deleted; the guards
  that followed
  ([runtime #72](https://github.com/Judgment-Pack/judgment-pack-runtime/pull/72),
  [gateway #9](https://github.com/Judgment-Pack/judgment-pack-gateway/pull/9)) ignore `*.seed` in
  both repositories. The incident is small and it is the point: custody failed by default, not by
  attack — `keygen` writes into whatever directory it runs from.
- **The seed does two jobs and the code has no seam for either.** The private key is held as a raw
  `ed25519.PrivateKey` in both signing structs (the receipt signer and the seal writer in
  [`go/store.go`](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/go/store.go)),
  and both call `ed25519.Sign` directly. The same seed also derives `argumentsKey`, the HMAC key
  for every acquisition's `argumentsDigest`
  ([`go/serve.go`](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/go/serve.go)) —
  a keyed PRF operation no signing interface supplies. Today, any custody option beyond a readable
  file path is a fork: a path-shaped option such as a systemd-exposed credential already fits the
  existing `<seedfile>` argument, but every oracle backend — agent, HSM, KMS — does not, and a
  signing seam alone would not be enough.
- **Format replacement has precedent.** Version 2 of the receipt format replaced version 1's HMAC
  with Ed25519 and deliberately rejects version-1 stores rather than deprecating them. The line has
  already shown it will replace a format outright when the trust property demands it.
- **Custody ceremony has precedent.** The demo's provisioning script treats the seed and the pinned
  public key as one artifact: it writes the pin from `keygen`'s stdout at first boot, never from
  `GET /publickey`, and refuses to serve if either half survives without the other. Operational
  custody discipline is encodable; it is just not yet written down anywhere reusable.

## Specification (sketch)

Four parts, in ascending order of format weight. Exact field names and canonical forms are
deliberately not fixed here; the gateway's `SPEC.md` canonicalization rules would govern.

### 1. Custody: a signing/commitment seam and a backend catalogue (no format)

The gateway performs its keyed operations through an interface rather than a held private seed.
That interface has **two** operations, because the seed currently backs two: Ed25519 signing, and
the keyed arguments commitment. A `crypto.Signer` covers only the first, so the seam is a real
design decision, not a type change: either the arguments-commitment secret is split out and
provisioned separately — acquiring its own custody, rotation, and pin-adjacent semantics — or a
backend must supply both a signing oracle and a keyed-MAC oracle. Retained from the file backend
either way: `keygen` (or its successor) must create exclusively and refuse an existing target,
reserving replacement for an explicit rotation or recovery command — today it silently truncates a
live identity.

The file seed stays the default backend and the reference stays one stdlib-only binary. Documented
alternatives, each with its bound stated:

- **systemd credentials** — two distinct bounds, not one: `LoadCredential=` scopes a (possibly
  plaintext) file to the service's runtime; encryption at rest belongs to
  `LoadCredentialEncrypted=`/`SetCredentialEncrypted=`, and TPM2 binding depends on how
  `systemd-creds` was configured. Neither protects a compromised process.
- **ssh-agent delegation** — the seed never enters the gateway process, for the signing half only.
  Works only with plain agent-held Ed25519 keys, whose signatures are standard; FIDO2 `sk-ed25519`
  keys are excluded — their signature format differs and would change the receipt format.
- **PKCS#11 / YubiHSM2, or a signing service** (e.g. Vault's transit engine) — the key becomes
  non-exportable *through the configured interface*, conditional on on-device generation, a
  wrapping/export policy that forbids extraction, sign-only authorization, and credential lifetime
  and revocation: PKCS#11 has `CKA_EXTRACTABLE`, YubiHSM supports export-under-wrap, and Vault
  supports `exportable` — each a configuration, not an impossibility. A stolen long-lived
  credential also keeps signing-oracle access after the process compromise ends. And fit is not
  automatic: YubiHSM2 caps Ed25519 messages at 2019 bytes while the receipt signing input carries
  no bound, so that device is not a drop-in backend without a message bound — and moving to a
  prehash mode (Ed25519ph) would be a signature-semantics change, not a configuration.
- **Cloud KMS** — AWS KMS (`ECC_NIST_EDWARDS25519`, with raw and prehash modes that are not
  interchangeable) and Google Cloud KMS (`EC_SIGN_ED25519`, PureEdDSA) offer Ed25519 and are
  candidate signing backends, subject to vector testing of message limits, raw-versus-prehash
  mode, and signature bytes against the frozen corpus; Azure Key Vault does not offer Ed25519.

### 2. Content-binding seals: the prerequisite (format)

The current seal commits to `sessionId`, `finalCount`, `sealedAt`, and `keyId` — a *count*, not
contents. Anchoring that seal therefore anchors how many receipts a session held, and nothing
about what they said: an attacker holding the disclosed seed can re-sign a whole session's
receipts and artifacts at the same count, and registry and checkpoint verify unchanged. Before a
checkpoint means anything about history, the seal must **commit to the session's content** — its
terminal receipt signature (the chain head), or a transcript or Merkle root over the session's
receipts and artifacts. This is a seal-format change with its own adversarial vector: a
same-count, post-disclosure receipt replacement must fail verification.

### 3. Rotation: a registry entry (format)

A registry may contain a **rotation entry**: the successor public key and `keyId`, signed by the
key being retired, at a defined position in the registry's append-only order. Verifiers pin the
*genesis* key (or a key set) and walk rotations. Two bounds are stated up front rather than
discovered later:

- **Handover versus hijack.** A rotation signed only by the old key cannot distinguish succession
  from theft — an attacker holding the current key rotates to a key they control and the chain
  remains valid. An anchored rotation entry plus out-of-band confirmation narrows this; nothing in
  this RFC closes it.
- **Open sessions.** Receipts are signed at acquisition; a session enters the registry only at its
  seal. A session open across a rotation would hold old-key receipts under a successor-key seal,
  which no single-key rule verifies. The sketch's choice space, deliberately unresolved: forbid
  rotation while any session is open (one key per session, simplest), or define receipt epochs and
  mixed-key verification. Either needs late-old-key and open-across-rotation adversarial cases.

### 4. Anchoring: an external checkpoint (format)

Periodically, the gateway signs a **checkpoint** — the registry's current length and a hash over
its canonical prefix, with the signing `keyId` — and publishes it *outside* itself. Given
content-binding seals (part 2), a stolen key can then forge only forward from the last checkpoint;
without part 2, a checkpoint bounds only session existence and counts, which is not the claim that
matters. The named witnesses are **not interchangeable**, and a minimum witness contract is part
of the format work: durable retention, append-only or at least equivocation-evident behavior, and
defined verifier behavior when competing checkpoints exist. An RFC 3161 timestamp proves a digest
existed at a time — existence, not an append-only log; git signs tag or commit *objects*, never
the ref, so a ref to a signed tag protects the object's contents while the ref itself can be
replaced or deleted; a transparency log provides inclusion and consistency proofs at the cost of
infrastructure. The witness must be pinned out of band exactly as the public
key must be; anchoring relocates the out-of-band problem rather than removing it, at checkpoint
granularity, in exchange for the one property nothing else on this list buys: history that a
disclosed key cannot silently rewrite.

## Alternatives

- **No change.** The current posture is honest and the reference is explicitly not hardened. This
  is the correct alternative until someone other than the project pins a key — and the argument for
  writing the design down *before* then is that the format parts (content-binding seals, rotation,
  checkpoints) change what independent verifiers must agree on, which is cheapest to decide while
  there are none.
- **Threshold signing (FROST, RFC 9591).** Splits the signing key so no single machine holds a
  usable copy — under assumptions that must be stated to avoid the overclaim: security holds only
  below the signing threshold of compromised participants, distributed key generation (not the
  trusted-dealer variant, which briefly holds the whole secret) is what removes the single holder,
  and collusion, authorization failure, and availability sit outside the bound. Far past this
  project's stage; recorded as horizon, not proposed.
- **Switching curves for provider compatibility.** Rejected, and the pressure for it has fallen:
  AWS and GCP now offer Ed25519, so cloud custody no longer requires a curve change. Opening a
  second algorithm would be a receipt-format break and a crypto-agility door the format
  deliberately does not have; one algorithm is a feature of a reference whose value is that two
  implementations can agree on everything.
- **Replace the registry with an external transparency log outright.** Strictly stronger than
  checkpoints and strictly heavier: the localhost reference would acquire an infrastructure
  dependency to run at all. The checkpoint keeps the log optional and the reference self-contained.

## Compatibility

- Custody is invisible on the wire; no verifier can tell which backend signed.
- Checkpoints are additive. A verifier that ignores them keeps exactly today's guarantees.
- Content-binding seals and rotation entries are format changes, and the current verifier's actual
  behavior on them is **fail-open, not failure**: the registry loader silently skips entries it
  cannot parse into the existing seal shape, so a rotation-unaware verifier would ignore a
  rotation entry — and possibly still answer `ok` — until successor-signed material appears. That
  silence is the argument for an explicit registry version or entry envelope that unaware
  verifiers *reject*, in the spirit of version 2's deliberate rejection of version 1.

## Security and privacy

- **Rotation hijack** is the serious new surface and is stated in the sketch: possession of the
  current key is possession of the succession. Any acceptance of part 3 without part 4 should say
  what it is accepting.
- **The witness is a new trust dependency.** An impostor witness is the same attack class as the
  impostor gateway `SECURITY.md` already describes: internal consistency proving itself. Hence the
  minimum witness contract in the sketch — retention, equivocation evidence, competing-checkpoint
  behavior — and the out-of-band pin the witness needs exactly as the public key does.
- **Checkpoint metadata.** A checkpoint discloses registry length and cadence to the witness —
  activity metadata, no content. Worth one sentence in operator guidance; not a blocker.
- **Custody backends can weaken silently** — a forwarded agent socket, a permissive PKCS#11
  module, an `exportable` flag, or a long-lived cloud credential that outlives the compromise it
  was stolen in. The catalogue states each backend's bound and its conditions rather than ranking
  backends as uniformly "more secure."

## Conformance

Cases would extend the gateway's frozen corpus, in its existing style: positive (a content-binding
seal verifies over an untouched session; a registry with a valid rotation chain verifies; a
checkpoint matches its registry prefix), negative (a rotation entry not signed by its predecessor;
a checkpoint under an unknown `keyId`; a registry shorter than its last checkpoint), boundary (a
session sealed at the rotation position; a checkpoint at registry genesis), adversarial (a
same-count receipt replacement after key disclosure — the vector part 2 exists for; a pre-rotation
registry replayed whole under the retired key; a forked succession — two rotation entries from one
predecessor; a rotation entry presented to a rotation-unaware verifier, which must fail closed
under the envelope rather than silently pass).

## Implementation

Two independent implementations are plausible and none exists; this RFC's own bar is unmet.

1. The reference gateway: the formats are implementable stdlib-only. The custody seam is *not* a
   small refactor — the seed backs both signing and the keyed arguments commitment, so the seam
   either splits the commitment secret (new provisioning semantics) or defines a two-operation
   backend interface. That design cost is part of what this RFC exists to record.
2. An independent verifier checked against frozen content-binding-seal, rotation, and checkpoint
   vectors — the corpus pattern the gateway already uses for receipts and seals, extended to the
   new entry types. The project's existing clean-room protocol applies, with the usual caveat that
   a second implementation built by this project evidences precision, not interoperability.

An ssh-agent custody backend would additionally demonstrate the signing half of the seam with no
new dependencies, but demonstrates no format and counts toward nothing.

## Unresolved questions

1. **Does anchoring pay?** It converts "disclosure forges history" into "disclosure forges since
   the last checkpoint," at the cost of a seal-format change *and* pinning a second party out of
   band. Whether that trade is worth two formats — or whether the honest answer is that a
   single-operator reference should simply say *history dies with the key* — is the question the
   checkpoint sketch exists to make askable.
2. **What authorizes a rotation?** Predecessor signature alone is hijackable; a ceremony
   (anchored entry + out-of-band confirmation) is heavier than the reference wants to be. No
   position is taken here.
3. **How do open sessions and rotation compose?** One key per session is simplest and blocks
   rotation behind session lifecycle; receipt epochs verify mixed sessions and multiply the
   verifier's state. Neither is chosen here.
4. **Is the arguments-commitment secret one secret or two?** Splitting it from the signing seed
   cleans the custody seam and doubles the provisioning surface; deriving it keeps one artifact
   and welds the two operations to one backend.
5. **Checkpoint cadence.** Per seal, per N entries, or on demand — and stated without wall-clock
   claims the gateway otherwise avoids making.
6. **Where custody guidance lives.** The backend catalogue may belong in the gateway's
   `SECURITY.md` rather than any specification text; custody is operations, not format.
7. **Whether this record should later live beside its implementation.** This is the first
   cross-project exploratory record under the provision the same pull request adds to
   [RFC 0000](0000-rfc-process.md), which defines what a disposition here can mean: endorsement
   of the record, never authority over the gateway. What stays open is narrower — whether, once
   any part of this is implemented, the record should move to the gateway repository so the
   design record and the artifact it governs share a home. Either answer is a reasonable outcome
   rather than a failure of this RFC.

# RFC 0011: A currency anchor for judgment artifacts — detecting staleness and rollback across the receipt boundary

- Status: Draft
- Type: Exploratory (research line — a cross-project artifact, outside JPS)
- Created: 2026-08-10

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **Scope note, load-bearing.** Nothing this RFC proposes lands in JPS Core, a profile, or a
> conformance class. If accepted, the parts land across repositories: the *identity* it keys on is
> the pack manifest ([RFC 0001](0001-pack-manifest.md)) and Core §5; the *index format* is a facet
> of pack discovery ([RFC 0005](0005-pack-discovery.md)) or a sibling of it; the *verification
> ceremony* it reuses is the [reference gateway's](https://github.com/Judgment-Pack/judgment-pack-gateway)
> registry-anchored offline check; the local precedent it generalizes is the reference runtime's
> reviewed-set lock; and the *consumer step* lands in whichever receipt or execution-verification
> protocol chooses to consult it. It is recorded under [RFC 0000's](0000-rfc-process.md)
> cross-project exploratory provision: a disposition here endorses (or declines) the design record
> as written and confers no authority over any owning repository, each of which decides by its own
> process. In particular it proposes **no** change to the gateway: the gateway's scope forbids it,
> and this record honors that (see Alternatives). The [architecture vision's](../docs/architecture/vision.md)
> statement — that these downstream questions establish binding and lineage, never that a policy or
> a fact is true — remains true with this RFC merged. It is recorded here because the design
> question is currently invisible: [Study 014](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/014-openworkproof-binding)
> *measured* a boundary — two attacks that no verification layer catches — and nothing anywhere
> records what closing it would take.

## Summary

A judgment authorizes an action, a receipt protocol binds the two, and an offline verifier later
proves the binding held. Two attacks survive every such proof, because the artifacts they produce
are internally consistent:

1. **Staleness** — a genuine judgment, correct when made, is reused after the policy it applied has
   been superseded. Every digest still matches; the decision is simply out of date.
2. **Rollback** — a decision is re-derived, coherently and with valid signatures, under an older
   version of the policy that would decide differently. Nothing in the chain records that a newer
   version exists.

Neither is detectable from inside the chain, and that is not a gap in any one verifier: a chain is a
closed, self-consistent object, and a holder of the relevant keys can re-mint it whole. Detection
requires an anchor **outside** the chain that states which version of a policy series is current —
a statement no receipt can carry about itself.

This RFC records the problem, sketches one direction — a **judgment currency registry**: an
append-only, independently signed, offline-verifiable statement of the current version of a pack
series, keyed on pack identity and reusing the gateway's registry-anchored verification pattern
without touching the gateway — and states plainly the one thing that makes currency genuinely hard,
which the sketch does not solve: a currency check needs a notion of *now*, and JPS and the gateway
both deliberately have none.

## Problem

[Study 014](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/014-openworkproof-binding)
composed the reference evaluator with an independently developed receipt protocol
([OpenWorkProof](https://github.com/dengyier/OpenWorkProof)) and tried, one mutation at a time, to
break the binding between a judgment and the action a receipt chain represents. Its verifier catches
substitution of the pack, the facts, the disposition, and the action; it catches tampered
signatures, broken causal chains, and out-of-window authorization. Its registered matrix contains
exactly two cells that **no layer catches, by construction, registered as expected-undetected
before the study ran** and confirmed undetected in the frozen primary attempt:

- **`e18` — staleness.** The baseline chain, verbatim, in a world where the pack series has since
  published a newer version. No retained byte differs from a valid decision, because none can:
  currency is not a property of the artifact, it is a relation between the artifact and a world that
  moved.
- **`e22` — rollback.** A fully consistent chain re-minted under an alternative, older, laxer policy
  artifact. The receipt protocol has no version ordering over policy artifacts — an older one is a
  different, equally valid contract — so a rollback and a first-time decision are indistinguishable
  to it.

The same question arrived independently from the other side of the composition: the OpenWorkProof
author, reviewing the study, named the missing piece as an *external anchor* and asked where it
should live, listing a transparency service, a monotonic registry, and a trusted current-version
pointer as candidates. Two independently designed systems reached the same boundary from opposite
directions. That convergence is the evidence that the boundary is real and not an artifact of either
design.

What is **not** inherent here — the part worth recording — is that JPS already owns every primitive
this needs except the anchor itself:

- **Identity and version exist.** Core §5 gives a pack a series identity (an absolute-URI `id`) and
  a `MAJOR.MINOR.PATCH` `version`, independent of `specVersion`. [RFC 0001](0001-pack-manifest.md)
  proposes a `contentHash` over the canonical pack bytes. The thing a currency statement would name
  — *this series, this version, this digest* — is already expressible.
- **A local currency statement already exists.** The reference runtime's reviewed-set lock
  (`jpack.lock.json`) pins a set of pack digests as the reviewed, current set for a project, and the
  audit trail records the pack digest a decision was made under. That is a "these are current"
  statement — but it is *local* to the project that wrote it and carries no independent signature a
  third-party verifier could pin. It is the right shape at the wrong scope.
- **The verification mechanism already exists, one repository over.** The gateway's sealed-session
  registry is an anchor that lives *outside* the store it checks: given the registry and a pinned
  public key, a verifier decides **offline** — no network — whether a store has replayed a whole
  session, rolled its receipt count back (`tail-rollback`), or exceeded its sealed high-water mark,
  and re-sealing a session is refused so a count cannot be walked backward. That is precisely the
  monotonic, out-of-store, offline-verifiable anchor shape the problem calls for.

So the anchor is a missing *artifact*, not a missing *capability*. Affected users: any relying party
that acts on a judgment whose freshness matters — which is any judgment over a policy that can
change. Today the only defense is that the relying party pins the exact version it expects and
rejects everything else (see Alternatives), which works for one verifier trusting one publisher and
does not scale to open verification.

## Evidence

- **The two registered cells and the frozen run.** `e18` and `e22` are registered in Study 014's
  matrix as `expected-undetected` with the rationale "currency is not chain-internal; detecting it
  needs an anchor outside the chain," and the frozen primary attempt records both passing all three
  verification layers. This is not a verifier that failed to look; it is a boundary that was
  predicted, registered before results, and measured. See the study's
  [`ANALYSIS.md`](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/blob/main/studies/014-openworkproof-binding/ANALYSIS.md).
- **The gateway proves the mechanism works.** The registry-anchored offline check is not
  hypothetical: it ships, with a frozen corpus, and catches whole-session replay and count rollback
  today — over acquisition sessions. What is unproven is the *subject change*, not the machinery.
- **The reviewed-set lock proves the local statement works.** A signed-by-nobody, local "current
  digests" statement is already consumed by the runtime. What is unproven is the *scope change* —
  from a project's own lock to an independently pinnable anchor — not the concept.
- **Independent convergence.** The receipt-protocol author reached the same "needs an external
  anchor" conclusion without access to the study's internal reasoning, from the protocol side. Two
  parties, two designs, one boundary.

## Specification (sketch)

Field names and canonical forms are deliberately not fixed here; whichever repository owns the
artifact governs its canonicalization, exactly as [RFC 0010](0010-gateway-signing-identity.md)
defers to the gateway's `SPEC.md`.

### 1. What the anchor states (format)

A **currency registry** is an append-only, independently signed log. Each entry binds a pack
*series* to a *current version* and its content digest — `(seriesId, version, contentHash)` — signed
by an authority the verifier pins out of band, at a defined position in an append-only order. "Which
digest is current for this series" is the whole of the claim. The registry states currency; it does
**not** state that the decision was correct, that the facts were true, or that the action was
authorized — those remain outside every layer, here as everywhere.

Two properties are load-bearing and mirror the gateway's registry directly:

- **Monotonicity.** A version may not be walked backward: an entry that supersedes `seriesId` must
  advance its position, and re-publishing an earlier version at a later position is refused, the way
  the gateway refuses to re-seal a sealed session. This is what turns rollback (`e22`) from
  invisible into a detectable regression against the anchor.
- **Supersession, not just latest.** A series may have several *currently supported* versions, not
  one — a security-patched `1.4.2` and a `2.0.0` may both be current while `1.4.1` is not. Currency
  is therefore membership in a current set, not equality with a single maximum. The entry shape must
  express a supported set and its retirements, or the anchor will force a false "one live version"
  model onto real policy lifecycles. (This is the sketch's least-settled format decision; see
  Unresolved.)

### 2. What a verifier does with it (consumer step)

A verifier already holds, from the chain it is checking, the pack identity and digest the decision
was made under — Study 014's commitment carries exactly `(packId, packVersion, packDigest)`, and the
gateway/runtime lock carries the digest natively. The added step is one comparison against a
**retained snapshot** of the currency registry, pinned and verified under the authority's key
exactly as the gateway's registry is:

1. Verify the chain as today (nothing changes here).
2. Extract `(seriesId, version, contentHash)` from the verified chain.
3. Verify the retained currency-registry snapshot's signature under the pinned authority key.
4. If the chain's `(version, contentHash)` is not in the series' current set at that snapshot,
   the decision is **stale or rolled back** — the registered `e18`/`e22` outcome, now caught.

The step is receipt-protocol-agnostic in principle: it reads only pack identity, which any protocol
that binds a judgment already carries. Whether it can be *specified* portably or must be restated
per protocol is open (see Unresolved).

### 3. Where it lives (cross-project placement)

- The **identity** it keys on is [RFC 0001](0001-pack-manifest.md) + Core §5 — no new identity.
- The **format** is a facet of, or a sibling to, pack discovery ([RFC 0005](0005-pack-discovery.md)),
  which already spans "specification (format) + product (service)": a discovery index that answers
  "what versions of this series exist" is one field short of answering "which are current."
- The **verification pattern** is the gateway's `verify_with_registry` shape, reused — not extended
  in the gateway. A separate verifier, or a runtime subcommand, consumes the snapshot.
- The **local precedent** is the reviewed-set lock; a signed, publishable currency registry is that
  lock's third-party-pinnable generalization.
- The **consumer step** lands in each protocol that opts in — a JPS-side reference verifier, and,
  independently, OpenWorkProof or any other receipt protocol, by its own decision.

Nothing in this list is the gateway growing a policy authority, and nothing is JPS Core acquiring a
registry. The artifact is new; every part it reuses stays where it is.

## Alternatives

- **No change — pin the exact version at the verifier.** The null option, and the correct one for a
  single relying party trusting a single publisher: the verifier hardcodes the `(version,
  contentHash)` it will accept and rejects all others. This *does* catch `e18`/`e22` for that
  verifier — it is a currency registry of size one, held privately. It fails only when verification
  must be open: when a party who did not configure the pin must still tell current from stale. The
  argument for writing the anchor down is exactly the gateway's argument in
  [RFC 0010](0010-gateway-signing-identity.md) — the format is cheapest to agree on before there are
  many verifiers, not after.
- **Reuse the reviewed-set lock as-is.** Rejected as insufficient, not wrong: the lock is a local
  project artifact with no independent signature, so a third party cannot pin it. It is the right
  data at the wrong scope, and the currency registry is its generalization, not its replacement.
- **Grow the anchor inside the gateway.** Rejected on scope, firmly. The gateway "does not decide
  anything," and its `CONTRIBUTING` forbids a receipt asserting that its contents are true or that an
  action was authorized "no matter how convenient." "Which policy version is current" is a decision
  about policy authority — precisely what the gateway refuses to hold. Study 014 respected that
  boundary; this RFC does too. The gateway lends its *registry pattern*; it does not host the
  subject.
- **A full transparency log outright.** Strictly stronger and strictly heavier, the same trade
  [RFC 0010](0010-gateway-signing-identity.md) records for checkpoints: inclusion and consistency
  proofs at the cost of standing infrastructure. For a cross-party currency oracle this may in fact
  be the right end state (see Security and privacy); the append-only signed registry is the
  self-contained step that does not require it on day one.

## Compatibility

- The consumer step is **additive**. A verifier that does not consult a currency registry keeps
  exactly today's guarantees and today's blind spot — it simply does not catch `e18`/`e22`, which is
  the current state. No existing verification result changes.
- No JPS format changes. The registry keys on existing identity; the chain artifacts a protocol
  already produces are unchanged.
- The migration risk is **silent non-consultation**: a verifier that believes it checks currency but
  holds a stale or absent snapshot gets a false sense of freshness. The registry snapshot must
  therefore be a pinned, dated, signed input the verifier reports on — not an optional lookup whose
  absence passes quietly. This mirrors [RFC 0010's](0010-gateway-signing-identity.md) fail-open
  warning: an unaware or under-provisioned verifier must be made to *reject*, not to pass.

## Security and privacy

- **The registry is a new trust dependency, pinned out of band.** An impostor currency registry is
  the same attack class the gateway's `SECURITY.md` and [RFC 0010](0010-gateway-signing-identity.md)
  already name: internal consistency proving itself. The authority key must be pinned exactly as the
  gateway's public key must be; the anchor relocates the out-of-band problem to the currency
  authority rather than removing it.
- **Who signs is the crux, and it is a policy-authority question, not a crypto one.** If the pack
  publisher signs its own currency, the anchor detects third-party rollback but trusts the publisher
  not to lie about its own supersessions; a neutral log signing over what publishers assert detects
  publisher equivocation at the cost of the infrastructure the transparency-log alternative names.
  This is the single largest unresolved question and is stated as one.
- **Metadata disclosure.** A currency registry reveals a policy series' version cadence and
  retirements to anyone who reads it — activity metadata about how often a policy changes. Usually
  benign, occasionally not; worth one sentence in guidance, not a blocker.
- **The freshness floor.** A currency check is only as current as the retained snapshot. A verifier
  offline against a month-old snapshot cannot detect a supersession that happened last week — it has
  simply moved the staleness from the decision to the anchor. This does not defeat the mechanism
  (rollback to a version retired *before* the snapshot is still caught), but it means "fully offline"
  and "detects staleness in real time" cannot both be true. See Unresolved.

## Conformance

Cases would follow the gateway's frozen-corpus style, over currency-registry vectors: positive (a
chain whose `(version, contentHash)` is in the series' current set at the snapshot verifies), negative
(a version retired at or before the snapshot fails; a registry entry signed under an unpinned
authority fails; a snapshot whose signature does not verify fails closed), boundary (a version
retired at exactly the snapshot position; a series with a multi-version current set, one member
present and one retired), adversarial (a rolled-back entry re-publishing an earlier version at a
later position, which the monotonicity rule must reject; a currency snapshot presented to a
currency-unaware verifier, which must fail closed under an explicit envelope rather than silently
pass; a chain whose pack digest matches a *retired* version whose bytes still validate structurally —
the `e22` vector, now caught by the anchor rather than missed).

## Implementation

Two independent implementations are plausible and none exists; this RFC's own bar is unmet.

1. A **currency-registry writer and offline verifier**, stdlib-shaped, reusing the gateway's
   `verify_with_registry` structure over the new entry type. The reviewed-set lock supplies the
   local writer's data model; the gateway supplies the offline-check pattern. The clean-room caveat
   from the project's protocol applies: a second implementation built by this project evidences
   precision, not interoperability.
2. A **consumer step in an independent receipt protocol** — OpenWorkProof is the natural first, since
   Study 014 already carries `(packId, packVersion, packDigest)` in its commitment and its adapter
   verifier already runs an offline ceremony the currency check would slot into as one more step.
   That it would be built by the protocol's own author, by its own process, is the point of the
   cross-project provision, and the strongest available evidence that the anchor interoperates rather
   than that one project agrees with itself.

A JPS-side reference verifier consuming a currency snapshot demonstrates the check but, built here,
counts toward interoperability the way a second in-house implementation does — as precision, not
independence.

## Unresolved questions

1. **Who signs currency?** The publisher (detects third-party rollback, trusts the publisher about
   its own supersessions) or a neutral log (detects publisher equivocation, needs infrastructure).
   No position is taken; this is the question the whole record exists to make askable, and it is a
   governance question wearing a format's clothes.
2. **Latest, or current set?** Real policy series support several versions at once. An anchor that
   models "the latest" is simpler and wrong for security-patch backports; an anchor that models a
   current *set* with retirements is right and multiplies the verifier's state and the adversarial
   surface. The sketch leans to the set and does not fix its shape.
3. **The freshness floor.** A currency check needs a notion of *now* that JPS and the gateway both
   deliberately refuse to hold — the gateway signs `sealedAt` and never validates it. An offline
   snapshot pushes "now" to snapshot time. Whether a currency anchor can stay honestly offline, or
   whether real-time staleness detection is irreducibly an online property (and therefore outside the
   line's offline-first posture), is the deepest open question, and the honest answer may be that
   offline currency detects *rollback below the snapshot* but not *staleness above it*.
4. **One RFC or a facet of 0005?** Pack discovery already answers "what versions exist." Currency is
   one field and one signature away. Whether this is [RFC 0005's](0005-pack-discovery.md) natural
   extension or a sibling record is undecided, and the answer decides where the format eventually
   lands.
5. **Portable consumer step, or per-protocol?** The comparison reads only pack identity, which
   suggests a portable specification; but each receipt protocol expresses that identity in its own
   binding, which suggests a per-protocol restatement. Whether one normative "how to consult a
   currency anchor" can serve OpenWorkProof, a JPS-side verifier, and the next protocol is open.
6. **Whether this record should later live beside its implementation.** Like
   [RFC 0010](0010-gateway-signing-identity.md), if any part of this is built, the design record may
   belong in the repository that owns the artifact — pack discovery's, a currency-registry
   repository's, or the runtime's — rather than here. Either answer is a reasonable outcome, not a
   failure of this RFC.

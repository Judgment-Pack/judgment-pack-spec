# RFC 0011: A currency anchor for pack versions — detecting stale and retired policy across the receipt boundary

- Status: Draft
- Type: Exploratory (research line — a cross-project artifact, outside JPS)
- Created: 2026-08-10

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **Scope note, load-bearing.** Nothing this RFC proposes lands in JPS Core, a profile, a
> conformance class, or any other RFC's specification-track surface. It *references* existing
> identity — Core §5's series `id` and `version`, and [RFC 0001](0001-pack-manifest.md)'s proposed
> pack digest — but proposes no change to them. If accepted, every proposed part lands in another
> repository: the currency-registry **format**, its **writer**, and an **offline verifier** land in
> the [reference runtime](https://github.com/Judgment-Pack/judgment-pack-runtime), generalizing its
> reviewed-set lock; the **consumer step** lands in each receipt or execution-verification protocol
> that chooses to consult the registry — [OpenWorkProof](https://github.com/dengyier/OpenWorkProof)
> first — by that protocol's own process. It proposes **no** change to the
> [reference gateway](https://github.com/Judgment-Pack/judgment-pack-gateway): the gateway's scope
> forbids it holding a policy authority, and this record honors that (see Alternatives). It borrows
> the gateway's *offline-comparison-against-a-pinned-snapshot* pattern as prior art and names
> everything the currency problem needs beyond it as new. Whether the format should later become
> standards-track pack-discovery work ([RFC 0005](0005-pack-discovery.md)) is an open question
> (Unresolved #4), not a destination proposed here. It is recorded under
> [RFC 0000's](0000-rfc-process.md) cross-project exploratory provision: a disposition here endorses
> (or declines) the design record as written and confers no authority over any owning repository.
> The [architecture vision's](../docs/architecture/vision.md) statement — that these downstream
> questions establish binding and lineage, never that a policy or a fact is true — remains true with
> this RFC merged. It is recorded here because the design question is currently invisible:
> [Study 014](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/014-openworkproof-binding)
> named a limitation it could not measure, and nothing anywhere records what addressing it would
> take.

## Summary

An action is taken in reliance on a judgment, a receipt protocol binds the two, and an offline
verifier later proves the binding held. One class of problem survives every such proof, because the
artifacts it produces are internally consistent: a judgment made under a **pack version that has
since been retired** is reused, or re-derived, after the version it applied is no longer current.
Every digest still matches; what changed is that the version the decision names is no longer in the
series' supported set, and no receipt can carry a true statement about its own currency. Whether a
decision in that position may still be relied upon is a separate question this record does not
answer (Specification §2a).

Detecting this requires an anchor **outside** the chain that records which versions of a pack series
are currently in force. This RFC records the problem and sketches one direction — a **pack-version
currency registry**: an append-only, independently signed history of add/retire/reinstate events
over a pack series, verified offline against a pinned snapshot, keyed on pack identity, and reusing
the gateway's snapshot-comparison pattern without touching the gateway. It scopes the claim
narrowly and states, up front, three things the sketch does not settle and one thing it cannot do:

- It addresses **pack-version staleness** only. It does **not** address a decision re-minted under a
  different *authorization contract* while the pack is unchanged — that is a property of the receipt
  protocol's own authorization state, not of pack currency (see Problem, and Study 014's `e22`).
- Who is authorized to speak for a series' currency is a trust-mapping question the sketch does not
  answer (Unresolved #1).
- A currency check needs a notion of *now* that JPS and the gateway deliberately refuse to hold, so
  an offline check establishes only **membership at the pinned snapshot** — not real-time staleness
  (Unresolved #3, and Security).

## Problem

[Study 014](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/014-openworkproof-binding)
composed the reference evaluator with an independently developed receipt protocol
([OpenWorkProof](https://github.com/dengyier/OpenWorkProof)) and tried, one mutation at a time, to
break the binding between a judgment and the action a receipt chain represents. Its verifier catches
substitution of the pack, the facts, the disposition, and the action; tampered signatures; broken
causal chains; and out-of-window authorization. In registering its mutation matrix it also recorded,
in a section titled *analytic limitations* (its `PREREGISTRATION.md` §4c), two things its machinery
**cannot** measure and therefore does not score:

- **Staleness of the pack version.** A decision correct under pack version `V` at decision time,
  reused after `V` has been superseded. No retained byte differs from a valid decision, because
  currency is not a property of the artifact — it is a relation between the artifact and a world that
  moved. The study removed its illustrative `e18` row precisely because it is baseline bytes plus an
  unobservable scenario: there is nothing to put in a fixture. It is an analytic limitation, not a
  measured result, and this RFC treats it as one.
- **Rollback of the authorization contract.** The study's `e22` is a *descriptive* row (excluded
  from its endpoint, marked "alternative valid WorkOrder remint accepted"): the same judgment —
  identical `(packId, packVersion, packDigest)` — re-bound under a different, older OpenWorkProof
  work order. This RFC's registry would **accept** `e22`, because the pack version did not change;
  what rolled back was the receipt protocol's authorization contract, not the pack. `e22` is named
  here to draw the boundary, not as something a pack-version anchor detects. Authorization-contract
  currency is the receipt protocol's own problem; it is out of scope.

The same missing piece was raised from the protocol side: a receipt-protocol
implementer reviewing the study observed that closing the gap needs an *external anchor* and asked
where it should live. That remark is motivating context, not evidence — it is not a citable public
artifact and it establishes only that the question was asked, not that two designs provably
converged.

What is worth recording is that JPS already owns the *identity* such an anchor would key on, and
nothing more:

- **Identity and version exist; their digest does not, yet.** Core §5 gives a pack a series identity
  (an absolute-URI `id`) and a `MAJOR.MINOR.PATCH` `version`; §11 makes a published `(id, version)`
  immutable only at SHOULD strength, and defines no precedence, supersession, or retirement over
  versions. [RFC 0001](0001-pack-manifest.md) *proposes* a `contentHash` but is Draft and leaves both
  the digest algorithm and the canonicalization unresolved; Core §13 lists content identity,
  canonicalization, and signatures as open. So "this series, this version, this digest" is
  *nameable*, but the digest it names is not yet an agreed portable value — a prerequisite, not a
  given (see Specification §0).
- **A local, unsigned digest inventory is precedent.** The reference runtime's reviewed-set lock
  (`jpack.lock.json`) is a deterministic, project-local list of pack digests with drift refusal, and
  its ADR is explicit that it approves nothing. It is precedent for *a local digest inventory that
  refuses drift* — and nothing more. It has no series identifier, no version, no supported-set or
  retirement notion, no history, no append-only order, and no independent signature a third party
  could pin. The currency registry's identity, lifecycle, history, signature, and trust model are all
  new; only the "deterministic digest inventory" shape is borrowed.
- **Offline comparison against a pinned snapshot is demonstrated, one repository over.** The gateway
  shows that a verifier can decide, offline and with no network, whether a store agrees with a
  separately trusted, signed snapshot, and flag a count mismatch against it. That is the *pattern*
  the currency check reuses. It is emphatically **not** authenticated append-only history: the
  gateway's seal binds a session's *count*, not its contents (RFC 0010 §2 exists to fix exactly
  that), its "replay" check merely notices a session absent from the snapshot, and refusing to
  re-seal is writer behavior, not third-party proof that history was not rewritten. Everything the
  currency problem needs beyond "compare against a pinned snapshot" — an authenticated registry head,
  a prefix-consistency rule, a lifecycle state machine, and an authority model — is new machinery,
  named as such below.

So the anchor is a missing *artifact* whose hardest parts are genuinely unsolved. Affected users: any
relying party that acts on a judgment whose pack version can be retired — which is any long-lived
policy. Today the only defense is that the relying party pins the exact version it expects and
rejects everything else (see Alternatives).

## Evidence

- **Study 014's analytic-limitations section and its frozen run.** §4c registers pack-version
  currency as unmeasurable-by-construction and gives the reasoning; the frozen primary attempt scored
  39 cells with `e18` absent (removed, not measured) and `e22` present only as an excluded
  descriptive row. The evidence this RFC draws is the *registered reasoning that the class is not
  chain-internal*, not a pair of measured cells — an earlier draft of this RFC, and a sentence in the
  study's own post-run `ANALYSIS.md`, both overstated it as "two registered expected-undetected
  cells"; that sentence is inaccurate against the pinned matrix and is being corrected in the study's
  `DEVIATIONS.md`.
- **The gateway proves the comparison pattern, at its stated strength.** Offline comparison against a
  pinned, signed snapshot ships, with a frozen corpus — over acquisition sessions, binding counts.
  What is unproven is every part the currency problem adds: content-bound history, a lifecycle state
  machine, and an authority for the assertion.
- **The reviewed-set lock proves the local inventory shape.** A deterministic local digest list with
  drift refusal is consumed by the runtime today. What is unproven is the *signed, third-party
  pinnable, versioned-with-history* generalization — which is most of the design.

## Specification (sketch)

Field names and canonical forms are deliberately not fixed here; the owning repository governs them,
exactly as [RFC 0010](0010-gateway-signing-identity.md) defers to the gateway's `SPEC.md`.

### 0. Prerequisite: one agreed pack digest (not owned here)

The whole mechanism rests on chain, manifest, and registry naming the *same* digest for the same
pack. That agreement does not exist yet: [RFC 0001](0001-pack-manifest.md) leaves the algorithm and
canonicalization open, and Study 014 uses SHA-256 over exact retained bytes as an expedient, not an
agreed canonical hash. A currency registry cannot be built portably until either RFC 0001's digest
scheme is settled, or an algorithm-qualified digest representation (e.g. `sha256:<hex>` over an
exactly specified byte sequence) is fixed and required of every producer and consumer. This RFC does
not settle it; it records the dependency as hard.

### 1. What the anchor states — a signed event history (format)

A **currency registry** for a pack series is an append-only, independently signed log of lifecycle
**events**, not a table of "the current version." Each event is one of:

- **add** `(seriesId, version, digest)` — this immutable `(version, digest)` binding enters the
  supported set;
- **retire** `(seriesId, version)` — this version leaves the supported set;
- **reinstate** `(seriesId, version)` — a previously retired version re-enters (an emergency
  rollback to a known-good release is a legitimate lifecycle move, not an attack).

Each event carries an authenticated **sequence position** and binds the prior head (a hash of the
canonical prefix), so the log has an append-only order a verifier can check, not merely a set a
writer asserts. The *current supported set* of a series at any position is the fold of its events up
to that position — several versions may be current at once (a patched `1.4.2` and a `2.0.0` while
`1.4.1` is retired), so currency is membership in a set, never equality with a maximum, and version
strings carry no precedence of their own.

The security property is a property of the **history**, not of the version numbers: an event may not
silently rewrite the prefix it commits to, and `(version, digest)` bindings are immutable once added,
so a "rollback" is detectable as a prefix that disagrees with a later authenticated head — the same
place the gateway's anchoring gap (RFC 0010 §2) says content-binding must live. What this does *not*
give is a rule that forbids reinstating a retired version: reinstatement is a signed event like any
other, so the anchor distinguishes an *authorized* reinstatement from an *unauthorized* prefix
rewrite by signature and head-consistency, not by version arithmetic.

The registry states currency; it does **not** state that a decision was correct, that facts were
true, or that an action was authorized.

### 2. What a verifier does with it — membership at a pinned snapshot (consumer step)

A verifier holds, from the chain it is checking, the pack identity and digest the decision was made
under. The added step is a comparison against a **retained, signed snapshot** of the registry, pinned
under an authority key the verifier trusts for that series (Unresolved #1):

1. Verify the chain as today (unchanged).
2. Extract `(seriesId, version, digest)` from the verified chain — where the protocol exposes it
   (see Compatibility; this is not automatic).
3. Verify the snapshot's signature and its internal head-consistency under the pinned authority.
4. Fold the snapshot's events to the series' supported set **at the snapshot's position**. If the
   chain's `(version, digest)` is not in that set, report exactly **"not current at snapshot"** — no
   more.

Step 4's verdict is deliberately narrow. It is **not** "this decision was stale when used" and **not**
"this is the latest state of the world." It is membership against one pinned, dated assertion. A
legitimate decision made and used while `v1` was current, but audited after `v1` retired, produces the
same "not current at snapshot" as a genuine stale reuse — distinguishing them needs a trusted ordering
between the *action's* time and the *registry's* state that neither JPS nor this sketch provides
(Unresolved #3). And replaying an *older* signed snapshot must itself be refused, which requires the
verifier to persist a minimum accepted registry head — a rollback rule on the snapshot, not just on
the log.

### 2a. Membership does not determine continued reliance

Membership at a snapshot answers *which versions an authority asserted in force at a position*. It
does not answer *whether a particular decision may still be relied upon*. That second question —
call it a **transition rule** — is outside what this registry and §2's membership primitive
determine.

The separation is load-bearing because the same history supports more than one defensible answer.
Given a decision made under `v1` while `v1` was current, and a later position at which `v1` is
retired, one relying party may hold that every unused `v1` decision stops being usable at the
retirement event; another may allow a window; another may let decisions created while `v1` was
current run to their own expiry. Which of these applies is not settled by the history, and this
record takes no position on it: a transition rule's source (a relying party's own choice, a
contract, a regulator, the issuing authority), its binding force, where it is evaluated, and who
owns it are all outside this record's scope — and Core assigns no such authority either. A verifier
that reports membership may of course also apply a configured rule, provided the membership result
it reports is not thereby replaced.

Two consequences for what is sketched here. The format defined in §1 carries no **decision-level**
expiry, grace, or grandfathering semantics — `retire` moves a version out of the supported set at a
defined position, and says nothing about decisions already made under it. And §2 step 4's verdict
stays exactly as narrow as it is: "this `(version, digest)` is not in the supported set at this
snapshot" is a fact a transition rule can consume, not a determination that a decision is void.
See Unresolved #10 for what this leaves open and #11 for evidence such a rule might use.

### 3. Where each part lands (cross-project placement)

- The **identity** it keys on is Core §5 + [RFC 0001](0001-pack-manifest.md), **referenced, not
  changed**.
- The **format, writer, and offline verifier** land in the
  [reference runtime](https://github.com/Judgment-Pack/judgment-pack-runtime): a currency-registry
  artifact and a `jpack` verify subcommand, generalizing the reviewed-set lock. Not JPS Core, not a
  profile, not RFC 0005.
- The **consumer step** lands in each receipt or execution-verification protocol that opts in, by its
  own process — OpenWorkProof first, since Study 014's adapter already carries `(packId, packVersion,
  packDigest)` and runs an offline ceremony the step would extend.
- The **authority** that signs currency is out of band and unresolved (Unresolved #1).

Nothing in this list is the gateway growing a policy authority, and nothing is JPS Core acquiring a
registry.

## Alternatives

- **No change — pin the exact version at the verifier.** The null option, correct for a single
  relying party trusting a single publisher: hardcode the accepted `(version, digest)` and reject all
  else. This is a currency registry of size one, held privately, and it addresses the stale-version
  class for that verifier. It fails only when verification must be open — when a party that did not
  configure the pin must still tell current from retired.
- **Reuse the reviewed-set lock as-is.** Insufficient, not wrong: local, unsigned for third parties,
  and carrying no version/series/history. It is precedent for the local inventory shape, not a
  third-party currency anchor.
- **Grow the anchor inside the gateway.** Rejected on scope, firmly. The gateway "does not decide
  anything," and its `CONTRIBUTING` forbids a receipt asserting its contents are true or an action
  authorized "no matter how convenient." "Which pack version is current" is a policy-authority
  statement — precisely what the gateway refuses to hold. Study 014 respected that boundary; this RFC
  does too. The gateway lends its snapshot-comparison *pattern*; it does not host the subject.
- **A full transparency log outright.** Strictly stronger and strictly heavier, the same trade
  [RFC 0010](0010-gateway-signing-identity.md) records for checkpoints: inclusion and consistency
  proofs at the cost of standing infrastructure. For a cross-party currency authority it may be the
  right end state; the append-only signed registry is the self-contained step that does not require
  it on day one, at the cost that an isolated offline verifier cannot detect a signer's split view.

## Compatibility

- The consumer step is **not** purely additive, and the earlier draft's claim that it was is
  withdrawn. A currency-unaware verifier over unchanged artifacts cannot be made to fail closed by
  the registry alone; making an unaware verifier *reject* rather than silently skip requires a
  versioned envelope in the consuming protocol — itself a protocol change, per protocol. What *is*
  additive is the guarantee for verifiers that do not adopt it: they keep exactly today's behavior and
  today's blind spot.
- The step is **not** protocol-agnostic. Core's portable disposition exposes only `kind`,
  `outcomeId`, `reasons`, and `handoff`; JPS defines no receipt chain; a protocol may bind opaque
  judgment bytes without surfacing `(seriesId, version, digest)` at all. OpenWorkProof carrying the
  tuple demonstrates OWP's fit, not a portable interface. Whether one specification can serve multiple
  protocols, or each must restate the extraction and envelope, is open (Unresolved #5).
- No JPS format changes. The registry references existing identity; but see §0 — a shared digest is a
  hard prerequisite, and "already nameable" is not "already portable."

## Security and privacy

- **The registry is a new trust dependency, pinned out of band.** An impostor registry is the same
  attack class the gateway's `SECURITY.md` and [RFC 0010](0010-gateway-signing-identity.md) name:
  internal consistency proving itself. The authority key is pinned exactly as the gateway's public key
  is; the anchor relocates the out-of-band problem to the currency authority.
- **Who signs is the crux, and it is a policy-authority question.** Core §10 forbids treating a URL or
  publisher label as authenticity, so an absolute-URI `seriesId` supplies syntax, not an authenticated
  owner: a verifier pinning a key must be told, out of band, that the key is authoritative *for that
  series*. Publisher-signing and neutral-log models need different artifacts — series-to-key
  delegation, rotation, and revocation for the first; inclusion proofs that attest inclusion, not
  currency authority, for the second, which cannot alone detect publisher equivocation for an isolated
  offline verifier. No model is chosen (Unresolved #1).
- **The freshness floor.** A currency check is only as current as the pinned snapshot; an offline
  verifier against a month-old snapshot cannot see last week's retirement. This does not defeat the
  mechanism — a version retired *before* the snapshot is still reported as not current at it — but "fully offline" and
  "detects staleness in real time" cannot both hold, and the honest verdict is membership at the
  snapshot, not real-time staleness (Unresolved #3).
- **Metadata disclosure.** A signed lifecycle history reveals, to anyone who can read a snapshot, a
  policy series' version cadence and its retire/reinstate activity — how often a policy changes, and
  when a version was pulled or brought back. That is activity metadata, not judgment content, and it
  is usually benign; occasionally it is not (a retirement can telegraph a discovered defect before an
  operator is ready to say so). It warrants a sentence in operator guidance and an access decision on
  who may read a series' currency, not a format change.
- **Resource risk of an unbounded append-only history.** A registry and its snapshots grow without
  bound, and a verifier folds an event history it did not author. Without limits, an oversized
  snapshot, an oversized series, or an oversized supported set is a denial-of-verification vector.
  Implementation limits (maximum snapshot bytes, events per series, current-set size) and fail-closed
  behavior above them are part of the format work, not an afterthought.

## Conformance

Cases would follow the gateway's frozen-corpus style, over currency-registry vectors:

- **Positive** — a chain whose `(version, digest)` is in the series' supported set at the snapshot
  verifies; a snapshot with a valid head chain and authorized events verifies.
- **Negative** — a version retired at or before the snapshot fails "not current at snapshot"; an event
  signed under an unpinned authority fails; a snapshot whose signature or head-consistency does not
  verify fails closed.
- **Boundary** — a version retired at exactly the snapshot position; a series whose supported set has
  two members, one present in the chain and one retired; a snapshot at series genesis; a snapshot,
  series, or supported set at the registered size limit, and one past it (which must fail closed).
- **Adversarial** — a prefix rewrite: a later head that disagrees with an earlier one under the same
  authority, which head-consistency must reject; a replayed *older* signed snapshot presented in place
  of a newer one, which the verifier's persisted-minimum-head rule must reject; an *unauthorized*
  reinstatement (a reinstate event not under the series authority), which must fail while an authorized
  reinstatement passes — the case that separates a legitimate emergency rollback from an attack; a
  currency-unaware verifier handed a snapshot, which must fail closed only under an explicit envelope
  (and does not, without one — see Compatibility).

## Implementation

Two independent implementations are plausible and none exists; this RFC's own bar is unmet, and §0's
prerequisite is unmet too.

1. A **currency-registry writer and offline verifier** in the reference runtime, reusing the gateway's
   snapshot-comparison structure over the new event type, with the reviewed-set lock as the local
   data-model precedent. The clean-room caveat applies: a second implementation built by this project
   evidences precision, not interoperability.
2. A **consumer step in an independent receipt protocol** — OpenWorkProof is the natural first, since
   Study 014 already carries the tuple and runs an offline ceremony the step would slot into. Built by
   the protocol's own author, by its own process, it is the strongest available evidence that the
   anchor interoperates rather than that one project agrees with itself.

## Unresolved questions

1. **Who signs currency, and how is authority for a series established?** Publisher (needs
   series-to-key delegation, rotation, revocation; trusts the publisher about its own retirements) or
   neutral log (needs infrastructure; attests inclusion, not currency authority). Core §10 forbids
   inferring authority from the series URL, so the trust mapping is out-of-band and unspecified here.
   This is the largest open question and is a governance question wearing a format's clothes.
2. **What is the event/lifecycle state machine, exactly?** add/retire/reinstate is a sketch; the exact
   legal transitions, whether a digest can ever rebind, and how forks or parallel supported lines are
   modeled are unfixed. The adversarial "unauthorized reinstatement vs prefix rewrite" case is the one
   that tests it.
3. **The freshness floor.** A currency check needs a notion of *now* that JPS and the gateway
   deliberately refuse to hold. An offline snapshot pushes "now" to snapshot time, so offline currency
   detects *retirement below the snapshot* but not *staleness above it*, and cannot by itself order the
   action against the registry state. Whether real-time staleness is irreducibly online — and
   therefore outside the line's offline-first posture — is open, and the honest answer may be yes.
4. **One RFC, a runtime artifact, or standards-track pack discovery?** [RFC 0005](0005-pack-discovery.md)
   answers "what versions exist"; currency adds "which are in force," an event history and a signature
   beyond a catalog index. Whether the format eventually belongs in the runtime, in a dedicated
   repository, or as standards-track discovery work is undecided; it is **not** proposed as an RFC 0005
   amendment here.
5. **Portable consumer step, or per-protocol?** The extraction reads pack identity, which suggests a
   portable spec; but each protocol expresses that identity in its own binding and needs its own
   fail-closed envelope, which suggests per-protocol restatement. Whether one "how to consult a
   currency anchor" can serve OpenWorkProof, a runtime verifier, and the next protocol is open.
6. **The authorization-contract sibling.** Pack-version currency does not touch Study 014's `e22`
   class — a same-pack decision re-minted under a rolled-back authorization contract. Whether that
   deserves its own anchor, owned by the receipt protocol rather than by pack identity, is a separate
   question this RFC deliberately does not open.
7. **Whether this record should later live beside its implementation.** Like
   [RFC 0010](0010-gateway-signing-identity.md), if any part is built, the design record may belong in
   the repository that owns the artifact. Either answer is a reasonable outcome, not a failure of this
   RFC.
8. **Bootstrap: what a fresh verifier must be given, and under which signer model.** The consumer
   step pins an authority key for the series (Unresolved #1) and, to refuse an older-snapshot
   replay, persists a minimum accepted head (Specification §2). What is not settled is what else —
   if anything — a fresh verifier must be given before its first snapshot. A pinned publisher key
   authenticates whatever history it is first handed; but authenticity of a view is not uniqueness
   of the series' origin. Without some independently supplied starting anchor (a genesis-head pin,
   an externally obtained checkpoint, or a richer trust bundle), the verifier cannot distinguish
   the series' history from any other history the same key signed — and even with one, a fork
   placed after the anchor point is not prevented. Whether such an anchor is necessary at all, per
   signer model (a neutral-log model may require more trust artifacts, not fewer); which threat it
   addresses and which it provably does not; and how it would be distributed, and rotated when the
   authority key rotates — open, and inseparable from Unresolved #1's trust mapping.
9. **Split views of the registry itself, and what witnessing would actually require.** Distinct
   from the publisher-equivocation limit Security records for the neutral-log model: the threat
   here is the registry operator — one party holding the currency-signing key and the history —
   presenting two internally valid, contradictory histories to different fresh verifiers, or to
   one verifier at different times. Nothing in the sketch gives an isolated offline verifier a way
   to see the sibling view; its acceptance establishes membership in the view it was handed. A
   persisted minimum accepted head catches some sequential conflicting views (Specification §2),
   and no more. Making split views observable in general is the transparency-log / witness /
   cross-signing direction the Alternatives trade names — and what that direction would deliver is
   conditional on a still-unspecified witness contract: retention, cross-view comparison, verifier
   enforcement, and witness independence and non-collusion. Related, not identical:
   [RFC 0010](0010-gateway-signing-identity.md) records its own external-anchoring questions for
   the gateway — its §2 prerequisite (count-binding seals becoming content-binding) is
   gateway-specific, its §4 checkpoints are gateway-signed with witness forms expressly
   non-interchangeable, and whether anchoring is worth adopting is open there. Whether any single
   witnessing mechanism could serve both records' different threat models — or each needs its
   own — is an open question for whichever repository would own such a mechanism; nothing here
   proposes one. (A frozen — and **not yet run** —
   [preregistration in the interoperability studies](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/016-policy-currency-anchor)
   registers the fresh-verifier split view as expected-undetected cells and the persisted-head
   sequential case as a refusal; it establishes nothing until its primary attempt publishes, and
   is cited as a measurement plan, not evidence.)
10. **Where is a transition rule sourced, evaluated, and audited?** §2a states that this registry
   and §2's membership primitive do not determine continued reliance; it deliberately does not say
   where that determination happens. Open: whether a transition rule can be expressed portably at
   all or is irreducibly local to each relying party; what constrains it (a party's own choice, a
   contract, a regulator, the issuing authority) and what binding force each source carries;
   whether the registry or its authority may publish optional, explicitly non-authoritative advice
   alongside a retirement — and if so, who issues, signs, and labels it, whether Unresolved #1's
   signer models differ here (a publisher can speak about its own series in a way a neutral log
   attesting inclusion cannot), and what keeps optional advice optional in practice; and how a
   relying party's own rule is recorded and audited, since a rule applied inconsistently is
   invisible to every mechanism sketched here. What a membership-only report avoids is hard-coding
   one rule into the primitive; what a derived usability result would additionally require — the
   ordering of #3 among it — is exactly what this question asks.
11. **Would consuming artifacts cite the registry state they observed, and what would that be good
   for?** A construction raised publicly by a reader (`@circuit`) on the reference implementation's
   announcement thread
   ([dev.to thread](https://dev.to/kikashy/the-receipt-was-valid-the-policy-was-retired-164a);
   recorded as motivating context — it establishes that the construction was raised publicly, and
   nothing about its merit): a decision — and, separately, each execution acting on it — records
   the registry **head** it validated against, inside the consuming protocol's own signed
   artifacts.

   What that would establish is narrow but real: the artifact **cites a head at which `v1` was in
   the supported set**. An auditor could then state two facts side by side — the cited head, and
   membership at the head the auditor trusts — instead of the second alone. That is *one possible
   input* to a transition rule (#10), not the input such a rule needs in general: a rule that stops
   reliance at retirement needs no citation at all, while window and run-to-expiry rules need an
   ordering between the decision's use and the registry's state that the citation does not supply
   (#3). A producer that also refuses to mint against a head where the version has already left the
   supported set fails earlier rather than at audit — but that refusal is a separately chosen
   policy, together with whatever accepted-head and freshness rules the producer applies, not a
   property of the citation.

   What it does **not** establish is when the artifact was created. A cited head attests the state
   an artifact's author *claims* to have relied on: a party able to coherently re-mint can cite an
   older head deliberately, and
   [Study 014](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/014-openworkproof-binding)
   registers the narrower supporting point — a currency field inside an artifact its author
   controls cannot establish that artifact's currency (its `PREREGISTRATION.md` §4c). The analogy
   is a build that cites a commit: the commit can be shown to exist and the tree reconstructed at
   it, while the claim that the build preceded some later commit is not established by the
   citation. Separately, #9's bound applies to the citation as it applies to any head: a head binds
   one prefix unambiguously, but an isolated offline verifier cannot establish that the named view
   is the globally unique one, nor discover a sibling view.

   Open, therefore: whether the citation belongs in each consuming protocol's artifacts (it could
   land nowhere else — this record defines no receipt); what a verifier is entitled to conclude
   from one; whether the ordering gap is closable without a trusted time source; and the disclosure
   surface it would create, which the existing metadata analysis does not cover — a stable head
   identifier embedded in every signed decision and execution artifact reveals which view of a
   series an actor observed, correlates artifacts that share a head, and carries that linkage to
   every audience the artifacts reach, outliving any access control on the registry itself.

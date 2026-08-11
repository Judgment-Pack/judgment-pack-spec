# RFC 0012: What a witness contract would have to specify — candidate clauses for a signed-history comparison

- Status: Draft
- Type: Exploratory (research line — a cross-project artifact, outside JPS)
- Created: 2026-08-11

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **Scope note, load-bearing.** Nothing this RFC proposes lands in JPS Core, a profile, a
> conformance class, or any other RFC's specification-track surface. If any part is built, the
> **witness record format, its writer, an offline comparison verifier, and a conformance vector
> corpus** land in the [reference runtime](https://github.com/Judgment-Pack/judgment-pack-runtime),
> beside the currency-registry artifacts [RFC 0011](0011-judgment-currency-anchor.md) §3 places
> there — one named destination, so that this record satisfies RFC 0000's cross-project provision
> rather than deferring the choice. The **consumer step** lands in each protocol that opts in, by
> that protocol's own process; the first two candidates, named rather than gestured at, are the
> runtime's own currency verifier (which already consumes a pinned snapshot) and
> [OpenWorkProof](https://github.com/dengyier/OpenWorkProof), which
> [RFC 0011](0011-judgment-currency-anchor.md) §3 already names as the first currency consumer.
> Whether the artifacts should later move to a dedicated repository is a question for the owning
> repository, not a destination proposed here. No change is proposed to the
> [reference gateway](https://github.com/Judgment-Pack/judgment-pack-gateway), whose scope forbids
> it holding a policy authority. A disposition here confers no authority over any owning
> repository, and the [architecture vision's](../docs/architecture/vision.md) binding-and-lineage
> ceiling — never that a policy or a fact is true — is unchanged.
>
> **This record narrows a question; it does not answer one, and its clause list is not claimed
> exhaustive.** [RFC 0011](0011-judgment-currency-anchor.md) Unresolved #9 says the transparency-log
> / witness / cross-signing direction is "conditional on a still-unspecified witness contract:
> retention, cross-view comparison, verifier enforcement, and witness independence and
> non-collusion." What follows are **candidate clauses** such a contract would have to address, with
> — for the clauses where evidence exists — what one measured prototype did and did not achieve.

## Summary

A signed, append-only registry cannot be caught equivocating by a verifier holding one view of it.
The direction everyone reaches for is *witnessing*: some party records the history it observed, a
verifier compares. That direction is real, and it is also under-specified in a way that matters —
"a witness signed it" is not a property until the contract around the signature is written down.

This record proposes **seven candidate clauses** — attribution, delivery, enforcement, coverage,
**retention**, recency, and non-collusion — and states, for each, what is known and from where.
It proposes no format. Its most useful content is negative: for five clauses a frozen study
registered a cell showing what stays invisible when the clause is absent; retention has no
measurement at all and is marked as such; and non-collusion is the clause where the honest
statement is that a *comparison* mechanism does not implement it, while quorum and cosigning
mechanisms exist that change its shape without removing its governance core.

Nothing here claims the list is complete or that satisfying every clause would make equivocation
observable in general. What the cited evidence supports is narrower and is stated with its bounds
in the next section.

## Problem

[RFC 0011](0011-judgment-currency-anchor.md)'s Alternatives section names the cost of a
self-contained registry: "an isolated offline verifier cannot detect a signer's split view."
Unresolved #9 names witnessing as the direction that would buy that back, and immediately
qualifies it as conditional on a contract nobody has written.

The qualification is not hedging. A witness mechanism has a signature at its centre, and the
signature is the easy part. What decides whether a comparison means anything is the surrounding
contract: which witness a record belongs to and how that is decided; which records reach the
verifier and who controls that; how much evidence, and whose, must exist before a view is called
witnessed; what a record about one position says about later ones; how long a witness keeps and
can produce what it saw; whether a witness's longer history should refuse a shorter presented
one; and what happens when the witness and the operator share an interest.

Each is a place where a mechanism can look like it works and not work.

## Evidence

Two frozen studies in the interoperability line, both preregistered, cross-vendor reviewed, run
once from their freeze commits, results published whichever way they fell.

- **[Study 016](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/016-policy-currency-anchor)**
  (currency anchor) established the gap: a fork of a single-operator signed registry is **silent**
  to a fresh, stateless verifier holding only its out-of-band pins. It bounded that immediately —
  the same presentation is refused when the verifier is supplied a previously accepted head.
- **[Study 017](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/017-witnessed-currency)**
  (witnessed currency) measured a **sighting** — one witness key's signature over an observed
  history head — compared against a presented view, as one added layer over Study 016's frozen
  verifier.

**The standing of that evidence, stated precisely, because the clauses below rest on it.** Each
study has two strata. The **locked-replication** stratum is a conformance suite over behaviour its
maintainer had already observed during development; its verdict can be falsified by regression but
is explicitly *not* a prospective prediction. Only the **reviewer holdout** — cells authored by the
cross-vendor reviewer before the freeze and executed for the first time inside the registered
attempt — is prospective evidence. Both studies' holdouts landed concordant on first execution.

**And what the evidence is not.** Both studies are study-internal: registry, witness keys,
comparison step and verifier were written by one project. Study 017 states plainly that it is **not
an interoperability study**, and its non-claims expressly exclude interoperability, transport,
discovery, retention policy, incentives, and organisational independence. Every clause statement
below is therefore bounded to *the registered cells of a prototype*, never to witnessing in
general: what a cell did not detect is a bound on that comparator under that configuration, and
this record states no impossibility results.

## Specification (sketch) — candidate clauses

No field names or canonical forms are fixed here; the owning repository would govern them, as
[RFC 0010](0010-gateway-signing-identity.md) defers to the gateway's `SPEC.md`.

### 1. Attribution — how a record is associated with a witness

A record should be associated with a witness by **verifying its signature against a key the
verifier trusts**, rather than by a routing decision taken on an identifier the record carries
about itself. Study 017's draft routed on such an identifier, and its cross-vendor reviewer
demonstrated that relabelling an *honest, conflicting* record with an unpinned identifier caused
the comparator to ignore it, so a detected conflict became a pass. That construction is retained
in the study as a standing control. (The draft's own safety argument had been that the label could
cause a refusal but never an acceptance; the demonstration is that it could cause an acceptance.
No claim is made here that label routing cannot also cause false refusals.)

In Study 017's prototype the comparator tries each record against the configured pinned keys only,
and carries no candidate signer material; **in that design** a genuine record from an untrusted
witness is indistinguishable from a corrupted record from a trusted one. That is a property of
that schema, not of verification in general: a contract that carried authenticated signer
material — a key with a certificate, a delegation, a key-to-witness authority mapping — could
separate "valid signature, untrusted signer" from "invalid signature, claimed signer", without
trusting a self-declared routing label. What such material must carry, and how rotation and
revocation work, is open.

### 2. Delivery — what a signature cannot reach

Whoever controls which records reach a verifier can **omit** a conflicting record or **corrupt**
it so it verifies under no trusted key. Study 017 executed both as registered endpoint cells: both
passed, under a configuration where a second record satisfied the count floor. Corruption was not
wholly invisible there — it left a count of unattributable records — but a count is not a
detection. A third route, **re-signing the payload under a fresh key**, follows from the same
comparator by inference and was not executed as its own endpoint; it is named here as an inference,
not a measurement.

What generalises is narrower than "silence and suppression are the same": for an *absent* record,
this comparator cannot distinguish omission from a witness that never observed the series, never
existed, or was unreachable. A contract must therefore say who is responsible for delivery and
what a verifier may conclude from an empty set — and note that the answer is
configuration-dependent, per the next clause.

### 3. Enforcement — how much evidence, and whose

A verifier can require *how much* attributed evidence must exist (a count) or *whose* must exist
(named witnesses). Study 017 registers both over the same bytes, and they differ: a count is
satisfied by whatever survived delivery, while naming a witness converts that specific absence into
a refusal — one that reports absence of evidence and cannot say why. Every outcome in clause 2 is
bound to its enforcement configuration: the same omitted record passes under a satisfied count and
refuses under a named floor.

With no floor at all, an empty comparison is *vacuously consistent* — a pass having compared
nothing. Study 017 makes that a registered structured field precisely because a verdict string
cannot carry the difference.

### 4. Coverage — what a record constrains

A record names a head at a position. Because the head commits through predecessor hashes to the
whole prefix ending there, it constrains **that authenticated prefix** — and says nothing about
later positions. Study 017's cell establishes the second half: a divergence above the highest
recorded position remained invisible, exactly as a genesis pin does not prevent a fork placed after
it ([RFC 0011](0011-judgment-currency-anchor.md) Unresolved #8). A contract must specify what a
witness undertakes to observe and how often.

### 5. Retention — unmeasured, and named as such

Coverage says what a record constrains; retention asks how long a witness keeps what it saw, and
whether it can still produce it when a verifier asks. **No cell in either study measures this.**
Study 017 deliberately renamed an earlier "retention horizon" construction to *positional prefix
coverage* after its reviewer showed the construction demonstrated position, not retention, and its
§4c states that retention policy is out of reach of that apparatus. The clause is listed because
RFC 0011 #9 names it and because omitting it here would misrepresent the list as complete; what
would evidence it is Unresolved #2.

### 6. Recency — a configured policy, not a property

Should a witness's record of a *longer* history refuse a *shorter* presented one? Study 017
registers both answers over identical bytes: a deliberate audit of an older snapshot and a stale
presentation are the same input to that comparator, so refusing catches the second and breaks the
first. A contract should make this an explicit configured policy and say which deployments take
which, rather than promoting a witness record to prior-acceptance state implicitly — the same
discipline [RFC 0011](0011-judgment-currency-anchor.md) §2 applies to its own snapshot rollback
rule.

### 7. Non-collusion — where mechanism ends and governance begins

A witness that signs whatever each audience is shown satisfies every clause above. Study 017's
exhibit is a pair in which one trusted key records contradictory heads at the same position for two
audiences; each run is internally valid, satisfies its enforcement floor, and passes. That result
supports a bounded statement: **a single-key, single-view comparison of the kind measured
implements no non-collusion clause**, and its own sibling cell shows the conditional effect of one
additional trusted conflicting record reaching the comparator.

It does not support the stronger claim that non-collusion is beyond mechanism. Mechanisms exist
that change its shape — named multi-witness quorums, cross-signing between witnesses, and
collective cosigning schemes (Syta et al., CoSi, has a working prototype) raise the number of
parties that must cooperate, and can expose a statement to several witnesses at once. What they do
not do is establish that those parties' interests actually diverge; that assumption remains
external to every artifact a verifier holds. The honest division is: **quorum and accountability
can be mechanised; independence is a governance property**, and how much of the clause each side
carries is Unresolved #1.

## Alternatives

- **No witnessing; pin the exact version.** The null option, correct for a single relying party
  trusting a single publisher, already recorded in RFC 0011's Alternatives. It fails when
  verification must be open.
- **Caller-supplied prior-acceptance state.** Study 016 measured this and the measurement is
  narrower than "a verifier that remembers": its layer holds no storage and returns no state
  update, and `minimumHeadPin` is a caller-provisioned input. What it established is a *conditional*
  refusal — given a previously accepted head, a conflicting sibling is refused by prefix
  containment. The persistence lifecycle (atomic update on accept, durability) is explicitly
  unimplemented and unmeasured there, and no cost comparison between this and witnessing was
  measured by either study; no ordering is asserted here.
- **A transparency log with inclusion and consistency proofs.** Strictly stronger *within a view*:
  inclusion and prefix-consistency machinery is what a bare comparison lacks. Its cost is
  deployment-dependent rather than uniformly heavier —
  [RFC 0010](0010-gateway-signing-identity.md)'s ordering is stated against its own comparator (an
  external log versus gateway-signed checkpoints in a self-contained deployment) and does not
  transfer to every witness architecture. Note also that a log does not dissolve this record: a
  bare log has an operator and clients, and inclusion or consistency proofs do not by themselves
  expose a split view to an isolated client — cross-view observability still requires persisted
  state, gossip, monitoring, or witness cosigning, which is where these clauses reappear.

## Compatibility

A verifier that does not consult witnesses keeps exactly today's behaviour and today's blind spot.
For a verifier that does, [RFC 0011](0011-judgment-currency-anchor.md)'s Compatibility conclusion
applies as it was written: a versioned envelope in the consuming protocol is what makes a
witness-*unaware* verifier reject rather than silently skip the step. An *adopting* verifier has
another route — out-of-band configuration that requires witness input, exactly as Study 017's
count and named-witness floors do. Which of the two a given consumer should use, and whether
protocol-level signalling is needed at all, is open per consumer.

## Security and privacy

- **Observability, never prevention.** Nothing here stops a split view from being served, and no
  verdict from a single view establishes which history is true. Within the registered cells of the
  measured prototype, satisfying the clauses made one registered fork observable to a verifier that
  compared; no claim is made that a complete contract makes equivocation observable in general.
- **The trust root multiplies.** Witnessing adds a key set to the out-of-band problem rather than
  removing it: a verifier must be told which witnesses to trust — RFC 0011's Unresolved #1, once
  per witness — and clause 1's authenticated-signer question sits underneath that.
- **Disclosure.** A witness record reveals the head a witness key **attested to** (not, without
  further assumption, what any party observed), and records sharing a head correlate. If records
  travel with artifacts, that linkage reaches every audience those artifacts reach and outlives
  access control on the registry itself — the same surface
  [RFC 0011](0011-judgment-currency-anchor.md) Unresolved #11 records for cited heads.
- **Resource risk.** A verifier folds a witness set it did not author. Per-record and per-set size
  limits, a bound on verification work, and fail-closed behaviour above them are part of any format
  work, not an afterthought; Study 017 carries a registered limit control and its at-cap sibling.

## Conformance

Cases would follow the frozen-corpus style. Each must fix its enforcement configuration, because
outcomes are configuration-bound (clause 3), and each should record structured evidence rather than
a verdict string alone:

- **Positive** — a consistent record under a stated floor verifies.
- **Attribution** — a record whose self-declared identity disagrees with its signature must not
  change the outcome; a record verifying under no trusted key is counted, not a refusal.
- **Delivery, paired** — an omitted conflicting record *with* the count floor satisfied by another
  record (passes) and *with* the omitted witness named in a required set (refuses); the same pairing
  for a record corrupted so it verifies under no trusted key.
- **Enforcement** — a floor above the available evidence (refuses); a zero floor with an empty set
  (passes, with the structured field recording that nothing was compared).
- **Coverage** — a record naming only an earlier position while a divergence sits above it.
- **Recency** — identical bytes under both policies, with opposite registered outcomes.
- **Non-collusion** — one trusted key recording contradictory heads for two audiences: each side
  passes; and the same construction with one additional trusted conflicting record delivered.
- **Boundary and resource** — record size, set size, and verification work at each registered limit
  and one past it, each failing closed.

## Implementation

None exists, and the two plausible independent paths are named rather than gestured at:

1. A **witness record writer and offline comparison verifier in the reference runtime**, beside the
   currency-registry artifacts [RFC 0011](0011-judgment-currency-anchor.md) §3 places there,
   together with the vector corpus above. It would exercise clauses 1–4, 6 and the mechanised half
   of 7; retention (5) needs a deployed observer and is out of its reach.
2. A **consumer step in an independent receipt protocol** — OpenWorkProof is the named first
   candidate, since RFC 0011 already names it as the first currency consumer and Study 014's
   adapter already carries the identity tuple a comparison would key on. Built by that protocol's
   author, by its own process, it would exercise clauses 1–3 and 6 against an artifact set this
   project did not design.

The clean-room caveat applies and is load-bearing here: two implementations built by this project
evidence precision, not interoperability. Study 017 is neither of these paths — it is a measured
prototype inside a study harness that explicitly disclaims format-proposal and interoperability
status.

## Unresolved questions

1. **Who witnesses, and what would evidence their independence?** Clause 7 divides into a
   mechanised part (quorum size, cross-signing, cosigning — how many parties must cooperate) and a
   governance part (whether those parties' interests actually diverge). The second is not observable
   from any artifact a verifier holds. Whether it can be evidenced at all — by disclosure, by
   selecting parties with structurally opposed interests, by an economic stake — and how much of the
   clause the mechanised part can carry, is open.
2. **What would evidence retention, coverage and liveness?** Clause 5 has no measurement and clause
   4 measures only the position side. What a witness undertakes to observe, how long it must be able
   to produce it, and what publication, timestamping, monitoring or audit mechanism could make any
   of that checkable — rather than asserted — is open.
3. **Delivery responsibility.** Who is obliged to carry records to a verifier, and what may a
   verifier conclude from an empty set (clause 2)? Every answer this record can see leaves an
   absent record's causes indistinguishable; whether that is irreducible, or reachable with
   publication or acknowledgement mechanisms, is open.
4. **One primitive, or several?** [RFC 0011](0011-judgment-currency-anchor.md) Unresolved #9 asks
   whether one witnessing mechanism can serve both the gateway's checkpoint questions
   ([RFC 0010](0010-gateway-signing-identity.md) §4) and a currency registry's, given their
   different threat models. This record adds a third instance: whatever would anchor a *cited
   registry head* ([RFC 0011](0011-judgment-currency-anchor.md) Unresolved #11) faces these same
   clauses.
5. **Is the clause list complete?** Seven clauses are proposed; nothing establishes that they
   suffice. Ordering, freshness of the comparison itself, and the interaction between witnessing and
   the transition rules of [RFC 0011](0011-judgment-currency-anchor.md) §2a are candidates not
   worked here.

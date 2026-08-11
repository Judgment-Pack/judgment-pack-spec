# RFC 0012: What a witness contract would have to specify — the clauses a signed-history comparison depends on

- Status: Draft
- Type: Exploratory (research line — a cross-project artifact, outside JPS)
- Created: 2026-08-11

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **Scope note, load-bearing.** Nothing this RFC proposes lands in JPS Core, a profile, a
> conformance class, or any other RFC's specification-track surface. If any part is built, the
> **format and verifier** land in the [reference runtime](https://github.com/Judgment-Pack/judgment-pack-runtime)
> or a dedicated repository, and the **consumer step** lands in each protocol that opts in, by
> that protocol's own process. It proposes **no** change to the
> [reference gateway](https://github.com/Judgment-Pack/judgment-pack-gateway), whose scope forbids
> it holding a policy authority. It is recorded under [RFC 0000](0000-rfc-process.md)'s
> cross-project exploratory provision: a disposition here endorses (or declines) the design record
> as written and confers no authority over any owning repository. The
> [architecture vision's](../docs/architecture/vision.md) statement — that these downstream
> questions establish binding and lineage, never that a policy or a fact is true — remains true
> with this RFC merged.
>
> **This record narrows a question; it does not answer one.**
> [RFC 0011](0011-judgment-currency-anchor.md) Unresolved #9 says the transparency-log / witness /
> cross-signing direction is "conditional on a still-unspecified witness contract: retention,
> cross-view comparison, verifier enforcement, and witness independence and non-collusion."
> This record writes down what those clauses would each have to specify, and — for the first time
> in this line — what a minimal instantiation of them measurably does and does not do.

## Summary

A signed, append-only registry cannot be caught equivocating by a verifier that holds only one
view of it. The direction everyone reaches for is *witnessing*: some party records the history it
observed, a verifier compares. That direction is real, and it is also under-specified in a way
that matters — "a witness signed it" is not a property until the contract around the signature is
written down.

This record enumerates the clauses such a contract needs — **attribution, delivery, enforcement,
coverage, recency, and non-collusion** — and states, for each, what a minimal mechanism achieves
and what it provably cannot. It draws on two frozen studies that measured exactly this, one of
which was built for the purpose. It proposes no format. Its most useful content is the negative
part: five of the six clauses have a measured cell showing what remains invisible when the clause
is absent, and the sixth — non-collusion — has one showing that nothing in a comparison mechanism
enforces it at all.

## Problem

[RFC 0011](0011-judgment-currency-anchor.md) records a currency registry whose Alternatives
section names the cost of staying self-contained: "an isolated offline verifier cannot detect a
signer's split view." Unresolved #9 names witnessing as the direction that would buy that back,
and immediately qualifies it as conditional on a contract nobody has written.

The qualification is not hedging. A witness mechanism has a signature at its centre, and a
signature is the *easiest* part. What decides whether a comparison means anything is the
surrounding contract:

- **Attribution.** Which witness does a record belong to, and how is that decided?
- **Delivery.** Which records reach the verifier, and who controls that?
- **Enforcement.** How much evidence, and whose, must exist before a view is called witnessed?
- **Coverage.** What does a record about position *n* say about position *n+1*?
- **Recency.** Does a witness's longer history refuse a shorter presented one, and should it?
- **Non-collusion.** What if the witness and the operator are the same interest?

Each of these is a place where a mechanism can look like it works and not work. That is the
problem this record exists to make explicit before anything is built.

## Evidence

Two frozen studies in the interoperability line, both preregistered, cross-vendor reviewed, run
once from their freeze commits, with results published whichever way they fell.

- **[Study 016](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/016-policy-currency-anchor)**
  (currency anchor) established the gap this record addresses: a fork of a single-operator signed
  registry is **silent** to a fresh, stateless verifier holding only its out-of-band pins — each
  view verifies cleanly on its own, and the contradiction exists only across a pair no single
  offline run can see. It also bounded that finding immediately: the same presentation is refused
  the moment the verifier holds prior-acceptance state. What a fresh verifier lacks is exactly
  state.
- **[Study 017](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/017-witnessed-currency)**
  (witnessed currency) was built to measure the next step: a **sighting** — one witness key's
  signature over an observed history head — compared against a presented view, as one added layer
  over Study 016's frozen verifier. Its registered result is that one attributed record of a
  sibling head makes the otherwise-silent fork observable, and that each remaining silence
  isolates one contract clause.

**What this evidence is not.** Both studies are study-internal: the registry, the witness keys,
the comparison step and the verifier were written by one project, and Study 017 states plainly
that it is **not an interoperability study** and makes no claim about witness independence as an
organisational property. Its measurements bound a *mechanism*, not a deployment. They are cited
here as measurements of a prototype, never as evidence that witnessing works between real
parties — which remains the stronger evidence this line does not have.

## Specification (sketch) — the clauses, and what each is worth

No field names or canonical forms are fixed here; the owning repository would govern them, as
[RFC 0010](0010-gateway-signing-identity.md) defers to the gateway's `SPEC.md`. What follows is
the contract's *shape*.

### 1. Attribution — by verification, never by assertion

A record must be associated with a witness by **verifying its signature against a pinned key**,
never by a self-declared identifier the record carries. This is stated first because it is the
clause most easily got wrong: Study 017's draft routed records by an unauthenticated key-id label
and its cross-vendor reviewer showed that relabelling an *honest, conflicting* record with an
unpinned identifier caused it to be ignored — turning a detected conflict into a pass. The label
could not cause a false refusal, only a false acceptance, which is the direction that matters.

The corollary is a limit, not a fix: once attribution is by verification, a record that verifies
under no pinned key is *unattributable*, and a genuine record from an unpinned witness is
indistinguishable from a corrupted record from a pinned one.

### 2. Delivery — the clause a signature cannot reach

Whoever controls which records reach the verifier can **omit** the conflicting one, **corrupt**
it so it attributes to nobody, or **re-sign** its payload under a fresh key. All three yield a
pass. In Study 017 the corrupted case leaves a count of unattributable records and nothing else —
and a count is not a detection.

No signature scheme addresses this, because the adversary never forges anything. A contract must
therefore say who is responsible for delivery, what a verifier may assume when it sees nothing,
and — the honest part — that *silence and suppression are the same observation*.

### 3. Enforcement — a count floor and a named floor say different things

A verifier can require *how much* attributed evidence must exist (a count) or *whose* must exist
(named witnesses). These are not interchangeable. A count is satisfied by whatever survived
delivery, including only the records an adversary chose to pass through. Naming witnesses
converts a specific absence into a refusal — but refuses on **absence of evidence**, and cannot
distinguish suppression from outage, from a witness that never observed the series, or from one
that never existed. Study 017 registers both arms over the same bytes.

Without any enforcement floor, an empty comparison is *vacuously consistent*: the verifier
reports a pass having compared nothing. A contract must require that this be
machine-distinguishable from a pass after a real comparison — Study 017 makes it a registered
structured field precisely because a verdict string cannot carry it.

### 4. Coverage — a record constrains one position

A sighting names a head at a position. It says nothing about what follows. A fork placed above
the highest sighted position is invisible, exactly as a genesis pin does not prevent a fork
placed after it ([RFC 0011](0011-judgment-currency-anchor.md) Unresolved #8). A contract must
specify what a witness undertakes to observe and how often, because "witnessed" without a
coverage claim is a statement about one point in a history.

### 5. Recency — a configured policy, not a property

Should a witness's record of a *longer* history refuse a *shorter* presented one? Study 017
registers both answers over identical bytes and finds the choice cannot be made from the
artifacts: a deliberate audit of an older snapshot and a stale presentation are the same input.
Refusing catches the second and breaks the first; accepting does the reverse. A contract must
make this an explicit configured policy and say which deployments take which — and no verifier
should promote a witness's record to prior-acceptance state implicitly, which is the same
discipline RFC 0011 §2 applies to its own snapshot rollback rule.

### 6. Non-collusion — the clause no mechanism implements

A witness that signs whatever each audience is shown satisfies every clause above. Study 017's
load-bearing exhibit is a pair in which one pinned key records contradictory heads at the same
position for two audiences; each run is internally valid, satisfies its enforcement floor, and
passes. The contradiction exists only across the pair, and no verifier holding one side sees it.

Non-collusion is therefore not a mechanism property at all — it is a **governance** property of
who the witnesses are and what makes their interests diverge from the operator's. That is the
same shape as [RFC 0011](0011-judgment-currency-anchor.md) Unresolved #1's "who signs currency",
and it is why this record cannot end in a format.

## Alternatives

- **No witnessing; pin the exact version.** The null option, correct for a single relying party
  trusting a single publisher, and already recorded in RFC 0011's Alternatives. It fails when
  verification must be open.
- **Per-verifier persisted state only.** Study 016 measured this: a verifier that remembers the
  head it previously accepted refuses a conflicting sibling by prefix containment. Strictly
  cheaper than witnessing and genuinely effective — for *sequential* views seen by *one*
  verifier. It cannot help a verifier's first encounter, and it does not compare across parties.
- **A full transparency log with inclusion and consistency proofs.** Strictly stronger and
  strictly heavier — the same trade [RFC 0010](0010-gateway-signing-identity.md) records for
  checkpoints. Note that it does not escape this record: a log has witnesses, and every clause
  above reappears as a question about them.

## Compatibility

Nothing here is additive to an existing verifier: a verifier that does not consult witnesses
keeps exactly today's behaviour and today's blind spot. A verifier that does needs a versioned
envelope in its own protocol to fail closed on absence, which is a per-protocol change — the same
conclusion [RFC 0011](0011-judgment-currency-anchor.md)'s Compatibility section reaches for the
currency step, for the same reason.

## Security and privacy

- **Observability, never prevention.** Every clause above, fully satisfied, makes an equivocation
  *observable to someone who compares*. Nothing stops a split view from being served, and no
  verdict from a single view establishes which history is the true one.
- **The trust root multiplies.** Witnessing does not remove the out-of-band problem; it adds a
  key set to it. A verifier must now be told which witnesses to trust, which is RFC 0011's
  Unresolved #1 again, once per witness.
- **Disclosure.** A witness record reveals which view of a series an actor observed, and records
  sharing a head correlate. If sightings travel with artifacts, that linkage reaches every
  audience those artifacts reach and outlives access control on the registry itself — the same
  surface [RFC 0011](0011-judgment-currency-anchor.md) Unresolved #11 records for cited heads.
- **Resource risk.** A verifier folds a witness set it did not author; per-record and per-set
  limits with fail-closed behaviour above them are part of any format work, not an afterthought.

## Conformance

Cases would follow the frozen-corpus style, and Study 017's registered matrix is a reusable
starting shape: a positive comparison; a record whose self-declared identity disagrees with its
signature (must not change the outcome); an unattributable record (counted, never a refusal);
an omitted record (passes — registered, not repaired); a count floor satisfied while a named
witness is absent; a record naming only an earlier position while a fork sits above it; the same
bytes under both recency policies; and one witness recording contradictory heads for two
audiences (passes on each side).

## Implementation

None exists. Study 017 is a measured prototype of clauses 1–5 inside a study harness and is
explicitly not a format proposal; clause 6 has no implementation anywhere, because it does not
have one. The strongest evidence this line could acquire remains what
[RFC 0011](0011-judgment-currency-anchor.md)'s Implementation section already names: a consumer
step built by an independent protocol's author, by that protocol's own process.

## Unresolved questions

1. **Who witnesses, and what makes them independent?** The governance question clause 6 reduces
   to. Independence is not observable from any artifact a verifier holds; it is a property of who
   the parties are. Whether it can be evidenced at all — by disclosure, by cross-signing between
   parties with divergent interests, by an economic stake — is open, and is the question this
   whole record is really about.
2. **What does a witness undertake, and how is that undertaking audited?** Coverage and liveness
   are contract terms, not mechanism outputs (clause 4). A witness that observes rarely is not
   distinguishable from one that observes often, from the records alone.
3. **Delivery responsibility.** Who is obliged to carry records to a verifier, and what may a
   verifier conclude from an empty set (clause 2)? Every answer this record can see leaves
   suppression and silence indistinguishable; whether that is irreducible is open.
4. **Is there one primitive, or several?** [RFC 0011](0011-judgment-currency-anchor.md)
   Unresolved #9 already asks whether one witnessing mechanism can serve both the gateway's
   checkpoint questions ([RFC 0010](0010-gateway-signing-identity.md) §4) and a currency
   registry's, given their different threat models. This record does not settle it and adds a
   third instance: whatever anchors a *cited registry head*
   ([RFC 0011](0011-judgment-currency-anchor.md) Unresolved #11) faces the same clauses.
5. **Where would this live?** Per RFC 0000's cross-project provision the format and verifier
   land outside JPS — the runtime, or a dedicated repository — and the consumer step lands per
   protocol. Which, and who would operate a witness set, is undecided and is not proposed here.

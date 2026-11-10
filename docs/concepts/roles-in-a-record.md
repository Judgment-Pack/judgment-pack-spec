# Roles in a record

<div class="notice notice-info"><strong>Informative.</strong> This page names four roles that the
project's documents use around a decision record, and says what each one does and does not do. It
defines nothing. The specification, its companion documents, the RFCs and each implementation's own
specification do, and every claim below links to the one that states it. Where this page and those
texts disagree, they win.</div>

A decision record is surrounded by four kinds of party: the **judge** that computed it, a
**signer** that saw what went into it or came out of it, a **witness** that kept what it saw of its
history, and a **reader** that checks all of it later. Each role is defined as much by what it
must not do as by what it does. A sentence such as "the verifier signs" or "the gateway witnesses
its own receipts" breaks one of the "never" lines below, so it is wrong.

## The judge

**Who.** An evaluator: in this project, the reference runtime. Its conformance class is
[Core §3.4](../../spec/judgment-pack-core.md#34-evaluator-conformance).

**Produces.** The portable disposition, the one result Core defines
([§8.3](../../spec/judgment-pack-core.md#83-the-portable-disposition)). Where a project keeps one, it
also produces a decision trail of chained records and their checkpoints
([runtime ADR-0047](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/v0.30.0/docs/adr/0047-make-a-decision-record-defensible.md)).

**Trusts.** The pack, the facts document and the evidence-availability document it was given
([§8.2](../../spec/judgment-pack-core.md#82-evaluation-inputs)). It does not check that the facts are
true, and Core defines no way to acquire them.

**Never.**
- It never states that a disposition is true, authorized or safe
  ([§1](../../spec/judgment-pack-core.md#1-purpose),
  [§3.5](../../spec/judgment-pack-core.md#35-non-claims)). A disposition is data, not an action
  ([vision](../architecture/vision.md#whether-other-systems-respect-a-judgment-is-measured-not-assumed)).
- It never attests to anything outside its own evaluation. Its trail is its operator's own
  account, and the trail's chain and signature establish nothing against that operator
  (ADR-0047, §2 and §2b).

## The signer

**Who.** An observer that issues signed receipts for what it saw, under a key that a verifier pins
out of band. The shipped instance is the reference gateway's version 3 receipt
([RFC 0014](../../rfcs/0014-lineage-record-and-action-binding.md); gateway
[`SPEC.md`](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/v0.24.0/SPEC.md) §1.2a).

**Produces.** Receipts and session seals. An acquisition receipt attests the bytes a source
returned. An action receipt records an authenticated write request made through the gateway and the
target's response ([RFC 0015](../../rfcs/0015-reported-receipts.md), Summary).

**Trusts.** Its own signing key, and the identity check at its boundary for who asked
([gateway §5](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/v0.24.0/SPEC.md#5-trust-boundary-and-honest-bounds)).

**Never.**
- It never gives a verdict. An action receipt "is lineage of a request and a response, never a
  statement that the action was right" (gateway §5).
- It never claims that a named source produced the bytes. A signature proves byte-lineage under a
  label, not truth (gateway §5;
  [vision](../architecture/vision.md#where-those-inputs-come-from-is-a-separate-open-question)).
- It does not sign for a call it did not make. For both receipt kinds, the gateway started the
  program that reached the outside world. A receipt for a call it was only told about, a *reported
  receipt*, is a Draft question and is not shipped (RFC 0015).
- It is never the witness of the receipts it signs. A witness is a party other than the operator
  of the history it witnesses
  ([gateway §8](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/v0.24.0/SPEC.md#8-the-checkpoint-witness)).

## The witness

**Who.** A party other than the operator of a history, which signs what it saw of that history.
A copy presented later, shorter or different, can then be compared with what it signed
([the checkpoint witness statement, §1](../../spec/checkpoint-witness.md#1-terms-and-the-canonical-form);
[RFC 0012](../../rfcs/0012-witness-contract.md), Summary).

**What is shipped, and what is not.**
- **Shipped: the checkpoint witness.** It witnesses a runtime trail's checkpoints, and its format
  is a companion document beside Core ([RFC 0017](../../rfcs/0017-checkpoint-witness-statement.md)).
  Its vectors are staged, so no reader conformance claim is available yet. A gateway run by a party
  other than the trail's operator can serve as one (gateway §8). The gateway is then the witness of
  someone else's trail, never of its own receipts.
- **Not shipped: a witness contract for comparing a signer's signed history.** RFC 0012 lists the
  clauses such a contract would need. Until that contract is written, "a witness signed it" is not
  a property.

**Produces.** Witness statements: a checkpoint it was given, a conflicting checkpoint it refused,
or the retirement of a trail.

**Trusts.** Only the submitters it allows for a trail, and nothing about what they submit. A
statement shows that the witness was given a checkpoint and signed it. It does not show that the
checkpoint names a real record, or that the submitter was the trail's operator
([§10](../../spec/checkpoint-witness.md#10-what-a-statement-establishes-and-what-it-does-not)).

**Never.**
- A witness is never a witness against an operator who can use its key. Independence depends on
  who holds the key, and no statement can show it.
- One witness never protects against collusion.
- Its `witnessedAt` never says when a record was made. These three points are all in §10.
- It is a new trust dependency. A verifier decides which witness keys it trusts "as it decides
  which time-stamping roots it trusts" (§10).

**A time-stamping authority is a witness of time only.** Behind `jpack audit stamp`, an RFC 3161
authority stamps a checkpoint's digest. The token shows that the checkpoint existed by the stamp's
time. It does not show when a record was made (ADR-0047 §2a; the runtime's
[README](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/v0.30.0/README.md), "Stamping
checkpoints").

## The reader

**Who.** Anything that checks receipts, chains, records, statements and recordings against keys and
pins it holds itself, and reports findings in the specification's terms. The current readers are
these:
- the runtime's `jpack audit verify` (ADR-0047);
- the gateway's Go and TypeScript verifiers;
- this repository's Python and TypeScript readers.

The issue that proposes a portable verifier,
[spec #255](https://github.com/Judgment-Pack/judgment-pack-spec/issues/255), lists these. Two
companion documents define reader classes: the
[witness-statement reader](../../spec/checkpoint-witness.md#11-the-witness-statement-reader) and the
[preparation verifier](../../spec/dialect.md).

**Trusts.** What it obtained independently of the evidence it checks: the public keys, the trail
identities, and at least one checkpoint, which it obtained itself or from a witness it trusts
(ADR-0047, "What a verifier must hold independently of the operator"). A key fetched from the party
under audit proves consistency, not authenticity (gateway §5).

**Never.**
- It never signs. Verification needs only public keys, so a reader holds nothing that could produce
  a receipt (gateway §5).
- It never attests. For witness statements, a reading and a report built on it must not be
  described as establishing anything §10 says they do not.
- It never computes a verdict. Spec #255 says this of the portable verifier: "the runtime stays
  the only judge".

**Not shipped: the portable verifier.** Spec #255 proposes a portable verifier library: an
independent reader for WebAssembly and native targets. It is deferred until a consumer needs
verification outside Go and TypeScript.

## Who may say what

| Role | Says | Never says | Shipped |
| --- | --- | --- | --- |
| Judge | "This pack, over these inputs, resolves to this disposition." | That the inputs are true, or that acting on the disposition is authorized or safe. | Yes: the reference runtime. |
| Signer | "A source returned these bytes." "This request got this response." | That the source is who its label names, or that the action was right. | Yes: the gateway's version 3 receipts. |
| Witness | "I was given this checkpoint of a trail I do not operate, and I signed it." | That the record is real, that the witness is independent, or when the record was made. | The checkpoint witness: yes. RFC 0012's signed-history contract: no. |
| Time-stamping authority | "This checkpoint existed by this time." | When the record was made. | Yes: `jpack audit stamp`. |
| Reader | "These bytes verify under that pinned key, and these are the findings." | A verdict, or anything under a signature of its own. | Yes: the readers above. The portable verifier (spec #255): no. |

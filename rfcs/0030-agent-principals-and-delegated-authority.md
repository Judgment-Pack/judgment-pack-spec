# RFC 0030: Agent principals and delegated authority

- Status: Draft
- Type: Mixed. The delegation statement (its members, canonical form, signing, narrowing check and verification steps) is **standards track at draft maturity**, proposed for a companion document beside Core. Everything else — the agent's run admission and records, the gateway's credentials, receipt member, action keys and connection grants, and the Desk's inventories — is an **exploratory cross-project record** outside JPS.
- Created: 2026-10-30
- Amended: 2026-11-09 (the confirmation review's five LOW findings, issue
  [#284](https://github.com/Judgment-Pack/judgment-pack-spec/issues/284): the actor row's source
  and tool, the owner in the admission read and its refusals' order, a grant with no owner,
  pending actions behind a removed owner, and the subject's standing read; then the narrow
  review's six LOW findings, issue
  [#291](https://github.com/Judgment-Pack/judgment-pack-spec/issues/291): the read-back's own
  source and tool on the actor row, the owner read's cost, and the vectors they need);
  2026-11-22 (ES256 delegation statements, a chain bound to one scope identifier, and the
  admission reads on the wire, version 2 and a skill-load read among them, in the standards-track
  part; a first dispatch outside the read-back's scope, issue
  [#293](https://github.com/Judgment-Pack/judgment-pack-spec/issues/293); and the acceptance plan;
  see [Amendment of 2026-11-22](#amendment-of-2026-11-22)); still Draft
- Target: first proposed for Spec `0.5.0` and carried as a Draft in release `v0.4.0`. The amendment
  of 2026-11-22 is proposed for release `v0.6.1`, which carries `specVersion` `0.6.0` unchanged
  (*Release*, under [Acceptance plan](#acceptance-plan)). The Draft is normative for
  nothing and pre-commits nothing for any `specVersion`.
- Issues: [#280](https://github.com/Judgment-Pack/judgment-pack-spec/issues/280) (the record),
  [#293](https://github.com/Judgment-Pack/judgment-pack-spec/issues/293) (the first-dispatch answer)

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **Scope note, load-bearing.** This record has two parts, and RFC 0000 treats them differently.
>
> *The standards-track part* is the delegation statement of §§2–3: its members, its canonical form
> and signing, the narrowing check and the verification steps. Independent parties must agree on
> it byte for byte, so it is proposed for a companion document beside Core. Since the amendment of
> 2026-11-22 it also holds the admission reads of §2a, whose bodies and answers an enforcing host
> and an issuing host must agree on in the same way. It owes RFC 0000's standards-track bar,
> including two independent implementations and conformance cases. The amendment of 2026-11-22
> sets out how that bar is to be met and recorded: the gateway and the agent library each build
> the standards-track part from this text alone and pass every conformance case it lists, and the
> acceptance record states that evidence as it is, two separately written implementations, same
> vendor, not a cross-vendor claim ([Acceptance plan](#acceptance-plan)). Until that record is
> made, the record is a Draft. It changes nothing in Core.
>
> *The exploratory part* is everything else, and every piece of it lands in another repository of
> the project, under RFC 0000's cross-project exploratory provision:
> - the receipt member, the action-key scope and the connection grant land in the
>   [reference gateway's](https://github.com/Judgment-Pack/judgment-pack-gateway) `SPEC.md`
>   (§1.2a, §1.2b, §1.4), design notes and posture;
> - the run's carried principal, its admission refusals, its record members and the lease's
>   principal binding land in the
>   [agent harness's](https://github.com/Judgment-Pack/judgment-pack-agent) contract and decision
>   records;
> - the inventories and the revoke actions land in the
>   [Desk](https://github.com/Judgment-Pack/judgment-pack-desk).
>
> A disposition here confers no authority over those repositories; each decides its own adoption.
> The implementation rows that build against this Draft are agent #260, gateway #356 and #357, and
> desk #679. Where they build against it, they build against a Draft, and the text may change.

## Amendment of 2026-11-22

This amendment changes the standards-track part in four places and the exploratory part in one,
and plans how the record meets RFC 0000's bar. Nothing else changes.

1. **ES256 delegation statements** (§2, *Signing with a P-256 key*; steps 3 to 5). An issuing host
   may sign with a P-256 key. Such a statement holds `alg: "ES256"` inside the signed bytes, and an
   Ed25519 statement is byte for byte what it was. The rule is per link, so a chain may mix the two.
2. **A chain bound to one scope identifier** (§2, *Binding a chain to one scope identifier*; §3,
   clause 9). `scope.scopeId` is the same on every link, and a request under a bound chain names
   that scope identifier or is refused `scope-id-mismatch`.
3. **The admission reads on the wire** (§2a). Version `"1"` is stated as both implementations send
   it. In version `"2"`, a call read adds `version`, the tool's descriptor digest, and `skills`,
   the skills loaded at the call, and a skill-load read is asked before a skill loads. Version
   `"1"` stays readable, a sender's version is configured and never negotiated, and an unknown
   version is refused by name.
4. **Step 12** gains `tool-version-refused` and `skill-refused`, on a version `"2"` read only.
5. **§4, rule 4** (exploratory part). The first dispatch that leaves its key uncertain under a link
   that excludes the read-back's source or tool is answered with its uncertain record, not refused
   (#293).
6. **[Acceptance plan](#acceptance-plan)**: the two implementations and what they are, the
   conformance cases both must pass, the build order (ES256 first), and the release, `v0.6.1`.

The ES256 text and the scope binding of §2 each stand alone. Neither needs §2a or the other, and
they are built and verified first, ES256 before the binding.

## Summary

An agent that reaches a system with a person's own credentials is indistinguishable from that
person. It has no identity of its own, and nothing records on whose behalf it acted or within what
limits. Its access is the person's whole access, and it cannot be stopped without stopping the
person. This record proposes the missing model in seven parts:

1. an **agent principal**: a registered, non-human principal with a stable identifier, the host
   that registered it and its software identity; an unregistered agent cannot act;
2. a **delegation**: a signed, bounded statement that a subject (a person or a service) authorizes
   an actor (an agent principal) for a scope until an expiry, with the subject and actor semantics
   of OAuth 2.0 Token Exchange (RFC 8693), exercised only through a short-lived,
   sender-constrained credential bound to it;
3. **chained delegation**: each link narrows scope and expiry and never widens them, by an exact
   check, and only the parent's actor or the subject can ask for a child; the chain is recorded;
4. **revocation**, which stops new dispatch at once and leaves the subject's own access untouched;
   effects already dispatched follow the existing uncertain-action rules;
5. the **connection grant** behind each gateway connection, treated as a principal-held resource.
   It has an owner, least-privilege scopes, a record of granted against used scopes, an owner and
   idle lifecycle, and publisher trust for customer MCP servers. Revocation or quarantine on the
   owner's removal is proposed as normative;
6. **recording**: receipts and run records name the actor, the subject and the delegation. A
   receipt reader that predates this record reads the same `caller` pair and returns the same
   status, by an exact rule that also states what that reader is misled about;
7. its **relation to existing contracts**:
   - the per-call identity of agent #102 becomes the subject where it names a person, and names
     the credential's holder otherwise;
   - run leases bound time and delegations bound authority;
   - action keys are scoped to the subject and the root actor, so that a lease takeover of a
     delegated run cannot reopen them.

It closes with open questions, each with a proposed default, and the conformance vectors a
normative version would need.

## Problem

The project already attributes calls, and already bounds what a run may do:

- the agent's source record declares, per source, whether a call runs as the person, a service or
  the connection (agent #102,
  [ADR-0019](https://github.com/Judgment-Pack/judgment-pack-agent/blob/main/docs/adr/0019-identity-per-tool-call.md));
- the gateway's version 3 receipt records `caller`, the issuer and subject of the token the gateway
  verified, and an action receipt records its `requester` in the same form (gateway `SPEC.md`
  §1.2a);
- approvals, effect classes
  ([ADR-0027](https://github.com/Judgment-Pack/judgment-pack-agent/blob/main/docs/adr/0027-tool-taxonomy.md))
  and run leases
  ([ADR-0025](https://github.com/Judgment-Pack/judgment-pack-agent/blob/main/docs/adr/0025-unattended-runs.md))
  bound what a run may do and when.

None of these says **who the agent is, who delegated to it, and what it was allowed to do**.
ADR-0019 says so itself: its identity is reported and counted, and beyond its first-service-action
safeguard "the label grants nothing". It labels whose credential a call runs under. A gateway
`caller` proves who asked at the gateway's boundary, and when an agent presents a person's token,
the caller is the person. So today:

- an audit cannot tell an agent's call from the person's own;
- an agent's reach is whatever its credential reaches, not a narrowed share of it;
- a child agent receives its parent's whole reach, and nothing records that it was a child;
- stopping an agent means revoking the person's credential, which stops the person as well;
- the standing grant behind a connection outlives its use and its owner, and nobody is recorded as
  answerable for it.

There is also a concrete defect this model bears on. The gateway scopes an action key to the
authenticated issuer and subject (§1.2b). ADR-0025's idempotency identity carries no principal, so
that a takeover by a new lease owner never replays an effect. When a takeover authenticates as a
different transport subject, the gateway sees a new key scope and sends the write again
(gateway #352, finding M6).

## Evidence

What exists, and what it shows:

1. **The per-call identity, built.** ADR-0019 (agent v0.8.0) puts `identity: {kind, label}` on the
   source record, with `kind` one of `person`, `service` or `connection`, and `connection` the
   default where the host declares nothing. It carries the identity on every `tool_call` and
   `tool_result`, counts calls per identity, and withholds a source whose identity changes mid-run.
   It always asks before the first `act` under a `service` identity, and the model never chooses
   an identity. What it lacks is a principal for the agent: the identity names the credential, not
   the party using it.
2. **The caller identity, built.** Gateway receipt version 3 records `caller` as
   `{issuer, subject, tokenDigest}` from a verified token, or `null` where no issuer is configured.
   An action records its `requester` in the same form, never `null`. Both are signed with every
   other member. A version 3 verifier tolerates a signed member it does not know. `witness`,
   `tool.transport` and `decision.recordBytes` were each added that way, and the specification says
   of each that a verifier written before it "tolerates it, as it tolerates any signed member it
   does not know" (§1.2a). The compatibility rule below follows that precedent.
3. **Leases and the fence, built.** ADR-0025 decision 1, as amended for agent #223, defines the
   lease (`owner`, `expiry`, `epoch`, `state`), the fence `{resource, owner, epoch}` presented at
   every commit and admission, and an idempotency identity `{run, operation, source, tool,
   requestDigest}` with no epoch. It states that "a lease grants neither tool permission nor
   approval", and that the fence adds no member to any checkpoint or event format. Time is bounded;
   authority is not, and the fence names no principal.
4. **Action keys and uncertain delivery, specified.** Gateway §1.2b defines `action.delivery`
   (`response` or `uncertain`), and reconciliation by a declared read-back that reports `committed`
   or `unknown`. Neither outcome permits another dispatch of the mutation. The action key is scoped
   to "gateway authority, authenticated issuer and subject".
5. **The takeover defect, observed.** The different-vendor review of gateway #351 recorded a probe
   (P4c) in which a takeover authenticating as a different subject produced two mutations of one
   operation. Gateway #352 offers two options: a run-level owner that survives takeover, or a
   takeover that presents the original subject's delegation. It is to be decided with its named
   consumer, agent #229 (run-owned jobs). For delegated runs, this record proposes the second
   option, refined. Undelegated takeovers still need #352's own fix.
6. **Effect classes, built.** ADR-0027 fixes the effects `pure`, `read`, `read-external`, `propose`
   and `act`, in that strength order. A tool's owner declares them; the model never does. So a
   scope can name effect classes by a closed vocabulary that already exists.
7. **Signing conventions, specified.** Gateway `SPEC.md` fixes a canonical form (§1.1), a key
   identifier (§1.2), domain-separated Ed25519 signing (§1.2, §1.2a), and an exact key rule and
   verification equation (§8.4). The statement reuses them rather than adding a second
   convention.
8. **Nothing of this model is built.** Agent #260, gateway #356 and #357, and desk #679 are filed
   against this Draft and open.

## Specification (sketch)

This is a Draft. The text is precise so that an implementation can build against it, but it is
normative for nothing. Where it says "must" or "refuses", read "is proposed to".

### Common forms

- **Canonical form.** Every signed or digested object in this record is serialized by `canon`, the
  canonical form of gateway `SPEC.md` §1.1: integers only, duplicate member names refused, member
  names ordered by Unicode code point, compact, raw UTF-8. It is not RFC 8785, whose name order
  differs outside the Basic Multilingual Plane. An implementation that reaches for an RFC 8785
  package gets that case wrong.
- **Signature.** An Ed25519 signature (RFC 8032), or, on a delegation statement that holds `alg`
  (§2, *Signing with a P-256 key*), an ES256 signature. Either is 64 bytes, written as exactly 128
  lowercase hexadecimal characters. It is made over a context prefix followed by `canon` of the
  object, with the object's top-level `signature` member removed and every other member retained,
  as gateway §1.2a signs a receipt. Ed25519 keys and signatures are held to gateway §8.4 by
  reference:
  - a pinned key is refused when it is not canonical, of small order, or not on the curve;
  - a signature verifies by the cofactorless equation with `S` below the group order;
  - the cofactored check is not used.

  ES256 keys and signatures are held to gateway §1.5 by reference, as §2 restates. Since a
  statement's digest covers its signature, two implementations that disagree on an edge signature
  also disagree on every chain digest that includes it.
- **Key identifier.** `keyId` is derived as gateway §1.2 derives one for an Ed25519 key: the first
  32 characters of the lowercase hexadecimal SHA-256 of the 32-byte public key. For a P-256 key it
  is derived as gateway §1.5 derives one: the first 32 characters of the lowercase hexadecimal
  SHA-256 of the key's 33-byte compressed point.
- **Digest.** `"sha256:"` followed by exactly 64 lowercase hexadecimal characters, as gateway §1.2a.
- **Time.** An RFC 3339 UTC timestamp with exactly millisecond precision,
  `YYYY-MM-DDTHH:MM:SS.sssZ`, the form ADR-0025's lease amendment fixes for a lease expiry. Two
  times *of this form* compare by their characters. A time of another form, such as a receipt's
  `servedAt` (§6), is never compared by characters with one of this form: both are parsed and the
  instants compared. An instant equal to an expiry is expired, as for a lease.
- **Identifier.** An **opaque identifier** is exactly 32 lowercase hexadecimal characters drawn from
  at least 128 random bits. A **flat token** is `[A-Za-z0-9._-]{1,128}`, never `.` or `..`, as
  gateway §3a.
- **Principal reference.** A person or service is named by
  `{"kind": "person" | "service", "issuer": string, "subject": string}`. `issuer` and `subject` are
  those of the identity the host verified for it, the same pair gateway §1.2a records in `caller`.
  Two references are equal only when all three members are equal. A reference carries no token,
  no token digest and no display label.
- **Issuing host and enforcing host.** The *issuing host* registers agents, issues delegations,
  and holds the authoritative state that admission reads (§2, *Authoritative state*). In the
  reference stack that is the Desk. An *enforcing host* admits and dispatches a call: the gateway
  for a gateway source, or the agent harness for a host source. An enforcing host that is also the
  issuing host reads its own state.

### 1. The agent principal

An agent principal is a principal distinct from every person and every service. The issuing host
registers it in its **agent inventory** before it can act. An inventory entry has these members:

| Member | Form | Meaning |
| --- | --- | --- |
| `agent` | opaque identifier | the stable identifier; assigned by the host at registration and never reused by that host, even after the entry is revoked |
| `host` | flat token | the registering host, as named in the trust configuration of every party that verifies its statements |
| `software` | `{"package": string, "version": string}` or `{"harness": digest}`, exactly one form | the agent's software identity: the package name and exact version it runs, or the digest of the harness it runs where no package identity applies |
| `label` | string | a name a person recognizes; never a credential (ADR-0019's credential-pattern rule applies) |
| `registeredBy` | principal reference | the person or service that registered it |
| `registeredAt` | time | |
| `state` | `"active"` or `"revoked"` | `revoked` is terminal |

Rules:

1. An agent principal has no credential of its own to any source. It acts only under a delegation
   (§2), and only through a credential bound to that delegation (§2, *The credential*).
2. A call under a chain any of whose actors is not an `active` entry of the issuing host's
   inventory is refused as `agent-unregistered`. A host that keeps no inventory admits no agent
   call.
3. **The software identity is host-attested, not proved.** The issuing host starts, or admits, the
   run, and it states the run's software when it obtains the credential. The enforcing host binds
   that statement to the credential (§2, *The credential*). The *presenting software* in step 9
   (verification) is that bound value, and nothing the caller asserts at call time. Because the
   value is the host's attestation, the binding holds the host to its own record. It does not
   prove which bytes ran (open question 5).
4. The inventory entry's `software` is current. A link whose `act.software` differs from its
   actor's current entry admits nothing (`software-mismatch`), so an upgrade needs new delegations.
5. Revoking an entry (`state` → `revoked`) revokes every delegation in which it is an actor (§4).
6. Registrations, changes to an entry and revocations are recorded, each with the principal that
   made it and the time (open question 19).
7. The `label` is shown, never trusted, as ADR-0019's label is.

### 2. The delegation

A delegation is a signed, bounded statement: subject P authorizes actor A, for scope S, until
expiry E. Its semantics are those of OAuth 2.0 Token Exchange (RFC 8693): the subject (`sub`) is the
principal on whose behalf the call is made, and the actor (`act`) is the party making it. It is RFC
8693's *delegation* case, never its *impersonation* case: an agent's call is never presented to a
reader of this model as the subject's alone. The statement is the host's record of the
authorization that RFC 8693 expresses with its `may_act` claim. A credential bound to it may be an
RFC 8693 issued token, and this record does not require one.

**The statement is not a credential.** Holding its bytes grants nothing. An enforcing host never
admits a call on statement bytes a caller supplies. It resolves the chain from the credential it
bound (step 0), and it binds a credential only at the issuing host's authenticated request.

**Members** (delegation version 1). Every member is required, except `alg`, which a statement holds
exactly when a P-256 key signs it; a nullable member is present as `null`, never absent.

| Member | Form | Meaning |
| --- | --- | --- |
| `delegationVersion` | the **string** `"1"` | |
| `id` | opaque identifier | assigned by the issuing host; never reused |
| `host` | flat token | the issuing host |
| `keyId` | key identifier | the issuing host's signing key |
| `alg` | the string `"ES256"`; **absent** on a statement an Ed25519 key signs | the signature algorithm, inside the signing input and the digest (*Signing with a P-256 key*, below) |
| `sub` | principal reference | the subject |
| `act` | `{"agent": opaque identifier, "software": as in §1}` | the actor and its bound software identity |
| `scope` | object, below | what the actor may do, and, where it holds `scopeId`, the one scope identifier the chain is bound to |
| `mayDelegate` | `true` or `false` | whether a child link may be issued below this one (§3) |
| `issuedAt` | time | |
| `expiresAt` | time | strictly later than `issuedAt` |
| `parent` | `null`, or `{"id": opaque identifier, "digest": digest}` | `null` for a root; otherwise the link this one is narrowed from |
| `depth` | integer | `0` for a root; the parent's `depth` plus one otherwise |
| `signature` | signature | |

**Scope.** `scope` is `{"sources": [entry, ...]}`, at least one entry, and on a chain bound to one
scope identifier also `"scopeId"` (*Binding a chain to one scope identifier*, below). Entries are
ordered by `audience.kind`, then `audience.name`, then `source`, each by code point, and no pair of
`audience` and `source` repeats. An entry is:

| Member | Form | Meaning |
| --- | --- | --- |
| `audience` | `{"kind": "gateway", "name": string}` or `{"kind": "agent-host", "name": flat token}` | the enforcing host that admits calls under this entry (below) |
| `source` | string | the source as that enforcing host names it: the gateway's `source` (for example `<platform>/live` or `<platform>/write`), or the agent's source record identifier for a host source |
| `tools` | array of strings, at least one, ordered by code point, no repeats | the exact tool names admitted; no pattern, prefix or wildcard (open question 4) |
| `effects` | array, at least one, of `"pure"`, `"read"`, `"read-external"`, `"propose"`, `"act"`, in that order, no repeats | the effect classes admitted, in ADR-0027's vocabulary |
| `limits` | object of limit name to non-negative integer; may be empty | resource limits, where the source has them |

**Audience.** An audience names one enforcing host, in one of two forms.
- **A gateway.** `{"kind": "gateway", "name": …}`, where `name` is exactly the string that
  gateway's receipts carry in `authority` (gateway `SPEC.md` §1.2, an operator-configured label
  such as `gateway:acme-finance`). The form is 1 to 256 characters from U+0021 to U+007E, so a
  label with `:` is admitted.
- **An agent host.** `{"kind": "agent-host", "name": …}`, where `name` is a flat token. It is the
  name the host declares in its harness configuration for the host sources it serves, and it is
  carried on each host source's ADR-0006 source record. When the issuing host runs the harness
  itself, the name is its own `host`.

An enforcing host admits only under an entry whose `audience` is its own. A staging gateway and a
production gateway that serve the same `source` name are therefore distinct entries. The agent
harness checks a gateway source against the entry for that gateway's audience and the gateway's
`source` name. The host declares that mapping on the ADR-0006 source record. A gateway source
record with no mapping cannot be checked, and its calls are refused (`out-of-scope`, reason
`source`).

**Limits.** Every limit is an **upper bound**: the quantity it names must not exceed it. A limit
name is one of two kinds:
- `calls`: the number of calls dispatched under the link for that entry;
- a name the source itself declares: `x-` followed by a flat token.

A source may declare a limit only when two things hold: the limit is an upper bound, and the source
can enforce it **before dispatch**, such as a row bound passed to a query or a size bound passed to
a request. A limit checked only after the result arrives is not a scope limit.

**Counting `calls`.** The counter for each (link, entry) pair is held by the issuing host and is
the only authoritative one. The admission read (below) checks it and increments it in one atomic
operation, so concurrent admissions cannot together exceed the limit.
- **When it counts.** Counting happens at dispatch, after the action-key lookup. The gateway first
  looks up the request's action key (§4, rule 4; §7, rule 3). A request that the lookup answers
  from retained evidence, sends to a read-back, or refuses dispatches nothing, and makes no
  counting admission read. Only a request that will physically dispatch — a first attempt, or a
  freed attempt — makes an admission read with counting set. Of the admissions made for one call,
  only the final one immediately before dispatch counts. A check before an approval pause, a park
  or a wake is made with counting unset.
- **A lost answer.** If the issuing host counted but its `admit` answer is lost, the budget is
  consumed and the call is not dispatched. This fails closed.
- **Who counts.** When the agent harness and a gateway both verify the same call, only the
  enforcing host that dispatches it, the gateway, counts it. The harness checks without counting.
  For a host source, the harness is the enforcing host and counts.
- **What counts.** A dispatched call, including a freed attempt (gateway §1.2b), counts once per
  dispatch. An answer from retained evidence counts nothing, and neither does a reconciliation
  read-back.
- **Across a chain.** A dispatched call counts against **every** link of its chain, so a child's
  calls count against its ancestors' limits.
- **On re-issue.** A re-issued root starts from the budget its new grant states (open question 3).

**Within the scope.** A call is within the scope of a link exactly when an entry has the enforcing
host's `audience` and the call's `source`, and four conditions hold:
- the call's tool is in the entry's `tools`;
- the tool's declared effect is in its `effects`. The effect is the owner's ADR-0027 declaration
  as admitted, never a model argument or a label;
- every limit name is known to the enforcing host;
- every limit holds: for `calls`, the count after this dispatch does not exceed it, and for a
  source-declared limit, the request is bounded within it before dispatch, as the source declares.

**Canonical form and signing.** The statement is serialized by `canon`. Its signature is Ed25519
under the issuing host's key, or ES256 under a P-256 key of that host where the statement holds
`alg` (below). It is made over the prefix `"judgment-pack/delegation/1:"` followed by
`canon` of the statement, with the top-level `signature` removed and every other member retained.
- Appending a member anywhere invalidates the signature.
- The prefix carries the version. It domain-separates a delegation from a receipt, a seal, a
  witness statement and a continuity statement, none of whose prefixes it shares.
- The statement's **digest** is `"sha256:"` + hex of SHA-256 over `canon` of the whole statement,
  `signature` included. A child, a receipt and a run record name the statement by its digest.
- The statement is at most 65536 bytes in `canon`, with at most 256 entries, at most 256 tools
  per entry and at most 16 limits per entry (open question 21).

**Signing with a P-256 key** (amendment of 2026-11-22). An issuing host may sign a statement with
an ECDSA P-256 key, by the algorithm the reference gateway states once for its own records (gateway
`SPEC.md` §1.5, as built in gateway v0.38.0;
[ADR-0053](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/12b0f43de0aa4b9e43e3fadca3cb9697e50f1087/docs/adr/0053-an-ecdsa-p256-signer-at-a-key-services-hsm-protection-level.md)).
The rules below restate it for a delegation statement completely: an implementation builds from
this subsection, the common forms and steps 1 to 7, and needs nothing of §2a.

- **The algorithm.** `ES256` is ECDSA over the curve P-256 with SHA-256 (FIPS 186-5; SEC 2's
  secp256r1), whose cofactor is 1:
  - `p` = `ffffffff00000001000000000000000000000000ffffffffffffffffffffffff`
    (2²⁵⁶ − 2²²⁴ + 2¹⁹² + 2⁹⁶ − 1);
  - the curve y² = x³ − 3x + b over it, with `b` =
    `5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b`;
  - `n`, the order of the base point, =
    `ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551`, so that (n − 1)/2 =
    `7fffffff800000007fffffffffffffffde737d56d38bcf4279dce5617e3192a8`.
- **The member.** A statement that a P-256 key signs holds the top-level member `alg`, the string
  `"ES256"`. A statement that an Ed25519 key signs holds no `alg` and no other member this
  amendment adds. It is byte for byte the statement it was before, under the same
  `delegationVersion` `"1"`, the same prefix and the same digest. No statement names Ed25519 by a
  member. An `alg` that is not a string, or is a string other than `"ES256"` (`"EdDSA"`,
  `"Ed25519"` and `"es256"` among them), is refused at step 3 (`malformed`).
- **Inside what is signed.** `alg` is a top-level member like any other, so the signing input (the
  prefix `"judgment-pack/delegation/1:"` and `canon` of the statement without `signature`) and the
  digest both cover it. Removing, adding or changing it changes the signed bytes.
- **The key.** A P-256 public key is its compressed point (SEC 1 §2.3.3): the byte `02` where y is
  even or `03` where it is odd, then the 32 bytes of x, big-endian. That is 33 bytes, written as 66
  lowercase hexadecimal characters. A verifier pins it only when its first byte is `02` or `03`,
  x < p, and x³ − 3x + b is a square modulo p. The uncompressed form (`04` and 64 bytes) and every
  other length are refused when the key is pinned. The cofactor is 1, so no point that exists is
  refused for its order.
- **The key identifier** is the first 32 lowercase hexadecimal characters of SHA-256 over the 33
  bytes. With gateway §1.5's synthetic scalar (32 bytes of `01`, a key no host holds), the point is
  `026ff03b949241ce1dadd43519e6960e0a85b41a69a05c328103aa2bce1594ca16` and the key identifier
  `dbdb99c64b3d511f72c88fb6c054da73`.
- **The signature** is `r||s`, each a 32-byte unsigned big-endian integer: 64 bytes, 128 lowercase
  hexadecimal characters, written as an Ed25519 signature is. It verifies under the pinned key
  exactly when 1 ≤ r ≤ n − 1, 1 ≤ s ≤ (n − 1)/2 (the low-S rule), and ECDSA verification (FIPS
  186-5 §6.4.2) holds with SHA-256 over the signing input as the message digest. A high-S
  signature, one with s > (n − 1)/2, does not verify, although plain ECDSA would accept it. A
  DER-encoded signature is not of the form: at its usual 70 to 72 bytes it is refused at step 3
  (`malformed`), and one that happened to be 64 bytes long would be read as `r||s` and fail step 5.
- **Why low-S.** For any valid `(r, s)`, `(r, n − s)` also passes plain ECDSA. Without the rule, any
  holder of a link could make a second signature over the same members, and so a second digest for
  one issued link, the digest a child, a receipt and a record name it by. The rule leaves one
  encoding per signature, and one digest per signing.
- **Signatures are not reproducible.** Two ES256 signings of one statement differ, so their digests
  differ. The issuing host signs a link once and keeps its bytes. It records the link it issued by
  that digest, and its `not-issued` check (*Authoritative state*) is of that digest. No verifier
  signs again in order to compare.
- **Choosing the algorithm and the key.** A verifier verifies a link by the algorithm its `alg`
  names, Ed25519 where it holds none, under the key its `keyId` names among the keys pinned for its
  `host` **of that algorithm**. A key is pinned with its algorithm: its length or form is held to
  that algorithm and never read as one. A key of the other algorithm is not the key the link names,
  so a link whose `keyId` names only a pinned key of the other algorithm is refused at step 4
  (`key-mismatch`). That is the refusal of an Ed25519-signed statement that has been given
  `alg: "ES256"`, and of an ES256 statement whose `alg` has been removed.
- **A chain may mix algorithms.** The rule is per link. Every link of a chain has one `host`
  (clause 3), and that host may hold pinned keys of both algorithms, while it moves from one to the
  other or for good. Each link is verified at steps 4 and 5 by its own `alg` and `keyId`, root
  first. The narrowing check of §3 compares neither: a child may be signed by the other algorithm
  than its parent, in either direction, and its `parent.digest` covers the parent's `alg` and
  signature. A verifier that will not accept one of the algorithms pins no key of it.
- **The proof-of-possession key is separate.** The algorithm of the run's RFC 9449 key (gateway
  §11.4 accepts `EdDSA` and `ES256` proofs) is independent of the statements' algorithm.
- **What the signer writes.** An issuing host writes only signatures that verify as above. A key
  service commonly returns an ECDSA signature DER-encoded, and with either value of s. The host
  then decodes it to r and s, replaces s with n − s where s > (n − 1)/2 (both verify under plain
  ECDSA, and only the low one here), and writes `r||s`, each padded to 32 bytes. It takes the key's
  33-byte compressed point from the public key the service exports, which is commonly an
  uncompressed point inside a key structure, and pins and publishes that point. The `keyId` it
  writes is the compressed point's.

**Verifying one ES256 link.** For a link that holds `alg`, steps 3 to 5 are, in this order, and the
first that fails is the refusal:
1. step 3: `alg` is the string `"ES256"`, and `signature` is exactly 128 lowercase hexadecimal
   characters; otherwise `malformed`;
2. step 4: among the keys pinned for the link's `host` with the algorithm ES256, one has the
   link's `keyId`; otherwise `key-mismatch`, a pinned Ed25519 key of that `keyId` included;
3. step 5: with r the first 32 bytes and s the last 32 of the signature, 1 ≤ r ≤ n − 1 and
   1 ≤ s ≤ (n − 1)/2, and ECDSA verification (FIPS 186-5 §6.4.2) holds under that key, the message
   digest being SHA-256 over the prefix `"judgment-pack/delegation/1:"` followed by `canon` of the
   link without `signature`; otherwise `signature-mismatch`.

A link that holds no `alg` is verified as before, by Ed25519 under a pinned Ed25519 key. Steps 1
and 2 and steps 6 and 7 are the same for both algorithms. Every refusal the amendment introduces
for a statement is one of the existing names `malformed`, `key-mismatch` and
`signature-mismatch`: no new refusal name is added at steps 1 to 7.

**Binding a chain to one scope identifier** (amendment of 2026-11-22). A *scope identifier* names
the party a gateway's sources serve, as the reference gateway defines it (gateway `SPEC.md` §1.2a,
the receipt's `scope`; §6, *Caller scope identifiers*). It is never a delegation's `scope`, which
names sources, tools and effects. A chain may be bound to exactly one scope identifier, so that its
calls reach that party's sources and no other's (agent issue #373).

- **The member.** `scope.scopeId` is a scope identifier in gateway §1.2a's form, never the marker
  `"unscoped"`. It sits inside `scope`, so the signing input and the digest cover it as they cover
  every member. A link that holds it is *bound*, and one that does not is *unbound*. A statement
  without it is byte for byte the statement it was before, whatever its algorithm.
- **Why inside `scope`.** A verifier written before the amendment refuses, at step 3
  (`malformed`), a member inside `scope` that version 1 does not name: every object within a link
  holds exactly the members version 1 names (gateway §11.1, which the agent library reads as the
  gateway does, agent ADR-0029). So it never admits a bound chain while ignoring its binding. A
  top-level member would be tolerated and ignored, and that verifier would then let a bound chain
  reach its sources of no scope identifier.
- **Its form.** A `scopeId` that is not a string of that form, or is `"unscoped"`, is refused at
  step 3 (`malformed`).
- **Along a chain** (§3, clause 9). Every link of a chain has the same binding: all are unbound, or
  all are bound to the same scope identifier. The binding is the root's, and each child repeats it.
  - A child cannot change it: another `scopeId` is `widened`.
  - **An unbound link under a bound one** is `widened`. It does not inherit the binding. Each link
    states its whole authority, as clause 6 makes it state its sources, so a reader of the leaf
    alone sees the binding.
  - A bound link under an unbound one is `widened` as well. An unbound chain reaches what the
    enforcing host lets an unbound delegation reach: at the reference gateway, the sources of no
    scope identifier, and never a scope identifier (gateway §6). A binding would change that reach,
    not narrow it, so a chain is bound from its root or not at all.
- **What it admits.** Under a bound chain, every entry of a `gateway` audience admits only a call to
  a source of that scope identifier, and every request names it. An `agent-host` entry is
  unaffected, since a host source has no scope identifier.
- **The request check, `scope-id-mismatch`.** Once step 0 has resolved the chain, and before step 8
  and any admission read, an enforcing host refuses a request:
  1. under a bound chain, that names no scope identifier, or one other than `scopeId`;
  2. under an unbound chain, that names a scope identifier;
  3. under a bound chain whose `scopeId` the enforcing host's own configuration does not let that
     issuing host's delegations reach (open question 27). A statement never grants a scope
     identifier that the enforcing host has not granted: scope isolation stays the enforcing
     host's.

  The refusal reads no issuing host, counts nothing and dispatches nothing. Case 3 is also refused
  when a credential is bound to the chain (§2, *The credential*), so no credential is bound to a
  chain that every call would be refused under.
- **At the gateway.** A delegated `/act` and a delegated `/acquire` may name `scope` only under a
  chain bound to that exact scope identifier, and then reach only that scope identifier's sources.
  Both routes follow the one rule, since a delegation bounds acquisitions and actions alike. A
  request that fails the check is refused `400` with `/acquire`'s sentence of a wrong scope,
  `scope: the request's scope does not match the source's` (gateway §6), which names no scope
  identifier: on `/acquire` where §6 refuses a wrong scope, and on `/act` at the scope step of
  gateway ADR-0054's order (its step 8, `"refusedAt": "scope-identifier"`). For a bound chain this
  replaces gateway §6's rule that a request under a delegation never reaches a scope identifier;
  an unbound chain keeps it. A source whose scope identifier is not the request's is refused by
  that step as today.
- **At the agent library.** It applies the same check before a call leaves the harness. Under a
  bound chain it sends `scopeId` as the scope of every acquisition and tool call to a gateway
  source, and refuses a gateway source whose mapping names another scope identifier, or none, as
  `scope-id-mismatch`. It checks the gateway's answer: a receipt whose `scope` is not `scopeId`
  withholds the result, as an unverified receipt does (agent ADR-0027).

The binding is independent of the algorithm and of §2a. An Ed25519 or an ES256 link may be bound,
and no read changes for it.

**Issuance.** The host issues a root only on the subject's authenticated grant. It refuses one whose
scope exceeds what the subject itself may do on that host when it is issued
(`subject-unauthorized`). A person cannot grant an agent more than the person holds, and a policy
can grant an agent less (desk #679). Children are issued by §3's rule.

**The credential.** Authority is exercised only through a credential that an enforcing host binds
to one leaf link.
1. **Who obtains it.** Only the issuing host requests a credential, over a channel on which it
   authenticates to the enforcing host as itself. Its request carries:
   - the chain;
   - the run's software (§1, rule 3);
   - the public key of the run's proof-of-possession key pair: an RFC 9449 (DPoP) key, or under
     RFC 8705 the client certificate's thumbprint.

   The enforcing host verifies the chain (steps 1 to 10, with no call yet), binds the credential to the
   leaf's `id`, the chain's digests, the software and the key, and returns it to the host. The host
   hands it to the run it started. An agent never obtains a credential by presenting statement
   bytes, and a request from anyone but the issuing host is refused.
2. **Lifetime.** A credential lives at most 5 minutes, and never past the leaf's `expiresAt`. The
   host obtains a fresh one against the current state as the run proceeds. This is independent of
   the delegation's own expiry, which can be up to 24 hours (open question 3).
3. **Sender constraint.** A credential is sender-constrained, under RFC 9449 or RFC 8705. A call
   that does not prove possession of the bound key is refused at step 0. The one exception is a
   chain whose every entry admits only `pure`, `read` or `read-external`: the operator may accept a
   bearer credential for it, still subject to the 5-minute lifetime, and posture reports that it
   did (open question 8).

The reason for both rules: a bearer credential that lives as long as the delegation lets a thief
perform the whole scope, mutations included, for up to a day. A short lifetime bounds that window
but does not close it. Sender constraint closes it, because the thief does not hold the run's
private key. Revocation (§4) does not make either rule redundant: it acts only once someone has
noticed.

**Authoritative state.** Steps 8 to 12 read state the issuing host holds:
- the inventory;
- revocations;
- the subject's standing in its authorization model (desk #612, #452);
- the `calls` counters.

The enforcing host gets this state by an **admission read**: an authenticated, synchronous request
to the issuing host, whose wire form is §2a. It names:
- the chain's digests;
- the call's audience, source, tool and effect;
- whether this dispatch is to be counted;
- the owner of the connection grant the call uses, where it uses one whose record names an owner
  and whose `ownerHost` is this issuing host, unless the enforcing host reads that owner's standing
  by §5's separate owner read instead (§5, rule 5).

The issuing host answers `admit`, or the first refusal of steps 8 to 12 and then of the owner's
standing (*Verification steps*, below). On `admit` with counting set, it has already incremented
the counters. Three checks are the issuing host's own:
- it answers `admit` only for links it recorded issuing, so a chain signed with a stolen key alone,
  without the host's channel credentials, is never admitted (`not-issued`, open question 18);
- it answers only an enforcing host that authenticates as the audience named in the call's entry,
  so one enforcing host can neither read another audience's state nor consume its counters;
- it checks `expiresAt` against its own clock as well, so an enforcing host with a slow clock does
  not admit past expiry.

The enforcing host does not admit from a copy, a cache or an earlier answer: a missing, late or
unreadable answer is a refusal. A gateway holds no authorization model of its own, so step 12 is
always the issuing host's answer (open question 10).

**When admission happens.** Admission is the check made **immediately before physical dispatch**.
It is made again after any approval pause, park, wake, re-authorization or freed attempt. A call
that was checked, but had not been dispatched when a revocation landed, is refused at its
re-check. Approval, a wait or an earlier check never carries authority past a revocation.

**Verification steps.** The enforcing host resolves the chain, root first, ending with the leaf it
bound to the credential. For a host source, the agent harness is the enforcing host and binds no
credential: step 0 then requires that the chain is the one the issuing host supplied to the run
when it started it, never one a model, a tool result or a child supplies. For one call the
enforcing host applies the steps below and stops at the first failure.
Where a step concerns links, links are taken from root to leaf, and within a link the reasons are
taken in the order the step lists them.

| Step | Refusal | Condition |
| --- | --- | --- |
| 0 | `credential-mismatch` | the presented credential is not live at this enforcing host, is expired, does not prove possession of its bound key where one is bound, or, if the caller also presents a chain, its bound chain is not byte-identical to the chain the caller presents |
| 1 | `malformed` | a link is not a JSON object, has a duplicate member name, holds a value outside the `canon` domain, or lacks a string `delegationVersion` |
| 2 | `unsupported-version` | a link's `delegationVersion` is a string other than `"1"` |
| 3 | `malformed` | a link violates any structural constraint of version 1 above: a member missing, of another type or form, an array out of order or with a repeat, `expiresAt` not after `issuedAt`, `parent` and `depth` inconsistent, or over a size cap; or it holds an `alg` that is not the string `"ES256"`, or a `scope.scopeId` that is not a scope identifier |
| 4 | `key-mismatch` | a link's `keyId` is not a key the verifier pinned for its `host` with the link's algorithm (ES256 where it holds `alg`, Ed25519 where it holds none), or reached by a rotation it followed (open question 1) |
| 5 | `signature-mismatch` | a link's signature does not verify over the input above: under gateway §8.4's rules for Ed25519, and under gateway §1.5's for ES256, the low-S rule included |
| 6 | `chain-broken` | §3's clauses 0 to 3 fail |
| 7 | `widened` | §3's clauses 4 to 9 fail |
| 8 | `not-yet-valid`, then `expired` | at the enforcing host's authoritative time t, some link has t < `issuedAt` minus the skew allowance (open question 17), or t ≥ `expiresAt` |
| 9 | `agent-unregistered`, then `software-mismatch` | some link's `act.agent` is not `active` in the inventory of `host`; or some link's `act.software` differs from its own actor's current inventory entry; or the **leaf's** `act.software` differs from the software bound to the credential |
| 10 | `not-issued`, then `revoked` | the issuing host has no record of issuing some link; or some link is revoked, some link's actor is revoked, or the subject has been removed from the host (§4) |
| 11 | `out-of-scope` | the call is not within the scope of some link. The refusal names the first failing reason, in the order `source`, `tool`, `effect`, `limit-unknown`, `limit` |
| 12 | `subject-mismatch`, then `subject-unauthorized`, then `tool-version-refused`, then `skill-refused` | the source's declared identity is a person other than `sub` (§7, rule 1), or the call is outside what the subject itself may do on the issuing host now, the subject's standing on a service's or a connection's credential included; on a read of version `"2"` only (§2a), the issuing host does not admit the call at the descriptor digest the read names, or with the skills it names as loaded |

Steps 1 to 7 depend only on the bytes and a pinned key, so any party can repeat them later. Steps 0
and 8 to 12 depend on the enforcing host's credential bindings and time, and on the issuing host's
state. They are admission checks. An enforcing host that cannot establish the state a step needs
refuses rather than admitting. Clock uncertainty closes admission, as ADR-0025 closes dispatch on
unavailable ownership evidence.

Some refusals are not verification steps, and they sit outside this table:
- `principal-changed` is a fence check (§7, rule 2), made with the lease at the same admission and
  before step 0;
- `action-key-unauthenticated`, `action-key-scope-conflict` and `standing-unknown` come from the
  gateway's action-key lookup (§4, rule 4; §7, rule 3), made before the counting admission read;
- `owner-removed`, then `owner-unknown`, come from the connection grant's owner standing (§5,
  rule 5). They are ordered **after step 12**: a call that steps 0 to 12 refuse reports that
  refusal, and a call they admit is refused if the owner has been removed or its standing cannot
  be read. Where the owner is named in the admission read, the issuing host answers the owner's
  standing after steps 8 to 12, and an owner refusal is not `admit`, so it counts nothing. Where
  the enforcing host makes §5's separate owner read instead, it makes it after the admission read
  answers `admit`. A call it then refuses is not dispatched, and its counted budget stays
  consumed, which fails closed, as a lost answer does;
- `scope-id-mismatch` is a request check (§2, *Binding a chain to one scope identifier*), made
  once step 0 has resolved the chain and before step 8;
- `not-parent-actor` and `delegation-not-permitted` are issuance refusals (§3);
- `admission-unknown`, `read-version-unsupported` and `read-malformed` concern the read itself
  (§2a), not the chain. The enforcing host refuses the call under them where the issuing host's
  answer to steps 8 to 10 would be reported, and nothing is counted.

### 2a. The admission reads on the wire

*Added by the amendment of 2026-11-22, in the standards-track part.* §2 says what an admission read
names and what it answers. Two enforcing hosts make it today and send the same body: the reference
gateway for its sources (gateway `SPEC.md` §11.5) and the agent library for its host sources (agent
[ADR-0029](https://github.com/Judgment-Pack/judgment-pack-agent/blob/main/docs/adr/0029-agent-principals.md)). An issuing host built by another
party must read that body byte for byte, so its form is stated here. Version `"1"` is the form as
built; version `"2"` adds two members to a call read and a third kind of read.

**Transport.** A read is a `POST` of `canon` bytes to the issuing host's admission URL, over HTTPS,
authenticated by a credential the enforcing host holds for that host (gateway §11.2's
`admission.url` and `admission.credential`). It follows no redirect and waits at most 5 seconds. It
takes only a `200` answer of at most 4096 bytes that the `canon` parser reads as one of the answers
below. An enforcing host that reaches the issuing host in process, as the agent library does through
the host's admission port, hands the port the same body and reads the same answers. Anything else,
no answer included, refuses as `admission-unknown`, so the read fails closed. A body is at most
65536 bytes in `canon`.

**The kinds of read, version `"1"`.** Every body holds `readVersion`, `host` (the issuing host, a
flat token) and `audience` (the enforcing host's own, §2), and is one of:

| Read | Body, beside those three | Answers |
| --- | --- | --- |
| call | `"chain": [digest, ...]` (root first), `"call": {"source", "tool", "effect", "count"}` or `null`, `"at": time` (the enforcing host's *t*) | `{"admission": "admit"}`; `{"admission": "refuse", "refusal": R}` with R one of `expired`, `agent-unregistered`, `software-mismatch`, `not-issued`, `revoked`, `subject-mismatch`, `subject-unauthorized`; or, for a read that names a call, `{"admission": "refuse", "refusal": "out-of-scope", "reason": X}` with X one of step 11's reasons |
| standing | `"standing": principal reference` (§4, rule 4) | `{"standing": "current"}` or `{"standing": "removed"}` |

A call read whose `call` is `null` is the one made when a credential is bound (§2, *The
credential*). It names no call and counts nothing.

**Version `"2"`.** A call read of version `"2"` is version `"1"`'s, with `readVersion` `"2"` and two
more members in `call`, both required:

| Member | Form | Meaning |
| --- | --- | --- |
| `version` | digest, or `null` | the descriptor digest of the tool called, from the approval the enforcing host dispatches under (below); `null` where that approval records none |
| `skills` | array of `{"id": skill id, "digest": digest}`, or `null` | the skills loaded in the run at the call, ordered by `id` by code point, no `id` repeated; `[]` when none is loaded; `null` from an enforcing host that does not observe the run's skills |

Every other member, and its form and meaning, is version `"1"`'s. A binding read of version `"2"`
has `call` `null`, as in version `"1"`, and a standing read of version `"2"` is version `"1"`'s with
`readVersion` `"2"`. A call read of version `"2"` may also be answered with R `tool-version-refused`
or `skill-refused` (step 12). Version `"2"` adds the skill-load read (below).

**Which digest `version` is.** The reference gateway defines one descriptor digest per tool. A
customer binding's snapshot of version 3 or 4 holds, on every allowed tool's entry,
`descriptorDigest`: `"sha256:"` and the SHA-256 of the exact JSON bytes of that tool's descriptor
object as the server's `tools/list` reported it, before any display filtering and with every member
the display omits (gateway
[`docs/design/tool-descriptors.md`](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/12b0f43de0aa4b9e43e3fadca3cb9697e50f1087/docs/design/tool-descriptors.md),
*Customer snapshot version 3*; also `adapters/README.md`). It is a digest of exact bytes, not of
`canon`: a change of formatting within the descriptor changes it, and needs the operator's
recapture. The snapshot that holds it is pinned per operation by its own digest (gateway ADR-0021,
`operationDescriptors`), and its signed provenance is gateway `SPEC.md` §9. Immediately before a
call under such a snapshot, the gateway refuses a tool whose current descriptor differs from the
approved one (`mcp-descriptor-drift`), so the approved digest is the descriptor of the tool called.

`version` is that digest:
- **from the gateway,** the `descriptorDigest` of the called tool's entry in the snapshot the call's
  operation pins (the live operation for `/acquire`, the write operation for `/act`), and `null`
  where that snapshot is of a version that holds no `descriptorDigest`;
- **from the agent library,** the digest its own approval of the tool records, by the same
  definition, and `null` where its approval records none (open question 24).

It is taken from the approval the enforcing host holds, never from the request, the model or the
tool's answer, as the effect is (§2, *Within the scope*).

**Which skills `skills` names.** A skill is the agent library's named, versioned bundle (agent
[ADR-0009](https://github.com/Judgment-Pack/judgment-pack-agent/blob/main/docs/adr/0009-skills.md)). An entry names it by its `id` (a letter, then
letters, digits and hyphens, at most 24 in all) and its bundle digest (`skill.json#/$defs/digest`:
`"sha256:"` and the SHA-256 of the canonical JSON of its bundle, as ADR-0009 defines it), which is
the digest the person approved and the run loaded it at. The set is the one the run's checkpoint
records as loaded (`checkpoint.skills`) at the instant of the read, after every load and unload
before it.
- **Library reads only.** Only the agent library loads skills, so only its reads carry them, as an
  array that may be empty. The library makes its read for every call of a tool with a source,
  gateway sources included, without counting for those (§2, *Counting `calls`*). So the issuing
  host judges a gateway call's skills on the library's read.
- **What a gateway read carries instead: `null`.** The gateway does not observe what a run has
  loaded, and it never takes a list from the caller: a list a request carried would be the caller's
  assertion, and an enforcing host admits nothing on one (§2, *The statement is not a credential*).
  `null` says "not observed", never "none loaded".
- **What it proves.** The library reports what it loaded, as the issuing host states the run's
  software (§1, rule 3). It is attested by the harness, not proved, and it does not show which
  instructions the model followed.

**What the issuing host does with them.** It may admit or refuse by them, as its policy and the
subject's approvals say. A call it would admit but for the tool's version is refused
`tool-version-refused`; one it would admit but for a loaded skill is refused `skill-refused`. Both
are step 12, after `subject-mismatch` and `subject-unauthorized`, in that order, and like every
refusal they count nothing. A `null` is judged by the host's policy. A policy that refused a call for
skills it cannot see would refuse every gateway read, so the proposed default is to judge skills on
the library's reads alone and to admit a gateway read's `null` (open question 25). A version `"1"`
read carries neither member, and is judged as a version `"2"` read carrying `null` for both.

**The skill-load read** (version `"2"` only). The agent library asks it immediately before a skill
loads into a delegated run, after its own checks (the skill is catalogued and admitted, and its
digest is the pinned one, ADR-0009) and after step 8 at its own time. Its body is
`{"readVersion": "2", "host", "audience", "chain": [digest, ...], "load": {"skill": {"id",
"digest"}, "skills": [{"id", "digest"}, ...]}, "at"}`, where:
- `load.skill` is the skill to load;
- `load.skills` is the set already loaded, in the form of a call read's `skills`, never `null`, and
  never holding `load.skill.id`;
- `audience` is the library's agent-host audience, `chain` the run's chain and `at` its time.

It is answered `{"load": "admit"}`, or `{"load": "refuse", "refusal": R}`, with R the first that
holds of `expired`, `agent-unregistered`, `software-mismatch`, `not-issued` and `revoked` (steps 8
to 10, as for a call read), then `skill-refused`: the issuing host does not admit that skill, at
that digest and beside the skills already loaded, for this chain now.

How it differs from a call read:
- it names no source, tool, effect or version, so step 11 does not apply, and it carries no
  `count`: it dispatches nothing, and no counter moves, whatever it answers;
- it makes no action-key lookup and uses no connection grant, so no owner read follows it;
- it is made once per load, immediately before the load. A refused or unanswered read loads
  nothing: `load_skill` answers with the refusal (`admission-unknown` where the read fails), the
  checkpoint's `skills` and `skill_loaded` are not written, and the run goes on. An unload makes no
  read;
- an earlier answer never carries past a revocation. A resumed run asks again for each skill it
  restores, in the checkpoint's load order, each read naming those restored before it, and it drops
  a skill that is refused;
- an `admit` grants nothing: a skill grants no tool (ADR-0009), and every call that follows makes
  its own call read, which names the skill in `skills`.

An undelegated run makes no skill-load read. A library configured for version `"1"` makes none
either, and its call reads carry no skills.

**Which version a sender sends.** An enforcing host sends every read to one issuing host at one
version: the version its configuration names for that host, `"1"` where it names none. That
configuration is how the sender knows. Its operator sets `"2"` only once the issuing host has said,
in the contract it publishes, that it reads version `"2"`. A sender never negotiates and never falls
back. A version `"2"` read that is refused is not sent again as version `"1"`, which would drop the
version and the skills from the host's judgment, and a version `"1"` sender never tries `"2"`. A
sender configured for a version its host does not read fails closed (below).

**The upgrade order.**
1. The issuing host reads `"1"` and `"2"`, the skill-load read included, and says so.
2. Each enforcing host's operator moves that host to `"2"`. The agent library and the gateway may
   move in either order: neither's read depends on the other's version.
3. The issuing host keeps reading `"1"` for as long as any enforcing host it serves may send it.
   Version `"1"` stays readable, and nothing in this amendment retires it.

**An unknown version, and a read of another form.** Once it has authenticated the sender as the
audience (§2, *Authoritative state*), the issuing host reads the body in this order and answers the
first check that fails:
1. the body is not a `canon` object of at most 65536 bytes, or holds no string `readVersion`:
   `{"refusal": "read-malformed"}`;
2. `readVersion` is a string the host does not read: `{"refusal": "read-version-unsupported"}`;
3. the body is not exactly one kind of read its version defines, or a member is missing, of another
   form, or not defined at that version (a `version` or `skills` in a version `"1"` call, or a
   `load` at version `"1"`), or a `skills` array is out of order or repeats an `id`:
   `{"refusal": "read-malformed"}`.

Neither answer admits, counts or records anything. An enforcing host that sends version `"2"`
refuses the call or the load under that name, and a standing read so answered as
`standing-unknown`, as any other answer to a standing read (§4, rule 4). An enforcing host that
sends only version `"1"` reads neither answer form, and refuses as `admission-unknown`. Either way
the read fails closed, and it is not retried at another version.

### 3. Chained delegation

A child link narrows a parent link `P` for another actor, or for the same actor with less: for
example, a sub-agent (agent
[ADR-0013](https://github.com/Judgment-Pack/judgment-pack-agent/blob/main/docs/adr/0013-sub-agents.md))
or another registered agent. The chain is recorded: each child names its parent by `id` and
digest, and every record of a call names the whole chain (§6).

**Who may obtain a child.** The issuing host issues a child of `P` only when two conditions hold:
- `P.mayDelegate` is `true`;
- the request comes either from `P`'s actor, authenticated by the live credential bound to `P` and
  relayed by the host, or from the subject's own authenticated grant.

It refuses otherwise:
- `delegation-not-permitted` when `P.mayDelegate` is `false`;
- `not-parent-actor` when the requester is neither of those.

A child whose actor runs other software than `P`'s actor needs the subject's grant (open
question 6). A request from a third registered agent, or from a party that holds only statement
bytes, obtains nothing.

**The narrowing check.** A chain `L0, …, Ln` (root first) is valid exactly when clause 0 holds and,
for each child `C = Lk` and its parent `P = L(k−1)`, `k ≥ 1`, clauses 1 to 9 hold:

0. `L0.parent` is `null` and `L0.depth` is `0`; a chain that starts below its root is broken;
1. `C.parent.id` equals `P.id`, and `C.parent.digest` equals the digest of `P`;
2. `C.depth` equals `P.depth + 1`, and does not exceed the maximum depth (open question 3);
3. `C.host` equals `P.host` (open question 7);
4. `C.sub` equals `P.sub` in all three members, so the subject never changes along a chain;
5. `C.issuedAt` ≥ `P.issuedAt`, and `C.expiresAt` ≤ `P.expiresAt`;
6. for every entry `e` of `C.scope.sources` there is an entry `p` of `P.scope.sources` with the
   same `audience` and `source`, and `e.tools` ⊆ `p.tools`, and `e.effects` ⊆ `p.effects`;
7. for that same pair, every limit name of `p.limits` is a limit name of `e.limits`, and
   `e.limits[name]` ≤ `p.limits[name]`. `e.limits` may add names `p.limits` does not have, which
   is sound because every limit is an upper bound;
8. `P.mayDelegate` is `true`: a child exists only below a link that permits one;
9. `C.scope.scopeId` and `P.scope.scopeId` are both absent, or both present and equal (amendment
   of 2026-11-22).

Clauses 0 to 3 failing is `chain-broken`; clauses 4 to 9 failing is `widened`. Equality is of
`canon` bytes. No clause compares `alg` or `keyId`: a child signed by the other algorithm than its
parent is valid when the clauses hold (§2, *Signing with a P-256 key*). The check is pairwise,
and by transitivity a link is never wider than any ancestor.
The host refuses to issue a child that would fail it, and every verifier checks it again, because
issuance is not evidence that the check was made.

### 4. Revocation

A **revocation** names a delegation `id`, an agent principal, or a removed principal. The issuing
host records it with the revoking principal and its time (open question 20).

Who may revoke:
- a delegation: its subject, the issuing host, and, for a child, the actor of its parent;
- an agent principal: the host, and the principal that registered it.

1. **Effect on new calls.** A revocation takes effect at the instant the issuing host records it
   durably.
   - From then, every admission read (§2) answers `revoked`. This covers every call under the
     revoked link, under every link below it in any chain, and under every chain with a revoked
     actor.
   - No enforcing host admits without a fresh admission read, so none admits after that instant.
   - The credentials bound to the revoked links are also revoked at the enforcing hosts that hold
     them, as a second barrier behind the admission read.
   - The host acknowledges the revocation to the revoker once it has recorded it durably.
2. **The subject's own access is untouched.** A revocation of a delegation or an agent never
   revokes, rotates or invalidates a session, token, credential or connection grant of the subject,
   and never changes the subject's authorization. The one interaction runs the other way. Removing a
   principal from the host revokes every delegation whose `sub` it is, and every chain below them;
   the connection grants it owns follow §5. This is how the removal of a person who has left
   reaches "every delegation they authorized" (desk #679). Delegations are revoked, never
   quarantined (open question 22).
3. **Effects in flight.** A revocation stops dispatch; it cannot undo a call already dispatched. An
   effect dispatched before the revocation follows the existing uncertain-action rules, unchanged:
   - gateway `SPEC.md` §1.2b: an action whose delivery is `uncertain` is reconciled by its declared
     read-back to `committed` or `unknown`, and neither outcome permits another dispatch;
   - agent ADR-0025 decision 1: an in-flight effect "remains unknown until reconciled by its
     authoritative host", and takeover "never automatically replays it";
   - agent ADR-0025 decision 4: re-authorization "is not retry permission".

   A revocation never turns an uncertain effect into a refused one, and never into a retry. A call
   that was admitted but not dispatched is not in flight: it is refused at its re-check (§2, *When
   admission happens*).
4. **Requests on an action key, before and after revocation.** A gateway request whose action key
   names an existing reservation is resolved **by key**, before the counting admission read (§2).
   A reservation made under a delegation records its scope: the gateway authority, the chain's
   `sub` (`kind`, `issuer` and `subject`), the chain's root actor, and the issuing host.

   **The key grants nothing on its own.** It is public in receipts (`action.delivery.key`). Before
   any retained response or read-back, the gateway authenticates the sender against the
   reservation's scope. For the actor, one part of that check, the read-back's source and tool,
   is made only once the key lookup has found the key uncertain (below). Only these senders are
   accepted:

   | Sender | Authenticated by | Before revocation | After revocation |
   | --- | --- | --- | --- |
   | the run's actor | a live credential bound to a chain whose `sub` and root actor equal the reservation's: step 0 and steps 1 to 7 applied, and step 11's `source` and `tool` conditions applied to the action's write source and tool on every link, and, for a request answered by the declared read-back, to the read-back's own source and tool on every link as well; steps 8 to 10, 12 and step 11's effect and limit conditions not, since nothing new is admitted | accepted | not possible: no live credential exists |
   | the subject | its own token, whose verified issuer and subject equal the reservation's `sub`, and a standing read (below) that answers the subject `current` | accepted | accepted, unless the subject has been removed |
   | the issuing host | authenticated as the reservation's issuing host, acting for the run | accepted | accepted |
   | the gateway's operator | the gateway's own operator authentication | accepted | accepted |

   Any other sender, a bare key, or a credential bound to another scope is refused as
   `action-key-unauthenticated`, and the refusal discloses nothing about the reservation. The one
   exception is the read-back's source and tool check, whose refusal discloses only what
   *The read-back's source and tool*, below, states.
   - **The actor's source and tool.** A narrower link of the same family has the reservation's
     `sub` and root actor, and may still exclude the action's write source or tool. Its credential
     is refused as `action-key-unauthenticated`, so no link reaches an action's retained response
     outside its own scope.
   - **The read-back's source and tool.** The declared read-back is another operation from the
     write: under gateway §1.2b its source is `<platform>/live` where the write's is
     `<platform>/write`, and it runs the declared read tool. A link may hold the write and exclude
     the read-back's source or tool. So a request that the key lookup answers with the read-back is
     held to step 11's `source` and `tool` conditions twice on every link: for the action's write,
     and for the read-back's own source and tool. A link that excludes either is refused as
     `action-key-unauthenticated` and no read-back runs, so no link triggers a read-back outside its
     own scope. The check is made after the key lookup finds the key uncertain and before the
     grant's state, owner read or publisher check (grant revoked or quarantined, `owner-unknown`,
     `action-reconciliation-unavailable`); its refusal tells a link that already holds the write
     only that the key awaits a read-back. A request answered from retained evidence runs no
     read-back and is not held to its source and tool. For neither operation are the effect and
     the limits checked:
     they bound what is dispatched, and a freed attempt is a dispatch that makes the full admission
     read of §2.
   - **The first dispatch that leaves the key uncertain** (amendment of 2026-11-22, #293). The check
     above refuses a *later* request on an uncertain key. It does not refuse the request whose own
     dispatch left the key uncertain: that request's write may already have been sent, and a refusal
     could lead the client to send it again under a new key. Where a link excludes the read-back's
     source or tool, no read-back runs, and that request is answered with its uncertain record
     (gateway `SPEC.md` §11.8: `409`, `action-reconciliation-unavailable`). Every later request on
     the key is held to the check above.
   - **How the gateway learns that the subject was removed.** The subject row makes no admission
     read, so the gateway makes a **standing read**: an authenticated, synchronous request to the
     reservation's issuing host, naming the subject and asking whether it is a current principal.
     It is answered `current` or `removed`. `removed` is refused as `action-key-unauthenticated`,
     and a missing, late or unreadable answer as `standing-unknown`. The read fails closed, and it
     is made on every subject request, before and after revocation.
   - **What an authenticated sender gets.** Retained evidence or the declared read-back. Only the
     actor's live credential can reach a freed attempt, and that attempt is a dispatch: it makes
     the counting admission read like any other. After revocation, no sender reaches a freed
     attempt or any dispatch. A read-back through a connection grant is a use of that grant, and
     §5's rule 5 applies to it: where the grant is revoked or quarantined, or its owner is refused,
     no read-back runs, and the action's outcome stays `unknown`.
   - **Counting.** The read-back is not a call under the delegation and counts against no limit
     (open question 12).
   - **Recording the read-back.** The read-back's receipt records `caller` as the reservation's
     subject pair: the same `issuer` and `subject` that the cited action's `requester` carries.
     `tokenDigest` is the digest of the token the sender presented. The sender is recorded in a new
     signed top-level member, `reconciler`:
     `{"kind": "actor" | "subject" | "host" | "operator", "issuer": string, "subject": string}`.
     It holds the identity the sender authenticated as; for the actor, `issuer` is the issuing
     host and `subject` the agent's identifier.
   - **What verifiers then report.** Gateway §1.2b's check resolves the cited action "under the
     same authority and authenticated issuer and subject". The amendment to §1.2b would say that,
     on a read-back carrying `reconciler`, that pair is `caller`'s, which is the reservation's
     subject and not the sender's token. A legitimate reconciliation then resolves for every
     sender above, and a new verifier holds `reconciler` to its form.
   - **What an older verifier reports.** It tolerates `reconciler` as an unknown signed member,
     resolves the read-back, and reports the same `action-committed` or `action-uncertain`
     observation it would for the subject's own read-back. It is misled on one point only: it takes
     the read-back as made by the subject, when the issuing host or the operator may have sent it.
   - **Undelegated reservations.** Reservations made under no delegation keep §1.2b's scope and
     rules unchanged.
5. **No restoration.** A revoked delegation is never un-revoked. A new grant is a new statement
   with a new `id`.
6. **Removing a connection grant's owner.** Removing the owner of a connection grant from the host
   revokes or quarantines that grant (§5, rule 5). The gateway then refuses every call through the
   grant, a read-back included, whatever delegation it comes under. Delegations whose `sub` is the
   removed owner are revoked by rule 2. Other delegations are unchanged, since they name sources,
   not grants.
7. **Compromise of the issuing host's key.** Revoking a `keyId` revokes every delegation it signed,
   and every chain through one (open question 18).

### 5. The connection grant, a principal-held resource

The standing grant behind a gateway connection is the provider authorization that lets the gateway
reach a mail account, a file store, a source-control host, a work-tracking service, a data platform
or a customer MCP server. It is a resource held by a principal, and it is distinct from a
delegation: a delegation narrows what one actor may do on a subject's behalf, while a grant is what
the gateway holds at all. A credential bound to a delegation (§2) is always narrower than the grant
it is derived from.

**The grant record** (gateway #357). It carries no credential, no token, no token digest and no
content.

| Member | Form | Meaning |
| --- | --- | --- |
| `connection` | flat token | the gateway's connection |
| `owner` | principal reference, or `null` where no owner is recorded (rule 5) | the person or service that authorized the grant and answers for it |
| `ownerHost` | flat token, or `null` exactly when `owner` is | the issuing host that holds the owner's standing |
| `scopes.required` | array of strings, ordered, no repeats | the union of the minimum scopes the connection's sources declare per operation |
| `scopes.granted` | array of strings, ordered, no repeats | what the provider granted, as last read |
| `scopes.used` | array of `{"scope": string, "lastUsedAt": time}`, ordered by `scope` | each granted scope that some dispatched call exercised, and when last |
| `lastUsedAt` | time or `null` | the last dispatched acquisition or action through the connection |
| `idleExpiry` | integer milliseconds, or `null` | the configured idle bound; `null` is none |
| `state` | `"active"`, `"quarantined"` or `"revoked"` | `revoked` is terminal |
| `publisher` | object or `null` | for a customer MCP server, below; `null` otherwise |

**Rules.**

1. **Least privilege at connect.** A connection that requests or holds a scope outside
   `scopes.required` is refused. Where the provider cannot narrow its grant, the connection is
   admitted and reports `excess-scope` with the extra scopes named.
2. **Drift.** Where the provider reports the scopes of a grant, the gateway reads them again on use;
   a scope added since the record was made is reported as `excess-scope` and the record updated.
3. **Granted against used.** A scope is *used* when a dispatched call's operation declares it among
   its required scopes. The record says this is derived from declarations, since few providers
   report which scope a call exercised. An operator query lists `granted` minus `used`, the scopes
   to trim.
4. **Idle lifecycle.** A grant is revoked by rule 6 when it has a non-null `idleExpiry` and its
   `lastUsedAt` is at least `idleExpiry` before the current time. A grant never used is measured
   from its creation. Equal is expired.
5. **Owner removal, proposed as normative.** Removing the owner principal from the host revokes
   **or** quarantines every grant it owns, as the operator configured (open question 13).
   - A quarantined grant admits no call and keeps its credential.
   - It leaves quarantine only by being revoked, or by being reassigned to a new owner. Only the
     operator of the issuing host may reassign it, and the reassignment takes effect only on the
     new owner's authenticated acceptance.
   - No grant remains usable with a removed owner.
   - **Pending action keys stay `unknown`.** Revoking or quarantining a grant deletes no record of a
     pending action. A quarantined grant serves no call, a declared read-back included, and a
     revoked grant has no credential. So an action whose declared read-back runs through the grant
     cannot be reconciled while the grant is revoked, quarantined or refused by its owner read. Its
     outcome stays `unknown` (§4, rule 3): a verifier reports it as `action-uncertain`, and it
     permits no other dispatch. A quarantined grant that is reassigned and accepted is in use
     again, and a read-back through it is then a use like any other.

   **How the gateway learns of the removal: a read at each use.** Before every use of a grant —
   delegated or not, a read-back included — the gateway learns the owner's standing from
   `ownerHost`. It does so in one of two ways:
   - **In the admission read.** For a delegated call whose grant's `ownerHost` is the issuing host,
     the enforcing host may name the grant's owner in the admission read (§2), and the issuing host
     answers the owner's standing with the rest.
   - **By an owner read.** Otherwise — an undelegated call, which makes no admission read, a grant
     whose `ownerHost` is another host, or an enforcing host that does not carry the owner in its
     admission read — the gateway makes an **owner read**: an authenticated, synchronous request to
     `ownerHost` asking whether the owner is a current principal.

   Either way, an owner that has been removed is refused (`owner-removed`) and rule 5 is applied to
   the grant. A missing, late or unreadable answer is refused (`owner-unknown`). For a delegated
   call, both refusals are ordered after step 12 (§2, *Verification steps*).
   - A grant never used after its owner's removal is caught at its next use, at its idle expiry
     (rule 4), or by the operator's periodic owner read.

   Why a read and not a notification: a notification event that the issuing host sends on removal
   can be late or lost. It would need a delivery guarantee the project does not offer: ADR-0025
   puts notification delivery guarantees out of the package's scope. Until it arrived, the gateway
   would keep admitting. A read at each use fails closed, reuses the synchronous admission read
   where a delegated call's owner is named in it, and needs no new delivery contract. Its cost is
   one synchronous owner read per use of an owned grant outside the admission read: an undelegated
   call, a delegated call whose enforcing host makes the separate owner read, and a read-back,
   which makes no admission read. A gateway may still act early on a removal it is told about, but
   such a message never admits anything.

   **A grant with no recorded owner.** A grant made before gateway #357, or one whose owner the
   operator has not yet recorded, has `owner` and `ownerHost` `null`. It is used as today, and the
   gateway's grant report names it with the finding `owner-missing` for as long as it has no owner,
   so no such grant stays outside this rule unseen. An owner, once recorded, is changed only by
   the reassignment above, never cleared.

   *Why a report and not a requirement at adoption.* Requiring the owner fields when gateway #357
   is adopted would either refuse every connection made before the record existed, which breaks
   working connections at an upgrade, or have the gateway fill in an owner it does not know. A
   guessed owner is worse than a named gap: its removal would revoke a grant it never answered
   for, and the real owner's removal would miss it. Only the operator knows who authorized a grant
   made before the record, so the record leaves the gap visible until the operator closes it.
6. **What revoking a grant does.** The gateway calls the provider's revocation endpoint where it
   offers one (for an OAuth provider, RFC 7009 token revocation), deletes the credential, and sets
   `state` to `revoked`. Where the provider offers no revocation, it deletes the credential and
   reports `provider-grant-may-persist`, since the authorization may still exist at the provider.
7. **Publisher trust for customer MCP.** At registration (gateway #348), `publisher` records the
   server's publisher and its liveness:
   `{"kind": "registry" | "repository" | "domain", "name": string, "state": "maintained" |
   "unmaintained" | "unknown", "checkedAt": time}`. Liveness covers the domain's registration,
   whether the repository is archived and whether the package is deprecated.
   - It is shown with the approval, and checked again on recapture and on a schedule.
   - A lapsed or archived publisher reports `publisher-unmaintained`, which an operator policy may
     make a refusal (open question 15).
   - A registration whose display name closely matches a known integration's, under a different
     publisher, is flagged `name-lookalike`.

A grant's owner is the principal answerable for it, not the subject of every call through it. How
the two meet is §7, rule 1.

### 6. Recording

**Gateway receipts.** A version 3 receipt for a call made under a delegation carries a new
top-level member, `delegation`, signed with every other member under §1.2a's rule:

| Member | Form | Meaning |
| --- | --- | --- |
| `id` | opaque identifier | the leaf link's `id` |
| `host` | flat token | the issuing host |
| `actor` | opaque identifier | the leaf's `act.agent` |
| `subject` | principal reference | the chain's `sub` |
| `chain` | array of digests, root first, ending with the leaf's | the chain the call was admitted under |
| `admittedAt` | time (millisecond form) | the enforcing host's authoritative time at the final admission before dispatch (§2) |

**The compatibility rule, exact.** Under a delegation:

1. `caller.issuer` and `caller.subject` are `delegation.subject.issuer` and
   `delegation.subject.subject`. On an action receipt, so are `action.requester.issuer` and
   `action.requester.subject`. `tokenDigest` is the digest of the token presented, which is the
   per-delegation credential. That credential may have been issued by a party other than
   `caller.issuer`: by the gateway itself, or by the exchange that minted it.
2. `caller` is never `null` on a receipt that carries `delegation`.
3. `receiptVersion` stays `"3"`, the signing prefix is unchanged, and no member changes its form.
   **The meaning of `caller` and `requester` does change** on a receipt that carries `delegation`.
   - Before, the triple described one token: its issuer, its subject and its digest.
   - Here, `issuer` and `subject` name the delegation's subject, and `tokenDigest` names a different
     credential, which another issuer may have issued.

   Gateway §1.2a's text for `caller` and `requester` would be amended to say exactly this.
4. A call made under no delegation carries no `delegation` member (open question 2), and its receipt
   is byte for byte the receipt it was before this record.

**What a verifier written before this record sees.**
- It tolerates `delegation` as it tolerates any signed member it does not know, and returns the
  status it returned before.
- It reads `caller` and `requester` as naming the subject: the same pair it read when agents used
  the subject's own token.
- It does not see the actor. That is the bound of rule 1, and such a reader had the same bound
  when agents used the subject's credential.
- It is misled on exactly one point: a reader that treats `{issuer, subject, tokenDigest}` as one
  token's, and correlates `tokenDigest` with that issuer's token records, finds no such token.

**What a verifier that reads the member checks.**
- **At §1.4 order 1:** it holds the member to the forms above. Within the one receipt, it also
  requires rules 1 and 2, and a `chain` of at least one and at most the maximum depth plus one
  digests. Gateway §1.2a says order 1 is never a relational check. These comparisons are between
  members of one receipt, so they are a stated exception, and the §1.2a amendment would say so.
- **Given the statements,** it may report `delegation-unresolved` beside `ok`, as gateway §4's
  steps 5 to 8 report their findings, when any of these holds:
  - a digest of `chain` resolves to no statement;
  - the chain's length is not the leaf's `depth` plus one;
  - steps 1 to 7 of §2 fail;
  - the leaf's `id`, `sub` or `act.agent` differ from `id`, `subject` or `actor`;
  - `admittedAt` falls outside the validity of some link: before its `issuedAt`, or at or after
    its `expiresAt`;
  - the call was served before it was admitted (below).
- **Admission and service are different instants.** Validity is judged by `admittedAt`, which
  names the admission. `servedAt` names a later event: the gateway stamps it after the source or
  executor has returned, and later still for an uncertain action. So a call admitted before
  `expiresAt` may be served after it, and that is not a finding.
- **Served no earlier than admitted.** `servedAt` is the gateway's stamp, to the second, of the
  form `YYYY-MM-DDTHH:MM:SSZ`. It is parsed, never compared by characters. It stands for the
  interval `[s, s + 1 s)`, and the call was served before it was admitted exactly when
  `s + 1 s` ≤ `admittedAt`. A `servedAt` of any other form is reported `delegation-unresolved`.
- **Revocation** at the served instant is not established offline unless a revocation statement
  (open question 20) is also given. The receipt asserts only that the gateway admitted the call.

**Agent records.** The record kinds are those of
[ADR-0024](https://github.com/Judgment-Pack/judgment-pack-agent/blob/main/docs/adr/0024-versioned-record-readers.md).
- **What carries `principal`.** Run events (`tool_call` and `tool_result` among them), the
  checkpoint, and the run report carry `principal`:
  `{"actor": {"agent", "host", "software"}, "subject": principal reference, "delegation": {"id",
  "digest"}, "chain": [digest, ...]}`.
- **Versions.** It ships under the versions after those current when this was written, which are
  run event 2, checkpoint 3 and run report 2. So the new versions are run event 3, checkpoint 4 and
  run report 3, unless the agent repository has moved on by then.
- **ADR-0019's identity is unchanged.** The source record's `identity` keeps its form and its
  meaning, the credential kind and label, beside `principal`.
- **Delegation is opt-in.** As ADR-0025's facilities are, delegation is an explicit opt-in: a run
  with no delegation configured keeps writing the current versions, byte for byte.
- **Older readers refuse.** A reader from agent v0.10.0 onward that predates these versions refuses
  them (`record version unsupported`) before reading the body, so it never reads an agent's call as
  the person's. Readers older than v0.10.0 predate ADR-0024, and this record promises nothing about
  them.

**Refusals are recorded.** A refused call is recorded with its refusal name, its actor and subject
where they parsed, and no credential.

**The Desk** shows both principals on runs, receipts and history (desk #679). It records every
registration, entry change, delegation, revocation and connection action with who performed it.

### 7. Relation to existing contracts

1. **Agent #102's identity and the subject.**
   - Under this record, the subject of every call is the delegation's `sub`.
   - **A `person` identity becomes the subject.** ADR-0019's per-source identity was the only
     principal a record named. When it is kind `person`, it names the subject: that person must be
     `sub`, or the call is refused as `subject-mismatch`.
   - **A `service` or `connection` identity names the credential's holder,** not the subject. For
     `service`, that is the service. For `connection`, it is the grant's owner (§5), or, for a host
     source with no grant record, the host itself.
   - **Using another principal's credential needs the subject's own standing.** When the
     credential's holder is not `sub`, the call is admitted only if the issuing host's
     authorization model gives `sub` standing to use that service's or connection's credential for
     the call (step 12, `subject-unauthorized`). A person's agent therefore never exceeds the
     person's authority, even through a connection a service owns (open question 11).
   - **One chain per run is enough.** The subject is the same for every source in the run, while
     the credential holders differ by source and are each checked for the subject's standing.
   - **What ADR-0019 keeps.** The label stays a display name, an identity change mid-run is still
     withheld until re-approval, and the first `act` under a `service` identity is still asked.
2. **Leases bound time; delegations bound authority.**
   - **A call needs both.** It needs a current fence (ADR-0025: owner, epoch, expiry, checked at
     admission) and a valid delegation. Neither stands in for the other: renewing a lease renews no
     delegation, and a new delegation renews no lease.
   - **Expiry or revocation while the lease is held.** Admission refuses, and the run parks for
     re-authorization naming the delegation. It never retries on its own.
   - **That park extends ADR-0025 decision 4.** Decision 4 parks with "a bounded connection
     reference and the unsent operation". Naming a delegation needs a new wait format, which
     agent #260 carries.
   - **The lease records its principal.** The fence today names no principal. So the lease record
     gains the run's admitted `sub` and root actor (the `act.agent` of `L0`): a new `run-lease`
     schema version, and a fence version that carries them.
   - **A takeover keeps the principals.** A worker that acquires a run's lease presents the run's
     chain. The effect host refuses a fenced dispatch whose `sub` or root actor differs from the
     lease's, as `principal-changed`. A takeover is a new epoch of the same principals, never a
     change of principal.
3. **Action keys are scoped to the subject and the root actor.**
   - **The scope.** Under a delegation, gateway §1.2b's key scope ("gateway authority,
     authenticated issuer and subject") becomes four values: the gateway authority, the chain's
     `sub` (`kind`, `issuer` and `subject`), and the chain's **root actor**.
   - **Why `kind` is included.** A person and a service that happen to share an issuer and subject
     pair then still have different scopes.
   - **What it excludes.** The transport token, the lease epoch, the worker and the delegation `id`.
     So a delegation re-issued for the same run keeps its keys.
   - **A takeover.** It presents the same subject and root actor and finds the same reservation. It
     is answered from retained evidence, a freed attempt or the declared read-back, never a new
     mutation.
   - **Relation to #352.** This is #352's second option, refined, for delegated runs. It composes
     with ADR-0025's epoch-free idempotency identity, which already binds the run.
   - **Undelegated calls.** A call made under no delegation keeps the scope §1.2b states today. So
     an undelegated takeover that authenticates as another subject still needs #352's own fix,
     decided with agent #229.
   - **A key presented under another scope.** It is open question 9.

## Alternatives

- **No change.** Agents keep using the person's credential. Every problem above stays, and the
  takeover defect needs a separate fix.
- **Each agent as a service identity of its own.** This gives the agent an identity but drops the
  subject. An audit sees a service, not on whose behalf it acted, and the service accumulates a
  standing grant wider than any one person's share. It is ADR-0019's `service` kind, which already
  exists and is not this.
- **Impersonation** (RFC 8693's other case). The agent receives a token that presents as the
  subject. It narrows nothing an audit can see, and it is exactly the indistinguishability this
  record removes.
- **Provider scopes alone.** OAuth scopes narrow per platform. They cannot name the project's effect
  classes or tools, cannot express a chain, and many providers cannot narrow below the grant.
  Gateway #356 covers that last case: the gateway enforces the scope itself where the platform
  cannot.
- **Attenuable capability tokens.** In this design, each holder of a token can append a caveat that
  narrows it, without contacting the issuer. That attenuation is the narrowing check this record
  states. It would add a second canonical form and signing convention to a project that has one,
  and offline attenuation cannot consult revocation or the subject's current standing. The
  statement here could later be carried in such a token without changing the check.
- **Put it in Core.** Core is a pack format, and authorization of an agent at an enforcing host is
  not a property of a pack. A companion beside Core is the proposed home of the shared statement.
- **A new `delegationVersion` for ES256** (amendment of 2026-11-22). A version `"2"` statement would
  change the prefix and make the version of every statement a choice between algorithms. The
  gateway's precedent (§1.5) puts `alg` inside the signed bytes and keeps the record's version. An
  Ed25519 statement then stays byte for byte, and an older verifier refuses an ES256 one at step 4.
- **Negotiating the read version per read.** A sender that tried `"2"` and fell back to `"1"` on a
  refusal would let any failure drop the version and the skills from the host's judgment. A
  configured version fails closed instead.
- **Skills in the statement's scope.** A scope that listed admitted skills would bind them at
  issuance, and a new skill, or a new digest of one, would need a new statement. The skill-load read
  asks for the issuing host's current judgment at the load, as standing is asked at the call, and
  leaves the statement as it is.

## Compatibility

- **Receipts.** See §6's rule. The version stays `"3"`, and every existing verifier tolerates the
  new signed member and returns the status it returned before. `caller` and `requester` keep naming
  the subject's pair, but on a delegated receipt `tokenDigest` names another credential (rule 3).
  A receipt made under no delegation is unchanged in its bytes. A verifier that knows version 2
  alone already refuses version 3, and still does. A reconciliation read-back of a delegated action
  carries `reconciler`, which existing verifiers tolerate; they resolve it as the subject's own
  read-back (§4, rule 4).
- **Action keys.** Unchanged for calls made under no delegation. Under a delegation, the scope
  changes from the transport subject to the delegation's subject and root actor. A key reserved
  under a transport subject before a gateway adopts this stays in its old scope.
- **Leases.** A new `run-lease` version and fence version carry the principal (§7, rule 2). Version
  1 leases are read as before and cannot host a delegated run.
- **Agent records.** New record versions, written only by runs with delegation configured. Readers
  from v0.10.0 onward refuse them by ADR-0024 rather than misreading them. ADR-0019's identity member
  is unchanged in form and meaning.
- **Desk.** No record format of the Desk changes by this record. Its authorization model gains a
  kind of principal (desk #612, #452).
- **Spec.** Nothing in Core `0.3.0`, its schema, corpus or released artifacts changes. Release `v0.4.0`
  carries this Draft and no normative text.
- **Statements, after the amendment of 2026-11-22.** An Ed25519 statement is unchanged in its
  bytes, its version, its prefix and its digest, and every verifier reads it as before. A verifier
  written before the amendment reads an ES256 statement as an Ed25519 one carrying an unknown signed
  member. Its `keyId` names no Ed25519 key that verifier pinned, so it refuses the link at step 4
  (`key-mismatch`) and never admits it. An issuing host signs with a P-256 key only once every
  enforcing host it issues to pins that key with its algorithm.
- **Scope binding, after the amendment.** An unbound statement is unchanged. A verifier written
  before the amendment refuses a bound one at step 3 (`malformed`), so it never admits a bound
  chain as an unbound one. A delegated request that names no scope identifier, under an unbound
  chain, is answered as before.
- **Reads, after the amendment.** Version `"1"` is unchanged and stays readable. A sender moves to
  `"2"` only by its configuration, after the issuing host says it reads it (§2a). A version `"1"`
  sender that receives one of the new answer forms reads it as `admission-unknown`, which fails
  closed.
- **Spec, for the amendment.** Release `v0.6.1` carries `specVersion` `0.6.0` unchanged: no Core
  text, schema or released conformance case changes (*Release*, under [Acceptance
  plan](#acceptance-plan)).

## Security and privacy

- **Confused deputy.** Without a subject, an agent's reach is its credential's. The delegation and
  step 12 hold every call to the intersection of the scope and the subject's current authority,
  through another principal's connection as much as through the subject's own.
- **Statement substitution and minting.** An enforcing host resolves the chain from the credential
  it bound (step 0). It binds credentials only at the issuing host's authenticated request, and
  child links only at the parent actor's or the subject's (§3). Holding statement bytes, by
  themselves, therefore admits nothing and mints nothing.
- **Public action keys.** A key is published in every action receipt. It grants nothing: every
  request on a key authenticates its sender against the reservation's scope before any retained
  response or read-back (§4, rule 4).
- **Widening along a chain.** The narrowing check is pairwise and repeated by every verifier;
  issuance is not trusted as evidence of it.
- **Credential theft.** A stolen credential is useless without the run's proof-of-possession key,
  and lives at most 5 minutes. A bearer credential is accepted only for read-only chains, and posture
  reports it.
- **The issuing host's key.** Its holder can issue any delegation within what it believes the subject
  holds. Verification proves the host signed, not that the subject consented: the host's record of
  the grant is the evidence of consent, and it is the host's. Key compromise is open question 18.
- **The issuing host's state.** Admission trusts the issuing host's answer for inventory, revocation,
  standing and counters. An issuing host that answers falsely admits falsely. The admission read
  makes that host a single point of availability, and the record chooses refusal over admission
  when it is unreachable.
- **Revocation races.** A call dispatched an instant before a revocation proceeds and is
  reconciled, never undone or retried. A call that was checked but not dispatched is refused at its
  re-check. "At once" means at the next admission read after the durable record.
- **Clocks.** Expiry is decided by the enforcing host's authoritative time, within a stated skew
  allowance (open question 17). Uncertainty refuses.
- **Software attestation.** The bound software identity is the host's statement (§1, rule 3), not a
  measurement. A host that misstates it misstates it.
- **Disclosure.**
  - A receipt already discloses the subject's issuer and subject in `caller`. The new member adds
    the agent's opaque identifier and the chain's digests, and no label.
  - A grant record carries scope names and times, no credential and no content.
  - Publisher checks query public registries and domains, which can disclose to those services
    which servers an operator uses. The schedule is the operator's.
- **Resource exhaustion.** Depth, lifetime and statement size are bounded (open questions 3 and 21).
- **Name lookalikes.** The flag is a heuristic. It reports, and refuses only by operator policy.
- **Algorithm confusion** (amendment of 2026-11-22). The algorithm is named inside the signed bytes,
  and keys are pinned with theirs. Neither a key's length nor a member a party adds after signing
  chooses how a link is verified, and removing or adding `alg` is refused at step 4.
- **Signature malleability.** The low-S rule leaves one ES256 encoding per signature, so no holder
  of a link can make a second digest for it.
- **Scope isolation.** A binding narrows and never grants. The enforcing host admits a bound chain
  only for a scope identifier its own configuration lets that issuing host's delegations reach, so
  an issuing host cannot move an agent into another party's scope by signing a statement.
- **The descriptor digest and the skills are the enforcing host's.** `version` comes from the
  enforcing host's approval and `skills` from the library's own record, never from the request. A
  gateway read says `null` rather than repeat what a caller claims. Skills are attested by the
  harness, as software is (§1, rule 3).
- **No downgrade of the read.** A sender's read version is configured, never negotiated, and a
  refused version `"2"` read is never sent again as `"1"`.
- **Disclosure, version `"2"`.** A read discloses to the issuing host the tool's descriptor digest
  and the ids and digests of the loaded skills. It never carries a skill's instructions or a
  descriptor's text.

## Conformance

A Draft claims no conformance class and ships no vectors. A normative version would need at least
the vectors below, positive and negative, hand-written and read by two independently written
readers.

- **Delegation statement:**
  - a valid root, and a valid three-link chain;
  - each structural violation of step 3, one per member;
  - a non-string `delegationVersion` (`malformed`), and the string `"2"` (`unsupported-version`);
  - an unpinned key, and each key refusal of gateway §8.4;
  - a signature over a changed member;
  - a signature with `S` not below the group order;
  - a signature that verifies only under the cofactored check;
  - a member appended at the top level and inside `scope`;
  - a member name outside the Basic Multilingual Plane, ordered by `canon` and not by RFC 8785;
  - a statement over each size cap.
- **Narrowing:**
  - one vector per failing clause, 0 to 8, with clause 0 as a truncated chain;
  - a child that adds a limit its parent lacks (valid), and one that drops one (widened);
  - an equal expiry (valid), and a later expiry (widened);
  - a changed `sub`, and a changed `sub.kind`;
  - a different `audience` with the same `source`;
  - `mayDelegate` false with a child below it;
  - a depth one past the maximum.
- **Issuance:**
  - a child requested by a third registered agent (`not-parent-actor`);
  - a child under `mayDelegate: false`;
  - a credential requested by a party that presents only statement bytes;
  - a root whose scope exceeds the subject's standing.
- **Credential:**
  - a chain substituted beside a valid credential;
  - a credential without its proof of possession;
  - a bearer credential for a chain with `act`;
  - a credential used after 5 minutes;
  - a credential used past the leaf's `expiresAt`.
- **Admission:**
  - equal-time expiry, not yet valid, and each edge of the skew allowance;
  - an unregistered actor, at the leaf and at an ancestor;
  - a software mismatch against the entry and against the credential, and a valid chain whose
    links' actors run different software;
  - a link the issuing host never recorded (`not-issued`), and an admission read from an enforcing
    host that is not the entry's audience;
  - a gateway audience whose authority label contains `:`;
  - a revoked leaf, a revoked ancestor, a revoked agent and a removed subject;
  - each `out-of-scope` reason, and their order within a link and across links;
  - two concurrent admissions at a `calls` limit of one;
  - a limit counted across a chain, a freed attempt counted, and a read-back not counted;
  - a subject that has lost the access since issuance;
  - a person's agent through a service-owned connection, with and without the person's standing;
  - an approval pause across a revocation.
- **Receipts:**
  - an acquisition and an action under a delegation, verified by a reader that knows the member
    and by one written before it, both returning `ok` and the same `caller`;
  - `caller` differing from `delegation.subject` (`malformed` for the new reader);
  - a `null` caller with the member;
  - a tampered member (`signature-mismatch`);
  - a call under no delegation, byte-identical to the receipt before this record;
  - `delegation-unresolved` for each of its causes;
  - `admittedAt` before `issuedAt`, equal to it, and equal to `expiresAt`;
  - a call admitted before `expiresAt` and served after it (no finding);
  - `servedAt` one second before `admittedAt`, in the same second, and of another form.
- **Action keys and leases:**
  - a takeover authenticating as another transport subject, with the same subject and root actor:
    one mutation, or the outcome stays `unknown`;
  - a takeover with another root actor (`principal-changed`);
  - a re-issued delegation keeping the key;
  - a key presented under another scope with the same subject, and with another subject;
  - reconciliation before and after revocation, by each sender of §4, rule 4's table, with its
    receipt's `caller` and `reconciler`, verified by a reader that knows `reconciler` and by one
    written before it;
  - a key presented with no credential, and with a credential bound to another scope
    (`action-key-unauthenticated`);
  - a key presented with the credential of a narrower link of the same `sub` and root actor
    whose scope excludes the action's write source, and one whose scope excludes its tool
    (`action-key-unauthenticated`), and one whose scope excludes only its effect and holds the
    read-back's source and tool, accepted on a key with retained evidence, or an uncertain key
    answered by read-back, and refused `out-of-scope` (reason `effect`) on a key whose attempt is
    freed;
  - an uncertain key presented with the credential of a link that holds the action's write source
    and tool and excludes the read-back's source, and one that excludes its read tool
    (`action-key-unauthenticated`, no read-back run), and the same links on a key with retained
    evidence (accepted);
  - an uncertain key whose grant is revoked, presented with the credential of a link that
    excludes the read-back's source (`action-key-unauthenticated`, the check made before the
    grant's state);
  - the subject's request with the standing read answering `removed`
    (`action-key-unauthenticated`), and unanswered (`standing-unknown`);
  - a request answered from retained evidence, and one refused at the key lookup, neither counted;
    a check before an approval pause not counted, and the dispatch after it counted once;
  - a first dispatch that leaves its key uncertain under a link that excludes the read-back's
    source, and one under a link that excludes its read tool: each answered `409`
    `action-reconciliation-unavailable` with its uncertain record and no read-back run, and a later
    request on that key with the same credential refused `action-key-unauthenticated` (#293).
- **Connection grants:**
  - excess scope, refused and, where the provider cannot narrow, reported;
  - drift, and unused scopes listed;
  - idle expiry at equal time;
  - owner removal revoking and quarantining, and reassignment with and without acceptance;
  - an undelegated call after the owner's removal (`owner-removed`), and with the owner read
    unanswered (`owner-unknown`);
  - a delegated call after the owner's removal, with the owner named in the admission read
    (`owner-removed`, nothing counted) and with a separate owner read (`owner-removed`, the
    counted budget consumed and the call not dispatched);
  - the same call that step 12 also refuses, on each path, reporting step 12's refusal: with the
    owner named in the admission read, and with a separate owner read, which is not made; nothing
    counted on either path;
  - a grant with no owner, used and reported `owner-missing`;
  - an owner recorded once, then a second recording of an owner that is not a reassignment,
    refused, and a clearing of the owner, refused (never cleared);
  - a pending action whose read-back grant is quarantined, and one whose grant is revoked, each
    staying `unknown` with no read-back run;
  - a read-back whose owner read goes unanswered: `owner-unknown`, no read-back run, the outcome
    stays `unknown` and the grant stays `active`;
  - a request on an uncertain key whose grant was revoked: no dispatch, no read-back, answered with
    its uncertain record, outcome stays `unknown`;
  - a provider without revocation, reporting `provider-grant-may-persist`;
  - a lapsed publisher, and a name lookalike.
- **Agent records:**
  - `principal` on each record kind;
  - an older reader refusing the new version, and a run without delegation writing the current
    version unchanged;
  - a child's narrowed chain recorded;
  - a refused attempt to widen.

### Conformance cases the amendment of 2026-11-22 adds

Both implementations must pass every case that applies to them; the `skills` and skill-load cases
are the library's alone. The cases are hand-written, under `conformance/delegation/` in this
repository, staged in no Core corpus as the witness and dialect vectors are, and each states its
expected verdict. *Kind* is P (positive), N (negative) or B (boundary). The ES256 statements are
signed once, by a signer independent of both implementations, and frozen, since ES256 signatures are
not reproducible (gateway ADR-0053's corpus rule). They use gateway §1.5's synthetic key, a second
synthetic P-256 key for the unpinned cases, and a synthetic Ed25519 key. The tables are in build
order: ES256 first (*Acceptance plan*).

*1. ES256 statements, steps 1 to 7.*

| Case | Kind | Expected |
| --- | --- | --- |
| `es256-root`: a root signed by the synthetic P-256 key, holding `alg: "ES256"` | P | `ok` |
| `es256-key-03`: a root under a P-256 key whose y is odd (prefix `03`) | B | `ok` |
| `es256-chain-three`: three ES256 links | P | `ok` |
| `es256-chain-five`: five ES256 links, the maximum depth | B | `ok` |
| `mixed-ed-es-ed`: an Ed25519 root, an ES256 child and an Ed25519 grandchild, both keys pinned | P | `ok` |
| `mixed-es-ed`: an ES256 root and an Ed25519 child | P | `ok` |
| `mixed-p256-unpinned`: `mixed-ed-es-ed` with the P-256 key not pinned | N | `key-mismatch`, at the child |
| `es256-high-s`: a valid signature with s replaced by n − s | N | `signature-mismatch` |
| `es256-s-half-plus-one`: s = (n − 1)/2 + 1 | B | `signature-mismatch` |
| `es256-r-zero`, `es256-s-zero`, `es256-r-n`, `es256-s-n` | B | `signature-mismatch` |
| `es256-der`: the valid signature DER-encoded, 72 bytes | N | `malformed` |
| `es256-sig-126-hex`, `es256-sig-uppercase` | B | `malformed` |
| `es256-alg-stripped`: an ES256 statement with `alg` removed and its signature kept | N | `key-mismatch` |
| `alg-on-ed25519`: an Ed25519-signed statement holding `alg: "ES256"`, signed with it | N | `key-mismatch` |
| `alg-eddsa`, `alg-ed25519`, `alg-lowercase`, `alg-number` | N | `malformed` |
| `es256-appended`: a top-level member appended after signing | N | `signature-mismatch` |
| `es256-changed`: a member changed after signing | N | `signature-mismatch` |
| `es256-resigned-parent`: a child naming the digest of a second signing of its parent's members | N | `chain-broken` |
| `ed25519-unchanged`: the gateway's 39 Ed25519 cases (`testdata/delegation/statements.json`), byte for byte | P, N, B | their recorded verdicts |
| `p256-pin-04`, `p256-pin-05`, `p256-pin-x-is-p`, `p256-pin-no-point`, `p256-pin-64-hex` | N | the pin is refused, and a link under that key is `key-mismatch` |

*2. The Draft's own missing cases, Ed25519.* `ed25519-s-not-below-order` and
`ed25519-cofactored-only` (N, `signature-mismatch`); `ed25519-pin-non-canonical`,
`ed25519-pin-small-order` and `ed25519-pin-off-curve` (N, the pin is refused); `scope-256-entries`,
`tools-256` and `limits-16` (B, `ok`), beside `scope-257-entries`, `tools-257` and `limits-17` (B,
`malformed`); `child-parent-id-differs` (N, `chain-broken`); and `member-missing-<name>`, one per
member of version 1 (N, `malformed`).

*3. The scope binding.* At the gateway, `scope-id-mismatch` is answered as §2's *At the gateway*
states, with `/acquire`'s sentence of a wrong scope.

| Case | Kind | Expected |
| --- | --- | --- |
| `bound-root`: a root bound to a synthetic scope identifier | P | `ok` |
| `bound-chain`: three links bound to the same one | P | `ok` |
| `bound-es256`: an ES256 chain, bound | P | `ok` |
| `bound-unbound-child`: an unbound child under a bound parent | N | `widened` |
| `bound-under-unbound`: a bound child under an unbound parent | N | `widened` |
| `bound-changed`: a child bound to another scope identifier | N | `widened` |
| `bound-unscoped-marker`: `scopeId: "unscoped"` | N | `malformed` |
| `bound-not-a-string`, `bound-bad-form` | N | `malformed` |
| `unbound-unchanged`: the cases of table 1, which hold no `scopeId` | P | unchanged |
| `request-bound-names-it`: a delegated `/act`, and an `/acquire`, naming `scopeId`, to a source of it | P | admitted |
| `request-bound-names-none` | N | `scope-id-mismatch`; no host read, nothing counted |
| `request-bound-names-other` | N | `scope-id-mismatch`; no host read, nothing counted |
| `request-unbound-names-one` | N | `scope-id-mismatch` |
| `request-unbound-names-none`, as before the amendment | P | admitted, to a source of no scope identifier |
| `request-bound-source-of-other`: naming `scopeId`, to a source of another scope identifier | N | the gateway's wrong-scope refusal |
| `bound-not-configured`: a `scopeId` not configured for the issuing host | N | `scope-id-mismatch`, at binding and at a call |
| `library-bound-mapping-other`: a gateway source mapped to another scope identifier | N | `scope-id-mismatch`, before the call leaves the harness |
| `library-receipt-scope-differs`: a receipt whose `scope` is not `scopeId` | N | the result withheld |
| `library-bound-host-source`: a host source under a bound chain | P | admitted, with no scope sent |

*4. Reads (§2a).* Each case holds the exact body and the answer, and says what is counted.

| Case | Kind | Expected |
| --- | --- | --- |
| `read-v1-call`: a version `"1"` call read, byte for byte as the gateway sends it | P | `admit`, counted when `count` is `true` |
| `read-v2-library-no-skills`: `skills: []`, `version` a digest | B | `admit` |
| `read-v2-library-two-skills`: two skills, ordered by `id` | P | `admit` |
| `read-v2-skill-refused`: a loaded skill the host does not admit | N | `skill-refused`, nothing counted |
| `read-v2-gateway`: `skills: null`, `version` the tool's `descriptorDigest` | P | `admit`, counted |
| `read-v2-version-null`: `version: null` | B | `admit` (the proposed default) |
| `read-v2-version-refused`: a digest other than the one the subject approved | N | `tool-version-refused`, nothing counted |
| `read-v2-order`: the subject unauthorized and the version refused | N | `subject-unauthorized` |
| `read-v2-binding`: `call: null` | P | `admit`, nothing counted |
| `read-v2-standing`: a standing read at version `"2"` | P | `current` |
| `read-version-unknown`: `readVersion: "3"` | N | `read-version-unsupported`; nothing counted; no version `"1"` read sent |
| `read-version-not-a-string`: `readVersion: 2` | N | `read-malformed` |
| `read-v2-to-v1-host`: a version `"2"` read to a host that reads only `"1"` | N | `read-version-unsupported`, not resent |
| `read-v1-sender-new-answer`: a version `"1"` sender answered `{"refusal": "read-version-unsupported"}` | N | `admission-unknown` |
| `read-v1-with-skills`: a version `"1"` call carrying `skills` | N | `read-malformed` |
| `read-v2-skills-missing`, `read-v2-skills-unsorted`, `read-v2-skills-repeated`, `read-v2-call-and-load` | N | `read-malformed` |
| `read-body-over-cap`: a body over 65536 bytes, by its `skills` | B | `read-malformed` |

*5. The skill-load read.*

| Case | Kind | Expected |
| --- | --- | --- |
| `skill-load-admit` | P | `admit`; no counter moves |
| `skill-load-first`: `load.skills: []` | B | `admit` |
| `skill-load-refused` | N | `skill-refused`; nothing loaded, no `skill_loaded` written |
| `skill-load-revoked`, `skill-load-expired`, `skill-load-not-issued` | N | `revoked`, `expired`, `not-issued` |
| `skill-load-at-expiry`: `at` equal to the leaf's `expiresAt` | B | `expired` |
| `skill-load-answer-lost` | N | `admission-unknown`; nothing loaded |
| `skill-load-with-count`: a `load` carrying `count` | N | `read-malformed` |
| `skill-load-names-itself`: `load.skills` holding `load.skill.id` | N | `read-malformed` |
| `skill-load-at-v1`: a `load` at version `"1"` | N | `read-malformed` |
| `skill-load-resume`: two restored skills, the second refused | P | the first loaded, the second dropped |
| `skill-load-undelegated`: a skill loaded in an undelegated run | P | no read made |

## Implementation

- **The agent harness** carries the chain per run, checks it before each dispatch, and records
  `principal`, in TypeScript and Go readers that share vectors (agent #260).
- **The gateway** verifies the chain at credential binding and at `/acquire` and `/act`. It binds
  sender-constrained credentials, writes the receipt member, scopes action keys and keeps grant
  records (gateway #356, #357, #352). Its Go verifier and its TypeScript verifier are the two
  receipt readers.
- **The Desk** issues delegations, keeps the inventories, answers admission reads and performs
  revocation (desk #679).
- **A second statement verifier** could be written from §§2–3 alone, since the forms are those the
  gateway already specifies.

*As built, at the amendment of 2026-11-22.* The gateway's row is built (gateway `SPEC.md` §11;
`go/delegation_statement.go` and `go/delegation_admission.go`), and so is the agent library's
(agent ADR-0029, accepted for agent v0.13.0, in Go and TypeScript). Both verify steps 1 to 7 for
Ed25519 statements, and both send version `"1"` reads. The gateway signs and verifies its own
records with ES256 since v0.38.0 (gateway §1.5), but it verifies only Ed25519 delegation statements:
its issuing-host keys are Ed25519 (gateway §11.2), as the library's are. Neither verifies an ES256
statement, holds a chain to a scope identifier, sends a version `"2"` read or asks a skill-load
read: both refuse a bound statement at step 3 today, and at the gateway a delegated request
reaches no scope identifier (gateway §6). The Desk's row (desk #679) is not assessed here.

All of these are written by one maintainer with assistance from one vendor's models. None is
independent organizational interoperability evidence ([Acceptance plan](#acceptance-plan)).
Same vendor, not a cross-vendor claim.

## Acceptance plan

*Added by the amendment of 2026-11-22.* This record is to move to Accepted on the evidence below,
built once the maintainer's reviewer has accepted this text. RFC 0000's bar is met by building
that evidence, and the record states it as what it is.

**The implementations.** Two separately written implementations build the standards-track part
from this text alone, not from each other's code or reading, and each passes every case of
*Conformance cases the amendment of 2026-11-22 adds* that applies to it:
- the reference gateway, in Go, the enforcing host for its sources (gateway `SPEC.md` §11);
- the agent library, in Go and, where it reads delegations, in TypeScript, the enforcing host for
  its host sources (agent ADR-0029).

Each implements ES256 statements and the scope binding (§2), and version `"2"` reads (§2a). The
library alone carries skills and asks the skill-load read; the gateway's reads carry `null`.

**What they are, and are not.** RFC 0000 asks for "at least two plausible independent
implementations", and says that "a stable normative feature should not be accepted without evidence
from two independent implementations". These are two separately written bodies of code, in separate
repositories. They are not independent in authorship: one maintainer writes both, with assistance
from one vendor's models, and the library's existing verifier was written from the gateway's
reading and checks itself against the gateway's vectors. Their agreement on every case shows that
the text can be implemented twice from itself. It does not show that independent parties
interoperate, as [RFC 0017](0017-checkpoint-witness-statement.md) said of its own readers. Same
vendor, not a cross-vendor claim. The standards-track part is proposed for acceptance on this record
at draft maturity, as the Type says, and the stable bar is not claimed.

**The cases that exist today.** None in this repository: the Draft ships no vectors. Outside it:
- in the gateway, at commit `12b0f43de0aa4b9e43e3fadca3cb9697e50f1087`:
  `testdata/delegation/statements.json`, 39 statement cases for steps 1 to 7 and the narrowing
  check, all Ed25519; `testdata/delegation/receipt-members.json`; and nine receipt stores,
  `corpus/v3/stores/v3-delegation-*.json`, which belong to the exploratory part (§6);
- in the agent library: `contract/testdata/principal/gateway-statements.json` (the gateway's 39,
  cited by repository, commit and digest) and `citation.json`; and `contract/vectors/principal/`,
  whose `admission.json` holds 33 admission cases with the exact read each makes, beside
  `answer.json`, `binding.json`, `chains.json`, `child.json`, `events.json`, `record.json`,
  `refusal.json` and `report.json`.

**The build order.** ES256 comes first, because a P-256 key is to sign delegation chains with no
Ed25519 key beside it. Each step depends only on those before it.
1. This text is accepted by the maintainer's reviewer and frozen.
2. **ES256.** The statement cases of tables 1 and 2 are made once, by a signer independent of both
   implementations, and frozen. Then the gateway's check: P-256 issuing-host keys pinned with their
   algorithm, and steps 3 to 5 as §2 states them, with its 39 Ed25519 cases passing unchanged. Then
   the library's check, in Go and TypeScript, against the same cases.
3. **The scope binding.** Its statement cases, then the gateway's request check on `/act` and
   `/acquire`, then the library's, with the request cases of table 3.
4. **Version `"2"` reads** at both, then the skill-load read at the library, with tables 4 and 5,
   against an issuing host, or a test double of one, that answers them.
5. The record below, and the maintainer's decision.

Steps 2 and 3 need nothing of step 4, and are not held for it.

**The work list.** What the evidence still needs:
- the conformance cases above, in this repository, where none exists today;
- the Draft's own missing cases (table 2);
- ES256 verification at the gateway, whose issuing-host keys are Ed25519 today (gateway §11.2), and
  at the library, Ed25519 only today (ADR-0029), with each one's pin form for a P-256 key;
- the scope binding at both: today both refuse a bound statement at step 3, and the gateway refuses
  `scope` on every delegated request (gateway §6);
- version `"2"` reads at both, and the skill-load read at the library;
- an issuing host's signer that writes low-S `r||s` and the compressed key (§2, *What the signer
  writes*): the chains a P-256 key signs come from it, and neither implementation is that signer;
- the review of the amendment's pull request (*Review standing*);
- `releases/v0.6.0.normative.json`, which a patch release needs (*Release*, below).

**The record.** At acceptance this section gains the record: each implementation's repository and
commit; the cases each passes, by name, and any it does not, with the reason; the review held or
waived; and the words "same vendor, not a cross-vendor claim". The status then becomes Accepted, at
draft maturity, by the maintainer's recorded decision. Until then the record is a Draft.

**Release.** Under [`VERSIONING.md`](../VERSIONING.md#release-numbers-and-specversion), the release
is **`v0.6.1`**, carrying `specVersion` `0.6.0` unchanged. This amendment changes no Core text, no
Core schema and no released conformance case or row. The cases it plans are staged in no Core
corpus, and a patch release "may change documentation, tooling, companion documents and staged
drafts". It stays `v0.6.1` on two conditions:
- the patch needs the normative record `releases/v0.6.0.normative.json`, which the release builder
  requires for any patch tag and which does not exist yet;
- if any other item of the release changes a Core schema or a released row, the release is `v0.7.0`
  instead.

Spec #391 (action receipts: an approval citation, a dry run and a scope), designed in a gateway
decision record of its own, folds into the same release. *Placeholder: its text follows.*

## Unresolved questions

Each has a proposed default. A default is a proposal for review, not a decision taken for `0.5.0`.

1. **Who signs a delegation, and how its key rotates.**
   - The issuing host signs, with an Ed25519 key pinned by `keyId`. Subject-held keys are not
     required.
   - Rotation uses a continuity statement modelled on gateway §3b, under its own prefix,
     `"judgment-pack/delegation-rotation/1:"`.
   - The host publishes it in a registry file of its own, which verifiers read as §3b's reader
     reads the gateway's registry.
   - A rotation to or from a P-256 key names the key's algorithm beside it, as gateway §3b's
     `nextAlg` and `previousAlg` do (amendment of 2026-11-22).
2. **`delegation` absent or `null` when no delegation applies?** Absent, so that a receipt made
   under no delegation is unchanged in its bytes. Its absence never proves the caller was not an
   agent; it proves only that no delegation was presented.
3. **Bounds and re-issue.**
   - A link lives at most 24 hours (`expiresAt − issuedAt`), the lease amendment's longest
     duration. Maximum depth 4.
   - A run that outlives its root parks for re-authorization, and re-issue needs the subject's
     fresh grant: a new root with a new `id`, keeping its action keys (§7, rule 3).
   - The new root's limits are the budget that grant states, with no counts carried forward. The
     subject sees the consumed counts when granting.
4. **Patterns in `tools`.** None; exact names only. A changed tool list already requires
   re-approval (ADR-0027), and so does a changed scope.
5. **Software identity.** Bound, host-attested, and compared with the current inventory entry. An
   upgrade needs new delegations. Measured attestation of the running bytes is out of scope for
   `0.5.0`.
6. **Is a sub-agent its own principal?**
   - A child that runs the same `act.software` as its parent may act under its parent's
     `act.agent`, with a narrowed link the parent's actor requests.
   - A child of other software is a registered principal of its own, and needs the subject's grant.
   - "In the same run" is not a condition, since the statement binds no run.
7. **Chains across hosts.** Refused; every link has one `host`.
8. **Sender-constrained credentials.**
   - Required for every chain that admits `propose` or `act` anywhere, under RFC 9449 or RFC 8705.
   - A bearer credential is accepted only for read-only chains, by operator choice, and posture
     reports it.
   - Every credential lives at most 5 minutes (§2, *The credential*), and the text there argues
     for both rules.
9. **A key presented under another scope.**
   - Refused as `action-key-scope-conflict` only when the existing reservation's scope has the same
     subject (`kind`, `issuer` and `subject`). Under another subject, the scopes are independent.
   - Receipts publish `action.delivery.key`, and ADR-0025's keys are derived from predictable
     inputs. A global refusal would let another principal pre-reserve a key and block a run, so it
     is not proposed, and the gateway does not rely on how keys are derived.
10. **Admission read and caching.**
    - A synchronous admission read at every admission, with no cache. Unreachable means refused.
    - A bounded cache would weaken "at once" to "within the bound", and is not proposed for `0.5.0`.
11. **A person's agent through a connection a service owns.**
    - `sub` stays the person. The call needs the person's own standing on that connection in the
      issuing host's authorization model (step 12).
    - Removing the person revokes the delegation by §4, rule 2.
    - The receipt's `caller` names the person.
12. **Requests on an action key after revocation.** Permitted, resolved by key and limited to
    retained evidence or the declared read-back. The sender is always authenticated against the
    reservation's scope, by §4, rule 4's table: after revocation, the subject's own token with a
    standing read answering `current`, the issuing host or the gateway's operator. Before
    revocation, the actor's credential reaches a key only when every link's scope has the action's
    write source and tool, and runs its read-back only when every link's scope also has the
    read-back's source and tool.
    A read-back through a revoked or quarantined grant does not run, and the outcome stays
    `unknown` (§5, rule 5). The read-back's `caller` is the reservation's subject
    pair, and `reconciler` names the sender. It dispatches no mutation and counts against no limit.
13. **Revoke or quarantine on owner removal, when the operator configured neither.** Revoke.
14. **Idle expiry.** Absent (`null`) by default. Posture reports a grant unused for 90 days as idle.
15. **Publisher trust.** Report only; refusal is an operator policy.
16. **The normative home.** The statement, its narrowing check and its verification would go in a
    companion document beside Core, with its vectors. The receipt member, key scope and grant
    would go in the gateway's `SPEC.md`. Records and the lease version would go in the agent's
    contract. None of this is committed for `0.5.0`.
17. **Clock skew between the issuing host and an enforcing host.**
    - The allowance is zero: the issuing host back-dates `issuedAt` by at most 5 seconds when it
      issues a link, and enforcing hosts allow no further skew.
    - A child's back-dated `issuedAt` is clamped to its parent's `issuedAt`, so clause 5 holds.
    - Expiry gets no allowance. The issuing host also checks `expiresAt` against its own clock in
      every admission read (§2), so an enforcing host whose clock runs slow does not admit past
      expiry.
18. **Compromise of the issuing host's key.**
    - A signed key-revocation statement names a `keyId`. It revokes every delegation that key
      signed, and every chain through one.
    - Enforcing hosts revoke every credential bound to those chains.
    - Recovery is a new key, pinned out of band, and new grants. A continuity statement from a
      compromised key is not followed.
19. **The inventory's own integrity.** Registrations, entry changes and revocations are appended to
    a log the issuing host keeps. Each entry names the principal and the time, and the Desk shows
    it beside the inventory. Signing that log is not proposed for `0.5.0`.
20. **The form of a revocation record.** A signed revocation statement under its own prefix,
    `"judgment-pack/delegation-revocation/1:"`. Its members are:
    - `revoked`: a tagged form, one of `{"kind": "delegation", "id": opaque identifier}`,
      `{"kind": "agent", "agent": opaque identifier}`, `{"kind": "principal", "principal":
      principal reference}` or `{"kind": "key", "keyId": key identifier}`. Three of the four
      identifiers share one lexical form, so the tag, not the value, says what is revoked;
    - `host`, `keyId`, `revokedBy` (a principal reference), `revokedAt`, and `signature`.

    An offline reader given these statements can establish revocation at an instant.
21. **Size caps.** At most 65536 bytes per statement in `canon`, 256 entries, 256 tools per entry,
    and 16 limits per entry.
22. **What a departed person's removal reaches, beside desk #679.**
    - Desk #679 says "revoke or quarantine every connection and delegation they authorized". This
      record revokes the person's delegations, and every chain below them. It revokes or
      quarantines the grants the person owns.
    - It never quarantines a delegation: a suspended authority whose subject is gone has no one to
      answer for it.
    - Agents the person registered stay registered, with no delegations of the person's left. The
      operator reassigns their `registeredBy`, or revokes them.
    - The proposal is that desk #679 adopt this reading. Until it does, the difference is recorded
      here.
23. **ES256 for the issuing host** (amendment of 2026-11-22). As §2 proposes: `alg` inside the
    signed bytes, `delegationVersion` `"1"` kept, and the algorithm chosen per link.
24. **The library's descriptor digest.** The library's approval of a tool records the per-tool
    descriptor digest by the gateway's definition (§2a). Until it does, its reads carry `version`
    `null`.
25. **A `null` in a version `"2"` read.** The issuing host admits a `null` `version`, and a gateway
    read's `null` `skills`, by default, and judges skills on the library's reads. A host whose
    policy refuses them refuses every such call, and says so where it states its policy.
26. **How a sender learns the host's read version.** By configuration, set by the operator from
    the issuing host's published contract (§2a). A machine-readable statement of the versions a
    host reads could replace it later. It would never be a per-read negotiation.
27. **Which scope identifiers an issuing host's delegations may bind.** The enforcing host's
    configuration names them for each issuing host, none by default, so a binding is opted into per
    host and a scope identifier is never implied. At the reference gateway that is a member of the
    host's entry in `delegation.hosts` (gateway §11.2), in a form the gateway states.

**Review standing.** This Draft does not mark the public comment period complete. The maintainer
authorized a departure from [RFC 0009](0009-interim-review-regime.md)'s cross-vendor review
requirement for this Draft: the adversarial review and its re-reads are by Anthropic Claude Opus
5.5, the model that also drafted it. `GOVERNANCE.md` defines no exception mechanism; this is
recorded as a departure and is not RFC 0009 cross-vendor compliance. The normative text proposed
for Spec 0.5.0 requires a cross-vendor review before adoption.
The amendment of 2026-11-09 (#284) closes the confirmation review's five LOW findings; its review
is same-vendor as well, is recorded on its pull request, and is not RFC 0009 cross-vendor
compliance either.
The amendment of 2026-11-22 has had no review at this commit. It materially amends this record, so
under RFC 0000 its pull request carries a recorded review with a written disposition for each
finding: by a model from another vendor, or under a waiver the maintainer records. A review by the
drafting vendor's model is same vendor, not a cross-vendor claim.

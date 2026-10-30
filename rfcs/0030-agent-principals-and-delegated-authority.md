# RFC 0030: Agent principals and delegated authority

- Status: Draft
- Type: Mixed. The delegation statement (its members, canonical form, signing, narrowing check and verification steps) is **standards track at draft maturity**, proposed for a companion document beside Core. Everything else — the agent's run admission and records, the gateway's credentials, receipt member, action keys and connection grants, and the Desk's inventories — is an **exploratory cross-project record** outside JPS.
- Created: 2026-10-30
- Target: proposed for Spec `0.5.0`. This Draft is carried in Spec `0.4.0`, is normative for nothing, and pre-commits nothing for `0.5.0`.
- Issue: [#280](https://github.com/Judgment-Pack/judgment-pack-spec/issues/280)

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **Scope note, load-bearing.** This record has two parts, and RFC 0000 treats them differently.
>
> *The standards-track part* is the delegation statement of §§2–3: its members, its canonical form
> and signing, the narrowing check and the verification steps. Independent parties must agree on
> it byte for byte, so it is proposed for a companion document beside Core. It owes RFC 0000's
> standards-track bar, including two independent implementations and conformance cases. Neither
> exists yet (see Implementation), so it can reach no status beyond Draft until they do. It
> changes nothing in Core.
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
- **Signature.** An Ed25519 signature (RFC 8032): 64 bytes, written as exactly 128 lowercase
  hexadecimal characters. It is made over a context prefix followed by `canon` of the object, with
  the object's top-level `signature` member removed and every other member retained, as gateway
  §1.2a signs a receipt. Keys and signatures are held to gateway §8.4 by reference:
  - a pinned key is refused when it is not canonical, of small order, or not on the curve;
  - a signature verifies by the cofactorless equation with `S` below the group order;
  - the cofactored check is not used.

  Since a statement's digest covers its signature, two implementations that disagree on an edge
  signature also disagree on every chain digest that includes it.
- **Key identifier.** `keyId` is derived as gateway §1.2 derives one: the first 32 characters of the
  lowercase hexadecimal SHA-256 of the 32-byte public key.
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

**Members** (delegation version 1). Every member is required; a nullable member is present as
`null`, never absent.

| Member | Form | Meaning |
| --- | --- | --- |
| `delegationVersion` | the **string** `"1"` | |
| `id` | opaque identifier | assigned by the issuing host; never reused |
| `host` | flat token | the issuing host |
| `keyId` | key identifier | the issuing host's signing key |
| `sub` | principal reference | the subject |
| `act` | `{"agent": opaque identifier, "software": as in §1}` | the actor and its bound software identity |
| `scope` | object, below | what the actor may do |
| `mayDelegate` | `true` or `false` | whether a child link may be issued below this one (§3) |
| `issuedAt` | time | |
| `expiresAt` | time | strictly later than `issuedAt` |
| `parent` | `null`, or `{"id": opaque identifier, "digest": digest}` | `null` for a root; otherwise the link this one is narrowed from |
| `depth` | integer | `0` for a root; the parent's `depth` plus one otherwise |
| `signature` | signature | |

**Scope.** `scope` is `{"sources": [entry, ...]}`, at least one entry. Entries are ordered by
`audience.kind`, then `audience.name`, then `source`, each by code point, and no pair of `audience`
and `source` repeats. An entry is:

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
under the issuing host's key. It is made over the prefix `"judgment-pack/delegation/1:"` followed by
`canon` of the statement, with the top-level `signature` removed and every other member retained.
- Appending a member anywhere invalidates the signature.
- The prefix carries the version. It domain-separates a delegation from a receipt, a seal, a
  witness statement and a continuity statement, none of whose prefixes it shares.
- The statement's **digest** is `"sha256:"` + hex of SHA-256 over `canon` of the whole statement,
  `signature` included. A child, a receipt and a run record name the statement by its digest.
- The statement is at most 65536 bytes in `canon`, with at most 256 entries, at most 256 tools
  per entry and at most 16 limits per entry (open question 21).

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
to the issuing host. It names the chain's digests, the call's audience, source, tool and effect,
and whether this dispatch is to be counted. The issuing host answers `admit`, or the first refusal
of steps 8 to 12. On `admit` with counting set, it has already incremented the counters. Three
checks are the issuing host's own:
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
| 3 | `malformed` | a link violates any structural constraint of version 1 above: a member missing, of another type or form, an array out of order or with a repeat, `expiresAt` not after `issuedAt`, `parent` and `depth` inconsistent, or over a size cap |
| 4 | `key-mismatch` | a link's `keyId` is not a key the verifier pinned for its `host`, or reached by a rotation it followed (open question 1) |
| 5 | `signature-mismatch` | a link's signature does not verify over the input above, under gateway §8.4's rules |
| 6 | `chain-broken` | §3's clauses 0 to 3 fail |
| 7 | `widened` | §3's clauses 4 to 8 fail |
| 8 | `not-yet-valid`, then `expired` | at the enforcing host's authoritative time t, some link has t < `issuedAt` minus the skew allowance (open question 17), or t ≥ `expiresAt` |
| 9 | `agent-unregistered`, then `software-mismatch` | some link's `act.agent` is not `active` in the inventory of `host`; or some link's `act.software` differs from its own actor's current inventory entry; or the **leaf's** `act.software` differs from the software bound to the credential |
| 10 | `not-issued`, then `revoked` | the issuing host has no record of issuing some link; or some link is revoked, some link's actor is revoked, or the subject has been removed from the host (§4) |
| 11 | `out-of-scope` | the call is not within the scope of some link. The refusal names the first failing reason, in the order `source`, `tool`, `effect`, `limit-unknown`, `limit` |
| 12 | `subject-mismatch`, then `subject-unauthorized` | the source's declared identity is a person other than `sub` (§7, rule 1), or the call is outside what the subject itself may do on the issuing host now, the subject's standing on a service's or a connection's credential included |

Steps 1 to 7 depend only on the bytes and a pinned key, so any party can repeat them later. Steps 0
and 8 to 12 depend on the enforcing host's credential bindings and time, and on the issuing host's
state. They are admission checks. An enforcing host that cannot establish the state a step needs
refuses rather than admitting. Clock uncertainty closes admission, as ADR-0025 closes dispatch on
unavailable ownership evidence.

Some refusals are not verification steps, and they sit outside this table:
- `principal-changed` is a fence check (§7, rule 2), made with the lease at the same admission and
  before step 0;
- `action-key-unauthenticated` and `action-key-scope-conflict` come from the gateway's action-key
  lookup (§4, rule 4; §7, rule 3), made before the counting admission read;
- `not-parent-actor` and `delegation-not-permitted` are issuance refusals (§3).

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
for each child `C = Lk` and its parent `P = L(k−1)`, `k ≥ 1`, clauses 1 to 8 hold:

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
8. `P.mayDelegate` is `true`: a child exists only below a link that permits one.

Clauses 0 to 3 failing is `chain-broken`; clauses 4 to 8 failing is `widened`. Equality is of
`canon` bytes. The check is pairwise, and by transitivity a link is never wider than any ancestor.
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
   reservation's scope. Only these senders are accepted:

   | Sender | Authenticated by | Before revocation | After revocation |
   | --- | --- | --- | --- |
   | the run's actor | a live credential bound to a chain whose `sub` and root actor equal the reservation's: step 0 and steps 1 to 7 applied, and steps 8 to 12 not, since nothing new is admitted | accepted | not possible: no live credential exists |
   | the subject | its own token, whose verified issuer and subject equal the reservation's `sub` | accepted | accepted, unless the subject has been removed |
   | the issuing host | authenticated as the reservation's issuing host, acting for the run | accepted | accepted |
   | the gateway's operator | the gateway's own operator authentication | accepted | accepted |

   Any other sender, a bare key, or a credential bound to another scope is refused as
   `action-key-unauthenticated`, and the refusal discloses nothing about the reservation.
   - **What an authenticated sender gets.** Retained evidence or the declared read-back. Only the
     actor's live credential can reach a freed attempt, and that attempt is a dispatch: it makes
     the counting admission read like any other. After revocation, no sender reaches a freed
     attempt or any dispatch.
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
   grant, whatever delegation it comes under. Delegations whose `sub` is the removed owner are
   revoked by rule 2. Other delegations are unchanged, since they name sources, not grants.
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
| `owner` | principal reference | the person or service that authorized the grant and answers for it |
| `ownerHost` | flat token | the issuing host that holds the owner's standing |
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
   - Pending action keys follow reconciliation (§4, rule 4).

   **How the gateway learns of the removal: a read at each use.** Before every use of a grant —
   delegated or not — the gateway learns the owner's standing from `ownerHost`.
   - For a delegated call, the admission read (§2) carries the grant's owner, and the issuing host
     answers the owner's standing with the rest. Where `ownerHost` is another host, the gateway
     makes a separate owner read to it.
   - For an undelegated call, which makes no admission read, the gateway makes an **owner read**:
     an authenticated, synchronous request to `ownerHost` asking whether the owner is a current
     principal.
   - An owner that has been removed is refused (`owner-removed`) and rule 5 is applied to the grant.
     A missing, late or unreadable answer is refused (`owner-unknown`).
   - A grant never used after its owner's removal is caught at its next use, at its idle expiry
     (rule 4), or by the operator's periodic owner read.

   Why a read and not a notification: a notification event that the issuing host sends on removal
   can be late or lost. It would need a delivery guarantee the project does not offer: ADR-0025
   puts notification delivery guarantees out of the package's scope. Until it arrived, the gateway
   would keep admitting. A read at each use fails closed, reuses the synchronous admission read
   that delegated calls already make, and needs no new delivery contract. Its cost is one
   synchronous read on undelegated calls through an owned grant. A gateway may still act early on
   a removal it is told about, but such a message never admits anything. A grant whose record has
   no owner, as before gateway #357, is used as today.
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
- **Spec.** Nothing in Core `0.3.0`, its schema, corpus or released artifacts changes. Spec `0.4.0`
  carries this Draft and no normative text.

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
  - a request answered from retained evidence, and one refused at the key lookup, neither counted;
    a check before an approval pause not counted, and the dispatch after it counted once.
- **Connection grants:**
  - excess scope, refused and, where the provider cannot narrow, reported;
  - drift, and unused scopes listed;
  - idle expiry at equal time;
  - owner removal revoking and quarantining, and reassignment with and without acceptance;
  - an undelegated call after the owner's removal (`owner-removed`), and with the owner read
    unanswered (`owner-unknown`);
  - a provider without revocation, reporting `provider-grant-may-persist`;
  - a lapsed publisher, and a name lookalike.
- **Agent records:**
  - `principal` on each record kind;
  - an older reader refusing the new version, and a run without delegation writing the current
    version unchanged;
  - a child's narrowed chain recorded;
  - a refused attempt to widen.

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

All of these are plausible routes, written by one maintainer with same-vendor assistance. None is
independent organizational interoperability evidence, and none is built. The standards-track part
cannot leave Draft on them alone.

## Unresolved questions

Each has a proposed default. A default is a proposal for review, not a decision taken for `0.5.0`.

1. **Who signs a delegation, and how its key rotates.**
   - The issuing host signs, with an Ed25519 key pinned by `keyId`. Subject-held keys are not
     required.
   - Rotation uses a continuity statement modelled on gateway §3b, under its own prefix,
     `"judgment-pack/delegation-rotation/1:"`.
   - The host publishes it in a registry file of its own, which verifiers read as §3b's reader
     reads the gateway's registry.
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
    reservation's scope, by §4, rule 4's table: after revocation, the subject's own token, the
    issuing host or the gateway's operator. The read-back's `caller` is the reservation's subject
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

**Review standing.** This Draft does not mark the public comment period complete. The maintainer
authorized a departure from [RFC 0009](0009-interim-review-regime.md)'s cross-vendor review
requirement for this Draft: the adversarial review and its re-reads are by Anthropic Claude Opus
5.5, the model that also drafted it. `GOVERNANCE.md` defines no exception mechanism; this is
recorded as a departure and is not RFC 0009 cross-vendor compliance. The normative text proposed
for Spec 0.5.0 requires a cross-vendor review before adoption.

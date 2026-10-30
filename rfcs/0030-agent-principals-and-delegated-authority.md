# RFC 0030: Agent principals and delegated authority

- Status: Draft
- Type: Exploratory (a cross-project record: the agent's run admission and records, the gateway's per-delegation credentials, receipts, action keys and connection grants, and the Desk's inventories; outside JPS Core)
- Created: 2026-10-30
- Target: normative text in Spec `0.5.0`; nothing in Spec `0.4.0` is normative for it
- Issue: [#280](https://github.com/Judgment-Pack/judgment-pack-spec/issues/280)

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **Scope note, load-bearing.** Nothing this Draft proposes lands in JPS Core, a profile or a
> conformance class, and it claims none. It is recorded under RFC 0000's cross-project
> exploratory provision, and its parts would land as follows. The delegation statement, its
> canonical form, its narrowing check and its verification steps are a format that independent
> parties must agree on: they are proposed for a companion document beside Core in Spec `0.5.0`.
> The receipt member and the action-key scope land in the
> [reference gateway's](https://github.com/Judgment-Pack/judgment-pack-gateway) `SPEC.md`
> (§1.2a, §1.2b, §1.4), with the connection grant in its design notes and posture; the run's
> carried principal, its admission refusals and its record members land in the
> [agent harness's](https://github.com/Judgment-Pack/judgment-pack-agent) contract and decision
> records; the inventories and the revoke actions land in the
> [Desk](https://github.com/Judgment-Pack/judgment-pack-desk). Each repository decides its own
> adoption by its own process. The implementation rows that build against this Draft are
> agent #260, gateway #356 and #357, and desk #679. Implementations may build against it; where
> they do, they build against a Draft, and the normative text may differ.

## Summary

An agent that reaches a system with a person's own credentials is indistinguishable from that
person. It has no identity of its own, nothing records on whose behalf it acted or within what
limits, its access is the person's whole access, and it cannot be stopped without stopping the
person. This record proposes the missing model in seven parts:

1. an **agent principal**: a registered, non-human principal with a stable identifier, the host
   that registered it and its software identity; an unregistered agent cannot act;
2. a **delegation**: a signed, bounded statement that a subject (a person or a service) authorizes
   an actor (an agent principal) for a scope until an expiry, with the subject and actor semantics
   of OAuth 2.0 Token Exchange (RFC 8693);
3. **chained delegation**, in which each link narrows scope and expiry and never widens them, by an
   exact check, and the chain is recorded;
4. **revocation** that stops new calls at once and leaves the subject's own access untouched, with
   effects in flight left to the existing uncertain-action rules;
5. the **connection grant** behind each gateway connection as a principal-held resource, with an
   owner, least-privilege scopes, a record of granted against used scopes, an owner and idle
   lifecycle, and publisher trust for customer MCP servers; revocation on the owner's removal is
   normative;
6. **recording**: receipts and run records name the actor, the subject and the delegation, while a
   reader that predates this sees the existing caller identity unchanged, by an exact rule;
7. its **relation to existing contracts**: the per-call identity of agent #102 becomes the subject,
   run leases bound time while delegations bound authority, and action keys are scoped to subject
   and actor so that a lease takeover cannot reopen them.

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
ADR-0019 is explicit that its identity "is reported, never a grant": it labels whose credential a
call runs under, and grants nothing. A gateway `caller` proves who asked at the gateway's boundary,
and when an agent presents a person's token, the caller is the person. So today:

- an audit cannot tell an agent's call from the person's own;
- an agent's reach is whatever its credential reaches, not a narrowed share of it;
- a child agent receives its parent's whole reach, and nothing records that it was a child;
- stopping an agent means revoking the person's credential, which stops the person as well;
- the standing grant behind a connection outlives its use and its owner, with nobody recorded as
  answerable for it.

There is also a concrete defect this model must close. The gateway scopes an action key to the
authenticated issuer and subject (§1.2b). ADR-0025's idempotency identity carries no principal, so
that a takeover by a new lease owner never replays an effect. When a takeover authenticates as a
different transport subject, the gateway sees a new key scope and sends the write again
(gateway #352, finding M6).

## Evidence

What exists, and what it shows:

1. **The per-call identity, built.** ADR-0019 (agent v0.8.0) puts `identity: {kind, label}` on the
   source record, with `kind` one of `person`, `service` or `connection`, carries it on every
   `tool_call` and `tool_result`, counts calls per identity, withholds a source whose identity
   changes mid-run, and always asks the first `act` under a `service` identity. The model never
   chooses an identity. What it does not have is a principal for the agent: the identity names the
   credential, not the party using it.
2. **The caller identity, built.** Gateway receipt version 3 records `caller` as
   `{issuer, subject, tokenDigest}` from a verified token, or `null` where no issuer is configured,
   and an action's `requester` in the same form, never `null`. Both are signed with every other
   member. A version 3 verifier tolerates a signed member it does not know: `witness`,
   `tool.transport` and `decision.recordBytes` were each added that way, and the specification says
   of each that a verifier written before it "tolerates it, as it tolerates any signed member it
   does not know" (§1.2a). That is the precedent the compatibility rule below follows.
3. **Leases and the fence, built.** ADR-0025 decision 1, as amended for agent #223, defines the
   lease (`owner`, `expiry`, `epoch`, `state`), the fence `{resource, owner, epoch}` presented at
   every commit and admission, and an idempotency identity `{run, operation, source, tool,
   requestDigest}` with no epoch. It states that "a lease grants neither tool permission nor
   approval". Time is bounded; authority is not.
4. **Action keys and uncertain delivery, specified.** Gateway §1.2b defines `action.delivery`
   (`response` or `uncertain`), reconciliation by a declared read-back that reports `committed` or
   `unknown`, and the rule that neither permits another dispatch of the mutation. Its action key is
   scoped to "gateway authority, authenticated issuer and subject".
5. **The takeover defect, observed.** The different-vendor review of gateway #351 recorded a probe
   (P4c) in which a takeover authenticating as a different subject produced two mutations of one
   operation. Gateway #352 asks for either a run-level owner that survives takeover, or a takeover
   that presents the original subject's delegation. This record proposes the second, refined.
6. **Effect classes, built.** ADR-0027 fixes the effects `pure`, `read`, `read-external`, `propose`
   and `act`, in that strength order, declared by a tool's owner and never by the model. A scope
   can therefore name effect classes by a closed vocabulary that already exists.
7. **Nothing of this model is built.** Agent #260, gateway #356 and #357, and desk #679 are filed
   against this Draft and open.

## Specification (sketch)

The key words below are used in their ordinary sense. This is a Draft: the text is precise so that
an implementation can build against it, but it is normative for nothing until a later version
lands.

### Common forms

- **Canonical form.** Every signed or digested object in this record is serialized by `canon`, the
  canonical form of gateway `SPEC.md` §1.1: integers only, duplicate member names refused, member
  names ordered by Unicode code point, compact, raw UTF-8. It is not RFC 8785, whose name order
  differs outside the Basic Multilingual Plane; an implementation reaching for an RFC 8785 package
  gets that case wrong.
- **Signature.** Ed25519 (RFC 8032), 64 bytes, written as exactly 128 lowercase hexadecimal
  characters, over a context prefix followed by `canon` of the object with its top-level
  `signature` member removed and every other member retained, as gateway §1.2a signs a receipt.
- **Key identifier.** `keyId` is derived as gateway §1.2 derives one: the first 32 characters of the
  lowercase hexadecimal SHA-256 of the 32-byte public key.
- **Digest.** `"sha256:"` followed by exactly 64 lowercase hexadecimal characters, as gateway §1.2a.
- **Time.** An RFC 3339 UTC timestamp with exactly millisecond precision,
  `YYYY-MM-DDTHH:MM:SS.sssZ`, the form ADR-0025's lease amendment fixes for a lease expiry. Two
  times of this form compare by their characters. An instant equal to an expiry is expired, as for
  a lease.
- **Identifier.** An **opaque identifier** is exactly 32 lowercase hexadecimal characters drawn from
  at least 128 random bits. A **flat token** is `[A-Za-z0-9._-]{1,128}`, never `.` or `..`, as
  gateway §3a.
- **Principal reference.** A person or service is named by
  `{"kind": "person" | "service", "issuer": string, "subject": string}`: the issuer and subject of
  the identity the host verified for it, the same pair gateway §1.2a records in `caller`. It carries
  no token, no token digest and no display label.

### 1. The agent principal

An agent principal is a principal distinct from every person and every service. A host registers
it in its **agent inventory** before it can act. An inventory entry has these members:

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
   (§2), and only through a credential minted or derived for that delegation (gateway #356).
2. A delegation whose actor is not an `active` entry of the issuing host's inventory admits nothing:
   the refusal is `agent-unregistered`. A host that keeps no inventory admits no agent call.
3. The software identity is part of the actor. A delegation binds the actor's `software` as it
   stood at issuance (§2); a call presented by software other than the bound identity is refused as
   `software-mismatch`. A software upgrade updates the inventory entry and requires new delegations
   (open question 5).
4. Revoking the entry (`state` → `revoked`) revokes every delegation whose actor it is (§4).
5. The `label` is shown, never trusted, as ADR-0019's label is.

### 2. The delegation

A delegation is a signed, bounded statement: subject P authorizes actor A, for scope S, until
expiry E. It is revocable by P, by the issuing host, and, for a link of a chain, by the actor of the
link it was narrowed from (§3, §4). Its semantics are those of OAuth 2.0 Token Exchange (RFC 8693):
the subject (`sub`) is the principal on whose behalf the call is made, and the actor (`act`) is the
party making it. This is RFC 8693's *delegation* case, never its *impersonation* case: an agent's
call is never presented to a reader of this model as the subject's alone. The statement is the
host's record of the authorization that RFC 8693 expresses with its `may_act` claim; a credential
the gateway mints for it may be an RFC 8693 issued token, and this record does not require one.

**The statement is not a credential.** Holding its bytes grants nothing. It is evidence that the
host recorded an authorization; authority is exercised only through a credential an enforcing host
binds to it, and is checked at every admission (verification steps 6 to 10).

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
| `issuedAt` | time | |
| `expiresAt` | time | strictly later than `issuedAt` |
| `parent` | `null`, or `{"id": opaque identifier, "digest": digest}` | `null` for a root; otherwise the link this one is narrowed from |
| `depth` | integer | `0` for a root; the parent's `depth` plus one otherwise |
| `signature` | signature | |

**Scope.** `scope` is `{"sources": [entry, ...]}`, at least one entry, ordered by `source` by code
point with no `source` repeated. An entry is:

| Member | Form | Meaning |
| --- | --- | --- |
| `source` | string | a source as the enforcing host names it: the gateway's `source` (for example `<platform>/live` or `<platform>/write`), the agent's source record identifier for a host source |
| `tools` | array of strings, at least one, ordered by code point, no repeats | the exact tool names admitted; no pattern, prefix or wildcard (open question 4) |
| `effects` | array, at least one, of `"pure"`, `"read"`, `"read-external"`, `"propose"`, `"act"`, in that order, no repeats | the effect classes admitted, in ADR-0027's vocabulary |
| `limits` | object of limit name to non-negative integer; may be empty | resource limits, where the source has them |

A **limit name** is either `calls` — the number of calls admitted under the link for that source —
or a name the source itself declares, `x-` followed by a flat token. A source may declare a limit
only when it can enforce it **before dispatch** (a row bound passed to a query, a size bound passed
to a request); a limit checked only after the result arrives is not a scope limit. An enforcing
host that does not know a limit name in an entry refuses every call to that entry's source as
`limit-unknown`.

A call is **within the scope** of a link exactly when an entry has the call's `source`, the call's
tool is in its `tools`, the tool's declared effect — the owner's ADR-0027 declaration as admitted,
never a model argument or a label — is in its `effects`, and every limit of the entry holds: for
`calls`, the count after admitting the call does not exceed it; for a source-declared limit, the
request is bounded within it, as the source declares, before dispatch. An admitted call increments
the counters of **every** link of its chain, so a child's calls count against its ancestors' limits.

**Canonical form and signing.** The statement is serialized by `canon`. Its signature is Ed25519
under the issuing host's key over the prefix `"judgment-pack/delegation/1:"` followed by `canon` of
the statement with the top-level `signature` removed and every other member retained. Appending a
member anywhere invalidates it. The prefix carries the version, and domain-separates a delegation
from a receipt, a seal, a witness statement and a continuity statement, none of whose prefixes it
shares. The statement's **digest** is `"sha256:"` + hex of SHA-256 over `canon` of the whole
statement, `signature` included; it is how a child, a receipt and a run record name the statement.

**Issuance.** The host issues a root only on the subject's authenticated grant, and refuses one
whose scope exceeds what the subject itself may do on that host when it is issued
(`subject-unauthorized`). A person cannot grant an agent more than the person holds; a policy can
grant an agent less (desk #679).

**Verification steps.** A verifier is handed the chain, root first, ending with the link the call
claims, and the call. It takes the first failure:

| Step | Refusal | Condition |
| --- | --- | --- |
| 1 | `malformed` | any link violates a structural constraint above: a member missing, of another type or form, an array out of order or with a repeat, a value outside the `canon` domain, `parent` and `depth` inconsistent with each other |
| 2 | `unsupported-version` | `delegationVersion` is not `"1"` |
| 3 | `key-mismatch` | a link's `keyId` is not a key the verifier pinned for its `host` |
| 4 | `signature-mismatch` | a link's signature does not verify over the input above |
| 5 | `chain-broken` or `widened` | the chain does not satisfy §3's check: `chain-broken` for clauses 1 to 3, `widened` for clauses 4 to 7 |
| 6 | `not-yet-valid` or `expired` | at the enforcing host's authoritative time t, some link has t < `issuedAt`, or t ≥ `expiresAt` |
| 7 | `agent-unregistered` or `software-mismatch` | the leaf's `act.agent` is not `active` in the inventory of `host`, or the presenting software is not `act.software` |
| 8 | `revoked` | some link, its actor, or its subject's standing on the host is revoked (§4) |
| 9 | `out-of-scope` | the call is not within the scope of every link; the refusal names which of `source`, `tool`, `effect` or `limit` failed first, in that order |
| 10 | `subject-unauthorized` | the call is outside what the subject itself may do on the host now |

Steps 1 to 5 depend only on the bytes and a pinned key: any party can repeat them later. Steps 6 to
10 depend on the enforcing host's time, inventory, revocation state and authorization model; they
are admission checks, made before dispatch, and an enforcing host that cannot establish the state a
step needs refuses rather than admitting. Clock uncertainty closes admission, as ADR-0025 closes
dispatch on unavailable ownership evidence.

### 3. Chained delegation

An actor may ask the host to issue a child link to another actor — a child agent of the delegation
coordinator (agent #217) or another registered agent. The host issues it under the same rules as a
root, and the chain is recorded: each child names its parent by `id` and digest, and every record of
a call names the whole chain (§6).

**The narrowing check.** A chain `L0, …, Ln` (root first) is valid exactly when `L0.parent` is
`null`, `L0.depth` is `0`, and for each child `C = Lk` and its parent `P = L(k−1)`, `k ≥ 1`:

1. `C.parent.id` equals `P.id`, and `C.parent.digest` equals the digest of `P`;
2. `C.depth` equals `P.depth + 1`, and `C.depth` does not exceed the maximum depth (open question 3);
3. `C.host` equals `P.host` (open question 7);
4. `C.sub` equals `P.sub`, member for member — the subject never changes along a chain;
5. `C.issuedAt` ≥ `P.issuedAt`, and `C.expiresAt` ≤ `P.expiresAt`;
6. for every entry `e` of `C.scope.sources` there is an entry `p` of `P.scope.sources` with
   `p.source` equal to `e.source`, and `e.tools` ⊆ `p.tools`, and `e.effects` ⊆ `p.effects`;
7. for that same pair, every limit name of `p.limits` is a limit name of `e.limits` with
   `e.limits[name]` ≤ `p.limits[name]`; `e.limits` may add names `p.limits` does not have.

Clauses 1 to 3 failing is `chain-broken`; clauses 4 to 7 failing is `widened`. Equality is of
`canon` bytes. The check is pairwise, and by transitivity a link is never wider than any ancestor.
A host refuses to issue a child that would fail it, and every verifier checks it again: issuance is
not evidence that the check was made.

### 4. Revocation

A **revocation** names a delegation `id`, or an agent principal, and is recorded by the issuing
host with the revoking principal and its time. Who may revoke: for a delegation, its subject, the
issuing host, and, for a child, the actor of its parent; for an agent principal, the host, and the
principal that registered it.

1. **Effect on new calls.** A revocation takes effect at the instant the host records it durably.
   From then, verification step 8 refuses every call presented under the revoked link and every link
   below it in any chain, and under every delegation whose actor is a revoked agent principal. An
   enforcing host consults the authoritative revocation state at each admission; it does not admit
   from a cached "not revoked" (open question 10). A credential minted or derived for a revoked
   delegation (gateway #356) is revoked with it. The host acknowledges a revocation to the revoker
   only after every enforcing host it delegated enforcement to has recorded it, or has had the
   delegation's credential revoked.
2. **The subject's own access is untouched.** A revocation names a delegation or an agent. It never
   revokes, rotates or invalidates a session, token, credential or connection grant of the subject,
   and it never changes the subject's authorization. The one interaction is the reverse one:
   removing a principal from the host revokes every delegation whose `sub` it is, and the connection
   grants it owns follow §5.
3. **Effects in flight.** A revocation stops admission; it cannot undo a call already admitted. An
   effect admitted before the revocation follows the existing uncertain-action rules unchanged:
   gateway `SPEC.md` §1.2b (an action whose delivery is `uncertain` is reconciled by its declared
   read-back to `committed` or `unknown`, and neither permits another dispatch), and agent ADR-0025
   decision 1 (an in-flight effect "remains unknown until reconciled by its authoritative host";
   takeover never replays it) and decision 4 (re-authorization "is not retry permission"). A
   revocation never turns an uncertain effect into a refused one, and never into a retry. The
   declared read-back that reconciles an action admitted before the revocation is not a new call
   under the delegation and is not refused by it (open question 12).
4. **No restoration.** A revoked delegation is never un-revoked. A new grant is a new statement
   with a new `id`.
5. **Revoking a connection grant's owner.** Removing the owner of a connection grant from the host
   revokes or quarantines that grant (§5, rule 5). The gateway then refuses every call through the
   grant, under whatever delegation it comes; delegations whose `sub` is the removed owner are
   revoked by rule 2, and other delegations are unchanged, since they name sources, not grants.

### 5. The connection grant, a principal-held resource

The standing grant behind a gateway connection — the provider authorization that lets the gateway
reach a mail account, a file store, a source-control host, a work-tracking service, a data
platform or a customer MCP server — is a resource held by a principal. It is distinct from a
delegation: a delegation narrows what one actor may do on a subject's behalf; a grant is what the
gateway holds at all.
A per-delegation credential (gateway #356) is always narrower than the grant it is derived from.

**The grant record** (gateway #357). It carries no credential, no token, no token digest and no
content.

| Member | Form | Meaning |
| --- | --- | --- |
| `connection` | flat token | the gateway's connection |
| `owner` | principal reference | the person or service that authorized the grant and answers for it |
| `scopes.required` | array of strings, ordered, no repeats | the union of the minimum scopes the connection's sources declare per operation |
| `scopes.granted` | array of strings, ordered, no repeats | what the provider granted, as last read |
| `scopes.used` | array of `{"scope": string, "lastUsedAt": time}`, ordered by `scope` | each granted scope that some admitted call exercised, and when last |
| `lastUsedAt` | time or `null` | the last admitted acquisition or action through the connection |
| `idleExpiry` | integer milliseconds, or `null` | the configured idle bound; `null` is none |
| `state` | `"active"`, `"quarantined"` or `"revoked"` | `revoked` is terminal |
| `publisher` | object or `null` | for a customer MCP server, below; `null` otherwise |

**Rules.**

1. **Least privilege at connect.** A connection that requests or holds a scope outside
   `scopes.required` is refused. Where the provider cannot narrow its grant, the connection is
   admitted and reports `excess-scope` with the extra scopes named.
2. **Drift.** Where the provider reports the scopes of a grant, the gateway reads them again on use;
   a scope added since the record was made is reported as `excess-scope` and the record updated.
3. **Granted against used.** A scope is *used* when an admitted call's operation declares it among
   its required scopes; the record says this is derived from declarations, since few providers
   report which scope a call exercised. An operator query lists `granted` minus `used`, the scopes
   to trim.
4. **Idle lifecycle.** A grant with a non-null `idleExpiry` whose `lastUsedAt` (or, never used, its
   creation) is at least `idleExpiry` before the current time is revoked by rule 6. Equal is
   expired.
5. **Owner removal — normative in this model.** Removing the owner principal from the host revokes
   **or** quarantines every grant it owns, as the operator configured (open question 13). A
   quarantined grant admits no call, keeps its credential, and leaves quarantine only by being
   reassigned to a new owner, by that owner's authenticated acceptance, or by being revoked. No
   grant remains `active` with a removed owner. Pending action keys follow reconciliation (§4,
   rule 3).
6. **What revoking a grant does.** The gateway calls the provider's revocation endpoint where it
   offers one (for an OAuth provider, RFC 7009 token revocation), deletes the credential, and sets
   `state` to `revoked`. Where the provider offers no revocation, it deletes the credential and
   reports `provider-grant-may-persist`, since the authorization may still exist at the provider.
7. **Publisher trust for customer MCP.** At registration (gateway #348), `publisher` records
   `{"kind": "registry" | "repository" | "domain", "name": string, "state": "maintained" |
   "unmaintained" | "unknown", "checkedAt": time}`: the server's publisher and its liveness — the
   domain's registration, the repository archived or not, the package deprecated or not. It is
   shown with the approval and checked again on recapture and on a schedule. A lapsed or archived
   publisher reports `publisher-unmaintained`, which an operator policy may make a refusal (open
   question 15). A registration whose display name closely matches a known integration's under a
   different publisher is flagged `name-lookalike`.

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

**The compatibility rule, exact.** Under a delegation:

1. `caller.issuer` and `caller.subject` are `delegation.subject.issuer` and
   `delegation.subject.subject`, and on an action receipt so are `action.requester.issuer` and
   `action.requester.subject`. `tokenDigest` remains the digest of the token presented, which is the
   per-delegation credential. That is, the existing caller identity is the subject's, exactly the
   pair the receipt carried when the agent called with the subject's own token.
2. `caller` is never `null` on a receipt that carries `delegation`.
3. No member of version 3 changes form or meaning, `receiptVersion` stays `"3"`, and the signing
   prefix is unchanged.
4. A call made under no delegation carries no `delegation` member (open question 2), and its
   receipt is byte for byte the receipt it was before this record.

So a verifier written before this record tolerates `delegation` as it tolerates any signed member it
does not know, returns the status it returned before, and reads `caller` and `requester` as naming
the subject — the identity it always read, unchanged. It does not see the actor; that is the bound
of rule 1, and it is the same bound such a reader had when agents used the subject's credential.
A verifier that reads the member holds it to the forms above at §1.4 order 1, and also requires,
as order-1 conditions within the one receipt, rules 1 and 2 above, and `chain` holding at least one
and at most the maximum depth plus one digests. Handed the statements, it may report
`delegation-unresolved` beside `ok`, as gateway §4's steps 5 to 8 report their findings, when a
digest of `chain` resolves to no statement, the chain's length is not the leaf's `depth` plus one,
steps 1 to 5 of §2 fail, the leaf's `id`, `sub` or `act.agent` differ from `id`, `subject` or
`actor`, or `servedAt` is outside the leaf's validity. Revocation at `servedAt` is not established
offline unless a revocation record is also given; the receipt asserts only that the gateway
admitted the call.

**Agent records.** `tool_call`, `tool_result` and the run record carry `principal`:
`{"actor": {"agent", "host", "software"}, "subject": principal reference, "delegation": {"id",
"digest"}, "chain": [digest, ...]}`. The source record's ADR-0019 `identity` keeps its form and its
meaning, the credential kind and label, beside it. These members ship under new record versions per
[ADR-0024](https://github.com/Judgment-Pack/judgment-pack-agent/blob/main/docs/adr/0024-versioned-record-readers.md):
a reader that predates them refuses the new version (`record version unsupported`) before reading
the body, so it never reads an agent's call as the person's; records of the current versions are
unchanged.

**Refusals are recorded.** A call refused at verification is recorded with its refusal name, its
actor and subject where they parsed, and no credential.

**The Desk** shows both principals on runs, receipts and history (desk #679), and records every
delegation, revocation and connection action with who performed it.

### 7. Relation to existing contracts

1. **Agent #102's identity becomes the subject.** ADR-0019's per-source identity was the only
   principal a record named. Under this record, the principal it names is the call's subject: for
   kind `person` or `service`, the principal it declares; for kind `connection`, the owner of the
   connection grant (§5). That principal must equal the delegation's `sub`, or the call is refused
   as `subject-mismatch`. The label stays a display name, and an identity change mid-run is still
   withheld until re-approval. A source whose identity is a service the subject is not — a shared
   connection a service owns — is used by a delegation whose `sub` is that service (open question 11).
2. **Leases bound time; delegations bound authority.** A call needs both a current fence (ADR-0025:
   owner, epoch, expiry, checked at admission) and a valid delegation. Neither stands in for the
   other: renewing a lease renews no delegation, and a new delegation renews no lease. When the
   delegation expires or is revoked while the lease is held, admission refuses, and the run parks
   for re-authorization (ADR-0025 decision 4) naming the delegation, never retrying on its own. A
   worker that acquires a run's lease presents the run's delegation chain; an enforcing host refuses
   a fenced dispatch whose `sub` or root actor (the `act.agent` of `L0`) differs from those the run
   was admitted with, as `principal-changed`. A takeover is a new epoch of the same principals, never
   a change of principal.
3. **Action keys are scoped to subject and actor.** Under a delegation, gateway §1.2b's key scope
   "gateway authority, authenticated issuer and subject" becomes the gateway authority, the chain's
   `sub` (`issuer` and `subject`) and the chain's **root actor**. It excludes the transport token,
   the lease epoch, the worker, and the delegation `id`, so a re-issued delegation for the same run
   keeps its keys. A takeover presents the same subject and root actor, finds the same reservation,
   and is answered from retained evidence, a freed attempt or the declared read-back — never a new
   mutation. This is gateway #352's second option, refined, and it composes with ADR-0025's
   epoch-free idempotency identity, which already binds the run. A call made under no delegation
   keeps the scope §1.2b states today. A key value already reserved under one scope and presented
   under another is refused (open question 9).

## Alternatives

- **No change.** Agents keep using the person's credential. Every problem above stays, and the
  takeover defect needs a separate fix.
- **Each agent as a service identity of its own.** It gives the agent an identity but drops the
  subject: an audit sees a service, not on whose behalf it acted, and the service accumulates a
  standing grant wider than any one person's share. It is ADR-0019's `service` kind, which already
  exists and is not this.
- **Impersonation** (RFC 8693's other case). The agent receives a token that presents as the
  subject. It narrows nothing an audit can see and is exactly the indistinguishability this record
  removes.
- **Provider scopes alone.** OAuth scopes narrow per platform, cannot name the project's effect
  classes or tools, cannot express a chain, and many providers cannot narrow below the grant. The
  gateway enforcing the scope itself where the platform cannot is gateway #356's rule.
- **An attenuable capability token** (macaroon- or biscuit-style chains). Its attenuation is the
  narrowing check this record states. It would add a second canonical form and signing convention
  to a project that has one. The statement here could later be carried in such a token without
  changing the check.
- **Put it in Core.** Core is a pack format; authorization of an agent at an enforcing host is not a
  property of a pack. A companion beside Core is the proposed home of the shared format.

## Compatibility

- **Receipts.** §6's rule: the version stays `"3"`, the new member is signed and tolerated by every
  existing verifier, `caller` and `requester` keep naming the subject, and a receipt made under no
  delegation is unchanged in its bytes. A verifier that knows version 2 alone already refuses
  version 3 and still does.
- **Action keys.** Unchanged for calls made under no delegation. Under one, the scope changes from
  the transport subject to the delegation's subject and root actor; a key reserved before a
  gateway adopts this, under a transport subject, stays in its old scope.
- **Agent records.** New record versions; older readers refuse them by ADR-0024 rather than
  misreading them. ADR-0019's identity member is unchanged in form and meaning.
- **Desk.** No record format of the Desk changes by this record; its authorization model gains a
  kind of principal (desk #612, #452).
- **Spec.** Nothing in Core `0.3.0`, its schema, corpus or released artifacts changes. Spec `0.4.0`
  carries this Draft and no normative text.

## Security and privacy

- **Confused deputy.** Without a subject, an agent's reach is its credential's. The delegation and
  step 10 hold every call to the intersection of the scope and the subject's current authority.
- **Widening along a chain.** The narrowing check is pairwise and repeated by every verifier;
  issuance is not trusted as evidence of it.
- **The statement as a bearer token.** It is not one. Stealing its bytes admits nothing; the
  credential bound to it is the thing to protect, and its theft is bounded by the delegation's
  expiry and revocation. Sender-constraining that credential is open question 8.
- **The issuing host's key.** Its holder can issue any delegation within what it believes the subject
  holds. Verification proves the host signed, not that the subject consented; the host's record of
  the grant is the evidence of that, and it is the host's.
- **Revocation races.** A call admitted an instant before a revocation proceeds and is reconciled,
  never undone or retried. "At once" means at the next admission after the durable record.
- **Clocks.** Expiry is decided by the enforcing host's authoritative time; uncertainty refuses.
- **Disclosure.** A receipt already discloses the subject's issuer and subject in `caller`; the
  new member adds the agent's opaque identifier and the chain's digests, and no label. A grant record
  carries scope names and times, no credential and no content. Publisher checks query public
  registries and domains, which can disclose to those services which servers an operator uses; the
  schedule is the operator's.
- **Resource exhaustion.** Depth and lifetime are bounded (open question 3); scopes are closed lists,
  bounded by the statement's size, which a normative version must cap.
- **Name lookalikes.** The flag is a heuristic; it reports, and refuses only by operator policy.

## Conformance

A Draft claims no conformance class and ships no vectors. A normative version would need at least
these, positive and negative, as hand-written vectors read by two independently written readers:

- **Delegation statement:** a valid root; a valid three-link chain; each structural violation of
  step 1, one per member; an unsupported version; an unpinned key; a signature over a changed member;
  a member appended at the top level and inside `scope`; a member name outside the Basic
  Multilingual Plane, ordered by `canon` and not by RFC 8785.
- **Narrowing:** one vector per clause 1 to 7 failing; a child that adds a limit its parent lacks
  (valid); a child that drops one (widened); equal expiry (valid); later expiry (widened); a changed
  `sub` (widened); depth one past the maximum.
- **Admission:** equal-time expiry; not yet valid; an unregistered actor; a software mismatch; a
  revoked leaf, a revoked ancestor, a revoked agent; each `out-of-scope` reason; a limit counted
  across a chain; an unknown limit name; a subject that has lost the access since issuance.
- **Receipts:** an acquisition and an action under a delegation verified by a reader that knows the
  member and by one written before it, both returning `ok` and the same `caller`; `caller` differing
  from `delegation.subject` (`malformed` for the new reader); a `null` caller with the member; a
  tampered member (`signature-mismatch`); a call under no delegation, byte-identical to the receipt
  before this record; `delegation-unresolved` for each of its causes.
- **Action keys:** a takeover authenticating as another transport subject with the same subject and
  root actor (one mutation, or the outcome stays `unknown`); a re-issued delegation keeping the key;
  a key presented under another scope.
- **Connection grants:** excess scope refused and, where the provider cannot narrow, reported; drift;
  unused scopes listed; idle expiry at equal time; owner removal revoking and quarantining; a
  provider without revocation reporting `provider-grant-may-persist`; a lapsed publisher; a name
  lookalike.
- **Agent records:** `tool_call`, `tool_result` and run record carrying `principal`; an older reader
  refusing the new version; a child's narrowed chain recorded; a refused attempt to widen.

## Implementation

The agent harness carries the chain per run, verifies it before each dispatch, and records
`principal` in TypeScript and Go readers sharing vectors (agent #260). The gateway verifies the chain
at `/acquire` and `/act`, mints or derives the per-delegation credential, writes the receipt member,
scopes action keys, and keeps grant records (gateway #356, #357, #352); its Go verifier and its
TypeScript verifier are the two receipt readers. The Desk issues delegations, keeps the inventories
and performs revocation (desk #679). A second implementation of the statement verifier could be
written from §§2–3 alone, since the forms are those the gateway already specifies. All of these are
plausible routes, by one maintainer with same-vendor assistance; none is independent organizational
interoperability evidence, and none is built.

## Unresolved questions

Each has a proposed default, which the Spec `0.5.0` text adopts unless review says otherwise.

1. **Who signs a delegation?** Default: the issuing host, with an Ed25519 key pinned by `keyId`,
   rotated by a continuity statement of gateway §3b's form. Subject-held keys are not required.
2. **`delegation` absent or `null` when no delegation applies?** Default: absent, so that a receipt
   made under no delegation is unchanged in its bytes. Its absence never proves the caller was not an
   agent; it proves only that no delegation was presented.
3. **Bounds.** Default: a link lives at most 24 hours (`expiresAt − issuedAt`), the lease amendment's
   longest duration; a longer run is re-issued a new root with a new `id`, which keeps its action
   keys (§7, rule 3). Maximum depth 4.
4. **Patterns in `tools`.** Default: none; exact names only. A changed tool list already requires
   re-approval (ADR-0027), and so does a changed scope.
5. **Software identity bound into the delegation.** Default: bound; an upgrade updates the
   inventory entry and needs new delegations.
6. **Is a sub-agent its own principal?** Default: a child that runs the same software in the same run
   may act under its parent's `act.agent` with a narrowed link; a child of other software is a
   registered principal of its own.
7. **Chains across hosts.** Default: refused; every link has one `host`.
8. **Sender-constrained credentials** (RFC 9449 proof of possession, RFC 8705 mutual TLS). Default:
   not required in `0.5.0`; the credential is short-lived to the delegation's expiry and revocable
   alone, and posture states which.
9. **A key presented under another scope.** Default: refused as `action-key-scope-conflict`. Keys
   are digests of run-bound identities, so a collision across scopes means a changed principal, and
   the refusal discloses only that the key exists, to a caller that already holds it.
10. **Caching revocation state.** Default: none; each admission consults the authoritative state,
    and an enforcing host that cannot reach it refuses.
11. **A person's agent through a connection a service owns.** Default: the delegation's `sub` is the
    service, issued by the host under its authorization policy, and the person who started the run
    is recorded on the run, not in the delegation.
12. **The read-back after revocation.** Default: permitted, as the gateway's reconciliation of an
    action admitted before the revocation; it dispatches no mutation and admits no new call.
13. **Revoke or quarantine on owner removal, when the operator configured neither.** Default: revoke.
14. **Idle expiry.** Default: absent (`null`); posture reports a grant unused for 90 days as idle.
15. **Publisher trust.** Default: report only; refusal is an operator policy.
16. **The normative home.** Default: the statement, its narrowing check and its verification in a
    companion document beside Core in Spec `0.5.0`, with its vectors; the receipt member and key
    scope in the gateway's `SPEC.md`; records in the agent's contract; the grant in the gateway.

This Draft does not mark complete the public comment period, the interim review regime's record
for a pull request creating an RFC ([RFC 0009](0009-interim-review-regime.md)), or the maintainer's
dispositions; those remain merge gates as the process states them.

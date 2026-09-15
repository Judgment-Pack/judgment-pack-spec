# RFC 0015: What a reported receipt would have to specify — the engine signing a call it did not make

- Status: Draft
- Type: Exploratory (research line — a cross-project artifact: the gateway's receipt format, verifier and HTTP surface, and a reporting plugin inside an MCP gateway; outside JPS)
- Created: 2026-09-15

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **Scope note, load-bearing.** Nothing this RFC proposes lands in JPS Core, a profile, a
> conformance class, or any other RFC's specification-track surface. If any part is built, the
> receipt members, the verification statuses, the HTTP surface and the conformance vectors land in
> the [reference gateway's](https://github.com/Judgment-Pack/judgment-pack-gateway) `SPEC.md`
> (§1.2a, §1.4, §4, §5, §5a, §6) and its frozen corpus; a reporting plugin lands where the MCP
> gateway it runs in keeps its plugins, by that project's own process, with any reference reporter
> beside the gateway's existing client plugins under `plugins/`; and if a decision record may cite a
> reported receipt, that rule lands in the
> [reference runtime's](https://github.com/Judgment-Pack/judgment-pack-runtime) citation decision
> ([ADR-0033](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0033-a-record-cites-the-receipts-it-relied-on.md)).
> It is recorded under [RFC 0000's](0000-rfc-process.md) cross-project exploratory provision: a
> disposition here endorses (or declines) the design record as written and confers no authority
> over any of those repositories, each of which decides by its own process. Unlike
> [RFC 0014](0014-lineage-record-and-action-binding.md), nothing it describes is built.
>
> **A word about the word.** The plan that asked for this called it a *witness* plugin, and the
> gateway's plugins note says such a receipt would be "witnessed, not acquired". In this directory
> [RFC 0012](0012-witness-contract.md) already uses *witness* for a party that records a signed
> history it observed so that a verifier can compare views. The thing asked for here is different
> — one party's account of one call, signed by the engine — and this record calls it a **reported
> receipt**, and its author a **reporter**, so that RFC 0012's word keeps one meaning.

## Summary

The reference gateway signs two kinds of receipt. An *acquisition* attests bytes a source returned;
an *action* records an authenticated write request made through the engine's executor and the
target's response, a refusal included. In both, the engine started the program that touched the
outside world. On the engine's catalog-backed path that program is also named by
the operator, pinned by digest, and run under the isolation the operator establishes; the format
admits more than that path — a bare `"command"` source, whose recorded digest is of the resolved
executable and does not bind a script an interpreter runs, and adapter subprocesses whose own
identity is the adapter's testimony in its envelope. The gateway's `SPEC.md` is exact about what
the engine's signature over that testimony is: an acquisition record of an adapter shape "is
therefore the adapter's testimony under the gateway's signature" (§1.2a, *Where the members come
from*).

An MCP gateway routes tool calls to many servers the engine never touches. A plugin in that gateway
sees calls and answers, and could hand them to the engine for a signature. The engine would then
sign an account submitted remotely by a party whose program it did not itself run and whose
executing program's identity it did not establish. This record states what such a receipt would
have to specify before any engine mints one, as **sixteen candidate clauses**, from what is attested
and what exactly was observed, through who submitted it and over what transport, to sessions,
time, correction, citation, the consumer's rule and where each part would land.

Its central content is one bound, stated as narrowly as it holds: a reported receipt would attest
that a principal the engine authenticated submitted an account of a call and an answer, and when
the engine received it. It would attest nothing about the call having been made, the endpoint
having answered, or the answer being the endpoint's. An endpoint that signed its own answer would
add an authenticated statement by that endpoint about the bytes its signature covers, which is a
different property from the engine's mediation and is not ranked against it here; this record does
not establish that any MCP server signs its results. **A reported receipt must never be readable as
an acquisition**; most of the clauses exist to keep it so.

It also records a fact that narrows the question: for calls the engine's own path can make, the
need is met without any of this. The gateway's MCP server
([ADR-0003](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/docs/adr/0003-a-fifth-process-speaks-mcp.md))
turns an MCP tool call to a configured platform's live tool into an ordinary acquisition by the
engine's own adapter. A reported receipt is about the calls that path does not make.

## Problem

The gateway's plugins note
([`docs/design/plugins.md`](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/docs/design/plugins.md),
*The witness: what a ContextForge plugin would need*) records two designs for giving an MCP gateway
receipts. The second, the engine as an MCP server, is built — design note
[`mcp-server.md`](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/docs/design/mcp-server.md),
[pull request 121](https://github.com/Judgment-Pack/judgment-pack-gateway/pull/121), merged after
six review rounds — and is honest by construction: the engine's adapter makes the call. It
covers the engine's configured platforms and nothing else. The first design, a surface on which an
authenticated remote party submits an envelope, is the one that would reach calls the engine does
not make, and the note leaves it to the specification "because 'receipts on every tool call' across
servers the engine never touches is a witness claim, and the specification should say what such a
receipt is worth before an engine mints one."

Two passages of the gateway's `SPEC.md` stand in the way, and both are there on purpose. §5: "A
client calls `/acquire` and **cannot supply a receipt** — the gateway produces every receipt. This
is what removes the model/agent from the proof path". §6: "No receipt is accepted from the caller";
and §6 defines an envelope only as what an adapter the engine started writes on its stdout (*Adapter
sources*), which the plugins note calls "no envelope from a caller". A reported receipt does not ask
the engine to accept a receipt — the engine would still produce it — but it does ask it to accept an
envelope from a caller, which is the property the first passage protects.

The risk is not that a reporter can lie. A reporter can lie, and a receipt that names the reporter
says so. The risk is **laundering**: a store holds receipts under one key, and a consumer that
reads a reported receipt as an acquisition gives a reporter's claim the strongest attestation the
project makes. Today what the key signed is an acquisition or a request and response the engine
mediated — there is no third kind — and
the consumers written so far, the gateway's verifier, the runtime's citations and the engine's own
action ladder among them, were written in that world. So the design question is less how to accept
a report than what must never be confusable once one is accepted, and what a consumer must bind
before relying on one.

## Evidence

What exists, and what it shows:

1. **The honest-by-construction path, built — for what it reaches.** `gateway mcp` exposes each
   configured platform's live tools; a call becomes `POST /acquire` on `<platform>/live` under the
   caller's token, with the call's arguments carried byte for byte, and a successful acquisition's
   answer carries the receipt. Its note is explicit that it "covers the engine's platforms, not every
   server the gateway routes." Its adapter starts an MCP server over stdio from a pinned image or a
   local command; it is not a client for an arbitrary remotely hosted MCP endpoint, and the frontend
   exposes configured live tools only.
2. **The engine already signs testimony.** §1.2a: for every adapter shape the gateway records what
   the adapter reported in its envelope, except `shape` (the operator's declaration), `statement`
   (the gateway's own commitment) and `pageItems` (the gateway's own digests); "what a compromised
   adapter can do is misreport its acquisition". What distinguishes that testimony from a report is
   not the signature but who started the program: an engine-started source, on the catalog-backed
   path pinned by digest, under the isolation §1.2a conditions the adapter's inability to sign on —
   against an account submitted remotely, by a program the engine neither started nor identified.
3. **Where a reporter would sit.** The plugins note records ContextForge's plugin framework as it
   was read for that note: hooks at `tool_pre_invoke` and `tool_post_invoke`, a hook answering with
   `continue_processing`, an optional `modified_payload` or a `violation`, plugins run in-process or
   as an external service over MCP (`kind: external`), in `enforce` or `permissive` mode. A reporter
   would be a `tool_post_invoke` hook. Naming the hook does not settle which request and which
   result it observes — other hooks may modify either — which clause 2 takes up. This record cites
   the note for that surface and does not re-verify ContextForge's current interface.
4. **A citation reads nothing but a signature.** §4 step 5 resolves an action's `cites` entry by
   three string comparisons and says "Nothing about the cited receipt's contents is read beyond its
   signature" ([RFC 0014](0014-lineage-record-and-action-binding.md) §5 records the same). If a
   reported receipt existed in a store, an action could cite it and the join would resolve; nothing
   today would say that the decision rested on a report.
5. **The neighbouring question.** [RFC 0012](0012-witness-contract.md) narrows what a witness
   contract over signed histories would need, clause by clause, and shows that "a witness signed it"
   is not a property until the contract is written. The same holds here with a different party and a
   different object: "the engine signed a report" is not a property until this record's clauses are
   answered.

What does not exist: no reported receipt, no reporter, no surface, no vector, and no study that
measured anything about one. Every clause below is a candidate.

## Specification (sketch) — candidate clauses

Each clause states what a design would have to decide, and where this record leans, why. None is a
commitment, and where a clause records only a question, the question is the content.

### 1. What is attested — and what is not

The claim a reported receipt would carry: *principal R, authenticated at the engine's boundary by a
token the engine verified, submitted an account that a call C to endpoint E returned result X, which
R says it observed at time O; the engine received the account at time S and placed it at this
position of this session.* The engine vouches for R's identity as its token verification
establishes it, for S, for the canonical values it retains from the submission (clause 2), and for
their position. It vouches for nothing else: not that C was made, not that E answered, not that X
is E's answer, not that O is true, not that E is who R says it is, and not that the session holds
every call R saw.

### 2. What was observed, and what is retained

A report is an account of an observation, and the observation needs its own contract before the
account can mean anything. Questions a design would have to answer:

- **The observation point**: where in the MCP gateway's routing the account is taken — before or
  after other plugins may modify the request or the result — and so which request and which result
  the account is of, and whether it is what reached the end user.
- **Correlation**: how an account pairs a result with its request under concurrent calls, and what
  names the invocation.
- **Coverage**: whether errors, cancellations, transport failures and calls with no answer are
  reported, and how; an account of "no answer" is an account too.
- **Representation**: the engine signs canonical values it retains (§1.1), not the wire bytes a
  reporter saw; the canonical domain excludes floating-point literals, which an MCP result may
  carry; a result may hold structured content, an error flag and resource links, and a link names a
  resource without attesting whatever is later fetched from it. What is retained, and what a value
  outside the canonical domain becomes, has to be stated.
- **Provenance of each member**: which members of the receipt the engine derives itself (the time
  of receipt, the commitments, the reporter's verified identity) and which are the reporter's
  assertions (everything describing the call).

### 3. The form: a kind, not a shape

A candidate form adds a third `kind`, `"report"`, with a `report` object in place of `acquisition`
or `action`, rather than a fifth `shape` of `acquisition`.

Both additions fail an unchanged version 3 verifier the same way: §1.4 order 1 classes a `kind` *or*
an acquisition `shape` outside its enumeration as `malformed`, so neither can pass a conforming
verifier that has not been updated. The reason for a kind is therefore not old verifiers but what
the receipt says and where a consumer draws its line once verifiers are updated: an acquisition's
object describes a fetch the engine mediated, and §1.2a's `action.cites` names what an action cites
as "the acquisition receipts the requester says the decision record relied on". A report under
`kind: "acquisition"` would put an account the engine did not mediate inside the object that
describes mediation, and after an update a consumer checking `kind` alone would accept it; a
separate kind puts the boundary at the member that says what a receipt is. A consumer that checks
one discriminator and not the other can misread either form, which is why clause 13 states the
consumer's rule in terms of the kind.

The `report` object would carry the reporter's account under the names and forms §6's envelope uses
— `adapter` (the reporting program as it names itself, **unpinned**), `endpoint`, `statement`
(committed by the engine, as for an acquisition), `snapshot`, `peerIdentity` (the identity the
*reporter's* transport to the endpoint established, as the reporter says — distinct from the
reporter's transport to the engine, clause 6), `schema`, `upstreamToken`, `observedAt` — beside the
identities of clause 4.

A further candidate, **domain separation**: a report's signature under its own prefix (for instance
`"judgment-pack-gateway/report/1:"`) rather than version 3's receipt prefix. `kind` is already inside
the signed bytes, so a report cannot be re-labelled without breaking its signature; a separate
prefix would additionally keep a report's signature from being valid as a receipt or seal whose
verifier requires its different specified prefix, at the cost of one more rule every verifier
implements. A separate *key* for
reports is a stronger variant with its own cost: the reference verifier's registry loader skips a
seal whose `keyId` is not its own key's, so a separate key cannot assume an unchanged registry
(clause 7). This record leaves both open.

### 4. The submitter and the requester

A report relayed by an MCP gateway involves at least two identities: the component that submits the
account, and the end user whose call it describes. One bearer token cannot establish both. With
the gateway's own service token, the authenticated principal is the gateway; with an end user's
token forwarded by the gateway, the authenticated principal is the user, and the token does not
authenticate the reporting plugin at all. The MCP server's note draws the same line for its own
path and refuses tokens issued for another resource.

Questions a design would have to answer: whether the receipt's top-level `caller` is the
authenticated submitter, with a `reporter` member duplicating it or replaced by it; whether the end
user's identity is carried separately, as the reporter's assertion; and what evidence of delegation
would be needed if the receipt were to attribute the call to the end user more strongly than as the
reporter's word. A candidate rule, whatever the answer: the engine accepts reports only from
principals its configuration names as reporters, and only for endpoints the configuration names for
each, so that a reported receipt carries not only who submitted but that the operator allowed that
principal to report on that endpoint. Without such a rule every principal with a valid token could
put the engine's signature on any account of any server, which is the laundering risk at its widest.

### 5. What a verified token proves here

The gateway's statement about `caller` holds unchanged: a verified token proves who submitted, at
the boundary, and not that they observed anything or approved anything.

### 6. The transport between reporter and engine

Token verification authenticates the reporter to the engine; it does not authenticate the engine to
the reporter, and it protects neither the submission nor the answer in transit. The reference serves
plain HTTP on loopback, and its security note makes the custody of commitment salts depend on the
transport; and the gateway's plugins note records that one workflow framework's HTTP client turns
certificate verification off for its whole process, which would let an impersonating engine collect
the bearer — the reference piece sends through another client for that reason. Questions a design
would have to answer: how the reporter authenticates the engine; where confidentiality and
integrity terminate; which components can read bearer tokens and salts on the way; and how a
reporter's credentials are renewed and revoked. This record chooses no mechanism.

### 7. Sessions and their lifecycle

A candidate rule: a session holds reports or it holds acquisitions and actions, never both, so that
a sealed session's count and chain speak for one kind of account and a consumer scoping to a
session (§5a.1) knows what it scoped to. Separation by kind settles neither who may append nor who
may seal. Today sessions share one namespace, any caller who knows a name can append to it and seal
it, a transport session's end seals nothing, and a signer restart empties the signer's session map,
so the process that follows restores neither the previous count nor the previous chain; `/seal`
refuses a session absent from its in-memory map rather than reconstructing it from disk. A remote
reporter adds accounts still queued outside the signer when a session is sealed. Questions a design would have to answer: who may append to and seal a report session;
whether reporters may share one; what happens to accounts in flight at a seal, to a lost
acknowledgement and its retry, to an account that arrives after a seal, and after a signer crash;
and how the registry handles a separate key or a separate store if clause 3's variants are taken.
And for the reporting plugin's project, with the gateway's acknowledgement contract: does reporting
complete before the original tool result is returned, or proceed independently? If reporting is
refused or its outcome is unknown, what result and reporting status reach the caller? Retrying the
account must be distinguished from rerunning the tool: a reporting failure does not establish that
the original call failed or that its effects were undone — the MCP server's note draws the same
line between a signer's refusal and an unknown outcome on its own path. Whatever the answers, under
the base proposal **the seal authenticates the signer's declared final count of minted report
receipts, whose contents are checked through store verification; it establishes neither a count of
submissions merely received or admitted nor that every routed call was reported.**

### 8. Time

`servedAt` stays the engine's own stamp. `observedAt` is the reporter's. The engine can compare its
clock with the reporter's claimed time — refuse an account whose `observedAt` is after `servedAt`
beyond an allowance for clock skew, or older than a configured window — and cannot verify the
claim. A candidate: apply both, and record the window the engine applied, so a consumer can tell
which window the **claimed** observation time satisfied. An account of a week-old or invented call
submitted with a current `observedAt` passes any such check; it is an expected-undetectable case,
not a failure of the check.

### 9. Duplication and fabrication

A reporter can report one call twice, or a call that never happened, and the engine cannot tell
either from a genuine account. A report key chosen by the reporter would let the engine refuse a
second account under the same key; that stops accidental duplication and nothing else. From the
reporter's account alone, the engine cannot establish whether the call occurred. Whether clause 10's
independently authenticated evidence would constrain acceptance remains open.

### 10. Upstream integrity

If the endpoint itself signed its answer, under a key the operator pins for that endpoint, an
account could carry that signature, and a verifier could check it: the bytes the signature covers
would then be the endpoint's by the endpoint's own statement, whatever the reporter is. That is an
authenticated endpoint statement about those bytes and nothing more. It does not establish that
the answer belongs to the reported request, requester, invocation or time — a genuine signed answer
can be replayed under another reported call — unless the signature covers that context; and a
canonicalization or transformation between the signed object and the retained value can break the
correspondence. §1.2a's `upstreamToken` is an opaque string the receipt carries, not a validation
protocol, and an account without one cannot establish that the endpoint offered none. Questions a
design would have to answer: what an upstream signature covers and how it binds the call's context;
how endpoint keys are trusted, pinned and rotated; and what a missing, invalid or unchecked token
means. This record does not establish that any MCP server signs its results, and it reads the
protocol version the gateway's MCP client proposes as defining no result signature, while its
extensible result data does not forbid an application-specific one.

### 11. Citation

Should an action be admissible when a receipt its decision cites is a report? Should §4 step 5 and
step 7 resolve a citation of a report, and with what effect on a verdict? Two boundaries shape the
answer. The runtime (ADR-0033) records the citations its caller supplies without reading any
receipt or store, so any kind the runtime recorded beside a citation would be the caller's
assertion, requiring comparison with the authenticated receipt — and its input grammar requires
exactly three members per citation, so a fourth is a grammar change with a migration. And the
verifier's citation findings count against the store-wide `ok`, while record findings name no
session and need explicit treatment under session scoping (§5a.1). Candidates: the action ladder
refuses a citation of a report unless configuration allows it for that platform; the verifier
derives the cited receipt's kind while resolving the citation, and a distinct finding says a
citation resolved to a report, with its effect on acceptance stated for each consumer policy; the
runtime records nothing new. The alternative — citations blind to kind, as today — would let a
decision that rested on a reporter's account read as one that rested on the engine's acquisition.

### 12. What a consumer binds

Binding a report cannot stop at the reporter and the result digest: a valid report by the expected
reporter about the expected endpoint can concern another query, another user or another
invocation, and its signature and result digest will verify. The MCP server's consumer guidance
already compares the signed source, session and caller, and the opened commitments, with the
intended request; a report needs the same and more. A consumer rule in the manner of §5a would keep
the whole §5a.4 ceremony — the store verified under a pinned key, the receipt bound among its
accepted findings, the result re-digested — and add binding to the intended call and its context
through the opened `statement` and arguments commitments. Questions: who receives and keeps the
commitments' salts when an account is relayed — the reporter, the gateway, the end user — and how a
consumer tells the report it expects from another genuine report by the same reporter about the
same endpoint.

### 13. The consumer's rule

Stated in terms of the kind (clause 3): a consumer that requires the lineage of an acquisition
refuses `kind: "report"`; a report verifies as a report and does not change the store-wide verdict
by being one; and a consumer that accepts a report accepts the reporter's account under clause 12's
binding — the engine's signature adds the reporter's verified identity, the time of receipt and the
position, not the truth of the account. A consumer relying on the account must explicitly trust the
authenticated reporting principal for that endpoint; the engine's admission allowlist (clause 4)
does not establish the consumer's trust.

### 14. Retention, deletion and correction

A report's `statement` and arguments would be committed as an acquisition's are, its result
retained in the clear as any artifact is, and what a reporter puts in the other members is in the
receipt in the clear. What happens afterwards is unspecified and consequential: changing a receipt's
signed values without re-signing invalidates its signature and can prevent reconstruction of the
session; deleting a retained result makes the
receipt `artifact-missing`; removing sealed receipts or sessions conflicts with the registry; and an
artifact may be shared by digest with another receipt. Questions a design would have to answer: how
long reports and their results are retained; whether and how an authorized party deletes one; how
an erroneous account is corrected or retracted — by a later report that says so, or otherwise — and
what a consumer concludes after either. Deletion and correction cannot be assumed neutral to
verification.

### 15. Resources

A report has a different resource profile from an acquisition: no source runs, and the submitter's
input drives parsing, signing and retention directly. Per-acquisition deadlines and output bounds
limit one source run, not aggregate concurrency or retained storage, and the MCP server's note
records that the signer admits acquisitions without a global bound. Questions a design would have to
answer: per-reporter rate and size bounds at the surface; aggregate concurrency and pending work;
the growth of sessions, the registry and the store; and the cost reports add to verification.

### 16. Where each part would land

| Part | Would land in |
|---|---|
| the `report` kind, its object, its commitments, its signature coverage, the statuses | the gateway's `SPEC.md` §1.2a, §1.4, §4 |
| the report surface (a new `POST`), its admission, its transport, its bounds | the gateway's `SPEC.md` §6 and its engine design notes |
| the honest bound and the consumer's rule | the gateway's `SPEC.md` §5 and §5a |
| vectors: a report, a malformed one, a report cited by an action, a mixed session | the gateway's frozen corpus |
| a reporter | the MCP gateway's own plugin tree, by its process; a reference reporter under the gateway's `plugins/` |
| whether a decision record may cite a report, and what it records | the runtime's ADR-0033 successor |

**Versioning.** A version 3 receipt with an unknown `kind` is `malformed` to a version 3 verifier. A
receipt that declared a new `receiptVersion` — `"4"`, say — and was otherwise well formed would be
`unsupported-version` to the same verifier instead: the reference skips version-specific structural
checks for a version it does not know. Either way, under the default store-wide rule of §5a.1 the
old verifier withholds every session of a store that holds one; a deliberate session-scoped consumer
may still act on a session that satisfies all of §5a.1's conditions. A version change identifies
the incompatibility to an old verifier; it does not remove it. How stores holding reports would
migrate, and whether reports would live in a separate store — which the registry's expected session
set would then have to account for — is open.

## Alternatives

- **No change.** Calls the engine's own path can make are receipted through the MCP server,
  honestly; a call to any other server gets no engine receipt, and the MCP gateway's own logs remain
  what they are — unsigned records of the gateway operator. This is the current state and costs
  nothing.
- **Make the engine the proxy, where its path reaches.** Configure a server the MCP gateway routes as
  an engine platform, and let the engine's own MCP adapter make the call through `gateway mcp`: each
  successful acquisition through that path is then honest by construction. Its reach is the current
  adapter's — an MCP server started over stdio from a pinned image or a local command, configured
  live tools only, no `/act` and no other MCP capability through the frontend — so a remotely hosted
  server needs a transport bridge the engine does not have, and moving a call through the engine can
  change its credentials, state and behaviour. Nor does an engine fronting a server mean that a
  particular call the MCP gateway routed some other way went through it. The costs beyond
  configuration are open.
- **Reporter-signed reports, the engine as notary.** The reporter signs its own account with its own
  key; the engine countersigns the reporter's signed statement with a time and a position. This adds
  a real property — attribution to the reporter's key that anyone holding it can check — and can
  reduce confusion **when consumers verify and distinguish both statements**. It does not remove
  laundering: a consumer can still take the engine's countersignature for endorsement of the
  enclosed claim. Its costs are a key per reporter, and the distribution, trust and lifecycle of
  those keys.
- **Witnessing over a log.** Reporters append to a log whose history independent witnesses record, in
  the sense of [RFC 0012](0012-witness-contract.md): the aim is to make conflicting histories
  observable under a specified witness contract, which RFC 0012 itself does not claim in general,
  and it establishes nothing about the truth of a call. It could complement reported receipts
  rather than replace them.
- **Product-only logging.** The MCP gateway records calls in its own store with no engine signature.
  Honest about what it is, and no part of this project's attestation.

## Compatibility

Under clause 16's versioning paragraph: a report is `malformed` to a version 3 verifier if it
declares version 3 and `unsupported-version` if it declares a version that verifier does not know,
and under the default store-wide rule either withholds every session of a store holding one;
stores without reports are unaffected. The statement in §5 that a client "cannot supply a receipt"
stays true — the engine would still produce every receipt — and the statement in §6 that an
envelope comes only from an adapter the engine started would change, for the report surface alone.
The seal's and the registry's **formats** could stay unchanged under the base proposal; clause 3's
separate-key variant and clause 16's separate-store variant could not assume the registry's
behaviour unchanged. The corpus would gain vectors. The runtime's citation grammar is unaffected
unless clause 11 adds a member to it, which is a grammar change with a migration.

## Security and privacy

- **Laundering** is the primary risk: a report read as an acquisition. Clauses 3, 7, 11, 12 and 13
  exist to prevent it; none of them helps a consumer that ignores `kind`.
- **A compromised reporter** can fabricate any call and any answer, with a current claimed time; the
  receipt names the reporter, which is what it can do.
- **A stolen reporter token** lets its holder report as that reporter until the token expires; the
  engine's token rules (issuer, audience, expiry) and clause 4's allowlist bound it, and clause 6's
  transport decides who can steal one.
- **The engine's key signs for more parties.** Every report is a signature under the same key that
  signs acquisitions; [RFC 0010](0010-gateway-signing-identity.md)'s custody questions weigh more
  when the key's use widens, and clause 3's separate-key variant is one answer, with its registry
  cost.
- **Disclosure and its lifecycle.** Clause 14: what a report carries in the clear, and that its
  deletion or correction is not neutral to verification.
- **Resources.** Clause 15.

## Conformance

Were a design adopted, the vectors would include: a well-formed report that verifies as a report; a
version 3 receipt of the new kind under an unchanged version 3 verifier, `malformed`, and a receipt
of a new version under it, `unsupported-version`; a report without its submitter's identity,
`malformed`; a session holding a report and an acquisition, refused at the surface and reported by
the verifier; an action citing a report, with whatever finding clause 11 chooses; an account whose
`observedAt` is after its `servedAt` beyond the skew allowance, refused at the surface; and
consumer-side cases in the manner of the gateway's ceremony test — a consumer that requires an
acquisition refusing a valid, verified report, and a consumer binding a report refusing another
genuine report by the same reporter about the same endpoint for a different call. None exists.

## Implementation

Nothing is implemented. Plausible independent implementations, were a design adopted: the reference
gateway minting and verifying reports; a verifier of the receipt format written independently of the
reference, which this record does not establish exists for version 3; and at least two reporters in
different MCP gateways or clients, the first a ContextForge plugin. RFC 0000's bar of two independent
implementations is unmet and is not claimed.

## Unresolved questions

1. **Whether the engine should mint reports at all**, given the proxy alternative, which reaches the
   strongest bound for calls the engine's own path can make, and the notary alternative, which adds
   independently checkable attribution to the reporter.
2. The observation point, correlation, coverage and retained representation of clause 2.
3. Whether a report is signed under its own prefix or under a separate key (clause 3), with the
   registry consequence of the latter.
4. How `caller`, the reporter and the end user relate (clause 4), and what delegation evidence a
   stronger attribution to the end user would need.
5. The transport between reporter and engine (clause 6): engine authentication, termination of
   confidentiality and integrity, custody of tokens and salts, credential renewal and revocation.
6. Who may append to and seal a report session, whether reporters share one, and what happens to
   accounts in flight, retried, late or interrupted by a crash (clause 7).
7. What window and skew allowance clause 8 applies by default, and how the engine's own timestamp is
   defined.
8. Whether a report key (clause 9) is required, optional, or absent.
9. What an upstream signature covers, how it binds the call's context, how endpoint keys are trusted
   and rotated, and what a missing or unchecked one means (clause 10).
10. What the action ladder and the verifier's join do with a citation of a report, with what effect
    on each consumer policy, and whether the runtime's grammar changes (clause 11).
11. Who holds the commitments' salts across a relay, and how a consumer tells an expected report from
    another genuine one (clause 12).
12. Retention, authorized deletion, correction and retraction of reports, and what a consumer
    concludes after each (clause 14).
13. Aggregate bounds on reporting and on the growth it causes (clause 15).
14. How stores holding reports migrate, and whether reports live in a separate store (clause 16).
15. Whether ContextForge's current plugin interface still offers what the plugins note recorded, and
    whether a second MCP gateway offers a comparable hook — the evidence for clause 2's observation
    point and for the implementation bar.

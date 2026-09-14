# RFC 0014: The lineage record and the action binding — how a decision cites what it read, and an action cites what it decided

- Status: Draft
- Type: Exploratory (research line — a cross-project artifact: the gateway's version 3 receipt and its verifier's join, the reference runtime's citation members; outside JPS)
- Created: 2026-09-14

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **Scope note, load-bearing.** Nothing this RFC proposes lands in JPS Core, a profile, a
> conformance class, or any other RFC's specification-track surface. Every part it records lives
> in another repository of the project and is governed there: the receipt members, the citation
> grammar and the verifier's join in the
> [reference gateway's](https://github.com/Judgment-Pack/judgment-pack-gateway) `SPEC.md`
> (§1.2a, §4, §6) and its frozen corpus; the record members in the
> [reference runtime's](https://github.com/Judgment-Pack/judgment-pack-runtime) architecture
> decision records
> ([ADR-0033](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0033-a-record-cites-the-receipts-it-relied-on.md),
> [ADR-0034](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0034-profile-a-matrix-against-its-history.md));
> the worked examples in the
> [demo's](https://github.com/Judgment-Pack/judgment-pack-demo) acts. It is recorded under
> [RFC 0000's](0000-rfc-process.md) cross-project exploratory provision: a disposition here
> endorses (or declines) the design record as written and confers no authority over any of those
> repositories, each of which decides by its own process. Unusually for a record in this
> directory, the parts already exist: this record is written after the fact, as the runtime's
> decision records are, so that a binding that spans three repositories can be read, reviewed and
> objected to as one design rather than reconstructed from three. RFC 0000 describes the
> provision for a design question that deserves visibility *before* any implementation exists,
> and RFCs 0010 and 0011 were filed prospectively; this record therefore **seeks** the
> provision's application to retrospective documentation and lists whether it covers that case
> as an unresolved process question (Unresolved 8).

## Summary

When a decision is challenged, three questions get asked: what information did we have, which
rule did we apply, what did we then do. The project answers them from three ledgers that, until
this line, only a person could reconcile. The gateway's receipts bind retained bytes to its
attestation under operator-configured source and authority labels — byte-lineage, never that
the genuinely named source returned them; the runtime's decision record says what was judged
and decided; a write to a target system was the application's own log. This record describes the join as built: a receipt that
names its source — which system, which statement, which snapshot, through what, for whom — and
a **citation**, one grammar owned by the gateway, by which a decision record names the receipts
it relied on and an action receipt names the decision record and the receipts it rests on. A
verifier that reads the gateway's store and the runtime's decision-record directory side by side
then resolves the join in both directions, by digest and by exact name, and interprets no
decision semantics beyond reading and validating a record's `cites` member.

The claim is deliberately small. A citation is the **caller's assertion**, recorded as given by
a runtime that holds no key and reads no store. The verifier's finding is that what a citation
names **is there**: a receipt at exactly that session, index and signature, whose own
verification under the gateway's key is reported as its own finding; a record with exactly the
claimed digest under the directory the operator named. Never that it was the right receipt,
never that the record is true, and never that a person approved the action the receipt
records.

## Problem

The interoperability problem is that three artifacts made by three programs must agree on one
way of naming each other, or the reconciliation stays manual.

- A version 2 receipt ([gateway `SPEC.md` §1.2](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/SPEC.md))
  binds the bytes, the position in a session, the chain, and two labels the operator chose. It
  does not say which system was asked, which statement ran, which snapshot was read, or through
  what; its arguments digest is a keyed equality oracle to every caller; and it has no form for
  an action a person asked for.
- A decision record ([runtime ADR-0018](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0018-opt-in-evaluation-audit-trail.md))
  holds the pack's digest, the facts as evaluated and the disposition. It does not hold where the
  facts came from, and it must not verify anything to say so: the runtime is stateless, keyless
  and offline by decision.
- A write-back is performed by whatever the application uses, and nothing ties it to the
  judgment that proposed it.

The affected users are whoever must answer the challenge — an auditor who trusts none of the
parties, a policy owner ruling on a disagreement between a draft and history
([ADR-0034](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0034-profile-a-matrix-against-its-history.md)),
an operator asked why a ticket changed state — and any second implementation of a receipt
verifier or a record writer, which needs the grammar written down rather than inferred from the
reference implementations.

## Evidence

Implementation, release and demonstration status are stated separately for each item below;
none of it is a sketch, and not all of it is released.

- **Receipt version 3** — gateway `SPEC.md` §1.2a, corpus `corpus/v3/`. A receipt carries a
  `kind` (`acquisition` or `action`), a salted `argumentsCommitment` in place of the keyed
  digest, a `caller` from a verified token or `null`, and either an `acquisition` record (adapter
  by name and digest, shape, endpoint, a commitment to the statement, snapshot, peer identity,
  schema digest, an upstream integrity token or `null`, page item digests, `observedAt`) or an
  `action` record (requester, decision claim, citations, tool, request commitment, adapter,
  `observedAt`). The gateway's own statement of what a version 3 receipt adds and does not change
  is that section's opening paragraph; this record does not restate it. Merged on the
  gateway's `main`; the gateway has cut no release containing it (its tags stop at `v0.2.0`,
  which predates every part named here), and the demo builds it from a pinned commit.
- **The verifier's join** — gateway `SPEC.md` §4 steps 5–7 and the statuses `citation-unresolved`,
  `decision-record-mismatch`, `record-citation-unresolved`, `record-citation-malformed`, held by
  twenty version 3 store vectors in the frozen corpus (among them `v3-action-valid`,
  `v3-citation-unresolved`, `v3-citation-case-differs`, `v3-decision-record-mismatch`,
  `v3-decision-records-absent`, `v3-record-cites-resolved`, `v3-record-cites-twice`,
  `v3-record-citation-member-by-another-case`, `v3-requester-null`).
- **The executor** — gateway `POST /act` (design note `docs/design/executor.md`): before any
  executor runs, the engine holds an authenticated requester, an open session of its own, a
  platform whose configuration allows writes, a tool the binding names, the decision claim's
  shape, each citation resolved in its own store and verified under its own key, and a record
  with the stated digest under its decision-record directory; then it performs the write through
  the platform's MCP tool and mints the action receipt. Seven cross-vendor review rounds and
  twenty-seven findings are recorded on the gateway's pull request 114.
- **The record's citation** — runtime ADR-0033: `cites` on every record a run leaves, held to
  the gateway's structural grammar and the runtime's one-MiB document limit, without resolving
  or verifying citations, recorded as given, omitted when none was supplied; a rehearsal accepts a citations document of the grammar and within the limit and
  writes no record, citations included. Runtime ADR-0034: a matrix row may carry the same `cites` under `matrixVersion "3"`,
  so a row transcribed under a receipted page can name that receipt. ADR-0033 shipped in runtime
  0.20.0; ADR-0034 is merged and tagged for 0.21.0, whose release was in progress at the time of
  writing. Each carries cross-vendor review records on its pull request: 145, eight rounds and
  thirty-one findings; 147, seven rounds, whose closing summary counts nineteen findings where
  its round tables itemize seventeen — the discrepancy is the source's and is left as found.
- **Worked examples** — the demo's Act 7
  ([pull request 70](https://github.com/Judgment-Pack/judgment-pack-demo/pull/70), open at the
  time of writing): a draft pack replayed against thirteen fixture rows standing for past
  decisions, initially without citations; an optional helper then copies the newest receipt of
  the store's last session onto every row as a caller-asserted citation — it does not establish
  that the receipt covers those rows, which is exactly what a citation does not establish. Act 8
  (branch `act8/approved-write`, pushed to the demo repository and not yet a pull request, since
  it builds on Act 7): a receipted read, a judgment citing it, an action minted under a person's
  token, the three ledgers verified together, and the judgment rewritten after the fact to show
  the action receipt outliving it. These are demonstrations, not conformance evidence, and their
  standing is as stated, not merged.

What the evidence does **not** include, said here so the *Implementation* section is not
misread: no second, independent implementation of the version 3 verifier exists; the runtime
is the only writer of records that cite; and the golden-record agreement test the gateway's
[ADR-0001](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/docs/adr/0001-one-engine-four-processes.md)
names — one record fetched through both adapter shapes deriving to byte-identical facts — is a
stated design and has not been built.

## Specification (sketch) — the join as built

Field names and canonical forms are not fixed here; the gateway's `SPEC.md` governs every form a
verifier checks and the runtime's decision records govern what its records carry, exactly as
[RFC 0010](0010-gateway-signing-identity.md) and [RFC 0011](0011-judgment-currency-anchor.md)
defer. What this section fixes is the *shape of the agreement* between the parts: who writes
what, who checks what, and what a check means.

### 1. The lineage record: a receipt names its source

An acquisition receipt records, under the gateway's signature, what the adapter reported about
how it got the bytes: the adapter by name, version and digest; the operator-declared shape; the
endpoint; a **commitment** to the statement (query, resource path or tool call) whose salt the
gateway returns to the caller and does not retain — exclusive possession of it depends on the
transport and on the caller's custody, which the gateway's `SECURITY.md` says and this record
does not improve on; the source's own word about currency (a bookmark, a transaction id, an
ETag) or `null`; the transport's peer identity or `null`; the discovered schema by digest or
`null`; an integrity token the upstream itself produced, carried verbatim, or `null`; for a page,
the gateway-computed digest of each item's canonical bytes, in order; and the adapter-reported
observation time — except for the `command` shape, which reports nothing, where it is the
gateway's own stamp of the moment it had read the command's output in full. Two of these are the honest
bounds: `upstreamToken` never lets a source that vouches for itself and one that vouches for
nothing read the same, and `shape` never lets bytes attested through a bare operator command
read as bytes whose acquisition was recorded.

The property this buys, and its bound: a reader can take *through what* — the adapter by name
and digest, the shape, the endpoint — and *which snapshot*, when the source reported one, off
the receipt offline; *which query* is a commitment, checkable offline when the statement and its
salt are available to the reader, and `null` when the adapter reported none. The
acquisition record is the **adapter's testimony under the gateway's signature** — a compromised
adapter can misreport its acquisition as it can misreport its bytes, and is attributable by the
source it was configured as; what it cannot do is sign, provided the isolation the operator
established keeps it from reading the signing seed, since an adapter run as the signer's own
identity can read what the signer can.

### 2. The citation: one grammar, owned by the gateway

A citation is `{sessionId, callIndex, signature}`: a flat session token, an integer from 0 to
2^53−1, and a version 3 signature of exactly 128 lowercase hexadecimal characters. The required
members and their value forms are the gateway's (§1.1, §1.2a, §3a); the runtime adopts those
forms and requires exactly the three members on input, as the executor does of a request's
citations, while the gateway's verifier tolerates additional signed members at any depth of a
receipt it verifies — so the accepted input sets differ at the edge, and one verifier still
resolves every citation any of them wrote. A citation **resolves** when its `sessionId` is exactly a
session directory name the verifier enumerated, its `callIndex` exactly a receipt file stem in
it, and its `signature` the same string as that receipt's — exact strings, never normalized, so
a citation that differs by case or by a leading zero names nothing.

### 3. The decision record cites, and is cited by digest

The runtime writes `cites` on every record a run leaves when the caller supplied citations,
holds the supplied document to the structural grammar above and to its document limit of one
MiB, resolving and verifying nothing, and records it as given. It does not check that a session exists, that a receipt verifies, or that the
cited receipts bear on the facts; a document not of the shape is refused as a bad invocation
before the project is read, as is one over the limit; a rehearsal accepts a document of the
shape and within the limit and records nothing, citations included.

A decision record is **cited by the digest of its bytes**, as the verifier enumerates
candidates (§4 step 6): every regular file under the directory whole, a `.jsonl` file included,
and for a `.jsonl` file additionally each line — the bytes split on `0x0A`, one trailing `0x0D`
removed, an empty piece not a candidate, a non-empty unterminated final piece a candidate.
Nothing inside a record is read to compute its digest, and `recordVersion` stays `"1"`: the
member is additive.

### 4. The action binds a decision to what was done

An action receipt carries the requester the gateway authenticated (never `null`), the
requester's **claim** of the decision — the record's digest and the pack's digest — and the
requester's citations, together with the tool, a commitment to the request sent, the executor's
identity and when the target answered; its `resultDigest` is over the target's response bytes,
retained like any artifact. The executor **refuses before anything runs** unless the citations
resolve in its own store under its own key and a record with the stated digest is under its
decision-record directory; it compares nothing inside the record and reads nothing of the
pack. A target's refusal of the write is a response like any other and is receipted.

### 5. The join, in both directions, by a verifier that reads one record member and no more

Given the store, the registry and the decision-record directory, the verifier resolves:

- from the action's side (§4 step 6): the action's `decision.recordDigest` equals the SHA-256 of
  some candidate anywhere under the directory, or `decision-record-mismatch`;
- from the record's side (§4 step 7): each candidate step 6 enumerated — a regular file whole,
  or for a `.jsonl` file each line and not the file whole — that is one JSON object with a
  top-level `cites` member is a record that cites, and each of its citations resolves as an
  action's do, or `record-citation-unresolved`; a `cites` of another shape is
  `record-citation-malformed`. The finding is keyed by the candidate's digest — the same digest
  an action would name it by. This is the one member of a record the verifier reads — and the
  reference reads it only in a record its scanner recognizes: a record nested deeper than ten
  thousand levels is passed over in this step with no citation finding at all, while its bytes
  remain a candidate for step 6, so an action's digest match does not establish that such a
  record's citations were checked;
- from the action to its receipts (§4 step 5): each citation resolves by three exact string
  comparisons — session directory name, receipt file stem, signature — or `citation-unresolved`.
  Whether the cited receipt itself verifies is that receipt's own finding, reported
  independently: a citation can resolve to a receipt the ladder reports `malformed` or
  `signature-mismatch`, and the store's verdict then fails on that finding, not on the
  citation. (The executor holds more before it runs: each cited receipt must also pass the
  ladder under the engine's key, which is its requirement and not the verifier's.)

**What "verifying" means here, exactly:** that what a citation names is there, by exact name,
and that a record with the claimed digest is somewhere under the directory the operator named;
what the named receipt is worth is its own finding. A stricter reading — that the cited receipts
were the right ones, that the record's facts match their artifacts, that the pack digest names
the pack the record was made under — would have the verifier interpret a record, and beyond
the `cites` member nothing in this design does. `packDigest` is recorded as given and checked
against nothing.

### 6. Identity: who asked

A non-null `caller` on a version 3 receipt, and `requester` on an action receipt, are the
issuer, subject and token digest of a token the gateway verified against a configured issuer,
with a local copy of its keys and nothing fetched on the request path. A gateway configured
with no issuer records `caller: null` on every acquisition receipt and refuses every action,
since a requester is never null; a version 2 receipt has no `caller` member. What a verified
token proves is **who asked**,
at the gateway's boundary. It does not prove that they approved what was asked for. The token
is never stored and never signed into a receipt.

### 7. Where each part lands

| Part | Repository | Where |
| --- | --- | --- |
| Receipt version 3: `kind`, `caller`, commitments, `acquisition`, `action` | gateway | `SPEC.md` §1.2a; `corpus/v3` |
| Citation grammar and resolution; decision-record candidates; the join statuses | gateway | `SPEC.md` §3a, §4 steps 5–7, §1.4 |
| The executor and its refusal ladder | gateway | `docs/design/executor.md`, `POST /act` |
| Identity verification and its bound | gateway | `docs/design/engine-config.md` (`identity`) |
| `cites` on decision records; nothing written on a rehearsal | runtime | ADR-0033; `experimental evaluate --cites`, the graph surface, the MCP tool |
| `cites` on matrix rows; the history profile that reads them | runtime | ADR-0034; `matrixVersion "3"` |
| Worked examples | demo | `projects/enterprise-demo/DEMO.md`, Acts 7 and 8 (standing as in *Evidence*) |

## Alternatives

- **No join.** Three ledgers reconciled by hand. This was the state before the line and remains
  what a deployment gets if it supplies no citations; nothing here is required.
- **The runtime verifies what it cites.** Rejected: the runtime is a stateless oracle that holds
  no key, opens no connection and reads no store, by its own decisions
  ([ADR-0006](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0006-authoring-lifecycle-in-the-client.md),
  [ADR-0012](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0012-jpack-project-convention.md),
  as ADR-0033 restates them), and a record that carried a verified reference would claim what
  the runtime cannot know.
- **The record embeds the receipt.** Rejected: a copied receipt verifies no better than a named
  one, and the record would then carry bytes the runtime cannot check for shape.
- **A citation member in JPS Core.** Not proposed. Nothing here is part of a pack: a pack names
  the evidence it needs ([RFC 0003](0003-evidence-reference.md)); a record names what was used.
  The question of a JPS-level member arises only if two independent runtimes write records
  that cite, which no one has done.
- **An outside lineage format** — OpenLineage, in-toto attestations. Not chosen for the
  binding itself, since neither carries a session chain, a seal, or a commitment scheme; whether
  a receipt and an action receipt can be **bound** to such a format, so that a consumer of
  either reads the other, is a study question the plan names and this record leaves open.
- **Digest the record's canonical form rather than its bytes.** Rejected: the verifier would
  then interpret a record to name it, and a book re-serialized by a tool that reorders members
  would silently keep verifying under a digest the bytes no longer have. Digesting the bytes
  means that changing a cited candidate's bytes breaks that match unless a candidate with the
  same bytes remains anywhere under the directory; it does **not** establish an append-only
  history of the book — step 6 binds neither a line's position nor the book's sequence, so
  lines can be reordered, and a copy kept elsewhere keeps a rewritten line's join alive.

## Compatibility

- **Readers.** A version 3 verifier verifies a version 2 store unchanged; a version 2 receipt
  means afterwards exactly what it meant before. A verifier that does not know `cites` reads a
  record with one as it always did — the member is additive and `recordVersion` is unchanged.
- **Writers.** A record without citations is byte for byte what it was. A matrix without
  `matrixVersion "3"` is unchanged.
- **Semantics.** A citation is an assertion; its presence changes no disposition, no trace, no
  payload. An action receipt is a new `kind`, not a change to acquisition receipts.
- **Migration.** None. A deployment adopts citations by supplying them.

## Security and privacy

- **Assertion, not finding.** Every citation and the decision claim are the caller's or the
  requester's word until the verifier resolves them. A record that cites receipts that do not
  exist is written as it was given; the finding that they do not resolve is the verifier's, and
  only when the store and the book are read together.
- **Disclosure.** The statement and the request sent to a target are commitments; the salts are
  returned to the caller and never stored, so a party holding the store learns nothing about
  them from their commitments alone. Every other member is in the clear — `endpoint`,
  `snapshot`, `peerIdentity`, `upstreamToken`, the tool's name — and can disclose what an adapter
  put there; what the retained artifact discloses is the source's affair, and a source that
  echoes its arguments has disclosed them. The token is never stored; its digest is.
- **Tampering is observable, not prevented.** The book is the runtime's file, writable by
  whoever can write the project; the store is the gateway's, writable by whoever can reach it.
  Rewriting a cited record is caught as `decision-record-mismatch` from the action's side when
  no candidate with the original bytes remains under the directory, and removing a cited
  receipt as `citation-unresolved`, with the seal's count missing it besides; nothing stops
  either edit, and neither finding says anything about the book's order or history.
- **Confusion.** Exact-string resolution: a citation that differs by case, by a leading zero, or
  by a look-alike character names nothing. A record's `cites` that is not exactly the grammar is
  `record-citation-malformed`, never partially read — in a record the reference's scanner
  recognizes; a record beyond its nesting limit yields no citation finding and stays a digest
  candidate (§5), so a match from the action's side says nothing about its citations.
- **Resource.** The verifier's walk of the decision-record directory is not bounded in bytes,
  entries or time; the gateway states availability as a limit of the reference, and an operator
  who mounts an archive has made the walk as long as the archive. The executor's walk is the
  same one.
- **Two engines on one store** is outside the executor's ownership claim, stated in its note.
- **What identity does not establish.** A token proves who asked. Approval of a specific action
  is not evidenced by anything here, and the receipt does not say it (Unresolved 1).

## Conformance

The conformance surface is the gateway's frozen corpus, not this record. Positive: a valid
action receipt with resolving citations and a record whose digest matches
(`v3-action-valid`, `v3-record-cites-resolved`). Negative: an unresolved citation, a mismatched
record, an absent record directory, a null requester, a `cites` member given twice
(`v3-citation-unresolved`, `v3-decision-record-mismatch`, `v3-decision-records-absent`,
`v3-requester-null`, `v3-record-cites-twice`). Boundary: a citation that differs by case
(`v3-citation-case-differs`), a record member spelled in another case
(`v3-record-citation-member-by-another-case`), a version 2 receipt relabelled as version 3, a
version 3 receipt signed under the version 2 prefix. Adversarial: a member appended inside the
acquisition record (`v3-appended-member-inside-acquisition`), a malformed kind.

On the runtime's side the conformance is shape refusal: a citation document not of the grammar
is refused on every surface before the project is read, as is one over the one-MiB limit, and
a rehearsal accepts a document of the grammar and within the limit and writes no record. These are the runtime's tests, not corpus vectors, and this
record does not promote them.

## Implementation

Two implementations exist and are not independent: the gateway's Go verifier and executor, and
the runtime's Go record writer, both by this project. A clean-room second implementation of the
verifier was built for receipt version 2 from the corpus alone — which is what exposed that the
format had never been written down and produced `SPEC.md` §1 — and none has been built for
version 3's join. The two-independent-implementations bar of [RFC 0000](0000-rfc-process.md)
is therefore **not met** for anything here, and this record asks for endorsement of a design
record, not for acceptance of a stable feature. A plausible second implementation is the same
exercise again: a verifier written from `SPEC.md` §1.2a and §4 and the version 3 corpus alone,
by someone with no access to the Go code, whose disagreements would be the finding.

## Unresolved questions

1. **Approval evidence.** A token proves who asked. What would evidence that a person approved
   *this* action — a signed statement over the request commitment and the decision claim,
   under a key the person holds — and where would it live? The plan names this open; nothing
   here answers it.
2. **A row's citation of a page.** A matrix row cites the page receipt it was transcribed under;
   the page receipt names each item by digest in `pageItems`, and the verifier checks the form
   of that list and nothing about its correspondence to the artifact. Which item a row came
   from is therefore a consumer's check by re-digest, not the verifier's finding. Whether a row
   should cite an item as well as its page is open.
3. **Binding to an outside format.** Whether a receipt, a record and an action receipt can be
   bound to OpenLineage or in-toto so that a consumer of either format reads the other, without
   weakening what the gateway's own verifier holds — a study, preregistered, with intervals.
4. **A JPS-level member.** Only if two independent runtimes write records that cite. Until then
   the grammar is the gateway's and the record member is the runtime's.
5. **The both-paths agreement.** The golden-record test ADR-0001 names is unbuilt, and
   [RFC 0003](0003-evidence-reference.md)'s two-back-end bar — two runtimes with different back
   ends resolving the same *references* — is not what the gateway's two adapters are: they
   acquire bytes for operator-named sources and resolve no pack reference. This record does
   not claim that bar met, and a later amendment to RFC 0003 must not cite it as if it did.
6. **Two engines on one store.** Stated as outside the executor's claim; whether it should be
   served, and by what (a store lock, a per-engine session prefix), is open.
7. **The bytes-of-a-line rule.** Digesting a `.jsonl` line by its bytes ties a citation to
   those bytes and to nothing about the book's order or history (step 6 searches every candidate
   under the directory). Whether a book should be allowed to be re-serialized under a recorded
   canonical form, at the cost of the verifier interpreting records, and whether a citation
   should bind position or sequence at all, are questions this record leaves open; for now the
   join is by bytes alone, and says so.
8. **Retrospective records under RFC 0000.** The cross-project provision speaks of visibility
   before an implementation exists. Whether it covers a record filed after the parts were built,
   as this one is, is a process question for the maintainer's disposition of this record.

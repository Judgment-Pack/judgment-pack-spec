# RFC 0023: Policy content and governing adoption

- Status: Review
- Type: Standards track, proposed companion at draft maturity
- Created: 2026-10-17
- Issue: [#211](https://github.com/Judgment-Pack/judgment-pack-spec/issues/211)

This is an open proposal, not part of JPS. It adds no released schema, conformance
class or execution authority. The [candidate contract](policy-companion-contract/README.md)
proposes exact format `1.0.0` at draft maturity; it is not adopted by being written.
The historical [prototype](policy-companion-prototype/README.md) remains explicitly
non-normative and byte-for-byte frozen at proposal `0.0.2`, baseline commit
`8a56a95d555c17640d2db4984363b779536b3c2a`. Host integration guidance below names separate
product responsibilities; acceptance of this RFC would not adopt those products'
protocols on their behalf.

## Summary

Propose a small domain-neutral companion for retained policy content and its exact
governing relationship to a consuming pack. Preserve the pack/graph as executable
authority. Policy text, review assertions and adoption describe intent, provenance
and governance; they introduce no condition language and do not change evaluator
precedence. Optional readable structured requirements are deferred from the first
candidate, whose closed grammar refuses a `requirements` member.

The proposed candidate supports pack consumers only. Composition with graphs needs
the relevant adopted graph contract and supporting hosts; this RFC does not
advertise standard Runner graph-job support. A Framework artifact is not required.
Collections can organize policies without implying dependency or priority.

## Problem

A policy may start as a document, be authored collaboratively, or be managed by
another system. It can remain effective while an executable interpretation is
developed or revised. A citation in a pack does not say whether that policy governs
execution, what exact policy version was interpreted, or what clauses remain
manual. A passing test does not establish complete coverage or approval.

Products can store these relationships privately, but then a second consumer cannot
distinguish a governing dependency from an informational reference or reconstruct
what exact content a review covered. Putting current permissions or mutable
publication state into Core would turn a portable evaluator into a governance
service, and still would not prove that a historical statement remains current.

The proposed boundary is immutable supplied-document meaning plus explicit limits.
The operational system owns authority and decides whether work may start now.

## Evidence

Three design cases motivate a shared form:

1. **Data access.** A platform team imports a sharing policy, reviews its clauses
   and implements release eligibility in a pack. Exact source/narrative bytes and
   interpretation must survive export. Policy withdrawal needs a live host gate;
   an offline content match cannot enforce it.
2. **Procurement.** An externally managed procurement policy publishes a new file
   revision. The consumer retains its existing adoption while reviewing the new
   revision. A changed file, missing file or access failure must not be inferred
   to mean approved, published or withdrawn.
3. **Refunds.** A local Desk admin authors, reviews and publishes a policy alone.
   The audit can truthfully record the same person performing those roles when
   the configured workflow permits it. It must not claim independent approval.
   Some clauses may remain manual; automated eligibility still lives in a pack.

The prototype supplies synthetic retained material for these domains. It is
design evidence only: no production policy approval, live enforcement, external
connector run or independent implementation agreement is claimed.

Existing Core sources/review metadata, retained Runtime/Runner artifacts and
Dialect provenance are prior boundaries to reuse, not proof this companion exists.
[RFC 0011](0011-judgment-currency-anchor.md) already explores retired pack versions
and an offline currency snapshot. It explicitly cannot establish real-time
currency or current authorization. This proposal does not adopt, supersede or move
that Draft's registry; its relationship to policy lifecycle remains a review item.
[RFC 0012](0012-witness-contract.md) and the accepted
[checkpoint witness companion](../spec/checkpoint-witness.md) concern supplied
history comparisons, not policy approval or a current permission to execute.

## Specification

### Proposed portable surface

The surface consists of **Policy content** and **Governing adoption**. The
[review candidate](policy-companion-contract/README.md) supplies self-contained
proposed prose, closed schemas, a bounded offline checker/capability record,
three retained-byte domain examples and reusable static positive/refusal vectors.
Both documents require exact `formatVersion: "1.0.0"`, with `kind: "policy"` or
`kind: "governing-adoption"`. The separate strict `x.y.z` artifact `version` does
not select grammar. No shared-major inference or integer/legacy alias is allowed.
This selector is proposed, not adopted, released or stable.

The frozen historical prototype uses its closed `prototype` wrapper with profile
`jps-policy-companion-prototype`, proposal `0.0.2` and status `non-normative`.
The candidate refuses that wrapper; no parser migration occurs. The
[explicit migration guide](policy-companion-contract/MIGRATION.md) preserves
source, narrative, interpretation and consumer bytes, requires new immutable
Policy/adoption identities and exact dependent references, retains originals and
requires dependent snapshot re-review. No approval or permission migrates.
The candidate's [prototype pin](policy-companion-contract/prototype-0.0.2-pin.json)
records the unchanged historical bytes.

A Policy contains:

- a stable absolute-URI identity, immutable artifact version and title;
- declared publication-management intent (`workspace-managed` or `externally-managed`),
  which does not authenticate a publisher or import its authority;
- a reference to exact retained UTF-8 narrative bytes;
- stable section identities anchored by half-open UTF-8 byte ranges in that exact
  narrative, plus explicit provenance references;
- retained original source references with provider/account/resource identity,
  nullable opaque source revision and original content identity.

The narrative can be authored directly or derived from original documents.
Original PDF/page/file bytes remain separate. An anchor in the narrative is not
an original-source offset, and a new extraction does not silently rewrite either.
No runtime conditions, live ACLs, publication states or approval booleans belong in
the immutable content. Optional readable structured requirements, including any
section-reference grammar, are deferred pending a concrete authoring/interchange
need and reference-check vectors. They are unsupported in the candidate. Any
future form must remain non-executable and requires an explicit selector change;
it must not introduce a second decision language.

A Governing adoption contains its own identity/version, the exact consuming pack
reference and one or more exact policy references. Every governing reference
declares whole-policy or explicit section scope, and per-section coverage:

| Coverage | Required interpretation |
| --- | --- |
| `implemented` | Exact typed consumer element references and retained interpretation/review basis |
| `manual` | Explicit responsible handoff/process |
| `awaiting-interpretation` | Unresolved meaning, with explanation |
| `awaiting-implementation` | Meaning agreed but automation not supplied, with explanation |
| `out-of-scope` | Explicit rationale; never silent omission |

The candidate resolves `{kind: "rule", id}` to Core `rules[]` and
`{kind: "exception", id}` to Core `exceptions[]`. The singleton references
`{kind: "applicability"}` and `{kind: "fallback"}` identify the actual Core
`applicability` and `fallbackOutcome` members; they have no fabricated ID. Absent
members, unknown IDs, duplicate references within one coverage record and
kind/ID confusion refuse. Fallback must name a declared, uniquely identified
outcome. These references identify supplied elements; they do not prove correct
interpretation or full Core semantic conformance. Evidence requirements, outcomes,
condition subelements and escalation are unsupported coverage kinds, as are graph
consumers. A clause implemented through scope, exception or fallback can reference
that actual element without inventing a dummy rule or a manual process.

Informational sources are separate and do not create governing dependencies.
Scope and coverage are declarations to be reviewed, not a language for conditional
authorization. Validation cannot prove that an organization declared every
applicable policy or that an interpretation is correct.

### Identity and offline checks

The proposed content reference is exact-byte SHA-256, byte length and media type.
Optional canonical document identity names its profile separately. Reuse the
existing [Dialect companion's `canon`](../spec/dialect.md) domain by explicit
reference: do not substitute JCS or preparation canonicalization. Existing pack
bytes are retained unchanged; no reserialization changes a pack's execution pin.

Artifact versions use the same lexical discipline as
[RFC 0021](0021-dialect-artifact-identity.md): exactly three unsigned decimal
components, no leading zeros except `0`, no suffixes or coercion, and the existing
256-ASCII-character bound. The candidate adds no bump arithmetic, compatibility
inference or version-reservation service. Draft CAS revisions, source revisions,
artifact versions and lifecycle revisions are separate values.

Readers check supported selectors, closed grammar, resource bounds, exact content
references, unique section identities, anchored UTF-8 boundaries and adoption
references within their declared scope. They refuse incomplete material rather
than silently treating it as approved. Identities are opaque references, not URLs
to fetch. Access and network acquisition require separate authority.

Candidate bounds retain the prototype's role-specific limits: parsed JSON is at
most 262,144 bytes, retained narrative/review/informational material at most
1,048,576 bytes each, and retained
original source material at most 4,194,304 bytes each. The fixture carrier loads at
most 16,777,216 distinct retained bytes in total; multiple registered media types
for identical bytes count once. An unsupported original size refuses the complete
bundle. Truncation, extraction substitution and silently dropping the original do
not produce a complete bundle. The parsed-document depth limit is 32; number
literals are at most 128 characters
with exponent magnitude at most 308. The candidate declares these limits explicitly;
they are not adopted Core limits or a stable content-size promise. Its refusal
objects use fixed bounded codes, never raw content. A malformed/missing selector
is `invalid-selector`; a well-formed unsupported selector is `unsupported-format`.
Physical/schema resource maxima report `input-over-bound`, separately from
reference, anchor, coverage and other semantic failures. Capability discovery lists
exact candidate format, proposed-draft maturity, features, limits and exclusions.

Consumer bytes are identified before adoption. A release can then bind the
consumer, adoption and supported dependency closure without circular hashes.
The host derives that closure from its reviewed registration, not from an
execution caller's possibly shortened list. Unsupported required composition
refuses. Policy citations alone cannot be upgraded into governing adoption.

### Review assertions and trust boundary

A review assertion needs the exact complete candidate, workflow revision,
reviewed scope/anchors, authenticated subject, decision time and authority basis.
Historical assertions cannot transfer silently to changed candidates. A section
approval does not replace an accountable whole-policy approval. Whether the same
local admin may author and approve is a workflow rule, not a universal spec ban.

The authentication/signature/export trust profile is unresolved. The candidate
therefore carries an exact interpretation basis, **not** portable proof of an
authorized sign-off. A hash, imported document, test report or model statement
must not be interpreted as that proof. No review-assertion conformance class is
introduced by this draft.

### Non-normative host integration boundaries

These are required product design considerations, not APIs standardized here:

| Boundary | Owning responsibility |
| --- | --- |
| Source observation | Gateway retains content/extraction and raw provider revision/lifecycle evidence; Desk interprets a configured authority mapping |
| Adoption | Desk records an authorized exact interpretation; Runtime checks supplied documents; Runner retains the registered dependency closure |
| Run/action admission | Desk's authoritative governance service decides current eligibility; Runner and actual action executors enforce at dispatch |
| Review/publication | Desk persists exact candidates, scoped sign-offs, immutable publication and idempotent receipts in transactional state |

Source state needs delivery identity, opaque source revision, observation time,
availability, retained bytes and explicit history completeness. The same bytes
with a new lifecycle assertion are a new observation. Persist snapshots/effects
before advancing cursors; duplicate/out-of-order delivery and cursor loss require
reconciliation. A source update does not overwrite drafts, transfer signatures or
upgrade pinned jobs. An unresolved update known before publication participates in
publication CAS; an update observed afterward creates impact review.

Publication, effectiveness, supersession, expiry and withdrawal are distinct.
Withdrawal defaults to blocking new dependent starts and later external actions.
The authority serializes withdrawal with start commitment: withdrawal first blocks
the start; commitment first admits the existing attempt. This is a logical
authorization boundary, not atomicity with a remote side effect or instantaneous
knowledge of unobserved upstream changes. Required unavailable/stale authority
holds new governed work. An already dispatched external action may be irreversible.

An eligibility preview is not a dispatch grant. Executors bind durable attempt,
resource, payload, release and epoch identities before requesting a start. A
recovered receipt is history, not a reusable permission to dispatch. Lost responses,
crashes and restored backups require reconciliation/fencing; uncertain external
operations must not be replayed. Offline pinned snapshots cannot establish these
live guarantees, so the Runtime offline reader does not implement that service.

Local Desk can be the authority for one admin's complete policy lifecycle. Team
identity, invitations and separate reviewers extend that host mode; they do not
need to be fabricated to enable honest single-person management. Gateway consumes
admission decisions at its action boundary and does not become policy authority.

## Alternatives

- **No change/product-only metadata:** sufficient for a private editor but leaves
  cross-product policy identity, coverage and governing/citation distinctions
  ambiguous. Keep IAM, review routing and live lifecycle product-owned regardless.
- **Core extension/profile:** would couple governance to evaluation and does not
  supply a live authority. Existing packs must remain usable without policies.
- **Adopt a universal control format:** OSCAL and other domain formats can support
  adapters, but requiring one narrows a domain-neutral product and introduces
  unnecessary control semantics. No normative mappings are proposed here.
- **Make readable requirements authoritative:** creates competing execution
  semantics. Defer optional readable requirements from this candidate; any later
  form must keep the pack/graph authoritative.
- **Use only pack-version currency:** RFC 0011's offline membership question is
  useful but different from policy content, adoption scope and current permissions.
- **Mandate frameworks:** organizing collections do not need another release type
  or implicit policy priority. Revisit only for a concrete interoperability need.

## Compatibility

No Core, Dialect, preparation, graph or released conformance bytes change. The
0.0.2 prototype remains unchanged. Candidate documents are opt-in; unsupported
readers refuse them, and format compatibility cannot be inferred from artifact
version arithmetic. Migrating a citation to a governing
dependency is a reviewed new adoption, never automatic import behavior.

Published policy content and consuming releases remain immutable. Renaming a
title or moving a folder does not change stored execution pins. A fork has a new
identity and fresh authority; imported approval history does not grant local roles.
Upgrading an existing job is explicit and retains historical runs. Supersession
alone does not declare every older pin ineligible; the adopted host rules decide.

## Security and privacy

Content identity does not establish truth, authority, current access or currency.
Prevent ambiguous JSON, oversized material, malformed versions, anchor substitution,
missing governing dependencies, imported approval booleans and cross-tenant
reference disclosure. Bound originals, narrative and interpretation separately.
Enforce current access in indexes, counts, exports and AI retrieval as well as pages.

Model output can suggest content but cannot sign as an invited reviewer or change
test expectations merely to obtain passing outcomes. Restore of an old local store
cannot prove that no later withdrawal/revocation occurred. An unavailable external
file or failed sync is not itself withdrawal. Cryptographic signatures, if added,
will still need trusted identity and freshness rules; they do not resolve these
questions merely by verifying mathematically.

## Conformance

The candidate reader result is limited to supplied-document validity and reference
agreement under exact proposed format `1.0.0`. Its reusable manifest supplies
positive, refusal, boundary and adversarial vectors with exact expected objects,
including malformed/unsupported selectors, independent artifact versions, aliases,
missing or stale byte references, optional canonical identities, section anchors,
UTF-8 boundaries, scope/coverage mismatches and governing-versus-informational
references. Runtime or other ports can execute retained static bytes directly; the
only generation grammar repeats one declared byte for a declared length.

The candidate and frozen prototype checks are experimental agreement aids, not
released corpus entries.
They must not be scored as proofs of authorization, complete policy coverage,
live admission or independent interoperability.

Host acceptance tests belong in their owning repositories: source update racing
publication; same bytes with changed lifecycle; revoked reviewer/access after
indexing; dependency omission; withdrawal-before-start; start-before-withdrawal
followed by refused action; lost response recovery; worker fencing; and restore
from a pre-withdrawal backup. A signed historical snapshot cannot satisfy these
live tests by itself.

## Implementation

Spec owns the eventual portable companion, exact reference meanings and staged
vectors. Runtime should expose shared offline validation/canonical/reference
tooling only for an explicitly adopted or clearly experimental capability. Desk
owns local/team lifecycle, durable review transactions, sync state, Library and
shared UI/chat handlers. Gateway owns provider observations and execution-boundary
enforcement. Runner owns frozen releases, closure and current start admission.
Exchange can publish reusable definitions only after its entry contract supports
them; it does not store private tenant approvals. Demo and evaluator studies
exercise these boundaries without becoming alternate production services.

Two plausible independently authored readers are a Runtime-backed local tool and
a separate organizational policy service validating exported bundles without Desk.
They would compare exact retained bytes and declared references and explicitly
decline live-authorization claims. Two language ports by this project's author
would not demonstrate independent authorship. That evidence is not available yet.

The first product path is single-admin local policy management. Its explicit
review can be self-review; later team deployments can require another reviewer.
Manual and chat actions must share the existing execution/context/approval/CAS
boundaries. No feature-specific model loop, permission inference or retry service
is required by this RFC.

## Unresolved questions

1. Adoption/disposition of the exact proposed `1.0.0` selector, declared bounds and
   closed reference/coverage grammar after public review; no released schema or
   conformance class is assigned here.
2. Trust/signature/export profile for review assertions and cross-workspace adoption.
3. Reconciliation with RFC 0011's proposed pack currency registry without silently
   adopting it or treating offline membership as live authorization.
4. First real sync provider and its demonstrable revision/lifecycle/freshness
   semantics; document-read support alone is insufficient.
5. Host defaults for self-review versus independent review, quorum changes,
   role-revocation effects on old signatures, expiry/grace and scheduled publication.
6. Supported graph/composition closure and its owning execution contract.
7. Independent implementation evidence and any domain-format adapter demand.

Moving this RFC to `Review` requests public comment; it does not mark it
`Accepted` or waive the public-comment process. The candidate supplies no
cross-vendor adversarial-review record or independent implementation evidence.
Review-assertion trust, Graph support and adoption remain unresolved. This proposal
must not be described as adopted, stable or implementation-complete on that basis.

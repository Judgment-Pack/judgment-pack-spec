# RFC 0018: The dialect

- Status: Accepted
- Type: Standards track (a companion document of the specification, with a reader conformance class
  and a vector corpus of its own)
- Created: 2026-10-14
- Accepted: 2026-10-15
- Amended: 2026-10-15 (every gateway source shape, in version 2; the unbound source form, in
  version 3; research replay; version 3 as the reference Runner reads it, its two vectors staged;
  the research result contract, binding, reconciliation and fixture lists, issue #171)
- Issue: [#141](https://github.com/Judgment-Pack/judgment-pack-spec/issues/141); the direction it
  serves is [#142](https://github.com/Judgment-Pack/judgment-pack-spec/issues/142)

> **Adoption record.** This RFC is accepted by the single maintainer under the interim review
> regime ([RFC 0009](0009-interim-review-regime.md)), at draft maturity. The maintainer recorded the
> decision on issue [#141](https://github.com/Judgment-Pack/judgment-pack-spec/issues/141) on
> 2026-10-15. The evidence is what Evidence below records: two preparation verifiers agree on the
> nine vectors, the second written from the text alone under a recorded protocol and in another
> language, and the reference Runner's `verify-run` is a third reader of the same bytes. The
> review rounds are recorded on the pull requests that made them and under
> [`rfcs/reviews/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/rfcs/reviews):
> the proposal's, on [pull request 144](https://github.com/Judgment-Pack/judgment-pack-spec/pull/144),
> as `0018-round-1.md`; the second reader's, on
> [pull request 145](https://github.com/Judgment-Pack/judgment-pack-spec/pull/145), as
> `0018-round-2.md`; the amendment that decided in the text the six choices the readers recorded, on
> [pull request 148](https://github.com/Judgment-Pack/judgment-pack-spec/pull/148), as
> `0018-round-3.md`; and the review of this acceptance, with a written disposition for every
> finding, on the pull request that makes it, recorded under `rfcs/reviews/` as `0018-round-4.md`.
>
> **What lands, and when.** The text under Specification, §§1–14, lands now as the companion
> document [`spec/dialect.md`](../spec/dialect.md), normative for the preparation-verifier reader
> class and for nothing else, beside the released Core `0.2.0-draft`, which it does not change. The
> nine vectors, already in this repository under `conformance/dialect/` and unchanged, stay
> **staged** until the next `specVersion` opens, as RFC 0013's rows and RFC 0017's vectors are: they
> are in no corpus, no claim may cite them, the site does not serve them, and no release bundle
> carries them; they are held to the same repository checks and can be run by hand. When that
> version opens they move into a corpus, normative for the reader class only, and Core §1.1's list
> of normative artifacts gains them. Of the texts Compatibility names for acceptance, they all
> change now except the vectors' corpus, which waits with them: Core §1.1's list gains the
> companion document, its `export-ignore` is removed, the site publishes it as a page of its own,
> and the architecture vision's sentence that nothing in the input-lineage research line is part of
> JPS gains the companion document as a second exception. Until a specification version publishes the vectors, no preparation-verifier conformance
> claim is available: §14 holds a verifier to the vectors published with the version its claim
> names, and no version publishes these. Whether the vectors take a `suiteVersion` of their own
> stays open (Unresolved 6). The paragraphs below describe the draft as it was proposed; the
> companion document is now the normative text, and Core §1.1 makes an RFC informative in any case.
>
> **Departures this acceptance discloses.** [RFC 0000](0000-rfc-process.md) names a comment period
> before acceptance. The maintainer waived it, because the project has no outside readers yet; it
> was not run, and this is a departure from that process, not a formality it has met by another
> route (Unresolved 9). The evidence bar's independence also rests on less than separate
> organisations: both readers are this project's, written by agents of one model, and the first
> reader's author is the text's, with the vectors in view; the second's independence rests on the
> recorded protocol and on its different language (Evidence, "The standing of that evidence").
> And the record of the proposal's review lapsed in one respect, which this pull request mends:
> the round of pull request 144 was recorded only on that pull request, as two comments, and not
> under `rfcs/reviews/`; this pull request copies it, with the rounds of pull requests 145 and 148,
> verbatim, so that all three are in the repository.
>
> **The decision this records.** Issue #141 asked whether the input mapping and the preparation the
> reference Runner defines become part of the specification as a companion document, normative for a
> new reader class, the *preparation verifier*, and for nothing else. The maintainer's decision of
> 2026-10-14, recorded on the issue, names the companion document the **dialect**, not the input
> dialect, and scopes it to every way a pack's facts and evidence are obtained and derived — an
> AI-assisted research recipe, an API call with its request body and header configuration, an MCP
> query, a SQL statement, and the other data integrations the gateway's sources and connections
> admit, each declared and pinned — with the derivations into facts and evidence availability, the
> calculated values with their lineage, and an output side. A reader recomputes what is recomputable
> and holds the rest by its recorded digest, so what a dialect establishes differs by part, and this
> RFC states it per part. Issue #142 records the direction it serves: dialects published in the
> Judgment Exchange. This RFC is the proposal that decision calls for. Taking the format up decides
> where it belongs; it does not accept this text, which becomes normative only when this RFC is
> accepted, by [RFC 0000](0000-rfc-process.md)'s process and under the
> [interim review regime](../GOVERNANCE.md#interim-review-regime).
>
> **What this draft adds, and what it does not.** Three things are added with this draft, none of
> them normative. The text under Specification, §§1–14, is added too as the proposed companion
> document
> [`spec/dialect.md`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/spec/dialect.md),
> word for word, so that a second reader could be written from a document of its own. The Runner's
> nine preparation vectors are added byte for byte, **staged**, in
> [`conformance/dialect/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/dialect).
> And a first reader, `tools/dialect_verify.py`, is added, with tests that run it over every
> vector; a second, `tools/dialect-verify-ts/`, written from the companion document alone, followed
> (Evidence). While this RFC is a draft the companion document is normative for nothing: Core §1.1 does
> not list it, the site publishes its text only as this RFC, and no release bundle carries it or the
> vectors (`.gitattributes`, `export-ignore`). That departs from [RFC 0017](0017-checkpoint-witness-statement.md),
> whose companion document was added when it was accepted; the reason is the second reader, which
> [RFC 0000](0000-rfc-process.md)'s evidence bar asks for before acceptance and which is written
> from a document. Nothing here changes Core `0.2.0-draft`, its schema, its four conformance classes
> or either of its corpora, and nothing asks the Runner, the runtime or the gateway to change.
>
> **The source.** The Runner's
> [`docs/MAPPING-V2.md`](https://github.com/Judgment-Pack/judgment-pack-runner/blob/05636eda96a9588279d61a6272625be859a28117/docs/MAPPING-V2.md)
> at commit `05636eda96a9588279d61a6272625be859a28117`, the head of the Runner's pull request 77,
> which publishes the vectors for a second reader; the vectors were copied from that commit, and the
> pull request reached the Runner's `main` as commit `82116bfab7705f74ca3e493c9722dd3831c7418f`,
> with the same files. Its subsection "The canonical form of a
> preparation" is taken up as the normative text, so that `MAPPING-V2.md` can point here when this
> RFC is accepted. Beside it: the Runner's design record for calculated values; the portable
> derivation rule, at the experiments repository's commit `96fa95874bfaa4d5a01c0c111fd8b5b6613c881c`,
> which the Runner vendors; the reference gateway's `SPEC.md` at `v0.15.0` (§1.1, §1.2a, §6) and its
> engine configuration's `decisionPolicy`; and the reference runtime's ADR-0050. "Runner, *name*"
> and "gateway §n" in the Specification mean those documents at those commits.

## Amendment of 2026-10-15: every gateway source shape, and the unbound source form

This amendment changes the accepted text in place, as the gateway amends its records: the
Specification below, and the companion document with it, say what it decided, and the sections
after the Specification say what changed. The status stays Accepted. The maintainer's decisions
are recorded on the pull request that makes it,
[pull request 151](https://github.com/Judgment-Pack/judgment-pack-spec/pull/151), and its review is
round 5 of this RFC, recorded under
[`rfcs/reviews/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/rfcs/reviews) as
`0018-round-5.md` with the maintainer's disposition of each finding; the two findings accepted there
are applied below.

**Where it comes from.** The maintainer's decision of 2026-10-14 on issue
[#141](https://github.com/Judgment-Pack/judgment-pack-spec/issues/141) scoped dialect version 3
from what the drafting of [RFC 0019](0019-exchange.md) surfaced, its unresolved questions 7 and 8:
a published dialect pins the installation its fixtures were recorded under, and neither seed entry
of the Exchange, which read the gateway's Databricks and Azure DevOps connections, sources of shape
`http`, could be prepared. Two parts of that scope are specified here. The third, that an entry of
direction `both` holds two documents, is the Exchange's entry format
([exchange #2](https://github.com/Judgment-Pack/judgment-pack-exchange/issues/2)) and changes
nothing in this document. The Runner's side is
[runner #79](https://github.com/Judgment-Pack/judgment-pack-runner/issues/79), done by the Runner's
pull request 80, merged as `c84e8e64e5d30c835f8d8e6370cd48e2bfd35ee9`: its mapping v2, kept at
version 2, reads a retained record of shape `airbyte`, `mcp` or `http` alike, and it published a
tenth vector, `http-shaped-source`.

**The first decision: every gateway source shape, in version 2.** The scope named the broadening
version 3's. The Runner made it in mapping v2 without a version bump, so the tenth vector's dialect
and its preparation both carry `version` 2; and this document's version 2 is the Runner's mapping
v2 byte for byte (§2). The maintainer decided that version 2 follows it. An `operation`'s profile
may be of shape `airbyte`, `mcp` or `http`; the record's `acquisition.shape` must be the profile's,
as §5.2 already held; and what the request must be follows the shape (§4.1). For `mcp` it is the
tool call `{tool, arguments}`, as before. For `http` and `airbyte` it is the request the gateway
source of that shape takes, as its adapter or connection defines it — `adapter-http`'s `{method,
path, query, body}`, as the tenth vector carries one; a connection's `{connection, revision, read,
…}`; `adapter-airbyte`'s stream read — held to being an object, to the template rules every request
has and to the receipt's commitment to it, and not to a set of members; under `adapter-http`, a
`query`, when present, is an object of string templates. The shape `airbyte` is defined and not
claimable: that adapter answers every read with a page, a paged acquisition is refused, and so no
`airbyte` vector exists. The maintainer decided the widening of `http` and `airbyte` on 2026-10-15,
before this amendment's review round, in place of a fixed `{method, path, query}` form that
admitted neither `adapter-http`'s `body` nor the gateway's connections (Unresolved question 12).
The derivations, the calculated values, the lineage, the canonical form and the digest are those of
every shape: the Runner's pull request 80 showed that a preparation's bytes do not depend on its
source's shape, and the tenth vector's preparation has the form of the other nine.

**The second decision: the unbound source form, in version 3.** A dialect may be published
unbound: its `operation` names, in place of a profile's id and digest, the catalog platform and
operation it is read through, the shape that serves it and the record it is written against
(§4.4). A binding document, closed and digested as every document here is, maps each unbound source
by its name to a profile of the installation's gateway. The bound dialect is a document of version
3, and its digest is what a preparation of it records; the published dialect's digest, an Exchange
entry's `dialect.digest` (RFC 0019 §3), is the unbound one's. A reader given an unbound dialect and
its binding document verifies the bound form, and a fixture of an unbound dialect carries the
binding document it was recorded under. What the form establishes is nothing beyond version 2's:
the binding document is the installation's statement of which profile each source was bound to. A
preparation commits the bound dialect, its profile assignments included, under the installation's
own key when a record binds the preparation; it commits neither the binding document's digest, nor
the published dialect's digest, nor the catalog names the binding removes, so a record cannot name
the published identity (Unresolved question 13; review round 5, finding 2). Version 3 keeps the
four kinds of §4.3. No Runner reads version 3, so none records a bound dialect's digest yet, and no
vector holds the form: it is defined, and not claimable, as the staging README says.

**What changes for a reader of version 2.** This changes accepted text of version 2 in two
ways: a compatible extension of the record kind to every adapter shape, and one restriction (review
round 5, finding 1). The extension: every version-2 dialect that was well-formed stays well-formed,
the nine vectors are unchanged with their answers, and what is new is read only where it was
refused before, an `operation` under a profile of shape `airbyte` or `http`. The restriction: a
receipt that attests a page (`E.acquisition.pageItems`), of any shape, is `acquisition-invalid`
(§5.2). It changes one answer the accepted text gave, and only one: a signed acquisition of shape
`mcp` whose receipt carried `pageItems` was a reading, and is refused now. The rule stays, because
the reference Runner has never prepared a paged acquisition, so no preparation over one exists to
verify, and no vector holds one. A dialect of version 3, which a
verifier refused as `input-malformed`, is refused by one that does not read version 3 as
`version-unread` (§11). And one rule is narrower than the Runner's: the Runner holds a request under
a profile of shape `http` to the template rules alone, and this text holds a `query` under a profile
whose adapter is `adapter-http` to string templates as well (§2, §4.1).

**The evidence.** Both readers read version 2's `operation` of shapes `airbyte`, `mcp` and `http`
now, and both refuse version 3 as `version-unread`, naming the unbound form, and take no binding
document. Both extensions were written by one author, from the text, on the pull request that makes
this amendment; both readers recompute the tenth vector's preparation byte for byte and give it the
answer the manifest records, a reading whose binding `matches`, as the Runner's `verify-run`
reports. The second reader's recorded independence covers the text as accepted on 2026-10-15; the
extension's implementation in both readers is one author's, so for the extension the two readers'
agreement is not independent. A reader by another author, written from the text, can close that
later.

**What it leaves open.** Unresolved questions 1 and 2 are updated, and 10 to 12 added: a vector of
shape `airbyte`; a vector of the unbound form, which needs a Runner that reads version 3 and binds a
dialect at import; the requests of `http`-shaped sources that are not `adapter-http`'s, resolved
by the maintainer's decision of 2026-10-15; and, added with 13 after review round 5, whether the
published dialect's and the binding document's digests should be carried in the committed form.
The `research`, `http`, `sql` and `web` kinds still have no preparer.

## Amendment of 2026-10-15: research replay

This amendment records the maintainer's decision of 2026-10-15, filed as issue
[#161](https://github.com/Judgment-Pack/judgment-pack-spec/issues/161), on
[pull request 164](https://github.com/Judgment-Pack/judgment-pack-spec/pull/164). Its review is
round 6 of this RFC, `0018-round-6.md`; the maintainer accepted all seven MEDIUM and five LOW
findings, applied below. The status stays Accepted.

A `research` source's acquisition is the research record `R` the caller assembles, carried as
`response.result`. Its `responses` array retains the AI connection's answers and the web reads
retained with it, each with its own profile reference, request, result, receipt and salts. The
verifier checks each response under its own trusted profile and over its own request, including
times and sessions, in the record's order. The record's own receipt and salts are present when it
came back through a gateway source, and absent otherwise. The read applies to `R`. Membership and
order are the caller's assertion; a missing named response is `acquisition-missing`, an unnamed
retained response is `acquisition-unexpected`, and a failed digest or receipt check is
`acquisition-invalid` (§4.3, §5.2, §11).

The recipe's `question`, `constraints`, `model` and `evidence` are recorded in the dialect and
under its digest, never re-executed. The model's and the connection's names are recorded and
checked against nothing a verifier is given. No model output is produced or compared. Every
retained response's citation, then the record's own when present, enters `cites` and version 3's
lineage member `receipts` (§9). A page cited by URL alone is no retained response; the claim it
supports is the answer's say (§13). At most 64 responses are retained per research source (§12).
The later research-contract amendment adds profile compatibility checks for declared model and
capabilities; this round's replay rule and its limits on what verification establishes remain.

The research replay rule and fixture layout are fixed, and marked as positions no vector decides;
§11 states the layout in the staging README's terms, with the expected answer in the staging
manifest. No vector is added, and the Evidence is unchanged. The first fixture waits for a
preparer of the `research` kind (Unresolved questions 1–3 and 14).

## Amendment of 2026-10-15: version 3 as the reference Runner reads it

This amendment records the maintainer's decisions of 2026-10-15 on
[pull request 167](https://github.com/Judgment-Pack/judgment-pack-spec/pull/167), which stages the
Runner's eleventh and twelfth vectors and extends both readers to version 3. Its review is round 7
of this RFC, recorded under
[`rfcs/reviews/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/rfcs/reviews) as
`0018-round-7.md` with the maintainer's disposition of each finding; the seven findings accepted
there are applied below. The status stays Accepted.

**Where it comes from.** The reference Runner reads version 3 since its pull request 83, merged as
`89cf44109ad3a9862ab0386811bef63d8a9a1657` and released in `v0.12.0`
([runner #82](https://github.com/Judgment-Pack/judgment-pack-runner/issues/82)). It prepares an
`operation` of version 3, bound or unbound and bound at import through a binding document the
operator supplies, and a `selected-file`, as it prepares version 2's, and it refuses `http`,
`sql`, `web` and `research` by name. It published two vectors of version 3: `version-3-bound`, the
calculated run's dialect written as version 3, and `unbound-bound-at-import`, a dialect published
unbound with its binding document and the bound dialect the Runner made of them. Both are staged
here byte for byte, and both readers give each a reading whose binding `matches`.

**The first decision: the text says what is now so.** Sentences that said no Runner reads version
3, no preparer writes it and no vector holds it are corrected to the present: §2, §4 (its table and
what the staged vectors exercise), §4.3, per kind (`operation` and `selected-file` are prepared;
`http`, `sql`, `web` and `research` are refused by name, and no vector holds them), §4.4 (the
Runner writes the form, and one vector holds it), and the companion document's Status. §14's claim
form admits a claim of dialect version 3 beside version 2. No rule a reader applies changes with
these sentences.

**The second decision: version 3 is written one way** (§2). `provider`, `facts` and `evidence` are
members of version 2 alone: a document of version 3 that names one is refused, `input-malformed`.
And version 3 is held to the Runner's encoding rule: a member its encoding leaves out when empty —
`sources`, `unmapped` and `unmappedEvidence` written as `[]`, the case's and a source's `parameters`
and `admits`' `facts` and `evidence` written as `{}` — is refused written empty, since the Runner
keeps a document of version 3 only as its encoding writes it. Every other member written empty is
read, as the Runner reads it: `admits`, a copy's arrays, and the kinds' members, `query`, `body`
and `headers` among them (review round 7, finding 2, which corrected a first list that was not the
Runner's). This changes no answer a vector gives. Before this pull request no verifier read version
3, so no answer an accepted text gave changes either. No vector decides either refusal.

**The review's findings, applied.** Round 7 found that the text and both readers differed from the
Runner in two rules more, and the maintainer decided both as the Runner has them. `cites` is
ordered by `callIndex` in versions 2 and 3 alike (§9.1), as the Runner writes it; the order in
`sources` the first draft of this amendment gave version 3 stays the rule of a preparation with a
`research` source, that kind's own, which no vector holds. And a copy's `facts` and `evidence` are
both required, in every version (§6.2), as the Runner requires them ("copy requires facts and
evidence arrays"). That changes one answer the accepted text gave: a copy that left an array out
was read, and is refused now; the Runner has never read one, so no preparation over one exists. The
round found three refusals more that the text already gave and the readers did not make, now made
by both: a binding document supplied as `null` (§4.4, §11); more than 64 retained responses in a
research record (§12), counted before any form; and a `research` source's acquisition held to its
own form (§§4.3, 5.2), its envelope admitted without a receipt and salts of its own, one of the two
alone refused, and the research record and each retained response held to their forms before the
kind is refused as unread.

**The third decision: two readings, recorded.** Where the text names a member of a version-3 kind
without its form, both readers take one reading, and no vector holds it (Evidence, "What writing
the readers found"). The member definitions are unchanged.

**The evidence.** Both readers' version-3 reading, the two refusals above among it, was written by
one author, who had read both, from the text. For the eleventh and twelfth vectors, as for the
tenth, the two readers' agreement is that author's and not independent. Unresolved question 11 is
resolved, and question 2 updated.

## Amendment of 2026-10-15: the portable research contract

This amendment records the maintainer's four decisions on
[issue #171](https://github.com/Judgment-Pack/judgment-pack-spec/issues/171), on
[pull request 173](https://github.com/Judgment-Pack/judgment-pack-spec/pull/173),
**RFC 0018: portable research contracts**. Its review is round 8 of this RFC, recorded as
[`0018-round-8.md`][round-8] under
[`rfcs/reviews/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/rfcs/reviews),
with the maintainer's disposition of each finding, as round 7 is recorded there. All seven
MEDIUM and five LOW findings are accepted and applied below. The status stays Accepted.

[round-8]:
  https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/rfcs/reviews/0018-round-8.md

**Where it comes from.** The evidence is the maintainer's review of the Desk's GTM recipe
([issue #171](https://github.com/Judgment-Pack/judgment-pack-spec/issues/171)), dated 2026-10-15:
requested fields, acquisition requirements and their derivation must travel with a recipe, while
connection identifiers and workspace state belong to the installation. The
requested fields and typed observations described there motivate §4.3, not an import of the
Desk's workspace schema. The Desk's `web/src/research/ledger.ts` ([source][desk-ledger]) at commit
`6b8a46c` retains search and page requests, exact responses, receipts and excerpts, and
distinguishes retrieval time from a page's claimed dates. Its `web/src/research/run.ts`
([source][desk-run]) at the same commit traces citations to retained excerpts and writes a
`researchRecord` with source responses and citations. Those files are evidence of retention and
citation handling; they do not implement this result contract or a
company/person workflow. The Runner's `docs/MAPPING-V2.md` at `89cf441`, "Dialect version 3",
supplies the operation binding model extended here and still refuses `research` by name.

[desk-ledger]:
  https://github.com/Judgment-Pack/judgment-pack-desk/blob/6b8a46c/web/src/research/ledger.ts
[desk-run]:
  https://github.com/Judgment-Pack/judgment-pack-desk/blob/6b8a46c/web/src/research/run.ts

**The four decisions.** The result contract is an ordered, bounded `fields` declaration, with
six exact encodings and a per-field answer in `R.fields`: required means an answer entry, not a
fabricated value, and found and conflicting observations cite retained responses (§4.3). The
binding form publishes a model and capability requirements, then assigns generated AI and web
profiles by id and digest; incompatible declarations give `profile-mismatch` (§4.4, §5.1).
Reconciliation keeps §8.1's prohibition of overlapping targets and gives a research rule one
bounded form for reading earlier research results, with declared precedence and treatment of
missing, stale and conflicting observations (§6.4). Finally, §11 gives two fixture lists, a
GTM company/person pair and work-item triage, including binding and retained-response changes
and the selected parent/child case of [RFC 0020](0020-workflow.md) §11; none is recorded.

The result and binding members enter the dialect's canonical digest; the preparation still
commits the bound document alone. Profile capability declarations enter profile digests, while
field entries and their citation indices enter the research record's bytes. Without a receipt
for that whole record, an unread field can change without changing the preparation; the text
states that limit. Version 3's one-spelling rule, operation binding and the preparation's form
stay unchanged. Every new refusal uses an existing code, and every new maximum is finite.

This resolves the dialect's research binding question deferred by issue #160 (Unresolved
question 15). Workflow version 1 still admits no stage whose dialect has a research source;
RFC 0020's contrary binding statements await its own revision, as fixture 8 and question 15
record. Its version-1 operation construction and required two-stage demonstration remain. Its stage
outputs still come from prepared facts, and its selected payload projects into the next case
under its own rules; no workflow or record-collection member is added to a dialect.

The replay mechanism adopted in pull request 164 remains: verification replays retained
responses under the profiles then bound and never asks a model or the web again. `evidence`
keeps its accepted form, an array of non-empty strings. Three answers the accepted text gave
change. A research source of pull request 164's form without `fields` or `capabilities`,
previously well-formed, is now `input-malformed`. A research record without `fields`, previously
well-formed, is now `input-malformed`. A retained response through a trusted but unassigned
profile, previously read, now gives `profile-mismatch`.

Section 13's table is reformatted as a list, with the text unchanged but for the `generated`
item. The new profile checks compare declared model and capabilities; they establish neither
which model actually ran nor that its answer is right (§13). No Runner prepares this kind,
and no research vector exists.
The readers followed in the pull request for issue #176, as pull request 167 followed 164: both
read this contract since, extended by one author who had read both. This amendment changes the
contract and fixture plans only.

## Summary

A **dialect** is a pack's terms spoken in a system's: the declared, reusable translation between a
system and a pack. Its input side says how the facts and the evidence availability a pack's
evaluation takes are obtained — from sources, each a declared acquisition of one kind, pinned so
that a reader can hold the bytes it produced by their digest — and how they are derived from those
bytes: case and source parameters, copies and derivation rules, calculated values with their
lineage, and the classes each target admits. Its optional output side says how a disposition
becomes the arguments of a write, as the gateway's decision policy does. Applying the input side at
one instant to a case and to concrete acquisitions produces a **preparation**: what each target was
derived from, under which receipt, at which instant, in a canonical form whose SHA-256 is the digest
the Runner passes the runtime and the runtime records as the evaluation record's binding.

This RFC proposes the dialect as a companion document of the specification, with one reader
conformance class, the *preparation verifier*, which recomputes a preparation from the dialect, the
case, the acquisitions and the input profiles it trusts, and holds a record's binding to it.
Version 2 of the dialect document is the Runner's mapping v2, byte for byte, and the preparation's
canonical form is the Runner's, stated here. Version 3, which the reference Runner reads, adds an
unbound form of an `operation`, bound at import, and four source kinds more — `http`, `sql`, `web`
and `research` — defined and not claimable, since nothing implements them and no vector holds
them. The research-contract amendment adds typed research fields, generated AI and web bindings,
and declared reconciliation over earlier research results; no preparation or vector is claimed.
The output side is defined by reference to the gateway's decision policy, its vectors deferred to
a later RFC.

What a preparation establishes is stated per part. A derivation is recomputable, and a verifier
that recomputes it establishes it itself. An acquisition's bytes are not: they are held by their
digest, and what they establish is the gateway receipt's business, byte lineage and not truth. A
research record establishes the least of all. The Runner's twelve vectors are staged byte for byte.
Two readers, each written from the text, the second without sight of the first, recompute all
twelve preparations byte for byte, the last three through extensions one author made to both, and
give every vector the same answer, and their reports agree with the
Runner's on the surface they share, the verification of a preparation; the one check they leave out,
of an export's retained result against its record, is the export's, not a preparation's.

## Problem

Core §8.2 takes one facts document and one evidence-availability document, and "defines no fact
namespace, merging, or acquisition". That boundary is right for Core, and nothing here moves it. But
a record now commits to how those documents were made. The reference runtime records a caller's
binding on the evaluation record, as given and never interpreted (runtime ADR-0050), and for a run
the Runner prepared, that binding is the SHA-256 of the Runner's preparation in the Runner's
canonical form. Today only the Runner's own verifier, `verify-run`, can read a preparation and hold a
record's binding to it. A third party that holds a record, its receipts and a preparation — the
counterparty, an auditor — cannot check the binding without the Runner's code and the Runner's words,
which describe one implementation, move with its releases, and sit beside its service, its exports
and its journal.

Two more parties need the format to be nobody's code. The Desk's inputs — import recipes, selected
records, and the research line's recipes and research records (Desk #369, #371) — produce mappings
and hand them to the Runner, and each new kind of input is today a change to the Runner with no
stated format. And the Judgment Exchange (#142) is to hold dialects as published entries, each
verified by running it on its fixtures: an entry whose input side is one program's convention can be
verified by no one else.

The [RFC index](README.md) states the rule this record applies: "A format that independent tools must
agree on is a candidate for the specification. An algorithm or engine belongs to a runtime. A hosted
service belongs to a product." The dialect and its preparation are the first kind. The Runner's
service — its jobs, exports and journal — and the gateway's acquisition are the others, and are
cited here, not taken up.

The checkpoint witness statement was in the same situation while it lived only in the gateway's
`SPEC.md`, and [RFC 0017](0017-checkpoint-witness-statement.md) resolved it by taking the format up as
a companion document, with the gateway's vectors byte for byte. The same move applies here.

## Evidence

- **The format, in use.** The Runner's mapping v2 is "implemented in Runner and Desk's advanced Jobs
  mapping workflow" (`MAPPING-V2.md`): typed case and source parameters; `operation` sources pinned
  by an installation's input profile and its digest, with a maximum age; copies and the vendored
  derivation rule; calculated values (the Runner's issue #14); admission by class. The Runner passes
  the preparation's binding to the runtime on every operational evaluation since its `v0.9.0`, and
  the runtime records it since its `v0.31.0` (ADR-0050).
- **The vectors.** Twelve, generated by the Runner from fixtures its tests write with a released
  runtime, and frozen: the Runner calls them "hand-maintained normative data". Two of the Runner's
  tests hold it to them, byte for byte, and run `verify-run` on each. They are a calculated run,
  signed, witnessed and bound; the same recomputed a second later; a record from before the binding;
  a binding of another scheme; altered lineage; a retained result that differs from its record; two
  sources whose rules read parameters no receipt commits; a case-only run with the characters the
  canonical form escapes; the case parameters `-0`, 2⁵³−1 and −(2⁵³−1), kept as written; and, added
  since, one source of shape `http` (`http-shaped-source`), and the first two of dialect version 3:
  the calculated run's dialect written as version 3 (`version-3-bound`), and a dialect published
  unbound and bound at import with its binding document (`unbound-bound-at-import`).
- **Two readers, from the text.** Two preparation verifiers in this repository are written from the
  companion document's text, and they agree on all twelve staged vectors byte for byte: each
  recomputes every vector's preparation equal to its `preparation.json`, with the digest its
  `preparation.sha256` states, and gives every vector the answer the staged manifest records; on the
  eight vectors that are readings, their reports are equal. On the tenth, and on the eleventh and
  twelfth, `version-3-bound` and `unbound-bound-at-import`, that agreement is one author's: each
  reader was extended to them by one author who had read both (Implementation). The first
  reader's reports agree, wherever
  the class reports them, with `verify-run`'s on `targetsByClass`, `unsignedParameters` and
  `unsignedFreshness`, and with the export on the facts and evidence-availability documents.
  - The first, `tools/dialect_verify.py` (commit `f821757`, corrected at `3c9520a`), was written by
    the text's author, with the vectors in view, from the companion document, the two sections of the
    checkpoint witness statement it adopts and RFC 8032; its author did not read the Runner's code. It
    uses Python's standard library alone, Ed25519 included.
  - The second, `tools/dialect-verify-ts/` (commit `e2d41c5`), was written by a different author, in
    another language, TypeScript, from the companion document's text alone, under a protocol that
    forbade sight of the first reader, its test, the reference Runner's words and this RFC's Evidence
    and Implementation sections. It read the vectors as data and this repository's manifest of their
    answers; its README and pull request #145 list what it read. It uses Node's built-ins alone, and
    computes Ed25519's equation itself.
  - The reference Runner's `verify-run` is a third reader of the same bytes, in its own repository.
- **The output side.** The gateway's decision policy holds a write to its decision record: `bind`
  (gateway ADR-0011), `fix` and `closed` (gateway ADR-0016, gateway #258, released in `v0.14.0`), and
  `requireSignedRecord` (gateway ADR-0012), its digest carried by every action receipt it governs.
- **The research line.** Desk #369 and #371 specify an ICP research recipe — a prompt and reviewed
  constraints, an AI connection and model by name, candidates with field-level supporting evidence,
  a run record — and its handoff into pack and graph evaluation through mapping v2's generated-input
  admission. Neither is built as a writer of this format yet; the `research` kind is the form they
  would write.

**The standing of that evidence.** Both readers are this project's, and both authors are AI coding
agents of one model, Anthropic's `claude-opus-5-5`, each working from a brief of its own. The first
reader's author is the text's: it drafted the companion document from the Runner's documentation,
the derivation rule's specification, the gateway's `SPEC.md` and the vectors, examined as files and
with small scripts of its own that took their digests and checked their signatures, and then wrote
the reader from the companion document alone, those scripts set aside. The second reader's author is
another session, which did not draft the text and saw neither the first reader nor the Runner's
words. A cross-vendor review that was allowed to read both readers, by OpenAI's `gpt-5.6-sol`, found
no sign that the first reader was in view, and one affirmative sign that it was not: the readers
disagreed on one case no vector holds, a `freshWithin` naming a declared parameter of the wrong type,
which the text decided in the second reader's favour and to which the first reader was corrected in
pull request #147. That round's record and the maintainer's disposition of each finding are on pull
request #145, and the correction's note on #147.

**What that establishes, and what it does not.** For [RFC 0000](0000-rfc-process.md)'s evidence bar,
it establishes that two implementations agree on the vectors, the second written from the text
without sight of the first. The second's independence rests on the recorded protocol — its author's
account of what it read, and what a reviewer could check from the code — and not on separate
organisations: both readers are one project's, by agents of one model, under one maintainer. Nor
does it show that the two interoperate where the vectors are silent: there each reader's tests are
its own. The reference Runner's `verify-run` is a third reader of the same bytes, in its own
repository and of the same project. What the bar still asks is Unresolved question 9.

**What writing the readers found.** Writing the first found three things the text did not say, each
fixed in the text and not in the reader: whether a copy may name one evidence requirement twice (it
may not); where a source parameter's `parameter-invalid` falls among a source's findings (first); and
where a failure of the case's own read falls (after the case's parameters, before every source). And
eight rules that neither the Runner's documentation nor its vectors decide, on which the text takes a
position and says so (Unresolved question 1). Writing the second found six points on which the text
had left the readers a choice, which its README records, set apart by the cross-vendor round from the
rules the text states or incorporates by reference. On those six the text, not the readers, now
decides, as the maintainer decided them: the report's form and the exit statuses (§11);
the byte-bound scans and the nesting convention (§12); the extraction of a version-2 record (§11);
"but for case", ASCII case only (§11); a `freshWithin` naming a declared parameter of another type,
which is false (§6.3); and a requirement id, a non-empty string of no other form (§6.3). Each of
those sentences has a test in each reader, and where a reader did not follow one it was changed to
it in the amendment that wrote them; that amendment's author read both readers, so those changes are
the text's, and add nothing to the second reader's independence. Beside them are the readings both
readers take where the text names a member without a form, held by no vector: `http`'s `path` as a
string template; `http`'s `headers` as an array of non-empty strings; and a `sql` binding's `name`
and `type` as non-empty strings (the amendment of 2026-10-15 that read version 3, which read
`research`'s `evidence` so too, the form the research-contract amendment then gave it). Both
readers read the research contract since the pull request for issue #176, one author's extension
of both from the text, held to each other on hand-written documents and to no vector. Where that
text leaves a choice they take one reading each: a plain read's `unwrap` pointers and a copy's
`source` are held to the closed list as froms, never under `values`; no pointer descends below an
observation's `value`; a reconciliation's conditions read only a named field's entry, its
`status`, and its `value` or `values`; a decimal's 128 is counted in characters; a research
source's question commits a parameter only under the record's own receipt; an acquired record
with no receipt at all is still listed in `unsignedFreshness`, its `receipts` empty; and a field
declared twice is `input-malformed` once forms are checked, but before that phase 3 measures its
answers by the first declaration of the name whose `type` is one of the six. One vector
is answered otherwise than `verify-run` answers it, by design: `disposition-differs-from-audit`
alters the Runner's export, not the preparation or the record (Conformance).

## Specification

This section is the text proposed to land: the proposed companion document `spec/dialect.md`, its
§§1–14 word for word, each heading one level down. The companion document adds only its Status,
which says what this RFC's preamble says. Its key words **MUST**, **MUST NOT**, **REQUIRED**,
**SHOULD**, **SHOULD NOT** and **MAY** are to be interpreted as described by BCP 14 when, and only
when, they appear in all capitals.

### 1. Terms and the canonical forms

A **dialect** is a pack's terms spoken in a system's: the declared, reusable translation between a
system and a pack. Its **input side** says how the facts and the evidence availability an
evaluation takes (Core §8.2) are obtained and derived; its **output side**, which is optional, says
how a disposition becomes the arguments of a write (§10). A dialect is declarative — pointers,
types, templates, derivation rules and bindings — and is never code.

The input side is one JSON document, the **dialect document** (§2). A **preparer** applies it, at
one instant, to a **case** — one JSON document, what an operator typed or a caller sent for one
evaluation — and to the **acquisitions** its sources name, and writes a **preparation** (§9): how
each fact and each evidence availability was derived, from which acquisition, under which receipt,
at which instant. The reference preparer is the Runner. A **preparation verifier** (§14) reads a
preparation by recomputing it from the same inputs (§11).

A **source** is one declared acquisition, of one **kind** (§4). An **acquisition** is what one call
for a source returned: for an acquired kind, a gateway's answer and the receipt it signed (§5); for
the case, and for a file the operator selected, bytes the operator supplied. A `research` source's
acquisition is instead the research record the caller assembles from retained responses (§4.3).
Every source has a **class** (§8.2): `asserted`, `record` or `generated`. A **target** is a fact
pointer or an evidence requirement that a source writes.

A **pointer** is an RFC 6901 JSON Pointer. A pointer **resolves** in a value when each of its
tokens names a member or an index that exists; otherwise it yields **absent**, which is not `null`.
A token names an array's element when it is `0`, or a digit other than `0` followed by any digits,
and its value is below the array's length; a token of any other form, or of any length beyond the
array's, names none, and no limit of an implementation's numbers applies to it.

A **timestamp** is a string of the form `YYYY-MM-DDThh:mm:ssZ`, a digit where each letter but `T`
and `Z` stands: UTC, whole seconds. Its **instant** is its count of seconds since
`1970-01-01T00:00:00Z` in the proleptic Gregorian calendar, when the date and time it writes exist:
month `01` to `12`, a day the month has, hour `00` to `23`, minute and second `00` to `59`. A string
of the form that names no time, such as `2026-02-30T00:00:00Z`, has no instant, nor has any other
string.

Hexadecimal is lowercase throughout. A **digest** is the string `sha256:` followed by 64
hexadecimal characters; the **digest of** some bytes is that string for their SHA-256. A **key** is
the 32-byte encoding of an Ed25519 public key, written as 64 hexadecimal characters; its **key
identifier** is the first 32 hexadecimal characters of the SHA-256 of the 32 bytes. A key is held to
the key rule of the checkpoint witness statement, its §5, before anything signed under it is read,
and a signature to the equation of that section: RFC 8032's check without the cofactor, with a
canonical scalar.

**Reading a document.** Every JSON document this document names — a dialect, a case, the
acquisitions, the profiles, a preparation, a record — is read strictly: exactly one JSON value
(RFC 8259), with only whitespace around it; no member name given twice in one object; every string
well-formed Unicode, a lone surrogate written as an escape included. A document that is not so
read is refused (§11). A number is read as its literal, its characters kept: a reader that reads a
number as a binary floating-point value and writes it again does not read it as this document
does. Every object this document defines is closed: a member it does not list is refused, and so
is a member it lists that is of another type or form. Member names are matched exactly, so a name
that differs from a listed one only by case is an unknown member.

**Integers.** An **integer** is a number whose literal is an optional `-` followed by `0`, or by a
digit other than `0` and any further digits, with no fraction and no exponent, and whose value is
from −(2⁵³−1) to 2⁵³−1. `-0` is an integer, and wherever a preparation carries one it keeps its
literal (§9.5). `1.0`, `1e2` and `9007199254740992` are not integers.

**The gateway canonical form**, `canon`, of a value is the canonical form of the checkpoint witness
statement, its §1, which is the gateway's (gateway §1.1). Its domain is objects with no member name
given twice, arrays, well-formed strings, integers, `true`, `false` and `null`. Its output orders
an object's members by the code points of their names, keeps an array's order, has no whitespace,
writes a string as raw UTF-8 with only `"` and `\` and the characters below U+0020 escaped (`\"`,
`\\`, `\b`, `\f`, `\n`, `\r`, `\t`, and `\u00` with two hexadecimal digits for every other one),
and writes an integer in decimal digits, `-0` as `0`. A value outside the domain, a number that is
not an integer above all, has no `canon` form and no digest. Every digest of §§2–8 is the digest of
a value's `canon` bytes: a dialect's, a profile's, a read's, an acquisition's result's, and the
commitment to a request.

**The preparation's canonical form** (§9.5) is another form, the one a preparation is digested in:
it escapes `&`, `<`, `>`, U+2028 and U+2029, and keeps each number's literal. The two forms are
never interchanged.

### 2. The dialect document

The dialect document is one JSON object. Its version 2 is the Runner's mapping v2 document: a
mapping v2 document the Runner accepts is a version-2 dialect document, with the same bytes and the
same digest. The one exception is a request's `query` under a profile whose adapter is the gateway's
`adapter-http`, which the Runner holds to the rules of a template alone and this document to string
templates as well (§4.1). Version 3 (§4.3, §4.4) is read by the reference Runner since its pull
request 83, released in `v0.12.0`: it prepares an `operation`, bound or unbound and bound at import,
and a `selected-file`, and refuses each of the other four kinds by name.

| Member | Form | Meaning |
| --- | --- | --- |
| `version` | the integer `2`, or `3` (§4.3, §4.4) | the dialect version, per which the source kinds (§4) and every form of this document are closed |
| `case` | an object (§3), REQUIRED | the case's parameters, and the facts and evidence copied from the case |
| `sources` | an array of at most 16 sources (§4), optional | absent is the empty array |
| `admits` | an object (§8.2), optional | the classes a target admits, where they are not the default |
| `unmapped` | an array of distinct pointers, optional | fact pointers a pack reads that the author acknowledges are not mapped |
| `unmappedEvidence` | an array of distinct non-empty strings, optional | evidence requirements a pack declares that the author acknowledges are not mapped |
| `provider` | the string `""`, optional, of version 2 only | a member of the Runner's version-1 mapping, which its encoding of a version-2 document carries empty |
| `facts`, `evidence` | `null`, optional, of version 2 only | the same |

`unmapped` and `unmappedEvidence` are for review of a dialect against a pack's inventory (Runner,
"Release checks, runtime and offline verification"): no preparation reads them, and a verifier
holds them to their form and to nothing else.

The **dialect digest** is the digest of the document's `canon` bytes, every member it holds
included. The same document with an optional member written out, as the Runner's encoding writes
`provider`, `facts` and `evidence`, or left out, has another digest: a verifier takes the document
as it was given and adds or removes nothing. A document outside the `canon` domain is refused.

**Version 3 is written one way.** `provider`, `facts` and `evidence` are members of version 2 alone:
a document of version 3 carries none of them, and one that names one is refused. And version 3 is
held to the reference Runner's encoding rule: the Runner keeps a document of version 3 only as its
encoding writes it, and its encoding leaves out a member it holds empty where the member is optional
and of an array or object type that it omits when empty. So, in version 3, `sources`, `unmapped` and
`unmappedEvidence` written as the empty array, and the case's `parameters`, a source's `parameters`,
and the `facts` and `evidence` of `admits` written as the empty object, are refused, since a document
so written would be kept under another digest than its own. Every other member written empty is kept
as written and read: `admits` itself, a copy's `facts` and `evidence` (§6.2), and the members of the
kinds of §4.3, `query`, `body` and `headers` among them. (No vector decides either refusal.)

Version 1 is no dialect: the Runner's version-1 file mapping has no preparation. The numbering is
the Runner's, kept so that every mapping v2 document is a version-2 dialect document byte for byte.

### 3. The case and parameters

`case` is an object of exactly `parameters`, an object, optional, absent being the empty object;
`facts`, an array of fact copies; and `evidence`, an array of evidence copies (§6.2). The case is
the source named `case`, of class `asserted`: what `facts` and `evidence` copy from the case
document is what the operator supplied.

A **parameter** has a name, a type and a value. The types are `string`, a JSON string; `integer`,
an integer (§1); and `timestamp`, a string that has an instant (§1). A name is a non-empty string,
and `runAt` is reserved.

- A **case parameter** is declared in `case.parameters` as `"name": {"pointer": P, "type": T}`,
  exactly those two members. Its value is the case document's value at `P`, which MUST resolve and
  MUST be of type `T`; otherwise the preparation fails, `parameter-invalid`.
- A **source parameter** is declared in a source's `parameters` (§4) as
  `"name": {"from": S, "pointer": P, "type": T}`, exactly those three members. `S` names a source
  earlier in `sources`, and `P` is a fact target of `S` (§8). Its value is the value at `P` in the
  facts of `S`'s claim (§6), taken only when that claim's `acquisitionStatus` is `resolved` and it
  gives a value at `P`. When it does not — `S` was skipped, its claim is not `resolved`, or it gives
  no value at `P` — the source that declares the parameter is **skipped** (§9.2). A value that is
  there and is not of type `T` fails the preparation, `parameter-invalid`. A source parameter
  cannot have the name of a case parameter, and `S` cannot name the source that declares it or a
  later one.
- **`runAt`** is in every scope, of type `timestamp`. Its value is the preparation's `verifiedAt`
  (§9.1). A derivation rule may read it (§6.3); a request template that names it is refused (§4.1).

A source's **scope** is the case parameters, its own source parameters, and `runAt`, at most 64
parameters. The case's scope is the case parameters and `runAt`.

### 4. Sources and their kinds

A source is an object with these members, and those its kind adds:

| Member | Form | Meaning |
| --- | --- | --- |
| `name` | a non-empty string, not `case`, distinct among the sources | the source's name, which its outcome, its lineage entries and its acquisition carry |
| `kind` | a kind of the document's version | what is declared, and how it is acquired |
| `parameters` | an object of source parameters (§3), optional | |
| `read` | a read (§6), REQUIRED | how the value acquired becomes a claim |

The kinds:

| Kind | Version | Class | What is declared | Vectors |
| --- | --- | --- | --- | --- |
| `operation` | 2 | the profile's | a read of a gateway source of shape `airbyte`, `mcp` or `http` that an input profile pins, and a template of its request (§4.1); in version 3, also unbound (§4.4) | of shapes `mcp` and `http`; in version 3, of shape `mcp` bound and of shape `http` unbound |
| `selected-file` | 2 | `asserted` for `local-file`, the profile's for `google-drive` | a document the operator selected (§4.2) | none |
| `http` | 3, proposed | the profile's | a request to a gateway HTTP source: method, path, query and body templates, header names (§4.3) | none |
| `sql` | 3, proposed | the profile's | a statement on a connection, with its bound parameters (§4.3) | none |
| `web` | 3, proposed | the profile's | a public page by URL, through the gateway's web source (§4.3) | none |
| `research` | 3, proposed | `generated` | a recipe (§4.3), also unbound (§4.4) | none |

A version-2 document that names a kind of version 3, or has an unbound source (§4.4), is refused.
**A kind without vectors is defined, and not claimable**: a verifier's claim names the kinds it
reads (§14), and may name only kinds that the vectors published with its specification version
exercise; and so with the shapes of an `operation`, and with a version. Today the staged vectors
exercise the case and `operation` of shapes `mcp` and `http` in version 2, and in version 3 the case
and `operation` of shape `mcp`, bound, and of shape `http`, unbound and bound at import (§4.4); none
is published.

#### 4.1 `operation`

An `operation` source has, besides the members of §4, exactly:

| Member | Form |
| --- | --- |
| `profile` | a non-empty string: the `id` of an input profile (§5.1) |
| `profileDigest` | a digest: that profile's digest |
| `maxAge` | an integer from 1 to 86400: seconds |
| `arguments` | the template of its request: an object, and not a template form (below) |
| `calculation` | an object (§7), present exactly when the profile is a calculator's |

An `operation` reads a gateway source of an adapter's shape, `airbyte`, `mcp` or `http`, which its
profile's `shape` names; a profile of shape `command` serves none. Its `arguments` are an object,
and not a template form, held to the rules of a template (below); what more its request must be
follows the shape:

- **`mcp`**, a tool call: exactly `tool`, a non-empty string, and `arguments`, a template. `tool`
  MUST be among the profile's `tools`.
- **`http`** and **`airbyte`**: the request the gateway source of that shape takes, as its adapter
  or its connection defines it. The gateway's `adapter-http` takes `{method, path, query, body}`,
  `query` and `body` optional and `query`, when present, an object of string values; a connection
  takes the form its provider documents in the gateway's `adapters/README.md`, such as
  `{connection, revision, read, …}`; and `adapter-airbyte` takes a stream read, `{stream, namespace,
  limit, state}`. These are examples of the forms the gateway defines, and not a closed list: this
  document holds such a request to being an object, to the rules of a template every request has,
  and to the receipt's commitment to it (§5.2, check 4), and not to a set of members. One rule more
  holds `adapter-http`'s `query`: under a profile whose adapter is `adapter-http`, by its
  `adapter.name`, a request's `query`, when it has one, MUST be an object, not a template form,
  each of whose members is a string template. The gateway's `adapter-airbyte` answers every read
  with a page, and an acquisition of a page is not read (§5.2), so no acquisition of shape
  `airbyte` is read today and no vector holds one: the shape is defined, and not claimable.

A **string template** is a string, a `$text`, or a `$param` naming a parameter of type `string` or
`timestamp`. An `arguments` that is not an object, or is a template form, is refused with the
dialect (§11). A request that does not fit its profile — under a profile of shape `command`, any;
under one of shape `mcp`, one that is not a tool call or names a tool the profile does not allow;
under one whose adapter is `adapter-http`, a `query` of another form — is `profile-mismatch`
(§5.1). (No vector decides the shape `airbyte`, a connection's request, `POST`, a `body`, a
template form in `path`, or a request with no `query`.)

**Templates.** A template is a JSON value in which an object one of whose member names begins with
`$` is a **template form**, which MUST be exactly one of:

- `{"$param": N}`, `N` a string: replaced, as a whole value, by the value of the parameter `N`, of
  any type, its literal kept;
- `{"$text": T}`, `T` a string: replaced by the string `T` with each **placeholder** in it replaced.
  A placeholder is `{{`, a parameter name, and the next `}}`; it MUST name an `integer` parameter,
  and is replaced by that integer's decimal digits as `canon` writes it, `-0` as `0`. A `{{` with no
  `}}` after it is refused, and a `}}` outside a placeholder is taken as it is. (No vector decides
  the last two rules.)

Every other value of a template is literal, taken as it is, an object or an array member by member.
A name a template form gives MUST be in the source's scope, and MUST NOT be `runAt`, which no request
can carry. A literal object whose only member's name begins with `$` cannot be written. The
**request** of an `operation` source is its `arguments` instantiated as a template — of shape `mcp`,
`{"tool": tool, "arguments": A}`, `A` its instantiated template — and MUST be in the `canon`
domain.

A request **commits** a parameter when it carries it unambiguously: as a whole value, `$param`,
anywhere in it, or in a `$text` whose placeholders name it and no other parameter. A `$text` whose
placeholders name two or more parameters commits none of them: `{{a}}{{b}}` renders `1` and `23` as
it renders `12` and `3`.

#### 4.2 `selected-file`

A `selected-file` source names a document the operator selected, by its member `provider`:
`local-file`, a file on the operator's machine, of class `asserted`, with no profile, no `maxAge` and
no request; or `google-drive`, a Drive file read through a gateway source a `drive` input profile
pins, with `profile`, `profileDigest`, `maxAge` and `arguments` as in §4.1, its `fileId` and the
consumed selection `grant` resolved from typed case parameters. Its acquisition is the Runner's
selected snapshot (Runner, "Supported input and trust configuration"), whose form this document
does not restate. The kind is defined, and not claimable: no vector holds one, and a version that
admits it to a claim states the snapshot's form first.

#### 4.3 Kinds proposed for version 3

Version 3 is version 2 with four kinds more, and with the unbound source form (§4.4); a document
of version 3 has `version` `3`, and so has its preparation (§9.1). The reference Runner reads
version 3 since its pull request 83 (`v0.12.0`), and prepares its `operation` and `selected-file` as
it prepares version 2's; it refuses each of the four kinds below by name. Those four are proposed: no
preparer writes them, no verifier reads them, and no vector holds them. The forms below are what a
writer, such as the Desk's inputs or an entry of the Exchange, needs to declare one; the first
implementation's vectors will fix each request's exact bytes, and may change them. Since version
2's `operation` reads a source of each adapter shape (§4.1), the `http` and `sql` kinds describe how
a request is formed — a body and headers, a statement and its bindings — and not how a configured
source is read. A source of each of these kinds is an object of exactly the members of §4 —
`name`, `kind`, `parameters` (its source parameters, as every source's) and `read` — with `profile`,
`profileDigest` and `maxAge` as in §4.1, and the members its kind names below. A `research` source
instead has §4.4's bound or unbound profile assignments, and keeps `maxAge`. Except for `research`,
each is acquired through the gateway source its profile pins, so §5's checks apply with the shape
the profile names. A `research` source retains responses acquired through the gateway sources
their own profiles pin, as below. The value acquired is read as every value is (§6).

- **`http`**, a request to a gateway source of shape `http` (the gateway's `adapter-http`):
  `method`, `GET` or `POST`; `path`, a template that yields a path under the profile's endpoint;
  `query`, optional, an object of string templates; `body`, optional, a template, refused beside
  `GET`; and `headers`, optional, the names of the headers the profile's source is configured to
  send, for review. A dialect names a header and never its value: values and credentials are the
  gateway's configuration and never a dialect's. The request is `{"method", "path", "query",
  "body"}`, as `adapter-http` reads one.
- **`sql`**, a statement on a connection the profile names, such as the gateway's Databricks
  connection: `statement`, a fixed string and never a template, so that the statement's structure
  and identifiers are fixed; and `bindings`, an array of `{"name", "type", "value"}`, each `value` a
  `$param` form, which the connection binds as the provider's named parameters. `bindings` is not
  `parameters`, which declares the source's parameters as every source's does, so a `sql` source
  can take a value from an earlier source and bind it. No text is substituted into a statement.
- **`web`**, one public page by URL through the gateway's web source (`adapter-web`, shape
  `http`): `url`, a string, or a `$param` form naming a `string` parameter. The request is
  `{"url": url}`, and the value acquired is the attachment record the web source returns.
- **`research`**, an AI-assisted research recipe, of class `generated`. Besides §4's members,
  `maxAge` and its profile assignments (§4.4), it has exactly `question`, a string template;
  `constraints`, an object in the `canon` domain; `model`, a non-empty string of at most 256 UTF-8
  bytes; `evidence`, an array of non-empty strings, each at most 4096 UTF-8 bytes, describing
  the evidence to retain; `fields`, the requested fields below; and `capabilities`, an array of
  distinct names from the closed set `answer`, `search`, `page`. `answer` is REQUIRED; the others
  name the web capabilities needed. The array follows that order and has one to three entries.
  A published source is unbound (§4.4), carrying no installation identifier.

  The source's request is exactly `{"question", "constraints", "model", "evidence", "fields",
  "capabilities"}`, with `question` instantiated as a template. These members, the fields' order
  and every field declaration, the read and its source order (§6.4), and all supplied profile
  assignments enter the dialect digest (§2). No defaults are inserted. The recipe is recorded,
  never re-executed by verification. Its model and capabilities are checked against the profiles
  then bound (§5.1); this checks declarations, not the actual model or its answer. Each retained
  response's own `request`, below, is what its receipt commits. No model output is produced or
  compared. `evidence` cannot weaken the citation requirements below.

  The source's acquisition is the **research record**, `R`, an object the caller assembles, with
  exactly two members: `fields`, the answers below, and `responses`, an array of at most 64
  retained responses, the AI connection's answers and the web reads retained with it, in the order
  the run made them. Each response is an object of exactly `profile`, `request`, `result`,
  `receipt` and `salts`. `profile` is an object of
  exactly `id`, a non-empty string, and `digest`, a digest, naming the trusted input profile the
  response came through (§5.1). `request` is the request made, an object in the `canon` domain;
  `result` is the returned JSON value; `receipt` and `salts` have §5.2's forms. The receipt's
  `resultDigest` names the result by its digest. A named response whose result bytes are not
  retained is `acquisition-missing`; a retained response that `R` does not name is
  `acquisition-unexpected` (§5.2).

  `R` is carried as the source's `response.result` (§5.2), and the source's read (§6) starts from
  `R`, not from each response's result separately. The record's own `receipt` and `salts` are
  present beside `result` in that `response` when `R` came back through a gateway source, and
  absent otherwise. Membership and order in `responses` are the caller's assertion: verification
  uses `R`'s order and does not establish that assertion (§13). A page cited by URL alone is no
  retained response; the claim it supports is the answer's say. A profile of another class is
  `profile-mismatch` (§5.1). The kind is defined, and not claimable: no vector holds one (§11).
  (No vector decides this.)

**Requested fields.** A research source's `fields` is an ordered array of 1 to 64 closed objects,
each exactly `{"name", "type", "required", "description"}`. `name` has §4's source-name form: a
non-empty string other than `case`, here bounded to 64 UTF-8 bytes and distinct within this array.
It is a stable identifier, not a display label; changing it changes the contract. `description`
is a non-empty string of at most 2048 UTF-8 bytes. `required` is a boolean: it requires an answer
entry, never a value. `type` is exactly one of the following strings, with these JSON encodings:

- `integer`: an integer in §1's domain, including `0` and `-0`; no fraction or exponent.
- `decimal`: a string of at most 128 ASCII characters in Core §2.2's decimal grammar,
  `-?(0|[1-9][0-9]*)(\.[0-9]+)?`, matching the whole string. A JSON number, exponent, leading
  plus, leading zero or empty string is not a decimal. Signs, scale and trailing zeroes are
  retained: `"1.0"` and `"1.00"` remain distinct strings under §6.3's equality. This adopts Core's
  lexical form only and adds no coercion, units or decimal operators to a rule.
- `boolean`: JSON `true` or `false`, never a string or a number.
- `text`: a well-formed JSON string of 0 to 8192 UTF-8 bytes; the empty string is a value.
- `text-list`: an array of 0 to 64 well-formed strings, each of 0 to 1024 UTF-8 bytes. Order,
  duplicates and empty strings are kept; an empty list is a value, not an absent answer.
- `range`: a closed object of exactly `min` and `max`, both integers as above or both decimal
  strings as above, never mixed; `min` is at most `max` by exact mathematical comparison.
  Comparison uses the decimal digits, never binary floating point, and changes no spelling.
  An equal-endpoint range is allowed. No open endpoint, `null` endpoint or extra unit is allowed.

**Answers.** `R.fields` is an object of at most 64 members, keyed by declared field name. An
undeclared name is refused. Every required field has an entry; an optional field may be absent.
An entry is a closed object with `status` and `cites`, and the conditional `value` or `values`:

- `found`: `value` is present, of the declared type; `values` is absent. `cites` has 1 to 64
  distinct indices into this record's `responses`.
- `not-found`: neither `value` nor `values` is present. `cites` has 0 to 64 distinct indices,
  naming retained responses about the unsuccessful search when any are given.
- `stale`: neither `value` nor `values` is present. `cites` has 0 to 64 distinct indices. The
  caller asserts that an observation was made; it is cited when `cites` names it. No observation
  is a resolved value here.
- `conflicting`: `value` is absent; `values` is an array of 2 to 64 closed objects, each exactly
  `{"value", "cites"}`. Each `value` has the declared type and each `cites` has 1 to 64 distinct
  response indices. At least two values differ under §6.3's JSON equality. Observations remain
  in their recorded order, without choosing one or coercing them. The entry's outer `cites` is
  `[]`; citations belong to each observation and are not replaced by a common list.

An index is an integer from `0` below `responses`' length, written without `-0`; indices in
each citation array are distinct by value. Any other index, a repeated value or a URL in place
of an index is `input-malformed`. This range is a form, not a §12 maximum. An index names the
whole retained response, not a URL, an excerpt id or the preparation's `cites`. Array order is
kept. A cited response with missing bytes still gives `acquisition-missing` (§5.2).
A receipt holds the cited bytes; it does not establish that they support the value. An answer's
status is the caller's assertion. In particular, `stale` describes an observation's currency,
not an exception to receipt freshness: an expired retained
receipt still fails as `acquisition-stale` (§5.2).

Absence is permitted only for an optional entry and for the conditional members just stated.
`null` is never an entry or a value, including a conflicting value, list item or range endpoint.
It may occur in a retained response's arbitrary result, where it remains evidence, not a typed
answer. Zero, `false` and `""` are present values only of their declared types; none means
`not-found`. A required entry may have any of the four statuses. A missing required entry, wrong
type, unknown member or status, misplaced `value` or `values`, reversed range, repeated field
name or invalid citation is `input-malformed`; exceeding a maximum is `input-over-bound` (§11).
The same rules hold every entry, whether or not the read uses it. (No vector decides this.)

**Reading fields.** In a plain research read, the pointers a copy or rule may read form a closed
list: `/fields`, `/fields/<name>`, `/fields/<name>/value` and its descendants,
`/fields/<name>/status`,
`/fields/<name>/values/<index>/value`, and `/fields/<name>/cites`. The name is escaped as one
RFC 6901 token. A range's endpoints append `/min` and `/max` to `value`; a text-list item appends
its index. These are pointers into `R`, not pack targets. Any other read pointer is
`input-malformed`; `/responses/...` is not readable by a read. Retained responses are for replay.
A copy of a missing `value` writes nothing (§6.2); a rule guards a value with its status and
follows §6.3. A read may retain the whole field entry for review. A plain research read MUST NOT
take a `from` under `values`; that `from` is `input-malformed`, as in §6.4. That section defines
reconciliation's combined value and pointers.
Deterministic sources keep their target declarations and gain no `fields` member.

`R.fields`, every status, value, observation and citation index, and `R.responses` in its order
are all in `R`'s `canon` bytes. The record's receipt commits all of them when present; without
one, fields as well as response membership and order are the caller's assertion. The preparation
commits the bound dialect, derived claims and receipt citations in §9's existing form; it gains
no whole-record digest. A change to an unread, unreceipted field need not change that preparation.

#### 4.4 The unbound source form (version 3)

An `operation` that names its profile by its digest pins the installation it was written under: the
gateway's key, its source and authority, its adapter and its endpoint (§5.1). Version 3 gives an
`operation` an **unbound** form, which names instead what an installation binds it to: the catalog
binding and operation it is read through, the shape that serves it, and the record it is written
against. A dialect is published unbound, as an entry of the Exchange holds one, and bound by the
installation that adopts it.

An unbound `operation` source has, besides the members of §4, exactly:

| Member | Form |
| --- | --- |
| `platform` | a non-empty string: a platform of the gateway's catalog, as its binding names it (`platform`) |
| `operation` | a non-empty string: an operation of that binding, as its `operations` name it |
| `shape` | `airbyte`, `mcp` or `http`: the shape that serves the operation |
| `record` | a non-empty string: the program whose answer the read is written against, as a profile's `adapter.name` names it (§5.1) |
| `maxAge` | as in §4.1 |
| `arguments` | as in §4.1 |
| `calculation` | as in §4.1, optional |

It has no `profile` and no `profileDigest`. The catalog's names are the gateway's
(`catalog/README.md`), and a verifier holds them to their form and to nothing else.

**Research binding.** A published `research` source has §4.3's members, including `model` and
`capabilities`, and none of `profile`, `profileDigest` and `webProfiles`: it is unbound. It names
requirements, with no connection id, endpoint, credential or other installation identifier.
Its bound form adds all three members. `profile` and `profileDigest`, as in §4.1, name the AI
profile for `answer`. `webProfiles` is a closed object with exactly the `search` and `page`
capabilities the source requests as keys; each value is exactly `{"profile", "profileDigest"}`,
of those same forms. It has zero to two members and is REQUIRED even when empty. One profile may
serve more than one capability; every assigned profile is of class `generated`. A source with
only some of the three binding members, or any operation catalog member, is `input-malformed`.
The new required members stay written when empty; §2's one-spelling rule is unchanged.

**The binding document.** An installation binds an unbound dialect with a **binding document**: one
JSON object of exactly `dialect`, the unbound dialect's digest (§2), and `sources`, an object
mapping the name of each unbound source of that dialect, and no other name, to its assignment.
For an `operation` that assignment is exactly `profile`, a non-empty string, and `profileDigest`,
a digest: an input profile of the installation's gateway, by its `id` and its digest. For
`research` it is exactly `profile`, `profileDigest` and `webProfiles`, of the forms above, with
exactly the requested web capabilities. Its digest is the digest of all its `canon` bytes.
It is neither the record's `binding` (§9.5) nor a binding of the gateway's catalog.

**The bound dialect** is the unbound dialect with the binding applied. For each unbound
`operation`, `platform`, `operation`, `shape` and `record` are removed, and the binding document's
`profile` and `profileDigest` are added; every other member is kept as written. For
`research`, the three assignment members are added, and every other member is kept as written:
there are no operation catalog names to remove, and `model`, `capabilities` and `fields` remain.
It is a document of version 3 with no unbound source, and its digest (§2) is the one a
preparation of it carries as `mappingDigest`. The unbound dialect's digest is the one its
publisher names, as an entry of the
Exchange names `dialect.digest` (RFC 0019 §3); the bound dialect's is the installation's, and one
dialect bound under two installations' profiles has two.

**Verifying it.** A verifier given a dialect with an unbound source is given its binding document
too, and reads the bound dialect as this document reads every dialect, with these added checks. A
binding document whose `dialect` is not the given dialect's digest, or whose `sources` do not name
exactly its unbound sources, is refused with the dialect, as is a dialect with an unbound source
and no binding document, and a binding document beside a dialect with none (§11). For an
`operation`, a profile the binding document names whose `shape` is not the unbound source's
`shape`, or whose `adapter.name` is not its `record`, is `profile-mismatch` (§5.1). A fixture of
an unbound dialect carries the binding document it was recorded under, and verifies against the
bound dialect.

The binding checks of §5.1 hold research too, including a bound dialect given directly. Its AI
profile MUST declare the exact `model` and capability `answer`; each assigned web profile MUST
declare the capability it serves. Every assigned profile MUST be `generated`; a profile that
declares a model MUST name the source's model. A missing profile, digest mismatch, missing
research declaration, wrong model, missing capability or wrong class is `profile-mismatch`.
Extra or missing assignment members, a capability assigned twice, or an assignment for an
unrequested capability is `input-malformed`. No substitution of another model is implicit.

**What it establishes.** Nothing beyond what an `operation` that names its profile establishes
(§13). The binding document is the installation's statement of which profile each source was bound
to. A preparation commits the bound dialect, by its digest, and with it the profile each source was
bound to; it commits neither the binding document's digest, nor the published dialect's digest, nor
the catalog names the binding removes (`platform`, `operation`, `shape` and `record`). Two published
dialects that differ only in those names, bound to the same profiles, have one bound dialect and one
digest. A record that binds the preparation commits what the preparation commits, under the
record's signature, the installation's own key. The reference Runner
writes version 3 since its pull request 83 (`v0.12.0`): it binds an unbound dialect at import, with a
binding document the operator supplies, and records the bound dialect's digest. The staged vector
`unbound-bound-at-import` holds the form, with its binding document; no specification version
publishes it, so the form is not claimable yet (§14). (That vector decides the bound dialect and its
digest; no vector decides the refusals of this section.)

For research, the same commitment holds: the preparation commits only the bound dialect's
digest, including all AI and web profile ids and digests, the model, capabilities, fields and
read. Neither the published digest nor the binding-document digest is added to §9.1. Rebinding
one assignment changes the bound digest. Replay uses the profiles then bound and the retained
bytes, never a live connection or a new model answer; it establishes no answer's correctness
(§13). The reference Runner still refuses `research` by name. No research binding or result
vector is recorded. (No vector decides this.)

### 5. Input profiles and acquisitions

#### 5.1 Input profiles

An **input profile** is an installation's public configuration for one gateway source: an object of
exactly

| Member | Form |
| --- | --- |
| `id` | a non-empty string, distinct among the profiles |
| `publicKey` | a key (§1): the gateway's |
| `class` | `record` or `generated` |
| `source`, `authority` | strings: the gateway's source name and authority label |
| `shape` | `airbyte`, `mcp`, `http` or `command` |
| `adapter` | an object of exactly `name` and `version`, strings, and `digest`, a digest |
| `endpoint` | a string, or `null` |
| `tools` | an array of distinct non-empty strings, optional, which a profile of shape `mcp` MUST give and MUST NOT give empty |
| `calculator` | an object of exactly `name` and `version`, strings, optional: the profile is a calculator's (§7) |
| `research` | an optional closed object of `capabilities` and conditional `model`, as below |

Its **digest** is the digest of its `canon` bytes. A calculator's profile MUST be of class `record`
and shape `mcp`. A profile whose key the key rule refuses is refused.

A profile may additionally declare `research`, a closed object of `capabilities` and, exactly
when they include `answer`, `model`. `capabilities` is a non-empty array of distinct names from
`answer`, `search`, `page`, in that order, at most three; `model` has §4.3's form. Web-only
profiles name no model. This whole declaration enters the profile digest. Malformed members
are `input-malformed`; a well-formed profile without the declaration or with unsuitable
capabilities, model or class is `profile-mismatch` when bound to research (§4.4). This extension
changes no operation binding check and makes no claim about model weights or execution.

A profile bound to a research source's capability serves the model's answer and is classed
`generated` for that binding. The same gateway web source bound to a `web` source is `record`;
its profile for that binding carries that class.

A profile is the installation's, never the dialect's: a dialect names a profile by its `id` and its
digest, and only an installation supplies one. A verifier is given the profiles it trusts, out of
band, as one JSON array, and MUST NOT take a profile or a key from a preparation, an acquisition or
an export. A source's **profile** is the trusted profile of its `profile` id, whose digest MUST be the
source's `profileDigest`; otherwise, and when a source does not fit its profile — an `operation`
whose request does not fit its profile's shape and adapter (§4.1), under a profile of shape
`command` among them, a tool the profile does not allow, a calculator's profile without
`calculation`, `calculation` without a calculator's profile, a profile bound to an unbound
`operation` of another shape or another record (§4.4) — the finding is `profile-mismatch`.

Each retained response of a `research` source names its own trusted profile by `profile.id` and
`profile.digest` (§4.3). That id MUST be among the profiles given out of band, and its digest MUST
match. The pair MUST be the source's AI assignment or one of its web assignments, each of class
`generated`; otherwise `profile-mismatch`. The reference in the response supplies neither a
profile nor a key. The source's profile does not substitute for a retained response's profile.

What a profile pins — the gateway's key, source, authority, adapter, shape, endpoint, class, tools
and any research declaration — is the installation's classification of a channel. It does not pin
a credential, a tenant's configuration or a model's weights, and an installation replaces a
profile when a change of those makes its classification wrong (Runner, "Decisions and ownership").

#### 5.2 Acquisitions

The **acquisitions** are one JSON object with a member for each source acquired, named by the
source's name, of the form `{"response": {"result": R, "receipt": E, "salts": S}}`, exactly, except
for `research` as below: the gateway's acquire answer (gateway §6) as the preparer kept it.
`R` is any JSON value; `E` is an object, a version-3 receipt (gateway §1.2a);
`S` is an object of `args` and, optionally, `statement`,
each 64 hexadecimal characters. A source to be acquired that has no member is
`acquisition-missing`; a member for a source that is skipped (§9.2), for a `local-file` source, or
for no source is `acquisition-unexpected`.

A `research` source is the one source whose `response` may lack `receipt` and `salts`: its member
is exactly `{"response": {"result": R}}` when the caller's research record did not come back through
a gateway source, and has the ordinary form above when it did. Both `receipt` and `salts` are
present or both are absent. `R` has §4.3's form. For a response named in `R.responses`, a missing
`result` means its bytes were not retained and is `acquisition-missing`, rather than a refusal of
the acquisition's form.
A retained response that `R` does not name is `acquisition-unexpected`. The order is `R.responses`'s
own; a different order is a different caller assertion, not a finding for disagreement with an
external order. When the record has its own receipt, that receipt also commits `R`'s bytes,
including the array's order, by check 5.

An acquisition is held to its source and its profile, and any of these checks that fails is
`acquisition-invalid`:

1. `E.receiptVersion` is `"3"` and `E.kind` is `"acquisition"`, and each member this list reads is
   of the form gateway §1.2a gives it; and `E.acquisition` has no member `pageItems`. A receipt with
   `pageItems` attests a page, which no preparation reads, whatever the source's shape, as the
   Runner reads none (Runner, "Deferred scope"). (No vector decides this.)
2. `E.keyId` is the key identifier of the profile's `publicKey`, and `E.signature`, 128 hexadecimal
   characters, verifies under that key by the equation (§1), over the ASCII bytes
   `judgment-pack-gateway/receipt/3:` followed by the `canon` bytes of `E` with its top-level
   `signature` member removed and every other member retained.
3. `E.source` and `E.authority` are the profile's `source` and `authority`; and
   `E.acquisition.adapter`, `E.acquisition.shape` and `E.acquisition.endpoint` are, as JSON values,
   the profile's `adapter`, `shape` and `endpoint`.
4. `E.argumentsCommitment` is `sha256:` followed by the hexadecimal SHA-256 of the 32 bytes `S.args`
   encodes, then the ASCII bytes `args:`, then the `canon` bytes of the source's request (§4.1).
5. `E.resultDigest` is the digest of `R`'s `canon` bytes; an `R` outside the `canon` domain fails.

For each retained response of a `research` source, checks 1–5 apply under that response's trusted
profile, with `E` its `receipt`, `S` its `salts` and `R` its `result`. Check 4 opens the commitment
over that response's own `request`, not the research source's recipe. A failed check is
`acquisition-invalid`. When the research record has its own receipt, checks 1–5 apply to it too,
under the research source's profile and over the source's request and the whole research record.
After the retained responses' checks and before the source's read, the whole record MUST be in
the `canon` domain even when it has no receipt of its own; otherwise `acquisition-invalid`.

Then its times, against the preparation's instant, `verifiedAt`: `E.acquisition.observedAt` and
`E.servedAt` MUST each have an instant no more than the source's `maxAge` seconds before
`verifiedAt` and no more than 30 seconds after it; otherwise `acquisition-stale`.
For research, this applies to every retained response and to the record's own receipt when
present, each using the research source's `maxAge`.

Then the sessions. The receipted calls of one preparation are in one of two forms: **they share a
session**, one `sessionId` at `callIndex` values that differ; or **each is alone in a session of its
own and is its session's first call**, each `sessionId` distinct, each `callIndex` 0. One call
alone is in both. Taken in the order of `sources`, the first receipt with which the receipts so far
are in neither form is `acquisition-sessions`. Within a `research` source, every retained
response's receipt participates, in `R.responses` order, followed by the record's own receipt when
present. A record with no receipt adds none of its own. The form is read from the receipts and
from nothing else.

An acquisition's **citation** is `{"callIndex", "sessionId", "signature"}`, those three members of
its receipt.

These checks are receipt-only. They do not establish that a session is sealed or complete, that no
attempt was left out, or that a caller did not choose among valid answers, in one session or in two
(Runner, "Time, sessions, errors and retries"). The receipt's `caller`, its `statement`, its chain
(`prevSignature`) and its `witness` are the gateway's verifier's to read (gateway §1.4, §4), and are
not read here.

### 6. Reads

A **read** turns the **value read** into a **claim**, an object of exactly `facts`,
`evidenceAvailability`, `acquisitionStatus`, `reason` and `basis`. A source's `read` is an object of
`unwrap`, optional, and exactly one of `copy` and `rule`. The case's read is
`{"copy": {"facts": F, "evidence": V}}`, `F` and `V` the case's `facts` and `evidence`.
For research only, §6.4 also admits the form `{"sources": [S, ...], "rule": R}`.

The **read digest** of a source is the digest of its `read`'s `canon` bytes, as the dialect writes
it; the case's is the digest of the case's read, so built.

#### 6.1 The value read

The value read starts as the acquisition's result, `R`, and for the case as the case document.
`unwrap` is an array of one to four pointers, applied in order: each MUST resolve, in the current
value, to a string that holds exactly one JSON value, read as §1 reads a document, which becomes the
current value; otherwise `read-failed`. An unwrap is not a count of records: a read that needs one
record guards it. An unwrapped value may hold numbers that are not integers, which a rule may
compare (§6.3) and no claim may carry.

For a source whose profile is a calculator's, the value read is held to §7 before the read applies.

#### 6.2 Copy

`copy` is an object of exactly `facts`, an array of `{"target": P, "source": Q}`, and `evidence`, an
array of `{"requirement": I, "source": Q}`, each entry exactly those members; both arrays are
REQUIRED, as the Runner requires them, and either may be empty. `P` is a fact target (§8.1), `I` a
non-empty string, `Q` a pointer. A copy names each requirement at most once, and one that names a
requirement twice is refused with the dialect. (No vector decides this.) The claim:

- `facts` starts as `{}`; for each entry whose `Q` resolves in the value read, that value is written
  at `P` (§8.1). An entry whose `Q` does not resolve writes nothing. (No vector decides this.)
- `evidenceAvailability` gives, for each entry whose `Q` resolves, `I` the value there, which MUST be
  `present`, `absent` or `unknown`, or the read fails, `read-failed`. An entry whose `Q` does not
  resolve gives `I` nothing. (No vector decides this.)
- `acquisitionStatus` is `resolved`, and `reason` is `copied`.
- `basis` is every entry's `Q`, of `facts` and of `evidence`, distinct, ordered by code point.

A value a copy writes MUST be in the `canon` domain, its numbers integers; otherwise `read-failed`.

#### 6.3 Rule

`rule` is a **derivation rule**, version 1: the portable derivation rule the Runner vendors, cited in
the Status, restated here whole.

A rule is an object of exactly `ruleVersion`, the string `"1"`; `parameters`, an object mapping each
parameter the rule reads to its type; and `clauses`, an array of one to 64 clauses, the last of
which has the `when` `{"op": "always"}`. Each parameter a rule declares MUST be in the source's scope
with the type declared, and its value is the scope's. A clause is an object of exactly `when`, a
condition; `claim`, a claim form; and `reason`, a string.

A condition is one of the objects below, each of exactly the members shown; `P` is a pointer into
the value read, and `N` and `M` name parameters the rule declares.

| Condition | True when |
| --- | --- |
| `{"op": "always"}` | always |
| `{"op": "exists", "field": P}` | `P` resolves |
| `{"op": "equals", "field": P, "to": X}` | `P` resolves to a value JSON-equal to the literal `X` |
| `{"op": "equalsParam", "field": P, "param": N}` | `P` resolves to a value JSON-equal to `N`'s value |
| `{"op": "isTrue", "field": P}` | `P` resolves to `true` |
| `{"op": "isDecimalString", "field": P}` | `P` resolves to a string that is `0`, or a digit other than `0` followed by any digits |
| `{"op": "freshWithin", "field": P, "asOf": N, "maxAge": M}` | `P` resolves to a string with an instant, `N`, of type `timestamp`, has an instant, and `0 ≤ instant(N) − instant(P) ≤` the value of `M`, of type `integer`, in seconds |
| `{"op": "all", "of": [C, …]}` | every condition listed is true, which the empty list is; evaluated in order, stopping at the first that is false |
| `{"op": "any", "of": [C, …]}` | some condition listed is true, which the empty list is not; evaluated in order, stopping at the first that is true |
| `{"op": "not", "of": C}` | `C` is false |

`all` and `any` list at most 64 conditions. **JSON-equal** compares type and value: numbers by their
mathematical value, so that `1` and `1.0` are equal; strings, booleans and `null` by value; arrays
element by element, in order; objects as sets of members. A number and a string are never equal.

That `N` and `M` name parameters the rule declares is a `freshWithin`'s form; their types are part of
its truth. A `freshWithin` whose `asOf` names a declared parameter of a type other than `timestamp`,
or whose `maxAge` names one of a type other than `integer`, is false, and the dialect is not
malformed.

A claim form is an object of exactly `facts`, an array of `{"pointer": P, "from": Q}`, each exactly
those members, `P` a fact target and `Q` a pointer into the value read; `evidence`, an object mapping
requirement ids to `present`, `absent` or `unknown`; and `acquisitionStatus`, one of `resolved`,
`absent` and `unknown`. A **requirement id**, in a claim form as in a copy (§6.2), is a non-empty
string, and that unqualified form is its only form.

**Deriving the claim.** The **match** is the first clause whose `when` is true; the last clause
ensures there is one. A **leaf** is a condition other than `always`, `all`, `any` and `not`, and
each leaf that is evaluated looks up its `field`. The claim is:

- `facts`: `{}`, and for each entry of the match's `facts`, in order, the value at `Q` in the value
  read written at `P` (§8.1); a `Q` that does not resolve fails the read, `read-failed`, and so does
  a value outside the `canon` domain;
- `evidenceAvailability`: the match's `evidence`;
- `acquisitionStatus`: the match's `acquisitionStatus`;
- `reason`: the match's `reason`;
- `basis`: the `field` of every leaf evaluated while the `when` of each clause up to and including
  the match was evaluated, distinct, ordered by code point. A leaf after a stop in `all` or `any` is
  not evaluated, and adds nothing.

A rule not of this form — a member, a condition or a claim form outside it, an unknown `op`, a type
other than the three, a literal outside the `canon` domain, a last clause that is not `always` — is
refused with the dialect (§11).

#### 6.4 Reconciliation of research sources

Section 8.1 still says: "No fact target of one source may equal another, or be a prefix of another
by whole tokens, of the same source or another, the case included". Overlapping fact targets are
`input-malformed`; last-writer-wins is not a reading of that text. A field name within a research
record is not a fact target: several sources may observe the same logical field, while only one
read writes the pack's target for it.

The one additional read form is `{"sources": [S, ...], "rule": R}`, exactly those two members,
on a version-3 `research` source. `sources` is an ordered array of 1 to 15 distinct names of
earlier `research` sources in the dialect; `R` is exactly the version-1 rule of §6.3. No `copy`
or `unwrap` is present. A missing, repeated, current, later or non-research source name, use on
another kind or version, or an extra member is `input-malformed`; a count over 15 is
`input-over-bound`. This dependency reads results, not source parameters, and adds no parameter
type or implicit fact target. Unavailable parameter values still skip their own source (§3).

The value read is the closed object `{"current": C, "sources": U}`. `C` is this source's `R`;
`U` is an object whose keys are the declared earlier names, each holding that source's retained
`R` after its acquisition checks. A skipped source's key is absent; no `null` or invented
`not-found` entry fills it. No other source is visible. A needed acquisition that is missing or
fails §5.2 ends preparation with that finding; fallback never catches invalid receipts or
`acquisition-stale`. Both acquired and skipped inputs count toward the declared source bound.
The derived value is held to §12's nesting bound before the rule applies, `input-over-bound`
otherwise; references do not duplicate input bytes in the combined document-size bound.

Pointers are `/sources/<source>/fields/<field>/status` and its sibling `value` or `values`,
and `/current/fields/<field>/status` and its siblings, each name escaped as one token. Conditions
and claim forms keep §6.3's semantics; the first matching clause is the declared precedence.
The rule MUST explicitly test a `found` status before selecting a value and name in its clauses
what absence, `not-found`, `stale` and `conflicting` do: advance to another source, or produce
an `absent` or `unknown` claim with no value for that target. The admissible fact `from` set is
closed: `/sources/<source>/fields/<field>/value`, `/current/fields/<field>/value`, or a descendant
of either. Any other `from`, including one under `values`, is `input-malformed`. Each selected
field MUST be declared by the source it names; otherwise `input-malformed`.

Let `<entry>` be that field entry's pointer, `/sources/<source>/fields/<field>` or
`/current/fields/<field>`. Its status guard is exactly
`{"op":"equals","field":"<entry>/status","to":S}`. The selecting clause's condition is that
guard with `S` equal to `"found"`, or an `all` with that guard as a direct member. Every selected
field also has that exact guard for each of `"not-found"`, `"stale"` and `"conflicting"`, and
the exact absence guard `{"op":"not","of":{"op":"exists","field":"<entry>"}}`.
These other-status and absence guards count anywhere in any clause's condition, at any depth
and polarity, whether or not evaluation reaches them. Missing guards are `input-malformed`.
In this version a reconciliation claim writes fact targets only: every claim form's `evidence`
MUST be `{}`, otherwise `input-malformed`. The last `always` clause has no facts and status
`unknown` or `absent`.
`all`, `any` and `not` combine the guards using §6.3; no new rule operator is added.

For example, a rule on `secondary`, with `sources: ["primary"]`, first guards primary's field
as `found` and copies its `value`. A second clause guards primary as absent, `not-found` or
`stale`, and secondary as `found`, then copies secondary's value. A third guards either as
`conflicting` and yields `unknown` with no fact. A fourth guards secondary as absent,
`not-found` or `stale` and yields `unknown` with no fact. The final `always` clause yields
`unknown` with no fact. The missing-entry guards are `not` of `exists` on each field entry.
The first clause therefore wins even if secondary conflicts; that order is part of this
example's declared policy. Authors may choose another order, but must write it in the rule.
Each clause's `reason` states its choice. A missing `from` pointer in a matched claim remains
`read-failed`, not permission to try the next clause. Non-found answers do not invent defaults.

The source list and whole rule enter the read digest and the dialect digest, in their written
order. The rule's `basis` and lineage's `candidateFrom` use the pointers into the combined value.
The target belongs to this source alone, of class `generated`, with generated influence; it
must admit `generated` (§8.2). The earlier sources retain their own outcomes and receipt lists;
§9.1's citations and §9.3's `receipts` are unchanged, and are not duplicated into the later
source's list. A rule reading several results establishes only the declared derivation from
those checked bytes (§13). (No vector decides this.)

### 7. Calculated values

An installation declares a calculator on an input profile, as `calculator` (§5.1). Declaring it,
the installation asserts that each tool the profile allows computes a deterministic function of the
inputs it echoes and the tables it reports, and calls no model. Nothing here can check that. A
calculator that calls a model is not a calculator: its profile is `generated`.

A source whose profile is a calculator's declares `calculation`, an object of exactly `inputs`, an
object mapping each input name to the name of a parameter in the source's scope, never `runAt`; and
`tables`, an object mapping each table name to an integer from 1 to 315360000, the most seconds its
contents may be old.

The value read MUST be an object whose member `calculation` is an object of exactly `calculator`, an
object of exactly `name` and `version`; `status`, one of `computed`, `input-missing` and
`cannot-compute`; `inputs`, an object giving each input the calculator used, by name, with its
value; and `asOf`, an object giving each table it read, by name, with a timestamp. That answer is
held to the source, and any of these checks that fails is `calculation-invalid`:

- `calculator` is the profile's `calculator`;
- every input it echoes is bound in `calculation.inputs`, and its value has the same `canon` bytes
  as the value of the parameter it is bound to: `"7"` is not `7`;
- every table it reports is named in `calculation.tables`, with a timestamp that has an instant;
- when `status` is `computed`, every input bound is echoed, and every table named is reported, as of
  no more than its limit before `verifiedAt` and no more than 30 seconds after it.

When `status` is `computed`, the source's read applies to the value read. Otherwise it does not
apply, and the claim is: `facts` `{}`; `evidenceAvailability` giving `unknown` to each evidence
target of the source (§8); `acquisitionStatus` `unknown`; `reason` `calculation-input-missing` or
`calculation-cannot-compute`; and `basis` `["/calculation/status"]`. A calculator that could not
compute has answered about the case; a stale table, or an answer about other inputs, is a fault of
the source, and fails the preparation.

Each lineage entry of a calculated source that was acquired carries `calculation` (§9.3), an object
of: `calculator`, `status` and `asOf`, as answered; and `inputs`, an array with one object for each
input echoed, ordered by the input's name, of exactly `name`, the input; `parameter`, the parameter
it is bound to; and `source` and `pointer`, where that parameter's value came from: `"case"` and its
case pointer, or the earlier source's name and its fact pointer. The values echoed are not repeated:
the acquisition holds them.

### 8. Targets, classes and admission

The **targets** of a source are its fact targets and its evidence targets, fixed by the dialect and
not by what an acquisition returns: for a copy, its entries' `target` pointers and `requirement`
ids; for a rule, every pointer of every claim form's `facts`, and every requirement of every claim
form's `evidence`, over all clauses. Every target is recorded in the lineage (§9.3), with a value or
without.

#### 8.1 Facts and evidence

A **fact target** is a pointer other than the empty string. Writing a value at it in a document
creates each object on the way, every token naming an object member. No fact target of one source
may equal another, or be a prefix of another by whole tokens, of the same source or another, the
case included; no requirement may be an evidence target of two sources; and there are at most 256
fact targets and 128 evidence targets in all. A dialect that breaks one of these is refused.

A preparation's **facts document** is `{}` with, for each outcome in order (§9.2) and each fact
target its claim gives a value, that value written at the target. Its **evidence-availability
document** is an object giving, for each outcome in order, each requirement its claim's
`evidenceAvailability` names, that value, `unknown` included. (No vector decides that `unknown` is
written rather than left out.) They are the facts document and the evidence-availability document
an evaluation takes (Core §8.2), and those its record carries (§11).

#### 8.2 Classes and admission

A target's **class** is its source's: `asserted` for the case and a local file, the profile's for
every other source. `record` names the acquisition channel, a signed read of a system, and not the
authorship or truth of every byte the system holds; `generated` names a model's answer.

A source's **generated influence** is true when its class is `generated`, or when a source parameter
it declares comes from a source whose generated influence is true; each of its targets carries it.
A dependency so cannot erase a model's influence. (No vector holds a generated source, so no vector
decides this.)

Each target **admits** `asserted` and `record` by default. `admits`, an object of `facts`, mapping
fact targets to arrays of classes, and `evidence`, mapping requirements to arrays of classes, both
optional, replaces the list of each target it names. A target is admitted when its class is in its
list and, when its generated influence is true, so is `generated`. Every target is held to it, one no
acquisition reached included; a target not admitted is `admission-refused`. A target named in
`admits` that no source writes is refused with the dialect.

### 9. The preparation

#### 9.1 Members

A preparation is a JSON object of exactly:

| Member | Form | Meaning |
| --- | --- | --- |
| `version` | the integer `2`, or `3` | the preparation's version, its dialect's `version` |
| `verifiedAt` | a timestamp | the instant: the one every freshness check is held to, and the value of `runAt` |
| `mappingDigest` | a digest | the dialect digest (§2) |
| `verification` | the string `verified acquisitions; session sealing and input truth are not established` | the preparer's account of its checks, the same in every preparation of this version |
| `cites` | an array | every acquisition's citations (§5.2), in the order below |
| `lineage` | an array | §9.3 |
| `outcomes` | an array | §9.2 |

In versions 2 and 3 alike, `cites` is ordered by `callIndex`, those of one index in the order of
`sources`, as the reference Runner writes it: each acquired source adds its one citation, and the
case, a local file and a skipped source contribute none. A `research` source has a rule of its own,
which no vector holds: in a preparation with one, `cites` is in the order of `sources` instead, the
`research` source adding every retained response's citation in `R.responses` order, followed by the
record's own citation when it has one, and every other acquired source its one citation. The
research list is also its lineage entries' `receipts` (§9.3). (No vector decides the rule of
`research`.)

#### 9.2 Outcomes

There is one outcome for the case, first, and one for each source, in the order of `sources`. A
source is **skipped** when a source parameter it declares has no value (§3): it is not acquired and
its read does not apply. An outcome is an object of:

- `name`: `case`, or the source's name;
- `parameters`: an object giving each parameter of the scope (§3), `runAt` included, its value, with
  the literal the case or the earlier source wrote; for a skipped source, those that have a value;
- `arguments`: the source's request (§4.1), for a source acquired, and absent otherwise;
- `claim`: the claim (§§6–7), and absent for a skipped source;
- `status`: the claim's `acquisitionStatus`, or `dependency-unavailable` for a skipped source;
- `reason`: the claim's `reason`, or `dependency-unavailable` for a skipped source.

(No vector holds a skipped source, so none decides the form of its outcome or its entries.)

#### 9.3 Lineage

There is one lineage entry for each target of the case and of each source, in the order of the
outcomes; within one outcome, its fact targets ordered by code point, then its evidence targets
ordered by code point. (No vector decides the order within one outcome.) An entry is an object of:

| Member | Value |
| --- | --- |
| `source` | the outcome's `name` |
| `kind` | `fact` or `evidence` |
| `target` | the fact target or the requirement |
| `class` | the target's class (§8.2) |
| `generatedInfluence` | its generated influence |
| `present` | `true` when the claim gives the target a value — a value at the pointer, or any availability for the requirement — and `false` otherwise |
| `status`, `reason` | the outcome's |
| `basis` | the claim's `basis`, or `[]` for a skipped source |
| `candidateFrom` | the pointers of the value read that the dialect could copy to the target, distinct, ordered by code point: a copy entry's `source`, or each `from` of a claim form that writes the target; absent when there is none, as for a rule's evidence target |
| `readDigest` | the read digest (§6) |
| `receipt` | the acquisition's citation; for `research`, the record's own citation when it has one; absent for the case, a local file, a skipped source and a research record with no receipt of its own |
| `receipts` | added in version 3: for an acquired `research` source, the same ordered list of citations it adds to `cites` (§9.1), including the record's own when present; absent otherwise |
| `calculation` | §7, for a calculated source that was acquired; absent otherwise |

`candidateFrom` lists what the dialect could read into a target, and not what was read; `basis`
lists what was read to decide.

#### 9.4 What derives a preparation

A preparation holds the instant, the dialect's digest, each scope's values, each request, each
claim and each acquisition's citation. It does not hold the case, the results or the receipts, which
a verifier is given (§11). What derives a preparation is the dialect, the case, the acquisitions,
the profiles and the instant, and nothing else.

#### 9.5 The canonical form of a preparation

A preparation's digest is taken of all of it in this form, the form the Runner digests a
preparation in (Runner, "The canonical form of a preparation"):

- **Members**: each object's members ordered by name, comparing the names' UTF-8 bytes, which orders
  them by code point; an array keeps its order.
- **Whitespace**: none between tokens.
- **Numbers**: the literal, its characters kept. Every number of a preparation is an integer (§1):
  `-0` stays `-0`, and `9007199254740991` and `-9007199254740991` are written whole, without an
  exponent.
- **Strings**: `"` and `\` are written `\"` and `\\`; U+0008, U+0009, U+000A, U+000C and U+000D are
  written `\b`, `\t`, `\n`, `\f` and `\r`; every other code point below U+0020 is written `\u00`
  and two hexadecimal digits; `&`, `<` and `>` are written `\u0026`, `\u003c` and `\u003e`, and
  U+2028 and U+2029 are written `\u2028` and `\u2029`; every other code point is written as its
  UTF-8 bytes, `/`, U+007F and every character outside ASCII included. `A&B <x> café ☃` is written
  `A\u0026B \u003cx\u003e café ☃`.
- **`true`, `false` and `null`** as they are.
- **`verifiedAt`** is 20 characters, and each outcome's `parameters` gives `runAt` the same string.
  A preparation recomputed at another instant is another preparation, with another digest.

This is not `canon`, which writes `&`, `<` and `>` as they are and `-0` as `0`. A dialect's, a
profile's, a read's and a result's digests, and the bytes a receipt's signature covers, are
`canon`'s.

The preparation's **digest** is the digest of those bytes, and its **binding** is these bytes
exactly, the digest in place of `D`:

```text
{"kind":"judgment-pack-runner/preparation/1","digest":"D"}
```

`kind` then `digest`, with no whitespace: the member a runtime's evaluation record carries as its
caller gave it (runtime ADR-0050). The scheme names the Runner because the Runner defined it; every
binding recorded names it, and this document keeps it unchanged.

### 10. The output side

A dialect's output side says how a disposition becomes the arguments of a write. An **output
dialect**, version 1, is a JSON object of exactly `outputVersion`, the string `"1"`; `platform`, a
non-empty string naming the catalog platform whose write tools it holds, as the gateway's engine
configuration names one; and `policies`, an object mapping each write tool's name to a **decision
policy** in the form the gateway's engine configuration gives an entry of a platform's
`decisionPolicy` (the gateway's `docs/design/engine-config.md` at `v0.15.0`, the release the Status
names, and gateway §1.2a, `policy`): `outcomes`, the outcome ids a record must have decided; optionally `packs`,
`reviewed` and `requireSignedRecord`; `bind`, pairs of a pointer into the write's arguments and a
pointer into the record's `inputs.facts`, whose values must be equal; `fix`, pairs of a pointer into
the arguments and the value the argument there must be; and `closed`, whether every argument must be
reached by `bind` or `fix`. This document restates none of it: the gateway's form is the output
side's.

A policy's digest is the digest of its `canon` bytes, which is the `policy` an action receipt
carries for a write held to it (gateway §1.2a); an output dialect is digested so too. The input
side and the output side are two documents, each with its own digest, so that a version-2 dialect
document stays the Runner's mapping v2 document byte for byte.

A policy holds a write to its decision record at the moment of the gateway's check: by `bind`, an
argument to a fact the record evaluated; by `fix`, an argument to a value the policy fixes; and, by
`closed`, the arguments to exactly those named. What that establishes is the gateway's (gateway
§1.2a, "What `decision` establishes"): not that the target read the arguments as intended, not that
the target was unchanged since the record, and not that a person approved the write.

No preparation reads the output side, and no conformance class of this document reads it. Its
vectors are deferred to a later RFC.

### 11. Verifying a preparation

A preparation verifier is given:

- the dialect document; the case document; the acquisitions (§5.2), `{}` when there are none; the
  input profiles it trusts (§5.1); and, for a dialect with an unbound source, its binding document
  (§4.4);
- the **preparation** to verify;
- optionally, the **record**: the line of bytes, without its newline, of the runtime evaluation
  record whose binding it holds to the preparation. A Runner export of version 2 carries the record
  as the member `run.audit` of its `run.json`, and not its bytes: the line taken from such an export
  is that member's value exactly as `run.json` writes it, with no re-encoding; and
- whether it **requires a binding**.

**Replaying research.** For a `research` source (§4.3), the verifier replays the source's read over
the caller-assembled research record `R`, carried as `response.result`, at the given preparation's
`verifiedAt`. `R.responses` retains the AI connection's answers and the web reads retained with it.
Before the read applies to `R`, each retained response is checked under its own trusted profile,
over its own request and result, with §5.2's checks 1–5, times and sessions; the record's own
receipt, when present, is checked too. The findings below run per source and, within it, per
response in `R.responses` order, then for the record's own receipt when present. The recipe's
`question`, `constraints`, `model`, `evidence`, `fields` and `capabilities` are recorded in the
dialect and under its digest. The model and required capabilities are held to the trusted
profiles then bound (§4.4, §5.1), not to the model's actual execution. The recipe is never
re-executed: verification calls neither the model nor the web. No model output is produced
or compared. For §6.4's read, the same checked record and the declared earlier results form the
combined value; those earlier acquisitions have already passed their own checks. A replay
establishes only what §13 says a derivation and an acquisition establish. (No vector decides this.)

**A research fixture.** In the terms of the staging README
([`conformance/dialect/README.md`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/conformance/dialect/README.md)),
one fixture is a directory holding:

| File | Given to the verifier as |
| --- | --- |
| `mapping.json` | the bound dialect, with the research recipe and its read (§4.4) |
| `unbound.json` | beside it, the published dialect with unbound research sources |
| `binding.json` | beside it, the binding document used to make `mapping.json` |
| `case.json` | the case document, including the recipe's case parameters |
| `sources.json` | the acquisitions: each `R`, including `R.fields` and `R.responses` (§4.3, §5.2) |
| `profiles.json` | every assigned AI and web profile, including assignments no response uses |
| `run.json` | the preparation, `run.input.preparation`, and the evaluation record: the bytes `run.auditBytes` holds in standard base64, or, in an export of version 2, `run.audit` exactly as `run.json` writes it, with no re-encoding |

In `sources.json`, each `R` is carried as `response.result`. Its `responses` array retains every
response's `profile`, `request`, `result`, `receipt` and `salts`; the record's own `receipt` and
`salts` sit beside `result` when present. Every retained response names an assigned profile.
The verifier trusts profiles out of band (§5.1), never by their presence in a fixture.

`preparation.json` and `preparation.sha256` hold what the verifier must compute: the preparation's
canonical bytes and their digest, recomputed from the retained inputs at its `verifiedAt`. The
record is the runtime evaluation record, distinct from the research record in `sources.json`.
The staging manifest gives `requiresBinding` and the expected answer, `expectedResult` with
`expectedBinding` for a reading or `expectedFinding` for a finding, as for every staged vector.
The fixture layout is fixed, but no Runner prepares the `research` kind and no vector holds one.
It is defined, and not claimable; the first fixture waits for a preparer of the `research` kind.
(No vector decides this.)

**The two fixture lists to record.** Each reading or finding variant below calls for a separate
fixture directory in that layout for each of two examples, named `<example>-<item>-<variant>`.
`<example>` and `<item>` are the names below; `<variant>` identifies the individual case, such
as `work-item-triage-presence-optional-omitted`. Refusal variants are reader tests, not fixtures,
until the staging README defines a refusal row form. No such fixture is recorded: no Runner
prepares the kind, and neither a synthetic expected digest nor a hand-written receipt stands
in for a recording. No research vector or conformance claim is made. The examples are:

- `gtm-company-person`: a company's `company-id` (`text`), `employee-count` (`integer`),
  `revenue` (`decimal`), `active` (`boolean`), `roles` (`text-list`) and `employee-range`
  (`range`); a person's corresponding record has `person-id`, `experience-years`, `allocation`,
  `contactable`, `roles` and `experience-range`, of those same six types. All identifiers and
  observations are synthetic. A copy can write the whole `R.fields` object to a facts target;
  a rule can instead write a found value to a qualification target. The declarations and reads
  are distinct: fields describe research, while the pack still defines qualification policy.
- `work-item-triage`: a work item's `item-id` (`text`), `points` (`integer`), `estimate`
  (`decimal`), `blocked` (`boolean`), `labels` (`text-list`) and `effort-range` (`range`);
  a selected item leads to a child follow-up record of the same types, with its own id. No
  company-domain or person-specific identity rule is built into these fields.

For both examples the item names and expected checks are:

1. `valid-types`: all six types, both integer and decimal ranges, empty and non-empty lists,
   decimal signs and scales, with retained citations and generated admissions; a reading with
   `expectedBinding: "matches"`. Test a source asking for `answer` alone, and one also asking
   for `search` and `page`; both use their assigned profiles and §9's citation order.
2. `presence`: separate valid readings for an omitted optional entry, required `not-found`,
   integer zero, decimal `"0"`, boolean `false` and text `""`. Separate refusals for an omitted
   required entry, `null` entry or value, `null` list item or range endpoint, a numeric decimal,
   mixed or reversed range endpoints, an unknown field and a value on a non-found entry:
   `input-malformed`. No absent, null or false value is replaced by a default.
3. `bounds-and-cites`: recordings at every new maximum and refusal inputs one over each:
   `input-over-bound`. Include an empty declaration list, empty found citation list, duplicate
   field, invalid index (including `-0` or one at or above `responses`' length), duplicate index
   and URL-only citation, all `input-malformed`; the index range is no §12 maximum. Missing
   cited response bytes give `acquisition-missing`. Keep document and nesting bounds in force.
4. `stale-and-conflicting`: fresh receipts carrying an explicitly stale observation, and two
   conflicting typed values with separate citations, yield the declared unknown or fallback
   claim and a reading. A stale entry may have no cited observation. An actually expired receipt
   gives `acquisition-stale`; a plain research rule with a fact `from` of
   `/fields/<name>/values/0/value` gives `input-malformed` (§4.3). This does not test the truth
   of a claimed `found` status.
5. `failed-fallback`: primary `not-found`, secondary `stale`, and a third source's `conflicting`
   entry. The third source's rule names the earlier two, tests their statuses in declared order,
   and derives `unknown` with no resolved target. Include success from secondary, all candidates
   unavailable, and a skipped earlier source with no acquisition, each handled by explicit
   clauses. A needed response absent gives `acquisition-missing`, a bad receipt
   `acquisition-invalid`, a later-source reference or overlapping target `input-malformed`, and
   a matched rule's missing value pointer `read-failed`; none silently tries another source.
6. `changed-binding`: retain `unbound.json` and `binding.json` beside `mapping.json`, the bound
   dialect, as the staging README requires. A second installation changes one generated AI or
   web assignment and its matching trusted profile. Every retained response's profile reference
   names its new assignment, and its receipt verifies under that profile; all earlier checks
   pass. With the old preparation fixed, the valid new bound dialect gives `preparation-differs`;
   an old profile digest, wrong model, missing capability or non-generated profile gives
   `profile-mismatch`. A binding for another published
   digest, a partial assignment or an extra capability gives `input-malformed`. A separately
   recorded preparation under the second binding may read; the first is not relabelled.
7. `changed-response`: change a retained result with its receipt and the independent expected
   preparation fixed: `acquisition-invalid`. Change `R.fields` under its own fixed receipt:
   the same finding. Without that receipt, a field change affecting a derived claim gives
   `preparation-differs`; a well-formed change to an unread field need not give a finding.
   With no record receipt, reorder responses, updating indices to cite the same responses,
   with the preparation fixed: the changed citation order gives `preparation-differs`. Replay
   makes no model or web call.
8. `selected-parent-child`: retain the selected parent and the resulting child using
   [RFC 0020](../rfcs/0020-workflow.md) §§3–5 and §11's output, selection and execution records.
   A stage's output pointer resolves in prepared facts, never directly in `R`; `cardinality`
   `one` can project the copied fields object. The selected payload's `/company-id/value` or
   `/item-id/value` projects to the next case under that workflow's typed bindings. Presence,
   generated influence, closed offered sets and parentage use its rules. Its §11 acceptance
   construction remains the two-stage `operation` run; this research plan neither replaces
   that demonstration nor changes the workflow's version or refusal codes. The analogous
   research recordings wait for research support. Workflow version 1 (RFC 0020 §4) admits no
   stage whose dialect has a research source. RFC 0020 §4's sentences that only `operation` has
   an unbound form and that portable research binding is deferred, and its question 2, are
   superseded pending its own revision. The coordinator is to file that revision as an issue.

The staging manifest's existing `reading` and `finding` rows keep their meanings. Malformed
and over-bound variants are reader tests under §11, with the exact refusal report as expected
output, not fixtures, until the staging README defines a refusal row form.
No manifest or file under `conformance/` is added by this plan. (No vector decides this.)

**Refusals.** Before it recomputes anything, it refuses the reading, which then reports nothing but
the refusal, at the first of these phases that fails, in this order:

1. the bounds of §12 that are measured on bytes — a document's size, its nesting (the case
   document's at 32 levels), and each number literal's characters and exponent — taken on every
   document before any is read: `input-over-bound`;
2. every document read as §1 reads one, and the record as one line: `input-malformed`;
3. the bounds of §12 that are counts — the sources, the parameters in a scope, the clauses of a
   rule, the conditions one `all` or `any` lists, the `unwrap` pointers, the fact and evidence
   targets, the retained responses per `research` source (at most 64), and every research field,
   text, list, observation, citation, capability and read-source maximum in §12 — and the nesting
   of each acquisition's result, taken wherever measurable before any form: `input-over-bound`.
   Type-dependent maxima measure each value by its field's declared `type` when that `type`
   is one of §4.3's six types, and not otherwise;
4. a dialect document that is an object whose `version` is an integer of a version this document
   defines, `2` or `3`, that the verifier does not read: `version-unread`;
5. every document's form — the dialect against §§2–8, every rule they give it included, and each of
   its sources against §4's members and its kind's, whichever its kind, and each reconciliation
   read against §6.4; the binding document against §4.4; a profile against §5.1 and the key rule;
   the acquisitions against §5.2, including every research field entry against its declaration
   (§4.3); the preparation's `verifiedAt` against the timestamp form with an instant; the record
   against its reading below: `input-malformed`;
6. a dialect that names a kind the verifier does not read: `kind-unread`.

Some bounds are measured later, because they cannot be measured sooner: an unwrapped string's
bytes, and the nesting and number literals of the value it holds, are measured when it is
unwrapped (§6.1), during recomputation. Over them the reading is refused, `input-over-bound`, with
nothing reported but the refusal. The nesting of §6.4's combined value is likewise measured
when it is formed, before its rule runs, with the same refusal.

**Findings.** Otherwise it recomputes the preparation at the given preparation's `verifiedAt`, by
§§3–9, and ends the reading at the first of these findings, in this order, reporting that one:

1. `profile-mismatch` (§5.1, §4.1, §4.4), the sources taken in their order, and within a `research`
   source its AI profile first, its web profiles in `search`, `page` order when assigned, then
   each retained response's profile in `R.responses` order;
2. for the case: `parameter-invalid` (§3), its parameters in their order, then `read-failed` for its
   read (§6.2);
3. for each source in its order: `parameter-invalid` for a source parameter it declares, in their
   order (§3); then, for its acquisition and its read, `acquisition-missing`,
   `acquisition-unexpected`, `acquisition-invalid`, `acquisition-stale`, `acquisition-sessions`
   (§5.2), `calculation-invalid` (§7) and `read-failed` (§6), in that order. For a `research` source,
   check for a missing or unexpected source member first, then apply the acquisition findings to
   each retained response in `R.responses` order, completing one response's checks before the next;
   then check the record's own receipt when present, and apply the source's read to `R`. After the
   last source, `acquisition-unexpected` for a member of the acquisitions that names no source;
4. `admission-refused` (§8.2);
5. **`preparation-differs`**: the recomputed preparation's canonical bytes (§9.5) are not the given
   preparation's, written in that form; a given preparation that cannot be written in that form
   differs;
6. with a record, **`record-inputs-differ`**: the record's `inputs.facts` is not the facts document
   (§8.1), its `inputs.evidence` is not the evidence-availability document, or its `cites`, absent
   being the empty array, is not the preparation's `cites` as a set, each compared as JSON values.
   The citations are compared as sets: a citation either side gives twice is one member of its set,
   and how many times one is given is not compared;
7. with a record that carries a `binding`, **`binding-foreign-kind`**: the record's `binding` is not
   an object whose `kind` is the string `judgment-pack-runner/preparation/1`; no digest is compared;
8. with a record that carries a `binding`, **`binding-mismatch`**: the bytes of the record's
   `binding` are not the preparation's binding (§9.5), byte for byte: another digest, or the same
   members written otherwise, in another order or with whitespace;
9. **`unbound`**: a binding is required, and no record is given or the record carries no
   `binding`.

**Reading the record.** The record is one line, holding neither a line feed nor a carriage return,
that is one JSON object read as §1 reads a document, with an object `inputs`. Its member `binding`
is read by that exact name: a record that names a member `binding` but for case is refused, not read
as one with no binding. Two member names differ **but for case** when they are not equal, and are
equal once each of `A` to `Z` in them is mapped to `a` to `z` and nothing else is: ASCII case only,
with no other folding. A record **carries** a binding when it has a member of that name, whatever
its value: a `binding` that is `null` is carried, and is not of the binding's form (finding 7); a
record with no member of that name carries none, which is no finding unless a binding is required
(finding 9). The member's bytes are those of its value as the line writes them, from its
first character to its last; nothing is canonicalised again. This document reads nothing else of the
record. It does not check the record's signature, its chain or its witness, which the runtime's
reader and the checkpoint witness statement's reader check; a binding commits a preparation only
under a record signature that verifies (§13).

**The reading.** A reading with no finding reports:

- the preparation's **digest**;
- the **binding**: `matches` with a record whose binding matches, `absent` with a record that
  carries none, and `not-checked` with no record;
- the **facts document** and the **evidence-availability document** (§8.1);
- **`targetsByClass`**, an object giving `asserted`, `record` and `generated` each the number of
  lineage entries of that class: every target counted, with a value or without;
- **`unsignedParameters`**, when it is not empty; and
- **`unsignedFreshness`**, when it is not empty.

**`unsignedParameters`** names the parameters a derivation read that no receipt commits. It has an
entry for each source that was acquired, whose read is a rule that was applied (not a skipped
source, not a calculator that did not compute), that has a target, and whose rule's conditions name
a parameter that its own acquisition does not commit. The parameters a rule's conditions name are,
at any depth, `equalsParam`'s `param` and `freshWithin`'s `asOf` and `maxAge`, and not those it only
declares. A source's own acquisition commits a parameter its request commits (§4.1), and an input
its calculator echoed that is bound to the parameter (§7); another source's receipt commits nothing
for it. An entry is `{"source", "parameters", "targets"}`: the source's name; each such parameter as
`{"name", "kind"}`, ordered by name; and the number of the source's targets. The kinds:

- `runAt`: the parameter `runAt`;
- `ambiguous-text`: a parameter that would be of kind `case`, `local-file` or `upstream`, which the
  source's request carries only in a `$text` that names another parameter too;
- `case`: a case parameter;
- `local-file`: a source parameter from a local-file source;
- `upstream`: a source parameter from an earlier source that has an entry here with a parameter of
  kind `case`, `local-file`, `upstream` or `ambiguous-text`;
- `upstream-runAt`: a source parameter from an earlier source that has an entry here whose
  parameters are all of kinds `runAt` and `upstream-runAt`.

A source parameter from an earlier acquired source that has no entry — whose value its rule derived
from signed values alone, or which it copied from its result — is not named. The entries are in the
order of `sources`.

**`unsignedFreshness`** is `{"against": "preparation.verifiedAt", "verifiedAt": V, "sources": L}`,
`V` the instant and `L` an entry, in the order of `sources`, for each source acquired:
`{"source", "checks", "targets"}`, `checks` being `["acquisition"]`, or
`["acquisition", "calculation"]` for a calculator that computed, and `targets` the number of the
source's targets. Each such freshness was judged against `verifiedAt`, which no receipt covers: a
matching binding in a record whose signature verifies is what commits it (§13).

**The report.** A verifier reports a reading, a refusal or a finding as one JSON object, written in
the preparation's canonical form (§9.5), whose member `result` is `reading`, `refusal` or `finding`.
A refusal is exactly `{"result": "refusal", "refusal": C}` and a finding exactly
`{"result": "finding", "finding": C}`, `C` its code. A reading is `result` and the members listed
above, exactly: `digest`; `binding`; `facts`, the facts document; `evidence`, the
evidence-availability document; `targetsByClass`; and `unsignedParameters` and `unsignedFreshness`
when they are not empty. A verifier that is a program writes the report on its standard output, as
one line, and exits with status 0 for a reading, 1 for a refusal and 2 for a finding, and with
status 3, writing no report, when it could not run at all, as on an argument it does not take or a
file it cannot open. A verifier that is a library states the same three outcomes in its own idiom.

### 12. Bounds

A verifier holds its inputs to the Runner's bounds (Runner, "Numeric and resource profile"), with
version 3's research bounds added:

- the dialect at most 131072 bytes; the dialect, the case and the acquisitions together at most
  2097152 bytes; the profiles, and a binding document, each at most 65536 bytes; and the preparation
  and the record each at most 8388608 bytes;
- at most 16 sources; 64 retained responses per `research` source; 64 parameters in one scope;
  64 clauses in one rule; 64 conditions listed by one `all` or `any`; four `unwrap` pointers;
  200000 bytes in one unwrapped string; and 256 fact targets and 128 evidence targets;
- at most 32 levels of nesting in a value a read applies to — the case document, a result, an
  unwrapped value — and at most 64 in any document; and
- number literals of at most 128 characters, whose exponent, when they have one, has a magnitude of
  at most 308.

For research, §4.3's maxima also hold: 64 declared fields and 64 answer entries per source;
64 UTF-8 bytes per field name; 2048 per description; 256 per model name; 4096 per evidence
instruction; 8192 per text value; 64 items per text-list, each at most 1024 UTF-8 bytes;
128 ASCII characters per decimal string, a range endpoint included; 64 conflicting observations
per entry; 64 indices per citation array; three capabilities per source or profile; two web
assignments per source; and 15 earlier sources per reconciliation read (§6.4). Count strings
after JSON decoding. Wrong forms and unmet minima are `input-malformed`; exceeding these maxima
is `input-over-bound`. The document-size and nesting bounds still hold arbitrary retained
results, requests, constraints and the combined value of §6.4. Nothing is truncated to fit.

Nesting is counted from the document's root at zero, and every object and every array is one level
of it: `{}` is at one level, `{"a": []}` at two, and a document that is a string, a number, `true`,
`false` or `null` at none. On the bytes, a **number literal** is a maximal run, outside strings, of
the characters `0` to `9`, `+`, `-`, `.`, `e` and `E`, and its **exponent** is the digits after its
first `e` or `E`: the run of digits that follows it, or that follows the `+` or `-` after it; a
literal with no such run has no exponent. An unwrapped string's bound is counted on the UTF-8 bytes
of its decoded value.

Over any bound it refuses the reading, `input-over-bound`, and MUST NOT read part of it. The bytes are
bounded first, by the documents' sizes, before any is read; §11 gives the order of the rest. A
preparer refuses the same inputs before it writes a preparation.

### 13. What a preparation establishes, and what it does not

A preparation has parts of three natures, and what it establishes differs by part. A
**derivation** — a copy, a rule, a calculated value's lineage, the facts and evidence-availability
documents, the preparation's form and its digest — is recomputable: a verifier that recomputes it
establishes it itself, from the inputs, trusting no one for it. An **acquisition**'s bytes are not
recomputable: they are held by their digest, under a receipt, and what they establish is the
receipt's business, which is byte lineage and not truth, the stance Core §6.3 takes of a source.
For research, each retained response is held this way, and the record itself only when it has its
own receipt. The caller assembles the research record: fields, membership and order are the
caller's assertion, even when a receipt commits the assembled record's bytes. An **asserted**
input is the operator's say, and recomputation shows only that it was carried faithfully. A page
cited by URL alone is no retained response; the claim it supports is the answer's say.

- **The facts and the evidence availability a copy or a rule derived.** Establishes: that these
  facts and this evidence availability were derived from those bytes by these rules, at that
  instant.

  Does not establish: that the rule is right for the pack, or reads what its author meant; that a
  target with no value has none in the system.

- **A calculated value's lineage.** Establishes: that the calculator's answer, in the bytes
  acquired, echoed the inputs bound to this case, and reported its tables as of instants within
  the dialect's limits before `verifiedAt`.

  Does not establish: that the calculator is deterministic or calls no model; that its arithmetic
  or its tables are right; that it used only what it echoes; that an `asOf` is true.

- **An acquisition of class `record`, verified under a trusted profile.** Establishes: byte
  lineage: the holder of the gateway key the profile pins signed a receipt that names these bytes
  by their digest, this request by its commitment, this adapter, shape and endpoint, at these
  times; what more the receipt says is the gateway's (gateway §1.2a, §5).

  Does not establish: that the system's record is true, current or complete; that the adapter
  reported its acquisition truly; that the session is sealed or complete, or that the caller did
  not choose among answers; anything once the gateway's key is copied.

- **An acquisition of class `generated`, a research record above all.** Establishes: the least:
  that each receipt holds its request and returned bytes under its trusted profile; for research,
  this applies to every retained response, and to the record itself when it has its own receipt;
  the declared model and capabilities match the profiles then bound, without establishing actual
  model use.

  Does not establish: that the answer is right, complete or current, or the model's own; that a
  candidate it names exists; that a page it cites says what it quotes, beyond a receipt for that
  page; that the retained set is every answer and every read the run made; that the caller did not
  choose among runs or responses; that the model made a read retained with the answer; that the
  caller's asserted membership and order describe the run; that a field's status, value or
  citation indices are the model's rather than the caller's say; that a cited response supports
  the value it is cited for; that a `stale` or `not-found` status is right; which model answered.

- **An asserted input: the case, a local file, a parameter no receipt commits.** Establishes: that
  the preparation carried what the operator supplied, faithfully.

  Does not establish: anything about it: an asserted input rewritten with its preparation
  recomputed verifies as the original did; `unsignedParameters` names the parameters a rule read
  on the operator's say.

- **A binding document (§4.4), and the bound dialect it yields.** Establishes: that the bound
  dialect is the published one with each unbound source bound to the profile the binding document
  names.

  Does not establish: that that profile is the one the publisher meant, or reads the system the
  publisher's fixtures were recorded from: the binding document is the installation's statement; a
  record commits the bound dialect, its profile assignments included, and neither the binding
  document's digest, nor the published dialect's, nor the catalog names the binding removes.

- **`verifiedAt`.** Establishes: that every freshness check holds against it.

  Does not establish: that it was the instant of admission: without a binding no signature covers
  it, and a preparation recomputed at another instant verifies as the original does.

- **A binding that matches, in a record whose signature verifies (a check this document does not
  make).** Establishes: that the preparation, its instant included, is the one committed in the
  record when its key's holder signed it.

  Does not establish: anything against the operator, who holds the key and the clock and can
  recompute, write and sign again, which only a checkpoint held independently from before the
  change shows; when anything was prepared: a binding carries no time.

- **A binding that matches, with no signature checked.** Establishes nothing by itself.

Nothing establishes an operator's intent, a source's truth, a model's correctness, or anything the
dialect does not name: a target the dialect does not map is unknown to the evaluation, which its
omission does not guarantee (Runner, "Release checks, runtime and offline verification"). A reading,
and a report built on one, MUST NOT be described as establishing anything listed above as not
established.

### 14. The preparation verifier

An implementation is a *conforming preparation verifier* when, for every reading it admits, it gives
the refusal, the finding or the reading §11 defines, and when it gives every vector's expected answer
in the dialect vectors published with the specification version it names. Its claim takes the form
"a preparation verifier conforming to `spec/dialect.md` of specVersion *X*, reading dialect version
2, or versions 2 and 3, and the kinds *K*, and `operation` of the shapes *S*", and names only
versions, kinds and shapes that the vectors published with that version exercise (§4). The class is
independent of Core's four classes and of the witness-statement reader: none implies it, and it
implies none. It says nothing about a preparer, which this document does not define as a class: a
verifier's agreement with a preparer shows that the two read the format alike, and no more. A claim
of this class MUST NOT be described as establishing anything §13 says a preparation does not
establish.

Until a specification version publishes the dialect vectors, no claim of this class is available.

## Alternatives

- **Leave it the Runner's.** The status quo. Every verifier is built against `MAPPING-V2.md`, which is
  normative for one implementation, moves with its releases, and describes the Runner's service, its
  exports and its journal beside the format, so that a reader must separate the two itself. Coherent
  while the Runner is the only reader; not once a counterparty checks a binding, or the Exchange
  publishes an entry.
- **Cite, without restating.** The specification would name `MAPPING-V2.md` at a commit and bind the
  vectors by their digests. Cheaper, and the bytes would be as fixed. It leaves the text under one
  implementation's governance, so that a correction there silently is, or is not, a correction here;
  and the text would stay the Runner's words for the Runner, which this RFC finds in places describe
  the Runner rather than the format. The maintainer's decision is otherwise.
- **A section of Core §8.2.** Core takes one facts document and "defines no fact namespace, merging,
  or acquisition"; a dialect is acquisition and merging. Every Core version would carry a format no
  Core class reads, and an evaluator would answer to it. A companion document, with its own class,
  keeps the two apart.
- **An extension (Core §9).** An extension is a member of a pack, and an optional one must not change
  Core semantics. A dialect is not part of a pack: one pack is read through many systems, each with
  its dialect, and a pack that carried its dialects would name its systems. Rejected.
- **A profile.** A profile constrains packs, and a dialect constrains nothing in one. The nearest
  draft is [RFC 0003](0003-evidence-reference.md), a candidate profile that keeps an evidence
  reference a bare identifier and leaves the derivation to "the resolving layer". This RFC specifies
  that layer's derivation and its record; RFC 0003 stays the place for a reference convention.
- **The specification's own names.** Renaming `operation`, the binding's scheme or the preparation's
  members would make every recorded binding stop matching, and the vectors would no longer be the
  Runner's bytes. Rejected. The issue calls one kind "a connection's record" and another "an MCP
  query"; both are `operation` here, the name the Runner's documents and vectors write — an operation
  is a tool of a gateway source of shape `mcp`, a SQL tool among them — and `record` is already a
  class.
- **The output side in the same document.** A member of the dialect document would make it no longer
  the Runner's mapping v2 document. Two documents, each with its digest, keep version 2 byte for
  byte.

## Compatibility

- **Packs, documents and evaluators.** Unchanged: no member of any pack, schema or disposition
  changes, and no Core class gains or loses a requirement.
- **The Runner.** Keeps its service, its exports and `verify-run`. Every mapping v2 document it
  accepts is a version-2 dialect document, and its preparation is the format's. No rule the text
  gives a verifier differs from what `verify-run` applies to a preparation, as far as the vectors and
  the Runner's documentation show; where the text takes a position no vector decides, the Runner's
  behaviour is the evidence, and a difference found is a defect in the text (Unresolved question 1).
  On acceptance, the Runner may point `MAPPING-V2.md`'s canonical-form subsection here; that is its
  decision.
- **The runtime.** Unchanged. It records the binding as given and interprets nothing (ADR-0050), and
  the binding's bytes and its digest are unchanged.
- **The gateway.** Unchanged. Its canonical form, its receipt and its decision policy are referenced,
  not restated.
- **The Desk.** Writes this format through the Runner today. A version-3 kind needs a preparer before
  the Desk can write one.
- **Versioning.** The dialect document's version is its `version` member: 2 is the Runner's mapping
  v2; 3 adds the unbound form and the kinds of §4.3, and the reference Runner reads it. A
  preparation's version is its dialect's. The output side has its own `outputVersion`, `"1"`.
  Every object is closed at every level, so a reader that knows a version refuses a member of a
  later one rather than skipping it.
- **On acceptance**, with the landing pull request and not before: Core §1.1's list of normative
  artifacts gains the companion document, normative for the class only; its `export-ignore` is
  removed and the site publishes it as a page of its own; and the vectors wait for the next
  `specVersion`, as the checkpoint witness vectors do.

## Security and privacy

- **Credentials are never in a dialect.** A dialect names an input profile by its id and its digest,
  a connection by its name and a header by its name; a credential, a header's value and a key's
  secret are the gateway's custody. A verifier takes no key and no profile from what it verifies:
  it is given the profiles it trusts, out of band, and holds each key to the key rule before it reads
  anything signed.
- **What a preparation and its acquisitions disclose.** A preparation holds every scope's parameter
  values, every request and every claim: case values, identifiers, the records read. The
  acquisitions hold the results and the salts, and a salt opens its commitment to whoever holds both.
  A verifier given them learns all of it; the Runner's own guidance stands: "distribute it only to
  intended reviewers".
- **A research recipe can carry personal data**, in `question`, `constraints`,
  `fields[].description`, `evidence` and the people, roles and contact details its answers name.
  A dialect published to the Exchange, or to anyone, MUST carry no case, no acquisition and no
  research record; its recipe's `question`, `constraints`, `fields[].description` and `evidence`
  carry the criteria and leave every literal that names a person, a customer or an account — a name,
  an email address, a profile URL, an internal identifier — to a case parameter; and the fixtures
  published with it are synthetic. A publisher strips those before publishing, and a reviewer of an
  entry checks that it did.
- **Resource use.** A verifier reads documents it did not author. §12 bounds the bytes, the sources,
  the retained research responses, the scopes, the clauses, the conditions listed, the unwraps, the
  targets, the nesting and the number literals. Research has at most 64 declared fields and
  64 answer entries per source, 64 bytes per field name, 2048 per description, 256 per model name,
  4096 per evidence instruction, 8192 per text value, 64 list items of 1024 bytes each, 128 ASCII
  characters per decimal string or decimal range endpoint, 64 conflicting observations per entry
  and 64 indices per citation array. String byte bounds use UTF-8. A reading over a bound is
  refused, never truncated. A rule's evaluation is bounded by its clauses and their conditions.
  Receipt verification costs at most one Ed25519 check per receipt: at most 16 sources, each with
  at most 64 retained responses when it is `research`, plus the record's own receipt when present.
  That is at most 1040 receipt signature checks. Both readers measure nesting before parsing.
- **Confusion.** The two canonical forms differ in three characters and in `-0`, and a verifier that
  mixes them gets another digest: two vectors are there for it. A binding that matches, with no
  record signature checked, establishes nothing, and a verifier's report must not say otherwise.
- **No hidden execution.** Templates substitute values and render integers, and nothing in a dialect
  is evaluated as code; a `sql` source's statement is fixed text, its values bound as the provider's
  parameters.

## Conformance

The vectors are the Runner's twelve, staged in
[`conformance/dialect/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/dialect)
byte for byte: nine copied from the Runner's commit `05636ed`, the same files as at its `main`
commit `82116bf`; the tenth, added by the amendment of 2026-10-15, from its `main` commit
`c84e8e6`; and the eleventh and twelfth, `version-3-bound` and `unbound-bound-at-import`, of dialect
version 3, from its `main` commit `89cf441`; each run as its README says: the dialect, the case, the
acquisitions and the profiles, and for a dialect bound at import its binding document; the
preparation to verify and the record, from the Runner's export; and whether a binding is required.
The answer expected of the class is in this repository's manifest of them.

| Vector | What it holds | The class's answer |
| --- | --- | --- |
| `valid` | a calculated run, signed, witnessed and bound | a reading, binding `matches` |
| `recomputed-one-second-later` | the export's preparation recomputed a second later, the record as it was | `binding-mismatch` |
| `unbound-record` | a record from before the binding, a binding required | `unbound` |
| `foreign-binding-kind` | the record's binding of another scheme, signed again | `binding-foreign-kind` |
| `changed-table-lineage` | the retained lineage names another instant for a table | `preparation-differs` |
| `disposition-differs-from-audit` | the export's retained result differs from its record | a reading, binding `matches` |
| `unsigned-parameters` | rules that read `runAt`, a case parameter and one in ambiguous text | a reading, binding `absent`, the parameters named |
| `escaped-strings` | a case value holding `&`, `<`, `>` and characters outside ASCII | a reading, binding `absent` |
| `numeric-spellings` | the case parameters `-0`, 2⁵³−1 and −(2⁵³−1) | a reading, binding `matches` |
| `http-shaped-source` | one source of shape `http`, its record from a stand-in of the gateway's `adapter-http`, signed, witnessed and bound | a reading, binding `matches` |
| `version-3-bound` | the calculated run's dialect written as version 3, its source bound; a preparation of version 3, signed, witnessed and bound | a reading, binding `matches` |
| `unbound-bound-at-import` | a dialect of version 3 published with its source unbound, its binding document, and the bound dialect the Runner made of them, of shape `http`, signed, witnessed and bound | a reading, binding `matches` |

They are positive (`valid`, `escaped-strings`, `numeric-spellings`, `unsigned-parameters`,
`http-shaped-source`, `version-3-bound`, `unbound-bound-at-import`), negative (`unbound-record`,
`changed-table-lineage`) and adversarial
(`recomputed-one-second-later`, `foreign-binding-kind`, the one second and the re-signed record
being what an operator who rewrote a record would do). `disposition-differs-from-audit` is answered otherwise than `verify-run` answers it:
it alters the Runner's export, whose retained result is no part of a preparation or a record, and the
class reads its preparation and its record as the valid case's.

**Kinds.** The vectors exercise the case and `operation`, of shapes `mcp` and `http`, in version 2,
and in version 3 an `operation` bound and one unbound, of shape `http`, with its binding document;
and no other kind: `selected-file`, `operation` of shape `airbyte`, the four kinds of version 3 and
the output side have none. No specification version publishes any of the vectors, so none is
claimable.

**What no vector holds.** `unwrap`; source parameters and skipped sources; a calculator that did not
compute; a `generated` class, generated influence and `admits`; timestamp parameters; a receipt that
fails; a stale acquisition or table; a broken session form; a refusal at a bound; a paged
acquisition; a request of shape `http` other than the tenth vector's — by `POST`, with a `body`,
with no `query`, or a connection's; a kind of version 3, and a binding document or a profile bound that is refused; and the positions of Unresolved question 1, the six choices among them. The repository's tests hold the two readers to some of these
with altered copies of a vector — a result changed by a byte, an instant past `maxAge`, a profile's
digest, a reader that writes `-0` as `0` or `&` as it is — but those are this repository's checks of
its readers, not vectors: they are not the Runner's bytes, and no claim could cite them.

**What this repository checks.** Every vector file to the SHA-256 the Runner's manifest gives it, and
the Runner's manifest and README to the SHA-256 this repository records; both readers over every
vector; the counts; and this section's equality with the companion document's §§1–14.

## Implementation

1. **`tools/dialect_verify.py`**, the first reader, written from the text by the text's author with
   the vectors in view (Evidence), at `f821757` and corrected at `3c9520a`. It reads dialect version
   2 and the kind `operation`, and refuses every other kind as `kind-unread`. Since the amendment of
   2026-10-15 it reads `operation` of shapes `airbyte`, `mcp` and `http`. Since the eleventh and
   twelfth vectors were staged it reads dialect version 3 as well, the unbound form with its binding
   document among it. Since the pull request for issue #176 it reads `research` as the
   research-contract amendment defines it, bound directly or through a binding document, and
   refuses `http`, `sql` and `web` as `kind-unread` after checking their forms.
2. **`tools/dialect-verify-ts/`**, the second reader, written from the companion document's text
   alone, in TypeScript, by a different author, under the protocol the Evidence records, at
   `e2d41c5`. It reads the same versions and kind, and refuses the rest as the first does. The
   amendment of 2026-10-15 extended it as it extended the first, by the same author, which adds
   nothing to its independence (the Amendment, "The evidence"); and so did the staging of the
   eleventh and twelfth vectors, which extended both readers to version 3, by one author who had
   read both.
   The pull request for issue #176 extended both to read `research` as the research-contract
   amendment defines it, by one author who had read both, from the text: that adds nothing to the
   second's independence, and the two readers' agreement on the contract's hand-written documents
   is that author's.
3. **The Runner**, the reference preparer, with `verify-run`, a third reader of the same bytes in its
   own repository, which reads every vector through the Runner's own code.
4. **The Desk's inputs**, a writer: its mapping editor and import recipes write version-2 documents
   for the Runner today, and the research line (Desk #369, #371) would write the `research` kind.

All four are this project's. The two readers here agree on the vectors, the second written without
sight of the first; a reader by a third organisation — an auditor or a counterparty, written from
this text and the vectors — would strengthen that evidence, and none exists.

## Unresolved questions

1. **The rules no vector decides.** The text takes a position, and marks it, on eight rules that
   neither the Runner's documentation nor its vectors decide: a `{{` with no `}}` and a stray `}}` in a
   `$text`; a copy entry whose source does not resolve, for a fact and for an availability; a copy
   that names a requirement twice; `unknown` written in the evidence-availability document rather than
   left out; generated influence; a skipped source's outcome and entries; and the order of the entries
   within one outcome. Each was taken without the Runner's code. The Runner's behaviour may differ, and
   a vector from the Runner for each is what settles it; until then a difference found is a defect in
   the text. The six choices the two readers recorded (Evidence) are decided in the text now, by the
   maintainer, and no vector decides them either; on the four that are rules of reading — the
   byte-bound scans, "but for case", a `freshWithin` of another declared type and a requirement id's
   form — the Runner's `verify-run` has not been compared. The amendment of 2026-10-15 takes
   positions of its own, each marked: the shape `airbyte`; a connection's request, `POST`, a `body`,
   a template form in `path` and a request with no `query`; the rule that holds `adapter-http`'s
   `query` to string templates; a paged acquisition refused whatever the shape, which is the
   Runner's rule and which no vector shows; and every rule of the unbound form but the bound dialect
   and its digest, which a vector now holds. The amendment that read version 3 adds two refusals,
   of a version-2 member and of a member written empty in version 3 that the Runner's encoding leaves
   out, and the order of `cites` in a preparation with a `research` source. The research
   amendment adds the research replay rule and the fixture layout, also marked as positions no
   vector decides. Issue #171's result types, field statuses and citations, research profile
   bindings, reconciliation read and fixture lists are likewise decisions no vector holds.
2. **The kinds without vectors.** `selected-file`'s snapshot form is not stated here, and the four
   version-3 kinds are proposed with no preparer. When a kind gets a preparer and vectors, and whether
   its request forms here survive the first implementation, is open. So for `operation` of shape
   `airbyte` (question 10); the unbound form has both (question 11). The research replay rule and
   fixture layout are fixed; the `research` kind's first fixture still waits on a preparer
   (question 14).
3. **Whether `research` belongs in the first version that adds kinds.** It establishes the least, its
   record's form and fixture layout are fixed here (§4.3, §5.2, §11), and its first fixture waits on
   a preparer. Its result and portable binding contracts are resolved by issue #171 (question 15).
   The Desk's research work (#369) and the Runner's deferred model calls over HTTP
   still leave open when the kind is implemented and exercised by a vector.
4. **The output side's vectors**, deferred to a later RFC, and whether a reader class should hold an
   output dialect at all, when the gateway holds every write to its policy at the moment of the write.
   And a **release selector**: an output dialect is read in the decision-policy form of the gateway
   release the Status names, `v0.15.0`, and names none itself. Whether it should name the release
   whose form it uses, and what a reader does when a later release changes that form, is open.
5. **The Exchange's entry format** (#142). This document gives an entry's parts — an input dialect,
   an output dialect, profiles by digest, fixtures and the preparation they must produce — and not the
   entry itself, its licence or its governance, which are #142's record to propose.
6. **When it lands, and its versions.** As RFC 0017's first question: whether the companion document
   and its vectors land with the next `specVersion`, and whether the vectors take a `suiteVersion` of
   their own. And whether the dialect keeps the Runner's numbering, which begins at 2.
7. **The binding's scheme** names the Runner, `judgment-pack-runner/preparation/1`, because the Runner
   defined it. A second preparer would write that name too; a scheme named by the specification would
   be a new scheme, not a rename, and whether one is wanted is open.
8. **A preparer class.** This document defines a verifier and no preparer, as the checkpoint witness
   statement defines a reader and no witness. Whether a preparer class is wanted, and what it would be
   held to beyond the vectors, is open.
9. **The evidence bar, what remains.** Two readers agree on the vectors, the second written from the
   text alone (Evidence). What [RFC 0000](0000-rfc-process.md)'s bar still asks, as the maintainer's
   decision on issue #141 states it, is a comment period, which has not run. A reader by a third
   organisation would strengthen the evidence, which today rests on one project's protocol; none
   exists. For the amendment of 2026-10-15, the two readers' agreement is one author's (the
   Amendment, "The evidence"), and a reader by another author would make it independent.
10. **A vector of shape `airbyte`.** The gateway's `adapter-airbyte` answers every read with a page,
    and a paged acquisition is refused (§5.2), so no `airbyte` record is read today and no vector
    holds one. One waits for a preparer that reads a page, item by item, or for an adapter that
    answers one record without a page.
11. **A vector of the unbound form.** It needs a Runner that reads version 3 and binds a dialect at
    import, the Desk's side being
    [Judgment-Pack/judgment-pack-desk#398](https://github.com/Judgment-Pack/judgment-pack-desk/issues/398):
    a fixture recorded under a binding document, whose preparation names the bound dialect's digest.
    Until then the form is defined and not claimable, and how an Exchange entry carries its
    fixtures' binding documents is the Exchange's to fix.
    *Resolved 2026-10-15:* the Runner reads version 3 and binds a dialect at import since its pull
    request 83 (`v0.12.0`), and its vector `unbound-bound-at-import`, recorded under a binding
    document, is staged (the amendment that read version 3). The form is not claimable until a
    specification version publishes the vectors (§14); the Desk's side and how an Exchange entry
    carries its fixtures' binding documents stay open.
12. **The requests of other `http`-shaped sources.** A first draft of the amendment held a request
    of shape `http` to `{method, path, query}`, the form the tenth vector carries. That refused
    `adapter-http`'s `body`, which the Runner admits, and the requests of the gateway's Databricks
    and Azure DevOps connections, which record shape `http` for requests of their own form, naming
    a connection and a read, and which the Exchange's seed entries read.
    *Resolved 2026-10-15, by the maintainer's decision on the pull request that makes the
    amendment:* for a source of shape `http` or `airbyte`, the request is the one the gateway source
    of that shape takes, as its adapter or connection defines it, and the text holds it to being an
    object, to the template rules and to the receipt's commitment, and not to a set of members
    (§4.1); `adapter-http`'s `query`, when present, stays held to string templates.
13. **The published identity in the committed form.** A preparation commits the bound dialect, its
    profile assignments included, and neither the binding document's digest, nor the published
    dialect's digest, nor the catalog names the binding removes (§4.4): a record that binds it
    cannot name the published dialect or its binding, and two published dialects that differ only
    in their catalog names, bound to the same profiles, prepare under one bound digest. Whether the
    published dialect's and the binding document's digests should be carried in the committed form,
    so that a record names the published identity, as the Exchange may want, is open; carrying them
    would change the preparation's form, and so its version.
14. **A research fixture.** Whether verification must reproduce a model's answer is resolved
    by the maintainer's decision of 2026-10-15, filed as issue
    [#161](https://github.com/Judgment-Pack/judgment-pack-spec/issues/161): the acquisition is the
    caller-assembled research record `R`, whose retained responses are checked under their own
    trusted profiles, over their own requests and results, before the read applies to `R`
    (§4.3, §5.2, §11). The recipe is recorded in the dialect and under its digest, never
    re-executed. No model output is produced or compared. The fixture layout is fixed in §11,
    including the staging manifest's expected answer. The `research` kind's first fixture still
    waits on a preparer; no vector holds it, and it remains defined and not claimable. Issue #171
    adds the GTM company/person and work-item triage fixture lists, including typed results,
    bindings, fallback and selected parent/child records, with none recorded (§11).
15. **Binding a published research recipe.** Which installation profiles can serve its named
    model and its AI and web capabilities, without publishing local identifiers, was left open
    by §4.3 and by issue #160's decision on the workflow prerequisite.
    *Resolved 2026-10-15, by decision 2 of issue #171:* §§4.4 and 5.1 extend the unbound form to
    research. The source declares `model` and `capabilities`; a binding document assigns its AI
    and web profiles by id and digest, all of class `generated`. An incompatible profile gives
    `profile-mismatch`. The preparation commits the bound dialect alone; replay checks retained
    bytes under those profiles and never establishes answer correctness. The result contract
    and reconciliation are decisions 1 and 3; the still-unrecorded fixtures are decision 4.
    Workflow version 1 (RFC 0020 §4) admits no stage whose dialect has a research source.
    RFC 0020 §4's sentences that only `operation` has an unbound form and that portable research
    binding is deferred, and its question 2, are superseded pending its own revision. The
    coordinator is to file that revision as an issue. Its operation demonstration remains due,
    and its version is not changed here.
16. **Reconciliation's limits.** Partners are research sources only: an `operation` cannot be a
    fallback partner. The reconciler is always acquired, even when an earlier source found the
    value; if the reconciler is skipped, its target is unwritten. Independent per-field fallback
    does not scale beyond a few fields within the 64-clause and 16-source bounds. Whether to
    admit other source kinds, conditional acquisition or a form that scales to more fields is
    open.

**Next revision.** The maintainer's decision of 2026-10-14 on issue #141 scoped dialect version 3
in three parts. The first two are specified by the amendment of 2026-10-15 (above): the record kind
over every gateway source shape, which the maintainer placed in version 2 once the Runner had made
it there ([Judgment-Pack/judgment-pack-runner#79](https://github.com/Judgment-Pack/judgment-pack-runner/issues/79));
and the unbound source form, bound at import, in version 3, the Desk's side being
[Judgment-Pack/judgment-pack-desk#398](https://github.com/Judgment-Pack/judgment-pack-desk/issues/398).
The third, two documents per `both` entry, is the Exchange's entry format,
[Judgment-Pack/judgment-pack-exchange#2](https://github.com/Judgment-Pack/judgment-pack-exchange/issues/2),
and changes nothing in this document.

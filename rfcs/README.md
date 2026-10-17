# Proposals (RFCs)

This directory holds Requests for Comments (RFCs) — design records for material changes to the
Judgment Pack Specification. An RFC is a proposal opened for public comment, in the sense used by
projects such as Rust and React. **An RFC is not part of the specification.** Nothing here is
normative, and no conformance class depends on any of it.

An accepted RFC is the exception, and only in one direction: the design record stays here and stays
non-normative, while the governing text — text the proposal produced, or, for a retrospective
record, text that preceded it — lives where the record says it lands: for a
standards-track RFC, the specification; for a cross-project exploratory record, the repository that
owns the artifact (see the closing note below). [RFC 0006](0006-evaluator-conformance.md)
is accepted and landed in Core `0.2.0-draft`; the normative statement of the evaluator conformance
class is [§3.4 of the Core specification](../spec/judgment-pack-core.md), not this directory.
[RFC 0017](0017-checkpoint-witness-statement.md) is accepted and its text landed in the same
merge, beside Core rather than in it: the normative statement of the checkpoint witness statement is
the companion document [`spec/checkpoint-witness.md`](../spec/checkpoint-witness.md), not this
directory. Its vectors are staged, as RFC 0013's rows are, until a later `specVersion` opens.
[RFC 0018](0018-dialect.md) is accepted in the same form: the normative statement of the dialect and
its preparation verifier is the companion document [`spec/dialect.md`](../spec/dialect.md), not this
directory, and its forty-seven vectors are staged until a later `specVersion` opens; it was amended
in place on 2026-10-15 and 2026-10-16, its status unchanged.
[RFC 0014](0014-lineage-record-and-action-binding.md) is the first accepted cross-project record,
and a retrospective one: the gateway's `SPEC.md` and the runtime's decision records govern what it
describes, and they did so before it was written.

Acceptance and incorporation are different events. [RFC 0000](0000-rfc-process.md) makes acceptance
the approval of a design at the maturity the RFC names; RFC 0006's text landed in the same merge,
which is a precedent and not a rule. [RFC 0013](0013-evaluator-error-and-precedence-cases.md) is
accepted and awaits incorporation: its rows are staged for the `suiteVersion` after `0.2.0-draft`,
are in no released corpus, and land when a later `specVersion` opens.

The purpose of this directory is to make the project's open design questions *visible* rather than
to imply they are settled. Concepts that are frequently assumed to be part of Judgment Pack — a
graph that composes packs, a planner that selects them, an evidence-integration layer, a discovery
registry — are design questions, not shipped features. They live here as drafts until they are
prototyped and shown to interoperate across independent implementations, or until one is
dispositioned: the planner's record, [RFC 0004](0004-planner-interface.md), is rejected as product
behavior and stays here as the record of why.

## Process

See [RFC 0000 — Request for Comments process](0000-rfc-process.md) for required sections, statuses,
and the evidence bar. Material or normative changes require an RFC and a public review period; a
stable feature requires two independent implementations and conformance cases.

## Index

| RFC | Title | Status | Belongs to |
| --- | --- | --- | --- |
| [0000](0000-rfc-process.md) | Request for Comments process | Active | Process |
| [0001](0001-pack-manifest.md) | Pack manifest | Draft | Specification (format) |
| [0002](0002-judgment-graph.md) | Judgment Graph composition | Draft | Specification (format) — scoped to the dataflow seam: one decision's outcome as another's input |
| [0003](0003-evidence-reference.md) | Evidence reference | Draft | Specification (format) |
| [0004](0004-planner-interface.md) | Planner interface | Rejected | Product — the specification standardizes no part of a planner |
| [0005](0005-pack-discovery.md) | Pack discovery | Draft | Specification (format) + product (service) |
| [0006](0006-evaluator-conformance.md) | Evaluator conformance | Accepted | Specification (Core `0.2.0-draft`: semantics + conformance class) |
| [0007](0007-determination-boundary.md) | The determination boundary — what a pack cannot hold | Draft | Specification (Core or profile) — undecided |
| [0008](0008-bounded-collection-quantifiers.md) | Bounded collection quantifiers for conditions | Draft | Specification (condition schema + semantics) — Core or profile undecided |
| [0009](0009-interim-review-regime.md) | The interim review regime | Accepted | Process (governance) |
| [0010](0010-gateway-signing-identity.md) | The gateway signing identity — custody, rotation, and anchoring | Draft | Research line (gateway repository: code, `SPEC.md`, guidance, corpus) — outside the specification |
| [0011](0011-judgment-currency-anchor.md) | A currency anchor for pack versions — detecting stale and retired policy | Draft | Research line (cross-project artifact: a runtime currency registry + verifier, consumer protocols) — outside the specification |
| [0012](0012-witness-contract.md) | What a witness contract would have to specify — candidate clauses for a signed-history comparison | Draft | Research line (cross-project artifact: a witness format + verifier, consumer protocols) — outside the specification |
| [0013](0013-evaluator-error-and-precedence-cases.md) | The first evaluation-suite rows that use `expectedErrorClass`, including two where several §8.4 classes apply and the order decides | Accepted | Specification-track (evaluation conformance suite) — rows staged for the `suiteVersion` after `0.2.0-draft`, in no released corpus |
| [0014](0014-lineage-record-and-action-binding.md) | The lineage record and the action binding — how a decision cites what it read, and an action cites what it decided | Accepted | Research line (cross-project artifact: gateway receipt version 3 + verifier join, runtime record and row citations; outside the specification) — a retrospective record; acceptance endorses the record only |
| [0015](0015-reported-receipts.md) | What a reported receipt would have to specify — the engine signing a call it did not make | Draft | Research line (cross-project artifact: gateway receipt format, verifier and surface; a reporting plugin in an MCP gateway; outside the specification) |
| [0016](0016-outcome-values.md) | Outcome values — a decision that states a quantity | Draft | Specification (a specification-defined extension, or Core — undecided) |
| [0017](0017-checkpoint-witness-statement.md) | The checkpoint witness statement | Accepted | Specification (a companion document beside Core, [`spec/checkpoint-witness.md`](../spec/checkpoint-witness.md), with a reader conformance class; its 54 vectors, the reference gateway's bytes, are staged for the next `specVersion`, in no corpus) |
| [0018] | The dialect | Accepted | Specification (a companion document; see below) |
| [0019] | The Judgment Exchange — a shared place for dialects | Draft | Research line (see below) |
| [0020] | The workflow | Draft | Specification (a proposed companion document; see below) |

[0018]: 0018-dialect.md
[0019]: 0019-exchange.md
[0020]: 0020-workflow.md

RFC 0018 states how a pack's facts and evidence are obtained and derived, and what a preparation
establishes per part. Its companion, [`spec/dialect.md`](../spec/dialect.md), defines the
preparation-verifier class; the reference Runner's 47 preparation vectors are staged for the next
`specVersion`, in no corpus. It was amended on 2026-10-15 for every gateway source shape in version
2, the unbound source form in version 3 and version 3 as the reference Runner reads it; on
2026-10-16 for the name an unbound operation's record carries, the research vectors staged and the
skipped source's form.

RFC 0019 is a cross-project record outside the specification: a catalog's entry format,
manifest, tests and contribution rules, and a desk's browse. Amended 2026-10-15 for
[issue #166](https://github.com/Judgment-Pack/judgment-pack-spec/issues/166) and
[issue #172](https://github.com/Judgment-Pack/judgment-pack-spec/issues/172): entry version 2
distinguishes kind `dialect` from pack-free kind `preset`; the seven enforcement
sentences are settled. Amended 2026-10-16 for
[issue #192](https://github.com/Judgment-Pack/judgment-pack-spec/issues/192), option A: entry
version 3 checks named-format references and artifact identities under RFC 0021, with immutable
pairs across catalog history and unchanged manifest rows. Catalog CI fetches tags and reads every
previous release's manifest and pinned entries as blobs, refusing unreadable history as
`artifact-history-invalid`, with no form-only fallback. Only a consumer checks form alone when
it does not hold the previous manifest, reporting `artifact-history-unchecked`. Identical content
under a pair is admitted in another entry under its kind's rules; presets stay integer-only.
The catalog's checker and fixtures follow in their own pull request on `judgment-pack-exchange`.
RFC 0019 stays a Draft; a hosted registry remains out of scope (Unresolved question 4).

RFC 0020 proposes `spec/workflow.md` beside Core, with a reader class and fixtures from a
two-stage run, none recorded yet.

The "Belongs to" column records where each proposal would land if accepted. A format that
independent tools must agree on is a candidate for the specification. An algorithm or engine belongs
to a runtime. A hosted service belongs to a product. Several of these proposals split across that
boundary, and saying so early is part of the design. A record whose every part lands in another
repository of the project is a cross-project exploratory record (see
[RFC 0000](0000-rfc-process.md)): acceptance endorses the record, and adoption stays with that
repository.

RFC 0021 adds [named Dialect artifact identities](0021-dialect-artifact-identity.md) through
exact `formatVersion` selectors, with unchanged historical formats and separate binding digests.

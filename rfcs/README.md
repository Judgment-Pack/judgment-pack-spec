# Proposals (RFCs)

This directory holds Requests for Comments (RFCs) — design records for material changes to the
Judgment Pack Specification. An RFC is a proposal opened for public comment, in the sense used by
projects such as Rust and React. **An RFC is not part of the specification.** Nothing here is
normative, and no conformance class depends on any of it.

An accepted RFC is the exception, and only in one direction: the design record stays here and stays
non-normative, while the text it produced lives where the proposal declared it would land — for a
standards-track RFC, the specification; for a cross-project exploratory record, the repository that
owns the artifact (see the closing note below). [RFC 0006](0006-evaluator-conformance.md)
is accepted and landed in Core `0.2.0-draft`; the normative statement of the evaluator conformance
class is [§3.4 of the Core specification](../spec/judgment-pack-core.md), not this directory.

The purpose of this directory is to make the project's open design questions *visible* rather than
to imply they are settled. Concepts that are frequently assumed to be part of Judgment Pack — a
graph that composes packs, a planner that selects them, an evidence-integration layer, a discovery
registry — are design questions, not shipped features. They live here as drafts until they are
prototyped and shown to interoperate across independent implementations.

## Process

See [RFC 0000 — Request for Comments process](0000-rfc-process.md) for required sections, statuses,
and the evidence bar. Material or normative changes require an RFC and a public review period; a
stable feature requires two independent implementations and conformance cases.

## Index

| RFC | Title | Status | Belongs to |
| --- | --- | --- | --- |
| [0000](0000-rfc-process.md) | Request for Comments process | Active | Process |
| [0001](0001-pack-manifest.md) | Pack manifest | Draft | Specification (format) |
| [0002](0002-judgment-graph.md) | Judgment Graph composition | Draft | Specification (format) |
| [0003](0003-evidence-reference.md) | Evidence reference | Draft | Specification (format) |
| [0004](0004-planner-interface.md) | Planner interface | Draft | Likely product |
| [0005](0005-pack-discovery.md) | Pack discovery | Draft | Specification (format) + product (service) |
| [0006](0006-evaluator-conformance.md) | Evaluator conformance | Accepted | Specification (Core `0.2.0-draft`: semantics + conformance class) |
| [0007](0007-determination-boundary.md) | The determination boundary — what a pack cannot hold | Draft | Specification (Core or profile) — undecided |
| [0008](0008-bounded-collection-quantifiers.md) | Bounded collection quantifiers for conditions | Draft | Specification (condition schema + semantics) — Core or profile undecided |
| [0009](0009-interim-review-regime.md) | The interim review regime | Accepted | Process (governance) |
| [0010](0010-gateway-signing-identity.md) | The gateway signing identity — custody, rotation, and anchoring | Draft | Research line (gateway repository: code, `SPEC.md`, guidance, corpus) — outside the specification |

The "Belongs to" column records where each proposal would land if accepted. A format that
independent tools must agree on is a candidate for the specification. An algorithm or engine belongs
to a runtime. A hosted service belongs to a product. Several of these proposals split across that
boundary, and saying so early is part of the design. A record whose every part lands in another
repository of the project is a cross-project exploratory record (see
[RFC 0000](0000-rfc-process.md)): acceptance endorses the record, and adoption stays with that
repository.

# Proposals (RFCs)

This directory holds Requests for Comments (RFCs) — design records for material changes to the
Judgment Pack Specification. An RFC is a proposal opened for public comment, in the sense used by
projects such as Rust and React. **An RFC is not part of the specification.** Nothing here is
normative, and no conformance class depends on any of it.

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

The "Belongs to" column records where each proposal would land if accepted. A format that
independent tools must agree on is a candidate for the specification. An algorithm or engine belongs
to a runtime. A hosted service belongs to a product. Several of these proposals split across that
boundary, and saying so early is part of the design.

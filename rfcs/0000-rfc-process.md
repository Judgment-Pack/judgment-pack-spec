# RFC 0000: Request for Comments process

- Status: Active
- Type: Process
- Created: 2026-07-22

## Summary

A Request for Comments (RFC) is the design record for a material change to the Judgment Pack
Specification, its profiles, conformance model, or governance. "RFC" is used here in the sense
adopted by projects such as Rust and React — a proposal opened for public comment and deliberate
disposition — not the IETF sense of an already-published standard.

This process replaces the earlier Judgment Enhancement Proposal (JEP) process; the required
sections and evidence bar are unchanged.

## Required sections

Every standards-track RFC should contain:

1. **Summary** — the proposed change in plain language.
2. **Problem** — the interoperability problem and affected users.
3. **Evidence** — real examples and known implementation experience.
4. **Specification** — exact proposed portable semantics.
5. **Alternatives** — including no change, extension, profile, and product-only behavior.
6. **Compatibility** — reader, writer, semantic, and migration effects.
7. **Security and privacy** — abuse, confusion, disclosure, and resource risks.
8. **Conformance** — positive, negative, boundary, and adversarial cases.
9. **Implementation** — at least two plausible independent implementations.
10. **Unresolved questions** — issues that must not be hidden by acceptance.

## Statuses

- `Draft`
- `Review`
- `Accepted`
- `Rejected`
- `Withdrawn`
- `Superseded`

Acceptance means the design is approved for the maturity named by the RFC. It does not automatically
make a feature stable.

## Review

Research-preview RFCs remain open for public comment for a reasonable period based on complexity.
Maintainers may request prototypes or conformance cases before disposition. A stable normative
feature should not be accepted without evidence from two independent implementations.

## Compatibility

During `0.x`, breaking proposals are allowed but must be labeled and accompanied by migration
guidance. After a stable release, its compatibility policy takes precedence over this draft process.

## Seeded proposals

The following early-stage RFCs are published as `Draft` to make current design questions visible
rather than settled. They are not part of the specification.

- [RFC 0001 — Pack manifest](0001-pack-manifest.md)
- [RFC 0002 — Judgment Graph composition](0002-judgment-graph.md)
- [RFC 0003 — Evidence reference](0003-evidence-reference.md)
- [RFC 0004 — Planner interface](0004-planner-interface.md)
- [RFC 0005 — Pack discovery](0005-pack-discovery.md)

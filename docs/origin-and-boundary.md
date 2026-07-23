# Origin and public boundary

The Judgment Pack Specification originated in architecture research conducted by Protoss AI into
portable organizational judgment, evidence lineage, deterministic validation, and governed AI
decision systems.

This repository is not a mirror of the Protoss product source tree. It intentionally extracts only
a reduced, vendor-neutral research surface.

The following remain outside this repository:

- Protoss product applications and infrastructure;
- customer data, packs, evidence, and outcomes;
- the Protoss Pack Factory and knowledge-discovery workflow;
- production runtime, compiler optimization, calibration, and learning systems;
- proprietary evaluation corpora and security test material;
- internal architecture proofs that have not demonstrated external implementability.

Public proposals must be evaluated on their interoperability value. A concept does not belong in
the specification merely because Protoss AI or a Protoss product uses it internally.

Protoss AI maintains the separate public `protoss-cli` project as one nonnormative implementation
of JPS document-conformance tooling. It consumes and is tested against the same public conformance
artifacts available to independent implementations. Protoss AI may also provide commercial
implementations of JPS; those implementations are not normative.

## Naming and authority

- **Judgment Pack Specification (JPS)** names the vendor-neutral specification and its public
  artifact set.
- **Protoss AI** names the current steward and the organization where the research originated.
- **Protoss CLI** names one separately maintained developer tool.

These names do not make a tool normative, designate a reference implementation, confer
certification, or change the authority of tagged JPS prose and schemas.

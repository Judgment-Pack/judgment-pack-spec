# Origin and scope

The Judgment Pack Specification (JPS) originated in practical work on making organizational
judgment portable and testable: representing the evidence, rules, exceptions, uncertainty,
escalation criteria, and evaluations behind a decision in a form that can be inspected and checked
independently of the system that produced it.

The specification is maintained in public as a vendor-neutral proposal. It is developed in the open
— today by a single maintainer, with no independent contributors yet (see
[GOVERNANCE.md](../GOVERNANCE.md#interim-review-regime)) — and is independent of any single product
or company.
No required commercial runtime controls it, and no implementation is designated normative by virtue
of its origin.

JPS defines document conformance and, as of `0.2.0-draft`, what an evaluation of a pack means for an
implementation claiming the evaluator conformance class (Core §3.4) — never how any engine is built. It
specifies what a conforming Judgment Pack document must contain, how such documents are validated
against tagged prose and schemas, and which single portable result an evaluation produces. It does not
specify how any given engine, service, or tool is built.

## What the specification is

- The normative prose and its normative references;
- versioned JSON Schemas and immutable schema identifiers;
- carrier, structural, and semantic conformance cases and their manifests;
- the evaluation corpus and its case carrier, normative for the evaluator conformance class of Core
  §3.4 and for nothing else;
- synthetic examples, testing guidance, release notes, and compatibility statements.

These artifacts are published as immutable, versioned releases. Any conforming implementation,
open-source or proprietary, consumes those releases like any other implementation, and is tested
against the same public conformance artifacts available to every other implementation.

## What the specification is not

The specification is not a mirror of any product source tree, and it does not incorporate a concept
merely because some system uses it internally. Public proposals are evaluated on their
interoperability value. The following remain outside the specification and its repository:

- product applications, services, and infrastructure;
- customer data, packs, evidence, and outcomes;
- production runtime, calibration, and learning systems;
- proprietary evaluation corpora and security test material;
- internal architecture that has not demonstrated external implementability.

## Naming and authority

**Judgment Pack Specification (JPS)** names the vendor-neutral specification and its public artifact
set. Implementations are named and maintained separately from the specification.

Naming an implementation does not make it normative, designate a reference implementation, confer
certification, or change the authority of tagged JPS prose and schemas. Conforming implementations
may be open-source or proprietary; passing an implementation's checks establishes only what that
implementation reports, never the authority of the specification itself.

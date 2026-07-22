# Conformance corpus

This directory contains 47 focused research-preview cases for testing the carrier, structural, and
semantic requirements of Judgment Pack Core `0.1.0-draft`. It is versioned with the draft but is not
yet a complete or normative conformance suite. Evaluator behavior is intentionally out of scope.

[`manifest.json`](manifest.json) is the machine-readable case index. Its shape is defined by
[`manifest.schema.json`](manifest.schema.json).

## Layers

- `carrier/` contains inputs that must be rejected before schema validation. Some files are
  deliberately malformed JSON, and duplicate-member cases must be parsed with duplicate detection.
- `structural/` contains well-formed JSON documents that fail the normative JSON Schema. JPS testing
  asserts the schema's `uri`, `date`, and `date-time` formats even though some general-purpose JSON
  Schema libraries treat `format` as annotation-only by default.
- `semantic/` contains documents that pass structural validation but fail a prose requirement, or
  cannot be fully interpreted with the case's declared consumer capabilities.
- `valid/` contains documents expected to pass carrier, structural, and semantic checks. A valid
  result does not claim factual truth, authority, evaluator conformance, or operational fitness.

Validation proceeds in layer order. A runner should stop a case at its target layer rather than
reporting downstream diagnostics for content that failed an earlier layer.

## Manifest expectations

Each case records:

- `layer` — the highest layer exercised by the case;
- `expectedResult` — `valid`, `invalid`, or `unsupported`;
- `expectedDiagnostic` — the primary provisional diagnostic code and JSON Pointer, or `null` for a
  valid case;
- `specSection` — the draft section that motivates the expectation; and
- optional `supportedExtensions` — the required-extension capabilities available to the consumer
  for that case. When omitted, the capability set is empty.

`unsupported` is distinct from `invalid`: the document is structurally readable and semantically
well-formed, but the consumer lacks a capability named by `metadata.requiredExtensions`.

Diagnostic codes in this corpus are test metadata, not yet a normative cross-implementation
diagnostic contract. The recorded diagnostic is the primary expected result; implementations may
also report additional detail. A pointer to a missing member identifies the location the member
would have occupied.

## Semantic checks represented here

The semantic cases exercise collection-local identifier uniqueness; declared outcome, evidence,
source, and exception-target references; reference-kind checking; recursive traversal of every
condition position for `evidence-present`; required-extension declaration consistency; and
required-extension capability negotiation.

Reference traversal must inspect every condition position, including root applicability, rule
conditions, exception conditions, and arbitrarily nested `all`, `any`, and `not` nodes. The focused
recursive fixture demonstrates the traversal requirement without defining an implementation
algorithm.

## Current boundary

This corpus does not yet test condition evaluation, resolution results, resource limits,
canonicalization, signatures, imports, or migration behavior. Future expansion should remain
focused: one primary expectation per negative fixture, with positive, boundary, and adversarial
counterparts added when the corresponding semantics become normative.

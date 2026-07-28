# Design principles

The Judgment Pack Specification is governed by the following design constraints.

## Representation before execution

A pack may represent valid organizational knowledge even when a particular runtime cannot execute
all of it. Runtimes must disclose unsupported capabilities rather than silently reinterpret content.

## Conformance is not truth

Validation demonstrates agreement with a contract. It does not establish that a source is accurate,
an interpretation is faithful, or a decision is appropriate.

## Evidence is not authority

Evidence supports claims. Authority permits actions. The two must not be inferred from each other.

## Unknown is a first-class result

Missing, conflicting, or inapplicable information must not silently become `false`, zero, or an
empty value. Portable decision rules declare what happens when their conditions cannot be resolved.

## No hidden executable semantics

Normative behavior cannot depend on prose prompts, host-language functions, network calls, model
outputs, environment variables, or vendor extensions that are not declared as required capabilities.

## A small stable core

The core should standardize only concepts required for exchange. Industry vocabularies, runtime
targets, signatures, and enterprise governance should evolve as profiles.

Evaluation is the recorded exception, and the reason belongs with the principle.
[RFC 0006](../rfcs/0006-evaluator-conformance.md) asked whether the evaluator conformance class
belonged in Core or in a profile and was answered on acceptance as **Core**: the evaluation semantics
and the disposition live in Core §§3.4 and 7–8 so that
[RFC 0008](../rfcs/0008-bounded-collection-quantifiers.md) and any future evaluation profile share one
error contract and one result shape rather than each restating them. An evaluation *method* — a scoring
regime, a calibration procedure, a test harness — still belongs in a profile or a product, and the
engine that performs an evaluation still belongs to a runtime.

## Independent implementation

The prose specification, schemas, and conformance cases—not any single vendor's codebase—define portable
behavior. A stable feature should have at least two independent implementations.

## Honest partial support

Tools may support subsets during the research phase, but they must report their capability set and
must not claim full conformance.

## Safe extensibility

Extensions are namespaced and preserved. An implementation that does not understand an optional
extension ignores its semantics without deleting it. Required extension semantics must be declared
explicitly and prevent unsupported consumers from claiming full interpretation.

## Portability over convenience

The normative carrier is JSON. Human-friendly authoring syntaxes may be added only when their
conversion to the normative model is explicit and lossless.

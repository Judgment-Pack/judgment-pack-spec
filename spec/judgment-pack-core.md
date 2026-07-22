# Judgment Pack Core `0.1.0-draft`

## Status

This document is a research preview. It may change incompatibly and MUST NOT be represented as an
industry standard or as suitable, by conformance alone, for consequential decisions.

The normative scope of `0.1.0-draft` is limited to carrier, structural, and semantic document
conformance. Sections 7 and 8 are informative experiments. This draft defines no evaluator
conformance class and no portable decision result.

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be
interpreted as described by BCP 14 when, and only when, they appear in all capitals. Normative
references are listed in §12.

## 1. Purpose

Judgment Pack Core defines a portable JSON document for representing:

- a decision intent and question;
- possible outcomes;
- evidence requirements;
- sources and claim-level citations;
- applicability conditions;
- rules and typed exceptions;
- explicit behavior for unknown information;
- escalation requirements; and
- basic authorship and review metadata.

The core defines representation and document conformance. It does not establish truth, authority,
safety, fitness for a deployment, or portable evaluation behavior.

### 1.1 Normative artifacts and precedence

The artifacts in this repository have distinct roles:

- this document is the normative prose for carrier and semantic document conformance and for the
  interpretation of schema-defined fields;
- [`schema/judgment-pack-core.schema.json`](../schema/judgment-pack-core.schema.json) is the
  normative machine-readable projection of structural document constraints; and
- examples, conformance cases, READMEs, design notes, the roadmap, and implementation behavior are
  informative unless a later specification explicitly gives an artifact normative status.

A conformance claim MUST satisfy all applicable normative requirements. If the schema and this
document disagree, this document controls and the mismatch is a specification defect that SHOULD
be reported. An example, test fixture, validator, or product behavior cannot override either
normative artifact.

## 2. Normative representation

### 2.1 JSON carrier

The normative carrier is a JSON text as defined by RFC 8259. In addition:

- object member names MUST be unique; and
- implementations MUST reject malformed or incomplete input and data exceeding their documented
  resource limits rather than process only a silent prefix.

Root type, recognized members, and field-value constraints belong to structural or semantic
document conformance rather than carrier conformance.

### 2.2 Decimal grammar

JSON numbers SHOULD NOT be used for business quantities whose exact decimal identity matters. The
comparison operand of a `fact` condition using `greater-than`, `greater-than-or-equal`, `less-than`,
or `less-than-or-equal` MUST be a string matching:

```text
decimal = [ "-" ] ( "0" / non-zero-digit *DIGIT ) [ "." 1*DIGIT ]
```

Exponent notation, leading plus signs, leading zeroes, `NaN`, and infinities are not admitted.
This grammar does not classify every numeric-looking string as a decimal and does not apply to
identifiers, versions, paths, locators, citations, equality operands, or other textual values merely
because they contain digits. Core `0.1.0-draft` has no general decimal type marker; exact decimal
quantities outside ordered fact-condition operands require a future profile or declared extension.

This draft defines decimal lexical syntax only. It has no decimal type marker and does not define
decimal equality, ordering, scale, units, or cross-unit conversion. Satisfying this grammar
therefore does not imply executable comparison support.

## 3. Conformance classes

This draft defines three document conformance classes. It does not define execution conformance.

### 3.1 Carrier-conforming document

A serialized document is carrier conforming when it satisfies §2.1, including valid and complete
RFC 8259 JSON, unique object member names, and explicit failure rather than silent partial
processing when a documented resource limit is exceeded.

### 3.2 Structurally conforming document

A carrier-conforming document is structurally conforming when it satisfies the normative JSON
Schema and all schema-adjacent requirements in this document.

The `format` keywords in the schema are assertions for JPS conformance, regardless of whether a
JSON Schema implementation treats `format` as annotation by default. A structural validator MUST
enable the Draft 2020-12 Format-Assertion vocabulary or perform equivalent checks. In particular:

- `id` MUST be an absolute URI conforming to RFC 3986;
- `source.publishedAt` MUST be an RFC 3339 `full-date`; and
- `metadata.createdAt` and every `metadata.reviews[].reviewedAt` value MUST be an RFC 3339
  `date-time`.

Accepting these fields without asserting their formats is insufficient for structural conformance.

### 3.3 Semantically conforming document

A structurally conforming document is semantically conforming when:

- every local reference resolves exactly once;
- referenced object kinds are correct;
- outcome, rule, evidence-requirement, source, and exception identifiers are unique within their
  collections;
- every rule outcome and fallback outcome names a declared outcome;
- every rule evidence reference names a declared evidence requirement;
- every rule source reference names a declared source;
- every `evidence-present` condition names a declared evidence requirement;
- every exception target names a declared rule when a target is present;
- every exception outcome names a declared outcome when an outcome is present;
- every exception source reference names a declared source;
- required extension capabilities are declared;
- field meanings and cross-field constraints follow the normative prose in §§4–6 and §9.

Condition or resolution results are not part of semantic document conformance.

### 3.4 Evaluator conformance

Evaluator conformance is reserved for a later draft. A tool MUST NOT claim evaluator conformance
under `0.1.0-draft`, even if it implements the experiments in §§7–8.

### 3.5 Non-claims

Conformance MUST NOT be described as proof that:

- a claim is true;
- evidence is authentic or sufficient;
- an author or reviewer had authority;
- an outcome is legally or ethically permissible;
- a particular runtime applied the pack correctly; or
- use of the pack is safe.

## 4. Root object

| Member                 | Required | Meaning                                                 |
| ---------------------- | -------: | ------------------------------------------------------- |
| `specVersion`          |      yes | Exact value `0.1.0-draft`                               |
| `id`                   |      yes | Stable absolute URI identifying the pack series         |
| `version`              |      yes | Three-component `MAJOR.MINOR.PATCH` revision string     |
| `title`                |      yes | Non-empty human-readable title                          |
| `description`          |       no | Human-readable overview                                 |
| `decision`             |      yes | Decision intent and question                            |
| `applicability`        |       no | Optional condition delimiting the pack's scope          |
| `evidenceRequirements` |       no | Declared inputs or proof obligations                    |
| `sources`              |       no | Located source material                                 |
| `outcomes`             |      yes | At least two possible outcomes                          |
| `rules`                |      yes | One or more rules                                       |
| `exceptions`           |       no | Typed exceptions to rules or normal resolution          |
| `fallbackOutcome`      |       no | Candidate outcome when normal rules yield no candidate  |
| `escalation`           |       no | Optional handoff configuration, not a decision outcome  |
| `metadata`             |       no | Authorship, license, creation, and review information   |
| `extensions`           |       no | Namespaced extension values                             |

Collection order is preserved for authoring and display but MUST NOT determine rule priority.

The root MUST be an object. The schema defines the recognized members of each Core object; a member
not defined for that Core object MUST NOT appear. The names and arbitrary JSON values inside an
`extensions` object are governed separately by §9.

## 5. Identity and references

The pack `id` MUST be an absolute URI. Local object identifiers are non-empty ASCII strings matching
`^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`.

Local identifiers are scoped to the pack version. They MUST NOT be interpreted as globally unique.
Meaning MUST NOT be inferred from the spelling of an identifier.

Core `0.1.0-draft` has no imports or remote-reference resolution. All rule, outcome, source,
evidence-requirement, and exception references resolve within one document.

## 6. Core objects

### 6.1 Decision

`decision.intent` explains the organizational purpose. `decision.question` states the question the
pack is intended to resolve. Both are required human-readable strings.

The decision object MAY include namespaced extensions. It MUST NOT embed prompts or executable
host-language code.

### 6.2 Evidence requirement

An evidence requirement declares:

- `id` — local identity;
- `description` — what must be provided;
- `required` — whether absence prevents normal resolution; and
- optional `kind` — `document`, `fact`, `measurement`, or `attestation`.

The kind is descriptive in this draft. Products may acquire or authenticate evidence differently.

### 6.3 Source

A source contains:

- `id` and `title`;
- a typed `locator` with `kind` and `value`;
- optional publisher and publication date;
- optional `citation` containing a location and excerpt; and
- optional rights information.

A source record represents provenance supplied by the author. Core conformance does not verify that
the source exists, that the excerpt is accurate, or that its license permits a proposed use.

### 6.4 Outcome

An outcome has a local `id`, human-readable `label`, and optional `description`.

An outcome is a declared result, not an authorization to perform an external action. Execution of
an outcome is outside Core.

### 6.5 Rule

A rule declares:

- `id` and `description`;
- `when`, a condition;
- `outcome`, a declared outcome id;
- `onUnknown`, either `ignore` or `escalate`;
- optional evidence-requirement references;
- optional source references; and
- optional rationale.

The representation has no rule-priority field, and array order carries no priority meaning.
Informative handling of conflicts and `onUnknown` appears in §8.

### 6.6 Exception

An exception declares a condition and one effect:

- `suppress-rule`, with `targetRule`;
- `force-outcome`, with `outcome`; or
- `escalate`.

For `suppress-rule`, `targetRule` is required and `outcome` is absent. For `force-outcome`, `outcome`
is required and `targetRule` is absent. For `escalate`, both are absent. Every exception also has a
required `onUnknown` policy of `ignore` or `escalate`. Informative evaluation order and effect
compatibility appear in §8.

### 6.7 Escalation

An escalation object describes configured handoff intent. `triggers` is a non-empty set chosen
from:

- `not-applicable`;
- `missing-required-evidence`;
- `unknown`;
- `conflict`; and
- `no-match`.

The target identifies a human role, queue, or external system by a display name. The object
configures handoff intent; it does not itself make a pack applicable, turn a condition into an
outcome, or prove that a handoff occurred. When the object is omitted, Core supplies no default
triggers or target. Core does not define delivery, identity resolution, authorization, or
service-level objectives.

### 6.8 Metadata

Metadata MAY carry authors, creation time, license expression, and review records. These are
author assertions. Signature and organizational-authority profiles may strengthen them later.

## 7. Experimental condition interpretation (informative)

This entire section is informative. It records a concrete experiment for design review and cannot
be used to claim evaluator conformance. The allowed JSON shapes for conditions remain normative
through the schema; the results described here do not.

In the experiment, a condition produces `true`, `false`, or `unknown`:

- `literal` returns its Boolean value;
- `all` uses strong three-valued conjunction;
- `any` uses strong three-valued disjunction;
- `not` negates while preserving `unknown`;
- `fact` compares a value selected from runtime-supplied facts; and
- `evidence-present` tests whether evidence was supplied for a named requirement.

### 7.1 `all`

- `false` if any child is false;
- `true` if every child is true;
- `unknown` otherwise.

### 7.2 `any`

- `true` if any child is true;
- `false` if every child is false;
- `unknown` otherwise.

### 7.3 `not`

`true` becomes `false`, `false` becomes `true`, and `unknown` remains `unknown`.

### 7.4 Fact conditions

A `fact.path` is interpreted as RFC 6901 JSON Pointer syntax against one runtime-supplied JSON facts
document. The empty string selects the document root. A syntactically valid pointer that does not
resolve, including an invalid array traversal at runtime, produces `unknown`.

The admitted operators are:

- `equals`;
- `not-equals`;
- `greater-than`;
- `greater-than-or-equal`;
- `less-than`;
- `less-than-or-equal`; and
- `in`.

For this experiment, `equals` uses type-preserving JSON equality: null equals null; Booleans and
strings compare by value; JSON numbers compare by their mathematical value without lossy
conversion; arrays compare recursively in order; and objects compare recursively by member name
and value without regard to member order. There is no coercion between JSON types. `not-equals` is
the Boolean inverse of `equals` when equality can be determined.

For `in`, the schema requires the condition value to be a non-empty array. The selected fact value
is compared for equality with each array item. A match produces `true`; no match produces `false`.

The schema requires operands of `greater-than`, `greater-than-or-equal`, `less-than`, and
`less-than-or-equal` to satisfy the decimal grammar in §2.2. This draft nevertheless assigns no
portable ordering to those decimal strings. Experimental evaluators may document local behavior,
but structural acceptance of an ordered condition does not imply executable support.

Missing paths, unsupported operators or operand shapes, incomparable values, and failed unit
interpretation produce `unknown` in the experiment.

### 7.5 Evidence presence

`evidence-present` is `true` when the runtime input explicitly associates at least one supplied
evidence item with the named requirement. It is `false` when a complete evidence manifest is
available and associates no item. It is `unknown` when the runtime cannot determine whether the
manifest is complete. This draft does not define an evidence-manifest interchange format.

## 8. Experimental resolution model (informative)

This entire section is informative. It makes the current design experiment unambiguous enough to
compare feedback, but implementing it does not establish evaluator conformance.

The experiment distinguishes three result kinds:

- an `outcome` result naming exactly one declared outcome;
- a `not-applicable` result carrying reason `not-applicable`, which is not an outcome; and
- an `unresolved` result carrying one or more reasons.

The generated reason vocabulary is `not-applicable`, `missing-required-evidence`, `unknown`,
`conflict`, and `no-match`, matching `escalation.triggers`. A true exception with effect `escalate`
adds the separate reason `exception-escalation`; that reason is a direct request rather than a
trigger-selected request. A result may retain multiple reasons. Reasons are a de-duplicated set;
their order carries no priority. Implementations may additionally record contributing rule,
exception, or evidence-requirement ids.

The experimental algorithm is:

1. Treat omitted `applicability` as the literal value `true`. If applicability is false, produce a
   terminal `not-applicable` result carrying reason `not-applicable` and do not evaluate exceptions
   or rules. If it is unknown, produce an `unresolved` result with reason `unknown` and stop.
2. Inspect every required evidence requirement. Record `missing-required-evidence` if any required
   evidence is absent, retaining the ids of all missing requirements for diagnostics.
3. Evaluate every exception condition and collect its effects. An unknown exception with
   `onUnknown: ignore` contributes no effect but remains unknown in a trace. An unknown exception
   with `onUnknown: escalate` records reason `unknown`.
4. Combine true exception effects as follows:

   - all `suppress-rule` effects are compatible and suppress the union of their target rules;
   - `force-outcome` effects are compatible when they all name the same outcome and conflict when
     they name different outcomes;
   - suppression is compatible with a forced outcome; and
   - one or more `escalate` effects are mutually compatible, record reason
     `exception-escalation`, and form a direct escalation request that takes precedence over
     suppression and forced outcomes.

5. Record reason `conflict` for incompatible forced outcomes. If required evidence is missing, an
   exception is unknown with `onUnknown: escalate`, exception effects conflict, or a true exception
   directly requests escalation, produce `unresolved` after all exception effects have been
   inspected. Retain every reason discovered at this stage. A direct exception escalation is also
   retained as such in diagnostics.
6. If one compatible forced outcome remains and no blocking state from step 5 exists, produce that
   outcome without evaluating normal rules. Otherwise, remove every suppressed rule and evaluate
   all remaining rules.
7. A true rule contributes its outcome as a candidate. A false rule contributes none. An unknown
   rule with `onUnknown: ignore` contributes no candidate and does not block resolution; an unknown
   rule with `onUnknown: escalate` records reason `unknown` and blocks both a candidate outcome and
   the fallback.
8. Record reason `conflict` when true rules name more than one distinct outcome. If both an
   escalate-on-unknown rule and conflicting true rules are present, retain both `unknown` and
   `conflict`; neither is discarded because the other also blocks resolution. Produce `unresolved`
   whenever either reason is present.
9. If no blocking reason exists and true rules name one distinct outcome, produce it. Multiple true
   rules naming that same outcome are compatible.
10. If no true rule contributes an outcome, use `fallbackOutcome` when present. False rules and
    unknown rules with `onUnknown: ignore` do not prevent this fallback. If no fallback is present,
    produce `unresolved` with reason `no-match`.

Thus, `onUnknown: escalate` has blocking precedence over otherwise compatible outcomes at the same
resolution stage, while `onUnknown: ignore` never changes an unknown condition to false and does
not erase that unknown from a trace. Array order, lexical id order, and implementation-defined
priority never select among rule outcomes in this experiment.

### 8.1 Handoff configuration

Evaluation state and handoff configuration are distinct. An unresolved or not-applicable result
exists independently of the optional `escalation` object; `escalation` is not itself an outcome.

For a generated reason, the configured target is requested when `escalation` is present and at
least one retained reason appears in `escalation.triggers`. When several reasons match, the
experiment creates one handoff request to the configured target and includes the complete retained
reason set. A true exception with effect `escalate` is a direct request and uses the configured
target regardless of the trigger list.

When `escalation` is omitted, there are no default triggers and no default target. When it is
present but no generated reason matches its triggers, there is likewise no configured handoff for
that reason. In either case, an unresolved result remains unresolved and must not be converted into
a fallback or other outcome. A direct exception escalation without an `escalation` object remains
an unresolved direct request with no Core-defined destination.

## 9. Extensions

`extensions` is an object whose keys use reverse-domain naming, for example
`com.example.review-policy`. Values may be any JSON value.

An optional extension MUST NOT change Core semantics. Consumers preserve optional extensions when
round-tripping but may otherwise ignore them.

Required extension semantics are declared in `metadata.requiredExtensions`. A consumer that does
not support every required extension MUST report the document as structurally readable but not
fully interpretable. It MUST NOT silently ignore a required extension.

Every name in `metadata.requiredExtensions` MUST appear as a key in at least one `extensions`
object in the document. A required-extension declaration without a corresponding value is
semantically invalid. An extension key omitted from `metadata.requiredExtensions` is optional.

Names beginning with `org.judgmentpack.` are reserved for future specification-defined extensions.

## 10. Security and privacy considerations

Implementations must treat packs, sources, citations, extensions, and runtime facts as untrusted
input. They SHOULD define limits for document bytes, nesting depth, collection sizes, string sizes,
and evaluation work.

Implementations MUST NOT:

- execute code found in strings or extensions;
- fetch source locators during ordinary validation unless explicitly requested;
- treat a URL or publisher name as proof of authenticity;
- expose sensitive evidence merely because a pack references it;
- convert conformance into authorization; or
- continue after silently dropping malformed or unsupported required content.

## 11. Versioning

`specVersion` identifies this specification draft. `version` identifies the pack revision. They are
independent.

During `0.x`, any specification release may be breaking. A future stable specification must define
reader, writer, and semantic compatibility separately and supply machine-readable migration cases.

A published pack version SHOULD be immutable. Changed content SHOULD receive a new version.

## 12. Normative references

- [BCP 14](https://www.rfc-editor.org/info/bcp14), including RFC 2119 and RFC 8174, defines the
  requirement keywords used by this document.
- [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) defines JSON.
- [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986) defines URI syntax.
- [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339) defines the date and date-time forms used by
  schema format assertions.
- [RFC 6901](https://www.rfc-editor.org/rfc/rfc6901) defines the JSON Pointer syntax admitted by
  `fact.path`.
- [JSON Schema Core, Draft 2020-12](https://json-schema.org/draft/2020-12/json-schema-core) and
  [JSON Schema Validation, Draft 2020-12](https://json-schema.org/draft/2020-12/json-schema-validation)
  define the schema dialect and validation keywords used by the normative schema.

## 13. Open questions

Before a candidate stable core, the project must resolve:

- whether portable rule evaluation belongs in Core or a separate profile;
- exact decimal, unit, date/time comparison, and normalization semantics;
- the minimum provenance and lineage model;
- whether authority and evaluation bindings belong in optional profiles;
- content identity, canonicalization, and signatures;
- imports and content-addressed dependencies;
- profile and capability negotiation; and
- a machine-readable semantic diagnostic contract.

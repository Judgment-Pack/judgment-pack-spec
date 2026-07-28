# Judgment Pack Core `0.2.0-draft`

## Status

This document is a research preview. It may change incompatibly and MUST NOT be represented as an
industry standard or as suitable, by conformance alone, for consequential decisions.

`0.2.0-draft` defines four conformance classes: carrier, structural, and semantic document
conformance, unchanged in substance from `0.1.0-draft`, and evaluator conformance (§3.4), which is
new. Sections 7 and 8 are normative for an implementation that claims the evaluator class and
informative for every other consumer; a document-conformance claim does not depend on them. The
document format is unchanged: a `0.1.0-draft` pack is unchanged in meaning here and may be
re-declared as `0.2.0-draft` without other edits (§11).

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

The core defines representation and document conformance. For an implementation that claims
evaluator conformance (§3.4) it also defines portable evaluation semantics (§§7–8) and one portable
result, the disposition of §8.3. It does not establish truth, authority, safety, or fitness for a
deployment, and a disposition is not made true, authorized, or safe by being portable.

### 1.1 Normative artifacts and precedence

The artifacts in this repository have distinct roles:

- this document is the normative prose for carrier and semantic document conformance, for evaluator
  conformance, and for the interpretation of schema-defined fields;
- [`schema/judgment-pack-core.schema.json`](../schema/judgment-pack-core.schema.json) is the
  normative machine-readable projection of structural document constraints;
- the evaluation corpus — the manifest and case fixtures under
  [`conformance/evaluation/`](../conformance/evaluation/README.md), not its README — is normative for
  evaluator conformance (§3.4) and for nothing else. This is the normative status the bullet below
  reserves for a later specification, granted here to those files only; and
- examples, the document-conformance corpus, READMEs, design notes, RFCs, the roadmap, and
  implementation behavior are informative unless a later specification explicitly gives an artifact
  normative status.

A conformance claim MUST satisfy all applicable normative requirements. If the schema or the
evaluation corpus disagrees with this document, this document controls and the mismatch is a
specification defect that SHOULD be reported. An example, test fixture, validator, or product
behavior cannot override any normative artifact.

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
because they contain digits. Core `0.2.0-draft` has no general decimal type marker; exact decimal
quantities outside ordered fact-condition operands require a future profile or declared extension.

This section defines decimal lexical syntax only. It has no decimal type marker and does not define
decimal equality, scale, units, or cross-unit conversion. §7.4 defines ordered comparison of two
strings satisfying this grammar for evaluator conformance (§3.4) and nothing else; it defines no
decimal-aware *equality*, so `equals` compares two such strings as strings. Outside that class,
satisfying this grammar does not imply executable comparison support.

## 3. Conformance classes

This draft defines three document conformance classes and one evaluator conformance class. The
document classes are unchanged in substance from `0.1.0-draft` and do not depend on the evaluator
class. It defines no execution conformance: applying an outcome remains outside Core.

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

An implementation is *evaluator conforming* when, given

- a semantically conforming pack (§3.3);
- one JSON facts document;
- one evidence-availability document (§8.2); and
- its own supported-extension set,

it produces the portable disposition of §8.3 under the semantics of §§7–8, reports every condition
that prevents completing an evaluation as an evaluation error rather than as a disposition (§8.4),
defines the limits §10 requires of this class, and passes the evaluation corpus published for the
exact `specVersion` it names.

The claim is narrow by construction: it says that the implementation computed the disposition this
document specifies for those inputs. It says nothing about the pack, the facts, the evidence, or the
consequences of acting on a disposition (§3.5).

An implementation that computes the disposition this document specifies and fails a corpus row has
found a specification defect in that row, not a conformance failure. §1.1 makes this document
control; the row is corrected under §3.4.1's corpus versioning, and no claim is made or lost against
a defective row.

Carrier, structural, and semantic document conformance are untouched by this class. A document is
conforming or not without reference to any evaluator, and an implementation MAY claim document
conformance alone.

#### 3.4.1 Evaluator-conformance claims

Exactly one form of evaluator-conformance claim is definable: a claim against this class and against
the [evaluation corpus](../conformance/evaluation/README.md) for one exact `specVersion`, naming that
version, the corpus version, and the results obtained. Everything else remains forbidden. An
implementation MUST NOT:

- claim partial or qualified evaluator conformance — a subset of §§7–8, a subset of the corpus, or
  conformance "except for" any requirement;
- claim evaluator conformance on the strength of prototyping, of an experimental surface, or of
  agreement with another implementation, in place of corpus results;
- claim evaluator conformance without having run the evaluation corpus for the exact `specVersion`
  claimed;
- claim evaluator conformance under `0.1.0-draft`, which defines no such class, or under any
  `specVersion` whose corpus it has not run; or
- describe an evaluator-conformance claim as establishing anything §3.5 excludes.

A claim is made against one exact `specVersion` and is not inherited by any other version (§11).
The evaluation corpus is a *seed* corpus: it is version-pinned, it is not exhaustive, and it grows by
RFC. Passing it is necessary for the claim and is not evidence that the implementation is correct on
inputs the corpus does not contain.

The corpus is **frozen at the release of a `specVersion`** and grows only into the next one: rows are
added, changed, or corrected on the way to a later `specVersion`, never inside a released one, so two
identically worded claims against the same `specVersion` require the same rows. "The corpus version"
a claim must name is the `suiteVersion` member of the evaluation manifest, which for a released
version equals the `specVersion` the corpus was published for.

### 3.5 Non-claims

Conformance MUST NOT be described as proof that:

- a claim is true;
- evidence is authentic or sufficient;
- an author or reviewer had authority;
- an outcome is legally or ethically permissible;
- a particular runtime applied the pack correctly; or
- use of the pack is safe.

The runtime-correctness bullet has exactly one narrow exception. An evaluator-conformance claim
(§3.4) asserts that the claimed implementation computed the §8.3 disposition this document specifies
for the evaluation-corpus inputs it ran. It asserts nothing about any other input, any deployment,
any particular run in production, the facts and evidence a caller supplied, or the permissibility of
acting on a disposition. Every other bullet above applies to the evaluator class unchanged.

## 4. Root object

| Member                 | Required | Meaning                                                 |
| ---------------------- | -------: | ------------------------------------------------------- |
| `specVersion`          |      yes | Exact value `0.2.0-draft`                               |
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

Core `0.2.0-draft` has no imports or remote-reference resolution. All rule, outcome, source,
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

The representation has no rule-priority field, and array order carries no priority meaning. Handling
of conflicts and `onUnknown` appears in §8, which is normative for evaluator conformance (§3.4) and
informative for a document-conformance consumer.

### 6.6 Exception

An exception declares a condition and one effect:

- `suppress-rule`, with `targetRule`;
- `force-outcome`, with `outcome`; or
- `escalate`.

For `suppress-rule`, `targetRule` is required and `outcome` is absent. For `force-outcome`, `outcome`
is required and `targetRule` is absent. For `escalate`, both are absent. Every exception also has a
required `onUnknown` policy of `ignore` or `escalate`. Evaluation order and effect compatibility
appear in §8, which is normative for evaluator conformance (§3.4) and informative for a
document-conformance consumer.

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

## 7. Condition interpretation

This section is **normative for evaluator conformance** (§3.4) and informative for every other
consumer. In `0.1.0-draft` the results described here were informative in every direction; that note
is amended, and amended only for the evaluator class. The allowed JSON shapes for conditions remain
normative through the schema for all classes, and a carrier, structural, or semantic document
conformance claim is unaffected by anything in this section: no result below can make a document
conforming or non-conforming.

A condition produces `true`, `false`, or `unknown`:

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

`equals` uses type-preserving JSON equality: null equals null; Booleans and
strings compare by value; JSON numbers compare by their mathematical value without lossy
conversion; arrays compare recursively in order; and objects compare recursively by member name
and value without regard to member order. There is no coercion between JSON types. `not-equals` is
the Boolean inverse of `equals` when equality can be determined.

For `in`, the schema requires the condition value to be a non-empty array. The selected fact value
is compared for equality with each array item. A match produces `true`; no match produces `false`.

The schema requires operands of `greater-than`, `greater-than-or-equal`, `less-than`, and
`less-than-or-equal` to satisfy the decimal grammar in §2.2. An ordered comparison is *defined* if
and only if both the selected fact value and the operand are JSON strings satisfying that grammar;
the two are then compared by mathematical value. Any other selected value — including a JSON number,
a Boolean, null, an array, an object, or a string that does not satisfy the grammar — makes the
comparison undefined and produces `unknown`. A JSON number is deliberately not coerced: the grammar
exists because a number's decimal identity is not preserved, and silently accepting one would make
two implementations disagree.

Equality of decimal strings is *string* equality and is deliberately not decimal-aware. `"1.0"` and
`"1.00"` are therefore not equal under `equals`, and `not-equals` is correspondingly `true`, while
neither is greater than the other under an ordered comparison, which reads both by mathematical value.
The two families of operator answer different questions and Core defines no reconciliation between
them; a pack that needs decimal-aware equality must normalize scale in the pack, in the operand and in
the facts it is compared against.

Units, quantities carrying units, and date or time values have no ordered comparison here. Such an
operand does not satisfy §2.2, so an ordered comparison over one is not expressible rather than
merely unknown-by-accident; `equals`, `not-equals`, and `in` still compare those values as ordinary
JSON. Outside evaluator conformance, structural acceptance of an ordered condition still implies no
executable support.

An implementation claiming evaluator conformance (§3.4) MUST implement every operator listed above.
"Unsupported operator" is not an available result for that class, and answering `unknown` where this
section defines `true` or `false` is a failure to implement §7.4 rather than a conforming result —
§3.4.1 forbids claiming a subset of §§7–8, whether or not a corpus row happens to exercise the
operator. Within that class `unknown` is produced by exactly three things: a path that is absent or
does not resolve; a selected value or operand whose shape the operator does not admit, which includes a
value carrying units, since this section does not admit one in an ordered comparison at all; and a value
the implementation cannot compare exactly. That last case is confined to JSON numbers outside an
implementation's exact range, it is the one open question of §13 that §8.3 names as the single seam in
its byte-agreement requirement, and it is not permission to return `unknown` for anything else.

### 7.5 Evidence presence

`evidence-present` is `true` when the evaluation input records the named requirement as available,
`false` when it records the requirement as absent, and `unknown` when the input cannot say. For
evaluator conformance those three states are supplied by the evidence-availability document of §8.2:
`present` is `true`, `absent` is `false`, and `unknown` — including an omitted key — is `unknown`.
That tri-state input replaces `0.1.0-draft`'s appeal to a "complete evidence manifest", which was
undefined and was the one recorded semantic divergence between careful readings of that draft. This
draft still defines no evidence-manifest interchange format beyond the tri-state of §8.2.

## 8. Resolution model

This section is **normative for evaluator conformance** (§3.4) and informative for every other
consumer, on the same terms as §7. The step order below is contractual only where it changes the
disposition; it mandates no implementation algorithm, and an implementation may compute in any order
that yields the specified disposition. §8.2 defines the inputs, §8.3 the one portable result, and
§8.4 the errors that replace a result.

Resolution produces one of three result kinds:

- an `outcome` result naming exactly one declared outcome;
- a `not-applicable` result carrying reason `not-applicable`, which is not an outcome; and
- an `unresolved` result carrying one or more reasons.

The generated reason vocabulary is `not-applicable`, `missing-required-evidence`, `unknown`,
`conflict`, and `no-match`, matching `escalation.triggers`. A true exception with effect `escalate`
adds the separate reason `exception-escalation`; that reason is a direct request rather than a
trigger-selected request. A result may retain multiple reasons. Reasons are a de-duplicated set;
their order carries no priority. Implementations may additionally record contributing rule,
exception, or evidence-requirement ids, outside the disposition (§8.3).

The algorithm is:

1. Treat omitted `applicability` as the literal value `true`. If applicability is false, produce a
   terminal `not-applicable` result carrying reason `not-applicable` and do not evaluate exceptions
   or rules. If it is unknown, produce an `unresolved` result with reason `unknown` and stop.
2. Inspect every required evidence requirement, using the presence values of §7.5. Record
   `missing-required-evidence` if and only if at least one required requirement's presence is
   `false`. Record `unknown` if and only if at least one required requirement's presence is
   `unknown` and none is `false`. Retain the ids of the requirements that produced either reason for
   diagnostics. This restates `0.1.0-draft`'s binary "any required evidence is absent" test in the
   three-valued terms of §7.5, and is the resolution of that draft's one recorded semantic
   divergence.
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

5. Record reason `conflict` for incompatible forced outcomes. If step 2 recorded either of its
   reasons, an exception is unknown with `onUnknown: escalate`, exception effects conflict, or a true
   exception directly requests escalation, produce `unresolved` after all exception effects have been
   inspected, and do not evaluate normal rules. Retain every reason discovered at this stage. A
   direct exception escalation is also retained as such in diagnostics.
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
priority MUST NOT select among rule outcomes, and a conflict MUST NOT be tie-broken: it is an
`unresolved` result.

### 8.1 Handoff configuration

Evaluation state and handoff configuration are distinct. An unresolved or not-applicable result
exists independently of the optional `escalation` object; `escalation` is not itself an outcome.

For a generated reason, the configured target is requested when `escalation` is present and at
least one retained reason appears in `escalation.triggers`. When several reasons match, resolution
creates exactly one handoff request to the configured target and includes the complete retained
reason set. That complete set is carried in the disposition's `reasons`; `handoff.triggeredBy` names
the subset of it that triggered the request, which is smaller whenever `escalation.triggers` does not
name every retained reason (§8.3). A true exception with effect `escalate` is a direct request and
uses the configured target regardless of the trigger list.

When `escalation` is omitted, there are no default triggers and no default target. When it is
present but no generated reason matches its triggers, there is likewise no configured handoff for
that reason. In either case, an unresolved result remains unresolved and must not be converted into
a fallback or other outcome. A direct exception escalation without an `escalation` object remains
an unresolved direct request with no Core-defined destination; the disposition records it as a
requested handoff whose destination the pack does not supply (§8.3).

### 8.2 Evaluation inputs

An evaluation takes exactly four inputs. Three are documents; the fourth is a property of the
implementation.

- **Pack** — one semantically conforming document (§3.3). A pack that is not semantically conforming
  is an evaluation error (§8.4), not a disposition.
- **Facts** — one JSON document. Every `fact.path` is an RFC 6901 JSON Pointer evaluated against it
  (§7.4). There is exactly one facts document per evaluation; Core defines no fact namespace,
  merging, or acquisition.
- **Evidence availability** — one JSON object whose member names are declared
  `evidenceRequirements[].id` values and whose values are exactly one of the strings `present`,
  `absent`, or `unknown`. An omitted key means `unknown`. An omitted document as a whole means every
  declared requirement is `unknown`. A member name that is not a declared requirement id, or a value
  outside those three strings, is an evaluation error (§8.4) — an undeclared key is far more likely
  to be a caller's mistake than a statement about the pack. Duplicate member names are already
  rejected by §2.1.
- **Supported extensions** — the set of `metadata.requiredExtensions` capabilities the implementation
  supports. A required capability outside that set is an evaluation error (§8.4), never a
  disposition (§9).

Core defines no transport, file layout, or command-line surface for these inputs. It defines what
they mean.

### 8.3 The portable disposition

An implementation claiming evaluator conformance MUST produce, for each evaluation, exactly one
*disposition* or exactly one evaluation error (§8.4) and no disposition. The disposition is a JSON
object with these members and no others:

| Member      | Present                  | Value                                                       |
| ----------- | ------------------------ | ----------------------------------------------------------- |
| `kind`      | always                   | `outcome`, `not-applicable`, or `unresolved`                 |
| `outcomeId` | iff `kind` is `outcome`  | the `id` of exactly one declared outcome                     |
| `reasons`   | always                   | the retained reason set, serialized as a sorted array        |
| `handoff`   | always                   | an object carrying the handoff state, and its trigger        |

`kind` is the result kind produced by §8. `not-applicable` and `unresolved` are not outcomes and MUST
NOT be mapped onto one, defaulted to one, or flattened into the same field as `outcomeId`.

`outcomeId` MUST be present when `kind` is `outcome` and MUST be absent otherwise — absent, not
`null` and not an empty string. It MUST name a declared outcome of the pack evaluated.

`reasons` is a **set**: unordered and duplicate-free. Its members are drawn from
`not-applicable`, `missing-required-evidence`, `unknown`, `conflict`, `no-match`, and
`exception-escalation`; no other value is admitted. It is empty if and only if `kind` is `outcome`.
When `kind` is `not-applicable` its one member is `not-applicable`. Two dispositions have the same
`reasons` when the sets are equal; serialized order is never a difference in the disposition.

`handoff` is an object with:

- `state` — `requested` when §8.1 makes a handoff request, whether trigger-selected or a direct
  exception request, and including a direct exception request made when the pack carries no
  `escalation` object, in which case the request has no Core-defined destination (§8.1). `none`
  otherwise. Present always.
- `triggeredBy` — present if and only if `state` is `requested`. A non-empty **set** of reason
  identifiers: every retained reason that appears in `escalation.triggers`, plus
  `exception-escalation` when a true exception with effect `escalate` made a direct request (§8.1).
  It is always a subset of `reasons`.

The disposition does not echo the configured escalation target. A consumer that needs the target
reads it from the pack; carrying a copy here would let a disposition disagree with the pack it came
from, and the target is a display name, not an address (§6.7). A requested handoff is a request, not
evidence that a handoff occurred.

Nothing else belongs in the disposition object. An implementation MAY report a trace, contributing
rule, exception, or evidence-requirement ids, timings, or any other diagnostic **outside** the
disposition, and their presence or absence MUST NOT change any member above.

**Serialization.** So that two conforming implementations can be compared:

- both sets — `reasons` and `handoff.triggeredBy` — are serialized as JSON arrays whose elements are
  sorted ascending by Unicode code point, with no duplicates;
- an absent member is omitted, never serialized as `null`;
- member order carries no meaning; and
- where a byte comparison is required, each disposition is first canonicalized as described by
  RFC 8785, which orders object members by name. A disposition contains no numbers, so that
  specification's number rules never engage.

Two conforming implementations given the same pack, facts document, evidence-availability document,
and supported-extension set MUST produce byte-identical canonicalized dispositions. That is the whole
of the portability claim, and §3.5 applies to every part of it.

That requirement has exactly one seam, and this is the whole of it: whether equality involving a JSON
number an implementation cannot represent exactly is `unknown` or an explicit input error is an open
question (§7.4, §13). Until §13 closes it, two implementations with different arithmetic ranges may
answer differently on such a value, and an input carrying one is outside the portable claim. No other
input, operator, or member is outside it, and no other implementation-relative escape exists in §§7–8:
an implementation MUST NOT read this seam as permission to answer `unknown` anywhere else.

Two illustrative canonicalized dispositions, informative:

```json
{"handoff":{"state":"none"},"kind":"outcome","outcomeId":"proceed","reasons":[]}
```

```json
{"handoff":{"state":"requested","triggeredBy":["missing-required-evidence"]},"kind":"unresolved","reasons":["missing-required-evidence"]}
```

### 8.4 Evaluation errors

An evaluation error is not a disposition. When an implementation claiming evaluator conformance
cannot complete an evaluation, it MUST report an evaluation error, MUST NOT emit a disposition for
that evaluation, and MUST NOT substitute `unresolved`, `not-applicable`, or a fallback outcome for
the error. Evaluation terminates wherever §8 had reached, and partial state MUST NOT be reported as a
result. This is the §3.1 rule applied one layer up: a documented limit or a malformed input produces
explicit failure, never a silent partial processing that a caller could mistake for a result. A
truncated evaluation reported as a disposition is a forged disposition.

An implementation MUST report the class of every evaluation error, identified by exactly one of:

- **`pack-not-conformant`** — the pack input is not a semantically conforming document (§3.3),
  failing at any of the carrier, structural, or semantic layer.
- **`unsupported-required-extension`** — the pack declares a capability in
  `metadata.requiredExtensions` that the implementation does not support. §9's "structurally readable
  but not fully interpretable" report is this error for the evaluator class: the unsupported part may
  be the part that decides, so no disposition may be produced.
- **`malformed-input`** — the facts document or the evidence-availability document is not a
  carrier-conforming JSON text (§2.1), or the evidence-availability document violates §8.2 by
  carrying an undeclared member name or a value outside `present`, `absent`, and `unknown`.
- **`resource-exhaustion`** — a limit documented under §10 was reached.

More than one class can apply to the same inputs: an over-limit facts document is `malformed-input`,
because §2.1 requires rejecting data beyond a documented limit, and equally `resource-exhaustion`; a
pack that fails semantic conformance presented with an evidence document carrying an undeclared key is
both `pack-not-conformant` and `malformed-input`. The classes are therefore evaluated in one fixed
order — `pack-not-conformant`, then `malformed-input`, then `unsupported-required-extension`, then
`resource-exhaustion` — and the first that applies is the class reported, so that two conforming
implementations report the same class for the same inputs. An implementation MAY name the other classes
it also considered as message detail.

An implementation MAY define additional classes for conditions none of these cover, and MAY attach any
message detail it likes. An implementation-defined class MUST be named in the reverse-domain form of
§9 — for example `com.example.timeout` — which cannot collide with a Core class identifier, since
those are bare kebab-case names, nor with a class another implementation defines. The transport, exit
status, and wire format of an evaluation error are not defined here; the class identifier is. A
machine-readable diagnostic contract remains open (§13).

## 9. Extensions

`extensions` is an object whose keys use reverse-domain naming, for example
`com.example.review-policy`. Values may be any JSON value.

An optional extension MUST NOT change Core semantics. Consumers preserve optional extensions when
round-tripping but may otherwise ignore them.

Required extension semantics are declared in `metadata.requiredExtensions`. A consumer that does
not support every required extension MUST report the document as structurally readable but not
fully interpretable. It MUST NOT silently ignore a required extension. For an implementation claiming
evaluator conformance, that report is the `unsupported-required-extension` evaluation error of §8.4
and no disposition is produced.

Every name in `metadata.requiredExtensions` MUST appear as a key in at least one `extensions`
object in the document. A required-extension declaration without a corresponding value is
semantically invalid. An extension key omitted from `metadata.requiredExtensions` is optional.

Names beginning with `org.judgmentpack.` are reserved for future specification-defined extensions.

## 10. Security and privacy considerations

Implementations must treat packs, sources, citations, extensions, and runtime facts as untrusted
input. They SHOULD define limits for document bytes, nesting depth, collection sizes, string sizes,
and evaluation work.

An implementation claiming evaluator conformance (§3.4) MUST define and document at least its
collection-size and evaluation-work limits, and reaching one MUST produce the
`resource-exhaustion` evaluation error of §8.4 rather than a disposition. Defining a limit is not
portability: two conforming implementations may define different limits, so an input above either
one is outside the portable claim. The evaluation corpus therefore keeps its cases well inside any
plausible limit instead of probing one.

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

`0.2.0-draft` changes no part of the document format. A pack declaring `specVersion` `0.1.0-draft` is
unchanged in meaning under this draft and may be re-declared as `0.2.0-draft` by editing that one
value and nothing else. Because the value is exact (§4), an unedited `0.1.0-draft` pack is not
structurally conforming to `0.2.0-draft` and must be re-declared before an implementation claiming
this draft evaluates it; the `0.1.0-draft` schema remains published for packs that keep the older
value.

An evaluator-conformance claim (§3.4) attaches to one exact `specVersion` and to the evaluation
corpus published with it. It is not inherited by a later or an earlier version, and re-declaring a
pack acquires nothing for the implementations that read it.

## 12. Normative references

- [BCP 14](https://www.rfc-editor.org/info/bcp14), including RFC 2119 and RFC 8174, defines the
  requirement keywords used by this document.
- [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) defines JSON.
- [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986) defines URI syntax.
- [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339) defines the date and date-time forms used by
  schema format assertions.
- [RFC 6901](https://www.rfc-editor.org/rfc/rfc6901) defines the JSON Pointer syntax admitted by
  `fact.path`.
- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) defines the JSON canonicalization used by §8.3
  when two dispositions are compared byte for byte.
- [JSON Schema Core, Draft 2020-12](https://json-schema.org/draft/2020-12/json-schema-core) and
  [JSON Schema Validation, Draft 2020-12](https://json-schema.org/draft/2020-12/json-schema-validation)
  define the schema dialect and validation keywords used by the normative schema.

## 13. Open questions

Whether portable rule evaluation belongs in Core or in a separate profile is closed: §3.4 places the
class in Core, so the error contract and the disposition shape live in one place that a later
evaluation profile can build on rather than restate. Before a candidate stable core, the project must
still resolve:

- exact unit, date/time, and normalization semantics beyond the decimal-string ordering of §7.4;
- whether equality between syntactically valid but arithmetically unrepresentable JSON numbers is
  `unknown`, as §7.4's incomparable-value rule implies, or an explicit input error. This is the single
  seam §8.3 excludes from its byte-agreement requirement, and the evaluation corpus carries no row for
  it because a row cannot state an expected result until the question is closed;
- an interchange form for evidence beyond §8.2's tri-state, and whether §8.2 grows into it;
- the minimum a trace must surface, including whether it must surface a true rule that a forced
  outcome skipped;
- a machine-readable diagnostic contract, for document validation and for the §8.4 error classes;
- the minimum provenance and lineage model;
- whether authority bindings belong in optional profiles;
- content identity, canonicalization, and signatures;
- imports and content-addressed dependencies; and
- profile and capability negotiation.

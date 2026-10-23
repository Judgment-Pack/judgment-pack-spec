# RFC 0027: Bounded pack-design advisories

- Status: Draft
- Type: Standards track, optional tooling contract at draft maturity
- Created: 2026-10-23
- Target: Core `0.4.0`; not incorporated into Core
- Issue: [#252](https://github.com/Judgment-Pack/judgment-pack-spec/issues/252)

## Summary

Propose optional, bounded pack-design diagnostics for compatible overlap, scoped coverage,
reachability, exception effects, and unknown facts. Diagnostics explain Core §§7–8; they add no
operator, priority, outcome, evaluator requirement or document-conformance failure. This Draft and
its proposal schema are normative for nothing. Acceptance, incorporation, public review and release
remain separate gates. The released `0.3.0` schemas, corpora and claims are unchanged.

## Problem

The existing recommended check in Core §3.3.1 reports overlapping conditions of rules naming
different outcomes. Authors also need to see agreement, intentional fallback, dead conditions and
exception interactions. Calling all overlap a conflict misstates Core. Calling an unobserved rule
unreachable mistakes a sample for proof. Calling every fallback a defect invents author intent.

## Evidence

Core §8 already defines same-outcome agreement, incompatible force effects, suppression, direct
escalation and unknown blocking. [The hand-written cases](pack-design-advisories/cases.json)
exercise those distinctions, including decimal endpoint equality and absent/null/non-comparable
facts. They are proposal examples, outside every released conformance manifest.

Existing Runtime work is reusable, with narrower claims:

- [Runtime #98](https://github.com/Judgment-Pack/judgment-pack-runtime/issues/98) supplies
  comparison-boundary probes;
- [Runtime #101](https://github.com/Judgment-Pack/judgment-pack-runtime/issues/101) suggests
  candidate inputs; and
- [Runtime #151](https://github.com/Judgment-Pack/judgment-pack-runtime/issues/151) checks
  pack-independent unreachable expectations, not whether this pack's rule can contribute.

The existing overlap implementation is tracked in
[Runtime #304](https://github.com/Judgment-Pack/judgment-pack-runtime/issues/304).
These primitives do not establish pack-specific coverage or reachability. The additional runtime
advisories belong to [Runtime #314](https://github.com/Judgment-Pack/judgment-pack-runtime/issues/314).
No complete static solver or independent implementation is claimed here.

## Specification

### Scope and resolution

The proposed landing is a new non-normative Core §3.3.2, with a separately versioned optional report
contract. Core §3.3.1's `JPS-RULES-OVERLAP`, `exact`/`not-excluded`, mandatory members and severity
policy remain byte-for-byte unchanged. In particular, an overlap of rule *conditions* is not proof
that the rules are evaluated: applicability, evidence and exceptions precede them.

For the new findings, reproduce Core §8 in order: applicability; required evidence and every
exception; conflicting force/direct escalation/unknown blocking; compatible force; suppression;
normal rule candidates; compatible agreement/conflict; fallback/no-match. Evaluate all effects at
the same stage and retain all reasons. A suppressed or bypassed rule is not an evaluated false
rule. Array order, id order and arbitrary winner selection supply no priority. A same-outcome
candidate set is compatible even when another stage prevents the final outcome.

A rule **contributes** when it survives earlier gates and suppression, is evaluated, and is true,
thus entering the candidate set. It can contribute during a rule conflict or alongside an unknown
rule; contribution does not imply a resolved disposition. **Condition never true** and **never
contributes** are different claims. This is a candidate-contribution definition local to these
advisories. RFC 0028's final contributor metadata names contributors to a successful final outcome;
it does not include candidates from an unresolved conflict. Neither contract substitutes its
definition for the other. Evidence references on rules are citations, not extra gates.

### Decision table and severity

| Situation within the stated domain | Finding code / effect | Certainty | Severity |
| --- | --- | --- | --- |
| Two or more true rules name one outcome | `JPS-RULES-COMPATIBLE` / `compatible-agreement` | proved by finite-domain evidence; otherwise possible | info |
| Every contribution of a rule has another contributing rule of the same outcome | `JPS-RULE-REDUNDANT` / `outcome-redundancy` | proved only | info |
| Different-outcome conditions overlap | Existing `JPS-RULES-OVERLAP` contract | existing exact/not-excluded | existing policy |
| Reachable fallback, explicitly declared intentional by the caller | `JPS-COVERAGE-GAP` / `fallback-reachable` | proved or possible | info |
| Reachable fallback without that declaration, or reachable no-match | `JPS-COVERAGE-GAP` / `fallback-reachable` or `no-match-reachable` | proved or possible | warning |
| No true point of a condition, or no contribution after all gates | `JPS-RULE-UNREACHABLE` / `condition-never-true` or `never-contributes` | proved only | warning |
| Incompatible true force effects | `JPS-EXCEPTION-INTERACTION` / `forced-conflict` | proved or possible | warning |
| Compatible force bypasses rules, or true suppression removes a rule | `JPS-EXCEPTION-INTERACTION` / `force-bypasses-rules` or `suppression` | proved or possible | info |
| Direct exception escalation blocks resolution | `JPS-EXCEPTION-INTERACTION` / `direct-escalation` | proved or possible | warning |
| Unknown applicability, evidence, rule or exception blocks an outcome/fallback | `JPS-UNKNOWN-INTERACTION` / `unknown-blocks-resolution` | proved or possible | warning |
| Unsupported analysis or exhausted work/output limit | `JPS-ANALYSIS-INCOMPLETE` / `analysis-incomplete` | incomplete | info |

`proved` means the stated claim has proof, not that all inputs were analyzed: an existential claim
can be proved by one replayable witness. A universal claim needs exhaustive declared-domain
analysis over the entire finite domain. Sound set algebra is a possible future capability only.
`possible` means the analysis has not excluded the interaction; it must not be phrased as an observed effect or actual conflict. `incomplete` describes analysis, not
an evaluation result. A possible finding names the unresolved limitation and suggested cases.
In format 1 a declined check sets the overall report incomplete, even when other checks completed.

All new severities are identical in validation, strict and publication views. None blocks
publication, changes document admission, mutates a pack or changes Core dispositions. Applications
may set a separate local review policy, identified as such. Future conformance promotion needs a
separate explicit specification decision; it is not implied by this proposal or implementation.

`outcome-redundancy` means outcome-equivalent contributions within the declared domain only:
removing a rule's *true contribution* would not remove its outcome from the candidate set. It is
not permission to delete the rule: its unknown escalation,
source/evidence citations, diagnostics and downstream attribution can differ, and exceptions may
reference the rule. No automatic deletion is permitted. The proof must have at least one
contribution; a vacuously subsumed dead rule is an unreachable finding instead.
A caller's `intentionalFallback` declaration applies to this report's domain only; it never hides
no-match or unknown blocking. It is analysis input, not a new member of a pack.

### Explicit domains and proof fragments

Every report names the exact supported Core version used to validate and evaluate the pack, not
the specification release proposing the advisory contract. Initial examples analyze Core `0.3.0`;
this RFC targets incorporation in `0.4.0`. `targetSpecVersion` must equal the pack's complete
`specVersion` and be supported by the analyzer. No compatibility is inferred from version prefixes.
The format's `formatVersion: 1` identifies this advisory contract separately.

Every report binds exact retained UTF-8 input bytes with `packDigest` and `domainDigest`, each
`sha256:` plus 64 lowercase hexadecimal digits. Do not hash an arbitrary JSON reserialization.
The report's `domain` is the type-preserving parsed echo of the retained domain bytes; checking its
digest requires those bytes. Identical parsed domains with different bytes intentionally have
different digests. Digest identity establishes neither truth nor approval.

The initial schema supports only `fragment: "finite-enumeration"` and a `domain` with
`kind: "finite-cases"` and `inputs`: 1–64 complete evaluation inputs, each with `facts` and
`evidence`. Exhaustive enumeration proves universal claims only over those exact inputs. Evidence
maps use Core §8.2's `present`/`absent`/`unknown`; omitted keys stay unknown. Repeated inputs do not
enlarge the domain. Suggestions and sampled probes are not an exhaustive domain unless the caller
explicitly supplies exactly that finite set as the intended domain. No schema type, threshold,
probe list, test corpus or lack of observed cases implicitly establishes a fact domain.

Domain input admission has these fixed ceilings, before analysis: 1048576 UTF-8 bytes including
whitespace; 16384 JSON value nodes (every object, array and scalar counts once, object member names
are not additional nodes); depth 32 with the domain object at depth 0; 65536 UTF-8 bytes for each
decoded string or object member name; 4096 ASCII digits per JSON number token, counting all digits
in its integer, fraction and exponent; 256 evidence entries per input. Depth increases by one for
each array item or object member value. Values remain type-preserving JSON with exact number
comparison as supported by Core; the numeric-token ceiling is admission, not a coercion rule.

Malformed JSON, duplicate members, non-finite numbers, unpaired surrogates, wrong input/evidence
shape, empty domains and over-limit domains refuse the optional report with a bounded explanation
(`domain-invalid` or `domain-limit`); they cannot produce a complete analysis or exhaustive claim.
An unsupported Core version, pack profile, required capability or inadmissible pack is likewise a
`pack-unsupported` refusal before analysis. These explanation labels identify analysis refusal,
not new Core evaluation-error classes. A refused call produces no report. Pack admission and each
evaluator invocation retain their separately documented resource/capability limits; analyzer work
does not waive them. Evaluator failure after admission refuses the whole optional report with a
bounded `analysis-limit` explanation; it cannot be squeezed into an unrelated closed limitation
reason or yield exhaustive claims. Earlier partial results are not a completed report.

### Optional future symbolic analysis (not in format 1)

A later capability could declare a one-path domain as explicit absent/present JSON states and exact
decimal intervals, rejecting empty/reversed intervals and impossible absent-root states. Such a
capability needs its own schema/version and tested domain membership, spelling and endpoint rules;
no symbolic-domain wire shape or implementation is promised here.

For such a future one-path fragment, track disjoint true/false sets and their unknown complement
relative to that declared domain. Equality and membership use Core's type-preserving equality; ordered comparison
uses exact decimal order and admits only decimal strings. `all` intersects true sets and unions
false sets; `any` unions true sets and intersects false sets; `not` swaps them. Never replace
`not(A)` with a two-valued complement of A's true set. An absent fact stays unknown; null is a
present value (and equals null); JSON numbers, null and malformed decimal strings are unknown for
ordered comparisons. Cross-path correlation, collections requiring unsupported reasoning,
extensions affecting execution, or unsupported exact numeric comparison are named analysis limits.
A supported evaluator's Core operator requirements are unchanged by an analyzer's narrower support.

Apply those sets through the actual resolution gates to prove coverage or contribution. Finding
no true point is not enough to prove coverage: ignored unknowns can reach fallback; escalated
unknowns block it. Required evidence and direct escalation must be included. No default priority,
Boolean-only simplification, inferred independence of ancestor/descendant paths, universal SAT
solver or extension semantics may be invented. A tool may decline a claim instead of solving it.

### Report shape, evidence and bounds

[The closed proposal schema](pack-design-advisories/report.schema.json) uses `formatVersion: 1`
and the analyzed pack's exact `targetSpecVersion` (initially `"0.3.0"`). This is a staged proposal
identifier, not a published schema URL or release claim. Report members are `formatVersion`,
`targetSpecVersion`, `packDigest`, `domainDigest`, `domain`,
`fragment`, `intentionalFallback`, `limits`, `usage`, `complete`, `limitations` and `findings`.
The matching [report examples](pack-design-advisories/reports.json) are hand-authored. Format 1
requests all six finding families in the decision table, excluding the incomplete control code;
a tool lacking any family reports incomplete rather than quietly claiming full analysis.

Each finding has `code`, `effect`, `certainty`, `severity`, nonempty `sources` and `message`.
Suppression/force findings describe the observed skip only. A counterfactual lost candidate
requires separate, explicitly described replay/proof with the changed effect, all remaining gates
and Core semantics preserved; a skipped trace alone supplies no such evidence. Format 1 carries
no machine-readable lost-candidate assertion.

A source has a JSON Pointer `path` into the analyzed pack and its `id` when pointing to a named
rule/exception/requirement. Multi-rule findings identify every claimed contributor, including its
outcome through the referenced pack. IDs and pointers must agree and distinct claimed contributors
must resolve to distinct entities. A fallback uses `/fallbackOutcome`; analysis-wide limits can
point to the root. For unreachable and redundancy findings, the first source names the subject
rule; later redundancy sources name the covering rules, and later unreachable sources name gating
entities. For compatible agreement, every source is a participating same-outcome rule. Exception
interactions list the relevant exceptions and any affected rules; unknown findings name the
blocking rule/exception/requirement or applicability pointer. A no-match finding points to the
root. This evidence ordering conveys no Core winner or policy priority.

A proved finding carries a `proof` with `method` (`witness` or `exhaustive-domain`)
and a bounded `summary`. `witness` method requires a complete replayable `witness` input. A witness
proves existence only; unreachable and redundancy claims cannot use it. All witnesses must belong
to the stated domain and reproduce the claimed Core stage/effect, not merely the raw conditions.
A universal exhaustion proof explains the covered region and gates, including unknowns.
No machine-verifiable proof certificate or trust in a summary string is implied by schema validity.
A report reader must check pointers/IDs, input identity, domain membership and proof semantics
before presenting a finding as verified. Schema validation alone checks shape only.

Optional `suggestedCases` (at most 16) propose complete inputs to exercise a boundary or unresolved
interaction. They may be outside the domain if the message says so, and never become proof by
being proposed. A possible finding has suggested cases when available but no proof or witness purporting to
confirm it. Incomplete findings carry neither. All supplied input values are synthetic or caller
approved; tools need not echo confidential facts merely to give diagnostics.

`limits.maxWork` (1–100000) and `limits.maxFindings` (1–256) are declared before analysis;
`usage.work` cannot exceed `maxWork`. Charge one analyzer work unit **before** each evaluator
invocation for a domain input and before each finding predicate applied to one input and one rule,
one exception, one rule pair or one exception pair. A predicate is one check-family question for
that entity/input (for example, whether a pair contributes compatible outcomes); caching must not
skip the charge for the logical check. Reuse one real evaluation per input; querying cached
results incurs only its predicate charge. Exhaustion before a charge stops the affected work.

Before enumeration, admit at most 256 rules and 256 exceptions for this optional analyzer (not new
Core document ceilings). Generate pairs incrementally, charging each per-input predicate before
constructing or testing the pair; never materialize an unbounded Cartesian collection first.
Report construction, linear aggregation of already checked predicate results, and digesting do not
consume units, but remain bounded by admitted bytes, entity counts and output ceilings. Thus
`maxWork` bounds these analyzer operations, **not** evaluator internals, total CPU or wall time.
Each evaluator call uses its own declared execution bounds and can refuse independently.
Byte/depth admission for the supplied pack remains the evaluator's separate contract.
The 64-input and 16-suggestion caps are report ceilings, not Core document ceilings. Output has the
same 1048576-byte, depth-32, node-16384 and per-string/number limits as domain admission; a tool
must stop adding findings before these bounds, reserving space for the incomplete marker.
If the required domain echo leaves no room for that marker, refuse the optional report with an
analysis-limit explanation; never omit the echo, exceed bounds or return a false complete flag.

Reserve one finding slot for `JPS-ANALYSIS-INCOMPLETE` before beginning. It may be released only
after all requested analysis finishes without a limitation. If any check is skipped,
unsupported, interrupted or output-truncated, set `complete: false` and add a limitation and that
finding, preserving already established proofs. `usage.findingsTruncated` is true only for an
output limit, which must have an `output-limit` limitation. Never truncate silently, emit more than
`maxFindings`, claim no findings means no problems, or convert an incomplete analysis into a
proved absence. An implementation may instead refuse the whole optional report with a bounded
analysis-limit explanation. `complete: true` means all advertised checks finished within their
stated support, not that every conceivable check or all Core inputs were proved safe.

Limitations carry the affected pack pointer and one closed reason: `unsupported-condition`,
`unsupported-extension`, `unsupported-domain`, `work-limit`, `output-limit`, or
`numeric-comparison-limit`. An unsupported optional extension irrelevant to Core may be noted
without poisoning unrelated proofs; required or execution-affecting semantics cannot be assumed
away. Separate independent subclaims may retain proofs with their full relevant gates analyzed.

## Alternatives

No change preserves the existing check but leaves agreement and dead rules easy to mislabel.
Product-only free text avoids a schema but prevents tools from sharing certainty and evidence.
Extensions to the pack would mix analysis input with policy; this proposal keeps the domain and
intent declaration in a separate report. A mandatory complete SAT solver is unnecessary and cannot
cover arbitrary extension semantics. Reusing `JPS-RULES-OVERLAP` for every interaction would change
its stable different-outcome meaning and severity, so separate codes are proposed.

## Compatibility

Reader/writer effects are confined to consumers opting into this new report format; old report
readers need not accept it. Pack bytes and Core §§7–8 semantics are unchanged. No migration,
relabeling of frozen `0.3.0` vectors, new operator, implicit extension capability, or current
conformance claim follows. The proposed specification incorporation target is `0.4.0`; adoption
must publish its final exact format/schema and review its release compatibility separately. RFC 0028's attribution work is a
separate contract and this report does not alter its artifacts.

## Security and privacy

Exact search can exhaust resources; explicit work, output and domain bounds make limits observable.
Diagnostics can expose policy regions and caller facts; retain source pointers and proof summaries
without requiring production-value disclosure. Invented certainty or promotion of a warning into
an authorization decision is a risk. These advisories grant no authority and prove no factual truth,
fitness or safety. A proof is conditional on the supplied pack, explicit domain and Core semantics.

## Conformance

There is no advisory conformance class. The proposal cases and negative mutations check the
proposed report shape, every code/effect/severity/certainty, rejected unknown members, proof versus
possibility, and explicit limits. A small test-only three-valued evaluator verifies the hand-written
conditions and resolution examples, including rule/exception permutation, conflicting reasons,
non-comparable values, suppression and force bypass. It is not a new reference evaluator or proof
engine. Reports must never be cited as passes of the released document/evaluation corpora.

## Implementation

A finite enumerator can replay the caller's explicit case domain and aggregate truth and
contribution sets. A second implementation could independently interpret the conditions and
resolution stages over those same finite inputs. A future symbolic implementation could partition
one path's JSON values and exact decimal intervals, propagate true/false/unknown sets and then
resolution gates. Unsupported analysis must remain explicit. These are plausible independent
approaches, not existing independent implementations or a symbolic capability already implemented. Runtime primitives above can supply probes and suggestions; new
pack-specific gate-aware analysis needs its own implementation and tests.

## Unresolved questions

Public comment, adversarial review and maintainer disposition are pending; this implementation of
a Draft is not approval. Stable maturity still needs the repository's independent evidence. Final
publication of the report schema, optional capability discovery and any future expansion beyond
finite enumeration are separate adoption work. A future machine-checkable proof certificate is not
promised by the summary-only proof record.

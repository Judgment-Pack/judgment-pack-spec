# How Judgment Pack compares to prior art

<div class="notice notice-info"><strong>Informative.</strong> This page positions Judgment Pack
against related models. It is explanatory, not normative, and it does not claim superiority — each
model below is well suited to the problem it was designed for.</div>

Reviewers usually arrive with an existing model in mind and ask, reasonably, "how is this different
from the thing I already use?" This page answers that for the closest neighbors. The short version:
Judgment Pack standardizes a *portable, testable document describing the judgment behind one
decision* — not a rule language, not an orchestration language, and not a knowledge store.

## Decision Model and Notation (DMN)

DMN is the closest analog and the most useful comparison. DMN standardizes decision logic —
primarily decision tables — and a Decision Requirements Graph that links decisions together. Both
DMN and Judgment Pack treat a decision as a first-class, portable artifact.

Where they differ:

- **Evidence, uncertainty, and escalation are first-class in a pack.** DMN centers on inputs and
  decision tables; a pack additionally declares what evidence is required, what happens when
  information is unknown or conflicting, and when a human must take over. In a pack, "unknown" is a
  first-class result, not an implicit false.
- **Judgment Pack ships a smaller core and defers composition.** DMN already standardizes the
  requirements graph; Judgment Pack deliberately ships only the single decision today and treats
  composition as an open proposal ([the vision page](../architecture/vision.md) explains why).
- **Conformance is explicitly separated from truth and authority.** A pack's specification takes
  care to say that a conforming document is not thereby correct, authorized, or safe.

A fair one-line framing: Judgment Pack aims to be to AI-era, evidence-driven judgment what DMN is to
business decision tables — with uncertainty and escalation built in, and a smaller starting core.

## Policy engines (OPA / Rego, Cedar)

Policy engines evaluate whether an action is *allowed* under a policy, and they are excellent at it.
The difference is purpose. A policy engine answers an authorization question and is designed to be
enforced. A pack represents *judgment* — the evidence and reasoning behind a decision that may be
uncertain, may abstain, and may escalate to a human. A pack explicitly refuses to conflate evidence
with authority; authorization stays in your own systems. The two are complementary: a policy engine
might gate whether a pack's outcome is permitted to act.

## Rule engines and `json-rules-engine`-style formats

General rule engines execute condition/action rules. A pack is not a general-purpose rule language
(that is an explicit [non-goal](../non-goals.md)). It constrains itself to representing one
decision's judgment so that the document stays small, testable, and portable, rather than becoming a
Turing-complete program whose behavior no second tool can reproduce.

## Workflow and process notation (BPMN)

BPMN models *process* — the sequence of tasks and gateways in a workflow. A pack models the
*judgment* at a single decision point, not the flow around it. The common DMN/BPMN pairing is
instructive: process notation calls out to decision artifacts. A pack sits at that decision point,
carrying the evidence and escalation logic BPMN never intended to hold.

## Knowledge graphs, vector stores, and retrieval

These answer *what is known* and *what is relevant*. They do not declare which decision the
information serves, when a rule applies, which exception overrides it, or when to escalate. A
knowledge source is an **evidence input** to a pack, not a parent of it. [Why Judgment
Pack?](../why.md) develops this at length.

## LLM evaluation frameworks

Eval frameworks record inputs and expected outputs to measure a model. A pack represents the *rules
and reasoning being evaluated*, in a form separate from any one model or prompt. Evaluation cases can
be attached to a pack, but portable evaluation is a possible later profile, not a claim of the
current draft.

## Summary

| Model | Primary question | What a Judgment Pack adds |
| --- | --- | --- |
| DMN | What is the decision logic? | Evidence, uncertainty, escalation as first-class; smaller core |
| Policy engine | Is this action allowed? | Judgment vs authority kept separate; abstention |
| Rule engine | Which rules fire? | A bounded, testable, portable single decision — not a language |
| BPMN | What is the process flow? | The judgment *at* a decision point, not the flow |
| Knowledge graph / RAG | What is known / relevant? | Which decision the knowledge serves, and when to stop |
| LLM eval | How good is the model? | The reasoning being evaluated, independent of the model |

For where each proposed capability would live if it graduates, see the
[architecture vision](../architecture/vision.md); for the recurring questions, see the
[FAQ](../../FAQ.md).

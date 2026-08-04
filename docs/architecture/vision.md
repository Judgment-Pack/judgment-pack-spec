# Architecture vision (non-normative)

<div class="notice notice-warning"><strong>Non-normative.</strong> This page is not part of the
Judgment Pack Specification and not part of any conformance class. It describes a possible future
architecture and open proposals, not shipped behavior.</div>

For what the specification actually defines, read the
[core specification](../../spec/judgment-pack-core.md).

People often picture Judgment Pack as a multi-layer system: an agent consults a planner, which
selects a graph of packs, which are evaluated by a runtime into a composite result. That picture is
useful for understanding *where the project is headed*. It is not what the specification defines
today, and most of it is deliberately outside the specification's scope.

This page draws the whole picture and then labels every part by what it actually is — shipped,
proposed, runtime, or product — so the vision can be discussed without being mistaken for the
standard.

## What is shipped today

The specification defines exactly one thing: a **Judgment Pack** — a portable JSON document that
declares a single decision (its evidence requirements, applicability, rules, exceptions, outcomes,
uncertainty handling, escalation, and sources) — together with how to check that a document
**conforms** at the carrier, structural, and semantic layers.

As of `0.2.0-draft` it also defines what an *evaluation* of one pack means — the semantics an
implementation must follow to claim the evaluator conformance class, and the one portable result it
produces. It still ships no evaluator, and it defines no execution, no composition, no discovery, and
no runtime. Those exclusions are intentional; see the [non-goals](../non-goals.md).

## The layered picture, labeled

<div class="diagram-figure is-portrait">
<img class="diagram" src="/assets/diagram-shipped-vs-proposed.svg" width="640" height="552" loading="lazy" decoding="async" alt="Vertical stack. Agent and Judgment Planner are product; Judgment Graph and Composite Judgment are proposed; the Judgment Pack single-decision document and its four conformance classes are the shipped standard; a runtime validates and evaluates.">
<p class="diagram-caption">Only the green core — the Judgment Pack document and its conformance classes — is the standard. Everything else is proposed, runtime, or product.</p>
</div>

| Layer in the common picture | What it really is | Status | Where it lives |
| --- | --- | --- | --- |
| Agent | The caller. Any AI system that uses a pack. | Out of scope | Product |
| Judgment Planner | Selects which pack(s) apply to a context. | Proposed / likely product | [RFC 0004](../../rfcs/0004-planner-interface.md) |
| Judgment Graph | A *format* for composing several packs. | Proposed | [RFC 0002](../../rfcs/0002-judgment-graph.md) |
| Judgment Pack | A single-decision document. | **Shipped** | The specification |
| Evidence (sources) | What a pack references; supplied by any system. | Reference **shipped**; integration out of scope | [RFC 0003](../../rfcs/0003-evidence-reference.md) |
| Evidence acquisition | Getting the bytes, and showing they were not invented. | Out of scope; open research, no RFC proposes it | [Research](#where-those-inputs-come-from-is-a-separate-open-question) |
| Runtime | Validates documents; may also evaluate. | Validator shipped; evaluator conformance class **shipped** in Core `0.2.0-draft` §3.4, and the reference runtime now states a claim of it in its own repository | Reference runtime, [RFC 0006](../../rfcs/0006-evaluator-conformance.md) |
| Composite Judgment | The aggregated result of evaluating a graph. | Proposed | [RFC 0002](../../rfcs/0002-judgment-graph.md) |
| Discovery / registry | Finding and selecting packs across catalogs. | Proposed (format) / product (service) | [RFC 0001](../../rfcs/0001-pack-manifest.md), [RFC 0005](../../rfcs/0005-pack-discovery.md) |

The **Judgment Pack** row is the standard, and the Runtime row is now half of one: the *meaning* of an
evaluation is specified, while the engine that performs it is not. Everything else above and below is a
proposal, a runtime behavior, or product territory.

## How to read the picture

<div class="diagram-figure is-standard">
<img class="diagram" src="/assets/diagram-three-properties.svg" width="640" height="372" loading="lazy" decoding="async" alt="The neutral judgment-pack-spec is the standard. A reference runtime, independent implementations, and products consume it as peers, and the reference runtime feeds a conformance corpus back to the specification.">
<p class="diagram-caption">A format goes to the specification, an engine to the runtime, a service to a product — and no consumer owns the standard.</p>
</div>

Three tests decide where each part belongs, and they are worth stating plainly:

- A **format** that two independent tools must agree on is a candidate for the specification — as an
  optional profile, only after two implementations prove it. Pack manifest, graph composition, and
  evidence reference are formats.
- An **algorithm or engine** — how a pack is validated, or how a graph is evaluated into a composite
  result — belongs to a runtime. That migration has already happened once, in the direction this test
  predicts: the *meaning* of an evaluation is now a normative claim of the document, in Core §§7–8 for
  the evaluator conformance class, with its result pinned as the §8.3 disposition — while the engine
  that computes it still belongs to a runtime. That is the split the Runtime row above states.
- A **hosted service or business logic** — a running registry, a planner that weighs cost, latency,
  and tenant context — is product. Standardizing it would re-couple a neutral format to one vendor.

## Knowledge is an input, not a parent

A knowledge graph, a database, an API, or a document store answers *what is known*. A pack declares
*which decision is being made, when it applies, which evidence changes it, and when a human must
take over*. Evidence sources feed a pack; they do not sit above it.

<div class="diagram-figure is-wide">
<img class="diagram" src="/assets/diagram-knowledge-input.svg" width="720" height="268" loading="lazy" decoding="async" alt="Evidence sources such as a knowledge graph, SQL, APIs, and documents feed a Judgment Pack, which declares which decision applies and when to escalate, and produces a decision with rationale.">
<p class="diagram-caption">Evidence sources answer “what is known.” The pack decides which of it matters — so knowledge feeds the pack rather than sitting above it.</p>
</div>

The [Why Judgment Pack?](../why.md) page develops this distinction, and the
[comparison](../concepts/comparison.md) page contrasts the format with DMN, policy engines, and rule
engines.

### Where those inputs come from is a separate, open question

A pack says which evidence matters. It says nothing about whether the bytes an agent presents as
that evidence are the bytes a source actually returned — and an agent that can assert a fact can
also invent one. That is a real gap, it is deliberately **outside this specification**, and the
project is researching it in the open rather than specifying it early:
[judgment-pack-evaluator-experiments](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments)
holds the studies and reference-adjacent prototypes, and
[judgment-pack-gateway](https://github.com/Judgment-Pack/judgment-pack-gateway) holds the later hosted
reference shape. They are distinct artifacts, not one interoperable interface:

- The inline [acquisition proxy](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/acquisition-proxy)
  wraps a downstream MCP server and issues version-1 HMAC receipts with retained,
  content-addressed results. Verification needs the same secret that can mint a receipt, and replay
  and tail rollback remain outside what the store can prove about itself.
- The gateway's incompatible version-2 format signs receipts and session seals with Ed25519. A
  verifier with a separately pinned public key can check a store against the registry obtained from
  the key holder without gaining the power to forge. Version 2 deliberately rejects version 1.
- A portable [derivation rule](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/derivation-rule)
  maps attested bytes into facts and evidence availability, and the experimental
  [admission gate](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/fabrication-gate)
  passes only that deterministic result to evaluation. The gateway alone does not remove
  caller-supplied facts, and the JPS reference runtime consumes none of these formats today.

Its ceiling is stated up front and is worth repeating here, because it is the kind of claim that
inflates in retelling: the mechanism proves **byte-lineage, not truth**. It establishes what a
judgment was computed over. It establishes nothing about whether those bytes are accurate, whether
the named source produced them, or whether acting on the result is authorized — the same three
things [conformance never establishes](../../spec/judgment-pack-core.md). Nothing in this research
line is part of JPS, and no RFC proposes the acquisition, receipt, seal, or admission formats as JPS
today. The derivation-rule evidence is also bounded: a later probe showed that the set of fields a
short-circuiting rule happened to read is not necessarily a sufficient policy basis. No portable
repair has been selected.

## The point of labeling

A standard earns trust by shipping a small, testable core and being honest about what is still a
proposal. Presenting the full layered stack as "the architecture" would over-claim and would blur
the line between the neutral specification and the products that implement it. The proposals that
make the vision concrete are tracked openly as [RFCs](../../rfcs/README.md); the
[FAQ](../../FAQ.md) answers the questions this picture usually raises.

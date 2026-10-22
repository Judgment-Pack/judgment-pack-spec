# RFC 0022: Reusable subgraphs contract — explicit encapsulation and reference binding

- Status: Draft
- Type: Exploratory (a cross-project exploratory record — the reference runtime's graph engine,
  the Desk's graph canvas, and authoring tools; outside the specification)
- Created: 2026-10-15
- Issue: [#129](https://github.com/Judgment-Pack/judgment-pack-spec/issues/129)

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **Scope note, load-bearing.** Nothing this record proposes lands in JPS Core, an existing profile,
> or an evaluator conformance class. It is recorded under
> [RFC 0000's](0000-rfc-process.md) cross-project exploratory provision. This record specifically
> speaks to Issue [#129](https://github.com/Judgment-Pack/judgment-pack-spec/issues/129) ("define a
> reusable subgraph contract before adding nested graph nodes"). The decision on the reusable
> subgraph contract itself belongs to the maintainer and is being made alongside graph work in
> progress in the reference runtime and the Desk; this proposal serves as structured input and
> exploratory design analysis for that decision rather than a change that lands on its own.
> Acceptance endorses this design record as written and confers no authority over each owning
> repository, which makes its own adoption decision by its own process.
>
> **Drafting assistance.** Drafted with assistance from Anthropic Claude (model `claude-3-7-sonnet`,
> 2026-10-15), per the [interim review regime](../GOVERNANCE.md#interim-review-regime).

## Summary

This record outlines candidate design requirements and interface boundaries for **reusable
subgraphs** in Judgment Pack composition.

[RFC 0002](0002-judgment-graph.md) established a candidate format for composing several Judgment
Packs into a flat directed acyclic graph (DAG) along the dataflow seam (outcome-as-fact and
evidence-availability edges). The reference runtime implemented this flat model across several
architectural decision records (ADR-0015 through ADR-0032). As composite workflows scale, authors
encounter recurring multi-node patterns — such as sanctions triage, vendor standing, or entity
compliance screening — that must be applied across multiple parent graphs or instantiated more
than once within a single parent graph.

The central problem this record addresses is how to achieve modular composition without silently
treating detached copies as live references:

1. **Explicit Encapsulation**: A reusable subgraph declares formal input parameters with
   node-scoped destination mappings (`inputs`) and exposed decision outputs (`outputs`), preventing
   ambient state leakage across graph boundaries.
2. **Cryptographic Identity and Exact Pinning**: Live references bind the exact bytes actually
   loaded at rest via `sha256:` content digests (following [RFC 0001](0001-pack-manifest.md) and
   ADR-0030), ensuring that unreviewed drift cannot occur silently. Policy versions declare exact
   matching, and mismatches fail before evaluation.
3. **Injective Instance Addressing**: Disjoint address spaces separate local node identifiers from
   hierarchical instance paths, avoiding collisions and preserving error and trace attribution.
4. **Preservation of Core Semantics**: Handoff destinations configured in packs remain intact as
   display names per Core §6.7 and §8.3; a destinationless escalation request omits the target
   member; originating instance paths travel beside the disposition as provenance. Complete Core §8.3
   disposition objects are preserved at all leaf nodes and exported boundaries, with `state` strictly
   `"requested"` or `"none"`, never flattening kinds into outcome IDs.
5. **Clear Algorithm Boundaries**: Acyclicity requirements remain declarative per RFC 0002's
   format-only determination; candidate algorithms (such as Tarjan's SCC and topological sorting)
   and numerical limits (depth 8, node budget 256) are characterized as provisional runtime
   implementation choices with unambiguous accounting rules.

## Problem

A single Judgment Pack evaluates a single decision. In real-world compliance, procurement, and
underwriting workflows, decisions compose into multi-tier structures. Under the flat graph model of
RFC 0002 and ADR-0015, every node references a single pack through a project-local identifier, and
every edge connects one node's outcome directly to another's fact or evidence input.

When authors encounter recurring sub-problems, the absence of an explicit subgraph contract creates
five distinct failure modes:

1. **Unprincipled copy-paste**: An author copies nodes and edges between graphs, manually renaming
   node identifiers. The copied fragment becomes detached. When regulatory policy updates, the
   copies diverge silently without detection or audit warning.
2. **Ambiguous inlining**: An authoring tool or macro processor expands a template graph into a
   parent flat graph, but presents the resulting document as if it were a live reference. Reviewers
   cannot determine whether an audit or review lock binds the canonical source document or an
   ad-hoc expansion.
3. **Ambient namespace leakage**: In an unencapsulated model, internal nodes of a subgraph might
   implicitly read ambient caller facts or inject intermediate outcomes into the parent scope,
   violating the isolation principle established in RFC 0002.
4. **Handoff destination conflation**: If a composite runtime rewrites a pack's configured escalation
   target to include the instance path (e.g., rewriting `"Sanctions Compliance Queue"` to
   `"vendor-check/ofac/Sanctions Compliance Queue"`), it corrupts the destination display name
   defined by Core §6.7, confusing downstream human routing systems. Furthermore, direct escalations
   lacking a configured target require clear omission handling.
5. **Disposition flattening**: Attempting to represent composite results by compressing result kinds
   (`not-applicable`, `unresolved`, `outcome`) into a single string field, or using invalid states
   such as `not-requested` instead of Core's `none`, destroys Core §8.3 portable disposition
   semantics.

## Evidence

The standing evidence for graph composition is recorded in RFC 0002:

- Study 003 (2026-07) identified cross-decision references in public policy corpora.
- The reference runtime prototype (ADR-0015, 2026-07-29) demonstrated flat dataflow composition
  behind an experimental surface, since released and expanded across eight decision records.
- Study 004 (2026-07-30) tested the composition grammar and measured that within-policy residue
  was effect- or entitlement-shaped rather than dataflow-shaped, leading the maintainer to scope
  composition explicitly to the dataflow seam (one decision's outcome as another's input).

What the repository currently has:

- A flat composition format where nodes reference packs only, and no graph nesting exists.
- An optional reviewed-set lock (`jpack.lock.json`, ADR-0019) that binds pack documents to exact
  byte digests.
- Document digest binding for matrix runs and validations (ADR-0030).
- Node evaluation traces on request (ADR-0031).
- Handoff target assertions in graph test rows (ADR-0032).

**The unmet evidence bar.** This record is an exploratory proposal addressing Issue #129. It
carries **no independent implementations** and no conformance corpus. Neither the reference runtime
nor the Desk currently implements nested graph nodes. This record provides design analysis,
structural contracts, and counterexample hypotheses to guide experimental implementations.

## Specification (The Proposed Contract)

### 1. Distinction Between Flat Expansion and Live Subgraphs

To eliminate ambiguity between copied fragments and referenced components, the contract defines
two strictly separate mechanisms:

- **Flat Expansion (Import / Macro)**: A pre-evaluation, build-time transformation that reads a
  template graph and inlines its nodes and edges directly into the parent graph's flat structure,
  prefixing node identifiers to prevent collisions. Once expanded, the parent graph is a standard
  flat graph. It carries no live reference or cryptographic binding to the source template; its
  provenance is that of an authoring transformation.
- **Live Reusable Subgraph Node**: A first-class composite node in the parent graph that references
  an external graph document by identity and exact loaded byte digest. The runtime treats the
  subgraph as an encapsulated decision boundary with declared interfaces.

Tools MUST NOT present a flat expansion as a live reference, and MUST NOT permit a live reference
to decouple silently from its declared digest.

### 2. Interface Boundary: Explicit Inputs and Outputs

A reusable subgraph is an encapsulated composite decision unit. It declares an explicit interface
contract:

```json
{
  "inputs": {
    "facts": {
      "<external-fact-pointer>": {
        "node": "<internal-node-id>",
        "pointer": "<internal-fact-pointer>"
      }
    },
    "evidence": {
      "<external-requirement-id>": {
        "node": "<internal-node-id>",
        "requirementId": "<internal-requirement-id>"
      }
    }
  },
  "outputs": {
    "<exposed-output-name>": {
      "node": "<internal-node-id>",
      "description": "<explanatory text>"
    }
  },
  "result": "<internal-node-id>"
}
```

#### Dataflow Edge Schema and Reserved Caller Identity

In addition to node definitions, graph documents define dataflow edges connecting caller inputs and
node outcomes to downstream nodes.

To prevent collision or semantic ambiguity between caller-provided inputs and internal node feeds, the
identifier `"caller"` is **reserved** as an immutable, special-purpose source ID representing the
parent evaluation context:

- No node within any graph (root or subgraph) may declare the identifier `"caller"`.
- Static validation MUST refuse any graph declaring a node with `id: "caller"` or `"node": "caller"`.

Dataflow edges encompass four distinct varieties:

1. **Caller-to-Node Fact Feed**: An edge where `from: "caller"` maps a caller-supplied fact path
   (`fact`) to a designated target node (`to`) and its input fact pointer (`input` or `fact`).
2. **Caller-to-Node Evidence Feed**: An edge where `from: "caller"` maps a caller-supplied evidence item
   (`evidence`) to a designated target node (`to`) and its requirement ID (`requirementId`).
3. **Node-to-Node Outcome-as-Fact Feed**: An edge where `from: "<upstream-node-id>"` feeds an upstream
   node's determined outcome to a downstream node's RFC 6901 fact pointer (`fact`).
4. **Node-to-Node Evidence Availability Feed**: An edge where `from: "<upstream-node-id>"` contributes
   an upstream node's availability status to a downstream node's evidence requirement (`requirementId` or `evidence`),
   with optional `onUnresolved` (`unknown` by default, or `absent` if declared).

##### Outcome Feed Value Semantics and Missing-Input Fallthrough

- **Determined Outcome**: When the upstream node evaluates to a determined outcome (`"kind": "outcome"`),
  its `outcomeId` string is written directly as the value at the downstream node's target fact pointer.
- **Non-Determined Outcome**: When the upstream node evaluates to `"kind": "unresolved"` (or produces
  no outcome), it injects no fact into the target pointer, leaving the target pointer absent.
- **Downstream Evaluation Under Core §7 and §8**:
  - Under Core §7, reading an absent fact pointer evaluates to `unknown`.
  - Under Core §8.1 step 4, a condition (such as an `all` or `equals` condition) referencing an absent
    pointer evaluates to `unknown`.
  - If `onUnknown` is `"ignore"` (or omitted), Core §8.1 step 5 skips the rule.
  - If no other rule, exception, or fallback outcome matches, evaluation proceeds to **Core §8 step 10**,
    yielding:
    ```json
    {
      "kind": "unresolved",
      "reasons": ["no-match"],
      "handoff": {
        "state": "none"
      }
    }
    ```
    rather than `["unknown"]`.

#### Binding Carrier Rules

1. **Node-Scoped Mappings**: An external fact or evidence contribution is explicitly mapped to a
   specific internal node and a specific destination pointer or requirement ID. Requirement IDs
   are pack-local; explicit mapping prevents collisions when two internal packs declare identical
   requirement IDs for different evidentiary purposes.
2. **Isolation and Missing Inputs**: Facts not declared in `inputs.facts` are unreachable inside the
   subgraph. If an external fact mapped to an internal pointer is not supplied by the caller or
   upstream edge, that pointer is absent at the target node (which Core §7 reads as `unknown`). If
   an external evidence requirement mapped to an internal requirement is not supplied, it is absent
   from the target pack's evidence availability document (which Core §8.2 reads as `unknown`). When a
   rule condition evaluates to `unknown` and `onUnknown: "ignore"` skips the rule without a matching
   fallback, Core §8 step 10 evaluates to `{"kind": "unresolved", "reasons": ["no-match"], "handoff": {"state": "none"}}`.
3. **Collision Refusal and Overlapping Pointers**: Following RFC 0002 and ADR-0015, if an incoming
   feed targets a fact pointer or evidence requirement that collides with caller-supplied data or
   another edge targeting the same internal node, the graph is refused before evaluation begins.
   Furthermore, two feeds targeting the same internal node MUST NOT specify RFC 6901 pointers that
   overlap once decoded (where one pointer's decoded token sequence is a prefix of another, such as
   `/entity` and `/entity/name`). Overlapping decoded pointers are refused during static validation.
4. **Fact Feeds vs. Evidence Feeds**: The `onUnresolved` switch applies strictly to **evidence
   availability feeds** (contributing `unknown` by default, or `absent` if declared). Outgoing
   **fact feeds** do not use `onUnresolved`: an upstream node that produced no outcome simply
   injects no fact into the target pointer, leaving the pointer absent, triggering Core §7 unknown
   reading and Core §8 step 10 `no-match` fallthrough downstream.

### 3. Reference Resolution, Identity, and Digest Pinning

A parent graph references a reusable subgraph as a node:

```json
{
  "nodes": {
    "vendor-sanctions": {
      "subgraph": "sanctions-screening",
      "version": "0.1.0",
      "digest": "sha256:47e7c8483de7dc1f8d764c50b1d83c3048bf230e4c5d5ddb228ebcb965d85406",
      "title": "Primary Vendor Sanctions Screening"
    }
  }
}
```

#### Resolution and Binding Rules

- **Project-Local Resolution**: In a project configuration (`jpack.json`), a `graphs` object maps
  local graph names to filesystem paths. A node specifying `"subgraph": "sanctions-screening"`
  resolves through this table.
- **Exact Loaded Bytes Digest**: The `digest` member carries the SHA-256 hash computed over the
  **exact bytes actually loaded at rest** (following [RFC 0001](0001-pack-manifest.md) and
  ADR-0030), without canonicalization. If the loaded file's bytes do not match the declared digest,
  validation fails before evaluation.
- **Policy Version Matching**: When a node declares `"version": "0.1.0"`, the loaded subgraph
  document's declared `"version"` string MUST match exactly. If the bytes match the digest but the
  loaded graph document declares a different policy version (e.g. `"0.2.0"`), the runtime MUST
  refuse the graph before evaluation with a reference-version-mismatch error.
- **Reviewed-Set Lock Binding (`jpack.lock.json`)**: In the reference runtime, `jpack.lock.json`
  (ADR-0019) binds loaded project documents to their evaluated byte digests. When a parent graph is
  evaluated in a *decided* (production) surface, the review lock MUST transitively cover the parent
  graph document, every referenced subgraph document, and all underlying packs. In *rehearsal*
  surfaces, the lock remains optional, allowing rapid iterative editing while visibly flagging
  unlocked runs.
- **Lock Disclaimers**: Generating a lock file approves nothing. A digest check establishes byte
  identity; it does not attest to reviewer authority, regulatory correctness, or policy freshness.
- **Snapshot Consistency**: When a parent graph instantiates the same subgraph multiple times (e.g.,
  `buyer-screening` and `seller-screening`), the runtime MUST evaluate all instances against a single
  immutable snapshot read of the document bytes.

### 4. Address Grammar and Version Negotiation

#### Local Identifiers vs. Instance Addresses

- **Local Node Identifiers**: Local node IDs inside any graph (parent or subgraph) MUST conform to
  the established runtime node grammar:
  ```regex
  ^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$
  ```
  Local IDs consist of lowercase alphanumeric segments separated by single hyphens (no dots, no
  underscores).

- **Instance Addresses**: When identifying a node across an instance boundary (in validation
  diagnostics, traces, or provenance fields), the address is a distinct type formatted as an
  injective slash-separated path:
  ```
  /instance-id/internal-node-id
  ```
  Because local IDs forbid slashes, slash-separated instance paths are disjoint from local node IDs
  and prevent ambiguous parsing.

#### Version Negotiation

- The graph document schema carries a required `formatVersion` string (e.g. `"0.2.0-draft"`).
- A reader that does not support nested subgraph nodes MUST refuse documents declaring an
  unsupported `formatVersion` or containing the `"subgraph"` member on a node.
- `formatVersion` (governing the schema grammar of the graph) is strictly independent of `version`
  (governing the revision history of the specific graph policy).

### 5. Acyclicity, Traversal Bounds, and Candidate Algorithms

#### Declarative Invariant

The composition of graphs, subgraphs, and dataflow edges MUST form a strict Directed Acyclic Graph
(DAG). Both of the following MUST hold:

1. **Subgraph Reference Acyclicity**: No graph may reference itself directly or transitively
   (`A -> B -> A` is invalid).
2. **Dataflow Acyclicity**: Across all expanded scopes, no directed cycle of outcome-as-fact or
   evidence-availability feeds may exist.

#### Candidate Algorithms vs. Format Specification

In keeping with RFC 0002's retained determination that the format defines no algorithm:

- Algorithms such as Tarjan's strongly connected components (SCC) for cycle detection or Kahn's
  algorithm for topological sorting are **candidate runtime implementation choices**.
- Conformance requires that any cyclic composition is refused before evaluation; an implementation
  is free to choose its verification algorithm.

#### Unambiguous Bounds and Accounting Rules

To prevent resource exhaustion (graph bomb attacks or combinatorial expansion):

- **Nesting Depth Accounting**:
  - The root parent graph is at depth **0**.
  - A subgraph directly referenced by a node in the root graph evaluates at depth **1**.
  - Each nested subgraph reference edge increments the depth by 1.
  - The provisional limit is a maximum depth of **8** (depths 0 through 8 inclusive are valid; a
    subgraph at depth 9 is refused before evaluation).

- **Node Budget Accounting**:
  - The counted units are **evaluated leaf pack node instances**.
  - Composite wrapper nodes (subgraph reference nodes) are structural boundaries and do NOT count
    toward the budget.
  - Repeated instances: If a subgraph containing `k` leaf pack nodes is instantiated `m` times, it
    contributes `k * m` leaf pack instances toward the budget.
  - The provisional budget is a maximum of **256** total evaluated leaf pack node instances
    (inclusive). An expanded graph with 256 leaf pack instances is admitted; 257 is refused before
    evaluation.

- Per Core §10, these limits are implementation-defined limits rather than immutable JPS
  conformance requirements. Traversal bounds are enforced during static validation before pack
  evaluation.

### 6. Execution Models and the Equivalence Conjecture

Two primary execution models exist for evaluating reusable subgraphs:

1. **Hierarchical Evaluation**: The runtime evaluates parent nodes in topological order. Upon
   reaching a subgraph node, it evaluates the subgraph's internal nodes according to the subgraph's
   local topological order, resolves its exposed outputs, and resumes parent evaluation.
2. **Flattened Topological Execution**: The runtime elaborates the entire composition into a single
   flattened DAG with hierarchical instance addresses, sorting all nodes into a unified global order.

#### The Equivalence Conjecture

Under pure dataflow (where nodes have no side effects, global state, or ambient mutation), and where
all leaf nodes evaluate to valid dispositions, hierarchical evaluation and flattened topological
execution produce identical final disposition assignments for all exposed nodes.

#### Why Equivalence is Not a Settled Theorem for Failures

Equivalence does not automatically hold when evaluations fail, request handoffs, or record traces:

- Suppose parent node `z` feeds one input of subgraph `a`. Hierarchical execution waits for `z` to
  complete before evaluating any node in `a`.
- A flattened global scheduler might evaluate an independent node `a.x` inside subgraph `a` before
  evaluating `z`.
- If both `z` and `a.x` encounter evaluation errors (Core §8.4), immediate abort without a
  synchronized barrier could report different error classes depending on scheduling order.
- Therefore, equivalence of failure states, handoff sets, and trace order requires explicit error
  precedence rules, synchronized evaluation barriers, or deterministic tie-breaking. Until an
  elaboration rule is formally proven across these edge conditions, equivalence is documented as a
  **design objective and conjecture**, not an established theorem.

### 7. Dispositions, Evaluator Errors, and Handoff Provenance

#### Preservation of Core §8.3 Dispositions

At leaf nodes and exported output boundaries, dispositions MUST be complete, valid Core §8.3
objects:

- `kind`: Exactly one of `"outcome"`, `"not-applicable"`, or `"unresolved"`.
- `outcomeId`: Present if and only if `kind` is `"outcome"`, naming a declared outcome of the pack.
- `reasons`: Sorted array of Core reason identifiers. Empty if and only if `kind` is `"outcome"`.
- `handoff`: Complete object carrying `state` (`"requested"` or `"none"`).
- `handoff.triggeredBy`: Present if and only if `state` is `"requested"`. When `state` is `"none"`,
  `triggeredBy` MUST be absent.
- Kinds MUST NOT be mapped to `outcomeId` or flattened into string fields.

#### Core §8.4 Evaluator Errors vs. Undefined Comparisons

- Evaluator errors are defined strictly by the **four Core §8.4 error classes**, evaluated in fixed
  precedence order:
  1. `pack-not-conformant`
  2. `malformed-input`
  3. `unsupported-required-extension`
  4. `resource-exhaustion`
- An authentic Core §8.4 error encountered in any internal pack terminates evaluation immediately,
  reporting the error class without emitting a forged disposition.
- Per Core §7.4, an undefined ordered comparison (e.g. comparing a boolean against a number) is NOT
  an evaluation error; it produces `unknown` and resolves normally under the pack's `onUnknown` rule.

#### Handoff Provenance and Destinationless Requests

- Per Core §6.7 and §8.3, a pack's configured escalation target (e.g. `"Sanctions Compliance Officer"`)
  is a display name for a role or queue, not a network address. The disposition does not echo or
  rewrite the target.
- If an internal node requests a handoff with a configured target, that target is preserved
  unaltered in the result envelope.
- If an escalation occurs without a configured target (such as a direct exception request per Core
  §8.1), the envelope's handoff entry **omits the `target` member** (it is absent, not `null`).
- The originating instance and node are reported **separately** beside it:
```json
{
  "handoffs": [
      {
        "originatingNode": "/contractor-sanctions/ofac-check",
        "target": {
          "kind": "human-role",
          "name": "Sanctions Compliance Officer"
        },
        "triggeredBy": ["missing-required-evidence"]
      },
    {
      "originatingNode": "/contractor-sanctions/pep-check",
      "triggeredBy": ["exception-escalation"]
    }
  ]
}
```

- Operational routing, message queues, and delivery mechanisms are explicitly outside the scope of
  this contract.

### 8. Traces, Observability, and Verifier Boundaries

#### Provenance Claim

Nested evaluation traces record the parent invocation, bound inputs, loaded document digests, and
per-node execution traces transported per ADR-0031. This provides structured provenance, not an
unconditional guarantee of "complete auditability."

#### Verifier-Held Artifacts and Trust Assumptions

An independent external verifier reproducing a composite run MUST hold:

1. The exact bytes actually loaded for the parent graph document and all referenced subgraph
   documents.
2. The exact bytes actually loaded for all referenced pack documents.
3. The exact input facts document and evidence-availability document.
4. The project configuration (`jpack.json`) and review lock (`jpack.lock.json`, if evaluating under
   a decided regime).

Canonical serialization (RFC 8785) is used strictly when comparing Core §8.3 dispositions
byte-for-byte; it is NEVER used for document identity or hash verification of graph or pack files.

Trust assumptions:

- The verifier trusts that the execution engine satisfies Core §3.4 evaluator conformance.
- Content digests attest that bytes have not changed; they do not attest that the policy within
  those bytes is lawful, authorized, or up to date.
- Minimum trace retention and formal verification procedures remain open questions under Core §13.

### 9. Complete Executable Examples

#### 1. Reusable Subgraph Document (`graphs/sanctions-screening.graph.json`)

```json
{
  "formatVersion": "0.2.0-draft",
  "id": "https://example.com/graphs/sanctions-screening",
  "version": "0.1.0",
  "title": "Sanctions screening subgraph",
  "inputs": {
    "facts": {
      "/entity/name": {
        "node": "ofac-check",
        "pointer": "/subject/legal-name"
      },
      "/entity/country": {
        "node": "pep-check",
        "pointer": "/subject/jurisdiction"
      }
    },
    "evidence": {
      "clearance-cert": {
        "node": "ofac-check",
        "requirementId": "ofac-clearance-document"
      }
    }
  },
  "nodes": {
    "ofac-check": {
      "pack": "ofac-screening",
      "title": "OFAC Sanctions List Screening"
    },
    "pep-check": {
      "pack": "pep-screening",
      "title": "Politically Exposed Persons Screening"
    },
    "composite-risk": {
      "pack": "risk-aggregator",
      "title": "Combined Screening Risk Determination"
    }
  },
  "edges": [
    {
      "from": "ofac-check",
      "to": "composite-risk",
      "fact": "/screening/ofac-verdict"
    },
    {
      "from": "pep-check",
      "to": "composite-risk",
      "fact": "/screening/pep-verdict"
    }
  ],
  "outputs": {
    "screening-verdict": {
      "node": "composite-risk",
      "description": "Composite sanctions and PEP clearance outcome"
    }
  },
  "result": "composite-risk"
}
```
*Exact SHA-256 byte digest:* `sha256:47e7c8483de7dc1f8d764c50b1d83c3048bf230e4c5d5ddb228ebcb965d85406` (computed over the exact 1,325 UTF-8 bytes of the
JSON text shown above, without a trailing newline; if stored with a trailing newline, the digest is
`sha256:63c895d2e5416aed8ea45abc0b56b3bace514e03cd72e2b9289ea9d1b27bc622`).

#### 2. Caller Input Documents

**Caller facts (`caller-facts.json`):**
```json
{
  "procurement": {
    "vendor": {
      "legal-name": "Acme Global Corp",
      "jurisdiction": "US"
    },
    "contractor": {
      "legal-name": "Prohibited Trade Ltd",
      "jurisdiction": "IR"
    }
  }
}
```

**Caller evidence availability (`caller-evidence.json`):**
```json
{
  "vendor-ofac-cert": "present",
  "contractor-ofac-cert": "absent"
}
```

#### 3. Parent Graph Document (`graphs/procurement-triage.graph.json`)

```json
{
  "formatVersion": "0.2.0-draft",
  "id": "https://example.com/graphs/procurement-triage",
  "version": "0.1.0",
  "title": "Procurement Vendor and Contractor Screening Triage",
  "nodes": {
    "vendor-sanctions": {
      "subgraph": "sanctions-screening",
      "version": "0.1.0",
      "digest": "sha256:47e7c8483de7dc1f8d764c50b1d83c3048bf230e4c5d5ddb228ebcb965d85406",
      "title": "Vendor Sanctions Screening"
    },
    "contractor-sanctions": {
      "subgraph": "sanctions-screening",
      "version": "0.1.0",
      "digest": "sha256:47e7c8483de7dc1f8d764c50b1d83c3048bf230e4c5d5ddb228ebcb965d85406",
      "title": "Subcontractor Sanctions Screening"
    },
    "procurement-approval": {
      "pack": "procurement-decision",
      "title": "Final Procurement Approval"
    }
  },
  "edges": [
    {
      "from": "caller",
      "fact": "/procurement/vendor/legal-name",
      "to": "vendor-sanctions",
      "input": "/entity/name"
    },
    {
      "from": "caller",
      "fact": "/procurement/vendor/jurisdiction",
      "to": "vendor-sanctions",
      "input": "/entity/country"
    },
    {
      "from": "caller",
      "evidence": "vendor-ofac-cert",
      "to": "vendor-sanctions",
      "requirementId": "clearance-cert"
    },
    {
      "from": "caller",
      "fact": "/procurement/contractor/legal-name",
      "to": "contractor-sanctions",
      "input": "/entity/name"
    },
    {
      "from": "caller",
      "fact": "/procurement/contractor/jurisdiction",
      "to": "contractor-sanctions",
      "input": "/entity/country"
    },
    {
      "from": "caller",
      "evidence": "contractor-ofac-cert",
      "to": "contractor-sanctions",
      "requirementId": "clearance-cert"
    },
    {
      "from": "vendor-sanctions",
      "output": "screening-verdict",
      "to": "procurement-approval",
      "fact": "/screening/vendor-cleared"
    },
    {
      "from": "contractor-sanctions",
      "output": "screening-verdict",
      "to": "procurement-approval",
      "fact": "/screening/contractor-cleared"
    }
  ],
  "result": "procurement-approval"
}
```

#### 4. Leaf Pack Definitions

**OFAC Screening Pack (`packs/ofac-screening.json`):**
```json
{
  "specVersion": "0.2.0-draft",
  "id": "https://example.com/packs/ofac-screening",
  "version": "0.1.0",
  "title": "OFAC Sanctions List Screening",
  "decision": {
    "intent": "Determine OFAC watchlist clearance based on certificate evidence.",
    "question": "Is the subject cleared of OFAC sanctions?"
  },
  "evidenceRequirements": [
    {
      "id": "ofac-clearance-document",
      "description": "OFAC Clearance Certificate",
      "kind": "document",
      "required": true
    }
  ],
  "outcomes": [
    { "id": "cleared", "label": "Cleared" },
    { "id": "flagged", "label": "Flagged on Watchlist" }
  ],
  "rules": [
    {
      "id": "rule-cleared",
      "description": "Clear when valid non-empty legal name is present.",
      "when": {
        "op": "fact",
        "path": "/subject/legal-name",
        "operator": "not-equals",
        "value": ""
      },
      "outcome": "cleared",
      "onUnknown": "ignore"
    }
  ],
  "escalation": {
    "target": {
      "kind": "human-role",
      "name": "Sanctions Compliance Officer"
    },
    "triggers": ["missing-required-evidence"]
  }
}
```

**PEP Screening Pack (`packs/pep-screening.json`):**
```json
{
  "specVersion": "0.2.0-draft",
  "id": "https://example.com/packs/pep-screening",
  "version": "0.1.0",
  "title": "Politically Exposed Persons Screening",
  "decision": {
    "intent": "Evaluate jurisdiction risk and escalate sanctioned territory operations.",
    "question": "Is the subject jurisdiction compliant?"
  },
  "outcomes": [
    { "id": "cleared", "label": "Cleared" },
    { "id": "pep-flagged", "label": "PEP Escalation Required" }
  ],
  "rules": [
    {
      "id": "rule-domestic",
      "description": "Domestic US jurisdiction is cleared.",
      "when": {
        "op": "fact",
        "path": "/subject/jurisdiction",
        "operator": "equals",
        "value": "US"
      },
      "outcome": "cleared",
      "onUnknown": "ignore"
    }
  ],
  "exceptions": [
    {
      "id": "exc-sanctioned-country",
      "description": "Sanctioned jurisdiction triggers direct escalation without configured target.",
      "when": {
        "op": "fact",
        "path": "/subject/jurisdiction",
        "operator": "equals",
        "value": "IR"
      },
      "effect": "escalate",
      "onUnknown": "ignore"
    }
  ]
}
```

**Risk Aggregator Pack (`packs/risk-aggregator.json`):**
```json
{
  "specVersion": "0.2.0-draft",
  "id": "https://example.com/packs/risk-aggregator",
  "version": "0.1.0",
  "title": "Combined Screening Risk Determination",
  "decision": {
    "intent": "Aggregate OFAC and PEP screening verdicts into a combined clearance.",
    "question": "Is the subject entity fully cleared?"
  },
  "outcomes": [
    { "id": "cleared", "label": "Cleared" },
    { "id": "rejected", "label": "Rejected" }
  ],
  "rules": [
    {
      "id": "rule-both-cleared",
      "description": "Cleared if both OFAC and PEP verdicts are cleared.",
      "when": {
        "op": "all",
        "conditions": [
          {
            "op": "fact",
            "path": "/screening/ofac-verdict",
            "operator": "equals",
            "value": "cleared"
          },
          {
            "op": "fact",
            "path": "/screening/pep-verdict",
            "operator": "equals",
            "value": "cleared"
          }
        ]
      },
      "outcome": "cleared",
      "onUnknown": "ignore"
    }
  ]
}
```

**Procurement Decision Pack (`packs/procurement-decision.json`):**
```json
{
  "specVersion": "0.2.0-draft",
  "id": "https://example.com/packs/procurement-decision",
  "version": "0.1.0",
  "title": "Final Procurement Approval",
  "decision": {
    "intent": "Approve procurement when both vendor and subcontractor are cleared.",
    "question": "Is the procurement contract approved?"
  },
  "outcomes": [
    { "id": "approved", "label": "Approved" },
    { "id": "rejected", "label": "Rejected" }
  ],
  "rules": [
    {
      "id": "rule-all-clear",
      "description": "Approve when both vendor and subcontractor have cleared screening.",
      "when": {
        "op": "all",
        "conditions": [
          {
            "op": "fact",
            "path": "/screening/vendor-cleared",
            "operator": "equals",
            "value": "cleared"
          },
          {
            "op": "fact",
            "path": "/screening/contractor-cleared",
            "operator": "equals",
            "value": "cleared"
          }
        ]
      },
      "outcome": "approved",
      "onUnknown": "ignore"
    }
  ]
}
```

#### 5. Project Configuration (`jpack.json`)

```json
{
  "formatVersion": "0.1.0",
  "packs": {
    "ofac-screening": { "path": "packs/ofac-screening.json" },
    "pep-screening": { "path": "packs/pep-screening.json" },
    "risk-aggregator": { "path": "packs/risk-aggregator.json" },
    "procurement-decision": { "path": "packs/procurement-decision.json" }
  },
  "graphs": {
    "sanctions-screening": { "path": "graphs/sanctions-screening.graph.json" },
    "procurement-triage": { "path": "graphs/procurement-triage.graph.json" }
  }
}
```

#### 6. Composite Result Envelope with Core Dispositions and Provenance

```json
{
  "formatVersion": "0.2.0-draft",
  "graphId": "https://example.com/graphs/procurement-triage",
  "headline": {
    "node": "procurement-approval",
    "disposition": {
      "kind": "unresolved",
      "reasons": ["no-match"],
      "handoff": {
        "state": "none"
      }
    }
  },
  "handoffs": [
    {
      "originatingNode": "/contractor-sanctions/ofac-check",
      "target": {
        "kind": "human-role",
        "name": "Sanctions Compliance Officer"
      },
      "triggeredBy": ["missing-required-evidence"]
    },
    {
      "originatingNode": "/contractor-sanctions/pep-check",
      "triggeredBy": ["exception-escalation"]
    }
  ],
  "nodes": {
    "vendor-sanctions": {
      "type": "subgraph",
      "graphId": "https://example.com/graphs/sanctions-screening",
      "digest": "sha256:47e7c8483de7dc1f8d764c50b1d83c3048bf230e4c5d5ddb228ebcb965d85406",
      "output": {
        "screening-verdict": {
          "kind": "outcome",
          "outcomeId": "cleared",
          "reasons": [],
          "handoff": {
            "state": "none"
          }
        }
      },
      "nodes": {
        "ofac-check": {
          "disposition": {
            "kind": "outcome",
            "outcomeId": "cleared",
            "reasons": [],
            "handoff": {
              "state": "none"
            }
          }
        },
        "pep-check": {
          "disposition": {
            "kind": "outcome",
            "outcomeId": "cleared",
            "reasons": [],
            "handoff": {
              "state": "none"
            }
          }
        },
        "composite-risk": {
          "disposition": {
            "kind": "outcome",
            "outcomeId": "cleared",
            "reasons": [],
            "handoff": {
              "state": "none"
            }
          }
        }
      }
    },
    "contractor-sanctions": {
      "type": "subgraph",
      "graphId": "https://example.com/graphs/sanctions-screening",
      "digest": "sha256:47e7c8483de7dc1f8d764c50b1d83c3048bf230e4c5d5ddb228ebcb965d85406",
      "output": {
        "screening-verdict": {
          "kind": "unresolved",
          "reasons": ["no-match"],
          "handoff": {
            "state": "none"
          }
        }
      },
      "nodes": {
        "ofac-check": {
          "disposition": {
            "kind": "unresolved",
            "reasons": ["missing-required-evidence"],
            "handoff": {
              "state": "requested",
              "triggeredBy": ["missing-required-evidence"]
            }
          }
        },
        "pep-check": {
          "disposition": {
            "kind": "unresolved",
            "reasons": ["exception-escalation"],
            "handoff": {
              "state": "requested",
              "triggeredBy": ["exception-escalation"]
            }
          }
        },
        "composite-risk": {
          "disposition": {
            "kind": "unresolved",
            "reasons": ["no-match"],
            "handoff": {
              "state": "none"
            }
          }
        }
      }
    },
    "procurement-approval": {
      "type": "pack",
      "disposition": {
        "kind": "unresolved",
        "reasons": ["no-match"],
        "handoff": {
          "state": "none"
        }
      }
    }
  }
}
```

#### 7. Negative Example: Reference-Version Mismatch Refusal

A parent graph node specifying an inconsistent version:
```json
{
  "nodes": {
    "vendor-sanctions": {
      "subgraph": "sanctions-screening",
      "version": "0.2.0",
      "digest": "sha256:47e7c8483de7dc1f8d764c50b1d83c3048bf230e4c5d5ddb228ebcb965d85406"
    }
  }
}
```
*Result:* Even though the loaded document matches the SHA-256 digest, the document declares
`"version": "0.1.0"`. The runtime refuses the graph before evaluation with diagnostic:
`JPS-GRAPH-REFERENCE-VERSION-MISMATCH: node 'vendor-sanctions' pins version '0.2.0' but loaded document declares '0.1.0'`.

## Alternatives

1. **JPS Core Specification-Defined Extension**: Define reusable subgraphs as a normative extension
   within Core JPS.
   *Why rejected*: Core JPS (§§3–8) governs the carrier, structural, and semantic evaluation of a
   single pack given single facts and evidence availability documents. Graph composition operates
   above the pack evaluation seam. Conflating composition with pack semantics would violate the
   separation of concerns established in RFC 0002.
2. **Candidate Profile Reading**: Standardize reusable subgraphs as an official optional JPS
   Profile (e.g. `org.judgmentpack.profile.subgraphs`).
   *Status*: Deferred. Per RFC 0000, establishing a profile requires two independent interoperating
   implementations and a shared conformance test suite. This exploratory record provides the design
   prerequisites for such work.
3. **Product-Only Desk Feature**: Treat subgraphs entirely as an authoring convenience within the
   Judgment Pack Desk, expanding all graphs to flat structures before serialization.
   *Why rejected*: If subgraphs exist only in authoring memory, independent backend engines cannot
   validate or execute modular graphs without proprietary flattening steps. An open interchange
   contract is required for cross-tool interoperability.
4. **Syntactic Macro Inlining Only**: Provide an external pre-processor command that copies and
   namespaces nodes at authoring time.
   *Why insufficient alone*: While flat expansion is supported, without a live reference contract,
   users cannot detect policy drift across shared decision modules.
5. **Ambient Global Fact Scoping**: Allow subgraphs to inherit caller facts automatically without
   explicit input declarations.
   *Why rejected*: Ambient scoping introduces hidden coupling, where an internal pack's conditions
   read parent facts that were never declared in the interface, destroying modular reasoning.
6. **Destination Rewriting**: Rewrite a pack's escalation target to embed the instance path.
   *Why rejected*: Core §6.7 and §8.3 require the escalation target to remain an intact display name.
   Originating node paths belong in envelope metadata, not in the destination.

## Compatibility

- **Additive Specification**: Existing flat graph documents remain completely valid.
- **Old-Reader Refusal**: The `formatVersion` gate ensures that older runtimes not supporting
  subgraphs fail fast with an explicit unsupported version error rather than silently ignoring
  subgraph nodes.
- **Specification Impact**: No normative effect on Core JPS. Core §§7–8 pack evaluation semantics
  are completely untouched.

## Security and privacy

- **Resource Limits**: Provisional limits on nesting depth (8) and node budget (256) prevent
  recursive denial-of-service ("graph bombs").
- **Untrusted Documents**: Subgraph documents loaded from project or external paths are untrusted
  inputs subject to schema validation, carrier parsing checks, and digest verification.
- **Integrity vs. Authority**: A valid digest match proves byte identity; it does not authorize the
  execution of an unreviewed policy.

## Conformance

When an experimental implementation is built, test vectors should exercise:

- Positive: Multi-instance subgraph resolution with distinct inputs and correct Core §8.3 outputs.
- Negative: Direct reference recursion (`A -> A`).
- Negative: Mutual reference recursion (`A -> B -> A`).
- Negative: Dataflow cycle across subgraph boundaries.
- Negative: Digest mismatch on loaded subgraph document.
- Negative: Policy version mismatch between node pin and loaded document.
- Negative: Overlapping decoded RFC 6901 pointers feeding the same target node.
- Negative: Colliding fact feed targeting an already-fed internal pointer.
- Negative: Nesting depth exceeding limit (depth 9).
- Negative: Total leaf pack node budget exceeding limit (257 nodes).

## Implementation

- **Status**: Exploratory draft. No implementation currently exists.
- **Two Plausible Independent Implementations**:
  1. *Reference Runtime* (`judgment-pack-runtime`): Engine implementation within `internal/graph/`,
     handling project-local resolution via `jpack.json`, digest pinning via `jpack.lock.json`,
     isolated instance evaluation scopes, and composite trace envelopes.
  2. *Judgment Pack Desk* (`judgment-pack-desk`): Visual authoring canvas and validator implementation
     in TypeScript/Node, supporting subgraph node creation, visual interface port mapping, and
     rehearsal evaluation.

- **Authoring Tools Ownership**: Command-line authoring utilities, build-time macro expansion, and
  template stamping belong to the Desk repository and external tooling, not to the specification.
- **Decision Ownership**: As noted in Issue [#129](https://github.com/Judgment-Pack/judgment-pack-spec/issues/129),
  the subgraph contract is decided by the maintainer in concert with ongoing runtime and Desk
  implementation work.

## Unresolved questions

1. **Parameter Remapping Schema**: Should `inputs.facts` support structural transformations (e.g.,
   re-rooting JSON objects), or should it remain strictly single-pointer mapping?
2. **Synchronization Barriers in Flattened Execution**: What specific synchronization barrier rule
   guarantees deterministic error reporting across concurrent or out-of-order flattened schedulers?
3. **Cross-Repository Subgraph Packaging**: How should shared subgraphs be packaged and distributed
   without relying on project-local filesystem paths? Does this require an extension to the pack
   manifest ([RFC 0001](0001-pack-manifest.md))?
4. **Dynamic Output Routing**: Can a subgraph conditionally select which output node surfaces based
   on rule firings, or must the output-to-node mapping remain strictly static?

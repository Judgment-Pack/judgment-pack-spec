# Frequently asked questions

This FAQ answers the questions most often raised about the Judgment Pack Specification (JPS),
including the hard architectural ones. Answers describe what the specification actually defines
today; where a capability is a proposal rather than shipped behavior, it is marked as such and
linked to the relevant [RFC](rfcs/README.md).

A recurring theme runs through the whole document: **JPS specifies a portable *document*, not an
engine.** A conforming pack is well-formed; it is never thereby true, authorized, safe, or fit for
use. Those are deliberately separate claims.

## General

**Q1. What is a Judgment Pack, in one sentence?** A portable, vendor-neutral JSON document that
declares a single decision — the evidence it requires, when it applies, its rules, exceptions,
possible outcomes, how uncertainty and escalation are handled, and where its claims came from — so
the reasoning can be inspected, tested, versioned, and moved between tools.

**Q2. What problem does it actually solve?** Coding agents work because their environment can already
judge their output — compilers, tests, CI. Most business agents have no such harness. A pack makes
the judgment behind a business decision explicit enough to test, the way a test suite makes "correct
code" explicit. See [Why Judgment Pack?](docs/why.md).

**Q3. Is JPS a standard yet?** No. It is a research preview at `0.1.0-draft` with no compatibility
guarantee; any `0.x` release may change incompatibly.

**Q4. Who is it for?** Tool and runtime implementers; standards and architecture reviewers;
enterprise architects evaluating governable AI decisioning; AI researchers studying testable
judgment; and domain experts who author packs.

**Q5. What is the one thing to understand about scope?** It specifies a document, not an engine.
Conformance means a document agrees with a contract — never that the pack is true, authorized, safe,
or fit for use.

## Architecture

**Q6. What does the specification define today?** Three document-conformance classes for a single
decision: carrier (valid JSON and encoding), structural (the schema), and semantic (local references
and cross-field rules). Nothing else is normative. See the
[core specification](spec/judgment-pack-core.md).

**Q7. Where do "Judgment Graph", "Planner", "Runtime", and "Composite Judgment" fit?** Nowhere in the
specification — they appear nowhere in it. The graph and composite result are proposals; the planner
is product; the runtime is a separate implementation. The
[architecture vision](docs/architecture/vision.md) shows how they would relate, clearly labeled and
non-normative.

**Q8. Why isn't the full layered architecture in the specification?** Because a standard earns trust
by standardizing only what independent tools must agree on, and only after two implementations prove
it. A layer with no format and no second implementation is a roadmap item, not a specification.

**Q9. Why split the specification, runtime, and products apart?** Authority hygiene. If a
specification and its runtime share a home, the runtime's behavior silently becomes the standard.
Separation lets the prose keep authority when an implementation disagrees, and lets each release on
its own cadence.

**Q10. Why not encode everything into one giant pack?** Atomicity is what makes a pack testable,
versionable, and reusable. A giant pack is unauditable and forces unrelated decisions to churn
together. Composing small packs is valuable — but composition is its own unsolved problem
([RFC 0002](rfcs/0002-judgment-graph.md)), not an argument for one big document.

**Q11. Is a Judgment Pack executable?** It is declarative. A runtime may evaluate it, but the
specification's resolution model is explicitly informative and experimental and defines no evaluator
conformance and no portable result.

## Judgment Packs

**Q12. How many packs should exist?** One per atomic decision an organization wants applied
consistently. If two decisions have different evidence, outcomes, or escalation, they are two packs.

**Q13. How are packs identified and versioned?** By an `id` (a URI) plus a `version`; a published
`(id, version)` pair should be immutable. The pack's version is independent of `specVersion`. See
[versioning](VERSIONING.md).

**Q14. What is inside a pack?** A decision (intent and question), evidence requirements, sources,
outcomes, rules, exceptions, escalation configuration, metadata, and namespaced extensions.

**Q15. How is a pack tested?** Against the conformance corpus — carrier, structural, and semantic
cases. Behavioral evaluation cases can be authored, but portable evaluation is a possible later
profile, not a conformance claim now.

## Judgment Graph (proposed)

**Q16. What is a Judgment Graph?** A proposed way to compose multiple packs into a larger decision
structure. The interchange format would be [RFC 0002](rfcs/0002-judgment-graph.md). It does not exist
in the specification today.

**Q17. Why is composition hard?** It raises every question a single pack avoids: ordering, conflict
when two packs disagree, a shared fact and evidence namespace, cyclic dependencies, and partial
failure. Presenting it as a finished layer invites a question with no answer yet.

**Q18. When will it enter the specification?** When a composition format is drafted, prototyped, and
shown to interoperate across two independent implementations — the same evidence gate every feature
faces. No date.

## Knowledge Graph and Evidence

**Q19. Why not just use a Knowledge Graph?** A knowledge graph answers "what is known?" A pack
declares "which decision is this, when does it apply, which evidence changes it, and when must a
human take over?" The knowledge graph is one evidence source feeding a pack — not the parent of the
judgment layer.

**Q20. Is a Knowledge Graph required?** No. Evidence may come from SQL, APIs, documents, an ERP or
CRM, a data lake, a knowledge graph, or nothing structured at all.

**Q21. What is "evidence" in a pack?** Declared requirements and references — the pack names what
evidence it needs and points at sources. It is not fetched data and not a query. The pack says what
it needs, never how to get it.

**Q22. Is there an "Evidence Layer"?** Not in the specification. An integration layer that connects
to real systems is a runtime or product concern. Only the reference/adapter contract — how a pack
names the evidence it expects — is a candidate for standardization
([RFC 0003](rfcs/0003-evidence-reference.md)).

## Skills, tools, and agent integration

Judgment can live in prose, code, skills, or a policy engine. JPS exists to make the judgment
*itself* an explicit, portable, independently governed, and verifiable artifact — not to replace the
skills and tools that already operationalize tasks.

**Q23. How does an agent know which Judgment Pack to execute?** Today it does not on its own — the
integrator selects the pack. A standard answer needs a discovery and selection contract
([RFC 0001](rfcs/0001-pack-manifest.md), [RFC 0005](rfcs/0005-pack-discovery.md)). Note the
recursion: selecting a pack is itself a judgment, which is exactly why an autonomous selector is
either governed by its own pack or is product logic ([RFC 0004](rfcs/0004-planner-interface.md)).

**Q24. Can agents create Judgment Packs?** Yes — authoring a pack is a fine use of a model. But a
generated pack is only a candidate document. Structural conformance says it is well-formed; it says
nothing about whether the judgment is correct or whether anyone with authority approved it.

**Q25. Can an agent compose packs at runtime?** Not portably yet — that needs the graph format and
evaluation semantics, both proposed or experimental. An implementation can do it privately, but it
cannot claim JPS conformance for the result.

**Q26. Why not just prompt an LLM, or use MCP?** A prompt couples intent to one model and phrasing;
it is not a structured document a second tool can validate, diff, or version. MCP is a runtime
transport for tools and context between a model and its host. JPS is a static, versioned, testable
artifact describing judgment. They are complementary and sit at different layers — you might ship a
pack over MCP.

### Skills and Tools

**Q27. Does Judgment Pack replace tools or agent skills?** No — the three sit at different layers and
are complementary. A **tool** exposes a capability an agent can use (fetch a record, run a search,
create a vendor). A **skill** guides or implements how a task is performed. A **Judgment Pack** makes
a consequential judgment explicit, testable, portable, versioned, and independently governable.
Skills may call or embed Judgment Packs; the intended relationship is complementary, not competitive.

```text
Tools:          What can the agent do?
Skills:         How should the agent perform the task?
Judgment Packs: What conclusion is justified, based on which evidence and rules?
```

See [what a Judgment Pack is](docs/why.md) and the [architecture vision](docs/architecture/vision.md).

**Q28. Why are `SKILL.md` files or codified skills not sufficient?** They often are. A skill can
absolutely contain judgment instructions — the limitation is not the *absence* of judgment, but
whether the judgment is exposed as a strong enough *contract*. For a low-risk, local, single-agent
task, a well-designed skill may be completely sufficient. The differences appear when the judgment
must be relied on beyond the skill that carries it:

- prose interpreted by a model, versus runtime-enforced semantics;
- implicit, versus typed, evidence requirements ([RFC 0003](rfcs/0003-evidence-reference.md));
- implicit, versus explicit, applicability conditions;
- ad-hoc handling of exceptions and overrides;
- abstention and escalation as first-class states, not asides;
- a standardized judgment output that other tools can read;
- evidence provenance that travels with the conclusion;
- versioning independent of the agent's implementation ([versioning](VERSIONING.md));
- reusable [conformance cases](TESTING.md) that ship with the artifact;
- portability across agents and runtimes;
- governance by an independent business or policy owner ([governance](GOVERNANCE.md)).

None of this says skills are weak. It says a pack turns judgment into a contract precisely when that
contract has to hold outside a single skill.

**Q29. What if a skill already contains judgment logic in `SKILL.md` or executable code?** This is the
sharpest form of the question, and the honest answer depends on *how* the judgment is expressed.

**Judgment written in `SKILL.md`.** The skill genuinely contains judgment — but a model may still
interpret its natural-language conditions differently from run to run, and enforcement, provenance,
expected outputs, and conformance tend to remain framework-specific or implicit. The judgment exists;
the *contract* around it may not.

**Judgment implemented in code.** Coded judgment can already be deterministic, testable, versioned,
enforceable, and production-ready. JPS is **not** automatically better than working code. A pack adds
value only when the judgment needs to become a first-class artifact with: a portable input and output
contract; explicit evidence and provenance semantics; policy versioning independent of code releases;
[conformance cases](TESTING.md) that travel with the artifact; cross-runtime interoperability;
[composability](rfcs/0002-judgment-graph.md) with judgments owned by other teams; and independent
inspection and approval.

```text
Application code may implement an API.
OpenAPI exposes a portable API contract.

Skill code may implement a judgment.
Judgment Pack exposes a portable judgment contract.
```

The analogy has a limit worth stating: organizational judgments are often less stable and less
uniform than API boundaries, so JPS has to *prove* useful interoperability rather than lean on the
conceptual resemblance. See [How Judgment Pack compares](docs/concepts/comparison.md).

**Q30. When is a skill sufficient without a Judgment Pack?** Often. A skill alone is a reasonable
choice when:

- only one agent or application uses the logic;
- the same engineering team owns the skill and the runtime;
- portability across runtimes is not required;
- the decision is low-risk;
- ordinary unit tests are adequate;
- no separate policy-owner approval is needed;
- no regulator, customer, or auditor needs an inspectable decision contract;
- the judgment does not need to compose with independently owned judgments.

Do not add a pack merely for architectural purity. A pack earns its place when: multiple agents must
reach consistent decisions; multiple runtimes must execute the same policy; evidence and provenance
must be standardized; policy versions must be traced independently from code releases; different
teams own separate parts of the final judgment; abstention and escalation must be enforced; or
external review or audit is required.

**Q31. How should skills and Judgment Packs work together?** The skill owns task execution and tool
use; the Judgment Pack owns the decision contract; the agent or workflow
[runtime](#runtime-and-performance) owns the authorized actions taken *after* the judgment. A skill
references a pack — remotely by `(id, version)` or by embedding it in the skill package — and maps
each result to an action:

```yaml
skill:
  id: supplier-onboarding

  tools:
    - fetch_supplier_record
    - run_sanctions_search
    - create_vendor

  judgments:
    - pack: supplier-approval@2.1.0

  actions:
    approved:
      - create_vendor
    rejected:
      - close_request
    escalated:
      - open_legal_review
```

<div class="diagram-figure is-wide">
<img class="diagram" src="/assets/diagram-skills-pack-flow.svg" alt="An agent or workflow runs a skill. The skill calls tools, which read evidence sources; the skill also invokes a Judgment Pack, and the evidence feeds that pack. The pack produces a judgment result routed to one outcome: approved leads to an authorized action, rejected to stop or close, insufficient evidence to a request for evidence, and escalated to human review.">
<p class="diagram-caption">Tools retrieve data and perform actions; the skill coordinates the task; the Judgment Pack evaluates whether a conclusion is justified; the runtime performs the authorized action afterward.</p>
</div>

In that flow: **tools** retrieve data or perform actions; **skills** coordinate the task;
**Judgment Packs** evaluate whether a conclusion is justified; and the **runtime or agent** performs
the authorized action after the judgment. The pack deliberately stops at the judgment — it should not
become a general-purpose workflow engine. A pack can live beside the skill it serves, referenced
remotely or embedded in the package:

```text
supplier-onboarding/
├── SKILL.md
├── tools/
└── judgments/
    └── supplier-approval.jpack.json
```

JPS is meant to slot into existing skill ecosystems, not replace them.

**Q32. If a skills framework adds all these capabilities, is JPack still necessary?** This is the
fair adversarial question. If a skills framework already provides formal applicability rules, typed
evidence contracts, explicit exceptions, deterministic or constrained evaluation, abstention and
escalation, provenance, independent versioning, conformance tests, judgment composition, and
governance, then it already implements much of what JPS proposes. At that point JPS is only useful if
it provides one of two things: (1) an **open, shared interoperability standard** across skill
frameworks, so a judgment authored against one framework stays inspectable and executable in another;
or (2) **materially better tooling and semantics** for authoring, testing, composing, governing, and
auditing judgments.

> Judgment Pack must earn its place through interoperability and tooling. If it becomes only another
> Markdown instruction format, the criticism that it is "skills with a new name" would be valid.

That bar is deliberate, and it is why the interoperability formats are tracked openly as
[RFCs](rfcs/README.md) rather than asserted.

## Runtime and Performance

**Q33. Is there an official runtime?** There is a vendor-neutral reference runtime. It validates
documents at the carrier, structural, and semantic layers. It does not evaluate rules, choose an
outcome, fetch a source, or authorize anything, and it is a reference, not the only valid
implementation.

**Q34. Does a conforming validator "make a decision"?** No. Passing validation establishes only the
document-conformance layers reported. It never establishes truth, authority, safety, or fitness.

**Q35. How does execution scale?** The specification defines no execution, so there are no execution
benchmarks to quote. What can be said honestly: a pack is a small, static, cacheable document that
validates offline in milliseconds and distributes over a CDN like any JSON artifact. The cost of
evaluating a graph of packs is an open question for a runtime and for
[RFC 0002](rfcs/0002-judgment-graph.md).

## Discovery and Versioning

**Q36. How are packs discovered?** Proposed: a per-pack manifest plus a registry index format — the
OCI / npm / Terraform-registry pattern. The interchange format is standardizable
([RFC 0001](rfcs/0001-pack-manifest.md), [RFC 0005](rfcs/0005-pack-discovery.md)); the running
registry is not.

**Q37. Will there be a registry?** Possibly two things that must not be conflated: a registry format
(neutral, specification-side) and a hosted registry service (product, with its own auth, billing, and
threat model).

**Q38. How does versioning work?** SemVer-tagged, immutable releases. Only a maintainer tag and
GitHub release is a real release; files on `main` are work in progress. Reader, writer, semantic, and
migration compatibility are stated separately per release. See [versioning](VERSIONING.md).

**Q39. Can I rely on `0.x`?** No. There is no compatibility or security SLA for `0.x` drafts;
behavior may be removed or changed with migration notes.

## Governance and Open source

**Q40. Who controls JPS?** Its maintainers and community contributors, in public. No required
commercial runtime controls it; conformance is defined by the prose, schema, and corpus, not by any
vendor's product. See [governance](GOVERNANCE.md).

**Q41. How are changes proposed?** Through the [RFC process](rfcs/0000-rfc-process.md). Editorial
fixes are ordinary pull requests; material or normative changes need an RFC with compatibility and
security analysis plus positive and negative cases, and a stable feature needs two independent
implementations.

**Q42. How does JPS stay vendor-neutral?** Implementations are named and maintained separately from
the specification, and naming one never makes it normative. Conformance is defined by the public
prose, schema, and corpus. The reference runtime is one implementation among peers; product
architecture stays on product properties, not on the specification.

**Q43. What is the license, and how do I contribute?** Apache-2.0. Start with the
[testing exercise](TESTING.md), open issues for ambiguities, and file RFCs for material changes.

## Composite Judgment, Testing, and Enterprise

**Q44. What is "Composite Judgment"?** The proposed aggregated result of evaluating a graph of packs.
It presupposes an evaluator the specification does not define, so it is a proposal with two halves:
the portable result format (a specification question, if tools must exchange it) and the computed
output (a runtime concern). See [RFC 0002](rfcs/0002-judgment-graph.md).

**Q45. Does passing conformance mean the pack is correct?** No — and this is the load-bearing
distinction. Conformance means the document agrees with the contract. Factual grounding,
organizational authorization, and operational fitness are three separate claims a validator must
never imply.

**Q46. Is JPS ready for production?** No. It is a research preview. Safe uses today are
experimentation, authoring, review, and conformance testing. Do not automate a real outcome from a
pack.

**Q47. How would an enterprise adopt it safely?** Treat conformance as document hygiene, not a
decision warrant; keep a human accountable for every consequential outcome; pin immutable
specification releases and recorded checksums; and keep authorization in your own systems, since the
specification explicitly refuses to model it. The [non-goals](docs/non-goals.md) and
[architecture vision](docs/architecture/vision.md) spell out these boundaries.

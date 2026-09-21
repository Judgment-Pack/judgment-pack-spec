# RFC 0002: Judgment Graph composition

- Status: Draft
- Type: Standards-track (candidate profile)
- Created: 2026-07-24

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **Amended 2026-09-21.** The status is unchanged: this is still a Draft, and nothing here is
> accepted. Three things changed, and each is marked where it appears.
>
> 1. **The prior question is decided.** Study 004 left this RFC asking which seam the format is
>    *for*. It is for the **dataflow seam**: one decision's outcome consumed as another decision's
>    input, as a fact or as evidence availability. The edge is not grown toward effect or entitlement
>    constructs. *Scope*, below, gives the decision, what it rests on and what it leaves open.
> 2. **The one implementation is described as it stands.** *Evidence* and *Implementation* named a
>    single runtime decision record and said the surface had "grown past" it. Eight graph-specific
>    records now shape it, first released across four runtime versions, with the graph test verb in
>    a fifth; they are named.
> 3. **Four statements of the sketch are corrected or marked as diverging from that
>    implementation.** Where the implementation departs from the sketch, the departure is recorded
>    as a question for this RFC and not settled by adopting either side: an implementation that
>    shares an author with the proposal is evidence of what is encodable, not of what is right.

## Summary

A portable *format* for composing several Judgment Packs into a larger decision structure — a
Judgment Graph — in which one pack's decision can depend on another's. This RFC concerns the
interchange format only, not the algorithm that evaluates it.

## Problem

A single pack declares a single decision. Real decisions compose: an invoice approval may depend on
a supplier-standing decision, which may depend on a sanctions decision. Nothing in the
[core specification](../spec/judgment-pack-core.md) describes how packs reference one another, so
every integrator wires composition privately and non-portably.

## Evidence

Decision Model and Notation (DMN) needed a Decision Requirements Graph precisely because real models
are graphs of decisions, not single tables — and defining that graph's semantics took the standard
years. The same pressure appears here as soon as more than one pack is authored for one workflow.
The repository's own [`data-request-intake-triage`](../examples/data-request-intake-triage.json)
example already shows the seam: its summarized completeness and appropriateness facts are the
verdicts of an upstream assessment that would naturally be its own pack feeding this one — an edge
this format would make first-class instead of an out-of-band convention.

The escape census ([Study 003](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/003-escape-census),
2026-07) supplies this RFC's first measured evidence from third-party policy text: all twelve
separable decisions of two public policies, written by a third party for a purpose unrelated to
JPS, encoded under an information barrier. Finding 4 reports a *forward entitlements /
cross-decision references* residue family — "insurance enables full refund if…" was left out of the
Book-flight pack because it belongs to the Cancel decision, and one pack cannot reference another's
outcome — <del>which is exactly the edge this format proposes</del> (*amended 2026-09-21:* which
motivated this proposal, and which Study 004, below, then showed the prototype's edge does not
express; the scope decision leaves effect and entitlement constructs of this kind outside the
format). The encoding runs were isolated and
barred from specification RFCs, so the observation was not prompted by this proposal; the study
itself was conducted by this project, so this is internally produced corpus evidence, not
independent third-party validation.

The reference runtime carries a working prototype of this composition
([ADR-0015](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/a3058cbadee993306d2f8bc9184cd6d9191a9143/docs/adr/0015-experimental-graph-surface.md),
2026-07-29, behind an explicitly experimental surface; the link pins the reviewed commit, which at
the time of review sat unmerged on the runtime's `jgraph` branch — it has since merged and been
released, and that surface has grown past what the pinned commit shows; *amended 2026-09-21:*
how far is set out under *The implementation as it stands*, below): a closed-schema
document of nodes, edges, and one declared result node, where a node references a pack, an edge
feeds one node's outcome downstream as a fact at an RFC 6901 pointer and/or as a tri-state
evidence contribution, and every node evaluates through the runtime's unchanged Core §§7–8
evaluator in deterministic topological order. It is one implementation, built by this project's
maintainer — evidence that the sketch is encodable and that its open questions have workable
answers, not the independent second implementation the evidence bar requires. Its adversarial
review contributed one observation worth recording as design evidence in its own right: a
prototype guard that refused caller-supplied values at a fed pointer only when the upstream
produced an outcome silently let the caller's value stand in for the outcome an unresolved
upstream never produced — the exact smuggling this format exists to remove, reintroduced by an
evaluation-dependent rule. The candidate invariant this surfaced, for this RFC to weigh rather
than a rule it sets: collision rules that depend on evaluation results reintroduce the smuggling,
and the prototype now decides every collision from the declared edges and the supplied inputs
alone.

A preregistered study
([Study 004](https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments/tree/main/studies/004-composition-closure),
2026-07-30) then measured that prototype grammar's closure over the cross-decision escape in
Study 003's frame. The frame was derived by a registered rule, not picked (five residue
sentences qualified; zero of the census's forty prepared-determination facts did — itself a
result); encoding rooms were hypothesis-blind, given only the policy, the census's own packs,
and the tool. **The grammar closed none of the five.** Every room produced a *validating* graph
with zero edges, independently declining to declare an edge that would be unfaithful — one room
demonstrated candidate edges that validate at exit 0 while inverting the policy's meaning — and
the blocking constructs were counted: an effect/entitlement device on four of five (the
reference changes a later decision's *rules*, not its facts), with action-completion facts and
a disjunctive fan-in on the fifth. The registered predictor's misses were as informative as its
hits: both items predicted to close as scalar verdict-consumption failed on one mechanism, the
gap between a decision's *permission* and an act's *performance*. The measured observation this
leaves for the RFC to weigh, not a resolution: within one policy's own decisions, the
cross-decision escape in this corpus is effect/entitlement-shaped rather than dataflow-shaped,
<del>while the outcome-as-input edge this sketch proposes matches the seam *between* systems — an
upstream decision's recorded verdict consumed as a downstream document's fact — which that
study's frame, by construction, could not contain. Whether this RFC scopes composition to the
between-systems seam or grows the edge toward entitlement constructs is now an evidenced
choice, and still an open one.</del> (*Amended 2026-09-21.* The struck passage did two things this RFC
no longer does. It placed a claim about the seam between systems inside "the measured
observation", although the study's frame could not contain that case, so nothing was measured
about it: that use of the edge is intended and unmeasured. And it called the choice open; it is
decided, in the Scope section below, for the dataflow seam and against effect and entitlement
constructs. The within-policy observation before the strike is the measurement, and it stands.)
The usual bounds apply: one grammar, one frame, two policies by
one benchmark team, internally produced under a preregistration; neither the zero nor any other
rate licenses claims about composition as a design class.

### The implementation as it stands

*Added 2026-09-21.* Eight decision records of the reference runtime are specific to its graph
surface. All are accepted, each is linked here at the runtime's `main`, and they first shipped
across four versions. The list is not everything that governs the surface: the runtime's decisions
on the reviewed-set lock, audit records and evaluation traces cover graphs too.

| Record | What it decided | First released |
| --- | --- | --- |
| [ADR-0015](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0015-experimental-graph-surface.md) | the standalone graph document, the `experimental graph` verbs, and a tested position on each of this RFC's five original open questions | 0.8.0 |
| [ADR-0016](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0016-graph-rows-coverage-report.md) | a derived coverage report over a graph's test rows, which informs and never gates | 0.10.0 |
| [ADR-0017](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0017-declare-graphs-in-the-project-configuration.md) | graphs declared in the project configuration — reversing, knowingly, ADR-0015's position that they stay out of it | 0.10.0 |
| [ADR-0026](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0026-run-the-declared-graph-matrix-over-mcp.md) | the declared graph matrix run over MCP, with a budget that stops a runaway matrix | 0.18.0 |
| [ADR-0029](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0029-serve-graphs-and-their-inventory.md) | the configured graphs and their inventory served read-only | 0.19.0 |
| [ADR-0030](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0030-bind-graph-matrix-runs-and-validations-to-the-loaded-document.md) | a digest that binds a matrix run or a validation to the exact graph document it loaded | 0.19.0 |
| [ADR-0031](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0031-report-node-traces-in-the-graph-matrix-on-request.md) | each compared node's evaluation trace, on request | 0.19.0 |
| [ADR-0032](https://github.com/Judgment-Pack/judgment-pack-runtime/blob/main/docs/adr/0032-let-a-graph-row-assert-the-handoff-target.md) | a test row may assert where a handoff would go | 0.19.0 |

One increment has no record of its own, and accounts for a fifth version: the graph test verb,
which runs a rows document against a graph and compares dispositions byte for byte in their
RFC 8785 canonical form, shipped in 0.9.0.

Five things about that surface bear on this RFC, and the first two are departures from its sketch.

- **A node names a pack by a project-local decision id, not by `(id, version)`.** The node has one
  reference member, `pack`, whose value is resolved through the runtime's project configuration
  (`jpack.json`, a convention of that runtime and no part of JPS). The pack's own `id` and `version`
  are read off the loaded document and *reported* in the result; the graph never declares them.
- **The graph document pins nothing about a pack.** It carries no pack version and no pack digest.
  What the runtime offers instead sits outside the document: an optional `expectedVersion` on the
  project's pack entry, which `packs validate` checks and the graph surface never consults; and an
  optional reviewed-set lock of byte digests, which the deciding surfaces consult and the
  rehearsal surfaces do not. ADR-0030's digest binds the graph *document's* bytes, not its packs'.
- **The document carries one switch whose meaning is evaluator behavior.** `onUnresolved`, on an
  evidence feed, says which tri-state an upstream that produced no outcome contributes, and so
  changes what a downstream node is given. The `result` member is a different kind of thing: a
  structural reference naming the node whose disposition the composite echoes as its headline,
  read after the nodes have evaluated and changing none of their inputs or dispositions.
- **A graph composes only packs that one project configuration declares.** There is no remote,
  registry or cross-project node reference anywhere in the format.
- **A companion format exists.** A rows document, with a version gate of its own, states cases and
  expectations for a graph; nothing in this RFC's sketch anticipates a test format.

The runtime labels the composition in band as experimental and as a non-normative convention of
that runtime, and says that no JPS version defines a graph or a composite result. One distinction
is easy to lose: the *composition* claims nothing, while the evaluator reached through it is the
one the runtime's conformance claim covers, and its `CONFORMANCE.md` lists `experimental graph
evaluate` and `experimental graph test` among the surfaces that reach that evaluator. A node's
disposition is a claimed evaluation; the graph around it is not.

## Scope

*Added 2026-09-21; decided by the maintainer.* Study 004 left one question prior to the others:
which seam this format is for. **It is for the dataflow seam** — one decision's outcome consumed as
another decision's input, as a fact at a pointer or as the availability of a piece of evidence.
**The edge is not grown toward effect or entitlement constructs.** The use the maintainer has in
mind for it is the seam between decisions that different parties or systems own — an upstream
verdict that a downstream pack reads and does not re-derive. That use is **intended and
unmeasured**: Study 004's frame could not contain a between-systems case by construction, and the
one implementation composes only packs that a single project configuration declares, so nothing
here shows that the seam between owners is where this edge is needed, or that it suffices there.

What the decision rests on. Study 004 measured that, within one policy's own decisions, the
cross-decision references in its corpus were effect- or entitlement-shaped on four of five items:
the reference changes what a later decision may *conclude*, not a fact its conditions read. That is
a measurement. What follows is a judgment, and it is the maintainer's: an edge that carried such a
reference would be a rule about another pack's rules, and extending edges that way risks growing
toward the general-purpose rules language the [non-goals](../docs/non-goals.md) exclude. The
non-goals exclude that language; they do not themselves say an entitlement edge begins one. The one
implementation reached the same place from the other side: its authoring guidance refuses an edge
where "a permission is not a performed act, and an entitlement that changes what a later decision
may conclude is not a fact its conditions read", and, where no faithful edge exists, treats a
validating graph with no edges as the correct answer. The limits are the ones Study 004 states for
itself — one grammar, one frame, two policies by one benchmark team — and the implementation
shares an author with this RFC.

What the decision leaves open, and where it goes. The within-policy residue Study 004 counted is
real and stays uncounted for by this format. It belongs with
[RFC 0007](0007-determination-boundary.md), which records what a pack cannot hold; nothing here
proposes a device for it. And the decision sharpens one question the implementation has not
faced, listed below under *Unresolved questions*: where decisions belong to different systems, a
downstream decision may receive an upstream verdict that was **recorded** elsewhere, while the
implementation **co-evaluates** every node in one run from one project's packs.

## Specification (sketch)

A graph document references packs by `(id, version)` and declares directed dependencies between
their decisions. The format would need to express, at minimum: nodes (pack references), edges
(which decision feeds which), and how one decision's outcome is exposed as another's evidence. The
format is declarative and carries no evaluation semantics itself.

*Amended 2026-09-21 — the sketch stands as the proposal, and the one implementation departs from
two of its sentences.*

- *"References packs by `(id, version)`."* The implementation references a project-local decision
  id and declares neither (see *The implementation as it stands*). A portable format cannot lean
  on one runtime's project configuration, so the sketch's form is kept as the proposal, and how a
  node should name its pack is now an unresolved question rather than a settled line.
- *"Carries no evaluation semantics itself."* Too strong for anything that exposes an upstream
  outcome as evidence. The implementation needed a declared switch, `onUnresolved`, for what an
  upstream without an outcome contributes. (Its `result` member, which names the headline node, is
  structure and not semantics, and does not bear on this sentence.) The narrower claim that
  survives: the format defines **no algorithm** — no order of evaluation,
  no conflict resolution, no aggregation — and may declare, per edge, a choice the evaluator must
  honor. Whether `onUnresolved` belongs in a portable format is listed below.

## Alternatives

- **No change** — composition stays a private, per-integrator concern.
- **Extension** — express edges in `extensions`; rejected because cross-pack references must be
  first-class and validated.
- **One giant pack** — collapse the graph into a single document; rejected because it destroys the
  atomic, independently testable and versionable unit the format is built on.
- **Product-only** — leave graphs to runtimes; viable for evaluation, but the *format* is a genuine
  interchange need.

## Compatibility

Would be a new optional profile. Core packs are unchanged and remain valid standalone.

## Security and privacy

Cross-pack references introduce supply-chain and confused-deputy risks: a graph could pull in an
unexpected pack version, or expose one decision's evidence to another. Version pinning and explicit
evidence exposure are required, not implicit.

*Amended 2026-09-21.* The requirement stands, and the one implementation meets half of it.
**Evidence exposure is explicit**: nothing crosses a node boundary except what an edge places.
**Version pinning is not in the document at all**: the graph carries no pack version and no pack
digest, and what pins a pack sits in the runtime's project files, optional, and consulted by some
surfaces and not others. That is a gap between this section and the prototype, recorded as one and
not closed by weakening the requirement. [RFC 0001](0001-pack-manifest.md)'s digest — `sha256:`
over the exact pack bytes — is the obvious candidate for what a node would pin, and is itself a
Draft.

## Conformance

Positive: a graph whose references all resolve and whose edges form a DAG. Negative: dangling pack
reference; version drift; a cycle where the format forbids one.

*Amended 2026-09-21.* "Version drift" is a case the implementation's graph document cannot
express, since it declares no version to drift from; it stays a case of this sketch. The
implementation does give the other cases a concrete form worth borrowing. Among its findings, and
not a complete list of them: a dangling pack reference; an edge naming an undeclared node; a
self-edge; a `result` naming an undeclared node; two edges feeding one fact pointer, or one
evidence requirement, **of the same target node** — different nodes may use the same pointer or
requirement id; two fact pointers of the same target node where one is a prefix of the other once
their RFC 6901 tokens are decoded; a fact pointer of more than 64 decoded reference tokens; and a
cycle, whose member nodes are determined using strongly connected components and reported together
in one finding. It also shows a distinction this section did not draw: whether references
resolve is two questions. One is answerable without reading any pack — in the implementation,
from the graph and the project configuration that names the packs. The other requires reading a
pack: that an edge's evidence requirement is one the target pack declares. The implementation
evaluates behind the first check only, so that a malformed pack gets its §8.4 error class from the
evaluator and not an unclassed refusal from the graph layer.

## Implementation

Two implementations should agree on whether a given graph document is well-formed and acyclic,
independent of any evaluator. One implementation exists — the reference runtime's experimental
graph surface (ADR-0015), written against an earlier draft of this sketch, since merged and
released, and since grown past what that decision record describes — and, sharing an author with
this RFC, counts toward encodability and nothing else. A second, independent implementation is
what the evidence bar actually asks for, and there is none.

*Amended 2026-09-21.* "Grown past" is now spelled out under *The implementation as it stands*:
eight decision records, a companion rows format, a declaration site in the project configuration,
three MCP tools, a plan verb that evaluates nothing, digest binding, node traces, and handoff-target
assertions. It is still one implementation by this RFC's author, and the sentence above about what
that counts toward is unchanged. One thing it makes concrete: the sketch's evaluator-independent
check exists in it — a graph can be loaded and checked for shape, references and cycles without
reading a pack — so a second implementation has a definite thing to agree or disagree with.

## Unresolved questions

*Amended 2026-09-21.* The prior question named at the end of the next paragraph — which seam this
format is for — is decided: see *Scope*. The five questions below it stay open, and four more are
added after them. The paragraph says the prototype takes a position on "the first four"; it has a
tested position on the fifth too, the composite result, which that bullet describes as a knowing
hedge.

Each question stays open. The runtime prototype (see Evidence) takes a position on the first four,
recorded here as one implementation's tested answers rather than as resolutions; the positions are
encoded as that surface's tests, so a better answer has a concrete artifact to refute. Study 004
(see Evidence) then measured that grammar against the census's cross-decision residue and closed
none of it, naming four constructs implicated in that grammar's five open items — entitlement
edges, action-completion facts, disjunctive fan-in, outcome-value mapping — so the questions
below now have a negative result to weigh beside the positions, and one prior question: which
seam this format is *for*.

- **Ordering and conflict** — when two packs produce conflicting outcomes for a shared question,
  what does the format say (if anything) versus the evaluator? *Prototype position: refuse, never
  merge.* Deterministic topological order with node ids breaking ties; two edges feeding one
  node's same or overlapping fact pointer (compared on decoded RFC 6901 tokens, so two spellings
  of one path cannot hide the collision) or the same evidence requirement are validation errors;
  a fact feed colliding with caller-supplied inputs is refused before any node evaluates —
  unconditionally, for the reason recorded under Evidence — and an evidence feed colliding with
  the caller's evidence document is refused before its target node evaluates, equally regardless
  of what any upstream produced.
- **Shared namespace** — do packs in a graph share a fact/evidence namespace, or is each isolated
  with explicit mapping? *Prototype position: isolated with explicit mapping.* Nothing is shared;
  the only values that cross a node boundary are the ones an edge explicitly places.
- **Cycles** — are cyclic dependencies always invalid, or valid with a declared fixpoint rule?
  *Prototype position: always invalid*, with cycle membership reported by strongly connected
  components so a node merely blocked behind a cycle is never named as part of one.
- **Partial failure** — how is an unresolved upstream decision represented downstream? The portable
  disposition of Core §8.3, landed by [RFC 0006](0006-evaluator-conformance.md) in `0.2.0-draft`, is
  the candidate representation; the edge semantics stay this RFC's to settle. *Prototype position:
  an upstream that produced no outcome injects no fact — the pointer is simply absent, which §7
  already reads as unknown — and an evidence feed contributes a declared tri-state (unknown by
  default, absent by declaration), so an unresolved upstream reaches a downstream pack only
  through that pack's own declared semantics: its unknown handling for the default, its
  required-evidence rule when the feed declares absence (*amended 2026-09-21:* and the fed
  requirement is one the downstream pack marks required, and that pack is applicable; an absence
  fed to an optional requirement engages no such rule). Every requested handoff surfaces beside
  the composite. Evaluation errors stay errors: a refused node refuses the whole run with its
  §8.4 class intact, and no partial composite exists.*
- **Composite result** — is the aggregated result a portable artifact (a spec concern) or a runtime
  output? This is the hardest question and is deliberately unresolved. The prototype hedges it
  knowingly: its composite is an envelope — the per-node §8.3 dispositions side by side, the
  declared result node's echoed as a headline — labeled in band as a runtime convention, carrying
  what a portable artifact would need while claiming to be none.

*Added 2026-09-21 — four questions the implementation and the scope decision surface.*

- **How does a node name its pack, and what does it pin?** The sketch says `(id, version)`. The
  prototype names a project-local decision id, reports the pack's own identity after loading, and
  pins nothing in the document. A project-local id is not portable, and an `(id, version)` pair
  names a series position and not bytes. Candidates: `(id, version)` alone; `(id, version)` with
  [RFC 0001](0001-pack-manifest.md)'s exact-bytes digest; the digest alone, with identity read
  from the pack. *Security and privacy* requires pinning, so "nothing" is not among them — but what
  a graph's reader may conclude when a pin and a loaded pack disagree is not yet said anywhere.
- **Co-evaluated, or consumed as recorded?** The intended use is the seam between decisions that
  different parties own, and that use is unmeasured (see *Scope*). The prototype evaluates every
  node in one run, from packs one project configuration declares, and has no way to name a pack
  outside it. Where the upstream decision belongs to another system, its verdict may already have
  been made, and would then arrive as a record and not as a pack to run. Whether an edge
  may take its input from a **recorded** disposition — and what it must then bind, which is where
  [RFC 0014](0014-lineage-record-and-action-binding.md)'s citation of a decision record by digest
  would meet this format — is unexamined. So is its cost: a recorded verdict can be stale in a way
  a verdict computed in the same run cannot.
- **Does a per-edge evaluator switch belong in a portable format?** `onUnresolved` exists because
  exposing an outcome as evidence forces the question of what a missing outcome contributes. The
  alternatives are to fix one answer in the format, or to leave it to the downstream pack's own
  handling of an unknown. The prototype's default, `unknown`, is the second. Its `absent` engages
  the downstream pack's required-evidence rule — when the target requirement is a required one
  and the downstream pack is applicable, and not otherwise — and is a claim about the *upstream*
  that the graph's author must ground in the source: the prototype's authoring guidance permits it
  only when the source says a decision that produced no outcome is itself the missing evidence. Note that the
  prototype's "no outcome" covers `not-applicable` as well as `unresolved`.
- **Is a test format part of the interchange?** The prototype grew a rows document — cases, inputs
  and expected dispositions for a graph, with its own version gate — because a composition nobody
  can test is not reviewable. The same split exists one level down, and is answered there: the
  reference runtime keeps a pack's test matrix as a convention of its own, and Core defines none.
  Whether graphs need a portable test format, or whether that too stays with each runtime, is
  open.

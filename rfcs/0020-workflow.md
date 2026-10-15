# RFC 0020: The workflow

- Status: Draft
- Type: Standards track (a companion document of the specification, with a reader conformance
  class; fixtures recorded from a two-stage run)
- Created: 2026-10-15
- Amended: 2026-10-15 (a research stage, issue #174)
- Issue: [#160](https://github.com/Judgment-Pack/judgment-pack-spec/issues/160)

This is an open proposal. Its companion text is present for review, normative for nothing.
No implementation or workflow fixture exists. The Type names the evidence to obtain, not evidence
already held. [RFC 0000](0000-rfc-process.md) governs its review and acceptance.

## Amendment of 2026-10-15: a research stage

This amendment records the maintainer's four decisions on
[issue #174](https://github.com/Judgment-Pack/judgment-pack-spec/issues/174), on
[pull request 177][round-2],
**RFC 0020: a research stage**. Its review is round 2 of this RFC, recorded in the pull request's
first comment, with the maintainer's dispositions in its second comment. The one HIGH, five
MEDIUM and six LOW findings are accepted and applied below. The status stays Draft.

This is the workflow revision anticipated by RFC 0018's round-8 amendment,
[the research contract](0018-dialect.md#amendment-of-2026-10-15-the-portable-research-contract).
Section 4 conditionally admits a stage whose dialect binds a `research` source at import, with
generated AI and any web profiles under that contract; question 2 is resolved. Freezing and
verification wait for a research-capable release form and encoding to be pinned. The published
dialect's own admission holds its model-served targets. Section 11 keeps the operation acceptance
construction and names the implementation work needed for an additional research recording
beside it. Workflow version 1's document form is unchanged. Replay checks retained bytes under
the profiles then bound and never asks a model or the web again.

This revision supersedes the dialect's statement that workflow version 1 admits no research
stage (fixture 8 in dialect §11, RFC 0018's question 15 and its round-8 paragraph), pending the
dialect's own amendment filed as [judgment-pack-spec#179][dialect-amendment]. Fixture 8's statement
that the research plan does not replace the operation demonstration stands: the research
recording is additional, beside that demonstration.

[dialect-amendment]: https://github.com/Judgment-Pack/judgment-pack-spec/issues/179
[round-2]: https://github.com/Judgment-Pack/judgment-pack-spec/pull/177

## Summary

A **workflow** declares how one dialect runs for each record selected from another stage's
outputs. Each stage pins its own published dialect and pack, names its input and output
projection, and declares the relation between its outputs and their parent. Selection records
bind the whole offered set and the chosen subset; output records preserve parentage; an execution
record closes the instance inventory, including zero-output and unsuccessful work.

This is option A of the design memo recorded on issue #160: a standalone companion document,
`spec/workflow.md`, with a `workflow-verifier` reader class. The Runner executes, the Desk
reviews, and the Runtime and Gateway keep their existing semantics. Verification establishes
consistency of recorded stages and selections, without authenticating reviewer identity or which
published dialect and binding produced the signed preparation. Acceptance needs the two-stage
run the maintainer's decision requires; it does not exist yet.

## Problem

A pack decides one case. A dialect prepares one case's facts and evidence. Neither says how to
run a second dialect once for each record a reviewer selected from the first one's discovery.
An installation importing that research needs the two dialects and packs by digest, the root
case, the exact offered collection and selected subset, the projection into each child case,
and the relation back to the selected parent. It also needs its own source bindings.

Issue #160 motivates this with organisation discovery followed by people research at selected
organisations, from the Desk's research line (#369 and #371). The design memo recorded on
issue #160, §1, finds that chain to be a motivating requirement, not a demonstrated execution.
The Desk's `web/src/research/run.ts` (judgment-pack-desk at `6b8a46c`) sequences `researchTurn` and
`casesAndCheck` in `AuthoringRun.start`: it researches and checks a candidate pack. Its budgets,
conversation state and sequencing are Desk-private. They do not establish an organisation/person
workflow. Copying a prompt or transcript would leave selection and iteration implicit.

The [judgment graph](0002-judgment-graph.md) is the dataflow between decisions: an outcome
becomes a fact or evidence availability for another evaluation. It supplies neither acquisition
nor record iteration. RFC 0011, named as a graph in the issue, is instead the
[currency-anchor proposal](0011-judgment-currency-anchor.md). Neither substitutes for the missing
contract, and pinning a pack's bytes does not establish that it is current policy.

## Evidence

**No workflow implementation or fixture exists.** No verifier has been written for this format,
no two readers have agreed on it, and no vector or conformance claim is made. The acceptance
fixture is a recorded two-stage run from the Desk's research line. The maintainer's decision on
issue #160 explicitly permits the Draft to land without it and requires its layout to be defined.
Specification §11 names those files and the positive, negative, boundary and recovery recordings
to obtain. They are a plan, not generated evidence standing in for a run.

**Prior art to reuse.** Judgment-pack-desk at `6b8a46c`, `web/src/research/ledger.ts`, defines
`SourceRecord` as a search or page: a request, exact acquisition response, receipt, verification
state and excerpts. At the same commit, `web/src/research/run.ts`'s `researchRecord` writes
`researchRecordVersion: '1'`, pack and check digests, sessions, registries, cases, citations and
source responses beside the authored pack. That research record is useful retained evidence; it
is not this workflow's selection, output or execution record. It supplies neither the
demonstrated two-stage chain nor its closed selection and child inventory. Import must not
invent those absent facts.

The Runner's `internal/runner/mapping_v2_export.go` at `89cf441` recomputes preparation at
retained time under historical profiles, and can separately rehearse evaluation under a pinned
Runtime. At that commit, `cmd/jpack-runner/main.go` distinguishes verified inputs from verified
disposition, and `internal/runner/run_chain.go` binds completed runs to audit bytes and
preceding entries; completion order does not establish a workflow dependency. These are reusable
components, not workflow verification already implemented.

**The prerequisite's standing.** The maintainer's decision records version-3 import/binding as
delivered by judgment-pack-runner #83, merged as `89cf441` and released as the Runner's
`v0.12.0`: the reference Runner reads a version-3 document and binds an unbound source at import
through a binding document. This Draft does not claim to have run that implementation. The first
recording must use that version-3 binder.

The Runner's `docs/MAPPING-V2.md` at `89cf441`, "Dialect version 3" and "Release checks, runtime
and offline verification", documents the binder and run-export form used in §§1 and 7.
Judgment-pack-runtime `v0.32.0` at `80a8176`, `README.md`, "Experimental evaluation behavior",
names the Core §8.4 error-envelope member `evaluationError.class`; its
`docs/building-with-packs.md`, "Keeping a record of what you decided", says refusals write no
audit record. The Runner's `internal/runner/mapping_v2_export.go` at `89cf441` reads the audit's
`disposition` member. Section 7 distinguishes that source evidence from the runtime documents
and records the reference Runner's failure-envelope retention limit; question 8 retains the gap.

**Condition 2's path.** This Draft chooses to demonstrate the chain through `operation` sources.
Specification §11 gives the concrete two-stage construction, including the generated profiles,
projections, reviewer selection and empty child. It is a construction to record, not a recorded
demonstration. It uses the dialect §4.4's operation binding; that section also defines the
research binding conditionally admitted by §4 below. Condition 2's operation demonstration
remains due with the acceptance fixture. The research recording follows fixture 8's plan beside
it and uses §11's workflow bundle layout. The published dialects' generated-only admissions
refuse record-class bindings using the existing dialect, without extending it. The installation
still classifies what each channel actually serves; the verifier cannot detect an undeclared
model behind a channel the installation calls a record source.

## Where it lives

On acceptance, `spec/workflow.md` would be a companion document of the specification beside
Core, normative for its reader class only. The text is present now to make the proposal reviewable
and to support a separately written reader. The Specification below and the companion's numbered
sections are held equal, with headings one level apart, as RFC 0018's are. Until acceptance,
`.gitattributes` export-ignores the companion, as it did for RFC 0018's Draft: no release bundle
carries it. The site publishes its text through this RFC's page.

The Runner interprets the definition, freezes bindings and releases, admits and executes
instances, and retains records. The Desk reviews selections and shows the pinned definitions,
projected cases and relations. These boundaries follow judgment-pack-desk at `6b8a46c`,
`docs/design/job-file-inputs.md` and `docs/design/jobs-mapping-v2.md`. The Runtime evaluates
each case and records its audit; the Gateway acquires under its existing profiles and receipts.
Neither gains workflow semantics.

The Exchange gains a workflow entry kind only through a later explicit revision of
[RFC 0019 §3](0019-exchange.md#3-the-entry-format). Version 1 is closed and names one pack
with its input/output dialect documents; it has no workflow member. This RFC adds none to it.

## Specification

This section is the proposed companion document's §§1–11, word for word, with each heading one
level down. The companion adds only its title and Status. Its rules are proposed, not adopted.

### 1. Terms and canonical forms

A **workflow** declares stages over selected records. A **stage** pins one dialect and one pack;
an **instance** prepares and evaluates one case. A **workflow runner** interprets the workflow,
admits and executes instances, and retains their records; its reference is the Runner. A review
interface, such as the Desk, reviews selections and displays the pinned definitions. A workflow
changes neither Core evaluation nor the dialect. Its output records are new envelopes around data.

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT** and **MAY** have
their BCP 14 meanings only in capitals. All forms below are closed; every listed member is
required unless expressly conditional. Unknown members, duplicate object names and duplicate ids
are refused. An id is `[a-z][a-z0-9-]{0,63}`. A digest is `sha256:` and 64 lowercase hexadecimal
characters, compared exactly. A timestamp has the form and valid instant of the dialect §1.

JSON is strict as in [the dialect](../spec/dialect.md), §1: one value, well-formed Unicode and
number literals retained. The workflow, selection, output, set and execution objects use its `canon`
form: object members ordered by code point, arrays preserved, no whitespace or inserted defaults,
all supplied members included, integers from −(2⁵³−1) to 2⁵³−1, and `-0` written `0`.
Non-integer number literals have no form here. Their digests are SHA-256 of those canonical bytes.
A digest member lives outside the object it names; an object never contains its own digest.

Cases and output payloads are objects serialized in the dialect §9.5 form, restricted to that
integer domain: number literals, including `-0`, survive; strings escape the additional characters
that §9.5 names. Their digests name those bytes. Preparations retain that same existing form;
acquired responses and audit records retain their original bytes. These forms are not exchanged.
Pack digests name exact retained bytes, explicitly adopting
[RFC 0001](../rfcs/0001-pack-manifest.md)'s still-Draft choice, with no normalization.
Published and bound dialects and binding documents use the dialect's canonical digests.
The required reference Runner is judgment-pack-runner at `89cf441`, the version-3 binder shipped
in `v0.12.0`. Its release digest is SHA-256 of `canonical(encode(r))`, where `r` is the decoded
`Release`, not the whole retained JSON object: the typed encoding can omit members. The required
encoding references at that pin are `internal/runner/model.go` (`Release`),
`internal/runner/source_inputs.go` (`InputMapping`), `internal/runner/dialect_v3.go`
(`InputMapping.MarshalJSON`) and `internal/runner/mapping_v2_export.go` (`releaseDigest`).
It is not a file-byte digest.
The Runner's `docs/MAPPING-V2.md` at `89cf441`, "Dialect version 3", documents the version-3
encoding; "Release checks, runtime and offline verification" documents the run export (§7).

The runtime reference is judgment-pack-runtime `v0.32.0` at `80a8176`. Its `README.md`,
"Experimental evaluation behavior", names `disposition` in the Core §8.3 result payload and
`evaluationError.class` in a Core §8.4 error envelope. Its `docs/building-with-packs.md`,
"Keeping a record of what you decided", and `docs/architecture.md`, "Packages", describe an
audit retaining the canonical disposition and no record for a refused evaluation. The Runner's
`internal/runner/mapping_v2_export.go` at `89cf441` reads the audit member `disposition`, hence
`run.audit.disposition`; this member name is established by that source. Runtime
`docs/adr/0027-pin-the-evaluation-trace-contract.md` at `80a8176` keeps trace outside the
disposition and discards it on evaluation error. Section 7 applies these distinct forms.

### 2. The workflow document and bounds

`workflow.json` is exactly `{workflowVersion, stages, result, limits}`. `workflowVersion` is the
integer `1`; `stages` is an ordered array of 1 to `limits.maxStages` stages (§3), with distinct
ids. Exactly the first stage is a root. Every other stage names an earlier stage; all are thereby
reachable from the root. `result` is a stage id naming a terminal stage, one with no consumers.
It names that stage's ordered outputs, without aggregating dispositions or discarding other stages.

`limits` is exactly the following integer members; each is at least 1 and at most the ceiling:

| Member | Ceiling | Applies to one execution branch |
| --- | --- | --- |
| `maxStages` | 32 | stages |
| `maxRecords` | 4096 | output envelopes across all stages |
| `maxInstances` | 4096 | logical instances, including failures and cancellations |
| `maxAttempts` | 16 | attempts per instance |
| `maxBytes` | 1073741824 | supplied bundle bytes, each file counted once |

The bounds below and §1's integer domain apply to workflow, selection, output, set and execution
objects and to cases and payloads; packs, acquisitions, preparations, audits and run exports keep
their own formats' bounds and number domains, within the branch's aggregate byte and file limits.
Those workflow objects have at most 64 container levels; cases and payloads have at most 32.
The dialect §12 counting convention applies. Every object has at most 4096 members, every array
at most 4096 elements, every decoded string and member name at most 65536 UTF-8 bytes, and every
number literal at most 128 characters. Smaller bounds stated here or by a referenced format win.
The bundle has at most 65536 files. The workflow is at most 262144 bytes; each selection and
output envelope at most 65536; each case and payload at most 1048576; each set and the execution
record at most 8388608. Dialect §12's smaller artifact and combined-input bounds
also apply separately to every preparation, including retained attempts. Counts include empty
containers and unsuccessful work; nothing is truncated to fit. The same bounds hold canonical
bytes and input bytes. A workflow runner refuses admission before acquisition when a known bound
fails. Account for results in instance order: stage order, then selected parent-record order,
then output index, regardless of acquisition or completion order. The first instance whose
outputs would exceed a branch bound and every later instance of that stage record
`limit-exceeded`, emitting no outputs. Earlier completed siblings' outputs remain in the closed
set with those failures explicit. Nothing is truncated to fit.

### 3. Stages and projected cases

A stage is exactly `{id, dialect, pack, input, execution, caseBindings, outputs, relation}` and
the conditional `selection` below. `dialect` is `{version, digest}`: integer version `2` or `3`
and the published canonical digest. An unknown stage `dialect.version` is `version-unread`, before
closed-form checking, as is a defined version the reader does not read. `pack` is `{id, digest}`:
its Core absolute-URI id, at most 2048 UTF-8 bytes, and exact-byte digest. Loaded identities MUST
match both pins. A mutable version, job id or
catalog name cannot substitute for them. Each stage has its own pins, even when stages share bytes.

The root's `input` is exactly `{root: true}`, `execution` is `once`, and `caseBindings` is `[]`.
It receives the supplied root case once. A dependent stage's `input` is exactly
`{fromStage: S, selected: true}`: `input.fromStage` names the earlier producing stage, and
`input.selected` requires its selection; the dependent stage's `execution` is
`each-selected-record`. It gets exactly one instance per selected upstream output envelope,
including when equal payloads have distinct record identities. There is one parent per instance.
No join, recursion, cross-product, entity deduplication or implicit input sharing is admitted.

For a dependent stage, `caseBindings` holds 1 to 64 objects, each exactly
`{from, to, type, required}`. `from` is a pointer into the selected record's payload, never its
envelope; `to` is a non-empty pointer into a fresh `{}` case. Both are RFC 6901 pointers of at
most 1024 UTF-8 bytes and 32 decoded tokens; escapes are only `~0` and `~1`. Reading follows
the dialect §1 pointer rule. Writing creates object members only, including numeric tokens.
Destinations MUST NOT equal or prefix one another by decoded whole tokens, regardless of whether
a value exists. The source pointer may be empty, explicitly naming the whole payload.

`type` is `string`, `integer`, `timestamp`, `boolean`, `object`, `array` or `null`, with the
JSON meanings and the dialect §1 integer and timestamp meanings. `required` is a boolean.
Only an absent optional value is omitted. An absent required value or any present mistyped value
fails projection before acquisition; `null` is present and matches only `null`. Copies preserve
literals and disclose only the named values, including their descendants for a container copy.
No coercion, default, template, expression or script runs here. The resulting case contains exactly
these copies, with no inherited root members. Overlap is a document refusal; a value failure is
an instance failure. The verifier recomputes both, rather than trusting the retained case.
Failing a present mistyped optional value is a deliberate departure from the design memo recorded
on issue #160, which failed only missing or mistyped required values.

`outputs` is `{pointer, cardinality}`. The pointer is non-empty, has the bounds above and resolves
in the prepared **facts document**, not an acquisition or an audit record. `cardinality` is `one` or
`many`: `one` requires an object; `many` requires an array of objects. An empty array succeeds
with zero outputs. An absent value, `null`, a wrong type or a non-object array member fails the
instance; none means an empty array. A many-output invocation evaluates one case about the
collection and supplies records for review, not a disposition for each candidate.

`selection` belongs to the producing stage whose outputs are offered. It is present exactly when
another stage consumes that stage, and absent on a stage no stage consumes (a terminal stage).
It is `{mode: "reviewer"}`, or `{mode: "disposition", rule: R}`. R is exactly
`{kind: "outcome", outcomeId: O}`, `{kind: "unresolved"}` or `{kind: "not-applicable"}`.
O is a declared pack outcome id, 1 to 256 UTF-8 bytes. This is equality on the recorded Core
§8.3 disposition's kind and, for `outcome`, its outcome id; reasons and handoff remain unchanged.
Disposition mode requires `outputs.cardinality: "one"`. Evaluation errors have no disposition
and no outputs. Rules do not select a batch's members by the batch's disposition.

`relation` is `{label, direction}`: label is an id, and direction is `output-to-parent` or
`parent-to-output`. A root's parent is the root case; a dependent output's parent is its selected
record. The label declares provenance, not a verified identity, employment or other domain fact.

### 4. Bindings and influence across stages

Before the root runs, the installation freezes each stage's published dialect, binding document
when required, resulting bound dialect and release (§7). Unbound `operation` and `research`
sources are bound at import and expanded exactly as the dialect §4.4 specifies. An operation's
expansion names its bound profile; a research source's expansion names its bound AI profile
and any web profiles, all of class `generated`. Its `fields`, `model` and `capabilities` remain
as published. The dialect's declared model, capability and class checks apply, with incompatible
research profiles giving `profile-mismatch` (dialect §§4.4 and 5.1). The workflow verifier reports
that finding as `preparation-mismatch` when it arises in a preparation and as
`stage-binding-mismatch` from §9's check 1. A workflow runner refuses to freeze a stage with
incompatible research profiles, so no instance is admitted.
A dialect with no unbound source has a null binding-document digest and an unchanged bound
digest; a superfluous binding document is refused as in the dialect §4.4.

Research-stage admission is conditional: its release form and encoding are pinned when a
Runner prepares the kind ([judgment-pack-runner#88][research-preparer]). Until then no research
stage can be frozen or verified under §§1 and 7; the release encoding at `89cf441` cannot retain
the research contract's members.

The two-stage operation construction in §11 remains the acceptance demonstration of issue #160's
condition 2; the research recording is additional, beside it.
An operation's profile declares the installation's classification of its channel. A published
dialect whose source serves a model's answers MUST declare `admits` exactly `["generated"]` at
every target of that source. A record-class binding then fails the dialect's
§8.2 admission at preparation; §9's check 1 confirms the bound profile's class against that
published admission. A published dialect MUST declare `admits` exactly `["generated"]` at every
target of a `research` source; §9's check 1 confirms it (`stage-binding-mismatch`).
This checks declared classes, not whether the channel actually serves a model: that still depends
on the installation's classification. Using the operation kind does not establish authorship.

Copied values remain **case assertions** in the unchanged dialect. The workflow adds a check
outside its preparation: it carries the upstream classes and generated influence across each
copy. For a payload, take all preparation fact-lineage entries whose target overlaps its full
facts pointer by decoded tokens, plus inherited workflow influence on those targets. Retain the
union of classes, sorted `asserted`, `generated`, `record`, and OR the generated-influence flags.
No contributor gives `classes: []` and `generatedInfluence: false`. A container or mixed output
conservatively carries every contributor's influence, also for a copy of only one of its fields.

Each copied value carries that parent summary. A case fact or evidence copy is affected if its
source overlaps a copied destination; a case parameter is affected on the same rule. Affected
targets include every target of every source in whose scope an affected case parameter lies,
whether or not its request or rule names it, and transitively every target of a source that
declares a source parameter from an affected target. Every affected target retains the parent
summary in workflow reasoning, in addition to its local dialect lineage. If generated influence
is true, the bound dialect's `admits` MUST explicitly include `generated` at each affected fact
and evidence target, as well as admit its ordinary class. Refuse admission before acquisition
otherwise. This conservative rule uses declared dependencies, including unused parameters.
A reviewer's selection cannot convert generated material into `record` or erase its influence.

The published, binding-document and bound digests are separate record members. The binding
document's `dialect` content-binds the published digest. What remains unauthenticated is that the
signed preparation and record came from this published dialect under this binding: two published
dialects differing only in catalog names bind to one bound dialect (RFC 0018 §4.4). The preparation
binds only that bound dialect; its binding is unchanged. Re-expansion checks consistency only.

### 5. Output records and closed sets

An output record is `{outputRecordVersion: 1, payloadDigest, lineage}`; the payload is a separate
object in §1's literal-preserving bytes. Its identity is the envelope's canonical digest, not
the payload digest: duplicate payloads can be distinct records. `lineage` is exactly:

- `workflowDigest`, `execution`, `stage`, `instance`: the workflow digest and three ids;
- `publishedDialectDigest`, `bindingDocumentDigest`, `boundDialectDigest`: digests, with only
  `bindingDocumentDigest` nullable under §4;
- `packDigest`, `releaseDigest`, `preparationDigest`, `auditDigest`: digests of the stage pack,
  frozen release, successful attempt's preparation and exact audit bytes without their newline;
- `outputPointer`, `index`: the declared facts pointer and an integer from 0 to 4095; `one`
  uses index 0, `many` its array index. Together they identify the projected value;
- `rootCaseDigest`: the root case's digest on every output; `caseDigest`: this output's own
  instance's case digest; `parentRecord` and `selectionDigest`, both null for the root and both
  digests for a dependent stage;
- `relation`: exactly the stage's relation; and `influence`: exactly `{classes,
  generatedInfluence}`, the distinct 0 to 3 classes and boolean computed in §4.

All pins agree with the stage and instance, and the payload's literal-preserving bytes equal
the corresponding prepared value's bytes. The successful attempt is the only output-producing
attempt. The full pointer for `many` appends the index token to `outputPointer`; for `one` it
is `outputPointer`. Lineage names the execution **id**, never the enclosing execution record's
digest. These edges are acyclic. Workflow lineage is never appended to preparation lineage or
Core's disposition, whose forms remain closed (dialect §9.3; Core §8.3).

A **closed output set** is the canonical object `{workflowDigest, execution, stage, records}`:
one digest, two ids, and the array of output-envelope digests, at most `limits.maxRecords`.
Records follow instance order (§7), then array index, with no duplicate envelope digest. Its
digest binds the whole offered set, selected or not. Failed instances contribute no outputs,
but remain in the inventory. The set is closed only after every expected instance is terminal;
it is never presented as complete discovery. Every stage, even one with no instances, has a set.

### 6. Selection records

A selection is exactly `{selectionVersion: 1, workflowDigest, execution, upstreamStage,
outputSetDigest, selected, mode, revision}` and the conditional members below. `execution` and
`upstreamStage` are ids; both digest members are digests. `selected` contains 0 to
`limits.maxRecords` distinct output-envelope digests, all in that closed set, in upstream order.
`revision` is an integer from 1 to 16. Revisions increase by one for each replacement selection
of the same execution and upstream stage; the first is 1. The bytes of each revision are retained.

`upstreamStage` names the producing stage whose outputs are offered. `mode` equals that stage's
`selection.mode`. In disposition mode the additional member `rule` equals that stage's
`selection.rule`, and `selected` is exactly every output whose evaluated case's recorded
disposition satisfies it. A dependent stage consumes this selection through `input.fromStage`
and `input.selected` (§3).
In reviewer mode the additional member `review` is exactly `{actor, assertion, at}`: an
installation-local actor string of 1 to 256 UTF-8 bytes, an assertion of 1 to 1024 UTF-8 bytes,
and a timestamp. They are the installation's assertion of a review and its time, not proof of a
real person's identity or intent. An empty selection is explicit, never inferred from silence.
The conditional member `refusal`, when present, is exactly `"limit-exceeded"`: the selection was
refused at admission (§8), remains unconsumed, and blocks its consumers for that recorded reason.

Once consumed by a downstream admission, a selection is immutable. A change writes a new
revision, with a new digest, and a new branch. All consumers within a branch use the same selection
of an upstream stage. Existing children remain attached to their original selection. Branches
share an execution id and unchanged ancestor instances; an execution record closes exactly one
branch, identified by its ordered selection digests, without overwriting earlier branch records.
Changed downstream output sets require new selections before any further children are admitted.

### 7. Execution records, instances and attempts

An execution record is exactly `{executionVersion: 1, workflowDigest, execution, rootCaseDigest,
frozen, instances, outputSets, selections}`. The digest members are digests and `execution` an id.
`frozen` has one entry per stage in document order, exactly `{stage, publishedDialectDigest,
bindingDocumentDigest, boundDialectDigest, packDigest, releaseDigest, runtimeDigest}`. These are
an id and digests, with only the binding nullable under §4. Retain the named documents. The
release pins the same pack, bound dialect and runtime executable as these entries; `runtimeDigest`
names exact executable bytes. No profile, binding, release or runtime substitution is allowed.
Read the release's `packDigest` and `runtimeDigest`, and its embedded `inputMapping`, not a mapping
digest member. Compute `boundDialectDigest` from that mapping's dialect `canon` bytes under its
version's encoding: version 2 writes `provider`, `facts` and `evidence`; version 3 omits those
legacy members. The release form and encoding are pinned by §1; do not normalize the two alike.
A research stage's release form and encoding are pinned when a Runner prepares the kind
([judgment-pack-runner#88][research-preparer]); until then no research stage can be frozen or
verified under §§1 and 7, as §4 requires.

`instances` holds 1 to `limits.maxInstances` entries, ordered by stage, then selected parent
order. Each is exactly `{id, stage, parentRecord, selectionDigest, inputDigest, caseDigest,
state, failure, attempts}`. Ids are unique within the execution. Parent and selection are null
together for the single root instance and otherwise digests. The root's input digest is
`rootCaseDigest`; a dependent input digest is the digest of
`canon({parentRecord, selectionDigest, caseBindings})`,
using the stage's bindings. It commits the projection's inputs even if projection fails.
`caseDigest` is the projected case's digest, null only when projection failed or was never begun.

Every expected instance appears, even if it was cancelled before acquisition. Its terminal state
is `completed-zero`, `completed`, `failed`, `interrupted` or `cancelled`. Completed states
require a successful preparation and evaluation, and respectively zero or one or more outputs.
`completed-zero` is possible only with `many`. An evaluation error is `failed`, never an
empty success. `interrupted` includes uncertain acquisition; `cancelled` records stopped work.
None of these three states emits outputs. Failed projection has state `failed` and no attempts.
`failure` is null except for `failed`, when it is `projection-invalid`, `admission-refused`,
`acquisition-failed`, `preparation-failed`, `evaluation-error`, `output-invalid` or
`limit-exceeded`. Recompute projection, admission, output and bound failures; compare evaluation
errors to the runtime error envelope's `evaluationError.class`, subject to the retention gap below.
Acquisition availability and stopping are installation
assertions, not independently verified events. A successful evaluation with valid in-bound
outputs cannot be recorded as failed without another retained failure of these kinds. A dialect
admission refusal after acquisition is recorded `admission-refused`, the dialect's own code,
not `preparation-failed`.

`attempts` has 0 to `limits.maxAttempts` entries in attempt order. Each is exactly
`{number, state, failure, preparationDigest, auditDigest, runDigest, retry}`. `number` starts at 1
and increments by one. `state` has the instance state's five values. `runDigest` names exact bytes
of a retained run export, including a failure export when no evaluation happened; it is null
exactly when the attempt has no run export. Preparation and audit digests are null exactly when
those artifacts do not exist; completed attempts require both. A failed preparation is not
retained as a valid preparation pin: its inputs and failure
are in the run export, with `preparationDigest: null`. Every referenced valid preparation,
including an unsuccessful attempt's, is checked under §9. `failure` follows the instance rule.
`retry` is null on attempt 1 and otherwise `{actor, at}`, with §6's actor and timestamp bounds,
the installation's explicit retry assertion. Earlier attempts must be failed or interrupted;
only the last may complete; its state and failure equal the instance's. With no attempts the state
is failed, interrupted or cancelled. Acquisitions, including uncertain ones, stay in their exports.
For a run export, read `run.input.preparation` and `run.audit` as dialect §11 specifies, using
the original audit bytes in standard-base64 `run.auditBytes` when present. In export version 2,
take the value bytes of `run.audit` exactly as written, with no re-encoding. Compare the separately
retained preparation and audit with these values; use the preparation's own `verifiedAt`.
The Runner's `docs/MAPPING-V2.md` at `89cf441`, "Release checks, runtime and offline verification",
names the export `{version, releaseDigest, release, run}` and exports a mapped run without audit
bytes, including a failed run, as version 2. "Exact bytes of the audit record" documents
`run.audit` and `run.auditBytes`; `internal/runner/model.go` at that pin names
`run.input.preparation`. Read the Core §8.3 disposition from `run.audit.disposition`, the exact
member read by `internal/runner/mapping_v2_export.go` at the same pin. The runtime's `README.md`,
"Experimental evaluation behavior", at `80a8176` (`v0.32.0`) names the error envelope's
`evaluationError.class` for Core §8.4. Refusals write no audit record under its
`docs/building-with-packs.md`, "Keeping a record of what you decided"; the error class is read
from the error envelope. The reference Runner's `internal/runner/runtime.go` at `89cf441` retains
that envelope in attempt diagnostics but returns no `run.result` on evaluation failure, so its
failure export does not carry that class. The workflow's retention of that envelope remains open.

`outputSets` has one entry per stage in stage order, exactly `{stage, status, records}`. `status`
is `closed` or `blocked`; `records` is the digest array of §5. Its closed-set digest is derived
using the execution's workflow digest and id. `selections` has one entry per stage in that same
order: a selection digest, or null. A stage with consumers may lack a selection only when the
branch ends before review or selection completes. Its consumers are `blocked`, with no instances,
outputs or selection, transitively; a selection carrying `refusal` blocks them in the same way,
with its digest retained in `selections`. A stage with a consumed upstream selection is `closed`,
including an empty selection yielding zero instances. Root is closed. Terminal stages have null
selections.

For each non-blocked dependent stage, reconstruct one expected instance for every selected
parent. Missing, extra, repeated or foreign-parent instances are findings. A consumed selection
cannot justify omitting a child; cancellation reserves that child with its explicit terminal state.
The record distinguishes blocked work, completed-zero and unsuccessful work. A branch is complete
only when all stages are closed, every required selection is consumed and every instance is in a
completed state (`completed` or `completed-zero`).

### 8. Admission, recovery and commitment

The workflow runner admits one logical instance per `(execution, stage, selection digest,
parent-record digest)`, using null for the last two at the root. It stores that key, the input
digest and instance id transactionally. A duplicate with the same input returns the same
instance; changed input is refused. This also holds for shared ancestors across branches. All
selected children are reserved before their stage acquires, or the stage is refused as over
bound without partial admission. A successful selection enters the execution's `selections` only
atomically with reservation of all its direct consumers' children. A bound refusal instead
writes a selection record carrying `refusal: "limit-exceeded"` and retains its digest there,
without reserving children. It is unconsumed and its consumers are blocked. The inventory
survives interruption or cancellation.

A retried acquisition is a new recorded attempt under the same instance, with new retained
responses and receipts, never an offline replay. Uncertain acquisitions are not retried
automatically. A retry in place is allowed from `failed` or `interrupted` only while its output
set is unconsumed. Once consumed, a retry opens a new branch with its own selection digest; the
retried instance is a new instance of that branch, in a new branch-local admission scope; only
unchanged ancestors reuse their existing instances. Earlier branch instances and sets remain
unchanged. A completed instance is not rerun in place; a new execution is required. Verification
recomputes derivations over retained answers and never calls a model or a source. Transactional
admission is a writer rule; an offline reader checks the resulting inventory, not the history of
every side effect. There is no end-to-end exactly-once claim.

The execution record commits outputs and selections without a digest cycle. It is unsigned in
this version. Existing audit signatures cover their own audit bytes and preparation bindings,
not these new envelopes or which published dialect and binding produced the preparation. An
independently held execution digest can expose subsequent replacement, but this version
specifies no authenticated execution commitment. The Runner's journal is unsigned and unchained
(judgment-pack-runner at `89cf441`, `internal/runner/events.go`); its actor verifies no person.

### 9. The workflow verifier

The `workflow-verifier` reads the workflow, its expected digest, one execution record and its
expected digest, and all referenced current-branch artifacts. Other branches and earlier selection
revisions are retained by the writer but not traversed. The reader checks the chosen revision's
form; it cannot establish an unprovided revision history or enforce transactional immutability.
The runtime executable is supplied separately only for optional replay; this reader compares the
release's runtime pin to the independently given runtime pin without claiming to run the binary.
It is also given independently trusted historical profiles and runtime pins, never trusted by
their presence in an export. Digest expectations name bytes to compare, not an authenticated
source. The reader takes no network access or acquisition permission.

The reference phase refuses, in order: byte/aggregate/nesting bounds (`input-over-bound`);
strict JSON and the integer domain scoped by §2 (`input-malformed`); count/string bounds
(`input-over-bound`); versions it cannot read (`version-unread`); closed forms and reference
ordering (`input-malformed`); absent artifacts with non-null pins (`inventory-mismatch`, a
refusal); and dialect kinds it cannot read (`kind-unread`). A binding document whose `dialect`
is not the published digest is `input-malformed` in the form phase, as dialect §4.4 requires.
Within a phase, use workflow order, instance order, attempt order and member code-point order.
Unknown versions, including a stage's `dialect.version`, are `version-unread`, never guessed forms.
Core disposition well-formedness is part of the form phase for a completed evaluation; invalidity
is `input-malformed`. An evaluation error has no disposition.

Next run the dialect's **preparation-verifier** for every referenced preparation, in instance
and attempt order, at its own saved `verifiedAt`, with its acquisitions, trusted profiles and
audit when present. Require binding for completed attempts and every audit given; an unsuccessful
attempt without an audit checks derivation only. Preparation refusals retain their codes and
precede all semantic findings; report the first refusal in instance and attempt order. If there
is none, the first preparation finding maps to `preparation-mismatch`, including the dialect's
`profile-mismatch` and disagreement with audit facts, evidence or citations. Only after every
preparation passes do the checks below run. Influence uses the recomputed lineage, never the
unchecked retained lineage. No freshness check substitutes today's clock.

Then perform checks 1 to 4 in order, stopping at the first finding. Within each check use stage
order, then instance and attempt order; finish one instance's listed clauses before the next.
Within check 1, workflow and execution pins come first, then frozen stage pins, then instance
artifacts; within an instance, `digest-mismatch` precedes `stage-binding-mismatch`. Within
check 3, an earlier instance's `influence-mismatch` precedes a later one's `case-mismatch`.

1. The workflow and record digests and every artifact pin (`digest-mismatch`); frozen published
   dialect expansion against each binding, profile, bound digest and release, including the
   bound profile's class against the published dialect's admission (`stage-binding-mismatch`).
   For a `research` source, check each assigned AI and web profile against the dialect §4.4's
   declared model, capability and class rules under the trusted profiles, and confirm `admits`
   is exactly `["generated"]` at every target of that source. These checks cover every frozen
   stage, with or without a preparation; failures, including the dialect's `profile-mismatch`,
   give `stage-binding-mismatch`. A workflow runner refuses to freeze a stage with incompatible
   research profiles, so no instance is admitted (§4).
2. Each selection's full offered set, revision and exact ordered membership; recompute the closed
   disposition predicate against the retained Core disposition (`selection-mismatch`).
3. Every projected case against its parent and bindings, including expected projection failures
   (`case-mismatch`), then inherited classes, influence and explicit admission
   (`influence-mismatch`).
4. The expected instance inventory, admission keys, attempts, terminal states, selection refusals,
   deterministic bound accounting and stage closure (`inventory-mismatch`); then re-extract all
   outputs, compare payload bytes, order, complete sets, parent/selection references, relation and
   lineage pins (`output-mismatch`). Neither failure nor missing data becomes `[]`.

Predicate checking establishes agreement with the recorded disposition, not its recomputation.
Runtime replay and verification of signatures or checkpoints are separate checks; this class
claims none of them. Checking embedded runs alone is not workflow verification.

The report is one closed JSON object, in the dialect §9.5 serialization, followed by one newline.
A refusal is `{result: "refusal", refusal: C}` and a finding is `{result: "finding", finding: C}`,
C one code above. A reading is exactly `{result: "reading", workflowDigest, executionDigest,
consistency: "agrees", completion, preparations: "agree", authentication: "not-established",
dispositions: "not-replayed", counts}`. `completion` is `complete` or `partial` by §7; `counts`
is `{stages, instances, outputs, selections}`, nonnegative integers within §2's bounds (selections
at most stages). A partial reading is consistency of an explicitly incomplete execution, not
successful completion. Reports are at most 4096 bytes. A program exits 0 for a reading, 1 for a
refusal, 2 for a finding, and 3 with no report when it could not run, including an existing file
that cannot be read or an invalid command argument. A missing pinned artifact is instead the
`inventory-mismatch` refusal above. A library exposes the same outcomes in its own idiom.

A conforming reader gives these answers for every admitted input and all fixtures published
with the specification version its claim names. Its claim names `workflow-verifier`, workflow
version 1, that `specVersion`, and the dialect versions, kinds and shapes the published fixtures
exercise. This is a reader class, not an executor, preparation writer or Core conformance class;
none implies another. No claim is available while this text is Draft or until such fixtures are
published. No fixtures or vectors have been recorded for it.

### 10. What a workflow establishes

A reading establishes that these stages ran over these selections **by their records**,
consistently: the definitions, preparations, offered sets, projections, inventory and relations
agree. A partial reading names incomplete work. Without authentication, rewriting the whole
recorded bundle consistently can yield another reading. No reading establishes good research,
a real person's approval, completeness of discovery, true identities, current policy, correct
model answers, which model answered, or exactly-once execution. Digest pins establish content
identity, not currency. Generated-only admission checks a profile's declared class. The
installation's classification of what its channel actually serves remains a trust assumption; a
reading cannot detect an undeclared model behind a record-class channel (§4; dialect §5.1).

### 11. The two-stage fixture to record

Nothing in this section is recorded yet. The first fixture is a run from the Desk's research
line using two version-3 unbound `operation` dialects, bound by the Runner at import. This remains
the acceptance construction for issue #160's condition 2. An additional research-stage recording
follows fixture 8's `selected-parent-child` plan in
[RFC 0018 §11](../rfcs/0018-dialect.md#11-verifying-a-preparation) beside that demonstration.
Its layout is the workflow bundle below, with fixture 8's `gtm-company-person` and
`work-item-triage` examples as its dialects. It waits until a Runner prepares the kind
([judgment-pack-runner#88][research-preparer]), with its release form and encoding pinned under
§§4 and 7, and the dialect's readers read the contract
([judgment-pack-spec#176][research-readers]). The concrete operation construction to demonstrate is:

[research-preparer]: https://github.com/Judgment-Pack/judgment-pack-runner/issues/88
[research-readers]: https://github.com/Judgment-Pack/judgment-pack-spec/issues/176

- `organisations`: root, `once`, pack and published dialect independently pinned; a case `query`
  parameter supplies an operation request. Platform `research-test`, operation `organisations`,
  shape `http`, record `adapter-http` bind to a generated profile. Its read copies the response's
  `/organisations` to facts `/organisations`. Outputs are that pointer, `many`; this producing
  stage's `selection` is `{mode: "reviewer"}`, with relation `discovered-for`, `output-to-parent`.
  The answer has three synthetic objects with ids.
- `people`: input `{fromStage: "organisations", selected: true}`, `each-selected-record`, its
  own pack and dialect pins; binding `{from: "/id", to: "/organisationId", type: "string",
  required: true}`. That case parameter supplies a request to operation `people` on the same
  platform and shape. Its generated profile's read copies `/people` to facts `/people`;
  outputs are that pointer, `many`, with no `selection` because no stage consumes it; relation
  `person-at-organisation`, `output-to-parent`. The published dialects declare `admits` exactly
  `["generated"]` at `/organisations` and `/people`, respectively, so a record-class binding fails
  dialect §8.2 admission. Both explicitly admit generated influence at every affected target.
- `result` is `people`. A reviewer selects the first and third organisation in upstream order;
  one child returns two synthetic people objects, the other an empty array. The inventory holds
  three instances, one `completed-zero`, five output records and the complete three-record
  offered set. The relation says which organisation was researched, not that employment is true.

A recording carries exactly one branch: one set per stage and only the selection revision that
branch names. Other revisions and branches are retained separately. Its directory contains the
following files; angle-bracket components are ids or decimal attempt/index numbers within the
bounds above, not literal path characters:

- `workflow.json`, `workflow.sha256`, `execution.json`, `execution.sha256`, `root-case.json`;
- `stages/<stage>/pack.json`, `dialect.json`, `binding.json`, `bound-dialect.json`, `profiles.json`
  and `release.json`; the binding file is present exactly when §4 requires it;
- `instances/<instance>/case.json`, and `attempts/<number>/sources.json`, `preparation.json`,
  `preparation.sha256`, `verified-at.txt`, `audit.json`, `audit-signatures.json`, `run.json` under
  that instance; artifacts, including the case, are absent exactly when their pins are null;
- `outputs/<stage>/<instance>/<index>/payload.json` and `record.json`;
- `selections/<stage>/<revision>.json`, `sets/<stage>.json`, `expected-report.json`, `trust.json`
  (declared public test trust material) and `README.md` (recording commands and independent pins).

Each `.sha256` file holds one digest and a newline; `verified-at.txt` holds the preparation's
timestamp and a newline. The preparation's own `verifiedAt` and digest computed from its bytes
govern; these side files must agree and never override them. `workflow.json`, `execution.json`,
selection files, set files and output `record.json` hold their `canon` bytes, with no newline;
so do `dialect.json`, `binding.json`, `bound-dialect.json` and `profiles.json` in their own forms.
`root-case.json`, `case.json`, `payload.json` and `preparation.json` hold the dialect §9.5 bytes,
with no newline. `pack.json`, `sources.json`, `release.json`, `run.json`, `audit.json` and
`audit-signatures.json` and `trust.json` retain original bytes, the audit line without its newline.
`expected-report.json` holds §9's report in §9.5 serialization followed by one newline.

Retain exact requests, answers, salts, receipts and supporting page responses in `sources.json`,
and the runtime and release pins; include no credentials, personal data or executable. Provision
the digest-matching runtime separately for optional offline disposition replay. Trust comes from
the recording protocol, not `trust.json` alone. A verifier must be able to run with acquisition
disabled; replay never asks an AI source to reproduce an answer. Optional chain/checkpoint files
remain separate evidence with their own verifier's report, outside this class's report.

Record variants for a second synthetic installation, preserving workflow/published digests and
changing bindings and releases; disposition selection of one-output cases for matching and
nonmatching outcomes, unresolved, not-applicable and errors; no selection; maximum fan-out and
one over it; missing versus null; duplicate payloads; reordered arrays; `-0` and escaped strings.
Keep independent expected commitments fixed when altering bindings, packs, answers, selections,
revisions or relations, adding an unselected child, omitting or repeating a selected child, or
laundering generated influence. Include a record-class downstream operation parameterised from a
generated payload without generated admission, refused before acquisition, including an affected
case parameter its request never names. Include two siblings of six outputs when ten records
remain, completed in both orders: the second and every later sibling record `limit-exceeded`.
Include interruption after atomic admission, uncertain acquisition, a recorded selection bound
refusal, and retries before and after consumption. Freeze expected reports with the recordings.
This layout supplies no evidence of those runs today.

## Alternatives

- **A standalone companion, chosen.** A definition and records travel independently of a catalog.
  Domain labels are data, so the interpreter needs no organisation or person special case.
- **An Exchange entry program, option B.** This saves no execution work and ties the execution
  contract to a publication container. Extracting its digested program recreates the standalone
  document. The maintainer declined it.
- **No format change; product composition, option C.** Runner jobs and triggers, plus private
  controller code, can serve one installation. A graph can carry a resulting decision downstream.
  Neither defines the reviewed subset, child inventory or output relation portably. The maintainer
  declined C as the standard, leaving it open as a product path that might supply the recording.
- **A pack extension or profile.** The contract spans several packs and prepares fresh cases; it
  neither extends one pack's evaluation nor constrains packs to a domain. A Core extension or a
  profile would put it under a reader that does not acquire or iterate records.

## Compatibility

This amendment leaves workflow version 1's document form unchanged and adds no member. A
research stage uses the existing workflow stage and record forms, with the dialect §4.4's
research binding contract; its outputs still come from prepared facts under §3. Its admission
is conditional: the release form and encoding are pinned when a Runner prepares the kind
([judgment-pack-runner#88][research-preparer]). Until then no research stage can be frozen or
verified under §§1 and 7; the existing release encoding at `89cf441` cannot retain that contract.

Core, the dialect, the graph and the Runner's existing API are unchanged. A standalone pack or
dialect keeps its existing meaning. This RFC defines documents and records, not new endpoints,
trigger kinds or a reinterpretation of a current Runner job. The Runner's `openapi.json` fixes
jobs to releases and names run input, state and audit at `89cf441`; a controller can reuse them.
Workflow admission and retention need implementation of their own.

Output lineage is a new workflow envelope. It is never appended to the dialect's preparation
lineage ([RFC 0018 §9.3](0018-dialect.md#93-lineage)) or
[Core's disposition](../spec/judgment-pack-core.md#83-the-portable-disposition), whose members
are closed. The separation follows the design memo recorded on issue #160, §3, and
`spec/dialect.md` §§8.2 and 9: case values stay asserted, source influence within one preparation
stays as specified, and the workflow adds the check across stages.

RFC 0018 §4.4's preparation binding stays unchanged. Workflow records separately retain the
published dialect's digest, the binding document's digest and the resulting bound dialect's
digest. The binding document content-binds the published digest, but no signature establishes that
the signed preparation and record came from that published dialect under that binding (§4).
The Runner's `docs/MAPPING-V2.md` at `89cf441`, "Release checks, runtime and offline verification",
says audit signatures do not cover the export envelope; they gain no workflow-envelope coverage.

Old readers refuse the new envelope; verifying only its embedded preparations is not workflow
verification. Existing Desk records remain their own form and can be cited as prior evidence,
without inventing selections or receipts during migration. Acceptance and publication will need
their own landing changes and a decision about the fixtures' corpus and version; this Draft
changes neither Core's artifact list nor any conformance corpus.

## Security and privacy

Case bindings disclose only explicitly named values, with a container copy disclosing that
container's descendants. Fresh cases inherit nothing else. A selection cannot cite records outside
the offered set its digest binds; nothing shows that this set is the only one the installation
obtained or offered (§10; dialect §13).
Retaining that set exposes unselected records to holders of the bundle too. The proposed fixture
uses synthetic opaque ids and no personal data. A digest is not an access-control decision.

There is no workflow script. Earlier-stage dependencies and finite bounds constrain fan-out and
resource use; exceeding a bound cannot yield a truncated success. Pack and dialect pins establish
content identity only. Relations remain provenance assertions, not proof of the domain statement
their labels suggest. Generated-only admission at model-served targets refuses record-class
bindings; preserved influence prevents selection from erasing a declared model's contribution.
The installation's classification of what a channel actually serves remains a trust assumption.
Neither admission nor influence establishes the model's correctness.

A reviewer actor is an installation's assertion, not a verified identity. The Runner's
`internal/runner/events.go` at `89cf441` states that its actors name mechanisms or the installation,
never a person, and that the journal is unsigned and unchained. Its progress entries are not an
authenticated execution commitment. The operator can rewrite a consistent bundle; existing audit
signatures and run checkpoints cover only their own subjects. The report keeps consistency,
partial completion, preparation agreement and the absence of workflow authentication explicit.

## Conformance

Specification §9 defines the reader class; no conformance claim is available while this text is
Draft or before fixtures are published. No workflow reader or fixture exists. Section 11 defines
one branch's recording layout, with independent expected commitments and expected reports frozen
from actual recordings. It requires the positive two-stage run, a second installation, disposition
selection, empty outputs, missing and null values, duplicate payloads, ordering and numeric bytes;
negative mutations of pins, selections, inventory and influence; bound and fan-out cases; and
interruption after admission, uncertain acquisition and retries on either side of consumption.
The generated-payload parameter case and deterministic sibling-bound case hold the rules of §§4
and 2 respectively. These are recordings to obtain, not evidence already held.

## Implementation

Implementation follows this order; none of these additions is implemented by this Draft:

1. **Specification:** the companion grammar, `workflow-verifier` reader contract and fixture
   layout first. A Runner reader and a separately written specification reader are two plausible
   implementations. The second should be written from the companion and recorded fixtures without
   sight of the first reader's code, in another language, with its sources and authorship protocol
   recorded. That is a proposed independence protocol, not independence already demonstrated.
2. **Runner:** the interpreter, durable instances, transactional selection admission, retries,
   frozen bindings/releases, workflow export and verification. This is the largest part of the
   cost. Reuse release admission, retained acquisitions, preparation verification and audit replay,
   preserving their separate claims. Version-3 binding precedes the operation acceptance
   demonstration. The additional research recording follows fixture 8's plan beside it, using
   §11's workflow bundle layout, and waits for research preparation, pinned release forms and
   encoding, and readers of the contract as §§4 and 11 require.
3. **Desk:** generic stage review and relation views, pinned definition display and explicit
   reviewer assertions. Record the required run from the research line, retaining the answers
   and the complete offered set, without organisation/person special cases in the Runner.
4. **Exchange:** a versioned workflow entry referencing the standalone definition and its
   fixtures, last, through a revision of RFC 0019. Runtime and Gateway require no semantic change.

This is the allocation in option A's cost paragraph of the design memo recorded on issue #160.
No reader code is added here. Repository tests hold the RFC's Specification equal to the companion,
hold the companion's preface to its title and Status, and keep the Draft out of release bundles.
They are not workflow conformance tests. The round-1 cross-vendor review and the maintainer's
dispositions are recorded on pull request 168; round 2's review and dispositions are the first
and second comments on [pull request 177][round-2].
This text applies both rounds' dispositions and the maintainer's producing-stage selection
rule, with the runtime-form question retained. Acceptance is not claimed.

## Unresolved questions

1. **An authenticated execution commitment.** Which signature or independently retained
   commitment authenticates the closed execution, selections and the published-dialect/binding
   association? The binding document content-binds the published digest, but nothing authenticates
   that the signed preparation and record came from that dialect under that binding (§4).
   Existing preparation binding remains unchanged; reviewer authentication is separate. The record
   has an execution id so a future outer commitment need not introduce a digest cycle.
2. **Published research binding, deferred through operations.** How does a published `research`
   recipe bind to an installation's AI source? This RFC chooses condition 2's operation path and
   defines the construction to record in §11; it does not settle research binding or extend its
   unbound form. The actual two-stage operation demonstration is still missing. What subsequent
   dialect revision will give research sources a portable binding contract remains open.
   *Resolved 2026-10-15, by decision 2 of issue #174:* The dialect §4.4 defines the research
   binding: the binding document assigns AI and any web profiles, all of class `generated`,
   against the published model and capabilities. Section 4 conditionally admits that binding for
   a workflow stage, pending a pinned research-capable release form and encoding. The two-stage
   operation demonstration remains due under §11; the research recording is additional beside it.
3. **Selection beyond one output per evaluated case.** Version 1 permits a closed disposition
   predicate only for `one`. A many-output case judges the collection; per-candidate decisions
   need separately prepared cases. Whether to specify a richer rule or a stage for such decisions
   waits for recordings; no batch disposition stands in for them now.
4. **Joins, recursion and cross-products.** All are excluded from version 1, which admits one
   earlier-stage parent per invocation. Whether any is necessary for portable research, without
   designing a general workflow engine, requires evidence beyond the motivating chain.
5. **A non-terminal result.** Version 1 requires `result` to name a terminal stage. Whether a
   published workflow should expose an intermediate result while other stages continue is open.
6. **Evidence and publication.** Which Desk implementation supplies the acceptance run, and when
   do independently written readers agree on the positive, negative and recovery recordings?
   What specification version and fixture corpus carry their claims? Nothing is recorded yet;
   repository equality and link checks cannot answer these questions.
7. **Identity and conservative influence.** Version 1 uses record-instance identity, with no
   inferred entity deduplication, and carries a container's influence into each copied field.
   Whether narrower field lineage is needed should be decided from recorded cases without
   weakening generated admission or assigning unproved identities.
8. **Pinned runtime forms.** No supplied runtime document at `80a8176` names the audit record's
   disposition member, so its documentary confirmation remains unresolved despite the Runner's
   source reading `disposition` at `89cf441` (§§1 and 7).
   How will a workflow retain the documented `evaluationError.class` error envelope when the
   reference Runner's failure export carries no such envelope (§7)?

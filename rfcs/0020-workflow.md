# RFC 0020: The workflow

- Status: Draft
- Type: Standards track (a companion document of the specification, with a reader conformance
  class; fixtures recorded from a two-stage run)
- Created: 2026-10-15
- Issue: [#160](https://github.com/Judgment-Pack/judgment-pack-spec/issues/160)

This is an open proposal. Its companion text is present for review, normative for nothing.
No implementation or workflow fixture exists. The Type names the evidence to obtain, not evidence
already held. [RFC 0000](0000-rfc-process.md) governs its review and acceptance.

## Summary

A **workflow** declares how one dialect runs for each record selected from another stage's
outputs. Each stage pins its own published dialect and pack, names its input and output
projection, and declares the relation between its outputs and their parent. Selection records
bind the whole offered set and the chosen subset; output records preserve parentage; an execution
record closes the instance inventory, including zero-output and unsuccessful work.

This is option A of the design memo recorded on issue #160: a standalone companion document,
`spec/workflow.md`, with a `workflow-verifier` reader class. The Runner executes, the Desk
reviews, and the Runtime and Gateway keep their existing semantics. Verification establishes
consistency of recorded stages and selections, without authenticating reviewer identity or the
published-dialect/binding-document association. Acceptance needs the recorded two-stage run the
maintainer's decision requires; it does not exist yet.

## Motivation

A pack decides one case. A dialect prepares one case's facts and evidence. Neither says how to
run a second dialect once for each record a reviewer selected from the first one's discovery.
An installation importing that research needs the two dialects and packs by digest, the root
case, the exact offered collection and selected subset, the projection into each child case,
and the relation back to the selected parent. It also needs its own source bindings.

Issue #160 motivates this with organisation discovery followed by people research at selected
organisations, from the Desk's research line (#369 and #371). The design memo recorded on
issue #160, §1, finds that chain to be a motivating requirement, not a demonstrated execution.
The Desk's `web/src/research/run.ts` (judgment-pack-desk) sequences `researchTurn` and
`casesAndCheck` in `AuthoringRun.start`: it researches and checks a candidate pack. Its budgets,
conversation state and sequencing are Desk-private. They do not establish an organisation/person
workflow. Copying a prompt or transcript would leave selection and iteration implicit.

The [judgment graph](0002-judgment-graph.md) is the dataflow between decisions: an outcome
becomes a fact or evidence availability for another evaluation. It supplies neither acquisition
nor record iteration. RFC 0011, named as a graph in the issue, is instead the
[currency-anchor proposal](0011-judgment-currency-anchor.md). Neither substitutes for the missing
contract, and pinning a pack's bytes does not establish that it is current policy.

### Alternatives

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

## Where it lives

On acceptance, `spec/workflow.md` would be a companion document of the specification beside
Core, normative for its reader class only. The text is present now to make the proposal reviewable
and to support a separately written reader. The Specification below and the companion's numbered
sections are held equal, with headings one level apart, as RFC 0018's are.

The Runner interprets the definition, freezes bindings and releases, admits and executes
instances, and retains records. The Desk reviews selections and shows the pinned definitions,
projected cases and relations. These boundaries follow judgment-pack-desk
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
an **instance** prepares and evaluates one case. The Runner interprets the workflow and executes
instances; the Desk reviews selections and displays the pinned definitions. A workflow changes
neither Core evaluation nor the dialect. Its output records are new envelopes around data.

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT** and **MAY** have
their BCP 14 meanings only in capitals. All forms below are closed; every listed member is
required unless expressly conditional. Unknown members, duplicate object names and duplicate ids
are refused. An id is `[a-z][a-z0-9-]{0,63}`. A digest is `sha256:` and 64 lowercase hexadecimal
characters, compared exactly. A timestamp has the form and valid instant of the dialect §1.

JSON is strict as in [the dialect](../spec/dialect.md), §1: one value, well-formed Unicode and
number literals retained. The workflow, selection, output and execution objects use its `canon`
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
Published and bound dialects and binding documents use
the dialect's canonical digests. A release digest uses the existing Runner release-digest recipe
(judgment-pack-runner, `internal/runner/mapping_v2_export.go`, `releaseDigest`): SHA-256 of the
whole retained release object in the dialect §9.5 form. It is not a file-byte digest.

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

Every JSON value here has at most 64 container levels; cases and payloads have at most 32.
The dialect §12 counting convention applies. Every object has at most 4096 members, every array
at most 4096 elements, every decoded string and member name at most 65536 UTF-8 bytes, and every
number literal at most 128 characters. Smaller bounds stated here or by a referenced format win.
The bundle has at most 65536 files. The workflow is at most 262144 bytes; each selection and
output envelope at most 65536; each case and payload at most 1048576; the execution record and
each other artifact at most 8388608. Dialect §12's smaller artifact and combined-input bounds
also apply separately to every preparation, including retained attempts. Counts include empty
containers and unsuccessful work; nothing is truncated to fit. The same bounds hold canonical
bytes and input bytes. A Runner refuses admission before acquisition when a known bound fails;
on an acquired result exceeding a bound it records failure and emits no truncated invocation
outputs. Completed siblings' outputs remain in the stage's closed set with that failure explicit.

### 3. Stages and projected cases

A stage is exactly `{id, dialect, pack, input, execution, caseBindings, outputs, selection,
relation}`. `dialect` is `{version, digest}`: integer version `2` or `3` and the published
canonical digest. `pack` is `{id, digest}`: its Core absolute-URI id, at most 2048 UTF-8 bytes,
and exact-byte digest. Loaded identities MUST match both pins. A mutable version, job id or
catalog name cannot substitute for them. Each stage has its own pins, even when stages share bytes.

The root's `input` is exactly `{root: true}`, `execution` is `once`, and `caseBindings` is `[]`.
It receives the supplied root case once. A dependent stage's `input` is exactly
`{fromStage: S, selected: true}`, where S is an earlier id; its `execution` is
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

`outputs` is `{pointer, cardinality}`. The pointer has the bounds above and resolves in the
prepared **facts document**, not an acquisition or an audit record. `cardinality` is `one` or
`many`: `one` requires an object; `many` requires an array of objects. An empty array succeeds
with zero outputs. An absent value, `null`, a wrong type or a non-object array member fails the
instance; none means an empty array. A many-output invocation evaluates one case about the
collection and supplies records for review, not a disposition for each candidate.

`selection` is `{mode: "reviewer"}`, or `{mode: "disposition", rule: R}`. R is exactly
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
when required, resulting bound dialect and release (§7). Unbound sources are expanded exactly as
the dialect §4.4 specifies. Only `operation` has that unbound form. This version does not extend
it to `research`. A dialect with no unbound source has a null binding-document digest and an
unchanged bound digest; a superfluous binding document is refused as in §4.4.

The two-stage construction in §11 takes the `operation` path of issue #160's condition 2.
Portable binding of a published `research` recipe to an installation's AI source is deferred.
An operation's profile still declares its class: an operation serving generated answers requires
class `generated`. Using the operation kind does not make a model answer a system record.

Copied values remain **case assertions** in the unchanged dialect. The workflow adds a check
outside its preparation: it carries the upstream classes and generated influence across each
copy. For a payload, take all preparation fact-lineage entries whose target overlaps its full
facts pointer by decoded tokens, plus inherited workflow influence on those targets. Retain the
union of classes, sorted `asserted`, `generated`, `record`, and OR the generated-influence flags.
No contributor gives `classes: []` and `generatedInfluence: false`. A container or mixed output
conservatively carries every contributor's influence, also for a copy of only one of its fields.

Each copied value carries that parent summary. A case fact or evidence copy is affected if its
source overlaps a copied destination; a case parameter is affected on the same rule. Every target
of a source declaring an affected parameter is affected, as are the targets of any source that
transitively takes its parameters from those targets. Every affected target retains the parent
summary in workflow reasoning, in addition to its local dialect lineage. If generated influence
is true, the bound dialect's `admits` MUST explicitly include `generated` at each affected fact
and evidence target, as well as admit its ordinary class. Refuse admission before acquisition
otherwise. This conservative rule uses declared dependencies, including unused parameters.
A reviewer's selection cannot convert generated material into `record` or erase its influence.

The published, binding-document and bound digests are separate record members. Nothing today
authenticates the pairing of the first two. The preparation binds only the bound dialect as in
RFC 0018 §4.4; that binding is unchanged. Re-expansion checks consistency, not authentication.

### 5. Output records and closed sets

An output record is `{outputVersion: 1, payloadDigest, lineage}`; the payload is a separate
object in §1's literal-preserving bytes. Its identity is the envelope's canonical digest, not
the payload digest: duplicate payloads can be distinct records. `lineage` is exactly:

- `workflowDigest`, `execution`, `stage`, `instance`: the workflow digest and three ids;
- `publishedDialectDigest`, `bindingDocumentDigest`, `boundDialectDigest`: digests, with only
  `bindingDocumentDigest` nullable under §4;
- `packDigest`, `releaseDigest`, `preparationDigest`, `auditDigest`: digests of the stage pack,
  frozen release, successful attempt's preparation and exact audit bytes without their newline;
- `outputPointer`, `index`: the declared facts pointer and an integer from 0 to 4095; `one`
  uses index 0, `many` its array index. Together they identify the projected value;
- `rootCaseDigest`: the case digest for every stage; `parentRecord` and `selectionDigest`,
  both null for the root and both digests for a dependent stage;
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

`mode` equals the stage's mode. In disposition mode the additional member `rule` equals its rule,
and `selected` is exactly every output whose evaluated case's recorded disposition satisfies it.
In reviewer mode the additional member `review` is exactly `{actor, assertion, at}`: an
installation-local actor string of 1 to 256 UTF-8 bytes, an assertion of 1 to 1024 UTF-8 bytes,
and a timestamp. They are the installation's assertion of a review and its time, not proof of a
real person's identity or intent. An empty selection is explicit, never inferred from silence.

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
errors to the audit or run export. Acquisition availability and stopping are installation
assertions, not independently verified events. A successful evaluation with valid in-bound
outputs cannot be recorded as failed without another retained failure of these kinds.

`attempts` has 0 to `limits.maxAttempts` entries in attempt order. Each is exactly
`{number, state, failure, preparationDigest, auditDigest, runDigest, retry}`. `number` starts at 1
and increments by one. `state` has the instance state's five values. `runDigest` names exact bytes
of a retained run export, including a failure export when no evaluation happened. Preparation
and audit digests are null exactly when those artifacts do not exist; completed attempts require
both. A failed preparation is not retained as a valid preparation pin: its inputs and failure
are in the run export, with `preparationDigest: null`. Every referenced valid preparation,
including an unsuccessful attempt's, is checked under §9. `failure` follows the instance rule.
`retry` is null on attempt 1 and otherwise `{actor, at}`, with §6's actor and timestamp bounds,
the installation's explicit retry assertion. Earlier attempts must be failed or interrupted;
only the last may complete; its state and failure equal the instance's. With no attempts the state
is failed, interrupted or cancelled. Acquisitions, including uncertain ones, stay in their exports.

`outputSets` has one entry per stage in stage order, exactly `{stage, status, records}`. `status`
is `closed` or `blocked`; `records` is the digest array of §5. Its closed-set digest is derived
using the execution's workflow digest and id. `selections` has one entry per stage in that same
order: a selection digest, or null. A stage with consumers may lack a selection only when the
branch ends before review or selection completes. Its consumers are `blocked`, with no instances,
outputs or selection, transitively. A stage with an upstream selection is `closed`, including
an empty selection yielding zero instances. Root is closed. Terminal stages have null selections.

For each non-blocked dependent stage, reconstruct one expected instance for every selected
parent. Missing, extra, repeated or foreign-parent instances are findings. A consumed selection
cannot justify omitting a child; cancellation reserves that child with its explicit terminal state.
The record distinguishes blocked work, completed-zero and unsuccessful work. A branch is complete
only when all stages are closed, every required selection is present and every instance completed.

### 8. Admission, recovery and commitment

The Runner admits one logical instance per `(execution, stage, selection digest, parent-record
digest)`, using null for the last two at the root. It stores that key, the input digest and the
instance id transactionally. A duplicate with the same input returns the same instance; changed
input is refused. This also holds for shared ancestors across branches. All selected children
are reserved before their stage acquires, or the stage is refused as over bound without partial
admission. A selection enters the execution's `selections` only atomically with reservation of
all its direct consumers' children. A bound refusal leaves it unconsumed, with no chosen selection
and blocked consumers in that branch. The inventory is retained on interruption or cancellation.

A retried acquisition is a new recorded attempt under the same instance, with new retained
responses and receipts, never an offline replay. Uncertain acquisitions are not retried
automatically. A completed instance is not rerun in place; a new execution is required.
Verification recomputes derivations over retained answers and never calls a model or a source.
Transactional admission is a writer rule; an offline reader checks the resulting inventory,
not the history of every side effect. There is no end-to-end exactly-once claim.

The execution record commits outputs and selections without a digest cycle. It is unsigned in
this version. Existing audit signatures cover their own audit bytes and preparation bindings,
not these new envelopes or the published-dialect/binding-document association. An independently
held execution digest can expose subsequent replacement, but this version specifies no
authenticated execution commitment. The Runner's journal is unsigned and unchained
(judgment-pack-runner, `internal/runner/events.go`); its actor does not verify a person.

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

Before semantic checks it refuses, in order: byte/aggregate/nesting bounds (`input-over-bound`);
strict JSON and integer domain (`input-malformed`); count/string bounds (`input-over-bound`);
versions it cannot read (`version-unread`); closed forms and reference ordering
(`input-malformed`); and dialect kinds it cannot read (`kind-unread`). It does not report success
after merely checking embedded runs. Within a phase, use workflow order, instance order, attempt
order and member code-point order. Unknown versions are `version-unread`, never guessed formats.

It then checks, in this order, stopping at the first finding:

1. The workflow and record digests and every artifact pin (`digest-mismatch`); frozen published
   dialect expansion against each binding, profile, bound digest and release (`binding-mismatch`).
2. Each selection's full offered set, revision and exact ordered membership; recompute the closed
   disposition predicate against the retained Core disposition (`selection-mismatch`).
3. Every projected case against its parent and bindings, including expected projection failures
   (`case-mismatch`), and inherited classes, influence and explicit admission
   (`influence-mismatch`).
4. The expected instance inventory, admission keys, attempts, terminal states and stage closure
   against the execution record (`inventory-mismatch`).
5. Every referenced preparation using the dialect's **preparation-verifier** checks at its saved
   `verifiedAt`, with its acquisitions, trusted profiles and audit when present. Require binding
   for completed attempts and every audit given; an unsuccessful attempt without an audit checks
   derivation only. Compare facts, evidence and citations with each audit (`preparation-mismatch`).
   Unsupported version or kind propagates as a refusal; other preparation refusals retain their
   code. A preparation finding
   maps to `preparation-mismatch`. No freshness check substitutes today's clock.
6. Re-extract all outputs, compare payload bytes, order, complete sets, parent/selection references,
   relation and lineage pins (`output-mismatch`). Neither failure nor missing data becomes `[]`.

Core disposition well-formedness is required for a completed evaluation; invalidity is
`input-malformed`. An evaluation error has no disposition. Predicate checking establishes
agreement with that recorded disposition, not its recomputation. Runtime replay and verification
of signatures or checkpoints are separate
checks; this class claims none of them. Cross-stage influence may require preparing upstream
facts to perform check 3; its findings still follow the precedence above.

The report is one closed JSON object, in the dialect §9.5 serialization, followed by one newline.
A refusal is `{result: "refusal", refusal: C}` and a finding is `{result: "finding", finding: C}`,
C one code above. A reading is exactly `{result: "reading", workflowDigest, executionDigest,
consistency: "agrees", completion, preparations: "agree", authentication: "not-established",
dispositions: "not-replayed", counts}`. `completion` is `complete` or `partial` by §7; `counts`
is `{stages, instances, outputs, selections}`, nonnegative integers within §2's bounds (selections
at most stages). A partial reading is consistency of an explicitly incomplete execution, not
successful completion. Reports are at most 4096 bytes. A program exits 0 for a reading, 1 for a
refusal, 2 for a finding, and 3 with no report when it could not run, including an unreadable file
or invalid command argument. A library exposes the same outcomes in its own idiom.

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
model answers, or exactly-once execution. Digest pins establish content identity, not currency.

### 11. The two-stage fixture to record

Nothing in this section is recorded yet. The first fixture is a run from the Desk's research
line using two version-3 unbound `operation` dialects, bound by the Runner at import. This is the
operation path, not an unbound research recipe. The concrete construction to demonstrate is:

- `organisations`: root, `once`, pack and published dialect independently pinned; a case `query`
  parameter supplies an operation request. Platform `research-test`, operation `organisations`,
  shape `http`, record `adapter-http` bind to a generated profile. Its read copies the response's
  `/organisations` to facts `/organisations`. Outputs are that pointer, `many`, selection reviewer,
  relation `discovered-for`, `output-to-parent`. The answer has three synthetic objects with ids.
- `people`: input `{fromStage: "organisations", selected: true}`, `each-selected-record`, its
  own pack and dialect pins; binding `{from: "/id", to: "/organisationId", type: "string",
  required: true}`. That case parameter supplies a request to operation `people` on the same
  platform and shape. Its generated profile's read copies `/people` to facts `/people`;
  outputs are that pointer, `many`, selection reviewer, relation `person-at-organisation`,
  `output-to-parent`. Both dialects explicitly admit generated influence at affected targets.
- `result` is `people`. A reviewer selects the first and third organisation in upstream order;
  one child returns two synthetic people objects, the other an empty array. The inventory holds
  three instances, one `completed-zero`, five output records and the complete three-record
  offered set. The relation says which organisation was researched, not that employment is true.

The recording directory contains the following named files; angle-bracket components are ids or
decimal attempt/index numbers within the bounds above, not literal path characters:

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
timestamp and a newline. JSON record files hold the canonical bytes of their own form, no newline.

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
laundering generated influence. Include interrupted admission and uncertain acquisition. Freeze
expected reports with the actual recordings. This layout supplies no evidence of those runs today.

## Evidence

**No workflow implementation or fixture exists.** No verifier has been written for this format,
no two readers have agreed on it, and no vector or conformance claim is made. The acceptance
fixture is a recorded two-stage run from the Desk's research line. The maintainer's decision on
issue #160 explicitly permits the Draft to land without it and requires its layout to be defined.
Specification §11 names those files and the positive, negative, boundary and recovery recordings
to obtain. They are a plan, not generated evidence standing in for a run.

**Prior art to reuse.** Judgment-pack-desk `web/src/research/ledger.ts` defines `SourceRecord`
as a search or page: a request, exact acquisition response, receipt, verification state and
excerpts. In `web/src/research/run.ts`, `researchRecord` writes `researchRecordVersion: '1'`,
pack and check digests, sessions, registries, cases, citations and source responses beside the
authored pack. That research record is useful retained evidence; it is not this workflow's
selection, output or execution record. It supplies neither the demonstrated two-stage chain nor
its closed selection and child inventory. Import must not invent those absent facts.

The Runner's `internal/runner/mapping_v2_export.go` recomputes preparation at retained time
under historical profiles, and can separately rehearse evaluation under a pinned Runtime.
Its `cmd/jpack-runner/main.go` distinguishes verified inputs from verified disposition.
`internal/runner/run_chain.go` binds completed runs to audit bytes and preceding entries;
completion order does not establish a workflow dependency. These are reusable components, not
workflow verification already implemented.

**The prerequisite's standing.** The maintainer's decision records version-3 import/binding as
delivered by judgment-pack-runner #83, merged as `89cf441` and released as the Runner's
`v0.12.0`: the reference Runner reads a version-3 document and binds an unbound source at import
through a binding document. This Draft does not claim to have run that implementation. The first
recording must use that version-3 binder.

**Condition 2's path.** This Draft chooses to demonstrate the chain through `operation` sources.
Specification §11 gives the concrete two-stage construction, including the generated profiles,
projections, reviewer selection and empty child. It is a construction to record, not a recorded
demonstration. It uses the unbound form RFC 0018 §4.4 already defines; portable binding of a
published `research` recipe to an installation's AI source is deferred. Condition 2's empirical
demonstration remains due with the acceptance fixture. Calling a model through an operation does
not change its generated class or require an extension of the dialect.

## Compatibility

Core, the dialect, the graph and the Runner's existing API are unchanged. A standalone pack or
dialect keeps its existing meaning. This RFC defines documents and records, not new endpoints,
trigger kinds or a reinterpretation of a current Runner job. The Runner's `openapi.json` fixes
jobs to releases and names run input, state and audit; a controller can reuse those surfaces.
Workflow admission and retention need implementation of their own.

Output lineage is a new workflow envelope. It is never appended to the dialect's preparation
lineage ([RFC 0018 §9.3](0018-dialect.md#93-lineage)) or
[Core's disposition](../spec/judgment-pack-core.md#83-the-portable-disposition), whose members
are closed. The separation follows the design memo recorded on issue #160, §3, and
`spec/dialect.md` §§8.2 and 9: case values stay asserted, source influence within one preparation
stays as specified, and the workflow adds the check across stages.

RFC 0018 §4.4's preparation binding stays unchanged. Workflow records separately retain the
published dialect's digest, the binding document's digest and the resulting bound dialect's
digest. Recomputing the latter from the former two does not authenticate their association.
The Runner's `docs/MAPPING-V2.md`, "Record signatures", says audit signatures do not cover
the export envelope; they do not acquire coverage of the workflow envelope through this proposal.

Old readers refuse the new envelope; verifying only its embedded preparations is not workflow
verification. Existing Desk records remain their own form and can be cited as prior evidence,
without inventing selections or receipts during migration. Acceptance and publication will need
their own landing changes and a decision about the fixtures' corpus and version; this Draft
changes neither Core's artifact list nor any conformance corpus.

## Security considerations

Case bindings disclose only explicitly named values, with a container copy disclosing that
container's descendants. Fresh cases inherit nothing else. The whole offered output set is bound,
including records not selected: a review cannot silently conceal a different offered collection.
Retaining that set exposes unselected records to holders of the bundle too. The proposed fixture
uses synthetic opaque ids and no personal data. A digest is not an access-control decision.

There is no workflow script. Earlier-stage dependencies and finite bounds constrain fan-out and
resource use; exceeding a bound cannot yield a truncated success. Pack and dialect pins establish
content identity only. Relations remain provenance assertions, not proof of the domain statement
their labels suggest. Explicit generated admission prevents selection from laundering a model's
answer into a record-class fact; it does not establish the model's correctness.

A reviewer actor is an installation's assertion, not a verified identity. The Runner's
`internal/runner/events.go` states that its journal's actors name mechanisms or the installation,
never a person, and that the journal is unsigned and unchained. Its progress entries are not an
authenticated execution commitment. The operator can rewrite a consistent bundle; existing audit
signatures and run checkpoints cover only their own subjects. The report keeps consistency,
partial completion, preparation agreement and the absence of workflow authentication explicit.

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
   preserving their separate claims. Version-3 binding precedes the recording; the operation path
   avoids making research-source binding an incidental feature of the workflow format.
3. **Desk:** generic stage review and relation views, pinned definition display and explicit
   reviewer assertions. Record the required run from the research line, retaining the answers
   and the complete offered set, without organisation/person special cases in the Runner.
4. **Exchange:** a versioned workflow entry referencing the standalone definition and its
   fixtures, last, through a revision of RFC 0019. Runtime and Gateway require no semantic change.

This is the allocation in option A's cost paragraph of the design memo recorded on issue #160.
No reader code is added here. The sole new repository test holds the RFC's Specification equal
to the companion; it is not a workflow conformance test. The cross-vendor adversarial review and
the maintainer's dispositions required by RFC 0000 and the interim review regime remain work for
the pull request. Neither that review nor acceptance is claimed in this draft.

## Unresolved questions

1. **An authenticated execution commitment.** Which signature or independently retained
   commitment authenticates the closed execution, selections and the published-dialect/binding
   pairing? Nothing authenticates that pairing today. Existing preparation binding remains
   unchanged, and human reviewer authentication is a separate question. The proposed record has
   an execution id so a future outer commitment need not introduce a digest cycle.
2. **Published research binding, deferred through operations.** How does a published `research`
   recipe bind to an installation's AI source? This RFC chooses condition 2's operation path and
   defines the construction to record in §11; it does not settle research binding or extend its
   unbound form. The actual two-stage operation demonstration is still missing. What subsequent
   dialect revision will give research sources a portable binding contract remains open.
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

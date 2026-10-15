# The workflow

## Status

This is the proposed companion text of [RFC 0020](../rfcs/0020-workflow.md), a Draft. It is
normative for nothing. Acceptance would place it beside Core, with the `workflow-verifier`
reader class defined below. No workflow implementation, recorded fixture or conformance claim
exists. The two-stage run in §11 is a recording requirement, not evidence already obtained.

## 1. Terms and canonical forms

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

## 2. The workflow document and bounds

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

## 3. Stages and projected cases

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

## 4. Bindings and influence across stages

Before the root runs, the installation freezes each stage's published dialect, binding document
when required, resulting bound dialect and release (§7). Unbound sources are expanded exactly as
the dialect §4.4 specifies. Only `operation` has that unbound form. This version does not extend
it to `research`. A dialect with no unbound source has a null binding-document digest and an
unchanged bound digest; a superfluous binding document is refused as in §4.4.

The two-stage construction in §11 takes the `operation` path of issue #160's condition 2.
Portable binding of a published `research` recipe to an installation's AI source is deferred.
An operation's profile declares the installation's classification of its channel. A published
dialect whose source serves a model's answers MUST declare `admits` exactly `["generated"]` at
every target of that source. A record-class binding then fails the dialect's §8.2 admission at
preparation; §9's check 1 confirms the bound profile's class against that published admission.
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

## 5. Output records and closed sets

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

## 6. Selection records

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

## 7. Execution records, instances and attempts

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

## 8. Admission, recovery and commitment

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

## 9. The workflow verifier

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
is none, the first preparation finding maps to `preparation-mismatch`, including disagreement
with audit facts, evidence or citations. Only after every preparation passes do the checks below
run. Influence uses the recomputed lineage, never the unchecked retained lineage. No freshness
check substitutes today's clock.

Then perform checks 1 to 4 in order, stopping at the first finding. Within each check use stage
order, then instance and attempt order; finish one instance's listed clauses before the next.
Within check 1, workflow and execution pins come first, then frozen stage pins, then instance
artifacts; within an instance, `digest-mismatch` precedes `stage-binding-mismatch`. Within
check 3, an earlier instance's `influence-mismatch` precedes a later one's `case-mismatch`.

1. The workflow and record digests and every artifact pin (`digest-mismatch`); frozen published
   dialect expansion against each binding, profile, bound digest and release, including the
   bound profile's class against the published dialect's admission (`stage-binding-mismatch`).
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

## 10. What a workflow establishes

A reading establishes that these stages ran over these selections **by their records**,
consistently: the definitions, preparations, offered sets, projections, inventory and relations
agree. A partial reading names incomplete work. Without authentication, rewriting the whole
recorded bundle consistently can yield another reading. No reading establishes good research,
a real person's approval, completeness of discovery, true identities, current policy, correct
model answers, or exactly-once execution. Digest pins establish content identity, not currency.
Generated-only admission checks a profile's declared class. The installation's classification
of what its channel actually serves remains a trust assumption; a reading cannot detect an
undeclared model behind a record-class channel (§4; dialect §5.1).

## 11. The two-stage fixture to record

Nothing in this section is recorded yet. The first fixture is a run from the Desk's research
line using two version-3 unbound `operation` dialects, bound by the Runner at import. This is the
operation path, not an unbound research recipe. The concrete construction to demonstrate is:

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

# The workflow

## Status

This is the proposed companion text of [RFC 0020](../rfcs/0020-workflow.md), a Draft. It is
normative for nothing. Acceptance would place it beside Core, with the `workflow-verifier`
reader class defined below. No workflow implementation, recorded fixture or conformance claim
exists. The two-stage run in §11 is a recording requirement, not evidence already obtained.

## 1. Terms and canonical forms

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

## 3. Stages and projected cases

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

## 4. Bindings and influence across stages

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

## 5. Output records and closed sets

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

## 6. Selection records

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

## 7. Execution records, instances and attempts

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

## 8. Admission, recovery and commitment

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

## 10. What a workflow establishes

A reading establishes that these stages ran over these selections **by their records**,
consistently: the definitions, preparations, offered sets, projections, inventory and relations
agree. A partial reading names incomplete work. Without authentication, rewriting the whole
recorded bundle consistently can yield another reading. No reading establishes good research,
a real person's approval, completeness of discovery, true identities, current policy, correct
model answers, or exactly-once execution. Digest pins establish content identity, not currency.

## 11. The two-stage fixture to record

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

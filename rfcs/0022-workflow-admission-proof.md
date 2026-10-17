# RFC 0022: Retained workflow admission proofs

- Status: Draft
- Type: Standards track, a proposed amendment to the Draft workflow contract
- Created: 2026-10-17
- Issue: [#209](https://github.com/Judgment-Pack/judgment-pack-spec/issues/209)

This is a contract proposal for review, not an adopted amendment. It changes neither
[RFC 0020](0020-workflow.md), its `spec/workflow.md` companion, nor any implementation or
conformance corpus. It now proposes explicit version-2 forms, transitions and byte construction
for the earlier membership, serialization and fork gaps. Those rules still require complete
operation/research recordings and independent implementation agreement before adoption. The
workflow remains Draft and normative for nothing.

## Summary

Retain public accounting epochs so an offline reader can independently check a workflow's
aggregate-byte admission refusals. An epoch binds the proposed selection and instance identities,
or the attempts being admitted, to the preceding closed accounting state. The reader derives
candidate files from retained, validated inputs and measures their actual bytes. It does not
accept a writer's asserted byte totals, baseline file list or private transition history.

Every explicit retry starts a new epoch. Earlier refusals remain checked against their own
prefixes, even when an earlier sibling later retries in place. Output accounting within a group
follows stage, selected-parent and output order, independently of completion order. This proposes
an epoch scope for the workflow's stage cutoff; it does not claim unchanged workflow semantics.

Proof bytes are ordinary supplied bundle bytes. The complete final proof, retained execution
artifacts and verification auxiliaries still have to fit the actual branch byte and file bounds.
If a mandatory proof or refusal recording cannot fit, recording is unavailable; that is not a
valid recorded `limit-exceeded` refusal.

## Problem

RFC 0020 requires an independent reader to recompute admission failures, counts actual supplied
file bytes, reserves selected children atomically, and orders output accounting independently of
completion. Its final branch does not retain enough information for two byte-only cases.

A refused selection has no admitted children. The reader cannot infer the writer's prospective
instance IDs, whose lengths affect serialized execution and lineage bytes. Fixing a private
writer's allocator in the reader would neither recover another writer's choice nor establish
interoperability.

An evaluated instance can retain a valid preparation and audit while its outputs are refused
for aggregate bytes. Later unrelated artifacts and retries may appear in the final branch. Using
all final files as the earlier baseline can make a false refusal appear justified. Omitting
unspecified files or accepting an asserted earlier total has the opposite problem: the writer
chooses the answer the reader is supposed to check.

Two realistic uses expose both gaps:

- A reviewed organisation-discovery result supplies two selected parents to a people-research
  stage. Two installations choose different valid child IDs, one short and one descriptive.
  Their projected cases agree, but their complete admission candidates have different byte
  lengths. A boundary recording needs the actual proposed IDs, not a guessed allocator.
- Two selected organisations produce sibling research instances A and B. A's first attempt
  fails; B retains a successful evaluation but its outputs are refused for bytes. The reviewer
  explicitly retries A before consuming the stage's set. A's new acquisitions and attempt must
  not enter B's earlier baseline, and B must remain failed until its own explicit retry.

This is a portable accounting contract between writers and readers. A product-only journal can
help one writer recover, but an offline reader cannot rely on its schema, scheduling or custody.
A profile or Core extension cannot supply missing workflow instance identities and accounting
order without defining the same cross-stage contract elsewhere.

## Evidence

[Issue #209](https://github.com/Judgment-Pack/judgment-pack-spec/issues/209) records these gaps
against RFC 0020 §§2, 8 and 9. It calls for long and short prospective IDs, later unrelated
artifacts, opposite sibling completion orders, a forged refusal when the candidate fits, and
equal contents at separate paths. Those are required cases to obtain, not recorded fixtures.

Runner at
[`a94513de3cffd07a14c2fb07603452d5147f352d`](https://github.com/Judgment-Pack/judgment-pack-runner/commit/a94513de3cffd07a14c2fb07603452d5147f352d)
contains a private experimental workflow driver and offline consistency reader. Its
[`workflow_recording.go`](https://github.com/Judgment-Pack/judgment-pack-runner/blob/a94513de3cffd07a14c2fb07603452d5147f352d/internal/runner/workflow_recording.go)
measures actual recording paths rather than deduplicated stored blobs. Its
[`workflow_read_inventory.go`](https://github.com/Judgment-Pack/judgment-pack-runner/blob/a94513de3cffd07a14c2fb07603452d5147f352d/internal/runner/workflow_read_inventory.go)
checks terminal inventory without assuming writer-generated IDs and returns an operational error
for byte-only refusals it cannot prove. It does not issue a reading for those cases.

The implementation's
[`draft-workflow.md`](https://github.com/Judgment-Pack/judgment-pack-runner/blob/a94513de3cffd07a14c2fb07603452d5147f352d/docs/design/draft-workflow.md)
states its private status and the remaining byte-proof limitation. Driver and reader tests include
synthetic operation-based organisation/selected-people execution, interruption and explicit retry,
retained attempts and per-attempt signatures. They are implementation experience, not a public
workflow API, a Desk acceptance recording, proof of this proposal, or conformance evidence.

RFC 0020 currently pins Runner `66e264e1e44f665e52b056be1b70864a27927338` for retained encodings
and Runtime `v0.34.0` at `785ea58927255b775a774e29952c560591429cd3`. This proposal changes neither
pin. No released component is claimed to emit or verify the proposed epochs. No independent
reader agreement or workflow conformance fixture establishes this proposal. The accounting
experiment described under Conformance is narrower: it exercises synthetic control bytes and
byte-boundary counterexamples, not a real workflow run.

## Specification

This section proposes a closed accounting profile for review. It is not adopted text. The
version-1 workflow in RFC 0020 remains unchanged; a writer must not emit this profile while
advertising version 1. The names and algorithms below settle the three earlier design gaps in
this proposal, subject to recordings, implementation agreement and review.

### 1. Versions, subject and limits

The proposed workflow has RFC 0020's document form with `workflowVersion: 2`. Its execution has
RFC 0020's execution form with `executionVersion: 2` and one additional required member,
`admissionProofDigest`. That member is the canonical digest of `admission-proof.json`. Selection
and output-record versions remain 1. The proof's `admissionProofVersion` is integer 1. A reader
that does not implement these selectors returns `version-unread`; it never invents a proof for
a version-1 execution. Version-1 and version-2 records cannot share a workflow digest.

The proof belongs to one execution and its retained branch history. Its root is exactly:

```text
{admissionProofVersion, workflowDigest, execution, rootCaseDigest,
 frozenDigest, rootInstance, epochBlocks}
```

The digests, ids, timestamps, strict JSON and `canon` encoding are those of RFC 0020 §1.
`frozenDigest` is the digest of `canon(execution.frozen)`; `rootInstance` names the one root
instance. All frozen stage pins, published and bound dialects, binding documents, profiles,
releases, packs and Runtime pins must pass their existing checks. None becomes trusted by being
named in the proof. Cases, payloads, preparations and raw retained artifacts keep their distinct
serialization domains from RFC 0020; they are not normalized to the proof's form.

`epochBlocks` contains 1 to 32 arrays, each containing 1 to 4096 epochs; every array except the
last is full. Epochs are numbered consecutively from 1 after flattening. The canonical proof and
its supplied bytes are each at most 8 MiB. All of RFC 0020 §2's container, string, nesting and
integer limits also apply. These are proposed format ceilings, not an increase to `maxBytes`.
Reaching a proof ceiling can make an operation unrecordable even when its other files would fit.

The declared workflow limits apply to the entire retained history of this branch:

| Limit | Count |
| --- | --- |
| `maxInstances` | Every distinct reserved instance id, including retired, failed and cancelled instances |
| `maxRecords` | Every admitted output envelope, including retired outputs |
| `maxAttempts` | Begun attempts per instance id, including interrupted and cancelled attempts |
| `maxBytes` | Actual bytes at every required recording path, plus all final supplied auxiliaries |
| File ceiling | Actual supplied paths, at most 65536 |

Retirement releases none of these capacities. Equal contents at different paths count separately.
Paths themselves are not charged as file contents; ids appearing inside JSON are charged through
those serialized bytes. The active execution and report counts describe the current branch view,
which can be smaller than its retained history. Limits never use those smaller active counts.

### 2. Epoch forms and prefixes

Every epoch has exactly `number`, `previousProofDigest`, `kind`, and the additional members in
the table below. Unknown members are refused. The first epoch has kind `root`, which occurs
exactly once. Every later epoch follows a closed epoch; only the last epoch may be open.

| `kind` | Additional required members |
| --- | --- |
| `root` | none |
| `selection` | `upstreamStage`, `revision`, `selectionCoreDigest`, `childIds` |
| `fork` | `upstreamStage`, `revision`, `selectionCoreDigest`, `childIds` |
| `group` | `reservation`, `starts`, `deferred`, `cancelled`, `results` |
| `retry` | `start`, `results` |

`reservation` is an earlier root, admitted selection or admitted fork epoch number. It names
the root or the complete direct-consumer reservation made there. A rejected selection reserves
nothing. A group cannot refer to a reservation whose instances have been retired.

A begin entry is exactly `{instance, number, retry}`. `number` is the next attempt number;
`retry` is null for a first attempt and otherwise exactly RFC 0020 §7's `{actor, at}` assertion.
A cancel entry is exactly `{instance, actor, at}`, using those same actor and timestamp bounds.
`starts` and `cancelled` contain these entries; `deferred` contains instance ids. Each array has
at most 4096 elements, with no repetition, and follows the reservation's stage/parent order.
The membership rules in §4 determine their complete partition, not a caller-supplied inventory.

`results` contains at most one observation per begin entry, in `starts` order, or at most one
for a retry. It is a proper prefix while the epoch is open and is complete when it is closed.
Root, selection and fork epochs are atomic and always closed. An open epoch admits no following
epoch and no downstream selection. A partial export may end at an open epoch, but must say it
is partial; reading it does not authorize acquisition or resume anything.

For a root, selection or fork, P(k) is the canonical proof through epoch k. For a group or retry,
P(k,j) includes its complete fixed plan and only its first j result observations. Repack blocks
by the same full-block rule at every prefix. P0 is the same root with `epochBlocks: []`; it is
only a digest preimage, not a valid export. `previousProofDigest` in epoch k names the preceding
closed prefix. No epoch contains its own digest, an execution-record digest, a counterfactual
candidate hash or an asserted byte total.

The proof prefix is serialized and hashed before materializing a control file that names it.
The same prefix bytes are used for both the acceptance and refusal candidate at a decision.
Future observations, later epochs and finalization files cannot enter an earlier prefix.
Hash linkage asserts a declared accounting sequence, not authentic wall-clock history.

### 3. Root and selection reservation

The root epoch materializes the frozen stage files, root case at both its required paths, one
root instance and all empty sets. The root instance has its given id, stage, root input/case
digest, null parent and selection, state `interrupted`, null failure and no attempts. The root
set is `closed`; other stages are `blocked`. Every execution selection is null. Include the
current proof and all control side files in this initial candidate. It must fit before any
acquisition. There is no root-refusal carrier that omits mandatory root material: failure to
record this state is recording unavailable (§8).

A selection epoch requires a closed producing stage with no open work and an unconsumed
selection. Its revision is 1 initially, otherwise exactly one greater than the greatest retained
revision for that stage, at most 16. Its offered set is reconstructed at this epoch. Check the
review/disposition form, full set and ordered selected membership under RFC 0020 §6. All prior
revisions named by proof epochs remain retained, including refused revisions.

Read `selections/<upstreamStage>/<revision>.json`. Remove `refusal` if present, and take the
canonical digest of that core. It must equal `selectionCoreDigest`. No other member is removed
or defaulted. The proof does not name the refusal-bearing digest before deciding whether the
reservation fits. Acceptance uses the core selection and its digest; refusal adds exactly
`refusal: "limit-exceeded"` and pins the digest of that complete selection instead.

The required child slots are all direct consumers in workflow order, each over the complete
selected-parent order. If their count plus the number of retained reserved identities exceeds
`maxInstances`, `childIds` must be null. This is the only no-allocation form. It derives a count
refusal before creating ids or projected cases. Otherwise `childIds` is an array with exactly
one valid id per slot, all distinct and fresh across the entire retained proof history. This
excludes the root id and every earlier prospective id, including ids from refused selections
that never reserved an instance. Those refused names are unavailable for reuse but do not
consume `maxInstances`; only reserved identities count toward that limit. An empty selection
has `childIds: []`, never null. No arbitrary allocator is assumed by the reader.

Derive every child's input digest, projection, inherited influence and admission from the
retained selected payload, stage bindings and frozen definitions. A projection failure reserves
a `failed`/`projection-invalid` instance with no case or attempt. A derived pre-acquisition
admission failure reserves a `failed`/`admission-refused` instance with its case and no attempt.
Every other child is `interrupted`, with its case, null failure and no attempts. Failed slots
are part of the atomic reservation and its instance count; they do not disappear from it.

First check the count refusal above, then projected-case local bounds, then the complete
reservation's file/byte bounds. A projected case exceeding its local encoding bound makes the
whole selection a bound refusal; it is not retained as an oversized case. Otherwise build the
complete acceptance candidate: all children and cases, the core selection, updated execution,
all updated sets, the proof and side files. Consumers become closed, including zero-instance
consumers of an empty selection. Their own unselected descendants stay blocked.

If this candidate fits, admit all children together. If a bound fails, reserve none, retain the
refusal-bearing selection, and keep all direct consumers and descendants blocked. Materialize
and measure that complete refusal candidate too. If it cannot fit, recording is unavailable;
a failed candidate alone is not proof that a refusal carrier can be exported. Local/count
failures need their own derivation, not a fabricated aggregate-byte total.

### 4. Group membership, begins and recovery

For a group, derive the eligible slots from its reservation at the preceding closed prefix:
they are exactly the still-active instances with state `interrupted` and no attempts. Derivable
projection/admission failures and previously settled instances are carried unchanged. The
`starts`, `deferred` and `cancelled` arrays must partition all eligible slots exactly, without
overlap or omission. `starts` or `cancelled` must be nonempty; a no-op defer-only epoch is invalid.

Deferred slots remain interrupted with no attempt. Cancelled slots become cancelled with no
attempt. Only deferred slots may be explicitly resumed by a later group. A pre-attempt stop
therefore does not invent an acquisition attempt or consume its attempt allowance.

Every `starts` or `cancelled` member requires its stage's offered set to be unconsumed at the
preceding closed prefix. This applies to a first begin as well as a resumed deferred slot;
an empty consumed selection also freezes its producing stage. Eligible slots in consumed
stages must remain in `deferred`, unchanged, when another stage from the same reservation is
started or cancelled. Starting or cancelling such a child instead requires the affected-stage
fork in §6; a consumed root requires a new execution. A later first begin cannot extend an
offered set already used by downstream children.

Each start commits the existing interrupted attempt stub: next number, null failure and all
artifact pins null, with its declared retry assertion. Its instance becomes interrupted with
null failure. All starts are committed atomically, in canonical order, before any group member
may acquire. Materialize P(k,0) with these stubs and all deferred/cancelled decisions and check
the complete byte/file bounds first. If that cannot fit, no begin is committed and no acquisition
is authorized. The operation is unrecordable, not an output or selection refusal.

“Begun” means this durable local commitment, not proof that a remote call occurred. A crash just
after committing begins can therefore leave interrupted attempts even when no call was made.
This preserves uncertainty rather than inferring a safe replay from absent receipts.

Acquisition may run concurrently after this commitment. Result observations are committed in
the fixed starts order, regardless of arrival order. A later received result stays in durable
custody until its turn. It cannot be charged to an earlier result's prefix. It must not be lost
on cancellation, crash or overflow; custody outside a portable export remains honest custody,
not a valid export of an omitted result.

Recovery makes no acquisition. It closes each remaining begun slot using all available retained
material, recording uncertainty as interrupted. A complete valid evaluation already received
must be processed as such, even if cancellation arrived later. A later response to an already
closed uncertain attempt stays separately retained; it cannot rewrite a sealed epoch or trigger
a new attempt automatically. A fresh explicit retry is a separate action with new receipts.

A retry epoch names exactly one active, failed or interrupted instance whose offered set is
unconsumed. It must already have at least one begun attempt; a never-begun deferred slot uses a
group instead. The next number must fit `maxAttempts`, earlier attempts remain unchanged, and
the explicit retry assertion is required. Projection/admission failures with no attempt cannot
be repaired by retrying identical frozen inputs. A completed or cancelled instance is ineligible.
The same begin, result and byte rules apply. Other failed siblings are not retried or changed.

### 5. Result observations and cutoff precedence

An observation is exactly:

```text
{instance, number, state, failure, runDigest, preparationDigest,
 auditDigest, evaluationErrorDigest, auditSignaturesDigest}
```

Its identity must match the next begin slot. `state` is `evaluated`, `failed`, `interrupted`,
`cancelled` or `suppressed`. `failure` is null except for `failed`, where it is
`acquisition-failed`, `preparation-failed`, `admission-refused` or `evaluation-error`.
All five artifact members are digests or null, with exactly the retained-file and phase
relationships of RFC 0020 §7 and §7 below. A non-null signature sidecar requires an audit.
These pins describe what was received; they do not contain a writer's output admission choice.

A complete valid audit and preparation require `evaluated`, null failure and their non-null
pins. A complete Core evaluation-error envelope requires `failed`/`evaluation-error`, its
non-null pin and no audit. Other failures must agree with the existing retained run/preparation
checks; only acquisition availability and stopping remain installation assertions. An interrupted
or cancelled observation cannot conceal a complete valid evaluation or Core error. Invalid or
contradictory observations are findings, not permission to discard bytes.

The pin/phase relationships are explicit:

| Observation | Required phase relationship |
| --- | --- |
| `evaluated` | Run, valid preparation and audit present; no evaluation-error artifact; run state completed and its result disposition agrees with its audit |
| `failed` / `evaluation-error` | Failed run, valid preparation and complete Core error present; no audit |
| `failed` / `preparation-failed` or `admission-refused` | Failed run present, no valid preparation or audit; the retained preparation inputs independently derive the stated failure |
| `failed` / `acquisition-failed` | No valid preparation, audit or Core error; any run is failed; absent run is an installation availability assertion |
| `interrupted` or `cancelled` | No complete audit or Core error; any run agrees with that state; a valid partial-phase preparation may be retained |
| `suppressed` | All artifact pins null; the stage's earlier cutoff in this epoch is independently established |

A preparation, audit or Core-error pin requires a run pin. Signature bytes require the audit
pin and retain their existing sidecar form/bounds. If a run embeds a signature sidecar, its exact
value bytes must agree with the separately retained sidecar and its observation pin. Without a
run, interrupted/cancelled observations have no other artifact pins. An ordinary invocation
failure without a complete Core error stays interrupted, as RFC 0020 §7 requires.

For `evaluated`, derive the declared output pointer and cardinality. Bad output shape gives
`failed`/`output-invalid`, retaining the attempt material and emitting no output. A valid shape
produces either completed-zero or a complete ordered proposal of output payloads and envelopes.
Its disposition is retained as evaluated; this proof does not replay Core.

At each observation, first add the actual received attempt files and the current proof prefix.
Then apply this order:

1. Retain a derived phase/output-shape failure, interruption or cancellation with its own state.
2. For a valid output proposal, apply an already established cutoff for that stage in this epoch,
   if any: emit no outputs and derive `failed`/`limit-exceeded`.
3. Otherwise construct the complete acceptance candidate, including every proposed output,
   changed execution/set file, proof prefix and side file. If all local and aggregate bounds fit,
   accept the whole proposal. Never truncate it.
4. If a bound fails, construct the complete no-output `failed`/`limit-exceeded` candidate.
   It must itself fit. This establishes the cutoff for that stage in this epoch.
5. If the actual received material or necessary failure carrier cannot fit, recording is
   unavailable. It is not a valid portable bound refusal.

The cutoff does not relabel an existing projection/admission failure, a stop or an acquisition,
preparation or evaluation failure. It suppresses later valid output proposals. A begun slot that
has not acquired may use `suppressed` with every artifact pin null and null failure only when
an earlier member has already established that stage's cutoff in this epoch; its derived attempt
state is failed with limit-exceeded. This is the sole no-run cutoff form. Received material must
instead be retained under its actual observation, even if its valid outputs will be suppressed.

This narrows RFC 0020 §2's “every later instance” rule explicitly. Each new epoch starts with no
cutoff. Earlier failed siblings retain their own original cutoff/refusal evidence until an
explicit action affects them. Later retries cannot enlarge an earlier prefix to make a false
old refusal appear valid.

### 6. Forks and unchanged work

A fork epoch replaces a consumed selection of an active producing stage U. Its fields and
selection checks match §3, except that the preceding selection must be consumed. The new core
selection uses the next retained revision and U's unchanged complete offered set. Even choosing
the same parents again changes the revision and selection digest.

Apply this exact affected-stage rule before evaluating the new reservation:

1. Compute U's strict descendants through workflow `input.fromStage` edges.
2. Preserve every active instance, selection and output outside that set, including unaffected
   sibling stages. Preserve U's instances and offered set, but replace its selection.
3. Retire all active descendants. Clear their active selections and sets; they are blocked
   until newly admitted. Retain their immutable files and all earlier proof epochs.
4. Reserve every direct consumer of U atomically under the new selection with fresh ids across
   retained history, using §3. Further descendants stay blocked. A bound refusal leaves the
   new branch's consumers blocked, with the complete refusal and history retained.

No caller chooses an arbitrary ancestor subset. Preserving only ancestors would lose unaffected
sibling instances that an unchanged earlier selection had reserved atomically. This proposal
therefore replaces RFC 0020 §8's “only unchanged ancestors” with “all unaffected instances.”
Retired instances remain historical evidence; they are never silently attached to the new
selection or presented as its results.

A consumed retry of a child requires this fork at its upstream producing stage, followed by an
explicit start for the new child. All direct-consumer instances are new, including collateral
siblings; their old results remain historical. No acquisition follows merely from creating a
fork. A consumed root retry requires a new execution, because its null-parent/null-selection
admission key otherwise collides. A completed instance cannot itself be a retry target. A
reviewed replacement selection can create a new child for a previously processed parent; starting
that child is a separately approved invocation, and the old completed instance stays immutable.

A new branch is the parent's complete checked closed prefix plus the fork epoch. It retains
every earlier required immutable artifact at its original path, including retired descendants
needed to reconstruct old refusal baselines. No auxiliary file or unrelated directory is imported
as history. Old execution and set control snapshots are reconstructed, not supplied as duplicate
files. The original branch's export and digest remain unchanged; the new export contains its
extended proof and its newly reconstructed active controls.

Forking frees no retained byte, file, instance, record or attempt budget. A caller needing a new
budget starts a new execution with new explicit acquisition approval; it cannot claim reused
history was verified while omitting the files needed to check it. This is a deliberate cost of
retaining independently checkable refusals, rather than a hidden baseline exemption.

### 7. Exact recording construction and measurement

Maintain two derived values while replaying the proof: the active logical execution state and
the immutable retained-file map. Neither is accepted from the writer as a baseline inventory.
Start with the frozen root inputs. Each validated epoch adds only the artifacts required by
that transition; a later retry, fork or selection never removes an earlier required immutable
path. A second value at an immutable path is invalid. Active control files are replaced once at
their fixed paths, never counted together with virtual historical versions of themselves.

At each candidate, materialize this closed path table. All conditional presence follows pins
or the transition; a writer cannot omit a large side file or add arbitrary files to the basis.

| Path | Exact bytes and presence |
| --- | --- |
| `workflow.json` | Workflow `canon` bytes |
| `workflow.sha256` | Its digest followed by one LF |
| `root-case.json` | Root case in dialect §9.5 bytes |
| `stages/<stage>/pack.json`, `release.json` | Original retained bytes under the frozen pins; release digest still uses the pinned typed encoding |
| `stages/<stage>/dialect.json`, `bound-dialect.json`, `binding.json` | Their declared canonical forms; binding present exactly when required |
| `stages/<stage>/profiles.json` | `canon` of the frozen release's decoded `inputProfiles`, or `[]` if absent |
| `instances/<id>/case.json` | Derived case in dialect §9.5 bytes when its pin is non-null; root duplicates the root case at this distinct path |
| `instances/<id>/attempts/<n>/run.json` | Exact retained run bytes when `runDigest` is non-null |
| `.../sources.json` | Exact JSON value span at `run.input.source.sources`, or the two bytes `{}` when absent; present exactly with that run |
| `.../preparation.json` | Dialect §9.5 bytes when the preparation pin is non-null, agreeing with the retained run |
| `.../preparation.sha256` | That pin followed by one LF; present exactly with the preparation |
| `.../verified-at.txt` | The preparation's own `verifiedAt` followed by one LF; present exactly with it |
| `.../audit.json` | Exact audit bytes without a trailing line separator, from decoded `run.auditBytes` when present, otherwise the exact `run.audit` value span |
| `.../audit-signatures.json` | Exact retained sidecar bytes named by `auditSignaturesDigest`; absent when null |
| `.../evaluation-error.json` | Exact complete Core error stdout under its pin, retaining any trailing newline |
| `outputs/<stage>/<instance>/<index>/payload.json` | Re-extracted payload in dialect §9.5 bytes, only for an admitted output |
| `outputs/<stage>/<instance>/<index>/record.json` | Derived envelope `canon` bytes with execution id, never execution-record digest |
| `selections/<stage>/<revision>.json` | The derived accepted core or complete refusal-bearing selection in `canon` bytes; every proof-referenced revision remains |
| `admission-proof.json` | Current P(k) or P(k,j), canonically repacked, with no newline |
| `admission-proof.sha256` | Its actual digest followed by one LF |
| `sets/<stage>.json` | Derived active `{workflowDigest, execution, stage, records}` in `canon` bytes, once per stage |
| `execution.json` | Full derived version-2 execution in `canon` bytes, pinning the actual current proof digest |
| `execution.sha256` | Digest of those execution bytes followed by one LF |

The abbreviated `.../` rows use the same instance/attempt prefix. Every separately pinned file
must agree with its retained run under RFC 0020 §7. Sidecar presence and exact bytes are committed
by the observation; they do not imply signature verification. A source value span excludes
surrounding JSON whitespace but preserves its own original bytes, including nested whitespace
and literals. Duplicate object names and invalid JSON are refused before span extraction.

Reconstruct execution members completely: frozen entries in workflow order; active instances
in stage/selected-parent order; all attempts in number order; state/failure from the transitions;
active sets in workflow order, with records in instance/output order; and the current selection
digest or null for each stage. Every observation's historical pins remain in the proof even if
its instance has since retired. They must never be looked up only in the final active execution.

For a valid output acceptance candidate, append all payload/envelope pairs, increment retained
record counts, set attempt/instance to completed or completed-zero, and rebuild the complete
affected set and execution. For refusal, append none of those outputs, set limit-exceeded, and
rebuild the same controls. The same observation, received files and proof prefix occur in both.
For selection acceptance/refusal use §3's corresponding complete forms. Compute real digest
values and full serialized bytes; no fixed-width hash-hole or guessed-header allowance replaces
this construction.

Measure `sum(len(file_bytes) for each distinct path)` and the number of paths. Compare exact
integer values to the workflow limits; equality fits. Check the existing per-artifact bounds
as well. For a genuinely byte-based refusal with no earlier cutoff, the complete acceptance
candidate must exceed the actual byte limit and the complete refusal candidate must fit it.
A fitting candidate cannot become refused because a writer supplied an asserted size.

The final supplied export contains the full proof and all its required retained history. Optional
`README.md`, `trust.json`, `expected-report.json` and files under `aux/` enter only finalization.
They cannot shadow required paths, count toward all final byte/file limits, and never justify an
earlier admission refusal. Other unexplained files in required recording namespaces are inventory
findings. Existing chain/checkpoint evidence may be retained under `aux/`, with its own verifier.
A finalization overflow gives `input-over-bound`, not retroactive admission justification.

### 8. Recording unavailable and reader order

If the known begin metadata, proof, actual received attempt material or complete refusal carrier
cannot fit, no valid proof-bearing export exists for that operation. Report an operational
recording failure, preserve acquired material in custody and expose the last complete recorded
prefix as such. Do not label it a complete account of the unrecordable operation, truncate it,
hide files as auxiliaries or automatically reacquire a smaller answer. This is the existing
operational-error category: exit 3 with no portable reading, refusal or finding report.

Version 2's reader applies these phases in order; this explicit replay order replaces version 1's
global semantic ordering where history requires a reconstructed earlier state:

1. Enforce supplied byte/file/nesting bounds, strict JSON/integer domains, count/string bounds,
   readable selectors, closed forms and earlier-reference ordering, using the existing refusal
   codes `input-over-bound`, `input-malformed` and `version-unread` in that order. Missing non-null
   pinned artifacts give the existing `inventory-mismatch` refusal; unread dialect kinds give
   `kind-unread`. Required canonical files must equal their canonical bytes.
2. Check independent workflow/execution pins, the proof pin/root/previous-prefix links, all
   frozen pins and all retained artifact pins (`digest-mismatch`), then frozen binding/profile
   consistency (`stage-binding-mismatch`). Retired artifacts receive the same checks as active
   ones. A bad digest cannot supply a purported historical baseline.
3. Check every retained preparation with the existing preparation verifier at its recorded time,
   with independent historical profiles. Order by begin epoch, then canonical member order.
   Preparation refusals precede preparation findings as in RFC 0020; findings map to
   `preparation-mismatch`. This is not Runtime or signature replay.
4. Replay epochs, and observations within each, in their canonical order. Check selection cores
   and offered sets (`selection-mismatch`), projected cases (`case-mismatch`), inherited influence
   and admission (`influence-mismatch`), then membership, state transitions and admission bounds
   (`inventory-mismatch`), followed by emitted payload/envelope agreement (`output-mismatch`).
   Finish each transition before moving to the next. Fork effects are derived, never supplied.
5. Compare the final reconstructed active execution, sets, history inventory and proof to the
   supplied files. Active inventory/control differences are `inventory-mismatch`; output bytes
   or lineage disagreements are `output-mismatch`. Reject missing or extra required history.

A reading retains RFC 0020 §9's fields and meanings. `completion` is partial if the last group is
open, any required selection is unconsumed, a stage is blocked or any active instance is not
completed/completed-zero. `counts` reports active stages, instances, outputs and selections;
it does not reset the retained-history limits in §1. Authentication remains not-established and
dispositions remain not-replayed. No portable proof report claims authentic intent, exactly-once
execution, source accuracy or a valid result from an unrecordable operation.

### 9. Processing bounds and adoption evidence

Readers process observations once in proof order and retain a bounded current logical state.
They may stream serialization and measurement, but must produce the same bytes and digests as
the full construction. A local/count overflow may stop a candidate derivation once its own bound
is proved; it must not be relabelled as a measured aggregate-byte overflow. Proof-prefix hashing
may reuse hash state over exact canonical array prefixes and closing suffixes. Correctness
cannot depend on a language-specific map order, serializer, filesystem block size or hash API.

The format ceilings are a concrete proposal to test, not measured capacity recommendations.
The executable accounting examples described below test byte construction and counterexamples;
they do not supply real operation/research recordings or implement the complete reader above.
Before adoption, record those workflows and compare exact proof prefixes, candidate files,
retained/active counts and reports with a separately authored reader under a recorded independence
protocol. Agreement on a boolean or isolated arithmetic example is insufficient.

## Alternatives

- **No contract change.** Keep byte-only refusals outside the experimental reader's supported
  subset. This is honest current behavior, but leaves the independent workflow reader incomplete.
- **Product-only journal.** Useful for recovery, but another reader would need private schemas,
  allocator rules and transition history. Publishing only asserted totals does not solve that.
- **Extension or profile.** A closed workflow record cannot gain the required history and pins
  through an unknown extension; a profile would still need a common accounting contract.
- **Full candidate copies.** Retaining complete counterfactual files can establish their contents,
  but duplicates large cases and outputs and may make the proof impossible to retain under the
  same actual bound. Derivation from already validated inputs is preferable where defined.
- **Fixed instance allocation.** A common allocator could remove one source of length variation,
  but changes valid instance identities and does not solve later artifacts or retries.
- **Freeze the accounting frontier after a byte refusal.** Simpler than epochs, but prevents an
  otherwise permitted earlier sibling or earlier stage from retrying in place. A stage-only
  freeze is insufficient when an earlier independent stage changes a later stage's baseline.
- **Logical units or exempt proof storage.** Either changes the selected actual-byte accounting
  policy. An unbounded reserve or an excluded proof area can hide the very resource use the
  reader is supposed to measure; neither is proposed here.

## Compatibility

This RFC adds a reviewable proposal and no adopted wire change. RFC 0020, `spec/workflow.md`,
schemas, released pins, reader codes and all current Runtime, Gateway, Runner and Desk behavior
remain unchanged. Spec #209 stays open. The proposed invariants cannot be used as an acceptance
or conformance claim under the existing workflow text.

Adoption would materially change the Draft workflow record. The proposed version-2 selectors
make required proof linkage, referenced earlier selections, epoch-scoped cutoffs, retained-history
limits and replay ordering explicit. Readers must not silently invent epochs for a form they do
not understand. Historical byte-only refusals cannot be upgraded by guessing prospective IDs or
private history. The proposed 8 MiB/32-block ceilings are format limits, not supported-history
or performance claims; capability discovery remains an implementation integration question.

Epochs preserve explicit in-place retries where the unconsumed-set rule permits them, but do not
promise every private writer schedule is representable. Membership, closure, stop and fork
rules are specified above and still need implementation agreement. Proof history consumes real capacity: a branch
that fit without proof can become unrecordable with it. That cost is explicit, not hidden in a
larger or exempt byte allowance.

## Security and privacy

A proof establishes consistency of a declared logical accounting sequence, not authentic
wall-clock history. Hash linkage and independently held expectations expose changes to the
committed proof; an operator able to replace the whole unsigned bundle consistently can still
declare a different sequence. Existing acquisition receipts and audit signatures authenticate
only their existing subjects. They do not authenticate selection intent, allocation choices,
epoch chronology or the whole workflow. No new permission or approval follows from a valid proof.

Arbitrary baseline inventories, duplicate ownership, omitted earlier revisions and moving future
artifacts into earlier epochs would permit false refusals. The public transition rules must
exclude them. A longer valid prospective ID can legitimately change a candidate's length; the
proof records that choice, but does not establish why a person or installation chose it.

Bounded proof bytes, blocks, members, IDs and nesting are needed before allocation and replay.
Repeated prefix hashing and reconstruction can be a resource attack even within byte limits;
two implementations must agree on both the digest domain and bounded processing strategy.
No network, model call or Runtime evaluation is needed to check accounting.

Retaining earlier selection revisions and failed attempts exposes additional review assertions,
answers and unselected material to bundle holders. Test material should be synthetic and contain
no credentials or personal data. Digests do not remove that disclosure and are not access control.
An unrecordable acquisition still needs honest custody; it must not disappear into a false valid
export or be replayed automatically to obtain a smaller answer.

## Conformance

No new conformance class, corpus entry or claim is created. The following are required recording
cases for the proposed contract and independent readers; they are not recorded workflow fixtures:

- **Long and short prospective IDs:** hold inputs fixed, retain each real candidate ID plan, and
  measure complete candidates. Construct a byte boundary only after measuring; require the
  designated refusal recording itself to fit. Never infer IDs or assert unretained sizes.
- **Duplicate paths:** equal cases, payloads, packs or audits at separate paths each count; a
  digest-keyed store must not reduce the recording's byte or file count.
- **Opposite completion order:** two siblings each offer six records with ten remaining. In
  both completion orders, canonical group order admits the first and refuses the second.
  Repeat with an actual-byte boundary and preserve all acquired material.
- **Earlier sibling retry after later refusal:** A's first attempt fails, B has a byte refusal,
  then A explicitly retries in a new epoch. B's original prefix and proof stay unchanged; B
  remains failed until its own retry. Also start with a fitting B candidate: A's later bytes
  must not turn a fabricated old refusal into a justified one.
- **Earlier selection revision:** retain a refused revision, execute unrelated later work, then
  revise the unconsumed selection. Check both at their own offered sets and prefixes; retain
  and count the earlier revision. Reject reuse of its prospective ids even though a refused
  reservation consumed no instance capacity. A consumed selection still requires a new branch.
- **Inserted, reordered or omitted epoch:** hold independent expectations fixed, mutate the
  chain, and check links, numbering, membership and final-state agreement. Also test a repinned
  but structurally invalid sequence; digest agreement alone is insufficient.
- **Changed membership or ownership:** move an attempt or source file to an earlier epoch,
  omit or repeat a selected child, assign one attempt twice, or attach equal audit bytes with
  another attempt's signature sidecar. No case may inflate or erase the earlier baseline.
- **False refusal when the candidate fits:** with no valid earlier cutoff, retain a complete
  in-bound candidate and mark it refused. The reader must reject that claim independently of
  the writer's failure label, candidate size assertion or final branch size.
- **Proof and finalization limits:** proof bytes cross the actual byte bound; a proof reaches
  its structural ceiling; candidate exceeds a file limit; refusal material itself cannot fit;
  or only final auxiliaries overflow. Distinguish unrecordable work, input-over-bound and a
  genuinely proved admission refusal without inventing portable codes before adoption.
- **Interruption and resume:** stop after atomic reservation, retain uncertain acquisition and
  reload without acquisition. Cover explicit first-attempt resume, retry, pre-attempt stops,
  incomplete epochs and branch forks under the forms above. Preserve unaffected siblings,
  reject arbitrary ancestor subsets, and require a new execution for a consumed-root retry.
  Start A and defer B, consume their stage's offered set downstream, then reject a later first
  begin of B without a fork. Also cover allowed resume before consumption, a consumed empty
  root selection, and carrying a consumed deferred slot unchanged while another stage resumes.

Record positive, negative, boundary and recovery bundles with exact bytes, fixed independent
pins and expected reports. First demonstrate the
operation-based workflow required by RFC 0020 and its additional research recording; isolated
arithmetic examples cannot substitute for either. Require independent agreement before claiming
the proposed accounting works across implementations.

### Synthetic accounting experiment

`tools/workflow_admission_probe.py` derives a small synthetic inventory from operations and
uses the existing canonical and literal-preserving JSON serializers. Run it from the repository
root with `python tools/workflow_admission_probe.py`; its focused checks are
`python -m unittest discover -s tests -p test_workflow_admission_probe.py -v`.

For its fixed one-output example, the complete acceptance candidate is **5,980 bytes in 22
files**. It fits `maxBytes: 5980`; at `maxBytes: 5979`, the same-sized acceptance candidate
does not fit and the **4,564-byte, 20-file** refusal carrier does. The proof and its digest
sidecar contribute **1,222 bytes**, included in both candidates. The program measures these
values from full serialized files, including controls and their actual digests.

With a separate two-stage example and `maxBytes: 8811`, a one-character prospective child id
produces an **8,811-byte** accepted reservation. A 64-character id produces an **8,937-byte**
candidate and an **8,423-byte** fitting refusal carrier. These are measured examples for this
synthetic encoding, not fixed protocol allowances or asserted sizes a reader may trust.

The tests also cover duplicate content at distinct paths, opposite completion order, historical
refusal stability after later retries, frozen consumed sets, fork retention, and literal numeric
and string encoding. They do not validate real stage artifacts, receipts, signatures, projection
or influence, implement an independent reader, or provide operation/research recordings. Pre-id
count refusals, local artifact-bound failures and final auxiliary overflow are outside this
experiment. Its passing checks establish only the stated synthetic accounting properties.

## Implementation

The Spec repository owns the proposed portable forms, canonical transitions, bounds, failure
precedence, recording layout and eventual vectors. A separate adoption change would amend
RFC 0020 and its companion together after the evidence and public review requirements are met.
The executable byte-accounting experiment tests construction and counterexamples for a limited
set of prevalidated synthetic inputs; it is not a workflow reader or a replacement for recordings.

Runner would own durable epoch membership, atomic child reservation, ordered result commitment,
retained history and export. Its existing private driver, custody and offline preparation checks
are useful starting points, not authority for a portable writer or reader to copy hidden state.
Desk would own explicit review, retry and stop controls through its existing context, Plan and
permission boundaries. Runtime and Gateway need no workflow or proof semantics; their existing
evaluations, acquisitions, receipts and signatures remain separate.

Two plausible implementations are a Go Runner reader/writer and a separately authored Python
offline reader written from the completed companion and recorded bundles without access to the
first reader's code. Record authorship, allowed inputs and comparison protocol. Different
languages or model reviews alone do not establish independent authorship or implementation.
Compare exact prefix digests, reconstructed files, totals and outcomes, not just final booleans.
Public review, including the repository's cross-vendor adversarial review, is separate from that
implementation evidence and cannot supply it.

## Unresolved questions

The three earlier wire-design gaps have concrete proposed rules in Specification §§2–8.
That closes the questions at the proposal level, not the implementation or adoption gates.

1. **Recorded transitions and independent agreement.** Obtain real operation and research
   recordings covering membership, stops, open-group recovery, candidate/refusal bytes and forks.
   Name the second reader's authors, permitted inputs and independence protocol, then compare
   exact prefixes, full materialized files, counts and outcomes. The synthetic accounting
   experiment does not establish this evidence.
2. **Capacity and integration.** Exercise the proposed 8 MiB/32-block ceilings and retained-history
   costs on realistic workloads. Define Runner capability discovery and Desk's presentation of
   recording unavailable through their existing interfaces. No new portable refusal code or
   increased byte allowance is implied by that product work.
3. **Adoption and compatibility review.** Review the explicit version-2 changes to semantic
   ordering, cutoff scope, fork retention and monotonic counts. Amend RFC 0020 and its companion
   together only after that disposition. Older records remain readable under their old format,
   with no invented proof or retroactive conformance claim.
4. **Authentication.** A future authenticated execution commitment remains RFC 0020's separate
   open question. It must not create digest cycles or turn consistency of a declared accounting
   sequence into an unsupported claim about authentic chronology or reviewer intent.

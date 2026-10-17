# RFC 0022: Retained workflow admission proofs

- Status: Draft
- Type: Standards track, a proposed amendment to the Draft workflow contract
- Created: 2026-10-17
- Issue: [#209](https://github.com/Judgment-Pack/judgment-pack-spec/issues/209)

This is a contract proposal for review, not an adopted amendment. It changes neither
[RFC 0020](0020-workflow.md), its `spec/workflow.md` companion, nor any implementation or
conformance corpus. The tentative encoding below is incomplete: the acceptance blockers in
Unresolved questions must be resolved before it can define a portable reader. The workflow
remains Draft and normative for nothing.

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
pin. No released component is claimed to emit or verify the proposed epochs. No epoch proof,
independent reader agreement or workflow conformance fixture has been recorded.

## Specification

The following are proposed invariants and a logical algorithm. They are requirements for a
future complete amendment, not a complete closed grammar or reader specification today.

### Accounting subject and root

An accounting proof belongs to exactly one supplied execution branch. Its root binds the
workflow's canonical digest, execution ID, root-case digest, frozen-stage commitment and explicit
root instance ID. The frozen commitment names the canonical ordered `frozen` array of RFC 0020
§7, not a new release encoding. The existing pack, published/bound dialect, binding, release,
profile and Runtime checks precede accounting. Embedded profiles do not become trusted merely
because the proof names them.

The root accounting state contains all frozen stage files, the workflow, root case and root
reservation, their required side files, the execution and stage-set control files, and the
initial proof prefix. Repeated contents at different recording paths remain different files:
the root case and an instance's case, or equal packs retained for two stages, count at each path.
File-system path lengths are not separately charged as file contents; IDs embedded in JSON and
proof plans are charged as their actual serialized bytes.

README, declared test trust material and expected reports are verification auxiliaries. They
enter only at finalization, belong to no execution epoch and cannot justify an earlier admission
refusal. Their actual bytes and files still count in the final supplied bundle. Any other supplied
material also counts in that final aggregate check; it cannot be inserted into an earlier epoch
as an arbitrary baseline contribution.

### Public epochs and membership

The proof retains ordered, numbered epochs. Each epoch names the canonical proof prefix through
the preceding epoch. Epochs are public logical accounting records, not a claim to reproduce every
database transaction, source checkpoint, wall-clock completion or private I/O event.

Exactly one root epoch establishes the initial reservation. A selection-admission epoch retains
one selection plan and reserves all children of every direct consumer in one operation, or
records the independently established refusal without reserving any child. A first-attempt group
accounts for the work on that reservation in canonical order. Its complete membership is fixed
before acquisition. Every child is covered, including deterministic projection/admission failures
and explicitly stopped work. A dependent selection cannot be admitted until its producing group
has closed. A group interrupted before work completes can leave a partial recording; it cannot
silently launch the remaining acquisitions on reload.

A selection plan binds the upstream stage, revision and canonical digest of the requested
selection with `refusal` absent. It supplies one prospective child ID per direct-consumer and
selected-parent slot, in that order. The reader derives those slots from the workflow and
selection, then checks valid, distinct IDs and collision with already reserved instances.
Admitted IDs must agree with the actual inventory. For an independently recomputable count or
projection bound that fails before ID allocation, a distinguished no-allocation plan can avoid
an oversized list; its precise form remains to be settled. Empty selection and no allocation
because of a bound failure are different cases.

Every actual attempt and retained execution artifact has exactly one epoch owner. An attempt is
identified by its instance and increasing attempt number; its exact run, source, preparation,
audit, signature sidecar and evaluation-error files follow the existing encoding rules. Shared
bytes do not merge ownership or recording paths. Epoch membership cannot be changed to move a
later acquisition into an earlier refusal's baseline. The encoding must distinguish a planned
attempt from stopped work and an attempt actually begun; that is acceptance blocker 1 below.

Earlier refused selection revisions referenced by the proof remain retained execution artifacts.
They are checked at their own epoch's offered set and remain byte-counted after a later revision.
This would amend RFC 0020's current rule that only the branch's named revision is traversed.
Unreferenced revisions and other branches cannot supply accounting evidence for this branch.

### Retries and cutoff scope

Each explicit retry starts a new epoch and appends an attempt under the existing instance when
the workflow's unconsumed-set rule permits an in-place retry. The epoch begins from the preceding
closed accounting state. It cannot alter earlier attempts, memberships, selection plans or proofs.
The existing retry actor/time assertion remains an installation assertion, not authentication or
acquisition permission. An uncertain acquisition is retained as uncertain; neither recovery nor
offline verification retries it automatically.

Within an epoch, results are accounted in workflow stage order, selected-parent order and output
index order. Acquisition or completion order cannot choose the winner of a shared bound. The
first output admission exceeding a branch bound establishes that stage's cutoff for that epoch.
Later affected members of the group emit no outputs under that cutoff. The exact interaction
with pre-attempt stops and other terminal failures remains part of acceptance blocker 1.

A later retry epoch considers its explicitly retried instance anew against the then-retained
branch. It does not turn other failed siblings into successes or silently retry them. Their old
refusals remain checked against their own epochs, including the old cutoff. An earlier sibling's
new attempt therefore cannot retroactively increase the baseline used to justify a later
sibling's old refusal. Retrying after consumption still needs a new branch; how that branch
reuses an accounting prefix is acceptance blocker 3.

### Reconstructing and measuring candidates

For each epoch, the reader first validates its linkage, membership, plans and ownership. It then
reconstructs the preceding closed execution state and the current epoch's known admission
metadata. It does not accept a supplied baseline list, byte total or unretained artifact size.

For selection admission, derive every projected case and initial child entry from the retained
selected payloads, bindings, influence and explicit IDs. For output admission, derive every
payload and output envelope from the independently checked preparation, audit and instance pins.
Do not retain a second full candidate merely to assert its length. Recompute the exact candidate
bytes under the workflow's distinct serialization domains.

At each decision the accounting map contains only files owned by the root and preceding steps,
the current known proof prefix, and the control files reconstructed for that step. Later
results, attempts, selections and epoch entries cannot appear. Planned membership of the current
epoch is known input and its bytes count; it is not permission to include future result bytes.
Replacing a mutable control file replaces its bytes at that path; it does not count all virtual
snapshots as supplied files. Immutable retained artifacts continue to count at every actual path.

The accepted candidate includes the complete selection reservation or output addition and every
required execution/set/selection/side-file change. The refusal candidate keeps all required
attempt and acquisition artifacts, records the derived failure, and emits none of the refused
outputs or children. Exact start/result control serialization is acceptance blocker 2; a
reserialized approximation or a constant guessed header allowance is insufficient.

An initial aggregate-bound refusal is justified only if the complete accepted candidate exceeds
the actual bound and the complete refusal recording fits. A candidate that fits cannot acquire a
refusal merely because a proof exists. A later member may instead have a previously established,
verified cutoff in the same epoch; the reader checks that derivation, not a bare failure label.
The proof-bearing baseline must itself fit. Count and artifact-local failures remain separately
recomputable, without disguising an aggregate-byte claim as one of those failures.

The accounting unit remains actual supplied file bytes, each path counted once, and actual file
counts. All proof bytes count. There is no exempt proof area, unbounded reserve, deduplication
credit or logical accounting unit replacing `maxBytes`. The final reader checks the entire
supplied bundle, including the full epoch history and finalization auxiliaries, against the
existing aggregate bounds. A finalization overflow can give `input-over-bound`; it cannot
retroactively justify an earlier `limit-exceeded` claim.

### Tentative bounded encoding and digest direction

The following notation identifies proposed fields, not a valid fixture or settled wire form:

```text
Proof = {admissionProofVersion: 1, workflowDigest, execution, rootCaseDigest,
         frozenDigest, rootInstance, epochBlocks}
Epoch = {number, previousProofDigest, kind, selectionPlans, attempts, stops}
SelectionPlan = {upstreamStage, revision, candidateSelectionDigest, childIds}
AttemptMember = {instance, number}
```

`kind` would distinguish root initialization, selection reservation, first-attempt groups and
explicit retries. A group also needs an unambiguous reservation reference. Conditional members,
stopped/resumed work, no-allocation plans and branch initialization remain unresolved; a consumer
cannot implement a complete reader from this notation.

One candidate bound is an 8 MiB canonical proof file, with epochs packed in at most 32 blocks
of at most 4096 entries, full blocks except the last. Every prefix is repacked by the same rule.
The existing integer, nesting, string and per-container bounds also apply. These are proposed
structural ceilings to review, not a new workflow budget or a promise that every possible branch
history fits them. A proof may reach its own bound while ordinary execution artifacts still fit.
That case is recording unavailable, not a proved workflow refusal. The final form must define
all member bounds, prefix packing and supported histories explicitly.

Let P0 be the canonical proof root with no epochs, and Pk the same root with epochs 1 through k.
Epoch k's `previousProofDigest` names P(k-1). Its entry contains no digest of Pk, final execution
digest, candidate execution hash or asserted candidate size. Pk can therefore be hashed before
serializing an execution control file that pins Pk. Output lineage continues to name the execution
ID, not its record digest. The reader computes actual digest values and serialized files; this
proposal grants no implicit fixed-width digest-hole arithmetic.

Only the current proof prefix contributes to a step's proof file size. Future epoch entries do
not contribute to that earlier step, while the full final proof contributes to the final bundle.
If historical prefix files are also supplied, each supplied path counts in that final aggregate.
Implementations should avoid quadratic prefix rehashing; an incremental hash state can retain the
open canonical array prefix and append its exact closing suffix when computing each digest.
Correctness cannot depend on one language's serializer or hash-state interface.

### Recording unavailable

When the proof, known admission metadata, retained attempt material or complete refusal record
cannot fit, the writer cannot produce a valid proof-bearing export for that operation. It reports
an operational recording failure and preserves acquired material in custody outside such an
export. It does not truncate answers, discard receipts, fabricate a failure that supposedly fits,
or declare the last valid prefix to be a complete account of the unrecordable operation. There
is no automatic acquisition retry or replay. This proposal does not yet assign a new portable
error code or change the current reader's operational-error behavior.

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

Adoption would materially change the Draft workflow record: required proof linkage, referenced
earlier selection artifacts, accounting-epoch cutoff scope and exact candidate construction need
a separately reviewed amendment. The version/discriminator and treatment of old Draft records
must be chosen then. Readers must not silently invent epochs for a form they do not understand.
Historical byte-only refusals cannot be upgraded by guessing prospective IDs or private history.

Epochs preserve explicit in-place retries where the unconsumed-set rule permits them, but do not
promise every private writer schedule is representable. Full membership, closure, stop and fork
rules need implementation agreement first. Proof history also consumes real capacity: a branch
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

No new conformance class, corpus entry or claim is created. The following are proposed cases for
an eventual complete contract and independent readers, not recorded fixtures or passing tests:

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
  and count the earlier revision. A consumed selection still requires a new branch.
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
  incomplete epochs and branch forks once their forms are settled.

After the grammar and transitions are complete, record positive, negative, boundary and recovery
bundles with exact bytes, fixed independent pins and expected reports. First demonstrate the
operation-based workflow required by RFC 0020 and its additional research recording; isolated
arithmetic examples cannot substitute for either. Require independent agreement before claiming
the proposed accounting works across implementations.

## Implementation

The Spec repository owns the proposed portable forms, canonical transitions, bounds, failure
precedence, recording layout and eventual vectors. A separate adoption change would amend
RFC 0020 and its companion together after the blockers and public review are resolved. This
draft adds no executable reader or prose-mirroring test.

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

The first three are explicit acceptance blockers for a complete portable amendment:

1. **Membership, stopped work and cutoff precedence.** How are planned slots, attempts actually
   begun, children stopped before acquisition, interrupted first attempts resumed later, and
   attempts suppressed by a group cutoff distinguished? Which attempt stubs are committed
   before acquisition, and how are already received later results retained? Resolve interaction
   between the cutoff, projection/admission failures, cancellation and other terminal failures.
2. **Exact candidate and control serialization.** Specify root initialization, reservation and
   attempt-group boundaries; every start/result transition; proof growth; mutable execution/set
   headers; side files; and counterfactual acceptance/refusal bytes. Choose closed conditional
   forms, member bounds and evaluation precedence. An approximate accounting formula is not a
   portable proof, and this notation is not sufficient to implement one yet.
3. **Branch forks and unchanged ancestors.** Define initialization for a new branch after
   consumption, reuse of a common prefix and ancestor artifacts, new instance identities,
   selection revision history, and exactly which old records the current proof traverses.
   Preserve the earlier branch unchanged without silently importing its unrelated artifacts.

Further decisions required before adoption are:

4. **Proof limits and capability discovery.** Are 8 MiB and 32 blocks appropriate? Which histories
   can be represented under actual limits, how does a writer discover support, and how does
   an unavailable recording surface without claiming a valid failure or losing custody?
5. **Version and reader outcomes.** Select the new discriminator or Draft-version amendment,
   missing/unsupported/malformed proof outcomes, linkage and accounting findings, and their
   order relative to existing preparation and workflow checks. Do not reinterpret old records.
6. **Independent agreement and recordings.** Who writes the second reader, what independence
   protocol is recorded, and which real operation/research recordings establish exact agreement
   on these transitions and adversarial cases? No such evidence is held today.
7. **Authentication.** A future authenticated execution commitment remains RFC 0020's separate
   open question. It must not create digest cycles or turn consistency of a declared accounting
   sequence into an unsupported claim about authentic chronology or reviewer intent.

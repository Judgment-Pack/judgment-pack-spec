# Experimental offline workflow reader

This is a separately authored experiment against proposed RFC 0022 at Spec
`88794f7ac09fc46d8af89605f1defbd7a7db14d9`. The initial algorithm was frozen at
`e3fde6153f992a42997b43459e5eb87b6ad5dcab`; that byte-identical checkpoint is
archived at `/tmp/jps-portable-delivery/workflow-reader-freeze-initial`. This is
not an adopted interface or a
complete workflow conformance claim. The initial algorithm was written before
receiving actual workflow recordings or comparison results from the Go writer.
The unit examples are manually constructed contract examples, not evidence that
an operation or research journey actually ran.

## API

```python
from tools.workflow_reader import Expectations, verify

result = verify(
    files,  # dict[str, bytes], relative recording paths and exact file bytes
    Expectations(
        workflow_digest=independently_held_workflow_digest,
        execution_digest=independently_held_execution_digest,
        runtime_digests=independently_held_runtime_digest_by_stage,
        historical_profiles=independently_held_profile_bytes,
    ),
    comparison_trace=True,
)
```

The caller loads files and supplies trust independently. The reader does not
acquire sources, run Runtime, replay policy, verify audit signatures, or derive
trusted pins/profiles from recording auxiliaries. `Verification.exit_code` is 0
for a reading, 1 for refusal, 2 for finding, or 3 for operational failure.
`report_bytes()` returns the report plus newline, or `None` for exit 3. `detail`
is explanatory local text, not part of the portable report.

The optional trace gives each reconstructed candidate's proof digest, path
count, total bytes, retained/active counts, fit decision, and each path's own byte
count and digest. Distinct paths count separately even when their bytes match.
No supplied total or final-inventory baseline is trusted. Auxiliary files affect
the final supplied-byte check but never an earlier candidate. A trace with
`completeCandidate: false` stopped at a proved local bound; its partial byte
count is not evidence of aggregate-byte overflow. Count-only selection refusal
has no purported measured allocation candidate. Trace labels are local
comparison identifiers, not new portable fields.

The algorithm strictly reads workflow controls, checks independent and retained
pins, verifies all retained preparations with the existing Python dialect
reader, and reconstructs history chronologically. It derives selection cases,
influence, reservations, starts, attempt observations, output sets, controls,
proof prefixes, candidate byte inventories and fork retirement. It keeps retired
material and monotonic reserved/output/attempt accounting separate from active
report counts. No workflow replay or accounting helper is shared with Runner.

## Scope and limitations after the first review fixes

- The imported preparation reader is `tools/dialect_verify.py` at the Spec pin.
  It is unchanged between the initial and revised Spec pins. Its supported operation/research dialect kinds and its refusals remain in
  force. It is reused openly, including canonical/literal JSON handling and
  actual preparation recomputation, rather than relabelled as new workflow work.
- Retained release encoding is projected from the approved Runner data
  declarations and encoding methods at
  `66e264e1e44f665e52b056be1b70864a27927338`. Its newly authorized retained
  serializer uses `UseNumber` followed by `json.Marshal`: raw number literals
  (including -0, decimals and exponents) survive, and HTML/U+2028/U+2029 are
  escaped. This differs from dialect `canon`. Retained triggers remain
  unsupported and return operational error.
- Run exports v2/v3 are the recorded scope. The reviewed RFC 0022 clarification
  now explicitly makes v4/v5 `version-unread`, before supported closed forms.
  Separately retained signature bytes are pinned and counted; authentication is
  not established. Their retained encoding is JSONL, possibly unreadable material,
  so they remain opaque bytes rather than being parsed as a single JSON document.
  The 16 KiB limit, exact pin, attempt ownership and chronological charging apply.
  The contract does not explicitly equate Runner `run.attempt` with the workflow
  attempt ordinal. This reader validates the integer form but adds no equality
  rule; a focused test preserves that distinction pending contract clarification.
- The reviewed clarification defines `run.finishedAt` as the exact terminal
  preparation/planning check instant for failed-preparation/admission observations.
  The revised reader requires its UTC-second form and directly recomputes from
  retained inputs at that instant. It never substitutes startedAt, receipt time
  or the current clock and never fabricates a preparation. Only the contract's
  explicit terminal findings establish the corresponding failure. A missing
  planned source is pending; a missing required response inside a retained
  research acquisition can be terminal. Unknown failures and operational
  inability return exit 3. This verifies consistency, not authenticated time.
  The initial frozen reader correctly left this previously undefined phase
  unsupported; that source checkpoint is preserved.
- Core error envelope shape comes only from the pinned Runtime declaration
  excerpt described below and the approved prose. There is no evaluator replay.
- The 49 focused unit tests cover closed forms, independent pins, selected and
  empty selections, exact byte equality, auxiliary overflow, output-count
  refusal, false refusal, open epochs/retry, fork retention/counts, retired-id
  reuse, payload substitution, and a preparation forgery with repinned carriers.
  The retained release encoding is checked against an existing dialect vector.
  They also cover the clarified terminal-clock rule, malformed times, clock
  non-substitution, actual dialect terminal failures versus pending acquisition,
  missing retained research responses, and unrelated operational errors.
  `workflow_reader_preflight.py` collects independent byte, nesting, counted and
  form errors across supplied artifacts before choosing input-over-bound,
  input-malformed, version-unread, inventory-mismatch or kind-unread precedence.
  Mixed-error tests reverse file insertion order and combine bounds, malformed
  controls, unread selectors and missing pins. This replaces the initial
  traversal-order limitation. Tests still do not establish all phase combinations,
  all generated-influence chains, all retained export encodings, ceiling-scale
  behavior, or actual operation/research workflow agreement. The first actual
  comparison and its disagreements are recorded below. No complete
  reader-conformance claim is made.
- Optional comparison trace is capped at 8,192 candidates and 1,000,000 aggregate
  path entries. Exceeding that local cap returns operational error; retry without
  trace. Proof prefixes and candidate maps are materialized. Proposal ceiling
  throughput and memory use have not been measured.

Focused validation, using Python 3.12:

```sh
/tmp/jps-portable-delivery/spec-admission-proof-venv/bin/python -m unittest tests.test_workflow_reader -v
```

## Authorship, exposure and input ledger

The protocol was published before implementation at Spec issue 209 comment
6243575419 and is retained locally as
`/tmp/jps-portable-delivery/workflow-proof-independence-protocol.md`. Both author
agents are OpenAI models; separate contexts/languages do not by themselves prove
independent authorship, and this is not cross-vendor evidence.

Before this work, this reader's author had reviewed Runtime dialect authoring
resources, but had not read Runner workflow writer/reader code, the synthetic
Spec admission probe or its tests, or helped draft their algorithms or RFC 0022.
It read RFC 0020 and RFC 0022, including their prose descriptions and numeric
examples of the earlier synthetic experiment. It has still not opened
`tools/workflow_admission_probe.py`, its tests, or Runner `workflow_*.go`.

Allowed inputs actually consulted before freeze:

- Spec RFC 0020, RFC 0022, their linked dialect/Core/workflow prose, contribution
  instructions, `tools/dialect_verify.py`, and existing dialect conformance
  records at the Spec pin. These are prose/dependency inputs; no workflow
  implementation or actual workflow recording was read. The focused existing
  export check uses `conformance/dialect/vectors/valid/run.json`.
- Runner snapshots under
  `/tmp/jps-portable-delivery/workflow-reader-inputs/runner-66e264e/`, with the
  full file hashes in `PROVENANCE.json`: `internal/runner/model.go` (Release,
  Run and referenced input declarations), `source_inputs.go` (source-input data),
  `mapping_v2_types.go` (mapping, profile and preparation data),
  `release_tests.go` (retained test data), `dialect_v3.go`
  (`InputMapping.MarshalJSON`), `dialect_artifact.go` (`marshalArtifact`),
  `mapping_v2_export.go` (`VerificationBundle`/`releaseDigest`), and
  `docs/MAPPING-V2.md` (referenced retained-export contract). Only declaration
  and retained-encoding rules were used as implementation authority.
- Runtime prose under `/tmp/jps-portable-delivery/runtime-034`, pinned
  `785ea58927255b775a774e29952c560591429cd3`, including README, architecture and
  ADR 0027.
- Additional Runtime error declaration dependency was authorized publicly before
  read at Spec issue 209 comment 6243644381. Read only
  `/tmp/jps-portable-delivery/workflow-reader-inputs/runtime-785ea589/retained-error-declarations.txt`
  and its `PROVENANCE.json`. Exact source `internal/result/result.go` ranges:
  23–26, 40–43, 49–56, 659–669, 1502–1513. No constructors or evaluator code.

Incidental exposure, reported before continuing and retained here:

1. Reading `model.go` lines 1–160 displayed the generic Run declaration and
   adjacent `served`/`decodeRun` helpers. Those algorithms were not used.
2. Reading `dialect_artifact.go` lines 105–180 while locating an identity
   declaration displayed adjacent `releaseDialectIdentity`, `admitJobDialect`
   and `checkDialectUpgrade` helpers. They were not used as workflow or
   preparation algorithm authority.
3. After the author independently flagged the missing failed-preparation clock,
   the coordinator disclosed that an existing Go helper used `run.finishedAt`.
   The helper was not opened or ported; the initial reader keeps this phase
   unsupported. The coordinator also recorded the v2/v3 run-scope interpretation.

The incidental line ranges above are exact. The declaration ledger records
symbol scope and source hashes; a complete per-command line-range transcript of
all earlier approved dependency reads is not reconstructed here. This limitation
must not be presented as a stronger exposure audit than the available record.

Source hashes of the initial freeze are reported to the coordinator separately
so this README does not contain a self-referential checksum. Subsequent Spec-only
clarifications and later actual-recording comparisons must preserve that initial
checkpoint, first disagreements, and changes; no expected report may be silently
regenerated merely to match either implementation.

## Revised-freeze input and change log

After the initial source freeze, the coordinator supplied only the reviewed Spec
RFC 0022 clarification at `88794f7ac09fc46d8af89605f1defbd7a7db14d9`, §§1 and 5
(public Draft review: PR 210 comment 6243734481). The author read the exact diff
against the initial Spec pin. No writer helper or actual workflow recording was
supplied or consulted before this revised freeze. The independent terminal
derivation calls the existing Python dialect recomputation directly and uses a
closed classifier; it does not compare against a fabricated expected preparation.

Additional approved dependency reads for this revision were the existing
`tools/dialect_verify.py` ranges 55–80, 157–255, 312–340, 1749–2040, 2455–2580,
3020–3170, plus symbol-location searches in that same file. RFC 0020 lines
120–212 were reread for canonical/value-domain rules. New focused examples reuse
only existing dialect vectors `valid` and
`work-item-triage-presence-optional-omitted`: mapping, case, profiles, sources,
and the latter's preparation timestamp. These are explicitly reused dialect
records inside hand-constructed unit examples, not newly executed workflows.

The coordinator reported preparing an external comparison harness, but it was not
opened or run by this author. Actual workflow recordings and cross-comparison
remain after this revised source freeze.

## First actual comparison and retained-encoding correction

After the five-file revised freeze was archived, the coordinator supplied the
actual snapshots in `/tmp/jps-portable-delivery/workflow-v2-recordings-frozen`,
independently held pins/profiles, and the measurement-only harness
`/tmp/jps-portable-delivery/check-workflow-recordings.py`. The author read the
harness and the preserved `/tmp/jps-portable-delivery/workflow-first-comparison.json`.
Original snapshots, pins, both freezes and that first comparison were not changed.

The first diagnosis found three separate causes:

1. The Python retained Release serializer incorrectly used dialect `canon`,
   changing -0 and HTML escaping. The typed projection was correct for the
   inspected specimen, but its final bytes were not the required retained form.
2. Operation recordings used a `query` template form under `adapter-http`,
   violating pinned dialect §4.1's object-of-string-templates requirement.
3. Completed research recordings recomputed evidence availability `{}`, while
   the actual Runtime audit retained `inputs.evidence: null`. These are different
   JSON values under dialect §11. Facts and citations agreed.

Only item 1 was changed in this reader. Neither of the other findings was waived,
normalized or hidden by changing expected pins. The read-only diagnosis was
reported before edits. The coordinator then authorized the precise retained
serializer dependency publicly at Spec issue 209 comment 6243895054 before read:
`runner-66e264e/retained-json-encoding.txt` and
`retained-json-encoding-provenance.json`, containing only pinned `model.go`
170–188 (`encode` and `canonical`). Excerpt SHA-256:
`fa8d0f74c62a2984c741a4f7fcf5391d65982d77dba4aba53a2fc4a203ef94df`.
This is a retained encoding dependency, not a workflow or preparation algorithm.

The fix adds an independent final serializer over the existing typed projection.
Five focused tests cover preserved raw -0/decimal/exponent spellings, numeric
input bounds, control/HTML/line-separator escaping, Unicode key order, typed
integer versus raw-number behavior, and omitted versus explicit-null fields.
The API and comparison trace contract remain unchanged. The previous raw
noninteger Release encoding limitation is removed.

Re-running the unchanged original snapshots after this fix gives 7 readings,
19 `record-inputs-differ` preparation findings and 8 operation profile findings.
All 67 retained stage Release digests agree; no Release digest mismatch remains. The newly enabled interrupted-recovery
snapshot agrees on the measured candidate inventory. Results were written to
`/tmp/workflow-reader-serialization-comparison.json`, preserving the first result.
This is a partial comparison result, not blanket agreement or adoption evidence.

Additional exposure during diagnosis: the approved Runner declaration/encoding
snapshots were reread at `model.go` 1–65, `source_inputs.go` 1–85,
`mapping_v2_types.go` 1–82, `dialect_v3.go` 48–98 and
`mapping_v2_export.go` 15–33. The last two ranges also displayed the adjacent
`version3Member` declaration/enumeration prefix and a `VerifyRun` comment,
respectively; no verification body was read or used. Source-input snapshot
declarations beyond `SourceInput` were displayed but not used. The author also
read the permitted Python dependency's serializer/request/binding sections and
the corresponding dialect prose. No excluded Runner workflow code or synthetic
probe was opened.

Model provenance: the session identifies this author as Codex based on GPT-6,
but does not expose a reliable exact served model identifier/version. Record
that exact model as unknown from this author's available context; do not infer
`gpt-6.1-sol`. The same-vendor limitation remains.

## First review corrections and additional exposure

The complete unedited review is preserved at
`/tmp/jps-portable-delivery/workflow-reader-review-round1.md`. The reviewer had
previously reviewed the Go writer and Spec prose and disclosed that exposure.
This reader author received the contract findings and diagnostic mutations, not
the writer's implementation. Initial, revised and retained-encoding freezes and
the first comparison remain unchanged. The new review-fix freeze is a separate
archive; this work does not assert conformance or adopt the proposed interface.

All three P2 findings were corrected with focused adversarial tests:

- Dialect §5.1's endpointScope eligibility is checked for every frozen stage,
  including unused downstream stages, before preparations or replay. Workflow
  §4's explicit generated-only admission rule (spec/workflow.md 193–198) also
  resolves the review's mixed-admission probe: a generated operation profile
  requires exactly `["generated"]` at its targets. This checks declared classes,
  not actual channel authorship. The Runner-attempt equality probe remains the
  separately documented contract question above.
- Optional retained Run strings and source mappingDigest obey their declared
  types. A retained import must have the published family-3 dialect/binding form,
  obey dialect counted bounds and binding grammar, and agree with the frozen
  published dialect and binding. Matching a bound mapping alone is insufficient:
  distinct catalog inputs can produce it. Tests include valid retained import,
  malformed import, foreign published and binding documents, and global bound
  precedence despite an unrelated malformed optional field.
- Original signature-sidecar bytes may be multiline JSONL or unreadable. Tests
  retain those bytes, exercise 16 KiB and one-byte-over boundaries, mutate literal
  bytes without repinning, and check missing, misplaced and unclaimed sidecars.
  Authentication remains `not-established`.

Additional approved reads for this correction were the pinned Run declarations
at model.go 54–108, DialectImport at dialect_v3.go 65–78, the referenced
MAPPING-V2.md retained-export/signature prose, workflow/RFC 0020/RFC 0022 and
dialect §5.1/§4.4 prose, and the existing Python dialect verifier's declaration,
binding/profile and form helpers. Existing `unbound-bound-at-import` dialect
records supply published/binding data inside new hand-authored unit examples.

One additional incidental exposure occurred and was reported immediately to the
coordinator: the command

```sh
cat /tmp/jps-portable-delivery/workflow-reader-inputs/runner-66e264e/internal/runner/source_inputs.go
```

requested the entire approved snapshot file, lines 1–485, rather than only its
allowed declarations. The file's SHA-256 is
`2cff77b5d2df6e3ad7a9aca38d2bf9e1ca37f45b0b4f17e710376e1baa28ef52`.
It was the first command in a combined read whose tool output was truncated.
The visible prefix included the generic `validInputEscapes`, `readInputJSONDepth`,
`pointerTokens`, `pointerRead`, `InputMapping.validate`, `mappingHash` and
`sourceDocument` helper bodies and the beginning of `readSourceDocument`, beyond
the SourceInput declarations. The exact truncation boundary is not reconstructed;
the requested full-file range is conservatively recorded as potential exposure.
This is additional generic validation/source-processing exposure, not zero
exposure. Those helper algorithms were not used as workflow or preparation
verification authority. No Runner workflow implementation or synthetic probe
was opened, and no writer algorithm was ported. Subsequent reads were limited
to explicit approved ranges. The coordinator must preserve this disclosure with
the review/public experiment record.

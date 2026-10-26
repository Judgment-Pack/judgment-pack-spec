# Retained column conversion draft artifacts

These files support Draft [RFC 0029](../0029-retained-column-conversions.md). They are not
published normative resources or whole-document/preparation verification. No current capability
is established here. The schema validates structure only; readers also enforce exact byte limits,
UTF-8/scalars, duplicate rejection, embedded JSON, cross-member constraints and conversion semantics.

`cases.json` contains handwritten expectations (including the preserved 36 compatibility cases),
not recorded outputs. `examples.json` contains labelled fragments. `reader.py` and `reader.mjs`
separately implement conversion preview and unchanged canon claim admissibility using exact
rational arithmetic. Both have the same author/assisting model; they are not independent authorship
or cross-vendor evidence. `check.py` drives both over the same cases. No network, package install,
model call, acquisition, evaluation or preparation is performed.

Run `python3 -B rfcs/retained-column-conversion/check.py` from the repository root. Python 3 with the repository’s `jsonschema` development dependency and Node 22 or later are required. Set `RFC0029_NODE` to an explicit supported Node binary when
the system `node` is older. The check prints a bounded summary and does not install
anything. Standard input to each reader is one JSON request per line: `{rule,frame}` or a
`{binary64Hex}` shortest-rational probe. Output is a preview plus `claimAdmissible`, or a refusal.
The Draft also exposes `{restore,profile,limits}`: `restore` is the closed four-member generated
carrier and limits contains exactly `originalSnapshotBytes`/`carrierBytes`. Restoration verifies
raw UTF-8 snapshot length/SHA-256 and returns the identical text, not an object serialization.
The complete received carrier bytes are separately counted; nested retained-frame bytes retain
the existing frame bound. The bounded line channel remains 4200000 bytes.

`{admission:{capabilities,required,sizes}}` checks the RFC's closed role-specific shape and exact
trusted expected Spec/schema/corpus pins before any callback. `required` is a complete capability
entry with the caller's limits; every role-applicable size is required. The effective bound is
the lower caller/reporter maximum per member. This is an admission-contract probe, not evidence
that reported sizes came from real production artifacts or that a production role is supported.
`{lineage:{rule,frame,profile?}}` derives the closed inline fragment and refuses issues or noncanon
values as `read-failed`. No failed application receives success lineage.

Run `python3 -B rfcs/retained-column-conversion/check.py --carrier-only` for the focused changed
carrier/capability/lineage fixtures. The default command also runs the preserved conversion corpus;
it is reserved for the stable candidate gate. New cases are handwritten, including original
revision 7 alongside current revision 8, exact numeric/Unicode/raw spellings, missing/null/empty,
complete role-limit boundaries, callback ordering, and intended safeguard-removal controls in
both readers. Examples show full asserted-origin append and distinct published/bound identities;
they are labelled fragments, not producer admission runs. Schema member/alternative removal
controls cover the new closed shapes; duplicate names and byte semantics require the readers.

The conditional document 1/2 MiB, combined 6/12 MiB and standalone producer transport 3 MiB
figures remain proposals. Preparation/record 8/16 MiB accounting, actual producer transport,
original inventory commitments in complete receipts, Runtime/Runner integration, independent
production recomputation, exact-head CI/review and normative adoption remain prerequisites.


Run `python3 -B rfcs/retained-column-conversion/check.py --inventory-only` for the
producer-specific relation and identity fixtures. The full original snapshot remains
byte-exact; the reader extracts a separately closed projection, compares the complete
ordered declaration inventory, binds unfiltered `record.values` and exact typed
status/value tokens, and derives the domain-separated 71-byte revision identity.
The proposed `desk-reviewed-input/1` profile member and optional role capability
binding require a new pinned adapter version 2; current version 1 is not claimed.

`{generatedConsistency:{carrier,profile,limits,trustedProducer,sourceBinding,
receiptResultDigest,rule}}` is a pure probe. Its supplied profile projection/digest
are independent seams, not authentication performed by this protocol. Every success
explicitly returns `acquisition:"not-verified"` and `history:"not-checked"`. Existing
signature/request/profile verification and complete original-history lookup by the
actual trusted producer remain required. A matching projection cannot prove that
history was loaded or that any record is true. The schema closes the extracted
projection, not the full legacy snapshot; opaque source members remain retained.

The focused checks exercise all eight original types, all five conversion kinds,
availability, original versus current revision, omitted/extra/reordered/unselected
declarations, exact escapes/-0/null/absence/status, wrong trusted context, stale
receipt digests, exact raw-frame identity and the 524288-byte original snapshot
boundary. Both readers have the same author and remain Draft-only prototypes.

Producer cases use explicit literal `requestPatch`/`expectedPatch` edits against
`examples.json`'s labelled `producerConsistency` fixture. An explicit `expected`
refusal replaces the positive expectation. Paths are decoded member names or array
indexes, and edits set a literal `value` or `remove:true`; the driver never invokes
a reader to produce an expected value. `wireJson`, where present, fixes the exact
received serialization for raw-frame identity. This avoids duplicating the entire
snapshot/inventory for each negative case while retaining exact expanded wire data.

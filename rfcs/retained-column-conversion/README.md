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
the minimum of the selected profile cap and lower caller/reporter maximum per member. The
expected identity is an explicitly synthetic installed-package fixture constant, independent of
caller/reporter agreement; it is not a real schema self-hash or support declaration. This is an admission-contract probe, not evidence
that reported sizes came from real production artifacts or that a production role is supported.
`{lineage:{rule,frame,profile?}}` derives the closed reference fragment and refuses issues or noncanon
values as `read-failed`. No failed application receives success lineage.

Run `python3 -B rfcs/retained-column-conversion/check.py --carrier-only` for the focused changed
carrier/capability/lineage fixtures. The default command also runs the preserved conversion corpus;
it is reserved for the stable candidate gate. New cases are handwritten, including original
revision 7 alongside current revision 8, exact numeric/Unicode/raw spellings, missing/null/empty,
complete role-limit boundaries, callback ordering, and intended safeguard-removal controls in
both readers. Examples show full asserted-origin append and distinct published/bound identities;
they are labelled fragments, not producer admission runs. Schema member/alternative removal
controls cover the new closed shapes; duplicate names and byte semantics require the readers.

The selected Draft table is document 1/2 MiB, frame 2/4 MiB, combined 12/24 MiB, carrier/grant/
stdout 3 MiB, response 5 MiB, preparation 16/32 MiB and record 9/17 MiB. Complete profiles,
HTTP/reply, storage and exports have separate table rows. These are proposals. Actual producer transport,
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


Run `python3 -B rfcs/retained-column-conversion/check.py --references-only` for this amendment's
focused checks. Present preparation input is exactly
`{state:"present",ref:{frameSha256:<exact raw frame UTF-8 digest>,location:"values"|"research-value"}}`;
missing is exactly `{state:"missing"}`. Parent `column` and the existing checked source/read/pointer
select the occurrence. Equal digests do not authorize different source/profile/receipt occurrences.
`values` resolves compact string/null JSON; `research-value` resolves exact `valueJson` contents.
Results, omission reasons, metadata and conditional original research identities remain per target.
Preview diagnostics may show input JSON, but inline input JSON is no longer preparation syntax.

`{verifyLineage:{rule,frame,transformation,profile?}}` compares the complete recomputed fragment.
It returns `acquisition:"not-verified"` on consistency: it authenticates no source, receipt or
history. Actual raw frame tokens are extracted before any reserialization; no `frameJson`,
network/digest-store lookup, canonical rehash or fallback is introduced. A standalone fragment
without its retained bound occurrence remains unverifiable. Production wrong-source checks
must retain the existing read/profile/receipt bindings even when frame bytes are equal.

`{retainSource:{source}}` checks the closed generated custody slot, exactly `{response:<existing
signed envelope>}` OR `{retainedResponseJson:<nonempty exact envelope text>}`. It returns sole
exact text. `signedResponseFragment` closes `{result,receipt,salts}` only; the existing full
receipt/salts schema, frozen request, signature, profile, producer inventory and freshness
verification remain mandatory. Labelled empty receipt/salts objects are intentionally only
structural examples. `retainCase:{source}` checks the case custody slot, `{case:<object>}` OR
`{retainedCaseJson:<nonempty exact case object text>}`, and returns sole exact text. This slot's
closure does not remove permitted enclosing mapping/source/import siblings. Both probes reject
dual forms, null/empty/wrong-case text, duplicate names and nonobjects. Their line bound is a
prototype limit; they provide no production admission, preparation or supported-role claim.

Successful production Draft retention must preserve the exact envelope/case and frame through
HTTP, storage, offline verification and export, materializing transient objects only. Hashes
identify raw custody, while existing signatures bind canonical result content; outer whitespace
is not signed. The original snapshot string remains authenticated canonical result content.
The complete original case/provenance and producer-v2 inventory guards remain unchanged.

The RFC's serialization ledger charges every JSON string layer, both changed documents,
bindings, siblings, provenance, receipts/signatures and all per-target results/basis metadata.
`--references-only` includes tiny encoder-specific byte measurements and changed safeguard
controls, while reusing unchanged producer guard evidence. The former combined arithmetic
omitted exact-text escaping and no longer supplies complete-envelope maxima. The earlier
6/12 MiB combined, 3 MiB response and 8/16 MiB preparation targets are superseded by the
complete table above. Conditional arithmetic/encoder evidence is not actual product-boundary
proof, adopted ceilings or established parity. The ordinary Runner TAB witness and diagnostic
reference substitution motivate this amendment; they do not establish actual reference-path
preparation or global bounds. Full integrated checklist/CI, independent review, producer/consumer
integration, normative disposition and immutable adoption identities remain separate work.


Run `python3 -B rfcs/retained-column-conversion/check.py --limits-only` for the affected cap,
role and selector slice. Handwritten exact-cap/one-over expectations cover all complete-artifact
members, caller/reporter lower limits, independent profile caps and matching but untrusted
identity tuples. The driver calls both actual admission functions with effect counters and
removes each changed safeguard at its intended assertion. It does not allocate maximum-size
product artifacts; `sizes` remains an instrumented reported-size seam. The prior reference,
producer and conversion expectations are preserved, and their unchanged suites are not repeated
by this focused option. The stable integrated default gate also includes the new cap slice.

`selectionFragment` is the closed `{contract,spec,profile,roles}` envelope. Roles are unique and
in the RFC's fixed five-role order. `{selection:{selector,role}}` probes one trusted endpoint-role
requirement before the callback. Real hosts obtain the complete role set from local operation
metadata, compare to their trusted installed package, validate before a larger read, and persist
the exact selector as optional enclosing `conversionContract` across source/preparation/release/run/
checkpoint custody. It does not relax the inner closed case/response slot; existing complete-object
signing/binding includes it. No route/header or
base64 encoding is normative here. Absence preserves ordinary behavior; body fields, binary
versions and equal frame hashes cannot infer selection. Extended examples test conditional Draft
grammar only and grant no end-to-end Extended preparation support. Runtime document-validation
may separately implement Extended; that does not infer a Runner role or remove existing behavior.

The complete ledger explicitly counts the sole retained case/response JSON string escaping,
independent release.sample and run.input copies, third input mapping, record delta and raw-audit
base64 sidecars. Source-shaped arithmetic and structural encoder probes are evidence for the
proposal only. Product boundaries, trusted producer history, actual Runtime record behavior,
ordinary defaults, independent review, immutable pins and normative adoption remain parent-owned
integration/release gates. No complete #171 or published support claim follows from these files.

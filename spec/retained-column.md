# Selected retained columns

## Status and exact scope

This companion is accepted at **draft maturity** through [RFC0029](../rfcs/0029-retained-column-conversions.md)
for the exact `v0.3.0-rc.2` distribution. Acceptance is separate from immutable publication:
the exact tag, maintainer-published GitHub release and verified artifacts are required before
published support can be claimed. RFC0029 is its informative design record.

This companion governs only explicitly selected `retained-column/1` document,
preview, preparation and offline-verification support. It supplements [the Dialect](dialect.md)
for that exact selection. It creates no general Core conformance, stable interoperability,
source truth, acquisition authenticity or execution-authority claim. Preparation versions remain
integer 2/3 and artifact formats remain integer 2/3 or named 2.0.0/3.0.0.

The key words MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT and MAY have BCP14 meaning
only when capitalized. Requirements written as direct imperative/prohibition in the contract
below are required behavior of a selected supporting role, not optional implementation advice.

## Installed identity and certification

The complete trusted support tuple is contract `retained-column/1`, Spec distribution version
`0.3.0-rc.2`, the exact immutable Spec source commit, the new schema SHA-256, complete selected
corpus SHA-256, profile and role (plus producerGrammar where applicable). Core packs continue
to declare exact specVersion `0.3.0`; that does not select this leaf. RC2 evidence remains
provisional for final Core conformance and is never described as a final Core release claim.

`releases/v0.3.0-rc.2.retained-column.json` inventories the new schema and all corpus inputs.
`corpusSha256` hashes the exact selected `conformance/retained-column/1/cases.json` bytes;
that file names every normative case group and its external companion inputs by digest.
The release inventory also binds the handwritten full-preparation fixtures and their driver.
Neither schema nor corpus contains its own final digest or final source commit. The generated
`release-identity.json`, included under release checksums/provenance, supplies sourceCommit.
Readers MUST check these installation files independently of caller/report agreement. Missing
installation identity is unsupported; mutable source checkout HEAD is not a substitute.

A selected leaf-support claim names the exact distribution/source/schema/corpus tuple, supported
profiles and separate roles, and states that every applicable published case passed. It establishes
agreement on this selected leaf and complete enclosing preparation checks only. It is not the
unavailable generic preparation-verifier claim of Dialect §14. The 47 historical staged Dialect
recordings remain staged with their existing identities and no publication claim. Historical
regression checks remain required. The bundled Python and TypeScript offline readers implement
Base preparation verification; Runtime's separately supported Extended document-validation role
must not be inferred to establish Extended preparation.

Test installation tuples in handwritten cases are explicitly synthetic fixtures, not support
pins. Corpus readers substitute no caller-provided expected manifest. Integration tests use an
independently fixed test installation to avoid a self-referential corpus/preparation hash.

## Contract


The requirements below govern only exact selected retained-column/1 support. Acceptance at draft maturity does not establish immutable publication or product support.

### Closed grammar and selection

A fact copy gains exactly `{target,source,conversion}`. `conversion` has exactly
`contractVersion:"1"`, `column` and `kind`, with exactly `trueValue` and `falseValue` added
when kind is `boolean`. Kinds are `text`, `decimal`, `number`, `boolean`, `research-value`.
An evidence copy gains exactly `{requirement,source,availability}`; `availability` has exactly
`contractVersion:"1"` and `column`. No default or coercion is inserted. These variants are legal
in ordinary `case.facts`, `case.evidence`, and source `read.copy`, under existing integer 2/3 and
named 2.0.0/3.0.0 carriers. They cannot mix quality-target members into an entry. All existing
pointer syntax, target ownership, source order, duplicate and ancestor overlap rules apply.
The source pointer resolves to the whole frame after ordinary unwrap, rather than a prepared
leaf. A missing frame gives `read-failed`; a missing column in a well-formed frame is an omission.
Unknown versions, kinds or members, wrong scalar types and mixed variants are `input-malformed`.
The complete structural companion is [contract.schema.json](../schema/retained-column/1/contract.schema.json).
It does not replace duplicate-member, UTF-8, scalar, byte-limit or cross-member semantic checks.

Column names are nonempty Unicode scalar strings, at most 160 UTF-8 bytes, compared exactly.
Boolean spellings are distinct, nonblank scalar strings of at most 160 UTF-8 bytes. Blank means
consisting entirely of U+0009–U+000D, U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A,
U+2028, U+2029, U+202F, U+205F, U+3000. No host whitespace extension applies.

### Retained frame

A frame has exactly `contractVersion:"1"`, `origin`, `values`, `research`. `origin` is
`asserted` or `generated`. `values` maps column names to strings or historical null.
Absent keys remain absent. Asserted frames have `research:null`; generated frames have a
research object with exactly `recordRecipeRevision`, `declaration`, `fields`.
The revision is a nonempty scalar string, at most 160 UTF-8 bytes. Declaration is null or
exactly `{recipeRevision,fields}`. Its ordered field array contains exactly `{name,fieldJson}`
entries with distinct names. `fieldJson` holds the exact original field JSON, at most 16384
UTF-8 bytes: an object containing one string `name` equal to the entry name and one string
`type`. Other original declaration members are opaque data, never executable policy.
Duplicate names anywhere inside fieldJson or its unpaired surrogates refuse the frame.
The eight original types are `text`, `integer`, `decimal`, `boolean`, `text-list`, `range`,
`string`, `number`. An unrecognized original type yields `research-type` when selected.
`fields` maps names to closed `{status,valueJson?}` entries. Status is exactly `supported`,
`interpretation`, `missing`, `conflicting`, `inaccessible` or `stale`. `valueJson`, when present,
is a string retaining the original raw JSON within the negotiated frame envelope; absent differs from
`"null"`. Embedded raw is retained data; malformed or over-512KiB typed JSON is a per-record `research-type` issue when selected,
not a blanket refusal of an inspectable frame. Modern resolved values must be duplicate-free and
scalar-valid; historical string/number keep the original validation exemptions described below.
Empty retained raw text is preserved but fails `research-type` when selected as resolved.

The host projects the frame from actual records under their original retained revisions and
preserves original source/recipe bytes and digests separately. The projection has a new identity.
It is never described as those original bytes. Generated frames travel through the existing
generated reviewed-input acquisition channel and keep its binding, receipt and review rules;
they do not become asserted cases. Declarations cover the complete retained revision inventory,
not the current recipe or an arbitrary record's type. Declaration null or a revision mismatch
never falls back to a requested/current type.

### Availability and ordered diagnostics

Except `research-value`, conversions first inspect the column's raw string/null/missing state.
Missing omits with `missing`; null omits with `legacy-null`; a blank string omits with `blank`.
For generated rows, a selected field entry actually present and outside
`supported`/`interpretation` omits with `unavailable` before text conversion. An absent research
field entry does not suppress a nonblank ordinary display column (availableInputValues behavior). Original input states remain distinct.
A nonblank text string retains its surrounding spaces. Evidence uses this same filtering and
then accepts only exact `present`, `absent` or `unknown`, without trimming. Other text gives
`evidence-availability`. A false boolean and evidence `absent` are present results.

`research-value` first rejects asserted context with `research-context`, then metadata columns `name`, `url`, `website`, `company_id`,
`company_name`, `company_url` with `research-metadata`, then unavailable/mismatched original declaration with `research-declaration`,
and an undeclared selected name with `research-field`. A missing entry or an unresolved status
omits with `unavailable`. Resolved absent/empty raw, null or wrongly typed values give
`research-type`. This ordering applies even if the ordinary display column is missing or blank.
Zero-record/planned columns remain inspectable proposals: document validity is distinct from
per-record conversion issues, and zero records establish no readiness or inferred type.

### Five conversions

`text` emits the original nonblank string as JSON. `decimal` accepts at most 128 UTF-8 bytes
matching the entire ASCII grammar `-?(0|[1-9][0-9]*)(\.[0-9]+)?` and emits the original
string, preserving scale, trailing zeroes and negative zero. Failure is `decimal-encoding`.
`boolean` compares exact spellings and emits true or false; another nonblank string gives
`boolean-spelling`.

`number` applies these steps in order, with no approximate rational comparison:

1. Require at most 128 UTF-8 bytes and full JSON number syntax
   `-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?`; otherwise `number-encoding`.
2. Parse to binary64 using round-to-nearest, ties-to-even. A parse/range error, nonfinite
   result or absolute parsed result above 9007199254740991 gives `number-range`.
   Finite underflow alone is not a parse error. Zero retains its input sign for output.
3. If a written exponent has absolute mathematical magnitude above 308, give `number-exponent`.
4. Select a decimal rational for the binary64 magnitude x as follows. Its round-trip interval
   lies between the exact midpoints to the adjacent binary64 values; midpoint endpoints are
   included iff x's significand least significant bit is even. Zero selects rational zero.
   Search positive `a*10^e`, integer a with neither leading nor trailing zero, minimizing a's
   digit count (at most 17). Among candidates with that count select the one with minimum exact
   rational distance from x. A distance tie selects an even final coefficient digit; a remaining
   tie selects the smaller rational. Restore the sign. Formatting notation is immaterial.
5. Compare the original literal's exact rational to the selected rational. Unequal gives
   `number-precision`. Equal emits the ORIGINAL JSON number text, never a float serialization.

The float is solely a legacy compatibility guard. In particular `1e3` can preview as `1e3`,
while Runner still refuses that exponent claim. The bundled readers implement the selection
with separate Fraction and BigInt rational algorithms; neither compares decimals approximately.

`research-value` emits the ORIGINAL `valueJson` after the context/status checks and validation
against its original type. Modern text is a scalar string of at most 8192 UTF-8 bytes; integer
is a literal integer with no fraction/exponent and absolute mathematical value at most
9007199254740991; decimal is the above decimal string; boolean is a JSON boolean; text-list is
at most 64 strings each at most 1024 UTF-8 bytes; range is exactly min/max, both such literal
integers or both decimal strings, min<=max by exact rational comparison. Empty text, lists,
zero, false and equal-endpoint ranges are valid. Null is invalid in resolved values.
All raw typed JSON is nonempty and at most 524288 UTF-8 bytes. Historical `string` and `number`
add an 8192-byte raw bound. Embedded research-value duplicate detection compares decoded object names using Unicode 15.0
simple lowercase, matching the available Go 1.26.10 table, and requires EOF after one value.
Full case folding or host multi-code-point lowercase expansion is not equivalent. The available
Go 1.26.10 table is Unicode 15.0; the pinned module declares Go 1.26. The exact compiler of any
historical deployment is not established by go.mod. That is a provenance limitation, not an
additional release gate; no known source-contract mismatch was found in the bounded comparison. Historical string requires a JSON string and imposes no decoded length/scalar check. In particular
an escaped lone surrogate can remain a preview candidate in its original raw spelling, although
the unchanged canon boundary refuses it. Historical number requires
a JSON number accepted as finite binary64 by the original Float64 parse, without adding modern
safe-integer/decimal precision restrictions; retain its raw bytes even when execution refuses it.

### Results, diagnostics and execution

A preview returns exact candidate JSON or an omission reason, and deterministic issue codes.
The pinned messages are:

| Code | Message |
| --- | --- |
| decimal-encoding | Use a plain decimal without separators, units, exponents, or leading zeros. |
| number-encoding | Use an unambiguous number without separators, units, or leading zeros. |
| number-range | Number is outside the supported precise range. |
| number-exponent | Number exponent is outside the supported range. |
| number-precision | This number would lose precision. Keep it as text or revise it. |
| boolean-spelling | Does not match either declared Yes or No value. |
| research-context | Research value requires a typed research field. |
| research-metadata | Record metadata cannot use Research value. Choose another conversion. |
| research-declaration | The original research field declaration is unavailable. |
| research-field | Choose a declared research field for Research value. |
| research-type | The research value does not match its original field type. |
| evidence-availability | Evidence availability must be present, absent, or unknown. |

Malformed/over-bound frame structure is a refusal, not a per-record type issue. A declared valid
conversion with bad record data is a conversion issue, retaining an inspectable failed draft.
Application refuses before evaluation on any issue, using `read-failed` with the preview issue.
Missing/blank/unavailable with no issue supplies an unknown fact, never a fabricated value.
Candidate JSON must independently pass the unchanged canon claim domain: scalar-valid strings,
booleans, arrays/objects of admissible values, and safe integer literals with no fraction or
exponent (including literal -0). A noncanon candidate gives `read-failed`; no successful
preparation is emitted. Preview and claim-admissibility prototypes are not preparation evidence.

### Identity, lineage and capability

New successful/omitted applications add closed `columnTransformation` lineage with exactly
`contractVersion:"1"`, `column`, `input`, `result`, and conditional `researchIdentity` for
selected original research declarations. Input is exactly `{state:"missing"}` or
`{state:"present",ref:{frameSha256:<digest>,location:"values"|"research-value"}}`.
The reference is closed: no inline `json`, URI, extra column, fallback or other member.
`frameSha256` is `sha256:` plus lower-case SHA-256 of the exact retained frame UTF-8
object token, including internal whitespace, escapes and number spelling. It is not a
hash of a decoded or canonicalized frame. `columnTransformation.column` selects the exact
case-sensitive column; the checked rule, existing target source/read identity and source
pointer bind the frame occurrence. Generated occurrences additionally retain their existing
source/profile/request/receipt binding. Equal frame hashes never authorize interchanging
occurrences, sources, profiles or receipts. Hashes convey custody identity, not authority.

For `location:"values"`, resolve the selected structured string or null in that occurrence's
`frame.values` to compact JSON: UTF-8 non-ASCII stays literal, C0 controls, quote and backslash
are escaped, and no optional whitespace or solidus escaping is added. This does not recover
request spelling discarded by a legacy host. For `location:"research-value"`, resolve the
selected field's exact retained `valueJson` string contents, including whitespace and numeric
spelling. The location must agree with the checked rule's kind. An absent column or absent
raw `valueJson` is missing input; a present reference to it refuses. Explicit `"null"` and
empty raw text are present and distinct even when conversion later refuses or omits them.
Missing input must have exactly `{state:"missing"}`; it cannot stand in for a present value.

The retained acquisition or case is the only resolution source. Do not search by digest,
fetch a URI, use a network or external digest store, substitute unsigned data or fall back
to current declarations/values. Unresolved, substituted, wrong-location, wrong-column and
wrong-source references refuse with `read-failed` after existing source admission checks.
Malformed outer shapes retain their ordinary refusal. A verification/export bundle must
include the exact retained occurrence under its existing custody and authority contract;
a standalone fragment is unverifiable. Transient decoding must never replace retained bytes.
Preview may separately expose selected input JSON for inspection; that diagnostic is not
the preparation wire format or an execution authorization.

Every target retains result exactly `{state:"value",json:<exact candidate JSON>}` or
`{state:"omitted",reason:"missing"|"blank"|"legacy-null"|"unavailable"}`, plus all its
existing target metadata and conditional research identity. Research identity remains
exactly `{recipeRevision,fieldSha256}`, hashing the exact UTF-8 `fieldJson`. Result JSON
remains inline and its aggregate serialized bytes still count. Offline recomputation
resolves the bound occurrence, reruns the checked conversion and compares the complete
fragment; neither a reference nor retained result is accepted as truth. The `lineage` and
`verifyLineage` probes derive/compare these fragments from their actual raw frame tokens.
They explicitly do not authenticate source context or verify a whole preparation. Existing
source/read/profile/receipt checks remain required, including when two frames hash equally.
No failed execution gains success lineage. Integration with the production preparation
schema, independent verification and complete preparation/signature accounting remains required.

This candidate selects new exact versioned schema/corpus pins; old closed readers gain no
implicit support. The prior Draft experiment and its evidence retain their original identities.
Existing envelope versions and historical optional-member absence stay unchanged; old closed
readers refuse unsupported lineage. Rules enter read/dialect identity. Frame identity and complete
original declaration inventory commitments bind the checked projection; source/recipe identities
stay separate. Changes to source, column, kind, spelling, raw bytes, declaration or revision
invalidate their relevant commitments and require fresh checking and ordinary CAS/review.
Editor sidecars must equal document-derived rules and confer no separate execution authority.

The selected capability wire shape is `capabilities.conversionContracts:[entry,...]`, not a string list
or a boolean support flag. Each entry is a closed object with required `contract`, `spec`,
`profile`, `role` and `limits`, and only the optional `producerGrammar` described in the
producer section below for its three applicable roles. `contract` is exactly `"retained-column/1"`; `profile` is exactly
`"base"` or `"extended"`. `spec` is closed with exactly `version` (nonempty version label),
`revision` (40 lower-case hex characters identifying the exact Spec commit), `schemaSha256`
and `corpusSha256` (each `sha256:` plus 64 lower-case hex characters). The normative support version is exactly `0.3.0-rc.2`; the final immutable source revision
and new schema/corpus digests come from the external release inventory described above. Test example pins are synthetic
and grant no real support. Consumers compare all identity members exactly to trusted expected
pins, never values learned solely from the report. Member order does not affect comparison.

`role` selects one closed set of positive safe-integer byte maxima in `limits`. Maxima and
reported sizes use JSON integer tokens (no fraction or exponent), at most 17 ASCII characters
including a possible minus; positive maxima reject zero and negative values. Sizes additionally
permit zero. The structural schema cannot inspect numeric spelling; the readers enforce it.

| Role | Exactly required limit members | Owner and meaning |
| --- | --- | --- |
| document-validation | documentBytes, frameBytes | Runtime checks document/target coverage and retained frame only. |
| preview | documentBytes, combinedBytes, frameBytes, profilesBytes, requestBodyBytes, inputReplyBytes | Runner complete preview request/reply and trusted profiles, not preparation support. |
| preparation | documentBytes, combinedBytes, frameBytes, preparationBytes, recordBytes, profilesBytes, requestBodyBytes, inputReplyBytes, releaseStoredBytes, runStoredBytes, exportBaseBytes, exportWireBytes | Runner complete preparation, record, storage and export boundaries. |
| preparation-verification | documentBytes, combinedBytes, frameBytes, preparationBytes, recordBytes, profilesBytes, requestBodyBytes, inputReplyBytes, releaseStoredBytes, runStoredBytes, exportBaseBytes, exportWireBytes | Offline verifier independently supports the complete retained bundle, replay and export bounds. |
| producer-carrier | originalSnapshotBytes, carrierBytes, grantBytes, adapterStdoutBytes, responseBytes, profilesBytes | Producer's exact snapshot, complete wrapper/grant/stdout/signed response and trusted profiles. |

These limits count each complete serialized artifact, including punctuation, escaping, provenance
and signatures, rather than selected payload members. A document limit applies separately to
each retained published and bound document; combinedBytes counts both documents plus all other
counted case/acquisition bytes. frameBytes is an additional frame constraint within the combined
budget, never an extra allocation. Each preparation/record artifact is separately constrained.
Maxima are declared capacities; lower positive reported maxima remain valid and constrain actual artifacts. A report need not equal the full profile cap. Every traversed owner must
support the requested role independently; a Runtime entry cannot authorize Runner or producer
work. All existing target-count, parser node/string-work, nesting and compatibility limits
remain applicable and do not grow when a byte maximum grows.

The array has at most 32 entries and no repeated exact contract/spec/profile/role/producerGrammar identity (including absence);
an empty array grants nothing. Every declared entry must have the required role members and
no unknown members. An absent capability or unmatched exact identity is `capability-unsupported`;
an unknown contract, role or profile also fails with `capability-unsupported`. Malformed shapes,
missing limits and duplicate identities give `input-malformed`. The selected role's artifact
sizes must all be present as nonnegative safe integers; each must fit the minimum of the selected
profile cap, caller-required maximum and reported maximum, otherwise `input-over-bound`. A larger
report or caller maximum cannot enlarge the selected profile. Separate published and bound documents
are each tested against documentBytes; the probe sizes report the largest one, while combinedBytes
counts both actual occurrences. Production readers measure each occurrence themselves. Known unsupported support is refused before
artifact admission, grant creation, dispatch or evaluation; it cannot pass because a payload is
tiny. For a supported identity, malformed declarations and over-bound inputs keep the existing
validation/diagnostic order. The executable `admission` probe checks this declaration and size
comparison before its one instrumented callback; it does not measure an actual producer response
or perform acquisition. Production owners still measure their actual complete artifacts.

Runtime 0.39.0-alpha.1 has no such support. No capability is inferred from carrier versions,
`semanticValidation:true`, an installed binary's version or an unadopted candidate. All existing review,
approval, phase, acquisition, mixed-origin, cancellation, unknown-ack/no-retry and CAS guards
remain with their present owners.

### Closed selection before larger reads

The optional selected-profile envelope is exactly
`{contract:"retained-column/1",spec:{version,revision,schemaSha256,corpusSha256},profile,roles}`.
It is a separate selector, not a capability entry: it contains no caller maxima, route names,
producer registration or host-version override. `roles` is nonempty, duplicate-free and follows
this fixed order: `document-validation`, `preview`, `preparation`, `preparation-verification`,
`producer-carrier`, omitting unused roles. Unknown identity/profile/role refuses as
`capability-unsupported`; an extra member, repeated role or noncanonical order is `input-malformed`.
Every operation independently requires its complete role set from trusted local operation metadata.
A selector omitting any of those roles refuses even when every reported payload size is tiny.
Producer grammar support remains an exact additional capability check; selecting a role does not
register a profile, verify a receipt or authenticate a producer.

The consumer compares the complete tuple to an immutable expected manifest installed with its
trusted package. Agreement between an untrusted caller and capability report cannot install a
revision. The schema/corpus digests live in that external manifest; the schema does not contain
its own digest, and the corpus does not hash itself. Informative prototype constants are visibly
synthetic test installation pins, granting no product support. The final actual revision and
schema/corpus bytes must be selected only after the artifact set is frozen and reviewed.

A transport conveys and validates this bounded selector before reading a body beyond ordinary
limits. Header/route encoding is an adapter detail; this companion specifies no Runner route name.
Validate exact installed identity, required roles and supported profile before the larger read,
then apply lower caller/reporter limits and every artifact guard before acquisition, grants,
dispatch or evaluation. Persist the exact selector as optional `conversionContract` on the
enclosing source input and preparation, and retain it through release/run and checkpoint/source-operation
custody. It is outside the closed inner case/response custody slot. Existing complete-object
signing/binding includes it. Offline verification,
replay, storage and export revalidate it against their trusted installed manifest. They cannot
infer selection from body contents, carrier numbers, frame hashes or an installed binary version.
An absent selector keeps ordinary legacy behavior and bytes; it never opts an old artifact into
new limits. No new signing domain or authority follows from the selector.

### Complete selected carrier contract

The selected table below defines the scoped contract for the pinned asserted CSV/URL and
reviewed generated-record projection on adoption. Historical smaller targets and their
analysis remain informative in RFC0029; they are not this table or product acceptance evidence. Extended remains conditional on all existing Extended requirements;
prototype examples and doubled arithmetic do not establish end-to-end Extended preparation.
Document-validation support is a separate role: this amendment does not remove an existing
Runtime document-only Extended implementation or infer Runner support from it.
Ordinary/legacy limits remain unchanged. All entries are complete UTF-8 byte counts.

| Limit member / counted artifact | Base | Extended, conditional |
| --- | ---: | ---: |
| documentBytes, each published/bound document | 1048576 | 2097152 |
| frameBytes, additionally within combined | 2097152 | 4194304 |
| combinedBytes, complete counted documents/bindings/case/acquisitions | 12582912 | 25165824 |
| originalSnapshotBytes, exact original producer snapshot | 524288 | 524288 |
| carrierBytes, complete four-member generated carrier | 3145728 | 3145728 |
| grantBytes, complete separately selected new-channel grant | 3145728 | 3145728 |
| adapterStdoutBytes, complete new-channel stdout | 3145728 | 3145728 |
| responseBytes, complete signed response before retention | 5242880 | 5242880 |
| preparationBytes, complete preparation | 16777216 | 33554432 |
| recordBytes, complete audit record line, signature sidecar separately bounded | 9437184 | 17825792 |
| profilesBytes, complete trusted profiles document | 81920 | 163840 |
| requestBodyBytes, complete incoming preview/prepare/run body | 16777216 | 33554432 |
| inputReplyBytes, complete preparation/inputs-next reply | 37748736 | 75497472 |
| releaseStoredBytes, complete retained release | 41943040 | 83886080 |
| runStoredBytes, complete stored run | 41943040 | 83886080 |
| exportBaseBytes, complete version-2-shaped base including parsed audit | 75497472 | 150994944 |
| exportWireBytes, complete version 3/4/5 wire including sidecars | 90177536 | 176160768 |

This does not replace a global MaxBody, canonical parser bound or legacy producer channel.
Existing counts, nesting, node/string work, target coverage, claim admissibility and signature
rules remain independently required. A consumer must implement every applicable boundary before
advertising the corresponding role; a frame, preview or transport probe cannot establish it.

An asserted projection appends the retained frame and keeps the complete original
`origin.originalValues`, its other provenance, prepared values and sibling acquisitions.
It does not replace original values by a digest or call a projected map original bytes.
The complete original declaration inventory is taken from the record's original retained
recipe revision, with no fallback to current declarations. Where the legacy host retained a
structured field rather than its request bytes, `fieldJson` is the exact compact encoding of
that retained original structured field. This grants no reconstruction claim for original
request whitespace, member order or escapes that the legacy host never retained.
`valueJson` keeps the actual retained raw value token; original numeric spelling is never
replaced by a binary64 serialization. Missing retained bytes or declarations remain explicit.

For generated reviewed input, the selected contract defines a new closed versioned result with exactly
`contractVersion:"1"`, `originalSnapshotJson`, `originalSnapshotSha256` and `retained`.
`originalSnapshotJson` is a string whose UTF-8 bytes equal the original reviewed snapshot
exactly; the digest is `sha256:` plus its lower-case SHA-256. `retained` is the frame.
Readers reject duplicate decoded member names in both the carrier and snapshot, unknown
members/versions, missing digest, nonobject snapshots and nongenerated retained frames. Snapshot
JSON may contain legacy escaped lone surrogates: the snapshot text stays opaque for restoration,
with no replacement-character, number or scalar normalization. Parsing validates JSON structure
only; the decoded object is never reserialized to establish original identity. Embedding a
parsed snapshot object or retaining only its digest is insufficient. The new
result replaces the old counted snapshot payload; it does not append a second payload copy.
The identity domains remain separate: originalSnapshotSha256 hashes original snapshot UTF-8;
raw carrier identity hashes the entire received wrapper bytes; raw frame identity hashes the exact
received retained frame bytes; canonical result identity is the existing canonical digest of the
new wrapper. The original source/recipe commitments and published/bound document identities are
separate again. The wrapper's four members add no new signature or authority field. The enclosing
existing receipt/commitment workflow must bind the checked frame and complete original inventory;
that production integration is a prerequisite. A changed wrapper needs a new receipt. Original
source/recipe artifacts, reviews, original receipts and publication
identities remain available under their actual retention contracts. A new signed wrapper
binds the new projection; it does not retroactively authenticate an old snapshot digest.

### Sole exact-text preparation sources

On the new generated producer path, a source value is exactly one of
`{response:<complete existing signed envelope>}` and
`{retainedResponseJson:<nonempty exact envelope UTF-8 text>}`. The signed envelope retains
its existing closed `{result,receipt,salts}` grammar and all receipt/salts validation.
No snapshot sibling, second response form, null/empty text, case variant or extra member
is permitted. The text must parse as that duplicate-free envelope, never a surrogate
object containing a partial result. Initial object input is admitted through the ordinary
source checks; successful selected preparation retains only the exact received envelope text.
Previously retained exact text is checked by the same acquisition reader. Parsing may be
transient, but serializing both representations or replacing text by a canonical re-encoding
is forbidden. Canonical result signatures authenticate content; they do not authenticate
outer whitespace or the raw frame token. Raw envelope/frame hashes remain separate custody
identities. `originalSnapshotJson` remains authenticated as string content of the canonical
result. The existing producer-v2 grammar and full original-inventory preconditions below
remain necessary before successful generated lineage.

Asserted input has the corresponding **case custody slot**: existing `case:<object>` or
`retainedCaseJson:<nonempty exact case UTF-8 object text>`, exclusively. The enclosing input's
existing mapping, sources, import, binding and other permitted siblings keep their ordinary
grammar; this alternative does not create an arbitrary extra-member allowance. It preserves
the complete case once, including original values, provenance and the appended frame.
Initial case object admission remains available; successful selected preparation with retained
case conversions changes that slot to exact text. Consumers transiently materialize it at
the existing case-reading boundary; exports and stored records keep the sole text. Duplicate
names, nonobjects, dual representations, null/empty/wrong-case members and unsupported use
refuse. Ordinary historical inputs and absent optional members keep their existing behavior.
No universal JSON marshaler change, canonical raw-frame rehash or provenance deletion is
permitted to conceal compaction. Preserve the actual selected frame token through HTTP,
preparation retention, storage, offline verification and export.

The companion `preparationSource` and `assertedCaseCustody` schemas are fragment schemas;
receipt/salts internals and enclosing ordinary input members remain their existing contracts.
`retainSource:{source}` and `retainCase:{source}` probes demonstrate only closed custody slots
and exact text restoration. Empty receipt/salts in a labelled example establish no signature,
profile, producer, freshness or acquisition validity. The probes do not prepare or execute.
Their line bound is an experimental harness bound, not a negotiated production byte limit.

### Producer grammar and complete original inventory

The generated wrapper remains exactly the four members above. Its signature domain remains
Gateway `canon` over the wrapper, under the existing acquisition receipt and frozen request.
The selected producer grammar is `desk-reviewed-input/1`. It requires a separately
implemented, pinned and reviewed adapter version `2`; historical adapter version `1`
does not acquire this support by installing the Spec.

**Trusted binding.** The optional `retainedColumnProducer` member of the installation's
trusted InputProfile is closed with exactly `contractVersion:"1"` and
`grammar:"desk-reviewed-input/1"`. It enters the existing complete profile digest. The new versioned schema projects this optional profile grammar; existing profiles without it
retain their historical bytes and meaning. A source using this grammar is an operation bound to
that profile's exact id/digest. The independently trusted profile must have class `generated`,
shape `mcp`, source `desk-inputs`, endpoint `desk-local:reviewed-inputs`, exactly the tool
`read_reviewed_input`, and adapter name `jpack-desk/reviewed-input`, version `2`, and
an independently trusted exact adapter digest. The existing public-key, authority, request,
receipt signature, canonical result-digest and freshness checks remain required. A caller's
frame, capability report or context object cannot register a trusted profile, select a
replacement key, upgrade class or establish human review.

For the roles `preparation`, `preparation-verification` and `producer-carrier`, a capability
entry may additionally carry exactly `producerGrammar:"desk-reviewed-input/1"`. It is part of
the exact capability identity, including presence versus absence. A report without it grants
no support for this generated grammar. The other two roles do not carry that member.
Ordinary entries remain unchanged and can be reported beside generated entries. Negotiation
requires the exact adopted Spec/schema/corpus pins and supported limits for each traversed
role; a prototype probe or adapter version is not a support declaration.

**Producer precondition, not an offline truth claim.** Before issuing the new wrapper, the
trusted producer must resolve the entire original declaration inventory by
`record.Research.RecipeVersion`, using the retained `doc.Recipe` or `doc.Recipes` revision as
`typedResearchValue` does. A current recipe is usable only when its revision equals that
original revision. It must compare the complete ordered retained field structures, including
all retained metadata and unselected fields, with the run's `Recipe.Fields` that the original
snapshot records. Missing history, missing original declarations, differing fields or ambiguous
revision resolution refuses production before evaluation. It must also retain the existing
record/review/model/source admission checks. A new signature over a wrapper does not establish
that an old producer loaded history, and an offline reader cannot observe whether this step
ran. This is a required behavior of the newly pinned producer, to be demonstrated through its
actual implementation and signed integration. It is not inferred from one selected field hash.

**Closed extracted projection.** The full original snapshot has other real members, such as
qualification, prepared values, reviews, model/source references and recipe metadata. They stay
byte-exact in `originalSnapshotJson`, and duplicate decoded keys are refused throughout, including
opaque siblings. They are not silently dropped and this contract does not falsely declare the full
snapshot closed. Instead the reader explicitly extracts the following closed projection, as
`deskSnapshotProjection` in the new versioned schema specifies. This projection is
computed from original bytes, not accepted as a replacement snapshot or independent authority.

| Projection member | Required original snapshot path or fixed value |
| --- | --- |
| grammar | `desk-reviewed-input/1` |
| snapshotVersion, snapshotClass | `version` exactly integer literal `1`, `class` exactly `generated` |
| recordClass | `record.class` exactly `generated` |
| runId, recordRunId | `research.id`, `record.research.runId` |
| recipeVersion, recordRecipeVersion | `research.recipeVersion`, `record.research.recipeVersion` |
| values | complete, unfiltered `record.values` string map |
| declarations | every raw object token in `research.recipe.fields`, in its original order |
| fields | every `record.research.entity.fields` key, with its status and exact optional raw `value` token |

Required path containers and selected members must have these forms. Unknown snapshot versions
are malformed for this grammar; another producer grammar requires explicit support. Opaque
siblings grant no executable policy. Selected strings must be scalar Unicode, without case,
URI or Unicode normalization. `record.values` contains strings; it is not the top-level
snapshot `values` map, which the legacy `availableInputValues` filters for blanks and
unavailable statuses. Frame `values` must equal **all of `snapshot.record.values`**, preserving
blank and unavailable display values. Availability remains a conversion decision. Prepared
values, current requested types and the filtered map are never substitutes.

The two run ids must be equal and match the existing ASCII grammar
`research_[a-f0-9]{32}` exactly (41 bytes). Both original revision numbers must be equal positive
safe JSON integer literals, `1` through `9007199254740991`, without exponent, fraction or leading
zero. The upper bound is the existing signed `canon` domain, not a new precision conversion.
Define revision identity as `sha256:` plus the lower-case SHA-256 of this byte concatenation:

```
UTF8("judgment-pack/retained-column/1/desk-reviewed-input/revision")
0x00
UTF8(the decoded original run id)
0x00
ASCII(the original positive integer in unsigned decimal)
```

This label is always 71 ASCII bytes, below the existing 160-byte revision-member ceiling for
every supported run id and safe revision, including both endpoints. It is a new projection
identity and grants no authority; it does not rename a source, snapshot, recipe, record or
publication. Both frame `research.recordRecipeRevision` and
`research.declaration.recipeRevision` must equal this identity. A current qualification revision
elsewhere in the snapshot is ignored for this purpose.

For each declaration, retain the complete original snapshot field object token and remove
**only** JSON whitespace bytes `0x20`, `0x09`, `0x0a`, `0x0d` occurring outside strings. Preserve
member order, all string bytes and escapes, numeric spelling, opaque field metadata and array
order. This is token compaction, not decoding/re-encoding or a Go struct-order contract. Its
`name` and original `type` must agree with the frame's entry and existing eight-type contract;
decoded duplicate object names and repeated declaration names refuse. Frame declaration entries
must equal this **entire ordered inventory** exactly, with no omission, extra entry, reordering
or selected-field-only comparison. Existing `fieldSha256` hashes the resulting exact `fieldJson`.

Each projected typed field is closed with exactly `status` and, if its original object contains
`value`, `valueJson`. `valueJson` is that exact raw value token, including internal whitespace,
escapes and numeric spelling; it is not compacted or serialized through binary64. Other original
field members, such as citations and notes, remain in the original snapshot. Frame research
fields must equal the complete projection: status, key inventory and raw-token presence/value.
Absent differs from null, and `-0` differs from `0`. Status/type applicability and canonical-claim
refusals then use the existing conversion interpreter; an issue never receives success lineage.

The pinned original snapshot ceiling stays 524288 bytes even if a generic caller reports a larger
maximum. Carrier, combined, profile and transport bounds remain separately negotiated; no byte
allocation is added outside the complete carrier. The full-envelope and preparation/record
accounting gates below remain required before a product support claim. Opaque original JSON may retain legacy escaped lone
surrogates, but selected field/frame strings keep their existing well-formed-string rules.

**Executable consistency probe.** `{generatedConsistency:{carrier,profile,limits,trustedProducer,
sourceBinding,receiptResultDigest,rule}}` uses the closed shapes in the selected leaf schema.
`limits` is exactly `originalSnapshotBytes`/`carrierBytes`. The profile and digest inputs are
independent integration seams; this line protocol cannot authenticate them. The probe checks the
required producer tuple and source binding, exact restoration, the supplied result digest against
existing wrapper `canon`, every original/frame relation above, and one recomputed transformation.
It returns separate original-snapshot, received-frame and revision identities plus the closed
projection. Every successful result explicitly says `acquisition:"not-verified"` and
`history:"not-checked"`. It cannot mint production authority from caller-supplied context or
claim that a receipt signature or history lookup occurred. The actual integration must run the
existing signature/profile/request checks and the new producer precondition first.

Malformed structures/duplicates use `input-malformed`; exceeded fixed or negotiated bounds use
`input-over-bound`; unsupported grammar capabilities use `capability-unsupported`; a trusted tuple
or source binding that does not fit uses `profile-mismatch`; a changed wrapper with the old result
digest uses `acquisition-invalid`; well-formed inventory/revision/value inconsistencies and failed
conversions use `read-failed`. Probe success is consistency only, not a preparation or an evaluation.

Pinned source evidence is Desk commit `605630a535a25292a40926ba72e269de03b951e7`:
[input_handoff.go](https://github.com/Judgment-Pack/judgment-pack-desk/blob/605630a535a25292a40926ba72e269de03b951e7/internal/desk/input_handoff.go#L25-L111)
fixes the existing source/tool/endpoint/adapter tuple and current adapter version `1`;
[its snapshot and filtered-values paths](https://github.com/Judgment-Pack/judgment-pack-desk/blob/605630a535a25292a40926ba72e269de03b951e7/internal/desk/input_handoff.go#L128-L271),
[availableInputValues](https://github.com/Judgment-Pack/judgment-pack-desk/blob/605630a535a25292a40926ba72e269de03b951e7/internal/desk/input_handoff.go#L471-L486),
[input_research_journal.go](https://github.com/Judgment-Pack/judgment-pack-desk/blob/605630a535a25292a40926ba72e269de03b951e7/internal/desk/input_research_journal.go#L17)
and [openInputResearch](https://github.com/Judgment-Pack/judgment-pack-desk/blob/605630a535a25292a40926ba72e269de03b951e7/internal/desk/input_research_journal.go#L112-L119)
fix the retained paths and run-id grammar; and
[input_typed_research.go](https://github.com/Judgment-Pack/judgment-pack-desk/blob/605630a535a25292a40926ba72e269de03b951e7/internal/desk/input_typed_research.go#L8-L50)
resolves the original declaration revision. None of these current paths implements the new full
history/inventory comparison or adapter version `2`. A support claim needs evidence from the
actual newly pinned producer; this historical source citation cannot supply it.

### Complete serialization-layer accounting (proof still required)

Count the bytes of each **actual complete serialized artifact** with its selected encoder.
Let `Q_E(t)` be the UTF-8 byte length of JSON string encoding exact text `t` using encoder E,
including its surrounding quotes. Each nested serialization applies its own Q; a decoded
byte length is never a substitute. For a serializer that leaves scalar non-ASCII literal,
uses short escapes where available and no optional escapes, Q equals raw UTF-8 length plus
2, plus 1 for each quote/backslash/short-escaped control, plus 5 for every other C0 control.
An encoder using HTML, Unicode or solidus escapes needs its actual additional charge.
Encoder behavior must be pinned and tested at every transition, including outer stores.

The accounting ledger must follow all these layers without dropping a copy:

| Artifact | Bytes that must actually be charged |
| --- | --- |
| Published and bound documents | Each complete changed document, including rule spelling/escaping; count both `source.import` publication and bound `source.mapping` when present, and every binding document/copy. Immutable original publications keep their identities. |
| Asserted case | Complete original case/provenance/prepared values plus appended frame; after retention charge `Q_E(exactCaseText)` and the `retainedCaseJson` member/container, once at each real embedding. |
| Generated carrier | All four wrapper members, including `Q_E(originalSnapshotJson)`, exact frame and full inventory. Carrier/frame limits remain additional constraints within the combined bound. |
| Grant and adapter stdout | Their complete wire forms, including any wrapper/string escaping, metadata, arguments, salts, receipts and protocol delimiters that their transport counts. Measure each separately. |
| Signed response | Complete envelope `result`, `receipt`, `salts`, signature and all ordinary metadata; check its raw transport bytes before decoding. |
| Retained source | `Q_E(exactSignedEnvelopeText)` plus the `retainedResponseJson` member/container. Do not add an object copy or charge only the decoded envelope. |
| Complete combined input | Actual retained source/case custody slot, both documents and bindings, all sibling acquisitions, arguments, salts, receipts, signatures and provenance at their serialized locations. No extra allocation outside this bound. |
| Preparation | Complete actual preparation, target/source/read metadata, all per-target reference fragments, inline applied results or omission reasons, conditional identities, basis arrays and signatures/commitments. Count repeated output values and metadata even when input refs share a frame. |
| Verification/export and signed record | Each complete actual enclosing artifact, including every source/input/preparation/record copy and every further escaped text layer it really stores. A preparation-sized fragment is not proof for its export or record. |

For a given unchanged input, compute growth by replacing each old serialized custody slot
with its actual new serialized slot and adding growth of **both** documents and any new
metadata; preserve every unaffected sibling. For complete preparation/export/record, measure
their actual separately emitted bytes rather than deriving a maximum from the combined bound.
Fixed-length hashes/signatures do not grow merely when content changes, but their containers,
independently growing inventories, basis arrays, result JSON and further embedded copies do.
All role limits apply together; fitting one 3 MiB transport does not prove complete combined,
preparation, record, storage or export support. Never enlarge global request, parser or canonical bounds
by implication, clip inputs, omit provenance or narrow previously usable spelling/type scope.

The accounting domain is the existing pinned Desk projection, preserving all five conversions,
eight original field types, original unfiltered values/declarations, opaque provenance, omission
and availability distinctions and every old sibling. This is an analysis of that compatibility
domain, not a restriction of generic retained-column syntax or permission to discard data.
The actual old complete input jointly bounds variable components at C=2097152/4194304, with
F=256/512 fact targets, E=128/256 evidence targets and L=F+E. The asserted ingress retains its
100-column, 160-byte-name and 16000-byte-cell constraints. Generated reviewed input is jointly
bounded by its complete 524288-byte original snapshot and complete old response; its unfiltered
`record.values` strings do not inherit the CSV cell ceiling. Existing column/name/count bounds
stay with their original owners. The new producer must load and compare the complete original history inventory.
A successful extraction cannot prove that this history was loaded.

The RFC's informative serialization analysis and historical witnesses motivate this selected
table. They are not actual product-boundary acceptance evidence. Complete compatible-envelope
and one-over proof remains required at every production owner before support is advertised.

Before acquisition, grant creation or evaluation, consumers require the exact adopted Spec
identity, `retained-column/1`, the selected profile and every role-specific reported limit:
Runtime document validation; Runner conversion preview, preparation and recomputation;
and producer/carrier/transport support. Unsupported support preserves an inspectable draft
and refuses before side effects. No capability is inferred from integer/named carrier
versions, an installed binary version, `semanticValidation:true` or this candidate. Extended
is advertised only when all existing extended requirements work. Raising document bytes
must not silently raise `MaxNodes` or `MaxStringBytes`. Immutable old releases, artifacts,
recipes and subscriptions retain their identities.

A product support claim is conditional on real producer/preparer admission, complete preparation and
record accounting, independent production recomputation, historical vectors, boundary and
one-over tests, exact-head CI and review. Serializer probes and arithmetic are not those
production gates. This candidate records no completion of those gates.

### Resource ceilings

Negotiate the companion profile before byte-bound processing or any acquisition/evaluation.
Known unsupported profiles give `profile-unsupported`; unknown profiles are malformed. Apply
Core §4.1's ordinary combined dialect/case/acquisition ceiling (2097152 base, 4194304 extended
bytes), dialect ceiling (131072/262144) and preparation ceiling (8388608/16777216) unless an
exactly selected implemented retained-column role applies the scoped table above. Target counts
(256/512 facts, 128/256 evidence), document nesting (64/128) and independent work budgets remain.
A frame is additionally bounded by the selected frame and combined ceilings; it does not get an extra allocation outside it. Fixed new
frame limits are 1000 values, 1000 declaration entries and 1000 field entries. Each raw
`values` string is at most 16000 UTF-8 bytes for asserted frames and 524288 UTF-8 bytes for
generated frames; the generated snapshot projection applies the same 524288-byte value bound.
This is a safe compatibility bound derived from the entire original snapshot ceiling, not a
claim that a value of that size can coexist with the required snapshot structure. All complete
snapshot, frame, carrier and combined limits still apply independently. These value ceilings
are fixed in Base and Extended, with no automatic doubling. JSON Schema maxLength counts
characters; readers independently enforce these UTF-8 byte limits. Other fixed bounds are
16384 bytes per fieldJson, nesting 32 inside fieldJson and nesting 64 inside retained raw values
(the existing research duplicate reader limit).
The legacy conversion/type limits stated above are FIXED compatibility constraints, not doubled
by extended. Frame members and embedding overhead count in the genuine carrier budget. Exceeding
a supported ceiling is `input-over-bound`. Never clip fields/declarations, drop rows or silently
reduce a supported input profile. The maximum formerly accepted envelope must be compared with
the actual projected envelope before adoption. If expansion cannot fit, propose an explicit
reviewed ceiling/profile amendment; the present limits do not establish full-envelope parity.
The Unicode `valueJson` member preserves raw JSON within the pinned supported ingress/storage
boundary described in the informative RFC evidence, including escaped lone-surrogate legacy strings. It does not
transport arbitrary invalid-UTF-8 host bytes. A broader arbitrary-host-import promise would need
a separately reviewed closed raw-byte representation, such as a mutually exclusive base64 member
whose decoded bytes are hashed and validated without repair. This contract adopts no such broader promise or encoding. Excluding unreachable raw bytes from the pinned public-path claim does
not authorize rewriting retained data or dropping any previously usable input.
The informative RFC retains the concrete boolean-spelling document-ceiling counterexample.
The selected scoped table addresses the selected encoding; it does not establish completed
maximum-envelope parity or authorize a narrower compatibility domain.

The prototypes check exact snapshot restoration, explicit synthetic capability declarations, frame
parsing, embedded raw parsing, conversions and reference lineage fragments and sole-text custody slots only. They do not claim
actual transport admission, whole acquisition/preparation accounting or production negotiation.

## Adoption evidence and compatibility gate

The complete existing Desk supported ingress/storage domain remains the compatibility domain:
all five conversion kinds, eight original types, raw spellings, ordinary/generated records,
original revisions, unfiltered values and complete provenance. No scope reduction, clipping,
automatic migration, current-type fallback or discarded sibling is authorized.

The maximum-envelope and actual producer/history evidence described above remains required
before a corresponding production support claim. A fixture or analytic inequality is not that
evidence. The source identity and status of every concrete product witness must remain accurate.
Independent review, exact-head CI, adopter-feedback disposition and immutable release gates are
separate requirements; this candidate records no completion of them. Same-vendor Codex review
under the expressly authorized bounded exception is identified as such, never as cross-vendor
compliance or independent authorship. The published RC1 and final 0.3.0 milestone remain intact.

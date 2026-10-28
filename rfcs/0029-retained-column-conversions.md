# RFC 0029: Retained column conversions

- Status: Accepted
- Type: Standards track, draft maturity
- Created: 2026-10-25
- Tracking: Judgment-Pack/judgment-pack-agent#171
- Selected leaf contract: `retained-column/1`

## Adoption at draft maturity

The design is accepted at draft maturity for the scoped `v0.3.0-rc.2` route recorded in
[the adoption pull request](https://github.com/Judgment-Pack/judgment-pack-spec/pull/274).
[The selected companion](../spec/retained-column.md), new versioned schema/corpus and
both-language offline readers carry the exact selected contract. Published RC1 remains
immutable and final v0.3.0 milestone #2 remains open. Acceptance permits this RC2 distribution;
it does not establish immutable publication, stable interoperability, production Desk cutover
or completion of Agent #171.

Note (2026-10-28): the accepted route's final distribution is `v0.3.0`; the RC2 wording above records the candidate's history.

The [adoption disposition](https://github.com/Judgment-Pack/judgment-pack-spec/pull/274#issuecomment-6431106029)
records same-vendor OpenAI Codex review under the authorized exception and dispositions of the
pre-adoption RFC comments at draft maturity. It judges the public review window and substantive
review work sufficient under the maintainer's scoped RC2 authorization; it claims neither a fixed
waiting period nor outside-adopter feedback. It does not establish cross-vendor review or
independent authorship. RFC 0000 and GOVERNANCE are unchanged. The final Core adopter period,
feedback disposition, final corpus and maturity gates remain required.

That record independently closes C1 and the supported immediate/published/frozen reference
correspondence. Its corrected maximum-envelope ledger supersedes the original sufficient-total
table in the earlier public proof comment, with the stated source/history premises and limitations.

## Summary

Add closed converted-copy and evidence-availability variants to Dialect reads. Their source is
an explicitly retained raw column frame. Five conversions preserve existing Desk preview
behavior, including historical research declarations and original JSON spelling. Conversion
policy enters the checked document and its identity instead of remaining executable sidecar data.
This RFC preserves the design and prototype history. Its adjacent prototype schema/cases remain
informative; the selected companion and versioned artifacts carry the accepted RC2 contract.
Acceptance changes no preparation version and is separate from immutable release publication.

## Problem

A two-member copy can carry a prepared value but cannot express how raw retained text became
that value. Replaying that copy cannot recompute boolean spellings, blank filtering or the
original research type. Treating the result as raw input loses the conversion policy and hides
preview-versus-execution differences. Authors need all five existing kinds, ordinary asserted
rows, generated rows, and original declaration types `string` and `number` as well as modern types.
A narrower new authoring profile does not solve that interoperability requirement.

## Evidence

The source-derived cases in [cases.json](retained-column-conversion/cases.json) retain the
36 expectations from the compatibility assessment, with additional handwritten bounds and
refusals. They are not recordings of either prototype. Source anchors are Desk commit
`605630a535a25292a40926ba72e269de03b951e7`, conversion blob
`4dd4fa466960b38364636d684b192a62a9bcf1a9`, research-value blob
`f7b217f55eb0e5e9a9439c3d3b89976ab8450039`, typed-research blob
`a7d77cf8d6175a2b151f3a451a9cad8f94a2b652`, and private decoder blob
`e31c7ad0d3d7a98cf9f3f5bf0e597a720f3eeb06`. These are design anchors, not
proof that this proposal ran through Desk. Historical string-map JSON decoding maps column
null to the zero string; the proposal omits it while retaining its distinct raw input identity.
Runner commit `503f2b494276509505ae97e365f4bcf738a4b4e4` refuses fractional,
exponent and unsafe number claims. A compatible preview does not remove those refusals.

A bounded extracted-helper comparison uses the exact pinned `convertInput` and `sameDecimal`
function bodies (source lines 70–115 and 216–223), their declarations and regular expressions.
Under Go 1.26.10, both draft readers agree on 34 number conversions (15 existing handwritten
cases plus 19 handwritten boundaries) and all seven existing shortest-decimal probes. No expected
result was changed to match execution. This closes the bounded numeric comparison task, not an
exhaustive claim or whole Desk execution evidence. The two prototypes remain same-author/model.

Pinned supported ingress also bounds the retained data compatibility question. `inputRequest`
(`input_preparations.go` lines 134–154) rejects invalid UTF-8 before decoding imports and recipes.
`decodeResearchAction` (`input_research_model.go` lines 68–74, blob
`9a35db1755faa6bfea47763b7e24755191e0a648`) admits at most 128 KiB and calls
`decodeDataJSON`; that decoder (`private_data.go` lines 185–201) rejects invalid UTF-8.
V2 record batches call it again (`input_research_records_v2.go` lines 246–260, blob
`bc09d4e997f1a8ef6b5e7aa1f22949d970067d3f`). Persisted preparations use the same
decoder. Thus arbitrary invalid-UTF-8 raw JSON accepted by the isolated legacy helper is not a
usable retained value through these pinned supported ingress/storage paths. ASCII JSON with an
escaped lone surrogate is distinct: the legacy string exemption can retain it, `valueJson` can
transport its exact spelling, and the unchanged canon boundary still refuses execution.
This is source-contract reachability evidence, not an HTTP, model-provider or whole Desk run.

## Specification

This section preserves the design's proposal and amendment history. For the accepted selected
RC2 contract, [the companion](../spec/retained-column.md) and its pinned versioned schema/corpus
control; historical statements about pending adoption below describe the prototype stage.

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
The complete structural companion is [contract.schema.json](retained-column-conversion/contract.schema.json).
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
while Runner still refuses that exponent claim. The adjacent readers implement the selection
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

This amends an unadopted Draft proposal, not a released `retained-column/1` contract. New
exact schema/corpus pins are required; old closed readers gain no implicit support.
Existing envelope versions and historical optional-member absence stay unchanged; old closed
readers refuse unsupported lineage. Rules enter read/dialect identity. Frame identity and complete
original declaration inventory commitments bind the checked projection; source/recipe identities
stay separate. Changes to source, column, kind, spelling, raw bytes, declaration or revision
invalidate their relevant commitments and require fresh checking and ordinary CAS/review.
Editor sidecars must equal document-derived rules and confer no separate execution authority.

The Draft wire shape is `capabilities.conversionContracts:[entry,...]`, not a string list
or a boolean support flag. Each entry is a closed object with required `contract`, `spec`,
`profile`, `role` and `limits`, and only the optional `producerGrammar` described in the proposed
producer section below for its three applicable roles. `contract` is exactly `"retained-column/1"`; `profile` is exactly
`"base"` or `"extended"`. `spec` is closed with exactly `version` (nonempty version label),
`revision` (40 lower-case hex characters identifying the exact Spec commit), `schemaSha256`
and `corpusSha256` (each `sha256:` plus 64 lower-case hex characters). For a Draft experiment,
version names Draft maturity and the digests identify the exact adjacent schema/cases bytes;
a normative release needs its own immutable artifact inventory. Test example pins are synthetic
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
Maxima are declared capacities, not a selected proposal's adoption. Every traversed owner must
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
`semanticValidation:true`, an installed binary's version or this Draft. All existing review,
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
its own digest, and the corpus does not hash itself. Draft prototype constants are visibly
synthetic test installation pins, granting no product support. The final actual revision and
schema/corpus bytes must be selected only after the artifact set is frozen and reviewed.

A transport conveys and validates this bounded selector before reading a body beyond ordinary
limits. Header/route encoding is an adapter detail; this RFC specifies no Runner route name.
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

### Proposed complete carrier amendment (pending adoption)

The selected Draft proposal below supersedes the earlier 6/12 MiB combined, 3 MiB
signed-response and 8/16 MiB preparation targets. It is a scoped proposed contract for the
pinned asserted CSV/URL and reviewed generated-record projection, not implemented product
support or normative adoption. Extended remains conditional on all existing Extended requirements;
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

For generated reviewed input, this Draft defines a new closed versioned result with exactly
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
source checks; successful Draft preparation retains only the exact received envelope text.
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
Initial case object admission remains available; successful Draft preparation with retained
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

### Proposed producer grammar and complete original inventory

The generated wrapper remains exactly the four members above. Its signature domain remains
Gateway `canon` over the wrapper, under the existing acquisition receipt and frozen request.
This section proposes producer grammar `desk-reviewed-input/1`; it does not adopt it or claim
that the current producer implements it. In particular, the current Desk adapter reports
version `1`; the grammar below requires a newly implemented and reviewed version `2`.

**Trusted binding.** A proposed optional `retainedColumnProducer` member of the installation's
trusted InputProfile is closed with exactly `contractVersion:"1"` and
`grammar:"desk-reviewed-input/1"`. It enters the existing complete profile digest. This Draft
changes no normative profile schema. A source using this grammar is an operation bound to
that profile's exact id/digest. The independently trusted profile must have class `generated`,
shape `mcp`, source `desk-inputs`, endpoint `desk-local:reviewed-inputs`, exactly the tool
`read_reviewed_input`, and adapter name `jpack-desk/reviewed-input`, proposed version `2`, and
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
role; a prototype probe or proposed adapter version is not a support declaration.

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
opaque siblings. They are not silently dropped and this Draft does not falsely declare the full
snapshot closed. Instead the reader explicitly extracts the following closed projection, as
`deskSnapshotProjection` in the adjacent experimental schema specifies. This projection is
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
accounting gates below remain unresolved. Opaque original JSON may retain legacy escaped lone
surrogates, but selected field/frame strings keep their existing well-formed-string rules.

**Executable consistency probe.** `{generatedConsistency:{carrier,profile,limits,trustedProducer,
sourceBinding,receiptResultDigest,rule}}` uses the closed shapes in the experimental schema.
`limits` is exactly `originalSnapshotBytes`/`carrierBytes`. The profile and digest inputs are
independent integration seams; this line protocol cannot authenticate them. The probe checks the
proposed producer tuple and source binding, exact restoration, the supplied result digest against
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
history/inventory comparison or the proposed adapter version `2`. Those remain real producer work.

### Complete serialization-layer accounting (proof still required)

Count the bytes of each **actual complete serialized artifact** with its selected encoder.
Let `Q_E(t)` be the UTF-8 byte length of JSON string encoding exact text `t` using encoder E,
including its surrounding quotes. Each nested serialization applies its own Q; a decoded
byte length is never a substitute. For a serializer that leaves scalar non-ASCII literal,
uses short escapes where available and no optional escapes, Q equals raw UTF-8 length plus
2, plus 1 for each quote/backslash/short-escaped control, plus 5 for every other C0 control.
An encoder using HTML, Unicode or solidus escapes needs its actual additional charge.
Encoder behavior must be pinned and tested at every transition, including outer stores.

The pinned original snapshot bound remains 524288 bytes. The pinned compact Go snapshot
has no literal C0 controls or unescaped `<`, `>` or `&`; its downstream canonical encoder
keeps UTF-8 non-ASCII literal. Thus its first string encoding obeys `Q_E(S)<=2*|S|+2`
for those encoders. This bound does not cover arbitrary encoders or a second quoting layer.
A prior projection estimate charged up to three times disjoint retained components plus
65536 structure bytes (two times only under separately verified 30-field ASCII-name
constraints). That estimate is not a proof for complete signed-response text or case text.

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

The previous `6050048/12034304` combined estimates counted two changed document copies but
omitted the complete signed-envelope/case string retention layer. They are superseded as
complete-envelope evidence. The complete-artifact proposal above replaces those targets;
it has conditional accounting evidence, not actual product-boundary proof. The old 524288
snapshot, 1048576 grant and ordinary channel limits remain unchanged; a new producer channel
requires its own reviewed selection. Generic larger profiles/receipts are not inferred.

The accounting domain is the existing pinned Desk projection, preserving all five conversions,
eight original field types, original unfiltered values/declarations, opaque provenance, omission
and availability distinctions and every old sibling. This is an analysis of that compatibility
domain, not a restriction of generic retained-column syntax or permission to discard data.
The actual old complete input jointly bounds variable components at C=2097152/4194304, with
F=256/512 fact targets, E=128/256 evidence targets and L=F+E. The existing producer's 524288-byte
snapshot, 100 columns, 160-byte column names, 16000-byte cells and complete old response bound
are used together. The new producer must load and compare the complete original history inventory.
A successful extraction cannot prove that this history was loaded.

For the fixed compact Go / literal-UTF8 JavaScript producer families, Q is the actual downstream
Go JSON string encoding, including quotes. The old compact Go text has Q(t)<=2|t|+2. Literal
JavaScript HTML is charged by its Go-equivalent component size for this inequality only; raw
custody bytes are never rewritten. Every further text embedding applies Q again. Arbitrary
pretty printers or ASCII-inflating encoders need separate accounting; consumers still measure
their actual bytes. A generic 64 KiB receipt allowance is not assumed. Old metadata stays inside
C; only bounded new tuple spelling/profile bookkeeping is charged separately.

A conservative per-document growth G=F*2977+E*1011+4096 gives G=895616/1787136.
Two changed published/bound documents each add G. The asserted complete combined bound is
4*C+2*G+65536 = 10245376/20417024. With S=524288, generated carrier
W<=5*S+65536+256=2687232, generated frame<=3*S+65536=1638400, and complete response
R<=min(C,2097152)+W+4096=4788480. The old gateway may normalize escapes; subtracting the
raw snapshot length from the old response would be invalid. Retaining the sole exact response
string gives combined<=C+min(C,2097152)+2*W+8192+2*G+65536 = 11433728/15313920.
These inequalities charge the second string layer explicitly. They fit the proposed 12/24 MiB
combined caps; raw response fits 5 MiB, while carrier/grant/stdout fit their separate 3 MiB caps.

Preparation must also count basis repeated L+1 times, inline results and every target's
metadata. Under the unchanged old aggregate prepared-value budget U<=C, the conservative bound is
65536+10240*L+(L+1)*(12*L+1)+3*C+8*F*1024+1549*E+2*F
= 14359553/32192513, below 16/32 MiB. The old normalizer could emit preparations that its
offline verifier refused, so old offline acceptance is not assumed as a preparation bound.
The record proposal charges old record bytes plus 2*F+65536, giving 8454656/16843776 below
9/17 MiB. This provisional record lemma depends on actual Runtime preserving its existing trace
shape; restored negative-zero endpoints can add bytes. It does not assert record byte/hash identity
or waive the answer-change review gate. Actual Runtime boundary evidence remains required.

A verification bundle retains independent release.sample and run.input plus release.inputMapping.
Count both complete new input/preparation copies and the third mapping. With old export base
V0=8/16 MiB and selected A=12/24 MiB, T=16/32 MiB, M=1/2 MiB:
release<=V0+A+T+M+65536=38862848/77660160;
stored run<=V0+A+T+4*F+65536=37815296/75565056;
export base<=V0+2*(A+T)+M+6*F+131072=68290048/136449024.
For versions 3/4/5, raw audit bytes are additionally base64 alongside parsed audit. Complete
wire<=selected exportBaseBytes+4*ceil(selected recordBytes/3)+65536
=88145920/174828204, fitting 86/168 MiB. Existing bounded signature sidecar, chain and checkpoint
remain separately checked, with version-aware base exclusions. An adapter that embeds the whole
export as JSON text must apply Q again; these wire caps do not authorize that different transport.

These are conservative analytic bounds and actual encoder checks on structural fragments.
They are not authenticated product admissions, maximum end-to-end runs or adoption evidence.
Every source assumption, whole-artifact boundary, lower caller limit and one-over refusal must
be confirmed by the actual selected producer, Runtime and Runner before declaring support.

A focused Runner witness now exercises the unchanged ordinary authenticated input entry
with one 16000-TAB asserted column reused by 256 distinct text targets. The pinned Desk pure
normalizer/qualification/preparation bodies retain the column and omit all blank prepared
values; the ordinary Runner entry accepts its 50844-byte request and emits a 1322969-byte
preparation that passes offline preparation checking, plus a 1406838-byte checked export.
This is the actual ordinary path in the candidate Runner, not a historical binary or full
Desk server/browser/persistence run. The corresponding projected request is 97559 bytes and
refuses at the unchanged 8388608-byte preparation limit. Its compact selected input JSON has
32002 bytes; each nested inline JSON string is `3*16000+6=48006` bytes, so input copies alone
charge `256*48006=12289536` bytes. The 13186521-byte diagnostic preparation and 13331607-byte
diagnostic export are assembled refused artifacts, not accepted/emitted candidate outputs.
Replacing only input states by the closed references measures 924633 diagnostic preparation
bytes; every target result, metadata and basis remains counted. This refutes inline-input
sufficiency for that admitted ordinary case, but proves neither reference-path admission nor
Base/Extended maxima. The real reference path, complete original-snapshot escaping families,
maximum siblings/bindings/results and boundary/one-over artifacts remain production gates.
The adjacent tiny serializer fixtures establish exact counts only for those encoders/inputs.

Before acquisition, grant creation or evaluation, consumers require the exact adopted Spec
identity, `retained-column/1`, the selected profile and every role-specific reported limit:
Runtime document validation; Runner conversion preview, preparation and recomputation;
and producer/carrier/transport support. Unsupported support preserves an inspectable draft
and refuses before side effects. No capability is inferred from integer/named carrier
versions, an installed binary version, `semanticValidation:true` or this Draft. Extended
is advertised only when all existing extended requirements work. Raising document bytes
must not silently raise `MaxNodes` or `MaxStringBytes`. Immutable old releases, artifacts,
recipes and subscriptions retain their identities.

This proposal is conditional on real producer/preparer admission, complete preparation and
record accounting, independent production recomputation, historical vectors, boundary and
one-over tests, exact-head CI and review. Serializer probes and arithmetic are not those
production gates. No normative adoption or support claim follows from this amendment.

### Resource ceilings

Negotiate the companion profile before byte-bound processing or any acquisition/evaluation.
Known unsupported profiles give `profile-unsupported`; unknown profiles are malformed. Apply
Core §4.1's ordinary combined dialect/case/acquisition ceiling (2097152 base, 4194304 extended
bytes), dialect ceiling (131072/262144) and preparation ceiling (8388608/16777216) unless an
exactly selected implemented retained-column role applies the scoped table above. Target counts
(256/512 facts, 128/256 evidence), document nesting (64/128) and independent work budgets remain.
A frame is additionally bounded by the selected frame and combined ceilings; it does not get an extra allocation outside it. Fixed new
frame limits are 1000 values, 1000 declaration entries, 1000 field entries, 16000 bytes per raw
column string, 16384 per fieldJson, nesting 32 inside fieldJson and nesting 64 inside retained raw values
(the existing research duplicate reader limit).
The legacy conversion/type limits stated above are FIXED compatibility constraints, not doubled
by extended. Frame members and embedding overhead count in the genuine carrier budget. Exceeding
a supported ceiling is `input-over-bound`. Never clip fields/declarations, drop rows or silently
reduce a supported input profile. The maximum formerly accepted envelope must be compared with
the actual projected envelope before adoption. If expansion cannot fit, propose an explicit
reviewed ceiling/profile amendment; the present limits do not establish full-envelope parity.
The Unicode `valueJson` member preserves raw JSON within the pinned supported ingress/storage
boundary described in Evidence, including escaped lone-surrogate legacy strings. It does not
transport arbitrary invalid-UTF-8 host bytes. A broader arbitrary-host-import promise would need
a separately reviewed closed raw-byte representation, such as a mutually exclusive base64 member
whose decoded bytes are hashed and validated without repair. No such broader promise or encoding
is adopted by this RFC. Excluding unreachable raw bytes from the pinned public-path claim does
not authorize rewriting retained data or dropping any previously usable input.
A concrete source-derived size witness shows that the existing extended dialect ceiling is
insufficient for this grammar's full legacy spelling scope. One CSV column has a 160-byte name;
119 distinct nonoverlapping fact targets share a boolean conversion with distinct 160-byte
spellings of U+0000 and U+0001. These are scalar UTF-8 strings and are nonblank under the pinned
whitespace set. Each control codepoint takes six JSON bytes. `normalizeInputImport`
(`input_preparations.go` lines 353–390) allows the one-column CSV and its 160-byte cell;
`validateInputQualification` (`input_qualification.go` lines 134–158, blob
`f3581e405dfd2271f2d86ab533e53424b9457497`) allows up to 1000 case facts, while this
witness stays below the existing 256 executable fact-target ceiling. `validateInputConversions`
(lines 44–69 of its pinned source) admits these distinct nonblank 160-byte spellings.

The old mapping is 23740 bytes and mapping plus sidecar is 259150 bytes. The complete synthetic
public recipe request is 270215 bytes; the CSV import request is 1176 bytes, both below the
2097152-byte ingress ceiling. The source-constructor-shaped old prepared input is 245437 bytes,
also below its 2097152-byte limit. Its synthetic Core pack passes structural schema validation.
The new declared document is 263912 bytes, or 263933 with explicit `profile:"extended"`, exceeding
262144. The frame adds 1196 bytes, so the combined ceiling is not the failing constraint here.
At 118 targets the same extended document family is 261716 bytes; 119 is its first failure,
not a claim of the globally smallest counterexample. These are exact compact JSON byte counts
for source-contract-admissible shapes; whole Desk HTTP admission, Runtime validation and real
preparation were not executed. The original shape/byte witness is not a forged preparation.

Consequently the proposed encoding and current ceilings cannot yet establish full compatibility.
Before adoption, either review explicit adequate document ceilings with real capability
negotiation and combined-envelope proof, or review a closed lossless compact policy encoding and
prove its worst case. Merely choosing today's extended profile is insufficient. The explicit
conditional document/combined proposal above is the Draft candidate, with no
adopted production ceiling selected; no installed ceiling is silently waived.

The prototypes check exact snapshot restoration, explicit Draft capability declarations, frame
parsing, embedded raw parsing, conversions and reference lineage fragments and sole-text custody slots only. They do not claim
actual transport admission, whole acquisition/preparation accounting or production negotiation.

## Alternatives

No change leaves executable conversions outside the checked read. Product-only preconversion
cannot provide portable recomputation. Extending quality targets to arbitrary JSON would change
its null/blank contract and still obscure original types. A restricted profile dropping number,
legacy types or original spellings is superseded by the full compatibility decision. A whole
new carrier version would force unrelated recipe/publication migration; a closed versioned leaf
lets old readers fail closed while preserving old documents byte for byte.

## Compatibility

Reader: old readers reject new members; unchanged historical integer/named documents retain
meaning, encodings and digests. Writer: emit the new leaf only after exact capability checks;
otherwise preserve inspectable drafts and report unsupported support. Semantic: the new variants
explicitly preserve legacy filtering and raw JSON while keeping current execution refusals.
Migration: construct a new checked projection from sufficient original retained history; no
current-type fallback, singleton invented declaration or automatic rewrite of old releases,
subscriptions, qualifications, receipts or recipes. Publication remains an explicit separate
operation. No automatic migration exists when original declarations/bytes are unavailable.
An incompatible future change needs a new exact leaf version, never reinterpretation of 1.
Adoption must name its exact supported Spec version, schema identities and complete corpus.
Published RC tag/assets remain immutable; reasonable feedback and final release gates still apply.
If adoption occurs after final publication it goes into the next appropriate immutable release.

## Security and privacy

Frames are data and provenance assertions, not trust, authorization or proof of truth. Opaque
field members and JSON strings cannot introduce commands or new policy. Strict UTF-8, duplicate
rejection before map construction, scalar validation, bounded nested parsing, and exact rational
arithmetic prevent divergent readings and bound work. Raw retained declarations/values can reveal
sensitive data: keep them within the existing reviewed acquisition/retention channel and avoid
echoing them into public diagnostics. No customer, credential or production data appears here.
Capabilities cannot waive approval or receipt checks. Resource expansion must be reviewed before
an implementation makes a broader availability claim.

## Conformance

The adjacent cases cover each kind, eight original declarations, absence/null/blank/status,
original precision/negative zero, invalid forms and current claim refusal. Closed input
references, exact response/case text custody and wrong digest/location/column/unresolved
references have paired handwritten cases. Equal-frame wrong-source refusal requires the
production source-binding reader; these local probes authenticate no source. Additional structural,
duplicate/scalar, version, tie, exponent/range ordering and byte-bound probes are handwritten.
The check harness runs both readers on identical requests and asserts expected outputs; expected
results are never generated from a reader. Structural schema probes are separate from semantic
checks. These are draft local cases, not the published corpus and not real producer/verifier
interoperability. Future adoption needs real Runtime document validation, real Runner preparation
and offline recomputation, tampered rule/frame/declaration/lineage refusal, unchanged historical
vectors and maximum-envelope comparisons. Full integrated checklist/CI and review are separate.

## Implementation

Python uses Fraction and binary64 midpoint intervals. JavaScript uses BigInt rational arithmetic
and decoded binary64 bits. They independently implement the algorithm but have the same author
and assisting model, so are neither independent authorship nor stable interoperability evidence.
Two plausible independent production implementations are a Go exact-rational conversion library
used by Runner, and a separately authored Python/TypeScript offline recomputation reader after
contract acceptance. Runtime owns full document validation, Runner owns acquisition/preparation,
and Agent owns checked authoring projections. Runner PR 146's shared mapping files remain in its
existing ownership lane. These prototypes do no provider calls and invent no preparations.

The maintainer authorized a same-vendor Codex exception for this bounded draft work. The
adoption pull request records that basis and the review dispositions. This is independent
review by separate Codex sessions, not cross-vendor review or independent implementation
authorship, and it does not modify GOVERNANCE.md.

## Unresolved questions and remaining gates

Acceptance ratifies the selected leaf union, number algorithm/legacy issue mapping,
historical-null rule, closed references, exact custody, conditional lineage and selected
role ceilings through the companion. Exact schema/corpus identities are pinned for RC2;
no released contract is reinterpreted. The following limits and gates remain explicit:

- Keep compatibility tied to the pinned supported ingress/storage and original producer/history
  premises. A broader arbitrary-host raw-byte importer needs separate review; the isolated legacy
  helper does not establish that surface.
- The bounded number/helper comparison includes underflow, decimal ties and range/exponent
  diagnostic precedence. Actual Desk tool-path comparison remains separate; extracted helpers
  and same-author readers establish no independent whole-application evidence.
- The corrected maximum-envelope ledger is a conservative sufficient bound under its stated
  source/semantic/history premises, not a measured global maximum or a whole Desk lifecycle
  run. Preserve its original-inventory and target correspondence conditions; do not infer
  arbitrary external mapping/history support or Extended preparation support.
- Production original-inventory verification, complete signed snapshot/frame relations and
  original-history custody remain product gates. The prototypes do not authenticate profiles,
  verify receipt signatures or load original history. Production Desk cutover is separate.
- Real independent production implementation evidence, applicable exact-head product checks,
  immutable RC2 artifact verification and final Core feedback/conformance gates remain required.
  This acceptance does not complete Agent #171, general Core conformance or final v0.3.0.

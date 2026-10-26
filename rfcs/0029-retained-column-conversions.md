# RFC 0029: Retained column conversions

- Status: Draft
- Type: Standards track, draft maturity
- Created: 2026-10-25
- Tracking: Judgment-Pack/judgment-pack-agent#171
- Proposed leaf contract: `retained-column/1`

## Summary

Add closed converted-copy and evidence-availability variants to Dialect reads. Their source is
an explicitly retained raw column frame. Five conversions preserve existing Desk preview
behavior, including historical research declarations and original JSON spelling. Conversion
policy enters the checked document and its identity instead of remaining executable sidecar data.
This RFC and its adjacent schema, handwritten cases and two reader prototypes are a proposal;
they change no normative schema, published capability, preparation version or release.

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

All requirements in this section describe the proposed contract, conditional on acceptance.

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
`{state:"present",json:<selected JSON text>}`. For ordinary columns `json` is the compact
JSON encoding of the retained structured string
or null in `frame.values`: UTF-8 non-ASCII remains literal, C0 controls, quote and backslash
are JSON-escaped, and no optional whitespace or solidus escaping is added. This is not a
claim to recover request spelling that the legacy host discarded. Research uses the exact
retained `valueJson`, including its whitespace and numeric spelling. Missing raw `valueJson`
is missing input; explicit `"null"` and empty `""` raw text are present inputs with different
bytes, even when their selected original type subsequently gives the same issue. Result
is exactly `{state:"value",json:<exact candidate JSON>}` or
`{state:"omitted",reason:"missing"|"blank"|"legacy-null"|"unavailable"}`.
Research identity is exactly `{recipeRevision,fieldSha256}`; hash is `sha256:` plus lower-case
SHA-256 over the exact UTF-8 fieldJson. The representation is inline: every input/result copy
counts at its serialized location; no
pooling, digest substitution or implied reference resolution is selected. Offline recomputation
derives all members from the supplied frame, never trusting retained result members. The Draft
readers expose this recomputation for successful/omitted canon-admissible previews only, not
a whole preparation verifier. Complete preparation/signature accounting and integration into
the existing preparation schema remain prerequisites. No failed execution gains success lineage.
Existing envelope versions and historical optional-member absence stay unchanged; old closed
readers refuse unsupported lineage. Rules enter read/dialect identity. Frame identity and complete
original declaration inventory commitments bind the checked projection; source/recipe identities
stay separate. Changes to source, column, kind, spelling, raw bytes, declaration or revision
invalidate their relevant commitments and require fresh checking and ordinary CAS/review.
Editor sidecars must equal document-derived rules and confer no separate execution authority.

The Draft wire shape is `capabilities.conversionContracts:[entry,...]`, not a string list
or a boolean support flag. Each entry is a closed object with exactly `contract`, `spec`,
`profile`, `role` and `limits`. `contract` is exactly `"retained-column/1"`; `profile` is exactly
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
| preview | documentBytes, combinedBytes, frameBytes | Runner conversion preview; not preparation support. |
| preparation | documentBytes, combinedBytes, frameBytes, preparationBytes, recordBytes | Runner complete preparation and signed record accounting. |
| preparation-verification | documentBytes, combinedBytes, frameBytes, preparationBytes, recordBytes | Offline verifier's independently supported complete input/preparation/record bounds. |
| producer-carrier | originalSnapshotBytes, carrierBytes, grantBytes, adapterStdoutBytes, responseBytes | Producer's exact acquired snapshot and complete wrapper/grant/adapter stdout/signed response transport. |

These limits count each complete serialized artifact, including punctuation, escaping, provenance
and signatures, rather than selected payload members. A document limit applies separately to
each retained published and bound document; combinedBytes counts both documents plus all other
counted case/acquisition bytes. frameBytes is an additional frame constraint within the combined
budget, never an extra allocation. Each preparation/record artifact is separately constrained.
Maxima are declared capacities, not a selected proposal's adoption. Every traversed owner must
support the requested role independently; a Runtime entry cannot authorize Runner or producer
work. All existing target-count, parser node/string-work, nesting and compatibility limits
remain applicable and do not grow when a byte maximum grows.

The array has at most 32 entries and no repeated exact contract/spec/profile/role identity;
an empty array grants nothing. Every declared entry must have the required role members and
no unknown members. An absent capability or unmatched exact identity is `capability-unsupported`;
an unknown contract, role or profile also fails with `capability-unsupported`. Malformed shapes,
missing limits and duplicate identities give `input-malformed`. The selected role's artifact
sizes must all be present as nonnegative safe integers; each must fit the lower of caller-required
and reported limits, otherwise `input-over-bound`. Known unsupported support is refused before
artifact admission, grant creation, dispatch or evaluation; it cannot pass because a payload is
tiny. For a supported identity, malformed declarations and over-bound inputs keep the existing
validation/diagnostic order. The executable `admission` probe checks this declaration and size
comparison before its one instrumented callback; it does not measure an actual producer response
or perform acquisition. Production owners still measure their actual complete artifacts.

Runtime 0.39.0-alpha.1 has no such support. No capability is inferred from carrier versions,
`semanticValidation:true`, an installed binary's version or this Draft. All existing review,
approval, phase, acquisition, mixed-origin, cancellation, unknown-ack/no-retry and CAS guards
remain with their present owners.

### Proposed complete carrier amendment (pending adoption)

The candidate byte table is document 1048576/2097152 and combined
6291456/12582912 for base/extended respectively. It is a conservative proposal for
the complete carrier layout below, not an implemented or adopted limit. The earlier
4194304/8388608 and 5242880/8388608 combined candidates do not establish full parity.
Other Core rows, including target counts, parser node/string work budgets, nesting and
preparation/record 8388608/16777216, do not change by implication. Preparation/record
accounting remains an adoption prerequisite; document byte expansion alone does not prove it.

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

For the pinned supported Desk producer the original snapshot is at most 524288 bytes.
Its compact Go representation has no literal C0 controls or unescaped `<`, `>` or `&`,
and its UTF-8 non-ASCII is retained by the actual downstream canonical encoder. Hence a
quoted exact snapshot of S bytes takes at most 2*S+2 bytes in these encoders. This is not
a bound for arbitrary JSON string encoders: escaping every non-ASCII character can exceed
2*S+2. The producer must fix and test its encoding rather than infer this bound from JSON.
A conservative frame proof charges at most three times disjoint retained component bytes,
plus a 65536-byte structure/provenance reserve. The tighter two-times charge applies only
when the pinned 30-field, ASCII-name producer constraints are separately verified.

Let C be the former complete combined bound (2097152/4194304), and G the conservative
document growth (895104/1790080). One changed counted dialect gives an asserted bound
2*C+G+65536 = 5154944/10244224. With a retained generated snapshot S<=524288 and the
conservative frame charge, its bound is C+G+4*S+65536 = 5154944/8147072.
Pinned Desk's asserted 2097152-byte producer cap gives 5154944/8147072, but cannot justify
the generic extended asserted case. A Core-sized extended asserted source-shaped witness
is 4194304 bytes before projection and 8871801 after appending the frame, above 8388608.
This is a counterexample to that proposed ceiling, not a real Desk/Runner admission run.

Published execution can count a published dialect in `source.import` beside its bound
`source.mapping`. Budget both changed copies: adding a further G gives conservative
complete-carrier maxima 6050048/12034304, below 6291456/12582912. Original immutable
publications are not rewritten; the proposed derivative needs a fresh identity and explicit
publication/binding workflow. All other original acquisitions, arguments, salts, receipts,
signatures, provenance and binding copies remain counted. Unchanged fixed-length digests
and signatures do not grow merely because their contents change. Additional changed
document copies or independently growing receipt/binding metadata need explicit accounting;
these formulas are not permission to omit them or to make unsupported-input claims.

The generated channel also needs its own transport contract. Keep the old 524288-byte
snapshot and 1048576-byte grant boundaries for the legacy channel. For the new pinned closed
profile, a 3145728-byte bound for each complete grant, adapter stdout and signed response
is a candidate: the conservative wrapper is at most 2687104 bytes and an additional
65536-byte receipt reserve gives 2752640. This is separate from the combined bound.
The currently pinned 1048576-byte Gateway default stdout and 2097152-byte Desk response
limits cannot be assumed to admit it. Generic profiles with larger receipts or original
snapshots have not been proved by this calculation and must not be silently narrowed.

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
Core §4.1's combined dialect/case/acquisition ceiling (2097152 base, 4194304 extended bytes),
dialect ceiling (131072/262144), target counts (256/512 facts, 128/256 evidence), document
nesting (64/128) and preparation ceiling (8388608/16777216). A frame is additionally bounded
by the selected combined ceiling; it does not get an extra allocation outside it. Fixed new
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
parsing, embedded raw parsing, conversions and inline lineage fragments only. They do not claim
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
original precision/negative zero, invalid forms and current claim refusal. Additional structural,
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

The maintainer authorized a same-vendor Codex exception for this bounded draft work. It is not
cross-vendor review and supplies no independent evidence. Public comment, the review record with
accurate exception basis, every finding's disposition and normative adoption remain required;
this draft does not record them as completed or silently modify GOVERNANCE.md.

## Unresolved questions

- Keep the compatibility claim tied to the pinned supported ingress/storage boundary. If a
  broader arbitrary-host raw-byte importer is intended, review an explicit byte-preserving
  representation; do not infer that new surface from the isolated legacy validation helper.
- Ratify the leaf union, number tie algorithm/legacy issue mapping, historical-null rule and
  conditional lineage before adopting any normative files.
- The bounded number/helper comparison now passes, including underflow, decimal ties and
  range/exponent diagnostic precedence. Actual Desk tool-path comparison remains separate;
  extracted helpers and same-author readers establish no independent whole-application evidence.
- Resolve the demonstrated document-ceiling incompatibility. Concrete options are an explicit
  reviewed ceiling amendment, or a revised closed compact encoding (for example shared rule
  declarations where applicable). Deduplication must also cover distinct-rule worst cases;
  no clipping or narrowed spellings is acceptable. Complete the maximum previously usable
  combined-envelope proof for the selected option. Existing extended ceilings alone do not fit
  the witness, and current production readers' extended support is not implied.
- Specify the production original-inventory commitment carrier and integrate conditional lineage
  with the existing preparation schema/recomputation owner; prototype results are not that carrier.
- Obtain real independent production implementation evidence and complete review/disposition,
  feedback, exact-head CI and immutable release gates. No completion claim for Agent #171 follows
  merely from this RFC.

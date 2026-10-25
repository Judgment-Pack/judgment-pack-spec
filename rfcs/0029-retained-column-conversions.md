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
`{state:"present",json:<original raw selected JSON>}`. For ordinary columns json is the
literal-preserving source member encoding (including null); research uses valueJson. Result
is exactly `{state:"value",json:<exact candidate JSON>}` or
`{state:"omitted",reason:"missing"|"blank"|"legacy-null"|"unavailable"}`.
Research identity is exactly `{recipeRevision,fieldSha256}`; hash is `sha256:` plus lower-case
SHA-256 over the exact UTF-8 fieldJson. Offline recomputation derives all members from the
supplied frame, never trusting retained result members. No failed execution gains success lineage.
Existing envelope versions and historical optional-member absence stay unchanged; old closed
readers refuse unsupported lineage. Rules enter read/dialect identity. Frame identity and complete
original declaration inventory commitments bind the checked projection; source/recipe identities
stay separate. Changes to source, column, kind, spelling, raw bytes, declaration or revision
invalidate their relevant commitments and require fresh checking and ordinary CAS/review.
Editor sidecars must equal document-derived rules and confer no separate execution authority.

Proposed capability reports add `capabilities.conversionContracts:["retained-column/1"]`.
Runtime advertises document validation/target coverage only. Runner separately advertises
`conversionPreview:true` and `conversionPreparation:true` after each is implemented. Consumers
require the exact leaf capability and applicable role; they infer nothing from carrier versions,
`semanticValidation:true`, an installed binary's version, or this draft. Runtime 0.39.0-alpha.1
has no such support. All existing review, approval, phase, acquisition, mixed-origin, cancellation,
unknown-ack/no-retry and CAS guards remain with their present owners.

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
prove its worst case. Merely choosing today's extended profile is insufficient. Neither option
is selected here; no installed ceiling is silently waived.

The prototypes bound frame parsing, embedded raw parsing and conversions only; they do not
claim negotiation or accounting for a whole acquisition/preparation.

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

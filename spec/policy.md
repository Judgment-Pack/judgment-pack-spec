# Policy content and governing adoption

## Status and artifact scope

This is the Policy companion text proposed for acceptance at **draft maturity**
under [RFC 0023](../rfcs/0023-policy-companion.md). The maintainer authorized that
acceptance conditional on required CI passing and
[PR 218](https://github.com/Judgment-Pack/judgment-pack-spec/pull/218) merging.
Until merge the default-branch RFC remains Review; this branch's acceptance
wording describes the approved draft that takes effect upon that merge. It does
not claim a completed merge, immutable publication, stable maturity or consumer
adoption.

Upon that merge, §§1–8 define the *Policy offline reader* companion class. They do not change Core `0.2.0-draft`, its schema, evaluator
semantics, document corpus or evaluation corpus. The exact document selector is
`formatVersion: "1.0.0"`; that identifies grammar, not stable maturity or a Spec
release. Unsupported readers refuse it without legacy aliases.

The draft normative artifacts are this prose and the closed versioned
[Policy](../schema/policy/1.0.0/policy.schema.json),
[Governing adoption](../schema/policy/1.0.0/governing-adoption.schema.json) and
[shared](../schema/policy/1.0.0/common.schema.json) schemas. Schema acceptance alone
is insufficient: exact retained bytes, anchors, references, coverage, bounds and
refusal order are also required. A disagreement is a specification defect, never
authority to execute. The [124 agreement vectors](../conformance/policy/1.0.0/vectors/manifest.json)
are staged in no released corpus until an exact independent Policy draft release names them.
No Policy offline-reader conformance claim is available before that release.

The [publication plan](../conformance/policy/1.0.0/PUBLICATION.md) follows the
selected independent companion release route and records its conditional-merge
and separate publication gates.
The first independent release identifier is `policy-v1.0.0-draft.1`. Its
presence in a source branch does not establish publication: the exact tag and
a maintainer-published GitHub release must both exist. Core `specVersion`
remains unchanged.
The historical [prototype 0.0.2](../rfcs/policy-companion-prototype/README.md) and
[proposed 1.0.0 candidate](../rfcs/policy-companion-contract/README.md) remain
byte-for-byte unchanged. Their pins, the [promotion map](../conformance/policy/1.0.0/PROMOTION.md),
and the [migration guide](../conformance/policy/1.0.0/MIGRATION.md) preserve their
meaning and distinguish schema/result identity changes from artifact bytes.

## 1. Exact selectors and immutable artifact identity

A document has exactly one `formatVersion`, the **string** `"1.0.0"`, and `kind`
`"policy"` or `"governing-adoption"`. No prototype wrapper, `specVersion`, integer
selector, alias, suffix, coercion, or extension member is permitted. The schemas' format-versioned
URLs identify exact draft schema resources, not a release tag or proof of publication.
Readers must dispatch on the whole selector before interpreting this grammar.

The independent `version` names a revision of the immutable artifact, alongside
its scheme-bearing URI `id`. It is exactly three unsigned ASCII decimal components
separated by dots: `0` or a nonzero digit followed by digits, with no leading zeros,
suffix, spaces or final newline, at most 256 characters. `0.0.0` and a 256-character
version are valid. No component arithmetic, bump policy, compatibility, reservation
or historical uniqueness is inferred. In particular, artifact `7.3.42` still uses
format `1.0.0`. Pack artifact references follow the same bounded version grammar;
the retained Pack keeps its own Core `specVersion` unchanged.

An `id` is an opaque, scheme-bearing identifier matching the complete `URI`
production of [RFC 3986, Appendix A](https://www.rfc-editor.org/rfc/rfc3986#appendix-A),
at most 2,048 characters. Optional query and fragment are allowed; a relative
reference is refused. This means `URI`, not the narrower `absolute-URI` production
that excludes fragments. Raw Unicode, controls, whitespace (including a final LF)
and malformed percent triplets refuse. Percent-encoded Unicode and registered
names remain valid; percent decoding, trimming and identity normalization never
occur. Raw brackets belong only around an authority's IP literal, so brackets in
path, query, fragment or rootless content must be percent-encoded. IPv6 dotted
tails must satisfy the IPv4 decimal-octet grammar without leading zeros. IPvFuture
accepts both `v` and `V`, under [RFC 5234 §2.3](https://www.rfc-editor.org/rfc/rfc5234#section-2.3).
An unbracketed numeric host that fails IPv4 can still be a valid registered name.
Identity is not permission to fetch it. Local IDs match `[a-z][a-z0-9]*(?:-[a-z0-9]+)*`, at most
128 characters. Required readable text is nonempty and at most 4,096 characters.
Every defined object is closed: unknown members at any level are refused.

The unreleased candidate URI correction after commit
`30b0b30a1b0c851c41bdb271d6ef9534c91bcdec` changes three dependency-derived answers:
final-LF identifiers and IPv6 literals with leading-zero IPv4 tails now refuse;
uppercase-`V` IPvFuture identifiers now validate. The checker applies a local
reader-local URI assertion, including its consuming-Pack structural checks. Shared
Core validators elsewhere and the frozen prototype are unchanged. The companion's
2,048-character ID bound belongs to its schemas; other Core URI fields retain
their existing schema bounds.
The 20 URI vectors also distinguish generic URI grammar from URL-parser behavior.
This correction was made before promotion; it does not change shared Core or prototype behavior.

## 2. Exact retained content and optional canonical identity

A content reference is exactly `{bytesDigest, byteLength, mediaType}`. The digest
is lowercase `sha256:` plus 64 hexadecimal digits over the exact retained bytes,
including whitespace and final newlines. Length is the exact nonnegative integer
byte count, never a Boolean. It never hashes a URL or filename. Media type is a
lowercase token/token string under the shared schema, at most 128 characters,
without parameters. Artifact bytes require `application/json`; a Policy narrative
requires `text/plain` and valid UTF-8. Original bytes may be opaque, including PDF.

Media type belongs to a reference and its registration, rather than to the digest
alone. Identical bytes can be registered as both `text/plain` narrative and
`text/markdown` original. Each reference must resolve under its declared media
type, hash and length; registering one type does not register another. Conflicting
bytes for one digest refuse. Distinct retained bytes count once toward the total
budget, even with multiple types or roles; each consuming role still applies its
own byte limit. Media-type declarations do not prove the content's actual type.

An artifact reference is exactly `{kind, id, version, content}` with optional
`canonicalIdentity: {profile: "jps-canon", canonicalDigest}`. The only artifact
reference kinds in this draft are `policy` and consuming `pack`, in their
specified positions. Exact bytes are always checked, even when canonical identity
is supplied. A canonical match never substitutes for the exact-byte pin.

`jps-canon` reuses the existing [Dialect canonical form](dialect.md),
which in turn references the checkpoint-witness form. It is not JCS or preparation
canonicalization. Objects sort names by Unicode code point; arrays retain order;
strings retain Unicode without normalization, with JSON escaping for quotes,
backslashes and controls; output is UTF-8 without insignificant whitespace.
Only integer JSON number literals whose magnitude is at most `9007199254740991`
are in this domain; `-0` canonically becomes `0`. Fractional or exponent literals
are outside this domain, even when mathematically integral. Companion documents
use this domain before schema checking; they retain their original bytes regardless.

Core permits other JSON numbers in optional extensions. The checker reads Pack
numbers as raw literals and validates numeric values with exact decimal/integer
values, without binary-float rounding or rewriting execution bytes. A Core-valid
Pack outside `jps-canon` remains usable with its raw content reference alone. If
its reference requests canonical identity, it refuses as
`unsupported-canonical-identity`. Canonical identity is checked only when present.
Pack and companion strict JSON reading share the existing `tools/dialect_verify.py`
reader, including number-literal and nesting bounds; no Core limit or pin changes.

## 3. Policy content, original provenance and sections

A Policy requires `formatVersion`, `kind`, `id`, `version`, `title`,
`managementMode`, `content`, `sections` and `sourceProvenance`.
`managementMode` is `workspace-managed` or `externally-managed`. It declares
publication-management intent and authenticates no publisher, approval or role.
It is retained artifact provenance/ownership intent, not current host governance;
changing host management or authority does not mutate historical content.
The old `desk-managed` spelling is refused, not aliased. Importing content as a
local draft requires explicit intent; it does not import the source's approval.

`content` identifies the exact retained narrative. Each of 1–64 sections has a
unique local `id`, readable `title`, and `anchor: {startByte, endByte, bytesDigest}`.
The anchor is a nonempty, zero-based, half-open range of UTF-8 bytes in **that
narrative**, with SHA-256 of the selected bytes. Both endpoints must be UTF-8
boundaries and `0 <= startByte < endByte <= narrative length`. Anchors may overlap
and need not partition the narrative. Their validity does not prove that all
meaningful clauses were represented, or that stable IDs preserve meaning after a
revision. These offsets are never original PDF/page/provider-document offsets.

Each of 0–16 unique original-source records requires a local `id`,
`source: {provider, accountId, resourceId}`, explicit `sourceRevision` and `content`.
The provider/account/resource values are readable opaque provenance, not
credentials or authenticated authority. `sourceRevision` is an opaque nonempty
string or explicit null when unavailable. Original bytes remain separate from
narrative/extraction bytes. The checker neither extracts nor interprets them.
Sections optionally carry 0–16 unique `sourceRefs`, each exactly
`{sourceId, location}`. `sourceId` must resolve to an original-source record;
`location` is a readable citation such as `Clause 2`, not a verified byte offset.

Newly authored content may have no sources. No executable conditions, lifecycle,
ACLs, roles, publication states, signatures, review assertions or approval Booleans
belong in these immutable documents. Optional structured `requirements` are also
unsupported; even a claimed non-executable form is refused. A later form requires
review and an explicit selector decision, without adding a second decision language.

## 4. Governing adoption and scoped total coverage

An adoption requires `formatVersion`, `kind`, `id`, `version`, `consumer` and
`governingPolicies`. The consumer is one exact retained Core `0.2.0-draft` Pack.
The checker validates its existing structural schema and resolves the elements
below. This is no evaluation or full Core semantic-conformance claim. Graph
consumers, graph composition, transitive closure, release envelopes, registration
and cycle handling remain unsupported, pending their owning contracts.

There are 1–16 governing-policy entries, each exactly `{policy, scope, coverage}`.
One stable Policy identity can occur only once; two versions of the same identity
in one adoption refuse rather than imply precedence. List order never establishes
policy priority. Each Policy reference resolves its exact bytes, ID/version,
optional canonical identity, selector, closed grammar, sources and sections.

Scope is either `{kind: "whole-policy"}` or
`{kind: "sections", sectionIds, reviewBasis}`. A section list is nonempty, unique,
at most 64 IDs and resolves only declared sections. The limited scope's retained
`reviewBasis` describes that intentional interpretation. Whole scope selects all
declared sections; it does not prove that the author declared every applicable
clause or every applicable policy.

Coverage contains **exactly one** record per selected section, at most 64 records,
with no duplicate section identities, omissions, unknown IDs or outside-scope
records. The five closed forms are:

| Status | Required members in addition to `sectionId` and `status` |
| --- | --- |
| `implemented` | Nonempty `consumerElements` (at most 64) and retained `reviewBasis` |
| `manual` | Readable `handoff` naming a responsible process |
| `awaiting-interpretation` | Readable `explanation` of unresolved meaning |
| `awaiting-implementation` | Readable `explanation` of missing implementation |
| `out-of-scope` | Readable `rationale` for this selected clause's exclusion |

A clause excluded from limited scope has no coverage record; a selected clause
marked `out-of-scope` has the explicit rationale above. Partial automation is
valid and never asserts complete automation or permission to run. Both kinds of
`reviewBasis` are retained explanatory bytes, not proof of a reviewer's identity,
whole-policy approval or authorized sign-off. Manual handoff text grants no role.

The typed `consumerElements` forms are exactly:

| Reference | Actual Core target |
| --- | --- |
| `{kind: "rule", id}` | A declared `rules[]` entry with that ID |
| `{kind: "exception", id}` | A declared `exceptions[]` entry with that ID |
| `{kind: "applicability"}` | The present `applicability` condition |
| `{kind: "fallback"}` | The present `fallbackOutcome`, resolving to a declared outcome |

Singletons have no fabricated ID. Kind/ID confusion, absent/unknown targets and
repeated references within one coverage record refuse. Rule and exception IDs
occupy separate namespaces. The checker also requires unique rule, exception and
outcome IDs, resolves fallback, and resolves each exception's optional target-rule
and outcome references. It does not implement all Core semantic checks or prove
that a condition correctly interprets a clause. Outcomes, evidence requirements,
condition subelements and escalation are unsupported coverage kinds.

Optional `informationalSources` is at most 16 unique content references. These
bytes remain citations; they never create governing dependencies, review
assertions, authority or permissions. The checker cannot upgrade one into an
adoption, infer natural-language consistency or decide applicability.

## 5. Resource limits and refusal classifications

These are Policy offline-reader bounds, not changes to Core limits.
All maxima are inclusive. Strings are counted after decoding in Unicode
characters unless the table specifies bytes. The closed schemas state all field
maxima; the capability record exposes them for discovery.

| Resource | Maximum |
| --- | --- |
| Any parsed companion/Pack/carrier JSON document | 262,144 exact bytes |
| JSON nesting, each object/array one level from zero | 32 |
| JSON number literal | 128 characters; exponent magnitude 308 |
| Narrative, interpretation/review basis, informational material | 1,048,576 bytes each |
| Original source material, one carrier registration | 4,194,304 bytes each |
| Distinct retained material across one supplied carrier | 16,777,216 bytes |
| Ordered registrations in the local fixture/vector input carrier | 16 |
| Artifact version | 256 ASCII characters |

An artifact is also subject to the parsed-document byte limit, even though its
content reference has the general material maximum. Each role is checked
independently. Unsupported original size refuses the whole supplied input;
truncating it, silently dropping it, or substituting narrative extraction is not
a complete input. Registration exceeding a bound changes no material state.

The reader returns exactly one of these bounded JSON objects (object member order
is irrelevant; no optional messages, paths, content, titles or provider identifiers):

```json
{"status":"valid","formatVersion":"1.0.0","maturity":"draft"}
{"status":"refused","code":"invalid-selector"}
```

`valid` means supplied-document and reference agreement under this draft only. A refusal reports no partial coverage or permission. CLI success
exits 0 and refusal exits 1. Environment/setup failures are not document results;
operators must not treat an inability to run as success.

| Code | Meaning |
| --- | --- |
| `input-over-bound` | Physical bytes/nesting/number limits, schema maxima, role sizes, registration count or aggregate bytes exceeded |
| `invalid-json` | Strict UTF-8 JSON failed: duplicate keys, BOM, nonfinite numbers, unpaired surrogates, multiple values, malformed syntax |
| `invalid-selector` | Root is not an object; selector missing, wrong type, not strict ASCII `x.y.z`, or over 256 characters |
| `unsupported-format` | Selector is well-formed within that bound but is not exactly `1.0.0`; no shared-major inference |
| `invalid-document` | Supported companion fails canonical numeric domain or closed schema; wrong kind, malformed artifact version or unsupported members |
| `missing-material` | A referenced digest, required fixture document or retained local file is absent/unavailable |
| `reference-mismatch` | Raw bytes/hash/length/registered media type, ID/version, or a supported requested canonical digest differs |
| `invalid-anchor` | Narrative UTF-8, section-ID uniqueness, byte range/boundary/hash or source reference fails |
| `invalid-coverage` | Semantic scope, total coverage, policy uniqueness or typed consumer reference fails |
| `invalid-consumer` | Retained Pack fails existing Core schema or the specific ID/fallback/exception checks in §4 |
| `unsupported-canonical-identity` | Requested `jps-canon` identity is outside that existing profile's domain |
| `invalid-carrier` | Synthetic fixture/vector carrier has invalid closed shape or local path usage |

Bounds on physical document bytes, nesting and number literals are checked before
JSON syntax, including on malformed bytes. Then strict JSON is parsed. Exact
format dispatch occurs before canonical-domain and schema interpretation:
`{"formatVersion":"7.0.0","n":1.5}` is `unsupported-format`. Selector lexical
failures, including the selector's own 256-character limit, are
`invalid-selector`; other schema maxima are `input-over-bound`. Unsupported kinds
under supported format are `invalid-document`. Other-field bounds or validity do
not cause reinterpretation under an unknown format.

For the portable vector input, parse, select and canonical-domain-check the root
before checking the registration count and registering material in listed order.
Local carrier sources are acquired only after root dispatch and the count check,
one source immediately before its registration. An earlier refusal prevents later
source acquisition. NUL paths and path-normalization failures are `invalid-carrier`.
Then check the root's schema and semantics in the following order:
Policy narrative, sources, sections in declaration order; adoption consumer then
Policies in declaration order, each reference before its Policy/coverage, then
informational sources. Canonical-domain conversion occurs immediately after root
selection; all schema maxima found at one schema check take priority over other
schema failures. Otherwise a closed-schema failure is `invalid-document` (or
`invalid-consumer` for Core), including structurally identical duplicates rejected
by `uniqueItems`. Semantic duplicate coverage/IDs with distinct records uses the
specific code above. On compound defects the first failing phase wins. Refusals
never render an input-derived diagnostic or exception string.

## 6. Discovery, examples and independent porting

[capabilities.json](../conformance/policy/1.0.0/capabilities.json), also returned by
`conformance/policy/1.0.0/verify.py --capabilities`, lists exact draft selectors, `draft`
maturity, kinds, supported Core release, features, bounds and explicit exclusions.
Capability discovery is an implementation statement, not adoption, trusted review
or a permission grant. Unsupported format and optional canonical identity are
separate capabilities; no parser tries an older grammar automatically.

The examples are synthetic retained-byte bundles, derived from 0.0.2 with **source,
narrative, interpretation and consumer files preserved byte-for-byte**. Policy and
adoption identities/bytes are explicitly regenerated. The original consumer URI
is opaque and intentionally retained, even where its spelling mentions prototype.

| Domain | Coverage |
| --- | --- |
| [Data access](../conformance/policy/1.0.0/examples/data-access/fixture.json) | Whole policy; rules, fallback, manual requests and pending audit implementation |
| [Procurement](../conformance/policy/1.0.0/examples/procurement/fixture.json) | Externally managed; applicability-only scope, limited sections, unresolved meaning, explicit exclusion |
| [Refunds](../conformance/policy/1.0.0/examples/refunds/fixture.json) | Whole policy; rules, exception-only routing, manual inspection, pending implementation |

[fixture.schema.json](../conformance/policy/1.0.0/fixture.schema.json) describes a local synthetic carrier,
not a portable release envelope or proof that a dependency closure is complete.
Its files must resolve in the same directory; no network acquisition occurs.
The separate [vector carrier specification](../conformance/policy/1.0.0/vectors/README.md) defines static
input bytes and expected results for reuse by Go or other implementations.
Only a two-integer byte-repeat generator compresses boundary payloads; there is
no mutation language, implicit migration or dependency on Python transformations.
The current vectors measure agreement by this author's code and reuse its existing
canonicalizer; they supply no independent authorship or cross-vendor evidence.

Using the repository's pinned `requirements-dev.txt` dependencies on Python 3.12:

```sh
python conformance/policy/1.0.0/verify.py --capabilities
python conformance/policy/1.0.0/verify.py conformance/policy/1.0.0/examples/refunds
python conformance/policy/1.0.0/check_vectors.py
python -m unittest discover -s conformance/policy/1.0.0 -p 'test_*.py' -v
```

The repository workflow runs the staged draft separately from the frozen prototype
and existing Core/Dialect checks. Passing these checks creates no released corpus or conformance claim.

## 7. Remaining decisions and host boundary

Review/publication transactions, authentication, review-assertion trust, signatures,
source observations and synchronization, current eligibility, run/action admission,
Graph closure and independent implementation evidence remain outside this
companion. Review assertions cannot be inferred from explanatory bytes or model
test output. No citation, content match, imported history or historical approval
silently becomes local authority or permission. Host publication and admission
require their own adopted contracts and current authenticated decisions.

## 8. Policy offline-reader class

A claim MUST name the exact immutable independent Policy release, document format `1.0.0`,
Policy corpus manifest and its digest, supported Core consumer release, and all
124 rows published for that class. Every row MUST pass with the complete expected
result object; a claimant cannot omit refusal/boundary rows or self-exempt a row.
Until an independent Policy release publishes this corpus, no such claim is available. Draft
acceptance alone and an experimental software release supply no claim.

The class checks supplied immutable documents and declared material only. It
MUST implement §§1–5, including the exact selector, closed schemas, required
references and refusal order, for both Policy and governing-adoption inputs.
The local fixture/vector carriers support reproducible testing; they are not
portable release envelopes or trusted registration. A larger host MAY support
other formats through separately named capabilities; it MUST NOT coerce those
inputs into format `1.0.0` or claim them as this class's accepted documents.

This class is separate from Core document/evaluator, Dialect preparation-verifier
and witness-statement reader conformance. It does not establish correct policy
interpretation, complete organizational dependency discovery, authorized sign-off,
current lifecycle/currency, source access, or permission to run/dispatch. It
provides no Graph, provider lifecycle, signature trust or team authorization
conformance. Stable maturity requires genuinely independently authored readers
and evidence under the repository's existing rules; two ports by the same author
or same-vendor model reviews do not provide it.

# NON-NORMATIVE Policy companion prototype

This directory is review material for [RFC 0023](../0023-policy-companion.md)
([Spec issue #211](https://github.com/Judgment-Pack/judgment-pack-spec/issues/211)).
It is **not adopted**, is not a JPS conformance corpus, and creates no supported
Runtime, Desk, Runner, Gateway or Exchange contract. Its schemas and checks are
deliberately outside the normative `schema/`, `spec/` and `conformance/` trees.
Every example is synthetic. No reviewer approved it and no service issued a receipt.

The first slice covers immutable Policy content and a governing adoption for an
exact Core pack. It makes the portable document part of the four-interface design
reviewable. Source observation/synchronization, authenticated review/publication
and run/action admission remain service boundaries; this directory does not model
those services with fictional permission tokens or purported authorized receipts.

## Proposed selectors and closed schemas

Both proposed documents carry this required wrapper:

```json
"prototype": {
  "profile": "jps-policy-companion-prototype",
  "proposalVersion": "0.0.1",
  "status": "non-normative"
}
```

`proposalVersion` selects this review profile, not an adopted format. The proposed
documents have no `formatVersion` or `specVersion`; unknown selectors and members
are rejected. Their independent `version` identifies immutable artifact content.
An adopted selector, migration and capability discovery need a later decision.
The existing consuming pack keeps its own Core `specVersion` unchanged.

| File | Proposed content |
| --- | --- |
| [policy.schema.json](policy.schema.json) | Stable URI identity/version/title, declared publication ownership, retained narrative, stable section IDs/anchors and original source provenance |
| [governing-adoption.schema.json](governing-adoption.schema.json) | Exact consumer pack, one or more exact Policies, explicit scope and per-section coverage |
| [common.schema.json](common.schema.json) | Closed shared references, profile wrapper, version grammar and narrative anchors |

All defined objects are closed. There is no extension escape hatch, executable
decision language, workflow language, current lifecycle, ACL, role grant,
signature, approval assertion, registration or admission permit. Schema `$id`
URNs identify local prototype schemas; the checker resolves them from disk and
never fetches an identity or source locator.

## Immutable content and source sections

Policy `content` references the exact retained UTF-8 `text/plain` narrative.
`sections[].anchor` has `startByte`, `endByte` and `bytesDigest`: a nonempty,
zero-based, half-open byte range in **that narrative**, with SHA-256 of the range.
Both endpoints must fall on UTF-8 boundaries. Changing narrative bytes invalidates
old anchors unless the new bytes and ranges actually match. These offsets are
never offsets into an original PDF, provider document or unspecified extraction.

`sourceProvenance` separately retains the original content reference,
provider/account/resource identity and an explicit string-or-null `sourceRevision`.
That provider revision is opaque; a null means unavailable. Section `sourceRefs`
name a source's local ID and a human source location, such as `Clause 2`.
The location is a provenance citation, not a verified PDF offset or executable
selector. Original bytes can be a PDF or another media type; their byte identity
is checked, but the prototype neither extracts nor interprets them.

`sourceProvenance` may be empty for newly authored content. The prototype does not
standardize extraction provenance, optional structured requirements, source
observations, lifecycle authority mappings or source synchronization. Stable
section identity across revisions and the fidelity of source-to-narrative
interpretation still require review; this checker only checks supplied material.
Anchors need not partition every narrative byte, and may overlap. Checking that
all meaningful policy clauses are represented is outside these offline checks.

`managementMode` is `desk-managed` or `externally-managed`. It declares intended
publication ownership and proves no publication, authority or external approval.
Import as draft creates new Desk-managed content with retained provenance; it is
not a third approval state or a transfer of source approval.

## Exact adoption and coverage

An artifact reference contains `kind`, `id`, `version` and `content`. The consumer
kind in this slice is only `pack`; graph composition, transitive dependencies,
release envelopes, job registration and cycle handling need separate contracts.
The checker reads the supplied consumer using the existing Core schema, verifies
its ID/version and exact retained bytes, and resolves implemented coverage to
pack rule IDs. This is neither evaluation nor full Core semantic conformance.
Core allows arbitrary JSON numbers in optional extensions (§§2.1 and 9), so pack
reading preserves number literals without imposing the Policy `canon` domain.
Schema checks use exact decimal/integer values, without binary-float rounding.
Pack bytes are never reserialized for their execution identity. A requested
`canonicalIdentity` is checked only when supplied; a Core-valid pack outside
`jps-canon` can retain its raw identity but cannot supply that canonical identity.

Every governing policy has either `whole-policy` scope or explicit `sections`
scope. A section scope also retains a `reviewBasis` content reference documenting
the intended limited interpretation. Coverage includes **exactly one** record
for every selected section, with no undeclared or out-of-scope section records:

| Coverage status | Required additional content |
| --- | --- |
| `implemented` | Nonempty pack `consumerElements` of kind `rule`, and retained `reviewBasis` |
| `manual` | Defined `handoff` to a responsible process |
| `awaiting-interpretation` | `explanation` of unresolved meaning |
| `awaiting-implementation` | `explanation` of missing implementation |
| `out-of-scope` | Explicit `rationale` |

The two uses of `reviewBasis` are retained explanatory bytes, not attestations or
proof of review. An `out-of-scope` record explains a selected clause's exclusion
from this implementation; clauses excluded from a limited adoption scope have no
coverage record. This distinction is proposed for review. Partial automation is
valid prototype input and never asserts complete automation or permission to run.

Multiple policies are supported from the start, with one entry per stable policy
identity. The first slice rejects adopting two versions of the same identity in
one adoption, rather than inventing precedence. Optional `informationalSources`
retain bytes without becoming governing policies. List order supplies no policy
precedence or executable dependency. Natural-language consistency, applicability
and interpretation are not inferred from structurally valid coverage.

## Byte identity and the existing canonical profile

`content` is `{bytesDigest, byteLength, mediaType}`. The digest is lowercase
`sha256:` plus 64 hexadecimal digits over **exact retained bytes**, including
whitespace and final newlines. It never hashes a URL or filename.

An artifact reference may additionally carry
`canonicalIdentity: {profile: "jps-canon", canonicalDigest}`. Here `jps-canon` is a
prototype selector referring directly to the existing Spec
[Dialect §1 `canon` form](../../spec/dialect.md#1-terms-and-the-canonical-forms),
defined by [checkpoint witness §1](../../spec/checkpoint-witness.md#1-terms-and-the-canonical-form).
The review baseline is Spec commit `002ab1908bce`; this selector refers to that
existing form. This proposal adopts no new canonicalization. The helper imports the repository's
existing strict reader and `canon` implementation from
[tools/dialect_verify.py](../../tools/dialect_verify.py).

Raw and canonical identities are separate fields and separate checks. The
examples retain readable JSON with final newlines, so their artifact byte
digests **differ** from their canonical digests. Equivalent canonical JSON with
different whitespace does not satisfy an exact byte reference. `jps-canon` is
neither a claim of RFC 8785/JCS equivalence nor the preparation canonical form;
unknown profiles are rejected. There is no self-digest in Policy content or
adoption, so the references introduce no self-hash cycle.

Digests identify content; they authenticate no author and grant no access.
Trust roots, signatures, authoritative adoption/publication receipts, revocation,
cross-installation import authority and live admission remain **unresolved**.
Nothing in this prototype substitutes for those decisions.

## Proposed bounds and focused checks

Artifact versions use current Spec/Runtime syntax: ASCII `x.y.z`, decimal
components with no leading zeros except `0`, no suffix/coercion/whitespace, and at
most **256 total characters**. There is no smaller component integer bound,
compatibility rule, publication rule or version bump algorithm. The parser's
integer tuple is only a parsing aid.

For bounded review fixtures, the helper permits at most 262,144 bytes per parsed
JSON document, nesting depth 32, and 1,048,576 bytes per retained material.
Schemas bound source lists to 16, sections/coverage/scope/rule references to 64,
governing policies to 16, local IDs to 128 characters, URIs to 2,048 characters
and descriptive strings to 4,096 characters. These are **proposed prototype
bounds**, not new bounds on Core or other adopted companions. Carrier bytes,
UTF-8 ranges and schema string character counts are distinct measurements.

Strict JSON is checked before schema validation: duplicate members, invalid
Unicode, a BOM, extra values and non-JSON constants are rejected. Policy/adoption
and fixture JSON additionally require the existing `canon` numeric domain;
fractions/exponents and integers outside that domain are rejected there, and `-0`
follows the profile's existing normalization to `0`. Consumer packs preserve
Core's numeric domain. Their reader reuses the existing strict reader's limits:
128 characters per number literal and exponent magnitude at most 308. Exceeding
those limits reports an unsupported prototype input bound, not invalid Core.
JSON Schema Draft 2020-12 plus URI format assertion handles
shape; the helper separately checks exact references, IDs, source/section
uniqueness, ranges/UTF-8 boundaries, rule references and exact scope coverage.
Schema acceptance alone does not establish those reference checks.
The checker does not reserve an artifact version or detect historical reuse of
the same ID/version with different content; immutable publication storage is a
separate contract.

| Synthetic example | Coverage exercised |
| --- | --- |
| [Data access](examples/data-access/fixture.json) | Whole policy; eligibility rules, manual restricted requests, pending audit implementation |
| [Procurement](examples/procurement/fixture.json) | Declared external ownership; limited section scope, unresolved conflict meaning, payment exclusion, public notice outside the selected scope |
| [Refunds](examples/refunds/fixture.json) | Whole policy; eligibility rules, manual damaged-goods review, pending abuse review implementation |

Each directory contains readable proposed Policy/adoption/pack documents,
separate narrative/original/review-basis bytes and a `fixture.json` containing
their reproducible byte identities. That manifest is local test scaffolding,
**not** a portable release envelope. No domain service transcript is copied here.

From the Spec repository root, use its already pinned dependencies:

```sh
python3 -m pip install -r requirements-dev.txt
python3 rfcs/policy-companion-prototype/verify.py
python3 -m unittest discover -s rfcs/policy-companion-prototype -p 'test_*.py' -v
```

The [repository workflow](../../.github/workflows/conformance.yml) explicitly runs
these tests after the full repository check in an exploratory, non-normative step
on Python 3.12. The existing `discover -s tests` command does not automatically
discover this RFC directory, so the workflow uses the separate invocation above.
Passing that step creates no normative corpus or conformance claim. The focused
tests exercise all three domains,
multiple policies, exact byte versus canonical identities, unsupported profiles,
malformed/oversized JSON and versions, unknown/live-authority fields, altered or
missing material, invalid anchors, source/rule references and incomplete/conflicting
coverage, plus Core-valid numeric extensions outside the Policy canonical domain.
They do not establish independent implementation agreement, actual
approvals, withdrawal ordering, recovery safety or production fitness. Required
full-repository checks remain the repository CI's responsibility.

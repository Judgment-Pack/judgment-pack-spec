# Dialect format 4.1.0 vectors (staged, proposed)

Hand-written vectors for the proposed dialect format `4.1.0`, a paged `operation` source
([RFC 0033](../../../rfcs/0033-paged-operation-source.md), in Review). The companion,
[`spec/dialect.md`](../../../spec/dialect.md), is unchanged: the format is the RFC's Specification
until it is accepted. These vectors are not a conformance corpus and not recordings: no preparer
writes the format, and no claim may cite them. The vectors of format `4.0.0`
([`format-4/`](../format-4/README.md)), the forty-seven staged Runner vectors and the format `2.0.0`
and `3.0.0` identity examples are unchanged.

## The vectors

There is one directory for each row of the RFC's Conformance table, in its order, named by the row
with the prefix `paged-`. Each holds the files a verifier is given, as the end-to-end vectors of
format `4.0.0` do: `dialect.json`, `case.json`, `sources.json` (the acquisitions), `profiles.json`
and `preparation.json`, and, for `paged-unbound-paged`, its binding document `binding.json` (§4.4).
A reading's `preparation.json` is the preparation the verifier recomputes; every other vector's is a
preparation of `verifiedAt` alone, so its expected refusal or finding comes first, and the three
vectors whose answer is `preparation-differs` hold a reading's preparation rewritten.

Every receipt is signed under RFC 8032 section 7.1 TEST 1's published seed, whose public key each
profile holds. The profiles are three: `feed`, of shape `mcp`; `web`, of shape `http` under
`adapter-http`; and `connection`, of shape `http` under another adapter, which admits no paging.
`paged-research-in-paged-session` alone is given a fourth, `assistant`, the research profile of its
`research` source. Every value is synthetic.

[`manifest.json`](manifest.json) pins each file by its SHA-256 and gives each vector:

- `row`, the Conformance table's case name, and `kind`, its kind there;
- `expected`: `{"result": "refusal", "refusal": R}`, `{"result": "finding", "finding": F}`, or a
  reading, with its `facts`, each named source's outcome `status`, `reason` and `paging` (absent for
  an outcome that has none), `cites` as `[sessionId, callIndex]` pairs in their order, and, where
  given, `unsignedParameters`; and of a reading also `preparationDigest`;
- `expectedReportOfAReaderThatDoesNotReadTheFormat`: the report of a reader written to the RFC's
  text that reads format `4.0.0` and not `4.1.0`, such as the first reader with `4.1.0` taken out of
  the formats it reads, as its test runs it: `version-unread` for a document of format `4.1.0` (RFC
  0033 section 11), and `input-malformed` for the two vectors of format `4.0.0`, as a reader of
  either format answers them. It does not describe the second reader, which reads neither format
  and refuses every vector `version-unread`; its test does not read this member.

A reader written to the text before the amendment, such as the preserved `v0.3.0` reader, refuses
every vector `input-malformed` (section 11). The repository's first reader,
[`tools/dialect_verify.py`](../../../tools/dialect_verify.py), reads the format; the second,
[`tools/dialect-verify-ts`](../../../tools/dialect-verify-ts/README.md), defines the selector and
refuses every vector `version-unread`. [`tests/test_dialect_format_4_1.py`](../../../tests/test_dialect_format_4_1.py)
and `tests/test_dialect_ts.py` hold them to the manifest, and check that the manifest has one vector
for each row of the RFC's table.

## How they are written

[`tools/paged_source_vectors.py`](../../../tools/paged_source_vectors.py) writes the directories and
the manifest. Every expected answer is a literal in it, written from the RFC's Specification before
the reader runs: the refusals and findings, and each reading's facts, `paging`, `cites` order and
statuses. It forms each page's request by its own code (section 3), signs each receipt, and asks the
reader only for the canonical forms, the Ed25519 arithmetic and each reading's recomputed
preparation, which it then holds to the hand-written answer; it stops at the first disagreement.
`python3 tools/paged_source_vectors.py --check` writes nothing and exits 1 when a file differs.

## Rows answered by a rule outside `paging`'s own members

- `paged-max-pages-exponent-not-measured`: `1e3` lies outside the `canon` domain, so the dialect is
  `input-malformed` by §1 before `paging`'s form is read, and phase 3, which measures `maxPages`
  only when it is an integer, does not refuse it `input-over-bound`. `paged-max-pages-not-integer`
  (`"2"`) and `paged-max-pages-zero` reach the paging rule.
- `paged-fills-query-three-tokens`: §4.1 holds `adapter-http`'s `query` to an object of string
  templates, so the parent of a `fills` of three tokens under `query` is a string or a template
  form, never an object: `input-malformed` by section 2's parent rule, before any profile is read.

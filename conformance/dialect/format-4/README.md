# Dialect format 4.0.0 vectors (staged, proposed)

Hand-written vectors for the proposed dialect format `4.0.0` ([`spec/dialect.md`](../../../spec/dialect.md)
§2.2, RFC 0018's amendment of 2026-11-12). They are not a conformance corpus, and they are not
recordings: no preparer writes format `4.0.0`, and every expected answer here was written by hand,
the distances computed by [`tools/dialect_builtins_reference.py`](../../../tools/dialect_builtins_reference.py),
which takes another method on the same sphere, and not by the reader under test. One of the
repository's two readers reads the format; the other refuses it `version-unread`. No claim may cite
them. The forty-seven staged Runner vectors and the format `2.0.0` and `3.0.0` identity examples are
unchanged.

## The end-to-end vector

[`case-rule-no-sources/`](case-rule-no-sources/) is one dialect with no source, whose case has a
copy and a rule: the rule tests an address against a list of address ranges and a speed derived from
two timestamped positions against a limit, and writes a literal and two derived values. The
directory holds the files a verifier is given (`dialect.json`, `case.json`, `sources.json`,
`profiles.json`, `preparation.json`) and two more, `dialect.canonical.json` and
`case-read.canonical.json`, the dialect's `canon` bytes and the case's read's, whose digests the
preparation names. [`manifest.json`](manifest.json) pins every file by its SHA-256, the three
digests, the report a reader of the format gives, and the report of a reader that does not read it.

## The rows

[`vectors.json`](vectors.json) holds one row for each form and refusal, each a case document and a
case rule over it, at the instant `verifiedAt`. A row is a frame, not a whole dialect: the test
builds the dialect `{"formatVersion": "4.0.0", "id": "urn:judgmentpack:dialect:format-4-vectors",
"version": "0.1.0", "case": {"parameters": P, "facts": [], "evidence": [], "rule": R}}`, `P` the row's
`parameters` (left out when the row has none), and gives it no source, no acquisition and no profile.
`R` is:

- the row's `rule`, when it has one;
- for a row with `when`, a rule declaring every case parameter and `runAt`, with the row's `derived`
  when it has them, whose first clause has the row's `when` and writes `/matched` the literal
  `true`, reason `true`, and whose last clause writes `/matched` the literal `false`, reason `false`.
  `expected` is the literal written; `expectedBasis`, when given, is the claim's `basis`;
- for a row with `expectedDerived`, one rule for each derived value it names, declared as for
  `when`, whose first clause is `{"op": "exists", "derived": D}` and writes `/value` from `D`, reason
  `some`, and whose last writes nothing, reason `none`. A number is the value `D` has; `null` says
  it has none.

A row with `dialect` gives the whole dialect instead. `expectedClaim` gives members of the case
rule's claim; `expectedRefusal` and `expectedFinding` the report's code. A reading is read from the
case outcome's `rule` (§2.2.6) of the preparation the verifier recomputes, given a preparation of
`verifiedAt` alone, which therefore differs. The bounds one over each maximum are reader tests in
`tests/test_dialect_format_4.py`, not rows.

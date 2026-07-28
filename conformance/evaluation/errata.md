# Evaluation corpus errata

This file is the project's record of defective rows in a **released** evaluation corpus, and it is the
only thing that can excuse a failing row from an evaluator-conformance claim (Core §3.4).

A released corpus is frozen: its rows are never edited inside the `suiteVersion` that published them
(Core §3.4.1). An erratum changes no row. It records that the project — not a claimant — has found a
row defective, so that a claim against that `suiteVersion` may exclude the row, provided the claim
names the row and cites the erratum here. Until an erratum exists for a row, a failing row is a
blocked claim and a specification-defect report, in that order.

Every entry states:

| Field          | Meaning                                                                     |
| -------------- | --------------------------------------------------------------------------- |
| `suiteVersion` | The exact released corpus version the erratum applies to.                    |
| Case id        | The `id` of the one row the erratum marks defective.                         |
| Issued         | The date the project issued the erratum, as an RFC 3339 full-date.           |
| Defect         | What is wrong with the row, and which section of Core decides that it is.    |

An erratum is issued by the maintainers through the ordinary change process; a corrected row lands in
the next `suiteVersion` rather than in the released one.

## `0.2.0-draft`

No errata. Every row of `suiteVersion` `0.2.0-draft` stands as published, and a claim against it must
state that every row passed.

# Example packs

Five synthetic Judgment Packs, checked in so a reader can see the format working before
writing one. Each is a complete document that validates against
[`schema/judgment-pack-core.schema.json`](../schema/judgment-pack-core.schema.json).

| Example | Synthetic domain | Worth inspecting |
| --- | --- | --- |
| [`data-request-intake-triage.json`](data-request-intake-triage.json) | triaging an incoming request for data | the only pack with an **optional** evidence requirement (`required: false` on `sensitive-data-approvals`) and the only one using `attestation` evidence — a good place to see how an absent-but-optional requirement differs from a missing one |
| [`minimal-expense-approval.json`](minimal-expense-approval.json) | approving an expense claim | the smallest complete pack here, and the clearest look at ordered comparison: `in`, `greater-than` and `less-than-or-equal` on one decision, with a `not` wrapping a nested condition |
| [`records-disposition-review.json`](records-disposition-review.json) | deciding whether records may be disposed of | evidence-light by design — one requirement, no exceptions — so the rule structure is what carries the decision |
| [`software-change-review.json`](software-change-review.json) | reviewing a proposed software change | two independent `evidence-present` conditions inside one `all`, which is the shape most real packs reach for first |
| [`supplier-invoice-approval.json`](supplier-invoice-approval.json) | approving a supplier invoice | an `exception` alongside a `not` condition — the pair worth reading together, because an exception is not the same thing as a negated rule |

## What these are, and are not

They are **synthetic and non-operational**. Every organisation, threshold, role and source in
them is invented for illustration. None of them is authorization, production policy, an
industry standard, or evidence that any decision is safe or correct. A pack states what a
decision was meant to consider; it does not make the decision right.

Two things not to do with them:

- **Do not add real or sensitive data.** These files are public, and a worked example is a
  bad place for a real threshold, a real supplier, or anything about a real person.
- **Do not fetch the source locators.** The `sources` entries carry example URIs and paths.
  Ordinary validation reads the document and nothing else — no locator is dereferenced, and
  a tool that fetched them would be doing something the specification does not ask for.

## Where to go next

- [`TESTING.md`](../TESTING.md) — how to validate a pack against the schema and the
  conformance corpus.
- [`docs/field-guide.md`](../docs/field-guide.md) — what each field means, in prose.
- [`schema/judgment-pack-core.schema.json`](../schema/judgment-pack-core.schema.json) — the
  normative shape these examples conform to.

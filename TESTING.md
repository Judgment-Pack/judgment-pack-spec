# Test the research preview

This exercise takes about 10–15 minutes. It tests whether the current JSON shape is understandable
and whether a Draft 2020-12 validator reports the expected structural results. It also invites
feedback about authoring and local references.

It does **not** test evaluator conformance. Core `0.1.0-draft` does not define an evaluator
conformance class, and schema acceptance does not show that a pack is correct, authorized, safe,
or operationally fit.

## Before you start

Use:

- a JSON Schema implementation that supports Draft 2020-12;
- format assertion for `uri`, `date`, and `date-time`, if your implementation makes format checks
  optional; and
- a text editor or scratch copy outside the checked-in examples.

Use only the supplied examples or invented, low-risk data. Do not put customer, employee, personal,
confidential, regulated, credential, or production data into a pack or issue report. Prefer a local
validator. If you use a hosted validator, submit only content you are comfortable publishing.
Validation should not fetch any URI in a source locator.

Record the validator name and version, its selected schema dialect, and whether format assertion is
enabled. Different implementations can otherwise appear to disagree.

## 1. Establish a structural baseline (minutes 0–4)

Configure the external validator with:

- schema: [`schema/judgment-pack-core.schema.json`](schema/judgment-pack-core.schema.json)
- instance: one of the files in [`examples/`](examples/)
- dialect: JSON Schema Draft 2020-12

Validate each example. The expected result is structurally valid. In particular, try the two
deliberately non-operational examples:

- [`examples/software-change-review.json`](examples/software-change-review.json)
- [`examples/records-disposition-review.json`](examples/records-disposition-review.json)

If an example is rejected, capture the diagnostic, instance location, schema location, validator
version, and format setting. A schema result covers only constraints represented in the schema.
Duplicate object member names, input-size limits, and some other carrier requirements also depend
on the JSON parser or host application.

## 2. Check a structural failure (minutes 4–7)

Work on a scratch copy of `software-change-review.json`; do not modify the checked-in example.

Add this member at the root, taking care to keep the JSON syntax valid:

```json
"unexpectedRootMember": true
```

Validation should fail because the root schema does not allow unrecognized members. Restore the
scratch copy before continuing. If it remains valid, confirm that the instance and schema were not
reversed and that Draft 2020-12 was selected.

## 3. Observe the schema/semantics boundary (minutes 7–10)

In the scratch copy, change a rule outcome reference from `"ready-for-demo"` to
`"missing-outcome"` and validate again.

The document can still pass the JSON Schema: `missing-outcome` has the right local-ID shape. It is
not semantically conforming, however, because that reference does not name an outcome declared in
the same pack. Manually inspect the pack for:

- duplicate outcome, rule, evidence-requirement, source, or exception IDs;
- rule and fallback references to undeclared outcomes;
- evidence and source references to undeclared objects; and
- exception targets, outcomes, and source references that do not name the required kind of object;
- `evidence-present` references anywhere in applicability, rules, or exceptions; and
- required-extension declarations without a corresponding namespaced extension value.

This is an authoring and reference-model test, not a portable execution test. Do not use the rules
to make or automate a real decision, and do not report an inferred outcome as proof that two
runtimes agree.

## 4. Try a small authoring change (minutes 10–13)

Using either synthetic example as a scratch template, change its title, descriptions, and labels to
another fictional, low-risk scenario. Keep the declared IDs and their references aligned, then run
schema validation again and repeat the manual reference review above.

While editing, note anything that is hard to express, easy to misunderstand, or accepted by the
schema despite looking contradictory. Avoid adding ordered comparisons of decimal strings: their
executable comparison semantics are reserved for a later evaluator draft.

## 5. Report what you learned (minutes 13–15)

When opening a repository issue, use the
[testing feedback template](.github/ISSUE_TEMPLATE/testing-feedback.md) and include a minimal
synthetic reproduction. Useful reports cover:

- confusing field names or object boundaries;
- unexpected schema acceptance or rejection;
- ambiguous local-reference requirements;
- missing concepts encountered during synthetic authoring; or
- documentation that could be more precise about what conformance does and does not establish.

Remove sensitive details, access tokens, internal URLs, organization names, and real policy text
before submitting. A passing example is useful feedback too—especially when accompanied by the
validator and settings used.

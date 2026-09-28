# Can the branch stand behind this contractor order?

Is this contractor order ready for a branch owner to review? This worked example follows **Westbrook Landscape Supply · Greenline contractor (fictional)** through missing records,
mismatched approvals, explicit refusals and a policy boundary.

**Synthetic demonstration · Pack v0.1.0 · 4 source artifacts · 18 project test cases**

[Download the one-page brief (PDF)](../../web/demos/contractor-order-readiness/v0.1.0/ONE-PAGE.pdf)
or [get the complete example (ZIP)](https://judgmentpack.org/artifacts/demos/contractor-order-readiness/v0.1.0/contractor-order-readiness-v0.1.0.zip).

## Pain points to validate

- A seller can promise a job-site delivery before stock, credit and dispatch agree.
- An approval for an earlier quote or a different branch does not support the current order.
- Branch teams repeatedly chase the same checks while contractors need a dependable answer.

These are discovery hypotheses. The example shows repeatable checks; it does not establish
how frequent or expensive the problem is in a real organization.

## The decision and its owner

The accountable reviewer is **Branch operations owner**. A possible sponsor is **Regional sales / branch operations director**.
Every artifact must match the same **order identifier, quote revision, fulfillment scope** before its facts can support the gate.

| Required artifact | Source owner |
| --- | --- |
| Contractor quote and pricing record | Branch sales representative |
| Stock allocation check | Inventory owner |
| Credit authorization record | Credit controller |
| Delivery slot and site check | Dispatch coordinator |

## Follow the evidence

The quote is accepted and stock allocated, but credit approval is missing. Add it to make the order reviewable, then show why an approval for another order or quote revision cannot be reused.

| What changes | Result | Next step |
| --- | --- | --- |
| A required review is missing | Unresolved: missing required evidence and unknown | Obtain the review; its exception flag is unknown too. |
| A review covers another case, revision or scope | Unresolved: unknown | Retrieve the matching record. |
| A source is unavailable | Unresolved: unknown | Restore acquisition; failure does not prove absence. |
| A prerequisite is explicitly false | Hold the order commitment | Resolve the negative prerequisite with its owner. |
| An explicit exception is raised | Unresolved: exception escalation | Ask the accountable owner to review it. |
| Quote discount (%) is 10.01 with all other prerequisites met | Discount exception review | Review the policy boundary. |
| Matching records meet the standard gate | Ready for branch review | The accountable person reviews the evidence package. |

This fictional gate does not reserve stock, grant credit, dispatch a vehicle or promise a delivery. The 10% discount limit is invented and does not represent Ewing policy. No notification or external action is sent. The role named in a handoff is a declared
target, not a delivered assignment.

## From artifacts to facts

The Runner mapping reads four separate local records. It checks their case parameters, then
projects fields into facts and evidence availability. A matching file can contain a refusal:
**presence is not approval**. Missing, mismatched and unavailable sources have distinct diagnoses.

All fixtures are asserted inputs. Matching identifiers does not authenticate their origin,
approver authority or freshness by age. The example uses neither a live vendor account nor an
LLM call. Candidate production integrations are documented in the integration plan and need
their own configuration.

## Inspect and reproduce

| Artifact | Purpose |
| --- | --- |
| [One-page PDF](../../web/demos/contractor-order-readiness/v0.1.0/ONE-PAGE.pdf) | Discuss the problem with a business owner. |
| [Pack](../../web/demos/contractor-order-readiness/v0.1.0/packs/contractor-order.pack.json) | Read the explicit decision policy. |
| [18 test cases](../../web/demos/contractor-order-readiness/v0.1.0/packs/contractor-order.matrix.json) | Inspect expected outcomes, unknowns, exceptions and boundaries. |
| [Source mapping](../../web/demos/contractor-order-readiness/v0.1.0/mapping/mapping.json) | Read the source binding and derivation rules. |
| [Walkthrough and setup](../../web/demos/contractor-order-readiness/v0.1.0/README.md) | Run the example and configure a separate job. |
| [Integration plan](../../web/demos/contractor-order-readiness/v0.1.0/INTEGRATION-PLAN.md) | Review source ownership and real connector requirements. |
| [Pilot plan](../../web/demos/contractor-order-readiness/v0.1.0/PILOT-PLAN.md) and [worksheet](../../web/demos/contractor-order-readiness/v0.1.0/PILOT-WORKSHEET.csv) | Measure whether the workflow is worth adopting. |
| [Coverage review](../../web/demos/contractor-order-readiness/v0.1.0/COVERAGE-REVIEW.md) | Understand the remaining advisory conflict probe. |

With [Runtime v0.23.1](https://github.com/Judgment-Pack/judgment-pack-runtime/releases/tag/v0.23.1)
installed and its published checksum verified, extract the ZIP, open its directory, then run:

```sh
jpack packs validate --config jpack.json
jpack packs test --config jpack.json
```

Expected: **18 passed, 0 mismatched**. The matrix evaluates captured projected inputs;
it does not re-acquire records or re-run the mapping. The pack declares JPS Core 0.2.0-draft;
the project matrix and Runner mapping are companion-tool conventions. These cases are not
the normative JPS conformance corpus.

## Repeat the check as evidence changes

A configured Desk/Runner can freeze this policy and mapping in a job release, retain each run,
save a shared brief on demand, and repeat from new local files on an event or a schedule.
The website provides static files; the ZIP does not install a job, trigger, account or connector.
Follow the setup guide to preview a complete source batch before enabling repeated execution.

## Test the business value

ERP and distributor commerce systems already provide order checks. Test whether unresolved handoffs across sales, inventory, credit and dispatch are frequent enough to justify an additional gate.

Start with one owner and roughly ten historical or shadow-mode cases. Compare evidence-assembly
time, missing-record resolution, rework and disagreements against the existing process. Include
integration and maintenance costs; do not assume the business value of an order, campaign or asset
is value created by the tool.

[Explore the other worked business examples](../../examples/#worked-business-examples).

# Turn a maintenance recommendation into a reviewable case

Is this maintenance recommendation ready for a planner to review? This worked example follows **Harbor Transit · vehicle BUS-042 (fictional)** through missing records,
mismatched approvals, explicit refusals and a policy boundary.

**Synthetic demonstration · Pack v0.1.0 · 4 source artifacts · 18 project test cases**

[Download the one-page brief (PDF)](../../web/demos/fleet-maintenance-review/v0.1.0/ONE-PAGE.pdf)
or [get the complete example (ZIP)](https://judgmentpack.org/artifacts/demos/fleet-maintenance-review/v0.1.0/fleet-maintenance-review-v0.1.0.zip).

## Pain points to validate

- A predictive alert still leaves someone to reconcile the vehicle, inspection and existing work orders.
- An inspection of another vehicle or component can create false confidence.
- Unclear ownership and duplicate work orders can turn an AI recommendation into more work.

These are discovery hypotheses. The example shows repeatable checks; it does not establish
how frequent or expensive the problem is in a real organization.

## The decision and its owner

The accountable reviewer is **Fleet maintenance planner**. A possible sponsor is **Fleet maintenance director / transit operations lead**.
Every artifact must match the same **vehicle identifier, observation batch, component identifier** before its facts can support the gate.

| Required artifact | Source owner |
| --- | --- |
| Asset and component record | Fleet records owner |
| Diagnostic observation report | Diagnostics analyst |
| Technician inspection record | Qualified technician |
| Work-order coordination check | Maintenance planner |

## Follow the evidence

An apparently useful recommendation has no inspection for this vehicle. Add it to make the evidence reviewable, then show that an inspection for another vehicle cannot clear the gate.

| What changes | Result | Next step |
| --- | --- | --- |
| A required review is missing | Unresolved: missing required evidence and unknown | Obtain the review; its exception flag is unknown too. |
| A review covers another case, revision or scope | Unresolved: unknown | Retrieve the matching record. |
| A source is unavailable | Unresolved: unknown | Restore acquisition; failure does not prove absence. |
| A prerequisite is explicitly false | Hold for investigation | Resolve the negative prerequisite with its owner. |
| An explicit exception is raised | Unresolved: exception escalation | Ask the accountable owner to review it. |
| Declared priority score (0–10) is 5.01 with all other prerequisites met | Priority planner review | Review the policy boundary. |
| Matching records meet the standard gate | Ready for planner review | The accountable person reviews the evidence package. |

This is a planning evidence gate, never a roadworthiness, dispatch or repair authorization. No model is called, safety is not certified, and a safety concern always requests a qualified human review. No notification or external action is sent. The role named in a handoff is a declared
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
| [One-page PDF](../../web/demos/fleet-maintenance-review/v0.1.0/ONE-PAGE.pdf) | Discuss the problem with a business owner. |
| [Pack](../../web/demos/fleet-maintenance-review/v0.1.0/packs/maintenance-review.pack.json) | Read the explicit decision policy. |
| [18 test cases](../../web/demos/fleet-maintenance-review/v0.1.0/packs/maintenance-review.matrix.json) | Inspect expected outcomes, unknowns, exceptions and boundaries. |
| [Source mapping](../../web/demos/fleet-maintenance-review/v0.1.0/mapping/mapping.json) | Read the source binding and derivation rules. |
| [Walkthrough and setup](../../web/demos/fleet-maintenance-review/v0.1.0/README.md) | Run the example and configure a separate job. |
| [Integration plan](../../web/demos/fleet-maintenance-review/v0.1.0/INTEGRATION-PLAN.md) | Review source ownership and real connector requirements. |
| [Pilot plan](../../web/demos/fleet-maintenance-review/v0.1.0/PILOT-PLAN.md) and [worksheet](../../web/demos/fleet-maintenance-review/v0.1.0/PILOT-WORKSHEET.csv) | Measure whether the workflow is worth adopting. |
| [Coverage review](../../web/demos/fleet-maintenance-review/v0.1.0/COVERAGE-REVIEW.md) | Understand the remaining advisory conflict probe. |

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

Compare with the diagnostics provider and existing maintenance-management system. Test the handoff to planners and technicians before adding another alert or dashboard.

Start with one owner and roughly ten historical or shadow-mode cases. Compare evidence-assembly
time, missing-record resolution, rework and disagreements against the existing process. Include
integration and maintenance costs; do not assume the business value of an order, campaign or asset
is value created by the tool.

[Explore the other worked business examples](../../examples/#worked-business-examples).

# Before promising a remedy, check the evidence

Is this proposed customer remedy ready for accountable owner review? This worked example follows **Alder Business Services · account ACCT-042 (fictional)** through missing records,
mismatched approvals, explicit refusals and a policy boundary.

**Synthetic demonstration · Pack v0.1.0 · 4 source artifacts · 18 project test cases**

[Download the one-page brief (PDF)](../../web/demos/customer-recovery-readiness/v0.1.0/ONE-PAGE.pdf)
or [get the complete example (ZIP)](https://judgmentpack.org/artifacts/demos/customer-recovery-readiness/v0.1.0/customer-recovery-readiness-v0.1.0.zip).

## Pain points to validate

- A feedback alert starts a follow-up, but the owner still chases the service investigation, remedy approval and account checks.
- An approval for an old remedy or another account can appear complete while failing to support this proposal.
- Customer-facing teams need one reviewable explanation of what is missing and who owns the next step.

These are discovery hypotheses. The example shows repeatable checks; it does not establish
how frequent or expensive the problem is in a real organization.

## The decision and its owner

The accountable reviewer is **Customer recovery owner**. A possible sponsor is **Head of Customer Experience / Customer Success operations**.
Every artifact must match the same **case identifier, remedy revision, account scope** before its facts can support the gate.

| Required artifact | Source owner |
| --- | --- |
| Customer feedback and case record | Customer experience lead |
| Service investigation and proposed remedy | Service operations lead |
| Remedy approval record | Commercial approval owner |
| Account owner and contact permission check | Account owner |

## Follow the evidence

A dissatisfied customer has an open follow-up and a proposed remedy, but the approval has not arrived. Supply a matching approval to make it reviewable, then replace it with one covering the old remedy revision. Finally cross the fictional CAD 500 boundary.

| What changes | Result | Next step |
| --- | --- | --- |
| A required review is missing | Unresolved: missing required evidence and unknown | Obtain the review; its exception flag is unknown too. |
| A review covers another case, revision or scope | Unresolved: unknown | Retrieve the matching record. |
| A source is unavailable | Unresolved: unknown | Restore acquisition; failure does not prove absence. |
| A prerequisite is explicitly false | Hold the proposed remedy | Resolve the negative prerequisite with its owner. |
| An explicit exception is raised | Unresolved: exception escalation | Ask the accountable owner to review it. |
| Proposed remedy amount (CAD) is 500.01 with all other prerequisites met | Additional commercial review | Review the policy boundary. |
| Matching records meet the standard gate | Ready for recovery owner review | The accountable person reviews the evidence package. |

This gate does not issue credits, contact customers or close tickets. All records and the CAD 500 review threshold are fictional; no Qualtrics connection, employer policy or endorsement is represented. No notification or external action is sent. The role named in a handoff is a declared
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
| [One-page PDF](../../web/demos/customer-recovery-readiness/v0.1.0/ONE-PAGE.pdf) | Discuss the problem with a business owner. |
| [Pack](../../web/demos/customer-recovery-readiness/v0.1.0/packs/customer-recovery.pack.json) | Read the explicit decision policy. |
| [18 test cases](../../web/demos/customer-recovery-readiness/v0.1.0/packs/customer-recovery.matrix.json) | Inspect expected outcomes, unknowns, exceptions and boundaries. |
| [Source mapping](../../web/demos/customer-recovery-readiness/v0.1.0/mapping/mapping.json) | Read the source binding and derivation rules. |
| [Walkthrough and setup](../../web/demos/customer-recovery-readiness/v0.1.0/README.md) | Run the example and configure a separate job. |
| [Integration plan](../../web/demos/customer-recovery-readiness/v0.1.0/INTEGRATION-PLAN.md) | Review source ownership and real connector requirements. |
| [Pilot plan](../../web/demos/customer-recovery-readiness/v0.1.0/PILOT-PLAN.md) and [worksheet](../../web/demos/customer-recovery-readiness/v0.1.0/PILOT-WORKSHEET.csv) | Measure whether the workflow is worth adopting. |
| [Coverage review](../../web/demos/customer-recovery-readiness/v0.1.0/COVERAGE-REVIEW.md) | Understand the remaining advisory conflict probe. |

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

Experience-management platforms already support follow-up workflows and tickets. CRM and service desks also provide approvals. Test whether reconciling records across these systems causes recurring work that existing configuration cannot solve economically.

Start with one owner and roughly ten historical or shadow-mode cases. Compare evidence-assembly
time, missing-record resolution, rework and disagreements against the existing process. Include
integration and maintenance costs; do not assume the business value of an order, campaign or asset
is value created by the tool.

[Explore the other worked business examples](../../examples/#worked-business-examples).

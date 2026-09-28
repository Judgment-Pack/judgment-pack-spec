# Data batch evidence readiness — fictional policy v0.1.0

## Purpose
Is this data batch ready for an accountable release review?

This gate does not publish a dataset or replace a quality engine. The 1% threshold is fictional; it is not a recommended production standard.

## Decision gate
Each record must match the submitted case, revision and scope. Missing or mismatched evidence cannot establish readiness. Positive results require accountable human review.

- Identity fields: datasetId, batchId, contractRevision.
- Required artifacts: Orchestrator completion record, Data quality report, Schema and contract check, Data owner review.
- Positive prerequisites: /pipeline/completed, /quality/criticalChecksPassed, /contract/compatible, /owner/approved must all be true.
- Exception: /contract/overrideRequested = true requests the Data product owner before ordinary outcomes.
- Valid metric range: 0 through 100 inclusive.
- Invalid rows (%) less-than-or-equal 1 yields Ready for release review when all other conditions hold. The other valid side yields Data quality review required.
- A false prerequisite or out-of-range metric yields Hold; unknown rule inputs remain unresolved.
- Numeric comparisons use decimal strings; JSON numeric values do not satisfy that contract.
- A successful scoped lookup with no record means absent. Failed acquisition, wrong case/revision/scope and invalid boolean data mean unknown. Missing required evidence prevents ordinary refusal resolution. If the absent record also carries the exception flag, the exception cannot be ruled out; the result records both missing-required-evidence and unknown.

## Evidence and facts
Artifacts are retained source snapshots. Facts are explicit projections of their typed fields. Presence means a matching record was supplied, not that its decision was positive. All local inputs are asserted, not independently authenticated records or live model output. Matching fields do not prove truth, authority or wall-clock freshness. No date-based expiry is implemented.

## Ownership
- Orchestrator completion record: Data engineer
- Data quality report: Data quality owner
- Schema and contract check: Schema owner
- Data owner review: Data product owner

One escalation target: Data product owner. These responsibilities do not create tasks or send notifications. No employer policy is copied.

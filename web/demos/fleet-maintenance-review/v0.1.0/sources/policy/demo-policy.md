# Maintenance recommendation evidence review — fictional policy v0.1.0

## Purpose
Is this maintenance recommendation ready for a planner to review?

This is a planning evidence gate, never a roadworthiness, dispatch or repair authorization. No model is called, safety is not certified, and a safety concern always requests a qualified human review.

## Decision gate
Each record must match the submitted case, revision and scope. Missing or mismatched evidence cannot establish readiness. Positive results require accountable human review.

- Identity fields: vehicleId, observationBatch, componentId.
- Required artifacts: Asset and component record, Diagnostic observation report, Technician inspection record, Work-order coordination check.
- Positive prerequisites: /asset/inScope, /diagnostic/signalSupported, /inspection/faultConfirmed, /workorder/noDuplicateOpen must all be true.
- Exception: /inspection/safetyConcern = true requests the Fleet maintenance planner before ordinary outcomes.
- Valid metric range: 0 through 10 inclusive.
- Declared priority score (0–10) less-than-or-equal 5 yields Ready for planner review when all other conditions hold. The other valid side yields Priority planner review.
- A false prerequisite or out-of-range metric yields Hold; unknown rule inputs remain unresolved.
- Numeric comparisons use decimal strings; JSON numeric values do not satisfy that contract.
- A successful scoped lookup with no record means absent. Failed acquisition, wrong case/revision/scope and invalid boolean data mean unknown. Missing required evidence prevents ordinary refusal resolution. If the absent record also carries the exception flag, the exception cannot be ruled out; the result records both missing-required-evidence and unknown.

## Evidence and facts
Artifacts are retained source snapshots. Facts are explicit projections of their typed fields. Presence means a matching record was supplied, not that its decision was positive. All local inputs are asserted, not independently authenticated records or live model output. Matching fields do not prove truth, authority or wall-clock freshness. No date-based expiry is implemented.

## Ownership
- Asset and component record: Fleet records owner
- Diagnostic observation report: Diagnostics analyst
- Technician inspection record: Qualified technician
- Work-order coordination check: Maintenance planner

One escalation target: Fleet maintenance planner. These responsibilities do not create tasks or send notifications. No employer policy is copied.

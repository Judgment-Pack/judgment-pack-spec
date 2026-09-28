# Customer recovery evidence readiness — fictional policy v0.1.0

## Purpose
Is this proposed customer remedy ready for accountable owner review?

This gate does not issue credits, contact customers or close tickets. All records and the CAD 500 review threshold are fictional; no Qualtrics connection, employer policy or endorsement is represented.

## Decision gate
Each record must match the submitted case, revision and scope. Missing or mismatched evidence cannot establish readiness. Positive results require accountable human review.

- Identity fields: caseId, remedyRevision, accountScope.
- Required artifacts: Customer feedback and case record, Service investigation and proposed remedy, Remedy approval record, Account owner and contact permission check.
- Positive prerequisites: /feedback/caseLinked, /service/issueVerified, /approval/remedyApproved, /account/ownerAssigned, /account/contactPermitted must all be true.
- Exception: /approval/exceptionRequested = true requests the Customer recovery owner before ordinary outcomes.
- Valid metric range: 0 through 100000 inclusive.
- Proposed remedy amount (CAD) less-than-or-equal 500 yields Ready for recovery owner review when all other conditions hold. The other valid side yields Additional commercial review.
- A false prerequisite or out-of-range metric yields Hold; unknown rule inputs remain unresolved.
- Numeric comparisons use decimal strings; JSON numeric values do not satisfy that contract.
- A successful scoped lookup with no record means absent. Failed acquisition, wrong case/revision/scope and invalid boolean data mean unknown. Missing required evidence prevents ordinary refusal resolution. If the absent record also carries the exception flag, the exception cannot be ruled out; the result records both missing-required-evidence and unknown.

## Evidence and facts
Artifacts are retained source snapshots. Facts are explicit projections of their typed fields. Presence means a matching record was supplied, not that its decision was positive. All local inputs are asserted, not independently authenticated records or live model output. Matching fields do not prove truth, authority or wall-clock freshness. No date-based expiry is implemented.

## Ownership
- Customer feedback and case record: Customer experience lead
- Service investigation and proposed remedy: Service operations lead
- Remedy approval record: Commercial approval owner
- Account owner and contact permission check: Account owner

One escalation target: Customer recovery owner. These responsibilities do not create tasks or send notifications. No employer policy is copied.

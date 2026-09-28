# Contractor order evidence readiness — fictional policy v0.1.0

## Purpose
Is this contractor order ready for a branch owner to review?

This fictional gate does not reserve stock, grant credit, dispatch a vehicle or promise a delivery. The 10% discount limit is invented and does not represent Ewing policy.

## Decision gate
Each record must match the submitted case, revision and scope. Missing or mismatched evidence cannot establish readiness. Positive results require accountable human review.

- Identity fields: orderId, quoteRevision, fulfillmentScope.
- Required artifacts: Contractor quote and pricing record, Stock allocation check, Credit authorization record, Delivery slot and site check.
- Positive prerequisites: /quote/customerAccepted, /inventory/allocated, /credit/approved, /delivery/confirmed must all be true.
- Exception: /credit/exceptionRequested = true requests the Branch operations owner before ordinary outcomes.
- Valid metric range: 0 through 100 inclusive.
- Quote discount (%) less-than-or-equal 10 yields Ready for branch review when all other conditions hold. The other valid side yields Discount exception review.
- A false prerequisite or out-of-range metric yields Hold; unknown rule inputs remain unresolved.
- Numeric comparisons use decimal strings; JSON numeric values do not satisfy that contract.
- A successful scoped lookup with no record means absent. Failed acquisition, wrong case/revision/scope and invalid boolean data mean unknown. Missing required evidence prevents ordinary refusal resolution. If the absent record also carries the exception flag, the exception cannot be ruled out; the result records both missing-required-evidence and unknown.

## Evidence and facts
Artifacts are retained source snapshots. Facts are explicit projections of their typed fields. Presence means a matching record was supplied, not that its decision was positive. All local inputs are asserted, not independently authenticated records or live model output. Matching fields do not prove truth, authority or wall-clock freshness. No date-based expiry is implemented.

## Ownership
- Contractor quote and pricing record: Branch sales representative
- Stock allocation check: Inventory owner
- Credit authorization record: Credit controller
- Delivery slot and site check: Dispatch coordinator

One escalation target: Branch operations owner. These responsibilities do not create tasks or send notifications. No employer policy is copied.

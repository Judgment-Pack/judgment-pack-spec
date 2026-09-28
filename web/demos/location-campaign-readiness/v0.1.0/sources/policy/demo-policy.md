# Local campaign evidence readiness — fictional policy v0.1.0

## Purpose
Is this location’s campaign package ready for marketing owner review?

This example does not publish content or spend advertising budget. The CAD 1,000 limit is fictional. It does not claim an existing Uberall integration or a policy used by Uberall.

## Decision gate
Each record must match the submitted case, revision and scope. Missing or mismatched evidence cannot establish readiness. Positive results require accountable human review.

- Identity fields: locationId, campaignRevision, channelScope.
- Required artifacts: Location registry record, Campaign offer and budget, Brand and content review, Channel and locale preflight.
- Positive prerequisites: /location/open, /offer/termsConfirmed, /brand/approved, /channel/ready must all be true.
- Exception: /brand/restrictedClaim = true requests the Regional marketing owner before ordinary outcomes.
- Valid metric range: 0 through 1000000 inclusive.
- Campaign spend (CAD) less-than-or-equal 1000 yields Ready for marketing review when all other conditions hold. The other valid side yields Budget exception review.
- A false prerequisite or out-of-range metric yields Hold; unknown rule inputs remain unresolved.
- Numeric comparisons use decimal strings; JSON numeric values do not satisfy that contract.
- A successful scoped lookup with no record means absent. Failed acquisition, wrong case/revision/scope and invalid boolean data mean unknown. Missing required evidence prevents ordinary refusal resolution. If the absent record also carries the exception flag, the exception cannot be ruled out; the result records both missing-required-evidence and unknown.

## Evidence and facts
Artifacts are retained source snapshots. Facts are explicit projections of their typed fields. Presence means a matching record was supplied, not that its decision was positive. All local inputs are asserted, not independently authenticated records or live model output. Matching fields do not prove truth, authority or wall-clock freshness. No date-based expiry is implemented.

## Ownership
- Location registry record: Location operations owner
- Campaign offer and budget: Campaign manager
- Brand and content review: Brand reviewer
- Channel and locale preflight: Regional marketing owner

One escalation target: Regional marketing owner. These responsibilities do not create tasks or send notifications. No employer policy is copied.

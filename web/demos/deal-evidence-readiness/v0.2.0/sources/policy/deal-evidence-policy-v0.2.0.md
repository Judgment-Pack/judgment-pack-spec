# Synthetic deal evidence policy v0.2.0

## Business purpose
Revenue Operations and the Deal Desk need to know which evidence prevents an accountable review of a late-stage deal. The gate identifies missing records, mismatched approvals, known refusals and commercial exceptions. It does not measure customer buying intent or authorize signature.

## Evidence binding and decision gate
Four records are required: CRM, current quote, security review, finance approval. Each must identify the opportunity, quote revision and delivery scope in the submitted review request. CRM must identify that quote as current. The quote must also match the requested terms revision, annual value and discount. Finance must cover those same terms and amounts. A successful, scoped lookup finding no record means absent. Provider errors and identity/revision/scope/commercial mismatches mean unknown, not absent or approved. Review status must not be inferred from the existence of a file.

This demo uses declared record fields and equality checks. Request parameters and local records are asserted. Agreement among them is not independent proof of authenticity, currentness or approver authority. It checks revisions and scope, not validity dates or elapsed age.

For a synthetic opportunity in negotiation, positive annual value, 0–20% discount inclusive, standard terms and affirmative finance/security approvals yield Evidence ready for owner review. Discounts over 20% and up to 100% with matching approvals require commercial review. Known approval refusals and invalid commercial values produce Hold. Nonstandard terms request a human review before ordinary outcome resolution. Missing required evidence, unknown inputs and out-of-scope cases request the Deal Desk owner. An unresolved result is not an execution error.

## Ownership
- CRM opportunity and current quote reference: account executive / Revenue Operations.
- Quote scope, revision and terms: Sales Operations / CPQ owner.
- Security approval: security reviewer.
- Commercial approval: finance approver.
- Discount exceptions and missing-evidence coordination: Deal Desk owner.
- Nonstandard terms: Legal, coordinated by the Deal Desk owner.

These are explanatory responsibilities, not delivered tasks. The runtime has one declared escalation target, Deal Desk owner.

## Measurement and limits
Measure evidence-assembly minutes per reviewed deal, time to identify a missing approval, avoidable rework and disagreements with the existing deal desk. Validate against real historical cases before claiming impact. All entities, amounts and thresholds here are fictional; none represents OpenText policy. Existing CRM/CPQ/contract platforms already provide approvals. The product hypothesis is value from repeatable evidence checks across systems, versioned tests and retained explanations. No source authentication, time-based freshness, portfolio ranking or external action is demonstrated.

# Coverage review

40 project-owned cases pass against the bundled pack v0.2.0 using Runtime v0.23.1. The runtime reports 11 witnessed probes out of 12; coverage remains advisory.

The remaining probe is `conflict`. In this policy, the three normal rules are mutually exclusive:

- Standard and discount-exception rules divide the same numeric value at `<= 20` and `> 20`.
- Both require security and finance to equal `true`; the refusal rule requires at least one to equal `false`.
- The nonstandard-terms exception requests escalation before normal outcome resolution.

Consequently these rules cannot simultaneously select distinct outcomes for a single fact document. We retain the advisory gap instead of fabricating a conflict or changing the policy to satisfy a coverage counter. This is a reasoning review, not a formal proof of the whole runtime.

Decimals are represented as JSON strings as required by JPS ordered comparisons. The source mapping checks opportunity and quote revision before using values. This does not establish authenticity or freshness by age; a production integration needs authenticated source access, current-version and validity-period rules, and an agreed owner for exceptions.


Version 0.2.0 includes 27 policy cases and 13 cases using inputs projected by the real Runner mapping. The mapping checks opportunity, quote, scope and commercial consistency; it does not authenticate local records. The 13 source projections were checked separately through Runner. Their captured facts, evidence and diagnoses are in `mapping/expected-projections.json`. Running the matrix re-evaluates those projected inputs; it does not re-run the source mapping. These are demonstration fixtures, not independent conformance evidence.

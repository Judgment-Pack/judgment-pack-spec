# Maintenance recommendation evidence review — pilot plan

## Hypothesis
A predictive alert still leaves someone to reconcile the vehicle, inspection and existing work orders. The proposed benefit is less time assembling and interpreting evidence for **Fleet maintenance director / transit operations lead**. It is not yet measured market demand.

## Bounded pilot
Start with one workflow, one accountable owner and approximately ten historical or shadow-mode cases, including known exceptions. Agree a baseline and acceptance criteria before the pilot. Keep current decision authority and external actions unchanged. Compare cases using the same definitions and include rejected and unresolved cases rather than selecting only successes.

## Measurements
- Median active minutes spent assembling evidence per case.
- Time from missing evidence to the named owner identifying the next step.
- Number of stale or mismatched approvals caught before a decision.
- Disagreements with the current process, with the owner’s reason for each.
- Integration and maintenance hours required; operator adoption and willingness to pay.

Potential time value = case volume × measured minutes saved × agreed loaded hourly cost / 60. Do not count this as realized savings without an observed baseline.

## Decision to proceed
Proceed only if the buyer confirms a frequent problem, can authorize the data access, and values the measured benefit above integration and operation costs. Stop if existing software already solves the problem cheaply, if no owner can define the decision, or if manual coordination is rare.

## First integration
Telematics or diagnostics API; asset registry; technician inspection record; CMMS work-order API. Start read-only. Use the existing source systems as the record of authority; make owner review and source diagnosis inspectable.

## Joint next step
Redesign the three-minute demo together around an actual planner decision, then identify the minimum pilot evidence that would justify a buying decision.

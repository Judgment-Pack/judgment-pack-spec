# What evidence is holding this deal back?

A worked example for Revenue Operations and the Deal Desk: reconcile a deal's CRM record,
quote, security review and finance approval before an accountable owner reviews it.

**Synthetic demonstration · Pack v0.2.0 · 4 source records · 40 project test cases**

[Download the one-page brief (PDF)](../../web/demos/deal-evidence-readiness/v0.2.0/ONE-PAGE.pdf)
or [get the complete demo (ZIP)](https://judgmentpack.org/artifacts/demos/deal-evidence-readiness/v0.2.0/deal-evidence-readiness-v0.2.0.zip).

## The business problem

An approval may exist and still cover the wrong quote, delivery scope or commercial terms.
The practical question is: **what is missing, what no longer matches, and who needs to act next?**
This example makes those checks explicit and repeatable, with a reason the reviewer can inspect.

### Pain points to test with a Deal Desk

- **Evidence is scattered.** The opportunity, quote and approvals may live in different systems.
  A reviewer has to assemble them before making a decision. The example brings four source
  records into one evidence check; real connections require integration work.
- **An approval can be stale.** A revised quote, delivery scope or discount can invalidate the
  assumptions behind an earlier review. The mapping checks which deal, revision, scope and
  commercial terms each record covers, rather than relying on an approved flag alone.
- **Exceptions can be handled inconsistently.** Reviewers may interpret a discount boundary or
  nonstandard terms differently. The pack makes the selected policy explicit, with saved tests
  for its normal decisions, exceptions and boundaries.
- **Blockers can surface late.** A missing security review or mismatched finance approval may only
  become visible when someone tries to progress the deal. The example identifies the specific
  gap and explains the next responsible role; it does not deliver a task or notification.
- **The same review work gets repeated.** Each change can trigger another round of collecting
  evidence and explaining the decision. A configured Desk/Runner can repeat the check on events
  or schedules and retain the inputs and explanation for later review.

These are problems to investigate with a prospective user. The synthetic demonstration shows
how the checks work; it has not established their frequency, cost or impact on real sales cycles.

### Who should evaluate this

The proposed process owner is **Deal Desk or Revenue Operations**, with a sales leader as a
potential sponsor and finance, security and legal as reviewers. The strongest candidate is a
team repeatedly reconciling complex deals across several systems and approval owners.

Start with one recurring review gate. Establish whether an existing CRM, quoting or contract
workflow could address the gap more simply. The pilot should test the value of consistent checks
across source records, versioned policy and a retained explanation against that alternative.

## The example deal

The fictional Harborline Manufacturing opportunity is worth **USD 480,000 annually**, at a
20% discount, for Canadian cloud delivery to 2,400 seats. The amount illustrates the case;
it is not a revenue or savings claim.

## Follow one deal through the checks

| What changes | Result | What the reviewer does next |
| --- | --- | --- |
| The security lookup finds no review | Unresolved: missing required evidence | Obtain a review for this quote and scope. |
| The security approval covers the previous quote | Unresolved: unknown | Request an approval for the current revision. |
| The approval covers a different delivery scope | Unresolved: unknown | Confirm the Canadian cloud scope and seat count. |
| Finance approved a different amount | Unresolved: unknown | Reconcile the quote and finance approval. |
| All records agree, but the discount is 28% | Commercial review | Ask the Deal Desk owner to review the exception. |
| A reviewer explicitly refuses approval | Hold | Address the refusal before proceeding. |
| Records agree and the standard policy is met | Evidence ready | The accountable owner reviews the deal. |

**Evidence ready is not permission to sign.** These are fictional rules and records, not
OpenText policy or a live OpenText/Salesforce integration. No task, notification or signature
is sent by this example. Responsibilities describe who should act; the pack's declared
escalation target is the Deal Desk owner.

## Where facts and evidence meet

1. **Read four records.** The source fixtures represent CRM, quote, security and finance.
2. **Check what each record covers.** The mapping checks opportunity, quote revision and
   delivery scope. Quote and finance must also match the requested terms, amount and discount.
3. **Derive the inputs.** Matching records supply facts and evidence availability. A successful
   lookup finding no record means *absent*. An unavailable source or a mismatched record means
   *unknown*. A file's existence alone never means approval.
4. **Evaluate the versioned policy.** The runtime computes the disposition. A configured
   Desk/Runner can retain inputs, lineage and a saved brief, then repeat on events or schedules.

Local files and request parameters are **asserted inputs**. Agreement between their fields does
not establish authenticity, currentness, approver authority or freshness by age. The downloaded
example needs no AI or cloud connection; connecting real sources and operating jobs requires
separate configuration.

## Inspect or run the example

The complete ZIP preserves relative paths and includes the policy, pack, test matrix,
13 source scenarios, Runner mapping, sample inputs, one-pager and pilot worksheet.
The same files are available in the [versioned demo release](https://github.com/Judgment-Pack/judgment-pack-spec/releases/tag/demo/deal-evidence-readiness/v0.2.0).

| Artifact | Purpose |
| --- | --- |
| [One-page brief (PDF)](../../web/demos/deal-evidence-readiness/v0.2.0/ONE-PAGE.pdf) | Share the problem and example with a business owner. |
| [Pack (JSON)](../../web/demos/deal-evidence-readiness/v0.2.0/packs/deal-readiness.pack.json) | Read the explicit policy and decision logic. |
| [40 test cases (JSON)](../../web/demos/deal-evidence-readiness/v0.2.0/packs/deal-readiness.matrix.json) | Inspect normal, refusal, missing-input and boundary expectations. |
| [Source mapping (JSON)](../../web/demos/deal-evidence-readiness/v0.2.0/mapping/mapping.json) | See how source records become facts and evidence. |
| [Walkthrough and setup (Markdown)](../../web/demos/deal-evidence-readiness/v0.2.0/README.md) | Reproduce the tests and understand the source fixtures. |
| [Pilot plan](../../web/demos/deal-evidence-readiness/v0.2.0/PILOT-PLAN.md) and [measurement worksheet (CSV)](../../web/demos/deal-evidence-readiness/v0.2.0/PILOT-WORKSHEET.csv) | Test whether this solves a recurring customer problem. |

Download [Runtime v0.23.1](https://github.com/Judgment-Pack/judgment-pack-runtime/releases/tag/v0.23.1)
for your platform, verify its published checksum, and put `jpack` on your PATH. Unzip the demo,
open its directory, then run:

```sh
jpack packs validate --config jpack.json
jpack packs test --config jpack.json
```

All **40 cases pass** with Runtime v0.23.1: 27 policy cases and 13 cases using captured Runner
projections of the supplied records. The matrix evaluates those inputs; it does not re-fetch
records or re-run the mapping. [The coverage review](../../web/demos/deal-evidence-readiness/v0.2.0/COVERAGE-REVIEW.md)
explains the remaining advisory conflict probe. These project tests are not the JPS conformance
corpus or proof of production fitness.

The pack uses **JPS Core 0.2.0-draft**. Project configuration, test matrices, source mapping,
scheduling and briefs are companion-tool conventions, not additions to the specification.
The website serves static documentation and downloads; it does not run jobs.

## Validate the business value

Start with one Deal Desk and three recently delayed deals. Measure evidence-assembly time,
avoidable rework, time to identify a blocker, and agreement with the accountable reviewer.
Separate customer negotiation and approver waiting time from the work this example addresses.

Compare the result with the team's existing CRM, CPQ and contract workflows, including
integration and maintenance costs. A useful pilot demonstrates improvement over that baseline;
it does not assume that the whole deal value is value created.

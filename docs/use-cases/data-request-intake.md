# Worked evaluation: the data-request intake pack

This walks one pack from document to disposition, using four rows of the authoritative
evaluation corpus. Nothing here is new behaviour or a new claim — every input and every
expected disposition below is copied from
[`conformance/evaluation/manifest.json`](../../conformance/evaluation/manifest.json), which
is what an implementation is actually held to.

The pack is [`examples/data-request-intake-triage.json`](../../examples/data-request-intake-triage.json).
The corpus copy at `conformance/evaluation/packs/data-request-intake-triage.json` is
**byte-identical** to it, so the document you read is the document the rows were judged
against.

It is synthetic. It decides nothing real, authorizes nothing, and its thresholds are invented.

## What the pack says

Three outcomes: `proceed`, `clarify-return`, `decline-redirect`.

**Applicability** limits the pack to four request types (`new-data-pipeline`,
`pipeline-change`, `dataset-onboarding`, `reporting-feed`). Outside those it does not apply.

**Evidence** — two required, one optional:

| id | required |
| --- | --- |
| `intake-form` | yes |
| `sponsor-endorsement` | yes |
| `sensitive-data-approvals` | **no** |

**One exception**, `embargoed-information-to-unauthorized`: embargoed material reaching
recipients outside the authorized set forces `decline-redirect`.

**Three rules**, each with `onUnknown: escalate`:

| rule | outcome | when |
| --- | --- | --- |
| `decline-hard-appropriateness-failure` | `decline-redirect` | appropriateness `equals` hard-fail |
| `clarify-incomplete-or-not-evaluable` | `clarify-return` | `any`: completeness incomplete, or appropriateness not evaluable |
| `proceed-complete-and-appropriate` | `proceed` | `all`: completeness complete **and** appropriateness pass |

**Escalation** targets the human role *Intake reviewer* on `not-applicable`,
`missing-required-evidence`, `unknown`, `conflict` and `no-match`.

## Four rows, and why each lands where it does

Every row below supplies `supportedExtensions: []`.

### 1. `proceed-complete-and-appropriate` — §§7.5, 8 step 9

| | |
| --- | --- |
| facts | type `new-data-pipeline`, completeness `complete`, appropriateness `pass`, embargoed `false` |
| evidence | `intake-form` present, `sponsor-endorsement` present |
| disposition | **outcome `proceed`**, no reasons, handoff `none` |

Applicability holds. Both required requirements are present, so step 2 records nothing. The
exception is false. One rule is true and it names `proceed`, so step 9 resolves it. The
optional `sensitive-data-approvals` is not mentioned at all — an omitted **optional**
requirement is not a finding, which is the difference this row makes visible.

### 2. `required-evidence-absent` — §8 step 2

| | |
| --- | --- |
| facts | type `dataset-onboarding`, completeness `complete`, appropriateness `pass`, embargoed `false` |
| evidence | `intake-form` present, **`sponsor-endorsement` absent** |
| disposition | **unresolved**, reason `missing-required-evidence`, handoff `requested` |

The facts alone would have produced `proceed` — they are the same shape as row 1. A missing
*required* requirement is recorded at step 2 and the pack does not reach an outcome. The
handoff is `requested` and triggered by that same reason, which is the escalation the pack
configured. Compare with the optional requirement in row 1: `required` is what makes absence
decisive.

### 3. `forced-outcome-embargo` — §8 steps 4, 6

| | |
| --- | --- |
| facts | type `reporting-feed`, completeness `complete`, appropriateness `pass`, **embargoed `true`** |
| evidence | both present |
| disposition | **outcome `decline-redirect`**, no reasons, handoff `none` |

The exception is true, so step 4 collects its forced outcome and step 6 produces it. The
normal rules are never consulted — and note that `proceed-complete-and-appropriate` would
otherwise have been true on these facts. That is the point of a forced outcome: it is not a
rule that wins a tie, it is a branch taken before rules are weighed.

### 4. `conflict-decline-and-clarify` — §8 step 8

| | |
| --- | --- |
| facts | type `pipeline-change`, completeness `incomplete`, appropriateness `hard-fail`, embargoed `false` |
| evidence | both present |
| disposition | **unresolved**, reason `conflict`, handoff `requested` |

Two rules are true and they name different outcomes: `decline-hard-appropriateness-failure`
gives `decline-redirect`, and `clarify-incomplete-or-not-evaluable` gives `clarify-return`.
Step 8 records `conflict`. **They are never tie-broken** — not by order, not by specificity,
not by severity. A pack that wants a precedence must state it as a condition, and a
disagreement the author did not resolve is returned to a person rather than settled by the
evaluator.

## What this establishes, and what it does not

Core evaluation takes a conforming pack, a fact document, evidence *availability* and a
supported-extension list, and produces an ordered, portable disposition. That is all.

Outside Core entirely:

- **Acquisition.** Nothing here fetches a fact or a document. `evidenceAvailability` is a
  tri-state the caller supplies — `present`, `absent`, `unknown` — and the evaluator never
  learns whether a document is genuine, current, or says what its requirement expects.
- **Authorization.** An outcome of `proceed` is not permission to proceed. No disposition
  authorizes anything, and §3.5 says so.
- **Action.** Nothing acts. A handoff of `requested` does not deliver a request; it records
  that the pack's configured target should receive one.

A disposition is what the pack's author said should follow from these inputs. Whether the
inputs were true, whether the pack is good policy, and whether acting on it is safe are all
questions this format does not answer and does not claim to.

# Deal evidence readiness — synthetic demo v0.2.0

Which evidence is holding this deal back? This self-contained example reconciles CRM,
quote, security and finance records before an accountable owner reviews a fictional deal.

Read the walkthrough at https://judgmentpack.org/examples/deal-evidence-readiness/ or
share `ONE-PAGE.pdf`. All records, organizations, amounts and thresholds are fictional.
They are not OpenText policy, customer data, or a live integration. Evidence ready does
not authorize signature or send a task. The files are licensed under Apache-2.0; see LICENSE.

## Run the pack's tests locally

1. Download Runtime **v0.23.1** for your platform from
   https://github.com/Judgment-Pack/judgment-pack-runtime/releases/tag/v0.23.1.
2. Verify that runtime archive against the release's `checksums.txt`, extract it, and put
   `jpack` on your PATH. The bundle does not install software or start any service.
3. Extract this demo ZIP and open its `deal-evidence-readiness-v0.2.0` directory.
4. Optionally check this bundle's contents with `sha256sum -c SHA256SUMS` (Linux) or
   `shasum -a 256 -c SHA256SUMS` (macOS).
5. Run:

```sh
jpack packs validate --config jpack.json
jpack packs test --config jpack.json
jpack packs lint --config jpack.json
```

Expected: **40 passed, 0 mismatched** with Runtime v0.23.1, and the lint passes: every fact the pack
reads and every evidence requirement it declares has a producer in `jpack.json`, each naming the
source in `mapping/mapping.json` that supplies it. These are project-owned
tests, not JPS conformance evidence. See `COVERAGE-REVIEW.md` for the remaining advisory
conflict probe. There are 27 policy cases and 13 cases using captured source projections.
Running the matrix evaluates those inputs; it does not re-run the source mapping.

Compare a ready case with a missing security review:

```sh
jpack experimental evaluate --config jpack.json --pack-id deal-readiness --facts inputs/ready.facts.json --evidence inputs/ready.evidence.json --rehearsal --format json
jpack experimental evaluate --config jpack.json --pack-id deal-readiness --facts inputs/missing-review.facts.json --evidence inputs/missing-review.evidence.json --rehearsal --format json
```

The first produces `outcomeId: evidence-ready`; the second produces `kind: unresolved`
with reason `missing-required-evidence`. Both are completed evaluations. An unresolved
decision is not an execution failure. These commands perform offline rehearsals, with no
operational job, external write or audit record created.

## Files

| Path | What it contains |
| --- | --- |
| `jpack.json` | Runtime project configuration with relative paths. |
| `packs/deal-readiness.pack.json` | Pack v0.2.0, declaring JPS Core 0.2.0-draft. |
| `packs/deal-readiness.matrix.json` | All 40 project-owned expected results. |
| `sources/policy/` | The synthetic policy cited by the pack. |
| `sources/readiness/scenarios/` | Thirteen folders, each with case, CRM, quote, security and finance JSON files. |
| `mapping/mapping.json` | Runner mapping v2 and per-source derivation rules. |
| `mapping/scenarios.json` | Scenario descriptions, expected dispositions, diagnoses, explanatory owners and next actions. |
| `mapping/expected-projections.json` | Captured Runner facts, evidence and diagnoses for the thirteen fixtures. |
| `inputs/` | Two projected input pairs for the commands above. |
| `PILOT-PLAN.md`, `PILOT-WORKSHEET.csv` | Pilot hypothesis, baseline and measurement template. |
| `ONE-PAGE.pdf` | Shareable business brief. |
| `SHA256SUMS` | Digests of every other bundle file; integrity checks, not authenticated source receipts. |

## Source mapping and the Desk

The mapping is a **Runner convention**, not JPS Core. Each scenario's `case.json` supplies
typed parameters. Its four other JSON files are the selected-file inputs named `crm`,
`quote`, `security`, and `finance`. All use provider `local-file`. Use all five files
from the same scenario folder; do not mix snapshots from different cases.

To inspect this in a compatible Desk, open the extracted project folder. Pack testing
works from the bundled configuration. Configuring a job is a separate step: choose the
pack, use the mapping as its input configuration, supply the scenario's case parameters,
and select its four source files. Preview the projection and compare it with
`mapping/expected-projections.json` before creating a release. A schedule or event needs
a configured source connection that reads a fresh batch; selecting files for one run does
not install an unattended integration. The download does not import local Desk jobs,
releases, schedules, account configuration or stored run history.

For a programmatic mapping check, Runner's authenticated `POST /v1/inputs/preview`
accepts `{"source":{"mapping":...,"case":...,"sources":...}}`. Each named source
supplies a selected-file `snapshot` containing its original bytes, SHA-256, name,
media type and selection time. Follow the Runner's current mapping documentation:
https://github.com/Judgment-Pack/judgment-pack-runner#verified-mapping-v2-runner-and-desk.
The original fixtures were checked using Runner source revision `5c672567f1a88fc7eefc678fb0fc069ed9bb7601`.
Compare projected facts, evidence and source diagnoses before evaluating the pack;
the 40-row matrix alone cannot detect a broken acquisition or mapping implementation.

## Interpretation and limits

- All local records and case parameters are asserted. Their consistency does not prove
  authenticity, currentness, approver authority, or validity by age.
- Identity, quote and scope mismatches yield unknown; a successful scoped lookup finding
  no record yields absent. A file's presence is not approval.
- Commercial numbers use decimal **strings**, as required by JPS ordered comparisons.
  Quote/finance binding uses exact string equality; it is not numeric normalization.
- Explanatory owners are next-action guidance. The pack's declared escalation target
  is the Deal Desk owner, and no external task is delivered.
- This is a single-deal demo. It does not demonstrate portfolio ranking, buying intent,
  close probability, authenticated CRM access, or production readiness.
- The pack is JPS; matrices, project configuration, mapping, briefs and scheduling are
  separately governed companion-tool features. No specification or corpus is changed.

Use the pilot worksheet to compare with existing CRM/CPQ/contract workflows. Measure
capacity and rework rather than attributing the deal's entire value to this tool.

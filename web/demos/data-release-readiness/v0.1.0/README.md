# Data batch evidence readiness — synthetic demo v0.1.0

Is this data batch ready for an accountable release review? Read the walkthrough at https://judgmentpack.org/examples/data-release-readiness/ or share `ONE-PAGE.pdf`.

All organizations, records, thresholds and policies are fictional. This gate does not publish a dataset or replace a quality engine. The 1% threshold is fictional; it is not a recommended production standard.
The files are licensed under Apache-2.0; see LICENSE.

## Reproduce the pack tests

Download Runtime **v0.23.1** for your platform from
https://github.com/Judgment-Pack/judgment-pack-runtime/releases/tag/v0.23.1,
verify its published checksum and put `jpack` on your PATH. Extract this demo and
open its `data-release-readiness-v0.1.0` directory. On Linux check `sha256sum -c SHA256SUMS`; on macOS
use `shasum -a 256 -c SHA256SUMS`. Then run:

```sh
jpack packs validate --config jpack.json
jpack packs test --config jpack.json
jpack packs lint --config jpack.json
jpack experimental evaluate --config jpack.json --pack-id data-release --facts inputs/ready.facts.json --evidence inputs/ready.evidence.json --rehearsal --format json
jpack experimental evaluate --config jpack.json --pack-id data-release --facts inputs/missing-review.facts.json --evidence inputs/missing-review.evidence.json --rehearsal --format json
```

Expected: **18 passed, 0 mismatched**, and the lint passes: every fact the pack reads and every
evidence requirement it declares has a producer in `jpack.json`, naming its source in
`mapping/mapping.json`. The ready input produces `outcomeId: ready`.
The missing-review input is unresolved with reasons `missing-required-evidence` and `unknown`:
the missing artifact also carries the exception flag, so that exception cannot be ruled out.
These are completed decisions, not failed executions. Rehearsal commands do not create an
operational job or audit record and do not take any business action.

## Contents and authority

| Files | Purpose |
| --- | --- |
| `packs/`, `jpack.json` | Pack and relative project configuration; JPS Core 0.2.0-draft. |
| `packs/data-release.matrix.json` | 18 project-owned expectations, using captured source projections. |
| `sources/policy/demo-policy.md` | The original fictional policy cited by the pack. |
| `sources/scenarios/` | 18 folders, each with a case and four separate source artifacts. |
| `mapping/` | Runner mapping v2, scenario expectations and captured facts/evidence. |
| `inputs/` | Projected ready and missing-review input pairs for offline evaluation. |
| `ONE-PAGE.pdf` | Printable business explanation. |
| `PILOT-PLAN.md`, `PILOT-WORKSHEET.csv` | A hypothesis and a measurement template, not proven savings. |
| `INTEGRATION-PLAN.md`, `COVERAGE-REVIEW.md` | Configuration boundaries and the advisory conflict probe. |
| `SHA256SUMS` | File integrity checks; not authenticated source receipts. |

The matrix evaluates projected facts; **it does not re-read files or re-run the mapping**.
The fixtures were separately projected through Runner revision
`5c672567f1a88fc7eefc678fb0fc069ed9bb7601`. Compare facts, evidence and diagnoses with
`mapping/expected-projections.json` when testing another mapping implementation.
The structural coverage report retains an advisory conflict probe: the two positive ranges
exclude one another and the refusal rule contradicts their true prerequisites. See the coverage
review rather than fabricating a conflict case.

## Configure a job separately

Open this extracted project in a compatible Desk to browse and test the pack. For a job, choose
the pack, preview `mapping/mapping.json`, and supply `case.json` plus all four selected files
from **one** scenario folder. The source names are `orchestrator`, `quality`, `contract`, `approval`.
Each source uses `local-file`; its fields must match `datasetId`, `batchId`, `contractRevision`.
Preview the projection and saved tests against the exact pack snapshot before creating a release.

For API callers, Runner's authenticated `POST /v1/inputs/preview` accepts a `source` object
with `mapping`, `case` and named `sources`. Each selected source supplies a `snapshot` with
its original bytes, SHA-256, name, media type and selection time. See the Runner mapping guide:
https://github.com/Judgment-Pack/judgment-pack-runner#verified-mapping-v2-runner-and-desk.

The download does not import a Desk's accounts, jobs, saved briefs, run history or schedules.
To repeat evaluations, configure a local file/event or schedule input that retrieves a new,
consistent source batch. A fixed selected snapshot will reproduce the same inputs. The local
Desk/Runner process must keep running; a browser is not the scheduler. A cloud trigger or a
real vendor connector requires its own configuration. No vendor is connected by this bundle.

## Interpretation and pilot

Artifacts are the supplied records; facts are typed projections of their payloads. A matching
record is present even when its decision is negative. A successful scoped lookup without a record
means absent; mismatches and failed lookups mean unknown. All local inputs are **asserted**.
Field agreement does not prove truth, currentness, approver authority or time-based freshness.
Decimal comparisons use strings, not JSON numbers. No LLM-generated evidence is used.

The pack is JPS; project matrices, mappings, scheduling and briefs are separately governed
companion-tool conventions. The 18 tests are not the normative conformance corpus or a claim
of operational fitness. The proposed owner is **Data product owner**. The pack records a handoff target;
it does not send a notification or assign an external task.

Compare with the team’s orchestrator, quality tooling and data catalog. A separate gate is useful only if coordinating records across them creates recurring work. Use one bounded pilot and measure actual time, rework and owner disagreements
before making value claims.

# Data batch evidence readiness — source integration plan

## Working local implementation
Runner mapping v2 is in `mapping/mapping.json`. All four source kinds are selected local files; all lineage classes are **asserted**. No live vendor connector, authenticated record class or model-generated value is claimed. The case supplies typed lookup parameters; facts are read from artifact payloads.

| Artifact | Accountable source owner | Derived facts |
| --- | --- | --- |
| Orchestrator completion record | Data engineer | `/review/context`, `/review/purpose`, `/pipeline/completed` |
| Data quality report | Data quality owner | `/quality/criticalChecksPassed`, `/quality/invalidRowsPercent` |
| Schema and contract check | Schema owner | `/contract/compatible`, `/contract/overrideRequested` |
| Data owner review | Data product owner | `/owner/approved` |

## Candidate source systems — not connected
Airflow run API or MCP; quality-check JSON in S3 or a local folder; schema registry API; owner approval export.

## Configuration to agree for a real adapter
For each source, record its integration/catalog ID, allowed operation or MCP tool, endpoint, auth reference, fixed request template, typed case parameters and response selectors. Do not invent a tool name from a vendor brand. Select it from the actual available catalog. Pin the source and operation to the release; retain response identity and provenance with each run. Keep secrets in integration configuration, not this folder or a pack.

Storage producers should select an exact artifact or bounded prefix/pattern and a stable published batch, with idempotency and a completion marker. Do not unboundedly scan a bucket. A directory or filename timestamp alone does not establish freshness or authority. Failed lookups remain unknown; only a successful scoped lookup can establish absence.

For an LLM source, retain the prompt/skill revision and request configuration and allow generated values only at explicitly permitted targets. This demo contains no model-generated evidence and must not relabel a model inference as an authenticated record.

## Production questions
Agree source identity, approver authority, time-based validity, polling/event semantics, repeated delivery, retries, timeouts and user ownership. Production ingestion must establish a consistent batch snapshot before the Runner evaluates it. External mutations require a separate reviewed action workflow.

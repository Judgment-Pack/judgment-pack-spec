# Customer recovery evidence readiness — source integration plan

## Working local implementation
Runner mapping v2 is in `mapping/mapping.json`. All four source kinds are selected local files; all lineage classes are **asserted**. No live vendor connector, authenticated record class or model-generated value is claimed. The case supplies typed lookup parameters; facts are read from artifact payloads.

| Artifact | Accountable source owner | Derived facts |
| --- | --- | --- |
| Customer feedback and case record | Customer experience lead | `/review/context`, `/review/purpose`, `/feedback/caseLinked` |
| Service investigation and proposed remedy | Service operations lead | `/service/issueVerified`, `/remedy/amountCAD` |
| Remedy approval record | Commercial approval owner | `/approval/remedyApproved`, `/approval/exceptionRequested` |
| Account owner and contact permission check | Account owner | `/account/ownerAssigned`, `/account/contactPermitted` |

## Candidate source systems — not connected
Experience-management feedback export or API; service desk investigation; commercial approval record; CRM account ownership and contact-permission fields.

## Configuration to agree for a real adapter
For each source, record its integration/catalog ID, allowed operation or MCP tool, endpoint, auth reference, fixed request template, typed case parameters and response selectors. Do not invent a tool name from a vendor brand. Select it from the actual available catalog. Pin the source and operation to the release; retain response identity and provenance with each run. Keep secrets in integration configuration, not this folder or a pack.

Storage producers should select an exact artifact or bounded prefix/pattern and a stable published batch, with idempotency and a completion marker. Do not unboundedly scan a bucket. A directory or filename timestamp alone does not establish freshness or authority. Failed lookups remain unknown; only a successful scoped lookup can establish absence.

For an LLM source, retain the prompt/skill revision and request configuration and allow generated values only at explicitly permitted targets. This demo contains no model-generated evidence and must not relabel a model inference as an authenticated record.

## Production questions
Agree source identity, approver authority, time-based validity, polling/event semantics, repeated delivery, retries, timeouts and user ownership. Production ingestion must establish a consistent batch snapshot before the Runner evaluates it. External mutations require a separate reviewed action workflow.

# Complete contributor contract fixtures

These hand-authored projections exercise RFC 0028 / workflow §5 complete-attribution model 2.
They are synthetic expected records, not output recorded from an executor. The historical
`../workflow/` version-1 representative fixtures and experimental RFC 0024 recordings are unchanged.

`bundle.json` contains two compatible rules, two compatible forcing exceptions, a suppressed rule,
a false rule, fallback, conflict, not-applicable and a hypothetical failed outcome-value resolution.
The forcing case bypasses otherwise matching normal rules. Both namespaces deliberately use
`a-rule`; their credits remain distinct. `semantic-cases.json` fixes expected membership and records
that a failed evaluation has no output. The value-resolution case is a hypothetical retained
unresolved result, not an executed Core `0.3.0` feature. Pack conditions are examples, not evidence
that the bounded readers evaluated them.

`pack-reversed.json` reverses rule and exception order. `bundle-reversed.json` retains exactly
the same memberships and summaries with the changed exact pack and envelope commitments.
`bundle-claimed-omission.json` drops a true member and consistently rebuilds its summary and pins.
Both bounded readers accept this projection: proving the missing condition requires separate
retained evaluation evidence or replay. Its independently fixed expected collection disagrees.
`drift.json` fixes the signed membership difference, with unchanged outcome totals and no changed
Core disposition rows. `mutations.json` contains hand-written replacements and expected outcomes;
its drift mismatch is a local comparison assertion, not a new portable workflow refusal code.

The Python and JavaScript experiments in `tools/workflow_bulk.py` and `tools/workflow_bulk.mjs`
share the public schema and fixtures but independently implement counting and drift. Both were
authored in the same model-assisted work; they do not establish independent authorship or
cross-vendor evidence. Callers supply admitted Core pack bytes independently. `bulk-consistency`
is an experimental accounting result, not a full workflow `reading`. Full inventory, preparations,
acquisition, signatures, evaluation replay, execution records and source truth are outside these
bounded readers. No conformance or publication claim is made.

Canonical commitments were calculated directly from the hand-authored JSON inputs with SHA-256,
not captured from a reader/executor run. Fixtures contain no customer or production data.

`execution-shape.json` is a standalone closed execution-version-3 shape vector with retry,
summary and sample checkpoint members; it is not the executed inventory behind a bundle
projection. `manifest.json` records schema answers, including intentionally out-of-schema
scenario/mutation wrappers and Core packs validated under their own schema.

# RFC 0027 proposal artifacts

These hand-written fixtures and the report schema exercise
[RFC 0027](../0027-pack-design-advisories.md), a Draft. They belong to no conformance manifest,
release corpus or currently published advisory format. The specification incorporation target is
`0.4.0`; the example packs themselves target Core `0.3.0`.

- `report.schema.json`: closed finite-domain report proposal (`formatVersion: 1`). JSON Schema
  validates shape; it does not verify a proof summary, digest, source identity or claim.
- `domain.json`: seven explicit complete inputs, including missing and null facts. Its original
  UTF-8 bytes are retained for the domain digest; whitespace changes identity.
- `sample-pack.json` and `no-fallback-pack.json`: synthetic complete Core packs, differing in
  fallback presence. Their exact file bytes bind the example reports.
- `reports.json`: one complete positive report and shape-control variants. To expand a variant,
  copy `base` and replace its root members with `patch`. `packFile`, when present, identifies the
  alternate retained pack; it is fixture metadata outside the report. Incomplete controls model
  analyzers with different capability/resource limits; they claim no completed proof. `usage.work`
  is illustrative accounting, not a recorded analyzer run.
- `cases.json`: synthetic independently written resolution examples. Copy `basePack` and replace
  its root members with each case's `patch` to construct a complete pack. `intentionalFallback`
  belongs to the case's check configuration, never the pack. `expected` is a small test-harness
  summary with candidate/skipped rule IDs, not the Core disposition wire shape.

The test-only finite evaluator in `tests/test_pack_design_advisories.py` checks the hand-written
expectations, permutations and proof claims. It is neither a production analyzer nor a new reference
evaluator. Suggested cases outside the domain expand a later testing exercise, not this proof.
A scoped unreachable finding establishes nothing about inputs outside the declared finite set.

A format-1 consumer must separately check exact retained input digests, target-version support,
source pointer/ID agreement and distinct entities, witness domain membership, proof semantics,
work used against the declared limit, output count against its limit, and the RFC's byte/depth/node
admission ceilings. Malformed domains and unsupported packs/profiles refuse analysis. Unsupported
checks, exhausted work and omitted output cannot silently become a complete report. No auto-delete,
publication gate, Core rule priority or conformance promotion follows from these artifacts.

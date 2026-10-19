# Policy offline reader — staged draft format 1.0.0

This is the supporting material for the [official-draft promotion candidate](../../../spec/policy.md)
and [RFC 0023](../../../rfcs/0023-policy-companion.md). RFC disposition and release
publication remain pending. The 124 vectors are in no released corpus; passing
them creates no conformance, approval or authority claim.

- [Draft contract](../../../spec/policy.md), [versioned closed schemas](../../../schema/policy/1.0.0/).
- [Portable vector input grammar](vectors/README.md), [exact manifest](vectors/manifest.json).
- [Capability record](capabilities.json), [promotion and identity map](PROMOTION.md).
- [Explicit prototype migration](MIGRATION.md), [publication plan](PUBLICATION.md).
- [Public-process assessment and proposed disposition](ADOPTION.md).

The examples retain the proposed candidate's exact Policy, adoption, Pack, source,
narrative and interpretation bytes. The checker continues to use the repository's
existing `tools/dialect_verify.py` strict reader/canonicalizer; this reuse does not
provide independently authored implementation evidence.

With the repository's pinned Python 3.12 dependencies:

```sh
python conformance/policy/1.0.0/verify.py --capabilities
python conformance/policy/1.0.0/check_vectors.py
python -m unittest discover -s conformance/policy/1.0.0 -p 'test_*.py' -v
```

The independent Policy draft bundle selects these artifacts; Core bundles exclude
the independently versioned schema/corpus directories. The site exposes versioned
schema resources and promotion prose as unreleased review material, while its raw
artifact directory withholds this corpus until publication. No Core corpus changes.

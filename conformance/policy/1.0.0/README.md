# Policy offline reader — draft format 1.0.0

This is the supporting material for the [Policy draft companion](../../../spec/policy.md)
and [RFC 0023](../../../rfcs/0023-policy-companion.md). The maintainer approved the
bounded draft conditional on required green CI and PR 218 merge; until then the
default-branch RFC remains Review. Immutable release publication remains separate.
The 124 vectors become a released corpus only when their exact Policy tag and a
maintainer-published GitHub release both exist. Passing them alone creates no
conformance, approval or authority claim.

- [Draft contract](../../../spec/policy.md), [versioned closed schemas](../../../schema/policy/1.0.0/).
- [Portable vector input grammar](vectors/README.md), [exact manifest](vectors/manifest.json).
- [Capability record](capabilities.json), [promotion and identity map](PROMOTION.md).
- [Explicit prototype migration](MIGRATION.md), [publication plan](PUBLICATION.md).
- [Public-process record and conditional draft disposition](ADOPTION.md).

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
schema resources and conditionally approved draft prose. Its raw artifact
directory is separate from the independent release bundle; obtain released
corpus bytes from the exact immutable Policy release. No Core corpus changes.

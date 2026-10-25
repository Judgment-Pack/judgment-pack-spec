# Historical compatibility evidence

The three manifest files are exact published source bytes, not captured implementation output.
The carrier fragment extracts only `DuplicateMemberError` and `strict_json_loads` from the immutable
0.2 source without changing those definitions; the import prelude permits offline CI execution.
`selector-only-surrogate.json` is a handwritten synthetic compatibility counterexample. Tests pin
these trusted resources and source identities independently of the mutable current implementation.

- `schema/judgment-pack-core-0.1.0-draft.schema.json`: source `80958f50c851e9809cb8036a23622391cf437c99:schema/judgment-pack-core.schema.json`, Git blob `df791f861b9e5dc6335fcf6db426cc107287543e`, preserved SHA-256 `c65c559db33d19d2f327858635266fca7fcc049fb75083a7a8d47517e27224fc`.
- `schema/conformance-manifest-0.1.0-draft.schema.json`: source `80958f50c851e9809cb8036a23622391cf437c99:conformance/manifest.schema.json`, Git blob `b53d34e48aea6c5ee24adb3b70a20353fcaf6d30`, preserved SHA-256 `f073bde8f6f2189edd0334c81c03fecfacf8fae2bd49305a788c75550dcbc2c5`.
- `schema/judgment-pack-core-0.2.0-draft.schema.json`: source `0f30fd7b2c3fd7792249c8f3c5335b9e697a2c7a:schema/judgment-pack-core.schema.json`, Git blob `09672519b1575f89bda40ad4b27448f77777e1dd`, preserved SHA-256 `847910902fa202d9fb3a97062071b532f11649031c9dad32490bf191dca5b3b5`.
- `schema/conformance-manifest-0.2.0-draft.schema.json`: source `0f30fd7b2c3fd7792249c8f3c5335b9e697a2c7a:conformance/manifest.schema.json`, Git blob `41e72265c62c644b1c63d8ad6eb4960a63e7bdf7`, preserved SHA-256 `e531a1a89f188dc12ff682263fdd6a0022bcfb6977dfeb642dd05fcbec5e0723`.
- `schema/conformance-evaluation-manifest-0.2.0-draft.schema.json`: source `0f30fd7b2c3fd7792249c8f3c5335b9e697a2c7a:conformance/evaluation/manifest.schema.json`, Git blob `6d8adc335f62958c6d91c4d2ca64ad8994f78612`, preserved SHA-256 `142c30a33c7272cff5e85522b95d36316d2e195565bc5bef6c04a999e0da51f6`.
- `tests/fixtures/historical-compatibility/0.1.0-draft-document-manifest.json`: source `80958f50c851e9809cb8036a23622391cf437c99:conformance/manifest.json`, Git blob `eb7df5ff57ff80f2694c8913b37ff7d466edaf38`, preserved SHA-256 `a88722b34cf7b408a30fa10bcf91aef2f54285419cc60476ffcaaf37025d7f97`.
- `tests/fixtures/historical-compatibility/0.2.0-draft-document-manifest.json`: source `0f30fd7b2c3fd7792249c8f3c5335b9e697a2c7a:conformance/manifest.json`, Git blob `25fc4ecb7b84f834df9c9591a0246ec2d38ef991`, preserved SHA-256 `ca3888de758e0e52632f3164bd40b41358cde19ea9ca238b50ff715b40713952`.
- `tests/fixtures/historical-compatibility/0.2.0-draft-evaluation-manifest.json`: source `0f30fd7b2c3fd7792249c8f3c5335b9e697a2c7a:conformance/evaluation/manifest.json`, Git blob `5754af3f181af9f3ae165ae141e9a22c6764ad0d`, preserved SHA-256 `d2c8bf03285f5f3478f1c9074dcf0dfb2257211eba009879cd5d9f02cbb545b1`.
- `tests/fixtures/historical-compatibility/tagged_carrier.py`: source `0f30fd7b2c3fd7792249c8f3c5335b9e697a2c7a:tests/test_repository.py`, Git blob `ca321e03408c4e51f4a0c674ab05802f18b35733`, preserved SHA-256 `cae9672d921872cdccd9672e0865374f86aa5bbe9e4d7551fa53960445a29fab`.

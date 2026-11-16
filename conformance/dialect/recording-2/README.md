# Recording schema version 2 vectors (staged for `0.6.0`)

Hand-written vectors for version 2 of the dialect-recording schemas,
[`schema/dialect-recording/2/`](../../../schema/dialect-recording/2/), proposed by RFC 0018's
amendment of 2026-11-15 (issue #326). They are not a conformance corpus and not recordings: no
preparer writes formats `4.0.0` or `4.1.0`, and no claim may cite them.

Each file is a preparation. Two are valid against version 2: a preparation of format `4.0.0` with a
case rule and derivations, byte for byte the one of
[`format-4/case-rule-no-sources/`](../format-4/case-rule-no-sources/), and one of format `4.1.0` with
a paged source, byte for byte the one of
[`format-4.1/paged-three-pages-no-next/`](../format-4.1/paged-three-pages-no-next/). Each other file
is one of those two changed in one rule that version 2 adds, and is invalid against it. The manifest
gives each file's base, the rule, and the change as JSON Patch operations (RFC 6902), so a reader of
the manifest can rebuild every file from its base. One rule can take more than one schema keyword:
`version-in-place-of-format` breaks both `required` (no `formatVersion`) and
`additionalProperties` (a `version` member), since the rule is that one replaces the other.

The Python reader ([`tools/dialect_verify.py`](../../../tools/dialect_verify.py)) is given each
file as the preparation, with the base vector's other files. It reads each valid one and answers
`preparation-differs` for each invalid one, since the preparation it recomputes is the base's. The
TypeScript reader refuses both formats `version-unread` before it reads a preparation.
`tests/test_record_schemas_2.py` holds the schema and the Python reader to the manifest.

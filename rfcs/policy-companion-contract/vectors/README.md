# Reusable proposed-draft agreement vectors

[manifest.json](manifest.json) supplies exact candidate inputs and exact expected
results for independent readers to execute. This is synthetic review material,
not an adopted JPS corpus or independent implementation evidence. No case asserts
approval, live authority, complete organizational coverage or permission.

The manifest is closed under [vectors.schema.json](../vectors.schema.json). It has
`vectorSuiteVersion: "1"`, `maturity: "proposed-draft"`, `synthetic: true` and
`cases`. This carrier version is local test scaffolding, distinct from the
companion `formatVersion` and artifact `version`; it is not a release envelope.
All paths are relative to **rfcs/policy-companion-contract/**, the candidate root,
regardless of the manifest's location. A path must resolve inside that root,
including after resolving symlinks; absolute paths and escaping paths refuse.
NUL-containing paths and path-normalization failures are `invalid-carrier`.
Do not fetch any URI in a document or reference.

Each case is exactly `{id, document, materials, expected}`:

- `id` is a unique readable test identifier.
- `document` describes exact root companion bytes using the source grammar below.
- `materials` is an **ordered** array of `{source, content}` registrations. `source`
  yields exact retained bytes; `content` independently declares the raw digest,
  byte length and media type. Do not repair a mismatching declaration, normalize
  bytes, derive a new declaration, or infer an unregistered media type.
- `expected` is the complete result object to compare with the candidate result.
  JSON object member order is irrelevant; names, values and absence of any extra
  members must agree. Compare both valid and refusal objects, not only exit codes.

The complete closed source grammar has only two alternatives:

```json
{"path":"examples/data-access/policy.json"}
{"repeatByte":120,"byteLength":1048576}
```

For `path`, read the file's bytes exactly; no text conversion or newline changes.
For `repeatByte`, allocate **exactly** `byteLength` copies of the unsigned byte
`repeatByte` (integer 0–255), with no prefix, suffix or encoding. `byteLength` is an
integer 0–4,194,305. A value of zero generates empty bytes. There are no mutations,
JSON reserialization instructions, interpolation, automatic reference rebinding or
other generators. One byte above a normal maximum is intentionally representable
to test refusal. Static document files already carry every altered field and exact
reference; readers do not need the Python scripts used during authoring.

To run a case, first measure/parse/select/canonical-domain-check its root bytes as
[contract §5](../README.md#5-resource-limits-and-refusal-classifications) specifies.
Then check the input's registration count (maximum 16), register materials in list
order (acquiring one source immediately before its registration and checking
declarations and distinct-byte budget), and validate the root
schema and its semantic references. Root bytes themselves are subject to the
262,144-byte limit and count toward the distinct-material budget only when
explicitly registered. A referenced Policy or Pack must be retained in materials;
the carrier does not implicitly register the root or fetch a missing digest.
Return the **first** failing phase's bounded result. Carrier preparation errors
such as an invalid path are `invalid-carrier`; an unavailable file is
`missing-material`. These are never successful document readings.

The compound transport/ordering vectors intentionally name a missing file
(`vectors/intentionally-missing-transport.bin`) or a NUL-containing path. These
are test harness transport inputs, not absent files that a port should create,
repair or fetch. Some earlier root/registration refusals must prevent acquisition
of those later sources. The `vector-carrier-nul-path` case actually reaches its
malformed path and returns `invalid-carrier`. The result for each case includes
these transport refusals; the harness compares them with `expected` and continues
to the next case. Carrier-manifest schema/setup failures remain harness failures.

The manifest includes one over-bound registration count and one over-bound
original reference; its own carrier schema permits those counterexamples. No
candidate reader must accept them. Aggregate boundary vectors include separately
registered identical bytes under two media types; both resolve, and the bytes
spend the aggregate budget only once. Every role independently applies its size
limit. Raw Core numeric extensions include fractional, exponent and unsafe integer
literals; expected results distinguish optional canonical identity from raw pins.

Run the reference harness with the repository's pinned dependencies:

```sh
python rfcs/policy-companion-contract/check_vectors.py
```

Successful harness output is exactly
`{"status":"matched","cases":104,"maturity":"proposed-draft"}`; this is harness
agreement, not the result for an individual document or a conformance claim. Each
refusal vector's exact output is retained in the manifest. The harness and schema
are optional conveniences: another language can read these same bytes and the
source grammar directly, without importing Python or mutable prototype helpers.

# Preparation vectors

Vectors for a second reader of mapping v2's preparation, and of dialect version 3's
(`docs/MAPPING-V2.md`, "Dialect version 3"): given a mapping, a case,
the source records and the trusted input profiles, compute the preparation the
Runner computes, byte for byte, take its SHA-256, and hold a Runtime audit record's
binding (runtime ADR-0050) to it. The specification takes this format up as a
companion document, the **dialect**, with a *preparation verifier* reader class
(Judgment-Pack/judgment-pack-spec#141). Two independent readers agreeing on these
vectors is the evidence that the format can be read without the Runner's code; until
a second one exists, the only reader is `jpack-runner verify-run`.

## The vectors are frozen

These files are **hand-maintained normative data**. They were generated once, by
[`tools/preparation-vectors`](../../tools/preparation-vectors/main.go), from fixtures
the Runner's tests keep under `internal/runner/testdata`, and they are **not
regenerated**: the generator refuses to write into a directory that exists, and CI
does not run it. The ninth vector, `numeric-spellings`, was added afterwards by the
same generator, run into a new directory: it wrote the first eight again byte for
byte, and only the new vector and its manifest entry were taken from that run. The
tenth, `http-shaped-source`, was added the same way: the run wrote the first nine again
byte for byte. So were the eleventh and twelfth, `version-3-bound` and
`unbound-bound-at-import`, the first of dialect version 3: the run wrote the first ten
again byte for byte. Changing a vector is a change of the contract a second reader is held
to, and needs the same justification as changing
[`docs/MAPPING-V2.md`](../../docs/MAPPING-V2.md#the-canonical-form-of-a-preparation).
If a vector looks wrong, the question is whether the documented form is wrong, not
whether the code disagrees with it.

The generator uses the standard library and none of the Runner's code. Two tests
hold the Runner to what it wrote, with no network and no Runtime:

- `TestPreparationVectorsAreByteExact` (`internal/runner`) holds the manifest to its
  SHA-256 and every file to the digest the manifest gives it. It computes each
  vector's preparation from its `mapping.json`, `case.json`, `sources.json` and
  `profiles.json`, at its `verifiedAt`, through the Runner's own code, and requires
  `preparation.json` byte for byte and `preparation.sha256`. It requires the export's
  inputs to be the vector's files, its retained preparation to be the computed one or,
  where the manifest says `altered`, another, and the record's binding to be the
  manifest's. It runs the verifier on the export and compares what it finds with the
  manifest's report.
- `TestVerifyRunReportsEachPreparationVector` (`cmd/jpack-runner`) runs `verify-run`
  on each vector with the manifest's arguments and requires its report on standard
  output, byte for byte, and its refusal.

Read every file as bytes. `.gitattributes` marks `vectors/**` as not text, so a
checkout never converts its line endings.

## What a vector holds

One directory per vector. Each file is the bytes named here, and the manifest gives
its SHA-256.

| File | What it holds |
| --- | --- |
| `mapping.json` | The mapping document, `run.input.source.mapping`, as the export holds it. Its sources name the profiles they trust by digest (`profileDigest`). |
| `case.json` | The case, `run.input.source.case`, as the export holds it. |
| `sources.json` | The source records as the Runner retains them, `run.input.source.sources`: for each source acquired, its response, `{result, receipt, salts}`. Absent for a case-only mapping, which has none. |
| `profiles.json` | The trusted input profiles, which the mapping names by digest and `verify-run` is given as `--profiles`. |
| `unbound.json` | For a dialect bound at import only: the published dialect, of version 3, whose unbound sources name no profile, `run.input.source.import.dialect`, as the export holds it. |
| `binding.json` | For a dialect bound at import only: the binding document that binds its unbound sources to the profiles, `run.input.source.import.binding`, as the export holds it. `mapping.json` is then the bound dialect Runner made of the two. |
| `preparation.json` | The preparation the Runner computes from the files above at the vector's `verifiedAt`, in its canonical form: `verifiedAt` included, no newline. |
| `preparation.sha256` | `sha256:` and the 64 lowercase hexadecimal characters of the SHA-256 of `preparation.json`, no newline. |
| `run.json` | The verification export `verify-run` reads (`--file`), as the Runner wrote it or, for an altered vector, with the one alteration the manifest names. |
| `release-digest.txt` | The release digest `verify-run` is given as trusted (`--release-digest`), no newline. |
| `public-key.txt` | Where `verify-run` checks the record's signature: the key, `--public-key`, ended by a newline. |
| `checkpoints.jsonl` | Where `verify-run` checks the run's chain entry against a held checkpoint: the checkpoint, `--expect`, one line ended by a newline. |

The record a binding is read from is in `run.json`: the record's exact bytes,
`run.auditBytes`, in standard base64, in an export of version 3 or later, and
`run.audit` in a version-2 export, which carries no bytes.

`manifest.json` lists the vectors in order. Each has:

- `name`, its directory; `note`, what it holds and what a reader must conclude;
  `from`, the fixture it was made from; `altered`, the one thing altered, or `null`
  for a fixture as the Runner wrote it.
- `verifiedAt`, the instant the preparation is computed at, whole seconds in UTC.
- `files`, each file's SHA-256.
- `preparation`: its `sha256`; the `binding` Runner passes the Runtime for it, the
  exact bytes; and `retained`, `equal` when the export retains this preparation and
  `altered` when it retains another.
- `import`, for a dialect bound at import only, which file is which: `published`, the
  published dialect (`unbound.json`); `binding`, the binding document
  (`binding.json`); and `bound`, the bound dialect Runner made of them
  (`mapping.json`), whose digest the preparation names as `mappingDigest`. Absent for
  every other vector.
- `recordBinding`, the record's binding as recorded, the exact bytes of its member
  named `binding`, or `null` when it carries none.
- `verifyRun`: the `arguments` given to `jpack-runner verify-run`, where `--file`,
  `--profiles` and `--expect` name the vector's files relative to its directory; its
  `exit` status; the `status` of its report; its `report`, the one line it writes on
  standard output, without the newline that ends it, or `null` when it writes none;
  and its `error`, the refusal it prints after `runner: ` on standard error, or `null`.

## The vectors

| Vector | From | What is altered | What verify-run finds |
| --- | --- | --- | --- |
| `valid` | `mapping-v2-calculated-bound` | nothing | `verified-inputs`, binding `matches`, signed and witnessed |
| `recomputed-one-second-later` | the valid case | the export's preparation recomputed one second later; the record as it was | `binding-mismatch` |
| `unbound-record` | `mapping-v2-before-calculators` | nothing: a record from before Runner passed a binding | `unbound`, with `--require-bound` (binding `absent`) |
| `foreign-binding-kind` | the valid case | the record's binding names another scheme, with the preparation's digest; the record signed again | `binding-foreign-kind` |
| `changed-table-lineage` | the valid case | the retained lineage names another instant for the calculator's table | refused: `retained lineage does not match recomputation` |
| `disposition-differs-from-audit` | the valid case | the retained result names another outcome than the audit record | `audit-disposition-mismatch` |
| `unsigned-parameters` | `mapping-v2-unsigned-parameters` | nothing | `verified-inputs`, naming the parameters no receipt commits |
| `escaped-strings` | `mapping-v2-before-exact-bytes` | nothing: a case-only run whose case holds `&`, `<`, `>` and non-ASCII letters | `verified-inputs` |
| `numeric-spellings` | `mapping-v2-calculated-numeric` | nothing: the valid case's mapping and inputs with three integer case parameters more, `-0`, `9007199254740991` and `-9007199254740991` | `verified-inputs`, binding `matches`, signed and witnessed |
| `http-shaped-source` | `mapping-v2-http-shaped` | nothing: one source of shape `http`, its record recorded from a stand-in of a gateway `http` source in the test's process | `verified-inputs`, binding `matches`, signed and witnessed |
| `version-3-bound` | `mapping-v3-bound` | nothing: the valid case's mapping written as a dialect document of version 3, its source bound | `verified-inputs`, binding `matches`, signed and witnessed |
| `unbound-bound-at-import` | `mapping-v3-imported` | nothing: a published version-3 dialect whose source is unbound, its binding document, and the bound dialect Runner made of them at import, with a source of shape `http` as in `http-shaped-source` | `verified-inputs`, binding `matches`, signed and witnessed |

The valid case is also the calculated-values case: its one source is a calculator
that computed. Its preparation's digest is the digest its record binds, so a reader
that computes `preparation.json` from the inputs and takes its SHA-256 holds the
record's binding to it. `escaped-strings` is there for the canonical form's escaping:
the Runner writes `A&B <x> café ☃` in a preparation as `A\u0026B \u003cx\u003e café ☃`.
`numeric-spellings` is there for numbers as written: each outcome keeps `-0`, not `0`,
and the largest and the least integers mapping v2 admits without an exponent. Numbers
such as `1.00` and `1e+02`, and integers beyond 2^53−1, are outside what mapping v2
admits (integers from −(2^53−1) to 2^53−1, with no fraction or exponent): preparation
refuses them as a parameter and as a copied value, so no preparation holds them and no
vector can (`TestAPreparationKeepsItsNumbersAsWritten`). `http-shaped-source` is there for
the source's shape: its one source is a gateway source of shape `http`, whose request is
a path, a method and a query rather than a tool call, and whose result is the adapter's
status, headers and body. Its preparation has the form of every other vector's: a
preparation does not name its source's shape, which the profile the mapping pins by
digest and the receipt it cites carry, and nothing in it depends on the shape.

The last two are dialect version 3 (`docs/MAPPING-V2.md`, "Dialect version 3").
`version-3-bound` is there for the version: its mapping is written as a version-3
document, with no `provider`, `facts` or `evidence`, which Runner writes empty in a
version-2 document only, so its `mappingDigest` is the digest of `mapping.json`'s
canonical bytes as it is; its preparation has the form of the version-2 vectors', its
`version` 3. `unbound-bound-at-import` is there for the binding: a reader binds
`unbound.json` with `binding.json` under `profiles.json` (each unbound source's
`platform`, `operation`, `shape` and `record` removed and the profile the binding
names added, every other member as written) and must get `mapping.json`; the profile
must be of the source's `shape`, and its `adapter.name` the source's `record`. The
preparation commits `mapping.json` by its digest, and neither `unbound.json`'s nor
`binding.json`'s: the run keeps them beside it, and no preparation holds them.

## The canonical form

Stated once, in [`docs/MAPPING-V2.md`](../../docs/MAPPING-V2.md#the-canonical-form-of-a-preparation):
members sorted by name in byte order, no insignificant whitespace, numbers as
written, strings escaped as Go's `encoding/json` escapes them, `verifiedAt` in
whole seconds of UTC, and the SHA-256 over all of it. It is not the gateway's
canonical JSON, by which a mapping and a profile are digested
(`internal/runner/testdata/gateway/canon.json` holds that one's vectors): that form
writes `&`, `<` and `>` as they are.

## Where the fixtures came from, and what is in them

Every fixture was written by a test of this repository, run with a real Runtime, and
is published byte for byte; none was changed to be published. The ids, times and keys
in them are those of the run that wrote them, and are data now.

- `mapping-v2-calculated-bound` was written for these vectors, by
  `TestACalculatedSignedAndWitnessedRunRefusesAnswerAndTableTimeTampering` with
  `JPACK_V2_CALCULATED_EXPORT_DIR` set, under the published Runtime 0.31.0, the
  release CI pins: no fixture the tests kept had a record that binds its preparation,
  or a calculator. The record is the line that Runtime wrote, chained, with the
  binding Runner passed. Its signature line was written by the test's helper in the
  form the Runtime's guide states, under the seed of RFC 8032's first test vector,
  whose public key is `public-key.txt`. `foreign-binding-kind` is signed again with
  the same seed. It signs nothing real.
- `mapping-v2-calculated-numeric` was written the same way, by
  `TestAPreparationKeepsItsNumbersAsWritten` with `JPACK_V2_NUMERIC_EXPORT_DIR` set:
  the valid case's run, made again with the three case parameters more.
- Each acquisition receipt in the fixtures was signed by the test with a key made
  for that run, standing in for a gateway: its public key is in
  `profiles.json`, and its private key was not kept. The calculator's answer is the
  test's.
- `mapping-v2-http-shaped` was written as `mapping-v2-calculated-bound` was, under the
  published Runtime 0.31.0, by `TestAnHTTPShapedRunIsSignedWitnessedAndBound` with
  `JPACK_V2_HTTP_EXPORT_DIR` set. Its source's record was recorded from a stand-in, in
  the test's process, of a gateway source its operator declared `http`: an endpoint the
  test served over TLS on the loopback address its profile names, read as the gateway's
  `adapter-http` reads one, and a receipt the stand-in signed as a gateway signs one. No
  live service was asked; the profile names the adapter `adapter-http`, version
  `stand-in`.
- `mapping-v3-bound` was written as `mapping-v2-calculated-bound` was, under the
  published Runtime 0.31.0, by `TestAVersion3RunIsSignedWitnessedAndBound` with
  `JPACK_V3_BOUND_EXPORT_DIR` set: the valid case's run, its mapping of version 3.
- `mapping-v3-imported` was written the same way, by
  `TestAnImportedRunIsSignedWitnessedAndBound` with `JPACK_V3_IMPORT_EXPORT_DIR` set:
  the run of `mapping-v2-http-shaped`'s mapping, published as version 3 with its source
  unbound and bound at import to the stand-in's profile. Its record was recorded from
  the stand-in as `mapping-v2-http-shaped`'s was; no live service was asked, and the
  catalog names it binds, `intake-api` and `requests.read`, name no real catalog.
- `mapping-v2-before-calculators`, `mapping-v2-unsigned-parameters` and
  `mapping-v2-before-exact-bytes` were written before Runner passed a binding: their
  records carry none.

The families `v1-file-mapping-run` and `no-mapping-run` are not here: a run without a
mapping v2 has no preparation.

## What the vectors do not cover

- The digests of a mapping and of a profile, which are taken over the gateway's
  canonical JSON, and a receipt's signature: the gateway's vectors cover them.
- The derivation rules a source's read applies: the vendored derivation corpus covers
  them (`internal/derivation/testdata`).
- A record's signature and a chain entry, which `verify-run` checks here only as it
  checks any export: they are the Runtime's and the chain's to state, not the
  preparation's.
- A re-execution (`--runtime`): no vector asks for one.

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
again byte for byte. So were the research vectors, the twenty-six after them, the first
of the kind `research`: the run wrote the first twelve again byte for byte. So was the
thirty-ninth, `skipped-source-dependency-unavailable`, the first to hold a skipped
source: the run wrote the first thirty-eight again byte for byte. So were the fortieth
and forty-first, `acquired-dependent-source` and `acquired-dependent-source-unknown`,
the first to hold an acquired source that declares source parameters: the run wrote
the first thirty-nine again byte for byte. Changing a
vector is a change of the contract a second reader is held to, and needs the same
justification as changing
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
  `altered` when it retains another; or `recorded` when the vector's inputs were
  changed after the run, so that the Runner computes no preparation from them and
  refuses them as `verify-run` does: `preparation.json` is then the preparation the
  run recorded, held fixed, which the export retains.
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
| `gtm-company-person-valid-types-all-six` | `research/gtm-company-person-valid-types-all-six` | nothing: a research run of all six field types, bound at import, its responses recorded from the stand-in | `verified-inputs`, binding `matches`, signed and witnessed |
| `gtm-company-person-presence-optional-omitted` | `research/gtm-company-person-presence-optional-omitted` | nothing: every optional entry omitted | `verified-inputs`, binding `matches`, signed and witnessed |
| `gtm-company-person-presence-required-not-found` | `research/gtm-company-person-presence-required-not-found` | nothing: a required entry `not-found` in each source | `verified-inputs`, binding `matches`, signed and witnessed |
| `gtm-company-person-presence-integer-zero` | `research/gtm-company-person-presence-integer-zero` | nothing: integer zero | `verified-inputs`, binding `matches`, signed and witnessed |
| `gtm-company-person-presence-decimal-zero` | `research/gtm-company-person-presence-decimal-zero` | nothing: the decimal `"0"` | `verified-inputs`, binding `matches`, signed and witnessed |
| `gtm-company-person-presence-boolean-false` | `research/gtm-company-person-presence-boolean-false` | nothing: `false` | `verified-inputs`, binding `matches`, signed and witnessed |
| `gtm-company-person-presence-text-empty` | `research/gtm-company-person-presence-text-empty` | nothing: the empty text | `verified-inputs`, binding `matches`, signed and witnessed |
| `gtm-company-person-stale-and-conflicting-unknown` | `research/gtm-company-person-stale-and-conflicting-unknown` | nothing: stale observations and conflicting values, each observation cited | `verified-inputs`, binding `matches`, signed and witnessed |
| `gtm-company-person-failed-fallback-all-unavailable` | `research/gtm-company-person-failed-fallback-all-unavailable` | nothing: a reconciliation of three sources, `not-found`, `stale` and `conflicting`, deriving `unknown` | `verified-inputs`, binding `matches`, signed and witnessed |
| `gtm-company-person-failed-fallback-secondary-found` | `research/gtm-company-person-failed-fallback-secondary-found` | nothing: the same reconciliation taking the secondary's found value | `verified-inputs`, binding `matches`, signed and witnessed |
| `gtm-company-person-changed-binding-second-installation` | `research/gtm-company-person-changed-binding-second-installation` | nothing: valid-types as a second installation binds it, one assignment and its profile changed | `verified-inputs`, binding `matches`, signed and witnessed |
| `gtm-company-person-changed-binding-old-preparation` | `research/gtm-company-person-changed-binding-second-installation` | the export retains valid-types' preparation, recorded under the first installation's binding | refused: `retained lineage does not match recomputation` |
| `gtm-company-person-changed-response-retained-result` | `research/gtm-company-person-valid-types-all-six` | the person's retained page says another thing; its receipt and the recorded preparation as they were | refused: `Source person: retained response 2, through the profile page: result digest failed (acquisition-invalid). …` |
| `work-item-triage-valid-types-all-six` | `research/work-item-triage-valid-types-all-six` | nothing: a research run of all six field types, bound at import, its responses recorded from the stand-in | `verified-inputs`, binding `matches`, signed and witnessed |
| `work-item-triage-presence-optional-omitted` | `research/work-item-triage-presence-optional-omitted` | nothing: every optional entry omitted | `verified-inputs`, binding `matches`, signed and witnessed |
| `work-item-triage-presence-required-not-found` | `research/work-item-triage-presence-required-not-found` | nothing: a required entry `not-found` in each source | `verified-inputs`, binding `matches`, signed and witnessed |
| `work-item-triage-presence-integer-zero` | `research/work-item-triage-presence-integer-zero` | nothing: integer zero | `verified-inputs`, binding `matches`, signed and witnessed |
| `work-item-triage-presence-decimal-zero` | `research/work-item-triage-presence-decimal-zero` | nothing: the decimal `"0"` | `verified-inputs`, binding `matches`, signed and witnessed |
| `work-item-triage-presence-boolean-false` | `research/work-item-triage-presence-boolean-false` | nothing: `false` | `verified-inputs`, binding `matches`, signed and witnessed |
| `work-item-triage-presence-text-empty` | `research/work-item-triage-presence-text-empty` | nothing: the empty text | `verified-inputs`, binding `matches`, signed and witnessed |
| `work-item-triage-stale-and-conflicting-unknown` | `research/work-item-triage-stale-and-conflicting-unknown` | nothing: stale observations and conflicting values, each observation cited | `verified-inputs`, binding `matches`, signed and witnessed |
| `work-item-triage-failed-fallback-all-unavailable` | `research/work-item-triage-failed-fallback-all-unavailable` | nothing: a reconciliation of three sources, `not-found`, `stale` and `conflicting`, deriving `unknown` | `verified-inputs`, binding `matches`, signed and witnessed |
| `work-item-triage-failed-fallback-secondary-found` | `research/work-item-triage-failed-fallback-secondary-found` | nothing: the same reconciliation taking the secondary's found value | `verified-inputs`, binding `matches`, signed and witnessed |
| `work-item-triage-changed-binding-second-installation` | `research/work-item-triage-changed-binding-second-installation` | nothing: valid-types as a second installation binds it, one assignment and its profile changed | `verified-inputs`, binding `matches`, signed and witnessed |
| `work-item-triage-changed-binding-old-preparation` | `research/work-item-triage-changed-binding-second-installation` | the export retains valid-types' preparation, recorded under the first installation's binding | refused: `retained lineage does not match recomputation` |
| `work-item-triage-changed-response-record-fields` | `research/work-item-triage-valid-types-all-six` | the follow-up record's answer for points changed under the record's own receipt; the receipt and the recorded preparation as they were | refused: `Source follow-up: the record's own receipt, through the profile assistant: result digest failed (acquisition-invalid). …` |
| `skipped-source-dependency-unavailable` | `mapping-v2-skipped-source` | nothing: three operations, the third skipped because a source it waits on is not `resolved` | `verified-inputs`, binding `matches`, signed and witnessed |
| `acquired-dependent-source` | `mapping-v2-acquired-dependent` | nothing: three operations, the third acquired with both its source parameters valued, its claim `resolved` | `verified-inputs`, binding `matches`, signed and witnessed |
| `acquired-dependent-source-unknown` | `mapping-v2-acquired-dependent-unknown` | nothing: as `acquired-dependent-source`, the third's claim `unknown` | `verified-inputs`, binding `matches`, signed and witnessed |

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

The research vectors are the kind `research` (`docs/MAPPING-V2.md`, "Research
sources"), the runs of the two examples of the specification's fixture plan
(spec/dialect.md §11), named by its form `<example>-<item>-<variant>`. Each is a
dialect of version 3 published with its research sources unbound, `unbound.json`,
bound at import by `binding.json` to the installation's AI and web profiles,
`profiles.json`, each of class `generated` and declaring the capabilities it serves and
the model; `mapping.json` is the bound dialect. `sources.json` holds each research
source's research record, `{"response": {"result": R}}`, and, for the follow-up of
`work-item-triage`, the record's own receipt and salts beside it: `R.responses` are the
responses retained, each with the profile it came through, its request, its result, its
receipt and its salts, and `R.fields` the typed answers, citing them by index. A reader
binds `unbound.json` with `binding.json` under `profiles.json` and must get
`mapping.json`; replays each retained response under the profile it names, over its own
request, and the record's own receipt over the source's request and the whole record;
derives each target from `R` by the source's read; and must get `preparation.json`,
whose `cites` follow the order of sources and whose lineage names each research
source's citations as `receipts`. Nothing asks a model or reads a page. The two
`changed-binding` vectors are the second installation's run, which reads, and its
export holding the first installation's preparation, which a reader recomputes, at its
`verifiedAt`, as another preparation (`preparation-differs`). The two
`changed-response` vectors change one retained result, or the answers under the
record's own receipt, with the receipts and the recorded preparation held fixed: a
reader replaying them finds `acquisition-invalid`, and `preparation.json` is the
preparation the run recorded (`retained`: `recorded`).

The plan's items that are refusals, a malformed or over-bound recipe, record or
binding, are reader tests and not vectors (spec/dialect.md §11), until the staging
README of the specification defines a refusal row; Runner's tests hold them
(`internal/runner/research_test.go`). Not recorded: a skipped earlier source in a
reconciliation, which Runner skips as it skips a source of every kind, in the form
`skipped-source-dependency-unavailable` holds; and the parent and child of
`selected-parent-child`, which are the workflow's (RFC 0020).

`skipped-source-dependency-unavailable` is there for a skipped source
(`docs/MAPPING-V2.md`: "Missing/unknown/absent upstream outputs skip the dependent
source and record `dependency-unavailable`"). Its mapping has three operations of one
profile: `intake` resolves the case's request and its type; `sponsor`'s record names no
sponsor, so its claim is `unknown`; and `endorsement` declares two source parameters,
each a fact target of an earlier source, `approver`, `sponsor`'s `/sponsor/id`, and
`requestType`, `intake`'s `/intake/type`, and is skipped, since `sponsor`'s claim is not
`resolved`. A skipped source is not acquired: `sources.json` holds no record of it,
`cites` no citation, and its read does not apply.
Runner writes the skipped-source form the specification's §§9.2–9.3 state since
judgment-pack-spec#194 (`c51c81d`):

- the outcome's `claim`, present: `{"acquisitionStatus": "unknown", "basis": [],
  "evidenceAvailability": {}, "facts": {}, "reason": "dependency-unavailable"}`;
- the outcome's `status`, `unknown`;
- each lineage entry's `status`, `unknown`;
- each lineage entry's `dependencies`, the source parameters it waited on, as objects
  `{"parameter", "source", "pointer"}` in the order of the parameters' names,
  `approver` before `requestType`, though `intake` comes before `sponsor` among the
  sources.

Its other members are as the text states them: the outcome's `reason`
`dependency-unavailable`, no `arguments`, and as `parameters` those that have a value
(`runAt`, `requestId`, `requestType`, and not `approver`); each lineage entry's
`reason` `dependency-unavailable`, `present` false, `basis` `[]` and no `receipt`.

`acquired-dependent-source` and `acquired-dependent-source-unknown` are there for an
acquired source that declares source parameters, the other side of Runner's rule for
`dependencies`: a lineage entry carries them for every source that declares one,
acquired or skipped (the specification's §9.3 states it so since
judgment-pack-spec#194, the amendment for judgment-pack-spec#189). Their mapping is
`skipped-source-dependency-unavailable`'s but for each source's `profileDigest`, the
digest of the profile whose key was made for the run. `sponsor`'s record names a
sponsor, `S-1`, so its claim is `resolved`, and `endorsement` is acquired with both its
source parameters valued: `approver` `S-1` and `requestType` `data-access`. Its
record names the endorsement in `acquired-dependent-source`, and its claim is
`resolved` (`endorsed`); it names none in `acquired-dependent-source-unknown`, and its
claim is `unknown` (`not-endorsed`). A reader concludes, of each:

- each of `endorsement`'s lineage entries, the fact `/endorsement` and the evidence
  `sponsor-endorsement`, carries `dependencies`, every source parameter it declares,
  each valued, as objects `{"parameter", "source", "pointer"}` in the order of the
  parameters' names, `approver` from `sponsor` before `requestType` from `intake`,
  though `intake` comes first among the sources: the same array as the skipped
  source's;
- the parameters' values are carried into its request: the outcome's `parameters` are
  `approver`, `requestId`, `requestType` and `runAt`, and its `arguments` are
  `{"tool": "lookup", "arguments": {"table": "endorsements", "approver": "S-1",
  "requestType": "data-access"}}`;
- each of its entries carries its `receipt`, `endorsement`'s citation, and the
  outcome's `status` and `reason`; no other source's entry carries `dependencies`.

`acquired-dependent-source-unknown` holds that a claim of `unknown` does not drop
them: its `/endorsement` entry is not `present`, its `sponsor-endorsement` entry is
`present` with the availability `unknown`, and both carry `dependencies` as
`acquired-dependent-source`'s do.

The last two of the first twelve are dialect version 3 (`docs/MAPPING-V2.md`, "Dialect version 3").
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
- `mapping-v2-skipped-source` was written as `mapping-v2-calculated-bound` was, by
  `TestASkippedSourceRunIsSignedWitnessedAndBound` with `JPACK_V2_SKIPPED_EXPORT_DIR`
  set, under the Runtime CI pins (commit `015949ca`), which takes a binding. Its record
  is signed under the seed of RFC 8032's first test vector, whose public key is
  `public-key.txt`. Its two acquisition receipts were signed by the test with a key made
  for the run, standing in for a gateway: the public key is in `profiles.json`, and the
  private key was not kept. The profile names the adapter `adapter-mcp`, version
  `stand-in`; no live service was asked, and every identifier is synthetic.
- `mapping-v2-acquired-dependent` and `mapping-v2-acquired-dependent-unknown` were
  written as `mapping-v2-skipped-source` was, by
  `TestAnAcquiredDependentSourceRunIsSignedWitnessedAndBound` with
  `JPACK_V2_ACQUIRED_EXPORT_DIR` set to the directory that holds them, under the
  Runtime CI pins (commit `09206e74`), which takes a binding. Each record is signed
  under the seed of RFC 8032's first test vector, whose public key is
  `public-key.txt`. Each run's three acquisition receipts were signed by the test with
  a key made for the run, standing in for a gateway: the public key is in
  `profiles.json`, and the private key was not kept. The profile names the adapter
  `adapter-mcp`, version `stand-in`; no live service was asked, and every identifier
  is synthetic.

- Each run under `research/` was written as `mapping-v2-calculated-bound` was, by
  `TestResearchRunsAreSignedWitnessedAndBound` with `JPACK_RESEARCH_EXPORT_DIR` set,
  under the Runtime CI pins (commit `4ea33155`), which takes a binding. Its research
  records were recorded from a stand-in, in the test's process, of a gateway serving
  three channels over TLS on the loopback address its profiles name: an AI
  connection's answer, a search connection's links and a public page, each read as
  `adapter-http` reads an endpoint, each receipt signed by the stand-in as a gateway
  signs one, under a key made for the run, at call indexes of one session. The
  profiles name the adapters `adapter-sources` and `adapter-web`, version `stand-in`,
  and a model, `synthetic-research-model-1`, which is a name and no model. No model was
  asked and no live service was read; every identifier and observation is synthetic.
  Each `changed-binding-second-installation` run was recorded right after its
  example's `valid-types-all-six`, by the same stand-in in a session of its own.

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

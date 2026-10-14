# dialect-verify-ts: a second, independent preparation verifier

This is a *preparation verifier*, the conformance class that the proposed companion document
[`spec/dialect.md`](../../spec/dialect.md) defines (its §14), written in TypeScript from that
document's text alone, so that [RFC 0018](../../rfcs/0018-dialect.md) can meet RFC 0000's evidence
bar of two independent readers agreeing on the vectors. The repository's first reader was not read
while this one was written; the files that were read are listed below.

Like the companion document, it is normative for nothing. The vectors it reads are
[staged](../../conformance/dialect/README.md): in no corpus, and no conformance claim of the class is
available until a specification version publishes them (§14). Agreement between two readers shows
that they read the format alike, and no more; a reading never establishes anything §13 says a
preparation does not establish.

## Running it

Node 22.18 or later on `PATH`; no dependencies and no build step (Node strips the types).

```text
node src/main.ts <vector directory> [--require-binding]
node src/main.ts --dialect F --case F [--acquisitions F] --profiles F --preparation F [--record F] [--require-binding]
```

A vector directory is read as the [staging note](../../conformance/dialect/README.md) lists:
`mapping.json`, `case.json`, `sources.json` (`{}` when absent), `profiles.json`, and from `run.json`
the preparation `run.input.preparation` and the record (`run.auditBytes`, standard base64, or else
`run.audit`). Whether a binding is required is the caller's to say: the vectors' answers are in
[`manifest.json`](../../conformance/dialect/manifest.json), `requiresBinding`. With the second form,
`--record` names a file holding the record line; one trailing line feed is removed, and nothing else.

`--emit-preparation F` writes the recomputed preparation's canonical bytes (§9.5) when the
recomputation completed; `--explain` writes the reason for a refusal or a finding to standard error.

It prints one line of JSON, members ordered by code point and every number its literal (§9.5's form):

| Answer | Report | Exit status |
| --- | --- | --- |
| a reading | `{"binding", "digest", "evidence", "facts", "result": "reading", "targetsByClass"}`, with `unsignedFreshness` and `unsignedParameters` when not empty | 0 |
| a refusal | `{"refusal": <code>, "result": "refusal"}` | 1 |
| a finding | `{"finding": <code>, "result": "finding"}` | 2 |
| the program could not run: an argument, a file that cannot be opened, a vector directory without its files, a `--emit-preparation` file that cannot be written (written before the report) | nothing on standard output | 3 |

`facts` and `evidence` are the facts document and the evidence-availability document (§8.1).

## Tests

`npm test`, or `node --test test/vectors.test.ts test/units.test.ts`:

- [`test/vectors.test.ts`](test/vectors.test.ts) reads every staged vector and holds the answer to the
  manifest's row (`expectedResult`, and `expectedBinding` or `expectedFinding`); the recomputed
  preparation to the vector's `preparation.json`, byte for byte, and a reading's digest to
  `preparation.sha256`; and a reading's facts and evidence-availability documents to the export's
  `run.input.facts` and `run.input.evidence`. A vector this reader could not answer from the text would
  be listed there as a known disagreement, with its reason; there is none.
- [`test/units.test.ts`](test/units.test.ts) holds the forms the text fixes (§1, §9.5, §12) and this
  reader's answers to inputs no vector holds, each made from a vector by one change; some re-sign the
  receipts under a key generated in the test, to reach the checks after a receipt's. Those answers are
  this reader's readings of the text, not the vectors'.

The repository's Python suite runs both through `tests/test_dialect_ts.py`, with
`--disable-wasm-trap-handler`: Node strips types with a WebAssembly module, which cannot reserve its
memory under an address-space limit (`ulimit -v`) without that flag.

There is no `typecheck` script: a type-check needs Node's type declarations as well as TypeScript, and
this directory installs nothing. The sources were checked with TypeScript 5.9 and Node 22's
declarations, outside the repository, with `--strict --noUnusedLocals --noUnusedParameters
--erasableSyntaxOnly --verbatimModuleSyntax --allowImportingTsExtensions --module nodenext`.

## What was read

Only these, under the independence protocol of its brief: `spec/dialect.md`, all of it;
`conformance/dialect/README.md` and `conformance/dialect/manifest.json`; the files of each vector
directory under `conformance/dialect/vectors/`, as data; `rfcs/0000-rfc-process.md`; `GOVERNANCE.md`;
`spec/judgment-pack-core.md`, §6.3 and §8.2, which the companion document cites; RFC 0018's title
block; and the repository's `README.md`, `tests/test_site.py` and `.github/workflows/conformance.yml`.
After the cross-vendor review round, and on the maintainer's disposition of it: that disposition, and
`spec/checkpoint-witness.md` §5, which §1 adopts by reference for the key rule and the equation.
Not read: the first reader or its test, the Runner's own README and manifest under
`conformance/dialect/vectors/`, the rest of RFC 0018, the review round's record, any other repository,
and any Go or Python source.

**Changed since.** The RFC 0018 amendment that wrote the six choices below into the text changed this
reader on one of them, a number literal's start (choice 2), and added a test for each. Its author had
read both readers; that change follows the text, takes no code from the first reader, and is no part
of this reader's independence, which is the account above.

## Where the text was not enough

No vector depends on any point below: every vector gets the same answer under either reading of each.

### Rules the companion document incorporates by reference

1. **The key rule and the equation**, the checkpoint witness statement's §5 (§1: "A key is held to the
   key rule of the checkpoint witness statement, its §5"). Read after the review round: the key rule this
   reader implements is exactly that one. A key is refused when its 32 bytes are not the canonical
   encoding of a point, read as written (`y` of p or more, or `x` 0 with the sign bit set), when the point's
   order divides 8 (the eight points §5 lists), or when they name no point; a key of mixed order is not
   refused. The equation is §5's as written: `S` below `L`, and the canonical encoding of [`S`]B − [h]A
   equal to `R`, byte for byte, `R` not otherwise decoded. (The first version decoded `R` and compared
   points, which gives the same answer for every signature; it now compares bytes, as §5 says.)
2. **The receipt's member forms**, gateway §1.2a (§5.2, check 1: "each member this list reads is of the
   form gateway §1.2a gives it"), in another repository and not read. Taken: `receiptVersion` the string
   `"3"`, `kind` the string `"acquisition"`, `keyId` 32 and `signature` 128 lowercase hexadecimal
   characters, `source` and `authority` strings, `acquisition` an object, `argumentsCommitment` and
   `resultDigest` digests; `adapter`, `shape` and `endpoint` are held by check 3's comparison. The
   citation's `callIndex` and `sessionId` are of the gateway's forms too; one that is not (a `callIndex`
   that is not a non-negative integer, a `sessionId` that is not a string) is taken as
   `acquisition-sessions`, the check that reads them, and `callIndex` values are compared by value.

### Rules the text states

These were listed as gaps in the first version; the text decides each.

- **A receipt time with no instant** is `acquisition-stale`: §5.2, "`E.acquisition.observedAt` and
  `E.servedAt` MUST each have an instant no more than the source's `maxAge` seconds before `verifiedAt`
  and no more than 30 seconds after it; otherwise `acquisition-stale`."
- **A record without `inputs.facts` or `inputs.evidence`** differs: §11, finding 6, "the record's
  `inputs.facts` is not the facts document (§8.1), its `inputs.evidence` is not the
  evidence-availability document, ... each compared as JSON values."
- **A calculator's answer not of §7's form** is `calculation-invalid`: §7, "The value read MUST be an
  object whose member `calculation` is an object of exactly ..." and "That answer is held to the
  source, and any of these checks that fails is `calculation-invalid`".
- **A source parameter of the wrong type beside one with no value** is `parameter-invalid`: §3, "A value
  that is there and is not of type `T` fails the preparation, `parameter-invalid`."
- **A placeholder's extent**: §4.1, "A placeholder is `{{`, a parameter name, and the next `}}`".
- **A rule's fact targets** are every pointer of its claim forms over all clauses, and none may equal or
  prefix another: §8, "for a rule, every pointer of every claim form's `facts` ... over all clauses";
  §8.1, "No fact target of one source may equal another, or be a prefix of another by whole tokens".
- **The lists of `admits`** are arrays of classes, with no further form: §8.2, "`admits`, an object of
  `facts`, mapping fact targets to arrays of classes ... A target is admitted when its class is in its
  list".
- **A `selected-file` source's members**: §4.2, "`local-file` ... with no profile, no `maxAge` and no
  request; or `google-drive` ... with `profile`, `profileDigest`, `maxAge` and `arguments` as in §4.1",
  held in phase 4 by §11, "each of its sources against §4's members and its kind's, whichever its kind".
  This reader reads `operation` and the case, and answers `kind-unread` to the rest.

### The genuine choices, which the text now decides

These were the six points the text left this reader. The maintainer decided each, and the text now
says it (RFC 0018, Evidence): §11 for the report, the record's extraction and "but for case", §12 for
the bounds, §6.3 for `freshWithin` and requirement ids. This reader follows each sentence: its readings
agreed with the decision on five of the six, and on the start of a number literal it was changed
(choice 2).

1. **The report and exit representation.** §11 lists what a reading reports, not its JSON, and gives no
   exit statuses. Taken: the form and the statuses in the table above; `result` takes the manifest's
   words `reading` and `finding`, and `refusal`.
2. **The byte-bound scans and the nesting convention** (§12). Taken: an object or an array opens a level,
   so `{}` is at one level and a scalar at none, measured on bytes outside strings before a document is
   read and as a value's depth for a result; a number literal is a maximal run outside strings of digits,
   `+`, `-`, `.`, `e` and `E`, whatever it starts with (it first took a run that starts with `-` or a
   digit, and was changed to the text's), its exponent's magnitude the value of the digits after its
   first `e` or `E`, leading zeros ignored; an unwrapped string's bytes are the UTF-8 bytes of its value,
   its escapes read.
3. **The version-2 record's extraction** ("written as one line", the staging note). Taken: the bytes of
   `run.audit` as `run.json` writes them, which is one line. No version-2 record in the vectors carries a
   binding, so no binding's bytes depend on it.
4. **"`binding` but for case"** (§11). Taken: ASCII case only: a top-level member of the record, other
   than `binding`, whose name is `binding` once `A`–`Z` are lowercased, is refused.
5. **`freshWithin` whose `asOf` is not declared `timestamp`, or whose `maxAge` is not declared
   `integer`.** Taken: the rule is read and the condition is false. §6.3 makes the types part of the
   condition's truth ("`N`, of type `timestamp`, has an instant ... the value of `M`, of type
   `integer`"), and its sentence on a rule not of its form does not name a declared type. The probe in
   [`test/units.test.ts`](test/units.test.ts) holds it.
6. **Requirement ids in a claim form's `evidence`**, which §6.3 calls "requirement ids" without a form.
   Taken: non-empty strings, as a copy's `requirement` is (§6.2).

Two things this reader could not compare, because the protocol kept it from the Runner's manifest:

- the vectors' expected `targetsByClass`, `unsignedParameters` and `unsignedFreshness`, which the staging
  note says are the members of those names in the Runner's `verify-run` report. This reader computes
  them from §11; the unit test pins its values for `unsigned-parameters` as its own reading, for the
  maintainer to compare;
- whether a vector requires a binding, which the staging note gives as the Runner's `verifyRun.arguments`.
  This reader takes `requiresBinding` from this repository's manifest.

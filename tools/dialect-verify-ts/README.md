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
| the program could not run: an argument, a file that cannot be opened, a vector directory without its files | nothing on standard output | 3 |

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
Not read: the first reader or its test, the Runner's own README and manifest under
`conformance/dialect/vectors/`, the rest of RFC 0018, any other repository, and any Go or Python source.
The checkpoint witness statement, which §1 adopts by reference for the key rule and the signature
equation, was not on the list and was not read either.

## Where the text was not enough

Each point the text did not decide, and the reading taken. No vector decides any of them: every vector
is answered the same under either reading of each.

1. **The key rule.** §1 holds a key to the checkpoint witness statement's §5, which this reader did not
   read. Taken: a key whose 32 bytes are not a canonical encoding of a curve point (RFC 8032 §5.1.3), or
   whose point is of small order, is refused. The equation is the one §1 states: RFC 8032's check
   without the cofactor, `S` below `L`, `R` decoded canonically.
2. **The receipt's member forms.** §5.2's check 1 defers to gateway §1.2a, in another repository.
   Taken: `receiptVersion` the string `"3"`, `kind` the string `"acquisition"`, `keyId` 32 and
   `signature` 128 lowercase hexadecimal characters, `source` and `authority` strings, `acquisition` an
   object, `argumentsCommitment` and `resultDigest` digests; `adapter`, `shape` and `endpoint` are held
   only by check 3's comparison.
3. **Receipt members outside check 1's list.** Taken: an `observedAt` or `servedAt` that is not a
   timestamp with an instant is `acquisition-stale`; a `callIndex` that is not a non-negative integer,
   or a `sessionId` that is not a string, is `acquisition-sessions`; `callIndex` values are compared by
   value, so `-0` is `0`.
4. **The report's form.** §11 lists what a reading reports, not its JSON. Taken: the form in the table
   above; `result` takes the manifest's words `reading` and `finding`, and `refusal`.
5. **Exit statuses.** The text gives none. Taken: those in the table above.
6. **Levels of nesting** (§12). Taken: an object or an array opens a level, so `{}` is at one level and a
   scalar at none; measured on bytes outside strings before a document is read, and as a value's depth
   for a result.
7. **A number literal's characters and exponent, measured on bytes.** Taken: a literal is a run outside
   strings that starts with `-` or a digit and continues with digits, `+`, `-`, `.`, `e` and `E`; its
   exponent's magnitude is the value of the digits after its first `e` or `E`, leading zeros ignored.
8. **An unwrapped string's bytes** (§12, 200000). Taken: the UTF-8 bytes of the string's value, its
   escapes read.
9. **The record "written as one line"**, for an export of version 2 (the staging note). Taken: the bytes
   of `run.audit` as `run.json` writes them, which is one line. No version-2 record in the vectors
   carries a binding, so no binding's bytes depend on it.
10. **"`binding` but for case"** (§11). Taken: ASCII case only: a top-level member of the record, other
    than `binding`, whose name is `binding` once `A`–`Z` are lowercased, is refused.
11. **A record without `inputs.facts` or `inputs.evidence`.** §11 gives `cites` an absent form, the empty
    array, and these none. Taken: an absent one differs (`record-inputs-differ`). "Compared as JSON
    values" is taken as §6.3's JSON-equal.
12. **`freshWithin` whose `asOf` is not declared `timestamp`, or whose `maxAge` is not declared
    `integer`.** Taken: the condition is false. §6.3's list of what refuses a rule does not name it.
13. **A calculator's answer that is not of §7's form** (not an object whose `calculation` is an object
    of exactly its members). §7 names no finding for it. Taken: `calculation-invalid`.
14. **A source parameter with a value of the wrong type, beside another that has none.** Taken:
    `parameter-invalid`; an absent value skips the source, a present value of the wrong type fails the
    preparation whatever its other parameters hold.
15. **A `selected-file` source's members** (§4.2), held in phase 4 before `kind-unread`. Taken:
    `local-file` is exactly `name`, `kind`, `provider`, `read` and optionally `parameters`;
    `google-drive` adds `profile`, `profileDigest`, `maxAge` and `arguments` as in §4.1. This reader
    reads `operation` and the case, the kinds the vectors exercise, and answers `kind-unread` to the
    rest.
16. **Requirement ids in a claim form's `evidence`.** Taken: non-empty strings, as a copy's
    `requirement` is.
17. **A placeholder's extent** (§4.1). Taken: the leftmost `{{`, then the next `}}` after it; what lies
    between is the name, which must be an `integer` parameter of the scope.
18. **A rule's fact targets.** Taken: the set of pointers its claim forms write, over all clauses, so a
    pointer written by two clauses is one target; two pointers of which one is a prefix of the other by
    whole tokens are refused.
19. **The lists of `admits`.** Taken: any array of the three class names, duplicates and the empty list
    allowed; an empty list admits nothing.

Two things this reader could not compare, because the protocol kept it from the Runner's manifest:

- the vectors' expected `targetsByClass`, `unsignedParameters` and `unsignedFreshness`, which the staging
  note says are the members of those names in the Runner's `verify-run` report. This reader computes
  them from §11; the unit test pins its values for `unsigned-parameters` as its own reading, for the
  maintainer to compare;
- whether a vector requires a binding, which the staging note gives as the Runner's `verifyRun.arguments`.
  This reader takes `requiresBinding` from this repository's manifest.

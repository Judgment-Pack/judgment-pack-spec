# dialect-verify-ts: a second, independent preparation verifier

This is a *preparation verifier*, the conformance class that the companion document
[`spec/dialect.md`](../../spec/dialect.md) defines (its §14), written in TypeScript from that
document's text alone, so that [RFC 0018](../../rfcs/0018-dialect.md) can meet RFC 0000's evidence
bar of two independent readers agreeing on the vectors. The repository's first reader was not read
while this one was written; the files that were read are listed below.

Like the reader the companion document's §14 describes, it is a reader and not the specification. The vectors it reads are
[staged](../../conformance/dialect/README.md): in no corpus, and no conformance claim of the class is
available until a specification version publishes them (§14). Agreement between two readers shows
that they read the format alike, and no more; a reading never establishes anything §13 says a
preparation does not establish.

## Running it

Node 22.18 or later on `PATH`; no dependencies and no build step (Node strips the types).

```text
node src/main.ts <vector directory> [--require-binding]
node src/main.ts --dialect F --case F [--acquisitions F] --profiles F --preparation F [--binding F] [--record F] [--require-binding]
```

A vector directory is read as the [staging note](../../conformance/dialect/README.md) lists:
`mapping.json`, `case.json`, `sources.json` (`{}` when absent), `profiles.json`, and from `run.json`
the preparation `run.input.preparation` and the record (`run.auditBytes`, standard base64, or else
`run.audit`). A directory that holds `binding.json` is a dialect bound at import: its dialect is then
`unbound.json`, read with `binding.json` as its binding document (§4.4). With the second form,
`--binding` names the binding document of a dialect with an unbound source.

Whether a binding is required is the caller's to say: the vectors' answers are in
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
  `run.input.facts` and `run.input.evidence`; and, for a vector of a dialect bound at import, the bound
  dialect this reader makes to the vector's `mapping.json`. A vector this reader could not answer from the text would
  be listed there as a known disagreement, with its reason; there is none.
- [`test/units.test.ts`](test/units.test.ts) holds the forms the text fixes (§1, §9.5, §12) and this
  reader's answers to inputs no vector holds, each made from a vector by one change; some re-sign the
  receipts under a key generated in the test, to reach the checks after a receipt's. Those answers are
  this reader's readings of the text, not the vectors'. Under "the research contract", it builds
  hand-written research documents of every new form and refusal, signed under a key generated in the
  test, each with the answer the text gives.

The repository's Python suite runs both through `tests/test_dialect_ts.py`, and gives this reader
the first reader's hand-written research documents (`tests/test_dialect.py`), holding the two
readers' reports equal on each, with `--disable-wasm-trap-handler`: Node strips types with a
WebAssembly module, which cannot reserve its memory under an address-space limit (`ulimit -v`)
without that flag.

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

**The amendment of 2026-10-15.** RFC 0018's amendment of that date extended this reader and the first,
by one author who had read both: version 2's `operation` of the shapes `airbyte`, `mcp` and `http`, a
tool call under `mcp` and, under `http` and `airbyte`, any object held to the template rules and the
receipt's commitment, with `adapter-http`'s `query` held to string templates (§4.1); a receipt that
attests a page refused (§5.2); and a dialect of version 3 refused as `version-unread` (§11), its unbound source form
and binding document (§4.4) not read and no binding document taken. The tests in
[`test/units.test.ts`](test/units.test.ts) under "the shapes of an `operation`" hold each. That extension
is no part of this reader's independence: the agreement of the two readers on the tenth vector,
`http-shaped-source`, is one author's.

**Dialect version 3.** The staging of the Runner's eleventh and twelfth vectors, `version-3-bound` and
`unbound-bound-at-import`, extended this reader and the first to dialect version 3, by one author who
had read both, from the text: a document of version 3 is read as one of version 2, and its preparation
is of version 3, its `cites` ordered by `callIndex` as version 2's are (§9.1); an `operation` of the unbound form is read
with the binding document it is given (`--binding`), the bound dialect made of the two and read as every
dialect is, a binding document of another form, of another dialect's digest, or that does not name
exactly the unbound sources refused as `input-malformed`, and a profile bound of another shape or record
`profile-mismatch` (§4.4); a source of a kind of §4.3 held to the form its kind names and refused as
`kind-unread`; and, as RFC 0018's amendment that read version 3 decided, a version-3 document that names
`provider`, `facts` or `evidence`, or writes empty a member the Runner's encoding leaves out when empty,
refused as `input-malformed` (§2). After the review of round 7, a copy's two arrays are required in every
version (§6.2), a binding document of `null` is refused, the 64 retained responses of a research record are
counted before any form (§12), and a `research` source's acquisition is held to its own form (§§4.3, 5.2).
Nothing is `version-unread` now: this reader reads both versions the text defines. The
tests in [`test/units.test.ts`](test/units.test.ts) under "dialect version 3" hold each. That extension
is no part of this reader's independence: the two readers' agreement on the eleventh and twelfth vectors
is one author's.

**The research contract.** The pull request for issue #176 extended this reader and the first to
read `research` as RFC 0018's round-8 amendment defines it, by one author who had read both, from
the text (§§4.3, 4.4, 5.1, 5.2, 6.4, 9, 11, 12): the recipe's `fields` and `capabilities`, bound
directly or through a binding document (`webProfiles` among the assignment's members); each assigned
profile the trusted one of its id and digest, of class `generated`, declaring the capability it
serves and, when it declares a model, the source's, or `profile-mismatch`, then each retained
response's profile; the research record's typed answers and their citation indices; each retained
response checked under its own profile and over its own request, in order, then the record's own
receipt; a plain read's closed list of pointers; the reconciliation read, its guards, its evidence
and its last clause, and its combined value held to the nesting bound; `cites` in the order of
`sources` in a preparation with a `research` source, and the lineage's `receipts`; and the research
maxima of §12 in phase 3. `http`, `sql` and `web` are still held to their forms and answered
`kind-unread`. The tests in [`test/units.test.ts`](test/units.test.ts) under "the research contract"
hold each. No vector holds the kind; the two readers' agreement on its hand-written documents is one
author's.

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
- **A `selected-file` source's members**: §4.2, "`local-file` ... with no profile, no `maxAge` and
  no request; or `google-drive` ... with `profile`, `profileDigest`, `maxAge` and `arguments` as in
  §4.1", held in phase 4 by §11, "each of its sources against §4's members and its kind's, whichever
  its kind". This reader reads `operation` and the case, and answers `kind-unread` to the rest;
  since the amendment of 2026-10-15, `operation` of the shapes `airbyte`, `mcp` and `http`; since
  the eleventh and twelfth vectors, dialect version 3, whose kinds `http`, `sql` and `web` it holds
  to their forms and answers `kind-unread`; and since issue #176, `research`.

### Version 3: what the text leaves open, as the extension's author read it

No vector depends on it; the first reader takes the same, and RFC 0018's Evidence records it.

- **The forms of version 3's kinds** (§4.3), where the text names a member without its form:
  `http`'s `path`, "a template that yields a path", is taken as a string template; its `headers`,
  "the names of the headers", and a `sql` binding's `name` and `type`, as non-empty strings.
  `research`'s `evidence` was read so too; the research-contract amendment gave it that form.

### The research contract: what the text leaves open, as the extension's author read it

No vector holds the kind; the first reader takes the same readings, and RFC 0018's Evidence records
them.

- **A plain read's pointers** (§4.3, "Reading fields"): an `unwrap` pointer, which takes the value
  read from where it points, and a copy's `source` are held to the closed list as a `from` is, and
  so are never under `values`; `/fields/<name>/values/<index>/value` has no descendants, where
  `/fields/<name>/value` has; `<name>` is a declared field's, and `<index>` an array index's form
  (§1).
- **A reconciliation's conditions** (§6.4, "Pointers are ..."): a condition reads only a field entry
  of a declared field of the current source or of a source the read names, that entry's `status`, or
  its `value` or `values` and their descendants; the text closes the set of `from`s and lists these
  pointers without saying the list is closed for conditions.
- **The units of a maximum** (§12): a decimal string's 128 is counted in characters; every other
  string maximum in UTF-8 bytes, an answer's field name among them, declared or not.
- **A field declared twice** is `input-malformed` once forms are checked; before that, phase 3
  measures its answers by the first declaration of the name whose `type` is one of the six.
- **`unsignedParameters` of a research source** (§11): the source's own acquisition commits what its
  question commits only when the record has a receipt of its own, the one receipt over the source's
  request (§5.2); without one, a parameter a condition names is unsigned.
- **An acquired research source with no receipt at all**: it is listed in `unsignedFreshness` ("for
  each source acquired"), and its lineage's `receipts` is the empty array ("for an acquired
  `research` source"). A preparation "with" a `research` source, whose `cites` follow `sources`, is
  one whose dialect has one, skipped or not.
- **The record in the canon domain** (§5.2) is checked after the retained responses and before the
  record's own receipt; no input distinguishes that from after it, since a record outside the domain
  fails an earlier check first.

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

# Registry rows, format 1.1.0 (proposed)

Hand-written rows for registry format `1.1.0`, status `proposed`
([`spec/registry-1.1.0.md`](../../../spec/registry-1.1.0.md): assembly, the assembled index,
bounds, locks and their signatures). They are staged beside the text and released with it, or
not at all: no bundle carries them, the site serves none of them, and no conformance claim may cite
them until a `registry-v1.1.0` tag releases the text (its §13). The `status` of `codes.json` and of
`manifest.json` says `proposed`, as the text's does. Where a row and the text differ, the text
governs. The rows of format `1.0.0`, in [`../1.0.0/`](../1.0.0/), are unchanged.

Every input is synthetic: the ids, repositories, owners, projects and values are made up, under
`example.invalid`. Every signature is made with a published seed of RFC 8032 §7.1: TEST 1 is the
standard owner's key and a single registry's signer, TEST 2 the repository's, and TEST 3 a key no
expected set names. No other private key or seed exists here, so any reader can make every
signature again.

They are not recordings. Every expectation was written by hand from the text. Those of the first 154
rows were written before any reader of format `1.1.0` existed; the key identifiers and three rows
came later, with the text that says them (below).
[`tools/registry_1_1_0_reader.py`](../../../tools/registry_1_1_0_reader.py), a second reader written
from the text, gives every row its expected result
([`tests/test_registry_1_1_0_reader.py`](../../../tests/test_registry_1_1_0_reader.py)).
[`tools/registry_1_1_0_rows.py`](../../../tools/registry_1_1_0_rows.py) holds the rows as data and
writes this directory, `README.md` and `codes.json` aside. It only lays the data out and computes
what is mechanical: digests, key identifiers, resolved digests, source statements and signatures. An
edit to the rows is an edit to that file, run again.

## The files

- [`codes.json`](codes.json): the 53 codes of the text's §12, each an error, `active`, with its
  section. It equals the text's table, which governs where the two differ.
- [`manifest.json`](manifest.json): the rows.
- `kinds/`: kind declarations. `database.json` and `db-role.json` are format `1.0.0`'s, byte for
  byte.
- `federation/`: manifests. `sources/<repository>/`: the documents a source is given, by what they
  hold. `assembled/<assembly>/`: what an accepted assembly writes.
- `single/`: one single registry, format `1.0.0`'s `valid-two-environments`, and its resolved forms.
- `locks/`, `signatures/`, `emitters/`: locks with their lock signatures beside them under the
  default name (§7), source signatures, and an emitter manifest with the files it owns.
- `vectors/<row>/`: a row's own documents and its expected output.

## A row

A row has `id`, `section`, `operation`, `class` (one of the five classes of §15: `assembler`,
`index-checker`, `lock-writer`, `lock-checker`, `lock-signature-verifier`), `description`, its
inputs, and `expected`. Each row is complete in itself: every document it needs is named in it, and
nothing carries over from another row. A description that says `reading:` names a point where the
text does not state the expected result outright; the row holds the reading the text most directly
supports.

| `operation` | Inputs | Expected output, and how it is compared |
| --- | --- | --- |
| `assemble` | `federation`; `sources`, by source name, each a `commit` and `files`, from the path the manifest names to the row file holding its bytes (a path absent there is not given); `known`, `indexes` and `locks` | the report (§2.1), compared as JSON with every `message` removed, order kept. An accepted assembly's row also has `writes`: the assembled registry and the index, each its exact JCS bytes |
| `check-index` | those of `assemble`, and `index` | the report |
| `write-lock` | `registry` and `kinds`, or those of `assemble` with `sourceSignatures` and `signers`; `previous`, or `firstSerial`; `emitters` | the lock, its exact JCS bytes; or `{"refused": [codes]}`, compared by code alone |
| `check-lock` | `lock`, `registry`, `kinds`, `index`, `emitters`, `expect` | the report |
| `coverage` | `lock`, `expect` (with `environment`), and `resolved` or `file` | the report |
| `verify` | `lock`, `lockSignatures`, `index`, `sourceSignatures`, `signers`, `expect`, `record`, `floor`, and optionally `concurrent`, `writeFails`, `registry`, `kinds`, `resolved` | the report, and `expectedRecord` |

- `expect` is the expected inputs of §9: `registryId`, `requireIndex` and, for coverage,
  `environment`. A member left out is not given.
- `signers` is the expected signer set of §11: `key`, the expected key (for an assembly, the
  standard owner's), and `repositories`, the repository key map. Keys are 64 lowercase hexadecimal
  characters.
- `emitters` is a list of `{"manifest", "path", "files"}`, with `source` in an assembled row and
  `check`, the host check's exit code, for a writer. Each file is `{"path", "mode", "file"}`,
  `file` naming its bytes, with `source` too for coverage in an assembled lock.
- `record` is the verifier's record for the expected registry id before the verification: `null`
  for none, `{"serial", "digest"}` for one, `"unreadable"` for one that exists and cannot be read,
  and any other value for one that exists and is not of its form. `concurrent` is a record another
  process writes after step 1 reads it, which the compare and set then finds; `writeFails: true`
  says the record cannot be written. `expectedRecord` is the record once the verification ends.
- `schemaRefuses`, where present, names the row's documents that their closed schema in
  `schema/registry/1.1.0/` refuses. Every other document a row names is admitted by its schema.

## Readings

These hold wherever the rows meet them:

- A report's `registry` is the digest of the registry the operation validates by registry §7 (the
  assembled registry for an assembly or an index check, the given registry for a lock check or a
  verification given one), present once that validation passed its step 3, and absent otherwise,
  as in coverage.
- An expected input's diagnostic, and a record's, are located at the lock's root; a serial's at
  `/serial`; `LOCK-INDEX-REQUIRED` and `LOCK-INDEX-MISSING` at the lock's `/index`;
  `LOCK-REGISTRY-INVALID` at the registry's root; a lock signature that is missing at the lock's
  root, and a source signature that is missing at the lock's `sources` item.
- A signature document's diagnostic is at the member it names, `LOCK-SIG-DOCUMENT` and
  `LOCK-SIG-EXTRA` at its root. A document refused when read is not then checked against a key.
- A diagnostic of the assembled registry about an entry's value keeps document `value` and its
  pointer into the value, and `source` names the source that holds the entry.
- After `FED-KIND-NOT-STANDARD` or `FED-KIND-CONFLICT`, the assembled registry holds one pin per
  kind name, the earlier source's where two differ, and its validation is given the declarations
  its pins name.
- An index check whose second assembly finds an error reports that error's diagnostics and no
  `FED-INDEX-MISMATCH`.

## Added with the text

The text once left two points open that the rows could not settle, and says them now (its Status
lists the changes). The rows that came with them:

- `verify-source-signatures-told-apart`: two `LOCK-SIG-EXTRA` at one pointer, told apart by the
  location member `keyId` (§2.1).
- `verify-signature-cap-after-lock`: no document is beyond the count until step 3 accepts the lock
  (§11).
- `verify-signature-cap-last-given`, with `verify-signature-cap-unread`: the documents are counted
  in the order given, the lock signature first, so those beyond the count are the last given (§11).

## Checks

`tests/test_registry_1_1_0_rows.py` holds the rows to the parts of the text that need no reader:
the schemas are valid schemas and each row document is admitted or refused by its own as the row
says; `codes.json` equals the §12 table, and every code is used by a row and every row's code is
listed (or is one of format `1.0.0`); every class has rows; every digest, content digest, resolved
digest and source statement follows from its inputs; every written document is its JCS bytes; every
signature that should verify does, under the key the row's signer set names; every report is in
order, distinct, and `valid` exactly when it holds no error, and its every `keyId` is on a
signature document's diagnostic and names a key the row gives; and every `expectedRecord` follows
from a model of §11's Rollback. It does not assemble, check or verify: that is a reader's work.

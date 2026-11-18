# terraform-file vectors

The machine-readable form and the hand-written vectors of the terraform-file reading `1.0.0`,
status `proposed` (`spec/terraform-file.md`, whose design record is RFC 0038). They are proposed
with the text: until a terraform-file tag releases them they are not a conformance corpus, and no
claim may cite them (the companion's §12). They are packaged on the companion's own scoped tag: a
`terraform-file-v` tag's bundle carries them, with the text, this README, the checks that hold
them to the text and the second reader those checks run, and its release record pins every file
here and that reader (the companion's §10, VERSIONING.md).
No Core bundle carries them, and the site serves none of them, before a release or after it. The
`status` of `codes.json`, `formats.json` and `manifest.json` says `proposed`, as the text's does.

Every input is synthetic, written by hand to the shape that Terraform's documentation of its JSON
output format gives for its `format_version` (§4), with no Terraform run and no recorded output. The
projects, names and values are made up. They are not recordings: every expected result was written
from the companion text, and a reader is held to them, never the other way round. Where a file here
and the text differ, the text governs.

## Readers

`tools/terraform_file_reader.py` is a second reader of the file, written from the companion text
alone (its §§1 to 12, the registry companion's §10.1 and §10.2, RFC 8785 and RFC 6901), with no
other reader ported and no expected result read before it was written. It uses the standard library
only, reads bytes only, and runs no program. `tests/test_terraform_file_vectors.py` runs every
vector through it, and each must give its expected result exactly: a refusal's code and members, an
accepted read's record and value, the value's canonical bytes, and a batch's bytes. It gives every
one. It was written by a model from the drafting vendor: a same-vendor reader, not a cross-vendor
claim. It is a test reader: its memory grows with `maxBytes`, since it holds the parsed file, and it
is not for production files.

The same tests hold `codes.json` to the text's §9 table and `formats.json` to its §4 table, the
manifest to the files, and each expected result to its form: an acquisition record of its own
input, whose `sha256` and `bytes` are the input's; a value in id order with no JSON number and no
sensitive text; a refusal of a listed code; batch lines in canonical form. They hold the second
reader's verdict on each declaration, malformed or not, to the one its vectors expect. They read only
the text, the files here and the second reader, and the companion's bundle carries them, with the
second reader, and runs them. `tests/test_terraform_file_declarations.py` holds the first reader,
`tools/dialect_verify.py`, to the same verdicts: it holds a `terraform-file` source to its form and
reads no file, directly, as the members of §2, and as a source of a dialect document, where the
document's own number domain refuses `1.0` and `1e2` first (`spec/dialect.md` §1). It needs the
dialect's staged vectors, which no bundle carries, so it stays in the repository.

The reference runtime's reader was run over every vector as they were written. It reports each
expected result but for one member: its acquisition record's `formatTable` is `proposed-1`, its own
name for the first table, where §7 gives `1.0.0`, in each of the 70 accepted reads. The text
governs. The reference runtime reads no declaration document (it takes a source's members as
options), so the `declarations` group's malformed forms have no counterpart there. Two
independently written readers agreeing on every vector is the companion's stable bar (§12).

## The files

[`1.0.0/`](1.0.0/) holds:

- `codes.json`, the code list of §9: each code, its severity, its status (`active`), the step of §3
  that raises it, and when, as §9's table says it;
- `formats.json`, the accepted table of §4, with its release, `1.0.0`;
- `manifest.json`, one row per vector;
- `declarations/`, the source declarations the vectors name: §2's members, `document`, `select` and
  `maxBytes`, as a dialect source carries them, and nothing else;
- `vectors/<group>/`, each group's inputs and expected results.

A manifest row has `id`; `group`; `section`, the text's section or step the vector holds;
`operation`; `class`, `reader`; `formatTable`, the table release that added the row's format row,
`1.0.0` for every vector here; `description`; `declaration`; `input`, or `generate` for an input
not committed; `broken`, for a refused input, what in it is broken; and `expected`. Each vector has
exactly one expected result.

`operation` is `read`, a file whose whole length is read, so that `TF-SIZE` carries its sha256 and
size; `read-stream`, an input read as a stream, such as standard input, read to one byte past
`maxBytes` and no further; or `batch`, the batch of §8, for a reader that writes it.

An expected result is one of the forms below. A refusal's diagnostic also carries its code's
`message` (§3), whose wording is the reader's own, so no expected result holds one.

- `{"record": …, "value": …}`, an accepted read: the acquisition record of §7, with `sha256` the
  input's SHA-256 in lower-case hex, and the acquired value of §6;
- `{"refusal": {"code", "sha256", "bytes"}}`, a refusal of the reading, or of the batch with
  `FACTS-ID-LIMIT` or `FACTS-DOCUMENT-LIMIT`, with the input's SHA-256 and size;
- `{"refusal": {"code": "TF-SIZE", "stream": true}}`, a stream longer than `maxBytes`, with neither
  sha256 nor size;
- `{"declaration": "malformed"}`, a declaration not of §2's form, read with no file: its input,
  `vectors/declarations/not-json.txt`, is not JSON, so a reader that read it would refuse it;
- a `.expected.jsonl` file, a batch's exact bytes, one line per selected resource, empty when
  nothing is selected.

A value nested deeper than sixteen is written on one line, as its input is.

## Conventions

- Every sensitive value, and every sensitive member name, holds the word `secret`, and no expected
  result does. The provider-unmarked vector's password holds no such word: Terraform's marker is
  the only signal the reading has, so a value a provider did not mark is acquired, which that vector
  shows plainly (RFC 0038's Security section).
- A large input is not committed. Its row's `generate` names a
  `template` under `vectors/`, a `replace` text that occurs in it exactly once, and `with`: the
  input is the template's bytes with that text replaced by `repeat` written `times` times, between
  double quotes when `quoted` is true. A rule has these members and no other. Its expected result's
  `sha256` and `bytes` are those of the generated bytes.
- Every limit a vector reaches is reached with a small `maxBytes`, with a value that grows past
  sixteen times a small file, or, for the default `maxBytes` of 67108864 bytes and one byte more,
  with generated inputs. The default `max` of 1000 has no vector (§12): `max` is held only as a
  declaration gives it.
- While the table has one release, no vector is of a later table release than `1.0.0`, so none
  holds a reader to `TF-FORMAT` for a row its claimed table lacks (§12).
- Two inputs are white space by design, `vectors/json/trailing-whitespace.json` and
  `vectors/json/white-space-only.json`, and no checkout converts a line ending here
  (`.gitattributes`).

## The groups

| Group | Vectors | What they hold |
| --- | --- | --- |
| `formats` | 14 | every row of the table, and versions outside it (§3 step 3, §4) |
| `plans` | 10 | changes, actions (a repeated name among them), unknown values and plans with nothing to change (§3 step 4, §§5, 6) |
| `state` | 15 | the state's shape, its modules and resources, and the members it is not to have (§3 step 4) |
| `document` | 16 | plans not of their shape, and resources, changes and `after_unknown` not of their form (§3 step 4) |
| `sensitivity` | 19 | missing and malformed mirrors, and removal over the whole read section (§3 steps 5, 6) |
| `mirrors` | 8 | mirrors whose shape differs from the value (§3 step 6, §12) |
| `diagnostics` | 2 | a refusal carries no name read from the file (§3) |
| `json` | 17 | the strict JSON of §3 step 2: depth, BOM, surrogates, duplicates, trailing bytes |
| `size` | 9 | files and streams of `maxBytes` and one byte more, the default `maxBytes` among them (§3 step 1, §12) |
| `selection` | 17 | types, mode (a mode neither `managed` nor `data` among them), the address pattern and `max` (§5) |
| `numbers` | 9 | normal forms, the 64-character bound and the `1e63` growth (§6) |
| `value-limit` | 5 | the value bound `L` and the charge on `afterUnknown` pointers, one exactly at it (§6, §12) |
| `deposed` | 8 | deposed objects in a plan and a state, and keys not of their form (§3 step 4, §12) |
| `batch` | 10 | lines, the id bound, the facts bound, and refusals before any line (§8, §12) |
| `declarations` | 40 | §2's members held to their forms, integer literals among them (§§2, 5) |
| `order` | 7 | which step refuses first, and code-point order of ids (§3, §6) |

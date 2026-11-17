# terraform-file vectors

The machine-readable form and the hand-written vectors of the terraform-file reading `1.0.0`,
status `proposed` (`spec/terraform-file.md`, whose design record is RFC 0038). They are proposed
with the text: until a terraform-file tag releases them they are not a conformance corpus, and no
claim may cite them (the companion's §12). No Core bundle carries them, and the site does not serve
them. The `status` of `codes.json`, `formats.json` and `manifest.json` says `proposed`, as the
text's does.

Every input is synthetic, written by hand to the shape that Terraform's documentation of its JSON
output format gives for its `format_version` (§4), with no Terraform run and no recorded output. The
projects, names and values are made up. They are not recordings: every expected result was written
from the companion text, and a reader is held to them, never the other way round. Where a file here
and the text differ, the text governs.

## Readers

No reader of the file exists in this repository. `tests/test_terraform_file_vectors.py` holds
`codes.json` to the text's §9 table and `formats.json` to its §4 table, the manifest to the files,
and each expected result to its form: an acquisition record of its own input, whose `sha256` and
`bytes` are the input's; a value in id order with no JSON number and no sensitive text; a refusal of
a listed code; batch lines in canonical form. It reads each declaration with the first reader,
`tools/dialect_verify.py`, which holds a `terraform-file` source to its form and reads no file:
directly, as the members of §2, and as a source of a dialect document, where the document's own
number domain refuses `1.0` and `1e2` first (`spec/dialect.md` §1).

The reference runtime's reader was run over every vector as they were written. It reports each
expected result but for one member: its acquisition record's `formatTable` is `proposed-1`, its own
name for the first table, where §7 gives `1.0.0`, in each of the 67 accepted reads. The text
governs. The reference runtime reads no declaration document (it takes a source's members as
options), so the `declarations` group's malformed forms have no counterpart there. A second,
independently written reader is the companion's stable bar (§12).

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

An expected result is one of:

- `{"record": …, "value": …}`, an accepted read: the acquisition record of §7, with `sha256` the
  input's SHA-256 in lower-case hex, and the acquired value of §6;
- `{"refusal": {"code", "sha256", "bytes"}}`, a refusal of the reading, or of the batch with
  `FACTS-ID-LIMIT`, with the input's SHA-256 and size;
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
  double quotes when `quoted` is true. Its expected result's `sha256` and `bytes` are those of the
  generated bytes.
- Every limit a vector reaches is reached with a small `maxBytes`, or with a value that grows past
  sixteen times a small file.
- Two inputs are white space by design, `vectors/json/trailing-whitespace.json` and
  `vectors/json/white-space-only.json`, and no checkout converts a line ending here
  (`.gitattributes`).

## The groups

| Group | Vectors | What they hold |
| --- | --- | --- |
| `formats` | 14 | every row of the table, and versions outside it (§3 step 3, §4) |
| `plans` | 8 | changes, actions, unknown values and plans with nothing to change (§§5, 6) |
| `state` | 6 | the state's shape and the members it is not to have (§3 step 4) |
| `document` | 13 | plans not of their shape, changes and `after_unknown` not of their form (§3 step 4) |
| `sensitivity` | 18 | missing and malformed mirrors, and removal over the whole read section (§3 steps 5, 6) |
| `mirrors` | 8 | mirrors whose shape differs from the value (§3 step 6, §12) |
| `diagnostics` | 2 | a refusal carries no name read from the file (§3) |
| `json` | 17 | the strict JSON of §3 step 2: depth, BOM, surrogates, duplicates, trailing bytes |
| `size` | 7 | files and streams of `maxBytes` and one byte more (§3 step 1, §12) |
| `selection` | 16 | types, mode, the address pattern and `max` (§5) |
| `numbers` | 9 | normal forms, the 64-character bound and the `1e63` growth (§6) |
| `value-limit` | 4 | the value bound `L` and the charge on `afterUnknown` pointers (§6, §12) |
| `deposed` | 8 | deposed objects in a plan and a state, and keys not of their form (§3 step 4, §12) |
| `batch` | 8 | lines, the 256-byte id bound, and refusals before any line (§8, §12) |
| `declarations` | 39 | §2's members held to their forms, integer literals among them (§§2, 5) |
| `order` | 7 | which step refuses first, and code-point order of ids (§3, §6) |

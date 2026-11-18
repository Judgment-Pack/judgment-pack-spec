# Registry 1.1.0 second reader

`registry_1_1_0_reader.py` reads registry companion format `1.1.0`, status `proposed`
([`spec/registry-1.1.0.md`](../spec/registry-1.1.0.md)). It assembles, checks an index, writes,
checks and covers a lock, and verifies a lock with its signatures, and it gives each row under
[`conformance/registry/1.1.0/`](../conformance/registry/1.1.0/) its result.
[`tests/test_registry_1_1_0_reader.py`](../tests/test_registry_1_1_0_reader.py) runs every row
through it and requires the row's expected result exactly.

## How it was written

- **From the text.** It was written from `spec/registry-1.1.0.md`, with `spec/registry.md` for the
  parts of format `1.0.0` the text builds on (admission, canonical form, kind declarations, the
  schema and pattern subsets, validation, resolution and the emitter manifest's `owns`),
  `spec/checkpoint-witness.md` §§1 and 5 for the key identifier, the key rule and the equation, and
  RFC 8785, RFC 6901, RFC 3986 and RFC 8032.
- **What it did not read first.** Until it had run over every row once, its author did not read the
  rows' generator (`tools/registry_1_1_0_rows.py`), any row's expected output (reports, written
  locks and assembled documents, expected records), or the `reading:` notes of the rows'
  descriptions. It read the rows' manifest for its inputs, the schemas, the rows' README and the
  format `1.0.0` rows. It ports no other reader.
- **The 1.0.0 part** was first held to the 15 `validate` and `resolve` rows of format `1.0.0`, and
  agrees with each.
- **Who wrote it.** A model from the drafting vendor: a same-vendor reader, not a cross-vendor
  claim.

## The first run, and what changed after it

Over the 142 rows of its first run, 137 agreed. The five that did not were each a location the text
does not state, and each row's `reading:` names the more specific one, which the reader then took:
`LOCK-INDEX-MISMATCH` for an index without exactly one standard item at the index's `/sources`;
`LOCK-NOT-COVERED` for a resolved registry at the lock's `resolved` item for the expected
environment; and `LOCK-EXPECTED` for a repository the map misses, or the standard's repository the
map names, at the lock's `sources` item. When twelve more rows were added, its first run over the
154 gave 152: the two others locate `LOCK-INDEX-MISMATCH` for an index whose registry digest is
another registry's at the index's `/registry/digest`, and the reader took that too. Where the text
leaves a choice open, the code says which it took, marked `READING`.

Running it also found where the text was silent: §2.1's report had no member for the key identifier
§11 says it names, and §11 did not say when, or for which documents, the cap of the lock's `sources`
count plus one applies. The text now says both (its Status lists the changes), the rows carry
`keyId` and three rows more, and the reader gives all 157 rows their result.

## What it is not

It is a test reader. It holds each document's size bound before parsing and its depth bound while
parsing, but it matches patterns with Python's backtracking `re`, which registry §3.4 does not allow
on input a reader does not control, and its Ed25519 arithmetic is neither constant-time nor fast. It
does not import YAML (registry §9): a `.yaml` or `.yml` path raises `NotImplementedError`, and no row
names one. It uses the standard library only, reads only the bytes it is given, opens no network
connection and starts no program.

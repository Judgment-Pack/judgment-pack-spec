# Checkpoint witness vectors (staged)

This directory holds 54 vectors for the checkpoint witness statement, written for the
witness-statement reader class that the companion document
[`spec/checkpoint-witness.md`](../../spec/checkpoint-witness.md) defines. Its design record,
[RFC 0017](../../rfcs/0017-checkpoint-witness-statement.md), was accepted on 2026-10-12, and the
vectors are **staged** until the next `specVersion` opens. They are in no corpus.

This directory is where they wait — reviewed, held to the same checks as a corpus, and runnable by
hand — until a later `specVersion` opens and they move into a corpus, as the
[staged evaluation rows](../evaluation/staged/README.md) wait for theirs.

- **Not part of any corpus.** The companion document's §11 holds a witness-statement reader to the
  witness vectors published with the specification version its claim names. No version publishes
  these, so no claim may cite them, and no conformance claim of the reader class is available
  until one does. Nothing here changes Core `0.2.0-draft`, its schema, its four
  classes, or either of its corpora.
- **Not published with the specification, and in no release bundle.** The site's build skips this
  directory, as it skips the staged evaluation rows, and a test holds that nothing under it is
  served. [`.gitattributes`](../../.gitattributes) marks it `export-ignore`, so no `git archive`
  release bundle carries it, and `-text`, so no checkout converts a line ending and changes a
  vector's bytes. The directory is work in progress on `main`, reachable in the repository and
  nowhere else.
- **Not this repository's to change.** Each vector is the reference gateway's, byte for byte.

## Where they come from

[`vectors/`](vectors/) is the reference gateway's `corpus/witness/` at release `v0.11.0`, commit
`13349cafe33bb7618567e47ce7f6e1a4224231b0`: the same 54 files, the same names, the same bytes.
[`manifest.json`](manifest.json) records that source and, for each vector, its SHA-256. A change
to a vector is a change to the gateway's corpus first: the gateway's `SPEC.md` §7 calls its corpus
"hand-maintained normative data" and says "Changing a vector is a specification change".

The vectors were written against the gateway's `SPEC.md` §8, which RFC 0017 restates. Their
expected answers were written from that text, not computed by a reader, and three readers agree on
every one — the gateway's Go reader, its TypeScript verifier, and the reference runtime's
`audit verify --witness` — all three this project's (RFC 0017, Evidence).

The gateway's 25 recovery vectors, `corpus/witness-recovery/`, are not here. They hold a witness's
own storage — its log, marks and registrations — which no reader reads, and they stay the
gateway's.

## What a vector holds

Each vector is one JSON object: `name`, its file's name without `.json`; `family`; `note`, what it
holds and why; `trail`, the identity of the trail being verified; `keys`, the witness keys supplied,
in order, each 64 lowercase hexadecimal characters; `witness`, the statements files; `head`, a head
file, when there is one; and `expected`, the answer.

**The answer.** A refusal is `{"refused": <name>}`, compared by its name. A reading with a finding
is `{"ok": false, "findings": [...]}`, its findings compared as a set of names. A reading with none
is `{"ok": true, "findings": [], "reading", "headIndex", "highestIndex", "latestCheckpoint":
{"index", "sequence", "witnessedAt"}, "conflicts", "retired"}`, every member compared: `reading` is
`"current"` with a head and `"historical"` without; `headIndex` is the head's index, or `null`;
`highestIndex` is the chain's; and `conflicts` are the conflict statements' sequences, in index
order.

**A file.** A file is a string, its text exactly, or `{"parts": [{"text": …, "times": n}, …]}`,
the bytes of each part's text repeated `n` times, in order. The vectors of the byte and statement
bounds are stated so, rather than as files of up to 64 MiB. A runner writes the bytes out in full
before a reader reads them, so what is read is the file, never the description of it.

**The keys.** Every statement is signed under the gateway's published test seed, which signs
nothing real, and the vectors carry only public keys. The other keys a vector supplies are public
keys only: multiples of the base point, a key of mixed order, and encodings the key rule refuses.

| Family | Vectors | What they hold |
| --- | --- | --- |
| `valid` | 9 | readings with no finding, current and historical |
| `begins-late` | 3 | a chain without its index 0, with and without a head, and nothing supplied |
| `equivocation` | 2 | two statements at one index, in one file and as a head |
| `head` | 2 | a head more than one index past the statements, and one past that names another signature |
| `key` | 6 | the key rule: each refusal, and a key of mixed order accepted |
| `signature` | 8 | the equation, and the order in which a statement's checks apply |
| `trail` | 1 | a statement of another trail |
| `malformed` | 6 | statements not of the statement's form, and a head file of two statements |
| `chain` | 10 | each clause of the chain rule, broken once |
| `bound` | 7 | each bound at its limit and one past it, and a file of many one-byte lines |

## The manifest

[`manifest.json`](manifest.json) carries `"status": "staged"`, as the staged evaluation rows'
`cases.json` does, the RFC that proposed the vectors (`proposedBy`), their `source`, and one row
per vector: `id`, the vector's `name`; `path`; `family`;
`expectedResult`, which is `reading`, `findings` or `refused`; `expectedFindings`, the set of names,
on a `findings` row; `expectedRefusal`, the name, on a `refused` row; and `sha256`, the SHA-256 of
the file. The vectors' own `expected` members are the source of truth, and the row restates them so
the index can be read without opening each file.

## How they are checked

The specification repository owns no reader, so nothing here verifies a signature or reads a
chain. Its tests hold:

- every file under `vectors/` to the SHA-256 its row records, and every row to a file, so a vector
  added, removed or changed by a byte fails;
- each vector to the gateway's form: one JSON value, no member given twice, exactly the members
  above, `name` its file's name, and `expected` exactly one of the three answers, with only the
  refusal and finding names RFC 0017 §9 lists;
- each row to the vector it names: its id, family and expected answer; and
- this README's count and its table to the manifest.

To run a vector, give a reader the vector's `trail`, its `keys` in order, its `witness` files and
its `head` file when there is one, writing out any file given in parts first, and compare its
answer with `expected` as above.

## How they land

RFC 0017 was accepted on 2026-10-12, and its text landed then as the companion document. The
vectors wait for the next `specVersion`. When it opens, this directory leaves the site's and the
release bundle's exclusions, the vectors join a corpus as the vectors of the witness-statement
reader class, normative for that class and for nothing else, and Core §1.1's list of normative
artifacts gains them. Whether they take a `suiteVersion` of their own is still the RFC's first
unresolved question.

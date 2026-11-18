# terraform-file-v1.0.0

`terraform-file-v1.0.0` is the first release of the terraform-file companion
([`spec/terraform-file.md`](../spec/terraform-file.md)): reading `1.0.0`, at status `released`,
with the first format table, release `1.0.0`. It is tagged on the companion's own scoped route,
beside Core and independent of `specVersion`, as the Policy and registry companions' releases are
([VERSIONING.md](../VERSIONING.md)). Tagged on 2026-11-18.

- **Released, and not stable.** The text is normative for the reader class of its §12, and for
  nothing else. No stability promise is made before the first stable release (§10), and the bar for
  that is two independently written readers agreeing on every vector (§12), the second from a
  different vendor. The two readers below are both same-vendor, so they do not meet it.
- **Two readers.** The reference runtime (Go) reads the file and runs every vector it can express:
  its batch tool takes a source's members as flags, so the malformed declarations that no command
  line can write have no counterpart there. A second reader in this repository
  (`tools/terraform_file_reader.py`), written from the text alone, gives every vector's expected
  result. Both were written by models from the drafting vendor: a same-vendor pair, not a
  cross-vendor claim. Five forms the text first left open were settled from the reference runtime's
  behaviour after the second reader was written, and each now has its sentence and its vectors.
- **What it reads.** The JSON that `terraform show -json` writes for a saved plan (`format_version`
  `1.0`, `1.1` and `1.2`) or for state (`1.0`). Every value marked sensitive is removed before
  anything is selected. Eight refusal codes, each an error, refuse the whole read:
  `TF-SIZE`, `TF-JSON`, `TF-FORMAT`, `TF-DOCUMENT`, `TF-SENSITIVITY`, `TF-SELECT-BOUND`,
  `TF-NUMBER` and `TF-VALUE-LIMIT`. A reader that writes the batch of §8 also reports the registry
  companion's `FACTS-ID-LIMIT` and `FACTS-DOCUMENT-LIMIT`.
- **What it publishes.** The release's own bundle, `judgment-pack-terraform-file-1.0.0`, carries the
  text; the code list (`conformance/terraform-file/1.0.0/codes.json`, eight codes); the format
  table (`formats.json`, release `1.0.0`); the 206 hand-written, synthetic vectors, their
  declarations, manifest and README; the checks that hold the vectors to the text, with the second
  reader they run; and these notes with the release record. No Core bundle carries the code list,
  the table or the vectors, and the site serves none of them.
- **What the record pins.** [`terraform-file-v1.0.0.json`](terraform-file-v1.0.0.json) names the
  reading, the SHA-256 of the text and the vectors' README, the format table with its rows (all of
  them added by this first release), the code list with its codes, the id of every vector and the
  digest of every file under `conformance/terraform-file/1.0.0/`, and the second reader's digest.
  The release builder admits the tag only when the tagged tree gives exactly that record, and when
  the text, the code list, the table and the manifest all say `released`.
- **A claim** names the reader class, the exact release `terraform-file-v1.0.0`, the table release
  it implements, and its complete vectors (§12).
- **Later releases.** Each later tag is the next patch of the table: one that adds an accepted
  `format_version`, with its vectors, and one, an erratum, that corrects the text, the lists or the
  vectors and adds no row. No code, row or vector is dropped by a later release of reading `1.0.0`.

## Compatibility

- **Core is unchanged.** No Core text, schema, corpus or bundle changes, and every Core tag keeps
  its bytes. Dialect version 3, which is proposed, cites this text rather than carry it.
- **Readers.** This is the reading's first release; there is no earlier release to migrate from.

## Scope

Every input is synthetic, written by hand to the shape Terraform's documentation of its JSON output
gives for each `format_version`, with no Terraform run and no recorded output. A file this reading
accepts says nothing about whether the plan or state it describes is safe; the reading only turns
its bytes into facts a pack can judge.

The design record, [RFC 0038](../rfcs/0038-terraform-file-source.md), stays as its Acceptance
record says. No independent implementation evidence beyond the two same-vendor readers is claimed.

# Registry rows (staged, proposed)

Hand-written rows for the registry format `1.0.0`, status `proposed`
([`spec/registry.md`](../../spec/registry.md), the companion whose design records,
[RFC 0034](../../rfcs/0034-registry-profile.md) to [RFC 0037](../../rfcs/0037-generated-facts-contracts.md),
are accepted). They are staged: the companion is published and bundled, and the rows are not. They
are not a conformance corpus: no bundle carries them, the site does not serve them, and no claim may
cite them. Every input is synthetic: the ids, owners, projects and values are made up, under
`example.invalid`.

They are not recordings. Every expectation was written by hand from the companion text, and a
reader is held to them, never the other way round. The reference runtime (Go) is the one reader
that has been run against them; no second, independently written reader exists in this repository
yet. One row differs from what the reference runtime reports today, and the companion text governs:
`kind-declarations` expects the `kind` member on a kind declaration's member diagnostic that the
runtime reports without it (§7.3).

Core's corpora are unchanged. Nothing here is named by `conformance/manifest.json` or
`conformance/evaluation/manifest.json`, and nothing here is a schema file.

## The files

Each format version has its own directory. [`1.0.0/`](1.0.0/) holds:

- [`codes.json`](1.0.0/codes.json), the machine-readable diagnostic code list: each code, its
  severity, its status (`active` or `deprecated`) and the section that defines it. It equals the
  companion's §12 table, which governs where the two differ.
- [`manifest.json`](1.0.0/manifest.json), the rows.
- `kinds/`, kind declarations shared by several rows, and `vectors/<row>/`, each row's own
  documents and its expected output. A kind declaration a row names under its own directory belongs
  to that row alone.

## A row

A row names an operation, the conformance class it binds (§15), its inputs and its expected output:

| `operation` | Inputs | Expected output, and how it is compared |
| --- | --- | --- |
| `validate` | `registry`, `kinds` | a validation report (§7.4). Compared as JSON, with every diagnostic's `message` removed, the order of `diagnostics` kept. |
| `resolve` | `registry`, `kinds`, `environment` | the resolved document (§8), as its exact RFC 8785 bytes, with no final line feed. A reader whose command line ends its output with one line feed compares the output with that one line feed removed. |
| `facts` | `registry`, `kinds`, `kind`, `environment` | the batch (§10.2), byte for byte: one line per entry, each ended by a line feed. |
| `contract` | `registry`, `kinds`, `kind` | the generated facts contract (§10.4), as its exact RFC 8785 bytes, compared as for `resolve`. |
| `check` | `contract`, `pack` | the pack check report (§10.5). Compared as JSON. |

A row whose `class` is `null` binds no conformance class: the `check` rows are informative, since
the pack check is outside every class of this version (§15).

`facts`, `contract` and `check` inputs are valid: `facts-contracts-valid` holds the report of the
registry the contract rows read, and the `facts` rows read the registry `valid-two-environments`
holds.

## Checks

`tests/test_registry_companion.py` holds the rows to the parts of the companion that need no reader:
every input is I-JSON within its bounds; every pin's digest is the SHA-256 of its declaration's
RFC 8785 bytes, and every `kindDocument` that of the declaration's bytes as supplied; every report's
registry digest, resolved document and facts line follows from its inputs by §§2.3, 8 and 10.1;
every report is in §7.4's order, names only codes of `codes.json` with their severities, and holds
no reference, pattern or other string value from its inputs (§7.4); no facts line holds a secret
reference; every contract is in
canonical order; and `codes.json` equals the companion's table. It does not validate a registry: that
is a reader's work, and the second reader that would hold the rows to the text from this repository
does not exist yet (§14).

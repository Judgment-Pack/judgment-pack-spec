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
yet. Two rows differ from what the reference runtime reports today, and the companion text governs:
`kind-declarations` expects the `kind` member on a kind declaration's member diagnostic that the
runtime reports without it (§7.3); and `pattern-bounds` expects `(ab|ac){1000}` refused at 5 000 as
written, which the runtime `v0.47.0` admits because it counts size on its engine's factored parse
(§3.4, §17).

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
| `manifest` | `manifest` | the emitter host's refusals of the manifest (§11.1), as `{"refusals": [{"code", "pointer"}]}`: each refusal's code and its pointer into the manifest. Compared as a set; the file lists them by pointer in code-point order. |
| `response` | `manifest`, `request`, `response` | the emitter host's refusals of a response (§11.3) that an emitter run under `manifest` wrote to answer `request`, the request's exact bytes, as for `manifest`. |
| `request` | `manifest`, `registry`, `kinds` | the request (§11.2) the emitter host writes for a manifest whose `environments` is `"all"`, with no options, as its exact RFC 8785 bytes, compared as for `resolve`. |
| `references` | `manifest`, `registry`, `kinds`, `response` | the harness's references check (§11.5) of the response's files against the request the host forms, as `{"references": [{"entry", "file", "pointer"}]}`, with `environment` too for `"each"`. Compared as a set; the file lists them by file, entry and pointer in code-point order. |
| `layout` | `vector`, a vector directory | how the harness reads the vector's layout (§11.5): `{"files": [...]}`, the paths its `expected/` gives, or `{"refused": true}` when the layout refuses the run. Compared as JSON. |

A row whose `class` is `null` binds no conformance class: the `check` rows are informative, since
the pack check is outside every class of this version (§15).

The `manifest`, `response` and `request` rows bind the emitter host (§11), and the `references` and
`layout` rows the emitter harness. A refusal's location is its code, the document `manifest` or
`response` (§7.3) and the pointer; a host reports other members, and the rows compare only these. A
host that reports the first refusal alone, or stops at it, does not meet them. A `references` row
stands for check 5 on a vector whose emitter wrote that response; a `layout` row compares the layout
alone, not the run that follows it. The rows `request-reads` and `request-unread-kind` differ only
in the registry's digest, which is what check 4 restores. These rows were run against the reference
runtime's host and harness (`v0.48.0`) and agree with them.

`facts`, `contract` and `check` inputs are valid: `facts-contracts-valid` holds the report of the
registry the contract rows read, and the `facts` rows read the registry `valid-two-environments`
holds.

## Checks

`tests/test_registry_companion.py` holds the rows to the parts of the companion that need no reader:
every input is I-JSON within its bounds; every pin's digest is the SHA-256 of its declaration's RFC
8785 bytes, and every `kindDocument` that of the declaration's bytes as supplied; every report's
registry digest, resolved document and facts line follows from its inputs by §§2.3, 8 and 10.1;
every report is in §7.4's order, names only codes of `codes.json` with their severities, and holds
no reference, pattern or other string value from its inputs (§7.4); no facts line holds a secret
reference; every contract is in canonical order; every host refusal follows from its manifest and
response by a model of §11.1's owns globs and §11.3's paths, members and codes; every request
follows from its inputs by §11.2, and `request-reads` and `request-unread-kind` are equal once their
digests are restored; every `references` row follows from a model of check 5, and every `layout` row
from a model of the layout; and `codes.json` equals the companion's table. It does not validate a
registry: that is a reader's work, and the second reader that would hold the rows to the text from
this repository does not exist yet (§14).

# Record-shape catalog

The specification byte-pins its releases, but the record formats it defines also need a guard on
their *shapes* between releases. This directory holds that guard:

- [`record-shapes.json`](record-shapes.json), generated: every JSON Schema the specification
  defines, in a normalized form, with its SHA-256 digest and an inventory by family;
- [`changes/`](changes/), written by hand or by the tool: one change record for every digest that
  appears, changes or disappears; and
- [`format-status.json`](format-status.json), maintained by hand: per family, the version the draft
  text writes, the last accepted compatibility baseline and the last released version.

[`tools/record_shapes.py`](../tools/record_shapes.py) generates the catalog and checks all three.
The check is the `record-shapes` step of `dev.json`, which every jpdev.json rule names, so it runs
on every pull request and on every push to `main`.

The catalog fingerprints shapes; it does not establish that a document is valid, that two
implementations agree on meaning, or that any record is true or authorized.

## What is catalogued

The inventory is derived from the tree; no schema is listed by hand. The tool finds every file named
`*.schema.json` outside dot directories and `node_modules`. A schema is in scope when its `$id` is
under `https://judgmentpack.org/schema/`, the specification's published schema namespace. Anything
else, such as an RFC's staged proposal under a `urn:` identifier, is listed under `outOfScope` and is
not fingerprinted.

To stop a mistyped `$id` from dropping a shape silently, the tool refuses a tree in which:

- a `*.schema.json` file under `schema/` or `conformance/` has an `$id` outside the namespace;
- a file under `schema/` is not a `*.schema.json` file; or
- two files have the same `$id` but different normalized forms.

The family and version come from the `$id`:

| `$id` after the namespace | Family | Version |
|---|---|---|
| `<specVersion>/<path>/<name>[-<N>].schema.json` | `<path>/<name>`, with a trailing model number `-<N>` dropped | the `specVersion` |
| `<family>/<formatVersion>/<member>.schema.json` | `<family>` | the `formatVersion` |

For example, `0.3.0/workflow-1.schema.json` is family `workflow` at `0.3.0`, and
`policy/1.0.0/common.schema.json` is family `policy` at `1.0.0`. A new schema file therefore joins
its family's inventory, or starts a new family, the next time the catalog is generated.

## Normalization

`jps-record-shape-normalization/1`, stated in the catalog's `normalization` member:

1. Decode the file's bytes as UTF-8. A byte order mark is refused.
2. Parse exactly one JSON value (RFC 8259). The tool refuses an object that repeats a member
   name, a number that is not an integer, an integer outside -(2^53-1) to 2^53-1, a number written
   with a fraction or an exponent, and a string with an unpaired surrogate.
3. Serialize the value as RFC 8785 (JCS) does:
   - object members sorted by the UTF-16 code units of their names;
   - no whitespace between tokens;
   - in strings, only the quotation mark, the reverse solidus and U+0000-U+001F escaped
     (`\b \t \n \f \r`, otherwise `\u00xx` in lowercase hexadecimal), and every other
     character written as itself;
   - integers in shortest decimal form;
   - `true`, `false` and `null` as themselves.
4. Encode the result as UTF-8, with no trailing newline.

The digest is SHA-256 over those bytes, written `sha256:<64 lowercase hexadecimal digits>`.
Because every number is an integer, the form needs no floating-point formatting. A conforming JCS
library gives the same bytes for every schema the catalog admits.

## The catalog format

`record-shapes.json` is `judgment-pack-record-shapes/1`:

```json
{
  "format": "judgment-pack-record-shapes/1",
  "namespace": "https://judgmentpack.org/schema/",
  "normalization": "jps-record-shape-normalization/1: ...",
  "families": { "<family>": ["<path>", "..."] },
  "schemas": [
    {
      "path": "schema/workflow-1.schema.json",
      "family": "workflow",
      "id": "https://judgmentpack.org/schema/0.3.0/workflow-1.schema.json",
      "version": "0.3.0",
      "sha256": "sha256:...",
      "normalized": "{...}"
    }
  ],
  "outOfScope": [{ "path": "rfcs/...", "id": "urn:..." }]
}
```

`families` and `schemas` are sorted by name and by path. The file is written with two-space
indentation and a final newline, so the generator writes the same bytes from the same shapes. Run
`python3 tools/record_shapes.py generate` after changing a schema. The check fails while the
committed catalog differs from the generated one.

## Change records

The change records replay the history of every catalogued path. They are files in `changes/` named
`NNNN-<slug>.json`, where each four-digit number is used once. Each file has exactly these members:

```json
{
  "reason": "Why the shape changed, with its issue or RFC",
  "changes": [
    { "path": "schema/workflow-1.schema.json", "family": "workflow",
      "from": "sha256:<old>", "to": "sha256:<new>" }
  ]
}
```

`from` is `null` for a schema that appears, and `to` is `null` for one that is removed. The check
applies the records in number order and fails when:

- a record's `from` is not the digest the earlier records end at for that path (a wrong old digest);
- the records end at a digest other than the catalog's for a path (a changed schema without a
  record, or a record with a wrong new digest);
- a catalogued path has no record, or a recorded path was removed without one.

[`0000-catalog-introduced.json`](changes/0000-catalog-introduced.json) records every shape as it was
when the catalog began.

To record a change, edit the schema, run `generate`, then run
`python3 tools/record_shapes.py record --slug <slug> --reason "<reason>"`. That command writes the
next record for every path whose digest differs from the replayed records, naming the family and
both digests. The reason is the author's.

## Format status

`format-status.json` is `judgment-pack-format-status/1`. It holds one record per catalogued family,
and no others:

```json
{
  "format": "judgment-pack-format-status/1",
  "families": {
    "judgment-pack-core": { "draftVersion": "0.3.0", "baseline": "v0.3.0", "lastReleased": "v0.3.0" }
  }
}
```

The check compares each record with what the tree and [`releases/`](../releases/) give:

- **`draftVersion`**: the highest version among the family's catalogued schemas, which is the
  version the draft text on `main` writes for that family. Semantic versions are ordered by SemVer
  precedence, and bare format numbers numerically.
- **`lastReleased`**: the tag of the latest release that includes the family, pre-releases
  included, or `null`.
- **`baseline`**: the tag of the latest including release that is not a candidate, or `null`.

A release is a notes file `releases/<tag>.md`. The notes land in the commit the tag is cut from, so a
release counts from that commit onward. A release includes a family when:

- for a Core tag `v<version>`, one of the family's schemas has an `$id` under
  `<namespace><specVersion>/`, where `specVersion` comes from the release's mapping file
  `releases/<tag>.json` when that file exists and is otherwise `<version>`; or
- a `releases/*.json` data file whose `tag` or `distribution` is the release names one of the
  family's schemas, by path in `schema` or by path or `$id` in the values of `schemas`.

A candidate is a release whose version carries VERSIONING.md's `-rc.N` or `-alpha.N` distribution
suffix, or a Core distribution whose tag is not its `specVersion`. A candidate counts for
`lastReleased` but is never a `baseline`. A Policy companion release (`policy-v<releaseVersion>`)
freezes its format on first publication, so it is a baseline.

When a pull request prepares a release, or moves a family's draft version, it updates this file in
the same change. The check's failure message gives the derived record.

## Comparing an implementation's catalog

An implementation that reads or writes one of these families can show which shapes it carries.
It builds its own catalog in the same format from the schema bytes it actually validates against,
using the same normalization. An implementation's own catalog needs `id`, `family`, `version` and
`sha256` for each schema. Its `path` is the implementation's own, and `normalized` is optional.

It then compares that catalog with this one at the exact release tag it claims, as follows:

1. For each `id` the implementation carries, find the entry with the same `id` in this catalog.
2. A missing `id`, or the same `id` with a different `sha256`, is a **conformance finding**. The
   implementation validates against a shape this release does not define. The finding names the
   family, the `id`, the claimed release tag and both digests.
3. A difference in `family` or `version` for the same `id` is also a finding: the two derivations
   disagree.
4. A family in this catalog that the implementation does not carry is not a finding by itself. A
   conformance claim says which families it covers.

The comparison establishes byte-level agreement on shapes only. It does not establish that the
implementation applies them correctly, and a matching digest is not a conformance claim. Each
implementation adopts the comparison in its own repository.

# The terraform-file reading

## Status

This document is a companion document of the Judgment Pack specification. It defines the reading
of a Terraform plan or state, as `terraform show -json` writes it: the checks a reader holds the
file's bytes to, the removal of every value marked sensitive, the selection of resources, the value
acquired and its acquisition record, and the batch a reference runtime may write from that value.

This text is the terraform-file reading `1.0.0`, status `proposed`. The version is this document's
own: it is neither a Core `specVersion` nor a dialect version, and no pack declares it. The
companion is released on its own scoped tag, `terraform-file-v<major>.<minor>.<patch>`, beside Core
and independent of `specVersion`; its first release is `terraform-file-v1.0.0` (§10). Until a tag
releases this text, it is normative for nothing, and no conformance claim may cite it. Once a tag
releases it, it is normative for the conformance class of §12, and for nothing else. Publication
beside a Core release, on the site or in a Core bundle, releases nothing.

Its design record is [RFC 0038](../rfcs/0038-terraform-file-source.md), accepted on 2026-11-16,
which is informative. The readings this text settles that RFC 0038 left open, and why, are recorded
in the amendments of 2026-11-17 to the dialect's design record,
[RFC 0018](../rfcs/0018-dialect.md). The maintainer accepted RFC 0038 on one review round by a model
from the drafting vendor, with the different-vendor review of the interim review regime waived, as
its Acceptance section says. That is a same-vendor review, not a cross-vendor claim. Where this text
and the record differ, this text governs; §13 lists what is open.

The dialect names the kind whose file this text reads: a `terraform-file` source of dialect version
3, which is proposed, declares its file by the members of §2 ([`dialect.md`](dialect.md) §4.5).
Dialect version 3 and later Core releases cite this text rather than carry it. Core is unchanged by
this document, and so is every form of the dialect.

Version `1.0.0` is proposed. Its first release makes it `released`, and not yet stable:

- **Its vectors are not written yet.** The machine-readable code list and format table, and the
  hand-written vectors, are to be under `conformance/terraform-file/1.0.0/` (§§11, 12). Until a
  release publishes them they are not a conformance corpus, and no claim may cite them.
- **One reader exists.** The reference runtime reads the file (`v0.48.0`), and where this text
  settles what RFC 0038 left open, it says what that reader does, except for deposed objects (§3,
  step 4), which that reader does not yet carry. No second, independently written reader exists.
  The stable bar is two readers agreeing on every vector (§12).

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT** and **MAY** have their
BCP 14 meanings only in capitals.

## 1. Terms

- A **declaration** (§2) says which output of `terraform show -json` a file is, which of its
  resources to select, and the largest file read. A `terraform-file` source of the dialect is one
  ([`dialect.md`](dialect.md) §4.5); a tool may take one by its own options, as the reference
  runtime's batch does (§8).
- A **reader** reads a file under a declaration by the steps of §3, and gives either the acquired
  value (§6) with its acquisition record (§7), or a refusal with one code of §9.
- An **integer** of a declaration written in JSON is an integer as the dialect defines one
  ([`dialect.md`](dialect.md) §1): its literal has no fraction and no exponent, so `1.0` and `1e2`
  are not integers.
- A **pointer** is an RFC 6901 JSON Pointer. A value's **canonical form** is its RFC 8785 form.
- **Code-point order** compares two strings by their Unicode code points, first difference first.

## 2. The declaration

A declaration has exactly `document` (`plan` or `state`: which output of `terraform show -json` the
file is), `select` (§5) and `maxBytes` (optional, an integer from 1 to 268435456, default
67108864). It names no path: the caller supplies the file, and binds its path at evaluation time.

A declaration not of this form, `actions` on a `state` and a malformed `select` among them (§5), is
malformed, and no file is read under it. What holds the declaration refuses it:
[`dialect.md`](dialect.md) §4.5 says how a dialect document that holds one is refused.

## 3. Reading the file

A reader takes these steps in order. The first failure refuses the acquisition with its code (§9),
and later steps do not run. A diagnostic carries its code, the file's sha256 and its size, and
nothing else: no value, member name, pointer or position. The one exception is a stream's `TF-SIZE`
(step 1), which carries neither the sha256 nor the size.

1. The sha256 of the whole file and its length are recorded. A file longer than `maxBytes` is
   `TF-SIZE`, unparsed. An input read as a stream, such as standard input, is read to at most
   `maxBytes` and one byte more: a longer stream is `TF-SIZE`, unparsed, and its diagnostic carries
   the code and a fixed reading that the input was a stream, with no sha256 and no size, since its
   whole length is never read. A stream within `maxBytes` has its sha256 and length recorded as a
   file's are.
2. The bytes are UTF-8 with no byte-order mark and no lone surrogate escape, one JSON value with only
   white space after it, nested at most 128 deep (the top-level value at depth 1), with no duplicate
   member name; otherwise `TF-JSON`. Numbers are kept as their decimal text.
3. The top-level value is an object whose `format_version` is a string in the accepted table for
   `document` (§4); otherwise `TF-FORMAT`.
4. A `plan` has `planned_values`, an object, and `resource_changes`, when present, an array (absent
   reads as empty). A `state` has neither `planned_values` nor `resource_changes`, and `values`, when
   present, is an object (absent reads as no resources). Otherwise `TF-DOCUMENT`. A resource of the
   read section (step 5) that is a deposed object, one an apply replaced but has not yet destroyed,
   has a **deposed key**, `deposed` in a `plan` and `deposed_key` in a `state`, which is a
   non-empty string. A resource's **id** is its `address`, or, with a deposed key, its `address`, a
   space, `deposed`, a space and the key. A deposed key of another type, an empty one, or two
   resources of the read section with one id, is `TF-DOCUMENT`. In a `plan`, each item of
   `resource_changes` is an object whose `change` is an object, with `actions` an array of
   strings; any other item is `TF-DOCUMENT`. A resource change's
   `change.after_unknown`, when present, has a mirror's form: `true`, `false`, or an object or
   array of mirrors. Any other `after_unknown`, null included, is `TF-DOCUMENT`.
5. The read section is `resource_changes` for a `plan`, and every resource under
   `values.root_module` and its `child_modules`, recursively, for a `state`. Every resource in it,
   selected or not, carries its sensitivity mirror (`change.before_sensitive` and
   `change.after_sensitive`, or `sensitive_values`): `true`, `false`, or an object or array of
   mirrors, Terraform writing the value's shape (step 6 reads any other). A missing mirror, or one
   with a string, number or null at any position, is `TF-SENSITIVITY`.
6. In each value of the read section, every position whose mirror is `true` is removed with all it
   holds: an object member is removed; an array element is never removed alone, and the array that
   holds it is removed instead, up to the nearest object member. A mirror position absent from the
   value is ignored. Nothing replaces a removed value. `removedSensitive` counts the object members
   removed, and `after_unknown` pointers at or below a removed position are dropped. Terraform
   leaves a value unknown at plan time out of `after`, so `after_sensitive` is read along
   `after_unknown` as well: a pointer that ends at, or passes through, a position that
   `after_sensitive` marks `true` and `after` lacks is cut at that position, so no member name below
   it is carried. The pointers cut at one position are one pointer, and none when `after_unknown`
   marks nothing `true` at or below it. Mirror and
   value positions are matched as RFC 6901 tokens are, whatever their shapes: a mirror member names
   the value's member of that name, or, over an array, the element its name indexes (`0`, or a
   digit 1 to 9 and further digits, less than the array's length), and any other name names
   nothing; a mirror array's element `k` names an array's element `k`, or an object's member named
   `k` in decimal. A mirror object or array that marks any position `true`, at any depth, over a
   string, number, boolean or null, removes that value; an empty mirror object or array removes
   nothing.
7. Selection (§5), then the acquired value (§6).

A reader never reads `configuration`, `variables`, `relevant_attributes`, `checks`, `prior_state`,
`planned_values` (beyond step 4), `output_changes` or `outputs`.

## 4. Accepted formats

This text keeps a table of accepted `format_version` values per `document`, with its own release
number; each accepted `format_version` of each `document` is backed by its own set of vectors,
written by hand to the shape that Terraform's documentation of its JSON output format gives for
that version, with no Terraform run and no recorded output. A version not in a reader's claimed
table, including a newer minor of a listed major, is `TF-FORMAT`. The table grows by a patch release
and never shrinks within a dialect version. The first table (RFC 0038, Unresolved question 2,
resolved) is the one the reference runtime's reader holds as `proposed-1`:

| `document` | Accepted `format_version` |
| --- | --- |
| `plan` | `1.0`, `1.1` and `1.2` |
| `state` | `1.0` |

The table's release number is a semantic version, and each newly accepted row is a patch release.
The first table's release is `1.0.0`, which the acquisition record's `formatTable` carries (§7).

## 5. Selection

`select` has `types`, a non-empty array of at most 64 distinct resource type names; `mode`,
`managed` (default) or `data`; `address`, optional, a pattern of at most 512 characters that
matches the whole address, in which `*` matches any run of characters other than `.`, `[` and `]`
and every other character matches itself; `actions`, optional and `plan` only, of `create`,
`update`, `delete`, `read` and `no-op`, keeping changes whose `change.actions` include one; and
`max`, an integer from 1 to 10000 (default 1000), past which the acquisition is `TF-SELECT-BOUND`.
`actions` on a `state`, or a malformed `select`, makes the declaration malformed (§2).
Child-module resources are included with their full address; selecting nothing gives an empty
array.

## 6. The acquired value

The acquired value is an array sorted by id (§3, step 4) in code-point order, one object per
selected resource: for a `state`, `{"address", "type", "name", "mode", "providerName", "index"?,
"deposed"?, "values"}`, with `deposed` the deposed key, present only for a deposed object; for a
`plan`, the same with `actions`, `before`, `after` and `afterUnknown` (the sorted pointers, in
`after`, of values known only after apply) in place of `values`. Numbers become decimal strings in
the registry companion's normal form ([`spec/registry.md`](registry.md) §10.1), with `0` for every
zero; one whose normal form would be longer than 64 characters is `TF-NUMBER`. The value is then
bounded by `L`, the lesser of 268435456 and sixteen times the file's length in bytes. It is
`TF-VALUE-LIMIT`, after `TF-SELECT-BOUND` and `TF-NUMBER`, when its canonical form (RFC 8785) is
longer than `L` bytes, or when the `afterUnknown` pointers of one selected `plan` resource, each
charged the length in bytes of its RFC 6901 form and eight bytes more, total more than `L` less the
bytes of the canonical form that come before that resource's object (the array's opening `[`, the
objects of the resources before it, and the comma after each of them); so a reader can refuse
before it holds the value or the pointers. Numbers in normal form grow at most about 13.4 times (an
array of `1e63`) and strings do not grow, so pointers that repeat a long member name are what reach
the multiple.

## 7. The acquisition record

The acquisition record is `{"kind": "terraform-file", "document", "formatVersion", "formatTable",
"sha256", "bytes", "removedSensitive", "selected"}`, with no path. Its `formatTable` is the release
of the accepted table the reader read the file by (§4): `1.0.0` for the first table.

## 8. The batch

A reference runtime may also write the acquired value as an evaluation batch, one line per selected
resource with the resource's id (§3, step 4) and facts `{"terraform": {"document", "formatVersion",
"sha256"}, "resource": …}`; that batch is a product format, not a dialect member. Each line's id is
1 to 256 bytes of UTF-8, the bound the reference runtime's batch evaluation holds an item's id to. A
selected resource whose id is outside it refuses the whole run, before any line is written, with
`FACTS-ID-LIMIT`, the registry companion's code of a batch line's id bound
([`spec/registry.md`](registry.md) §10.2), and neither a dialect code nor one of §9's: every
selected resource is checked for it before any facts document is held to the registry companion's
facts bound (`FACTS-DOCUMENT-LIMIT`, [`spec/registry.md`](registry.md) §10.1). Its diagnostic
carries what a refusal of the reading carries, the code, the file's sha256 and its size, and never
the id.

## 9. Diagnostic codes

The list is closed: a refusal of the reading carries exactly one of these eight codes, the code of
the step that refused it (§3), which states the rule; a row only names it. Each code's severity is
`error`, and each code's status in `1.0.0` is `active`. The machine-readable list is to be
`conformance/terraform-file/1.0.0/codes.json` (§11); where the two differ, this text governs.
`FACTS-ID-LIMIT` and `FACTS-DOCUMENT-LIMIT`, which the batch reports (§8), are the registry
companion's codes ([`spec/registry.md`](registry.md) §12), and not this list's.

| Code | Severity | Step | Raised when |
| --- | --- | --- | --- |
| `TF-SIZE` | error | 1 | the file, or an input read as a stream, is longer than `maxBytes` |
| `TF-JSON` | error | 2 | the bytes are not one JSON value in UTF-8 with no byte-order mark, no lone surrogate escape, only white space after it, nesting at most 128 deep and no duplicate member name |
| `TF-FORMAT` | error | 3 | the top-level value is not an object whose `format_version` is a string in the accepted table for `document` |
| `TF-DOCUMENT` | error | 4 | the file is not of its `document`'s shape, a resource change, its `after_unknown` or a deposed key is not of its form, or two resources of the read section have one id |
| `TF-SENSITIVITY` | error | 5 | a resource of the read section has no sensitivity mirror, or one with a string, number or null at any position |
| `TF-SELECT-BOUND` | error | 7 (§5) | more resources are selected than `max` |
| `TF-NUMBER` | error | 7 (§6) | a number of the acquired value has a normal form longer than 64 characters |
| `TF-VALUE-LIMIT` | error | 7 (§6) | the acquired value's canonical form, or one selected `plan` resource's `afterUnknown` pointers as charged, are over `L` |

## 10. Versioning and stability

The companion is released on the scoped tag `terraform-file-v<major>.<minor>.<patch>`. The first
release is `terraform-file-v1.0.0`, at status `released`: it is released, and not stable, and it
carries the first table, release `1.0.0` (§4). [VERSIONING.md](../VERSIONING.md) defines the scoped
routes of the Policy and registry companions, and none yet for this one, so this text does not yet
say what record a tag of it names or what bundle it publishes. No stability promise is made before
the first stable release, which needs the second reader §12 asks for.

Dialect version 3, which is proposed, and later Core releases cite this text rather than carry it.

## 11. Machine-readable form and vectors

None is written yet. They are to be under `conformance/terraform-file/1.0.0/`: the code list of §9
as `codes.json`, with each code's severity, status and step; the accepted table of §4 as
`formats.json`, with its release; and the vectors of §12, with a manifest that names, for each
vector, the table release that added its row. Every input is synthetic. Where a file and this text
differ, this text governs.

## 12. Conformance

| Class | Sections | Vectors |
| --- | --- | --- |
| Reader | §§2–7 and §9, and §8 for a reader that writes the batch | none yet |

A claim names the exact release, the table release it implements, and its complete vectors. A
reader is held only to the vectors of the table releases it claims: a file whose `format_version` is
in a later table than the reader's is `TF-FORMAT` for that reader, and that is the expected result
for its claim (RFC 0038 §3). A class without vectors is defined, and not claimable. The stable bar
is two independently written readers agreeing on every vector.

**Vectors.** The vectors, each written by hand as §4 says, are those RFC 0038's Conformance section
lists, with these besides, each with one expected result:

- a stream of `maxBytes` bytes (accepted, with its sha256 and size), and a stream of one byte more
  (`TF-SIZE`, with no sha256 and no size), beside the file row of `maxBytes` and one byte more,
  which stays a file row;
- a plan whose `afterUnknown` pointers repeat a long member name past sixteen times the file's
  length (`TF-VALUE-LIMIT`); a plan whose pointers fit that bound as their canonical form but not
  with eight bytes charged to each (`TF-VALUE-LIMIT`), beside one that fits both; and a file of
  `1e63` numbers, whose value grows about 13.4 times (accepted);
- mirrors whose shape differs from the value, which Terraform does not write, since it writes the
  mirror in the value's shape: a mirror object over an array, marking an element by its index and
  naming a member that is not an index; a mirror array over an object, marking the member `0`; a
  mirror object over a string, marking a position below it (removed); and an empty mirror object
  over a number (kept);
- for the reference runtime's batch, a selected resource whose address is 256 bytes (one line,
  with that id), and one of 257 bytes beside a resource whose facts document is over the facts
  bound (`FACTS-ID-LIMIT`, and no line);
- deposed objects: a plan whose replacement left a deposed object to delete, and a state holding a
  deposed object beside its current one, each carried with `deposed` and sorted after the current
  object; two resources of one id, and a deposed key that is a number, neither of which Terraform
  writes (each `TF-DOCUMENT`); and, for the batch, a deposed object whose id passes 256 bytes
  while its address does not (`FACTS-ID-LIMIT`).

## 13. What is open

- **A refusal's source outcome.** How a refusal of §3's steps maps to a source outcome
  ([`dialect.md`](dialect.md) §9.2) is not stated here: a refusal's source outcome is defined when
  dialect version 3 opens. RFC 0038 records a proposal, open, as its Unresolved question 6.
- **Outside this release:** outputs (RFC 0038, Unresolved question 4); a kind for another tool that
  writes the same JSON (Unresolved question 3); `format_version` values `0.x`, which no table
  lists; and the kind's place in a dialect document, which waits on dialect version 3
  ([`dialect.md`](dialect.md) §4.5).
- **Review regime.** The different-vendor review was waived for the record.

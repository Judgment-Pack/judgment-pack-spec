# Changelog

All notable changes prepared for or included in Judgment Pack Specification previews are recorded
here.

## Unreleased

### Added

- **The terraform-file companion's first release, `terraform-file-v1.0.0`** (reading `1.0.0`,
  status `released`, and not stable; release notes `releases/terraform-file-v1.0.0.md`). The
  text's status sentence and §§11 and 12, the code list, the format table and the vectors' manifest
  say `released`, and the vectors' README no longer says proposed. Its release record,
  `releases/terraform-file-v1.0.0.json`, names the reading, the SHA-256 of the text and the vectors'
  README, the format table, release `1.0.0`, with its rows (all of them added by this first
  release), the code list with its eight codes, the id of every vector and the digest of every file
  under `conformance/terraform-file/1.0.0/`, and the second reader's digest;
  `releases/terraform-file-v1.0.0.milestone.json` links the release's milestone. The site's page
  labels the text normative for its reader class. The stable bar is unchanged: two independently
  written readers agreeing on every vector (§12); the reference runtime and the repository's second
  reader, both from the drafting vendor, give every vector's expected result. Core, its bundles and
  its corpora are unchanged.
- **The `terraform-file` reading is a companion of its own** (`spec/terraform-file.md`, reading
  `1.0.0`; RFC 0018's and RFC 0038's amendments of 2026-11-17; #365). The reading of a
  `terraform-file` source's file, which `spec/dialect.md` §4.5 carried, moves to the new text,
  unchanged but for the maintainer's rulings: it is released under its own selector, the scoped
  tag `terraform-file-v<major>.<minor>.<patch>`, first `terraform-file-v1.0.0`, as released and not
  yet stable, without waiting for the next `specVersion`, and dialect version 3 and a later Core
  cite it rather than carry it. The first format table's release is `1.0.0`, each newly accepted row
  a patch release, and the acquisition record's `formatTable` carries it, which settles the rest of
  RFC 0038's Unresolved question 2. A refusal's source outcome is defined when dialect version 3
  opens; RFC 0038's new Unresolved question 6 records the proposal. The text adds a table of its
  eight codes, a reader conformance class and the claim rule of RFC 0038's Conformance section; its
  machine-readable code list, format table and vectors are the next entry. §4.5 now names the kind, its
  members and class, and cites the companion; RFC 0018's Specification section follows. The site
  publishes the text at `spec/terraform-file/`. No release record is added, and nothing released
  changes.
- **The `terraform-file` reading's code list, format table and vectors**
  (`conformance/terraform-file/1.0.0/`, with reading `1.0.0`; `spec/terraform-file.md`
  §§4, 9, 11 and 12). `codes.json` lists §9's eight codes, each `error` and `active`, with the step
  that raises it and when; `formats.json` is §4's first table, release `1.0.0`: `plan` `1.0`, `1.1`
  and `1.2`, and `state` `1.0`. 188 hand-written, synthetic vectors, each with a source declaration
  and one expected result and each naming table release `1.0.0`, cover RFC 0038's Conformance list
  and §12's additions, every format row, the default `maxBytes` and one byte more, and declarations
  of §2's forms, among them a `maxBytes` written `1.0` or `1e2` and a `mode` or an `actions`
  element that is a number, each malformed with no file read. Their three large inputs are written
  from committed templates by a rule the manifest gives. `tests/test_terraform_file_vectors.py`
  holds the two lists to the text's tables, the manifest to a closed list of groups and every
  expected result to one known shape and its form, and reads each declaration with the first
  reader, directly and as a dialect source; no reader of the file exists in this repository, so the
  reading's results are checked for form only. The companion's status, §9, §11 and §12 now say
  where the files are, and §12 that the default `max` has no vector. The text now states the
  readings the vectors pin, so that none lives in a vector alone: a sha256 is 64 lower-case
  hexadecimal digits with no prefix (§1); `afterUnknown` is sorted in code-point order of its RFC
  6901 strings, and a `values`, `before` or `after` removed whole is absent, each marked optional
  (§6); and such a removal counts one in `removedSensitive`, which counts nothing removed inside a
  removed value or an array removed up to its object member (§3, step 6). No Core bundle carries
  them, the site serves none of them, and no release record is added.
- **A second reader of the `terraform-file` reading** (`tools/terraform_file_reader.py`; RFC 0038,
  Implementation item 3; #369). It is written from the companion text alone, with the registry
  companion's §10.1 and §10.2, RFC 8785 and RFC 6901, uses the standard library only, and reads
  bytes only: it holds the declaration to §2's form, and the file to `maxBytes` (a stream read to
  one byte past it), a depth of 128, the 64-character number bound, `max` and the value bound `L`
  before it writes what they bound. `tests/test_terraform_file_vectors.py` now runs every one of the
  188 vectors through it, and it gives each one's expected result exactly, so the reading's
  results are no longer checked for form only. The companion's status says a second reader is in
  the repository and agrees on every vector; it is a same-vendor reader, not a cross-vendor claim,
  and a test reader, whose memory grows with `maxBytes`, not one for production files. The reading
  stays `proposed`, and nothing about its stability changes.
- **The `terraform-file` reading settles five forms its text left open** (`spec/terraform-file.md`
  §3 step 4, §§5 and 8; #369), each as the reference runtime's reader already reads it, and each
  with vectors that decide it: 18 more, 206 in all. A resource's `address`, `type`, `name`, `mode`
  and `provider_name` are strings, which may be empty, and its `index`, when present, a string or a
  number; `mode` is not restricted when read, so a resource of another mode is read and never
  selected. In a state, `values.root_module` and each child module, when present, is an object that
  needs no `address`, whose `resources` and `child_modules`, when present, are arrays. A type name
  of `select` is a non-empty string. `actions` may repeat a name, read as a set, and an empty
  `actions` selects nothing. In the batch, every selected resource's id is checked, an empty one
  among those refused, before any facts document is held to the facts bound, and either refusal,
  `FACTS-ID-LIMIT` or `FACTS-DOCUMENT-LIMIT`, refuses the whole run before any line is written. A
  refusal's diagnostic now carries a `message` too, a fixed text for its code that holds nothing
  read from the file, in the reader's own words (§3), and §8 gives the reference runtime's batch
  tool's form of a refusal: exit status 2, nothing on standard output, and one canonical object of
  `bytes`, `code`, `message` and `sha256` on standard error. The tool may refuse an empty `actions`
  on its command line, a rule of its flags and not of the reading.
- RFC 0039, a Draft, proposes a federated registry as registry format `1.1.0`: a manifest of
  sources (one standard repository, the rest service repositories), an assembly from bytes the
  caller supplies at full commit ids into one ordinary `1.0.0` registry, and an index that records
  each document's repository, commit, path, content digest and identity. Assembly fetches nothing.
  A repository's bounds may only tighten the standard's, compared construct by construct, and a
  construct with no decidable comparison is refused. Nothing is built.
- RFC 0040, a Draft, proposes registry locks and lock signatures as registry format `1.1.0`: a
  canonical lock of a registry, its kind declarations, each environment's resolved registry and an
  assembled index, and a detached Ed25519 signature over the lock's digest, the reference runtime's
  pack signature design under its own prefix, checked against an expected key before the lock is
  read. Nothing is built.
- RFC 0039 and RFC 0040, Drafts, are amended by the maintainer's rulings of 2026-11-17 on eight of
  their Unresolved questions. In RFC 0039, a repository may serve a subset of the environments, and
  the assembly refuses a gap in any environment a repository serves; an assembly has one standard,
  and the format leaves room for layers; bounds may be given per environment, and tighten-only is
  checked in each; and an assembled registry offered as a source is refused. In RFC 0040, an
  assembled lock needs all of a set of signatures, each repository's documents by its own key and
  the lock by the standard owner's, against a set given out of band with one key per role, and is
  verified only with its index, from which each repository's statement is rebuilt; the lock carries
  a serial that a verifier checks against the last it accepted for the registry id, a record that
  is the verifier's own and is never lowered; the lock pins the emitter manifests and the files
  they own; and a lock names one registry. Each remaining question carries a proposed resolution. Both stay Drafts, and nothing is
  built.
- **The registry companion's format `1.1.0` text, proposed** (`spec/registry-1.1.0.md`; RFC 0039's
  and RFC 0040's amendments of 2026-11-18). The text states RFC 0039's assembly, assembled index
  and tighten-only bounds and RFC 0040's lock, lock signature and source signatures as the
  companion would at format `1.1.0`, with their diagnostic codes, versioning, conformance classes
  and security considerations. It keeps the eight rulings of 2026-11-17 as the records state them,
  and decides the eleven questions that remained as their proposed resolutions: no pattern
  inclusion and no structural bounds in `1.1.0`; no per-entry provenance in the index; selectors
  `"1.1.0"`; an assembly-wide cap only the standard states (`maxAssemblyEntries`); default file
  names for the lock and its signature; separate signature documents for packs and registries; no
  rotation statement; the lock check and the index check reported apart; and one review round over
  both records, whose different-vendor review the maintainer waived (the review is same vendor, not
  a cross-vendor claim). The RFCs' questions sections become Settled questions, and both stay Drafts. It is
  normative for nothing until `registry-v1.1.0`, and format `1.0.0` and `spec/registry.md` are
  unchanged. No schema, code list, row or reader exists.
- **The registry companion's format `1.1.0`, released as `registry-v1.1.0`** (status `released`,
  and not stable; release notes `releases/registry-v1.1.0.md`). Format `1.1.0` is `spec/registry.md`
  (its §§1 to 17, whose rules are unchanged; §§13 to 15 and 17 add only pointers to the second
  file) together with `spec/registry-1.1.0.md`, two files of one companion,
  each with its own section numbers. Both texts' status sentences, the code list and the rows'
  manifest say `released`, the rows' README and the second reader no longer say proposed, and no
  schema's title or description says draft, staged, proposed or not released. Its release record,
  `releases/registry-v1.1.0.json`, names each schema's `$id` and the SHA-256 of both texts, the
  rows' README, format `1.0.0`'s rows' README, every schema, the code list and every row file;
  format `1.0.0`'s schemas, code list and rows, which the bundle carries, must be the bytes the
  record of `registry-v1.0.0` pins. The release builder knows both
  formats: a `registry-v1.1.0` tag releases format `1.1.0`, and a `registry-v1.0.0` tag still gives
  the bytes it gave. The site serves each format's schemas at their `$id` once that format is
  released, and a change record names the nine schemas' new digests. The stable bar is unchanged:
  two independently written readers agreeing on every row of a class (§15). Format `1.0.0`, Core,
  its bundles and its corpora are unchanged.
- **The registry companion's first release, `registry-v1.0.0`** (registry format `1.0.0`, status
  `released`, and not stable; release notes `releases/registry-v1.0.0.md`). The text's status
  sentence, the code list and the rows' manifest say `released`, the rows' README and its heading
  no longer say proposed, and no schema's title or description says draft, staged, proposed or not
  released. Its release record, `releases/registry-v1.0.0.json`, names each schema's `$id` and the
  SHA-256 of the text, the rows' README, every schema, the code list and every row file, and
  `releases/registry-v1.0.0.milestone.json` links the release's milestone. From this release on
  the site serves each registry schema at its `$id`. `catalog/format-status.json` records the
  release as the registry family's baseline, and a change record names the schemas' new digests.
  The stable bar is unchanged: two independently written readers agreeing on every row of a class
  (§15), where one reader, the reference runtime, exists. Core, its bundles and its corpora are
  unchanged.
- **The registry companion's documents have closed schemas** (`schema/registry/1.0.0/`, format
  `1.0.0`, released with `spec/registry.md`, which governs where they differ). There is one JSON
  Schema 2020-12 schema for each of the ten documents of §2.1, and `common.schema.json` for the
  definitions they share. Each requires its selector at `"1.0.0"`, is closed wherever the text gives
  a document's members, and states the forms, bounds, patterns, §12's code list and each code's
  severity; a rule no schema can state, such as canonical order or a digest, is left to the reader,
  and a `$comment` names its section. The harness report's schema holds only its selector, since
  §11.5 names no other member, and the facts document (§10.1), a facts document of Core, has none.
  As with the rows, the companion's own release bundle carries the schemas and no Core bundle does,
  and the site serves each at its `$id` (§13). `tests/test_registry_schemas.py` validates every row
  document a reader admits or writes against its schema. The status of the companion and §14 say so,
  and no row changes. Where the text was silent, it now states the reference runtime's reading, and
  the schemas follow it: a refused registry ends validation after step 2, so the diagnostics of the
  declarations step 1 admitted are still reported (§7.1); a contract's `id` and `version` take a
  kind's forms, and `values` sit only on a string, decimal or boolean, or an array of one (§10.3);
  the check report of a refused contract has neither digest (§10.5); in a manifest, `description` is
  a string, `deprecated` a boolean and `requestVersions` SemVer, `owns` is non-empty, the items of
  `requestVersions`, `owns` and `env` are distinct, no two `reads` name one kind, and `command`'s
  program follows §11.3's path rules after an optional `./` (§11.1); an emitter diagnostic has
  exactly `code`, `severity` and `location`, and `base64` is RFC 4648 §4's, padded, with no bit set
  past the data (§11.3); and §11.5's kind-filtering check no longer names a contract digest the
  facts form does not carry.
- RFC 0027 (#252), a Draft, proposes bounded optional pack-design advisories for compatible
  agreement, scoped coverage and reachability, exception effects and unknown blocking. A closed
  finite-domain report proposal binds exact pack/domain bytes, distinguishes proof from possibility
  and incomplete analysis, and carries explicit resource limits and hand-written
  positive/adversarial cases. It was proposed for specification `0.6.0` and is not released in it;
  it changes no Core resolution or released conformance claim.

### Changed

- **The terraform-file reading has a release route of its own** (`spec/terraform-file.md` §10,
  reading `1.0.0`; VERSIONING.md, "Independently versioned terraform-file companion").
  Its first release is the scoped tag `terraform-file-v1.0.0`, at status `released`, which is not
  stable; this change cuts no tag and changes no status. As for the registry, the release builder
  gives a `terraform-file-v` tag a bundle of its own, `judgment-pack-terraform-file-<version>`, with
  the text, the code list, the format table, the declarations and vectors with their README, the
  checks that hold the vectors to the text with the second reader they run, and the records and
  companion texts the text links, and
  leaves `conformance/terraform-file/` out of every Core bundle by path rather than by
  `export-ignore`, which no longer marks it; `-text` does, as its digests are pinned. The builder
  refuses a `terraform-file-v` tag unless its release record, `releases/<tag>.json`, equals the one
  the tree gives (the SHA-256 of the text, the README, `codes.json`, `formats.json`, the manifest,
  every declaration and vector file and the second reader; the table's release, its rows and the
  rows it adds, the codes and the vector ids), unless the tag's number is the table release `formats.json` gives,
  unless the text's status sentence, the code list, the format table and the manifest all say
  `released` and neither the text nor the README still calls the reading proposed, and unless notes
  exist. The reading's first table release is `1.0.0`, and each later one is exactly the next patch
  of the latest earlier one, in the worktree and at tags: one that accepts new rows, and an erratum,
  which accepts none and whose record's `added` is empty. The text defines no minor or major
  release of the table, so none is on the route. An earlier record of the same reading must carry
  another table release, and the record of the higher one must keep every code, table row and
  vector of the lower; the bytes are not frozen from one release to the next. The release
  and deploy workflows take `terraform-file-v` tags, a plain one drafted as a full release that is
  never marked latest, as a registry tag is. The companion has no schema, so the site serves
  nothing new: no code list, table or vector, before a release or after it. The checks that read
  each declaration with the dialect's first reader move to
  `tests/test_terraform_file_declarations.py`, since they need the dialect's staged vectors, which
  no bundle carries; `tests/test_terraform_file_vectors.py` keeps the rest, the second reader's
  checks among them, and runs inside the bundle, which carries the second reader. The second
  reader's tests load it by its path. `tests/test_terraform_file_release.py` holds the route. The
  text's status bullet now says that the reference runtime reads deposed objects too (`v0.49.0`);
  the second reader and the stable bar are unchanged.
- **The registry companion's rows, code list and schemas are no longer staged: they are published
  with its first release** (`spec/registry.md` §§13 and 14, format `1.0.0`; VERSIONING.md,
  "Independently versioned registry companion"). That release is the scoped tag `registry-v1.0.0`,
  at status `released`, which is not stable. As for Policy, the release builder gives a `registry-v`
  tag a bundle of its own, `judgment-pack-registry-<version>`, with the text, the schemas, the code
  list, the rows and their README, the checks that hold the rows to the text and the records the
  text links, and leaves `schema/registry/` and `conformance/registry/` out of every Core bundle by
  path rather than by `export-ignore`, which no longer marks them; `-text` does, as their digests
  are pinned. The builder refuses a `registry-v` tag unless its release record,
  `releases/<tag>.json`, equals the one the tree gives (each schema's `$id`, and the SHA-256 of the
  text, the README, every schema, the code list and every row file), unless the text's status
  sentence, `codes.json` and the rows' manifest all say `released`, and unless no schema's title or
  description still says draft, staged, proposed or not released. An earlier record of the same
  format, in the worktree or at a tag, must name the same schemas with the same bytes. The release
  and deploy workflows take `registry-v` tags, and the site serves each registry schema at its `$id`
  once the rows' manifest says `released`, so a site built for a Core release before then serves
  none; it serves no row or schema as a file. `tests/test_registry_release.py` holds the route, and
  §15's claim names the rows by the record's digests.
- **The registry companion's closed code list gains fourteen codes** (`spec/registry.md` §12 and
  `conformance/registry/1.0.0/codes.json`, format `1.0.0`, proposed; the maintainer's ruling,
  option A). The emitter host's and harness's own refusals and warnings, which the reference
  runtime reported as provisional codes of its own, are listed under its names and severities and
  named where §11 describes them: `EMIT-OWNS-OVERLAP` (§11.1); `EMIT-KIND-ID` and `EMIT-OPTIONS`
  (§11.2); `EMIT-LINK`, `EMIT-PATH-UNREADABLE`, `EMIT-WRITE`, `EMIT-INTERRUPTED` and the warnings
  `EMIT-ENV-UNSET`, `EMIT-REPORT-TRUNCATED` and `EMIT-STAGING-LEFTOVER` (§11.4); and `EMIT-VECTOR`,
  `EMIT-HARNESS-BOUND` and the warning `EMIT-LINK-OMITTED` (§11.5). `FACTS-ID-LIMIT` joins the
  other `FACTS-*-LIMIT` codes: §10.2 states a batch line's id bound, 1 to 256 bytes, which every
  registry id meets, and a tool that writes lines of that shape from another source refuses the
  whole run past it. §17's two open items on host and harness refusals are closed, and the earlier
  entries below that left them open are superseded. No row changes.
- **The `terraform-file` kind joins dialect version 3, with its first format table and vectors
  written by hand** (`spec/dialect.md` §§4, 4.3 and 4.5, proposed; RFC 0018's amendment of
  2026-11-17 on the kind's version, first table and vectors; the maintainer's rulings). The kind is
  `3, proposed` in §4's table, as §4.3's kinds are, which resolves RFC 0038's Unresolved question 1;
  neither repository reader knows it yet. The first accepted table is plan `1.0`, `1.1` and `1.2`
  and state `1.0`, the reference reader's `proposed-1`, which resolves Unresolved question 2; the
  table's release number stays open. Each row is backed by vectors written by hand to its
  `format_version`'s documented shape, with no Terraform run and no recorded output, in place of
  vectors made with the Terraform release that writes it; RFC 0038 §3 and its Conformance section
  carry dated notes saying so. §4.5 names `FACTS-ID-LIMIT` the registry companion's code. No
  released text carries the kind. By §2.1 the kind is now also defined in the named formats `3.0.0`,
  `4.0.0` and `4.1.0`, released with Core `0.6.0`: a document of one of them that names it, an
  unknown kind under the released text, is now one of a kind defined and not claimable, and nothing
  changes for a document that does not name it.
- **Both repository readers hold a `terraform-file` source to its form** (`spec/dialect.md` §4.5,
  proposed; #358). Each checked such a source as one of a kind its version does not list
  (`input-malformed`). Each now holds it to §4.5's members, `document`, `select` and `maxBytes`, and
  `select`'s `types`, `mode`, `address`, `actions` and `max`, and then refuses it as `kind-unread`,
  as it does `http`, `sql` and `web`, in a document of version 3; a document of version 2 that names
  it stays `input-malformed`. In formats `4.0.0` and `4.1.0` the Python reader does the same, and
  the TypeScript reader, which reads neither, refuses the document `version-unread` first.
  Hand-written cases hold the two readers' reports equal, and each reader's answer in those two
  formats. §4.5 now says so; RFC 0018's Specification section follows. The TypeScript reader's
  `forms.ts`, a file of the `v0.3.0` retained column, keeps its `v0.3.0` bytes under the
  historical-compatibility fixtures, as `verify.ts` does. No released text carries the kind, so nothing released changes.
- **RFC 0038 §2 step 1 notes the stream reading** (#353). The RFC said the reader hashes the
  whole input; an amendment note there now points at `spec/dialect.md` §4.5, where a stream is read
  to `maxBytes` and one byte more and a longer one is `TF-SIZE` with no sha256 and no size. No
  normative text changes.

- **The `terraform-file` kind's readings** (`spec/dialect.md` §4.5, proposed; RFC 0018's amendment
  of 2026-11-17). An input read as a stream is read to `maxBytes` and one byte more, and a longer
  one is `TF-SIZE` with no sha256 and no size (#353). The acquired value is held to the lesser of
  268435456 bytes and sixteen times the file, each `afterUnknown` pointer charged eight bytes
  more, and past it is `TF-VALUE-LIMIT` (#346). A sensitivity mirror of another shape than its
  value is matched as JSON Pointer tokens are, and one that marks a position below a scalar
  removes the scalar (#347). A batch line's id is 1 to 256 bytes, and a resource outside that
  refuses the whole run, `FACTS-ID-LIMIT`, before any line is written (#351). A deposed object
  carries its key as `deposed`, its id is its address, ` deposed ` and the key, the value is
  sorted by id, and an empty key or two resources of one id are `TF-DOCUMENT` (#348); the
  reference runtime does not carry the key yet. An `after_unknown` not of a mirror's form is
  `TF-DOCUMENT`, and an `afterUnknown` pointer is cut at a position `after_sensitive` marks and
  `after` lacks, as the reference reader does. In a plan, each resource change's `change` is an
  object with `actions` an array of strings, or `TF-DOCUMENT`. §4.5 lists the vectors each reading needs beside RFC 0038's. No released
  text carries the kind, so nothing released changes.
- **The registry companion's emitter host** (`spec/registry.md` §11, format `1.0.0`, proposed).
  §11 adopts the reference host's stricter readings (#349): an `owns` glob follows the path rules,
  its first segment holds no `*`, and `**` matches as in gitignore; a response's three members are
  required; a path holds no `:`, no segment ending in `.` or a space, no Windows device name and no
  name git reads as `.git`; an emitter code is `x-` and lower-case words, at most 64 bytes; and
  `EMIT-MANIFEST` is adopted, with the locations of it and of `EMIT-RESPONSE`. §7.3's location
  gains the host's members: `manifest`, the position of another manifest an `owns` overlap names,
  and `variable`, the name (never the value) of an `env` variable the host's environment lacks. Deleting owned
  files, the host never enters a directory git reads as `.git` (§11.4). Five staged emitter-host
  rows, operations `manifest` and `response`, exercise them. Overlap, options, links and unreadable paths
  stay open (§17).
- **The registry companion's harness** (`spec/registry.md` §11.5, format `1.0.0`, proposed; #350).
  Kind filtering forms the request with a synthetic unread kind, restores every registry digest in
  it, requires the original request's bytes, and only then compares responses, so an emitter that
  writes the digest into a file passes. A run passes the references check inside a complete
  occurrence of any secret-position string, so two whole references with a shared prefix pass. A
  vector that gives its request whole skips both checks, and the marker `expected/~empty` records
  a run that writes no files. A vector not of the layout, such as one that holds another file,
  refuses the whole run. Two staged emitter-host rows, operation `request`, and six emitter-harness
  rows, operations `references` and `layout`, exercise them; the harness's own refusal codes were
  provisional then and are the companion's now (§12).

## `0.6.0` — 2026-11-16

Core `specVersion` `0.6.0`, tagged `v0.6.0`, releases the dialect formats `4.0.0` and `4.1.0` and a
workflow stage that names them (#326, #328; [release notes](releases/v0.6.0.md)). The maintainer
waived the candidate period: no release candidate precedes it.

- **Core's rules are `0.5.0`'s.** The selector moves in place: Core's text, schema and both corpora
  name `0.6.0`, and no carrier, structural, semantic or evaluation rule differs, so a `0.5.0` pack
  whose selector alone changes keeps every verdict and disposition (Core §11). Of the files the move
  touches, 435 change the selector alone: 423 conformance files (262 structural, 64 valid, 51
  evaluation, 28 semantic, 12 carrier, 5 advisory and the manifest), 6 examples and 6 site demos.
  Byte-identical copies of the four `0.5.0` schemas stay published at their `0.5.0` identifiers,
  and the workflow schema staged for `0.6.0` replaces `schema/workflow-1.schema.json` in place. The
  document corpus holds 369 conformance cases and 5 advisory cases, and the evaluation corpus 103
  rows with 29 pairs, both `suiteVersion` `0.6.0`. The second evaluator, `tools/core_050_eval.py`,
  admits `0.5.0` and `0.6.0`.
- **Dialect formats `4.0.0` and `4.1.0`.** RFC 0018's amendments of 2026-11-12, 2026-11-13 and
  2026-11-15 are adopted for `0.6.0`, and RFC 0033 (#328) is accepted: its sections 1 to 11 land as
  `spec/dialect.md` §2.3, format `4.1.0`, and the sentences its section 12 lists are amended in
  §§2.1, 5.2, 9, 11, 12, 13 and 14, with RFC 0018's copy of the text. "Proposed" and "staged" are
  gone from both formats' text, vectors and schemas; the vectors stay hand-written and in no corpus,
  and no claim names either format.
- **Recordings and workflow stages (#326).** `schema/dialect-recording/2/` is released, informative:
  the bundles carry it and the site serves it at its `$id`s. RFC 0020's amendment of 2026-11-15 is
  accepted for `0.6.0`; the RFC stays a Draft. `spec/workflow.md` says "since `0.6.0`" where it said
  "staged for".
- **The workflow reader** (`tools/workflow_reader.py`) reads a stage of format `4.0.0` or `4.1.0`:
  the stage's dialect reference selects the release digest rule, an open release's Runner members
  are checked when present, a paged source's profile fit is checked, and a preparation's facts are
  the dialect reader's prepared facts document. `conformance/dialect/workflow-format-4/` marks each
  stage admitted.
- **Patch-release tests (#319).** `tests/test_release.py` holds the patch-release refusals to a
  hand-authored fixture and a test-local normative record, not to the live tree, so the move to a
  new `specVersion` leaves them unchanged.
- The reviews are those on pull requests 329, 330, 331 and 332, by a model of the drafting vendor:
  same-vendor reviews, not a cross-vendor claim. The maintainer waived the review by another vendor.

The entries below record the work in the order it landed, under the names it then had: formats
`4.0.0` and `4.1.0` were proposed, and their artifacts staged for `0.6.0`.

### Added

- RFC 0033 (#328), a Draft, proposes a paged `operation` source for the dialect, as a named format
  `4.1.0` of format `4.0.0`'s family. The pages are one gateway session's calls 0 to n−1, and each
  request is formed from the case and the page before. The loop ends at a page with no next
  reference, or at a declared bound, and the preparation records which. The pages' records are
  joined in call order, duplicates kept, and read once. `pageItems` stays refused.
  `spec/dialect.md` is unchanged; the format's staged vectors and the readers' handling of it are
  the entry below.
- RFC 0033's staged vectors (#328): `conformance/dialect/format-4.1/` holds one hand-written vector
  for each row of the RFC's Conformance table, marked proposed. The Python reader reads format
  `4.1.0` (paging, the walk, the joined value with `last`, the bounds and the preparation); the
  TypeScript reader defines the selector and refuses it `version-unread`. Format `4.0.0` and earlier
  are read as before, and `spec/dialect.md` is unchanged.
- Formats `4.0.0` and `4.1.0` in workflows and recordings (#326), staged for `0.6.0`, each decision
  taken at its recommended answer unless the maintainer answers otherwise. RFC 0020's amendment
  proposal writes the release digest of a stage of either format into its own text: SHA-256 of the
  `canon` bytes of the whole retained release, with two worked examples. A staged
  `schema/workflow-1-0.6.0.schema.json` adds both formats to a named dialect reference. RFC 0018's
  amendment adds version 2 of the dialect-recording schemas for preparations of both formats; it
  does not read version 1's form, and version 1 is unchanged. Reading `0.5.0` recordings is left
  as a follow-up. `conformance/dialect/workflow-format-4/` and `conformance/dialect/recording-2/`
  hold the staged vectors. No release carries the staged schemas and the site does not serve them;
  every `0.5.x` file is unchanged.

### Changed

- The staged vectors in `conformance/dialect/workflow-format-4/` (#337): neither one-stage workflow
  carries `selection` any more, since its one stage is terminal and `spec/workflow.md` §3 forbids
  `selection` there. A new case adds it back, and the workflow reader refuses it `input-malformed`.
  The workflow bytes are in no digest, so no dialect or release digest changes.
- `spec/dialect.md` §2.2.6 and its copy in RFC 0018 (#335): `unsignedParameters` is no longer listed among the ways a format
  `4.0.0` preparation differs. It is a member of the reading (§11), not of the preparation, and the
  case's entry is now stated as a difference of the reading. Text only: no reader, vector, schema or
  digest changes.
- RFC 0033 section 4 (#326): a paged receipt whose `prevSignature` breaks gateway section 1.2
  within the receipt is `acquisition-invalid` (check 1). That covers a signature at `callIndex` 0
  and `null` at a later one. Before, step 4 answered `acquisition-sessions`. The Python reader
  applies the rule, and two staged vectors carry it.
- An amendment to RFC 0018 (#324) states the bounds of the proposed dialect format `4.0.0` once, in
  `spec/dialect.md` §2.2.7: a literal is at most Core §4.1's "Dialect text value bytes" and a list
  element at most its "Dialect text-list item bytes", under the document's profile, and §2.2.4
  points there instead of giving 8192 bytes alone. §2.2.2 names Core §4.1's "Dialect decimal string
  characters" as the research decimal ceiling that `extended` raises, not the `decimal` type's 128
  characters. The Python reader takes these bounds from one table of Core §4.1's `base` rows, and a
  test holds both bundled readers' refusal of a document of the format that declares `extended`,
  `profile-unsupported`. Four staged rows hold a literal and a list element at their `base` bounds
  and one byte over (171 rows). No answer, digest or vector changes; Core `0.5.0`'s schema, text and
  corpora are unchanged.
- RFC 0018's open question 2 on format `4.0.0` (#324) records that a workflow stage naming a dialect
  of the format is not admitted in `0.5.x`: admission waits for `specVersion` `0.6.0` and for a
  release-digest encoding of the format, which RFC 0020 has to define. No workflow schema changes.

## `0.5.2` — 2026-11-13

A release that carries Core `specVersion` `0.5.0` unchanged, byte for byte, as `v0.5.1` does: packs
keep declaring `0.5.0`, the tag name is not a selector, and consumers pinned to `v0.5.0` or `v0.5.1`
need do nothing. It adds the annotation vocabulary `1.0.0`, status `proposed`, beside Core. The
[release notes](releases/v0.5.2.md) give its scope, what a pack author does, what is and is not in its
bundles, and what it does not establish.

### Added

- RFC 0032 (#320), accepted at draft maturity on a same-vendor review with the different-vendor
  review waived, adds the annotation vocabulary `1.0.0`, status `proposed`
  (`spec/annotation-vocabulary.md`), a companion with its own version that defines one well-known
  annotation key, `severity` on an outcome, with the ordered levels `low`, `medium`, `high` and
  `critical`. Absence states no severity; a vocabulary checker applies only to `specVersion`
  `0.5.0`, refuses any other value and any list with `JPS-VOCABULARY-SEVERITY-VALUE` after Core
  admits the pack, and recommends the advisory `JPS-VOCABULARY-SEVERITY-IDENTIFIER` for an outcome
  identifier that ends in another level. The key is inert by Core §8.5. The companion is normative
  for the vocabulary-checker class, published and bundled; Core `0.5.0` §1.1 does not list it. Its
  hand-written rows and machine-readable form stay staged under
  `conformance/annotation-vocabulary/1.0.0/`, in no corpus, bundle or claim, and
  `tools/annotation_vocabulary.py` is the one reader. The review round is copied to
  `rfcs/reviews/0032-round-1.md` (same vendor, not a cross-vendor claim). Core `0.5.0`'s schema,
  text and corpora are unchanged.

## `0.5.1` — 2026-11-13

A release that carries Core `specVersion` `0.5.0` unchanged, byte for byte, the first patch release
under the release numbering rule: packs keep declaring `0.5.0`, the tag name is not a selector, and
consumers pinned to `v0.5.0` need do nothing. The [release notes](releases/v0.5.1.md) give its scope
and what is and is not in its bundles.

### Added

- An amendment to RFC 0018 (#316) proposes dialect format `4.0.0` (`spec/dialect.md` §2.2): a
  named format with no integer twin, adding a rule on the case, `decimal`, `string-list` and
  `address-range-list` parameters, rule version `2.0.0` (ordered comparison, membership, a forward
  freshness window, literal claim values) and the built-in derived values `duration`, `distance`
  and `speed` in exact integer arithmetic, with the preparation form that records them. Its
  vectors are hand-written and staged under `conformance/dialect/format-4/`; the Python reader
  reads the format and the TypeScript reader refuses it `version-unread`. Formats 2, 3, `2.0.0`
  and `3.0.0`, their digests and vectors, and Core are unchanged. The workflow schemas do not yet
  name the format, and no claim names it. Its review is round 17 of RFC 0018, recorded in
  `rfcs/reviews/0018-round-17.md` (three MEDIUM and five LOW, all applied; same vendor, not a
  cross-vendor claim).

### Changed

- The builder can cut a patch release (#314). A tag `vX.Y.Z` carries `specVersion` `X.Y.0`, and
  `v0.4.0` stays the one recorded exception. A patch release's normative artifacts must be byte for
  byte those of its `X.Y.0` release, as `releases/v0.5.0.normative.json` records them for `0.5.0`;
  the builder pins that record's SHA-256 and refuses a patch tag whose files differ, and a patch tag
  of a `specVersion` no release carries. A patch bundle carries `catalog/`, the record and a
  generated `release-identity.json`. In `catalog/format-status.json` a patch tag is a baseline, not a
  candidate. `VERSIONING.md` and `catalog/README.md` state the rule.

## `0.5.0` — 2026-11-12

Core `specVersion` `0.5.0`, tagged `v0.5.0`, releases [RFC 0031](rfcs/0031-annotations-and-value-sets.md)
(#301), annotations and annotated value sets, with issues #304 and #308
([release notes](releases/v0.5.0.md)). The maintainer waived the candidate period: no release
candidate precedes it.

- The text, schema, document cases, evaluation rows and example staged under the working selector
  `0.4.0-draft` are released under `0.5.0`, and the staged paths are retired. The released Core
  schema, document-manifest schema and evaluation-manifest schema replace `0.3.0`'s in place, and
  the workflow document schema's identifier moves to `/schema/0.5.0/`. Byte-identical copies of the
  four `0.3.0` schemas stay published at their `0.3.0` identifiers; the `0.3.0` text and corpora stay
  at tag `v0.3.0`. The document corpus holds 369 conformance cases and 5 advisory cases, and the
  evaluation corpus 103 rows with 29 pairs, both `suiteVersion` `0.5.0`. Three valid cases added
  after the round-1 review pin that the reserved prefix `org.judgmentpack.` ends in its dot: the
  names `org.judgmentpackx.a`, optional and required, and `org.judgmentpack` are admitted (Core §9).
- **Why `0.5.0`.** Tag `v0.4.0` carries `specVersion` `0.3.0` unchanged. [VERSIONING.md](VERSIONING.md)
  now states the release numbering rule: a tag's major and minor numbers are those of the
  `specVersion` it carries, and its patch number counts later releases that carry it unchanged.
  `v0.4.0` is the rule's recorded exception, so no `specVersion` `0.4.0` is assigned and the version
  staged as `0.4.0-draft` is released as `0.5.0`. A `0.5.0` reader refuses a pack declaring
  `0.4.0-draft`, by the exact selector; such a pack moves by changing its `specVersion` to `0.5.0`
  (Core §11).
- RFC 0031 is Accepted on its same-vendor round-1 review, with the different-vendor review waived by
  the maintainer; that is not a cross-vendor claim. Its Acceptance section states each evidence-bar
  item, and the round-1 record gains a dated note. Item 3 is met in part: both implementations are
  by the drafting vendor, both refuse the 18 document cases that declare the `extended` profile,
  which neither supports, and
  the reference runtime passed the vectors staged at c867b35 but has not run the seven cases #308
  added, the two fixtures #304 rewrote, or anything under `0.5.0`, which is its follow-up.
- The second evaluator is `tools/core_050_eval.py`. The site serves Core `0.5.0` at `/spec/0.5.0/`
  and keeps `/spec/0.3.0/` as a signpost to the tag.

The entries below record the work in the order it landed, under the names it then had: RFC 0031 and
its artifacts were a Draft staged under `0.4.0-draft`.

### Added

- RFC 0031 (#301), a Draft, proposes annotations and annotated value sets. Short labels on the
  pack, its outcomes and rules live in the reserved extension `org.judgmentpack.annotations`: keys
  from the local-identifier grammar, each mapped to a string or a list of distinct strings, with
  ceilings and refused empty forms. A string refuses control, bidirectional-format, invisible and
  default-ignorable characters, and white space at either end. The extension is optional and never
  required. A pack may declare named value sets at its root, whose entries may carry descriptions
  and annotations, and an `in` condition may name one in place of an inline list. An evaluator must
  give a conforming pack the result of its evaluation form, with annotations removed and references
  expanded, so well-formed labels are inert and a reference equals its inline list. It targets the next `specVersion`
  after `0.3.0`, is normative for nothing, and changes neither the published schema, Core text nor
  any released conformance claim.
- RFC 0031 (#301) is staged as a draft Core `specVersion`, under the working selector `0.4.0-draft`,
  which no maintainer has assigned and no release carries ([VERSIONING.md](VERSIONING.md)). The
  staged schema is the `0.3.0` schema plus exactly the record's fragments. The staged Core text
  (`spec/staged/`, retired at the release) is marked normative for nothing.
  Hand-written vectors sit in no corpus: 215 document cases in
  `conformance/staged/`, with five provisional conformance codes,
  and 82 evaluation rows with their pairs in
  `conformance/evaluation/staged/annotations-value-sets/`,
  where one more row is held. An annotated expense example is staged too. Tests hold all of it to the
  repository's checks, including a static check of the paired rows, and check that every released
  case and row still holds under the draft selector. Under the draft selector an `extensions` object
  is one the schema defines, a change that takes effect there and refuses one `0.3.0` shape the
  released checker accepts; Core `0.3.0` and that checker are unchanged. The staged directories are excluded from release
  archives and from the site. The record-shape catalog lists the staged schema, whose `$id` is in the
  specification's schema namespace, with its shape and digest, and Core's `draftVersion` there names
  the working selector, not an assigned `specVersion`. RFC 0031 stays a Draft, and the released
  schema, Core text and corpora are unchanged.
- RFC 0031's round-1 review, by a reviewer from the drafting model's own vendor, is recorded at
  `rfcs/reviews/0031-round-1.md` with its disposition; it is not the different-vendor review the
  record's Evidence bar asks for. The staged artifacts follow it:
  the string rule above; a filtered view that states its counts and shows every character outside
  printable ASCII unambiguously; limits on the pack as presented counted as document limits; the
  annotations name in a supported-extension set ignored (draft §8.2); the two value-set advisories
  kept out of the draft's Core text; and more inertness rows, over evidence, exceptions, the
  fallback outcome and escalation routes. The draft schema's new digest has a change record.
- A second evaluator for the staged draft selector `0.4.0-draft` (#301),
  `tools/core_draft_eval.py` (now `tools/core_050_eval.py`), written from Core, the
  staged delta and RFC 0031 alone, by the drafting model's own vendor. It admits a pack (the
  carrier, the `base` profile, the staged schema and the semantic checks, written fresh), builds the
  evaluation form and evaluates it under Core §§7–8. Its test, `tests/test_core_draft_eval.py` (now `tests/test_core_050_eval.py`),
  runs every staged evaluation row against its expectation (82 agree; the held row agrees and stays
  held), the rows they carry over, the 29 pairs, and every staged and carried-over document case;
  the 18 cases that declare `extended` are checked to be refused with `profile-unsupported`. It
  also states, as its own cases, the rules of Core §§7–8 its mutation check found no row
  distinguishes. It is a test tool, not a product, and makes no conformance claim; whether it meets
  RFC 0031's evidence bar item 3 is the maintainer's judgment. RFC 0031 and the staged READMEs say
  so. No case, row, fixture, schema or expectation changes.
- Under the staged selector `0.4.0-draft`, a local identifier, an extension name, a pack version or
  a decimal operand holds no line terminator in any engine (#308; RFC 0031, Unresolved question 5,
  answered). Some engines let `$` match before a final line feed, so `"name\n"` passed Core's
  local-identifier pattern under one validator and failed under another. The staged schema adds a
  `not` beside the local-identifier, pack-version and decimal-operand patterns and beside the
  extension-name pattern, which also takes over the reserved prefix from a lookahead RE2 cannot
  compile, and escapes a class hyphen ECMA-262's `v` flag refuses. The patterns admit the same
  values in Python, ECMA-262 (`u` and `v`), RE2, Perl, Java and Ruby, and what Core
  `0.3.0` admits under ECMA-262. Seven staged cases refuse one such value in each kind of position;
  the draft schema's new digest has a change record. Core `0.3.0` is unchanged.
- An informative concept page, [Roles in a record](docs/concepts/roles-in-a-record.md) (#275),
  names the judge, the signer, the witness and the reader around a decision record: what each
  produces, trusts and never does, and which parts are not shipped. It defines nothing.
- JSON Schemas for three record formats that had none (#286), so the record-shape catalog
  fingerprints them, each with a generated change record and a format-status record: receipts as
  consumed, `schema/receipt/3/acquisition.schema.json`, the form spec/dialect.md §5.2 holds a
  gateway's version-3 acquisition receipt to; the decision record and audit chain,
  `schema/decision-record/1/record.schema.json`, the record as dialect §11 reads it, and
  `schema/decision-record/1/checkpoint.schema.json`, the checkpoint of checkpoint-witness §2; and
  the dialect recordings, `schema/dialect-recording/1/export.schema.json`, a Runner export as the
  recording reader reads it, and `schema/dialect-recording/1/preparation.schema.json`, the
  preparation of dialect §9. Each describes only the members the prose reads, leaves open what the
  gateway, the runtime or the Runner owns, and says what it does not check. A test validates every
  dialect vector of each family against its schema, with hand-written cases for each constraint.
  The schemas are informative and at draft maturity, as the companion documents are: Core §1.1
  does not list them, so publishing them changes no format's normative status, and the prose
  controls where they differ. The site serves each at its `$id`.

### Changed

- [RFC 0030](rfcs/0030-agent-principals-and-delegated-authority.md) is amended for #284
  (2026-11-09), still Draft, closing the five LOW findings of its confirmation review. On an action
  key, the actor's credential is also held to step 11's `source` and `tool` conditions for the
  action's write (NC1), and the subject's request makes a standing read to the issuing host,
  failing closed as `standing-unknown` (NC5). The admission read may name the grant's owner, or
  the gateway makes a separate owner read, and `owner-removed` and `owner-unknown` are ordered
  after step 12 (NC2). A grant with no owner is used and reported `owner-missing` rather than
  required at adoption (NC3). A pending action whose read-back runs through a revoked or
  quarantined grant stays `unknown` (NC4). The needed vectors are listed. Nothing in Core or any
  released conformance claim changes.
- [RFC 0030](rfcs/0030-agent-principals-and-delegated-authority.md) is amended again for #291
  (2026-11-09), still Draft, closing the six LOW findings of the narrow review of #289. A request
  on an action key that the declared read-back answers holds the actor's credential to step 11's
  `source` and `tool` conditions for the read-back's own source and tool as well as the write's,
  refusing `action-key-unauthenticated` otherwise. The owner read's cost is restated as one read
  per use outside the admission read. The vectors now name the key's state where a link excludes
  only the effect, what is counted on each owner-read path and step 12's refusal on both, that a
  recorded owner is never cleared (NC3), a read-back whose owner read is unanswered staying
  `unknown`, and a request on an uncertain key whose grant was revoked answered with its uncertain
  record, with no dispatch and no read-back, its outcome staying `unknown` (NC4). The read-back's
  source and tool check is placed after the key lookup finds the key uncertain and before the
  grant's state, owner read or publisher check. Nothing in Core or any released conformance claim
  changes.

## `0.4.0` — 2026-11-02

A release that carries `specVersion` `0.3.0` unchanged: packs keep declaring `0.3.0`, the tag name
is not a selector, and consumers pinned to `v0.3.0` need do nothing. The
[release notes](releases/v0.4.0.md) give its scope and what is and is not in its bundles.

### Added

- A Core `0.3.0` dialect recording set (#249): 46 recordings made by the reference Runner under Core
  `0.3.0`, in `conformance/dialect/vectors-0.3.0/` with `manifest-0.3.0.json`, beside the 47
  historical recordings, whose bytes do not change. They are staged like those: in no corpus and no
  release bundle.
- RFC 0030 (#280), a Draft, proposes agent principals and delegated authority: a registered agent
  principal, a signed and bounded delegation with RFC 8693 subject and actor semantics exercised
  through short-lived, sender-constrained credentials, an exact narrowing check for chains,
  revocation, the connection grant as a principal-held resource, and actor, subject and delegation
  in receipts and run records with an exact compatibility rule for existing readers. Its delegation
  statement is standards track at draft maturity, and the rest is a cross-project exploratory
  record. It is normative for nothing, and nothing in Core or any released conformance claim
  changes.
- A record-shape catalog (#256): `catalog/record-shapes.json` gives every JSON Schema the
  specification defines in a stated normalized form (RFC 8785 serialization of an integer-only JSON
  value) with its SHA-256 digest and a family inventory derived from the tree. Change records in
  `catalog/changes/` replay every digest, and `catalog/format-status.json` gives per family the
  draft version, the last accepted compatibility baseline and the last release, checked against
  `releases/`. The `record-shapes` check runs on every pull request. `catalog/README.md` describes
  how an implementation compares its own catalog, where a mismatch is a finding and no part of a
  conformance claim. No schema, corpus or released artifact changes. The catalog is in this release's
  bundles.

### Changed

- `VERSIONING.md` and the builder gain the exact mapping `releases/v0.4.0.json`. It is that tag's
  alone and introduces no general rule that a tag may differ from its artifacts' `specVersion`.
- RFC 0028 and the complete-attribution text now target `0.5.0`, and RFC 0027 targets `0.6.0`. The
  staged `$id` under `0.4.0` is not edited and is not published by this release.
- RFC 0019 is named at Draft maturity, outside the specification, as the record #142 asked for.

## `0.3.0` — 2026-10-29

The first Core release without a `-draft` suffix, at maturity `draft`, after the candidates
`v0.3.0-rc.1` (2026-10-25) and `v0.3.0-rc.2` (2026-10-27); the
[release notes](releases/v0.3.0.md) give its scope and migration note.

### Added

- The selected `retained-column/1` leaf ([RFC 0029](rfcs/0029-retained-column-conversions.md),
  accepted at draft maturity; #274): the [selected retained columns](spec/retained-column.md)
  companion, the versioned schema `schema/retained-column/1/contract.schema.json`, the corpus
  `conformance/retained-column/1/` and the two offline readers. It was first distributed in
  `v0.3.0-rc.2`. The final is its normative support distribution (support version `0.3.0`, inventory
  `releases/v0.3.0.retained-column.json`), with the schema and corpus bytes unchanged.
- Name the next Core release `0.3.0`, define conformance maturity independently, and require `v0.3.0-rc.1` before release (#231).
- Re-pin released Core schemas, manifests, packs, vectors, readers, and site routes to exact `specVersion` `0.3.0`, preserving `0.2.0-draft` artifacts (#231).

- Policy companion decision (#211): keep RFC 0023 Accepted at draft maturity and Policy 1.0.0 pinned, record its duplicate-identity and no-list-priority rules, and leave disagreement refusal and the second independently authored reader open.
- RFC 0022 aligns reusable-subgraph bounds, routed handoff provenance, dialect-owned remapping and
  cross-installation packaging with the decisions on #129, #219, #232 and #170 (#233).
- Dialect-owned data quality and typed research results (#170, #169): six closed deterministic
  conversions with recorded failures, three explicit reconciliation modes, presence/type/domain
  findings surfaced as unknown facts, transformation lineage, typed research result states,
  versioned acquisition-source profiles, resolved execution settings and retained response bytes.
  Replay uses retained bytes without calling a model or the web.
- RFC 0020 limits the later-sibling `limit-exceeded` rule to instances admitted for acquisition;
  admission failures keep their own codes, with a recorded positive vector and negative twin (#213).
- Document ceiling profiles (#232): default `base` and declared `extended`, a shared
  ceiling table, explicit unsupported-profile refusal, capability discovery and
  byte identity. Schemas retain base bounds; profile conformance covers negotiation.
- A non-normative rule-overlap check (#227) with the closed `JPS-RULES-OVERLAP` diagnostic,
  exact and not-excluded findings, warning/strict/publish severity levels, exclusive rewrite
  guidance, and advisory vectors. Core §8 conflict resolution is unchanged.

- Core escalation routes (#219): exclusive single target or up to eight conditional routes,
  ordered fan-out in `handoff.routes`, complete retained reasons, and unchanged single-target
  disposition bytes. Structural fixtures and staged evaluation vectors cover selection, bounds,
  duplicate targets and no selection; profile negotiation, Dialect outputs and delivery receipts
  remain separate work.

- RFC 0020's accepted issue #228 amendment: workflow output envelopes name their contributing
  rule outside Core's unchanged disposition; every stage records a closed disposition summary
  and a reproducible seeded sample; the workflow verifier recomputes both and refuses disagreement;
  and drift is a comparison over two verified bundles of the same workflow, without a verdict.
  The closed workflow schema and hand-written two-stage contract fixture carry the new records,
  digest recomputation, drift rows and refusal vectors. No workflow implementation, recorded
  executor run or conformance claim is added.

- Official-draft Policy promotion preparation: versioned closed format `1.0.0`
  schemas, retained-byte examples and 124 staged agreement vectors, explicit
  migration/provenance and a scoped independent draft release route through the
  shared builder/workflow. First release identifier `policy-v1.0.0-draft.1`
  requires its exact tag and a maintainer-published GitHub release to establish
  immutable publication. The maintainer approved the bounded draft after CI, effective upon
  PR 218 merge, recording the limited public review and standing temporary different-vendor-review
  exception. Core versions and evaluation are unchanged.

- The forty-second to forty-seventh dialect vectors, the six `endpoint-scope-` vectors
  (`endpoint-scope-two-paths-one-origin`, `endpoint-scope-wildcard-two-origins`,
  `endpoint-scope-endpoint-outside`, `endpoint-scope-redirect-outside`,
  `endpoint-scope-changed-constraint`, `endpoint-scope-changed-request`), staged byte for byte from
  Runner commit `10c073c`, pull request 142 (issue #199), beside the forty-one unchanged vectors.
  Both readers, unchanged, give each the manifest's answer: a reading whose binding `matches` for
  the first two, `acquisition-invalid` for the endpoint outside, the redirect outside and the
  changed request, `profile-mismatch` for the changed constraint. The markers round 15 placed in
  `spec/dialect.md` §§5.1 and 5.2 (and the RFC's Specification, equally) follow the staged vectors
  for the rules they decide; this is no rule change. The vectors remain staged until the next
  `specVersion` opens, in no corpus.
- The staged Runner manifest of the dialect vectors brought to Runner commit `a4fa245`, pull
  request 137 (issue #205): the one expectation it changes, the `verifyRun.report` of
  `disposition-differs-from-audit`, now carries the preparation's checked report beside the
  finding. No vector file, count or status changes, and the cross-reader test's comparison of a
  reading with the report now covers that vector. `source.extendedBy` records the commit with no
  vectors.
- The fortieth and forty-first dialect vectors, `acquired-dependent-source` and
  `acquired-dependent-source-unknown`, staged byte for byte from Runner commit `694fe69`, pull
  request 109 (issue #203), beside the thirty-nine unchanged vectors: an acquired source that
  declares source parameters, its claim `resolved` or `unknown`, whose lineage entries name every
  declared parameter in `dependencies` (§9.3). Both readers, unchanged, recompute each preparation
  byte for byte and give a reading whose binding `matches`, and the cross-reader test holds their
  reports equal on all forty-one. The vectors remain staged until the next `specVersion` opens, in
  no corpus.
- The thirty-ninth dialect vector, `skipped-source-dependency-unavailable`, from Runner commit
  `ed1bc2a`, pull request 105, staged byte for byte beside the thirty-eight unchanged vectors.
  The vectors remain staged until the next `specVersion` opens, in no corpus.
- The reference Runner's twenty-six research vectors, the first of the kind `research`, are staged
  byte for byte in [`conformance/dialect/`][staged-dialect] beside the twelve, from the Runner's
  pull request 97 (issue #190): the runs of the two examples of [`spec/dialect.md`](spec/dialect.md)
  §11's fixture plan, `gtm-company-person` and `work-item-triage`, each a dialect of version 3 bound
  at import, its responses recorded from a stand-in of a gateway. Both readers, unchanged, give each
  the Runner's answer: a reading whose binding `matches` for twenty-two, `preparation-differs` for
  the two `changed-binding-old-preparation`, and `acquisition-invalid` for the two
  `changed-response`, and the cross-reader test now holds the two readers' reports equal on every
  staged vector. Those two carry a value of the Runner's manifest new here, `retained: "recorded"`:
  their inputs were changed after the run, so no preparation can be computed from them, and their
  `preparation.json` is the preparation the run recorded, held fixed. The staging README defines it,
  and the repository's tests hold such a file to the Runner's digest as it is and recompute nothing
  from its inputs. They recompute the two `changed-binding-old-preparation`, whose export retains a
  preparation of an earlier instant, at the vector's own `verifiedAt`. RFC 0018 is amended with them
  (2026-10-16, round 11), and the companion document with it; its status stays `Accepted`. §11 says
  that a fixture whose inputs were changed after the run holds the recorded preparation fixed and
  expects the finding the change gives; and the text says what is now so: the Runner prepares
  `research`, twenty-six vectors hold it, and the companion's Status counts thirty-eight vectors
  (§§4.3, 8.2, 9.1, 11 and the Status). No answer a reader gives changes. The review of round 11,
  two MEDIUM findings, both applied, is recorded with the maintainer's disposition in
  `rfcs/reviews/0018-round-11.md`.
- [RFC 0020](rfcs/0020-workflow.md) (Draft): the workflow, a proposed companion document beside
  Core, with a `workflow-verifier` reader class. It defines pinned stages, a selection between
  stages, one instance per selected record, projected cases, output lineage and an execution
  inventory. The proposed text is added as `spec/workflow.md`, held equal to the RFC's
  Specification, normative for nothing while the RFC is a draft and in no release bundle
  (`.gitattributes`, `export-ignore`). Its two-stage run and independent readers remain to be
  recorded and implemented; no workflow fixture or conformance claim exists. Nothing in Core,
  the dialect or the conformance corpora changes.
- The reference Runner's eleventh and twelfth preparation vectors, the first of dialect version 3,
  are staged byte for byte in
  [`conformance/dialect/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/dialect)
  beside the ten, from the Runner's pull request 83: `version-3-bound`, the valid case's dialect
  written as version 3, and `unbound-bound-at-import`, a dialect published with its source unbound,
  with its binding document and the bound dialect the Runner made of them. Both readers,
  `tools/dialect_verify.py` and `tools/dialect-verify-ts/`, now read dialect version 3 as
  [`spec/dialect.md`](spec/dialect.md) §§4.3, 4.4 and 9.1 define it: a document of version 3 is read
  as one of version 2, and its preparation is of version 3; an unbound source is read with its
  binding document, as the bound dialect, and a binding document of another dialect, or one that
  does not name exactly the unbound sources, is refused, and a profile bound of another shape or
  record is `profile-mismatch`; a source of a kind of §4.3 is held to its form and refused as
  `kind-unread`. Both give the two vectors the Runner's answer, a reading whose binding `matches`.
  The extension is one author's, who read both readers, so for these two their agreement is not
  independent. RFC 0018 is amended with them (2026-10-15), and the companion document with it; its
  status stays `Accepted`. The text now says what is so: the reference Runner reads version 3 since
  its pull request 83 (`v0.12.0`), preparing `operation` and `selected-file` and refusing `http`,
  `sql`, `web` and `research` by name, and two vectors hold version 3 (§§2, 4, 4.3, 4.4 and the
  Status); §14's claim form admits a claim of version 3 beside version 2. Version 3 is written one
  way (§2): a document of version 3 that names `provider`, `facts` or `evidence`, members of version
  2 alone, or writes empty a member the Runner's encoding leaves out when empty (`sources`,
  `unmapped`, `unmappedEvidence`, the case's and a source's `parameters`, and `admits`' `facts` and
  `evidence`), is refused, and both readers refuse both. The Evidence records the readings both
  readers take where the text names a member of a version-3 kind without a form. The amendment's
  review, round 7, recorded in `rfcs/reviews/0018-round-7.md`, brought two rules more to the
  Runner's: `cites` is ordered by `callIndex` in versions 2 and 3 alike (§9.1), and a copy's
  `facts` and `evidence` are both required in every version (§6.2), which changes one answer the
  accepted text gave: a copy that left an array out was read and is refused now. Both readers now
  refuse a binding document of `null`, count a research record's 64 retained responses before any
  form (§12), and hold a `research` acquisition to its own form (§§4.3, 5.2).
- [RFC 0018](rfcs/0018-dialect.md) is `Accepted`, at draft maturity, under the interim review
  regime; the maintainer waived the comment period RFC 0000 names, because the project has no
  outside readers yet, and the adoption record says so as a departure. The RFC taken up from the
  reference Runner's mapping v2 is the dialect, a pack's terms spoken in a system's: how the facts
  and the evidence availability an evaluation takes are obtained and derived, with a reader class
  of its own, the *preparation verifier*, which recomputes a preparation and holds a runtime
  record's binding to it. Its Specification section, word for word, lands as the companion document
  [`spec/dialect.md`](spec/dialect.md), normative for that class and for nothing else, beside the
  released Core `0.2.0-draft`, which it does not change. Core §1.1's list of normative artifacts
  gains it, the architecture vision's sentence that nothing in the input-lineage research line is
  part of JPS gains it as a second exception, and the site serves it as a page of its own. Version
  2 of the dialect document is the Runner's mapping v2 byte for byte, and the preparation's
  canonical form is the Runner's, stated there; version 3, with the kinds `http`, `sql`, `web` and
  `research`, is proposed and not claimable; the output side is the gateway's decision policy, by
  reference. The RFC states what a preparation establishes per part: a derivation is recomputable,
  an acquisition is held by its digest under its receipt, and a research record establishes the
  least. The Runner's 9 preparation vectors in
  [`conformance/dialect/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/dialect),
  byte for byte unchanged, stay **staged** until the next `specVersion` opens: in no corpus, no
  claim may cite them, the site does not serve them, and no release bundle carries them. Two
  readers, `tools/dialect_verify.py` and `tools/dialect-verify-ts/` (the second written from the
  text alone), agree on all nine. The records of the RFC's three review rounds, as their pull
  requests carry them, are added under `rfcs/reviews/`.
- [RFC 0017](rfcs/0017-checkpoint-witness-statement.md) is `Accepted`. Its Specification section,
  word for word apart from one pointer to the vectors, lands as the companion document
  [`spec/checkpoint-witness.md`](spec/checkpoint-witness.md), normative for a new conformance
  class, the *witness-statement reader*, and for nothing else, beside the released Core
  `0.2.0-draft`, which it does not change. Core §1.1's list of normative artifacts gains it, and the
  architecture vision's sentence that nothing in the input-lineage research line is part of JPS
  gains its first exception, the statement. The gateway's 54 vectors in
  [`conformance/witness/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/witness),
  byte for byte unchanged, stay **staged** until the next `specVersion` opens, as RFC 0013's rows
  are: in no corpus, no claim may cite them, the site does not serve them, and no release bundle
  carries them. When that version opens they move into a corpus and Core §1.1's list gains them;
  whether they take a `suiteVersion` of their own stays open (the RFC's first unresolved question).
  The record of the RFC's first review round, as its pull request carries it, is added under
  `rfcs/reviews/`.
- [RFC 0017](rfcs/0017-checkpoint-witness-statement.md) (Draft): the checkpoint witness statement,
  taken up from the reference gateway (`v0.11.0`, `SPEC.md` §8) as a proposed companion document of
  the specification, with a reader conformance class of its own. The maintainer's decision on issue
  #122 is that the statement is taken up, with its vectors the same bytes as the gateway's; the RFC
  restates its canonical form, signed bytes, key rule and equation, chain rule, reading, bounds,
  refusals, findings and report sentences, changing no rule a reader applies. It leaves to the
  gateway one rule on the producer, that a gateway witness signs with the gateway's own seed, and
  says what it resolves of RFC 0012's question 4 and RFC 0010 §4. The gateway's 54 witness vectors
  are imported byte for byte into
  [`conformance/witness/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/witness),
  with a manifest that records each one's SHA-256. They are in no corpus while the RFC is a draft:
  no claim may cite them, the site does not serve them, and no release bundle carries them
  (`.gitattributes`, `export-ignore`). The repository's tests hold their bytes, their form and their
  counts; nothing here verifies a signature. Nothing in Core `0.2.0-draft`, its schema, its classes or
  its corpora changes.
- The field guide gains **When rules could disagree**, informative authoring guidance for a
  consequence of §8 that two independent encodings of real policy each had to discover: the format
  has no rule priority, so a pack that holds both an *allowed* rule and a *not allowed* rule answers
  `conflict` whenever one of each is true. It gives the shapes that work — detectors that all name
  one outcome with the ordinary outcome as `fallbackOutcome`; the policy's own ordering as an
  exception; disjoint conditions — says when `conflict` is the right answer, and names the trap in
  the first shape: a detector with `onUnknown: ignore` lets the fallback answer for a check that
  never ran. This is the guidance [RFC 0007](rfcs/0007-determination-boundary.md) (finding E4)
  said did not exist. Nothing normative changes.
- [RFC 0013](rfcs/0013-evaluator-error-and-precedence-cases.md) is `Accepted`, and its five rows —
  the first to use `expectedErrorClass`, two of them inputs where more than one §8.4 class applies
  and the fixed order decides — are **staged** in
  [`conformance/evaluation/staged/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/evaluation/staged)
  for the `suiteVersion`
  after `0.2.0-draft`. They are in no corpus: the `0.2.0-draft` corpus is frozen and unchanged, no
  claim may cite a staged row, the site serves nothing under the staged directory, and no release
  bundle carries it (`.gitattributes`, `export-ignore`). That does not make them optional reading:
  they restate §8.2 and §8.4 as already released, so an implementation that disagrees with one may
  be violating the released contract without having failed a released row. The RFC's four open
  questions are decided (a structural fixture that fails for its one stated reason; no asserted
  phase, because §8.4 requires a class and not a phase; two fixtures; five rows). The repository's
  check that every evidence key a case supplies be declared by its pack becomes conditional on the
  expected error class. It admits a correctly labelled error row, which it used to refuse, and asks
  more of what it still covers: the class a case expects must be the one §8.4's fixed order reports
  for the case's own inputs, read without an evaluator. For the released rows it refuses what the
  old check refused, and every one passes unchanged. The RFC was first merged without the
  cross-vendor review the interim regime requires; that cannot be undone, the adoption record says
  so, and the review on the accepting pull request is the first the proposal has had.
- RFC 0010 (Draft): the gateway signing identity — custody of the private seed (which also keys
  the arguments commitment), content-binding seals, key rotation in the registry, and external
  checkpoint anchoring of sealed history. The first RFC whose every part lands outside JPS — in
  the reference gateway repository's code, specification, guidance, and corpus — and the
  architecture vision's statement that no RFC proposes the research line's formats as JPS remains
  true. Prompted by a stray private seed found untracked in the runtime repository's working
  tree; the ignore-rule guards shipped separately in both repositories.
- Search, answer-engine, and generative-engine discoverability for the static site: every indexable production
  page now carries full-name titles, explicit index directives, complete Open Graph and summary-card
  metadata, sitemap and license discovery links, and schema.org Microdata for the site, project,
  versioned technical specification, visible breadcrumbs, and all 47 complete FAQ answers. FAQ
  questions now render as stable semantic headings without adding executable JavaScript, and a
  concise experimental `/llms.txt` navigation aid points machine readers to the normative,
  informative, proposed, and companion-project surfaces without claiming crawler or ranking support.

### Changed

- RFC 0018 and its companion record issue #214, option C (2026-10-18, round 16): the constrained
  page form refuses an escaped slash or backslash (`%2f`, `%2F`, `%5c`, `%5C`) anywhere in the
  path, and a segment whose part before its first `;`, `%3b`, `%3B`, `%3f`, `%3F`, `%23` or
  `%00` is a dot segment (`..;x`, `.;`, `%2e%2e;`, `..%3bx`, `.%00`). The refusals hold wherever
  round 15's form does: every scope entry and endpoint, at admission and at check 3, and at
  binding for a `web` source's literal `url`. Section 13 says the scope holds the URL as written,
  not what a server serves for it; double encoding, an overlong UTF-8 dot, a full-width dot or
  solidus and a server's own rewriting stay the operator's. Both readers implement the refusals
  with controls on altered copies of a staged vector; no vector changes. The Runner's matcher
  and the Desk's admission check remain follow-ups. The review, same-vendor at the maintainer's
  direction while the OpenAI reviewer was unavailable, and the maintainer's disposition are
  recorded in `rfcs/reviews/0018-round-16.md` (two MEDIUM and five LOW, all applied).
- RFC 0018 and its companion record issue #199, direction A (2026-10-17, round 15): an optional
  `endpointScope` for page profiles, checked against each signed final endpoint. The form admits
  all three spellings of port 443; only generated research page profiles admit the wildcard,
  while record profiles hold prefix entries only. Both readers implement the rule with controls
  on altered copies of a staged vector. Exact profiles and historical receipts stay unchanged;
  no vector changes. Runner support and evidence as vectors, and the Desk's profile review,
  remain follow-ups. The review and the maintainer's disposition are recorded in
  `rfcs/reviews/0018-round-15.md` (one HIGH, two MEDIUM and four LOW, all applied).
- RFC 0018 and its companion, issue #200: the `dependencies` row of §9.3's lineage table no longer
  says the member is absent for a local file. It reads "absent for the case and a source that
  declares none", as round 12's rule in the same section already gives it to every source that
  declares a source parameter, acquired or skipped; the reference Runner writes it for a local
  file with parameters. A correction of a contradiction inside round 12's own text, not a new
  rule. Both readers already follow the general rule; no reader changes, no vector is changed.
- RFC 0018 and its companion record issue #197, option A (2026-10-16, round 14): a `selected-file`
  of provider `google-drive` requires a `drive` input profile of class `record`, and its binding
  is `record`; a profile of class `generated` bound to it is `profile-mismatch` (§§4, 4.2 and 5.1).
  The reference Runner already enforces this rule. Neither repository reader reads the kind,
  and no vector holds it; §5.1 marks the rule as a position no vector decides. No reader changes,
  and no vector is changed or claimed; the review and the maintainer's disposition are recorded
  in `rfcs/reviews/0018-round-14.md` (six LOW, five applied and one noted).
- RFC 0018 and its companion record issue #195 (2026-10-16, round 13): §5.1 states which class
  a binding takes, by kind, with references from §§4, 4.4 and 8.2. An `operation` of any admitted
  shape takes its profile's class; research capability bindings take `generated`, and `web`
  bindings take `record`. A profile of the other class on a research or `web` binding is
  `profile-mismatch`; the `web` refusal is named for the first time, with no vector deciding it.
  The research `answer` profile serves the model's answer; `search` and `page` profiles serve
  the web reads retained with the answer — the links found, the pages read — in the research
  record. The readers are unchanged, and no vector is changed or claimed; the `web` refusal's
  vector waits for a Runner of that kind.
- RFC 0018 and its companion record issue #189, option A (2026-10-16, round 12): a skipped
  source's outcome keeps its five-member claim and status `unknown`; each of its lineage entries
  has status `unknown`. Every source that declares a source parameter, acquired or skipped,
  carries `dependencies`, all declared source parameters in parameter-name order, including those
  that have a value (§§9.2–9.3); the member is absent for the case, a local file and a source that
  declares none. Both readers follow, recompute the thirty-ninth vector's preparation byte for
  byte and give a reading whose binding `matches`. A reader of the accepted text answered
  `preparation-differs` on the Runner's skipped-source bytes and now gives a reading, and the old
  form now gives `preparation-differs`. The Runner is unchanged.
- [RFC 0019](rfcs/0019-exchange.md) stays a Draft and records issue #192, option A: entry format
  version 3 carries checked named-format references and `artifact: {id, version}` under RFC 0021.
  Integer references and kind rules remain; presets stay integer-only. Named identity includes
  the whole canonical document. Changed canonical content under an existing pair is refused
  within a release and across catalog history; identical content is admitted in another entry
  under its kind's rules. Catalog CI fetches tags and reads every previous release's manifest and
  pinned entries as blobs, refusing unreadable history as `artifact-history-invalid`, with no
  form-only fallback. Only a consumer checks form alone when it does not hold the previous
  manifest, reporting `artifact-history-unchecked`.
  Manifest rows are unchanged and upgrade keys remain released entry digests. Reader compatibility,
  publication and binding limits, and catalog and consumer test duties are recorded. The checker
  and fixtures follow in their own pull request on `judgment-pack-exchange`; the Desk's publication
  flow remains separate work. No Core, companion document or conformance corpus changes.
- [RFC 0018](rfcs/0018-dialect.md), round 10 (issue #184): the `record` of an unbound `operation`
  source names the program, as a profile's `adapter.name` and the gateway's receipt carry it, and
  never a catalog's result-contract name. [`spec/dialect.md`](spec/dialect.md) §4.4 gains the
  paragraph, equal to the RFC's; the gateway's catalog version 4 carries the program under
  `adapter`. No vector changes. The review records of rounds 9 and 10 are added under
  [`rfcs/reviews/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/rfcs/reviews)
  as `0018-round-9.md` and `0018-round-10.md`.
- Both readers, `tools/dialect_verify.py` and `tools/dialect-verify-ts/`, now give RFC 0018's
  round-9 receipt answers (issue #185, and with it issue #182): a receipt's `servedAt` or
  `acquisition.observedAt` that is not a string with an instant, a `callIndex` that is not an
  integer at least zero, or a `sessionId` that is not a string is `acquisition-invalid`, before
  the time and session rules ([`spec/dialect.md`](spec/dialect.md) §5.2, check 1, and §11,
  finding 3), in versions 2 and 3, on `operation` receipts, every retained `research` response
  and a research record's own receipt; a `sessionId` is otherwise any string, not held to the
  gateway's token form. `acquisition-stale` now names only a present instant outside the window,
  and `acquisition-sessions` only a well-formed session set that fails the session rule. Before,
  the second reader gave `acquisition-stale` for a time that was not a string and
  `acquisition-sessions` for a malformed `callIndex` or `sessionId`, and both gave
  `acquisition-stale` for a string with no instant. Each reader has a unit case for each answer:
  `tests/test_dialect.py` adds cases on `operation` receipts, signed again over the `valid`,
  `version-3-bound` and `unsigned-parameters` vectors, and on research receipts, and the
  cross-reader test gives both readers all of them, their reports equal byte for byte. The twelve
  staged vectors' answers do not change. The TypeScript reader's README gives §6.4's closed
  condition list in place of the removed "Pointers are …" sentence, and the round-9 receipt rule
  in place of its old receipt readings; RFC 0018's Evidence and Implementation say what is now
  so. No sentence of §§1–14 changes. The correction is one author's, who read both readers, and
  adds nothing to the second reader's independence.
- [RFC 0018](rfcs/0018-dialect.md) and [the dialect](spec/dialect.md) are amended for
  issues #179 and #182 (2026-10-15, round 9): fixture 8 follows RFC 0020's round 2, admitting a
  research stage once a Runner pins its release form and encoding (judgment-pack-runner#88),
  with its recording beside the operation demonstration. Section 4.3 now records that both
  repository readers read `research` since #181; no preparer writes any of the four proposed
  kinds, and no vector holds one. Neither repository reader reads `http`, `sql` or `web`: each
  holds one to its form and refuses it as `kind-unread`; the reference Runner refuses all four
  by name. Reconciliation conditions name only a field entry, its `status`, its `value` or
  `values`, or descendants of `/value` or `/values`, for listed sources and their declared fields
  or this source's declared fields under `/current`; another pointer is `input-malformed`.
  This matches both readers' existing answers. Acquisitions carry exactly the responses the
  research record names, by form, with missing result bytes still `acquisition-missing`;
  `acquisition-unexpected` remains for unexpected source members. Receipt form precedes time
  and session checks: malformed time
  or session members are `acquisition-invalid`, `acquisition-stale` names only a present instant
  outside the window, and `acquisition-sessions` only a well-formed set that fails the session
  rule. `sessionId` is a string, without the gateway's token restriction. The three changed
  answers in versions 2 and 3 are a non-string time, a string with no instant, and a malformed
  `callIndex` or `sessionId`, all now `acquisition-invalid`; no vector's answer changes.
  The receipt positions carry the no-vector markers. The Evidence limits the readers' follow-up
  to those receipt answers and the TypeScript README's quotation of the removed sentence; the
  condition and response decisions need no reader change. The amendment links pull request 183,
  question 14
  uses the preparer link, and the Amended line follows the earlier entries' form. No reader or
  vector changes here, and no research fixture or conformance claim is added.
- Both readers, `tools/dialect_verify.py` and `tools/dialect-verify-ts/`, now read the research
  contract of RFC 0018's round 8 (issue #176) as [`spec/dialect.md`](spec/dialect.md) §§4.3, 4.4,
  5.1, 5.2, 6.4, 9, 11 and 12 define it: a `research` source's requested `fields` and
  `capabilities`, bound directly or through a binding document; the profiles it is bound to, each
  the trusted one of its id and digest, of class `generated`, declaring the model and the
  capability it serves, or `profile-mismatch`; the research record's typed answers, `found`,
  `not-found`, `stale` and `conflicting`, and their citation indices; each retained response
  replayed under its own profile, then the record's own receipt; a plain read's closed list of
  pointers; the reconciliation read, its guards and its combined value; `cites` in the order of
  `sources` and the lineage's `receipts`; and the research maxima of §12, counted before any form.
  Neither refuses `research` as `kind-unread` now. The three answers the amendment said would
  change, change: a research source without `fields` or `capabilities`, and a research record
  without `fields`, are `input-malformed`, and a retained response through a trusted but
  unassigned profile is `profile-mismatch`. Each reader's tests, and the repository's suite over
  both, hold hand-written documents of every new form and refusal, and the two readers' reports
  are equal on each. That agreement is one author's, who extended both from the text; no vector
  holds the kind, no fixture is recorded and nothing is claimable. The companion's Status and RFC
  0018's amendment, Evidence and Implementation say so now, and the Evidence records the readings
  both readers take where the contract's text leaves a choice.
- [RFC 0019](rfcs/0019-exchange.md) is amended by pull request #178 (2026-10-15), still Draft,
  for #166's seven sentences and #172's option A. Entry format version 2 requires `kind`,
  `dialect` or `preset`; a preset is input-only, has no pack or fixtures, and establishes its
  recipe's identity and form, nothing about a preparation. A desk pairs it with a pack locally
  before any run;
  display metadata and README budget suggestions grant no execution permission. The format
  carries no budget; research `constraints` is part of the request, not a budget. The manifest row
  names the kind, with its bounds unchanged. The text names every manifest pin and fixture
  list, the verifier's dialect byte bound, upgrade keys matched to the same entry's earlier
  releases fetched by CI, RFC 0018's full unbound classification and the reader-locator grammar.
  Replay, tag, withdrawal and review checks belong to consumer tests; the producer may require
  tags on `main`, while the consumer checks no ancestry. Catalog implementation belongs to
  judgment-pack-exchange#8. Core, the dialect, RFC 0020 and the conformance corpora are unchanged.
  Pull request #178 also follows RFC 0018's amendments in §1's gateway shapes, Evidence's reader
  status, Implementation item 4's seeds and Compatibility's Accepted status at draft maturity,
  resolves question 8 and updates questions 3 and 7.
  Its nineteen accepted review dispositions name the catalog's and consumer's own form checkers
  for RFC 0018 §§2–8 and 12 as round 8 amends them, for both entry kinds even when replay skips;
  close presets to version 3, unbound eligible sources, three files and no profile requirements;
  state mutual refusal of version-1 and version-2 entries and non-empty manifests; gate research
  publication on #176 and workflow use on RFC 0020's condition (#177); assign the Desk's preset
  duties and coordinator handoff; and clarify budgets, synthetic research fixtures, review
  claims, locators, the index and revision attribution to pull requests #150, #163 and #178.

- [RFC 0020](rfcs/0020-workflow.md) (Draft) and `spec/workflow.md` are amended for issue #174
  (2026-10-15, round 2): research-stage admission is conditional on pinning its release form and
  encoding when a Runner prepares the kind (judgment-pack-runner#88); until then no research
  stage can be frozen or verified. Binding names generated AI and any web profiles under the
  dialect §4.4. Check 1 checks every frozen stage's research profiles and generated-only target
  admissions, with or without a preparation; profile findings map to the workflow's existing
  codes. Question 2 is resolved. The two-stage operation acceptance demonstration remains due;
  an additional research recording follows RFC 0018 §11's fixture 8 plan in the workflow bundle
  layout, once a Runner prepares the kind and the dialect's readers read the contract
  (judgment-pack-spec#176). The contrary dialect admission statement is superseded pending
  judgment-pack-spec#179. Workflow version 1's document form gains no member, and replay still
  checks retained bytes without a model or web call. The companion stays equal to the RFC's
  Specification; no workflow fixture or conformance claim is added.
- [RFC 0018](rfcs/0018-dialect.md) and [the dialect](spec/dialect.md) are amended for issue #171
  (2026-10-15, round 8): research declares bounded typed fields and records found, not-found,
  stale and conflicting answers with retained-response citations. Published recipes name model
  and capability requirements; binding assigns generated AI and web profiles by id and digest,
  with mismatches refused. Reconciliation is a declared rule over research results, retaining
  the prohibition of overlapping targets. The GTM company/person and work-item triage fixture
  lists include changed bindings, retained responses and the workflow's selected parent/child
  case; none is recorded because no Runner prepares `research`. Replay never calls a model or
  the web, and establishes retained bytes, not answer correctness. `evidence` keeps its accepted
  form, an array of non-empty strings. Three accepted answers change: a research source of pull
  request 164's form without `fields` or `capabilities` is now `input-malformed`; a research record
  without `fields` is now `input-malformed`; a retained response through a trusted but unassigned
  profile now gives `profile-mismatch`. This resolves the dialect's research binding question
  deferred by issue #160. Workflow version 1 admits no stage with a research source; RFC 0020's
  contrary binding statements are superseded pending its own revision, with its operation
  construction still due. At that amendment both readers held the superseded research form;
  they read the contract since the entry above. Round 8's twelve accepted findings clarify reads,
  reconciliation guards, citation indices, generated claims and fixture variants; its review and
  dispositions are
  [recorded verbatim][round-8]. No Core, preparation-form or conformance
  change is made, and no vector is claimed.

[round-8]:
  https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/rfcs/reviews/0018-round-8.md

- [RFC 0018](rfcs/0018-dialect.md) is amended (2026-10-15), and
  [`spec/dialect.md`](spec/dialect.md) with it; its status stays `Accepted`. Version 2's
  `operation` reads a gateway source of shape `airbyte`, `mcp` or `http`, as the reference Runner's
  mapping v2 does since its pull request 80: the record's `acquisition.shape` is the profile's; the
  request is a tool call for `mcp`, and for `http` and `airbyte` the request the gateway source of
  that shape takes, held to being an object, to the template rules and to the receipt's commitment,
  not to a set of members (`airbyte` defined and not claimable); and a receipt that attests a page
  is refused whatever the shape. This changes accepted text in two ways: a compatible extension of
  the record kind to every adapter shape, under which every version-2 dialect that was well-formed
  stays so and the nine vectors keep their answers; and one restriction, the refusal of a paged
  acquisition, which changes one answer the accepted text gave: a signed `mcp` acquisition whose
  receipt carried `pageItems` was read and is refused now. The Runner has never prepared one. Version 3 gains the unbound source form, an `operation` that names the catalog platform
  and operation it is read through in place of a profile, with a binding document and the bound
  dialect it yields; it is defined and not claimable, since, at that amendment, no Runner read
  version 3 (the Runner reads it since its pull request 83: see the entry of the eleventh and
  twelfth vectors above). A verifier
  that does not read a dialect's version refuses it, `version-unread`. The Runner's tenth
  preparation vector, `http-shaped-source`, is staged byte for byte beside the nine, and both
  readers, `tools/dialect_verify.py` and `tools/dialect-verify-ts/`, read it to the Runner's answer;
  their extensions are one author's, so for the amendment their agreement is not independent.
- Implementations page and presentation: they say what the runtime and Runner now establish about
  a decision record, as runtime conventions and in the runtime's own wording. The runtime's listing
  names chaining on by default, record signatures in a sidecar with key rotation, checkpoints a
  holder keeps and `jpack audit verify` against them, and RFC 3161 stamps (runtime v0.26.0), and
  v0.27.0's refusal of a signing key another user could replace, with a link to the runtime guide's
  "Checking a trail, and handing over a checkpoint". The Runner's listing names its chain of runs
  and signatures, checked by `verify-run` (v0.5.0), and the gateway's a decision policy that
  requires a signed record (v0.9.0, its ADR-0012). The gateway's top line said "not integrated with
  the runtime"; it now says the gateway runs its sources and receipts them apart from the runtime,
  and that such a policy can hold a write to a record a runtime key it trusts signed. The
  presentation labels its receipt sentences as the gateway's receipt store, unchanged, and gains a
  section on the decision record in runtime ADR-0047's terms: a chain establishes consistency, not
  completeness; a signature, nothing against the key holder; a held checkpoint, existence at
  hand-over if the holder is independent; a stamp, existence by a time, not when a record was made.
  None of this is in JPS, and nothing normative changes.
- The six published demo projects now pass `jpack packs lint`, the check the runtime offers for a
  project's producers. Each demo's `jpack.json` declares, for every fact pointer its pack reads and
  every evidence requirement it declares, the source in the demo's own `mapping/mapping.json` that
  supplies it; these are the runtime's non-normative hints and no pack changes. Each README adds the
  lint to its commands and says what it checks. The demos keep their versions, and their published
  archives change in `jpack.json` and `README.md` only; each demo's manifest records the new digests,
  and the deal demo's archive pin moves with them. Nothing normative changes.
- [RFC 0002](rfcs/0002-judgment-graph.md) (Judgment Graph composition) is amended; it stays a
  `Draft`. The question Study 004 left prior to the others — which seam the format is for — is
  decided: the **dataflow seam**, one decision's outcome consumed as another's input, and the edge
  is not grown toward effect or entitlement constructs. The use intended for it, the seam between
  decisions different parties own, is stated as intended and unmeasured. The one implementation is
  described as it stands: eight graph-specific runtime decision records, first released across four
  versions, with the graph test verb in a fifth, where the RFC named one. Four statements of the
  sketch are corrected or marked as diverging from that implementation — it names a pack by a
  project-local decision id and not by `(id, version)`, pins nothing about a pack in the document,
  and carries one switch, `onUnresolved`, whose meaning is evaluator behavior — and each
  divergence is recorded as a question for the RFC and not settled by adopting either side. Four
  unresolved questions are added: how a node names and pins its pack; whether an upstream verdict
  is co-evaluated or consumed as recorded; whether a per-edge evaluator switch belongs in a
  portable format; and whether a test format is part of the interchange.
- [RFC 0004](rfcs/0004-planner-interface.md) (planner interface) is dispositioned `Rejected`: a
  planner is product, and the specification standardizes no part of one, the narrow selection query
  included. The RFC named this its most likely outcome when it was opened. The record states what the
  rejection rests on — the maintainer knows of no pair of products that has asked for the surface,
  and the reference runtime deliberately leaves selection with the application — and what it leaves
  undecided, including whether a selection query could be portable at all. Nothing normative
  changes; the index, the architecture vision, the FAQ, the site descriptions and
  [RFC 0006](rfcs/0006-evaluator-conformance.md)'s adoption record, which had assigned a question
  to RFC 0004, follow.
- Search metadata descriptions are normalized to 160 characters, conformance-case descriptions now
  name JPS and their layer, and sitemap entries no longer misreport the deployment timestamp as every
  page's content-modification time. Duplicate downloadable JSON under `/artifacts/` now carries an
  `X-Robots-Tag: noindex` response while canonical schema URLs remain available. The deployment guide
  also forbids cloning the intentionally `noindex` preview artifact to live and requires an explicit
  production build plus indexing checks.
- [RFC 0014](rfcs/0014-lineage-record-and-action-binding.md) (the lineage record and the action
  binding) is `Accepted` — the first accepted cross-project record, and a retrospective one.
  Acceptance endorses the record as an account of a design the gateway and the runtime had already
  adopted by their own processes; it confers no authority over them, makes nothing part of JPS, and
  claims no stability. The record's own process question — whether
  [RFC 0000's](rfcs/0000-rfc-process.md) cross-project provision covers a record filed after its
  parts were built — is ruled on, and RFC 0000 now says that it does and on what conditions. Four
  developments since the record was filed on 2026-09-14 are recorded in place. One overtook a
  statement and that statement is struck: the golden-record agreement test, called unbuilt, is
  built for one platform. One stands beside statements that remain true: a second verifier of
  receipt version 3 exists and is neither independent nor clean-room. Two update statements marked
  "at the time of writing": runtime 0.21.0 is released, and the demo's Acts 7 and 8 are merged. The
  descriptions of this directory no longer call it open proposals only.
- **The first evaluator-conformance claim now exists, and the site stops saying it does not.** The
  reference runtime states one for `0.2.0-draft` in its own repository. Four surfaces asserted the
  opposite as present fact and are corrected: the overview (`README.md`), the architecture vision's
  Runtime row, FAQ Q33, and the implementations listing. Each now records that a claim exists and
  where it lives, and none restates any part of it — a partial restatement is what §3.4.1 forbids, and
  the distinction the corrected text carries is that `experimental` on a runtime surface reports
  *stability* and never conformance. The dated records are deliberately not edited: the
  `0.2.0-draft` release notes and its entries below describe what was true at that release.
- Implementations page: added the clean-room Python evaluator as a second listing, with a stated
  caveat that both implementations trace to one maintainer and so corroborate the specification's
  precision rather than evidencing independent interoperability.
- Site ecosystem update: the landing hero now gives Slack and the public project repositories the
  same first-screen prominence as the specification, and a status-labelled project directory links
  the runtime, cloneable demo, gateway, and research repositories without presenting any companion
  tool as normative. The Implementations page now links directly to runtime releases, build and MCP
  guidance, and the runtime's complete conformance claim; records project matrices, experimental
  graphs, opt-in evaluation records, and reviewed-set locking as non-normative runtime behavior; and
  lists the demo and gateway separately as companion projects. It also corrects the stale statement
  that the runtime never produces an outcome: its evaluator produces a disposition from supplied
  inputs, which never authorizes an action or establishes truth, safety, or fitness.
- Architecture vision: recorded that where a pack's *inputs* come from is an open question outside
  this specification, naming the research repositories and the reference gateway — with their stated
  ceiling, byte-lineage rather than truth, carried on the site rather than left to the reader.
- Architecture vision: distinguishes the inline HMAC acquisition proxy from the incompatible
  Ed25519 gateway and adds the portable-derivation and deterministic-admission steps between
  acquisition and evaluation. The page and presentation now state that no runtime consumes these
  formats and that none is part of JPS; the architecture diagram also reflects Core
  `0.2.0-draft`'s evaluator class and a runtime that evaluates as well as validates.
- RFC 0002: the runtime's graph prototype is no longer described as living unmerged on a branch. The
  reviewed commit stays pinned; the surface has since merged, shipped, and grown past it.
- The site now renders `~~struck~~` text as a deletion, as GitHub does. The RFCs correct themselves
  in place — a superseded sentence is struck and a dated note follows it — and the site's renderer
  had no strikethrough, so on five published RFC pages a withdrawn claim appeared unstruck, wrapped
  in literal tildes. A test holds that every strike in an RFC's source is a `<del>` on its page.
- Field guide: a rule's `evidenceRequirementRefs` is now described as what it is, a citation that
  no evaluation step reads. The guide said the rule "relies on" the requirements it names, which
  reads as a gate. It now names the two mechanisms that do gate on evidence: a requirement declared
  `required: true`, and an `evidence-present` condition. Nothing normative changes.
- Field guide: says that an outcome named for human review, such as `manual-review`, is an ordinary
  outcome result that requests no handoff, and that the escalation target is requested only by an
  unresolved or not-applicable result whose reason the triggers name, or by an `escalate` exception.
  Four of the five example packs use such an outcome as their `fallbackOutcome`. Nothing normative
  changes.
- README and Implementations page: the project's desk and jobs runner are listed with the other
  companion projects, as separately governed, non-normative research previews. Neither evaluates a
  pack itself, so neither is listed as an implementation.

[staged-dialect]: https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/dialect

## `0.2.0-draft` — 2026-07-28

The draft that added the evaluator conformance class; its
[release notes](releases/v0.2.0-draft.md) give its scope and limitations.

### Added

- **Core `0.2.0-draft`: the evaluator conformance class.** [RFC 0006](rfcs/0006-evaluator-conformance.md)
  is accepted at draft maturity and lands in the specification: §3.4 defines the class and §3.4.1 the
  single form of claim permitted against it, §§7–8 become normative for that class (and stay
  informative for every other consumer), §8.2 defines the evaluation inputs including the tri-state
  evidence-availability document, §8.3 pins the portable disposition, and §8.4 makes an evaluation
  error something other than a result — in a fixed precedence order where more than one class applies,
  with implementation-defined classes required to use §9's reverse-domain form. §7.4 requires every
  operator of an implementation claiming the class, states that equality of decimal strings is string
  equality and deliberately not decimal-aware, and confines "cannot compare exactly" to JSON numbers
  outside an implementation's exact range — the single seam §8.3 excludes from its byte-agreement
  requirement and §13 leaves open. §3.4.1 freezes the corpus at the release of a `specVersion` and names
  `suiteVersion` as the corpus version a claim must state. §10 raises collection-size and
  evaluation-work limits to a MUST for implementations claiming the class. Document conformance is unchanged, and §3.5's non-claims
  apply to the new class with one narrow, stated exception. Full scope and caveats:
  [`releases/v0.2.0-draft.md`](releases/v0.2.0-draft.md).
- A 20-case **seed** evaluation corpus in [`conformance/evaluation/`](conformance/evaluation/README.md),
  with its own case carrier and four pack fixtures. Thirteen rows are imported from the
  cross-implementation agreement harness — ten over the nine walked RFC 0006 appendix instances,
  counting both variants of instance 7, plus three probes. Seven are constructed here from the
  specification text — reproduced on one of those two implementations, which checks the derivation
  rather than establishing agreement between two of them: the handoff subset rule and
  `state: none`, `no-match` with no fallback, a direct exception escalation in a pack with no
  `escalation` object, and §7.4's ordered comparison including its refusal to coerce a JSON number. It
  is normative for the evaluator class only, version-pinned, and grows by RFC. Its README states its
  gaps: no error rows, no number-representability row (deliberately — that question is open), handoff
  coverage counted row by row, three mandatory operators (`not-equals`, `greater-than`,
  `less-than-or-equal`) with no row, no `literal`, `not`, composite-equality, or fallback-selection row,
  no `suppress-rule` row, no permutation or hostile rows, and the inputs its carrier cannot yet express.
- **The claim's scope is the contract, not the corpus (§§3.4, 3.4.1, 3.5).** An evaluator-conformance
  claim asserts compliance with the whole §§7–10 contract for every input the implementation admits;
  corpus results are required, non-exhaustive evidence of that. A claim must state that every row of the
  named corpus version passed, and a failed row blocks the claim.
- **An erratum mechanism for a frozen corpus** at
  [`conformance/evaluation/errata.md`](conformance/evaluation/errata.md). Only a project-issued, versioned
  erratum can mark a row of a released corpus defective — a claimant cannot — and an erratum edits no row.
  It is in place and empty for `suiteVersion` `0.2.0-draft`.
- **Input preflight (§8.2).** The inputs are admitted before §8 runs, in the order pack, facts, evidence
  availability; an omitted evidence document is the implicit empty object; any violation of §8.2's shape,
  including a non-object evidence input, is `malformed-input`; and because preflight completes before step
  1, an input error can never be outraced by a `not-applicable` result.
- Two optional case members in the evaluation carrier, defined now and used by no row so that later rows
  need no carrier change: `workBudget` (a positive integer of work units, in the units a future accounting
  model will define) and `expectedErrorPhase` (`preflight` or `evaluation`, alongside `expectedErrorClass`
  only).
- A top-level `FAQ.md`; an informative, non-normative architecture-vision page
  (`docs/architecture/vision.md`); a prior-art comparison page (`docs/concepts/comparison.md`); and
  seeded draft RFCs 0001–0005 (pack manifest, Judgment Graph composition, evidence reference,
  planner interface, and pack discovery) that record open design questions without adding anything
  normative.
- Site navigation: a Concepts hub (`concepts/index.html`) gathering the conceptual and reference
  pages, breadcrumbs on every page, and footer links to the Concepts and Project & docs hubs, so
  every page is reachable through structured navigation rather than only through in-prose links.
- Static SVG architecture diagrams (shipped-versus-proposed, the three-property split, and evidence
  sources feeding a pack) on the architecture-vision page, rendered without any JavaScript so the
  strict `script-src 'none'` policy is preserved.
- FAQ: a "Skills, tools, and agent integration" section (with a "Skills and Tools" subsection)
  that explains, honestly, how Judgment Packs relate to tools, agent skills, and `SKILL.md` —
  including when a skill alone is sufficient — with a static SVG integration diagram.
- A `NOTICE` file naming Brian Jin as the copyright holder, included in the release bundle. The
  repository previously identified no owner: `LICENSE` is the unmodified Apache-2.0 text, whose
  appendix is a template rather than a filled-in field. `LICENSE` is deliberately left
  byte-identical to the canonical text so automated license scanners continue to report a clean
  Apache-2.0 match.
- A superseded-draft signpost at `/spec/0.1.0-draft/`, so a versioned URL that citers may already have
  used resolves to the tagged source and the current draft instead of a 404.

### Changed

- Version identifiers move to `0.2.0-draft`: Core prose, the structural schema (`$id` and the exact
  `specVersion` constant), the document-conformance manifest, every example, and every fixture. The
  document format is unchanged, so a `0.1.0-draft` pack is unchanged in representation and
  document-conformance meaning and needs only that one value edited; because the value is exact, an
  unedited pack is not structurally conforming here. Re-declaration is not inert, though: it opts the pack
  into this draft's evaluator semantics, which existed for no consumer under `0.1.0-draft`, and confers no
  conformance on any implementation. The `0.1.0-draft` schema is preserved at
  `schema/judgment-pack-core-0.1.0-draft.schema.json`, and that draft's document-conformance manifest
  schema at `schema/conformance-manifest-0.1.0-draft.schema.json`, both served at the `$id` each was
  published under so a previously cited identifier still resolves. Each preserved file matches the tagged
  `v0.1.0-draft` artifact in every byte except its `$id` member, which was re-pointed to the project's
  neutral domain when the retired pre-publication identifier was withdrawn; `releases/v0.2.0-draft.md`
  publishes the digests of both forms. `conformance/structural/invalid-spec-version.json` now carries
  `0.1.0-draft` as its negative value, which makes the re-declaration requirement a corpus case.
- §8.4's classes are split by phase so the error contract cannot contradict §10: a documented document or
  carrier limit reached while admitting an input is `malformed-input` (§2.1 refuses the document, so
  preflight never admits it), while a collection-size or evaluation-work limit reached during evaluation is
  `resource-exhaustion`. Every error carries exactly one class — a Core class where one applies, otherwise
  a documented implementation-defined class in §9's reverse-domain form.
- `tools/build_release.py` now requires `HEAD` to be the resolved release commit. Artifacts are validated
  from the worktree and archived from the commit, so the gate previously accepted a validated tree and an
  archived tree that were not the same tree.
- The evidence behind the change is two implementations agreeing 13/13. Both trace to one maintainer's
  direction, so that agreement corroborates the semantics rather than independently confirming them,
  and RFC 0000's bar for a *stable* feature is still unmet — carried as a caveat in the RFC's adoption
  record, the release notes, and the corpus README rather than stated once and forgotten.
- Every assertion that evaluator conformance cannot be claimed is now the `0.2.0-draft` truth: the
  class exists, claims are governed by §3.4.1, and no implementation ships a claim with this release.
  The reference runtime's evaluator remains experimental and claims nothing; whether it claims the
  class is a decision for that repository. The site says the same: the implementations listing no longer
  says the runtime does not evaluate rules, and the example guides no longer call a conflict result
  unportable now that §8.3 makes it a portable `unresolved` disposition.

- Renamed the change-proposal process from Judgment Enhancement Proposal (JEP) to Request for
  Comments (RFC); moved `jeps/` to `rfcs/`. The required sections and evidence bar are unchanged.
  The historical `0.1.0-draft` entry below is left as shipped.
- Implementations page: replaced the earlier vendor-branded CLI listing with the vendor-neutral
  `judgment-pack` reference runtime (which inherited that CLI's implementation), linking to its own
  repository, and removed the vendor-branded on-site CLI page. Every page on the site is now
  vendor-neutral, and no page names the retired pre-publication brand.

## `0.1.0-draft` — 2026-07-22

Initial research preview.

### Added

- Core prose specification and Draft 2020-12 structural schema.
- Synthetic expense-approval, software-change, and records-disposition examples.
- A 47-case carrier, structural, semantic, and capability corpus with machine-readable
  expectations.
- A domain-authoring test exercise and focused feedback template.
- Automated repository checks for schema, examples, conformance metadata, links, and fixture drift.
- Public governance, contribution, security, and JEP processes.

### Compatibility

This is the first tagged draft. It makes no compatibility promise for later
`0.x` releases. Pack evaluation is experimental and has no evaluator-conformance class in this
release.

### Known limitations

- No CLI or validator is part of the normative specification release; implementations are separate
  and nonnormative.
- Conformance does not establish factual truth, authority, safety, or operational fitness.
- Runtime facts, evidence transport, result traces, and ordered business-value comparison are not
  portable evaluation contracts in this draft.

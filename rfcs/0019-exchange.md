# RFC 0019: The Judgment Exchange — a shared place for dialects

- Status: Draft
- Type: Exploratory (a cross-project exploratory record — the `judgment-pack-exchange` repository,
  a desk's browse of it; a hosted registry is out of scope (Unresolved question 4); outside JPS)
- Created: 2026-10-14
- Issue: [#142](https://github.com/Judgment-Pack/judgment-pack-spec/issues/142); the dialect an
  entry holds is [RFC 0018](0018-dialect.md)

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **Scope note, load-bearing.** Nothing this record proposes lands in JPS Core, a profile, a
> conformance class, or the dialect's proposed companion document. It is recorded under
> [RFC 0000's](0000-rfc-process.md) cross-project exploratory provision, and each part lands in
> another repository of the project: the entry format, the manifest, the test and the contribution
> rules in the repository
> [`judgment-pack-exchange`](https://github.com/Judgment-Pack/judgment-pack-exchange) (its
> `docs/entry-format.md`, `docs/release-contract.md`, `CONTRIBUTING.md` and `tests/`); a desk's
> browse of the manifest in the [Desk](https://github.com/Judgment-Pack/judgment-pack-desk); a
> hosted registry is out of scope (Unresolved question 4). Acceptance endorses the record as written
> and confers no authority over any of them, each of which adopts its part by its own process. The
> repository has made one such decision already: its `docs/entry-format.md` holds its copy of the
> entry format and says that this record "is normative when it lands", and that where the two
> differ once it lands, "the RFC is right and this page is a bug". That is the repository's
> adoption, made by its own process, and not an authority this record claims.
>
> **The decision this records.** Issue #142 records the maintainer's direction of 2026-10-14: the
> names *dialect* and *Judgment Exchange*, and a shared place for dialects, filed as a record of its
> own once its prerequisites land. The maintainer's decision of 2026-10-15 makes an Exchange any
> repository in the entry format with a manifest a desk can read, for reuse between installations;
> the organisation's repository is the first such catalog. That decision states:
> "public submission, its review load and the hosted registry stay out of scope (RFC 0019's
> unresolved question 4 stays open)".
> The maintainer fixed the entry format for both this record and the repository, which was created
> on 2026-10-14 and scaffolded from it in parallel. §3 gives that format with the maintainer's
> review corrections in [pull request #150][pr-150], the six proposed metadata members, their
> bounds and range grammar in [pull request #163][pr-163], and entry format version 2 in
> [pull request #178][pr-178]. Under the
> [interim review regime](../GOVERNANCE.md#interim-review-regime), the pull request that merges this
> record carries a cross-vendor adversarial review, with the maintainer's disposition of each
> finding.

## Revision in pull request #178: the seven sentences and presets

Pull request #178 records the maintainer's decisions on [issue #166][issue-166] and
[issue #172][issue-172], option A. Section 3 gains entry format version 2 and its required `kind`,
`dialect` or `preset`. A preset carries a recipe without a pack or preparation fixtures; its
identity and form establish nothing about a preparation (§5). The seven sentences are settled in
§§3, 6 and 7: the manifest's pins, the verifier's byte bound, previous-release upgrade keys, the
dialect's definition of unbound, reader locators, the consumer's tests and the producer's branch
rule. The manifest's bounds stay unchanged; the release contract gains the row's `kind`, form
checks and the consumer's preset duties. RFC 0019 stays a Draft.

Pull request #178 also follows RFC 0018's amendments in §1's gateway shapes, Evidence's reader
status, Implementation item 4's seeds and Compatibility's Accepted status at draft maturity,
resolves question 8 and updates questions 3 and 7.

The review's nineteen accepted dispositions fix upgrade history, checker ownership and scope,
binding classification, preset closure, version coexistence, research and workflow gates, budget
wording, revision attribution and consumer duties, with locator, index and fixture corrections.

The catalog at `v0.1.0` records its enforcement in `judgment-pack-exchange`,
`docs/entry-format.md`, `docs/release-contract.md`, `docs/releasing.md` and
`tests/test_entries.py`. Those files are evidence of what it holds today, not a definition this
RFC copies. Its implementation of #178 belongs to [judgment-pack-exchange#8][exchange-8].
Nothing here adds a workflow entry or changes [RFC 0020](0020-workflow.md).

[issue-166]: https://github.com/Judgment-Pack/judgment-pack-spec/issues/166
[issue-172]: https://github.com/Judgment-Pack/judgment-pack-spec/issues/172
[exchange-8]: https://github.com/Judgment-Pack/judgment-pack-exchange/issues/8
[pr-150]: https://github.com/Judgment-Pack/judgment-pack-spec/pull/150
[pr-163]: https://github.com/Judgment-Pack/judgment-pack-spec/pull/163
[pr-178]: https://github.com/Judgment-Pack/judgment-pack-spec/pull/178
[spec-176]: https://github.com/Judgment-Pack/judgment-pack-spec/issues/176
[spec-177]: https://github.com/Judgment-Pack/judgment-pack-spec/issues/177

## Summary

A **dialect** is a pack's terms spoken in a system's ([RFC 0018](0018-dialect.md)): an input
dialect derives a pack's facts and evidence availability from a system's records, and an output
dialect binds a disposition to a write's arguments. An **Exchange** is any repository in the entry
format, with a manifest a desk can read. The organisation's `judgment-pack-exchange` is the first
such catalog, holding the entries the organisation reviews and checks (§4), as the gateway's
catalog holds bindings. The format exists for reuse between installations: import from any catalog,
bind locally and run the same fixtures; export an installation's dialect as an entry. The decision
states: "public submission, its review load and the hosted registry stay out of scope (RFC 0019's
unresolved question 4 stays open)" (§2). A catalog's release contract (§7) holds import to a
tagged state and an update to an explicit, reviewed upgrade.

An entry of kind `dialect` carries its documents, the pack it was written against, its
requirements, source kinds, its licence, its author, one fixed sentence its author asserts, its
fixtures and its verification records. What a published entry establishes is that assertion, under
the review of the catalog that holds it, and that its fixtures hold at the Runner and runtime a
verification record names: nothing about any record's truth, nothing about an operator's intent,
and, for a research source, nothing about the answer's correctness. An entry of kind `preset`
carries an input recipe without a pack or fixtures. Its checks establish the recipe's identity and
form only; a desk pairs it with a pack locally before any run (§7).

Two seed entries are planned, each with its write-back: Azure DevOps work items into a triage pack,
and a Databricks table into a pack. Neither is written or verified. Their verification records wait
on the maintainer's first live checks of the two connections, and their inputs on a source kind the
Exchange's test can recompute.

## Problem

The glue between a system and a pack is rewritten for every deployment, and it is nobody's to
verify.

- A deployment that reads a system into a pack writes a mapping: case parameters, sources pinned by
  the installation's input profiles, derivation rules, admission by class. The reference Runner's
  mapping v2 is that mapping, and RFC 0018's version 2 is the same document. It is written for one
  installation, in the Desk's mapping editor or by hand, and kept there. The next deployment of the
  same pack against the same system writes it again, and no one compares the two.
- A write-back is held by a decision policy the operator writes for a platform (the gateway's engine
  configuration, `decisionPolicy`). The gateway's design note gives worked policies for Azure DevOps
  and Databricks as examples (`docs/design/engine-config.md`, "The write-back platforms"). An
  operator copies one and edits it, and the copy is the operator's.
- Since RFC 0018 a preparation verifier can recompute a preparation from a dialect, a case, the
  acquisitions and the profiles, and hold a record's binding to it. A verifier needs a dialect and
  fixtures to run it on. No place publishes a dialect with fixtures, a licence and its author's
  stated claim, so that a second party can run it before relying on it.

The Desk's inputs and the gateway's policies have the format but no shared place. The Desk is to
produce the dialect format from its inputs (Desk #398), so that "a dialect authored in the Desk can
be published to the Judgment Exchange later". The research line already says that "Marketplace
recipes should carry mappings and connector requirements, not credentials or a redistributed
prospect database" (Desk #369), and that "A portable recipe can be reused with a compatible
provider after reviewing the mappings, without sharing credentials or republishing a prospect
database" (Desk #371).

Affected users: an operator who would rather adopt a reviewed dialect than write one; a pack author
who wants a pack read the same way across deployments; a counterparty or an auditor who holds a
preparation and wants the dialect it was made with; and a second reader of RFC 0018, which needs
fixtures its own author did not write.

## Evidence

**What exists.** The first account below records the scaffold of 2026-10-14; the revision note and
the update following it distinguish the current readers from that original pin.

- **The format.** [RFC 0018](0018-dialect.md), the dialect, landed as a Draft in #144 (merge
  commit `f821757`). Version 2 of the dialect document is the Runner's mapping v2 byte for byte;
  version 3 proposes source kinds `http`, `sql`, `web` and `research`, defined and not claimable;
  the output side is the gateway's decision policy, by reference. Its first reader,
  `tools/dialect_verify.py`, reads dialect version 2 and source kind `operation`, and refuses every
  other source kind as `kind-unread`.
- **The vectors.** The Runner's nine preparation vectors are published (Runner #75, closed by
  Runner pull request 77, merged as `82116bf`, released in Runner v0.10.0) and staged byte for
  byte in [`conformance/dialect/`][dialect-vectors]. They are the pattern an entry's fixture
  follows: the dialect, the case, the acquisitions, the profiles, and the preparation's exact
  canonical bytes, which a second reader recomputes.
- **The output side.** A gateway decision policy holds a write to its decision record by `bind`
  (gateway ADR-0011), `fix` and `closed` (gateway #258, ADR-0016, released in gateway v0.14.0),
  and `requireSignedRecord` (gateway ADR-0012). One limit is documented and open: a policy does
  not hold a container's shape, which the worked Azure DevOps policy shows (gateway #267).
- **The catalog's manner.** The gateway's [`catalog/README.md`][gateway-catalog] holds the
  bindings the engine ships, one hand-maintained file per platform. A configuration pins the file
  it uses by digest, "so a catalog update never silently changes what a running engine reaches";
  "every licence is copied from the artifact's own statement for that version, never assumed";
  tests hold each file to its shape. A no is recorded as a decision: no catalog binding of the
  Azure DevOps local server (gateway #259), and no `write` operation for `postgres`, since raw SQL
  is no write tool (gateway #260).
- **The browse pattern.** The gateway's [`docs/design/connection-catalog.md`][connection-catalog]
  is how a desk reads what a companion offers: one versioned document, read within bounds (five
  seconds and 32 KiB), its version and shape validated before display, unknown identifiers never
  executed, and no fallback to a guessed catalog. "The catalog is not an extension loading
  mechanism."
- **The repository.** `judgment-pack-exchange` was created on 2026-10-14 and scaffolded from the
  entry format in its first commit, `b516dd7`; its CI job, `entries`, passed on that commit. It
  holds no entries (Implementation).

**The prerequisites, as they stand on 2026-10-14.**

- RFC 0018 landed as a Draft (#144), with the Runner's vectors staged. It is not accepted:
  acceptance waits on a reader written from its text by someone other than its author, agreeing on
  the vectors, after a comment period (issue #141). The first reader in this repository,
  `tools/dialect_verify.py`, is the text's author's; the second, `tools/dialect-verify-ts/`, was
  written from the text alone by a different author and added in #145 (RFC 0018's Evidence).
- The vectors are published: Runner #75, in Runner v0.10.0.
- Output dialects are expressible: gateway #258, in gateway v0.14.0. The gateway publishes no
  policy vectors, and RFC 0018 defers the output side's vectors to a later RFC.
- The first live checks of the Databricks and Azure DevOps connections (gateway v0.13.0) are
  pending. The gateway's tests of both answer from in-process servers, and its live checks run only
  where an operator names a workspace or an organisation. The seed entries wait on these checks.

**What does not exist.** No entry, no verification record, no desk's browse, no hosted registry, no
independent reader, and no live check of either connection. The record is filed before the first
entry, so that the format and the governance are visible before any entry is reviewed against
them.

**Since the version-3 staging.** RFC 0018 is Accepted and its companion is
[`spec/dialect.md`](../spec/dialect.md). Both specification readers read version 3 and its unbound
operation form, held by the Runner's two staged version-3 vectors. They still hold the research
form superseded by round 8 until its follow-up implementation; no research vector is recorded. The
catalog's `v0.1.0` tests still describe their older pinned verifier. The rules below use RFC 0018
§§4.3 and 4.4 as amended in round 8, not the catalog's temporary reading (#166).

## Specification

### 1. The names

A **dialect** is a pack's terms spoken in a system's (RFC 0018 §1).

- An **input dialect** derives a pack's facts and evidence availability from a system's records,
  through any source kind RFC 0018 defines: a gateway source of shape `airbyte`, `mcp` or `http`
  (`operation`), a file the operator selected (`selected-file`), and, proposed for version 3, an
  HTTP request (`http`), a SQL statement on a connection (`sql`), a public page (`web`) and an
  AI-assisted research recipe (`research`). It is RFC 0018's dialect document.
- An **output dialect** binds a disposition to a write's arguments: RFC 0018 §10's output side, in
  the gateway's decision-policy form.

An **Exchange** is a catalog of dialects in the entry format (§3), with a manifest a desk can read
(§2). A binding says how an engine reaches a system; a dialect says how a pack reads that system's
records, or how a disposition becomes that system's write. An **entry** holds a dialect as kind
`dialect`, with a pack, or as kind `preset`, a recipe without a pack. The **Judgment Exchange**,
the organisation's `judgment-pack-exchange`, is the first such catalog.

### 2. Where it lives

**The maintainer's decision of 2026-10-15**, on issue
[#142](https://github.com/Judgment-Pack/judgment-pack-spec/issues/142): an Exchange is any
repository in the entry format with a manifest a desk can read. The organisation's
`judgment-pack-exchange` is the first such catalog, holding the entries the organisation reviews
and checks (§4), in the manner the gateway's catalog holds bindings. It is not a place users upload
to. The decision states: "public submission, its review load and the hosted registry stay out of
scope (RFC 0019's unresolved question 4 stays open)". The format exists for reuse between
installations: import from any catalog, bind locally, run the same fixtures; export an
installation's dialect as an entry.

**A catalog's manifest.** A desk browses it through the connection-catalog pattern: it reads one
document within bounds, holds it to its shape before showing anything, holds each entry it fetches
to the manifest's digests, runs nothing an entry holds, and falls back to no guessed manifest when
it cannot read one. §7 states what a release pins and what a consumer verifies before offering an
entry for import. The same entry format and fixtures let an installation publish a catalog of its
own; publishing there requires no upload to the organisation's catalog. The organisation's review,
contribution rules and recorded decisions (§6) govern its catalog, and do not make it the reviewer
of every other catalog.

**A hosted registry** is out of scope (Unresolved question 4). If the product warrants one, it could
serve a catalog's manifest and files:
the same bytes and digests, with listing, search and download at a stable address. The repository
would remain where its entries are written, reviewed, pinned, verified and declined. A consumer
would still hold each file to the release it chose; another manifest is detected only if the
consumer pins it by other means. Whether to host one, who would run it, and how a desk would pin
its identity remain open (Unresolved questions 1 and 4).

### 3. The entry format

The maintainer fixed the original format for both this record and the repository. The format is
that of any catalog — a repository in it with a manifest a desk can read — and exists for reuse
between installations. This section includes the maintainer's correction to the original's last
sentence on review (finding 2), scopes review to the catalog that holds the entry, and includes
the `output` member, the `output.json` file and the manifest's `outputDigest` added by the
maintainer's decision on exchange issue #2 in pull request #150 (Unresolved question 6); #163's
additions follow the original format below. Pull request #178 adds entry format version 2:
version 1 with a required `kind` member, `dialect` or `preset`, and the conditional members below.
Kind `dialect` retains the pack and fixture rules of version 1; kind `preset` has direction
`input`, omits `pack` and `fixtures`, and holds no fixture directory. Its required `verification`
is `[]`: no preparation was verified.
It has a `dialect` member and `dialect.json`, and no `output` member or `output.json`.

A missing or unknown `kind`, a wrong direction for a preset, a pack or fixtures on a preset, or a
non-empty preset `verification` refuses the entry. A version-1 reader refuses `entryVersion: 2`;
it must not infer a pack or a verification from a preset. A version-2 reader refuses a version-1
entry and a version-1 manifest: their closed forms lack the required `kind`. Conversely, a
version-1 reader refuses the version-2 manifest's rows, whose `kind` it does not admit. The empty
manifest, `[]`, has no rows and fits both forms. Entry format versions are separate from dialect
document versions: a version-2 entry of kind `dialect` may declare `dialectVersion` of 2 or more,
as the members list permits; kind `preset` requires exactly 3. Declaring a version does not make
it readable by a form checker or verifier. A reader refuses an entry format it does not implement.

A preset's `dialect.json` is a version-3 dialect document, held to the whole document form of
RFC 0018 §§2–8 and 12 as round 8 amends them, including version 3's one-spelling rule. Every
source that has an unbound form under §4.4 is unbound. Sources may be `research` under §4.3:
fields, model and capability requirements travel with the recipe; AI and web profile assignments
belong to local binding. A preset's directory holds exactly `entry.json`, `dialect.json` and
`README.md`, with no other file or directory; it holds no binding document. Its `requires` names
no profile. A preset supplies no preparation, acquisition or workflow. The catalog checks its
document's form and digest and the scans only (§4); it never runs the recipe or treats those
checks as preparation verification.

An **entry** is one directory `entries/<publisher>/<name>/` holding, as separate files with these
names:

- `entry.json` — a closed JSON object: `entryVersion` (`2`); `kind` (`"dialect"` or `"preset"`);
  `id` (`<publisher>.<name>`, lower-case letters, digits, `-` and `.`); `title`; `direction`
  (`"input"`, `"output"` or `"both"`); `pack` (required for kind `dialect`, absent for `preset`; an
  object: `id`, the pack's id, an absolute URI as Core §4 makes it, and either `versions`, a
  version range, or `digests`, an array of the pack digests the dialect was written against);
  `dialect` (an object: `path`, always `dialect.json`; `dialectVersion`; `digest`, the SHA-256 of
  the dialect document's canonical bytes as RFC 0018 defines them; required for direction `input`
  and `both`, absent for `output`); `output` (an object: `path`, always `output.json`;
  `outputVersion`; `digest`, the SHA-256 of the output document's canonical bytes as RFC 0018 §10
  defines them; required for direction `output` and `both`, absent for `input`); `requires` (an
  object, members optional: `inputProfile` by digest, `connectionProfile` by digest, `platform` by
  catalog binding name for an output dialect); `sourceKinds` (the source kinds the dialect uses,
  from RFC 0018's list); `licence` (an SPDX identifier); `author` (a handle or organisation name
  as the author chooses to be named; never required to be a personal name); `assertion` (the one
  fixed sentence the format gives: that the author asserts these rules derive these facts and this
  evidence-availability from records of that shape, or these arguments from that disposition, and
  asserts nothing about any record's truth); `fixtures` (for kind `dialect`, an array of `{name,
  path, preparationDigest}`; absent for `preset`); `verification` (an array, empty for `preset`
  and otherwise empty until verified, of `{date, runner, runtime, readers, result}` where
  `readers` names the preparation verifiers that agreed and `result` is `"agree"`).
- `dialect.json` — the dialect document in RFC 0018's format; present exactly when `entry.json`
  has a `dialect` member.
- `output.json` — the output dialect in RFC 0018 §10's form; present exactly when `entry.json` has
  an `output` member.
- `fixtures/<name>/` — for each fixture, the recorded source records (as the Runner retains them)
  and `preparation.json`, the exact canonical bytes the dialect must produce from them; for a
  `research` source, the retained responses and research record under RFC 0018 §4.3.
- `README.md` — what the dialect is for, in the publisher's words; no credentials, no personal
  data.

The repository root holds `manifest.json`, an array of closed rows with `id`, `kind`, `path`,
`entryDigest`, `fixtures`, and `dialectDigest` and `outputDigest` by direction, pinning each entry
by the SHA-256 of its `entry.json`, `dialect.json` and `output.json` bytes, in `id` order;
`dialectDigest` is present exactly when the entry has a dialect document and `outputDigest`
exactly when it has an output document; a test holds every entry to the manifest and every fixture
to its `preparationDigest` by running the specification's preparation verifier over it. A preset
row has `fixtures: []` and no `outputDigest`; its `kind` equals the entry's. Section 5 states what
each entry kind establishes under the holding catalog's review; neither establishes truth.
CI refuses recognised credential shapes and local paths; a maintainer must refuse credentials and
personal data in every file of an entry before merge, recipe literals and receipt metadata
included; and the scan's silence proves nothing.

**Authoring metadata, proposed by pull request #163.** Pull request #163 added
`description`, `compatibility` and `upgrade`, as
[exchange #6](https://github.com/Judgment-Pack/judgment-pack-exchange/issues/6) requests. They are
optional members of `entry.json`, included in its `entryDigest` when present. `description` says
what the entry is for; `compatibility` names the desk and runner releases its author says it fits;
`upgrade` gives review notes keyed by the previous entry's digest, the manifest's `entryDigest`,
not a dialect digest. These are authoring statements, not verification records or permissions.

The six metadata members below, their bounds and the compatibility-range grammar came from #163.
RFC 0019 defines the format and the exchange enforces it: where its page differs once
this RFC lands, the page is a bug, as the exchange's adoption rule states. The catalog's `v0.1.0`
text and tests hold those additions since exchange #6; pull request #178 settles the upgrade keys'
meaning and the checks that establish it (#166).

Each `upgrade` key equals the `entryDigest` of the row with this entry's `id` in the manifest of
some release of this catalog lower in tag order (§3's three integer components) than the release
being made. The catalog's CI fetches the catalog's tags and refuses a key found in none of those
rows. A catalog with no earlier release admits no `upgrade`. A pull request is compared against
the releases that exist when it is checked. For this history check, CI reads the earlier
manifest's rows' `id` and `entryDigest` whatever its form, including version 1; it does not import
that manifest as version 2. A digest of unpublished intermediate bytes or another entry's bytes
is not such a key. A verification record changes `entryDigest`, so upgrade notes name the
released entry's stored bytes, even when its dialect is unchanged.

**The members.** Every object is closed. Members are required unless stated otherwise; conditional
members are absent outside their condition. The following list retains the original types and
bounds, with version 2's `kind` and its conditional pack and fixture rules. All members, including
integer values and release tags, fit within the finite file bound below:

- `entryVersion`: integer, exactly `2`.
- `kind`: string, exactly `dialect` or `preset`.
- `id`: string, 3 to 128 characters, matching `^[a-z0-9]+(\.[a-z0-9-]+)+$`; equal to the entry's
  path under `entries/` with `/` read as `.`. The path rule below splits at the first dot.
- `title`: string, 1 to 200 characters.
- `description`: optional string, 1 to 4096 characters.
- `compatibility`: optional closed object of exactly `desk` and `runner`. Each is a string of 1 to
  64 characters, a release tag or range as below. `desk` names releases of a desk that reads
  catalogs; `runner` names Runner releases.
- `upgrade`: optional object of 1 to 32 members. Each key is a `sha256:` digest of a previous
  release's `entry.json` stored bytes, as above; each value is a string of 1 to 2048 characters, a
  note for review when moving from that entry digest to this entry.
- `direction`: string, `input`, `output` or `both`; exactly `input` for `preset`.
- `pack`: closed object, required for kind `dialect`, absent for `preset`; exactly `id` and one of
  `versions` and `digests`. `id` is an absolute URI (Core §4), at most 2048 characters. `versions`
  is a string of 1 to 64 characters in the pack's own versioning; its range syntax stays
  Unresolved question 2. `digests` is an array of 1 to 16 `sha256:` digests.
- `dialect`: closed object for directions `input` and `both`, absent for `output`; exactly `path`,
  `dialectVersion` and `digest`. `path` is the string `dialect.json`; `dialectVersion` is an
  integer of 2 or more, exactly 3 for a preset, equal to the document's `version`; `digest` is a
  `sha256:` digest.
- `output`: closed object for directions `output` and `both`, absent for `input`; exactly `path`,
  `outputVersion` and `digest`. `path` is the string `output.json`; `outputVersion` is an integer
  of 1 or more, equal to the integer the document's `outputVersion` spells; `digest` is a
  `sha256:` digest.
- `requires`: closed object whose members are optional: `inputProfile` and `connectionProfile`,
  each a `sha256:` digest, and `platform`, a string of at most 64 characters matching
  `^[a-z][a-z0-9-]*$`. For a preset, `inputProfile` and `connectionProfile` are absent.
- `sourceKinds`: an array of 1 to 16 distinct strings, empty for `output`; each a source kind
  RFC 0018 §4 lists for the document's `dialectVersion`. A version above 3 uses version 3's list
  until a later RFC defines more. This list does not make a version readable by a verifier.
- `licence`: one SPDX licence identifier matching `[A-Za-z0-9][A-Za-z0-9.+-]*`, or a `LicenseRef-`
  form of that grammar, at most 64 characters; no compound licence expressions.
- `author`: string, 1 to 100 characters.
- `assertion`: string, the fixed sentence below, byte for byte. For a preset it remains the
  author's statement; no preparation or pack fit is verified by it (§5).
- `fixtures`: required for kind `dialect`, absent for `preset`; an array of 1 to 64 closed objects,
  empty for `output`. Each has exactly `name`, `path` and `preparationDigest`. `name` is a string
  of at most 64 characters matching `^[a-z0-9]+(-[a-z0-9]+)*$`, distinct within the entry; `path`
  is `fixtures/<name>`; `preparationDigest` is a `sha256:` digest.
- `verification`: an array of at most 32 closed objects, empty until verified; exactly `[]` for
  `preset`. Each record has exactly `date`, `runner`, `runtime`, `readers` and `result`. `date` is
  a string, a day in `YYYY-MM-DD` form; `runner` and `runtime` are release-tag strings in the
  grammar below; `result` is exactly the string `agree`.
- `verification[].readers`: an array of 1 to 8 strings, each at most 200 characters, in the
  reader-locator grammar below.

**Reader locators** (#166). Each is `<owner>/<name>/<path>@<commit>`. Owner and name are each 1 to
100 characters of `[A-Za-z0-9_.-]`. The path has one or more `/`-separated segments, each matching
`[A-Za-z0-9_.-]+`, with no empty, `.` or `..` segment. The commit is 7 to 40 lowercase
hexadecimal digits. The last `@` separates the commit from the locator. The whole locator's
200-character bound still holds; a wrong form or an exceeded bound refuses the verification record
and its entry.

`entry.json` and `README.md` are each at most 64 KiB, and a fixture directory at most 16 MiB;
`dialect.json` is at most 131,072 bytes, RFC 0018 §12's bound. When CI reads a fixture, it relies
on the pinned preparation verifier to hold that bound, refusing the reading as `input-over-bound`
if exceeded. For fixture replay, the catalog holds no separate byte check. A skipped fixture
establishes no verifier byte check. Independently, the catalog's own form checker, written to
RFC 0018's text, checks the whole document form of §§2–8 and 12 as round 8 amends them, including
that byte bound, for each `dialect.json` of either entry kind, even if every fixture is skipped.
A malformed document, a bound exceeded, or a version or source kind the form checker does not
read refuses the entry. Passing a digest and scan alone cannot stand in for this form check.
The specification's preparation verifier is not used for a preset: it requires fixture inputs
and a binding document for unbound sources. A research preset therefore waits for a form checker
that reads round 8; the specification readers' support is [judgment-pack-spec#176][spec-176],
which the catalog's checker follows through exchange #8. Every object is closed: a member the
list does not give is refused. A member name given twice in one object is refused, as Core §2.1
refuses one. The 64 KiB file bound governs even when each member is within its own bound; the maxima
are not a promise that all maximum-length values fit together.

**Compatibility ranges.** A release tag has the form
`^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$`, as a verification record's tags do.
A compatibility value is either one such tag, naming that release alone, or
two comparisons: `>=` followed by the lower tag and `<` followed by the upper tag, with exactly
one space between them, `>=v0.10.0 <v0.11.0`, for example. The lower bound is inclusive and
the upper bound exclusive; tags are ordered by their three integer components, and the upper
bound must exceed the lower. No other range syntax is admitted. An absent `compatibility` makes
no compatibility statement; an absent `upgrade`, or no note for the previous digest, supplies no
upgrade guidance. None of these absences approves an import or an upgrade (§7).

**Manifest form, specified by #163 and amended by #178.** `manifest.json` is at most 1 MiB
(1,048,576 bytes) and contains at most 1,024 rows. Each row is a closed object with exactly `id`,
`kind`, `path`, `entryDigest`, `fixtures`, and `dialectDigest` and `outputDigest` when the entry's
direction requires them. Duplicate member names are refused. Rows have distinct `id` values, ordered
by those ids as byte strings (their UTF-8 bytes). The `id` has the grammar and bound in the
members list; `kind` is `dialect` or `preset` and equals the entry's; each digest has the form
given below. The row's `path` is exactly `entries/<publisher>/<name>`, without a trailing slash:
split `id` at its first `.` for `<publisher>` and `<name>`, leaving any further dots in `<name>`.
A path that differs, or an entry whose `id` differs from the row's, is refused. There is exactly
one row per entry directory in the release's tree and one entry per row.

The row's `fixtures` is an array of closed `{name, files}` objects, one per fixture in
`entry.json` in the same order (empty for an output-only entry or a preset, whose `entry.json`
omits `fixtures`). A wrong or mismatched `kind`, or a non-empty preset fixture list, refuses the
row. Each `name` equals that fixture's name, and `files` is an array of 3 to 5 distinct strings
listing its complete file set by basename. `case.json`, `profiles.json` and `preparation.json` are
required; `sources.json` is optional; `binding.json` is required exactly when the entry's dialect
has an unbound source under RFC 0018 §4.4, including round 8's research form:

- An `operation` is unbound when it has all of `platform`, `operation`, `shape` and `record`,
  and neither binding member `profile` nor `profileDigest`. Its bound form has both binding
  members and none of those four catalog members. Some but not all of either set, a mixture of
  the two forms, or neither complete form is `input-malformed`.
- A `research` source is unbound when it has none of the binding members `profile`,
  `profileDigest` and `webProfiles`; its bound form has all three. Some but not all of that set,
  or any operation catalog member, is `input-malformed`.

The catalog's own test checks this classification and the binding members' forms for every
fixture, whether or not the preparation verifier reads it (§4). It also checks each binding
document's form, bound, dialect digest and exact source assignments under RFC 0018 §4.4. A partial
or malformed binding document is refused by the catalog. A fixture lacking a required binding
document, or carrying one when the dialect has no unbound source, is refused. Both specification
readers read version 3's unbound operation form; their round-8 research implementation is still
due (#176). The catalog's temporary operation-only classification is retired (#166); correcting
its `tests/fixtures/unread-version-entry` example belongs to judgment-pack-exchange#8.
No other file is admitted in a fixture directory. A consumer knows from this list which files to
fetch under `<path>/fixtures/<name>/` over any transport; a listed file that
cannot be fetched is a failure, not an absent optional file. The consumer checks that the list
equals the file set in the release's tree. The fixture lists landed through exchange #6; #178
adds the row's `kind` through exchange #8, leaving the manifest's bounds unchanged.

**How the format is spelled.** The assertion's words, digests and fixture files follow. Pull
request #163 defined the closed fixture file set and named its `binding.json`.

- **The assertion.** `assertion` is exactly this sentence: "The author asserts that these rules
  derive these facts and this evidence-availability from records of that shape, or these arguments
  from that disposition, and asserts nothing about any record's truth."
- **Two documents.** An entry's `direction` follows from the documents it holds: `input` holds
  `dialect.json`, `output` holds `output.json`, and `both` holds both, each with its own digest in
  `entry.json` and in `manifest.json`; a document the direction does not give is refused, as is
  one it gives and the entry lacks. `output.digest` is the digest of the output document's `canon`
  bytes (RFC 0018 §1, §10); `outputDigest` is of the file's bytes, as it lies.
  `output.outputVersion` is an integer equal to the integer the document's own `outputVersion`
  spells, which RFC 0018 §10 writes as the string `"1"`. Output fixtures are held by their digests
  only until the gateway publishes policy vectors (RFC 0019, unresolved question 5): an output
  document has no preparation for a verifier to recompute, so an entry of direction `output` holds
  `sourceKinds` and `fixtures` as empty arrays, and an output document is pinned by
  `output.digest` and the manifest's `outputDigest` alone.
- **Digests.** Every digest is written `sha256:` followed by 64 lower-case hexadecimal characters,
  as RFC 0018 §1 writes one. `dialect.digest` is the digest of the published document's `canon`
  bytes (RFC 0018 §1, §2). A preparation carries the bound dialect's digest as `mappingDigest`
  (§9.1 there); binding an unbound document changes that digest (§4.4 there). A preset has no
  preparation or `preparationDigest`. The manifest's `entryDigest` and `dialectDigest`, and a
  fixture's `preparationDigest`, are digests of the files' bytes as stored. A `dialect.json`
  stored in bytes other than its `canon` form, indented say, has a `dialectDigest` other than its
  `dialect.digest`, and each is held to its own definition. `preparation.json` holds the
  preparation's canonical bytes (RFC 0018 §9.5), so its `preparationDigest` is the preparation's
  digest.
- **A fixture's files.** A fixture directory holds `case.json`, the case document; `sources.json`,
  the acquisitions, optional and absent for a case-only fixture; `profiles.json`, the input
  profiles the fixture was prepared under; `preparation.json`; and, exactly for a dialect with an
  unbound source, `binding.json`, the binding document the fixture was recorded under (RFC 0018
  §4.4). This file set is closed and listed in the manifest row as above. The first four names
  follow the Runner's vectors; `binding.json` names RFC 0018 §4.4's document. A verifier reads
  these inputs under RFC 0018 §11, with the dialect taken from the entry's `dialect.json`. A
  fixture's `path` is `fixtures/<name>`, relative to the entry's directory. For a `research`
  source, `sources.json` holds the research record as the acquisition's result under RFC 0018
  §4.3. Each retained response is held by its own receipt and digest; the whole record's receipt
  is present only when it came through a gateway source. Without one, fields and response
  membership and order remain the caller's assertion. No whole-record commitment is invented.
- **The repository's own copy.** The repository's `docs/entry-format.md` adopts this RFC as the
  format's definition when it lands: where the page differs, the page is a bug (the scope note).
  Its `v0.1.0` page and tests hold exchange #6's metadata and fixture lists. Pull request #178's
  changes follow through exchange #8; the exchange enforces the format defined here.

### 4. The Exchange's test

A catalog's test, run on every push and pull request in its repository, holds:

- **the manifest to the entries**: one row for each entry directory and one entry for each row, in
  `id` byte order, with §3's bounds, closed rows, matching entry kinds, paths and fixture lists,
  and `entryDigest`, `dialectDigest` and `outputDigest` over the files' bytes, the last two
  present as §3 gives them;
- **each `entry.json` to the members list (§3)**: each member's type, requiredness, grammar and
  bound, every object closed, and the `assertion` the fixed sentence exactly; upgrade keys are
  checked against the same entry's rows in earlier releases' manifests, fetching tags as §3
  requires, with no form-only fallback;
- **each `dialect.json` to the whole document form of RFC 0018 §§2–8 and 12 as round 8 amends
  them**, by the catalog's own form checker (§3), for both kind `dialect` and kind `preset`,
  whether or not any fixture is replayed;
- **each fixture's source classification and binding document to RFC 0018 §4.4**, by the
  catalog's own test under §3, including partial binding members, the required or forbidden
  `binding.json`, and that document's form, bound, dialect digest and exact source assignments,
  whether or not the preparation verifier reads the fixture;
- **`dialect.digest` and `output.digest`** to their documents' `canon` bytes, and each fixture's
  `preparation.json` to its `preparationDigest`;
- **each fixture to the specification's preparation verifier**, `tools/dialect_verify.py` at the
  specification commit the repository's CI pins: the test gives it the entry's `dialect.json` and
  the fixture's files, and requires a **reading** — no refusal and no finding (RFC 0018 §11) —
  whose digest equals the fixture's `preparationDigest`. No record is given, so the reading's
  binding is `not-checked`, and a fixture says nothing about any runtime record; and
- **every file to a scan** that refuses the common shapes of a credential, a token and a key, and
  a local path, before anything is merged. A scan's silence is not a finding that none is there:
  credentials and personal data in every file are a maintainer's to refuse before merge (§3).

**A preset.** The catalog checks its entry and manifest form, the whole document form of RFC 0018
§§2–8 and 12 as round 8 amends them, its file and canonical digests, and the same scans.
There are no fixtures to replay and no preparation-verification record to add. A form, digest,
bound or scan failure refuses it. These checks establish only the recipe's identity and form.

**A fixture the verifier cannot recompute.** After the catalog's form check passes, a fixture
whose source kind the specification's verifier refuses as `kind-unread` is held by its digests
only: the test skips recomputation and says why. The same applies to an unread dialect version,
identified by the verifier's unread-version detail; every other refusal fails the entry.
The readers currently refuse `http`, `sql` and `web` as `kind-unread`, but round-8 `research`
as `input-malformed`: they still read the superseded research form. An entry with a round-8
research source cannot be published while the readers refuse it. Once #176 lands and the catalog
pins a reader of round 8, its research fixtures are verified as any other fixture; no recipe is
re-executed. Both readers already read version 3's operation form. The catalog at `v0.1.0` pins
an older verifier; its supported versions and source kinds follow that pin. An unread version or
source kind is reported by name, never as a successful replay. A skipped fixture establishes
only that its bytes were recorded and pinned; the independent form check still holds the
dialect's document form (Unresolved question 3).

### 5. What an entry establishes, and what it does not

An entry of kind `dialect` establishes, to a reader who performs the checks in §7:

- **The author's assertion**, the format's one sentence (§3): that these rules derive these facts
  and this evidence availability from records of that shape, or these arguments from that
  disposition. It stands under the review of the catalog that holds the entry. In the
  organisation's catalog that means the maintainer's read of every entry and, for a material entry,
  a recorded cross-vendor review round with the maintainer's disposition of each finding (§6).
  Another catalog's review is its own; the organisation's review does not extend to its entries.
- **That its fixtures hold at the named Runner and runtime**, as each verification record states:
  on its date, each reader it names recomputed every fixture's preparation from the entry's dialect
  and the fixture's files, byte for byte equal to `preparation.json`. For those fixtures, that is
  what RFC 0018 §13 says a recomputed derivation establishes: these facts and this evidence
  availability were derived from those bytes by these rules.

A **preset** establishes the recipe's identity and form only: the published bytes have their
stated digest and the document has the form of those sections: the whole document form of
RFC 0018 §§2–8 and 12 as round 8 amends them (§§3–4 here). Its fixed assertion is the author's
statement under the catalog's review, not an established derivation. A preset establishes nothing
about any preparation, pack fit, acquisition or answer. Its `verification` stays empty; no
preparation fixtures exist to support a claim. A desk pairs it with a pack locally before any run.
The format carries no budget; a README may describe one. A research source's `constraints` is
part of the request and is not a budget. Display metadata and README budget suggestions grant no
execution permission, for either entry kind.

Neither entry kind establishes:

- anything about any record's truth: the stance Core §6.3 takes of a source and the gateway's
  catalog takes of a binding;
- that the dialect is right for the pack, or reads what its author meant (RFC 0018 §13), or fits
  any record, or any release of the system, the pack, the Runner or the gateway, other than its
  fixtures and the releases a verification record names;
- anything about an operator's intent, or that an operator who adopts the entry may read or write
  what it names;
- for a `research` source, anything about the answer's correctness: receipts hold each retained
  response's bytes, and the whole research record only when its own receipt is present. Response
  receipts alone do not commit that whole record. RFC 0018 §13 states that limit;
- for an output dialect, that a write its policy admits is the right write: the gateway holds a
  write to its policy at the moment of the write, and says what that establishes; and
- for a fixture held by its digests only (§4), anything beyond that its bytes were recorded.

### 6. The repository's rules

These are the rules of the organisation's `judgment-pack-exchange` catalog (§2).

- **Contributions.** The contribution rules are the other repositories': a DCO sign-off on every
  commit, one review round, and the thank-you bot.
- **Review.** A new entry and a changed dialect are material; a change to a README or a title is
  not; any other change is classified on its pull request, out loud. One entry per pull request. A
  material change gets a maintainer's read and one recorded cross-vendor round, with the
  maintainer's disposition of each finding, on its pull request, under the specification's
  [interim review regime](../GOVERNANCE.md#interim-review-regime).
- **Pinning.** The manifest records `kind` and pins each entry by `entryDigest`, `dialectDigest`
  for directions `input` and `both`, `outputDigest` for `output` and `both`, and the `fixtures`
  list (§3). A change to a pinned file or fixture file set updates its row in the same pull
  request. A preparation carries its bound dialect's digest (`mappingDigest`); fixture replay
  holds that binding under RFC 0018 §4.4. A verification record on earlier bytes records those
  bytes. A preset has no preparation to pin or replay. An earlier entry is the manifest at an
  earlier commit.
- **Licences.** `licence` is an SPDX identifier, and the author's choice: a dialect is data, so
  its licence is whatever its author grants. The organisation's default is `Apache-2.0`, the
  licence of each of its repositories, the Exchange's included; the Exchange's contribution guide
  applies it to an entry's files unless the entry's `licence` names another licence that lets the
  Exchange publish it, and the contributor certifies the right to grant it. A fixture is recorded
  bytes of a system's records: an author who may not publish a system's records makes fixtures
  from records the author may publish.
- **The thank-you bot.** The repository runs the organisation's workflow that thanks a merged
  contributor and suggests another task, as the other repositories do.
- **A recorded no is a decision.** An entry, a system or a source kind the Exchange declines is
  recorded with the reason and the condition that would reopen it, as the catalog records its own
  (gateway #259, #260).
- **What the Exchange refuses**, each before merge: CI where its test or its scan recognises the
  case — a recognised credential shape, a local path, a missing required fixture — and the
  maintainer who reviews the entry for everything else, in every file of the entry.
  - Credentials, tokens and keys, of any kind and in any file. A dialect names an input profile by
    its id and digest, a connection by its name and a header by its name, never a value (RFC 0018,
    Security and privacy).
  - Personal data, in a dialect, a fixture or a README.
  - Non-synthetic fixtures for an entry with a `research` source: every fixture published with
    such an entry is synthetic, under RFC 0018's round-8 Security and privacy rule.
  - Code of any kind. A dialect is declarative (RFC 0018 §1), and an entry holds no program,
    script, executable, image or package. The catalog runs its form, digest and scan checks (§4),
    and replays fixtures with the specification's verifier at the commit its CI pins.
  - An entry of kind `dialect` and direction `input` or `both` without fixtures: `fixtures` names
    at least one. An output-only dialect has `fixtures: []`; a preset omits the member and has no
    fixture directory. A preset carrying a pack, fixture or preparation-verification record is
    refused (§3).

### 7. A catalog's release contract

A **catalog location** is a git repository URL or a local directory containing the catalog's git
repository. A **release** is a tag resolved to the commit it names, with an annotated tag peeled
to its commit; a tag that does not resolve to a commit is refused. Its tag has §3's release-tag
grammar, `vMAJOR.MINOR.PATCH`. No branch ancestry is checked by the consumer. A producer may
require the tagged commit to be on `main` as its own rule; `judgment-pack-exchange` does so in
`.github/workflows/release.yml` and documents it in `docs/releasing.md`. A consumer does not rely
on that producer rule (#166). The consumer reads `manifest.json` and every entry file as the blob
in that commit's tree, byte for byte, with no conversion, including no checkout line-ending
conversion. Every fetched file therefore belongs to that same commit.

The consumer retains the catalog location, tag, resolved commit and manifest for the import.
A later repository state does not replace what the installation imported. A tag that now resolves
to a commit different from the one retained for that tag is refused. A catalog with no entries
may release the empty manifest, `[]`.

**Who holds these duties** (#166). `judgment-pack-exchange/tests/test_entries.py` holds the
catalog's manifest, entries, fixtures and scans (§4). Its `docs/release-contract.md` will document
all the consumer duties below; those are to be held by the consumer's own tests. For the Desk, the
repository is `Judgment-Pack/judgment-pack-desk`, tracked by
[judgment-pack-desk#400](https://github.com/Judgment-Pack/judgment-pack-desk/issues/400):

- The Desk's tests are to hold import replay with its reader and the fixture's own inputs.
- The Desk's tests are to hold refusal of lower tags and tags moved from their retained commits.
- The Desk's tests are to hold withdrawal: the imported commit stays and shows the withdrawal.
- The Desk's tests are to hold review records: reviewer, time, old and new commits, and explicit
  approval before replacement.
- The Desk's tests are to hold matching entry kinds in the manifest row and `entry.json`.
- The Desk's tests are to hold a preset's document-form check by its own checker (§§3–4).
- The Desk's tests are to hold refusal to run an unpaired preset.

The coordinator is to carry this complete list to Desk #400. These name the repository responsible
for each duty, not a claim that an importer or its tests have shipped. Another consumer holds each
duty in its own repository's tests. The catalog's CI cannot establish that a consumer fetched,
replayed or reviewed anything.

**Before import.** The consumer performs these checks itself, independently of a catalog's CI. It
fetches the release's manifest within the 1 MiB and 1,024-row bounds, checks its form (§3), and
checks one row per entry directory in the commit's tree and one entry per row, distinct ids in
byte order, closed rows and the exact `id`-to-`path` match. For each entry it would offer for
import, it fetches the entry's files from that release, using the manifest's fixture file lists,
and verifies:

- `entry.json` against the manifest's `entryDigest`, and its members against §3, including its
  `id`, `kind`, direction and authoring metadata, with the row's `kind` matching its `kind` and
  its path matching its `id`; each input dialect, of either entry kind, is held to its document's
  form as in §4 by the consumer's own form checker, written to RFC 0018's text;
- `dialect.json` against the manifest's `dialectDigest` over the stored bytes and `dialect.digest`
  over the document's canonical bytes (RFC 0018 §1, §2), when the entry has an input dialect;
- `output.json` against `outputDigest` over the stored bytes and `output.digest` over the
  document's canonical bytes (RFC 0018 §10), when the entry has an output dialect;
- each fixture's `preparation.json` against its `preparationDigest`, and its closed file set
  against the manifest list and §3, with every listed file fetched successfully and the source
  classification and binding document checked even when the preparation reader skips it;
- every pinned digest against the fetched bytes it names, including the profiles and acquisitions
  checked by the reader, using canonical bytes only where that digest's definition requires them;
- each file's bounds (§3 and RFC 0018 §12), and every file against the credential and local-path
  scan described in §4; a recognised credential or local path refuses the entry, and a scan's
  silence establishes no absence of credentials or personal data; and
- each recomputable fixture by replay with the consumer's own preparation reader, using the
  entry's own dialect, the fixture's own `profiles.json` and remaining inputs, and, for an unbound
  version-3 dialect, that fixture's `binding.json` (RFC 0018 §4.4). The reader must return a
  reading with no finding and a digest equal to `preparationDigest`. No record is supplied, so its
  binding is `not-checked`. A fixture outside the reader's supported versions or source kinds is
  reported as not recomputable, with the reason, never as a successful replay (§4).

A failed digest, form, file-set, bound or scan check refuses the entry before it is offered for
import; a malformed manifest refuses the catalog's import. A replay disagreement, finding or
verifier refusal also refuses the entry. File digests and canonical digests are distinct checks,
even when they happen to be equal. The manifest gives no separate digest for `README.md` or each
fixture input: those files are fetched as blobs from the same commit. For a fixture not recomputed,
its checks establish only the pinned fixture bytes, not the derivation; the dialect's document
form is checked independently. Verification runs no entry-supplied code and re-executes no research
recipe.

**An update** is an explicit, reviewed upgrade from one release to another. A lower tag, ordered
by its three integer components (§3), is refused, as is a moved tag. The consumer verifies the new
release as above. An entry is changed if any file under its path is added, removed or differs in
bytes between the two commits, including its README, fixture inputs and binding documents, even
when no pinned digest changes. A change of entry kind or direction is a change to the entry, shown
for review with the changed files. An entry absent from the new release stays imported at its
previous commit and is shown as withdrawn; it is not silently removed or replaced.

The consumer shows the changed entry, its compatibility statement, and the `upgrade` note keyed
by the previously imported entry's digest, if one exists. A compatibility range excluding the
consumer's own release informs the review and does not block the upgrade. The review records who
approved it (the reviewer's identifier), when, and both the previously imported and new commits;
only that explicit approval replaces the imported entry. Neither a newer tag nor an author's
compatibility statement replaces the installation's review.

**Importing enables no execution and grants no permission.** Local binding means the binding
document of RFC 0018 §4.4 for a version-3 dialect with unbound sources, mapping those sources to
the installation's input profiles. Its fixture replay uses the fixture's own binding document and
profiles, not the installation's replacement bindings. An entry with dialect version 2 is imported
as published and, where it has fixtures, re-verified under its own dialect with their own
profiles. Using it against the installation's sources means re-authoring, which remains Unresolved
question 7; import does not substitute profiles in version 2.

A desk importing a preset pairs its dialect with a pack locally before any run; an unpaired preset
is refused for running. It chooses parameters and, where required, binds sources under RFC 0018
§4.4. This local pairing is not a catalog-verified preparation and adds no verification record to
the published preset. A preset's lack of fixtures is not a successful replay.

The format carries no budget; a README may describe one. A research source's `constraints` is
part of the request, not a budget. Display metadata, requirements and README suggestions are data
for review, never allowances. Import does not bind a connection, call a source, schedule a run or
authorise a write. The installation chooses its local bindings and parameters separately and may
export its dialect as an entry in any catalog (§2).

The catalog's `docs/release-contract.md` and entry-format rules adopted pull request #163 through
exchange #6 and hold it at `v0.1.0`. Pull request #178 preserves the manifest's bounds and adds
the row's `kind`, form checks and the consumer's preset duties to that contract; the catalog's
implementation follows through exchange #8. This amendment records no implemented importer.
Signing remains Unresolved question 1.

## Alternatives

- **Entries in the gateway's catalog.** The catalog holds bindings, one file per platform in the
  engine configuration's shape, held by the gateway's Go tests and released with the gateway. A
  dialect is a pair, a system and a pack, written by whoever wrote it, in a format the specification
  proposes and the Runner prepares. Held in the catalog, every dialect would move with the gateway's
  releases and its review, the input side would sit in a repository that never prepares one, and a
  pack author would contribute to a gateway to publish a reading of their pack. The Exchange takes
  the catalog's manner and not its place.
- **Entries in each pack.** RFC 0018 rejects a dialect as an extension: "one pack is read through
  many systems, each with its dialect, and a pack that carried its dialects would name its systems".
  A pack's digest would change with every new system read into it, and a dialect for another
  author's pack would need that author.
- **A registry only.** A hosted service with no repository would hold entries, their review and
  their history in its own store: nothing to clone or pin by commit, no public review record beside
  the bytes, and the service's operator to trust for both. A hosted registry is out of scope
  (Unresolved question 4); §2 describes the open question of serving a catalog's manifest.
- **No shared place.** The status quo: each deployment writes its own dialect and verifies it
  against nothing but its own runs. A counterparty can hold a preparation to its dialect (RFC 0018),
  but has no published dialect to compare it with, and a second reader has no fixtures but the
  Runner's nine.

## Compatibility

- **Core and the dialect.** Nothing in Core `0.2.0-draft`, its schema, its classes or its corpora
  changes, and nothing in RFC 0018's dialect format or its companion document. This record defines
  no conformance class.
- **The Exchange and the dialect.** RFC 0018 is Accepted at draft maturity; the catalog adopts
  changes by its own process. Its CI pins this repository at a commit for the verifier (`f821757`
  at its scaffold). A change to the dialect format reaches the Exchange only when the Exchange
  moves its pin, by its own pull request; an entry the moved verifier answers otherwise is decided
  on that pull request.
- **The Desk** browses; it changes nothing in an entry, and nothing in its own inputs until an
  operator adopts one by review. The Desk producing the dialect format is Desk #398.
- **The Runner and the gateway** are unchanged. The Runner prepares from an adopted input dialect
  as from any mapping v2 document; the gateway holds a write to an adopted policy as to any
  policy. An entry with dialect version 2 stays as published for import and fixture replay.
  Pointing its `profile` and `profileDigest` at the installation's own input profile changes its
  bytes and digest and is re-authoring (Unresolved question 7). Version 3's unbound form uses RFC
  0018 §4.4's binding document; fixture replay uses the fixture's own binding and profiles (§7).

Entry format version 2 requires `kind`; a version-1 reader refuses its entries and its manifest
rows, so it refuses the whole non-empty catalog, kind `dialect` included. A version-2 reader
likewise refuses version-1 entries and manifest rows under the closed forms (§3). The
organisation's catalog has released only the empty manifest, which fits both forms; nothing
published is stranded. The upgrade-history check reads earlier rows' `id` and `entryDigest`
whatever their form (§3). This changes the entry and manifest forms, not the dialect's version.

Presets add neither a workflow entry kind nor a workflow member: [RFC 0020](0020-workflow.md)
still requires a later decision for that. A workflow stage may pin a preset's published dialect
digest with its own pack (RFC 0020 §3); that is a local pairing and grants nothing by itself.
A preset with a `research` source cannot be a stage of workflow version 1 until RFC 0020's
condition is met; its revision is [judgment-pack-spec#177][spec-177], following RFC 0018 round 8.

## Security and privacy

- **Credentials and personal data in a dialect or a fixture.** A dialect carries none by its format
  (RFC 0018, Security and privacy); a fixture is where they arrive. A fixture recorded from a real
  system holds that system's records, and a recorded result cannot be edited afterwards: its digest
  is in a receipt the gateway signed, so an edited result is `acquisition-invalid` (RFC 0018 §5.2).
  Personal data is kept out of a fixture by recording from records that hold none — a project, a
  table or a workspace kept for the purpose — never by editing a recording. A receipt also carries
  what the gateway signed of the read: the endpoint, which names an organisation's or a workspace's
  host; the caller, where a verified token named one; and the source and authority labels. A
  publisher records under a gateway and an identity it is content to name, and a reviewer checks
  each fixture's receipts as well as its results. CI's scan refuses recognised credential shapes and
  local paths; a maintainer refuses credentials and personal data in every file of an entry before
  merge, recipe literals and receipt metadata included (§3). An entry with a `research` source
  publishes synthetic fixtures only (§6).
- **A wrong dialect's effect.** Bounded, not prevented. An input dialect that reads the wrong member
  derives wrong facts faithfully: the Runner recomputes every preparation rather than trust an
  author's, the lineage records which pointer fed which target, admission refuses a class a target
  does not admit, and an `operation` source is refused under any input profile but the one it pins
  (`profile-mismatch`, RFC 0018 §5.1), so a dialect reaches no source its adopter has not
  configured. None of that shows that the rule was right for the pack. An output dialect is a
  policy, and the gateway holds each write to it at the moment of the write, by `bind`, `fix`,
  `closed` and `requireSignedRecord`; a policy that holds too little admits what it admits, as the
  open limit on a container's shape shows (gateway #267). An entry is adopted by an operator's
  review; a desk's browse installs nothing.
- **Licences.** A fixture can carry records its author has no right to publish, and a licence can
  forbid what the Exchange does with it. The author certifies the right to grant the entry's
  licence, and the review reads the fixtures' origin; a licence that does not let the Exchange
  publish an entry is refused.
- **A research recipe's prompt as data.** A `research` source's question and constraints are text a
  model reads when an operator runs the recipe. To the Exchange they are data: the test runs no
  model, and no reader sends a recipe anywhere. A reviewer reads them as instructions a model will
  follow, and checks that they ask for what the dialect's targets need and no more, and that every
  literal naming a person, a customer or an account is left to a case parameter (RFC 0018, Security
  and privacy). A desk that runs one is to treat what comes back as data (Desk #369).
- **The manifest and its host.** A desk trusts what it pins. Pinned by commit, the manifest is the
  repository's; served by a registry, it is whatever the registry serves, until something signs it
  (Unresolved questions 1 and 4).
- **Resource use.** A desk reads the manifest within §3's 1 MiB and 1,024-row bounds, not the
  connection catalog's 32 KiB bound. It holds entry files to §3's bounds and a verifier's inputs to
  RFC 0018 §12's bounds, refusing what exceeds them.

## Conformance

**None of JPS's.** This record defines no conformance class, and no claim of any JPS class can
cite an entry. An entry's check is the Exchange's own test (§4), at the specification commit the
repository pins. The repository aligns its tests to §3's members list by its own pull request. At
`b516dd7`, the scaffold's tests held: positively, an example entry built from this repository's
staged `valid` vector, which is not an entry and is not in the manifest, holds to every rule and
gets a reading whose digest is its `preparationDigest`; negatively, a changed byte against either
manifest digest, an assertion that is not the sentence, an `id` that is not its path's, an unknown
member, an empty `fixtures`, both `versions` and `digests`, a verification record without its
members, a manifest out of `id` order or with an `id` twice; at a boundary, the empty manifest the
repository holds today; and adversarially, each credential shape and local path the scan is
written for, and a relative link that does not resolve.

**The verification record's form.** `verification` is an array, empty until an entry is verified,
of `{date, runner, runtime, readers, result}`, each member as §3's list gives it: `date`, the day
the readers ran; `runner` and `runtime`, the release tags of the Runner and the runtime at which
the fixtures hold; `readers`, the preparation verifiers that agreed, each named as
`<owner>/<name>/<path>@<commit>` in §3's grammar so that it can be found again — for example,
`Judgment-Pack/judgment-pack-runner/cmd/verify-run@82116bf`; and `result`,
`"agree"`, the only value the format gives. A reader that disagrees adds no record: its
disagreement is a finding against the entry or the reader, recorded where it was found. A record
is added by a pull request after the run it records, and is a record of the bytes it was made on
(§6). A preset has no such run or record; its `verification` is the empty array.

**The catalog's form checker.** Exchange #8 is to hold both entry kinds to §§3–4 with passing
version-3 unbound operation documents and, once supported, round-8 research documents. Refusal
cases include malformed reads, rules, reconciliation and admission forms, partial binding
members, a version or source kind the checker does not read, and exceeded bounds. The same
cases hold kind `dialect` even when every fixture's replay is skipped. Preset cases also hold
version 3, every eligible source unbound, the exact three-file directory and no profile in
`requires`. These are duties for the catalog's checker and the consumer's own checker, not
preparation-verifier tests or a claim that either checker has shipped.

## Implementation

1. **The repository.** `judgment-pack-exchange`, created on 2026-10-14. Its first commit,
   `b516dd7`, scaffolds the layout, `docs/entry-format.md`, an empty `manifest.json`,
   `tests/test_entries.py`, the example entry, the contribution rules, the licence and the
   thank-you bot. Its CI job, `entries`, checks out this repository at `f821757`, the merge of RFC
   0018, and runs the tests; it passed on that commit. At `v0.1.0`, its `docs/entry-format.md`,
   `docs/release-contract.md`, `docs/releasing.md` and `tests/test_entries.py` hold version 1,
   metadata, fixture lists and its release practice. Entry version 2 and pull request #178's
   enforcement changes belong to judgment-pack-exchange#8; they are not implemented here.
2. **A desk's browse and importer.** Proposed, not built, and tracked by
   [judgment-pack-desk#400](https://github.com/Judgment-Pack/judgment-pack-desk/issues/400). It
   takes a catalog location, a git repository URL or local directory (§7), and a release tag. The
   Desk would read the manifest as blob bytes at the tag's resolved commit; show each entry's
   title, entry kind, direction, pack when present, requirements, source kinds, licence, author,
   assertion and verification records as the entry gives them; fetch and check an entry's files
   under §7; and hand an entry the operator adopts to its inputs, which produce the dialect format
   (Desk #398). It runs nothing an entry holds. It pairs an imported preset with a pack locally
   before any run.
3. **A hosted registry** is out of scope (Unresolved question 4).
4. **The seed entries, planned and not verified.** Neither is written. Each is an input dialect
   with its write-back, so each is of direction `both` (Unresolved question 6). Their verification
   records are added after the maintainer's first live checks of the two connections, on gateway
   v0.13.0 or later.
   - **Azure DevOps work items into a triage pack.** Input: the organisation's work items, read by
     the `azure-devops` connection (a WIQL query, items by id, or both as one read). Output: the
     work item's state, written through the `azure-devops` write-back platform's
     `wit_work_item_write` under the gateway's worked policy, which fixes `action` to `update`,
     tests the revision first, fixes the state the outcome maps to, binds the item's id and
     revision to the record's facts, and is closed (`docs/design/engine-config.md`, "The
     write-back platforms"; its open limit is gateway #267).
   - **A Databricks table into a pack.** Input: a table read by the `databricks` connection, one
     SQL statement on its warehouse with its values bound as named parameters. Output: a Unity
     Catalog function the workspace's owners write, called through its managed MCP server on the
     `databricks` write-back platform, each of its parameters bound to a fact (the same design
     note's worked `record_approval`).
   - **What each needs.** A connection profile; an input profile for the gateway source the reads
     come through; fixtures recorded from a real workspace or organisation whose recorded records
     hold no personal data — a project or a table kept for the purpose, since a recording cannot
     be edited afterwards (Security and privacy); and a source kind the Exchange's test can
     recompute. Both connections declare their reads of shape `http`. RFC 0018 §4.1 now admits
     that shape through `operation`, with the connection's request object; no new `sql` or `http`
     source kind is needed for that route. The seed fixtures and live checks are still due
     (question 8).
     A catalog pinned to a verifier that cannot read them reports that limit under §4.

**The readers.** The Exchange's test runs `tools/dialect_verify.py`, the first reader of RFC 0018,
written by that text's author; the second reader, `tools/dialect-verify-ts/`, was written from the
text alone by a different author (RFC 0018's Evidence), and the Runner's `verify-run` is a third.
All are this project's, and RFC 0000's bar of two independent implementations is not claimed.

## Unresolved questions

1. **Signing entries, and by whom.** An entry is pinned by the manifest's digests and the
   repository's history, and nothing is signed. Whether an author signs an entry, the Exchange
   signs the manifest, both or neither; with which key; and what a desk holds a signature to, are
   open. A hosted registry makes the question pressing.
2. **Entry versions against pack versions, and a range syntax for `pack.versions`.**
   `pack.versions` takes the form the pack's own versioning gives, 1 to 64 characters, and Core
   gives a `MAJOR.MINOR.PATCH` version and no range: which range syntax, if any, is open; the
   scaffold's example writes `>=0.1.0`. A published pack version SHOULD be immutable (Core §11),
   not MUST, so a version names content less firmly than a digest. And how an entry follows a pack
   is open: a pack version that changes a fact pointer breaks a dialect, and whether its successor
   is a new entry, the same `id` with new digests, or an entry per pack version, is undecided.
3. **Fixtures the verifier cannot recompute.** Such a fixture is held by its digests only, and
   establishes that its bytes were recorded; its dialect document still passes the catalog's
   own form check (§4). Whether an entry of kind `dialect` none of whose fixtures is recomputed
   is published at all, or published and marked, is open. A round-8 research entry is refused
   until the readers implement it (#176), as §4 requires. Presets are separately settled by
   question 10; they have no preparation fixtures. For `research` it stays
   partly so for good: once a reader reads the source kind, a research fixture's derivation is
   recomputable, but a model's answer is never reproduced by verification. Round 8 holds each
   retained response under its receipt; a whole research record without its own receipt remains
   partly the caller's assertion (§3).
4. **The hosted registry and its identity.** Whether to host one, who runs it, under what name and
   key, how a desk pins it, and what a desk does when the registry and the catalog disagree. The
   maintainer's decision of 2026-10-15 leaves these open and the hosted registry out of scope; any
   repository in the entry format can already be a catalog (§2), without a hosted registry.
5. **Output dialects before the gateway publishes policy vectors.** RFC 0018 defers the output
   side's vectors, and the gateway publishes none. An output dialect has no preparation, so a
   fixture's `preparationDigest` has nothing to name for it, and `dialectVersion`, an integer of 2
   or more equal to the document's `version`, has nothing to equal in an output dialect, whose
   `outputVersion` is the string `"1"`. Whether the Exchange carries output dialects now, held by
   review and by the gateway's own tests of its policies, or waits for vectors, is open.
6. **An entry of direction `both`.** RFC 0018 §10 keeps the input side and the output side as two
   documents, each with its own digest, so that a version-2 dialect stays the Runner's mapping v2
   byte for byte. The format holds one `dialect.json` with one `digest`. Whether a `both` entry
   holds one file per side, is two entries that name each other, or is one document of both, is
   open, and both seed entries are of this direction. *Resolved by pull request #150, on
   the maintainer's decision at exchange issue #2: a `both` entry holds one file per side,
   `dialect.json` and `output.json`, each with its own digest, in `entry.json` and in
   `manifest.json` (§3); the exchange's pull request is
   [#3](https://github.com/Judgment-Pack/judgment-pack-exchange/pull/3).*

7. **Re-authoring a version-2 dialect for another installation.** A version-2 `operation` source
   names its input profile by id and digest (RFC 0018 §4.1), and a profile pins the gateway's key,
   source, authority, adapter, shape and endpoint (§5.1 there). Import keeps that dialect as
   published and re-verifies its fixtures with their own profiles (§7). Using it against the
   installation's sources requires re-authoring: changing the profile changes the dialect's bytes
   and digest, and the catalog's verification does not cover that copy. Whether a desk can
   constrain such re-authoring to a profile substitution, and what checks and new fixtures it
   needs, remains open. RFC 0018 §4.4 now defines a binding document for version 3's unbound
   source form; that procedure does not apply to a dialect of version 2. Both readers now read the
   version-3 operation form; its vectors are staged and no released specification version
   publishes them.
8. **The seed entries' source kind.** The earlier question was whether to wait for new source kinds
   or publish over `mcp`. *Resolved as a format question by RFC 0018 §4.1's amendment of 2026-10-15:
   `operation` admits the connections' `http` shape and request objects. The seeds still need
   their live checks and fixtures, and the catalog a reader pinned to that form. This records no
   verified seed.*
9. **Public submission and its review load.** Out of scope by the maintainer's decision of
   2026-10-15 on issue #142 (§2). The organisation's catalog holds the entries it reviews and
   checks (§4); it is not a place users upload to. Reuse uses any catalog in the entry format,
   with local binding and the same fixtures, and an installation can export its dialect as an
   entry. This is a scope decision, not a submission queue waiting for a review policy.

10. **A dialect published without a pack.** *Resolved on 2026-10-15 by #172, option A:* entry
    version 2 adds required `kind`; `preset` is input-only, without a pack or fixtures, checked
    for document form, digests and scans. Its manifest row names the kind. It establishes the
    recipe's identity and form, nothing about a preparation; a desk pairs it with a pack locally
    before any run. The format carries no budget; README suggestions and metadata grant no
    execution permission, and `constraints` is part of the request, not a budget (§§3–5, 7).
11. **The catalog's seven sentences.** *Resolved on 2026-10-15 by #166:* §6 names all manifest
    pins and the fixture list; §3 specifies reliance on the verifier's dialect bound, previous
    release upgrade keys matched to the same entry's history, RFC 0018 §4.4's full classification,
    and reader locators; §7 assigns replay, tag, withdrawal and review checks to the consumer's
    tests and distinguishes the producer's branch rule. The catalog's implementation follows
    through judgment-pack-exchange#8. These decisions settle the seven questions for #178;
    their implementation and tests remain the catalog's and each consumer's duties.

[dialect-vectors]:
  https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/dialect

[gateway-catalog]:
  https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/catalog/README.md

[connection-catalog]:
  https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/docs/design/connection-catalog.md

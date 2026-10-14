# RFC 0019: The Judgment Exchange — a shared place for dialects

- Status: Draft
- Type: Exploratory (a cross-project exploratory record — the `judgment-pack-exchange` repository,
  a desk's browse of it, and a hosted registry later; outside JPS)
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
> `docs/entry-format.md`, `CONTRIBUTING.md` and `tests/`); a desk's browse of the manifest in the
> [Desk](https://github.com/Judgment-Pack/judgment-pack-desk); and a hosted registry, later, in the
> hosted application, as that application's question. Acceptance endorses this record as written
> and confers no authority over any of them, each of which adopts its part by its own process. The
> repository has made one such decision already: its `docs/entry-format.md` repeats the entry format
> and says that this record "is normative when it lands", and that where the two differ once it
> lands, "the RFC is right and this page is a bug". That is the repository's adoption, made by its
> own process, and not an authority this record claims.
>
> **The decision this records.** Issue #142 records the maintainer's direction of 2026-10-14: the
> names *dialect* and *Judgment Exchange*, and a shared place for dialects, a repository first and a
> hosted registry later, filed as a record of its own once its prerequisites land. The maintainer
> fixed the entry format for both this record and the repository, which was created the same day
> and scaffolded from it in parallel. §3 quotes the format word for word, but for one sentence the
> maintainer corrected on review, and gives each member's type, requiredness, grammar and bound as
> the maintainer's disposition of that review fixed them. Under the
> [interim review regime](../GOVERNANCE.md#interim-review-regime), the pull request that merges this
> record carries a cross-vendor adversarial review, with the maintainer's disposition of each
> finding.

## Summary

A **dialect** is a pack's terms spoken in a system's ([RFC 0018](0018-dialect.md)): an input
dialect derives a pack's facts and evidence availability from a system's records, and an output
dialect binds a disposition to a write's arguments. The **Judgment Exchange** is the place that
holds dialects, as the gateway's catalog holds bindings. It is first a repository under the
organisation, `judgment-pack-exchange`: hand-maintained data in the catalog's manner, each entry a
directory pinned by digest in a manifest that a desk can browse, and each held by a test that runs
the specification's preparation verifier over the entry's fixtures. Later, if the product warrants
it, a hosted registry serves the same manifest.

An entry carries a dialect document, the pack it was written against, what it requires, its source
kinds, its licence, its author, one fixed sentence its author asserts, its fixtures and its
verification records. What a published entry establishes is that assertion, under the Exchange's
review, and that its fixtures hold at the Runner and runtime a verification record names: nothing
about any record's truth, nothing about an operator's intent, and, for a research source, nothing
about the answer's correctness.

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

**What exists.**

- **The format.** [RFC 0018](0018-dialect.md), the dialect, landed as a Draft in #144 (merge commit
  `f821757`). Version 2 of the dialect document is the Runner's mapping v2 byte for byte; version 3
  proposes the kinds `http`, `sql`, `web` and `research`, defined and not claimable; the output side
  is the gateway's decision policy, by reference. Its second reader, `tools/dialect_verify.py`,
  reads dialect version 2 and the kind `operation`, and refuses every other kind as `kind-unread`.
- **The vectors.** The Runner's nine preparation vectors are published (Runner #75, closed by Runner
  pull request 77, merged as `82116bf`, released in Runner v0.10.0) and staged byte for byte in
  [`conformance/dialect/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/dialect).
  They are the pattern an entry's fixture follows: the dialect, the case, the acquisitions, the
  profiles, and the preparation's exact canonical bytes, which a second reader recomputes.
- **The output side.** A gateway decision policy holds a write to its decision record by `bind`
  (gateway ADR-0011), `fix` and `closed` (gateway #258, ADR-0016, released in gateway v0.14.0), and
  `requireSignedRecord` (gateway ADR-0012). One limit is documented and open: a policy does not hold
  a container's shape, which the worked Azure DevOps policy shows (gateway #267).
- **The catalog's manner.** The gateway's
  [`catalog/README.md`](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/catalog/README.md)
  holds the bindings the engine ships, one hand-maintained file per platform. A configuration pins
  the file it uses by digest, "so a catalog update never silently changes what a running engine
  reaches"; "every licence is copied from the artifact's own statement for that version, never
  assumed"; tests hold each file to its shape. A no is recorded as a decision: no catalog binding
  of the Azure DevOps local server (gateway #259), and no `write` operation for `postgres`, since
  raw SQL is no write tool (gateway #260).
- **The browse pattern.** The gateway's
  [`docs/design/connection-catalog.md`](https://github.com/Judgment-Pack/judgment-pack-gateway/blob/main/docs/design/connection-catalog.md)
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
  the vectors, after a comment period (issue #141). The second reader in this repository is the
  text's author's. An independent second reader is being written; none is published.
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

## Specification

### 1. The names

A **dialect** is a pack's terms spoken in a system's (RFC 0018 §1).

- An **input dialect** derives a pack's facts and evidence availability from a system's records,
  through any source kind RFC 0018 defines: a tool call on a gateway source of shape `mcp`, which
  the issue calls a connection's record or an MCP query (`operation`), a file the operator selected
  (`selected-file`), and, proposed for version 3, an HTTP request (`http`), a SQL statement on a
  connection (`sql`), a public page (`web`) and an AI-assisted research recipe (`research`). It is
  RFC 0018's dialect document.
- An **output dialect** binds a disposition to a write's arguments: RFC 0018 §10's output side, in
  the gateway's decision-policy form.

The **Judgment Exchange** is the place that holds dialects, as the gateway's catalog holds
bindings. A binding says how an engine reaches a system; a dialect says how a pack reads that
system's records, or how a disposition becomes that system's write. An **entry** is one dialect as
the Exchange holds it (§3).

### 2. Where it lives, in order

1. **A repository**, `judgment-pack-exchange`, under the organisation. Hand-maintained data in the
   catalog's manner: each entry a directory written and reviewed by hand, pinned by digest in a
   manifest; each licence the author's, stated and never assumed; a no recorded as a decision (§6).
   A desk browses the manifest through the connection-catalog pattern: it reads one document within
   bounds, holds it to its shape before showing anything, holds each entry it fetches to the
   manifest's digests, runs nothing an entry holds, and falls back to no guessed manifest when it
   cannot read one. A test holds each entry to its fixtures with the specification's preparation
   verifier (§4). The contribution rules are the other repositories': a DCO sign-off on every
   commit, one review round, and the thank-you bot.
2. **A hosted registry**, later, serving the same manifest: the hosted application's question, to be
   decided if the product warrants it.

**What moves and what stays when the registry comes.** The repository stays where entries are
written, reviewed, pinned, verified and declined: the manifest the repository publishes is the
registry's source, byte for byte; an entry's files and digests are the same in both; the test stays
the entry's check, and a recorded no stays in the repository. Serving moves: listing, search and
download at a stable address, so that a desk need not clone a repository. A desk holds what a
registry serves to the manifest's digests, as it holds the repository's, so the registry adds reach
and not trust: a registry that serves other bytes for an entry is caught by the digests. A registry
that serves another manifest is caught only by a desk that pins the manifest by other means
(Unresolved questions 1 and 4).

### 3. The entry format

The maintainer fixed the format for both this record and the repository. It is quoted here word for
word, but for its last sentence, which the maintainer corrected in the disposition of this record's
review (finding 2):

An **entry** is one directory `entries/<publisher>/<name>/` holding, as separate files with these
names:

- `entry.json` — a closed JSON object: `entryVersion` (`1`); `id` (`<publisher>.<name>`, lower-case
  letters, digits, `-` and `.`); `title`; `direction` (`"input"`, `"output"` or `"both"`); `pack`
  (an object: `id`, the pack's id, and either `versions`, a version range, or `digests`, an array of
  the pack digests the dialect was written against); `dialect` (an object: `path`, always
  `dialect.json`; `dialectVersion`; `digest`, the SHA-256 of the dialect document's canonical bytes
  as RFC 0018 defines them); `requires` (an object, members optional: `inputProfile` by digest,
  `connectionProfile` by digest, `platform` by catalog binding name for an output dialect);
  `sourceKinds` (the kinds the dialect's sources use, from RFC 0018's list); `licence` (an SPDX
  identifier); `author` (a handle or organisation name as the author chooses to be named; never
  required to be a personal name); `assertion` (the one fixed sentence the format gives: that the
  author asserts these rules derive these facts and this evidence-availability from records of that
  shape, or these arguments from that disposition, and asserts nothing about any record's truth);
  `fixtures` (an array of `{name, path, preparationDigest}`); `verification` (an array, empty until
  verified, of `{date, runner, runtime, readers, result}` where `readers` names the preparation
  verifiers that agreed and `result` is `"agree"`).
- `dialect.json` — the dialect document in RFC 0018's format.
- `fixtures/<name>/` — for each fixture, the recorded source records (as the Runner retains them)
  and `preparation.json`, the exact canonical bytes the dialect must produce from them; for a
  `research` source, the research record held by digest.
- `README.md` — what the dialect is for, in the publisher's words; no credentials, no personal data.

The repository root holds `manifest.json`, an array of `{id, path, entryDigest, dialectDigest}`
pinning each entry by the SHA-256 of its `entry.json` and `dialect.json` bytes, in `id` order; a
test holds every entry to the manifest and every fixture to its `preparationDigest` by running the
specification's preparation verifier over it. What a published entry establishes is the author's
assertion above, under the Exchange's review; nothing about truth. CI refuses recognised credential
shapes and local paths; a maintainer must refuse credentials and personal data in every file of an
entry before merge, recipe literals and receipt metadata included; and the scan's silence proves
nothing.

**The members.** Every member and nested object of `entry.json` has a type, a requiredness, a
grammar or a set of allowed values, and a bound, as the maintainer's disposition of this record's
review gives them (finding 1):

| Member | Type | Required | Grammar, allowed values and bound |
| --- | --- | --- | --- |
| `entryVersion` | integer | yes | `1` |
| `id` | string | yes | `^[a-z0-9]+(\.[a-z0-9-]+)+$`, 3 to 128 characters, equal to the entry's path under `entries/` with `/` read as `.`: `entries/<publisher>/<name>/` holds the id `<publisher>.<name>` |
| `title` | string | yes | 1 to 200 characters |
| `direction` | string | yes | `input`, `output` or `both` |
| `pack` | object, closed | yes | `id`, and exactly one of `versions` and `digests` |
| `pack.id` | string | yes | an absolute URI (Core §4), at most 2048 characters |
| `pack.versions` | string | exactly one of the two | 1 to 64 characters, in the pack's own versioning; a range syntax is an unresolved question (2) |
| `pack.digests` | array of strings | exactly one of the two | 1 to 16 `sha256:` digests |
| `dialect` | object, closed | yes | `path`, `dialectVersion` and `digest` |
| `dialect.path` | string | yes | the literal `dialect.json` |
| `dialect.dialectVersion` | integer | yes | 2 or more, equal to the dialect document's `version` |
| `dialect.digest` | string | yes | a `sha256:` digest |
| `requires` | object, closed | yes | its members optional |
| `requires.inputProfile` | string | no | a `sha256:` digest |
| `requires.connectionProfile` | string | no | a `sha256:` digest |
| `requires.platform` | string | no | `^[a-z][a-z0-9-]*$`, at most 64 characters |
| `sourceKinds` | array of strings | yes | 1 to 16, distinct, each a kind RFC 0018 lists for the document's `dialectVersion` (§4 there); a `dialectVersion` above 3 is read with version 3's list until a later RFC defines more |
| `licence` | string | yes | one SPDX licence identifier matching `[A-Za-z0-9][A-Za-z0-9.+-]*`, or a `LicenseRef-` form of that grammar; no compound licence expressions; at most 64 characters |
| `author` | string | yes | 1 to 100 characters |
| `assertion` | string | yes | the fixed sentence (below), byte for byte |
| `fixtures` | array of closed objects | yes | 1 to 64 |
| `fixtures[].name` | string | yes | `^[a-z0-9]+(-[a-z0-9]+)*$`, at most 64 characters, distinct within the entry |
| `fixtures[].path` | string | yes | `fixtures/<name>` |
| `fixtures[].preparationDigest` | string | yes | a `sha256:` digest |
| `verification` | array of closed objects | yes | at most 32; empty until verified |
| `verification[].date` | string | yes | `YYYY-MM-DD` |
| `verification[].runner` | string | yes | a release tag, `^v\d+\.\d+\.\d+$` |
| `verification[].runtime` | string | yes | a release tag, `^v\d+\.\d+\.\d+$` |
| `verification[].readers` | array of strings | yes | 1 to 8, each `<repository>/<path>@<commit>`, at most 200 characters |
| `verification[].result` | string | yes | `agree` |

`entry.json` and `README.md` are each at most 64 KiB, and a fixture directory at most 16 MiB;
`dialect.json` is bounded as RFC 0018 §12 bounds a verifier's inputs. Every object is closed: a
member the table does not list is refused. A member name given twice in one object is refused, as
Core §2.1 refuses one.

**How the format is spelled.** Beside the table, the assertion's words, the digests and a fixture's
files are spelled as follows, as the repository's scaffold spells them.

- **The assertion.** `assertion` is exactly this sentence: "The author asserts that these rules
  derive these facts and this evidence-availability from records of that shape, or these arguments
  from that disposition, and asserts nothing about any record's truth."
- **Digests.** Every digest is written `sha256:` followed by 64 lower-case hexadecimal characters,
  as RFC 0018 §1 writes one. `dialect.digest` is the digest of the dialect document's `canon` bytes
  (RFC 0018 §1): its dialect digest (§2 there), which every preparation it produces carries as
  `mappingDigest` (§9.1 there). The manifest's `entryDigest` and `dialectDigest`, and a fixture's
  `preparationDigest`, are digests of the files' bytes as stored. A `dialect.json` stored in bytes
  other than its `canon` form, indented say, has a `dialectDigest` other than its `dialect.digest`,
  and each is held to its own definition. `preparation.json` holds the preparation's canonical bytes
  (RFC 0018 §9.5), so its `preparationDigest` is the preparation's digest.
- **A fixture's files.** A fixture directory holds `case.json`, the case document; `sources.json`,
  the acquisitions, optional and absent for a case-only fixture; `profiles.json`, the input profiles
  the fixture was prepared under; and `preparation.json`. They are the files the specification's
  preparation verifier reads (RFC 0018 §11), named as the Runner's vectors name them, with the
  dialect taken from the entry's `dialect.json`. A fixture's `path` is `fixtures/<name>`, relative
  to the entry's directory. For a `research` source, `sources.json` holds the research record as the
  acquisition's result, held by its digest under its receipt, as every acquisition is.
- **The repository's own copy.** The repository's `docs/entry-format.md` repeats the format, with
  the spellings its tests make, and says that this record is normative for the repository when it
  lands (the scope note).

### 4. The Exchange's test

A test in the repository, run on every push and pull request, holds:

- **the manifest to the entries**: one row for each entry directory and one entry for each row, in
  `id` order, each `id` its directory's `<publisher>.<name>`, and `entryDigest` and `dialectDigest`
  over the files' bytes;
- **each `entry.json` to the members' table (§3)**: each member's type, requiredness, grammar and
  bound, every object closed, and the `assertion` the fixed sentence exactly;
- **`dialect.digest`** to the dialect document's `canon` bytes, and each fixture's
  `preparation.json` to its `preparationDigest`;
- **each fixture to the specification's preparation verifier**, `tools/dialect_verify.py` at the
  specification commit the repository's CI pins: the test gives it the entry's `dialect.json` and
  the fixture's files, and requires a **reading** — no refusal and no finding (RFC 0018 §11) — whose
  digest equals the fixture's `preparationDigest`. No record is given, so the reading's binding is
  `not-checked`, and a fixture says nothing about any runtime record; and
- **every file to a scan** that refuses the common shapes of a credential, a token and a key, and a
  local path, before anything is merged. A scan's silence is not a finding that none is there:
  credentials and personal data in every file are a maintainer's to refuse before merge (§3).

**A fixture the verifier cannot recompute.** A fixture of a source kind the specification's verifier
cannot recompute is held by its digests only: the test skips the recomputation and says why. Today
that is `research`, and, until a reader reads them, every kind but `operation`: the verifier reads
dialect version 2 and the kind `operation`, and refuses every other kind as `kind-unread`. What such
a fixture establishes is only that these bytes were recorded and pinned; it is no check of the
dialect (Unresolved question 3).

### 5. What an entry establishes, and what it does not

An entry establishes, to a reader who runs the Exchange's test:

- **The author's assertion**, the format's one sentence (§3): that these rules derive these facts
  and this evidence availability from records of that shape, or these arguments from that
  disposition. It stands under the Exchange's review: a maintainer's read of every entry, and, for
  a material entry, a recorded cross-vendor review round with the maintainer's disposition of each
  finding.
- **That its fixtures hold at the named Runner and runtime**, as each verification record states:
  on its date, each reader it names recomputed every fixture's preparation from the entry's dialect
  and the fixture's files, byte for byte equal to `preparation.json`. For those fixtures, that is
  what RFC 0018 §13 says a recomputed derivation establishes: these facts and this evidence
  availability were derived from those bytes by these rules.

It does not establish:

- anything about any record's truth: the stance Core §6.3 takes of a source and the gateway's
  catalog takes of a binding;
- that the dialect is right for the pack, or reads what its author meant (RFC 0018 §13), or fits
  any record, or any release of the system, the pack, the Runner or the gateway, other than its
  fixtures and the releases a verification record names;
- anything about an operator's intent, or that an operator who adopts the entry may read or write
  what it names;
- for a `research` source, anything about the answer's correctness: its research record is held by
  its digest, and RFC 0018 §13 says it establishes the least of any acquisition;
- for an output dialect, that a write its policy admits is the right write: the gateway holds a
  write to its policy at the moment of the write, and says what that establishes; and
- for a fixture held by its digests only (§4), anything beyond that its bytes were recorded.

### 6. The repository's rules

- **Review.** A new entry and a changed dialect are material; a change to a README or a title is
  not; any other change is classified on its pull request, out loud. One entry per pull request. A
  material change gets a maintainer's read and one recorded cross-vendor round, with the
  maintainer's disposition of each finding, on its pull request, under the specification's [interim
  review regime](../GOVERNANCE.md#interim-review-regime).
- **Pinning.** The manifest pins each entry by `entryDigest` and `dialectDigest`, and a changed
  byte changes the row in the same pull request. A dialect's digest is inside every preparation it
  produces (`mappingDigest`), so a changed dialect changes every fixture's `preparation.json`, and a
  verification record made on the earlier bytes is a record of other bytes. An earlier entry is the
  manifest at an earlier commit.
- **Licences.** `licence` is an SPDX identifier, and the author's choice: a dialect is data, so its
  licence is whatever its author grants. The organisation's default is `Apache-2.0`, the licence of
  each of its repositories, the Exchange's included; the Exchange's contribution guide applies it to
  an entry's files unless the entry's `licence` names another licence that lets the Exchange publish
  it, and the contributor certifies the right to grant it. A fixture is recorded bytes of a system's
  records: an author who may not publish a system's records makes fixtures from records the author
  may publish.
- **The thank-you bot.** The repository runs the organisation's workflow that thanks a merged
  contributor and suggests another task, as the other repositories do.
- **A recorded no is a decision.** An entry, a system or a source kind the Exchange declines is
  recorded with the reason and the condition that would reopen it, as the catalog records its own
  (gateway #259, #260).
- **What the Exchange refuses**, each before merge: CI where its test or its scan recognises the
  case — a recognised credential shape, a local path, an entry with no fixture — and the maintainer
  who reviews the entry for everything else, in every file of the entry.
  - Credentials, tokens and keys, of any kind and in any file. A dialect names an input profile by
    its id and digest, a connection by its name and a header by its name, never a value (RFC 0018,
    Security and privacy).
  - Personal data, in a dialect, a fixture or a README.
  - Code of any kind. A dialect is declarative (RFC 0018 §1), and an entry holds no program, script,
    executable, image or package; the only program run over an entry is the specification's
    verifier, at the commit the repository's CI pins.
  - A dialect without fixtures: `fixtures` names at least one.

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
  the bytes, and the service's operator to trust for both. It may come second, serving the
  repository's manifest (§2); it is not a substitute for it.
- **No shared place.** The status quo: each deployment writes its own dialect and verifies it
  against nothing but its own runs. A counterparty can hold a preparation to its dialect (RFC 0018),
  but has no published dialect to compare it with, and a second reader has no fixtures but the
  Runner's nine.

## Compatibility

- **Core and the dialect.** Nothing in Core `0.2.0-draft`, its schema, its classes or its corpora
  changes, and nothing in RFC 0018's dialect format or its companion document. This record defines
  no conformance class.
- **The Exchange against a draft.** The repository depends on RFC 0018 while it is a draft: its CI
  pins this repository at a commit (`f821757` today) for the verifier. A change to the dialect
  format reaches the Exchange only when the Exchange moves its pin, by its own pull request; an
  entry the moved verifier answers otherwise is decided on that pull request.
- **The Desk** browses; it changes nothing in an entry, and nothing in its own inputs until an
  operator adopts one by review. The Desk producing the dialect format is Desk #398.
- **The Runner and the gateway** are unchanged. The Runner prepares from an adopted input dialect
  as from any mapping v2 document; the gateway holds a write to an adopted policy as to any policy.
  Adopting an input dialect with an `operation` source points its `profile` and `profileDigest` at
  the installation's own input profile, which changes the dialect's bytes and its digest
  (Unresolved question 7).

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
  merge, recipe literals and receipt metadata included (§3).
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
- **Resource use.** A desk reads the manifest within bounds, as it reads the connection catalog, and
  a verifier reads an entry's documents within RFC 0018 §12's bounds, refusing what exceeds them.

## Conformance

**None of JPS's.** This record defines no conformance class, and no claim of any JPS class can cite
an entry. An entry's check is the Exchange's own test (§4), at the specification commit the
repository pins. The repository aligns its tests to §3's table by its own pull request. At
`b516dd7`, the scaffold's tests held: positively, an example entry built from this
repository's staged `valid` vector, which is not an entry and is not in the manifest, holds to every
rule and gets a reading whose digest is its `preparationDigest`; negatively, a changed byte against
either manifest digest, an assertion that is not the sentence, an `id` that is not its path's, an
unknown member, an empty `fixtures`, both `versions` and `digests`, a verification record without
its members, a manifest out of `id` order or with an `id` twice; at a boundary, the empty manifest
the repository holds today; and adversarially, each credential shape and local path the scan is
written for, and a relative link that does not resolve.

**The verification record's form.** `verification` is an array, empty until an entry is verified,
of `{date, runner, runtime, readers, result}`, each member as §3's table gives it: `date`, the day
the readers ran; `runner` and `runtime`, the release tags of the Runner and the runtime at which the
fixtures hold; `readers`, the preparation verifiers that agreed, each named as
`<repository>/<path>@<commit>` so that it can be found again — the Runner's `verify-run`, or the
specification's `tools/dialect_verify.py`, at a commit; and `result`, `"agree"`, the only value the
format gives. A reader that disagrees adds no record: its disagreement is a finding
against the entry or the reader, recorded where it was found. A record is added by a pull request
after the run it records, and is a record of the bytes it was made on (§6).

## Implementation

1. **The repository.** `judgment-pack-exchange`, created on 2026-10-14. Its first commit,
   `b516dd7`, scaffolds the layout, `docs/entry-format.md`, an empty `manifest.json`,
   `tests/test_entries.py`, the example entry, the contribution rules, the licence and the thank-you
   bot. Its CI job, `entries`, checks out this repository at `f821757`, the merge of RFC 0018, and
   runs the tests; it passed on that commit. It holds no entries.
2. **A desk's browse.** Proposed, not built, and tracked by no issue yet. The Desk would read the
   manifest at a pinned commit through the connection-catalog pattern (§2); show each entry's title,
   direction, pack, requirements, source kinds, licence, author, assertion and verification records
   as the entry gives them; fetch an entry's files and hold them to the manifest's digests; and hand
   an entry the operator adopts to its inputs, which produce the dialect format (Desk #398). It runs
   nothing an entry holds.
3. **A hosted registry**, later (§2).
4. **The seed entries, planned and not verified.** Neither is written. Each is an input dialect with
   its write-back, so each is of direction `both` (Unresolved question 6). Their verification
   records are added after the maintainer's first live checks of the two connections, on gateway
   v0.13.0 or later.
   - **Azure DevOps work items into a triage pack.** Input: the organisation's work items, read by
     the `azure-devops` connection (a WIQL query, items by id, or both as one read). Output: the
     work item's state, written through the `azure-devops` write-back platform's
     `wit_work_item_write` under the gateway's worked policy, which fixes `action` to `update`,
     tests the revision first, fixes the state the outcome maps to, binds the item's id and revision
     to the record's facts, and is closed (`docs/design/engine-config.md`, "The write-back
     platforms"; its open limit is gateway #267).
   - **A Databricks table into a pack.** Input: a table read by the `databricks` connection, one SQL
     statement on its warehouse with its values bound as named parameters. Output: a Unity Catalog
     function the workspace's owners write, called through its managed MCP server on the
     `databricks` write-back platform, each of its parameters bound to a fact (the same design
     note's worked `record_approval`).
   - **What each needs.** A connection profile; an input profile for the gateway source the reads
     come through; fixtures recorded from a real workspace or organisation whose recorded records
     hold no personal data — a project or a table kept for the purpose, since a recording cannot be
     edited afterwards (Security and privacy); and a source kind the Exchange's test can recompute.
     Both connections declare their reads of shape `http`, and an `operation` source admits a
     profile of shape `mcp` only (RFC 0018 §4.1). The Databricks read fits RFC 0018's proposed `sql`
     kind, which no preparer writes and no reader reads yet; the Azure DevOps read is in the
     connection's own request form, which no kind of RFC 0018 describes (`http` is `adapter-http`'s
     request). Until then a seed's input fixtures are held by their digests only (§4), or its reads
     go through an MCP server the operator runs as a source of shape `mcp`, as the gateway's
     adapters README documents the organisation's local Azure DevOps server (Unresolved question 8).

**The readers.** The Exchange's test runs `tools/dialect_verify.py`, the second reader of RFC 0018,
written by that text's author; the Runner's `verify-run` is the first. Both are this project's, and
RFC 0000's bar of two independent implementations is not claimed.

## Unresolved questions

1. **Signing entries, and by whom.** An entry is pinned by the manifest's digests and the
   repository's history, and nothing is signed. Whether an author signs an entry, the Exchange signs
   the manifest, both or neither; with which key; and what a desk holds a signature to, are open. A
   hosted registry makes the question pressing.
2. **Entry versions against pack versions, and a range syntax for `pack.versions`.**
   `pack.versions` takes the form the pack's own versioning gives, 1 to 64 characters, and Core
   gives a `MAJOR.MINOR.PATCH` version and no range: which range syntax, if any, is open; the
   scaffold's example writes `>=0.1.0`. A published pack version SHOULD be
   immutable (Core §11), not MUST, so a version names content less firmly than a digest. And how an
   entry follows a pack is open: a pack version that changes a fact pointer breaks a dialect, and
   whether its successor is a new entry, the same `id` with new digests, or an entry per pack
   version, is undecided.
3. **Fixtures the verifier cannot recompute.** Such a fixture is held by its digests only, and
   establishes that its bytes were recorded. Whether an entry none of whose fixtures is recomputed
   is published at all, or published and marked, is open. For `research` it stays partly so for
   good: once a reader reads the kind, a research fixture's derivation is recomputable, but its
   research record, a model's answer, never is, and is held by its digest as every acquisition is.
4. **The hosted registry's identity.** Who runs it, under what name and key, how a desk pins it, and
   what a desk does when the registry and the repository disagree.
5. **Output dialects before the gateway publishes policy vectors.** RFC 0018 defers the output
   side's vectors, and the gateway publishes none. An output dialect has no preparation, so a
   fixture's `preparationDigest` has nothing to name for it, and `dialectVersion`, an integer of 2
   or more equal to the document's `version`, has nothing to equal in an output dialect, whose
   `outputVersion` is the string `"1"`. Whether the Exchange
   carries output dialects now, held by review and by the gateway's own tests of its policies, or
   waits for vectors, is open.
6. **An entry of direction `both`.** RFC 0018 §10 keeps the input side and the output side as two
   documents, each with its own digest, so that a version-2 dialect stays the Runner's mapping v2
   byte for byte. The format holds one `dialect.json` with one `digest`. Whether a `both` entry
   holds one file per side, is two entries that name each other, or is one document of both, is
   open, and both seed entries are of this direction.
7. **A dialect pins its installation.** An `operation` source names its input profile by id and
   digest (RFC 0018 §4.1), and a profile pins the gateway's key, source, authority, adapter, shape
   and endpoint (§5.1 there). An entry's dialect therefore pins the profile its fixtures were
   recorded under, and an operator who adopts it under another profile changes its bytes and its
   digest: the Exchange's verification is of the entry's bytes, not of the adopted copy. Whether
   adoption is defined as that one substitution and a desk checks that nothing else changed, or a
   dialect names its profile otherwise, which RFC 0018 does not provide, is open.
8. **The seed entries' source kind.** Through the two connections as they stand, neither seed's
   input is a kind the Exchange's test can recompute (Implementation). Whether the seeds wait for
   version 3 and a preparer that writes `sql` and a kind for the Azure DevOps connection's reads, or
   are first published over sources of shape `mcp` that an operator runs, is open.

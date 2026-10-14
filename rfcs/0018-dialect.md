# RFC 0018: The dialect

- Status: Draft
- Type: Standards track (a companion document of the specification, with a reader conformance class
  and a vector corpus of its own)
- Created: 2026-10-14
- Issue: [#141](https://github.com/Judgment-Pack/judgment-pack-spec/issues/141); the direction it
  serves is [#142](https://github.com/Judgment-Pack/judgment-pack-spec/issues/142)

> This is an open proposal, not part of the specification. See
> [RFC 0000](0000-rfc-process.md) for the process and evidence bar.
>
> **The decision this records.** Issue #141 asked whether the input mapping and the preparation the
> reference Runner defines become part of the specification as a companion document, normative for a
> new reader class, the *preparation verifier*, and for nothing else. The maintainer's decision of
> 2026-10-14, recorded on the issue, names the companion document the **dialect**, not the input
> dialect, and scopes it to every way a pack's facts and evidence are obtained and derived — an
> AI-assisted research recipe, an API call with its request body and header configuration, an MCP
> query, a SQL statement, and the other data integrations the gateway's sources and connections
> admit, each declared and pinned — with the derivations into facts and evidence availability, the
> calculated values with their lineage, and an output side. A reader recomputes what is recomputable
> and holds the rest by its recorded digest, so what a dialect establishes differs by part, and this
> RFC states it per part. Issue #142 records the direction it serves: dialects published in the
> Judgment Exchange. This RFC is the proposal that decision calls for. Taking the format up decides
> where it belongs; it does not accept this text, which becomes normative only when this RFC is
> accepted, by [RFC 0000](0000-rfc-process.md)'s process and under the
> [interim review regime](../GOVERNANCE.md#interim-review-regime).
>
> **What this draft adds, and what it does not.** Three things are added with this draft, none of
> them normative. The text under Specification, §§1–14, is added too as the proposed companion
> document
> [`spec/dialect.md`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/spec/dialect.md),
> word for word, so that a second reader could be written from a document of its own. The Runner's
> nine preparation vectors are added byte for byte, **staged**, in
> [`conformance/dialect/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/dialect).
> And the second reader, `tools/dialect_verify.py`, is added, with tests that run it over every
> vector. While this RFC is a draft the companion document is normative for nothing: Core §1.1 does
> not list it, the site publishes its text only as this RFC, and no release bundle carries it or the
> vectors (`.gitattributes`, `export-ignore`). That departs from [RFC 0017](0017-checkpoint-witness-statement.md),
> whose companion document was added when it was accepted; the reason is the second reader, which
> [RFC 0000](0000-rfc-process.md)'s evidence bar asks for before acceptance and which is written
> from a document. Nothing here changes Core `0.2.0-draft`, its schema, its four conformance classes
> or either of its corpora, and nothing asks the Runner, the runtime or the gateway to change.
>
> **The source.** The Runner's
> [`docs/MAPPING-V2.md`](https://github.com/Judgment-Pack/judgment-pack-runner/blob/05636eda96a9588279d61a6272625be859a28117/docs/MAPPING-V2.md)
> at commit `05636eda96a9588279d61a6272625be859a28117`, the head of the Runner's pull request 77,
> which publishes the vectors for a second reader; the vectors were copied from that commit, and the
> pull request reached the Runner's `main` as commit `82116bfab7705f74ca3e493c9722dd3831c7418f`,
> with the same files. Its subsection "The canonical form of a
> preparation" is taken up as the normative text, so that `MAPPING-V2.md` can point here when this
> RFC is accepted. Beside it: the Runner's design record for calculated values; the portable
> derivation rule, at the experiments repository's commit `96fa95874bfaa4d5a01c0c111fd8b5b6613c881c`,
> which the Runner vendors; the reference gateway's `SPEC.md` at `v0.15.0` (§1.1, §1.2a, §6) and its
> engine configuration's `decisionPolicy`; and the reference runtime's ADR-0050. "Runner, *name*"
> and "gateway §n" in the Specification mean those documents at those commits.

## Summary

A **dialect** is a pack's terms spoken in a system's: the declared, reusable translation between a
system and a pack. Its input side says how the facts and the evidence availability a pack's
evaluation takes are obtained — from sources, each a declared acquisition of one kind, pinned so
that a reader can hold the bytes it produced by their digest — and how they are derived from those
bytes: case and source parameters, copies and derivation rules, calculated values with their
lineage, and the classes each target admits. Its optional output side says how a disposition
becomes the arguments of a write, as the gateway's decision policy does. Applying the input side at
one instant to a case and to concrete acquisitions produces a **preparation**: what each target was
derived from, under which receipt, at which instant, in a canonical form whose SHA-256 is the digest
the Runner passes the runtime and the runtime records as the evaluation record's binding.

This RFC proposes the dialect as a companion document of the specification, with one reader
conformance class, the *preparation verifier*, which recomputes a preparation from the dialect, the
case, the acquisitions and the input profiles it trusts, and holds a record's binding to it.
Version 2 of the dialect document is the Runner's mapping v2, byte for byte, and the preparation's
canonical form is the Runner's, stated here. Version 3 is proposed, with four source kinds more —
`http`, `sql`, `web` and `research` — defined and not claimable, since nothing implements them and
no vector holds them. The output side is defined by reference to the gateway's decision policy, its
vectors deferred to a later RFC.

What a preparation establishes is stated per part. A derivation is recomputable, and a verifier
that recomputes it establishes it itself. An acquisition's bytes are not: they are held by their
digest, and what they establish is the gateway receipt's business, byte lineage and not truth. A
research record establishes the least of all. The Runner's nine vectors are staged byte for byte. A
second reader, written from the text, recomputes all nine preparations byte for byte, and its
reports agree with the Runner's on the surface the two share, the verification of a preparation; the
one check it leaves out, of an export's retained result against its record, is the export's, not a
preparation's.

## Problem

Core §8.2 takes one facts document and one evidence-availability document, and "defines no fact
namespace, merging, or acquisition". That boundary is right for Core, and nothing here moves it. But
a record now commits to how those documents were made. The reference runtime records a caller's
binding on the evaluation record, as given and never interpreted (runtime ADR-0050), and for a run
the Runner prepared, that binding is the SHA-256 of the Runner's preparation in the Runner's
canonical form. Today only the Runner's own verifier, `verify-run`, can read a preparation and hold a
record's binding to it. A third party that holds a record, its receipts and a preparation — the
counterparty, an auditor — cannot check the binding without the Runner's code and the Runner's words,
which describe one implementation, move with its releases, and sit beside its service, its exports
and its journal.

Two more parties need the format to be nobody's code. The Desk's inputs — import recipes, selected
records, and the research line's recipes and research records (Desk #369, #371) — produce mappings
and hand them to the Runner, and each new kind of input is today a change to the Runner with no
stated format. And the Judgment Exchange (#142) is to hold dialects as published entries, each
verified by running it on its fixtures: an entry whose input side is one program's convention can be
verified by no one else.

The [RFC index](README.md) states the rule this record applies: "A format that independent tools must
agree on is a candidate for the specification. An algorithm or engine belongs to a runtime. A hosted
service belongs to a product." The dialect and its preparation are the first kind. The Runner's
service — its jobs, exports and journal — and the gateway's acquisition are the others, and are
cited here, not taken up.

The checkpoint witness statement was in the same situation while it lived only in the gateway's
`SPEC.md`, and [RFC 0017](0017-checkpoint-witness-statement.md) resolved it by taking the format up as
a companion document, with the gateway's vectors byte for byte. The same move applies here.

## Evidence

- **The format, in use.** The Runner's mapping v2 is "implemented in Runner and Desk's advanced Jobs
  mapping workflow" (`MAPPING-V2.md`): typed case and source parameters; `operation` sources pinned
  by an installation's input profile and its digest, with a maximum age; copies and the vendored
  derivation rule; calculated values (the Runner's issue #14); admission by class. The Runner passes
  the preparation's binding to the runtime on every operational evaluation since its `v0.9.0`, and
  the runtime records it since its `v0.31.0` (ADR-0050).
- **The vectors.** Nine, generated once by the Runner from fixtures its tests write with a released
  runtime, and frozen: the Runner calls them "hand-maintained normative data". Two of the Runner's
  tests hold it to them, byte for byte, and run `verify-run` on each. They are a calculated run,
  signed, witnessed and bound; the same recomputed a second later; a record from before the binding;
  a binding of another scheme; altered lineage; a retained result that differs from its record; two
  sources whose rules read parameters no receipt commits; a case-only run with the characters the
  canonical form escapes; and the case parameters `-0`, 2⁵³−1 and −(2⁵³−1), kept as written.
- **A second reader, from the text.** `tools/dialect_verify.py` is a preparation verifier written
  from the companion document's words, from the two sections of the checkpoint witness statement it
  adopts, and from RFC 8032, and from nothing else: its author did not read the Runner's code. The
  Runner's `verify-run` is the first reader. The second recomputes every vector's preparation byte
  for byte equal to its `preparation.json`, with the digest its `preparation.sha256` states; gives
  every vector the answer the staged manifest records; and, wherever the class reports them, agrees
  with `verify-run`'s report on `targetsByClass`, `unsignedParameters` and `unsignedFreshness`, and
  with the export on the facts and evidence-availability documents. It uses Python's standard
  library alone, Ed25519 included.
- **The output side.** The gateway's decision policy holds a write to its decision record: `bind`
  (gateway ADR-0011), `fix` and `closed` (gateway ADR-0016, gateway #258, released in `v0.14.0`), and
  `requireSignedRecord` (gateway ADR-0012), its digest carried by every action receipt it governs.
- **The research line.** Desk #369 and #371 specify an ICP research recipe — a prompt and reviewed
  constraints, an AI connection and model by name, candidates with field-level supporting evidence,
  a run record — and its handoff into pack and graph evaluation through mapping v2's generated-input
  admission. Neither is built as a writer of this format yet; the `research` kind is the form they
  would write.

**The standing of that evidence.** The second reader is this project's, and its author is the text's:
an AI coding agent, Anthropic's `claude-opus-5-5`, working from the maintainer's brief, which drafted
the companion document from the Runner's documentation, the derivation rule's specification, the
gateway's `SPEC.md` and the vectors, examined as files and with small scripts of its own that took
their digests and checked their signatures, and then wrote the reader from the companion document
alone, those scripts set aside. The text was written with the vectors in view. Their agreement is evidence that the
text is precise enough for one author to implement on the surface the vectors exercise — the case
and `operation` sources; copies, and rules of `all`, `equalsParam`, `freshWithin` and `always`;
`$param` and `$text`; a calculator that computed; string and integer parameters; one and two
acquisitions in one session — and not that it interoperates, nor that it is right where the vectors
are silent. This RFC does not claim [RFC 0000](0000-rfc-process.md)'s bar of two independent
implementations.

**What writing the reader found.** Three things the text did not say, each fixed in the text and not
in the reader: whether a copy may name one evidence requirement twice (it may not); where a source
parameter's `parameter-invalid` falls among a source's findings (first); and where a failure of the
case's own read falls (after the case's parameters, before every source). And eight rules that
neither the Runner's documentation nor its vectors decide, on which the text takes a position and
says so (Unresolved question 1). One vector is answered otherwise than `verify-run` answers it, by
design: `disposition-differs-from-audit` alters the Runner's export, not the preparation or the
record (Conformance).

## Specification

This section is the text proposed to land: the proposed companion document `spec/dialect.md`, its
§§1–14 word for word, each heading one level down. The companion document adds only its Status,
which says what this RFC's preamble says. Its key words **MUST**, **MUST NOT**, **REQUIRED**,
**SHOULD**, **SHOULD NOT** and **MAY** are to be interpreted as described by BCP 14 when, and only
when, they appear in all capitals.

### 1. Terms and the canonical forms

A **dialect** is a pack's terms spoken in a system's: the declared, reusable translation between a
system and a pack. Its **input side** says how the facts and the evidence availability an
evaluation takes (Core §8.2) are obtained and derived; its **output side**, which is optional, says
how a disposition becomes the arguments of a write (§10). A dialect is declarative — pointers,
types, templates, derivation rules and bindings — and is never code.

The input side is one JSON document, the **dialect document** (§2). A **preparer** applies it, at
one instant, to a **case** — one JSON document, what an operator typed or a caller sent for one
evaluation — and to the **acquisitions** its sources name, and writes a **preparation** (§9): how
each fact and each evidence availability was derived, from which acquisition, under which receipt,
at which instant. The reference preparer is the Runner. A **preparation verifier** (§14) reads a
preparation by recomputing it from the same inputs (§11).

A **source** is one declared acquisition, of one **kind** (§4). An **acquisition** is what one call
for a source returned: for an acquired kind, a gateway's answer and the receipt it signed (§5); for
the case, and for a file the operator selected, bytes the operator supplied. Every source has a
**class** (§8.2): `asserted`, `record` or `generated`. A **target** is a fact pointer or an evidence
requirement that a source writes.

A **pointer** is an RFC 6901 JSON Pointer. A pointer **resolves** in a value when each of its
tokens names a member or an index that exists; otherwise it yields **absent**, which is not `null`.
A token names an array's element when it is `0`, or a digit other than `0` followed by any digits,
and its value is below the array's length; a token of any other form, or of any length beyond the
array's, names none, and no limit of an implementation's numbers applies to it.

A **timestamp** is a string of the form `YYYY-MM-DDThh:mm:ssZ`, a digit where each letter but `T`
and `Z` stands: UTC, whole seconds. Its **instant** is its count of seconds since
`1970-01-01T00:00:00Z` in the proleptic Gregorian calendar, when the date and time it writes exist:
month `01` to `12`, a day the month has, hour `00` to `23`, minute and second `00` to `59`. A string
of the form that names no time, such as `2026-02-30T00:00:00Z`, has no instant, nor has any other
string.

Hexadecimal is lowercase throughout. A **digest** is the string `sha256:` followed by 64
hexadecimal characters; the **digest of** some bytes is that string for their SHA-256. A **key** is
the 32-byte encoding of an Ed25519 public key, written as 64 hexadecimal characters; its **key
identifier** is the first 32 hexadecimal characters of the SHA-256 of the 32 bytes. A key is held to
the key rule of the checkpoint witness statement, its §5, before anything signed under it is read,
and a signature to the equation of that section: RFC 8032's check without the cofactor, with a
canonical scalar.

**Reading a document.** Every JSON document this document names — a dialect, a case, the
acquisitions, the profiles, a preparation, a record — is read strictly: exactly one JSON value
(RFC 8259), with only whitespace around it; no member name given twice in one object; every string
well-formed Unicode, a lone surrogate written as an escape included. A document that is not so
read is refused (§11). A number is read as its literal, its characters kept: a reader that reads a
number as a binary floating-point value and writes it again does not read it as this document
does. Every object this document defines is closed: a member it does not list is refused, and so
is a member it lists that is of another type or form. Member names are matched exactly, so a name
that differs from a listed one only by case is an unknown member.

**Integers.** An **integer** is a number whose literal is an optional `-` followed by `0`, or by a
digit other than `0` and any further digits, with no fraction and no exponent, and whose value is
from −(2⁵³−1) to 2⁵³−1. `-0` is an integer, and wherever a preparation carries one it keeps its
literal (§9.5). `1.0`, `1e2` and `9007199254740992` are not integers.

**The gateway canonical form**, `canon`, of a value is the canonical form of the checkpoint witness
statement, its §1, which is the gateway's (gateway §1.1). Its domain is objects with no member name
given twice, arrays, well-formed strings, integers, `true`, `false` and `null`. Its output orders
an object's members by the code points of their names, keeps an array's order, has no whitespace,
writes a string as raw UTF-8 with only `"` and `\` and the characters below U+0020 escaped (`\"`,
`\\`, `\b`, `\f`, `\n`, `\r`, `\t`, and `\u00` with two hexadecimal digits for every other one),
and writes an integer in decimal digits, `-0` as `0`. A value outside the domain, a number that is
not an integer above all, has no `canon` form and no digest. Every digest of §§2–8 is the digest of
a value's `canon` bytes: a dialect's, a profile's, a read's, an acquisition's result's, and the
commitment to a request.

**The preparation's canonical form** (§9.5) is another form, the one a preparation is digested in:
it escapes `&`, `<`, `>`, U+2028 and U+2029, and keeps each number's literal. The two forms are
never interchanged.

### 2. The dialect document

The dialect document is one JSON object. Its version 2 is the Runner's mapping v2 document: a
mapping v2 document the Runner accepts is a version-2 dialect document, with the same bytes and the
same digest.

| Member | Form | Meaning |
| --- | --- | --- |
| `version` | the integer `2` | the dialect version, per which the source kinds (§4) and every form of this document are closed |
| `case` | an object (§3), REQUIRED | the case's parameters, and the facts and evidence copied from the case |
| `sources` | an array of at most 16 sources (§4), optional | absent is the empty array |
| `admits` | an object (§8.2), optional | the classes a target admits, where they are not the default |
| `unmapped` | an array of distinct pointers, optional | fact pointers a pack reads that the author acknowledges are not mapped |
| `unmappedEvidence` | an array of distinct non-empty strings, optional | evidence requirements a pack declares that the author acknowledges are not mapped |
| `provider` | the string `""`, optional | a member of the Runner's version-1 mapping, which its encoding of a version-2 document carries empty |
| `facts`, `evidence` | `null`, optional | the same |

`unmapped` and `unmappedEvidence` are for review of a dialect against a pack's inventory (Runner,
"Release checks, runtime and offline verification"): no preparation reads them, and a verifier
holds them to their form and to nothing else.

The **dialect digest** is the digest of the document's `canon` bytes, every member it holds
included. The same document with an optional member written out, as the Runner's encoding writes
`provider`, `facts` and `evidence`, or left out, has another digest: a verifier takes the document
as it was given and adds or removes nothing. A document outside the `canon` domain is refused.

Version 1 is no dialect: the Runner's version-1 file mapping has no preparation. The numbering is
the Runner's, kept so that every mapping v2 document is a version-2 dialect document byte for byte.

### 3. The case and parameters

`case` is an object of exactly `parameters`, an object, optional, absent being the empty object;
`facts`, an array of fact copies; and `evidence`, an array of evidence copies (§6.2). The case is
the source named `case`, of class `asserted`: what `facts` and `evidence` copy from the case
document is what the operator supplied.

A **parameter** has a name, a type and a value. The types are `string`, a JSON string; `integer`,
an integer (§1); and `timestamp`, a string that has an instant (§1). A name is a non-empty string,
and `runAt` is reserved.

- A **case parameter** is declared in `case.parameters` as `"name": {"pointer": P, "type": T}`,
  exactly those two members. Its value is the case document's value at `P`, which MUST resolve and
  MUST be of type `T`; otherwise the preparation fails, `parameter-invalid`.
- A **source parameter** is declared in a source's `parameters` (§4) as
  `"name": {"from": S, "pointer": P, "type": T}`, exactly those three members. `S` names a source
  earlier in `sources`, and `P` is a fact target of `S` (§8). Its value is the value at `P` in the
  facts of `S`'s claim (§6), taken only when that claim's `acquisitionStatus` is `resolved` and it
  gives a value at `P`. When it does not — `S` was skipped, its claim is not `resolved`, or it gives
  no value at `P` — the source that declares the parameter is **skipped** (§9.2). A value that is
  there and is not of type `T` fails the preparation, `parameter-invalid`. A source parameter
  cannot have the name of a case parameter, and `S` cannot name the source that declares it or a
  later one.
- **`runAt`** is in every scope, of type `timestamp`. Its value is the preparation's `verifiedAt`
  (§9.1). A derivation rule may read it (§6.3); a request template that names it is refused (§4.1).

A source's **scope** is the case parameters, its own source parameters, and `runAt`, at most 64
parameters. The case's scope is the case parameters and `runAt`.

### 4. Sources and their kinds

A source is an object with these members, and those its kind adds:

| Member | Form | Meaning |
| --- | --- | --- |
| `name` | a non-empty string, not `case`, distinct among the sources | the source's name, which its outcome, its lineage entries and its acquisition carry |
| `kind` | a kind of the document's version | what is declared, and how it is acquired |
| `parameters` | an object of source parameters (§3), optional | |
| `read` | a read (§6), REQUIRED | how the value acquired becomes a claim |

The kinds:

| Kind | Version | Class | What is declared | Vectors |
| --- | --- | --- | --- | --- |
| `operation` | 2 | the profile's | a tool of a gateway source an input profile pins, and a template of its arguments (§4.1) | yes |
| `selected-file` | 2 | `asserted` for `local-file`, the profile's for `google-drive` | a document the operator selected (§4.2) | none |
| `http` | 3, proposed | the profile's | a request to a gateway HTTP source: method, path, query and body templates, header names (§4.3) | none |
| `sql` | 3, proposed | the profile's | a statement on a connection, with its bound parameters (§4.3) | none |
| `web` | 3, proposed | the profile's | a public page by URL, through the gateway's web source (§4.3) | none |
| `research` | 3, proposed | `generated` | an AI-assisted research recipe (§4.3) | none |

A version-2 document that names a kind of version 3 is refused. **A kind without vectors is
defined, and not claimable**: a verifier's claim names the kinds it reads (§14), and may name only
kinds that the vectors published with its specification version exercise. Today the staged
vectors exercise `operation` and the case, and none is published.

#### 4.1 `operation`

An `operation` source has, besides the members of §4, exactly:

| Member | Form |
| --- | --- |
| `profile` | a non-empty string: the `id` of an input profile (§5.1) |
| `profileDigest` | a digest: that profile's digest |
| `maxAge` | an integer from 1 to 86400: seconds |
| `arguments` | an object of exactly `tool`, a non-empty string, and `arguments`, a template |
| `calculation` | an object (§7), present exactly when the profile is a calculator's |

The profile's `shape` MUST be `mcp`, and `tool` MUST be among the profile's `tools`.

**Templates.** A template is a JSON value in which an object one of whose member names begins with
`$` is a **template form**, which MUST be exactly one of:

- `{"$param": N}`, `N` a string: replaced, as a whole value, by the value of the parameter `N`, of
  any type, its literal kept;
- `{"$text": T}`, `T` a string: replaced by the string `T` with each **placeholder** in it replaced.
  A placeholder is `{{`, a parameter name, and the next `}}`; it MUST name an `integer` parameter,
  and is replaced by that integer's decimal digits as `canon` writes it, `-0` as `0`. A `{{` with no
  `}}` after it is refused, and a `}}` outside a placeholder is taken as it is. (No vector decides
  the last two rules.)

Every other value of a template is literal, taken as it is, an object or an array member by member.
A name a template form gives MUST be in the source's scope, and MUST NOT be `runAt`, which no request
can carry. A literal object whose only member's name begins with `$` cannot be written. The
**request** of an `operation` source is `{"tool": tool, "arguments": A}`, `A` its instantiated
template, and MUST be in the `canon` domain.

A request **commits** a parameter when it carries it unambiguously: as a whole value, `$param`,
anywhere in it, or in a `$text` whose placeholders name it and no other parameter. A `$text` whose
placeholders name two or more parameters commits none of them: `{{a}}{{b}}` renders `1` and `23` as
it renders `12` and `3`.

#### 4.2 `selected-file`

A `selected-file` source names a document the operator selected, by its member `provider`:
`local-file`, a file on the operator's machine, of class `asserted`, with no profile, no `maxAge` and
no request; or `google-drive`, a Drive file read through a gateway source a `drive` input profile
pins, with `profile`, `profileDigest`, `maxAge` and `arguments` as in §4.1, its `fileId` and the
consumed selection `grant` resolved from typed case parameters. Its acquisition is the Runner's
selected snapshot (Runner, "Supported input and trust configuration"), whose form this document
does not restate. The kind is defined, and not claimable: no vector holds one, and a version that
admits it to a claim states the snapshot's form first.

#### 4.3 Kinds proposed for version 3

Version 3 is version 2 with four kinds more. It is proposed: no preparer writes it, no verifier
reads it, and no vector holds it. The forms below are what a writer, such as the Desk's inputs or an
entry of the Exchange, needs to declare one; the first implementation's vectors will fix each
request's exact bytes, and may change them. A source of each of these kinds is an object of exactly
the members of §4 — `name`, `kind`, `parameters` (its source parameters, as every source's) and
`read` — with `profile`, `profileDigest` and `maxAge` as in §4.1, and the members its kind names
below. Each is acquired through the gateway source its profile pins, so §5's checks apply with the
shape the profile names, and the value it acquires is read as every value is (§6).

- **`http`**, a request to a gateway source of shape `http` (the gateway's `adapter-http`):
  `method`, `GET` or `POST`; `path`, a template that yields a path under the profile's endpoint;
  `query`, optional, an object of string templates; `body`, optional, a template, refused beside
  `GET`; and `headers`, optional, the names of the headers the profile's source is configured to
  send, for review. A dialect names a header and never its value: values and credentials are the
  gateway's configuration and never a dialect's. The request is `{"method", "path", "query",
  "body"}`, as `adapter-http` reads one.
- **`sql`**, a statement on a connection the profile names, such as the gateway's Databricks
  connection: `statement`, a fixed string and never a template, so that the statement's structure
  and identifiers are fixed; and `bindings`, an array of `{"name", "type", "value"}`, each `value` a
  `$param` form, which the connection binds as the provider's named parameters. `bindings` is not
  `parameters`, which declares the source's parameters as every source's does, so a `sql` source
  can take a value from an earlier source and bind it. No text is substituted into a statement.
- **`web`**, one public page by URL through the gateway's web source (`adapter-web`, shape
  `http`): `url`, a string, or a `$param` form naming a `string` parameter. The request is
  `{"url": url}`, and the value acquired is the attachment record the web source returns.
- **`research`**, an AI-assisted research recipe asked of a gateway source whose profile is of
  class `generated`: the AI connection, by the profile's `source`, and its model. Its members are
  `question`, a string template; `constraints`, an object; `model`, the model's name, which MUST be
  the one the profile's source is configured to call; and `evidence`, the fields each answer MUST
  support with a source reference: a retrieved page's receipt or URL, an excerpt and a retrieval
  time. The request is the recipe, and the value acquired is the **research record**, held by its
  digest as every value acquired is. A profile of another class is refused. A research record that
  did not come back through a gateway source is no acquisition: it can enter a dialect only as a
  selected file, asserted.

### 5. Input profiles and acquisitions

#### 5.1 Input profiles

An **input profile** is an installation's public configuration for one gateway source: an object of
exactly

| Member | Form |
| --- | --- |
| `id` | a non-empty string, distinct among the profiles |
| `publicKey` | a key (§1): the gateway's |
| `class` | `record` or `generated` |
| `source`, `authority` | strings: the gateway's source name and authority label |
| `shape` | `airbyte`, `mcp`, `http` or `command` |
| `adapter` | an object of exactly `name` and `version`, strings, and `digest`, a digest |
| `endpoint` | a string, or `null` |
| `tools` | an array of distinct non-empty strings, optional, which a profile of shape `mcp` MUST give and MUST NOT give empty |
| `calculator` | an object of exactly `name` and `version`, strings, optional: the profile is a calculator's (§7) |

Its **digest** is the digest of its `canon` bytes. A calculator's profile MUST be of class `record`
and shape `mcp`. A profile whose key the key rule refuses is refused.

A profile is the installation's, never the dialect's: a dialect names a profile by its `id` and its
digest, and only an installation supplies one. A verifier is given the profiles it trusts, out of
band, as one JSON array, and MUST NOT take a profile or a key from a preparation, an acquisition or
an export. A source's **profile** is the trusted profile of its `profile` id, whose digest MUST be the
source's `profileDigest`; otherwise, and when a source does not fit its profile — an `operation`
whose profile's shape is not `mcp`, a tool the profile does not allow, a calculator's profile
without `calculation`, `calculation` without a calculator's profile — the finding is
`profile-mismatch`.

What a profile pins — the gateway's key, source, authority, adapter, shape, endpoint, class and
tools — is the installation's classification of a channel. It does not pin a credential, a
tenant's configuration or a model's weights, and an installation replaces a profile when a change
of those makes its classification wrong (Runner, "Decisions and ownership").

#### 5.2 Acquisitions

The **acquisitions** are one JSON object with a member for each source acquired, named by the
source's name, of the form `{"response": {"result": R, "receipt": E, "salts": S}}`, exactly: the
gateway's acquire answer (gateway §6) as the preparer kept it. `R` is any JSON value; `E` is an
object, a version-3 receipt (gateway §1.2a); `S` is an object of `args` and, optionally, `statement`,
each 64 hexadecimal characters. A source to be acquired that has no member is
`acquisition-missing`; a member for a source that is skipped (§9.2), for a `local-file` source, or
for no source is `acquisition-unexpected`.

An acquisition is held to its source and its profile, and any of these checks that fails is
`acquisition-invalid`:

1. `E.receiptVersion` is `"3"` and `E.kind` is `"acquisition"`, and each member this list reads is
   of the form gateway §1.2a gives it.
2. `E.keyId` is the key identifier of the profile's `publicKey`, and `E.signature`, 128 hexadecimal
   characters, verifies under that key by the equation (§1), over the ASCII bytes
   `judgment-pack-gateway/receipt/3:` followed by the `canon` bytes of `E` with its top-level
   `signature` member removed and every other member retained.
3. `E.source` and `E.authority` are the profile's `source` and `authority`; and
   `E.acquisition.adapter`, `E.acquisition.shape` and `E.acquisition.endpoint` are, as JSON values,
   the profile's `adapter`, `shape` and `endpoint`.
4. `E.argumentsCommitment` is `sha256:` followed by the hexadecimal SHA-256 of the 32 bytes `S.args`
   encodes, then the ASCII bytes `args:`, then the `canon` bytes of the source's request (§4.1).
5. `E.resultDigest` is the digest of `R`'s `canon` bytes; an `R` outside the `canon` domain fails.

Then its times, against the preparation's instant, `verifiedAt`: `E.acquisition.observedAt` and
`E.servedAt` MUST each have an instant no more than the source's `maxAge` seconds before
`verifiedAt` and no more than 30 seconds after it; otherwise `acquisition-stale`.

Then the sessions. The acquisitions of one preparation are in one of two forms: **they share a
session**, one `sessionId` at `callIndex` values that differ; or **each is alone in a session of its
own and is its session's first call**, each `sessionId` distinct, each `callIndex` 0. One acquisition
alone is in both. Taken in the order of `sources`, the first acquisition with which the acquisitions
so far are in neither form is `acquisition-sessions`. The form is read from the receipts and from
nothing else.

An acquisition's **citation** is `{"callIndex", "sessionId", "signature"}`, those three members of
its receipt.

These checks are receipt-only. They do not establish that a session is sealed or complete, that no
attempt was left out, or that a caller did not choose among valid answers, in one session or in two
(Runner, "Time, sessions, errors and retries"). The receipt's `caller`, its `statement`, its chain
(`prevSignature`) and its `witness` are the gateway's verifier's to read (gateway §1.4, §4), and are
not read here.

### 6. Reads

A **read** turns the **value read** into a **claim**, an object of exactly `facts`,
`evidenceAvailability`, `acquisitionStatus`, `reason` and `basis`. A source's `read` is an object of
`unwrap`, optional, and exactly one of `copy` and `rule`. The case's read is
`{"copy": {"facts": F, "evidence": V}}`, `F` and `V` the case's `facts` and `evidence`.

The **read digest** of a source is the digest of its `read`'s `canon` bytes, as the dialect writes
it; the case's is the digest of the case's read, so built.

#### 6.1 The value read

The value read starts as the acquisition's result, `R`, and for the case as the case document.
`unwrap` is an array of one to four pointers, applied in order: each MUST resolve, in the current
value, to a string that holds exactly one JSON value, read as §1 reads a document, which becomes the
current value; otherwise `read-failed`. An unwrap is not a count of records: a read that needs one
record guards it. An unwrapped value may hold numbers that are not integers, which a rule may
compare (§6.3) and no claim may carry.

For a source whose profile is a calculator's, the value read is held to §7 before the read applies.

#### 6.2 Copy

`copy` is an object of `facts`, an array of `{"target": P, "source": Q}`, and `evidence`, an array
of `{"requirement": I, "source": Q}`, each entry exactly those members; each array is optional, and
absent is the empty array. `P` is a fact target (§8.1), `I` a non-empty string, `Q` a pointer. A
copy names each requirement at most once, and one that names a requirement twice is refused with the
dialect. (No vector decides this.) The claim:

- `facts` starts as `{}`; for each entry whose `Q` resolves in the value read, that value is written
  at `P` (§8.1). An entry whose `Q` does not resolve writes nothing. (No vector decides this.)
- `evidenceAvailability` gives, for each entry whose `Q` resolves, `I` the value there, which MUST be
  `present`, `absent` or `unknown`, or the read fails, `read-failed`. An entry whose `Q` does not
  resolve gives `I` nothing. (No vector decides this.)
- `acquisitionStatus` is `resolved`, and `reason` is `copied`.
- `basis` is every entry's `Q`, of `facts` and of `evidence`, distinct, ordered by code point.

A value a copy writes MUST be in the `canon` domain, its numbers integers; otherwise `read-failed`.

#### 6.3 Rule

`rule` is a **derivation rule**, version 1: the portable derivation rule the Runner vendors, cited in
the Status, restated here whole.

A rule is an object of exactly `ruleVersion`, the string `"1"`; `parameters`, an object mapping each
parameter the rule reads to its type; and `clauses`, an array of one to 64 clauses, the last of
which has the `when` `{"op": "always"}`. Each parameter a rule declares MUST be in the source's scope
with the type declared, and its value is the scope's. A clause is an object of exactly `when`, a
condition; `claim`, a claim form; and `reason`, a string.

A condition is one of the objects below, each of exactly the members shown; `P` is a pointer into
the value read, and `N` and `M` name parameters the rule declares.

| Condition | True when |
| --- | --- |
| `{"op": "always"}` | always |
| `{"op": "exists", "field": P}` | `P` resolves |
| `{"op": "equals", "field": P, "to": X}` | `P` resolves to a value JSON-equal to the literal `X` |
| `{"op": "equalsParam", "field": P, "param": N}` | `P` resolves to a value JSON-equal to `N`'s value |
| `{"op": "isTrue", "field": P}` | `P` resolves to `true` |
| `{"op": "isDecimalString", "field": P}` | `P` resolves to a string that is `0`, or a digit other than `0` followed by any digits |
| `{"op": "freshWithin", "field": P, "asOf": N, "maxAge": M}` | `P` resolves to a string with an instant, `N`, of type `timestamp`, has an instant, and `0 ≤ instant(N) − instant(P) ≤` the value of `M`, of type `integer`, in seconds |
| `{"op": "all", "of": [C, …]}` | every condition listed is true, which the empty list is; evaluated in order, stopping at the first that is false |
| `{"op": "any", "of": [C, …]}` | some condition listed is true, which the empty list is not; evaluated in order, stopping at the first that is true |
| `{"op": "not", "of": C}` | `C` is false |

`all` and `any` list at most 64 conditions. **JSON-equal** compares type and value: numbers by their
mathematical value, so that `1` and `1.0` are equal; strings, booleans and `null` by value; arrays
element by element, in order; objects as sets of members. A number and a string are never equal.

A claim form is an object of exactly `facts`, an array of `{"pointer": P, "from": Q}`, each exactly
those members, `P` a fact target and `Q` a pointer into the value read; `evidence`, an object mapping
requirement ids to `present`, `absent` or `unknown`; and `acquisitionStatus`, one of `resolved`,
`absent` and `unknown`.

**Deriving the claim.** The **match** is the first clause whose `when` is true; the last clause
ensures there is one. A **leaf** is a condition other than `always`, `all`, `any` and `not`, and
each leaf that is evaluated looks up its `field`. The claim is:

- `facts`: `{}`, and for each entry of the match's `facts`, in order, the value at `Q` in the value
  read written at `P` (§8.1); a `Q` that does not resolve fails the read, `read-failed`, and so does
  a value outside the `canon` domain;
- `evidenceAvailability`: the match's `evidence`;
- `acquisitionStatus`: the match's `acquisitionStatus`;
- `reason`: the match's `reason`;
- `basis`: the `field` of every leaf evaluated while the `when` of each clause up to and including
  the match was evaluated, distinct, ordered by code point. A leaf after a stop in `all` or `any` is
  not evaluated, and adds nothing.

A rule not of this form — a member, a condition or a claim form outside it, an unknown `op`, a type
other than the three, a literal outside the `canon` domain, a last clause that is not `always` — is
refused with the dialect (§11).

### 7. Calculated values

An installation declares a calculator on an input profile, as `calculator` (§5.1). Declaring it,
the installation asserts that each tool the profile allows computes a deterministic function of the
inputs it echoes and the tables it reports, and calls no model. Nothing here can check that. A
calculator that calls a model is not a calculator: its profile is `generated`.

A source whose profile is a calculator's declares `calculation`, an object of exactly `inputs`, an
object mapping each input name to the name of a parameter in the source's scope, never `runAt`; and
`tables`, an object mapping each table name to an integer from 1 to 315360000, the most seconds its
contents may be old.

The value read MUST be an object whose member `calculation` is an object of exactly `calculator`, an
object of exactly `name` and `version`; `status`, one of `computed`, `input-missing` and
`cannot-compute`; `inputs`, an object giving each input the calculator used, by name, with its
value; and `asOf`, an object giving each table it read, by name, with a timestamp. That answer is
held to the source, and any of these checks that fails is `calculation-invalid`:

- `calculator` is the profile's `calculator`;
- every input it echoes is bound in `calculation.inputs`, and its value has the same `canon` bytes
  as the value of the parameter it is bound to: `"7"` is not `7`;
- every table it reports is named in `calculation.tables`, with a timestamp that has an instant;
- when `status` is `computed`, every input bound is echoed, and every table named is reported, as of
  no more than its limit before `verifiedAt` and no more than 30 seconds after it.

When `status` is `computed`, the source's read applies to the value read. Otherwise it does not
apply, and the claim is: `facts` `{}`; `evidenceAvailability` giving `unknown` to each evidence
target of the source (§8); `acquisitionStatus` `unknown`; `reason` `calculation-input-missing` or
`calculation-cannot-compute`; and `basis` `["/calculation/status"]`. A calculator that could not
compute has answered about the case; a stale table, or an answer about other inputs, is a fault of
the source, and fails the preparation.

Each lineage entry of a calculated source that was acquired carries `calculation` (§9.3), an object
of: `calculator`, `status` and `asOf`, as answered; and `inputs`, an array with one object for each
input echoed, ordered by the input's name, of exactly `name`, the input; `parameter`, the parameter
it is bound to; and `source` and `pointer`, where that parameter's value came from: `"case"` and its
case pointer, or the earlier source's name and its fact pointer. The values echoed are not repeated:
the acquisition holds them.

### 8. Targets, classes and admission

The **targets** of a source are its fact targets and its evidence targets, fixed by the dialect and
not by what an acquisition returns: for a copy, its entries' `target` pointers and `requirement`
ids; for a rule, every pointer of every claim form's `facts`, and every requirement of every claim
form's `evidence`, over all clauses. Every target is recorded in the lineage (§9.3), with a value or
without.

#### 8.1 Facts and evidence

A **fact target** is a pointer other than the empty string. Writing a value at it in a document
creates each object on the way, every token naming an object member. No fact target of one source
may equal another, or be a prefix of another by whole tokens, of the same source or another, the
case included; no requirement may be an evidence target of two sources; and there are at most 256
fact targets and 128 evidence targets in all. A dialect that breaks one of these is refused.

A preparation's **facts document** is `{}` with, for each outcome in order (§9.2) and each fact
target its claim gives a value, that value written at the target. Its **evidence-availability
document** is an object giving, for each outcome in order, each requirement its claim's
`evidenceAvailability` names, that value, `unknown` included. (No vector decides that `unknown` is
written rather than left out.) They are the facts document and the evidence-availability document
an evaluation takes (Core §8.2), and those its record carries (§11).

#### 8.2 Classes and admission

A target's **class** is its source's: `asserted` for the case and a local file, the profile's for
every other source. `record` names the acquisition channel, a signed read of a system, and not the
authorship or truth of every byte the system holds; `generated` names a model's answer.

A source's **generated influence** is true when its class is `generated`, or when a source parameter
it declares comes from a source whose generated influence is true; each of its targets carries it.
A dependency so cannot erase a model's influence. (No vector holds a generated source, so no vector
decides this.)

Each target **admits** `asserted` and `record` by default. `admits`, an object of `facts`, mapping
fact targets to arrays of classes, and `evidence`, mapping requirements to arrays of classes, both
optional, replaces the list of each target it names. A target is admitted when its class is in its
list and, when its generated influence is true, so is `generated`. Every target is held to it, one no
acquisition reached included; a target not admitted is `admission-refused`. A target named in
`admits` that no source writes is refused with the dialect.

### 9. The preparation

#### 9.1 Members

A preparation is a JSON object of exactly:

| Member | Form | Meaning |
| --- | --- | --- |
| `version` | the integer `2` | the preparation's version, the dialect's |
| `verifiedAt` | a timestamp | the instant: the one every freshness check is held to, and the value of `runAt` |
| `mappingDigest` | a digest | the dialect digest (§2) |
| `verification` | the string `verified acquisitions; session sealing and input truth are not established` | the preparer's account of its checks, the same in every preparation of this version |
| `cites` | an array | every acquisition's citation (§5.2), ordered by `callIndex`, those of one index in the order of `sources` |
| `lineage` | an array | §9.3 |
| `outcomes` | an array | §9.2 |

#### 9.2 Outcomes

There is one outcome for the case, first, and one for each source, in the order of `sources`. A
source is **skipped** when a source parameter it declares has no value (§3): it is not acquired and
its read does not apply. An outcome is an object of:

- `name`: `case`, or the source's name;
- `parameters`: an object giving each parameter of the scope (§3), `runAt` included, its value, with
  the literal the case or the earlier source wrote; for a skipped source, those that have a value;
- `arguments`: the source's request (§4.1), for a source acquired, and absent otherwise;
- `claim`: the claim (§§6–7), and absent for a skipped source;
- `status`: the claim's `acquisitionStatus`, or `dependency-unavailable` for a skipped source;
- `reason`: the claim's `reason`, or `dependency-unavailable` for a skipped source.

(No vector holds a skipped source, so none decides the form of its outcome or its entries.)

#### 9.3 Lineage

There is one lineage entry for each target of the case and of each source, in the order of the
outcomes; within one outcome, its fact targets ordered by code point, then its evidence targets
ordered by code point. (No vector decides the order within one outcome.) An entry is an object of:

| Member | Value |
| --- | --- |
| `source` | the outcome's `name` |
| `kind` | `fact` or `evidence` |
| `target` | the fact target or the requirement |
| `class` | the target's class (§8.2) |
| `generatedInfluence` | its generated influence |
| `present` | `true` when the claim gives the target a value — a value at the pointer, or any availability for the requirement — and `false` otherwise |
| `status`, `reason` | the outcome's |
| `basis` | the claim's `basis`, or `[]` for a skipped source |
| `candidateFrom` | the pointers of the value read that the dialect could copy to the target, distinct, ordered by code point: a copy entry's `source`, or each `from` of a claim form that writes the target; absent when there is none, as for a rule's evidence target |
| `readDigest` | the read digest (§6) |
| `receipt` | the acquisition's citation; absent for the case, a local file and a skipped source |
| `calculation` | §7, for a calculated source that was acquired; absent otherwise |

`candidateFrom` lists what the dialect could read into a target, and not what was read; `basis`
lists what was read to decide.

#### 9.4 What derives a preparation

A preparation holds the instant, the dialect's digest, each scope's values, each request, each
claim and each acquisition's citation. It does not hold the case, the results or the receipts, which
a verifier is given (§11). What derives a preparation is the dialect, the case, the acquisitions,
the profiles and the instant, and nothing else.

#### 9.5 The canonical form of a preparation

A preparation's digest is taken of all of it in this form, the form the Runner digests a
preparation in (Runner, "The canonical form of a preparation"):

- **Members**: each object's members ordered by name, comparing the names' UTF-8 bytes, which orders
  them by code point; an array keeps its order.
- **Whitespace**: none between tokens.
- **Numbers**: the literal, its characters kept. Every number of a preparation is an integer (§1):
  `-0` stays `-0`, and `9007199254740991` and `-9007199254740991` are written whole, without an
  exponent.
- **Strings**: `"` and `\` are written `\"` and `\\`; U+0008, U+0009, U+000A, U+000C and U+000D are
  written `\b`, `\t`, `\n`, `\f` and `\r`; every other code point below U+0020 is written `\u00`
  and two hexadecimal digits; `&`, `<` and `>` are written `\u0026`, `\u003c` and `\u003e`, and
  U+2028 and U+2029 are written `\u2028` and `\u2029`; every other code point is written as its
  UTF-8 bytes, `/`, U+007F and every character outside ASCII included. `A&B <x> café ☃` is written
  `A\u0026B \u003cx\u003e café ☃`.
- **`true`, `false` and `null`** as they are.
- **`verifiedAt`** is 20 characters, and each outcome's `parameters` gives `runAt` the same string.
  A preparation recomputed at another instant is another preparation, with another digest.

This is not `canon`, which writes `&`, `<` and `>` as they are and `-0` as `0`. A dialect's, a
profile's, a read's and a result's digests, and the bytes a receipt's signature covers, are
`canon`'s.

The preparation's **digest** is the digest of those bytes, and its **binding** is these bytes
exactly, the digest in place of `D`:

```text
{"kind":"judgment-pack-runner/preparation/1","digest":"D"}
```

`kind` then `digest`, with no whitespace: the member a runtime's evaluation record carries as its
caller gave it (runtime ADR-0050). The scheme names the Runner because the Runner defined it; every
binding recorded names it, and this document keeps it unchanged.

### 10. The output side

A dialect's output side says how a disposition becomes the arguments of a write. An **output
dialect**, version 1, is a JSON object of exactly `outputVersion`, the string `"1"`; `platform`, a
non-empty string naming the catalog platform whose write tools it holds, as the gateway's engine
configuration names one; and `policies`, an object mapping each write tool's name to a **decision
policy** in the form the gateway's engine configuration gives an entry of a platform's
`decisionPolicy` (the gateway's `docs/design/engine-config.md` at `v0.15.0`, the release the Status
names, and gateway §1.2a, `policy`): `outcomes`, the outcome ids a record must have decided; optionally `packs`,
`reviewed` and `requireSignedRecord`; `bind`, pairs of a pointer into the write's arguments and a
pointer into the record's `inputs.facts`, whose values must be equal; `fix`, pairs of a pointer into
the arguments and the value the argument there must be; and `closed`, whether every argument must be
reached by `bind` or `fix`. This document restates none of it: the gateway's form is the output
side's.

A policy's digest is the digest of its `canon` bytes, which is the `policy` an action receipt
carries for a write held to it (gateway §1.2a); an output dialect is digested so too. The input
side and the output side are two documents, each with its own digest, so that a version-2 dialect
document stays the Runner's mapping v2 document byte for byte.

A policy holds a write to its decision record at the moment of the gateway's check: by `bind`, an
argument to a fact the record evaluated; by `fix`, an argument to a value the policy fixes; and, by
`closed`, the arguments to exactly those named. What that establishes is the gateway's (gateway
§1.2a, "What `decision` establishes"): not that the target read the arguments as intended, not that
the target was unchanged since the record, and not that a person approved the write.

No preparation reads the output side, and no conformance class of this document reads it. Its
vectors are deferred to a later RFC.

### 11. Verifying a preparation

A preparation verifier is given:

- the dialect document; the case document; the acquisitions (§5.2), `{}` when there are none; and
  the input profiles it trusts (§5.1);
- the **preparation** to verify;
- optionally, the **record**: the line of bytes, without its newline, of the runtime evaluation
  record whose binding it holds to the preparation; and
- whether it **requires a binding**.

**Refusals.** Before it recomputes anything, it refuses the reading, which then reports nothing but
the refusal, at the first of these phases that fails, in this order:

1. the bounds of §12 that are measured on bytes — a document's size, its nesting (the case
   document's at 32 levels), and each number literal's characters and exponent — taken on every
   document before any is read: `input-over-bound`;
2. every document read as §1 reads one, and the record as one line: `input-malformed`;
3. the bounds of §12 that are counts — the sources, the parameters in a scope, the clauses of a
   rule, the conditions one `all` or `any` lists, the `unwrap` pointers, the fact and evidence
   targets — and the nesting of each acquisition's result, taken on the documents read wherever the
   count can be taken, before any form is checked: `input-over-bound`;
4. every document's form — the dialect against §§2–8, every rule they give it included, and each of
   its sources against §4's members and its kind's, whichever its kind; a profile against §5.1 and
   the key rule; the acquisitions against the form of §5.2; the preparation's `verifiedAt` against
   the timestamp form with an instant; the record against its reading below: `input-malformed`;
5. a dialect that names a kind the verifier does not read: `kind-unread`.

One bound is measured later, because it cannot be measured sooner: an unwrapped string's bytes, and
the nesting and the number literals of the value it holds, are measured when it is unwrapped (§6.1),
during the recomputation, and over them the reading is refused there, `input-over-bound`, with
nothing reported but the refusal.

**Findings.** Otherwise it recomputes the preparation at the given preparation's `verifiedAt`, by
§§3–9, and ends the reading at the first of these findings, in this order, reporting that one:

1. `profile-mismatch` (§5.1), the sources taken in their order;
2. for the case: `parameter-invalid` (§3), its parameters in their order, then `read-failed` for its
   read (§6.2);
3. for each source in its order: `parameter-invalid` for a source parameter it declares, in their
   order (§3); then, for its acquisition and its read, `acquisition-missing`,
   `acquisition-unexpected`, `acquisition-invalid`, `acquisition-stale`, `acquisition-sessions`
   (§5.2), `calculation-invalid` (§7) and `read-failed` (§6), in that order; and, after the last
   source, `acquisition-unexpected` for a member of the acquisitions that names no source;
4. `admission-refused` (§8.2);
5. **`preparation-differs`**: the recomputed preparation's canonical bytes (§9.5) are not the given
   preparation's, written in that form; a given preparation that cannot be written in that form
   differs;
6. with a record, **`record-inputs-differ`**: the record's `inputs.facts` is not the facts document
   (§8.1), its `inputs.evidence` is not the evidence-availability document, or its `cites`, absent
   being the empty array, is not the preparation's `cites` as a set, each compared as JSON values.
   The citations are compared as sets: a citation either side gives twice is one member of its set,
   and how many times one is given is not compared;
7. with a record that carries a `binding`, **`binding-foreign-kind`**: the record's `binding` is not
   an object whose `kind` is the string `judgment-pack-runner/preparation/1`; no digest is compared;
8. with a record that carries a `binding`, **`binding-mismatch`**: the bytes of the record's
   `binding` are not the preparation's binding (§9.5), byte for byte: another digest, or the same
   members written otherwise, in another order or with whitespace;
9. **`unbound`**: a binding is required, and no record is given or the record carries no
   `binding`.

**Reading the record.** The record is one line, holding neither a line feed nor a carriage return,
that is one JSON object read as §1 reads a document, with an object `inputs`. Its member `binding`
is read by that exact name: a record that names a member `binding` but for case is refused, not read
as one with no binding. A record **carries** a binding when it has a member of that name, whatever
its value: a `binding` that is `null` is carried, and is not of the binding's form (finding 7); a
record with no member of that name carries none, which is no finding unless a binding is required
(finding 9). The member's bytes are those of its value as the line writes them, from its
first character to its last; nothing is canonicalised again. This document reads nothing else of the
record. It does not check the record's signature, its chain or its witness, which the runtime's
reader and the checkpoint witness statement's reader check; a binding commits a preparation only
under a record signature that verifies (§13).

**The reading.** A reading with no finding reports:

- the preparation's **digest**;
- the **binding**: `matches` with a record whose binding matches, `absent` with a record that
  carries none, and `not-checked` with no record;
- the **facts document** and the **evidence-availability document** (§8.1);
- **`targetsByClass`**, an object giving `asserted`, `record` and `generated` each the number of
  lineage entries of that class: every target counted, with a value or without;
- **`unsignedParameters`**, when it is not empty; and
- **`unsignedFreshness`**, when it is not empty.

**`unsignedParameters`** names the parameters a derivation read that no receipt commits. It has an
entry for each source that was acquired, whose read is a rule that was applied (not a skipped
source, not a calculator that did not compute), that has a target, and whose rule's conditions name
a parameter that its own acquisition does not commit. The parameters a rule's conditions name are,
at any depth, `equalsParam`'s `param` and `freshWithin`'s `asOf` and `maxAge`, and not those it only
declares. A source's own acquisition commits a parameter its request commits (§4.1), and an input
its calculator echoed that is bound to the parameter (§7); another source's receipt commits nothing
for it. An entry is `{"source", "parameters", "targets"}`: the source's name; each such parameter as
`{"name", "kind"}`, ordered by name; and the number of the source's targets. The kinds:

- `runAt`: the parameter `runAt`;
- `ambiguous-text`: a parameter that would be of kind `case`, `local-file` or `upstream`, which the
  source's request carries only in a `$text` that names another parameter too;
- `case`: a case parameter;
- `local-file`: a source parameter from a local-file source;
- `upstream`: a source parameter from an earlier source that has an entry here with a parameter of
  kind `case`, `local-file`, `upstream` or `ambiguous-text`;
- `upstream-runAt`: a source parameter from an earlier source that has an entry here whose
  parameters are all of kinds `runAt` and `upstream-runAt`.

A source parameter from an earlier acquired source that has no entry — whose value its rule derived
from signed values alone, or which it copied from its result — is not named. The entries are in the
order of `sources`.

**`unsignedFreshness`** is `{"against": "preparation.verifiedAt", "verifiedAt": V, "sources": L}`,
`V` the instant and `L` an entry, in the order of `sources`, for each source acquired:
`{"source", "checks", "targets"}`, `checks` being `["acquisition"]`, or
`["acquisition", "calculation"]` for a calculator that computed, and `targets` the number of the
source's targets. Each such freshness was judged against `verifiedAt`, which no receipt covers: a
matching binding in a record whose signature verifies is what commits it (§13).

### 12. Bounds

A verifier holds its inputs to the Runner's bounds (Runner, "Numeric and resource profile"):

- the dialect at most 131072 bytes; the dialect, the case and the acquisitions together at most
  2097152 bytes; the profiles at most 65536 bytes; and the preparation and the record each at most
  8388608 bytes;
- at most 16 sources; 64 parameters in one scope; 64 clauses in one rule; 64 conditions listed by
  one `all` or `any`; four `unwrap` pointers; 200000 bytes in one unwrapped string; and 256 fact
  targets and 128 evidence targets;
- at most 32 levels of nesting in a value a read applies to — the case document, a result, an
  unwrapped value — and at most 64 in any document; and
- number literals of at most 128 characters, whose exponent, when they have one, has a magnitude of
  at most 308.

Over any bound it refuses the reading, `input-over-bound`, and MUST NOT read part of it. The bytes are
bounded first, by the documents' sizes, before any is read; §11 gives the order of the rest. A
preparer refuses the same inputs before it writes a preparation.

### 13. What a preparation establishes, and what it does not

A preparation has parts of three natures, and what it establishes differs by part. A **derivation**
— a copy, a rule, a calculated value's lineage, the facts and evidence-availability documents, the
preparation's form and its digest — is recomputable: a verifier that recomputes it establishes it
itself, from the inputs, trusting no one for it. An **acquisition**'s bytes are not recomputable:
they are held by their digest, under a receipt, and what they establish is the receipt's business,
which is byte lineage and not truth, the stance Core §6.3 takes of a source. An **asserted** input
is the operator's say, and recomputation shows only that it was carried faithfully.

| Part | Establishes, to a verifier that recomputed the preparation | Does not establish |
| --- | --- | --- |
| The facts and the evidence availability a copy or a rule derived | that these facts and this evidence availability were derived from those bytes by these rules, at that instant | that the rule is right for the pack, or reads what its author meant; that a target with no value has none in the system |
| A calculated value's lineage | that the calculator's answer, in the bytes acquired, echoed the inputs bound to this case, and reported its tables as of instants within the dialect's limits before `verifiedAt` | that the calculator is deterministic or calls no model; that its arithmetic or its tables are right; that it used only what it echoes; that an `asOf` is true |
| An acquisition of class `record`, verified under a trusted profile | byte lineage: the holder of the gateway key the profile pins signed a receipt that names these bytes by their digest, this request by its commitment, this adapter, shape and endpoint, at these times; what more the receipt says is the gateway's (gateway §1.2a, §5) | that the system's record is true, current or complete; that the adapter reported its acquisition truly; that the session is sealed or complete, or that the caller did not choose among answers; anything once the gateway's key is copied |
| An acquisition of class `generated`, a research record above all | the least: that this request — a recipe, its question and the model as named — was asked of the gateway source the profile names, and that these bytes came back under that receipt | that the answer is right, complete or current, or the model's own; that a candidate it names exists; that a page it cites says what it quotes, beyond a receipt for that page |
| An asserted input: the case, a local file, a parameter no receipt commits | that the preparation carried what the operator supplied, faithfully | anything about it: an asserted input rewritten with its preparation recomputed verifies as the original did; `unsignedParameters` names the parameters a rule read on the operator's say |
| `verifiedAt` | that every freshness check holds against it | that it was the instant of admission: without a binding no signature covers it, and a preparation recomputed at another instant verifies as the original does |
| A binding that matches, in a record whose signature verifies (a check this document does not make) | that the preparation, its instant included, is the one committed in the record when its key's holder signed it | anything against the operator, who holds the key and the clock and can recompute, write and sign again, which only a checkpoint held independently from before the change shows; when anything was prepared: a binding carries no time |
| A binding that matches, with no signature checked | nothing, by itself | — |

Nothing establishes an operator's intent, a source's truth, a model's correctness, or anything the
dialect does not name: a target the dialect does not map is unknown to the evaluation, which its
omission does not guarantee (Runner, "Release checks, runtime and offline verification"). A reading,
and a report built on one, MUST NOT be described as establishing anything the right-hand column
names.

### 14. The preparation verifier

An implementation is a *conforming preparation verifier* when, for every reading it admits, it gives
the refusal, the finding or the reading §11 defines, and when it gives every vector's expected answer
in the dialect vectors published with the specification version it names. Its claim takes the form
"a preparation verifier conforming to `spec/dialect.md` of specVersion *X*, reading dialect version
2 and the kinds *K*", and names only kinds that the vectors published with that version exercise
(§4). The class is independent of Core's four classes and of the witness-statement reader: none
implies it, and it implies none. It says nothing about a preparer, which this document does not
define as a class: a verifier's agreement with a preparer shows that the two read the format alike,
and no more. A claim of this class MUST NOT be described as establishing anything §13 says a
preparation does not establish.

Until a specification version publishes the dialect vectors, no claim of this class is available.

## Alternatives

- **Leave it the Runner's.** The status quo. Every verifier is built against `MAPPING-V2.md`, which is
  normative for one implementation, moves with its releases, and describes the Runner's service, its
  exports and its journal beside the format, so that a reader must separate the two itself. Coherent
  while the Runner is the only reader; not once a counterparty checks a binding, or the Exchange
  publishes an entry.
- **Cite, without restating.** The specification would name `MAPPING-V2.md` at a commit and bind the
  vectors by their digests. Cheaper, and the bytes would be as fixed. It leaves the text under one
  implementation's governance, so that a correction there silently is, or is not, a correction here;
  and the text would stay the Runner's words for the Runner, which this RFC finds in places describe
  the Runner rather than the format. The maintainer's decision is otherwise.
- **A section of Core §8.2.** Core takes one facts document and "defines no fact namespace, merging,
  or acquisition"; a dialect is acquisition and merging. Every Core version would carry a format no
  Core class reads, and an evaluator would answer to it. A companion document, with its own class,
  keeps the two apart.
- **An extension (Core §9).** An extension is a member of a pack, and an optional one must not change
  Core semantics. A dialect is not part of a pack: one pack is read through many systems, each with
  its dialect, and a pack that carried its dialects would name its systems. Rejected.
- **A profile.** A profile constrains packs, and a dialect constrains nothing in one. The nearest
  draft is [RFC 0003](0003-evidence-reference.md), a candidate profile that keeps an evidence
  reference a bare identifier and leaves the derivation to "the resolving layer". This RFC specifies
  that layer's derivation and its record; RFC 0003 stays the place for a reference convention.
- **The specification's own names.** Renaming `operation`, the binding's scheme or the preparation's
  members would make every recorded binding stop matching, and the vectors would no longer be the
  Runner's bytes. Rejected. The issue calls one kind "a connection's record" and another "an MCP
  query"; both are `operation` here, the name the Runner's documents and vectors write — an operation
  is a tool of a gateway source of shape `mcp`, a SQL tool among them — and `record` is already a
  class.
- **The output side in the same document.** A member of the dialect document would make it no longer
  the Runner's mapping v2 document. Two documents, each with its digest, keep version 2 byte for
  byte.

## Compatibility

- **Packs, documents and evaluators.** Unchanged: no member of any pack, schema or disposition
  changes, and no Core class gains or loses a requirement.
- **The Runner.** Keeps its service, its exports and `verify-run`. Every mapping v2 document it
  accepts is a version-2 dialect document, and its preparation is the format's. No rule the text
  gives a verifier differs from what `verify-run` applies to a preparation, as far as the vectors and
  the Runner's documentation show; where the text takes a position no vector decides, the Runner's
  behaviour is the evidence, and a difference found is a defect in the text (Unresolved question 1).
  On acceptance, the Runner may point `MAPPING-V2.md`'s canonical-form subsection here; that is its
  decision.
- **The runtime.** Unchanged. It records the binding as given and interprets nothing (ADR-0050), and
  the binding's bytes and its digest are unchanged.
- **The gateway.** Unchanged. Its canonical form, its receipt and its decision policy are referenced,
  not restated.
- **The Desk.** Writes this format through the Runner today. A version-3 kind needs a preparer before
  the Desk can write one.
- **Versioning.** The dialect document's version is its `version` member: 2 is the Runner's mapping
  v2; 3 is proposed. A preparation's version is its dialect's. The output side has its own
  `outputVersion`, `"1"`. Every object is closed at every level, so a reader that knows a version
  refuses a member of a later one rather than skipping it.
- **On acceptance**, with the landing pull request and not before: Core §1.1's list of normative
  artifacts gains the companion document, normative for the class only; its `export-ignore` is
  removed and the site publishes it as a page of its own; and the vectors wait for the next
  `specVersion`, as the checkpoint witness vectors do.

## Security and privacy

- **Credentials are never in a dialect.** A dialect names an input profile by its id and its digest,
  a connection by its name and a header by its name; a credential, a header's value and a key's
  secret are the gateway's custody. A verifier takes no key and no profile from what it verifies:
  it is given the profiles it trusts, out of band, and holds each key to the key rule before it reads
  anything signed.
- **What a preparation and its acquisitions disclose.** A preparation holds every scope's parameter
  values, every request and every claim: case values, identifiers, the records read. The
  acquisitions hold the results and the salts, and a salt opens its commitment to whoever holds both.
  A verifier given them learns all of it; the Runner's own guidance stands: "distribute it only to
  intended reviewers".
- **A research recipe can carry personal data**, in its question, its constraints and the people,
  roles and contact details its answers name. A dialect published to the Exchange, or to anyone, MUST
  carry no case, no acquisition and no research record; its recipe's `question` and `constraints`
  carry the criteria and leave every literal that names a person, a customer or an account — a name,
  an email address, a profile URL, an internal identifier — to a case parameter; and the fixtures
  published with it are synthetic. A publisher strips those before publishing, and a reviewer of an
  entry checks that it did.
- **Resource use.** A verifier reads documents it did not author. §12 bounds the bytes, the sources,
  the scopes, the clauses, the conditions listed, the unwraps, the targets, the nesting and the
  number literals, and a reading over a bound is refused, never truncated. A rule's evaluation is
  bounded by its clauses and the conditions they list; a verification costs at most one Ed25519
  check per acquisition, and at most 16 acquisitions. The second reader measures nesting before it
  parses a document.
- **Confusion.** The two canonical forms differ in three characters and in `-0`, and a verifier that
  mixes them gets another digest: two vectors are there for it. A binding that matches, with no
  record signature checked, establishes nothing, and a verifier's report must not say otherwise.
- **No hidden execution.** Templates substitute values and render integers, and nothing in a dialect
  is evaluated as code; a `sql` source's statement is fixed text, its values bound as the provider's
  parameters.

## Conformance

The vectors are the Runner's nine, staged in
[`conformance/dialect/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/dialect)
byte for byte, copied from the Runner's commit `05636ed` and the same files as at its `main` commit
`82116bf`, each run as its README says: the dialect, the case, the acquisitions and the
profiles; the preparation to verify and the record, from the Runner's export; and whether a binding
is required. The answer expected of the class is in this repository's manifest of them.

| Vector | What it holds | The class's answer |
| --- | --- | --- |
| `valid` | a calculated run, signed, witnessed and bound | a reading, binding `matches` |
| `recomputed-one-second-later` | the export's preparation recomputed a second later, the record as it was | `binding-mismatch` |
| `unbound-record` | a record from before the binding, a binding required | `unbound` |
| `foreign-binding-kind` | the record's binding of another scheme, signed again | `binding-foreign-kind` |
| `changed-table-lineage` | the retained lineage names another instant for a table | `preparation-differs` |
| `disposition-differs-from-audit` | the export's retained result differs from its record | a reading, binding `matches` |
| `unsigned-parameters` | rules that read `runAt`, a case parameter and one in ambiguous text | a reading, binding `absent`, the parameters named |
| `escaped-strings` | a case value holding `&`, `<`, `>` and characters outside ASCII | a reading, binding `absent` |
| `numeric-spellings` | the case parameters `-0`, 2⁵³−1 and −(2⁵³−1) | a reading, binding `matches` |

They are positive (`valid`, `escaped-strings`, `numeric-spellings`, `unsigned-parameters`), negative
(`unbound-record`, `changed-table-lineage`) and adversarial (`recomputed-one-second-later`,
`foreign-binding-kind`, the one second and the re-signed record being what an operator who rewrote a
record would do). `disposition-differs-from-audit` is answered otherwise than `verify-run` answers it:
it alters the Runner's export, whose retained result is no part of a preparation or a record, and the
class reads its preparation and its record as the valid case's.

**Kinds.** The vectors exercise the case and `operation`, and no other kind: `selected-file`, the four
kinds of version 3 and the output side have none, and are not claimable.

**What no vector holds.** `unwrap`; source parameters and skipped sources; a calculator that did not
compute; a `generated` class, generated influence and `admits`; timestamp parameters; a receipt that
fails; a stale acquisition or table; a broken session form; a refusal at a bound; and the eight
positions of Unresolved question 1. The repository's tests hold the second reader to some of these
with altered copies of a vector — a result changed by a byte, an instant past `maxAge`, a profile's
digest, a reader that writes `-0` as `0` or `&` as it is — but those are this repository's checks of
one reader, not vectors: they are not the Runner's bytes, and no claim could cite them.

**What this repository checks.** Every vector file to the SHA-256 the Runner's manifest gives it, and
the Runner's manifest and README to the SHA-256 this repository records; the second reader over every
vector; the counts; and this section's equality with the companion document's §§1–14.

## Implementation

1. **The Runner**, the reference preparer, with `verify-run`, the first reader, which reads every
   vector through the Runner's own code.
2. **`tools/dialect_verify.py`**, the second reader, written from the text by the text's author
   (Evidence), which reads dialect version 2 and the kind `operation`, and refuses every other kind as
   `kind-unread`.
3. **The Desk's inputs**, a writer: its mapping editor and import recipes write version-2 documents
   for the Runner today, and the research line (Desk #369, #371) would write the `research` kind.

All three are this project's. An independent verifier — by an auditor or a counterparty, written from
this text and the vectors — is the evidence a stable class needs, and none exists.

## Unresolved questions

1. **The rules no vector decides.** The text takes a position, and marks it, on eight rules that
   neither the Runner's documentation nor its vectors decide: a `{{` with no `}}` and a stray `}}` in a
   `$text`; a copy entry whose source does not resolve, for a fact and for an availability; a copy
   that names a requirement twice; `unknown` written in the evidence-availability document rather than
   left out; generated influence; a skipped source's outcome and entries; and the order of the entries
   within one outcome. Each was taken without the Runner's code. The Runner's behaviour may differ, and
   a vector from the Runner for each is what settles it; until then a difference found is a defect in
   the text.
2. **The kinds without vectors.** `selected-file`'s snapshot form is not stated here, and the four
   version-3 kinds are proposed with no preparer. When a kind gets a preparer and vectors, and whether
   its request forms here survive the first implementation, is open.
3. **Whether `research` belongs in the first version that adds kinds.** It establishes the least, its
   record's form is the Desk's to settle (#369), and the Runner defers model calls over HTTP; it could
   wait for both rather than enter version 3.
4. **The output side's vectors**, deferred to a later RFC, and whether a reader class should hold an
   output dialect at all, when the gateway holds every write to its policy at the moment of the write.
   And a **release selector**: an output dialect is read in the decision-policy form of the gateway
   release the Status names, `v0.15.0`, and names none itself. Whether it should name the release
   whose form it uses, and what a reader does when a later release changes that form, is open.
5. **The Exchange's entry format** (#142). This document gives an entry's parts — an input dialect,
   an output dialect, profiles by digest, fixtures and the preparation they must produce — and not the
   entry itself, its licence or its governance, which are #142's record to propose.
6. **When it lands, and its versions.** As RFC 0017's first question: whether the companion document
   and its vectors land with the next `specVersion`, and whether the vectors take a `suiteVersion` of
   their own. And whether the dialect keeps the Runner's numbering, which begins at 2.
7. **The binding's scheme** names the Runner, `judgment-pack-runner/preparation/1`, because the Runner
   defined it. A second preparer would write that name too; a scheme named by the specification would
   be a new scheme, not a rename, and whether one is wanted is open.
8. **A preparer class.** This document defines a verifier and no preparer, as the checkpoint witness
   statement defines a reader and no witness. Whether a preparer class is wanted, and what it would be
   held to beyond the vectors, is open.

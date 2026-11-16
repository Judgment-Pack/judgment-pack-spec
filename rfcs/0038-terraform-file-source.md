# RFC 0038: A file-sourced dialect source — Terraform plan and state JSON

- Status: Accepted
- Type: Standards track, the dialect companion (`spec/dialect.md`), one new source kind. Core is
  unchanged.
- Created: 2026-11-16
- Accepted: 2026-11-16, by the maintainer, on the same-vendor review recorded on pull request 340,
  with the different-vendor review waived; see [Acceptance](#acceptance).
- Issue: [#339](https://github.com/Judgment-Pack/judgment-pack-spec/issues/339) (the registry line)
- Related: RFC 0018 (the dialect); RFC 0034 (the registry profile), RFC 0037 (generated facts
  contracts); the dialect's `selected-file` kind (§4.2)

> **Accepted** on 2026-11-16 ([Acceptance](#acceptance)). The text below is proposed for the dialect companion,
> [`spec/dialect.md`](../spec/dialect.md), as a new source kind. Until that text is released,
> this record is normative for nothing. Core is untouched.
>
> **Review standing.** [RFC 0009](0009-interim-review-regime.md) asks for a recorded adversarial
> review by a model from a different vendor. That review has not happened, and this record does not
> claim it. One review round by a model from the drafting vendor covered RFCs 0034 to 0038 together;
> it is copied verbatim to [`rfcs/reviews/0034-round-1.md`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/rfcs/reviews/0034-round-1.md). That is a
> same-vendor review, not a cross-vendor claim.

## Summary

A registry (RFC 0034) says what a platform should be. A Terraform plan says what a change is about
to make it, and a Terraform state says what Terraform last recorded. Packs can judge both, for
example "no plan may grant a role outside the registry's grants", "a plan that destroys a database
needs approval", or "every Cloud Run service in state reads its secrets from a pinned version".
Before they can, the plan or state has to become facts without carrying a secret into a decision
record.

This RFC adds one dialect source kind, **`terraform-file`**. It reads the JSON that
`terraform show -json` writes for a saved plan or for state, and only that:

- **Files only.** The source reads a file the caller supplies. It never runs Terraform, never reads
  a state backend, never reads a binary plan and never contacts a network.
- **Bound to the bytes.** The acquisition records the file's sha256, so the decision record names
  the exact plan or state it judged.
- **Sensitive values dropped.** Every value Terraform marks sensitive is removed before any read.
  It never reaches facts, lineage, records or diagnostics. A file that carries no sensitivity
  markers at all is refused, because nothing could tell which of its values are secret.
- **Pinned formats.** The source accepts a closed list of Terraform JSON `format_version` values,
  and refuses newer ones until the list grows.

## Problem

1. **Plans and state are the evidence of infrastructure change**, and teams already gate them in CI
   with policy tools. A Judgment Pack evaluation gives that gate a decision record, but there is no
   defined, safe way to turn a plan into facts.
2. **Plan and state JSON hold secrets.** Database passwords, private keys and tokens that a
   configuration passes to a resource are in the JSON, marked only by a parallel sensitivity
   structure. A reader that ignores that structure copies secrets into facts, and from there into
   records and logs.
3. **A file is not a gateway acquisition.** The dialect's acquisitions are signed reads through the
   gateway (§5.2), or an operator's selected file (§4.2). A plan produced by a CI step is a file
   with a known format, and needs a kind that names that format, checks it and records its digest.
4. **The format moves.** Terraform versions its JSON output. A reader that takes any version can
   misread a new structure silently, including the sensitivity structure.

## Evidence

- The adopting organization behind RFC 0034 deploys with Terraform. It wants plans judged in CI
  against its registry, and state judged for drift between deployments, with records that name the
  plan.
- `terraform show -json <planfile>` and `terraform show -json` (state) are Terraform's documented
  machine-readable outputs. Their resource values come with `sensitive_values`,
  `before_sensitive` and `after_sensitive` mirrors, and outputs with a `sensitive` flag.

## Specification

### 1. The kind

A `terraform-file` source has, besides the members of dialect §4, exactly:

| Member | Form | Meaning |
|---|---|---|
| `document` | `plan` or `state` | which output of `terraform show -json` the file is |
| `select` | an object, below | which resources the acquired value holds |
| `maxBytes` | an integer from 1 to 268435456, optional (default 67108864) | the largest file read |

Its class is `asserted`, as for a local file (dialect §8.2). The caller supplies the file, and
nothing attests that it is the plan that was applied. A pack that must not decide on asserted
inputs says so through admission (`admits`), as it does today.

The file is named at evaluation time, not in the dialect: the dialect declares the source, and the
caller binds a path (the reference Runner's input binding, the reference runtime's command line).

### 2. Reading the file

The reader does these steps in order. The first failure refuses the acquisition with the code
shown, and later steps do not run. **A diagnostic carries its code, the file's sha256 and its
size, and nothing else**: no value, member name, pointer or position, because before step 6 any of
those could be part of a sensitive value (a map key is data). Each rule below is decided by the
file's bytes alone, so a vector states one expected code.

1. **Size.** The reader computes the sha256 of the **whole** file as supplied, and its length in
   bytes. A file longer than `maxBytes` is refused (`TF-SIZE`) without being parsed. The hash and
   size are recorded whatever happens next.
2. **Strict JSON** (`TF-JSON`). The bytes MUST be:
   - UTF-8 with no byte-order mark, and no lone surrogate escape;
   - one JSON value, with nothing after it but whitespace;
   - nested at most 128 deep, where the top-level value is depth 1 and each value inside an object
     or array is one deeper than its container;
   - free of duplicate member names in any object.

   Numbers are kept as their decimal text, never as binary floating point. A binary plan file
   fails here, and the message says to pass the output of `terraform show -json` instead.
3. **Format** (`TF-FORMAT`). The top-level value MUST be an object with `format_version`, a string
   in the accepted table for the source's `document` (§3). A raw state file, which has no
   `format_version`, is refused here.
4. **Document** (`TF-DOCUMENT`).
   - A `plan` MUST have `planned_values`, an object. Its `resource_changes`, when present, MUST be
     an array, and when absent reads as an empty one.
   - A `state` MUST NOT have `planned_values` or `resource_changes`. Its `values`, when present,
     MUST be an object, and when absent reads as a state with no resources.
5. **Sensitivity markers** (`TF-SENSITIVITY`). The **read section** is `resource_changes` for a
   `plan`, and every resource under `values.root_module` and its `child_modules`, recursively, for
   a `state`. **Every** resource in the read section, selected or not, MUST carry its mirror:
   - for a `plan`, each item of `resource_changes` has `change.before_sensitive` and
     `change.after_sensitive`;
   - for a `state`, each resource has `sensitive_values`.

   A mirror is `true`, `false`, or an object or array that mirrors the value's shape. An empty
   mirror (`{}`, `[]` or `false`) is a marker that nothing there is sensitive. A missing mirror, or
   one of another JSON type, refuses the file. The check runs before selection, so its outcome does
   not depend on `select`.
6. **Removal of sensitive values.** In each value of the read section (a change's `before` and
   `after`, a state resource's `values`), every position whose mirror is `true` is removed, with all
   it contains, by these rules:
   - **An object member** is removed, and the member is then absent.
   - **An array element** is never removed alone, because the elements after it would shift and a
     pack would read the wrong one. The whole array that holds it is removed instead. If that array
     is itself an array element, the rule applies again, up to the nearest object member, which is
     removed.
   - A mirror position that does not exist in the value is ignored.

   A removed value is never replaced by a placeholder, so nothing can compare equal to it and a
   pack reading it sees `unknown`. **`removedSensitive`** counts the object members removed. Each
   removal counts once, however much it contained. Pointers in `after_unknown` (§5) that fall at or
   below a removed position are dropped as well.
7. **Selection** (§4), then the acquired value (§5). Only the selected resources' values continue,
   and only these sanitized values can ever reach facts, lineage, a record or a message.

The reader never reads `configuration`, `variables`, `relevant_attributes`, `checks`,
`prior_state`, `planned_values` (beyond step 4's check), `output_changes` or `outputs`. Variable
values carry no sensitivity mirror in these formats, a configuration can embed literals, and
outputs are not resources. A pack that needs an output's value is out of scope for the first
version (Unresolved question 4).

### 3. Accepted formats

The companion keeps a table of accepted `format_version` values per `document`. Each row is
backed by vectors made with the Terraform release that writes it. The first table holds the
versions the reference vectors are recorded with. A version not in the table, including a newer
minor of a listed major, is refused (`TF-FORMAT`).

The table grows by a patch release of the companion, with vectors, and never shrinks within a
dialect version. Because two readers of one dialect version can then hold tables of different
releases, **the table has its own release number**. A reader's claim names the table release it
implements, each vector names the release that added its row, and a reader is held only to the
vectors of the releases it claims. A file whose `format_version` is in a later table than the
reader's is `TF-FORMAT` for that reader, and that is the expected result for its claim.

This is deliberately stricter than Terraform's own compatibility promise for the JSON output. A
new minor may add members, and the sensitivity mirror of a new member is exactly what a reader must
not guess.

### 4. Selecting resources

`select` is an object of:

| Member | Form | Meaning |
|---|---|---|
| `types` | a non-empty array of at most 64 distinct resource type names, such as `google_cloud_run_v2_service` | only resources of these types |
| `mode` | `managed` or `data`, optional (default `managed`) | |
| `address` | a pattern of at most 512 characters, optional | only resources whose **whole** address matches. `*` matches any run, possibly empty, of characters other than `.`, `[` and `]`, and every other character matches itself |
| `actions` | an array of plan actions, optional, `plan` only | only changes whose `change.actions` include one of these: `create`, `update`, `delete`, `read` or `no-op` |
| `max` | an integer from 1 to 10000, optional (default 1000) | more selected resources than this refuse the acquisition (`TF-SELECT-BOUND`) |

`actions` on a `state` source, or a malformed `select`, makes the dialect invalid (dialect §11),
not the file. Resources in child modules are included, with their full address. Selection that
matches nothing yields an empty array, which is not an error: "no database is destroyed" is a
valid fact.

### 5. The acquired value

The acquired value is an array, sorted by `address` in code-point order, of one object per
selected resource:

- **For `state`**: `{"address", "type", "name", "mode", "providerName", "index"?, "values"}`, with
  `values` the resource's values after §2.
- **For `plan`**: the same members, with `actions` (the change's `actions`, as written), `before`
  and `after` (the change's values after §2) in place of `values`, and `afterUnknown`. The last is
  the list of JSON Pointers, in `after`, of values known only after apply, taken from
  `after_unknown`, with those under a removed position dropped, and sorted. A value that is unknown
  at plan time is absent from `after`, so a pack reading it sees `unknown`.

**Numbers** become decimal strings in RFC 0037's normal form (§2 rule 1 there): no exponent, no
leading `+`, no trailing zero after the point, and `0` for every zero, including `-0`. A number
whose normal form would be longer than 64 characters refuses the file (`TF-NUMBER`), because no
fact comparison needs it and its expansion would be unbounded (`1e1000000`).

The dialect's reads (copy and rule, §6) then turn the acquired value into facts, as for any other
source.

The acquisition record carries `{"kind": "terraform-file", "document", "formatVersion",
"formatTable", "sha256", "bytes", "removedSensitive", "selected"}`, with `formatTable` the table
release (§3). It carries no path: a path names a machine, not the evidence.

### 6. One decision per resource

A gate over a plan usually wants one decision per resource, not one over the whole plan. A tool may
write the same acquired value as an evaluation batch, one line per selected resource, with id
`<address>` and facts `{"terraform": {document, formatVersion, sha256}, "resource": <the object of
§5>}`, as RFC 0037 does for registry entries:

```
jpack terraform facts --plan plan.json --type google_sql_user --actions delete,update > changes.jsonl
jpack experimental evaluate --pack-id sql-user-change --batch changes.jsonl --require-outcome allowed
```

The batch is a product format of the reference runtime, not a dialect member. It follows §2 to §5
exactly, so the same file gives the same facts either way.

## Alternatives

- **Run Terraform inside the source.** That needs a binary, provider plugins, credentials and
  network: everything a judgment step should not hold. The CI step that made the plan already has
  them.
- **Read the binary plan file.** Its format is internal and unversioned.
- **Read raw state (`terraform.tfstate`).** It has a different structure, carries every attribute
  including secrets, and marks sensitivity differently by version. `terraform show -json` of state
  is the documented form.
- **Mask sensitive values with a placeholder.** A placeholder is a value, and it compares. Absence
  gives `unknown`, which a pack handles deliberately.
- **Accept any `format_version` 1.x.** That trusts additive change to keep sensitivity mirrors
  complete, which is the one thing that must not be trusted.
- **A gateway acquisition instead of a file.** The gateway reads live systems under signed
  receipts. The drift adapter (a separate gateway proposal) does that for live cloud state. A plan
  is a CI artifact and belongs to the CI step that made it.

## Compatibility

- One new kind. A reader that predates it refuses a dialect that names it, as for any unknown kind
  (dialect §4).
- Whether the kind joins the proposed version 3 or opens the next version is Unresolved question 1.
- Core, the record format and the gateway are unchanged.

## Security and privacy

- **Secrets.** Sensitive values are removed before selection, and before anything else sees them,
  in §2 step 6. A file without mirrors, on any resource, is refused, not read optimistically. A
  sensitive array element takes its whole array with it, so no index shifts. `variables`,
  `configuration`, `prior_state` and outputs are never read.
- **Diagnostics** carry the code, the file's sha256 and its size only. They never carry a value, a
  member name or a pointer, since before removal a member name can itself be sensitive data.
- **No execution and no network.** The source reads bytes, nothing else.
- **Bounded.** The file size, nesting depth, selection size and pattern form are all bounded. The
  pattern has no backtracking.
- **Residual risk.** A provider that fails to mark a secret attribute sensitive leaks it into the
  JSON, and Terraform's own marker is the only signal this source has. Packs that read attributes
  known to hold credentials should not, and the vectors include such a provider-unmarked case to
  show the limit plainly.
- **Asserted class.** The record proves which bytes were judged, not that they were the plan
  applied. Binding the plan's sha256 to the apply step is the pipeline's job.

## Conformance

**Vectors**, each a `terraform show -json` output recorded from a synthetic configuration, with no
real project or credential:
- **Plans:** create, update, delete and replace, and a plan with values unknown until apply.
- **State.**
- **Sensitivity:**
  - a sensitive attribute, and a sensitive nested block;
  - a sensitive element of a list, which removes the list;
  - a sensitive element of a list nested in a list;
  - an `after_unknown` pointer under a removed position;
  - a sensitive output, which is never read either way.
- **Refusals**, each with one expected code:
  - a missing mirror on a selected resource, and on an unselected one (both `TF-SENSITIVITY`);
  - a raw state file (`TF-FORMAT`), and a binary plan (`TF-JSON`);
  - an unaccepted `format_version`, and one from a later table release than the claim;
  - a duplicate member name, depth 128 and 129, and trailing data (`TF-JSON`);
  - `maxBytes` and one byte more (`TF-SIZE`), with the sha256 of the whole file in both;
  - a number with an exponent that expands past 64 characters (`TF-NUMBER`);
  - a selection of `max` and of one more (`TF-SELECT-BOUND`);
  - a state with no `values` (accepted, empty) and a state with `resource_changes`
    (`TF-DOCUMENT`).
- **Diagnostics:** a vector whose refused file has a sensitive member name, asserting that the
  name does not appear in the diagnostic.
- **Selection:** child-module addresses, `count` and `for_each` indexes, and data sources.

Every vector asserts that no value marked sensitive appears in the acquired value, the facts, the
lineage or any diagnostic.

## Implementation

1. **The reference runtime:** the reader of §2 to §5, fuzzed on the JSON reader and the pattern
   matcher, and the batch tool of §6.
2. **The reference Runner:** the kind, when the dialect version that holds it is in force.
3. **A second reader in Python** for the vectors, beside the dialect's existing verifier.

## Acceptance

On 2026-11-16 the maintainer accepted RFCs 0034 to 0038 together, the registry line's five records.
The different-vendor review was waived (RFC 0034, Unresolved question 1).

**What acceptance rests on.** One review round by a model from the drafting vendor, read-only, by a
reviewer that did not write the records, over all five. It is recorded on
[pull request 340](https://github.com/Judgment-Pack/judgment-pack-spec/pull/340) with the
maintainer's disposition of each finding (seven HIGH, nine MEDIUM and two LOW, each fixed in that
pull request), and copied verbatim to [`rfcs/reviews/0034-round-1.md`](https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/rfcs/reviews/0034-round-1.md).

The changes made after that round are not covered by it: nothing in this record, and the Status lines, notices,
this section and the index rows that record the acceptance.

**What this leaves unestablished.**

- **No different-vendor review.** RFC 0009's review has not happened. This is a same-vendor review,
  not a cross-vendor claim.
- **No companion text yet.** Acceptance settles the design. The normative text, its schemas and its
  vectors come in later pull requests, and the stable-maturity bar (two readers agreeing on every
  vector) is met there, not here.

## Unresolved questions

1. **Version 3 or the next version.** Version 3 is proposed and partly read already. Adding a kind
   to it is simpler, but changes a proposal that a reader has begun.
2. **The first accepted `format_version` table**: which Terraform releases the vectors are recorded
   with.
3. **OpenTofu.** It writes the same JSON forms today. Whether `terraform-file` names both, or a
   sibling kind follows, depends on whether the formats diverge.
4. **Outputs.** Plan and state outputs carry their own sensitivity markers, and some checks
   (an exported endpoint, for example) want them. They are left out of the first version to keep
   one read section per document.
5. **Review regime:** as in RFC 0034, question 1.

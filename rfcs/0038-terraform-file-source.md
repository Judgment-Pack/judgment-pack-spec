# RFC 0038: A file-sourced dialect source — Terraform plan and state JSON

- Status: Draft
- Type: Standards track, the dialect companion (`spec/dialect.md`), one new source kind. Core is
  unchanged.
- Created: 2026-11-16
- Issue: [#339](https://github.com/Judgment-Pack/judgment-pack-spec/issues/339) (the registry line)
- Related: RFC 0018 (the dialect); RFC 0034 (the registry profile), RFC 0037 (generated facts
  contracts); the dialect's `selected-file` kind (§4.2)

> This RFC, a Draft, is normative for nothing. Core is untouched.

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
shown, and the diagnostic names the code and the file's sha256, never a value.

1. **Read at most `maxBytes` bytes.** A larger file is refused (`TF-SIZE`). The sha256 of the
   bytes is computed here and recorded whatever happens next.
2. **Parse strict JSON.** The input must be UTF-8 with no byte-order mark, with nesting at most 128
   deep, with no duplicate member name in any object, and with numbers kept as their decimal text,
   never as binary floating point (`TF-JSON`). A binary plan file fails here, and the diagnostic
   says to pass the output of `terraform show -json` instead.
3. **Check the format.** The top level MUST have `format_version`, a string in the accepted list
   (§3) (`TF-FORMAT`). A raw state file, which has no `format_version`, is refused here.
4. **Check the document.** A `plan` MUST have `planned_values` or `resource_changes`. A `state`
   MUST have `values` and no `resource_changes` (`TF-DOCUMENT`).
5. **Check the sensitivity markers.** Every resource whose values are read MUST carry its mirror:
   - `sensitive_values`, for a resource under `planned_values`, `prior_state` or state `values`;
   - `before_sensitive` and `after_sensitive`, for a change under `resource_changes`.

   Every output MUST carry `sensitive`. A file in which some read value lacks its mirror is refused
   (`TF-SENSITIVITY`). An empty mirror (`{}` or `false`) is a marker that nothing there is
   sensitive. A missing mirror is not.
6. **Drop sensitive values.**
   - Every position whose mirror is `true` is removed, with all it contains.
   - A mirror member that is `true` above an object or array removes the whole subtree.
   - An output with `sensitive: true` is removed.

   Removal leaves the member absent, so a pack reading it sees `unknown`. It is never replaced by
   a placeholder, so no reader can mistake a placeholder for a value. The acquisition records the
   count of removed positions, not their pointers.
7. **Select** (§4), and build the acquired value (§5).

The members `configuration`, `variables`, `relevant_attributes` and `checks` are never read.
Variable values carry no sensitivity mirror in these formats, and a configuration can embed
literals.

### 3. Accepted formats

The companion keeps a table of accepted `format_version` values per `document`. Each row is backed
by vectors made with the Terraform release that writes it. The first table holds the versions the
reference vectors are recorded with. A version not in the table, including a newer minor of a
listed major, is refused (`TF-FORMAT`). The table grows by a patch release of the companion, with
vectors, and never shrinks within a dialect version.

This is deliberately stricter than Terraform's own compatibility promise for the JSON output. A
new minor may add members, and the sensitivity mirror of a new member is exactly what a reader must
not guess.

### 4. Selecting resources

`select` is an object of:

| Member | Form | Meaning |
|---|---|---|
| `types` | a non-empty array of distinct resource type names, such as `google_cloud_run_v2_service` | only resources of these types |
| `mode` | `managed` or `data`, optional (default `managed`) | |
| `address` | a pattern, optional | only resources whose address matches; `*` matches any run of characters other than `.` and `[`, and nothing else is special |
| `actions` | an array of plan actions, optional, `plan` only | only changes whose `change.actions` include one of these: `create`, `update`, `delete`, `read` or `no-op` |
| `max` | an integer from 1 to 10000, optional (default 1000) | more resources than this refuse the acquisition (`TF-SELECT-BOUND`) |

Resources in child modules are included, with their full address. Selection that matches nothing
yields an empty array, which is not an error: "no database is destroyed" is a valid fact.

### 5. The acquired value

The acquired value is an array, sorted by `address` in code-point order, of one object per
selected resource:

- **For `state`**: `{"address", "type", "name", "mode", "providerName", "index"?, "values"}`, with
  `values` the resource's values after §2.
- **For `plan`**: the same members, plus `actions` (the change's `actions`, as written), `before`
  and `after` (the change's values after §2), and `afterUnknown`. The last is the list of pointers,
  in `after`, of values known only after apply, taken from `after_unknown` and sorted. A value that
  is unknown at plan time is absent from `after`, so a pack reading it sees `unknown`.

Numbers are kept as decimal strings in RFC 0037's normal form, so ordered comparisons are defined.
The dialect's reads (copy and rule, §6) then turn the acquired value into facts, as for any other
source.

The acquisition record carries `{"kind": "terraform-file", "document", "formatVersion",
"sha256", "bytes", "removedSensitive", "selected"}`. It carries no path: a path names a machine, not
the evidence.

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
  in §2 step 6. A file without mirrors is refused, not read optimistically. `variables` and
  `configuration` are never read.
- **Diagnostics** carry codes, the file's digest and pointers to the failing position. They never
  carry values or resource attribute contents.
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
- **Sensitivity:** a sensitive attribute, a sensitive nested block, and a sensitive output.
- **Refusals:**
  - a missing mirror on one resource;
  - a raw state file, and a binary plan;
  - an unaccepted `format_version`;
  - a duplicate member name, too deep, too large, and over the selection bound.
- **Selection:** child-module addresses, `count` and `for_each` indexes, and data sources.

Every vector asserts that no value marked sensitive appears in the acquired value, the facts, the
lineage or any diagnostic.

## Implementation

1. **The reference runtime:** the reader of §2 to §5, fuzzed on the JSON reader and the pattern
   matcher, and the batch tool of §6.
2. **The reference Runner:** the kind, when the dialect version that holds it is in force.
3. **A second reader in Python** for the vectors, beside the dialect's existing verifier.

## Unresolved questions

1. **Version 3 or the next version.** Version 3 is proposed and partly read already. Adding a kind
   to it is simpler, but changes a proposal that a reader has begun.
2. **The first accepted `format_version` table**: which Terraform releases the vectors are recorded
   with.
3. **OpenTofu.** It writes the same JSON forms today. Whether `terraform-file` names both, or a
   sibling kind follows, depends on whether the formats diverge.
4. **Review regime:** as in RFC 0034, question 1.

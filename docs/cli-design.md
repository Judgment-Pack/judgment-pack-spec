# Protoss CLI for JPS

> **Status: informative tooling design; implementation and releases are separate**
>
> The public [`protoss-cli`](https://github.com/protossai/protoss-cli) repository implements the
> initial commands and owns its [installation and release
> instructions](https://github.com/protossai/protoss-cli#install-a-tagged-release). CLI behavior is
> nonnormative and its pre-1.0 interfaces may change independently of JPS releases.

The developer tool is an extensible `protoss` executable with Judgment Pack Specification (JPS)
functionality under the `protoss spec` namespace. It lives in a separate `protoss-cli` repository,
remains nonnormative, and must consume immutable JPS releases in the same way as any independent
implementation.

The [tooling architecture](tooling-architecture.md) defines the repository and authority boundary.
This page proposes the user-facing command structure within that boundary.

## Product goals

The CLI should help developers inspect and test JPS documents without turning a Protoss
implementation into the specification.

Its initial goals are to:

- validate carrier, structural, and semantic document conformance offline;
- distinguish an invalid document from an unsupported version or required extension;
- run the public, version-pinned conformance corpus;
- expose the exact schema and specification versions used by the tool;
- produce stable, automation-friendly results alongside readable terminal output; and
- leave room for additional Protoss developer-tool namespaces and later JPS authoring tools.

It must not claim evaluator conformance, infer a decision outcome, fetch cited sources, authorize an
action, or present document validity as proof of truth, authenticity, authority, safety, or
operational fitness.

## Command shape

The executable name is `protoss`. Specification tooling is one explicit namespace beneath it:

```text
protoss
├── version
└── spec
    ├── validate <pack-or->
    ├── test-conformance [suite]
    ├── schema <spec-version>
    └── explain <diagnostic-code>       # deferred until codes are stable
```

The minimum viable implementation contains `validate`, `test-conformance`, and bundled schema
access. `explain` should not ship until the project publishes a stable, versioned diagnostic
contract.

There should be no unqualified `evaluate`, `decide`, or `execute` command while JPS defines no
evaluator-conformance class or portable decision result.

## `protoss spec validate`

Current usage:

```text
protoss spec validate [options] <pack-or->
```

`<pack-or->` accepts one local file path or `-` for standard input. The initial command should not
accept an HTTP URL. Validation should proceed in order:

1. Parse the JSON carrier while rejecting duplicate object member names.
2. Inspect the root `specVersion` using a version-neutral dispatch check.
3. Select the exact supported JPS artifacts declared by that value.
4. Apply the matching structural schema with required URI, date, and date-time assertions.
5. Check normative semantic document constraints and local references.
6. Compare required extensions with capabilities explicitly supported by the installed tool.

Dispatch has an explicit classification order. Malformed JSON or a duplicate member is carrier
`invalid`. A parsed value that is not an object, or whose root `specVersion` is absent or not a
string, is structural `invalid`; the tool must not guess a release. A syntactically usable but
unsupported exact version is `unsupported`. Only a recognized exact version selects a full schema.

The default runs every supported document-conformance layer. The `--through` option can stop
after `carrier` or `structural` for debugging. A partial result must include the requested scope and
the layers attempted, set `fullDocumentConformance` to `false`, and render success as, for example,
“valid through structural (partial validation).” It must never render an unqualified “valid
document” message.

Examples:

```text
protoss spec validate pack.json
protoss spec validate --format json pack.json
protoss spec validate --through structural -
```

The command should be deterministic for the same input, CLI version, supported extensions, and JPS
artifact set. It should never evaluate the pack's rules or emit one of its declared outcomes.

## `protoss spec test-conformance`

Current usage:

```text
protoss spec test-conformance [--spec-version <version>] [options] [suite]
```

With no `suite`, the command should run the immutable corpus for `--spec-version`. In the current
implementation, omitting that option selects exactly `0.1.0-draft`; help and output identify that
selection. A supplied suite should be a local manifest path or a directory
containing exactly `manifest.json` at its root; the runner should not search parent, child, or
network locations. Its declared `specVersion` must match an explicit `--spec-version` when both are
present. Remote mutable branches should not be the default test authority.

The runner should:

- validate the manifest before reading case paths;
- preserve malformed and duplicate-member fixtures exactly;
- compare actual results and diagnostic locations with manifest expectations;
- count an expected invalid case as a passing conformance test when it is rejected correctly;
- report unsupported required capabilities separately from invalid documents; and
- identify the corpus version and integrity digest in its output.

This command tests one implementation against a document corpus. A passing suite does not certify
the implementation or create an evaluator-conformance claim.

The initial implementation computes one corpus digest over `manifest.json`,
`manifest.schema.json`, and every fixture's original bytes. Its
`sha256-length-prefixed-v1` format sorts the relative POSIX paths, then hashes each path and file
body as an unsigned 64-bit big-endian byte length followed by those exact bytes. The CLI reports
that digest for a bundled suite and computes it by the same format for a local suite, so equivalent
corpora have the same value.

Machine output should contain a suite summary and one result per case. Each case should identify its
ID, expected and actual status, pass or mismatch state, expected diagnostic, and actual diagnostics.
An invalid case passes when the expected status is produced and its expected diagnostic code and
JSON Pointer are present; additional deterministic diagnostics do not fail the case unless a future
manifest explicitly requires an exact set. Failure to load the suite is an operational error, not a
case mismatch.

The implementation retains at most 100 diagnostics per document result and 1,000 across one suite
result. Machine results expose `diagnosticsTruncated`, including on individual suite cases, so a
consumer never has to infer whether the configured output limit was reached.

## `protoss spec schema`

Current usage:

```text
protoss spec schema <spec-version> [--write <path-or->]
```

The exact version is required even when the CLI supports only one release. Without `--write`, the
command should report schema ID, JPS version, byte length, and SHA-256 digest in the selected human
or JSON result format. `--write <path>` should write the original schema bytes and report the same
metadata. `--write -` should emit only the raw schema bytes to standard output; it is mutually
exclusive with `--format json` and `--quiet`, and operational diagnostics belong on standard error.
The command should not silently substitute a nearby `0.x` version or fetch an unavailable schema
from a mutable branch.

## Common options

The initial option surface should remain small:

| Option | Behavior |
| --- | --- |
| `--help` | Show help for the selected namespace or command. |
| `--version` | Show the CLI version; this is distinct from JPS `specVersion`. |
| `--format human\|json` | Select human-readable or versioned machine output. |
| `--quiet` | Suppress successful human output without hiding errors. |
| `--no-color` | Disable terminal color without changing content. |
| `--through carrier\|structural\|semantic` | Stop validation after the named layer and report that scope. |
| `--max-bytes <n>` | Lower, but never bypass, the implementation's documented input limit. |

Offline operation should be the default, not an option users must remember to enable. Options that
permit network access, install code, or execute extensions do not belong in the default validation
path.

## Process input and output

In human mode, the primary command result belongs on standard output. Invocation, input/output,
resource, and internal failure explanations belong on standard error. A document reported as
`invalid` or `unsupported` is still a command result, so its human diagnostics remain on standard
output even though the process exits nonzero.

`--format json` should write exactly one UTF-8 JSON object followed by one newline to standard
output, including for normal `invalid`, `unsupported`, and `mismatch` results and handled flag or
argument errors when JSON was requested. It should never add
ANSI control sequences or human prose. Standard error should remain empty unless the CLI cannot
initialize or serialize the requested result envelope. `--quiet` applies only to human output and
is invalid in combination with `--format json`. Color should be enabled only for an interactive
terminal and must be disabled for redirected output, JSON, or `--no-color`.

Reading a pack from `-` consumes standard input once. Commands that reserve standard output for raw
bytes, such as `schema --write -`, must reject options that also claim that stream for a formatted
result.

## Result model

Every command should distinguish these states:

| Status | Meaning |
| --- | --- |
| `valid` | The document passed every document-conformance layer that the result says was run. |
| `invalid` | A carrier, structural, or semantic document requirement failed. |
| `unsupported` | The exact JPS version or a required extension capability is unavailable. |
| `error` | Invocation, input/output, resource, or internal tool processing failed. |
| `mismatch` | A conformance test did not produce its manifest's expected result. |

`unsupported` must not be collapsed into `invalid`. Likewise, a file read failure or resource-limit
failure must not be reported as a document-conformance result.

Human output should be a rendering of the same result represented by JSON, not a separate semantic
contract. A proposed machine result could have this shape:

```json
{
  "outputVersion": "1",
  "tool": {
    "name": "protoss",
    "version": "<cli-version>"
  },
  "command": "spec validate",
  "status": "invalid",
  "specVersion": "0.1.0-draft",
  "validationScope": {
    "requestedThrough": "semantic",
    "fullDocumentConformance": true
  },
  "layers": [
    { "name": "carrier", "status": "passed" },
    { "name": "structural", "status": "failed" }
  ],
  "extensions": {
    "required": [],
    "supported": [],
    "unsupported": []
  },
  "diagnostics": [
    {
      "code": "JPS-STRUCTURE-REQUIRED-MEMBER",
      "codeStability": "provisional",
      "layer": "structural",
      "severity": "error",
      "instancePath": "/decision",
      "message": "Required member is missing."
    }
  ],
  "diagnosticsTruncated": false
}
```

This example is informative rather than a normative JPS output schema. Diagnostic codes in the
current conformance corpus remain provisional. The CLI versions its JSON envelope independently
from the CLI release, JPS, and any future plugin API.

Diagnostics should use JSON Pointer instance locations, include schema locations when useful, sort
deterministically, and avoid copying sensitive input values into messages. Multiple independent
errors may be reported when doing so does not create misleading downstream noise.

## Exit codes

The initial implementation uses these process exit codes:

| Code | Meaning |
| ---: | --- |
| `0` | Command succeeded; for `validate`, the reported scope is valid. |
| `1` | Document invalid, or a conformance-suite expectation mismatched. |
| `2` | Exact JPS version or required extension unsupported. |
| `3` | Invalid invocation or configuration. |
| `4` | Input/output or resource-limit failure. |
| `5` | Internal CLI failure. |

JSON output should still include the corresponding status. Exit codes are a compact automation
signal, not the complete result contract.

For a conformance run, `0` means every case met its expectation and `1` means the suite completed
with one or more mismatches. A suite that cannot be selected because its exact JPS version or a
required runner capability is unsupported returns `2`; an invocation rejected before execution
returns `3`; an input/output or resource failure returns `4`; and an internal failure returns `5`.
When multiple processing failures occur, internal failure takes precedence over input/output or
resource failure. Expected `invalid` and `unsupported` cases that pass their assertions do not make
the suite process exit nonzero.

## Versions and extensions

During JPS `0.x`, the CLI should dispatch on the complete `specVersion`; it must not infer
compatibility from a shared prefix. Each CLI release should publish a machine-readable matrix of
the exact JPS releases, diagnostic-output versions, and plugin API versions it supports.

Released CLI builds should bundle or verify immutable tagged schemas and corpus metadata by digest.
A development build may test an exact release-candidate commit, but it must label that source as
unreleased and must not turn the mutable `main` branch into validation authority.

Development builds may temporarily embed an integrity-checked local snapshot labelled
`unreleased-local-snapshot`. The CLI release gate requires artifacts from an approved immutable
commit or tag and rejects dirty-snapshot provenance.

Plugins may add commands, renderers, integrations, or support for namespaced extensions. They must
not redefine Core fields or silently claim support for an extension. Validation must not discover,
download, install, or execute a plugin as a side effect.

## Security and privacy defaults

The CLI core should:

- operate without network access by default;
- never fetch source locators or dereference arbitrary document URIs;
- never execute strings, rules, extension values, or embedded content from a pack;
- enforce documented byte, nesting, collection, diagnostic, and processing limits;
- keep telemetry disabled unless a later design introduces explicit, informed opt-in;
- avoid writing pack content to logs, crash reports, or update checks;
- treat terminal control characters and hostile extension values as untrusted display content; and
- require an explicit action before invoking external plugins or integrations.

Security limits should produce an operational error distinct from document invalidity unless the
normative JPS carrier itself defines the exceeded limit.

## Future growth

After the validation contract is proven, the separate CLI repository could consider:

```text
protoss spec init
protoss spec inspect
protoss spec format
protoss spec migrate
protoss spec bundle
```

- `init` could create a clearly synthetic starter document.
- `inspect` could summarize document structure and references without evaluating rules.
- `format` could apply a documented presentation format without changing meaning.
- `migrate` could perform explicit, reviewable transformations between two exact JPS releases.
- `bundle` could prepare verified schemas and corpus artifacts for offline development.

These names are design directions, not reserved or promised features. New commands must document
their compatibility, security, output, and authority boundaries. Experimental behavior should be
visibly labelled and must not alter default Core validation.

## Implementation and release boundary

Implementation work lives in the separate `protoss-cli` repository. Its Go CLI owns the executable,
packaging, supported operating systems, output contract, and future public extension mechanisms.
It must test against immutable artifacts published here before release, but neither repository
should release or write directly to the other.

The current Go packages are internal implementation details. The executable and its versioned JSON
output are the only implemented integration boundary; there is no stable in-process SDK or plugin
API yet. A private commercial repository can remain separate now, but composing its commands into
the same binary requires a deliberately designed and versioned public contract first.

A passing `protoss spec validate` result would establish only the reported JPS document-
conformance scope. It would not establish truth, authenticity, organizational authority, legality,
safety, operational fitness, certification, evaluator conformance, or permission to act.

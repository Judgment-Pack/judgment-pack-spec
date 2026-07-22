# Tooling architecture

## Status and scope

This document is an informative architecture recommendation. It is not part of the normative
Judgment Pack Specification (JPS), does not define a final or released CLI contract, and does not
commit the project to a delivery date or implementation language.

The recommended ecosystem has two repositories:

| Repository | Responsibility |
| --- | --- |
| `judgment-pack-spec` | Normative JPS prose and schemas; nonnormative conformance artifacts, release metadata, synthetic examples, and the static specification site |
| separate `protoss-cli` | The extensible `protoss` executable, including the `protoss spec <command>` namespace, packaging, future public extension contracts, and tool releases |

The CLI implementation is kept in its separate public repository. This specification repository
does not contain or release the executable. CLI source code and deployment configuration should
not be added here, and the availability of a CLI release or service never changes JPS authority.

The current implementation exposes an executable and versioned JSON result boundary. Its Go
packages are internal; the plugin tree below remains a design direction, not an implemented SDK or
permission for public code to depend on a private repository.

## Why keep the repositories separate

The specification and its tools have different authority, governance, and release needs.

- A tool must not become normative merely because it is maintained by the specification steward.
  The tagged prose and schema retain authority when a CLI implementation disagrees with them.
- Specification releases should be small, reviewable, and immutable. CLI releases may respond more
  frequently to platform support, packaging, security, performance, and usability needs.
- The specification repository can remain usable by independent implementers without requiring
  Protoss packages, services, accounts, or network access.
- Runtime dependencies and plugin supply-chain risk stay outside the repository that publishes the
  interchange contract.
- The `protoss` executable can grow other namespaces without forcing those products or workflows
  into JPS Core.

The split also makes independent implementation meaningful: the conformance corpus is published by
the specification project, while the CLI is one consumer of that corpus rather than its source of
truth.

## Specification repository responsibilities

The `judgment-pack-spec` repository owns:

- normative prose and its normative references;
- versioned JSON Schemas and immutable schema identifiers;
- carrier, structural, and semantic conformance cases and their manifests;
- synthetic examples, testing guidance, release notes, and compatibility statements;
- integrity tests that detect drift among prose, schemas, examples, and conformance metadata; and
- the source and deployment configuration for a static specification site.

The static site should publish immutable views of tagged releases and clearly label any view built
from `main` as work in progress. Its rendered pages must not override the tagged source artifacts.
The site should not host a validator service, execute packs, fetch source locators, or require a
Protoss account to read the specification.

This repository should not own executable packaging, shell completion, plugin discovery, update
checks, telemetry, credentials, operating-system installers, or mutable service infrastructure.

## CLI repository responsibilities

A separate `protoss-cli` repository owns the `protoss` executable and the implementation decisions
needed to distribute it. JPS functionality belongs beneath an explicit specification namespace:

The [proposed CLI design](cli-design.md) describes the user-facing commands, result model, exit
codes, and safety defaults in more detail.

```text
protoss
├── version
├── spec
│   ├── validate <pack-or->
│   ├── test-conformance [suite]
│   ├── schema <spec-version>
│   └── explain <diagnostic-code>       # deferred until codes are stable
└── plugin
    ├── list
    └── doctor
```

The initial JPS command surface should remain deliberately narrow:

- `protoss spec validate` checks the carrier, structural schema, semantic references, and required
  extension capabilities supported by the installed tool. It reports the exact JPS release used.
- `protoss spec test-conformance` runs a selected, version-pinned corpus and distinguishes invalid
  documents from unsupported required capabilities.
- `protoss spec schema` identifies or emits an immutable schema bundled for an exact JPS release.
- `protoss spec explain` could give nonnormative help after the project publishes a stable,
  versioned diagnostic contract; it is not part of the proposed minimum viable product.

There should be no unqualified `evaluate`, `decide`, or `execute` command while JPS lacks an
evaluator conformance class. Any future experimental evaluator should be unmistakably labeled as
experimental, produce no JPS evaluator-conformance claim, and remain outside the default validation
path.

Core validation should be deterministic and offline by default. In particular, it should reject
duplicate JSON member names, assert required URI/date/date-time formats, enforce documented resource
limits, and avoid fetching source locators. Network access or external extension execution should
require a separate explicit action.

## Extensibility boundary

The umbrella executable allows JPS support to coexist with future Protoss capabilities without
expanding the JPS specification. CLI plugins may add commands, output renderers, integrations, or
support for namespaced JPS extensions, but they do not alter Core conformance.

A future plugin-facing API should have its own version and compatibility policy, separate from both
the CLI version and `specVersion`. A consumer that lacks a capability named by
`metadata.requiredExtensions` should report the document as unsupported or not fully interpretable;
installing a plugin must not silently reinterpret a Core field. Plugin installation and execution
are implementation concerns of `protoss-cli`, not of this specification repository.

## Version compatibility policy

Three versions remain independent:

1. `specVersion` identifies the exact JPS release targeted by a pack.
2. The `protoss` CLI version identifies a tool release.
3. A future plugin API version identifies compatibility between the executable and plugins.

During JPS `0.x`, the CLI should compare the complete `specVersion`; it must not infer compatibility
from a shared major or minor prefix. A CLI release may support several exact JPS releases, but it
should publish a machine-readable compatibility matrix and return an unsupported-version result for
anything outside that matrix. An unsupported version is not the same as an invalid document.

Released CLI builds should validate against immutable, tagged specification artifacts. They may
bundle schemas and corpus metadata for offline operation, provided the files retain their upstream
identifiers and are verified against recorded digests. They should never use the specification
repository's mutable `main` branch as the default validation authority.

Every validation result should identify at least the CLI version, exact `specVersion`, validation
layers run, supported required-extension capabilities, and diagnostic-contract version when one
exists. A CLI bug fix must not silently redefine JPS semantics; a normative interpretation change
requires the corresponding specification process, release notes, and compatibility analysis.

## Cross-repository testing and release flow

The repositories should integrate through immutable artifacts rather than shared source ownership:

1. A specification change updates prose, schema, examples, and focused conformance cases together
   in `judgment-pack-spec`. Its own CI validates artifact integrity before merge.
2. Before a JPS release, `protoss-cli` CI runs the proposed corpus at the exact specification commit
   or release candidate. Independent implementations can run the same artifact.
3. The specification repository publishes an immutable tag, versioned schema URL, conformance
   bundle, checksums, release notes, and matching static-site release view.
4. A normal dependency-update pull request in `protoss-cli` pins that tag and recorded checksums,
   updates its compatibility matrix, and runs old and new supported corpora. Specification CI should
   not push directly to or release the CLI repository.
5. The CLI is released on its own cadence. Its release notes state which exact JPS versions and
   diagnostic contracts it supports; a JPS release does not automatically create a CLI release.
6. Failures are classified before correction: normative ambiguity or artifact disagreement is fixed
   through the specification process, while implementation, packaging, and plugin defects are fixed
   in `protoss-cli`.

This flow permits a CLI release to support multiple JPS versions and a JPS release to be tested by
multiple tools. Neither repository needs write access to the other's release process.

## Authority and safety boundary

The CLI is a nonnormative implementation. Passing `protoss spec validate` establishes only
the document-conformance layers actually reported. It would not establish that:

- a claim or cited source is true;
- evidence is authentic or sufficient;
- an author, reviewer, plugin, or operator has organizational authority;
- a declared outcome is lawful, ethical, safe, or suitable;
- an experimental evaluator produced a portable result; or
- an external action should be performed.

The names Protoss and JPS do not confer certification or standards authority. CLI documentation,
diagnostics, plugins, and static-site presentation cannot override normative tagged JPS artifacts.
Any future certification, hosted validation, registry, evaluator, or execution service would require
its own explicit design, governance, threat model, and authorization.

## Decision for this repository

This repository remains the specification and static-site repository. It may document the expected
integration contract for developer tools, but it does not contain, deploy, or release the
`protoss` CLI. Implementation work remains in the separately governed `protoss-cli` repository,
which must consume immutable JPS releases like any other implementation.

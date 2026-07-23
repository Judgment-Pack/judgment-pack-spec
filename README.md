# Judgment Pack Specification

[![Repository conformance](https://github.com/Judgment-Pack/judgment-pack-spec/actions/workflows/conformance.yml/badge.svg)](https://github.com/Judgment-Pack/judgment-pack-spec/actions/workflows/conformance.yml)

> **Status: Research Preview — `0.1.0-draft`**
>
> This repository is an early design proposal. It is not an industry standard, is not covered by
> compatibility guarantees, and is not ready for consequential production decisions.

Core `0.1.0-draft` supports testing carrier, structural, and semantic document conformance. It does
not define evaluator conformance or a portable decision result.

The Judgment Pack Specification (JPS) explores a portable, vendor-neutral way to represent
reusable organizational judgment.

Traditional knowledge systems answer “what information is available?” A Judgment Pack is intended
to make a different artifact portable: what decision is being made, what evidence it requires,
where its claims came from, when it applies, how exceptions and uncertainty are handled, which
outcomes are possible, and when a human must take over.

## Why this repository exists

AI systems increasingly participate in business decisions, but prompts, retrieval configurations,
and application code do not provide a stable interchange format for organizational judgment. This
research preview exists to test whether a small declarative core can support independent tools and
runtimes without standardizing any one product, model, or workflow.

The specification is successful only if independent implementations can exchange the same pack and
agree on its document structure and declared field and reference semantics. Portable evaluation is
a possible later profile, not a claim of this draft.

## What JPS is

- A JSON-based interchange format for decision intent, evidence requirements, rules, exceptions,
  outcomes, uncertainty handling, escalation, sources, and traceability.
- A specification that separates document conformance from factual truth and organizational
  authorization.
- A potential foundation for validators, authoring tools, registries, evaluation systems, and
  execution engines maintained by different vendors.

## What JPS is not

- A claim that a conforming pack is correct, safe, authorized, or suitable for a particular use.
- A prompt format, chain-of-thought format, retrieval API, workflow engine, or general-purpose rule
  language.
- A standard for model selection, inference, optimization, calibration, enterprise identity, or
  user-interface behavior.
- A stable standard. All `0.x` material may change incompatibly.

## Repository contents

| Path                                                                             | Purpose                                             |
| -------------------------------------------------------------------------------- | --------------------------------------------------- |
| [`spec/judgment-pack-core.md`](spec/judgment-pack-core.md)                       | Normative prose for document conformance            |
| [`schema/judgment-pack-core.schema.json`](schema/judgment-pack-core.schema.json) | Normative Draft 2020-12 structural schema           |
| [`examples/`](examples/)                                                         | Synthetic examples from unrelated domains           |
| [`conformance/`](conformance/)                                                   | 47 non-normative document-conformance test cases    |
| [`TESTING.md`](TESTING.md)                                                       | A 10–15 minute external testing exercise            |
| [`VERSIONING.md`](VERSIONING.md)                                                 | Release and compatibility policy                    |
| [`CHANGELOG.md`](CHANGELOG.md)                                                   | Draft and published change history                  |
| [`docs/design-principles.md`](docs/design-principles.md)                         | Design constraints                                  |
| [`docs/non-goals.md`](docs/non-goals.md)                                         | Explicit boundary                                   |
| [`docs/origin-and-boundary.md`](docs/origin-and-boundary.md)                     | Relationship to Protoss AI                          |
| [`docs/cli-design.md`](docs/cli-design.md)                                       | Install and use the nonnormative Protoss CLI        |
| [`docs/tooling-architecture.md`](docs/tooling-architecture.md)                   | Boundary for the separate `protoss` CLI             |
| [`jeps/0000-jep-process.md`](jeps/0000-jep-process.md)                           | Proposed change process                             |
| [`ROADMAP.md`](ROADMAP.md)                                                       | Evidence-gated path toward a specification          |
| [`web/`](web/)                                                                   | Static documentation site and deployment guide      |
| [`.vscode/tasks.json`](.vscode/tasks.json)                                       | One-command local documentation preview             |

This repository intentionally contains no end-user CLI source. The separate, public, nonnormative
[`protoss-cli`](https://github.com/protossai/protoss-cli) repository exposes JPS tools under
`protoss spec <command>` and consumes immutable specification releases like any other
implementation. Its current integration boundary is the executable and versioned JSON output; no
stable Go SDK or plugin API exists yet. See the self-contained [Protoss CLI guide](docs/cli-design.md)
for installation and usage, and the
[tooling architecture recommendation](docs/tooling-architecture.md).

## Minimal shape

```json
{
  "specVersion": "0.1.0-draft",
  "id": "https://example.com/judgment-packs/expense-approval",
  "version": "0.1.0",
  "title": "Expense approval",
  "decision": {
    "intent": "Determine whether an expense may be automatically approved.",
    "question": "May this expense be approved without human review?"
  },
  "outcomes": [
    { "id": "approve", "label": "Approve" },
    { "id": "manual-review", "label": "Manual review" }
  ],
  "rules": [
    {
      "id": "large-expense",
      "description": "Large expenses require a human decision.",
      "when": {
        "op": "fact",
        "path": "/expense/amount",
        "operator": "greater-than",
        "value": "5000"
      },
      "outcome": "manual-review",
      "onUnknown": "escalate"
    }
  ],
  "fallbackOutcome": "approve"
}
```

See the complete example before relying on this abbreviated shape.

## Conformance, truth, and authority

These are deliberately separate claims:

1. **Carrier conformance:** the serialized input satisfies the JSON and carrier requirements.
2. **Structural conformance:** the document satisfies the JPS schema, including asserted formats.
3. **Semantic document conformance:** local references and cross-field constraints satisfy the
   normative prose.
4. **Factual grounding:** evidence supports the pack's claims.
5. **Organizational authorization:** an accountable organization permits the pack's use.
6. **Operational fitness:** a particular runtime applies it safely and effectively.

This research preview specifies the first three document claims. It explicitly does not specify
evaluator conformance; the condition and resolution sections are informative experiments only. A
validator must never imply factual grounding, organizational authorization, or operational fitness.
The core specification defines the
[normative artifact roles and precedence](spec/judgment-pack-core.md#11-normative-artifacts-and-precedence).

## Test this preview

Follow [`TESTING.md`](TESTING.md) to validate the supplied examples, observe the schema/semantics
boundary, make a small synthetic authoring change, and report reproducible feedback. In addition to
the minimal example, the repository includes deliberately non-operational examples for software
change readiness and records disposition review.

The repository also includes a minimal static documentation site. Build it locally with:

```bash
python3 -m pip install -r requirements-dev.txt
python3 web/build.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory public
```

Then open `http://localhost:8000`. The generated `public/` directory contains only static HTML,
CSS, and raw artifacts; no pack is executed and no source locator is fetched. See
[`web/DEPLOYMENT.md`](web/DEPLOYMENT.md) for preview-first hosting guidance.

### Preview from VS Code

Open the repository in WSL with VS Code, then select **Terminal → Run Task → JPS: Preview site**.
The task creates the ignored `.venv/`, installs the pinned dependencies, rebuilds `public/`, and
serves it at [http://localhost:8000](http://localhost:8000). Follow the link in the task terminal and
press `Ctrl+C` there to stop the server.

Use **Terminal → Run Build Task** or `Ctrl+Shift+B` to install dependencies and rebuild the site
without starting the server. The task definitions are in [`.vscode/tasks.json`](.vscode/tasks.json).

These exercises test documents, not decisions. Do not infer or automate a real outcome from a pack
and do not present agreement between experimental evaluators as JPS conformance.

## Participate

Start with [`TESTING.md`](TESTING.md) for a short exercise or
[`CONTRIBUTING.md`](CONTRIBUTING.md) to propose a change. Material changes should begin as a
Judgment Enhancement Proposal (JEP), include compatibility and security analysis, and add positive
and negative examples.

The project is initially stewarded by Protoss AI. Stewardship does not make Protoss implementations
normative; the long-term goal is reproducible behavior across independent implementations.

## License

Licensed under the Apache License 2.0. See [`LICENSE`](LICENSE).

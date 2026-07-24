# Changelog

All notable changes prepared for or included in Judgment Pack Specification previews are recorded
here.

## Unreleased

### Changed

- Renamed the change-proposal process from Judgment Enhancement Proposal (JEP) to Request for
  Comments (RFC); moved `jeps/` to `rfcs/`. The required sections and evidence bar are unchanged.
  The historical `0.1.0-draft` entry below is left as shipped.
- Implementations page: replaced the Protoss CLI listing with the vendor-neutral `judgment-pack`
  reference runtime (which inherited the CLI implementation), linking to its own repository, and
  removed the Protoss-branded on-site CLI page. Every page on the site is now vendor-neutral.

### Added

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

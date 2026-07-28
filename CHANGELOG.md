# Changelog

All notable changes prepared for or included in Judgment Pack Specification previews are recorded
here.

## Unreleased

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
  gaps: no error rows, no number-representability row (deliberately — that question is open), thin
  handoff coverage on the imported rows, no `suppress-rule` row, and no permutation or hostile rows.
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
  document format is unchanged, so a `0.1.0-draft` pack is unchanged in meaning and needs only that one
  value edited; because the value is exact, an unedited pack is not structurally conforming here. The
  `0.1.0-draft` schema is preserved at `schema/judgment-pack-core-0.1.0-draft.schema.json` and is still
  served at its own `$id`. `conformance/structural/invalid-spec-version.json` now carries `0.1.0-draft`
  as its negative value, which makes the re-declaration requirement a corpus case.
- The evidence behind the change is two implementations agreeing 13/13. Both trace to one maintainer's
  direction, so that agreement corroborates the semantics rather than independently confirming them,
  and RFC 0000's bar for a *stable* feature is still unmet — carried as a caveat in the RFC's adoption
  record, the release notes, and the corpus README rather than stated once and forgotten.
- Every assertion that evaluator conformance cannot be claimed is now the `0.2.0-draft` truth: the
  class exists, claims are governed by §3.4.1, and no implementation ships a claim with this release.
  The reference runtime's evaluator remains experimental and claims nothing; whether it claims the
  class is a decision for that repository.

- Renamed the change-proposal process from Judgment Enhancement Proposal (JEP) to Request for
  Comments (RFC); moved `jeps/` to `rfcs/`. The required sections and evidence bar are unchanged.
  The historical `0.1.0-draft` entry below is left as shipped.
- Implementations page: replaced the Protoss CLI listing with the vendor-neutral `judgment-pack`
  reference runtime (which inherited the CLI implementation), linking to its own repository, and
  removed the Protoss-branded on-site CLI page. Every page on the site is now vendor-neutral.

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

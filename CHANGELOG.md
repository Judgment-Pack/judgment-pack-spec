# Changelog

All notable changes prepared for or included in Judgment Pack Specification previews are recorded
here.

## Unreleased

### Added

- RFC 0010 (Draft): the gateway signing identity — custody of the private seed (which also keys
  the arguments commitment), content-binding seals, key rotation in the registry, and external
  checkpoint anchoring of sealed history. The first RFC whose every part lands outside JPS — in
  the reference gateway repository's code, specification, guidance, and corpus — and the
  architecture vision's statement that no RFC proposes the research line's formats as JPS remains
  true. Prompted by a stray private seed found untracked in the runtime repository's working
  tree; the ignore-rule guards shipped separately in both repositories.
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
  gaps: no error rows, no number-representability row (deliberately — that question is open), handoff
  coverage counted row by row, three mandatory operators (`not-equals`, `greater-than`,
  `less-than-or-equal`) with no row, no `literal`, `not`, composite-equality, or fallback-selection row,
  no `suppress-rule` row, no permutation or hostile rows, and the inputs its carrier cannot yet express.
- **The claim's scope is the contract, not the corpus (§§3.4, 3.4.1, 3.5).** An evaluator-conformance
  claim asserts compliance with the whole §§7–10 contract for every input the implementation admits;
  corpus results are required, non-exhaustive evidence of that. A claim must state that every row of the
  named corpus version passed, and a failed row blocks the claim.
- **An erratum mechanism for a frozen corpus** at
  [`conformance/evaluation/errata.md`](conformance/evaluation/errata.md). Only a project-issued, versioned
  erratum can mark a row of a released corpus defective — a claimant cannot — and an erratum edits no row.
  It is in place and empty for `suiteVersion` `0.2.0-draft`.
- **Input preflight (§8.2).** The inputs are admitted before §8 runs, in the order pack, facts, evidence
  availability; an omitted evidence document is the implicit empty object; any violation of §8.2's shape,
  including a non-object evidence input, is `malformed-input`; and because preflight completes before step
  1, an input error can never be outraced by a `not-applicable` result.
- Two optional case members in the evaluation carrier, defined now and used by no row so that later rows
  need no carrier change: `workBudget` (a positive integer of work units, in the units a future accounting
  model will define) and `expectedErrorPhase` (`preflight` or `evaluation`, alongside `expectedErrorClass`
  only).
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
  document format is unchanged, so a `0.1.0-draft` pack is unchanged in representation and
  document-conformance meaning and needs only that one value edited; because the value is exact, an
  unedited pack is not structurally conforming here. Re-declaration is not inert, though: it opts the pack
  into this draft's evaluator semantics, which existed for no consumer under `0.1.0-draft`, and confers no
  conformance on any implementation. The `0.1.0-draft` schema is preserved at
  `schema/judgment-pack-core-0.1.0-draft.schema.json`, and that draft's document-conformance manifest
  schema at `schema/conformance-manifest-0.1.0-draft.schema.json`, both served at the `$id` each was
  published under so a previously cited identifier still resolves. Each preserved file matches the tagged
  `v0.1.0-draft` artifact in every byte except its `$id` member, which was re-pointed to the project's
  neutral domain when the retired pre-publication identifier was withdrawn; `releases/v0.2.0-draft.md`
  publishes the digests of both forms. `conformance/structural/invalid-spec-version.json` now carries
  `0.1.0-draft` as its negative value, which makes the re-declaration requirement a corpus case.
- §8.4's classes are split by phase so the error contract cannot contradict §10: a documented document or
  carrier limit reached while admitting an input is `malformed-input` (§2.1 refuses the document, so
  preflight never admits it), while a collection-size or evaluation-work limit reached during evaluation is
  `resource-exhaustion`. Every error carries exactly one class — a Core class where one applies, otherwise
  a documented implementation-defined class in §9's reverse-domain form.
- `tools/build_release.py` now requires `HEAD` to be the resolved release commit. Artifacts are validated
  from the worktree and archived from the commit, so the gate previously accepted a validated tree and an
  archived tree that were not the same tree.
- The evidence behind the change is two implementations agreeing 13/13. Both trace to one maintainer's
  direction, so that agreement corroborates the semantics rather than independently confirming them,
  and RFC 0000's bar for a *stable* feature is still unmet — carried as a caveat in the RFC's adoption
  record, the release notes, and the corpus README rather than stated once and forgotten.
- Every assertion that evaluator conformance cannot be claimed is now the `0.2.0-draft` truth: the
  class exists, claims are governed by §3.4.1, and no implementation ships a claim with this release.
  The reference runtime's evaluator remains experimental and claims nothing; whether it claims the
  class is a decision for that repository. The site says the same: the implementations listing no longer
  says the runtime does not evaluate rules, and the example guides no longer call a conflict result
  unportable now that §8.3 makes it a portable `unresolved` disposition.

- Renamed the change-proposal process from Judgment Enhancement Proposal (JEP) to Request for
  Comments (RFC); moved `jeps/` to `rfcs/`. The required sections and evidence bar are unchanged.
  The historical `0.1.0-draft` entry below is left as shipped.
- Implementations page: replaced the earlier vendor-branded CLI listing with the vendor-neutral
  `judgment-pack` reference runtime (which inherited that CLI's implementation), linking to its own
  repository, and removed the vendor-branded on-site CLI page. Every page on the site is now
  vendor-neutral, and no page names the retired pre-publication brand.
- **The first evaluator-conformance claim now exists, and the site stops saying it does not.** The
  reference runtime states one for `0.2.0-draft` in its own repository. Four surfaces asserted the
  opposite as present fact and are corrected: the overview (`README.md`), the architecture vision's
  Runtime row, FAQ Q33, and the implementations listing. Each now records that a claim exists and
  where it lives, and none restates any part of it — a partial restatement is what §3.4.1 forbids, and
  the distinction the corrected text carries is that `experimental` on a runtime surface reports
  *stability* and never conformance. The dated records are deliberately not edited: the
  `0.2.0-draft` release notes and the entries above describe what was true at that release.
- Implementations page: added the clean-room Python evaluator as a second listing, with a stated
  caveat that both implementations trace to one maintainer and so corroborate the specification's
  precision rather than evidencing independent interoperability.
- Site ecosystem update: the landing hero now gives Slack and the public project repositories the
  same first-screen prominence as the specification, and a status-labelled project directory links
  the runtime, cloneable demo, gateway, and research repositories without presenting any companion
  tool as normative. The Implementations page now links directly to runtime releases, build and MCP
  guidance, and the runtime's complete conformance claim; records project matrices, experimental
  graphs, opt-in evaluation records, and reviewed-set locking as non-normative runtime behavior; and
  lists the demo and gateway separately as companion projects. It also corrects the stale statement
  that the runtime never produces an outcome: its evaluator produces a disposition from supplied
  inputs, which never authorizes an action or establishes truth, safety, or fitness.
- Architecture vision: recorded that where a pack's *inputs* come from is an open question outside
  this specification, naming the research repositories and the reference gateway — with their stated
  ceiling, byte-lineage rather than truth, carried on the site rather than left to the reader.
- Architecture vision: distinguishes the inline HMAC acquisition proxy from the incompatible
  Ed25519 gateway and adds the portable-derivation and deterministic-admission steps between
  acquisition and evaluation. The page and presentation now state that no runtime consumes these
  formats and that none is part of JPS; the architecture diagram also reflects Core
  `0.2.0-draft`'s evaluator class and a runtime that evaluates as well as validates.
- RFC 0002: the runtime's graph prototype is no longer described as living unmerged on a branch. The
  reviewed commit stays pinned; the surface has since merged, shipped, and grown past it.

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

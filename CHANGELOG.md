# Changelog

All notable changes prepared for or included in Judgment Pack Specification previews are recorded
here.

## Unreleased

### Added

- The staged Runner manifest of the dialect vectors brought to Runner commit `a4fa245`, pull
  request 137 (issue #205): the one expectation it changes, the `verifyRun.report` of
  `disposition-differs-from-audit`, now carries the preparation's checked report beside the
  finding. No vector file, count or status changes, and the cross-reader test's comparison of a
  reading with the report now covers that vector. `source.extendedBy` records the commit with no
  vectors.
- The fortieth and forty-first dialect vectors, `acquired-dependent-source` and
  `acquired-dependent-source-unknown`, staged byte for byte from Runner commit `694fe69`, pull
  request 109 (issue #203), beside the thirty-nine unchanged vectors: an acquired source that
  declares source parameters, its claim `resolved` or `unknown`, whose lineage entries name every
  declared parameter in `dependencies` (§9.3). Both readers, unchanged, recompute each preparation
  byte for byte and give a reading whose binding `matches`, and the cross-reader test holds their
  reports equal on all forty-one. The vectors remain staged until the next `specVersion` opens, in
  no corpus.
- The thirty-ninth dialect vector, `skipped-source-dependency-unavailable`, from Runner commit
  `ed1bc2a`, pull request 105, staged byte for byte beside the thirty-eight unchanged vectors.
  The vectors remain staged until the next `specVersion` opens, in no corpus.
- The reference Runner's twenty-six research vectors, the first of the kind `research`, are staged
  byte for byte in [`conformance/dialect/`][staged-dialect] beside the twelve, from the Runner's
  pull request 97 (issue #190): the runs of the two examples of [`spec/dialect.md`](spec/dialect.md)
  §11's fixture plan, `gtm-company-person` and `work-item-triage`, each a dialect of version 3 bound
  at import, its responses recorded from a stand-in of a gateway. Both readers, unchanged, give each
  the Runner's answer: a reading whose binding `matches` for twenty-two, `preparation-differs` for
  the two `changed-binding-old-preparation`, and `acquisition-invalid` for the two
  `changed-response`, and the cross-reader test now holds the two readers' reports equal on every
  staged vector. Those two carry a value of the Runner's manifest new here, `retained: "recorded"`:
  their inputs were changed after the run, so no preparation can be computed from them, and their
  `preparation.json` is the preparation the run recorded, held fixed. The staging README defines it,
  and the repository's tests hold such a file to the Runner's digest as it is and recompute nothing
  from its inputs. They recompute the two `changed-binding-old-preparation`, whose export retains a
  preparation of an earlier instant, at the vector's own `verifiedAt`. RFC 0018 is amended with them
  (2026-10-16, round 11), and the companion document with it; its status stays `Accepted`. §11 says
  that a fixture whose inputs were changed after the run holds the recorded preparation fixed and
  expects the finding the change gives; and the text says what is now so: the Runner prepares
  `research`, twenty-six vectors hold it, and the companion's Status counts thirty-eight vectors
  (§§4.3, 8.2, 9.1, 11 and the Status). No answer a reader gives changes. The review of round 11,
  two MEDIUM findings, both applied, is recorded with the maintainer's disposition in
  `rfcs/reviews/0018-round-11.md`.
- [RFC 0020](rfcs/0020-workflow.md) (Draft): the workflow, a proposed companion document beside
  Core, with a `workflow-verifier` reader class. It defines pinned stages, a selection between
  stages, one instance per selected record, projected cases, output lineage and an execution
  inventory. The proposed text is added as `spec/workflow.md`, held equal to the RFC's
  Specification, normative for nothing while the RFC is a draft and in no release bundle
  (`.gitattributes`, `export-ignore`). Its two-stage run and independent readers remain to be
  recorded and implemented; no workflow fixture or conformance claim exists. Nothing in Core,
  the dialect or the conformance corpora changes.
- The reference Runner's eleventh and twelfth preparation vectors, the first of dialect version 3,
  are staged byte for byte in
  [`conformance/dialect/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/dialect)
  beside the ten, from the Runner's pull request 83: `version-3-bound`, the valid case's dialect
  written as version 3, and `unbound-bound-at-import`, a dialect published with its source unbound,
  with its binding document and the bound dialect the Runner made of them. Both readers,
  `tools/dialect_verify.py` and `tools/dialect-verify-ts/`, now read dialect version 3 as
  [`spec/dialect.md`](spec/dialect.md) §§4.3, 4.4 and 9.1 define it: a document of version 3 is read
  as one of version 2, and its preparation is of version 3; an unbound source is read with its
  binding document, as the bound dialect, and a binding document of another dialect, or one that
  does not name exactly the unbound sources, is refused, and a profile bound of another shape or
  record is `profile-mismatch`; a source of a kind of §4.3 is held to its form and refused as
  `kind-unread`. Both give the two vectors the Runner's answer, a reading whose binding `matches`.
  The extension is one author's, who read both readers, so for these two their agreement is not
  independent. RFC 0018 is amended with them (2026-10-15), and the companion document with it; its
  status stays `Accepted`. The text now says what is so: the reference Runner reads version 3 since
  its pull request 83 (`v0.12.0`), preparing `operation` and `selected-file` and refusing `http`,
  `sql`, `web` and `research` by name, and two vectors hold version 3 (§§2, 4, 4.3, 4.4 and the
  Status); §14's claim form admits a claim of version 3 beside version 2. Version 3 is written one
  way (§2): a document of version 3 that names `provider`, `facts` or `evidence`, members of version
  2 alone, or writes empty a member the Runner's encoding leaves out when empty (`sources`,
  `unmapped`, `unmappedEvidence`, the case's and a source's `parameters`, and `admits`' `facts` and
  `evidence`), is refused, and both readers refuse both. The Evidence records the readings both
  readers take where the text names a member of a version-3 kind without a form. The amendment's
  review, round 7, recorded in `rfcs/reviews/0018-round-7.md`, brought two rules more to the
  Runner's: `cites` is ordered by `callIndex` in versions 2 and 3 alike (§9.1), and a copy's
  `facts` and `evidence` are both required in every version (§6.2), which changes one answer the
  accepted text gave: a copy that left an array out was read and is refused now. Both readers now
  refuse a binding document of `null`, count a research record's 64 retained responses before any
  form (§12), and hold a `research` acquisition to its own form (§§4.3, 5.2).
- [RFC 0018](rfcs/0018-dialect.md) is `Accepted`, at draft maturity, under the interim review
  regime; the maintainer waived the comment period RFC 0000 names, because the project has no
  outside readers yet, and the adoption record says so as a departure. The RFC taken up from the
  reference Runner's mapping v2 is the dialect, a pack's terms spoken in a system's: how the facts
  and the evidence availability an evaluation takes are obtained and derived, with a reader class
  of its own, the *preparation verifier*, which recomputes a preparation and holds a runtime
  record's binding to it. Its Specification section, word for word, lands as the companion document
  [`spec/dialect.md`](spec/dialect.md), normative for that class and for nothing else, beside the
  released Core `0.2.0-draft`, which it does not change. Core §1.1's list of normative artifacts
  gains it, the architecture vision's sentence that nothing in the input-lineage research line is
  part of JPS gains it as a second exception, and the site serves it as a page of its own. Version
  2 of the dialect document is the Runner's mapping v2 byte for byte, and the preparation's
  canonical form is the Runner's, stated there; version 3, with the kinds `http`, `sql`, `web` and
  `research`, is proposed and not claimable; the output side is the gateway's decision policy, by
  reference. The RFC states what a preparation establishes per part: a derivation is recomputable,
  an acquisition is held by its digest under its receipt, and a research record establishes the
  least. The Runner's 9 preparation vectors in
  [`conformance/dialect/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/dialect),
  byte for byte unchanged, stay **staged** until the next `specVersion` opens: in no corpus, no
  claim may cite them, the site does not serve them, and no release bundle carries them. Two
  readers, `tools/dialect_verify.py` and `tools/dialect-verify-ts/` (the second written from the
  text alone), agree on all nine. The records of the RFC's three review rounds, as their pull
  requests carry them, are added under `rfcs/reviews/`.
- [RFC 0017](rfcs/0017-checkpoint-witness-statement.md) is `Accepted`. Its Specification section,
  word for word apart from one pointer to the vectors, lands as the companion document
  [`spec/checkpoint-witness.md`](spec/checkpoint-witness.md), normative for a new conformance
  class, the *witness-statement reader*, and for nothing else, beside the released Core
  `0.2.0-draft`, which it does not change. Core §1.1's list of normative artifacts gains it, and the
  architecture vision's sentence that nothing in the input-lineage research line is part of JPS
  gains its first exception, the statement. The gateway's 54 vectors in
  [`conformance/witness/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/witness),
  byte for byte unchanged, stay **staged** until the next `specVersion` opens, as RFC 0013's rows
  are: in no corpus, no claim may cite them, the site does not serve them, and no release bundle
  carries them. When that version opens they move into a corpus and Core §1.1's list gains them;
  whether they take a `suiteVersion` of their own stays open (the RFC's first unresolved question).
  The record of the RFC's first review round, as its pull request carries it, is added under
  `rfcs/reviews/`.
- [RFC 0017](rfcs/0017-checkpoint-witness-statement.md) (Draft): the checkpoint witness statement,
  taken up from the reference gateway (`v0.11.0`, `SPEC.md` §8) as a proposed companion document of
  the specification, with a reader conformance class of its own. The maintainer's decision on issue
  #122 is that the statement is taken up, with its vectors the same bytes as the gateway's; the RFC
  restates its canonical form, signed bytes, key rule and equation, chain rule, reading, bounds,
  refusals, findings and report sentences, changing no rule a reader applies. It leaves to the
  gateway one rule on the producer, that a gateway witness signs with the gateway's own seed, and
  says what it resolves of RFC 0012's question 4 and RFC 0010 §4. The gateway's 54 witness vectors
  are imported byte for byte into
  [`conformance/witness/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/witness),
  with a manifest that records each one's SHA-256. They are in no corpus while the RFC is a draft:
  no claim may cite them, the site does not serve them, and no release bundle carries them
  (`.gitattributes`, `export-ignore`). The repository's tests hold their bytes, their form and their
  counts; nothing here verifies a signature. Nothing in Core `0.2.0-draft`, its schema, its classes or
  its corpora changes.
- The field guide gains **When rules could disagree**, informative authoring guidance for a
  consequence of §8 that two independent encodings of real policy each had to discover: the format
  has no rule priority, so a pack that holds both an *allowed* rule and a *not allowed* rule answers
  `conflict` whenever one of each is true. It gives the shapes that work — detectors that all name
  one outcome with the ordinary outcome as `fallbackOutcome`; the policy's own ordering as an
  exception; disjoint conditions — says when `conflict` is the right answer, and names the trap in
  the first shape: a detector with `onUnknown: ignore` lets the fallback answer for a check that
  never ran. This is the guidance [RFC 0007](rfcs/0007-determination-boundary.md) (finding E4)
  said did not exist. Nothing normative changes.
- [RFC 0013](rfcs/0013-evaluator-error-and-precedence-cases.md) is `Accepted`, and its five rows —
  the first to use `expectedErrorClass`, two of them inputs where more than one §8.4 class applies
  and the fixed order decides — are **staged** in
  [`conformance/evaluation/staged/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/evaluation/staged)
  for the `suiteVersion`
  after `0.2.0-draft`. They are in no corpus: the `0.2.0-draft` corpus is frozen and unchanged, no
  claim may cite a staged row, the site serves nothing under the staged directory, and no release
  bundle carries it (`.gitattributes`, `export-ignore`). That does not make them optional reading:
  they restate §8.2 and §8.4 as already released, so an implementation that disagrees with one may
  be violating the released contract without having failed a released row. The RFC's four open
  questions are decided (a structural fixture that fails for its one stated reason; no asserted
  phase, because §8.4 requires a class and not a phase; two fixtures; five rows). The repository's
  check that every evidence key a case supplies be declared by its pack becomes conditional on the
  expected error class. It admits a correctly labelled error row, which it used to refuse, and asks
  more of what it still covers: the class a case expects must be the one §8.4's fixed order reports
  for the case's own inputs, read without an evaluator. For the released rows it refuses what the
  old check refused, and every one passes unchanged. The RFC was first merged without the
  cross-vendor review the interim regime requires; that cannot be undone, the adoption record says
  so, and the review on the accepting pull request is the first the proposal has had.
- RFC 0010 (Draft): the gateway signing identity — custody of the private seed (which also keys
  the arguments commitment), content-binding seals, key rotation in the registry, and external
  checkpoint anchoring of sealed history. The first RFC whose every part lands outside JPS — in
  the reference gateway repository's code, specification, guidance, and corpus — and the
  architecture vision's statement that no RFC proposes the research line's formats as JPS remains
  true. Prompted by a stray private seed found untracked in the runtime repository's working
  tree; the ignore-rule guards shipped separately in both repositories.
- Search, answer-engine, and generative-engine discoverability for the static site: every indexable production
  page now carries full-name titles, explicit index directives, complete Open Graph and summary-card
  metadata, sitemap and license discovery links, and schema.org Microdata for the site, project,
  versioned technical specification, visible breadcrumbs, and all 47 complete FAQ answers. FAQ
  questions now render as stable semantic headings without adding executable JavaScript, and a
  concise experimental `/llms.txt` navigation aid points machine readers to the normative,
  informative, proposed, and companion-project surfaces without claiming crawler or ranking support.
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

- RFC 0018 and its companion, issue #200: the `dependencies` row of §9.3's lineage table no longer
  says the member is absent for a local file. It reads "absent for the case and a source that
  declares none", as round 12's rule in the same section already gives it to every source that
  declares a source parameter, acquired or skipped; the reference Runner writes it for a local
  file with parameters. A correction of a contradiction inside round 12's own text, not a new
  rule. Both readers already follow the general rule; no reader changes, no vector is changed.
- RFC 0018 and its companion record issue #197, option A (2026-10-16, round 14): a `selected-file`
  of provider `google-drive` requires a `drive` input profile of class `record`, and its binding
  is `record`; a profile of class `generated` bound to it is `profile-mismatch` (§§4, 4.2 and 5.1).
  The reference Runner already enforces this rule. Neither repository reader reads the kind,
  and no vector holds it; §5.1 marks the rule as a position no vector decides. No reader changes,
  and no vector is changed or claimed; the review and the maintainer's disposition are recorded
  in `rfcs/reviews/0018-round-14.md` (six LOW, five applied and one noted).
- RFC 0018 and its companion record issue #195 (2026-10-16, round 13): §5.1 states which class
  a binding takes, by kind, with references from §§4, 4.4 and 8.2. An `operation` of any admitted
  shape takes its profile's class; research capability bindings take `generated`, and `web`
  bindings take `record`. A profile of the other class on a research or `web` binding is
  `profile-mismatch`; the `web` refusal is named for the first time, with no vector deciding it.
  The research `answer` profile serves the model's answer; `search` and `page` profiles serve
  the web reads retained with the answer — the links found, the pages read — in the research
  record. The readers are unchanged, and no vector is changed or claimed; the `web` refusal's
  vector waits for a Runner of that kind.
- RFC 0018 and its companion record issue #189, option A (2026-10-16, round 12): a skipped
  source's outcome keeps its five-member claim and status `unknown`; each of its lineage entries
  has status `unknown`. Every source that declares a source parameter, acquired or skipped,
  carries `dependencies`, all declared source parameters in parameter-name order, including those
  that have a value (§§9.2–9.3); the member is absent for the case, a local file and a source that
  declares none. Both readers follow, recompute the thirty-ninth vector's preparation byte for
  byte and give a reading whose binding `matches`. A reader of the accepted text answered
  `preparation-differs` on the Runner's skipped-source bytes and now gives a reading, and the old
  form now gives `preparation-differs`. The Runner is unchanged.
- [RFC 0019](rfcs/0019-exchange.md) stays a Draft and records issue #192, option A: entry format
  version 3 carries checked named-format references and `artifact: {id, version}` under RFC 0021.
  Integer references and kind rules remain; presets stay integer-only. Named identity includes
  the whole canonical document. Changed canonical content under an existing pair is refused
  within a release and across catalog history; identical content is admitted in another entry
  under its kind's rules. Catalog CI fetches tags and reads every previous release's manifest and
  pinned entries as blobs, refusing unreadable history as `artifact-history-invalid`, with no
  form-only fallback. Only a consumer checks form alone when it does not hold the previous
  manifest, reporting `artifact-history-unchecked`.
  Manifest rows are unchanged and upgrade keys remain released entry digests. Reader compatibility,
  publication and binding limits, and catalog and consumer test duties are recorded. The checker
  and fixtures follow in their own pull request on `judgment-pack-exchange`; the Desk's publication
  flow remains separate work. No Core, companion document or conformance corpus changes.
- [RFC 0018](rfcs/0018-dialect.md), round 10 (issue #184): the `record` of an unbound `operation`
  source names the program, as a profile's `adapter.name` and the gateway's receipt carry it, and
  never a catalog's result-contract name. [`spec/dialect.md`](spec/dialect.md) §4.4 gains the
  paragraph, equal to the RFC's; the gateway's catalog version 4 carries the program under
  `adapter`. No vector changes. The review records of rounds 9 and 10 are added under
  [`rfcs/reviews/`](https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/rfcs/reviews)
  as `0018-round-9.md` and `0018-round-10.md`.
- Both readers, `tools/dialect_verify.py` and `tools/dialect-verify-ts/`, now give RFC 0018's
  round-9 receipt answers (issue #185, and with it issue #182): a receipt's `servedAt` or
  `acquisition.observedAt` that is not a string with an instant, a `callIndex` that is not an
  integer at least zero, or a `sessionId` that is not a string is `acquisition-invalid`, before
  the time and session rules ([`spec/dialect.md`](spec/dialect.md) §5.2, check 1, and §11,
  finding 3), in versions 2 and 3, on `operation` receipts, every retained `research` response
  and a research record's own receipt; a `sessionId` is otherwise any string, not held to the
  gateway's token form. `acquisition-stale` now names only a present instant outside the window,
  and `acquisition-sessions` only a well-formed session set that fails the session rule. Before,
  the second reader gave `acquisition-stale` for a time that was not a string and
  `acquisition-sessions` for a malformed `callIndex` or `sessionId`, and both gave
  `acquisition-stale` for a string with no instant. Each reader has a unit case for each answer:
  `tests/test_dialect.py` adds cases on `operation` receipts, signed again over the `valid`,
  `version-3-bound` and `unsigned-parameters` vectors, and on research receipts, and the
  cross-reader test gives both readers all of them, their reports equal byte for byte. The twelve
  staged vectors' answers do not change. The TypeScript reader's README gives §6.4's closed
  condition list in place of the removed "Pointers are …" sentence, and the round-9 receipt rule
  in place of its old receipt readings; RFC 0018's Evidence and Implementation say what is now
  so. No sentence of §§1–14 changes. The correction is one author's, who read both readers, and
  adds nothing to the second reader's independence.
- [RFC 0018](rfcs/0018-dialect.md) and [the dialect](spec/dialect.md) are amended for
  issues #179 and #182 (2026-10-15, round 9): fixture 8 follows RFC 0020's round 2, admitting a
  research stage once a Runner pins its release form and encoding (judgment-pack-runner#88),
  with its recording beside the operation demonstration. Section 4.3 now records that both
  repository readers read `research` since #181; no preparer writes any of the four proposed
  kinds, and no vector holds one. Neither repository reader reads `http`, `sql` or `web`: each
  holds one to its form and refuses it as `kind-unread`; the reference Runner refuses all four
  by name. Reconciliation conditions name only a field entry, its `status`, its `value` or
  `values`, or descendants of `/value` or `/values`, for listed sources and their declared fields
  or this source's declared fields under `/current`; another pointer is `input-malformed`.
  This matches both readers' existing answers. Acquisitions carry exactly the responses the
  research record names, by form, with missing result bytes still `acquisition-missing`;
  `acquisition-unexpected` remains for unexpected source members. Receipt form precedes time
  and session checks: malformed time
  or session members are `acquisition-invalid`, `acquisition-stale` names only a present instant
  outside the window, and `acquisition-sessions` only a well-formed set that fails the session
  rule. `sessionId` is a string, without the gateway's token restriction. The three changed
  answers in versions 2 and 3 are a non-string time, a string with no instant, and a malformed
  `callIndex` or `sessionId`, all now `acquisition-invalid`; no vector's answer changes.
  The receipt positions carry the no-vector markers. The Evidence limits the readers' follow-up
  to those receipt answers and the TypeScript README's quotation of the removed sentence; the
  condition and response decisions need no reader change. The amendment links pull request 183,
  question 14
  uses the preparer link, and the Amended line follows the earlier entries' form. No reader or
  vector changes here, and no research fixture or conformance claim is added.
- Both readers, `tools/dialect_verify.py` and `tools/dialect-verify-ts/`, now read the research
  contract of RFC 0018's round 8 (issue #176) as [`spec/dialect.md`](spec/dialect.md) §§4.3, 4.4,
  5.1, 5.2, 6.4, 9, 11 and 12 define it: a `research` source's requested `fields` and
  `capabilities`, bound directly or through a binding document; the profiles it is bound to, each
  the trusted one of its id and digest, of class `generated`, declaring the model and the
  capability it serves, or `profile-mismatch`; the research record's typed answers, `found`,
  `not-found`, `stale` and `conflicting`, and their citation indices; each retained response
  replayed under its own profile, then the record's own receipt; a plain read's closed list of
  pointers; the reconciliation read, its guards and its combined value; `cites` in the order of
  `sources` and the lineage's `receipts`; and the research maxima of §12, counted before any form.
  Neither refuses `research` as `kind-unread` now. The three answers the amendment said would
  change, change: a research source without `fields` or `capabilities`, and a research record
  without `fields`, are `input-malformed`, and a retained response through a trusted but
  unassigned profile is `profile-mismatch`. Each reader's tests, and the repository's suite over
  both, hold hand-written documents of every new form and refusal, and the two readers' reports
  are equal on each. That agreement is one author's, who extended both from the text; no vector
  holds the kind, no fixture is recorded and nothing is claimable. The companion's Status and RFC
  0018's amendment, Evidence and Implementation say so now, and the Evidence records the readings
  both readers take where the contract's text leaves a choice.
- [RFC 0019](rfcs/0019-exchange.md) is amended by pull request #178 (2026-10-15), still Draft,
  for #166's seven sentences and #172's option A. Entry format version 2 requires `kind`,
  `dialect` or `preset`; a preset is input-only, has no pack or fixtures, and establishes its
  recipe's identity and form, nothing about a preparation. A desk pairs it with a pack locally
  before any run;
  display metadata and README budget suggestions grant no execution permission. The format
  carries no budget; research `constraints` is part of the request, not a budget. The manifest row
  names the kind, with its bounds unchanged. The text names every manifest pin and fixture
  list, the verifier's dialect byte bound, upgrade keys matched to the same entry's earlier
  releases fetched by CI, RFC 0018's full unbound classification and the reader-locator grammar.
  Replay, tag, withdrawal and review checks belong to consumer tests; the producer may require
  tags on `main`, while the consumer checks no ancestry. Catalog implementation belongs to
  judgment-pack-exchange#8. Core, the dialect, RFC 0020 and the conformance corpora are unchanged.
  Pull request #178 also follows RFC 0018's amendments in §1's gateway shapes, Evidence's reader
  status, Implementation item 4's seeds and Compatibility's Accepted status at draft maturity,
  resolves question 8 and updates questions 3 and 7.
  Its nineteen accepted review dispositions name the catalog's and consumer's own form checkers
  for RFC 0018 §§2–8 and 12 as round 8 amends them, for both entry kinds even when replay skips;
  close presets to version 3, unbound eligible sources, three files and no profile requirements;
  state mutual refusal of version-1 and version-2 entries and non-empty manifests; gate research
  publication on #176 and workflow use on RFC 0020's condition (#177); assign the Desk's preset
  duties and coordinator handoff; and clarify budgets, synthetic research fixtures, review
  claims, locators, the index and revision attribution to pull requests #150, #163 and #178.

- [RFC 0020](rfcs/0020-workflow.md) (Draft) and `spec/workflow.md` are amended for issue #174
  (2026-10-15, round 2): research-stage admission is conditional on pinning its release form and
  encoding when a Runner prepares the kind (judgment-pack-runner#88); until then no research
  stage can be frozen or verified. Binding names generated AI and any web profiles under the
  dialect §4.4. Check 1 checks every frozen stage's research profiles and generated-only target
  admissions, with or without a preparation; profile findings map to the workflow's existing
  codes. Question 2 is resolved. The two-stage operation acceptance demonstration remains due;
  an additional research recording follows RFC 0018 §11's fixture 8 plan in the workflow bundle
  layout, once a Runner prepares the kind and the dialect's readers read the contract
  (judgment-pack-spec#176). The contrary dialect admission statement is superseded pending
  judgment-pack-spec#179. Workflow version 1's document form gains no member, and replay still
  checks retained bytes without a model or web call. The companion stays equal to the RFC's
  Specification; no workflow fixture or conformance claim is added.
- [RFC 0018](rfcs/0018-dialect.md) and [the dialect](spec/dialect.md) are amended for issue #171
  (2026-10-15, round 8): research declares bounded typed fields and records found, not-found,
  stale and conflicting answers with retained-response citations. Published recipes name model
  and capability requirements; binding assigns generated AI and web profiles by id and digest,
  with mismatches refused. Reconciliation is a declared rule over research results, retaining
  the prohibition of overlapping targets. The GTM company/person and work-item triage fixture
  lists include changed bindings, retained responses and the workflow's selected parent/child
  case; none is recorded because no Runner prepares `research`. Replay never calls a model or
  the web, and establishes retained bytes, not answer correctness. `evidence` keeps its accepted
  form, an array of non-empty strings. Three accepted answers change: a research source of pull
  request 164's form without `fields` or `capabilities` is now `input-malformed`; a research record
  without `fields` is now `input-malformed`; a retained response through a trusted but unassigned
  profile now gives `profile-mismatch`. This resolves the dialect's research binding question
  deferred by issue #160. Workflow version 1 admits no stage with a research source; RFC 0020's
  contrary binding statements are superseded pending its own revision, with its operation
  construction still due. At that amendment both readers held the superseded research form;
  they read the contract since the entry above. Round 8's twelve accepted findings clarify reads,
  reconciliation guards, citation indices, generated claims and fixture variants; its review and
  dispositions are
  [recorded verbatim][round-8]. No Core, preparation-form or conformance
  change is made, and no vector is claimed.

[round-8]:
  https://github.com/Judgment-Pack/judgment-pack-spec/blob/main/rfcs/reviews/0018-round-8.md

- [RFC 0018](rfcs/0018-dialect.md) is amended (2026-10-15), and
  [`spec/dialect.md`](spec/dialect.md) with it; its status stays `Accepted`. Version 2's
  `operation` reads a gateway source of shape `airbyte`, `mcp` or `http`, as the reference Runner's
  mapping v2 does since its pull request 80: the record's `acquisition.shape` is the profile's; the
  request is a tool call for `mcp`, and for `http` and `airbyte` the request the gateway source of
  that shape takes, held to being an object, to the template rules and to the receipt's commitment,
  not to a set of members (`airbyte` defined and not claimable); and a receipt that attests a page
  is refused whatever the shape. This changes accepted text in two ways: a compatible extension of
  the record kind to every adapter shape, under which every version-2 dialect that was well-formed
  stays so and the nine vectors keep their answers; and one restriction, the refusal of a paged
  acquisition, which changes one answer the accepted text gave: a signed `mcp` acquisition whose
  receipt carried `pageItems` was read and is refused now. The Runner has never prepared one. Version 3 gains the unbound source form, an `operation` that names the catalog platform
  and operation it is read through in place of a profile, with a binding document and the bound
  dialect it yields; it is defined and not claimable, since, at that amendment, no Runner read
  version 3 (the Runner reads it since its pull request 83: see the entry of the eleventh and
  twelfth vectors above). A verifier
  that does not read a dialect's version refuses it, `version-unread`. The Runner's tenth
  preparation vector, `http-shaped-source`, is staged byte for byte beside the nine, and both
  readers, `tools/dialect_verify.py` and `tools/dialect-verify-ts/`, read it to the Runner's answer;
  their extensions are one author's, so for the amendment their agreement is not independent.
- Implementations page and presentation: they say what the runtime and Runner now establish about
  a decision record, as runtime conventions and in the runtime's own wording. The runtime's listing
  names chaining on by default, record signatures in a sidecar with key rotation, checkpoints a
  holder keeps and `jpack audit verify` against them, and RFC 3161 stamps (runtime v0.26.0), and
  v0.27.0's refusal of a signing key another user could replace, with a link to the runtime guide's
  "Checking a trail, and handing over a checkpoint". The Runner's listing names its chain of runs
  and signatures, checked by `verify-run` (v0.5.0), and the gateway's a decision policy that
  requires a signed record (v0.9.0, its ADR-0012). The gateway's top line said "not integrated with
  the runtime"; it now says the gateway runs its sources and receipts them apart from the runtime,
  and that such a policy can hold a write to a record a runtime key it trusts signed. The
  presentation labels its receipt sentences as the gateway's receipt store, unchanged, and gains a
  section on the decision record in runtime ADR-0047's terms: a chain establishes consistency, not
  completeness; a signature, nothing against the key holder; a held checkpoint, existence at
  hand-over if the holder is independent; a stamp, existence by a time, not when a record was made.
  None of this is in JPS, and nothing normative changes.
- The six published demo projects now pass `jpack packs lint`, the check the runtime offers for a
  project's producers. Each demo's `jpack.json` declares, for every fact pointer its pack reads and
  every evidence requirement it declares, the source in the demo's own `mapping/mapping.json` that
  supplies it; these are the runtime's non-normative hints and no pack changes. Each README adds the
  lint to its commands and says what it checks. The demos keep their versions, and their published
  archives change in `jpack.json` and `README.md` only; each demo's manifest records the new digests,
  and the deal demo's archive pin moves with them. Nothing normative changes.
- [RFC 0002](rfcs/0002-judgment-graph.md) (Judgment Graph composition) is amended; it stays a
  `Draft`. The question Study 004 left prior to the others — which seam the format is for — is
  decided: the **dataflow seam**, one decision's outcome consumed as another's input, and the edge
  is not grown toward effect or entitlement constructs. The use intended for it, the seam between
  decisions different parties own, is stated as intended and unmeasured. The one implementation is
  described as it stands: eight graph-specific runtime decision records, first released across four
  versions, with the graph test verb in a fifth, where the RFC named one. Four statements of the
  sketch are corrected or marked as diverging from that implementation — it names a pack by a
  project-local decision id and not by `(id, version)`, pins nothing about a pack in the document,
  and carries one switch, `onUnresolved`, whose meaning is evaluator behavior — and each
  divergence is recorded as a question for the RFC and not settled by adopting either side. Four
  unresolved questions are added: how a node names and pins its pack; whether an upstream verdict
  is co-evaluated or consumed as recorded; whether a per-edge evaluator switch belongs in a
  portable format; and whether a test format is part of the interchange.
- [RFC 0004](rfcs/0004-planner-interface.md) (planner interface) is dispositioned `Rejected`: a
  planner is product, and the specification standardizes no part of one, the narrow selection query
  included. The RFC named this its most likely outcome when it was opened. The record states what the
  rejection rests on — the maintainer knows of no pair of products that has asked for the surface,
  and the reference runtime deliberately leaves selection with the application — and what it leaves
  undecided, including whether a selection query could be portable at all. Nothing normative
  changes; the index, the architecture vision, the FAQ, the site descriptions and
  [RFC 0006](rfcs/0006-evaluator-conformance.md)'s adoption record, which had assigned a question
  to RFC 0004, follow.
- Search metadata descriptions are normalized to 160 characters, conformance-case descriptions now
  name JPS and their layer, and sitemap entries no longer misreport the deployment timestamp as every
  page's content-modification time. Duplicate downloadable JSON under `/artifacts/` now carries an
  `X-Robots-Tag: noindex` response while canonical schema URLs remain available. The deployment guide
  also forbids cloning the intentionally `noindex` preview artifact to live and requires an explicit
  production build plus indexing checks.
- [RFC 0014](rfcs/0014-lineage-record-and-action-binding.md) (the lineage record and the action
  binding) is `Accepted` — the first accepted cross-project record, and a retrospective one.
  Acceptance endorses the record as an account of a design the gateway and the runtime had already
  adopted by their own processes; it confers no authority over them, makes nothing part of JPS, and
  claims no stability. The record's own process question — whether
  [RFC 0000's](rfcs/0000-rfc-process.md) cross-project provision covers a record filed after its
  parts were built — is ruled on, and RFC 0000 now says that it does and on what conditions. Four
  developments since the record was filed on 2026-09-14 are recorded in place. One overtook a
  statement and that statement is struck: the golden-record agreement test, called unbuilt, is
  built for one platform. One stands beside statements that remain true: a second verifier of
  receipt version 3 exists and is neither independent nor clean-room. Two update statements marked
  "at the time of writing": runtime 0.21.0 is released, and the demo's Acts 7 and 8 are merged. The
  descriptions of this directory no longer call it open proposals only.
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
- The site now renders `~~struck~~` text as a deletion, as GitHub does. The RFCs correct themselves
  in place — a superseded sentence is struck and a dated note follows it — and the site's renderer
  had no strikethrough, so on five published RFC pages a withdrawn claim appeared unstruck, wrapped
  in literal tildes. A test holds that every strike in an RFC's source is a `<del>` on its page.
- Field guide: a rule's `evidenceRequirementRefs` is now described as what it is, a citation that
  no evaluation step reads. The guide said the rule "relies on" the requirements it names, which
  reads as a gate. It now names the two mechanisms that do gate on evidence: a requirement declared
  `required: true`, and an `evidence-present` condition. Nothing normative changes.
- Field guide: says that an outcome named for human review, such as `manual-review`, is an ordinary
  outcome result that requests no handoff, and that the escalation target is requested only by an
  unresolved or not-applicable result whose reason the triggers name, or by an `escalate` exception.
  Four of the five example packs use such an outcome as their `fallbackOutcome`. Nothing normative
  changes.
- README and Implementations page: the project's desk and jobs runner are listed with the other
  companion projects, as separately governed, non-normative research previews. Neither evaluates a
  pack itself, so neither is listed as an implementation.

[staged-dialect]: https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/conformance/dialect

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

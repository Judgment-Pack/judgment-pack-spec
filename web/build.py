#!/usr/bin/env python3
"""Build the JPS documentation site as portable static files."""

from __future__ import annotations

import argparse
import html
import json
import hashlib
import posixpath
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from string import Template
from urllib.parse import urlsplit, urlunsplit

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "web"
DEFAULT_OUTPUT = ROOT / "public"
TEMPLATE = Template((WEB_ROOT / "templates" / "page.html").read_text(encoding="utf-8"))
SITE_VERSION = "0.2.0-draft"
TAGGED_SOURCE_REF = "v0.2.0-draft"
GITHUB_BLOB_ROOT = "https://github.com/Judgment-Pack/judgment-pack-spec/blob/"
GITHUB_ROOT = GITHUB_BLOB_ROOT + TAGGED_SOURCE_REF + "/"
GITHUB_URL = "https://github.com/Judgment-Pack/judgment-pack-spec"
SLACK_URL = "https://join.slack.com/t/judgment-pack/shared_invite/zt-44qrd47ok-o_~Vk3BFDzsN~EGAPkeQBw"
# Recognizable, monochrome inline marks (currentColor) — no external icon dependency.
GITHUB_ICON_SVG = (
    '<svg class="nav-icon-svg" viewBox="0 0 16 16" width="18" height="18" '
    'aria-hidden="true" focusable="false" fill="currentColor">'
    '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 '
    '0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53'
    '.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 '
    '0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 '
    '1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 '
    '3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 '
    '16 8c0-4.42-3.58-8-8-8z"/></svg>'
)
SLACK_ICON_SVG = (
    '<svg class="nav-icon-svg" viewBox="0 0 24 24" width="18" height="18" '
    'aria-hidden="true" focusable="false" fill="currentColor">'
    '<path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 '
    '2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A'
    '2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521'
    '-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 '
    '0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 '
    '2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 '
    '2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1'
    '-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a'
    '2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52z'
    'M15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 '
    '15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/></svg>'
)
OUTPUT_MARKER = ".generated-by-jps-site-build"
GENERATOR_ID = "jps-site-build"
# Content hash of the stylesheet, appended as ?v= so a rebuilt CSS always defeats browser cache.
STYLES_HASH = hashlib.sha256((WEB_ROOT / "static" / "styles.css").read_bytes()).hexdigest()[:8]
_SHA_RE = re.compile(r"\A[0-9a-f]{7,40}\Z")


@dataclass(frozen=True)
class BuildConfig:
    """Build-wide settings that make a deployed page traceable and preview-safe."""

    environment: str
    base_url: str
    commit_sha: str
    build_time: str
    written: list[PurePosixPath] = field(default_factory=list)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def default_noindex(self) -> bool:
        # Preview builds are noindex everywhere; production indexes by default.
        return not self.is_production

    @property
    def short_sha(self) -> str:
        return self.commit_sha[:12] if self.commit_sha else "dev"


_CONFIG: BuildConfig | None = None


def active_config() -> BuildConfig:
    if _CONFIG is None:
        raise RuntimeError("BuildConfig is not initialized; run build() via the CLI entrypoint")
    return _CONFIG


@dataclass(frozen=True)
class Page:
    source: str
    output: PurePosixPath
    title: str
    description: str
    section: str
    artifact_label: str = "Informative"
    source_ref: str = TAGGED_SOURCE_REF


@dataclass(frozen=True)
class ExampleGuide:
    focus: str
    demonstrates: str
    good_for: tuple[str, ...]
    edges: tuple[str, ...]
    failure_paths: tuple[str, ...]


EXAMPLE_GUIDES = {
    "minimal-expense-approval.json": ExampleGuide(
        focus="Cross-feature authoring and local-reference tracing.",
        demonstrates=(
            "A fuller JPS document with applicability, two evidence requirements, a cited source, "
            "three outcomes and rules, an exception, a fallback, and explicit escalation metadata."
        ),
        good_for=(
            "Tracing outcome, evidence, and source IDs from declarations to every local reference.",
            "Inspecting nested all/not conditions and the boundary between schema checks and semantic checks.",
            "Reviewing how one synthetic pack records applicability, exceptions, fallback, and human-handoff configuration.",
        ),
        edges=(
            "The declared amount split includes 5000 in the less-than-or-equal branch and values above 5000 in the review branch. Ordered decimal comparison is defined for the evaluator conformance class only, and this page is not a corpus row, so nothing here asserts a portable result.",
            "Under the §§7–8 resolution model, an active-investigation forced outcome bypasses normal rules. Separately, a prohibited category plus an amount above 5000 can produce conflicting normal-rule candidates, which resolve to an unresolved disposition carrying the conflict reason. Both behaviors are specified for an implementation claiming evaluator conformance; this page is not a corpus row, so nothing here is the corpus expectation for either.",
            "If activeInvestigation is absent, its exception is unknown and declares escalation under the §§7–8 resolution model. Missing required evidence also requests handoff, while a non-employee-expense value is not applicable.",
            "If resolution otherwise completes with no matching rule, the declared manual-review fallback applies. The listed no-match escalation trigger is unreachable under the §8 algorithm while that fallback exists.",
        ),
        failure_paths=(
            "In a scratch copy, remove an outcome or evidence declaration while leaving a reference to it; the document can retain a valid JSON shape but must fail semantic document conformance.",
            "Add an unknown root member to produce a structural failure, or duplicate a JSON member to produce a carrier failure before schema validation.",
            "Never treat an illustrative approve, reject, or review label as authorization to process a real expense.",
        ),
    ),
    "software-change-review.json": ExampleGuide(
        focus="Schema-versus-semantics exercises in a harmless training scenario.",
        demonstrates=(
            "A deliberately non-operational training-demo pack with two required evidence items, "
            "simple exact-match rules, a compound evidence condition, and a human-review fallback."
        ),
        good_for=(
            "Following the scratch-edit exercises in Test the preview.",
            "Contrasting structural JSON Schema validation with semantic local-reference validation.",
            "Checking how multiple evidence requirements are declared and referenced by one rule.",
        ),
        edges=(
            "Only the fictional training-demo environment is applicable; any other environment is outside the example's declared scope.",
            "With required evidence present, a known pending status matches neither rule; the §§7–8 resolution model selects the human-review fallback.",
            "A missing status or required evidence instead produces an unresolved reason and may request the configured handoff; it does not select the fallback.",
            "Ready for demo is only a display label. It is never deployment approval."
        ),
        failure_paths=(
            "Add an unexpected root member in a scratch copy to see a structural failure.",
            "Change a rule outcome to missing-outcome: the local ID can pass the schema while the dangling reference fails semantic document conformance.",
            "Do not substitute a production change, real test report, credential, or internal locator for the invented training data.",
        ),
    ),
    "records-disposition-review.json": ExampleGuide(
        focus="A sensitive-domain-shaped example with an explicitly harmless boundary.",
        demonstrates=(
            "A second unrelated domain using applicability, exact-match rules, one evidence item, "
            "one cited source, and a human-review fallback without offering legal or records guidance."
        ),
        good_for=(
            "Checking that the same JPS document shape remains understandable outside software and expense examples.",
            "Tracing evidence and source references through two mutually exclusive illustrative status rules.",
            "Reviewing whether safety boundaries remain visible in a domain where labels could otherwise be mistaken for authority.",
        ),
        edges=(
            "Only context=training-fixture is applicable, and active and retired are mutually exclusive exact labels in the invented data.",
            "With required evidence present, another known status or category matches no rule; the §§7–8 resolution model selects the human-review fallback.",
            "A missing field or inventory note instead produces an unresolved reason and may request the configured handoff; it does not select the fallback.",
            "The example.invalid source locator is inert, and ordinary validation must not fetch it unless explicitly requested.",
        ),
        failure_paths=(
            "Remove the inventory-note declaration while retaining a reference to produce a semantic document failure.",
            "Give a source an invalid date or URI to produce a structural format failure when format assertion is enabled.",
            "Remove demo copy is only a display label: it never deletes, retains, or authorizes disposition of any real record.",
        ),
    ),
    "supplier-invoice-approval.json": ExampleGuide(
        focus="A business approve / manual-review / escalate / reject decision gated on evidence.",
        demonstrates=(
            "A synthetic accounts-payable pack with applicability, three required evidence items, a cited "
            "source, four outcomes, exact-match and compound rules, a suspected-duplicate exception, a "
            "manual-review fallback, and explicit escalation."
        ),
        good_for=(
            "Seeing how required evidence, a variance threshold, and a restricted-supplier check combine into one automatic-approval decision.",
            "Tracing every outcome, evidence, and source id from its declaration to each local reference.",
            "Contrasting the automatic approve path with the manual-review, escalate, and reject paths in one document.",
        ),
        edges=(
            "Only context=training-fixture is applicable; any other context is outside the example's declared scope.",
            "A restricted supplier rejects and a variance above the declared tolerance escalates; both outrank the automatic path under the §§7–8 resolution model.",
            "With all required evidence present, an in-tolerance invoice from a non-restricted supplier follows the automatic approve path.",
            "A suspected-duplicate flag forces manual review; missing required evidence instead requests the configured handoff.",
        ),
        failure_paths=(
            "In a scratch copy, remove the goods-receipt evidence declaration while keeping a reference to it; the document keeps a valid JSON shape but must fail semantic document conformance.",
            "Point fallbackOutcome at an undeclared outcome id to produce a dangling-reference semantic failure.",
            "Approve, escalate, and reject are only display labels; never treat them as authorization to pay, hold, or refuse a real invoice.",
        ),
    ),
    "data-request-intake-triage.json": ExampleGuide(
        focus="A three-way triage decision over summarized assessment facts.",
        demonstrates=(
            "A synthetic data-governance intake pack that routes a data request to proceed, "
            "clarify/return, or decline/redirect using summarized completeness and appropriateness "
            "facts, two required evidence items, a cited source, a forced-outcome exception, a "
            "clarify fallback, and explicit escalation."
        ),
        good_for=(
            "Modeling a triage decision whose inputs are themselves the verdicts of an upstream review process.",
            "Tracing a forced-outcome exception that overrides every normal rule under the §§7–8 resolution model.",
            "Contrasting fix-with-more-information outcomes (clarify/return) with fail-permanently outcomes (decline/redirect).",
        ),
        edges=(
            "Only the six declared request types are applicable; any other request type is outside the example's declared scope.",
            "An incomplete submission that also carries a hard appropriateness failure matches both the clarify rule and the decline rule, producing conflicting normal-rule candidates under the §§7–8 resolution model. In this draft that is a portable result for an implementation claiming evaluator conformance: an unresolved disposition carrying the conflict reason, never a tie-broken outcome.",
            "Under the §§7–8 resolution model, the embargoed-information forced outcome bypasses normal rules entirely; a missing embargo fact makes the exception unknown, and its onUnknown declares escalation.",
            "If resolution otherwise completes with no matching rule, the declared clarify-return fallback applies. The listed no-match escalation trigger is unreachable under the §8 algorithm while that fallback exists.",
        ),
        failure_paths=(
            "In a scratch copy, remove the decline-redirect outcome while leaving the exception that references it; the document keeps a valid JSON shape but must fail semantic document conformance.",
            "Point a rule's evidenceRequirementRefs at an undeclared evidence id to produce a dangling-reference semantic failure.",
            "Proceed, clarify, and decline are only display labels; never treat them as authorization to accept, return, or refuse a real data request.",
        ),
    ),
}


PAGES = (
    Page(
        "README.md",
        PurePosixPath("index.html"),
        "Judgment Pack Specification",
        "Judgment Pack is an open specification for representing, testing, and exchanging the evidence, rules, exceptions, uncertainty, escalation criteria, and evaluations behind AI decisions.",
        "overview",
        source_ref="main",
    ),
    Page(
        "docs/why.md",
        PurePosixPath("why/index.html"),
        "Why Judgment Pack?",
        "Why executable, testable judgment is the missing layer for reliable business agents — and how a Judgment Pack provides it.",
        "why",
        source_ref="main",
    ),
    Page(
        "spec/judgment-pack-core.md",
        PurePosixPath("spec/0.2.0-draft/index.html"),
        "JPS Core 0.2.0-draft",
        "The normative prose for JPS carrier, structural, and semantic document conformance and for the evaluator conformance class.",
        "spec",
        "Normative prose",
    ),
    Page(
        "docs/field-guide.md",
        PurePosixPath("field-guide/index.html"),
        "Field guide",
        "An informative, plain-language walkthrough of every part of a Judgment Pack document.",
        "field-guide",
        "Informative guide",
        source_ref="main",
    ),
    Page(
        "TESTING.md",
        PurePosixPath("testing/index.html"),
        "Test the research preview",
        "A short, synthetic exercise for testing JPS documents and reporting reproducible feedback.",
        "testing",
    ),
    Page(
        "GOVERNANCE.md",
        PurePosixPath("project/governance/index.html"),
        "Governance",
        "How the open, vendor-neutral specification is governed and how to participate.",
        "governance",
    ),
    Page(
        "ROADMAP.md",
        PurePosixPath("project/roadmap/index.html"),
        "Evidence-gated roadmap",
        "The evidence required before JPS can advance beyond a research preview.",
        "project",
    ),
    Page(
        "VERSIONING.md",
        PurePosixPath("project/versioning/index.html"),
        "Versioning and release policy",
        "Specification, pack, artifact, and compatibility versioning rules.",
        "project",
    ),
    Page(
        "CHANGELOG.md",
        PurePosixPath("project/changelog/index.html"),
        "Changelog",
        "The draft and published history of the JPS research preview.",
        "project",
    ),
    Page(
        "CONTRIBUTING.md",
        PurePosixPath("project/contributing/index.html"),
        "Contributing",
        "How to test, discuss, and propose changes to JPS.",
        "project",
    ),
    Page(
        "SECURITY.md",
        PurePosixPath("project/security/index.html"),
        "Security policy",
        "The research-preview security boundary and vulnerability reporting process.",
        "project",
    ),
    Page(
        "CODE_OF_CONDUCT.md",
        PurePosixPath("project/code-of-conduct/index.html"),
        "Code of conduct",
        "Expected conduct for participation in the JPS project.",
        "project",
    ),
    Page(
        "docs/design-principles.md",
        PurePosixPath("project/design-principles/index.html"),
        "Design principles",
        "The constraints that shape the JPS research proposal.",
        "project",
    ),
    Page(
        "docs/non-goals.md",
        PurePosixPath("project/non-goals/index.html"),
        "Non-goals",
        "Explicit boundaries on what JPS does and does not standardize.",
        "project",
    ),
    Page(
        "docs/origin-and-boundary.md",
        PurePosixPath("project/origin-and-boundary/index.html"),
        "Origin and scope",
        "How the specification is developed independently of any single implementation.",
        "project",
        source_ref="main",
    ),
    Page(
        "docs/tooling-architecture.md",
        PurePosixPath("project/tooling/index.html"),
        "Specification and implementation boundary",
        "Why the specification stays independent of any particular tool or implementation.",
        "project",
        source_ref="main",
    ),
    Page(
        "FAQ.md",
        PurePosixPath("faq/index.html"),
        "FAQ",
        "Answers to common and hard architectural questions about the Judgment Pack Specification.",
        "faq",
        source_ref="main",
    ),
    Page(
        "docs/architecture/vision.md",
        PurePosixPath("architecture/vision/index.html"),
        "Architecture vision (non-normative)",
        "A non-normative picture of the layered architecture, labeling each part as shipped, proposed, runtime, or product.",
        "concepts",
        "Non-normative",
        source_ref="main",
    ),
    Page(
        "docs/concepts/comparison.md",
        PurePosixPath("concepts/comparison/index.html"),
        "How Judgment Pack compares",
        "How JPS relates to DMN, policy engines, rule engines, BPMN, knowledge graphs, and LLM evaluation.",
        "concepts",
        source_ref="main",
    ),
    Page(
        "rfcs/README.md",
        PurePosixPath("rfcs/index.html"),
        "Proposals (RFCs)",
        "Open Requests for Comments — design proposals that are not part of the specification.",
        "proposals",
        "Non-normative",
        source_ref="main",
    ),
    Page(
        "rfcs/0000-rfc-process.md",
        PurePosixPath("rfcs/0000-rfc-process/index.html"),
        "Request for Comments (RFC) process",
        "The process for proposing material changes to JPS.",
        "proposals",
        source_ref="main",
    ),
    Page(
        "rfcs/0001-pack-manifest.md",
        PurePosixPath("rfcs/0001-pack-manifest/index.html"),
        "RFC 0001: Pack manifest",
        "Draft proposal for an optional manifest describing a pack from the outside.",
        "proposals",
        "Draft proposal",
        source_ref="main",
    ),
    Page(
        "rfcs/0002-judgment-graph.md",
        PurePosixPath("rfcs/0002-judgment-graph/index.html"),
        "RFC 0002: Judgment Graph composition",
        "Draft proposal for a portable format that composes several packs into a decision graph.",
        "proposals",
        "Draft proposal",
        source_ref="main",
    ),
    Page(
        "rfcs/0003-evidence-reference.md",
        PurePosixPath("rfcs/0003-evidence-reference/index.html"),
        "RFC 0003: Evidence reference",
        "Draft proposal for how a pack names the evidence it needs so runtimes can bind it to sources.",
        "proposals",
        "Draft proposal",
        source_ref="main",
    ),
    Page(
        "rfcs/0004-planner-interface.md",
        PurePosixPath("rfcs/0004-planner-interface/index.html"),
        "RFC 0004: Planner interface",
        "Exploratory proposal testing whether any of a pack-selecting planner is standardizable.",
        "proposals",
        "Draft proposal",
        source_ref="main",
    ),
    Page(
        "rfcs/0005-pack-discovery.md",
        PurePosixPath("rfcs/0005-pack-discovery/index.html"),
        "RFC 0005: Pack discovery",
        "Draft proposal for a portable index format for finding and selecting packs across catalogs.",
        "proposals",
        "Draft proposal",
        source_ref="main",
    ),
    Page(
        "rfcs/0007-determination-boundary.md",
        PurePosixPath("rfcs/0007-determination-boundary/index.html"),
        "RFC 0007: The determination boundary",
        "Draft proposal: the specification draws its boundary at computation, but the boundary that appears in use is determination — and part of the judgment leaves the pack.",
        "proposals",
        "Draft proposal",
        source_ref="main",
    ),
    Page(
        "rfcs/0009-interim-review-regime.md",
        PurePosixPath("rfcs/0009-interim-review-regime/index.html"),
        "RFC 0009: The interim review regime",
        "Accepted process RFC: what stands in for outside review while the project has one maintainer, what the public record cannot prove, and the criteria that permit removing the regime.",
        "proposals",
        "Accepted process RFC",
        source_ref="main",
    ),
    Page(
        "rfcs/0006-evaluator-conformance.md",
        PurePosixPath("rfcs/0006-evaluator-conformance/index.html"),
        "RFC 0006: Evaluator conformance",
        "Accepted standards-track RFC: the design record for the evaluator conformance class, portable disposition, error contract, and evaluation corpus that landed in Core 0.2.0-draft.",
        "proposals",
        "Accepted standards-track RFC",
        source_ref="main",
    ),
    Page(
        "rfcs/0008-bounded-collection-quantifiers.md",
        PurePosixPath("rfcs/0008-bounded-collection-quantifiers/index.html"),
        "RFC 0008: Bounded collection quantifiers",
        "Draft proposal for existential and universal conditions over an array-valued fact, and an honest count of how few measured cases they reach.",
        "proposals",
        "Draft proposal",
        source_ref="main",
    ),
    Page(
        "releases/v0.2.0-draft.md",
        PurePosixPath("project/releases/0.2.0-draft/index.html"),
        "0.2.0-draft release notes",
        "Scope, artifacts, the independence caveat, limitations, and testing guidance for the draft that adds the evaluator conformance class.",
        "project",
    ),
    Page(
        "releases/v0.1.0-draft.md",
        PurePosixPath("project/releases/0.1.0-draft/index.html"),
        "0.1.0-draft release notes",
        "Scope, artifacts, limitations, and testing guidance for the first draft release.",
        "project",
        source_ref="v0.1.0-draft",
    ),
    Page(
        "conformance/evaluation/README.md",
        PurePosixPath("conformance/evaluation/index.html"),
        "Evaluation corpus",
        "The seed evaluation corpus and its case carrier — normative for the evaluator conformance class and for nothing else.",
        "conformance",
        "Normative for the evaluator class",
    ),
    Page(
        "conformance/evaluation/errata.md",
        PurePosixPath("conformance/evaluation/errata/index.html"),
        "Evaluation corpus errata",
        "The project's record of defective rows in a released evaluation corpus — the only thing that can excuse a failing row from an evaluator-conformance claim.",
        "conformance",
        "Normative for the evaluator class",
        # Errata postdate the release they apply to, so this page tracks the branch, not the tag.
        source_ref="main",
    ),
    Page(
        "web/DEPLOYMENT.md",
        PurePosixPath("project/deployment/index.html"),
        "Static site deployment",
        "How to build, preview, and later publish the provider-neutral static site.",
        "project",
    ),
    Page(
        ".github/ISSUE_TEMPLATE/testing-feedback.md",
        PurePosixPath("project/testing-feedback/index.html"),
        "Testing feedback template",
        "The information needed for safe, reproducible JPS testing feedback.",
        "project",
    ),
)


NAVIGATION = (
    ("overview", "Overview", PurePosixPath("index.html")),
    ("why", "Why", PurePosixPath("why/index.html")),
    ("spec", "Spec", PurePosixPath("spec/0.2.0-draft/index.html")),
    ("examples", "Examples", PurePosixPath("examples/index.html")),
    ("conformance", "Conformance", PurePosixPath("conformance/index.html")),
    ("faq", "FAQ", PurePosixPath("faq/index.html")),
    ("implementations", "Implementations", PurePosixPath("implementations/index.html")),
    ("proposals", "Proposals", PurePosixPath("rfcs/index.html")),
    ("governance", "Governance", PurePosixPath("project/governance/index.html")),
)


# Sections that own an index page. A page in one of these sections gets a breadcrumb
# "Home / <section> / <page>" so its parent index is always one click up; other sections
# render "Home / <page>". Keyed by the `section` field on Page / page_html().
SECTION_INDEX = {
    "examples": ("Examples", PurePosixPath("examples/index.html")),
    "conformance": ("Conformance", PurePosixPath("conformance/index.html")),
    "proposals": ("Proposals", PurePosixPath("rfcs/index.html")),
    "concepts": ("Concepts", PurePosixPath("concepts/index.html")),
    "project": ("Project & docs", PurePosixPath("project/index.html")),
    "implementations": ("Implementations", PurePosixPath("implementations/index.html")),
}


def output_href(current: PurePosixPath, target: PurePosixPath) -> str:
    """Return a portable relative URL from one output file to another."""
    start = current.parent.as_posix() or "."
    if target.name == "index.html":
        destination = target.parent.as_posix() or "."
        relative = posixpath.relpath(destination, start=start)
        return "./" if relative == "." else f"{relative.rstrip('/')}/"
    return posixpath.relpath(target.as_posix(), start=start)


def absolute_url(base_url: str, output: PurePosixPath) -> str:
    """Absolute, cleanUrls-correct URL for an output file.

    ``base_url`` must already be trailing-slash-free. Directory index pages collapse to a
    trailing-slash URL to match ``firebase.json`` ``cleanUrls`` and ``output_href``; the join is
    unconditionally single-slash so a root or nested path can never produce ``//``.
    """
    path = output.as_posix()
    if path == "index.html" or path.endswith("/index.html"):
        directory = path[: -len("index.html")]  # "" at root, "spec/0.1.0-draft/" nested
        return f"{base_url}/{directory}"
    if path.endswith(".html"):
        path = path[: -len(".html")]
    return f"{base_url}/{path}"


class LocalLinkRewriter(Treeprocessor):
    def __init__(
        self,
        md: markdown.Markdown,
        source: str,
        output: PurePosixPath,
        routes: dict[str, PurePosixPath | str],
    ) -> None:
        super().__init__(md)
        self.source = PurePosixPath(source)
        self.output = output
        self.routes = routes

    def rewrite(self, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
            return value
        target = posixpath.normpath(
            posixpath.join(self.source.parent.as_posix(), parsed.path)
        )
        route = self.routes.get(target)
        if route is None:
            return value
        if isinstance(route, str):
            return route
        path = output_href(self.output, route)
        return urlunsplit(("", "", path, parsed.query, parsed.fragment))

    def run(self, root):  # type: ignore[no-untyped-def]
        for element in root.iter():
            attribute = "href" if element.tag == "a" else "src" if element.tag == "img" else None
            if attribute and element.get(attribute):
                element.set(attribute, self.rewrite(element.get(attribute, "")))
        return root


class LinkRewriteExtension(Extension):
    def __init__(
        self,
        source: str,
        output: PurePosixPath,
        routes: dict[str, PurePosixPath | str],
    ) -> None:
        self.source = source
        self.output = output
        self.routes = routes
        super().__init__()

    def extendMarkdown(self, md: markdown.Markdown) -> None:  # noqa: N802
        md.treeprocessors.register(
            LocalLinkRewriter(md, self.source, self.output, self.routes),
            "jps-local-links",
            4,
        )


def strip_front_matter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    return text[end + 5 :] if end >= 0 else text


def home_body(text: str) -> str:
    """Return the shared overview content for the site homepage, dropping repository-only
    chrome (title, badges, status callout, and the README hero/diagram) that the site
    replaces with its own hero. A ``<!-- site-overview -->`` marker delimits the shared
    content; everything above it is GitHub-README-only. Falls back to stripping the leading
    title, one badge line, and the status blockquote when the marker is absent."""
    marker = "<!-- site-overview -->"
    index = text.find(marker)
    if index >= 0:
        return text[index + len(marker) :].lstrip("\n")
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].startswith("[!["):
        lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].startswith(">"):
        while lines and (lines[0].startswith(">") or not lines[0].strip()):
            lines.pop(0)
    return "\n".join(lines)


def render_markdown(
    text: str,
    source: str,
    output: PurePosixPath,
    routes: dict[str, PurePosixPath | str],
) -> tuple[str, str]:
    renderer = markdown.Markdown(
        extensions=[
            "extra",
            "sane_lists",
            "toc",
            LinkRewriteExtension(source, output, routes),
        ],
        extension_configs={
            "toc": {
                "anchorlink": False,
                "permalink": False,
                "toc_depth": "2-3",
            }
        },
        output_format="html5",
    )
    body = renderer.convert(strip_front_matter(text))
    return body, renderer.toc


def nav_icon_anchor(url: str, label: str, svg: str) -> str:
    """External community icon link: new tab, accessible name, tooltip, keyboard-focusable."""
    return (
        f'<a class="nav-icon" href="{html.escape(url)}" target="_blank" rel="noopener noreferrer" '
        f'aria-label="{html.escape(label, quote=True)}" title="{html.escape(label, quote=True)}">'
        f"{svg}</a>"
    )


def nav_html(current: PurePosixPath, active: str) -> str:
    links = []
    for key, label, target in NAVIGATION:
        current_attr = ""
        if key == active:
            current_attr = (
                ' aria-current="page"'
                if current == target
                else ' aria-current="location"'
            )
        links.append(
            f'<li><a href="{html.escape(output_href(current, target))}"{current_attr}>'
            f"{html.escape(label)}</a></li>"
        )
    text_nav = '<ul class="primary-nav">' + "".join(links) + "</ul>"
    icons = (
        nav_icon_anchor(GITHUB_URL, "View the specification on GitHub", GITHUB_ICON_SVG)
        + nav_icon_anchor(SLACK_URL, "Join the Judgment Pack community", SLACK_ICON_SVG)
    )
    # JS-free responsive nav: a hidden, focusable checkbox toggles the collapsed link
    # list on small screens; the icons and hamburger label stay visible beside it.
    toggle = '<input type="checkbox" id="nav-menu-toggle" class="nav-toggle-input">'
    hamburger = (
        '<label for="nav-menu-toggle" class="nav-toggle">'
        '<span class="nav-toggle-bars" aria-hidden="true"></span>'
        '<span class="visually-hidden">Menu</span></label>'
    )
    actions = f'<div class="nav-actions">{icons}{hamburger}</div>'
    return toggle + text_nav + actions


def footer_html(current: PurePosixPath) -> str:
    internal = (
        ("Presentation", PurePosixPath("presentation/index.html")),
        ("Concepts", PurePosixPath("concepts/index.html")),
        ("Project & docs", PurePosixPath("project/index.html")),
        ("Governance", PurePosixPath("project/governance/index.html")),
        ("Contributing", PurePosixPath("project/contributing/index.html")),
        ("Code of conduct", PurePosixPath("project/code-of-conduct/index.html")),
        ("Apache-2.0", PurePosixPath("project/license/index.html")),
    )
    external = (
        ("GitHub", GITHUB_URL, "View the specification on GitHub"),
        ("Slack", SLACK_URL, "Join the Judgment Pack community"),
    )
    links = [
        f'<a href="{html.escape(output_href(current, target))}">{html.escape(label)}</a>'
        for label, target in internal
    ]
    for label, url, title in external:
        links.append(
            f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer" '
            f'title="{html.escape(title, quote=True)}">{html.escape(label)}</a>'
        )
    config = active_config()
    build_stamp = ""
    if config.commit_sha:
        build_stamp = (
            '<span class="build-stamp">Built from '
            f"<code>{html.escape(config.short_sha)}</code>"
            f" · {html.escape(config.build_time)}</span>"
        )
    return (
        '<span class="footer-tagline">Judgment Pack is an open, vendor-neutral specification for '
        "executable and testable AI judgment.</span>"
        '<span class="footer-links">'
        + " · ".join(links)
        + "</span>"
        + build_stamp
    )


def page_html(
    *,
    output: PurePosixPath,
    title: str,
    description: str,
    section: str,
    artifact_label: str,
    body: str,
    toc: str = "",
    source: str | None = None,
    source_ref: str = TAGGED_SOURCE_REF,
    hero: str = "",
    body_class: str = "",
    base_href: str = "",
    noindex: bool = False,
) -> str:
    config = active_config()
    stylesheet = output_href(output, PurePosixPath("assets/styles.css")) + f"?v={STYLES_HASH}"
    favicon = output_href(output, PurePosixPath("assets/favicon.svg"))
    home = output_href(output, PurePosixPath("index.html"))
    source_link = ""
    if source:
        source_is_tagged = source_ref == TAGGED_SOURCE_REF
        source_label = "View tagged source" if source_is_tagged else "View current source"
        source_title = (
            f"Source from the immutable {TAGGED_SOURCE_REF} tag"
            if source_is_tagged
            else f"Current source from the mutable {source_ref} branch"
        )
        source_link = (
            '<a class="source-link" href="'
            + html.escape(GITHUB_BLOB_ROOT + source_ref + "/" + source)
            + '" title="'
            + html.escape(source_title, quote=True)
            + '">'
            + html.escape(source_label)
            + "</a>"
        )
    toc_panel = ""
    mobile_toc = ""
    if toc and toc.count("<li>") >= 3:
        toc_panel = (
            '<aside class="page-toc"><nav aria-label="On this page">'
            '<p class="toc-title">On this page</p>'
            + toc
            + "</nav></aside>"
        )
        mobile_toc = (
            '<details class="mobile-toc"><summary>On this page</summary>'
            + toc
            + "</details>"
        )
        heading_end = body.find("</h1>")
        if heading_end >= 0:
            insert_at = heading_end + len("</h1>")
            body = body[:insert_at] + mobile_toc + body[insert_at:]
        else:
            body = mobile_toc + body
    base_element = f'<base href="{html.escape(base_href)}">' if base_href else ""

    # Breadcrumb: "Home / <section index> / <this page>" so every page shows its place and its
    # parent index is one click up. Skipped on the homepage and the 404 page.
    breadcrumb = ""
    if output.as_posix() not in {"index.html", "404.html"}:
        crumbs = [f'<a href="{html.escape(home)}">Home</a>']
        section_crumb = SECTION_INDEX.get(section)
        if section_crumb is not None and section_crumb[1] != output:
            crumbs.append(
                f'<a href="{html.escape(output_href(output, section_crumb[1]))}">'
                f"{html.escape(section_crumb[0])}</a>"
            )
        crumbs.append(
            f'<span class="crumb-current" aria-current="page">{html.escape(title)}</span>'
        )
        separator = '<span class="crumb-sep" aria-hidden="true">/</span>'
        breadcrumb = (
            '<nav class="breadcrumb" aria-label="Breadcrumb">'
            + separator.join(crumbs)
            + "</nav>"
        )

    effective_noindex = noindex or config.default_noindex
    canonical_link = ""
    social_meta = ""
    if config.base_url and not effective_noindex:
        location = html.escape(absolute_url(config.base_url, output), quote=True)
        canonical_link = f'<link rel="canonical" href="{location}">'
        social_meta = (
            '<meta property="og:type" content="website">'
            f'<meta property="og:url" content="{location}">'
            f'<meta property="og:title" content="{html.escape(f"{title} — JPS", quote=True)}">'
            f'<meta property="og:description" content="{html.escape(description, quote=True)}">'
        )
    generator_meta = f'<meta name="generator" content="{GENERATOR_ID} {html.escape(SITE_VERSION)}">'

    return TEMPLATE.safe_substitute(
        language="en",
        page_title=html.escape(f"{title} — JPS"),
        description=html.escape(description, quote=True),
        robots_meta=(
            '<meta name="robots" content="noindex, nofollow">' if effective_noindex else ""
        ),
        base_element=base_element,
        canonical_link=canonical_link,
        social_meta=social_meta,
        generator_meta=generator_meta,
        stylesheet=html.escape(stylesheet),
        favicon=html.escape(favicon),
        home=html.escape(home),
        navigation=nav_html(output, section),
        breadcrumb=breadcrumb,
        hero=hero,
        body_class=html.escape(body_class),
        artifact_label=html.escape(artifact_label),
        source_link=source_link,
        content=body,
        toc=toc_panel,
        footer=footer_html(output),
        version=SITE_VERSION,
    )


def write_page(root: Path, output: PurePosixPath, content: str) -> None:
    destination = (root / Path(output.as_posix())).resolve()
    try:
        destination.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"refusing to write outside the site output: {output}") from error
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    if _CONFIG is not None:
        _CONFIG.written.append(output)


def repository_file(relative: str) -> Path:
    candidate = (ROOT / relative).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as error:
        raise ValueError(f"repository path escapes the source tree: {relative}") from error
    if not candidate.is_file():
        raise ValueError(f"repository file does not exist: {relative}")
    return candidate


def raw_block(text: str, language: str = "json") -> str:
    return (
        '<div class="code-frame"><pre tabindex="0"><code class="language-'
        + html.escape(language)
        + '">'
        + html.escape(text)
        + "</code></pre></div>"
    )


# One human-readable definition per JSON key, derived from the normative schema. Each entry is
# (summary, allowed-values-or-None). Powers the clickable-key cards and the schema field reference.
KEY_REFERENCE: dict[str, tuple[str, tuple[str, ...] | None]] = {
    "specVersion": ("The JPS specification version this document targets.", ("0.2.0-draft",)),
    "id": ("A stable identifier. At the top level it is the pack's globally unique URI; inside outcomes, rules, evidence requirements, sources, and exceptions it is a pack-local id (lowercase, hyphenated).", None),
    "version": ("The pack's own semantic version (MAJOR.MINOR.PATCH), separate from specVersion.", None),
    "title": ("A short human-readable name for the pack.", None),
    "description": ("Human-readable prose for the pack, or for a rule, outcome, evidence requirement, or exception.", None),
    "decision": ("The single decision this pack is about, as an intent and a question.", None),
    "intent": ("What the decision is meant to determine, in the author's words.", None),
    "question": ("The specific question the pack answers.", None),
    "applicability": ("An optional condition that delimits when the whole pack applies; if it does not hold, the pack is not applicable.", None),
    "evidenceRequirements": ("The evidence a decision may draw on. Each item is declared once and referenced by id.", None),
    "required": ("Whether an evidence requirement must be present.", ("true", "false")),
    "kind": ("A category. Evidence: document/fact/measurement/attestation. Source locator: uri/repository/path/other. Escalation target: human-role/queue/system.", ("document", "fact", "measurement", "attestation", "uri", "repository", "path", "other", "human-role", "queue", "system")),
    "sources": ("Provenance: the cited references the pack relies on.", None),
    "publisher": ("Who published a source.", None),
    "publishedAt": ("A source's publication date (YYYY-MM-DD).", None),
    "locator": ("Where a source can be found: a kind and a value.", None),
    "value": ("An operand or literal. In a fact condition, the value compared with operator (a decimal string for ordered comparisons, an array for `in`); in a literal condition, a boolean; in a source locator, the locator string.", None),
    "citation": ("The specific location and excerpt within a source.", None),
    "location": ("Where in a source the cited passage appears.", None),
    "excerpt": ("The quoted passage from a source.", None),
    "rights": ("Usage or licensing information for a source.", None),
    "outcomes": ("The possible results of the decision (at least two). Each has an id and a label.", None),
    "label": ("The human-readable name shown for an outcome.", None),
    "rules": ("The decision rules (at least one). Each declares a condition and the outcome it selects.", None),
    "when": ("The condition under which a rule or exception applies.", None),
    "outcome": ("For a rule, the outcome id selected when its condition holds; for a force-outcome exception, the outcome forced.", None),
    "onUnknown": ("How to treat a rule or exception whose condition cannot be evaluated.", ("ignore", "escalate")),
    "evidenceRequirementRefs": ("Evidence requirement ids a rule depends on.", None),
    "sourceRefs": ("Source ids a rule or exception is grounded in.", None),
    "rationale": ("Why a rule exists, recorded for human review.", None),
    "exceptions": ("Overrides that change the ordinary outcome under specific conditions.", None),
    "effect": ("What an exception does.", ("suppress-rule", "force-outcome", "escalate")),
    "targetRule": ("The rule id a suppress-rule exception disables.", None),
    "fallbackOutcome": ("The outcome id used when no rule matches (§8).", None),
    "escalation": ("Handoff configuration: when and to whom the decision is escalated. Not itself an outcome.", None),
    "triggers": ("The situations that cause escalation.", ("not-applicable", "missing-required-evidence", "unknown", "conflict", "no-match")),
    "target": ("The escalation destination: a kind and a name.", None),
    "name": ("The name of an escalation target, such as a role or a queue.", None),
    "message": ("Guidance shown when escalating.", None),
    "metadata": ("Non-normative bookkeeping: authors, timestamps, license, reviews, required extensions.", None),
    "authors": ("Who authored the pack.", None),
    "createdAt": ("When the pack was created (ISO-8601 date-time).", None),
    "license": ("The pack's license.", None),
    "requiredExtensions": ("Extension namespaces an implementation must understand to use the pack.", None),
    "reviews": ("A record of human reviews of the pack.", None),
    "reviewer": ("Who reviewed the pack.", None),
    "reviewedAt": ("When a review occurred.", None),
    "disposition": ("A review's conclusion.", ("approved", "changes-requested", "rejected")),
    "note": ("A reviewer's note.", None),
    "extensions": ("Namespaced additional data with reverse-DNS keys; org.judgmentpack.* is reserved.", None),
    "condition": ("A nested condition, used by the `not` operator.", None),
    "conditions": ("The list of sub-conditions combined by `all` or `any`.", None),
    "op": ("The kind of condition.", ("fact", "all", "any", "not", "evidence-present", "literal")),
    "path": ("A JSON Pointer to the fact a fact-condition reads.", None),
    "operator": ("The comparison a fact condition applies.", ("equals", "not-equals", "greater-than", "greater-than-or-equal", "less-than", "less-than-or-equal", "in")),
    "evidenceRequirement": ("The evidence requirement id an evidence-present condition checks.", None),
}


def _key_link(key: str) -> str:
    display = html.escape(json.dumps(key))
    if key in KEY_REFERENCE:
        return f'<a class="jkey" href="#kd-{html.escape(key)}">{display}</a>'
    return display


def _json_scalar(value: object) -> str:
    if isinstance(value, bool):
        return '<span class="jbool">' + ("true" if value else "false") + "</span>"
    if value is None:
        return '<span class="jnull">null</span>'
    if isinstance(value, (int, float)):
        return '<span class="jnum">' + html.escape(json.dumps(value)) + "</span>"
    if isinstance(value, str):
        return '<span class="jstr">' + html.escape(json.dumps(value)) + "</span>"
    return html.escape(json.dumps(value))


def _annotate(value: object, indent: int) -> str:
    pad = "  " * indent
    pad1 = "  " * (indent + 1)
    if isinstance(value, dict):
        if not value:
            return "{}"
        items = list(value.items())
        rows = [
            pad1 + _key_link(k) + ": " + _annotate(v, indent + 1) + ("," if i < len(items) - 1 else "")
            for i, (k, v) in enumerate(items)
        ]
        return "{\n" + "\n".join(rows) + "\n" + pad + "}"
    if isinstance(value, list):
        if not value:
            return "[]"
        rows = [
            pad1 + _annotate(v, indent + 1) + ("," if i < len(value) - 1 else "")
            for i, v in enumerate(value)
        ]
        return "[\n" + "\n".join(rows) + "\n" + pad + "]"
    return _json_scalar(value)


def _keydef_cards(current: PurePosixPath) -> str:
    parts = [
        '<p class="kd-hint">Click a highlighted key in the document to see what it means and its '
        "allowed values.</p>"
    ]
    for key, (summary, values) in KEY_REFERENCE.items():
        vals = ""
        if values:
            chips = " ".join("<code>" + html.escape(v) + "</code>" for v in values)
            vals = '<p class="kd-values"><span>One of:</span> ' + chips + "</p>"
        parts.append(
            '<div class="keydef" id="kd-' + html.escape(key) + '">'
            + "<h4><code>" + html.escape(key) + "</code></h4>"
            + "<p>" + html.escape(summary) + "</p>" + vals + "</div>"
        )
    guide = output_href(current, PurePosixPath("field-guide/index.html"))
    parts.append(
        '<p class="kd-more"><a href="' + html.escape(guide) + '">Full field guide &rarr;</a></p>'
    )
    return '<aside class="keydefs" aria-label="Key reference">' + "".join(parts) + "</aside>"


def annotated_json_block(value: object, current: PurePosixPath) -> str:
    """A JSON code block whose keys link to a side panel of schema definitions (no JavaScript)."""
    code = (
        '<div class="code-frame annotated-frame"><pre tabindex="0">'
        '<code class="language-json">' + _annotate(value, 0) + "</code></pre></div>"
    )
    return '<div class="annotated-json">' + code + _keydef_cards(current) + "</div>"


def field_reference_html() -> str:
    """The full key reference as a definition list, for the schema page."""
    rows = []
    for key, (summary, values) in KEY_REFERENCE.items():
        vals = ""
        if values:
            chips = " ".join("<code>" + html.escape(v) + "</code>" for v in values)
            vals = ' <span class="kd-values">One of: ' + chips + "</span>"
        rows.append(
            "<div><dt><code>" + html.escape(key) + "</code></dt><dd>"
            + html.escape(summary) + vals + "</dd></div>"
        )
    return '<dl class="field-reference">' + "".join(rows) + "</dl>"


def tag(text: str, kind: str = "neutral") -> str:
    return f'<span class="tag tag-{html.escape(kind)}">{html.escape(text)}</span>'


def artifact_link(current: PurePosixPath, source: str) -> str:
    target = PurePosixPath("artifacts") / PurePosixPath(source)
    return output_href(current, target)


def source_link(current: PurePosixPath, source: str, label: str = "Download raw JSON") -> str:
    return (
        f'<a class="button button-secondary" href="{html.escape(artifact_link(current, source))}" '
        f'download>{html.escape(label)}</a>'
    )


def item_list(items: tuple[str, ...]) -> str:
    return "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ul>"


def prepare_output(output: Path) -> None:
    resolved = output.resolve()
    if resolved in {ROOT.resolve(), Path("/").resolve()}:
        raise ValueError(f"refusing to replace unsafe output directory: {resolved}")
    if resolved.exists():
        marker = resolved / OUTPUT_MARKER
        if not marker.is_file():
            raise ValueError(
                f"refusing to replace {resolved}: it is not a recognized generated site"
            )
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)
    (resolved / OUTPUT_MARKER).write_text(
        "Generated by web/build.py. Edit source files, not this directory.\n",
        encoding="utf-8",
    )


def build_routes(manifest: dict) -> dict[str, PurePosixPath | str]:
    routes: dict[str, PurePosixPath | str] = {page.source: page.output for page in PAGES}
    routes.update(
        {
            ".": PurePosixPath("index.html"),
            "examples": PurePosixPath("examples/index.html"),
            "conformance": PurePosixPath("conformance/index.html"),
            "rfcs": PurePosixPath("rfcs/index.html"),
            "concepts": PurePosixPath("concepts/index.html"),
            "docs/concepts": PurePosixPath("concepts/index.html"),
            "schema": PurePosixPath("schema/index.html"),
            "web": PurePosixPath("project/deployment/index.html"),
            "LICENSE": PurePosixPath("project/license/index.html"),
            "schema/judgment-pack-core.schema.json": PurePosixPath("schema/index.html"),
            "conformance/README.md": PurePosixPath("conformance/index.html"),
            "conformance/manifest.json": PurePosixPath("conformance/manifest/index.html"),
            "conformance/manifest.schema.json": PurePosixPath(
                "conformance/manifest-schema/index.html"
            ),
            # The evaluation corpus is browsable as one page; its machine-readable files are served
            # from the copied artifact tree rather than as generated pages.
            "conformance/evaluation": PurePosixPath("conformance/evaluation/index.html"),
            "conformance/evaluation/manifest.json": PurePosixPath(
                "artifacts/conformance/evaluation/manifest.json"
            ),
            "conformance/evaluation/manifest.schema.json": PurePosixPath(
                "artifacts/conformance/evaluation/manifest.schema.json"
            ),
            ".vscode/tasks.json": GITHUB_ROOT + ".vscode/tasks.json",
        }
    )
    for path in sorted((ROOT / "conformance" / "evaluation" / "packs").glob("*.json")):
        source = path.relative_to(ROOT).as_posix()
        routes[source] = PurePosixPath("artifacts") / PurePosixPath(source)
    for path in sorted((ROOT / "examples").glob("*.json")):
        source = path.relative_to(ROOT).as_posix()
        routes[source] = PurePosixPath("examples") / path.stem / "index.html"
    for case in manifest["cases"]:
        source = f"conformance/{case['path']}"
        repository_file(source)
        routes[source] = (
            PurePosixPath("conformance/cases")
            / PurePosixPath(case["path"]).with_suffix("")
            / "index.html"
        )
    return routes


def build_markdown_pages(
    output_root: Path, routes: dict[str, PurePosixPath | str]
) -> None:
    for page in PAGES:
        path = ROOT / page.source
        text = path.read_text(encoding="utf-8")
        if page.source == "README.md":
            text = home_body(text)
        elif page.source == ".github/ISSUE_TEMPLATE/testing-feedback.md":
            text = "# Testing feedback template\n\n" + strip_front_matter(text)
        body, toc = render_markdown(text, page.source, page.output, routes)
        if page.source in {
            "TESTING.md",
            ".github/ISSUE_TEMPLATE/testing-feedback.md",
        }:
            body += """
<div class="notice notice-info"><strong>Ready to report a result?</strong>
Use only a minimal synthetic reproduction, then
<a href="https://github.com/Judgment-Pack/judgment-pack-spec/issues/new?template=testing-feedback.md">open a testing feedback issue on GitHub</a>.</div>
"""
        hero = ""
        body_class = ""
        if page.source == "README.md":
            body_class = "home-page"
            hero = f"""
<section class="hero" aria-labelledby="hero-title">
  <div class="hero-copy">
    <p class="eyebrow">Open, vendor-neutral specification</p>
    <h1 id="hero-title">Make expert judgment executable and testable.</h1>
    <p class="hero-lede">Judgment Pack is an open specification for representing the evidence, rules,
    exceptions, uncertainty, escalation criteria, and evaluations behind an AI agent's decisions.</p>
    <div class="hero-actions">
      <a class="button button-primary" href="{html.escape(output_href(page.output, PurePosixPath('spec/0.2.0-draft/index.html')))}">Read the specification</a>
      <a class="button button-secondary" href="{html.escape(GITHUB_URL)}" target="_blank" rel="noopener noreferrer">View on GitHub</a>
    </div>
    <p class="hero-support"><a href="{html.escape(output_href(page.output, PurePosixPath('why/index.html')))}">Why Judgment Pack?</a></p>
  </div>
  <div class="scope-card" aria-label="Current scope">
    <p class="scope-card-title">What this draft can test</p>
    <ol>
      <li>JSON carrier conformance</li>
      <li>Schema structure and formats</li>
      <li>Document references and constraints</li>
      <li>Evaluator conformance, against the evaluation corpus</li>
    </ol>
    <p><strong>It never proves truth, authority, safety, or fitness.</strong></p>
  </div>
</section>"""
            toc = ""
        rendered = page_html(
            output=page.output,
            title=page.title,
            description=page.description,
            section=page.section,
            artifact_label=page.artifact_label,
            body=body,
            toc=toc,
            source=page.source,
            source_ref=page.source_ref,
            hero=hero,
            body_class=body_class,
        )
        write_page(output_root, page.output, rendered)


def build_schema_page(
    output_root: Path, routes: dict[str, PurePosixPath | str]
) -> None:
    source = "schema/judgment-pack-core.schema.json"
    page_output = PurePosixPath("schema/index.html")
    raw = (ROOT / source).read_text(encoding="utf-8")
    schema = json.loads(raw)
    definitions = schema.get("$defs", {})
    properties = schema.get("properties", {})
    body = f"""
<h1>JPS Core JSON Schema</h1>
<p class="lede">The normative Draft 2020-12 structural schema for
<code>{html.escape(SITE_VERSION)}</code>. Format assertions for URI, date, and date-time are required
by the Core specification.</p>
<div class="notice notice-warning"><strong>Scope:</strong> Schema acceptance establishes structural
conformance only. It does not establish semantic document conformance, truth, authority, safety,
or operational fitness.</div>
<dl class="facts">
  <div><dt>Planned release identifier</dt><dd><code>{html.escape(str(schema.get('$id', '')))}</code></dd></div>
  <div><dt>Dialect</dt><dd><code>{html.escape(str(schema.get('$schema', '')))}</code></dd></div>
  <div><dt>Root properties</dt><dd>{len(properties)}</dd></div>
  <div><dt>Definitions</dt><dd>{len(definitions)}</dd></div>
</dl>
<p>{source_link(page_output, source)}</p>
<h2 id="field-reference">Field reference</h2>
<p>Every field and its allowed values, generated from the schema. The same definitions appear as
clickable cards beside each example document.</p>
{field_reference_html()}
<h2 id="raw-schema">Raw schema</h2>
{raw_block(raw)}
"""
    rendered = page_html(
        output=page_output,
        title="JPS Core JSON Schema",
        description=f"The normative JSON Schema for JPS Core {SITE_VERSION}.",
        section="spec",
        artifact_label="Normative schema",
        body=body,
        source=source,
    )
    write_page(output_root, page_output, rendered)


def build_examples(
    output_root: Path, routes: dict[str, PurePosixPath | str]
) -> None:
    index_output = PurePosixPath("examples/index.html")
    cards = []
    example_paths = sorted((ROOT / "examples").glob("*.json"))
    example_names = {path.name for path in example_paths}
    guide_names = set(EXAMPLE_GUIDES)
    if example_names != guide_names:
        missing = ", ".join(sorted(example_names - guide_names)) or "none"
        stale = ", ".join(sorted(guide_names - example_names)) or "none"
        raise ValueError(
            f"example guidance mismatch; missing guides: {missing}; stale guides: {stale}"
        )

    for path in example_paths:
        source = path.relative_to(ROOT).as_posix()
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
        guide = EXAMPLE_GUIDES[path.name]
        detail_output = routes[source]
        assert isinstance(detail_output, PurePosixPath)
        title = str(value.get("title", path.stem.replace("-", " ").title()))
        description = str(value.get("description", "Synthetic JPS example."))
        outcomes = value.get("outcomes", [])
        rules = value.get("rules", [])
        cards.append(
            f"""
<article class="card">
  <p class="card-kicker">Synthetic · non-operational</p>
  <h2><a href="{html.escape(output_href(index_output, detail_output))}">{html.escape(title)}</a></h2>
  <p>{html.escape(description)}</p>
  <p><strong>Focus:</strong> {html.escape(guide.focus)}</p>
  <p class="card-meta">{len(outcomes)} outcomes · {len(rules)} rules</p>
</article>"""
        )
        body = f"""
<h1>{html.escape(title)}</h1>
<p class="lede">{html.escape(description)}</p>
<div class="notice notice-warning"><strong>Synthetic example:</strong> This document is for
schema and authoring tests. It is not a policy, authorization, or instruction to perform an
external action.</div>
<dl class="facts">
  <div><dt>Pack ID</dt><dd><code>{html.escape(str(value.get('id', '')))}</code></dd></div>
  <div><dt>Pack version</dt><dd><code>{html.escape(str(value.get('version', '')))}</code></dd></div>
  <div><dt>Outcomes</dt><dd>{len(outcomes)}</dd></div>
  <div><dt>Rules</dt><dd>{len(rules)}</dd></div>
</dl>
<p>{source_link(detail_output, source)}</p>
<h2 id="example-guide">Guide to this example</h2>
<p><strong>Focus:</strong> {html.escape(guide.focus)}</p>
<p>The checked-in document is expected to pass JPS carrier, structural, and semantic document
checks. The edge and failure notes below are inspection prompts or scratch-copy exercises; they are
not evaluation-corpus rows and assert no evaluator-conformance result.</p>
<h3 id="what-this-example-demonstrates">What this example demonstrates</h3>
<p>{html.escape(guide.demonstrates)}</p>
<h3 id="good-for">Good for</h3>
{item_list(guide.good_for)}
<h3 id="edges-to-inspect">Edges to inspect</h3>
{item_list(guide.edges)}
<h3 id="failure-paths">Failure paths</h3>
{item_list(guide.failure_paths)}
<div class="notice notice-info"><strong>Keep the layers separate.</strong> A malformed carrier, a
schema-shape failure, and a dangling local reference fail at different document-conformance layers.
Missing evidence, unknown facts, conflicts, and no-match handling belong to the resolution model of
§§7–8, which JPS 0.2.0-draft makes normative for the evaluator conformance class only.
A document-conformance result never depends on them, and the notes on this page are not corpus rows.</div>
<h2 id="document">Annotated document</h2>
<p>The complete validated pack. Each highlighted key links to its definition on the right — click a
key to see what it means and its allowed values.</p>
{annotated_json_block(value, detail_output)}
"""
        rendered = page_html(
            output=detail_output,
            title=title,
            description=description,
            section="examples",
            artifact_label="Synthetic example",
            body=body,
            source=source,
        )
        write_page(output_root, detail_output, rendered)

    index_body = f"""
<h1>Synthetic examples</h1>
<p class="lede">These are synthetic, structurally and semantically conforming JPS documents for
inspecting and testing the document format. Unrelated domains exercise the same portable
shape without claiming that the examples are complete, authoritative, or safe for operational
use.</p>
<div class="notice notice-info"><strong>Use synthetic data only.</strong> These examples are
designed for structural and semantic document testing, not decision execution. Ordinary validation
must not fetch their source locators unless explicitly requested.</div>
<h2 id="how-to-use-these-examples">How to use these examples</h2>
<ol>
  <li>Open a detail page to understand the document's focus, boundaries, edges, and useful failure exercises.</li>
  <li>Download the exact JSON and validate it locally; the checked-in document should pass all three document-conformance layers.</li>
  <li>Edit only a scratch copy to create a carrier, structural, or semantic failure.</li>
  <li>Compare what you observe with <a href="{html.escape(output_href(index_output, PurePosixPath('testing/index.html')))}">Test the preview</a>.</li>
</ol>
<p>These pages are about document conformance. JPS 0.2.0-draft also defines portable evaluation
semantics, but an evaluator-conformance claim is made against the
<a href="{html.escape(output_href(index_output, PurePosixPath('conformance/evaluation/index.html')))}">evaluation
corpus</a>, never against an example. The edge notes on each page explain illustrative applicability,
evidence, unknown, conflict, and fallback situations without claiming an expected runtime decision.
Validity never proves truth, authority, safety, or fitness.</p>
<p>For the structural baseline, use an independent Draft 2020-12 implementation and inspect
semantic references separately. Conforming tools that check all current JPS document-conformance
layers are listed on the <a href="{html.escape(output_href(index_output, PurePosixPath('implementations/index.html')))}">Implementations</a> page.</p>
<div class="card-grid">{''.join(cards)}</div>
"""
    rendered = page_html(
        output=index_output,
        title="Synthetic examples",
        description="Browsable, non-operational examples of JPS documents in unrelated domains.",
        section="examples",
        artifact_label="Informative",
        body=index_body,
    )
    write_page(output_root, index_output, rendered)


def build_conformance(
    output_root: Path,
    routes: dict[str, PurePosixPath | str],
    manifest: dict,
) -> None:
    index_output = PurePosixPath("conformance/index.html")
    intro_text = (ROOT / "conformance/README.md").read_text(encoding="utf-8")
    intro, _ = render_markdown(intro_text, "conformance/README.md", index_output, routes)
    layers = ("carrier", "structural", "semantic")
    counts = {layer: 0 for layer in layers}
    rows_by_layer: dict[str, list[str]] = {layer: [] for layer in layers}
    for case in manifest["cases"]:
        layer = case["layer"]
        counts[layer] = counts.get(layer, 0) + 1
        source = f"conformance/{case['path']}"
        detail_output = routes[source]
        assert isinstance(detail_output, PurePosixPath)
        diagnostic = (case.get("expectedDiagnostic") or {}).get("code", "—")
        rows_by_layer.setdefault(layer, []).append(
            "<tr>"
            f'<th scope="row"><a href="{html.escape(output_href(index_output, detail_output))}"><code>{html.escape(case["id"])}</code></a></th>'
            f"<td>{html.escape(case['expectedResult'])}</td>"
            f"<td>{html.escape(case['focus'])}</td>"
            f"<td><code>{html.escape(diagnostic)}</code></td>"
            f"<td>{html.escape(case['specSection'])}</td>"
            "</tr>"
        )
        raw = repository_file(source).read_text(encoding="utf-8")
        expected = case["expectedResult"]
        expected_kind = "valid" if expected == "valid" else "unsupported" if expected == "unsupported" else "invalid"
        diagnostic_detail = case.get("expectedDiagnostic")
        diagnostic_html = ""
        if diagnostic_detail:
            diagnostic_html = (
                "<div><dt>Expected diagnostic</dt><dd><code>"
                + html.escape(diagnostic_detail["code"])
                + "</code> at <code>"
                + html.escape(diagnostic_detail["path"] or "(document root)")
                + "</code></dd></div>"
            )
        capabilities = case.get("supportedExtensions")
        capabilities_html = ""
        if capabilities is not None:
            capabilities_html = (
                "<div><dt>Supported extensions</dt><dd>"
                + (", ".join(f"<code>{html.escape(item)}</code>" for item in capabilities) or "None")
                + "</dd></div>"
            )
        body = f"""
<p><a class="back-link" href="{html.escape(output_href(detail_output, index_output))}">← All conformance cases</a></p>
<h1><code>{html.escape(case['id'])}</code></h1>
<p class="lede">{html.escape(case['focus'])}</p>
<p>{tag(layer, layer)} {tag(expected, expected_kind)}</p>
<dl class="facts">
  <div><dt>Layer</dt><dd>{html.escape(layer)}</dd></div>
  <div><dt>Expected result</dt><dd>{html.escape(expected)}</dd></div>
  {diagnostic_html}
  <div><dt>Specification</dt><dd>{html.escape(case['specSection'])}</dd></div>
  {capabilities_html}
</dl>
<div class="notice notice-info">The expected result is conformance-corpus metadata, not a claim
about factual grounding, authority, safety, or operational fitness.</div>
<p>{source_link(detail_output, source, 'Download exact fixture')}</p>
<h2 id="fixture">Exact fixture</h2>
{raw_block(raw)}
"""
        rendered = page_html(
            output=detail_output,
            title=case["id"],
            description=case["focus"],
            section="conformance",
            artifact_label="Informative test case",
            body=body,
            source=source,
        )
        write_page(output_root, detail_output, rendered)

    summaries = "".join(
        f'<li><a href="#{html.escape(layer)}"><strong>{counts.get(layer, 0)}</strong> {html.escape(layer)}</a></li>'
        for layer in layers
    )
    tables = []
    for layer in layers:
        rows = rows_by_layer.get(layer, [])
        if not rows:
            continue
        tables.append(
            f"""
<section class="case-group" aria-labelledby="{html.escape(layer)}">
  <h2 id="{html.escape(layer)}">{html.escape(layer.title())} cases <span class="count">{len(rows)}</span></h2>
  <div class="table-scroll"><table>
    <thead><tr><th scope="col">Case</th><th scope="col">Result</th><th scope="col">Focus</th><th scope="col">Diagnostic</th><th scope="col">Spec</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table></div>
</section>"""
        )
    manifest_output = PurePosixPath("conformance/manifest/index.html")
    manifest_schema_output = PurePosixPath("conformance/manifest-schema/index.html")
    body = f"""
{intro}
<div class="notice notice-warning"><strong>Document conformance only.</strong> These cases test
documents. Evaluator conformance is claimed against the separate
<a href="{html.escape(output_href(index_output, PurePosixPath('conformance/evaluation/index.html')))}">evaluation
corpus</a>, and no corpus of either kind can establish truth, authority, safety, or fitness.</div>
<nav class="case-summary" aria-label="Conformance layers"><ul>{summaries}</ul></nav>
<p class="artifact-actions">
  <a class="button button-secondary" href="{html.escape(output_href(index_output, manifest_output))}">View manifest</a>
  <a class="button button-secondary" href="{html.escape(output_href(index_output, manifest_schema_output))}">View manifest schema</a>
</p>
{''.join(tables)}
"""
    rendered = page_html(
        output=index_output,
        title="Conformance corpus",
        description="The browsable JPS document-conformance corpus and its exact expected results.",
        section="conformance",
        artifact_label="Informative test corpus",
        body=body,
        source="conformance/README.md",
    )
    write_page(output_root, index_output, rendered)

    for source, page_output, title, label in (
        (
            "conformance/manifest.json",
            manifest_output,
            "Conformance manifest",
            "Informative manifest",
        ),
        (
            "conformance/manifest.schema.json",
            manifest_schema_output,
            "Conformance manifest schema",
            "Informative schema",
        ),
    ):
        raw = (ROOT / source).read_text(encoding="utf-8")
        raw_body = f"""
<p><a class="back-link" href="{html.escape(output_href(page_output, index_output))}">← Conformance corpus</a></p>
<h1>{html.escape(title)}</h1>
<p>{source_link(page_output, source)}</p>
{raw_block(raw)}
"""
        rendered = page_html(
            output=page_output,
            title=title,
            description=f"Raw {title.lower()} for JPS {SITE_VERSION}.",
            section="conformance",
            artifact_label=label,
            body=raw_body,
            source=source,
        )
        write_page(output_root, page_output, rendered)


def project_card(
    current: PurePosixPath,
    title: str,
    description: str,
    target: PurePosixPath,
) -> str:
    return f"""
<article class="card">
  <h2><a href="{html.escape(output_href(current, target))}">{html.escape(title)}</a></h2>
  <p>{html.escape(description)}</p>
</article>"""


def build_project_index(output_root: Path) -> None:
    page_output = PurePosixPath("project/index.html")
    groups = (
        (
            "Release and direction",
            (
                ("0.2.0-draft release", "Current draft scope, the independence caveat, and known limitations.", "project/releases/0.2.0-draft/index.html"),
                ("0.1.0-draft release", "The first published draft's scope and known limitations.", "project/releases/0.1.0-draft/index.html"),
                ("0.1.0-draft specification", "Where the superseded draft's tagged prose lives.", "spec/0.1.0-draft/index.html"),
                ("Changelog", "Draft and published preview history.", "project/changelog/index.html"),
                ("Versioning", "Release and compatibility policy.", "project/versioning/index.html"),
                ("Roadmap", "Evidence gates for each maturity stage.", "project/roadmap/index.html"),
            ),
        ),
        (
            "Design and tooling",
            (
                ("Design principles", "Constraints that shape JPS.", "project/design-principles/index.html"),
                ("Non-goals", "What JPS intentionally does not standardize.", "project/non-goals/index.html"),
                ("Origin and scope", "How the specification stays independent of any implementation.", "project/origin-and-boundary/index.html"),
                ("Specification and implementation boundary", "Why the spec is usable without any particular tool.", "project/tooling/index.html"),
                ("Site deployment", "Build, preview, and hosting guidance.", "project/deployment/index.html"),
            ),
        ),
        (
            "Concepts and proposals",
            (
                ("FAQ", "Common and hard architectural questions.", "faq/index.html"),
                ("Field guide", "Plain-language walkthrough of every field.", "field-guide/index.html"),
                ("Architecture vision", "A non-normative picture of the layered architecture.", "architecture/vision/index.html"),
                ("Comparison", "How JPS relates to DMN, policy engines, and rule engines.", "concepts/comparison/index.html"),
                ("Proposals (RFCs)", "Open design proposals and the change process.", "rfcs/index.html"),
            ),
        ),
        (
            "Participation and stewardship",
            (
                ("Contributing", "Ways to test and propose changes.", "project/contributing/index.html"),
                ("Governance", "Current decision model and future neutrality.", "project/governance/index.html"),
                ("Security", "Security boundary and reporting.", "project/security/index.html"),
                ("Testing feedback", "Safe, reproducible report template.", "project/testing-feedback/index.html"),
                ("Code of conduct", "Expected participation standards.", "project/code-of-conduct/index.html"),
                ("License", "Apache License 2.0.", "project/license/index.html"),
            ),
        ),
    )
    sections = []
    for heading, items in groups:
        cards = "".join(
            project_card(page_output, title, description, PurePosixPath(target))
            for title, description, target in items
        )
        sections.append(f"<section><h2>{html.escape(heading)}</h2><div class=\"card-grid\">{cards}</div></section>")
    body = f"""
<h1>Project information</h1>
<p class="lede">Design rationale, release policy, governance, participation, security, and the
boundary between the specification and future developer tools.</p>
{''.join(sections)}
"""
    rendered = page_html(
        output=page_output,
        title="Project information",
        description="Governance, roadmap, release, design, tooling, security, and contribution information for JPS.",
        section="project",
        artifact_label="Informative",
        body=body,
    )
    write_page(output_root, page_output, rendered)


def build_concepts_index(output_root: Path) -> None:
    page_output = PurePosixPath("concepts/index.html")
    cards = (
        ("Why Judgment Pack?", "The gap between information and judgment, and why coding agents work better than most business agents.", "why/index.html"),
        ("Architecture vision", "A non-normative picture of the layered architecture — what is shipped versus what is proposed.", "architecture/vision/index.html"),
        ("How Judgment Pack compares", "How JPS relates to DMN, policy engines, rule engines, BPMN, and knowledge graphs.", "concepts/comparison/index.html"),
        ("Field guide", "A plain-language walkthrough of every part of a Judgment Pack document.", "field-guide/index.html"),
        ("FAQ", "Answers to common and hard architectural questions.", "faq/index.html"),
    )
    grid = "".join(
        project_card(page_output, title, description, PurePosixPath(target))
        for title, description, target in cards
    )
    body = f"""
<h1>Concepts</h1>
<p class="lede">Start here to understand what a Judgment Pack is, how it differs from the systems it
is often confused with, and where the wider architecture is headed — before reading the normative
specification.</p>
<div class="card-grid">{grid}</div>
"""
    rendered = page_html(
        output=page_output,
        title="Concepts",
        description="Understand what a Judgment Pack is, how it compares to prior art, and the non-normative architecture vision.",
        section="concepts",
        artifact_label="Informative",
        body=body,
    )
    write_page(output_root, page_output, rendered)


def build_license(output_root: Path) -> None:
    page_output = PurePosixPath("project/license/index.html")
    raw = (ROOT / "LICENSE").read_text(encoding="utf-8")
    body = f"<h1>Apache License 2.0</h1>{raw_block(raw, 'text')}"
    rendered = page_html(
        output=page_output,
        title="Apache License 2.0",
        description="The license for the Judgment Pack Specification repository.",
        section="project",
        artifact_label="License",
        body=body,
        source="LICENSE",
    )
    write_page(output_root, page_output, rendered)


def copy_artifacts(output_root: Path) -> None:
    for directory in ("schema", "examples", "conformance"):
        for path in sorted((ROOT / directory).rglob("*.json")):
            relative = path.relative_to(ROOT)
            destination = output_root / "artifacts" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)


def copy_static(output_root: Path) -> None:
    destination = output_root / "assets"
    shutil.copytree(WEB_ROOT / "static", destination)


def build_robots(output_root: Path, config: BuildConfig) -> None:
    if config.is_production:
        lines = ["# Published specification.", "User-agent: *", "Allow: /"]
        if config.base_url:
            sitemap_url = absolute_url(config.base_url, PurePosixPath("sitemap.xml"))
            lines += ["", f"Sitemap: {sitemap_url}"]
    else:
        lines = [
            "# Non-production preview build — do not index.",
            "User-agent: *",
            "Disallow: /",
        ]
    (output_root / "robots.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_sitemap(output_root: Path, config: BuildConfig) -> None:
    if not (config.is_production and config.base_url):
        return
    seen: set[str] = set()
    locations: list[str] = []
    for output in config.written:
        if output.name == "404.html":
            continue
        location = absolute_url(config.base_url, output)
        if location in seen:
            continue
        seen.add(location)
        locations.append(location)
    entries = "".join(
        f"  <url><loc>{html.escape(location)}</loc>"
        f"<lastmod>{html.escape(config.build_time)}</lastmod></url>\n"
        for location in sorted(locations)
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + entries
        + "</urlset>\n"
    )
    (output_root / "sitemap.xml").write_text(document, encoding="utf-8")


def build_not_found(output_root: Path) -> None:
    page_output = PurePosixPath("404.html")
    body = """
<h1>Page not found</h1>
<p class="lede">The requested documentation page does not exist in this preview.</p>
<p><a class="button button-primary" href="./">Return to the overview</a></p>
"""
    rendered = page_html(
        output=page_output,
        title="Page not found",
        description="The requested JPS documentation page was not found.",
        section="",
        artifact_label="",
        body=body,
        base_href="/",
        noindex=True,
    )
    write_page(output_root, page_output, rendered)


CANONICAL_SCHEMA_SOURCES = (
    "schema/judgment-pack-core.schema.json",
    # The superseded schemas stay served at the $id each was published under, so a pack or manifest that
    # still declares the older exact specVersion remains checkable and a cited identifier keeps resolving.
    "schema/judgment-pack-core-0.1.0-draft.schema.json",
    "schema/conformance-manifest-0.1.0-draft.schema.json",
    "conformance/manifest.schema.json",
    "conformance/evaluation/manifest.schema.json",
)


def publish_canonical_schemas(output_root: Path) -> None:
    """Serve each schema at the path of its own ``$id`` so the identifier resolves."""
    for source in CANONICAL_SCHEMA_SOURCES:
        file = ROOT / source
        schema_id = json.loads(file.read_text(encoding="utf-8")).get("$id", "")
        path = urlsplit(schema_id).path.lstrip("/")
        if not path:
            raise ValueError(f"{source} has no $id path to publish at")
        destination = output_root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(file.read_bytes())


def build_implementations_index(output_root: Path) -> None:
    page_output = PurePosixPath("implementations/index.html")
    runtime_url = "https://github.com/Judgment-Pack/judgment-pack-runtime"
    experiments_url = "https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments"
    governance = output_href(page_output, PurePosixPath("project/governance/index.html"))
    body = f"""
<h1>Implementations</h1>
<p class="lede">Independent tools that implement JPS document conformance. A listing here records
that a tool exercises the public specification; it is not certification, endorsement, or authority
over the specification.</p>
<div class="notice notice-info"><strong>The specification is the authority.</strong> No
implementation — including the reference runtime — is normative. Passing a tool's checks establishes
only what that tool reports about the JPS document layers, never factual grounding, authorization,
safety, or fitness. Any implementation that passes the public conformance corpus is equally valid.</div>
<h2 id="available">Available implementations</h2>
<div class="card-grid">
  <article class="card">
    <p class="card-kicker">Open source · Apache-2.0 · maintained with the specification</p>
    <h2><a href="{html.escape(runtime_url)}" target="_blank" rel="noopener noreferrer">judgment-pack</a></h2>
    <p>The project's vendor-neutral reference runtime; the command it installs is <code>jpack</code>.
    It validates the carrier, structural schema, and semantic references of a JPS document against an
    immutable specification release, and it states an evaluator-conformance claim for
    <code>0.2.0-draft</code> in its own repository. Its evaluating surfaces stay labelled
    <code>experimental</code>, which reports their <em>stability</em> and never their conformance.
    Nothing it reports chooses an outcome for a real decision, fetches a source, or authorizes an
    action.</p>
    <p class="card-meta">Reference runtime · one implementation among peers</p>
  </article>
  <article class="card">
    <p class="card-kicker">Open source · Apache-2.0 · experimental, claims no conformance</p>
    <h2><a href="{html.escape(experiments_url)}" target="_blank" rel="noopener noreferrer">clean-room Python evaluator</a></h2>
    <p>A second evaluator, written from the specification text alone inside an information barrier and
    published with its interpretation log, clean-room protocol, and agreement harness. It exists to
    test whether the prose pins the semantics: where two independent readings diverge, the divergence
    locates an ambiguity in the specification rather than a defect in either reader. It claims no JPS
    conformance of any kind.</p>
    <p class="card-meta">Agreement evidence · not a conformance claim</p>
  </article>
</div>
<div class="notice notice-warning"><strong>Two implementations, one author.</strong> Both listings
above trace to the same maintainer's direction, so their agreement corroborates that the
specification is precise — it is not independent evidence of interoperability, and the project does
not present it as such. See <a href="{html.escape(governance)}">governance</a> for the interim
review regime this sits under.</div>
<h2 id="adding-an-implementation">Adding an implementation</h2>
<p>This list is open to independent implementations tested against the public conformance
artifacts. Presence here does not confer certification, official-validator status, endorsement, or
authority over the specification.</p>
"""
    rendered = page_html(
        output=page_output,
        title="Implementations",
        description="Independent, nonnormative tools that implement JPS document conformance.",
        section="implementations",
        artifact_label="Informative",
        body=body,
    )
    write_page(output_root, page_output, rendered)


@dataclass(frozen=True)
class Slide:
    """One full-height section of the presentation.

    ``figure`` names a file in ``web/static``; ``wide`` puts it under the text
    instead of beside it, for the two figures that need the room.
    """

    anchor: str
    kicker: str
    heading: str
    lede: str = ""
    points: tuple[str, ...] = ()
    quote: str = ""
    note: str = ""
    figure: str = ""
    figure_alt: str = ""
    figure_caption: str = ""
    wide: bool = False
    actions: tuple[tuple[str, str, bool], ...] = ()


# The deck is written to be read in order and skimmed out of order, so every
# slide carries its own claim in the heading and its evidence in the points.
# Numbers here are load-bearing and each is sourced from a repository that
# publishes its own method; none is rounded up.
SLIDES: tuple[Slide, ...] = (
    Slide(
        anchor="decision-engine",
        kicker="01 — The premise",
        heading="Every company runs on decisions",
        lede=(
            "Approve or decline. Escalate or handle it. Refund or refuse. Strip away the software "
            "and the org chart, and this is what a company does all day."
        ),
        points=(
            "<strong>The know-how is real, and it was expensive.</strong> Which evidence counts, "
            "which exception beats which rule, when to stop and ask a person. It took years to build up.",
            "<strong>Almost none of it is written down.</strong> It lives in policy documents, in "
            "precedent, and in the one person who remembers why the limit is 5,000.",
            "<strong>Now AI is doing the work.</strong> And that know-how is exactly the thing nobody "
            "can hand it.",
        ),
        figure="deck-decision-engine.svg",
        figure_alt=(
            "An organization box holding policy, precedent, expertise, and hard-won exceptions, with "
            "an arrow labelled judgment leading to a box of decisions: approve, reject, escalate, "
            "hold."
        ),
        figure_caption="The arrow is the valuable part. It is also the part nobody wrote down.",
    ),
    Slide(
        anchor="black-box",
        kicker="02 — The problem",
        heading="When the AI gets it wrong, nobody can say why",
        lede=(
            "Company rules, the instructions given to the model, ordinary software code, and the "
            "model's own guesswork all end up mixed into one thing."
        ),
        points=(
            "<strong>You cannot isolate the cause.</strong> Were the instructions unclear? Was it a "
            "bug? Did the model simply make something up? From outside, all three look the same.",
            "<strong>Auditors get behaviour, not a document.</strong> You can show someone what the "
            "system did. You cannot show them what it was supposed to do.",
            "<strong>It cannot move.</strong> Switch tools, vendors, or models and someone rebuilds "
            "the reasoning from memory.",
            "<strong>You cannot tell whether a change helped.</strong> With nothing written down, "
            "there is nothing to measure against.",
        ),
        figure="deck-black-box.svg",
        figure_alt=(
            "A single hatched box containing company rules, AI instructions, software code, and the "
            "model's guesswork together, with question marks pressing in from all four sides."
        ),
        figure_caption="Four things in one box, one answer out. Which part caused it?",
    ),
    Slide(
        anchor="coding-agents",
        kicker="03 — The diagnosis",
        heading="AI works best where the work checks itself",
        lede=(
            "The AI that genuinely delivers today is AI that writes code. Not because coding is easy "
            "— because the work comes with an automatic referee."
        ),
        points=(
            "<strong>Code grades itself.</strong> It compiles or it does not. Tests pass or they "
            "fail. The verdict arrives in seconds, and nobody has to agree on it first.",
            "<strong>Business decisions have no referee.</strong> Goals are fuzzy, the evidence is "
            "spread across a dozen systems, the same word means different things to different teams, "
            "and you learn whether you were right months later.",
            "<strong>So the missing piece is not a smarter model.</strong> It is writing the judgment "
            "down, and having a way to check it.",
        ),
        figure="deck-coding-vs-business.svg",
        figure_alt=(
            "Two panels. A coding agent writes code, which passes through a compiler and tests, "
            "producing a pass-or-fail verdict in seconds: the target is explicit, the work actually "
            "runs, and the verdict is objective — the environment grades the work. A business agent "
            "reads documents, weighs them up, and decides, producing no verdict at all: the goal is "
            "fuzzy, evidence is scattered, and feedback comes months later — nothing says pass or "
            "fail."
        ),
        figure_caption=(
            "The same models sit behind both panels. Only one environment can tell you whether the "
            "work was any good."
        ),
    ),
    Slide(
        anchor="knowledge-and-judgment",
        kicker="04 — The distinction",
        heading="Knowing things is not the same as deciding",
        lede=(
            "Most AI effort goes into helping the machine know more — search, retrieval, connecting "
            "it to your documents. That is a different problem, and solving it does not solve this one."
        ),
        points=(
            "<strong>Search finds what is relevant.</strong> It has no opinion about what should "
            "happen next.",
            "<strong>Judgment decides what happens next.</strong> Does this case even apply? Which "
            "rule fires? What overrides it? Is this enough to act on, or does a person need to look?",
            "<strong>One feeds the other.</strong> Your documents and databases are inputs to a "
            "decision. They do not make the decision, and better search will never start.",
        ),
        figure="deck-knowledge-vs-judgment.svg",
        figure_alt=(
            "Two boxes side by side. Knowledge answers what do we know — documents, databases, "
            "search results, with no opinion on what to do — and feeds Judgment, which answers so "
            "what happens: which rule applies, what overrides it, when to ask a person."
        ),
        figure_caption="Complementary, not competing — and only one of them decides.",
    ),
    Slide(
        anchor="what-a-pack-is",
        kicker="05 — The proposal",
        heading="Write the decision down in a file",
        lede=(
            "A Judgment Pack is a plain file that spells out one decision, completely. No AI inside "
            "it, no software inside it. Just the reasoning, in a form a machine can act on."
        ),
        points=(
            "<strong>It states the intent, not only the logic.</strong> What is being decided, and "
            "why — so a reader can tell whether the rules actually serve the goal.",
            "<strong>It puts the awkward parts in writing.</strong> The exceptions, what to do when "
            "a fact is missing, and when a person has to take over — the nuance code buries and "
            "instructions leave to chance.",
            "<strong>The possible answers are fixed in advance.</strong> It cannot return something "
            "nobody approved.",
            "<strong>It reviews like code.</strong> Version it, compare two versions, and argue about "
            "a change in writing rather than in a meeting.",
        ),
        figure="deck-pack-anatomy.svg",
        figure_alt=(
            "One document listing, in order: the decision, evidence, when it applies, rules, "
            "exceptions, missing facts, answers, and ask a human — each with a one-line gloss."
        ),
        figure_caption="One file, one decision. The file format is the easy part; the contents are the point.",
    ),
    Slide(
        anchor="conformance",
        kicker="06 — The discipline",
        heading="A green checkmark that does not mean “approved”",
        lede=(
            "The obvious way to ruin this is a tool that says PASS and lets everyone read it as "
            "“this decision is fine.” The design works hard to make that impossible to say by accident."
        ),
        points=(
            "<strong>Four things can be checked automatically.</strong> That the file opens, that it "
            "is put together correctly, that it does not contradict itself, and that two separate "
            "tools reach the same answer from it.",
            "<strong>Three things are deliberately out of reach.</strong> Whether the facts are "
            "actually true. Whether anyone with authority approved this. Whether it is safe to act "
            "on here.",
            "<strong>Passing is never permission.</strong> A valid file is not a correct, authorised, "
            "or safe one — and nothing built on this is allowed to imply that it is.",
        ),
        figure="deck-conformance-line.svg",
        figure_alt=(
            "Four filled rows — readable, well-formed, consistent, agreed — above a drawn line, with "
            "is it true, is it allowed, and is it safe in outline below it. Nothing below the line is "
            "ever claimed."
        ),
        figure_caption="Drawing this line is the design. Blurring it is the whole risk.",
    ),
    Slide(
        anchor="portability",
        kicker="07 — The test",
        heading="Built twice, separately, with identical answers",
        lede=(
            "“Portable” is easy to claim and hard to earn. So it was tested rather than asserted."
        ),
        points=(
            "<strong>One decision, one answer — down to the character.</strong> The result is pinned "
            "precisely enough that two programs can be compared automatically instead of by eye.",
            "<strong>The second version was built in isolation.</strong> From the written spec alone, "
            "in a different programming language, with no access to the first.",
            "<strong>All 20 test cases matched exactly.</strong> Every detail that could have drifted "
            "between them did not.",
            "<strong>Where they disagreed, the writing got fixed.</strong> An early mismatch showed "
            "the spec was ambiguous. Catching that is the entire point of the exercise.",
        ),
        note=(
            "Said plainly: both were built under the same maintainer. That shows the spec is precise "
            "enough to follow. It is <em>not</em> proof that two unrelated companies would agree, and "
            "it is not presented as such."
        ),
        figure="deck-portable-result.svg",
        figure_alt=(
            "One decision file feeds two separately built programs — the reference tool, built by the "
            "project, and an independent rebuild, built from the written spec alone. Both produce the "
            "same answer, identical character for character."
        ),
        figure_caption="If two careful readers disagree, the writing was unclear — so the writing gets fixed.",
    ),
    Slide(
        anchor="inputs",
        kicker="08 — The open edge",
        heading="A file can say which evidence matters. It cannot say the evidence is real.",
        lede=(
            "An AI that can state a fact can also invent one. That is a genuine hole, it sits outside "
            "this specification, and it is being worked on in the open rather than quietly patched."
        ),
        points=(
            "<strong>Let the system fetch the data, not the AI.</strong> A reference service runs the "
            "lookup itself and signs the result, so an AI cannot hand in a number it made up.",
            "<strong>Each session is sealed when it closes.</strong> That catches the two tricks a "
            "stored record cannot catch by itself: replaying an old session, or quietly deleting the "
            "end of one.",
            "<strong>Anyone can check it; nobody extra can fake it.</strong> Checking needs only a "
            "public key. The format and the checker are open on purpose — an assurance nobody can "
            "verify is worth nothing.",
        ),
        note=(
            "The limit is stated up front and does not move: this proves <strong>where the data came "
            "from, not that it is correct</strong>. It shows the numbers a decision was based on were "
            "not tampered with. It says nothing about whether those numbers were right."
        ),
        figure="deck-attested-inputs.svg",
        figure_alt=(
            "A source is fetched and signed by a gateway, producing a receipt. Receipts are linked in "
            "order and the session is sealed. A verifier checks the chain and the seal using only a "
            "public key."
        ),
        figure_caption="Shows the data was not tampered with — never that the data is correct.",
    ),
    Slide(
        anchor="evidence",
        kicker="09 — The method",
        heading="We publish the results that went against us",
        quote=(
            "“A standard earns trust by shipping something small that works, and being honest about "
            "everything that does not yet.”"
        ),
        lede=(
            "Experiments are written down before they are run, the people doing the work do not know "
            "which result is hoped for, and failures get published as loudly as successes. Three "
            "examples, none of them flattering:"
        ),
        points=(
            "<strong>A feature meant to solve a problem solved none of it.</strong> Five people tried "
            "independently, and all five concluded the honest answer was to build nothing.",
            "<strong>A number we had published was six times too high.</strong> “About 19 of 25” was "
            "re-measured properly at 3. It had already been quoted elsewhere. We corrected it in public.",
            "<strong>A study's core assumption turned out to be false — and we found it ourselves.</strong> "
            "The headline was rewritten to say so, and the flattering summary table was deleted "
            "rather than defended.",
        ),
        note=(
            "This is also why it is called a research preview and not a standard. The path to a real "
            "1.0 is gated on evidence — outside implementations, outside reviews, real users — and "
            "none of those gates is quietly ticked off."
        ),
    ),
    Slide(
        anchor="status",
        kicker="10 — Where it actually stands",
        heading="Small, working, and honest about the rest",
        lede=(
            "A research preview. No stability promises yet, and not something to put in front of a "
            "consequential real decision today."
        ),
        points=(
            "<strong>Works today:</strong> the file format, the checks that tell you a file is sound, "
            "and an agreed way to turn one into an answer — held in place by 47 tests on the format "
            "and 20 on the answers.",
            "<strong>Built:</strong> a reference tool anyone can run, plus a second independent one "
            "kept deliberately separate so that agreement between them means something.",
            "<strong>Proposed, not built:</strong> chaining decisions together, choosing which "
            "decision applies, and a shared directory for finding them. Each is an open proposal with "
            "its bar for acceptance written down.",
            "<strong>Still open:</strong> proving where evidence came from, and everything the later "
            "stages depend on.",
        ),
        actions=(
            ("Read the specification", "spec/0.2.0-draft/index.html", False),
            ("See a worked example", "examples/index.html", True),
            ("Try the tools", "implementations/index.html", True),
            ("What has to be proven next", "project/roadmap/index.html", True),
        ),
    ),
)


def slide_html(current: PurePosixPath, index: int, slide: Slide) -> str:
    parts = [
        f'<span class="slide-number">{html.escape(slide.kicker)}</span>',
    ]
    heading_tag = "h1" if index == 0 else "h2"
    parts.append(f"<{heading_tag}>{html.escape(slide.heading)}</{heading_tag}>")
    if slide.quote:
        parts.append(f'<blockquote class="slide-quote">{html.escape(slide.quote)}</blockquote>')
    if slide.lede:
        parts.append(f'<p class="slide-lede">{html.escape(slide.lede)}</p>')

    figure = ""
    if slide.figure:
        source = output_href(current, PurePosixPath("assets") / slide.figure)
        caption = (
            f"<figcaption>{html.escape(slide.figure_caption)}</figcaption>"
            if slide.figure_caption
            else ""
        )
        figure = (
            '<figure class="slide-figure">'
            f'<img src="{html.escape(source)}" alt="{html.escape(slide.figure_alt, quote=True)}">'
            f"{caption}</figure>"
        )

    points = ""
    if slide.points:
        items = "".join(f"<li>{point}</li>" for point in slide.points)
        points = f'<ul class="slide-points">{items}</ul>'

    if figure or points:
        # A wide figure sits under the text; a standard one sits beside it.
        if slide.wide:
            body_class = "slide-body figure-wide"
            inner = points + figure
        elif figure and points:
            body_class = "slide-body has-figure"
            inner = figure + points
        else:
            body_class = "slide-body"
            inner = figure + points
        parts.append(f'<div class="{body_class}">{inner}</div>')

    if slide.note:
        parts.append(f'<p class="slide-note">{slide.note}</p>')

    if slide.actions:
        links = "".join(
            f'<a class="is-quiet" href="{html.escape(output_href(current, PurePosixPath(target)))}">'
            f"{html.escape(label)}</a>"
            if quiet
            else f'<a href="{html.escape(output_href(current, PurePosixPath(target)))}">'
            f"{html.escape(label)}</a>"
            for label, target, quiet in slide.actions
        )
        parts.append(f'<div class="slide-actions">{links}</div>')

    return (
        f'<section class="slide" id="{html.escape(slide.anchor)}">'
        f'<div class="slide-inner">{"".join(parts)}</div>'
        "</section>"
    )


def build_presentation(output_root: Path) -> None:
    """A scroll-through overview of the project, one full-height section per idea."""
    page_output = PurePosixPath("presentation/index.html")
    rail = "".join(
        f'<a href="#{html.escape(slide.anchor)}" '
        f'aria-label="{html.escape(slide.kicker, quote=True)}"></a>'
        for slide in SLIDES
    )
    sections = "".join(slide_html(page_output, index, slide) for index, slide in enumerate(SLIDES))
    body = (
        f'<nav class="deck-rail" aria-label="Sections">{rail}</nav>'
        f'<div class="deck-run">{sections}</div>'
    )
    rendered = page_html(
        output=page_output,
        title="Judgment Pack in ten sections",
        description=(
            "A scroll-through overview of the Judgment Pack Specification: the problem, the format, "
            "what conformance does and does not establish, and where the project honestly stands."
        ),
        section="concepts",
        artifact_label="Non-normative overview",
        body=body,
        body_class="deck",
    )
    write_page(output_root, page_output, rendered)


PREVIOUS_SITE_VERSION = "0.1.0-draft"


def build_superseded_spec_notice(output_root: Path) -> None:
    """Keep the previous draft's versioned URL resolvable.

    ``/spec/0.1.0-draft/`` was published and may already have been cited. The prose itself is not
    re-published here — the immutable tag holds it — but the URL must not 404, for the same reason the
    superseded schema stays served at its own ``$id``.
    """
    page_output = PurePosixPath(f"spec/{PREVIOUS_SITE_VERSION}/index.html")
    current = output_href(page_output, PurePosixPath(f"spec/{SITE_VERSION}/index.html"))
    release_notes = output_href(
        page_output, PurePosixPath(f"project/releases/{PREVIOUS_SITE_VERSION}/index.html")
    )
    current_release_notes = output_href(
        page_output, PurePosixPath(f"project/releases/{SITE_VERSION}/index.html")
    )
    versioning = output_href(page_output, PurePosixPath("project/versioning/index.html"))
    # GITHUB_ROOT already points into the *current* tag's blob tree, so the previous draft's tagged
    # source must be built from the repository URL instead.
    tag_url = f"{GITHUB_URL}/tree/v{PREVIOUS_SITE_VERSION}/spec"
    body = f"""
<h1>JPS Core {html.escape(PREVIOUS_SITE_VERSION)} is superseded</h1>
<p class="lede">This URL held the prose for JPS Core <code>{html.escape(PREVIOUS_SITE_VERSION)}</code>.
The current draft is <a href="{html.escape(current)}">Core {html.escape(SITE_VERSION)}</a>.</p>
<div class="notice notice-warning"><strong>Nothing here is normative.</strong> This page is a
signpost. The normative text of a superseded draft is the tagged source, not a rendered page on a
mutable site.</div>
<ul>
  <li><a href="{html.escape(tag_url)}" target="_blank" rel="noopener noreferrer">Tagged
  <code>v{html.escape(PREVIOUS_SITE_VERSION)}</code> source</a> — the immutable prose as published.</li>
  <li><a href="{html.escape(release_notes)}">{html.escape(PREVIOUS_SITE_VERSION)} release notes</a> —
  that draft's scope and known limitations.</li>
  <li><a href="{html.escape(current)}">Core {html.escape(SITE_VERSION)}</a> — the current draft. A
  <code>{html.escape(PREVIOUS_SITE_VERSION)}</code> pack is unchanged in representation and in
  document-conformance meaning there and needs only its <code>specVersion</code> re-declared;
  re-declaring it also opts it into that draft's evaluator semantics and confers no conformance on any
  implementation.</li>
  <li><a href="{html.escape(current_release_notes)}">{html.escape(SITE_VERSION)} release notes</a> — what
  "preserved" means for the <code>{html.escape(PREVIOUS_SITE_VERSION)}</code> schemas, which stay served at
  the <code>$id</code> each was published under. Each preserved file matches the tagged artifact in every
  byte except that <code>$id</code> member, which was re-pointed to this project's domain when the retired
  pre-publication identifier was withdrawn; the release notes publish the SHA-256 digest of both forms, and
  the immutable tag remains the authoritative record of its own bytes.</li>
  <li><a href="{html.escape(versioning)}">Versioning policy</a> — why a conformance claim is made
  against one exact version and is never inherited.</li>
</ul>
"""
    rendered = page_html(
        output=page_output,
        title=f"JPS Core {PREVIOUS_SITE_VERSION} (superseded)",
        description=(
            f"JPS Core {PREVIOUS_SITE_VERSION} is superseded by {SITE_VERSION}; where to find the "
            "tagged prose of the earlier draft."
        ),
        section="spec",
        artifact_label="Superseded",
        body=body,
    )
    write_page(output_root, page_output, rendered)


def build(output: Path, config: BuildConfig) -> None:
    global _CONFIG
    _CONFIG = config
    manifest = json.loads(repository_file("conformance/manifest.json").read_text(encoding="utf-8"))
    manifest_schema = json.loads(
        repository_file("conformance/manifest.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(manifest_schema)
    Draft202012Validator(manifest_schema).validate(manifest)
    routes = build_routes(manifest)
    prepare_output(output)
    copy_static(output)
    copy_artifacts(output)
    publish_canonical_schemas(output)
    build_markdown_pages(output, routes)
    build_schema_page(output, routes)
    build_superseded_spec_notice(output)
    build_examples(output, routes)
    build_conformance(output, routes, manifest)
    build_implementations_index(output)
    build_presentation(output)
    build_project_index(output)
    build_concepts_index(output)
    build_license(output)
    build_not_found(output)
    build_robots(output, config)
    build_sitemap(output, config)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="generated site directory (default: public/)",
    )
    parser.add_argument(
        "--environment",
        choices=("preview", "production"),
        default="preview",
        help="production enables indexability, canonical URLs, and the sitemap",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="absolute https origin, e.g. https://spec.example.org; required for production",
    )
    parser.add_argument(
        "--commit-sha",
        default="",
        help="git commit for build provenance; required for production",
    )
    parser.add_argument(
        "--build-time",
        default="",
        help="ISO-8601 UTC timestamp for sitemap lastmod; defaults to build wall-clock",
    )
    return parser.parse_args()


def _default_build_time() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_config_from_args(args: argparse.Namespace) -> BuildConfig:
    environment = args.environment
    base_url = (args.base_url or "").strip().rstrip("/")
    commit_sha = (args.commit_sha or "").strip().lower()
    if environment == "production":
        problems: list[str] = []
        parts = urlsplit(base_url)
        if not base_url:
            problems.append("--base-url is required for --environment production")
        elif parts.scheme != "https" or not parts.netloc:
            problems.append(
                f"--base-url must be an absolute https:// origin with a host, got {base_url!r}"
            )
        elif parts.query or parts.fragment:
            problems.append(f"--base-url must not carry a query or fragment: {base_url!r}")
        if not commit_sha:
            problems.append("--commit-sha is required for --environment production")
        elif not _SHA_RE.match(commit_sha):
            problems.append(f"--commit-sha is not a hex git sha: {commit_sha!r}")
        if problems:
            raise SystemExit("production build refused:\n  - " + "\n  - ".join(problems))
    build_time = (args.build_time or "").strip() or _default_build_time()
    return BuildConfig(
        environment=environment,
        base_url=base_url,
        commit_sha=commit_sha,
        build_time=build_time,
    )


if __name__ == "__main__":
    arguments = parse_args()
    configuration = build_config_from_args(arguments)
    destination_root = arguments.output.resolve()
    build(destination_root, configuration)
    print(f"Built JPS static site ({configuration.environment}) at {destination_root}")

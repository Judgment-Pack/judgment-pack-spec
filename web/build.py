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
SITE_NAME = "Judgment Pack Specification"
SITE_SHORT_NAME = "JPS"
SITE_DESCRIPTION = (
    "Judgment Pack (JPS) is an open, vendor-neutral specification for making AI judgment "
    "explicit, testable, portable, and governable separately from any runtime."
)
GITHUB_ORG_URL = "https://github.com/Judgment-Pack"
GITHUB_URL = GITHUB_ORG_URL + "/judgment-pack-spec"
GITHUB_BLOB_ROOT = GITHUB_URL + "/blob/"
GITHUB_ROOT = GITHUB_BLOB_ROOT + TAGGED_SOURCE_REF + "/"
RUNTIME_URL = GITHUB_ORG_URL + "/judgment-pack-runtime"
RUNTIME_RELEASES_URL = RUNTIME_URL + "/releases/latest"
RUNTIME_BUILD_URL = RUNTIME_URL + "/blob/main/docs/building-with-packs.md"
RUNTIME_MCP_URL = RUNTIME_URL + "/blob/main/docs/mcp-clients.md"
RUNTIME_CLAIM_URL = RUNTIME_URL + "/blob/main/CONFORMANCE.md"
DEMO_URL = GITHUB_ORG_URL + "/judgment-pack-demo"
GATEWAY_URL = GITHUB_ORG_URL + "/judgment-pack-gateway"
EXPERIMENTS_URL = GITHUB_ORG_URL + "/judgment-pack-evaluator-experiments"
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
        SITE_DESCRIPTION,
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
        source_ref="main",
    ),
    Page(
        "GOVERNANCE.md",
        PurePosixPath("project/governance/index.html"),
        "Governance",
        "How the open, vendor-neutral specification is governed and how to participate.",
        "governance",
        source_ref="main",
    ),
    Page(
        "ROADMAP.md",
        PurePosixPath("project/roadmap/index.html"),
        "Evidence-gated roadmap",
        "The evidence required before JPS can advance beyond a research preview.",
        "project",
        source_ref="main",
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
        source_ref="main",
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
        "rfcs/0010-gateway-signing-identity.md",
        PurePosixPath("rfcs/0010-gateway-signing-identity/index.html"),
        "RFC 0010: The gateway signing identity",
        "Draft proposal for the gateway's trust root: seed custody, content-binding seals, rotation, and external anchoring — every part landing outside JPS.",
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
        source_ref="main",
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
        source_ref="main",
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


_FAQ_QUESTION_RE = re.compile(r"^\*\*(Q\d+\.\s+.+?\?)\*\*\s*(.*)$")


def faq_semantic_markdown(text: str) -> str:
    """Promote numbered FAQ questions to headings in the generated site.

    The source stays compact and readable on GitHub. The HTML gets real question headings so
    humans, assistive technology, search systems, and browser agents can identify each answer as a
    self-contained passage. The FAQ page uses an H2-only table of contents, so these H3s do not turn
    its navigation into a 47-item list.
    """
    output: list[str] = []
    for line in text.splitlines():
        match = _FAQ_QUESTION_RE.match(line)
        if match is None:
            output.append(line)
            continue
        question, answer_start = match.groups()
        output.extend((f"### {question}", "", answer_start))
    return "\n".join(output)


_FAQ_HTML_RE = re.compile(
    r'(?P<heading><h3 id="q\d+[^\"]*"[^>]*>.*?</h3>)\n'
    r'(?P<answer>.*?)(?=\n<h[23](?:\s|>)|\Z)',
    re.DOTALL,
)


def faq_microdata_html(body: str, expected_count: int) -> str:
    """Wrap every complete visible FAQ answer in schema.org microdata without adding scripts."""
    wrapped = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal wrapped
        wrapped += 1
        heading = match.group("heading").replace("<h3 ", '<h3 itemprop="name" ', 1)
        answer = match.group("answer").strip()
        return (
            '<section class="faq-item" itemprop="mainEntity" itemscope '
            'itemtype="https://schema.org/Question">\n'
            + heading
            + '\n<div itemprop="acceptedAnswer" itemscope '
            'itemtype="https://schema.org/Answer"><div itemprop="text">\n'
            + answer
            + "\n</div></div>\n</section>"
        )

    result = _FAQ_HTML_RE.sub(replace, body)
    if wrapped != expected_count:
        raise ValueError(
            f"FAQ structured-data coverage mismatch: expected {expected_count}, wrapped {wrapped}"
        )
    return result


def render_markdown(
    text: str,
    source: str,
    output: PurePosixPath,
    routes: dict[str, PurePosixPath | str],
    *,
    toc_depth: str = "2-3",
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
                "toc_depth": toc_depth,
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
        ("Machine-readable guide", PurePosixPath("llms.txt")),
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
    project_scope = ""
    project_meta = ""
    if current == PurePosixPath("index.html") and config.is_production and config.base_url:
        project_scope = (
            ' itemscope itemtype="https://schema.org/Project" '
            f'itemid="{html.escape(config.base_url + "/#project", quote=True)}"'
        )
        project_meta = (
            f'<meta itemprop="alternateName" content="{SITE_SHORT_NAME}">'
            f'<meta itemprop="description" content="{html.escape(SITE_DESCRIPTION, quote=True)}">'
            f'<link itemprop="url" href="{html.escape(config.base_url + "/", quote=True)}">'
            f'<link itemprop="sameAs" href="{html.escape(GITHUB_ORG_URL, quote=True)}">'
            f'<link itemprop="license" href="{html.escape(absolute_url(config.base_url, PurePosixPath("project/license/index.html")), quote=True)}">'
        )
    project_name = (
        '<span itemprop="name">Judgment Pack</span>' if project_scope else "Judgment Pack"
    )
    return (
        f'<span class="footer-tagline"{project_scope}>'
        + project_name
        + " is an open, vendor-neutral specification for "
        "explicit and testable AI judgment."
        + project_meta
        + "</span>"
        '<span class="footer-links">'
        + " · ".join(links)
        + "</span>"
        + build_stamp
    )


def complete_page_title(title: str) -> str:
    if title == SITE_NAME:
        return f"{SITE_NAME} ({SITE_SHORT_NAME})"
    return f"{title} | {SITE_NAME}"


def concise_meta_description(description: str, limit: int = 160) -> str:
    """Normalize metadata copy and shorten it at a word boundary without changing visible prose."""
    normalized = re.sub(r"\s+", " ", description).strip()
    if len(normalized) <= limit:
        return normalized
    shortened = normalized[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:—-")
    return shortened + "…"


def page_schema_type(output: PurePosixPath) -> str:
    if output == PurePosixPath("index.html"):
        return "WebSite"
    if output == PurePosixPath("faq/index.html"):
        return "FAQPage"
    if output == PurePosixPath(f"spec/{SITE_VERSION}/index.html"):
        return "TechArticle"
    return "WebPage"


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
    # parent index is one click up. Skipped on the homepage and the 404 page. Production markup uses
    # the same visible trail as BreadcrumbList microdata; there is no hidden or divergent SEO copy.
    breadcrumb = ""
    if output.as_posix() not in {"index.html", "404.html"}:
        crumb_items: list[tuple[str, PurePosixPath]] = [
            ("Home", PurePosixPath("index.html"))
        ]
        section_crumb = SECTION_INDEX.get(section)
        if section_crumb is not None and section_crumb[1] != output:
            crumb_items.append(section_crumb)
        crumb_items.append((title, output))
        crumbs: list[str] = []
        structured_breadcrumbs = bool(config.base_url and not (noindex or config.default_noindex))
        for position, (label, target) in enumerate(crumb_items, start=1):
            last = position == len(crumb_items)
            item_scope = (
                ' itemprop="itemListElement" itemscope '
                'itemtype="https://schema.org/ListItem"'
                if structured_breadcrumbs
                else ""
            )
            if last:
                item_url = ""
                if structured_breadcrumbs:
                    item_url = (
                        f'<meta itemprop="name" content="{html.escape(label, quote=True)}">'
                        f'<link itemprop="item" href="{html.escape(absolute_url(config.base_url, target), quote=True)}">'
                        f'<meta itemprop="position" content="{position}">'
                    )
                crumb = (
                    f'<span{item_scope}><span class="crumb-current" aria-current="page"'
                    f'>{html.escape(label)}</span>{item_url}</span>'
                )
            else:
                structured_meta = ""
                if structured_breadcrumbs:
                    structured_meta = (
                        f'<meta itemprop="name" content="{html.escape(label, quote=True)}">'
                        f'<link itemprop="item" href="{html.escape(absolute_url(config.base_url, target), quote=True)}">'
                        f'<meta itemprop="position" content="{position}">'
                    )
                crumb = (
                    f'<span{item_scope}><a href="{html.escape(output_href(output, target))}">'
                    f'{html.escape(label)}</a>{structured_meta}</span>'
                )
            crumbs.append(crumb)
        separator = '<span class="crumb-sep" aria-hidden="true">/</span>'
        breadcrumb_scope = (
            ' itemprop="breadcrumb" itemscope itemtype="https://schema.org/BreadcrumbList"'
            if structured_breadcrumbs
            else ""
        )
        breadcrumb = (
            f'<nav class="breadcrumb" aria-label="Breadcrumb"{breadcrumb_scope}>'
            + separator.join(crumbs)
            + "</nav>"
        )

    effective_noindex = noindex or config.default_noindex
    canonical_link = ""
    discovery_links = ""
    social_meta = ""
    html_schema = ""
    schema_meta = ""
    full_title = complete_page_title(title)
    meta_description = concise_meta_description(description)
    if config.base_url and not effective_noindex:
        raw_location = absolute_url(config.base_url, output)
        location = html.escape(raw_location, quote=True)
        raw_logo = absolute_url(config.base_url, PurePosixPath("assets/logo.png"))
        logo = html.escape(raw_logo, quote=True)
        sitemap = html.escape(
            absolute_url(config.base_url, PurePosixPath("sitemap.xml")), quote=True
        )
        license_url = html.escape(
            absolute_url(config.base_url, PurePosixPath("project/license/index.html")), quote=True
        )
        canonical_link = f'<link rel="canonical" href="{location}">'
        discovery_links = (
            f'<link rel="sitemap" type="application/xml" href="{sitemap}">'
            f'<link rel="license" href="{license_url}">'
        )
        social_meta = (
            '<meta property="og:type" content="website">'
            f'<meta property="og:url" content="{location}">'
            f'<meta property="og:site_name" content="{SITE_NAME}">'
            '<meta property="og:locale" content="en_US">'
            f'<meta property="og:title" content="{html.escape(full_title, quote=True)}">'
            f'<meta property="og:description" content="{html.escape(meta_description, quote=True)}">'
            f'<meta property="og:image" content="{logo}">'
            '<meta property="og:image:type" content="image/png">'
            '<meta property="og:image:width" content="1024">'
            '<meta property="og:image:height" content="1024">'
            '<meta property="og:image:alt" content="Judgment Pack geometric mark">'
            '<meta name="twitter:card" content="summary">'
            f'<meta name="twitter:title" content="{html.escape(full_title, quote=True)}">'
            f'<meta name="twitter:description" content="{html.escape(meta_description, quote=True)}">'
            f'<meta name="twitter:image" content="{logo}">'
            '<meta name="twitter:image:alt" content="Judgment Pack geometric mark">'
        )
        schema_type = page_schema_type(output)
        schema_item_id = (
            config.base_url + "/#website" if schema_type == "WebSite" else raw_location + "#webpage"
        )
        html_schema = (
            f' itemscope itemtype="https://schema.org/{schema_type}" '
            f'itemid="{html.escape(schema_item_id, quote=True)}"'
        )
        name_property = "headline" if schema_type == "TechArticle" else "name"
        schema_meta = (
            f'<meta itemprop="{name_property}" content="{html.escape(title, quote=True)}">'
            f'<meta itemprop="description" content="{html.escape(meta_description, quote=True)}">'
            '<meta itemprop="inLanguage" content="en">'
            f'<link itemprop="url" href="{location}">'
            f'<link itemprop="license" href="{license_url}">'
        )
        if schema_type == "WebSite":
            schema_meta += f'<meta itemprop="alternateName" content="{SITE_SHORT_NAME}">'
        else:
            schema_meta += (
                f'<link itemprop="isPartOf" href="{html.escape(config.base_url + "/#website", quote=True)}">'
                f'<link itemprop="about" href="{html.escape(absolute_url(config.base_url, PurePosixPath("spec/0.2.0-draft/index.html")), quote=True)}">'
            )
        if schema_type == "TechArticle":
            schema_meta += (
                f'<meta itemprop="version" content="{SITE_VERSION}">'
                '<meta itemprop="creativeWorkStatus" content="Research preview">'
            )
    generator_meta = f'<meta name="generator" content="{GENERATOR_ID} {html.escape(SITE_VERSION)}">'

    return TEMPLATE.safe_substitute(
        language="en",
        html_schema=html_schema,
        page_title=html.escape(full_title),
        description=html.escape(meta_description, quote=True),
        robots_meta=(
            '<meta name="robots" content="noindex, nofollow">'
            if effective_noindex
            else '<meta name="robots" content="index, follow, max-image-preview:large">'
        ),
        base_element=base_element,
        canonical_link=canonical_link,
        discovery_links=discovery_links,
        social_meta=social_meta,
        generator_meta=generator_meta,
        schema_meta=schema_meta,
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
            + '<p class="keydef-title"><code>' + html.escape(key) + "</code></p>"
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


def home_ecosystem_html(current: PurePosixPath) -> str:
    """Render the non-normative paths from the specification into the wider project."""
    implementations = output_href(current, PurePosixPath("implementations/index.html"))
    return f"""
<section class="home-ecosystem" id="project-ecosystem" aria-labelledby="ecosystem-title">
  <div class="home-section-heading">
    <div>
      <p class="eyebrow">Open tools, demos, and research</p>
      <h2 id="ecosystem-title">Take the next step.</h2>
    </div>
    <div class="home-section-intro">
      <p>The specification stays independent. Companion repositories let you run it, inspect the
      implementation, and challenge the research without turning any tool into the standard.</p>
      <p><a href="{html.escape(GITHUB_ORG_URL)}" target="_blank" rel="noopener noreferrer">Browse the project's public repositories</a></p>
    </div>
  </div>
  <div class="ecosystem-grid">
    <article class="ecosystem-card ecosystem-card-community">
      <p class="card-kicker">Community · Slack</p>
      <h3>Bring the case the format handles badly.</h3>
      <p>Questions, criticism, implementation work, and testing feedback are welcome. The most useful
      contribution at this stage is a concrete failure or a second implementation.</p>
      <div class="card-actions">
        <a class="button button-primary" href="{html.escape(SLACK_URL)}" target="_blank" rel="noopener noreferrer">Join the Slack community</a>
      </div>
    </article>
    <article class="ecosystem-card">
      <p class="card-kicker">Reference runtime · CLI + MCP</p>
      <h3>Build and test packs locally.</h3>
      <p><code>jpack</code> validates documents, runs project-owned matrices, evaluates Core inputs,
      and exposes offline tools and method prompts over stdio MCP. Project configuration, graph
      composition, evaluation records, and reviewed-set locks are non-normative runtime features.</p>
      <div class="card-actions">
        <a href="{html.escape(RUNTIME_RELEASES_URL)}" target="_blank" rel="noopener noreferrer">Download <code>jpack</code></a>
        <a href="{html.escape(RUNTIME_URL)}" target="_blank" rel="noopener noreferrer">Runtime repository</a>
      </div>
    </article>
    <article class="ecosystem-card">
      <p class="card-kicker">Cloneable demo · Synthetic scenarios</p>
      <h3>See decisions, refusals, and handoff requests.</h3>
      <p>The browser sandbox and self-serve Slack-app source demonstrate authoring, deterministic
      evaluation, experimental composition, attested inputs, and replayable evaluation records. The
      runtime computes every disposition; the model may gather inputs, draft, and narrate, but it
      cannot change the runtime result. Use synthetic, non-sensitive material only.</p>
      <div class="card-actions">
        <a href="{html.escape(DEMO_URL)}" target="_blank" rel="noopener noreferrer">Demo repository</a>
      </div>
    </article>
    <article class="ecosystem-card">
      <p class="card-kicker">Input lineage · Research gateway</p>
      <h3>Trace a judgment to the bytes it used.</h3>
      <p>The open reference gateway signs acquired results and seals sessions. A verifier with a
      separately pinned public key can check the store against the registry obtained from the key
      holder and detect tampering, replay, and rollback after sealing. It proves byte-lineage, never
      truth, source identity, authorization, or production readiness.</p>
      <div class="card-actions">
        <a href="{html.escape(GATEWAY_URL)}" target="_blank" rel="noopener noreferrer">Gateway repository</a>
      </div>
    </article>
    <article class="ecosystem-card">
      <p class="card-kicker">Open evidence · Experiments</p>
      <h3>Inspect the methods and the negative results.</h3>
      <p>Clean-room implementations, agreement harnesses, and preregistered studies test where the
      prose is precise and where the format or surrounding trust model still fails.</p>
      <div class="card-actions">
        <a href="{html.escape(EXPERIMENTS_URL)}" target="_blank" rel="noopener noreferrer">Research repository</a>
        <a href="{html.escape(implementations)}">Implementation boundaries</a>
      </div>
    </article>
  </div>
  <p class="ecosystem-boundary"><strong>Status boundary:</strong> only the tagged Core prose,
  schemas, and named conformance artifacts define JPS. Every runtime workflow, graph, gateway,
  demo, and research format above is separately governed and non-normative.</p>
</section>
"""


def build_markdown_pages(
    output_root: Path, routes: dict[str, PurePosixPath | str]
) -> None:
    for page in PAGES:
        path = ROOT / page.source
        text = path.read_text(encoding="utf-8")
        faq_question_count = 0
        if page.source == "README.md":
            text = home_body(text)
        elif page.source == "FAQ.md":
            faq_question_count = sum(
                1 for line in text.splitlines() if _FAQ_QUESTION_RE.match(line)
            )
            text = faq_semantic_markdown(text)
        elif page.source == ".github/ISSUE_TEMPLATE/testing-feedback.md":
            text = "# Testing feedback template\n\n" + strip_front_matter(text)
        body, toc = render_markdown(
            text,
            page.source,
            page.output,
            routes,
            toc_depth="2" if page.source == "FAQ.md" else "2-3",
        )
        if page.source == "FAQ.md" and active_config().is_production:
            body = faq_microdata_html(body, faq_question_count)
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
    <h1 id="hero-title">The Judgment Pack Specification makes AI judgment explicit and testable.</h1>
    <p class="hero-lede">Judgment Pack (JPS) is an open, vendor-neutral specification for representing
    the evidence, rules, exceptions, uncertainty, escalation criteria, and evaluations behind an AI
    agent's decisions.</p>
    <div class="hero-actions">
      <a class="button button-primary" href="{html.escape(output_href(page.output, PurePosixPath('spec/0.2.0-draft/index.html')))}">Read the specification</a>
      <a class="button button-secondary" href="{html.escape(SLACK_URL)}" target="_blank" rel="noopener noreferrer">Join Slack</a>
      <a class="button button-secondary" href="{html.escape(GITHUB_ORG_URL)}" target="_blank" rel="noopener noreferrer">Browse repositories</a>
    </div>
    <p class="hero-support"><a href="{html.escape(output_href(page.output, PurePosixPath('why/index.html')))}">Why Judgment Pack?</a> · <a href="#project-ecosystem">See what you can run today</a></p>
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
</section>
{home_ecosystem_html(page.output)}"""
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
  <div><dt>Canonical schema identifier</dt><dd><code>{html.escape(str(schema.get('$id', '')))}</code></dd></div>
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
            description=(
                f"JPS {layer} conformance case {case['id']}: {case['focus']}"
            ),
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


def build_llms_txt(output_root: Path, config: BuildConfig) -> None:
    """Publish a concise, non-authoritative navigation aid for language-model consumers."""

    def guide_url(output: PurePosixPath) -> str:
        if config.base_url:
            return absolute_url(config.base_url, output)
        path = output.as_posix()
        if path == "index.html":
            return "/"
        if path.endswith("/index.html"):
            return "/" + path[: -len("index.html")]
        return "/" + path

    document = f"""# {SITE_NAME} ({SITE_SHORT_NAME})

> {SITE_DESCRIPTION}

- Current draft: `{SITE_VERSION}`
- Status: research preview; no compatibility, production-readiness, certification, truth, safety, or authorization claim
- License: Apache-2.0
- Canonical site: {guide_url(PurePosixPath("index.html"))}

This experimental file is a navigation aid, not a crawler-control policy or a source of normative
text. `robots.txt` controls crawling. The versioned Core prose and named artifacts below control JPS
conformance.

## Normative specification and artifacts

- [JPS Core {SITE_VERSION}]({guide_url(PurePosixPath("spec/0.2.0-draft/index.html"))}): normative prose for the four named conformance classes
- [Core JSON Schema]({guide_url(PurePosixPath("schema/0.2.0-draft/judgment-pack-core.schema.json"))}): normative structural schema
- [Document-conformance corpus]({guide_url(PurePosixPath("conformance/index.html"))}): carrier, structural, and semantic cases
- [Evaluation corpus]({guide_url(PurePosixPath("conformance/evaluation/index.html"))}): normative only for evaluator conformance
- [Versioning policy]({guide_url(PurePosixPath("project/versioning/index.html"))})

## Explanations and direct answers

- [Why Judgment Pack?]({guide_url(PurePosixPath("why/index.html"))})
- [Field guide]({guide_url(PurePosixPath("field-guide/index.html"))})
- [Frequently asked questions]({guide_url(PurePosixPath("faq/index.html"))})
- [How Judgment Pack compares]({guide_url(PurePosixPath("concepts/comparison/index.html"))})
- [Synthetic examples]({guide_url(PurePosixPath("examples/index.html"))})

## Project boundaries and participation

- [Implementations and claim boundaries]({guide_url(PurePosixPath("implementations/index.html"))})
- [Governance]({guide_url(PurePosixPath("project/governance/index.html"))})
- [Proposals (RFCs)]({guide_url(PurePosixPath("rfcs/index.html"))}): not normative unless accepted and landed in a release
- [Specification repository]({GITHUB_URL})
- [Public repositories]({GITHUB_ORG_URL})
- [Community Slack]({SLACK_URL})

## Interpretation boundary

A conforming document or evaluator result never establishes that evidence is true, that a pack is
authorized, that an outcome is safe or fit, or that an action may be taken. The specification,
reference runtime, demo, gateway, and research repositories have separate authority and release
boundaries.
"""
    (output_root / "llms.txt").write_text(document, encoding="utf-8")


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
        f"  <url><loc>{html.escape(location)}</loc></url>\n"
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
    governance = output_href(page_output, PurePosixPath("project/governance/index.html"))
    python_evaluator_url = EXPERIMENTS_URL + "/tree/main/python"
    gateway_spec_url = GATEWAY_URL + "/blob/main/SPEC.md"
    gateway_corpus_url = GATEWAY_URL + "/tree/main/corpus"
    body = f"""
<h1>Implementations</h1>
<p class="lede">Independent tools that implement one or more JPS conformance classes or test the
specification's semantics. A listing here is not certification, endorsement, or authority over the
specification.</p>
<div class="notice notice-info"><strong>The specification is the authority.</strong> No
implementation — including the reference runtime — is normative. A claim belongs to its claimant,
one conformance class, and one exact <code>specVersion</code>. Corpus results are required but
non-exhaustive evidence; they are not certification. Any implementation that satisfies the complete
requirements of the same class for the same exact version is equally valid. No conformance class
establishes factual grounding, authorization, safety, or operational fitness.</div>
<h2 id="available">Available implementations</h2>
<div class="card-grid">
  <article class="card">
    <p class="card-kicker">Open source · Apache-2.0 · maintained with the specification</p>
    <h2><a href="{html.escape(RUNTIME_URL)}" target="_blank" rel="noopener noreferrer">judgment-pack</a></h2>
    <p>The project's vendor-neutral reference runtime; the command it installs is <code>jpack</code>.
    It validates the carrier, structural schema, and semantic references of a JPS document against an
    immutable specification release. Its evaluator produces a disposition from supplied inputs, and
    the runtime states an evaluator-conformance claim <a href="{html.escape(RUNTIME_CLAIM_URL)}"
    target="_blank" rel="noopener noreferrer">in full in its own repository</a>. Evaluating surfaces
    stay labelled <code>experimental</code>, which reports their <em>stability</em>, never their
    conformance. A disposition never establishes truth, authorization, safety, or fitness, does not
    authorize an action, and the runtime fetches no source.</p>
    <ul>
      <li>CLI and stdio MCP surfaces for validation, schemas, fixtures, project inventory, evaluation,
      and six static method prompts.</li>
      <li>Project-owned pack matrices with informative, non-gating coverage, plus an experimental
      graph-composition workflow with its own matrices.</li>
      <li>Opt-in JSONL evaluation records and a deterministic reviewed-set lock that detects drift.
      Both are runtime conventions, not JPS audit or approval formats.</li>
    </ul>
    <div class="artifact-actions">
      <a class="button button-primary" href="{html.escape(RUNTIME_RELEASES_URL)}" target="_blank" rel="noopener noreferrer">Download latest release</a>
      <a class="button button-secondary" href="{html.escape(RUNTIME_BUILD_URL)}" target="_blank" rel="noopener noreferrer">Build with packs</a>
      <a class="button button-secondary" href="{html.escape(RUNTIME_MCP_URL)}" target="_blank" rel="noopener noreferrer">Connect an MCP client</a>
    </div>
    <p class="card-meta">Reference runtime · one implementation among peers · <a href="{html.escape(RUNTIME_URL)}" target="_blank" rel="noopener noreferrer">source</a></p>
  </article>
  <article class="card">
    <p class="card-kicker">Open source · Apache-2.0 · experimental, claims no conformance</p>
    <h2><a href="{html.escape(python_evaluator_url)}" target="_blank" rel="noopener noreferrer">clean-room Python evaluator</a></h2>
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
<h2 id="companion-projects">Companion projects</h2>
<p>These projects exercise the implementation around JPS. They are not additional JPS
implementations, and none of their interfaces or artifacts becomes part of the specification by
being listed here.</p>
<div class="card-grid">
  <article class="card">
    <p class="card-kicker">Cloneable sandbox · Slack-app source · non-normative</p>
    <h2><a href="{html.escape(DEMO_URL)}" target="_blank" rel="noopener noreferrer">judgment-pack demo</a></h2>
    <p>A browser workspace and enterprise-shaped synthetic project with the runtime pre-wired over
    MCP, plus a self-serve Slack implementation. It demonstrates pack authoring and matrices,
    evaluation and honest refusal, experimental graphs, attested inputs, project-owned evaluation
    records, and reviewed-set drift detection. The runtime computes every disposition; the model may
    gather inputs, draft, and narrate, but cannot change the runtime result. Use synthetic,
    non-sensitive material only.</p>
    <p class="card-meta">Demo material · never authorization or production guidance</p>
  </article>
  <article class="card">
    <p class="card-kicker">Open source · research preview · not integrated with the runtime</p>
    <h2><a href="{html.escape(GATEWAY_URL)}" target="_blank" rel="noopener noreferrer">open reference gateway</a></h2>
    <p>The gateway acquires JSON results from operator-configured sources, content-addresses them,
    signs version-2 receipts with Ed25519, chains them per session, and seals the final count. A
    verifier with a separately pinned public key can check a store against the gateway-held registry.
    This is a localhost-only, single-operator reference with no authentication, high availability, or
    key rotation. It proves byte-lineage, never truth, source identity, authorization, or production
    readiness.</p>
    <p class="card-meta"><a href="{html.escape(gateway_spec_url)}" target="_blank" rel="noopener noreferrer">Receipt and seal specification</a> · <a href="{html.escape(gateway_corpus_url)}" target="_blank" rel="noopener noreferrer">frozen corpus</a></p>
  </article>
</div>
<h2 id="adding-an-implementation">Adding an implementation</h2>
<p>This list is open to independent tools tested against the public conformance
artifacts. Presence here does not confer certification, official-validator status, endorsement, or
authority over the specification. A submission should say which class and exact version it claims,
if any, and link to the complete claim rather than asking this project to restate it.</p>
"""
    rendered = page_html(
        output=page_output,
        title="Implementations",
        description="Independent JPS implementations and separately governed companion tools.",
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
            "and the org chart, and making decisions is what a company does all day."
        ),
        points=(
            "<strong>Your operational know-how is your most valuable asset.</strong> Which evidence "
            "counts, which exception beats which rule, and when to ask a human. It took years to "
            "build up.",
            "<strong>Almost none of it is written down.</strong> It lives in policy documents, in "
            "past precedents, and in the heads of senior staff.",
            "<strong>Now AI is taking over the work.</strong> But this institutional know-how is the "
            "exact thing software teams struggle to hand it.",
        ),
        figure="deck-decision-engine.svg",
        figure_alt=(
            "An organization box holding policy, precedent, expertise, and hard-won exceptions, with "
            "an arrow labelled judgment leading to a box of decisions: approve, reject, escalate, "
            "hold."
        ),
        figure_caption=(
            "The arrow is institutional judgment — the most critical part, and the part nobody wrote "
            "down."
        ),
    ),
    Slide(
        anchor="black-box",
        kicker="02 — The problem",
        heading="When AI makes a mistake, nobody can explain why",
        lede=(
            "Company rules, prompt instructions, software code, and the model's own statistical "
            "guesses are mashed together into a single black box."
        ),
        points=(
            "<strong>You cannot isolate the root cause.</strong> Was the prompt unclear? Was it a "
            "software bug? Did the model hallucinate? From the outside, all three look identical.",
            "<strong>Auditors get outcomes, not policy.</strong> You can show regulators what the AI "
            "did, but not a clean document proving what it was supposed to do.",
            "<strong>Your logic is locked to one vendor.</strong> Switch AI tools or models, and "
            "engineers rebuild your business reasoning from scratch.",
            "<strong>You cannot measure improvement.</strong> Without a written baseline of rules, "
            "there is no way to test whether a prompt change made decisions better or worse.",
        ),
        figure="deck-black-box.svg",
        figure_alt=(
            "A single hatched box containing company rules, AI instructions, software code, and the "
            "model's guesswork together, with question marks pressing in from all four sides."
        ),
        figure_caption="Four different layers in one box. When an error happens, which part caused it?",
    ),
    Slide(
        anchor="coding-agents",
        kicker="03 — The diagnosis",
        heading="AI succeeds where the work checks itself",
        lede=(
            "AI works exceptionally well at writing code. Not because coding is easy, but because "
            "code comes with an automatic referee."
        ),
        points=(
            "<strong>Code grades itself.</strong> Software compiles or it fails. Automated tests pass "
            "or they break. The verdict is instant and clear.",
            "<strong>Business decisions lack a referee.</strong> Rules are spread across systems, "
            "terms mean different things to different teams, and results take months to evaluate.",
            "<strong>The fix is not just a smarter model.</strong> The missing piece is writing "
            "business judgment down in a clear format that can be checked automatically.",
        ),
        figure="deck-coding-vs-business.svg",
        figure_alt=(
            "Two panels. A coding agent gets a tick: pass or fail, in seconds — the target is "
            "explicit and the verdict is objective. A business agent gets a question mark: no verdict "
            "at all — the goal is fuzzy and feedback comes months later."
        ),
        figure_caption=(
            "The same models sit behind both panels. Only one environment can tell you whether the "
            "work was any good."
        ),
    ),
    Slide(
        anchor="knowledge-and-judgment",
        kicker="04 — The distinction",
        heading="Search finds information. Judgment makes the call.",
        lede=(
            "Most AI projects focus on search and document retrieval. Connecting AI to your documents "
            "matters, but finding information is not the same as making a decision."
        ),
        points=(
            "<strong>Search retrieves facts.</strong> It locates the relevant policy page or customer "
            "history, but it has no opinion on what to do next.",
            "<strong>Judgment decides the action.</strong> It determines which rule applies, handles "
            "exceptions, checks whether the evidence is sufficient, and escalates to a human when it "
            "is not.",
            "<strong>Search feeds judgment.</strong> Data and documents are inputs to a decision. "
            "They do not make the call on their own.",
        ),
        figure="deck-knowledge-vs-judgment.svg",
        figure_alt=(
            "Two boxes side by side. Knowledge answers what do we know — documents, databases, "
            "search results, with no opinion on what to do — and feeds Judgment, which answers so "
            "what happens: which rule applies, what overrides it, when to ask a person."
        ),
        figure_caption="Knowledge and judgment work together — but only judgment decides what happens next.",
    ),
    Slide(
        anchor="what-a-pack-is",
        kicker="05 — The proposal",
        heading="Package business judgment into a single file",
        lede=(
            "A Judgment Pack is a clean, structured file that spells out one business decision "
            "completely. No hidden AI prompts, no buried code — just clear, executable logic."
        ),
        points=(
            "<strong>It states business intent.</strong> What is being decided and why, so anyone can "
            "verify that the rules match the business goal.",
            "<strong>It handles real-world complexity.</strong> Exceptions, missing information, and "
            "the point at which a human manager must step in are all written down explicitly.",
            "<strong>The permitted outcomes are named in advance.</strong> The file lists every result "
            "the business will accept, so anything else an AI produces is visibly outside the set "
            "rather than a plausible-looking surprise.",
            "<strong>It reviews like software.</strong> Track changes over time, compare versions, "
            "and sign off on a policy update in writing.",
        ),
        figure="deck-pack-anatomy.svg",
        figure_alt=(
            "One document listing, in order: the decision, evidence, when it applies, rules, "
            "exceptions, missing facts, answers, and ask a human — each with a one-line gloss."
        ),
        figure_caption="One decision, one clean file — which is what makes business logic inspectable.",
    ),
    Slide(
        anchor="who-it-is-for",
        kicker="06 — Who it is for",
        heading="One file, three different readers",
        lede=(
            "Judgment Pack connects business policy, AI engineering, and compliance review through a "
            "single shared artifact — one each of them can actually read."
        ),
        points=(
            "<strong>Engineering and technology leaders</strong> keep institutional knowledge as an asset the company "
            "owns — written in a vendor-neutral file rather than inside one vendor's prompt, so "
            "changing the tool underneath does not mean rewriting the rules. Whether decisions hold "
            "when the <em>model</em> changes is untested, and implementations from outside this "
            "project remain an open gate.",
            "<strong>Risk, legal, and compliance teams</strong> inspect the exact logic, exception "
            "rules, and human escalation triggers before a system goes live — rather than inferring "
            "them from behaviour afterwards.",
            "<strong>The policy owner</strong> can read the rules that govern their own process without "
            "reading code, and argue with a proposed change before it ships rather than after.",
            "<strong>The common thread:</strong> the reasoning stops being a property of one tool and "
            "becomes a document all three can review.",
        ),
        figure="deck-audience-value.svg",
        figure_alt=(
            "A decision written down feeds three readers. Engineering gets logic that outlives the "
            "tool. The policy owner gets rules they can read without code. Risk and audit get what "
            "the system was supposed to do."
        ),
        figure_caption="Aligning technical execution, operational rules, and regulatory review on one artifact.",
    ),
    Slide(
        anchor="conformance",
        kicker="07 — Guardrails",
        heading="Checking the format is not the same as business approval",
        lede=(
            "The obvious risk with automated checks is that a “valid” file gets read as a “safe” "
            "business decision. The design keeps those two things firmly apart."
        ),
        points=(
            "<strong>What automated tools check:</strong> that the file is correctly formed, and that it "
            "hangs together internally — every reference resolves, identifiers are unique, and each "
            "field means what the specification says it means.",
            "<strong>What agreement between tools actually is:</strong> a requirement the "
            "specification places on conforming engines — same inputs, same result — not a check "
            "anyone runs against your file. The evidence behind it is a 20-row seed corpus that "
            "publishes its own gaps.",
            "<strong>What stays with people:</strong> whether the input facts are true, whether "
            "someone with authority signed off, and whether the policy is lawful and safe to act on "
            "here.",
            "<strong>Validation is not permission.</strong> A valid file is well formed and "
            "internally consistent. It does not mean the rules are free of contradictions — two "
            "rules that disagree are a result the engine reports, not a validation failure — and "
            "never that the logic is correct, authorised, or appropriate for a given case.",
        ),
        figure="deck-conformance-line.svg",
        figure_alt=(
            "Four filled rows — readable, well-formed, references resolve, and evaluated — above a drawn "
            "line, with "
            "is it true, is it allowed, and is it safe in outline below it. Nothing below the line is "
            "ever claimed."
        ),
        figure_caption=(
            "Keeping structural validation separate from business sign-off is what stops a green "
            "check being misread."
        ),
    ),
    Slide(
        anchor="findings",
        kicker="08 — Research findings",
        heading="What the research has shown so far",
        lede=(
            "The work tested whether business reasoning can be lifted out of AI prompts and into a "
            "standalone, portable format. Four things came back:"
        ),
        points=(
            "<strong>Logic can be separated from the model.</strong> Business rules do not have to "
            "live inside a prompt. Moved into a plain file, the exceptions and escalation rules stay "
            "explicit rather than implied.",
            "<strong>Separate implementations reach the same result.</strong> A second tool, rebuilt "
            "from the written specification alone in a different programming language, matches the "
            "reference tool on every case — byte for byte, once the specification was amended to pin "
            "the one output detail their first run showed it had left open.",
            "<strong>Not everything fits, and the misfits are informative.</strong> Encoding real "
            "policies surfaced cases the format could not hold — recorded as published negatives rather "
            "than smoothed over, and they are what the open proposals are trying to answer.",
            "<strong>Disagreement is the useful signal.</strong> Where the two implementations "
            "differed, the fault was in the written specification rather than in either program — so "
            "the specification got fixed.",
        ),
        note=(
            "Measured across 47 tests on the file format, plus 20 decision scenarios replayed through "
            "both engines. One limit, stated plainly: both implementations trace to the same "
            "maintainer, and the second was written from reference texts that already carried the "
            "first's implementation notes — so the agreement <em>corroborates</em> that the "
            "specification is precise rather than independently confirming it. Two genuinely "
            "independent implementations is the bar for calling any of this stable, and it is not met."
        ),
        figure="deck-portable-result.svg",
        figure_alt=(
            "One decision file feeds two separately built programs — the reference tool, built by the "
            "project, and an independent rebuild, built from the written spec alone. Both produce the "
            "same answer, identical character for character."
        ),
        figure_caption="Independent engines processing the same Judgment Pack reach identical results.",
    ),
    Slide(
        anchor="inputs",
        kicker="09 — Data integrity",
        heading="Verifying the inputs before the logic is applied",
        lede=(
            "A Judgment Pack defines how rules are applied. It cannot guarantee the input data is "
            "factual — and an AI that can state a fact can also invent one. That gap is handled in a "
            "separate layer."
        ),
        points=(
            "<strong>A gateway fetches the data, not the AI.</strong> A configured source is run by the "
            "gateway and its result signed on the way in — so a model can still state a made-up "
            "number, but it cannot produce a valid receipt for one.",
            "<strong>Admission is deterministic.</strong> A declared rule derives facts from the "
            "attested bytes, and an experimental gate passes only that result to the evaluator. The "
            "model supplies neither the proof nor the admitted facts.",
            "<strong>Records are tamper-evident.</strong> After a session is sealed, an altered, "
            "replayed, or truncated store can be detected against the registry obtained from the key "
            "holder rather than passing silently.",
            "<strong>Anyone can verify, and no-one gains the power to forge.</strong> Checking needs "
            "only a public key — no access to the source systems, and nothing that would let the "
            "checker mint a record. The key has to be obtained out of band.",
        ),
        note=(
            "The ceiling is stated up front and does not move: this proves <strong>that these exact "
            "bytes passed through the gateway and were not altered afterwards</strong> — never that a "
            "genuinely-named system produced them, and never that the data was right. The source name "
            "on a receipt is an operator label, not an authenticated origin. This is a "
            "single-operator reference implementation with no authentication, high availability, or "
            "key rotation. No runtime consumes it yet, and nothing in the specification defines the "
            "gateway, derivation, or admission formats — which is why the status section still lists "
            "the line as open."
        ),
        figure="deck-attested-inputs.svg",
        figure_alt=(
            "A source is fetched and signed by a gateway, producing a receipt. Receipts are linked in "
            "order and the session is sealed. A verifier checks the chain and the seal using only a "
            "public key."
        ),
        figure_caption="The acquisition proof; deterministic derivation and admission follow before evaluation.",
        actions=(
            ("Inspect the gateway", GATEWAY_URL, False),
            ("Review the input-lineage research", EXPERIMENTS_URL, True),
        ),
    ),
    Slide(
        anchor="evidence",
        kicker="10 — Open research",
        heading="We publish the results that went against us",
        quote=(
            "“An open standard earns trust by solving real problems simply, and being transparent "
            "about what is still unsolved.”"
        ),
        lede=(
            "Experiments are written down before they run, the people doing the work do not know "
            "which result is hoped for, and failures are published as visibly as successes. Three "
            "examples, none of them flattering:"
        ),
        points=(
            "<strong>Chaining decisions together closed nothing in the frame we tested.</strong> We "
            "measured it against five clauses picked by a rule fixed in advance from two published "
            "benchmark policies. Five isolated AI sessions worked them blind to the hypothesis, and "
            "every one produced a valid graph with no links at all. One went further and showed the "
            "links it could have declared pass every check while inverting the policy's meaning.",
            "<strong>A number we published was six times too high.</strong> We said a feature we were "
            "weighing would cover about 19 of 25 hard cases. Our own re-count put it at 3, hours "
            "after we had already repeated the figure in a companion proposal. We struck it out in "
            "public rather than quietly editing it away.",
            "<strong>A study's own assumption turned out to be false, and our own review caught "
            "it.</strong> It assumed two checks were independent. They were not. We rewrote the "
            "finding, relabelled the results that no longer counted, and deleted the flattering "
            "summary table.",
        ),
        note=(
            "None of this is something you have to take on trust — each is written up in full, method "
            "and data, in the "
            '<a href="https://github.com/Judgment-Pack/judgment-pack-evaluator-experiments" '
            'target="_blank" rel="noopener noreferrer">public research repository</a>. It is also why '
            "this is published as a research preview: to invite independent review and testing before "
            "a 1.0, rather than after it."
        ),
    ),
    Slide(
        anchor="status",
        kicker="11 — Project status",
        heading="What works today, and what comes next",
        lede=(
            "Current release: Core 0.2.0-draft. A practical foundation for testing and evaluation — "
            "with no stability promises yet, and not something to put in front of a consequential "
            "real decision today."
        ),
        points=(
            "<strong>Ready today:</strong> the file specification, the checks that a file is sound, "
            "and an agreed way to turn one into an answer — held in place by 47 tests on the format "
            "and 20 on the answers.",
            "<strong>Tooling:</strong> the open-source reference runtime serves the same core through "
            "a CLI and stdio MCP, walks project-owned pack matrices, and reports informative coverage. "
            "Projects can opt into JSONL evaluation records and a reviewed-set lock that makes drift "
            "visible. Those workflows are runtime conventions, not JPS audit, approval, or security "
            "formats.",
            "<strong>Demonstrations and checks:</strong> a cloneable browser sandbox and self-serve "
            "Slack-app source exercise synthetic end-to-end flows, while a second evaluator written "
            "clean-room from the specification checks the semantics. Both evaluators trace to the "
            "same maintainer, so their agreement corroborates the prose rather than independently "
            "confirming interoperability.",
            "<strong>Proposed, not standardised:</strong> linking several decisions together, choosing "
            "which decision applies, and a shared catalogue for finding them. The first has a working "
            "prototype in the reference runtime, labelled experimental for stability — composition "
            "itself has no conformance class for anyone to claim; "
            "the other two have no portable format at all, and the project expects that choosing which "
            "decision applies ends up outside the specification entirely. Each has its evidence bar "
            "written down in advance, and none has met it.",
            "<strong>Still open:</strong> the outside implementations, outside reviews, and real users "
            "that a 1.0 is gated on. A working open gateway, portable derivation prototype, and "
            "deterministic admission gate explore where inputs came from, but no runtime consumes "
            "their formats and nothing in JPS defines them.",
        ),
        actions=(
            ("Read the specification", "spec/0.2.0-draft/index.html", False),
            ("See a worked example", "examples/index.html", True),
            ("Tools, demos, and source", "implementations/index.html", True),
            ("View the roadmap", "project/roadmap/index.html", True),
        ),
    ),
    Slide(
        anchor="get-involved",
        kicker="12 — Get involved",
        heading="Help build the open standard for AI judgment",
        lede=(
            "This is a vendor-neutral specification with, today, a single maintainer and no independent "
            "contributors — which is exactly the problem. At this stage the most useful contribution is "
            "criticism. Four kinds of people would move it furthest:"
        ),
        points=(
            "<strong>Evaluation partners.</strong> Teams running AI in domains where a decision has "
            "to be defensible, willing to model real workflows as Judgment Packs alongside their "
            "existing system — not in place of it.",
            "<strong>Open-source maintainers.</strong> Engineers interested in building validators, "
            "authoring tools, SDKs, and runtime integrations — above all, an implementation this "
            "project did not write.",
            "<strong>Risk and compliance experts.</strong> Policy, legal, and audit practitioners to "
            "pressure-test exception handling, escalation, and what an auditor actually needs to see.",
            "<strong>Research collaborators.</strong> People working on data attestation, evaluation "
            "method, and decision composition — especially anyone willing to try to break a published "
            "result.",
        ),
        note=(
            "The most valuable thing anyone can send is a case this format handles badly. The "
            "roadmap is gated on evidence from outside the project, and that evidence does not exist "
            "yet."
        ),
        actions=(
            ("Read the specification", "spec/0.2.0-draft/index.html", False),
            ("Contribute on GitHub", GITHUB_URL, True),
            ("Join the Slack community", SLACK_URL, True),
            ("How to contribute", "project/contributing/index.html", True),
        ),
    ),
)


def static_svg_dimensions(filename: str) -> tuple[str, str]:
    """Read intrinsic width/height from a checked-in SVG viewBox for stable image layout."""
    source = repository_file(f"web/static/{filename}").read_text(encoding="utf-8")
    match = re.search(
        r'<svg\b[^>]*\bviewBox="[-+0-9.]+\s+[-+0-9.]+\s+([-+0-9.]+)\s+([-+0-9.]+)"',
        source,
    )
    if match is None:
        raise ValueError(f"static SVG has no numeric viewBox: {filename}")
    width, height = (f"{float(value):g}" for value in match.groups())
    return width, height


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
        width, height = static_svg_dimensions(slide.figure)
        caption = (
            f"<figcaption>{html.escape(slide.figure_caption)}</figcaption>"
            if slide.figure_caption
            else ""
        )
        figure = (
            '<figure class="slide-figure">'
            f'<img src="{html.escape(source)}" width="{width}" height="{height}" '
            f'loading="lazy" decoding="async" alt="{html.escape(slide.figure_alt, quote=True)}">'
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
        links = []
        for label, target, quiet in slide.actions:
            # An absolute target leaves the site, so it opens in a new tab and
            # never carries a referrer-bearing opener back to this page.
            if target.startswith("https://"):
                href = html.escape(target, quote=True)
                external = ' target="_blank" rel="noopener noreferrer"'
            else:
                href = html.escape(output_href(current, PurePosixPath(target)))
                external = ""
            css = ' class="is-quiet"' if quiet else ""
            links.append(f'<a{css} href="{href}"{external}>{html.escape(label)}</a>')
        parts.append(f'<div class="slide-actions">{"".join(links)}</div>')

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
        title="Judgment Pack in twelve sections",
        description=(
            "A scroll-through overview of the Judgment Pack Specification: the problem, the format, who "
            "it is for, what checking does and does not establish, and where the project honestly "
            "stands."
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
    build_llms_txt(output, config)
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
        help="ISO-8601 UTC timestamp for build provenance; defaults to build wall-clock",
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

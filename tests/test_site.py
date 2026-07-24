from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


class DocumentInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.scripts = 0
        self.h1_count = 0
        self.dangerous_attributes: list[tuple[str, str]] = []
        self.navigation_labels: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for name, value in attrs:
            normalized = (value or "").lstrip().lower()
            if name.lower().startswith("on") or normalized.startswith("javascript:"):
                self.dangerous_attributes.append((name, value or ""))
        if values.get("id"):
            self.ids.add(values["id"] or "")
        if tag == "script":
            self.scripts += 1
        if tag == "h1":
            self.h1_count += 1
        if tag in {"a", "link"} and values.get("href"):
            self.links.append(values["href"] or "")
        if tag == "img" and values.get("src"):
            self.links.append(values["src"] or "")


def inspect(path: Path) -> DocumentInspector:
    parser = DocumentInspector()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


class StaticSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="jps-site-test-")
        cls.output = Path(cls.temporary.name) / "site"
        cls.base_url = "https://spec.example.test"
        cls.commit_sha = "0123456789abcdef0123456789abcdef01234567"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "web" / "build.py"),
                "--output",
                str(cls.output),
                "--environment",
                "production",
                "--base-url",
                cls.base_url,
                "--commit-sha",
                cls.commit_sha,
                "--build-time",
                "2026-01-01T00:00:00+00:00",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_primary_pages_are_generated_without_client_javascript(self) -> None:
        expected = (
            "index.html",
            "spec/0.1.0-draft/index.html",
            "schema/index.html",
            "testing/index.html",
            "examples/index.html",
            "conformance/index.html",
            "project/index.html",
            "project/tooling/index.html",
            "project/deployment/index.html",
            "404.html",
        )
        for relative in expected:
            with self.subTest(relative=relative):
                page = self.output / relative
                self.assertTrue(page.is_file())
                document = inspect(page)
                self.assertEqual(document.scripts, 0)
                self.assertIn("main-content", document.ids)

    def test_every_local_link_resolves_and_fragment_exists(self) -> None:
        parsed_documents: dict[Path, DocumentInspector] = {}
        for page in self.output.rglob("*.html"):
            parsed_documents[page.resolve()] = inspect(page)

        for page, document in parsed_documents.items():
            self.assertEqual(
                document.scripts,
                0,
                f"{page.relative_to(self.output)} includes client JavaScript",
            )
            self.assertEqual(
                document.h1_count,
                1,
                f"{page.relative_to(self.output)} should have exactly one h1",
            )
            self.assertEqual(
                document.dangerous_attributes,
                [],
                f"{page.relative_to(self.output)} includes an event handler or javascript URL",
            )
            for link in document.links:
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc or link.startswith(("mailto:", "tel:")):
                    continue
                path = unquote(parsed.path)
                if path.startswith("/"):
                    destination = (self.output / path.lstrip("/")).resolve()
                elif path:
                    destination = (page.parent / path).resolve()
                else:
                    destination = page
                try:
                    destination.relative_to(self.output.resolve())
                except ValueError:
                    self.fail(f"{page.relative_to(self.output)} links outside the site: {link}")
                if destination.is_dir():
                    destination = destination / "index.html"
                self.assertTrue(
                    destination.is_file(),
                    f"{page.relative_to(self.output)} has broken link {link}",
                )
                if parsed.fragment and destination.suffix == ".html":
                    target = parsed_documents.get(destination.resolve()) or inspect(destination)
                    self.assertIn(
                        unquote(parsed.fragment),
                        target.ids,
                        f"{page.relative_to(self.output)} has missing fragment {link}",
                    )

    def test_raw_json_artifacts_are_copied_byte_for_byte(self) -> None:
        for directory in ("schema", "examples", "conformance"):
            for source in (ROOT / directory).rglob("*.json"):
                relative = source.relative_to(ROOT)
                published = self.output / "artifacts" / relative
                with self.subTest(relative=relative.as_posix()):
                    self.assertTrue(published.is_file())
                    self.assertEqual(published.read_bytes(), source.read_bytes())

    def test_every_manifest_case_has_a_browsable_page(self) -> None:
        manifest = json.loads(
            (ROOT / "conformance" / "manifest.json").read_text(encoding="utf-8")
        )
        for case in manifest["cases"]:
            detail = (
                self.output
                / "conformance"
                / "cases"
                / Path(case["path"]).with_suffix("")
                / "index.html"
            )
            with self.subTest(case=case["id"]):
                self.assertTrue(detail.is_file())
                content = detail.read_text(encoding="utf-8")
                self.assertIn(case["id"], content)
                for extension in case.get("supportedExtensions", []):
                    self.assertIn(extension, content)

    def test_example_pages_explain_scope_edges_and_failure_paths(self) -> None:
        index = (self.output / "examples" / "index.html").read_text(encoding="utf-8")
        self.assertIn("How to use these examples", index)
        self.assertIn("structurally and semantically conforming JPS documents", index)
        self.assertNotIn("Protoss", index)
        self.assertIn("Conforming tools", index)
        self.assertIn("For the structural baseline", index)

        expected = {
            "minimal-expense-approval": (
                "Cross-feature authoring and local-reference tracing",
                "Ordered decimal evaluation is still informative",
                "remove an outcome or evidence declaration",
            ),
            "software-change-review": (
                "Schema-versus-semantics exercises",
                "pending status matches neither rule",
                "Change a rule outcome to missing-outcome",
            ),
            "records-disposition-review": (
                "sensitive-domain-shaped example",
                "context=training-fixture",
                "Remove demo copy is only a display label",
            ),
        }
        for slug, phrases in expected.items():
            with self.subTest(example=slug):
                detail = self.output / "examples" / slug / "index.html"
                self.assertTrue(detail.is_file())
                content = detail.read_text(encoding="utf-8")
                self.assertIn("Guide to this example", content)
                self.assertIn("What this example demonstrates", content)
                self.assertIn("Good for", content)
                self.assertIn("Edges to inspect", content)
                self.assertIn("Failure paths", content)
                self.assertIn("defines no evaluator conformance class", content)
                for phrase in phrases:
                    self.assertIn(phrase, content)

    def test_firebase_configuration_is_static_only(self) -> None:
        config = json.loads((ROOT / "firebase.json").read_text(encoding="utf-8"))
        hosting = config["hosting"]
        # Multi-site: a static spec target plus a redirect-only target.
        spec = next(site for site in hosting if site.get("target") == "spec")
        self.assertEqual(spec["public"], "public")
        self.assertTrue(spec["cleanUrls"])
        self.assertNotIn("rewrites", spec)
        self.assertNotIn("redirects", spec)
        policy = spec["headers"][0]["headers"][0]["value"]
        self.assertIn("script-src 'none'", policy)
        header_keys = {header["key"] for header in spec["headers"][0]["headers"]}
        self.assertIn("Strict-Transport-Security", header_keys)
        # The redirect target 301s every path to the canonical neutral domain.
        redirect = next(site for site in hosting if site.get("target") == "redirect")
        self.assertNotIn("rewrites", redirect)
        self.assertEqual(redirect["redirects"][0]["type"], 301)
        self.assertEqual(
            redirect["redirects"][0]["destination"], "https://judgmentpack.org"
        )

    def test_implementations_page_lists_the_neutral_reference_runtime(self) -> None:
        # The Protoss CLI has been superseded by the neutral judgment-pack runtime, which owns its
        # own repository and docs; the separate on-site CLI page no longer exists.
        self.assertFalse((self.output / "cli" / "index.html").exists())
        impl = (self.output / "implementations" / "index.html").read_text(encoding="utf-8")
        self.assertIn(
            'href="https://github.com/Judgment-Pack/judgment-pack-runtime"', impl
        )
        self.assertIn(">judgment-pack</a>", impl)
        self.assertIn("vendor-neutral reference runtime", impl)
        self.assertNotIn("protoss", impl.lower())
        # The specification, not any implementation, remains the authority.
        self.assertIn("The specification is the authority.", impl)
        self.assertIn("equally valid", impl)
        self.assertNotIn("official validator", impl.lower())
        # The spec page still cites its immutable tagged source (docs use the mutable branch).
        specification = (
            self.output / "spec" / "0.1.0-draft" / "index.html"
        ).read_text(encoding="utf-8")
        self.assertIn("blob/v0.1.0-draft/spec/judgment-pack-core.md", specification)
        self.assertIn("View tagged source", specification)

    def test_published_site_is_indexable_and_nested_404_is_not(self) -> None:
        robots = (self.output / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Allow: /", robots)
        overview = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('name="robots" content="noindex, nofollow"', overview)
        not_found = (self.output / "404.html").read_text(encoding="utf-8")
        self.assertIn('<base href="/">', not_found)
        self.assertIn('name="robots" content="noindex, nofollow"', not_found)

    def test_cli_is_demoted_from_primary_nav_to_implementations(self) -> None:
        overview = (self.output / "index.html").read_text(encoding="utf-8")
        nav_start = overview.index('aria-label="Primary"')
        primary_nav = overview[nav_start : overview.index("</nav>", nav_start)]
        # A vendor product must not sit as a peer of Specification/Conformance in primary nav.
        self.assertIn(">Implementations</a>", primary_nav)
        self.assertNotIn("Protoss CLI", primary_nav)
        self.assertNotIn(">CLI</a>", primary_nav)

        implementations = (
            self.output / "implementations" / "index.html"
        ).read_text(encoding="utf-8")
        self.assertIn("<title>Implementations — JPS</title>", implementations)
        self.assertIn(">judgment-pack</a>", implementations)
        self.assertIn("implementation among peers", implementations)
        self.assertIn("This list is open", implementations)
        lowered = implementations.lower()
        # The page denies normative/official status rather than claiming it.
        self.assertIn("does not confer certification", lowered)

    def test_production_pages_carry_absolute_canonical_and_og_url(self) -> None:
        overview = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertIn(f'<link rel="canonical" href="{self.base_url}/">', overview)
        spec = (
            self.output / "spec" / "0.1.0-draft" / "index.html"
        ).read_text(encoding="utf-8")
        self.assertIn(
            f'<link rel="canonical" href="{self.base_url}/spec/0.1.0-draft/">', spec
        )
        self.assertIn(
            f'property="og:url" content="{self.base_url}/spec/0.1.0-draft/"', spec
        )

    def test_absolute_urls_never_contain_double_slashes(self) -> None:
        pattern = re.compile(
            r'(?:rel="canonical" href|property="og:url" content)="(https://[^"]+)"'
        )
        for page in self.output.rglob("*.html"):
            for url in pattern.findall(page.read_text(encoding="utf-8")):
                self.assertNotIn("//", url.split("://", 1)[1], f"double slash in {url}")
        sitemap = (self.output / "sitemap.xml").read_text(encoding="utf-8")
        for location in re.findall(r"<loc>(https://[^<]+)</loc>", sitemap):
            self.assertNotIn("//", location.split("://", 1)[1], f"double slash in {location}")

    def test_sitemap_lists_indexable_pages_and_excludes_404(self) -> None:
        sitemap = (self.output / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn(f"<loc>{self.base_url}/</loc>", sitemap)
        self.assertIn(f"<loc>{self.base_url}/spec/0.1.0-draft/</loc>", sitemap)
        self.assertIn(f"<loc>{self.base_url}/implementations/</loc>", sitemap)
        self.assertNotIn("404", sitemap)

    def test_pages_carry_neutral_generator_and_commit_provenance(self) -> None:
        overview = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertIn(
            '<meta name="generator" content="jps-site-build 0.1.0-draft">', overview
        )
        self.assertIn("Built from", overview)
        self.assertIn(self.commit_sha[:12], overview)
        generator = overview.split('name="generator" content="')[1].split('"')[0]
        self.assertNotIn("protoss", generator.lower())

    def test_schemas_are_served_at_their_canonical_id_path(self) -> None:
        cases = {
            "schema/0.1.0-draft/judgment-pack-core.schema.json": ROOT
            / "schema"
            / "judgment-pack-core.schema.json",
            "schema/0.1.0-draft/conformance/manifest.schema.json": ROOT
            / "conformance"
            / "manifest.schema.json",
        }
        for served, source in cases.items():
            with self.subTest(served=served):
                published = self.output / served
                self.assertTrue(published.is_file(), f"{served} is not served")
                # Byte-for-byte identical to the source schema, and the $id points here.
                self.assertEqual(published.read_bytes(), source.read_bytes())
                schema = json.loads(published.read_text(encoding="utf-8"))
                self.assertEqual(schema["$id"], f"https://judgmentpack.org/{served}")

    def test_noindex_pages_have_no_canonical(self) -> None:
        not_found = (self.output / "404.html").read_text(encoding="utf-8")
        self.assertNotIn('rel="canonical"', not_found)

    def test_preview_build_is_noindex_and_uncanonical(self) -> None:
        with tempfile.TemporaryDirectory(prefix="jps-preview-test-") as temporary:
            output = Path(temporary) / "site"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "web" / "build.py"),
                    "--output",
                    str(output),
                    "--environment",
                    "preview",
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Disallow: /", (output / "robots.txt").read_text(encoding="utf-8"))
            overview = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn('name="robots" content="noindex, nofollow"', overview)
            self.assertNotIn('rel="canonical"', overview)
            self.assertFalse((output / "sitemap.xml").exists())

    def test_production_build_refuses_missing_base_url(self) -> None:
        with tempfile.TemporaryDirectory(prefix="jps-guard-test-") as temporary:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "web" / "build.py"),
                    "--output",
                    str(Path(temporary) / "site"),
                    "--environment",
                    "production",
                    "--commit-sha",
                    "abcdef1",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--base-url is required", result.stderr)


    def _primary_nav(self, page_html: str) -> str:
        start = page_html.index('aria-label="Primary"')
        return page_html[start : page_html.index("</nav>", start)]

    def test_navigation_has_github_and_slack_icons(self) -> None:
        nav = self._primary_nav((self.output / "index.html").read_text(encoding="utf-8"))
        self.assertIn('class="nav-icon-svg"', nav)  # inline SVG, no external icon dependency
        self.assertIn('href="https://github.com/Judgment-Pack/judgment-pack-spec"', nav)
        self.assertIn('aria-label="View the specification on GitHub"', nav)
        self.assertIn('title="View the specification on GitHub"', nav)
        self.assertIn('href="https://join.slack.com/t/judgment-pack/shared_invite/zt-44qrd47ok-o_~Vk3BFDzsN~EGAPkeQBw"', nav)
        self.assertIn('aria-label="Join the Judgment Pack community"', nav)
        self.assertIn('title="Join the Judgment Pack community"', nav)
        self.assertGreaterEqual(nav.count('target="_blank"'), 2)
        self.assertGreaterEqual(nav.count('rel="noopener noreferrer"'), 2)

    def test_why_and_governance_are_in_primary_navigation(self) -> None:
        nav = self._primary_nav((self.output / "index.html").read_text(encoding="utf-8"))
        self.assertIn(">Why</a>", nav)
        self.assertIn(">Governance</a>", nav)
        self.assertIn(">Implementations</a>", nav)

    def test_preview_banner_is_a_collapsible_details(self) -> None:
        page = (self.output / "index.html").read_text(encoding="utf-8")
        # Native <details> disclosure — collapsible with no JavaScript, collapsed by default.
        self.assertIn('<details class="preview-banner">', page)
        self.assertNotIn('<details class="preview-banner" open>', page)
        self.assertIn('<summary class="preview-banner-summary">', page)
        self.assertIn("Research preview", page)
        self.assertIn(
            "No compatibility guarantee. Not for consequential production decisions.",
            page,
        )

    def test_mobile_nav_uses_a_jsfree_hamburger_with_icons(self) -> None:
        nav = self._primary_nav((self.output / "index.html").read_text(encoding="utf-8"))
        # A checkbox + <label for> toggle: pure CSS, no JavaScript or inline handlers.
        self.assertIn('<input type="checkbox" id="nav-menu-toggle"', nav)
        self.assertIn('<label for="nav-menu-toggle" class="nav-toggle">', nav)
        self.assertNotIn("onclick", nav)
        # The two community icons stay visible beside the hamburger (not hidden in the menu).
        actions = nav[nav.index('class="nav-actions"') :]
        self.assertEqual(actions.count('class="nav-icon"'), 2)
        self.assertIn("nav-toggle", actions)

    def test_no_javascript_anywhere_in_rendered_pages(self) -> None:
        # script-src 'none' is a hard invariant: no <script> tag or inline handler in any page.
        for path in self.output.rglob("*.html"):
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(self.output)
            self.assertNotIn("<script", text, f"{rel} contains a <script> tag")
            self.assertNotIn("onclick", text, f"{rel} contains an inline handler")
            self.assertNotIn("javascript:", text, f"{rel} contains a javascript: URL")

    def test_why_page_explains_motivation(self) -> None:
        why = (self.output / "why" / "index.html").read_text(encoding="utf-8")
        self.assertIn("<title>Why Judgment Pack? — JPS</title>", why)
        for phrase in (
            "Why coding agents work better",
            "Coding agents have compilers and tests.",
            "Knowledge helps an agent",
            "Determines applicability",
            "What Judgment Pack is not",
            "supplier invoice",
        ):
            self.assertIn(phrase, why)
        # Links to the full example and the specification, rewritten to real site routes.
        self.assertIn('href="../examples/supplier-invoice-approval/"', why)
        self.assertIn('href="../spec/0.1.0-draft/"', why)
        self.assertNotIn("Protoss", why)

    def test_protoss_appears_only_in_changelog_history(self) -> None:
        # The Protoss CLI has been superseded by the neutral judgment-pack runtime. Protoss now
        # survives only in the changelog, as the historical record of that removal.
        allowed = {"project/changelog/index.html"}
        offenders = [
            page.relative_to(self.output).as_posix()
            for page in self.output.rglob("*.html")
            if page.relative_to(self.output).as_posix() not in allowed
            and "protoss" in page.read_text(encoding="utf-8").lower()
        ]
        self.assertEqual([], offenders, f"Protoss appears outside the changelog: {offenders}")

    def test_footer_has_tagline_and_community_links(self) -> None:
        overview = (self.output / "index.html").read_text(encoding="utf-8")
        footer = overview[overview.index("<footer") :]
        self.assertIn(
            "open, vendor-neutral specification for executable and testable AI judgment", footer
        )
        self.assertIn('href="https://github.com/Judgment-Pack/judgment-pack-spec"', footer)
        self.assertIn('href="https://join.slack.com/t/judgment-pack/shared_invite/zt-44qrd47ok-o_~Vk3BFDzsN~EGAPkeQBw"', footer)
        self.assertIn(">Apache-2.0</a>", footer)

    def test_supplier_invoice_example_is_published(self) -> None:
        detail = self.output / "examples" / "supplier-invoice-approval" / "index.html"
        self.assertTrue(detail.is_file())
        content = detail.read_text(encoding="utf-8")
        self.assertIn("Guide to this example", content)
        self.assertIn("invoice", content.lower())
        index = (self.output / "examples" / "index.html").read_text(encoding="utf-8")
        self.assertIn("supplier-invoice-approval/", index)


    def test_example_json_keys_link_to_definition_cards(self) -> None:
        page = self.output / "examples" / "supplier-invoice-approval" / "index.html"
        detail = page.read_text(encoding="utf-8")
        for key in ("op", "operator", "when", "outcome", "onUnknown", "effect"):
            self.assertIn(f'<a class="jkey" href="#kd-{key}">', detail)
            self.assertIn(f'<div class="keydef" id="kd-{key}">', detail)
        # Cards carry allowed values pulled from the schema.
        self.assertIn("greater-than", detail)
        self.assertIn("evidence-present", detail)
        # Fully JS-free: script-src 'none' stays intact.
        self.assertEqual(inspect(page).scripts, 0)

    def test_schema_page_has_a_field_reference(self) -> None:
        schema = (self.output / "schema" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<dl class="field-reference">', schema)
        self.assertIn("<dt><code>op</code></dt>", schema)
        self.assertIn("<dt><code>operator</code></dt>", schema)

    def test_faq_and_proposals_are_generated_and_in_primary_nav(self) -> None:
        faq = self.output / "faq" / "index.html"
        proposals = self.output / "rfcs" / "index.html"
        self.assertTrue(faq.is_file())
        self.assertTrue(proposals.is_file())
        self.assertIn("<title>FAQ — JPS</title>", faq.read_text(encoding="utf-8"))
        nav = self._primary_nav((self.output / "index.html").read_text(encoding="utf-8"))
        self.assertIn(">FAQ</a>", nav)
        self.assertIn(">Proposals</a>", nav)

    def test_rfc_rename_is_complete_on_the_guidance_surface(self) -> None:
        # The change-proposal process is now "Request for Comments (RFC)"; the old JEP route is gone.
        process = self.output / "rfcs" / "0000-rfc-process" / "index.html"
        self.assertTrue(process.is_file())
        self.assertIn("Request for Comments", process.read_text(encoding="utf-8"))
        self.assertFalse((self.output / "project" / "jep-process" / "index.html").exists())
        governance = (
            self.output / "project" / "governance" / "index.html"
        ).read_text(encoding="utf-8")
        self.assertIn("Request for Comments (RFC)", governance)
        self.assertNotIn("Judgment Enhancement Proposal", governance)
        # The old name survives only as history (changelog) and as the rename note (RFC process).
        allowed = {"project/changelog/index.html", "rfcs/0000-rfc-process/index.html"}
        offenders = [
            page.relative_to(self.output).as_posix()
            for page in self.output.rglob("*.html")
            if "Judgment Enhancement Proposal" in page.read_text(encoding="utf-8")
            and page.relative_to(self.output).as_posix() not in allowed
        ]
        self.assertEqual([], offenders, f"stale JEP references: {offenders}")

    def test_vision_page_is_labeled_non_normative(self) -> None:
        vision = (
            self.output / "architecture" / "vision" / "index.html"
        ).read_text(encoding="utf-8")
        self.assertIn('<span class="artifact-label">Non-normative</span>', vision)
        self.assertIn("This page is not part of the", vision)
        # The layered-vision terms are allowed to appear here, clearly labeled.
        self.assertIn("Judgment Graph", vision)
        # Static SVG diagrams (JS-free) illustrate the shipped-vs-proposed split.
        self.assertEqual(vision.count('img class="diagram"'), 3)
        for name in ("shipped-vs-proposed", "three-properties", "knowledge-input"):
            svg = self.output / "assets" / f"diagram-{name}.svg"
            self.assertTrue(svg.is_file(), f"missing diagram asset: {name}")
            self.assertIn(f'src="/assets/diagram-{name}.svg"', vision)

    def test_specification_page_excludes_layered_vision_terms(self) -> None:
        # The product/runtime vision must not leak into the normative specification page.
        spec = (
            self.output / "spec" / "0.1.0-draft" / "index.html"
        ).read_text(encoding="utf-8")
        for term in ("Judgment Graph", "Composite Judgment", "Judgment Planner", "Evidence Layer"):
            self.assertNotIn(term, spec, f"vision term leaked into the spec page: {term}")

    def _internal_html_targets(self, page):
        targets = set()
        for link in inspect(page).links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or link.startswith(("mailto:", "tel:")):
                continue
            path = unquote(parsed.path)
            if not path:
                continue
            dest = (
                (self.output / path.lstrip("/"))
                if path.startswith("/")
                else (page.parent / path)
            ).resolve()
            if dest.is_dir():
                dest = dest / "index.html"
            if dest.suffix == ".html" and dest.exists():
                targets.add(dest.resolve())
        return targets

    def test_every_page_is_reachable_from_home(self) -> None:
        # Guards against orphaned pages that can only be reached by hunting through prose links.
        pages = {p.resolve() for p in self.output.rglob("*.html")}
        home = (self.output / "index.html").resolve()
        seen = {home}
        stack = [home]
        while stack:
            for dest in self._internal_html_targets(stack.pop()):
                if dest in pages and dest not in seen:
                    seen.add(dest)
                    stack.append(dest)
        orphaned = {
            p.relative_to(self.output).as_posix() for p in pages - seen
        } - {"404.html"}  # 404 is intentionally unlinked
        self.assertEqual(set(), orphaned, f"pages unreachable from home: {sorted(orphaned)}")

    def test_breadcrumbs_orient_every_page(self) -> None:
        home = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('class="breadcrumb"', home)  # the homepage needs no breadcrumb
        for page in self.output.rglob("*.html"):
            rel = page.relative_to(self.output).as_posix()
            if rel in {"index.html", "404.html"}:
                continue
            with self.subTest(page=rel):
                text = page.read_text(encoding="utf-8")
                self.assertIn('<nav class="breadcrumb"', text)
                self.assertIn(">Home</a>", text)
        vision = (
            self.output / "architecture" / "vision" / "index.html"
        ).read_text(encoding="utf-8")
        crumb = vision[
            vision.index('class="breadcrumb"') : vision.index(
                "</nav>", vision.index('class="breadcrumb"')
            )
        ]
        self.assertIn(">Home</a>", crumb)
        self.assertIn(">Concepts</a>", crumb)  # deep page nests under its section index

    def test_faq_covers_skills_tools_and_agent_integration(self) -> None:
        faq = (self.output / "faq" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="skills-tools-and-agent-integration"', faq)
        self.assertIn('id="skills-and-tools"', faq)
        # The tools/skills/packs distinction and the adversarial "skills with a new name" test.
        self.assertIn("What conclusion is justified", faq)
        self.assertIn("skills with a new name", faq)
        # The integration diagram is a static SVG (JS-free) that resolves.
        self.assertIn('src="/assets/diagram-skills-pack-flow.svg"', faq)
        self.assertTrue(
            (self.output / "assets" / "diagram-skills-pack-flow.svg").is_file()
        )
        why = (self.output / "why" / "index.html").read_text(encoding="utf-8")
        self.assertIn("faq/#skills-and-tools", why)  # the Why page points into this section

    def test_concepts_hub_links_the_learning_pages(self) -> None:
        concepts = self.output / "concepts" / "index.html"
        self.assertTrue(concepts.is_file())
        text = concepts.read_text(encoding="utf-8")
        self.assertIn("<title>Concepts — JPS</title>", text)
        for phrase in (
            "Why Judgment Pack?",
            "Architecture vision",
            "How Judgment Pack compares",
            "Field guide",
            "FAQ",
        ):
            self.assertIn(phrase, text)
        home = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertIn(">Concepts</a>", home[home.index("<footer") :])


if __name__ == "__main__":
    unittest.main()

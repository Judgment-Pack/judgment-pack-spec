from __future__ import annotations

import json
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
        subprocess.run(
            [sys.executable, str(ROOT / "web" / "build.py"), "--output", str(cls.output)],
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
            "cli/index.html",
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
        self.assertIn("Protoss CLI", index)
        self.assertIn("one available local tool", index)
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
        self.assertEqual(hosting["public"], "public")
        self.assertTrue(hosting["cleanUrls"])
        self.assertNotIn("rewrites", hosting)
        self.assertNotIn("redirects", hosting)
        policy = hosting["headers"][0]["headers"][0]["value"]
        self.assertIn("script-src 'none'", policy)

    def test_cli_page_is_explicitly_nonnormative_and_separate(self) -> None:
        content = (self.output / "cli" / "index.html").read_text(encoding="utf-8")
        overview = (self.output / "index.html").read_text(encoding="utf-8")
        specification = (
            self.output / "spec" / "0.1.0-draft" / "index.html"
        ).read_text(encoding="utf-8")
        self.assertIn("<title>Protoss CLI — JPS</title>", content)
        self.assertIn('aria-current="page">Protoss CLI</a>', content)
        self.assertIn(">Protoss CLI</a>", overview)
        self.assertNotIn(">CLI proposal</a>", content)
        self.assertNotIn("Proposed Protoss CLI", content)
        self.assertNotIn("Informative proposal", content)
        self.assertIn(
            '<span class="artifact-label">Nonnormative CLI guide</span>',
            content,
        )
        self.assertIn("public, nonnormative developer tool", content)
        self.assertIn("github.com/protossai/protoss-cli", content)
        self.assertIn("CLI behavior is nonnormative", content)
        self.assertIn("pre-1.0 interfaces may change", content)
        self.assertIn(
            "go install github.com/protossai/protoss-cli/cmd/protoss@latest",
            content,
        )
        self.assertIn(
            "go install github.com/protossai/protoss-cli/cmd/protoss@63f42d255ad79346f53efbab536af4c752db5d95",
            content,
        )
        self.assertIn("moving version query", content)
        self.assertIn("0.0.0-dev", content)
        self.assertIn("blob/main/docs/cli-design.md", content)
        self.assertIn("View current source", content)
        self.assertNotIn("blob/v0.1.0-draft/docs/cli-design.md", content)
        self.assertIn(
            "blob/v0.1.0-draft/spec/judgment-pack-core.md",
            specification,
        )
        self.assertIn("View tagged source", specification)
        self.assertIn("protoss spec validate", content)
        self.assertNotIn("protoss jps", content)
        self.assertIn("There should be no unqualified", content)
        lowered = content.lower()
        self.assertNotIn("official validator", lowered)
        self.assertNotIn("certified validator", lowered)
        self.assertNotIn("reference implementation", lowered)

    def test_published_site_is_indexable_and_nested_404_is_not(self) -> None:
        robots = (self.output / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Allow: /", robots)
        overview = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('name="robots" content="noindex, nofollow"', overview)
        not_found = (self.output / "404.html").read_text(encoding="utf-8")
        self.assertIn('<base href="/">', not_found)
        self.assertIn('name="robots" content="noindex, nofollow"', not_found)


if __name__ == "__main__":
    unittest.main()

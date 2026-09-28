"""Public demo downloads stay self-contained and exclude unreviewed Desk state."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path, PurePosixPath
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker
from test_repository import pack_conformance_diagnostics

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web"))
import build


class DemoBundleTests(unittest.TestCase):
    def test_download_rewrite_preserves_relative_link_context(self):
        archive = "https://judgmentpack.org/artifacts/demo.zip"
        rewriter = build.LocalLinkRewriter(None, "docs/topic/guide.md",
            PurePosixPath("topic/guide/index.html"), {
                "README.md": PurePosixPath("index.html"),
                "docs/topic/README.md": PurePosixPath("topic/index.html"),
                archive: PurePosixPath("artifacts/demo.zip"),
            })
        self.assertEqual(rewriter.rewrite("README.md"), "../")
        self.assertEqual(rewriter.rewrite(archive), "../../artifacts/demo.zip")
        self.assertEqual(rewriter.rewrite("https://example.test/README.md"),
            "https://example.test/README.md")

    def test_download_is_reproducible_and_self_contained(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build.copy_deal_demo(root / "first")
            build.copy_deal_demo(root / "second")
            relative = build.DEAL_DEMO_OUTPUT / (build.DEAL_DEMO_ARCHIVE + ".zip")
            first, second = root / "first" / relative, root / "second" / relative
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as bundle:
                prefix = build.DEAL_DEMO_ARCHIVE + "/"
                self.assertTrue(all(name.startswith(prefix) for name in bundle.namelist()))
                sums = bundle.read(prefix + "SHA256SUMS").decode().splitlines()
                expected_names = {prefix + "SHA256SUMS"}
                for line in sums:
                    digest, name = line.split("  ", 1)
                    expected_names.add(prefix + name)
                    self.assertEqual(hashlib.sha256(bundle.read(prefix + name)).hexdigest(), digest)
                self.assertEqual(set(bundle.namelist()), expected_names)
                config = json.loads(bundle.read(prefix + "jpack.json"))
                for pack in config["packs"].values():
                    for key in ("path", "matrix"):
                        self.assertIn(prefix + pack[key], expected_names)
                self.assertIn(prefix + "LICENSE", expected_names)
                self.assertTrue(bundle.read(prefix + "ONE-PAGE.pdf").startswith(b"%PDF-"))

    def test_only_reviewed_bytes_are_published(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            location = Path("web/demos/deal-evidence-readiness")
            shutil.copytree(ROOT / location, root / location)
            unexpected = root / build.DEAL_DEMO_SOURCE / "private-run.json"
            unexpected.write_text('{"private":"must not publish"}')
            with patch.object(build, "ROOT", root):
                build.copy_deal_demo(root / "output")
                self.assertFalse((root / "output" / build.DEAL_DEMO_OUTPUT / unexpected.name).exists())
                pack = root / build.DEAL_DEMO_SOURCE / "packs/deal-readiness.pack.json"
                pack.write_text(pack.read_text() + "\n")
                with self.assertRaisesRegex(ValueError, "checksum changed"):
                    build.copy_deal_demo(root / "modified")

    def test_manifest_cannot_publish_outside_its_bundle(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "web/demos/deal-evidence-readiness/manifest.json"
            manifest.parent.mkdir(parents=True)
            with patch.object(build, "ROOT", root):
                for name in ("../private.json", "/tmp/private.json", ".desk/run.json"):
                    with self.subTest(name=name):
                        manifest.write_text(json.dumps({"files": {name: "unused"}}))
                        with self.assertRaisesRegex(ValueError, "unsafe public demo path"):
                            build.deal_demo_files()

    def test_pack_and_captured_projections_remain_consistent(self):
        folder = ROOT / build.DEAL_DEMO_SOURCE
        pack = json.loads((folder / "packs/deal-readiness.pack.json").read_text())
        schema = json.loads((ROOT / "schema/judgment-pack-core.schema.json").read_text())
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual(pack_conformance_diagnostics(validator, pack), [])
        matrix = json.loads((folder / "packs/deal-readiness.matrix.json").read_text())
        rows = {row["id"]: row for row in matrix["cases"]}
        self.assertEqual(len(rows), 40)
        scenarios = json.loads((folder / "mapping/scenarios.json").read_text())
        projections = json.loads((folder / "mapping/expected-projections.json").read_text())
        self.assertEqual(len(scenarios), 13)
        self.assertEqual({p["key"] for p in projections}, {s["key"] for s in scenarios})
        for projection in projections:
            scenario = next(s for s in scenarios if s["key"] == projection["key"])
            row = rows["source-" + scenario["key"]]
            self.assertEqual(row["facts"], projection["facts"])
            self.assertEqual(row["evidenceAvailability"], projection["evidence"])
            self.assertEqual(row["expectedDisposition"], scenario["expectedDisposition"])
            self.assertEqual(projection["diagnosis"], scenario["diagnosis"])
            inputs = folder / "sources/readiness/scenarios" / scenario["key"]
            self.assertEqual(json.loads((inputs / "case.json").read_text()), scenario["case"])
            for name in ("crm", "quote", "security", "finance"):
                self.assertTrue(json.loads((inputs / (name + ".json")).read_text())["synthetic"])

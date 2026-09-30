"""Domain downloads preserve the public bundle and publication boundaries."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker
from test_repository import pack_conformance_diagnostics

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web"))
import build


class DomainDemoTests(unittest.TestCase):
    def test_all_bundles_are_reproducible_and_keep_the_published_sales_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for demo in build.WORKED_DEMOS:
                with self.subTest(demo=demo.slug):
                    build.copy_demo(root / "a", demo)
                    build.copy_demo(root / "b", demo)
                    relative = demo.output / (demo.archive + ".zip")
                    first = (root / "a" / relative).read_bytes()
                    self.assertEqual(first, (root / "b" / relative).read_bytes())
                    if demo.slug == "deal-evidence-readiness":
                        self.assertEqual(hashlib.sha256(first).hexdigest(),
                            "8616e63464d2609426586d398a995da4abde5fde6a87b4c0e997d3e66d559b80")
                    with zipfile.ZipFile(root / "a" / relative) as archive:
                        prefix = demo.archive + "/"
                        manifest = json.loads((ROOT / demo.source.parent / "manifest.json").read_text())
                        expected = {prefix + name for name in manifest["files"]} | {prefix + "SHA256SUMS"}
                        self.assertEqual(set(archive.namelist()), expected)
                        for line in archive.read(prefix + "SHA256SUMS").decode().splitlines():
                            digest, name = line.split("  ", 1)
                            self.assertEqual(hashlib.sha256(archive.read(prefix + name)).hexdigest(), digest)
                        self.assertTrue(archive.read(prefix + "ONE-PAGE.pdf").startswith(b"%PDF-"))
                        config = json.loads(archive.read(prefix + "jpack.json"))
                        for entry in config["packs"].values():
                            for field in ("path", "matrix"):
                                self.assertIn(prefix + entry[field], expected)

    def test_new_packs_and_source_scenarios_match_the_captured_projection_cases(self):
        validator = Draft202012Validator(
            json.loads((ROOT / "schema/judgment-pack-core.schema.json").read_text()),
            format_checker=FormatChecker())
        for demo in build.WORKED_DEMOS[1:]:
            with self.subTest(demo=demo.slug):
                root = ROOT / demo.source
                config = json.loads((root / "jpack.json").read_text())
                self.assertEqual(len(config["packs"]), 1)
                entry = next(iter(config["packs"].values()))
                pack = json.loads((root / entry["path"]).read_text())
                self.assertEqual(pack_conformance_diagnostics(validator, pack), [])
                rows = {r["id"]: r for r in json.loads((root / entry["matrix"]).read_text())["cases"]}
                scenarios = json.loads((root / "mapping/scenarios.json").read_text())
                projections = json.loads((root / "mapping/expected-projections.json").read_text())
                mapping = json.loads((root / "mapping/mapping.json").read_text())
                self.assertEqual(len(rows), 18)
                self.assertEqual(set(rows), {s["key"] for s in scenarios})
                self.assertEqual(set(rows), {p["key"] for p in projections})
                self.assertEqual(len(mapping["sources"]), 4)
                for source in mapping["sources"]:
                    self.assertEqual(source["provider"], "local-file")
                    self.assertEqual(source["kind"], "selected-file")
                for projection in projections:
                    scenario = next(s for s in scenarios if s["key"] == projection["key"])
                    row = rows[scenario["key"]]
                    self.assertEqual(row["facts"], projection["facts"])
                    self.assertEqual(row["evidenceAvailability"], projection["evidence"])
                    self.assertEqual(row["expectedDisposition"], scenario["expectedDisposition"])
                    self.assertEqual(scenario["diagnosis"], projection["diagnosis"])
                    folder = root / "sources/scenarios" / scenario["key"]
                    self.assertEqual(json.loads((folder / "case.json").read_text()), scenario["case"])
                    for source in mapping["sources"]:
                        self.assertTrue(json.loads((folder / (source["name"] + ".json")).read_text())["synthetic"])
                self.assertEqual(rows["02-missing"]["expectedDisposition"]["reasons"],
                    ["missing-required-evidence", "unknown"])

    def test_each_new_bundle_rejects_unreviewed_or_escaping_content(self):
        for demo in build.WORKED_DEMOS[1:]:
            with self.subTest(demo=demo.slug), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                folder = root / demo.source
                folder.mkdir(parents=True)
                (folder / "allowed.json").write_text('{}')
                (folder / "private.json").write_text('{"not":"reviewed"}')
                manifest = folder.parent / "manifest.json"
                digest = hashlib.sha256(b'{}').hexdigest()
                manifest.write_text(json.dumps({"files": {"allowed.json": digest}}))
                with patch.object(build, "ROOT", root):
                    build.copy_demo(root / "output", demo)
                    self.assertFalse((root / "output" / demo.output / "private.json").exists())
                    (folder / "allowed.json").write_text('{"changed":true}')
                    with self.assertRaisesRegex(ValueError, "checksum changed"):
                        build.demo_files(demo)
                    for name in ("../private.json", "/tmp/private.json", ".desk-private/state.json"):
                        manifest.write_text(json.dumps({"files": {name: digest}}))
                        with self.assertRaisesRegex(ValueError, "unsafe public demo path"):
                            build.demo_files(demo)

    def test_private_desk_state_is_absent_from_new_public_text_and_paths(self):
        for demo in build.WORKED_DEMOS[1:]:
            for relative, content in build.demo_files(demo):
                with self.subTest(demo=demo.slug, path=relative):
                    self.assertNotIn("meeting", relative.parts)
                    self.assertNotIn("state.json", relative.parts)
                    if relative.suffix not in {".json", ".md", ".csv"}:
                        continue
                    text = content.decode()
                    for private in ("/home/", "localhost:5173", ".desk-private/", "linkedin.com/in/"):
                        self.assertNotIn(private, text)

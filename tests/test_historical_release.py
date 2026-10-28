"""Immutable published anchors and real preservation/migration entry paths (Spec #259)."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from urllib.parse import urlsplit
import zipfile

from jsonschema import Draft202012Validator, FormatChecker
import test_repository as current

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/historical-compatibility"
# Trusted immutable source commits/blobs and independently verified SHA-256 anchors.
# 0.1 differs only by its previously published $id substitution; no Git history is required in CI.
ANCHORS = [{'tag': 'v0.1.0-draft',
  'commit': '80958f50c851e9809cb8036a23622391cf437c99',
  'source': 'schema/judgment-pack-core.schema.json',
  'blob': 'df791f861b9e5dc6335fcf6db426cc107287543e',
  'sourceSha256': '81f6986edc8d2bbf6f49c28a9bbec4f9054f7c72cab5a5028130e01d2e7274d8',
  'target': 'schema/judgment-pack-core-0.1.0-draft.schema.json',
  'targetSha256': 'c65c559db33d19d2f327858635266fca7fcc049fb75083a7a8d47517e27224fc',
  'id': 'https://judgmentpack.org/schema/0.1.0-draft/judgment-pack-core.schema.json'},
 {'tag': 'v0.1.0-draft',
  'commit': '80958f50c851e9809cb8036a23622391cf437c99',
  'source': 'conformance/manifest.schema.json',
  'blob': 'b53d34e48aea6c5ee24adb3b70a20353fcaf6d30',
  'sourceSha256': 'fa3f55f53712253551d6374ff3f06621e936b56c04dabd399703bbb05285c740',
  'target': 'schema/conformance-manifest-0.1.0-draft.schema.json',
  'targetSha256': 'f073bde8f6f2189edd0334c81c03fecfacf8fae2bd49305a788c75550dcbc2c5',
  'id': 'https://judgmentpack.org/schema/0.1.0-draft/conformance/manifest.schema.json'},
 {'tag': 'v0.2.0-draft',
  'commit': '0f30fd7b2c3fd7792249c8f3c5335b9e697a2c7a',
  'source': 'schema/judgment-pack-core.schema.json',
  'blob': '09672519b1575f89bda40ad4b27448f77777e1dd',
  'sourceSha256': '847910902fa202d9fb3a97062071b532f11649031c9dad32490bf191dca5b3b5',
  'target': 'schema/judgment-pack-core-0.2.0-draft.schema.json',
  'targetSha256': '847910902fa202d9fb3a97062071b532f11649031c9dad32490bf191dca5b3b5',
  'id': 'https://judgmentpack.org/schema/0.2.0-draft/judgment-pack-core.schema.json'},
 {'tag': 'v0.2.0-draft',
  'commit': '0f30fd7b2c3fd7792249c8f3c5335b9e697a2c7a',
  'source': 'conformance/manifest.schema.json',
  'blob': '41e72265c62c644b1c63d8ad6eb4960a63e7bdf7',
  'sourceSha256': 'e531a1a89f188dc12ff682263fdd6a0022bcfb6977dfeb642dd05fcbec5e0723',
  'target': 'schema/conformance-manifest-0.2.0-draft.schema.json',
  'targetSha256': 'e531a1a89f188dc12ff682263fdd6a0022bcfb6977dfeb642dd05fcbec5e0723',
  'id': 'https://judgmentpack.org/schema/0.2.0-draft/conformance/manifest.schema.json'},
 {'tag': 'v0.2.0-draft',
  'commit': '0f30fd7b2c3fd7792249c8f3c5335b9e697a2c7a',
  'source': 'conformance/evaluation/manifest.schema.json',
  'blob': '6d8adc335f62958c6d91c4d2ca64ad8994f78612',
  'sourceSha256': '142c30a33c7272cff5e85522b95d36316d2e195565bc5bef6c04a999e0da51f6',
  'target': 'schema/conformance-evaluation-manifest-0.2.0-draft.schema.json',
  'targetSha256': '142c30a33c7272cff5e85522b95d36316d2e195565bc5bef6c04a999e0da51f6',
  'id': 'https://judgmentpack.org/schema/0.2.0-draft/conformance/evaluation/manifest.schema.json'},
 {'tag': 'v0.1.0-draft',
  'commit': '80958f50c851e9809cb8036a23622391cf437c99',
  'source': 'conformance/manifest.json',
  'blob': 'eb7df5ff57ff80f2694c8913b37ff7d466edaf38',
  'target': 'tests/fixtures/historical-compatibility/0.1.0-draft-document-manifest.json',
  'targetSha256': 'a88722b34cf7b408a30fa10bcf91aef2f54285419cc60476ffcaaf37025d7f97'},
 {'tag': 'v0.2.0-draft',
  'commit': '0f30fd7b2c3fd7792249c8f3c5335b9e697a2c7a',
  'source': 'conformance/manifest.json',
  'blob': '25fc4ecb7b84f834df9c9591a0246ec2d38ef991',
  'target': 'tests/fixtures/historical-compatibility/0.2.0-draft-document-manifest.json',
  'targetSha256': 'ca3888de758e0e52632f3164bd40b41358cde19ea9ca238b50ff715b40713952'},
 {'tag': 'v0.2.0-draft',
  'commit': '0f30fd7b2c3fd7792249c8f3c5335b9e697a2c7a',
  'source': 'conformance/evaluation/manifest.json',
  'blob': '5754af3f181af9f3ae165ae141e9a22c6764ad0d',
  'target': 'tests/fixtures/historical-compatibility/0.2.0-draft-evaluation-manifest.json',
  'targetSha256': 'd2c8bf03285f5f3478f1c9074dcf0dfb2257211eba009879cd5d9f02cbb545b1'},
 {'tag': 'v0.2.0-draft',
  'commit': '0f30fd7b2c3fd7792249c8f3c5335b9e697a2c7a',
  'source': 'tests/test_repository.py',
  'blob': 'ca321e03408c4e51f4a0c674ab05802f18b35733',
  'sourceSha256': 'df577e6b8a6ab8e432c5e519a3c2e36c3b393ae060eba960bdaf1e5f55eebd72',
  'extractedDefinitions': ['DuplicateMemberError', 'strict_json_loads'],
  'target': 'tests/fixtures/historical-compatibility/tagged_carrier.py',
  'targetSha256': 'cae9672d921872cdccd9672e0865374f86aa5bbe9e4d7551fa53960445a29fab'}]

SCHEMAS = [row for row in ANCHORS if row["target"].startswith("schema/")]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def publisher():
    # Execute the actual canonical publisher without a broad site build.
    tree = ast.parse((ROOT / "web/build.py").read_text(encoding="utf-8"))
    nodes = [node for node in tree.body if
             (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and
              target.id == "CANONICAL_SCHEMA_SOURCES" for target in node.targets)) or
             (isinstance(node, ast.FunctionDef) and node.name == "publish_canonical_schemas")]
    namespace = {"ROOT": ROOT, "Path": Path, "json": json, "urlsplit": urlsplit}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "web/build.py:canonical-publisher", "exec"), namespace)
    return namespace["publish_canonical_schemas"]


def tagged_carrier():
    path = FIXTURES / "tagged_carrier.py"
    spec = importlib.util.spec_from_file_location("historical_020_carrier", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HistoricalReleaseTests(unittest.TestCase):
    def test_published_schema_and_source_fixture_byte_anchors(self):
        for row in ANCHORS:
            with self.subTest(path=row["target"]):
                path = ROOT / row["target"]
                self.assertTrue(path.is_file(), "trusted historical resource is absent")
                self.assertEqual(row["targetSha256"], hashlib.sha256(path.read_bytes()).hexdigest(),
                                 "historical resource differs from trusted published bytes")
                if "id" in row:
                    self.assertEqual(row["id"], load(row["target"])["$id"])

    def test_released_manifests_accept_only_their_historical_maturity(self):
        for version in ("0.1.0-draft", "0.2.0-draft"):
            for kind in ("document", "evaluation"):
                if version == "0.1.0-draft" and kind == "evaluation":
                    continue  # No evaluator corpus was published by that release.
                path = f"schema/conformance-{'evaluation-' if kind == 'evaluation' else ''}manifest-{version}.schema.json"
                schema = load(path)
                manifest = json.loads((FIXTURES / f"{version}-{kind}-manifest.json").read_text())
                validator = Draft202012Validator(schema, format_checker=FormatChecker())
                self.assertEqual([], list(validator.iter_errors(manifest)), f"released {version}/{kind} manifest rejected")
                for status in ("draft", "candidate", "release"):
                    changed = {**manifest, "status": status}
                    self.assertFalse(validator.is_valid(changed), "new maturity reinterprets a historical selector")

    def test_historical_selectors_refuse_current_only_profiles_and_routes(self):
        pack = json.loads((FIXTURES / "selector-only-surrogate.json").read_text())
        pack["title"] = "Hand-authored structural control"
        historical = Draft202012Validator(load("schema/judgment-pack-core-0.2.0-draft.schema.json"), format_checker=FormatChecker())
        self.assertTrue(historical.is_valid(pack), "historical control must be valid")
        variants = [{**pack, "profile": "base"}, {**pack, "escalation": {
            "triggers": ["unknown"], "routes": [{"target": {"kind": "queue", "name": "Synthetic"}}]}}]
        for changed in variants:
            self.assertFalse(historical.is_valid(changed), "historical selector admitted newer-only shape")
            migrated = {**changed, "specVersion": "0.3.0"}
            self.assertTrue(Draft202012Validator(load("schema/judgment-pack-core.schema.json"),
                                                format_checker=FormatChecker()).is_valid(migrated))
        self.assertFalse(historical.is_valid({**pack, "specVersion": "0.3.0"}), "exact selector dispatch weakened")

    def test_previous_canonical_urls_publish_the_trusted_promised_bytes(self):
        output = Path(tempfile.mkdtemp(prefix="historical-publisher-"))
        publisher()(output)
        # This complete inventory is the five canonical IDs published at immutable v0.2.0-draft.
        self.assertEqual(5, len(SCHEMAS))
        for row in SCHEMAS:
            path = output / urlsplit(row["id"]).path.lstrip("/")
            self.assertTrue(path.is_file(), f"old canonical URL disappeared: {row['id']}")
            self.assertEqual(row["targetSha256"], hashlib.sha256(path.read_bytes()).hexdigest(),
                             "canonical URL serves rewritten historical bytes")
        current_path = output / "schema/0.3.0/conformance/evaluation/manifest.schema.json"
        self.assertTrue(current_path.is_file())
        self.assertEqual((ROOT / "conformance/evaluation/manifest.schema.json").read_bytes(), current_path.read_bytes())

    def test_actual_core_archives_carry_all_preserved_resource_bytes(self):
        # No candidate Git writes: a disposable fixture repository exercises the actual builder CLI.
        fixture = Path(tempfile.mkdtemp(prefix="historical-archive-fixture-"))
        for directory in ("tools", "schema", "spec", "examples", "conformance/evaluation", "releases", "docs/releases"):
            (fixture / directory).mkdir(parents=True, exist_ok=True)
        files = [".gitattributes", "tools/build_release.py", "schema/judgment-pack-core.schema.json", "conformance/manifest.json",
                 "conformance/evaluation/manifest.json", "releases/v0.3.0-rc.1.json", "releases/v0.3.0-rc.1.md",
                 "docs/releases/v0.3.0.md", "spec/judgment-pack-core.md", *(row["target"] for row in SCHEMAS)]
        for name in files:
            shutil.copyfile(ROOT / name, fixture / name)
        for name in ("README.md", "LICENSE", "NOTICE", "CHANGELOG.md", "VERSIONING.md", "TESTING.md", "SECURITY.md"):
            (fixture / name).write_text("Hand-authored archive fixture, not release artifacts.\n")
        (fixture / "examples/control.json").write_text('{"fixture":true}\n')
        def git(*args):
            return subprocess.check_output(["git", *args], cwd=fixture, text=True, stderr=subprocess.PIPE).strip()
        git("init", "--quiet")
        git("add", ".")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-s", "-m", "Historical inventory fixture")
        commit = git("rev-parse", "HEAD")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "tag", "-a", "v0.3.0-rc.1", "-m", "Fixture only")
        built = subprocess.run([sys.executable, "tools/build_release.py", "--tag", "v0.3.0-rc.1", "--commit", commit,
                                "--output", "dist"], cwd=fixture, capture_output=True, text=True)
        self.assertEqual(0, built.returncode, built.stderr)
        prefix = "judgment-pack-spec-0.3.0-rc.1/"
        with tarfile.open(fixture / "dist/judgment-pack-spec_0.3.0-rc.1_artifacts.tar.gz") as archive:
            names = set(archive.getnames())
            for row in SCHEMAS:
                name = prefix + row["target"]
                self.assertIn(name, names, "preserved resource omitted from actual Core archive")
                self.assertEqual(row["targetSha256"], hashlib.sha256(archive.extractfile(name).read()).hexdigest())
        with zipfile.ZipFile(fixture / "dist/judgment-pack-spec_0.3.0-rc.1_artifacts.zip") as archive:
            for row in SCHEMAS:
                self.assertIn(prefix + row["target"], archive.namelist())
                self.assertEqual(row["targetSha256"], hashlib.sha256(archive.read(prefix + row["target"])).hexdigest())
        print(json.dumps({"purpose": "disposable archive inventory fixture, not release evidence", "commit": commit,
                          "tree": git("rev-parse", "HEAD^{tree}"), "fixture": fixture.name}))

    def test_selector_only_migration_counterexample_uses_actual_old_and_current_carriers(self):
        text = (FIXTURES / "selector-only-surrogate.json").read_text()
        old = tagged_carrier()
        admitted = old.strict_json_loads(text)
        self.assertTrue(Draft202012Validator(load("schema/judgment-pack-core-0.2.0-draft.schema.json"),
                                            format_checker=FormatChecker()).is_valid(admitted))
        migrated = text.replace('"0.2.0-draft"', '"0.3.0"', 1)
        with self.assertRaises(current.UnpairedSurrogateError):
            current.strict_json_loads(migrated)
        repaired = migrated.replace('\\ud800', '\\ud83d\\ude00')
        parsed = current.strict_json_loads(repaired)
        self.assertTrue(Draft202012Validator(load("schema/judgment-pack-core.schema.json"),
                                            format_checker=FormatChecker()).is_valid(parsed))
        self.assertEqual([], current.semantic_diagnostics(parsed))
        with self.assertRaises(old.DuplicateMemberError):
            old.strict_json_loads('{"x":1,"x":2}')

    def test_migration_guidance_records_the_demonstrated_exceptions(self):
        core = (ROOT / "spec/judgment-pack-core.md").read_text()
        notes = (ROOT / "releases/v0.3.0.md").read_text()
        self.assertNotIn("changes no part of the document format", core)
        self.assertNotIn("every conformance verdict of §§3.1–3.3 is the same", core)
        for text in (core, notes):
            self.assertIn("Selector-only migration is sufficient only", re.sub(r"\s+", " ", text))
            self.assertIn("\\uD800", text)
            self.assertIn("surrogate pair", text)
            self.assertIn("profile", text)
            self.assertIn("routes", text)
        site = (ROOT / "web/build.py").read_text()
        self.assertNotIn("needs only its <code>specVersion</code> re-declared", site)

    def test_policy_format_digest_inventory_is_preserved(self):
        # These separately pinned bytes are authoritative for Policy, not this Core restoration.
        manifest = load("releases/policy-v1.0.0-draft.1.json")
        for path, digest in manifest["formatDigests"].items():
            self.assertEqual(digest, "sha256:" + hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), path)

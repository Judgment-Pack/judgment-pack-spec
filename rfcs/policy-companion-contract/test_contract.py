"""Focused proposed-draft agreement/carrier checks, outside the adopted corpus."""

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from jsonschema import FormatChecker

import check_vectors
import verify as v


class ContractTests(unittest.TestCase):
    def test_static_manifest_exact_results(self):
        answers = check_vectors.run_vectors()
        self.assertEqual(len(answers), 124)
        for name, actual, expected in answers:
            with self.subTest(vector=name):
                self.assertEqual(actual, expected)
                self.assertLess(len(json.dumps(actual)), 128)
        codes = {actual.get("code") for _, actual, _ in answers}
        self.assertTrue(set(v.CODES) <= codes)

    def test_three_domain_bundles_and_declared_coverage(self):
        states, kinds = set(), set()
        for directory in sorted((v.HERE / "examples").iterdir()):
            with self.subTest(domain=directory.name):
                self.assertEqual(v.verify_bundle(directory), v.VALID)
                manifest, material, by_path = v.load_bundle(directory)
                adoption = v.read_companion(by_path[manifest["adoption"]])
                for governing in adoption["governingPolicies"]:
                    for coverage in governing["coverage"]:
                        states.add(coverage["status"])
                        kinds.update(item["kind"] for item in coverage.get("consumerElements", []))
        self.assertEqual(states, {"implemented", "manual", "awaiting-interpretation", "awaiting-implementation", "out-of-scope"})
        self.assertEqual(kinds, {"rule", "exception", "applicability", "fallback"})

    def test_historical_prototype_is_byte_frozen(self):
        pin = json.loads((v.HERE / "prototype-0.0.2-pin.json").read_bytes())
        old = v.HERE.parent / "policy-companion-prototype"
        self.assertEqual(pin["commit"], "8a56a95d555c17640d2db4984363b779536b3c2a")
        self.assertEqual(pin["proposalVersion"], "0.0.2")
        for name, digest in pin["files"].items():
            with self.subTest(path=name):
                self.assertEqual(v.spec_canon.digest_of((old / name).read_bytes()), digest)
        actual = {str(path.relative_to(old)) for path in old.rglob("*") if path.is_file() and "__pycache__" not in str(path)}
        self.assertEqual(actual, set(pin["files"]))

    def test_source_consumer_narrative_and_review_bytes_preserved(self):
        old = v.HERE.parent / "policy-companion-prototype/examples"
        for directory in sorted((v.HERE / "examples").iterdir()):
            for name in ("source.txt", "consumer-pack.json", "narrative.txt", "interpretation.txt"):
                with self.subTest(domain=directory.name, role=name):
                    self.assertEqual((directory / name).read_bytes(), (old / directory.name / name).read_bytes())

    def test_discovery_matches_retained_record_and_cli(self):
        retained = json.loads((v.HERE / "capabilities.json").read_bytes())
        self.assertEqual(retained, v.CAPABILITY)
        self.assertEqual(retained["formatVersions"], ["1.0.0"])
        self.assertEqual(retained["maturity"], "proposed-draft")
        self.assertIn("live-authority", retained["excludes"])
        self.assertIn("independent-interoperability-evidence", retained["excludes"])
        completed = subprocess.run([sys.executable, str(v.HERE / "verify.py"), "--capabilities"], capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(json.loads(completed.stdout), retained)

    def test_cli_refusal_does_not_echo_retained_input_or_paths(self):
        manifest = json.loads((v.HERE / "examples/data-access/fixture.json").read_bytes())
        secret = b"fictional-private-title-must-not-be-echoed"
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for entry in manifest["materials"]:
                raw = (v.HERE / "examples/data-access" / entry["path"]).read_bytes()
                if entry["path"] == "narrative.txt":
                    raw += secret  # Intentionally stale declared exact hash/length.
                (directory / entry["path"]).write_bytes(raw)
            (directory / "fixture.json").write_text(json.dumps(manifest))
            completed = subprocess.run([sys.executable, str(v.HERE / "verify.py"), str(directory)], capture_output=True, check=False)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, b'{"status":"refused","code":"reference-mismatch"}\n')
        self.assertEqual(completed.stderr, b"")
        self.assertNotIn(secret, completed.stdout)
        self.assertNotIn(temporary.encode(), completed.stdout)

    def test_local_fixture_carrier_refuses_paths_unknown_fields_and_missing_files(self):
        original = json.loads((v.HERE / "examples/data-access/fixture.json").read_bytes())
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for mutation, code in ((lambda d: d["materials"][0].update(path="../outside.txt"), "invalid-carrier"),
                                   (lambda d: d.update(approved=True), "invalid-carrier"),
                                   (lambda d: None, "missing-material")):
                manifest = copy.deepcopy(original)
                mutation(manifest)
                (directory / "fixture.json").write_text(json.dumps(manifest))
                self.assertEqual(v.verify_bundle(directory), {"status": "refused", "code": code})
            symlink = directory / "narrative.txt"
            symlink.symlink_to(v.HERE / "examples/data-access/narrative.txt")
            (directory / "fixture.json").write_text(json.dumps(original))
            self.assertEqual(v.verify_bundle(directory), {"status": "refused", "code": "invalid-carrier"})

    def test_cli_refuses_nul_material_path_with_bounded_json(self):
        manifest = json.loads((v.HERE / "examples/data-access/fixture.json").read_bytes())
        manifest["materials"][0]["path"] = "fictional-private\x00path.txt"
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "fixture.json").write_text(json.dumps(manifest))
            completed = subprocess.run([sys.executable, str(v.HERE / "verify.py"), str(directory)], capture_output=True, check=False)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, b'{"status":"refused","code":"invalid-carrier"}\n')
        self.assertEqual(completed.stderr, b"")

    def test_vector_carrier_nul_paths_have_safe_results_and_no_cli_traceback(self):
        expected = {"status": "refused", "code": "invalid-carrier"}
        source = {"path": "vectors/private\x00transport.bin"}
        case = {"id": "nul-transport", "document": {"path": "examples/data-access/policy.json"},
                "materials": [{"source": source, "content": v.identity(b"x", "text/plain")}], "expected": expected}
        self.assertEqual(check_vectors.case_result(case), expected)
        root_nul = {**case, "document": source, "materials": []}
        self.assertEqual(check_vectors.case_result(root_nul), expected)
        manifest = {"vectorSuiteVersion": "1", "maturity": "proposed-draft", "synthetic": True, "cases": [case]}
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(json.dumps(manifest))
            completed = subprocess.run([sys.executable, str(v.HERE / "check_vectors.py"), str(path)], capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, b'{"status":"matched","cases":1,"maturity":"proposed-draft"}\n')
        self.assertEqual(completed.stderr, b"")

    def test_failed_registration_is_atomic(self):
        material = {}
        first = v.identity(b"x", "text/plain")
        v.register_material(first, b"x", material)
        before = copy.deepcopy(material)
        with self.assertRaises(v.ContractError) as caught:
            v.register_material(first, b"changed", material)
        self.assertEqual(caught.exception.code, "reference-mismatch")
        self.assertEqual(material, before)
        wrong_type = v.identity(b"x", "text/markdown")
        self.assertEqual(v.result(lambda: v.resolve(wrong_type, material)), {"status": "refused", "code": "reference-mismatch"})

    def test_schema_version_pattern_is_exact_without_trailing_newline_alias(self):
        raw = (v.HERE / "examples/data-access/policy.json").read_bytes()
        manifest, material, _ = v.load_bundle(v.HERE / "examples/data-access")
        document = v.read_companion(raw)
        for version in ("0.0.0", "42.7.999", "9" * 252 + ".0.0"):
            document["version"] = version
            v.check_schema("policy", document)
        for version in ("1x0x0", "1.0.0\n", "01.0.0", "1.0.0+build"):
            document["version"] = version
            self.assertEqual(v.result(lambda: v.check_schema("policy", document)), {"status": "refused", "code": "invalid-document"})

    def test_uri_matrix_covers_policy_and_consuming_core_without_global_override(self):
        manifest, material, by_path = v.load_bundle(v.HERE / "examples/data-access")
        base = v.read_companion(by_path[manifest["policy"]])
        cases = json.loads((v.HERE / "vectors/manifest.json").read_bytes())["cases"]
        count = 0
        for case in cases:
            if not case["id"].startswith("uri-"):
                continue
            count += 1
            document = v.read_companion(check_vectors.source_bytes(case["document"], v.HERE))
            policy = copy.deepcopy(base)
            policy["id"] = document["consumer"]["id"] if document["kind"] == "governing-adoption" else document["id"]
            with self.subTest(vector=case["id"], root="policy"):
                self.assertEqual(v.result(lambda: v.check_policy(policy, material)), case["expected"])
            if document["kind"] == "governing-adoption":
                reference = document["consumer"]["content"]
                entry = next(item for item in case["materials"] if item["content"] == reference)
                pack = v.strict_json(check_vectors.source_bytes(entry["source"], v.HERE))
                expected = v.VALID if case["expected"]["status"] == "valid" else {"status": "refused", "code": "invalid-consumer"}
                with self.subTest(vector=case["id"], root="consuming-pack"):
                    self.assertEqual(v.result(lambda: v.check_schema("core", pack)), expected)
        self.assertEqual(count, 21)  # Twenty added cases plus the original relative-ID refusal.
        self.assertIsNot(FormatChecker().checkers["uri"][0], v.candidate_uri)

    def test_uri_adoption_vectors_preserve_every_pack_byte_except_id_token(self):
        original = (v.HERE / "examples/data-access/consumer-pack.json").read_bytes()
        original_id = json.dumps(json.loads(original)["id"]).encode()
        cases = json.loads((v.HERE / "vectors/manifest.json").read_bytes())["cases"]
        count = 0
        for case in cases:
            if not case["id"].startswith("uri-"):
                continue
            document = v.read_companion(check_vectors.source_bytes(case["document"], v.HERE))
            if document["kind"] != "governing-adoption":
                continue
            count += 1
            entry = next(item for item in case["materials"] if item["content"] == document["consumer"]["content"])
            retained = check_vectors.source_bytes(entry["source"], v.HERE)
            new_id = json.dumps(document["consumer"]["id"]).encode()
            with self.subTest(vector=case["id"]):
                self.assertEqual(retained.count(new_id), 1)
                self.assertEqual(retained.replace(new_id, original_id, 1), original)
        self.assertEqual(count, 7)


if __name__ == "__main__":
    unittest.main()

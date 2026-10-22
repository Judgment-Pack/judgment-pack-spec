from __future__ import annotations

import copy
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("policy_release", ROOT / "tools/build_release.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
TAG = "policy-v1.0.0-draft.1"
VERSION = "1.0.0-draft.1"


class PolicyReleaseTests(unittest.TestCase):
    def accepted_tree(self, directory):
        root = Path(directory)
        for name in (*BUILDER.POLICY_BUNDLE_PATHS, f"releases/{TAG}.md", f"releases/{TAG}.json"):
            source, target = ROOT / name, root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copyfile(source, target)
        rfc = root / "rfcs/0023-policy-companion.md"
        rfc.write_text(rfc.read_text().replace("- Status: Review", "- Status: Accepted"))
        return root

    def test_exact_draft_namespace_and_refused_aliases(self):
        self.assertEqual(BUILDER.release_version(TAG), VERSION)
        for tag in ("policy-v1.0.0", "policy-v1.0.0-rc.1", "policy-v01.0.0-draft.1",
                    "policy-v1.0.0-draft.01", "policy-v1.0.0-draft.1+local",
                    "policy-v1.0.0-draft.1\n", "policy-1.0.0-draft.1"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                BUILDER.release_version(tag)

    def test_review_state_cannot_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.accepted_tree(temporary)
            rfc = root / "rfcs/0023-policy-companion.md"
            rfc.write_text(rfc.read_text().replace("- Status: Accepted", "- Status: Review"))
            with self.assertRaisesRegex(ValueError, "acceptance at draft maturity"):
                BUILDER.validate_policy_artifacts(VERSION, TAG, root)

    def test_release_metadata_refuses_mismatch_and_changed_format(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.accepted_tree(temporary)
            BUILDER.validate_policy_artifacts(VERSION, TAG, root)
            path = root / "releases" / f"{TAG}.json"
            original = path.read_text()
            for key, value in (("tag", "policy-v9.0.0-draft.1"), ("maturity", "stable"),
                               ("formatVersion", "1.0.1"), ("extra", True)):
                metadata = json.loads(original)
                metadata[key] = value
                path.write_text(json.dumps(metadata))
                with self.subTest(key=key), self.assertRaises(ValueError):
                    BUILDER.validate_policy_artifacts(VERSION, TAG, root)
            path.write_text(original)
            schema = root / "schema/policy/1.0.0/policy.schema.json"
            schema.write_text(schema.read_text() + " ")
            with self.assertRaisesRegex(ValueError, "format bytes"):
                BUILDER.validate_policy_artifacts(VERSION, TAG, root)

    def test_corpus_file_changes_and_prior_identity_conflicts_refuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.accepted_tree(temporary)
            source = root / BUILDER.POLICY_ROOT / "examples/data-access/narrative.txt"
            raw = source.read_bytes()
            source.write_bytes(raw + b" ")
            with self.assertRaisesRegex(ValueError, "corpus identity"):
                BUILDER.validate_policy_artifacts(VERSION, TAG, root)
            source.write_bytes(raw)
            metadata = json.loads((root / "releases" / f"{TAG}.json").read_text())
            metadata["formatDigests"]["spec/policy.md"] = "sha256:" + "0" * 64
            (root / "releases/policy-v1.0.0-draft.0.json").write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError, "earlier release record"):
                BUILDER.validate_policy_artifacts(VERSION, TAG, root)

    def test_policy_corpus_inventory_refuses_unlisted_owned_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.accepted_tree(temporary)
            BUILDER.validate_policy_artifacts(VERSION, TAG, root)
            orphan = root / BUILDER.POLICY_ROOT / "vectors/documents/unlisted.json"
            orphan.write_text("{}")
            with self.assertRaisesRegex(ValueError, "corpus identity"):
                BUILDER.validate_policy_artifacts(VERSION, TAG, root)
            orphan.unlink()
            BUILDER.validate_policy_artifacts(VERSION, TAG, root)

    def test_proposed_draft_acceptance_matches_the_release_gate(self):
        self.assertIn("- Status: Accepted\n", (ROOT / "rfcs/0023-policy-companion.md").read_text())
        BUILDER.validate_policy_artifacts(VERSION, TAG)

    def test_tagged_history_cannot_be_rewritten_through_worktree_records(self):
        current = json.loads((ROOT / "releases" / f"{TAG}.json").read_text())
        old = copy.deepcopy(current)
        old["schemas"]["policy"] = "https://invalid.example/changed-schema"
        with patch.object(BUILDER, "git", side_effect=["policy-v1.0.0-draft.0", json.dumps(old)]):
            with self.assertRaisesRegex(ValueError, "immutable tagged"):
                BUILDER.validate_policy_history(TAG)

    def test_policy_validation_routes_without_core_version_repinning(self):
        commit = "a" * 40
        def git(*args):
            if args[0] == "rev-parse":
                return commit
            if args[0] in ("tag", "status"):
                return ""
            raise AssertionError(args)
        with patch.object(BUILDER, "git", side_effect=git), \
             patch.object(BUILDER, "validate_policy_artifacts") as policy, \
             patch.object(BUILDER, "validate_artifacts") as core:
            self.assertEqual(BUILDER.validate(TAG, commit), VERSION)
            policy.assert_called_once_with(VERSION, TAG)
            core.assert_not_called()
        with patch.object(BUILDER, "git", side_effect=lambda *args: "b" * 40 if "HEAD^{commit}" in args else commit), \
             patch.object(BUILDER, "validate_policy_artifacts"):
            with self.assertRaisesRegex(ValueError, "not checked out"):
                BUILDER.validate(TAG, commit)

    def test_shared_archiver_carries_self_contained_policy_artifacts(self):
        # Capture the uncommitted candidate in a temporary index/tree; create no commit or tag.
        with tempfile.TemporaryDirectory() as temporary:
            index = Path(temporary) / "index"
            env = dict(os.environ, GIT_INDEX_FILE=str(index))
            subprocess.run(["git", "read-tree", "HEAD"], cwd=ROOT, env=env, check=True)
            subprocess.run(["git", "add", "-A"], cwd=ROOT, env=env, check=True)
            tree = subprocess.check_output(["git", "write-tree"], cwd=ROOT, env=env, text=True).strip()
            output = Path(temporary) / "dist"
            with patch.object(BUILDER, "validate", return_value=VERSION):
                artifacts = BUILDER.build(TAG, tree, output)
            prefix = f"judgment-pack-policy-{VERSION}/"
            required = ["spec/policy.md", "schema/policy/1.0.0/policy.schema.json",
                        "conformance/policy/1.0.0/vectors/manifest.json",
                        "conformance/policy/1.0.0/verify.py", "tools/dialect_verify.py",
                        "rfcs/policy-companion-contract/verify.py", f"releases/{TAG}.json"]
            with tarfile.open(artifacts[0]) as archive:
                members = set(archive.getnames())
                file_members = {item.name for item in archive.getmembers() if item.isfile()}
                for name in required:
                    self.assertIn(prefix + name, members)
                self.assertNotIn(prefix + "conformance/evaluation/manifest.json", members)
                self.assertNotIn(prefix + "conformance/dialect/manifest.json", members)
                unpacked = Path(temporary) / "unpacked"
                archive.extractall(unpacked, filter="data")
            with zipfile.ZipFile(artifacts[1]) as archive:
                self.assertEqual(file_members,
                                 set(archive.namelist()) - {name for name in archive.namelist() if name.endswith("/")})
            packaged = unpacked / prefix
            checked = subprocess.run([os.sys.executable, "conformance/policy/1.0.0/check_vectors.py"],
                                     cwd=packaged, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(checked.stdout), {"status": "matched", "cases": 124, "maturity": "draft"})
            checksums = artifacts[2].read_text().splitlines()
            for artifact, line in zip(artifacts[:2], checksums):
                self.assertEqual(line, BUILDER.sha256(artifact) + "  " + artifact.name)
            core_paths = BUILDER.bundle_paths("v0.2.0-draft", tree)
            core_archive = subprocess.check_output(["git", "archive", "--format=tar", tree, *core_paths], cwd=ROOT)
            with tarfile.open(fileobj=io.BytesIO(core_archive)) as archive:
                core = set(archive.getnames())
            self.assertIn("conformance/evaluation/manifest.json", core)
            self.assertFalse(any(name.startswith(("schema/policy/", "conformance/policy/")) for name in core))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_release", ROOT / "tools" / "build_release.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load release builder")
BUILD_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD_RELEASE)


class ReleaseBuilderTests(unittest.TestCase):
    def test_release_version_accepts_exact_semver_tags(self) -> None:
        self.assertEqual(BUILD_RELEASE.release_version("v0.1.0-draft"), "0.1.0-draft")
        self.assertEqual(BUILD_RELEASE.release_version("v1.2.3-rc.1"), "1.2.3-rc.1")
        self.assertEqual(BUILD_RELEASE.release_version("v1.2.3-0"), "1.2.3-0")
        self.assertEqual(BUILD_RELEASE.release_version("v1.2.3-alpha.1"), "1.2.3-alpha.1")
        # Alphanumeric prerelease ids may contain leading zeroes (SemVer §9).
        self.assertEqual(BUILD_RELEASE.release_version("v1.2.3-01alpha"), "1.2.3-01alpha")

    def test_release_version_rejects_ambiguous_tags(self) -> None:
        for tag in (
            "0.1.0",
            "v0.1",
            "v00.1.0",
            "v0.1.0+local",
            "main",
            "v1.2.3-01",
            "v1.2.3-alpha.01",
        ):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                BUILD_RELEASE.release_version(tag)

    def test_artifact_validation_accepts_the_current_version(self) -> None:
        manifest = json.loads(
            (ROOT / "conformance" / "manifest.json").read_text(encoding="utf-8")
        )
        version = manifest["specVersion"]
        BUILD_RELEASE.validate_artifacts(version, f"v{version}")

    def test_artifact_validation_pins_the_evaluation_corpus(self) -> None:
        # An evaluator-conformance claim binds to the corpus published for the exact specVersion
        # (Core §§3.4, 3.4.1), so a tag whose evaluation manifest still names the previous version
        # must not build even when every document artifact is correctly re-pinned.
        for stale in ("specVersion", "suiteVersion"):
            with self.subTest(member=stale), tempfile.TemporaryDirectory() as directory:
                root = self._release_tree(Path(directory), "0.3.0-draft")
                evaluation_path = root / "conformance" / "evaluation" / "manifest.json"
                evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
                evaluation[stale] = "0.2.0-draft"
                evaluation_path.write_text(json.dumps(evaluation), encoding="utf-8")
                with self.assertRaises(ValueError) as raised:
                    BUILD_RELEASE.validate_artifacts(
                        "0.3.0-draft", "v0.3.0-draft", root=root
                    )
                self.assertIn("evaluation corpus", str(raised.exception))
                # The same tree validates once the corpus is re-pinned.
                evaluation[stale] = "0.3.0-draft"
                evaluation_path.write_text(json.dumps(evaluation), encoding="utf-8")
                BUILD_RELEASE.validate_artifacts("0.3.0-draft", "v0.3.0-draft", root=root)

    def test_validate_requires_head_to_be_the_release_commit(self) -> None:
        # Artifacts are validated from the worktree and archived from the commit, so a release built
        # while HEAD points elsewhere would ship a tree nobody validated.
        manifest = json.loads(
            (ROOT / "conformance" / "manifest.json").read_text(encoding="utf-8")
        )
        version = manifest["specVersion"]
        tag = f"v{version}"
        commit = "a" * 40
        original = BUILD_RELEASE.git
        try:
            for head, expected in ((commit, None), ("b" * 40, "not checked out")):
                with self.subTest(head=head):
                    def fake_git(*arguments: str, head: str = head) -> str:
                        if arguments[:2] == ("rev-parse", "--verify"):
                            return head if arguments[2] == "HEAD^{commit}" else commit
                        if arguments[0] == "status":
                            return ""
                        raise AssertionError(f"unexpected git call: {arguments}")

                    BUILD_RELEASE.git = fake_git
                    if expected is None:
                        self.assertEqual(BUILD_RELEASE.validate(tag, commit), version)
                    else:
                        with self.assertRaises(ValueError) as raised:
                            BUILD_RELEASE.validate(tag, commit)
                        self.assertIn(expected, str(raised.exception))
        finally:
            BUILD_RELEASE.git = original

    def test_release_bundle_leaves_staged_evaluation_rows_out(self) -> None:
        # The bundle is a `git archive` of BUNDLE_PATHS, and those include conformance/ whole. Rows
        # staged for a later suiteVersion are in no corpus, so .gitattributes marks their directory
        # export-ignore: no bundle carries a staged row, whatever is staged when a release is cut.
        # The released corpus beside them must stay in the bundle, so it is checked as the control.
        self.assertIn("conformance", BUILD_RELEASE.BUNDLE_PATHS)
        staged_root = ROOT / "conformance" / "evaluation" / "staged"
        staged_root_posix = staged_root.relative_to(ROOT).as_posix()
        staged = sorted(
            path.relative_to(ROOT).as_posix() for path in staged_root.rglob("*") if path.is_file()
        )
        self.assertTrue(staged, "nothing is staged; this test can go with the directory")
        evaluation = ROOT / "conformance" / "evaluation"
        released = sorted(
            path.relative_to(ROOT).as_posix()
            for path in [
                evaluation / "manifest.json",
                evaluation / "manifest.schema.json",
                *(evaluation / "packs").glob("*.json"),
            ]
        )
        # An attribute on a path says nothing about its ancestors, and `git archive` drops a whole
        # directory that is export-ignored: a rule on conformance/evaluation would leave the
        # released manifest "unspecified" and still omit it. So the ancestors are part of the control.
        ancestors = ["conformance", "conformance/evaluation", "conformance/evaluation/packs"]
        try:
            completed = subprocess.run(
                ["git", "check-attr", "export-ignore", "--", *staged, *released, *ancestors],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git cannot read attributes here: {error}")
        attributes = dict(
            line.rsplit(": export-ignore: ", 1) for line in completed.stdout.splitlines()
        )
        for path in staged:
            with self.subTest(path=path):
                self.assertEqual("set", attributes.get(path))
        for path in [*released, *ancestors]:
            with self.subTest(path=path):
                self.assertEqual("unspecified", attributes.get(path))

        # The attributes are configuration; the archive is the fact. Where there is a commit to
        # archive, list what the builder's own command would put in a bundle.
        archived = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD", "conformance/evaluation"],
            cwd=ROOT,
            capture_output=True,
        )
        if archived.returncode != 0:
            return  # no commit here (a bare scratch repository); the attribute checks above stand
        with tarfile.open(fileobj=io.BytesIO(archived.stdout)) as bundle:
            members = set(bundle.getnames())
        tracked = set(
            subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", "HEAD", "conformance/evaluation"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
        )
        self.assertEqual(
            [], sorted(name for name in members if name.startswith(staged_root_posix + "/"))
        )
        for path in released:
            if path in tracked:
                with self.subTest(archived=path):
                    self.assertIn(path, members)

    @staticmethod
    def _release_tree(directory: Path, version: str) -> Path:
        """A minimal, correctly pinned artifact tree for the version-pinning checks."""
        (directory / "conformance" / "evaluation").mkdir(parents=True)
        (directory / "schema").mkdir()
        (directory / "releases").mkdir()
        (directory / "conformance" / "manifest.json").write_text(
            json.dumps({"specVersion": version}), encoding="utf-8"
        )
        (directory / "conformance" / "evaluation" / "manifest.json").write_text(
            json.dumps({"specVersion": version, "suiteVersion": version}),
            encoding="utf-8",
        )
        (directory / "schema" / "judgment-pack-core.schema.json").write_text(
            json.dumps(
                {
                    "$id": (
                        "https://judgmentpack.org/schema/"
                        f"{version}/judgment-pack-core.schema.json"
                    ),
                    "properties": {"specVersion": {"const": version}},
                }
            ),
            encoding="utf-8",
        )
        (directory / "releases" / f"v{version}.md").write_text("notes\n", encoding="utf-8")
        return directory


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
import json
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

    def test_release_version_rejects_ambiguous_tags(self) -> None:
        for tag in ("0.1.0", "v0.1", "v00.1.0", "v0.1.0+local", "main"):
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

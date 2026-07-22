from __future__ import annotations

import importlib.util
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


if __name__ == "__main__":
    unittest.main()

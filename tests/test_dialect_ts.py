from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
# A second preparation verifier, written in TypeScript from spec/dialect.md's text alone
# (tools/dialect-verify-ts/README.md). Node runs it directly, stripping the types; nothing is installed.
READER = ROOT / "tools" / "dialect-verify-ts"
MINIMUM = (22, 18)
TESTS = ("test/vectors.test.ts", "test/units.test.ts")


def node_version(node: str) -> tuple[str, tuple[int, int] | None]:
    found = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=60).stdout.strip()
    match = re.fullmatch(r"v(\d+)\.(\d+)\.\d+", found)
    return found, (int(match.group(1)), int(match.group(2))) if match else None


class SecondDialectReaderTest(unittest.TestCase):
    def test_the_typescript_reader_answers_every_staged_vector(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("no node on PATH; the TypeScript reader needs Node 22.18 or later")
        found, version = node_version(node)
        if version is None or version < MINIMUM:
            self.skipTest(f"node {found or 'of an unknown version'} is on PATH; the TypeScript reader needs 22.18 or later")
        # Node strips the types with a WebAssembly module, which cannot reserve its memory under an
        # address-space limit (ulimit -v) unless the trap handler is disabled; the flag changes nothing else.
        run = subprocess.run(
            [node, "--disable-wasm-trap-handler", "--no-warnings", "--test", *TESTS],
            cwd=READER,
            capture_output=True,
            text=True,
            timeout=600,
        )
        self.assertEqual(run.returncode, 0, f"node --test failed:\n{run.stdout[-6000:]}\n{run.stderr[-2000:]}")
        # A vector the text does not let the reader answer is marked there as a known disagreement (a
        # TODO), which is reported and does not fail; every other test must have run and passed.
        self.assertTrue(re.search(r"(?m)^# pass [1-9][0-9]*$", run.stdout) and re.search(r"(?m)^# fail 0$", run.stdout), run.stdout[-2000:])

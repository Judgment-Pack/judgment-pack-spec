from __future__ import annotations

import base64
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
# A second preparation verifier, written in TypeScript from spec/dialect.md's text alone
# (tools/dialect-verify-ts/README.md). Node runs it directly, stripping the types; nothing is installed.
READER = ROOT / "tools" / "dialect-verify-ts"
MINIMUM = (22, 18)
TESTS = ("test/vectors.test.ts", "test/units.test.ts")


# Reads a JSON array of cases on standard input, each document in base64, and writes the second reader's report for
# each, as one JSON array; a fault of the reader is written in place of a report.
BATCH = """
import { pathToFileURL } from "node:url";
const reader = %s;
const { verify } = await import(pathToFileURL(reader + "/src/verify.ts").href);
const { preparationForm } = await import(pathToFileURL(reader + "/src/json.ts").href);
const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const bytes = (value) => (value === null ? undefined : Uint8Array.from(Buffer.from(value, "base64")));
const reports = JSON.parse(Buffer.concat(chunks).toString("utf8")).map((c) => {
  try {
    const inputs = { requireBinding: c.requireBinding };
    for (const k of ["dialect", "case", "acquisitions", "profiles", "preparation", "record", "binding"]) inputs[k] = bytes(c[k]);
    return Buffer.from(preparationForm(verify(inputs).report)).toString("utf8");
  } catch (e) {
    return "fault: " + String((e && e.stack) || e);
  }
});
process.stdout.write(JSON.stringify(reports));
"""


def first_reader_tests() -> Any:
    """tests/test_dialect.py, which holds the hand-written research documents and the first reader."""
    module = sys.modules.get("test_dialect") or sys.modules.get("tests.test_dialect")
    if module is None:
        spec = importlib.util.spec_from_file_location("test_dialect", Path(__file__).with_name("test_dialect.py"))
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules["test_dialect"] = module
        spec.loader.exec_module(module)
    return module


def node_version(node: str) -> tuple[str, tuple[int, int] | None]:
    found = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=60).stdout.strip()
    match = re.fullmatch(r"v(\d+)\.(\d+)\.\d+", found)
    return found, (int(match.group(1)), int(match.group(2))) if match else None


class SecondDialectReaderTest(unittest.TestCase):
    def node(self) -> str:
        node = shutil.which("node")
        if node is None:
            self.skipTest("no node on PATH; the TypeScript reader needs Node 22.18 or later")
        found, version = node_version(node)
        if version is None or version < MINIMUM:
            self.skipTest(f"node {found or 'of an unknown version'} is on PATH; the TypeScript reader needs 22.18 or later")
        return node

    def test_the_typescript_reader_answers_every_staged_vector(self) -> None:
        node = self.node()
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

    def test_both_readers_answer_every_research_case_alike(self) -> None:
        # The research contract of RFC 0018's round 8 (issue #176): every hand-written case of
        # tests/test_dialect.py, each new form and each refusal, given to both readers. Their reports must be
        # equal byte for byte, and the answer the text gives. A disagreement is a finding about the readers or
        # the text, and is reported here, never papered over.
        node = self.node()
        first = first_reader_tests()
        batch, names = [], []
        for name, expected, build in first.research_cases():
            inputs = build()
            report = first.READER.preparation_bytes(first.READER.report(inputs.verify().answer)).decode("utf-8")
            encoded = {
                member: None if getattr(inputs, member) is None else base64.b64encode(getattr(inputs, member)).decode("ascii")
                for member in ("dialect", "case", "acquisitions", "profiles", "preparation", "record", "binding")
            }
            batch.append({**encoded, "requireBinding": inputs.require_binding})
            names.append((name, expected, report))
        run = subprocess.run(
            [node, "--disable-wasm-trap-handler", "--no-warnings", "--input-type=module", "--eval", BATCH % json.dumps(str(READER))],
            input=json.dumps(batch).encode("utf-8"),
            capture_output=True,
            timeout=600,
        )
        self.assertEqual(run.returncode, 0, run.stderr.decode("utf-8", "replace")[-4000:])
        reports = json.loads(run.stdout)
        self.assertEqual(len(names), len(reports))
        disagreements = [
            f"{name}: first {first_report}, second {second}"
            for (name, _, first_report), second in zip(names, reports)
            if second != first_report
        ]
        self.assertEqual([], disagreements)
        for (name, expected, report), _ in zip(names, reports):
            result = json.loads(report)
            code = "reading" if result["result"] == "reading" else f"{result['result']}:{result[result['result']]}"
            with self.subTest(case=name):
                self.assertEqual(expected, code)

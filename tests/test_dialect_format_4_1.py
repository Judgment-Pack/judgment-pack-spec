"""Dialect format 4.1.0, a paged `operation` source (RFC 0033, in Review; spec/dialect.md is unchanged): the
staged vectors under conformance/dialect/format-4.1/, one for each row of the RFC's Conformance table, read by
the first reader, by one that does not read the format, and by the preserved v0.3.0 reader.

The expected answers are hand-written in tools/paged_source_vectors.py and pinned in the manifest; a
reading's preparation.json is the reader's recomputation, held here to them."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from test_dialect import READER, ROOT

FORMAT_41 = ROOT / "conformance" / "dialect" / "format-4.1"
RFC = ROOT / "rfcs" / "0033-paged-operation-source.md"


def manifest() -> dict[str, Any]:
    return json.loads((FORMAT_41 / "manifest.json").read_text(encoding="utf-8"))


def files_of(entry: dict[str, Any]) -> dict[str, bytes]:
    return {name: (FORMAT_41 / entry["name"] / name).read_bytes() for name in entry["files"]}


def verify(reader: Any, files: dict[str, bytes]) -> Any:
    return reader.verify(files["dialect.json"], files["case.json"], files["sources.json"], files["profiles.json"],
                         files["preparation.json"], binding=files.get("binding.json"))


def answer_of(result: Any) -> dict[str, Any]:
    if "reading" in result.answer:
        return {"result": "reading"}
    if "refused" in result.answer:
        return {"result": "refusal", "refusal": result.answer["refused"]}
    return {"result": "finding", "finding": result.answer["finding"]}


def conformance_rows() -> list[str]:
    """The case names of the RFC's Conformance table: each backticked name before a row's first `: `."""
    text = RFC.read_text(encoding="utf-8")
    table = text.split("## Conformance", 1)[1].split("\n## ", 1)[0]
    names: list[str] = []
    for line in table.splitlines():
        if not line.startswith("| `"):
            continue
        head = line.split("|")[1].split(": ", 1)[0]
        names.extend(re.findall(r"`([^`]+)`", head))
    return names


class PagedSourceVectorTests(unittest.TestCase):
    def test_one_vector_for_each_row_of_the_conformance_table(self) -> None:
        rows = conformance_rows()
        self.assertEqual(90, len(rows))
        entries = manifest()["cases"]
        self.assertEqual(rows, [entry["row"] for entry in entries])
        self.assertEqual(["paged-" + row for row in rows], [entry["name"] for entry in entries])
        self.assertEqual(sorted([e["name"] for e in entries] + ["README.md", "manifest.json"]),
                         sorted(p.name for p in FORMAT_41.iterdir()))

    def test_every_vector(self) -> None:
        for entry in manifest()["cases"]:
            with self.subTest(vector=entry["name"]):
                directory = FORMAT_41 / entry["name"]
                self.assertEqual(sorted(entry["files"]), sorted(p.name for p in directory.iterdir()))
                files = files_of(entry)
                for name, sha in entry["files"].items():
                    self.assertEqual(sha, hashlib.sha256(files[name]).hexdigest(), name)
                result = verify(READER, files)
                expected = entry["expected"]
                self.assertEqual({k: expected[k] for k in ("result", "refusal", "finding") if k in expected},
                                 answer_of(result), result.answer)
                if expected["result"] == "reading":
                    self.assert_reading(entry, files, result)

    def assert_reading(self, entry: dict[str, Any], files: dict[str, bytes], result: Any) -> None:
        expected = entry["expected"]
        reading = result.answer["reading"]
        self.assertEqual(entry["preparationDigest"], result.digest)
        self.assertEqual(expected["facts"], READER.as_plain(reading["facts"]))
        if "unsignedParameters" in expected:
            self.assertEqual(expected["unsignedParameters"], reading.get("unsignedParameters", []))
        # the given preparation is written in its canonical form (§9.5)
        self.assertEqual(files["preparation.json"],
                         READER.preparation_bytes(READER.read_document(files["preparation.json"], "p")))
        preparation = json.loads(files["preparation.json"])
        self.assertEqual("4.1.0", preparation["formatVersion"])
        self.assertNotIn("version", preparation)
        outcomes = {o["name"]: o for o in preparation["outcomes"]}
        for name, want in expected["outcomes"].items():
            got = outcomes[name]
            self.assertEqual((want["status"], want["reason"], want.get("paging")),
                             (got["status"], got["reason"], got.get("paging")), name)
        # RFC 0033 section 8: `cites` in the order of `sources`, each paged source's pages in call order
        self.assertEqual(expected["cites"], [[c["sessionId"], c["callIndex"]] for c in preparation["cites"]])
        # and each entry of an acquired paged source carries `receipts`, one citation per page, and no `receipt`
        for line in preparation["lineage"]:
            paging = expected["outcomes"].get(line["source"], {}).get("paging")
            if paging is None:
                continue
            self.assertNotIn("receipt", line)
            self.assertEqual(paging["pages"], len(line["receipts"]))
            self.assertEqual(line["receipts"], [c for c in preparation["cites"] if c in line["receipts"]])
        # unsignedFreshness keeps one entry per acquired source, a paged one among them
        acquired = [name for name, outcome in outcomes.items() if "arguments" in outcome]
        self.assertEqual(sorted(acquired), sorted(e["source"] for e in reading["unsignedFreshness"]["sources"]))

    def test_a_reader_that_does_not_read_the_format_refuses_it_in_phase_4(self) -> None:
        # RFC 0033 section 11: phases 0 to 3 as for format 4.0.0, then `version-unread`, before any form; a
        # document of format 4.0.0 is answered as today
        with mock.patch.object(READER, "READ_FORMATS", ("2.0.0", "3.0.0", "4.0.0")):
            for entry in manifest()["cases"]:
                with self.subTest(vector=entry["name"]):
                    result = verify(READER, files_of(entry))
                    self.assertEqual(entry["expectedReportOfAReaderThatDoesNotReadTheFormat"],
                                     json.loads(READER.preparation_bytes(READER.report(result.answer))))

    def test_the_preserved_v0_3_0_reader_refuses_every_vector_input_malformed(self) -> None:
        # RFC 0033 section 11: a reader written to the text before the amendment takes phases 0 to 3 and
        # refuses an unknown selector in phase 5; it imports tools/retained_column.py, which is this tree's.
        path = ROOT / "tests/fixtures/historical-compatibility/v0.3.0/tools/dialect_verify.py"
        spec = importlib.util.spec_from_file_location("dialect_verify_v0_3_0_paged", path)
        assert spec is not None and spec.loader is not None
        old = importlib.util.module_from_spec(spec)
        with mock.patch.object(sys, "path", [str(ROOT / "tools"), *sys.path]), \
             mock.patch.dict(sys.modules, {spec.name: old}):
            spec.loader.exec_module(old)
        for entry in manifest()["cases"]:
            with self.subTest(vector=entry["name"]):
                files = files_of(entry)
                result = old.verify(files["dialect.json"], files["case.json"], files["sources.json"],
                                    files["profiles.json"], files["preparation.json"], binding=files.get("binding.json"))
                self.assertEqual({"refusal": "input-malformed", "result": "refusal"},
                                 json.loads(old.preparation_bytes(old.report(result.answer))))


class PagedSourceUnitTests(unittest.TestCase):
    def test_a_member_with_pages_is_not_measured_in_an_earlier_format(self) -> None:
        # RFC 0033 sections 1 and 7: in format 4.0.0, 65 pages and a 33-level result are refused in phase 5,
        # input-malformed, not measured in phase 3
        deep: Any = 1
        for _ in range(33):
            deep = {"a": deep}
        acquisitions = {"changes": {"pages": [{"result": deep}] * 65}}
        dialect = {"formatVersion": "4.0.0", "sources": [{"paging": {"maxPages": READER.Num("65")}}]}
        READER.count_bounds(dialect, acquisitions)
        with self.assertRaises(READER.Refused) as refused:
            READER.count_bounds({**dialect, "formatVersion": "4.1.0"}, acquisitions)
        self.assertEqual("input-over-bound", refused.exception.name)

    def test_the_requests_replace_or_add_the_member_and_change_nothing_else(self) -> None:
        first = {"tool": "t", "arguments": {"since": "s", "cursor": "c0"}}
        self.assertEqual({"tool": "t", "arguments": {"since": "s", "cursor": "r1"}},
                         READER.with_reference(first, "/arguments/cursor", "r1"))
        self.assertEqual({"tool": "t", "arguments": {"since": "s", "cursor": "c0", "page": "r1"}},
                         READER.with_reference(first, "/arguments/page", "r1"))
        self.assertEqual("c0", first["arguments"]["cursor"])


if __name__ == "__main__":
    unittest.main()

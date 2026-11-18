"""The registry companion's rows of format 1.1.0, status released, against its second reader.

tools/registry_1_1_0_reader.py was written from spec/registry-1.1.0.md and registry.md alone, and
gives each row's result from the row's inputs. Every row of conformance/registry/1.1.0/manifest.json
must give its expected result exactly: the report with every `message` removed, order kept; an
accepted assembly's written registry and index, byte for byte; a written lock's exact bytes, or a
writer's refusal by its codes; and a verification's record once it ends. Two readers agreeing on
every row is the companion's stable bar (§15). The rows' own consistency, which needs no reader, is
held by tests/test_registry_1_1_0_rows.py.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "conformance" / "registry" / "1.1.0"


def _load_reader() -> Any:
    spec = importlib.util.spec_from_file_location("registry_1_1_0_reader", ROOT / "tools" / "registry_1_1_0_reader.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["registry_1_1_0_reader"] = module
    spec.loader.exec_module(module)
    return module


def read(path: str) -> bytes:
    return (BASE / path).read_bytes()


def _plain(report: dict) -> dict:
    out = dict(report)
    out["diagnostics"] = [{k: v for k, v in d.items() if k != "message"} for d in report["diagnostics"]]
    return out


def _sources(row: dict) -> dict:
    return {name: {"commit": s["commit"], "files": {p: read(f) for p, f in s["files"].items()}}
            for name, s in row["sources"].items()}


def _known(row: dict) -> dict:
    return {"indexes": [read(p) for p in row["known"]["indexes"]], "locks": [read(p) for p in row["known"]["locks"]]}


def _emitters(reader: Any, row: dict) -> list | None:
    if "emitters" not in row:
        return None
    return [reader.Emitter(read(e["manifest"]), e["path"], [(f["path"], f["mode"], read(f["file"])) for f in e["files"]],
                           source=e.get("source"), check=e.get("check")) for e in row["emitters"]]


def _file(row: dict) -> dict | None:
    if "file" not in row:
        return None
    f = row["file"]
    out = {"path": f["path"], "mode": f["mode"], "bytes": read(f["file"])}
    if "source" in f:
        out["source"] = f["source"]
    return out


def run(reader: Any, row: dict) -> tuple[Any, Any]:
    """The reader's result for one row, and the row's expected result, in one comparable form."""
    op = row["operation"]
    if op == "assemble":
        got, writes = reader.assemble(read(row["federation"]), _sources(row), _known(row))
        want_writes = None
        if "writes" in row:
            want_writes = {name: read(path) for name, path in row["writes"].items()}
        return ([_plain(got), writes],
                [_plain(json.loads(read(row["expected"]))), want_writes])
    if op == "check-index":
        got = reader.check_index(read(row["federation"]), _sources(row), _known(row), read(row["index"]))
        return _plain(got), _plain(json.loads(read(row["expected"])))
    if op == "write-lock":
        args: dict = {"previous": read(row["previous"]) if "previous" in row else None,
                      "first_serial": row.get("firstSerial"), "emitters": _emitters(reader, row) or []}
        if "federation" in row:
            args.update(federation=read(row["federation"]), sources=_sources(row), known=_known(row),
                        source_signatures=[read(p) for p in row["sourceSignatures"]], signers=row["signers"])
        else:
            args.update(registry=read(row["registry"]), kinds=[read(k) for k in row["kinds"]])
        got = reader.write_lock(**args)
        expected = read(row["expected"])
        try:
            parsed = json.loads(expected)
        except ValueError:
            parsed = None
        if isinstance(parsed, dict) and set(parsed) == {"refused"}:
            want: Any = {"refused": sorted(set(parsed["refused"]))}
        else:
            want = expected
        return got, want
    if op == "check-lock":
        got = reader.check_lock(read(row["lock"]), read(row["registry"]), [read(k) for k in row["kinds"]],
                                row["expect"], index=read(row["index"]) if "index" in row else None,
                                emitters=_emitters(reader, row))
        return _plain(got), _plain(json.loads(read(row["expected"])))
    if op == "coverage":
        got = reader.coverage(read(row["lock"]), row["expect"],
                              resolved=read(row["resolved"]) if "resolved" in row else None, file=_file(row))
        return _plain(got), _plain(json.loads(read(row["expected"])))
    if op == "verify":
        got, record = reader.verify(
            lock=read(row["lock"]), lock_signatures=[read(p) for p in row["lockSignatures"]],
            source_signatures=[read(p) for p in row["sourceSignatures"]], signers=row["signers"],
            expect=row["expect"], record=row["record"], floor=row.get("floor"),
            index=read(row["index"]) if "index" in row else None, concurrent=row.get("concurrent"),
            write_fails=row.get("writeFails", False),
            registry=read(row["registry"]) if "registry" in row else None,
            kinds=[read(k) for k in row.get("kinds", [])],
            resolved=read(row["resolved"]) if "resolved" in row else None, file=_file(row))
        return [_plain(got), record], [_plain(json.loads(read(row["expected"]))), row["expectedRecord"]]
    raise AssertionError(f"unknown operation {op}")


class SecondReaderTest(unittest.TestCase):
    """Every row of format 1.1.0, through tools/registry_1_1_0_reader.py."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.reader = _load_reader()
        cls.rows = json.loads(read("manifest.json"))["vectors"]

    def test_every_row_agrees(self) -> None:
        self.assertTrue(self.rows)
        for row in self.rows:
            with self.subTest(row=row["id"]):
                got, want = run(self.reader, row)
                self.assertEqual(got, want)

    def test_reader_refuses_yaml(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.reader._yaml_refused("registry.yaml")


if __name__ == "__main__":
    unittest.main()

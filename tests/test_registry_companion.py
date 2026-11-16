"""The registry companion `1.0.0`, status proposed (spec/registry.md), and its staged rows.

The rows under conformance/registry/1.0.0/ are hand-written and synthetic. These tests hold them to
the parts of the companion that need no registry reader: the manifest names every file and only
files; every input is I-JSON within its bound; pins and digests follow §2.3; resolved documents and
facts lines follow from their inputs by §8 and §10.1; reports are in §7.4's order, name only listed
codes with their severities, and carry no value; contracts are canonical and in §10.3's order; and
codes.json equals the companion's §12 table. Validation itself is a reader's work: no second reader
exists in this repository yet (spec/registry.md §14).
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "conformance" / "registry" / "1.0.0"
SPEC = ROOT / "spec" / "registry.md"
MANIFEST = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
CODES = {c["code"]: c for c in json.loads((BASE / "codes.json").read_text(encoding="utf-8"))["codes"]}
ORDER = ("document", "kindDocument", "kind", "entry.kind", "entry.id", "environment", "pointer", "line",
         "column")


def _pairs(pairs):
    names = [name for name, _ in pairs]
    if len(names) != len(set(names)):
        raise ValueError("duplicate member")
    return dict(pairs)


def load(path: Path):
    return json.loads(path.read_bytes().decode("utf-8"), object_pairs_hook=_pairs,
                      parse_float=Decimal, parse_int=int)


def number(value) -> str:
    if isinstance(value, int):
        if abs(value) > 2**53 - 1:
            raise ValueError("integer out of range")
        return str(value)
    double = float(value)
    if Decimal(repr(double)) != value:
        raise ValueError("decimal does not round-trip")
    if double == 0:
        if value.is_signed():
            raise ValueError("negative zero")
        return "0"
    if double.is_integer() and abs(double) < 1e21:
        return str(int(double))
    text = repr(double)
    if "e" in text:
        exponent = int(text.split("e")[1])
        if -7 < exponent < 21:
            return format(Decimal(text), "f")
        mantissa = text.split("e")[0]
        return f"{mantissa}e{'+' if exponent > 0 else '-'}{abs(exponent)}"
    return text


def jcs(value) -> str:
    if value is None or isinstance(value, bool):
        return json.dumps(value)
    if isinstance(value, (int, Decimal)):
        return number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ",".join(jcs(item) for item in value) + "]"
    keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
    return "{" + ",".join(json.dumps(key, ensure_ascii=False) + ":" + jcs(value[key]) for key in keys) + "}"


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def depth(value, level: int = 1) -> int:
    if isinstance(value, dict):
        return max([level] + [depth(v, level + 1) for v in value.values()])
    if isinstance(value, list):
        return max([level] + [depth(v, level + 1) for v in value])
    return level - 1


def tokens(pointer: str) -> list[str]:
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer.split("/")[1:]]


def escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def lookup(value, path):
    for token in path:
        if isinstance(value, dict) and token in value:
            value = value[token]
        elif isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]{0,8}", token) and int(token) < len(value):
            value = value[int(token)]
        else:
            return None, False
    return value, True


def set_at(value, path, new):
    if not path:
        return new
    parent, _ = lookup(value, path[:-1])
    if isinstance(parent, list):
        parent[int(path[-1])] = new
    else:
        parent[path[-1]] = new
    return value


def positions(value, pattern, at=()):
    """Every position of value a pointer pattern (§3.5) matches."""
    if not pattern:
        yield list(at), value
        return
    head, rest = pattern[0], pattern[1:]
    if isinstance(value, dict):
        for name in value:
            if head == "*" or head.replace("~2", "*") == name:
                yield from positions(value[name], rest, at + (name,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            if head == "*" or head == str(index):
                yield from positions(item, rest, at + (str(index),))


def kinds_of(row) -> dict[str, dict]:
    return {k["kind"]: k for k in (load(BASE / path) for path in row["kinds"])}


def resolve(registry, environment):
    entries = []
    patches = {}
    for overlay in registry.get("overlays", []):
        if overlay["environment"] == environment:
            for patch in overlay["patches"]:
                patches[(patch["kind"], patch["id"])] = patch["set"]
    for entry in registry["entries"]:
        if environment not in entry.get("environments", registry["environments"]):
            continue
        value = copy.deepcopy(entry["value"])
        for pointer, new in sorted(patches.get((entry["kind"], entry["id"]), {}).items()):
            value = set_at(value, tokens(pointer), copy.deepcopy(new))
        entries.append({"kind": entry["kind"], "id": entry["id"], "owner": entry["owner"], "value": value})
    return entries


def mapped(kind, value):
    value = copy.deepcopy(value)

    def numbers(node):
        if isinstance(node, bool) or node is None or isinstance(node, str):
            return node
        if isinstance(node, (int, Decimal)):
            text = format(Decimal(node).normalize(), "f")
            return text if "." not in text else text.rstrip("0").rstrip(".")
        if isinstance(node, list):
            return [numbers(item) for item in node]
        return {name: numbers(item) for name, item in node.items()}

    value = numbers(value)
    for pattern in kind.get("secrets", []):
        for path, reference in list(positions(value, tokens(pattern))):
            store, locator = reference[len("secret:"):].split(":", 1)
            value = set_at(value, path, {"scope": locator.split("/")[1], "store": store})
    return value


def facts_lines(row) -> str:
    registry = load(BASE / row["registry"])
    kinds = kinds_of(row)
    environment = row["environment"]
    resolved = {(e["kind"], e["id"]): e for e in resolve(registry, environment)}
    identity = {"digest": digest(jcs(registry).encode()), "id": registry["id"], "version": registry["version"]}
    lines = []
    for (kind_name, entry_id), entry in resolved.items():
        if kind_name != row["kind"]:
            continue
        kind = kinds[kind_name]
        references = {}
        for pattern in kind.get("references", []):
            for path, text in positions(entry["value"], tokens(pattern["pointer"])):
                target, _, pointer = text[len("entry:"):].partition("#")
                target_kind, target_id = target.split("/", 1)
                target_value = mapped(kinds[target_kind], resolved[(target_kind, target_id)]["value"])
                if "#" in text:
                    target_value, _ = lookup(target_value, tokens(pointer))
                references["".join("/" + escape(t) for t in path)] = {
                    "id": target_id, "kind": target_kind, "value": target_value}
        facts = {"entry": {"id": entry_id, "kind": kind_name, "owner": entry["owner"]},
                 "environment": environment, "references": references, "registry": identity,
                 "value": mapped(kind, entry["value"])}
        lines.append(jcs({"facts": facts, "id": f"{kind_name}/{entry_id}"}) + "\n")
    return "".join(lines)


def location_key(diagnostic):
    location = diagnostic["location"]
    entry = location.get("entry", {})
    values = (location.get("document", ""), location.get("kindDocument", ""), location.get("kind", ""),
              entry.get("kind", ""), entry.get("id", ""), location.get("environment", ""),
              location.get("pointer", ""), location.get("line", 0), location.get("column", 0),
              diagnostic["code"])
    return tuple(v.encode() if isinstance(v, str) else v for v in values)


def input_strings(row) -> set[str]:
    """Strings of entry values, overlay values and patterns: what a report must never carry."""
    found = set()

    def walk(node):
        if isinstance(node, str):
            found.add(node)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for item in node.values():
                walk(item)

    registry = load(BASE / row["registry"])
    for entry in registry.get("entries", []) if isinstance(registry.get("entries"), list) else []:
        if isinstance(entry, dict):
            walk(entry.get("value"))
    for overlay in registry.get("overlays", []) if isinstance(registry.get("overlays"), list) else []:
        for patch in overlay.get("patches", []) if isinstance(overlay, dict) else []:
            if isinstance(patch, dict):
                walk(patch.get("set"))
    for path in row["kinds"]:
        text = (BASE / path).read_text(encoding="utf-8")
        found.update(re.findall(r'"pattern"\s*:\s*"((?:[^"\\]|\\.)*)"', text))
    return {s for s in found if len(s) >= 6 or s.startswith(("entry:", "secret:"))}


class RegistryRows(unittest.TestCase):
    def test_manifest_names_every_file_and_only_files(self) -> None:
        named = {"manifest.json", "codes.json"}
        for row in MANIFEST["vectors"]:
            for member in ("registry", "contract", "pack", "expected"):
                if member in row:
                    named.add(row[member])
            named.update(row.get("kinds", []))
        on_disk = {p.relative_to(BASE).as_posix() for p in BASE.rglob("*") if p.is_file()}
        self.assertEqual(named, on_disk)
        self.assertEqual(len({row["id"] for row in MANIFEST["vectors"]}), len(MANIFEST["vectors"]))

    def test_inputs_are_i_json_within_bounds(self) -> None:
        for path in sorted(BASE.rglob("*.json")):
            with self.subTest(path=path.name):
                data = path.read_bytes()
                if path.parent.name == "kinds" or "kinds" in path.parts:
                    self.assertLessEqual(len(data), 262144)
                self.assertLessEqual(len(data), 8388608)
                if path.parts[-2] == "admission" or path.name in ("duplicate-member.json",):
                    continue
                value = load(path)
                jcs(value)  # refuses an out-of-range number or negative zero
                self.assertLessEqual(depth(value), 32 if "pack-" not in path.name else 128)

    def test_pins_of_valid_rows_are_the_jcs_digests_of_their_declarations(self) -> None:
        for row in MANIFEST["vectors"]:
            if row["operation"] != "validate" or not load(BASE / row["expected"])["valid"]:
                continue
            with self.subTest(row=row["id"]):
                registry = load(BASE / row["registry"])
                supplied = {digest(jcs(load(BASE / p)).encode()) for p in row["kinds"]}
                self.assertEqual({pin["digest"] for pin in registry["kinds"]}, supplied)

    def test_reports_follow_section_7_4(self) -> None:
        for row in MANIFEST["vectors"]:
            if row["operation"] != "validate":
                continue
            with self.subTest(row=row["id"]):
                report = load(BASE / row["expected"])
                diagnostics = report["diagnostics"]
                self.assertEqual(report["valid"], not any(d["severity"] == "error" for d in diagnostics))
                for d in diagnostics:
                    self.assertIn(d["code"], CODES)
                    self.assertEqual(d["severity"], CODES[d["code"]]["severity"])
                    self.assertNotIn("message", d)
                keys = [location_key(d) for d in diagnostics]
                self.assertEqual(keys, sorted(set(keys)))
                raw = {digest((BASE / p).read_bytes()) for p in row["kinds"]}
                for d in diagnostics:
                    if "kindDocument" in d["location"]:
                        self.assertIn(d["location"]["kindDocument"], raw)
                if "registry" in report:
                    data = load(BASE / row["registry"])
                    self.assertEqual(report["registry"]["digest"], digest(jcs(data).encode()))
                text = json.dumps(report, ensure_ascii=False)
                for value in input_strings(row):
                    self.assertNotIn(json.dumps(value, ensure_ascii=False)[1:-1], text)

    def test_resolved_documents_follow_section_8(self) -> None:
        for row in MANIFEST["vectors"]:
            if row["operation"] != "resolve":
                continue
            with self.subTest(row=row["id"]):
                registry = load(BASE / row["registry"])
                expected = (BASE / row["expected"]).read_bytes()
                document = {"entries": resolve(registry, row["environment"]), "environment": row["environment"],
                            "kinds": registry["kinds"],
                            "registry": {"digest": digest(jcs(registry).encode()), "id": registry["id"],
                                         "version": registry["version"]},
                            "resolvedFormatVersion": "1.0.0"}
                self.assertEqual(expected.decode("utf-8"), jcs(document))

    def test_facts_lines_follow_section_10_1(self) -> None:
        for row in MANIFEST["vectors"]:
            if row["operation"] != "facts":
                continue
            with self.subTest(row=row["id"]):
                expected = (BASE / row["expected"]).read_text(encoding="utf-8")
                self.assertNotIn("secret:", expected)
                self.assertEqual(expected, facts_lines(row))

    def test_contracts_are_canonical_and_in_order(self) -> None:
        for row in MANIFEST["vectors"]:
            if row["operation"] != "contract":
                continue
            with self.subTest(row=row["id"]):
                data = (BASE / row["expected"]).read_bytes().decode("utf-8")
                contract = load(BASE / row["expected"])
                self.assertEqual(data, jcs(contract))
                keys = [(f["pointer"].encode(), f["type"]) for f in contract["facts"]]
                self.assertEqual(keys, sorted(set(keys)))
                kind = kinds_of(row)[row["kind"]]
                self.assertEqual(contract["source"]["kind"]["digest"], digest(jcs(kind).encode()))

    def test_check_reports_name_their_inputs(self) -> None:
        for row in MANIFEST["vectors"]:
            if row["operation"] != "check":
                continue
            with self.subTest(row=row["id"]):
                self.assertIsNone(row["class"])
                report = load(BASE / row["expected"])
                self.assertEqual(report["contract"]["digest"], digest(jcs(load(BASE / row["contract"])).encode()))
                self.assertEqual(report["pack"]["digest"], digest((BASE / row["pack"]).read_bytes()))
                for d in report["diagnostics"]:
                    self.assertEqual(d["severity"], CODES[d["code"]]["severity"])


class RegistryCompanionText(unittest.TestCase):
    def test_code_list_equals_the_section_12_table(self) -> None:
        text = SPEC.read_text(encoding="utf-8")
        table = re.findall(r"^\| `([A-Z]+-[A-Z0-9-]+)` \| (error|warning) \| (§[0-9.]+) \|", text, re.M)
        self.assertEqual([(c["code"], c["severity"], c["section"]) for c in CODES.values()], table)
        self.assertTrue(all(c["status"] == "active" for c in CODES.values()))

    def test_every_selector_is_1_0_0(self) -> None:
        text = SPEC.read_text(encoding="utf-8")
        rows = re.findall(r"^\| [^|]+ \| `([a-zA-Z]+Version)` \| `\"([0-9.]+)\"` \|", text, re.M)
        self.assertEqual(len(rows), 10)
        self.assertTrue(all(version == "1.0.0" for _, version in rows))

    def test_bundled_companion_links_rows_by_url(self) -> None:
        text = SPEC.read_text(encoding="utf-8")
        self.assertNotIn("](../conformance/registry", text)


if __name__ == "__main__":
    unittest.main()

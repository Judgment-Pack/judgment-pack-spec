"""The registry companion `1.0.0`, status proposed (spec/registry.md), and its staged rows.

The rows under conformance/registry/1.0.0/ are hand-written and synthetic. These tests hold them to
the parts of the companion that need no registry reader: the manifest names every file and only
files; every input is I-JSON within its bound; pins and digests follow §2.3; resolved documents and
facts lines follow from their inputs by §8 and §10.1; reports are in §7.4's order, name only listed
codes with their severities, and carry no value; contracts are canonical and in §10.3's order; and
codes.json equals the companion's §12 table. The emitter host's rows are held to a model of the
§11 rules they exercise: owns globs, response paths, the members of a response and emitter codes;
requests, the kind-filtering check's restored digest, the references check and the vector layout.
Validation itself is a reader's work: no second reader exists in this repository yet
(spec/registry.md §14).
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
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


# A model of §11's path, glob and code rules, as far as the emitter host's rows exercise them. It is
# not a host: it reads no request, runs nothing, and checks no bound but a path's length.
DEVICE_NAMES = {"con", "prn", "aux", "nul", "conin$", "conout$"}
HFS_IGNORED = {*range(0x200C, 0x2010), *range(0x202A, 0x202F), *range(0x206A, 0x2070), 0xFEFF}
EMITTER_CODE = re.compile(r"x-[a-z0-9]+(-[a-z0-9]+)*")
RESPONSE_MEMBERS = ("emitResponseVersion", "files", "diagnostics")
MANIFEST_REQUIRED = ("emitterManifestVersion", "id", "version", "owner", "reads", "requestVersions",
                     "command", "owns")


def ascii_lower(text: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)


def git_name(segment: str) -> bool:
    """git's is_ntfs_dotgit and is_hfs_dotgit, for one segment (§11.3)."""
    rest = None
    if segment[:1] == "." and ascii_lower(segment[1:4]) == "git":
        rest = segment[4:]
    elif ascii_lower(segment[:3]) == "git" and segment[3:5] == "~1":
        rest = segment[5:]
    if rest is not None and all(c in ". " for c in rest):
        return True
    skipped = "".join(c for c in segment if ord(c) not in HFS_IGNORED)
    return skipped[:1] == "." and ascii_lower(skipped[1:]) == "git" and skipped[1:].isascii()


def device_name(segment: str) -> bool:
    base = segment.split(".", 1)[0].rstrip(" ").lower()
    if base in DEVICE_NAMES:
        return True
    return base[:3] in ("com", "lpt") and base[3:] in ("1", "2", "3", "4", "5", "6", "7", "8", "9",
                                                      "\u00b9", "\u00b2", "\u00b3")


def path_form(path: str, glob: bool = False) -> bool:
    if not path or len(path.encode("utf-8")) > 512:
        return False
    if any(c in "\0\\:" or unicodedata.category(c) == "Cc" for c in path):
        return False
    for segment in path.split("/"):
        if segment in ("", ".", "..") or segment.startswith("~") or segment.endswith((".", " ")):
            return False
        if git_name(segment) or device_name(segment) or (glob and "**" in segment and segment != "**"):
            return False
    return True


def glob_admitted(glob: str) -> bool:
    return path_form(glob, glob=True) and "*" not in glob.split("/", 1)[0]


def glob_matches(glob: str, path: str) -> bool:
    segments = glob.split("/")
    if segments[-1] == "**":
        segments[-1:] = ["*", "**"]

    def segment(pattern: str, name: str) -> bool:
        return re.fullmatch("[^/]*".join(re.escape(part) for part in pattern.split("*")), name, re.S) is not None

    def match(pattern: list[str], names: list[str]) -> bool:
        if not pattern:
            return not names
        if pattern[0] == "**":
            return any(match(pattern[1:], names[k:]) for k in range(len(names) + 1))
        return bool(names) and segment(pattern[0], names[0]) and match(pattern[1:], names[1:])

    return match(segments, path.split("/"))


def manifest_refusals(manifest) -> set[str]:
    found = {"/" + name for name in MANIFEST_REQUIRED if name not in manifest}
    found.update(f"/owns/{i}" for i, glob in enumerate(manifest.get("owns", [])) if not glob_admitted(glob))
    return found


def response_refusals(manifest, response) -> set[str]:
    found = {"/" + name for name in response if name not in RESPONSE_MEMBERS}
    found.update("/" + name for name in RESPONSE_MEMBERS if name not in response)
    previous = None
    for i, file in enumerate(response.get("files", [])):
        path = file["path"]
        if not path_form(path) or not any(glob_matches(glob, path) for glob in manifest["owns"]):
            found.add(f"/files/{i}/path")
            continue
        if previous is not None and path <= previous:
            found.add(f"/files/{i}/path")
        previous = path
    for i, diagnostic in enumerate(response.get("diagnostics", [])):
        code = diagnostic["code"]
        if len(code.encode("utf-8")) > 64 or not EMITTER_CODE.fullmatch(code):
            found.add(f"/diagnostics/{i}/code")
    return found


def emit_request(row) -> str:
    """The request (§11.2) the host writes for a row's manifest, registry and kinds, environments "all"."""
    manifest = load(BASE / row["manifest"])
    registry = load(BASE / row["registry"])
    reads = {r["kind"] for r in manifest["reads"]}
    identity = {"digest": digest(jcs(registry).encode()), "id": registry["id"], "version": registry["version"]}
    pins = [pin for pin in registry["kinds"] if pin["kind"] in reads]
    resolved = [{"entries": [e for e in resolve(registry, environment) if e["kind"] in reads],
                 "environment": environment, "kinds": pins, "registry": identity,
                 "resolvedFormatVersion": "1.0.0"}
                for environment in registry["environments"]]
    kinds = kinds_of(row)
    declarations = [kinds[pin["kind"]] for pin in sorted(pins, key=lambda pin: pin["kind"].encode())]
    return jcs({"declarations": declarations, "emitRequestVersion": "1.0.0",
                "emitter": {"id": manifest["id"], "version": manifest["version"]}, "options": {},
                "resolved": resolved})


def restored(request: str, original: str) -> str:
    """Check 4's restoration (§11.5): each registry digest set to the original request's."""
    changed, before = json.loads(request), json.loads(original)
    for a, b in zip(changed.get("resolved", []), before.get("resolved", [])):
        a["registry"]["digest"] = b["registry"]["digest"]
    for a, b in zip(changed.get("factsContracts", []), before.get("factsContracts", [])):
        if "registry" in a["source"] and "registry" in b["source"]:
            a["source"]["registry"]["digest"] = b["source"]["registry"]["digest"]
    return jcs(changed)


def failing_references(row) -> set[tuple]:
    """Check 5 (§11.5): (file, entry kind, entry id, pointer) of each string a file holds a run of."""
    request = json.loads(emit_request(row))
    kinds = kinds_of(row)
    first = {}
    for document in request["resolved"]:
        for entry in document["entries"]:
            for pattern in kinds[entry["kind"]].get("secrets", []):
                for path, text in positions(entry["value"], tokens(pattern)):
                    first.setdefault(text, (entry["kind"], entry["id"], "".join("/" + escape(t) for t in path)))
    strings = [s for s in first if len(s) >= 32]
    found = set()
    for file in load(BASE / row["response"])["files"]:
        data = file["text"]
        covers = [(i, i + len(s)) for s in strings for i in range(len(data)) if data.startswith(s, i)]
        for s in strings:
            for end in range(32, len(data) + 1):
                length = max((n for n in range(32, min(end, len(s)) + 1) if data[end - n:end] in s), default=0)
                if length and not any(a <= end - length and end <= b for a, b in covers):
                    found.add((file["path"],) + first[s])
                    break
    return found


def vector_layout(vector: Path) -> dict:
    """§11.5's vector layout, as far as the layout rows exercise it: the files expected/ gives, or a refusal."""
    refused = {"refused": True}
    members = {"request.json": False, "registry.json": False, "kinds": True, "options.json": False,
               "expected": True, "expected-failure.json": False}
    present = set()
    for entry in vector.iterdir():
        if entry.name not in members or entry.is_symlink() or entry.is_dir() != members[entry.name]:
            return refused
        present.add(entry.name)
    if (("request.json" in present) == ("registry.json" in present)
            or "request.json" in present and present & {"kinds", "options.json"}
            or "registry.json" in present and "kinds" not in present
            or len(present & {"expected", "expected-failure.json"}) != 1):
        return refused
    marker, beside, files = False, False, []
    for entry in sorted((vector / "expected").rglob("*")):
        relative = entry.relative_to(vector / "expected").as_posix()
        if entry.name == "~empty":
            if relative != "~empty" or entry.is_symlink() or not entry.is_file() or entry.stat().st_size:
                return refused
            marker = True
            continue
        beside = True
        if entry.is_symlink() or not (entry.is_file() or entry.is_dir()):
            return refused
        if entry.is_file():
            files.append(relative)
    if marker and beside or not marker and not files:
        return refused
    return {"files": sorted(files, key=str.encode)}


class RegistryRows(unittest.TestCase):
    def test_manifest_names_every_file_and_only_files(self) -> None:
        named = {"manifest.json", "codes.json"}
        for row in MANIFEST["vectors"]:
            for member in ("registry", "contract", "pack", "manifest", "request", "response", "expected"):
                if member in row:
                    named.add(row[member])
            named.update(row.get("kinds", []))
            if "vector" in row:
                below = (BASE / row["vector"]).rglob("*")
                named.update(p.relative_to(BASE).as_posix() for p in below if p.is_file())
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

    def test_host_refusals_follow_section_11(self) -> None:
        for row in MANIFEST["vectors"]:
            if row["operation"] not in ("manifest", "response"):
                continue
            with self.subTest(row=row["id"]):
                self.assertEqual(row["class"], "emitter-host")
                refusals = load(BASE / row["expected"])["refusals"]
                keys = [(r["pointer"].encode(), r["code"]) for r in refusals]
                self.assertEqual(keys, sorted(set(keys)))
                manifest = load(BASE / row["manifest"])
                if row["operation"] == "manifest":
                    self.assertEqual({r["code"] for r in refusals}, {"EMIT-MANIFEST"})
                    self.assertEqual({r["pointer"] for r in refusals}, manifest_refusals(manifest))
                    continue
                self.assertEqual(manifest_refusals(manifest), set())
                request = BASE / row["request"]
                self.assertEqual(request.read_bytes().decode("utf-8"), jcs(load(request)))
                self.assertEqual({r["code"] for r in refusals}, {"EMIT-RESPONSE"})
                self.assertEqual({r["pointer"] for r in refusals},
                                 response_refusals(manifest, load(BASE / row["response"])))

    def test_requests_follow_section_11_2(self) -> None:
        rows = [row for row in MANIFEST["vectors"] if row["operation"] == "request"]
        self.assertTrue(rows)
        by_registry = {}
        for row in rows:
            with self.subTest(row=row["id"]):
                self.assertEqual(row["class"], "emitter-host")
                expected = (BASE / row["expected"]).read_bytes().decode("utf-8")
                self.assertEqual(expected, emit_request(row))
                registry = load(BASE / row["registry"])
                reads = {r["kind"] for r in load(BASE / row["manifest"])["reads"]}
                registry["kinds"] = [pin for pin in registry["kinds"] if pin["kind"] in reads]
                registry["entries"] = [e for e in registry["entries"] if e["kind"] in reads]
                by_registry.setdefault((row["manifest"], jcs(registry)), []).append(expected)
        # Check 4 (§11.5): requests whose registries differ only in kinds the manifest does not read
        # are the same bytes once each registry digest is restored, and differ before.
        groups = [g for g in by_registry.values() if len(g) > 1]
        self.assertTrue(groups)
        for group in groups:
            for request in group[1:]:
                self.assertNotEqual(request, group[0])
                self.assertEqual(restored(request, group[0]), group[0])

    def test_references_follow_section_11_5(self) -> None:
        for row in MANIFEST["vectors"]:
            if row["operation"] != "references":
                continue
            with self.subTest(row=row["id"]):
                self.assertEqual(row["class"], "emitter-harness")
                manifest = load(BASE / row["manifest"])
                self.assertEqual(response_refusals(manifest, load(BASE / row["response"])), set())
                references = load(BASE / row["expected"])["references"]
                keys = [(r["file"].encode(), r["entry"]["kind"].encode(), r["entry"]["id"].encode(),
                         r["pointer"].encode()) for r in references]
                self.assertEqual(keys, sorted(set(keys)))
                self.assertTrue(all("environment" not in r for r in references))
                self.assertEqual({(r["file"], r["entry"]["kind"], r["entry"]["id"], r["pointer"])
                                  for r in references}, failing_references(row))

    def test_vector_layouts_follow_section_11_5(self) -> None:
        rows = [row for row in MANIFEST["vectors"] if row["operation"] == "layout"]
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(row=row["id"]):
                self.assertEqual(row["class"], "emitter-harness")
                vector = BASE / row["vector"]
                request = (vector / "request.json").read_bytes().decode("utf-8")
                self.assertEqual(request, jcs(load(vector / "request.json")))
                self.assertEqual(load(BASE / row["expected"]), vector_layout(vector))


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

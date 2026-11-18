"""The terraform-file reading `1.0.0`, status proposed (spec/terraform-file.md), and its vectors.

The vectors under conformance/terraform-file/1.0.0/ are hand-written and synthetic. These tests hold
codes.json to the companion's §9 table and formats.json to its §4 table; the manifest to its files;
and every vector to one expected result of the form §§5 to 9 give it: the acquisition record of its
own input, a value in id order that carries no number and no sensitive text, a refusal of a listed
code with the input's sha256 and size, or batch lines in canonical form. Each declaration is read
by the first reader, tools/dialect_verify.py, which holds a `terraform-file` source to its form and
reads no file (spec/dialect.md §4.5): directly, as §2's members, and as a source of a dialect
document. The reading itself is held by the second reader, tools/terraform_file_reader.py, written
from the companion text alone: every vector, declarations included, must give its expected result
exactly. Two readers agreeing on every vector is the companion's stable bar (§12).
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import re
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "conformance" / "terraform-file" / "1.0.0"
SPEC = ROOT / "spec" / "terraform-file.md"
CODE = re.compile(r"TF-[A-Z]+(?:-[A-Z]+)*")
REFUSALS = {"TF-SIZE", "TF-JSON", "TF-FORMAT", "TF-DOCUMENT", "TF-SENSITIVITY", "TF-SELECT-BOUND", "TF-NUMBER",
            "TF-VALUE-LIMIT"}
# §8: the batch's own refusal, the registry companion's code, and not one of §9's.
BATCH_CODES = {"FACTS-ID-LIMIT"}
DEFAULT_MAX_BYTES = 67108864
ROW_MEMBERS = {"id", "group", "section", "operation", "class", "formatTable", "description", "declaration",
               "expected"}
ROW_OPTIONAL = {"input", "generate", "broken"}
# The groups of conformance/terraform-file/README.md, a closed list: each is a directory under vectors/.
GROUPS = ("formats", "plans", "state", "document", "sensitivity", "mirrors", "diagnostics", "json", "size",
          "selection", "numbers", "value-limit", "deposed", "batch", "declarations", "order")
# A row's section: one or more of the text's sections, each with the steps of §3 it holds, if any.
SECTION = re.compile(r"§(\d+)(?: steps? [1-7](?: and [1-7])?)?(?:, §(\d+)(?: steps? [1-7](?: and [1-7])?)?)*")
GENERATE = {"template", "replace", "with"}
GENERATE_WITH = {"repeat", "times", "quoted"}
IDENTITY = {"address", "type", "name", "mode", "providerName"}
STATE_OPTIONAL = {"index", "deposed", "values"}
PLAN_REQUIRED = IDENTITY | {"actions", "afterUnknown"}
PLAN_OPTIONAL = {"index", "deposed", "before", "after"}
# Every sensitive value and every sensitive member name the vectors write holds this word, and no
# expected result does (§3, step 6).
SENSITIVE = "secret"


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    names = [name for name, _ in pairs]
    if len(names) != len(set(names)):
        raise ValueError("duplicate member")
    return dict(pairs)


def _no_number(literal: str) -> Any:
    raise ValueError(f"a number, {literal}, where the value carries decimal strings")


def load(path: Path) -> Any:
    return json.loads(path.read_bytes().decode("utf-8"), object_pairs_hook=_pairs)


def load_line(text: str) -> Any:
    # §8: a batch line carries the acquired value's objects and strings, so it holds no JSON number.
    return json.loads(text, object_pairs_hook=_pairs, parse_int=_no_number, parse_float=_no_number,
                      parse_constant=_no_number)


def canonical(value: Any) -> str:
    """RFC 8785 for a value with no number in it: members sorted by their UTF-16 code units."""
    if isinstance(value, dict):
        members = sorted(value.items(), key=lambda item: item[0].encode("utf-16-be"))
        return "{" + ",".join(canonical(k) + ":" + canonical(v) for k, v in members) + "}"
    if isinstance(value, list):
        return "[" + ",".join(canonical(v) for v in value) + "]"
    if isinstance(value, (str, bool)) or value is None:
        return json.dumps(value, ensure_ascii=False)
    raise ValueError(f"no canonical form here for {value!r}")


def object_id(resource: dict[str, Any]) -> str:
    # §3, step 4: the address, or for a deposed object the address, " deposed " and its key.
    if "deposed" in resource:
        return resource["address"] + " deposed " + resource["deposed"]
    return resource["address"]


def code_points(text: str) -> list[int]:
    return [ord(c) for c in text]


def first_reader_tests() -> Any:
    """tests/test_dialect.py, which holds the version-3 dialect vector a source is added to, and the first
    reader, loaded once as tests/test_dialect_ts.py loads them."""
    module = sys.modules.get("test_dialect") or sys.modules.get("tests.test_dialect")
    if module is None:
        spec = importlib.util.spec_from_file_location("test_dialect", Path(__file__).with_name("test_dialect.py"))
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules["test_dialect"] = module
        spec.loader.exec_module(module)
    return module


MANIFEST = load(BASE / "manifest.json")
ROWS = MANIFEST["vectors"]
CODES = load(BASE / "codes.json")
FORMATS = load(BASE / "formats.json")


_GENERATED: dict[str, bytes] = {}


def generated(rule: dict[str, Any]) -> bytes:
    """A large input is not committed: its template is, and the rule that writes it (README.md). A rule of
    any other members or forms is refused, not read."""
    if not (isinstance(rule, dict) and set(rule) == GENERATE and isinstance(rule["with"], dict)
            and set(rule["with"]) == GENERATE_WITH and isinstance(rule["template"], str)
            and isinstance(rule["replace"], str) and rule["replace"]
            and isinstance(rule["with"]["repeat"], str) and rule["with"]["repeat"]
            and type(rule["with"]["times"]) is int and rule["with"]["times"] >= 1
            and isinstance(rule["with"]["quoted"], bool)):
        raise ValueError(f"a generate rule not of its form: {rule!r}")
    key = json.dumps(rule, sort_keys=True)
    if key not in _GENERATED:
        _GENERATED[key] = _generate(rule)
    return _GENERATED[key]


def _generate(rule: dict[str, Any]) -> bytes:
    template = (BASE / "vectors" / rule["template"]).read_bytes()
    placeholder = rule["replace"].encode("utf-8")
    if template.count(placeholder) != 1:
        raise ValueError("the template names its placeholder other than once")
    written = rule["with"]["repeat"] * rule["with"]["times"]
    if rule["with"]["quoted"]:
        written = '"' + written + '"'
    return template.replace(placeholder, written.encode("utf-8"))


def input_of(row: dict[str, Any]) -> bytes:
    return generated(row["generate"]) if "generate" in row else (BASE / row["input"]).read_bytes()


def declared_max_bytes(row: dict[str, Any]) -> int:
    return json.loads((BASE / row["declaration"]).read_bytes()).get("maxBytes", DEFAULT_MAX_BYTES)


def expected_of(row: dict[str, Any]) -> Any:
    path = BASE / row["expected"]
    return path.read_bytes() if path.suffix == ".jsonl" else load(path)


def shape_of(row: dict[str, Any]) -> str | None:
    """The one known shape a row's expected result has (README.md), or None for any other."""
    expected = expected_of(row)
    operation = row["operation"]
    if isinstance(expected, bytes):
        return "batch-lines" if operation == "batch" and row["expected"].endswith(".expected.jsonl") else None
    if not row["expected"].endswith(".expected.json") or not isinstance(expected, dict):
        return None
    if set(expected) == {"record", "value"} and operation in ("read", "read-stream"):
        if isinstance(expected["record"], dict) and isinstance(expected["value"], list):
            return "accepted"
        return None
    if set(expected) == {"refusal"} and isinstance(expected["refusal"], dict):
        refusal = expected["refusal"]
        if set(refusal) == {"code", "sha256", "bytes"}:
            return "refusal"
        if refusal == {"code": "TF-SIZE", "stream": True} and operation == "read-stream":
            return "stream-refusal"
        return None
    if expected == {"declaration": "malformed"} and operation == "read":
        return "malformed"
    return None


def holds_a_number(value: Any) -> bool:
    # §6: every number of the acquired value is a decimal string, so the value holds no JSON number.
    if isinstance(value, dict):
        return any(holds_a_number(v) for v in value.values())
    if isinstance(value, list):
        return any(holds_a_number(v) for v in value)
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def declaration_verdicts() -> dict[str, bool | None]:
    """Each declaration file, and whether its vectors expect it malformed: None if they disagree."""
    verdicts: dict[str, set[bool]] = {}
    for row in ROWS:
        verdicts.setdefault(row["declaration"], set()).add(shape_of(row) == "malformed")
    return {name: found.pop() if len(found) == 1 else None for name, found in verdicts.items()}


class TerraformFileListTests(unittest.TestCase):
    def test_code_list_equals_the_section_9_table(self) -> None:
        text = SPEC.read_text(encoding="utf-8")
        table = re.findall(r"^\| `(TF-[A-Z-]+)` \| (error) \| ([^|]+?) \| ([^|]+?) \|$", text, re.M)
        self.assertEqual(8, len(table))
        self.assertEqual([(code, severity, step, raised.replace("`", "")) for code, severity, step, raised in table],
                         [(c["code"], c["severity"], c["step"], c["meaning"]) for c in CODES["codes"]])
        self.assertTrue(all(c["status"] == "active" for c in CODES["codes"]))
        self.assertEqual(REFUSALS, {c["code"] for c in CODES["codes"]})
        for entry in CODES["codes"]:
            with self.subTest(code=entry["code"]):
                self.assertEqual({"code", "severity", "status", "step", "meaning"}, set(entry))

    def test_format_table_equals_the_section_4_table(self) -> None:
        text = SPEC.read_text(encoding="utf-8")
        table = re.findall(r"^\| `(plan|state)` \| ([^|]+?) \|$", text, re.M)
        written = [(document, re.findall(r"`([0-9.]+)`", accepted)) for document, accepted in table]
        self.assertEqual(written, [(row["document"], row["accepted"]) for row in FORMATS["table"]])
        self.assertEqual([("plan", ["1.0", "1.1", "1.2"]), ("state", ["1.0"])], written)
        # §4: the first table's release is 1.0.0, which the record's formatTable carries (§7).
        self.assertIn("The first table's release is `1.0.0`", text)
        self.assertEqual("1.0.0", FORMATS["release"])

    def test_the_text_the_lists_and_the_manifest_say_one_status(self) -> None:
        text = SPEC.read_text(encoding="utf-8")
        said = re.findall(r"^This text is the terraform-file reading `1\.0\.0`, status `([a-z]+)`\.", text, re.M)
        self.assertEqual(["proposed"], said)
        for name, document in (("codes.json", CODES), ("formats.json", FORMATS), ("manifest.json", MANIFEST)):
            with self.subTest(name=name):
                self.assertEqual(("terraform-file", "1.0.0", said[0]),
                                 (document["companion"], document["reading"], document["status"]))


class TerraformFileManifestTests(unittest.TestCase):
    def test_manifest_names_every_file_and_only_files(self) -> None:
        named = {"manifest.json", MANIFEST["codes"], MANIFEST["formats"]}
        for row in ROWS:
            named.update({row["declaration"], row["expected"]})
            named.add(row["input"] if "input" in row else "vectors/" + row["generate"]["template"])
        on_disk = {p.relative_to(BASE).as_posix() for p in BASE.rglob("*") if p.is_file()}
        self.assertEqual(set(), named - on_disk, "named and not on disk")
        self.assertEqual(set(), on_disk - named, "on disk and named by no vector")

    def test_each_vector_has_one_expected_result_and_names_its_table_release(self) -> None:
        headings = set(re.findall(r"^## (\d+)\. ", SPEC.read_text(encoding="utf-8"), re.M))
        ids = [row["id"] for row in ROWS]
        self.assertEqual(len(ids), len(set(ids)))
        expected = [row["expected"] for row in ROWS]
        self.assertEqual(len(expected), len(set(expected)), "two vectors share an expected file")
        for row in ROWS:
            with self.subTest(id=row["id"]):
                self.assertTrue(ROW_MEMBERS <= set(row) <= ROW_MEMBERS | ROW_OPTIONAL, sorted(row))
                self.assertEqual(1, ("input" in row) + ("generate" in row))
                self.assertEqual("reader", row["class"])
                self.assertEqual(FORMATS["release"], row["formatTable"])
                self.assertIn(row["operation"], ("read", "read-stream", "batch"))
                self.assertIn(row["group"], GROUPS)
                self.assertTrue(row["expected"].startswith(f"vectors/{row['group']}/{row['id']}.expected."))
                self.assertTrue(row["declaration"].startswith("declarations/"))
                cited = SECTION.fullmatch(row["section"])
                self.assertIsNotNone(cited, row["section"])
                for number in re.findall(r"§(\d+)", row["section"]):
                    self.assertIn(number, headings, row["section"])

    def test_the_groups_are_a_closed_list(self) -> None:
        self.assertEqual(set(GROUPS), {row["group"] for row in ROWS})
        self.assertEqual(set(GROUPS), {p.name for p in (BASE / "vectors").iterdir() if p.is_dir()})

    def test_every_expected_result_is_of_one_known_shape(self) -> None:
        for row in ROWS:
            with self.subTest(id=row["id"]):
                self.assertIsNotNone(shape_of(row), row["expected"])

    def test_a_generated_input_is_small_as_committed_and_follows_its_rule(self) -> None:
        rows = [row for row in ROWS if "generate" in row]
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(id=row["id"]):
                template = BASE / "vectors" / row["generate"]["template"]
                self.assertLess(template.stat().st_size, 4096)
                data = generated(row["generate"])
                result = expected_of(row)
                pinned = result["record"] if shape_of(row) == "accepted" else result["refusal"]
                self.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), (pinned["sha256"], pinned["bytes"]))
        for path in BASE.rglob("*"):
            if path.is_file():
                with self.subTest(path=path.relative_to(BASE).as_posix()):
                    self.assertLess(path.stat().st_size, 131072)

    def test_the_corpus_covers_every_row_code_and_declaration_form(self) -> None:
        accepted = {(e["record"]["document"], e["record"]["formatVersion"])
                    for e in (expected_of(r) for r in ROWS) if isinstance(e, dict) and "record" in e}
        for row in FORMATS["table"]:
            for version in row["accepted"]:
                with self.subTest(document=row["document"], formatVersion=version):
                    self.assertIn((row["document"], version), accepted)
        results = [expected_of(r) for r in ROWS]
        refused = {e["refusal"]["code"] for e in results if isinstance(e, dict) and "refusal" in e}
        self.assertEqual(REFUSALS | BATCH_CODES, refused)
        operations = {(r["operation"], isinstance(e, dict) and "refusal" in e) for r, e in zip(ROWS, results)}
        for operation in ("read-stream", "batch"):
            for refusal in (True, False):
                with self.subTest(operation=operation, refusal=refusal):
                    self.assertIn((operation, refusal), operations)
        # §2: a declared integer is an integer literal, and a member of another type is malformed; each
        # read with no file.
        verdicts = declaration_verdicts()
        for name in ("declaration-max-bytes-1.0", "declaration-max-bytes-1e2", "declaration-mode-number",
                     "declaration-actions-number"):
            with self.subTest(declaration=name):
                self.assertIs(True, verdicts[f"declarations/{name}.json"])


class TerraformFileResultTests(unittest.TestCase):
    def test_an_accepted_result_is_the_record_of_its_input_and_a_value_of_section_6s_form(self) -> None:
        accepted = {(row["document"], v) for row in FORMATS["table"] for v in row["accepted"]}
        rows = [row for row in ROWS if shape_of(row) == "accepted"]
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(id=row["id"]):
                data = input_of(row)
                result = expected_of(row)
                self.assertEqual({"record", "value"}, set(result))
                record, value = result["record"], result["value"]
                document = json.loads((BASE / row["declaration"]).read_bytes())["document"]
                self.assertEqual({"kind": "terraform-file", "document": document, "formatTable": FORMATS["release"],
                                  "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                                  "selected": len(value)},
                                 {k: record[k] for k in record if k not in ("formatVersion", "removedSensitive")})
                self.assertEqual(set(record), {"kind", "document", "formatVersion", "formatTable", "sha256", "bytes",
                                               "removedSensitive", "selected"})
                self.assertIn((document, record["formatVersion"]), accepted)
                self.assertTrue(isinstance(record["removedSensitive"], int) and record["removedSensitive"] >= 0)
                self.assertLessEqual(len(data), declared_max_bytes(row))
                self.assertFalse(holds_a_number(value))
                self.assert_value(document, value)

    def assert_value(self, document: str, value: list[dict[str, Any]]) -> None:
        ids = [object_id(resource) for resource in value]
        self.assertEqual(sorted(ids, key=code_points), ids, "not in code-point order of id")
        self.assertEqual(len(ids), len(set(ids)))
        for resource in value:
            self.assertTrue(all(isinstance(resource[m], str) for m in IDENTITY), resource)
            if document == "state":
                self.assertTrue(IDENTITY <= set(resource) <= IDENTITY | STATE_OPTIONAL, sorted(resource))
            else:
                self.assertTrue(PLAN_REQUIRED <= set(resource) <= PLAN_REQUIRED | PLAN_OPTIONAL, sorted(resource))
                self.assertTrue(resource["actions"] and all(isinstance(a, str) for a in resource["actions"]))
                pointers = resource["afterUnknown"]
                self.assertEqual(sorted(pointers, key=code_points), pointers)
                self.assertEqual(len(pointers), len(set(pointers)))
                self.assertTrue(all(p == "" or p.startswith("/") for p in pointers), pointers)
            if "deposed" in resource:
                self.assertTrue(isinstance(resource["deposed"], str) and resource["deposed"])

    def test_a_refusal_names_a_listed_code_and_its_input_only(self) -> None:
        rows = [row for row in ROWS if shape_of(row) in ("refusal", "stream-refusal")]
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(id=row["id"]):
                refusal = expected_of(row)["refusal"]
                data = input_of(row)
                over = len(data) > declared_max_bytes(row)
                if refusal.get("stream"):
                    # §3, step 1: a stream past maxBytes is read one byte past it, so neither its sha256 nor
                    # its size is known.
                    self.assertEqual({"code": "TF-SIZE", "stream": True}, refusal)
                    self.assertEqual("read-stream", row["operation"])
                    self.assertTrue(over)
                    continue
                self.assertEqual({"code", "sha256", "bytes"}, set(refusal))
                self.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), (refusal["sha256"], refusal["bytes"]))
                codes = REFUSALS | (BATCH_CODES if row["operation"] == "batch" else set())
                self.assertIn(refusal["code"], codes)
                self.assertEqual(refusal["code"] == "TF-SIZE", over)

    def test_a_batch_is_one_canonical_line_per_selected_resource(self) -> None:
        rows = [row for row in ROWS if shape_of(row) == "batch-lines"]
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(id=row["id"]):
                data = input_of(row)
                text = expected_of(row).decode("utf-8")
                self.assertTrue(text == "" or text.endswith("\n"))
                lines = [load_line(line) for line in text.splitlines()]
                self.assertEqual(text, "".join(canonical(line) + "\n" for line in lines))
                document = json.loads((BASE / row["declaration"]).read_bytes())["document"]
                for line in lines:
                    self.assertEqual({"facts", "id"}, set(line))
                    self.assertEqual({"resource", "terraform"}, set(line["facts"]))
                    terraform = line["facts"]["terraform"]
                    self.assertEqual({"document": document, "sha256": hashlib.sha256(data).hexdigest()},
                                     {k: terraform[k] for k in ("document", "sha256")})
                    self.assertEqual({"document", "formatVersion", "sha256"}, set(terraform))
                    self.assertEqual(object_id(line["facts"]["resource"]), line["id"])
                    self.assertTrue(1 <= len(line["id"].encode("utf-8")) <= 256)
                self.assert_value(document, [line["facts"]["resource"] for line in lines])

    def test_no_expected_result_carries_a_sensitive_value(self) -> None:
        # §3, step 6: nothing from a position marked sensitive reaches the value, the record or a batch line.
        marked = [row for row in ROWS if SENSITIVE.encode() in input_of(row)]
        self.assertGreater(len(marked), 20)
        for row in ROWS:
            with self.subTest(id=row["id"]):
                self.assertNotIn(SENSITIVE.encode(), (BASE / row["expected"]).read_bytes().lower())


class TerraformFileDeclarationTests(unittest.TestCase):
    """§2: a declaration is a source's members, held to their forms with no file read. The first reader holds a
    `terraform-file` source to those forms (spec/dialect.md §4.5) and then refuses it `kind-unread`."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tests = first_reader_tests()
        cls.reader = cls.tests.READER
        cls.verdicts = declaration_verdicts()

    def test_every_declaration_has_one_verdict(self) -> None:
        self.assertEqual([], sorted(name for name, verdict in self.verdicts.items() if verdict is None))
        on_disk = {p.relative_to(BASE).as_posix() for p in (BASE / "declarations").glob("*.json")}
        self.assertEqual(on_disk, set(self.verdicts))

    def test_the_first_reader_holds_each_declaration_to_its_form(self) -> None:
        required, optional = self.reader.TERRAFORM_MEMBERS
        for name, malformed in sorted(self.verdicts.items()):
            with self.subTest(declaration=name):
                data = (BASE / name).read_bytes()
                try:
                    value = self.reader.read_document(data, "declaration")
                    self.reader.check_terraform_file(self.reader.closed(value, required, optional, "declaration"),
                                                     "declaration")
                    verdict = False
                except self.reader.Refused as refused:
                    self.assertEqual("input-malformed", refused.name)
                    verdict = True
                self.assertEqual(malformed, verdict)

    def test_each_declaration_is_read_as_a_source_of_a_dialect_document(self) -> None:
        # Added to the version-3-bound vector's dialect as test_dialect.py's terraform_file_cases() adds one,
        # its bytes spliced in as written, so that a literal such as 1e2 stays as written. A malformed source
        # is input-malformed, a well-formed one kind-unread. A declaration that is not an object cannot be a
        # source's members; it is held directly above. On this path the dialect document's own number domain
        # (spec/dialect.md §1) refuses 1.0 and 1e2 before any source is read.
        placeholder = "\u0000terraform-file source"
        for name, malformed in sorted(self.verdicts.items()):
            text = (BASE / name).read_text(encoding="utf-8").strip()
            if not text.startswith("{"):
                continue
            with self.subTest(declaration=name):
                inputs = self.tests.Inputs("version-3-bound", self.tests.REQUIRES_BINDING["version-3-bound"])
                document = json.loads(inputs.dialect)
                document["sources"].append(placeholder)
                inner = text[1:].lstrip()
                source = ('{"name": "terraform", "kind": "terraform-file", "read": {"copy": {"facts": [], '
                          '"evidence": []}}' + ("" if inner.startswith("}") else ", ") + inner)
                written = json.dumps(document)
                self.assertEqual(1, written.count(json.dumps(placeholder)))
                inputs.dialect = written.replace(json.dumps(placeholder), source).encode("utf-8")
                result = self.reader.report(inputs.verify().answer)
                expected = "refusal:input-malformed" if malformed else "refusal:kind-unread"
                self.assertEqual(expected, f"{result['result']}:{result[result['result']]}", result)


class _CountingStream(io.RawIOBase):
    """A stream that counts what is read from it, so a test sees a stream read past maxBytes plus one."""

    def __init__(self, data: bytes) -> None:
        self.data = io.BytesIO(data)
        self.taken = 0

    def readable(self) -> bool:
        return True

    def read(self, size: int = -1) -> bytes:
        chunk = self.data.read(size)
        self.taken += len(chunk)
        return chunk


def exact(value: Any) -> str:
    # One text per value that tells true from 1, so a comparison holds members, types and order exactly.
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


class TerraformFileSecondReaderTests(unittest.TestCase):
    """The second reader, tools/terraform_file_reader.py, written from the companion text alone, over every
    vector of the manifest: each must equal its expected result exactly, a refusal's code and members, an
    accepted read's record and value (its canonical bytes too), or a batch's bytes."""

    @classmethod
    def setUpClass(cls) -> None:
        from tools import terraform_file_reader
        cls.reader = terraform_file_reader

    def result_of(self, row: dict[str, Any]) -> Any:
        reader = self.reader
        try:
            declaration = reader.read_declaration((BASE / row["declaration"]).read_bytes())
        except reader.Malformed:
            return {"declaration": "malformed"}
        data = input_of(row)
        if row["operation"] == "batch":
            written = reader.batch(data, declaration)
            return written if isinstance(written, bytes) else {"refusal": written.as_json()}
        if row["operation"] == "read-stream":
            stream = _CountingStream(data)
            result = reader.read_stream(stream, declaration)
            # §3, step 1: a stream is read to at most maxBytes and one byte more.
            self.assertLessEqual(stream.taken, declaration.max_bytes + 1)
        else:
            result = reader.read(data, declaration)
        if isinstance(result, reader.Refused):
            return {"refusal": result.as_json()}
        return {"record": result.record, "value": result.value}

    def test_every_vector_gives_its_expected_result(self) -> None:
        agreed = 0
        for row in ROWS:
            with self.subTest(id=row["id"]):
                expected = expected_of(row)
                found = self.result_of(row)
                if isinstance(expected, bytes):
                    self.assertIsInstance(found, bytes)
                    self.assertEqual(expected.decode("utf-8"), found.decode("utf-8"))
                else:
                    self.assertEqual(exact(expected), exact(found))
                    if "value" in expected:
                        self.assertEqual(canonical(expected["value"]).encode("utf-8"),
                                         self.reader.canonical(found["value"]).encode("utf-8"))
                agreed += 1
        self.assertEqual(len(ROWS), agreed)

    def test_the_reader_holds_its_bounds_on_inputs_no_vector_writes(self) -> None:
        reader = self.reader
        # §6: a number's normal-form length is found before it is written, so an exponent of thirty
        # digits is TF-NUMBER at once, and a zero is 0 whatever its exponent.
        self.assertIsNone(reader.normal_form("1e" + "9" * 30))
        self.assertIsNone(reader.normal_form("1e-" + "9" * 30))
        self.assertEqual("0", reader.normal_form("-0.0e" + "9" * 30))
        self.assertEqual("100", reader.normal_form("1e" + "0" * 40 + "2"))
        self.assertEqual("-0.0000001", reader.normal_form("-1e-7"))
        # §3, step 2: depth is held while parsing, so a hundred thousand open brackets are TF-JSON.
        declaration = reader.read_declaration(b'{"document": "plan", "select": {"types": ["t"]}}')
        bomb = b"[" * 100000
        self.assertEqual(reader.Refused("TF-JSON", hashlib.sha256(bomb).hexdigest(), len(bomb)),
                         reader.read(bomb, declaration))
        # §5: the address pattern is matched one character at a time, with no backtracking.
        self.assertFalse(reader.address_matches("*a" * 256, "a" * 20000 + "b"))
        self.assertTrue(reader.address_matches("m.*.r[*]", "m.x.r[0]"))
        self.assertFalse(reader.address_matches("m.*.r", "m.x.y.r"))

    def test_the_reader_and_the_first_reader_give_each_declaration_one_verdict(self) -> None:
        for name, malformed in sorted(declaration_verdicts().items()):
            with self.subTest(declaration=name):
                try:
                    self.reader.read_declaration((BASE / name).read_bytes())
                    verdict = False
                except self.reader.Malformed:
                    verdict = True
                self.assertEqual(malformed, verdict)


if __name__ == "__main__":
    unittest.main()

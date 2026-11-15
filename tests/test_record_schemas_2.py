"""Version 2 of the dialect-recording schemas: preparations of the proposed formats 4.0.0 and 4.1.0 and an
export carrying one, staged for specVersion 0.6.0 (RFC 0018, the amendment of 2026-11-15, issue #326).

Every reading among the staged vectors of both formats validates against version 2 and none against version 1;
no preparation or export of version 1's form validates against version 2 (decision 3)."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from test_record_schemas import exports, preparations, read

ROOT = Path(__file__).resolve().parents[1]
DIALECT = ROOT / "conformance" / "dialect"
NAMESPACE = "https://judgmentpack.org/"
VERSION_1 = {"preparation": "schema/dialect-recording/1/preparation.schema.json",
             "export": "schema/dialect-recording/1/export.schema.json"}
VERSION_2 = {"preparation": "schema/dialect-recording/2/preparation.schema.json",
             "export": "schema/dialect-recording/2/export.schema.json"}
DECISION_RECORD = "schema/decision-record/1/record.schema.json"
# The staged sets are frozen; a reading added to one changes this count in the same change.
READINGS = 30


def validators() -> dict[str, Draft202012Validator]:
    schemas = {(version, name): read(ROOT / path) for version, paths in ((1, VERSION_1), (2, VERSION_2))
               for name, path in paths.items()}
    registry = Registry().with_resources((schema["$id"], Resource.from_contents(schema)) for schema in schemas.values())
    checker = FormatChecker()
    return {key: Draft202012Validator(schema, registry=registry, format_checker=checker) for key, schema in schemas.items()}


def readings() -> list[tuple[str, dict]]:
    """The preparation of every reading among the staged vectors of formats 4.0.0 and 4.1.0."""
    found = []
    for directory in ("format-4", "format-4.1"):
        manifest = json.loads((DIALECT / directory / "manifest.json").read_text(encoding="utf-8"))
        for case in manifest.get("cases") or manifest["vectors"]:
            expected = case.get("expectedReport") or case.get("expected")
            if expected["result"] == "reading":
                found.append((f"{directory}/{case['name']}", read(DIALECT / directory / case["name"] / "preparation.json")))
    return found


class Version2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validators = validators()

    def valid(self, version: int, name: str, value: object) -> bool:
        return self.validators[(version, name)].is_valid(value)

    def test_each_schema_is_valid_at_its_own_id_and_says_its_standing(self) -> None:
        for path in VERSION_2.values():
            with self.subTest(path=path):
                schema = read(ROOT / path)
                Draft202012Validator.check_schema(schema)
                self.assertEqual(NAMESPACE + path, schema["$id"])
                self.assertTrue(schema["description"].startswith(
                    "Informative, at draft maturity, staged for specVersion 0.6.0 (RFC 0018, the amendment of "
                    "2026-11-15, issue #326). "))
                self.assertIn("Core section 1.1 does not list this schema among the normative artifacts, so "
                              "publishing it changes no format's normative status", schema["description"])

    def test_the_export_is_version_1s_carrying_the_new_preparation(self) -> None:
        one, two = read(ROOT / VERSION_1["export"]), read(ROOT / VERSION_2["export"])
        expected = copy.deepcopy(one)
        for member in ("$id", "title", "description"):
            expected[member] = two[member]
        expected["properties"]["run"]["properties"]["input"]["properties"]["preparation"]["$ref"] = (
            NAMESPACE + VERSION_2["preparation"])
        self.assertEqual(expected, two)
        record = {name: value for name, value in read(ROOT / DECISION_RECORD).items()
                  if name not in ("$schema", "$id", "title", "description")}
        copied = dict(two["$defs"]["record"])
        copied.pop("description")
        self.assertEqual(record, copied)

    def test_every_reading_of_both_formats_validates_against_version_2_alone(self) -> None:
        found = readings()
        self.assertEqual(READINGS, len(found))
        self.assertEqual({"4.0.0", "4.1.0"}, {value["formatVersion"] for _, value in found})
        for where, value in found:
            with self.subTest(vector=where):
                self.assertEqual([], [e.message for e in self.validators[(2, "preparation")].iter_errors(value)])
                self.assertFalse(self.valid(1, "preparation", value))

    def test_a_recording_of_either_format_validates_against_version_2s_export_alone(self) -> None:
        where, export = exports()[0]
        for vector, preparation in (readings()[0], readings()[-1]):
            with self.subTest(vector=vector):
                carried = copy.deepcopy(export)
                carried["run"]["input"]["preparation"] = preparation
                self.assertTrue(self.valid(2, "export", carried), where)
                self.assertFalse(self.valid(1, "export", carried))

    def test_version_2_does_not_read_version_1s_form(self) -> None:
        # decision 3: a preparation of version 2 or 3, and an export carrying one, are version 1's alone
        found = preparations()
        self.assertEqual(190, len(found))
        for where, value in found:
            with self.subTest(vector=where):
                self.assertTrue(self.valid(1, "preparation", value))
                self.assertFalse(self.valid(2, "preparation", value))
        for where, value in exports():
            with self.subTest(recording=where):
                self.assertTrue(self.valid(1, "export", value))
                self.assertFalse(self.valid(2, "export", value))
        # a preparation of version 1's form given a format selector is still not version 2's form
        _, value = found[0]
        both = {**copy.deepcopy(value), "formatVersion": "4.0.0"}
        self.assertFalse(self.valid(2, "preparation", both))


if __name__ == "__main__":
    unittest.main()

"""The terraform-file reading's declarations (spec/terraform-file.md §2), read by the first reader.

Each declaration under conformance/terraform-file/1.0.0/declarations/ is read by tools/dialect_verify.py,
which holds a `terraform-file` source to its form and reads no file (spec/dialect.md §4.5): directly, as
§2's members, and as a source of a dialect document. These checks need the first reader and the dialect's
staged vectors (tests/test_dialect.py), which no bundle carries, so they are kept apart from
tests/test_terraform_file_vectors.py, whose checks need only the companion's own files and its second
reader, and run inside the companion's bundle (VERSIONING.md, "Independently versioned terraform-file
companion"). Those checks hold the second reader to the same verdict on each declaration.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from typing import Any


def sibling(name: str) -> Any:
    """A module of this directory, loaded once whether the suite runs from the repository root, as
    `tests.<name>`, or from this directory, as `<name>`, as tests/test_dialect_ts.py loads them."""
    module = sys.modules.get(name) or sys.modules.get(f"tests.{name}")
    if module is None:
        spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(f"{name}.py"))
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module


class TerraformFileDeclarationTests(unittest.TestCase):
    """§2: a declaration is a source's members, held to their forms with no file read. The first reader holds a
    `terraform-file` source to those forms (spec/dialect.md §4.5) and then refuses it `kind-unread`."""

    @classmethod
    def setUpClass(cls) -> None:
        # tests/test_dialect.py holds the version-3 dialect vector a source is added to, and the first reader.
        cls.tests = sibling("test_dialect")
        cls.reader = cls.tests.READER
        cls.vectors = sibling("test_terraform_file_vectors")
        cls.verdicts = cls.vectors.declaration_verdicts()

    def test_the_declarations_are_the_vectors(self) -> None:
        # Every declaration file is read below, and each has one verdict (test_terraform_file_vectors.py).
        on_disk = {p.relative_to(self.vectors.BASE).as_posix()
                   for p in (self.vectors.BASE / "declarations").glob("*.json")}
        self.assertTrue(on_disk)
        self.assertEqual(on_disk, set(self.verdicts))
        self.assertNotIn(None, self.verdicts.values())

    def test_the_first_reader_holds_each_declaration_to_its_form(self) -> None:
        required, optional = self.reader.TERRAFORM_MEMBERS
        for name, malformed in sorted(self.verdicts.items()):
            with self.subTest(declaration=name):
                data = (self.vectors.BASE / name).read_bytes()
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
            text = (self.vectors.BASE / name).read_text(encoding="utf-8").strip()
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


if __name__ == "__main__":
    unittest.main()

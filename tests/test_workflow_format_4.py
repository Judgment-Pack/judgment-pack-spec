"""Dialect formats 4.0.0 and 4.1.0 in a workflow stage, staged for specVersion 0.6.0 (issue #326; RFC 0020,
the amendment proposal of 2026-11-15): the staged workflow schema, and the release digest RFC 0020 section 1
writes into its own text for the two formats, held to the RFC's worked examples."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import dialect_verify as d  # noqa: E402
from tools import workflow_reader_encoding as encoding  # noqa: E402

RFC = ROOT / "rfcs" / "0020-workflow.md"
PUBLISHED = ROOT / "schema" / "workflow-1.schema.json"
STAGED = ROOT / "schema" / "workflow-1-0.6.0.schema.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def reference_validator(schema: dict) -> jsonschema.Draft202012Validator:
    """A validator of the schema's named or integer dialect reference alone."""
    return jsonschema.Draft202012Validator({"$schema": schema["$schema"], "$defs": schema["$defs"],
                                            "$ref": "#/$defs/dialectReference"}, format_checker=jsonschema.FormatChecker())


def named(format_version: object) -> dict:
    return {"formatVersion": format_version, "id": "urn:example:dialect:four", "version": "1.0.0",
            "digest": "sha256:" + "a" * 64}


def worked_examples() -> list[tuple[str, str]]:
    """The amendment's worked examples: each one-line JSON block and the digest the text gives it."""
    text = RFC.read_text(encoding="utf-8")
    section = text.split("## Amendment proposal of 2026-11-15", 1)[1].split("\n## ", 1)[0]
    found = re.findall(r"```json\n(.*?)\n```\n\nIts release digest is\n`(sha256:[0-9a-f]{64})`", section, re.S)
    return found


class StagedSchemaTests(unittest.TestCase):
    def test_the_staged_schema_is_the_published_one_with_the_two_formats(self) -> None:
        published, staged = load(PUBLISHED), load(STAGED)
        self.assertEqual("https://judgmentpack.org/schema/0.6.0/workflow-1.schema.json", staged["$id"])
        expected = copy.deepcopy(published)
        expected["$id"] = staged["$id"]
        expected["$defs"]["dialectReference"]["oneOf"][1]["properties"]["formatVersion"]["enum"] += ["4.0.0", "4.1.0"]
        self.assertEqual(expected, staged)

    def test_the_published_schema_still_refuses_the_two_formats(self) -> None:
        validator = reference_validator(load(PUBLISHED))
        for format_version in ("2.0.0", "3.0.0"):
            self.assertTrue(validator.is_valid(named(format_version)), format_version)
        for format_version in ("4.0.0", "4.1.0"):
            self.assertFalse(validator.is_valid(named(format_version)), format_version)

    def test_the_staged_schema_admits_the_two_formats_and_no_other(self) -> None:
        validator = reference_validator(load(STAGED))
        for format_version in ("2.0.0", "3.0.0", "4.0.0", "4.1.0"):
            self.assertTrue(validator.is_valid(named(format_version)), format_version)
        for format_version in ("4.2.0", "5.0.0", "4.0", 4, None):
            self.assertFalse(validator.is_valid(named(format_version)), format_version)
        # no integer twin: integer version 4 stays outside the legacy form
        self.assertFalse(validator.is_valid({"version": 4, "digest": "sha256:" + "a" * 64}))
        self.assertTrue(validator.is_valid({"version": 3, "digest": "sha256:" + "a" * 64}))

    def test_the_companion_names_the_two_formats_as_staged(self) -> None:
        for path in (RFC, ROOT / "spec" / "workflow.md"):
            text = path.read_text(encoding="utf-8")
            self.assertIn("Staged for `specVersion` `0.6.0`, `formatVersion` may also be `\"4.0.0\"` or `\"4.1.0\"`", text)
            self.assertIn("a stage whose dialect is of format `4.0.0` or\n`4.1.0` takes no Runner encoding", text)


class ReleaseDigestTests(unittest.TestCase):
    def test_the_worked_examples_digest_as_the_text_gives(self) -> None:
        examples = worked_examples()
        self.assertEqual(2, len(examples))
        self.assertEqual(["4.0.0", "4.1.0"], [json.loads(line)["inputMapping"]["formatVersion"] for line, _ in examples])
        for line, stated in examples:
            with self.subTest(stated=stated):
                raw = line.encode("utf-8")
                # each line is already its canon bytes, so its digest is SHA-256 of the line
                self.assertEqual(stated, "sha256:" + hashlib.sha256(raw).hexdigest())
                value = d.read_document(raw, "worked example")
                self.assertEqual(raw, d.canon(value))
                self.assertEqual(raw, encoding.release_digest_bytes(value))

    def test_the_pinned_encoding_drops_the_members_the_formats_add(self) -> None:
        (rule_line, rule_digest), (paged_line, paged_digest) = worked_examples()
        for line, stated, member in ((rule_line, rule_digest, b'"rule"'), (paged_line, paged_digest, b'"paging"')):
            pinned = encoding.release_bytes(d.read_document(line.encode("utf-8"), "worked example"))
            self.assertNotIn(member, pinned)
            self.assertNotEqual(stated, "sha256:" + hashlib.sha256(pinned).hexdigest())

    def test_every_member_counts_and_none_is_defaulted(self) -> None:
        (line, stated), _ = worked_examples()
        value = d.read_document(line.encode("utf-8"), "worked example")
        for change in (lambda v: v.__setitem__("note", None),
                       lambda v: v["inputMapping"]["case"]["rule"].__setitem__("ruleVersion", "1"),
                       lambda v: v.pop("runtimeDigest")):
            changed = copy.deepcopy(value)
            change(changed)
            self.assertNotEqual(stated, "sha256:" + hashlib.sha256(encoding.release_digest_bytes(changed)).hexdigest())

    def test_a_release_outside_the_canon_domain_is_refused(self) -> None:
        (line, _), _ = worked_examples()
        value = d.read_document(line[:-1].encode("utf-8") + b',"weight":1.5}', "release")
        with self.assertRaises(d.Refused) as caught:
            encoding.release_digest_bytes(value)
        self.assertEqual("input-malformed", caught.exception.name)

    def test_other_formats_keep_the_pinned_encoding(self) -> None:
        (line, _), _ = worked_examples()
        for mapping in ({"formatVersion": "3.0.0", "id": "urn:example:dialect:three", "version": "1.0.0", "sources": []},
                        {"version": 3, "sources": []}):
            value = d.read_document(line.encode("utf-8"), "release")
            value["inputMapping"] = d.read_document(d.canon(mapping), "mapping")
            self.assertEqual(encoding.release_bytes(value), encoding.release_digest_bytes(value))


if __name__ == "__main__":
    unittest.main()

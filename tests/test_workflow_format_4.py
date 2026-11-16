"""Dialect formats 4.0.0 and 4.1.0 in a workflow stage, for specVersion 0.6.0 (issue #326; RFC 0020, the
amendment of 2026-11-15): the workflow schema of 0.6.0, which Core 0.6.0 moved in place from its staged
copy, and the release digest RFC 0020 section 1 writes into its own text for the two formats, held to the
RFC's worked examples."""

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
# The 0.6.0 schema is the one staged for it, moved in place; 0.5.0's stays as its preserved copy.
PUBLISHED = ROOT / "schema" / "workflow-1.schema.json"
PREVIOUS = ROOT / "schema" / "workflow-1-0.5.0.schema.json"


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
    section = text.split("## Amendment of 2026-11-15", 1)[1].split("\n## ", 1)[0]
    found = re.findall(r"```json\n(.*?)\n```\n\nIts release digest is\n`(sha256:[0-9a-f]{64})`", section, re.S)
    return found


class SchemaTests(unittest.TestCase):
    def test_the_0_6_0_schema_is_the_0_5_0_one_with_the_two_formats(self) -> None:
        previous, published = load(PREVIOUS), load(PUBLISHED)
        self.assertEqual("https://judgmentpack.org/schema/0.6.0/workflow-1.schema.json", published["$id"])
        self.assertEqual("https://judgmentpack.org/schema/0.5.0/workflow-1.schema.json", previous["$id"])
        self.assertFalse((ROOT / "schema" / "workflow-1-0.6.0.schema.json").exists())
        expected = copy.deepcopy(previous)
        expected["$id"] = published["$id"]
        expected["$defs"]["dialectReference"]["oneOf"][1]["properties"]["formatVersion"]["enum"] += ["4.0.0", "4.1.0"]
        self.assertEqual(expected, published)

    def test_the_0_5_0_schema_still_refuses_the_two_formats(self) -> None:
        validator = reference_validator(load(PREVIOUS))
        for format_version in ("2.0.0", "3.0.0"):
            self.assertTrue(validator.is_valid(named(format_version)), format_version)
        for format_version in ("4.0.0", "4.1.0"):
            self.assertFalse(validator.is_valid(named(format_version)), format_version)

    def test_the_0_6_0_schema_admits_the_two_formats_and_no_other(self) -> None:
        validator = reference_validator(load(PUBLISHED))
        for format_version in ("2.0.0", "3.0.0", "4.0.0", "4.1.0"):
            self.assertTrue(validator.is_valid(named(format_version)), format_version)
        for format_version in ("4.2.0", "5.0.0", "4.0", 4, None):
            self.assertFalse(validator.is_valid(named(format_version)), format_version)
        # no integer twin: integer version 4 stays outside the legacy form
        self.assertFalse(validator.is_valid({"version": 4, "digest": "sha256:" + "a" * 64}))
        self.assertTrue(validator.is_valid({"version": 3, "digest": "sha256:" + "a" * 64}))

    def test_the_companion_names_the_two_formats_since_0_6_0(self) -> None:
        for path in (RFC, ROOT / "spec" / "workflow.md"):
            text = path.read_text(encoding="utf-8")
            self.assertIn("Since `specVersion` `0.6.0`, `formatVersion` may also be `\"4.0.0\"` or `\"4.1.0\"`", text)
            self.assertNotIn("Staged for `specVersion` `0.6.0`", text)
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
                self.assertEqual(raw, encoding.release_digest_bytes(value, value["inputMapping"]["formatVersion"]))

    def test_the_pinned_encoding_drops_the_members_the_formats_add(self) -> None:
        (rule_line, rule_digest), (paged_line, paged_digest) = worked_examples()
        for line, stated, member in ((rule_line, rule_digest, b'"rule"'), (paged_line, paged_digest, b'"paging"')):
            pinned = encoding.release_bytes(d.read_document(line.encode("utf-8"), "worked example"))  # the 0.5.x rule
            self.assertNotIn(member, pinned)
            self.assertNotEqual(stated, "sha256:" + hashlib.sha256(pinned).hexdigest())

    def test_every_member_counts_and_none_is_defaulted(self) -> None:
        # the form is open: a member the four required ones do not name is admitted and digested
        (line, stated), _ = worked_examples()
        value = d.read_document(line.encode("utf-8"), "worked example")
        for change in (lambda v: v.__setitem__("note", None),
                       lambda v: v.__setitem__("createdAt", "2026-11-15T12:00:00Z"),
                       lambda v: v["inputMapping"]["case"]["rule"].__setitem__("ruleVersion", "1")):
            changed = copy.deepcopy(value)
            change(changed)
            self.assertNotEqual(stated, "sha256:" + hashlib.sha256(encoding.release_digest_bytes(changed, "4.0.0")).hexdigest())

    def test_a_release_without_a_required_member_is_refused(self) -> None:
        (line, _), _ = worked_examples()
        value = d.read_document(line.encode("utf-8"), "worked example")
        for name, wrong in (("id", 1), ("packDigest", "sha256:1"), ("runtimeDigest", None)):
            for change in (lambda v: v.pop(name), lambda v: v.__setitem__(name, wrong)):
                changed = copy.deepcopy(value)
                change(changed)
                with self.subTest(member=name, changed=changed.get(name, "absent")):
                    with self.assertRaises(d.Refused) as caught:
                        encoding.release_digest_bytes(changed, "4.0.0")
                    self.assertEqual("input-malformed", caught.exception.name)

    def test_the_rfc_lists_the_runner_members_the_vector_carries(self) -> None:
        directory = ROOT / "conformance" / "dialect" / "workflow-format-4"
        release = load(directory / "stage-4.0.0.runner-release.json")
        runner = {"id", "inputMapping", "packDigest", "runtimeDigest", "schemaVersion", "pack", "packId",
                  "packVersion", "title", "createdAt", "config", "lock", "validation", "sample", "preview", "tests",
                  "dialect", "inputProfiles", "mappingWarnings", "testEvidence", "suppliedReviewedSet"}
        self.assertEqual(runner, set(release))
        for path in (RFC, ROOT / "spec" / "workflow.md"):
            section = " ".join(path.read_text(encoding="utf-8").split("For instance, not as a pin,", 1)[1]
                               .split("The release digest is", 1)[0].split())
            self.assertEqual(runner - {"id", "inputMapping", "packDigest", "runtimeDigest"},
                             set(re.findall(r"`([A-Za-z]+)`", section)) - {"Release"}, path.name)

    def test_a_release_outside_the_canon_domain_is_refused(self) -> None:
        (line, _), _ = worked_examples()
        value = d.read_document(line[:-1].encode("utf-8") + b',"weight":1.5}', "release")
        with self.assertRaises(d.Refused) as caught:
            encoding.release_digest_bytes(value, "4.0.0")
        self.assertEqual("input-malformed", caught.exception.name)

    def test_the_0_6_0_schemas_are_bundled_and_the_vectors_are_not(self) -> None:
        # Released with 0.6.0: the workflow schema and version 2 of the dialect-recording schemas are in
        # the bundle; the format vectors stay in no corpus and no bundle.
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
        self.assertEqual([], [line for line in attributes
                              if line.startswith(("schema/workflow-1", "schema/dialect-recording"))])
        self.assertIn("conformance/dialect/** export-ignore -text", attributes)

    def test_other_formats_keep_the_pinned_encoding(self) -> None:
        (line, _), _ = worked_examples()
        for mapping, format_version in (({"formatVersion": "3.0.0", "id": "urn:example:dialect:three", "version": "1.0.0",
                                          "sources": []}, "3.0.0"), ({"version": 3, "sources": []}, None)):
            value = d.read_document(line.encode("utf-8"), "release")
            value["inputMapping"] = d.read_document(d.canon(mapping), "mapping")
            self.assertEqual(encoding.release_bytes(value), encoding.release_digest_bytes(value, format_version))

    def test_the_stage_reference_not_the_release_selects_the_rule(self) -> None:
        # RFC 0020 section 1: a 4.0.0 release under a stage of another format takes that stage's rule, and back
        (line, _), _ = worked_examples()
        value = d.read_document(line.encode("utf-8"), "release")
        for format_version in ("3.0.0", None, "4.2.0"):
            self.assertEqual(encoding.release_bytes(value), encoding.release_digest_bytes(value, format_version))
        value["inputMapping"] = d.read_document(d.canon({"version": 3, "case": {"facts": [], "evidence": []}}), "mapping")
        for format_version in ("4.0.0", "4.1.0"):
            self.assertEqual(d.canon(value), encoding.release_digest_bytes(value, format_version))


class StagedStageVectorTests(unittest.TestCase):
    """conformance/dialect/workflow-format-4/: a stage of each format, with its dialect and release digests."""

    DIRECTORY = ROOT / "conformance" / "dialect" / "workflow-format-4"

    def test_each_stage_is_admitted_by_the_0_6_0_schema_with_the_digests_given(self) -> None:
        from tools import workflow_reader as reader
        manifest = load(self.DIRECTORY / "manifest.json")
        cases = manifest["cases"]
        self.assertEqual(["4.0.0", "4.1.0", "4.0.0", "4.0.0"], [case["formatVersion"] for case in cases])
        self.assertEqual(load(PUBLISHED)["$id"], manifest["schema"])
        self.assertEqual({f for c in cases for f in (c["workflow"], c["release"])} | {"README.md", "manifest.json"},
                         {path.name for path in self.DIRECTORY.iterdir()})
        published = jsonschema.Draft202012Validator(load(PUBLISHED), format_checker=jsonschema.FormatChecker())
        previous = jsonschema.Draft202012Validator(load(PREVIOUS), format_checker=jsonschema.FormatChecker())
        for case in cases:
            with self.subTest(stage=case["name"]):
                workflow, release = load(self.DIRECTORY / case["workflow"]), load(self.DIRECTORY / case["release"])
                dialect = load(ROOT / "conformance" / "dialect" / case["dialect"])
                # the manifest names each schema by its version: 0.6.0's admits the stage, 0.5.0's does not
                self.assertEqual(("valid", "invalid"), (case["expected"]["schema-0.6.0"], case["expected"]["schema-0.5.0"]))
                self.assertEqual([], [error.message for error in published.iter_errors(workflow)])
                self.assertFalse(previous.is_valid(workflow))
                (stage,) = workflow["stages"]
                self.assertEqual({"formatVersion": case["formatVersion"], "id": dialect["id"],
                                  "version": dialect["version"], "digest": case["dialectDigest"]}, stage["dialect"])
                raw_dialect = (ROOT / "conformance" / "dialect" / case["dialect"]).read_bytes()
                self.assertEqual(case["dialectDigest"],
                                 "sha256:" + hashlib.sha256(d.canon(d.read_document(raw_dialect, "dialect"))).hexdigest())
                self.assertEqual(dialect, release["inputMapping"])
                self.assertEqual(stage["pack"]["digest"], release["packDigest"])
                value = d.read_document((self.DIRECTORY / case["release"]).read_bytes(), "release")
                self.assertEqual(case["releaseDigest"],
                                 "sha256:" + hashlib.sha256(encoding.release_digest_bytes(value, case["formatVersion"])).hexdigest())
                self.assertNotEqual(case["releaseDigest"],
                                    "sha256:" + hashlib.sha256(encoding.release_bytes(value)).hexdigest())
                # the workflow reader reads the selector as Core 0.6.0 does (its contract has no `sample`)
                form = {name: member for name, member in stage.items() if name != "sample"}
                reader.Reader.stage_form(object.__new__(reader.Reader), form, 0)
                # selection is present exactly on a consumed stage; the one stage here is terminal
                probe = object.__new__(reader.Reader)
                probe.stage_order = [stage["id"]]
                if case["expected"]["workflowReader"] == "admitted":
                    self.assertNotIn("selection", stage)
                    self.assertEqual({stage["id"]: []}, probe.consumers_form(workflow["stages"]))
                else:
                    self.assertEqual("input-malformed", case["expected"]["workflowReader"])
                    self.assertIn("selection", stage)
                    with self.assertRaises(reader.Problem) as caught:
                        probe.consumers_form(workflow["stages"])
                    self.assertEqual(("refusal", "input-malformed", case["expected"]["rule"]),
                                     (caught.exception.result, caught.exception.code, caught.exception.detail))


if __name__ == "__main__":
    unittest.main()

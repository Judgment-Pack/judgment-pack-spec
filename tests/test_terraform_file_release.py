"""The terraform-file companion's release route (VERSIONING.md, spec/terraform-file.md section 10).

A `terraform-file-vMAJOR.MINOR.PATCH` tag is gated on its own release record, which the builder
derives from the tagged tree, and packaged in its own bundle, as the registry's tags are. These
tests hold the builder to that: the exact tag grammar; the tree as it stands, refused before the
commit a tag names and passing from it on; a candidate tree, with its statuses said `released`
(whichever they say now) and its record written here from the bytes, which passes, and each
mismatch, unlisted file, tag number that is not the table release, status, statement, missing note
and earlier record that shrinks the reading, which refuses; each later table release the next patch
of the latest earlier one, an erratum's with no new row, and every other number refused; the tagged
history; the routing; what
the bundle carries, whose own checks pass in it, and what a Core bundle leaves out; and the
attributes that keep the bytes as committed.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("terraform_file_release", ROOT / "tools/build_release.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
TAG = "terraform-file-v1.0.0"
VERSION = "1.0.0"
TEXT = "spec/terraform-file.md"
README = "conformance/terraform-file/README.md"
VECTORS = "conformance/terraform-file/1.0.0"
MANIFEST = f"{VECTORS}/manifest.json"
CODES = f"{VECTORS}/codes.json"
FORMATS = f"{VECTORS}/formats.json"
# The status each of the four says; one match each, whichever word it is.
STATUS_SENTENCE = re.compile(r"^(This text is the terraform-file reading `1\.0\.0`, status `)([a-z]+)(`\.)", re.M)
HEADER_STATUS = re.compile(r'^(  "status": ")([a-z]+)(",)$', re.M)
# The other statements of the status the tag commit rewrites: the text's lead, the README's status
# and the manifest's label.
LEAD = re.compile(r"`1\.0\.0`(\s+)is(\s+)proposed\b")
README_STATUS = re.compile(r"`1\.0\.0`,(\s+)status(\s+)`proposed`")
LABEL = re.compile(r'^(  "label": )("[^"\n]*")(,)$', re.M)
ZERO = "sha256:" + "0" * 64


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def files(root: Path, directory: str) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): digest(path)
            for path in sorted((root / directory).rglob("*")) if path.is_file()}


def record(root: Path, tag: str = TAG, version: str = VERSION, added: dict | None = None) -> dict:
    """The record of the candidate tree, from its bytes; the builder must derive the same. `added`
    is the rows its table release accepts beyond the latest earlier one: all of them, unless given,
    as for the first release."""
    vectors = json.loads((root / MANIFEST).read_text("utf-8"))
    codes = json.loads((root / CODES).read_text("utf-8"))
    formats = json.loads((root / FORMATS).read_text("utf-8"))
    table = {row["document"]: sorted(row["accepted"]) for row in formats["table"]}
    return {
        "companion": "terraform-file", "releaseVersion": version, "tag": tag, "maturity": "released",
        "reading": "1.0.0",
        "formatTable": {"path": FORMATS, "sha256": digest(root / FORMATS), "release": formats["release"],
                        "table": table, "added": copy.deepcopy(table) if added is None else added},
        "codes": {"path": CODES, "sha256": digest(root / CODES), "codes": [code["code"] for code in codes["codes"]]},
        "corpus": {"path": MANIFEST, "sha256": digest(root / MANIFEST),
                   "vectors": sorted(row["id"] for row in vectors["vectors"]), "files": files(root, VECTORS)},
        "formatDigests": {TEXT: digest(root / TEXT), README: digest(root / README)},
    }


def write_record(root: Path, release: object | None = None, tag: str = TAG) -> Path:
    path = root / "releases" / f"{tag}.json"
    path.write_text(json.dumps(record(root) if release is None else release, indent=2) + "\n")
    return path


def set_status(root: Path, word: str, names: tuple[str, ...] = (TEXT, MANIFEST, CODES, FORMATS)) -> None:
    for name in names:
        path = root / name
        pattern = STATUS_SENTENCE if name == TEXT else HEADER_STATUS
        text, count = pattern.subn(rf"\g<1>{word}\g<3>", path.read_text("utf-8"))
        if count != 1:
            raise AssertionError(f"{path}: {count} status statements")
        path.write_bytes(text.encode("utf-8"))


def rewrite(path: Path, pattern: re.Pattern, replacement) -> None:
    path.write_bytes(pattern.sub(replacement, path.read_text("utf-8")).encode("utf-8"))


def say_released(root: Path) -> None:
    """What the commit a tag names changes that the builder reads: the four statuses, the text's
    lead, the README's status and the manifest's label. A tree that already says so is left as it
    is."""
    set_status(root, "released")
    rewrite(root / TEXT, LEAD, r"`1.0.0`\1is\2released")
    rewrite(root / README, README_STATUS, r"`1.0.0`,\1status\2`released`")
    rewrite(root / MANIFEST, LABEL, lambda match: match.group(1) + json.dumps(
        json.loads(match.group(2)).replace(", proposed:", ", released:")) + match.group(3))


def edit_json(path: Path, change) -> None:
    document = json.loads(path.read_text("utf-8"))
    change(document)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class TerraformFileReleaseTests(unittest.TestCase):
    def copied_tree(self, directory: str) -> Path:
        root = Path(directory)
        for name in BUILDER.TERRAFORM_FILE_BUNDLE_PATHS:
            source, target = ROOT / name, root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copyfile(source, target)
        (root / "releases").mkdir()
        return root

    def released_tree(self, directory: str) -> Path:
        root = self.copied_tree(directory)
        say_released(root)
        (root / "releases" / f"{TAG}.md").write_text("# terraform-file-v1.0.0\n\nSynthetic notes.\n")
        write_record(root)
        return root

    def later_release(self, root: Path, number: str, added: dict, change=None) -> str:
        """Make the tree the candidate of table release `number`, beside the records it has: the
        table says that release, `change` edits it, notes exist, and the record is written from the
        bytes, naming `added` as the rows it accepts beyond the latest earlier release."""
        tag = f"terraform-file-v{number}"

        def edit(document):
            document.update(release=number)
            if change is not None:
                change(document)

        edit_json(root / FORMATS, edit)
        (root / "releases" / f"{tag}.md").write_text("Synthetic notes.\n")
        write_record(root, record(root, tag, number, added), tag)
        return tag

    def test_exact_tag_and_refused_aliases(self):
        self.assertEqual(BUILDER.release_version(TAG), VERSION)
        self.assertTrue(BUILDER.is_terraform_file_tag(TAG))
        self.assertFalse(BUILDER.is_registry_tag(TAG))
        self.assertFalse(BUILDER.is_policy_tag(TAG))
        self.assertFalse(BUILDER.is_patch_release(TAG))
        self.assertFalse(BUILDER.is_patch_release("terraform-file-v1.0.1"))
        self.assertFalse(BUILDER.is_terraform_file_tag("registry-v1.0.0"))
        for tag in ("terraform-file-v1.0.0-rc.1", "terraform-file-v1.0.0-draft.1", "terraform-file-v01.0.0",
                    "terraform-file-v1.0", "terraform-file-v1.0.0+local", "terraform-file-v1.0.0\n",
                    "terraform-file-1.0.0", "Terraform-file-v1.0.0", "terraform-file-v1.0.0.0",
                    "terraform_file-v1.0.0", "terraform-v1.0.0", "xterraform-file-v1.0.0"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                BUILDER.release_version(tag)

    def test_the_tree_as_it_stands_is_refused_before_the_tag_commit_and_passes_from_it(self):
        status = json.loads((ROOT / MANIFEST).read_text("utf-8"))["status"]
        self.assertIn(status, ("proposed", "released"))
        if status == "proposed":
            with self.assertRaisesRegex(ValueError, "release record is missing|say status released"):
                BUILDER.validate_terraform_file_artifacts(VERSION, TAG)
        else:
            # From the commit a tag names on, the tree is the latest terraform-file release's record.
            records = sorted((path.name[:-len(".json")] for path in (ROOT / "releases").glob("terraform-file-v*.json")
                              if not path.name.endswith(".milestone.json")),
                             key=lambda tag: tuple(int(n) for n in BUILDER.release_version(tag).split(".")))
            self.assertTrue(records)
            BUILDER.validate_terraform_file_artifacts(BUILDER.release_version(records[-1]), records[-1])

    def test_a_tree_that_says_proposed_cannot_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_tree(temporary)
            say_released(root)
            set_status(root, "proposed")
            (root / "releases" / f"{TAG}.md").write_text("Synthetic notes.\n")
            write_record(root)
            with self.assertRaisesRegex(ValueError, "say status released"):
                BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)

    def test_the_candidate_passes_and_its_record_must_equal_the_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)
            self.assertEqual(record(root), BUILDER.terraform_file_record(VERSION, TAG, root))
            path = root / "releases" / f"{TAG}.json"
            original = json.loads(path.read_text())
            for key, value, message in (
                    ("tag", "terraform-file-v9.0.0", "identity, maturity or reading"),
                    ("releaseVersion", "1.0.1", "identity, maturity or reading"),
                    ("maturity", "stable", "identity, maturity or reading"),
                    ("reading", "1.0.1", "identity, maturity or reading"),
                    ("companion", "registry", "identity, maturity or reading"),
                    ("extra", True, "closed shape")):
                changed = copy.deepcopy(original)
                changed[key] = value
                write_record(root, changed)
                with self.subTest(key=key), self.assertRaisesRegex(ValueError, message):
                    BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)
            for change, message in (
                    (lambda r: r.pop("formatTable"), "closed shape"),
                    (lambda r: r["formatDigests"].pop(README), "text or README bytes"),
                    (lambda r: r["formatTable"].update(release="1.0.1"), "format table"),
                    (lambda r: r["formatTable"]["table"]["plan"].pop(), "format table"),
                    (lambda r: r["formatTable"].update(added={}), "format table"),
                    (lambda r: r["formatTable"].pop("added"), "format table"),
                    (lambda r: r["corpus"]["vectors"].pop(), "corpus identity"),
                    (lambda r: r["corpus"]["files"].popitem(), "corpus identity"),
                    (lambda r: r["codes"]["codes"].pop(), "code list identity"),
                    (lambda r: r["codes"]["codes"].reverse(), "code list identity")):
                changed = copy.deepcopy(original)
                change(changed)
                write_record(root, changed)
                with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                    BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)
            for malformed in ([], "record"):
                write_record(root, malformed)
                with self.subTest(record=malformed), self.assertRaisesRegex(ValueError, "closed shape"):
                    BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)
            write_record(root, original)
            BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)

    def test_a_changed_or_unlisted_byte_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            for name, message in ((TEXT, "text or README bytes"), (README, "text or README bytes"),
                                  (FORMATS, "format table"), (CODES, "corpus identity"),
                                  (MANIFEST, "corpus identity"),
                                  (f"{VECTORS}/declarations/plan.json", "corpus identity"),
                                  (f"{VECTORS}/vectors/formats/plan-1.0.json", "corpus identity"),
                                  (f"{VECTORS}/vectors/json/white-space-only.json", "corpus identity")):
                path = root / name
                raw = path.read_bytes()
                path.write_bytes(raw + b"\n")
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, message):
                    BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)
                path.write_bytes(raw)
            for orphan in (root / VECTORS / "vectors/unlisted.json", root / VECTORS / "declarations/unlisted.json"):
                orphan.write_text("{}\n")
                with self.subTest(orphan=orphan.name), self.assertRaisesRegex(ValueError, "corpus identity"):
                    BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)
                orphan.unlink()
            BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)

    def test_the_lists_must_be_of_their_form(self):
        # A list the record cannot name is refused before any record is compared.
        for name, change, message in (
                (CODES, lambda d: d["codes"].append(dict(d["codes"][0])), "code list"),
                (CODES, lambda d: d.update(codes=[]), "code list"),
                (FORMATS, lambda d: d["table"].append(dict(d["table"][0])), "format table"),
                (FORMATS, lambda d: d["table"][0]["accepted"].append(d["table"][0]["accepted"][0]), "format table"),
                (FORMATS, lambda d: d.update(release="1.0"), "format table"),
                (FORMATS, lambda d: d.pop("release"), "format table"),
                (MANIFEST, lambda d: d["vectors"].append(dict(d["vectors"][0])), "two share an id"),
                (MANIFEST, lambda d: d.update(vectors=[]), "no vectors")):
            with self.subTest(name=name, message=message), tempfile.TemporaryDirectory() as temporary:
                root = self.released_tree(temporary)
                edit_json(root / name, change)
                with self.assertRaisesRegex(ValueError, message):
                    BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)

    def test_the_tag_number_is_the_table_release_it_carries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            # A later tag whose table did not grow to its number is refused, though its record
            # is the tree's.
            later, number = "terraform-file-v1.0.1", "1.0.1"
            (root / "releases" / f"{later}.md").write_text("Synthetic notes.\n")
            write_record(root, record(root, later, number), later)
            with self.assertRaisesRegex(ValueError, "tag's number must be the release of the format table"):
                BUILDER.validate_terraform_file_artifacts(number, later, root)
            # Once the table says that release, the same tag passes, as an erratum of the first.
            edit_json(root / FORMATS, lambda document: document.update(release=number))
            write_record(root, record(root, later, number, {}), later)
            BUILDER.validate_terraform_file_artifacts(number, later, root)
            # And the first tag no longer does.
            write_record(root, record(root))
            with self.assertRaisesRegex(ValueError, "tag's number must be the release of the format table"):
                BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)

    def test_every_status_must_say_released(self):
        # `stable` is a status no wording check reads, so only the status check refuses it.
        for name, word in ((name, word) for name in (TEXT, MANIFEST, CODES, FORMATS) for word in ("proposed", "stable")):
            with self.subTest(name=name, word=word), tempfile.TemporaryDirectory() as temporary:
                root = self.released_tree(temporary)
                set_status(root, word, (name,))
                write_record(root)
                with self.assertRaisesRegex(ValueError, "say status released"):
                    BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)
        for name, change in ((CODES, lambda d: d.update(companion="registry")),
                             (FORMATS, lambda d: d.update(reading="1.0.1")),
                             (MANIFEST, lambda d: d.pop("status"))):
            with self.subTest(name=name, change="identity"), tempfile.TemporaryDirectory() as temporary:
                root = self.released_tree(temporary)
                edit_json(root / name, change)
                write_record(root)
                with self.assertRaisesRegex(ValueError, "say status released"):
                    BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)

    def test_no_statement_may_still_call_the_reading_proposed(self):
        def append(name, addition):
            return lambda root: (root / name).write_text((root / name).read_text("utf-8") + addition)

        def heading(root):
            lines = (root / README).read_text("utf-8").split("\n", 1)
            (root / README).write_text(lines[0] + " (proposed)\n" + lines[1])

        for label, change in (
                ("the text's lead", append(TEXT, "\nVersion `1.0.0` is\nproposed.\n")),
                ("the text's status", append(TEXT, "\nThe reading `1.0.0`, status `proposed`.\n")),
                ("the README's status", append(README, "\nVectors of the reading `1.0.0`, status\n`proposed`.\n")),
                ("the README's heading", heading),
                ("the label", lambda root: rewrite(root / MANIFEST, LABEL, r'\1"terraform-file vectors, staged"\3')),
                ("a label not a string", lambda root: rewrite(root / MANIFEST, LABEL, r"\g<1>1\g<3>"))):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = self.released_tree(temporary)
                change(root)
                write_record(root)
                with self.assertRaisesRegex(ValueError, "call the reading proposed"):
                    BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)
        # Another proposed thing the text names, such as dialect version 3, is not the reading.
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            append(TEXT, "\nDialect version 3, which is proposed, cites this text.\n")(root)
            write_record(root)
            BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)

    def test_notes_are_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            (root / "releases" / f"{TAG}.md").unlink()
            with self.assertRaisesRegex(ValueError, "notes are missing"):
                BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)

    def test_an_earlier_record_of_the_reading_never_shrinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            first = record(root)
            earlier = root / "releases" / f"{TAG}.json"
            later = self.later_release(root, "1.0.1", {})

            def variant(change):
                previous = copy.deepcopy(first)
                change(previous)
                return previous

            def drop_plan_row(previous):
                previous["formatTable"]["table"]["plan"].remove("1.2")
                previous["formatTable"]["added"]["plan"].remove("1.2")

            def other_bytes(previous):
                previous["formatDigests"] = {TEXT: ZERO, README: ZERO}
                previous["corpus"]["files"] = {f"{VECTORS}/vectors/formats/plan-1.0.json": ZERO}

            # An earlier release that names less, or other bytes, agrees; the later record names
            # the rows it accepts beyond it, none for an erratum.
            for label, previous, added in (
                    ("the same contents", first, {}),
                    ("fewer codes", variant(lambda p: p["codes"]["codes"].pop()), {}),
                    ("fewer rows", variant(drop_plan_row), {"plan": ["1.2"]}),
                    ("fewer vectors", variant(lambda p: p["corpus"]["vectors"].pop()), {}),
                    ("other bytes", variant(other_bytes), {})):
                earlier.write_text(json.dumps(previous))
                write_record(root, record(root, later, "1.0.1", added), later)
                with self.subTest(agrees=label):
                    BUILDER.validate_terraform_file_artifacts("1.0.1", later, root)
            # A record of another reading, and a milestone link, are not records of this one.
            earlier.write_text(json.dumps(first))
            write_record(root, record(root, later, "1.0.1", {}), later)
            (root / "releases/terraform-file-v0.9.0.json").write_text(
                json.dumps(variant(lambda p: p.update(reading="0.9.0", codes={}))))
            (root / "releases/terraform-file-v0.9.0.milestone.json").write_text("[]")
            BUILDER.validate_terraform_file_artifacts("1.0.1", later, root)
            # An earlier release that names a code, a row or a vector the later lacks, one of the
            # same table release, and one not of the record's form conflict. The later record is the
            # builder's own here, so that only the history can refuse it.
            for label, previous in (
                    ("a code dropped", variant(lambda p: p["codes"]["codes"].append("TF-RETIRED"))),
                    ("a row dropped", variant(lambda p: p["formatTable"]["table"]["plan"].append("0.2"))),
                    ("a document dropped", variant(lambda p: p["formatTable"]["table"].update(apply=["1.0"]))),
                    ("a vector dropped", variant(lambda p: p["corpus"]["vectors"].append("retired-vector"))),
                    ("the same table release", variant(lambda p: p["formatTable"].update(release="1.0.1"))),
                    ("a release not of its form", variant(lambda p: p["formatTable"].update(release="1.0"))),
                    ("no reading", variant(lambda p: p.pop("reading"))),
                    ("no vectors", variant(lambda p: p["corpus"].pop("vectors"))),
                    ("a code not a string", variant(lambda p: p["codes"]["codes"].append(7))),
                    ("a list", []), ("a string", "terraform-file")):
                earlier.write_text(json.dumps(previous))
                write_record(root, BUILDER.terraform_file_record("1.0.1", later, root), later)
                with self.subTest(conflicts=label), self.assertRaisesRegex(ValueError, "earlier release record"):
                    BUILDER.validate_terraform_file_artifacts("1.0.1", later, root)
        # A higher release must name everything a lower one does; it may name more.
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            higher = root / "releases/terraform-file-v1.0.1.json"
            grown = record(root, "terraform-file-v1.0.1", "1.0.1", {"state": ["1.1"]})
            grown["formatTable"]["release"] = "1.0.1"
            grown["formatTable"]["table"]["state"].append("1.1")
            grown["codes"]["codes"].append("TF-LATER")
            higher.write_text(json.dumps(grown))
            BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)
            shrunk = record(root, "terraform-file-v1.0.1", "1.0.1", {})
            shrunk["formatTable"]["release"] = "1.0.1"
            shrunk["corpus"]["vectors"].pop()
            higher.write_text(json.dumps(shrunk))
            with self.assertRaisesRegex(ValueError, "earlier release record: table release 1.0.1 lacks"):
                BUILDER.validate_terraform_file_artifacts(VERSION, TAG, root)

    def test_each_later_table_release_is_the_next_patch_and_an_erratum_accepts_no_row(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            table = record(root)["formatTable"]["table"]
            # The first release accepts every row of its table.
            self.assertEqual(table, BUILDER.terraform_file_record(VERSION, TAG, root)["formatTable"]["added"])
            # An erratum takes the next patch and accepts no new row, and its record says so.
            erratum = self.later_release(root, "1.0.1", {})
            self.assertEqual({}, BUILDER.terraform_file_record("1.0.1", erratum, root)["formatTable"]["added"])
            BUILDER.validate_terraform_file_artifacts("1.0.1", erratum, root)
            # A release that accepts a row takes the next patch too, and its record names the row.
            grown = self.later_release(root, "1.0.2", {"state": ["1.1"]},
                                       lambda document: document["table"][1]["accepted"].append("1.1"))
            BUILDER.validate_terraform_file_artifacts("1.0.2", grown, root)
            # A record that misstates the rows its release accepts is not the tree's.
            for added in ({}, table, {"state": ["1.0", "1.1"]}):
                write_record(root, record(root, grown, "1.0.2", added), grown)
                with self.subTest(added=added), self.assertRaisesRegex(ValueError, "format table identity or rows"):
                    BUILDER.validate_terraform_file_artifacts("1.0.2", grown, root)
            write_record(root, record(root, grown, "1.0.2", {"state": ["1.1"]}), grown)
            # Any number but the next patch of the latest earlier release is refused, with rows or
            # with none; the text defines no minor or major release of the table.
            for number in ("1.0.4", "1.1.0", "2.0.0", "1.1.3"):
                with self.subTest(number=number), tempfile.TemporaryDirectory() as copied:
                    candidate = Path(copied) / "tree"
                    shutil.copytree(root, candidate)
                    tag = self.later_release(candidate, number, {})
                    with self.assertRaisesRegex(ValueError, "earlier release record: .*not the next patch"):
                        BUILDER.validate_terraform_file_artifacts(number, tag, candidate)
            # A release whose predecessor's record is gone from the tree skips a patch.
            with tempfile.TemporaryDirectory() as copied:
                candidate = Path(copied) / "tree"
                shutil.copytree(root, candidate)
                (candidate / "releases" / f"{erratum}.json").unlink()
                with self.assertRaisesRegex(ValueError, "earlier release record: table release 1.0.2 is not the next patch"):
                    BUILDER.validate_terraform_file_artifacts("1.0.2", grown, candidate)
            next_patch = self.later_release(root, "1.0.3", {})
            BUILDER.validate_terraform_file_artifacts("1.0.3", next_patch, root)
        # With no earlier record, the reading's first table release is 1.0.0, and no other.
        for number in ("1.0.1", "1.1.0", "0.9.0", "2.0.0"):
            with self.subTest(first=number), tempfile.TemporaryDirectory() as temporary:
                root = self.released_tree(temporary)
                (root / "releases" / f"{TAG}.json").unlink()
                tag = self.later_release(root, number, record(root)["formatTable"]["table"])
                with self.assertRaisesRegex(ValueError, "first table release is 1.0.0"):
                    BUILDER.validate_terraform_file_artifacts(number, tag, root)

    def test_tagged_history_cannot_be_rewritten_through_worktree_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            old = record(root)
            later = self.later_release(root, "1.0.1", {})
            shrunk = copy.deepcopy(old)
            shrunk["codes"]["codes"].append("TF-RETIRED")
            # Only the tags are read, whatever the worktree's records say.
            (root / "releases" / f"{TAG}.json").write_text(json.dumps(shrunk))
            for listed in (f"{TAG}\n{later}", TAG):
                with self.subTest(listed=listed), patch.object(BUILDER, "ROOT", root), \
                        patch.object(BUILDER, "git", side_effect=[listed, json.dumps(shrunk)]):
                    with self.assertRaisesRegex(ValueError, "immutable tagged release history: table release 1.0.1 lacks"):
                        BUILDER.validate_terraform_file_history(later)
            (root / "releases" / f"{TAG}.json").write_text(json.dumps(old))
            with patch.object(BUILDER, "ROOT", root), \
                    patch.object(BUILDER, "git", side_effect=[TAG, json.dumps(old)]):
                BUILDER.validate_terraform_file_history(later)
            # A tag outside the grammar is not read.
            with patch.object(BUILDER, "ROOT", root), \
                    patch.object(BUILDER, "git", side_effect=[f"terraform-file-v0.9\n{TAG}", json.dumps(old)]):
                BUILDER.validate_terraform_file_history(later)
            # With the first tag gone, the later one has no predecessor, and 1.0.1 is not the first.
            with patch.object(BUILDER, "ROOT", root), patch.object(BUILDER, "git", side_effect=[""]), \
                    self.assertRaisesRegex(ValueError, "immutable tagged release history: .*first table release"):
                BUILDER.validate_terraform_file_history(later)
            # A tagged predecessor the worktree's records do not show: the rows the later release
            # accepts beyond it must be the ones its record names.
            fewer = copy.deepcopy(old)
            fewer["formatTable"]["table"]["plan"].remove("1.2")
            with patch.object(BUILDER, "ROOT", root), \
                    patch.object(BUILDER, "git", side_effect=[TAG, json.dumps(fewer)]), \
                    self.assertRaisesRegex(ValueError, "immutable tagged release history: the record's added rows"):
                BUILDER.validate_terraform_file_history(later)
            # And a tagged predecessor two patches below.
            skipped = copy.deepcopy(old)
            skipped["formatTable"]["release"] = "0.9.9"
            with patch.object(BUILDER, "ROOT", root), \
                    patch.object(BUILDER, "git", side_effect=["terraform-file-v0.9.9", json.dumps(skipped)]), \
                    self.assertRaisesRegex(ValueError, "immutable tagged release history: .*not the next patch"):
                BUILDER.validate_terraform_file_history(later)

    def test_terraform_file_validation_routes_to_its_own_gate(self):
        commit = "a" * 40

        def git(*args):
            if args[0] == "rev-parse":
                return commit
            if args[0] in ("tag", "status"):
                return ""
            raise AssertionError(args)

        with patch.object(BUILDER, "git", side_effect=git), \
                patch.object(BUILDER, "validate_terraform_file_artifacts") as companion, \
                patch.object(BUILDER, "validate_terraform_file_history") as history, \
                patch.object(BUILDER, "validate_registry_artifacts") as registry, \
                patch.object(BUILDER, "validate_registry_history") as registry_history, \
                patch.object(BUILDER, "validate_policy_artifacts") as policy, \
                patch.object(BUILDER, "validate_artifacts") as core:
            self.assertEqual(BUILDER.validate(TAG, commit), VERSION)
            companion.assert_called_once_with(VERSION, TAG)
            history.assert_called_once_with(TAG)
            for other in (registry, registry_history, policy, core):
                other.assert_not_called()
        with patch.object(BUILDER, "git", side_effect=git), \
                patch.object(BUILDER, "validate_registry_artifacts"), \
                patch.object(BUILDER, "validate_terraform_file_artifacts") as companion, \
                patch.object(BUILDER, "validate_terraform_file_history") as history:
            BUILDER.validate("registry-v1.0.0", commit)
            companion.assert_not_called()
            history.assert_not_called()
        with patch.object(BUILDER, "git", side_effect=lambda *args: "b" * 40 if "HEAD^{commit}" in args else commit), \
                patch.object(BUILDER, "validate_terraform_file_artifacts"):
            with self.assertRaisesRegex(ValueError, "not checked out"):
                BUILDER.validate(TAG, commit)

    def candidate_tree(self, temporary: str) -> str:
        # Capture the uncommitted candidate in a temporary index and tree, with synthetic notes
        # and record where the tree has none yet; create no commit or tag.
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / "index"))
        subprocess.run(["git", "read-tree", "HEAD"], cwd=ROOT, env=env, check=True)
        subprocess.run(["git", "add", "-A"], cwd=ROOT, env=env, check=True)
        for name, content in ((f"releases/{TAG}.md", "Synthetic notes.\n"), (f"releases/{TAG}.json", "{}\n")):
            if (ROOT / name).exists():
                continue
            blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=ROOT, input=content,
                                  capture_output=True, text=True, check=True).stdout.strip()
            subprocess.run(["git", "update-index", "--add", "--cacheinfo", f"100644,{blob},{name}"],
                           cwd=ROOT, env=env, check=True)
        return subprocess.check_output(["git", "write-tree"], cwd=ROOT, env=env, text=True).strip()

    def test_the_bundle_carries_the_companion_and_its_checks_pass_in_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            tree = self.candidate_tree(temporary)
            output = Path(temporary) / "dist"
            with patch.object(BUILDER, "validate", return_value=VERSION):
                artifacts = BUILDER.build(TAG, tree, output)
            self.assertEqual([path.name for path in artifacts],
                             [f"judgment-pack-terraform-file_{VERSION}_artifacts.tar.gz",
                              f"judgment-pack-terraform-file_{VERSION}_artifacts.zip", "checksums.txt"])
            prefix = f"judgment-pack-terraform-file-{VERSION}/"
            with tarfile.open(artifacts[0]) as archive:
                file_members = {item.name[len(prefix):] for item in archive.getmembers() if item.isfile()}
                unpacked = Path(temporary) / "unpacked"
                archive.extractall(unpacked, filter="data")
            with zipfile.ZipFile(artifacts[1]) as archive:
                self.assertEqual({prefix + name for name in file_members},
                                 {name for name in archive.namelist() if not name.endswith("/")})
            tracked = set(subprocess.check_output(
                ["git", "ls-tree", "-r", "--name-only", tree, VECTORS], cwd=ROOT, text=True).split())
            self.assertGreater(len(tracked), 100)
            self.assertLessEqual(tracked, file_members)
            for name in (TEXT, README, MANIFEST, CODES, FORMATS, "spec/dialect.md", "spec/registry.md",
                         "VERSIONING.md", "LICENSE", "tests/test_terraform_file_vectors.py",
                         f"releases/{TAG}.md", f"releases/{TAG}.json"):
                self.assertIn(name, file_members)
            for name in file_members:
                self.assertFalse(name.startswith(("conformance/evaluation/", "conformance/policy/",
                                                  "conformance/registry/", "conformance/dialect/",
                                                  "schema/", "examples/", "web/", "tools/")), name)
            self.assertEqual({"tests/test_terraform_file_vectors.py"},
                             {name for name in file_members if name.startswith("tests/")})
            packaged = unpacked / prefix
            # The bytes as committed: the whitespace vectors and every pinned file are unchanged.
            for name in tracked:
                with self.subTest(member=name):
                    self.assertEqual((ROOT / name).read_bytes(), (packaged / name).read_bytes())
            # The text and the vectors' README link only to what the bundle carries, or to the web.
            for name in (TEXT, README):
                for link in re.findall(r"\]\(([^)\s]+)\)", (packaged / name).read_text("utf-8")):
                    target = link.split("#", 1)[0]
                    if target and not re.match(r"[a-z]+:", target):
                        with self.subTest(name=name, link=link):
                            self.assertTrue((packaged / name).parent.joinpath(target).resolve().exists())
            # The checks that hold the vectors to the text pass inside the bundle alone. They are
            # found from the bundle's tests directory, not imported as a `tests` package, which an
            # installed distribution of that name would shadow.
            checked = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-v", "-s", "tests", "-p", "test_terraform_file_*.py"],
                cwd=packaged, capture_output=True, text=True, timeout=600)
            self.assertEqual(0, checked.returncode, checked.stderr[-2000:])
            self.assertRegex(checked.stderr, r"Ran [1-9][0-9]* tests")
            self.assertNotIn("skipped", checked.stderr)
            self.assertIn("test_terraform_file_vectors.", checked.stderr)
            checksums = artifacts[2].read_text().splitlines()
            for artifact, line in zip(artifacts[:2], checksums):
                self.assertEqual(line, BUILDER.sha256(artifact) + "  " + artifact.name)

    def test_a_core_bundle_carries_the_text_and_none_of_the_vectors(self):
        with tempfile.TemporaryDirectory() as temporary:
            tree = self.candidate_tree(temporary)
            core_paths = BUILDER.bundle_paths("v0.2.0-draft", tree)
            self.assertFalse(any(path.startswith("conformance/terraform-file") for path in core_paths))
            core_archive = subprocess.check_output(["git", "archive", "--format=tar", tree, *core_paths], cwd=ROOT)
            with tarfile.open(fileobj=io.BytesIO(core_archive)) as archive:
                core = set(archive.getnames())
            self.assertIn(TEXT, core)
            self.assertIn("conformance/evaluation/manifest.json", core)
            self.assertFalse(any(name.startswith(("conformance/terraform-file", "conformance/registry",
                                                  "conformance/policy")) for name in core))
            for tag in ("registry-v1.0.0", "policy-v1.0.0-draft.1"):
                with self.subTest(tag=tag):
                    self.assertFalse(any("terraform-file" in path for path in BUILDER.bundle_paths(tag, tree)
                                         if path != "rfcs/0038-terraform-file-source.md"))

    def test_no_attribute_drops_or_converts_the_bytes(self):
        names = [MANIFEST, CODES, FORMATS, f"{VECTORS}/declarations/plan.json",
                 f"{VECTORS}/vectors/unlisted.txt", README, TEXT]
        whitespace = [f"{VECTORS}/vectors/json/trailing-whitespace.json", f"{VECTORS}/vectors/json/white-space-only.json"]
        try:
            completed = subprocess.run(["git", "check-attr", "export-ignore", "text", "whitespace", "--",
                                        *names, *whitespace],
                                       cwd=ROOT, check=True, capture_output=True, text=True)
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git cannot read attributes here: {error}")
        attributes = {tuple(line.rsplit(": ", 2)[:2]): line.rsplit(": ", 1)[1]
                      for line in completed.stdout.splitlines()}
        for name in (*names, *whitespace):
            with self.subTest(name=name):
                self.assertEqual("unspecified", attributes[(name, "export-ignore")])
                self.assertEqual("unspecified" if name == TEXT else "unset", attributes[(name, "text")])
                self.assertEqual("unset" if name in whitespace else "unspecified", attributes[(name, "whitespace")])


if __name__ == "__main__":
    unittest.main()

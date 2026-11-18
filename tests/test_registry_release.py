"""The registry companion's release route (VERSIONING.md, spec/registry.md section 13).

A `registry-vMAJOR.MINOR.PATCH` tag is gated on its own release record, which the builder derives
from the tagged tree, and packaged in its own bundle, as Policy's tags are. The builder knows two
formats: `1.0.0`, released on `registry-v1.0.0`, and `1.1.0`, which is spec/registry.md together
with spec/registry-1.1.0.md. The current release is `registry-v1.1.0`, held from the worktree;
`registry-v1.0.0` is the historical one, held from its tagged tree, which this builder still admits
and packages as it did. For each, these tests hold the builder to: the tree as it stands, refused
before the commit a tag names and passing from it on; a candidate tree, with its statuses said
`released` (whichever they say now) and its record written here from the bytes, which passes, and
each mismatch, unlisted file, status, schema wording, missing note and earlier record that refuses;
the tagged history; what the bundle carries and that its checks pass in it. Beside those: the exact
tag grammar, the format a tag names, the routing, what a Core bundle leaves out, and the attributes
that keep the bytes as committed.
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
SPEC = importlib.util.spec_from_file_location("registry_release", ROOT / "tools/build_release.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
# The draft wording before the commit a tag names; that commit rewrites it, so either may be found.
SCHEMA_TITLE = re.compile(r'"title": "DRAFT (Registry companion [0-9.]+: [a-z -]+)"')
SCHEMA_STATUS = re.compile(r"Staged and proposed with (spec/[a-z0-9.-]+\.md), which governs where they differ; "
                           r"not released, and served by no bundle and no site\. ")
# The other statements of the status the tag commit rewrites: the texts' statements, the README's
# heading and statements, and the rows' manifest label.
STATUS_STATEMENT = re.compile(r"\b(status|says)(\s+)`proposed`")
README_HEADING = re.compile(r"^(# .*?)\s*\((?:staged, )?proposed\)$", re.M)
HEADER_STATUS = re.compile(r'^(  "status": ")([a-z]+)(",)$', re.M)
LABEL = re.compile(r'^(  "label": )("[^"\n]*")(,)$', re.M)
ZERO = "sha256:" + "0" * 64


class Release:
    """A registry release the tests hold the builder to: its tag, the format the tag names, the
    text whose sentence says the format's status, a document schema to edit, and the checks its
    bundle carries."""

    def __init__(self, tag: str, status_text: str, document_schema: str, checks: tuple[str, ...],
                 readmes: tuple[str, ...], tools: tuple[str, ...], earlier_pins: tuple[str, ...] = ()):
        self.tag = tag
        self.version = BUILDER.release_version(tag)
        self.form = BUILDER.registry_format(self.version)
        self.format = self.form.version
        self.namespace = f"https://judgmentpack.org/schema/registry/{self.format}/"
        self.texts = self.form.texts
        self.status_text = status_text
        self.readme = self.form.readme
        self.schemas = self.form.schema_root
        self.rows = self.form.root
        self.manifest = f"{self.rows}/manifest.json"
        self.codes = f"{self.rows}/codes.json"
        self.document_schema = document_schema
        self.checks = checks
        self.readmes = readmes
        self.tools = tools
        # The files of an earlier format the bundle carries that this release's record pins itself.
        self.earlier_pins = earlier_pins
        self.status_sentence = re.compile(
            rf"^(This text is registry format `{re.escape(self.format)}`, status `)([a-z]+)(`\.)", re.M)
        self.lead = re.compile(rf"`{re.escape(self.format)}`(\s+)is(\s+)proposed\b")

    def next_patch(self) -> str:
        major, minor, patch_number = self.format.split(".")
        return f"{major}.{minor}.{int(patch_number) + 1}"


CURRENT = Release(
    "registry-v1.1.0", "spec/registry-1.1.0.md", "lock",
    ("test_registry_companion", "test_registry_schemas", "test_registry_1_1_0_rows",
     "test_registry_1_1_0_reader"),
    ("conformance/registry/README.md", "conformance/registry/1.1.0/README.md"),
    ("tools/registry_1_1_0_reader.py", "tools/registry_1_1_0_rows.py", "tools/dialect_verify.py",
     "tools/retained_column.py", "tools/_retained_column.py"),
    ("conformance/registry/README.md",))
HISTORICAL = Release(
    "registry-v1.0.0", "spec/registry.md", "registry",
    ("test_registry_companion", "test_registry_schemas"),
    ("conformance/registry/README.md",), ())


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def files(root: Path, directory: str) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): digest(path)
            for path in sorted((root / directory).rglob("*")) if path.is_file()}


def record(release: Release, root: Path) -> dict:
    """The record of the candidate tree, from its bytes; the builder must derive the same."""
    rows = json.loads((root / release.manifest).read_text("utf-8"))
    codes = json.loads((root / release.codes).read_text("utf-8"))
    return {
        "companion": "registry", "releaseVersion": release.version, "tag": release.tag, "maturity": "released",
        "formatVersion": release.format,
        "schemas": {path.name[:-len(".schema.json")]: release.namespace + path.name
                    for path in sorted((root / release.schemas).glob("*.schema.json"))},
        "codes": {"path": release.codes, "sha256": digest(root / release.codes), "codes": len(codes["codes"])},
        "corpus": {"path": release.manifest, "sha256": digest(root / release.manifest),
                   "rows": len(rows["vectors"]), "files": files(root, release.rows)},
        "formatDigests": {**files(root, release.schemas),
                          **{text: digest(root / text) for text in release.texts},
                          release.readme: digest(root / release.readme),
                          **{pin: digest(root / pin) for pin in release.earlier_pins}},
    }


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text("utf-8")
    if text.count(old) != 1:
        raise AssertionError(f"{path}: {old!r} is not there exactly once")
    path.write_bytes(text.replace(old, new).encode("utf-8"))


def write_record(release: Release, root: Path, content: dict | None = None) -> Path:
    path = root / "releases" / f"{release.tag}.json"
    path.write_text(json.dumps(record(release, root) if content is None else content, indent=2) + "\n")
    return path


def set_status(release: Release, root: Path, word: str, names: tuple[str, ...] | None = None) -> None:
    for name in names or (release.status_text, release.manifest, release.codes):
        path = root / name
        pattern = release.status_sentence if name == release.status_text else HEADER_STATUS
        text, count = pattern.subn(rf"\g<1>{word}\g<3>", path.read_text("utf-8"))
        if count != 1:
            raise AssertionError(f"{path}: {count} status statements")
        path.write_bytes(text.encode("utf-8"))


def say_released(release: Release, root: Path) -> None:
    """What the commit a tag names changes: the three statuses, the texts' and the README's other
    statements of the status, the label and each schema's wording. A tree that already says so is
    left as it is."""
    set_status(release, root, "released")
    for name in release.texts:
        rewrite(root / name, release.lead, rf"`{release.format}`\1is\2released")
        rewrite(root / name, STATUS_STATEMENT, r"\1\2`released`")
    rewrite(root / release.readme, README_HEADING, r"\1")
    rewrite(root / release.readme, STATUS_STATEMENT, r"\1\2`released`")
    rewrite(root / release.manifest, LABEL, lambda match: match.group(1) + json.dumps(
        json.loads(match.group(2)).replace(", proposed:", ", released:")
        .replace(", in no corpus until its first release", "").replace(", staged in no corpus", ""))
        + match.group(3))
    for path in sorted((root / release.schemas).glob("*.schema.json")):
        text = path.read_text("utf-8")
        text = SCHEMA_STATUS.sub(r"Released with \1, which governs where they differ. ",
                                 SCHEMA_TITLE.sub(r'"title": "\1"', text), 1)
        path.write_bytes(text.encode("utf-8"))


def rewrite(path: Path, pattern: re.Pattern, replacement) -> None:
    path.write_bytes(pattern.sub(replacement, path.read_text("utf-8")).encode("utf-8"))


def edit_schema(release: Release, root: Path, name: str, change) -> None:
    path = root / release.schemas / f"{name}.schema.json"
    schema = json.loads(path.read_text("utf-8"))
    change(schema)
    path.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def tagged_tree(tag: str) -> str:
    """The tree a registry tag names. Without the tag (a clone without tags) the test is skipped,
    except under CI, which checks out every tag and where a skip would hide the check."""
    try:
        return subprocess.run(["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{tree}}"], cwd=ROOT,
                              check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        if os.environ.get("CI"):
            raise AssertionError(f"the tag {tag} is not in this clone: {error}") from None
        raise unittest.SkipTest(f"the tag {tag} is not in this clone") from None


def worktree_tree(temporary: str, tag: str) -> str:
    """Capture the uncommitted candidate in a temporary index and tree, with synthetic notes and
    record where the tree has none yet; create no commit or tag."""
    env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / "index"))
    subprocess.run(["git", "read-tree", "HEAD"], cwd=ROOT, env=env, check=True)
    subprocess.run(["git", "add", "-A"], cwd=ROOT, env=env, check=True)
    for name, content in ((f"releases/{tag}.md", "Synthetic notes.\n"), (f"releases/{tag}.json", "{}\n")):
        if (ROOT / name).exists():
            continue
        blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=ROOT, input=content,
                              capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(["git", "update-index", "--add", "--cacheinfo", f"100644,{blob},{name}"],
                       cwd=ROOT, env=env, check=True)
    return subprocess.check_output(["git", "write-tree"], cwd=ROOT, env=env, text=True).strip()


def extract(tree: str, paths: tuple[str, ...], target: Path) -> None:
    archive = subprocess.check_output(["git", "archive", "--format=tar", tree, *paths], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as unpacked:
        unpacked.extractall(target, filter="data")


class FormatReleaseTests:
    """The release of one format; the classes below say which, and where its tree comes from."""

    release: Release

    def source_root(self) -> Path:
        raise NotImplementedError

    def candidate_tree(self, temporary: str) -> str:
        raise NotImplementedError

    def copied_tree(self, directory: str) -> Path:
        root = Path(directory)
        source_root = self.source_root()
        for name in self.release.form.bundle_paths:
            source, target = source_root / name, root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copyfile(source, target)
        (root / "releases").mkdir()
        # The records of the other releases, which hold the earlier formats the bundle carries.
        for record_path in sorted((source_root / "releases").glob("registry-v*.json")):
            if record_path.name not in (f"{self.release.tag}.json",) and not record_path.name.endswith(".milestone.json"):
                shutil.copyfile(record_path, root / "releases" / record_path.name)
        return root

    def released_tree(self, directory: str) -> Path:
        root = self.copied_tree(directory)
        say_released(self.release, root)
        (root / "releases" / f"{self.release.tag}.md").write_text(f"# {self.release.tag}\n\nSynthetic notes.\n")
        write_record(self.release, root)
        return root

    def validate(self, root: Path) -> None:
        BUILDER.validate_registry_artifacts(self.release.version, self.release.tag, root)

    def test_the_tree_as_it_stands_is_refused_before_the_tag_commit_and_passes_from_it(self):
        root = self.source_root()
        status = json.loads((root / self.release.manifest).read_text("utf-8"))["status"]
        self.assertIn(status, ("proposed", "released"))
        if status == "proposed":
            with self.assertRaisesRegex(ValueError, "release record is missing|say status released"):
                self.validate(root)
        else:
            # From the commit a tag names on, the tree is its format's latest registry release's record.
            records = sorted((path.name[:-len(".json")] for path in (root / "releases").glob("registry-v*.json")
                              if not path.name.endswith(".milestone.json")
                              and BUILDER.registry_format(BUILDER.release_version(path.name[:-len(".json")]))
                              is self.release.form),
                             key=lambda tag: tuple(int(n) for n in BUILDER.release_version(tag).split(".")))
            self.assertTrue(records)
            BUILDER.validate_registry_artifacts(BUILDER.release_version(records[-1]), records[-1], root)

    def test_a_tree_that_says_proposed_cannot_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_tree(temporary)
            say_released(self.release, root)
            set_status(self.release, root, "proposed")
            (root / "releases" / f"{self.release.tag}.md").write_text("Synthetic notes.\n")
            write_record(self.release, root)
            with self.assertRaisesRegex(ValueError, "say status released"):
                self.validate(root)

    def test_the_candidate_passes_and_its_record_must_equal_the_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            self.validate(root)
            self.assertEqual(record(self.release, root),
                             BUILDER.registry_record(self.release.version, self.release.tag, root))
            path = root / "releases" / f"{self.release.tag}.json"
            original = json.loads(path.read_text())
            other_format = "1.0.0" if self.release.format != "1.0.0" else "1.1.0"
            for key, value, message in (
                    ("tag", "registry-v9.0.0", "identity, maturity or format"),
                    ("releaseVersion", self.release.next_patch(), "identity, maturity or format"),
                    ("maturity", "stable", "identity, maturity or format"),
                    ("formatVersion", self.release.next_patch(), "identity, maturity or format"),
                    ("formatVersion", other_format, "identity, maturity or format"),
                    ("companion", "policy", "identity, maturity or format"),
                    ("extra", True, "closed shape")):
                changed = copy.deepcopy(original)
                changed[key] = value
                write_record(self.release, root, changed)
                with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, message):
                    self.validate(root)
            changes = [
                (lambda r: r["schemas"].pop("common"), "schema identities"),
                (lambda r: r["corpus"].update(rows=r["corpus"]["rows"] + 1), "corpus identity"),
                (lambda r: r["codes"].update(codes=r["codes"]["codes"] - 1), "code list identity")]
            changes += [(lambda r, text=text: r["formatDigests"].pop(text), "format bytes")
                        for text in (*self.release.texts, self.release.readme, *self.release.earlier_pins)]
            for change, message in changes:
                changed = copy.deepcopy(original)
                change(changed)
                write_record(self.release, root, changed)
                with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                    self.validate(root)
            write_record(self.release, root, original)
            self.validate(root)

    def test_a_changed_or_unlisted_byte_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            row_file = next(path.relative_to(root).as_posix()
                            for path in sorted((root / self.release.rows / "vectors").rglob("*")) if path.is_file())
            for name, message in ((f"{self.release.schemas}/common.schema.json", "format bytes"),
                                  *((text, "format bytes") for text in self.release.texts),
                                  (self.release.readme, "format bytes"),
                                  (self.release.codes, "corpus identity"), (row_file, "corpus identity")):
                path = root / name
                raw = path.read_bytes()
                path.write_bytes(raw + b"\n")
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, message):
                    self.validate(root)
                path.write_bytes(raw)
            orphan = root / self.release.rows / "vectors/unlisted.json"
            orphan.write_text("{}\n")
            with self.assertRaisesRegex(ValueError, "corpus identity"):
                self.validate(root)
            orphan.unlink()
            self.validate(root)

    def test_a_schema_must_keep_its_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            name = self.release.document_schema
            replace_once(root / self.release.schemas / f"{name}.schema.json",
                         f'"$id": "{self.release.namespace}{name}.schema.json"',
                         f'"$id": "{self.release.namespace}{name}-2.schema.json"')
            with self.assertRaisesRegex(ValueError, r"\$id differs"):
                self.validate(root)

    def test_every_status_must_say_released(self):
        for name in (self.release.status_text, self.release.manifest, self.release.codes):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = self.released_tree(temporary)
                set_status(self.release, root, "proposed", (name,))
                write_record(self.release, root)
                with self.assertRaisesRegex(ValueError, "say status released"):
                    self.validate(root)

    def test_one_text_says_the_status_once(self):
        # A second status sentence of the format, in either text, is refused even when it agrees.
        for name in self.release.texts:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = self.released_tree(temporary)
                path = root / name
                path.write_text(path.read_text("utf-8")
                                + f"\nThis text is registry format `{self.release.format}`, status `released`.\n")
                write_record(self.release, root)
                with self.assertRaisesRegex(ValueError, "say status released"):
                    self.validate(root)

    def test_no_schema_may_still_call_itself_unreleased(self):
        def nested(schema):
            schema.setdefault("$defs", {})["annotated"] = {"type": "string", "description": "Not released."}

        document = self.release.document_schema
        for label, name, change in (
                ("title", document, lambda schema: schema.update(title="DRAFT " + schema["title"])),
                ("description", document,
                 lambda schema: schema.update(description="Staged. " + schema["description"])),
                ("proposed", "common",
                 lambda schema: schema.update(description=schema["description"] + " Proposed.")),
                ("no title", document, lambda schema: schema.pop("title")),
                ("nested", document, nested),
                ("comment", document, lambda schema: schema.update({"$comment": "Unreleased."})),
                ("nested comment", "common", lambda schema: schema.setdefault("$defs", {}).update(
                    commented={"$comment": "Not yet released."})),
                ("pre-release", document, lambda schema: schema.update(title=schema["title"] + " (pre-release)")),
                ("no corpus", "common",
                 lambda schema: schema.update(description=schema["description"] + " In no corpus."))):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = self.released_tree(temporary)
                edit_schema(self.release, root, name, change)
                write_record(self.release, root)
                with self.assertRaisesRegex(ValueError, "draft and unreleased wording"):
                    self.validate(root)
        # A property named `description` is a name, not an annotation, and a JSON Schema draft's
        # name, or a release that is, are not the draft wording.
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            edit_schema(self.release, root, document, lambda schema: schema.setdefault("$defs", {}).update(
                named={"properties": {"description": {"type": "string"}},
                       "$comment": "A JSON Schema draft 2020-12 (draft-2020-12) schema, released."}))
            write_record(self.release, root)
            self.validate(root)

    def test_no_statement_may_still_call_the_format_proposed(self):
        def append(name, addition):
            return lambda root: (root / name).write_text((root / name).read_text("utf-8") + addition)

        def heading(root):
            lines = (root / self.release.readme).read_text("utf-8").split("\n", 1)
            (root / self.release.readme).write_text(lines[0] + " (proposed)\n" + lines[1])

        version = self.release.format
        changes = [(f"{name}: the lead", append(name, f"\nVersion `{version}` is\nproposed.\n"))
                   for name in self.release.texts]
        changes += [(f"{name}: a status", append(name, "\nIts rows are published at status\n`proposed`.\n"))
                    for name in self.release.texts]
        changes += [
            ("the README's status", append(self.release.readme, f"\nRows of the format `{version}`, status\n`proposed`.\n")),
            ("the README's list status", append(self.release.readme, "\nThe code list says\n`proposed`.\n")),
            ("the README's heading", heading),
            ("the label", lambda root: rewrite(root / self.release.manifest, LABEL, r'\1"Registry rows, staged"\3')),
            ("a label not a string", lambda root: rewrite(root / self.release.manifest, LABEL, r"\g<1>1\g<3>"))]
        for label, change in changes:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = self.released_tree(temporary)
                change(root)
                write_record(self.release, root)
                with self.assertRaisesRegex(ValueError, "call the format proposed"):
                    self.validate(root)

    def test_no_prose_may_still_call_the_format_unreleased(self):
        def append(name, addition):
            return lambda root: (root / name).write_text((root / name).read_text("utf-8") + addition)

        prose = (*self.release.texts, self.release.readme, *self.release.earlier_pins)
        changes = [(f"{name}: a draft", append(name, "\nThis companion is a draft and is not yet released.\n"))
                   for name in prose]
        changes += [(f"{name}: proposed rows", append(name, "\nThese rows are proposed and no claim may cite them.\n"))
                    for name in prose]
        changes += [
            ("no claim may cite them", append(self.release.readme, "\nNo conformance claim may\ncite them.\n")),
            ("the code list", append(self.release.status_text, "\nThe code list is not yet released.\n")),
            ("normative for nothing", append(self.release.status_text,
                                             "\nThis text is normative for nothing until its tag.\n")),
            ("the format, proposed", append(self.release.readme, f"\nRows of format `{self.release.format}`, proposed.\n")),
            ("the rows' directory", append(self.release.readme, f"\nThe rows, `{self.release.rows}/`, proposed.\n"))]
        for label, change in changes:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = self.released_tree(temporary)
                change(root)
                write_record(self.release, root)
                with self.assertRaisesRegex(ValueError, "a draft, proposed or unreleased"):
                    self.validate(root)
        # A rule about text no tag released, a record that proposed a resolution, and design
        # records accepted rather than Drafts are not the format.
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            for name in prose:
                append(name, "\nA text no registry tag released is normative for nothing, and no conformance claim"
                             " may cite it. The records proposed a resolution. The design records are accepted"
                             " rather than Drafts, on the route without its draft-only restriction.\n")(root)
            write_record(self.release, root)
            self.validate(root)

    def test_the_design_records_must_be_accepted(self):
        self.assertTrue(self.release.form.rfcs)
        self.assertLessEqual(set(self.release.form.rfcs), set(self.release.form.bundle_paths))
        for name in self.release.form.rfcs:
            for label, change in (
                    ("draft", lambda path: replace_once(path, "- Status: Accepted\n", "- Status: Draft\n")),
                    ("a second status", lambda path: replace_once(
                        path, "- Status: Accepted\n", "- Status: Accepted\n- Status: Draft\n")),
                    ("no status", lambda path: replace_once(path, "- Status: Accepted\n", ""))):
                with self.subTest(name=name, label=label), tempfile.TemporaryDirectory() as temporary:
                    root = self.released_tree(temporary)
                    change(root / name)
                    with self.assertRaisesRegex(ValueError, "design records to say Status: Accepted"):
                        self.validate(root)

    def test_notes_are_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            (root / "releases" / f"{self.release.tag}.md").unlink()
            with self.assertRaisesRegex(ValueError, "notes are missing"):
                self.validate(root)

    def test_an_earlier_record_of_the_format_must_name_the_same_schemas(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            current = record(self.release, root)
            earlier = root / "releases/registry-v0.9.0.json"
            unrelated = copy.deepcopy(current)
            unrelated["formatVersion"] = "0.9.0"
            unrelated["formatDigests"] = {"schema/registry/0.9.0/registry.schema.json": ZERO}
            # A record of the other format names other schemas, and is no conflict.
            other = copy.deepcopy(current)
            other["formatVersion"] = "1.0.0" if self.release.format != "1.0.0" else "1.1.0"
            other["schemas"] = {"common": f"https://judgmentpack.org/schema/registry/{other['formatVersion']}/common.schema.json"}
            for previous in (current, unrelated, other):
                earlier.write_text(json.dumps(previous))
                self.validate(root)
            (root / "releases/registry-v0.9.0.milestone.json").write_text("[]")
            self.validate(root)
            changed = copy.deepcopy(current)
            changed["formatDigests"][f"{self.release.schemas}/common.schema.json"] = ZERO
            renamed = copy.deepcopy(current)
            renamed["schemas"]["common"] = self.release.namespace + "shared.schema.json"
            for previous in (changed, renamed, [], {"formatVersion": self.release.format}):
                earlier.write_text(json.dumps(previous))
                with self.subTest(previous=str(previous)[:60]), \
                        self.assertRaisesRegex(ValueError, "earlier release record"):
                    self.validate(root)
            # A later release of the format may change the texts and the rows, not the schemas.
            later = copy.deepcopy(current)
            for text in self.release.texts:
                later["formatDigests"][text] = ZERO
            later["corpus"]["files"] = {}
            earlier.write_text(json.dumps(later))
            self.validate(root)

    def test_tagged_history_cannot_be_rewritten_through_worktree_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            old = record(self.release, root)
            old["formatDigests"][f"{self.release.schemas}/{self.release.document_schema}.schema.json"] = ZERO
            with patch.object(BUILDER, "ROOT", root), \
                    patch.object(BUILDER, "git", side_effect=[f"registry-v0.9.0\n{self.release.tag}", json.dumps(old)]):
                with self.assertRaisesRegex(ValueError, "immutable tagged"):
                    BUILDER.validate_registry_history(self.release.tag)
            with patch.object(BUILDER, "ROOT", root), \
                    patch.object(BUILDER, "git", side_effect=["registry-v0.9.0", json.dumps(record(self.release, root))]):
                BUILDER.validate_registry_history(self.release.tag)

    def test_the_bundle_carries_the_companion_and_its_checks_pass_in_it(self):
        release = self.release
        with tempfile.TemporaryDirectory() as temporary:
            tree = self.candidate_tree(temporary)
            output = Path(temporary) / "dist"
            with patch.object(BUILDER, "validate", return_value=release.version):
                artifacts = BUILDER.build(release.tag, tree, output)
            self.assertEqual([path.name for path in artifacts],
                             [f"judgment-pack-registry_{release.version}_artifacts.tar.gz",
                              f"judgment-pack-registry_{release.version}_artifacts.zip", "checksums.txt"])
            prefix = f"judgment-pack-registry-{release.version}/"
            with tarfile.open(artifacts[0]) as archive:
                file_members = {item.name[len(prefix):] for item in archive.getmembers() if item.isfile()}
                unpacked = Path(temporary) / "unpacked"
                archive.extractall(unpacked, filter="data")
            with zipfile.ZipFile(artifacts[1]) as archive:
                self.assertEqual({prefix + name for name in file_members},
                                 {name for name in archive.namelist() if not name.endswith("/")})
            carried = [path for path in release.form.bundle_paths if path.startswith(("schema/", "conformance/"))]
            tracked = set(subprocess.check_output(["git", "ls-tree", "-r", "--name-only", tree, *carried],
                                                  cwd=ROOT, text=True).split())
            self.assertTrue(tracked)
            self.assertLessEqual(tracked, file_members)
            for name in (*release.texts, *release.readmes, release.manifest, release.codes, "spec/dialect.md",
                         "LICENSE", *(f"tests/{check}.py" for check in release.checks),
                         f"releases/{release.tag}.md", f"releases/{release.tag}.json"):
                self.assertIn(name, file_members)
            for name in file_members:
                self.assertFalse(name.startswith(("conformance/evaluation/", "conformance/policy/",
                                                  "schema/policy/", "examples/", "web/")), name)
            self.assertEqual(set(release.tools), {name for name in file_members if name.startswith("tools/")})
            self.assertNotIn("schema/judgment-pack-core.schema.json", file_members)
            packaged = unpacked / prefix
            # The texts and the rows' READMEs link only to what the bundle carries, or to the web.
            for name in (*release.texts, *release.readmes):
                for link in re.findall(r"\]\(([^)\s]+)\)", (packaged / name).read_text("utf-8")):
                    target = link.split("#", 1)[0]
                    if target and not re.match(r"[a-z]+:", target):
                        with self.subTest(name=name, link=link):
                            self.assertTrue((packaged / name).parent.joinpath(target).resolve().exists())
            # The checks that hold the rows to the text pass inside the bundle alone. They are
            # found from the bundle's tests directory, not imported as a `tests` package, which an
            # installed distribution of that name would shadow.
            checked = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-v", "-s", "tests", "-p", "test_registry_*.py"],
                cwd=packaged, capture_output=True, text=True, timeout=900)
            self.assertEqual(0, checked.returncode, checked.stderr[-2000:])
            self.assertRegex(checked.stderr, r"Ran [1-9][0-9]* tests")
            self.assertNotIn("skipped", checked.stderr)
            for module in release.checks:
                self.assertIn(module + ".", checked.stderr)
            checksums = artifacts[2].read_text().splitlines()
            for artifact, line in zip(artifacts[:2], checksums):
                self.assertEqual(line, BUILDER.sha256(artifact) + "  " + artifact.name)


class CurrentRegistryReleaseTests(FormatReleaseTests, unittest.TestCase):
    """registry-v1.1.0, format 1.1.0, from the worktree."""

    release = CURRENT

    def source_root(self) -> Path:
        return ROOT

    def candidate_tree(self, temporary: str) -> str:
        return worktree_tree(temporary, self.release.tag)


    def test_the_earlier_format_it_carries_is_the_bytes_of_its_record(self):
        # Format 1.0.0's schemas, code list and rows are carried as the record of registry-v1.0.0
        # pins them: a changed byte, a status, a file added or missing refuses the tag.
        self.assertEqual([HISTORICAL.form], BUILDER.registry_carried_formats(self.release.form))
        self.assertEqual(list(self.release.earlier_pins), BUILDER.registry_carried_prose(self.release.form))

        def append(name):
            return lambda root: (root / name).write_bytes((root / name).read_bytes() + b" ")

        def remove(name):
            return lambda root: (root / name).unlink()

        def proposed(root):
            set_status(HISTORICAL, root, "proposed", (HISTORICAL.manifest,))

        def first_row(root):
            return next(path for path in sorted((root / HISTORICAL.rows / "vectors").rglob("*")) if path.is_file())

        for label, change, message in (
                ("a byte added to a schema", append(f"{HISTORICAL.schemas}/registry.schema.json"),
                 "registry.schema.json, which the registry bundle carries, differs"),
                ("the rows' manifest says proposed", proposed, "schemas, code list or rows"),
                ("a byte added to the code list", append(HISTORICAL.codes), "schemas, code list or rows"),
                ("a byte added to a row", lambda root: first_row(root).write_bytes(first_row(root).read_bytes() + b" "),
                 "schemas, code list or rows"),
                ("a row file added", lambda root: (root / HISTORICAL.rows / "vectors/unlisted.json").write_text("{}\n"),
                 "schemas, code list or rows"),
                ("a row file missing", lambda root: first_row(root).unlink(), "schemas, code list or rows"),
                ("a schema directory file added", lambda root: (root / HISTORICAL.schemas / "notes.txt").write_text("x\n"),
                 "schemas, code list or rows"),
                ("a schema missing", remove(f"{HISTORICAL.schemas}/emit-request.schema.json"),
                 "schemas, code list or rows"),
                ("no record of the format", remove(f"releases/{HISTORICAL.tag}.json"), "has no release record")):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = self.released_tree(temporary)
                self.validate(root)
                change(root)
                with self.assertRaisesRegex(ValueError, message):
                    self.validate(root)

    def test_an_earlier_file_this_record_does_not_pin_must_be_the_earlier_bytes(self):
        # The rows' README of format 1.0.0 changed after registry-v1.0.0; only this release's own
        # pin of it lets it differ from that record.
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            earlier = json.loads((root / "releases" / f"{HISTORICAL.tag}.json").read_text("utf-8"))
            current = record(self.release, root)
            for pin in self.release.earlier_pins:
                self.assertNotEqual(earlier["formatDigests"][pin], current["formatDigests"][pin])
                BUILDER.validate_registry_carried(self.release.form, current, root)
                unpinned = copy.deepcopy(current)
                unpinned["formatDigests"].pop(pin)
                with self.subTest(pin=pin), self.assertRaisesRegex(ValueError, "does not pin it"):
                    BUILDER.validate_registry_carried(self.release.form, unpinned, root)
                write_record(self.release, root, unpinned)
                with self.subTest(pin=pin), self.assertRaisesRegex(ValueError, "format bytes"):
                    self.validate(root)

    def test_the_record_of_a_carried_format_must_be_the_tagged_one(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            tagged = json.loads((root / "releases" / f"{HISTORICAL.tag}.json").read_text("utf-8"))
            moved = copy.deepcopy(tagged)
            moved["formatDigests"][f"{HISTORICAL.schemas}/registry.schema.json"] = ZERO
            for old, refused in ((tagged, False), (moved, True)):
                with self.subTest(refused=refused), patch.object(BUILDER, "ROOT", root), \
                        patch.object(BUILDER, "git", side_effect=[HISTORICAL.tag, json.dumps(old)]):
                    if refused:
                        with self.assertRaisesRegex(ValueError, "differs from the one its tag names"):
                            BUILDER.validate_registry_history(self.release.tag)
                    else:
                        BUILDER.validate_registry_history(self.release.tag)


class HistoricalRegistryReleaseTests(FormatReleaseTests, unittest.TestCase):
    """registry-v1.0.0, format 1.0.0, from the tree its tag names: this builder still admits it and
    packages it as the builder at that tag did."""

    release = HISTORICAL

    @classmethod
    def setUpClass(cls) -> None:
        cls.tree = tagged_tree(cls.release.tag)
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        extract(cls.tree, (*cls.release.form.bundle_paths, "tools/build_release.py",
                           f"releases/{cls.release.tag}.md", f"releases/{cls.release.tag}.json"),
                Path(cls.directory.name))
        # The tagged tree's own builder sits beside it, not where the copied trees look.
        cls.tagged_builder = Path(cls.directory.name) / "tagged_build_release.py"
        (Path(cls.directory.name) / "tools/build_release.py").rename(cls.tagged_builder)

    def source_root(self) -> Path:
        return Path(self.directory.name)

    def candidate_tree(self, temporary: str) -> str:
        return self.tree

    def test_it_carries_no_earlier_format(self):
        self.assertEqual([], BUILDER.registry_carried_formats(self.release.form))
        self.assertEqual([], BUILDER.registry_carried_prose(self.release.form))

    def test_the_tagged_builder_and_this_one_agree(self):
        # What the builder at the tag derived and packaged, this one derives and packages the same.
        spec = importlib.util.spec_from_file_location("tagged_build_release", self.tagged_builder)
        tagged = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tagged)
        root = self.source_root()
        self.assertEqual(tagged.registry_record(self.release.version, self.release.tag, root),
                         BUILDER.registry_record(self.release.version, self.release.tag, root))
        self.assertEqual(tagged.bundle_paths(self.release.tag, self.tree),
                         BUILDER.bundle_paths(self.release.tag, self.tree))
        self.assertEqual(json.loads((root / "releases" / f"{self.release.tag}.json").read_text("utf-8")),
                         BUILDER.registry_record(self.release.version, self.release.tag, root))


class RegistryRouteTests(unittest.TestCase):
    def test_exact_tag_and_refused_aliases(self):
        for release in (CURRENT, HISTORICAL):
            self.assertEqual(BUILDER.release_version(release.tag), release.version)
            self.assertTrue(BUILDER.is_registry_tag(release.tag))
            self.assertFalse(BUILDER.is_policy_tag(release.tag))
            self.assertFalse(BUILDER.is_patch_release(release.tag))
        for tag in ("registry-v1.0.0-rc.1", "registry-v1.0.0-draft.1", "registry-v01.0.0",
                    "registry-v1.0", "registry-v1.0.0+local", "registry-v1.0.0\n", "registry-1.0.0",
                    "Registry-v1.0.0", "registry-v1.0.0.0", "registry-v1.1.0-rc.1", "registry-v1.01.0"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                BUILDER.release_version(tag)

    def test_a_tag_releases_the_format_its_major_and_minor_numbers_name(self):
        for version, form in (("1.0.0", "1.0.0"), ("1.0.3", "1.0.0"), ("1.1.0", "1.1.0"), ("1.1.2", "1.1.0")):
            with self.subTest(version=version):
                self.assertEqual(form, BUILDER.registry_format(version).version)
        self.assertEqual(("spec/registry.md",), BUILDER.registry_format("1.0.0").texts)
        self.assertEqual(("spec/registry.md", "spec/registry-1.1.0.md"), BUILDER.registry_format("1.1.0").texts)
        for version in ("1.2.0", "2.0.0", "0.9.0", "0.1.0", "1.1.0-rc.1", "1.1", ""):
            with self.subTest(version=version):
                with self.assertRaisesRegex(ValueError, "names no registry format"):
                    BUILDER.registry_format(version)
                with self.assertRaisesRegex(ValueError, "names no registry format"):
                    BUILDER.registry_record(version, f"registry-v{version}", ROOT)
                with self.assertRaisesRegex(ValueError, "names no registry format"):
                    BUILDER.validate_registry_artifacts(version, f"registry-v{version}", ROOT)
        for tag in ("registry-v1.2.0", "registry-v2.0.0"):
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, "names no registry format"):
                BUILDER.bundle_paths(tag, "HEAD")

    def test_registry_validation_routes_to_its_own_gate(self):
        commit = "a" * 40

        def git(*args):
            if args[0] == "rev-parse":
                return commit
            if args[0] in ("tag", "status"):
                return ""
            raise AssertionError(args)

        for release in (CURRENT, HISTORICAL):
            with self.subTest(tag=release.tag), patch.object(BUILDER, "git", side_effect=git), \
                    patch.object(BUILDER, "validate_registry_artifacts") as registry, \
                    patch.object(BUILDER, "validate_registry_history") as history, \
                    patch.object(BUILDER, "validate_policy_artifacts") as policy, \
                    patch.object(BUILDER, "validate_artifacts") as core:
                self.assertEqual(BUILDER.validate(release.tag, commit), release.version)
                registry.assert_called_once_with(release.version, release.tag)
                history.assert_called_once_with(release.tag)
                policy.assert_not_called()
                core.assert_not_called()
        with patch.object(BUILDER, "git", side_effect=lambda *args: "b" * 40 if "HEAD^{commit}" in args else commit), \
                patch.object(BUILDER, "validate_registry_artifacts"):
            with self.assertRaisesRegex(ValueError, "not checked out"):
                BUILDER.validate(CURRENT.tag, commit)

    def test_a_core_bundle_carries_the_texts_and_none_of_the_registry_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            tree = worktree_tree(temporary, CURRENT.tag)
            core_paths = BUILDER.bundle_paths("v0.2.0-draft", tree)
            core_archive = subprocess.check_output(["git", "archive", "--format=tar", tree, *core_paths], cwd=ROOT)
            with tarfile.open(fileobj=io.BytesIO(core_archive)) as archive:
                core = set(archive.getnames())
            for text in CURRENT.texts:
                self.assertIn(text, core)
            self.assertIn("conformance/evaluation/manifest.json", core)
            self.assertFalse(any(name.startswith(("schema/registry", "conformance/registry",
                                                  "schema/policy", "conformance/policy"))
                                 for name in core))

    def test_no_attribute_drops_or_converts_the_bytes(self):
        names = [CURRENT.manifest, CURRENT.codes, f"{CURRENT.schemas}/lock.schema.json",
                 f"{CURRENT.rows}/vectors/unlisted.txt", f"{CURRENT.rows}/README.md",
                 HISTORICAL.manifest, HISTORICAL.codes, f"{HISTORICAL.schemas}/registry.schema.json",
                 f"{HISTORICAL.rows}/vectors/unlisted.txt", *CURRENT.texts]
        try:
            completed = subprocess.run(["git", "check-attr", "export-ignore", "text", "--", *names],
                                       cwd=ROOT, check=True, capture_output=True, text=True)
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git cannot read attributes here: {error}")
        attributes = {tuple(line.rsplit(": ", 2)[:2]): line.rsplit(": ", 1)[1]
                      for line in completed.stdout.splitlines()}
        for name in names:
            with self.subTest(name=name):
                self.assertEqual("unspecified", attributes[(name, "export-ignore")])
                self.assertEqual("unspecified" if name in CURRENT.texts else "unset", attributes[(name, "text")])


if __name__ == "__main__":
    unittest.main()

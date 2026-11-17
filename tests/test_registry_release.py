"""The registry companion's release route (VERSIONING.md, spec/registry.md section 13).

A `registry-vMAJOR.MINOR.PATCH` tag is gated on its own release record, which the builder derives
from the tagged tree, and packaged in its own bundle, as Policy's tags are. These tests hold the
builder to that: the exact tag grammar; the tree as it stands, refused before the commit a tag
names and passing from it on; a candidate tree, with its statuses said `released` (whichever they
say now) and its record written here from the bytes, which passes, and each mismatch, unlisted file, status, schema wording, missing note and
earlier record that refuses; the tagged history; the routing; what the bundle carries and what a
Core bundle leaves out; and the attributes that keep the bytes as committed.
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
TAG = "registry-v1.0.0"
VERSION = "1.0.0"
NAMESPACE = "https://judgmentpack.org/schema/registry/1.0.0/"
TEXT = "spec/registry.md"
README = "conformance/registry/README.md"
SCHEMAS = "schema/registry/1.0.0"
ROWS = "conformance/registry/1.0.0"
MANIFEST = f"{ROWS}/manifest.json"
CODES = f"{ROWS}/codes.json"
# The status each of the three says; one match each, whichever word it is.
STATUS_SENTENCE = re.compile(r"^(This text is registry format `1\.0\.0`, status `)([a-z]+)(`\.)", re.M)
HEADER_STATUS = re.compile(r'^(  "status": ")([a-z]+)(",)$', re.M)
# The draft wording before the commit a tag names; that commit rewrites it, so either may be found.
SCHEMA_TITLE = re.compile(r'"title": "DRAFT (Registry companion 1\.0\.0: [a-z -]+)"')
SCHEMA_STATUS = ("Staged and proposed with spec/registry.md, which governs where they differ; not "
                 "released, and served by no bundle and no site. ")


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def files(root: Path, directory: str) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): digest(path)
            for path in sorted((root / directory).rglob("*")) if path.is_file()}


def record(root: Path) -> dict:
    """The record of the candidate tree, from its bytes; the builder must derive the same."""
    rows = json.loads((root / MANIFEST).read_text("utf-8"))
    codes = json.loads((root / CODES).read_text("utf-8"))
    return {
        "companion": "registry", "releaseVersion": VERSION, "tag": TAG, "maturity": "released",
        "formatVersion": "1.0.0",
        "schemas": {path.name[:-len(".schema.json")]: NAMESPACE + path.name
                    for path in sorted((root / SCHEMAS).glob("*.schema.json"))},
        "codes": {"path": CODES, "sha256": digest(root / CODES), "codes": len(codes["codes"])},
        "corpus": {"path": MANIFEST, "sha256": digest(root / MANIFEST), "rows": len(rows["vectors"]),
                   "files": files(root, ROWS)},
        "formatDigests": {**files(root, SCHEMAS), TEXT: digest(root / TEXT), README: digest(root / README)},
    }


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text("utf-8")
    if text.count(old) != 1:
        raise AssertionError(f"{path}: {old!r} is not there exactly once")
    path.write_bytes(text.replace(old, new).encode("utf-8"))


def write_record(root: Path, release: dict | None = None) -> Path:
    path = root / "releases" / f"{TAG}.json"
    path.write_text(json.dumps(record(root) if release is None else release, indent=2) + "\n")
    return path


def set_status(root: Path, word: str, names: tuple[str, ...] = (TEXT, MANIFEST, CODES)) -> None:
    for name in names:
        path = root / name
        pattern = STATUS_SENTENCE if name == TEXT else HEADER_STATUS
        text, count = pattern.subn(rf"\g<1>{word}\g<3>", path.read_text("utf-8"))
        if count != 1:
            raise AssertionError(f"{path}: {count} status statements")
        path.write_bytes(text.encode("utf-8"))


def say_released(root: Path) -> None:
    """What the commit a tag names changes: the three statuses and each schema's wording. A tree
    that already says so is left as it is."""
    set_status(root, "released")
    for path in sorted((root / SCHEMAS).glob("*.schema.json")):
        text = path.read_text("utf-8")
        text = SCHEMA_TITLE.sub(r'"title": "\1"', text).replace(
            SCHEMA_STATUS, "Released with spec/registry.md, which governs where they differ. ", 1)
        path.write_bytes(text.encode("utf-8"))


def edit_schema(root: Path, name: str, change) -> None:
    path = root / SCHEMAS / f"{name}.schema.json"
    schema = json.loads(path.read_text("utf-8"))
    change(schema)
    path.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class RegistryReleaseTests(unittest.TestCase):
    def copied_tree(self, directory: str) -> Path:
        root = Path(directory)
        for name in BUILDER.REGISTRY_BUNDLE_PATHS:
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
        (root / "releases" / f"{TAG}.md").write_text("# registry-v1.0.0\n\nSynthetic notes.\n")
        write_record(root)
        return root

    def test_exact_tag_and_refused_aliases(self):
        self.assertEqual(BUILDER.release_version(TAG), VERSION)
        self.assertTrue(BUILDER.is_registry_tag(TAG))
        self.assertFalse(BUILDER.is_policy_tag(TAG))
        self.assertFalse(BUILDER.is_patch_release(TAG))
        for tag in ("registry-v1.0.0-rc.1", "registry-v1.0.0-draft.1", "registry-v01.0.0",
                    "registry-v1.0", "registry-v1.0.0+local", "registry-v1.0.0\n", "registry-1.0.0",
                    "Registry-v1.0.0", "registry-v1.0.0.0"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                BUILDER.release_version(tag)

    def test_the_tree_as_it_stands_is_refused_before_the_tag_commit_and_passes_from_it(self):
        status = json.loads((ROOT / MANIFEST).read_text("utf-8"))["status"]
        self.assertIn(status, ("proposed", "released"))
        if status == "proposed":
            with self.assertRaisesRegex(ValueError, "release record is missing|say status released"):
                BUILDER.validate_registry_artifacts(VERSION, TAG)
        else:
            # From the commit a tag names on, the tree is the latest registry release's record.
            records = sorted((path.name[:-len(".json")] for path in (ROOT / "releases").glob("registry-v*.json")
                              if not path.name.endswith(".milestone.json")),
                             key=lambda tag: tuple(int(n) for n in BUILDER.release_version(tag).split(".")))
            self.assertTrue(records)
            BUILDER.validate_registry_artifacts(BUILDER.release_version(records[-1]), records[-1])

    def test_a_tree_that_says_proposed_cannot_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.copied_tree(temporary)
            say_released(root)
            set_status(root, "proposed")
            (root / "releases" / f"{TAG}.md").write_text("Synthetic notes.\n")
            write_record(root)
            with self.assertRaisesRegex(ValueError, "say status released"):
                BUILDER.validate_registry_artifacts(VERSION, TAG, root)

    def test_the_candidate_passes_and_its_record_must_equal_the_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            BUILDER.validate_registry_artifacts(VERSION, TAG, root)
            self.assertEqual(record(root), BUILDER.registry_record(VERSION, TAG, root))
            path = root / "releases" / f"{TAG}.json"
            original = json.loads(path.read_text())
            for key, value, message in (
                    ("tag", "registry-v9.0.0", "identity, maturity or format"),
                    ("releaseVersion", "1.0.1", "identity, maturity or format"),
                    ("maturity", "stable", "identity, maturity or format"),
                    ("formatVersion", "1.0.1", "identity, maturity or format"),
                    ("companion", "policy", "identity, maturity or format"),
                    ("extra", True, "closed shape")):
                changed = copy.deepcopy(original)
                changed[key] = value
                write_record(root, changed)
                with self.subTest(key=key), self.assertRaisesRegex(ValueError, message):
                    BUILDER.validate_registry_artifacts(VERSION, TAG, root)
            for change, message in (
                    (lambda r: r["schemas"].pop("common"), "schema identities"),
                    (lambda r: r["formatDigests"].pop(TEXT), "format bytes"),
                    (lambda r: r["corpus"].update(rows=r["corpus"]["rows"] + 1), "corpus identity"),
                    (lambda r: r["codes"].update(codes=r["codes"]["codes"] - 1), "code list identity")):
                changed = copy.deepcopy(original)
                change(changed)
                write_record(root, changed)
                with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                    BUILDER.validate_registry_artifacts(VERSION, TAG, root)
            write_record(root, original)
            BUILDER.validate_registry_artifacts(VERSION, TAG, root)

    def test_a_changed_or_unlisted_byte_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            for name, message in ((f"{SCHEMAS}/registry.schema.json", "format bytes"),
                                  (TEXT, "format bytes"), (README, "format bytes"),
                                  (CODES, "corpus identity"),
                                  (f"{ROWS}/vectors/emitter-harness/empty-marker/expected/~empty",
                                   "corpus identity")):
                path = root / name
                raw = path.read_bytes()
                path.write_bytes(raw + b"\n")
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, message):
                    BUILDER.validate_registry_artifacts(VERSION, TAG, root)
                path.write_bytes(raw)
            orphan = root / ROWS / "vectors/unlisted.json"
            orphan.write_text("{}\n")
            with self.assertRaisesRegex(ValueError, "corpus identity"):
                BUILDER.validate_registry_artifacts(VERSION, TAG, root)
            orphan.unlink()
            BUILDER.validate_registry_artifacts(VERSION, TAG, root)

    def test_a_schema_must_keep_its_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            replace_once(root / SCHEMAS / "registry.schema.json", f'"$id": "{NAMESPACE}registry.schema.json"',
                         f'"$id": "{NAMESPACE}registry-2.schema.json"')
            with self.assertRaisesRegex(ValueError, r"\$id differs"):
                BUILDER.validate_registry_artifacts(VERSION, TAG, root)

    def test_every_status_must_say_released(self):
        for name in (TEXT, MANIFEST, CODES):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = self.released_tree(temporary)
                set_status(root, "proposed", (name,))
                write_record(root)
                with self.assertRaisesRegex(ValueError, "say status released"):
                    BUILDER.validate_registry_artifacts(VERSION, TAG, root)

    def test_no_schema_may_still_call_itself_unreleased(self):
        def nested(schema):
            schema.setdefault("$defs", {})["annotated"] = {"type": "string", "description": "Not released."}

        for label, name, change in (
                ("title", "registry", lambda schema: schema.update(title="DRAFT " + schema["title"])),
                ("description", "registry",
                 lambda schema: schema.update(description="Staged. " + schema["description"])),
                ("proposed", "common",
                 lambda schema: schema.update(description=schema["description"] + " Proposed.")),
                ("no title", "registry", lambda schema: schema.pop("title")),
                ("nested", "registry", nested)):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = self.released_tree(temporary)
                edit_schema(root, name, change)
                write_record(root)
                with self.assertRaisesRegex(ValueError, "draft and unreleased wording"):
                    BUILDER.validate_registry_artifacts(VERSION, TAG, root)
        # A property named `description` is a name, not an annotation.
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            edit_schema(root, "registry", lambda schema: schema.setdefault("$defs", {}).update(
                named={"properties": {"description": {"type": "string"}}}))
            write_record(root)
            BUILDER.validate_registry_artifacts(VERSION, TAG, root)

    def test_notes_are_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            (root / "releases" / f"{TAG}.md").unlink()
            with self.assertRaisesRegex(ValueError, "notes are missing"):
                BUILDER.validate_registry_artifacts(VERSION, TAG, root)

    def test_an_earlier_record_of_the_format_must_name_the_same_schemas(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            current = record(root)
            earlier = root / "releases/registry-v0.9.0.json"
            unrelated = copy.deepcopy(current)
            unrelated["formatVersion"] = "0.9.0"
            unrelated["formatDigests"] = {"schema/registry/0.9.0/registry.schema.json": "sha256:" + "0" * 64}
            for previous in (current, unrelated):
                earlier.write_text(json.dumps(previous))
                BUILDER.validate_registry_artifacts(VERSION, TAG, root)
            (root / "releases/registry-v0.9.0.milestone.json").write_text("[]")
            BUILDER.validate_registry_artifacts(VERSION, TAG, root)
            changed = copy.deepcopy(current)
            changed["formatDigests"][f"{SCHEMAS}/common.schema.json"] = "sha256:" + "0" * 64
            renamed = copy.deepcopy(current)
            renamed["schemas"]["common"] = NAMESPACE + "shared.schema.json"
            for previous in (changed, renamed, [], {"formatVersion": "1.0.0"}):
                earlier.write_text(json.dumps(previous))
                with self.subTest(previous=str(previous)[:60]), \
                        self.assertRaisesRegex(ValueError, "earlier release record"):
                    BUILDER.validate_registry_artifacts(VERSION, TAG, root)
            # A later release of the format may change the text and the rows, not the schemas.
            later = copy.deepcopy(current)
            later["formatDigests"][TEXT] = "sha256:" + "0" * 64
            later["corpus"]["files"] = {}
            earlier.write_text(json.dumps(later))
            BUILDER.validate_registry_artifacts(VERSION, TAG, root)

    def test_tagged_history_cannot_be_rewritten_through_worktree_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.released_tree(temporary)
            old = record(root)
            old["formatDigests"][f"{SCHEMAS}/registry.schema.json"] = "sha256:" + "0" * 64
            with patch.object(BUILDER, "ROOT", root), \
                    patch.object(BUILDER, "git", side_effect=[f"registry-v0.9.0\n{TAG}", json.dumps(old)]):
                with self.assertRaisesRegex(ValueError, "immutable tagged"):
                    BUILDER.validate_registry_history(TAG)
            with patch.object(BUILDER, "ROOT", root), \
                    patch.object(BUILDER, "git", side_effect=["registry-v0.9.0", json.dumps(record(root))]):
                BUILDER.validate_registry_history(TAG)

    def test_registry_validation_routes_to_its_own_gate(self):
        commit = "a" * 40

        def git(*args):
            if args[0] == "rev-parse":
                return commit
            if args[0] in ("tag", "status"):
                return ""
            raise AssertionError(args)

        with patch.object(BUILDER, "git", side_effect=git), \
                patch.object(BUILDER, "validate_registry_artifacts") as registry, \
                patch.object(BUILDER, "validate_registry_history") as history, \
                patch.object(BUILDER, "validate_policy_artifacts") as policy, \
                patch.object(BUILDER, "validate_artifacts") as core:
            self.assertEqual(BUILDER.validate(TAG, commit), VERSION)
            registry.assert_called_once_with(VERSION, TAG)
            history.assert_called_once_with(TAG)
            policy.assert_not_called()
            core.assert_not_called()
        with patch.object(BUILDER, "git", side_effect=lambda *args: "b" * 40 if "HEAD^{commit}" in args else commit), \
                patch.object(BUILDER, "validate_registry_artifacts"):
            with self.assertRaisesRegex(ValueError, "not checked out"):
                BUILDER.validate(TAG, commit)

    def test_the_bundle_carries_the_companion_and_a_core_bundle_does_not(self):
        # Capture the uncommitted candidate in a temporary index and tree, with synthetic notes
        # and record where the tree has none yet; create no commit or tag.
        with tempfile.TemporaryDirectory() as temporary:
            index = Path(temporary) / "index"
            env = dict(os.environ, GIT_INDEX_FILE=str(index))
            subprocess.run(["git", "read-tree", "HEAD"], cwd=ROOT, env=env, check=True)
            subprocess.run(["git", "add", "-A"], cwd=ROOT, env=env, check=True)
            for name, content in ((f"releases/{TAG}.md", "Synthetic notes.\n"),
                                  (f"releases/{TAG}.json", "{}\n")):
                if (ROOT / name).exists():
                    continue
                blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=ROOT, input=content,
                                      capture_output=True, text=True, check=True).stdout.strip()
                subprocess.run(["git", "update-index", "--add", "--cacheinfo", f"100644,{blob},{name}"],
                               cwd=ROOT, env=env, check=True)
            tree = subprocess.check_output(["git", "write-tree"], cwd=ROOT, env=env, text=True).strip()
            output = Path(temporary) / "dist"
            with patch.object(BUILDER, "validate", return_value=VERSION):
                artifacts = BUILDER.build(TAG, tree, output)
            self.assertEqual([path.name for path in artifacts],
                             [f"judgment-pack-registry_{VERSION}_artifacts.tar.gz",
                              f"judgment-pack-registry_{VERSION}_artifacts.zip", "checksums.txt"])
            prefix = f"judgment-pack-registry-{VERSION}/"
            with tarfile.open(artifacts[0]) as archive:
                file_members = {item.name[len(prefix):] for item in archive.getmembers() if item.isfile()}
                unpacked = Path(temporary) / "unpacked"
                archive.extractall(unpacked, filter="data")
            with zipfile.ZipFile(artifacts[1]) as archive:
                self.assertEqual({prefix + name for name in file_members},
                                 {name for name in archive.namelist() if not name.endswith("/")})
            tracked = set(subprocess.check_output(
                ["git", "ls-tree", "-r", "--name-only", tree, SCHEMAS, ROWS], cwd=ROOT, text=True).split())
            self.assertTrue(tracked)
            self.assertLessEqual(tracked, file_members)
            for name in (TEXT, README, MANIFEST, CODES, "spec/dialect.md", "LICENSE",
                         "tests/test_registry_companion.py", "tests/test_registry_schemas.py",
                         f"releases/{TAG}.md", f"releases/{TAG}.json"):
                self.assertIn(name, file_members)
            for name in file_members:
                self.assertFalse(name.startswith(("conformance/evaluation/", "conformance/policy/",
                                                  "schema/policy/", "examples/", "web/", "tools/")), name)
            self.assertNotIn("schema/judgment-pack-core.schema.json", file_members)
            packaged = unpacked / prefix
            # The text and the rows' README link only to what the bundle carries, or to the web.
            for name in (TEXT, README):
                for link in re.findall(r"\]\(([^)\s]+)\)", (packaged / name).read_text("utf-8")):
                    target = link.split("#", 1)[0]
                    if target and not re.match(r"[a-z]+:", target):
                        with self.subTest(name=name, link=link):
                            self.assertTrue((packaged / name).parent.joinpath(target).resolve().exists())
            # The checks that hold the rows to the text pass inside the bundle alone.
            checked = subprocess.run(
                [sys.executable, "-m", "unittest", "-q", "tests.test_registry_companion",
                 "tests.test_registry_schemas"],
                cwd=packaged, capture_output=True, text=True, timeout=600)
            self.assertEqual(0, checked.returncode, checked.stderr[-2000:])
            self.assertRegex(checked.stderr, r"Ran [1-9][0-9]* tests")
            self.assertNotIn("skipped", checked.stderr)
            checksums = artifacts[2].read_text().splitlines()
            for artifact, line in zip(artifacts[:2], checksums):
                self.assertEqual(line, BUILDER.sha256(artifact) + "  " + artifact.name)
            core_paths = BUILDER.bundle_paths("v0.2.0-draft", tree)
            core_archive = subprocess.check_output(["git", "archive", "--format=tar", tree, *core_paths], cwd=ROOT)
            with tarfile.open(fileobj=io.BytesIO(core_archive)) as archive:
                core = set(archive.getnames())
            self.assertIn(TEXT, core)
            self.assertIn("conformance/evaluation/manifest.json", core)
            self.assertFalse(any(name.startswith(("schema/registry", "conformance/registry",
                                                  "schema/policy", "conformance/policy"))
                                 for name in core))

    def test_no_attribute_drops_or_converts_the_bytes(self):
        names = [MANIFEST, CODES, f"{SCHEMAS}/registry.schema.json", f"{ROWS}/vectors/unlisted.txt", TEXT]
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
                self.assertEqual("unspecified" if name == TEXT else "unset", attributes[(name, "text")])


if __name__ == "__main__":
    unittest.main()

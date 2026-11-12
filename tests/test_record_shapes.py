"""The record-shape catalog, its change records and the format-status records (catalog/README.md).

Each test that edits a tree works in a temporary copy of the parts the tool reads: every schema
file, releases/ and catalog/.
"""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile
import unittest

from tools import record_shapes as shapes

ROOT = Path(__file__).resolve().parents[1]


def copy_tree(target: Path) -> None:
    for path in shapes.find_schema_files(ROOT):
        (target / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target / path)
    for directory in (shapes.RELEASES, "catalog"):
        shutil.copytree(ROOT / directory, target / directory)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", "utf-8")


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        copy_tree(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def regenerate(self) -> dict:
        catalog = shapes.build_catalog(self.root)
        (self.root / shapes.CATALOG).write_text(shapes.render(catalog), "utf-8")
        return catalog

    def entry(self, catalog: dict, path: str) -> dict:
        [entry] = [entry for entry in catalog["schemas"] if entry["path"] == path]
        return entry

    def edit_schema(self, path: str, change) -> None:
        value = json.loads((self.root / path).read_text("utf-8"))
        change(value)
        write_json(self.root / path, value)


class RepositoryState(unittest.TestCase):
    def test_the_committed_catalog_change_records_and_status_agree_with_the_tree(self):
        self.assertEqual([], shapes.check(ROOT))

    def test_every_schema_under_the_namespace_is_catalogued_and_nothing_else_is_dropped(self):
        catalog = shapes.build_catalog(ROOT)
        found = set(shapes.find_schema_files(ROOT))
        catalogued = {entry["path"] for entry in catalog["schemas"]}
        excluded = {entry["path"] for entry in catalog["outOfScope"]}
        self.assertEqual(found, catalogued | excluded)
        self.assertFalse(catalogued & excluded)
        self.assertEqual(catalogued, {path for paths in catalog["families"].values() for path in paths})
        for entry in catalog["outOfScope"]:
            self.assertFalse(str(entry["id"]).startswith(shapes.NAMESPACE), entry["path"])
            self.assertNotIn(entry["path"].split("/", 1)[0], shapes.SPEC_DIRECTORIES)

    def test_the_check_runs_on_every_pull_request(self):
        manifest = json.loads((ROOT / "dev.json").read_text("utf-8"))
        [step] = [step for step in manifest["checks"] if step["name"] == "record-shapes"]
        self.assertEqual(step["run"], "python3 -B tools/record_shapes.py check")
        # A changed path that no rule maps runs the whole list; every rule names the check.
        mapping = json.loads((ROOT / "jpdev.json").read_text("utf-8"))
        for rule in mapping["changed"]:
            self.assertIn("record-shapes", rule["checks"], rule["paths"])


class Normalization(unittest.TestCase):
    def test_a_vector_normalizes_exactly(self):
        source = (b'{\n  "b": [1, -0, true, null],\n  "a": "\\u00e9\\n\\u001f/\\"",\n'
                  b'  "\\ue000": 0, "\\ud83d\\ude00": {"y": 2, "x": 1}\n}\n')
        normalized = shapes.normalize(shapes.parse(source))
        # Members by UTF-16 code units: U+1F600 (D83D DE00) sorts before U+E000.
        expected = '{"a":"é\\n\\u001f/\\"","b":[1,0,true,null],"\U0001f600":{"x":1,"y":2},"":0}'
        self.assertEqual(normalized, expected)
        self.assertEqual(shapes.digest(normalized),
                         "sha256:" + hashlib.sha256(expected.encode("utf-8")).hexdigest())

    def test_layout_and_member_order_do_not_change_the_digest(self):
        path = ROOT / "schema" / "workflow-1.schema.json"
        value = json.loads(path.read_text("utf-8"))

        def reverse(item):
            if isinstance(item, dict):
                return {name: reverse(item[name]) for name in reversed(list(item))}
            if isinstance(item, list):
                return [reverse(element) for element in item]
            return item

        relaid = json.dumps(reverse(value), indent=7, ensure_ascii=True).encode("utf-8")
        self.assertNotEqual(relaid, path.read_bytes())
        self.assertEqual(shapes.normalize(shapes.parse(relaid)),
                         shapes.normalize(shapes.parse(path.read_bytes())))

    def test_inputs_outside_the_normalization_are_refused(self):
        for source, reason in ((b'{"a": 1, "a": 2}', "repeats"), (b'{"a": 1.5}', "non-integer"),
                               (b'{"a": 1e2}', "non-integer"), (b'{"a": NaN}', "non-JSON"),
                               (b'{"a": 9007199254740992}', "outside"),
                               (b'\xef\xbb\xbf{}', "byte order mark"), (b'{} {}', "one JSON value"),
                               (b'{"a": "\xff"}', "UTF-8"), (b'{"a": "\\ud800"}', "unpaired")):
            with self.subTest(source=source), self.assertRaisesRegex(shapes.ShapeError, reason):
                shapes.normalize(shapes.parse(source))


class Determinism(Fixture):
    def test_the_generator_writes_the_same_bytes_from_the_same_shapes(self):
        first = shapes.render(shapes.build_catalog(self.root))
        self.assertEqual(first, shapes.render(shapes.build_catalog(self.root)))
        self.assertEqual(first, (ROOT / shapes.CATALOG).read_text("utf-8"))
        # Re-lay every schema out: new whitespace and reversed member order give the same catalog.
        for path in shapes.find_schema_files(self.root):
            value = json.loads((self.root / path).read_text("utf-8"))
            if isinstance(value, dict):
                value = {name: value[name] for name in reversed(list(value))}
            (self.root / path).write_text(json.dumps(value, indent=3), "utf-8")
        self.assertEqual(first, shapes.render(shapes.build_catalog(self.root)))


class UnseenCharacters(unittest.TestCase):
    def test_the_catalog_file_writes_an_unseen_character_as_its_escape(self):
        # Written by hand: a C1 control, a line separator, a right-to-left override, a zero-width
        # space, a byte order mark and DELETE are escaped; a section sign and a character outside
        # the Basic Multilingual Plane are left as they are.
        value = {"text": "a\u009fb\u2028c\u202ed\u200be\ufefff\u007fg\u00a7h\U0001f600"}
        self.assertEqual(
            shapes.render(value),
            '{\n  "text": "a\\u009fb\\u2028c\\u202ed\\u200be\\ufefff\\u007fg\u00a7h\U0001f600"\n}\n',
        )
        self.assertEqual(json.loads(shapes.render(value)), value)

    def test_the_catalog_file_escapes_what_displays_as_nothing_or_as_a_space(self):
        # Written by hand: a combining grapheme joiner, a Hangul filler, a variation selector, one
        # from the supplement, a no-break space, an ideographic space, two unassigned code points (one
        # of them default-ignorable) and a private-use one are escaped, the supplementary ones as surrogate pairs; a precomposed
        # letter, a combining acute accent and U+0020 are left as they are.
        value = {"text": "a\u034fb\u3164c\ufe0fd\U000e0100e\u00a0f\u3000g\ufff0h\u0378h\ue000i\u00e9j\u0301 k"}
        self.assertEqual(
            shapes.render(value),
            '{\n  "text": "a\\u034fb\\u3164c\\ufe0fd\\udb40\\udd00e\\u00a0f\\u3000g\\ufff0h\\u0378h\\ue000i\u00e9j\u0301 k"\n}\n',
        )
        self.assertEqual(json.loads(shapes.render(value)), value)

    def test_the_committed_catalog_carries_no_unseen_character(self):
        import unicodedata
        text = (ROOT / shapes.CATALOG).read_text("utf-8")
        # Default_Ignorable_Code_Point, written out here by hand rather than taken from the tool.
        ignorable = ((0x00AD, 0x00AD), (0x034F, 0x034F), (0x061C, 0x061C), (0x115F, 0x1160),
                     (0x17B4, 0x17B5), (0x180B, 0x180F), (0x200B, 0x200F), (0x202A, 0x202E),
                     (0x2060, 0x206F), (0x3164, 0x3164), (0xFE00, 0xFE0F), (0xFEFF, 0xFEFF),
                     (0xFFA0, 0xFFA0), (0xFFF0, 0xFFF8), (0x1BCA0, 0x1BCA3), (0x1D173, 0x1D17A),
                     (0xE0000, 0xE0FFF))
        found = sorted({"U+%04X" % ord(ch) for ch in text
                        if ch != "\n" and (ord(ch) > 0x7E or ch < " ") and (
                            unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp", "Zs", "Cn", "Co", "Cs")
                            or any(low <= ord(ch) <= high for low, high in ignorable))})
        self.assertEqual(found, [])


class ChangeRecords(Fixture):
    PATH = "schema/workflow-1.schema.json"

    def change_shape(self) -> tuple[str, str]:
        before = self.entry(shapes.build_catalog(self.root), self.PATH)["sha256"]
        self.edit_schema(self.PATH, lambda value: value.update(title=value["title"] + " (changed)"))
        after = self.entry(self.regenerate(), self.PATH)["sha256"]
        self.assertNotEqual(before, after)
        return before, after

    def record(self, name: str, changes: list[dict]) -> None:
        write_json(self.root / shapes.CHANGES / name, {"reason": "test", "changes": changes})

    def next_record(self, slug: str) -> str:
        """The name the next change record takes, after those the tree already holds."""
        numbers = [int(shapes.RECORD_FILE.match(path.name).group(1))
                   for path in (self.root / shapes.CHANGES).iterdir()]
        return "%04d-%s.json" % (max(numbers) + 1, slug)

    def test_a_changed_schema_without_a_change_record_fails(self):
        before, after = self.change_shape()
        faults = shapes.check(self.root)
        self.assertEqual(1, len(faults), faults)
        self.assertIn(self.PATH, faults[0])
        self.assertIn("change records end at %s" % before, faults[0])
        self.assertIn(after, faults[0])

    def test_a_changed_schema_with_its_change_record_passes(self):
        before, after = self.change_shape()
        expected = self.next_record("retitle-workflow")
        written = shapes.write_record(self.root, "retitle-workflow", "Retitle for a test")
        self.assertEqual(written.name, expected)
        self.assertEqual(json.loads(written.read_text("utf-8")),
                         {"reason": "Retitle for a test", "changes": [
                             {"path": self.PATH, "family": "workflow", "from": before, "to": after}]})
        self.assertEqual([], shapes.check(self.root))

    def test_the_next_change_record_follows_the_highest_number_across_a_gap(self):
        # Renumber the last record three past its number, so the numbers have a gap below it.
        last = sorted((self.root / shapes.CHANGES).iterdir())[-1]
        gap = int(shapes.RECORD_FILE.match(last.name).group(1)) + 3
        last.rename(last.with_name("%04d-x.json" % gap))
        self.assertEqual([], shapes.check(self.root))
        self.change_shape()
        written = shapes.write_record(self.root, "retitle-workflow", "Retitle for a test")
        self.assertEqual("%04d-retitle-workflow.json" % (gap + 1), written.name)
        self.assertEqual([], shapes.check(self.root))

    def test_a_stale_catalog_fails(self):
        self.edit_schema(self.PATH, lambda value: value.update(title="changed"))
        faults = shapes.check(self.root)
        self.assertTrue(any("is not the catalog the tree gives" in fault for fault in faults), faults)

    def test_a_change_record_naming_a_wrong_old_digest_fails(self):
        before, after = self.change_shape()
        wrong = self.entry(shapes.build_catalog(self.root), "schema/judgment-pack-core.schema.json")["sha256"]
        self.record(self.next_record("wrong-old"),
                    [{"path": self.PATH, "family": "workflow", "from": wrong, "to": after}])
        faults = shapes.check(self.root)
        self.assertTrue(any("from %s, but the earlier records end at %s" % (wrong, before) in fault
                            for fault in faults), faults)

    def test_a_change_record_naming_a_wrong_new_digest_fails(self):
        before, after = self.change_shape()
        wrong = "sha256:" + "0" * 64
        self.record(self.next_record("wrong-new"),
                    [{"path": self.PATH, "family": "workflow", "from": before, "to": wrong}])
        faults = shapes.check(self.root)
        self.assertTrue(any(self.PATH in fault and "change records end at %s" % wrong in fault
                            for fault in faults), faults)

    def test_a_change_record_adding_a_path_already_held_fails(self):
        before, after = self.change_shape()
        self.record(self.next_record("added-again"),
                    [{"path": self.PATH, "family": "workflow", "from": None, "to": after}])
        faults = shapes.check(self.root)
        self.assertTrue(any("adds %s, which the earlier records already hold at %s" % (self.PATH, before) in fault
                            for fault in faults), faults)

    def test_an_addition_or_a_removal_needs_a_change_record(self):
        (self.root / self.PATH).unlink()
        self.regenerate()
        faults = shapes.check(self.root)
        self.assertTrue(any("%s (family workflow) was removed without a change record" % self.PATH in fault
                            for fault in faults), faults)

    def test_change_records_must_be_numbered_once_and_closed(self):
        self.record("0000-again.json", [{"path": "x", "family": "x", "from": None, "to": "sha256:" + "1" * 64}])
        with self.assertRaisesRegex(shapes.ShapeError, "share the number 0000"):
            shapes.check(self.root)
        (self.root / shapes.CHANGES / "0000-again.json").unlink()
        write_json(self.root / shapes.CHANGES / self.next_record("open"), {"reason": "x", "changes": [], "extra": 1})
        with self.assertRaisesRegex(shapes.ShapeError, "exactly the members reason and changes"):
            shapes.check(self.root)


class Inventory(Fixture):
    def test_a_new_schema_file_appears_in_the_inventory_without_hand_edits(self):
        # A version above every catalogued workflow shape, so the family's draft version moves.
        write_json(self.root / "schema" / "workflow-2.schema.json",
                   {"$id": shapes.NAMESPACE + "0.6.0/workflow-2.schema.json", "type": "object"})
        write_json(self.root / "schema" / "example" / "1" / "record.schema.json",
                   {"$id": shapes.NAMESPACE + "example/1/record.schema.json", "type": "object"})
        catalog = shapes.build_catalog(self.root)
        self.assertIn("schema/workflow-2.schema.json", catalog["families"]["workflow"])
        self.assertEqual(["schema/example/1/record.schema.json"], catalog["families"]["example"])
        self.assertEqual("0.6.0", self.entry(catalog, "schema/workflow-2.schema.json")["version"])
        # Found is not accepted: the new shapes still need their change records and status.
        self.regenerate()
        faults = "\n".join(shapes.check(self.root))
        self.assertIn("schema/workflow-2.schema.json (family workflow) at sha256:", faults)
        self.assertIn("no record for the family example", faults)
        self.assertIn('"draftVersion": "0.6.0"', [line for line in faults.splitlines() if "workflow is" in line][0])

    def test_a_schema_in_a_specification_directory_outside_the_namespace_is_refused(self):
        write_json(self.root / "conformance" / "new" / "thing.schema.json",
                   {"$id": "https://example.org/thing.schema.json"})
        with self.assertRaisesRegex(shapes.ShapeError, "conformance/new/thing.schema.json is in conformance/"):
            shapes.build_catalog(self.root)

    def test_a_non_schema_file_in_the_schema_directory_is_refused(self):
        write_json(self.root / "schema" / "loose.json", {"$id": shapes.NAMESPACE + "0.4.0/loose.schema.json"})
        with self.assertRaisesRegex(shapes.ShapeError, "schema/loose.json is in schema/"):
            shapes.build_catalog(self.root)

    def test_one_identifier_with_two_shapes_is_refused(self):
        write_json(self.root / "schema" / "copy.schema.json",
                   {"$id": shapes.NAMESPACE + "0.3.0/workflow-1.schema.json"})
        with self.assertRaisesRegex(shapes.ShapeError, "names two different shapes"):
            shapes.build_catalog(self.root)


class FormatStatus(Fixture):
    def status(self) -> dict:
        return json.loads((self.root / shapes.STATUS).read_text("utf-8"))

    def test_the_status_records_are_those_releases_give(self):
        derived = shapes.derive_status(ROOT, shapes.build_catalog(ROOT))
        self.assertEqual(derived, json.loads((ROOT / shapes.STATUS).read_text("utf-8"))["families"])
        # Hand-checked against releases/: the four families Core 0.5.0 moved in place draft 0.5.0,
        # and releases/v0.5.0.md, with no mapping (its tag is its specVersion), makes v0.5.0 their
        # last release and their baseline. v0.4.0, which carries 0.3.0 unchanged, is neither now.
        # The Policy companion's only release is policy-v1.0.0-draft.1; the leaf shipped in rc.2 and
        # the final; the contributors shape under 0.4.0 is staged and unreleased.
        for family in ("judgment-pack-core", "conformance/manifest", "conformance/evaluation/manifest",
                       "workflow"):
            self.assertEqual(derived[family],
                             {"draftVersion": "0.5.0", "baseline": "v0.5.0", "lastReleased": "v0.5.0"})
        self.assertEqual(derived["policy"], {"draftVersion": "1.0.0", "baseline": "policy-v1.0.0-draft.1",
                                             "lastReleased": "policy-v1.0.0-draft.1"})
        self.assertEqual(derived["retained-column"],
                         {"draftVersion": "1", "baseline": "v0.3.0", "lastReleased": "v0.3.0"})
        self.assertEqual(derived["workflow-contributors"],
                         {"draftVersion": "0.4.0", "baseline": None, "lastReleased": None})

    def test_the_readme_example_is_cores_record(self):
        # catalog/README.md shows Core's record as its format-status example. Staging 0.4.0-draft
        # moved Core's draftVersion and left the example behind once (#301), so it is held here.
        lines = [line.strip() for line in (ROOT / "catalog/README.md").read_text("utf-8").splitlines()
                 if line.strip().startswith('"judgment-pack-core": {')]
        self.assertEqual(len(lines), 1)
        example = json.loads("{" + lines[0] + "}")["judgment-pack-core"]
        status = json.loads((ROOT / shapes.STATUS).read_text("utf-8"))["families"]
        self.assertEqual(example, status["judgment-pack-core"])

    def test_a_status_record_that_differs_from_releases_fails(self):
        status = self.status()
        status["families"]["judgment-pack-core"]["lastReleased"] = "v0.3.0-rc.2"
        write_json(self.root / shapes.STATUS, status)
        faults = shapes.check(self.root)
        self.assertEqual(1, len(faults), faults)
        self.assertIn("family judgment-pack-core", faults[0])
        self.assertIn('"lastReleased": "v0.5.0"', faults[0].split("give", 1)[1])

    def test_a_candidate_is_released_but_is_not_a_baseline(self):
        (self.root / "releases" / "v0.4.0-rc.1.md").write_text("# v0.4.0-rc.1\n", "utf-8")
        write_json(self.root / "releases" / "v0.4.0-rc.1.json",
                   {"releaseVersion": "0.4.0-rc.1", "tag": "v0.4.0-rc.1", "specVersion": "0.4.0"})
        derived = shapes.derive_status(self.root, shapes.build_catalog(self.root))
        self.assertEqual(derived["workflow-contributors"],
                         {"draftVersion": "0.4.0", "baseline": None, "lastReleased": "v0.4.0-rc.1"})
        self.assertEqual(derived["workflow"]["lastReleased"], "v0.5.0")
        faults = shapes.check(self.root)
        self.assertEqual(1, len(faults), faults)
        self.assertIn("family workflow-contributors", faults[0])
        # Without the mapping that carries specVersion 0.3.0, the tag would read as specVersion 0.4.0.
        (self.root / "releases" / "v0.4.0.json").unlink()
        derived = shapes.derive_status(self.root, shapes.build_catalog(self.root))
        self.assertEqual(derived["workflow-contributors"],
                         {"draftVersion": "0.4.0", "baseline": "v0.4.0", "lastReleased": "v0.4.0"})

    def test_the_carrying_release_is_last_released_but_publishes_and_baselines_nothing(self):
        catalog = shapes.build_catalog(self.root)
        derived = shapes.derive_status(self.root, catalog)
        self.assertEqual(derived["workflow-contributors"],
                         {"draftVersion": "0.4.0", "baseline": None, "lastReleased": None})
        four = {"judgment-pack-core", "conformance/manifest", "conformance/evaluation/manifest", "workflow"}
        # v0.4.0 includes the four families its mapping's specVersion 0.3.0 names, and is never a
        # baseline; v0.5.0, whose tag is its specVersion, is now their last release and baseline.
        releases = shapes.load_releases(self.root, catalog)
        self.assertEqual(four, releases["v0.4.0"]["families"])
        self.assertTrue(releases["v0.4.0"]["candidate"])
        self.assertEqual(four, releases["v0.5.0"]["families"])
        self.assertFalse(releases["v0.5.0"]["candidate"])
        self.assertEqual(derived["judgment-pack-core"]["baseline"], "v0.5.0")
        self.assertEqual([], shapes.check(self.root))
        # Without v0.5.0's notes the tree reads as it did at v0.4.0: that tag is the four families'
        # last release and v0.3.0 stays their baseline.
        notes = self.root / "releases" / "v0.5.0.md"
        kept = notes.read_bytes()
        notes.unlink()
        derived = shapes.derive_status(self.root, shapes.build_catalog(self.root))
        self.assertEqual(derived["judgment-pack-core"]["baseline"], "v0.3.0")
        self.assertEqual({family for family, record in derived.items()
                          if record["lastReleased"] == "v0.4.0"}, four)
        notes.write_bytes(kept)
        # The mapping is what keeps the staged shape unpublished: losing it, or moving its
        # specVersion, is a fault in the status records and not a new baseline accepted silently.
        mapping = self.root / "releases" / "v0.4.0.json"
        identity = json.loads(mapping.read_text("utf-8"))
        write_json(mapping, {**identity, "specVersion": "0.4.0"})
        self.assertTrue(any("family workflow-contributors" in fault for fault in shapes.check(self.root)))
        mapping.unlink()
        self.assertTrue(any("family workflow-contributors" in fault for fault in shapes.check(self.root)))

    def test_a_release_naming_a_schema_the_catalog_lacks_is_refused(self):
        write_json(self.root / "releases" / "v0.3.0.extra.json",
                   {"distribution": "v0.3.0", "schema": "schema/missing.schema.json"})
        with self.assertRaisesRegex(shapes.ShapeError, "names the schema schema/missing.schema.json"):
            shapes.check(self.root)

    def test_a_status_record_for_a_family_the_catalog_lacks_fails(self):
        status = self.status()
        status["families"]["no-such-family"] = {"draftVersion": "1", "baseline": None, "lastReleased": None}
        write_json(self.root / shapes.STATUS, status)
        faults = shapes.check(self.root)
        self.assertEqual(["%s records the family no-such-family, which the catalog does not have" % shapes.STATUS],
                         faults)


if __name__ == "__main__":
    unittest.main()

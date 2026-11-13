"""The proposed annotation vocabulary `1.0.0` (RFC 0032), its staged rows and its reference checker.

The companion, spec/annotation-vocabulary.md, is normative for nothing while RFC 0032 is a Draft,
and its rows under conformance/annotation-vocabulary/1.0.0/ are staged: in no corpus and no bundle.
Every expectation in the rows was written by hand. These tests hold:

- the machine-readable form, the checker and the companion text to one list of levels, one order
  and two codes;
- each row's Core `0.5.0` result, through the document corpus's own harness (test_repository), so
  that Core's acceptance of each value the vocabulary refuses is shown rather than assumed;
- each row's vocabulary result, findings and advisories, through the reference checker;
- inertness: the pair's packs have equal evaluation forms and give each hand-written disposition
  through the second Core evaluator, and removing the key from any admitted row changes neither;
- a second reading of the refusal: the fragment in vocabulary.json, applied by a general JSON
  Schema validator, refuses exactly the outcomes the checker refuses; and
- that neither the companion nor the rows reach a release bundle.

The site's exclusion of the rows is held in tests/test_site.py.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import unittest
from typing import Any

from jsonschema import Draft202012Validator

from test_repository import assert_findings, core_validators, evaluate_text
from tools import annotation_vocabulary as av
from tools import core_050_eval as ev

ROOT = av.ROOT
_BUILDER = importlib.util.spec_from_file_location("build_release", ROOT / "tools" / "build_release.py")
if _BUILDER is None or _BUILDER.loader is None:
    raise RuntimeError("could not load release builder")
BUILD_RELEASE = importlib.util.module_from_spec(_BUILDER)
_BUILDER.loader.exec_module(BUILD_RELEASE)
STAGED = av.STAGED
COMPANION = ROOT / "spec" / "annotation-vocabulary.md"
RFC = ROOT / "rfcs" / "0032-outcome-severity.md"
ANNOTATIONS = ev.ANNOTATIONS


def manifest() -> dict[str, Any]:
    return json.loads((STAGED / "manifest.json").read_text(encoding="utf-8"))


def vocabulary() -> dict[str, Any]:
    return json.loads((STAGED / "vocabulary.json").read_text(encoding="utf-8"))


def pairs(items: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {(item["code"], item["path"]) for item in items}


def without_severity(pack: dict[str, Any]) -> dict[str, Any]:
    """The pack with the key removed from every outcome, an emptied object removed with it."""
    stripped = copy.deepcopy(pack)
    for outcome in stripped["outcomes"]:
        extensions = outcome.get("extensions", {})
        annotations = extensions.get(ANNOTATIONS)
        if annotations is not None and av.KEY in annotations:
            del annotations[av.KEY]
            if not annotations:
                del extensions[ANNOTATIONS]
            if not extensions:
                del outcome["extensions"]
    return stripped


class VocabularyForm(unittest.TestCase):
    def test_the_file_the_checker_and_the_text_agree(self) -> None:
        document = vocabulary()
        self.assertEqual((av.VOCABULARY, av.VERSION, "proposed"),
                         (document["vocabulary"], document["version"], document["status"]))
        self.assertEqual(av.VERSION, manifest()["vocabularyVersion"])
        (key,) = document["keys"]
        self.assertEqual(av.KEY, key["key"])
        self.assertEqual(["outcome"], key["positions"])
        self.assertEqual("ascending", key["order"])
        self.assertEqual(list(av.LEVELS), key["values"])
        self.assertEqual(list(av.LEVELS), key["outcomeAnnotationsSchema"]["properties"]["severity"]["enum"])
        self.assertEqual((av.VALUE_CODE, av.IDENTIFIER_CODE), (key["refusal"], key["identifierAdvisory"]))
        # The fragment is not a catalogued schema family (catalog/README.md): it has no $id.
        self.assertNotIn("$id", json.dumps(document))

        text = COMPANION.read_text(encoding="utf-8")
        self.assertIn("annotation vocabulary version `1.0.0`, status `proposed`", text)
        table = [text.index(f"| `{level}` |") for level in av.LEVELS]
        self.assertEqual(sorted(table), table, "the companion's table lists the levels out of order")
        self.assertIn("`low` < `medium` < `high` < `critical`", text)
        for code in (av.VALUE_CODE, av.IDENTIFIER_CODE):
            with self.subTest(code=code):
                self.assertIn(code, text)
                self.assertIn(code, RFC.read_text(encoding="utf-8"))

    def test_every_pack_is_named_and_every_id_is_unique(self) -> None:
        rows = manifest()
        named = {row["pack"] for row in rows["rows"]}
        for pair in rows["pairs"]:
            named.update(pair["packs"])
        present = {path.relative_to(STAGED).as_posix() for path in (STAGED / "packs").glob("*.json")}
        self.assertEqual(present, named)
        ids = [row["id"] for row in rows["rows"]] + [pair["id"] for pair in rows["pairs"]]
        self.assertEqual(len(ids), len(set(ids)))


class CoreResult(unittest.TestCase):
    """What Core `0.5.0` says of each row: the vocabulary changes none of it (§2.6, §6.2)."""

    def test_each_row_has_its_core_result(self) -> None:
        validators = core_validators()
        for row in manifest()["rows"]:
            with self.subTest(row=row["id"]):
                text = (STAGED / row["pack"]).read_text(encoding="utf-8")
                result, diagnostics = evaluate_text(text, validators, [])
                expected = row["expectedCore"]
                self.assertEqual(expected["result"], result)
                if expected["diagnostic"] is None:
                    self.assertEqual([], diagnostics)
                else:
                    assert_findings(self, row["id"], [expected["diagnostic"]], diagnostics)
                # The second evaluator admits what the corpus harness calls valid or unsupported.
                admitted = ev.admit_pack(text).layer is None
                self.assertEqual(expected["result"] != "invalid", admitted)

    def test_core_admits_every_value_the_vocabulary_refuses(self) -> None:
        refused = [row for row in manifest()["rows"] if row["expectedResult"] == "refused"]
        self.assertGreaterEqual(len(refused), 8)
        for row in refused:
            with self.subTest(row=row["id"]):
                self.assertIn(row["expectedCore"]["result"], ("valid", "unsupported"))


class CheckerResult(unittest.TestCase):
    def test_each_row_has_its_vocabulary_result(self) -> None:
        for row in manifest()["rows"]:
            with self.subTest(row=row["id"]):
                report = av.check((STAGED / row["pack"]).read_bytes())
                self.assertEqual(av.VERSION, report["version"])
                self.assertEqual(row["expectedResult"], report["result"])
                self.assertEqual(pairs(row["expectedFindings"]), pairs(report["findings"]))
                self.assertEqual(len(row["expectedFindings"]), len(report["findings"]))
                self.assertEqual(pairs(row["expectedAdvisories"]), pairs(report["advisories"]))

    def test_the_rows_cover_each_refusal_the_text_names(self) -> None:
        by_id = {row["id"]: row for row in manifest()["rows"]}
        for name in ("refuse-unknown-value", "refuse-wrong-case", "refuse-none", "refuse-informational",
                     "refuse-look-alike", "refuse-list-one", "refuse-list-two"):
            with self.subTest(row=name):
                self.assertEqual("refused", by_id[name]["expectedResult"])
        for name in ("core-empty-string", "core-trailing-space", "core-number", "core-empty-list"):
            with self.subTest(row=name):
                self.assertEqual("not-checked", by_id[name]["expectedResult"])
                self.assertEqual([], by_id[name]["expectedFindings"])
        for name in ("not-checked-rule", "not-checked-root", "not-checked-entry", "not-checked-other-keys"):
            with self.subTest(row=name):
                self.assertEqual("pass", by_id[name]["expectedResult"])
                self.assertIn('"sev1"', (STAGED / by_id[name]["pack"]).read_text(encoding="utf-8"))

    def test_the_fragment_refuses_exactly_what_the_checker_refuses(self) -> None:
        (key,) = vocabulary()["keys"]
        fragment = Draft202012Validator(key["outcomeAnnotationsSchema"])
        for row in manifest()["rows"]:
            if row["expectedCore"]["result"] == "invalid":
                continue  # §6.2: the vocabulary is applied only to an admitted pack
            pack = json.loads((STAGED / row["pack"]).read_text(encoding="utf-8"))
            refused = {
                ev.pointer(["outcomes", index, "extensions", ANNOTATIONS, av.KEY])
                for index, outcome in enumerate(pack["outcomes"])
                if not fragment.is_valid(outcome.get("extensions", {}).get(ANNOTATIONS, {}))
            }
            with self.subTest(row=row["id"]):
                self.assertEqual({path for _, path in pairs(row["expectedFindings"])}, refused)


class Inertness(unittest.TestCase):
    def test_the_pair_has_one_evaluation_form_and_one_disposition_per_input(self) -> None:
        for pair in manifest()["pairs"]:
            self.assertEqual("evaluation-form", pair["basis"])
            texts = [(STAGED / name).read_bytes() for name in pair["packs"]]
            forms = [ev.evaluation_form(ev.admit_pack(text).pack) for text in texts]
            for name, form in zip(pair["packs"][1:], forms[1:]):
                with self.subTest(pair=pair["id"], pack=name):
                    self.assertTrue(ev.json_equal(forms[0], form))
            # The pair spans a pack the vocabulary passes and one it refuses.
            results = {av.check(text)["result"] for text in texts}
            self.assertEqual({"pass", "refused"}, results)
            for evaluation in pair["evaluations"]:
                expected = ev.canonical(evaluation["expectedDisposition"])
                for name, text in zip(pair["packs"], texts):
                    with self.subTest(pair=pair["id"], facts=evaluation["id"], pack=name):
                        result = ev.evaluate(text, json.dumps(evaluation["facts"]).encode(),
                                             json.dumps(evaluation["evidenceAvailability"]).encode(),
                                             evaluation["supportedExtensions"])
                        self.assertIsNone(result.error_class, result.detail)
                        self.assertEqual(expected, ev.canonical(result.disposition))

    def test_removing_the_key_changes_no_evaluation_form(self) -> None:
        # §2.6: a pack evaluates as the same pack with the key removed, whatever the value.
        checked = 0
        for row in manifest()["rows"]:
            text = (STAGED / row["pack"]).read_bytes()
            admission = ev.admit_pack(text)
            if admission.layer is not None:
                continue
            stripped = without_severity(admission.pack)
            stripped_text = ev.dump_json(stripped).encode("utf-8")
            with self.subTest(row=row["id"]):
                self.assertIsNone(ev.admit_pack(stripped_text).layer)
                self.assertTrue(ev.json_equal(ev.evaluation_form(admission.pack), ev.evaluation_form(stripped)))
                self.assertEqual("pass", av.check(stripped_text)["result"])
            checked += 1
        self.assertGreaterEqual(checked, 20)


class NotReleased(unittest.TestCase):
    def test_no_bundle_carries_the_companion_or_the_rows(self) -> None:
        # As for RFC 0020's Draft: the proposed companion is normative for nothing, so no bundle
        # carries it, and the rows are staged. Published companions and the corpus are the controls.
        excluded = [
            "spec/annotation-vocabulary.md",
            "conformance/annotation-vocabulary",
            "conformance/annotation-vocabulary/1.0.0/vocabulary.json",
            "conformance/annotation-vocabulary/1.0.0/manifest.json",
            "conformance/annotation-vocabulary/1.0.0/packs/each-level.json",
        ]
        released = ["spec/dialect.md", "spec/judgment-pack-core.md", "conformance/manifest.json"]
        try:
            completed = subprocess.run(
                ["git", "check-attr", "export-ignore", "--", *excluded, *released],
                cwd=ROOT, check=True, capture_output=True, text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git cannot read attributes here: {error}")
        attributes = dict(line.rsplit(": export-ignore: ", 1) for line in completed.stdout.splitlines())
        for path in excluded:
            with self.subTest(path=path):
                self.assertEqual("set", attributes.get(path))
        for path in released:
            with self.subTest(path=path):
                self.assertEqual("unspecified", attributes.get(path))

    def test_a_patch_tag_carries_core_unchanged_beside_the_vocabulary(self) -> None:
        # The builder's own patch-release check: Core 0.5.0's normative files are the bytes the
        # record names, and nothing added here joins that set (it is derived from the tree).
        paths = BUILD_RELEASE.normative_paths("0.5.0")
        self.assertIn("conformance/manifest.json", paths)
        added = [path for path in paths
                 if path.startswith("conformance/annotation-vocabulary/")
                 or path == "spec/annotation-vocabulary.md"]
        self.assertEqual([], added)
        BUILD_RELEASE.validate_unchanged_normative_artifacts("v0.5.2")


if __name__ == "__main__":
    unittest.main()

"""The annotation vocabulary `1.0.0`, status proposed (RFC 0032), its staged rows and its checker.

RFC 0032 is accepted at draft maturity. The companion, spec/annotation-vocabulary.md, is published
and bundled; its rows under conformance/annotation-vocabulary/1.0.0/ stay staged: in no corpus and
no bundle. Every expectation in the rows was written by hand. These tests hold:

- the machine-readable form, the checker and the companion text to one list of levels, one order,
  one position, one value form and two codes, each read from the companion's own sentences;
- each row's Core `0.5.0` result, through the document corpus's own harness (test_repository), so
  that Core's acceptance of each value the vocabulary refuses is shown rather than assumed;
- each row's vocabulary result, reason, findings and advisories, through the reference checker,
  with the `extended` row not run by this base-only checker, as in Core's document corpus;
- inertness: the pair's packs have equal evaluation forms and give each hand-written disposition
  through the second Core evaluator; removing the key from any admitted row, as §2.6 defines the
  removal, changes neither; and the two other readings of the removal are not §2.6's;
- a second reading of the refusal: the fragment in vocabulary.json, applied by a general JSON
  Schema validator, refuses exactly the outcomes the checker refuses; and
- that the companion reaches a release bundle and the rows do not, and that no bundled file links
  to the rows.

The companion's page, and the site's exclusion of the rows, are held in tests/test_site.py.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
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


def section(text: str, number: str) -> str:
    """The body of the companion's section `number` (such as "2.2"), up to the next heading."""
    match = re.search(rf"^#{{2,3}} {re.escape(number)} [^\n]*\n(.*?)(?=^#{{2,3}} |\Z)", text, re.M | re.S)
    if match is None:
        raise AssertionError(f"the companion has no section {number}")
    return match.group(1)


def without_severity(pack: dict[str, Any]) -> dict[str, Any]:
    """The same pack with the key removed, as the companion's §2.6 defines it after Core §8.5
    step 3: remove the member; if the annotations object is then empty, remove it; if that leaves
    the outcome's `extensions` object empty, remove that too. Nothing else is touched."""
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


def member_only_removed(pack: dict[str, Any]) -> dict[str, Any]:
    """The first reading §2.6 rules out: only the member removed, an emptied object left."""
    stripped = copy.deepcopy(pack)
    for outcome in stripped["outcomes"]:
        annotations = outcome.get("extensions", {}).get(ANNOTATIONS)
        if annotations is not None and av.KEY in annotations:
            del annotations[av.KEY]
    return stripped


def emptied_extensions_kept(pack: dict[str, Any]) -> dict[str, Any]:
    """The second reading §2.6 rules out: an emptied annotations object removed, but an
    `extensions` object it leaves empty kept."""
    stripped = member_only_removed(pack)
    for outcome in stripped["outcomes"]:
        extensions = outcome.get("extensions", {})
        if extensions.get(ANNOTATIONS) == {}:
            del extensions[ANNOTATIONS]
    return stripped


def declares_extended(text: str | bytes) -> bool:
    return json.loads(text).get("profile") == "extended"


# The Core layer a corpus code belongs to, for a pack Core refuses (§6.2: the checker reports it).
LAYER_OF_FAMILY = {"JPS-CARRIER-": "carrier", "JPS-STRUCTURE-": "structural", "JPS-SEMANTIC-": "semantic"}


def layer_of(code: str) -> str:
    (layer,) = [layer for family, layer in LAYER_OF_FAMILY.items() if code.startswith(family)]
    return layer


# Facts documents for the two bases the rows use (expense approval and access review), so that a
# comparison of results reaches outcomes, a conflict, an unknown and not-applicable in each.
FACTS = [
    {"expense": {"band": "within-limit", "receipt": "present"}},
    {"expense": {"band": "near-limit", "receipt": "present"}},
    {"expense": {"band": "over-limit", "receipt": "present"}},
    {"expense": {"band": "over-limit", "receipt": "missing"}},
    {"expense": {"receipt": "present"}},
    {"account": {"reviewed": True, "last-use": "inside-period", "approval": "present"}},
    {"account": {"reviewed": True, "last-use": "outside-period", "approval": "present"}},
    {"account": {"reviewed": True, "last-use": "outside-period", "approval": "missing"}},
    {"account": {"reviewed": False}},
    {},
]


def outcome_of(text: bytes, facts: dict[str, Any]) -> str:
    """The second evaluator's result for one facts document: the canonical disposition, or the
    evaluation error's class."""
    result = ev.evaluate(text, json.dumps(facts).encode(), b"{}", [])
    return ev.canonical(result.disposition) if result.disposition is not None else str(result.error_class)


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
        for code in (av.VALUE_CODE, av.IDENTIFIER_CODE):
            with self.subTest(code=code):
                self.assertIn(code, RFC.read_text(encoding="utf-8"))
        self.assertIn(av.VALUE_CODE, section(text, "6.3"))
        self.assertIn(av.IDENTIFIER_CODE, section(text, "3.1"))

    def test_the_file_holds_what_the_text_states(self) -> None:
        # Each member of vocabulary.json is read from the companion's own sentences, so that a
        # change to either one alone fails here.
        (key,) = vocabulary()["keys"]
        text = COMPANION.read_text(encoding="utf-8")

        # §2.1: the key and its one position.
        positions = re.findall(r"The key `([^`]+)` is defined in an? ([a-z-]+)'s annotations, and nowhere else\.",
                               section(text, "2.1"))
        self.assertEqual([(key["key"], "outcome")], positions)
        self.assertEqual(["outcome"], key["positions"])

        # §2.2: the table, row by row, is the list of values, and each row's place is its order.
        values_section = section(text, "2.2")
        table = re.findall(r"^\| `([^`]*)` \| ([^|\n]*?) \|$", values_section, re.M)
        values = [value for value, _ in table]
        self.assertEqual(key["values"], values)
        self.assertEqual(list(av.LEVELS), values)
        self.assertEqual(key["outcomeAnnotationsSchema"]["properties"]["severity"]["enum"], values)
        places = ["least severe", *[f"above `{below}`" for below in values[:-2]], "most severe"]
        self.assertEqual(places, [place for _, place in table])

        # §2.2: the order sentence, whole: its direction and its chain of every value, in order.
        sentences = re.findall(r"The order is total and ([a-z]+): ([^.\n]*)\.", values_section)
        self.assertEqual(1, len(sentences), sentences)
        ((direction, chain),) = sentences
        self.assertEqual(key["order"], direction)
        self.assertEqual("ascending", direction)
        self.assertRegex(chain, r"^`[^`]+`(?: < `[^`]+`)*$")
        self.assertEqual(values, re.findall(r"`([^`]+)`", chain))

        # §2.3: absence; §2.5: one annotation string.
        self.assertIn(f"**{key['absence']}**", " ".join(section(text, "2.3").split()))
        forms = re.findall(r"The value of `([^`]+)` MUST be one annotation ([a-z]+)\.", section(text, "2.5"))
        self.assertEqual([(key["key"], key["valueForm"])], forms)
        self.assertEqual("string", key["valueForm"])

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
                # The second evaluator admits what the corpus harness calls valid or unsupported,
                # except a pack that declares `extended`, which as a base-only reader it does not run.
                layer = ev.admit_pack(text).layer
                if declares_extended(text):
                    self.assertEqual("profile", layer)
                else:
                    self.assertEqual(expected["result"] != "invalid", layer is None)

    def test_core_admits_every_value_the_vocabulary_refuses(self) -> None:
        refused = [row for row in manifest()["rows"] if row["expectedResult"] == "refused"]
        self.assertGreaterEqual(len(refused), 8)
        for row in refused:
            with self.subTest(row=row["id"]):
                self.assertIn(row["expectedCore"]["result"], ("valid", "unsupported"))


class CheckerResult(unittest.TestCase):
    def test_each_row_has_its_vocabulary_result(self) -> None:
        not_run = []
        for row in manifest()["rows"]:
            with self.subTest(row=row["id"]):
                text = (STAGED / row["pack"]).read_bytes()
                report = av.check(text)
                self.assertEqual(av.VERSION, report["version"])
                if declares_extended(text):
                    # Core's corpus convention: a base-only reader does not run the row, and says so.
                    self.assertEqual(("not-checked", av.REASON_PROFILE, None, []),
                                     (report["result"], report["reason"], report["coreLayer"], report["findings"]))
                    not_run.append(row["id"])
                    continue
                self.assertEqual(row["expectedResult"], report["result"])
                self.assertEqual(row["expectedReason"], report["reason"])
                self.assertEqual(pairs(row["expectedFindings"]), pairs(report["findings"]))
                self.assertEqual(len(row["expectedFindings"]), len(report["findings"]))
                self.assertEqual(pairs(row["expectedAdvisories"]), pairs(report["advisories"]))
                # §6.2: Core's refusal is reported with the layer that refused it, and only then.
                if row["expectedReason"] == av.REASON_CORE:
                    self.assertEqual(layer_of(row["expectedCore"]["diagnostic"]["code"]), report["coreLayer"])
                else:
                    self.assertIsNone(report["coreLayer"])
        self.assertEqual(["profile-extended"], not_run)
        failures, rows_not_run = av.run_rows()
        self.assertEqual(([], not_run), (failures, rows_not_run))

    def test_not_applied_always_says_why(self) -> None:
        # §6.2: every row the vocabulary is not applied to names one of the three reasons, and a
        # row it is applied to names none.
        reasons = {av.REASON_SELECTOR, av.REASON_CORE, av.REASON_PROFILE}
        self.assertEqual(3, len(reasons))
        for row in manifest()["rows"]:
            with self.subTest(row=row["id"]):
                if row["expectedResult"] == "not-checked":
                    self.assertIn(row["expectedReason"], reasons - {av.REASON_PROFILE})
                    self.assertEqual([], row["expectedFindings"])
                    self.assertEqual([], row["expectedAdvisories"])
                else:
                    self.assertIsNone(row["expectedReason"])

    def test_another_selector_is_not_applied_and_is_not_a_core_refusal(self) -> None:
        # §6.2: the vocabulary applies only to 0.5.0. Each selector row holds a value the
        # vocabulary refuses, so its result is the selector's doing: the same pack declaring 0.5.0
        # is refused.
        by_id = {row["id"]: row for row in manifest()["rows"]}
        declared = {}
        for name in ("selector-earlier", "selector-later"):
            with self.subTest(row=name):
                row = by_id[name]
                self.assertEqual(("not-checked", av.REASON_SELECTOR),
                                 (row["expectedResult"], row["expectedReason"]))
                self.assertEqual("JPS-STRUCTURE-SPEC-VERSION", row["expectedCore"]["diagnostic"]["code"])
                pack = json.loads((STAGED / row["pack"]).read_text(encoding="utf-8"))
                declared[name] = tuple(int(part) for part in pack["specVersion"].split("."))
                pack["specVersion"] = av.SPEC_VERSION
                report = av.check(ev.dump_json(pack).encode("utf-8"))
                self.assertEqual(("refused", None), (report["result"], report["reason"]))
        self.assertLess(declared["selector-earlier"], (0, 5, 0))
        self.assertGreater(declared["selector-later"], (0, 5, 0))

    def test_the_extended_row_records_what_the_same_pack_gives_under_base(self) -> None:
        # The row's expectations are a reader's that supports `extended`. The pack is within every
        # base ceiling, and the vocabulary reads no ceiling, so the same pack declaring no profile
        # gives them under this base-only checker.
        (row,) = [row for row in manifest()["rows"] if declares_extended((STAGED / row["pack"]).read_bytes())]
        pack = json.loads((STAGED / row["pack"]).read_text(encoding="utf-8"))
        del pack["profile"]
        report = av.check(ev.dump_json(pack).encode("utf-8"))
        self.assertEqual((row["expectedResult"], row["expectedReason"]), (report["result"], report["reason"]))
        self.assertEqual(pairs(row["expectedFindings"]), pairs(report["findings"]))
        self.assertEqual(pairs(row["expectedAdvisories"]), pairs(report["advisories"]))

    def test_the_rows_cover_each_refusal_the_text_names(self) -> None:
        by_id = {row["id"]: row for row in manifest()["rows"]}
        for name in ("refuse-unknown-value", "refuse-wrong-case", "refuse-none", "refuse-informational",
                     "refuse-look-alike", "refuse-list-one", "refuse-list-two"):
            with self.subTest(row=name):
                self.assertEqual("refused", by_id[name]["expectedResult"])
        for name in ("core-empty-string", "core-trailing-space", "core-number", "core-empty-list"):
            with self.subTest(row=name):
                self.assertEqual(("not-checked", av.REASON_CORE),
                                 (by_id[name]["expectedResult"], by_id[name]["expectedReason"]))
                self.assertEqual([], by_id[name]["expectedFindings"])
        # A key the vocabulary ignores passes: these rows are named `ignored-`, not after a result.
        for name in ("ignored-rule", "ignored-root", "ignored-entry", "ignored-other-keys"):
            with self.subTest(row=name):
                self.assertEqual("pass", by_id[name]["expectedResult"])
                self.assertIn('"sev1"', (STAGED / by_id[name]["pack"]).read_text(encoding="utf-8"))
        self.assertEqual([], [row_id for row_id in by_id if row_id.startswith("not-checked")])

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

    def test_removing_the_key_changes_no_evaluation_form_and_no_result(self) -> None:
        # §2.6: a pack evaluates as the same pack with the key removed, whatever the value. This is
        # a structural control of the removal §2.6 defines: the evaluation forms are compared by the
        # function that computes them, so their equality follows from Core §8.5 step 3 as that
        # function implements it. The results are compared too, through the second evaluator. The
        # hand-written dispositions are the pair's.
        checked = 0
        outcomes = 0
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
                for facts in FACTS:
                    got = outcome_of(text, facts)
                    self.assertEqual(got, outcome_of(stripped_text, facts), facts)
                    outcomes += '"kind":"outcome"' in got
            checked += 1
        self.assertGreaterEqual(checked, 20)
        self.assertGreaterEqual(outcomes, 40)

    def test_the_two_other_readings_of_removal_are_not_section_2_6s(self) -> None:
        # §2.6 defines the removal so that it is true when `severity` is an outcome's only
        # annotation key. each-level.json is such a pack: every outcome's annotations hold the key
        # alone, and no outcome has another extension.
        text = (STAGED / "packs" / "each-level.json").read_bytes()
        pack = ev.admit_pack(text).pack
        self.assertTrue(all(outcome["extensions"] == {ANNOTATIONS: {av.KEY: outcome["extensions"][ANNOTATIONS][av.KEY]}}
                            for outcome in pack["outcomes"]))
        form = ev.evaluation_form(pack)

        # §2.6's removal: a conforming pack, whose evaluation form is the pack's.
        defined = without_severity(pack)
        self.assertTrue(all("extensions" not in outcome for outcome in defined["outcomes"]))
        self.assertIsNone(ev.admit_pack(ev.dump_json(defined)).layer)
        self.assertTrue(ev.json_equal(form, ev.evaluation_form(defined)))

        # Removing only the member leaves `{}`, which Core §9.2 refuses: not a conforming pack.
        member_only = ev.dump_json(member_only_removed(pack))
        result, diagnostics = evaluate_text(member_only, core_validators(), [])
        self.assertEqual("invalid", result)
        self.assertIn(f"/outcomes/0/extensions/{ANNOTATIONS}", {diagnostic.path for diagnostic in diagnostics})
        self.assertEqual("structural", ev.admit_pack(member_only).layer)

        # Keeping an emptied `extensions` object gives a conforming pack whose evaluation form keeps
        # it (Core §8.5 keeps an `extensions` object already empty), so it is not the pack's.
        kept = emptied_extensions_kept(pack)
        self.assertTrue(all(outcome.get("extensions") == {} for outcome in kept["outcomes"]))
        self.assertIsNone(ev.admit_pack(ev.dump_json(kept)).layer)
        self.assertFalse(ev.json_equal(form, ev.evaluation_form(kept)))

        # Another member beside the annotations stays, and the forms are still equal.
        beside = copy.deepcopy(pack)
        beside["outcomes"][0]["extensions"]["com.example.authoring"] = {"draftedWith": "editor"}
        removed = without_severity(beside)
        self.assertEqual({"com.example.authoring": {"draftedWith": "editor"}}, removed["outcomes"][0]["extensions"])
        self.assertIsNone(ev.admit_pack(ev.dump_json(removed)).layer)
        self.assertTrue(ev.json_equal(ev.evaluation_form(beside), ev.evaluation_form(removed)))

        # The companion states the three steps, and rules out both readings, in §2.6.
        inertness = section(COMPANION.read_text(encoding="utf-8"), "2.6")
        for step in (
            "1. the member `severity` is removed from the outcome's annotations object;",
            "2. if that leaves the annotations object empty, the member `org.judgmentpack.annotations` is\n"
            "   removed from the outcome's `extensions` object; and",
            "3. if that leaves the `extensions` object empty, the outcome's `extensions` member is removed.",
        ):
            with self.subTest(step=step[:2]):
                self.assertIn(step, inertness)
        self.assertIn("Removing only the member can leave an empty\nannotations object, which Core §9.2 refuses",
                      inertness)


class Released(unittest.TestCase):
    def test_the_rfc_is_accepted_on_a_recorded_review_and_core_is_untouched(self) -> None:
        # Accepted as RFC 0031 was: a same-vendor round, the different-vendor review waived, and
        # the round copied into the repository as RFC 0018's acceptance did. The vocabulary keeps
        # its status, and Core 0.5.0 is frozen, so its §1.1 does not list the companion.
        rfc = RFC.read_text(encoding="utf-8")
        self.assertIn("\n- Status: Accepted\n", rfc)
        self.assertNotIn("- Status: Draft", rfc)
        self.assertIn("\n- Accepted: 2026-11-13, by the maintainer,", rfc)
        acceptance = rfc[rfc.index("\n## Acceptance\n"):]
        for phrase in ("The different-vendor review was waived.", "D19 (b)"):
            self.assertIn(phrase, acceptance)
        review = (ROOT / "rfcs" / "reviews" / "0032-round-1.md").read_text(encoding="utf-8")
        self.assertIn("## Review record (same vendor, not a cross-vendor claim)", review)
        index = (ROOT / "rfcs" / "README.md").read_text(encoding="utf-8")
        self.assertIn("| [0032](0032-outcome-severity.md) | Outcome severity, one well-known annotation key "
                      "| Accepted |", index)
        companion = COMPANION.read_text(encoding="utf-8")
        self.assertIn("This text is annotation vocabulary version `1.0.0`, status `proposed`.", companion)
        self.assertNotIn("normative for nothing", companion)
        core = (ROOT / "spec" / "judgment-pack-core.md").read_text(encoding="utf-8")
        self.assertNotIn("annotation-vocabulary", core[core.index("### 1.1"):core.index("## 2.")])

    def test_bundles_carry_the_companion_and_not_the_rows(self) -> None:
        # As for RFC 0018's acceptance: the accepted companion is bundled, and its rows stay staged,
        # with the machine-readable form among them. The other published companions and the corpus
        # are the controls.
        excluded = [
            "conformance/annotation-vocabulary",
            "conformance/annotation-vocabulary/1.0.0/vocabulary.json",
            "conformance/annotation-vocabulary/1.0.0/manifest.json",
            "conformance/annotation-vocabulary/1.0.0/packs/each-level.json",
        ]
        released = ["spec/annotation-vocabulary.md", "spec/dialect.md", "spec/judgment-pack-core.md",
                    "conformance/manifest.json"]
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

    def test_no_bundled_file_links_to_an_export_ignored_file(self) -> None:
        # A bundle leaves out the rows (export-ignore), so a relative link to them from a Markdown
        # file the bundle carries would dangle there; the companion, now bundled, links to them on
        # the repository instead. The bundled files are the builder's own list, less what
        # export-ignore removes.
        def export_ignored(paths: list[str]) -> set[str]:
            completed = subprocess.run(["git", "check-attr", "export-ignore", "--", *paths],
                                       cwd=ROOT, check=True, capture_output=True, text=True)
            return {line.rsplit(": export-ignore: ", 1)[0] for line in completed.stdout.splitlines()
                    if line.endswith(": export-ignore: set")}

        root = ROOT.resolve()
        candidates = []
        for entry in BUILD_RELEASE.BUNDLE_PATHS:
            path = root / entry
            found = sorted(path.rglob("*.md")) if path.is_dir() else [path] if path.suffix == ".md" else []
            candidates.extend(item.relative_to(root).as_posix() for item in found)
        try:
            bundled = sorted(set(candidates) - export_ignored(candidates))
            self.assertIn("CHANGELOG.md", bundled)
            self.assertIn("spec/annotation-vocabulary.md", bundled)
            targets: dict[str, list[str]] = {}
            for name in bundled:
                for link in re.findall(r"\]\(([^)\s]+)\)", (root / name).read_text(encoding="utf-8")):
                    path = link.split("#", 1)[0]
                    if not path or re.match(r"[a-z]+:", path):
                        continue
                    resolved = (root / name).parent.joinpath(path).resolve()
                    if resolved.is_relative_to(root):
                        targets.setdefault(resolved.relative_to(root).as_posix(), []).append(name)
            self.assertIn("VERSIONING.md", targets)  # the control: links are read
            dangling = {path: targets[path] for path in export_ignored(sorted(targets))}
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git cannot read attributes here: {error}")
        self.assertEqual({}, dangling)


if __name__ == "__main__":
    unittest.main()

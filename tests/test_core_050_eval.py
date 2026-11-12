"""Every evaluation row and document case of Core `0.5.0`, run through the second evaluator.

The evaluator (tools/core_050_eval.py) was written from Core `0.3.0`, the staged delta and RFC 0031
alone, which are Core `0.5.0` now. These tests run every evaluation row of the manifest, every row
staged after `0.3.0`, and every document case through it, and compare each result with the
expectation written by hand. A disagreement is a finding against the row or the evaluator, settled
in review: no expectation is ever replaced by this evaluator's output. Only the `base` profile is
supported; a fixture that declares `extended` is checked to be refused with `profile-unsupported`,
not run.
"""
from __future__ import annotations

import copy
import unittest
from pathlib import Path
from typing import Any

from tools import core_050_eval as ev

ROOT = ev.ROOT
ROWS = ev.EVALUATION
HISTORICAL = ROOT / "tests" / "fixtures" / "historical-compatibility"


def load(path: Path) -> Any:
    return ev.load_json(path.read_bytes())


def disposition(text: str) -> Any:
    return ev.load_json(text)


def rows_document() -> dict[str, Any]:
    return load(ROWS / "manifest.json")


def all_rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in document["cases"]}


def added_packs(document: dict[str, Any]) -> set[str]:
    """The packs of the rows `0.5.0` adds: those the `0.3.0` manifest does not name."""
    previous = {row["id"] for row in load(HISTORICAL / "0.3.0-evaluation-manifest.json")["cases"]}
    return {row["pack"] for row in document["cases"] if row["id"] not in previous}


def result_of(row: dict[str, Any], base: Path = ROWS) -> tuple[str, Any]:
    return ev.run_row(row, base).expected_form()


def show(form: tuple[str, Any]) -> str:
    return f"{form[0]} {ev.canonical(form[1])}"


def admitted(path: Path) -> dict[str, Any] | None:
    admission = ev.admit_pack(path.read_bytes())
    return admission.pack if admission.layer is None else None


class RowsTest(unittest.TestCase):
    """The 103 rows of conformance/evaluation/manifest.json: 20 of Core 0.3.0 and 83 that 0.5.0 adds."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.document = rows_document()

    def test_the_rows_declare_the_selector(self) -> None:
        self.assertEqual(ev.SELECTOR, self.document["specVersion"])
        self.assertEqual("0.5.0", ev.SELECTOR)

    def test_every_row_gives_its_expected_result(self) -> None:
        self.assertEqual(103, len(self.document["cases"]))
        for row in self.document["cases"]:
            with self.subTest(row=row["id"]):
                got, expected = result_of(row), ev.expected_of(row)
                self.assertTrue(ev.agrees(got, expected), f"got {show(got)}; expected {show(expected)}")

    def test_the_row_once_held_is_a_row(self) -> None:
        # Core §8.2: a name no conforming pack can require is ignored in a supported-extension set,
        # so the row the 0.3.0 case schema could not state runs like any other.
        (row,) = [row for row in self.document["cases"] if ev.ANNOTATIONS in row["supportedExtensions"]]
        self.assertEqual("annotations-supported-extension-set", row["id"])
        got, expected = result_of(row), ev.expected_of(row)
        self.assertTrue(ev.agrees(got, expected), f"got {show(got)}; expected {show(expected)}")

    def test_the_command_line_tally(self) -> None:
        results = ev.run_rows()
        self.assertEqual(103, sum(1 for item in results if item.status == "passed"))
        self.assertEqual([], [item.id for item in results if item.status != "passed"])


class PairsTest(unittest.TestCase):
    """The rows' pairs: a pack and its inline twin, annotated and bare, evaluate identically."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.document = rows_document()
        cls.rows = all_rows(cls.document)

    def test_every_pair_evaluates_identically(self) -> None:
        self.assertEqual(29, len(self.document["pairs"]))
        for pair in self.document["pairs"]:
            with self.subTest(pair=pair["id"]):
                results = {show(result_of(self.rows[case])) for case in pair["cases"]}
                self.assertEqual(1, len(results), results)

    def test_evaluation_form_pairs_have_equal_evaluation_forms(self) -> None:
        for pair in self.document["pairs"]:
            if pair["basis"] != "evaluation-form":
                continue
            with self.subTest(pair=pair["id"]):
                packs = [self.rows[case]["pack"] for case in pair["cases"]]
                forms = [ev.evaluation_form(admitted(ROWS / pack)) for pack in dict.fromkeys(packs)]
                self.assertGreater(len(forms), 1, "the pair names one pack")
                for form in forms[1:]:
                    self.assertTrue(ev.json_equal(forms[0], form), f"{packs}: evaluation forms differ")

    def test_optional_extension_pairs_differ_only_in_optional_vendor_extensions(self) -> None:
        pairs = [pair for pair in self.document["pairs"] if pair["basis"] == "optional-extension"]
        self.assertEqual(1, len(pairs))
        for pair in pairs:
            with self.subTest(pair=pair["id"]):
                forms = [ev.evaluation_form(admitted(ROWS / self.rows[case]["pack"])) for case in pair["cases"]]
                self.assertFalse(ev.json_equal(forms[0], forms[1]), "the forms are equal: the basis is evaluation-form")
                stripped = [without_optional_extensions(form) for form in forms]
                self.assertTrue(ev.json_equal(stripped[0], stripped[1]))
                for case in pair["cases"]:
                    got = ev.run_row(self.rows[case], ROWS)
                    stripped_text = ev.dump_json(without_optional_extensions(
                        ev.evaluation_form(admitted(ROWS / self.rows[case]["pack"]))))
                    bare = ev.evaluate(stripped_text, self.rows[case]["facts"], self.rows[case].get("evidenceAvailability"),
                                       self.rows[case]["supportedExtensions"])
                    self.assertEqual(show(got.expected_form()), show(bare.expected_form()))

    def test_supported_extension_set_pairs_differ_only_by_the_annotations_name(self) -> None:
        pairs = [pair for pair in self.document["pairs"] if pair["basis"] == "supported-extension-set"]
        self.assertEqual(1, len(pairs))
        for pair in pairs:
            rows = [self.rows[case] for case in pair["cases"]]
            self.assertEqual(1, len({row["pack"] for row in rows}))
            sets = [set(row["supportedExtensions"]) for row in rows]
            self.assertEqual({ev.ANNOTATIONS}, sets[0] ^ sets[1])

    def test_every_pack_is_its_own_evaluation_form_exactly_when_listed(self) -> None:
        # The list names the packs of the rows 0.5.0 adds; every other conforming pack fixture is its
        # own evaluation form too, holding no value set and no annotation.
        listed = set(self.document["ownEvaluationForm"])
        added = added_packs(self.document)
        seen = set()
        for path in sorted((ROWS / "packs").glob("*.json")):
            name = f"packs/{path.name}"
            pack = admitted(path)
            if name not in added:
                with self.subTest(pack=name):
                    self.assertNotIn(name, listed)
                    self.assertTrue(pack is None or ev.json_equal(ev.evaluation_form(pack), pack))
                continue
            if pack is None:
                self.assertNotIn(name, listed)
                continue
            with self.subTest(pack=name):
                own = ev.json_equal(ev.evaluation_form(pack), pack)
                self.assertEqual(name in listed, own)
                seen.add(name)
        self.assertLessEqual(listed, seen)


def without_optional_extensions(form: dict[str, Any]) -> dict[str, Any]:
    """The form with every extension name not listed as required removed (Core §9: optional), and
    an `extensions` member that held only such names removed with them, as Core §8.5 step 3
    removes one that annotations alone filled; one already empty is kept."""
    form = copy.deepcopy(form)
    required = set(form.get("metadata", {}).get("requiredExtensions", []))
    _, schema = ev._schema()
    for holder in ev.extension_holders(form, schema):
        extensions = holder["extensions"]
        optional = [name for name in extensions if name not in required]
        for name in optional:
            del extensions[name]
        if optional and not extensions:
            del holder["extensions"]
    return form


class StagedRowsTest(unittest.TestCase):
    """The rows staged after Core 0.3.0 (issue #219), which declare 0.5.0 since the graduation."""

    def test_staged_rows_of_core_0_3_0(self) -> None:
        manifest = ROOT / "conformance" / "evaluation" / "staged" / "cases.json"
        document = load(manifest)
        self.assertEqual("0.5.0", document["stagedAfter"])
        self.assertEqual(15, len(document["cases"]))
        for row in document["cases"]:
            with self.subTest(row=row["id"]):
                got, expected = result_of(row, manifest.parent), ev.expected_of(row)
                self.assertTrue(ev.agrees(got, expected), f"got {show(got)}; expected {show(expected)}")


class DocumentCasesTest(unittest.TestCase):
    """The document cases of conformance/manifest.json, at the layers this module admits: carrier,
    profile, structural (the schema), and semantic (written here)."""

    def check_case(self, case: dict[str, Any], data: bytes, tally: dict[str, int]) -> None:
        result, admission = ev.admit_document(data, case.get("supportedExtensions", []))
        if admission.profile == "extended":
            # A base-only reader refuses the declaration with the one diagnostic of Core §4.1.
            self.assertEqual(ev.PROFILE_UNSUPPORTED, result)
            tally["extended, refused"] += 1
            return
        expected = case["expectedResult"]
        self.assertEqual(expected, result, f"{admission.layer}: {admission.detail or admission.findings}")
        if expected == "valid":
            self.assertEqual([], admission.findings)
        elif expected == "unsupported" or case["layer"] == "semantic":
            wanted = (case["expectedDiagnostic"]["code"], case["expectedDiagnostic"]["path"])
            self.assertEqual({wanted}, set(admission.findings))
            self.assertEqual("semantic" if expected == "invalid" else None, admission.layer)
        else:
            self.assertEqual(case["layer"], admission.layer, admission.detail)
        tally[f"{case['layer']} {expected}"] += 1

    def test_document_cases(self) -> None:
        document = load(ROOT / "conformance" / "manifest.json")
        tally: dict[str, int] = {}
        for case in document["cases"]:
            for key in (f"{case['layer']} {case['expectedResult']}", "extended, refused"):
                tally.setdefault(key, 0)
            with self.subTest(case=case["id"]):
                self.check_case(case, (ROOT / "conformance" / case["path"]).read_bytes(), tally)
        self.assertEqual(371, len(document["cases"]))
        self.assertEqual(18, tally["extended, refused"])
        self.assertEqual(1, tally["semantic unsupported"])


class TextReadingsTest(unittest.TestCase):
    """The readings of the text the rows rely on, each stated once with its section."""

    def baseline(self) -> dict[str, Any]:
        return load(ROWS / "packs" / "inert-baseline.json")

    def evaluate(self, pack: dict[str, Any], facts: Any, evidence: Any = None, supported: Any = (), **options: Any):
        return ev.evaluate(ev.dump_json(pack), facts, evidence, supported, **options)

    def test_numbers_compare_by_mathematical_value(self) -> None:  # Core §7.4
        n = ev.Number
        for left, right in [("1", "1.0"), ("1", "1e0"), ("1", "10E-1"), ("0", "-0"), ("0", "0.0e5"),
                            ("1e400", "10e399"), ("1.5", "15e-1"), ("-2.50", "-25E-1")]:
            self.assertTrue(ev.json_equal(n(left), n(right)), (left, right))
        for left, right in [("9007199254740993", "9007199254740992"), ("1.5", "15e-2"), ("1", "-1"),
                            ("1e400", "1e399")]:
            self.assertFalse(ev.json_equal(n(left), n(right)), (left, right))

    def test_no_coercion_between_types(self) -> None:  # Core §7.4
        one = ev.Number("1")
        for other in (True, "1", [one], {"a": one}, None):
            self.assertFalse(ev.json_equal(one, other), other)
        self.assertFalse(ev.json_equal(True, ev.Number("1")))
        self.assertTrue(ev.json_equal({"a": one, "b": [None, "x"]}, {"b": [None, "x"], "a": ev.Number("1.0")}))
        self.assertFalse(ev.json_equal([one, "x"], ["x", one]))

    def test_pointers(self) -> None:  # Core §7.4, RFC 6901
        facts = ev.load_json('{"a/b": 1, "~1": 2, "": 3, "list": [10, 20], "s": "text"}')
        found = lambda path: ev.resolve_pointer(facts, path)
        self.assertEqual((True, facts), found(""))
        self.assertTrue(ev.json_equal(ev.Number("1"), found("/a~1b")[1]))
        self.assertTrue(ev.json_equal(ev.Number("2"), found("/~01")[1]))
        self.assertTrue(ev.json_equal(ev.Number("3"), found("/")[1]))
        self.assertTrue(ev.json_equal(ev.Number("20"), found("/list/1")[1]))
        for path in ("/list/01", "/list/-", "/list/2", "/s/0", "/missing", "/list/x"):
            self.assertEqual((False, None), found(path), path)

    def test_ordered_comparisons_read_decimal_strings_only(self) -> None:  # Core §7.4
        run = ev._Run({"v": "999.99", "n": ev.Number("5"), "e": "1.0"}, {}, ev.WORK_LIMIT)
        fact = lambda path, operator, value: run.fact({"path": path, "operator": operator, "value": value})
        self.assertTrue(fact("/v", "less-than", "1000"))
        self.assertIsNone(fact("/n", "greater-than", "4"))
        self.assertIsNone(fact("/missing", "greater-than", "4"))
        self.assertFalse(fact("/e", "equals", "1.00"))
        self.assertTrue(fact("/e", "not-equals", "1.00"))
        self.assertFalse(fact("/e", "greater-than", "1.00"))
        self.assertFalse(fact("/e", "less-than", "1.00"))
        self.assertTrue(fact("/e", "greater-than-or-equal", "1.00"))

    def test_carrier_refusals(self) -> None:  # Core §2.1
        for text in ('{"a": 1, "a": 2}', '{"a": NaN}', '{"a": Infinity}', '"\\ud800"', '"\\udc00\\ud800"',
                     '{"a": 1} x', '{"a": ', b'"\xff"'):
            with self.subTest(text=text):
                with self.assertRaises(ev.CarrierError):
                    ev.load_json(text)
        self.assertEqual("\U0001F600", ev.load_json('"\\ud83d\\ude00"'))
        self.assertEqual({}, ev.load_json("{} \n"))

    def test_preflight_order_and_input_errors(self) -> None:  # Core §8.2, §8.4
        pack, facts = self.baseline(), {"request": {"kind": "intake", "tier": "tier-1", "flagged": False}}
        self.assertEqual(ev.MALFORMED_INPUT, self.evaluate(pack, b'{"a": 1, "a": 1}').error_class)
        self.assertEqual(ev.MALFORMED_INPUT, self.evaluate(pack, facts, []).error_class)
        self.assertEqual(ev.MALFORMED_INPUT, self.evaluate(pack, facts, {"receipt": "present"}).error_class)
        declared = copy.deepcopy(pack)
        declared["evidenceRequirements"] = [{"id": "receipt", "description": "A receipt.", "required": False}]
        self.assertEqual(ev.MALFORMED_INPUT, self.evaluate(declared, facts, {"receipt": "yes"}).error_class)
        self.assertIsNotNone(self.evaluate(declared, facts, {"receipt": "present"}).disposition)
        broken = copy.deepcopy(pack)
        broken["rules"][0]["outcome"] = "missing"
        self.assertEqual(ev.PACK_NOT_CONFORMANT, self.evaluate(broken, b"{", []).error_class)
        required = copy.deepcopy(pack)
        required["metadata"] = {"requiredExtensions": ["com.example.policy"]}
        required["rules"][0]["extensions"] = {"com.example.policy": True}
        self.assertEqual(ev.MALFORMED_INPUT, self.evaluate(required, facts, []).error_class)
        self.assertEqual(ev.UNSUPPORTED_REQUIRED_EXTENSION, self.evaluate(required, facts).error_class)
        self.assertIsNotNone(self.evaluate(required, facts, None, ["com.example.policy"]).disposition)

    def test_a_base_reader_refuses_an_extended_pack(self) -> None:  # Core §4.1
        pack = self.baseline()
        pack["profile"] = "extended"
        result = self.evaluate(pack, {})
        self.assertEqual({"code": "profile-unsupported", "profile": "extended"}, result.refusal)
        self.assertIsNone(result.disposition)
        self.assertIsNone(result.error_class)
        pack["profile"] = "base"
        self.assertIsNotNone(self.evaluate(pack, {}).disposition)
        pack["profile"] = "huge"
        self.assertEqual(ev.PACK_NOT_CONFORMANT, self.evaluate(pack, {}).error_class)

    def test_a_name_no_pack_can_require_is_ignored_in_the_supported_set(self) -> None:  # Core §8.2
        self.assertFalse(ev.requirable(ev.ANNOTATIONS))
        self.assertFalse(ev.requirable("org.judgmentpack.future"))
        self.assertTrue(ev.requirable("com.example.policy"))

    def test_format_assertions_are_available(self) -> None:  # Core §3.2
        validator, _ = ev._schema()
        self.assertLessEqual({"uri", "date", "date-time"}, set(validator.format_checker.checkers))

    def test_the_evaluation_form(self) -> None:  # Core §8.5
        valid = ROOT / "conformance" / "valid"
        kept = admitted(valid / "annotations-empty-extensions.json")
        form = ev.evaluation_form(kept)
        empties = [rule["id"] for rule in kept["rules"] if rule.get("extensions") == {}]
        self.assertTrue(empties)
        self.assertEqual(empties, [rule["id"] for rule in form["rules"] if rule.get("extensions") == {}])
        self.assertNotIn(ev.ANNOTATIONS, form.get("extensions", {}))
        beside = admitted(valid / "annotations-required-vendor-beside.json")
        form = ev.evaluation_form(beside)
        names = {name for item in form["rules"] for name in item.get("extensions", {})}
        self.assertEqual({"com.example.review-policy"}, names)
        before = copy.deepcopy(beside)
        ev.evaluation_form(beside)
        self.assertTrue(ev.json_equal(before, beside), "the evaluation form changed its input")
        empty = admitted(ROWS / "packs" / "value-set-empty-collection.json")
        self.assertEqual([], empty["valueSets"])
        self.assertNotIn("valueSets", ev.evaluation_form(empty))

    def test_a_reference_costs_what_its_inline_twin_costs(self) -> None:  # Core §10
        document = rows_document()
        rows = all_rows(document)
        for pair in document["pairs"]:
            if not pair["id"].startswith("value-set-"):
                continue
            with self.subTest(pair=pair["id"]):
                work = {ev.run_row(rows[case], ROWS).work for case in pair["cases"]}
                self.assertEqual(1, len(work), work)

    def test_the_work_limit_is_an_evaluation_error(self) -> None:  # Core §10, §8.4
        facts = {"request": {"kind": "intake", "tier": "tier-1", "flagged": False}}
        full = self.evaluate(self.baseline(), facts)
        self.assertIsNotNone(full.disposition)
        short = self.evaluate(self.baseline(), facts, work_limit=full.work - 1)
        self.assertEqual(ev.RESOURCE_EXHAUSTION, short.error_class)
        self.assertIsNone(short.disposition)
        exact = self.evaluate(self.baseline(), facts, work_limit=full.work)
        self.assertEqual(ev.canonical(full.disposition), ev.canonical(exact.disposition))

    def test_dispositions_canonicalize_with_sorted_sets(self) -> None:  # Core §8.3
        self.assertEqual('{"handoff":{"state":"none"},"kind":"outcome","outcomeId":"proceed","reasons":[]}',
                         ev.canonical({"kind": "outcome", "outcomeId": "proceed", "reasons": [], "handoff": {"state": "none"}}))
        handoff = ev._handoff({"triggers": ["unknown", "conflict"], "target": {"kind": "queue", "name": "q"}},
                              {"unknown", "conflict", "no-match"}, True)
        self.assertEqual({"state": "requested", "triggeredBy": ["conflict", "exception-escalation", "unknown"]}, handoff)
        self.assertEqual({"state": "requested", "triggeredBy": ["exception-escalation"]}, ev._handoff(None, {"exception-escalation"}, True))
        self.assertEqual({"state": "none"}, ev._handoff(None, {"no-match"}, False))
        routes = {"triggers": ["unknown", "conflict"],
                  "routes": [{"target": {"kind": "queue", "name": "a"}, "triggers": ["conflict"]}]}
        self.assertEqual({"state": "none", "routes": []}, ev._handoff(routes, {"unknown"}, False))
        self.assertEqual({"state": "none", "routes": []}, ev._handoff(routes, {"no-match"}, False))
        self.assertEqual({"state": "requested", "triggeredBy": ["conflict", "unknown"],
                          "routes": [{"kind": "queue", "name": "a"}]}, ev._handoff(routes, {"unknown", "conflict"}, False))


class RulesNoRowExercisesTest(unittest.TestCase):
    """Rules of Core §§7-8 that no evaluation row distinguishes (the mutation check of
    this evaluator found each one surviving every row). These cases are this module's own, written
    from the text like the evaluator: they guard it against regression and are not conformance rows,
    so they add no independent check of a reading."""

    FACTS = {"request": {"kind": "intake", "tier": "tier-3", "flagged": False}}
    REQUESTED = {"state": "requested", "triggeredBy": ["unknown"]}

    def variant(self, change: Any) -> dict[str, Any]:
        pack = load(ROWS / "packs" / "inert-baseline.json")
        change(pack)
        return pack

    def disposition_of(self, pack: dict[str, Any], facts: Any, evidence: Any = None) -> str:
        result = ev.evaluate(ev.dump_json(pack), facts, evidence)
        self.assertIsNotNone(result.disposition, result.detail)
        return ev.canonical(result.disposition)

    def expect(self, kind: str, reasons: list[str], handoff: dict[str, Any], outcome: str | None = None) -> str:
        value: dict[str, Any] = {"kind": kind, "reasons": reasons, "handoff": handoff}
        if outcome is not None:
            value["outcomeId"] = outcome
        return ev.canonical(value)

    @staticmethod
    def exception(effect: str, **members: Any) -> dict[str, Any]:
        name = "-".join(["exception", effect, *[str(value) for value in members.values()]])
        return {"id": name, "description": "An exception.",
                "when": {"op": "literal", "value": True}, "effect": effect, "onUnknown": "ignore", **members}

    @staticmethod
    def receipt(pack: dict[str, Any], required: bool) -> None:
        pack["evidenceRequirements"] = [{"id": "receipt", "description": "A receipt.", "required": required}]

    def test_a_suppressed_rule_is_not_evaluated(self) -> None:  # Core §8 steps 4 and 6
        facts = {"request": {"kind": "intake", "tier": "tier-1", "flagged": True}}
        pack = self.variant(lambda p: p.update(exceptions=[self.exception("suppress-rule", targetRule="flagged")]))
        self.assertEqual(self.expect("outcome", [], {"state": "none"}, "accept"), self.disposition_of(pack, facts))

    def test_forced_outcomes_that_differ_conflict(self) -> None:  # Core §8 steps 4 and 5
        pack = self.variant(lambda p: p.update(exceptions=[self.exception("force-outcome", outcome="accept"),
                                                            self.exception("force-outcome", outcome="refer")]))
        self.assertEqual(self.expect("unresolved", ["conflict"], {"state": "requested", "triggeredBy": ["conflict"]}),
                         self.disposition_of(pack, self.FACTS))

    def test_missing_evidence_stops_before_the_rules(self) -> None:  # Core §8 steps 2 and 5
        pack = self.variant(lambda p: self.receipt(p, True))
        facts = {"request": {"kind": "intake", "flagged": False}}  # the escalate rule would be unknown
        self.assertEqual(self.expect("unresolved", ["missing-required-evidence"], {"state": "none"}),
                         self.disposition_of(pack, facts, {"receipt": "absent"}))

    def test_an_omitted_evidence_key_is_unknown(self) -> None:  # Core §8.2, §8 step 2
        pack = self.variant(lambda p: self.receipt(p, True))
        self.assertEqual(self.expect("unresolved", ["unknown"], self.REQUESTED), self.disposition_of(pack, self.FACTS, {}))
        self.assertEqual(self.expect("unresolved", ["unknown"], self.REQUESTED), self.disposition_of(pack, self.FACTS))

    def test_evidence_recorded_absent_is_false(self) -> None:  # Core §7.5
        def change(pack: dict[str, Any]) -> None:
            self.receipt(pack, False)
            pack["rules"][1]["when"] = {"op": "not", "condition": {"op": "evidence-present", "evidenceRequirement": "receipt"}}
        pack = self.variant(change)
        self.assertEqual(self.expect("outcome", [], {"state": "none"}, "refer"),
                         self.disposition_of(pack, self.FACTS, {"receipt": "absent"}))

    def test_an_unknown_rule_that_ignores_does_not_block(self) -> None:  # Core §8 steps 7 and 10
        facts = {"request": {"kind": "intake", "tier": "tier-3"}}
        no_match = self.expect("unresolved", ["no-match"], {"state": "requested", "triggeredBy": ["no-match"]})
        self.assertEqual(no_match, self.disposition_of(self.variant(lambda p: None), facts))
        with_fallback = self.variant(lambda p: p.update(fallbackOutcome="refer"))
        self.assertEqual(self.expect("outcome", [], {"state": "none"}, "refer"), self.disposition_of(with_fallback, facts))

    def test_three_valued_all_any_and_not(self) -> None:  # Core §§7.1-7.3
        unknown = {"op": "fact", "path": "/request/missing", "operator": "equals", "value": True}
        false = {"op": "literal", "value": False}
        true = {"op": "literal", "value": True}
        for when, expected in [({"op": "all", "conditions": [unknown, false]}, "no-match"),
                               ({"op": "any", "conditions": [unknown, true]}, "accept"),
                               ({"op": "not", "condition": unknown}, "unknown")]:
            with self.subTest(op=when["op"]):
                pack = self.variant(lambda p: p["rules"][0].update(when=when))
                if expected == "accept":
                    wanted = self.expect("outcome", [], {"state": "none"}, "accept")
                else:
                    wanted = self.expect("unresolved", [expected], {"state": "requested", "triggeredBy": [expected]})
                self.assertEqual(wanted, self.disposition_of(pack, self.FACTS))

    def test_an_ordered_comparison_over_a_non_decimal_string_is_unknown(self) -> None:  # Core §7.4
        when = {"op": "fact", "path": "/request/amount", "operator": "greater-than", "value": "100"}
        pack = self.variant(lambda p: p["rules"][0].update(when=when))
        for amount in ("1e3", " 1000", "+1000", "1000."):
            with self.subTest(amount=amount):
                facts = {"request": {"kind": "intake", "amount": amount, "flagged": False}}
                self.assertEqual(self.expect("unresolved", ["unknown"], self.REQUESTED), self.disposition_of(pack, facts))

    def test_a_reference_reads_the_set_it_names(self) -> None:  # Core §§7.4, 8.5
        def change(pack: dict[str, Any]) -> None:
            pack["valueSets"] = [{"id": "other", "entries": [{"value": "tier-9"}]},
                                 {"id": "priority", "entries": [{"value": "tier-2"}, {"value": "tier-3"}]}]
            when = pack["rules"][0]["when"]
            del when["value"]
            when["valueSet"] = "priority"
        self.assertEqual(self.expect("outcome", [], {"state": "none"}, "accept"),
                         self.disposition_of(self.variant(change), self.FACTS))

    def test_an_unreferenced_set_costs_no_work(self) -> None:  # Core §§6.9, 10
        bare = ev.evaluate(ev.dump_json(self.variant(lambda p: None)), self.FACTS)
        entries = [{"value": f"code-{i}"} for i in range(512)]
        unreferenced = self.variant(lambda p: p.update(valueSets=[{"id": "unused", "entries": entries}]))
        self.assertEqual(bare.work, ev.evaluate(ev.dump_json(unreferenced), self.FACTS).work)


if __name__ == "__main__":
    unittest.main()

"""Dialect format 4.0.0 (spec/dialect.md §2.2, proposed): the hand-written rows and the end-to-end vectors
under conformance/dialect/format-4/, the bounds and refusals, and the formats before it unchanged.

The expected answers are hand-written, never recorded from the reader under test; the distances among them
were computed by tools/dialect_builtins_reference.py, another method on the same sphere."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from test_dialect import READER, RFC_8032_TEST_1, ROOT, signer

FORMAT_4 = ROOT / "conformance" / "dialect" / "format-4"
ID = "urn:judgmentpack:dialect:format-4-vectors"


class Literal(str):
    """A number as its literal, so that `-0` and `99.5` reach the reader as written."""


def load(text: str) -> Any:
    return json.loads(text, parse_int=Literal, parse_float=Literal)


def dump(value: Any) -> str:
    if isinstance(value, Literal):
        return str(value)
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(k) + ":" + dump(v) for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ",".join(dump(v) for v in value) + "]"
    return json.dumps(value)


def resolved(facts: list[dict[str, Any]], reason: str) -> dict[str, Any]:
    return {"claim": {"facts": facts, "evidence": {}, "acquisitionStatus": "resolved"}, "reason": reason}


def dialect_of(row: dict[str, Any], clauses: list[dict[str, Any]] | None) -> dict[str, Any]:
    """The rows' frame (format-4/README.md): one case with no source, its copy empty, its rule the row's
    `rule`, or one the row's `when` or `expectedDerived` gives, declaring every case parameter and runAt."""
    if "dialect" in row:
        return row["dialect"]
    if clauses is None:
        rule = row["rule"]
    else:
        declared = {name: d["type"] for name, d in row.get("parameters", {}).items()}
        rule = {"ruleVersion": "2.0.0", "parameters": {**declared, "runAt": "timestamp"}}
        if "derived" in row:
            rule["derived"] = row["derived"]
        rule["clauses"] = clauses
    case: dict[str, Any] = {"facts": [], "evidence": [], "rule": rule}
    if row.get("parameters"):
        case = {"parameters": row["parameters"], **case}
    return {"formatVersion": "4.0.0", "id": ID, "version": "0.1.0", "case": case}


def run(document: dict[str, Any], case: Any, verified_at: str) -> Any:
    return READER.verify(
        dump(document).encode("utf-8"),
        dump(case).encode("utf-8"),
        b"{}",
        b"[]",
        json.dumps({"verifiedAt": verified_at}).encode("utf-8"),
    )


def rule_of(result: Any) -> dict[str, Any]:
    """The case outcome's `rule` of the recomputed preparation: the rows give a placeholder preparation, so
    every reading ends `preparation-differs` with the recomputed preparation kept."""
    assert result.answer.get("finding") == "preparation-differs", result.answer
    preparation = load(result.preparation.decode("utf-8"))
    return preparation["outcomes"][0]["rule"]


ALWAYS = {"op": "always"}


class FormatFourRowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = load((FORMAT_4 / "vectors.json").read_text(encoding="utf-8"))
        self.verified_at = self.document["verifiedAt"]

    def answer(self, row: dict[str, Any], clauses: list[dict[str, Any]] | None) -> Any:
        return run(dialect_of(row, clauses), row.get("case", {}), self.verified_at)

    def assert_not_read(self, row: dict[str, Any], result: Any) -> bool:
        if "expectedRefusal" in row:
            self.assertEqual({"refused": row["expectedRefusal"]}, {"refused": result.answer.get("refused")}, result.answer)
            return True
        if "expectedFinding" in row:
            self.assertEqual(row["expectedFinding"], result.answer.get("finding"), result.answer)
            return True
        return False

    def test_every_row(self) -> None:
        ids = [row["id"] for row in self.document["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        for row in self.document["cases"]:
            with self.subTest(row=row["id"]):
                if "expectedDerived" in row:
                    self.derived_row(row)
                elif "when" in row:
                    clauses = [
                        {**resolved([{"pointer": "/matched", "value": True}], "true"), "when": row["when"]},
                        {**resolved([{"pointer": "/matched", "value": False}], "false"), "when": ALWAYS},
                    ]
                    result = self.answer(row, clauses)
                    if self.assert_not_read(row, result):
                        continue
                    rule = rule_of(result)
                    self.assertEqual({"matched": row["expected"]}, rule["claim"]["facts"])
                    self.assertEqual("true" if row["expected"] else "false", rule["reason"])
                    if "expectedBasis" in row:
                        self.assertEqual(row["expectedBasis"], rule["claim"]["basis"])
                else:
                    result = self.answer(row, None)
                    if self.assert_not_read(row, result):
                        continue
                    claim = rule_of(result)["claim"]
                    for name, expected in row["expectedClaim"].items():
                        self.assertEqual(expected, claim[name], name)

    def derived_row(self, row: dict[str, Any]) -> None:
        # Each derived value the row names, by itself: copied when it has a value, and none otherwise.
        for name, expected in row["expectedDerived"].items():
            clauses = [
                {**resolved([{"pointer": "/value", "derived": name}], "some"), "when": {"op": "exists", "derived": name}},
                {**resolved([], "none"), "when": ALWAYS},
            ]
            rule = rule_of(self.answer(row, clauses))
            if expected is None:
                self.assertEqual(("none", {}), (rule["reason"], rule["claim"]["facts"]), name)
            else:
                self.assertEqual(("some", {"value": expected}), (rule["reason"], rule["claim"]["facts"]), name)


INPUTS = ("dialect.json", "case.json", "sources.json", "profiles.json", "preparation.json")


class FormatFourVectorTests(unittest.TestCase):
    def test_the_end_to_end_vectors(self) -> None:
        manifest = json.loads((FORMAT_4 / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(["case-rule-no-sources", "source-rule"], [entry["name"] for entry in manifest["cases"]])
        for entry in manifest["cases"]:
            directory = FORMAT_4 / entry["name"]
            self.assertEqual(sorted(entry["files"]), sorted(p.name for p in directory.iterdir()))
            files = {name: (directory / name).read_bytes() for name in entry["files"]}
            for name, sha in entry["files"].items():
                self.assertEqual(sha, hashlib.sha256(files[name]).hexdigest(), name)
            dialect = READER.read_document(files["dialect.json"], "dialect")
            self.assertEqual(files["dialect.canonical.json"], READER.canon(dialect))
            self.assertEqual(entry["dialectDigest"], READER.digest_of(READER.canon(dialect)))
            if "readDigest" in entry:
                parsed = READER.parse_dialect(dialect)
                self.assertEqual(files["case-read.canonical.json"], READER.canon(parsed.case_read.as_written))
                self.assertEqual(entry["readDigest"], READER.digest_of(files["case-read.canonical.json"]))
            result = READER.verify(*(files[name] for name in INPUTS))
            self.assertEqual(entry["preparationDigest"], result.digest)
            self.assertEqual(entry["expectedReport"], json.loads(READER.preparation_bytes(READER.report(result.answer))))
            # the given preparation is written in its canonical form (§9.5)
            self.assertEqual(files["preparation.json"], READER.preparation_bytes(READER.read_document(files["preparation.json"], "p")))
            preparation = json.loads(files["preparation.json"])
            if "expectedOutcomes" in entry:
                self.assertEqual(entry["expectedOutcomes"],
                                 {o["name"]: [o["status"], o["reason"]] for o in preparation["outcomes"]})
            if "expectedDerivations" in entry:
                # §2.2.6: every entry of a target of a rule of version 2.0.0 carries `derivation`, a skipped
                # source's among them; an entry of a copy carries none
                derivations: dict[str, dict[str, Any]] = {name: {} for name in entry["expectedDerivations"]}
                for line in preparation["lineage"]:
                    if "derivation" in line:
                        derivations[line["source"]][line["target"]] = line["derivation"]
                self.assertEqual(entry["expectedDerivations"], derivations)
            with mock.patch.object(READER, "READ_FORMATS", ("2.0.0", "3.0.0")):
                refused = READER.verify(*(files[name] for name in INPUTS))
            self.assertEqual(entry["expectedReportOfAReaderThatDoesNotReadTheFormat"],
                             json.loads(READER.preparation_bytes(READER.report(refused.answer))))

    def test_the_end_to_end_vector_under_another_parameter_or_time(self) -> None:
        directory = FORMAT_4 / "case-rule-no-sources"
        inputs = {name: (directory / name).read_bytes() for name in
                  ("dialect.json", "case.json", "sources.json", "profiles.json", "preparation.json")}
        # The parameter values are committed through the case outcome's `parameters` (§2.2.6): another
        # limit, which the rule still passes, gives another preparation.
        case = json.loads(inputs["case.json"])
        case["settings"]["maxSpeed"] = 250001
        result = READER.verify(inputs["dialect.json"], json.dumps(case).encode(), inputs["sources.json"],
                               inputs["profiles.json"], inputs["preparation.json"])
        self.assertEqual("preparation-differs", result.answer.get("finding"))
        self.assertEqual(250001, json.loads(result.preparation)["outcomes"][0]["parameters"]["maxSpeed"])
        # an address outside every range takes the second clause
        case = json.loads(inputs["case.json"])
        case["current"]["address"] = "2001:db9::7"
        result = READER.verify(inputs["dialect.json"], json.dumps(case).encode(), inputs["sources.json"],
                               inputs["profiles.json"], inputs["preparation.json"])
        rule = json.loads(result.preparation)["outcomes"][0]["rule"]
        self.assertEqual(("implausible", {"signIn": {"plausible": False}}), (rule["reason"], rule["claim"]["facts"]))
        lineage = {e["target"]: e for e in json.loads(result.preparation)["lineage"]}
        self.assertEqual({"by": "none"}, lineage["/signIn/distanceMm"]["derivation"])
        self.assertFalse(lineage["/signIn/distanceMm"]["present"])
        self.assertNotIn("derivation", lineage["/request/id"])


def source_rule(result: Any = None, dialect: Any = None, profiles: Any = None) -> list[bytes]:
    """The source vector's inputs changed: each acquisition's result, the dialect or the profiles, then every
    profileDigest set to its profile's and each receipt committed to its result again and signed under the
    vector's key, RFC 8032 section 7.1 TEST 1's published seed (source-rule/ in format-4/README.md)."""
    directory = FORMAT_4 / "source-rule"
    document = json.loads((directory / "dialect.json").read_bytes())
    acquisitions = json.loads((directory / "sources.json").read_bytes())
    trusted = json.loads((directory / "profiles.json").read_bytes())
    for change, value in ((dialect, document), (profiles, trusted)):
        if change is not None:
            change(value)
    for name, member in acquisitions.items():
        if result is not None:
            result(name, member["response"]["result"])
    seed, public = RFC_8032_TEST_1
    _, sign = signer(bytes.fromhex(seed))
    digests = {p["id"]: READER.digest_of(READER.canon(READER.read_document(json.dumps(p).encode(), "p"))) for p in trusted}
    for source in document["sources"]:
        source["profileDigest"] = digests[source["profile"]]
    for member in acquisitions.values():
        receipt = member["response"]["receipt"]
        changed = READER.read_document(json.dumps(member["response"]["result"]).encode(), "result")
        receipt["resultDigest"] = READER.digest_of(READER.canon(changed))
        receipt["keyId"] = hashlib.sha256(bytes.fromhex(public)).hexdigest()[:32]
        del receipt["signature"]
        message = b"judgment-pack-gateway/receipt/3:" + READER.canon(READER.read_document(json.dumps(receipt).encode(), "r"))
        receipt["signature"] = sign(message).hex()
    return [json.dumps(document).encode(), (directory / "case.json").read_bytes(), json.dumps(acquisitions).encode(),
            json.dumps(trusted).encode(), (directory / "preparation.json").read_bytes()]


class FormatFourSourceTests(unittest.TestCase):
    def answer(self, inputs: list[bytes]) -> Any:
        return READER.verify(*inputs)

    def test_the_vector_signed_again_unchanged_is_still_read(self) -> None:
        # the helper's own control: signed again with no change, the vector still reads
        self.assertIn("reading", self.answer(source_rule()).answer)

    def test_a_source_list_parameter_at_and_over_its_bounds(self) -> None:
        # §2.2.7: a source parameter's elements and their bytes are measured when it takes its value, from
        # the claim of the source it comes from, before its type is checked
        for tags, expected in (
            (["a"] * 1024, "preparation-differs"),
            (["a"] * 1025, "input-over-bound"),
            (["é" * 512], "preparation-differs"),
            (["é" * 512 + "a"], "input-over-bound"),
            (["a"] * 1024 + [1], "input-over-bound"),
            (["a"] * 1023 + [1], "parameter-invalid"),
        ):
            def change(name: str, result: dict[str, Any], tags: list[Any] = tags) -> None:
                result["tags"] = tags
            with self.subTest(count=len(tags), first=tags[0]):
                answer = self.answer(source_rule(change)).answer
                self.assertEqual(expected, answer.get("refused") or answer.get("finding"), answer)

    def test_a_calculator_that_did_not_compute_writes_derivation_none(self) -> None:
        # §2.2.6: a read that was not applied writes none of its targets, each `{"by": "none"}`, the
        # requirement the calculator's answer marks `unknown` included
        calculator = {"name": "review-window", "version": "1.0.0"}

        def dialect(document: dict[str, Any]) -> None:
            sponsor = document["sources"][1]
            sponsor["profile"] = "calculated-records"
            sponsor["calculation"] = {"inputs": {}, "tables": {}}

        def profiles(trusted: list[dict[str, Any]]) -> None:
            trusted.append({**trusted[0], "id": "calculated-records", "calculator": calculator})

        def result(name: str, value: dict[str, Any]) -> None:
            if name == "sponsor":
                value["calculation"] = {"calculator": calculator, "status": "input-missing", "inputs": {}, "asOf": {}}

        inputs = source_rule(result, dialect, profiles)
        recomputed = json.loads(self.answer(inputs).preparation)
        lineage = {(e["source"], e["target"]): e for e in recomputed["lineage"]}
        self.assertEqual(({"by": "none"}, False), (lineage[("sponsor", "/sponsor/id")]["derivation"],
                                                    lineage[("sponsor", "/sponsor/id")]["present"]))
        self.assertEqual(({"by": "none"}, True), (lineage[("sponsor", "sponsor-endorsement")]["derivation"],
                                                   lineage[("sponsor", "sponsor-endorsement")]["present"]))
        # the source's acquisition still has its derivations
        self.assertEqual({"by": "pointer", "from": "/tags"}, lineage[("intake", "/request/tags")]["derivation"])
        reading = self.answer(inputs[:4] + [READER.preparation_bytes(recomputed)]).answer["reading"]
        # a calculator that did not compute has no unsignedParameters entry (§11)
        self.assertEqual(["intake"], [e["source"] for e in reading["unsignedParameters"]])

    def test_a_repeated_pointer_takes_the_last_entrys_value_and_derivation(self) -> None:
        # §2.2.4: every entry of the match is applied in order, so an earlier `from` is still read; the last
        # entry at a pointer gives its value and its derivation; candidateFrom keeps every `from`
        rule = simple_rule([{"pointer": "/x", "from": "/y"}, {"pointer": "/x", "value": 1}])
        recomputed = json.loads(run(frame(rule), {"y": 2}, "2026-11-12T18:00:00Z").preparation)
        entry = next(e for e in recomputed["lineage"] if e["target"] == "/x")
        self.assertEqual(({"by": "literal"}, ["/y"]), (entry["derivation"], entry["candidateFrom"]))
        self.assertEqual({"x": 1}, recomputed["outcomes"][0]["rule"]["claim"]["facts"])
        rule = simple_rule([{"pointer": "/x", "value": 1}, {"pointer": "/x", "from": "/y"}])
        recomputed = json.loads(run(frame(rule), {"y": 2}, "2026-11-12T18:00:00Z").preparation)
        entry = next(e for e in recomputed["lineage"] if e["target"] == "/x")
        self.assertEqual({"by": "pointer", "from": "/y"}, entry["derivation"])


def frame(rule: dict[str, Any], parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    case: dict[str, Any] = {"facts": [], "evidence": [], "rule": rule}
    if parameters:
        case = {"parameters": parameters, **case}
    return {"formatVersion": "4.0.0", "id": ID, "version": "0.1.0", "case": case}


def simple_rule(facts: list[dict[str, Any]], derived: list[dict[str, Any]] | None = None,
                parameters: dict[str, str] | None = None) -> dict[str, Any]:
    rule: dict[str, Any] = {"ruleVersion": "2.0.0", "parameters": parameters or {}}
    if derived is not None:
        rule["derived"] = derived
    rule["clauses"] = [{**resolved(facts, "r"), "when": ALWAYS}]
    return rule


def duration(name: str) -> dict[str, Any]:
    return {"name": name, "builtin": "duration", "from": {"field": "/a"}, "to": {"field": "/b"}}


class FormatFourBoundTests(unittest.TestCase):
    def refusal(self, document: dict[str, Any], case: Any = None) -> Any:
        result = run(document, {} if case is None else case, "2026-11-12T18:00:00Z")
        return result.answer.get("refused") or result.answer.get("finding")

    def test_derived_values_at_and_over_the_bound(self) -> None:
        at = frame(simple_rule([{"pointer": "/x", "value": 1}], [duration(f"d{i}") for i in range(16)]))
        self.assertEqual("preparation-differs", self.refusal(at))
        over = frame(simple_rule([{"pointer": "/x", "value": 1}], [duration(f"d{i}") for i in range(17)]))
        self.assertEqual("input-over-bound", self.refusal(over))

    def test_a_literal_at_and_over_the_bound(self) -> None:
        # bytes, not characters: 4096 two-byte characters are at the bound, one more byte is over it
        at = frame(simple_rule([{"pointer": "/x", "value": "é" * 4096}]))
        self.assertEqual("preparation-differs", self.refusal(at))
        over = frame(simple_rule([{"pointer": "/x", "value": "é" * 4096 + "a"}]))
        self.assertEqual("input-over-bound", self.refusal(over))
        # counted in phase 3, before any form: a member the root does not take is not reached
        self.assertEqual("input-over-bound", self.refusal({**over, "unknown": 1}))

    def test_a_list_parameter_at_and_over_the_bounds(self) -> None:
        parameters = {"allowed": {"pointer": "/allowed", "type": "string-list"}}
        document = frame(simple_rule([{"pointer": "/x", "value": 1}], parameters={"allowed": "string-list"}), parameters)
        for allowed, expected in (
            (["a"] * 1024, "preparation-differs"),
            (["a"] * 1025, "input-over-bound"),
            (["é" * 512], "preparation-differs"),
            (["é" * 512 + "a"], "input-over-bound"),
            # measured before the type is checked: a list over its count that is not of strings
            (["a"] * 1024 + [1], "input-over-bound"),
            (["a"] * 1023 + [1], "parameter-invalid"),
        ):
            with self.subTest(count=len(allowed), length=len(allowed[0])):
                self.assertEqual(expected, self.refusal(document, {"allowed": allowed}))
        ranges = {"ranges": {"pointer": "/ranges", "type": "address-range-list"}}
        document = frame(simple_rule([{"pointer": "/x", "value": 1}], parameters={"ranges": "address-range-list"}), ranges)
        self.assertEqual("preparation-differs", self.refusal(document, {"ranges": ["10.0.0.0/8"] * 1024}))
        self.assertEqual("input-over-bound", self.refusal(document, {"ranges": ["10.0.0.0/8"] * 1025}))

    def test_a_decimal_parameter_at_and_over_its_characters(self) -> None:
        parameters = {"t": {"pointer": "/t", "type": "decimal"}}
        document = frame(simple_rule([{"pointer": "/x", "value": 1}], parameters={"t": "decimal"}), parameters)
        self.assertEqual("preparation-differs", self.refusal(document, {"t": "1." + "0" * 126}))
        self.assertEqual("parameter-invalid", self.refusal(document, {"t": "1." + "0" * 127}))

    def test_the_literal_and_the_list_element_take_core_4_1s_base_rows(self) -> None:
        # §2.2.7: a literal takes Core §4.1's row "Dialect text value bytes" and a list element its row
        # "Dialect text-list item bytes", the rows a research text value and text-list item take (§12).
        # The reader takes all four maxima from one table, which holds the `base` column of Core's.
        core = (ROOT / "spec" / "judgment-pack-core.md").read_text(encoding="utf-8")
        table = {}
        for line in core.splitlines():
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if line.startswith("| Dialect ") and len(cells) == 3:
                table[cells[0]] = (cells[1], cells[2])
        self.assertEqual({"Dialect text value bytes": ("8192", "16384"),
                          "Dialect text-list item bytes": ("1024", "2048")},
                         {row: table.get(row) for row in READER.CORE_CEILINGS_BASE})
        self.assertEqual({row: int(table[row][0]) for row in READER.CORE_CEILINGS_BASE}, READER.CORE_CEILINGS_BASE)
        text = READER.CORE_CEILINGS_BASE["Dialect text value bytes"]
        item = READER.CORE_CEILINGS_BASE["Dialect text-list item bytes"]
        self.assertEqual((text, text, item, item), (READER.MAX_LITERAL_BYTES, READER.MAX_TEXT_BYTES,
                                                    READER.MAX_LIST_ELEMENT_BYTES, READER.MAX_ITEM_BYTES))

    def test_a_document_of_the_format_declaring_extended_is_refused_profile_unsupported(self) -> None:
        # §2.2.7 and §2: the reader supports `base` alone, so it refuses a document of the format that declares
        # `extended` in phase 0, before any bound is measured, a literal over base's bound included.
        over = frame(simple_rule([{"pointer": "/x", "value": "é" * 4096 + "a"}]))
        directory = FORMAT_4 / "case-rule-no-sources"
        vector = json.loads((directory / "dialect.json").read_bytes())
        for document in (frame(simple_rule([{"pointer": "/x", "value": 1}])), over, vector):
            with self.subTest(document=sorted(document["case"])):
                result = run({"profile": "extended", **document}, {}, "2026-11-12T18:00:00Z")
                self.assertEqual("profile-unsupported", result.answer.get("refused"), result.answer)
                self.assertEqual({"result": "refusal", "refusal": "profile-unsupported", "profile": "extended"},
                                 READER.report(result.answer))
        # The control: the same documents declaring `base` are read under base's bounds.
        self.assertEqual("preparation-differs", self.refusal({"profile": "base", **frame(simple_rule([{"pointer": "/x", "value": 1}]))}))
        self.assertEqual("input-over-bound", self.refusal({"profile": "base", **over}))

    def test_the_counted_bounds_hold_the_case_rule(self) -> None:
        clauses = [{**resolved([{"pointer": f"/x{i}", "value": 1}], "r"), "when": {"op": "exists", "field": "/x"}}
                   for i in range(64)] + [{**resolved([], "r"), "when": ALWAYS}]
        document = frame({"ruleVersion": "2.0.0", "parameters": {}, "clauses": clauses})
        self.assertEqual("input-over-bound", self.refusal(document))
        listed = {"op": "all", "of": [{"op": "exists", "field": "/x"}] * 65}
        document = frame({"ruleVersion": "2.0.0", "parameters": {},
                          "clauses": [{**resolved([], "r"), "when": listed}, {**resolved([], "r"), "when": ALWAYS}]})
        self.assertEqual("input-over-bound", self.refusal(document))


class FormatFourPhaseTests(unittest.TestCase):
    def end_to_end(self) -> list[bytes]:
        directory = FORMAT_4 / "case-rule-no-sources"
        return [(directory / name).read_bytes() for name in
                ("dialect.json", "case.json", "sources.json", "profiles.json", "preparation.json")]

    def test_a_reader_that_does_not_read_format_4_refuses_it_in_phase_4(self) -> None:
        with mock.patch.object(READER, "READ_FORMATS", ("2.0.0", "3.0.0")):
            self.assertEqual("version-unread", READER.verify(*self.end_to_end()).answer.get("refused"))
            # phase 4 comes before the forms: a malformed document of the format is version-unread too
            dialect = json.loads(self.end_to_end()[0])
            dialect["case"]["rule"]["ruleVersion"] = "1"
            inputs = self.end_to_end()
            inputs[0] = json.dumps(dialect).encode()
            self.assertEqual("version-unread", READER.verify(*inputs).answer.get("refused"))
            # the format's own counts are a reader's of the format: one that does not read it does not
            # take them (§2.2.7)
            dialect["case"]["rule"]["derived"] = [duration(f"d{i}") for i in range(17)]
            inputs[0] = json.dumps(dialect).encode()
            self.assertEqual("version-unread", READER.verify(*inputs).answer.get("refused"))
            # and §12's counts, taken as for format 3.0.0, still come first
            dialect["sources"] = [{}] * 17
            inputs[0] = json.dumps(dialect).encode()
            self.assertEqual("input-over-bound", READER.verify(*inputs).answer.get("refused"))
        # a reader of the format takes its counts in phase 3
        inputs[0] = json.dumps({**dialect, "sources": []}).encode()
        self.assertEqual("input-over-bound", READER.verify(*inputs).answer.get("refused"))

    def test_a_reader_from_before_the_format_refuses_an_unknown_selector(self) -> None:
        many = json.loads(self.end_to_end()[0])
        many["sources"] = [{}] * 17
        with mock.patch.object(READER, "READ_FORMATS", ("2.0.0", "3.0.0")), \
             mock.patch.object(READER, "DEFINED_FORMATS", ("2.0.0", "3.0.0")):
            self.assertEqual("input-malformed", READER.verify(*self.end_to_end()).answer.get("refused"))
            # only once phases 0 to 3 pass (§2.2.7)
            self.assertEqual("input-over-bound", READER.verify(json.dumps(many).encode(),
                                                               *self.end_to_end()[1:]).answer.get("refused"))

    def test_the_preserved_v0_3_0_reader_refuses_the_format_once_phases_0_to_3_pass(self) -> None:
        # The v0.3.0 reader, preserved byte for byte, is one written to the text before this amendment;
        # it imports tools/retained_column.py, which is this tree's.
        path = ROOT / "tests/fixtures/historical-compatibility/v0.3.0/tools/dialect_verify.py"
        spec = importlib.util.spec_from_file_location("dialect_verify_v0_3_0", path)
        old = importlib.util.module_from_spec(spec)
        with mock.patch.object(sys, "path", [str(ROOT / "tools"), *sys.path]), \
             mock.patch.dict(sys.modules, {spec.name: old}):
            spec.loader.exec_module(old)
        refusal = lambda inputs: json.loads(old.preparation_bytes(old.report(old.verify(*inputs).answer)))
        for entry in json.loads((FORMAT_4 / "manifest.json").read_text(encoding="utf-8"))["cases"]:
            with self.subTest(entry["name"]):
                inputs = [(FORMAT_4 / entry["name"] / name).read_bytes() for name in INPUTS]
                self.assertEqual({"refusal": "input-malformed", "result": "refusal"}, refusal(inputs))
                many = json.loads(inputs[0])
                many["sources"] = [{}] * 17
                self.assertEqual({"refusal": "input-over-bound", "result": "refusal"},
                                 refusal([json.dumps(many).encode(), *inputs[1:]]))

    def test_format_3_and_rule_version_1_are_unchanged(self) -> None:
        version_1 = {"ruleVersion": "1", "parameters": {"n": "integer"}, "clauses": [
            {"when": {"op": "freshWithin", "field": "/at", "asOf": "n", "maxAge": "n"},
             "claim": {"facts": [{"pointer": "/x", "from": "/x"}], "evidence": {}, "acquisitionStatus": "resolved"},
             "reason": "fresh"},
            {"when": ALWAYS, "claim": {"facts": [], "evidence": {}, "acquisitionStatus": "unknown"}, "reason": "stale"},
        ]}
        # a source's rule of version 1 reads in format 4.0.0 as before: freshWithin of another type is
        # false, not refused
        for format4 in (False, True):
            read = READER.check_read({"rule": version_1}, {"n": "integer", "runAt": "timestamp"}, "s", format4)
            self.assertEqual("1", read.rule_version)
            claim = READER.rule_claim(read.rule, {"at": "2026-11-12T18:00:00Z", "x": 1}, {"n": READER.Num("5")})
            self.assertEqual("stale", claim["reason"])
        version_2 = READER.read_document(json.dumps(simple_rule([{"pointer": "/x", "value": 1}])).encode(), "rule")
        # rule version 2.0.0 only in format 4.0.0
        with self.assertRaises(READER.Refused):
            READER.check_read({"rule": version_2}, {"runAt": "timestamp"}, "s", False)
        self.assertEqual("2.0.0", READER.check_read({"rule": version_2}, {"runAt": "timestamp"}, "s", True).rule_version)
        # a 3.0.0 document of the end-to-end vector's copy alone keeps its integer preparation version
        document = {"formatVersion": "3.0.0", "id": ID, "version": "0.1.0",
                    "case": {"facts": [{"target": "/x", "source": "/x"}], "evidence": []}}
        result = run(document, {"x": 1}, "2026-11-12T18:00:00Z")
        preparation = json.loads(result.preparation)
        self.assertEqual(3, preparation["version"])
        self.assertNotIn("formatVersion", preparation)
        self.assertNotIn("rule", preparation["outcomes"][0])
        self.assertNotIn("derivation", preparation["lineage"][0])

    def test_the_case_rules_parameters_are_unsigned(self) -> None:
        rule = {"ruleVersion": "2.0.0", "parameters": {"n": "integer", "runAt": "timestamp"},
                "derived": [{"name": "d", "builtin": "duration", "from": {"field": "/a"}, "to": {"param": "runAt"}}],
                "clauses": [{**resolved([{"pointer": "/x", "value": 1}], "r"), "when": ALWAYS}]}
        parameters = {"n": {"pointer": "/n", "type": "integer"}}
        case = {"n": 1, "a": "2026-11-12T18:00:00Z"}

        def reading(document: dict[str, Any]) -> dict[str, Any]:
            computed = run(document, case, "2026-11-12T18:00:00Z").preparation
            return READER.verify(dump(document).encode(), dump(case).encode(), b"{}", b"[]", computed).answer["reading"]

        # runAt, which a derived value reads, is named; n, declared and not read, is not
        self.assertEqual([{"source": "case", "parameters": [{"name": "runAt", "kind": "runAt"}], "targets": 1}],
                         reading(frame(rule, parameters))["unsignedParameters"])
        rule["clauses"] = [{**resolved([], "r"), "when": {"op": "compareParam", "field": "/m", "relation": "less-than", "param": "n"}},
                           {**resolved([{"pointer": "/x", "value": 1}], "r"), "when": ALWAYS}]
        self.assertEqual([{"name": "n", "kind": "case"}, {"name": "runAt", "kind": "runAt"}],
                         reading(frame(rule, parameters))["unsignedParameters"][0]["parameters"])
        # aheadWithin names its asOf and its maxAhead, with no derived value reading runAt
        del rule["derived"]
        rule["clauses"] = [{**resolved([], "r"), "when": {"op": "aheadWithin", "field": "/m", "asOf": "runAt", "maxAhead": "n"}},
                           {**resolved([{"pointer": "/x", "value": 1}], "r"), "when": ALWAYS}]
        self.assertEqual([{"name": "n", "kind": "case"}, {"name": "runAt", "kind": "runAt"}],
                         reading(frame(rule, parameters))["unsignedParameters"][0]["parameters"])
        # a case rule with no target has no entry
        rule["clauses"] = [{**resolved([], "r"), "when": {"op": "compareParam", "field": "/m", "relation": "less-than", "param": "n"}},
                           {**resolved([], "r"), "when": ALWAYS}]
        self.assertNotIn("unsignedParameters", reading(frame(rule, parameters)))


class DistanceReferenceTests(unittest.TestCase):
    def test_the_algorithm_stays_within_a_micrometre_of_the_reference(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("dialect_builtins_reference", ROOT / "tools" / "dialect_builtins_reference.py")
        assert spec is not None and spec.loader is not None
        reference = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reference)
        from fractions import Fraction
        worst = Fraction(0)
        for coordinates in reference.EDGES:
            expected = Fraction(reference.reference_mm(*coordinates))
            worst = max(worst, abs(reference.algorithm_unrounded_mm(READER, coordinates) - expected))
        self.assertLess(worst, Fraction(1, 1000))

    def test_the_series_and_the_arcsine_at_their_ends(self) -> None:
        self.assertEqual(0, READER.sin_scaled(0))
        self.assertEqual(READER.SCALE, READER.cos_scaled(0))
        self.assertEqual(READER.HALF_PI_SCALED, READER.asin_scaled(READER.SCALE))
        self.assertEqual(0, READER.asin_scaled(0))
        self.assertEqual(0, READER.distance_mm(*(READER.Fraction(v) for v in ("0", "0", "0", "0"))))


if __name__ == "__main__":
    unittest.main()

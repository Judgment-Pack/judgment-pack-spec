"""Hand-written RFC 0027 examples, not a Core evaluator/conformance claim or static solver."""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import re
import unittest
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator

from test_repository import pack_conformance_diagnostics

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "rfcs" / "pack-design-advisories"
MISSING = object()
DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")


def load(name):
    return json.loads((FIXTURES / name).read_text())


def select(value, path):
    if not path:
        return value
    for token in path[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict):
            value = value.get(token, MISSING)
        elif isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", token):
            value = value[int(token)] if int(token) < len(value) else MISSING
        else:
            return MISSING
    return value


def equal(left, right):
    # Type preserving: Python's True == 1 must never become JSON equality.
    if type(left) is not type(right):
        if type(left) in (int, float) and type(right) in (int, float):
            return Decimal(str(left)) == Decimal(str(right))
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(equal(a, b) for a, b in zip(left, right))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(equal(left[k], right[k]) for k in left)
    return left == right


def condition(node, supplied):
    op = node["op"]
    if op == "literal":
        return node["value"]
    if op == "not":
        value = condition(node["condition"], supplied)
        return None if value is None else not value
    if op in ("all", "any"):
        values = [condition(child, supplied) for child in node["conditions"]]
        if op == "all":
            return False if False in values else (None if None in values else True)
        return True if True in values else (None if None in values else False)
    if op == "evidence-present":
        return {"present": True, "absent": False, "unknown": None}[
            supplied["evidence"].get(node["evidenceRequirement"], "unknown")
        ]
    if op != "fact":
        raise ValueError("Test harness does not implement extensions")
    value = select(supplied["facts"], node["path"])
    if value is MISSING:
        return None
    operand, operator = node["value"], node["operator"]
    if operator == "equals":
        return equal(value, operand)
    if operator == "not-equals":
        return not equal(value, operand)
    if operator == "in":
        return any(equal(value, item) for item in operand)
    if not all(isinstance(item, str) and DECIMAL.fullmatch(item) for item in (value, operand)):
        return None
    left, right = Decimal(value), Decimal(operand)
    return {"greater-than": left > right, "greater-than-or-equal": left >= right,
            "less-than": left < right, "less-than-or-equal": left <= right}[operator]


def preflight_evidence(pack, supplied):
    """Core §8.2 admits evidence before applicability or any other terminal stage."""
    evidence = supplied["evidence"]
    if not isinstance(evidence, dict):
        raise ValueError("malformed-input: evidence must be an object")
    declared = {row["id"] for row in pack.get("evidenceRequirements", [])}
    if not set(evidence).issubset(declared):
        raise ValueError("malformed-input: evidence contains undeclared IDs")
    if any(not isinstance(value, str) or value not in ("present", "absent", "unknown")
           for value in evidence.values()):
        raise ValueError("malformed-input: invalid evidence availability")


def resolve(pack, supplied):
    """Replay just the Core stages used by these proposal fixtures; never invent a winner."""
    preflight_evidence(pack, supplied)
    rules = pack["rules"]
    result = {"kind": "unresolved", "outcome": None, "reasons": [],
              "candidates": [], "skipped": [], "fallback": False}
    applicable = condition(pack.get("applicability", {"op": "literal", "value": True}), supplied)
    if applicable is not True:
        result.update(kind="not-applicable" if applicable is False else "unresolved",
                      reasons=["not-applicable" if applicable is False else "unknown"],
                      skipped=[rule["id"] for rule in rules])
        return result
    reasons = set()
    presence = [supplied["evidence"].get(row["id"], "unknown")
                for row in pack.get("evidenceRequirements", []) if row["required"]]
    if "absent" in presence:
        reasons.add("missing-required-evidence")
    elif "unknown" in presence:
        reasons.add("unknown")
    active = []
    for row in pack.get("exceptions", []):
        truth = condition(row["when"], supplied)
        if truth is True:
            active.append(row)
        elif truth is None and row["onUnknown"] == "escalate":
            reasons.add("unknown")
    forces = {row["outcome"] for row in active if row["effect"] == "force-outcome"}
    if len(forces) > 1:
        reasons.add("conflict")
    if any(row["effect"] == "escalate" for row in active):
        reasons.add("exception-escalation")
    if reasons:
        result.update(reasons=sorted(reasons), skipped=[row["id"] for row in rules])
        return result
    if forces:
        result.update(kind="outcome", outcome=next(iter(forces)),
                      skipped=[row["id"] for row in rules])
        return result
    suppressed = {row["targetRule"] for row in active if row["effect"] == "suppress-rule"}
    outcomes = set()
    for row in rules:
        if row["id"] in suppressed:
            result["skipped"].append(row["id"])
            continue
        truth = condition(row["when"], supplied)
        if truth is True:
            result["candidates"].append(row["id"])
            outcomes.add(row["outcome"])
        elif truth is None and row["onUnknown"] == "escalate":
            reasons.add("unknown")
    if len(outcomes) > 1:
        reasons.add("conflict")
    if reasons:
        result["reasons"] = sorted(reasons)
    elif outcomes:
        result.update(kind="outcome", outcome=next(iter(outcomes)))
    elif "fallbackOutcome" in pack:
        result.update(kind="outcome", outcome=pack["fallbackOutcome"], fallback=True)
    else:
        result["reasons"] = ["no-match"]
    return result


def reports():
    fixtures = load("reports.json")
    yield "base", "sample-pack.json", fixtures["base"]
    for row in fixtures["variants"]:
        report = copy.deepcopy(fixtures["base"])
        report.update(row["patch"])
        yield row["id"], row.get("packFile", "sample-pack.json"), report


def normalized(result):
    return {key: sorted(value) if isinstance(value, list) else value
            for key, value in result.items()}


class PackDesignAdvisoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load("report.schema.json")
        cls.validator = Draft202012Validator(cls.schema)
        cls.core = Draft202012Validator(json.loads(
            (ROOT / "schema" / "judgment-pack-core.schema.json").read_text()))

    def test_closed_report_schema_and_all_hand_written_controls(self):
        Draft202012Validator.check_schema(self.schema)
        for name, _, report in reports():
            with self.subTest(name=name):
                self.validator.validate(report)
                self.assertLessEqual(report["usage"]["work"], report["limits"]["maxWork"])
                self.assertLessEqual(len(report["findings"]), report["limits"]["maxFindings"])
                self.assertLessEqual(len(json.dumps(report).encode()), 1048576)
                self.assertEqual("0.3.0", report["targetSpecVersion"])

    def test_digest_binding_uses_exact_retained_bytes(self):
        domain_bytes = (FIXTURES / "domain.json").read_bytes()
        for name, pack_file, report in reports():
            with self.subTest(name=name):
                self.assertEqual("sha256:" + hashlib.sha256(domain_bytes).hexdigest(), report["domainDigest"])
                self.assertTrue(equal(json.loads(domain_bytes), report["domain"]))
                pack_bytes = (FIXTURES / pack_file).read_bytes()
                self.assertEqual("sha256:" + hashlib.sha256(pack_bytes).hexdigest(), report["packDigest"])
                self.assertEqual(json.loads(pack_bytes)["specVersion"], report["targetSpecVersion"])
        # Whitespace changes byte identity even when the declared domain is identical.
        self.assertNotEqual(hashlib.sha256(domain_bytes).digest(), hashlib.sha256(domain_bytes + b" ").digest())
        self.assertTrue(equal(json.loads(domain_bytes), json.loads(domain_bytes + b" ")))

    def test_report_domain_witnesses_and_suggestions_pass_evidence_preflight(self):
        for name, pack_file, report in reports():
            pack = load(pack_file)
            supplied_inputs = list(report["domain"]["inputs"])
            for finding in report["findings"]:
                if "witness" in finding:
                    supplied_inputs.append(finding["witness"])
                supplied_inputs.extend(finding.get("suggestedCases", []))
            for index, supplied in enumerate(supplied_inputs):
                with self.subTest(report=name, input=index):
                    preflight_evidence(pack, supplied)

    def test_invalid_evidence_is_refused_before_terminal_resolution(self):
        pack = load("sample-pack.json")
        # Even a false applicability or a compatible force cannot outrun preflight.
        packs = [pack, dict(pack, applicability={"op": "literal", "value": False})]
        facts = {"score": "70", "mode": "medium", "review": False}
        for tested_pack in packs:
            for evidence in ({"not-declared": "present"}, [], {"unused-present": "maybe"}):
                with self.subTest(applicability=tested_pack.get("applicability"), evidence=evidence):
                    with self.assertRaisesRegex(ValueError, "^malformed-input:"):
                        resolve(tested_pack, {"facts": facts, "evidence": evidence})

    def test_examples_are_current_core_documents_without_new_members(self):
        fixtures = load("cases.json")
        packs = [load("sample-pack.json"), load("no-fallback-pack.json")]
        packs += [dict(fixtures["basePack"], **case["patch"]) for case in fixtures["cases"]]
        for index, pack in enumerate(packs):
            with self.subTest(index=index):
                self.assertEqual([], pack_conformance_diagnostics(self.core, pack))
                self.assertNotIn("intentionalFallback", pack)

    def test_three_valued_condition_boundaries(self):
        atom = {"op": "fact", "path": "/x", "operator": "greater-than-or-equal", "value": "70"}
        for value, expected in [("70", True), ("70.00", True), ("69.999", False),
                                (None, None), (70, None), (True, None), ("70 units", None)]:
            with self.subTest(value=value):
                self.assertIs(expected, condition(atom, {"facts": {"x": value}, "evidence": {}}))
        missing = {"facts": {}, "evidence": {}}
        self.assertIsNone(condition({"op": "not", "condition": atom}, missing))
        self.assertIs(False, condition({"op": "all", "conditions": [atom, {"op": "literal", "value": False}]}, missing))
        self.assertIs(True, condition({"op": "any", "conditions": [atom, {"op": "literal", "value": True}]}, missing))
        self.assertFalse(equal(True, 1))
        self.assertFalse(equal("70", "70.00"))
        self.assertTrue(equal(None, None))

    def test_hand_written_resolution_examples_and_permutations(self):
        fixtures = load("cases.json")
        for case in fixtures["cases"]:
            pack = dict(fixtures["basePack"], **case["patch"])
            for rules in itertools.permutations(pack["rules"]):
                for exceptions in itertools.permutations(pack.get("exceptions", [])):
                    reordered = dict(pack, rules=list(rules), exceptions=list(exceptions))
                    with self.subTest(case=case["id"]):
                        self.assertEqual(normalized(case["expected"]), normalized(resolve(reordered, case["input"])))

    def test_proved_report_claims_replay_with_full_gates(self):
        for name, pack_file, report in reports():
            pack = load(pack_file)
            inputs = report["domain"]["inputs"]
            evaluated = [resolve(pack, supplied) for supplied in inputs]
            for finding in report["findings"]:
                with self.subTest(report=name, effect=finding["effect"]):
                    for source in finding["sources"]:
                        entity = select(pack, source["path"])
                        self.assertIsNot(entity, MISSING)
                        if "id" in source:
                            self.assertEqual(source["id"], entity["id"])
                    if finding["certainty"] != "proved":
                        continue
                    effect = finding["effect"]
                    sources = [select(pack, source["path"]) for source in finding["sources"]]
                    if finding["proof"]["method"] == "exhaustive-domain":
                        subject = sources[0]
                        if effect == "condition-never-true":
                            self.assertTrue(all(condition(subject["when"], supplied) is not True for supplied in inputs))
                        elif effect == "never-contributes":
                            self.assertTrue(all(subject["id"] not in row["candidates"] for row in evaluated))
                        elif effect == "outcome-redundancy":
                            matching = [row for row in evaluated if subject["id"] in row["candidates"]]
                            self.assertTrue(matching, "No vacuous redundancy for a dead rule")
                            for row in matching:
                                self.assertTrue(any(other["id"] in row["candidates"] and other["outcome"] == subject["outcome"] for other in sources[1:]))
                        else:
                            self.fail("Unhandled universal hand-written claim")
                        continue
                    supplied = finding["witness"]
                    self.assertTrue(any(equal(supplied, row) for row in inputs))
                    result = resolve(pack, supplied)
                    if effect == "compatible-agreement":
                        self.assertTrue(all(row["id"] in result["candidates"] for row in sources))
                        self.assertEqual(1, len({row["outcome"] for row in sources}))
                    elif effect == "fallback-reachable":
                        self.assertTrue(result["fallback"])
                    elif effect == "no-match-reachable":
                        self.assertEqual(["no-match"], result["reasons"])
                    elif effect == "forced-conflict":
                        self.assertIn("conflict", result["reasons"])
                        self.assertTrue(all(condition(row["when"], supplied) is True for row in sources))
                        self.assertGreater(len({row["outcome"] for row in sources}), 1)
                    elif effect == "force-bypasses-rules":
                        self.assertEqual("outcome", result["kind"])
                        self.assertEqual(sources[0]["outcome"], result["outcome"])
                        self.assertIn(sources[1]["id"], result["skipped"])
                    elif effect == "suppression":
                        self.assertIs(True, condition(sources[0]["when"], supplied))
                        self.assertEqual(sources[1]["id"], sources[0]["targetRule"])
                        self.assertIn(sources[1]["id"], result["skipped"])
                    elif effect == "direct-escalation":
                        self.assertIn("exception-escalation", result["reasons"])
                    elif effect == "unknown-blocks-resolution":
                        self.assertIn("unknown", result["reasons"])
                    else:
                        self.fail("Unhandled existential hand-written claim")

    def test_schema_members_and_enums_have_mutation_sensitive_vectors(self):
        vectors = [report for _, _, report in reports()]
        def visit(node, path=()):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == "properties" and node.get("additionalProperties") is False:
                        for member in value:
                            changed = copy.deepcopy(self.schema)
                            cursor = changed
                            for part in path:
                                cursor = cursor[part]
                            del cursor["properties"][member]
                            validator = Draft202012Validator(changed)
                            self.assertTrue(any(not validator.is_valid(row) for row in vectors), (path, member))
                    elif key == "enum" and "allOf" not in path:
                        for member in value:
                            changed = copy.deepcopy(self.schema)
                            cursor = changed
                            for part in path:
                                cursor = cursor[part]
                            cursor["enum"].remove(member)
                            validator = Draft202012Validator(changed)
                            self.assertTrue(any(not validator.is_valid(row) for row in vectors), (path, member))
                    yield from visit(value, path + (key,))
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    yield from visit(value, path + (index,))
        # Remove declarations from closed objects, not repeated conditional narrowing.
        # Removing an if/then restriction weakens a schema and cannot invalidate a vector.
        list(visit(self.schema))

    def test_adversarial_report_shapes(self):
        base = load("reports.json")["base"]
        mutations = [
            ((), "surprise", True), (("domain",), "surprise", True),
            (("domain", "inputs", 0), "surprise", True),
            (("findings", 0), "surprise", True), (("findings", 0, "proof"), "surprise", True),
            (("findings", 0, "sources", 0), "surprise", True),
            (("limits",), "maxFindings", 257), (("limits",), "maxWork", 100001),
            (("domain",), "inputs", []), (("domain",), "inputs", base["domain"]["inputs"] * 10),
            (("domain", "inputs", 0, "evidence"), "bad", "maybe"),
            (("findings", 0), "certainty", "possible"),
            (("findings", 0), "severity", "error"),
            (("findings", 0), "effect", "forced-conflict"),
            (("findings", 1, "proof"), "method", "witness"),
            (("findings", 0), "sources", [{"path": "/bad~escape"}, {"path": "/rules/1"}]),
            ((), "complete", False), (("usage",), "findingsTruncated", True),
            ((), "packDigest", "sha256:bad"), ((), "fragment", "universal-sat"),
            (("findings", 0), "suggestedCases", [base["domain"]["inputs"][0]] * 17),
        ]
        for path, key, value in mutations:
            mutated = copy.deepcopy(base)
            cursor = mutated
            for part in path:
                cursor = cursor[part]
            cursor[key] = value
            with self.subTest(path=path, key=key):
                self.assertFalse(self.validator.is_valid(mutated))
        possible = next(row for name, _, row in reports() if name == "possible-unsupported-analysis")
        possible["findings"][0]["proof"] = {"method": "exhaustive-domain", "summary": "No sampled counterexample."}
        self.assertFalse(self.validator.is_valid(possible))

    def test_no_sample_based_absence_or_lost_candidate_inference(self):
        fixture = load("cases.json")
        case = next(row for row in fixture["cases"] if row["id"] == "gap-without-fallback")
        pack = dict(fixture["basePack"], **case["patch"])
        self.assertEqual([], resolve(pack, case["input"])["candidates"])
        outside = {"facts": {"score": "70"}, "evidence": {}}
        self.assertEqual(["r-high"], resolve(pack, outside)["candidates"])
        for case_id in ("compatible-force-bypasses-rule", "suppressed-unknown-rule"):
            case = next(row for row in fixture["cases"] if row["id"] == case_id)
            pack = dict(fixture["basePack"], **case["patch"])
            self.assertEqual(["r-normal"], resolve(pack, case["input"])["skipped"])
            self.assertIsNone(condition(pack["rules"][0]["when"], case["input"]))
            self.assertEqual([], resolve(pack, case["input"])["candidates"])

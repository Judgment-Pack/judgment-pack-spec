from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "workflow-1.schema.json"
FIXTURE = ROOT / "conformance" / "workflow"


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def redraw_sample(selection: dict[str, object]) -> list[str]:
    bundle = json.loads((FIXTURE / "left-bundle.json").read_text(encoding="utf-8"))
    stage = next(
        row for row in bundle["stages"] if row["stage"] == selection["upstreamStage"]
    )
    partitions: dict[str, list[tuple[bytes, str]]] = {}
    for row in stage["records"]:
        disposition = row["disposition"]
        if disposition["kind"] != "outcome":
            continue
        record_digest = row["recordDigest"]
        rank = hashlib.sha256(
            selection["seed"].encode("utf-8")
            + b"\x00"
            + record_digest.encode("utf-8")
        ).digest()
        partitions.setdefault(disposition["outcomeId"], []).append((rank, record_digest))
    chosen = {
        record_digest
        for rows in partitions.values()
        for _, record_digest in sorted(rows)[: selection["size"]]
    }
    return [
        row["recordDigest"] for row in stage["records"] if row["recordDigest"] in chosen
    ]


class WorkflowTextTests(unittest.TestCase):
    def test_the_rfcs_specification_is_the_companion_text(self) -> None:
        # As for RFC 0018: numbered companion sections, with RFC headings one level down.
        companion = (ROOT / "spec" / "workflow.md").read_text(encoding="utf-8")
        rfc = (ROOT / "rfcs" / "0020-workflow.md").read_text(encoding="utf-8")
        preface, numbered = companion.split("\n## 1. ", 1)
        self.assertEqual(
            "# The workflow\n\n## Status\n\n"
            "This is the proposed companion text of [RFC 0020](../rfcs/0020-workflow.md), "
            "a Draft. It is\n"
            "normative for nothing. Acceptance would place it beside Core, with the "
            "`workflow-verifier`\n"
            "reader class defined below. No workflow implementation or conformance claim "
            "exists. Section 11's\n"
            "hand-written contract fixture records the bulk forms; the full two-stage run\n"
            "remains a recording requirement, not execution evidence already obtained.\n",
            preface,
        )
        expected = ("## 1. " + numbered).rstrip("\n")
        start = rfc.index("\n### 1. ") + 1
        section = rfc[start : rfc.index("\n## Alternatives")].rstrip("\n")
        promoted = "\n".join(
            line[1:] if line.startswith("##") else line for line in section.splitlines()
        )
        self.assertEqual(expected, promoted)

    def test_bulk_output_and_summary_forms_are_closed(self) -> None:
        companion = (ROOT / "spec" / "workflow.md").read_text(encoding="utf-8")
        section = companion.split("\n## 5. ", 1)[1].split("\n## 6. ", 1)[0]
        unwrapped = section.replace("\n", " ")
        self.assertIn(
            "`{outputRecordVersion: 1, payloadDigest, contributingRule, lineage}`",
            unwrapped,
        )
        self.assertIn(
            "`{summaryVersion: 1, workflowDigest, execution, stage, records, "
            "recordsDigest, byKind, byOutcome, byReason, byRule}`",
            unwrapped,
        )
        self.assertIn("`canon([D1, D2, …, Dn])`", unwrapped)
        self.assertIn("outside the Core §8.3 disposition", unwrapped)
        self.assertIn("absent for a fallback outcome,", unwrapped)
        self.assertIn("`not-applicable` and `unresolved`", unwrapped)
        self.assertIn("`{contributors, fallback}`", unwrapped)

    def test_seeded_sample_form_and_algorithm_are_exact(self) -> None:
        companion = (ROOT / "spec" / "workflow.md").read_text(encoding="utf-8")
        section = companion.split("\n## 6. ", 1)[1].split("\n## 7. ", 1)[0]
        self.assertIn("`{mode: \"sample\", maxSize: N}`", companion)
        self.assertIn("`seed`, `size` and `algorithm`", section)
        self.assertIn('`algorithm` is exactly `"sha256-rank-v1"`', section)
        self.assertIn("`UTF8(seed) || 0x00 || UTF8(recordDigest)`", section)
        self.assertIn("`input-over-bound`", section)
        self.assertIn("`input-malformed`", section)

    def test_execution_carries_summaries_samples_and_resume_state(self) -> None:
        companion = (ROOT / "spec" / "workflow.md").read_text(encoding="utf-8")
        execution = companion.split("\n## 7. ", 1)[1].split("\n## 8. ", 1)[0]
        recovery = companion.split("\n## 8. ", 1)[1].split("\n## 9. ", 1)[0]
        unwrapped = execution.replace("\n", " ")
        self.assertIn(
            "`{executionVersion: 1, workflowDigest, execution, rootCaseDigest, "
            "frozen, instances, outputSets, summaries, selections, samples}`",
            unwrapped,
        )
        self.assertIn("one stage-summary digest per stage", execution)
        self.assertIn("sample-selection digest", execution)
        self.assertIn(
            "complete `summaries` and `samples` arrays", recovery.replace("\n", " ")
        )

    def test_verifier_recomputes_bulk_records_and_reports_drift(self) -> None:
        companion = (ROOT / "spec" / "workflow.md").read_text(encoding="utf-8")
        section = companion.split("\n## 9. ", 1)[1].split("\n## 10. ", 1)[0]
        self.assertIn("`summary-mismatch`", section)
        self.assertIn("`sample-mismatch`", section)
        self.assertIn('refusal: "drift-workflow-mismatch"', section)
        self.assertIn(
            '`{result: "drift", workflowDigest, leftExecutionDigest,', section
        )
        self.assertIn("**drift computation**", section)
        self.assertIn("A stage-delta row is exactly", section)
        self.assertIn("A record-delta row is exactly one of", section)
        self.assertIn("left: null", section)
        self.assertIn("right: null", section)
        self.assertIn("no judgment, verdict or authorization", section)

    def test_two_stage_plan_carries_bulk_and_refusal_vectors(self) -> None:
        companion = (ROOT / "spec" / "workflow.md").read_text(encoding="utf-8")
        section = companion.split("\n## 11. ", 1)[1]
        unwrapped = section.replace("\n", " ")
        self.assertIn("one summary for each stage and one seeded sample", unwrapped)
        self.assertIn("empty, missing, malformed and oversized seeds", unwrapped)
        self.assertIn("a sample size one above the stage's `maxSize`", unwrapped)
        self.assertIn("A second bundle of the same workflow", unwrapped)
        self.assertIn("For every new refusal code, retain a valid expected-report", unwrapped)
        self.assertIn("Interrupted and resumed variants retain", unwrapped)


class WorkflowFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(cls.schema)
        cls.validator = jsonschema.Draft202012Validator(
            cls.schema, format_checker=jsonschema.FormatChecker()
        )
        cls.manifest = json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))
        cls.validator.validate(cls.manifest)

    def test_every_object_schema_is_explicitly_closed(self) -> None:
        def visit(value: object) -> None:
            if isinstance(value, dict):
                if value.get("type") == "object":
                    self.assertIs(value.get("additionalProperties"), False, value)
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(self.schema)

    def test_every_fixture_file_has_its_recorded_schema_result(self) -> None:
        paths = {entry["path"] for entry in self.manifest["files"]}
        actual = {
            str(path.relative_to(FIXTURE))
            for path in FIXTURE.rglob("*.json")
            if path.name != "manifest.json"
        }
        self.assertEqual(paths, actual)
        for entry in self.manifest["files"]:
            with self.subTest(path=entry["path"]):
                value = json.loads((FIXTURE / entry["path"]).read_text(encoding="utf-8"))
                errors = list(self.validator.iter_errors(value))
                self.assertEqual(entry["schemaValid"], not errors)

    def test_recorded_summary_digests_cover_the_ordered_dispositions(self) -> None:
        for name in ("left-bundle.json", "right-bundle.json"):
            bundle = json.loads((FIXTURE / name).read_text(encoding="utf-8"))
            for stage in bundle["stages"]:
                with self.subTest(bundle=name, stage=stage["stage"]):
                    dispositions = [row["disposition"] for row in stage["records"]]
                    self.assertEqual(stage["summary"]["recordsDigest"], digest(dispositions))

    def test_recorded_summaries_are_recomputed_from_output_rows(self) -> None:
        for name in ("left-bundle.json", "right-bundle.json"):
            bundle = json.loads((FIXTURE / name).read_text(encoding="utf-8"))
            for stage in bundle["stages"]:
                by_kind = {"outcome": 0, "not-applicable": 0, "unresolved": 0}
                by_outcome: dict[str, int] = {}
                by_reason: dict[str, int] = {}
                by_rule: dict[str, dict[str, object]] = {}
                for row in stage["records"]:
                    disposition = row["disposition"]
                    by_kind[disposition["kind"]] += 1
                    for reason in disposition["reasons"]:
                        if disposition["kind"] == "unresolved":
                            by_reason[reason] = by_reason.get(reason, 0) + 1
                    if disposition["kind"] == "outcome":
                        outcome = disposition["outcomeId"]
                        by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
                        counts = by_rule.setdefault(
                            outcome, {"contributors": {}, "fallback": 0}
                        )
                        contributor = row["output"].get("contributingRule")
                        if contributor is None:
                            counts["fallback"] = int(counts["fallback"]) + 1
                        else:
                            contributors = counts["contributors"]
                            assert isinstance(contributors, dict)
                            contributors[contributor] = contributors.get(contributor, 0) + 1
                summary = stage["summary"]
                self.assertEqual(summary["records"], len(stage["records"]))
                self.assertEqual(summary["byKind"], by_kind)
                self.assertEqual(summary["byOutcome"], by_outcome)
                self.assertEqual(summary["byReason"], by_reason)
                self.assertEqual(summary["byRule"], by_rule)

    def test_recorded_summary_mismatch_is_caught_by_recomputation(self) -> None:
        vector = json.loads(
            (FIXTURE / "vectors" / "summary-mismatch.json").read_text(encoding="utf-8")
        )
        self.assertEqual(vector["expectedRefusal"], "summary-mismatch")
        self.assertNotEqual(vector["summary"]["recordsDigest"], digest(vector["dispositions"]))

    def test_sample_refusal_vectors_cover_bound_and_seed_form(self) -> None:
        vector_names = (
            "sample-seed-empty.json",
            "sample-seed-invalid.json",
            "sample-seed-missing.json",
            "sample-seed-oversized.json",
            "sample-size-over-bound.json",
        )
        vectors = {
            name: json.loads((FIXTURE / "vectors" / name).read_text(encoding="utf-8"))
            for name in vector_names
        }
        size = vectors["sample-size-over-bound.json"]
        seed = vectors["sample-seed-invalid.json"]
        self.assertEqual(size["expectedRefusal"], "input-over-bound")
        self.assertGreater(size["selection"]["size"], size["stageMaxSize"])
        self.assertEqual(seed["expectedRefusal"], "input-malformed")
        self.assertNotRegex(seed["selection"]["seed"], r"^[0-9a-f]{64}$")
        for name in ("sample-seed-empty.json", "sample-seed-missing.json", "sample-seed-oversized.json"):
            with self.subTest(name=name):
                vector = vectors[name]
                self.assertEqual(vector["expectedRefusal"], "input-malformed")
                self.assertTrue(list(self.validator.iter_errors(vector)))

        for name, vector in vectors.items():
            with self.subTest(repaired=name):
                repaired = dict(vector["selection"])
                if name == "sample-size-over-bound.json":
                    repaired["size"] = vector["stageMaxSize"]
                else:
                    repaired["seed"] = "0" * 64
                self.validator.validate(repaired)
                self.assertLessEqual(repaired["size"], vector["stageMaxSize"])
                self.assertEqual(repaired["selected"], redraw_sample(repaired))

    def test_recorded_sample_is_redrawn_from_seed(self) -> None:
        sample = json.loads((FIXTURE / "sample.json").read_text(encoding="utf-8"))
        self.assertEqual(sample["selected"], redraw_sample(sample))

    def test_drift_is_recomputed_from_the_two_recorded_bundles(self) -> None:
        left = json.loads((FIXTURE / "left-bundle.json").read_text(encoding="utf-8"))
        right = json.loads((FIXTURE / "right-bundle.json").read_text(encoding="utf-8"))
        recorded = json.loads((FIXTURE / "drift.json").read_text(encoding="utf-8"))
        stage_rows = []
        record_rows = []
        self.assertEqual(len(left["stages"]), len(right["stages"]))
        for left_stage, right_stage in zip(left["stages"], right["stages"]):
            left_summary, right_summary = left_stage["summary"], right_stage["summary"]
            dynamic = {}
            for member in ("byOutcome", "byReason"):
                dynamic[member] = {
                    key: right_summary[member].get(key, 0) - left_summary[member].get(key, 0)
                    for key in sorted(set(left_summary[member]) | set(right_summary[member]))
                    if right_summary[member].get(key, 0) != left_summary[member].get(key, 0)
                }
            by_rule = {}
            for outcome in sorted(set(left_summary["byRule"]) | set(right_summary["byRule"])):
                left_rule = left_summary["byRule"].get(outcome, {"contributors": {}, "fallback": 0})
                right_rule = right_summary["byRule"].get(outcome, {"contributors": {}, "fallback": 0})
                contributors = {
                    key: right_rule["contributors"].get(key, 0)
                    - left_rule["contributors"].get(key, 0)
                    for key in sorted(
                        set(left_rule["contributors"]) | set(right_rule["contributors"])
                    )
                    if right_rule["contributors"].get(key, 0)
                    != left_rule["contributors"].get(key, 0)
                }
                fallback = right_rule["fallback"] - left_rule["fallback"]
                if contributors or fallback:
                    by_rule[outcome] = {"contributors": contributors, "fallback": fallback}
            stage_rows.append(
                {
                    "stage": left_stage["stage"],
                    "records": right_summary["records"] - left_summary["records"],
                    "byKind": {
                        key: right_summary["byKind"][key] - left_summary["byKind"][key]
                        for key in ("outcome", "not-applicable", "unresolved")
                    },
                    "byOutcome": dynamic["byOutcome"],
                    "byReason": dynamic["byReason"],
                    "byRule": by_rule,
                }
            )

            def keyed(stage: dict[str, object]) -> dict[tuple[str, int], dict[str, object]]:
                counts: dict[str, int] = {}
                rows = {}
                for row in stage["records"]:  # type: ignore[index]
                    payload = row["output"]["payloadDigest"]
                    counts[payload] = counts.get(payload, 0) + 1
                    rows[(payload, counts[payload])] = row["disposition"]
                return rows

            left_records, right_records = keyed(left_stage), keyed(right_stage)
            for payload, occurrence in sorted(set(left_records) | set(right_records)):
                left_disposition = left_records.get((payload, occurrence))
                right_disposition = right_records.get((payload, occurrence))
                if left_disposition == right_disposition:
                    continue
                change = "added" if left_disposition is None else "removed" if right_disposition is None else "changed"
                record_rows.append(
                    {
                        "change": change,
                        "stage": left_stage["stage"],
                        "payloadDigest": payload,
                        "occurrence": occurrence,
                        "left": left_disposition,
                        "right": right_disposition,
                    }
                )
        self.assertEqual(recorded["stages"], stage_rows)
        self.assertEqual(recorded["records"], record_rows)

    def test_refusal_vectors_have_closed_expected_reports(self) -> None:
        cases = {
            "sample-size-over-bound": "input-over-bound",
            "sample-seed-invalid": "input-malformed",
            "summary-mismatch": "summary-mismatch",
        }
        for name, refusal in cases.items():
            with self.subTest(name=name):
                report = json.loads((FIXTURE / "reports" / f"{name}.json").read_text(encoding="utf-8"))
                self.assertEqual(report, {"result": "refusal", "refusal": refusal})
                self.validator.validate(report)

    def test_fixture_carries_each_bulk_contract_form(self) -> None:
        left = json.loads((FIXTURE / "left-bundle.json").read_text(encoding="utf-8"))
        right = json.loads((FIXTURE / "right-bundle.json").read_text(encoding="utf-8"))
        outputs = [
            row["output"]
            for bundle in (left, right)
            for stage in bundle["stages"]
            for row in stage["records"]
        ]
        self.assertTrue(any("contributingRule" in output for output in outputs))
        self.assertTrue(any("contributingRule" not in output for output in outputs))
        for bundle in (left, right):
            for stage in bundle["stages"]:
                self.assertEqual(
                    {
                        "summaryVersion", "workflowDigest", "execution", "stage", "records",
                        "recordsDigest", "byKind", "byOutcome", "byReason", "byRule",
                    },
                    set(stage["summary"]),
                )
        drift = json.loads((FIXTURE / "drift.json").read_text(encoding="utf-8"))
        self.assertEqual({"changed", "added", "removed"}, {row["change"] for row in drift["records"]})
        self.assertEqual(
            {"reading", "finding", "refusal"},
            {
                json.loads(path.read_text(encoding="utf-8"))["result"]
                for path in (FIXTURE / "reading.json", FIXTURE / "finding.json", FIXTURE / "reports" / "summary-mismatch.json")
            },
        )


if __name__ == "__main__":
    unittest.main()

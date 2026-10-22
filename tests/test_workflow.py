from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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
            "reader class defined below. No workflow implementation, recorded fixture or "
            "conformance claim\n"
            "exists. The two-stage run in §11 is a recording requirement, "
            "not evidence already obtained.\n",
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
        self.assertIn("no judgment, verdict or authorization", section)

    def test_two_stage_plan_carries_bulk_and_refusal_vectors(self) -> None:
        companion = (ROOT / "spec" / "workflow.md").read_text(encoding="utf-8")
        section = companion.split("\n## 11. ", 1)[1]
        unwrapped = section.replace("\n", " ")
        self.assertIn("one summary and one seeded sample for each stage", unwrapped)
        self.assertIn("empty, missing, malformed and oversized seeds", unwrapped)
        self.assertIn("a sample size one above the stage's `maxSize`", unwrapped)
        self.assertIn("A second bundle of the same workflow", unwrapped)
        self.assertIn("For every new refusal code, retain a valid expected-report", unwrapped)
        self.assertIn("Interrupted and resumed variants retain", unwrapped)


if __name__ == "__main__":
    unittest.main()

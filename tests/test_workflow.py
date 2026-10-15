from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WorkflowTextTests(unittest.TestCase):
    def test_the_rfcs_specification_is_the_companion_text(self) -> None:
        # As for RFC 0018: numbered companion sections, with RFC headings one level down.
        companion = (ROOT / "spec" / "workflow.md").read_text(encoding="utf-8")
        rfc = (ROOT / "rfcs" / "0020-workflow.md").read_text(encoding="utf-8")
        expected = companion[companion.index("\n## 1. ") + 1 :].rstrip("\n")
        start = rfc.index("\n### 1. ") + 1
        section = rfc[start : rfc.index("\n## Evidence")].rstrip("\n")
        promoted = "\n".join(
            line[1:] if line.startswith("##") else line for line in section.splitlines()
        )
        self.assertEqual(expected, promoted)


if __name__ == "__main__":
    unittest.main()

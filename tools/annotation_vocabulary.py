"""A reference checker for the proposed annotation vocabulary `1.0.0`.

It was written from the companion text, spec/annotation-vocabulary.md, which RFC 0032 proposes and
which is normative for nothing while that RFC is a Draft. It is the one reader of the vocabulary; no
second, independently written reader exists. What it is not: a product, a conformance claim, or a
source of expectations. The staged rows' expectations were written by hand.

What it does (the section numbers are the companion's):

- Core first (§6.2): the pack is admitted by tools/core_050_eval.py, the repository's second Core
  `0.5.0` evaluator, which supports the `base` profile only. A pack it does not admit as
  semantically conforming is reported `not-checked`, with the Core layer that stopped it, and no
  finding of the vocabulary. Supported extensions play no part.
- The refusal (§6.3): for each outcome whose annotations hold the key `severity`, a value that is
  not one of the four levels, compared by code point, or that is a list, is the finding
  JPS-VOCABULARY-SEVERITY-VALUE at that value. Every refused outcome is reported.
- The advisory (§3.1): an outcome whose value is a level, and whose identifier's last
  hyphen-separated segment is another level, is the advisory JPS-VOCABULARY-SEVERITY-IDENTIFIER at
  its `id`. It changes no result.

Nothing else is read: no other key, no other position, and nothing about evaluation (§2.6).

Usage:
    python tools/annotation_vocabulary.py check PACK
    python tools/annotation_vocabulary.py rows
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    from tools import core_050_eval as core
except ImportError:  # run as a script: tools/ is the script's directory
    import core_050_eval as core  # type: ignore[no-redef]

VOCABULARY = "annotation-vocabulary"
VERSION = "1.0.0"
KEY = "severity"
# §2.2, ascending: the index is the order and nothing else.
LEVELS = ("low", "medium", "high", "critical")
VALUE_CODE = "JPS-VOCABULARY-SEVERITY-VALUE"
IDENTIFIER_CODE = "JPS-VOCABULARY-SEVERITY-IDENTIFIER"

ROOT = core.ROOT
STAGED = ROOT / "conformance" / "annotation-vocabulary" / VERSION


def is_level(value: Any) -> bool:
    """§2.4 and §2.5: one string, equal by code point to a level. No folding, trimming or mapping."""
    return isinstance(value, str) and any(value == level for level in LEVELS)


def check(text: str | bytes) -> dict[str, Any]:
    """The checker's report for one pack (§6.1): result, Core layer, findings and advisories."""
    report: dict[str, Any] = {"vocabulary": VOCABULARY, "version": VERSION}
    admission = core.admit_pack(text)
    if admission.layer is not None:
        report.update(result="not-checked", coreLayer=admission.layer, findings=[], advisories=[])
        return report
    findings: list[dict[str, str]] = []
    advisories: list[dict[str, str]] = []
    for index, outcome in enumerate(admission.pack["outcomes"]):
        annotations = outcome.get("extensions", {}).get(core.ANNOTATIONS)
        if annotations is None or KEY not in annotations:
            continue  # §2.3: no stated severity
        value = annotations[KEY]
        if not is_level(value):
            findings.append({
                "code": VALUE_CODE,
                "path": core.pointer(["outcomes", index, "extensions", core.ANNOTATIONS, KEY]),
            })
            continue  # §3.1: a refused value takes no advisory
        segment = outcome["id"].rsplit("-", 1)[-1]
        if is_level(segment) and segment != value:
            advisories.append({"code": IDENTIFIER_CODE, "path": core.pointer(["outcomes", index, "id"])})
    report.update(result="refused" if findings else "pass", coreLayer=None, findings=findings,
                  advisories=advisories)
    return report


def _pairs(items: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {(item["code"], item["path"]) for item in items}


def run_rows(base: Path = STAGED) -> list[str]:
    """Every staged row and pair against its hand-written expectation; the disagreements."""
    manifest = core.load_json((base / "manifest.json").read_bytes())
    failures: list[str] = []
    for row in manifest["rows"]:
        got = check((base / row["pack"]).read_bytes())
        if (got["result"] != row["expectedResult"]
                or _pairs(got["findings"]) != _pairs(row["expectedFindings"])
                or _pairs(got["advisories"]) != _pairs(row["expectedAdvisories"])):
            failures.append(f"{row['id']}: got {got}")
    for pair in manifest["pairs"]:
        packs = [(base / name).read_bytes() for name in pair["packs"]]
        forms = [core.evaluation_form(core.admit_pack(pack).pack) for pack in packs]
        if not all(core.json_equal(forms[0], form) for form in forms[1:]):
            failures.append(f"{pair['id']}: evaluation forms differ")
        for evaluation in pair["evaluations"]:
            expected = core.canonical(evaluation["expectedDisposition"])
            for name, pack in zip(pair["packs"], packs):
                result = core.evaluate(pack, evaluation["facts"], evaluation["evidenceAvailability"],
                                       evaluation["supportedExtensions"])
                got = core.canonical(result.disposition) if result.disposition is not None else result.error_class
                if got != expected:
                    failures.append(f"{pair['id']}/{evaluation['id']}/{name}: got {got}")
    return failures


def main(argv: list[str]) -> int:
    if argv[:1] == ["check"] and len(argv) == 2:
        report = check(Path(argv[1]).read_bytes())
        print(core.canonical(report))
        return {"pass": 0, "refused": 1}.get(report["result"], 2)
    if argv == ["rows"]:
        failures = run_rows()
        for failure in failures:
            print(failure)
        print(f"annotation-vocabulary {VERSION}: {len(failures)} disagreements")
        return 0 if not failures else 1
    print(__doc__.split("Usage:")[1].rstrip(), file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

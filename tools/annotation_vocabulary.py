"""A reference checker for the proposed annotation vocabulary `1.0.0`.

It was written from the companion text, spec/annotation-vocabulary.md, which RFC 0032 proposes and
which is normative for nothing while that RFC is a Draft. It is the one reader of the vocabulary; no
second, independently written reader exists. What it is not: a product, a conformance claim, or a
source of expectations. The staged rows' expectations were written by hand.

What it does (the section numbers are the companion's):

- The selector, then Core (§6.2): a pack whose `specVersion` is a string other than `0.5.0` is
  reported `not-checked` with the reason `spec-version`, read after only the parsing needed to find
  it. Otherwise the pack is admitted by tools/core_050_eval.py, the repository's second Core `0.5.0`
  evaluator, which supports the `base` profile only. A pack that declares `extended` is reported
  `not-checked` with the reason `profile-unsupported`: not run, not failed. A pack it does not
  admit as semantically conforming is reported `not-checked` with the reason `core-refused` and
  the Core layer that refused it. None of these takes a finding of the vocabulary. Supported
  extensions play no part.
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
SPEC_VERSION = "0.5.0"  # §6.2: the one selector the vocabulary applies to

# §6.2: why the vocabulary was not applied, one of three.
REASON_SELECTOR = "spec-version"
REASON_CORE = "core-refused"
REASON_PROFILE = core.PROFILE_UNSUPPORTED

ROOT = core.ROOT
STAGED = ROOT / "conformance" / "annotation-vocabulary" / VERSION


def is_level(value: Any) -> bool:
    """§2.4 and §2.5: one string, equal by code point to a level. No folding, trimming or mapping."""
    return isinstance(value, str) and any(value == level for level in LEVELS)


def declares_another_selector(text: str | bytes) -> bool:
    """§6.2: a `specVersion` that is a string other than `0.5.0`. A text that does not parse, or a
    missing or non-string `specVersion`, is left to Core, which refuses it."""
    try:
        pack = core.load_json(text)
    except (core.CarrierError, core.LimitError):
        return False
    if not isinstance(pack, dict):
        return False
    selector = pack.get("specVersion")
    return isinstance(selector, str) and selector != SPEC_VERSION


def check(text: str | bytes) -> dict[str, Any]:
    """The checker's report for one pack (§6.1): result, the reason when the vocabulary was not
    applied, the Core layer that refused the pack, findings and advisories."""
    report: dict[str, Any] = {"vocabulary": VOCABULARY, "version": VERSION}
    if declares_another_selector(text):
        report.update(result="not-checked", reason=REASON_SELECTOR, coreLayer=None, findings=[],
                      advisories=[])
        return report
    admission = core.admit_pack(text)
    if admission.layer is not None:
        reason = REASON_PROFILE if admission.layer == "profile" else REASON_CORE
        report.update(result="not-checked", reason=reason,
                      coreLayer=None if reason == REASON_PROFILE else admission.layer,
                      findings=[], advisories=[])
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
    report.update(result="refused" if findings else "pass", reason=None, coreLayer=None,
                  findings=findings, advisories=advisories)
    return report


def _pairs(items: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {(item["code"], item["path"]) for item in items}


def declares_extended(text: str | bytes) -> bool:
    """A row whose pack declares `extended` records a result for a reader that supports it."""
    try:
        pack = core.load_json(text)
    except (core.CarrierError, core.LimitError):
        return False
    return isinstance(pack, dict) and pack.get("profile") == "extended"


def run_rows(base: Path = STAGED) -> tuple[list[str], list[str]]:
    """Every staged row and pair against its hand-written expectation: the disagreements, and the
    rows not run. As in Core's document corpus, a row whose pack declares `extended` is not run by
    this `base`-only checker, which reports it not applied, and that is not a failure."""
    manifest = core.load_json((base / "manifest.json").read_bytes())
    failures: list[str] = []
    not_run: list[str] = []
    for row in manifest["rows"]:
        text = (base / row["pack"]).read_bytes()
        got = check(text)
        if declares_extended(text) and (got["result"], got["reason"]) == ("not-checked", REASON_PROFILE):
            not_run.append(row["id"])
            continue
        if (got["result"] != row["expectedResult"]
                or got["reason"] != row["expectedReason"]
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
    return failures, not_run


def main(argv: list[str]) -> int:
    if argv[:1] == ["check"] and len(argv) == 2:
        report = check(Path(argv[1]).read_bytes())
        print(core.canonical(report))
        return {"pass": 0, "refused": 1}.get(report["result"], 2)
    if argv == ["rows"]:
        failures, not_run = run_rows()
        for failure in failures:
            print(failure)
        for row_id in not_run:
            print(f"{row_id}: not run (profile-unsupported: this checker supports base only)")
        print(f"annotation-vocabulary {VERSION}: {len(failures)} disagreements, {len(not_run)} not run")
        return 0 if not failures else 1
    print(__doc__.split("Usage:")[1].rstrip(), file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

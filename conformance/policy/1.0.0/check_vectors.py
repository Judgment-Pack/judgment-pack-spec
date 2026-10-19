#!/usr/bin/env python3
"""Run the static draft agreement vectors; not a JPS conformance claim."""

import argparse
import json
from pathlib import Path

import verify as v


def source_bytes(source, root):
    if "repeatByte" in source:
        return bytes([source["repeatByte"]]) * source["byteLength"]
    path = v.local_path(root, source["path"], allow_nested=True)
    # Vectors deliberately include one byte over the registration bound.
    return v.read_local(path, v.MAX_ORIGINAL_BYTES + 1)


def case_result(case):
    try:
        raw = source_bytes(case["document"], v.HERE)
    except v.ContractError as error:
        return {"status": "refused", "code": error.code}
    registrations = [(item["content"], item["source"]) for item in case["materials"]]
    return v.verify_input(raw, registrations, load_material=lambda source: source_bytes(source, v.HERE))


def run_vectors(manifest_path=None):
    manifest_path = Path(manifest_path) if manifest_path else v.HERE / "vectors/manifest.json"
    manifest = v.read_json(v.read_local(manifest_path, v.MAX_DOCUMENT_BYTES))
    v.check_schema("vectors", manifest)
    ids, answers = set(), []
    for case in manifest["cases"]:
        v.require(case["id"] not in ids, "invalid-carrier")
        ids.add(case["id"])
        actual = case_result(case)
        answers.append((case["id"], actual, case["expected"]))
    return answers


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, nargs="?")
    args = parser.parse_args(argv)
    try:
        answers = run_vectors(args.manifest)
        failed = [name for name, actual, expected in answers if actual != expected]
        answer = {"status": "mismatch" if failed else "matched", "cases": len(answers), "maturity": "draft"}
        if failed:
            answer["caseIds"] = failed
    except v.ContractError as error:
        answer = {"status": "refused", "code": error.code}
    print(json.dumps(answer, separators=(",", ":")))
    return 0 if answer["status"] == "matched" else 1


if __name__ == "__main__":
    raise SystemExit(main())

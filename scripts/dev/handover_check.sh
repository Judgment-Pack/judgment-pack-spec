#!/usr/bin/env bash
# from judgment-pack-devkit v0.10.0 (lib/handover_check.sh)
set -eu

python3 - <<'PY'
import json, os, subprocess, sys

manifest = json.load(open("dev.json", encoding="utf-8"))
handover = manifest.get("handover", {})
base = os.environ["JPDEV_HANDOVER_BASE"]
if "Boundary change: yes" not in os.environ.get("JPDEV_PR_BODY", "").splitlines():
    for path in handover.get("boundary_paths", []):
        diff = subprocess.check_output(
            ["git", "diff", "--unified=0", base + "...HEAD", "--", path], text=True
        )
        removed = [line for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")]
        if removed:
            print("handover: boundary path has removals: " + path, file=sys.stderr)
            raise SystemExit(1)
probe = handover.get("schema_probe")
if probe:
    subprocess.run(["bash", "-c", probe], check=True)
PY

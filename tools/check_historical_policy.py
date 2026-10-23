#!/usr/bin/env python3
"""Run a byte-frozen Policy RFC tree with its historical Core schema."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_SCHEMA = ROOT / "schema" / "judgment-pack-core-0.2.0-draft.schema.json"
RFC_DIRECTORIES = {
    "prototype": "policy-companion-prototype",
    "contract": "policy-companion-contract",
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in RFC_DIRECTORIES:
        choices = "|".join(RFC_DIRECTORIES)
        print(f"usage: {Path(sys.argv[0]).name} {choices}", file=sys.stderr)
        return 2

    selected = RFC_DIRECTORIES[sys.argv[1]]
    with tempfile.TemporaryDirectory() as directory:
        historical_root = Path(directory)
        schema_directory = historical_root / "schema"
        tools_directory = historical_root / "tools"
        rfcs_directory = historical_root / "rfcs"
        schema_directory.mkdir()
        tools_directory.mkdir()
        rfcs_directory.mkdir()
        shutil.copyfile(
            HISTORICAL_SCHEMA,
            schema_directory / "judgment-pack-core.schema.json",
        )
        shutil.copyfile(ROOT / "tools" / "dialect_verify.py", tools_directory / "dialect_verify.py")
        shutil.copytree(
            ROOT / "rfcs" / "policy-companion-prototype",
            rfcs_directory / "policy-companion-prototype",
        )
        if selected == "policy-companion-contract":
            shutil.copytree(
                ROOT / "rfcs" / selected,
                rfcs_directory / selected,
            )
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                f"rfcs/{selected}",
                "-p",
                "test_*.py",
                "-v",
            ],
            cwd=historical_root,
            check=False,
        )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate and build immutable JPS release bundles from a tagged commit."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?$"
)
BUNDLE_PATHS = (
    "README.md",
    "LICENSE",
    "NOTICE",
    "CHANGELOG.md",
    "VERSIONING.md",
    "TESTING.md",
    "SECURITY.md",
    "spec",
    "schema",
    "examples",
    "conformance",
)


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def release_version(tag: str) -> str:
    if not tag.startswith("v") or not VERSION_PATTERN.fullmatch(tag[1:]):
        raise ValueError("release tag must be an exact SemVer tag with a leading v")
    return tag[1:]


def validate_artifacts(version: str, tag: str, root: Path = ROOT) -> None:
    """Check every version-pinned artifact against the exact release version.

    A claim binds to one exact ``specVersion`` and, for evaluator conformance, to the evaluation
    corpus published with it (Core §§3.4, 3.4.1), so the evaluation manifest is pinned here beside
    the document manifest and the schema.
    """
    manifest = json.loads((root / "conformance" / "manifest.json").read_text("utf-8"))
    evaluation = json.loads(
        (root / "conformance" / "evaluation" / "manifest.json").read_text("utf-8")
    )
    schema = json.loads(
        (root / "schema" / "judgment-pack-core.schema.json").read_text("utf-8")
    )
    if manifest.get("specVersion") != version:
        raise ValueError("release tag does not match the conformance specVersion")
    if evaluation.get("specVersion") != version:
        raise ValueError("release tag does not match the evaluation corpus specVersion")
    if evaluation.get("suiteVersion") != version:
        raise ValueError("release tag does not match the evaluation corpus suiteVersion")
    if schema.get("properties", {}).get("specVersion", {}).get("const") != version:
        raise ValueError("release tag does not match the schema specVersion constant")
    expected_schema_id = (
        f"https://judgmentpack.org/schema/{version}/judgment-pack-core.schema.json"
    )
    if schema.get("$id") != expected_schema_id:
        raise ValueError("schema $id does not point at the exact release version")
    release_notes = root / "releases" / f"{tag}.md"
    if not release_notes.is_file():
        raise ValueError("release notes are missing for the exact tag")


def validate(tag: str, commit: str) -> str:
    """Gate a release on the tree that was actually validated.

    ``validate_artifacts`` reads the worktree while ``build`` archives the resolved commit, so the two
    describe the same release only when ``HEAD`` is that commit. Checking it here is what makes the
    validated tree and the archived tree one tree instead of two that happen to share a tag.
    """
    version = release_version(tag)
    validate_artifacts(version, tag)

    resolved_commit = git("rev-parse", "--verify", f"{commit}^{{commit}}")
    resolved_tag = git("rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")
    if resolved_commit != resolved_tag:
        raise ValueError("release tag does not resolve to the requested commit")
    resolved_head = git("rev-parse", "--verify", "HEAD^{commit}")
    if resolved_head != resolved_commit:
        raise ValueError(
            "release worktree is not checked out at the release commit: "
            f"HEAD is {resolved_head} and {tag} resolves to {resolved_commit}. "
            "The artifacts are validated from the worktree and archived from the commit, so they "
            f"must be the same tree; check out {tag} and run the builder again."
        )
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("tracked release worktree is dirty")
    return version


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build(tag: str, commit: str, output: Path) -> list[Path]:
    version = validate(tag, commit)
    output.mkdir(parents=True, exist_ok=True)
    prefix = f"judgment-pack-spec-{version}/"
    release_note = f"releases/{tag}.md"
    common = (
        "archive",
        f"--prefix={prefix}",
        commit,
        *BUNDLE_PATHS,
        release_note,
    )
    archives = [
        output / f"judgment-pack-spec_{version}_artifacts.tar.gz",
        output / f"judgment-pack-spec_{version}_artifacts.zip",
    ]
    subprocess.run(
        ["git", *common[:1], "--format=tar.gz", f"--output={archives[0]}", *common[1:]],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        ["git", *common[:1], "--format=zip", f"--output={archives[1]}", *common[1:]],
        cwd=ROOT,
        check=True,
    )
    checksums = output / "checksums.txt"
    checksums.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in archives),
        encoding="utf-8",
    )
    return [*archives, checksums]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    artifacts = build(arguments.tag, arguments.commit, arguments.output.resolve())
    for artifact in artifacts:
        print(f"{artifact.name}: {artifact.stat().st_size} bytes")


if __name__ == "__main__":
    main()

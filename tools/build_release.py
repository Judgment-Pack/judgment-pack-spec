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

POLICY_FORMAT = "1.0.0"
POLICY_ROOT = "conformance/policy/1.0.0"
POLICY_SCHEMA_ROOT = "schema/policy/1.0.0"
POLICY_TAG_PATTERN = re.compile(
    r"policy-v((?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"-draft\.(?:0|[1-9][0-9]*))"
)
POLICY_FORMAT_PATHS = (
    "spec/policy.md",
    *tuple(f"{POLICY_SCHEMA_ROOT}/{name}.schema.json"
           for name in ("common", "policy", "governing-adoption")),
    f"{POLICY_SCHEMA_ROOT}/consumer-core-0.2.0-draft.schema.json",
    f"{POLICY_ROOT}/fixture.schema.json",
    f"{POLICY_ROOT}/vectors.schema.json",
    f"{POLICY_ROOT}/vectors/README.md",
)
POLICY_BUNDLE_PATHS = (
    "LICENSE", "NOTICE", "VERSIONING.md", "GOVERNANCE.md", "CONTRIBUTING.md",
    "requirements-dev.txt", "spec/policy.md", "spec/dialect.md",
    "spec/checkpoint-witness.md", POLICY_SCHEMA_ROOT, POLICY_ROOT,
    "schema/judgment-pack-core.schema.json", "tools/dialect_verify.py",
    "rfcs/0000-rfc-process.md", "rfcs/0023-policy-companion.md",
    "rfcs/policy-companion-prototype", "rfcs/policy-companion-contract",
)


def is_policy_tag(tag: str) -> bool:
    return POLICY_TAG_PATTERN.fullmatch(tag) is not None


def validate_policy_artifacts(version: str, tag: str, root: Path = ROOT) -> None:
    """Gate only the independently versioned, draft Policy companion surface."""
    manifest_path = root / "releases" / f"{tag}.json"
    if not manifest_path.is_file():
        raise ValueError("Policy release manifest is missing for the exact tag")
    release = json.loads(manifest_path.read_text("utf-8"))
    expected_keys = {"companion", "releaseVersion", "tag", "maturity", "formatVersion",
                     "consumerSpecVersions", "schemas", "corpus", "formatDigests"}
    if set(release) != expected_keys:
        raise ValueError("Policy release manifest has an invalid closed shape")
    if (release["companion"] != "policy" or release["releaseVersion"] != version
            or release["tag"] != tag or release["maturity"] != "draft"
            or release["formatVersion"] != POLICY_FORMAT
            or release["consumerSpecVersions"] != ["0.2.0-draft"]):
        raise ValueError("Policy release identity, maturity or format does not match")
    expected_schemas = {name: f"https://judgmentpack.org/schema/policy/{POLICY_FORMAT}/{name}.schema.json"
                        for name in ("common", "policy", "governing-adoption", "fixture", "vectors")}
    if release["schemas"] != expected_schemas:
        raise ValueError("Policy release schema identities do not match the exact format")
    for name, identity in expected_schemas.items():
        directory = POLICY_SCHEMA_ROOT if name in ("common", "policy", "governing-adoption") else POLICY_ROOT
        schema = json.loads((root / directory / f"{name}.schema.json").read_text("utf-8"))
        if schema.get("$id") != identity:
            raise ValueError("Policy schema $id differs from its immutable format identity")
    digests = release["formatDigests"]
    if not isinstance(digests, dict) or set(digests) != set(POLICY_FORMAT_PATHS):
        raise ValueError("Policy format digest inventory does not match")
    if any(value != "sha256:" + sha256(root / path) for path, value in digests.items()):
        raise ValueError("Policy format bytes differ from the release manifest")
    # Reusing an exact selector cannot revise published meaning or its resource URLs.
    for previous_path in (root / "releases").glob("policy-v*.json"):
        if previous_path == manifest_path:
            continue
        previous = json.loads(previous_path.read_text("utf-8"))
        if previous.get("formatVersion") == POLICY_FORMAT:
            if (previous.get("formatDigests") != digests
                    or previous.get("schemas") != expected_schemas
                    or previous.get("consumerSpecVersions") != release["consumerSpecVersions"]
                    or previous.get("corpus") != release["corpus"]):
                raise ValueError("Policy exact format identity conflicts with an earlier release record")
    corpus_path = f"{POLICY_ROOT}/vectors/manifest.json"
    manifest = json.loads((root / corpus_path).read_text("utf-8"))
    if release["corpus"] != {"path": corpus_path, "sha256": "sha256:" + sha256(root / corpus_path), "cases": 124,
                                "files": policy_corpus_digests(root)}:
        raise ValueError("Policy corpus identity or count does not match")
    if (manifest.get("maturity") != "draft" or manifest.get("vectorSuiteVersion") != "1"
            or len(manifest.get("cases", [])) != 124):
        raise ValueError("Policy corpus selector, maturity or rows do not match")
    rfc = (root / "rfcs/0023-policy-companion.md").read_text("utf-8")
    if not re.search(r"^- Status: Accepted$", rfc, re.MULTILINE):
        raise ValueError("Policy release requires RFC 0023 acceptance at draft maturity")
    if not (root / "releases" / f"{tag}.md").is_file():
        raise ValueError("Policy release notes are missing for the exact tag")


def policy_corpus_digests(root: Path = ROOT) -> dict[str, str]:
    paths = sorted(path for directory in ("examples", "vectors")
                   for path in (root / POLICY_ROOT / directory).rglob("*")
                   if path.is_file())
    return {path.relative_to(root).as_posix(): "sha256:" + sha256(path) for path in paths}


def validate_policy_history(tag: str) -> None:
    """Compare immutable tagged records, so editing old working files cannot repoint a format."""
    release = json.loads((ROOT / "releases" / f"{tag}.json").read_text("utf-8"))
    for previous in git("tag", "--list", "policy-v*").splitlines():
        if previous == tag or not is_policy_tag(previous):
            continue
        old = json.loads(git("show", f"refs/tags/{previous}:releases/{previous}.json"))
        if old.get("formatVersion") == release["formatVersion"]:
            for key in ("schemas", "formatDigests", "consumerSpecVersions", "corpus"):
                if old.get(key) != release[key]:
                    raise ValueError("Policy exact format conflicts with immutable tagged release history")


def bundle_paths(tag: str, commit: str) -> tuple[str, ...]:
    if is_policy_tag(tag):
        return (*POLICY_BUNDLE_PATHS, f"releases/{tag}.md", f"releases/{tag}.json")
    # Policy has its own release identity. Do not carry its separately versioned
    # schemas/corpus in a Core archive or alter the frozen Core manifests.
    paths = []
    for path in BUNDLE_PATHS:
        if path in ("schema", "conformance"):
            children = git("ls-tree", "--name-only", f"{commit}:{path}").splitlines()
            paths.extend(f"{path}/{child}" for child in children if child != "policy")
        else:
            paths.append(path)
    return (*paths, f"releases/{tag}.md")


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
    policy = POLICY_TAG_PATTERN.fullmatch(tag)
    if policy:
        return policy.group(1)
    if not tag.startswith("v") or not VERSION_PATTERN.fullmatch(tag[1:]):
        raise ValueError("release tag must be exact v-SemVer or policy-vSemVer-draft.N")
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
    if is_policy_tag(tag):
        validate_policy_artifacts(version, tag)
    else:
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
    if is_policy_tag(tag):
        validate_policy_history(tag)
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
    artifact = "judgment-pack-policy" if is_policy_tag(tag) else "judgment-pack-spec"
    prefix = f"{artifact}-{version}/"
    common = (
        "archive",
        f"--prefix={prefix}",
        commit,
        *bundle_paths(tag, commit),
    )
    archives = [
        output / f"{artifact}_{version}_artifacts.tar.gz",
        output / f"{artifact}_{version}_artifacts.zip",
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

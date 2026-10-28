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

# Explicit reviewed distribution identities; no generic prerelease normalization.
CORE_RC_TAG = "v0.3.0-rc.1"
CORE_RC_IDENTITY = {
    "releaseVersion": "0.3.0-rc.1",
    "tag": CORE_RC_TAG,
    "specVersion": "0.3.0",
    "maturity": "draft",
    "distribution": "release-candidate",
}

# Explicit planned RC2 distribution; published RC1 mapping stays exact and immutable.
CORE_RC2_TAG = "v0.3.0-rc.2"
CORE_RC2_IDENTITY = {"releaseVersion": "0.3.0-rc.2", "tag": CORE_RC2_TAG,
                     "specVersion": "0.3.0", "maturity": "draft", "distribution": "release-candidate"}
CORE_RC_IDENTITIES = {CORE_RC_TAG: CORE_RC_IDENTITY, CORE_RC2_TAG: CORE_RC2_IDENTITY}
RETAINED_INVENTORY = "releases/v0.3.0-rc.2.retained-column.json"
RETAINED_BUNDLE_PATHS = ("tools/dialect_verify.py", "tools/retained_column.py",
                         "tools/_retained_column.py", "tools/check_retained_column.py",
                         "tools/dialect-verify-ts", "requirements-dev.txt")

# The final carries RC2's selected leaf byte for byte under its own inventory. It has no
# distribution mapping: VERSIONING.md allowlists the two RC mappings only.
CORE_FINAL_TAG = "v0.3.0"
FINAL_RETAINED_INVENTORY = "releases/v0.3.0.retained-column.json"
RETAINED_INVENTORIES = {CORE_RC2_TAG: RETAINED_INVENTORY, CORE_FINAL_TAG: FINAL_RETAINED_INVENTORY}
CORE_MILESTONE = {"number": 2, "title": "v0.3.0"}


def validate_retained_inventory(root: Path = ROOT, tag: str = CORE_RC2_TAG) -> None:
    inventory = root / RETAINED_INVENTORIES[tag]
    if not inventory.is_file():
        raise ValueError("retained-column inventory is missing for the exact tag")
    release = json.loads(inventory.read_text("utf-8"))
    if set(release) != {"contract", "distribution", "maturity", "schema", "schemaSha256",
                        "corpus", "corpusSha256", "files", "claim"}:
        raise ValueError("retained-column inventory has an invalid closed shape")
    if (release["contract"] != "retained-column/1" or release["distribution"] != tag
            or release["maturity"] != "draft" or release["claim"] != "selected-leaf-support"):
        raise ValueError("retained-column inventory identity or scope differs")
    schema = "schema/retained-column/1/contract.schema.json"
    corpus = "conformance/retained-column/1/cases.json"
    if release["schema"] != schema or release["corpus"] != corpus:
        raise ValueError("retained-column artifact paths differ")
    expected = {schema, "spec/retained-column.md", "spec/dialect.md", "spec/judgment-pack-core.md",
                "tools/dialect_verify.py", "tools/retained_column.py", "tools/_retained_column.py",
                "tools/check_retained_column.py"}
    for directory in ("conformance/retained-column/1", "tools/dialect-verify-ts/src"):
        expected.update(p.relative_to(root).as_posix() for p in (root / directory).rglob("*") if p.is_file())
    if set(release["files"]) != expected:
        raise ValueError("retained-column complete artifact inventory differs")
    if any(value != "sha256:" + sha256(root / path) for path, value in release["files"].items()):
        raise ValueError("retained-column immutable artifact bytes differ")
    if (release["schemaSha256"] != release["files"][schema]
            or release["corpusSha256"] != release["files"][corpus]):
        raise ValueError("retained-column schema or corpus pin differs")
    resource = json.loads((root / schema).read_text("utf-8"))
    if resource.get("$id") != "https://judgmentpack.org/schema/retained-column/1/contract.schema.json":
        raise ValueError("retained-column immutable schema identity differs")
    cases = json.loads((root / corpus).read_text("utf-8"))
    corpus_inputs = {"conformance/retained-column/1/" + name for name in
                     ("examples.json", "preparations.json", "capabilities.json", "manifest.json")}
    if set(cases["inputs"]) != corpus_inputs:
        raise ValueError("retained-column complete corpus input set differs")
    for path, value in cases["inputs"].items():
        if path not in expected or value != release["files"][path]:
            raise ValueError("retained-column corpus companion input differs")


def validate_final_retained_inventory(root: Path = ROOT) -> None:
    """Hold the final's inventory to the bytes RC2 published: only its distribution differs."""
    validate_retained_inventory(root, CORE_FINAL_TAG)
    final = json.loads((root / FINAL_RETAINED_INVENTORY).read_text("utf-8"))
    published = root / RETAINED_INVENTORY
    if not published.is_file():
        raise ValueError("the published RC2 retained-column inventory is missing")
    if {**final, "distribution": CORE_RC2_TAG} != json.loads(published.read_text("utf-8")):
        raise ValueError("final retained-column inventory differs from the published RC2 inventory")


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
    "tools/retained_column.py", "tools/_retained_column.py",
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
    if tag in CORE_RC_IDENTITIES:
        paths.extend((f"releases/{tag}.json", "docs/releases/v0.3.0.md"))
    if tag in RETAINED_INVENTORIES:
        paths.extend((*RETAINED_BUNDLE_PATHS, RETAINED_INVENTORIES[tag], f"releases/{tag}.milestone.json"))
    return (*paths, core_release_notes_path(tag).relative_to(ROOT).as_posix())


def core_release_notes_path(tag: str, root: Path = ROOT) -> Path:
    """Return the immutable notes path, or the prepared notes before release publication."""
    published = root / "releases" / f"{tag}.md"
    if published.is_file():
        return published
    return root / "docs" / "releases" / f"{tag}.md"


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
    """Check exact format pins; only the reviewed RCs have a separate distribution identity.

    The RC distributes proposed 0.3.0 artifacts, not a released conformance corpus.
    No arbitrary prerelease suffix may be stripped to infer a compatible specVersion.
    The v0.3.0 final carries RC2's selected leaf under its own inventory and no mapping.
    """
    if version != release_version(tag):
        raise ValueError("release version does not match the exact tag")
    if tag not in CORE_RC_IDENTITIES and (root / "releases" / f"{tag}.json").exists():
        raise ValueError("only the allowlisted Core RCs have a release mapping")
    if tag in CORE_RC_IDENTITIES:
        mapping = root / "releases" / f"{tag}.json"
        if not mapping.is_file():
            raise ValueError("Core RC release mapping is missing for the exact tag")
        if json.loads(mapping.read_text("utf-8")) != CORE_RC_IDENTITIES[tag]:
            raise ValueError("Core RC release mapping does not match the reviewed identity")
        version = CORE_RC_IDENTITIES[tag]["specVersion"]
    manifest = json.loads((root / "conformance" / "manifest.json").read_text("utf-8"))
    evaluation = json.loads(
        (root / "conformance" / "evaluation" / "manifest.json").read_text("utf-8")
    )
    schema = json.loads(
        (root / "schema" / "judgment-pack-core.schema.json").read_text("utf-8")
    )
    if manifest.get("specVersion") != version:
        raise ValueError("release tag does not match the conformance specVersion")
    if tag in CORE_RC_IDENTITIES:
        if manifest.get("suiteVersion") != version:
            raise ValueError("Core RC does not match the document corpus suiteVersion")
        if manifest.get("status") != "draft" or evaluation.get("status") != "draft":
            raise ValueError("Core RC requires draft manifest maturity")
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
    if tag in RETAINED_INVENTORIES:
        if tag == CORE_FINAL_TAG:
            validate_final_retained_inventory(root)
        else:
            validate_retained_inventory(root, tag)
        milestone = root / "releases" / f"{tag}.milestone.json"
        if not milestone.is_file() or json.loads(milestone.read_text("utf-8")) != CORE_MILESTONE:
            raise ValueError(f"{tag} must preserve the final Core milestone")
        if "- Status: Accepted" not in (root / "rfcs/0029-retained-column-conversions.md").read_text("utf-8").splitlines():
            raise ValueError(f"{tag} requires recorded RFC0029 acceptance at draft maturity")
    release_notes = core_release_notes_path(tag, root)
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
    extra = ()
    if tag in CORE_RC_IDENTITIES:
        # This generated member is covered by both archive checksums/attestations.
        identity = {**CORE_RC_IDENTITIES[tag], "sourceCommit": git("rev-parse", "--verify", f"{commit}^{{commit}}")}
        encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")) + "\n"
        extra = (f"--add-virtual-file={prefix}release-identity.json:{encoded}",)
    common = (
        "archive",
        f"--prefix={prefix}",
        *extra,
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

#!/usr/bin/env python3
"""One reviewed recovery route for the unchanged v0.3.0-rc.1 artifact source."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import types
import zipfile

REPOSITORY = "Judgment-Pack/judgment-pack-spec"
TAG = "v0.3.0-rc.1"
TAG_OBJECT = "c0ddd58e507ce42891947929acb1ad0330faa038"
SOURCE = "495535f29a517dc6a36075b77238634011e7371e"
WORKFLOW = ".github/workflows/recover-core-rc.yml"
REF = "refs/heads/main"
ARCHIVES = ("judgment-pack-spec_0.3.0-rc.1_artifacts.tar.gz",
            "judgment-pack-spec_0.3.0-rc.1_artifacts.zip")
PREFIX = "judgment-pack-spec-0.3.0-rc.1/"
TOOLCHAINS = {"node": "22", "python": "3.12"}
CHECKS = ["local-paths", "agent-docs", "diff-check", "repository-tests",
          "policy-prototype", "policy-contract", "policy-official-draft"]


def run(*args: str, root: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=root, check=check, capture_output=True, text=True, timeout=120)


def output(*args: str, root: Path) -> str:
    return run(*args, root=root).stdout.strip()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_dispatch(event: dict, env: dict) -> str:
    expected = event.get("inputs", {}).get("expectedWorkflowCommit")
    if (env.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
            or env.get("GITHUB_REPOSITORY") != REPOSITORY
            or event.get("repository", {}).get("full_name") != REPOSITORY
            or event.get("ref") != REF or env.get("GITHUB_REF") != REF
            or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{40}", expected)
            or env.get("GITHUB_SHA") != expected or env.get("GITHUB_WORKFLOW_SHA") != expected
            or env.get("GITHUB_WORKFLOW_REF") != f"{REPOSITORY}/{WORKFLOW}@{REF}"):
        raise ValueError("expected genuine main dispatch at the exact reviewed workflow commit")
    if any(not re.fullmatch(r"[1-9][0-9]*", env.get(key, "")) for key in ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT")):
        raise ValueError("expected genuine main dispatch run identity")
    if set(event.get("inputs", {})) != {"expectedWorkflowCommit"}:
        raise ValueError("recovery accepts no artifact identity inputs")
    return expected


def trusted_source_helpers(source: Path) -> dict[str, bytes]:
    """Establish original helper identity in recovery-owned code before executing source Python."""
    if (Path(output("git", "rev-parse", "--show-toplevel", root=source)).resolve() != source.resolve()
            or output("git", "rev-parse", "--verify", "HEAD^{commit}", root=source) != SOURCE
            or output("git", "rev-parse", "--verify", f"refs/tags/{TAG}", root=source) != TAG_OBJECT
            or output("git", "rev-parse", "--verify", f"refs/tags/{TAG}^{{commit}}", root=source) != SOURCE):
        raise ValueError("source checkout root, commit and exact annotated tag must match")
    if output("git", "status", "--porcelain", "--untracked-files=no", root=source):
        raise ValueError("tracked release checkout must be clean before helper execution")
    helpers = {}
    # Check BOTH before running either. Byte comparison also catches helpers hidden by index flags.
    for name in ("build_release", "release_milestone"):
        relative = f"tools/{name}.py"
        original = subprocess.run(["git", "show", f"{SOURCE}:{relative}"], cwd=source,
                                  check=True, capture_output=True, timeout=120).stdout
        if (source / relative).read_bytes() != original:
            raise ValueError("source helper bytes differ from the original tagged blob")
        helpers[name] = original
    return helpers


def tagged_helpers(source: Path):
    helpers = trusted_source_helpers(source)
    # Compile verified immutable bytes, not a second path read or an untracked .pyc cache.
    def load(name, path, raw):
        module = types.ModuleType(name)
        module.__file__ = str(path)
        exec(compile(raw, str(path), "exec"), module.__dict__)
        return module
    builder = load("recovery_tagged_builder", source / "tools/build_release.py", helpers["build_release"])
    previous = sys.modules.get("build_release")
    sys.modules["build_release"] = builder
    try:
        milestone = load("recovery_tagged_milestone", source / "tools/release_milestone.py", helpers["release_milestone"])
    finally:
        if previous is None:
            del sys.modules["build_release"]
        else:
            sys.modules["build_release"] = previous
    return builder, milestone


def validate_remote(source: Path) -> None:
    text = output("git", "ls-remote", "--exit-code", f"https://github.com/{REPOSITORY}.git",
                  f"refs/tags/{TAG}", f"refs/tags/{TAG}^{{}}", root=source)
    lines = text.splitlines()
    expected = {f"{TAG_OBJECT}\trefs/tags/{TAG}", f"{SOURCE}\trefs/tags/{TAG}^{{}}"}
    if len(lines) != 2 or set(lines) != expected:
        raise ValueError("remote annotated tag object or peeled source differs")


# This one-off recovery refuses if a complete draft-visible inventory cannot be bounded.
RELEASE_PAGE_SIZE = 100
MAX_RELEASE_PAGES = 20
MAX_RELEASE_API_BYTES = 16 << 20


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("ambiguous duplicate release API JSON member")
        result[key] = value
    return result


def release_api(source: Path, path: str) -> tuple[dict, object]:
    response = run("gh", "api", "--hostname", "github.com", "--include", "--method", "GET",
                   "-H", "Accept: application/vnd.github+json", path, root=source, check=False)
    text = response.stdout.replace("\r\n", "\n")
    if len(text.encode("utf-8")) > MAX_RELEASE_API_BYTES:
        raise ValueError("release absence API response exceeds bound")
    head, separator, body = text.partition("\n\n")
    lines = head.splitlines()
    if (response.returncode != 0 or not separator or not lines
            or not re.fullmatch(r"HTTP/\S+ 200(?: .*|)", lines[0])):
        raise ValueError("release absence requires successful API evidence")
    headers = {}
    for line in lines[1:]:
        key, colon, value = line.partition(":")
        if not colon:
            raise ValueError("malformed release absence API headers")
        key = key.lower()
        if key == "link" and key in headers:
            raise ValueError("ambiguous release pagination headers")
        headers[key] = value.strip()
    return headers, json.loads(body, object_pairs_hook=unique_json_object)


def draft_visibility(source: Path) -> int:
    _, repository = release_api(source, f"repos/{REPOSITORY}")
    if (not isinstance(repository, dict) or repository.get("full_name") != REPOSITORY
            or type(repository.get("id")) is not int or repository["id"] <= 0
            or not isinstance(repository.get("permissions"), dict)
            or repository["permissions"].get("push") is not True):
        raise ValueError("authenticated push access and draft visibility are unproven")
    return repository["id"]


def release_page_links(value: str | None, repository_id: int) -> dict[str, int]:
    if value is None:
        return {}
    from urllib.parse import parse_qs, urlsplit
    links = {}
    for part in value.split(","):
        match = re.fullmatch(r'\s*<([^>]+)>;\s*rel="(next|prev|first|last)"\s*', part)
        if not match or match[2] in links:
            raise ValueError("malformed or duplicate release pagination relation")
        url = urlsplit(match[1])
        query = parse_qs(url.query, strict_parsing=True)
        if (url.scheme != "https" or url.netloc != "api.github.com" or url.fragment
                or url.path not in (f"/repos/{REPOSITORY}/releases", f"/repositories/{repository_id}/releases")
                or set(query) != {"page", "per_page"} or query["per_page"] != [str(RELEASE_PAGE_SIZE)]
                or len(query["page"]) != 1 or not re.fullmatch(r"[1-9][0-9]*", query["page"][0])):
            raise ValueError("release pagination leaves the exact repository or page contract")
        links[match[2]] = int(query["page"][0])
    return links


def refuse_existing_release(source: Path) -> None:
    # The tag endpoint is published-only. A tag404 says nothing about a draft.
    repository_id = draft_visibility(source)
    seen_ids, seen_tags = set(), set()
    last_boundary = None
    for page in range(1, MAX_RELEASE_PAGES + 1):
        headers, releases = release_api(source, f"repos/{REPOSITORY}/releases?per_page={RELEASE_PAGE_SIZE}&page={page}")
        if not isinstance(releases, list) or len(releases) > RELEASE_PAGE_SIZE:
            raise ValueError("malformed release inventory page")
        links = release_page_links(headers.get("link"), repository_id)
        for release in releases:
            if (not isinstance(release, dict) or type(release.get("id")) is not int or release["id"] <= 0
                    or not isinstance(release.get("tag_name"), str) or not release["tag_name"].strip()
                    or type(release.get("draft")) is not bool):
                raise ValueError("malformed release inventory member")
            if release["id"] in seen_ids or release["tag_name"] in seen_tags:
                raise ValueError("duplicate or unstable release inventory")
            seen_ids.add(release["id"])
            seen_tags.add(release["tag_name"])
            if release["tag_name"] == TAG:
                raise ValueError("a release or draft already exists for the exact tag")
        next_page, observed_last = links.get("next"), links.get("last")
        if last_boundary is not None and observed_last is not None and observed_last != last_boundary:
            raise ValueError("release pagination boundary changed during inventory")
        if observed_last is not None:
            last_boundary = observed_last
        # Missing later links cannot erase an earlier advertised completion boundary.
        last = last_boundary
        if last is not None and page == last and page > 1 and not releases:
            raise ValueError("advertised final release page is empty")
        if (("first" in links and links["first"] != 1)
                or ("prev" in links and links["prev"] != page - 1)
                or (next_page is not None and (next_page != page + 1 or len(releases) != RELEASE_PAGE_SIZE))
                or (last is not None and ((last < page and releases) or (next_page and last < next_page)
                                         or (last > page and next_page is None)))):
            raise ValueError("incomplete or inconsistent release pagination")
        if next_page is None and (len(releases) < RELEASE_PAGE_SIZE or last == page):
            if draft_visibility(source) != repository_id:
                raise ValueError("repository draft visibility changed during inventory")
            return
        # A full page without completion evidence requires another explicit page, never absence.
    raise ValueError("release inventory exhausted its bounded complete-absence proof")


def admission(source: Path, workflow: Path, event: dict, env: dict) -> tuple[dict, object]:
    revision = validate_dispatch(event, env)
    if (output("git", "rev-parse", "HEAD", root=workflow) != revision
            or output("git", "status", "--porcelain", "--untracked-files=no", root=workflow)):
        raise ValueError("workflow checkout differs from the reviewed revision")
    builder, milestone = tagged_helpers(source)
    milestone.validate_checkout(TAG, SOURCE, root=source)
    if output("git", "rev-parse", "--verify", f"refs/tags/{TAG}", root=source) != TAG_OBJECT:
        raise ValueError("local annotated tag object differs")
    builder.validate_artifacts(builder.release_version(TAG), TAG, root=source)
    link = milestone.validate_milestone(TAG, REPOSITORY, root=source)
    manifest = json.loads((source / "dev.json").read_text())
    if ({key: manifest["toolchains"][key]["version"] for key in TOOLCHAINS} != TOOLCHAINS
            or [step["name"] for step in manifest["checks"]] != CHECKS):
        raise ValueError("tagged required checklist or declared toolchains differ")
    validate_remote(source)
    refuse_existing_release(source)
    identity = {"repository": REPOSITORY, "tag": TAG, "tagObject": TAG_OBJECT,
                "artifactSourceCommit": SOURCE, "workflowCommit": revision,
                "workflowRef": f"{REPOSITORY}/{WORKFLOW}@{REF}", "milestone": link,
                "workflowRun": {"id": env["GITHUB_RUN_ID"], "attempt": env["GITHUB_RUN_ATTEMPT"],
                                "url": f"https://github.com/{REPOSITORY}/actions/runs/{env['GITHUB_RUN_ID']}"}}
    return identity, builder


def verify_archives(source: Path, dist: Path) -> dict:
    # Independently compare every regular member with its ORIGINAL committed blob.
    def member_path(name):
        if not name.startswith(PREFIX):
            raise ValueError("archive prefix differs")
        path = name[len(PREFIX):]
        if not path or any(part in ("", ".", "..") for part in path.split("/")):
            raise ValueError("unsafe archive member")
        return path
    members = []
    with tarfile.open(dist / ARCHIVES[0], "r:gz") as archive:
        found = {}
        for item in archive:
            if item.isdir():
                continue
            path = member_path(item.name)
            if not item.isfile() or item.size > 8 * 1024 * 1024 or path in found:
                raise ValueError("invalid or duplicate tar member")
            found[path] = archive.extractfile(item).read()
        members.append(found)
    with zipfile.ZipFile(dist / ARCHIVES[1]) as archive:
        found = {}
        for item in archive.infolist():
            if item.is_dir():
                continue
            path = member_path(item.filename)
            if item.file_size > 8 * 1024 * 1024 or path in found:
                raise ValueError("invalid or duplicate zip member")
            found[path] = archive.read(item)
        members.append(found)
    tracked = output("git", "ls-tree", "-r", "--name-only", SOURCE, root=source).splitlines()
    fixed = {"README.md", "LICENSE", "NOTICE", "CHANGELOG.md", "VERSIONING.md", "TESTING.md",
             "SECURITY.md", f"releases/{TAG}.json", f"releases/{TAG}.md", "docs/releases/v0.3.0.md"}
    excluded = ("conformance/evaluation/staged/", "conformance/witness/", "conformance/dialect/",
                "schema/policy/", "conformance/policy/")
    expected = {p for p in tracked if (p in fixed or p.startswith(("spec/", "schema/", "examples/", "conformance/")))
                and p != "spec/workflow.md" and not p.startswith(excluded)}
    identity = {"releaseVersion": "0.3.0-rc.1", "tag": TAG, "specVersion": "0.3.0",
                "maturity": "draft", "distribution": "release-candidate", "sourceCommit": SOURCE}
    if members[0] != members[1] or set(members[0]) != expected | {"release-identity.json"}:
        raise ValueError("archive inventories differ from the exact tagged inventory")
    for path in expected:
        blob = subprocess.run(["git", "show", f"{SOURCE}:{path}"], cwd=source, check=True,
                              capture_output=True, timeout=120).stdout
        if members[0][path] != blob:
            raise ValueError(f"archive member differs from original tag: {path}")
    if json.loads(members[0]["release-identity.json"]) != identity:
        raise ValueError("archive release source identity differs")
    checksums = "".join(f"{digest(dist / name)}  {name}\n" for name in ARCHIVES)
    if (dist / "checksums.txt").read_text() != checksums:
        raise ValueError("archive checksums differ")
    return {name: digest(dist / name) for name in (*ARCHIVES, "checksums.txt")}


def runtime_toolchains(source: Path) -> dict:
    node = output("node", "--version", root=source)
    python = output(sys.executable, "--version", root=source)
    version = re.fullmatch(r"v22\.(\d+)\.\d+", node)
    if not version or int(version[1]) < 18 or not re.fullmatch(r"Python 3\.12\.\d+", python):
        raise ValueError("running toolchains differ from the tagged declarations")
    return {"node": node, "python": python}


def evidence(identity: dict, source: Path, dist: Path) -> dict:
    return {**identity, "evidenceVersion": "1", "toolchains": runtime_toolchains(source),
            "nodeOptions": os.environ.get("NODE_OPTIONS"),
            "manifestSha256": digest(source / "dev.json"),
            "artifacts": verify_archives(source, dist),
            "validationLogs": {name: digest(dist / name) for name in ("setup.log", "validation.log")}}


def verify_attestations(dist: Path, revision: str) -> None:
    # The certificate describes this main-branch WORKFLOW revision, not the old artifact checkout.
    for name in (*ARCHIVES, "recovery-evidence.json"):
        result = output("gh", "attestation", "verify", str(dist / name), "--hostname", "github.com",
                        "--repo", REPOSITORY,
                        "--cert-identity", f"https://github.com/{REPOSITORY}/{WORKFLOW}@{REF}",
                        "--cert-oidc-issuer", "https://token.actions.githubusercontent.com",
                        "--source-ref", REF, "--source-digest", revision, "--signer-digest", revision,
                        "--deny-self-hosted-runners", "--predicate-type", "https://slsa.dev/provenance/v1",
                        "--format", "json", root=dist)
        verified = json.loads(result)
        if not isinstance(verified, list) or not verified:
            raise ValueError("missing cryptographic attestation verification results")
        for row in verified:
            result = row.get("verificationResult") if isinstance(row, dict) else None
            if (not isinstance(result, dict) or not isinstance(result.get("statement"), dict)
                    or result["statement"].get("predicateType") != "https://slsa.dev/provenance/v1"
                    or not isinstance(result.get("signature"), dict)
                    or not isinstance(result["signature"].get("certificate"), dict)
                    or not result["signature"]["certificate"]
                    or not isinstance(result.get("verifiedTimestamps"), list)
                    or not result["verifiedTimestamps"]):
                raise ValueError("malformed cryptographic attestation verification results")
        print(json.dumps(verified))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("admit", "toolchains", "package", "verify"))
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--workflow-root", required=True, type=Path)
    parser.add_argument("--dist", required=True, type=Path)
    args = parser.parse_args()
    try:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        source, workflow, dist = args.source_root.resolve(), args.workflow_root.resolve(), args.dist.resolve()
        if args.phase == "toolchains":
            validate_dispatch(event, os.environ)
            print(json.dumps(runtime_toolchains(source), sort_keys=True))
            return
        identity, builder = admission(source, workflow, event, os.environ)
        if args.phase == "admit":
            with Path(os.environ["GITHUB_OUTPUT"]).open("a") as stream:
                for key, version in TOOLCHAINS.items():
                    print(f"{key}={version}", file=stream)
        elif args.phase == "package":
            if set(p.name for p in dist.iterdir()) != {"setup.log", "validation.log"}:
                raise ValueError("packaging output already exists or validation logs are missing")
            if os.environ.get("NODE_OPTIONS") != "--test-reporter=tap":
                raise ValueError("original tests require the controlled TAP environment")
            builder.build(TAG, SOURCE, dist)
            record = evidence(identity, source, dist)
            (dist / "recovery-evidence.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        else:
            record = json.loads((dist / "recovery-evidence.json").read_text())
            if set(p.name for p in dist.iterdir()) != {*ARCHIVES, "checksums.txt", "setup.log", "validation.log", "recovery-evidence.json"}:
                raise ValueError("unexpected recovery output")
            if record != evidence(identity, source, dist):
                raise ValueError("recovery evidence differs from actual identities or bytes")
            verify_attestations(dist, identity["workflowCommit"])
        print(json.dumps(identity, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError, tarfile.TarError, zipfile.BadZipFile) as error:
        parser.exit(1, f"exact RC recovery refused: {error}\n")


if __name__ == "__main__":
    main()

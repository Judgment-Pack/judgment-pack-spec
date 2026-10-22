#!/usr/bin/env python3
"""Fail closed unless an immutable release has an explicit repository milestone."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from build_release import release_version


ROOT = Path(__file__).resolve().parents[1]


def command(*args: str, root: Path = ROOT) -> str:
    return subprocess.run(args, cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def validate_event(event: dict, event_name: str, tag: str, repository: str) -> None:
    release_version(tag)
    if event.get("repository", {}).get("full_name") != repository:
        raise ValueError("event repository does not match")
    if event_name == "release":
        release = event.get("release", {})
        if (event.get("action") != "published" or release.get("draft") is not False
                or release.get("tag_name") != tag
                or not isinstance(release.get("published_at"), str)
                or not release["published_at"].strip()):
            raise ValueError("expected a published, non-draft release for the exact tag")
    elif event_name == "push":
        if event.get("ref") != f"refs/tags/{tag}" or event.get("deleted") is not False:
            raise ValueError("expected creation or update of the exact release tag")
    else:
        raise ValueError("only release publication and tag push events are supported")


def validate_checkout(tag: str, commit: str, root: Path = ROOT) -> str:
    release_version(tag)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("expected a full release commit SHA")
    head = command("git", "rev-parse", "--verify", "HEAD^{commit}", root=root)
    tagged = command("git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}", root=root)
    if head != commit or tagged != commit:
        raise ValueError("checkout, release tag and requested commit must match")
    if command("git", "status", "--porcelain", "--untracked-files=no", root=root):
        raise ValueError("tracked release checkout must be clean")
    return head


def validate_milestone(tag: str, repository: str, root: Path = ROOT) -> dict:
    link = json.loads(command("git", "show", f"HEAD:releases/{tag}.milestone.json", root=root))
    if (not isinstance(link, dict) or set(link) != {"number", "title"}
            or type(link["number"]) is not int or link["number"] <= 0
            or not isinstance(link["title"], str) or not link["title"].strip()):
        raise ValueError("milestone link must contain only a positive number and nonempty title")
    milestone = json.loads(command("gh", "api", f"repos/{repository}/milestones/{link['number']}", root=root))
    if (not isinstance(milestone, dict) or type(milestone.get("number")) is not int
            or milestone.get("number") != link["number"] or milestone.get("title") != link["title"]
            or milestone.get("state") not in ("open", "closed")):
        raise ValueError("repository milestone number, title or state does not match the release link")
    return link


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    try:
        repository = os.environ["GITHUB_REPOSITORY"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError("invalid repository identity")
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text("utf-8"))
        validate_event(event, os.environ["GITHUB_EVENT_NAME"], args.tag, repository)
        validate_checkout(args.tag, args.commit)
        link = validate_milestone(args.tag, repository)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"release milestone gate refused: {error}\n")
    print(f"Release {args.tag} links to milestone #{link['number']}: {link['title']}")


if __name__ == "__main__":
    main()

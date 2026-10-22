"""Release planning gate and event wiring, with hand-authored GitHub responses."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import release_milestone as gate

SHA = "a" * 40
REPOSITORY = "example/spec"


class ReleaseMilestoneTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "tools").mkdir()
        (self.root / "releases").mkdir()
        for name in ("release_milestone.py", "build_release.py"):
            shutil.copyfile(ROOT / "tools" / name, self.root / "tools" / name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        # Deliberately authored command fixtures, not recorded command output.
        (self.bin / "git").write_text('''#!/usr/bin/env python3
import os, sys
from pathlib import Path
if sys.argv[1] == 'show':
    print(Path(sys.argv[2].removeprefix('HEAD:')).read_text(), end='')
elif sys.argv[1] == 'status':
    print(os.environ.get('FIXTURE_DIRTY', ''), end='')
else:
    print(os.environ.get('FIXTURE_HEAD', 'a' * 40) if sys.argv[-1] == 'HEAD^{commit}' else os.environ.get('FIXTURE_TAG', 'a' * 40))
''')
        (self.bin / "gh").write_text('''#!/usr/bin/env python3
import os, sys
assert sys.argv == ['%s', 'api', 'repos/example/spec/milestones/2']
if os.environ.get('FIXTURE_API_ERROR'):
    sys.exit(1)
print(os.environ.get('FIXTURE_MILESTONE', '{"number":2,"title":"v0.3.0","state":"open"}'))
''' % (self.bin / "gh"))
        for executable in self.bin.iterdir():
            executable.chmod(0o755)

    def run_gate(self, tag="v0.3.0", *, event=None, link=None, missing=False, env=None, event_name="release", commit=SHA):
        if event is None:
            event = {"action": "published", "repository": {"full_name": REPOSITORY},
                     "release": {"tag_name": tag, "draft": False, "prerelease": True,
                                 "published_at": "2026-10-22T12:00:00Z"}}
        event_path = self.root / "event.json"
        event_path.write_text(json.dumps(event))
        if not missing:
            mapping = self.root / "releases" / f"{tag}.milestone.json"
            mapping.write_text(json.dumps({"number": 2, "title": "v0.3.0"} if link is None else link))
        environment = {**os.environ, "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
                       "GITHUB_REPOSITORY": REPOSITORY, "GITHUB_EVENT_NAME": event_name,
                       "GITHUB_EVENT_PATH": str(event_path), **(env or {})}
        return subprocess.run([sys.executable, str(self.root / "tools" / "release_milestone.py"),
                               "--tag", tag, "--commit", commit], cwd=self.root, env=environment,
                              capture_output=True, text=True)

    def test_published_core_prerelease_and_companion_share_open_or_closed_milestone(self):
        for tag in ("v0.3.0", "v0.3.0-rc.1", "policy-v1.0.0-draft.1"):
            for state in ("open", "closed"):
                with self.subTest(tag=tag, state=state):
                    result = self.run_gate(tag, env={"FIXTURE_MILESTONE": json.dumps(
                        {"number": 2, "title": "v0.3.0", "state": state})})
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_tag_push_is_gated_before_release_preparation(self):
        result = self.run_gate(event_name="push", event={"repository": {"full_name": REPOSITORY},
            "ref": "refs/tags/v0.3.0", "deleted": False})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_and_malformed_links_fail_closed(self):
        self.assertNotEqual(self.run_gate(missing=True).returncode, 0)
        for link in ({}, [], {"number": True, "title": "v0.3.0"},
                     {"number": 0, "title": "v0.3.0"}, {"number": 2, "title": " "},
                     {"number": 2, "title": "v0.3.0", "state": "closed"}):
            with self.subTest(link=link):
                self.assertNotEqual(self.run_gate(link=link).returncode, 0)
        path = self.root / "releases" / "v0.3.0.milestone.json"
        path.write_text('{')
        self.assertNotEqual(self.run_gate(missing=True).returncode, 0)

    def test_api_failure_and_wrong_milestone_are_refused(self):
        for env in ({"FIXTURE_API_ERROR": "1"}, {"FIXTURE_MILESTONE": "not-json"},
                    {"FIXTURE_MILESTONE": '{"number":3,"title":"v0.3.0","state":"open"}'},
                    {"FIXTURE_MILESTONE": '{"number":2,"title":"wrong","state":"closed"}'}):
            with self.subTest(env=env):
                self.assertNotEqual(self.run_gate(env=env).returncode, 0)

    def test_bad_event_identity_and_unsupported_tags_are_refused(self):
        base = {"action": "published", "repository": {"full_name": REPOSITORY},
                "release": {"tag_name": "v0.3.0", "draft": False, "published_at": "2026-10-22"}}
        events = [{**base, "action": "created"}, {**base, "repository": {"full_name": "other/spec"}}]
        for changes in ({"draft": True}, {"tag_name": "v0.2.0"}, {"published_at": ""}, {"published_at": True}):
            events.append({**base, "release": {**base["release"], **changes}})
        for event in events:
            self.assertNotEqual(self.run_gate(event=event).returncode, 0)
        for tag in ("demos-v0.3.0", "v01.3.0", "policy-v1.0.0", "v0.3.0+build"):
            self.assertNotEqual(self.run_gate(tag).returncode, 0)

    def test_mismatched_head_and_dirty_checkout_are_refused(self):
        for env in ({"FIXTURE_HEAD": "b" * 40}, {"FIXTURE_TAG": "b" * 40}, {"FIXTURE_DIRTY": " M tools/release_milestone.py"}):
            self.assertNotEqual(self.run_gate(env=env).returncode, 0)

    def test_real_annotated_tag_and_immutable_mapping(self):
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        def git(*args):
            result = subprocess.run([real_git, *args], cwd=self.root,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout.strip()
        git("init", "--quiet")
        mapping = self.root / "releases/v0.3.0.milestone.json"
        mapping.write_text(json.dumps({"number": 2, "title": "v0.3.0"}))
        git("add", "tools", "releases")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
            "commit", "--quiet", "-m", "Hand-authored release fixture")
        commit = git("rev-parse", "HEAD")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
            "tag", "-a", "v0.3.0", "-m", "Annotated release fixture")
        # Keep the GitHub fixture executable, but resolve Git from the actual host toolchain.
        real_bin = self.root / "real-bin"
        real_bin.mkdir()
        shutil.copyfile(self.bin / "gh", real_bin / "gh")
        (real_bin / "gh").chmod(0o755)
        # gh's argv check deliberately expects its original path.
        gh = real_bin / "gh"
        gh.write_text(gh.read_text().replace(str(self.bin / "gh"), str(gh)))
        env = {"PATH": str(real_bin) + os.pathsep + os.environ["PATH"]}
        result = self.run_gate(commit=commit, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Move HEAD forward while retaining the old tag: an event-pinned new commit cannot
        # silently substitute its tree for the tag's immutable release tree.
        (self.root / "later.txt").write_text("Later fixture commit")
        git("add", "later.txt")
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
            "commit", "--quiet", "-m", "Later fixture")
        later = git("rev-parse", "HEAD")
        result = self.run_gate(commit=later, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checkout, release tag and requested commit must match", result.stderr)
        # A plausible link present only in the worktree is not part of this tagged commit.
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
            "tag", "-a", "v0.3.1", "-m", "Untracked link fixture")
        result = self.run_gate("v0.3.1", commit=later, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("git", result.stderr)
        self.assertIn("HEAD:releases/v0.3.1.milestone.json", result.stderr)

    def test_annotated_tag_is_peeled_to_commit(self):
        calls = []
        def git(*args, **kwargs):
            calls.append(args)
            return "" if args[1] == "status" else SHA
        with patch.object(gate, "command", side_effect=git):
            self.assertEqual(gate.validate_checkout("v0.3.0", SHA), SHA)
        self.assertIn(("git", "rev-parse", "--verify", "refs/tags/v0.3.0^{commit}"), calls)


class ReleaseWorkflowTests(unittest.TestCase):
    def test_triggers_and_gate_order(self):
        deploy = (ROOT / ".github/workflows/deploy.yml").read_text()
        release = (ROOT / ".github/workflows/release.yml").read_text()
        conformance = (ROOT / ".github/workflows/conformance.yml").read_text()
        # Exact event blocks constrain eligible events; actionlint validates the complete YAML.
        self.assertIn("on:\n  release:\n    types: [published]\n", deploy)
        self.assertNotIn("  push:", deploy)
        self.assertNotIn("  pull_request:", deploy)
        self.assertNotIn("workflow_dispatch", deploy)
        self.assertNotIn("  preview:", deploy)
        self.assertIn("on:\n  push:\n    branches: [main]\n  pull_request:", conformance)
        self.assertIn("  repository-conformance:", conformance)
        self.assertIn("group: deploy-production", deploy)
        self.assertIn("environment: production", deploy)
        self.assertIn("startsWith(github.event.release.tag_name, 'policy-v')", deploy)
        self.assertIn("startsWith(github.event.release.tag_name, 'v')", deploy)
        for workflow in (deploy, release):
            self.assertLess(workflow.index("release_milestone.py"), workflow.index("pip install"))
            self.assertIn("persist-credentials: false", workflow)
            self.assertIn("issues: read", workflow)
        self.assertIn("ref: refs/tags/${{ github.event.release.tag_name }}", deploy)
        self.assertIn("ref: ${{ github.ref }}", release)
        self.assertLess(deploy.index("release_milestone.py"), deploy.index("google-github-actions/auth"))
        self.assertIn('--tag "$RELEASE_TAG" --commit "${GITHUB_SHA}"', deploy)
        self.assertNotIn('--commit "$(git rev-parse HEAD)"', deploy)

"""The release evidence gate: its configuration held to the workflows, the manifest and the kit.

A `vMAJOR.MINOR.PATCH` release takes main's `repository-conformance` evidence at the exact commit
instead of running the repository suite again (web/DEPLOYMENT.md, "Release evidence"). These tests
keep `.github/ci-evidence.json`, `conformance.yml`, `release.yml`, `dev.json` and the vendored gate
from drifting apart. The gate's own tests ship with the development kit.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".github/ci-evidence.json"
GATE = ROOT / "scripts/dev/release_evidence.py"
# The kit release the gate is vendored from, and the SHA-256 of that release's
# lib/release_evidence.py. A re-vendor changes both, and line 2 of the copy.
KIT_RELEASE = "v0.10.0"
KIT_LIBRARY_SHA256 = "d44af3df07f64036013ba9967a54cf799cec678068f0937395d6a2eef370e0e8"
# The release job's steps, in order. Only the repository suite depends on the evidence job.
RELEASE_STEPS = [
    "Check out tagged source",
    "Validate release milestone and tagged checkout",
    "Read declared toolchains",
    "Set up Node",
    "Set up Python",
    "Report source and toolchains",
    "Install test dependencies",
    "Check repository artifacts and static site",
    "Check exact Policy format and agreement corpus",
    "Build immutable release bundles",
    "Create draft prerelease",
    "Attest release bundles",
]
SUITE_STEP = "Check repository artifacts and static site"


def load_gate():
    spec = importlib.util.spec_from_file_location("vendored_release_evidence", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def jobs_of(workflow: str) -> dict[str, str]:
    """Each job's block under `jobs:`, by its key (two-space indent)."""
    body = workflow.split("\njobs:\n", 1)[1]
    parts = re.split(r"^  ([A-Za-z0-9_-]+):\n", body, flags=re.MULTILINE)
    return {parts[index]: parts[index + 1] for index in range(1, len(parts), 2)}


def steps_of(job: str) -> list[str]:
    """Each step's text, in order (steps are list items at six spaces), without the blank lines
    and the comments between steps."""
    parts = re.split(r"^      - ", job.split("\n    steps:\n", 1)[1], flags=re.MULTILINE)[1:]
    return ["- " + re.sub(r"^(?: {0,6}#.*)?\n", "", part, flags=re.MULTILINE) for part in parts]


def field(block: str, key: str, indent: int) -> str | None:
    found = re.search(r"^%s%s: (.+)$" % (" " * indent, re.escape(key)), block, re.MULTILINE)
    return found.group(1).strip() if found else None


def step_named(job: str, name: str) -> str:
    matches = [step for step in steps_of(job) if field(step, "- name", 0) == name]
    if len(matches) != 1:
        raise AssertionError("expected one step named %r, found %d" % (name, len(matches)))
    return matches[0]


def steps_running(job: str, text: str) -> list[str]:
    return [step for step in steps_of(job) if text in step]


class VendoredGateTests(unittest.TestCase):
    def test_vendored_copy_is_the_kit_library_after_line_two(self):
        lines = GATE.read_bytes().split(b"\n")
        self.assertEqual(lines[1].decode(),
                         "# from judgment-pack-devkit %s (lib/release_evidence.py)" % KIT_RELEASE)
        library = b"\n".join(lines[:1] + lines[2:])
        self.assertEqual(hashlib.sha256(library).hexdigest(), KIT_LIBRARY_SHA256,
                         "scripts/dev/release_evidence.py is not the kit's lib/release_evidence.py "
                         "of %s after line 2" % KIT_RELEASE)


class ConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.manifest = json.loads((ROOT / "dev.json").read_text(encoding="utf-8"))

    def test_the_gate_accepts_the_configuration_for_this_repository(self):
        self.gate.check_config(self.config)
        self.assertEqual(self.config["repository"], "Judgment-Pack/judgment-pack-spec")
        self.assertEqual(self.config["branch"], "main")

    def test_every_input_is_a_tracked_file(self):
        self.assertTrue(self.config["inputs"])
        for path in self.config["inputs"]:
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file(), path)
                tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", path], cwd=ROOT,
                                         capture_output=True, text=True)
                self.assertEqual(tracked.returncode, 0, path + " is not tracked")

    def test_every_job_trigger_and_capture_exists_in_its_workflow(self):
        branch = self.config["branch"]
        for key, workflow in self.config["workflows"].items():
            text = (ROOT / workflow["path"]).read_text(encoding="utf-8")
            self.assertEqual(field(text, "name", 0), workflow["name"], workflow["path"])
            triggers = text.split("\non:\n", 1)[1].split("\n\n", 1)[0]
            for event in workflow["events"]:
                self.assertIn(event, ("push", "workflow_dispatch"))
                if event == "push":
                    self.assertIn("  push:\n    branches: [%s]\n" % branch, triggers)
                else:
                    self.assertIn("  workflow_dispatch:", triggers)
            jobs = jobs_of(text)
            for job_key, spec in workflow["jobs"].items():
                with self.subTest(workflow=key, job=job_key):
                    self.assertIn(spec["job_id"], jobs, "no job %s in %s" % (spec["job_id"], workflow["path"]))
                    job = jobs[spec["job_id"]]
                    # A matrix leg's display name carries its values; this repository has none.
                    self.assertNotIn("matrix:", job)
                    self.assertEqual(field(job, "name", 4) or spec["job_id"], spec["name"])
                    self.assertEqual([field(job, "runs-on", 4)], spec["labels"])
                    self.assert_capture(key, job_key, spec, job)

    def assert_capture(self, key, job_key, spec, job):
        events = self.config["workflows"][key]["events"]
        self.assertEqual(events, ["push"], "the capture condition below is written for push only")
        trusted = "github.ref == 'refs/heads/%s' && github.event_name == 'push'" % self.config["branch"]
        [capture] = steps_running(job, "scripts/dev/release_evidence.py capture")
        self.assertEqual(field(capture, "if", 8), trusted)
        self.assertIn("--workflow %s --job %s" % (key, job_key), capture)
        [upload] = steps_running(job, "ci-evidence-")
        self.assertEqual(field(upload, "if", 8), trusted)
        self.assertRegex(field(upload, "uses", 8), r"^actions/upload-artifact@[0-9a-f]{40} # v")
        self.assertEqual(field(upload, "name", 10),
                         "ci-evidence-%s-%s-${{ github.run_attempt }}" % (key, job_key))
        self.assertEqual(field(upload, "path", 10), re.search(r'--output "([^"]+)"', capture).group(1))
        self.assertEqual(field(upload, "if-no-files-found", 10), "error")
        logs = re.findall(r'--(check|setup)-log "([^"]+)"', capture)
        self.assertEqual([kind for kind, _ in logs].count("setup"), 1 if spec.get("setup") else 0)
        for kind, path in logs:
            # The log the capture reads is the one the step wrote with pipefail, from the run the
            # trusted event takes: the whole list, not a --changed selection.
            command = "scripts/dev/check.sh --setup" if kind == "setup" else "scripts/dev/check.sh --all"
            writers = [line.strip() for step in steps_of(job) for line in step.splitlines()
                       if line.strip().endswith('| tee "%s"' % path)]
            self.assertIn('%s | tee "%s"' % (command, path), writers)
            [writer] = [step for step in steps_of(job) if '| tee "%s"' % path in step]
            self.assertIn("set -o pipefail", writer)
        if spec["checks"] == "all":
            self.assertTrue(self.manifest["checks"])
        else:
            names = {check["name"] for check in self.manifest["checks"]}
            self.assertLessEqual(set(spec["checks"]), names)
        if spec.get("setup"):
            self.assertTrue(self.manifest["setup"])

    def test_installed_requirements_are_recorded_from_the_checks_environment(self):
        venv = self.manifest["toolchains"]["python"]["venv"]
        requirement = re.search(r"^jsonschema\[format-nongpl\]==(\S+)$",
                                (ROOT / "requirements-dev.txt").read_text(encoding="utf-8"), re.MULTILINE)
        self.assertIsNotNone(requirement, "requirements-dev.txt pins jsonschema with its format extras")
        for name, profile in self.config["profiles"].items():
            with self.subTest(profile=name):
                tools = profile["tools"]
                for tool in ("python-packages", "jsonschema-formats"):
                    self.assertEqual(tools[tool][0], "%s/bin/python3" % venv)
                self.assertEqual(tools["python-packages"][1:], ["-m", "pip", "freeze", "--all"])
                pin = profile["pins"]["jsonschema-formats"]
                version, formats = re.fullmatch(r"jsonschema==(\S+) formats: (.+)", pin).groups()
                self.assertEqual(version, requirement.group(1))
                # Without the extras these format checkers are absent and a malformed URI or
                # timestamp validates (CONTRIBUTING.md, "Local checks").
                self.assertLessEqual({"uri", "date-time"}, set(formats.split()))


class ReleaseWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        cls.release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        cls.jobs = jobs_of(cls.release)
        cls.conformance = jobs_of((ROOT / ".github/workflows/conformance.yml").read_text(encoding="utf-8"))

    def test_the_route_admits_exactly_the_gates_tag_grammar(self):
        route = step_named(self.jobs["evidence"], "Choose reuse or the whole suite at the tag")
        number = re.search(r"^\s+number='([^']+)'$", route, re.MULTILINE).group(1)
        grammar = re.search(r'^\s+grammar="([^"]+)"$', route, re.MULTILINE).group(1)
        expanded = grammar.replace("${number}", number)
        self.assertEqual(expanded, "^" + self.gate.TAG.pattern + "$")
        for tag in ("v0.3.0", "v1.10.0", "v0.3.0-rc.1", "v0.2.0-draft", "policy-v1.0.0-draft.1",
                    "v01.0.0", "v0.3", "v0.3.0.1", "demo/deal-evidence-readiness/v0.2.0"):
            with self.subTest(tag=tag):
                self.assertEqual(re.search(expanded, tag) is not None,
                                 self.gate.TAG.fullmatch(tag) is not None)

    def test_reuse_skips_only_the_repository_suite_and_a_refusal_stops_the_release(self):
        evidence, release = self.jobs["evidence"], self.jobs["release"]
        self.assertEqual(field(release, "needs", 4), "evidence")
        self.assertEqual(field(evidence, "route", 6), "${{ steps.route.outputs.route }}")
        permissions = evidence.split("    permissions:\n", 1)[1].split("    outputs:\n", 1)[0]
        self.assertEqual(re.findall(r"^      ([a-z-]+): (\w+)$", permissions, re.MULTILINE),
                         [("contents", "read"), ("actions", "read")])
        # The suite runs unless the route is exactly the evidence route, which the job reaches only
        # when the gate exited 0: a missing or other route value runs it.
        self.assertEqual(field(step_named(release, SUITE_STEP), "if", 8),
                         "needs.evidence.outputs.route != 'evidence'")
        self.assertEqual([name for name in RELEASE_STEPS if "needs.evidence" in step_named(release, name)],
                         [SUITE_STEP])
        self.assertIn("python -m unittest discover -s tests -v", step_named(release, SUITE_STEP))
        verify = step_named(evidence, "Reuse exact-commit main CI evidence, or refuse")
        self.assertEqual(field(verify, "if", 8), "steps.route.outputs.route == 'evidence'")
        self.assertEqual(field(verify, "RELEASE_TAG", 10), "${{ github.ref_name }}")
        self.assertIn('python3 scripts/dev/release_evidence.py verify --output "${{ runner.temp }}/release-evidence.json"',
                      verify)
        self.assertNotIn("continue-on-error", self.release)
        record = step_named(evidence, "Keep the decision record")
        self.assertEqual(field(record, "if", 8),
                         "${{ !cancelled() && steps.route.outputs.route == 'evidence' }}")
        self.assertEqual(field(record, "name", 10), "release-evidence-${{ github.run_attempt }}")
        self.assertEqual(field(record, "path", 10), "${{ runner.temp }}/release-evidence.json")
        self.assertEqual(field(record, "if-no-files-found", 10), "error")

    def test_release_steps_keep_their_order_and_release_semantics(self):
        release = self.jobs["release"]
        self.assertEqual([field(step, "- name", 0) for step in steps_of(release)], RELEASE_STEPS)
        self.assertEqual(field(step_named(release, "Check exact Policy format and agreement corpus"), "if", 8),
                         "startsWith(github.ref_name, 'policy-v')")
        draft = step_named(release, "Create draft prerelease")
        for flag in ("--draft", "--prerelease", "--verify-tag", '--notes-file "releases/${GITHUB_REF_NAME}.md"'):
            self.assertIn(flag, draft)
        self.assertIn("subject-checksums: dist/checksums.txt", step_named(release, "Attest release bundles"))

    def test_the_evidence_job_sets_up_its_runner_as_main_ci_does(self):
        evidence = self.jobs["evidence"]
        [ci] = self.conformance.values()

        def uses(job, action):
            return [field(step, "uses", 8) for step in steps_of(job) if "uses: %s@" % action in step]

        for action in ("actions/setup-python", "actions/setup-node"):
            self.assertEqual(len(uses(ci, action)), 1)
            self.assertEqual(uses(evidence, action), uses(ci, action))

        def toolchains(job):
            [step] = steps_running(job, "<<'P")
            return re.findall(r"^          (?:import|m =|tc =|print).*$", step, re.MULTILINE)

        self.assertEqual(len(toolchains(ci)), 5)
        self.assertEqual(toolchains(evidence), toolchains(ci))
        for name in ("Set up Python", "Set up Node"):
            with self.subTest(step=name):
                self.assertEqual(re.sub(r"^        if: .*\n", "", step_named(evidence, name), flags=re.MULTILINE),
                                 step_named(ci, name))
        self.assertEqual(len(steps_running(evidence, "run: scripts/dev/check.sh --setup")), 1)
        self.assertEqual(len(steps_running(ci, "scripts/dev/check.sh --setup")), 1)


if __name__ == "__main__":
    unittest.main()

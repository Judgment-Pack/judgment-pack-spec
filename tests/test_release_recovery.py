"""Hand-authored exact-RC recovery fixtures; fixture Git identities are not release evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import recover_core_rc as recovery

REVISION = "b" * 40
# Hand-authored CLI-output fixture, never evidence of an actual cryptographic verification.
VERIFIED = json.dumps([{"verificationResult": {"statement":{"predicateType":"https://slsa.dev/provenance/v1"},
    "signature":{"certificate":{"fixture":True}}, "verifiedTimestamps":[{"fixture":True}]}}])


def environment():
    return {"GITHUB_RUN_ID":"123", "GITHUB_RUN_ATTEMPT":"1", "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REPOSITORY": recovery.REPOSITORY,
            "GITHUB_REF": recovery.REF, "GITHUB_SHA": REVISION, "GITHUB_WORKFLOW_SHA": REVISION,
            "GITHUB_WORKFLOW_REF": f"{recovery.REPOSITORY}/{recovery.WORKFLOW}@{recovery.REF}"}


def event():
    return {"repository": {"full_name": recovery.REPOSITORY}, "ref": recovery.REF,
            "inputs": {"expectedWorkflowCommit": REVISION}}


class RecoveryGateTests(unittest.TestCase):
    def test_dispatch_requires_exact_repository_event_main_and_two_revision_bindings(self):
        self.assertEqual(recovery.validate_dispatch(event(), environment()), REVISION)
        for key in environment():
            bad = environment()
            bad[key] = "wrong"
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "genuine main dispatch"):
                recovery.validate_dispatch(event(), bad)
        for change in ({"ref": "main"}, {"repository": {"full_name": "fork/spec"}},
                       {"inputs": {"expectedWorkflowCommit": "short"}},
                       {"inputs": {"expectedWorkflowCommit": REVISION, "tag": "v0.3.1"}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                recovery.validate_dispatch({**event(), **change}, environment())

    def test_remote_exact_annotated_object_and_peeled_source(self):
        correct = f"{recovery.TAG_OBJECT}\trefs/tags/{recovery.TAG}\n{recovery.SOURCE}\trefs/tags/{recovery.TAG}^{{}}"
        with patch.object(recovery, "output", return_value=correct):
            recovery.validate_remote(ROOT)
        for value in ("", correct.splitlines()[0], correct + "\n" + correct,
                      correct.replace(recovery.TAG_OBJECT, "a" * 40), correct.replace(recovery.SOURCE, "d" * 40)):
            with patch.object(recovery, "output", return_value=value), self.assertRaisesRegex(ValueError, "remote annotated tag"):
                recovery.validate_remote(ROOT)
        with patch.object(recovery, "output", side_effect=subprocess.CalledProcessError(1, "git")), self.assertRaises(subprocess.CalledProcessError):
            recovery.validate_remote(ROOT)

    def test_absence_requires_actual_404_not_generic_api_failure_or_existing_draft(self):
        absent = subprocess.CompletedProcess([], 1, 'HTTP/2.0 404 Not Found\r\ncontent-type: application/json\r\n\r\n{"message":"Not Found"}', "")
        with patch.object(recovery, "run", return_value=absent):
            recovery.refuse_existing_release(ROOT)
        cases = [(0, 'HTTP/2.0 200 OK\n\n{"draft":true,"assets":[]}'),
                 (0, 'HTTP/2.0 200 OK\n\n{"draft":false}'),
                 (1, ''), (1, 'HTTP/2.0 403 Forbidden\n\n{"message":"Not Found"}'),
                 (1, 'HTTP/2.0 404 Not Found\n\n{"message":"unknown"}'),
                 (0, absent.stdout)]
        for code, response in cases:
            with self.subTest(response=response), patch.object(recovery, "run", return_value=subprocess.CompletedProcess([], code, response, "")), self.assertRaisesRegex(ValueError, "release absence"):
                recovery.refuse_existing_release(ROOT)

    def test_runtime_toolchains_refuse_node_versions_that_would_skip_the_original_reader(self):
        for node in ("v22.18.0", "v22.23.1"):
            with patch.object(recovery,"output",side_effect=[node,"Python 3.12.11"]):
                self.assertEqual(recovery.runtime_toolchains(ROOT)["node"],node)
        for versions in (("v22.17.0","Python 3.12.11"),("v24.0.0","Python 3.12.11"),("v22.23.1","Python 3.13.0"),("unknown","Python 3.12.11")):
            with patch.object(recovery,"output",side_effect=versions), self.assertRaisesRegex(ValueError,"running toolchains"):
                recovery.runtime_toolchains(ROOT)

    def test_crypto_verification_uses_exact_workflow_certificate_and_two_workflow_digests(self):
        calls = []
        def verified(*args, **kwargs):
            calls.append(args)
            return VERIFIED
        import contextlib
        import io
        retained = io.StringIO()
        with patch.object(recovery, "output", side_effect=verified), contextlib.redirect_stdout(retained):
            recovery.verify_attestations(ROOT, REVISION)
        self.assertEqual(len(calls), 3)
        self.assertEqual(len(retained.getvalue().splitlines()),3)
        for line in retained.getvalue().splitlines():
            self.assertTrue(line.startswith("["),"retain complete CLI verification JSON")
            self.assertEqual(json.loads(line),json.loads(VERIFIED))
        for args in calls:
            for flag, value in (("--source-digest", REVISION), ("--signer-digest", REVISION),
                                ("--source-ref", recovery.REF), ("--repo", recovery.REPOSITORY),
                                ("--cert-identity", f"https://github.com/{recovery.REPOSITORY}/{recovery.WORKFLOW}@{recovery.REF}"),
                                ("--cert-oidc-issuer", "https://token.actions.githubusercontent.com"),
                                ("--predicate-type", "https://slsa.dev/provenance/v1")):
                self.assertIn(flag,args)
                self.assertEqual(args[args.index(flag)+1], value)
            self.assertIn("--deny-self-hosted-runners", args)
            self.assertNotIn(recovery.SOURCE, args)
        for malformed in ('[]', '{}', 'null', '[{}]', '[{"verificationResult":null}]', '[{"verificationResult":true}]', '[{"verificationResult":{"unknown":true}}]'):
            with patch.object(recovery, "output", return_value=malformed), self.assertRaisesRegex(ValueError, "cryptographic attestation"):
                recovery.verify_attestations(ROOT, REVISION)
        with patch.object(recovery, "output", side_effect=subprocess.CalledProcessError(1, "gh")), self.assertRaises(subprocess.CalledProcessError):
            recovery.verify_attestations(ROOT, REVISION)


class RecoveryEntryTests(unittest.TestCase):
    def setUp(self):
        from test_release import CoreRCEntryPathTests
        self.fixture = CoreRCEntryPathTests(methodName="runTest")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.source = self.fixture.root
        import shutil
        shutil.copyfile(ROOT / "tools/release_milestone.py", self.source / "tools/release_milestone.py")
        (self.source / "dev.json").write_bytes((ROOT / "dev.json").read_bytes())
        (self.source / f"releases/{recovery.TAG}.milestone.json").write_text('{"number":2,"title":"v0.3.0"}')
        self.commit = self.fixture.commit()
        self.tag_object = self.fixture.git("rev-parse", f"refs/tags/{recovery.TAG}")
        self.dist = self.source / "dist"
        self.constants = patch.multiple(recovery, SOURCE=self.commit, TAG_OBJECT=self.tag_object)
        self.constants.start()
        self.addCleanup(self.constants.stop)

    def mock_output(self, *args, root):
        if args[:2] == ("git", "ls-remote"):
            return f"{self.tag_object}\trefs/tags/{recovery.TAG}\n{self.commit}\trefs/tags/{recovery.TAG}^{{}}"
        if root == self.source / "workflow":
            return REVISION if args[1] == "rev-parse" else ""
        return subprocess.run(args, cwd=root, check=True, capture_output=True, text=True).stdout.strip()

    def test_actual_original_validators_run_and_refuse_dirty_artifact_checkout(self):
        builder, milestone = recovery.tagged_helpers(self.source)
        self.assertEqual(builder.ROOT, self.source)
        self.assertEqual(milestone.ROOT, self.source)
        original = milestone.command
        def command(*args, root):
            if args[0] == "gh":
                return '{"number":2,"title":"v0.3.0","state":"open"}'
            return original(*args, root=root)
        with patch.object(recovery, "tagged_helpers", return_value=(builder, milestone)), patch.object(milestone, "command", side_effect=command), patch.object(recovery, "output", side_effect=self.mock_output), patch.object(recovery, "refuse_existing_release"):
            identity, _ = recovery.admission(self.source, self.source / "workflow", event(), environment())
            self.assertEqual(identity["artifactSourceCommit"], self.commit)
            self.assertEqual(identity["tagObject"], self.tag_object)
            self.assertEqual(identity["workflowCommit"], REVISION)
            (self.source / "spec/core.md").write_text("Unapproved worktree edit")
            with self.assertRaisesRegex(ValueError, "tracked release checkout must be clean"):
                recovery.admission(self.source, self.source / "workflow", event(), environment())

    def test_real_original_builder_archives_are_compared_to_actual_committed_blobs(self):
        builder, _ = recovery.tagged_helpers(self.source)
        builder.build(recovery.TAG, self.commit, self.dist)
        self.assertEqual(set(recovery.verify_archives(self.source, self.dist)), {*recovery.ARCHIVES, "checksums.txt"})
        # Consistently forged archive members and checksums must still fail against committed blobs.
        for filename in recovery.ARCHIVES:
            target = self.dist / filename
            if filename.endswith(".zip"):
                with zipfile.ZipFile(target) as archive:
                    files = {item.filename: archive.read(item) for item in archive.infolist() if not item.is_dir()}
                files[recovery.PREFIX + "spec/core.md"] = b"Forged fixture bytes\n"
                with zipfile.ZipFile(target, "w") as archive:
                    for name, raw in files.items():
                        archive.writestr(name, raw)
            else:
                import io
                with tarfile.open(target, "r:gz") as archive:
                    files = {item.name: archive.extractfile(item).read() for item in archive if item.isfile()}
                files[recovery.PREFIX + "spec/core.md"] = b"Forged fixture bytes\n"
                with tarfile.open(target, "w:gz") as archive:
                    for name, raw in files.items():
                        member = tarfile.TarInfo(name)
                        member.size = len(raw)
                        archive.addfile(member, io.BytesIO(raw))
        (self.dist / "checksums.txt").write_text("".join(f"{recovery.digest(self.dist / name)}  {name}\n" for name in recovery.ARCHIVES))
        with self.assertRaisesRegex(ValueError, "member differs from original tag"):
            recovery.verify_archives(self.source, self.dist)

    def test_actual_package_and_verify_entry_keep_workflow_and_artifact_identities_distinct(self):
        import contextlib
        import io
        builder, milestone = recovery.tagged_helpers(self.source)
        original = milestone.command
        def command(*args, root):
            if args[0] == "gh":
                return '{"number":2,"title":"v0.3.0","state":"open"}'
            return original(*args, root=root)
        verified_calls = []
        def observed(*args, root):
            if args[:3] == ("gh", "attestation", "verify"):
                verified_calls.append(args)
                return VERIFIED
            return self.mock_output(*args, root=root)
        self.dist.mkdir()
        (self.dist / "setup.log").write_text("Hand-authored setup fixture, not release validation")
        (self.dist / "validation.log").write_text("Hand-authored checklist fixture, not release validation")
        event_path = self.source / "dispatch.json"
        event_path.write_text(json.dumps(event()))
        def invoke(phase, *, options="--test-reporter=tap"):
            args = ["recover_core_rc.py", phase, "--source-root", str(self.source),
                    "--workflow-root", str(self.source / "workflow"), "--dist", str(self.dist)]
            with patch.object(sys, "argv", args), patch.dict(os.environ, {**environment(), "GITHUB_EVENT_PATH":str(event_path), "NODE_OPTIONS":options}), patch.object(recovery, "tagged_helpers", return_value=(builder,milestone)), patch.object(milestone, "command", side_effect=command), patch.object(recovery, "output", side_effect=observed), patch.object(recovery, "refuse_existing_release"), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                recovery.main()
        with self.assertRaises(SystemExit) as stopped:
            invoke("package", options="--test-reporter=spec")
        self.assertEqual(stopped.exception.code,1)
        self.assertFalse((self.dist / recovery.ARCHIVES[0]).exists())
        invoke("package")
        evidence_path = self.dist / "recovery-evidence.json"
        record = json.loads(evidence_path.read_text())
        self.assertEqual(record["artifactSourceCommit"], self.commit)
        self.assertEqual(record["workflowCommit"], REVISION)
        self.assertNotEqual(record["artifactSourceCommit"], record["workflowCommit"])
        invoke("verify")
        self.assertEqual(len(verified_calls),3)
        with self.assertRaises(SystemExit) as stopped:
            invoke("package")
        self.assertEqual(stopped.exception.code,1)
        record["artifactSourceCommit"] = REVISION
        evidence_path.write_text(json.dumps(record))
        with self.assertRaises(SystemExit) as stopped:
            invoke("verify")
        self.assertEqual(stopped.exception.code,1)

    def test_cli_refuses_bad_dispatch_before_importing_or_calling_any_source(self):
        with tempfile.TemporaryDirectory() as temp:
            event_path = Path(temp) / "event.json"
            event_path.write_text(json.dumps(event()))
            result = subprocess.run([sys.executable, str(ROOT / "tools/recover_core_rc.py"), "admit",
                                     "--source-root", str(self.source), "--workflow-root", str(ROOT), "--dist", str(self.dist)],
                                    env={**os.environ, **environment(), "GITHUB_EVENT_PATH": str(event_path), "GITHUB_SHA": "c" * 40},
                                    capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("genuine main dispatch", result.stderr)


class RecoveryWorkflowTests(unittest.TestCase):
    def test_future_release_toolchain_and_recovery_source_check_attest_draft_order(self):
        normal = (ROOT / ".github/workflows/release.yml").read_text()
        self.assertIn('tc["node"]["version"]', normal)
        self.assertIn("uses: actions/setup-node@", normal)
        self.assertIn("node-version: ${{ steps.dev.outputs.node }}", normal)
        self.assertLess(normal.index("actions/setup-node@"), normal.index("python -m unittest"))
        workflow = (ROOT / recovery.WORKFLOW).read_text()
        self.assertIn("on:\n  workflow_dispatch:", workflow)
        self.assertNotIn("  push:", workflow)
        self.assertIn(f"ref: {recovery.SOURCE}", workflow)
        self.assertIn("ref: ${{ github.sha }}", workflow)
        self.assertIn("NODE_OPTIONS: --test-reporter=tap", workflow)
        for value in ("scripts/dev/check.sh --setup", "scripts/dev/check.sh --all", "set -euo pipefail", "persist-credentials: false", "--draft --prerelease --verify-tag"):
            self.assertIn(value, workflow)
        ordered = ["recover_core_rc.py admit", "recover_core_rc.py toolchains", "scripts/dev/check.sh --setup", "scripts/dev/check.sh --all",
                   "recover_core_rc.py package", "subject-checksums: dist/checksums.txt",
                   "subject-path: dist/recovery-evidence.json", "recover_core_rc.py verify", "gh release create"]
        self.assertEqual(sorted(workflow.index(item) for item in ordered), [workflow.index(item) for item in ordered])
        self.assertNotIn("GH_TOKEN", workflow.split("    steps:")[0])
        expected_tokens = {"Admit only the exact reviewed dispatch and immutable RC",
                           "Recheck admission and build with original tagged builder",
                           "Verify actual provenance, archive bytes, and release absence",
                           "Create draft prerelease without replacing any release or asset"}
        actual_tokens = set()
        for section in workflow.split("      - name: ")[1:]:
            name = section.splitlines()[0]
            if "GH_TOKEN:" in section:
                actual_tokens.add(name)
        self.assertEqual(actual_tokens,expected_tokens)
        for forbidden in ("GITHUB_EVENT_NAME:", "GITHUB_SHA:", "--clobber", "release upload", "release edit", "release delete", "--skip", "continue-on-error"):
            self.assertNotIn(forbidden, workflow)


class DialectReporterContractTests(unittest.TestCase):
    def test_parsed_reporter_is_explicit_and_execution_summary_assertions_remain(self):
        import test_dialect_ts as dialect
        case = dialect.SecondDialectReaderTest(methodName="test_the_typescript_reader_answers_every_staged_vector")
        good = subprocess.CompletedProcess([],0,"# pass 271\n# fail 0\n","")
        with patch.object(case,"node",return_value="fixture-node"), patch.object(dialect.subprocess,"run",return_value=good) as called:
            case.test_the_typescript_reader_answers_every_staged_vector()
        self.assertIn("--test-reporter=tap", called.call_args.args[0])
        self.assertEqual(called.call_args.kwargs["env"]["NODE_OPTIONS"], "")
        for code, summary in ((1,good.stdout),(0,"# pass 0\n# fail 0\n"),(0,"# pass 271\n# fail 1\n"),(0,"271 passed")):
            with self.subTest(code=code,summary=summary), patch.object(case,"node",return_value="fixture-node"), patch.object(dialect.subprocess,"run",return_value=subprocess.CompletedProcess([],code,summary,"")), self.assertRaises(AssertionError):
                case.test_the_typescript_reader_answers_every_staged_vector()

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

    def run_source_cli(self, source, *, stub_api=False):
        """Actual CLI with fixture-only identity constants and no credentials/network."""
        import shutil
        workflow = self.source / "workflow-cli"
        workflow.mkdir()
        (workflow / "README.md").write_text("Hand-authored workflow checkout fixture")
        def git(*args):
            return subprocess.run(["git",*args],cwd=workflow,check=True,capture_output=True,text=True).stdout.strip()
        git("init","--quiet")
        git("add","README.md")
        git("-c","user.name=Fixture","-c","user.email=fixture@example.invalid","commit","--quiet","-m","Workflow fixture")
        revision = git("rev-parse","HEAD")
        cli = self.source / "recovery-cli.py"
        text = (ROOT / "tools/recover_core_rc.py").read_text()
        text = text.replace('SOURCE = "495535f29a517dc6a36075b77238634011e7371e"',f'SOURCE = "{self.commit}"')
        text = text.replace('TAG_OBJECT = "c0ddd58e507ce42891947929acb1ad0330faa038"',f'TAG_OBJECT = "{self.tag_object}"')
        cli.write_text(text)
        fixture_event = event()
        fixture_event["inputs"]["expectedWorkflowCommit"] = revision
        event_path = self.source / "cli-event.json"
        event_path.write_text(json.dumps(fixture_event))
        env = {key:value for key,value in os.environ.items() if key not in ("GH_TOKEN","GITHUB_TOKEN")}
        env.update(environment())
        env.update({"GITHUB_SHA":revision,"GITHUB_WORKFLOW_SHA":revision,"GITHUB_EVENT_PATH":str(event_path),
                    "GITHUB_OUTPUT":str(self.source / "cli-output"),"PYTHONDONTWRITEBYTECODE":"1"})
        if stub_api:
            binary = self.source / "cli-bin"
            binary.mkdir()
            real_git = shutil.which("git")
            (binary / "git").write_text("#!/usr/bin/env python3\nimport os,sys\n" +
                "if sys.argv[1] == 'ls-remote':\n print(" + repr(f"{self.tag_object}\trefs/tags/{recovery.TAG}\n{self.commit}\trefs/tags/{recovery.TAG}^{{}}") + ")\n" +
                "else: os.execv(" + repr(real_git) + ", [" + repr(real_git) + "] + sys.argv[1:])\n")
            (binary / "gh").write_text("#!/usr/bin/env python3\nimport sys\nfrom pathlib import Path\n" +
                "Path(" + repr(str(self.source / "original-milestone-reached")) + ").write_text('fixture API only')\n" +
                "if sys.argv[-1].endswith('/milestones/2'): print('{\"number\":2,\"title\":\"v0.3.0\",\"state\":\"open\"}')\n" +
                "else:\n print('HTTP/2.0 404 Not Found\\n\\n{\"message\":\"Not Found\"}');sys.exit(1)\n")
            for path in binary.iterdir():
                path.chmod(0o755)
            env["PATH"] = str(binary)+os.pathsep+env["PATH"]
        return subprocess.run([sys.executable,str(cli),"admit","--source-root",str(source),"--workflow-root",str(workflow),"--dist",str(self.dist)],
                              env=env,capture_output=True,text=True,timeout=30)

    def marker_helper(self, directory):
        (directory / "tools").mkdir(exist_ok=True)
        marker = directory / "import-executed"
        (directory / "tools/build_release.py").write_text("from pathlib import Path\nPath("+repr(str(marker))+").write_text('fixture import side effect')\nraise ValueError('fixture helper executed')\n")
        return marker

    def test_cli_nonrepository_source_refuses_without_executing_helper(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            marker = self.marker_helper(source)
            self.assertNotEqual(subprocess.run(["git","rev-parse","HEAD"],cwd=source,capture_output=True).returncode,0)
            result = self.run_source_cli(source)
            self.assertFalse(marker.exists(),"rejected source helper executed before source validation")
            self.assertEqual(result.returncode,1,result.stdout)
            self.assertIn("exact RC recovery refused",result.stderr)

    def test_cli_wrong_commit_refuses_without_executing_helper(self):
        marker = self.marker_helper(self.source)
        self.fixture.git("add","tools/build_release.py")
        self.fixture.git("-c","user.name=Fixture","-c","user.email=fixture@example.invalid","commit","--quiet","-m","Wrong fixture source")
        result = self.run_source_cli(self.source)
        self.assertFalse(marker.exists(),"rejected source helper executed before source validation")
        self.assertEqual(result.returncode,1,result.stdout)
        self.assertIn("source checkout root, commit and exact annotated tag",result.stderr)

    def test_cli_dirty_helper_refuses_without_executing_helper(self):
        marker = self.marker_helper(self.source)
        result = self.run_source_cli(self.source)
        self.assertFalse(marker.exists(),"rejected source helper executed before source validation")
        self.assertEqual(result.returncode,1,result.stdout)
        self.assertIn("clean before helper execution",result.stderr)

    def test_cli_hidden_modified_helper_refuses_before_import(self):
        marker = self.marker_helper(self.source)
        self.fixture.git("update-index","--assume-unchanged","tools/build_release.py")
        self.assertEqual(self.fixture.git("status","--porcelain","--untracked-files=no"),"")
        result = self.run_source_cli(self.source)
        self.assertFalse(marker.exists(),"changed helper bytes executed before source validation")
        self.assertEqual(result.returncode,1,result.stdout)
        self.assertIn("helper bytes differ",result.stderr)

    def test_both_helper_blobs_are_checked_before_either_module_is_created(self):
        (self.source / "tools/release_milestone.py").write_text("raise ValueError('changed second helper')")
        self.fixture.git("update-index","--assume-unchanged","tools/release_milestone.py")
        with patch.object(recovery.types,"ModuleType") as create:
            with self.assertRaisesRegex(ValueError,"helper bytes differ"):
                recovery.tagged_helpers(self.source)
            create.assert_not_called()

    def test_verified_helper_bytes_bypass_untracked_python_cache_and_keep_original_roots(self):
        import importlib.util
        import py_compile
        helper = self.source / "tools/build_release.py"
        marker = self.source / "cache-import-executed"
        poison = self.source / "poison.py"
        poison.write_text(helper.read_text().replace("ROOT =", "Path("+repr(str(marker))+").write_text('fixture cache side effect')\nROOT =",1))
        with patch.object(sys,"pycache_prefix",None):
            cached = Path(importlib.util.cache_from_source(str(helper)))
            cached.parent.mkdir(exist_ok=True)
            py_compile.compile(str(poison),cfile=str(cached),doraise=True,invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
            builder,milestone = recovery.tagged_helpers(self.source)
        self.assertFalse(marker.exists(),"unverified Python cache executed")
        self.assertEqual(builder.ROOT,self.source)
        self.assertEqual(milestone.ROOT,self.source)
        self.assertIs(milestone.release_version,builder.release_version)
        self.assertEqual(builder.validate(recovery.TAG,self.commit),"0.3.0-rc.1")

    def test_actual_cli_valid_source_reaches_original_validators_after_preflight(self):
        result = self.run_source_cli(self.source,stub_api=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue((self.source / "original-milestone-reached").exists())
        self.assertEqual((self.source / "cli-output").read_text(),"node=22\npython=3.12\n")

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

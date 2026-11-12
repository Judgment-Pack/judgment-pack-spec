from __future__ import annotations

import importlib.util
import io
import json
import hashlib
import re
import shutil
import sys
import zipfile
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

from test_retained_release import v0_3_0_tree


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_release", ROOT / "tools" / "build_release.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load release builder")
BUILD_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD_RELEASE)


class ReleaseBuilderTests(unittest.TestCase):
    def test_0_3_0_release_naming_is_recorded(self) -> None:
        versioning = (ROOT / "VERSIONING.md").read_text(encoding="utf-8")
        notes = ROOT / "releases" / "v0.3.0.md"
        self.assertIn("`v0.3.0-rc.1`", versioning)
        self.assertIn("`v0.3.0`", versioning)
        # The two prerelease forms, and which of them this repository's Core route uses.
        self.assertIn("`vX.Y.Z-rc.N` is a candidate of the complete milestone", versioning)
        self.assertIn("with no change to its normative artifacts", re.sub(r"\s+", " ", versioning))
        self.assertIn("`vX.Y.Z-alpha.N`, used by the implementations and never by this", versioning)
        self.assertTrue(notes.is_file())
        self.assertEqual("# v0.3.0", notes.read_text(encoding="utf-8").splitlines()[0])
        # The prepared notes stay as a pointer: the published RC1 notes link to them.
        pointer = (ROOT / "docs" / "releases" / "v0.3.0.md").read_text(encoding="utf-8")
        self.assertEqual("# v0.3.0", pointer.splitlines()[0])
        self.assertIn("(../../releases/v0.3.0.md)", pointer)
        self.assertIn("(../docs/releases/v0.3.0.md)",
                      (ROOT / "releases" / "v0.3.0-rc.1.md").read_text(encoding="utf-8"))

    def test_the_release_numbering_rule_is_recorded_with_its_exception(self) -> None:
        versioning = re.sub(r"\s+", " ", (ROOT / "VERSIONING.md").read_text(encoding="utf-8"))
        for text in ("## Release numbers and specVersion",
                     "This rule is normative for every Core release from `v0.5.0` on.",
                     "A Core release tag's major and minor numbers equal those of the `specVersion` the "
                     "release carries.",
                     "`specVersion` `0.5.0` is first released as tag `v0.5.0`.",
                     "The patch number counts the later releases that carry the same `specVersion` "
                     "unchanged: `v0.5.1`, `v0.5.2`, and so on.",
                     "A pack's `specVersion` stays `0.5.0` under every such release.",
                     "A new `specVersion` always takes a new minor (or major) number.",
                     "Recorded exception: tag `v0.4.0` (2026-11-02) carries `specVersion` `0.3.0` "
                     "unchanged; under this rule it would have been `v0.3.1`.",
                     "no `specVersion` `0.4.0` is assigned: the version staged as `0.4.0-draft` is "
                     "released as `0.5.0`",
                     "A tag such as `v0.5.1` needs a reviewed change to the builder before it is cut."):
            with self.subTest(text=text):
                self.assertIn(text, versioning)
        # The staged-selector section is history now; no sentence may still call it staged.
        self.assertNotIn("## Staged draft Core selector 0.4.0-draft", versioning)
        self.assertIn("## Core 0.5.0 was staged as 0.4.0-draft", versioning)

    def test_the_builder_does_not_yet_build_a_patch_release(self) -> None:
        # VERSIONING.md says a patch tag needs a builder change first. Until it lands, a v0.5.1 that
        # carries specVersion 0.5.0 unchanged is refused, not built under a guessed identity.
        with tempfile.TemporaryDirectory() as directory:
            root = self._release_tree(Path(directory), "0.5.0")
            BUILD_RELEASE.validate_artifacts("0.5.0", "v0.5.0", root=root)
            (root / "releases" / "v0.5.1.md").write_text("notes\n", encoding="utf-8")
            with self.assertRaises(ValueError) as raised:
                BUILD_RELEASE.validate_artifacts("0.5.1", "v0.5.1", root=root)
            self.assertIn("conformance specVersion", str(raised.exception))

    def test_the_0_5_0_notes_state_the_selector_and_the_waived_candidate_period(self) -> None:
        notes = re.sub(r"\s+", " ", (ROOT / "releases" / "v0.5.0.md").read_text(encoding="utf-8"))
        schema = ROOT / "schema" / "judgment-pack-core.schema.json"
        for text in ("Packs declare exact `specVersion` `0.5.0`, and the tag equals the selector",
                     "The text was staged under the working selector `0.4.0-draft`, which was never released.",
                     "no `specVersion` `0.4.0` is assigned",
                     "A `0.5.0` reader refuses a pack declaring `0.4.0-draft`, by the exact selector.",
                     "## Candidate period", "The maintainer waived the candidate period",
                     "same-vendor review, not a cross-vendor claim",
                     "The #308 content and the #304 fixture corrections postdate the round-1 review "
                     "and were covered by the review of the graduation pull request, also by the same "
                     "vendor, whose findings added the three reserved-prefix cases.",
                     "**Reader compatibility:**", "**Writer compatibility:**",
                     "**Semantic compatibility:**", "**Migration compatibility:**", "## Migration note",
                     "Stay on the `v0.3.0` bundle for the `retained-column/1` leaf.",
                     "https://judgmentpack.org/schema/0.5.0/judgment-pack-core.schema.json",
                     hashlib.sha256(schema.read_bytes()).hexdigest(),
                     "369 conformance cases and 5 advisory cases", "103 rows, 29 pairs"):
            with self.subTest(text=text[:40]):
                self.assertIn(text, notes)
        for name in ("schema/judgment-pack-core-0.3.0.schema.json",
                     "schema/conformance-manifest-0.3.0.schema.json",
                     "schema/conformance-evaluation-manifest-0.3.0.schema.json",
                     "schema/workflow-1-0.3.0.schema.json"):
            with self.subTest(preserved=name):
                self.assertIn(f"`{name}`", notes)
                self.assertIn(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), notes)
        errata = (ROOT / "conformance" / "evaluation" / "errata.md").read_text(encoding="utf-8")
        self.assertIn("## `0.5.0`\n\nNo errata.", errata)

    def test_final_notes_name_both_candidates_the_leaf_and_the_pins(self) -> None:
        notes = (ROOT / "releases" / "v0.3.0.md").read_text(encoding="utf-8")
        inventory = json.loads(
            (ROOT / "releases" / "v0.3.0.retained-column.json").read_text(encoding="utf-8")
        )
        for text in ("`v0.3.0-rc.1`", "published 2026-10-25", "`v0.3.0-rc.2`",
                     "published 2026-10-27", "The leaf is part of this release.",
                     "This release is the leaf's normative support distribution.",
                     "support version `0.3.0`", "keep their `v0.3.0-rc.2` labels",
                     "the Core and Dialect sentences on the leaf's adoption, and a dated note in RFC 0029",
                     "RFC 0024 is not part of this release; it remains a Draft.",
                     "## What this release pins", "## Checks run for this release",
                     "https://judgmentpack.org/schema/0.3.0/judgment-pack-core.schema.json",
                     inventory["schemaSha256"], inventory["corpusSha256"],
                     "## Migration note", "## Included work", "## Versioning and maturity"):
            with self.subTest(text=text):
                self.assertIn(text, re.sub(r"\s+", " ", notes))
        self.assertNotIn("if merged before the tag", notes)
        # The checks section states the mechanism, not values to fill in at the tag: the reused run's
        # identity lives in the decision artifact and the published release body.
        checks = notes.split("## Checks run for this release", 1)[1]
        for text in ("evidence for this exact commit", "release evidence gate",
                     "`release-evidence-<attempt>` artifact", "issue #259", "issue #261",
                     "#274", "same-vendor review under the authorized exception"):
            with self.subTest(checks=text):
                self.assertIn(text, re.sub(r"\s+", " ", checks))
        # The record of the reused run is the decision artifact (web/DEPLOYMENT.md), nothing else.
        self.assertNotIn("appended", checks)
        candidate = re.sub(r"\s+", " ", notes.split("## Candidate period", 1)[1].split("\n## ", 1)[0])
        for text in ("published on 2026-10-25", "on 2026-10-27", "recorded on issue #231 before the tag",
                     "No adopter feedback was received", "the maintainer shortened the candidate period",
                     "the tag was cut on 2026-10-29"):
            with self.subTest(candidate=text):
                self.assertIn(text, candidate)
        self.assertIn("kept as the run's\n`release-evidence-<attempt>` artifact",
                      (ROOT / "web" / "DEPLOYMENT.md").read_text(encoding="utf-8"))
        for placeholder in ("<conformance run id>", "<main commit>"):
            self.assertNotIn(placeholder, notes)

    def test_release_version_accepts_exact_semver_tags(self) -> None:
        self.assertEqual(BUILD_RELEASE.release_version("v0.1.0-draft"), "0.1.0-draft")
        self.assertEqual(BUILD_RELEASE.release_version("v0.3.0-rc.1"), "0.3.0-rc.1")
        self.assertEqual(BUILD_RELEASE.release_version("v1.2.3-rc.1"), "1.2.3-rc.1")
        self.assertEqual(BUILD_RELEASE.release_version("v1.2.3-0"), "1.2.3-0")
        self.assertEqual(BUILD_RELEASE.release_version("v1.2.3-alpha.1"), "1.2.3-alpha.1")
        # Alphanumeric prerelease ids may contain leading zeroes (SemVer §9).
        self.assertEqual(BUILD_RELEASE.release_version("v1.2.3-01alpha"), "1.2.3-01alpha")

    def test_release_version_rejects_ambiguous_tags(self) -> None:
        for tag in (
            "0.1.0",
            "v0.1",
            "v00.1.0",
            "v0.1.0+local",
            "main",
            "v1.2.3-01",
            "v1.2.3-alpha.01",
        ):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                BUILD_RELEASE.release_version(tag)

    def test_artifact_validation_accepts_the_current_version(self) -> None:
        manifest = json.loads(
            (ROOT / "conformance" / "manifest.json").read_text(encoding="utf-8")
        )
        version = manifest["specVersion"]
        self.assertEqual("0.5.0", version)
        BUILD_RELEASE.validate_artifacts(version, f"v{version}")
        # The ordinary path: the tag is the specVersion, so the release has no distribution mapping,
        # no generated identity and the notes and milestone link the workflow reads.
        self.assertNotIn("v0.5.0", BUILD_RELEASE.CORE_MAPPED_IDENTITIES)
        self.assertNotIn("v0.5.0", BUILD_RELEASE.GENERATED_IDENTITIES)
        self.assertFalse((ROOT / "releases" / "v0.5.0.json").exists())
        self.assertEqual("# v0.5.0", (ROOT / "releases" / "v0.5.0.md").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual({"number": 6, "title": "v0.5.0"},
                         json.loads((ROOT / "releases" / "v0.5.0.milestone.json").read_text(encoding="utf-8")))

    def test_core_bundle_uses_immutable_final_notes_and_keeps_historical_notes(self) -> None:
        current = BUILD_RELEASE.bundle_paths("v0.3.0", "HEAD")
        historical = BUILD_RELEASE.bundle_paths("v0.2.0-draft", "HEAD")
        self.assertEqual(ROOT / "releases" / "v0.3.0.md", BUILD_RELEASE.core_release_notes_path("v0.3.0"))
        self.assertIn("releases/v0.3.0.md", current)
        self.assertNotIn("docs/releases/v0.3.0.md", current)
        # A final has no distribution mapping; only the two RCs' and v0.4.0's are allowlisted.
        self.assertNotIn("releases/v0.3.0.json", current)
        self.assertFalse((ROOT / "releases" / "v0.3.0.json").exists())
        self.assertIn("releases/v0.2.0-draft.md", historical)
        self.assertNotIn("releases/v0.3.0.retained-column.json", historical)

    def test_artifact_validation_pins_the_evaluation_corpus(self) -> None:
        # An evaluator-conformance claim binds to the corpus published for the exact specVersion
        # (Core §§3.4, 3.4.1), so a tag whose evaluation manifest still names the previous version
        # must not build even when every document artifact is correctly re-pinned.
        for stale in ("specVersion", "suiteVersion"):
            with self.subTest(member=stale), tempfile.TemporaryDirectory() as directory:
                root = self._release_tree(Path(directory), "0.3.0")
                evaluation_path = root / "conformance" / "evaluation" / "manifest.json"
                evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
                evaluation[stale] = "0.2.0-draft"
                evaluation_path.write_text(json.dumps(evaluation), encoding="utf-8")
                with self.assertRaises(ValueError) as raised:
                    BUILD_RELEASE.validate_artifacts(
                        "0.3.0", "v0.3.0", root=root
                    )
                self.assertIn("evaluation corpus", str(raised.exception))
                # The same tree validates once the corpus is re-pinned.
                evaluation[stale] = "0.3.0"
                evaluation_path.write_text(json.dumps(evaluation), encoding="utf-8")
                BUILD_RELEASE.validate_artifacts("0.3.0", "v0.3.0", root=root)

    def test_validate_requires_head_to_be_the_release_commit(self) -> None:
        # Artifacts are validated from the worktree and archived from the commit, so a release built
        # while HEAD points elsewhere would ship a tree nobody validated.
        manifest = json.loads(
            (ROOT / "conformance" / "manifest.json").read_text(encoding="utf-8")
        )
        version = manifest["specVersion"]
        tag = f"v{version}"
        commit = "a" * 40
        original = BUILD_RELEASE.git
        try:
            for head, expected in ((commit, None), ("b" * 40, "not checked out")):
                with self.subTest(head=head):
                    def fake_git(*arguments: str, head: str = head) -> str:
                        if arguments[:2] == ("rev-parse", "--verify"):
                            return head if arguments[2] == "HEAD^{commit}" else commit
                        if arguments[0] == "status":
                            return ""
                        raise AssertionError(f"unexpected git call: {arguments}")

                    BUILD_RELEASE.git = fake_git
                    if expected is None:
                        self.assertEqual(BUILD_RELEASE.validate(tag, commit), version)
                    else:
                        with self.assertRaises(ValueError) as raised:
                            BUILD_RELEASE.validate(tag, commit)
                        self.assertIn(expected, str(raised.exception))
        finally:
            BUILD_RELEASE.git = original

    def test_release_bundle_leaves_staged_evaluation_rows_out(self) -> None:
        # The bundle is a `git archive` of BUNDLE_PATHS, and those include conformance/ whole. Rows
        # staged for a later suiteVersion are in no corpus, so .gitattributes marks their directory
        # export-ignore: no bundle carries a staged row, whatever is staged when a release is cut.
        # The released corpus beside them must stay in the bundle, so it is checked as the control.
        self.assertIn("conformance", BUILD_RELEASE.BUNDLE_PATHS)
        staged_root = ROOT / "conformance" / "evaluation" / "staged"
        staged_root_posix = staged_root.relative_to(ROOT).as_posix()
        staged = sorted(
            path.relative_to(ROOT).as_posix() for path in staged_root.rglob("*") if path.is_file()
        )
        self.assertTrue(staged, "nothing is staged; this test can go with the directory")
        evaluation = ROOT / "conformance" / "evaluation"
        released = sorted(
            path.relative_to(ROOT).as_posix()
            for path in [
                evaluation / "manifest.json",
                evaluation / "manifest.schema.json",
                *(evaluation / "packs").glob("*.json"),
            ]
        )
        # An attribute on a path says nothing about its ancestors, and `git archive` drops a whole
        # directory that is export-ignored: a rule on conformance/evaluation would leave the
        # released manifest "unspecified" and still omit it. So the ancestors are part of the control.
        ancestors = ["conformance", "conformance/evaluation", "conformance/evaluation/packs"]
        try:
            completed = subprocess.run(
                ["git", "check-attr", "export-ignore", "--", *staged, *released, *ancestors],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git cannot read attributes here: {error}")
        attributes = dict(
            line.rsplit(": export-ignore: ", 1) for line in completed.stdout.splitlines()
        )
        for path in staged:
            with self.subTest(path=path):
                self.assertEqual("set", attributes.get(path))
        for path in [*released, *ancestors]:
            with self.subTest(path=path):
                self.assertEqual("unspecified", attributes.get(path))

        # The attributes are configuration; the archive is the fact. Where there is a commit to
        # archive, list what the builder's own command would put in a bundle.
        archived = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD", "conformance/evaluation"],
            cwd=ROOT,
            capture_output=True,
        )
        if archived.returncode != 0:
            return  # no commit here (a bare scratch repository); the attribute checks above stand
        with tarfile.open(fileobj=io.BytesIO(archived.stdout)) as bundle:
            members = set(bundle.getnames())
        tracked = set(
            subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", "HEAD", "conformance/evaluation"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
        )
        self.assertEqual(
            [], sorted(name for name in members if name.startswith(staged_root_posix + "/"))
        )
        for path in released:
            if path in tracked:
                with self.subTest(archived=path):
                    self.assertIn(path, members)

    def test_release_bundle_leaves_the_witness_vectors_out(self) -> None:
        # The vectors RFC 0017 proposed are staged since its acceptance, in no corpus
        # (conformance/witness/README.md), so no bundle may carry them; .gitattributes marks their
        # directory export-ignore, and -text, since a converted line ending would change their bytes.
        # The document corpus beside them stays in the bundle, and is checked as the control.
        witness_root = (ROOT / "conformance" / "witness").relative_to(ROOT).as_posix()
        witness = sorted(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / witness_root).rglob("*")
            if path.is_file()
        )
        self.assertTrue(witness, "no witness vector is here; this test can go with the directory")
        released = ["conformance", "conformance/manifest.json", "conformance/README.md"]
        try:
            completed = subprocess.run(
                ["git", "check-attr", "export-ignore", "text", "--", *witness, *released],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git cannot read attributes here: {error}")
        attributes = {
            tuple(line.rsplit(": ", 2)[:2]): line.rsplit(": ", 1)[1]
            for line in completed.stdout.splitlines()
        }
        for path in witness:
            with self.subTest(path=path):
                self.assertEqual("set", attributes.get((path, "export-ignore")))
                self.assertEqual("unset", attributes.get((path, "text")))
        for path in released:
            with self.subTest(path=path):
                self.assertEqual("unspecified", attributes.get((path, "export-ignore")))

        archived = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD", "conformance"],
            cwd=ROOT,
            capture_output=True,
        )
        if archived.returncode != 0:
            return  # no commit here (a bare scratch repository); the attribute checks above stand
        with tarfile.open(fileobj=io.BytesIO(archived.stdout)) as bundle:
            members = set(bundle.getnames())
        self.assertEqual(
            [], sorted(name for name in members if name.startswith(witness_root + "/"))
        )
        self.assertIn("conformance/manifest.json", members)

    def test_release_bundle_carries_the_witness_companion_document(self) -> None:
        # The companion document landed with RFC 0017's acceptance; it is under spec/, which every
        # bundle carries, and nothing marks it export-ignore.
        self.assertIn("spec", BUILD_RELEASE.BUNDLE_PATHS)
        document = "spec/checkpoint-witness.md"
        self.assertTrue((ROOT / document).is_file())
        try:
            completed = subprocess.run(
                ["git", "check-attr", "export-ignore", "--", document, "spec"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git cannot read attributes here: {error}")
        for line in completed.stdout.splitlines():
            with self.subTest(line=line):
                self.assertTrue(line.endswith(": export-ignore: unspecified"))
        archived = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD", "spec"],
            cwd=ROOT,
            capture_output=True,
        )
        if archived.returncode != 0:
            return  # no commit here (a bare scratch repository); the attribute check above stands
        tracked = subprocess.run(
            ["git", "ls-tree", "--name-only", "HEAD", document],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()
        with tarfile.open(fileobj=io.BytesIO(archived.stdout)) as bundle:
            members = set(bundle.getnames())
        if tracked:
            self.assertIn(document, members)

    def test_release_bundle_leaves_the_dialect_vectors_out_and_carries_its_companion(self) -> None:
        # The dialect vectors are staged since RFC 0018's acceptance, in no corpus
        # (conformance/dialect/README.md), so no bundle carries them: .gitattributes marks them
        # export-ignore, and -text, since a converted line ending would change their bytes. The
        # companion document they belong to is published and under spec/, which every bundle
        # carries. The witness companion document and the document corpus are the controls.
        dialect_root = "conformance/dialect"
        vectors = sorted(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / dialect_root).rglob("*")
            if path.is_file()
        )
        self.assertTrue(vectors, "no dialect vector is here; this test can go with the directory")
        companion = "spec/dialect.md"
        self.assertTrue((ROOT / companion).is_file())
        released = [
            "spec",
            companion,
            "spec/checkpoint-witness.md",
            "conformance",
            "conformance/manifest.json",
        ]
        try:
            completed = subprocess.run(
                ["git", "check-attr", "export-ignore", "text", "--", *vectors, *released],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git cannot read attributes here: {error}")
        attributes = {
            tuple(line.rsplit(": ", 2)[:2]): line.rsplit(": ", 1)[1]
            for line in completed.stdout.splitlines()
        }
        for path in vectors:
            with self.subTest(path=path):
                self.assertEqual("set", attributes.get((path, "export-ignore")))
                self.assertEqual("unset", attributes.get((path, "text")))
        for path in released:
            with self.subTest(path=path):
                self.assertEqual("unspecified", attributes.get((path, "export-ignore")))

        archived = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD", "spec", "conformance"],
            cwd=ROOT,
            capture_output=True,
        )
        if archived.returncode != 0:
            return  # no commit here (a bare scratch repository); the attribute checks above stand
        tracked = subprocess.run(
            ["git", "ls-tree", "--name-only", "HEAD", companion],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()
        with tarfile.open(fileobj=io.BytesIO(archived.stdout)) as bundle:
            members = set(bundle.getnames())
        self.assertEqual(
            [], sorted(name for name in members if name.startswith(dialect_root + "/"))
        )
        if tracked:
            self.assertIn(companion, members)
        self.assertIn("conformance/manifest.json", members)

    def test_release_bundle_leaves_the_workflow_companion_out(self) -> None:
        # As for RFC 0018's Draft: the proposed companion is normative for nothing and excluded
        # until acceptance. Published companions and the spec directory are the controls.
        self.assertIn("spec", BUILD_RELEASE.BUNDLE_PATHS)
        companion = "spec/workflow.md"
        self.assertTrue((ROOT / companion).is_file())
        released = ["spec", "spec/dialect.md", "spec/checkpoint-witness.md"]
        try:
            completed = subprocess.run(
                ["git", "check-attr", "export-ignore", "--", companion, *released],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git cannot read attributes here: {error}")
        attributes = dict(
            line.rsplit(": export-ignore: ", 1) for line in completed.stdout.splitlines()
        )
        self.assertEqual("set", attributes.get(companion))
        for path in released:
            with self.subTest(path=path):
                self.assertEqual("unspecified", attributes.get(path))

        # Use the attributes under review even before they have been committed.
        archived = subprocess.run(
            ["git", "archive", "--worktree-attributes", "--format=tar", "HEAD", "spec"],
            cwd=ROOT,
            capture_output=True,
        )
        if archived.returncode != 0:
            return  # no commit here; the attribute checks above stand
        with tarfile.open(fileobj=io.BytesIO(archived.stdout)) as bundle:
            members = set(bundle.getnames())
        self.assertNotIn(companion, members)
        self.assertIn("spec/dialect.md", members)
        self.assertIn("spec/checkpoint-witness.md", members)

    @staticmethod
    def _release_tree(directory: Path, version: str) -> Path:
        """A minimal, correctly pinned artifact tree for the version-pinning checks."""
        (directory / "conformance" / "evaluation").mkdir(parents=True)
        (directory / "schema").mkdir()
        (directory / "releases").mkdir()
        (directory / "conformance" / "manifest.json").write_text(
            json.dumps({"specVersion": version}), encoding="utf-8"
        )
        (directory / "conformance" / "evaluation" / "manifest.json").write_text(
            json.dumps({"specVersion": version, "suiteVersion": version}),
            encoding="utf-8",
        )
        (directory / "schema" / "judgment-pack-core.schema.json").write_text(
            json.dumps(
                {
                    "$id": (
                        "https://judgmentpack.org/schema/"
                        f"{version}/judgment-pack-core.schema.json"
                    ),
                    "properties": {"specVersion": {"const": version}},
                }
            ),
            encoding="utf-8",
        )
        (directory / "releases" / f"v{version}.md").write_text("notes\n", encoding="utf-8")
        if version == "0.3.0":
            # The v0.3.0 final also carries RC2's selected leaf: its inventories, the leaf bytes they
            # pin, the milestone link and RFC 0029's acceptance are copied, not invented.
            inventory = json.loads(
                (ROOT / "releases" / "v0.3.0.retained-column.json").read_text(encoding="utf-8")
            )
            # Core 0.5.0 changed four leaf files in place; their v0.3.0 bytes are the preserved copies.
            v0_3_0_tree(directory, ("releases/v0.3.0.retained-column.json",
                                    "releases/v0.3.0-rc.2.retained-column.json",
                                    "releases/v0.3.0.milestone.json",
                                    "rfcs/0029-retained-column-conversions.md", *inventory["files"]))
        return directory


class CoreRCEntryPathTests(unittest.TestCase):
    """Hand-authored artifact trees, real Git tags and the actual builder CLI."""

    TAG = "v0.3.0-rc.1"
    IDENTITY = {"releaseVersion": "0.3.0-rc.1", "tag": TAG, "specVersion": "0.3.0",
                "maturity": "draft", "distribution": "release-candidate"}

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for directory in ("tools", "schema", "conformance/evaluation", "spec",
                          "examples", "releases", "docs/releases"):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "tools/build_release.py", self.root / "tools/build_release.py")
        for name in ("README.md", "LICENSE", "NOTICE", "CHANGELOG.md", "VERSIONING.md",
                     "TESTING.md", "SECURITY.md"):
            (self.root / name).write_text("Hand-authored release fixture.\n")
        (self.root / "spec/core.md").write_text("Proposed Core fixture, not a specification.\n")
        (self.root / "examples/example.json").write_text('{"specVersion":"0.3.0"}\n')
        for path, value in (
            ("conformance/manifest.json", {"specVersion": "0.3.0", "suiteVersion": "0.3.0", "status": "draft"}),
            ("conformance/evaluation/manifest.json", {"specVersion": "0.3.0", "suiteVersion": "0.3.0", "status": "draft"}),
            ("schema/judgment-pack-core.schema.json", {
                "$id": "https://judgmentpack.org/schema/0.3.0/judgment-pack-core.schema.json",
                "properties": {"specVersion": {"const": "0.3.0"}}}),
            (f"releases/{self.TAG}.json", self.IDENTITY),
        ):
            (self.root / path).write_text(json.dumps(value) + "\n")
        for path in (f"releases/{self.TAG}.md", "docs/releases/v0.3.0.md"):
            (self.root / path).write_text("# Hand-authored candidate notes\n")
        self.git("init", "--quiet")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, tag=None):
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--quiet", "-s", "-m", "Hand-authored release fixture")
        commit = self.git("rev-parse", "HEAD")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "tag", "-a", tag or self.TAG, "-m", "Release fixture")
        return commit

    def run_builder(self, commit, tag=None):
        return subprocess.run([sys.executable, str(self.root / "tools/build_release.py"),
                               "--tag", tag or self.TAG, "--commit", commit,
                               "--output", str(self.root / "dist")], cwd=self.root,
                              capture_output=True, text=True)

    def fresh_case(self):
        case = CoreRCEntryPathTests(methodName="runTest")
        case.setUp()
        self.addCleanup(case.doCleanups)
        return case

    def rewrite_json(self, path, change):
        target = self.root / path
        value = json.loads(target.read_text())
        change(value)
        target.write_text(json.dumps(value) + "\n")

    def test_rc_cli_builds_both_archives_with_exact_distribution_identity(self):
        commit = self.commit()
        result = self.run_builder(commit)
        self.assertEqual(0, result.returncode, result.stderr)
        prefix = "judgment-pack-spec-0.3.0-rc.1/"
        expected = {**self.IDENTITY, "sourceCommit": commit}
        tar = self.root / "dist/judgment-pack-spec_0.3.0-rc.1_artifacts.tar.gz"
        zip_path = tar.with_name("judgment-pack-spec_0.3.0-rc.1_artifacts.zip")
        with tarfile.open(tar) as archive:
            names = {m.name for m in archive.getmembers() if m.isfile()}
            self.assertIn(prefix + "release-identity.json", names)
            self.assertEqual(expected, json.load(archive.extractfile(prefix + "release-identity.json")))
            self.assertIn(prefix + f"releases/{self.TAG}.json", names)
            self.assertIn(prefix + f"releases/{self.TAG}.md", names)
            self.assertIn(prefix + "docs/releases/v0.3.0.md", names)
            self.assertEqual("0.3.0", json.load(archive.extractfile(prefix + "conformance/manifest.json"))["specVersion"])
        with zipfile.ZipFile(zip_path) as archive:
            self.assertEqual(names, {n for n in archive.namelist() if not n.endswith("/")})
            self.assertEqual(expected, json.loads(archive.read(prefix + "release-identity.json")))
        checksums = (self.root / "dist/checksums.txt").read_text().splitlines()
        self.assertEqual([hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name
                          for p in (tar, zip_path)], checksums)

    def test_rc_cli_refuses_missing_mapping_and_notes(self):
        for path, message in ((f"releases/{self.TAG}.json", "mapping is missing"),
                              (f"releases/{self.TAG}.md", "notes are missing")):
            with self.subTest(path=path):
                case = self.fresh_case()
                (case.root / path).unlink()
                result = case.run_builder(case.commit())
                self.assertNotEqual(0, result.returncode)
                self.assertIn(message, result.stderr)

    def test_rc_cli_refuses_changed_or_open_mapping(self):
        for changed in ({**self.IDENTITY, "specVersion": "0.2.0-draft"},
                        {**self.IDENTITY, "distribution": "final"},
                        {**self.IDENTITY, "maturity": "candidate"},
                        {**self.IDENTITY, "tag": "v0.3.0-rc.2"},
                        {**self.IDENTITY, "releaseVersion": "0.3.0"},
                        {**self.IDENTITY, "extra": True}, []):
            with self.subTest(changed=changed):
                case = self.fresh_case()
                (case.root / f"releases/{self.TAG}.json").write_text(json.dumps(changed))
                result = case.run_builder(case.commit())
                self.assertNotEqual(0, result.returncode)
                self.assertIn("mapping does not match", result.stderr)

    def test_rc_cli_refuses_each_format_pin_and_maturity_mismatch(self):
        cases = (("conformance/manifest.json", ("specVersion",), "conformance specVersion"),
                 ("conformance/manifest.json", ("suiteVersion",), "document corpus suiteVersion"),
                 ("conformance/evaluation/manifest.json", ("specVersion",), "evaluation corpus specVersion"),
                 ("conformance/evaluation/manifest.json", ("suiteVersion",), "evaluation corpus suiteVersion"),
                 ("schema/judgment-pack-core.schema.json", ("properties", "specVersion", "const"), "schema specVersion"),
                 ("schema/judgment-pack-core.schema.json", ("$id",), "schema $id"),
                 ("conformance/manifest.json", ("status",), "draft manifest maturity"),
                 ("conformance/evaluation/manifest.json", ("status",), "draft manifest maturity"))
        for path, keys, message in cases:
            with self.subTest(path=path, keys=keys):
                case = self.fresh_case()
                def alter(value):
                    for key in keys[:-1]:
                        value = value[key]
                    value[keys[-1]] = "wrong"
                case.rewrite_json(path, alter)
                result = case.run_builder(case.commit())
                self.assertNotEqual(0, result.returncode)
                self.assertIn(message, result.stderr)

    def test_rc_cli_does_not_strip_arbitrary_prerelease_suffixes(self):
        for tag in ("v0.3.0-rc.3", "v0.3.0-alpha.1", "v0.3.1-rc.1"):
            with self.subTest(tag=tag):
                case = self.fresh_case()
                (case.root / f"releases/{tag}.md").write_text("Wrong candidate fixture notes\n")
                result = case.run_builder(case.commit(tag=tag), tag=tag)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("conformance specVersion", result.stderr)

    def test_artifact_api_refuses_a_version_unrelated_to_the_tag(self):
        with self.assertRaisesRegex(ValueError, "version does not match the exact tag"):
            BUILD_RELEASE.validate_artifacts("0.3.0", self.TAG, root=self.root)

    def test_rc_cli_refuses_wrong_commit_and_mixed_checkout(self):
        commit = self.commit()
        (self.root / "later.txt").write_text("Different tree\n")
        later = self.commit(tag="v0.3.1")
        wrong = self.run_builder(later)
        self.assertNotEqual(0, wrong.returncode)
        self.assertIn("tag does not resolve", wrong.stderr)
        mixed = self.run_builder(commit)
        self.assertNotEqual(0, mixed.returncode)
        self.assertIn("not checked out", mixed.stderr)

    def test_rc_cli_refuses_dirty_tracked_dependency(self):
        commit = self.commit()
        # A dependency may change without changing its version selector; the clean-tree gate
        # still prevents validating its changed bytes and shipping the tagged originals.
        (self.root / "examples/example.json").write_text('{"specVersion":"0.3.0","tampered":true}\n')
        result = self.run_builder(commit)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("tracked release worktree is dirty", result.stderr)

    def test_prepared_rc_files_and_workflow_resolve_exact_notes(self):
        self.assertEqual(self.IDENTITY, json.loads((ROOT / f"releases/{self.TAG}.json").read_text()))
        self.assertEqual({"number": 2, "title": "v0.3.0"},
                         json.loads((ROOT / f"releases/{self.TAG}.milestone.json").read_text()))
        self.assertEqual(ROOT / f"releases/{self.TAG}.md", BUILD_RELEASE.core_release_notes_path(self.TAG))
        workflow = (ROOT / ".github/workflows/release.yml").read_text()
        self.assertIn('--notes-file "releases/${GITHUB_REF_NAME}.md"', workflow)
        notes = (ROOT / f"releases/{self.TAG}.md").read_text()
        self.assertIn("No preparation-verifier conformance claim", notes)
        self.assertIn("about one week", notes)


class CoreCarriedReleaseTests(unittest.TestCase):
    """v0.4.0 carries specVersion 0.3.0 unchanged: hand-authored trees, real tags, the builder CLI."""

    TAG = "v0.4.0"
    IDENTITY = {"releaseVersion": "0.4.0", "tag": TAG, "specVersion": "0.3.0",
                "maturity": "draft", "distribution": "specification-unchanged"}

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for directory in ("tools", "schema", "conformance/evaluation", "spec", "examples",
                          "releases", "catalog"):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "tools/build_release.py", self.root / "tools/build_release.py")
        for name in ("README.md", "LICENSE", "NOTICE", "CHANGELOG.md", "VERSIONING.md",
                     "TESTING.md", "SECURITY.md"):
            (self.root / name).write_text("Hand-authored release fixture.\n")
        (self.root / "spec/core.md").write_text("Core fixture, not a specification.\n")
        (self.root / "examples/example.json").write_text('{"specVersion":"0.3.0"}\n')
        (self.root / "catalog/record-shapes.json").write_text('{"format":"fixture"}\n')
        (self.root / "releases/v0.3.0.md").write_text("# Hand-authored earlier notes\n")
        for path, value in (
            ("conformance/manifest.json", {"specVersion": "0.3.0", "suiteVersion": "0.3.0", "status": "draft"}),
            ("conformance/evaluation/manifest.json", {"specVersion": "0.3.0", "suiteVersion": "0.3.0", "status": "draft"}),
            ("schema/judgment-pack-core.schema.json", {
                "$id": "https://judgmentpack.org/schema/0.3.0/judgment-pack-core.schema.json",
                "properties": {"specVersion": {"const": "0.3.0"}}}),
            (f"releases/{self.TAG}.json", self.IDENTITY),
        ):
            (self.root / path).write_text(json.dumps(value) + "\n")
        (self.root / f"releases/{self.TAG}.md").write_text("# Hand-authored notes\n")
        self.git("init", "--quiet")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, tag=None):
        self.git("add", "-A")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--quiet", "-s", "-m", "Hand-authored release fixture")
        commit = self.git("rev-parse", "HEAD")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "tag", "-a", tag or self.TAG, "-m", "Release fixture")
        return commit

    def run_builder(self, commit, tag=None):
        return subprocess.run([sys.executable, str(self.root / "tools/build_release.py"),
                               "--tag", tag or self.TAG, "--commit", commit,
                               "--output", str(self.root / "dist")], cwd=self.root,
                              capture_output=True, text=True)

    def fresh_case(self):
        case = CoreCarriedReleaseTests(methodName="runTest")
        case.setUp()
        self.addCleanup(case.doCleanups)
        return case

    def test_the_mapping_builds_both_archives_with_the_exact_identity(self):
        commit = self.commit()
        result = self.run_builder(commit)
        self.assertEqual(0, result.returncode, result.stderr)
        prefix = "judgment-pack-spec-0.4.0/"
        expected = {**self.IDENTITY, "sourceCommit": commit}
        tar = self.root / "dist/judgment-pack-spec_0.4.0_artifacts.tar.gz"
        zip_path = tar.with_name("judgment-pack-spec_0.4.0_artifacts.zip")
        with tarfile.open(tar) as archive:
            names = {m.name for m in archive.getmembers() if m.isfile()}
            self.assertEqual(expected, json.load(archive.extractfile(prefix + "release-identity.json")))
            self.assertEqual("0.3.0", json.load(archive.extractfile(prefix + "conformance/manifest.json"))["specVersion"])
        for member in (f"releases/{self.TAG}.json", f"releases/{self.TAG}.md", "catalog/record-shapes.json"):
            with self.subTest(member=member):
                self.assertIn(prefix + member, names)
        # Exactly this tag's two release files: no earlier notes, no tools, no milestone link.
        self.assertEqual({prefix + f"releases/{self.TAG}.json", prefix + f"releases/{self.TAG}.md"},
                         {name for name in names if name.startswith(prefix + "releases/")})
        self.assertEqual([], [name for name in names if name.startswith(prefix + "tools/")])
        with zipfile.ZipFile(zip_path) as archive:
            self.assertEqual(names, {n for n in archive.namelist() if not n.endswith("/")})
            self.assertEqual(expected, json.loads(archive.read(prefix + "release-identity.json")))
        self.assertEqual([hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name
                          for p in (tar, zip_path)],
                         (self.root / "dist/checksums.txt").read_text().splitlines())

    def test_a_missing_mapping_or_missing_notes_is_refused(self):
        for path, message in ((f"releases/{self.TAG}.json", "mapping is missing"),
                              (f"releases/{self.TAG}.md", "notes are missing")):
            with self.subTest(path=path):
                case = self.fresh_case()
                (case.root / path).unlink()
                result = case.run_builder(case.commit())
                self.assertNotEqual(0, result.returncode)
                self.assertIn(message, result.stderr)

    def test_a_tampered_mapping_is_refused(self):
        for changed in ({**self.IDENTITY, "specVersion": "0.4.0"},
                        {**self.IDENTITY, "specVersion": "0.2.0-draft"},
                        {**self.IDENTITY, "distribution": "release-candidate"},
                        {**self.IDENTITY, "maturity": "candidate"},
                        {**self.IDENTITY, "tag": "v0.4.1"},
                        {**self.IDENTITY, "releaseVersion": "0.3.0"},
                        {**self.IDENTITY, "extra": True},
                        {key: value for key, value in self.IDENTITY.items() if key != "distribution"},
                        []):
            with self.subTest(changed=changed):
                case = self.fresh_case()
                (case.root / f"releases/{self.TAG}.json").write_text(json.dumps(changed))
                result = case.run_builder(case.commit())
                self.assertNotEqual(0, result.returncode)
                self.assertIn("mapping does not match", result.stderr)

    def test_no_other_tag_can_use_the_mapping(self):
        for tag in ("v0.3.1", "v0.4.1", "v0.5.0", "v1.0.0", "v0.4.0-rc.1", "v0.4.0-alpha.1"):
            version = tag[1:]
            for mapping, message in (
                    # This tag's bytes copied under another tag's name; then renamed to fit it.
                    (self.IDENTITY, "only the allowlisted Core distributions"),
                    ({**self.IDENTITY, "releaseVersion": version, "tag": tag},
                     "only the allowlisted Core distributions"),
                    # And with no mapping at all, the tag's own version is held to the 0.3.0 pins.
                    (None, "conformance specVersion")):
                with self.subTest(tag=tag, mapping=mapping):
                    case = self.fresh_case()
                    (case.root / f"releases/{self.TAG}.json").unlink()
                    (case.root / f"releases/{self.TAG}.md").unlink()
                    (case.root / f"releases/{tag}.md").write_text("Wrong tag fixture notes\n")
                    if mapping is not None:
                        (case.root / f"releases/{tag}.json").write_text(json.dumps(mapping))
                    result = case.run_builder(case.commit(tag=tag), tag=tag)
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn(message, result.stderr)

    def test_the_catalog_and_the_mapping_join_this_tags_bundle_only(self):
        # bundle_paths reads the schema/ and conformance/ children from this repository's commit.
        current = BUILD_RELEASE.bundle_paths(self.TAG, "HEAD")
        self.assertIn("catalog", current)
        self.assertIn(f"releases/{self.TAG}.json", current)
        self.assertIn(f"releases/{self.TAG}.md", current)
        for path in ("tools/retained_column.py", "requirements-dev.txt", "rfcs",
                     "releases/v0.3.0.retained-column.json", "releases/v0.3.0.md"):
            with self.subTest(absent=path):
                self.assertNotIn(path, current)
        for tag in ("v0.3.0", "v0.3.0-rc.1", "v0.3.0-rc.2", "v0.3.1", "v0.5.0", "v0.2.0-draft",
                    "policy-v1.0.0-draft.1"):
            with self.subTest(tag=tag):
                paths = BUILD_RELEASE.bundle_paths(tag, "HEAD")
                self.assertNotIn("catalog", paths)
                self.assertNotIn(f"releases/{self.TAG}.json", paths)

    def test_a_tree_whose_core_moved_is_refused(self):
        # The route carries 0.3.0: a re-pinned Core under this tag is not this release.
        for path, keys, message in (
                ("conformance/manifest.json", ("specVersion",), "conformance specVersion"),
                ("conformance/manifest.json", ("suiteVersion",), "document corpus suiteVersion"),
                ("conformance/manifest.json", ("status",), "draft manifest maturity"),
                ("conformance/evaluation/manifest.json", ("specVersion",), "evaluation corpus specVersion"),
                ("conformance/evaluation/manifest.json", ("suiteVersion",), "evaluation corpus suiteVersion"),
                ("conformance/evaluation/manifest.json", ("status",), "draft manifest maturity"),
                ("schema/judgment-pack-core.schema.json", ("properties", "specVersion", "const"), "schema specVersion"),
                ("schema/judgment-pack-core.schema.json", ("$id",), "schema $id")):
            with self.subTest(path=path, keys=keys):
                case = self.fresh_case()
                value = json.loads((case.root / path).read_text())
                target = value
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = "0.4.0"
                (case.root / path).write_text(json.dumps(value))
                result = case.run_builder(case.commit())
                self.assertNotEqual(0, result.returncode)
                self.assertIn(message, result.stderr)

    def test_the_prepared_files_are_the_reviewed_identity(self):
        self.assertEqual(self.IDENTITY, BUILD_RELEASE.CORE_CARRIED_IDENTITY)
        self.assertEqual(self.IDENTITY, json.loads((ROOT / f"releases/{self.TAG}.json").read_text()))
        self.assertEqual({"number": 4, "title": "v0.4.0"},
                         json.loads((ROOT / f"releases/{self.TAG}.milestone.json").read_text()))
        # main carries Core 0.5.0 now, so the v0.4.0 identity is checked on a tree holding that tag's
        # pins, which are the v0.3.0 bytes the preserved copies keep, with this tag's own files.
        with tempfile.TemporaryDirectory() as directory:
            tree = Path(directory)
            v0_3_0_tree(tree, ("schema/judgment-pack-core.schema.json", "conformance/manifest.json",
                               "conformance/evaluation/manifest.json"))
            for name in (f"releases/{self.TAG}.json", f"releases/{self.TAG}.md"):
                (tree / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, tree / name)
            BUILD_RELEASE.validate_artifacts("0.4.0", self.TAG, root=tree)
            # The live tree is no v0.4.0 tree: its pins are 0.5.0's.
            with self.assertRaises(ValueError):
                BUILD_RELEASE.validate_artifacts("0.4.0", self.TAG)
        self.assertEqual("# v0.4.0", (ROOT / f"releases/{self.TAG}.md").read_text().splitlines()[0])
        try:
            attributes = subprocess.run(
                ["git", "check-attr", "export-ignore", "--", "catalog/record-shapes.json",
                 "catalog/format-status.json", "catalog/README.md", f"releases/{self.TAG}.json"],
                cwd=ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git cannot read attributes here: {error}")
        for line in attributes:
            with self.subTest(line=line):
                self.assertTrue(line.endswith(": export-ignore: unspecified"))

    def test_the_notes_state_what_a_consumer_needs(self):
        notes = re.sub(r"\s+", " ", (ROOT / f"releases/{self.TAG}.md").read_text(encoding="utf-8"))
        for text in ("carries `specVersion` `0.3.0` unchanged",
                     "/blob/v0.4.0/catalog/README.md",
                     "Packs keep declaring exact `specVersion` `0.3.0`",
                     "The tag name is not a selector.",
                     "Consumers pinned to `v0.3.0` need do nothing.",
                     "Stay on the `v0.3.0` bundle for the `retained-column/1` leaf.",
                     "## What is in the bundles", "They do not hold:",
                     "#249", "RFC 0030", "at Draft (#280)", "#256", "stays at Draft maturity (#142)",
                     "**Reader compatibility:**", "**Writer compatibility:**",
                     "**Semantic compatibility:**", "**Migration compatibility:**",
                     "## Migration note",
                     "https://judgmentpack.org/schema/0.4.0/workflow-contributors-2.schema.json` is not "
                     "published by this release",
                     "same-vendor review, not a cross-vendor claim"):
            with self.subTest(text=text):
                self.assertIn(text, notes)


if __name__ == "__main__":
    unittest.main()

"""The dialect vectors RFC 0018 stages, and the first reader written from the companion text.

The vectors are the reference Runner's `vectors/preparation/`, byte for byte, staged until the
next specVersion opens (conformance/dialect/README.md). These tests hold their bytes to the digests the Runner's
manifest gives them and the Runner's manifest and README to the digests this repository records;
run tools/dialect_verify.py, a preparation verifier written from spec/dialect.md, over every vector;
and hold the RFC's Specification section to the companion document's text.
"""

from __future__ import annotations

import collections
import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
DIALECT = ROOT / "conformance" / "dialect"
VECTORS = DIALECT / "vectors"
RFC = "rfcs/0018-dialect.md"
COMPANION = "spec/dialect.md"
SOURCE = {
    "repository": "https://github.com/Judgment-Pack/judgment-pack-runner",
    "pullRequest": 77,
    "commit": "05636eda96a9588279d61a6272625be859a28117",
    "path": "vectors/preparation",
    "mergedAs": "82116bfab7705f74ca3e493c9722dd3831c7418f",
    # The tenth vector, from the Runner's main after its pull request 80 (the amendment of
    # 2026-10-15); the eleventh and twelfth, of dialect version 3, from its main after its pull
    # request 83; and the twenty-six research vectors, of the two examples of §11's fixture plan,
    # from its main after its pull request 97.
    "extendedBy": [
        {
            "pullRequest": 80,
            "commit": "c84e8e64e5d30c835f8d8e6370cd48e2bfd35ee9",
            "vectors": ["http-shaped-source"],
        },
        {
            "pullRequest": 83,
            "commit": "89cf44109ad3a9862ab0386811bef63d8a9a1657",
            "vectors": ["version-3-bound", "unbound-bound-at-import"],
        },
        {
            "pullRequest": 97,
            "commit": "4352763e22489ca80ffbf5df338b7e7cb61319e2",
            "vectors": [
                "gtm-company-person-valid-types-all-six",
                "gtm-company-person-presence-optional-omitted",
                "gtm-company-person-presence-required-not-found",
                "gtm-company-person-presence-integer-zero",
                "gtm-company-person-presence-decimal-zero",
                "gtm-company-person-presence-boolean-false",
                "gtm-company-person-presence-text-empty",
                "gtm-company-person-stale-and-conflicting-unknown",
                "gtm-company-person-failed-fallback-all-unavailable",
                "gtm-company-person-failed-fallback-secondary-found",
                "gtm-company-person-changed-binding-second-installation",
                "gtm-company-person-changed-binding-old-preparation",
                "gtm-company-person-changed-response-retained-result",
                "work-item-triage-valid-types-all-six",
                "work-item-triage-presence-optional-omitted",
                "work-item-triage-presence-required-not-found",
                "work-item-triage-presence-integer-zero",
                "work-item-triage-presence-decimal-zero",
                "work-item-triage-presence-boolean-false",
                "work-item-triage-presence-text-empty",
                "work-item-triage-stale-and-conflicting-unknown",
                "work-item-triage-failed-fallback-all-unavailable",
                "work-item-triage-failed-fallback-secondary-found",
                "work-item-triage-changed-binding-second-installation",
                "work-item-triage-changed-binding-old-preparation",
                "work-item-triage-changed-response-record-fields",
            ],
        },
    ],
}
# The count as the RFC and the companion spell it.
WORDS = {9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 38: "thirty-eight"}
# The Runner's manifest says what each vector's export retains (its README, "What a vector holds"):
# `equal`, the preparation the Runner computes from the vector's inputs, which is preparation.json;
# `altered`, another, while preparation.json is still that computation; and `recorded`, the
# preparation the run recorded, held fixed as preparation.json, when the vector's inputs were
# changed after the run, so that no preparation can be computed from them
# (conformance/dialect/README.md).
RETAINED = {"equal", "altered", "recorded"}
FINDINGS = {
    "profile-mismatch",
    "parameter-invalid",
    "acquisition-missing",
    "acquisition-unexpected",
    "acquisition-invalid",
    "acquisition-stale",
    "acquisition-sessions",
    "calculation-invalid",
    "read-failed",
    "admission-refused",
    "preparation-differs",
    "record-inputs-differ",
    "binding-foreign-kind",
    "binding-mismatch",
    "unbound",
}
HEX_64 = re.compile(r"[0-9a-f]{64}")

_SPEC = importlib.util.spec_from_file_location("dialect_verify", ROOT / "tools" / "dialect_verify.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("could not load the first reader")
READER = importlib.util.module_from_spec(_SPEC)
# Its dataclasses resolve their annotations through the module, so it is registered first.
sys.modules[_SPEC.name] = READER
_SPEC.loader.exec_module(READER)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signer(seed: bytes) -> tuple[bytes, Any]:
    """An Ed25519 key of a test's own (RFC 8032, 5.1.5 and 5.1.6), on the first reader's arithmetic, so that a
    receipt can be signed again to reach the checks after its signature's. Held to RFC 8032's first test
    vector in the test that uses it."""
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little") & ((1 << 254) - 8) | (1 << 254)
    public = READER._encode(READER._multiply(a, READER.BASE))

    def sign(message: bytes) -> bytes:
        r = int.from_bytes(hashlib.sha512(h[32:] + message).digest(), "little") % READER.L
        encoded_r = READER._encode(READER._multiply(r, READER.BASE))
        k = int.from_bytes(hashlib.sha512(encoded_r + public + message).digest(), "little") % READER.L
        return encoded_r + ((r + k * a) % READER.L).to_bytes(32, "little")

    return public, sign


class Inputs:
    """One vector's files, given to a verifier as conformance/dialect/README.md says."""

    def __init__(self, name: str, require_binding: bool) -> None:
        directory = VECTORS / name
        # A vector of a dialect bound at import holds the published dialect, unbound.json, and its binding
        # document, binding.json, which a verifier is given; mapping.json is then the bound dialect (§4.4).
        imported = (directory / "binding.json").is_file()
        self.dialect = (directory / ("unbound.json" if imported else "mapping.json")).read_bytes()
        self.binding = (directory / "binding.json").read_bytes() if imported else None
        self.case = (directory / "case.json").read_bytes()
        sources = directory / "sources.json"
        self.acquisitions = sources.read_bytes() if sources.is_file() else b"{}"
        self.profiles = (directory / "profiles.json").read_bytes()
        run = (directory / "run.json").read_bytes()
        self.run = READER.read_document(run, "run.json")["run"]
        self.preparation = READER.preparation_bytes(self.run["input"]["preparation"])
        # run.auditBytes; or, in a version-2 export, run.audit exactly as run.json writes it (§11)
        self.record = READER.record_of_export(run)
        self.require_binding = require_binding

    def verify(self) -> Any:
        return READER.verify(
            self.dialect,
            self.case,
            self.acquisitions,
            self.profiles,
            self.preparation,
            self.record,
            self.require_binding,
            self.binding,
        )


REQUIRES_BINDING = {row["id"]: row["requiresBinding"] for row in json.loads((DIALECT / "manifest.json").read_text(encoding="utf-8"))["cases"]}


def altered_vector(
    name: str,
    profile: Any = None,
    dialect: Any = None,
    receipt: Any = None,
    request: Any = None,
    only: str | None = None,
) -> Inputs:
    """The vector's inputs altered: each profile, then the dialect, each source's profileDigest set to its
    profile's, then each receipt (with `only`, that source's alone), committed to `request` when one is given
    and signed again under a key of the test's own."""
    inputs = Inputs(name, REQUIRES_BINDING[name])
    public, sign = signer(b"the dialect tests' own key")
    profiles = json.loads(inputs.profiles)
    for item in profiles:
        if profile is not None:
            profile(item)
        item["publicKey"] = public.hex()
    digests = {
        item["id"]: READER.digest_of(READER.canon(READER.read_document(json.dumps(item).encode(), "a profile")))
        for item in profiles
    }
    document = json.loads(inputs.dialect)
    if dialect is not None:
        dialect(document)
    for source in document["sources"]:
        source["profileDigest"] = digests[source["profile"]]
    sources = json.loads(inputs.acquisitions)
    for source_name, member in sources.items():
        response = member["response"]
        signed = response["receipt"]
        if receipt is not None and only in (None, source_name):
            receipt(signed)
        if request is not None:
            salt = bytes.fromhex(response["salts"]["args"])
            signed["argumentsCommitment"] = READER.digest_of(salt + b"args:" + READER.canon(request))
        signed["keyId"] = hashlib.sha256(public).hexdigest()[:32]
        del signed["signature"]
        message = b"judgment-pack-gateway/receipt/3:" + READER.canon(READER.read_document(json.dumps(signed).encode(), "a receipt"))
        signed["signature"] = sign(message).hex()
    inputs.profiles = json.dumps(profiles).encode("utf-8")
    inputs.dialect = json.dumps(document).encode("utf-8")
    inputs.acquisitions = json.dumps(sources).encode("utf-8")
    return inputs


def vector_cases() -> list[tuple[str, str, Any]]:
    """Every staged vector as research_cases() gives a case, `(name, expected answer, build)`, its
    answer the row of this repository's manifest: tests/test_dialect_ts.py gives each to both
    readers and holds their reports equal, byte for byte."""
    cases: list[tuple[str, str, Any]] = []
    for row in json.loads((DIALECT / "manifest.json").read_text(encoding="utf-8"))["cases"]:
        if row["expectedResult"] == "reading":
            expected = "reading"
        else:
            expected = f"finding:{row['expectedFinding']}"

        def build(row: dict[str, Any] = row) -> Inputs:
            return Inputs(row["id"], row["requiresBinding"])

        cases.append((f"vector {row['id']}", expected, build))
    return cases


# Round 9 of RFC 0018 (issue #182 item 4; spec/dialect.md §5.2, check 1, and §11, finding 3): a receipt's
# `servedAt` or `acquisition.observedAt` that is not a string with an instant, a `callIndex` that is not an
# integer at least zero, or a `sessionId` that is not a string, is malformed, `acquisition-invalid`, before the
# time and session rules; `sessionId` is any string. Each receipt is signed again, so that the member named is
# the one change the checks after the signature's can see.
EXPIRED = {"valid": "2026-10-14T14:53:25Z", "version-3-bound": "2026-10-15T15:39:11Z"}  # 301 seconds old


def receipt_cases() -> list[tuple[str, str, Any]]:
    """Round 9's receipt answers on `operation` receipts, in dialect versions 2 (`valid`) and 3
    (`version-3-bound`) alike, and the session rule over two sources (`unsigned-parameters`), as `(name,
    expected answer, build)` in research_cases()'s form. Signed again, an acquisition whose checks all pass
    leaves the given preparation differing, `finding:preparation-differs`."""
    cases: list[tuple[str, str, Any]] = []
    invalid, differs = "finding:acquisition-invalid", "finding:preparation-differs"

    def add(name: str, expected: str, vector: str, change: Any, only: str | None = None) -> None:
        cases.append((f"{vector}: {name}", expected, lambda: altered_vector(vector, receipt=change, only=only)))

    def put(*path: str, value: Any = None, drop: bool = False) -> Any:
        def change(receipt: dict[str, Any]) -> None:
            *parents, last = path
            holder = receipt
            for key in parents:
                holder = holder[key]
            if drop:
                del holder[last]
            else:
                holder[last] = value

        return change

    for vector in ("valid", "version-3-bound"):
        add("servedAt a number", invalid, vector, put("servedAt", value=1760453906))
        add("servedAt null", invalid, vector, put("servedAt", value=None))
        add("servedAt absent", invalid, vector, put("servedAt", drop=True))
        add("servedAt a string of another form", invalid, vector, put("servedAt", value="2026-10-14T14:58:26.000Z"))
        add("observedAt a string that names no time", invalid, vector, put("acquisition", "observedAt", value="2026-02-30T14:58:26Z"))
        add("observedAt a number", invalid, vector, put("acquisition", "observedAt", value=0))
        add("callIndex a string", invalid, vector, put("callIndex", value="0"))
        add("callIndex below zero", invalid, vector, put("callIndex", value=-1))
        add("callIndex true", invalid, vector, put("callIndex", value=True))
        add("callIndex absent", invalid, vector, put("callIndex", drop=True))
        add("sessionId a number", invalid, vector, put("sessionId", value=0))
        add("sessionId null", invalid, vector, put("sessionId", value=None))
        add("sessionId absent", invalid, vector, put("sessionId", drop=True))
        # any string: not held to the gateway's token form
        add("sessionId empty", differs, vector, put("sessionId", value=""))
        add("sessionId of no token form", differs, vector, put("sessionId", value="a session, not a token: \u00fcn\u00efcode"))
        # a present instant outside the window is still stale; a malformed member beside it is the form first
        add("servedAt expired", "finding:acquisition-stale", vector, put("servedAt", value=EXPIRED[vector]))

        def expired_and_malformed(receipt: dict[str, Any], vector: str = vector) -> None:
            receipt["acquisition"]["observedAt"] = EXPIRED[vector]
            receipt["callIndex"] = "0"

        add("observedAt expired and callIndex a string: the form first", invalid, vector, expired_and_malformed)

        # review round of pull request 186: the time is read in `acquisition` alone; one moved to the receipt's
        # top level leaves `acquisition.observedAt` absent
        def misplaced(receipt: dict[str, Any]) -> None:
            receipt["observedAt"] = receipt["acquisition"].pop("observedAt")

        add("observedAt moved to the receipt's top level", invalid, vector, misplaced)
    # Two receipts, `vendor` at callIndex 0 and `registry` at 1 of one session: a well-formed set in neither form is
    # `acquisition-sessions`; a malformed member of the second receipt is `acquisition-invalid`.
    two = "unsigned-parameters"

    def session(sid: Any, index: Any) -> Any:
        return lambda r: r.update({"sessionId": sid, "callIndex": index})

    add("a second session whose call is not its first", "finding:acquisition-sessions", two, session("another.session", 1), "registry")
    add("one session, one callIndex twice", "finding:acquisition-sessions", two, session("mapping.session", 0), "registry")
    add("each alone in a session of its own, each its first call", differs, two, session("another.session", 0), "registry")
    add("the second receipt's callIndex a string", invalid, two, session("mapping.session", "1"), "registry")
    add("the second receipt's callIndex below zero", invalid, two, session("mapping.session", -1), "registry")
    add("the second receipt's sessionId a number", invalid, two, session(1, 1), "registry")
    return cases


class DialectVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((DIALECT / "manifest.json").read_text(encoding="utf-8"))
        cls.runner = json.loads((VECTORS / "manifest.json").read_text(encoding="utf-8"))
        cls.rows = {row["id"]: row for row in cls.manifest["cases"]}

    def inputs(self, name: str) -> Inputs:
        return Inputs(name, self.rows[name]["requiresBinding"])

    def test_manifest_names_its_status_proposal_and_source(self) -> None:
        self.assertEqual(
            {"status", "proposedBy", "source", "runnerFiles", "cases"}, set(self.manifest)
        )
        self.assertEqual("staged", self.manifest["status"])
        self.assertEqual(RFC, self.manifest["proposedBy"])
        self.assertTrue((ROOT / RFC).is_file())
        self.assertEqual(SOURCE, self.manifest["source"])
        self.assertEqual({"vectors/README.md", "vectors/manifest.json"}, set(self.manifest["runnerFiles"]))
        for row in self.manifest["cases"]:
            with self.subTest(row=row.get("id")):
                expected = {"id", "path", "requiresBinding", "expectedResult"}
                if row["expectedResult"] == "finding":
                    expected.add("expectedFinding")
                    self.assertIn(row["expectedFinding"], FINDINGS)
                else:
                    self.assertEqual("reading", row["expectedResult"])
                    expected.add("expectedBinding")
                    self.assertIn(row["expectedBinding"], {"matches", "absent", "not-checked"})
                self.assertEqual(expected, set(row))
                self.assertEqual(f"vectors/{row['id']}", row["path"])
                self.assertIsInstance(row["requiresBinding"], bool)

    def test_vectors_are_the_runners_bytes(self) -> None:
        # Every file is the Runner's: a vector's files to the digests the Runner's manifest gives,
        # and that manifest and the Runner's README to the digests recorded here, so a file added,
        # removed or changed by a byte fails.
        for relative, digest in self.manifest["runnerFiles"].items():
            with self.subTest(file=relative):
                self.assertIsNotNone(HEX_64.fullmatch(digest))
                self.assertEqual(digest, sha256(DIALECT / relative))
        listed = {"README.md", "manifest.json"}
        for vector in self.runner["vectors"]:
            for name, digest in vector["files"].items():
                relative = f"{vector['name']}/{name}"
                listed.add(relative)
                with self.subTest(file=relative):
                    self.assertEqual(digest, "sha256:" + sha256(VECTORS / relative))
        on_disk = {
            path.relative_to(VECTORS).as_posix() for path in VECTORS.rglob("*") if path.is_file()
        }
        self.assertEqual([], sorted(on_disk - listed), "files that the Runner's manifest names not")
        self.assertEqual([], sorted(listed - on_disk), "files that the Runner's manifest names, missing")

    def test_rows_name_the_runners_vectors_in_order(self) -> None:
        self.assertEqual(
            [vector["name"] for vector in self.runner["vectors"]],
            [row["id"] for row in self.manifest["cases"]],
        )
        for vector in self.runner["vectors"]:
            with self.subTest(vector=vector["name"]):
                self.assertEqual(
                    "--require-bound" in vector["verifyRun"]["arguments"],
                    self.rows[vector["name"]]["requiresBinding"],
                )

    def test_counts_match_the_manifest(self) -> None:
        count = len(self.manifest["cases"])
        statements = [
            ("conformance/dialect/README.md", f"This directory holds {count} vectors"),
            ("conformance/README.md", f"holds the reference Runner's {count} preparation vectors"),
            ("README.md", f"{count} dialect vectors"),
            ("rfcs/README.md", f"the reference Runner's {count} preparation vectors are staged"),
            (RFC, f"The vectors are the Runner's {WORDS[count]}, staged"),
        ]
        for relative, expected in statements:
            with self.subTest(file=relative):
                text = " ".join((ROOT / relative).read_text(encoding="utf-8").split())
                self.assertIn(expected, text)

    def test_the_companion_counts_the_vectors_of_the_commits_it_names(self) -> None:
        # The companion's Status names the Runner commits its vectors were copied from, and counts
        # the vectors of the commits it names: thirty-eight, from four commits, since the amendment
        # that staged the research vectors.
        text = " ".join((ROOT / COMPANION).read_text(encoding="utf-8").split())
        source = self.manifest["source"]
        self.assertIn(source["commit"], text)
        count = len(self.manifest["cases"]) - sum(len(e["vectors"]) for e in source["extendedBy"])
        count += sum(len(e["vectors"]) for e in source["extendedBy"] if e["commit"] in text)
        self.assertIn(f"Its {WORDS[count]} vectors", text)

    def test_the_first_reader_recomputes_every_preparation(self) -> None:
        # The preparation's canonical bytes, recomputed from the dialect, the case, the acquisitions
        # and the profiles at the vector's verifiedAt, are the Runner's, byte for byte. That instant
        # is the given preparation's in every vector but the two `changed-binding-old-preparation`,
        # whose export retains the first installation's preparation, of an earlier instant
        # (`altered`): there the reader is given preparation.json, of the vector's own. A vector
        # retained `recorded` is not recomputed: its inputs were changed after the run
        # (test_a_recorded_preparation_is_held_fixed).
        for vector in self.runner["vectors"]:
            name = vector["name"]
            with self.subTest(vector=name):
                expected = (VECTORS / name / "preparation.json").read_bytes()
                self.assertEqual(vector["verifiedAt"], json.loads(expected)["verifiedAt"])
                if vector["preparation"]["retained"] == "recorded":
                    continue
                inputs = self.inputs(name)
                if json.loads(inputs.preparation)["verifiedAt"] != vector["verifiedAt"]:
                    self.assertEqual("altered", vector["preparation"]["retained"])
                    inputs.preparation = expected
                outcome = inputs.verify()
                self.assertEqual(expected, outcome.preparation)
                self.assertEqual((VECTORS / name / "preparation.sha256").read_text(), outcome.digest)
                self.assertEqual(vector["preparation"]["sha256"], outcome.digest)
                self.assertEqual(
                    vector["preparation"]["binding"].encode("ascii"), READER.binding_of(outcome.digest)
                )

    def test_a_recorded_preparation_is_held_fixed(self) -> None:
        # `retained: "recorded"` (RETAINED): the vector's inputs were changed after the run, so no
        # preparation can be computed from them. Its preparation.json is the preparation the run
        # recorded, which the export retains: it is held to the digest and the binding the Runner's
        # manifest gives, as it is, and not recomputed. The reader gives the finding this
        # repository's manifest records, the code the Runner's refusal names, and computes no
        # preparation.
        recorded = []
        for vector in self.runner["vectors"]:
            name, retained = vector["name"], vector["preparation"]["retained"]
            with self.subTest(vector=name):
                self.assertIn(retained, RETAINED)
                if retained != "recorded":
                    continue
                recorded.append(name)
                held = (VECTORS / name / "preparation.json").read_bytes()
                digest = "sha256:" + hashlib.sha256(held).hexdigest()
                self.assertEqual(vector["preparation"]["sha256"], digest)
                self.assertEqual((VECTORS / name / "preparation.sha256").read_text(), digest)
                binding = vector["preparation"]["binding"].encode("ascii")
                self.assertEqual(binding, READER.binding_of(digest))
                inputs = self.inputs(name)
                self.assertEqual(held, inputs.preparation)
                row = self.rows[name]
                self.assertEqual("finding", row["expectedResult"])
                self.assertIn(f"({row['expectedFinding']})", vector["verifyRun"]["error"])
                outcome = inputs.verify()
                finding = outcome.answer.get("finding")
                self.assertEqual(row["expectedFinding"], finding, outcome.answer)
                self.assertIsNone(outcome.preparation)
        self.assertEqual(
            [
                "gtm-company-person-changed-response-retained-result",
                "work-item-triage-changed-response-record-fields",
            ],
            recorded,
        )

    def test_the_first_reader_gives_each_vector_its_answer(self) -> None:
        for row in self.manifest["cases"]:
            with self.subTest(vector=row["id"]):
                answer = self.inputs(row["id"]).verify().answer
                if row["expectedResult"] == "finding":
                    self.assertEqual(row["expectedFinding"], answer.get("finding"), answer)
                else:
                    self.assertIn("reading", answer, answer)
                    self.assertEqual(row["expectedBinding"], answer["reading"]["binding"])

    def test_readings_agree_with_the_runners_report_and_export(self) -> None:
        # Where the class reports what verify-run reports, the two agree; and the facts and
        # evidence-availability documents are the ones the Runner's export evaluated.
        compared = 0
        for vector in self.runner["vectors"]:
            name = vector["name"]
            if vector["preparation"]["retained"] == "recorded":
                continue  # nothing is computed from inputs changed after the run
            inputs = self.inputs(name)
            outcome = inputs.verify()
            with self.subTest(vector=name):
                self.assertEqual(READER.as_plain(inputs.run["input"]["facts"]), outcome.facts)
                self.assertEqual(READER.as_plain(inputs.run["input"]["evidence"]), outcome.evidence)
            report = json.loads(vector["verifyRun"]["report"]) if vector["verifyRun"]["report"] else None
            if "reading" not in outcome.answer or report is None or "targetsByClass" not in report:
                continue
            reading = outcome.answer["reading"]
            for member in ("targetsByClass", "unsignedParameters", "unsignedFreshness"):
                with self.subTest(vector=name, member=member):
                    self.assertEqual(report.get(member), reading.get(member))
            with self.subTest(vector=name, member="binding"):
                self.assertEqual(report["binding"]["status"], reading["binding"])
            compared += 1
        self.assertGreaterEqual(compared, 4)

    # Controls: what the first reader must not accept. They are this repository's checks of one
    # reader, with altered copies of a vector, and not vectors (RFC 0018, Conformance).

    def test_a_reader_that_writes_minus_zero_as_zero_fails_numeric_spellings(self) -> None:
        def normalising(value: Any) -> str:
            return str(int(value.literal)) if isinstance(value, READER.Num) else str(value)

        with mock.patch.object(READER, "write_number", normalising):
            valid = self.inputs("valid").verify()
            numeric = self.inputs("numeric-spellings").verify()
        self.assertEqual((VECTORS / "valid" / "preparation.json").read_bytes(), valid.preparation)
        self.assertNotEqual(
            (VECTORS / "numeric-spellings" / "preparation.json").read_bytes(), numeric.preparation
        )
        # Such a reader writes the given preparation as it writes its own, so the two agree; the
        # record's binding, the Runner's digest of the bytes as written, is what refuses it.
        self.assertEqual("binding-mismatch", numeric.answer.get("finding"))

    def test_a_reader_that_writes_ampersand_raw_fails_escaped_strings(self) -> None:
        raw = {k: v for k, v in READER._PREPARATION_ESCAPES.items() if k not in "&<>"}
        with mock.patch.object(READER, "_PREPARATION_ESCAPES", raw):
            valid = self.inputs("valid").verify()
            escaped = self.inputs("escaped-strings").verify()
        self.assertEqual((VECTORS / "valid" / "preparation.json").read_bytes(), valid.preparation)
        self.assertNotEqual(
            (VECTORS / "escaped-strings" / "preparation.json").read_bytes(), escaped.preparation
        )

    def test_a_result_changed_by_a_byte_is_not_verified(self) -> None:
        inputs = self.inputs("valid")
        sources = json.loads(inputs.acquisitions)
        sources["fx"]["response"]["result"]["facts"]["request"]["completeness"] = "complets"
        inputs.acquisitions = json.dumps(sources).encode("utf-8")
        self.assertEqual("acquisition-invalid", inputs.verify().answer.get("finding"))

    def test_an_instant_past_the_maximum_age_is_stale(self) -> None:
        inputs = self.inputs("valid")
        preparation = json.loads(inputs.preparation)
        preparation["verifiedAt"] = "2026-10-14T15:03:27Z"  # 301 seconds after the acquisition
        inputs.preparation = json.dumps(preparation).encode("utf-8")
        self.assertEqual("acquisition-stale", inputs.verify().answer.get("finding"))

    def test_a_profile_other_than_the_one_the_dialect_names_is_a_mismatch(self) -> None:
        inputs = self.inputs("valid")
        profiles = json.loads(inputs.profiles)
        profiles[0]["endpoint"] = "postgresql://another"
        inputs.profiles = json.dumps(profiles).encode("utf-8")
        self.assertEqual("profile-mismatch", inputs.verify().answer.get("finding"))

    def test_a_record_of_other_inputs_is_not_the_preparations(self) -> None:
        # The record must have evaluated the facts, the evidence and the citations the preparation
        # derived; its binding alone would still match, so each is altered with the binding kept.
        for alteration in (
            (b'"type":"data-access"}},"evidence"', b'"type":"data-accesS"}},"evidence"'),
            (b'"intake-form":"present","sponsor', b'"intake-form":"absent","sponsor'),
            (b'"callIndex":0,"signature":"d9af', b'"callIndex":1,"signature":"d9af'),
        ):
            with self.subTest(alteration=alteration[1]):
                inputs = self.inputs("valid")
                self.assertIn(alteration[0], inputs.record)
                inputs.record = inputs.record.replace(*alteration)
                self.assertEqual("record-inputs-differ", inputs.verify().answer.get("finding"))

    # The review round's probes (pull request 144), one test each.

    def test_an_absent_binding_is_unbound_and_a_null_one_is_foreign(self) -> None:
        # Findings 7 and 8 are of a record that carries a binding; absence is not null.
        member = b',"binding":{"kind":"judgment-pack-runner/preparation/1","digest":"sha256:2a058ca1490ee316a87ad5999a7460906699a6f8987c93369a344ae4614b7a6d"}'
        inputs = self.inputs("valid")
        self.assertIn(member, inputs.record)
        inputs.record = inputs.record.replace(member, b"")
        self.assertEqual("unbound", inputs.verify().answer.get("finding"))
        inputs.require_binding = False
        self.assertEqual("absent", inputs.verify().answer["reading"]["binding"])
        inputs.record = self.inputs("valid").record.replace(member, b',"binding":null')
        self.assertEqual("binding-foreign-kind", inputs.verify().answer.get("finding"))

    def test_a_citation_given_twice_is_one_member_of_the_set(self) -> None:
        inputs = self.inputs("valid")
        start = inputs.record.index(b'"cites":[') + len(b'"cites":[')
        end = inputs.record.index(b"]", start)
        citation = inputs.record[start:end]
        inputs.record = inputs.record[:start] + citation + b"," + citation + inputs.record[end:]
        self.assertEqual("matches", inputs.verify().answer["reading"]["binding"])

    def test_a_result_nested_too_deep_is_over_a_bound_before_its_receipt_is_read(self) -> None:
        inputs = self.inputs("valid")
        sources = json.loads(inputs.acquisitions)
        nested: Any = "deep"
        for _ in range(33):
            nested = [nested]
        sources["fx"]["response"]["result"] = nested
        inputs.acquisitions = json.dumps(sources).encode("utf-8")
        self.assertEqual("input-over-bound", inputs.verify().answer.get("refused"))

    def test_a_bound_on_bytes_comes_before_a_document_that_is_not_json(self) -> None:
        inputs = self.inputs("escaped-strings")
        inputs.dialect = b"{"
        inputs.case = b"[" * 33 + b"]" * 33
        self.assertEqual("input-over-bound", inputs.verify().answer.get("refused"))

    def test_a_source_of_an_unread_kind_is_held_to_its_form_first(self) -> None:
        inputs = self.inputs("escaped-strings")
        dialect = json.loads(inputs.dialect)
        dialect["sources"] = [{"name": "upload", "kind": "selected-file", "provider": "a-floppy-disk"}]
        inputs.dialect = json.dumps(dialect).encode("utf-8")
        self.assertEqual("input-malformed", inputs.verify().answer.get("refused"))

    def _with_rule_condition(self, alter: Any) -> Any:
        inputs = self.inputs("unsigned-parameters")
        dialect = json.loads(inputs.dialect)
        alter(dialect["sources"][0]["read"]["rule"]["clauses"][0]["when"]["of"])
        inputs.dialect = json.dumps(dialect).encode("utf-8")
        return inputs.verify().answer

    def test_rule_members_of_another_type_are_malformed(self) -> None:
        # equalsParam is the first condition of the vendor rule's first clause, freshWithin the second.
        probes = {
            "op": lambda of: of[0].__setitem__("op", ["equalsParam"]),
            "equalsParam.param": lambda of: of[0].__setitem__("param", ["vendorId"]),
            "freshWithin.asOf": lambda of: of[1].__setitem__("asOf", {"name": "runAt"}),
        }
        for name, alter in probes.items():
            with self.subTest(member=name):
                self.assertEqual("input-malformed", self._with_rule_condition(alter).get("refused"))

    def test_every_condition_member_of_another_type_is_refused_not_raised(self) -> None:
        # Each member of each condition the vectors use, given a value of each other JSON type:
        # the reading is refused or ends at a finding, and never raises.
        for index, members in ((0, ("op", "field", "param")), (1, ("op", "field", "asOf", "maxAge"))):
            for member in members:
                for value in ([], {}, 1, None, True, ["x"], {"x": 1}):
                    def alter(of: Any, index: int = index, member: str = member, value: Any = value) -> None:
                        of[index][member] = value

                    with self.subTest(condition=index, member=member, value=value):
                        answer = self._with_rule_condition(alter)
                        self.assertTrue({"refused", "finding"} & set(answer), answer)

    def test_a_fresh_within_of_another_declared_type_is_false_not_malformed(self) -> None:
        # Found by the independent reader's round (#145): §6.3 makes `asOf`'s `timestamp` and
        # `maxAge`'s `integer` part of the condition's truth, and names no declared type's mismatch
        # among the forms that refuse a dialect. Over the valid vector's inputs, a rule whose
        # freshWithin names a declared `string` as `asOf` derives its last clause's claim, so the
        # reading ends in preparation-differs, not input-malformed.
        inputs = self.inputs("valid")
        dialect = json.loads(inputs.dialect)
        dialect["sources"][0]["read"] = {
            "rule": {
                "ruleVersion": "1",
                "parameters": {"invoiceCurrency": "string", "invoiceAmount": "string"},
                "clauses": [
                    {
                        "when": {
                            "op": "freshWithin",
                            "field": "/calculation/asOf/ecb-rates",
                            "asOf": "invoiceCurrency",
                            "maxAge": "invoiceAmount",
                        },
                        "claim": {
                            "facts": [{"pointer": "/request", "from": "/facts/request"}],
                            "evidence": {"intake-form": "present"},
                            "acquisitionStatus": "resolved",
                        },
                        "reason": "fresh",
                    },
                    {
                        "when": {"op": "always"},
                        "claim": {"facts": [], "evidence": {"intake-form": "unknown"}, "acquisitionStatus": "unknown"},
                        "reason": "not-fresh",
                    },
                ],
            }
        }
        inputs.dialect = json.dumps(dialect).encode("utf-8")
        outcome = inputs.verify()
        self.assertEqual("preparation-differs", outcome.answer.get("finding"), outcome.answer)
        preparation = json.loads(outcome.preparation)
        fx = next(o for o in preparation["outcomes"] if o["name"] == "fx")
        self.assertEqual("not-fresh", fx["reason"])
        self.assertEqual(["/calculation/asOf/ecb-rates"], fx["claim"]["basis"])

        # The condition itself, with each type isolated: true only for a timestamp and an integer.
        def fresh(declared: dict[str, str]) -> str:
            rule = {
                "ruleVersion": "1",
                "parameters": declared,
                "clauses": [
                    {
                        "when": {"op": "freshWithin", "field": "/at", "asOf": "stamp", "maxAge": "window"},
                        "claim": {"facts": [], "evidence": {}, "acquisitionStatus": "resolved"},
                        "reason": "fresh",
                    },
                    {
                        "when": {"op": "always"},
                        "claim": {"facts": [], "evidence": {}, "acquisitionStatus": "unknown"},
                        "reason": "not-fresh",
                    },
                ],
            }
            scope = {"stamp": "2026-10-14T14:58:26Z", "window": READER.Num("300")}
            return READER.rule_claim(rule, {"at": "2026-10-14T14:58:00Z"}, scope)["reason"]

        self.assertEqual("fresh", fresh({"stamp": "timestamp", "window": "integer"}))
        self.assertEqual("not-fresh", fresh({"stamp": "string", "window": "integer"}))
        self.assertEqual("not-fresh", fresh({"stamp": "timestamp", "window": "string"}))

    def test_a_long_index_token_names_no_element(self) -> None:
        token = "1" + "0" * 4999
        self.assertIs(READER.ABSENT, READER.resolve([], "/" + token))
        self.assertIs(READER.ABSENT, READER.resolve([[]], "/0/" + token))
        self.assertEqual("x", READER.resolve(["a"] * 10 + ["x"], "/10"))
        self.assertIs(READER.ABSENT, READER.resolve(["a"] * 10, "/10"))
        claim = READER.copy_claim({"facts": [{"target": "/x", "source": "/" + token}], "evidence": []}, [])
        self.assertEqual({}, claim["facts"])
        inputs = self.inputs("escaped-strings")
        dialect = json.loads(inputs.dialect)
        dialect["case"]["facts"] = [{"target": "/request", "source": "/" + token}]
        inputs.dialect, inputs.case = json.dumps(dialect).encode("utf-8"), b"[]"
        self.assertEqual("preparation-differs", inputs.verify().answer.get("finding"))

    def test_a_key_of_small_order_is_refused(self) -> None:
        inputs = self.inputs("valid")
        profiles = json.loads(inputs.profiles)
        profiles[0]["publicKey"] = "00" * 32
        inputs.profiles = json.dumps(profiles).encode("utf-8")
        self.assertEqual("input-malformed", inputs.verify().answer.get("refused"))

    def test_an_integer_parameter_written_with_a_fraction_is_invalid(self) -> None:
        inputs = self.inputs("numeric-spellings")
        inputs.case = inputs.case.replace(b'"zero":-0', b'"zero":0.0')
        self.assertEqual("parameter-invalid", inputs.verify().answer.get("finding"))

    def test_a_kind_without_vectors_is_not_read(self) -> None:
        inputs = self.inputs("escaped-strings")
        dialect = json.loads(inputs.dialect)
        dialect["sources"] = [{"name": "upload", "kind": "selected-file", "provider": "local-file", "read": {"copy": {"facts": [], "evidence": []}}}]
        inputs.dialect = json.dumps(dialect).encode("utf-8")
        self.assertEqual("kind-unread", inputs.verify().answer.get("refused"))
        dialect["sources"][0]["kind"] = "research"
        inputs.dialect = json.dumps(dialect).encode("utf-8")
        self.assertEqual("input-malformed", inputs.verify().answer.get("refused"))

    # The shapes of an `operation` (§4.1, §5.2) and version 3 (§11), from the amendment of 2026-10-15. Written
    # by its author, who wrote the second reader's extension too.

    def _altered(
        self,
        name: str,
        profile: Any = None,
        dialect: Any = None,
        receipt: Any = None,
        request: Any = None,
    ) -> Inputs:
        return altered_vector(name, profile, dialect, receipt, request)

    def _with_arguments(self, arguments: Any, parameters: Any = None) -> Any:
        inputs = self.inputs("http-shaped-source")
        document = json.loads(inputs.dialect)
        document["sources"][0]["arguments"] = arguments
        if parameters is not None:
            document["case"]["parameters"].update(parameters)
        inputs.dialect = json.dumps(document).encode("utf-8")
        return inputs.verify().answer

    def test_the_test_signer_is_rfc_8032s(self) -> None:
        public, sign = signer(bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"))
        self.assertEqual("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", public.hex())
        self.assertEqual(
            "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b",
            sign(b"").hex(),
        )
        self.assertTrue(READER.signature_verifies(public, b"", sign(b"")))

    def test_the_tenth_vectors_request_is_adapter_https(self) -> None:
        outcome = self.inputs("http-shaped-source").verify()
        intake = json.loads(outcome.preparation)["outcomes"][1]
        self.assertEqual({"method": "GET", "path": "/intake/requests", "query": {"id": "REQ-7"}}, intake["arguments"])

    def test_a_request_that_does_not_fit_its_profile_is_a_mismatch(self) -> None:
        def shape(value: str, tools: Any = None) -> Any:
            def alter(profile: dict[str, Any]) -> None:
                profile["shape"] = value
                profile.pop("tools", None)
                if tools is not None:
                    profile["tools"] = tools

            return alter

        # the http request under a profile of shape mcp, and under one of shape command, which serves none
        for profile in (shape("mcp", ["requests"]), shape("command")):
            answer = self._altered("http-shaped-source", profile=profile).verify().answer
            self.assertEqual("profile-mismatch", answer.get("finding"), answer)
        # under mcp, a request is exactly a tool call
        for arguments in (
            {"tool": "requests", "arguments": {"id": {"$param": "requestId"}}, "path": "/intake/requests"},
            {"tool": "requests"},
            {"tool": {"$param": "requestId"}, "arguments": {}},
        ):
            with self.subTest(arguments=arguments):
                answer = self._altered(
                    "http-shaped-source",
                    profile=shape("mcp", ["requests"]),
                    dialect=lambda d, a=arguments: d["sources"][0].__setitem__("arguments", a),
                ).verify().answer
                self.assertEqual("profile-mismatch", answer.get("finding"), answer)

    def test_an_http_request_is_an_object_held_to_its_commitment_not_to_a_member_set(self) -> None:
        # not an object, a template form, or outside the template rules: refused with the dialect
        for arguments in ("/intake/requests", [], {"$param": "requestId"}, {"path": {"$param": "nope"}}, {"path": {"$param": "runAt"}}):
            with self.subTest(arguments=arguments):
                self.assertEqual("input-malformed", self._with_arguments(arguments).get("refused"))
        # any other object is of the form, and the receipt does not commit it (§5.2, check 4)
        for arguments in (
            {"path": "/intake/requests", "method": "GET", "query": {"id": "REQ-8"}},
            {"path": "/intake/requests", "method": "GET"},
            {"path": "/intake/requests", "method": "PUT", "query": {"id": "REQ-7"}},
            {"path": "/intake/requests", "method": "POST", "query": {"id": "REQ-7"}, "body": {"id": "REQ-7"}},
            {"tool": "requests", "arguments": {"id": {"$param": "requestId"}}},
            {},
        ):
            with self.subTest(arguments=arguments):
                self.assertEqual("acquisition-invalid", self._with_arguments(arguments).get("finding"))
        # under adapter-http, a query is an object of string templates
        for query in ({"id": 7}, {"id": True}, {"id": ["REQ-7"]}, {"$param": "requestId"}, "id=REQ-7"):
            with self.subTest(query=query):
                arguments = {"path": "/intake/requests", "method": "GET", "query": query}
                self.assertEqual("profile-mismatch", self._with_arguments(arguments).get("finding"))
        integer = {"n": {"pointer": "/n", "type": "integer"}}
        query = {"path": "/intake/requests", "method": "GET", "query": {"id": {"$param": "n"}}}
        self.assertEqual("profile-mismatch", self._with_arguments(query, integer).get("finding"))
        # a $text is a string template; the case has no /n, so the reading ends at the case's parameter
        query["query"]["id"] = {"$text": "REQ-{{n}}"}
        self.assertEqual("parameter-invalid", self._with_arguments(query, integer).get("finding"))

    def test_a_connections_request_is_read_under_its_own_adapter(self) -> None:
        # The form a gateway connection takes (adapters/README.md), whose `query` is a WIQL string: read
        # under a profile of shape http whose adapter is the connection's; under adapter-http, its query
        # is of another form.
        request = {
            "connection": "board",
            "revision": "0" * 64,
            "read": "workitems.query",
            "query": "SELECT [System.Id] FROM WorkItems",
            "top": 50,
        }

        def adapter(name: str) -> Any:
            return lambda p: p["adapter"].__setitem__("name", name)

        def receipt(name: str) -> Any:
            return lambda r: r["acquisition"]["adapter"].__setitem__("name", name)

        def with_request(d: dict[str, Any]) -> None:
            d["sources"][0]["arguments"] = dict(request)

        answer = self._altered(
            "http-shaped-source", profile=adapter("adapter-sources"), dialect=with_request, receipt=receipt("adapter-sources"), request=request
        ).verify().answer
        self.assertEqual("preparation-differs", answer.get("finding"), answer)
        answer = self._altered("http-shaped-source", dialect=with_request, request=request).verify().answer
        self.assertEqual("profile-mismatch", answer.get("finding"), answer)

    def test_the_records_shape_is_the_profiles(self) -> None:
        answer = self._altered("http-shaped-source").verify().answer
        self.assertEqual("preparation-differs", answer.get("finding"), answer)  # signed again, every check passes
        for shape in ("mcp", "airbyte"):
            with self.subTest(shape=shape):
                answer = self._altered(
                    "http-shaped-source", receipt=lambda r, shape=shape: r["acquisition"].__setitem__("shape", shape)
                ).verify().answer
                self.assertEqual("acquisition-invalid", answer.get("finding"), answer)

    def test_a_receipt_that_attests_a_page_is_not_read_whatever_the_shape(self) -> None:
        def paged(receipt: dict[str, Any]) -> None:
            receipt["acquisition"]["pageItems"] = [receipt["resultDigest"]]

        for name in ("http-shaped-source", "valid"):
            with self.subTest(vector=name):
                answer = self._altered(name, receipt=paged).verify().answer
                self.assertEqual("acquisition-invalid", answer.get("finding"), answer)

    def test_a_receipt_member_of_another_form_is_invalid_before_the_time_and_session_rules(self) -> None:
        # Round 9 (issue #182 item 4) on operation receipts, in versions 2 and 3: receipt_cases(), which the
        # cross-reader test gives the second reader too.
        for name, expected, build in receipt_cases():
            with self.subTest(case=name):
                answer = build().verify().answer
                self.assertEqual(expected, answer_code(answer), answer.get("detail"))

    def test_a_paged_mcp_receipt_is_refused_the_amendments_one_restriction(self) -> None:
        # Review round 5, finding 1: a signed acquisition of shape mcp whose receipt carries pageItems was
        # read under the accepted text; the amendment refuses it (§5.2), the one answer it changes for an
        # input that was read before. The valid vector, signed again: without the page every check passes,
        # with it the acquisition is refused.
        unpaged = self._altered("valid").verify().answer
        self.assertEqual("preparation-differs", unpaged.get("finding"), unpaged)
        paged = self._altered(
            "valid", receipt=lambda r: r["acquisition"].__setitem__("pageItems", [r["resultDigest"]])
        ).verify().answer
        self.assertEqual("acquisition-invalid", paged.get("finding"), paged)

    def test_a_stream_read_under_an_airbyte_profile_is_read_as_its_shape_gives_it(self) -> None:
        def as_airbyte(stream: dict[str, Any], paged: bool) -> Any:
            def receipt(r: dict[str, Any]) -> None:
                r["acquisition"]["shape"] = "airbyte"
                if paged:
                    r["acquisition"]["pageItems"] = []

            return self._altered(
                "http-shaped-source",
                profile=lambda p: p.__setitem__("shape", "airbyte"),
                dialect=lambda d: d["sources"][0].__setitem__("arguments", dict(stream)),
                receipt=receipt,
                request=stream,
            ).verify().answer

        # adapter-airbyte's stream read, and an object of other members: the request is not a member set
        for stream in ({"stream": "requests", "namespace": None, "limit": 10}, {"stream": "requests", "syncMode": "full_refresh"}):
            with self.subTest(stream=stream):
                self.assertEqual("preparation-differs", as_airbyte(stream, False).get("finding"))
                self.assertEqual("acquisition-invalid", as_airbyte(stream, True).get("finding"))

    # Dialect version 3 (§4.3, §4.4, §9.1), from the Runner's eleventh and twelfth vectors. Written by the author
    # who extended both readers to it, as the amendment of 2026-10-15's author extended both before.

    def test_a_dialect_of_version_3_is_read_and_its_form_checked(self) -> None:
        def answer(alter: Any, case: bytes | None = None) -> Any:
            inputs = self.inputs("http-shaped-source")
            document = json.loads(inputs.dialect)
            alter(document)
            inputs.dialect = json.dumps(document).encode("utf-8")
            if case is not None:
                inputs.case = case
            return inputs.verify().answer

        def unbound(document: dict[str, Any]) -> None:
            source = document["sources"][0]
            del source["profile"], source["profileDigest"]
            source.update({"platform": "intake", "operation": "requests", "shape": "http", "record": "adapter-http"})

        def version(value: Any) -> Any:
            return lambda d: d.__setitem__("version", value)

        def version_3(document: dict[str, Any]) -> None:
            # written as version 3 is: without the members of version 2 alone (§2)
            document["version"] = 3
            for member in ("provider", "facts", "evidence"):
                document.pop(member, None)

        # read, as version 3: its preparation is another, of version 3 and another digest
        self.assertEqual("preparation-differs", answer(version_3).get("finding"))
        # its form is checked: the members of version 2 alone, an unbound source with no binding document,
        # and a member of no form
        self.assertEqual("input-malformed", answer(version(3)).get("refused"))
        self.assertEqual("input-malformed", answer(lambda d: (unbound(d), version_3(d))).get("refused"))
        self.assertEqual("input-malformed", answer(lambda d: (version_3(d), d.update({"Version": "x"}))).get("refused"))
        # an unbound source in a version-2 dialect; versions this document does not define
        self.assertEqual("input-malformed", answer(unbound).get("refused"))
        self.assertEqual("input-malformed", answer(version(4)).get("refused"))
        self.assertEqual("input-malformed", answer(version("3")).get("refused"))
        # the bounds before it come first
        self.assertEqual("input-over-bound", answer(version_3, b"[" * 33 + b"]" * 33).get("refused"))

    def test_the_vector_bound_at_import_is_the_runners_import(self) -> None:
        # The Runner's manifest marks each vector of a dialect bound at import and says which file
        # is which; those are the vectors that hold a binding document, and the ones this repository
        # reads unbound.json of. Each one's bound dialect, made of unbound.json and binding.json
        # (§4.4), is its mapping.json.
        for vector in self.runner["vectors"]:
            with self.subTest(vector=vector["name"]):
                directory = VECTORS / vector["name"]
                held = (directory / "binding.json").is_file()
                self.assertEqual(held, "import" in vector)
                if held:
                    self.assertEqual(
                        {"published": "unbound.json", "binding": "binding.json", "bound": "mapping.json"}, vector["import"]
                    )
                    def document(file: str) -> Any:
                        return READER.read_document((directory / file).read_bytes(), file)

                    unbound, mapping = document("unbound.json"), document("mapping.json")
                    binding = READER.parse_binding(document("binding.json"))
                    self.assertEqual(READER.digest_of(READER.canon(unbound)), binding["dialect"])
                    bound = READER.bind(unbound, binding)
                    self.assertEqual(READER.canon(mapping), READER.canon(bound))

    def test_the_bound_dialect_is_the_vectors_mapping_and_the_preparation_commits_it_alone(self) -> None:
        directory = VECTORS / "unbound-bound-at-import"
        unbound = READER.read_document((directory / "unbound.json").read_bytes(), "unbound.json")
        binding = READER.parse_binding(READER.read_document((directory / "binding.json").read_bytes(), "binding.json"))
        mapping = READER.read_document((directory / "mapping.json").read_bytes(), "mapping.json")
        self.assertEqual(READER.digest_of(READER.canon(unbound)), binding["dialect"])
        self.assertEqual(READER.canon(mapping), READER.canon(READER.bind(unbound, binding)))
        preparation = (directory / "preparation.json").read_bytes()
        self.assertIn(b'"mappingDigest":"' + READER.digest_of(READER.canon(mapping)).encode() + b'"', preparation)
        self.assertIn(b'"version":3}', preparation)
        # neither the published dialect's digest, nor the binding document's, nor the catalog names (§4.4)
        for absent in (binding["dialect"], READER.digest_of(READER.canon(binding)), "intake-api", "requests.read"):
            self.assertNotIn(absent.encode(), preparation)
        # The bound dialect given as the dialect, with no binding document, is a version-3 document with no
        # unbound source, and is read alike.
        inputs = self.inputs("unbound-bound-at-import")
        inputs.dialect, inputs.binding = (directory / "mapping.json").read_bytes(), None
        outcome = inputs.verify()
        self.assertEqual("matches", outcome.answer["reading"]["binding"], outcome.answer)
        self.assertEqual(preparation, outcome.preparation)

    def test_a_version_3_document_is_read_as_version_2s_its_preparation_of_version_3(self) -> None:
        # version-3-bound is the valid case's mapping written as version 3. Read as a document of version 2, its
        # preparation differs in its version and its digest, and in nothing else (§9.1).
        inputs = self.inputs("version-3-bound")
        document = json.loads(inputs.dialect)
        document["version"] = 2
        inputs.dialect = json.dumps(document).encode("utf-8")
        outcome = inputs.verify()
        self.assertEqual("preparation-differs", outcome.answer.get("finding"), outcome.answer)
        given = json.loads((VECTORS / "version-3-bound" / "preparation.json").read_bytes())
        recomputed = json.loads(outcome.preparation)
        self.assertEqual(2, recomputed["version"])
        self.assertEqual(READER.digest_of(READER.canon(READER.read_document(inputs.dialect, "the dialect"))), recomputed["mappingDigest"])
        for member in ("version", "mappingDigest"):
            del given[member], recomputed[member]
        self.assertEqual(given, recomputed)

    def test_cites_are_ordered_by_call_index_in_versions_2_and_3(self) -> None:
        # §9.1: in versions 2 and 3 alike, `cites` is ordered by callIndex, as the Runner writes it (review round
        # 7, finding 1). The two sources of unsigned-parameters, vendor then registry, their receipts' callIndex
        # swapped and signed again: in the order of sources the indices are [1, 0], and `cites` is [0, 1].
        for version, expected in ((2, ["registry", "vendor"]), (3, ["registry", "vendor"])):
            with self.subTest(version=version):
                def written(d: dict[str, Any], v: int = version) -> None:
                    d["version"] = v
                    if v == 3:  # without the members of version 2 alone (§2)
                        for member in ("provider", "facts", "evidence"):
                            d.pop(member, None)

                inputs = self._altered(
                    "unsigned-parameters",
                    dialect=written,
                    receipt=lambda r: r.__setitem__("callIndex", 1 - r["callIndex"]),
                )
                outcome = inputs.verify()
                self.assertEqual("preparation-differs", outcome.answer.get("finding"), outcome.answer)
                preparation = json.loads(outcome.preparation)
                receipts = {entry["source"]: entry["receipt"] for entry in preparation["lineage"] if "receipt" in entry}
                order = [next(name for name, receipt in receipts.items() if receipt == c) for c in preparation["cites"]]
                self.assertEqual(expected, order)
                self.assertEqual([1, 0], [receipts[name]["callIndex"] for name in ("vendor", "registry")])
                self.assertEqual([0, 1], [c["callIndex"] for c in preparation["cites"]])

    def _imported(self, unbound: Any = None, binding: Any = None) -> Inputs:
        """The import vector's inputs, its published dialect altered and the binding document's `dialect` written
        again as its digest; then the binding document altered."""
        inputs = self.inputs("unbound-bound-at-import")
        document = json.loads(inputs.dialect)
        if unbound is not None:
            unbound(document)
        inputs.dialect = json.dumps(document).encode("utf-8")
        written = json.loads(inputs.binding)
        written["dialect"] = READER.digest_of(READER.canon(READER.read_document(inputs.dialect, "the dialect")))
        if binding is not None:
            binding(written)
        inputs.binding = json.dumps(written).encode("utf-8")
        return inputs

    def test_the_binding_document_is_held_to_its_form_and_to_the_dialect_it_binds(self) -> None:
        unchanged = self._imported().verify().answer
        self.assertEqual("matches", unchanged["reading"]["binding"], unchanged)
        entry = lambda b: b["sources"]["intake"]  # noqa: E731
        probes = {
            # §4.4: refused with the dialect (§11)
            "a binding for another dialect": lambda b: b.__setitem__("dialect", "sha256:" + "0" * 64),
            "a source more": lambda b: b["sources"].__setitem__("other", dict(entry(b))),
            "no source": lambda b: b.__setitem__("sources", {}),
            "a name but for case": lambda b: b.__setitem__("sources", {"Intake": entry(b)}),
            # its form
            "a member more": lambda b: b.__setitem__("version", 1),
            "an entry member more": lambda b: entry(b).__setitem__("shape", "http"),
            "an empty profile": lambda b: entry(b).__setitem__("profile", ""),
            "a profileDigest that is not a digest": lambda b: entry(b).__setitem__("profileDigest", "sha256:XYZ"),
            "a dialect that is not a digest": lambda b: b.__setitem__("dialect", b["dialect"].upper()),
            "sources that are an array": lambda b: b.__setitem__("sources", [entry(b)]),
        }
        for name, alter in probes.items():
            with self.subTest(probe=name):
                answer = self._imported(binding=alter).verify().answer
                self.assertEqual("input-malformed", answer.get("refused"), answer)
        # the published dialect changed under a binding of the dialect as it was
        inputs = self.inputs("unbound-bound-at-import")
        inputs.dialect = inputs.dialect.replace(b'"maxAge":300', b'"maxAge":301')
        self.assertEqual("input-malformed", inputs.verify().answer.get("refused"))
        # a dialect with an unbound source and no binding document, and one beside a dialect with none
        inputs = self.inputs("unbound-bound-at-import")
        inputs.binding = None
        self.assertEqual("input-malformed", inputs.verify().answer.get("refused"))
        for name in ("version-3-bound", "valid"):
            with self.subTest(beside=name):
                inputs = self.inputs(name)
                inputs.binding = self.inputs("unbound-bound-at-import").binding
                self.assertEqual("input-malformed", inputs.verify().answer.get("refused"))
        # read as a document: not one JSON value; and its bounds, measured on bytes first (§12)
        inputs = self.inputs("unbound-bound-at-import")
        for data, refusal in (
            (b"{", "input-malformed"),
            (inputs.binding + b" " * (65536 - len(inputs.binding)), "matches"),
            (inputs.binding + b" " * (65537 - len(inputs.binding)), "input-over-bound"),
            (b"[" * 65 + b"]" * 65, "input-over-bound"),
        ):
            with self.subTest(binding=data[:20], size=len(data)):
                inputs.binding = data
                answer = inputs.verify().answer
                self.assertEqual(refusal, answer.get("refused") or answer["reading"]["binding"], answer)

    def test_an_unbound_source_is_held_to_its_form(self) -> None:
        source = lambda d: d["sources"][0]  # noqa: E731
        probes = {
            "a shape of command": lambda d: source(d).__setitem__("shape", "command"),
            "an empty platform": lambda d: source(d).__setitem__("platform", ""),
            "a record that is not a string": lambda d: source(d).__setitem__("record", 7),
            "a profile beside the catalog names": lambda d: source(d).__setitem__("profile", "intake"),
            "no operation": lambda d: source(d).pop("operation"),
            "a version-2 document": lambda d: d.__setitem__("version", 2),
        }
        for name, alter in probes.items():
            with self.subTest(probe=name):
                answer = self._imported(unbound=alter).verify().answer
                self.assertEqual("input-malformed", answer.get("refused"), answer)

    def test_a_profile_bound_of_another_shape_or_record_is_a_mismatch(self) -> None:
        # §4.4, §5.1: the profile the binding document names serves the unbound source's shape and record. The
        # source names another, or is bound to a profile the verifier does not trust by that id and digest.
        source = lambda d: d["sources"][0]  # noqa: E731
        entry = lambda b: b["sources"]["intake"]  # noqa: E731
        for name, unbound, binding in (
            ("another shape", lambda d: source(d).__setitem__("shape", "mcp"), None),
            ("another record", lambda d: source(d).__setitem__("record", "adapter-airbyte"), None),
            ("an untrusted profile", None, lambda b: entry(b).__setitem__("profile", "another")),
            ("another profile digest", None, lambda b: entry(b).__setitem__("profileDigest", "sha256:" + "1" * 64)),
        ):
            with self.subTest(probe=name):
                answer = self._imported(unbound=unbound, binding=binding).verify().answer
                self.assertEqual("profile-mismatch", answer.get("finding"), answer)

    def test_a_kind_of_version_3_is_held_to_its_form_and_not_read(self) -> None:
        # `http`, `sql` and `web`; `research` is read since the research-contract amendment (ResearchContractTests).
        bound = json.loads(self.inputs("version-3-bound").dialect)["sources"][0]
        common = {"profile": bound["profile"], "profileDigest": bound["profileDigest"], "maxAge": 300, "read": {"copy": {"facts": [], "evidence": []}}}
        string = {"$param": "invoiceCurrency"}
        well_formed = {
            "http": {"method": "POST", "path": "/requests", "query": {"currency": string}, "body": {"n": 1}, "headers": ["Accept"]},
            "sql": {"statement": "SELECT 1 WHERE c = :c", "bindings": [{"name": "c", "type": "STRING", "value": string}]},
            "web": {"url": string},
        }
        malformed = {
            "http": [{"method": "PUT"}, {"path": {"a": 1}}, {"path": {"$param": "runAt"}}, {"method": "GET"}, {"query": {"currency": 7}}, {"headers": "Accept"}],
            "sql": [{"statement": {"$text": "SELECT 1"}}, {"bindings": [{"name": "c", "type": "STRING", "value": "EUR"}]}, {"bindings": [{"name": "c", "value": string}]}],
            "web": [{"url": 7}, {"url": {"$param": "nope"}}, {"url": {"$text": "https://example.org/"}}],
        }

        def answer(source: dict[str, Any], name: str = "version-3-bound", version: int = 3) -> Any:
            inputs = self.inputs(name)
            document = json.loads(inputs.dialect)
            document["version"] = version
            document["sources"].append(source)
            inputs.dialect = json.dumps(document).encode("utf-8")
            return inputs.verify().answer

        for kind, members in well_formed.items():
            source = {"name": "more", "kind": kind, **common, **members}
            with self.subTest(kind=kind):
                self.assertEqual("kind-unread", answer(source).get("refused"))
                # in a version-2 document, a kind of version 3 is refused
                self.assertEqual("input-malformed", answer(source, version=2).get("refused"))
                # a member more, and one of its own left out
                self.assertEqual("input-malformed", answer({**source, "arguments": {}}).get("refused"))
                self.assertEqual("input-malformed", answer({k: v for k, v in source.items() if k != next(iter(members))}).get("refused"))
            for alteration in malformed[kind]:
                with self.subTest(kind=kind, alteration=alteration):
                    self.assertEqual("input-malformed", answer({**source, **alteration}).get("refused"))
        # the members of version 3's kinds that the Runner's encoding keeps written empty are read so
        http = {"name": "more", "kind": "http", **common, **well_formed["http"]}
        for member, empty in (("headers", []), ("query", {}), ("body", {})):
            with self.subTest(written_empty=member):
                self.assertEqual("kind-unread", answer({**http, member: empty}).get("refused"))
        # a kind of another type is refused, not raised
        for kind in (["web"], {"web": 1}, 3, None):
            with self.subTest(kind=kind):
                self.assertEqual("input-malformed", answer({"name": "more", "kind": kind, **common, "url": "x"}).get("refused"))
        # selected-file is of version 3 too, and not read
        local = {"name": "upload", "kind": "selected-file", "provider": "local-file", "read": {"copy": {"facts": [], "evidence": []}}}
        self.assertEqual("kind-unread", answer(local).get("refused"))
        # every form comes first: the binding document's too
        web = {"name": "page", "kind": "web", **common, "url": "https://example.org/"}
        # a binding document of the dialect as it was, before the source was added, is refused before the kind
        self.assertEqual("input-malformed", answer(web, "unbound-bound-at-import").get("refused"))
        inputs = self._imported(unbound=lambda d: d["sources"].append(web))
        self.assertEqual("kind-unread", inputs.verify().answer.get("refused"))
        inputs.binding = None
        self.assertEqual("input-malformed", inputs.verify().answer.get("refused"))

    def test_version_3_carries_no_member_of_version_2_alone(self) -> None:
        # §2: `provider`, `facts` and `evidence` are members of version 2 alone; a document of version 3 that
        # names one is refused. In version 2 each is read, as the version-2 vectors write all three.
        for member, value in (("provider", '""'), ("facts", "null"), ("evidence", "null")):
            for version, expected in ((3, ("refused", "input-malformed")), (2, ("finding", "preparation-differs"))):
                with self.subTest(member=member, version=version):
                    inputs = self.inputs("version-3-bound")
                    written = f'"version":{version},"{member}":{value}}}'.encode()
                    inputs.dialect = inputs.dialect.replace(b'"version":3}', written)
                    answer = inputs.verify().answer
                    self.assertEqual(expected[1], answer.get(expected[0]), answer)

    def test_version_3_leaves_an_optional_member_out_when_it_is_empty(self) -> None:
        # §2: in version 3 an optional member whose absence means its empty value is left out when it is empty;
        # written as [] or {} it is refused. Each alteration is read in version 2, so that its emptiness alone is
        # what version 3 refuses.
        # The members are those the Runner's encoding leaves out when empty (review round 7, finding 2); the
        # members it keeps written empty are read in both versions.
        source = lambda d: d["sources"][0]  # noqa: E731
        refused = {
            "unmapped": lambda d: d.__setitem__("unmapped", []),
            "unmappedEvidence": lambda d: d.__setitem__("unmappedEvidence", []),
            "admits.facts": lambda d: d.__setitem__("admits", {"facts": {}}),
            "admits.evidence": lambda d: d.__setitem__("admits", {"evidence": {}}),
            "a source's parameters": lambda d: source(d).__setitem__("parameters", {}),
        }
        kept = {
            "admits": lambda d: d.__setitem__("admits", {}),
            "a copy's facts": lambda d: source(d)["read"]["copy"].__setitem__("facts", []),
            "a copy's evidence": lambda d: source(d)["read"]["copy"].__setitem__("evidence", []),
        }
        for name, alter in list(refused.items()) + list(kept.items()):
            in_version_3 = ("refused", "input-malformed") if name in refused else ("finding", "preparation-differs")
            for version, expected in ((3, in_version_3), (2, ("finding", "preparation-differs"))):
                with self.subTest(member=name, version=version):
                    inputs = self.inputs("version-3-bound")
                    document = json.loads(inputs.dialect)
                    document["version"] = version
                    alter(document)
                    inputs.dialect = json.dumps(document).encode("utf-8")
                    answer = inputs.verify().answer
                    self.assertEqual(expected[1], answer.get(expected[0]), answer)
        # A case-only dialect: `sources` and the case's `parameters` written empty. The case's own `facts` and
        # `evidence` are required, not optional, and are written empty in every version.
        inputs = self.inputs("escaped-strings")
        inputs.acquisitions, inputs.record, inputs.require_binding = b"{}", None, False
        inputs.preparation = b'{"verifiedAt":"2026-10-14T00:00:00Z"}'
        for written, refused in (
            ({}, False),
            ({"sources": []}, True),
            ({"case": {"parameters": {}, "facts": [], "evidence": []}}, True),
        ):
            for version in (2, 3):
                with self.subTest(written=written, version=version):
                    document = {"version": version, "case": {"facts": [], "evidence": []}, **written}
                    inputs.dialect = json.dumps(document).encode("utf-8")
                    answer = inputs.verify().answer
                    if refused and version == 3:
                        self.assertEqual("input-malformed", answer.get("refused"), answer)
                    else:
                        self.assertEqual("preparation-differs", answer.get("finding"), answer)

    def test_a_copy_has_both_its_arrays_in_every_version(self) -> None:
        # §6.2: both arrays are required, as the Runner requires them (review round 7, finding 2); either may be
        # empty, and a copy that leaves one out is refused in versions 2 and 3.
        for version in (2, 3):
            for copy, refused in (({}, True), ({"facts": []}, True), ({"evidence": []}, True), ({"facts": [], "evidence": []}, False)):
                with self.subTest(version=version, copy=copy):
                    inputs = self.inputs("version-3-bound")
                    document = json.loads(inputs.dialect)
                    document["version"] = version
                    document["sources"][0]["read"]["copy"] = copy
                    inputs.dialect = json.dumps(document).encode("utf-8")
                    answer = inputs.verify().answer
                    if refused:
                        self.assertEqual("input-malformed", answer.get("refused"), answer)
                    else:
                        self.assertEqual("preparation-differs", answer.get("finding"), answer)

    def test_a_binding_document_of_null_is_refused(self) -> None:
        # §4.4, §11: a binding document supplied is held to its form, `null` included; it is not taken as
        # absent (review round 7, finding 3).
        for name in ("version-3-bound", "unbound-bound-at-import"):
            with self.subTest(vector=name):
                inputs = self.inputs(name)
                inputs.binding = b"null"
                self.assertEqual("input-malformed", inputs.verify().answer.get("refused"))

    def test_an_operations_acquisition_has_its_receipt_and_salts(self) -> None:
        # §5.2: only a research record may come back without a receipt and salts of its own (review round 7,
        # finding 5); the research record's own form is ResearchContractTests'.
        inputs = self.inputs("version-3-bound")
        sources = json.loads(inputs.acquisitions)
        del sources["fx"]["response"]["receipt"], sources["fx"]["response"]["salts"]
        inputs.acquisitions = json.dumps(sources).encode("utf-8")
        self.assertEqual("input-malformed", inputs.verify().answer.get("refused"))

    # The six choices the text now decides (RFC 0018, Evidence), each held here as the text says.

    def _program(self, *arguments: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(ROOT / "tools" / "dialect_verify.py"), *arguments],
            capture_output=True,
            timeout=300,
        )

    def _files(self, directory: Path, inputs: Inputs) -> list[str]:
        names = {
            "dialect": inputs.dialect,
            "case": inputs.case,
            "acquisitions": inputs.acquisitions,
            "profiles": inputs.profiles,
            "preparation": inputs.preparation,
        }
        if inputs.record is not None:
            names["record"] = inputs.record
        if inputs.binding is not None:
            names["binding"] = inputs.binding
        arguments = []
        for name, data in names.items():
            (directory / name).write_bytes(data)
            arguments += [f"--{name}", str(directory / name)]
        return arguments + (["--require-binding"] if inputs.require_binding else [])

    def test_the_report_is_one_object_in_the_preparations_form_and_the_exit_status_says_which(self) -> None:
        # §11, the report: `result` and the members its form carries, written as §9.5 writes; exit 0
        # for a reading, 1 for a refusal, 2 for a finding, 3 with no report when it could not run.
        with tempfile.TemporaryDirectory() as scratch:
            directory = Path(scratch)
            run = self._program(*self._files(directory, self.inputs("escaped-strings")))
            self.assertEqual(0, run.returncode, run.stderr)
            line = run.stdout.rstrip(b"\n")
            self.assertEqual(run.stdout, line + b"\n")
            self.assertNotIn(b"\n", line)
            report = READER.read_document(line, "the report")
            self.assertEqual(READER.preparation_bytes(report), line)
            self.assertEqual({"result", "digest", "binding", "facts", "evidence", "targetsByClass"}, set(report))
            self.assertEqual(("reading", "absent"), (report["result"], report["binding"]))
            self.assertIn(b'"vendor":"A\\u0026B \\u003cx\\u003e caf\xc3\xa9 \xe2\x98\x83"', line)

            run = self._program(*self._files(directory, self.inputs("recomputed-one-second-later")))
            self.assertEqual((2, b'{"finding":"binding-mismatch","result":"finding"}\n'), (run.returncode, run.stdout))

            inputs = self.inputs("valid")
            inputs.dialect = b"{"
            run = self._program(*self._files(directory, inputs))
            self.assertEqual((1, b'{"refusal":"input-malformed","result":"refusal"}\n'), (run.returncode, run.stdout))

            arguments = self._files(directory, self.inputs("valid"))
            unopened = list(arguments)
            unopened[unopened.index("--profiles") + 1] = str(directory / "no-such-file")
            at = arguments.index("--case")
            for name, broken in (
                ("a file it cannot open", unopened),
                ("an argument it does not take", arguments + ["--an-argument-it-does-not-take"]),
                ("a required argument left out", arguments[:at] + arguments[at + 2 :]),
            ):
                with self.subTest(could_not_run=name):
                    run = self._program(*broken)
                    self.assertEqual((3, b""), (run.returncode, run.stdout))
            # its help is no reading either
            self.assertEqual(3, self._program("--help").returncode)

            # a dialect bound at import, with its binding document; and without it, refused
            arguments = self._files(directory, self.inputs("unbound-bound-at-import"))
            run = self._program(*arguments)
            self.assertEqual(0, run.returncode, run.stderr)
            self.assertIn(b'"binding":"matches"', run.stdout)
            at = arguments.index("--binding")
            run = self._program(*(arguments[:at] + arguments[at + 2 :]))
            self.assertEqual((1, b'{"refusal":"input-malformed","result":"refusal"}\n'), (run.returncode, run.stdout))

    def test_a_reading_reports_each_number_as_its_literal(self) -> None:
        # A case-only reading whose facts hold -0: the report keeps it, as §9.5 writes a number.
        inputs = self.inputs("escaped-strings")
        inputs.dialect = b'{"version":2,"case":{"facts":[{"target":"/n","source":"/n"}],"evidence":[]}}'
        inputs.case = b'{"n":-0}'
        inputs.record, inputs.require_binding = None, False
        inputs.preparation = b'{"verifiedAt":"2026-10-14T00:00:00Z"}'
        inputs.preparation = inputs.verify().preparation
        with tempfile.TemporaryDirectory() as scratch:
            run = self._program(*self._files(Path(scratch), inputs))
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertIn(b'"facts":{"n":-0}', run.stdout)
        self.assertIn(b'"binding":"not-checked"', run.stdout)

    def test_nesting_counts_each_object_and_array_from_zero_at_the_root(self) -> None:
        self.assertEqual(
            [0, 0, 1, 1, 2, 2],
            [READER.value_depth(v) for v in ("x", READER.Num("1"), {}, [], {"a": []}, [{}])],
        )
        READER.measure(b"{}", "a document", 1)
        READER.measure(b'"{[{["', "a document", 0)
        with self.assertRaises(READER.Refused):
            READER.measure(b'{"a":[]}', "a document", 1)
        # the case document at 32 levels is within its bound, at 33 over it
        inputs = self.inputs("escaped-strings")
        inputs.case = b"[" * 32 + b"]" * 32
        self.assertNotEqual("input-over-bound", inputs.verify().answer.get("refused"))
        inputs.case = b"[" * 33 + b"]" * 33
        self.assertEqual("input-over-bound", inputs.verify().answer.get("refused"))

    def test_a_number_literal_is_a_maximal_run_and_its_exponent_follows_the_first_e(self) -> None:
        within = [b"[1e308,-1E-308,1e+0000308,true,false,null]", b"[1e5e999]", b"[1e+-999]", b"[" + b"9" * 128 + b"]"]
        over = [b"[e999]", b"[E+999]", b"[.1e309]", b"[+1e309]", b"[1e999.5]", b"[." + b"1" * 128 + b"]", b"[1e309]"]
        for data in within:
            with self.subTest(within=data[:40]):
                READER.measure(data, "a document", 64)
        for data in over:
            with self.subTest(over=data[:40]):
                with self.assertRaises(READER.Refused) as refused:
                    READER.measure(data, "a document", 64)
                self.assertEqual("input-over-bound", refused.exception.name)
        # through the reading: a run that starts with `e` is over its bound before the case is read
        inputs = self.inputs("escaped-strings")
        inputs.case = b"[e999]"
        self.assertEqual("input-over-bound", inputs.verify().answer.get("refused"))
        inputs.case = b"[1e5e999]"
        self.assertEqual("input-malformed", inputs.verify().answer.get("refused"))

    def test_an_unwrapped_strings_bound_is_its_decoded_values_utf8_bytes(self) -> None:
        # 200000 bytes of UTF-8 are within the bound and 200001 over it, though the string holds about
        # 100000 characters.
        def unwrapped(size: int) -> Any:
            head, tail = '{"pad":"', '","id":7}'
            room = size - len((head + tail).encode("utf-8"))
            text = head + "é" * (room // 2) + "a" * (room % 2) + tail
            self.assertEqual(size, len(text.encode("utf-8")))
            self.assertLess(len(text), 100100)
            return READER.apply_unwrap({"wrapped": text}, ["/wrapped"])

        self.assertEqual(7, READER.integer_of(unwrapped(200000)["id"]))
        with self.assertRaises(READER.Refused) as refused:
            unwrapped(200001)
        self.assertEqual("input-over-bound", refused.exception.name)

    def test_a_version_2_record_is_run_audit_as_run_json_writes_it(self) -> None:
        # An export of version 2 carries the record as run.audit, and no bytes. Written into such an
        # export as it is, the valid vector's bound record still matches: its line is the member's
        # value exactly as run.json writes it. Re-encoded, its binding's members would be reordered.
        inputs = self.inputs("valid")
        line = inputs.record
        run = b'{"version":2,"run": {"input": {"preparation": ' + inputs.preparation + b'}, "audit": ' + line + b" }}"
        self.assertEqual(line, READER.record_of_export(run))
        inputs.record = READER.record_of_export(run)
        self.assertEqual("matches", inputs.verify().answer["reading"]["binding"])
        inputs.record = READER.preparation_bytes(READER.read_document(line, "the record"))
        self.assertEqual("binding-mismatch", inputs.verify().answer.get("finding"))

    def test_but_for_case_is_ascii_case_only(self) -> None:
        refused = ("BINDING", "bInDiNg", "Binding")
        not_refused = ("ｂｉｎｄｉｎｇ", "BİNDİNG", "bındıng", "bindinǵ", "bindings")
        for name in refused + not_refused:
            with self.subTest(name=name):
                inputs = self.inputs("valid")
                member = json.dumps(name, ensure_ascii=False).encode("utf-8")
                inputs.record = inputs.record.replace(b'"inputs":', member + b':1,"inputs":', 1)
                answer = inputs.verify().answer
                if name in refused:
                    self.assertEqual("input-malformed", answer.get("refused"), answer)
                else:
                    self.assertEqual("matches", answer["reading"]["binding"], answer)

    def test_a_fresh_within_of_another_declared_type_is_false_and_the_rule_is_read(self) -> None:
        # The vendor rule's freshWithin, `asOf` runAt and `maxAge` window: each given a declared
        # parameter of another type, the condition is false, so the vendor answers by its last clause.
        for member, name in (("maxAge", "runAt"), ("asOf", "window"), ("asOf", "vendorId")):
            with self.subTest(member=member, names=name):
                answer = self._with_rule_condition(lambda of: of[1].__setitem__(member, name))
                self.assertEqual("preparation-differs", answer.get("finding"), answer)
        # a parameter the rule does not declare is the form's, and refused
        answer = self._with_rule_condition(lambda of: of[1].__setitem__("asOf", "region"))
        self.assertEqual("input-malformed", answer.get("refused"), answer)

    def test_a_requirement_id_is_a_non_empty_string_of_no_other_form(self) -> None:
        inputs = self.inputs("unsigned-parameters")
        dialect = json.loads(inputs.dialect)
        evidence = dialect["sources"][0]["read"]["rule"]["clauses"][0]["claim"]["evidence"]
        for requirement, answer in (("", ("refused", "input-malformed")), ("pack#1/intake form", ("finding", "preparation-differs"))):
            with self.subTest(requirement=requirement):
                evidence.clear()
                evidence[requirement] = "present"
                inputs.dialect = json.dumps(dialect).encode("utf-8")
                result = inputs.verify().answer
                self.assertEqual(answer[1], result.get(answer[0]), result)
        inputs = self.inputs("valid")
        dialect = json.loads(inputs.dialect)
        dialect["sources"][0]["read"]["copy"]["evidence"][0]["requirement"] = ""
        inputs.dialect = json.dumps(dialect).encode("utf-8")
        self.assertEqual("input-malformed", inputs.verify().answer.get("refused"))


# The research contract (RFC 0018, round 8, issue #176): hand-written documents of every new form
# and refusal, signed under a key of the tests' own. The Runner's twenty-six research vectors hold
# the kind as it records it; these are this repository's checks of its two readers, not vectors, and
# no claim could cite them. Each case is answered by the first reader here and by the second in
# tests/test_dialect_ts.py, which holds the two reports equal.

RESEARCH_AT = "2026-10-15T12:00:00Z"
RESEARCH_SERVED = "2026-10-15T11:59:00Z"
RESEARCH_OBSERVED = "2026-10-15T11:58:30Z"
RESEARCH_EXPIRED = "2026-10-15T11:40:00Z"  # 20 minutes before the instant, past every maxAge here
RESEARCH_KEY = signer(b"the research tests' own key")
RESEARCH_SALT = "5a" * 32
COMPANY = "Synthetic Company 0001"


def research_digest(value: Any) -> str:
    return READER.digest_of(READER.canon(value))


def research_profile(pid: str, source: str, adapter: str, research: Any = None, klass: str = "generated") -> dict[str, Any]:
    profile = {
        "id": pid,
        "publicKey": RESEARCH_KEY[0].hex(),
        "class": klass,
        "source": source,
        "authority": "research.example.test",
        "shape": "http",
        "adapter": {"name": adapter, "version": "1.0.0", "digest": "sha256:" + "ab" * 32},
        "endpoint": None,
    }
    if research is not None:
        profile["research"] = research
    return profile


def research_profiles() -> list[dict[str, Any]]:
    """The installation's trusted profiles: an AI profile for model-a, and a web profile for search and
    page; and, for the refusals, one of another model, one of search alone, one of class record, one with
    no research declaration, and a web profile that declares another model."""
    return [
        research_profile("ai", "ai-answers", "adapter-ai", {"capabilities": ["answer"], "model": "model-a"}),
        research_profile("web", "web-pages", "adapter-web", {"capabilities": ["search", "page"]}),
        research_profile("ai-b", "ai-answers", "adapter-ai", {"capabilities": ["answer"], "model": "model-b"}),
        research_profile("ai-2", "ai-answers-2", "adapter-ai", {"capabilities": ["answer"], "model": "model-a"}),
        research_profile("web-search", "web-pages", "adapter-web", {"capabilities": ["search"]}),
        research_profile("web-record", "web-pages", "adapter-web", {"capabilities": ["search", "page"]}, "record"),
        research_profile("web-b", "web-pages", "adapter-web", {"capabilities": ["answer", "search", "page"], "model": "model-b"}),
        research_profile("plain", "ai-answers", "adapter-ai"),
    ]


def company_fields() -> list[dict[str, Any]]:
    """`gtm-company-person`'s company, all six types (§11's first example list); synthetic."""
    return [
        {"name": "company-id", "type": "text", "required": True, "description": "A synthetic company identifier."},
        {"name": "employee-count", "type": "integer", "required": True, "description": "Employees, as cited."},
        {"name": "revenue", "type": "decimal", "required": False, "description": "Annual revenue, a decimal string."},
        {"name": "active", "type": "boolean", "required": False, "description": "Whether the company trades."},
        {"name": "roles", "type": "text-list", "required": False, "description": "Roles the company hires for."},
        {"name": "employee-range", "type": "range", "required": False, "description": "The band of employees."},
    ]


def research_source(name: str, read: Any, fields: Any = None, capabilities: Any = None) -> dict[str, Any]:
    """A bound research source; `profile`, `profileDigest` and `webProfiles` are given the trusted
    profiles' digests when the documents are built."""
    capabilities = ["answer", "search", "page"] if capabilities is None else capabilities
    return {
        "name": name,
        "kind": "research",
        "maxAge": 600,
        "question": {"$param": "company"},
        "constraints": {"region": "EU", "synthetic": True},
        "model": "model-a",
        "evidence": ["the page that states the headcount"],
        "fields": company_fields() if fields is None else fields,
        "capabilities": capabilities,
        "profile": "ai",
        "profileDigest": "ai",
        "webProfiles": {c: {"profile": "web", "profileDigest": "web"} for c in capabilities if c != "answer"},
        "read": read,
    }


def answer_response(model: str = "model-a") -> dict[str, Any]:
    return {"profile": "ai", "request": {"prompt": f"Which company? ({model})"}, "result": {"text": "Synthetic Company 0001 employs no one."}}


def search_response() -> dict[str, Any]:
    return {"profile": "web", "request": {"query": "Synthetic Company 0001"}, "result": {"hits": ["https://company.example.test/about"]}}


def page_response() -> dict[str, Any]:
    return {"profile": "web", "request": {"url": "https://company.example.test/about"}, "result": {"page": "Headcount: 0."}}


def company_answers() -> dict[str, Any]:
    """Every type, found: integer zero, a negative decimal of scale two, `false`, the empty list, and a
    decimal range whose endpoints are equal by value and spelled apart."""
    return {
        "company-id": {"status": "found", "value": "synthetic-company-0001", "cites": [0]},
        "employee-count": {"status": "found", "value": 0, "cites": [0, 2]},
        "revenue": {"status": "found", "value": "-12.50", "cites": [2]},
        "active": {"status": "found", "value": False, "cites": [0]},
        "roles": {"status": "found", "value": [], "cites": [1]},
        "employee-range": {"status": "found", "value": {"min": "1.0", "max": "1.00"}, "cites": [2]},
    }


def copy_fields(name: str) -> dict[str, Any]:
    return {"copy": {"facts": [{"target": f"/{name}/fields", "source": "/fields"}], "evidence": []}}


def status_guard(entry: str, status: str) -> dict[str, Any]:
    return {"op": "equals", "field": f"{entry}/status", "to": status}


def absence_guard(entry: str) -> dict[str, Any]:
    return {"op": "not", "of": {"op": "exists", "field": entry}}


def unavailable(entry: str) -> dict[str, Any]:
    return {"op": "any", "of": [absence_guard(entry), status_guard(entry, "not-found"), status_guard(entry, "stale")]}


def clause(when: Any, reason: str, target: str | None = None, source: str | None = None, status: str = "unknown") -> dict[str, Any]:
    facts = [{"pointer": target, "from": source}] if target is not None else []
    return {"when": when, "claim": {"facts": facts, "evidence": {}, "acquisitionStatus": status}, "reason": reason}


PRIMARY = "/sources/primary/fields/employee-count"
SECONDARY = "/sources/secondary/fields/employee-count"
CURRENT = "/current/fields/employee-count"
COUNT_TARGET = "/company/employee-count"


def reconciliation_rule() -> dict[str, Any]:
    """§6.4's example extended to a third source (§11, `failed-fallback`): the primary's found value
    first, then the secondary's, a conflict anywhere unknown, then the source's own found value, and
    unknown when no candidate is left; each absence, not-found, stale and conflicting status named."""
    return {
        "ruleVersion": "1",
        "parameters": {},
        "clauses": [
            clause(status_guard(PRIMARY, "found"), "the primary found it", COUNT_TARGET, PRIMARY + "/value", "resolved"),
            clause({"op": "all", "of": [unavailable(PRIMARY), status_guard(SECONDARY, "found")]}, "the secondary found it", COUNT_TARGET, SECONDARY + "/value", "resolved"),
            clause({"op": "any", "of": [status_guard(e, "conflicting") for e in (PRIMARY, SECONDARY, CURRENT)]}, "a conflict is not chosen"),
            clause({"op": "all", "of": [unavailable(SECONDARY), status_guard(CURRENT, "found")]}, "this source found it", COUNT_TARGET, CURRENT + "/value", "resolved"),
            clause(unavailable(CURRENT), "no candidate is left"),
            clause({"op": "always"}, "otherwise"),
        ],
    }


def count_only() -> list[dict[str, Any]]:
    return [{"name": "employee-count", "type": "integer", "required": False, "description": "Employees, as cited."}]


def observed(name: str) -> dict[str, Any]:
    return {"copy": {"facts": [{"target": f"/observed/{name}", "source": "/fields/employee-count/status"}], "evidence": []}}


def count_answer(status: str, value: Any = 7, cites: Any = None) -> dict[str, Any]:
    if status == "found":
        return {"employee-count": {"status": "found", "value": value, "cites": [0] if cites is None else cites}}
    if status == "conflicting":
        return {"employee-count": {"status": "conflicting", "cites": [], "values": [{"value": 7, "cites": [0]}, {"value": 9, "cites": [0]}]}}
    if status == "absent":
        return {}
    return {"employee-count": {"status": status, "cites": [] if cites is None else cites}}


class ResearchScenario:
    """One hand-written research run: a version-3 dialect, its case, the trusted profiles, and for each
    research source its record's answers and the responses it retains, signed when built. A test alters
    any part before the documents are built (`documents`)."""

    def __init__(self, kind: str = "company") -> None:
        self.profiles = research_profiles()
        self.case = {"company": COMPANY}
        self.admits: dict[str, list[str]] = {}
        self.admits_evidence: dict[str, list[str]] = {}
        self.records: dict[str, dict[str, Any]] = {}
        self.own: set[str] = set()  # the sources whose record has a receipt of its own
        self.unbound: set[str] = set()  # the sources published unbound, bound by a binding document
        self.call_indices: dict[str, list[int]] = {}  # each source's receipts' callIndex, when not in turn
        self.require_binding = False
        sources: list[dict[str, Any]]
        if kind == "company":
            sources = [research_source("company", copy_fields("company"))]
            self.admits = {"/company/fields": ["generated"]}
            self.records = {"company": {"fields": company_answers(), "responses": [answer_response(), search_response(), page_response()]}}
        elif kind == "reconcile":
            sources = [
                research_source("primary", observed("primary"), count_only(), ["answer"]),
                research_source("secondary", observed("secondary"), count_only(), ["answer", "page"]),
                research_source("combined", {"sources": ["primary", "secondary"], "rule": reconciliation_rule()}, count_only(), ["answer"]),
            ]
            self.admits = {**{f"/observed/{n}": ["generated"] for n in ("primary", "secondary")}, COUNT_TARGET: ["generated"]}
            self.records = {
                "primary": {"fields": count_answer("found", 7), "responses": [answer_response()]},
                "secondary": {"fields": count_answer("found", 9), "responses": [answer_response(), page_response()]},
                "combined": {"fields": count_answer("not-found"), "responses": []},
            }
        else:
            raise AssertionError(kind)
        self.dialect = {
            "version": 3,
            "case": {
                "parameters": {"company": {"pointer": "/company", "type": "string"}},
                "facts": [{"target": "/case/company", "source": "/company"}],
                "evidence": [],
            },
            "sources": sources,
        }
        # applied to each receipt before it is signed: (source name, response index or "own", receipt)
        self.receipt_hooks: list[Any] = []
        # applied to the documents once every receipt is signed: (documents)
        self.after_hooks: list[Any] = []
        # applied to the documents' bytes last: (document, bytes written, bytes in their place)
        self.replacements: list[tuple[str, bytes, bytes]] = []

    def source(self, name: str) -> dict[str, Any]:
        return next(s for s in self.dialect["sources"] if s["name"] == name)

    def documents(self, preparation: bytes | None = None) -> "HandInputs":
        profiles = copy.deepcopy(self.profiles)
        by_id = {p["id"]: p for p in profiles}
        digests = {p["id"]: research_digest(p) for p in profiles}
        dialect = copy.deepcopy(self.dialect)
        admits = {member: dict(lists) for member, lists in (("facts", self.admits), ("evidence", self.admits_evidence)) if lists}
        if admits:
            dialect["admits"] = admits
        for source in dialect["sources"]:
            if source.get("kind") != "research":
                if source.get("profileDigest") in digests:
                    source["profileDigest"] = digests[source["profileDigest"]]
                continue
            if source.get("profileDigest") in digests:
                source["profileDigest"] = digests[source["profileDigest"]]
            for assignment in (source.get("webProfiles") or {}).values():
                if isinstance(assignment, dict) and assignment.get("profileDigest") in digests:
                    assignment["profileDigest"] = digests[assignment["profileDigest"]]
        case_values = {"company": self.case.get("company")}
        acquisitions: dict[str, Any] = {}
        call = 0
        for source in dialect["sources"]:
            name = source.get("name")
            if name not in self.records:
                continue
            spec = self.records[name]
            indices = iter(self.call_indices.get(name, []))
            responses = []
            for index, response in enumerate(spec.get("responses", [])):
                profile = by_id.get(response["profile"], profiles[0])
                entry = {
                    "profile": {"id": response["profile"], "digest": response.get("digest", digests.get(response["profile"], "sha256:" + "0" * 64))},
                    "request": response["request"],
                    "result": response["result"],
                    "receipt": self._receipt(name, index, profile, response["request"], response["result"], next(indices, call)),
                    "salts": {"args": RESEARCH_SALT},
                }
                call += 1
                responses.append(entry)
            record = {"fields": spec["fields"], "responses": responses}
            member: dict[str, Any] = {"result": record}
            if name in self.own:
                request = {
                    "question": READER.instantiate(source["question"], case_values),
                    **{k: source[k] for k in ("constraints", "model", "evidence", "fields", "capabilities")},
                }
                member["receipt"] = self._receipt(name, "own", by_id[source["profile"]], request, record, next(indices, call))
                member["salts"] = {"args": RESEARCH_SALT}
                call += 1
            acquisitions[name] = {"response": member}
        binding = None
        if self.unbound:
            assignments = {}
            for source in dialect["sources"]:
                if source.get("name") in self.unbound:
                    assignments[source["name"]] = {k: source.pop(k) for k in ("profile", "profileDigest", "webProfiles")}
            binding = {"dialect": research_digest(dialect), "sources": assignments}
        documents = {"dialect": dialect, "case": self.case, "acquisitions": acquisitions, "profiles": profiles, "binding": binding}
        for hook in self.after_hooks:
            hook(documents)
        written = {name: None if value is None else json.dumps(value).encode("utf-8") for name, value in documents.items()}
        for name, old, new in self.replacements:
            assert old in written[name], old
            written[name] = written[name].replace(old, new)
        return HandInputs(
            written["dialect"],
            written["case"],
            written["acquisitions"],
            written["profiles"],
            preparation if preparation is not None else ('{"verifiedAt":"%s"}' % RESEARCH_AT).encode("ascii"),
            written["binding"],
            self.require_binding,
        )

    def _receipt(self, name: str, index: Any, profile: dict[str, Any], request: Any, result: Any, call: int) -> dict[str, Any]:
        receipt = {
            "receiptVersion": "3",
            "kind": "acquisition",
            "keyId": hashlib.sha256(RESEARCH_KEY[0]).hexdigest()[:32],
            "source": profile["source"],
            "authority": profile["authority"],
            "sessionId": "research-session",
            "callIndex": call,
            "argumentsCommitment": "sha256:" + hashlib.sha256(bytes.fromhex(RESEARCH_SALT) + b"args:" + READER.canon(request)).hexdigest(),
            "resultDigest": research_digest(result),
            "servedAt": RESEARCH_SERVED,
            "acquisition": {"adapter": profile["adapter"], "shape": profile["shape"], "endpoint": profile["endpoint"], "observedAt": RESEARCH_OBSERVED},
        }
        for hook in self.receipt_hooks:
            hook(name, index, receipt)
        message = b"judgment-pack-gateway/receipt/3:" + READER.canon(receipt)
        receipt["signature"] = RESEARCH_KEY[1](message).hex()
        return receipt

    def prepared(self) -> "HandInputs":
        """The documents, with the preparation the first reader recomputes from them."""
        inputs = self.documents()
        recomputed = inputs.verify()
        if recomputed.preparation is None:
            raise AssertionError(f"no preparation was recomputed: {recomputed.answer}")
        inputs.preparation = recomputed.preparation
        return inputs


class HandInputs:
    """Hand-written documents, given to a verifier as Inputs gives a vector's."""

    def __init__(self, dialect: bytes, case: bytes, acquisitions: bytes, profiles: bytes, preparation: bytes, binding: bytes | None, require_binding: bool) -> None:
        self.dialect, self.case, self.acquisitions, self.profiles = dialect, case, acquisitions, profiles
        self.preparation, self.binding, self.require_binding = preparation, binding, require_binding
        self.record: bytes | None = None

    def verify(self) -> Any:
        return READER.verify(
            self.dialect, self.case, self.acquisitions, self.profiles, self.preparation, self.record, self.require_binding, self.binding
        )


def assign(source: dict[str, Any], ai: str | None = None, **web: str) -> None:
    """Bind a research source to other trusted profiles, each named by its id (its digest filled in)."""
    if ai is not None:
        source["profile"], source["profileDigest"] = ai, ai
    for capability, pid in web.items():
        source["webProfiles"][capability] = {"profile": pid, "profileDigest": pid}


def gate(scenario: ResearchScenario) -> None:
    """An earlier research source whose rule leaves its claim `absent`, and the primary taking a parameter from
    it: the primary is skipped (§3, §9.2), and its record not acquired."""
    rule = {
        "ruleVersion": "1",
        "parameters": {},
        "clauses": [
            clause(status_guard("/fields/employee-count", "found"), "found", "/gate/count", "/fields/employee-count/value", "resolved"),
            clause({"op": "always"}, "nothing to go on", status="absent"),
        ],
    }
    scenario.dialect["sources"].insert(0, research_source("gate", {"rule": rule}, count_only(), ["answer"]))
    scenario.source("primary")["parameters"] = {"gateCount": {"from": "gate", "pointer": "/gate/count", "type": "integer"}}
    scenario.admits["/gate/count"] = ["generated"]
    scenario.records["gate"] = {"fields": count_answer("not-found"), "responses": []}
    del scenario.records["primary"]


def guarded_rule(*, without: tuple[str, str] | None = None) -> dict[str, Any]:
    """The reconciliation rule with one guard of the primary's taken out: `(status, entry)`."""
    rule = reconciliation_rule()
    if without is None:
        return rule
    status, entry = without

    def keep(condition: dict[str, Any]) -> bool:
        if status == "absent":
            return condition != absence_guard(entry)
        return condition != status_guard(entry, status)

    def prune(condition: dict[str, Any]) -> dict[str, Any]:
        if condition["op"] in ("all", "any"):
            return {**condition, "of": [prune(c) for c in condition["of"] if keep(c)]}
        return condition

    for item in rule["clauses"]:
        item["when"] = prune(item["when"])
    return rule


def research_cases() -> list[tuple[str, str, Any]]:
    """Every new form and every refusal the research contract names, as `(name, expected answer, build)`:
    `build()` gives the documents; the answer is `reading`, `refusal:<code>` or `finding:<code>`. A reading is
    built with the preparation the first reader recomputes, so that the second's must be byte for byte equal."""
    cases: list[tuple[str, str, Any]] = []

    def add(name: str, expected: str, alter: Any = None, kind: str = "company", fixed: Any = None) -> None:
        """`fixed`: the alteration whose documents give the preparation held fixed, None for the unaltered."""

        def build() -> HandInputs:
            scenario = ResearchScenario(kind)
            if alter is not None:
                alter(scenario)
            if expected == "reading" and fixed is None:
                return scenario.prepared()
            if fixed is not None:
                base = ResearchScenario(kind)
                if fixed is not True:
                    fixed(base)
                return scenario.documents(base.prepared().preparation)
            return scenario.documents()

        cases.append((name, expected, build))

    company = lambda s: s.source("company")  # noqa: E731
    answers = lambda s: s.records["company"]["fields"]  # noqa: E731
    declaration = lambda s, name: next(d for d in s.source("company")["fields"] if d["name"] == name)  # noqa: E731
    malformed, over = "refusal:input-malformed", "refusal:input-over-bound"

    def set_in(getter: Any, key: Any, value: Any) -> Any:
        return lambda s: getter(s).__setitem__(key, value)

    def drop(getter: Any, key: Any) -> Any:
        return lambda s: getter(s).pop(key)

    def both(*alterations: Any) -> Any:
        def alter(s: ResearchScenario) -> None:
            for a in alterations:
                a(s)
        return alter

    def after(change: Any) -> Any:
        return lambda s: s.after_hooks.append(change)

    def record(documents: dict[str, Any], name: str = "company") -> dict[str, Any]:
        return documents["acquisitions"][name]["response"]["result"]

    def answer_alone(s: ResearchScenario) -> None:
        company(s)["capabilities"] = ["answer"]
        company(s)["webProfiles"] = {}
        s.records["company"]["responses"] = [answer_response()]
        for entry in answers(s).values():
            entry["cites"] = [0]

    def rule_read(s: ResearchScenario) -> None:
        company(s)["read"] = {"rule": {"ruleVersion": "1", "parameters": {}, "clauses": [
            {"when": status_guard("/fields/employee-count", "found"), "claim": {"facts": [{"pointer": COUNT_TARGET, "from": "/fields/employee-count/value"}], "evidence": {"company-headcount": "present"}, "acquisitionStatus": "resolved"}, "reason": "found"},
            {"when": {"op": "exists", "field": "/fields/employee-count/values/0/value"}, "claim": {"facts": [], "evidence": {"company-headcount": "unknown"}, "acquisitionStatus": "unknown"}, "reason": "observations conflict"},
            {"when": {"op": "always"}, "claim": {"facts": [], "evidence": {"company-headcount": "absent"}, "acquisitionStatus": "absent"}, "reason": "not found"},
        ]}}
        s.admits = {COUNT_TARGET: ["generated"]}
        s.admits_evidence = {"company-headcount": ["generated"]}

    def parameter_rule(s: ResearchScenario) -> None:
        rule_read(s)
        rule = company(s)["read"]["rule"]
        rule["parameters"] = {"company": "string"}
        rule["clauses"][0]["when"] = {"op": "all", "of": [status_guard("/fields/employee-count", "found"), {"op": "equalsParam", "field": "/fields/company-id/value", "param": "company"}]}
        answers(s)["company-id"]["value"] = COMPANY

    # ---- readings: every new form ----
    add("valid-types: answer, search and page, all six types found", "reading")
    add("valid-types: a source asking for answer alone", "reading", answer_alone)
    add("the record with a receipt of its own", "reading", lambda s: s.own.add("company"))
    add("bound through a binding document", "reading", lambda s: s.unbound.add("company"))
    add("bound through a binding document, the record with a receipt of its own", "reading", both(lambda s: s.unbound.add("company"), lambda s: s.own.add("company")))
    add("presence: every optional entry omitted", "reading", lambda s: [answers(s).pop(n) for n in ("revenue", "active", "roles", "employee-range")])
    add("presence: a required entry not-found", "reading", set_in(answers, "employee-count", {"status": "not-found", "cites": [1]}))
    add("presence: integer -0, decimal 0, text empty, boolean false", "reading", both(
        set_in(answers, "company-id", {"status": "found", "value": "", "cites": [0]}),
        set_in(answers, "revenue", {"status": "found", "value": "0", "cites": [0]}),
        lambda s: answers(s)["employee-count"].__setitem__("value", 424242),
        lambda s: s.replacements.append(("acquisitions", b'"value": 424242', b'"value": -0')),
    ))
    add("stale with no citation, conflicting with separate citations", "reading", both(
        set_in(answers, "active", {"status": "stale", "cites": []}),
        set_in(answers, "roles", {"status": "conflicting", "cites": [], "values": [{"value": ["buyer", "buyer", ""], "cites": [0]}, {"value": ["buyer"], "cites": [1, 2]}]}),
    ))
    add("an integer range, a list with duplicates and empty strings, decimals spelled apart", "reading", both(
        set_in(answers, "employee-range", {"status": "conflicting", "cites": [], "values": [{"value": {"min": -3, "max": 12}, "cites": [0]}, {"value": {"min": -3, "max": 12, }, "cites": [1]}, {"value": {"min": 0, "max": 0}, "cites": [2]}]}),
        set_in(answers, "roles", {"status": "found", "value": ["x", "x", ""], "cites": [0]}),
        set_in(answers, "revenue", {"status": "conflicting", "cites": [], "values": [{"value": "1.0", "cites": [0]}, {"value": "1.00", "cites": [2]}]}),
    ))
    add("a rule guards the found value, and a condition reads an observation", "reading", rule_read)
    add("a rule over a conflict reads an observation and resolves nothing", "reading", both(rule_read, set_in(answers, "employee-count", {"status": "conflicting", "cites": [], "values": [{"value": 1, "cites": [0]}, {"value": 2, "cites": [2]}]})))
    add("a rule names a parameter no receipt commits", "reading", parameter_rule)
    add("a rule names a parameter the record's own receipt commits", "reading", both(parameter_rule, lambda s: s.own.add("company")))
    add("no retained response and no receipt", "reading", both(
        lambda s: s.records["company"].__setitem__("responses", []),
        lambda s: s.records["company"].__setitem__("fields", {"company-id": {"status": "not-found", "cites": []}, "employee-count": {"status": "stale", "cites": []}}),
    ))
    add("reconciliation: the primary's found value", "reading", kind="reconcile")
    add("reconciliation: the secondary's, the primary not-found", "reading", lambda s: s.records["primary"].__setitem__("fields", count_answer("not-found")), "reconcile")
    add("reconciliation: a conflict derives unknown (failed-fallback)", "reading", both(
        lambda s: s.records["primary"].__setitem__("fields", count_answer("not-found")),
        lambda s: s.records["secondary"].__setitem__("fields", count_answer("stale")),
        lambda s: s.records["combined"].update({"fields": count_answer("conflicting"), "responses": [answer_response()]}),
    ), "reconcile")
    add("reconciliation: every candidate unavailable", "reading", both(
        lambda s: s.records["primary"].__setitem__("fields", count_answer("not-found")),
        lambda s: s.records["secondary"].__setitem__("fields", count_answer("stale")),
    ), "reconcile")
    add("reconciliation: an absent entry, and this source's own found value", "reading", both(
        lambda s: s.records["primary"].__setitem__("fields", count_answer("absent")),
        lambda s: s.records["secondary"].__setitem__("fields", count_answer("not-found")),
        lambda s: s.records["combined"].update({"fields": count_answer("found", 11), "responses": [answer_response()]}),
    ), "reconcile")
    add("reconciliation: a skipped earlier source is absent from the combined value", "reading", gate, "reconcile")
    add("cites follow the sources, not callIndex, in a preparation with research", "reading", lambda s: s.call_indices.update({"primary": [5], "secondary": [0, 1]}), "reconcile")
    add("a field no read uses changes, with no receipt for the record", "reading", both(rule_read, set_in(answers, "roles", {"status": "found", "value": ["other"], "cites": [0]})), fixed=rule_read)

    # ---- findings ----
    add("a read field changes, with no receipt for the record", "finding:preparation-differs", lambda s: answers(s)["employee-count"].__setitem__("value", 1), fixed=True)
    add("responses reordered, their indices updated to cite the same", "finding:preparation-differs", both(
        rule_read,
        lambda s: s.records["company"].__setitem__("responses", [page_response(), answer_response(), search_response()]),
        lambda s: s.call_indices.__setitem__("company", [2, 0, 1]),
        lambda s: [e.__setitem__("cites", [{0: 1, 1: 2, 2: 0}[i] for i in e["cites"]]) for e in answers(s).values()],
    ), fixed=rule_read)
    add("a second installation binds another AI profile", "finding:preparation-differs", both(
        lambda s: s.unbound.add("company"), lambda s: assign(company(s), "ai-2"),
        lambda s: s.records["company"]["responses"][0].__setitem__("profile", "ai-2"),
    ), fixed=lambda s: s.unbound.add("company"))
    add("an AI profile of another model", "finding:profile-mismatch", lambda s: assign(company(s), "ai-b"))
    add("an AI profile lacking answer", "finding:profile-mismatch", lambda s: assign(company(s), "web-search"))
    add("an AI profile with no research declaration", "finding:profile-mismatch", lambda s: assign(company(s), "plain"))
    add("a web profile lacking the capability it serves", "finding:profile-mismatch", lambda s: assign(company(s), page="web-search"))
    add("a web profile not of class generated", "finding:profile-mismatch", lambda s: assign(company(s), search="web-record"))
    add("a web profile that declares another model", "finding:profile-mismatch", lambda s: assign(company(s), search="web-b"))
    add("an old profile digest", "finding:profile-mismatch", lambda s: company(s).__setitem__("profileDigest", "sha256:" + "0" * 64))
    add("an untrusted profile", "finding:profile-mismatch", lambda s: company(s).__setitem__("profile", "elsewhere"))
    add("a binding naming an old profile digest", "finding:profile-mismatch", both(lambda s: s.unbound.add("company"), after(lambda d: d["binding"]["sources"]["company"]["webProfiles"]["page"].__setitem__("profileDigest", "sha256:" + "0" * 64))))
    add("a binding naming a profile of another model", "finding:profile-mismatch", both(lambda s: s.unbound.add("company"), lambda s: assign(company(s), "ai-b")))
    add("a retained response through a trusted, unassigned profile", "finding:profile-mismatch", lambda s: s.records["company"]["responses"][1].__setitem__("profile", "web-search"))
    add("a retained response naming an untrusted profile", "finding:profile-mismatch", lambda s: s.records["company"]["responses"][1].__setitem__("profile", "elsewhere"))
    add("a retained response naming another digest", "finding:profile-mismatch", lambda s: s.records["company"]["responses"][2].__setitem__("digest", "sha256:" + "0" * 64))
    add("the research record not acquired", "finding:acquisition-missing", after(lambda d: d["acquisitions"].pop("company")))
    add("a cited response whose bytes are not retained", "finding:acquisition-missing", after(lambda d: record(d)["responses"][2].pop("result")))
    add("a retained result changed", "finding:acquisition-invalid", after(lambda d: record(d)["responses"][1]["result"].__setitem__("hits", [])))
    add("a retained request changed", "finding:acquisition-invalid", after(lambda d: record(d)["responses"][0]["request"].__setitem__("prompt", "Which?")))
    add("the fields changed under the record's own receipt", "finding:acquisition-invalid", both(lambda s: s.own.add("company"), after(lambda d: record(d)["fields"]["employee-count"].__setitem__("value", 1))))
    add("the record's own receipt over another request", "finding:acquisition-invalid", both(lambda s: s.own.add("company"), lambda s: s.receipt_hooks.append(lambda n, i, r: r.__setitem__("argumentsCommitment", "sha256:" + "0" * 64) if i == "own" else None)))
    add("a retained receipt of another source", "finding:acquisition-invalid", lambda s: s.receipt_hooks.append(lambda n, i, r: r.__setitem__("source", "elsewhere") if i == 1 else None))
    add("an expired retained receipt", "finding:acquisition-stale", lambda s: s.receipt_hooks.append(lambda n, i, r: r["acquisition"].__setitem__("observedAt", RESEARCH_EXPIRED) if i == 1 else None))
    add("the record's own receipt expired", "finding:acquisition-stale", both(lambda s: s.own.add("company"), lambda s: s.receipt_hooks.append(lambda n, i, r: r.__setitem__("servedAt", RESEARCH_EXPIRED) if i == "own" else None)))
    add("two retained responses at one callIndex", "finding:acquisition-sessions", lambda s: s.call_indices.__setitem__("company", [0, 0, 1]))
    add("the record's own receipt at a retained response's callIndex", "finding:acquisition-sessions", both(lambda s: s.own.add("company"), lambda s: s.call_indices.__setitem__("company", [0, 1, 2, 1])))
    # Round 9 (issue #182 item 4): each receipt's members are held to their forms before the time and session
    # rules, a retained response's and the record's own alike; `sessionId` is any string.
    def receipt_of(index: Any, **members: Any) -> Any:
        def change(n: str, i: Any, r: dict[str, Any]) -> None:
            if i == index:
                for key, value in members.items():
                    if key == "observedAt":
                        r["acquisition"][key] = value
                    else:
                        r[key] = value

        return lambda s: s.receipt_hooks.append(change)

    own = lambda s: s.own.add("company")  # noqa: E731
    invalid = "finding:acquisition-invalid"
    add("a retained receipt's servedAt that is not a string", invalid, receipt_of(1, servedAt=1760529540))
    add("a retained receipt's observedAt with no instant", invalid, receipt_of(2, observedAt="2026-10-15T11:58:30.5Z"))
    add("the record's own receipt's servedAt that names no time", invalid, both(own, receipt_of("own", servedAt="2026-02-30T11:59:00Z")))
    add("the record's own receipt's observedAt that is null", invalid, both(own, receipt_of("own", observedAt=None)))
    add("a retained receipt's callIndex that is a string", invalid, receipt_of(1, callIndex="1"))
    add("a retained receipt's callIndex below zero", invalid, receipt_of(0, callIndex=-1))
    add("a retained receipt's sessionId that is not a string", invalid, receipt_of(2, sessionId=2))
    add("the record's own receipt's sessionId that is null", invalid, both(own, receipt_of("own", sessionId=None)))
    add("an expired retained receipt whose callIndex is a string: the form first", invalid, receipt_of(1, observedAt=RESEARCH_EXPIRED, callIndex="1"))
    add("an expired response before a malformed one: one response's checks complete first", "finding:acquisition-stale", both(
        receipt_of(0, servedAt=RESEARCH_EXPIRED), receipt_of(1, callIndex="1"),
    ))
    # review round of pull request 186: `acquisition.observedAt` moved to the receipt's top level is absent
    def misplaced_at(index: Any) -> Any:
        def change(n: str, i: Any, r: dict[str, Any]) -> None:
            if i == index:
                r["observedAt"] = r["acquisition"].pop("observedAt")

        return lambda s: s.receipt_hooks.append(change)

    add("a retained receipt's observedAt moved to the receipt's top level", invalid, misplaced_at(1))
    add("the record's own receipt's observedAt moved to the receipt's top level", invalid, both(own, misplaced_at("own")))
    add("a sessionId of no token form, shared by every receipt", "reading", both(
        own, lambda s: s.receipt_hooks.append(lambda n, i, r: r.__setitem__("sessionId", "a session, not a token: \u00fcn\u00efcode")),
    ))
    add("a skipped research source with a record", "finding:acquisition-unexpected", both(gate, lambda s: s.records.__setitem__("primary", {"fields": count_answer("not-found"), "responses": []})), "reconcile")
    add("a matched clause's value pointer that does not resolve", "finding:read-failed", lambda s: s.source("combined")["read"]["rule"]["clauses"][0]["claim"]["facts"][0].__setitem__("from", PRIMARY + "/value/min"), "reconcile")
    add("a plain rule's from that does not resolve", "finding:read-failed", both(
        lambda s: company(s).__setitem__("read", {"rule": {"ruleVersion": "1", "parameters": {}, "clauses": [{"when": {"op": "always"}, "claim": {"facts": [{"pointer": "/company/revenue", "from": "/fields/revenue/value"}], "evidence": {}, "acquisitionStatus": "resolved"}, "reason": "always"}]}}),
        lambda s: s.__setattr__("admits", {"/company/revenue": ["generated"]}),
        lambda s: answers(s).__setitem__("revenue", {"status": "not-found", "cites": []}),
    ))
    add("a research target that does not admit generated", "finding:admission-refused", lambda s: s.__setattr__("admits", {"/company/fields": ["record"]}))
    add("the combined value nested beyond 32 levels", over, lambda s: s.records["primary"]["responses"][0].__setitem__("result", json.loads("[" * 29 + "]" * 29)), "reconcile")

    # ---- refusals: the recipe's form ----
    add("a source without fields (pull request 164's form)", malformed, drop(company, "fields"))
    add("a source without capabilities", malformed, drop(company, "capabilities"))
    # Each declaration refusal leaves the record answering only declared fields, so that no other check refuses it.
    unanswered = drop(answers, "revenue")
    add("an empty declaration list", malformed, both(set_in(company, "fields", []), lambda s: s.records["company"].__setitem__("fields", {})))
    add("a declaration of another type", malformed, both(unanswered, lambda s: declaration(s, "revenue").__setitem__("type", "number")))
    add("a declaration whose required is not a boolean", malformed, lambda s: declaration(s, "revenue").__setitem__("required", "no"))
    add("a declaration named case", malformed, both(unanswered, lambda s: declaration(s, "revenue").__setitem__("name", "case")))
    add("a declaration with an empty description", malformed, lambda s: declaration(s, "revenue").__setitem__("description", ""))
    add("a declaration with a member more", malformed, lambda s: declaration(s, "revenue").__setitem__("unit", "EUR"))
    add("a field declared twice", malformed, both(unanswered, lambda s: declaration(s, "revenue").__setitem__("name", "active")))
    add("evidence that is not an array", malformed, set_in(company, "evidence", "the page that states the headcount"))
    add("an empty evidence instruction", malformed, set_in(company, "evidence", [""]))
    add("capabilities without answer", malformed, set_in(company, "capabilities", ["search", "page"]))
    add("capabilities out of order", malformed, set_in(company, "capabilities", ["answer", "page", "search"]))
    add("a capability named twice", malformed, both(set_in(company, "capabilities", ["answer", "search", "search"]), lambda s: company(s)["webProfiles"].pop("page")))
    add("answer named twice", malformed, both(set_in(company, "capabilities", ["answer", "answer"]), set_in(company, "webProfiles", {})))
    add("an unknown capability", malformed, set_in(company, "capabilities", ["answer", "browse"]))
    add("no capability", malformed, set_in(company, "capabilities", []))
    add("the bound form without webProfiles", malformed, drop(company, "webProfiles"))
    add("webProfiles missing a requested capability", malformed, lambda s: company(s)["webProfiles"].pop("page"))
    add("webProfiles assigning an unrequested capability", malformed, set_in(company, "capabilities", ["answer", "search"]))
    add("a web assignment with a member more", malformed, lambda s: company(s)["webProfiles"]["page"].__setitem__("model", "model-a"))
    add("a web assignment whose digest is not a digest", malformed, lambda s: company(s)["webProfiles"]["page"].__setitem__("profileDigest", "sha256:XYZ"))
    add("an operation's catalog member", malformed, set_in(company, "platform", "research"))
    add("a question naming no parameter in scope", malformed, set_in(company, "question", {"$param": "elsewhere"}))
    add("a question that is a number", malformed, set_in(company, "question", 7))
    add("a question that is an object, not a template form", malformed, set_in(company, "question", {"text": "Which?"}))
    add("constraints that are not an object", malformed, set_in(company, "constraints", ["EU"]))
    add("an empty model", malformed, set_in(company, "model", ""))
    add("research in a version-2 dialect", malformed, lambda s: s.dialect.__setitem__("version", 2))
    add("an unbound source with no binding document", malformed, both(lambda s: s.unbound.add("company"), after(lambda d: d.__setitem__("binding", None))))
    add("a binding for another published digest", malformed, both(lambda s: s.unbound.add("company"), after(lambda d: d["binding"].__setitem__("dialect", "sha256:" + "0" * 64))))
    add("a binding without webProfiles", malformed, both(lambda s: s.unbound.add("company"), after(lambda d: d["binding"]["sources"]["company"].pop("webProfiles"))))
    add("a binding assigning an unrequested capability", malformed, both(lambda s: s.unbound.add("company"), set_in(company, "capabilities", ["answer", "search"])))
    add("a binding's web assignment of another form", malformed, both(lambda s: s.unbound.add("company"), after(lambda d: d["binding"]["sources"]["company"]["webProfiles"]["search"].pop("profileDigest"))))
    add("a profile's model without answer", malformed, lambda s: s.profiles[1]["research"].__setitem__("model", "model-a"))
    add("a profile serving answer with no model", malformed, lambda s: s.profiles[0]["research"].pop("model"))
    add("a profile's empty capabilities", malformed, lambda s: s.profiles[1]["research"].__setitem__("capabilities", []))
    add("a profile's research with a member more", malformed, lambda s: s.profiles[1]["research"].__setitem__("weights", "x"))

    # ---- refusals: the record's answers (§4.3, §11's `presence` and `bounds-and-cites`) ----
    add("a record without fields (pull request 164's form)", malformed, after(lambda d: record(d).pop("fields")))
    add("a required entry omitted", malformed, drop(answers, "employee-count"))
    add("an answer for an undeclared field", malformed, set_in(answers, "headcount", {"status": "not-found", "cites": []}))
    add("a null entry", malformed, set_in(answers, "revenue", None))
    add("a null value", malformed, lambda s: answers(s)["revenue"].__setitem__("value", None))
    add("an integer of another type", malformed, lambda s: answers(s)["employee-count"].__setitem__("value", "12"))
    add("an integer with a fraction", malformed, lambda s: answers(s)["employee-count"].__setitem__("value", 12.5))
    add("a numeric decimal", malformed, lambda s: answers(s)["revenue"].__setitem__("value", 12))
    for spelling in ("012", "+1", "1e2", "", "1.", ".5", "1,5"):
        add(f"a decimal spelled {spelling!r}", malformed, lambda s, v=spelling: answers(s)["revenue"].__setitem__("value", v))
    add("a boolean written as a string", malformed, lambda s: answers(s)["active"].__setitem__("value", "false"))
    add("a text that is not a string", malformed, lambda s: answers(s)["company-id"].__setitem__("value", 1))
    add("a null list item", malformed, lambda s: answers(s)["roles"].__setitem__("value", ["buyer", None]))
    add("a null range endpoint", malformed, lambda s: answers(s)["employee-range"].__setitem__("value", {"min": None, "max": "2"}))
    add("mixed range endpoints", malformed, lambda s: answers(s)["employee-range"].__setitem__("value", {"min": 1, "max": "2"}))
    add("a reversed decimal range", malformed, lambda s: answers(s)["employee-range"].__setitem__("value", {"min": "2.5", "max": "2.25"}))
    add("a reversed integer range", malformed, lambda s: answers(s)["employee-range"].__setitem__("value", {"min": 3, "max": -3}))
    add("a range with a unit", malformed, lambda s: answers(s)["employee-range"].__setitem__("value", {"min": 1, "max": 2, "unit": "people"}))
    add("a found entry without cites", malformed, lambda s: answers(s)["revenue"].pop("cites"))
    add("a found entry citing nothing", malformed, lambda s: answers(s)["revenue"].__setitem__("cites", []))
    add("a value on a not-found entry", malformed, lambda s: answers(s)["revenue"].__setitem__("status", "not-found"))
    add("values on a found entry", malformed, lambda s: answers(s)["revenue"].__setitem__("values", [{"value": "1", "cites": [0]}, {"value": "2", "cites": [0]}]))
    add("a conflicting entry with no observation", malformed, set_in(answers, "revenue", {"status": "conflicting", "cites": [], "values": []}))
    add("a conflicting entry of one value", malformed, set_in(answers, "revenue", {"status": "conflicting", "cites": [], "values": [{"value": "1", "cites": [0]}]}))
    add("a conflicting entry whose values do not differ", malformed, set_in(answers, "employee-count", {"status": "conflicting", "cites": [], "values": [{"value": 7, "cites": [0]}, {"value": 7, "cites": [1]}]}))
    add("a conflicting entry with cites of its own", malformed, set_in(answers, "revenue", {"status": "conflicting", "cites": [0], "values": [{"value": "1", "cites": [0]}, {"value": "2", "cites": [1]}]}))
    add("an observation citing nothing", malformed, set_in(answers, "revenue", {"status": "conflicting", "cites": [], "values": [{"value": "1", "cites": []}, {"value": "2", "cites": [1]}]}))
    add("an observation with a member more", malformed, set_in(answers, "revenue", {"status": "conflicting", "cites": [], "values": [{"value": "1", "cites": [0], "url": "https://company.example.test/about"}, {"value": "2", "cites": [1]}]}))
    add("an unknown status", malformed, set_in(answers, "revenue", {"status": "guessed", "cites": []}))
    add("an index -0", malformed, both(lambda s: answers(s)["revenue"].__setitem__("cites", [424242]), lambda s: s.replacements.append(("acquisitions", b"[424242]", b"[-0]"))))
    add("an index at the responses' length", malformed, lambda s: answers(s)["revenue"].__setitem__("cites", [3]))
    add("a negative index", malformed, lambda s: answers(s)["revenue"].__setitem__("cites", [-1]))
    add("an index written with a fraction", malformed, lambda s: answers(s)["revenue"].__setitem__("cites", [1.0]))
    add("an index cited twice", malformed, lambda s: answers(s)["revenue"].__setitem__("cites", [2, 2]))
    add("a URL in place of an index", malformed, lambda s: answers(s)["revenue"].__setitem__("cites", ["https://company.example.test/about"]))

    # ---- refusals: a plain research read's pointers (§4.3, "Reading fields") ----
    read_rule = lambda s: company(s)["read"]["rule"]  # noqa: E731
    add("a plain rule's from under values", malformed, both(rule_read, lambda s: read_rule(s)["clauses"][0]["claim"]["facts"][0].__setitem__("from", "/fields/employee-count/values/0/value")))
    add("a copy from under values", malformed, lambda s: company(s)["read"]["copy"]["facts"][0].__setitem__("source", "/fields/roles/values/0/value"))
    add("a copy of a retained response", malformed, lambda s: company(s)["read"]["copy"]["facts"][0].__setitem__("source", "/responses/0/result"))
    add("a copy of the whole record", malformed, lambda s: company(s)["read"]["copy"]["facts"][0].__setitem__("source", ""))
    add("a condition on an undeclared field", malformed, both(rule_read, lambda s: read_rule(s)["clauses"][1].__setitem__("when", {"op": "exists", "field": "/fields/headcount/status"})))
    add("a pointer below a status", malformed, both(rule_read, lambda s: read_rule(s)["clauses"][1].__setitem__("when", {"op": "exists", "field": "/fields/employee-count/status/0"})))
    add("an observation pointer of another form", malformed, both(rule_read, lambda s: read_rule(s)["clauses"][1].__setitem__("when", {"op": "exists", "field": "/fields/employee-count/values/00/value"})))
    add("an unwrap outside the closed list", malformed, lambda s: company(s)["read"].__setitem__("unwrap", ["/responses/0/result/text"]))

    # ---- refusals: the reconciliation read (§6.4) ----
    combined_read = lambda s: s.source("combined")["read"]  # noqa: E731
    clauses = lambda s: combined_read(s)["rule"]["clauses"]  # noqa: E731
    web_source = {"name": "page", "kind": "web", "profile": "web", "profileDigest": "web", "maxAge": 600, "url": "https://company.example.test/about", "read": {"copy": {"facts": [], "evidence": []}}}
    current_only = {"ruleVersion": "1", "parameters": {}, "clauses": [
        clause(status_guard(CURRENT, "found"), "this source found it", COUNT_TARGET, CURRENT + "/value", "resolved"),
        clause({"op": "any", "of": [absence_guard(CURRENT)] + [status_guard(CURRENT, s) for s in ("not-found", "stale", "conflicting")]}, "not found"),
        clause({"op": "always"}, "otherwise"),
    ]}
    add("no earlier source named", malformed, lambda s: combined_read(s).update({"sources": [], "rule": copy.deepcopy(current_only)}), "reconcile")
    add("a reconciliation of the current source alone", "reading", lambda s: combined_read(s).update({"sources": ["primary"], "rule": copy.deepcopy(current_only)}), "reconcile")
    add("an earlier source named twice", malformed, lambda s: combined_read(s).__setitem__("sources", ["primary", "secondary", "primary"]), "reconcile")
    add("the current source named", malformed, lambda s: combined_read(s).__setitem__("sources", ["primary", "secondary", "combined"]), "reconcile")
    add("a later source named", malformed, lambda s: s.dialect["sources"].insert(1, s.dialect["sources"].pop(2)), "reconcile")
    add("a source that does not exist named", malformed, lambda s: combined_read(s).__setitem__("sources", ["primary", "secondary", "elsewhere"]), "reconcile")
    add("a non-research source named", malformed, both(lambda s: s.dialect["sources"].insert(0, copy.deepcopy(web_source)), lambda s: combined_read(s)["sources"].append("page")), "reconcile")
    add("a non-research source beside, not named", "refusal:kind-unread", lambda s: s.dialect["sources"].insert(0, copy.deepcopy(web_source)), "reconcile")
    add("a reconciliation on another kind", malformed, lambda s: s.dialect["sources"].append({**copy.deepcopy(web_source), "read": copy.deepcopy(combined_read(s))}), "reconcile")
    add("a reconciliation with an unwrap", malformed, lambda s: combined_read(s).__setitem__("unwrap", ["/current"]), "reconcile")
    add("a reconciliation with a copy", malformed, lambda s: combined_read(s).__setitem__("copy", {"facts": [], "evidence": []}), "reconcile")
    add("a reconciliation's from under values", malformed, lambda s: clauses(s)[0]["claim"]["facts"][0].__setitem__("from", PRIMARY + "/values/0/value"), "reconcile")
    add("a reconciliation's from outside the admissible set", malformed, lambda s: clauses(s)[0]["claim"]["facts"][0].__setitem__("from", PRIMARY + "/status"), "reconcile")
    add("a reconciliation's from of a field its source does not declare", malformed, lambda s: clauses(s)[0]["claim"]["facts"][0].__setitem__("from", "/sources/primary/fields/revenue/value"), "reconcile")
    add("a reconciliation's from of a source it does not name", malformed, lambda s: combined_read(s).__setitem__("sources", ["primary"]), "reconcile")
    add("a selecting clause without its found guard", malformed, lambda s: clauses(s)[0].__setitem__("when", {"op": "exists", "field": PRIMARY + "/value"}), "reconcile")
    add("a found guard nested below an all", malformed, lambda s: clauses(s)[1].__setitem__("when", {"op": "all", "of": [unavailable(PRIMARY), {"op": "any", "of": [status_guard(SECONDARY, "found")]}]}), "reconcile")
    for missing in ("not-found", "stale", "conflicting", "absent"):
        add(f"a selected field without its {missing} guard", malformed, lambda s, m=missing: combined_read(s).__setitem__("rule", guarded_rule(without=(m, PRIMARY))), "reconcile")
    add("a reconciliation claim that writes evidence", malformed, both(lambda s: clauses(s)[2]["claim"].__setitem__("evidence", {"company-headcount": "unknown"})), "reconcile")
    add("a last clause that resolves", malformed, lambda s: clauses(s)[-1]["claim"].__setitem__("acquisitionStatus", "resolved"), "reconcile")
    add("a condition outside the reconciliation's pointers", malformed, lambda s: clauses(s)[4].__setitem__("when", {"op": "any", "of": [unavailable(CURRENT), {"op": "exists", "field": "/sources/primary/responses"}]}), "reconcile")
    add("a reconciliation's target that overlaps another's", malformed, lambda s: [c["claim"]["facts"][0].__setitem__("pointer", "/observed/primary/count") for c in clauses(s) if c["claim"]["facts"]], "reconcile")
    add("16 earlier sources named", over, lambda s: combined_read(s).__setitem__("sources", ["primary"] * 16), "reconcile")

    # ---- the maxima of §12: one over each, and every maximum reached (§11's `bounds-and-cites`) ----
    long = lambda n: "x" * n  # noqa: E731
    add("65 fields declared", over, lambda s: company(s)["fields"].extend({"name": f"extra-{i}", "type": "integer", "required": False, "description": "An extra."} for i in range(59)))
    add("65 answer entries, one undeclared", over, lambda s: answers(s).update({f"extra-{i}": {"status": "not-found", "cites": []} for i in range(59)}))
    add("a field name of 65 bytes", over, lambda s: declaration(s, "revenue").__setitem__("name", long(65)))
    # an answer's name is measured before its entry, or whether it is declared (review M1)
    add("an answer named by 65 bytes, undeclared", over, set_in(answers, long(65), {"status": "not-found", "cites": []}))
    add("an answer named by 64 bytes, undeclared", malformed, set_in(answers, long(64), {"status": "not-found", "cites": []}))
    add("an answer named by 65 bytes, its entry malformed", over, set_in(answers, long(65), None))
    # a name declared twice: phase 3 measures by the first declaration whose type is one of the six (review M2)
    twice = lambda first: lambda s: company(s)["fields"].extend([  # noqa: E731
        {"name": "notes", "type": first, "required": False, "description": "Notes."},
        {"name": "notes", "type": "text", "required": False, "description": "Notes again."},
    ])
    long_notes = set_in(answers, "notes", {"status": "found", "value": long(8193), "cites": [0]})
    add("a name declared twice, first of an unknown type: measured as the second, text", over, both(twice("number"), long_notes))
    add("a name declared twice, first an integer: measured as the first, and refused as declared twice", malformed, both(twice("integer"), long_notes))
    add("a description of 2049 bytes", over, lambda s: declaration(s, "revenue").__setitem__("description", long(2049)))
    add("a model of 257 bytes", over, set_in(company, "model", long(257)))
    add("an evidence instruction of 4097 bytes", over, set_in(company, "evidence", [long(4097)]))
    add("a text of 8193 bytes", over, lambda s: answers(s)["company-id"].__setitem__("value", "é" * 4096 + "x"))
    add("a text-list of 65 items", over, lambda s: answers(s)["roles"].__setitem__("value", ["r"] * 65))
    add("a text-list item of 1025 bytes", over, lambda s: answers(s)["roles"].__setitem__("value", [long(1025)]))
    add("a decimal of 129 characters", over, lambda s: answers(s)["revenue"].__setitem__("value", "1" * 129))
    add("a range endpoint of 129 characters", over, lambda s: answers(s)["employee-range"].__setitem__("value", {"min": "1", "max": "1" * 129}))
    add("65 conflicting observations", over, set_in(answers, "employee-count", {"status": "conflicting", "cites": [], "values": [{"value": i, "cites": [0]} for i in range(65)]}))
    add("65 indices in a citation", over, lambda s: answers(s)["revenue"].__setitem__("cites", list(range(65))))
    add("65 indices in an observation's citation", over, set_in(answers, "employee-count", {"status": "conflicting", "cites": [], "values": [{"value": 1, "cites": list(range(65))}, {"value": 2, "cites": [0]}]}))
    add("four capabilities", over, set_in(company, "capabilities", ["answer", "search", "page", "page"]))
    add("a profile of four capabilities", over, lambda s: s.profiles[1]["research"].__setitem__("capabilities", ["search", "page", "page", "page"]))
    add("a profile's model of 257 bytes", over, lambda s: s.profiles[0]["research"].__setitem__("model", long(257)))
    add("three web assignments", over, lambda s: company(s)["webProfiles"].__setitem__("answer", {"profile": "ai", "profileDigest": "ai"}))
    add("three web assignments in a binding", over, both(lambda s: s.unbound.add("company"), after(lambda d: d["binding"]["sources"]["company"]["webProfiles"].__setitem__("answer", {}))))
    add("65 retained responses", over, lambda s: s.records["company"]["responses"].extend([answer_response()] * 62))

    def every_maximum(s: ResearchScenario) -> None:
        source = company(s)
        source["fields"].extend({"name": f"extra-{i:02}", "type": "integer", "required": False, "description": "An extra."} for i in range(57))
        source["fields"].append({"name": long(64), "type": "integer", "required": False, "description": long(2048)})
        source["model"] = long(256)
        source["evidence"] = [long(4096)]
        s.profiles[0]["research"]["model"] = long(256)
        s.records["company"]["responses"] = [answer_response() for _ in range(62)] + [search_response(), page_response()]
        entries = answers(s)
        entries["company-id"]["value"] = "é" * 4096
        entries["roles"]["value"] = ["é" * 512] * 64
        entries["revenue"]["value"] = "-" + "1" * 125 + ".5"
        entries["employee-range"]["value"] = {"min": "1" * 128, "max": "2" + "0" * 127}
        entries["employee-count"] = {"status": "conflicting", "cites": [], "values": [{"value": i, "cites": list(range(64))} for i in range(64)]}
        entries.update({f"extra-{i:02}": {"status": "found", "value": i, "cites": [0]} for i in range(57)})
        entries[long(64)] = {"status": "not-found", "cites": list(range(64))}

    add("every maximum reached", "reading", every_maximum)
    return cases


def answer_code(answer: dict[str, Any]) -> str:
    if "reading" in answer:
        return "reading"
    if "finding" in answer:
        return "finding:" + answer["finding"]
    return "refusal:" + answer["refused"]


class ResearchContractTests(unittest.TestCase):
    """The research contract of RFC 0018's round 8 (spec/dialect.md §§4.3, 4.4, 5.1, 5.2, 6.4, 9, 11, 12), on
    hand-written documents: the first reader's answers here, the second's held equal to them in
    tests/test_dialect_ts.py."""

    def test_every_case_has_the_answer_the_text_gives(self) -> None:
        for name, expected, build in research_cases():
            with self.subTest(case=name):
                answer = build().verify().answer
                self.assertEqual(expected, answer_code(answer), answer.get("detail"))

    def _reading(self, inputs: HandInputs) -> tuple[dict[str, Any], dict[str, Any]]:
        result = inputs.verify()
        self.assertIn("reading", result.answer, result.answer)
        return result.answer["reading"], READER.read_document(result.preparation, "the preparation")

    def test_a_reading_of_every_type(self) -> None:
        # §4.3: the record's fields, copied whole, are the facts; every target is generated, with generated
        # influence (§8.2); the request is the recipe's members, the question instantiated; the lineage's
        # `receipts` are the retained responses' citations, in order, and the record has no `receipt` (§9.3).
        scenario = ResearchScenario()
        reading, preparation = self._reading(scenario.prepared())
        facts = READER.as_plain(reading["facts"])
        self.assertEqual(READER.as_plain(json.loads(json.dumps(company_answers()))), facts["company"]["fields"])
        self.assertEqual({"asserted": 1, "record": 0, "generated": 1}, reading["targetsByClass"])
        outcome = preparation["outcomes"][1]
        self.assertEqual(COMPANY, outcome["arguments"]["question"])
        self.assertEqual({"question", "constraints", "model", "evidence", "fields", "capabilities"}, set(outcome["arguments"]))
        entry = preparation["lineage"][1]
        self.assertEqual(("generated", True), (entry["class"], entry["generatedInfluence"]))
        self.assertNotIn("receipt", entry)
        self.assertEqual(preparation["cites"], entry["receipts"])
        self.assertEqual([0, 1, 2], [READER.integer_of(c["callIndex"]) for c in entry["receipts"]])
        self.assertEqual(["acquisition"], reading["unsignedFreshness"]["sources"][0]["checks"])

    def test_the_records_own_receipt_is_its_receipt_and_its_last_citation(self) -> None:
        scenario = ResearchScenario()
        scenario.own.add("company")
        _, preparation = self._reading(scenario.prepared())
        entry = preparation["lineage"][1]
        self.assertEqual(entry["receipts"][-1], entry["receipt"])
        self.assertEqual([0, 1, 2, 3], [READER.integer_of(c["callIndex"]) for c in preparation["cites"]])

    def test_cites_follow_the_sources_in_a_preparation_with_research(self) -> None:
        # §9.1: in the order of `sources`, a research source adding each retained response's citation in order;
        # not by `callIndex`, as a preparation with no research source is ordered.
        scenario = ResearchScenario("reconcile")
        scenario.call_indices = {"primary": [5], "secondary": [0, 1]}
        _, preparation = self._reading(scenario.prepared())
        self.assertEqual([5, 0, 1], [READER.integer_of(c["callIndex"]) for c in preparation["cites"]])
        receipts = [e.get("receipts") for e in preparation["lineage"]]
        self.assertEqual([None, preparation["cites"][:1], preparation["cites"][1:], []], receipts)

    def test_a_binding_document_yields_the_dialect_bound_directly(self) -> None:
        # §4.4: the bound dialect is the published one with the three assignment members added; a preparation
        # commits it alone, so one bound through a binding document and one given bound have one digest.
        direct = ResearchScenario()
        bound = ResearchScenario()
        bound.unbound.add("company")
        inputs = bound.prepared()
        published = json.loads(inputs.dialect)
        self.assertFalse({"profile", "profileDigest", "webProfiles"} & set(published["sources"][0]))
        reading, preparation = self._reading(inputs)
        self.assertEqual(self._reading(direct.prepared())[0]["digest"], reading["digest"])
        self.assertEqual(research_digest(json.loads(direct.documents().dialect)), preparation["mappingDigest"])

    def test_reconciliation_derives_the_declared_precedence(self) -> None:
        def count(alter: Any) -> Any:
            scenario = ResearchScenario("reconcile")
            alter(scenario)
            reading, preparation = self._reading(scenario.prepared())
            claim = preparation["outcomes"][-1]["claim"]
            return READER.as_plain(reading["facts"]).get("company", {}).get("employee-count"), claim["acquisitionStatus"], claim["reason"]

        records = lambda s: s.records  # noqa: E731
        self.assertEqual((7, "resolved", "the primary found it"), count(lambda s: None))
        self.assertEqual((9, "resolved", "the secondary found it"), count(lambda s: records(s)["primary"].__setitem__("fields", count_answer("not-found"))))
        self.assertEqual((9, "resolved", "the secondary found it"), count(gate))

        def failed(s: ResearchScenario) -> None:
            records(s)["primary"]["fields"] = count_answer("not-found")
            records(s)["secondary"]["fields"] = count_answer("stale")
            records(s)["combined"] = {"fields": count_answer("conflicting"), "responses": [answer_response()]}

        self.assertEqual((None, "unknown", "a conflict is not chosen"), count(failed))

    def test_a_research_rule_names_a_parameter_only_the_records_receipt_commits(self) -> None:
        # §11, unsignedParameters: the question commits the case parameter only under the record's own receipt.
        expected = [{"source": "company", "parameters": [{"name": "company", "kind": "case"}], "targets": 2}]
        cases = {name: build for name, _, build in research_cases()}
        reading, _ = self._reading(cases["a rule names a parameter no receipt commits"]())
        self.assertEqual(expected, READER.as_plain(reading["unsignedParameters"]))
        reading, _ = self._reading(cases["a rule names a parameter the record's own receipt commits"]())
        self.assertNotIn("unsignedParameters", reading)

    def test_an_integer_answer_of_minus_zero_keeps_its_literal(self) -> None:
        cases = {name: build for name, _, build in research_cases()}
        inputs = cases["presence: integer -0, decimal 0, text empty, boolean false"]()
        line = READER.preparation_bytes(READER.report(inputs.verify().answer))
        self.assertIn(b'"employee-count":{"cites":[0,2],"status":"found","value":-0}', line)

    def test_a_record_with_no_response_and_no_receipt_is_acquired(self) -> None:
        cases = {name: build for name, _, build in research_cases()}
        reading, preparation = self._reading(cases["no retained response and no receipt"]())
        self.assertEqual([], preparation["lineage"][1]["receipts"])
        self.assertEqual([], preparation["cites"])
        self.assertEqual("company", reading["unsignedFreshness"]["sources"][0]["source"])

    # Review round 7's research refusals (findings 4 and 5), on the contract's form.

    def test_a_research_record_holds_at_most_64_retained_responses(self) -> None:
        # §§11 and 12: counted in the third phase, before any form; 64 are admitted, 65 are over the bound
        # even when the one beyond is malformed (review round 7, finding 4).
        def answer(retained: int, malformed: bool) -> str:
            scenario = ResearchScenario()
            scenario.records["company"]["responses"].extend([answer_response()] * (retained - 3))
            if malformed:
                scenario.after_hooks.append(lambda d: d["acquisitions"]["company"]["response"]["result"]["responses"].append({}))
            return answer_code(scenario.documents().verify().answer)

        self.assertEqual("finding:preparation-differs", answer(64, False))
        self.assertEqual("refusal:input-over-bound", answer(65, False))
        self.assertEqual("refusal:input-over-bound", answer(64, True))
        self.assertEqual("refusal:input-malformed", answer(63, True))

    def test_a_research_acquisition_has_the_form_of_its_kind(self) -> None:
        # §§4.3, 5.2 and 11 (review round 7, finding 5): the caller-assembled record needs no receipt of its own,
        # both or neither of `receipt` and `salts`, and the record and each retained response held to their form.
        def answer(change: Any = None, own: bool = False) -> str:
            scenario = ResearchScenario()
            if own:
                scenario.own.add("company")
            if change is not None:
                scenario.after_hooks.append(lambda d: change(d["acquisitions"]["company"]["response"]))
            return answer_code(scenario.documents().verify().answer)

        retained = lambda r: r["result"]["responses"][0]  # noqa: E731
        cases = {
            "research-no-own-receipt": (None, "finding:preparation-differs"),
            "research-result-not-retained": (lambda r: retained(r).pop("result"), "finding:acquisition-missing"),
            "research-salts-alone": (lambda r: r.__setitem__("salts", {"args": "0" * 64}), "refusal:input-malformed"),
            "research-record-not-object": (lambda r: r.__setitem__("result", ["x"]), "refusal:input-malformed"),
            "research-record-missing-responses": (lambda r: r["result"].pop("responses"), "refusal:input-malformed"),
            "research-record-bad-responses": (lambda r: r["result"].__setitem__("responses", {}), "refusal:input-malformed"),
            "research-record-extra-member": (lambda r: r["result"].__setitem__("more", 1), "refusal:input-malformed"),
            "not an object": (lambda r: r["result"]["responses"].__setitem__(0, "x"), "refusal:input-malformed"),
            "a member more": (lambda r: retained(r).__setitem__("more", 1), "refusal:input-malformed"),
            "no profile": (lambda r: retained(r).pop("profile"), "refusal:input-malformed"),
            "a profile of another form": (lambda r: retained(r).__setitem__("profile", {"id": "ai"}), "refusal:input-malformed"),
            "a profile digest of another form": (lambda r: retained(r)["profile"].__setitem__("digest", "sha256:XYZ"), "refusal:input-malformed"),
            "a request that is not an object": (lambda r: retained(r).__setitem__("request", "Which?"), "refusal:input-malformed"),
            "a receipt that is not an object": (lambda r: retained(r).__setitem__("receipt", []), "refusal:input-malformed"),
            "salts of another form": (lambda r: retained(r).__setitem__("salts", {"args": "x"}), "refusal:input-malformed"),
        }
        for name, (change, expected) in cases.items():
            with self.subTest(case=name):
                self.assertEqual(expected, answer(change))
        self.assertEqual("finding:preparation-differs", answer(own=True))
        self.assertEqual("refusal:input-malformed", answer(lambda r: r.pop("salts"), own=True))


class DialectTextTests(unittest.TestCase):
    def test_the_rfcs_specification_is_the_companion_text(self) -> None:
        # RFC 0017's choice: the Specification section is the text proposed to land. Here the text
        # is a file too, from which the two readers were written, so the two are held equal: the
        # companion's §§1-14, word for word, each heading one level down in the RFC.
        companion = (ROOT / COMPANION).read_text(encoding="utf-8")
        rfc = (ROOT / RFC).read_text(encoding="utf-8")
        expected = companion[companion.index("\n## 1. ") + 1 :].rstrip("\n")
        start = rfc.index("\n### 1. ") + 1
        section = rfc[start : rfc.index("\n## Alternatives")].rstrip("\n")
        promoted = "\n".join(
            line[1:] if line.startswith("##") else line for line in section.splitlines()
        )
        self.assertEqual(expected, promoted)

    def test_the_rfc_is_accepted_and_its_companion_is_listed_in_core(self) -> None:
        rfc = (ROOT / RFC).read_text(encoding="utf-8")
        self.assertIn("- Status: Accepted", rfc)
        self.assertIn("- Accepted: 2026-10-15", rfc)
        self.assertIn("**Adoption record.**", rfc)
        self.assertNotIn("This is an open proposal", rfc)
        companion = (ROOT / COMPANION).read_text(encoding="utf-8")
        self.assertIn("normative for one\nconformance class, the *preparation verifier* (§14)", companion)
        self.assertNotIn("normative for nothing", companion)
        core = (ROOT / "spec" / "judgment-pack-core.md").read_text(encoding="utf-8")
        normative = core[core.index("### 1.1") : core.index("## 2.")]
        self.assertIn("[`spec/dialect.md`](dialect.md)", normative)
        # The vectors wait for the next specVersion, so §1.1 does not list them yet.
        self.assertNotIn("conformance/dialect", normative)

    def test_the_findings_the_tests_know_are_the_texts(self) -> None:
        companion = (ROOT / COMPANION).read_text(encoding="utf-8")
        section = companion[companion.index("## 11.") : companion.index("## 12.")]
        named = set(re.findall(r"`([a-z]+(?:-[a-z]+)*)`", section))
        refusals = {"input-over-bound", "input-malformed", "version-unread", "kind-unread"}
        self.assertLessEqual(FINDINGS | refusals, named)
        counts = collections.Counter(row["expectedFinding"] for row in json.loads(
            (DIALECT / "manifest.json").read_text(encoding="utf-8"))["cases"] if "expectedFinding" in row)
        self.assertLessEqual(set(counts), FINDINGS)


if __name__ == "__main__":
    unittest.main()

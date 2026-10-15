"""The dialect vectors RFC 0018 stages, and the first reader written from the companion text.

The vectors are the reference Runner's `vectors/preparation/`, byte for byte, staged until the
next specVersion opens (conformance/dialect/README.md). These tests hold their bytes to the digests the Runner's
manifest gives them and the Runner's manifest and README to the digests this repository records;
run tools/dialect_verify.py, a preparation verifier written from spec/dialect.md, over every vector;
and hold the RFC's Specification section to the companion document's text.
"""

from __future__ import annotations

import collections
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
    # The tenth vector, from the Runner's main after its pull request 80 (the amendment of 2026-10-15); the
    # eleventh and twelfth, of dialect version 3, from its main after its pull request 83.
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
    ],
}
# The count as the RFC and the companion spell it.
WORDS = {9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}
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
        # The companion's Status names the Runner commits its vectors were copied from, and counts the vectors
        # of the commits it names: twelve, from three commits, since the amendment that read version 3.
        text = " ".join((ROOT / COMPANION).read_text(encoding="utf-8").split())
        source = self.manifest["source"]
        self.assertIn(source["commit"], text)
        count = len(self.manifest["cases"]) - sum(len(e["vectors"]) for e in source["extendedBy"])
        count += sum(len(e["vectors"]) for e in source["extendedBy"] if e["commit"] in text)
        self.assertIn(f"Its {WORDS[count]} vectors", text)

    def test_the_first_reader_recomputes_every_preparation(self) -> None:
        # The preparation's canonical bytes, recomputed from the dialect, the case, the acquisitions
        # and the profiles at the given preparation's instant, are the Runner's, byte for byte.
        for vector in self.runner["vectors"]:
            name = vector["name"]
            with self.subTest(vector=name):
                outcome = self.inputs(name).verify()
                self.assertEqual((VECTORS / name / "preparation.json").read_bytes(), outcome.preparation)
                self.assertEqual((VECTORS / name / "preparation.sha256").read_text(), outcome.digest)
                self.assertEqual(vector["preparation"]["sha256"], outcome.digest)
                self.assertEqual(
                    vector["preparation"]["binding"].encode("ascii"), READER.binding_of(outcome.digest)
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
        """The vector's inputs altered: each profile, then the dialect, each source's profileDigest set to its
        profile's, then each receipt, committed to `request` when one is given and signed again under a key of
        the test's own."""
        inputs = self.inputs(name)
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
        for member in sources.values():
            response = member["response"]
            signed = response["receipt"]
            if receipt is not None:
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
        # The Runner's manifest marks the vector of a dialect bound at import and says which file is which; it
        # is the one vector that holds a binding document, and the one this repository reads unbound.json of.
        for vector in self.runner["vectors"]:
            with self.subTest(vector=vector["name"]):
                held = (VECTORS / vector["name"] / "binding.json").is_file()
                self.assertEqual(held, "import" in vector)
                if held:
                    self.assertEqual(
                        {"published": "unbound.json", "binding": "binding.json", "bound": "mapping.json"}, vector["import"]
                    )

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
        bound = json.loads(self.inputs("version-3-bound").dialect)["sources"][0]
        common = {"profile": bound["profile"], "profileDigest": bound["profileDigest"], "maxAge": 300, "read": {"copy": {"facts": [], "evidence": []}}}
        string = {"$param": "invoiceCurrency"}
        well_formed = {
            "http": {"method": "POST", "path": "/requests", "query": {"currency": string}, "body": {"n": 1}, "headers": ["Accept"]},
            "sql": {"statement": "SELECT 1 WHERE c = :c", "bindings": [{"name": "c", "type": "STRING", "value": string}]},
            "web": {"url": string},
            "research": {"question": {"$text": "Which?"}, "constraints": {}, "model": "a-model", "evidence": ["excerpt"]},
        }
        malformed = {
            "http": [{"method": "PUT"}, {"path": {"a": 1}}, {"path": {"$param": "runAt"}}, {"method": "GET"}, {"query": {"currency": 7}}, {"headers": "Accept"}],
            "sql": [{"statement": {"$text": "SELECT 1"}}, {"bindings": [{"name": "c", "type": "STRING", "value": "EUR"}]}, {"bindings": [{"name": "c", "value": string}]}],
            "web": [{"url": 7}, {"url": {"$param": "nope"}}, {"url": {"$text": "https://example.org/"}}],
            "research": [{"question": 7}, {"constraints": []}, {"model": None}, {"evidence": "excerpt"}],
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

    def _researched(self, acquisition: Any) -> Any:
        """version-3-bound with a `research` source added, its acquisition the given member."""
        inputs = self.inputs("version-3-bound")
        document = json.loads(inputs.dialect)
        bound = document["sources"][0]
        document["sources"].append({
            "name": "study", "kind": "research", "profile": bound["profile"], "profileDigest": bound["profileDigest"],
            "maxAge": 300, "question": "Which?", "constraints": {}, "model": "a-model", "evidence": ["excerpt"],
            "read": {"copy": {"facts": [], "evidence": []}},
        })
        inputs.dialect = json.dumps(document).encode("utf-8")
        sources = json.loads(inputs.acquisitions)
        sources["study"] = acquisition
        inputs.acquisitions = json.dumps(sources).encode("utf-8")
        return inputs.verify().answer

    RETAINED = {
        "profile": {"id": "fx", "digest": "sha256:" + "0" * 64},
        "request": {"question": "Which?"},
        "result": {"answer": "none"},
        "receipt": {},
        "salts": {"args": "0" * 64},
    }

    def test_a_research_record_holds_at_most_64_retained_responses(self) -> None:
        # §§11 and 12: counted in the third phase, before any form; 64 are admitted, 65 are over the bound
        # even when the one beyond is malformed (review round 7, finding 4).
        record = lambda responses: {"response": {"result": {"responses": responses}}}  # noqa: E731
        self.assertEqual("kind-unread", self._researched(record([self.RETAINED] * 64)).get("refused"))
        self.assertEqual("input-over-bound", self._researched(record([self.RETAINED] * 65)).get("refused"))
        self.assertEqual("input-over-bound", self._researched(record([self.RETAINED] * 64 + [{}])).get("refused"))
        self.assertEqual("input-malformed", self._researched(record([self.RETAINED] * 63 + [{}])).get("refused"))

    def test_a_research_acquisition_has_the_form_of_its_kind(self) -> None:
        # §§4.3, 5.2 and 11 (review round 7, finding 5): the caller-assembled record needs no receipt of its own,
        # both or neither of `receipt` and `salts`, and the record and each retained response held to their form
        # before the kind is refused as unread.
        own = {"receipt": {}, "salts": {"args": "0" * 64}}
        retained = self.RETAINED
        unretained = {k: v for k, v in retained.items() if k != "result"}
        cases = {
            "research-no-own-receipt": ({"response": {"result": {"responses": []}}}, "kind-unread"),
            "research-own-receipt": ({"response": {"result": {"responses": [retained]}, **own}}, "kind-unread"),
            "research-result-not-retained": ({"response": {"result": {"responses": [unretained]}}}, "kind-unread"),
            "research-receipt-alone": ({"response": {"result": {"responses": []}, "receipt": {}}}, "input-malformed"),
            "research-salts-alone": ({"response": {"result": {"responses": []}, "salts": own["salts"]}}, "input-malformed"),
            "research-record-not-object": ({"response": {"result": ["x"]}}, "input-malformed"),
            "research-record-missing-responses": ({"response": {"result": {}}}, "input-malformed"),
            "research-record-bad-responses": ({"response": {"result": {"responses": {}}}}, "input-malformed"),
            "research-record-extra-member": ({"response": {"result": {"responses": [], "more": 1}}}, "input-malformed"),
        }
        malformed_retained = {
            "not an object": "x",
            "a member more": {**retained, "more": 1},
            "no profile": {k: v for k, v in retained.items() if k != "profile"},
            "a profile of another form": {**retained, "profile": {"id": "fx"}},
            "a profile digest of another form": {**retained, "profile": {"id": "fx", "digest": "sha256:XYZ"}},
            "a request that is not an object": {**retained, "request": "Which?"},
            "a receipt that is not an object": {**retained, "receipt": []},
            "salts of another form": {**retained, "salts": {"args": "x"}},
        }
        for name, entry in malformed_retained.items():
            cases[f"research-record-malformed-retained ({name})"] = (
                {"response": {"result": {"responses": [entry]}}}, "input-malformed")
        for name, (acquisition, expected) in cases.items():
            with self.subTest(case=name):
                self.assertEqual(expected, self._researched(acquisition).get("refused"))
        # an acquisition of any other kind still has its receipt and salts
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

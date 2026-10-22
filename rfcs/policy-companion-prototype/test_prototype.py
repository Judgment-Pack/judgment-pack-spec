"""Targeted proposal checks, intentionally outside the normative test/corpus trees."""

import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import verify as v


class PrototypeTests(unittest.TestCase):
    def setUp(self):
        self.manifest, self.material, self.policy, self.adoption = v.load_bundle(v.HERE / "examples" / "data-access")

    def reject(self, callback, text=None):
        with self.assertRaises(v.PrototypeError) as caught:
            callback()
        if text:
            self.assertIn(text, str(caught.exception))

    def retain(self, document):
        raw = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        content = v.identity(raw, "application/json")
        v.register_material(content, raw, self.material)
        return content

    def consumer(self):
        return v.read_json(v.resolve(self.adoption["consumer"]["content"], self.material))

    def retain_consumer(self, document):
        reference = self.adoption["consumer"]
        reference["content"] = self.retain(document)
        reference["canonicalIdentity"] = v.canonical_identity(v.resolve(reference["content"], self.material))

    def test_three_synthetic_domains_and_all_coverage_states(self):
        states, kinds = set(), set()
        for directory in sorted((v.HERE / "examples").iterdir()):
            with self.subTest(domain=directory.name):
                self.assertEqual(v.verify_bundle(directory), directory.name)
                _, _, _, adoption = v.load_bundle(directory)
                states.update(item["status"] for item in adoption["governingPolicies"][0]["coverage"])
                kinds.update(element["kind"] for item in adoption["governingPolicies"][0]["coverage"] for element in item.get("consumerElements", []))
        self.assertEqual(states, {"implemented", "manual", "awaiting-interpretation", "awaiting-implementation", "out-of-scope"})
        self.assertEqual(kinds, {"rule", "exception", "applicability", "fallback"})

    def test_version_grammar_and_current_256_character_bound(self):
        for value in ("0.0.0", "10.2.300", "9" * 252 + ".0.0"):
            with self.subTest(valid=value):
                v.parse_version(value)
                self.policy["version"] = value
                v.check_schema("policy", self.policy)
        for value in (True, 1, "", "1.0", "01.0.0", "1.00.0", "1.0.01", "-1.0.0", "1.0.0-rc.1", "1.0.0+build", "1.0.0\n", " 1.0.0", "١.0.0", "9" * 253 + ".0.0"):
            with self.subTest(invalid=value):
                self.reject(lambda: v.parse_version(value), "invalid artifact version")
                self.policy["version"] = value
                self.reject(lambda: v.check_schema("policy", self.policy), "schema")

    def test_strict_json_and_canon_domain_before_schema(self):
        for raw in (b'{"a":1,"a":2}', b'"\\ud800"', b'\xef\xbb\xbf{}', b'{}{}', b'1.0', b'1e2', b'9007199254740992', b'NaN', b'"\xff"'):
            with self.subTest(raw=raw):
                self.reject(lambda: v.read_json(raw), "invalid JSON/canon domain")
        self.assertEqual(v.read_json(b'{"zero":-0}'), {"zero": 0})
        self.reject(lambda: v.read_json(b"[" * 33 + b"0" + b"]" * 33), "invalid JSON/canon domain")
        self.reject(lambda: v.read_json(b" " * (v.MAX_DOCUMENT_BYTES + 1)), "byte bound")

    def test_profile_is_explicitly_unadopted_and_exact(self):
        for field, value in (("status", "adopted"), ("proposalVersion", "0.0.1"), ("proposalVersion", "0.0.3"), ("profile", "unknown-profile")):
            changed = copy.deepcopy(self.policy)
            changed["prototype"][field] = value
            self.reject(lambda: v.check_schema("policy", changed), "schema")
            changed = copy.deepcopy(self.adoption)
            changed["prototype"][field] = value
            self.reject(lambda: v.check_adoption(changed, self.material), "schema")
        for field in ("formatVersion", "specVersion", "proposalVersion"):
            changed = copy.deepcopy(self.policy)
            changed[field] = "0.0.2"
            self.reject(lambda: v.check_schema("policy", changed), "schema")

    def test_closed_objects_refuse_live_authority_and_decision_language(self):
        for field in ("approved", "published", "effectiveAt", "permissions", "signatures", "rules", "requirements"):
            changed = copy.deepcopy(self.policy)
            changed[field] = True
            self.reject(lambda: v.check_schema("policy", changed), "schema")
        self.policy["sourceProvenance"][0]["source"]["credential"] = "fictional"
        self.reject(lambda: v.check_schema("policy", self.policy), "schema")
        self.adoption["governingPolicies"][0]["coverage"][0]["authorized"] = True
        self.reject(lambda: v.check_schema("governing-adoption", self.adoption), "schema")

    def test_readable_structured_requirements_are_explicitly_unsupported(self):
        self.policy["requirements"] = [{"id": "retention", "sectionId": "eligibility", "text": "Keep a record."}]
        self.reject(lambda: v.check_policy(self.policy, self.material), "schema")
        del self.policy["requirements"]
        self.policy["sections"][0]["requirements"] = ["Keep a record."]
        self.reject(lambda: v.check_policy(self.policy, self.material), "schema")

    def test_uri_digest_and_integer_assertions(self):
        for field, value in (("id", "not an absolute URI"), ("content", {"bytesDigest": "sha256:" + "A" * 64, "byteLength": 1, "mediaType": "text/plain"}), ("content", {"bytesDigest": "sha256:" + "a" * 64, "byteLength": True, "mediaType": "text/plain"})):
            changed = copy.deepcopy(self.policy)
            changed[field] = value
            self.reject(lambda: v.check_schema("policy", changed), "schema")

    def test_original_bytes_are_separate_from_narrative_offsets(self):
        original = b"%PDF-synthetic-original-\xff"
        content = v.identity(original, "application/pdf")
        v.register_material(content, original, self.material)
        self.policy["sourceProvenance"][0]["content"] = content
        v.check_policy(self.policy, self.material)
        self.assertNotEqual(content, self.policy["content"])

    def test_original_role_accepts_four_mib_and_other_roles_keep_one_mib(self):
        raw = b"x" * v.MAX_ORIGINAL_BYTES
        original = v.identity(raw, "text/plain")
        v.register_material(original, raw, self.material)
        self.policy["sourceProvenance"][0]["content"] = original
        v.check_policy(self.policy, self.material)
        self.assertEqual(v.resolve(original, self.material, v.MAX_ORIGINAL_BYTES), raw)
        self.reject(lambda: v.resolve(original, self.material), "role byte bound")
        # The same digest can serve multiple roles only within each role's bound.
        self.policy["content"] = original
        self.reject(lambda: v.check_policy(self.policy, self.material), "schema")
        coverage = self.adoption["governingPolicies"][0]["coverage"][0]
        basis = coverage["reviewBasis"]
        coverage["reviewBasis"] = original
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "schema")
        coverage["reviewBasis"] = basis
        self.adoption["informationalSources"] = [original]
        self.reject(lambda: v.check_schema("governing-adoption", self.adoption), "schema")
        oversized = v.identity(raw + b"x", "application/pdf")
        self.reject(lambda: v.register_material(oversized, raw + b"x", self.material), "schema")
        self.policy["sourceProvenance"][0]["content"] = oversized
        self.reject(lambda: v.check_schema("policy", self.policy), "schema")

    def test_narrative_review_and_informational_role_boundaries(self):
        narrative = v.resolve(self.policy["content"], self.material)
        raw = narrative + b" " * (v.MAX_MATERIAL_BYTES - len(narrative))
        content = v.identity(raw, "text/plain")
        v.register_material(content, raw, self.material)
        self.policy["content"] = content
        v.check_policy(self.policy, self.material)
        coverage = self.adoption["governingPolicies"][0]["coverage"][0]
        coverage["reviewBasis"] = content
        self.adoption["informationalSources"] = [content]
        v.check_adoption(self.adoption, self.material)
        overflow = v.identity(raw + b" ", "text/plain")
        v.register_material(overflow, raw + b" ", self.material)
        for role in ("narrative", "review", "informational"):
            with self.subTest(role=role):
                changed_policy = copy.deepcopy(self.policy)
                changed_adoption = copy.deepcopy(self.adoption)
                if role == "narrative":
                    changed_policy["content"] = overflow
                    self.reject(lambda: v.check_policy(changed_policy, self.material), "schema")
                else:
                    if role == "review":
                        changed_adoption["governingPolicies"][0]["coverage"][0]["reviewBasis"] = overflow
                    else:
                        changed_adoption["informationalSources"] = [overflow]
                    self.reject(lambda: v.check_adoption(changed_adoption, self.material), "schema")

    def test_registration_aggregate_counts_blob_once_and_rejects_overflow_atomically(self):
        material = {}
        for index in range(4):
            raw = bytes([index]) * v.MAX_ORIGINAL_BYTES
            v.register_material(v.identity(raw, "application/pdf"), raw, material)
        raw = material[next(iter(material))][0]
        second_type = v.identity(raw, "text/plain")
        v.register_material(second_type, raw, material)
        self.assertEqual(len(material), 4)
        self.assertEqual(v.resolve(second_type, material, v.MAX_ORIGINAL_BYTES), raw)
        overflow = v.identity(b"x", "text/plain")
        self.reject(lambda: v.register_material(overflow, b"x", material), "aggregate retained byte bound")
        self.assertNotIn(overflow["bytesDigest"], material)
        malformed = {**second_type, "byteLength": True}
        self.reject(lambda: v.register_material(malformed, raw, material), "schema")
        self.reject(lambda: v.resolve(malformed, material), "schema")

    def test_fixture_loader_aggregate_boundary_and_oversized_original_refusal(self):
        manifest = copy.deepcopy(self.manifest)
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for entry in manifest["materials"]:
                (directory / entry["path"]).write_bytes(v.resolve(entry["content"], self.material))
            remaining = v.MAX_TOTAL_MATERIAL_BYTES - sum(len(value[0]) for value in self.material.values())
            for index in range(4):
                length = min(v.MAX_ORIGINAL_BYTES, remaining)
                raw = bytes([index]) * length
                name = "retained-%s.pdf" % index
                (directory / name).write_bytes(raw)
                manifest["materials"].append({"path": name, "content": v.identity(raw, "application/pdf")})
                remaining -= length
            (directory / "fixture.json").write_text(json.dumps(manifest))
            _, material, _, _ = v.load_bundle(directory)
            self.assertEqual(sum(len(value[0]) for value in material.values()), v.MAX_TOTAL_MATERIAL_BYTES)
            # A second registered type for the same bytes does not spend more budget.
            duplicate = copy.deepcopy(manifest["materials"][-1])
            duplicate["path"] = "same-bytes.txt"
            duplicate["content"]["mediaType"] = "text/plain"
            (directory / duplicate["path"]).write_bytes(material[duplicate["content"]["bytesDigest"]][0])
            manifest["materials"].append(duplicate)
            (directory / "fixture.json").write_text(json.dumps(manifest))
            v.load_bundle(directory)
            extra = {"path": "overflow.pdf", "content": v.identity(b"x", "application/pdf")}
            (directory / extra["path"]).write_bytes(b"x")
            manifest["materials"].append(extra)
            (directory / "fixture.json").write_text(json.dumps(manifest))
            self.reject(lambda: v.load_bundle(directory), "aggregate retained byte bound")
            manifest["materials"] = [extra]
            raw = b"x" * (v.MAX_ORIGINAL_BYTES + 1)
            extra["content"] = v.identity(raw, "application/pdf")
            (directory / extra["path"]).write_bytes(raw)
            (directory / "fixture.json").write_text(json.dumps(manifest))
            self.reject(lambda: v.load_bundle(directory), "schema")
            extra["content"]["byteLength"] = v.MAX_ORIGINAL_BYTES
            (directory / "fixture.json").write_text(json.dumps(manifest))
            self.reject(lambda: v.load_bundle(directory), "local file byte bound")

    def test_identical_markdown_original_and_plain_narrative_bundle(self):
        manifest = copy.deepcopy(self.manifest)
        payloads = {entry["path"]: v.resolve(entry["content"], self.material) for entry in manifest["materials"]}
        narrative = v.resolve(self.policy["content"], self.material)
        original = self.policy["sourceProvenance"][0]["content"]
        source_entry = next(entry for entry in manifest["materials"] if entry["content"] == original)
        source_entry["path"] = "original.md"
        source_entry["content"] = v.identity(narrative, "text/markdown")
        payloads["original.md"] = narrative
        policy = copy.deepcopy(self.policy)
        policy["sourceProvenance"][0]["content"] = source_entry["content"]
        policy_raw = (json.dumps(policy, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        payloads[manifest["policy"]] = policy_raw
        adoption = copy.deepcopy(self.adoption)
        reference = adoption["governingPolicies"][0]["policy"]
        reference["content"] = v.identity(policy_raw, "application/json")
        reference["canonicalIdentity"] = v.canonical_identity(policy_raw)
        payloads[manifest["adoption"]] = (json.dumps(adoption, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for entry in manifest["materials"]:
                raw = payloads[entry["path"]]
                entry["content"] = v.identity(raw, entry["content"]["mediaType"])
                (directory / entry["path"]).write_bytes(raw)
            (directory / "fixture.json").write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(v.verify_bundle(directory), "data-access")
            _, material, loaded, _ = v.load_bundle(directory)
            self.assertEqual(v.resolve(loaded["content"], material), narrative)
            self.assertEqual(v.resolve(loaded["sourceProvenance"][0]["content"], material), narrative)

    def test_material_requires_registered_media_type_and_exact_length(self):
        content = self.policy["content"]
        raw = v.resolve(content, self.material)
        markdown = v.identity(raw, "text/markdown")
        self.reject(lambda: v.resolve(markdown, self.material), "unregistered retained material media type")
        v.register_material(markdown, raw, self.material)
        self.assertEqual(v.resolve(markdown, self.material), raw)
        self.assertEqual(v.resolve(content, self.material), raw)
        html = v.identity(raw, "text/html")
        self.reject(lambda: v.resolve(html, self.material), "unregistered retained material media type")
        wrong_length = {**markdown, "byteLength": len(raw) + 1}
        self.reject(lambda: v.resolve(wrong_length, self.material), "byte identity")
        self.reject(lambda: v.register_material(wrong_length, raw, self.material), "byte identity")

    def test_material_registration_rejects_conflicting_bytes_and_wrong_digest(self):
        content = self.policy["content"]
        raw = v.resolve(content, self.material)
        markdown = v.identity(raw, "text/markdown")
        self.reject(lambda: v.register_material(markdown, raw + b"changed", self.material), "conflicting retained material bytes")
        self.reject(lambda: v.resolve(markdown, self.material), "unregistered retained material media type")
        self.assertEqual(v.resolve(content, self.material), raw)
        wrong_digest = {**markdown, "bytesDigest": "sha256:" + "0" * 64}
        self.reject(lambda: v.register_material(wrong_digest, raw, self.material), "byte identity")
        self.reject(lambda: v.resolve(wrong_digest, self.material), "missing retained material")

    def test_non_utf8_policy_narrative_is_refused(self):
        raw = b"\xff"
        content = v.identity(raw, "text/plain")
        v.register_material(content, raw, self.material)
        self.policy["content"] = content
        self.reject(lambda: v.check_policy(self.policy, self.material), "narrative is not UTF-8")

    def test_missing_and_altered_retained_bytes_refused(self):
        self.policy["content"]["bytesDigest"] = "sha256:" + "0" * 64
        self.reject(lambda: v.check_policy(self.policy, self.material), "missing retained material")
        _, material, policy, _ = v.load_bundle(v.HERE / "examples" / "data-access")
        key = policy["content"]["bytesDigest"]
        material[key] = (material[key][0] + b"changed", {"text/plain"})
        self.reject(lambda: v.check_policy(policy, material), "byte identity")

    def test_anchor_range_digest_and_utf8_boundaries(self):
        raw = v.resolve(self.policy["content"], self.material)
        unicode_start = raw.index("—".encode("utf-8"))
        for start, end, expected in ((0, len(raw) + 1, "outside narrative"), (10, 10, "outside narrative"), (unicode_start + 1, unicode_start + 2, "splits a UTF-8 sequence"), (0, 5, "anchor digest mismatch")):
            changed = copy.deepcopy(self.policy)
            changed["sections"][0]["anchor"].update({"startByte": start, "endByte": end})
            self.reject(lambda: v.check_policy(changed, self.material), expected)

    def test_duplicate_section_source_and_unresolved_source_refs(self):
        changed = copy.deepcopy(self.policy)
        duplicate = copy.deepcopy(changed["sections"][0]); duplicate["title"] = "Different title"
        changed["sections"].append(duplicate)
        self.reject(lambda: v.check_policy(changed, self.material), "duplicate section")
        changed = copy.deepcopy(self.policy)
        duplicate = copy.deepcopy(changed["sourceProvenance"][0]); duplicate["sourceRevision"] = "different"
        changed["sourceProvenance"].append(duplicate)
        self.reject(lambda: v.check_policy(changed, self.material), "duplicate source")
        self.policy["sections"][0]["sourceRefs"][0]["sourceId"] = "missing"
        self.reject(lambda: v.check_policy(self.policy, self.material), "unknown section source")

    def test_exact_consumer_identity_and_rule_refs(self):
        for field, value in (("id", "urn:example:other-pack"), ("version", "2.0.0")):
            changed = copy.deepcopy(self.adoption)
            changed["consumer"][field] = value
            self.reject(lambda: v.check_adoption(changed, self.material), "artifact identity mismatch")
        self.adoption["governingPolicies"][0]["coverage"][0]["consumerElements"][0]["id"] = "missing-rule"
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "unknown consumer rule")

    def test_each_typed_element_can_alone_cover_a_section(self):
        pack = self.consumer()
        pack["applicability"] = {"op": "literal", "value": True}
        pack["exceptions"] = [{"id": "route-review", "description": "Synthetic review routing", "when": {"op": "literal", "value": False}, "effect": "escalate", "onUnknown": "escalate"}]
        self.retain_consumer(pack)
        coverage = self.adoption["governingPolicies"][0]["coverage"][0]
        for element in ({"kind": "rule", "id": "eligible"}, {"kind": "exception", "id": "route-review"}, {"kind": "applicability"}, {"kind": "fallback"}):
            with self.subTest(element=element):
                coverage["consumerElements"] = [element]
                v.check_adoption(self.adoption, self.material)

    def test_element_grammar_refuses_kind_id_confusion_and_unsupported_kinds(self):
        for element in ({"kind": "applicability", "id": "eligible"}, {"kind": "fallback", "id": "review"}, {"kind": "rule"}, {"kind": "exception"}, {"kind": "rule", "id": "eligible", "path": "/rules/0"}, {"kind": "outcome", "id": "review"}, {"kind": "evidenceRequirement", "id": "record"}, {"kind": "condition"}, {"kind": "escalation"}, {"kind": "fallbackOutcome"}):
            with self.subTest(element=element):
                self.adoption["governingPolicies"][0]["coverage"][0]["consumerElements"] = [element]
                self.reject(lambda: v.check_adoption(self.adoption, self.material), "schema")

    def test_absent_singletons_and_unknown_exception_references_refuse(self):
        pack = self.consumer()
        del pack["fallbackOutcome"]
        self.retain_consumer(pack)
        coverage = self.adoption["governingPolicies"][0]["coverage"][0]
        for element, message in (({"kind": "fallback"}, "missing consumer fallback"), ({"kind": "applicability"}, "missing consumer applicability"), ({"kind": "exception", "id": "eligible"}, "unknown consumer exception")):
            coverage["consumerElements"] = [element]
            self.reject(lambda: v.check_adoption(self.adoption, self.material), message)

    def test_rule_and_exception_ids_have_separate_namespaces(self):
        pack = self.consumer()
        pack["exceptions"] = [{"id": "eligible", "description": "Different element with a shared local spelling", "when": {"op": "literal", "value": False}, "effect": "suppress-rule", "targetRule": "eligible", "onUnknown": "ignore"}]
        self.retain_consumer(pack)
        coverage = self.adoption["governingPolicies"][0]["coverage"][0]
        coverage["consumerElements"] = [{"kind": "rule", "id": "eligible"}, {"kind": "exception", "id": "eligible"}]
        v.check_adoption(self.adoption, self.material)
        pack["exceptions"][0]["id"] = "exception-only"
        self.retain_consumer(pack)
        coverage["consumerElements"] = [{"kind": "rule", "id": "exception-only"}]
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "unknown consumer rule")

    def test_duplicate_element_references_refuse_in_one_record(self):
        pack = self.consumer()
        pack["applicability"] = {"op": "literal", "value": True}
        pack["exceptions"] = [{"id": "review-routing", "description": "Synthetic routing", "when": {"op": "literal", "value": False}, "effect": "escalate", "onUnknown": "ignore"}]
        self.retain_consumer(pack)
        coverage = self.adoption["governingPolicies"][0]["coverage"][0]
        for element in ({"kind": "rule", "id": "eligible"}, {"kind": "exception", "id": "review-routing"}, {"kind": "applicability"}, {"kind": "fallback"}):
            with self.subTest(element=element):
                coverage["consumerElements"] = [element, copy.deepcopy(element)]
                self.reject(lambda: v.check_adoption(self.adoption, self.material), "schema")

    def test_consumer_duplicate_ids_and_dangling_executable_targets_refuse(self):
        original = self.consumer()
        original["exceptions"] = [{"id": "review-routing", "description": "Synthetic routing", "when": {"op": "literal", "value": False}, "effect": "escalate", "onUnknown": "ignore"}]
        for collection, text in (("rules", "consumer rule"), ("exceptions", "consumer exception"), ("outcomes", "consumer outcome")):
            with self.subTest(collection=collection):
                pack = copy.deepcopy(original)
                duplicate = copy.deepcopy(pack[collection][0])
                duplicate["description"] = "Distinct object reusing the same ID"
                pack[collection].append(duplicate)
                self.retain_consumer(pack)
                self.reject(lambda: v.check_adoption(self.adoption, self.material), "duplicate " + text)
        for member, effect, text in (("targetRule", "suppress-rule", "exception target rule"), ("outcome", "force-outcome", "exception outcome")):
            pack = copy.deepcopy(original)
            pack["exceptions"][0].update({"effect": effect, member: "missing"})
            self.retain_consumer(pack)
            self.reject(lambda: v.check_adoption(self.adoption, self.material), "unknown consumer " + text)
        pack = copy.deepcopy(original)
        pack["fallbackOutcome"] = "missing"
        self.retain_consumer(pack)
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "unknown consumer fallback outcome")
        pack = copy.deepcopy(original)
        pack["exceptions"][0]["outcome"] = "eligible"  # Core forbids outcome on escalate.
        self.retain_consumer(pack)
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "core schema")

    def test_consumer_element_reference_count_boundary(self):
        pack = self.consumer()
        rule = pack["rules"][0]
        pack["rules"] = [{**copy.deepcopy(rule), "id": "rule-%s" % index} for index in range(64)]
        self.retain_consumer(pack)
        coverage = self.adoption["governingPolicies"][0]["coverage"][0]
        coverage["consumerElements"] = [{"kind": "rule", "id": item["id"]} for item in pack["rules"]]
        v.check_adoption(self.adoption, self.material)
        coverage["consumerElements"].append({"kind": "fallback"})
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "schema")

    def test_raw_and_canonical_identities_are_not_interchangeable(self):
        reference = self.adoption["consumer"]
        raw = v.resolve(reference["content"], self.material)
        compact = v.spec_canon.canon(v.read_json(raw))
        self.assertNotEqual(v.spec_canon.digest_of(raw), v.spec_canon.digest_of(compact))
        self.assertEqual(reference["canonicalIdentity"]["canonicalDigest"], v.spec_canon.digest_of(compact))
        content = v.identity(compact, "application/json")
        material = {}
        v.register_material(content, compact, material)
        self.reject(lambda: v.check_artifact(reference, "pack", material), "missing retained material")
        reference["content"] = content
        v.check_artifact(reference, "pack", material)

    def test_non_ascii_key_order_and_escaping_keep_raw_and_canon_vectors_separate(self):
        raw = b'{ "\\u00e9": "line\\n", "a": "\\u00e9", "\\ud83d\\ude00": "slash/" }\n'
        expected = '{"a":"é","é":"line\\n","😀":"slash/"}'.encode("utf-8")
        canonical = v.spec_canon.canon(v.read_json(raw))
        self.assertEqual(canonical, expected)
        self.assertNotEqual(v.identity(raw, "application/json"), v.identity(expected, "application/json"))
        self.assertEqual(v.canonical_identity(raw), v.canonical_identity(expected))

    def test_canonical_identity_optional_but_checked_when_present(self):
        for reference in (self.adoption["consumer"], self.adoption["governingPolicies"][0]["policy"]):
            del reference["canonicalIdentity"]
        v.check_adoption(self.adoption, self.material)
        reference = self.adoption["consumer"]
        reference["canonicalIdentity"] = {"profile": "jps-canon", "canonicalDigest": "sha256:" + "0" * 64}
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "canonical identity mismatch")
        reference["canonicalIdentity"]["profile"] = "jcs"
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "schema")

    def test_core_valid_optional_numeric_extension_needs_no_canon_identity(self):
        # Core §§2.1 and 9 permit RFC8259 numbers in optional arbitrary JSON values.
        reference = self.adoption["consumer"]
        original = v.resolve(reference["content"], self.material)
        raw = original.rstrip()[:-1] + b',"extensions":{"com.example.numeric-notes":{"fraction":1.234567890123456789,"exponent":1e2,"large":9007199254740992}}}\n'
        # Independently assert the unchanged Core schema accepts this extension.
        core = json.loads(raw, parse_float=Decimal)
        v.VALIDATORS["core"].validate(core)
        parsed = v.read_core_json(raw)
        numbers = parsed["extensions"]["com.example.numeric-notes"]
        self.assertEqual(numbers["fraction"].literal, "1.234567890123456789")
        self.assertEqual(numbers["exponent"].literal, "1e2")
        self.assertEqual(numbers["large"].literal, "9007199254740992")
        view = v.core_schema_view(parsed)["extensions"]["com.example.numeric-notes"]
        self.assertEqual(view, {"fraction": Decimal("1.234567890123456789"), "exponent": 100, "large": 9007199254740992})
        reference["content"] = v.identity(raw, "application/json")
        v.register_material(reference["content"], raw, self.material)
        del reference["canonicalIdentity"]
        v.check_adoption(self.adoption, self.material)
        self.assertEqual(v.resolve(reference["content"], self.material), raw)
        reference["canonicalIdentity"] = {"profile": "jps-canon", "canonicalDigest": "sha256:" + "0" * 64}
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "unsupported requested jps-canon identity")

    def test_consumer_numeric_limits_are_explicit_prototype_bounds(self):
        for raw in (b'{"value":1e309}', b'{"value":' + b"1" * 129 + b"}"):
            self.reject(lambda: v.read_core_json(raw), "unsupported prototype consumer bound")
        self.reject(lambda: v.read_core_json(b'{"value":1,"value":2}'), "invalid consumer JSON")

    def test_coverage_must_cover_exact_declared_scope_once(self):
        governing = self.adoption["governingPolicies"][0]
        removed = governing["coverage"].pop()
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "omits an in-scope section")
        governing["coverage"].append(removed)
        duplicate = {"sectionId": "eligibility", "status": "manual", "handoff": "Fictional manual process"}
        governing["coverage"].append(duplicate)
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "duplicate section coverage")
        governing["coverage"].pop()
        governing["scope"] = {"kind": "sections", "sectionIds": ["eligibility"], "reviewBasis": governing["coverage"][0]["reviewBasis"]}
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "coverage outside declared scope")
        governing["scope"]["sectionIds"] = ["missing"]
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "unknown section")

    def test_coverage_variant_requires_explanation_and_no_wrong_fields(self):
        for record in ({"sectionId": "eligibility", "status": "implemented", "consumerElements": []}, {"sectionId": "eligibility", "status": "manual"}, {"sectionId": "eligibility", "status": "out-of-scope"}, {"sectionId": "eligibility", "status": "awaiting-implementation"}, {"sectionId": "eligibility", "status": "awaiting-interpretation"}, {"sectionId": "eligibility", "status": "manual", "handoff": "Fictional queue", "consumerElements": [{"kind": "rule", "id": "eligible"}]}):
            changed = copy.deepcopy(self.adoption)
            changed["governingPolicies"][0]["coverage"][0] = record
            self.reject(lambda: v.check_schema("governing-adoption", changed), "schema")

    def test_review_basis_must_be_retained_not_an_approval_claim(self):
        self.adoption["governingPolicies"][0]["coverage"][0]["reviewBasis"]["bytesDigest"] = "sha256:" + "0" * 64
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "missing retained material")

    def test_informational_source_cannot_replace_governing_dependency(self):
        self.adoption["informationalSources"] = [self.policy["content"]]
        v.check_adoption(self.adoption, self.material)
        self.adoption["governingPolicies"] = []
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "schema")

    def test_pack_only_first_slice_refuses_graphs(self):
        self.adoption["consumer"]["kind"] = "graph"
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "schema")

    def test_multiple_policy_references_with_independent_identities(self):
        other = copy.deepcopy(self.policy)
        other["id"] = "urn:example:synthetic-second-policy"
        content = self.retain(other)
        governing = copy.deepcopy(self.adoption["governingPolicies"][0])
        governing["policy"] = {"kind": "policy", "id": other["id"], "version": other["version"], "content": content}
        self.adoption["governingPolicies"].append(governing)
        v.check_adoption(self.adoption, self.material)
        duplicate = copy.deepcopy(governing)
        duplicate["scope"] = {"kind": "sections", "sectionIds": ["eligibility"], "reviewBasis": governing["coverage"][0]["reviewBasis"]}
        duplicate["coverage"] = duplicate["coverage"][:1]
        self.adoption["governingPolicies"].append(duplicate)
        self.reject(lambda: v.check_adoption(self.adoption, self.material), "duplicate governing policy")


if __name__ == "__main__":
    unittest.main()

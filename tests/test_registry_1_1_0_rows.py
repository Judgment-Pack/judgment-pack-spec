"""The rows and schemas of registry format 1.1.0, proposed (conformance/registry/1.1.0/, schema/registry/1.1.0/).

They are staged with spec/registry-1.1.0.md, which governs where they differ. These tests hold them to
the parts of the text that need no reader: every schema is a JSON Schema 2020-12 schema under its
`$id`; every row document is admitted or refused by the schema its selector names, as its row says;
codes.json is the text's section 12, and the rows use every code of it and no code of neither format;
every class of section 15 has rows; every digest, content digest, resolved digest, statement and
serial follows from the inputs; every document a reader writes is its JCS bytes; every signature that
should verify does, and every key is a published RFC 8032 key; every report is in order; and every
verifier's record after a row follows from section 11's Rollback rule. They never assemble, check or
verify: that is a reader's work.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import unittest
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from test_registry_companion import jcs, load, lookup, resolve, tokens

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "conformance" / "registry" / "1.1.0"
OLD = ROOT / "conformance" / "registry" / "1.0.0"
SCHEMAS = ROOT / "schema" / "registry" / "1.1.0"
OLD_SCHEMAS = ROOT / "schema" / "registry" / "1.0.0"
SPEC = ROOT / "spec" / "registry-1.1.0.md"
NAMESPACE = "https://judgmentpack.org/schema/registry/1.1.0/"
OLD_NAMESPACE = "https://judgmentpack.org/schema/registry/1.0.0/"
MANIFEST = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
CODES_DOCUMENT = json.loads((BASE / "codes.json").read_text(encoding="utf-8"))
CODES = {item["code"]: item for item in CODES_DOCUMENT["codes"]}
OLD_CODES = {item["code"]: item for item in json.loads((OLD / "codes.json").read_text(encoding="utf-8"))["codes"]}
STAGED = ("Staged and proposed with spec/registry-1.1.0.md, which governs where they differ; not released, "
          "and served by no bundle and no site. ")

# Section 2: each document's selector, the value it takes, and the schema that holds it.
SELECTORS = {
    ("federationFormatVersion", "1.1.0"): NAMESPACE + "federation-manifest.schema.json",
    ("indexFormatVersion", "1.1.0"): NAMESPACE + "assembled-index.schema.json",
    ("boundsFormatVersion", "1.1.0"): NAMESPACE + "bounds.schema.json",
    ("lockFormatVersion", "1.1.0"): NAMESPACE + "lock.schema.json",
    ("lockSignatureVersion", "1.1.0"): NAMESPACE + "lock-signature.schema.json",
    ("sourceSignatureVersion", "1.1.0"): NAMESPACE + "source-signature.schema.json",
    ("reportFormatVersion", "1.1.0"): NAMESPACE + "validation-report.schema.json",
    ("registryFormatVersion", "1.0.0"): OLD_NAMESPACE + "registry.schema.json",
    ("kindFormatVersion", "1.0.0"): OLD_NAMESPACE + "kind-declaration.schema.json",
    ("resolvedFormatVersion", "1.0.0"): OLD_NAMESPACE + "resolved-registry.schema.json",
    ("emitterManifestVersion", "1.0.0"): OLD_NAMESPACE + "emitter-manifest.schema.json",
}
SELECTOR_NAMES = {name for name, _ in SELECTORS}
# Section 15's classes, and the operations of the rows that bind each.
CLASSES = {"assemble": "assembler", "check-index": "index-checker", "write-lock": "lock-writer",
           "check-lock": "lock-checker", "coverage": "lock-checker", "verify": "lock-signature-verifier"}
# RFC 8032 section 7.1's published public keys of TEST 1, TEST 2 and TEST 3: the only keys a row signs with.
RFC8032_KEYS = {
    "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
    "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
    "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025",
}
# RFC 8032 section 7.1's seeds. No row file may hold one: only the generator signs.
RFC8032_SEEDS = {
    "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
    "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
    "c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
}
SMALL_ORDER_KEY = "01" + "00" * 31
PREFIX = {"lock": b"judgment-pack-registry/lock-signature/1:", "source": b"judgment-pack-registry/source-signature/1:"}
ORDER = ("document", "source", "keyId", "kindDocument", "kind", "entry.kind", "entry.id", "environment", "pointer",
         "line", "column")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
MESSAGE = "A fixed text."
SERIAL_CODES = {"LOCK-SERIAL-ROLLBACK", "LOCK-SERIAL-CONFLICT", "LOCK-SERIAL-STATE"}

_SPEC = importlib.util.spec_from_file_location("dialect_verify", ROOT / "tools" / "dialect_verify.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("could not load the Ed25519 arithmetic")
ED25519 = importlib.util.module_from_spec(_SPEC)
sys.modules.setdefault(_SPEC.name, ED25519)
_SPEC.loader.exec_module(ED25519)

SCHEMA_DOCUMENTS = {path.name: json.loads(path.read_text(encoding="utf-8")) for path in sorted(SCHEMAS.glob("*.json"))}
OLD_SCHEMA_DOCUMENTS = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(OLD_SCHEMAS.glob("*.json"))]
REGISTRY = Registry().with_resources(
    (schema["$id"], Resource.from_contents(schema))
    for schema in (*SCHEMA_DOCUMENTS.values(), *OLD_SCHEMA_DOCUMENTS))


def validator(identity: str) -> Draft202012Validator:
    return Draft202012Validator({"$ref": identity}, registry=REGISTRY)


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def digest(document) -> str:
    return sha(jcs(document).encode("utf-8"))


def text_of(relative: str) -> bytes:
    return (BASE / relative).read_bytes()


def document(relative: str):
    return load(BASE / relative)


def given_key_ids(row: dict) -> set[str]:
    """The key identifiers (section 11) of the signature documents a row gives that hold a key of its form."""
    found = set()
    for relative in row.get("lockSignatures", []) + row.get("sourceSignatures", []):
        try:
            key = json.loads(text_of(relative)).get("publicKey")
        except ValueError:
            continue
        if isinstance(key, str) and re.fullmatch(r"[0-9a-f]{64}", key):
            found.add(hashlib.sha256(bytes.fromhex(key)).hexdigest()[:32])
    return found


def tree() -> set[str]:
    return {path.relative_to(BASE).as_posix() for path in BASE.rglob("*") if path.is_file()} - {
        "README.md", "codes.json", "manifest.json"}


def selector(value):
    if not isinstance(value, dict):
        return None
    found = [(name, value[name]) for name in SELECTOR_NAMES if name in value]
    return found[0] if len(found) == 1 else None


def named(row) -> list[str]:
    """Every file a row names, by the members the row forms of the README give."""
    names = [row["expected"]]
    for member in ("federation", "index", "lock", "registry", "previous", "resolved"):
        if member in row:
            names.append(row[member])
    for member in ("kinds", "lockSignatures", "sourceSignatures"):
        names.extend(row.get(member, []))
    if "known" in row:
        names.extend(row["known"]["indexes"] + row["known"]["locks"])
    for given in row.get("sources", {}).values():
        names.extend(given["files"].values())
    for emitter in row.get("emitters", []):
        names.append(emitter["manifest"])
        names.extend(item["file"] for item in emitter["files"])
    if "file" in row:
        names.append(row["file"]["file"])
    names.extend(row.get("writes", {}).values())
    return names


def report_codes(row) -> list[str]:
    expected = document(row["expected"])
    if "refused" in expected:
        return expected["refused"]
    if "diagnostics" in expected:
        return [d["code"] for d in expected["diagnostics"]]
    return []


def sort_key(diagnostic):
    location = diagnostic["location"]
    entry = location.get("entry", {})
    values = {"entry.kind": entry.get("kind", ""), "entry.id": entry.get("id", "")}
    return tuple(values[name] if name in values else location.get(name, 0 if name in ("line", "column") else "")
                 for name in ORDER) + (diagnostic["code"],)


def statement(item) -> dict:
    return {"repository": item["repository"], "commit": item["commit"], "documents": item["documents"]}


def lock_digest(data: bytes) -> str:
    return sha(data[:-1] if data.endswith(b"\n") else data)


def well_formed_record(record) -> bool:
    return (isinstance(record, dict) and set(record) == {"serial", "digest"} and type(record["serial"]) is int
            and 1 <= record["serial"] <= 2**53 - 1 and isinstance(record["digest"], str)
            and DIGEST.fullmatch(record["digest"]) is not None)


def rollback(serial: int, lock: str, record, floor):
    """Section 11, Rollback: the refusal of a lock of this serial and digest, or None when it is admitted."""
    if record is not None and not well_formed_record(record):
        return "LOCK-SERIAL-STATE"
    if record is None:
        if floor is None:
            return "LOCK-EXPECTED"
        return "LOCK-SERIAL-ROLLBACK" if serial < floor else None
    if floor is not None and floor > record["serial"]:
        return "LOCK-SERIAL-ROLLBACK" if serial < floor else None
    if serial < record["serial"]:
        return "LOCK-SERIAL-ROLLBACK"
    if serial == record["serial"] and lock != record["digest"]:
        return "LOCK-SERIAL-CONFLICT"
    return None


def verification_record(row, serial: int, lock: str):
    """The serial step and the write of section 11, for a row whose other steps all accept: (refusal, record)."""
    record, floor = row["record"], row.get("floor")
    refusal = rollback(serial, lock, record, floor)
    if refusal is None and "concurrent" in row:
        record = row["concurrent"]
        refusal = rollback(serial, lock, record, floor)
    if refusal is not None:
        return refusal, record
    new = {"serial": serial, "digest": lock}
    if record == new:
        return None, record
    if row.get("writeFails"):
        return "LOCK-SERIAL-STATE", record
    return None, new


def section_12() -> list[tuple[str, str, str]]:
    rows = []
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"\| `((?:FED|LOCK)-[A-Z-]+)` \| (.+) \| (§[^|]+?) \|", line)
        if match:
            rows.append(match.groups())
    return rows


def all_registries() -> dict[str, dict]:
    found = {}
    for relative in tree():
        if relative.endswith(".json"):
            value = load(BASE / relative)
            if selector(value) == ("registryFormatVersion", "1.0.0"):
                found[digest(value)] = value
    return found


def all_indexes() -> dict[str, dict]:
    found = {}
    for relative in tree():
        if relative.endswith(".json"):
            value = load(BASE / relative)
            if selector(value) == ("indexFormatVersion", "1.1.0"):
                found[digest(value)] = value
    return found


def source_of(row, name: str) -> dict:
    return next(item for item in document(row["federation"])["sources"] if item["name"] == name)


class Schemas(unittest.TestCase):
    def test_every_schema_is_a_draft_2020_12_schema_under_its_id(self) -> None:
        self.assertEqual({"assembled-index", "bounds", "common", "federation-manifest", "lock", "lock-signature",
                          "source-signature", "source-statement", "validation-report"},
                         {name[: -len(".schema.json")] for name in SCHEMA_DOCUMENTS})
        for name, schema in SCHEMA_DOCUMENTS.items():
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(schema)
                self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
                self.assertEqual(NAMESPACE + name, schema["$id"])
                self.assertTrue(schema["title"].startswith("DRAFT Registry companion 1.1.0: "))
                self.assertTrue(schema["description"].startswith(STAGED))

    def test_schemas_close_every_object_they_define(self) -> None:
        def walk(node, where):
            if isinstance(node, dict):
                if node.get("type") == "object" and "properties" in node:
                    self.assertIn("additionalProperties", node, where)
                    self.assertIsNot(node["additionalProperties"], True, where)
                for key, value in node.items():
                    walk(value, where + "/" + key)
            elif isinstance(node, list):
                for position, value in enumerate(node):
                    walk(value, where + "/" + str(position))
        for name, schema in SCHEMA_DOCUMENTS.items():
            walk(schema, name)

    def test_the_report_schema_lists_exactly_the_codes_of_both_formats(self) -> None:
        common = SCHEMA_DOCUMENTS["common.schema.json"]["$defs"]
        self.assertEqual(sorted(CODES), sorted(common["newCode"]["enum"]))

    def test_the_report_schema_holds_key_id_to_a_signature_documents_diagnostic(self) -> None:
        reports = validator(NAMESPACE + "validation-report.schema.json")

        def errors(location: dict) -> list[str]:
            diagnostic = {"code": "LOCK-SIG-EXTRA", "severity": "error", "message": MESSAGE, "location": location}
            value = {"reportFormatVersion": "1.1.0", "valid": False, "diagnostics": [diagnostic]}
            return [error.message for error in reports.iter_errors(value)]
        key = hashlib.sha256(bytes.fromhex(sorted(RFC8032_KEYS)[0])).hexdigest()[:32]
        self.assertEqual([], errors({"document": "signature", "keyId": key, "pointer": ""}))
        for location in ({"document": "lock", "keyId": key, "pointer": ""},
                         {"document": "signature", "keyId": key[:31], "pointer": ""},
                         {"document": "signature", "keyId": key.upper(), "pointer": ""}):
            with self.subTest(location=location):
                self.assertTrue(errors(location))

    def test_row_documents_are_admitted_or_refused_as_their_rows_say(self) -> None:
        refused = {path for row in MANIFEST["vectors"] for path in row.get("schemaRefuses", [])}
        for relative in sorted(refused):
            self.assertIn(relative, tree())
        checked = 0
        for relative in sorted(tree()):
            if not relative.endswith(".json"):
                continue
            with self.subTest(file=relative):
                value = load(BASE / relative)
                if "refused" in value:
                    self.assertEqual({"refused"}, set(value))
                    continue
                found = selector(value)
                self.assertIsNotNone(found)
                schema = next(identity for (name, _), identity in SELECTORS.items() if name == found[0])
                plain = json.loads(json.dumps(value, default=float))
                if found[0] == "reportFormatVersion":
                    for diagnostic in plain["diagnostics"]:
                        diagnostic["message"] = MESSAGE
                errors = list(validator(schema).iter_errors(plain))
                if relative in refused:
                    self.assertTrue(errors, "the row says the schema refuses it")
                else:
                    self.assertEqual([], [error.message for error in errors])
                checked += 1
        self.assertGreater(checked, 300)

    def test_every_source_statement_meets_its_schema(self) -> None:
        statements = validator(NAMESPACE + "source-statement.schema.json")
        for identity, index in all_indexes().items():
            for item in index["sources"]:
                with self.subTest(index=identity, source=item["name"]):
                    self.assertEqual([], [e.message for e in statements.iter_errors(statement(item))])


class Codes(unittest.TestCase):
    def test_codes_json_is_the_section_12_table(self) -> None:
        table = section_12()
        self.assertEqual(22, sum(code.startswith("FED-") for code, _, _ in table))
        self.assertEqual(31, sum(code.startswith("LOCK-") for code, _, _ in table))
        self.assertEqual(53, len({code for code, _, _ in table}))
        self.assertEqual([code for code, _, _ in table], [item["code"] for item in CODES_DOCUMENT["codes"]])
        for code, raised, section in table:
            with self.subTest(code=code):
                self.assertEqual({"code", "severity", "status", "section", "meaning"}, set(CODES[code]))
                self.assertEqual("error", CODES[code]["severity"])
                self.assertEqual("active", CODES[code]["status"])
                self.assertEqual(section, CODES[code]["section"])
                self.assertEqual(raised.replace("`", ""), CODES[code]["meaning"])
        self.assertFalse(set(CODES) & set(OLD_CODES))

    def test_the_text_codes_json_and_the_manifest_say_one_status(self) -> None:
        self.assertIn("This text is registry format `1.1.0`, status `proposed`.", SPEC.read_text(encoding="utf-8"))
        for value in (CODES_DOCUMENT, MANIFEST):
            self.assertEqual(("registry", "1.1.0", "proposed"),
                             (value["companion"], value["formatVersion"], value["status"]))

    def test_every_code_is_used_and_every_used_code_is_listed(self) -> None:
        used = {code for row in MANIFEST["vectors"] for code in report_codes(row)}
        self.assertEqual(set(), set(CODES) - used)
        self.assertEqual(set(), used - set(CODES) - set(OLD_CODES))


class Manifest(unittest.TestCase):
    def test_the_manifest_has_the_form_of_format_1_0_0(self) -> None:
        self.assertEqual(["companion", "formatVersion", "status", "label", "codes", "vectors"], list(MANIFEST))
        self.assertEqual("codes.json", MANIFEST["codes"])
        identities = [row["id"] for row in MANIFEST["vectors"]]
        self.assertEqual(len(identities), len(set(identities)))
        for row in MANIFEST["vectors"]:
            with self.subTest(row=row["id"]):
                self.assertRegex(row["id"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
                self.assertEqual(["id", "section", "operation", "class", "description"], list(row)[:5])
                self.assertRegex(row["section"], r"^(§[0-9]+(\.[0-9]+)?|§§[0-9]+(\.[0-9]+)?(, [0-9]+(\.[0-9]+)?)+)$")
                self.assertEqual(CLASSES[row["operation"]], row["class"])
                self.assertIn("expected", row)

    def test_every_class_of_section_15_has_rows(self) -> None:
        counts = {}
        for row in MANIFEST["vectors"]:
            counts[row["class"]] = counts.get(row["class"], 0) + 1
        self.assertEqual({"assembler", "index-checker", "lock-writer", "lock-checker", "lock-signature-verifier"},
                         set(counts))
        self.assertEqual(set(CLASSES), {row["operation"] for row in MANIFEST["vectors"]})

    def test_the_manifest_names_every_file_and_only_files(self) -> None:
        files = tree()
        seen = set()
        for row in MANIFEST["vectors"]:
            for relative in named(row):
                with self.subTest(row=row["id"], file=relative):
                    self.assertIn(relative, files)
                    seen.add(relative)
        self.assertEqual(set(), files - seen)

    def test_inputs_are_synthetic_and_hold_no_seed(self) -> None:
        for relative in tree():
            data = text_of(relative).decode("utf-8")
            with self.subTest(file=relative):
                for seed in RFC8032_SEEDS:
                    self.assertNotIn(seed, data)
                for host in re.findall(r"https?://([^/\"\s]+)", data):
                    self.assertTrue(host == "example.invalid" or host.endswith("@example.invalid"), host)


class Derived(unittest.TestCase):
    def test_written_documents_are_their_jcs_bytes(self) -> None:
        for relative in tree():
            written = relative.startswith(("assembled/", "single/resolved-")) or (
                relative.startswith("locks/") and relative.endswith(".lock.json"))
            if written:
                with self.subTest(file=relative):
                    self.assertEqual(jcs(document(relative)).encode("utf-8"), text_of(relative))
        for row in MANIFEST["vectors"]:
            if row["operation"] == "write-lock" and "refused" not in document(row["expected"]):
                self.assertEqual(jcs(document(row["expected"])).encode("utf-8"), text_of(row["expected"]))

    def test_every_pin_is_the_digest_of_a_declaration_here(self) -> None:
        declarations = {}
        for relative in tree():
            if relative.startswith("kinds/"):
                value = document(relative)
                declarations[digest(value)] = value
        for identity, registry in all_registries().items():
            for pin in registry["kinds"]:
                with self.subTest(registry=identity, kind=pin["kind"]):
                    self.assertIn(pin["digest"], declarations)
                    declaration = declarations[pin["digest"]]
                    self.assertEqual((pin["kind"], pin["id"], pin["version"]),
                                     (declaration["kind"], declaration["id"], declaration["version"]))

    def test_single_registry_is_format_1_0_0s_and_its_resolved_forms_follow(self) -> None:
        old = OLD / "vectors" / "valid-two-environments"
        self.assertEqual((old / "registry.json").read_bytes(), text_of("single/registry.json"))
        for environment in ("dev", "prod"):
            self.assertEqual((old / f"resolved-{environment}.json").read_bytes(),
                             text_of(f"single/resolved-{environment}.json"))

    def test_accepted_assemblies_write_what_the_inputs_give(self) -> None:
        for row in MANIFEST["vectors"]:
            if "writes" not in row:
                continue
            with self.subTest(row=row["id"]):
                self.assertTrue(document(row["expected"])["valid"])
                manifest = document(row["federation"])
                registry = document(row["writes"]["registry"])
                index = document(row["writes"]["index"])
                self.assertEqual({"digest": digest(registry)}, document(row["expected"])["registry"])
                self.assertEqual(manifest["registry"], {"id": registry["id"], "version": registry["version"]})
                self.assertEqual(manifest["environments"], registry["environments"])
                self.assertEqual({"digest": digest(manifest)}, index["federation"])
                self.assertEqual({"id": registry["id"], "version": registry["version"], "digest": digest(registry)},
                                 index["registry"])
                self.assertEqual([s["name"] for s in manifest["sources"]], [s["name"] for s in index["sources"]])
                owners, entries, pins = set(), [], {}
                for source, item in zip(manifest["sources"], index["sources"]):
                    given = row["sources"][source["name"]]
                    roles = {source.get("registry"): "registry", source.get("bounds"): "bounds",
                             **{path: "kind" for path in source.get("kinds", [])}}
                    roles.pop(None, None)
                    self.assertEqual((source["role"], source["repository"], given["commit"]),
                                     (item["role"], item["repository"], item["commit"]))
                    self.assertEqual(sorted(roles), [d["path"] for d in item["documents"]])
                    self.assertEqual(sorted(roles), sorted(given["files"]))
                    for entry in item["documents"]:
                        data = text_of(given["files"][entry["path"]])
                        self.assertEqual(roles[entry["path"]], entry["role"])
                        self.assertEqual(sha(data), entry["contentDigest"])
                        self.assertEqual(digest(load(BASE / given["files"][entry["path"]])), entry["digest"])
                    if "registry" in source:
                        own = document(given["files"][source["registry"]])
                        owners.update(own["owners"])
                        served = source.get("environments", manifest["environments"])
                        self.assertEqual(served, own["environments"])
                        for entry in own["entries"]:
                            written = dict(entry)
                            if served != manifest["environments"] and "environments" not in entry:
                                written["environments"] = served
                            entries.append(written)
                        for pin in own["kinds"]:
                            pins.setdefault(pin["kind"], pin)
                self.assertEqual(sorted(owners), registry["owners"])
                key = lambda entry: (entry["kind"], entry["id"])
                self.assertEqual(sorted(entries, key=key), registry["entries"])
                self.assertEqual([pins[name] for name in sorted(pins)], registry["kinds"])

    def test_locks_name_what_they_lock(self) -> None:
        registries, indexes = all_registries(), all_indexes()
        signatures = {sha(text_of(r)[:-1]): r for r in tree() if r.startswith("signatures/")}
        for relative in sorted(tree()):
            if not relative.endswith(".lock.json") or not relative.startswith("locks/"):
                continue
            with self.subTest(lock=relative):
                lock = document(relative)
                registry = registries[lock["registry"]["digest"]]
                self.assertEqual((registry["id"], registry["version"]), (lock["registry"]["id"], lock["registry"]["version"]))
                self.assertEqual(registry["kinds"], lock["kinds"])
                resolved = []
                for environment in registry["environments"]:
                    resolved_document = {"entries": resolve(registry, environment), "environment": environment,
                                         "kinds": registry["kinds"],
                                         "registry": {"digest": digest(registry), "id": registry["id"],
                                                      "version": registry["version"]},
                                         "resolvedFormatVersion": "1.0.0"}
                    resolved.append({"environment": environment, "digest": digest(resolved_document)})
                self.assertEqual(resolved, lock["resolved"])
                self.assertEqual("index" in lock, "sources" in lock)
                if "index" in lock:
                    index = indexes[lock["index"]["digest"]]
                    self.assertEqual(lock["registry"]["digest"], index["registry"]["digest"])
                    for item, source in zip(index["sources"], lock["sources"], strict=True):
                        self.assertEqual((item["name"], item["role"], item["repository"]),
                                         (source["name"], source["role"], source["repository"]))
                        self.assertEqual(digest(statement(item)), source["statement"])
                        self.assertIn(source["signature"], signatures)
                self.assertEqual(sorted(lock.get("emitters", []), key=lambda e: (e.get("source", ""), e["path"])),
                                 lock.get("emitters", []))
                for emitter in lock.get("emitters", []):
                    self.assertEqual("index" in lock, "source" in emitter)
                    if "source" in emitter:
                        self.assertIn(emitter["source"], [source["name"] for source in lock["sources"]])
                    self.assertEqual(digest(document(emitter["path"])), emitter["digest"])
                    self.assertEqual(sorted(f["path"] for f in emitter["files"]), [f["path"] for f in emitter["files"]])
                    for item in emitter["files"]:
                        self.assertEqual(sha(text_of("emitters/" + item["path"])), item["digest"])

    def test_writers_write_the_next_serial(self) -> None:
        for row in MANIFEST["vectors"]:
            if row["operation"] != "write-lock" or "refused" in document(row["expected"]):
                continue
            with self.subTest(row=row["id"]):
                lock = document(row["expected"])
                self.assertEqual("previous" in row, "firstSerial" not in row)
                serial = document(row["previous"])["serial"] + 1 if "previous" in row else row["firstSerial"]
                self.assertEqual(serial, lock["serial"])
                if "registry" in row:
                    self.assertEqual(digest(document(row["registry"])), lock["registry"]["digest"])
                    self.assertNotIn("index", lock)
                else:
                    given = [sha(text_of(path)[:-1]) for path in row["sourceSignatures"]]
                    self.assertEqual(sorted(given), sorted(source["signature"] for source in lock["sources"]))
                emitters = [{**({"source": e["source"]} if "source" in e else {}), "path": e["path"],
                             "digest": digest(document(e["manifest"])),
                             "files": [{"path": f["path"], "mode": f["mode"], "digest": sha(text_of(f["file"]))}
                                       for f in sorted(e["files"], key=lambda f: f["path"])]}
                            for e in sorted(row.get("emitters", []), key=lambda e: (e.get("source", ""), e["path"]))]
                self.assertEqual(emitters, lock.get("emitters", []))

    def test_signatures_are_by_published_keys_and_verify(self) -> None:
        invalid = {path for row in MANIFEST["vectors"] if "LOCK-SIG-INVALID" in report_codes(row)
                   for path in row.get("lockSignatures", []) + row.get("sourceSignatures", [])}
        refused = {path for row in MANIFEST["vectors"] for path in row.get("schemaRefuses", [])}
        checked = 0
        for relative in sorted(tree()):
            if not relative.endswith(".json"):
                continue
            value = document(relative)
            found = selector(value)
            if found not in {("lockSignatureVersion", "1.1.0"), ("sourceSignatureVersion", "1.1.0")}:
                continue
            with self.subTest(signature=relative):
                key = value.get("publicKey", "")
                self.assertTrue(key in RFC8032_KEYS or key.lower() in RFC8032_KEYS or key == SMALL_ORDER_KEY, key)
                if relative in refused or key not in RFC8032_KEYS:
                    continue
                kind = "lock" if found[0] == "lockSignatureVersion" else "source"
                member = "lockDigest" if kind == "lock" else "sourceDigest"
                message = PREFIX[kind] + jcs({member: value[member], found[0]: "1.1.0"}).encode("ascii")
                verifies = ED25519.signature_verifies(bytes.fromhex(key), message, bytes.fromhex(value["signature"]))
                self.assertEqual(relative not in invalid, verifies)
                if relative.startswith("locks/"):
                    self.assertEqual(lock_digest(text_of(relative[: -len(".sig.json")])), value["lockDigest"])
                if relative.startswith(("locks/", "signatures/")):
                    data = text_of(relative)
                    self.assertEqual(jcs(value).encode("ascii") + b"\n", data)
                checked += 1
        self.assertGreater(checked, 10)
        for row in MANIFEST["vectors"]:
            signers = row.get("signers", {})
            for key in [signers.get("key")] + list(signers.get("repositories", {}).values()):
                if key is not None:
                    self.assertTrue(key in RFC8032_KEYS or key == SMALL_ORDER_KEY, key)

    def test_reports_follow_section_2_1(self) -> None:
        for row in MANIFEST["vectors"]:
            value = document(row["expected"])
            if "diagnostics" not in value:
                continue
            with self.subTest(row=row["id"]):
                diagnostics = value["diagnostics"]
                self.assertEqual(sorted(diagnostics, key=sort_key), diagnostics)
                self.assertEqual(len(diagnostics), len({json.dumps(d, sort_keys=True) for d in diagnostics}))
                self.assertEqual(value["valid"], not any(d["severity"] == "error" for d in diagnostics))
                for diagnostic in diagnostics:
                    code, location = diagnostic["code"], diagnostic["location"]
                    self.assertNotIn("message", diagnostic)
                    self.assertEqual((CODES.get(code) or OLD_CODES[code])["severity"], diagnostic["severity"])
                    if location["document"] in ("federation", "lock", "signature"):
                        self.assertNotIn("source", location)
                    if "source" in location:
                        self.assertIn(location["source"], {s["name"] for s in document(row["federation"])["sources"]})
                    if "keyId" in location:
                        # Section 2.1: on a signature document's diagnostic alone, the identifier of a given
                        # document's key (section 11).
                        self.assertEqual("signature", location["document"])
                        self.assertIn(location["keyId"], given_key_ids(row))

    def test_diagnostic_pointers_address_their_documents(self) -> None:
        absent = {("LOCK-INDEX-REQUIRED", "/index"), ("LOCK-SIG-MEMBER", "/signature")}
        for row in MANIFEST["vectors"]:
            value = document(row["expected"])
            for diagnostic in value.get("diagnostics", []):
                location = diagnostic["location"]
                name, source = location["document"], location.get("source")
                if name == "federation":
                    target = row["federation"]
                elif name in ("registry", "bounds") and source is not None:
                    given = row["sources"][source]["files"]
                    target = given[source_of(row, source)[name]]
                elif name == "registry":
                    target = row["registry"]
                elif name in ("lock", "index"):
                    target = row[name]
                elif name == "signature" and len(row.get("lockSignatures", [])) == 1 and not row["sourceSignatures"]:
                    target = row["lockSignatures"][0]
                else:
                    continue
                with self.subTest(row=row["id"], code=diagnostic["code"]):
                    _, found = lookup(load(BASE / target), tokens(location["pointer"]))
                    self.assertEqual((diagnostic["code"], location["pointer"]) not in absent, found)

    def test_records_follow_the_rollback_rule(self) -> None:
        modelled = 0
        for row in MANIFEST["vectors"]:
            if row["operation"] != "verify":
                continue
            with self.subTest(row=row["id"]):
                value = document(row["expected"])
                codes = set(report_codes(row))
                data = text_of(row["lock"])
                lock = document(row["lock"])
                after = row.get("concurrent", row["record"])
                if value["valid"]:
                    self.assertEqual({"serial": lock["serial"], "digest": lock_digest(data)}, row["expectedRecord"])
                else:
                    self.assertEqual(after, row["expectedRecord"])
                first_contact = codes == {"LOCK-EXPECTED"} and row["record"] is None and "floor" not in row
                if value["valid"] or (codes and codes <= SERIAL_CODES) or first_contact:
                    refusal, record = verification_record(row, lock["serial"], lock_digest(data))
                    self.assertEqual(set() if refusal is None else {refusal}, codes)
                    self.assertEqual(record, row["expectedRecord"])
                    modelled += 1
        self.assertGreaterEqual(modelled, 19)


if __name__ == "__main__":
    unittest.main()

"""The schemas of the registry companion's documents (schema/registry/1.0.0/).

They are proposed with spec/registry.md, which governs where they differ. These tests hold them to
the text and to the rows: each is a JSON Schema 2020-12 schema under its `$id`; every row
document a reader admits, or writes, validates against the schema its selector names; the code list
the reports use is codes.json's, and every other enum, and each range form, is the text's list;
each schema refuses another selector and a missing required member, and every object a schema
closes refuses an unlisted member; the forms the text states are refused when broken; and no schema
refuses a member that a row's expected refusals admit.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schema" / "registry" / "1.0.0"
BASE = ROOT / "conformance" / "registry" / "1.0.0"
SPEC = ROOT / "spec" / "registry.md"
NAMESPACE = "https://judgmentpack.org/schema/registry/1.0.0/"
MANIFEST = json.loads((BASE / "manifest.json").read_text(encoding="utf-8"))
CODES = json.loads((BASE / "codes.json").read_text(encoding="utf-8"))["codes"]

# spec/registry.md section 2.1: each document's selector, and the schema that holds it.
SELECTORS = {
    "kindFormatVersion": "kind-declaration",
    "registryFormatVersion": "registry",
    "resolvedFormatVersion": "resolved-registry",
    "reportFormatVersion": "validation-report",
    "factsContractVersion": "facts-contract",
    "factsCheckFormatVersion": "pack-check-report",
    "emitterManifestVersion": "emitter-manifest",
    "emitRequestVersion": "emit-request",
    "emitResponseVersion": "emit-response",
    "harnessReportVersion": "harness-report",
}
# Section 11.5 names no member of the harness report but its selector, so its schema is open.
OPEN = {"harness-report"}
# Messages are informative and the rows leave them out (section 7.4); a report's schema requires one.
MESSAGE = "A fixed text."


def load_schemas() -> dict[str, dict]:
    return {path.name[: -len(".schema.json")]: json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(SCHEMAS.glob("*.schema.json"))}


SCHEMA_DOCUMENTS = load_schemas()
REGISTRY = Registry().with_resources(
    (schema["$id"], Resource.from_contents(schema)) for schema in SCHEMA_DOCUMENTS.values()
)


def validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(SCHEMA_DOCUMENTS[name], registry=REGISTRY)


def subschema(name: str, definition: str) -> Draft202012Validator:
    return Draft202012Validator({"$ref": NAMESPACE + name + ".schema.json#/$defs/" + definition},
                                registry=REGISTRY)


def read(relative: str):
    return json.loads((BASE / relative).read_text(encoding="utf-8"))


def selector_of(document) -> str | None:
    if isinstance(document, dict):
        found = [name for name in SELECTORS if name in document]
        if len(found) == 1:
            return found[0]
    return None


def with_messages(document):
    """A report as a reader writes it: the rows remove every message (section 7.4, "Agreement")."""
    document = copy.deepcopy(document)
    if selector_of(document) in ("reportFormatVersion", "factsCheckFormatVersion"):
        for diagnostic in document["diagnostics"]:
            diagnostic.setdefault("message", MESSAGE)
    return document


def kind_digest(relative: str) -> str:
    return "sha256:" + hashlib.sha256((BASE / relative).read_bytes()).hexdigest()


def errors(report) -> list[dict]:
    return [d for d in report["diagnostics"] if d["severity"] == "error"]


def admitted_kinds(row: dict, report: dict) -> list[str]:
    """The declarations of a validate row that steps 1 and 2 found nothing in (sections 2.2, 3, 7.1).

    A refused registry ends validation after step 2 (section 7.1), so a report names every
    declaration that steps 1 and 2 refuse whether or not the registry was admitted.
    """
    refused = [d for d in errors(report) if d["location"]["document"] == "kind"]
    if any("kindDocument" not in d["location"] for d in refused):
        return []
    named = {d["location"]["kindDocument"] for d in refused}
    contents = {kind: read(kind) for kind in row["kinds"]}
    admitted = []
    for kind in row["kinds"]:
        copies = [other for other in row["kinds"] if contents[other] == contents[kind]]
        if not any(kind_digest(other) in named for other in copies):
            admitted.append(kind)
    return admitted


def refused_documents(expected: dict) -> set[str]:
    """The inputs a host's expected refusals name, by the document each refusal code is in."""
    documents = set()
    for refusal in expected["refusals"]:
        documents.add({"EMIT-MANIFEST": "manifest", "EMIT-RESPONSE": "response"}.get(
            refusal["code"], refusal.get("document", "other")))
    return documents


def admitted_row_documents() -> dict[str, set[str]]:
    """Every JSON file of the rows that a row says a reader admits or writes, with the reason."""
    found: dict[str, set[str]] = {}

    def add(relative: str, why: str) -> None:
        found.setdefault(relative, set()).add(why)

    for row in MANIFEST["vectors"]:
        operation, rid = row["operation"], row["id"]
        expected = row.get("expected", "")
        if expected.endswith(".json") and selector_of(read(expected)):
            add(expected, f"{rid}: written")
        if operation == "validate":
            report = read(expected)
            if report["valid"]:
                add(row["registry"], f"{rid}: valid")
            for kind in admitted_kinds(row, report):
                add(kind, f"{rid}: no diagnostic of steps 1 and 2")
        elif operation in ("resolve", "facts", "contract", "request", "references"):
            add(row["registry"], f"{rid}: resolved")
            for kind in row["kinds"]:
                add(kind, f"{rid}: pinned by a resolved registry")
            if "manifest" in row:
                add(row["manifest"], f"{rid}: the host ran it")
            if operation == "references":
                add(row["response"], f"{rid}: a run that did not fail")
        elif operation == "check":
            add(row["contract"], f"{rid}: checked against")
        elif operation in ("manifest", "response"):
            refused = refused_documents(read(expected))
            for member in ("manifest", "request", "response"):
                if member in row and member not in refused:
                    add(row[member], f"{rid}: no refusal in document {member}")
    return found


def pointer(error) -> str:
    path = "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in error.absolute_path)
    if error.validator == "required" and isinstance(error.instance, dict):
        missing = [name for name in error.validator_value if name not in error.instance]
        return path + "/" + missing[0] if missing else path
    return path


def folded(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def backticked(text: str) -> list[str]:
    """The code spans of a passage, each without the quotes of a JSON string."""
    return [token.removeprefix('"').removesuffix('"') for token in re.findall(r"`([^`]+)`", text)]


def walk(value, location=""):
    """Each (location, object) of a schema, the location a JSON Pointer into it."""
    yield location, value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from walk(item, location + "/" + key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk(item, location + "/" + str(index))


def enums() -> dict[tuple[str, str], list]:
    """Every enum of every schema but the code lists, which codes.json holds."""
    found = {}
    for name, schema in SCHEMA_DOCUMENTS.items():
        for location, value in walk(schema):
            if isinstance(value, dict) and isinstance(value.get("enum"), list):
                if (name, location) not in (("common", "/$defs/code"), ("common", "/$defs/warningCode")):
                    found[(name, location)] = value["enum"]
    return found


# Each enum of the schemas, and the passage of spec/registry.md (white space folded) whose code
# spans list its values; the passage is the regular expression's one group.
TEXT_LISTS = {
    ("common", "/$defs/typeName"): r"\| `type` \| a type name, or a non-empty array of distinct type "
                                   r"names, from (.*?) \|",
    ("common", "/$defs/locationDocument"): r"\| `document` \| (.*?) \| always \|",
    ("common", "/$defs/registryDocument"): r"That location uses only \u00a77\.3's registry documents "
                                           r"\((.*?), never the host's",
    ("common", "/$defs/location/dependentSchemas/path/properties/document"):
        r"\| `path` \| [^|]*\| in documents (.*?) only,",
    ("common", "/$defs/diagnostic/properties/severity"): r"from \u00a712's closed list; `severity`, (.*?), "
                                                         r"the code's;",
    ("emit-response", "/$defs/file/properties/mode"): r"and an optional `mode`, (.*?)\. A path",
    ("emit-response", "/$defs/diagnostic/properties/severity"):
        r"An emitter diagnostic has exactly `code`, `severity` \((.*?)\) and `location`",
    ("emitter-manifest", "/properties/input"): r"`input` \(optional, (.*?)\);",
    ("emitter-manifest", "/properties/environments"): r"`environments`, (.*?), required with",
    ("emitter-manifest", "/properties/env/items/not"): r"other than (`PATH`[^;]*?`SOURCE_DATE_EPOCH`);",
    ("facts-contract", "/$defs/factType"): r"- `type`: (.*?); - `present`",
    ("facts-contract", "/$defs/fact/properties/present"): r"- `present`: (.*?); - `items`",
    ("facts-contract", "/$defs/fact/dependentSchemas/values/properties/type"):
        r"distinct values of the type, only on (a `string`, `decimal` or `boolean`, or on an `array`) "
        r"whose `items`",
    ("facts-contract", "/$defs/fact/dependentSchemas/values/then/properties/items"):
        r"distinct values of the type, only on a (`string`, `decimal` or `boolean`), or on an",
}

SAMPLES = {
    "kind-declaration": "kinds/db-role.json",
    "registry": "vectors/valid-two-environments/registry.json",
    "resolved-registry": "vectors/valid-two-environments/resolved-prod.json",
    "validation-report": "vectors/bounds-and-warnings/report.json",
    "facts-contract": "vectors/facts-contracts/contract-service.json",
    "pack-check-report": "vectors/facts-contracts/check-service.json",
    "emitter-manifest": "vectors/emitter-host/emitter.json",
    "emit-request": "vectors/emitter-host/request.json",
    "emit-response": "vectors/emitter-harness/response-references.json",
}
WARNING = {"code": "x-a", "severity": "warning", "location": {"document": "registry", "pointer": ""}}

# Each closed object of the schemas: the schema whose sample holds one, the changes that make the
# sample hold one when it does not, and the path to it. The location is where the object is closed.
CLOSED = {
    ("common", "/$defs/schemaKeywords/properties/propertyNames"):
        ("kind-declaration", {"schema": {"type": "object", "propertyNames": {"maxLength": 8}}},
         ["schema", "propertyNames"]),
    ("common", "/$defs/subschema"): ("kind-declaration", {}, ["schema", "properties", "database"]),
    ("common", "/$defs/schema"): ("kind-declaration", {}, ["schema"]),
    ("common", "/$defs/pin"): ("registry", {}, ["kinds", 0]),
    ("common", "/$defs/location"): ("validation-report", {}, ["diagnostics", 0, "location"]),
    ("common", "/$defs/location/properties/entry"): ("validation-report", {}, "entry"),
    ("common", "/$defs/diagnostic"): ("validation-report", {}, ["diagnostics", 0]),
    ("emit-request", ""): ("emit-request", {}, []),
    ("emit-request", "/properties/emitter"): ("emit-request", {}, ["emitter"]),
    ("emit-response", ""): ("emit-response", {}, []),
    ("emit-response", "/$defs/file"): ("emit-response", {}, ["files", 0]),
    ("emit-response", "/$defs/diagnostic"): ("emit-response", {"diagnostics": [WARNING]},
                                             ["diagnostics", 0]),
    ("emitter-manifest", ""): ("emitter-manifest", {}, []),
    ("emitter-manifest", "/properties/reads/items"): ("emitter-manifest", {}, ["reads", 0]),
    ("facts-contract", ""): ("facts-contract", {}, []),
    ("facts-contract", "/properties/source/oneOf/0"): ("facts-contract", {"source": {"authored": True}},
                                                       ["source"]),
    ("facts-contract", "/properties/source/oneOf/1"): ("facts-contract", {}, ["source"]),
    ("facts-contract", "/properties/source/oneOf/1/properties/kind"): ("facts-contract", {},
                                                                       ["source", "kind"]),
    ("facts-contract", "/$defs/fact"): ("facts-contract", {}, ["facts", 0]),
    ("kind-declaration", ""): ("kind-declaration", {}, []),
    ("kind-declaration", "/properties/entryId"): ("kind-declaration", {}, ["entryId"]),
    ("kind-declaration", "/properties/references/items"): ("kind-declaration", {}, ["references", 0]),
    ("kind-declaration", "/properties/bounds"): ("kind-declaration", {}, ["bounds"]),
    ("pack-check-report", ""): ("pack-check-report", {}, []),
    ("pack-check-report", "/properties/contract"): ("pack-check-report", {}, ["contract"]),
    ("pack-check-report", "/properties/pack"): ("pack-check-report", {}, ["pack"]),
    ("registry", ""): ("registry", {}, []),
    ("registry", "/properties/secretScopes/additionalProperties"): ("registry", {}, ["secretScopes", "dev"]),
    ("registry", "/$defs/entry"): ("registry", {}, ["entries", 0]),
    ("registry", "/$defs/overlay"): ("registry", {}, ["overlays", 0]),
    ("registry", "/$defs/patch"): ("registry", {}, ["overlays", 0, "patches", 0]),
    ("resolved-registry", ""): ("resolved-registry", {}, []),
    ("resolved-registry", "/properties/registry"): ("resolved-registry", {}, ["registry"]),
    ("resolved-registry", "/properties/entries/items"): ("resolved-registry", {}, ["entries", 0]),
    ("validation-report", ""): ("validation-report", {}, []),
    ("validation-report", "/properties/registry"): ("validation-report", {}, ["registry"]),
}


def sample(name: str):
    if name == "harness-report":
        return {"harnessReportVersion": "1.0.0"}
    return with_messages(read(SAMPLES[name]))


class RegistrySchemas(unittest.TestCase):
    def test_each_schema_is_a_2020_12_schema_under_its_id(self) -> None:
        self.assertEqual({"common", *SELECTORS.values()}, set(SCHEMA_DOCUMENTS))
        for name, schema in SCHEMA_DOCUMENTS.items():
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(schema)
                self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
                self.assertEqual(NAMESPACE + name + ".schema.json", schema["$id"])
                self.assertTrue(schema["title"].startswith("DRAFT Registry companion 1.0.0: "))
                self.assertIn("spec/registry.md, which governs", schema["description"])

    def test_each_document_schema_requires_its_selector_at_1_0_0(self) -> None:
        for selector, name in SELECTORS.items():
            schema = SCHEMA_DOCUMENTS[name]
            with self.subTest(schema=name):
                self.assertEqual({"const": "1.0.0"}, schema["properties"][selector])
                self.assertIn(selector, schema["required"])
                self.assertEqual(name not in OPEN, schema.get("additionalProperties") is False)

    def test_patterns_end_without_a_dollar(self) -> None:
        # In Python, `$` also matches before a final line feed; ECMA-262 does not. Each anchored
        # pattern ends with (?![\s\S]), which means the end of the string in both.
        def patterns(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key == "pattern" and isinstance(item, str):
                        yield item
                    else:
                        yield from patterns(item)
            elif isinstance(value, list):
                for item in value:
                    yield from patterns(item)

        for name, schema in SCHEMA_DOCUMENTS.items():
            for pattern in patterns(schema):
                with self.subTest(schema=name, pattern=pattern):
                    re.compile(pattern)
                    self.assertFalse(pattern.endswith("$") and not pattern.endswith("\\$"))
                    self.assertNotIn("\\d", pattern)

    def test_code_lists_equal_codes_json(self) -> None:
        definitions = SCHEMA_DOCUMENTS["common"]["$defs"]
        self.assertEqual([c["code"] for c in CODES], definitions["code"]["enum"])
        self.assertEqual([c["code"] for c in CODES if c["severity"] == "warning"],
                         definitions["warningCode"]["enum"])
        diagnostic = subschema("common", "diagnostic")
        for entry in CODES:
            other = "error" if entry["severity"] == "warning" else "warning"
            location = {"document": "registry", "pointer": ""}
            with self.subTest(code=entry["code"]):
                self.assertTrue(diagnostic.is_valid({"code": entry["code"], "severity": entry["severity"],
                                                     "location": location, "message": MESSAGE}))
                self.assertFalse(diagnostic.is_valid({"code": entry["code"], "severity": other,
                                                      "location": location, "message": MESSAGE}))

    def test_every_enum_is_the_texts_list(self) -> None:
        # As the code lists are codes.json's, each other enum is the list the text gives.
        text = folded(SPEC.read_text(encoding="utf-8"))
        found = enums()
        self.assertEqual(set(TEXT_LISTS), set(found))
        for key, passage in TEXT_LISTS.items():
            with self.subTest(schema=key[0], location=key[1]):
                matches = re.findall(passage, text)
                self.assertEqual(1, len(matches), "the passage is not in the text once")
                self.assertEqual(sorted(backticked(matches[0])), sorted(found[key]))

    def test_every_range_form_of_the_text_is_admitted(self) -> None:
        text = folded(SPEC.read_text(encoding="utf-8"))
        forms = backticked(re.search(r"with `versions` one of (.*?); `input`", text).group(1))
        self.assertEqual(4, len(forms))
        reads = SCHEMA_DOCUMENTS["emitter-manifest"]["properties"]["reads"]["items"]["properties"]
        check = Draft202012Validator(reads["versions"], registry=REGISTRY)
        for form in forms:
            for lower, upper in (("1.2.3", "2.0.0"), ("0.0.0", "10.20.30")):
                admitted = form.replace("x.y.z", lower, 1).replace("x.y.z", upper, 1)
                with self.subTest(form=form, versions=admitted):
                    self.assertTrue(check.is_valid(admitted))
        for refused in ("1.2.3", ">1.2.3", "<2.0.0", "<=2.0.0", ">=1.2.3", "^1.2", "~>1.2.3", "^01.2.3",
                        "=1.2.3-rc.1", "^1.2.3+b", ">=1.2.3  <2.0.0", ">=1.2.3 <=2.0.0", "^1.2.3 ",
                        "1.2.3 - 2.0.0", "*", "^1.2.3\n"):
            with self.subTest(versions=refused):
                self.assertFalse(check.is_valid(refused))

    def test_a_refused_registry_still_reports_its_declarations(self) -> None:
        # Section 7.1: a refused registry ends validation after step 2. The admission row's registry
        # is refused, and its report still names the declaration step 2 refuses, so the one it
        # names nothing in is admitted and validated against its schema.
        row = next(row for row in MANIFEST["vectors"] if row["id"] == "admission")
        report = read(row["expected"])
        self.assertFalse(report["valid"])
        self.assertIn("REG-KIND-SCHEMA-KEYWORD", [d["code"] for d in report["diagnostics"]])
        self.assertEqual(["kinds/database.json"], admitted_kinds(row, report))
        self.assertIn("admission: no diagnostic of steps 1 and 2",
                      admitted_row_documents()["kinds/database.json"])

    def test_every_row_document_a_reader_admits_validates(self) -> None:
        found = admitted_row_documents()
        exercised = set()
        for relative, reasons in sorted(found.items()):
            document = read(relative)
            selector = selector_of(document)
            with self.subTest(document=relative, reasons=sorted(reasons)):
                self.assertIsNotNone(selector)
                name = SELECTORS[selector]
                exercised.add(name)
                problems = [f"{pointer(e)}: {e.message}"
                            for e in validator(name).iter_errors(with_messages(document))]
                self.assertEqual([], problems)
        # Every document schema but the harness report's has a row document; the rows have no
        # harness report (spec/registry.md section 14).
        self.assertEqual(set(SELECTORS.values()) - {"harness-report"}, exercised)

    def test_no_schema_refuses_what_a_row_admits(self) -> None:
        # The host's rows list every refusal of a manifest or a response (section 11); a schema
        # refuses nothing at another pointer.
        for row in MANIFEST["vectors"]:
            if row["operation"] not in ("manifest", "response"):
                continue
            refusals = {r["pointer"] for r in read(row["expected"])["refusals"]}
            member = "manifest" if row["operation"] == "manifest" else "response"
            name = "emitter-manifest" if member == "manifest" else "emit-response"
            refused = {pointer(e) for e in validator(name).iter_errors(read(row[member]))}
            with self.subTest(row=row["id"]):
                self.assertTrue(refused, "the schema states none of this row's refusals")
                self.assertLessEqual(refused, refusals)


class ClosedSchemas(unittest.TestCase):
    def sample(self, name: str):
        return sample(name)

    def assertRefused(self, name: str, document) -> None:  # noqa: N802
        self.assertFalse(validator(name).is_valid(document))

    def test_samples_validate(self) -> None:
        for name in SELECTORS.values():
            with self.subTest(schema=name):
                self.assertEqual([], [e.message for e in validator(name).iter_errors(self.sample(name))])

    def test_an_unlisted_member_is_refused(self) -> None:
        for name in set(SELECTORS.values()) - OPEN:
            document = self.sample(name)
            document["unlisted"] = True
            with self.subTest(schema=name):
                self.assertRefused(name, document)

    def test_another_selector_is_refused(self) -> None:
        for selector, name in SELECTORS.items():
            for value in ("1.0.1", "1.1.0", "2.0.0", 1, None):
                document = self.sample(name)
                document[selector] = value
                with self.subTest(schema=name, selector=value):
                    self.assertRefused(name, document)

    def test_a_missing_required_member_is_refused(self) -> None:
        for name in SELECTORS.values():
            for member in SCHEMA_DOCUMENTS[name]["required"]:
                document = self.sample(name)
                del document[member]
                with self.subTest(schema=name, member=member):
                    self.assertRefused(name, document)

    def test_every_closed_object_is_held_closed(self) -> None:
        # Each object a schema closes is listed, and a sample that holds one valid is refused once
        # the object gains an unlisted member.
        found = {(name, location) for name, schema in SCHEMA_DOCUMENTS.items()
                 for location, value in walk(schema)
                 if isinstance(value, dict) and False in (value.get("additionalProperties"),
                                                          value.get("unevaluatedProperties"))}
        self.assertEqual(set(CLOSED), found)
        for (name, location), (document_schema, changes, path) in CLOSED.items():
            document = self.sample(document_schema)
            document.update(copy.deepcopy(changes))
            if path == "entry":
                index = next(i for i, d in enumerate(document["diagnostics"]) if "entry" in d["location"])
                path = ["diagnostics", index, "location", "entry"]
            with self.subTest(schema=name, location=location, path=path):
                self.assertTrue(validator(document_schema).is_valid(document))
                target = document
                for part in path:
                    target = target[part]
                target["unlisted"] = True
                self.assertRefused(document_schema, document)

    def test_nested_documents_are_closed(self) -> None:
        # A request holds declarations and resolved registries, each closed by its own schema.
        for path in (["declarations", 0], ["resolved", 0], ["resolved", 0, "kinds", 0]):
            document = self.sample("emit-request")
            target = document
            for part in path:
                target = target[part]
            target["unlisted"] = True
            with self.subTest(path=path):
                self.assertRefused("emit-request", document)

    def test_kind_declaration_forms(self) -> None:
        base = self.sample("kind-declaration")
        broken = [
            ("id", "https://example.invalid/kinds/x#fragment"), ("id", "relative/kind"),
            ("id", "https://example.invalid/a b"), ("version", "1.0.0+build"), ("version", "1.0"),
            ("kind", "Db-role"), ("kind", "db-role\n"), ("owner", ""), ("owner", "a b"),
            ("entryId", {"pattern": "^a$", "flags": "i"}), ("entryId", {"pattern": "a" * 257}),
            ("secrets", ["/password", "/password"]), ("secrets", ["password"]), ("secrets", [""]),
            ("secrets", ["/~3"]), ("overlayable", ["/" + "a" * 512]),
            ("references", [{"pointer": "/database", "kinds": []}]),
            ("references", [{"pointer": "/database", "kinds": ["database", "database"]}]),
            ("bounds", {"maxEntries": 0}), ("bounds", {"maxEntryBytes": 8388609}),
            ("bounds", {"maxRows": 1}), ("deprecated", "yes"),
            ("schema", {"type": "object", "format": "uri"}),
            ("schema", {"oneOf": [{"type": "string"}]}),
            ("schema", {"properties": {"a": {"$defs": {"b": {}}}}}),
            ("schema", {"items": [{"type": "string"}]}),
            ("schema", {"enum": []}), ("schema", {"enum": list(range(1025))}),
            ("schema", {"anyOf": [True] * 17}), ("schema", {"allOf": []}),
            ("schema", {"type": ["string", "string"]}), ("schema", {"type": "decimal"}),
            ("schema", {"required": ["a", "a"]}), ("schema", {"minLength": -1}),
            ("schema", {"minLength": 1.5}), ("schema", {"propertyNames": {"minLength": 1}}),
            ("schema", {"$ref": "#/definitions/a"}), ("schema", {"$ref": "#/$defs/a/b"}),
            ("schema", {"$ref": "#/$defs/"}), ("schema", {"$ref": "#/$defs/~2"}),
            ("schema", {"pattern": "a" * 257}), ("schema", 1),
        ]
        for member, value in broken:
            document = copy.deepcopy(base)
            document[member] = value
            with self.subTest(member=member, value=value):
                self.assertRefused("kind-declaration", document)
        admitted = [
            ("schema", True), ("schema", {"$defs": {"a~1b": {}}, "$ref": "#/$defs/a~1b"}),
            ("schema", {"type": ["string", "null"], "minLength": 2.0}),
            ("secrets", ["/grants/*/role", "/~2"]),
        ]
        for member, value in admitted:
            document = copy.deepcopy(base)
            document[member] = value
            with self.subTest(member=member, value=value):
                self.assertTrue(validator("kind-declaration").is_valid(document))

    def test_registry_forms(self) -> None:
        base = self.sample("registry")
        broken = [
            ("environments", []), ("environments", ["dev", "dev"]), ("environments", ["Dev"]),
            ("environments", [f"e{i}" for i in range(33)]), ("owners", []),
            ("kinds", [{"kind": "database", "id": "https://example.invalid/kinds/database",
                        "version": "1.0.0", "digest": "sha256:" + "A" * 64}]),
            ("secretScopes", {"dev": {"aws-sm": ["example-dev"]}}),
            ("secretScopes", {"dev": {"gcp-sm": ["example-dev", "example-dev"]}}),
            ("secretScopes", {"dev": {"gcp-sm": ["123456"]}}),
            ("overlays", [{"environment": "prod", "patches": [
                {"kind": "db-role", "id": "billing-api", "set": {"/password": None}}]}]),
            ("overlays", [{"environment": "prod", "patches": [
                {"kind": "db-role", "id": "billing-api", "set": {"password": 1}}]}]),
            ("overlays", [{"environment": "prod", "patches": [
                {"kind": "db-role", "id": "billing-api", "set": {"/~2": 1}}]}]),
            ("overlays", [{"environment": "prod"}]),
        ]
        for member, value in broken:
            document = copy.deepcopy(base)
            document[member] = value
            with self.subTest(member=member, value=value):
                self.assertRefused("registry", document)
        for entry in ({"environments": []}, {"environments": ["dev", "dev"]}, {"id": "a/b"},
                      {"id": "a#b"}, {"id": ""}, {"id": "a" * 129}):
            document = copy.deepcopy(base)
            document["entries"][0].update(entry)
            with self.subTest(entry=entry):
                self.assertRefused("registry", document)

    def test_report_forms(self) -> None:
        base = self.sample("validation-report")
        document = copy.deepcopy(base)
        document["valid"] = True
        document["diagnostics"].append({"code": "REG-ENTRY-OWNER", "severity": "error", "message": MESSAGE,
                                        "location": {"document": "registry", "pointer": "/entries/0/owner"}})
        self.assertRefused("validation-report", document)
        locations = [
            {"document": "registry"}, {"document": "ledger", "pointer": ""},
            {"document": "registry", "pointer": "", "line": 1},
            {"document": "yaml", "pointer": "/a", "line": 1},
            {"document": "registry", "pointer": "", "path": "a"},
            {"document": "vector", "pointer": "", "path": "/abs"},
            {"document": "registry", "pointer": "", "manifest": 1},
            {"document": "registry", "pointer": "", "entry": {"kind": "a"}},
            {"document": "registry", "pointer": "a"},
        ]
        for location in locations:
            document = copy.deepcopy(base)
            document["diagnostics"][0]["location"] = location
            with self.subTest(location=location):
                self.assertRefused("validation-report", document)
        document = copy.deepcopy(base)
        document["diagnostics"] = [document["diagnostics"][0]] * 1002
        self.assertRefused("validation-report", document)
        document = copy.deepcopy(base)
        del document["diagnostics"][0]["message"]
        self.assertRefused("validation-report", document)

    def test_contract_forms(self) -> None:
        base = self.sample("facts-contract")
        facts = [
            {"pointer": "", "type": "string", "present": "always"},
            {"pointer": "/" + "/a" * 35, "type": "string", "present": "always"},
            {"pointer": "/a", "type": "integer", "present": "always"},
            {"pointer": "/a", "type": "string", "present": "sometimes"},
            {"pointer": "/a", "type": "string", "present": "always", "items": "string"},
            {"pointer": "/a", "type": "object", "present": "always", "values": [{}]},
            {"pointer": "/a", "type": "null", "present": "always", "values": [None]},
            {"pointer": "/a", "type": "array", "present": "always", "values": [["x"]]},
            {"pointer": "/a", "type": "array", "present": "always", "values": ["x"]},
            {"pointer": "/a", "type": "array", "items": "null", "present": "always", "values": [None]},
            {"pointer": "/a", "type": "array", "items": "object", "present": "always", "values": [{}]},
            {"pointer": "/a", "type": "array", "items": "array", "present": "always", "values": [[]]},
            {"pointer": "/a", "type": "string", "present": "always", "values": []},
            {"pointer": "/a", "type": "string", "present": "always", "values": ["x", "x"]},
            {"pointer": "/a", "type": "string", "present": "always", "values": [1]},
            {"pointer": "/a", "type": "decimal", "present": "always", "values": ["1.0e2"]},
            {"pointer": "/a", "type": "decimal", "present": "always", "values": [1]},
            {"pointer": "/a", "type": "array", "items": "boolean", "present": "always", "values": ["true"]},
            {"pointer": "/a", "type": "string", "present": "always", "secretReference": True},
            {"pointer": "/a", "type": "object", "present": "always", "secretReference": False},
        ]
        for fact in facts:
            document = copy.deepcopy(base)
            document["facts"] = [fact]
            with self.subTest(fact=fact):
                self.assertRefused("facts-contract", document)
        for source in ({"authored": False}, {}, {"authored": True, "kind": base["source"]["kind"]},
                       {"kind": {"id": "x", "version": "1.0.0", "digest": base["source"]["kind"]["digest"]}}):
            document = copy.deepcopy(base)
            document["source"] = source
            with self.subTest(source=source):
                self.assertRefused("facts-contract", document)
        for member, value in (("id", "relative/contract"), ("id", "https://example.invalid/c#f"),
                              ("id", 1), ("version", "1.0"), ("version", "1.0.0+build"), ("version", 1)):
            document = copy.deepcopy(base)
            document[member] = value
            with self.subTest(member=member, value=value):
                self.assertRefused("facts-contract", document)
        document = copy.deepcopy(base)
        document["source"] = {"authored": True}
        document["facts"] = [{"pointer": "/a/*/~2", "type": "array", "items": "decimal", "present": "optional",
                              "values": ["-1.5", "0"]}]
        self.assertTrue(validator("facts-contract").is_valid(document))
        for fact in ({"type": "string", "values": ["x"]}, {"type": "boolean", "values": [True, False]},
                     {"type": "array", "items": "string", "values": ["x"]},
                     {"type": "array", "items": "boolean", "values": [True]}):
            document["facts"] = [{"pointer": "/a", "present": "always", **fact}]
            with self.subTest(fact=fact):
                self.assertTrue(validator("facts-contract").is_valid(document))

    def test_pack_check_report_forms(self) -> None:
        # Section 10.5: a refused contract's report has its diagnostics alone, and an admitted
        # contract's has both digests and the pack's advisories.
        base = self.sample("pack-check-report")
        refused = {"code": "FACTS-CONTRACT-FORM", "severity": "error", "message": MESSAGE,
                   "location": {"document": "contract", "pointer": ""}}
        document = copy.deepcopy(base)
        del document["contract"], document["pack"]
        document["diagnostics"] = [refused]
        self.assertTrue(validator("pack-check-report").is_valid(document))
        document["diagnostics"] = [refused] * 1001
        self.assertTrue(validator("pack-check-report").is_valid(document))
        for diagnostics in ([], [refused] * 1002, base["diagnostics"]):
            document["diagnostics"] = diagnostics
            with self.subTest(diagnostics=len(diagnostics)):
                self.assertRefused("pack-check-report", document)
        for member in ("contract", "pack"):
            document = copy.deepcopy(base)
            del document[member]
            with self.subTest(without=member):
                self.assertRefused("pack-check-report", document)
            document["diagnostics"] = [refused]
            with self.subTest(without=member, diagnostics="the contract's"):
                self.assertRefused("pack-check-report", document)
        document = copy.deepcopy(base)
        document["diagnostics"].append(refused)
        self.assertRefused("pack-check-report", document)

    def test_manifest_forms(self) -> None:
        base = self.sample("emitter-manifest")
        broken = [
            ("reads", [{"kind": "queue", "id": "https://example.invalid/kinds/queue", "versions": "1.0.0"}]),
            ("reads", [{"kind": "queue", "id": "https://example.invalid/kinds/queue", "versions": "^1.0"}]),
            ("reads", [{"kind": "queue", "id": "https://example.invalid/kinds/queue",
                        "versions": ">=1.0.0 <2.0.0-rc.1"}]),
            ("input", "registry"), ("requestVersions", []), ("environments", "some"),
            ("command", []), ("command", ["/usr/bin/emit"]), ("command", ["../emit"]), ("command", [""]),
            ("command", ["a:b"]), ("command", ["~x"]), ("command", ["a/./b"]), ("command", ["con"]),
            ("command", ["Aux.sh"]), ("command", ["."]), ("command", [".."]), ("command", ["./"]),
            ("command", ["./."]), ("command", ["././gen"]), ("command", ["./../gen"]), ("command", ["gen/"]),
            ("command", ["a//b"]), ("command", ["gen."]), ("command", [".git/hooks/x"]),
            ("command", ["./.git/x"]), ("command", ["./~x"]), ("command", ["./con"]), ("command", ["a\\b"]),
            ("command", ["gen", "/abs"]), ("command", ["gen", "../x"]), ("command", ["gen", "a/../b"]),
            ("command", ["gen", "a/.."]), ("command", ["gen", "a\x00"]), ("command", ["gen", 1]),
            ("description", 1), ("deprecated", "yes"), ("deprecated", 1),
            ("requestVersions", ["1.0.0", "1.0.0"]), ("requestVersions", ["1.0"]),
            ("requestVersions", ["1.0.0+build"]), ("requestVersions", [1]),
            ("owns", []), ("owns", ["gen/**", "gen/**"]), ("env", ["EXAMPLE", "EXAMPLE"]),
            ("owns", ["**"]), ("owns", ["*/gen"]), ("owns", ["gen/a**"]), ("owns", ["gen/***"]),
            ("owns", ["gen/"]), ("owns", ["gen/../x"]), ("owns", ["/gen"]),
            ("env", ["PATH"]), ("env", ["SOURCE_DATE_EPOCH"]), ("env", ["lower"]), ("env", ["A" * 65]),
            ("options", {"oneOf": []}),
        ]
        for member, value in broken:
            document = copy.deepcopy(base)
            document[member] = value
            with self.subTest(member=member, value=value):
                self.assertRefused("emitter-manifest", document)
        twice = copy.deepcopy(base)
        twice["reads"] = [base["reads"][0], base["reads"][0]]
        self.assertRefused("emitter-manifest", twice)
        admitted = [
            ("command", ["./gen"]), ("command", ["bin/gen", "--flag", "a/b", "-", "..x", "./x", ""]),
            ("command", ["./bin/gen.py"]), ("command", ["COM0"]), ("description", "An emitter."),
            ("deprecated", True), ("deprecated", False), ("requestVersions", ["1.0.0", "1.1.0-rc.1"]),
        ]
        for member, value in admitted:
            document = copy.deepcopy(base)
            document[member] = value
            with self.subTest(member=member, value=value):
                self.assertTrue(validator("emitter-manifest").is_valid(document))
        facts = copy.deepcopy(base)
        facts["input"] = "factsContracts"
        self.assertRefused("emitter-manifest", facts)
        del facts["environments"]
        self.assertTrue(validator("emitter-manifest").is_valid(facts))
        resolved = copy.deepcopy(base)
        del resolved["environments"]
        self.assertRefused("emitter-manifest", resolved)
        resolved["input"] = "resolved"
        self.assertRefused("emitter-manifest", resolved)

    def test_request_forms(self) -> None:
        base = self.sample("emit-request")
        both = copy.deepcopy(base)
        both["factsContracts"] = []
        self.assertRefused("emit-request", both)
        facts = copy.deepcopy(base)
        del facts["declarations"], facts["resolved"]
        facts["factsContracts"] = [read("vectors/facts-contracts/contract-bag.json")]
        self.assertTrue(validator("emit-request").is_valid(facts))
        half = copy.deepcopy(base)
        del half["resolved"]
        self.assertRefused("emit-request", half)
        empty = copy.deepcopy(base)
        empty["resolved"] = []
        self.assertRefused("emit-request", empty)

    def test_response_forms(self) -> None:
        base = self.sample("emit-response")
        paths = ["../a", "a/./b", "a//b", "~a", "a/~b", "a/", "/a", "a\\b", "a:b", "a\x00b", "a\x1fb",
                 "a\x85b", "a.", "a ", "a/CON", "nul.txt", "Com1.log", "LPT\u00b9", "CON .txt",
                 "conin$", ".git", ".GIT/config", "git~1", ".git. .", ".g\u200cit", "\ufeff.git",
                 "a" * 513]
        for path in paths:
            document = copy.deepcopy(base)
            document["files"][0]["path"] = path
            with self.subTest(path=path):
                self.assertRefused("emit-response", document)
        for path in ("COM0", "CONSOLE", "a.git", ".gitignore", "git~2", "a/b.c", "*"):
            document = copy.deepcopy(base)
            document["files"][0]["path"] = path
            with self.subTest(path=path):
                self.assertTrue(validator("emit-response").is_valid(document))
        files = [
            {"path": "a"}, {"path": "a", "text": "x\n", "base64": ""}, {"path": "a", "text": "x"},
            {"path": "a", "text": "x\r\n"}, {"path": "a", "text": "x\n", "mode": "0600"},
        ] + [{"path": "a", "base64": value} for value in (
            "QR==", "QUJ=", "QQ", "QQ=", "Q===", "QUJD====", "QUJD\n", "QU\nJD", "QU JD", "-_8=", "QUJD=",
            "=", "QUJ", 1)]
        for file in files:
            document = copy.deepcopy(base)
            document["files"][0] = file
            with self.subTest(file=file):
                self.assertRefused("emit-response", document)
        diagnostics = [
            {"code": "x-a", "severity": "warning", "location": {"document": "registry", "pointer": ""},
             "message": MESSAGE},
            {"code": "x-a", "severity": "info", "location": {"document": "registry", "pointer": ""}},
            {"code": "REG-ENTRY-OWNER", "severity": "error",
             "location": {"document": "registry", "pointer": ""}},
            {"code": "x-a", "severity": "warning", "location": {"document": "manifest", "pointer": ""}},
            {"code": "x-a", "severity": "warning",
             "location": {"document": "registry", "pointer": "", "path": "a"}},
        ]
        for diagnostic in diagnostics:
            document = copy.deepcopy(base)
            document["diagnostics"] = [diagnostic]
            with self.subTest(diagnostic=diagnostic):
                self.assertRefused("emit-response", document)
        for value in ("", "QQ==", "QUI=", "QUJD", "+/+/", "AA==", "AAA=", "QUJDRA=="):
            document = copy.deepcopy(base)
            document["files"][0] = {"path": "a", "base64": value}
            with self.subTest(base64=value):
                self.assertTrue(validator("emit-response").is_valid(document))
        document = copy.deepcopy(base)
        document["diagnostics"] = [{**WARNING, "value": 1}]
        self.assertRefused("emit-response", document)
        document = copy.deepcopy(base)
        document["files"] = [{"path": f"gen/{i}", "base64": ""} for i in range(10001)]
        self.assertRefused("emit-response", document)


class RegistrySchemasText(unittest.TestCase):
    def test_the_companion_says_where_the_schemas_are(self) -> None:
        text = re.sub(r"\s+", " ", SPEC.read_text(encoding="utf-8"))
        self.assertIn("https://github.com/Judgment-Pack/judgment-pack-spec/tree/main/schema/registry/1.0.0",
                      text)
        self.assertNotIn("](../schema/registry", text)
        self.assertNotIn("do not exist yet", text)


if __name__ == "__main__":
    unittest.main()

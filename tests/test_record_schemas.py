"""The schemas of the decision record and audit chain, the dialect recordings and receipts as
consumed (#286), held to every vector of their families and to hand-written cases.

Every vector named below must validate. The hand-written cases change one member of a vector each
and must be refused, or name a value the specification gives that no vector carries and must be
accepted, so that every constraint and every enum value in the schemas is exercised by a case.
"""

from __future__ import annotations

import base64
import copy
import functools
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
DIALECT = ROOT / "conformance" / "dialect"
RECORDINGS = ("vectors", "vectors-0.3.0")

SCHEMA_PATHS = {
    "receipt": "schema/receipt/3/acquisition.schema.json",
    "record": "schema/decision-record/1/record.schema.json",
    "checkpoint": "schema/decision-record/1/checkpoint.schema.json",
    "preparation": "schema/dialect-recording/1/preparation.schema.json",
    "export": "schema/dialect-recording/1/export.schema.json",
}
NAMESPACE = "https://judgmentpack.org/"
DELETE = object()
MAX = 9007199254740991

# The members each object must carry, as the prose names them. Written here rather than read from
# the schemas, so that a schema that stops requiring one fails a case.
REQUIRED = {
    "receipt": ("receiptVersion", "kind", "callIndex", "sessionId", "servedAt", "keyId", "signature",
                "source", "authority", "acquisition", "argumentsCommitment", "resultDigest"),
    "acquisition": ("adapter", "shape", "endpoint", "observedAt"),
    "checkpoint": ("checkpointVersion", "trail", "sequence", "recordDigest"),
    "preparation": ("version", "verifiedAt", "mappingDigest", "verification", "cites", "lineage", "outcomes"),
    "outcome": ("name", "parameters", "claim", "status", "reason"),
    "claim": ("facts", "evidenceAvailability", "acquisitionStatus", "reason", "basis"),
    "lineageEntry": ("source", "kind", "target", "class", "generatedInfluence", "present", "status", "reason",
                     "basis", "readDigest"),
    "calculation": ("calculator", "status", "inputs", "asOf"),
}


def strict_json(data: bytes, what: str):
    """Read one JSON value; a repeated member name or a non-finite number is refused, not read."""
    def pairs(items):
        names = [name for name, _ in items]
        if len(names) != len(set(names)):
            raise ValueError("%s repeats a member name" % what)
        return dict(items)

    def constant(name):
        raise ValueError("%s holds %s" % (what, name))

    return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)


def read(path: Path):
    return strict_json(path.read_bytes(), path.relative_to(ROOT).as_posix())


def load_schemas() -> dict:
    return {name: read(ROOT / path) for name, path in SCHEMA_PATHS.items()}


# The schemas the tests validate with. The mutation check replaces this with a changed copy.
SCHEMAS = load_schemas()


_BUILT: list = []


def validators(schemas: dict) -> dict:
    """The validators of schemas, built once for each schemas object."""
    if _BUILT and _BUILT[0] is schemas:
        return _BUILT[1]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values())
    checker = FormatChecker()
    built = {name: Draft202012Validator(schema, registry=registry, format_checker=checker)
             for name, schema in schemas.items()}
    _BUILT[:] = [schemas, built]
    return built


def recording_directories() -> list[Path]:
    found = [path for set_name in RECORDINGS for path in sorted((DIALECT / set_name).iterdir())
             if path.is_dir()]
    if not found:
        raise AssertionError("no dialect recording was found")
    return found


def acquisition_receipts(acquisitions: dict, where: str) -> list[tuple[str, object]]:
    """Each receipt of the acquisitions (spec/dialect.md section 5.2): a source's own, and each
    retained response's of a research record."""
    found = []
    for name, member in acquisitions.items():
        response = member["response"]
        if "receipt" in response:
            found.append(("%s %s" % (where, name), response["receipt"]))
        result = response.get("result")
        if isinstance(result, dict) and isinstance(result.get("responses"), list):
            for index, retained in enumerate(result["responses"]):
                if "receipt" in retained:
                    found.append(("%s %s response %d" % (where, name, index), retained["receipt"]))
    return found


def embedded_receipts(value, where: str) -> list[tuple[str, object]]:
    """Every object with a member receiptVersion, inside JSON text held in strings included."""
    found = []
    if isinstance(value, dict):
        if "receiptVersion" in value:
            found.append((where, value))
        for name, member in value.items():
            found.extend(embedded_receipts(member, where + "/" + name))
    elif isinstance(value, list):
        for index, member in enumerate(value):
            found.extend(embedded_receipts(member, "%s/%d" % (where, index)))
    elif isinstance(value, str) and value[:1] in ("{", "["):
        try:
            inner = strict_json(value.encode("utf-8"), where)
        except ValueError:
            return found
        found.extend(embedded_receipts(inner, where + "(text)"))
    return found


@functools.lru_cache(maxsize=None)
def receipts() -> tuple:
    found = []
    for directory in recording_directories() + sorted((DIALECT / "artifact-identity").iterdir()):
        if (directory / "sources.json").is_file():
            found.extend(acquisition_receipts(read(directory / "sources.json"),
                                              directory.relative_to(ROOT).as_posix()))
    for directory in recording_directories():
        export = read(directory / "run.json")
        for label, source in (("run.input", export["run"]["input"]["source"]),
                              ("release.sample", export["release"]["sample"]["source"])):
            if "sources" in source:
                found.extend(acquisition_receipts(source["sources"], "%s %s" % (
                    directory.relative_to(ROOT).as_posix(), label)))
    retained = read(ROOT / "conformance/retained-column/1/preparations.json")
    found.extend(embedded_receipts(retained, "conformance/retained-column/1/preparations.json"))
    return tuple(found)


@functools.lru_cache(maxsize=None)
def preparations() -> tuple:
    found = []
    for directory in recording_directories() + sorted((DIALECT / "artifact-identity").iterdir()):
        if (directory / "preparation.json").is_file():
            found.append((directory.relative_to(ROOT).as_posix(), read(directory / "preparation.json")))
    for directory in recording_directories():
        found.append((directory.relative_to(ROOT).as_posix() + " release.sample",
                      read(directory / "run.json")["release"]["sample"]["preparation"]))
    found.append(("research-replay-vector.json", read(DIALECT / "research-replay-vector.json")["preparation"]))
    return tuple(found)


@functools.lru_cache(maxsize=None)
def exports() -> tuple:
    return tuple((directory.relative_to(ROOT).as_posix(), read(directory / "run.json"))
                 for directory in recording_directories())


@functools.lru_cache(maxsize=None)
def records() -> tuple:
    found = []
    for where, export in exports():
        found.append((where + " run.audit", export["run"]["audit"]))
        if "auditBytes" in export["run"]:
            line = base64.b64decode(export["run"]["auditBytes"], validate=True)
            found.append((where + " run.auditBytes", strict_json(line, where + " run.auditBytes")))
    return tuple(found)


@functools.lru_cache(maxsize=None)
def checkpoints() -> tuple:
    found = []
    for directory in recording_directories():
        where = directory.relative_to(ROOT).as_posix()
        held = directory / "checkpoints.jsonl"
        if held.is_file():
            for number, line in enumerate(held.read_bytes().split(b"\n")[:-1], 1):
                found.append(("%s checkpoints.jsonl line %d" % (where, number), strict_json(line, where)))
        export = read(directory / "run.json")
        if "chain" in export:
            found.append((where + " chain.checkpoint", export["chain"]["checkpoint"]))
    return tuple(found)


def changed(value, path: tuple, new):
    """A deep copy of value with the member at path set to new, or removed for DELETE."""
    result = copy.deepcopy(value)
    at = result
    for key in path[:-1]:
        at = at[key]
    if new is DELETE:
        del at[path[-1]]
    else:
        at[path[-1]] = new
    return result


def vector(*parts: str):
    return read(DIALECT.joinpath(*parts))


class SchemaTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.validators = validators(SCHEMAS)

    def errors(self, name: str, value) -> list:
        return list(self.validators[name].iter_errors(value))

    def accepts(self, name: str, value, case: str) -> None:
        with self.subTest(schema=name, case=case):
            self.assertEqual([], [error.message for error in self.errors(name, value)])

    def refuses(self, name: str, value, case: str) -> None:
        with self.subTest(schema=name, case=case):
            self.assertNotEqual([], self.errors(name, value), "%s was accepted" % case)


class TheSchemasAsPublished(unittest.TestCase):
    def test_each_schema_is_valid_draft_2020_12_at_its_own_id_path(self) -> None:
        for name, path in SCHEMA_PATHS.items():
            with self.subTest(schema=name):
                schema = read(ROOT / path)
                Draft202012Validator.check_schema(schema)
                self.assertEqual(NAMESPACE + path, schema["$id"])

    def test_each_schema_says_its_maturity_and_that_it_changes_no_normative_status(self) -> None:
        for name, path in SCHEMA_PATHS.items():
            with self.subTest(schema=name):
                description = read(ROOT / path)["description"]
                self.assertTrue(description.startswith("Informative, at draft maturity. "))
                self.assertIn("Core section 1.1 does not list this schema among the normative "
                              "artifacts, so publishing it changes no format's normative status",
                              description)

    def test_the_export_carries_the_decision_record_schema_unchanged(self) -> None:
        record = {name: value for name, value in read(ROOT / SCHEMA_PATHS["record"]).items()
                  if name not in ("$schema", "$id", "title", "description")}
        copied = dict(read(ROOT / SCHEMA_PATHS["export"])["$defs"]["record"])
        copied.pop("description")
        self.assertEqual(record, copied)


class EveryVectorValidates(SchemaTestCase):
    # The vector sets are frozen; a vector added to one changes these counts in the same change.
    def check_all(self, name: str, found: tuple, count: int) -> None:
        self.assertEqual(count, len(found), "the %s vectors found" % name)
        for where, value in found:
            self.accepts(name, value, where)

    def test_every_receipt_validates(self) -> None:
        self.check_all("receipt", receipts(), 932)

    def test_every_preparation_validates(self) -> None:
        self.check_all("preparation", preparations(), 190)

    def test_every_recording_validates(self) -> None:
        self.check_all("export", exports(), 93)

    def test_every_record_validates(self) -> None:
        self.check_all("record", records(), 181)

    def test_every_checkpoint_validates(self) -> None:
        self.check_all("checkpoint", checkpoints(), 174)


class Receipts(SchemaTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.receipt = vector("vectors", "valid", "sources.json")["fx"]["response"]["receipt"]

    def test_values_no_vector_carries_are_accepted(self) -> None:
        for shape in ("airbyte", "command", "http", "mcp"):
            self.accepts("receipt", changed(self.receipt, ("acquisition", "shape"), shape), "shape " + shape)
        self.accepts("receipt", changed(self.receipt, ("acquisition", "endpoint"), None), "endpoint null")
        self.accepts("receipt", changed(self.receipt, ("callIndex",), MAX), "callIndex 2^53-1")
        self.accepts("receipt", changed(self.receipt, ("sessionId",), ""), "sessionId not a token")
        self.accepts("receipt", changed(self.receipt, ("servedAt",), "2024-02-29T23:59:59Z"), "a leap day")
        self.accepts("receipt", changed(self.receipt, ("witness",), {"any": "form"}), "a member not read")

    def test_a_receipt_of_another_form_is_refused(self) -> None:
        cases = {
            "receiptVersion 2": (("receiptVersion",), "2"),
            "receiptVersion integer": (("receiptVersion",), 3),
            "kind action": (("kind",), "action"),
            "callIndex -1": (("callIndex",), -1),
            "callIndex 2^53": (("callIndex",), MAX + 1),
            "callIndex string": (("callIndex",), "0"),
            "sessionId null": (("sessionId",), None),
            "servedAt fraction": (("servedAt",), "2026-10-14T14:58:26.5Z"),
            "servedAt offset": (("servedAt",), "2026-10-14T14:58:26+00:00"),
            "servedAt newline": (("servedAt",), "2026-10-14T14:58:26Z\n"),
            "servedAt no such day": (("servedAt",), "2026-02-30T00:00:00Z"),
            "servedAt leap second": (("servedAt",), "2026-12-31T23:59:60Z"),
            "servedAt hour 24": (("servedAt",), "2026-10-14T24:00:00Z"),
            "observedAt no such month": (("acquisition", "observedAt"), "2026-13-01T00:00:00Z"),
            "keyId upper case": (("keyId",), "009D0C0170CD88991A709E465C4B6F07"),
            "keyId 31 characters": (("keyId",), "009d0c0170cd88991a709e465c4b6f0"),
            "keyId newline": (("keyId",), "009d0c0170cd88991a709e465c4b6f07\n"),
            "keyId not a string": (("keyId",), 9),
            "signature 127 characters": (("signature",), self.receipt["signature"][:-1]),
            "signature newline": (("signature",), self.receipt["signature"] + "\n"),
            "signature not a string": (("signature",), None),
            "servedAt not a string": (("servedAt",), 1760453906),
            "observedAt not a string": (("acquisition", "observedAt"), None),
            "signature upper case": (("signature",), self.receipt["signature"].upper()),
            "source not a string": (("source",), None),
            "authority not a string": (("authority",), 1),
            "adapter with a fourth member": (("acquisition", "adapter", "extra"), "x"),
            "adapter without digest": (("acquisition", "adapter", "digest"), DELETE),
            "adapter without name": (("acquisition", "adapter", "name"), DELETE),
            "adapter without version": (("acquisition", "adapter", "version"), DELETE),
            "adapter name not a string": (("acquisition", "adapter", "name"), 1),
            "adapter version not a string": (("acquisition", "adapter", "version"), 1),
            "adapter digest upper case": (("acquisition", "adapter", "digest"),
                                          self.receipt["acquisition"]["adapter"]["digest"].upper()),
            "adapter not an object": (("acquisition", "adapter"), "dbhub"),
            "shape web": (("acquisition", "shape"), "web"),
            "endpoint a number": (("acquisition", "endpoint"), 1),
            "a page": (("acquisition", "pageItems"), []),
            "acquisition not an object": (("acquisition",), []),
            "argumentsCommitment without sha256": (("argumentsCommitment",),
                                                   self.receipt["argumentsCommitment"][7:]),
            "resultDigest 63 characters": (("resultDigest",), self.receipt["resultDigest"][:-1]),
            "resultDigest newline": (("resultDigest",), self.receipt["resultDigest"] + "\n"),
            "resultDigest not a string": (("resultDigest",), None),
            "argumentsCommitment not a string": (("argumentsCommitment",), 0),
            "acquisition a string": (("acquisition",), "mcp"),
        }
        for required in REQUIRED["receipt"]:
            cases["without " + required] = ((required,), DELETE)
        for required in REQUIRED["acquisition"]:
            cases["acquisition without " + required] = (("acquisition", required), DELETE)
        for case, (path, new) in cases.items():
            self.refuses("receipt", changed(self.receipt, path, new), case)
        self.refuses("receipt", [self.receipt], "not an object")


class DecisionRecords(SchemaTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.record = vector("vectors", "valid", "run.json")["run"]["audit"]
        self.checkpoint = strict_json((DIALECT / "vectors/valid/checkpoints.jsonl").read_bytes(), "checkpoint")

    def test_a_record_carries_any_binding_and_members_not_read(self) -> None:
        self.accepts("record", changed(self.record, ("binding",), None), "binding null")
        self.accepts("record", changed(self.record, ("binding",), DELETE), "no binding")
        self.accepts("record", {"inputs": {}}, "inputs alone")
        for name in ("bindings", "bındıng", "Binding\n", "xbinding", "binding_"):
            self.accepts("record", changed(self.record, (name,), 1), "the member %r" % name)

    def test_a_record_of_another_form_is_refused(self) -> None:
        for name in ("Binding", "BINDING", "bindinG", "bInDiNg"):
            self.refuses("record", changed(self.record, (name,), self.record["binding"]),
                         "a member %s" % name)
        self.refuses("record", changed(self.record, ("inputs",), DELETE), "no inputs")
        self.refuses("record", changed(self.record, ("inputs",), []), "inputs an array")
        self.refuses("record", changed(self.record, ("inputs",), None), "inputs null")
        self.refuses("record", [self.record], "not an object")

    def test_a_checkpoint_at_its_bounds_is_accepted(self) -> None:
        self.accepts("checkpoint", changed(self.checkpoint, ("sequence",), 1), "sequence 1")
        self.accepts("checkpoint", changed(self.checkpoint, ("sequence",), MAX - 1), "sequence 2^53-2")

    def test_a_checkpoint_of_another_form_is_refused(self) -> None:
        cases = {
            "a fifth member": (("extra",), 1),
            "checkpointVersion 2": (("checkpointVersion",), "2"),
            "checkpointVersion integer": (("checkpointVersion",), 1),
            "trail upper case": (("trail",), self.checkpoint["trail"].upper()),
            "trail 33 characters": (("trail",), self.checkpoint["trail"] + "0"),
            "trail newline": (("trail",), self.checkpoint["trail"] + "\n"),
            "sequence 0": (("sequence",), 0),
            "sequence 2^53-1": (("sequence",), MAX),
            "sequence string": (("sequence",), "1"),
            "trail not a string": (("trail",), 1),
            "recordDigest without sha256": (("recordDigest",), self.checkpoint["recordDigest"][7:]),
            "recordDigest newline": (("recordDigest",), self.checkpoint["recordDigest"] + "\n"),
            "recordDigest not a string": (("recordDigest",), None),
        }
        for required in REQUIRED["checkpoint"]:
            cases["without " + required] = ((required,), DELETE)
        for case, (path, new) in cases.items():
            self.refuses("checkpoint", changed(self.checkpoint, path, new), case)
        self.refuses("checkpoint", [self.checkpoint], "not an object")


class Preparations(SchemaTestCase):
    def setUp(self) -> None:
        super().setUp()
        # valid: version 2, a calculated source; skipped-source-dependency-unavailable: dependencies;
        # the research replay: version 3, receipts, transformation and researchExecution.
        self.calculated = vector("vectors", "valid", "preparation.json")
        self.dependent = vector("vectors", "skipped-source-dependency-unavailable", "preparation.json")
        self.research = vector("research-replay-vector.json")["preparation"]
        self.assertIn("calculation", self.calculated["lineage"][0])
        self.assertIn("dependencies", self.dependent["lineage"][-1])
        self.assertIn("transformation", self.research["lineage"][0])

    def test_values_no_vector_carries_are_accepted(self) -> None:
        calculation = ("lineage", 0, "calculation", "status")
        for status in ("input-missing", "cannot-compute"):
            self.accepts("preparation", changed(self.calculated, calculation, status), "calculation " + status)
        claim = ("outcomes", 1, "claim")
        self.accepts("preparation", changed(self.calculated, claim + ("acquisitionStatus",), "absent"),
                     "acquisitionStatus absent")
        self.accepts("preparation", changed(self.calculated, ("outcomes", 1, "status"), "absent"), "status absent")
        self.accepts("preparation", changed(self.calculated, ("lineage", 0, "status"), "absent"),
                     "lineage status absent")
        self.accepts("preparation", changed(self.calculated, claim + ("evidenceAvailability",),
                                            {"a": "absent", "b": "present", "c": "unknown"}),
                     "every availability")
        application = ("lineage", 0, "transformation", "applications", 0, "state")
        for state in ("missing", "failed"):
            self.accepts("preparation", changed(self.research, application, state), "application " + state)
        self.accepts("preparation", changed(self.research, ("lineage", 0, "transformation", "reconciliation"),
                                            {"mode": "agree"}), "a reconciliation")
        retained = ("lineage", 0, "researchExecution", "retainedBytes")
        entry = self.research["lineage"][0]["researchExecution"]["retainedBytes"][0]
        self.accepts("preparation", changed(self.research, retained, [entry] * 64), "64 retained entries")
        facts = claim + ("facts",)
        self.accepts("preparation", changed(self.calculated, facts, {"n": [MAX, -MAX, 0]}), "integer bounds")
        self.accepts("preparation", changed(self.calculated, ("lineage", 0, "basis"), [""]), "the empty pointer")
        self.accepts("preparation", changed(self.calculated, ("version",), 3), "version 3 without receipts")
        self.accepts("preparation", changed(self.calculated, ("cites", 0, "callIndex"), MAX), "callIndex 2^53-1")
        self.accepts("preparation", changed(self.calculated, ("lineage", 0, "target"), "/"),
                     "a fact target of one character")
        evidence = changed(self.calculated, ("lineage", 0, "kind"), "evidence")
        self.accepts("preparation", changed(evidence, ("lineage", 0, "target"), "f"),
                     "a requirement id of one character")
        last = len(self.dependent["lineage"]) - 1
        dependencies = self.dependent["lineage"][last]["dependencies"]
        self.accepts("preparation", changed(self.dependent, ("lineage", last, "dependencies"), dependencies[:1]),
                     "one dependency")
        settings = ("lineage", 0, "researchExecution", "resolvedSettings")
        for member in ("model", "profile", "version"):
            self.accepts("preparation", changed(self.research, settings + (member,), "m"),
                         "a resolved %s of one character" % member)

    def test_a_preparation_of_another_form_is_refused(self) -> None:
        prepared = self.calculated
        signature = prepared["cites"][0]["signature"]
        cases = {
            "a member it does not list": (("extra",), 1),
            "lineage not an array": (("lineage",), {}),
            "outcomes not an array": (("outcomes",), {}),
            "a case outcome with a member it does not list": (("outcomes", 0, "extra"), 1),
            "a case outcome without claim": (("outcomes", 0, "claim"), DELETE),
            "verifiedAt not a string": (("verifiedAt",), 1760453906),
            "verifiedAt newline": (("verifiedAt",), prepared["verifiedAt"] + "\n"),
            "mappingDigest not a string": (("mappingDigest",), None),
            "mappingDigest newline": (("mappingDigest",), prepared["mappingDigest"] + "\n"),
            "a citation not an object": (("cites", 0), signature),
            "a citation's callIndex a string": (("cites", 0, "callIndex"), "0"),
            "a citation's signature not a string": (("cites", 0, "signature"), 0),
            "a citation's signature newline": (("cites", 0, "signature"), signature + "\n"),
            "an outcome not an object": (("outcomes", 1), "fx"),
            "a claim not an object": (("outcomes", 1, "claim"), None),
            "a lineage entry not an object": (("lineage", 0), "fx"),
            "a lineage entry's basis with a non-string": (("lineage", 0, "basis"), [1]),
            "a lineage entry's basis a lone newline": (("lineage", 0, "basis"), ["\n"]),
            "a calculation not an object": (("lineage", 0, "calculation"), "computed"),
            "a calculator not an object": (("lineage", 0, "calculation", "calculator"), "fx"),
            "a calculator without name": (("lineage", 0, "calculation", "calculator", "name"), DELETE),
            "a calculation input not an object": (("lineage", 0, "calculation", "inputs", 0), "fx"),
            "a calculation input without name": (("lineage", 0, "calculation", "inputs", 0, "name"), DELETE),
            "a calculation input without parameter": (("lineage", 0, "calculation", "inputs", 0, "parameter"),
                                                      DELETE),
            "a calculation input without source": (("lineage", 0, "calculation", "inputs", 0, "source"), DELETE),
            "a calculation's asOf an array": (("lineage", 0, "calculation", "asOf"), []),
            "version 1": (("version",), 1),
            "version 4": (("version",), 4),
            "version string": (("version",), "2"),
            "verifiedAt fraction": (("verifiedAt",), "2026-10-14T14:58:26.0Z"),
            "verifiedAt no such day": (("verifiedAt",), "2026-04-31T00:00:00Z"),
            "mappingDigest upper case": (("mappingDigest",), prepared["mappingDigest"].upper()),
            "verification another account": (("verification",), "verified acquisitions"),
            "cites not an array": (("cites",), {}),
            "a citation with a fourth member": (("cites", 0, "extra"), 1),
            "a citation without signature": (("cites", 0, "signature"), DELETE),
            "a citation without callIndex": (("cites", 0, "callIndex"), DELETE),
            "a citation without sessionId": (("cites", 0, "sessionId"), DELETE),
            "a citation's callIndex -1": (("cites", 0, "callIndex"), -1),
            "a citation's sessionId null": (("cites", 0, "sessionId"), None),
            "a citation's signature upper case": (("cites", 0, "signature"), signature.upper()),
            "no outcome": (("outcomes",), []),
            "a first outcome not the case": (("outcomes", 0, "name"), "fx"),
            "an outcome with a member it does not list": (("outcomes", 1, "extra"), 1),
            "an outcome's name not a string": (("outcomes", 1, "name"), 1),
            "an outcome's parameters without runAt": (("outcomes", 1, "parameters", "runAt"), DELETE),
            "an outcome's runAt not an instant": (("outcomes", 1, "parameters", "runAt"), "now"),
            "an outcome's parameters an array": (("outcomes", 1, "parameters"), []),
            "an outcome's status another": (("outcomes", 1, "status"), "missing"),
            "an outcome's reason not a string": (("outcomes", 1, "reason"), None),
            "a claim with a member it does not list": (("outcomes", 1, "claim", "extra"), 1),
            "a claim's facts an array": (("outcomes", 1, "claim", "facts"), []),
            "a claim's acquisitionStatus another": (("outcomes", 1, "claim", "acquisitionStatus"), "found"),
            "a claim's availability another": (("outcomes", 1, "claim", "evidenceAvailability"), {"a": "maybe"}),
            "a claim's availability for an empty id": (("outcomes", 1, "claim", "evidenceAvailability"),
                                                        {"": "present"}),
            "a claim's evidenceAvailability an array": (("outcomes", 1, "claim", "evidenceAvailability"), []),
            "a claim's reason not a string": (("outcomes", 1, "claim", "reason"), 1),
            "a claim's basis repeating a pointer": (("outcomes", 1, "claim", "basis"), ["/a", "/a"]),
            "a claim's basis not a pointer": (("outcomes", 1, "claim", "basis"), ["a"]),
            "a claim's basis with an escape ~2": (("outcomes", 1, "claim", "basis"), ["/a~2"]),
            "a claim's basis not an array": (("outcomes", 1, "claim", "basis"), "/a"),
            "a fraction in a fact": (("outcomes", 1, "claim", "facts"), {"n": 1.5}),
            "an integer past 2^53-1 in a fact": (("outcomes", 1, "claim", "facts"), {"n": [MAX + 1]}),
            "an integer below -(2^53-1) in a parameter": (("outcomes", 1, "parameters", "n"), -MAX - 1),
            "a fraction in arguments": (("outcomes", 1, "arguments"), {"n": {"m": [0.5]}}),
            "a lineage entry with a member it does not list": (("lineage", 0, "extra"), 1),
            "a lineage entry's source not a string": (("lineage", 0, "source"), 1),
            "a lineage entry's kind another": (("lineage", 0, "kind"), "value"),
            "a fact target not a pointer": (("lineage", 0, "target"), "fact"),
            "a fact target the empty pointer": (("lineage", 0, "target"), ""),
            "a lineage entry's class another": (("lineage", 0, "class"), "computed"),
            "a lineage entry's generatedInfluence a string": (("lineage", 0, "generatedInfluence"), "false"),
            "a lineage entry's present a string": (("lineage", 0, "present"), "true"),
            "a lineage entry's status another": (("lineage", 0, "status"), "found"),
            "a lineage entry's reason not a string": (("lineage", 0, "reason"), None),
            "a lineage entry's basis not a pointer": (("lineage", 0, "basis"), ["x"]),
            "a lineage entry's readDigest upper case": (("lineage", 0, "readDigest"),
                                                         prepared["lineage"][0]["readDigest"].upper()),
            "candidateFrom empty": (("lineage", 0, "candidateFrom"), []),
            "candidateFrom repeating a pointer": (("lineage", 0, "candidateFrom"), ["/a", "/a"]),
            "candidateFrom not a pointer": (("lineage", 0, "candidateFrom"), ["a"]),
            "a receipt citation with a fourth member": (("lineage", 0, "receipt", "extra"), 1),
            "a calculation with a member it does not list": (("lineage", 0, "calculation", "extra"), 1),
            "a calculation's status another": (("lineage", 0, "calculation", "status"), "stale"),
            "a calculator with a third member": (("lineage", 0, "calculation", "calculator", "extra"), 1),
            "a calculator without version": (("lineage", 0, "calculation", "calculator", "version"), DELETE),
            "a calculator's name not a string": (("lineage", 0, "calculation", "calculator", "name"), 1),
            "a calculator's version not a string": (("lineage", 0, "calculation", "calculator", "version"), 1),
            "a calculation input with a fifth member": (("lineage", 0, "calculation", "inputs", 0, "extra"), 1),
            "a calculation input without pointer": (("lineage", 0, "calculation", "inputs", 0, "pointer"), DELETE),
            "a calculation input's pointer not a pointer": (("lineage", 0, "calculation", "inputs", 0,
                                                             "pointer"), "x"),
            "a calculation input's name not a string": (("lineage", 0, "calculation", "inputs", 0, "name"), 1),
            "a calculation input's parameter not a string": (("lineage", 0, "calculation", "inputs", 0,
                                                              "parameter"), 1),
            "a calculation input's source not a string": (("lineage", 0, "calculation", "inputs", 0,
                                                           "source"), 1),
            "a calculation's asOf not an instant": (("lineage", 0, "calculation", "asOf"), {"t": "today"}),
            "a calculation's inputs an object": (("lineage", 0, "calculation", "inputs"), {}),
        }
        for required in REQUIRED["preparation"]:
            cases["without " + required] = ((required,), DELETE)
        for required in REQUIRED["outcome"]:
            cases["an outcome without " + required] = (("outcomes", 1, required), DELETE)
        for required in REQUIRED["claim"]:
            cases["a claim without " + required] = (("outcomes", 1, "claim", required), DELETE)
        for required in REQUIRED["lineageEntry"]:
            cases["a lineage entry without " + required] = (("lineage", 0, required), DELETE)
        for required in REQUIRED["calculation"]:
            cases["a calculation without " + required] = (("lineage", 0, "calculation", required), DELETE)
        for case, (path, new) in cases.items():
            self.refuses("preparation", changed(prepared, path, new), case)
        self.refuses("preparation", changed(prepared, ("lineage", 0, "receipts"), []),
                     "receipts in version 2")
        evidence = changed(changed(prepared, ("lineage", 0, "kind"), "evidence"), ("lineage", 0, "target"), "form")
        self.accepts("preparation", evidence, "an evidence target that is not a pointer")
        self.refuses("preparation", changed(evidence, ("lineage", 0, "target"), ""), "an empty requirement")
        self.refuses("preparation", changed(evidence, ("lineage", 0, "target"), 1), "a requirement not a string")
        self.refuses("preparation", [prepared], "not an object")

    def test_dependencies_of_another_form_are_refused(self) -> None:
        last = len(self.dependent["lineage"]) - 1
        dependency = ("lineage", last, "dependencies", 0)
        cases = {
            "dependencies empty": (("lineage", last, "dependencies"), []),
            "dependencies an object": (("lineage", last, "dependencies"), {}),
            "a dependency not an object": (dependency, "sponsor"),
            "a dependency with a fourth member": (dependency + ("extra",), 1),
            "a dependency without parameter": (dependency + ("parameter",), DELETE),
            "a dependency without source": (dependency + ("source",), DELETE),
            "a dependency without pointer": (dependency + ("pointer",), DELETE),
            "a dependency's pointer not a pointer": (dependency + ("pointer",), "x"),
            "a dependency's parameter not a string": (dependency + ("parameter",), 1),
            "a dependency's source not a string": (dependency + ("source",), 1),
        }
        for case, (path, new) in cases.items():
            self.refuses("preparation", changed(self.dependent, path, new), case)

    def test_research_lineage_of_another_form_is_refused(self) -> None:
        transformation = ("lineage", 0, "transformation")
        application = transformation + ("applications", 0)
        execution = ("lineage", 0, "researchExecution")
        settings = execution + ("resolvedSettings",)
        retained = execution + ("retainedBytes",)
        entry = self.research["lineage"][0]["researchExecution"]["retainedBytes"][0]
        cases = {
            "receipts not an array": (("lineage", 0, "receipts"), {}),
            "a receipts citation with a fourth member": (("lineage", 0, "receipts"),
                                                         [dict(self.calculated["cites"][0], extra=1)]),
            "a transformation not an object": (transformation, []),
            "an application not an object": (application, "source"),
            "a researchExecution not an object": (execution, []),
            "resolved settings not an object": (settings, "default"),
            "resolved settings' model not a string": (settings + ("model",), 1),
            "resolved settings' profile not a string": (settings + ("profile",), 1),
            "resolved settings' version not a string": (settings + ("version",), 1),
            "a retained entry not an object": (retained + (0,), entry["digest"]),
            "a transformation with a member it does not list": (transformation + ("extra",), 1),
            "a transformation without applications": (transformation + ("applications",), DELETE),
            "a transformation without findings": (transformation + ("findings",), DELETE),
            "a transformation's findings an object": (transformation + ("findings",), {}),
            "a transformation's applications an object": (transformation + ("applications",), {}),
            "a transformation's reconciliation an array": (transformation + ("reconciliation",), []),
            "an application without id": (application + ("id",), DELETE),
            "an application without source": (application + ("source",), DELETE),
            "an application without state": (application + ("state",), DELETE),
            "an application's id not a string": (application + ("id",), 1),
            "an application's source not a pointer": (application + ("source",), "results"),
            "an application's state another": (application + ("state",), "converted"),
            "a researchExecution with a member it does not list": (execution + ("extra",), 1),
            "a researchExecution without resolvedSettings": (execution + ("resolvedSettings",), DELETE),
            "a researchExecution without retainedBytes": (execution + ("retainedBytes",), DELETE),
            "resolved settings with a member they do not list": (settings + ("extra",), 1),
            "resolved settings without settings": (settings + ("settings",), DELETE),
            "resolved settings' settings an array": (settings + ("settings",), []),
            "resolved settings' model empty": (settings + ("model",), ""),
            "resolved settings' profile empty": (settings + ("profile",), ""),
            "resolved settings' version empty": (settings + ("version",), ""),
            "resolved settings without model": (settings + ("model",), DELETE),
            "resolved settings without profile": (settings + ("profile",), DELETE),
            "resolved settings without version": (settings + ("version",), DELETE),
            "65 retained entries": (retained, [entry] * 65),
            "a retained entry with its base64": (retained + (0, "base64"), "e30="),
            "a retained entry without digest": (retained + (0, "digest"), DELETE),
            "a retained entry without mediaType": (retained + (0, "mediaType"), DELETE),
            "a retained entry's mediaType not a string": (retained + (0, "mediaType"), 1),
            "a retained entry's digest upper case": (retained + (0, "digest"), entry["digest"].upper()),
            "retainedBytes an object": (retained, {}),
        }
        for case, (path, new) in cases.items():
            self.refuses("preparation", changed(self.research, path, new), case)


class Recordings(SchemaTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.export = vector("vectors", "valid", "run.json")
        self.legacy = vector("vectors", "unbound-record", "run.json")
        self.assertEqual((5, 2), (self.export["version"], self.legacy["version"]))

    def test_both_evaluator_versions_and_both_export_forms_are_accepted(self) -> None:
        later = vector("vectors-0.3.0", "valid", "run.json")
        self.accepts("export", later, "0.3.0")
        self.accepts("export", self.legacy, "an export of version 2")
        self.accepts("export", changed(self.export, ("version",), 3), "an export of version 3")
        self.accepts("export", changed(self.export, ("run", "auditBytes"), "YQ=="), "two padding characters")
        self.accepts("export", changed(self.export, ("run", "auditBytes"), "YWI="), "one padding character")
        self.accepts("export", changed(self.export, ("run", "auditBytes"), ""), "no bytes")
        self.accepts("export", changed(self.export, ("run", "audit", "Binding\n"), 1),
                     "an audit member that is not binding but for case")

    def test_a_recording_of_another_form_is_refused(self) -> None:
        cases = {
            "version not an integer": (("version",), "5"),
            "without version": (("version",), DELETE),
            "without release": (("release",), DELETE),
            "without run": (("run",), DELETE),
            "release not an object": (("release",), "{}"),
            "release.pack an object": (("release", "pack"), {"specVersion": "0.2.0-draft"}),
            "without release.pack": (("release", "pack"), DELETE),
            "without run.input": (("run", "input"), DELETE),
            "run.input not an object": (("run", "input"), []),
            "without run.input.preparation": (("run", "input", "preparation"), DELETE),
            "run.input.preparation of another form": (("run", "input", "preparation", "version"), 4),
            "without run.result": (("run", "result"), DELETE),
            "run.result not an object": (("run", "result"), "0.2.0-draft"),
            "the declared version disagrees with the audit": (("run", "result", "evaluatorSpecVersion"), "0.3.0"),
            "without run.result.evaluatorSpecVersion": (("run", "result", "evaluatorSpecVersion"), DELETE),
            "an evaluator version not read": (("run", "result", "evaluatorSpecVersion"), "0.4.0"),
            "without run.audit": (("run", "audit"), DELETE),
            "run.audit not an object": (("run", "audit"), []),
            "run.audit without inputs": (("run", "audit", "inputs"), DELETE),
            "run.audit's inputs an array": (("run", "audit", "inputs"), []),
            "run.audit with a binding but for case": (("run", "audit", "Binding"), None),
            "run.audit without evaluatorSpecVersion": (("run", "audit", "evaluatorSpecVersion"), DELETE),
            "run.audit without pack": (("run", "audit", "pack"), DELETE),
            "run.audit.pack not an object": (("run", "audit", "pack"), "0.2.0-draft"),
            "run.audit.pack without specVersion": (("run", "audit", "pack", "specVersion"), DELETE),
            "the audit's evaluator version disagrees": (("run", "audit", "evaluatorSpecVersion"), "0.3.0"),
            "the audit's pack version disagrees": (("run", "audit", "pack", "specVersion"), "0.3.0"),
            "an export of version 5 without audit bytes": (("run", "auditBytes"), DELETE),
            "audit bytes not base64": (("run", "auditBytes"), "e30"),
            "audit bytes in URL-safe base64": (("run", "auditBytes"), "-_8="),
            "audit bytes with a newline": (("run", "auditBytes"), "YQ==\n"),
            "audit bytes not a string": (("run", "auditBytes"), None),
        }
        for case, (path, new) in cases.items():
            self.refuses("export", changed(self.export, path, new), case)
        self.refuses("export", changed(self.legacy, ("run", "auditBytes"), "e30="),
                     "an export of version 2 with audit bytes")
        self.refuses("export", changed(self.legacy, ("version",), DELETE), "an export without audit bytes or version")
        self.refuses("export", [self.export], "not an object")
        later = vector("vectors-0.3.0", "valid", "run.json")
        disagreements = {
            "the declared version disagrees": ("run", "result", "evaluatorSpecVersion"),
            "the audit's evaluator version disagrees": ("run", "audit", "evaluatorSpecVersion"),
            "the audit's pack version disagrees": ("run", "audit", "pack", "specVersion"),
        }
        for case, path in disagreements.items():
            self.refuses("export", changed(later, path, "0.2.0-draft"), "0.3.0: " + case)


if __name__ == "__main__":
    unittest.main()

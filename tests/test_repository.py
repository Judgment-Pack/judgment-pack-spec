from __future__ import annotations

import json
import re
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE = ROOT / "conformance"
SCHEMA_PATH = ROOT / "schema" / "judgment-pack-core.schema.json"
MANIFEST_PATH = CONFORMANCE / "manifest.json"
MANIFEST_SCHEMA_PATH = CONFORMANCE / "manifest.schema.json"
EVALUATION = CONFORMANCE / "evaluation"
EVALUATION_MANIFEST_PATH = EVALUATION / "manifest.json"
EVALUATION_MANIFEST_SCHEMA_PATH = EVALUATION / "manifest.schema.json"
SPEC_VERSION = "0.2.0-draft"
PREVIOUS_SPEC_VERSION = "0.1.0-draft"
SCHEMA_ID = f"https://judgmentpack.org/schema/{SPEC_VERSION}/judgment-pack-core.schema.json"
PREVIOUS_SCHEMA_PATH = (
    ROOT / "schema" / f"judgment-pack-core-{PREVIOUS_SPEC_VERSION}.schema.json"
)
PREVIOUS_SCHEMA_ID = (
    f"https://judgmentpack.org/schema/{PREVIOUS_SPEC_VERSION}/judgment-pack-core.schema.json"
)
PREVIOUS_MANIFEST_SCHEMA_PATH = (
    ROOT / "schema" / f"conformance-manifest-{PREVIOUS_SPEC_VERSION}.schema.json"
)
PREVIOUS_MANIFEST_SCHEMA_ID = (
    f"https://judgmentpack.org/schema/{PREVIOUS_SPEC_VERSION}"
    "/conformance/manifest.schema.json"
)
# §8.3: the reason vocabulary a disposition may carry.
REASONS = {
    "not-applicable",
    "missing-required-evidence",
    "unknown",
    "conflict",
    "no-match",
    "exception-escalation",
}


class DuplicateMemberError(ValueError):
    def __init__(self, member: str):
        super().__init__(f"duplicate object member: {member}")
        self.member = member


@dataclass(frozen=True)
class Diagnostic:
    code: str
    path: str
    message: str


def strict_json_loads(text: str) -> Any:
    def object_from_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise DuplicateMemberError(key)
            value[key] = item
        return value

    return json.loads(text, object_pairs_hook=object_from_pairs)


def pointer(parts: Iterable[Any]) -> str:
    encoded = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "" if not encoded else "/" + "/".join(encoded)


def walk_schema_errors(error: Any) -> Iterable[Any]:
    yield error
    for child in error.context:
        yield from walk_schema_errors(child)


def schema_diagnostic(error: Any) -> Diagnostic:
    validator = str(error.validator)
    schema_path = [str(part) for part in error.absolute_schema_path]
    instance_path = list(error.absolute_path)

    if validator == "required":
        missing = re.match(r"^'([^']+)' is a required property$", error.message)
        if missing:
            instance_path.append(missing.group(1))
        if "exceptions" in schema_path and "allOf" in schema_path:
            code = "JPS-STRUCTURE-EXCEPTION-SHAPE"
        else:
            code = "JPS-STRUCTURE-REQUIRED-MEMBER"
    elif validator == "additionalProperties":
        unexpected = re.search(r"\('([^']+)' (?:was|were) unexpected\)", error.message)
        if unexpected:
            instance_path.append(unexpected.group(1))
        code = "JPS-STRUCTURE-UNKNOWN-MEMBER"
    elif validator == "format":
        suffix = str(error.validator_value).replace("-", "-").upper()
        code = f"JPS-STRUCTURE-FORMAT-{suffix}"
    elif validator == "pattern":
        pattern = error.validator_value
        if pattern == "^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$":
            code = "JPS-STRUCTURE-LOCAL-ID"
        elif pattern.startswith("^(0|[1-9][0-9]*)"):
            code = "JPS-STRUCTURE-PACK-VERSION"
        elif pattern == "^(?:/(?:[^~/]|~0|~1)*)*$":
            code = "JPS-STRUCTURE-FACT-PATH"
        elif pattern == "^-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?$":
            code = "JPS-STRUCTURE-DECIMAL-OPERAND"
        elif "org\\.judgmentpack" in pattern:
            code = "JPS-STRUCTURE-EXTENSION-NAME"
            if isinstance(error.instance, str):
                instance_path.append(error.instance)
        else:
            code = "JPS-STRUCTURE-PATTERN"
    elif validator == "minItems":
        if instance_path[-1:] == ["conditions"]:
            code = "JPS-STRUCTURE-CONDITION-ARITY"
        elif instance_path[-1:] == ["triggers"]:
            code = "JPS-STRUCTURE-ESCALATION-TRIGGERS"
        else:
            code = "JPS-STRUCTURE-COLLECTION-ARITY"
    elif validator == "type" and error.validator_value == "array":
        code = "JPS-STRUCTURE-IN-OPERAND"
    elif validator == "const" and instance_path == ["specVersion"]:
        code = "JPS-STRUCTURE-SPEC-VERSION"
    elif validator in {"oneOf", "const", "enum"} and "condition" in "/".join(schema_path):
        code = "JPS-STRUCTURE-CONDITION-SHAPE"
    elif validator in {"not", "allOf"} and "exceptions" in schema_path:
        code = "JPS-STRUCTURE-EXCEPTION-SHAPE"
    else:
        suffix = validator.replace("_", "-").upper()
        code = f"JPS-STRUCTURE-{suffix}"
    return Diagnostic(code, pointer(instance_path), error.message)


def structural_diagnostics(validator: Draft202012Validator, value: Any) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    seen: set[tuple[str, str, str]] = set()
    for top_level in validator.iter_errors(value):
        for error in walk_schema_errors(top_level):
            item = schema_diagnostic(error)
            identity = (item.code, item.path, item.message)
            if identity not in seen:
                seen.add(identity)
                diagnostics.append(item)
    return diagnostics


def condition_references(condition: dict[str, Any], base: list[Any]) -> Iterable[tuple[str, str]]:
    op = condition.get("op")
    if op == "evidence-present":
        yield condition["evidenceRequirement"], pointer(base + ["evidenceRequirement"])
    elif op in {"all", "any"}:
        for index, child in enumerate(condition.get("conditions", [])):
            yield from condition_references(child, base + ["conditions", index])
    elif op == "not" and isinstance(condition.get("condition"), dict):
        yield from condition_references(condition["condition"], base + ["condition"])


def duplicate_id_diagnostics(value: dict[str, Any], collection: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    seen: set[str] = set()
    for index, item in enumerate(value.get(collection, [])):
        local_id = item["id"]
        if local_id in seen:
            diagnostics.append(
                Diagnostic(
                    "JPS-SEMANTIC-DUPLICATE-ID",
                    pointer([collection, index, "id"]),
                    f"duplicate {collection} id: {local_id}",
                )
            )
        seen.add(local_id)
    return diagnostics


def extension_names(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        extensions = value.get("extensions")
        if isinstance(extensions, dict):
            names.update(extensions)
        for child in value.values():
            names.update(extension_names(child))
    elif isinstance(value, list):
        for child in value:
            names.update(extension_names(child))
    return names


def semantic_diagnostics(value: dict[str, Any]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    collections = ("outcomes", "rules", "evidenceRequirements", "sources", "exceptions")
    for collection in collections:
        diagnostics.extend(duplicate_id_diagnostics(value, collection))

    outcomes = {item["id"] for item in value.get("outcomes", [])}
    rules = {item["id"] for item in value.get("rules", [])}
    evidence = {item["id"] for item in value.get("evidenceRequirements", [])}
    sources = {item["id"] for item in value.get("sources", [])}

    def unresolved(
        reference: str, target: set[str], path: list[Any], kind: str, code: str
    ) -> None:
        if reference not in target:
            diagnostics.append(
                Diagnostic(
                    code,
                    pointer(path),
                    f"{kind} reference does not resolve: {reference}",
                )
            )

    for index, rule in enumerate(value.get("rules", [])):
        unresolved(
            rule["outcome"],
            outcomes,
            ["rules", index, "outcome"],
            "outcome",
            "JPS-SEMANTIC-UNRESOLVED-OUTCOME",
        )
        for ref_index, reference in enumerate(rule.get("evidenceRequirementRefs", [])):
            unresolved(
                reference,
                evidence,
                ["rules", index, "evidenceRequirementRefs", ref_index],
                "evidence requirement",
                "JPS-SEMANTIC-UNRESOLVED-EVIDENCE",
            )
        for ref_index, reference in enumerate(rule.get("sourceRefs", [])):
            unresolved(
                reference,
                sources,
                ["rules", index, "sourceRefs", ref_index],
                "source",
                "JPS-SEMANTIC-UNRESOLVED-SOURCE",
            )
        for reference, ref_path in condition_references(rule["when"], ["rules", index, "when"]):
            if reference not in evidence:
                diagnostics.append(
                    Diagnostic(
                        "JPS-SEMANTIC-UNRESOLVED-EVIDENCE",
                        ref_path,
                        f"evidence requirement reference does not resolve: {reference}",
                    )
                )

    fallback = value.get("fallbackOutcome")
    if fallback is not None:
        unresolved(
            fallback,
            outcomes,
            ["fallbackOutcome"],
            "outcome",
            "JPS-SEMANTIC-UNRESOLVED-OUTCOME",
        )

    applicability = value.get("applicability")
    if isinstance(applicability, dict):
        for reference, ref_path in condition_references(applicability, ["applicability"]):
            if reference not in evidence:
                diagnostics.append(
                    Diagnostic(
                        "JPS-SEMANTIC-UNRESOLVED-EVIDENCE",
                        ref_path,
                        f"evidence requirement reference does not resolve: {reference}",
                    )
                )

    for index, exception in enumerate(value.get("exceptions", [])):
        if "targetRule" in exception:
            unresolved(
                exception["targetRule"],
                rules,
                ["exceptions", index, "targetRule"],
                "rule",
                "JPS-SEMANTIC-UNRESOLVED-RULE",
            )
        if "outcome" in exception:
            unresolved(
                exception["outcome"],
                outcomes,
                ["exceptions", index, "outcome"],
                "outcome",
                "JPS-SEMANTIC-UNRESOLVED-OUTCOME",
            )
        for ref_index, reference in enumerate(exception.get("sourceRefs", [])):
            unresolved(
                reference,
                sources,
                ["exceptions", index, "sourceRefs", ref_index],
                "source",
                "JPS-SEMANTIC-UNRESOLVED-SOURCE",
            )
        for reference, ref_path in condition_references(
            exception["when"], ["exceptions", index, "when"]
        ):
            if reference not in evidence:
                diagnostics.append(
                    Diagnostic(
                        "JPS-SEMANTIC-UNRESOLVED-EVIDENCE",
                        ref_path,
                        f"evidence requirement reference does not resolve: {reference}",
                    )
                )

    declared_required = value.get("metadata", {}).get("requiredExtensions", [])
    used_extensions = extension_names(value)
    for index, required in enumerate(declared_required):
        if required not in used_extensions:
            diagnostics.append(
                Diagnostic(
                    "JPS-SEMANTIC-MISSING-REQUIRED-EXTENSION",
                    pointer(["metadata", "requiredExtensions", index]),
                    f"required extension has no value in the document: {required}",
                )
            )
    return diagnostics


def unsupported_diagnostics(
    value: dict[str, Any], supported_extensions: Iterable[str]
) -> list[Diagnostic]:
    supported = set(supported_extensions)
    diagnostics: list[Diagnostic] = []
    for index, required in enumerate(value.get("metadata", {}).get("requiredExtensions", [])):
        if required not in supported:
            diagnostics.append(
                Diagnostic(
                    "JPS-CAPABILITY-REQUIRED-EXTENSION",
                    pointer(["metadata", "requiredExtensions", index]),
                    f"required extension is not supported: {required}",
                )
            )
    return diagnostics


def evaluate_case(
    path: Path,
    validator: Draft202012Validator,
    supported_extensions: Iterable[str],
) -> tuple[str, list[Diagnostic]]:
    try:
        value = strict_json_loads(path.read_text(encoding="utf-8"))
    except DuplicateMemberError as error:
        return "invalid", [
            Diagnostic("JPS-CARRIER-DUPLICATE-MEMBER", pointer([error.member]), str(error))
        ]
    except (UnicodeError, json.JSONDecodeError) as error:
        return "invalid", [Diagnostic("JPS-CARRIER-INVALID-JSON", "", str(error))]

    diagnostics = structural_diagnostics(validator, value)
    if diagnostics:
        return "invalid", diagnostics

    diagnostics = semantic_diagnostics(value)
    if diagnostics:
        return "invalid", diagnostics

    diagnostics = unsupported_diagnostics(value, supported_extensions)
    if diagnostics:
        return "unsupported", diagnostics
    return "valid", []


class RepositoryConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = strict_json_loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.manifest_schema = strict_json_loads(
            MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        cls.manifest = strict_json_loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())

    def test_pointer_escaping(self) -> None:
        cases = [
            ([], ""),
            (["rules", 0, "when"], "/rules/0/when"),
            (["a/b", "c~d"], "/a~1b/c~0d"),
        ]

        for parts, expected in cases:
            with self.subTest(parts=parts):
                self.assertEqual(pointer(parts), expected)

    def test_schemas_are_valid_draft_2020_12(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        Draft202012Validator.check_schema(self.manifest_schema)
        self.assertEqual(self.schema["$id"], SCHEMA_ID)

    def test_manifest_matches_its_schema(self) -> None:
        validator = Draft202012Validator(
            self.manifest_schema, format_checker=FormatChecker()
        )
        errors = sorted(validator.iter_errors(self.manifest), key=lambda item: list(item.path))
        self.assertEqual([], [error.message for error in errors])
        self.assertEqual(self.manifest["suiteVersion"], SPEC_VERSION)
        self.assertEqual(self.manifest["specVersion"], SPEC_VERSION)
        self.assertTrue(self.manifest["validationProfile"]["formatAssertionRequired"])
        self.assertTrue(self.manifest["validationProfile"]["rejectDuplicateObjectMembers"])

    def test_manifest_covers_every_fixture_once(self) -> None:
        listed = [case["path"] for case in self.manifest["cases"]]
        case_ids = [case["id"] for case in self.manifest["cases"]]
        self.assertEqual(len(listed), len(set(listed)), "manifest contains duplicate paths")
        self.assertEqual(len(case_ids), len(set(case_ids)), "manifest contains duplicate case ids")
        for case in self.manifest["cases"]:
            directory = Path(case["path"]).parts[0]
            if directory == "valid":
                self.assertEqual("semantic", case["layer"])
                self.assertEqual("valid", case["expectedResult"])
            else:
                self.assertEqual(case["layer"], directory)
        fixture_paths = sorted(
            str(path.relative_to(CONFORMANCE))
            for directory in ("carrier", "structural", "semantic", "valid")
            for path in (CONFORMANCE / directory).glob("*.json")
        )
        self.assertEqual(sorted(listed), fixture_paths)

    def test_conformance_cases(self) -> None:
        for case in self.manifest["cases"]:
            with self.subTest(case=case["id"]):
                case_path = (CONFORMANCE / case["path"]).resolve()
                try:
                    case_path.relative_to(CONFORMANCE.resolve())
                except ValueError:
                    self.fail(f"case path escapes conformance directory: {case['path']}")
                actual, diagnostics = evaluate_case(
                    case_path, self.validator, case.get("supportedExtensions", [])
                )
                self.assertEqual(
                    case["expectedResult"],
                    actual,
                    "\n".join(f"{item.code} {item.path}: {item.message}" for item in diagnostics),
                )
                expected = case["expectedDiagnostic"]
                if expected is None:
                    self.assertEqual([], diagnostics)
                else:
                    matches = [
                        item
                        for item in diagnostics
                        if item.code == expected["code"] and item.path == expected["path"]
                    ]
                    self.assertTrue(
                        matches,
                        f"expected {expected}; got "
                        + repr([(item.code, item.path) for item in diagnostics]),
                    )

    def test_examples_are_structurally_and_semantically_valid(self) -> None:
        for example_path in sorted((ROOT / "examples").glob("*.json")):
            with self.subTest(example=example_path.name):
                value = strict_json_loads(example_path.read_text(encoding="utf-8"))
                self.assertEqual(value["specVersion"], SPEC_VERSION)
                self.assertEqual([], structural_diagnostics(self.validator, value))
                self.assertEqual([], semantic_diagnostics(value))

    def test_canonical_example_and_fixture_do_not_drift(self) -> None:
        example = (ROOT / "examples" / "minimal-expense-approval.json").read_bytes()
        fixture = (CONFORMANCE / "valid" / "minimal-expense-approval.json").read_bytes()
        self.assertEqual(example, fixture)

    def test_superseded_schema_stays_published_for_its_own_version(self) -> None:
        # A 0.1.0-draft pack is unchanged in representation and document-conformance meaning (Core §11)
        # but must be re-declared to pass the current schema, so the older schema stays available at its
        # own exact version for a document that keeps the older value.
        previous = strict_json_loads(PREVIOUS_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(previous)
        self.assertEqual(previous["$id"], PREVIOUS_SCHEMA_ID)
        self.assertEqual(
            previous["properties"]["specVersion"]["const"], PREVIOUS_SPEC_VERSION
        )
        self.assertEqual(self.schema["properties"]["specVersion"]["const"], SPEC_VERSION)

        # The document-conformance manifest schema was published at its own 0.1.0-draft identifier too,
        # so a manifest that still cites it keeps resolving.
        previous_manifest = strict_json_loads(
            PREVIOUS_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(previous_manifest)
        self.assertEqual(previous_manifest["$id"], PREVIOUS_MANIFEST_SCHEMA_ID)
        self.assertEqual(
            previous_manifest["properties"]["specVersion"]["const"], PREVIOUS_SPEC_VERSION
        )

    def test_evaluation_manifest_matches_its_schema(self) -> None:
        schema = strict_json_loads(
            EVALUATION_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(schema)
        manifest = strict_json_loads(EVALUATION_MANIFEST_PATH.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        errors = sorted(validator.iter_errors(manifest), key=lambda item: list(item.path))
        self.assertEqual([], [error.message for error in errors])
        self.assertEqual(manifest["suiteVersion"], SPEC_VERSION)
        self.assertEqual(manifest["specVersion"], SPEC_VERSION)
        self.assertEqual(manifest["label"], "seed")
        ids = [case["id"] for case in manifest["cases"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate evaluation case ids")

    def test_evaluation_cases_are_well_formed_against_their_pack(self) -> None:
        # Carrier well-formedness only: the specification repository owns no evaluator, so these
        # checks verify that each case could be run, never that a disposition is the right one.
        manifest = strict_json_loads(EVALUATION_MANIFEST_PATH.read_text(encoding="utf-8"))
        # §8.2 makes the pack input a semantically conforming document, so a pack fixture is required to
        # conform — except for a fixture whose whole point is the §8.4 `pack-not-conformant` error, which
        # requires the opposite. The check is therefore conditional on what the case expects rather than
        # dropped: a fixture that quietly became conforming would make such a row unrunnable too.
        non_conformant_packs = {
            case["pack"]
            for case in manifest["cases"]
            if case.get("expectedErrorClass") == "pack-not-conformant"
        }
        packs: dict[str, Any] = {}
        for case in manifest["cases"]:
            with self.subTest(case=case["id"]):
                pack_path = (EVALUATION / case["pack"]).resolve()
                try:
                    pack_path.relative_to(EVALUATION.resolve())
                except ValueError:
                    self.fail(f"pack path escapes the evaluation corpus: {case['pack']}")
                self.assertTrue(pack_path.is_file(), f"missing pack: {case['pack']}")
                expects_non_conformant_pack = case["pack"] in non_conformant_packs
                if expects_non_conformant_pack:
                    self.assertNotIn(
                        "expectedDisposition",
                        case,
                        "a pack another case expects to fail §3.3 cannot also yield a disposition",
                    )
                if case["pack"] not in packs:
                    pack = strict_json_loads(pack_path.read_text(encoding="utf-8"))
                    diagnostics = structural_diagnostics(
                        self.validator, pack
                    ) + semantic_diagnostics(pack)
                    if expects_non_conformant_pack:
                        self.assertNotEqual(
                            [],
                            diagnostics,
                            f"{case['pack']} conforms, so no case can expect pack-not-conformant",
                        )
                    else:
                        self.assertEqual(pack["specVersion"], SPEC_VERSION)
                        self.assertEqual([], diagnostics)
                    packs[case["pack"]] = pack
                pack = packs[case["pack"]]

                declared_evidence = {
                    item["id"] for item in pack.get("evidenceRequirements", [])
                }
                for key, value in (case.get("evidenceAvailability") or {}).items():
                    self.assertIn(
                        key,
                        declared_evidence,
                        f"undeclared evidence key {key}: §8.2 makes that an evaluation error",
                    )
                    self.assertIn(value, {"present", "absent", "unknown"})

                self.assertEqual(
                    "expectedDisposition" in case,
                    "expectedErrorClass" not in case,
                    "a case states exactly one of expectedDisposition and expectedErrorClass",
                )
                disposition = case.get("expectedDisposition")
                if disposition is None:
                    continue

                reasons = disposition["reasons"]
                self.assertEqual(reasons, sorted(set(reasons)), "reasons are a sorted set")
                self.assertTrue(set(reasons) <= REASONS, f"unknown reason in {reasons}")
                kind = disposition["kind"]
                if kind == "outcome":
                    self.assertEqual([], reasons, "an outcome disposition carries no reason")
                    outcomes = {item["id"] for item in pack["outcomes"]}
                    self.assertIn(disposition["outcomeId"], outcomes)
                else:
                    self.assertNotIn("outcomeId", disposition)
                    self.assertTrue(reasons, f"{kind} carries at least one reason")
                if kind == "not-applicable":
                    self.assertEqual(["not-applicable"], reasons)

                handoff = disposition["handoff"]
                triggers = set(pack.get("escalation", {}).get("triggers", []))
                if handoff["state"] == "requested":
                    triggered = handoff["triggeredBy"]
                    self.assertEqual(triggered, sorted(set(triggered)))
                    self.assertTrue(triggered, "a requested handoff names what triggered it")
                    self.assertTrue(
                        set(triggered) <= set(reasons),
                        "triggeredBy is a subset of reasons",
                    )
                    for trigger in triggered:
                        self.assertTrue(
                            trigger in triggers or trigger == "exception-escalation",
                            f"{trigger} is neither a declared trigger nor a direct request",
                        )
                else:
                    self.assertEqual("none", handoff["state"])
                    self.assertNotIn("triggeredBy", handoff)

    def test_evaluation_manifest_covers_every_pack_fixture_once(self) -> None:
        # Mirrors test_manifest_covers_every_fixture_once: a pack committed under packs/ and
        # referenced by no case would ship in the release bundle unexercised.
        manifest = strict_json_loads(EVALUATION_MANIFEST_PATH.read_text(encoding="utf-8"))
        referenced = {case["pack"] for case in manifest["cases"]}
        committed = {
            f"packs/{path.name}" for path in (EVALUATION / "packs").glob("*.json")
        }
        self.assertEqual(committed, referenced)

    def test_evaluation_pack_fixture_does_not_drift_from_the_example(self) -> None:
        example = (ROOT / "examples" / "data-request-intake-triage.json").read_bytes()
        fixture = (EVALUATION / "packs" / "data-request-intake-triage.json").read_bytes()
        self.assertEqual(example, fixture)

    def test_relative_markdown_links_resolve(self) -> None:
        link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
        failures: list[str] = []
        for markdown_path in sorted(ROOT.rglob("*.md")):
            if ".git" in markdown_path.parts:
                continue
            text = markdown_path.read_text(encoding="utf-8")
            for raw_target in link_pattern.findall(text):
                target = raw_target.strip().strip("<>").split("#", 1)[0]
                if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                    continue
                resolved = (markdown_path.parent / target).resolve()
                if not resolved.exists():
                    failures.append(f"{markdown_path.relative_to(ROOT)} -> {raw_target}")
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()

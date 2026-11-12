"""The staged draft Core specVersion `0.4.0-draft`, which carries RFC 0031 (a Draft).

Nothing here is a released corpus. The draft's schema, text, document cases, evaluation rows and
example are staged: normative for nothing, published nowhere and in no bundle
(conformance/staged/README.md). These tests hold them to the same checks as released artifacts, and
check that every released case still holds under the draft selector.
"""
from __future__ import annotations

import collections
import copy
import decimal
import json
import re
import shutil
import subprocess
import sys
import types
import unittest
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

import test_repository
from test_repository import (
    CONFORMANCE,
    EVALUATION,
    EVALUATION_MANIFEST_PATH,
    EVALUATION_MANIFEST_SCHEMA_PATH,
    EVALUATION_STAGED,
    EVALUATION_STAGED_CASES_PATH,
    MANIFEST_PATH,
    MANIFEST_SCHEMA_PATH,
    ROOT,
    SPEC_PATH,
    SPEC_VERSION,
    Diagnostic,
    DuplicateMemberError,
    NonJSONConstantError,
    extension_names,
    UnpairedSurrogateError,
    duplicate_id_diagnostics,
    pointer,
    pointer_contains,
    pointer_depth,
    schema_diagnostic,
    semantic_diagnostics,
    strict_json_loads,
    unsupported_diagnostics,
)

DRAFT_VERSION = "0.4.0-draft"
DRAFT_SCHEMA_PATH = ROOT / "schema" / "staged" / f"judgment-pack-core-{DRAFT_VERSION}.schema.json"
DRAFT_SCHEMA_ID = f"https://judgmentpack.org/schema/{DRAFT_VERSION}/judgment-pack-core.schema.json"
DRAFT_TEXT_PATH = ROOT / "spec" / "staged" / f"judgment-pack-core-{DRAFT_VERSION}.md"
STAGED = CONFORMANCE / "staged"
STAGED_MANIFEST_PATH = STAGED / "manifest.json"
DRAFT_ROWS = EVALUATION_STAGED / "annotations-value-sets"
DRAFT_ROWS_PATH = DRAFT_ROWS / "cases.json"
EXAMPLE_PATH = ROOT / "examples" / "staged" / "expense-approval-annotated.json"
RELEASED_EXAMPLE_PATH = ROOT / "examples" / "minimal-expense-approval.json"

ANNOTATIONS = "org.judgmentpack.annotations"
LOCAL_ID = "^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"
# RFC 0031 §1.3's class for annotation keys, and §1.4's pattern for annotation strings, as the schema
# holds them after JSON decoding (§1.7).
KEY_CLASS = "[\u0000-\u001f\u007f-\u009f\u2028-\u202e]"
_WHITE_SPACE = "[\u0009-\u000d\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]"
STRING_PATTERN = (
    "[\u0000-\u001f\u007f-\u009f\u00ad\u034f\u061c\u115f\u1160\u17b4\u17b5\u180b-\u180f\u200b-\u200f"
    "\u2028-\u202e\u2060-\u206f\u3164\ufe00-\ufe0f\ufeff\uffa0\ufff0-\ufff8"
    "\U0001bca0-\U0001bca3\U0001d173-\U0001d17a\U000e0000-\U000e0fff]"
    f"|^{_WHITE_SPACE}|{_WHITE_SPACE}$"
)
# The two `not` subschemas: under an annotations object's propertyNames, whose instances are always
# strings, and in annotationString, where `type` keeps a non-string from failing it (§1.7).
REFUSED_NOTS = ({"pattern": KEY_CLASS}, {"type": "string", "pattern": STRING_PATTERN})
# Issue #308 (RFC 0031, Unresolved question 5, answered): beside the local-identifier grammar and the
# extension-name grammar, a `not` refuses the same class as an annotation key's, so a name that ends
# in a line terminator is refused whatever an engine's anchors admit. The extension-name grammar's
# reserved prefix moves from a lookahead, which RE2 cannot compile, into that `not`, and its class
# hyphen is escaped, which ECMA-262's `v` flag requires. Each `not` holds `"type": "string"`, so a
# non-string fails `type` alone, as in annotationString.
RELEASED_EXTENSION_NAME = "^(?!org\\.judgmentpack\\.)[a-z][a-z0-9]*(?:\\.[a-z][a-z0-9-]*)+$"
EXTENSION_NAME = "^[a-z][a-z0-9]*(?:\\.[a-z][a-z0-9\\-]*)+$"
GRAMMAR_NOT = {"type": "string", "pattern": KEY_CLASS}
# The same `not` stands beside the pack-version and decimal-operand grammars, and takes the code of
# the grammar beside it.
PACK_VERSION = "^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$"
DECIMAL = "^-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?$"
GRAMMAR_CODES = {
    LOCAL_ID: "JPS-STRUCTURE-LOCAL-ID",
    PACK_VERSION: "JPS-STRUCTURE-PACK-VERSION",
    DECIMAL: "JPS-STRUCTURE-DECIMAL-OPERAND",
}
EXTENSION_NAME_NOT = {"type": "string", "pattern": "^org\\.judgmentpack\\.|" + KEY_CLASS}
# The same rule as §1.4 states it in words, written out by hand: the code points refused anywhere in
# an annotation string, and Unicode's White_Space, refused at either end.
REFUSED_ANYWHERE = (
    (0x0000, 0x001F), (0x007F, 0x009F), (0x00AD, 0x00AD), (0x034F, 0x034F), (0x061C, 0x061C),
    (0x115F, 0x1160), (0x17B4, 0x17B5), (0x180B, 0x180F), (0x200B, 0x200F), (0x2028, 0x202E),
    (0x2060, 0x206F), (0x3164, 0x3164), (0xFE00, 0xFE0F), (0xFEFF, 0xFEFF), (0xFFA0, 0xFFA0),
    (0xFFF0, 0xFFF8), (0x1BCA0, 0x1BCA3), (0x1D173, 0x1D17A), (0xE0000, 0xE0FFF),
)
WHITE_SPACE = (
    (0x0009, 0x000D), (0x0020, 0x0020), (0x0085, 0x0085), (0x00A0, 0x00A0), (0x1680, 0x1680),
    (0x2000, 0x200A), (0x2028, 0x2029), (0x202F, 0x202F), (0x205F, 0x205F), (0x3000, 0x3000),
)
NEW_CODES = [
    "JPS-STRUCTURE-MAX-LENGTH",
    "JPS-STRUCTURE-MIN-PROPERTIES",
    "JPS-STRUCTURE-MAX-PROPERTIES",
    "JPS-STRUCTURE-VALUE-SET-REFERENCE",
    "JPS-SEMANTIC-UNRESOLVED-VALUE-SET",
]
# RFC 0031's two advisory codes, outside conformance. No case states them: the released case schema
# admits only the ruleOverlap advisory (RFC 0031, Unresolved question 3).
ADVISORY_CODES = ["JPS-VALUE-SET-UNREFERENCED", "JPS-VALUE-SET-DUPLICATE-VALUE"]
# The selector substitution that carries a released case over: the root member's exact bytes.
RELEASED_SELECTOR = b'"specVersion": "0.3.0"'
DRAFT_SELECTOR = b'"specVersion": "0.4.0-draft"'


def draft_schema(profile: str = "base") -> dict[str, Any]:
    """The staged schema, with Core §4.1's ceilings for `profile` (RFC 0031 §7 adds six rows).

    The published schema carries the base maxima. A reader supporting `extended` applies the
    extended values of every row: the route row of Core 0.3.0, as tools/profile_validation.py does,
    and the six rows of the draft. Each base value is asserted before it is replaced, so a schema
    edit that moved one fails here instead of passing under a stale patch.
    """
    if profile not in ("base", "extended"):
        raise ValueError("unknown ceiling profile")
    schema = strict_json_loads(DRAFT_SCHEMA_PATH.read_text(encoding="utf-8"))
    if profile == "extended":
        defs = schema["$defs"]
        rows = (
            (defs["escalation"]["properties"]["routes"], "maxItems", 8, 16),
            (defs["disposition"]["properties"]["handoff"]["properties"]["routes"], "maxItems", 8, 16),
            (defs["annotations"], "maxProperties", 16, 32),
            (defs["annotations"]["additionalProperties"]["else"], "maxItems", 16, 32),
            (defs["annotations"]["propertyNames"], "maxLength", 64, 128),
            (defs["annotationString"], "maxLength", 256, 512),
            (schema["properties"]["valueSets"], "maxItems", 64, 128),
            (defs["valueSet"]["properties"]["entries"], "maxItems", 512, 1024),
        )
        for holder, keyword, base, extended in rows:
            if holder[keyword] != base:
                raise ValueError(f"base ceiling {keyword} is {holder[keyword]}, not {base}")
            holder[keyword] = extended
    return schema


def draft_validators() -> dict[str, Draft202012Validator]:
    return {
        profile: Draft202012Validator(draft_schema(profile), format_checker=FormatChecker())
        for profile in ("base", "extended")
    }


def draft_schema_diagnostic(error: Any) -> Diagnostic:
    """RFC 0031's code rule (Conformance, Codes), then the released corpus's rule for the rest."""
    validator = str(error.validator)
    schema_path = [str(part) for part in error.absolute_schema_path]
    instance_path = list(error.absolute_path)
    under_names = "propertyNames" in schema_path
    key = [error.instance] if under_names and isinstance(error.instance, str) else []

    def code(name: str, path: list[Any]) -> Diagnostic:
        return Diagnostic(name, pointer(path), error.message)

    # The two mapped refusals of the reference rule (§3.3), checked first so that a reference
    # inside an exception's `when` is not read as an exception-shape refusal.
    if validator == "not" and error.validator_value == {"required": ["value"]}:
        return code("JPS-STRUCTURE-VALUE-SET-REFERENCE", instance_path)
    if (
        validator == "const"
        and error.validator_value == "in"
        and instance_path[-1:] == ["operator"]
        and schema_path[-4:] == ["then", "properties", "operator", "const"]
    ):
        return code("JPS-STRUCTURE-VALUE-SET-REFERENCE", instance_path)
    if validator == "not" and error.validator_value in REFUSED_NOTS:
        # Under an annotations object's propertyNames the class repeats the local-identifier
        # grammar for engines whose `$` admits a final line feed, and takes its code (§1.3).
        if under_names:
            return code("JPS-STRUCTURE-LOCAL-ID", instance_path + key)
        return code("JPS-STRUCTURE-NOT", instance_path)
    if (
        validator == "not"
        and error.validator_value == GRAMMAR_NOT
        and isinstance(error.schema, dict)
        and error.schema.get("pattern") in GRAMMAR_CODES
    ):
        # Issue #308: the class repeats the grammar beside it, and takes that grammar's code.
        return code(GRAMMAR_CODES[error.schema["pattern"]], instance_path)
    if (validator == "not" and error.validator_value == EXTENSION_NAME_NOT) or (
        validator == "pattern" and error.validator_value == EXTENSION_NAME
    ):
        # Issue #308: the extension-name grammar, its reserved prefix and the class are one code,
        # at the key under propertyNames, as the released grammar's refusal is.
        return code("JPS-STRUCTURE-EXTENSION-NAME", instance_path + key)
    if (
        validator == "anyOf"
        and under_names
        and isinstance(error.validator_value, list)
        and error.validator_value[:1] == [{"const": ANNOTATIONS}]
    ):
        # A key refused by the extension-name grammar as a branch of an anyOf (rule 1).
        return code("JPS-STRUCTURE-EXTENSION-NAME", instance_path + key)
    if validator == "pattern" and error.validator_value == LOCAL_ID and under_names:
        return code("JPS-STRUCTURE-LOCAL-ID", instance_path + key)
    new_keywords = {
        "maxLength": "JPS-STRUCTURE-MAX-LENGTH",
        "minProperties": "JPS-STRUCTURE-MIN-PROPERTIES",
        "maxProperties": "JPS-STRUCTURE-MAX-PROPERTIES",
    }
    if validator in new_keywords:
        return code(new_keywords[validator], instance_path + key)
    return schema_diagnostic(error)


def draft_walk(error: Any) -> Iterable[Any]:
    yield error
    if str(error.validator) == "anyOf" and "propertyNames" in [str(p) for p in error.absolute_schema_path]:
        return  # one refusal, the key's: its branches are not separate findings
    for child in error.context:
        yield from draft_walk(child)


def draft_structural_diagnostics(validator: Draft202012Validator, value: Any) -> list[Diagnostic]:
    # Findings are a set of (code, pointer) pairs (conformance/staged/README.md): a keyword reported
    # twice at one pointer, whatever the messages say, is one finding.
    diagnostics: list[Diagnostic] = []
    seen: set[tuple[str, str]] = set()
    for top_level in validator.iter_errors(value):
        for error in draft_walk(top_level):
            item = draft_schema_diagnostic(error)
            identity = (item.code, item.path)
            if identity not in seen:
                seen.add(identity)
                diagnostics.append(item)
    return diagnostics


def fact_conditions(value: dict[str, Any]) -> list[tuple[dict[str, Any], list[Any]]]:
    """Every fact condition in every condition position RFC 0031 §3.2 names, with its path."""
    found: list[tuple[dict[str, Any], list[Any]]] = []

    def walk(condition: Any, path: list[Any]) -> None:
        if not isinstance(condition, dict):
            return
        op = condition.get("op")
        if op == "fact":
            found.append((condition, path))
        elif op in ("all", "any"):
            for index, child in enumerate(condition.get("conditions", [])):
                walk(child, path + ["conditions", index])
        elif op == "not":
            walk(condition.get("condition"), path + ["condition"])

    if "applicability" in value:
        walk(value["applicability"], ["applicability"])
    for index, rule in enumerate(value.get("rules", [])):
        walk(rule.get("when"), ["rules", index, "when"])
    for index, exception in enumerate(value.get("exceptions", [])):
        walk(exception.get("when"), ["exceptions", index, "when"])
    return found


def schema_extension_holders(value: dict[str, Any]) -> list[dict[str, Any]]:
    """The objects whose `extensions` member the schema defines, and that carry one (RFC 0031 §4.1).

    A member named `extensions` inside an operand, an entry value or an extension's own value is
    data, not an `extensions` object. A value-set object has no such member (§2.2), and a pack whose
    set carried one is refused before this is read.
    """
    holders: list[Any] = [value, value.get("decision"), value.get("escalation"), value.get("metadata")]
    for collection in ("evidenceRequirements", "sources", "outcomes", "rules", "exceptions"):
        holders.extend(value.get(collection, []))
    for value_set in value.get("valueSets", []):
        holders.extend(value_set.get("entries", []))
    return [holder for holder in holders if isinstance(holder, dict) and isinstance(holder.get("extensions"), dict)]


def schema_extension_objects(value: dict[str, Any]) -> list[dict[str, Any]]:
    return [holder["extensions"] for holder in schema_extension_holders(value)]


def schema_extension_names(value: Any) -> set[str]:
    names: set[str] = set()
    for extensions in schema_extension_objects(value):
        names.update(extensions)
    return names


def draft_semantic_diagnostics(value: dict[str, Any]) -> list[Diagnostic]:
    diagnostics = semantic_diagnostics(value, extension_names_of=schema_extension_names)
    diagnostics.extend(duplicate_id_diagnostics(value, "valueSets"))
    declared = {item["id"] for item in value.get("valueSets", [])}
    for condition, path in fact_conditions(value):
        if "valueSet" in condition and condition["valueSet"] not in declared:
            diagnostics.append(Diagnostic(
                "JPS-SEMANTIC-UNRESOLVED-VALUE-SET",
                pointer(path + ["valueSet"]),
                f"value-set reference does not resolve: {condition['valueSet']}",
            ))
    return diagnostics


def profile_of(value: Any) -> str:
    """The declared profile, for choosing ceilings; anything else is the schema's to refuse."""
    profile = value.get("profile", "base") if isinstance(value, dict) else "base"
    return profile if profile in ("base", "extended") else "base"


def draft_pack_diagnostics(validators: dict[str, Draft202012Validator], pack: Any) -> list[Diagnostic]:
    diagnostics = draft_structural_diagnostics(validators[profile_of(pack)], pack)
    if diagnostics:
        return diagnostics
    return draft_semantic_diagnostics(pack)


def draft_evaluate_text(
    text: str, validators: dict[str, Draft202012Validator], supported: Iterable[str]
) -> tuple[str, list[Diagnostic]]:
    try:
        value = strict_json_loads(text)
    except DuplicateMemberError as error:
        return "invalid", [Diagnostic("JPS-CARRIER-DUPLICATE-MEMBER", error.path, str(error))]
    except (UnicodeError, json.JSONDecodeError, UnpairedSurrogateError, NonJSONConstantError) as error:
        return "invalid", [Diagnostic("JPS-CARRIER-INVALID-JSON", "", str(error))]
    diagnostics = draft_pack_diagnostics(validators, value)
    if diagnostics:
        return "invalid", diagnostics
    diagnostics = unsupported_diagnostics(value, supported)
    if diagnostics:
        return "unsupported", diagnostics
    return "valid", []


def evaluation_form(pack: dict[str, Any]) -> dict[str, Any]:
    """EF(P), RFC 0031 §4.1, for a semantically conforming pack: expand, remove sets, remove annotations."""
    form = copy.deepcopy(pack)
    entries = {item["id"]: [entry["value"] for entry in item["entries"]] for item in form.get("valueSets", [])}
    for condition, _ in fact_conditions(form):
        if "valueSet" in condition:
            condition["value"] = copy.deepcopy(entries[condition.pop("valueSet")])
    form.pop("valueSets", None)
    for holder in [form] + form.get("outcomes", []) + form.get("rules", []):
        extensions = holder.get("extensions")
        if isinstance(extensions, dict) and ANNOTATIONS in extensions:
            del extensions[ANNOTATIONS]
            if not extensions:
                del holder["extensions"]
    return form


def _equality_key(value: Any) -> Any:
    """A key under Core §7.4's type-preserving equality: numbers by value, objects regardless of order."""
    if isinstance(value, bool):
        return ("boolean", value)
    if value is None:
        return ("null",)
    if isinstance(value, (int, float, decimal.Decimal)):
        number = decimal.Decimal(str(value))
        return ("number", "0" if number == 0 else str(number.normalize()))
    if isinstance(value, str):
        return ("string", value)
    if isinstance(value, list):
        return ("array", tuple(_equality_key(item) for item in value))
    return ("object", tuple(sorted((name, _equality_key(item)) for name, item in value.items())))


# A set of values is (complemented, members): (False, S) is S, and (True, S) is every value but S.
_ALL: tuple[bool, frozenset[Any]] = (True, frozenset())
_NONE: tuple[bool, frozenset[Any]] = (False, frozenset())


def _intersect(x: tuple[bool, frozenset[Any]], y: tuple[bool, frozenset[Any]]) -> tuple[bool, frozenset[Any]]:
    if x[0] and y[0]:
        return True, x[1] | y[1]
    if x[0]:
        return False, y[1] - x[1]
    if y[0]:
        return False, x[1] - y[1]
    return False, x[1] & y[1]


def _unite(x: tuple[bool, frozenset[Any]], y: tuple[bool, frozenset[Any]]) -> tuple[bool, frozenset[Any]]:
    if x[0] and y[0]:
        return True, x[1] & y[1]
    if x[0]:
        return True, x[1] - y[1]
    if y[0]:
        return True, y[1] - x[1]
    return False, x[1] | y[1]


def _true_and_false_sets(condition: Any, paths: set[str]) -> Any:
    """Core §3.3.1's true and false sets for the equality fragment, or None outside it."""
    op = condition.get("op") if isinstance(condition, dict) else None
    if op == "literal":
        return (_ALL, _NONE) if condition["value"] is True else (_NONE, _ALL)
    if op == "fact":
        paths.add(condition["path"])
        operator = condition["operator"]
        if operator in ("equals", "not-equals"):
            members = frozenset([_equality_key(condition["value"])])
            sets = ((False, members), (True, members))
            return sets if operator == "equals" else sets[::-1]
        if operator == "in":
            members = frozenset(_equality_key(item) for item in condition["value"])
            return (False, members), (True, members)
        return None
    if op in ("all", "any"):
        children = [_true_and_false_sets(child, paths) for child in condition["conditions"]]
        if any(child is None for child in children):
            return None
        true, false = (_ALL, _NONE) if op == "all" else (_NONE, _ALL)
        for child_true, child_false in children:
            if op == "all":
                true, false = _intersect(true, child_true), _unite(false, child_false)
            else:
                true, false = _unite(true, child_true), _intersect(false, child_false)
        return true, false
    if op == "not":
        child = _true_and_false_sets(condition["condition"], paths)
        return None if child is None else (child[1], child[0])
    return None


def exact_overlap(first: Any, second: Any) -> bool | None:
    """Whether two conditions can both be true (Core §3.3.1), where the equality fragment decides it."""
    paths: set[str] = set()
    a, b = _true_and_false_sets(first, paths), _true_and_false_sets(second, paths)
    if a is None or b is None or len(paths) > 1:
        return None
    both = _intersect(a[0], b[0])
    return both[0] or bool(both[1])


def without_optional_extensions(pack: dict[str, Any]) -> dict[str, Any]:
    """The pack with every extension key that metadata.requiredExtensions does not list removed."""
    form = copy.deepcopy(pack)
    required = set(form.get("metadata", {}).get("requiredExtensions", []))
    for holder in schema_extension_holders(form):
        extensions = holder["extensions"]
        removed = [name for name in extensions if name not in required]
        for name in removed:
            del extensions[name]
        if removed and not extensions:
            del holder["extensions"]  # emptied by the removal, as EF's step 3 drops one
    return form


def spec_sections(*paths: Path) -> set[str]:
    numbers: set[str] = set()
    heading = re.compile(r"^#{2,6}\s+(\d+(?:\.\d+)*)\b")
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            match = heading.match(line)
            if match:
                numbers.add(match.group(1))
    return numbers


def assert_one_finding(test: unittest.TestCase, case_id: str, expected: dict[str, str],
                       diagnostics: list[Diagnostic]) -> None:
    """The released corpus's strictness (test_conformance_cases): the expected finding, and no other
    outside the outermost oneOf that encloses it. Findings compare as a set of (code, pointer) pairs."""
    pairs = list(dict.fromkeys((d.code, d.path) for d in diagnostics))
    wanted = (expected["code"], expected["path"])
    test.assertIn(wanted, pairs, f"{case_id}: expected {wanted}; got {pairs}")
    enclosing = [d.path for d in diagnostics if d.code == "JPS-STRUCTURE-ONEOF" and pointer_contains(d.path, wanted[1])]
    if enclosing:
        outermost = min(enclosing, key=pointer_depth)
        strays = [p for p in pairs if not pointer_contains(outermost, p[1])]
        test.assertEqual([], strays, f"{case_id}: stray diagnostics outside {outermost!r}: {pairs}")
    else:
        test.assertEqual([wanted], pairs, f"{case_id}: expected only {wanted}; got {pairs}")


def case_validator(manifest_schema_path: Path) -> Draft202012Validator:
    manifest_schema = strict_json_loads(manifest_schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(
        {"$schema": manifest_schema["$schema"], "$ref": "#/$defs/case", "$defs": manifest_schema["$defs"]},
        format_checker=FormatChecker(),
    )


class DraftSchemaTests(unittest.TestCase):
    def test_schema_is_draft_2020_12_with_the_draft_identity(self) -> None:
        schema = draft_schema()
        Draft202012Validator.check_schema(schema)
        self.assertEqual(DRAFT_SCHEMA_ID, schema["$id"])
        self.assertEqual(DRAFT_VERSION, schema["properties"]["specVersion"]["const"])
        self.assertEqual(
            f"Staged draft structural schema for {DRAFT_VERSION}, carrying RFC 0031 (a Draft). It is "
            "normative for nothing and is not published. Conformance does not establish truth, "
            "authority, safety, or operational fitness.",
            schema["description"],
        )

    def test_schema_is_the_released_schema_plus_exactly_the_rfc_fragments(self) -> None:
        # Undo RFC 0031's fragments (§§1.7, 2.7, 3.3) and the identity: what remains must be the
        # released 0.3.0 schema, so the draft changes nothing the RFC does not name.
        released = strict_json_loads((ROOT / "schema" / "judgment-pack-core.schema.json").read_text(encoding="utf-8"))
        draft = draft_schema()
        defs = draft["$defs"]
        for name in ("annotationString", "annotations", "annotatedExtensions", "entryExtensions", "valueSet", "valueSetEntry"):
            del defs[name]
        self.assertEqual({"type": "array", "maxItems": 64, "uniqueItems": True, "items": {"$ref": "#/$defs/valueSet"}},
                         draft["properties"].pop("valueSets"))
        for holder in (draft["properties"], defs["outcome"]["properties"], defs["rule"]["properties"]):
            self.assertEqual({"$ref": "#/$defs/annotatedExtensions"}, holder["extensions"])
            holder["extensions"] = {"$ref": "#/$defs/extensions"}
        fact = [branch for branch in defs["condition"]["oneOf"] if branch["properties"]["op"] == {"const": "fact"}]
        self.assertEqual(1, len(fact))
        fact = fact[0]
        self.assertEqual({"$ref": "#/$defs/localId"}, fact["properties"].pop("valueSet"))
        self.assertEqual(["op", "path", "operator"], fact["required"])
        fact["required"] = ["op", "path", "operator", "value"]
        self.assertEqual(
            {"if": {"required": ["valueSet"]},
             "then": {"not": {"required": ["value"]}, "properties": {"operator": {"const": "in"}}},
             "else": {"required": ["value"]}},
            fact["allOf"].pop(),
        )
        # Issue #308 (RFC 0031, Unresolved question 5, answered): the identifier patterns.
        self.assertEqual(GRAMMAR_NOT, defs["localId"].pop("not"))
        self.assertEqual(GRAMMAR_NOT, draft["properties"]["version"].pop("not"))
        self.assertEqual(GRAMMAR_NOT, defs["decimalString"].pop("not"))
        self.assertEqual({"pattern": RELEASED_EXTENSION_NAME}, released["$defs"]["extensions"]["propertyNames"])
        self.assertEqual({"pattern": EXTENSION_NAME, "not": EXTENSION_NAME_NOT}, defs["extensions"]["propertyNames"])
        defs["extensions"]["propertyNames"] = {"pattern": RELEASED_EXTENSION_NAME}
        required = defs["metadata"]["properties"]["requiredExtensions"]
        self.assertEqual({"type": "string", "pattern": EXTENSION_NAME, "not": EXTENSION_NAME_NOT}, required["items"])
        required["items"] = {"type": "string", "pattern": RELEASED_EXTENSION_NAME}
        for member in ("$id", "description"):
            draft[member] = released[member]
        draft["properties"]["specVersion"] = released["properties"]["specVersion"]
        self.assertEqual(released, draft)

    def test_the_fragments_are_the_rfc_text(self) -> None:
        # The JSON blocks of RFC 0031 §§1.7 and 2.7 are the definitions, byte for byte once parsed.
        text = (ROOT / "rfcs" / "0031-annotations-and-value-sets.md").read_text(encoding="utf-8")
        blocks = [json.loads(block) for block in re.findall(r"^```json\n(.*?)^```$", text, re.M | re.S)]
        defs = draft_schema()["$defs"]
        for name, value in {**blocks[0], **blocks[1]}.items():
            with self.subTest(definition=name):
                self.assertEqual(value, defs[name])
        self.assertEqual(blocks[2]["valueSets"], draft_schema()["properties"]["valueSets"])
        fact = [b for b in defs["condition"]["oneOf"] if b["properties"]["op"] == {"const": "fact"}][0]
        self.assertEqual(blocks[3]["allOf"][1:], fact["allOf"][2:])
        self.assertEqual(blocks[3]["properties"], fact["properties"])
        self.assertEqual(blocks[3]["required"], fact["required"])

    def test_extended_ceilings_refuse_an_unknown_profile_and_a_moved_base_value(self) -> None:
        with self.assertRaises(ValueError):
            draft_schema("future")
        self.assertEqual(16, draft_schema()["$defs"]["annotations"]["maxProperties"])
        self.assertEqual(32, draft_schema("extended")["$defs"]["annotations"]["maxProperties"])
        self.assertEqual(1024, draft_schema("extended")["$defs"]["valueSet"]["properties"]["entries"]["maxItems"])


class DraftDocumentCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validators = draft_validators()
        cls.manifest = strict_json_loads(STAGED_MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.released = strict_json_loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_shape(self) -> None:
        # Staged cases carry no suiteVersion: they belong to none. They validate against the released
        # case schema unchanged, so moving one into a manifest edits nothing.
        self.assertEqual(
            {"status", "stagedAfter", "specVersion", "caseSchema", "readerProfiles", "carriesOver", "newCodes",
             "advisoryCodes", "cases"},
            set(self.manifest),
        )
        self.assertEqual(ADVISORY_CODES, self.manifest["advisoryCodes"])
        self.assertEqual("staged", self.manifest["status"])
        self.assertEqual(SPEC_VERSION, self.manifest["stagedAfter"])
        self.assertEqual(DRAFT_VERSION, self.manifest["specVersion"])
        self.assertEqual("../manifest.schema.json#/$defs/case", self.manifest["caseSchema"])
        self.assertEqual(["base", "extended"], self.manifest["readerProfiles"])
        self.assertEqual("../manifest.json", self.manifest["carriesOver"])
        self.assertEqual(NEW_CODES, self.manifest["newCodes"])
        validator = case_validator(MANIFEST_SCHEMA_PATH)
        for case in self.manifest["cases"]:
            with self.subTest(case=case.get("id")):
                self.assertEqual([], [e.message for e in validator.iter_errors(case)])

    def test_ids_and_paths_are_unique_and_new(self) -> None:
        cases = self.manifest["cases"]
        for field in ("id", "path"):
            counts = collections.Counter(case[field] for case in cases)
            self.assertEqual([], [value for value, count in counts.items() if count > 1], field)
            released = {case[field] for case in self.released["cases"]}
            self.assertEqual(set(), set(counts) & released, f"a staged {field} the released manifest already uses")

    def test_every_staged_file_is_named_once(self) -> None:
        listed = {case["path"] for case in self.manifest["cases"]}
        on_disk = {p.relative_to(STAGED).as_posix() for p in STAGED.rglob("*.json") if p.name != "manifest.json"}
        self.assertEqual(set(), listed - on_disk, "case paths naming no file")
        self.assertEqual(set(), on_disk - listed, "files no case names")

    def test_layers_directories_and_codes_agree(self) -> None:
        released_codes = {c["expectedDiagnostic"]["code"] for c in self.released["cases"] if c["expectedDiagnostic"]}
        used = set()
        families = {"carrier": {"CARRIER"}, "structural": {"STRUCTURE"}, "semantic": {"SEMANTIC", "CAPABILITY"}}
        for case in self.manifest["cases"]:
            with self.subTest(case=case["id"]):
                directory = case["path"].split("/")[0]
                if directory == "valid":
                    self.assertEqual(("semantic", "valid", None),
                                     (case["layer"], case["expectedResult"], case["expectedDiagnostic"]))
                else:
                    self.assertEqual(directory, case["layer"])
                expected = case["expectedDiagnostic"]
                if expected:
                    used.add(expected["code"])
                    self.assertIn(expected["code"].split("-")[1], families[case["layer"]])
        self.assertEqual(set(NEW_CODES), used - released_codes, "newCodes is exactly the codes the released corpus lacks")
        self.assertEqual(set(), used & set(ADVISORY_CODES), "an advisory code is never a conformance diagnostic")

    def test_each_advisory_code_has_cases_whose_document_result_is_valid(self) -> None:
        # RFC 0031's Evidence bar item 3 asks for the document result of every advisory case. That
        # result is `valid`, and these cases state it; the advisory itself is not stated.
        slugs = {"JPS-VALUE-SET-UNREFERENCED": "unreferenced", "JPS-VALUE-SET-DUPLICATE-VALUE": "duplicate-value"}
        for advisory, slug in slugs.items():
            cases = [c for c in self.manifest["cases"] if c["id"].startswith("advisory-value-set-" + slug)]
            with self.subTest(advisory=advisory):
                self.assertTrue(cases)
                for c in cases:
                    self.assertEqual(("valid", None), (c["expectedResult"], c["expectedDiagnostic"]))
                    self.assertTrue(c["path"].startswith("valid/"), "the released case schema keeps advisory/ for ruleOverlap")
                    self.assertNotIn("expectedAdvisories", c)

    def test_staged_json_holds_no_raw_non_ascii_character(self) -> None:
        # The README's promise: every non-ASCII character is a JSON escape, one outside the BMP as a
        # surrogate pair, so no invisible character sits raw in a fixture.
        files = [*STAGED.rglob("*.json"), *DRAFT_ROWS.rglob("*.json"), EXAMPLE_PATH, DRAFT_SCHEMA_PATH]
        for path in files:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertTrue(path.read_bytes().isascii())
        non_bmp = strict_json_loads((STAGED / "valid" / "annotations-non-bmp.json").read_text(encoding="utf-8"))
        self.assertEqual("\U0001F600" * 256, non_bmp["rules"][0]["extensions"][ANNOTATIONS]["label"])

    def test_cases_cite_sections_of_the_draft_or_of_core(self) -> None:
        sections = spec_sections(SPEC_PATH, DRAFT_TEXT_PATH)
        for case in self.manifest["cases"]:
            with self.subTest(case=case["id"]):
                number = case["specSection"].lstrip("§")
                self.assertIn(number, sections)

    def test_staged_document_cases(self) -> None:
        for case in self.manifest["cases"]:
            with self.subTest(case=case["id"]):
                text = (STAGED / case["path"]).read_text(encoding="utf-8")
                self.assertIn(DRAFT_SELECTOR.decode(), text)
                result, diagnostics = draft_evaluate_text(text, self.validators, case.get("supportedExtensions", []))
                self.assertEqual(case["expectedResult"], result, [(d.code, d.path) for d in diagnostics])
                if case["expectedDiagnostic"] is None:
                    self.assertEqual([], diagnostics)
                else:
                    assert_one_finding(self, case["id"], case["expectedDiagnostic"], diagnostics)

    def test_each_structural_case_holds_one_defect(self) -> None:
        # Issue #304: a case holds exactly the defect it names. The oneOf rule above admits a
        # finding inside the outermost oneOf whose pointer encloses the stated one, so a second,
        # unrelated defect at an enclosing object (an escalation with neither target nor routes)
        # would pass it. Here every refusal the validator reports at the top level must hold the
        # stated finding, so each one comes from the case's own defect.
        for case in self.manifest["cases"]:
            if case["layer"] != "structural":
                continue
            with self.subTest(case=case["id"]):
                value = strict_json_loads((STAGED / case["path"]).read_text(encoding="utf-8"))
                wanted = (case["expectedDiagnostic"]["code"], case["expectedDiagnostic"]["path"])
                top_level = list(self.validators[profile_of(value)].iter_errors(value))
                self.assertTrue(top_level)
                for error in top_level:
                    pairs = {(d.code, d.path) for d in map(draft_schema_diagnostic, draft_walk(error))}
                    self.assertIn(wanted, pairs, f"a refusal that is not the case's own: {sorted(pairs)}")

    def test_no_valid_case_has_an_exact_rule_overlap(self) -> None:
        # Issue #304: a valid case is about its own property, so it carries no exact overlap of two
        # rules naming different outcomes, which a validator running the recommended check (Core
        # §3.3.1) would report. The check here is exact for the fragment it reads: `literal`,
        # `equals`, `not-equals` and `in` on one fact path, under `all`, `any` and `not`, on the
        # evaluation form (a reference reads as its set, RFC 0031 §4.4). A pair outside that
        # fragment is not decided here.
        decided = 0
        for case in self.manifest["cases"]:
            if case["expectedResult"] != "valid":
                continue
            with self.subTest(case=case["id"]):
                form = evaluation_form(strict_json_loads((STAGED / case["path"]).read_text(encoding="utf-8")))
                rules = form.get("rules", [])
                for first in range(len(rules)):
                    for second in range(first + 1, len(rules)):
                        a, b = rules[first], rules[second]
                        if a["outcome"] == b["outcome"]:
                            continue
                        overlap = exact_overlap(a["when"], b["when"])
                        if overlap is not None:
                            decided += 1
                            self.assertFalse(overlap, f"rules {a['id']} and {b['id']} overlap")
        self.assertGreater(decided, 0)

    def test_every_released_document_case_holds_under_the_draft_selector(self) -> None:
        # The draft refuses one 0.3.0 shape, by its reading of an extensions object, a change under
        # the draft selector (RFC 0031, Compatibility), and no released case has it: each released
        # case, with its root selector's bytes replaced, gives its released result and diagnostic
        # under the draft.
        # A fixture that does not declare 0.3.0 (the 0.2.0-draft negative case, malformed carriers)
        # is run unchanged and must also keep its expectation.
        replaced = 0
        for case in self.released["cases"]:
            with self.subTest(case=case["id"]):
                data = (CONFORMANCE / case["path"]).read_bytes()
                if RELEASED_SELECTOR in data:
                    self.assertEqual(1, data.count(RELEASED_SELECTOR))
                    data = data.replace(RELEASED_SELECTOR, DRAFT_SELECTOR)
                    replaced += 1
                try:
                    text = data.decode("utf-8")
                except UnicodeError:
                    text = None
                if text is None:
                    self.assertEqual("JPS-CARRIER-INVALID-JSON", case["expectedDiagnostic"]["code"])
                    continue
                result, diagnostics = draft_evaluate_text(text, self.validators, case.get("supportedExtensions", []))
                self.assertEqual(case["expectedResult"], result, [(d.code, d.path) for d in diagnostics])
                if case["expectedDiagnostic"] is None:
                    self.assertEqual([], diagnostics)
                else:
                    assert_one_finding(self, case["id"], case["expectedDiagnostic"], diagnostics)
        self.assertGreater(replaced, 140)

    def test_the_draft_code_rules_match_nothing_in_the_released_schema(self) -> None:
        # Each rule draft_schema_diagnostic adds is keyed on a subschema only the RFC's fragments
        # hold, so it cannot recode a released refusal; the carry-over test above checks the results.
        released = strict_json_loads((ROOT / "schema" / "judgment-pack-core.schema.json").read_text(encoding="utf-8"))
        found = []

        def walk(node: Any, path: list[str]) -> None:
            if isinstance(node, dict):
                for keyword, value in node.items():
                    if keyword in ("maxLength", "minProperties", "maxProperties"):
                        found.append(path + [keyword])
                    if keyword == "not" and value in ({"required": ["value"]}, *REFUSED_NOTS, GRAMMAR_NOT, EXTENSION_NAME_NOT):
                        found.append(path + [keyword])
                    if keyword == "pattern" and value == EXTENSION_NAME:
                        found.append(path + [keyword])
                    if keyword == "anyOf" and "propertyNames" in path:
                        found.append(path + [keyword])
                    if keyword == "const" and value == "in" and path[-3:] == ["then", "properties", "operator"]:
                        found.append(path + [keyword])
                    walk(value, path + [keyword])
            elif isinstance(node, list):
                for index, item in enumerate(node):
                    walk(item, path + [str(index)])

        walk(released, [])
        self.assertEqual([], found)


class DraftExampleTests(unittest.TestCase):
    def test_example_is_valid_and_is_the_staged_fixture(self) -> None:
        text = EXAMPLE_PATH.read_text(encoding="utf-8")
        self.assertEqual(text, (STAGED / "valid" / "expense-approval-annotated.json").read_text(encoding="utf-8"))
        self.assertEqual(("valid", []), draft_evaluate_text(text, draft_validators(), []))

    def test_example_uses_both_features_and_its_evaluation_form_is_the_released_example(self) -> None:
        example = strict_json_loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        self.assertTrue(example["valueSets"])
        self.assertTrue(any("valueSet" in condition for condition, _ in fact_conditions(example)))
        self.assertTrue(any(ANNOTATIONS in e for e in schema_extension_objects(example)))
        released = strict_json_loads(RELEASED_EXAMPLE_PATH.read_text(encoding="utf-8"))
        released["specVersion"] = DRAFT_VERSION
        released["version"] = example["version"]
        self.assertNotEqual(released["version"], "0.1.0", "changed content gets a new pack version (Core §11)")
        self.assertEqual(released, evaluation_form(example))


class DraftEvaluationRowTests(unittest.TestCase):
    """RFC 0031's staged evaluation rows, held to the released rows' checks and the static pair check."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.validators = draft_validators()
        cls.document = strict_json_loads(DRAFT_ROWS_PATH.read_text(encoding="utf-8"))
        cls.rows = cls.document["cases"]
        cls.held = [item["case"] for item in cls.document["heldCases"]]
        cls.by_id = {row["id"]: row for row in cls.rows + cls.held}

    def pack(self, relative: str) -> dict[str, Any]:
        return strict_json_loads((DRAFT_ROWS / relative).read_text(encoding="utf-8"))

    def test_document_shape(self) -> None:
        self.assertEqual(
            {"status", "stagedAfter", "specVersion", "caseSchema", "carriesOver", "cases", "heldCases", "pairs",
             "ownEvaluationForm"},
            set(self.document),
        )
        self.assertEqual(("staged", SPEC_VERSION, DRAFT_VERSION, "../../manifest.schema.json#/$defs/case"),
                         (self.document["status"], self.document["stagedAfter"], self.document["specVersion"],
                          self.document["caseSchema"]))
        self.assertEqual(["../../manifest.json", "../cases.json"], self.document["carriesOver"])
        validator = case_validator(EVALUATION_MANIFEST_SCHEMA_PATH)
        for row in self.rows:
            with self.subTest(row=row["id"]):
                self.assertEqual("rfc-0031", row["origin"])
                self.assertEqual([], [e.message for e in validator.iter_errors(row)])

    def test_held_rows_fail_the_released_case_schema_only_where_they_say(self) -> None:
        # A held row is one the released case schema cannot state. It fails that schema in exactly
        # one place, the reserved name in its supported-extension set, and is otherwise a row.
        validator = case_validator(EVALUATION_MANIFEST_SCHEMA_PATH)
        self.assertEqual(["annotations-supported-extension-set"], [row["id"] for row in self.held])
        for item in self.document["heldCases"]:
            self.assertEqual({"case", "heldBecause"}, set(item))
            errors = list(validator.iter_errors(item["case"]))
            self.assertEqual([(["supportedExtensions", 0], "pattern")],
                             [(list(e.absolute_path), e.validator) for e in errors])
            self.assertEqual([ANNOTATIONS], item["case"]["supportedExtensions"])
            repaired = dict(item["case"], supportedExtensions=[])
            self.assertEqual([], list(validator.iter_errors(repaired)))

    def test_ids_are_unique_and_new(self) -> None:
        counts = collections.Counter(row["id"] for row in self.rows + self.held)
        self.assertEqual([], [i for i, n in counts.items() if n > 1])
        released = {c["id"] for c in strict_json_loads(EVALUATION_MANIFEST_PATH.read_text(encoding="utf-8"))["cases"]}
        staged = {c["id"] for c in strict_json_loads(EVALUATION_STAGED_CASES_PATH.read_text(encoding="utf-8"))["cases"]}
        self.assertEqual(set(), set(counts) & (released | staged))

    def test_every_pack_is_named_and_every_name_is_a_pack(self) -> None:
        listed = {row["pack"] for row in self.rows + self.held}
        on_disk = {"packs/" + p.name for p in (DRAFT_ROWS / "packs").glob("*.json")}
        self.assertEqual(set(), listed - on_disk)
        self.assertEqual(set(), on_disk - listed)
        self.assertEqual(set(), {p.name for p in (DRAFT_ROWS / "packs").iterdir()} - {Path(p).name for p in on_disk})

    def test_rows_are_well_formed_against_their_pack(self) -> None:
        # The released rows' checker, with the draft's schema, selector and conformance checks. A
        # checker outside a running test raises on its first failure, which names the row.
        # The class is reached through its module so that the loader does not collect it here too.
        checker = test_repository.RepositoryConformanceTests()
        checker._check_evaluation_cases(self.rows + self.held, DRAFT_ROWS, self.validators["base"], DRAFT_VERSION,
                                        lambda _validator, pack: draft_pack_diagnostics(self.validators, pack))

    def test_rows_cite_sections_of_the_draft_or_of_core(self) -> None:
        sections = spec_sections(SPEC_PATH, DRAFT_TEXT_PATH)
        for row in self.rows + self.held:
            with self.subTest(row=row["id"]):
                self.assertIn(row["specSection"].lstrip("§"), sections)

    def test_non_conformant_packs_fail_for_their_one_stated_reason(self) -> None:
        stated = {
            "packs/malformed-too-many-keys.json": [("JPS-STRUCTURE-MAX-PROPERTIES", "/rules/0/extensions/" + ANNOTATIONS)],
            "packs/malformed-tab.json": [("JPS-STRUCTURE-NOT", "/rules/0/extensions/" + ANNOTATIONS + "/category")],
            "packs/annotations-listed-as-required.json": [("JPS-STRUCTURE-EXTENSION-NAME", "/metadata/requiredExtensions/0")],
            "packs/value-set-unresolved.json": [("JPS-SEMANTIC-UNRESOLVED-VALUE-SET", "/rules/0/when/valueSet")],
            "packs/value-set-unresolved-outcome-id.json": [("JPS-SEMANTIC-UNRESOLVED-VALUE-SET", "/rules/0/when/valueSet")],
        }
        failing = {row["pack"] for row in self.rows if row.get("expectedErrorClass") == "pack-not-conformant"}
        self.assertEqual(set(stated), failing)
        for relative, reasons in stated.items():
            with self.subTest(pack=relative):
                diagnostics = draft_pack_diagnostics(self.validators, self.pack(relative))
                self.assertEqual(reasons, [(d.code, d.path) for d in diagnostics])

    def test_paired_rows_have_equal_evaluation_forms_inputs_and_expectations(self) -> None:
        # RFC 0031's static check: a pair that fails it is a defect in the fixtures, caught here
        # before any implementation runs them.
        paired = collections.Counter()
        for item in self.document["pairs"]:
            with self.subTest(pair=item["id"]):
                self.assertEqual({"id", "basis", "cases"}, set(item))
                rows = [self.by_id[case_id] for case_id in item["cases"]]
                paired.update(item["cases"])
                self.assertGreaterEqual(len(rows), 2)
                packs = [self.pack(row["pack"]) for row in rows]
                forms = [evaluation_form(pack) for pack in packs]
                expected = [row.get("expectedDisposition", row.get("expectedErrorClass")) for row in rows]
                self.assertEqual(1, len({json.dumps(e, sort_keys=True) for e in expected}), "one expected result")
                for field in ("facts", "evidenceAvailability"):
                    self.assertEqual(1, len({json.dumps(row.get(field), sort_keys=True) for row in rows}), field)
                if item["basis"] == "evaluation-form":
                    self.assertTrue(all(form == forms[0] for form in forms), "evaluation forms differ")
                    self.assertEqual(1, len({json.dumps(row["supportedExtensions"]) for row in rows}))
                    self.assertGreater(len({row["pack"] for row in rows}), 1, "a pair compares two packs")
                elif item["basis"] == "optional-extension":
                    stripped = [without_optional_extensions(form) for form in forms]
                    self.assertTrue(all(form == stripped[0] for form in stripped))
                    self.assertFalse(all(form == forms[0] for form in forms), "the pair differs in an optional extension")
                    self.assertEqual(1, len({json.dumps(row["supportedExtensions"]) for row in rows}))
                elif item["basis"] == "supported-extension-set":
                    self.assertEqual(1, len({row["pack"] for row in rows}))
                    sets = [set(row["supportedExtensions"]) for row in rows]
                    self.assertEqual({ANNOTATIONS}, set.union(*sets) - set.intersection(*sets))
                else:
                    self.fail(f"unknown basis {item['basis']!r}")
        self.assertEqual([], [i for i, n in paired.items() if n > 1], "a row belongs to one pair at most")

    def test_own_evaluation_forms_are_exactly_those_listed(self) -> None:
        listed = set(self.document["ownEvaluationForm"])
        self.assertEqual(sorted(listed), self.document["ownEvaluationForm"])
        for row in self.rows + self.held:
            if row.get("expectedErrorClass") == "pack-not-conformant":
                continue
            with self.subTest(row=row["id"]):
                pack = self.pack(row["pack"])
                self.assertEqual(row["pack"] in listed, evaluation_form(pack) == pack)

    def test_every_released_and_staged_row_holds_under_the_draft_selector(self) -> None:
        # Each released row, and each row staged after 0.3.0, keeps its expectation under the draft
        # when its pack's selector is replaced: the pack keeps its conformance result, and a
        # conforming one is its own evaluation form, so RFC 0031 §4.2 gives it Core 0.3.0's result.
        for base, path in ((EVALUATION, EVALUATION_MANIFEST_PATH), (EVALUATION_STAGED, EVALUATION_STAGED_CASES_PATH)):
            rows = strict_json_loads(path.read_text(encoding="utf-8"))["cases"]
            for row in rows:
                with self.subTest(row=row["id"]):
                    data = (base / row["pack"]).read_bytes()
                    self.assertEqual(1, data.count(RELEASED_SELECTOR))
                    pack = strict_json_loads(data.replace(RELEASED_SELECTOR, DRAFT_SELECTOR).decode("utf-8"))
                    diagnostics = draft_pack_diagnostics(self.validators, pack)
                    if row.get("expectedErrorClass") == "pack-not-conformant":
                        self.assertNotEqual([], diagnostics)
                    else:
                        self.assertEqual([], diagnostics)
                        self.assertEqual(pack, evaluation_form(pack))


def code_points(ranges: Iterable[tuple[int, int]]) -> set[int]:
    return {cp for low, high in ranges for cp in range(low, high + 1)}


def every_code_point() -> Iterable[int]:
    # Every scalar value: a surrogate is not a character a JSON string can hold alone.
    return (cp for cp in range(0x110000) if not 0xD800 <= cp <= 0xDFFF)


# A Node script that sweeps the schema's string pattern under ECMA-262 Unicode mode. It reads the
# schema with JSON.parse, so the surrogate-pair escapes decode as they do for any ECMA-262 validator.
NODE_SWEEP = r"""
const schema = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
const pattern = schema.$defs.annotationString.not.pattern;
const result = {};
try { new RegExp(pattern); result.withoutUnicodeMode = "compiles"; }
catch (error) { result.withoutUnicodeMode = error.name; }
for (const flags of ["u", "v"]) {
  let re;
  try { re = new RegExp(pattern, flags); } catch (error) { result[flags] = error.name; continue; }
  const found = {inner: [], lead: [], trail: []};
  for (let cp = 0; cp <= 0x10ffff; cp++) {
    if (cp >= 0xd800 && cp <= 0xdfff) continue;
    const c = String.fromCodePoint(cp);
    if (re.test("a" + c + "a")) found.inner.push(cp);
    if (re.test(c + "a")) found.lead.push(cp);
    if (re.test("a" + c)) found.trail.push(cp);
  }
  result[flags] = found;
}
console.log(JSON.stringify(result));
"""


def stated_code_points(text: str, opening: str) -> set[int]:
    """The code points a sentence lists, from `opening` to the full stop that ends it."""
    flat = " ".join(text.split())
    start = flat.index(opening) + len(opening)
    sentence = flat[start:flat.index(".", start)]
    ranges = [(int(low, 16), int(high or low, 16))
              for low, high in re.findall(r"U\+([0-9A-F]{4,5})(?:–U\+([0-9A-F]{4,5}))?", sentence)]
    return code_points(ranges)


class DraftCharacterRuleTests(unittest.TestCase):
    """RFC 0031 §1.4: what an annotation string refuses, checked against every code point."""

    def string_pattern(self) -> str:
        return draft_schema()["$defs"]["annotationString"]["not"]["pattern"]

    def expected(self) -> dict[str, list[int]]:
        anywhere = code_points(REFUSED_ANYWHERE)
        at_an_end = sorted(anywhere | code_points(WHITE_SPACE))
        return {"inner": sorted(anywhere), "lead": at_an_end, "trail": at_an_end}

    def test_the_schema_holds_the_two_patterns(self) -> None:
        defs = draft_schema()["$defs"]
        self.assertEqual({"type": "string", "pattern": STRING_PATTERN}, defs["annotationString"]["not"])
        self.assertEqual({"pattern": KEY_CLASS}, defs["annotations"]["propertyNames"]["not"])

    def test_the_rfc_and_the_draft_text_state_the_hand_written_code_points(self) -> None:
        for path in (ROOT / "rfcs" / "0031-annotations-and-value-sets.md", DRAFT_TEXT_PATH):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertEqual(code_points(REFUSED_ANYWHERE),
                                 stated_code_points(text, "The refused code points are exactly"))
                self.assertEqual(code_points(WHITE_SPACE), stated_code_points(text, "White_Space, which is exactly"))

    def test_python_re_refuses_exactly_the_stated_code_points(self) -> None:
        # The engine of the repository's validator: jsonschema's `pattern` is re.search.
        engine = re.compile(self.string_pattern())
        found: dict[str, list[int]] = {"inner": [], "lead": [], "trail": []}
        for cp in every_code_point():
            c = chr(cp)
            if engine.search("a" + c + "a"):
                found["inner"].append(cp)
            if engine.search(c + "a"):
                found["lead"].append(cp)
            if engine.search("a" + c):
                found["trail"].append(cp)
        self.assertEqual(self.expected(), found)

    def test_the_validator_refuses_each_range_edge_and_admits_its_neighbours(self) -> None:
        validator = Draft202012Validator(draft_schema()["$defs"]["annotationString"])
        anywhere = code_points(REFUSED_ANYWHERE)
        edges = {cp for low, high in REFUSED_ANYWHERE for cp in (low - 1, low, high, high + 1)} - {-1}
        for cp in sorted(edges):
            with self.subTest(code_point=f"U+{cp:04X}"):
                self.assertEqual(cp in anywhere, not validator.is_valid("a" + chr(cp) + "a"))
        for low, high in WHITE_SPACE:
            for cp in (low, high):
                with self.subTest(white_space=f"U+{cp:04X}"):
                    self.assertFalse(validator.is_valid(chr(cp) + "a"))
                    self.assertFalse(validator.is_valid("a" + chr(cp)))
                    self.assertFalse(validator.is_valid(chr(cp)))
                    self.assertEqual(cp in anywhere, not validator.is_valid("a" + chr(cp) + "a"))

    def test_ecma_262_unicode_mode_refuses_exactly_the_stated_code_points(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("no node on PATH; the ECMA-262 sweep needs Node 20 or later")
        found = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=60).stdout.strip()
        match = re.fullmatch(r"v(\d+)\.\d+\.\d+", found)
        if match is None or int(match.group(1)) < 20:
            self.skipTest(f"node {found or 'of an unknown version'} is on PATH; the v-flag sweep needs Node 20 or later")
        run = subprocess.run([node, "-e", NODE_SWEEP, str(DRAFT_SCHEMA_PATH)],
                             capture_output=True, text=True, timeout=600, check=True)
        result = json.loads(run.stdout)
        # Without Unicode mode the surrogate pairs are code units, and one range is out of order.
        self.assertEqual("SyntaxError", result["withoutUnicodeMode"])
        self.assertEqual(self.expected(), result["u"])
        self.assertEqual(self.expected(), result["v"])


# Issue #308: the four anchored grammars (a local identifier, an extension name, a pack version and a
# decimal operand), each code point before, inside and after a value, and strings of more than one
# line, where engines' anchors differ.
GRAMMAR_BASES = (("na", "me"), ("com.ex", "ample"), ("1.0", ".0"), ("12", ".5"))
GRAMMAR_LINES = (
    "name", "name\n", "name\r", "name\r\n", "name\u0085", "name\u2028", "name\u2029", "BAD\nname",
    "name\nBAD", "\nname", "com.example", "com.example\n", "com.example\r", "com.example\u2028",
    "BAD\ncom.example", "com.example\nBAD", "org.judgmentpack.annotations", "org.judgmentpack.future",
    "com.example\norg.judgmentpack.x", "org.judgmentpack.x\ncom.example", "org.judgmentpackx.y",
    "orgxjudgmentpack.y", "com.example-x", "com.example.a-b-", "com.-x", "a.b",
    "1.0.0", "1.0.0\n", "1.0.0\r", "x\n1.0.0", "1.0.0\nx", "01.0.0", "1.5", "1.5\n", "-0.5\r\n",
    "x\n1.5", "1.5\u2028", "-", "",
)
NODE_GRAMMAR_SWEEP = r"""
const schema = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
const [bases, lines] = JSON.parse(process.argv[2]);
const pairs = [schema.$defs.localId, schema.$defs.extensions.propertyNames, schema.properties.version,
               schema.$defs.decimalString];
const result = {};
for (const flags of ["u", "v"]) {
  let res;
  try { res = pairs.map(p => [new RegExp(p.pattern, flags), new RegExp(p.not.pattern, flags)]); }
  catch (error) { result[flags] = error.name; continue; }
  const admits = (g, s) => res[g][0].test(s) && !res[g][1].test(s);
  const found = {grammars: [], lines: lines.map(s => res.map((_, g) => admits(g, s)))};
  bases.forEach(([head, tail], g) => {
    const one = {lead: [], inner: [], trail: []};
    for (let cp = 0; cp <= 0x10ffff; cp++) {
      if (cp >= 0xd800 && cp <= 0xdfff) continue;
      const c = String.fromCodePoint(cp);
      if (admits(g, c + head + tail)) one.lead.push(cp);
      if (admits(g, head + c + tail)) one.inner.push(cp);
      if (admits(g, head + tail + c)) one.trail.push(cp);
    }
    found.grammars.push(one);
  });
  result[flags] = found;
}
console.log(JSON.stringify(result));
"""
LINE_TERMINATOR_CASES = (
    "structural-local-id-trailing-lf-id",
    "structural-local-id-trailing-lf-reference",
    "structural-extension-name-trailing-lf",
    "structural-extension-name-trailing-lf-annotated",
    "structural-required-extension-trailing-lf",
    "structural-pack-version-trailing-lf",
    "structural-decimal-operand-trailing-lf",
)
# Each grammar read as a whole-string match, written without an end anchor, and the reserved prefix
# read as a prefix (Core §§2.2, 4, 5 and 9).
WHOLE_STRING = (
    r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*",
    r"[a-z][a-z0-9]*(?:\.[a-z][a-z0-9-]*)+",
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)",
    r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?",
)


def grammar_sweep(admits: Any) -> dict[str, Any]:
    grammars = []
    for g, (head, tail) in enumerate(GRAMMAR_BASES):
        one: dict[str, list[int]] = {"lead": [], "inner": [], "trail": []}
        for cp in every_code_point():
            c = chr(cp)
            if admits(g, c + head + tail):
                one["lead"].append(cp)
            if admits(g, head + c + tail):
                one["inner"].append(cp)
            if admits(g, head + tail + c):
                one["trail"].append(cp)
        grammars.append(one)
    return {"grammars": grammars, "lines": [[admits(g, s) for g in range(len(GRAMMAR_BASES))] for s in GRAMMAR_LINES]}


class DraftAnchoredGrammarTests(unittest.TestCase):
    """Issue #308 (RFC 0031, Unresolved question 5, answered): no local identifier, extension name,
    pack version or decimal operand holds a line terminator, whatever an engine's anchors admit, and
    the patterns compile in every engine RFC 0031 §1.7 lists."""

    @staticmethod
    def whole_string(g: int, s: str) -> bool:
        matched = re.fullmatch(WHOLE_STRING[g], s) is not None
        return matched and not (g == 1 and s.startswith("org.judgmentpack."))

    def test_the_schema_holds_one_pattern_pair_per_grammar_at_every_position(self) -> None:
        schema = draft_schema()
        defs = schema["$defs"]
        self.assertEqual({"type": "string", "pattern": LOCAL_ID, "not": GRAMMAR_NOT}, defs["localId"])
        self.assertEqual({"type": "string", "pattern": PACK_VERSION, "not": GRAMMAR_NOT}, schema["properties"]["version"])
        self.assertEqual({"type": "string", "pattern": DECIMAL, "not": GRAMMAR_NOT}, defs["decimalString"])
        name = {"pattern": EXTENSION_NAME, "not": EXTENSION_NAME_NOT}
        self.assertEqual(name, defs["extensions"]["propertyNames"])
        self.assertEqual([{"const": ANNOTATIONS}, name], defs["annotatedExtensions"]["propertyNames"]["anyOf"])
        self.assertEqual({"type": "string", **name}, defs["metadata"]["properties"]["requiredExtensions"]["items"])
        self.assertNotIn("(?!", json.dumps(schema))

    def test_the_rfc_states_the_patterns(self) -> None:
        text = (ROOT / "rfcs" / "0031-annotations-and-value-sets.md").read_text(encoding="utf-8")
        section = text[text.index("**5. Line feeds before the end anchor"):]
        block = json.loads(re.search(r"^```json\n(.*?)^```$", section, re.M | re.S).group(1))
        schema = draft_schema()
        defs = schema["$defs"]
        self.assertEqual({
            "properties/version": schema["properties"]["version"],
            "$defs/localId": defs["localId"],
            "$defs/decimalString": defs["decimalString"],
            "$defs/extensions": defs["extensions"],
            "$defs/metadata/properties/requiredExtensions/items": defs["metadata"]["properties"]["requiredExtensions"]["items"],
        }, block)

    def admits_in_python(self) -> Any:
        # The engine of the repository's validator: jsonschema's `pattern` is re.search.
        schema = draft_schema()
        defs = schema["$defs"]
        holders = (defs["localId"], defs["extensions"]["propertyNames"], schema["properties"]["version"], defs["decimalString"])
        pairs = [(re.compile(holder["pattern"]), re.compile(holder["not"]["pattern"])) for holder in holders]
        return lambda g, s: bool(pairs[g][0].search(s)) and not pairs[g][1].search(s)

    def test_python_re_admits_exactly_the_whole_string_grammar(self) -> None:
        self.assertEqual(grammar_sweep(self.whole_string), grammar_sweep(self.admits_in_python()))

    def test_the_released_patterns_admit_a_final_line_feed_in_python_re(self) -> None:
        # What the `not` closes: each released grammar admits a final line feed where ECMA-262 refuses it.
        for g, (pattern, value) in enumerate(((LOCAL_ID, "name\n"), (RELEASED_EXTENSION_NAME, "com.example\n"),
                                              (PACK_VERSION, "1.0.0\n"), (DECIMAL, "1.5\n"))):
            with self.subTest(value=value.strip()):
                self.assertIsNotNone(re.search(pattern, value))
                self.assertFalse(self.admits_in_python()(g, value))

    def test_each_line_terminator_is_refused_once_at_every_position(self) -> None:
        validator = draft_validators()["base"]
        base = strict_json_loads((STAGED / "valid" / "annotations-one-element-list.json").read_text(encoding="utf-8"))
        name = "com.example.review-policy"
        for ending in ("\n", "\r", "\r\n", "\u0085", "\u2028", "\u2029"):
            positions = []
            pack = copy.deepcopy(base)
            pack["rules"][0]["id"] += ending
            positions.append((pack, "JPS-STRUCTURE-LOCAL-ID", "/rules/0/id"))
            pack = copy.deepcopy(base)
            pack["rules"][0]["outcome"] += ending
            positions.append((pack, "JPS-STRUCTURE-LOCAL-ID", "/rules/0/outcome"))
            pack = copy.deepcopy(base)
            pack["decision"]["extensions"] = {name + ending: {}}
            positions.append((pack, "JPS-STRUCTURE-EXTENSION-NAME", "/decision/extensions/" + name + ending))
            pack = copy.deepcopy(base)
            pack["rules"][0]["extensions"][name + ending] = {}
            positions.append((pack, "JPS-STRUCTURE-EXTENSION-NAME", "/rules/0/extensions/" + name + ending))
            pack = copy.deepcopy(base)
            pack["rules"][0]["extensions"][name] = {}
            pack["metadata"] = {"requiredExtensions": [name + ending]}
            positions.append((pack, "JPS-STRUCTURE-EXTENSION-NAME", "/metadata/requiredExtensions/0"))
            pack = copy.deepcopy(base)
            pack["version"] += ending
            positions.append((pack, "JPS-STRUCTURE-PACK-VERSION", "/version"))
            for pack, code, path in positions:
                with self.subTest(ending=ending.encode("unicode_escape").decode("ascii"), path=path.strip()):
                    self.assertEqual([(code, path)],
                                     [(d.code, d.path) for d in draft_structural_diagnostics(validator, pack)])
            # A decimal operand sits inside the condition's oneOf, where the corpus admits what a
            # validator reports for the other branches (assert_one_finding).
            pack = copy.deepcopy(base)
            pack["rules"][0]["when"] = {"op": "fact", "path": "/amount", "operator": "greater-than", "value": "10" + ending}
            with self.subTest(ending=ending.encode("unicode_escape").decode("ascii"), path="/rules/0/when/value"):
                assert_one_finding(self, "decimal operand", {"code": "JPS-STRUCTURE-DECIMAL-OPERAND", "path": "/rules/0/when/value"},
                                   draft_structural_diagnostics(validator, pack))

    def test_each_case_is_valid_without_its_line_feed(self) -> None:
        # Each case holds only the defect it names (issue #304): the same pack without the line feed
        # is valid under the draft selector, for a reader supporting the one vendor name the
        # required-name case lists.
        validators = draft_validators()
        manifest = strict_json_loads(STAGED_MANIFEST_PATH.read_text(encoding="utf-8"))
        cases = {case["id"]: case for case in manifest["cases"]}
        for case_id in LINE_TERMINATOR_CASES:
            with self.subTest(case=case_id):
                text = (STAGED / cases[case_id]["path"]).read_text(encoding="utf-8")
                self.assertEqual(1, text.count("\\n\""))
                self.assertEqual(("valid", []), draft_evaluate_text(text.replace("\\n\"", "\""), validators,
                                                                    ["com.example.review-policy"]))

    def test_ecma_262_unicode_mode_agrees_with_python_re(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("no node on PATH; the ECMA-262 sweep needs Node 20 or later")
        found = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=60).stdout.strip()
        match = re.fullmatch(r"v(\d+)\.\d+\.\d+", found)
        if match is None or int(match.group(1)) < 20:
            self.skipTest(f"node {found or 'of an unknown version'} is on PATH; the v-flag sweep needs Node 20 or later")
        run = subprocess.run([node, "-e", NODE_GRAMMAR_SWEEP, str(DRAFT_SCHEMA_PATH),
                              json.dumps([GRAMMAR_BASES, GRAMMAR_LINES])],
                             capture_output=True, text=True, timeout=600, check=True)
        result = json.loads(run.stdout)
        expected = grammar_sweep(self.whole_string)
        self.assertEqual(expected, result["u"])
        self.assertEqual(expected, result["v"])


class DraftSemanticReadingTests(unittest.TestCase):
    def test_extension_objects_are_the_schema_members_only(self) -> None:
        # RFC 0031 §4.1: a member named extensions inside an operand or an entry value is data.
        pack = strict_json_loads((STAGED / "semantic" / "required-extension-in-entry-value.json").read_text(encoding="utf-8"))
        self.assertEqual(set(), schema_extension_names(pack) & {"com.example.effective-window"})
        self.assertIn("com.example.effective-window", extension_names(pack))

    def test_the_reading_is_a_change_under_the_draft_selector_not_a_clarification(self) -> None:
        # Round-1 finding H3: the narrow reading takes effect under the draft selector. Neither text
        # may present it as a clarification of Core 0.3.0, whose released checker keeps the broad
        # reading (extension_names, above, is that checker's).
        for path in (ROOT / "rfcs" / "0031-annotations-and-value-sets.md", DRAFT_TEXT_PATH):
            flat = " ".join(path.read_text(encoding="utf-8").split())
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertIsNone(re.search(r"clarif\w* (?:of )?(?:released text|Core `0\.3\.0`)", flat))
        flat = " ".join(DRAFT_TEXT_PATH.read_text(encoding="utf-8").split())
        self.assertIn("This reading is a change that takes effect under this selector; it does not change "
                      "Core `0.3.0`.", flat)

    def test_evaluation_form_of_the_rfc_examples(self) -> None:
        positions = strict_json_loads((STAGED / "valid" / "annotations-positions.json").read_text(encoding="utf-8"))
        form = evaluation_form(positions)
        self.assertNotIn("extensions", form)
        self.assertNotIn("extensions", form["outcomes"][0])
        self.assertEqual({"com.example.authoring": {"draftedWith": "editor"}}, form["rules"][0]["extensions"])
        self.assertNotIn("extensions", form["rules"][1])
        empty = strict_json_loads((STAGED / "valid" / "annotations-empty-extensions.json").read_text(encoding="utf-8"))
        self.assertEqual({}, evaluation_form(empty)["rules"][0]["extensions"])


class DraftComparisonTests(unittest.TestCase):
    def test_findings_compare_as_a_set_of_code_and_pointer_pairs(self) -> None:
        # One keyword reported twice at one pointer is one finding; another pair is still a stray.
        path = "/rules/0/extensions/" + ANNOTATIONS
        twice = [Diagnostic("JPS-STRUCTURE-MIN-PROPERTIES", path, "first report"),
                 Diagnostic("JPS-STRUCTURE-MIN-PROPERTIES", path, "second report")]
        expected = {"code": "JPS-STRUCTURE-MIN-PROPERTIES", "path": path}
        assert_one_finding(self, "twice", expected, twice)
        with self.assertRaises(AssertionError):
            assert_one_finding(self, "stray", expected, twice + [Diagnostic("JPS-STRUCTURE-TYPE", path, "other")])
        validator = draft_validators()["base"]
        pack = strict_json_loads((STAGED / "structural" / "annotations-empty-object.json").read_text(encoding="utf-8"))
        (error,) = validator.iter_errors(pack)
        again = copy.copy(error)
        again.message = "the same keyword, reported again with another message"
        doubled = [error, again]
        reporting_twice = types.SimpleNamespace(iter_errors=lambda _value: iter(doubled))
        self.assertEqual([("JPS-STRUCTURE-MIN-PROPERTIES", path)],
                         [(d.code, d.path) for d in draft_structural_diagnostics(reporting_twice, pack)])


class DraftCoordinationTests(unittest.TestCase):
    OUTCOME_VALUES = "org.judgmentpack.outcome-values"

    def test_the_shape_drafted_for_rfc_0016_admits_both_names_on_an_outcome_only(self) -> None:
        # RFC 0031, Compatibility, "Coordination with RFC 0016": the definitions both records would
        # need, applied to the staged schema with a stand-in for RFC 0016's value definition.
        text = (ROOT / "rfcs" / "0031-annotations-and-value-sets.md").read_text(encoding="utf-8")
        section = text[text.index("**Coordination with RFC 0016.**"):]
        block = json.loads(re.search(r"^```json\n(.*?)^```$", section, re.M | re.S).group(1))
        self.assertEqual({"outcomeExtensions", "requiredExtensionName"}, set(block))
        schema = draft_schema()
        defs = schema["$defs"]
        vendor = defs["extensions"]["propertyNames"]
        self.assertEqual([{"enum": [ANNOTATIONS, self.OUTCOME_VALUES]}, vendor],
                         block["outcomeExtensions"]["propertyNames"]["anyOf"])
        self.assertEqual([{"const": self.OUTCOME_VALUES}, vendor], block["requiredExtensionName"]["anyOf"])
        defs.update(copy.deepcopy(block))
        defs["outcomeValues"] = {"type": "object"}
        defs["outcome"]["properties"]["extensions"] = {"$ref": "#/$defs/outcomeExtensions"}
        defs["metadata"]["properties"]["requiredExtensions"]["items"] = {"$ref": "#/$defs/requiredExtensionName"}
        validator = Draft202012Validator(schema, format_checker=FormatChecker())

        def refused_at(value: dict[str, Any]) -> list[list[Any]]:
            # A key's refusal names the key, as the code rule's pointers do.
            return [list(error.absolute_path) + ([error.instance] if "propertyNames" in error.absolute_schema_path else [])
                    for error in validator.iter_errors(value)]

        pack = strict_json_loads((STAGED / "valid" / "annotations-positions.json").read_text(encoding="utf-8"))
        pack["outcomes"][0]["extensions"][self.OUTCOME_VALUES] = {}
        pack.setdefault("metadata", {})["requiredExtensions"] = [self.OUTCOME_VALUES, "com.example.authoring"]
        self.assertEqual([], refused_at(pack))
        on_rule = copy.deepcopy(pack)
        on_rule["rules"][1]["extensions"] = {self.OUTCOME_VALUES: {}}
        self.assertEqual([("JPS-STRUCTURE-EXTENSION-NAME", "/rules/1/extensions/" + self.OUTCOME_VALUES)],
                         [(d.code, d.path) for d in draft_structural_diagnostics(validator, on_rule)])
        future = copy.deepcopy(pack)
        future["outcomes"][0]["extensions"]["org.judgmentpack.future"] = {}
        self.assertEqual([["outcomes", 0, "extensions", "org.judgmentpack.future"]], refused_at(future))
        requiring = copy.deepcopy(pack)
        requiring["metadata"]["requiredExtensions"].append(ANNOTATIONS)
        self.assertEqual([["metadata", "requiredExtensions", 2]], refused_at(requiring))
        # Evaluation-form step 3 removes only the annotations member: RFC 0016's stays, and so
        # does every name the pack requires.
        form = evaluation_form(pack)
        self.assertEqual({self.OUTCOME_VALUES: {}}, form["outcomes"][0]["extensions"])
        present = {name for holder in schema_extension_holders(form) for name in holder["extensions"]}
        self.assertLessEqual(set(pack["metadata"]["requiredExtensions"]), present)


class DraftPublicationTests(unittest.TestCase):
    STAGED_PATHS = (
        "schema/staged/judgment-pack-core-0.4.0-draft.schema.json",
        "spec/staged/judgment-pack-core-0.4.0-draft.md",
        "conformance/staged/manifest.json",
        "conformance/staged/README.md",
        "examples/staged/expense-approval-annotated.json",
        "conformance/evaluation/staged/annotations-value-sets/cases.json",
    )
    RELEASED_PATHS = ("schema/judgment-pack-core.schema.json", "spec/judgment-pack-core.md",
                      "conformance/manifest.json", "examples/minimal-expense-approval.json",
                      "schema", "spec", "conformance", "examples")

    def test_staged_paths_are_in_no_bundle(self) -> None:
        try:
            completed = subprocess.run(
                ["git", "check-attr", "export-ignore", "--", *self.STAGED_PATHS, *self.RELEASED_PATHS],
                cwd=ROOT, check=True, capture_output=True, text=True)
        except (OSError, subprocess.CalledProcessError) as error:
            self.skipTest(f"git cannot read attributes here: {error}")
        attributes = dict(line.rsplit(": export-ignore: ", 1) for line in completed.stdout.splitlines())
        for path in self.STAGED_PATHS:
            self.assertEqual("set", attributes[path], path)
        for path in self.RELEASED_PATHS:
            self.assertEqual("unspecified", attributes[path], path)

    def test_staged_artifacts_are_not_published_on_the_site(self) -> None:
        sys.path.insert(0, str(ROOT / "web"))
        import build  # noqa: PLC0415  (as tests/test_site.py imports it)
        for path in self.STAGED_PATHS:
            if path.endswith(".json"):
                self.assertFalse(build.is_published_artifact(Path(path)), path)
        self.assertTrue(build.is_published_artifact(Path("schema/judgment-pack-core.schema.json")))
        self.assertNotIn(str(DRAFT_SCHEMA_PATH.relative_to(ROOT)), build.CANONICAL_SCHEMA_SOURCES)
        self.assertNotIn(str(DRAFT_TEXT_PATH.relative_to(ROOT)), [page.source for page in build.PAGES])


if __name__ == "__main__":
    unittest.main()

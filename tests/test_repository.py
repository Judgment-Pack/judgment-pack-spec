from __future__ import annotations

import collections
import hashlib
import json
import json.scanner
import re
import tempfile
import unittest
from dataclasses import dataclass
from json.decoder import WHITESPACE, WHITESPACE_STR, JSONDecodeError, scanstring
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE = ROOT / "conformance"
SCHEMA_PATH = ROOT / "schema" / "judgment-pack-core.schema.json"
MANIFEST_PATH = CONFORMANCE / "manifest.json"
MANIFEST_SCHEMA_PATH = CONFORMANCE / "manifest.schema.json"
SPEC_PATH = ROOT / "spec" / "judgment-pack-core.md"
EVALUATION = CONFORMANCE / "evaluation"
EVALUATION_MANIFEST_PATH = EVALUATION / "manifest.json"
EVALUATION_MANIFEST_SCHEMA_PATH = EVALUATION / "manifest.schema.json"
# Rows written for the suiteVersion after the released one. They are in no corpus and no claim may
# cite them (conformance/evaluation/staged/README.md); they are held to the released case schema so
# that moving them into the manifest edits nothing.
EVALUATION_STAGED = EVALUATION / "staged"
EVALUATION_STAGED_CASES_PATH = EVALUATION_STAGED / "cases.json"
SPEC_VERSION = "0.5.0"
PREVIOUS_SPEC_VERSIONS = ("0.1.0-draft", "0.2.0-draft", "0.3.0")
SCHEMA_ID = f"https://judgmentpack.org/schema/{SPEC_VERSION}/judgment-pack-core.schema.json"
STATUS_VECTORS_PATH = ROOT / "tests" / "conformance-status-vectors.json"

# Core §9.2's reserved name, and the subschemas the code rule of the corpus keys on
# (conformance/README.md, "Codes"). Each is held only by a definition Core 0.5.0 adds or amends.
ANNOTATIONS = "org.judgmentpack.annotations"
LOCAL_ID = "^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"
# Core §9.2's class for annotation keys, and its pattern for annotation strings, as the schema holds
# them after JSON decoding.
KEY_CLASS = "[\u0000-\u001f\u007f-\u009f\u2028-\u202e]"
_WHITE_SPACE = "[\u0009-\u000d\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]"
STRING_PATTERN = (
    "[\u0000-\u001f\u007f-\u009f\u00ad\u034f\u061c\u115f\u1160\u17b4\u17b5\u180b-\u180f\u200b-\u200f"
    "\u2028-\u202e\u2060-\u206f\u3164\ufe00-\ufe0f\ufeff\uffa0\ufff0-\ufff8"
    "\U0001bca0-\U0001bca3\U0001d173-\U0001d17a\U000e0000-\U000e0fff]"
    f"|^{_WHITE_SPACE}|{_WHITE_SPACE}$"
)
# The two `not` subschemas: under an annotations object's propertyNames, whose instances are always
# strings, and in annotationString, where `type` keeps a non-string from failing it.
REFUSED_NOTS = ({"pattern": KEY_CLASS}, {"type": "string", "pattern": STRING_PATTERN})
# Core §§2.2, 4, 5 and 9: beside the local-identifier, pack-version, decimal-operand and
# extension-name grammars, a `not` refuses the class of an annotation key, so a value that ends in a
# line terminator is refused whatever an engine's anchors admit. The extension-name grammar's
# reserved prefix is in that `not`, not in a lookahead, and its class hyphen is escaped.
RELEASED_EXTENSION_NAME = "^(?!org\\.judgmentpack\\.)[a-z][a-z0-9]*(?:\\.[a-z][a-z0-9-]*)+$"
EXTENSION_NAME = "^[a-z][a-z0-9]*(?:\\.[a-z][a-z0-9\\-]*)+$"
GRAMMAR_NOT = {"type": "string", "pattern": KEY_CLASS}
PACK_VERSION = "^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$"
DECIMAL = "^-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?$"
GRAMMAR_CODES = {
    LOCAL_ID: "JPS-STRUCTURE-LOCAL-ID",
    PACK_VERSION: "JPS-STRUCTURE-PACK-VERSION",
    DECIMAL: "JPS-STRUCTURE-DECIMAL-OPERAND",
}
EXTENSION_NAME_NOT = {"type": "string", "pattern": "^org\\.judgmentpack\\.|" + KEY_CLASS}
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
    def __init__(self, member: str, path: str = ""):
        super().__init__(f"duplicate object member: {member}")
        self.member = member
        self.path = path


class UnpairedSurrogateError(ValueError):
    def __init__(self, message: str = "unpaired surrogate escape in JSON string"):
        super().__init__(message)


class NonJSONConstantError(ValueError):
    def __init__(self, token: str):
        super().__init__(f"non-JSON numeric constant: {token}")


@dataclass(frozen=True)
class Diagnostic:
    code: str
    path: str
    message: str


def pointer(parts: Iterable[Any]) -> str:
    encoded = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "" if not encoded else "/" + "/".join(encoded)


def rule_overlap_diagnostic_keywords(
    validator: Draft202012Validator, diagnostic: dict[str, Any]
) -> set[str]:
    """Return schema keywords plus Core §3.3.1's cross-item id invariant."""
    pending = list(validator.iter_errors(diagnostic))
    keywords = set()
    while pending:
        error = pending.pop()
        keywords.add(error.validator)
        pending.extend(error.context)
    rules = diagnostic.get("rules")
    if isinstance(rules, list):
        ids = [rule.get("id") for rule in rules if isinstance(rule, dict)]
        if len(ids) == len(rules) and len(ids) != len(set(ids)):
            keywords.add("distinct-rule-ids")
    return keywords


def assert_no_unpaired_surrogates(text: str) -> None:
    """Refuse JSON string escapes that do not form a valid surrogate pair (§2.1)."""
    in_string = False
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if not in_string:
            if c == '"':
                in_string = True
            i += 1
        else:
            if c == '"':
                in_string = False
                i += 1
            elif c == '\\':
                if i + 1 < n and text[i + 1] == 'u':
                    if i + 6 <= n:
                        val = int(text[i + 2 : i + 6], 16)
                        if 0xD800 <= val <= 0xDBFF:
                            if i + 12 <= n and text[i + 6 : i + 8] == "\\u":
                                low_val = int(text[i + 8 : i + 12], 16)
                                if 0xDC00 <= low_val <= 0xDFFF:
                                    i += 12
                                    continue
                            raise UnpairedSurrogateError(
                                f"unpaired high surrogate escape \\u{text[i + 2 : i + 6]}"
                            )
                        elif 0xDC00 <= val <= 0xDFFF:
                            raise UnpairedSurrogateError(
                                f"unpaired low surrogate escape \\u{text[i + 2 : i + 6]}"
                            )
                        else:
                            i += 6
                            continue
                i += 2
            else:
                i += 1


def strict_json_loads(text: str) -> Any:
    path_stack: list[Any] = []

    def custom_parse_object(
        s_and_end: tuple[str, int],
        strict: bool,
        scan_once: Any,
        object_hook: Any,
        object_pairs_hook: Any,
        memo: dict[Any, Any] | None = None,
        _w: Any = WHITESPACE.match,
        _ws: str = WHITESPACE_STR,
    ) -> tuple[dict[str, Any], int]:
        s, end = s_and_end
        pairs = []
        seen = set()
        if memo is None:
            memo = {}
        memo_get = memo.setdefault

        nextchar = s[end : end + 1]
        if nextchar != '"':
            if nextchar in _ws:
                end = _w(s, end).end()
                nextchar = s[end : end + 1]
            if nextchar == "}":
                return {}, end + 1
            elif nextchar != '"':
                raise JSONDecodeError("Expecting property name enclosed in double quotes", s, end)
        end += 1
        while True:
            key, end = scanstring(s, end, strict)
            key = memo_get(key, key)
            if key in seen:
                raise DuplicateMemberError(key, pointer(path_stack + [key]))
            seen.add(key)

            if s[end : end + 1] != ":":
                end = _w(s, end).end()
                if s[end : end + 1] != ":":
                    raise JSONDecodeError("Expecting ':' delimiter", s, end)
            end += 1

            try:
                if s[end] in _ws:
                    end += 1
                    if s[end] in _ws:
                        end = _w(s, end + 1).end()
            except IndexError:
                pass

            path_stack.append(key)
            try:
                value, end = scan_once(s, end)
            finally:
                path_stack.pop()

            pairs.append((key, value))

            try:
                nextchar = s[end]
                if nextchar in _ws:
                    end = _w(s, end + 1).end()
                    nextchar = s[end]
            except IndexError:
                nextchar = ""
            end += 1

            if nextchar == "}":
                break
            elif nextchar != ",":
                raise JSONDecodeError("Expecting ',' delimiter", s, end - 1)
            end = _w(s, end).end()
            nextchar = s[end : end + 1]
            end += 1
            if nextchar != '"':
                raise JSONDecodeError("Expecting property name enclosed in double quotes", s, end - 1)

        return dict(pairs), end

    def custom_parse_array(
        s_and_end: tuple[str, int],
        scan_once: Any,
        _w: Any = WHITESPACE.match,
        _ws: str = WHITESPACE_STR,
    ) -> tuple[list[Any], int]:
        s, end = s_and_end
        values = []
        nextchar = s[end : end + 1]
        if nextchar in _ws:
            end = _w(s, end).end()
            nextchar = s[end : end + 1]
        if nextchar == "]":
            return values, end + 1

        idx = 0
        while True:
            path_stack.append(idx)
            try:
                value, end = scan_once(s, end)
            finally:
                path_stack.pop()
            values.append(value)
            idx += 1

            nextchar = s[end : end + 1]
            if nextchar in _ws:
                end = _w(s, end).end()
                nextchar = s[end : end + 1]
            end += 1
            if nextchar == "]":
                break
            elif nextchar != ",":
                raise JSONDecodeError("Expecting ',' delimiter", s, end - 1)
            end = _w(s, end).end()
        return values, end

    def reject_constant(token: str) -> Any:
        raise NonJSONConstantError(token)

    decoder = json.JSONDecoder(parse_constant=reject_constant)
    decoder.parse_object = custom_parse_object
    decoder.parse_array = custom_parse_array
    decoder.scan_once = json.scanner.py_make_scanner(decoder)
    result = decoder.decode(text)
    assert_no_unpaired_surrogates(text)
    return result


def pointer_depth(ptr: str) -> int:
    return 0 if not ptr else ptr.count("/")


def pointer_contains(ancestor: str, descendant: str) -> bool:
    """Whether `descendant` lies at or under `ancestor` on JSON Pointer segment boundaries."""
    return descendant == ancestor or ancestor == "" or descendant.startswith(ancestor + "/")


# §N or §§N–M citations in conformance/manifest.json.
_SECTION_HEADING_RE = re.compile(r"^#{2,6}\s+(\d+(?:\.\d+)*)\b")
_SECTION_CITATION_PREFIX_RE = re.compile(r"^§+")
_RANGE_SEPARATOR = "–"


def spec_section_numbers() -> set[str]:
    """The section numbers that appear as headings in the Core specification."""
    numbers: set[str] = set()
    for line in SPEC_PATH.read_text(encoding="utf-8").splitlines():
        match = _SECTION_HEADING_RE.match(line)
        if match:
            numbers.add(match.group(1))
    return numbers


def parse_spec_section(spec_section: str) -> list[str]:
    """The individual section numbers named by one citation string.

    Handles single sections (``§4``, ``§7.4``) and ranges (``§§2–7``); both
    endpoints of a range are returned so each can be checked independently.
    """
    body = _SECTION_CITATION_PREFIX_RE.sub("", spec_section)
    return [part.strip() for part in body.split(_RANGE_SEPARATOR) if part.strip()]


def walk_schema_errors(error: Any) -> Iterable[Any]:
    yield error
    if str(error.validator) == "anyOf" and "propertyNames" in [str(p) for p in error.absolute_schema_path]:
        return  # one refusal, the key's: its branches are not separate findings
    for child in error.context:
        yield from walk_schema_errors(child)


def schema_diagnostic(error: Any) -> Diagnostic:
    """The corpus's code rule (conformance/README.md, "Codes"): the rules for the subschemas Core
    0.5.0 adds or amends, then the keyword rule every earlier corpus used."""
    validator = str(error.validator)
    schema_path = [str(part) for part in error.absolute_schema_path]
    instance_path = list(error.absolute_path)
    under_names = "propertyNames" in schema_path
    key = [error.instance] if under_names and isinstance(error.instance, str) else []

    def code(name: str, path: list[Any]) -> Diagnostic:
        return Diagnostic(name, pointer(path), error.message)

    # The two mapped refusals of the reference rule (§7.4), checked first so that a reference
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
        # grammar for engines whose `$` admits a final line feed, and takes its code (§9.2).
        if under_names:
            return code("JPS-STRUCTURE-LOCAL-ID", instance_path + key)
        return code("JPS-STRUCTURE-NOT", instance_path)
    if (
        validator == "not"
        and error.validator_value == GRAMMAR_NOT
        and isinstance(error.schema, dict)
        and error.schema.get("pattern") in GRAMMAR_CODES
    ):
        # The class repeats the grammar beside it, and takes that grammar's code.
        return code(GRAMMAR_CODES[error.schema["pattern"]], instance_path)
    if (validator == "not" and error.validator_value == EXTENSION_NAME_NOT) or (
        validator == "pattern" and error.validator_value == EXTENSION_NAME
    ):
        # The extension-name grammar, its reserved prefix and the class are one code, at the key
        # under propertyNames.
        return code("JPS-STRUCTURE-EXTENSION-NAME", instance_path + key)
    if (
        validator == "anyOf"
        and under_names
        and isinstance(error.validator_value, list)
        and error.validator_value[:1] == [{"const": ANNOTATIONS}]
    ):
        # A key refused by the extension-name grammar as a branch of an anyOf.
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
    return keyword_diagnostic(error)


def keyword_diagnostic(error: Any) -> Diagnostic:
    """The keyword rule of every corpus up to 0.3.0, which the 0.5.0 rule falls back to."""
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
            if "propertyNames" in schema_path and isinstance(error.instance, str):
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
    elif (
        validator == "type"
        and error.validator_value == "array"
        and instance_path[-1:] == ["value"]
    ):
        code = "JPS-STRUCTURE-IN-OPERAND"
    elif (
        validator == "type"
        and error.validator_value == "string"
        and isinstance(error.schema, dict)
        and error.schema.get("pattern") == r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$"
    ):
        code = "JPS-STRUCTURE-DECIMAL-OPERAND"
    elif validator == "minLength":
        code = "JPS-STRUCTURE-MIN-LENGTH"
    elif validator == "uniqueItems":
        code = "JPS-STRUCTURE-UNIQUE-ITEMS"
    elif validator == "const" and instance_path == ["specVersion"]:
        code = "JPS-STRUCTURE-SPEC-VERSION"
    elif validator in {"oneOf", "const", "enum"} and "condition" in "/".join(schema_path):
        code = "JPS-STRUCTURE-CONDITION-SHAPE"
    elif validator in {"not", "allOf"} and "exceptions" in schema_path:
        code = "JPS-STRUCTURE-EXCEPTION-SHAPE"
        if validator == "not" and isinstance(error.instance, dict):
            val = error.validator_value
            forbidden: list[str] = []
            if isinstance(val, dict):
                if "required" in val and isinstance(val["required"], list):
                    forbidden.extend(val["required"])
                elif "anyOf" in val and isinstance(val["anyOf"], list):
                    for branch in val["anyOf"]:
                        if (
                            isinstance(branch, dict)
                            and "required" in branch
                            and isinstance(branch["required"], list)
                        ):
                            forbidden.extend(branch["required"])
            for member in forbidden:
                if member in error.instance:
                    instance_path.append(member)
                    break
    else:
        suffix = validator.replace("_", "-").upper()
        code = f"JPS-STRUCTURE-{suffix}"
    return Diagnostic(code, pointer(instance_path), error.message)


def structural_diagnostics(validator: Draft202012Validator, value: Any) -> list[Diagnostic]:
    # Findings are a set of (code, pointer) pairs (conformance/README.md): a keyword reported twice
    # at one pointer, and a grammar and its `not` that both refuse one value, are one finding.
    diagnostics: list[Diagnostic] = []
    seen: set[tuple[str, str]] = set()
    for top_level in validator.iter_errors(value):
        for error in walk_schema_errors(top_level):
            item = schema_diagnostic(error)
            identity = (item.code, item.path)
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


def fact_conditions(value: dict[str, Any]) -> list[tuple[dict[str, Any], list[Any]]]:
    """Every fact condition in every condition position §3.3 names, with its path."""
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
    """The objects whose `extensions` member the schema defines, and that carry one (§9.1).

    A member named `extensions` inside an operand, an entry value or an extension's own value is
    data, not an `extensions` object. A value-set object has no such member (§6.9), and a pack whose
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


def extension_names(value: Any) -> set[str]:
    """The names a member called `extensions` holds anywhere in the document: the reading of the
    repository's 0.3.0 checker, kept for that version's corpus (Core §9.1)."""
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


def semantic_diagnostics(
    value: dict[str, Any],
    extension_names_of: Callable[[Any], set[str]] = schema_extension_names,
) -> list[Diagnostic]:
    """§3.3's checks. `extension_names_of` reads the names §9's required-extension rule may count.

    Core 0.5.0 counts only the `extensions` objects the schema defines as members (§9.1); the
    repository's 0.3.0 checker counted a member so named anywhere (`extension_names`).
    """
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
    used_extensions = extension_names_of(value)
    for index, required in enumerate(declared_required):
        if required not in used_extensions:
            diagnostics.append(
                Diagnostic(
                    "JPS-SEMANTIC-MISSING-REQUIRED-EXTENSION",
                    pointer(["metadata", "requiredExtensions", index]),
                    f"required extension has no value in the document: {required}",
                )
            )
    diagnostics.extend(duplicate_id_diagnostics(value, "valueSets"))
    declared_sets = {item["id"] for item in value.get("valueSets", [])}
    for condition, path in fact_conditions(value):
        if "valueSet" in condition and condition["valueSet"] not in declared_sets:
            diagnostics.append(
                Diagnostic(
                    "JPS-SEMANTIC-UNRESOLVED-VALUE-SET",
                    pointer(path + ["valueSet"]),
                    f"value-set reference does not resolve: {condition['valueSet']}",
                )
            )
    return diagnostics


def core_schema(profile: str = "base") -> dict[str, Any]:
    """The published schema, with Core §4.1's ceilings for `profile`.

    The published schema carries the base maxima. A reader supporting `extended` applies the
    extended value of every row, as tools/profile_validation.py does. Each base value is asserted
    before it is replaced, so a schema edit that moved one fails here instead of passing under a
    stale patch.
    """
    if profile not in ("base", "extended"):
        raise ValueError("unknown ceiling profile")
    schema = strict_json_loads(SCHEMA_PATH.read_text(encoding="utf-8"))
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


def core_validators() -> dict[str, Draft202012Validator]:
    return {
        profile: Draft202012Validator(core_schema(profile), format_checker=FormatChecker())
        for profile in ("base", "extended")
    }


def profile_of(value: Any) -> str:
    """The declared profile, for choosing ceilings; anything else is the schema's to refuse."""
    profile = value.get("profile", "base") if isinstance(value, dict) else "base"
    return profile if profile in ("base", "extended") else "base"


Validators = Draft202012Validator | Mapping[str, Draft202012Validator]


def validator_for(validators: Validators, value: Any) -> Draft202012Validator:
    """One validator, or the validator of the ceiling profile `value` declares (§4.1)."""
    if isinstance(validators, Mapping):
        return validators[profile_of(value)]
    return validators


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
    validators: Validators,
    supported_extensions: Iterable[str],
) -> tuple[str, list[Diagnostic]]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeError as error:
        return "invalid", [Diagnostic("JPS-CARRIER-INVALID-JSON", "", str(error))]
    return evaluate_text(text, validators, supported_extensions)


def evaluate_text(
    text: str,
    validators: Validators,
    supported_extensions: Iterable[str],
) -> tuple[str, list[Diagnostic]]:
    try:
        value = strict_json_loads(text)
    except DuplicateMemberError as error:
        return "invalid", [
            Diagnostic("JPS-CARRIER-DUPLICATE-MEMBER", error.path, str(error))
        ]
    except (UnicodeError, json.JSONDecodeError, UnpairedSurrogateError, NonJSONConstantError) as error:
        return "invalid", [Diagnostic("JPS-CARRIER-INVALID-JSON", "", str(error))]

    diagnostics = structural_diagnostics(validator_for(validators, value), value)
    if diagnostics:
        return "invalid", diagnostics

    diagnostics = semantic_diagnostics(value)
    if diagnostics:
        return "invalid", diagnostics

    diagnostics = unsupported_diagnostics(value, supported_extensions)
    if diagnostics:
        return "unsupported", diagnostics
    return "valid", []


def pack_conformance_diagnostics(validator: Validators, pack: Any) -> list[Diagnostic]:
    """Why a parsed pack is not a semantically conforming document (§3.3), or an empty list.

    The layers are ordered, as in `evaluate_case`: the semantic checks read a document the
    structural layer has already accepted, and are not run on one it refused. That is §3.3's own
    layering, and it is also what keeps this function total. `semantic_diagnostics` indexes into
    `outcomes`, `rules`, `evidenceRequirements` and `metadata` as the schema shapes them, so on a
    pack where one of those is `null` or a string it raises instead of reporting — and a fixture
    whose whole point is to be nonconforming is exactly where such a shape turns up.
    """
    diagnostics = structural_diagnostics(validator_for(validator, pack), pack)
    if diagnostics:
        return diagnostics
    return semantic_diagnostics(pack)


def assert_findings(
    test: unittest.TestCase,
    case_id: str,
    expected: list[dict[str, str]],
    diagnostics: list[Diagnostic],
) -> None:
    """The corpus's strictness: every expected finding, and no other outside the outermost oneOf
    that encloses one of them. Findings compare as a set of (code, pointer) pairs."""
    pairs = list(dict.fromkeys((d.code, d.path) for d in diagnostics))
    wanted = [(item["code"], item["path"]) for item in expected]
    for finding in wanted:
        test.assertIn(finding, pairs, f"case {case_id!r}: expected {finding}; got {pairs}")
    regions = []
    for _, path in wanted:
        enclosing = [
            d.path
            for d in diagnostics
            if d.code == "JPS-STRUCTURE-ONEOF" and pointer_contains(d.path, path)
        ]
        if enclosing:
            regions.append(min(enclosing, key=pointer_depth))
    strays = [
        pair
        for pair in pairs
        if pair not in wanted and not any(pointer_contains(region, pair[1]) for region in regions)
    ]
    test.assertEqual(
        [],
        strays,
        f"case {case_id!r} expected only {wanted}"
        + (f" and findings inside {regions}" if regions else "")
        + f", but got stray diagnostic(s): {strays}; all diagnostics: {pairs}",
    )


def expected_findings(case: dict[str, Any]) -> list[dict[str, str]]:
    """A case's expected findings: its `expectedDiagnostics`, or its one `expectedDiagnostic`."""
    if "expectedDiagnostics" in case:
        return case["expectedDiagnostics"]
    return [case["expectedDiagnostic"]]


# §8.4: the Core classes decided while admitting the inputs (§8.2), in the order they are evaluated.
PREFLIGHT_ERROR_CLASSES = (
    "pack-not-conformant",
    "malformed-input",
    "unsupported-required-extension",
)


def preflight_error_class(
    pack_diagnostics: list[Diagnostic], pack: Any, case: dict[str, Any]
) -> str | None:
    """The §8.4 class an evaluation case's own inputs call for, read without an evaluator.

    §8.4 evaluates the Core classes in one fixed order — `pack-not-conformant`, then
    `malformed-input`, then `unsupported-required-extension`, then `resource-exhaustion` — and the
    first that applies is the class reported. The first three are decided while admitting the inputs
    (§8.2), and whether each applies can be read off a case and its pack fixture: the pack conforms or
    does not, the evidence document names only declared requirements or does not, and the required
    extensions are all supported or are not. This carrier embeds `facts` as parsed JSON and holds
    evidence values to the tri-state, so an undeclared member name is the only malformed input a case
    can state; `resource-exhaustion` is reached while evaluating, which this repository cannot do.
    `None` therefore means nothing the case states refuses the inputs.

    This restates the order independently of any evaluator, so a row that pins the wrong class for
    its own inputs fails here rather than in whichever implementation happens to run it first.
    """
    if pack_diagnostics:
        return "pack-not-conformant"
    declared = {item["id"] for item in pack.get("evidenceRequirements", [])}
    if any(key not in declared for key in case.get("evidenceAvailability") or {}):
        return "malformed-input"
    required = set(pack.get("metadata", {}).get("requiredExtensions", []))
    if not required <= set(case["supportedExtensions"]):
        return "unsupported-required-extension"
    return None


class RepositoryConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = strict_json_loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.manifest_schema = strict_json_loads(
            MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        cls.manifest = strict_json_loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.validators = core_validators()
        cls.validator = cls.validators["base"]
        cls.manifest_registry = Registry().with_resource(
            SCHEMA_ID, Resource.from_contents(cls.schema)
        )

    def test_document_and_advisory_counts_match_the_manifest(self) -> None:
        """Every CURRENT statement separates conformance cases from advisories.

        The manifest is the authoritative index and these statements repeat its
        count by hand, so a corpus addition that misses one leaves a public
        page asserting a number the repository can disprove.

        This is deliberately a per-statement check rather than a search for the
        number: the repository uses the same value for the FAQ question count,
        which is a coincidence and not a fact about the corpus. Matching on the
        number alone would tie the two together, so that changing the corpus
        would demand editing the FAQ sentence. Historical statements in
        CHANGELOG.md and releases/ are also out of scope by design — they record
        what was true when published, and rewriting them would be falsifying a
        record rather than fixing a stale one.
        """
        advisory_count = sum(
            case["path"].startswith("advisory/") for case in self.manifest["cases"]
        )
        conformance_count = len(self.manifest["cases"]) - advisory_count
        self.assertEqual((369, 5), (conformance_count, advisory_count))
        statements = (
            (
                "README.md",
                "the repository contents table",
                f"| {conformance_count} document-conformance cases and "
                f"{advisory_count} advisory vectors",
            ),
            (
                "conformance/README.md",
                "the opening description",
                f"This directory contains {conformance_count} focused conformance cases",
            ),
            (
                "conformance/README.md",
                "the opening advisory count",
                "plus five advisory vectors",
            ),
            (
                "web/build.py",
                "the research-presentation note",
                f"Measured across {conformance_count} tests on the file format and "
                f"{advisory_count} advisory vectors",
            ),
            (
                "web/build.py",
                "the research-presentation summary",
                f"held in place by {conformance_count} tests on the format",
            ),
            (
                "web/build.py",
                "the research-presentation summary advisory count",
                f"{advisory_count} advisory vectors, and 103 tests on the answers",
            ),
        )
        for relative, where, expected in statements:
            with self.subTest(file=relative, statement=where):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn(
                    expected,
                    text,
                    f"{relative}: {where} no longer states the manifest's "
                    f"{conformance_count} document-conformance cases and "
                    f"{advisory_count} advisory vectors. Update that statement "
                    f"to match conformance/manifest.json, which is authoritative; "
                    f"do not change CHANGELOG.md, releases/, or the FAQ question "
                    f"count, which are out of scope.",
                )

    def test_pointer_escaping(self) -> None:
        cases = [
            ([], ""),
            (["rules", 0, "when"], "/rules/0/when"),
            (["a/b", "c~d"], "/a~1b/c~0d"),
        ]

        for parts, expected in cases:
            with self.subTest(parts=parts):
                self.assertEqual(pointer(parts), expected)

    def test_pointer_containment(self) -> None:
        cases = [
            ("", "", True),
            ("", "/rules", True),
            ("", "/rules/0/when", True),
            ("/rules/0/when", "/rules/0/when", True),
            ("/rules/0/when", "/rules/0/when/value", True),
            ("/rules/0/when", "/rules/0/whenever", False),
            ("/rules/0/when", "/rules/0", False),
            ("/rules/0/when", "", False),
            ("/rules/0", "/rules/00", False),
        ]

        for ancestor, descendant, expected in cases:
            with self.subTest(ancestor=ancestor, descendant=descendant):
                self.assertEqual(pointer_contains(ancestor, descendant), expected)

    def test_strict_json_loads_duplicate_member_detection(self) -> None:
        cases = [
            (
                "unique_members",
                '{"a": 1, "b": 2, "c": {"d": 3}}',
                {"a": 1, "b": 2, "c": {"d": 3}},
                None,
                None,
            ),
            (
                "duplicate_member_root",
                '{"a": 1, "b": 2, "a": 3}',
                None,
                "a",
                "/a",
            ),
            (
                "duplicate_member_nested",
                '{"a": 1, "b": {"c": 2, "c": 4}}',
                None,
                "c",
                "/b/c",
            ),
            (
                "same_member_separate_siblings",
                '{"a": {"x": 1}, "b": {"x": 2}}',
                {"a": {"x": 1}, "b": {"x": 2}},
                None,
                None,
            ),
        ]

        for name, text, expected_result, expected_duplicate_member, expected_path in cases:
            with self.subTest(case=name):
                if expected_duplicate_member is not None:
                    with self.assertRaises(DuplicateMemberError) as ctx:
                        strict_json_loads(text)
                    self.assertEqual(ctx.exception.member, expected_duplicate_member)
                    self.assertEqual(ctx.exception.path, expected_path)
                else:
                    self.assertEqual(strict_json_loads(text), expected_result)

    def test_strict_json_loads_unpaired_surrogate_detection(self) -> None:
        cases = [
            ("valid_string", '{"title": "valid string"}', True),
            ("valid_surrogate_pair_grinning_face", '{"title": "\\uD83D\\uDE00"}', True),
            ("valid_surrogate_pair_lowest_u10000", '{"title": "\\uD800\\uDC00"}', True),
            ("valid_surrogate_pair_highest_u10ffff", '{"title": "\\uDBFF\\uDFFF"}', True),
            ("mixed_case_pair", '{"title": "\\uD83d\\uDe00"}', True),
            ("valid_surrogate_in_member_name", '{"\\uD83D\\uDE00": 1}', True),
            ("escaped_backslash_before_u", '{"title": "\\\\uD800"}', True),
            ("lone_high_surrogate", '{"title": "\\uD800"}', False),
            ("lone_low_surrogate", '{"title": "\\uDC00"}', False),
            ("reversed_surrogate_pair", '{"title": "\\uDC00\\uD800"}', False),
            ("two_high_surrogates", '{"title": "\\uD800\\uD800"}', False),
            ("high_surrogate_followed_by_literal_abc", '{"title": "\\uD800abc"}', False),
            ("high_surrogate_followed_by_literal_A", '{"title": "\\uD800A"}', False),
            ("high_surrogate_followed_by_escaped_A", '{"title": "\\uD800\\u0041"}', False),
            ("high_plus_literal_plus_low", '{"title": "\\uD800x\\uDC00"}', False),
            ("high_plus_escape_plus_low", '{"title": "\\uD800\\n\\uDC00"}', False),
            ("high_plus_escaped_hex_plus_low", '{"title": "\\uD800\\u0041\\uDC00"}', False),
            ("pair_split_across_two_strings", '["\\uD800", "\\uDC00"]', False),
            ("pair_split_across_key_and_value", '{"\\uD800": "\\uDC00"}', False),
            ("unpaired_high_in_member_name", '{"\\uD800": 1}', False),
            ("unpaired_low_in_member_name", '{"\\uDC00": 1}', False),
        ]
        for name, text, should_pass in cases:
            with self.subTest(case=name):
                if should_pass:
                    self.assertIsNotNone(strict_json_loads(text))
                else:
                    with self.assertRaises(UnpairedSurrogateError):
                        strict_json_loads(text)

    def test_strict_json_loads_rejects_non_json_constants(self) -> None:
        for token in ("NaN", "Infinity", "-Infinity"):
            for text in (token, '{"value": ' + token + '}', '[' + token + ']'):
                with self.subTest(text=text):
                    with self.assertRaises(NonJSONConstantError):
                        strict_json_loads(text)

        self.assertEqual("NaN", strict_json_loads('"NaN"'))
        self.assertEqual(-1500.0, strict_json_loads("-1.5e3"))

    def test_evaluate_case_reports_non_json_constants_as_carrier_failures(self) -> None:
        text = (CONFORMANCE / "valid" / "minimal-expense-approval.json").read_text(
            encoding="utf-8"
        )
        self.assertEqual(1, text.count('"value": "employee-expense"'))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "non-json-constant.json"
            for token in ("NaN", "Infinity", "-Infinity"):
                for document in (
                    text.replace('"value": "employee-expense"', '"value": ' + token),
                    token,
                ):
                    with self.subTest(token=token, root=document == token):
                        path.write_text(document, encoding="utf-8")
                        result, diagnostics = evaluate_case(path, self.validators, [])
                        self.assertEqual("invalid", result)
                        self.assertEqual(
                            [("JPS-CARRIER-INVALID-JSON", "")],
                            [(item.code, item.path) for item in diagnostics],
                        )

    def test_schemas_are_valid_draft_2020_12(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        Draft202012Validator.check_schema(self.manifest_schema)
        self.assertEqual(self.schema["$id"], SCHEMA_ID)

    def test_manifest_matches_its_schema(self) -> None:
        validator = Draft202012Validator(
            self.manifest_schema,
            format_checker=FormatChecker(),
            registry=self.manifest_registry,
        )
        errors = sorted(validator.iter_errors(self.manifest), key=lambda item: list(item.path))
        self.assertEqual([], [error.message for error in errors])
        self.assertEqual(self.manifest["suiteVersion"], SPEC_VERSION)
        self.assertEqual(self.manifest["specVersion"], SPEC_VERSION)
        self.assertEqual("draft", self.manifest["status"])
        self.assertTrue(self.manifest["validationProfile"]["formatAssertionRequired"])
        self.assertTrue(self.manifest["validationProfile"]["rejectDuplicateObjectMembers"])
        diagnostic_validator = validator.evolve(
            schema={"$ref": "#/$defs/ruleOverlapDiagnostic"}
        )
        for case in self.manifest["cases"]:
            for diagnostic in case.get("expectedAdvisories", []):
                self.assertEqual(
                    set(), rule_overlap_diagnostic_keywords(diagnostic_validator, diagnostic)
                )

    def test_conformance_manifest_status_ladder_vectors(self) -> None:
        vectors = strict_json_loads(STATUS_VECTORS_PATH.read_text(encoding="utf-8"))
        schemas = (
            self.manifest_schema,
            strict_json_loads(
                EVALUATION_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8")
            ),
        )
        for schema in schemas:
            status_validator = Draft202012Validator(schema["properties"]["status"])
            for vector in vectors:
                with self.subTest(schema=schema["$id"], status=vector["status"]):
                    self.assertEqual(
                        vector["valid"], status_validator.is_valid(vector["status"])
                    )

    def test_core_schema_descriptions_name_their_spec_versions(self) -> None:
        paths = (SCHEMA_PATH,)  # Historical descriptions are frozen; trusted anchors test them.
        for path in paths:
            schema = strict_json_loads(path.read_text(encoding="utf-8"))
            version = schema["properties"]["specVersion"]["const"]
            self.assertEqual(
                f"Structural schema for {version}. Conformance does not establish truth, "
                "authority, safety, or operational fitness.",
                schema["description"],
            )

    def test_rule_overlap_advisory_vectors_cover_the_recommendation(self) -> None:
        self.assertEqual(["JPS-RULES-OVERLAP"], self.manifest["diagnosticVocabulary"]["advisory"])

        cases = {
            case["id"]: case
            for case in self.manifest["cases"]
            if case["path"].startswith("advisory/")
        }
        self.assertEqual(
            {
                "advisory-rules-overlap-exact",
                "advisory-rules-touching",
                "advisory-rules-overlap-same-outcome",
                "advisory-rules-exclusive-rewrite",
                "advisory-rules-overlap-not-excluded",
            },
            set(cases),
        )

        exact = cases["advisory-rules-overlap-exact"]["expectedAdvisories"]
        self.assertEqual(1, len(exact))
        diagnostic = exact[0]
        self.assertEqual("JPS-RULES-OVERLAP", diagnostic["code"])
        self.assertEqual("exact", diagnostic["certainty"])
        self.assertEqual(
            {"validate": "warning", "strict": "error", "publish": "block"},
            diagnostic["severity"],
        )
        self.assertEqual("/rules/0", diagnostic["path"])
        self.assertEqual(
            {"path": "/score", "from": "70", "fromInclusive": True},
            diagnostic["overlap"],
        )
        self.assertEqual({"score": "70"}, diagnostic["witnessFacts"])
        self.assertEqual(
            [
                {"id": "r-medium", "outcome": "medium"},
                {"id": "r-high", "outcome": "high"},
            ],
            diagnostic["rules"],
        )
        self.assertEqual("r-medium", diagnostic["suggestedRewrite"]["ruleId"])
        self.assertEqual("all", diagnostic["suggestedRewrite"]["when"]["op"])

        for case_id in (
            "advisory-rules-touching",
            "advisory-rules-overlap-same-outcome",
            "advisory-rules-exclusive-rewrite",
        ):
            self.assertEqual([], cases[case_id]["expectedAdvisories"])

        not_excluded = cases["advisory-rules-overlap-not-excluded"]["expectedAdvisories"]
        self.assertEqual(1, len(not_excluded))
        self.assertEqual("not-excluded", not_excluded[0]["certainty"])
        self.assertEqual(
            {"validate": "warning", "strict": "warning", "publish": "warning"},
            not_excluded[0]["severity"],
        )
        self.assertNotIn("overlap", not_excluded[0])
        self.assertNotIn("witnessFacts", not_excluded[0])

    def test_rule_overlap_manifest_members_and_values_are_exercised(self) -> None:
        import copy

        property_paths = (
            ("properties", "diagnosticVocabulary"),
            ("properties", "diagnosticVocabulary", "properties", "advisory"),
            ("$defs", "case", "properties", "expectedAdvisories"),
            ("$defs", "ruleOverlapDiagnostic", "properties", "code"),
            ("$defs", "ruleOverlapDiagnostic", "properties", "certainty"),
            ("$defs", "ruleOverlapDiagnostic", "properties", "severity"),
            ("$defs", "ruleOverlapDiagnostic", "properties", "path"),
            ("$defs", "ruleOverlapDiagnostic", "properties", "rules"),
            ("$defs", "ruleOverlapDiagnostic", "properties", "overlap"),
            ("$defs", "ruleOverlapDiagnostic", "properties", "witnessFacts"),
            ("$defs", "ruleOverlapDiagnostic", "properties", "effect"),
            ("$defs", "ruleOverlapDiagnostic", "properties", "suggestedRewrite"),
            (
                "$defs", "ruleOverlapDiagnostic", "properties", "severity",
                "properties", "validate",
            ),
            (
                "$defs", "ruleOverlapDiagnostic", "properties", "severity",
                "properties", "strict",
            ),
            (
                "$defs", "ruleOverlapDiagnostic", "properties", "severity",
                "properties", "publish",
            ),
            (
                "$defs", "ruleOverlapDiagnostic", "properties", "rules", "items",
                "properties", "id",
            ),
            (
                "$defs", "ruleOverlapDiagnostic", "properties", "rules", "items",
                "properties", "outcome",
            ),
            (
                "$defs", "ruleOverlapDiagnostic", "properties", "suggestedRewrite",
                "properties", "ruleId",
            ),
            (
                "$defs", "ruleOverlapDiagnostic", "properties", "suggestedRewrite",
                "properties", "when",
            ),
        )
        for property_path in property_paths:
            schema = copy.deepcopy(self.manifest_schema)
            parent = schema
            for part in property_path[:-1]:
                parent = parent[part]
            del parent[property_path[-1]]
            with self.subTest(member="/".join(property_path)):
                self.assertFalse(
                    Draft202012Validator(
                        schema, registry=self.manifest_registry
                    ).is_valid(self.manifest)
                )

        advisories = [
            advisory
            for case in self.manifest["cases"]
            for advisory in case.get("expectedAdvisories", [])
        ]
        self.assertEqual({"exact", "not-excluded"}, {item["certainty"] for item in advisories})
        self.assertEqual(
            {"warning", "error"},
            {item["severity"]["strict"] for item in advisories},
        )
        self.assertEqual(
            {"warning", "block"},
            {item["severity"]["publish"] for item in advisories},
        )

    def test_rule_overlap_diagnostic_negative_vectors(self) -> None:
        manifest = strict_json_loads(
            (CONFORMANCE / "advisory/diagnostic-negative/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("review", manifest["status"])
        self.assertEqual("§3.3.1", manifest["specSection"])
        self.assertEqual(2, len({case["id"] for case in manifest["controls"]}))
        self.assertEqual(3, len({case["id"] for case in manifest["cases"]}))

        validator = Draft202012Validator(
            self.manifest_schema, registry=self.manifest_registry
        ).evolve(
            schema={"$ref": "#/$defs/ruleOverlapDiagnostic"}
        )
        for control in manifest["controls"]:
            with self.subTest(control=control["id"]):
                self.assertEqual(
                    set(), rule_overlap_diagnostic_keywords(validator, control["diagnostic"])
                )

        for case in manifest["cases"]:
            with self.subTest(case=case["id"]):
                diagnostic = case["diagnostic"]
                self.assertIn(
                    case["expectedKeyword"],
                    rule_overlap_diagnostic_keywords(validator, diagnostic),
                )

    def test_rule_overlap_region_members_are_exercised(self) -> None:
        import copy

        manifest = strict_json_loads(
            (CONFORMANCE / "advisory/diagnostic-negative/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        controls = {case["id"]: case["diagnostic"] for case in manifest["controls"]}
        members = (
            (0, "path", "shared-values"),
            (0, "sharedValues", "shared-values"),
            (1, "path", "bounded-range"),
            (1, "from", "bounded-range"),
            (1, "fromInclusive", "bounded-range"),
            (1, "to", "bounded-range"),
            (1, "toInclusive", "bounded-range"),
        )
        for branch, member, control in members:
            schema = copy.deepcopy(self.manifest_schema)
            del schema["$defs"]["ruleOverlapDiagnostic"]["properties"]["overlap"][
                "oneOf"
            ][branch]["properties"][member]
            validator = Draft202012Validator(
                schema, registry=self.manifest_registry
            ).evolve(schema={"$ref": "#/$defs/ruleOverlapDiagnostic"})
            with self.subTest(branch=branch, member=member):
                self.assertFalse(validator.is_valid(controls[control]))

    def test_manifest_covers_every_fixture_once(self) -> None:
        case_ids = collections.Counter(case["id"] for case in self.manifest["cases"])
        for case_id, count in sorted(case_ids.items()):
            with self.subTest(case_id=case_id):
                self.assertEqual(1, count, f"case id {case_id!r} appears {count} times")

        paths = collections.Counter(case["path"] for case in self.manifest["cases"])
        for path, count in sorted(paths.items()):
            with self.subTest(path=path):
                self.assertEqual(1, count, f"case path {path!r} appears {count} times")

        for case in self.manifest["cases"]:
            with self.subTest(case_id=case["id"]):
                directory = Path(case["path"]).parts[0]
                if directory in ("advisory", "valid"):
                    self.assertEqual("semantic", case["layer"])
                    self.assertEqual("valid", case["expectedResult"])
                else:
                    self.assertEqual(case["layer"], directory)

        listed = set(paths.keys())
        on_disk = {
            path.relative_to(CONFORMANCE).as_posix()
            for path in CONFORMANCE.rglob("*.json")
            if not (path.name.endswith(".schema.json") or path.name in ("manifest.json", "cases.json"))
            and path.relative_to(CONFORMANCE).parts[0]
            not in ("evaluation", "witness", "dialect", "policy", "workflow", "retained-column", "staged",
                    "annotation-vocabulary")
        }

        for path in sorted(listed - on_disk):
            with self.subTest(missing=path):
                self.fail(f"case path {path!r} names no file")

        for path in sorted(on_disk - listed):
            with self.subTest(orphan=path):
                self.fail(f"fixture {path!r} is named by no case")

    def test_core_fixture_audit_keeps_orphans_and_unknown_namespaces_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            named = root / "valid/named.json"
            named.parent.mkdir()
            named.write_text("{}")
            for namespace in ("evaluation", "witness", "dialect", "policy", "workflow", "retained-column", "staged",
                              "annotation-vocabulary"):
                owned = root / namespace / "owned.json"
                owned.parent.mkdir()
                owned.write_text("{}")

            def audit():
                case = RepositoryConformanceTests("test_manifest_covers_every_fixture_once")
                case.manifest = {"cases": [{"id": "named", "path": "valid/named.json",
                                            "layer": "semantic", "expectedResult": "valid"}]}
                result = unittest.TestResult()
                with patch.dict(globals(), {"CONFORMANCE": root}):
                    case.run(result)
                self.assertEqual([], result.errors)
                return result

            self.assertTrue(audit().wasSuccessful())
            for relative in ("valid/orphan.json", "unknown-companion/orphan.json",
                             "policy-other/orphan.json"):
                orphan = root / relative
                orphan.parent.mkdir(exist_ok=True)
                orphan.write_text("{}")
                result = audit()
                self.assertEqual(1, len(result.failures))
                self.assertIn(f"fixture '{relative}' is named by no case", result.failures[0][1])
                orphan.unlink()
            named.unlink()
            result = audit()
            self.assertEqual(1, len(result.failures))
            self.assertIn("case path 'valid/named.json' names no file", result.failures[0][1])

    def test_conformance_cases_cite_existing_spec_sections(self) -> None:
        """Every document-conformance case's specSection resolves to a heading.

        A citation is the only link a fixture has back to the prose it defends;
        if the section number drifts or disappears, the case silently becomes
        misleading. The manifest schema only checks that the field starts with
        ``§``, so this test guards the cross-reference itself.
        """
        sections = spec_section_numbers()
        for case in self.manifest["cases"]:
            with self.subTest(case_id=case["id"]):
                for number in parse_spec_section(case["specSection"]):
                    self.assertIn(
                        number,
                        sections,
                        f"case {case['id']!r} cites spec section {number!r} "
                        f"which does not exist in {SPEC_PATH.name}",
                    )
    def test_conformance_cases_expect_diagnostics_from_their_layer(self) -> None:
        layer_families = {
            "carrier": {"CARRIER"},
            "structural": {"STRUCTURE"},
            "semantic": {"SEMANTIC", "CAPABILITY"},
        }
        for case in self.manifest["cases"]:
            expected = case["expectedDiagnostic"]
            if expected is None:
                continue
            with self.subTest(case_id=case["id"]):
                code = expected["code"]
                family = code.split("-")[1]
                layer = case["layer"]
                self.assertIn(
                    family,
                    layer_families.get(layer, set()),
                    f"case {case['id']!r} filed under layer {layer!r} expects diagnostic "
                    f"{code!r}, whose family {family!r} does not belong to that layer",
                )

    def test_conformance_cases(self) -> None:
        for case in self.manifest["cases"]:
            with self.subTest(case=case["id"]):
                case_path = (CONFORMANCE / case["path"]).resolve()
                try:
                    case_path.relative_to(CONFORMANCE.resolve())
                except ValueError:
                    self.fail(f"case path escapes conformance directory: {case['path']}")
                actual, diagnostics = evaluate_case(
                    case_path, self.validators, case.get("supportedExtensions", [])
                )
                self.assertEqual(
                    case["expectedResult"],
                    actual,
                    "\n".join(f"{item.code} {item.path}: {item.message}" for item in diagnostics),
                )
                if case["expectedDiagnostic"] is None:
                    self.assertEqual([], diagnostics)
                else:
                    assert_findings(self, case["id"], expected_findings(case), diagnostics)

    def test_more_than_one_expected_finding_is_stated_only_for_the_two_refusal_case(self) -> None:
        # The 0.5.0 case schema's expectedDiagnostics lists every finding of a case that gives more
        # than one. One case uses it: value beside valueSet under the operator equals, two Core §7.4
        # refusals of one condition, found at the condition and at its operator. Its expectedDiagnostic is the first item, so a consumer reading
        # only that member still reads a finding the case gives.
        listing = [case for case in self.manifest["cases"] if "expectedDiagnostics" in case]
        self.assertEqual(
            ["structural-value-set-reference-and-value-operator-equals"],
            [case["id"] for case in listing],
        )
        (case,) = listing
        self.assertEqual(
            [
                {"code": "JPS-STRUCTURE-VALUE-SET-REFERENCE", "path": "/rules/0/when"},
                {"code": "JPS-STRUCTURE-VALUE-SET-REFERENCE", "path": "/rules/0/when/operator"},
            ],
            case["expectedDiagnostics"],
        )
        self.assertEqual(case["expectedDiagnostics"][0], case["expectedDiagnostic"])
        # It is described as the two refusals it holds, not as one defect.
        self.assertNotIn("one defect", case["focus"])
        self.assertIn("two section 7.4 refusals of one condition", case["focus"])
        readme = " ".join((CONFORMANCE / "README.md").read_text(encoding="utf-8").split())
        self.assertIn("which holds two §7.4 refusals of one condition", readme)
        _, diagnostics = evaluate_case(CONFORMANCE / case["path"], self.validators, [])
        dropped = [d for d in diagnostics if d.path != "/rules/0/when/operator"]
        with self.assertRaises(AssertionError):
            assert_findings(self, case["id"], case["expectedDiagnostics"], dropped)

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

    def test_superseded_schemas_stay_published_for_their_own_versions(self) -> None:
        # A pack that keeps an older exact version remains checkable against that version's frozen
        # schema, while the live schema accepts only the current exact identifier.
        self.assertEqual(self.schema["properties"]["specVersion"]["const"], SPEC_VERSION)
        for version in PREVIOUS_SPEC_VERSIONS:
            with self.subTest(version=version):
                previous_path = (
                    ROOT / "schema" / f"judgment-pack-core-{version}.schema.json"
                )
                previous = strict_json_loads(previous_path.read_text(encoding="utf-8"))
                Draft202012Validator.check_schema(previous)
                self.assertEqual(
                    previous["$id"],
                    f"https://judgmentpack.org/schema/{version}/judgment-pack-core.schema.json",
                )
                self.assertEqual(previous["properties"]["specVersion"]["const"], version)

                # Each published document-conformance manifest schema keeps resolving too.
                manifest_path = (
                    ROOT / "schema" / f"conformance-manifest-{version}.schema.json"
                )
                previous_manifest = strict_json_loads(
                    manifest_path.read_text(encoding="utf-8")
                )
                Draft202012Validator.check_schema(previous_manifest)
                self.assertEqual(
                    previous_manifest["$id"],
                    f"https://judgmentpack.org/schema/{version}/conformance/manifest.schema.json",
                )
                self.assertEqual(
                    previous_manifest["properties"]["specVersion"]["const"], version
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
        self.assertEqual("draft", manifest["status"])
        self.assertEqual(manifest["label"], "seed")
        ids = collections.Counter(case["id"] for case in manifest["cases"])
        for case_id, count in sorted(ids.items()):
            with self.subTest(case_id=case_id):
                self.assertEqual(1, count, f"evaluation case id {case_id!r} appears {count} times")


    def test_evaluation_cases_are_well_formed_against_their_pack(self) -> None:
        manifest = strict_json_loads(EVALUATION_MANIFEST_PATH.read_text(encoding="utf-8"))
        self._check_evaluation_cases(manifest["cases"], EVALUATION)

    def _check_evaluation_cases(
        self,
        cases: list[dict[str, Any]],
        base: Path,
        validator: Validators | None = None,
        spec_version: str = SPEC_VERSION,
        conformance: Callable[[Validators, Any], list[Diagnostic]] = pack_conformance_diagnostics,
    ) -> None:
        # Carrier well-formedness only: the specification repository owns no evaluator, so these
        # checks verify that each case could be run, never that a disposition is the right one.
        # `base` is the directory a case's `pack` path resolves against: the released corpus, or the
        # staged rows beside it.
        #
        # §8.2 makes the pack input a semantically conforming document, so a pack fixture is required to
        # conform — except for a fixture whose whole point is the §8.4 `pack-not-conformant` error, which
        # requires the opposite. The check is therefore conditional on what the case expects rather than
        # dropped: a fixture that quietly became conforming would make such a row unrunnable too.
        #
        # `validator`, `spec_version` and `conformance` default to the released corpus's: a pack is
        # checked under the ceilings of the profile it declares (§4.1).
        validator = validator or self.validators
        non_conformant_packs = {
            case["pack"]
            for case in cases
            if case.get("expectedErrorClass") == "pack-not-conformant"
        }
        packs: dict[str, Any] = {}
        pack_diagnostics: dict[str, list[Diagnostic]] = {}
        for case in cases:
            with self.subTest(case=case["id"]):
                pack_path = (base / case["pack"]).resolve()
                try:
                    pack_path.relative_to(base.resolve())
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
                    diagnostics = conformance(validator, pack)
                    if expects_non_conformant_pack:
                        self.assertNotEqual(
                            [],
                            diagnostics,
                            f"{case['pack']} conforms, so no case can expect pack-not-conformant",
                        )
                    else:
                        self.assertEqual(pack["specVersion"], spec_version)
                        self.assertEqual([], diagnostics)
                    packs[case["pack"]] = pack
                    pack_diagnostics[case["pack"]] = diagnostics
                pack = packs[case["pack"]]

                for value in (case.get("evidenceAvailability") or {}).values():
                    self.assertIn(value, {"present", "absent", "unknown"})

                # An undeclared evidence key used to be refused here outright, because §8.2 makes it
                # an evaluation error and every row expected a disposition. A row whose point is that
                # error needs the key, so the check is conditional on what the case expects, exactly
                # as the pack-conformance check above is. That admits what the old check refused — a
                # correctly labelled error row — and asks more of everything it still covers: the
                # class a case expects must be the one §8.4's fixed order reports for the case's own
                # inputs, and a case whose inputs nothing refuses must not expect a preflight class
                # at all. A row that keeps its disposition and gains an undeclared key still fails.
                called_for = preflight_error_class(pack_diagnostics[case["pack"]], pack, case)
                expected_class = case.get("expectedErrorClass")
                if called_for is None:
                    # Nothing the case states refuses its inputs, so the three classes decided while
                    # admitting them are ruled out. Anything else stays the schema's business:
                    # `resource-exhaustion` is reached while evaluating, and §8.4 permits a documented
                    # implementation-defined class where no Core class applies, neither of which this
                    # repository can decide without an evaluator.
                    self.assertNotIn(
                        expected_class,
                        PREFLIGHT_ERROR_CLASSES,
                        "nothing this case states refuses its inputs, so §8.4 gives it no preflight "
                        "class to expect",
                    )
                else:
                    self.assertEqual(
                        called_for,
                        expected_class,
                        "§8.4 evaluates the classes in one fixed order and reports the first that "
                        "applies to the case's own inputs",
                    )

                self.assertEqual(
                    "expectedDisposition" in case,
                    "expectedErrorClass" not in case,
                    "a case states exactly one of expectedDisposition and expectedErrorClass",
                )
                disposition = case.get("expectedDisposition")
                if disposition is None:
                    continue

                disposition_validator = validator_for(validator, pack).evolve(
                    schema={"$ref": "#/$defs/disposition"}
                )
                self.assertEqual([], list(disposition_validator.iter_errors(disposition)))
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
                escalation = pack.get("escalation", {})
                triggers = set(escalation.get("triggers", []))
                requested_by = sorted(set(reasons) & (triggers | {"exception-escalation"}))
                if "routes" in escalation:
                    selected = [
                        route["target"] for route in escalation["routes"]
                        if requested_by and (
                            "triggers" not in route or set(route["triggers"]) & set(reasons)
                        )
                    ]
                    self.assertEqual(selected, handoff.get("routes"))
                    self.assertEqual("requested" if selected else "none", handoff["state"])
                    if selected:
                        self.assertEqual(requested_by, handoff.get("triggeredBy"))
                else:
                    self.assertNotIn("routes", handoff)
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

    def test_routes_schema_members_are_exercised(self) -> None:
        import copy
        pack = strict_json_loads((CONFORMANCE / "valid/escalation-routes.json").read_text())
        for member in ("routes", "target", "triggers"):
            schema = copy.deepcopy(self.schema)
            escalation = schema["$defs"]["escalation"]["properties"]
            if member == "routes":
                del escalation["routes"]
            else:
                del escalation["routes"]["items"]["properties"][member]
            with self.subTest(member=member):
                self.assertFalse(Draft202012Validator(schema).is_valid(pack))
        schema = copy.deepcopy(self.schema)
        del schema["$defs"]["disposition"]["properties"]["handoff"]["properties"]["routes"]
        case = next(c for c in self._staged_cases() if c["id"] == "routes-one")
        validator = Draft202012Validator(schema).evolve(schema={"$ref": "#/$defs/disposition"})
        self.assertFalse(validator.is_valid(case["expectedDisposition"]))

    def test_routes_schema_constraints_are_exercised(self) -> None:
        import copy
        mutations = [
            ("both", lambda e: e.pop("oneOf")),
            ("nine", lambda e: e["properties"]["routes"].pop("maxItems")),
            ("empty", lambda e: e["properties"]["routes"].pop("minItems")),
            ("outside-trigger", lambda e: e.pop("allOf")),
            ("empty-triggers", lambda e: e["properties"]["routes"]["items"]["properties"]["triggers"].pop("minItems")),
            ("missing-target", lambda e: e["properties"]["routes"]["items"].pop("required")),
            ("unknown-member", lambda e: e["properties"]["routes"]["items"].pop("additionalProperties")),
        ]
        for name, mutate in mutations:
            schema = copy.deepcopy(self.schema)
            fixture = strict_json_loads((CONFORMANCE / ("structural/escalation-routes-" + name + ".json")).read_text())
            with self.subTest(constraint=name):
                self.assertFalse(self.validator.is_valid(fixture))
                mutate(schema["$defs"]["escalation"])
                self.assertTrue(Draft202012Validator(schema).is_valid(fixture))

    def test_routes_expectation_mutations_are_caught(self) -> None:
        import copy
        cases = {c["id"]: c for c in self._staged_cases()}
        mutations = [
            ("routes-one", lambda h: h.update(routes=[])),
            ("routes-fan-out", lambda h: h["routes"].reverse()),
            ("routes-unconditional", lambda h: h.update(routes=[])),
            ("routes-no-selection", lambda h: h.update(state="requested", triggeredBy=["unknown"])),
            ("routes-duplicate-target", lambda h: h["routes"].pop()),
            ("routes-outcome-no-request", lambda h: h.update(routes=[{"kind": "queue", "name": "Conflict"}])),
        ]
        # subTest normally collects failures instead of raising: use a fresh case whose
        # outcome is unset, so assertRaises observes the deliberate invalid expectation.
        for name, mutate in mutations:
            case = copy.deepcopy(cases[name])
            mutate(case["expectedDisposition"]["handoff"])
            checker = RepositoryConformanceTests()
            checker.validator = self.validator
            with self.subTest(mutation=name), self.assertRaises(AssertionError):
                checker._check_evaluation_cases([case], EVALUATION_STAGED)

    def test_disposition_routes_state_negative_vectors(self) -> None:
        import copy
        manifest = strict_json_loads(
            (EVALUATION_STAGED / "disposition-negative/manifest.json").read_text()
        )
        self.assertEqual("staged", manifest["status"])
        self.assertEqual("§8.3", manifest["specSection"])
        self.assertEqual(4, len({case["id"] for case in manifest["cases"]}))
        for path in (SCHEMA_PATH, EVALUATION_MANIFEST_SCHEMA_PATH):
            schema = strict_json_loads(path.read_text())
            validator = Draft202012Validator(schema).evolve(schema={"$ref": "#/$defs/disposition"})
            for case in manifest["cases"]:
                with self.subTest(schema=path.name, case=case["id"]):
                    errors = list(validator.iter_errors(case["disposition"]))
                    self.assertEqual(
                        [(case["expectedKeyword"], ["handoff", "routes"])],
                        [(error.validator, list(error.path)) for error in errors],
                    )
                    corrected = copy.deepcopy(case["disposition"])
                    corrected["handoff"]["routes"] = case["correctedRoutes"]
                    self.assertEqual([], list(validator.iter_errors(corrected)))
                    del corrected["handoff"]["routes"]
                    self.assertEqual([], list(validator.iter_errors(corrected)))
                    weakened = copy.deepcopy(schema)
                    branch = "then" if case["expectedKeyword"] == "minItems" else "else"
                    del weakened["$defs"]["disposition"]["properties"]["handoff"]["allOf"][0][branch]["properties"]
                    permissive = Draft202012Validator(weakened).evolve(schema={"$ref": "#/$defs/disposition"})
                    self.assertTrue(permissive.is_valid(case["disposition"]))

    def test_routes_legacy_canonical_bytes(self) -> None:
        legacy = next(c for c in self._staged_cases() if c["id"] == "routes-legacy-target-bytes")
        released = strict_json_loads(EVALUATION_MANIFEST_PATH.read_text())["cases"]
        original = next(c for c in released if c["pack"] == legacy["pack"])
        # These dispositions contain only ASCII strings and no numbers, so this is JCS.
        canonical = lambda d: json.dumps(d, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(canonical(original["expectedDisposition"]), canonical(legacy["expectedDisposition"]))

    def test_evaluation_manifest_covers_every_pack_fixture_once(self) -> None:
        # Mirrors test_manifest_covers_every_fixture_once: a pack committed under packs/ and
        # referenced by no case would ship in the release bundle unexercised.
        manifest = strict_json_loads(EVALUATION_MANIFEST_PATH.read_text(encoding="utf-8"))
        listed = {case["pack"] for case in manifest["cases"]}
        on_disk = {
            f"packs/{path.relative_to(EVALUATION / 'packs').as_posix()}"
            for path in (EVALUATION / "packs").rglob("*.json")
            if not (path.name.endswith(".schema.json") or path.name in ("manifest.json", "cases.json"))
        }

        for path in sorted(listed - on_disk):
            with self.subTest(missing=path):
                self.fail(f"evaluation pack path {path!r} names no file")

        for path in sorted(on_disk - listed):
            with self.subTest(orphan=path):
                self.fail(f"evaluation pack fixture {path!r} is named by no case")



    def test_evaluation_pack_fixture_does_not_drift_from_the_example(self) -> None:
        example = (ROOT / "examples" / "data-request-intake-triage.json").read_bytes()
        fixture = (EVALUATION / "packs" / "data-request-intake-triage.json").read_bytes()
        self.assertEqual(example, fixture)

    def test_pack_conformance_diagnostics_is_layered_and_total(self) -> None:
        # The evaluation-case checks call this on every pack fixture, the deliberately nonconforming
        # ones included. It must report, never raise, whatever shape the pack has: a fixture written
        # to fail structurally is exactly where a member turns out to be `null` or a string.
        conforming = strict_json_loads(
            (EVALUATION / "packs" / "direct-exception-escalation.json").read_text(encoding="utf-8")
        )
        self.assertEqual([], pack_conformance_diagnostics(self.validator, conforming))

        for member, value in (
            ("evidenceRequirements", None),
            ("outcomes", None),
            ("rules", "not-an-array"),
            ("metadata", None),
            ("exceptions", 7),
        ):
            with self.subTest(member=member, value=value):
                broken = json.loads(json.dumps(conforming))
                broken[member] = value
                diagnostics = pack_conformance_diagnostics(self.validator, broken)
                self.assertTrue(diagnostics, "a structurally invalid pack reports why")
                self.assertTrue(
                    all(item.code.startswith("JPS-STRUCTURE-") for item in diagnostics),
                    [item.code for item in diagnostics],
                )

        # A structurally clean pack still reaches the semantic layer: a rule that names an outcome
        # the pack does not declare passes the schema and must be reported here.
        dangling = json.loads(json.dumps(conforming))
        dangling["rules"][0]["outcome"] = "undeclared-outcome"
        self.assertEqual([], structural_diagnostics(self.validator, dangling))
        semantic = pack_conformance_diagnostics(self.validator, dangling)
        self.assertTrue(semantic, "the semantic layer runs once the structural layer is clean")
        self.assertFalse(any(item.code.startswith("JPS-STRUCTURE-") for item in semantic))

    def _staged_cases(self) -> list[dict[str, Any]]:
        staged = strict_json_loads(EVALUATION_STAGED_CASES_PATH.read_text(encoding="utf-8"))
        return staged["cases"]

    def test_staged_evaluation_cases_match_the_released_case_schema(self) -> None:
        # Staged rows are written for the suiteVersion after the released one. They validate against
        # the released *case* schema unchanged, so moving a row into the manifest edits nothing, and
        # they carry no suiteVersion, because they belong to none.
        staged = strict_json_loads(EVALUATION_STAGED_CASES_PATH.read_text(encoding="utf-8"))
        self.assertEqual({"status", "stagedAfter", "caseSchema", "cases"}, set(staged))
        self.assertEqual("staged", staged["status"])
        self.assertEqual(SPEC_VERSION, staged["stagedAfter"])
        self.assertEqual("../manifest.schema.json#/$defs/case", staged["caseSchema"])
        self.assertTrue(staged["cases"], "a staged file with no case should be deleted instead")

        manifest_schema = strict_json_loads(
            EVALUATION_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        case_validator = Draft202012Validator(
            {
                "$schema": manifest_schema["$schema"],
                "$ref": "#/$defs/case",
                "$defs": manifest_schema["$defs"],
            },
            format_checker=FormatChecker(),
        )
        for case in staged["cases"]:
            with self.subTest(case=case.get("id")):
                errors = sorted(case_validator.iter_errors(case), key=lambda item: list(item.path))
                self.assertEqual([], [error.message for error in errors])

        staged_counts = collections.Counter(case["id"] for case in staged["cases"])
        for case_id, count in sorted(staged_counts.items()):
            with self.subTest(case_id=case_id):
                self.assertEqual(1, count, f"staged case id {case_id!r} appears {count} times")

        staged_ids = set(staged_counts.keys())
        manifest = strict_json_loads(EVALUATION_MANIFEST_PATH.read_text(encoding="utf-8"))
        released_ids = {case["id"] for case in manifest["cases"]}
        self.assertEqual(
            set(),
            staged_ids & released_ids,
            "a staged id that a released row already uses could not move into the manifest",
        )

    def test_staged_evaluation_cases_are_well_formed_against_their_pack(self) -> None:
        self._check_evaluation_cases(self._staged_cases(), EVALUATION_STAGED)

    def test_staged_cases_reference_every_staged_pack_fixture(self) -> None:
        # Every committed fixture is referenced, and every reference is committed. A fixture may be
        # referenced more than once — the precedence rows reuse the single-class rows' fixtures on
        # purpose — so this is set equality, not a count.
        listed = {case["pack"] for case in self._staged_cases()}
        on_disk = {
            f"packs/{path.relative_to(EVALUATION_STAGED / 'packs').as_posix()}"
            for path in (EVALUATION_STAGED / "packs").rglob("*.json")
            if not (path.name.endswith(".schema.json") or path.name in ("manifest.json", "cases.json"))
        }

        for path in sorted(listed - on_disk):
            with self.subTest(missing=path):
                self.fail(f"staged pack path {path!r} names no file")

        for path in sorted(on_disk - listed):
            with self.subTest(orphan=path):
                self.fail(f"staged fixture {path!r} is named by no case")


    def test_staged_copy_of_a_released_fixture_does_not_drift(self) -> None:
        # A staged case may reuse a released fixture, and a case's `pack` path resolves inside its own
        # directory, so the fixture is copied. The copy is the released bytes or it is a different
        # pack under the same name.
        shared = [
            path
            for path in (EVALUATION_STAGED / "packs").glob("*.json")
            if (EVALUATION / "packs" / path.name).is_file()
        ]
        self.assertTrue(shared, "no staged case reuses a released fixture; delete this test with the copy")
        for path in shared:
            with self.subTest(pack=path.name):
                self.assertEqual((EVALUATION / "packs" / path.name).read_bytes(), path.read_bytes())

    def test_staged_non_conformant_fixture_fails_for_its_one_stated_reason(self) -> None:
        # RFC 0013: "The pack must fail for one stated reason. A fixture that is invalid three ways
        # cannot show which one the class was reported for." One reason is not enough to hold: a
        # fixture that came to fail for a *different* single reason would leave its description, its
        # rows' focus and the adoption record false. The stated reason is one outcome where §4
        # requires two, so that is what is asserted.
        non_conformant = {
            case["pack"]
            for case in self._staged_cases()
            if case.get("expectedErrorClass") == "pack-not-conformant"
        }
        self.assertEqual({"packs/error-single-outcome.json"}, non_conformant)
        pack = strict_json_loads(
            (EVALUATION_STAGED / "packs" / "error-single-outcome.json").read_text(encoding="utf-8")
        )
        self.assertEqual(1, len(pack["outcomes"]))
        diagnostics = pack_conformance_diagnostics(self.validator, pack)
        self.assertEqual(
            [("JPS-STRUCTURE-COLLECTION-ARITY", "/outcomes")],
            [(item.code, item.path) for item in diagnostics],
        )
        # The semantic layer is not run on a document the structural layer refused, so the line
        # above cannot show that nothing is wrong *beneath* the stated reason — a rule naming an
        # outcome that does not exist, say. "Exactly one reason" is therefore held the other way
        # round as well: take the one reason away and the pack must conform at every layer.
        repaired = json.loads(json.dumps(pack))
        repaired["outcomes"].append(
            {"id": "hold", "label": "Hold", "description": "The synthetic request waits."}
        )
        self.assertEqual([], pack_conformance_diagnostics(self.validator, repaired))

    def test_relative_markdown_links_resolve(self) -> None:
        link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
        failures: list[str] = []
        # The dialect vectors are the Runner's bytes, its README among them, whose relative links
        # are relative to the Runner's repository: they are not this repository's to resolve or
        # to change (conformance/dialect/README.md).
        runners_bytes = (ROOT / "conformance" / "dialect" / "vectors").resolve()
        # A preserved v0.3.0 copy keeps its bytes, links relative to the path it was published at.
        preserved = (ROOT / "tests" / "fixtures" / "historical-compatibility" / "v0.3.0").resolve()
        for markdown_path in sorted(ROOT.rglob("*.md")):
            if ".git" in markdown_path.parts:
                continue
            if runners_bytes in markdown_path.resolve().parents or preserved in markdown_path.resolve().parents:
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


# The checkpoint witness vectors RFC 0017 proposed: the reference gateway's corpus/witness/ at
# v0.11.0, byte for byte. The RFC is accepted and its text landed as spec/checkpoint-witness.md; the
# vectors are staged, in no corpus, until the next specVersion opens (conformance/witness/README.md).
# The repository owns no reader, so nothing here verifies a
# signature or reads a chain: these tests hold the files to the digests the manifest records, each
# vector to the gateway's form, each manifest row to the vector it names, and every statement of the
# vectors' counts to the manifest.
WITNESS = CONFORMANCE / "witness"
WITNESS_VECTORS = WITNESS / "vectors"
WITNESS_MANIFEST_PATH = WITNESS / "manifest.json"
WITNESS_RFC = "rfcs/0017-checkpoint-witness-statement.md"
WITNESS_SOURCE = {
    "repository": "https://github.com/Judgment-Pack/judgment-pack-gateway",
    "tag": "v0.11.0",
    "commit": "13349cafe33bb7618567e47ce7f6e1a4224231b0",
    "path": "corpus/witness",
}
WITNESS_FAMILIES = (
    "valid",
    "begins-late",
    "equivocation",
    "head",
    "key",
    "signature",
    "trail",
    "malformed",
    "chain",
    "bound",
)
# RFC 0017 §9: the refusals and findings a reader reports, by the names the vectors use.
WITNESS_REFUSALS = {
    "keys-over-bound",
    "key-not-canonical",
    "key-small-order",
    "key-not-on-curve",
    "bytes-over-bound",
    "statements-over-bound",
}
WITNESS_FINDINGS = {
    "witness-malformed",
    "witness-signature-invalid",
    "witness-trail-mismatch",
    "witness-equivocation",
    "witness-chain-broken",
    "witness-head-unreached",
}
WITNESS_READING_MEMBERS = {
    "ok",
    "findings",
    "reading",
    "headIndex",
    "highestIndex",
    "latestCheckpoint",
    "conflicts",
    "retired",
}
HEX_32 = re.compile(r"[0-9a-f]{32}")
HEX_64 = re.compile(r"[0-9a-f]{64}")
WITNESSED_AT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")


def is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


class WitnessVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = strict_json_loads(WITNESS_MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.vectors = {
            row["path"]: strict_json_loads((WITNESS / row["path"]).read_text(encoding="utf-8"))
            for row in cls.manifest["cases"]
            if (WITNESS / row["path"]).is_file()
        }

    def test_manifest_names_its_status_proposal_and_source(self) -> None:
        self.assertEqual({"status", "proposedBy", "source", "cases"}, set(self.manifest))
        # "proposed" while RFC 0017 was a draft; since its acceptance "staged", as the staged
        # evaluation rows' cases.json says, until the next specVersion opens.
        self.assertEqual("staged", self.manifest["status"])
        self.assertEqual(WITNESS_RFC, self.manifest["proposedBy"])
        self.assertTrue((ROOT / WITNESS_RFC).is_file())
        self.assertEqual(WITNESS_SOURCE, self.manifest["source"])
        for row in self.manifest["cases"]:
            with self.subTest(row=row.get("id")):
                self._check_row_shape(row)

    def _assert_whole(self, pattern: re.Pattern[str], value: Any) -> None:
        # The form is the whole value: fullmatch, never search, so nothing may stand before or after.
        self.assertIsInstance(value, str)
        self.assertIsNotNone(
            pattern.fullmatch(value), f"{value!r} is not, as a whole, of the form {pattern.pattern}"
        )

    def _check_row_shape(self, row: dict[str, Any]) -> None:
        expected = {"id", "path", "family", "expectedResult", "sha256"}
        if row.get("expectedResult") == "findings":
            expected.add("expectedFindings")
        elif row.get("expectedResult") == "refused":
            expected.add("expectedRefusal")
        else:
            self.assertEqual("reading", row.get("expectedResult"))
        self.assertEqual(expected, set(row))
        self._assert_whole(HEX_64, row["sha256"])

    def test_vectors_are_the_gateways_bytes(self) -> None:
        # Every file under vectors/, of any name, is a row, and every row a file whose SHA-256 is the
        # one recorded from the gateway's release: a vector added, removed or changed by a byte fails.
        rows = self.manifest["cases"]
        self.assertEqual(len(rows), len({row["id"] for row in rows}), "a case id appears twice")
        self.assertEqual(len(rows), len({row["path"] for row in rows}), "a case path appears twice")
        listed = {row["path"] for row in rows}
        on_disk = {
            path.relative_to(WITNESS).as_posix() for path in WITNESS_VECTORS.rglob("*") if path.is_file()
        }
        self.assertEqual([], sorted(listed - on_disk), "rows that name no file")
        self.assertEqual([], sorted(on_disk - listed), "files that no row names")
        for row in rows:
            with self.subTest(path=row["path"]):
                self.assertTrue(row["path"].startswith("vectors/"))
                digest = hashlib.sha256((WITNESS / row["path"]).read_bytes()).hexdigest()
                self.assertEqual(row["sha256"], digest)

    def _check_file(self, value: Any) -> None:
        # A file is its text, or parts whose text is repeated `times` times, in order.
        if isinstance(value, str):
            return
        self.assertIsInstance(value, dict)
        self.assertEqual({"parts"}, set(value))
        self.assertTrue(value["parts"])
        for part in value["parts"]:
            self.assertEqual({"text", "times"}, set(part))
            self.assertIsInstance(part["text"], str)
            self.assertTrue(is_count(part["times"]) and part["times"] >= 1)

    def _check_expected(self, vector: dict[str, Any]) -> None:
        expected = vector["expected"]
        self.assertIsInstance(expected, dict)
        if "refused" in expected:
            self.assertEqual({"refused"}, set(expected))
            self.assertIn(expected["refused"], WITNESS_REFUSALS)
            return
        if expected.get("ok") is False:
            self.assertEqual({"ok", "findings"}, set(expected))
            self.assertIsInstance(expected["findings"], list)
            self.assertTrue(expected["findings"], "a reading that is not ok names a finding")
            self.assertLessEqual(set(expected["findings"]), WITNESS_FINDINGS)
            return
        self.assertEqual(WITNESS_READING_MEMBERS, set(expected))
        self.assertIs(True, expected["ok"])
        self.assertEqual([], expected["findings"])
        # Current with a head, historical without; the head's index exactly when there is a head.
        self.assertEqual("current" if "head" in vector else "historical", expected["reading"])
        if "head" in vector:
            self.assertTrue(is_count(expected["headIndex"]))
        else:
            self.assertIsNone(expected["headIndex"])
        self.assertTrue(is_count(expected["highestIndex"]))
        latest = expected["latestCheckpoint"]
        self.assertEqual({"index", "sequence", "witnessedAt"}, set(latest))
        self.assertTrue(is_count(latest["index"]))
        self.assertTrue(is_count(latest["sequence"]) and latest["sequence"] >= 1)
        self._assert_whole(WITNESSED_AT, latest["witnessedAt"])
        self.assertIsInstance(expected["conflicts"], list)
        self.assertTrue(all(is_count(item) for item in expected["conflicts"]))
        self.assertIsInstance(expected["retired"], bool)

    def _check_vector_form(self, path: str, vector: Any) -> None:
        self.assertIsInstance(vector, dict)
        required = {"name", "family", "note", "trail", "keys", "witness", "expected"}
        self.assertLessEqual(required, set(vector))
        self.assertLessEqual(set(vector), required | {"head"})
        self.assertEqual(Path(path).stem, vector["name"])
        self.assertIn(vector["family"], WITNESS_FAMILIES)
        self.assertTrue(isinstance(vector["note"], str) and vector["note"])
        self._assert_whole(HEX_32, vector["trail"])
        self.assertIsInstance(vector["keys"], list)
        for key in vector["keys"]:
            self._assert_whole(HEX_64, key)
        self.assertIsInstance(vector["witness"], list)
        for item in vector["witness"]:
            self._check_file(item)
        if "head" in vector:
            self._check_file(vector["head"])
        self._check_expected(vector)

    def test_vectors_have_the_gateways_form(self) -> None:
        for path, vector in sorted(self.vectors.items()):
            with self.subTest(path=path):
                self._check_vector_form(path, vector)

    def test_form_checks_refuse_a_value_inside_other_characters(self) -> None:
        # The control for the checks above: a trail, a key, a time or a digest with anything before
        # or after it, a newline included, fails the same checks the unaltered vector and row pass.
        path = "vectors/valid-one-statement.json"
        vector = self.vectors[path]
        row = next(row for row in self.manifest["cases"] if row["path"] == path)
        self._check_vector_form(path, vector)
        self._check_row_shape(row)

        def set_trail(altered: dict[str, Any], value: str) -> None:
            altered["trail"] = value

        def set_key(altered: dict[str, Any], value: str) -> None:
            altered["keys"][0] = value

        def set_time(altered: dict[str, Any], value: str) -> None:
            altered["expected"]["latestCheckpoint"]["witnessedAt"] = value

        members = (
            ("trail", vector["trail"], set_trail),
            ("keys[0]", vector["keys"][0], set_key),
            ("witnessedAt", vector["expected"]["latestCheckpoint"]["witnessedAt"], set_time),
        )
        affixes = (("INVALID", ""), ("", "!"), ("INVALID", "!"), ("", "\n"))
        for before, after in affixes:
            for member, value, assign in members:
                with self.subTest(member=member, before=before, after=after):
                    altered = json.loads(json.dumps(vector))
                    assign(altered, before + value + after)
                    with self.assertRaises(AssertionError):
                        self._check_vector_form(path, altered)
            with self.subTest(member="sha256", before=before, after=after):
                altered_row = dict(row, sha256=before + row["sha256"] + after)
                with self.assertRaises(AssertionError):
                    self._check_row_shape(altered_row)

    def test_rows_restate_their_vectors(self) -> None:
        for row in self.manifest["cases"]:
            with self.subTest(row=row["id"]):
                vector = self.vectors.get(row["path"])
                self.assertIsNotNone(vector, f"{row['path']} names no file")
                assert vector is not None
                self.assertEqual(vector["name"], row["id"])
                self.assertEqual(vector["family"], row["family"])
                expected = vector["expected"]
                if "refused" in expected:
                    self.assertEqual("refused", row["expectedResult"])
                    self.assertEqual(expected["refused"], row["expectedRefusal"])
                elif expected["ok"]:
                    self.assertEqual("reading", row["expectedResult"])
                else:
                    self.assertEqual("findings", row["expectedResult"])
                    self.assertEqual(sorted(set(expected["findings"])), row["expectedFindings"])

    def test_vector_counts_match_the_manifest(self) -> None:
        # The counts are repeated by hand in prose, so each statement of them is held here.
        rows = self.manifest["cases"]
        count = len(rows)
        families = collections.Counter(row["family"] for row in rows)
        self.assertEqual(set(WITNESS_FAMILIES), set(families), "a family with no vector, or an unknown one")
        statements = [
            ("conformance/witness/README.md", f"This directory holds {count} vectors"),
            ("conformance/README.md", f"holds the {count} vectors"),
            ("README.md", f"{count} checkpoint witness vectors"),
            (WITNESS_RFC, f"The vectors are the gateway's {count}, imported unchanged"),
        ]
        for family in WITNESS_FAMILIES:
            row = f"| `{family}` | {families[family]} |"
            statements.append(("conformance/witness/README.md", row))
            statements.append((WITNESS_RFC, row))
        for relative, expected in statements:
            with self.subTest(file=relative, statement=expected):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn(
                    expected,
                    " ".join(text.split()),
                    f"{relative} no longer states what conformance/witness/manifest.json holds",
                )


if __name__ == "__main__":
    unittest.main()

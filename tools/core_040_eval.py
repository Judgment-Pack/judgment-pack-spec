"""A second evaluator for Core `0.4.0`, written from the text.

It was written, before the release, from three texts and nothing else: Core `0.3.0`, the staged
delta of the working selector `0.4.0-draft` and RFC 0031 (rfcs/0031-annotations-and-value-sets.md).
Those texts are Core `0.4.0` now (spec/judgment-pack-core.md), and the section numbers below are
its. No other implementation was read, run or copied. Its authoring vendor is the texts' own, so it
is a second reading of the text, not a different vendor's.

What it is not: a product, a conformance claim, or evidence that an expectation is right.

What it does:

- admission of a pack (Core §§3.3 and 8.2): the carrier of Core §2.1, profile
  negotiation (Core §4.1, `base` only), the structural schema with format assertions (the
  one part reused from the repository: the schema file, applied by a general-purpose JSON Schema
  validator), and the semantic conditions of Core §3.3, written here;
- the preflight of the facts and evidence-availability documents and of the required extensions,
  in Core §8.2's order, which is §8.4's error precedence;
- the evaluation form `EF(P)` of Core §8.5: references expanded in entry order, `valueSets`
  removed, annotations removed from the root, outcomes and rules;
- Core §§7-8 over `EF(P)`: conditions, the ten resolution steps, the handoff of §8.1 and the
  disposition of §8.3.

Limits (Core §10). Every input: nesting deeper than MAX_NESTING, or a number literal longer than
MAX_NUMBER_LITERAL characters, is refused while admitting it. For the facts or evidence document
that is `malformed-input`; for the pack it is a carrier refusal, so `pack-not-conformant`, which
Core §8.4's order reports first (RFC 0031 leaves to Core whether `malformed-input` also applies to
the pack). Every number is compared exactly, so the open number question of Core §13 never arises
here. Evaluation: one work unit per condition node evaluated and one per operand item compared;
more than the work limit is the `resource-exhaustion` error. Expansion is charged per reference, as its inline twin is, and nothing
is charged for annotations, value-set objects or unreferenced entries (Core §10), because only
`EF(P)` is evaluated.

Profiles. Only `base` is supported. A pack declaring `extended` is refused with the one diagnostic
Core §4.1 names, `profile-unsupported`; Core §8.4 names no evaluation error class for it, so this
module reports that refusal and no class.

Usage:
    python tools/core_040_eval.py rows
    python tools/core_040_eval.py evaluate PACK FACTS [EVIDENCE] [--supported NAME]...
"""
from __future__ import annotations

import copy
import dataclasses
import json
import re
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
SELECTOR = "0.4.0"
SCHEMA_PATH = ROOT / "schema" / "judgment-pack-core.schema.json"
EVALUATION = ROOT / "conformance" / "evaluation"
ANNOTATIONS = "org.judgmentpack.annotations"

MAX_NESTING = 64
MAX_NUMBER_LITERAL = 1024
WORK_LIMIT = 1_000_000

PACK_NOT_CONFORMANT = "pack-not-conformant"
MALFORMED_INPUT = "malformed-input"
UNSUPPORTED_REQUIRED_EXTENSION = "unsupported-required-extension"
RESOURCE_EXHAUSTION = "resource-exhaustion"
PROFILE_UNSUPPORTED = "profile-unsupported"

EVIDENCE_STATES = ("present", "absent", "unknown")
DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")  # Core §2.2
INDEX = re.compile(r"0|[1-9][0-9]*")  # RFC 6901 array-index


# --- Carrier (Core §2.1) -------------------------------------------------------------------------

class CarrierError(ValueError):
    """The input is not a carrier-conforming JSON text."""


class LimitError(ValueError):
    """The input reached one of this module's documented document limits while being admitted."""


class Number:
    """A JSON number, kept as its literal and compared by mathematical value (Core §7.4).

    The key is a sign, a digit string without leading or trailing zeros, and an integer exponent
    (RFC 0031 §2.4), so no exponent is expanded and no binary floating point is involved.
    """

    __slots__ = ("literal", "key")
    _GRAMMAR = re.compile(r"(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?")

    def __init__(self, literal: str) -> None:
        match = self._GRAMMAR.fullmatch(literal)
        if match is None:
            raise CarrierError(f"not a JSON number: {literal!r}")
        sign, whole, fraction, exponent = match.groups()
        fraction = fraction or ""
        digits = (whole + fraction).lstrip("0")
        if not digits:
            self.key: tuple[int, str, int] = (0, "", 0)  # 0, -0, 0.0 and 0e9 are one value
        else:
            scale = int(exponent or "0") - len(fraction)
            stripped = digits.rstrip("0")
            self.key = (-1 if sign else 1, stripped, scale + len(digits) - len(stripped))
        self.literal = literal

    def __repr__(self) -> str:
        return f"Number({self.literal!r})"


def _number(literal: str) -> Number:
    if len(literal) > MAX_NUMBER_LITERAL:
        raise LimitError(f"a number literal of {len(literal)} characters")
    return Number(literal)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    names = [name for name, _ in pairs]
    if len(set(names)) != len(names):
        raise CarrierError("duplicate object member name")
    return dict(pairs)


def _constant(name: str) -> Any:
    raise CarrierError(f"{name} is not JSON")


_SURROGATE = re.compile("[\ud800-\udfff]")


def load_json(text: str | bytes) -> Any:
    """Parse one JSON text under Core §2.1, with numbers as exact `Number` values."""
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except UnicodeDecodeError as error:
            raise CarrierError("not UTF-8") from error
    try:
        value = json.loads(text, object_pairs_hook=_object, parse_int=_number, parse_float=_number,
                           parse_constant=_constant)
    except RecursionError as error:
        raise LimitError("nesting") from error
    except json.JSONDecodeError as error:
        raise CarrierError(str(error)) from error
    stack = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        if depth > MAX_NESTING:
            raise LimitError(f"nesting deeper than {MAX_NESTING}")
        if isinstance(item, str):
            if _SURROGATE.search(item):
                raise CarrierError("an unpaired surrogate escape")
        elif isinstance(item, dict):
            for name, member in item.items():
                if _SURROGATE.search(name):
                    raise CarrierError("an unpaired surrogate escape")
                stack.append((member, depth + 1))
        elif isinstance(item, list):
            stack.extend((member, depth + 1) for member in item)
    return value


def dump_json(value: Any) -> str:
    """A value read by load_json as JSON text, each number written as its own literal."""
    if isinstance(value, Number):
        return value.literal
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(name, ensure_ascii=False) + ":" + dump_json(member)
                              for name, member in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ",".join(dump_json(member) for member in value) + "]"
    return json.dumps(value, ensure_ascii=False)


def _schema_value(value: Any) -> Any:
    """The value a JSON Schema validator reads: exact numbers, as int or Decimal."""
    if isinstance(value, Number):
        literal = value.literal
        return int(literal) if re.fullmatch(r"-?[0-9]+", literal) else Decimal(literal)
    if isinstance(value, dict):
        return {name: _schema_value(member) for name, member in value.items()}
    if isinstance(value, list):
        return [_schema_value(member) for member in value]
    return value


# --- JSON values (Core §7.4) ---------------------------------------------------------------------

def _kind(value: Any) -> str:
    if value is None:
        return "null"
    if value is True or value is False:
        return "boolean"
    if isinstance(value, Number):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise TypeError(f"not a JSON value from load_json: {type(value).__name__}")


def json_equal(left: Any, right: Any) -> bool:
    """Core §7.4's type-preserving equality: no coercion, numbers by value, objects unordered."""
    kind = _kind(left)
    if kind != _kind(right):
        return False
    if kind == "number":
        return left.key == right.key
    if kind == "array":
        return len(left) == len(right) and all(json_equal(a, b) for a, b in zip(left, right))
    if kind == "object":
        return left.keys() == right.keys() and all(json_equal(left[name], right[name]) for name in left)
    return left == right


def resolve_pointer(document: Any, path: str) -> tuple[bool, Any]:
    """RFC 6901 against the facts document (Core §7.4): (found, value)."""
    if path == "":
        return True, document
    if not path.startswith("/"):
        return False, None
    current = document
    for token in path[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                return False, None
            current = current[token]
        elif isinstance(current, list):
            if not INDEX.fullmatch(token) or int(token) >= len(current):
                return False, None
            current = current[int(token)]
        else:
            return False, None
    return True, current


def pointer(parts: list[Any]) -> str:
    return "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts)


# --- Admission (Core §§3.1-3.3, 4.1, 9.1) --------------------------------------------------------

_SCHEMA_CACHE: dict[str, Any] = {}


def _schema() -> tuple[Any, dict[str, Any]]:
    if "validator" not in _SCHEMA_CACHE:
        from jsonschema import Draft202012Validator, FormatChecker

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        checker = FormatChecker()
        # Core §3.2: format keywords are assertions. A checker without them checks less than it
        # says, so refuse to run rather than admit what it cannot check.
        missing = {"uri", "date", "date-time"} - set(checker.checkers)
        if missing:
            raise RuntimeError(f"format assertions unavailable ({sorted(missing)}); install requirements-dev.txt")
        _SCHEMA_CACHE["validator"] = Draft202012Validator(schema, format_checker=checker)
        _SCHEMA_CACHE["schema"] = schema
        items = schema["$defs"]["metadata"]["properties"]["requiredExtensions"]["items"]
        _SCHEMA_CACHE["requirable"] = Draft202012Validator(items)
    return _SCHEMA_CACHE["validator"], _SCHEMA_CACHE["schema"]


def requirable(name: Any) -> bool:
    """Whether a conforming pack can list `name` in `metadata.requiredExtensions` (Core §8.2)."""
    _schema()
    return _SCHEMA_CACHE["requirable"].is_valid(name)


def condition_nodes(pack: dict[str, Any]) -> Iterator[tuple[dict[str, Any], list[Any]]]:
    """Every condition in every condition position (Core §3.3), with its path."""
    roots: list[tuple[Any, list[Any]]] = []
    if "applicability" in pack:
        roots.append((pack["applicability"], ["applicability"]))
    roots += [(rule["when"], ["rules", i, "when"]) for i, rule in enumerate(pack.get("rules", []))]
    roots += [(item["when"], ["exceptions", i, "when"]) for i, item in enumerate(pack.get("exceptions", []))]
    stack = list(reversed(roots))
    while stack:
        node, path = stack.pop()
        yield node, path
        if node["op"] in ("all", "any"):
            stack.extend(reversed([(child, path + ["conditions", i]) for i, child in enumerate(node["conditions"])]))
        elif node["op"] == "not":
            stack.append((node["condition"], path + ["condition"]))


def extension_objects(pack: Any, schema: dict[str, Any]) -> list[dict[str, Any]]:
    """The `extensions` objects of Core §9.1: members the schema defines on Core objects."""
    return [holder["extensions"] for holder in extension_holders(pack, schema)]


def extension_holders(pack: Any, schema: dict[str, Any]) -> list[dict[str, Any]]:
    """The Core objects whose `extensions` member is an `extensions` object (Core §9.1).

    The positions are read from the schema, not listed here: a walk of the instance beside the
    schema, through `properties`, `items` and plain `$ref`, that never enters a condition (whose
    schema is a `oneOf`) or a value typed `true`, so an operand or entry value is never read.
    """
    defs = schema["$defs"]
    kinds = {"#/$defs/extensions", "#/$defs/annotatedExtensions", "#/$defs/entryExtensions"}
    found: list[dict[str, Any]] = []

    def walk(instance: Any, node: Any) -> None:
        while isinstance(node, dict) and set(node) == {"$ref"}:
            node = defs[node["$ref"].rsplit("/", 1)[1]]
        if not isinstance(node, dict):
            return
        if isinstance(instance, dict):
            for name, member in instance.items():
                member_schema = node.get("properties", {}).get(name)
                if name == "extensions" and isinstance(member_schema, dict) and member_schema.get("$ref") in kinds:
                    if isinstance(member, dict):
                        found.append(instance)
                elif member_schema is not None:
                    walk(member, member_schema)
        elif isinstance(instance, list) and "items" in node:
            for member in instance:
                walk(member, node["items"])

    walk(pack, schema)
    return found


def semantic_findings(pack: dict[str, Any]) -> list[tuple[str, str]]:
    """Core §3.3, for a structurally conforming pack: (code, pointer) pairs.

    Codes are the corpus's provisional test metadata (conformance/manifest.json); Core names none.
    """
    findings: list[tuple[str, str]] = []
    ids: dict[str, set[str]] = {}
    for collection in ("outcomes", "rules", "evidenceRequirements", "sources", "exceptions", "valueSets"):
        seen: set[str] = set()
        for i, item in enumerate(pack.get(collection, [])):
            if item["id"] in seen:
                findings.append(("JPS-SEMANTIC-DUPLICATE-ID", pointer([collection, i, "id"])))
            seen.add(item["id"])
        ids[collection] = seen

    def check(value: str, collection: str, path: list[Any], code: str) -> None:
        if value not in ids[collection]:
            findings.append((code, pointer(path)))

    for i, rule in enumerate(pack["rules"]):
        check(rule["outcome"], "outcomes", ["rules", i, "outcome"], "JPS-SEMANTIC-UNRESOLVED-OUTCOME")
        for j, ref in enumerate(rule.get("evidenceRequirementRefs", [])):
            check(ref, "evidenceRequirements", ["rules", i, "evidenceRequirementRefs", j],
                    "JPS-SEMANTIC-UNRESOLVED-EVIDENCE")
        for j, ref in enumerate(rule.get("sourceRefs", [])):
            check(ref, "sources", ["rules", i, "sourceRefs", j], "JPS-SEMANTIC-UNRESOLVED-SOURCE")
    if "fallbackOutcome" in pack:
        check(pack["fallbackOutcome"], "outcomes", ["fallbackOutcome"], "JPS-SEMANTIC-UNRESOLVED-OUTCOME")
    for i, item in enumerate(pack.get("exceptions", [])):
        if "targetRule" in item:
            check(item["targetRule"], "rules", ["exceptions", i, "targetRule"], "JPS-SEMANTIC-UNRESOLVED-RULE")
        if "outcome" in item:
            check(item["outcome"], "outcomes", ["exceptions", i, "outcome"], "JPS-SEMANTIC-UNRESOLVED-OUTCOME")
        for j, ref in enumerate(item.get("sourceRefs", [])):
            check(ref, "sources", ["exceptions", i, "sourceRefs", j], "JPS-SEMANTIC-UNRESOLVED-SOURCE")
    for node, path in condition_nodes(pack):
        if node["op"] == "evidence-present":
            check(node["evidenceRequirement"], "evidenceRequirements", path + ["evidenceRequirement"],
                    "JPS-SEMANTIC-UNRESOLVED-EVIDENCE")
        elif node["op"] == "fact" and "valueSet" in node:
            check(node["valueSet"], "valueSets", path + ["valueSet"], "JPS-SEMANTIC-UNRESOLVED-VALUE-SET")
    _, schema = _schema()
    present = {name for extensions in extension_objects(pack, schema) for name in extensions}
    for i, name in enumerate(pack.get("metadata", {}).get("requiredExtensions", [])):
        if name not in present:
            findings.append(("JPS-SEMANTIC-MISSING-REQUIRED-EXTENSION", pointer(["metadata", "requiredExtensions", i])))
    return findings


@dataclasses.dataclass
class Admission:
    """A pack's admission. `layer` is the first failing layer, or None when admitted."""

    pack: Any = None
    layer: str | None = None
    findings: list[tuple[str, str]] = dataclasses.field(default_factory=list)
    detail: str = ""
    profile: str | None = None


def admit_pack(text: str | bytes) -> Admission:
    """Carrier, profile negotiation, structure and semantics, in that order (Core §§3.1-3.3, 4.1)."""
    try:
        pack = load_json(text)
    except (CarrierError, LimitError) as error:
        return Admission(layer="carrier", detail=str(error))
    # Core §4.1: profile negotiation comes after only the parsing needed to find the declaration.
    if isinstance(pack, dict) and pack.get("profile") == "extended":
        return Admission(pack=pack, layer="profile", detail=PROFILE_UNSUPPORTED, profile="extended")
    validator, _ = _schema()
    try:
        errors = [error.message for error in validator.iter_errors(_schema_value(pack))]
    except RecursionError:
        return Admission(pack=pack, layer="carrier", detail="nesting")
    if errors:
        return Admission(pack=pack, layer="structural", detail=errors[0])
    findings = semantic_findings(pack)
    if findings:
        return Admission(pack=pack, layer="semantic", findings=findings)
    return Admission(pack=pack)


def admit_document(text: str | bytes, supported: Any = ()) -> tuple[str, Admission]:
    """A document case's result: valid, invalid, unsupported (Core §9) or profile-unsupported."""
    admission = admit_pack(text)
    if admission.layer == "profile":
        return PROFILE_UNSUPPORTED, admission
    if admission.layer is not None:
        return "invalid", admission
    missing = _unsupported(admission.pack, supported)
    if missing:
        admission.findings = [("JPS-CAPABILITY-REQUIRED-EXTENSION", pointer(["metadata", "requiredExtensions", i]))
                              for i in missing]
        return "unsupported", admission
    return "valid", admission


def _unsupported(pack: dict[str, Any], supported: Any) -> list[int]:
    # Core §8.2: a name no conforming pack can list is not a capability; it is ignored.
    capabilities = {name for name in supported if requirable(name)}
    required = pack.get("metadata", {}).get("requiredExtensions", [])
    return [i for i, name in enumerate(required) if name not in capabilities]


# --- The evaluation form (Core §8.5) -------------------------------------------------------------

def evaluation_form(pack: dict[str, Any]) -> dict[str, Any]:
    """EF(P) of a semantically conforming pack. A reference is resolved to its set's one array of
    entry values, shared by every reference to that set rather than copied (Core §10)."""
    form = copy.deepcopy(pack)
    arrays = {item["id"]: [entry["value"] for entry in item["entries"]] for item in form.get("valueSets", [])}
    for node, _ in condition_nodes(form):
        if node["op"] == "fact" and "valueSet" in node:
            node["value"] = arrays[node.pop("valueSet")]
    form.pop("valueSets", None)
    for holder in [form, *form["outcomes"], *form["rules"]]:
        extensions = holder.get("extensions")
        if isinstance(extensions, dict) and ANNOTATIONS in extensions:
            del extensions[ANNOTATIONS]
            if not extensions:
                del holder["extensions"]
    return form


# --- Evaluation (Core §§7-8) ---------------------------------------------------------------------

class _Exhausted(Exception):
    pass


class _Run:
    def __init__(self, facts: Any, evidence: dict[str, str], work_limit: int) -> None:
        self.facts = facts
        self.evidence = evidence
        self.work_limit = work_limit
        self.work = 0

    def charge(self, units: int = 1) -> None:
        self.work += units
        if self.work > self.work_limit:
            raise _Exhausted()

    def condition(self, node: dict[str, Any]) -> bool | None:
        """Core §7: True, False, or None for unknown."""
        self.charge()
        op = node["op"]
        if op == "literal":
            return node["value"]
        if op in ("all", "any"):
            values = [self.condition(child) for child in node["conditions"]]
            decisive, other = (False, True) if op == "all" else (True, False)
            if decisive in values:
                return decisive
            if all(value is other for value in values):
                return other
            return None
        if op == "not":
            value = self.condition(node["condition"])
            return None if value is None else not value
        if op == "evidence-present":
            return {"present": True, "absent": False}.get(self.evidence.get(node["evidenceRequirement"], "unknown"))
        return self.fact(node)

    def fact(self, node: dict[str, Any]) -> bool | None:
        found, selected = resolve_pointer(self.facts, node["path"])
        if not found:
            return None
        operator, operand = node["operator"], node["value"]
        if operator == "in":
            self.charge(len(operand))
            return any(json_equal(selected, item) for item in operand)
        if operator in ("equals", "not-equals"):
            self.charge()
            return json_equal(selected, operand) is (operator == "equals")
        self.charge()
        if not (isinstance(selected, str) and isinstance(operand, str)
                and DECIMAL.fullmatch(selected) and DECIMAL.fullmatch(operand)):
            return None
        left, right = Fraction(selected), Fraction(operand)
        return {"greater-than": left > right, "greater-than-or-equal": left >= right,
                "less-than": left < right, "less-than-or-equal": left <= right}[operator]


def _handoff(escalation: dict[str, Any] | None, reasons: set[str], direct: bool) -> dict[str, Any]:
    """Core §§8.1 and 8.3."""
    triggers = set(escalation["triggers"]) if escalation else set()
    matched = reasons & triggers
    requested = bool(matched) or direct
    triggered_by = sorted(matched | ({"exception-escalation"} if direct else set()))
    if escalation is not None and "routes" in escalation:
        selected = [copy.deepcopy(route["target"]) for route in escalation["routes"]
                    if requested and ("triggers" not in route or set(route["triggers"]) & reasons)]
        if selected:
            return {"state": "requested", "triggeredBy": triggered_by, "routes": selected}
        return {"state": "none", "routes": []}
    if requested:
        return {"state": "requested", "triggeredBy": triggered_by}
    return {"state": "none"}


def _disposition(form: dict[str, Any], kind: str, outcome: str | None, reasons: set[str],
                 direct: bool) -> dict[str, Any]:
    result: dict[str, Any] = {"kind": kind}
    if kind == "outcome":
        result["outcomeId"] = outcome
    result["reasons"] = sorted(reasons)
    result["handoff"] = _handoff(form.get("escalation"), reasons, direct)
    return result


def resolve(form: dict[str, Any], run: _Run) -> dict[str, Any]:
    """Core §8's ten steps over an evaluation form."""
    # Step 1.
    applicable = run.condition(form.get("applicability", {"op": "literal", "value": True}))
    if applicable is False:
        return _disposition(form, "not-applicable", None, {"not-applicable"}, False)
    if applicable is None:
        return _disposition(form, "unresolved", None, {"unknown"}, False)
    reasons: set[str] = set()
    # Step 2.
    presence = [run.evidence.get(item["id"], "unknown") for item in form.get("evidenceRequirements", [])
                if item["required"]]
    evidence_blocks = "absent" in presence or "unknown" in presence
    if "absent" in presence:
        reasons.add("missing-required-evidence")
    elif "unknown" in presence:
        reasons.add("unknown")
    # Steps 3 and 4.
    suppressed: set[str] = set()
    forced: set[str] = set()
    direct = False
    unknown_escalates = False
    for item in form.get("exceptions", []):
        value = run.condition(item["when"])
        if value is None:
            if item["onUnknown"] == "escalate":
                unknown_escalates = True
                reasons.add("unknown")
        elif value:
            if item["effect"] == "suppress-rule":
                suppressed.add(item["targetRule"])
            elif item["effect"] == "force-outcome":
                forced.add(item["outcome"])
            else:
                direct = True
    if direct:
        reasons.add("exception-escalation")
    # Step 5.
    forced_conflict = len(forced) > 1
    if forced_conflict:
        reasons.add("conflict")
    if evidence_blocks or unknown_escalates or forced_conflict or direct:
        return _disposition(form, "unresolved", None, reasons, direct)
    # Step 6.
    if forced:
        return _disposition(form, "outcome", next(iter(forced)), set(), False)
    # Steps 7 and 8.
    candidates: set[str] = set()
    for rule in form["rules"]:
        if rule["id"] in suppressed:
            continue
        value = run.condition(rule["when"])
        if value is True:
            candidates.add(rule["outcome"])
        elif value is None and rule["onUnknown"] == "escalate":
            reasons.add("unknown")
    if len(candidates) > 1:
        reasons.add("conflict")
    if reasons:
        return _disposition(form, "unresolved", None, reasons, False)
    # Steps 9 and 10.
    if candidates:
        return _disposition(form, "outcome", next(iter(candidates)), set(), False)
    if "fallbackOutcome" in form:
        return _disposition(form, "outcome", form["fallbackOutcome"], set(), False)
    return _disposition(form, "unresolved", None, {"no-match"}, False)


@dataclasses.dataclass
class Result:
    """Exactly one of a disposition (Core §8.3), an error class (§8.4), or the profile refusal."""

    disposition: dict[str, Any] | None = None
    error_class: str | None = None
    refusal: dict[str, str] | None = None
    detail: str = ""
    work: int = 0

    def expected_form(self) -> tuple[str, Any]:
        if self.disposition is not None:
            return "expectedDisposition", self.disposition
        if self.error_class is not None:
            return "expectedErrorClass", self.error_class
        return "refusal", self.refusal


def _document(value: Any) -> Any:
    """Bytes are a JSON text to admit; anything else is a value already read by load_json (a str
    is then a JSON string document, not a text)."""
    if isinstance(value, (bytes, bytearray)):
        return load_json(bytes(value))
    _kind_tree(value)
    return value


def _kind_tree(value: Any) -> None:
    stack = [value]
    while stack:
        item = stack.pop()
        _kind(item)
        if isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)


def evaluate(pack: str | bytes, facts: Any, evidence: Any = None, supported: Any = (), *,
             work_limit: int = WORK_LIMIT) -> Result:
    """One evaluation. `pack` is JSON text; `facts` and `evidence` are JSON texts as bytes, or
    values read by load_json; `evidence` None means no evidence-availability document (Core §8.2)."""
    # Preflight, in Core §8.2's order: the pack, the facts, the evidence, the required extensions.
    admission = admit_pack(pack)
    if admission.layer == "profile":
        return Result(refusal={"code": PROFILE_UNSUPPORTED, "profile": "extended"})
    if admission.layer is not None:
        return Result(error_class=PACK_NOT_CONFORMANT, detail=f"{admission.layer}: {admission.detail or admission.findings}")
    value = admission.pack
    try:
        facts = _document(facts)
    except (CarrierError, LimitError) as error:
        return Result(error_class=MALFORMED_INPUT, detail=f"facts: {error}")
    try:
        evidence = {} if evidence is None else _document(evidence)
    except (CarrierError, LimitError) as error:
        return Result(error_class=MALFORMED_INPUT, detail=f"evidence: {error}")
    declared = {item["id"] for item in value.get("evidenceRequirements", [])}
    if not isinstance(evidence, dict):
        return Result(error_class=MALFORMED_INPUT, detail="evidence: not an object")
    for name, state in evidence.items():
        if name not in declared:
            return Result(error_class=MALFORMED_INPUT, detail=f"evidence: undeclared requirement {name!r}")
        if not isinstance(state, str) or state not in EVIDENCE_STATES:
            return Result(error_class=MALFORMED_INPUT, detail=f"evidence: value for {name!r}")
    missing = _unsupported(value, supported)
    if missing:
        return Result(error_class=UNSUPPORTED_REQUIRED_EXTENSION, detail=f"requiredExtensions {missing}")
    run = _Run(facts, evidence, work_limit)
    try:
        return Result(disposition=resolve(evaluation_form(value), run), work=run.work)
    except _Exhausted:
        return Result(error_class=RESOURCE_EXHAUSTION, detail=f"work over {work_limit}", work=run.work)


def canonical(value: Any) -> str:
    """RFC 8785 bytes for a disposition, which holds no number (Core §8.3)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# --- The evaluation rows -------------------------------------------------------------------------

@dataclasses.dataclass
class RowResult:
    id: str
    status: str  # passed or failed
    got: tuple[str, Any]
    expected: tuple[str, Any]


def expected_of(row: dict[str, Any]) -> tuple[str, Any]:
    if "expectedDisposition" in row:
        return "expectedDisposition", row["expectedDisposition"]
    return "expectedErrorClass", row["expectedErrorClass"]


def run_row(row: dict[str, Any], base: Path, replace: tuple[bytes, bytes] | None = None) -> Result:
    data = (base / row["pack"]).read_bytes()
    if replace is not None:
        data = data.replace(*replace)
    return evaluate(data, row["facts"], row.get("evidenceAvailability"), row["supportedExtensions"])


def agrees(got: tuple[str, Any], expected: tuple[str, Any]) -> bool:
    return got[0] == expected[0] and canonical(got[1]) == canonical(expected[1])


def run_rows(manifest: Path = EVALUATION / "manifest.json") -> list[RowResult]:
    document = load_json(manifest.read_bytes())
    results = []
    for row in document["cases"]:
        got = run_row(row, manifest.parent).expected_form()
        status = "passed" if agrees(got, expected_of(row)) else "failed"
        results.append(RowResult(row["id"], status, got, expected_of(row)))
    return results


def main(argv: list[str]) -> int:
    if argv[:1] == ["rows"] and len(argv) == 1:
        results = run_rows()
        for item in results:
            if item.status != "passed":
                print(f"{item.status}: {item.id}: got {canonical(item.got)}; expected {canonical(item.expected)}")
        counts = {status: sum(1 for item in results if item.status == status) for status in ("passed", "failed")}
        print(f"core-040-eval: {counts['passed']} passed, {counts['failed']} failed")
        return 0 if counts["failed"] == 0 else 1
    if argv[:1] == ["evaluate"] and len(argv) >= 3:
        rest, supported = argv[1:], []
        while "--supported" in rest:
            at = rest.index("--supported")
            supported.append(rest[at + 1])
            del rest[at:at + 2]
        pack, facts, *evidence = (Path(name).read_bytes() for name in rest)
        result = evaluate(pack, facts, evidence[0] if evidence else None, supported)
        print(canonical(dict([result.expected_form()])))
        return 0
    print(__doc__.split("Usage:")[1].rstrip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

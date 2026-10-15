#!/usr/bin/env python3
"""A preparation verifier written from the words of spec/dialect.md.

This is the first of the two readers RFC 0018 records (its Evidence): it recomputes a preparation
from a dialect document, a case, the acquisitions and the trusted input profiles, at the
preparation's own instant, writes it in the preparation's canonical form, takes its digest, and
holds a runtime record's binding to it (spec/dialect.md §§3-11). It was written from that
document's text, and from the two sections of the checkpoint witness statement it adopts (§1, the
canonical form; §5, the key rule and the equation), and from nothing else: not the Runner's code,
whose `verify-run` is a third reader of the same bytes.

It reads dialect version 2 and the kind `operation`, the only kind the staged vectors exercise, and
refuses every other kind as `kind-unread` (spec/dialect.md §4: a kind without vectors is defined
and not claimable). Since the amendment of 2026-10-15 it reads `operation` of the shapes `airbyte`,
`mcp` and `http` (§4.1), each request in its shape's form. It does not read dialect version 3 — the
kinds of §4.3, and the unbound source form with its binding document (§4.4) — and refuses a dialect
of that version as `version-unread` (§11), taking no binding document. It uses the Python standard
library alone.

    python tools/dialect_verify.py --dialect mapping.json --case case.json \\
        --acquisitions sources.json --profiles profiles.json --preparation preparation.json \\
        [--record record.jsonl] [--require-binding]

It prints the report §11 gives, one JSON object in the preparation's canonical form, and exits 0
for a reading, 1 for a refusal and 2 for a finding; it exits 3, printing no report, when it could
not run at all. The reason for a refusal or a finding goes to standard error.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, NoReturn

# ---------------------------------------------------------------------------------------------
# Outcomes of a reading (§11)


class Refused(Exception):
    """A refusal: the reading reports nothing but its name."""

    def __init__(self, name: str, detail: str = "") -> None:
        super().__init__(f"{name}: {detail}" if detail else name)
        self.name = name


class Finding(Exception):
    """A finding: the reading ends at it and reports it."""

    def __init__(self, name: str, detail: str = "") -> None:
        super().__init__(f"{name}: {detail}" if detail else name)
        self.name = name


def malformed(detail: str) -> Refused:
    return Refused("input-malformed", detail)


# ---------------------------------------------------------------------------------------------
# Bounds (§12)

DIALECT_BYTES = 131072
ENVELOPE_BYTES = 2097152
PROFILES_BYTES = 65536
PREPARATION_BYTES = 8388608
RECORD_BYTES = 8388608
MAX_SOURCES = 16
MAX_SCOPE = 64
MAX_CLAUSES = 64
MAX_LISTED = 64
MAX_UNWRAP = 4
MAX_UNWRAPPED_BYTES = 200000
MAX_FACT_TARGETS = 256
MAX_EVIDENCE_TARGETS = 128
MAX_VALUE_DEPTH = 32
MAX_DOCUMENT_DEPTH = 64
MAX_NUMBER_CHARACTERS = 128
MAX_EXPONENT = 308

# ---------------------------------------------------------------------------------------------
# Reading a document (§1): strict, numbers kept as their literals

INTEGER_LITERAL = re.compile(r"-?(?:0|[1-9][0-9]*)")
LARGEST = 2**53 - 1


@dataclass(frozen=True)
class Num:
    """A JSON number, read as its literal, its characters kept."""

    literal: str

    @property
    def value(self) -> Decimal:
        return Decimal(self.literal)

    def is_integer(self) -> bool:
        return (
            INTEGER_LITERAL.fullmatch(self.literal) is not None
            and abs(int(self.literal)) <= LARGEST
        )


# §12: a literal's exponent is the run of digits after its first `e` or `E`, past a sign there; a
# literal with no such run has none.
EXPONENT = re.compile(r"[^eE]*[eE][+-]?([0-9]+)")
LITERAL_CHARACTERS = b"0123456789+-.eE"


def _number_bounds(literal: str) -> None:
    if len(literal) > MAX_NUMBER_CHARACTERS:
        raise Refused("input-over-bound", "a number literal of more than 128 characters")
    exponent = EXPONENT.match(literal)
    if exponent and int(exponent.group(1)) > MAX_EXPONENT:
        raise Refused("input-over-bound", "an exponent of magnitude over 308")


def _number(literal: str) -> Num:
    _number_bounds(literal)
    return Num(literal)


def measure(data: bytes, what: str, max_depth: int) -> None:
    """§12: the bounds measured on a document's bytes before it is read (§11, the first phase):
    its nesting, every object and every array one level from zero at the root, and each number
    literal's characters and exponent, a literal being a maximal run of the characters 0-9, +, -, .,
    e and E outside strings. It reads bytes, so it measures a document that is not JSON, or not
    UTF-8, as well as one that is."""
    depth = 0
    in_string = escaped = False
    position, length = 0, len(data)
    while position < length:
        byte = data[position]
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
        elif byte == 0x22:
            in_string = True
        elif byte in b"[{":
            depth += 1
            if depth > max_depth:
                raise Refused("input-over-bound", f"{what} nests more than {max_depth} levels")
        elif byte in b"]}":
            depth -= 1
        elif byte in LITERAL_CHARACTERS:
            end = position
            while end < length and data[end] in LITERAL_CHARACTERS:
                end += 1
            _number_bounds(data[position:end].decode("ascii"))
            position = end
            continue
        position += 1


def _no_constants(name: str) -> Any:
    raise malformed(f"{name} is not JSON")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise malformed("a member name given twice")
        result[name] = value
    return result


def _well_formed(value: Any) -> None:
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as error:
            raise malformed("a string that is not well-formed Unicode") from error
    elif isinstance(value, dict):
        for name, member in value.items():
            _well_formed(name)
            _well_formed(member)
    elif isinstance(value, list):
        for item in value:
            _well_formed(item)


def value_depth(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + max((value_depth(member) for member in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((value_depth(item) for item in value), default=0)
    return 0


def read_document(data: bytes, what: str, max_depth: int = MAX_DOCUMENT_DEPTH) -> Any:
    """One JSON value, read strictly (§1), its bounds measured first."""
    measure(data, what, max_depth)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise malformed(f"{what} is not UTF-8") from error
    if text.startswith("\ufeff"):
        raise malformed(f"{what} begins with a byte order mark")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_int=_number,
            parse_float=_number,
            parse_constant=_no_constants,
        )
    except (Refused, Finding):
        raise
    except (ValueError, RecursionError) as error:
        raise malformed(f"{what} is not one JSON value") from error
    _well_formed(value)
    return value


# ---------------------------------------------------------------------------------------------
# Values: forms, equality, pointers

HEX = re.compile(r"[0-9a-f]*")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
TIMESTAMP = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})Z")
CLASSES = ("asserted", "record", "generated")
TYPES = ("string", "integer", "timestamp")
AVAILABILITY = ("present", "absent", "unknown")
STATUSES = ("resolved", "absent", "unknown")
BINDING_KIND = "judgment-pack-runner/preparation/1"
VERIFICATION = "verified acquisitions; session sealing and input truth are not established"


def is_hex(value: Any, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and HEX.fullmatch(value) is not None


def is_digest(value: Any) -> bool:
    return isinstance(value, str) and DIGEST.fullmatch(value) is not None


def is_integer(value: Any) -> bool:
    return isinstance(value, Num) and value.is_integer()


def integer_of(value: Num) -> int:
    return int(value.literal)


def _days_from_civil(year: int, month: int, day: int) -> int:
    year -= month <= 2
    era = (year if year >= 0 else year - 399) // 400
    year_of_era = year - era * 400
    day_of_year = (153 * (month + (-3 if month > 2 else 9)) + 2) // 5 + day - 1
    day_of_era = year_of_era * 365 + year_of_era // 4 - year_of_era // 100 + day_of_year
    return era * 146097 + day_of_era - 719468


def instant(value: Any) -> int | None:
    """§1: the seconds since 1970-01-01T00:00:00Z a timestamp names, or None."""
    if not isinstance(value, str):
        return None
    match = TIMESTAMP.fullmatch(value)
    if match is None:
        return None
    year, month, day, hour, minute, second = (int(part) for part in match.groups())
    if not 1 <= month <= 12 or hour > 23 or minute > 59 or second > 59:
        return None
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days_in_month = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
    if not 1 <= day <= days_in_month:
        return None
    return _days_from_civil(year, month, day) * 86400 + hour * 3600 + minute * 60 + second


def of_type(value: Any, kind: str) -> bool:
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        return is_integer(value)
    return instant(value) is not None


def json_equal(left: Any, right: Any) -> bool:
    """JSON-equal (§6.3): type and value, numbers by their mathematical value."""
    if isinstance(left, Num) or isinstance(right, Num):
        return isinstance(left, Num) and isinstance(right, Num) and left.value == right.value
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, str) or isinstance(right, str):
        return isinstance(left, str) and isinstance(right, str) and left == right
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(json_equal(a, b) for a, b in zip(left, right))
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(json_equal(left[k], right[k]) for k in left)
    return False


ABSENT = object()


def pointer_tokens(pointer: Any) -> list[str] | None:
    """RFC 6901: the tokens of a pointer, or None when it is not one."""
    if not isinstance(pointer, str):
        return None
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        return None
    tokens = []
    for raw in pointer[1:].split("/"):
        if re.search(r"~(?![01])", raw):
            return None
        tokens.append(raw.replace("~1", "/").replace("~0", "~"))
    return tokens


def is_pointer(value: Any) -> bool:
    return pointer_tokens(value) is not None


def names_an_element(token: str, length: int) -> bool:
    """§1: a token of decimal digits, with no leading zero but `0`, whose value is below the
    array's length. The token is compared by its length first, so a token of any length is read
    without converting it to a number: one longer than the length's own digits names no element."""
    if re.fullmatch(r"0|[1-9][0-9]*", token) is None:
        return False
    bound = str(length)
    if len(token) != len(bound):
        return len(token) < len(bound)
    return token < bound


def resolve(document: Any, pointer: str) -> Any:
    """The value a pointer resolves to, or ABSENT (§1)."""
    tokens = pointer_tokens(pointer)
    assert tokens is not None
    current = document
    for token in tokens:
        if isinstance(current, dict):
            if token not in current:
                return ABSENT
            current = current[token]
        elif isinstance(current, list):
            if not names_an_element(token, len(current)):
                return ABSENT
            current = current[int(token)]
        else:
            return ABSENT
    return current


def write_at(document: dict[str, Any], pointer: str, value: Any) -> None:
    """§8.1: write a value at a fact target, creating each object on the way."""
    tokens = pointer_tokens(pointer)
    assert tokens
    current = document
    for token in tokens[:-1]:
        nxt = current.get(token)
        if not isinstance(nxt, dict):
            nxt = {}
            current[token] = nxt
        current = nxt
    current[tokens[-1]] = value


def is_prefix(shorter: list[str], longer: list[str]) -> bool:
    return len(shorter) <= len(longer) and longer[: len(shorter)] == shorter


# ---------------------------------------------------------------------------------------------
# The two canonical forms (§1, §9.5)


class OutsideDomain(Exception):
    """A value with no `canon` form."""


def _canon_string(text: str) -> str:
    out = ['"']
    for character in text:
        code = ord(character)
        if character == '"':
            out.append('\\"')
        elif character == "\\":
            out.append("\\\\")
        elif character == "\b":
            out.append("\\b")
        elif character == "\f":
            out.append("\\f")
        elif character == "\n":
            out.append("\\n")
        elif character == "\r":
            out.append("\\r")
        elif character == "\t":
            out.append("\\t")
        elif code < 0x20:
            out.append("\\u%04x" % code)
        else:
            out.append(character)
    out.append('"')
    return "".join(out)


def _canon(value: Any) -> str:
    if isinstance(value, dict):
        names = sorted(value)  # Python orders str by code point
        return "{" + ",".join(_canon_string(n) + ":" + _canon(value[n]) for n in names) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_canon(item) for item in value) + "]"
    if isinstance(value, str):
        return _canon_string(value)
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, Num):
        if not value.is_integer():
            raise OutsideDomain(value.literal)
        return str(int(value.literal))
    if isinstance(value, int):
        if abs(value) > LARGEST:
            raise OutsideDomain(str(value))
        return str(value)
    raise OutsideDomain(repr(value))


def canon(value: Any) -> bytes:
    """The gateway canonical form (§1)."""
    return _canon(value).encode("utf-8")


def in_canon_domain(value: Any) -> bool:
    try:
        canon(value)
    except OutsideDomain:
        return False
    return True


def digest_of(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


_PREPARATION_ESCAPES = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
    "&": "\\u0026",
    "<": "\\u003c",
    ">": "\\u003e",
    "\u2028": "\\u2028",
    "\u2029": "\\u2029",
}


def _preparation_string(text: str) -> str:
    out = ['"']
    for character in text:
        escape = _PREPARATION_ESCAPES.get(character)
        if escape is not None:
            out.append(escape)
        elif ord(character) < 0x20:
            out.append("\\u%04x" % ord(character))
        else:
            out.append(character)
    out.append('"')
    return "".join(out)


def write_number(value: Num | int) -> str:
    """§9.5: the literal, its characters kept; every number of a preparation is an integer."""
    if isinstance(value, Num):
        if not value.is_integer():
            raise OutsideDomain(value.literal)
        return value.literal
    return str(value)


def _preparation_form(value: Any) -> str:
    if isinstance(value, dict):
        names = sorted(value, key=lambda name: name.encode("utf-8"))
        return (
            "{"
            + ",".join(_preparation_string(n) + ":" + _preparation_form(value[n]) for n in names)
            + "}"
        )
    if isinstance(value, list):
        return "[" + ",".join(_preparation_form(item) for item in value) + "]"
    if isinstance(value, str):
        return _preparation_string(value)
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, (Num, int)) and not isinstance(value, bool):
        return write_number(value)
    raise OutsideDomain(repr(value))


def preparation_bytes(value: Any) -> bytes:
    """The canonical form of a preparation (§9.5)."""
    return _preparation_form(value).encode("utf-8")


def binding_of(digest: str) -> bytes:
    """§9.5: the binding, these bytes exactly."""
    return ('{"kind":"' + BINDING_KIND + '","digest":"' + digest + '"}').encode("ascii")


# ---------------------------------------------------------------------------------------------
# Ed25519: the key rule and the equation (checkpoint witness statement §5)

P = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493
D = (-121665 * pow(121666, P - 2, P)) % P
SQRT_MINUS_ONE = pow(2, (P - 1) // 4, P)
SMALL_ORDER = {
    bytes.fromhex(h)
    for h in (
        "0100000000000000000000000000000000000000000000000000000000000000",
        "ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f",
        "0000000000000000000000000000000000000000000000000000000000000000",
        "0000000000000000000000000000000000000000000000000000000000000080",
        "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05",
        "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85",
        "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a",
        "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa",
    )
}


def _x_from_y(y: int, sign: int) -> int | None:
    numerator = (y * y - 1) % P
    denominator = (D * y * y + 1) % P
    x2 = numerator * pow(denominator, P - 2, P) % P
    if x2 == 0:
        return 0
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P != 0:
        x = x * SQRT_MINUS_ONE % P
    if (x * x - x2) % P != 0:
        return None
    if x & 1 != sign:
        x = P - x
    return x


def key_refusal(key: bytes) -> str | None:
    """The key rule, in its order; None for a key a reader may trust."""
    encoded = int.from_bytes(key, "little")
    y = encoded & ((1 << 255) - 1)
    sign = encoded >> 255
    if y >= P or (y in (1, P - 1) and sign == 1):
        return "key-not-canonical"
    if key in SMALL_ORDER:
        return "key-small-order"
    if _x_from_y(y, sign) is None:
        return "key-not-on-curve"
    return None


def _add(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x1, y1, z1, t1 = a
    x2, y2, z2, t2 = b
    pa = (y1 - x1) * (y2 - x2) % P
    pb = (y1 + x1) * (y2 + x2) % P
    pc = 2 * t1 * t2 * D % P
    pd = 2 * z1 * z2 % P
    e, f, g, h = pb - pa, pd - pc, pd + pc, pb + pa
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _multiply(scalar: int, point: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    result = (0, 1, 1, 0)
    while scalar:
        if scalar & 1:
            result = _add(result, point)
        point = _add(point, point)
        scalar >>= 1
    return result


def _encode(point: tuple[int, int, int, int]) -> bytes:
    x, y, z, _ = point
    inverse = pow(z, P - 2, P)
    x, y = x * inverse % P, y * inverse % P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


_BASE_Y = 4 * pow(5, P - 2, P) % P
_BASE_X = _x_from_y(_BASE_Y, 0)
BASE = (_BASE_X, _BASE_Y, 1, _BASE_X * _BASE_Y % P)


def signature_verifies(key: bytes, message: bytes, signature: bytes) -> bool:
    """[S]B - [h]A encodes to R, S below L: RFC 8032 without the cofactor."""
    if len(signature) != 64 or key_refusal(key) is not None:
        return False
    r_bytes, s = signature[:32], int.from_bytes(signature[32:], "little")
    if s >= L:
        return False
    encoded = int.from_bytes(key, "little")
    y = encoded & ((1 << 255) - 1)
    x = _x_from_y(y, encoded >> 255)
    assert x is not None
    a = (x, y, 1, x * y % P)
    h = int.from_bytes(hashlib.sha512(r_bytes + key + message).digest(), "little") % L
    ha = _multiply(h, a)
    negative = ((P - ha[0]) % P, ha[1], ha[2], (P - ha[3]) % P)
    return _encode(_add(_multiply(s, BASE), negative)) == r_bytes


# ---------------------------------------------------------------------------------------------
# The dialect document (§§2-8)


def closed(value: Any, required: set[str], optional: set[str], what: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise malformed(f"{what} is not an object")
    missing = required - set(value)
    unknown = set(value) - required - optional
    if missing or unknown:
        raise malformed(f"{what}: members missing {sorted(missing)} or unknown {sorted(unknown)}")
    return value


@dataclass
class Parameter:
    name: str
    type: str
    pointer: str
    origin: str  # "case", or the name of the source it is taken from


@dataclass
class Read:
    unwrap: list[str]
    copy: dict[str, Any] | None
    rule: dict[str, Any] | None
    as_written: dict[str, Any]
    fact_targets: list[str] = field(default_factory=list)
    evidence_targets: list[str] = field(default_factory=list)
    # target -> the pointers of the value read the dialect could copy to it (§9.3)
    candidates: dict[tuple[str, str], list[str]] = field(default_factory=dict)


@dataclass
class Source:
    name: str
    kind: str
    parameters: dict[str, Parameter]
    read: Read
    profile_id: str = ""
    profile_digest: str = ""
    max_age: int = 0
    form: str = ""  # the shape whose request form `arguments` take (§4.1)
    tool: str = ""
    template: Any = None  # `arguments`, the request's template, whole
    calculation: dict[str, Any] | None = None


@dataclass
class Dialect:
    document: dict[str, Any]
    case_parameters: dict[str, Parameter]
    case_read: Read
    sources: list[Source]
    admits: dict[tuple[str, str], list[str]]


def check_template(value: Any, scope: dict[str, str], what: str) -> None:
    """§4.1: every template form is $param or $text, naming parameters in scope, never runAt."""
    if isinstance(value, dict):
        if any(name.startswith("$") for name in value):
            if len(value) != 1:
                raise malformed(f"{what}: a template form of more than one member")
            (form, argument), = value.items()
            if form == "$param":
                if not isinstance(argument, str) or argument == "runAt" or argument not in scope:
                    raise malformed(f"{what}: $param names no parameter in scope")
            elif form == "$text":
                if not isinstance(argument, str):
                    raise malformed(f"{what}: $text is not a string")
                for name in placeholders(argument, what):
                    if name == "runAt" or scope.get(name) != "integer":
                        raise malformed(f"{what}: a placeholder names no integer parameter")
            else:
                raise malformed(f"{what}: an unknown template form {form}")
            return
        for name, member in value.items():
            check_template(member, scope, what)
    elif isinstance(value, list):
        for item in value:
            check_template(item, scope, what)


# §4.1: each shape's request form, by its members, required and optional. No two forms share a member.
REQUEST_FORMS = {
    "mcp": ({"tool", "arguments"}, set()),
    "http": ({"method", "path"}, {"query"}),
    "airbyte": ({"stream"}, {"namespace", "limit", "state"}),
}


def is_string_template(value: Any, scope: dict[str, str]) -> bool:
    """§4.1: a string, a $text, or a $param naming a parameter of type string or timestamp."""
    if isinstance(value, str):
        return True
    if isinstance(value, dict) and len(value) == 1:
        (form, argument), = value.items()
        if form == "$text":
            return True
        if form == "$param":
            return scope.get(argument) in ("string", "timestamp")
    return False


def check_request(value: Any, scope: dict[str, str], what: str) -> str:
    """§4.1: `arguments`, the template of a request, of one shape's form, which its members name. The
    shape it is of is returned; whether it is the profile's is a finding, `profile-mismatch`."""
    if not isinstance(value, dict):
        raise malformed(f"{what}: arguments are not an object")
    members = set(value)
    forms = [shape for shape, (required, optional) in REQUEST_FORMS.items() if required <= members <= required | optional]
    if not forms:
        raise malformed(f"{what}: arguments of no request form, members {sorted(members)}")
    shape = forms[0]
    check_template(value, scope, what)
    if shape == "mcp":
        if not isinstance(value["tool"], str) or not value["tool"]:
            raise malformed(f"{what}: tool is not a non-empty string")
    elif shape == "http":
        if value["method"] not in ("GET", "POST"):
            raise malformed(f"{what}: method is not GET or POST")
        if not is_string_template(value["path"], scope):
            raise malformed(f"{what}: path is not a string template")
        if "query" in value:
            query = value["query"]
            if not isinstance(query, dict) or any(name.startswith("$") for name in query):
                raise malformed(f"{what}: query is not an object, or is a template form")
            if not all(is_string_template(member, scope) for member in query.values()):
                raise malformed(f"{what}: a query member is not a string template")
    else:
        if not is_string_template(value["stream"], scope):
            raise malformed(f"{what}: stream is not a string template")
        if "namespace" in value and value["namespace"] is not None and not is_string_template(value["namespace"], scope):
            raise malformed(f"{what}: namespace is not a string template or null")
        if "limit" in value:
            limit = value["limit"]
            named = isinstance(limit, dict) and scope.get(limit.get("$param")) == "integer"
            if not (is_integer(limit) or named):
                raise malformed(f"{what}: limit is not an integer or a $param naming one")
        if "state" in value and not is_string_template(value["state"], scope):
            raise malformed(f"{what}: state is not a string template")
    return shape


def placeholders(text: str, what: str = "a $text") -> list[str]:
    """§4.1: `{{`, a parameter name, and the next `}}`."""
    names = []
    position = 0
    while True:
        start = text.find("{{", position)
        if start < 0:
            return names
        end = text.find("}}", start + 2)
        if end < 0:
            raise malformed(f"{what}: a {{{{ with no }}}} after it")
        names.append(text[start + 2 : end])
        position = end + 2


def check_condition(condition: Any, declared: dict[str, str], what: str, depth: int = 0) -> None:
    if not isinstance(condition, dict) or not isinstance(condition.get("op"), str):
        raise malformed(f"{what}: a condition is not an object with an op that is a string")
    op = condition["op"]
    shapes = {
        "always": set(),
        "exists": {"field"},
        "equals": {"field", "to"},
        "equalsParam": {"field", "param"},
        "isTrue": {"field"},
        "isDecimalString": {"field"},
        "freshWithin": {"field", "asOf", "maxAge"},
        "all": {"of"},
        "any": {"of"},
        "not": {"of"},
    }
    if op not in shapes:
        raise malformed(f"{what}: an unknown op")
    closed(condition, {"op"} | shapes[op], set(), what)
    if "field" in condition and not is_pointer(condition["field"]):
        raise malformed(f"{what}: a field that is not a pointer")
    if op == "equals" and not in_canon_domain(condition["to"]):
        raise malformed(f"{what}: a literal outside the canon domain")
    for member in ("param", "asOf", "maxAge"):
        if member in condition and not isinstance(condition[member], str):
            raise malformed(f"{what}: {member} is not a string naming a parameter")
    if op == "equalsParam" and condition["param"] not in declared:
        raise malformed(f"{what}: equalsParam names a parameter the rule does not declare")
    if op == "freshWithin":
        # §6.3: `asOf` and `maxAge` name parameters the rule declares, which is the condition's
        # form; that the one is a `timestamp` and the other an `integer` is part of its truth, so a
        # declared parameter of another type makes it false, not the dialect malformed.
        for member in ("asOf", "maxAge"):
            if condition[member] not in declared:
                raise malformed(f"{what}: {member} names a parameter the rule does not declare")
    if op in ("all", "any"):
        if not isinstance(condition["of"], list) or len(condition["of"]) > MAX_LISTED:
            if isinstance(condition["of"], list):
                raise Refused("input-over-bound", f"{what}: more than 64 conditions listed")
            raise malformed(f"{what}: `of` is not a list")
        for item in condition["of"]:
            check_condition(item, declared, what, depth + 1)
    if op == "not":
        check_condition(condition["of"], declared, what, depth + 1)


def fact_target(pointer: Any, what: str) -> str:
    if not is_pointer(pointer) or pointer == "":
        raise malformed(f"{what}: a fact target that is not a pointer other than the root")
    return pointer


def check_read(value: Any, scope: dict[str, str], what: str) -> Read:
    read = closed(value, set(), {"unwrap", "copy", "rule"}, what)
    if ("copy" in read) == ("rule" in read):
        raise malformed(f"{what}: a read has exactly one of copy and rule")
    unwrap = read.get("unwrap", [])
    if "unwrap" in read:
        if not isinstance(unwrap, list) or not unwrap:
            raise malformed(f"{what}: unwrap is not a list of one to four pointers")
        if len(unwrap) > MAX_UNWRAP:
            raise Refused("input-over-bound", f"{what}: more than four unwrap pointers")
        if not all(is_pointer(p) for p in unwrap):
            raise malformed(f"{what}: an unwrap entry that is not a pointer")
    result = Read(unwrap=list(unwrap), copy=None, rule=None, as_written=read)
    if "copy" in read:
        copy = closed(read["copy"], set(), {"facts", "evidence"}, what + " copy")
        facts = copy.get("facts", [])
        evidence = copy.get("evidence", [])
        if not isinstance(facts, list) or not isinstance(evidence, list):
            raise malformed(f"{what}: copy facts and evidence are arrays")
        for entry in facts:
            closed(entry, {"target", "source"}, set(), what + " copy fact")
            target = fact_target(entry["target"], what)
            if not is_pointer(entry["source"]):
                raise malformed(f"{what}: a copy source that is not a pointer")
            result.fact_targets.append(target)
            result.candidates.setdefault(("fact", target), []).append(entry["source"])
        seen_requirements: set[str] = set()
        for entry in evidence:
            closed(entry, {"requirement", "source"}, set(), what + " copy evidence")
            requirement = entry["requirement"]
            if not isinstance(requirement, str) or not requirement:
                raise malformed(f"{what}: a requirement that is not a non-empty string")
            if requirement in seen_requirements:
                raise malformed(f"{what}: a copy names a requirement twice")
            seen_requirements.add(requirement)
            if not is_pointer(entry["source"]):
                raise malformed(f"{what}: a copy source that is not a pointer")
            result.evidence_targets.append(requirement)
            result.candidates.setdefault(("evidence", requirement), []).append(entry["source"])
        result.copy = {"facts": facts, "evidence": evidence}
    else:
        rule = closed(read["rule"], {"ruleVersion", "parameters", "clauses"}, set(), what + " rule")
        if rule["ruleVersion"] != "1":
            raise malformed(f"{what}: ruleVersion is not \"1\"")
        declared = rule["parameters"]
        if not isinstance(declared, dict):
            raise malformed(f"{what}: rule parameters are not an object")
        for name, kind in declared.items():
            if kind not in TYPES:
                raise malformed(f"{what}: a rule parameter of another type")
            if scope.get(name) != kind:
                raise malformed(f"{what}: a rule parameter not in scope with its type")
        clauses = rule["clauses"]
        if not isinstance(clauses, list) or not clauses:
            raise malformed(f"{what}: clauses are not a non-empty array")
        if len(clauses) > MAX_CLAUSES:
            raise Refused("input-over-bound", f"{what}: more than 64 clauses")
        fact_seen: list[str] = []
        evidence_seen: list[str] = []
        for clause in clauses:
            closed(clause, {"when", "claim", "reason"}, set(), what + " clause")
            check_condition(clause["when"], declared, what)
            if not isinstance(clause["reason"], str):
                raise malformed(f"{what}: a reason that is not a string")
            claim = closed(
                clause["claim"], {"facts", "evidence", "acquisitionStatus"}, set(), what + " claim"
            )
            if not isinstance(claim["facts"], list):
                raise malformed(f"{what}: claim facts are not an array")
            for entry in claim["facts"]:
                closed(entry, {"pointer", "from"}, set(), what + " claim fact")
                target = fact_target(entry["pointer"], what)
                if not is_pointer(entry["from"]):
                    raise malformed(f"{what}: a from that is not a pointer")
                if target not in fact_seen:
                    fact_seen.append(target)
                candidates = result.candidates.setdefault(("fact", target), [])
                candidates.append(entry["from"])
            if not isinstance(claim["evidence"], dict):
                raise malformed(f"{what}: claim evidence is not an object")
            for requirement, availability in claim["evidence"].items():
                if not requirement or availability not in AVAILABILITY:
                    raise malformed(f"{what}: claim evidence of another form")
                if requirement not in evidence_seen:
                    evidence_seen.append(requirement)
            if claim["acquisitionStatus"] not in STATUSES:
                raise malformed(f"{what}: an acquisitionStatus of another value")
        if clauses[-1]["when"] != {"op": "always"}:
            raise malformed(f"{what}: the last clause's when is not always")
        result.fact_targets = fact_seen
        result.evidence_targets = evidence_seen
        result.rule = rule
    if not in_canon_domain(read):
        raise malformed(f"{what}: a read outside the canon domain")
    return result


def check_parameter_name(name: Any, what: str) -> None:
    if not isinstance(name, str) or not name or name == "runAt":
        raise malformed(f"{what}: a parameter name that is empty or runAt")


def parse_dialect(document: Any) -> Dialect:
    top = closed(
        document,
        {"version", "case"},
        {"sources", "admits", "unmapped", "unmappedEvidence", "provider", "facts", "evidence"},
        "the dialect",
    )
    if not (isinstance(top["version"], Num) and top["version"].is_integer()):
        raise malformed("the dialect's version is not an integer")
    if integer_of(top["version"]) != 2:
        # Version 3 was refused before any form was checked (§11, `version-unread`).
        raise malformed("a dialect version this document does not define")
    if "provider" in top and top["provider"] != "":
        raise malformed("provider is not the empty string")
    for name in ("facts", "evidence"):
        if name in top and top[name] is not None:
            raise malformed(f"{name} is not null")
    if not in_canon_domain(top):
        raise malformed("the dialect is outside the canon domain")
    for name, check in (("unmapped", is_pointer), ("unmappedEvidence", lambda v: isinstance(v, str) and v)):
        if name in top:
            items = top[name]
            if not isinstance(items, list) or not all(check(i) for i in items):
                raise malformed(f"{name} is not an array of its form")
            if len(set(items)) != len(items):
                raise malformed(f"{name} names one twice")

    case = closed(top["case"], {"facts", "evidence"}, {"parameters"}, "case")
    case_parameters: dict[str, Parameter] = {}
    declared = case.get("parameters", {})
    if not isinstance(declared, dict):
        raise malformed("case parameters are not an object")
    for name, declaration in declared.items():
        check_parameter_name(name, "case")
        closed(declaration, {"pointer", "type"}, set(), f"case parameter {name}")
        if not is_pointer(declaration["pointer"]) or declaration["type"] not in TYPES:
            raise malformed(f"case parameter {name} is not of its form")
        case_parameters[name] = Parameter(name, declaration["type"], declaration["pointer"], "case")
    if len(case_parameters) + 1 > MAX_SCOPE:
        raise Refused("input-over-bound", "more than 64 parameters in the case's scope")
    case_scope = {name: p.type for name, p in case_parameters.items()}
    case_scope["runAt"] = "timestamp"
    case_read = check_read(
        {"copy": {"facts": case["facts"], "evidence": case["evidence"]}}, case_scope, "the case's read"
    )

    sources: list[Source] = []
    raw_sources = top.get("sources", [])
    if not isinstance(raw_sources, list):
        raise malformed("sources is not an array")
    if len(raw_sources) > MAX_SOURCES:
        raise Refused("input-over-bound", "more than 16 sources")
    unread_kind = False
    for index, raw in enumerate(raw_sources):
        what = f"source {index}"
        if not isinstance(raw, dict) or not isinstance(raw.get("name"), str):
            raise malformed(f"{what} has no name")
        name = raw["name"]
        if not name or name == "case" or any(s.name == name for s in sources):
            raise malformed(f"{what}: a name that is empty, case, or given twice")
        kind = raw.get("kind")
        if kind in ("http", "sql", "web", "research"):
            raise malformed(f"{what}: a kind of version 3 in a version-2 document")
        # Every kind's form is checked, its common members (§4) and its own, before a kind this
        # reader does not read is refused (§11): `kind-unread` comes after every form.
        if kind == "operation":
            closed(
                raw,
                {"name", "kind", "read", "profile", "profileDigest", "maxAge", "arguments"},
                {"parameters", "calculation"},
                what,
            )
            acquired = True
        elif kind == "selected-file":
            closed(
                raw,
                {"name", "kind", "read", "provider"},
                {"parameters", "profile", "profileDigest", "maxAge", "arguments"},
                what,
            )
            drive = {"profile", "profileDigest", "maxAge", "arguments"}
            if raw["provider"] == "local-file":
                if drive & set(raw):
                    raise malformed(f"{what}: a local file has no profile, maxAge or request")
                acquired = False
            elif raw["provider"] == "google-drive":
                if not drive <= set(raw):
                    raise malformed(f"{what}: a Drive file has a profile, maxAge and a request")
                acquired = True
            else:
                raise malformed(f"{what}: a provider of another value")
            unread_kind = True
        else:
            raise malformed(f"{what}: a kind this version does not list")
        parameters: dict[str, Parameter] = {}
        declared = raw.get("parameters", {})
        if not isinstance(declared, dict):
            raise malformed(f"{what}: parameters are not an object")
        for pname, declaration in declared.items():
            check_parameter_name(pname, what)
            if pname in case_parameters:
                raise malformed(f"{what}: a source parameter shadows a case parameter")
            closed(declaration, {"from", "pointer", "type"}, set(), f"{what} parameter {pname}")
            origin = declaration["from"]
            if not any(s.name == origin for s in sources):
                raise malformed(f"{what}: a source parameter from no earlier source")
            if not is_pointer(declaration["pointer"]) or declaration["type"] not in TYPES:
                raise malformed(f"{what}: a source parameter not of its form")
            parameters[pname] = Parameter(pname, declaration["type"], declaration["pointer"], origin)
        scope = dict(case_scope)
        scope.update({pname: p.type for pname, p in parameters.items()})
        if len(scope) > MAX_SCOPE:
            raise Refused("input-over-bound", f"{what}: more than 64 parameters in scope")
        source = Source(name=name, kind=kind, parameters=parameters, read=Read([], None, None, {}))
        if acquired:
            if not isinstance(raw["profile"], str) or not raw["profile"]:
                raise malformed(f"{what}: profile is not a non-empty string")
            if not is_digest(raw["profileDigest"]):
                raise malformed(f"{what}: profileDigest is not a digest")
            if not is_integer(raw["maxAge"]) or not 1 <= integer_of(raw["maxAge"]) <= 86400:
                raise malformed(f"{what}: maxAge is not an integer from 1 to 86400")
            source.form = check_request(raw["arguments"], scope, f"{what} arguments")
            source.profile_id = raw["profile"]
            source.profile_digest = raw["profileDigest"]
            source.max_age = integer_of(raw["maxAge"])
            source.tool = raw["arguments"]["tool"] if source.form == "mcp" else ""
            source.template = raw["arguments"]
        if "calculation" in raw:
            calculation = closed(raw["calculation"], {"inputs", "tables"}, set(), f"{what} calculation")
            inputs, tables = calculation["inputs"], calculation["tables"]
            if not isinstance(inputs, dict) or not isinstance(tables, dict):
                raise malformed(f"{what}: calculation inputs and tables are objects")
            for bound in inputs.values():
                if not isinstance(bound, str) or bound == "runAt" or bound not in scope:
                    raise malformed(f"{what}: an input bound to no parameter in scope, or runAt")
            for limit in tables.values():
                if not is_integer(limit) or not 1 <= integer_of(limit) <= 315360000:
                    raise malformed(f"{what}: a table limit of another form")
            source.calculation = calculation
        source.read = check_read(raw["read"], scope, what + " read")
        sources.append(source)
    # A source parameter's pointer is a fact target of the source it comes from (§3).
    for source in sources:
        for parameter in source.parameters.values():
            origin = next(s for s in sources if s.name == parameter.origin)
            if parameter.pointer not in origin.read.fact_targets:
                raise malformed(f"{source.name}: a source parameter reads no fact target of {origin.name}")

    # §8.1: targets never overlap; a requirement has one source; bounds.
    every_fact: list[list[str]] = []
    evidence_sources: dict[str, str] = {}
    for owner, read in [("case", case_read)] + [(s.name, s.read) for s in sources]:
        for target in read.fact_targets:
            tokens = pointer_tokens(target)
            assert tokens is not None
            for other in every_fact:
                if is_prefix(other, tokens) or is_prefix(tokens, other):
                    raise malformed("two fact targets overlap")
            every_fact.append(tokens)
        for requirement in read.evidence_targets:
            if requirement in evidence_sources:
                raise malformed("a requirement is the evidence target of two sources")
            evidence_sources[requirement] = owner
    if len(every_fact) > MAX_FACT_TARGETS or len(evidence_sources) > MAX_EVIDENCE_TARGETS:
        raise Refused("input-over-bound", "more fact or evidence targets than the bounds")

    admits: dict[tuple[str, str], list[str]] = {}
    if "admits" in top:
        raw_admits = closed(top["admits"], set(), {"facts", "evidence"}, "admits")
        written_facts = {t for r in [case_read] + [s.read for s in sources] for t in r.fact_targets}
        for member, kind, written in (("facts", "fact", written_facts), ("evidence", "evidence", set(evidence_sources))):
            entries = raw_admits.get(member, {})
            if not isinstance(entries, dict):
                raise malformed(f"admits.{member} is not an object")
            for target, classes in entries.items():
                if target not in written:
                    raise malformed(f"admits names a target no source writes")
                if not isinstance(classes, list) or not all(c in CLASSES for c in classes):
                    raise malformed("admits gives a list of another form")
                admits[(kind, target)] = list(classes)

    dialect = Dialect(top, case_parameters, case_read, sources, admits)
    if unread_kind:
        raise Refused("kind-unread", "selected-file is defined and not read by this reader")
    return dialect


def count_bounds(dialect: Any, acquisitions: Any) -> None:
    """§12's counted bounds, and a result's nesting, taken on the documents read wherever the count
    can be taken, before any form is checked (§11, the third phase)."""

    def over(detail: str) -> Refused:
        return Refused("input-over-bound", detail)

    if isinstance(acquisitions, dict):
        for name, member in acquisitions.items():
            response = member.get("response") if isinstance(member, dict) else None
            if isinstance(response, dict) and "result" in response:
                if value_depth(response["result"]) > MAX_VALUE_DEPTH:
                    raise over(f"acquisition {name}: a result nested more than 32 levels")
    if not isinstance(dialect, dict):
        return
    facts: set[str] = set()
    evidence: set[str] = set()

    def entries(value: Any) -> list[Any]:
        return value if isinstance(value, list) else []

    def copy_targets(copy: Any) -> None:
        if isinstance(copy, dict):
            for entry in entries(copy.get("facts")):
                if isinstance(entry, dict) and isinstance(entry.get("target"), str):
                    facts.add(entry["target"])
            for entry in entries(copy.get("evidence")):
                if isinstance(entry, dict) and isinstance(entry.get("requirement"), str):
                    evidence.add(entry["requirement"])

    def listed(condition: Any) -> None:
        if not isinstance(condition, dict):
            return
        if condition.get("op") in ("all", "any") and isinstance(condition.get("of"), list):
            if len(condition["of"]) > MAX_LISTED:
                raise over("more than 64 conditions listed")
            for item in condition["of"]:
                listed(item)
        elif condition.get("op") == "not":
            listed(condition.get("of"))

    case = dialect.get("case")
    case_parameters = case.get("parameters") if isinstance(case, dict) else None
    in_case = len(case_parameters) if isinstance(case_parameters, dict) else 0
    if in_case + 1 > MAX_SCOPE:
        raise over("more than 64 parameters in the case's scope")
    if isinstance(case, dict):
        copy_targets({"facts": case.get("facts"), "evidence": case.get("evidence")})
    sources = dialect.get("sources")
    if isinstance(sources, list):
        if len(sources) > MAX_SOURCES:
            raise over("more than 16 sources")
        for source in sources:
            if not isinstance(source, dict):
                continue
            own = source.get("parameters")
            if isinstance(own, dict) and in_case + len(own) + 1 > MAX_SCOPE:
                raise over("more than 64 parameters in a scope")
            read = source.get("read")
            if not isinstance(read, dict):
                continue
            if isinstance(read.get("unwrap"), list) and len(read["unwrap"]) > MAX_UNWRAP:
                raise over("more than four unwrap pointers")
            copy_targets(read.get("copy"))
            rule = read.get("rule")
            clauses = rule.get("clauses") if isinstance(rule, dict) else None
            if isinstance(clauses, list):
                if len(clauses) > MAX_CLAUSES:
                    raise over("more than 64 clauses")
                for clause in clauses:
                    if not isinstance(clause, dict):
                        continue
                    listed(clause.get("when"))
                    claim = clause.get("claim")
                    if isinstance(claim, dict):
                        for entry in entries(claim.get("facts")):
                            if isinstance(entry, dict) and isinstance(entry.get("pointer"), str):
                                facts.add(entry["pointer"])
                        if isinstance(claim.get("evidence"), dict):
                            evidence.update(claim["evidence"])
    if len(facts) > MAX_FACT_TARGETS or len(evidence) > MAX_EVIDENCE_TARGETS:
        raise over("more fact or evidence targets than the bounds")


# ---------------------------------------------------------------------------------------------
# Input profiles (§5.1)


def parse_profiles(document: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(document, list):
        raise malformed("the profiles are not an array")
    profiles: dict[str, dict[str, Any]] = {}
    for index, profile in enumerate(document):
        what = f"profile {index}"
        closed(
            profile,
            {"id", "publicKey", "class", "source", "authority", "shape", "adapter", "endpoint"},
            {"tools", "calculator"},
            what,
        )
        if not isinstance(profile["id"], str) or not profile["id"] or profile["id"] in profiles:
            raise malformed(f"{what}: an id that is empty or given twice")
        if not is_hex(profile["publicKey"], 64) or key_refusal(bytes.fromhex(profile["publicKey"])):
            raise malformed(f"{what}: a key the key rule refuses")
        if profile["class"] not in ("record", "generated"):
            raise malformed(f"{what}: a class of another value")
        if not isinstance(profile["source"], str) or not isinstance(profile["authority"], str):
            raise malformed(f"{what}: source and authority are strings")
        if profile["shape"] not in ("airbyte", "mcp", "http", "command"):
            raise malformed(f"{what}: a shape of another value")
        adapter = closed(profile["adapter"], {"name", "version", "digest"}, set(), what + " adapter")
        if not isinstance(adapter["name"], str) or not isinstance(adapter["version"], str):
            raise malformed(f"{what}: adapter name and version are strings")
        if not is_digest(adapter["digest"]):
            raise malformed(f"{what}: adapter digest is not a digest")
        if profile["endpoint"] is not None and not isinstance(profile["endpoint"], str):
            raise malformed(f"{what}: endpoint is a string or null")
        if "tools" in profile:
            tools = profile["tools"]
            if (
                not isinstance(tools, list)
                or not all(isinstance(t, str) and t for t in tools)
                or len(set(tools)) != len(tools)
            ):
                raise malformed(f"{what}: tools are distinct non-empty strings")
        if profile["shape"] == "mcp" and not profile.get("tools"):
            raise malformed(f"{what}: a profile of shape mcp gives tools, not empty")
        if "calculator" in profile:
            calculator = closed(profile["calculator"], {"name", "version"}, set(), what + " calculator")
            if not isinstance(calculator["name"], str) or not isinstance(calculator["version"], str):
                raise malformed(f"{what}: calculator name and version are strings")
            if profile["class"] != "record" or profile["shape"] != "mcp":
                raise malformed(f"{what}: a calculator's profile is record and mcp")
        if not in_canon_domain(profile):
            raise malformed(f"{what}: outside the canon domain")
        profiles[profile["id"]] = profile
    return profiles


# ---------------------------------------------------------------------------------------------
# Templates and requests (§4.1)


def instantiate(template: Any, values: dict[str, Any]) -> Any:
    if isinstance(template, dict):
        if len(template) == 1:
            (form, argument), = template.items()
            if form == "$param":
                return values[argument]
            if form == "$text":
                text = argument
                out = []
                position = 0
                while True:
                    start = text.find("{{", position)
                    if start < 0:
                        out.append(text[position:])
                        break
                    end = text.find("}}", start + 2)
                    out.append(text[position:start])
                    out.append(str(integer_of(values[text[start + 2 : end]])))
                    position = end + 2
                return "".join(out)
        return {name: instantiate(member, values) for name, member in template.items()}
    if isinstance(template, list):
        return [instantiate(item, values) for item in template]
    return template


def commits(template: Any) -> tuple[set[str], set[str]]:
    """§4.1: the parameters a request commits, and those it carries only in ambiguous text."""
    committed: set[str] = set()
    ambiguous: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if len(value) == 1 and next(iter(value)) in ("$param", "$text"):
                (form, argument), = value.items()
                if form == "$param":
                    committed.add(argument)
                else:
                    names = set(placeholders(argument))
                    if len(names) == 1:
                        committed.update(names)
                    else:
                        ambiguous.update(names)
                return
            for member in value.values():
                walk(member)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(template)
    return committed, ambiguous - committed


# ---------------------------------------------------------------------------------------------
# Reads (§6)


def apply_unwrap(value: Any, unwrap: list[str]) -> Any:
    for pointer in unwrap:
        text = resolve(value, pointer)
        if not isinstance(text, str):
            raise Finding("read-failed", "an unwrap pointer does not resolve to a string")
        data = text.encode("utf-8")
        if len(data) > MAX_UNWRAPPED_BYTES:
            raise Refused("input-over-bound", "an unwrapped string of more than 200000 bytes")
        try:
            value = read_document(data, "an unwrapped string", MAX_VALUE_DEPTH)
        except Refused as refusal:
            if refusal.name == "input-over-bound":
                raise
            raise Finding("read-failed", "an unwrapped string that is not one JSON value") from refusal
    return value


def copy_claim(copy: dict[str, Any], value: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    availability: dict[str, Any] = {}
    basis: set[str] = set()
    for entry in copy["facts"]:
        basis.add(entry["source"])
        found = resolve(value, entry["source"])
        if found is ABSENT:
            continue
        if not in_canon_domain(found):
            raise Finding("read-failed", "a copied value outside the canon domain")
        write_at(facts, entry["target"], found)
    for entry in copy["evidence"]:
        basis.add(entry["source"])
        found = resolve(value, entry["source"])
        if found is ABSENT:
            continue
        if found not in AVAILABILITY:
            raise Finding("read-failed", "a copied availability of another value")
        availability[entry["requirement"]] = found
    return {
        "facts": facts,
        "evidenceAvailability": availability,
        "acquisitionStatus": "resolved",
        "reason": "copied",
        "basis": sorted(basis),
    }


def evaluate(
    condition: dict[str, Any],
    value: Any,
    params: dict[str, Any],
    basis: set[str],
    declared: dict[str, str],
) -> bool:
    op = condition["op"]
    if op == "always":
        return True
    if op == "all":
        return all(evaluate(c, value, params, basis, declared) for c in condition["of"])
    if op == "any":
        return any(evaluate(c, value, params, basis, declared) for c in condition["of"])
    if op == "not":
        return not evaluate(condition["of"], value, params, basis, declared)
    basis.add(condition["field"])
    found = resolve(value, condition["field"])
    if found is ABSENT:
        return False
    if op == "exists":
        return True
    if op == "equals":
        return json_equal(found, condition["to"])
    if op == "equalsParam":
        return json_equal(found, params[condition["param"]])
    if op == "isTrue":
        return found is True
    if op == "isDecimalString":
        return isinstance(found, str) and re.fullmatch(r"0|[1-9][0-9]*", found) is not None
    if op == "freshWithin":
        # True only for `N` of type `timestamp` and `M` of type `integer` (§6.3), as declared.
        if declared[condition["asOf"]] != "timestamp" or declared[condition["maxAge"]] != "integer":
            return False
        field_instant = instant(found)
        as_of = instant(params[condition["asOf"]])
        if field_instant is None or as_of is None:
            return False
        return 0 <= as_of - field_instant <= integer_of(params[condition["maxAge"]])
    raise AssertionError(op)


def rule_claim(rule: dict[str, Any], value: Any, scope_values: dict[str, Any]) -> dict[str, Any]:
    params = {name: scope_values[name] for name in rule["parameters"]}
    basis: set[str] = set()
    match = None
    for clause in rule["clauses"]:
        if evaluate(clause["when"], value, params, basis, rule["parameters"]):
            match = clause
            break
    assert match is not None
    facts: dict[str, Any] = {}
    for entry in match["claim"]["facts"]:
        found = resolve(value, entry["from"])
        if found is ABSENT:
            raise Finding("read-failed", "a from that does not resolve")
        if not in_canon_domain(found):
            raise Finding("read-failed", "a value outside the canon domain")
        write_at(facts, entry["pointer"], found)
    return {
        "facts": facts,
        "evidenceAvailability": dict(match["claim"]["evidence"]),
        "acquisitionStatus": match["claim"]["acquisitionStatus"],
        "reason": match["reason"],
        "basis": sorted(basis),
    }


# ---------------------------------------------------------------------------------------------
# Acquisitions (§5.2) and calculated values (§7)


def check_acquisition(
    source: Source, profile: dict[str, Any], response: dict[str, Any], request: Any, at: int
) -> None:
    result, receipt, salts = response["result"], response["receipt"], response["salts"]

    def invalid(detail: str) -> Finding:
        return Finding("acquisition-invalid", f"{source.name}: {detail}")

    acquisition = receipt.get("acquisition")
    forms = (
        receipt.get("receiptVersion") == "3",
        receipt.get("kind") == "acquisition",
        is_hex(receipt.get("keyId"), 32),
        is_hex(receipt.get("signature"), 128),
        isinstance(receipt.get("source"), str),
        isinstance(receipt.get("authority"), str),
        isinstance(receipt.get("sessionId"), str),
        is_integer(receipt.get("callIndex")) and integer_of(receipt["callIndex"]) >= 0,
        is_digest(receipt.get("argumentsCommitment")),
        is_digest(receipt.get("resultDigest")),
        isinstance(receipt.get("servedAt"), str),
        isinstance(acquisition, dict),
    )
    if not all(forms):
        raise invalid("a receipt member not of its form")
    if not (
        isinstance(acquisition.get("adapter"), dict)
        and isinstance(acquisition.get("shape"), str)
        and (acquisition.get("endpoint") is None or isinstance(acquisition.get("endpoint"), str))
        and isinstance(acquisition.get("observedAt"), str)
    ):
        raise invalid("an acquisition member not of its form")
    if "pageItems" in acquisition:
        raise invalid("the receipt attests a page, which no preparation reads")
    key = bytes.fromhex(profile["publicKey"])
    if receipt["keyId"] != hashlib.sha256(key).hexdigest()[:32]:
        raise invalid("keyId is not the profile key's")
    unsigned = {name: member for name, member in receipt.items() if name != "signature"}
    try:
        message = b"judgment-pack-gateway/receipt/3:" + canon(unsigned)
    except OutsideDomain as error:
        raise invalid("a receipt outside the canon domain") from error
    if not signature_verifies(key, message, bytes.fromhex(receipt["signature"])):
        raise invalid("the signature does not verify")
    if receipt["source"] != profile["source"] or receipt["authority"] != profile["authority"]:
        raise invalid("source or authority is not the profile's")
    for name in ("adapter", "shape", "endpoint"):
        if not json_equal(acquisition.get(name), profile[name]):
            raise invalid(f"acquisition.{name} is not the profile's")
    commitment = hashlib.sha256(bytes.fromhex(salts["args"]) + b"args:" + canon(request)).hexdigest()
    if receipt["argumentsCommitment"] != "sha256:" + commitment:
        raise invalid("argumentsCommitment is not the request's")
    try:
        result_digest = digest_of(canon(result))
    except OutsideDomain as error:
        raise invalid("a result outside the canon domain") from error
    if receipt["resultDigest"] != result_digest:
        raise invalid("resultDigest is not the result's")
    for moment in (acquisition["observedAt"], receipt["servedAt"]):
        seconds = instant(moment)
        if seconds is None or not at - source.max_age <= seconds <= at + 30:
            raise Finding("acquisition-stale", source.name)


def sessions_in_a_form(receipts: list[dict[str, Any]]) -> bool:
    sessions = [r["sessionId"] for r in receipts]
    indexes = [integer_of(r["callIndex"]) for r in receipts]
    shared = len(set(sessions)) == 1 and len(set(indexes)) == len(indexes)
    apart = len(set(sessions)) == len(sessions) and all(i == 0 for i in indexes)
    return shared or apart


def check_calculation(
    source: Source, profile: dict[str, Any], value: Any, scope_values: dict[str, Any], at: int
) -> dict[str, Any]:
    def invalid(detail: str) -> Finding:
        return Finding("calculation-invalid", f"{source.name}: {detail}")

    answer = value.get("calculation") if isinstance(value, dict) else None
    if not isinstance(answer, dict) or set(answer) != {"calculator", "status", "inputs", "asOf"}:
        raise invalid("the value read has no calculation of its form")
    if not isinstance(answer["calculator"], dict) or set(answer["calculator"]) != {"name", "version"}:
        raise invalid("calculator is not of its form")
    if answer["status"] not in ("computed", "input-missing", "cannot-compute"):
        raise invalid("status of another value")
    if not isinstance(answer["inputs"], dict) or not isinstance(answer["asOf"], dict):
        raise invalid("inputs and asOf are objects")
    if not json_equal(answer["calculator"], profile["calculator"]):
        raise invalid("the calculator is not the profile's")
    assert source.calculation is not None
    bound, tables = source.calculation["inputs"], source.calculation["tables"]
    for name, echoed in answer["inputs"].items():
        if name not in bound:
            raise invalid("an input echoed that is not bound")
        try:
            same = canon(echoed) == canon(scope_values[bound[name]])
        except OutsideDomain:
            same = False
        if not same:
            raise invalid("an input echoed that is not its parameter's value")
    for name, as_of in answer["asOf"].items():
        if name not in tables or instant(as_of) is None:
            raise invalid("a table reported that is not named, or with no instant")
    if answer["status"] == "computed":
        if set(bound) - set(answer["inputs"]):
            raise invalid("a bound input not echoed")
        for name, limit in tables.items():
            if name not in answer["asOf"]:
                raise invalid("a named table not reported")
            seconds = instant(answer["asOf"][name])
            assert seconds is not None
            if not at - integer_of(limit) <= seconds <= at + 30:
                raise invalid("a table older than its limit, or in the future")
    return answer


# ---------------------------------------------------------------------------------------------
# Recomputing a preparation (§§3-9)


@dataclass
class Outcome:
    name: str
    source: Source | None  # None for the case
    read: Read
    klass: str
    generated: bool
    parameters: dict[str, Any]
    skipped: bool = False
    request: Any = None
    receipt: dict[str, Any] | None = None
    claim: dict[str, Any] | None = None
    answer: dict[str, Any] | None = None  # a calculator's calculation, as answered


@dataclass
class Computation:
    preparation: dict[str, Any]
    outcomes: list[Outcome]
    facts: dict[str, Any]
    evidence: dict[str, Any]


def recompute(
    dialect: Dialect,
    case: Any,
    acquisitions: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    verified_at: str,
) -> Computation:
    at = instant(verified_at)
    assert at is not None
    # 1. profile-mismatch
    for source in dialect.sources:
        profile = profiles.get(source.profile_id)
        if profile is None or digest_of(canon(profile)) != source.profile_digest:
            raise Finding("profile-mismatch", f"{source.name}: no trusted profile of that id and digest")
        # §4.1: the request is of the profile's shape's form, and a profile of shape `command`
        # serves no operation; a tool call names a tool the profile allows.
        if profile["shape"] != source.form:
            raise Finding("profile-mismatch", f"{source.name}: a request of the {source.form} form under a {profile['shape']} profile")
        if source.form == "mcp" and source.tool not in profile.get("tools", []):
            raise Finding("profile-mismatch", f"{source.name}: a tool the profile does not allow")
        if ("calculator" in profile) != (source.calculation is not None):
            raise Finding("profile-mismatch", f"{source.name}: calculation and calculator disagree")
    # 2. parameter-invalid, the case's first
    case_values: dict[str, Any] = {}
    for name, parameter in dialect.case_parameters.items():
        found = resolve(case, parameter.pointer)
        if found is ABSENT or not of_type(found, parameter.type):
            raise Finding("parameter-invalid", f"case parameter {name}")
        case_values[name] = found

    outcomes: list[Outcome] = []
    case_scope = dict(case_values)
    case_scope["runAt"] = verified_at
    case_outcome = Outcome("case", None, dialect.case_read, "asserted", False, case_scope)
    case_outcome.claim = copy_claim(dialect.case_read.copy or {}, case)
    outcomes.append(case_outcome)

    receipts: list[dict[str, Any]] = []
    for source in dialect.sources:
        profile = profiles[source.profile_id]
        values = dict(case_values)
        skipped = False
        generated = profile["class"] == "generated"
        for name, parameter in source.parameters.items():
            origin = next(o for o in outcomes if o.name == parameter.origin)
            generated = generated or origin.generated
            if origin.skipped or origin.claim is None or origin.claim["acquisitionStatus"] != "resolved":
                skipped = True
                continue
            found = resolve(origin.claim["facts"], parameter.pointer)
            if found is ABSENT:
                skipped = True
                continue
            if not of_type(found, parameter.type):
                raise Finding("parameter-invalid", f"{source.name} parameter {name}")
            values[name] = found
        values["runAt"] = verified_at
        outcome = Outcome(source.name, source, source.read, profile["class"], generated, values)
        outcomes.append(outcome)
        if skipped:
            outcome.skipped = True
            if source.name in acquisitions:
                raise Finding("acquisition-unexpected", source.name)
            continue
        if source.name not in acquisitions:
            raise Finding("acquisition-missing", source.name)
        response = acquisitions[source.name]["response"]
        outcome.request = instantiate(source.template, values)
        check_acquisition(source, profile, response, outcome.request, at)
        outcome.receipt = response["receipt"]
        receipts.append(response["receipt"])
        if not sessions_in_a_form(receipts):
            raise Finding("acquisition-sessions", source.name)
        value = apply_unwrap(response["result"], source.read.unwrap)
        if source.calculation is not None:
            outcome.answer = check_calculation(source, profile, value, values, at)
            if outcome.answer["status"] != "computed":
                outcome.claim = {
                    "facts": {},
                    "evidenceAvailability": {r: "unknown" for r in source.read.evidence_targets},
                    "acquisitionStatus": "unknown",
                    "reason": "calculation-" + outcome.answer["status"],
                    "basis": ["/calculation/status"],
                }
                continue
        if source.read.copy is not None:
            outcome.claim = copy_claim(source.read.copy, value)
        else:
            assert source.read.rule is not None
            outcome.claim = rule_claim(source.read.rule, value, values)
    named = {s.name for s in dialect.sources}
    for name in acquisitions:
        if name not in named:
            raise Finding("acquisition-unexpected", f"{name} names no source")

    # 4. admission-refused
    for outcome in outcomes:
        for kind, targets in (("fact", outcome.read.fact_targets), ("evidence", outcome.read.evidence_targets)):
            for target in targets:
                admitted = dialect.admits.get((kind, target), ["asserted", "record"])
                if outcome.klass not in admitted or (outcome.generated and "generated" not in admitted):
                    raise Finding("admission-refused", f"{outcome.name} {target}")

    return build(dialect, outcomes, verified_at)


def citation(receipt: dict[str, Any]) -> dict[str, Any]:
    return {name: receipt[name] for name in ("callIndex", "sessionId", "signature")}


def read_digest(read: Read) -> str:
    return digest_of(canon(read.as_written))


def calculation_lineage(dialect: Dialect, outcome: Outcome) -> dict[str, Any]:
    """§7: the calculation member of a calculated source's entries."""
    assert outcome.source is not None and outcome.source.calculation is not None
    assert outcome.answer is not None
    bound = outcome.source.calculation["inputs"]
    inputs = []
    for name in sorted(outcome.answer["inputs"]):
        parameter_name = bound[name]
        parameter = outcome.source.parameters.get(parameter_name)
        if parameter is None:
            parameter = dialect.case_parameters[parameter_name]
        inputs.append(
            {"name": name, "parameter": parameter_name, "source": parameter.origin, "pointer": parameter.pointer}
        )
    return {
        "calculator": outcome.answer["calculator"],
        "status": outcome.answer["status"],
        "asOf": outcome.answer["asOf"],
        "inputs": inputs,
    }


def build(dialect: Dialect, outcomes: list[Outcome], verified_at: str) -> Computation:
    cites_order = []
    for position, outcome in enumerate(outcomes):
        if outcome.receipt is not None:
            cites_order.append((integer_of(outcome.receipt["callIndex"]), position, citation(outcome.receipt)))
    cites = [entry for _, _, entry in sorted(cites_order, key=lambda item: (item[0], item[1]))]

    lineage = []
    out_outcomes = []
    facts_document: dict[str, Any] = {}
    evidence_document: dict[str, Any] = {}
    for outcome in outcomes:
        status = "dependency-unavailable" if outcome.skipped else outcome.claim["acquisitionStatus"]
        reason = "dependency-unavailable" if outcome.skipped else outcome.claim["reason"]
        entry_outcome: dict[str, Any] = {
            "name": outcome.name,
            "parameters": dict(outcome.parameters),
            "status": status,
            "reason": reason,
        }
        if outcome.request is not None:
            entry_outcome["arguments"] = outcome.request
        if outcome.claim is not None:
            entry_outcome["claim"] = outcome.claim
        out_outcomes.append(entry_outcome)
        claim = outcome.claim or {"facts": {}, "evidenceAvailability": {}, "basis": []}
        for kind, targets in (
            ("fact", sorted(outcome.read.fact_targets)),
            ("evidence", sorted(outcome.read.evidence_targets)),
        ):
            for target in targets:
                if kind == "fact":
                    present = resolve(claim["facts"], target) is not ABSENT
                else:
                    present = target in claim["evidenceAvailability"]
                entry: dict[str, Any] = {
                    "source": outcome.name,
                    "kind": kind,
                    "target": target,
                    "class": outcome.klass,
                    "generatedInfluence": outcome.generated,
                    "present": present,
                    "status": status,
                    "reason": reason,
                    "basis": [] if outcome.skipped else list(claim["basis"]),
                    "readDigest": read_digest(outcome.read),
                }
                candidates = sorted(set(outcome.read.candidates.get((kind, target), [])))
                if candidates:
                    entry["candidateFrom"] = candidates
                if outcome.receipt is not None:
                    entry["receipt"] = citation(outcome.receipt)
                if outcome.answer is not None:
                    entry["calculation"] = calculation_lineage(dialect, outcome)
                lineage.append(entry)
                if kind == "fact" and present:
                    write_at(facts_document, target, resolve(claim["facts"], target))
                if kind == "evidence" and present:
                    evidence_document[target] = claim["evidenceAvailability"][target]
    preparation = {
        "version": 2,
        "verifiedAt": verified_at,
        "mappingDigest": digest_of(canon(dialect.document)),
        "verification": VERIFICATION,
        "cites": cites,
        "lineage": lineage,
        "outcomes": out_outcomes,
    }
    return Computation(preparation, outcomes, facts_document, evidence_document)


# ---------------------------------------------------------------------------------------------
# The record (§11)


def _skip_string(text: str, i: int) -> int:
    assert text[i] == '"'
    i += 1
    while text[i] != '"':
        i += 2 if text[i] == "\\" else 1
    return i + 1


def _skip_value(text: str, i: int) -> int:
    if text[i] == '"':
        return _skip_string(text, i)
    if text[i] in "{[":
        depth = 0
        while True:
            c = text[i]
            if c == '"':
                i = _skip_string(text, i)
                continue
            if c in "{[":
                depth += 1
            elif c in "}]":
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
    while i < len(text) and text[i] not in ",}] \t\r\n":
        i += 1
    return i


def top_level_members(text: str) -> list[tuple[str, str]]:
    """Each top-level member's name and its value as the line writes it."""
    members = []
    i = 0
    whitespace = " \t\r\n"
    while text[i] in whitespace:
        i += 1
    assert text[i] == "{"
    i += 1
    while True:
        while text[i] in whitespace:
            i += 1
        if text[i] == "}":
            return members
        end = _skip_string(text, i)
        name = json.loads(text[i:end])
        i = end
        while text[i] in whitespace:
            i += 1
        assert text[i] == ":"
        i += 1
        while text[i] in whitespace:
            i += 1
        end = _skip_value(text, i)
        members.append((name, text[i:end]))
        i = end
        while text[i] in whitespace:
            i += 1
        if text[i] == ",":
            i += 1


@dataclass
class Record:
    value: dict[str, Any]
    binding: bytes | None


def read_record(data: bytes) -> Any:
    """The record read as one line holding one JSON value (§11, the second phase)."""
    if b"\n" in data or b"\r" in data:
        raise malformed("the record is not one line")
    return read_document(data, "the record")


# §11: two names differ "but for case" when they are equal once A-Z are mapped to a-z, and nothing
# else is: ASCII case only, no other folding.
ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def parse_record(data: bytes, value: Any) -> Record:
    """The record's form (§11, the fourth phase), and its binding as the line writes it."""
    if not isinstance(value, dict) or not isinstance(value.get("inputs"), dict):
        raise malformed("the record is not an evaluation record with inputs")
    binding = None
    for name, raw in top_level_members(data.decode("utf-8")):
        if name.translate(ASCII_LOWER) == "binding" and name != "binding":
            raise malformed("a member named binding but for case")
        if name == "binding":
            binding = raw.encode("utf-8")
    return Record(value, binding)


def record_of_export(run: bytes) -> bytes | None:
    """The record line a Runner export's run.json holds (conformance/dialect/README.md): the bytes
    `run.auditBytes` holds in standard base64; or, in an export of version 2, which carries no bytes,
    the member `run.audit`'s value exactly as run.json writes it, with no re-encoding (§11). None when
    it holds neither."""
    document = read_document(run, "run.json")
    if not isinstance(document, dict) or not isinstance(document.get("run"), dict):
        return None
    held = dict(top_level_members(dict(top_level_members(run.decode("utf-8")))["run"]))
    if "auditBytes" in held:
        return base64.b64decode(json.loads(held["auditBytes"]), validate=True)
    if "audit" in held:
        return held["audit"].encode("utf-8")
    return None


# ---------------------------------------------------------------------------------------------
# The reading (§11)


def unsigned_parameters(dialect: Dialect, computation: Computation) -> list[dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    ordered = []
    for outcome in computation.outcomes[1:]:
        source = outcome.source
        assert source is not None
        if outcome.skipped or source.read.rule is None:
            continue
        if outcome.answer is not None and outcome.answer["status"] != "computed":
            continue
        targets = len(source.read.fact_targets) + len(source.read.evidence_targets)
        if not targets:
            continue
        named: set[str] = set()

        def walk(condition: dict[str, Any]) -> None:
            op = condition["op"]
            if op == "equalsParam":
                named.add(condition["param"])
            elif op == "freshWithin":
                named.update((condition["asOf"], condition["maxAge"]))
            elif op in ("all", "any"):
                for c in condition["of"]:
                    walk(c)
            elif op == "not":
                walk(condition["of"])

        for clause in source.read.rule["clauses"]:
            walk(clause["when"])
        committed, ambiguous = commits(source.template)
        if outcome.answer is not None and source.calculation is not None:
            for name in outcome.answer["inputs"]:
                committed.add(source.calculation["inputs"][name])
        listed = []
        for name in sorted(named - committed):
            if name == "runAt":
                listed.append({"name": name, "kind": "runAt"})
                continue
            parameter = source.parameters.get(name)
            if parameter is None:
                kind = "case"
            else:
                upstream = entries.get(parameter.origin)
                if upstream is None:
                    continue
                kinds = {p["kind"] for p in upstream["parameters"]}
                if kinds & {"case", "local-file", "upstream", "ambiguous-text"}:
                    kind = "upstream"
                else:
                    kind = "upstream-runAt"
            if kind in ("case", "local-file", "upstream") and name in ambiguous:
                kind = "ambiguous-text"
            listed.append({"name": name, "kind": kind})
        if listed:
            entry = {"source": source.name, "parameters": listed, "targets": targets}
            entries[source.name] = entry
            ordered.append(entry)
    return ordered


def unsigned_freshness(computation: Computation, verified_at: str) -> dict[str, Any] | None:
    sources = []
    for outcome in computation.outcomes[1:]:
        if outcome.skipped or outcome.receipt is None:
            continue
        checks = ["acquisition"]
        if outcome.answer is not None and outcome.answer["status"] == "computed":
            checks.append("calculation")
        targets = len(outcome.read.fact_targets) + len(outcome.read.evidence_targets)
        sources.append({"source": outcome.name, "checks": checks, "targets": targets})
    if not sources:
        return None
    return {"against": "preparation.verifiedAt", "verifiedAt": verified_at, "sources": sources}


def as_plain(value: Any) -> Any:
    """A value with each number as Python reads it, for comparison and printing."""
    if isinstance(value, Num):
        return int(value.literal) if value.is_integer() else float(value.value)
    if isinstance(value, dict):
        return {name: as_plain(member) for name, member in value.items()}
    if isinstance(value, list):
        return [as_plain(item) for item in value]
    return value


@dataclass
class Verification:
    answer: dict[str, Any]
    preparation: bytes | None = None
    digest: str | None = None
    facts: Any = None
    evidence: Any = None


def verify(
    dialect: bytes,
    case: bytes,
    acquisitions: bytes,
    profiles: bytes,
    preparation: bytes,
    record: bytes | None = None,
    require_binding: bool = False,
) -> Verification:
    """§11: a refusal, a finding, or a reading."""
    result = Verification(answer={})
    try:
        if len(dialect) > DIALECT_BYTES or len(dialect) + len(case) + len(acquisitions) > ENVELOPE_BYTES:
            raise Refused("input-over-bound", "the dialect, case and acquisitions")
        if len(profiles) > PROFILES_BYTES:
            raise Refused("input-over-bound", "the profiles")
        if len(preparation) > PREPARATION_BYTES or (record is not None and len(record) > RECORD_BYTES):
            raise Refused("input-over-bound", "the preparation or the record")
        # §11's phases, in order: the bounds measured on bytes, on every document before any is
        # read; every document read; the counted bounds; every form; the kinds; and only then the
        # recomputation.
        documents = [
            (dialect, "the dialect", MAX_DOCUMENT_DEPTH),
            (case, "the case", MAX_VALUE_DEPTH),
            (acquisitions, "the acquisitions", MAX_DOCUMENT_DEPTH),
            (profiles, "the profiles", MAX_DOCUMENT_DEPTH),
            (preparation, "the preparation", MAX_DOCUMENT_DEPTH),
        ]
        if record is not None:
            documents.append((record, "the record", MAX_DOCUMENT_DEPTH))
        for data, what, depth in documents:
            measure(data, what, depth)
        dialect_document = read_document(dialect, "the dialect")
        case_document = read_document(case, "the case", MAX_VALUE_DEPTH)
        acquisitions_document = read_document(acquisitions, "the acquisitions")
        profiles_document = read_document(profiles, "the profiles")
        given = read_document(preparation, "the preparation")
        record_document = read_record(record) if record is not None else None
        count_bounds(dialect_document, acquisitions_document)
        # §11, the fourth phase: a dialect of a version this reader does not read is refused before any
        # form is checked. Version 3 is defined (§4.3, §4.4) and not read here.
        if isinstance(dialect_document, dict) and is_integer(dialect_document.get("version")):
            if integer_of(dialect_document["version"]) == 3:
                raise Refused(
                    "version-unread",
                    "dialect version 3 — the unbound source form and its binding document (§4.4), and "
                    "the kinds of §4.3 — is defined, and not read by this reader",
                )
        parsed_record = parse_record(record, record_document) if record is not None else None
        if not isinstance(acquisitions_document, dict):
            raise malformed("the acquisitions are not an object")
        for name, member in acquisitions_document.items():
            closed(member, {"response"}, set(), f"acquisition {name}")
            response = closed(member["response"], {"result", "receipt", "salts"}, set(), f"acquisition {name}")
            if not isinstance(response["receipt"], dict):
                raise malformed(f"acquisition {name}: the receipt is not an object")
            salts = closed(response["salts"], {"args"}, {"statement"}, f"acquisition {name} salts")
            if not all(is_hex(salt, 64) for salt in salts.values()):
                raise malformed(f"acquisition {name}: a salt of another form")
        if not isinstance(given, dict) or instant(given.get("verifiedAt")) is None:
            raise malformed("the preparation's verifiedAt is not a timestamp with an instant")
        trusted = parse_profiles(profiles_document)
        parsed_dialect = parse_dialect(dialect_document)
        verified_at = given["verifiedAt"]

        computation = recompute(parsed_dialect, case_document, acquisitions_document, trusted, verified_at)
        result.preparation = preparation_bytes(computation.preparation)
        result.digest = digest_of(result.preparation)
        result.facts = as_plain(computation.facts)
        result.evidence = as_plain(computation.evidence)
        try:
            given_bytes = preparation_bytes(given)
        except OutsideDomain:
            given_bytes = None
        if given_bytes != result.preparation:
            raise Finding("preparation-differs")
        binding = "not-checked"
        if parsed_record is not None:
            inputs = parsed_record.value["inputs"]
            record_cites = parsed_record.value.get("cites", [])
            cites = computation.preparation["cites"]
            # As sets: a citation either side gives twice is one member, and how many times one is
            # given is not compared (§11, finding 6).
            same_cites = (
                isinstance(record_cites, list)
                and all(any(json_equal(a, b) for b in cites) for a in record_cites)
                and all(any(json_equal(a, b) for b in record_cites) for a in cites)
            )
            if (
                not json_equal(inputs.get("facts", ABSENT), computation.facts)
                or not json_equal(inputs.get("evidence", ABSENT), computation.evidence)
                or not same_cites
            ):
                raise Finding("record-inputs-differ")
            if parsed_record.binding is None:
                binding = "absent"
            else:
                member = parsed_record.value["binding"]
                if not (isinstance(member, dict) and member.get("kind") == BINDING_KIND):
                    raise Finding("binding-foreign-kind")
                if parsed_record.binding != binding_of(result.digest):
                    raise Finding("binding-mismatch")
                binding = "matches"
        if require_binding and binding != "matches":
            raise Finding("unbound")
        counts = {"asserted": 0, "record": 0, "generated": 0}
        for entry in computation.preparation["lineage"]:
            counts[entry["class"]] += 1
        reading: dict[str, Any] = {
            "digest": result.digest,
            "binding": binding,
            "facts": computation.facts,
            "evidence": computation.evidence,
            "targetsByClass": counts,
        }
        parameters = unsigned_parameters(parsed_dialect, computation)
        if parameters:
            reading["unsignedParameters"] = parameters
        freshness = unsigned_freshness(computation, verified_at)
        if freshness:
            reading["unsignedFreshness"] = freshness
        result.answer = {"reading": reading}
    except Refused as refusal:
        result.answer = {"refused": refusal.name, "detail": str(refusal)}
    except Finding as finding:
        result.answer = {"finding": finding.name, "detail": str(finding)}
    return result


def report(answer: dict[str, Any]) -> dict[str, Any]:
    """§11, the report: one object whose `result` is `reading`, `refusal` or `finding`, with exactly
    the members that form carries."""
    if "reading" in answer:
        return {"result": "reading", **answer["reading"]}
    if "finding" in answer:
        return {"result": "finding", "finding": answer["finding"]}
    return {"result": "refusal", "refusal": answer["refused"]}


# §11: a program exits 0 for a reading, 1 for a refusal, 2 for a finding, and 3 when it could not run.
EXIT_STATUS = {"reading": 0, "refusal": 1, "finding": 2}
COULD_NOT_RUN = 3


class _Arguments(argparse.ArgumentParser):
    def exit(self, status: int = 0, message: str | None = None) -> NoReturn:
        # argparse leaves by this door when no reading was run, for its help or for an argument it
        # does not take; §11 gives that one status, not argparse's 0 or 2, which are a reading's and
        # a finding's.
        super().exit(COULD_NOT_RUN, message)


def main(argv: list[str] | None = None) -> int:
    parser = _Arguments(description=__doc__.splitlines()[0])
    parser.add_argument("--dialect", required=True, type=Path)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--acquisitions", type=Path, help="absent: no acquisitions, {}")
    parser.add_argument("--profiles", required=True, type=Path)
    parser.add_argument("--preparation", required=True, type=Path)
    parser.add_argument("--record", type=Path, help="one record line, without its newline")
    parser.add_argument("--require-binding", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        documents = (
            arguments.dialect.read_bytes(),
            arguments.case.read_bytes(),
            arguments.acquisitions.read_bytes() if arguments.acquisitions else b"{}",
            arguments.profiles.read_bytes(),
            arguments.preparation.read_bytes(),
            arguments.record.read_bytes() if arguments.record else None,
        )
        outcome = verify(*documents, arguments.require_binding)
        answer = report(outcome.answer)
        line = preparation_bytes(answer) + b"\n"
    except Exception as error:  # a file it cannot open, or a fault of its own: never 1 or 2
        print(f"dialect_verify: could not run: {error!r}", file=sys.stderr)
        return COULD_NOT_RUN
    sys.stdout.buffer.write(line)
    sys.stdout.flush()
    if "detail" in outcome.answer:
        print(f"dialect_verify: {outcome.answer['detail']}", file=sys.stderr)
    return EXIT_STATUS[answer["result"]]


if __name__ == "__main__":
    sys.exit(main())

"""A second reader of the registry companion, format 1.1.0, status proposed (spec/registry-1.1.0.md).

It was written from the text alone: spec/registry-1.1.0.md, the format 1.0.0 text it builds on
(spec/registry.md: admission, canonical form, kind declarations, the schema and pattern subsets,
validation, resolution and the emitter manifest's `owns`), checkpoint-witness.md §§1 and 5 for the
key identifier, the key rule and the equation, RFC 8785 for canonical JSON, RFC 6901 for pointers,
RFC 3986 for URIs and RFC 8032 for Ed25519. It ports no other reader, and no row's expected result
was read before it first ran over every row. Its agreement with the rows under
conformance/registry/1.1.0/ is checked by tests/test_registry_1_1_0_reader.py. It was written by a
model from the drafting vendor: a same-vendor reader, not a cross-vendor claim. How it was written
is in tools/registry_1_1_0_reader_README.md.

It reads bytes only. It opens no network connection, starts no program and fetches nothing: every
document is given to it. It is a test reader. It holds each document's size bound before parsing
and its depth bound while parsing, but it matches patterns with Python's backtracking `re`, which
registry §3.4 does not allow a conformant reader on adversarial input, and its Ed25519 arithmetic
is neither constant-time nor fast. It is not for production input.

It does not import YAML (registry §9): a path ending in `.yaml` or `.yml` is refused with
`NotImplementedError`, and no row names one.

Where the text does not say a form, the reader takes the one named in a comment marked READING.

    report = assemble(rows_input)                 # §4: the report, and the written documents
    report = check_index(...)                     # §5.1
    lock_or_refusal = write_lock(...)             # §8
    report = check_lock(...)                      # §9
    report = coverage(...)                        # §9.1
    report, record = verify(...)                  # §11
"""
from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from typing import Any

MAX_SAFE = 2 ** 53 - 1
KIB = 1024
MIB = 1024 * 1024


class _Absent:
    """A member that is not there, told apart from a JSON null."""

    def __repr__(self) -> str:
        return "ABSENT"


ABSENT = _Absent()

# ---------------------------------------------------------------------------------------------------
# Pointers (RFC 6901)


def escape_token(token: Any) -> str:
    return str(token).replace("~", "~0").replace("/", "~1")


def pointer(*tokens: Any) -> str:
    return "".join("/" + escape_token(t) for t in tokens)


def split_pointer(text: str) -> list[str] | None:
    """The tokens of an RFC 6901 pointer, or None when it is not one."""
    if text == "":
        return []
    if not text.startswith("/"):
        return None
    out = []
    for raw in text[1:].split("/"):
        if re.search(r"~(?![01])", raw):
            return None
        out.append(raw.replace("~1", "/").replace("~0", "~"))
    return out


INDEX_TOKEN = re.compile(r"(?:0|[1-9][0-9]{0,8})\Z")


def lookup(value: Any, tokens: list[str]) -> Any:
    for token in tokens:
        if isinstance(value, dict):
            if token not in value:
                return ABSENT
            value = value[token]
        elif isinstance(value, list):
            if not re.fullmatch(r"0|[1-9][0-9]*", token) or int(token) >= len(value):
                return ABSENT
            value = value[int(token)]
        else:
            return ABSENT
    return value


# ---------------------------------------------------------------------------------------------------
# JSON values: numbers, equality, canonical form (registry §2.3, RFC 8785)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_integer_value(value: Any) -> bool:
    return is_number(value) and (isinstance(value, int) or float(value).is_integer())


def is_count(value: Any) -> bool:
    # Registry §3.2: a number with a non-negative integer value of at most 2^53 - 1.
    return is_integer_value(value) and 0 <= value <= MAX_SAFE


def json_equal(a: Any, b: Any) -> bool:
    """Registry §7.2's JSON equality: numbers by value, objects regardless of member order."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a is b
    if a is None or b is None:
        return a is None and b is None
    if is_number(a) and is_number(b):
        return a == b
    if isinstance(a, str) and isinstance(b, str):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(json_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(json_equal(a[k], b[k]) for k in a)
    return False


def _es_number(x: float) -> str:
    """ECMAScript's Number::toString for a finite double, as RFC 8785 writes numbers."""
    if x == 0:
        return "0"
    sign = "-" if x < 0 else ""
    x = abs(x)
    tup = Decimal(repr(x)).as_tuple()
    digits = "".join(str(d) for d in tup.digits).lstrip("0")
    exponent = tup.exponent
    stripped = digits.rstrip("0")
    exponent += len(digits) - len(stripped)
    digits = stripped
    k = len(digits)
    n = exponent + k
    if k <= n <= 21:
        return sign + digits + "0" * (n - k)
    if 0 < n <= 21:
        return sign + digits[:n] + "." + digits[n:]
    if -6 < n <= 0:
        return sign + "0." + "0" * (-n) + digits
    e = n - 1
    mark = "+" if e >= 0 else "-"
    if k == 1:
        return sign + digits + "e" + mark + str(abs(e))
    return sign + digits[0] + "." + digits[1:] + "e" + mark + str(abs(e))


_JCS_ESCAPES = {'"': '\\"', "\\": "\\\\", "\b": "\\b", "\f": "\\f", "\n": "\\n", "\r": "\\r", "\t": "\\t"}


def _jcs_string(text: str) -> str:
    out = ['"']
    for ch in text:
        if ch in _JCS_ESCAPES:
            out.append(_JCS_ESCAPES[ch])
        elif ord(ch) < 0x20:
            out.append("\\u%04x" % ord(ch))
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def jcs(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _jcs_string(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _es_number(value)
    if isinstance(value, list):
        return "[" + ",".join(jcs(v) for v in value) + "]"
    if isinstance(value, dict):
        members = sorted(value.items(), key=lambda kv: kv[0].encode("utf-16-be"))
        return "{" + ",".join(_jcs_string(k) + ":" + jcs(v) for k, v in members) + "}"
    raise TypeError(f"not a JSON value: {type(value).__name__}")


def jcs_bytes(value: Any) -> bytes:
    return jcs(value).encode("utf-8")


def sha256_digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def digest_of(value: Any) -> str:
    """Registry §2.3: a document's identity is the digest of its JCS bytes."""
    return sha256_digest(jcs_bytes(value))


def depth_of(value: Any, level: int = 1) -> int:
    if isinstance(value, dict):
        return max([level] + [depth_of(v, level + 1) for v in value.values()])
    if isinstance(value, list):
        return max([level] + [depth_of(v, level + 1) for v in value])
    return level - 1


# ---------------------------------------------------------------------------------------------------
# Admission (registry §2.2)


class _Stop(Exception):
    def __init__(self, code: str, at: str) -> None:
        super().__init__(code)
        self.code = code
        self.at = at


_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
_HEX4 = re.compile(r"[0-9a-fA-F]{4}")
_SIMPLE_ESCAPES = {'"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}


class _BadNumber:
    pass


def _admit_number(literal: str) -> Any:
    if not any(c in literal for c in ".eE"):
        value = int(literal)
        if literal.startswith("-") and value == 0:
            return _BadNumber()
        if abs(value) > MAX_SAFE:
            return _BadNumber()
        return value
    exact = Decimal(literal)
    if exact.is_zero() and literal.startswith("-"):
        return _BadNumber()
    adjusted = exact.adjusted() if not exact.is_zero() else 0
    if adjusted > 400 or adjusted < -400:
        return _BadNumber()
    as_double = float(literal)
    if as_double in (float("inf"), float("-inf")):
        return _BadNumber()
    if Decimal(repr(as_double)) != exact:
        return _BadNumber()
    return as_double


class _Parser:
    def __init__(self, text: str, max_depth: int) -> None:
        self.s = text
        self.i = 0
        self.n = len(text)
        self.max_depth = max_depth
        self.bad_numbers: list[str] = []
        self.lone_surrogate = False

    def fail(self) -> None:
        raise _Stop("REG-DOC-JSON", "")

    def ws(self) -> None:
        while self.i < self.n and self.s[self.i] in " \t\n\r":
            self.i += 1

    def value(self, at: str, depth: int) -> Any:
        self.ws()
        if self.i >= self.n:
            self.fail()
        c = self.s[self.i]
        if c == "{":
            return self.obj(at, depth + 1)
        if c == "[":
            return self.arr(at, depth + 1)
        if c == '"':
            return self.string()
        for word, val in (("true", True), ("false", False), ("null", None)):
            if self.s.startswith(word, self.i):
                self.i += len(word)
                return val
        if c == "-" or "0" <= c <= "9":
            m = _NUMBER.match(self.s, self.i)
            if not m:
                self.fail()
            self.i = m.end()
            admitted = _admit_number(m.group())
            if isinstance(admitted, _BadNumber):
                self.bad_numbers.append(at)
            return admitted
        self.fail()

    def obj(self, at: str, depth: int) -> dict:
        if depth > self.max_depth:
            raise _Stop("REG-DOC-DEPTH", at)
        self.i += 1
        out: dict = {}
        self.ws()
        if self.i < self.n and self.s[self.i] == "}":
            self.i += 1
            return out
        while True:
            self.ws()
            if self.i >= self.n or self.s[self.i] != '"':
                self.fail()
            name = self.string()
            member = at + "/" + escape_token(name)
            if name in out:
                raise _Stop("REG-DOC-DUPLICATE", member)
            self.ws()
            if self.i >= self.n or self.s[self.i] != ":":
                self.fail()
            self.i += 1
            out[name] = self.value(member, depth)
            self.ws()
            if self.i >= self.n:
                self.fail()
            c = self.s[self.i]
            self.i += 1
            if c == "}":
                return out
            if c != ",":
                self.fail()

    def arr(self, at: str, depth: int) -> list:
        if depth > self.max_depth:
            raise _Stop("REG-DOC-DEPTH", at)
        self.i += 1
        out: list = []
        self.ws()
        if self.i < self.n and self.s[self.i] == "]":
            self.i += 1
            return out
        while True:
            out.append(self.value(at + "/" + str(len(out)), depth))
            self.ws()
            if self.i >= self.n:
                self.fail()
            c = self.s[self.i]
            self.i += 1
            if c == "]":
                return out
            if c != ",":
                self.fail()

    def string(self) -> str:
        self.i += 1
        out = []
        while True:
            if self.i >= self.n:
                self.fail()
            c = self.s[self.i]
            if c == '"':
                self.i += 1
                return "".join(out)
            if c == "\\":
                self.i += 1
                if self.i >= self.n:
                    self.fail()
                e = self.s[self.i]
                if e in _SIMPLE_ESCAPES:
                    out.append(_SIMPLE_ESCAPES[e])
                    self.i += 1
                elif e == "u":
                    code = self._hex4(self.i + 1)
                    self.i += 5
                    if 0xD800 <= code <= 0xDBFF and self.s.startswith("\\u", self.i):
                        low = self._hex4(self.i + 2)
                        if 0xDC00 <= low <= 0xDFFF:
                            self.i += 6
                            out.append(chr(0x10000 + ((code - 0xD800) << 10) + (low - 0xDC00)))
                            continue
                    if 0xD800 <= code <= 0xDFFF:
                        self.lone_surrogate = True
                    out.append(chr(code))
                else:
                    self.fail()
            elif ord(c) < 0x20:
                self.fail()
            else:
                out.append(c)
                self.i += 1

    def _hex4(self, at: int) -> int:
        m = _HEX4.match(self.s, at)
        if not m:
            self.fail()
        return int(m.group(), 16)


def parse_json(data: bytes, max_depth: int = 32) -> tuple[Any, list[tuple[str, str]]]:
    """Registry §2.2 steps 2 and 3: the value, or the refusals (code, pointer). Admitted numbers are
    replaced by their canonical form: an int, or the double a non-integer literal equals."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None, [("REG-DOC-JSON", "")]
    parser = _Parser(text, max_depth)
    try:
        value = parser.value("", 0)
        parser.ws()
        if parser.i != parser.n:
            return None, [("REG-DOC-JSON", "")]
    except _Stop as stop:
        return None, [(stop.code, stop.at)]
    if parser.lone_surrogate:
        return None, [("REG-DOC-STRING", "")]
    if parser.bad_numbers:
        return None, [("REG-DOC-NUMBER", at) for at in parser.bad_numbers]
    return value, []


def admit(data: bytes, bound: int, selector: str, supported: tuple[str, ...]) -> tuple[Any, list[tuple[str, str]]]:
    """Registry §2.2, all four steps: (value, []) or (None, refusals)."""
    if len(data) > bound:
        return None, [("REG-DOC-SIZE", "")]
    value, refusals = parse_json(data)
    if refusals:
        return None, refusals
    if not isinstance(value, dict):
        return None, [("REG-DOC-SELECTOR", "")]
    if not isinstance(value.get(selector), str) or value[selector] not in supported:
        return None, [("REG-DOC-SELECTOR", pointer(selector))]
    return value, []


# ---------------------------------------------------------------------------------------------------
# Diagnostics and reports (registry §§7.3, 7.4; §2.1)

WARNINGS = frozenset({
    "REG-KIND-DEPRECATED", "REG-PIN-UNPINNED", "REG-VALUE-DEPRECATED", "REG-REPORT-TRUNCATED",
    "REF-SECRET-UNSCOPED", "FACTS-POINTER-UNKNOWN", "FACTS-TYPE-ORDERED", "FACTS-VALUE-UNREACHABLE",
    "EMIT-DEPRECATED", "EMIT-ENV-UNSET", "EMIT-REPORT-TRUNCATED", "EMIT-STAGING-LEFTOVER", "EMIT-LINK-OMITTED",
})

REPORT_CAP = 1000


def diag(code: str, document: str, at: str, **members: Any) -> dict:
    location = {"document": document}
    for name, value in members.items():
        if value is not None and value is not ABSENT:
            location[name] = value
    location["pointer"] = at
    return {"code": code, "location": location}


def severity(code: str) -> str:
    return "warning" if code in WARNINGS else "error"


def _order_key(d: dict) -> tuple:
    loc = d["location"]
    entry = loc.get("entry") or {}
    return (loc.get("document", ""), loc.get("source", ""), loc.get("keyId", ""), loc.get("kindDocument", ""),
            loc.get("kind", ""), entry.get("kind", ""), entry.get("id", ""), loc.get("environment", ""),
            loc.get("pointer", ""), loc.get("line", 0), loc.get("column", 0), d["code"])


def ordered(diagnostics: list[dict]) -> list[dict]:
    """Registry §7.4's order, with §2.1's `source` directly after `document`; equal ones are one."""
    seen: dict[tuple, dict] = {}
    for d in diagnostics:
        seen.setdefault(_order_key(d), d)
    return [seen[k] for k in sorted(seen)]


def report(version: str, diagnostics: list[dict], registry_digest: str | None = None) -> dict:
    found = ordered(diagnostics)
    valid = not any(severity(d["code"]) == "error" for d in found)
    listed = found[:REPORT_CAP]
    out_diags = []
    for d in listed:
        out_diags.append({"code": d["code"], "severity": severity(d["code"]),
                          "message": "registry diagnostic " + d["code"], "location": d["location"]})
    if len(found) > REPORT_CAP:
        out_diags.append({"code": "REG-REPORT-TRUNCATED", "severity": "warning",
                          "message": "registry diagnostic REG-REPORT-TRUNCATED",
                          "location": {"document": "registry", "pointer": ""}})
    out: dict = {"reportFormatVersion": version, "valid": valid}
    if registry_digest is not None:
        out["registry"] = {"digest": registry_digest}
    out["diagnostics"] = out_diags
    return out


# ---------------------------------------------------------------------------------------------------
# Forms shared by several documents

KIND_NAME = re.compile(r"[a-z][a-z0-9-]{0,62}\Z")
OWNER = re.compile(r"[A-Za-z0-9._@/-]{1,128}\Z")
ENVIRONMENT = re.compile(r"[a-z][a-z0-9-]{0,31}\Z")
ENTRY_ID = re.compile(r"[\x21-\x22\x24-\x2e\x30-\x7e]{1,128}\Z")
SEMVER = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(-(0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)(\.(0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
PROJECT = re.compile(r"[a-z][a-z0-9-]{4,28}[a-z0-9]\Z")
SECRET_NAME = re.compile(r"[A-Za-z0-9_-]{1,255}\Z")
SECRET_VERSION = re.compile(r"[1-9][0-9]{0,8}\Z")


def matches(rx: re.Pattern, value: Any) -> bool:
    return isinstance(value, str) and rx.match(value) is not None


# RFC 3986, absolute-URI = scheme ":" hier-part [ "?" query ]
_UNRESERVED = r"A-Za-z0-9\-._~"
_SUB_DELIMS = r"!$&'()*+,;="
_PCT = r"%[0-9A-Fa-f]{2}"
_PCHAR = rf"(?:[{_UNRESERVED}{_SUB_DELIMS}:@]|{_PCT})"
_SEGMENT = rf"{_PCHAR}*"
_SEGMENT_NZ = rf"{_PCHAR}+"
_USERINFO = rf"(?:[{_UNRESERVED}{_SUB_DELIMS}:]|{_PCT})*"
_DEC_OCTET = r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"
_IPV4 = rf"{_DEC_OCTET}\.{_DEC_OCTET}\.{_DEC_OCTET}\.{_DEC_OCTET}"
_H16 = r"[0-9A-Fa-f]{1,4}"
_LS32 = rf"(?:{_H16}:{_H16}|{_IPV4})"
_IPV6 = (rf"(?:(?:{_H16}:){{6}}{_LS32}|::(?:{_H16}:){{5}}{_LS32}|(?:{_H16})?::(?:{_H16}:){{4}}{_LS32}"
         rf"|(?:(?:{_H16}:){{0,1}}{_H16})?::(?:{_H16}:){{3}}{_LS32}|(?:(?:{_H16}:){{0,2}}{_H16})?::(?:{_H16}:){{2}}{_LS32}"
         rf"|(?:(?:{_H16}:){{0,3}}{_H16})?::{_H16}:{_LS32}|(?:(?:{_H16}:){{0,4}}{_H16})?::{_LS32}"
         rf"|(?:(?:{_H16}:){{0,5}}{_H16})?::{_H16}|(?:(?:{_H16}:){{0,6}}{_H16})?::)")
_IPVFUTURE = rf"v[0-9A-Fa-f]+\.[{_UNRESERVED}{_SUB_DELIMS}:]+"
_HOST = rf"(?:\[(?:{_IPV6}|{_IPVFUTURE})\]|{_IPV4}|(?:[{_UNRESERVED}{_SUB_DELIMS}]|{_PCT})*)"
_AUTHORITY = rf"(?:(?P<userinfo>{_USERINFO})@)?{_HOST}(?::[0-9]*)?"
_HIER = rf"(?://{_AUTHORITY}(?:/{_SEGMENT})*|/(?:{_SEGMENT_NZ}(?:/{_SEGMENT})*)?|{_SEGMENT_NZ}(?:/{_SEGMENT})*|)"
_QUERY = rf"(?:{_PCHAR}|[/?])*"
ABSOLUTE_URI = re.compile(rf"[A-Za-z][A-Za-z0-9+\-.]*:{_HIER}(?P<query>\?{_QUERY})?\Z")


def absolute_uri(value: Any, limit: int = 2048) -> re.Match | None:
    """Registry §3.1: an RFC 3986 absolute-URI of at most `limit` characters, with no white space."""
    if not isinstance(value, str) or len(value) > limit:
        return None
    return ABSOLUTE_URI.match(value)


# ---------------------------------------------------------------------------------------------------
# The pattern subset (registry §3.4)


class PatternRefused(Exception):
    pass


_SPECIAL = set("\\.^$|?*+()[]{}")
_ESCAPES = set("./\\()[]{}*+?|^$")
_CLASS_ESCAPES = _ESCAPES | {"-"}
_QUANT = re.compile(r"\{(0|[1-9][0-9]{0,3})(,(0|[1-9][0-9]{0,3})?)?\}")


class _PatternParser:
    def __init__(self, text: str) -> None:
        self.p = text
        self.i = 0
        self.n = len(text)

    def refuse(self) -> None:
        raise PatternRefused()

    def parse(self) -> tuple:
        node = self.alternation()
        if self.i != self.n:
            self.refuse()
        return node

    def alternation(self) -> tuple:
        branches = [self.sequence()]
        while self.i < self.n and self.p[self.i] == "|":
            self.i += 1
            branches.append(self.sequence())
        return ("alt", branches)

    def sequence(self) -> list:
        items = []
        while self.i < self.n and self.p[self.i] not in "|)":
            items.append(self.quantified())
        return items

    def quantified(self) -> tuple:
        atom, quantifiable = self.atom()
        if self.i < self.n and self.p[self.i] in "*+?{":
            if not quantifiable:
                self.refuse()
            c = self.p[self.i]
            if c == "{":
                m = _QUANT.match(self.p, self.i)
                if not m:
                    self.refuse()
                lo = int(m.group(1))
                if m.group(2) is None:
                    kind, hi = "exact", lo
                elif m.group(3) is None:
                    kind, hi = "atleast", None
                else:
                    kind, hi = "range", int(m.group(3))
                    if lo > hi:
                        self.refuse()
                if lo > 1000 or (hi is not None and hi > 1000):
                    self.refuse()
                self.i = m.end()
                node = ("quant", atom, kind, lo, hi)
            else:
                self.i += 1
                node = ("quant", atom, c, None, None)
            if self.i < self.n and self.p[self.i] in "*+?{":
                self.refuse()
            return node
        return atom

    def atom(self) -> tuple[tuple, bool]:
        c = self.p[self.i]
        if c == "\\":
            if self.i + 1 >= self.n:
                self.refuse()
            e = self.p[self.i + 1]
            self.i += 2
            if e == "d":
                return ("digit",), True
            if e in _ESCAPES:
                return ("lit", e), True
            self.refuse()
        if c == ".":
            self.i += 1
            return ("any",), True
        if c == "^":
            if self.i != 0:
                self.refuse()
            self.i += 1
            return ("bol",), False
        if c == "$":
            if self.i != self.n - 1:
                self.refuse()
            self.i += 1
            return ("eol",), False
        if c == "(":
            if self.i + 1 < self.n and self.p[self.i + 1] == "?":
                self.refuse()
            self.i += 1
            inner = self.alternation()
            if self.i >= self.n or self.p[self.i] != ")":
                self.refuse()
            self.i += 1
            return ("group", inner), True
        if c == "[":
            return self.bracket(), True
        if c in _SPECIAL:
            self.refuse()
        self.i += 1
        return ("lit", c), True

    def bracket(self) -> tuple:
        self.i += 1
        negated = False
        if self.i < self.n and self.p[self.i] == "^":
            negated = True
            self.i += 1
        raw: list[tuple] = []  # ("ch", c, escaped) | ("digit",) | ("dash",)
        closed = False
        while self.i < self.n:
            c = self.p[self.i]
            if c == "]":
                self.i += 1
                closed = True
                break
            if c == "[":
                self.refuse()
            if c == "\\":
                if self.i + 1 >= self.n:
                    self.refuse()
                e = self.p[self.i + 1]
                self.i += 2
                if e == "d":
                    raw.append(("digit",))
                elif e in _CLASS_ESCAPES:
                    raw.append(("ch", e, True))
                else:
                    self.refuse()
                continue
            for pair in ("--", "&&", "~~", "||"):
                if self.p.startswith(pair, self.i):
                    self.refuse()
            raw.append(("dash",) if c == "-" else ("ch", c, False))
            self.i += 1
        if not closed or not raw:
            self.refuse()
        items: list[tuple] = []
        k = 0
        while k < len(raw):
            item = raw[k]
            if (item[0] == "ch" and k + 2 < len(raw) and raw[k + 1][0] == "dash"):
                end = raw[k + 2]
                if end[0] != "ch":
                    self.refuse()
                if ord(item[1]) > ord(end[1]):
                    self.refuse()
                items.append(("range", item[1], end[1]))
                k += 3
                continue
            if item[0] == "dash":
                # READING: an unescaped `-` that is the class's first or last item is a literal, as
                # ECMAScript (u), RE2 and Python all read it; anywhere else it must make a range.
                if k != 0 and k != len(raw) - 1:
                    self.refuse()
                items.append(("ch", "-"))
            elif item[0] == "digit":
                if k + 1 < len(raw) and raw[k + 1][0] == "dash" and k + 2 < len(raw):
                    self.refuse()
                items.append(("digit",))
            else:
                items.append(("ch", item[1]))
            k += 1
        return ("class", negated, items)


def _quant_count(node: tuple) -> int:
    _, _, kind, lo, hi = node
    if kind in ("*", "+", "?"):
        return 1
    count = hi if kind == "range" else lo
    return 1 if count == 0 else count


def _is_zero_quant(node: tuple) -> bool:
    return node[0] == "quant" and node[2] in ("exact", "range") and node[3] == 0 and (node[4] in (0, None) if node[2] == "exact" else node[4] == 0)


def _inner_quants(node: tuple) -> list[tuple]:
    """The quantifiers directly below `node` (not below another quantifier)."""
    out: list[tuple] = []
    kind = node[0]
    if kind == "alt":
        for seq in node[1]:
            for item in seq:
                out.extend(_inner_quants(item))
    elif kind == "group":
        out.extend(_inner_quants(node[1]))
    elif kind == "quant":
        out.append(node)
    return out


def _chain(node: tuple, memo: dict) -> int:
    key = id(node)
    if key in memo:
        return memo[key]
    below = 1
    for inner in _inner_quants(node[1]):
        below = max(below, 1 if _is_zero_quant(inner) else _chain(inner, memo))
    memo[key] = _quant_count(node) * below
    return memo[key]


def _all_quants(node: tuple) -> list[tuple]:
    out: list[tuple] = []
    kind = node[0]
    if kind == "alt":
        for seq in node[1]:
            for item in seq:
                out.extend(_all_quants(item))
    elif kind == "group":
        out.extend(_all_quants(node[1]))
    elif kind == "quant":
        out.append(node)
        out.extend(_all_quants(node[1]))
    return out


def _size(node: tuple) -> int:
    kind = node[0]
    if kind == "alt":
        total = sum(max(1, sum(_size(i) for i in seq)) for seq in node[1]) + len(node[1]) - 1
        return max(1, total)
    if kind == "group":
        return max(1, _size(node[1]))
    if kind == "quant":
        atom = _size(node[1])
        q, lo, hi = node[2], node[3], node[4]
        if q == "*":
            size = 2 + atom
        elif q in ("+", "?"):
            size = 1 + atom
        elif q == "exact":
            size = lo * atom
        elif q == "atleast":
            size = 2 + atom if lo == 0 else 1 + lo * atom
        else:
            size = hi * atom + (hi - lo)
        return max(1, size)
    return 1


def _class_char(c: str) -> str:
    return re.escape(c) if c not in "-" else "\\-"


def _to_python(node: tuple) -> str:
    kind = node[0]
    if kind == "alt":
        return "|".join("".join(_to_python(i) for i in seq) for seq in node[1])
    if kind == "group":
        return "(?:" + _to_python(node[1]) + ")"
    if kind == "quant":
        inner = _to_python(node[1])
        q, lo, hi = node[2], node[3], node[4]
        if q in ("*", "+", "?"):
            return inner + q
        if q == "exact":
            return inner + "{%d}" % lo
        if q == "atleast":
            return inner + "{%d,}" % lo
        return inner + "{%d,%d}" % (lo, hi)
    if kind == "lit":
        return re.escape(node[1])
    if kind == "digit":
        return "[0-9]"
    if kind == "any":
        return "[^\n\r  ]"
    if kind == "bol":
        return "^"
    if kind == "eol":
        return r"\Z"
    if kind == "class":
        parts = []
        for item in node[2]:
            if item[0] == "ch":
                parts.append(_class_char(item[1]))
            elif item[0] == "range":
                parts.append(_class_char(item[1]) + "-" + _class_char(item[2]))
            else:
                parts.append("0-9")
        return "[" + ("^" if node[1] else "") + "".join(parts) + "]"
    raise AssertionError(kind)


class Pattern:
    def __init__(self, text: str) -> None:
        if len(text) > 256:
            raise PatternRefused()
        tree = _PatternParser(text).parse()
        memo: dict = {}
        for q in _all_quants(tree):
            if _chain(q, memo) > 1000:
                raise PatternRefused()
        self.size = _size(tree)
        self.regex = re.compile(_to_python(tree))

    def search(self, text: str) -> bool:
        return self.regex.search(text) is not None


_PATTERN_CACHE: dict[str, Pattern | None] = {}


def compile_pattern(text: str) -> Pattern | None:
    if text not in _PATTERN_CACHE:
        try:
            _PATTERN_CACHE[text] = Pattern(text)
        except PatternRefused:
            _PATTERN_CACHE[text] = None
    return _PATTERN_CACHE[text]


DEFAULT_ENTRY_ID = "^[a-z][a-z0-9-]{0,62}$"

# ---------------------------------------------------------------------------------------------------
# Pointer patterns (registry §3.5)

STAR = object()


def pointer_pattern(text: Any) -> list | None:
    """The tokens of a pointer pattern (STAR for `*`), or None when it is not one."""
    if not isinstance(text, str) or not text.startswith("/") or len(text.encode("utf-8")) > 512:
        return None
    out: list = []
    for raw in text[1:].split("/"):
        if re.search(r"~(?![012])", raw):
            return None
        if raw == "*":
            out.append(STAR)
        else:
            out.append(raw.replace("~1", "/").replace("~2", "*").replace("~0", "~"))
    return out


def pattern_matches(tokens: list, concrete: list[str]) -> bool:
    return len(tokens) == len(concrete) and all(t is STAR or t == c for t, c in zip(tokens, concrete))


def patterns_overlap(a: list, b: list) -> bool:
    return len(a) == len(b) and all(x is STAR or y is STAR or x == y for x, y in zip(a, b))


def positions(value: Any, tokens: list, at: tuple = ()) -> list[tuple]:
    """Registry §6.1: the positions of `value` that a pointer pattern matches, as token tuples."""
    if not tokens:
        return [at]
    head, rest = tokens[0], tokens[1:]
    out: list[tuple] = []
    if isinstance(value, dict):
        names = list(value) if head is STAR else ([head] if head in value else [])
        for name in names:
            out.extend(positions(value[name], rest, at + (name,)))
    elif isinstance(value, list):
        if head is STAR:
            indices = range(len(value))
        elif re.fullmatch(r"0|[1-9][0-9]*", head) and int(head) < len(value):
            indices = [int(head)]
        else:
            indices = []
        for i in indices:
            out.extend(positions(value[i], rest, at + (str(i),)))
    return out


def _types_of(schema: dict) -> set | None:
    t = schema.get("type", ABSENT)
    if t is ABSENT:
        return None
    return {t} if isinstance(t, str) else set(t)


def reachable(schema: Any, tokens: list, defs: dict, guard: frozenset = frozenset()) -> bool:
    """Registry §3.5's reachability, decided from the schema alone."""
    if schema is True:
        return True
    if schema is False or not isinstance(schema, dict):
        return False
    if not tokens:
        return True
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/$defs/"):
        name = _ref_name(ref)
        if name in defs and name not in guard and reachable(defs[name], tokens, defs, guard | {name}):
            return True
    for key in ("allOf", "anyOf"):
        branches = schema.get(key)
        if isinstance(branches, list) and any(reachable(b, tokens, defs, guard) for b in branches):
            return True
    types = _types_of(schema)
    head, rest = tokens[0], tokens[1:]
    allows_object = types is None or "object" in types
    allows_array = types is None or "array" in types
    if allows_object:
        props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        extra = schema.get("additionalProperties", ABSENT)

        def through_extra() -> bool:
            if extra is ABSENT or extra is True:
                return True
            if extra is False:
                return False
            return reachable(extra, rest, defs, guard)
        if head is STAR:
            if any(reachable(s, rest, defs, guard) for s in props.values()) or through_extra():
                return True
        elif head in props:
            if reachable(props[head], rest, defs, guard):
                return True
        elif through_extra():
            return True
    if allows_array and (head is STAR or INDEX_TOKEN.match(head)):
        items = schema.get("items", ABSENT)
        if items is ABSENT or items is True:
            return True
        if items is not False and reachable(items, rest, defs, guard):
            return True
    return False


def _ref_name(ref: str) -> str | None:
    token = ref[len("#/$defs/"):]
    if token == "" or "/" in token or re.search(r"~(?![01])", token):
        return None
    return token.replace("~1", "/").replace("~0", "~")


# ---------------------------------------------------------------------------------------------------
# Kind declarations (registry §3)

SCHEMA_KEYWORDS = {
    "type", "enum", "const", "properties", "required", "additionalProperties", "minProperties",
    "maxProperties", "propertyNames", "items", "minItems", "maxItems", "uniqueItems", "minLength",
    "maxLength", "pattern", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "anyOf",
    "allOf", "not", "$defs", "$ref", "title", "description", "default", "deprecated", "examples",
}
TYPE_NAMES = {"null", "boolean", "object", "array", "number", "integer", "string"}
KIND_MEMBERS = {"kindFormatVersion", "id", "version", "kind", "owner", "description", "entryId", "schema",
                "secrets", "references", "overlayable", "bounds", "deprecated"}
KIND_REQUIRED = ("id", "version", "kind", "owner", "schema")


def _is_subschema(value: Any) -> bool:
    return isinstance(value, (dict, bool))


class _SchemaReader:
    """Registry §§3.2 and 3.3: a schema's diagnostics in reading order."""

    def __init__(self, schema: Any, base: str) -> None:
        self.schema = schema
        self.base = base
        self.diags: list[tuple[str, str]] = []
        self.count = 0
        self.stopped = False
        self.refs: list[tuple[str, str | None, str | None]] = []  # (pointer, name, the def it sits in)
        self.patterns: list[tuple[str, str]] = []  # (pointer, text) in reading order
        self.defs: dict = {}

    def run(self) -> None:
        s = self.schema
        if not _is_subschema(s):
            self.diags.append(("REG-KIND-FORM", self.base))
            return
        if isinstance(s, dict) and isinstance(s.get("$defs"), dict):
            self.defs = s["$defs"]
        self._count()
        if isinstance(s, dict) and "$defs" in s:
            defs = s["$defs"]
            at = self.base + "/$defs"
            if not isinstance(defs, dict):
                self.diags.append(("REG-KIND-SCHEMA-FORM", at))
            else:
                for name in sorted(defs):
                    if self.stopped:
                        return
                    sub = defs[name]
                    if not _is_subschema(sub):
                        self.diags.append(("REG-KIND-SCHEMA-FORM", at + "/" + escape_token(name)))
                        continue
                    self._count()
                    self._read(sub, at + "/" + escape_token(name), name)
        if self.stopped:
            return
        if isinstance(s, dict):
            self._keywords(s, self.base, None, root=True)

    def _count(self) -> None:
        self.count += 1
        if self.count > 4096 and not self.stopped:
            self.stopped = True
            self.diags.append(("REG-KIND-SCHEMA-LIMIT", self.base))

    def _sub(self, value: Any, at: str, in_def: str | None) -> None:
        if self.stopped:
            return
        if not _is_subschema(value):
            self.diags.append(("REG-KIND-SCHEMA-FORM", at))
            return
        self._count()
        if self.stopped:
            return
        self._read(value, at, in_def)

    def _read(self, s: Any, at: str, in_def: str | None) -> None:
        if isinstance(s, dict):
            self._keywords(s, at, in_def, root=False)

    def _keywords(self, s: dict, at: str, in_def: str | None, root: bool) -> None:
        for key in sorted(s):
            if self.stopped:
                return
            value = s[key]
            here = at + "/" + escape_token(key)
            if key not in SCHEMA_KEYWORDS:
                self.diags.append(("REG-KIND-SCHEMA-KEYWORD", here))
                continue
            if key == "$defs":
                if not root:
                    self.diags.append(("REG-KIND-SCHEMA-FORM", here))
                continue
            if key == "type":
                names = [value] if isinstance(value, str) else value
                ok = (isinstance(value, str) and value in TYPE_NAMES) or (
                    isinstance(value, list) and value and all(isinstance(n, str) and n in TYPE_NAMES for n in value)
                    and len(set(value)) == len(value))
                if not ok:
                    self.diags.append(("REG-KIND-SCHEMA-FORM", here))
                del names
            elif key == "enum":
                if not isinstance(value, list) or not value:
                    self.diags.append(("REG-KIND-SCHEMA-FORM", here))
                elif len(value) > 1024:
                    self.diags.append(("REG-KIND-SCHEMA-LIMIT", here))
            elif key in ("const", "default"):
                pass
            elif key == "properties":
                if not isinstance(value, dict):
                    self.diags.append(("REG-KIND-SCHEMA-FORM", here))
                else:
                    for name in sorted(value):
                        self._sub(value[name], here + "/" + escape_token(name), in_def)
            elif key == "required":
                if not (isinstance(value, list) and all(isinstance(v, str) for v in value)
                        and len(set(value)) == len(value)):
                    self.diags.append(("REG-KIND-SCHEMA-FORM", here))
            elif key in ("additionalProperties", "items", "not"):
                if key == "items" and isinstance(value, list):
                    self.diags.append(("REG-KIND-SCHEMA-FORM", here))
                else:
                    self._sub(value, here, in_def)
            elif key in ("minProperties", "maxProperties", "minItems", "maxItems", "minLength", "maxLength"):
                if not is_count(value):
                    self.diags.append(("REG-KIND-SCHEMA-FORM", here))
            elif key == "propertyNames":
                self._count()
                if self.stopped:
                    return
                if not isinstance(value, dict):
                    self.diags.append(("REG-KIND-SCHEMA-FORM", here))
                    continue
                for inner in sorted(value):
                    inner_at = here + "/" + escape_token(inner)
                    if inner == "pattern":
                        self._pattern(value[inner], inner_at)
                    elif inner == "maxLength":
                        if not is_count(value[inner]):
                            self.diags.append(("REG-KIND-SCHEMA-FORM", inner_at))
                    else:
                        self.diags.append(("REG-KIND-SCHEMA-KEYWORD", inner_at))
            elif key == "uniqueItems" or key == "deprecated":
                if not isinstance(value, bool):
                    self.diags.append(("REG-KIND-SCHEMA-FORM", here))
            elif key == "pattern":
                self._pattern(value, here)
            elif key in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
                if not is_number(value):
                    self.diags.append(("REG-KIND-SCHEMA-FORM", here))
            elif key in ("anyOf", "allOf"):
                if not isinstance(value, list) or not value:
                    self.diags.append(("REG-KIND-SCHEMA-FORM", here))
                elif len(value) > 16:
                    self.diags.append(("REG-KIND-SCHEMA-LIMIT", here))
                else:
                    for i, branch in enumerate(value):
                        self._sub(branch, here + "/" + str(i), in_def)
            elif key == "$ref":
                name = _ref_name(value) if isinstance(value, str) and value.startswith("#/$defs/") else None
                if name is None:
                    self.diags.append(("REG-KIND-SCHEMA-REF", here))
                    self.refs.append((here, None, in_def))
                elif name not in self.defs:
                    self.diags.append(("REG-KIND-SCHEMA-REF", here))
                    self.refs.append((here, None, in_def))
                else:
                    self.refs.append((here, name, in_def))
            elif key in ("title", "description"):
                if not isinstance(value, str):
                    self.diags.append(("REG-KIND-SCHEMA-FORM", here))
            elif key == "examples":
                if not isinstance(value, list):
                    self.diags.append(("REG-KIND-SCHEMA-FORM", here))

    def _pattern(self, value: Any, at: str) -> None:
        if not isinstance(value, str):
            self.diags.append(("REG-KIND-PATTERN", at))
            return
        if compile_pattern(value) is None:
            self.diags.append(("REG-KIND-PATTERN", at))
            return
        self.patterns.append((at, value))

    def cycle_diagnostic(self) -> str | None:
        edges: dict[str, set[str]] = {name: set() for name in self.defs}
        for _, name, in_def in self.refs:
            if name is not None and in_def is not None and in_def in edges:
                edges[in_def].add(name)

        def reaches(start: str) -> set[str]:
            seen: set[str] = set()
            todo = list(edges.get(start, ()))
            while todo:
                n = todo.pop()
                if n not in seen:
                    seen.add(n)
                    todo.extend(edges.get(n, ()))
            return seen
        reach = {name: reaches(name) for name in edges}
        on_cycle = {name for name in edges if name in reach[name]}
        leads = {name for name in edges if name in on_cycle or reach[name] & on_cycle}
        for at, _, in_def in self.refs:
            if in_def is not None and in_def in leads:
                return at
        return None

    def expanded_size(self) -> int:
        memo: dict[str, int] = {}

        def size(node: Any) -> int:
            if not isinstance(node, dict):
                return 1
            total = 1
            for key in sorted(node):
                value = node[key]
                if key == "properties" and isinstance(value, dict):
                    total += sum(size(v) for v in value.values())
                elif key in ("additionalProperties", "items", "not"):
                    total += size(value)
                elif key in ("anyOf", "allOf") and isinstance(value, list):
                    total += sum(size(v) for v in value)
                elif key == "propertyNames":
                    total += 1
                elif key == "$ref" and isinstance(value, str):
                    name = _ref_name(value) if value.startswith("#/$defs/") else None
                    if name in self.defs:
                        if name not in memo:
                            memo[name] = 4097
                            memo[name] = min(size(self.defs[name]), 4097)
                        total += memo[name]
                if total > 4096:
                    return 4097
            return total
        root = dict(self.schema) if isinstance(self.schema, dict) else self.schema
        if isinstance(root, dict):
            root.pop("$defs", None)
        return size(root)


class Kind:
    """A supplied kind declaration, admitted and read (registry §7.1 steps 1 and 2)."""

    def __init__(self, data: bytes, source: str | None = None) -> None:
        self.data = data
        self.source = source
        self.kind_document = sha256_digest(data)
        self.value, refusals = admit(data, 256 * KIB, "kindFormatVersion", ("1.0.0",))
        self.admitted = self.value is not None
        self.diags: list[dict] = []
        self.kind: str | None = None
        self.usable = False
        self.digest: str | None = None
        self.schema: Any = None
        self.defs: dict = {}
        self.entry_pattern: Pattern | None = None
        self.secrets: list[list] = []
        self.references: list[tuple[list, list[str]]] = []
        self.overlayable: list[list] = []
        self.max_entries = 10000
        self.max_entry_bytes = 65536
        self.deprecated = False
        if not self.admitted:
            for code, at in refusals:
                kd = None if code == "REG-DOC-SIZE" else self.kind_document
                self.diags.append(diag(code, "kind", at, source=source, kindDocument=kd))
            return
        self.digest = digest_of(self.value)
        self._read()
        self.usable = not self.diags

    def _d(self, code: str, at: str) -> None:
        self.diags.append(diag(code, "kind", at, source=self.source, kindDocument=self.kind_document,
                               kind=self.kind))

    def _read(self) -> None:
        v = self.value
        if matches(KIND_NAME, v.get("kind")):
            self.kind = v["kind"]
        for name in v:
            if name not in KIND_MEMBERS:
                self._d("REG-KIND-UNKNOWN-MEMBER", pointer(name))
        for name in KIND_REQUIRED:
            if name not in v:
                self._d("REG-KIND-MISSING-MEMBER", pointer(name))
        if "id" in v and not absolute_uri(v["id"]):
            self._d("REG-KIND-FORM", "/id")
        if "version" in v and not matches(SEMVER, v["version"]):
            self._d("REG-KIND-FORM", "/version")
        if "kind" in v and self.kind is None:
            self._d("REG-KIND-FORM", "/kind")
        if "owner" in v and not matches(OWNER, v["owner"]):
            self._d("REG-KIND-FORM", "/owner")
        if "description" in v and not isinstance(v["description"], str):
            self._d("REG-KIND-FORM", "/description")
        if "deprecated" in v:
            if not isinstance(v["deprecated"], bool):
                self._d("REG-KIND-FORM", "/deprecated")
            else:
                self.deprecated = v["deprecated"]
        pattern_texts: list[tuple[str, str]] = []
        entry_text = DEFAULT_ENTRY_ID
        if "entryId" in v:
            e = v["entryId"]
            if not isinstance(e, dict) or set(e) != {"pattern"}:
                self._d("REG-KIND-FORM", "/entryId")
            elif not isinstance(e["pattern"], str) or compile_pattern(e["pattern"]) is None:
                self._d("REG-KIND-PATTERN", "/entryId/pattern")
            else:
                entry_text = e["pattern"]
                pattern_texts.append(("/entryId/pattern", entry_text))
        self.entry_pattern = compile_pattern(entry_text)
        schema_ok = False
        if "schema" in v:
            reader = _SchemaReader(v["schema"], "/schema")
            reader.run()
            for code, at in reader.diags:
                self._d(code, at)
            cycle = reader.cycle_diagnostic()
            if cycle is not None:
                self._d("REG-KIND-SCHEMA-REF", cycle)
            if not reader.diags and cycle is None:
                if reader.expanded_size() > 4096:
                    self._d("REG-KIND-SCHEMA-LIMIT", "/schema")
                else:
                    schema_ok = True
            pattern_texts.extend(reader.patterns)
            self.schema = v["schema"]
            self.defs = reader.defs
        total = 0
        for at, text in pattern_texts:
            size = compile_pattern(text).size
            if size > 4096 or total + size > 65536:
                self._d("REG-KIND-PATTERN-LIMIT", at)
                continue
            total += size
        for member in ("secrets", "overlayable"):
            if member not in v:
                continue
            items = v[member]
            if not isinstance(items, list):
                self._d("REG-KIND-FORM", pointer(member))
                continue
            seen: list = []
            parsed: list = []
            for i, item in enumerate(items):
                at = pointer(member, i)
                if not isinstance(item, str) or item in seen:
                    self._d("REG-KIND-FORM", at)
                    seen.append(item)
                    continue
                seen.append(item)
                tokens = pointer_pattern(item)
                if tokens is None:
                    self._d("REG-KIND-POINTER-FORM", at)
                    continue
                parsed.append((at, tokens))
            if member == "secrets":
                self.secrets = parsed
            else:
                self.overlayable = parsed
        if "references" in v:
            refs = v["references"]
            if not isinstance(refs, list):
                self._d("REG-KIND-FORM", "/references")
            else:
                for i, item in enumerate(refs):
                    at = pointer("references", i)
                    if (not isinstance(item, dict) or not isinstance(item.get("pointer"), str)
                            or not isinstance(item.get("kinds"), list) or not item["kinds"]):
                        self._d("REG-KIND-FORM", at)
                        continue
                    bad = False
                    for name in item:
                        if name not in ("pointer", "kinds"):
                            self._d("REG-KIND-UNKNOWN-MEMBER", at + "/" + escape_token(name))
                            bad = True
                    kinds = item["kinds"]
                    if not all(matches(KIND_NAME, k) for k in kinds) or len(set(map(str, kinds))) != len(kinds):
                        self._d("REG-KIND-FORM", at + "/kinds")
                        bad = True
                    tokens = pointer_pattern(item["pointer"])
                    if tokens is None:
                        self._d("REG-KIND-POINTER-FORM", at + "/pointer")
                        continue
                    if not bad:
                        self.references.append((at + "/pointer", tokens, list(kinds)))
        if "bounds" in v:
            b = v["bounds"]
            if not isinstance(b, dict):
                self._d("REG-KIND-FORM", "/bounds")
            else:
                for name in b:
                    if name not in ("maxEntries", "maxEntryBytes"):
                        self._d("REG-KIND-UNKNOWN-MEMBER", pointer("bounds", name))
                if "maxEntries" in b:
                    if is_integer_value(b["maxEntries"]) and 1 <= b["maxEntries"] <= MAX_SAFE:
                        self.max_entries = int(b["maxEntries"])
                    else:
                        self._d("REG-KIND-FORM", "/bounds/maxEntries")
                if "maxEntryBytes" in b:
                    if is_integer_value(b["maxEntryBytes"]) and 1 <= b["maxEntryBytes"] <= 8 * MIB:
                        self.max_entry_bytes = int(b["maxEntryBytes"])
                    else:
                        self._d("REG-KIND-FORM", "/bounds/maxEntryBytes")
        if schema_ok:
            for at, tokens in self.secrets + self.overlayable:
                if not reachable(self.schema, tokens, self.defs):
                    self._d("REG-KIND-POINTER-UNREACHABLE", at)
            for at, tokens, _ in self.references:
                if not reachable(self.schema, tokens, self.defs):
                    self._d("REG-KIND-POINTER-UNREACHABLE", at)
        for at, tokens in self.secrets:
            if any(patterns_overlap(tokens, r[1]) for r in self.references):
                self._d("REG-KIND-POINTER-CONFLICT", at)
        self.secrets = [t for _, t in self.secrets]
        self.overlayable = [t for _, t in self.overlayable]
        self.references = [(t, k) for _, t, k in self.references]

    def kind_member(self) -> Any:
        return self.value.get("kind") if self.value else None


# ---------------------------------------------------------------------------------------------------
# Value validation (registry §7.2)


def _type_holds(value: Any, name: str) -> bool:
    if name == "null":
        return value is None
    if name == "boolean":
        return isinstance(value, bool)
    if name == "object":
        return isinstance(value, dict)
    if name == "array":
        return isinstance(value, list)
    if name == "number":
        return is_number(value)
    if name == "integer":
        return is_integer_value(value)
    if name == "string":
        return isinstance(value, str)
    return False


def _resolve_ref(schema: dict, defs: dict) -> Any:
    name = _ref_name(schema["$ref"])
    return defs.get(name, True)


def validate_value(value: Any, schema: Any, defs: dict, at: tuple = ()) -> list[tuple[str, tuple]]:
    """Registry §7.2: (code, position) for every failure, each keyword checked on its own."""
    if schema is True:
        return []
    if schema is False:
        return [("REG-VALUE-TYPE", at)]
    out: list[tuple[str, tuple]] = []
    for key in sorted(schema):
        kw = schema[key]
        if key == "type":
            names = [kw] if isinstance(kw, str) else kw
            if not any(_type_holds(value, n) for n in names):
                out.append(("REG-VALUE-TYPE", at))
        elif key == "enum":
            if not any(json_equal(value, e) for e in kw):
                out.append(("REG-VALUE-ENUM", at))
        elif key == "const":
            if not json_equal(value, kw):
                out.append(("REG-VALUE-CONST", at))
        elif key == "required" and isinstance(value, dict):
            for name in kw:
                if name not in value:
                    out.append(("REG-VALUE-REQUIRED", at + (name,)))
        elif key in ("minProperties", "maxProperties") and isinstance(value, dict):
            if (key == "minProperties" and len(value) < kw) or (key == "maxProperties" and len(value) > kw):
                out.append(("REG-VALUE-PROPERTY-COUNT", at))
        elif key == "propertyNames" and isinstance(value, dict):
            for name in value:
                bad = False
                if "maxLength" in kw and len(name) > kw["maxLength"]:
                    bad = True
                if "pattern" in kw and not compile_pattern(kw["pattern"]).search(name):
                    bad = True
                if bad:
                    out.append(("REG-VALUE-PROPERTY-NAME", at + (name,)))
        elif key == "additionalProperties" and isinstance(value, dict):
            props = schema.get("properties", {})
            for name in value:
                if name in props:
                    continue
                if kw is False:
                    out.append(("REG-VALUE-ADDITIONAL", at + (name,)))
                else:
                    out.extend(validate_value(value[name], kw, defs, at + (name,)))
        elif key == "properties" and isinstance(value, dict):
            for name in sorted(kw):
                if name in value:
                    out.extend(validate_value(value[name], kw[name], defs, at + (name,)))
        elif key == "items" and isinstance(value, list):
            for i, item in enumerate(value):
                out.extend(validate_value(item, kw, defs, at + (str(i),)))
        elif key in ("minItems", "maxItems") and isinstance(value, list):
            if (key == "minItems" and len(value) < kw) or (key == "maxItems" and len(value) > kw):
                out.append(("REG-VALUE-ITEM-COUNT", at))
        elif key == "uniqueItems" and isinstance(value, list) and kw is True:
            if any(json_equal(value[i], value[j]) for i in range(len(value)) for j in range(i + 1, len(value))):
                out.append(("REG-VALUE-UNIQUE", at))
        elif key in ("minLength", "maxLength") and isinstance(value, str):
            if (key == "minLength" and len(value) < kw) or (key == "maxLength" and len(value) > kw):
                out.append(("REG-VALUE-LENGTH", at))
        elif key == "pattern" and isinstance(value, str):
            if not compile_pattern(kw).search(value):
                out.append(("REG-VALUE-PATTERN", at))
        elif key in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum") and is_number(value):
            fails = ((key == "minimum" and value < kw) or (key == "maximum" and value > kw)
                     or (key == "exclusiveMinimum" and value <= kw) or (key == "exclusiveMaximum" and value >= kw))
            if fails:
                out.append(("REG-VALUE-RANGE", at))
        elif key == "allOf":
            for branch in kw:
                out.extend(validate_value(value, branch, defs, at))
        elif key == "anyOf":
            held = None
            for branch in kw:
                result = validate_value(value, branch, defs, at)
                if not any(severity(c) == "error" for c, _ in result):
                    held = result
                    break
            if held is None:
                out.append(("REG-VALUE-ANY-OF", at))
            else:
                out.extend(held)
        elif key == "not":
            inner = validate_value(value, kw, defs, at)
            if not any(severity(c) == "error" for c, _ in inner):
                out.append(("REG-VALUE-NOT", at))
        elif key == "$ref":
            out.extend(validate_value(value, _resolve_ref(schema, defs), defs, at))
        elif key == "deprecated" and kw is True:
            out.append(("REG-VALUE-DEPRECATED", at))
    return out


def _expand(schema: Any, defs: dict, guard: frozenset = frozenset()) -> list[dict]:
    """The subschemas that apply at one position: the schema and those its $ref, allOf and anyOf reach."""
    if not isinstance(schema, dict):
        return []
    out = [schema]
    ref = schema.get("$ref")
    if isinstance(ref, str):
        name = _ref_name(ref) if ref.startswith("#/$defs/") else None
        if name in defs and name not in guard:
            out.extend(_expand(defs[name], defs, guard | {name}))
    for key in ("allOf", "anyOf"):
        if isinstance(schema.get(key), list):
            for branch in schema[key]:
                out.extend(_expand(branch, defs, guard))
    return out


def _schemas_at(schema: Any, defs: dict, value: Any, tokens: list[str]) -> list[dict]:
    nodes = _expand(schema, defs)
    for token in tokens:
        nxt: list = []
        for node in nodes:
            if isinstance(value, dict):
                props = node.get("properties") if isinstance(node.get("properties"), dict) else {}
                if token in props:
                    nxt.extend(_expand(props[token], defs))
                elif isinstance(node.get("additionalProperties"), dict):
                    nxt.extend(_expand(node["additionalProperties"], defs))
            elif isinstance(value, list) and isinstance(node.get("items"), dict):
                nxt.extend(_expand(node["items"], defs))
        nodes = nxt
        value = lookup(value, [token])
    return nodes


# ---------------------------------------------------------------------------------------------------
# References (registry §§6.2 to 6.4)

ENTRY_REF = re.compile(r"entry:([a-z][a-z0-9-]{0,62})/([\x21-\x22\x24-\x2e\x30-\x7e]{1,128})(?:#(.*))?\Z", re.S)


def parse_entry_ref(value: Any) -> tuple[str, str, list[str] | None] | None:
    if not isinstance(value, str):
        return None
    m = ENTRY_REF.match(value)
    if not m:
        return None
    if m.group(3) is None:
        return m.group(1), m.group(2), None
    text = m.group(3)
    if len(text) > 512:
        return None
    tokens = split_pointer(text)
    if tokens is None:
        return None
    return m.group(1), m.group(2), tokens


def secret_ref(value: Any) -> tuple[str | None, str | None]:
    """Registry §6.3: (code, None) for a refused value, or (None, project) for a secret reference."""
    if not isinstance(value, str) or not value.startswith("secret:"):
        return "REF-SECRET-FORM", None
    rest = value[len("secret:"):]
    if ":" not in rest:
        return "REF-SECRET-FORM", None
    store, locator = rest.split(":", 1)
    if store != "gcp-sm":
        return "REF-SECRET-STORE", None
    segments = locator.split("/")
    if len(segments) != 6 or segments[0] != "projects" or segments[2] != "secrets" or segments[4] != "versions":
        return "REF-SECRET-FORM", None
    project, name, version = segments[1], segments[3], segments[5]
    if SECRET_NAME.match(name) and version != "" and (
            not re.fullmatch(r"[0-9]+", version) or re.fullmatch(r"[0-9]+", project)):
        return "REF-SECRET-PIN", None
    if not (PROJECT.match(project) and SECRET_NAME.match(name) and SECRET_VERSION.match(version)):
        return "REF-SECRET-FORM", None
    return None, project


# ---------------------------------------------------------------------------------------------------
# Validation of a registry (registry §7.1) and resolution (registry §8)

REGISTRY_MEMBERS = ("registryFormatVersion", "id", "version", "environments", "owners", "kinds", "entries",
                    "overlays", "secretScopes")
REGISTRY_REQUIRED = ("id", "version", "environments", "owners", "kinds", "entries")
ENTRY_MEMBERS = ("kind", "id", "owner", "value", "environments")


def entry_name(entry: Any) -> dict | None:
    if isinstance(entry, dict) and matches(KIND_NAME, entry.get("kind")) and matches(ENTRY_ID, entry.get("id")):
        return {"kind": entry["kind"], "id": entry["id"]}
    return None


class Validation:
    """One registry, validated with the declarations supplied beside it (registry §7.1).

    `source` names the source a diagnostic is about (§2.1), or None; `locate`, when given, maps a
    registry location (pointer, entry index, pin index, overlay and patch index) to a source and a
    pointer into that source's registry, as the assembled registry needs (§4, step 6)."""

    def __init__(self, registry: bytes | dict, kinds: list[Kind], source: str | None = None,
                 locate: Any = None, defer: Any = None) -> None:
        self.source = source
        self.locate = locate
        self.defer = defer
        self.diags: list[dict] = []
        self.digest: str | None = None
        self.value: dict | None = None
        self.passed_shape = False
        self.kinds = kinds
        self.environments: list[str] = []
        self.checked: dict[str, dict[int, Any]] = {}
        self.pins: dict[str, Kind] = {}
        self.unusable_pins: set[str] = set()
        self.entries: list[tuple[int, dict]] = []
        self.passed: set[int] = set()
        self.patches: dict[str, dict[int, dict]] = {}
        self.failed: dict[str, set[int]] = {}
        self.ref_results: list[tuple[str, int, tuple, str, str, str]] = []
        self._run(registry)

    # Locations -------------------------------------------------------------------------------------

    def _reg(self, code: str, at: str, entry: Any = None, kind: Any = None, environment: Any = None,
             entry_index: int | None = None, pin_index: int | None = None, overlay: tuple | None = None) -> None:
        source, where = self.source, at
        if self.locate is not None:
            source, where = self.locate(at, entry_index, pin_index, overlay)
        self.diags.append(diag(code, "registry", where, source=source, entry=entry, kind=kind,
                               environment=environment))

    def _val(self, code: str, entry_index: int, environment: str, at: tuple) -> None:
        source = self.source
        if self.locate is not None:
            source, _ = self.locate("", entry_index, None, None)
        self.diags.append(diag(code, "value", pointer(*at), source=source,
                               entry=entry_name(self.value["entries"][entry_index]), environment=environment))

    # The steps -------------------------------------------------------------------------------------

    def _run(self, registry: bytes | dict) -> None:
        if isinstance(registry, dict):
            value, refusals = registry, []
        else:
            value, refusals = admit(registry, 8 * MIB, "registryFormatVersion", ("1.0.0",))
        # Step 1: admission; a refused declaration is no declaration later. Equal ones are one.
        by_bytes: dict[bytes, Kind] = {}
        for k in self.kinds:
            if not k.admitted:
                self.diags.extend(k.diags)
                continue
            key = jcs_bytes(k.value)
            if key not in by_bytes or k.kind_document < by_bytes[key].kind_document:
                by_bytes[key] = k
        declarations = list(by_bytes.values())
        # Step 2: kind declarations.
        for k in declarations:
            self.diags.extend(k.diags)
        self.declarations = declarations
        if refusals:
            for code, at in refusals:
                self.diags.append(diag(code, "registry", at, source=self.source))
            return
        self.value = value
        if not self._shape(value):
            return
        self.passed_shape = True
        self.digest = digest_of(value)
        self._pins(value)
        self._entries(value)
        self._overlays(value)
        self._per_environment(value)
        self._bounds(value)

    def _shape(self, v: dict) -> bool:
        stop = False
        for name in v:
            if name not in REGISTRY_MEMBERS:
                self._reg("REG-REGISTRY-UNKNOWN-MEMBER", pointer(name))
                stop = True
        for name in REGISTRY_REQUIRED:
            if name not in v:
                self._reg("REG-REGISTRY-MISSING-MEMBER", pointer(name))
                stop = True
        if stop:
            return False
        if not absolute_uri(v["id"]):
            self._reg("REG-REGISTRY-FORM", "/id")
            stop = True
        if not matches(SEMVER, v["version"]):
            self._reg("REG-REGISTRY-FORM", "/version")
            stop = True
        if not isinstance(v["entries"], list):
            self._reg("REG-REGISTRY-FORM", "/entries")
            stop = True
        if "overlays" in v and not isinstance(v["overlays"], list):
            self._reg("REG-REGISTRY-FORM", "/overlays")
            stop = True
        for member, rx in (("environments", ENVIRONMENT), ("owners", OWNER)):
            items = v[member]
            if not isinstance(items, list) or not items or (member == "environments" and len(items) > 32):
                self._reg("REG-REGISTRY-FORM", pointer(member))
                stop = True
                continue
            seen: list = []
            for i, item in enumerate(items):
                if not matches(rx, item):
                    self._reg("REG-REGISTRY-FORM", pointer(member, i))
                    stop = True
                elif item in seen:
                    self._reg("REG-REGISTRY-DUPLICATE", pointer(member, i))
                    stop = True
                seen.append(item)
        kinds = v["kinds"]
        if not isinstance(kinds, list):
            self._reg("REG-REGISTRY-FORM", "/kinds")
            stop = True
        else:
            for i, pin in enumerate(kinds):
                at = pointer("kinds", i)
                if not isinstance(pin, dict):
                    self._reg("REG-REGISTRY-FORM", at, pin_index=i)
                    stop = True
                    continue
                unknown = [n for n in pin if n not in ("kind", "id", "version", "digest")]
                for name in unknown:
                    self._reg("REG-REGISTRY-UNKNOWN-MEMBER", at + "/" + escape_token(name), pin_index=i)
                    stop = True
                if not (matches(KIND_NAME, pin.get("kind")) and absolute_uri(pin.get("id"))
                        and matches(SEMVER, pin.get("version")) and matches(DIGEST, pin.get("digest"))):
                    self._reg("REG-REGISTRY-FORM", at, pin_index=i)
                    stop = True
        if stop:
            return False
        self.environments = list(v["environments"])
        if "secretScopes" in v and not self._scopes(v):
            return False
        # Entries: a malformed one is dropped, and validation goes on. READING (as the 1.0.0 rows
        # read it): step 3's diagnostics are about the document's shape and carry no `entry` or `kind`.
        for i, entry in enumerate(v["entries"]):
            at = pointer("entries", i)
            if not isinstance(entry, dict):
                self._reg("REG-REGISTRY-FORM", at, entry_index=i)
                continue
            name = entry_name(entry)
            dropped = False
            for member in entry:
                if member not in ENTRY_MEMBERS:
                    self._reg("REG-REGISTRY-UNKNOWN-MEMBER", at + "/" + escape_token(member), entry_index=i)
                    dropped = True
            for member in ("kind", "id", "owner", "value"):
                if member not in entry:
                    self._reg("REG-REGISTRY-MISSING-MEMBER", at + "/" + member, entry_index=i)
                    dropped = True
            if not dropped:
                if not matches(KIND_NAME, entry["kind"]):
                    self._reg("REG-REGISTRY-FORM", at + "/kind", entry_index=i)
                    dropped = True
                if not matches(OWNER, entry["owner"]):
                    self._reg("REG-REGISTRY-FORM", at + "/owner", entry_index=i)
                    dropped = True
                if not isinstance(entry["id"], str):
                    self._reg("REG-REGISTRY-FORM", at + "/id", entry_index=i)
                    dropped = True
                if "environments" in entry:
                    envs = entry["environments"]
                    if not isinstance(envs, list) or not envs:
                        self._reg("REG-REGISTRY-FORM", at + "/environments", entry_index=i)
                        dropped = True
                    else:
                        seen = []
                        for j, item in enumerate(envs):
                            if not isinstance(item, str) or item in seen:
                                self._reg("REG-REGISTRY-FORM", at + "/environments/" + str(j),
                                          entry_index=i)
                                dropped = True
                            seen.append(item)
            if not dropped:
                self.entries.append((i, entry))
        for i in range(1, len(kinds)):
            if kinds[i]["kind"] < kinds[i - 1]["kind"]:
                self._reg("REG-REGISTRY-ORDER", pointer("kinds", i), pin_index=i)
                break
        for k in range(1, len(self.entries)):
            (i, a), (_, b) = self.entries[k], self.entries[k - 1]
            if (a["kind"], a["id"]) < (b["kind"], b["id"]):
                self._reg("REG-REGISTRY-ORDER", pointer("entries", i), entry_index=i)
                break
        return True

    def _scopes(self, v: dict) -> bool:
        scopes = v["secretScopes"]
        bad = False
        if not isinstance(scopes, dict):
            self._reg("REF-SECRET-SCOPE-FORM", "/secretScopes")
            return False
        if any(env not in scopes for env in self.environments):
            self._reg("REF-SECRET-SCOPE-FORM", "/secretScopes")
            bad = True
        for env, stores in scopes.items():
            at = pointer("secretScopes", env)
            if env not in self.environments or not isinstance(stores, dict):
                self._reg("REF-SECRET-SCOPE-FORM", at)
                bad = True
                continue
            for store, projects in stores.items():
                sat = at + "/" + escape_token(store)
                if store != "gcp-sm" or not isinstance(projects, list):
                    self._reg("REF-SECRET-SCOPE-FORM", sat)
                    bad = True
                    continue
                seen: list = []
                for i, p in enumerate(projects):
                    if not matches(PROJECT, p) or p in seen:
                        self._reg("REF-SECRET-SCOPE-FORM", sat + "/" + str(i))
                        bad = True
                    seen.append(p)
        if bad:
            return False
        listed: dict[str, set[str]] = {}
        for env in sorted(scopes):
            for store in scopes[env]:
                for i, p in enumerate(scopes[env][store]):
                    # §6.4: shared when listed for an environment read earlier, whichever listing that was.
                    if listed.get(p, set()) - {env}:
                        self._reg("REF-SECRET-SCOPE-SHARED", pointer("secretScopes", env, store, i))
                    listed.setdefault(p, set()).add(env)
        return True

    def _pins(self, v: dict) -> None:
        by_digest = {k.digest: k for k in self.declarations}
        seen: set[str] = set()
        self.pin_index: dict[str, int] = {}
        pinned_digests: set[str] = set()
        for i, pin in enumerate(v["kinds"]):
            at = pointer("kinds", i)
            name = pin["kind"]
            if name in seen:
                self._reg("REG-REGISTRY-DUPLICATE", at, kind=name, pin_index=i)
                continue
            seen.add(name)
            self.pin_index[name] = i
            k = by_digest.get(pin["digest"])
            if k is None:
                self._reg("REG-PIN-MISSING", at, kind=name, pin_index=i)
                self.unusable_pins.add(name)
                continue
            pinned_digests.add(k.digest)
            if not k.usable:
                self.unusable_pins.add(name)
                continue
            kv = k.value
            if kv.get("kind") != name or kv.get("id") != pin["id"] or kv.get("version") != pin["version"]:
                self._reg("REG-PIN-MISMATCH", at, kind=name, pin_index=i)
                self.unusable_pins.add(name)
                continue
            if k.deprecated:
                self._reg("REG-KIND-DEPRECATED", at, kind=name, pin_index=i)
            self.pins[name] = k
        for k in self.declarations:
            if k.usable and k.digest not in pinned_digests:
                self.diags.append(diag("REG-PIN-UNPINNED", "kind", "", source=k.source,
                                       kindDocument=k.kind_document, kind=k.kind))

    def applies(self, entry: dict, environment: str) -> bool:
        return "environments" not in entry or environment in entry["environments"]

    def _entries(self, v: dict) -> None:
        pinned_names = {pin["kind"] for pin in v["kinds"]}
        seen: set[tuple[str, str]] = set()
        for i, entry in self.entries:
            at = pointer("entries", i)
            name = entry_name(entry)
            if entry["kind"] not in pinned_names:
                self._reg("REG-ENTRY-KIND", at + "/kind", entry=name, entry_index=i)
                continue
            k = self.pins.get(entry["kind"])
            if k is None:
                continue
            ok = True
            if not (ENTRY_ID.match(entry["id"]) and k.entry_pattern.search(entry["id"])):
                self._reg("REG-ENTRY-ID", at + "/id", entry_index=i)
                ok = False
            key = (entry["kind"], entry["id"])
            if key in seen:
                self._reg("REG-ENTRY-DUPLICATE", at + "/id", entry=name, entry_index=i)
                ok = False
            seen.add(key)
            if entry["owner"] not in v["owners"]:
                self._reg("REG-ENTRY-OWNER", at + "/owner", entry=name, entry_index=i)
                ok = False
            for j, env in enumerate(entry.get("environments", [])):
                if env not in self.environments:
                    self._reg("REG-ENTRY-ENVIRONMENT", at + "/environments/" + str(j), entry=name, entry_index=i)
                    ok = False
            if ok:
                self.passed.add(i)

    def _overlays(self, v: dict) -> None:
        for env in self.environments:
            self.patches[env] = {}
            self.failed[env] = set()
        if "overlays" not in v:
            return
        by_key = {(e["kind"], e["id"]): (i, e) for i, e in reversed(self.entries)}
        seen_envs: set[str] = set()
        for o, overlay in enumerate(v["overlays"]):
            at = pointer("overlays", o)
            if (not isinstance(overlay, dict) or set(overlay) != {"environment", "patches"}
                    or not isinstance(overlay["environment"], str) or not isinstance(overlay["patches"], list)):
                self._reg("REG-REGISTRY-FORM", at, overlay=(o, None))
                continue
            env = overlay["environment"]
            if env not in self.environments:
                self._reg("REG-OVERLAY-ENVIRONMENT", at + "/environment", overlay=(o, None))
                continue
            if env in seen_envs:
                self._reg("REG-OVERLAY-DUPLICATE", at + "/environment", overlay=(o, None))
                continue
            seen_envs.add(env)
            named: dict[tuple, int] = {}
            for p, patch in enumerate(overlay["patches"]):
                pat = at + "/patches/" + str(p)
                if (not isinstance(patch, dict) or set(patch) != {"kind", "id", "set"}
                        or not isinstance(patch["kind"], str) or not isinstance(patch["id"], str)
                        or not isinstance(patch["set"], dict)):
                    self._reg("REG-REGISTRY-FORM", pat, environment=None, overlay=(o, p))
                    continue
                name = entry_name(patch)
                key = (patch["kind"], patch["id"])
                if key in named:
                    self._reg("REG-OVERLAY-PATCH-DUPLICATE", pat, entry=name, overlay=(o, p))
                    if key in by_key:
                        self.failed[env].add(by_key[key][0])
                    continue
                if key not in by_key:
                    self._reg("REG-OVERLAY-ENTRY-MISSING", pat, entry=name, overlay=(o, p))
                    named[key] = p
                    continue
                i, entry = by_key[key]
                named[key] = p
                if i not in self.passed:
                    continue
                if not self.applies(entry, env):
                    self._reg("REG-OVERLAY-ENTRY-ABSENT", pat, entry=name, overlay=(o, p))
                    self.failed[env].add(i)
                    continue
                if not self._patch(patch, pat, name, entry, (o, p)):
                    self.failed[env].add(i)
                else:
                    self.patches[env][i] = patch["set"]

    def _patch(self, patch: dict, at: str, name: Any, entry: dict, overlay: tuple) -> bool:
        k = self.pins[entry["kind"]]
        ok = True
        read: list[list[str]] = []
        for key in sorted(patch["set"]):
            tokens = split_pointer(key)
            if tokens is None:
                self._reg("REG-OVERLAY-POINTER", at + "/set", entry=name, overlay=overlay)
                ok = False
                continue
            if not any(pattern_matches(t, tokens) for t in k.overlayable):
                self._reg("REG-OVERLAY-NOT-OVERLAYABLE", at + "/set", entry=name, overlay=overlay)
                ok = False
                continue
            kat = at + "/set/" + escape_token(key)
            if not self._target(entry["value"], tokens, k):
                self._reg("REG-OVERLAY-TARGET", kat, entry=name, overlay=overlay)
                ok = False
                continue
            if patch["set"][key] is None:
                self._reg("REG-OVERLAY-NULL", kat, entry=name, overlay=overlay)
                ok = False
                continue
            if any(_prefix(r, tokens) or _prefix(tokens, r) for r in read):
                self._reg("REG-OVERLAY-PREFIX", kat, entry=name, overlay=overlay)
                ok = False
            read.append(tokens)
        return ok

    def _target(self, value: Any, tokens: list[str], k: Kind) -> bool:
        if not tokens:
            return False
        if lookup(value, tokens) is not ABSENT:
            return True
        parent = lookup(value, tokens[:-1])
        if not isinstance(parent, dict):
            return False
        nodes = _schemas_at(k.schema, k.defs, value, tokens[:-1])
        return any(isinstance(n.get("properties"), dict) and tokens[-1] in n["properties"] for n in nodes)

    def resolved_value(self, i: int, entry: dict, env: str) -> Any:
        value = _copy(entry["value"])
        for key, new in (self.patches.get(env, {}).get(i) or {}).items():
            value = _set(value, split_pointer(key), _copy(new))
        return value

    def _per_environment(self, v: dict) -> None:
        by_key: dict[tuple, tuple[int, dict]] = {}
        for i, e in self.entries:
            by_key.setdefault((e["kind"], e["id"]), (i, e))
        scopes = v.get("secretScopes")
        for env in self.environments:
            checked: dict[int, Any] = {}
            for i, entry in self.entries:
                if i in self.passed and self.applies(entry, env) and i not in self.failed[env]:
                    checked[i] = self.resolved_value(i, entry, env)
            self.checked[env] = checked
        for env in self.environments:
            for i, value in self.checked[env].items():
                entry = v["entries"][i]
                k = self.pins[entry["kind"]]
                for code, at in validate_value(value, k.schema, k.defs):
                    self._val(code, i, env, at)
                for tokens in k.secrets:
                    for at in positions(value, tokens):
                        code, project = secret_ref(lookup(value, list(at)))
                        if code is not None:
                            self._val(code, i, env, at)
                        elif scopes is None:
                            self._val("REF-SECRET-UNSCOPED", i, env, at)
                        elif project not in scopes.get(env, {}).get("gcp-sm", []):
                            self._val("REF-SECRET-SCOPE", i, env, at)
                found: dict[tuple, set[str]] = {}
                for tokens, kinds in k.references:
                    for at in positions(value, tokens):
                        found.setdefault(at, set()).update(kinds)
                for at in sorted(found):
                    code = self._reference(lookup(value, list(at)), found[at], env, by_key)
                    if code is not None:
                        target = parse_entry_ref(lookup(value, list(at)))
                        if self.defer is not None and target is not None and code in (
                                "REF-ENTRY-MISSING", "REF-ENTRY-ABSENT-IN-ENVIRONMENT", "REF-ENTRY-POINTER") \
                                and self.defer(target[0], target[1]):
                            continue
                        self._val(code, i, env, at)
                        if target is not None:
                            self.ref_results.append((code, i, at, env, target[0], target[1]))

    def _reference(self, value: Any, kinds: set[str], env: str, by_key: dict) -> str | None:
        ref = parse_entry_ref(value)
        if ref is None:
            return "REF-ENTRY-FORM"
        kind, entry_id, tokens = ref
        if kind not in kinds:
            return "REF-ENTRY-KIND"
        if (kind, entry_id) not in by_key:
            return "REF-ENTRY-MISSING"
        i, target = by_key[(kind, entry_id)]
        if not self.applies(target, env):
            return "REF-ENTRY-ABSENT-IN-ENVIRONMENT"
        if tokens is not None and i in self.checked[env]:
            if lookup(self.checked[env][i], tokens) is ABSENT:
                return "REF-ENTRY-POINTER"
        return None

    def _bounds(self, v: dict) -> None:
        counts: dict[str, int] = {}
        for _, entry in self.entries:
            counts[entry["kind"]] = counts.get(entry["kind"], 0) + 1
        for name, k in self.pins.items():
            if counts.get(name, 0) > k.max_entries:
                self._reg("REG-BOUND-ENTRIES", pointer("kinds", self.pin_index[name]), kind=name,
                          pin_index=self.pin_index[name])
        for env in self.environments:
            for i, value in self.checked[env].items():
                k = self.pins[v["entries"][i]["kind"]]
                if len(jcs_bytes(value)) > k.max_entry_bytes:
                    self._val("REG-BOUND-ENTRY-BYTES", i, env, ())
            if self.valid_so_far():
                doc = self.resolve(env)
                if len(jcs_bytes(doc)) > 8 * MIB:
                    self.diags.append(diag("REG-DOC-SIZE", "registry", "", source=self.source, environment=env))
                if depth_of(doc) > 32:
                    self.diags.append(diag("REG-DOC-DEPTH", "registry", "", source=self.source, environment=env))

    def valid_so_far(self) -> bool:
        return self.value is not None and self.passed_shape

    @property
    def valid(self) -> bool:
        return self.passed_shape and not any(severity(d["code"]) == "error" for d in self.diags)

    def resolve(self, env: str) -> dict:
        """Registry §8: the resolved registry of one environment."""
        v = self.value
        entries = []
        for i, entry in self.entries:
            if self.applies(entry, env):
                entries.append({"kind": entry["kind"], "id": entry["id"], "owner": entry["owner"],
                                "value": self.resolved_value(i, entry, env)})
        return {"resolvedFormatVersion": "1.0.0",
                "registry": {"id": v["id"], "version": v["version"], "digest": self.digest},
                "environment": env, "kinds": v["kinds"], "entries": entries}


def _prefix(a: list[str], b: list[str]) -> bool:
    return len(a) < len(b) and b[:len(a)] == a


def _copy(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_copy(v) for v in value]
    return value


def _set(value: Any, tokens: list[str], new: Any) -> Any:
    if not tokens:
        return new
    head, rest = tokens[0], tokens[1:]
    if isinstance(value, dict):
        value[head] = _set(value.get(head), rest, new) if rest else new
    elif isinstance(value, list):
        value[int(head)] = _set(value[int(head)], rest, new) if rest else new
    return value


def validate_registry(registry: bytes, kinds: list[bytes]) -> dict:
    """Registry §7: the `1.0.0` validation report of one registry."""
    v = Validation(registry, [Kind(k) for k in kinds])
    return report("1.0.0", v.diags, v.digest)


def resolve_registry(registry: bytes, kinds: list[bytes], environment: str) -> bytes | None:
    v = Validation(registry, [Kind(k) for k in kinds])
    if not v.valid or environment not in v.environments:
        return None
    return jcs_bytes(v.resolve(environment))


# ==== format 1.1.0 ====

REPORT_VERSION = "1.1.0"
FEDERATION_BOUND = 256 * KIB
INDEX_BOUND = 8 * MIB
BOUNDS_BOUND = 256 * KIB
LOCK_BOUND = 1 * MIB
SIGNATURE_BOUND = 4096
KIND_BOUND = 256 * KIB
REGISTRY_BOUND = 8 * MIB

# ---------------------------------------------------------------------------------------------------
# Ed25519 (RFC 8032), with checkpoint-witness §5's key rule and cofactorless equation

_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _P - 2, _P)) % _P
_SQRT_M1 = pow(2, (_P - 1) // 4, _P)
SMALL_ORDER = frozenset(bytes.fromhex(h) for h in (
    "0100000000000000000000000000000000000000000000000000000000000000",
    "ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f",
    "0000000000000000000000000000000000000000000000000000000000000000",
    "0000000000000000000000000000000000000000000000000000000000000080",
    "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05",
    "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85",
    "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a",
    "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa",
))


def _inv(x: int) -> int:
    return pow(x, _P - 2, _P)


def _recover_x(y: int, sign: int) -> int | None:
    u = (y * y - 1) % _P
    v = (_D * y * y + 1) % _P
    x2 = u * _inv(v) % _P
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P != 0:
        x = x * _SQRT_M1 % _P
    if (x * x - x2) % _P != 0:
        return None
    if (x & 1) != sign:
        x = _P - x
    return x


def _decode_point(data: bytes) -> tuple | None:
    n = int.from_bytes(data, "little")
    y, sign = n & ((1 << 255) - 1), n >> 255
    if y >= _P:
        return None
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % _P)


def _add(a: tuple, b: tuple) -> tuple:
    x1, y1, z1, t1 = a
    x2, y2, z2, t2 = b
    aa = (y1 - x1) * (y2 - x2) % _P
    bb = (y1 + x1) * (y2 + x2) % _P
    cc = 2 * _D * t1 * t2 % _P
    dd = 2 * z1 * z2 % _P
    e, f, g, h = bb - aa, dd - cc, dd + cc, bb + aa
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _mul(k: int, point: tuple) -> tuple:
    out = (0, 1, 1, 0)
    while k:
        if k & 1:
            out = _add(out, point)
        point = _add(point, point)
        k >>= 1
    return out


def _encode_point(point: tuple) -> bytes:
    x, y, z, _ = point
    zi = _inv(z)
    x, y = x * zi % _P, y * zi % _P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


_BY = 4 * _inv(5) % _P
_BASE = (_recover_x(_BY, 0), _BY, 1, _recover_x(_BY, 0) * _BY % _P)


def key_trusted(key: bytes) -> bool:
    """checkpoint-witness §5: canonical, not of small order, and on the curve."""
    if len(key) != 32:
        return False
    n = int.from_bytes(key, "little")
    y, sign = n & ((1 << 255) - 1), n >> 255
    if y >= _P or (y in (1, _P - 1) and sign):
        return False
    if key in SMALL_ORDER:
        return False
    return _decode_point(key) is not None


def ed25519_verify(key: bytes, message: bytes, signature: bytes) -> bool:
    """[S]B - [h]A, encoded, is R byte for byte, with S below L; no cofactor."""
    if len(signature) != 64:
        return False
    point = _decode_point(key)
    if point is None:
        return False
    r, s = signature[:32], int.from_bytes(signature[32:], "little")
    if s >= _L:
        return False
    h = int.from_bytes(hashlib.sha512(r + key + message).digest(), "little") % _L
    x, y, z, t = _mul(h, point)
    check = _add(_mul(s, _BASE), ((-x) % _P, y, z, (-t) % _P))
    return _encode_point(check) == r


def key_id(key_hex: str) -> str:
    """§11, checkpoint-witness §1: the first 32 hexadecimal characters of the key's SHA-256."""
    return hashlib.sha256(bytes.fromhex(key_hex)).hexdigest()[:32]


HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX128 = re.compile(r"[0-9a-f]{128}\Z")
COMMIT = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")

# ---------------------------------------------------------------------------------------------------
# Signature documents (§10, §11 "Reading a signature document" and "Checking a document")

LOCK_SIGNATURE = ("lockSignatureVersion", "lockDigest", b"judgment-pack-registry/lock-signature/1:")
SOURCE_SIGNATURE = ("sourceSignatureVersion", "sourceDigest", b"judgment-pack-registry/source-signature/1:")


class SignatureDocument:
    def __init__(self, data: bytes, form: tuple) -> None:
        self.version_member, self.digest_member, self.prefix = form
        self.data = data
        self.refusals: list[tuple[str, str]] = []
        self.value: dict | None = None
        self.key_id: str | None = None
        self.identity: str | None = None
        self._read()

    @property
    def readable(self) -> bool:
        return self.value is not None and not self.refusals

    def _read(self) -> None:
        data = self.data
        if len(data) > SIGNATURE_BOUND or b"\\" in data:
            self.refusals.append(("LOCK-SIG-DOCUMENT", ""))
            return
        value, refusals = parse_json(data)
        if refusals or not isinstance(value, dict):
            self.refusals.append(("LOCK-SIG-DOCUMENT", ""))
            return
        self.value = value
        self.identity = digest_of(value)
        key = value.get("publicKey")
        if isinstance(key, str) and HEX64.match(key):
            self.key_id = key_id(key)
        vm = self.version_member
        if vm in value and value[vm] != "1.1.0":
            self.refusals.append(("LOCK-SIG-VERSION", pointer(vm)))
            return
        members = (vm, "algorithm", "publicKey", self.digest_member, "signature")
        for name in value:
            if name not in members:
                self.refusals.append(("LOCK-SIG-MEMBER", pointer(name)))
        for name in members:
            if name not in value:
                self.refusals.append(("LOCK-SIG-MEMBER", pointer(name)))
        if "algorithm" in value and value["algorithm"] != "ed25519":
            self.refusals.append(("LOCK-SIG-ALGORITHM", "/algorithm"))
        if "publicKey" in value and not (isinstance(key, str) and HEX64.match(key)
                                         and key_trusted(bytes.fromhex(key))):
            self.refusals.append(("LOCK-SIG-PUBLIC-KEY", "/publicKey"))
        dm = self.digest_member
        if dm in value and not matches(DIGEST, value[dm]):
            self.refusals.append(("LOCK-SIG-FORM", pointer(dm)))
        if "signature" in value and not matches(HEX128, value["signature"]):
            self.refusals.append(("LOCK-SIG-FORM", "/signature"))

    def check(self, expected_key: str, digest: str) -> tuple[str, str] | None:
        """The first failure, in §11's order, of this document against a key and a digest."""
        v = self.value
        if bytes.fromhex(v["publicKey"]) != bytes.fromhex(expected_key):
            return "LOCK-SIG-UNEXPECTED-KEY", "/publicKey"
        if v[self.digest_member] != digest:
            return "LOCK-SIG-DIGEST-MISMATCH", pointer(self.digest_member)
        message = self.prefix + jcs_bytes({self.digest_member: digest, self.version_member: "1.1.0"})
        if not ed25519_verify(bytes.fromhex(expected_key), message, bytes.fromhex(v["signature"])):
            return "LOCK-SIG-INVALID", "/signature"
        return None


def sig_diag(code: str, at: str, document: SignatureDocument | None) -> dict:
    """§2.1: a signature document's diagnostic names its key identifier when the document was read, is
    not LOCK-SIG-DOCUMENT, and has a publicKey of its form; a document never read (None) names none."""
    kid = document.key_id if document is not None else None
    return diag(code, "signature", at, keyId=kid)


# ---------------------------------------------------------------------------------------------------
# Paths (§3) and globs (registry §11.1)

_DEVICE = re.compile(r"(?:CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|(?:COM|LPT)[1-9\u00b9\u00b2\u00b3])\Z", re.I)
_HFS_IGNORED = set(range(0x200C, 0x2010)) | set(range(0x202A, 0x202F)) | set(range(0x206A, 0x2070)) | {0xFEFF}


def _git_name(segment: str) -> bool:
    low = segment.lower()
    for name in (".git", "git~1"):
        if low.startswith(name) and all(c in ". " for c in low[len(name):]):
            return True
    return "".join(c for c in segment if ord(c) not in _HFS_IGNORED).lower() == ".git"


def path_form(path: Any) -> bool:
    """§3: registry §11.3's response path form, without its `owns` condition, of at most 512 bytes."""
    if not isinstance(path, str) or path == "" or len(path.encode("utf-8")) > 512:
        return False
    if path.startswith("/") or path.endswith("/"):
        return False
    if any(c in path for c in "\\:\x00") or any(ord(c) < 0x20 or ord(c) == 0x7f for c in path):
        return False
    for segment in path.split("/"):
        if segment in ("", ".", "..") or segment.startswith("~"):
            return False
        if segment.endswith(".") or segment.endswith(" "):
            return False
        if _DEVICE.match(segment.split(".", 1)[0].rstrip(" ")):
            return False
        if _git_name(segment):
            return False
    return True


def glob_matches(glob: str, path: str) -> bool:
    def seg(g: str, s: str) -> bool:
        return re.fullmatch("".join(".*" if c == "*" else re.escape(c) for c in g), s, re.S) is not None

    def walk(gs: list[str], ps: list[str]) -> bool:
        if not gs:
            return not ps
        if gs[0] == "**":
            if len(gs) == 1:
                return len(ps) >= 1
            return any(walk(gs[1:], ps[k:]) for k in range(len(ps) + 1))
        return bool(ps) and seg(gs[0], ps[0]) and walk(gs[1:], ps[1:])
    return walk(glob.split("/"), path.split("/"))


def owns_globs(manifest: Any) -> list[str]:
    if isinstance(manifest, dict) and isinstance(manifest.get("owns"), list):
        return [g for g in manifest["owns"] if isinstance(g, str)]
    return []


def repository_identity(value: Any) -> bool:
    m = absolute_uri(value)
    return m is not None and m.group("userinfo") is None and m.group("query") is None

# ---------------------------------------------------------------------------------------------------
# The federation manifest (§3)

SOURCE_NAME = KIND_NAME
FEDERATION_MEMBERS = ("federationFormatVersion", "registry", "environments", "sources")
SOURCE_MEMBERS = ("name", "role", "repository", "environments", "registry", "bounds", "kinds")


class Source:
    def __init__(self, index: int, value: dict) -> None:
        self.index = index
        self.name = value.get("name")
        self.role = value.get("role")
        self.repository = value.get("repository")
        self.serves: list[str] = []
        self.paths: list[tuple[str, str, str]] = []  # (pointer in the manifest, path, role)
        self.registry_path = value.get("registry")
        self.bounds_path = value.get("bounds")
        self.kind_paths = value.get("kinds") or []
        self.commit: Any = None
        self.files: dict[str, bytes] = {}
        self.documents: dict[str, Any] = {}
        self.registry: dict | None = None
        self.registry_digest: str | None = None
        self.bounds: dict | None = None
        self.kinds: list[Kind] = []
        self.validation: Validation | None = None

    @property
    def standard(self) -> bool:
        return self.role == "standard"


def read_manifest(data: bytes) -> tuple[dict | None, list[Source], list[dict]]:
    """§4 step 1's admission and §3's form: (manifest, sources, diagnostics)."""
    value, refusals = admit(data, FEDERATION_BOUND, "federationFormatVersion", ("1.1.0",))
    if refusals:
        return None, [], [diag(code, "federation", at) for code, at in refusals]
    out: list[dict] = []

    def bad(at: str) -> None:
        out.append(diag("FED-MANIFEST", "federation", at))
    for name in value:
        if name not in FEDERATION_MEMBERS:
            bad(pointer(name))
    for name in FEDERATION_MEMBERS:
        if name not in value:
            bad(pointer(name))
    reg = value.get("registry", ABSENT)
    if reg is not ABSENT:
        if not isinstance(reg, dict):
            bad("/registry")
        else:
            for name in reg:
                if name not in ("id", "version"):
                    bad(pointer("registry", name))
            if not absolute_uri(reg.get("id")):
                bad("/registry/id")
            if not matches(SEMVER, reg.get("version")):
                bad("/registry/version")
    envs = value.get("environments", ABSENT)
    environments: list[str] = []
    if envs is not ABSENT:
        if not isinstance(envs, list) or not envs or len(envs) > 32:
            bad("/environments")
        else:
            for i, e in enumerate(envs):
                if not matches(ENVIRONMENT, e) or e in envs[:i]:
                    bad(pointer("environments", i))
            environments = [e for e in envs if isinstance(e, str)]
    sources: list[Source] = []
    items = value.get("sources", ABSENT)
    if items is not ABSENT:
        if not isinstance(items, list) or not 1 <= len(items) <= 256:
            bad("/sources")
            items = items if isinstance(items, list) else []
        standards = 0
        names: list[str] = []
        total_paths = 0
        for i, item in enumerate(items):
            at = pointer("sources", i)
            if not isinstance(item, dict):
                bad(at)
                continue
            src = Source(i, item)
            sources.append(src)
            for name in item:
                if name not in SOURCE_MEMBERS:
                    bad(at + "/" + escape_token(name))
            for name in ("name", "role", "repository"):
                if name not in item:
                    bad(at + "/" + name)
            if "name" in item:
                if not matches(SOURCE_NAME, item["name"]) or item["name"] in names:
                    bad(at + "/name")
                elif names and item["name"] < names[-1]:
                    bad(at + "/name")
                if isinstance(item["name"], str):
                    names.append(item["name"])
            if "role" in item:
                if item["role"] == "standard":
                    standards += 1
                    if standards > 1:
                        bad(at + "/role")
                elif item["role"] != "repository":
                    bad(at + "/role")
            if "environments" in item:
                served = item["environments"]
                ok = (src.role == "repository" and isinstance(served, list) and served
                      and all(isinstance(e, str) and e in environments for e in served)
                      and len(set(served)) == len(served)
                      and [e for e in environments if e in served] == served)
                if not ok:
                    bad(at + "/environments")
                src.serves = list(served) if ok else list(environments)
            else:
                src.serves = list(environments)
            if src.role == "repository" and "registry" not in item:
                bad(at + "/registry")
            for member, role in (("registry", "registry"), ("bounds", "bounds")):
                if member in item:
                    if not path_form(item[member]):
                        bad(at + "/" + member)
                    else:
                        src.paths.append((at + "/" + member, item[member], role))
            if "kinds" in item:
                kinds = item["kinds"]
                if not isinstance(kinds, list) or len(kinds) > 64:
                    bad(at + "/kinds")
                    src.kind_paths = []
                else:
                    for k, path in enumerate(kinds):
                        if not path_form(path) or path in kinds[:k]:
                            bad(at + "/kinds/" + str(k))
                        else:
                            src.paths.append((at + "/kinds/" + str(k), path, "kind"))
            folded: list[str] = []
            for where, path, _ in src.paths:
                if path.casefold() in folded:
                    bad(where)
                folded.append(path.casefold())
            total_paths += len(src.paths)
        if items and standards == 0:
            bad("/sources")
        if total_paths > 4096:
            bad("/sources")
    return value, sources, out


# ---------------------------------------------------------------------------------------------------
# Bounds (§6)

ROW_MEMBERS = ("type", "enum", "const", "minimum", "exclusiveMinimum", "maximum", "exclusiveMaximum",
               "minLength", "maxLength", "minItems", "maxItems", "minProperties", "maxProperties",
               "uniqueItems", "required", "patterns")
# Constraints: each is replaced as one by a per-environment bound (§6.4). Length, item and member
# counts are two constraints each, one per member: READING, so that the effective bound admits
# exactly what both admit, as §6.4 says it does.
CONSTRAINTS = (("type",), ("enum", "const"), ("minimum", "exclusiveMinimum"), ("maximum", "exclusiveMaximum"),
               ("minLength",), ("maxLength",), ("minItems",), ("maxItems",), ("minProperties",),
               ("maxProperties",), ("uniqueItems",))
ADDED = ("required", "patterns")
BOUNDS_KIND_MEMBERS = ("kind", "maxEntries", "maxAssemblyEntries", "fields")
FIELD_MEMBERS = ("pointer", "bound", "environments", "description")


def _bound_form(bound: Any, at: str, out: list[tuple[str, str]]) -> dict:
    """§§6.2, 6.3: the bound's usable members; refusals appended as (code, pointer)."""
    if not isinstance(bound, dict):
        out.append(("FED-BOUND-FORM", at))
        return {}
    usable: dict = {}
    for name in sorted(bound):
        value = bound[name]
        here = at + "/" + escape_token(name)
        if name not in ROW_MEMBERS:
            out.append(("FED-BOUND-NOT-COMPARABLE" if name in SCHEMA_KEYWORDS else "FED-BOUND-FORM", here))
            continue
        ok = True
        if name == "type":
            ok = (isinstance(value, str) and value in TYPE_NAMES) or (
                isinstance(value, list) and value and all(isinstance(n, str) and n in TYPE_NAMES for n in value)
                and len(set(value)) == len(value))
        elif name == "enum":
            ok = isinstance(value, list) and 0 < len(value) <= 1024
        elif name in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
            ok = is_number(value)
        elif name in ("minLength", "maxLength", "minItems", "maxItems", "minProperties", "maxProperties"):
            ok = is_count(value)
        elif name == "uniqueItems":
            ok = isinstance(value, bool)
        elif name == "required":
            ok = isinstance(value, list) and all(isinstance(v, str) for v in value) and len(set(value)) == len(value)
        elif name == "patterns":
            ok = (isinstance(value, list) and 0 < len(value) <= 16 and all(isinstance(v, str) for v in value)
                  and len(set(value)) == len(value) and all(compile_pattern(v) is not None for v in value))
        if not ok:
            out.append(("FED-BOUND-FORM", here))
            continue
        usable[name] = value
    return usable


class Field:
    def __init__(self, at: str, pointer_text: str, tokens: list, bound: dict, environments: dict) -> None:
        self.at = at
        self.pointer = pointer_text
        self.tokens = tokens
        self.bound = bound
        self.environments = environments

    def effective(self, env: str) -> tuple[dict, dict]:
        """§6.4's effective bound in `env`, with where each member comes from ("bound" or "env")."""
        over = self.environments.get(env, {})
        out: dict = {}
        origin: dict = {}
        for group in CONSTRAINTS:
            source = over if any(m in over for m in group) else self.bound
            for m in group:
                if m in source:
                    out[m] = source[m]
                    origin[m] = "env" if source is over else "bound"
        for m in ADDED:
            values = list(self.bound.get(m, []))
            values += [v for v in over.get(m, []) if v not in values]
            if values:
                out[m] = values
                origin[m] = "env" if m in over and m not in self.bound else "bound"
        return out, origin


class BoundsKind:
    def __init__(self, at: str, kind: str) -> None:
        self.at = at
        self.kind = kind
        self.max_entries: int | None = None
        self.max_assembly: int | None = None
        self.fields: list[Field] = []


class Bounds:
    """One admitted bounds document, read for its form (§6.1)."""

    def __init__(self, value: dict, source: Source, environments: list[str]) -> None:
        self.source = source
        self.kinds: list[BoundsKind] = []
        self.diags: list[tuple[str, str]] = []
        d = self.diags
        for name in value:
            if name not in ("boundsFormatVersion", "kinds"):
                d.append(("FED-BOUND-FORM", pointer(name)))
        kinds = value.get("kinds", ABSENT)
        if not isinstance(kinds, list):
            d.append(("FED-BOUND-FORM", "/kinds"))
            return
        seen: list[str] = []
        for i, item in enumerate(kinds):
            at = pointer("kinds", i)
            if not isinstance(item, dict) or not matches(KIND_NAME, item.get("kind")):
                d.append(("FED-BOUND-FORM", at))
                continue
            name = item["kind"]
            if name in seen or (seen and name < seen[-1]):
                d.append(("FED-BOUND-FORM", at))
            seen.append(name)
            bk = BoundsKind(at, name)
            for member in item:
                if member not in BOUNDS_KIND_MEMBERS:
                    d.append(("FED-BOUND-FORM", at + "/" + escape_token(member)))
            for member in ("maxEntries", "maxAssemblyEntries"):
                if member in item:
                    v = item[member]
                    if not (is_integer_value(v) and 0 <= v <= 100000):
                        d.append(("FED-BOUND-FORM", at + "/" + member))
                    elif member == "maxAssemblyEntries" and not source.standard:
                        d.append(("FED-BOUND-FORM", at + "/" + member))
                    elif member == "maxEntries":
                        bk.max_entries = int(v)
                    else:
                        bk.max_assembly = int(v)
            fields = item.get("fields", [])
            if not isinstance(fields, list):
                d.append(("FED-BOUND-FORM", at + "/fields"))
                fields = []
            pointers: list[str] = []
            for j, field in enumerate(fields):
                fat = at + "/fields/" + str(j)
                if not isinstance(field, dict) or "pointer" not in field or "bound" not in field:
                    d.append(("FED-BOUND-FORM", fat))
                    continue
                for member in field:
                    if member not in FIELD_MEMBERS:
                        d.append(("FED-BOUND-FORM", fat + "/" + escape_token(member)))
                text = field["pointer"]
                tokens = [] if text == "" else pointer_pattern(text)
                if not isinstance(text, str) or tokens is None:
                    d.append(("FED-BOUND-FORM", fat + "/pointer"))
                    continue
                if text in pointers or (pointers and text < pointers[-1]):
                    d.append(("FED-BOUND-FORM", fat))
                pointers.append(text)
                if "description" in field and not isinstance(field["description"], str):
                    d.append(("FED-BOUND-FORM", fat + "/description"))
                bound = _bound_form(field["bound"], fat + "/bound", d)
                per_env: dict = {}
                if "environments" in field:
                    envs = field["environments"]
                    if not isinstance(envs, dict):
                        d.append(("FED-BOUND-FORM", fat + "/environments"))
                    else:
                        for env in envs:
                            eat = fat + "/environments/" + escape_token(env)
                            if env not in environments or (not source.standard and env not in source.serves):
                                d.append(("FED-BOUND-ENVIRONMENT", eat))
                                continue
                            per_env[env] = _bound_form(envs[env], eat, d)
                bk.fields.append(Field(fat, text, tokens, bound, per_env))
            self.kinds.append(bk)

    def kind(self, name: str) -> BoundsKind | None:
        for bk in self.kinds:
            if bk.kind == name:
                return bk
        return None


def _lower(b: dict, upper: bool = False) -> tuple | None:
    inclusive, exclusive = ("maximum", "exclusiveMaximum") if upper else ("minimum", "exclusiveMinimum")
    best = None
    for member, excl in ((inclusive, False), (exclusive, True)):
        if member in b:
            v = b[member]
            if best is None:
                best = (v, excl, member)
            else:
                tighter = v < best[0] if upper else v > best[0]
                if tighter or (v == best[0] and excl):
                    best = (v, excl, member)
    return best


def _value_set(b: dict) -> list | None:
    if "enum" in b and "const" in b:
        return [v for v in b["enum"] if json_equal(v, b["const"])]
    if "enum" in b:
        return list(b["enum"])
    if "const" in b:
        return [b["const"]]
    return None


def bound_schema(b: dict) -> dict:
    schema = {k: v for k, v in b.items() if k != "patterns"}
    if b.get("patterns"):
        schema["allOf"] = [{"pattern": p} for p in b["patterns"]]
    return schema


def _admits(b: dict, value: Any) -> bool:
    return not any(severity(c) == "error" for c, _ in validate_value(value, bound_schema(b), {}))


def widenings(r: dict, s: dict) -> list[str]:
    """§6.2: the members of R whose row is looser than S's, or that name a value S refuses."""
    out: list[str] = []
    if "type" in r and "type" in s:
        rs = [r["type"]] if isinstance(r["type"], str) else r["type"]
        ss = [s["type"]] if isinstance(s["type"], str) else s["type"]
        if any(t not in ss and not (t == "integer" and "number" in ss) for t in rs):
            out.append("type")
    sset = _value_set(s)
    for member in ("enum", "const"):
        if member not in r:
            continue
        values = r["enum"] if member == "enum" else [r["const"]]
        if sset is not None and any(not any(json_equal(v, w) for w in sset) for v in values):
            out.append(member)
        elif any(not _admits(s, v) for v in values):
            out.append(member)
    for upper in (False, True):
        rl, sl = _lower(r, upper), _lower(s, upper)
        if rl is not None and sl is not None:
            tighter = rl[0] < sl[0] if upper else rl[0] > sl[0]
            if not (tighter or (rl[0] == sl[0] and (rl[1] or not sl[1]))):
                out.append(rl[2])
    for low, high in (("minLength", "maxLength"), ("minItems", "maxItems"), ("minProperties", "maxProperties")):
        if low in r and low in s and r[low] < s[low]:
            out.append(low)
        if high in r and high in s and r[high] > s[high]:
            out.append(high)
    if "uniqueItems" in r and s.get("uniqueItems") is True and r["uniqueItems"] is not True:
        out.append("uniqueItems")
    return out

# ---------------------------------------------------------------------------------------------------
# Assembly (§4)


def _yaml_refused(path: str) -> None:
    if path.endswith(".yaml") or path.endswith(".yml"):
        raise NotImplementedError("this reader does not import YAML (registry §9)")


def _known_identities(known: dict) -> tuple[set[str], set[str]]:
    """The registry digests and ids the known indexes and locks name. READING: a known document
    that is not admissible names nothing, since no code refuses one."""
    digests: set[str] = set()
    ids: set[str] = set()
    for data, selector, bound in ([(d, "indexFormatVersion", INDEX_BOUND) for d in known.get("indexes", [])]
                                  + [(d, "lockFormatVersion", LOCK_BOUND) for d in known.get("locks", [])]):
        value, refusals = admit(data, bound, selector, ("1.1.0",))
        if refusals:
            continue
        reg = value.get("registry")
        if isinstance(reg, dict):
            if isinstance(reg.get("digest"), str):
                digests.add(reg["digest"])
            if isinstance(reg.get("id"), str):
                ids.add(reg["id"])
    return digests, ids


class Assembly:
    """§4: one assembly of a manifest at given commits. `report` and, with no error, `registry`
    and `index` (the documents step 8 writes)."""

    def __init__(self, manifest: bytes, given: dict[str, dict], known: dict) -> None:
        self.diags: list[dict] = []
        self.manifest: dict | None = None
        self.sources: list[Source] = []
        self.assembled: dict | None = None
        self.validation: Validation | None = None
        self.registry: dict | None = None
        self.index: dict | None = None
        self.kinds: list[Kind] = []
        self._run(manifest, given, known)
        digest = self.validation.digest if self.validation is not None and self.validation.passed_shape else None
        self.report = report(REPORT_VERSION, self.diags, digest)
        if self.report["valid"]:
            self.registry_bytes = jcs_bytes(self.assembled)
            self.index_bytes = jcs_bytes(self.index)

    def _errors(self) -> bool:
        return any(severity(d["code"]) == "error" for d in self.diags)

    def _run(self, manifest: bytes, given: dict[str, dict], known: dict) -> None:
        if len(known.get("indexes", [])) > 256 or len(known.get("locks", [])) > 256:
            # READING: at the manifest's root, as a refusal of the assembly before any source.
            self.diags.append(diag("FED-KNOWN-LIMIT", "federation", ""))
            return
        if not self._step1(manifest, given):
            return
        if not self._step2():
            return
        if not self._step3(known):
            return
        self._step4()
        self._step5()
        self._step6()
        self._step7()
        if not self._errors():
            self._step8()

    def _step1(self, manifest: bytes, given: dict[str, dict]) -> bool:
        value, sources, diags = read_manifest(manifest)
        self.diags.extend(diags)
        if value is None:
            return False
        self.manifest = value
        self.sources = sources
        commits: dict[str, str] = {}
        for src in sources:
            at = pointer("sources", src.index)
            g = given.get(src.name) if isinstance(src.name, str) else None
            src.commit = g.get("commit") if g else None
            src.files = dict(g.get("files", {})) if g else {}
            if not matches(COMMIT, src.commit):
                self.diags.append(diag("FED-COMMIT", "federation", at))
            elif isinstance(src.repository, str):
                if src.repository in commits and commits[src.repository] != src.commit:
                    self.diags.append(diag("FED-COMMIT", "federation", at))
                commits.setdefault(src.repository, src.commit)
            if "repository" in (self.manifest["sources"][src.index]) and not repository_identity(src.repository):
                self.diags.append(diag("FED-REPOSITORY", "federation", at + "/repository"))
            for where, path, _ in src.paths:
                if path not in src.files:
                    self.diags.append(diag("FED-SOURCE-MISSING", "federation", where))
        return not self._errors()

    def _step2(self) -> bool:
        for src in self.sources:
            for _, path, role in src.paths:
                _yaml_refused(path)
                data = src.files[path]
                entry = {"path": path, "role": role, "contentDigest": sha256_digest(data)}
                if role == "registry":
                    value, refusals = admit(data, REGISTRY_BOUND, "registryFormatVersion", ("1.0.0",))
                    for code, at in refusals:
                        self.diags.append(diag(code, "registry", at, source=src.name))
                    if value is not None:
                        src.registry = value
                        src.registry_digest = digest_of(value)
                        entry["digest"] = src.registry_digest
                elif role == "bounds":
                    value, refusals = admit(data, BOUNDS_BOUND, "boundsFormatVersion", ("1.1.0",))
                    for code, at in refusals:
                        self.diags.append(diag(code, "bounds", at, source=src.name))
                    if value is not None:
                        src.bounds = value
                        entry["digest"] = digest_of(value)
                else:
                    k = Kind(data, source=src.name)
                    if not k.admitted:
                        self.diags.extend(k.diags)
                    else:
                        src.kinds.append(k)
                        entry["digest"] = k.digest
                src.documents[path] = entry
        return not self._errors()

    def _step3(self, known: dict) -> bool:
        reg_id = self.manifest["registry"]["id"]
        digests, ids = _known_identities(known)
        seen: dict[str, str] = {}
        for src in self.sources:
            r = src.registry
            if r is None:
                continue
            if r.get("environments") != src.serves:
                self.diags.append(diag("FED-ENVIRONMENTS", "registry", "/environments", source=src.name))
            rid = r.get("id")
            if isinstance(rid, str):
                if rid == reg_id or rid in seen:
                    self.diags.append(diag("FED-REGISTRY-DUPLICATE", "registry", "/id", source=src.name))
                seen.setdefault(rid, src.name)
            if src.registry_digest in digests or (isinstance(rid, str) and rid in ids):
                self.diags.append(diag("FED-SOURCE-ASSEMBLED", "registry", "", source=src.name))
        return not self._errors()

    # Step 4 ---------------------------------------------------------------------------------------

    def _standard(self) -> Source | None:
        for src in self.sources:
            if src.standard:
                return src
        return None

    def governed(self) -> dict[str, set[str]]:
        std = self._standard()
        out: dict[str, set[str]] = {}
        for k in (std.kinds if std else []):
            if isinstance(k.kind_member(), str):
                out.setdefault(k.kind_member(), set()).add(k.digest)
        return out

    @staticmethod
    def _pins(src: Source) -> list[tuple[int, dict]]:
        kinds = src.registry.get("kinds") if src.registry else None
        if not isinstance(kinds, list):
            return []
        return [(i, p) for i, p in enumerate(kinds)
                if isinstance(p, dict) and isinstance(p.get("kind"), str) and isinstance(p.get("digest"), str)]

    def _step4(self) -> None:
        governed = self.governed()
        first: dict[str, str] = {}
        for src in self.sources:
            for i, pin in self._pins(src):
                name = pin["kind"]
                at = pointer("kinds", i)
                if name in governed and pin["digest"] not in governed[name]:
                    self.diags.append(diag("FED-KIND-NOT-STANDARD", "registry", at, source=src.name, kind=name))
                if name in first and first[name] != pin["digest"]:
                    self.diags.append(diag("FED-KIND-CONFLICT", "registry", at, source=src.name, kind=name))
                first.setdefault(name, pin["digest"])

    # Step 5 ---------------------------------------------------------------------------------------

    def _declarations(self, digests: set[str]) -> list[Kind]:
        out: list[Kind] = []
        for src in self.sources:
            for k in src.kinds:
                if k.digest in digests:
                    out.append(k)
        return out

    def _holders(self) -> dict[tuple[str, str], list[str]]:
        out: dict[tuple[str, str], list[str]] = {}
        for src in self.sources:
            entries = src.registry.get("entries") if src.registry else None
            for e in entries if isinstance(entries, list) else []:
                if isinstance(e, dict) and isinstance(e.get("kind"), str) and isinstance(e.get("id"), str):
                    out.setdefault((e["kind"], e["id"]), []).append(src.name)
        return out

    def _step5(self) -> None:
        holders = self._holders()
        std = self._standard()
        for src in self.sources:
            if src.registry is None:
                continue
            kinds = self._declarations({p["digest"] for _, p in self._pins(src)})
            name = src.name

            def defer(kind: str, entry_id: str, name: str = name) -> bool:
                return any(h != name for h in holders.get((kind, entry_id), []))
            src.validation = Validation(src.registry, kinds, source=name, defer=defer)
            self.diags.extend(src.validation.diags)
        std_scopes = std.registry.get("secretScopes") if std and std.registry else None
        if isinstance(std_scopes, dict):
            for src in self.sources:
                if src.standard or src.validation is None or not src.validation.passed_shape:
                    continue
                scopes = src.registry.get("secretScopes")
                if not isinstance(scopes, dict):
                    continue
                for env, stores in scopes.items():
                    for store, projects in stores.items():
                        allowed = std_scopes.get(env, {}).get(store, []) if isinstance(std_scopes.get(env), dict) else []
                        for i, p in enumerate(projects):
                            if p not in allowed:
                                self.diags.append(diag("FED-SCOPE-WIDENS", "registry",
                                                       pointer("secretScopes", env, store, i), source=src.name))

    # Step 6 ---------------------------------------------------------------------------------------

    def _step6(self) -> None:
        if any(src.registry is not None and (src.validation is None or not src.validation.passed_shape)
               for src in self.sources):
            # READING: a source whose registry stops at registry §7.1's step 3 has no entries to
            # assemble; its own diagnostics refuse the assembly.
            return
        m = self.manifest
        envs = list(m["environments"])
        owners: set[str] = set()
        pins: dict[str, tuple[dict, str, int]] = {}
        entries: list[tuple[str, str, int, dict, str, int]] = []
        overlays: dict[str, list[tuple[dict, str, int, int]]] = {}
        overlay_first: dict[str, tuple[str, int]] = {}
        std = self._standard()
        for src in self.sources:
            r = src.registry
            if r is None:
                continue
            owners.update(r["owners"])
            for i, pin in enumerate(r["kinds"]):
                pins.setdefault(pin["kind"], (pin, src.name, i))
            fewer = src.serves != envs
            for j, e in src.validation.entries:
                item = dict(e)
                if fewer and "environments" not in item:
                    item["environments"] = list(src.serves)
                entries.append((e["kind"], e["id"], len(entries), item, src.name, j))
            for o, overlay in enumerate(r.get("overlays", [])):
                if (isinstance(overlay, dict) and isinstance(overlay.get("environment"), str)
                        and isinstance(overlay.get("patches"), list)):
                    env = overlay["environment"]
                    overlay_first.setdefault(env, (src.name, o))
                    for p, patch in enumerate(overlay["patches"]):
                        overlays.setdefault(env, []).append((patch, src.name, o, p))
        entries.sort(key=lambda t: (t[0], t[1], t[2]))
        assembled: dict = {"registryFormatVersion": "1.0.0", "id": m["registry"]["id"],
                           "version": m["registry"]["version"], "environments": envs,
                           "owners": sorted(owners),
                           "kinds": [pins[name][0] for name in sorted(pins)],
                           "entries": [t[3] for t in entries]}
        overlay_list = []
        overlay_map: list[tuple[str, int, list[tuple[str, int, int]]]] = []
        for env in envs:
            if env in overlays:
                overlay_list.append({"environment": env, "patches": [t[0] for t in overlays[env]]})
                first_src, first_o = overlay_first[env]
                overlay_map.append((first_src, first_o, [(t[1], t[2], t[3]) for t in overlays[env]]))
        if overlay_list:
            assembled["overlays"] = overlay_list
        if std and std.registry and "secretScopes" in std.registry:
            assembled["secretScopes"] = std.registry["secretScopes"]
        entry_map = [(t[4], t[5]) for t in entries]
        pin_map = [(pins[name][1], pins[name][2]) for name in sorted(pins)]
        std_name = std.name if std else None

        def locate(at: str, entry_index: Any, pin_index: Any, overlay: Any) -> tuple[Any, str]:
            if entry_index is not None:
                name, j = entry_map[entry_index]
                return name, pointer("entries", j) + at[len(pointer("entries", entry_index)):]
            if pin_index is not None:
                name, j = pin_map[pin_index]
                return name, pointer("kinds", j) + at[len(pointer("kinds", pin_index)):]
            if overlay is not None:
                o, p = overlay
                first_src, first_o, patches = overlay_map[o]
                if p is None:
                    return first_src, pointer("overlays", first_o) + at[len(pointer("overlays", o)):]
                name, so, sp = patches[p]
                return name, pointer("overlays", so, "patches", sp) + at[len(pointer("overlays", o, "patches", p)):]
            if at.startswith("/secretScopes"):
                return std_name, at
            return None, at
        self.assembled = assembled
        self.entry_map = entry_map
        kinds = self._declarations({p["digest"] for p in assembled["kinds"]})
        self.validation = Validation(assembled, kinds, locate=locate)
        holders = {}
        for t in entries:
            holders.setdefault((t[0], t[1]), t[4])
        served = {src.name: src.serves for src in self.sources}
        for d in self.validation.diags:
            self.diags.append(d)
        for code, i, at, env, kind, entry_id in self.validation.ref_results:
            if code != "REF-ENTRY-ABSENT-IN-ENVIRONMENT":
                continue
            holder = holders.get((kind, entry_id))
            if holder is not None and env not in served[holder]:
                name, _ = entry_map[i]
                self.diags.append(diag("FED-ENVIRONMENT-GAP", "value", pointer(*at), source=name,
                                       entry=entry_name(assembled["entries"][i]), environment=env))
        listed: dict[str, set[str]] = {}
        for src in self.sources:
            scopes = src.registry.get("secretScopes") if src.registry else None
            if not isinstance(scopes, dict):
                continue
            for env in sorted(scopes):
                for store in scopes[env]:
                    for i, p in enumerate(scopes[env][store]):
                        # §4 step 6: shared when listed for an environment read earlier, whichever listing that was.
                        if listed.get(p, set()) - {env}:
                            self.diags.append(diag("REF-SECRET-SCOPE-SHARED", "registry",
                                                   pointer("secretScopes", env, store, i), source=src.name))
                        listed.setdefault(p, set()).add(env)

    # Step 7 ---------------------------------------------------------------------------------------

    def _declaration_for(self, kind: str) -> Kind | None:
        if self.assembled is not None:
            for pin in self.assembled["kinds"]:
                if pin["kind"] == kind:
                    for k in self._declarations({pin["digest"]}):
                        return k
        std = self._standard()
        for k in (std.kinds if std else []):
            if k.kind_member() == kind:
                return k
        return None

    def _step7(self) -> None:
        envs = list(self.manifest["environments"])
        governed = self.governed()
        pinned = {p["kind"] for p in self.assembled["kinds"]} if self.assembled else set()
        if self.assembled is None:
            for src in self.sources:
                pinned.update(p["kind"] for _, p in self._pins(src))
        docs: list[Bounds] = []
        for src in self.sources:
            if src.bounds is None:
                continue
            b = Bounds(src.bounds, src, envs)
            docs.append(b)
            for code, at in b.diags:
                self.diags.append(diag(code, "bounds", at, source=src.name))
            for bk in b.kinds:
                ok = bk.kind in governed if src.standard else (bk.kind in governed or bk.kind in pinned)
                if not ok:
                    self.diags.append(diag("FED-BOUND-KIND", "bounds", bk.at + "/kind", source=src.name))
                    continue
                k = self._declaration_for(bk.kind)
                if k is None or not k.usable:
                    continue
                for f in bk.fields:
                    if f.tokens and not reachable(k.schema, f.tokens, k.defs):
                        self.diags.append(diag("FED-BOUND-POINTER-UNREACHABLE", "bounds", f.at + "/pointer",
                                               source=src.name))
        std = next((b for b in docs if b.source.standard), None)
        for b in docs:
            for bk in b.kinds:
                for f in bk.fields:
                    for env, eb in f.environments.items():
                        for member in widenings(eb, f.bound):
                            self.diags.append(diag("FED-BOUND-WIDENS", "bounds",
                                                   f.at + "/environments/" + escape_token(env) + "/" + member,
                                                   source=b.source.name))
        if std is not None:
            for b in docs:
                if b is std:
                    continue
                for bk in b.kinds:
                    sk = std.kind(bk.kind)
                    if sk is None:
                        continue
                    if bk.max_entries is not None and sk.max_entries is not None and bk.max_entries > sk.max_entries:
                        self.diags.append(diag("FED-BOUND-WIDENS", "bounds", bk.at + "/maxEntries",
                                               source=b.source.name))
                    for f in bk.fields:
                        same = next((sf for sf in sk.fields if sf.pointer == f.pointer), None)
                        if same is None:
                            if any(patterns_overlap(f.tokens, sf.tokens) for sf in sk.fields):
                                self.diags.append(diag("FED-BOUND-OVERLAP", "bounds", f.at + "/pointer",
                                                       source=b.source.name))
                            continue
                        for member in widenings(f.bound, same.bound):
                            self.diags.append(diag("FED-BOUND-WIDENS", "bounds", f.at + "/bound/" + member,
                                                   source=b.source.name))
                        for env in b.source.serves:
                            r, origin = f.effective(env)
                            s, _ = same.effective(env)
                            for member in widenings(r, s):
                                where = (f.at + "/environments/" + escape_token(env) + "/" + member
                                         if origin.get(member) == "env" else f.at + "/bound/" + member)
                                self.diags.append(diag("FED-BOUND-WIDENS", "bounds", where, source=b.source.name))
        self._values(docs, std)
        self._entry_counts(docs, std)

    def _values(self, docs: list[Bounds], std: Bounds | None) -> None:
        v = self.validation
        if v is None:
            return
        by_source = {b.source.name: b for b in docs}
        for env in v.environments:
            for i, value in v.checked[env].items():
                entry = v.value["entries"][i]
                holder, _ = self.entry_map[i]
                checks: list[Bounds] = [std] if std is not None else []
                own = by_source.get(holder)
                if own is not None and not own.source.standard:
                    checks.append(own)
                for b in checks:
                    bk = b.kind(entry["kind"])
                    if bk is None:
                        continue
                    for f in bk.fields:
                        bound, _ = f.effective(env)
                        for at in positions(value, f.tokens):
                            if not _admits(bound, lookup(value, list(at))):
                                self.diags.append(diag("FED-VALUE-BOUND", "value", pointer(*at),
                                                       source=b.source.name, entry=entry_name(entry),
                                                       environment=env))

    def _entry_counts(self, docs: list[Bounds], std: Bounds | None) -> None:
        for src in self.sources:
            if src.validation is None or not src.validation.passed_shape:
                continue
            limits: dict[str, list[int]] = {}
            for b in ([std] if std is not None else []) + [b for b in docs if b.source is src and not src.standard]:
                for bk in b.kinds:
                    if bk.max_entries is not None:
                        limits.setdefault(bk.kind, []).append(bk.max_entries)
            counts: dict[str, int] = {}
            for j, e in src.validation.entries:
                counts[e["kind"]] = counts.get(e["kind"], 0) + 1
                if any(counts[e["kind"]] == limit + 1 for limit in limits.get(e["kind"], [])):
                    self.diags.append(diag("FED-BOUND-ENTRIES", "registry", pointer("entries", j),
                                           source=src.name, entry=entry_name(e)))
        if std is not None and self.assembled is not None:
            counts = {}
            for i, e in enumerate(self.assembled["entries"]):
                counts[e["kind"]] = counts.get(e["kind"], 0) + 1
                bk = std.kind(e["kind"])
                if bk is not None and bk.max_assembly is not None and counts[e["kind"]] == bk.max_assembly + 1:
                    name, j = self.entry_map[i]
                    self.diags.append(diag("FED-BOUND-ENTRIES", "registry", pointer("entries", j),
                                           source=name, entry=entry_name(e)))

    # Step 8 ---------------------------------------------------------------------------------------

    def _step8(self) -> None:
        if len(jcs_bytes(self.assembled)) > REGISTRY_BOUND:
            self.diags.append(diag("REG-DOC-SIZE", "registry", ""))
            return
        m = self.manifest
        self.index = {
            "indexFormatVersion": "1.1.0",
            "federation": {"digest": digest_of(m)},
            "registry": {"id": m["registry"]["id"], "version": m["registry"]["version"],
                         "digest": digest_of(self.assembled)},
            "sources": [{"name": src.name, "role": src.role, "repository": src.repository, "commit": src.commit,
                         "documents": [src.documents[p] for p in sorted(src.documents)]}
                        for src in self.sources],
        }
        self.registry = self.assembled

    def resolved(self) -> list[dict]:
        return [{"environment": env, "digest": digest_of(self.validation.resolve(env))}
                for env in self.validation.environments]


def assemble(manifest: bytes, sources: dict[str, dict], known: dict) -> tuple[dict, dict | None]:
    """§4: the report, and, for an assembly with no error, the bytes it writes."""
    a = Assembly(manifest, sources, known)
    writes = {"registry": a.registry_bytes, "index": a.index_bytes} if a.report["valid"] else None
    return a.report, writes


def statement(item: dict) -> dict:
    """§10.2: the source statement of an index's source item."""
    return {"repository": item.get("repository"), "commit": item.get("commit"),
            "documents": [{"path": d.get("path"), "role": d.get("role"), "contentDigest": d.get("contentDigest"),
                           "digest": d.get("digest")} for d in item.get("documents", []) if isinstance(d, dict)]}


def _first_difference(a: Any, b: Any, at: str, skip: set[str]) -> str | None:
    if at in skip:
        return None
    if isinstance(a, dict) and isinstance(b, dict):
        for name in sorted(set(a) | set(b), key=lambda k: k.encode("utf-16-be")):
            here = at + "/" + escape_token(name)
            if name not in a or name not in b:
                if here not in skip:
                    return here
                continue
            found = _first_difference(a[name], b[name], here, skip)
            if found is not None:
                return found
        return None
    if isinstance(a, list) and isinstance(b, list):
        for i in range(max(len(a), len(b))):
            here = at + "/" + str(i)
            if i >= len(a) or i >= len(b):
                return here
            found = _first_difference(a[i], b[i], here, skip)
            if found is not None:
                return found
        return None
    return None if json_equal(a, b) else at


def check_index(manifest: bytes, sources: dict[str, dict], known: dict, index: bytes) -> dict:
    """§5.1."""
    a = Assembly(manifest, sources, known)
    if not a.report["valid"]:
        return a.report
    diags = list(a.diags)
    given, refusals = admit(index, INDEX_BOUND, "indexFormatVersion", ("1.1.0",))
    digest = a.validation.digest
    if refusals:
        diags.extend(diag(code, "index", at) for code, at in refusals)
        return report(REPORT_VERSION, diags, digest)
    built = a.index
    skip: set[str] = set()
    for i, item in enumerate(built["sources"]):
        other = lookup(given, ["sources", str(i), "documents"])
        for j, doc in enumerate(item["documents"]):
            here = pointer("sources", i, "documents", j, "contentDigest")
            g = lookup(other, [str(j)]) if isinstance(other, list) else ABSENT
            if isinstance(g, dict) and g.get("path") == doc["path"] and "contentDigest" in g:
                skip.add(here)
                if g["contentDigest"] != doc["contentDigest"]:
                    diags.append(diag("FED-INDEX-MISMATCH", "index", here))
    if lookup(given, ["federation", "digest"]) is not ABSENT:
        skip.add("/federation/digest")
        if lookup(given, ["federation", "digest"]) != built["federation"]["digest"]:
            diags.append(diag("FED-INDEX-MISMATCH", "index", "/federation/digest"))
    first = _first_difference(built, given, "", skip)
    if first is not None:
        diags.append(diag("FED-INDEX-MISMATCH", "index", first))
    return report(REPORT_VERSION, diags, digest)

# ---------------------------------------------------------------------------------------------------
# The lock (§7)

LOCK_MEMBERS = ("lockFormatVersion", "serial", "registry", "kinds", "resolved", "index", "sources", "emitters")
LOCK_REQUIRED = ("serial", "registry", "kinds", "resolved")
MODES = ("0644", "0755")


def _pin_form(pin: Any) -> bool:
    return (isinstance(pin, dict) and set(pin) == {"kind", "id", "version", "digest"}
            and matches(KIND_NAME, pin["kind"]) and absolute_uri(pin["id"]) is not None
            and matches(SEMVER, pin["version"]) and matches(DIGEST, pin["digest"]))


def lock_form(v: dict) -> list[str]:
    """§7's form: the pointers at which the lock is not of it (`LOCK-FORM`)."""
    out: list[str] = []
    for name in v:
        if name not in LOCK_MEMBERS:
            out.append(pointer(name))
    for name in LOCK_REQUIRED:
        if name not in v:
            out.append(pointer(name))
    if "serial" in v and not (is_integer_value(v["serial"]) and 1 <= v["serial"] <= MAX_SAFE):
        out.append("/serial")
    r = v.get("registry", ABSENT)
    if r is not ABSENT and not (isinstance(r, dict) and set(r) == {"id", "version", "digest"}
                                and absolute_uri(r["id"]) is not None and matches(SEMVER, r["version"])
                                and matches(DIGEST, r["digest"])):
        out.append("/registry")
    if "kinds" in v:
        if not isinstance(v["kinds"], list):
            out.append("/kinds")
        else:
            out.extend(pointer("kinds", i) for i, p in enumerate(v["kinds"]) if not _pin_form(p))
    if "resolved" in v:
        res = v["resolved"]
        if not isinstance(res, list) or not 1 <= len(res) <= 32:
            out.append("/resolved")
        else:
            for i, item in enumerate(res):
                if not (isinstance(item, dict) and set(item) == {"environment", "digest"}
                        and matches(ENVIRONMENT, item["environment"]) and matches(DIGEST, item["digest"])):
                    out.append(pointer("resolved", i))
    if "index" in v and not (isinstance(v["index"], dict) and set(v["index"]) == {"digest"}
                             and matches(DIGEST, v["index"]["digest"])):
        out.append("/index")
    if ("index" in v) != ("sources" in v):
        out.append("/sources" if "index" in v else "/index")
    if "sources" in v:
        src = v["sources"]
        if not isinstance(src, list) or not 1 <= len(src) <= 256:
            out.append("/sources")
        else:
            for i, item in enumerate(src):
                if not (isinstance(item, dict) and set(item) == {"name", "role", "repository", "statement", "signature"}
                        and matches(SOURCE_NAME, item["name"]) and item["role"] in ("standard", "repository")
                        and repository_identity(item["repository"]) and matches(DIGEST, item["statement"])
                        and matches(DIGEST, item["signature"])):
                    out.append(pointer("sources", i))
    if "emitters" in v:
        em = v["emitters"]
        if not isinstance(em, list):
            out.append("/emitters")
        else:
            keys = []
            for i, item in enumerate(em):
                at = pointer("emitters", i)
                members = {"path", "digest", "files"} | ({"source"} if "index" in v else set())
                if not (isinstance(item, dict) and set(item) == members and path_form(item["path"])
                        and matches(DIGEST, item["digest"]) and isinstance(item["files"], list)
                        and ("source" not in item or matches(SOURCE_NAME, item["source"]))):
                    out.append(at)
                    continue
                keys.append((item.get("source", ""), item["path"]))
                paths = []
                for k, f in enumerate(item["files"]):
                    if not (isinstance(f, dict) and set(f) == {"path", "mode", "digest"} and path_form(f["path"])
                            and f["mode"] in MODES and matches(DIGEST, f["digest"])):
                        out.append(at + "/files/" + str(k))
                        continue
                    paths.append(f["path"])
                if paths != sorted(paths) or len(set(paths)) != len(paths):
                    out.append(at + "/files")
            if keys != sorted(keys) or len(set(keys)) != len(keys):
                out.append("/emitters")
    return out


def lock_digest(data: bytes) -> str:
    """§7: the SHA-256 of the lock's bytes without one final line feed."""
    return sha256_digest(data[:-1] if data.endswith(b"\n") else data)


def _expect_problems(expect: dict, coverage: bool = False) -> bool:
    if not isinstance(expect, dict):
        return True
    if "registryId" not in expect or absolute_uri(expect["registryId"]) is None:
        return True
    if not isinstance(expect.get("requireIndex"), bool):
        return True
    if coverage and not matches(ENVIRONMENT, expect.get("environment")):
        return True
    return False


def read_lock(data: bytes, expect: dict) -> tuple[dict | None, list[dict]]:
    """§9 step 1: the lock, or its diagnostics."""
    value, refusals = admit(data, LOCK_BOUND, "lockFormatVersion", ("1.1.0",))
    if refusals:
        return None, [diag(code, "lock", at) for code, at in refusals]
    out = [diag("LOCK-FORM", "lock", at) for at in lock_form(value)]
    if out:
        return None, out
    body = data[:-1] if data.endswith(b"\n") else data
    if body != jcs_bytes(value):
        out.append(diag("LOCK-NOT-CANONICAL", "lock", ""))
    if value["registry"]["id"] != expect["registryId"]:
        out.append(diag("LOCK-UNEXPECTED-REGISTRY", "lock", "/registry/id"))
    if expect["requireIndex"] and "index" not in value:
        out.append(diag("LOCK-INDEX-REQUIRED", "lock", "/index"))
    return (None if out else value), out


class Emitter:
    """An emitter manifest given with its files: `files` maps a path to (mode, bytes)."""

    def __init__(self, manifest: bytes, path: str, files: list[tuple[str, str, bytes]], source: str | None = None,
                 check: int | None = None) -> None:
        self.manifest = manifest
        self.path = path
        self.source = source
        self.check = check
        self.files = {p: (mode, data) for p, mode, data in files}
        self.value, self.refusals = parse_json(manifest)

    def digest(self) -> str | None:
        return digest_of(self.value) if not self.refusals else None

    def item(self) -> dict:
        globs = owns_globs(self.value)
        files = [{"path": p, "mode": mode, "digest": sha256_digest(data)}
                 for p, (mode, data) in sorted(self.files.items()) if any(glob_matches(g, p) for g in globs)]
        out = {"path": self.path, "digest": self.digest(), "files": files}
        if self.source is not None:
            out["source"] = self.source
        return out


def _emitter_key(item: dict) -> tuple[str, str]:
    return item.get("source", ""), item["path"]


# ---------------------------------------------------------------------------------------------------
# The expected signer set (§11)


def signer_problems(signers: dict, expect: dict) -> list[str]:
    """§11 Verifying step 1, the signer set's part: the codes, before anything is read."""
    out: list[str] = []
    key = signers.get("key") if isinstance(signers, dict) else None
    repos = signers.get("repositories") if isinstance(signers, dict) else None
    if not (isinstance(key, str) and HEX64.match(key) and key_trusted(bytes.fromhex(key))):
        out.append("LOCK-SIG-EXPECTED-KEY")
    if repos is not None:
        if not isinstance(repos, dict):
            out.append("LOCK-EXPECTED")
            repos = {}
        for identity, k in repos.items():
            if not (isinstance(k, str) and HEX64.match(k) and key_trusted(bytes.fromhex(k))):
                out.append("LOCK-SIG-EXPECTED-KEY")
    require = expect.get("requireIndex") if isinstance(expect, dict) else None
    if isinstance(require, bool) and (repos is not None) != require:
        out.append("LOCK-EXPECTED")
    if repos:
        keys = [bytes.fromhex(k) for k in repos.values() if isinstance(k, str) and HEX64.match(k)]
        if isinstance(key, str) and HEX64.match(key) and bytes.fromhex(key) in keys:
            out.append("LOCK-EXPECTED")
        if len(set(keys)) != len(keys):
            out.append("LOCK-EXPECTED")
    return out


def _key_for(item: dict, signers: dict) -> str | None:
    if item["role"] == "standard":
        return signers.get("key")
    return (signers.get("repositories") or {}).get(item["repository"])


# ---------------------------------------------------------------------------------------------------
# Writing a lock (§8)


def write_lock(*, registry: bytes | None = None, kinds: list[bytes] | None = None, federation: bytes | None = None,
               sources: dict | None = None, known: dict | None = None, source_signatures: list[bytes] = (),
               signers: dict | None = None, previous: bytes | None = None, first_serial: int | None = None,
               emitters: list[Emitter] = ()) -> bytes | dict:
    """§8: the lock's JCS bytes, or {"refused": [codes]}."""
    refused: list[str] = []
    assembly = None
    if federation is not None:
        assembly = Assembly(federation, sources or {}, known or {"indexes": [], "locks": []})
        if not assembly.report["valid"]:
            refused.append("LOCK-REGISTRY-INVALID")
        v = assembly.validation
        reg_value = assembly.assembled
    else:
        v = Validation(registry, [Kind(k) for k in kinds or []])
        if not v.valid:
            refused.append("LOCK-REGISTRY-INVALID")
        reg_value = v.value
    reg_id = reg_value.get("id") if isinstance(reg_value, dict) else None
    serial = first_serial
    if previous is not None:
        prev, refusals = admit(previous, LOCK_BOUND, "lockFormatVersion", ("1.1.0",))
        if refusals or lock_form(prev):
            refused.append("LOCK-FORM")
        elif prev["registry"]["id"] != reg_id:
            refused.append("LOCK-UNEXPECTED-REGISTRY")
        elif prev["serial"] >= MAX_SAFE:
            refused.append("LOCK-FORM")
        else:
            serial = int(prev["serial"]) + 1
    elif first_serial is None or not (is_integer_value(first_serial) and 1 <= first_serial <= MAX_SAFE):
        refused.append("LOCK-FORM")
    lock_sources = None
    if assembly is not None:
        refused.extend(signer_problems(signers or {}, {"requireIndex": True}))
        if assembly.index is not None and "LOCK-SIG-EXPECTED-KEY" not in refused:
            items = assembly.index["sources"]
            docs = list(source_signatures)
            if len(docs) < len(items):
                refused.append("LOCK-SIG-MISSING")
            if len(docs) > len(items):
                refused.append("LOCK-SIG-EXTRA")
            lock_sources = []
            # READING: the writer is given one document per source, in the sources' order.
            for item, data in zip(items, docs):
                doc = SignatureDocument(data, SOURCE_SIGNATURE)
                key = _key_for(item, signers)
                if not doc.readable:
                    refused.extend(code for code, _ in doc.refusals)
                    continue
                if key is None:
                    refused.append("LOCK-EXPECTED")
                    continue
                failure = doc.check(key, digest_of(statement(item)))
                if failure is not None:
                    refused.append(failure[0])
                    continue
                lock_sources.append({"name": item["name"], "role": item["role"], "repository": item["repository"],
                                     "statement": digest_of(statement(item)), "signature": doc.identity})
    emitter_items = []
    for e in emitters:
        if e.check != 0 or e.refusals:
            refused.append("LOCK-EMITTER-MISMATCH")
            continue
        emitter_items.append(e.item())
    if refused:
        return {"refused": sorted(set(refused))}
    lock: dict = {"lockFormatVersion": "1.1.0", "serial": serial,
                  "registry": {"id": reg_value["id"], "version": reg_value["version"], "digest": v.digest},
                  "kinds": reg_value["kinds"],
                  "resolved": [{"environment": env, "digest": digest_of(v.resolve(env))} for env in v.environments]}
    if assembly is not None:
        lock["index"] = {"digest": digest_of(assembly.index)}
        lock["sources"] = lock_sources
    if emitters:
        lock["emitters"] = sorted(emitter_items, key=_emitter_key)
    data = jcs_bytes(lock)
    if len(data) > LOCK_BOUND:
        return {"refused": ["LOCK-FORM"]}
    return data


# ---------------------------------------------------------------------------------------------------
# Checking a lock (§9) and coverage (§9.1)


def _check_rest(lock: dict, registry: bytes | None, kinds: list[bytes], index: bytes | None,
                emitters: list[Emitter] | None, diags: list[dict]) -> tuple[bool, str | None, dict | None]:
    """§9 steps 2 to 8 over an accepted lock. Returns (go on, the registry's digest, the index)."""
    v = Validation(registry, [Kind(k) for k in kinds])
    diags.extend(v.diags)
    digest = v.digest if v.passed_shape else None
    if not v.valid:
        diags.append(diag("LOCK-REGISTRY-INVALID", "registry", ""))
        return False, digest, None
    r = v.value
    if [lock["registry"][m] for m in ("id", "version", "digest")] != [r["id"], r["version"], v.digest]:
        diags.append(diag("LOCK-REGISTRY-MISMATCH", "lock", "/registry"))
    lk, rk = lock["kinds"], r["kinds"]
    if len(lk) != len(rk):
        diags.append(diag("LOCK-KINDS-MISMATCH", "lock", "/kinds"))
    else:
        for i, (a, b) in enumerate(zip(lk, rk)):
            if not json_equal(a, b):
                diags.append(diag("LOCK-KINDS-MISMATCH", "lock", pointer("kinds", i)))
                break
    res = lock["resolved"]
    for i in range(max(len(res), len(v.environments))):
        at = pointer("resolved", i) if i < len(res) else "/resolved"
        if i >= len(res) or i >= len(v.environments) or res[i]["environment"] != v.environments[i]:
            diags.append(diag("LOCK-RESOLVED-MISMATCH", "lock", at))
        elif res[i]["digest"] != digest_of(v.resolve(v.environments[i])):
            diags.append(diag("LOCK-RESOLVED-MISMATCH", "lock", at))
    idx = _check_index_and_sources(lock, index, diags)
    _check_emitters(lock, emitters, diags)
    return True, digest, idx


def _check_index_and_sources(lock: dict, index: bytes | None, diags: list[dict]) -> dict | None:
    """§9 steps 6 and 7."""
    if "index" not in lock:
        if index is not None:
            diags.append(diag("LOCK-INDEX-UNLOCKED", "index", ""))
        return None
    if index is None:
        diags.append(diag("LOCK-INDEX-MISSING", "lock", "/index"))
        return None
    value, refusals = admit(index, INDEX_BOUND, "indexFormatVersion", ("1.1.0",))
    if refusals:
        diags.extend(diag(code, "index", at) for code, at in refusals)
        return None
    items = value.get("sources") if isinstance(value.get("sources"), list) else []
    standards = sum(1 for it in items if isinstance(it, dict) and it.get("role") == "standard")
    if digest_of(value) != lock["index"]["digest"]:
        diags.append(diag("LOCK-INDEX-MISMATCH", "lock", "/index"))
        return None
    # READING: an index the lock names that breaks a rule of its own is located at the index's
    # member that breaks it.
    if lookup(value, ["registry", "digest"]) != lock["registry"]["digest"]:
        diags.append(diag("LOCK-INDEX-MISMATCH", "index", "/registry/digest"))
        return None
    if standards != 1:
        diags.append(diag("LOCK-INDEX-MISMATCH", "index", "/sources"))
        return None
    ls = lock["sources"]
    for i in range(max(len(ls), len(items))):
        if i >= len(ls):
            diags.append(diag("LOCK-SOURCES-MISMATCH", "lock", "/sources"))
            break
        item = items[i] if i < len(items) else None
        mine = ls[i]
        if (not isinstance(item, dict) or [mine[m] for m in ("name", "role", "repository")]
                != [item.get(m) for m in ("name", "role", "repository")]
                or mine["statement"] != digest_of(statement(item))):
            diags.append(diag("LOCK-SOURCES-MISMATCH", "lock", pointer("sources", i)))
    return value


def _check_emitters(lock: dict, emitters: list[Emitter] | None, diags: list[dict]) -> None:
    """§9 step 8."""
    if "emitters" not in lock:
        if emitters:
            diags.append(diag("LOCK-EMITTER-MISMATCH", "lock", "/emitters"))
        return
    if not emitters:
        diags.append(diag("LOCK-EMITTER-MISSING", "lock", "/emitters"))
        return
    given = {(e.source or "", e.path): e for e in emitters}
    if set(given) - {_emitter_key(item) for item in lock["emitters"]}:
        diags.append(diag("LOCK-EMITTER-MISMATCH", "lock", "/emitters"))
    for i, item in enumerate(lock["emitters"]):
        at = pointer("emitters", i)
        e = given.get(_emitter_key(item))
        if e is None:
            diags.append(diag("LOCK-EMITTER-MISSING", "lock", at))
            continue
        for code, where in e.refusals:
            diags.append(diag(code, "emitter", where))
        if e.digest() != item["digest"]:
            diags.append(diag("LOCK-EMITTER-MISMATCH", "lock", at))
        listed = {f["path"] for f in item["files"]}
        for k, f in enumerate(item["files"]):
            fat = at + "/files/" + str(k)
            if f["path"] not in e.files:
                diags.append(diag("LOCK-EMITTER-MISSING", "lock", fat))
                continue
            mode, data = e.files[f["path"]]
            if mode != f["mode"] or sha256_digest(data) != f["digest"]:
                diags.append(diag("LOCK-EMITTER-MISMATCH", "lock", fat))
        globs = owns_globs(e.value)
        for path in e.files:
            if path not in listed and any(glob_matches(g, path) for g in globs):
                diags.append(diag("LOCK-EMITTER-MISMATCH", "lock", at))


def check_lock(lock: bytes, registry: bytes, kinds: list[bytes], expect: dict, index: bytes | None = None,
               emitters: list[Emitter] | None = None) -> dict:
    """§9: the report of a lock check."""
    if _expect_problems(expect):
        return report(REPORT_VERSION, [diag("LOCK-EXPECTED", "lock", "")])
    value, diags = read_lock(lock, expect)
    if value is None:
        return report(REPORT_VERSION, diags)
    _, digest, _ = _check_rest(value, registry, kinds, index, emitters, diags)
    return report(REPORT_VERSION, diags, digest)


def _coverage(lock: dict, expect: dict, resolved: bytes | None, file: dict | None, diags: list[dict]) -> None:
    if resolved is not None:
        value, refusals = admit(resolved, REGISTRY_BOUND, "resolvedFormatVersion", ("1.0.0",))
        at = next((i for i, r in enumerate(lock["resolved"]) if r["environment"] == expect["environment"]), None)
        want = lock["resolved"][at]["digest"] if at is not None else None
        if (refusals or value.get("environment") != expect["environment"]
                or lookup(value, ["registry", "digest"]) != lock["registry"]["digest"] or digest_of(value) != want):
            # READING: at the lock's resolved item for the expected environment, or at /resolved
            # when the lock names none.
            diags.append(diag("LOCK-NOT-COVERED", "lock", "/resolved" if at is None else pointer("resolved", at)))
    if file is not None:
        covered = False
        for item in lock.get("emitters", []):
            if "index" in lock and item.get("source") != file.get("source"):
                continue
            for f in item["files"]:
                if (f["path"] == file["path"] and f["mode"] == file["mode"]
                        and f["digest"] == sha256_digest(file["bytes"])):
                    covered = True
        if not covered:
            diags.append(diag("LOCK-NOT-COVERED", "lock", "/emitters"))


def coverage(lock: bytes, expect: dict, resolved: bytes | None = None, file: dict | None = None) -> dict:
    """§9.1: `file` is {"path", "mode", "bytes", "source"?}."""
    if _expect_problems(expect, coverage=True):
        return report(REPORT_VERSION, [diag("LOCK-EXPECTED", "lock", "")])
    value, diags = read_lock(lock, expect)
    if value is None:
        return report(REPORT_VERSION, diags)
    _coverage(value, expect, resolved, file, diags)
    return report(REPORT_VERSION, diags)

# ---------------------------------------------------------------------------------------------------
# Verification (§11)


def _record_form(record: Any) -> bool:
    return (isinstance(record, dict) and set(record) == {"serial", "digest"} and is_integer_value(record["serial"])
            and 1 <= record["serial"] <= MAX_SAFE and matches(DIGEST, record["digest"]))


def _serial_rule(serial: int, digest: str, record: dict | None, floor: int | None) -> str | None:
    """§11 Rollback: the code a lock's serial and digest earn under a record and a floor."""
    if record is not None and (floor is None or floor <= record["serial"]):
        if serial < record["serial"]:
            return "LOCK-SERIAL-ROLLBACK"
        if serial == record["serial"] and digest != record["digest"]:
            return "LOCK-SERIAL-CONFLICT"
        return None
    if floor is not None and serial < floor:
        return "LOCK-SERIAL-ROLLBACK"
    return None


ABSENT_RECORD = object()


def verify(*, lock: bytes, lock_signatures: list[bytes], source_signatures: list[bytes], signers: dict,
           expect: dict, record: Any, floor: Any = None, index: bytes | None = None, concurrent: Any = None,
           write_fails: bool = False, registry: bytes | None = None, kinds: list[bytes] = (),
           resolved: bytes | None = None, file: dict | None = None) -> tuple[dict, Any]:
    """§11: the report, and the verifier's record for the expected registry id once it ends."""
    final_record = concurrent if concurrent is not None else record
    diags: list[dict] = []

    def done(digest: str | None = None) -> tuple[dict, Any]:
        return report(REPORT_VERSION, diags, digest), final_record
    # Step 1: the expected inputs, before the lock or any document is read.
    for code in signer_problems(signers, expect):
        diags.append(diag(code, "lock", ""))
    if _expect_problems(expect, coverage=resolved is not None or file is not None):
        diags.append(diag("LOCK-EXPECTED", "lock", ""))
    floor_ok = floor if (floor is not None and is_integer_value(floor) and 1 <= floor <= MAX_SAFE) else None
    if floor is not None and floor_ok is None:
        diags.append(diag("LOCK-EXPECTED", "lock", ""))
    if record is not None and not _record_form(record):
        diags.append(diag("LOCK-SERIAL-STATE", "lock", ""))
    elif record is None and floor is None:
        diags.append(diag("LOCK-EXPECTED", "lock", ""))
    if diags:
        return done()
    # Step 2: the lock signature, before the lock is parsed. §11 (Verifying): only the first is read.
    if not lock_signatures:
        diags.append(diag("LOCK-SIG-MISSING", "lock", ""))
        return done()
    for _ in lock_signatures[1:]:
        diags.append(sig_diag("LOCK-SIG-EXTRA", "", None))
    first = SignatureDocument(lock_signatures[0], LOCK_SIGNATURE)
    for code, at in first.refusals:
        diags.append(sig_diag(code, at, first))
    if first.readable:
        failure = first.check(signers["key"], lock_digest(lock))
        if failure is not None:
            diags.append(sig_diag(failure[0], failure[1], first))
    if diags:
        return done()
    # Step 3: the lock.
    value, lock_diags = read_lock(lock, expect)
    diags.extend(lock_diags)
    if value is None:
        return done()
    digest = lock_digest(lock)
    # Step 4: the serial.
    code = _serial_rule(value["serial"], digest, record, floor_ok)
    if code is not None:
        diags.append(diag(code, "lock", "/serial"))
    # Step 5: the index.
    index_value = None
    if index is not None:
        index_value, refusals = admit(index, INDEX_BOUND, "indexFormatVersion", ("1.1.0",))
    _check_index_and_sources(value, index, diags)
    # Step 6: the source signatures.
    items = value.get("sources", [])
    room = max(0, len(items) + 1 - len(lock_signatures))
    # §11 (Verifying): counted in the order given, the lock signature first; once step 3 accepts the
    # lock, before any source signature document is read, those beyond the lock's `sources` count plus
    # one are LOCK-SIG-EXTRA and never read.
    for _ in source_signatures[room:]:
        diags.append(sig_diag("LOCK-SIG-EXTRA", "", None))
    docs = [SignatureDocument(d, SOURCE_SIGNATURE) for d in source_signatures[:room]]
    matched: dict[int, SignatureDocument] = {}
    for doc in docs:
        if not doc.readable:
            for code, at in doc.refusals:
                diags.append(sig_diag(code, at, doc))
            continue
        target = next((i for i, it in enumerate(items) if it["signature"] == doc.identity), None)
        if target is None or target in matched:
            diags.append(sig_diag("LOCK-SIG-EXTRA", "", doc))
            continue
        matched[target] = doc
    repos = signers.get("repositories") or {}
    by_name = {}
    if isinstance(index_value, dict) and isinstance(index_value.get("sources"), list):
        by_name = {it.get("name"): it for it in index_value["sources"] if isinstance(it, dict)}
    for i, item in enumerate(items):
        # READING: found once the lock is read, at the lock's item.
        if item["role"] == "standard":
            if item["repository"] in repos:
                diags.append(diag("LOCK-EXPECTED", "lock", pointer("sources", i)))
                continue
        elif item["repository"] not in repos:
            diags.append(diag("LOCK-EXPECTED", "lock", pointer("sources", i)))
            continue
        if i not in matched:
            diags.append(diag("LOCK-SIG-MISSING", "lock", pointer("sources", i)))
            continue
        index_item = by_name.get(item["name"])
        if index_item is None:
            continue
        failure = matched[i].check(_key_for(item, signers), digest_of(statement(index_item)))
        if failure is not None:
            diags.append(sig_diag(failure[0], failure[1], matched[i]))
    # Step 7: the rest of §9, and coverage.
    reg_digest = None
    if registry is not None:
        _, reg_digest, _ = _check_rest(value, registry, list(kinds), index, None, diags)
    if resolved is not None or file is not None:
        _coverage(value, expect, resolved, file, diags)
    if any(severity(d["code"]) == "error" for d in diags):
        return done(reg_digest)
    # Recording: a compare and set against the record step 1 read.
    current = record
    if concurrent is not None:
        current = concurrent
        code = _serial_rule(value["serial"], digest, concurrent, floor_ok)
        if code is not None:
            diags.append(diag(code, "lock", "/serial"))
            return done(reg_digest)
    if current is not None and current.get("serial") == value["serial"] and current.get("digest") == digest:
        final_record = current
        return done(reg_digest)
    if write_fails:
        diags.append(diag("LOCK-SERIAL-STATE", "lock", ""))
        final_record = current
        return done(reg_digest)
    final_record = {"serial": value["serial"], "digest": digest}
    return done(reg_digest)

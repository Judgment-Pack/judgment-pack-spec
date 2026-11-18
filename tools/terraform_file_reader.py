"""A second reader of the terraform-file reading `1.0.0`, status proposed (spec/terraform-file.md).

It was written from the text alone: spec/terraform-file.md §§1-12, the registry companion's §10.1
(the number normal form and the facts bound) and §10.2 (batch lines and their id bound), RFC 8785
for canonical JSON and RFC 6901 for pointers. It ports no other reader. Its agreement with the
vectors under conformance/terraform-file/1.0.0/ is checked by tests/test_terraform_file_vectors.py;
the companion's stable bar is two independently written readers agreeing on every vector (§12).

It reads bytes only. It never runs Terraform, opens no network connection and starts no program. It
holds its own bounds: `maxBytes` before parsing (a stream is read to one byte past it and no
further), a nesting depth of 128 while parsing, the 64-character number bound without writing a
number out, `max` before any value is formed, and the value bound `L` before the `afterUnknown`
pointers of a resource are written.

It is a test reader: its memory grows with `maxBytes`, since it holds the parsed file, and it is not
for production files.

Where the text does not say a form, the reader takes the one named in a comment marked READING. The
text has since settled the readings this reader took on the resource members, the module shape, the
type names, `actions` and the batch's facts bound (§3 step 4, §5, §8), and each now cites it.

    declaration = read_declaration(declaration_bytes)    # raises Malformed
    result = read(file_bytes, declaration)               # Acquired or Refused
    result = read_stream(binary_stream, declaration)
    result = batch(file_bytes, declaration)              # bytes or Refused
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, BinaryIO

FORMAT_TABLE = "1.0.0"
ACCEPTED = {"plan": ("1.0", "1.1", "1.2"), "state": ("1.0",)}  # §4

MAX_BYTES_DEFAULT = 67108864  # §2
MAX_BYTES_LIMIT = 268435456
MAX_DEPTH = 128  # §3 step 2
SELECT_MAX_DEFAULT = 1000  # §5
SELECT_MAX_LIMIT = 10000
TYPES_LIMIT = 64
ADDRESS_PATTERN_LIMIT = 512
ACTIONS = ("create", "update", "delete", "read", "no-op")
NUMBER_LIMIT = 64  # §6
VALUE_LIMIT_CAP = 268435456
VALUE_LIMIT_MULTIPLE = 16
POINTER_CHARGE = 8

ID_LIMIT = 256  # §8, registry §10.2
FACTS_BYTES_LIMIT = 10 * 1024 * 1024  # registry §10.1
FACTS_DEPTH_LIMIT = 128
FACTS_VALUES_LIMIT = 250000
FACTS_STRING_LIMIT = 1024 * 1024

CODES = ("TF-SIZE", "TF-JSON", "TF-FORMAT", "TF-DOCUMENT", "TF-SENSITIVITY", "TF-SELECT-BOUND", "TF-NUMBER",
         "TF-VALUE-LIMIT")
BATCH_CODES = ("FACTS-ID-LIMIT", "FACTS-DOCUMENT-LIMIT")
# §3: each code's message, a fixed text in this reader's own words that holds nothing read from the file.
MESSAGES = {
    "TF-SIZE": "the file is longer than maxBytes",
    "TF-JSON": "the file is not one strict JSON value",
    "TF-FORMAT": "the file's format_version is not in the accepted table for its document",
    "TF-DOCUMENT": "the file is not of its document's shape",
    "TF-SENSITIVITY": "a resource's sensitivity mirror is missing or not of a mirror's form",
    "TF-SELECT-BOUND": "more resources are selected than max",
    "TF-NUMBER": "a number's normal form is longer than 64 characters",
    "TF-VALUE-LIMIT": "the acquired value is over its bound",
    "FACTS-ID-LIMIT": "a selected resource's batch line id is not 1 to 256 bytes",
    "FACTS-DOCUMENT-LIMIT": "a selected resource's facts document is over the facts bound",
}
STREAM_MESSAGE = "the input was read as a stream and is longer than maxBytes"


# ---------------------------------------------------------------------------------------------------
# Results


class Malformed(Exception):
    """§2: a declaration not of its form. No file is read under it."""


class _Refusal(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Refused:
    """§3: a refusal carries its code, the file's sha256, its size and the code's message, and nothing
    else; a stream past `maxBytes` carries the code and a message that it was a stream (step 1)."""
    code: str
    sha256: str | None
    size: int | None
    stream: bool = False

    @property
    def message(self) -> str:
        return STREAM_MESSAGE if self.stream else MESSAGES[self.code]

    def as_json(self) -> dict[str, Any]:
        """The vectors' form, which leaves the message out, since its wording is a reader's own."""
        if self.stream:
            return {"code": self.code, "stream": True}
        return {"code": self.code, "sha256": self.sha256, "bytes": self.size}

    def diagnostic(self) -> dict[str, Any]:
        """The whole diagnostic (§3): the vectors' form and the message."""
        if self.stream:
            return {"code": self.code, "message": self.message}
        return {"bytes": self.size, "code": self.code, "message": self.message, "sha256": self.sha256}


@dataclass(frozen=True)
class Acquired:
    """§§6, 7: the acquired value, and its acquisition record."""
    record: dict[str, Any]
    value: list[dict[str, Any]]

    def value_bytes(self) -> bytes:
        return canonical(self.value).encode("utf-8")


@dataclass(frozen=True)
class Declaration:
    document: str
    types: frozenset[str]
    mode: str
    address: str | None
    actions: frozenset[str] | None
    max: int
    max_bytes: int


# ---------------------------------------------------------------------------------------------------
# JSON (§3 step 2): strict, numbers kept as their decimal text, depth bounded while parsing.


class Number:
    """A JSON number, kept as its literal text."""
    __slots__ = ("text",)

    def __init__(self, text: str) -> None:
        self.text = text

    def __repr__(self) -> str:
        return f"Number({self.text})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Number) and other.text == self.text

    def __hash__(self) -> int:
        return hash(self.text)


class _NotJSON(Exception):
    pass


_WHITE = re.compile(r"[ \t\n\r]*")
_RUN = re.compile(r'[^"\\\x00-\x1f]*')
_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
_HEX4 = re.compile(r"[0-9A-Fa-f]{4}")
_ESCAPES = {'"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}


class _Parser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.at = 0

    def white(self) -> None:
        self.at = _WHITE.match(self.text, self.at).end()

    def value(self, depth: int) -> Any:
        # READING: "nested at most 128 deep (the top-level value at depth 1)" gives every value a depth,
        # the top-level value 1 and a value inside a container one more than the container, scalars
        # included; a value at depth 129 is TF-JSON.
        if depth > MAX_DEPTH:
            raise _NotJSON("too deep")
        text, at = self.text, self.at
        if at >= len(text):
            raise _NotJSON("end of input")
        c = text[at]
        if c == "{":
            return self.object(depth)
        if c == "[":
            return self.array(depth)
        if c == '"':
            return self.string()
        if text.startswith("true", at):
            self.at = at + 4
            return True
        if text.startswith("false", at):
            self.at = at + 5
            return False
        if text.startswith("null", at):
            self.at = at + 4
            return None
        match = _NUMBER.match(text, at)
        if match is None:
            raise _NotJSON("no value")
        self.at = match.end()
        return Number(match.group())

    def object(self, depth: int) -> dict[str, Any]:
        self.at += 1
        members: dict[str, Any] = {}
        self.white()
        if self.text.startswith("}", self.at):
            self.at += 1
            return members
        while True:
            if not self.text.startswith('"', self.at):
                raise _NotJSON("member name")
            name = self.string()
            if name in members:
                raise _NotJSON("duplicate member name")
            self.white()
            if not self.text.startswith(":", self.at):
                raise _NotJSON("colon")
            self.at += 1
            self.white()
            members[name] = self.value(depth + 1)
            self.white()
            if self.text.startswith(",", self.at):
                self.at += 1
                self.white()
                continue
            if self.text.startswith("}", self.at):
                self.at += 1
                return members
            raise _NotJSON("object")

    def array(self, depth: int) -> list[Any]:
        self.at += 1
        items: list[Any] = []
        self.white()
        if self.text.startswith("]", self.at):
            self.at += 1
            return items
        while True:
            items.append(self.value(depth + 1))
            self.white()
            if self.text.startswith(",", self.at):
                self.at += 1
                self.white()
                continue
            if self.text.startswith("]", self.at):
                self.at += 1
                return items
            raise _NotJSON("array")

    def string(self) -> str:
        text = self.text
        at = self.at + 1
        parts: list[str] = []
        while True:
            run = _RUN.match(text, at)
            parts.append(run.group())
            at = run.end()
            if at >= len(text):
                raise _NotJSON("unterminated string")
            c = text[at]
            if c == '"':
                self.at = at + 1
                return "".join(parts)
            if c != "\\":
                raise _NotJSON("control character in a string")
            e = text[at + 1:at + 2]
            if e in _ESCAPES:
                parts.append(_ESCAPES[e])
                at += 2
                continue
            if e != "u" or not _HEX4.fullmatch(text, at + 2, at + 6):
                raise _NotJSON("escape")
            unit = int(text[at + 2:at + 6], 16)
            at += 6
            if 0xDC00 <= unit <= 0xDFFF:
                raise _NotJSON("lone surrogate escape")
            if 0xD800 <= unit <= 0xDBFF:
                if not (text.startswith("\\u", at) and _HEX4.fullmatch(text, at + 2, at + 6)):
                    raise _NotJSON("lone surrogate escape")
                low = int(text[at + 2:at + 6], 16)
                if not 0xDC00 <= low <= 0xDFFF:
                    raise _NotJSON("lone surrogate escape")
                at += 6
                parts.append(chr(0x10000 + ((unit - 0xD800) << 10) + (low - 0xDC00)))
                continue
            parts.append(chr(unit))


def parse_json(data: bytes) -> Any:
    """§3 step 2: UTF-8 with no byte-order mark and no lone surrogate escape, one JSON value with only
    white space after it, nested at most 128 deep, with no duplicate member name. Raises _NotJSON."""
    if data.startswith(b"\xef\xbb\xbf"):
        raise _NotJSON("byte-order mark")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise _NotJSON("not UTF-8") from error
    parser = _Parser(text)
    parser.white()
    value = parser.value(1)
    parser.white()
    if parser.at != len(text):
        raise _NotJSON("bytes after the value")
    return value


# ---------------------------------------------------------------------------------------------------
# The declaration (§§2, 5)


_INTEGER = re.compile(r"-?(?:0|[1-9][0-9]*)")


def _integer(value: Any, low: int, high: int) -> int:
    # §1: an integer's literal has no fraction and no exponent.
    if not isinstance(value, Number) or not _INTEGER.fullmatch(value.text):
        raise Malformed("not an integer")
    digits = value.text.lstrip("-")
    if len(digits) > len(str(high)):
        raise Malformed("out of range")
    number = int(value.text)
    if not low <= number <= high:
        raise Malformed("out of range")
    return number


def check_declaration(value: Any) -> Declaration:
    """§2 and §5: a declaration has exactly `document`, `select` and optional `maxBytes`."""
    if not isinstance(value, dict):
        raise Malformed("not an object")
    if not {"document", "select"} <= set(value) <= {"document", "select", "maxBytes"}:
        raise Malformed("members")
    document = value["document"]
    if not isinstance(document, str) or document not in ("plan", "state"):
        raise Malformed("document")
    max_bytes = _integer(value["maxBytes"], 1, MAX_BYTES_LIMIT) if "maxBytes" in value else MAX_BYTES_DEFAULT
    select = value["select"]
    # READING: §5 lists `select`'s members; a member it does not list makes `select` malformed (a vector
    # holds this).
    if not isinstance(select, dict) or not {"types"} <= set(select) <= {"types", "mode", "address", "actions", "max"}:
        raise Malformed("select")
    types = select["types"]
    # §5: a non-empty array of at most 64 distinct names, each a non-empty string.
    if not (isinstance(types, list) and 1 <= len(types) <= TYPES_LIMIT
            and all(isinstance(t, str) and t for t in types) and len(set(types)) == len(types)):
        raise Malformed("types")
    mode = select.get("mode", "managed")
    if not isinstance(mode, str) or mode not in ("managed", "data"):
        raise Malformed("mode")
    address = select.get("address")
    if "address" in select and not (isinstance(address, str) and len(address) <= ADDRESS_PATTERN_LIMIT):
        raise Malformed("address")
    actions = None
    if "actions" in select:
        if document != "plan":
            raise Malformed("actions on a state")
        # §5: an array of names from the five, possibly empty (it then keeps no change), read as a set.
        listed = select["actions"]
        if not (isinstance(listed, list) and all(isinstance(a, str) and a in ACTIONS for a in listed)):
            raise Malformed("actions")
        actions = frozenset(listed)
    maximum = _integer(select["max"], 1, SELECT_MAX_LIMIT) if "max" in select else SELECT_MAX_DEFAULT
    return Declaration(document, frozenset(types), mode, address, actions, maximum, max_bytes)


def read_declaration(data: bytes) -> Declaration:
    try:
        value = parse_json(data)
    except _NotJSON as error:
        raise Malformed("not JSON") from error
    return check_declaration(value)


# ---------------------------------------------------------------------------------------------------
# Mirrors (§3 steps 4-6)


def _is_mirror(value: Any) -> bool:
    """`true`, `false`, or an object or array of mirrors. Depth is bounded by the parse."""
    if value is True or value is False:
        return True
    if isinstance(value, dict):
        return all(_is_mirror(v) for v in value.values())
    if isinstance(value, list):
        return all(_is_mirror(v) for v in value)
    return False


def _marks(mirror: Any) -> bool:
    """Whether a mirror marks any position `true`, at any depth."""
    if mirror is True:
        return True
    if isinstance(mirror, dict):
        return any(_marks(v) for v in mirror.values())
    if isinstance(mirror, list):
        return any(_marks(v) for v in mirror)
    return False


_INDEX = re.compile(r"0|[1-9][0-9]*")


def _mirror_children(mirror: Any) -> list[tuple[str, Any]]:
    """A mirror's positions one level down, each with its RFC 6901 token."""
    if isinstance(mirror, dict):
        return list(mirror.items())
    if isinstance(mirror, list):
        return [(str(k), m) for k, m in enumerate(mirror)]
    return []


def _value_child(value: Any, mirror: Any, token: str) -> tuple[bool, Any]:
    """The value position a mirror position names (§3 step 6), matched as RFC 6901 tokens are: a mirror
    member names the value's member of that name, or, over an array, the element its name indexes; a
    mirror array's element k names an array's element k, or an object's member named k in decimal."""
    if isinstance(value, dict):
        return (True, value[token]) if token in value else (False, None)
    if isinstance(value, list):
        if _INDEX.fullmatch(token) and (len(token) <= len(str(len(value)))) and int(token) < len(value):
            return True, value[int(token)]
        return False, None
    return False, None


_REMOVE = object()


def _remove(value: Any, mirror: Any, path: tuple[str, ...], removed: list[tuple[str, ...]]) -> tuple[Any, int]:
    """§3 step 6 on one position: the value with what its mirror marks removed, and the count of object
    members removed in it, or _REMOVE when this position itself is to be removed. An array element is never
    removed alone: its array is removed instead, up to the nearest object member. `removed` collects the
    paths of the object members removed (a removal inside a removed value is not collected)."""
    if mirror is True:
        return _REMOVE, 0
    if mirror is False:
        return value, 0
    if not isinstance(value, (dict, list)):
        # A mirror object or array over a string, number, boolean or null removes that value when it marks
        # any position true, at any depth; an empty one, or one that marks nothing, removes nothing.
        return (_REMOVE, 0) if _marks(mirror) else (value, 0)
    if isinstance(value, dict):
        named: dict[str, Any] = {}
        for token, sub in _mirror_children(mirror):
            if token in value:
                named[token] = sub
        kept: dict[str, Any] = {}
        count = 0
        inner: list[tuple[str, ...]] = []
        for name, member in value.items():
            if name not in named:
                kept[name] = member
                continue
            result, n = _remove(member, named[name], path + (name,), inner)
            if result is _REMOVE:
                count += 1
                inner.append(path + (name,))
            else:
                kept[name] = result
                count += n
        removed.extend(inner)
        return kept, count
    # An array.
    by_index: dict[int, Any] = {}
    for token, sub in _mirror_children(mirror):
        found, _ = _value_child(value, mirror, token)
        if found:
            by_index[int(token)] = sub
    items: list[Any] = []
    count = 0
    inner = []
    for k, element in enumerate(value):
        if k not in by_index:
            items.append(element)
            continue
        result, n = _remove(element, by_index[k], path + (str(k),), inner)
        if result is _REMOVE:
            return _REMOVE, 0
        items.append(result)
        count += n
    removed.extend(inner)
    return items, count


def remove_sensitive(value: Any, mirror: Any) -> tuple[bool, Any, int, list[tuple[str, ...]]]:
    """A `values`, `before` or `after` and its mirror: whether it is kept, what is kept, the count of
    removals (one for the value removed whole) and the removed paths ((), the whole, when removed whole)."""
    removed: list[tuple[str, ...]] = []
    result, count = _remove(value, mirror, (), removed)
    if result is _REMOVE:
        return False, None, 1, [()]
    return True, result, count, removed


def _lacked_marks(value: Any, present: bool, mirror: Any, path: tuple[str, ...], out: list[tuple[str, ...]]) -> None:
    """The positions `after_sensitive` marks true that `after` lacks (§3 step 6)."""
    if mirror is True:
        if not present:
            out.append(path)
        return
    if mirror is False:
        return
    if present and not isinstance(value, (dict, list)):
        # A marking mirror over a scalar removes the scalar, and every pointer at or below it is dropped.
        return
    for token, sub in _mirror_children(mirror):
        if present:
            found, child = _value_child(value, mirror, token)
        else:
            found, child = False, None
        _lacked_marks(child, found, sub, path + (token,), out)


class _Trie:
    __slots__ = ("children", "end")

    def __init__(self) -> None:
        self.children: dict[str, _Trie] = {}
        self.end = False

    @classmethod
    def of(cls, paths: list[tuple[str, ...]]) -> "_Trie":
        root = cls()
        for path in paths:
            node = root
            for token in path:
                node = node.children.setdefault(token, cls())
            node.end = True
        return root


def _escape_token(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


class _OverBudget(Exception):
    pass


def _walk_unknown(mirror: Any, removed: _Trie | None, cut: _Trie | None, length: int,
                  emit: Any) -> None:
    """The `afterUnknown` pointers of one resource (§3 step 6, §6): the positions `after_unknown` marks
    true, less those at or below a removed position, and with those at or below a position
    `after_sensitive` marks true and `after` lacks cut at it, the pointers cut at one position being one.
    `emit(tokens_or_None, length)` is called once per pointer with its RFC 6901 form's length in bytes."""
    stack: list[tuple[Any, _Trie | None, _Trie | None, int, tuple[str, ...]]] = [(mirror, removed, cut, length, ())]
    while stack:
        node, rem, cut_node, size, path = stack.pop()
        if rem is not None and rem.end:
            continue
        if cut_node is not None and cut_node.end:
            if _marks(node):
                emit(path, size)
            continue
        if node is True:
            emit(path, size)
            continue
        for token, sub in reversed(_mirror_children(node)):
            stack.append((sub, rem.children.get(token) if rem is not None else None,
                          cut_node.children.get(token) if cut_node is not None else None,
                          size + 1 + len(_escape_token(token).encode("utf-8")), path + (token,)))


# ---------------------------------------------------------------------------------------------------
# Numbers (§6, registry §10.1)


def normal_form(literal: str) -> str | None:
    """The registry companion's normal form of a JSON number literal, `0` for every zero, or None when it
    would be longer than 64 characters. Its length is found before it is written."""
    negative = literal.startswith("-")
    body = literal[1:] if negative else literal
    mantissa, exponent = re.split("[eE]", body, maxsplit=1) if ("e" in body or "E" in body) else (body, "0")
    whole, _, fraction = mantissa.partition(".")
    digits = (whole + fraction).lstrip("0")
    if not digits:
        return "0"
    sign = -1 if exponent.startswith("-") else 1
    magnitude = exponent.lstrip("+-").lstrip("0") or "0"
    if len(magnitude) > 15:
        # |exponent| >= 10**15 while the literal has fewer than 2**28 digits: either way the normal form
        # has more than 64 characters.
        return None
    significant = digits.rstrip("0")
    scale = sign * int(magnitude) - len(fraction) + (len(digits) - len(significant))
    sign_text = "-" if negative else ""
    if scale >= 0:
        size = len(sign_text) + len(significant) + scale
        if size > NUMBER_LIMIT:
            return None
        return sign_text + significant + "0" * scale
    places = -scale
    if len(significant) > places:
        size = len(sign_text) + len(significant) + 1
        if size > NUMBER_LIMIT:
            return None
        return sign_text + significant[:-places] + "." + significant[-places:]
    size = len(sign_text) + 2 + places
    if size > NUMBER_LIMIT:
        return None
    return sign_text + "0." + "0" * (places - len(significant)) + significant


def _decimal(value: Any) -> Any:
    """§6: numbers become decimal strings in normal form; one too long is TF-NUMBER."""
    if isinstance(value, Number):
        written = normal_form(value.text)
        if written is None:
            raise _Refusal("TF-NUMBER")
        return written
    if isinstance(value, dict):
        return {name: _decimal(member) for name, member in value.items()}
    if isinstance(value, list):
        return [_decimal(item) for item in value]
    return value


# ---------------------------------------------------------------------------------------------------
# Canonical form (RFC 8785) of a value that holds no number


_CONTROL = {"\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f", "\r": "\\r", '"': '\\"', "\\": "\\\\"}
_NEEDS_ESCAPE = re.compile(r'["\\\x00-\x1f]')


def _string(text: str) -> str:
    def escape(match: re.Match[str]) -> str:
        c = match.group()
        return _CONTROL.get(c) or "\\u%04x" % ord(c)
    return '"' + _NEEDS_ESCAPE.sub(escape, text) + '"'


def canonical(value: Any) -> str:
    """RFC 8785 for strings, booleans, null, arrays, objects and non-negative integers."""
    parts: list[str] = []
    _canonical(value, parts)
    return "".join(parts)


def _canonical(value: Any, parts: list[str]) -> None:
    if value is True:
        parts.append("true")
    elif value is False:
        parts.append("false")
    elif value is None:
        parts.append("null")
    elif isinstance(value, str):
        parts.append(_string(value))
    elif isinstance(value, int):
        parts.append(str(value))
    elif isinstance(value, dict):
        parts.append("{")
        for i, name in enumerate(sorted(value, key=lambda n: n.encode("utf-16-be"))):
            if i:
                parts.append(",")
            parts.append(_string(name))
            parts.append(":")
            _canonical(value[name], parts)
        parts.append("}")
    elif isinstance(value, list):
        parts.append("[")
        for i, item in enumerate(value):
            if i:
                parts.append(",")
            _canonical(item, parts)
        parts.append("]")
    else:
        raise TypeError(f"no canonical form for {value!r}")


# ---------------------------------------------------------------------------------------------------
# Selection (§5)


def address_matches(pattern: str, address: str) -> bool:
    """`*` matches any run of characters other than `.`, `[` and `]`, and every other character matches
    itself; the pattern matches the whole address. A set of pattern positions is advanced one character
    at a time, so no input backtracks.
    READING: a run may be empty (a vector holds this)."""
    stars = 0
    literal: dict[str, int] = {}
    for i, c in enumerate(pattern):
        if c == "*":
            stars |= 1 << i
        else:
            literal[c] = literal.get(c, 0) | 1 << i

    def closure(states: int) -> int:
        while True:
            more = states | ((states & stars) << 1)
            if more == states:
                return states
            states = more

    states = closure(1)
    for c in address:
        step = (states & literal.get(c, 0)) << 1
        if c not in ".[]":
            step |= states & stars
        states = closure(step)
        if not states:
            return False
    return bool(states >> len(pattern) & 1)


# ---------------------------------------------------------------------------------------------------
# The reading (§3)


_IDENTITY = (("address", "address"), ("type", "type"), ("name", "name"), ("mode", "mode"),
             ("provider_name", "providerName"))


@dataclass
class _Resource:
    item: dict[str, Any]
    id: str
    deposed: str | None
    # Filled by step 6.
    kept: dict[str, tuple[bool, Any]] | None = None
    removed_after: list[tuple[str, ...]] | None = None
    lacked: list[tuple[str, ...]] | None = None


def _deposed_key(item: dict[str, Any], member: str) -> str | None:
    if member not in item:
        return None
    key = item[member]
    if not isinstance(key, str) or not key:
        raise _Refusal("TF-DOCUMENT")
    return key


def _identity(item: dict[str, Any]) -> None:
    # §3 step 4: `address`, `type`, `name`, `mode` and `provider_name` are strings, which may be empty and
    # are not checked against one another; `index`, when present, is a string or a number.
    for member, _ in _IDENTITY:
        if not isinstance(item.get(member), str):
            raise _Refusal("TF-DOCUMENT")
    if "index" in item and not isinstance(item["index"], (str, Number)):
        raise _Refusal("TF-DOCUMENT")


def _state_resources(values: Any) -> list[dict[str, Any]]:
    """Every resource under `values.root_module` and its `child_modules`, recursively.
    §3 step 4: a module, when present, is an object, which needs no `address`; its `resources`, when
    present, is an array of objects, and its `child_modules`, when present, an array of modules."""
    found: list[dict[str, Any]] = []
    if "root_module" not in values:
        return found
    modules = [values["root_module"]]
    while modules:
        module = modules.pop()
        if not isinstance(module, dict):
            raise _Refusal("TF-DOCUMENT")
        resources = module.get("resources", [])
        children = module.get("child_modules", [])
        if not isinstance(resources, list) or not isinstance(children, list):
            raise _Refusal("TF-DOCUMENT")
        for resource in resources:
            if not isinstance(resource, dict):
                raise _Refusal("TF-DOCUMENT")
            found.append(resource)
        modules.extend(reversed(children))
    return found


def _read_section(top: dict[str, Any], document: str) -> list[_Resource]:
    """§3 step 4: the document's shape, and the read section of step 5."""
    section: list[_Resource] = []
    if document == "plan":
        if not isinstance(top.get("planned_values"), dict):
            raise _Refusal("TF-DOCUMENT")
        changes = top.get("resource_changes", [])
        if not isinstance(changes, list):
            raise _Refusal("TF-DOCUMENT")
        for item in changes:
            if not isinstance(item, dict) or not isinstance(item.get("change"), dict):
                raise _Refusal("TF-DOCUMENT")
            change = item["change"]
            actions = change.get("actions")
            if not isinstance(actions, list) or not all(isinstance(a, str) for a in actions):
                raise _Refusal("TF-DOCUMENT")
            if "after_unknown" in change and not _is_mirror(change["after_unknown"]):
                raise _Refusal("TF-DOCUMENT")
            _identity(item)
            key = _deposed_key(item, "deposed")
            section.append(_Resource(item, _id(item["address"], key), key))
    else:
        if "planned_values" in top or "resource_changes" in top:
            raise _Refusal("TF-DOCUMENT")
        values = top.get("values", {})
        if not isinstance(values, dict):
            raise _Refusal("TF-DOCUMENT")
        for item in _state_resources(values):
            _identity(item)
            key = _deposed_key(item, "deposed_key")
            section.append(_Resource(item, _id(item["address"], key), key))
    ids = [resource.id for resource in section]
    if len(set(ids)) != len(ids):
        raise _Refusal("TF-DOCUMENT")
    return section


def _id(address: str, deposed: str | None) -> str:
    return address if deposed is None else address + " deposed " + deposed


def _mirrors_of(resource: _Resource, document: str) -> list[tuple[str, str]]:
    """Each value a resource carries and the member of its sensitivity mirror."""
    if document == "plan":
        return [("before", "before_sensitive"), ("after", "after_sensitive")]
    return [("values", "sensitive_values")]


def _holder(resource: _Resource, document: str) -> dict[str, Any]:
    return resource.item["change"] if document == "plan" else resource.item


def _check_sensitivity(section: list[_Resource], document: str) -> None:
    """§3 step 5: every resource of the read section carries its mirror."""
    for resource in section:
        holder = _holder(resource, document)
        for _, mirror in _mirrors_of(resource, document):
            if mirror not in holder or not _is_mirror(holder[mirror]):
                raise _Refusal("TF-SENSITIVITY")


def _remove_all(section: list[_Resource], document: str) -> int:
    """§3 step 6 over the whole read section; returns removedSensitive."""
    total = 0
    for resource in section:
        holder = _holder(resource, document)
        resource.kept = {}
        for member, mirror_member in _mirrors_of(resource, document):
            if member not in holder:
                resource.kept[member] = (False, None)
                if member == "after":
                    resource.removed_after = []
                    resource.lacked = []
                    _lacked_marks(None, False, holder[mirror_member], (), resource.lacked)
                continue
            kept, value, count, removed = remove_sensitive(holder[member], holder[mirror_member])
            resource.kept[member] = (kept, value)
            total += count
            if member == "after":
                resource.removed_after = removed
                resource.lacked = []
                _lacked_marks(holder[member], True, holder[mirror_member], (), resource.lacked)
    return total


def _selects(resource: _Resource, declaration: Declaration) -> bool:
    item = resource.item
    if item["type"] not in declaration.types or item["mode"] != declaration.mode:
        return False
    if declaration.address is not None and not address_matches(declaration.address, item["address"]):
        return False
    if declaration.actions is not None:
        if not any(action in declaration.actions for action in item["change"]["actions"]):
            return False
    return True


def _object_of(resource: _Resource, document: str) -> dict[str, Any]:
    """§6: the resource's object, without `afterUnknown` (added under the value bound)."""
    item = resource.item
    out: dict[str, Any] = {target: item[source] for source, target in _IDENTITY}
    if "index" in item:
        out["index"] = _decimal(item["index"])
    if resource.deposed is not None:
        out["deposed"] = resource.deposed
    assert resource.kept is not None
    if document == "plan":
        out["actions"] = list(item["change"]["actions"])
        for member in ("before", "after"):
            kept, value = resource.kept[member]
            if kept:
                out[member] = _decimal(value)
    else:
        kept, value = resource.kept["values"]
        if kept:
            out["values"] = _decimal(value)
    return out


def _pointers(resource: _Resource, budget: int) -> list[str]:
    """§6: the sorted `afterUnknown` pointers of one plan resource. Each is charged the length in bytes of
    its RFC 6901 form and eight bytes more; a total over `budget` is TF-VALUE-LIMIT, found before any
    pointer is written."""
    change = resource.item["change"]
    if "after_unknown" not in change:
        return []
    removed = _Trie.of(resource.removed_after or [])
    cut = _Trie.of(resource.lacked or [])
    charged = 0
    found: list[tuple[str, ...]] = []

    def charge(path: tuple[str, ...], size: int) -> None:
        nonlocal charged
        charged += size + POINTER_CHARGE
        if charged > budget:
            raise _Refusal("TF-VALUE-LIMIT")
        found.append(path)

    _walk_unknown(change["after_unknown"], removed, cut, 0, charge)
    pointers = {"".join("/" + _escape_token(t) for t in path) for path in found}
    return sorted(pointers)


def _value(section: list[_Resource], document: str, declaration: Declaration, size: int) -> list[dict[str, Any]]:
    """§3 step 7: selection (§5), then the acquired value (§6), in the order of their refusals:
    TF-SELECT-BOUND, then TF-NUMBER, then TF-VALUE-LIMIT."""
    selected = [resource for resource in section if _selects(resource, declaration)]
    if len(selected) > declaration.max:
        raise _Refusal("TF-SELECT-BOUND")
    selected.sort(key=lambda resource: resource.id)
    objects = [_object_of(resource, document) for resource in selected]
    limit = min(VALUE_LIMIT_CAP, VALUE_LIMIT_MULTIPLE * size)
    before = 1  # the array's opening "["
    value: list[dict[str, Any]] = []
    for resource, obj in zip(selected, objects):
        if document == "plan":
            obj["afterUnknown"] = _pointers(resource, limit - before)
        written = len(canonical(obj).encode("utf-8"))
        before += written + 1  # the object, and the comma after it
        if before > limit:
            raise _Refusal("TF-VALUE-LIMIT")
        value.append(obj)
    total = 2 if not value else before
    if total > limit:
        raise _Refusal("TF-VALUE-LIMIT")
    return value


def _read(data: bytes, declaration: Declaration) -> tuple[Acquired, str]:
    """§3 steps 2 to 7 on bytes within `maxBytes`. Raises _Refusal."""
    try:
        top = parse_json(data)
    except _NotJSON as error:
        raise _Refusal("TF-JSON") from error
    document = declaration.document
    if not isinstance(top, dict):
        raise _Refusal("TF-FORMAT")
    version = top.get("format_version")
    if not isinstance(version, str) or version not in ACCEPTED[document]:
        raise _Refusal("TF-FORMAT")
    section = _read_section(top, document)
    _check_sensitivity(section, document)
    removed = _remove_all(section, document)
    value = _value(section, document, declaration, len(data))
    record = {"kind": "terraform-file", "document": document, "formatVersion": version, "formatTable": FORMAT_TABLE,
              "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "removedSensitive": removed,
              "selected": len(value)}
    return Acquired(record, value), version


def read(data: bytes, declaration: Declaration) -> Acquired | Refused:
    """A file whose whole length is read (§3 step 1)."""
    digest, size = hashlib.sha256(data).hexdigest(), len(data)
    if size > declaration.max_bytes:
        return Refused("TF-SIZE", digest, size)
    try:
        return _read(data, declaration)[0]
    except _Refusal as refusal:
        return Refused(refusal.code, digest, size)


def take_stream(stream: BinaryIO, max_bytes: int) -> bytes | None:
    """An input read as a stream, read to at most `maxBytes` and one byte more: None when it is longer."""
    chunks: list[bytes] = []
    remaining = max_bytes + 1
    while remaining > 0:
        chunk = stream.read(min(remaining, 1 << 20))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    if remaining <= 0:
        return None
    return b"".join(chunks)


def read_stream(stream: BinaryIO, declaration: Declaration) -> Acquired | Refused:
    """An input read as a stream (§3 step 1): past `maxBytes` it is TF-SIZE with no sha256 and no size."""
    data = take_stream(stream, declaration.max_bytes)
    if data is None:
        return Refused("TF-SIZE", None, None, stream=True)
    return read(data, declaration)


# ---------------------------------------------------------------------------------------------------
# The batch (§8)


def _facts_within_bound(facts: dict[str, Any]) -> bool:
    """The registry companion's facts bound (its §10.1): JCS bytes at most 10 MiB, nesting at most 128 deep
    counting containers (the root at depth 1, as its §2.2 counts), at most 250 000 values, and no string
    over 1 MiB in UTF-8."""
    values = 0
    stack: list[tuple[Any, int]] = [(facts, 1)]
    while stack:
        value, depth = stack.pop()
        values += 1
        if values > FACTS_VALUES_LIMIT:
            return False
        if isinstance(value, str):
            if len(value.encode("utf-8")) > FACTS_STRING_LIMIT:
                return False
        elif isinstance(value, dict):
            if depth > FACTS_DEPTH_LIMIT:
                return False
            for name, member in value.items():
                # READING: a member name is a string the document holds.
                if len(name.encode("utf-8")) > FACTS_STRING_LIMIT:
                    return False
                stack.append((member, depth + 1))
        elif isinstance(value, list):
            if depth > FACTS_DEPTH_LIMIT:
                return False
            stack.extend((item, depth + 1) for item in value)
    return len(canonical(facts).encode("utf-8")) <= FACTS_BYTES_LIMIT


def batch(data: bytes, declaration: Declaration) -> bytes | Refused:
    """§8: one line per selected resource, the JCS bytes of {"facts", "id"} and a line feed (registry
    §10.2). Every selected resource's id is checked for 1 to 256 bytes of UTF-8 before any facts document
    is held to the facts bound, and either refusal refuses the whole run before any line is written.
    A facts document over the bound refuses the run with FACTS-DOCUMENT-LIMIT, carrying what FACTS-ID-LIMIT
    carries."""
    result = read(data, declaration)
    if isinstance(result, Refused):
        return result
    digest, size = result.record["sha256"], result.record["bytes"]
    ids = [_id(obj["address"], obj.get("deposed")) for obj in result.value]
    if any(not 1 <= len(i.encode("utf-8")) <= ID_LIMIT for i in ids):
        return Refused("FACTS-ID-LIMIT", digest, size)
    terraform = {"document": result.record["document"], "formatVersion": result.record["formatVersion"],
                 "sha256": digest}
    lines: list[str] = []
    for i, obj in zip(ids, result.value):
        facts = {"terraform": terraform, "resource": obj}
        if not _facts_within_bound(facts):
            return Refused("FACTS-DOCUMENT-LIMIT", digest, size)
        lines.append(canonical({"facts": facts, "id": i}) + "\n")
    return "".join(lines).encode("utf-8")

#!/usr/bin/env python3
"""Writes the staged vectors of the proposed dialect format 4.1.0, a paged `operation` source (RFC 0033,
in Review), under conformance/dialect/format-4.1/: one directory per row of the RFC's Conformance table,
and manifest.json.

    python3 tools/paged_source_vectors.py [--check]

Every expected answer is written here by hand, from the RFC's Specification, before the reader is run:
each refusal and finding, and of each reading its facts, each paged source's `paging`, the order of
`cites` and the outcome's status. The requests, the receipts and their signatures are formed here, under
RFC 8032 section 7.1 TEST 1's published seed, on this script's own request forming (RFC 0033 section 3),
not the reader's. The reader (tools/dialect_verify.py) is used for the two canonical forms and the Ed25519
arithmetic, and to compute each reading's preparation.json, which is then held to the hand-written
expectations; the script stops at the first disagreement. With --check it writes nothing and exits 1 when
a file it would write differs from the one on disk.
"""

from __future__ import annotations

import base64
import contextlib
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterator

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "conformance" / "dialect" / "format-4.1"
_SPEC = importlib.util.spec_from_file_location("dialect_verify_for_paged_vectors", ROOT / "tools" / "dialect_verify.py")
assert _SPEC is not None and _SPEC.loader is not None
READER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = READER
_SPEC.loader.exec_module(READER)

SEED = "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
PUBLIC = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
VERIFIED_AT = "2026-11-15T12:00:00Z"
SERVED = "2026-11-15T11:59:00Z"
STALE = "2026-11-15T11:50:00Z"  # 600 seconds before verifiedAt, over maxAge 300
ID = "urn:judgmentpack:dialect:paged-vectors"
S1, S2, S3 = "paged.session.1", "paged.session.2", "paged.session.3"
UNREAD = {"refusal": "version-unread", "result": "refusal"}


class Literal(str):
    """A number written as its literal, such as `1e3`."""


# --- Ed25519 under the published seed (RFC 8032, 5.1.5 and 5.1.6) ------------------------------------

_H = hashlib.sha512(bytes.fromhex(SEED)).digest()
_A = int.from_bytes(_H[:32], "little") & ((1 << 254) - 8) | (1 << 254)
_PUBLIC = READER._encode(READER._multiply(_A, READER.BASE))
assert _PUBLIC.hex() == PUBLIC


def sign(message: bytes) -> str:
    r = int.from_bytes(hashlib.sha512(_H[32:] + message).digest(), "little") % READER.L
    encoded_r = READER._encode(READER._multiply(r, READER.BASE))
    k = int.from_bytes(hashlib.sha512(encoded_r + _PUBLIC + message).digest(), "little") % READER.L
    return (encoded_r + ((r + k * _A) % READER.L).to_bytes(32, "little")).hex()


def text(value: Any, indent: int | None = None) -> str:
    """JSON text, a Literal written as its literal."""
    marked = json.dumps(value, indent=indent, ensure_ascii=False,
                        default=None, cls=_Marked)
    return marked.replace('"\\u0000', "").replace('\\u0000"', "")


class _Marked(json.JSONEncoder):
    def encode(self, o: Any) -> str:
        return super().encode(_mark(o))


def _mark(value: Any) -> Any:
    if isinstance(value, Literal):
        return "\u0000" + str(value) + "\u0000"
    if isinstance(value, dict):
        return {k: _mark(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_mark(v) for v in value]
    return value


def canon_of(value: Any) -> bytes:
    return READER.canon(READER.read_document(text(value).encode("utf-8"), "a value"))


def digest(value: Any) -> str:
    return READER.digest_of(canon_of(value))


# --- Profiles ------------------------------------------------------------------------------------------

ADAPTER_DIGEST = "sha256:" + hashlib.sha256(b"stand-in adapter").hexdigest()
FEED = {"id": "feed", "publicKey": PUBLIC, "class": "record", "source": "changes/feed", "authority": "test",
        "shape": "mcp", "adapter": {"name": "adapter-mcp", "version": "stand-in", "digest": ADAPTER_DIGEST},
        "endpoint": "stdio:change-feed", "tools": ["list-changes", "get-record"]}
WEB = {"id": "web", "publicKey": PUBLIC, "class": "record", "source": "records/web", "authority": "test",
       "shape": "http", "adapter": {"name": "adapter-http", "version": "stand-in", "digest": ADAPTER_DIGEST},
       "endpoint": "https://records.example.test"}
CONNECTION = {"id": "connection", "publicKey": PUBLIC, "class": "record", "source": "records/connection",
              "authority": "test", "shape": "http",
              "adapter": {"name": "adapter-connection", "version": "stand-in", "digest": ADAPTER_DIGEST},
              "endpoint": None}
PROFILES = [FEED, WEB, CONNECTION]
BY_ID = {p["id"]: p for p in PROFILES}
# a research profile (§4.3, §5.1), given beside the three to the one row that declares a `research` source
MODEL = "synthetic-research-model-1"
ASSISTANT = {"id": "assistant", "publicKey": PUBLIC, "class": "generated", "source": "research/answers",
             "authority": "test", "shape": "http",
             "adapter": {"name": "adapter-sources", "version": "stand-in", "digest": ADAPTER_DIGEST},
             "endpoint": "https://answers.example.test", "research": {"capabilities": ["answer"], "model": MODEL}}

# --- Requests (RFC 0033 section 3, formed here) --------------------------------------------------------


def instantiate(template: Any, values: dict[str, Any]) -> Any:
    if isinstance(template, dict):
        if set(template) == {"$param"}:
            return values[template["$param"]]
        return {k: instantiate(v, values) for k, v in template.items()}
    if isinstance(template, list):
        return [instantiate(v, values) for v in template]
    return template


def formed(first: dict[str, Any], fills: str, reference: str) -> dict[str, Any]:
    """The first request with the member at `fills` set to the reference: replaced or added."""
    request = copy.deepcopy(first)
    tokens = fills[1:].split("/")
    current = request
    for token in tokens[:-1]:
        current = current[token]
    current[tokens[-1]] = reference
    return request


_salts = [0]
_salt_label = [""]


def salt() -> str:
    _salts[0] += 1
    return hashlib.sha256(f"paged-vectors salt {_salt_label[0]}{_salts[0]}".encode()).hexdigest()


@contextlib.contextmanager
def salts_apart(label: str) -> Iterator[None]:
    """Salts of their own for a row added after the first staging, so that no earlier vector's bytes move."""
    held = (_salts[0], _salt_label[0])
    _salts[0], _salt_label[0] = 0, label + " "
    try:
        yield
    finally:
        _salts[0], _salt_label[0] = held


def page(profile: dict[str, Any], request: Any, result: Any, session: str, index: int, prev: str | None,
         at: str = SERVED, change: Callable[[dict[str, Any]], None] | None = None, corrupt: bool = False,
         asked: Any = None) -> dict[str, Any]:
    """One page: the result, its receipt signed under the seed, its salts. `asked`, when given, is the request
    the receipt commits in place of `request`; `change` alters the receipt before it is signed; `corrupt`
    flips the signature's last byte after."""
    args_salt = salt()
    receipt = {
        "acquisition": {"adapter": profile["adapter"], "endpoint": profile["endpoint"], "observedAt": at,
                        "peerIdentity": None, "schema": None, "shape": profile["shape"], "snapshot": "paged",
                        "statement": None, "upstreamToken": None},
        "argumentsCommitment": "sha256:" + hashlib.sha256(
            bytes.fromhex(args_salt) + b"args:" + canon_of(request if asked is None else asked)).hexdigest(),
        "authority": profile["authority"],
        "callIndex": index,
        "caller": None,
        "keyId": hashlib.sha256(bytes.fromhex(PUBLIC)).hexdigest()[:32],
        "kind": "acquisition",
        "prevSignature": prev,
        "receiptVersion": "3",
        "resultDigest": digest(result),
        "servedAt": at,
        "sessionId": session,
        "source": profile["source"],
    }
    if change is not None:
        change(receipt)
    receipt["signature"] = sign(b"judgment-pack-gateway/receipt/3:" + canon_of(receipt))
    if corrupt:
        receipt["signature"] = receipt["signature"][:-2] + ("00" if receipt["signature"][-2:] != "00" else "01")
    return {"result": result, "receipt": receipt, "salts": {"args": args_salt}}


def pages(profile: dict[str, Any], first: Any, fills: str, results: list[Any], session: str = S1,
          next_of: Callable[[Any], Any] = lambda r: r.get("next"), start: int = 0, prev: str | None = None,
          per_page: dict[int, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """A session's pages in call order, page i asked with the reference page i-1 named. `per_page` gives
    page()'s keyword arguments for a page by its position."""
    out: list[dict[str, Any]] = []
    for i, result in enumerate(results):
        request = first if i == 0 else formed(first, fills, next_of(results[i - 1]))
        options = dict((per_page or {}).get(i, {}))
        index = options.pop("index", start + i)
        made = page(profile, request, result, options.pop("session", session), index,
                    options.pop("prev", prev if i == 0 else out[-1]["receipt"]["signature"]), **options)
        out.append(made)
    return out


# --- Dialects ------------------------------------------------------------------------------------------

COPY = {"copy": {"facts": [{"target": "/changes/end", "source": "/end"},
                           {"target": "/changes/items", "source": "/items"},
                           {"target": "/changes/pages", "source": "/pages"}], "evidence": []}}
PAGING = {"next": "/next", "noNext": "absent", "fills": "/arguments/cursor", "items": "/items", "maxPages": 8}
LIST = {"tool": "list-changes", "arguments": {"since": {"$param": "since"}, "limit": 2}}
CASE = {"id": "CASE-1", "since": "2026-11-14T00:00:00Z"}
CASE_PARAMETERS = {"since": {"pointer": "/since", "type": "string"}}


def rule(when: dict[str, Any], unknown_reason: str, resolved_reason: str, target: str = "/changes/items",
         parameters: dict[str, str] | None = None) -> dict[str, Any]:
    """A rule of version 1: when `when` holds, `unknown`; otherwise the records, resolved."""
    return {"rule": {"ruleVersion": "1", "parameters": parameters or {}, "clauses": [
        {"when": when, "claim": {"facts": [], "evidence": {}, "acquisitionStatus": "unknown"}, "reason": unknown_reason},
        {"when": {"op": "always"}, "claim": {"facts": [{"pointer": target, "from": "/items"}], "evidence": {},
                                             "acquisitionStatus": "resolved"}, "reason": resolved_reason}]}}


def paged(name: str = "changes", profile: dict[str, Any] = FEED, arguments: Any = None, paging: Any = None,
          read: Any = None, **more: Any) -> dict[str, Any]:
    source = {"name": name, "kind": "operation", "profile": profile["id"], "profileDigest": digest(profile),
              "maxAge": 300, "arguments": LIST if arguments is None else arguments}
    source.update(more)
    if paging is not False:
        source["paging"] = PAGING if paging is None else paging
    source["read"] = COPY if read is None else read
    return source


def unpaged(name: str, target: str, arguments: Any = None, **more: Any) -> dict[str, Any]:
    source = {"name": name, "kind": "operation", "profile": "feed", "profileDigest": digest(FEED), "maxAge": 300,
              "arguments": arguments or {"tool": "get-record", "arguments": {"id": name}}}
    source.update(more)
    source["read"] = {"copy": {"facts": [{"target": target, "source": "/id"}], "evidence": []}}
    return source


def dialect(*sources: dict[str, Any], fmt: str = "4.1.0", parameters: Any = None) -> dict[str, Any]:
    return {"formatVersion": fmt, "id": ID, "version": "0.1.0",
            "case": {"parameters": parameters or CASE_PARAMETERS, "facts": [], "evidence": []},
            "sources": list(sources)}


def q0(source: dict[str, Any], case: dict[str, Any] = CASE) -> Any:
    return instantiate(source["arguments"], case)


def items(*names: str) -> list[dict[str, str]]:
    return [{"id": n} for n in names]


def results(*spec: tuple[list[str], Any]) -> list[dict[str, Any]]:
    """Each page's value: its records and its next reference; `None` for a page that names none (absent)."""
    out = []
    for names, reference in spec:
        value: dict[str, Any] = {"items": items(*names)}
        if reference is not None:
            value["next"] = reference
        out.append(value)
    return out


THREE = results((["c1", "c2"], "t1"), (["c3", "c4"], "t2"), (["c5"], None))


def nest(depth: int) -> Any:
    """A value nested `depth` levels (every object and array one level)."""
    value: Any = 1
    for _ in range(depth):
        value = {"a": value}
    return value


def cites(*pairs: tuple[str, int]) -> list[list[Any]]:
    return [[s, i] for s, i in pairs]


# --- The rows ------------------------------------------------------------------------------------------

CASES: list[dict[str, Any]] = []


def row(name: str, kind: str, row_name: str, document: dict[str, Any], acquisitions: dict[str, Any],
        expected: dict[str, Any], case: dict[str, Any] = CASE, binding: Any = None,
        preparation: Callable[[dict[str, Any]], dict[str, Any]] | None = None, unread: Any = UNREAD,
        profiles: list[dict[str, Any]] = PROFILES) -> None:
    CASES.append({"name": "paged-" + name, "kind": kind, "row": row_name, "dialect": document, "case": case,
                  "sources": acquisitions, "binding": binding, "expected": expected, "rewrite": preparation,
                  "unread": unread, "profiles": profiles})


def reading(facts: Any, outcomes: dict[str, Any], cite: list[list[Any]], **more: Any) -> dict[str, Any]:
    return {"result": "reading", "facts": facts, "outcomes": outcomes, "cites": cite, **more}


def copied(end: str, count: int, references: list[str]) -> dict[str, Any]:
    return {"status": "resolved", "reason": "copied", "paging": {"end": end, "pages": count, "references": references}}


def refusal(code: str) -> dict[str, Any]:
    return {"result": "refusal", "refusal": code}


def finding(code: str) -> dict[str, Any]:
    return {"result": "finding", "finding": code}


def facts(end: str, count: int, *names: str) -> dict[str, Any]:
    return {"changes": {"end": end, "items": items(*names), "pages": count}}


def build_rows() -> None:
    src = paged()
    first = q0(src)
    three = pages(FEED, first, "/arguments/cursor", THREE)

    # --- positive ---
    row("three-pages-no-next", "positive", "three-pages-no-next", dialect(src), {"changes": {"pages": three}},
        reading(facts("no-next", 3, "c1", "c2", "c3", "c4", "c5"), {"changes": copied("no-next", 3, ["t1", "t2"])},
                cites((S1, 0), (S1, 1), (S1, 2))))
    one = results((["c1"], None))
    row("one-page", "positive", "one-page", dialect(src), {"changes": {"pages": pages(FEED, first, "/arguments/cursor", one)}},
        reading(facts("no-next", 1, "c1"), {"changes": copied("no-next", 1, [])}, cites((S1, 0))))
    two = paged(paging={**PAGING, "maxPages": 2})
    bound2 = results((["c1", "c2"], "t1"), (["c3", "c4"], "t2"))
    row("ends-at-bound", "positive", "ends-at-bound", dialect(two),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", bound2)}},
        reading(facts("bound", 2, "c1", "c2", "c3", "c4"), {"changes": copied("bound", 2, ["t1"])}, cites((S1, 0), (S1, 1))))
    one_page = paged(paging={**PAGING, "maxPages": 1})
    row("max-pages-one", "positive", "max-pages-one", dialect(one_page),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", results((["c1"], "t1")))}},
        reading(facts("bound", 1, "c1"), {"changes": copied("bound", 1, [])}, cites((S1, 0))))
    row("reference-repeated-at-bound", "positive", "reference-repeated-at-bound", dialect(two),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", results((["c1"], "t1"), (["c2"], "t1")))}},
        reading(facts("bound", 2, "c1", "c2"), {"changes": copied("bound", 2, ["t1"])}, cites((S1, 0), (S1, 1))))
    bound_rule = paged(paging={**PAGING, "maxPages": 2}, read=rule({"op": "equals", "field": "/end", "to": "bound"},
                                                                    "partial-read", "whole-read"))
    row("bound-rule-unknown", "positive", "bound-rule-unknown", dialect(bound_rule),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", bound2)}},
        reading({}, {"changes": {"status": "unknown", "reason": "partial-read",
                                 "paging": {"end": "bound", "pages": 2, "references": ["t1"]}}}, cites((S1, 0), (S1, 1))))
    window = paged(arguments={"tool": "list-changes", "arguments": {"from": {"$param": "start"}, "to": {"$param": "end"}}},
                   paging={**PAGING, "fills": "/arguments/pageToken"})
    window_case = {"id": "CASE-1", "start": "2026-11-14T00:00:00Z", "end": "2026-11-15T00:00:00Z"}
    window_parameters = {"start": {"pointer": "/start", "type": "string"}, "end": {"pointer": "/end", "type": "string"}}
    row("fills-added", "positive", "fills-added", dialect(window, parameters=window_parameters),
        {"changes": {"pages": pages(FEED, q0(window, window_case), "/arguments/pageToken", results((["c1"], "w1"), (["c2"], None)))}},
        reading(facts("no-next", 2, "c1", "c2"), {"changes": copied("no-next", 2, ["w1"])}, cites((S1, 0), (S1, 1))),
        case=window_case)
    cursor_parameters = {"cursor": {"pointer": "/cursor", "type": "string"}}
    cursor_case = {"id": "CASE-1", "cursor": "c0"}
    continued = paged(arguments={"tool": "list-changes", "arguments": {"cursor": {"$param": "cursor"}}},
                      read={"rule": {"ruleVersion": "1", "parameters": {"cursor": "string"}, "clauses": [
                          {"when": {"op": "equalsParam", "field": "/values/0/start", "param": "cursor"},
                           "claim": {"facts": [{"pointer": "/changes/items", "from": "/items"}], "evidence": {},
                                     "acquisitionStatus": "resolved"}, "reason": "continues"},
                          {"when": {"op": "always"}, "claim": {"facts": [], "evidence": {}, "acquisitionStatus": "unknown"},
                           "reason": "does-not-continue"}]}})
    cursor_first = q0(continued, cursor_case)
    replaced = [{"start": "c0", "items": items("c1"), "next": "t1"}, {"start": "t1", "items": items("c2")}]
    row("fills-replaced", "positive", "fills-replaced", dialect(continued, parameters=cursor_parameters),
        {"changes": {"pages": pages(FEED, cursor_first, "/arguments/cursor", replaced)}},
        reading({"changes": {"items": items("c1", "c2")}},
                {"changes": {"status": "resolved", "reason": "continues", "paging": {"end": "no-next", "pages": 2, "references": ["t1"]}}},
                cites((S1, 0), (S1, 1)), unsignedParameters=[]), case=cursor_case)
    for spelling, last in (("absent", None), ("null", "null"), ("empty-string", "")):
        last_page: dict[str, Any] = {"items": items("c2")}
        if last is not None:
            last_page["next"] = None if last == "null" else last
        values = [{"items": items("c1"), "next": "t1"}, last_page]
        ending = paged(paging={**PAGING, "noNext": spelling})
        row(f"end-{'empty-string' if spelling == 'empty-string' else spelling}", "positive",
            f"end-{'empty-string' if spelling == 'empty-string' else spelling}", dialect(ending),
            {"changes": {"pages": pages(FEED, first, "/arguments/cursor", values)}},
            reading(facts("no-next", 2, "c1", "c2"), {"changes": copied("no-next", 2, ["t1"])}, cites((S1, 0), (S1, 1))))
    row("empty-middle-page", "positive", "empty-middle-page", dialect(src),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", results((["c1"], "t1"), ([], "t2"), (["c2"], None)))}},
        reading(facts("no-next", 3, "c1", "c2"), {"changes": copied("no-next", 3, ["t1", "t2"])}, cites((S1, 0), (S1, 1), (S1, 2))))
    row("duplicates-kept", "positive", "duplicates-kept", dialect(src),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", results((["c1", "c2"], "t1"), (["c2", "c3"], None)))}},
        reading(facts("no-next", 2, "c1", "c2", "c2", "c3"), {"changes": copied("no-next", 2, ["t1"])}, cites((S1, 0), (S1, 1))))
    composed, decomposed = "é", "é"
    row("references-equivalent-not-equal", "positive", "references-equivalent-not-equal", dialect(src),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", results((["c1"], composed), (["c2"], decomposed), (["c3"], None)))}},
        reading(facts("no-next", 3, "c1", "c2", "c3"), {"changes": copied("no-next", 3, [composed, decomposed])},
                cites((S1, 0), (S1, 1), (S1, 2))))
    incomplete = rule({"op": "isTrue", "field": "/last/incomplete"}, "incomplete-read", "whole-read")
    flagged = paged(read=incomplete)
    values = [{"items": items("c1"), "next": "t1"}, {"items": items("c2"), "next": "t2"}, {"items": items("c3"), "incomplete": True}]
    row("last-page-incomplete", "positive", "last-page-incomplete", dialect(flagged),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", values)}},
        reading({}, {"changes": {"status": "unknown", "reason": "incomplete-read",
                                 "paging": {"end": "no-next", "pages": 3, "references": ["t1", "t2"]}}},
                cites((S1, 0), (S1, 1), (S1, 2))))
    values = [{"items": items("c1"), "incomplete": True, "next": "t1"}, {"items": items("c2"), "next": "t2"},
              {"items": items("c3"), "incomplete": False}]
    row("last-is-the-last-page", "positive", "last-is-the-last-page", dialect(flagged),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", values)}},
        reading({"changes": {"items": items("c1", "c2", "c3")}},
                {"changes": {"status": "resolved", "reason": "whole-read",
                             "paging": {"end": "no-next", "pages": 3, "references": ["t1", "t2"]}}},
                cites((S1, 0), (S1, 1), (S1, 2))))
    at_values = paged(read=rule({"op": "isTrue", "field": "/values/1/incomplete"}, "incomplete-page", "whole-read"))
    values = [{"items": items("c1"), "next": "t1"}, {"items": items("c2"), "incomplete": True, "next": "t2"}, {"items": items("c3")}]
    row("page-flag-at-values", "positive", "page-flag-at-values", dialect(at_values),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", values)}},
        reading({}, {"changes": {"status": "unknown", "reason": "incomplete-page",
                                 "paging": {"end": "no-next", "pages": 3, "references": ["t1", "t2"]}}},
                cites((S1, 0), (S1, 1), (S1, 2))))
    http_query = paged(profile=WEB, arguments={"method": "GET", "path": "/v1/records", "query": {"since": {"$param": "since"}}},
                       paging={**PAGING, "next": "/nextPageToken", "fills": "/query/pageToken"})
    values = [{"items": items("c1"), "nextPageToken": "q1"}, {"items": items("c2")}]
    row("http-query", "positive", "http-query", dialect(http_query),
        {"changes": {"pages": pages(WEB, q0(http_query), "/query/pageToken", values, next_of=lambda r: r["nextPageToken"])}},
        reading(facts("no-next", 2, "c1", "c2"), {"changes": copied("no-next", 2, ["q1"])}, cites((S1, 0), (S1, 1))))
    http_body = paged(profile=WEB, arguments={"method": "POST", "path": "/v1/records/search",
                                              "body": {"filter": {"since": {"$param": "since"}}}},
                      paging={**PAGING, "fills": "/body/cursor"})
    row("http-body", "positive", "http-body", dialect(http_body),
        {"changes": {"pages": pages(WEB, q0(http_body), "/body/cursor", results((["c1"], "b1"), (["c2"], None)))}},
        reading(facts("no-next", 2, "c1", "c2"), {"changes": copied("no-next", 2, ["b1"])}, cites((S1, 0), (S1, 1))))
    unbound = {"name": "changes", "kind": "operation", "platform": "change-feed", "operation": "list-changes", "shape": "mcp",
               "record": "adapter-mcp", "maxAge": 300, "arguments": LIST, "paging": PAGING, "read": COPY}
    unbound_dialect = dialect(unbound)
    binding = {"dialect": digest(unbound_dialect), "sources": {"changes": {"profile": "feed", "profileDigest": digest(FEED)}}}
    row("unbound-paged", "positive", "unbound-paged", unbound_dialect, {"changes": {"pages": three}},
        reading(facts("no-next", 3, "c1", "c2", "c3", "c4", "c5"), {"changes": copied("no-next", 3, ["t1", "t2"])},
                cites((S1, 0), (S1, 1), (S1, 2))), binding=binding)
    lookup = unpaged("lookup", "/lookup/id")
    two_pages = pages(FEED, first, "/arguments/cursor", results((["c1"], "t1"), (["c2"], None)))
    lookup_page = page(FEED, q0(lookup), {"id": "R-1"}, S2, 0, None)
    row("beside-unpaged", "positive", "beside-unpaged", dialect(src, lookup),
        {"changes": {"pages": two_pages}, "lookup": {"response": lookup_page}},
        reading({**facts("no-next", 2, "c1", "c2"), "lookup": {"id": "R-1"}},
                {"changes": copied("no-next", 2, ["t1"]), "lookup": {"status": "resolved", "reason": "copied"}},
                cites((S1, 0), (S1, 1), (S2, 0))))
    updates = paged(name="updates", read={"copy": {"facts": [{"target": "/updates/items", "source": "/items"}], "evidence": []}})
    row("two-paged-sessions-apart", "positive", "two-paged-sessions-apart", dialect(src, updates),
        {"changes": {"pages": two_pages},
         "updates": {"pages": pages(FEED, q0(updates), "/arguments/cursor", results((["u1"], "v1"), (["u2"], None)), session=S2)}},
        reading({**facts("no-next", 2, "c1", "c2"), "updates": {"items": items("u1", "u2")}},
                {"changes": copied("no-next", 2, ["t1"]),
                 "updates": {"status": "resolved", "reason": "copied", "paging": {"end": "no-next", "pages": 2, "references": ["v1"]}}},
                cites((S1, 0), (S1, 1), (S2, 0), (S2, 1))))
    # a skipped paged source: its parameter reads a target `first` does not write
    a = unpaged("first", "/first/id", read=None)
    a["read"] = {"copy": {"facts": [{"target": "/first/cursor", "source": "/cursor"}, {"target": "/first/id", "source": "/id"}], "evidence": []}}
    b = unpaged("second", "/second/id")
    skipped = paged(parameters={"start": {"from": "first", "pointer": "/first/cursor", "type": "string"}},
                    arguments={"tool": "list-changes", "arguments": {"cursor": {"$param": "start"}}})
    b_page = page(FEED, q0(b), {"id": "R-2"}, S3, 0, None)
    a_page = page(FEED, q0(a), {"id": "R-1"}, S3, 1, b_page["receipt"]["signature"])
    skipped_dialect = dialect(a, b, skipped)
    skipped_expected = reading({"first": {"id": "R-1"}, "second": {"id": "R-2"}},
                               {"first": {"status": "resolved", "reason": "copied"}, "second": {"status": "resolved", "reason": "copied"},
                                "changes": {"status": "unknown", "reason": "dependency-unavailable"}},
                               cites((S3, 1), (S3, 0)))
    row("cites-order-paged-skipped", "positive", "cites-order-paged-skipped", skipped_dialect,
        {"first": {"response": a_page}, "second": {"response": b_page}}, skipped_expected)

    # --- boundary ---
    at_row = paged(paging={**PAGING, "maxPages": 64})
    many = [{"items": items(f"c{i}"), "next": f"t{i + 1}"} for i in range(64)]
    row("max-pages-at-row", "boundary", "max-pages-at-row", dialect(at_row),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", many)}},
        reading(facts("bound", 64, *[f"c{i}" for i in range(64)]),
                {"changes": copied("bound", 64, [f"t{i + 1}" for i in range(63)])}, cites(*[(S1, i) for i in range(64)])))
    row("max-pages-over-row", "boundary", "max-pages-over-row", dialect(paged(paging={**PAGING, "maxPages": 65})),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", one)}}, refusal("input-over-bound"))
    many = [{"items": items(f"c{i}"), "next": f"t{i + 1}"} for i in range(65)]
    row("pages-over-row", "boundary", "pages-over-row", dialect(at_row),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", many)}}, refusal("input-over-bound"))
    at_bytes, over_bytes = "é" * 4096, "é" * 4096 + "a"
    row("reference-at-bytes", "boundary", "reference-at-bytes", dialect(src),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", results((["c1"], at_bytes), (["c2"], None)))}},
        reading(facts("no-next", 2, "c1", "c2"), {"changes": copied("no-next", 2, [at_bytes])}, cites((S1, 0), (S1, 1))))
    row("reference-over-bytes", "boundary", "reference-over-bytes", dialect(src),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", results((["c1"], over_bytes), (["c2"], None)))}},
        refusal("input-over-bound"))
    row("reference-over-bytes-at-bound", "boundary", "reference-over-bytes-at-bound", dialect(two),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", results((["c1"], "t1"), (["c2"], over_bytes)))}},
        refusal("input-over-bound"))
    row("items-before-reference-bytes", "negative", "items-before-reference-bytes", dialect(src),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", [{"items": {"id": "c1"}, "next": over_bytes}])}},
        finding("read-failed"))
    deep30 = {"items": items("c1"), "detail": nest(29)}
    row("joined-nesting-at-bound", "boundary", "joined-nesting-at-bound", dialect(src),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", [deep30])}},
        reading(facts("no-next", 1, "c1"), {"changes": copied("no-next", 1, [])}, cites((S1, 0))))
    deep31 = {"items": items("c1"), "detail": nest(30)}
    row("joined-nesting-over", "boundary", "joined-nesting-over", dialect(src),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", [deep31])}}, refusal("input-over-bound"))
    wrapped = paged(read={**COPY, "unwrap": ["/body"]})
    body0 = {"body": json.dumps({"items": items("c1"), "next": "t1"})}
    body1_at = {"body": json.dumps({"items": items("c2")}), "trace": nest(31)}
    body1_over = {"body": json.dumps({"items": items("c2")}), "trace": nest(32)}
    wrapped_pages = pages(FEED, first, "/arguments/cursor", [body0, body1_at], next_of=lambda r: "t1")
    row("page-result-nesting-at-bound", "boundary", "page-result-nesting-at-bound", dialect(wrapped),
        {"changes": {"pages": wrapped_pages}},
        reading(facts("no-next", 2, "c1", "c2"), {"changes": copied("no-next", 2, ["t1"])}, cites((S1, 0), (S1, 1))))
    row("page-result-nesting-over", "boundary", "page-result-nesting-over", dialect(wrapped),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", [body0, body1_over], next_of=lambda r: "t1",
                                    per_page={0: {"corrupt": True}})}},
        refusal("input-over-bound"))

    # --- negative and adversarial: the walk ---
    def pages_of(values: list[Any], **options: Any) -> dict[str, Any]:
        return {"changes": {"pages": pages(FEED, first, "/arguments/cursor", values, **options)}}

    two_named = results((["c1"], "t1"), (["c2"], None))
    row("request-not-formed", "negative", "request-not-formed", dialect(src),
        pages_of(two_named, per_page={1: {"asked": formed(first, "/arguments/cursor", "t9")}}), finding("acquisition-invalid"))
    swapped = pages(FEED, first, "/arguments/cursor", THREE)
    row("pages-swapped", "adversarial", "pages-swapped", dialect(src),
        {"changes": {"pages": [swapped[1], swapped[0], swapped[2]]}}, finding("acquisition-invalid"))

    def page_items(receipt: dict[str, Any]) -> None:
        receipt["acquisition"]["pageItems"] = ["sha256:" + hashlib.sha256(b"c2").hexdigest()]

    row("page-items-receipt", "negative", "page-items-receipt", dialect(src),
        pages_of(two_named, per_page={1: {"change": page_items}}), finding("acquisition-invalid"))
    row("prev-signature-malformed", "negative", "prev-signature-malformed", dialect(src),
        pages_of(two_named, per_page={1: {"prev": "not-a-signature"}}), finding("acquisition-invalid"))
    # a receipt at odds with its own callIndex is check 1's, before step 4 reads the chain (issue #326)
    with salts_apart("prev-signature-at-call-0"):
        at_call_0 = pages_of(two_named, per_page={0: {"prev": "ab" * 64}})
    row("prev-signature-at-call-0", "negative", "prev-signature-at-call-0", dialect(src), at_call_0,
        finding("acquisition-invalid"))
    with salts_apart("prev-signature-null-after-0"):
        null_after_0 = pages_of(two_named, per_page={1: {"prev": None}})
    row("prev-signature-null-after-0", "negative", "prev-signature-null-after-0", dialect(src), null_after_0,
        finding("acquisition-invalid"))
    row("stale-last-page", "negative", "stale-last-page", dialect(src),
        pages_of(two_named, per_page={1: {"at": STALE}}), finding("acquisition-stale"))
    row("stale-middle-page", "negative", "stale-middle-page", dialect(src),
        pages_of(THREE, per_page={1: {"at": STALE}}), finding("acquisition-stale"))
    # call 1 asked page 1 and was dropped; call 2 asked it again and was kept
    p0 = page(FEED, first, two_named[0], S1, 0, None)
    dropped = page(FEED, formed(first, "/arguments/cursor", "t1"), two_named[1], S1, 1, p0["receipt"]["signature"])
    kept = page(FEED, formed(first, "/arguments/cursor", "t1"), two_named[1], S1, 2, dropped["receipt"]["signature"])
    row("call-index-gap", "adversarial", "call-index-gap", dialect(src), {"changes": {"pages": [p0, kept]}},
        finding("acquisition-sessions"))
    later = page(FEED, formed(first, "/arguments/cursor", "t1"), two_named[1], S1, 0, None)
    earlier = page(FEED, first, two_named[0], S1, 1, later["receipt"]["signature"])
    row("call-index-reordered", "adversarial", "call-index-reordered", dialect(src), {"changes": {"pages": [earlier, later]}},
        finding("acquisition-sessions"))
    row("page-from-another-session", "adversarial", "page-from-another-session", dialect(src),
        pages_of(two_named, per_page={1: {"session": S2}}), finding("acquisition-sessions"))
    row("chain-broken", "adversarial", "chain-broken", dialect(src),
        pages_of(two_named, per_page={1: {"prev": "ab" * 64}}), finding("acquisition-sessions"))
    tail = pages(FEED, first, "/arguments/cursor", two_named)
    shared = page(FEED, q0(lookup), {"id": "R-1"}, S1, 2, tail[-1]["receipt"]["signature"])
    row("session-shared", "negative", "session-shared", dialect(src, lookup),
        {"changes": {"pages": tail}, "lookup": {"response": shared}}, finding("acquisition-sessions"))
    first_lookup = page(FEED, q0(lookup), {"id": "R-1"}, S1, 0, None)
    row("session-of-earlier-source", "negative", "session-of-earlier-source", dialect(lookup, src),
        {"lookup": {"response": first_lookup}, "changes": {"pages": pages(FEED, first, "/arguments/cursor", two_named)}},
        finding("acquisition-sessions"))
    row("two-paged-one-session", "adversarial", "two-paged-one-session", dialect(src, updates),
        {"changes": {"pages": two_pages},
         "updates": {"pages": pages(FEED, q0(updates), "/arguments/cursor", results((["u1"], None)), session=S1)}},
        finding("acquisition-sessions"))
    # a later research source whose record's own receipt is the next call of the paged session
    research = {"name": "summary", "kind": "research", "profile": "assistant", "profileDigest": digest(ASSISTANT),
                "webProfiles": {}, "maxAge": 300, "question": "Summarize the changes.", "constraints": {"synthetic": True},
                "model": MODEL, "evidence": ["Use only the retained responses."],
                "results": [{"id": "summary", "type": "string", "required": True, "description": "The summary.",
                             "cardinality": "one"}],
                "capabilities": ["answer"],
                "read": {"copy": {"facts": [{"target": "/summary/state", "source": "/results/summary/status"}], "evidence": []}}}
    research_asked = {name: research[name] for name in ("question", "constraints", "model", "evidence", "results", "capabilities")}
    record = {"results": {"summary": {"status": "missing", "cites": [], "reason": "No summary was retained."}},
              "responses": [],
              "execution": {"resolvedSettings": {"model": MODEL, "profile": "assistant", "version": "1",
                                                 "settings": {"temperature": "0"}},
                            "retainedBytes": [{"mediaType": "application/json",
                                               "base64": base64.b64encode(b'{"status":"missing"}').decode("ascii")}]}}
    with salts_apart("research-in-paged-session"):
        summary = page(ASSISTANT, research_asked, record, S1, 2, tail[-1]["receipt"]["signature"])
    row("research-in-paged-session", "negative", "research-in-paged-session", dialect(src, research),
        {"changes": {"pages": tail}, "summary": {"response": summary}},
        finding("acquisition-sessions"), profiles=[*PROFILES, ASSISTANT])
    row("page-missing", "negative", "page-missing", dialect(src), pages_of(results((["c1"], "t1"))), finding("acquisition-missing"))
    after_end = pages(FEED, first, "/arguments/cursor", results((["c1"], None), (["c2"], None)), next_of=lambda r: "t1")
    row("page-after-end", "adversarial", "page-after-end", dialect(src), {"changes": {"pages": after_end}},
        finding("acquisition-unexpected"))
    row("page-beyond-bound", "adversarial", "page-beyond-bound", dialect(two),
        pages_of(results((["c1"], "t1"), (["c2"], "t2"), (["c3"], None))), finding("acquisition-unexpected"))
    # the joined value would nest 33 levels, but it is formed only after the page retained after the end is refused
    with salts_apart("unexpected-before-joined-nesting"):
        beyond_deep = pages_of([deep31, {"items": items("c2")}], next_of=lambda r: "t1")
    row("unexpected-before-joined-nesting", "negative", "unexpected-before-joined-nesting", dialect(src),
        beyond_deep, finding("acquisition-unexpected"))
    alone = page(FEED, q0(a), {"id": "R-1"}, S3, 0, None)
    row("skipped-paged-with-member", "negative", "skipped-paged-with-member", dialect(a, skipped),
        {"first": {"response": alone},
         "changes": {"pages": pages(FEED, {"tool": "list-changes", "arguments": {"cursor": "x"}}, "/arguments/cursor", one, session=S1)}},
        finding("acquisition-unexpected"))
    row("reference-repeated", "negative", "reference-repeated", dialect(src),
        pages_of(results((["c1"], "t1"), (["c2"], "t1"), (["c3"], None))), finding("read-failed"))
    row("reference-number", "negative", "reference-number", dialect(src),
        pages_of([{"items": items("c1"), "next": 7}]), finding("read-failed"))
    nested_next = paged(paging={**PAGING, "next": "/page/next"})
    row("next-parent-absent", "negative", "next-parent-absent", dialect(nested_next),
        pages_of([{"items": items("c1")}]), finding("read-failed"))
    row("items-not-array", "negative", "items-not-array", dialect(src), pages_of([{"items": "c1", "next": "t1"}]),
        finding("read-failed"))
    row("reference-equals-q0", "adversarial", "reference-equals-q0", dialect(continued, parameters=cursor_parameters),
        {"changes": {"pages": pages(FEED, cursor_first, "/arguments/cursor",
                                    [{"start": "c0", "items": items("c1"), "next": "c0"}, {"start": "c0", "items": items("c2")}])}},
        finding("read-failed"), case=cursor_case)
    null_end = paged(paging={**PAGING, "noNext": "null"})
    row("end-spelling-undeclared", "negative", "end-spelling-undeclared", dialect(null_end),
        pages_of([{"items": items("c1"), "next": "t1"}, {"items": items("c2"), "next": ""}], next_of=lambda r: "t1"),
        finding("read-failed"))
    row("end-absent-member-null", "negative", "end-absent-member-null", dialect(src),
        pages_of([{"items": items("c1"), "next": "t1"}, {"items": items("c2"), "next": None}], next_of=lambda r: "t1"),
        finding("read-failed"))
    misspelled = paged(paging={**PAGING, "noNext": "null", "next": "/nxt"})
    row("next-misspelled", "negative", "next-misspelled", dialect(misspelled), pages_of(THREE), finding("read-failed"))
    row("read-failed-before-invalid", "negative", "read-failed-before-invalid", dialect(src),
        pages_of([{"items": "c1", "next": "t1"}, {"items": items("c2")}], next_of=lambda r: "t1", per_page={1: {"corrupt": True}}),
        finding("read-failed"))

    # --- the preparation rewritten ---
    def rewrite_end(preparation: dict[str, Any]) -> dict[str, Any]:
        preparation["outcomes"][1]["paging"]["end"] = "bound"
        return preparation

    def drop_reference(preparation: dict[str, Any]) -> dict[str, Any]:
        preparation["outcomes"][1]["paging"]["references"].pop()
        return preparation

    def by_call_index(preparation: dict[str, Any]) -> dict[str, Any]:
        preparation["cites"].sort(key=lambda c: READER.integer_of(c["callIndex"]))
        return preparation

    row("end-changed", "adversarial", "end-changed", dialect(src), {"changes": {"pages": three}},
        finding("preparation-differs"), preparation=rewrite_end)
    row("reference-dropped", "adversarial", "reference-dropped", dialect(src), {"changes": {"pages": three}},
        finding("preparation-differs"), preparation=drop_reference)
    row("cites-by-call-index-paged-skipped", "adversarial", "cites-by-call-index-paged-skipped", skipped_dialect,
        {"first": {"response": a_page}, "second": {"response": b_page}}, finding("preparation-differs"), preparation=by_call_index)

    # --- refusals of form ---
    malformed = refusal("input-malformed")
    unpaged_changes = paged(paging=False)
    as_response = {"changes": {"response": page(FEED, first, {"items": items("c1")}, S1, 0, None)}}
    row("paging-in-4.0.0", "negative", "paging-in-4.0.0", dialect(src, fmt="4.0.0"), as_response, malformed,
        unread=malformed)
    row("paging-with-calculation", "negative", "paging-with-calculation",
        dialect(paged(calculation={"inputs": {}, "tables": {}})), {"changes": {"pages": three}}, malformed)
    in_form = paged(arguments={"tool": "list-changes", "arguments": {"filter": {"$param": "since"}}},
                    paging={**PAGING, "fills": "/arguments/filter/cursor"})
    row("fills-in-template-form", "negative", "fills-in-template-form", dialect(in_form),
        {"changes": {"pages": pages(FEED, q0(in_form), "/arguments/filter/cursor", one)}}, malformed)
    row("fills-parent-unresolved", "negative", "fills-parent-unresolved",
        dialect(paged(paging={**PAGING, "fills": "/arguments/page/cursor"})), {"changes": {"pages": three}}, malformed)
    row("pages-empty", "negative", "pages-empty", dialect(src), {"changes": {"pages": []}}, malformed)
    row("max-pages-zero", "negative", "max-pages-zero", dialect(paged(paging={**PAGING, "maxPages": 0})),
        {"changes": {"pages": three}}, malformed)
    row("response-form-for-paged", "negative", "response-form-for-paged", dialect(src), as_response, malformed)
    row("pages-form-for-unpaged", "negative", "pages-form-for-unpaged", dialect(unpaged_changes),
        {"changes": {"pages": [as_response["changes"]["response"]]}}, malformed)
    row("pages-and-response", "negative", "pages-and-response", dialect(src),
        {"changes": {"pages": three, "response": three[0]}}, malformed)
    row("no-next-unknown", "negative", "no-next-unknown", dialect(paged(paging={**PAGING, "noNext": "missing"})),
        {"changes": {"pages": three}}, malformed)
    row("pages-form-for-undeclared", "negative", "pages-form-for-undeclared", dialect(src),
        {"changes": {"pages": three}, "elsewhere": {"pages": [as_response["changes"]["response"]]}}, malformed)
    row("max-pages-not-integer", "negative", "max-pages-not-integer",
        dialect(paged(paging={**PAGING, "maxPages": "2"})), {"changes": {"pages": three}}, malformed)
    # 1e3 is outside the canon domain (§1): phase 3 does not measure it, and the dialect is input-malformed
    row("max-pages-exponent-not-measured", "negative", "max-pages-exponent-not-measured",
        dialect(paged(paging={**PAGING, "maxPages": Literal("1e3")})), {"changes": {"pages": three}}, malformed)
    many = [{"items": items(f"c{i}"), "next": f"t{i + 1}"} for i in range(65)]
    row("pages-over-row-in-4.0.0", "negative", "pages-over-row-in-4.0.0", dialect(unpaged_changes, fmt="4.0.0"),
        {"changes": {"pages": pages(FEED, first, "/arguments/cursor", many)}}, malformed, unread=malformed)

    # --- profile-mismatch ---
    mismatch = finding("profile-mismatch")

    def fills_row(name: str, profile: dict[str, Any], arguments: Any, fills: str) -> None:
        source = paged(profile=profile, arguments=arguments, paging={**PAGING, "fills": fills})
        row(name, "negative", name, dialect(source),
            {"changes": {"pages": pages(profile, q0(source), fills, one)}}, mismatch)

    get = {"method": "GET", "path": "/v1/records", "query": {"since": {"$param": "since"}}}
    post = {"method": "POST", "path": "/v1/records/search", "body": {"since": {"$param": "since"}}}
    fills_row("fills-tool", FEED, LIST, "/tool")
    fills_row("fills-path", WEB, get, "/path")
    fills_row("fills-method", WEB, get, "/method")
    fills_row("fills-connection", CONNECTION, {"connection": "conn-1", "revision": "rev-1", "read": "changes"}, "/connection")
    fills_row("fills-arguments-itself", FEED, LIST, "/arguments")
    fills_row("fills-query-itself", WEB, get, "/query")
    fills_row("fills-body-itself", WEB, post, "/body")
    # §4.1 holds query's members to string templates, so a parent of three tokens under query is no object:
    # input-malformed by section 2's parent rule, before any profile is read
    three_tokens = paged(profile=WEB, arguments={"method": "GET", "path": "/v1/records", "query": {"filter": "open"}},
                         paging={**PAGING, "fills": "/query/filter/cursor"})
    row("fills-query-three-tokens", "negative", "fills-query-three-tokens", dialect(three_tokens),
        {"changes": {"pages": pages(WEB, q0(three_tokens), "/query/filter/cursor", one)}}, malformed)

    # --- a reader that does not read the format ---
    row("format-4.1.0-unread", "negative", "format-4.1.0-unread", dialect(src), {"changes": {"pages": three}},
        reading(facts("no-next", 3, "c1", "c2", "c3", "c4", "c5"), {"changes": copied("no-next", 3, ["t1", "t2"])},
                cites((S1, 0), (S1, 1), (S1, 2))),
        )


# --- Writing and checking ------------------------------------------------------------------------------


def inputs_of(case: dict[str, Any], preparation: bytes) -> dict[str, bytes]:
    files = {
        "dialect.json": (text(case["dialect"], 2) + "\n").encode("utf-8"),
        "case.json": (text(case["case"], 2) + "\n").encode("utf-8"),
        "sources.json": (text(case["sources"], 1) + "\n").encode("utf-8"),
        "profiles.json": (text(case["profiles"], 2) + "\n").encode("utf-8"),
        "preparation.json": preparation,
    }
    if case["binding"] is not None:
        files["binding.json"] = (text(case["binding"], 2) + "\n").encode("utf-8")
    return files


def run(files: dict[str, bytes]) -> Any:
    return READER.verify(files["dialect.json"], files["case.json"], files["sources.json"], files["profiles.json"],
                         files["preparation.json"], binding=files.get("binding.json"))


def check_reading(name: str, case: dict[str, Any], answer: dict[str, Any], preparation: dict[str, Any]) -> None:
    expected = case["expected"]
    assert "reading" in answer, (name, answer)
    reading = answer["reading"]
    assert READER.as_plain(reading["facts"]) == expected["facts"], (name, reading["facts"])
    outcomes = {o["name"]: o for o in preparation["outcomes"]}
    # each case parameter's value, by its one-token pointer into the case
    values = {p: case["case"][d["pointer"][1:]] for p, d in case["dialect"]["case"]["parameters"].items()}
    declared = {s["name"]: s for s in case["dialect"]["sources"]}
    for source, want in expected["outcomes"].items():
        got = outcomes[source]
        assert (got["status"], got["reason"]) == (want["status"], want["reason"]), (name, source, got["status"], got["reason"])
        assert READER.as_plain(got.get("paging")) == want.get("paging"), (name, source, got.get("paging"))
        if want.get("paging") is None:
            continue
        # RFC 0033 section 8, by hand: the outcome carries Q0 as `arguments`, formed here from the case, and
        # each lineage entry of the source carries `receipts`, its pages' citations in call order, and no `receipt`
        assert got["arguments"] == instantiate(declared[source]["arguments"], values), (name, source, got["arguments"])
        lines = [line for line in preparation["lineage"] if line["source"] == source]
        for line in lines:
            assert "receipt" not in line, (name, source, line)
            assert [c["callIndex"] for c in line["receipts"]] == list(range(want["paging"]["pages"])), (name, source, line)
            assert len({c["sessionId"] for c in line["receipts"]}) == 1, (name, source, line)
    assert [[c["sessionId"], c["callIndex"]] for c in READER.as_plain(preparation["cites"])] == expected["cites"], name
    if "unsignedParameters" in expected:
        assert reading.get("unsignedParameters", []) == expected["unsignedParameters"], (name, reading)


def main(argv: list[str]) -> int:
    build_rows()
    check = "--check" in argv
    manifest_cases = []
    differs = []
    names = set()
    for case in CASES:
        name = case["name"]
        assert name not in names, name
        names.add(name)
        placeholder = (text({"verifiedAt": VERIFIED_AT}) + "\n").encode("utf-8")
        files = inputs_of(case, placeholder)
        expected = case["expected"]
        if expected["result"] == "reading" or case["rewrite"] is not None:
            first = run(files)
            assert first.answer.get("finding") == "preparation-differs", (name, first.answer)
            recomputed = first.preparation
            if case["rewrite"] is not None:
                rewritten = case["rewrite"](READER.read_document(recomputed, "p"))
                files["preparation.json"] = READER.preparation_bytes(rewritten)
            else:
                files["preparation.json"] = recomputed
        result = run(files)
        if expected["result"] == "reading":
            check_reading(name, case, result.answer, json.loads(files["preparation.json"]))
        else:
            got = {"result": "refusal", "refusal": result.answer["refused"]} if "refused" in result.answer else \
                  {"result": "finding", "finding": result.answer.get("finding")}
            assert got == expected, (name, result.answer)
        entry = {"name": name, "row": case["row"], "kind": case["kind"],
                 "files": {f: hashlib.sha256(b).hexdigest() for f, b in files.items()},
                 "expected": expected,
                 "expectedReportOfAReaderThatDoesNotReadTheFormat": case["unread"]}
        if expected["result"] == "reading":
            entry["preparationDigest"] = result.digest
        manifest_cases.append(entry)
        directory = OUT / name
        for f, b in files.items():
            path = directory / f
            if check:
                if not path.is_file() or path.read_bytes() != b:
                    differs.append(str(path.relative_to(ROOT)))
            else:
                directory.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b)
    manifest = {
        "status": "hand-written; format 4.1.0 of specVersion 0.6.0 (RFC 0033, accepted), not a published conformance corpus",
        "rfc": 33,
        "companion": "spec/dialect.md §2.3",
        "verifiedAt": VERIFIED_AT,
        "signing": {"identity": "RFC 8032, section 7.1, TEST 1", "publicKey": PUBLIC},
        "cases": manifest_cases,
    }
    data = (json.dumps(manifest, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    if check:
        if (OUT / "manifest.json").read_bytes() != data:
            differs.append("manifest.json")
        for d in differs:
            print("differs:", d)
        return 1 if differs else 0
    (OUT / "manifest.json").write_bytes(data)
    print(f"{len(manifest_cases)} vectors written")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

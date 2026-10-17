"""Round 15 reader controls, altered copies of a staged research vector, never vectors."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest
from typing import Any

from test_dialect import Inputs, READER, signer

VECTOR = "gtm-company-person-valid-types-all-six"
PREFIX = "https://a.example/docs"


def encoded(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def canonical(value: Any) -> bytes:
    return READER.canon(READER.read_document(encoded(value), "control"))


def digest(value: Any) -> str:
    return READER.digest_of(canonical(value))


def scoped_inputs(scope: Any = None, endpoints: tuple[Any, ...] = (
    PREFIX + "/one", PREFIX + "/two",
), profile_edit: Any = None, documents_edit: Any = None, after: Any = None) -> Inputs:
    inputs = Inputs(VECTOR, False)
    inputs.record = None
    profiles = json.loads(inputs.profiles)
    page = next(p for p in profiles if p["id"] == "page")
    page["endpoint"] = None
    page["endpointScope"] = [PREFIX] if scope is None else scope
    if profile_edit:
        profile_edit(page)
    binding = json.loads(inputs.binding)
    document = json.loads(inputs.dialect)
    acquisitions = json.loads(inputs.acquisitions)
    responses = acquisitions["person"]["response"]["result"]["responses"]
    page_response = responses.pop()
    for index, endpoint in enumerate(endpoints):
        retained = copy.deepcopy(page_response)
        retained["request"] = {"url": PREFIX + f"/request-{index}?item=synthetic"}
        retained["receipt"]["acquisition"]["endpoint"] = endpoint
        retained["receipt"]["callIndex"] = 3 + index
        responses.append(retained)
    documents = {"profiles": profiles, "binding": binding, "dialect": document,
                 "acquisitions": acquisitions}
    if documents_edit:
        documents_edit(documents)
    public, sign = signer(b"round 15 reader controls")
    for profile in profiles:
        profile["publicKey"] = public.hex()
    digests = {p["id"]: digest(p) for p in profiles}
    for assignment in binding["sources"].values():
        for ref in [assignment, *assignment["webProfiles"].values()]:
            ref["profileDigest"] = digests[ref["profile"]]
    binding["dialect"] = digest(document)
    for member in acquisitions.values():
        for response in member["response"]["result"]["responses"]:
            response["profile"]["digest"] = digests[response["profile"]["id"]]
            receipt = response["receipt"]
            receipt["keyId"] = hashlib.sha256(public).hexdigest()[:32]
            receipt["argumentsCommitment"] = READER.digest_of(
                bytes.fromhex(response["salts"]["args"]) + b"args:" + canonical(response["request"]))
            receipt["resultDigest"] = digest(response["result"])
            del receipt["signature"]
            receipt["signature"] = sign(
                b"judgment-pack-gateway/receipt/3:" + canonical(receipt)).hex()
    if after:
        after(documents)
    for name, value in documents.items():
        setattr(inputs, name, encoded(value))
    # As existing reader controls do, obtain a matching preparation only if all checks pass.
    computed = inputs.verify().preparation
    if computed is not None:
        inputs.preparation = computed
    return inputs


def endpoint_scope_cases() -> list[tuple[str, str, Any]]:
    cases = []

    def add(name: str, answer: str = "reading", **kwargs: Any) -> None:
        cases.append(("scope " + name, answer, lambda: scoped_inputs(**kwargs)))

    invalid = "finding:acquisition-invalid"
    malformed = "refusal:input-malformed"
    add("two different page endpoints")
    add("another host", invalid, endpoints=("https://other.example/docs/one",))
    add("second response outside", invalid, endpoints=(PREFIX, "https://other.example/docs"))
    add("segment boundary", invalid, endpoints=(PREFIX + "x",))
    add("equal path", endpoints=(PREFIX,))
    add("host case and default port", endpoints=("https://A.EXAMPLE:443/docs/one",))
    add("written default port in scope", scope=["https://A.EXAMPLE:443/docs"])
    add("empty endpoint port", endpoints=("https://a.example:/docs/x",))
    add("empty endpoint port with written scope port", scope=["https://a.example:443/docs"],
        endpoints=("https://a.example:/docs/x",))
    add("empty scope port", scope=["https://a.example:/docs"],
        endpoints=("https://a.example/docs/x",))
    add("record wildcard", malformed, scope=["https://*"],
        profile_edit=lambda p: p.__setitem__("class", "record"))
    add("record wildcard without research", malformed, scope=[PREFIX, "https://*"],
        profile_edit=lambda p: (p.__setitem__("class", "record"), p.pop("research")))
    add("trailing prefix slash", scope=[PREFIX + "/"])
    add("trailing prefix excludes parent", invalid, scope=[PREFIX + "/"], endpoints=(PREFIX,))
    add("root admits absent path", scope=["https://a.example/"], endpoints=("https://a.example",))
    add("absent prefix path", scope=["https://a.example"], endpoints=("https://a.example/",))
    add("union of prefixes", scope=["https://other.example", PREFIX])
    add("wildcard", scope=["https://*"], endpoints=("https://new.example/a", "https://next.example/b"))
    add("path case", invalid, endpoints=("https://a.example/Docs/one",))
    add("host suffix", invalid, endpoints=("https://sub.a.example/docs",))
    add("encoded slash is no boundary", invalid, endpoints=(PREFIX + "%2Fx",))
    add("encoded spelling", scope=[PREFIX + "/%7e"], endpoints=(PREFIX + "/%7e/x",))
    add("escape case differs", invalid, scope=[PREFIX + "/%7e"], endpoints=(PREFIX + "/%7E",))
    add("no escape decoding", invalid, scope=[PREFIX + "/%7e"], endpoints=(PREFIX + "/~",))
    add("repeated slash preserved", invalid, scope=[PREFIX + "//x"], endpoints=(PREFIX + "/x",))
    add("path at sign is not user", endpoints=(PREFIX + "/@name",))
    for endpoint in [
        None, "http://a.example/docs", "https://a.example:444/docs", "https://a.example:0443/docs",
        "https://a.example:0/docs", "https://a.example:80/docs", "https://a.example:4430/docs",
        "https://user@a.example/docs", PREFIX + "?x", PREFIX + "#x",
        "https://127.0.0.1/docs", "https://[::1]/docs", "https://127.1/docs",
        "https://localhost/docs", "https://a.example./docs", "https://a_b.example/docs",
        "https://-a.example/docs", "https://a-.example/docs", "https://a..example/docs",
        "https://" + "a" * 64 + ".example/docs", "https://a.123/docs", "https://0x7f.0x0.0x0.0x1/docs", "https://é.example/docs",
        PREFIX + "/%", PREFIX + "/%2", PREFIX + "/%gg", PREFIX + "/\\x", PREFIX + "/x\n",
        PREFIX + "/.", PREFIX + "/../x", PREFIX + "/%2e/x", PREFIX + "/.%2E/x",
        PREFIX + "/%2E%2e/x", PREFIX + "/%2e./x", PREFIX + "/x/..", "https://*/docs",
        "HTTPS://a.example/docs", "https://a.example/" + "x" * 2031,
    ]:
        add("invalid endpoint " + repr(endpoint), invalid, scope=["https://*"], endpoints=(endpoint,))
    for scope in [[], {}, "https://*", [None], [PREFIX, PREFIX], ["https://*/docs"],
                  ["http://a.example"], [PREFIX + "/.."], [PREFIX + "?x"],
                  ["https://127.0.0.1"], ["https://a.example:444"], ["https://a.example./"],
                  ["https://A.EXAMPLE/" + "%2E/"], ["https://a.example/" + "x" * 2031]]:
        expected = "refusal:input-over-bound" if isinstance(scope, list) and any(
            isinstance(e, str) and len(e.encode()) > 2048 for e in scope) else malformed
        add("bad scope " + repr(scope)[:65], expected, scope=scope)
    add("null scope", malformed, profile_edit=lambda p: p.__setitem__("endpointScope", None))
    for name, edit in [
        ("exact endpoint beside scope", lambda p: p.__setitem__("endpoint", PREFIX)),
        ("wrong adapter", lambda p: p["adapter"].__setitem__("name", "adapter-sources")),
        ("wrong shape", lambda p: p.__setitem__("shape", "airbyte")),
        ("search declaration", lambda p: p["research"].__setitem__("capabilities", ["search", "page"])),
        ("answer declaration", lambda p: p.__setitem__("research", {
            "capabilities": ["answer", "page"], "model": "synthetic-research-model-1"})),
        ("no generated declaration", lambda p: p.pop("research")),
    ]:
        add(name, malformed, profile_edit=edit)
    add("record profile on research", "finding:profile-mismatch",
        profile_edit=lambda p: p.__setitem__("class", "record"))
    add("32 entries", scope=[PREFIX] + [f"https://site{i}.example" for i in range(31)])
    add("33 entries before forms", "refusal:input-over-bound", scope=[PREFIX] * 33,
        profile_edit=lambda p: p.__setitem__("shape", "command"))
    longest = "https://a.example/" + "x" * (2048 - len("https://a.example/"))
    add("2048 byte entry", scope=[longest], endpoints=(longest,))
    add("2049 bytes before forms", "refusal:input-over-bound", scope=[longest + "x"],
        profile_edit=lambda p: p.__setitem__("shape", "command"))
    add("UTF8 bytes before grammar", "refusal:input-over-bound", scope=["é" * 1025])
    add("changed scope with old pin", "finding:profile-mismatch", after=lambda d:
        d["profiles"][-1].__setitem__("endpointScope", ["https://*"]))
    add("changed request", invalid, after=lambda d: d["acquisitions"]["person"]["response"]
        ["result"]["responses"][-1]["request"].__setitem__("url", PREFIX + "/altered"))
    add("changed receipt without signature", invalid, after=lambda d: d["acquisitions"]
        ["person"]["response"]["result"]["responses"][-1]["receipt"]["acquisition"]
        .__setitem__("endpoint", PREFIX + "/altered"))
    # The offline contract holds the final URL only; the original request is still committed.
    add("requested URL is not scope-checked in replay", documents_edit=lambda d:
        d["acquisitions"]["person"]["response"]["result"]["responses"][-1]["request"]
        .__setitem__("url", "https://outside.example/start"))
    for field, value in [("shape", "mcp"), ("adapter", {"name": "other"})]:
        add("exact " + field + " still held", invalid, documents_edit=lambda d, f=field, v=value:
            d["acquisitions"]["person"]["response"]["result"]["responses"][-1]
            ["receipt"]["acquisition"].__setitem__(f, v))

    def operation(d: Any) -> None:
        d["dialect"].pop("admits", None)
        d["dialect"]["sources"] = [{"name": "operation", "kind": "operation",
            "profile": "page", "profileDigest": digest(d["profiles"][-1]),
            "maxAge": 600, "arguments": {"url": PREFIX},
            "read": {"copy": {"facts": [], "evidence": []}}}]
        d["binding"]["sources"] = {}
    # Rebinding to an operation is a finding, even without an acquisition.
    def operation_inputs() -> Inputs:
        i = scoped_inputs()
        d = {"dialect": json.loads(i.dialect), "profiles": json.loads(i.profiles),
             "binding": json.loads(i.binding)}
        operation(d)
        i.dialect, i.binding, i.acquisitions = encoded(d["dialect"]), None, b"{}"
        return i
    cases.append(("scope on operation", "finding:profile-mismatch", operation_inputs))
    cases.append(("scope exact historical profile unchanged", "reading", lambda: Inputs(VECTOR, True)))
    return cases


class EndpointScopeTests(unittest.TestCase):
    def test_endpoint_scope_controls(self) -> None:
        for name, expected, build in endpoint_scope_cases():
            with self.subTest(case=name):
                answer = READER.report(build().verify().answer)
                actual = ("reading" if answer["result"] == "reading"
                          else answer["result"] + ":" + answer[answer["result"]])
                self.assertEqual(expected, actual, answer)

    def test_scope_changes_profile_binding_document_and_preparation_binding(self) -> None:
        first, second = scoped_inputs(), scoped_inputs(scope=["https://*"])
        self.assertNotEqual(digest(json.loads(first.profiles)[-1]), digest(json.loads(second.profiles)[-1]))
        self.assertNotEqual(digest(json.loads(first.binding)), digest(json.loads(second.binding)))
        self.assertNotEqual(json.loads(first.preparation)["mappingDigest"],
                            json.loads(second.preparation)["mappingDigest"])
        self.assertNotEqual(READER.binding_of(first.verify().digest),
                            READER.binding_of(second.verify().digest))
        second.preparation = first.preparation
        self.assertEqual("preparation-differs", second.verify().answer.get("finding"))

    def test_record_web_profile_is_well_formed_but_kind_stays_unread(self) -> None:
        inputs = scoped_inputs(profile_edit=lambda p: (p.__setitem__("class", "record"), p.pop("research")))
        profiles = READER.parse_profiles(READER.read_document(inputs.profiles, "profiles"))
        self.assertIn("endpointScope", profiles["page"])
        d = json.loads(inputs.dialect)
        d.pop("admits", None)
        d["sources"] = [{"name": "page", "kind": "web", "profile": "page",
            "profileDigest": digest(json.loads(inputs.profiles)[-1]), "maxAge": 600,
            "url": PREFIX, "read": {"copy": {"facts": [], "evidence": []}}}]
        inputs.dialect, inputs.binding, inputs.acquisitions = encoded(d), None, b"{}"
        self.assertEqual("kind-unread", inputs.verify().answer.get("refused"))

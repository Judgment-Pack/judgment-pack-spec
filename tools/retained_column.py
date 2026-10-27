"""Selected retained-column/1 integration; no selection changes ordinary readers.

The immutable package's release identity supplies the source revision. Source checkouts
without that generated identity cannot advertise released support. Test installation pins
are patched by tests, never accepted from a caller, capability report or environment.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import Any

try:
    from tools import _retained_column as engine
except ModuleNotFoundError:
    import _retained_column as engine

ROOT = Path(__file__).resolve().parents[1]
TAG = "v0.3.0-rc.2"
ROLES = tuple(engine.ROLE_LIMITS)
CAPS = engine.PROFILE_CAPS


def installed_spec() -> dict[str, str]:
    identity = json.loads((ROOT / "release-identity.json").read_text("utf-8"))
    inventory = json.loads((ROOT / "releases/v0.3.0-rc.2.retained-column.json").read_text("utf-8"))
    if (identity.get("tag") != TAG or identity.get("releaseVersion") != "0.3.0-rc.2"
            or identity.get("specVersion") != "0.3.0" or identity.get("maturity") != "draft"
            or not re.fullmatch("[0-9a-f]{40}", identity.get("sourceCommit", ""))):
        engine.fail("capability-unsupported")
    for name, digest in inventory["files"].items():
        if "sha256:" + hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            engine.fail("capability-unsupported")
    return {"version": "0.3.0-rc.2", "revision": identity["sourceCommit"],
            "schemaSha256": inventory["schemaSha256"], "corpusSha256": inventory["corpusSha256"]}


@dataclass
class Selection:
    selector: dict[str, Any]
    raw: dict[int, tuple[str, int, int]] = field(default_factory=dict)
    documents: dict[int, int] = field(default_factory=dict)
    origin: str = "asserted"
    profiles_bytes: int = 0


CURRENT: ContextVar[Selection | None] = ContextVar("retained_column_selection", default=None)


def selected() -> bool:
    return CURRENT.get() is not None


def _plain(value: Any) -> Any:
    if hasattr(value, "literal"):
        return engine.Number(value.literal)
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


def begin(raw: bytes, required: tuple[str, ...] = ("preparation-verification",)) -> Selection:
    if len(raw) > 4096:
        engine.fail("input-over-bound")
    s = engine.parse(raw.decode("utf-8"))
    engine.closed(s, ["contract", "spec", "profile", "roles"])
    engine.closed(s["spec"], ["version", "revision", "schemaSha256", "corpusSha256"])
    try:
        expected = installed_spec()
    except (OSError, ValueError, KeyError, TypeError):
        engine.fail("capability-unsupported")
    if s["contract"] != "retained-column/1" or s["spec"] != expected or s["profile"] != "base":
        engine.fail("capability-unsupported")
    roles = s["roles"]
    if not isinstance(roles, list) or not roles or any(not isinstance(v, str) or v not in ROLES for v in roles):
        engine.fail("capability-unsupported")
    if len(set(roles)) != len(roles) or roles != [v for v in ROLES if v in roles]:
        engine.fail()
    if any(v not in roles for v in required):
        engine.fail("capability-unsupported")
    return Selection(s)


def remember(value: Any, text: str) -> None:
    """Retain token spans in the current operation, including array occurrences.

    JSON has already passed the host's strict reader. The scan never serializes a
    decoded value to recover raw custody and never searches by a frame digest.
    """
    context = CURRENT.get()
    if context is None:
        return
    decoder = json.JSONDecoder()
    def space(i: int) -> int:
        while i < len(text) and text[i] in " \t\r\n":
            i += 1
        return i
    def walk(v: Any, i: int) -> int:
        i = space(i)
        start = i
        if isinstance(v, dict):
            i = space(i + 1)
            for _ in v:
                name, i = decoder.raw_decode(text, i)
                i = space(i)
                i = walk(v[name], space(i + 1))
                i = space(i)
                if text[i] == ',':
                    i = space(i + 1)
            i += 1
            context.raw[id(v)] = (text, start, i)
        elif isinstance(v, list):
            i = space(i + 1)
            for member in v:
                i = space(walk(member, i))
                if text[i] == ',':
                    i = space(i + 1)
            i += 1
            context.raw[id(v)] = (text, start, i)
        else:
            _, i = decoder.raw_decode(text, i)
        return i
    walk(value, 0)
    context.documents[id(value)] = len(text.encode("utf-8"))


def raw_of(value: Any) -> str:
    context = CURRENT.get()
    if context is None or id(value) not in context.raw:
        engine.fail("read-failed")
    text, start, end = context.raw[id(value)]
    return text[start:end]


def rule(value: Any, availability: bool = False) -> dict[str, Any]:
    if not selected():
        engine.fail("capability-unsupported")
    p = _plain(value)
    if availability:
        engine.closed(p, ["contractVersion", "column"])
        p = {**p, "kind": "evidence-availability"}
    if not availability and p.get("kind") not in ("text", "decimal", "number", "boolean", "research-value"):
        engine.fail()
    # Validate the complete rule against a harmless frame, never record data.
    engine.validate(p, {"contractVersion": "1", "origin": "asserted", "values": {}, "research": None}, "base")
    return p


def application(host: Any, entry: dict[str, Any], value: Any, transformations: dict[str, Any], evidence: bool = False) -> Any:
    declaration = rule(entry["availability" if evidence else "conversion"], evidence)
    frame = host.resolve(value, entry["source"])
    if frame is host.ABSENT:
        raise host.Finding("read-failed", "the selected retained frame is missing")
    context = CURRENT.get()
    assert context is not None
    expected_origin = context.origin
    if not isinstance(frame, dict) or frame.get("origin") != expected_origin:
        raise host.Finding("read-failed", "retained frame origin differs from its bound occurrence")
    fragment = engine.lineage({"rule": declaration, "frame": _plain(frame), "profile": "base"}, raw_of(frame))
    key = ("evidence:" if evidence else "fact:") + entry["requirement" if evidence else "target"]
    transformations[key] = fragment
    if fragment["result"]["state"] == "omitted":
        return host.ABSENT
    return host.read_document(fragment["result"]["json"].encode("utf-8"), "converted candidate")


def capabilities(entries: Any, spec: dict[str, Any], required: str | None = None, producer: bool = False) -> dict[str, int] | None:
    if not isinstance(entries, list) or len(entries) > 32:
        engine.fail()
    seen = set()
    limits = None
    for entry in entries:
        engine.closed(entry, ["contract", "spec", "profile", "role", "limits"], ["producerGrammar"])
        engine.closed(entry["spec"], ["version", "revision", "schemaSha256", "corpusSha256"])
        role = entry["role"]
        if entry["contract"] != "retained-column/1" or entry["spec"] != spec or entry["profile"] != "base" or role not in ROLES:
            engine.fail("capability-unsupported")
        grammar = entry.get("producerGrammar")
        if grammar is not None and (role not in ("preparation", "preparation-verification", "producer-carrier") or grammar != "desk-reviewed-input/1"):
            engine.fail("capability-unsupported")
        identity = (role, grammar)
        if identity in seen:
            engine.fail()
        seen.add(identity)
        engine.closed(entry["limits"], engine.ROLE_LIMITS[role])
        for name, maximum in entry["limits"].items():
            engine.positive(maximum)
        if role == required and (not producer or grammar == "desk-reviewed-input/1"):
            limits = {k: min(CAPS["base"][k], engine.positive(v)) for k, v in entry["limits"].items()}
    if required and limits is None:
        engine.fail("capability-unsupported")
    return limits



def profile(host: Any, p: dict[str, Any]) -> None:
    context = CURRENT.get()
    assert context is not None
    if "conversionContracts" in p:
        capabilities(_plain(p["conversionContracts"]), context.selector["spec"])
    if "retainedColumnProducer" in p:
        engine.closed(p["retainedColumnProducer"], ["contractVersion", "grammar"])
        if p["retainedColumnProducer"] != {"contractVersion": "1", "grammar": "desk-reviewed-input/1"}:
            engine.fail("capability-unsupported")


def producer(host: Any, source: Any, p: dict[str, Any], response: Any = None) -> None:
    copies = source.read.copy or {"facts": [], "evidence": []}
    leaves = [e for e in copies["facts"] if "conversion" in e] + [e for e in copies["evidence"] if "availability" in e]
    if not leaves:
        return
    context = CURRENT.get()
    assert context is not None
    if "producer-carrier" not in context.selector["roles"]:
        engine.fail("capability-unsupported")
    if p.get("retainedColumnProducer") is None or p.get("conversionContracts") is None:
        engine.fail("capability-unsupported")
    trust = {k: _plain(p.get(k)) for k in ("id", "class", "source", "authority", "shape", "endpoint", "adapter", "tools", "retainedColumnProducer")}
    trust["profileDigest"] = host.digest_of(host.canon(p))
    binding = {"kind": source.kind, "profile": source.profile_id, "profileDigest": source.profile_digest}
    engine.producer_context(trust, binding)
    limits = capabilities(_plain(p.get("conversionContracts")), context.selector["spec"], "producer-carrier", True)
    assert limits is not None
    if context.profiles_bytes > limits["profilesBytes"]:
        engine.fail("input-over-bound")
    if source.read.unwrap or source.calculation is not None or any(e["source"] != "/retained" for e in leaves):
        raise host.Finding("profile-mismatch", "generated conversion must read the directly bound retained carrier")
    if response is None:
        return
    context.origin = "generated"
    carrier = response["result"]
    text = raw_of(carrier)
    if context.documents.get(id(response), len(raw_of(response).encode("utf-8"))) > limits["responseBytes"]:
        engine.fail("input-over-bound")
    first = leaves[0]
    declaration = rule(first.get("conversion", first.get("availability")), "availability" in first)
    engine.generated_consistency({"carrier": _plain(carrier), "profile": "base",
        "limits": {"originalSnapshotBytes": engine.Number(str(limits["originalSnapshotBytes"])), "carrierBytes": engine.Number(str(limits["carrierBytes"]))},
        "trustedProducer": trust, "sourceBinding": binding,
        "receiptResultDigest": response["receipt"]["resultDigest"], "rule": declaration}, text)


def restore_acquisitions(host: Any, acquisitions: Any) -> None:
    if not isinstance(acquisitions, dict):
        return
    for name, source in acquisitions.items():
        if not isinstance(source, dict) or "retainedResponseJson" not in source:
            continue
        engine.closed(source, ["retainedResponseJson"])
        text = source["retainedResponseJson"]
        if not isinstance(text, str) or not text:
            engine.fail()
        if len(text.encode("utf-8")) > CAPS["base"]["responseBytes"]:
            engine.fail("input-over-bound")
        response = host.read_document(text.encode("utf-8"), "retained signed response")
        engine.closed(response, ["result", "receipt", "salts"])
        acquisitions[name] = {"response": response}


def restore_case(host: Any, case: Any) -> Any:
    if isinstance(case, dict) and "retainedCaseJson" in case:
        engine.closed(case, ["retainedCaseJson"])
        text = case["retainedCaseJson"]
        if not isinstance(text, str) or not text:
            engine.fail()
        value = host.read_document(text.encode("utf-8"), "retained case", host.MAX_VALUE_DEPTH)
        if not isinstance(value, dict):
            engine.fail()
        return value
    return case


def source_documents(host: Any, raw: bytes) -> tuple[bytes, bytes, bytes, bytes | None]:
    """Read a complete persisted SourceInput, counting both mapping documents once.

    The selector is explicit and already installed before this larger read. The input's
    selector must independently agree; neither body contents nor a preparation opts in.
    """
    context = CURRENT.get()
    assert context is not None
    if len(raw) > CAPS['base']['combinedBytes']:
        engine.fail('input-over-bound')
    source = host.read_document(raw, 'selected source input')
    engine.closed(source, ['conversionContract', 'mapping'],
                  ['case', 'retainedCaseJson', 'sources', 'import', 'snapshot', 'mappingDigest'])
    begin(host.preparation_bytes(source['conversionContract']))
    if source['conversionContract'] != context.selector:
        engine.fail('capability-unsupported')
    if 'case' in source and 'retainedCaseJson' in source:
        engine.fail()
    if not isinstance(source['mapping'], dict) or ('sources' in source and not isinstance(source['sources'], dict)) or ('case' in source and not isinstance(source['case'], dict)):
        engine.fail()
    mapping = raw_of(source['mapping']).encode('utf-8')
    if len(mapping) > CAPS['base']['documentBytes']:
        engine.fail('input-over-bound')
    if 'mappingDigest' in source and source['mappingDigest'] != host.digest_of(host.canon(source['mapping'])):
        raise host.Finding('read-failed', 'stored mapping differs from its digest')
    if 'retainedCaseJson' in source:
        case = host.preparation_bytes({'retainedCaseJson': source['retainedCaseJson']})
    elif 'case' in source:
        case = raw_of(source['case']).encode('utf-8') if isinstance(source['case'], (dict, list)) else host.preparation_bytes(source['case'])
    else:
        case = b'{}'
    acquisitions = raw_of(source['sources']).encode('utf-8') if 'sources' in source else b'{}'
    binding = None
    if 'import' in source:
        imported = source['import']
        engine.closed(imported, ['dialect', 'binding'])
        if not isinstance(imported['dialect'], dict) or not isinstance(imported['binding'], dict):
            engine.fail()
        published = raw_of(imported['dialect']).encode('utf-8')
        binding = raw_of(imported['binding']).encode('utf-8')
        if len(published) > CAPS['base']['documentBytes'] or len(binding) > host.BINDING_BYTES:
            engine.fail('input-over-bound')
        bound = host.read_bound(host.parse_dialect(imported['dialect']), imported['binding'], True).document
        if host.canon(bound) != host.canon(source['mapping']):
            raise host.Finding('read-failed', 'retained published and bound mappings differ')
        mapping = published
    return mapping, case, acquisitions, binding


def export_inputs(host: Any, raw: bytes) -> tuple[list[tuple[bytes, bytes]], bytes]:
    """Measure the actual selected wire, stores, base projection and sidecars.

    Record signature/chain authority remains the existing consumer's separate contract;
    this adapter returns preparation agreement, never a record-signature claim.
    """
    import base64
    if len(raw) > CAPS['base']['exportWireBytes']:
        engine.fail('input-over-bound')
    document = host.read_document(raw, 'selected verification export')
    engine.closed(document, ['version', 'releaseDigest', 'release', 'run'], ['chain'])
    if not host.is_integer(document['version']) or host.integer_of(document['version']) not in (2, 3, 4, 5):
        engine.fail()
    version = host.integer_of(document['version'])
    release, run = document['release'], document['run']
    if not isinstance(release, dict) or not isinstance(run, dict):
        engine.fail()
    if (len(raw_of(release).encode()) > CAPS['base']['releaseStoredBytes']
            or len(raw_of(run).encode()) > CAPS['base']['runStoredBytes']):
        engine.fail('input-over-bound')
    if (version >= 3 and 'auditBytes' not in run or version >= 4 and 'chain' not in document or version == 5 and 'auditSignatures' not in run):
        engine.fail()
    base = len(raw)
    def binary(member: str, cap: int, minimum: int) -> bytes | None:
        nonlocal base
        if member not in run:
            return None
        if version < minimum or not isinstance(run[member], str):
            engine.fail()
        try:
            data = base64.b64decode(run[member], validate=True)
        except (ValueError, TypeError):
            engine.fail()
        if len(data) > cap:
            engine.fail('input-over-bound')
        # Subtract only mandatory punctuation and the exact received string token.
        # Additional whitespace remains conservatively charged to the base artifact.
        member_text = dict(host.top_level_members(raw_of(run)))[member]
        base -= len(member_text.encode()) + len(json.dumps(member)) + 2
        return data
    audit = binary('auditBytes', CAPS['base']['recordBytes'], 3)
    binary('auditSignatures', 16384, 5)
    if 'chain' in document:
        if version < 4:
            engine.fail()
        chain = document['chain']
        engine.closed(chain, ['entry', 'checkpoint'])
        if not isinstance(chain['entry'], str):
            engine.fail()
        try:
            entry = base64.b64decode(chain['entry'], validate=True)
        except (ValueError, TypeError):
            engine.fail()
        checkpoint = chain['checkpoint']
        engine.closed(checkpoint, ['checkpointVersion', 'recordDigest', 'sequence', 'trail'])
        if len(entry) > 1024 or len(raw_of(checkpoint).encode()) > 185:
            engine.fail('input-over-bound')
        base -= len(raw_of(chain).encode()) + len(',"chain":')
    if base > CAPS['base']['exportBaseBytes']:
        engine.fail('input-over-bound')
    if audit is None:
        if not isinstance(run.get('audit'), dict):
            engine.fail()
        audit = raw_of(run['audit']).encode('utf-8')
    if len(audit) > CAPS['base']['recordBytes']:
        engine.fail('input-over-bound')
    if not isinstance(run.get('audit'), dict) or host.preparation_bytes(host.read_document(audit, 'retained audit')) != host.preparation_bytes(run['audit']):
        raise host.Finding('record-inputs-differ', 'visible audit differs from retained audit bytes')
    # Keep the existing recorded-Core version/schema checks. This does not verify a
    # signature sidecar or chain: the report makes no such authority claim.
    host.recording_of_export(raw)
    retained = []
    for parent, member in ((release, 'sample'), (run, 'input')):
        inp = parent.get(member)
        if not isinstance(inp, dict) or not isinstance(inp.get('source'), dict) or not isinstance(inp.get('preparation'), dict):
            engine.fail()
        retained.append((raw_of(inp['source']).encode(), raw_of(inp['preparation']).encode()))
    mapping = release.get("inputMapping")
    if not isinstance(mapping, dict):
        engine.fail()
    if len(raw_of(mapping).encode()) > CAPS["base"]["documentBytes"]:
        engine.fail("input-over-bound")
    for parent, member in ((release, "sample"), (run, "input")):
        if host.canon(parent[member]["source"]["mapping"]) != host.canon(mapping):
            raise host.Finding("read-failed", "release mapping differs from retained input mapping")
    return retained, audit

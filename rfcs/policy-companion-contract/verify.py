#!/usr/bin/env python3
"""Offline checker for the PROPOSED DRAFT Policy companion 1.0.0, never authority."""

import argparse
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import dialect_verify as spec_canon

MAX_DOCUMENT_BYTES = 262144
MAX_MATERIAL_BYTES = 1048576
MAX_ORIGINAL_BYTES = 4194304
MAX_TOTAL_MATERIAL_BYTES = 16777216
MAX_MATERIALS = 16
MAX_DEPTH = 32
VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", re.ASCII)
FORMAT_VERSION = "1.0.0"
VALID = {"status": "valid", "formatVersion": FORMAT_VERSION, "maturity": "proposed-draft"}
CODES = (
    "input-over-bound", "invalid-json", "invalid-selector", "unsupported-format",
    "invalid-document", "missing-material", "reference-mismatch", "invalid-anchor",
    "invalid-coverage", "invalid-consumer", "unsupported-canonical-identity", "invalid-carrier",
)
CAPABILITY = {
    "capability": "jps-policy-companion-offline",
    "maturity": "proposed-draft",
    "formatVersions": [FORMAT_VERSION],
    "consumerSpecVersions": ["0.2.0-draft"],
    "kinds": ["policy", "governing-adoption"],
    "features": ["exact-byte-sha256", "utf8-section-anchors", "scoped-total-coverage",
                 "typed-core-pack-references", "optional-jps-canon-identity", "multiple-media-types"],
    "limits": {"documentBytes": MAX_DOCUMENT_BYTES, "documentDepth": MAX_DEPTH,
               "numberLiteralCharacters": 128, "exponentMagnitude": 308,
               "materialBytes": MAX_MATERIAL_BYTES, "originalBytes": MAX_ORIGINAL_BYTES,
               "distinctRetainedBytes": MAX_TOTAL_MATERIAL_BYTES, "materialRegistrations": MAX_MATERIALS,
               "versionCharacters": 256, "sections": 64, "sources": 16, "governingPolicies": 16,
               "consumerElementsPerSection": 64, "textCharacters": 4096, "uriCharacters": 2048,
               "localIdCharacters": 128, "mediaTypeCharacters": 128, "sourceRefsPerSection": 16,
               "scopeSectionIds": 64, "coverageRecordsPerPolicy": 64, "informationalSources": 16,
               "canonicalIntegerMagnitude": 9007199254740991},
    "excludes": ["adopted-or-stable-format", "graph-consumers", "evaluation", "full-core-semantics",
                 "signatures", "review-assertion-trust", "live-authority", "permissions", "currency",
                 "source-fetch", "automatic-migration", "independent-interoperability-evidence"],
    "refusalCodes": list(CODES),
}


class ContractError(ValueError):
    """Finite safe code only: never include retained input in public diagnostics."""
    def __init__(self, code):
        assert code in CODES
        super().__init__(code)
        self.code = code


def require(condition, code):
    if not condition:
        raise ContractError(code)


def identity(data, media_type):
    return {"bytesDigest": spec_canon.digest_of(data), "byteLength": len(data), "mediaType": media_type}


def strict_json(data):
    require(len(data) <= MAX_DOCUMENT_BYTES, "input-over-bound")
    try:
        return spec_canon.read_document(data, "candidate document", MAX_DEPTH)
    except spec_canon.Refused as error:
        raise ContractError("input-over-bound" if error.name == "input-over-bound" else "invalid-json") from error


def plain(value):
    if isinstance(value, spec_canon.Num):
        return int(value.literal)
    if isinstance(value, dict):
        return {key: plain(child) for key, child in value.items()}
    if isinstance(value, list):
        return [plain(child) for child in value]
    return value


def canon_document(value):
    try:
        spec_canon.canon(value)
        return plain(value)
    except spec_canon.OutsideDomain as error:
        raise ContractError("invalid-document") from error


def read_json(data):
    """For local schemas/carriers; companion reading additionally selects format first."""
    return canon_document(strict_json(data))


def select_format(document):
    require(isinstance(document, dict), "invalid-selector")
    selector = document.get("formatVersion")
    require(isinstance(selector, str) and len(selector) <= 256 and VERSION.fullmatch(selector), "invalid-selector")
    require(selector == FORMAT_VERSION, "unsupported-format")


def read_companion(data):
    value = strict_json(data)
    select_format(value)  # No schema, identity interpretation, or migration before exact dispatch.
    return canon_document(value)


def canonical_identity(data):
    try:
        value = strict_json(data)
        digest = spec_canon.digest_of(spec_canon.canon(value))
    except (ContractError, spec_canon.OutsideDomain) as error:
        if isinstance(error, ContractError) and error.code == "input-over-bound":
            raise
        raise ContractError("unsupported-canonical-identity") from error
    return {"profile": "jps-canon", "canonicalDigest": digest}


def core_schema_view(value):
    if isinstance(value, spec_canon.Num):
        number = value.value  # Exact Decimal, without float rounding or canon restriction.
        return int(number) if number == number.to_integral_value() else number
    if isinstance(value, dict):
        return {key: core_schema_view(child) for key, child in value.items()}
    if isinstance(value, list):
        return [core_schema_view(child) for child in value]
    return value


def validators():
    schemas = {name: read_json((HERE / (name + ".schema.json")).read_bytes())
               for name in ("common", "policy", "governing-adoption", "fixture", "vectors")}
    registry = Registry().with_resources((schema["$id"], Resource.from_contents(schema)) for schema in schemas.values())
    schemas["core"] = read_json((ROOT / "schema/judgment-pack-core.schema.json").read_bytes())
    checker = FormatChecker()
    if "uri" not in checker.checkers or checker.conforms("not a URI", "uri"):
        raise RuntimeError("Install pinned requirements-dev.txt URI dependencies")
    result = {}
    for name, schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        result[name] = Draft202012Validator(schema, registry=registry, format_checker=checker)
    return result


VALIDATORS = None


def check_schema(name, document):
    global VALIDATORS
    if VALIDATORS is None:
        VALIDATORS = validators()
    errors = list(VALIDATORS[name].iter_errors(core_schema_view(document) if name == "core" else document))
    # Schema maxima are resource refusals; required/type/enum/minimum failures are semantic.
    def over(error):
        return error.validator in ("maxItems", "maxLength", "maximum") or any(over(child) for child in error.context)
    if any(over(error) for error in errors):
        raise ContractError("input-over-bound")
    require(not errors, "invalid-consumer" if name == "core" else "invalid-carrier" if name == "fixture" else "invalid-document")


def unique_by_id(items, code):
    result = {}
    for item in items:
        require(item["id"] not in result, code)
        result[item["id"]] = item
    return result


def register_material(reference, raw, material):
    check_schema("common", reference)
    require(len(raw) <= MAX_ORIGINAL_BYTES, "input-over-bound")
    entry = material.get(reference["bytesDigest"])
    require(entry is None or entry[0] == raw, "reference-mismatch")
    require(identity(raw, reference["mediaType"]) == reference, "reference-mismatch")
    total = sum(len(value[0]) for value in material.values())
    require(total + (len(raw) if entry is None else 0) <= MAX_TOTAL_MATERIAL_BYTES, "input-over-bound")
    media_types = {reference["mediaType"]}
    if entry is not None:
        media_types.update(entry[1])
    material[reference["bytesDigest"]] = (entry[0] if entry is not None else raw, media_types)


def resolve(reference, material, limit=MAX_MATERIAL_BYTES):
    check_schema("common", reference)
    require(reference["byteLength"] <= limit, "input-over-bound")
    entry = material.get(reference["bytesDigest"])
    require(entry is not None, "missing-material")
    require(reference["mediaType"] in entry[1], "reference-mismatch")
    require(identity(entry[0], reference["mediaType"]) == reference, "reference-mismatch")
    return entry[0]


def check_artifact(reference, kind, material):
    require(reference["kind"] == kind, "reference-mismatch")
    require(reference["content"]["mediaType"] == "application/json", "invalid-document")
    raw = resolve(reference["content"], material, MAX_DOCUMENT_BYTES)
    document = strict_json(raw) if kind == "pack" else read_companion(raw)
    require(isinstance(document, dict), "invalid-consumer" if kind == "pack" else "invalid-document")
    require(reference["id"] == document.get("id") and reference["version"] == document.get("version"), "reference-mismatch")
    if "canonicalIdentity" in reference:
        require(reference["canonicalIdentity"] == canonical_identity(raw), "reference-mismatch")
    return document


def check_policy(document, material):
    select_format(document)
    check_schema("policy", document)
    narrative = resolve(document["content"], material)
    require(document["content"]["mediaType"] == "text/plain", "invalid-document")
    try:
        narrative.decode("utf-8")
    except UnicodeError as error:
        raise ContractError("invalid-anchor") from error
    sources = unique_by_id(document["sourceProvenance"], "invalid-document")
    for source in sources.values():
        resolve(source["content"], material, MAX_ORIGINAL_BYTES)
    sections = unique_by_id(document["sections"], "invalid-anchor")
    for section in sections.values():
        anchor = section["anchor"]
        start, end = anchor["startByte"], anchor["endByte"]
        require(0 <= start < end <= len(narrative), "invalid-anchor")
        try:
            narrative[:start].decode("utf-8")
            narrative[start:end].decode("utf-8")
        except UnicodeError as error:
            raise ContractError("invalid-anchor") from error
        require(spec_canon.digest_of(narrative[start:end]) == anchor["bytesDigest"], "invalid-anchor")
        for source_ref in section.get("sourceRefs", []):
            require(source_ref["sourceId"] in sources, "invalid-anchor")
    return sections


def check_adoption(document, material):
    select_format(document)
    check_schema("governing-adoption", document)
    consumer = check_artifact(document["consumer"], "pack", material)
    check_schema("core", consumer)
    rules = unique_by_id(consumer["rules"], "invalid-consumer")
    exceptions = unique_by_id(consumer.get("exceptions", []), "invalid-consumer")
    outcomes = unique_by_id(consumer["outcomes"], "invalid-consumer")
    if "fallbackOutcome" in consumer:
        require(consumer["fallbackOutcome"] in outcomes, "invalid-consumer")
    for exception in exceptions.values():
        if "targetRule" in exception:
            require(exception["targetRule"] in rules, "invalid-consumer")
        if "outcome" in exception:
            require(exception["outcome"] in outcomes, "invalid-consumer")
    policies = set()
    for governing in document["governingPolicies"]:
        reference = governing["policy"]
        policy = check_artifact(reference, "policy", material)
        sections = check_policy(policy, material)
        require(reference["id"] not in policies, "invalid-coverage")
        policies.add(reference["id"])
        scope = governing["scope"]
        selected = set(sections) if scope["kind"] == "whole-policy" else set(scope["sectionIds"])
        require(selected.issubset(sections), "invalid-coverage")
        if scope["kind"] == "sections":
            resolve(scope["reviewBasis"], material)
        seen = set()
        for coverage in governing["coverage"]:
            section_id = coverage["sectionId"]
            require(section_id in selected and section_id not in seen, "invalid-coverage")
            seen.add(section_id)
            if coverage["status"] == "implemented":
                elements_seen = set()
                for element in coverage["consumerElements"]:
                    kind = element["kind"]
                    key = (kind, element.get("id"))
                    require(key not in elements_seen, "invalid-coverage")
                    elements_seen.add(key)
                    if kind in ("rule", "exception"):
                        require(element["id"] in (rules if kind == "rule" else exceptions), "invalid-coverage")
                    else:
                        require(("applicability" if kind == "applicability" else "fallbackOutcome") in consumer, "invalid-coverage")
                resolve(coverage["reviewBasis"], material)
        require(seen == selected, "invalid-coverage")
    for source in document.get("informationalSources", []):
        resolve(source, material)


def check_document(raw, material):
    document = read_companion(raw)
    kind = document.get("kind")
    require(kind in ("policy", "governing-adoption"), "invalid-document")
    (check_policy if kind == "policy" else check_adoption)(document, material)


def verify_input(raw, registrations, load_material=None):
    """Check bytes pairs, or acquire each carrier source lazily through a supplied loader."""
    def check():
        document = read_companion(raw)
        require(len(registrations) <= MAX_MATERIALS, "input-over-bound")
        material = {}
        for reference, retained in registrations:
            raw_material = retained if load_material is None else load_material(retained)
            register_material(reference, raw_material, material)
        kind = document.get("kind")
        require(kind in ("policy", "governing-adoption"), "invalid-document")
        (check_policy if kind == "policy" else check_adoption)(document, material)
    return result(check)


def result(callback):
    try:
        callback()
    except ContractError as error:
        return {"status": "refused", "code": error.code}
    return dict(VALID)


def read_local(path, limit):
    try:
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
    except OSError as error:
        raise ContractError("missing-material") from error
    require(len(raw) <= limit, "input-over-bound")
    return raw


def local_path(directory, name, allow_nested=False):
    require(isinstance(name, str) and "\x00" not in name, "invalid-carrier")
    try:
        require(not Path(name).is_absolute(), "invalid-carrier")
        path = (directory / name).resolve()
    except (ValueError, OSError, RuntimeError) as error:
        raise ContractError("invalid-carrier") from error
    require(path.is_relative_to(directory) if allow_nested else path.parent == directory, "invalid-carrier")
    return path


def load_bundle(directory):
    """Local synthetic fixture carrier, never a release or dependency-closure protocol."""
    directory = Path(directory).resolve()
    manifest = read_json(read_local(directory / "fixture.json", MAX_DOCUMENT_BYTES))
    check_schema("fixture", manifest)
    material, by_path = {}, {}
    for entry in manifest["materials"]:
        name, reference = entry["path"], entry["content"]
        require(name not in by_path, "invalid-carrier")
        path = local_path(directory, name)
        remaining = MAX_TOTAL_MATERIAL_BYTES - sum(len(value[0]) for value in material.values())
        limit = MAX_ORIGINAL_BYTES if reference["bytesDigest"] in material else min(MAX_ORIGINAL_BYTES, remaining)
        raw = read_local(path, limit)
        register_material(reference, raw, material)
        by_path[name] = raw
    for role in ("policy", "consumer", "adoption"):
        require(manifest[role] in by_path, "missing-material")
    return manifest, material, by_path


def verify_bundle(directory):
    def check():
        manifest, material, by_path = load_bundle(directory)
        policy = read_companion(by_path[manifest["policy"]])
        check_policy(policy, material)
        adoption = read_companion(by_path[manifest["adoption"]])
        check_adoption(adoption, material)
        policy_content = identity(by_path[manifest["policy"]], "application/json")
        require(any(item["policy"]["content"] == policy_content for item in adoption["governingPolicies"]), "reference-mismatch")
        require(adoption["consumer"]["content"] == identity(by_path[manifest["consumer"]], "application/json"), "reference-mismatch")
    return result(check)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capabilities", action="store_true")
    parser.add_argument("directory", type=Path, nargs="?")
    args = parser.parse_args(argv)
    if args.capabilities:
        answer = CAPABILITY
    elif args.directory is not None:
        answer = verify_bundle(args.directory)
    else:
        parser.error("supply one fixture directory or --capabilities")
    print(json.dumps(answer, ensure_ascii=True, separators=(",", ":")))
    return 1 if answer.get("status") == "refused" else 0


if __name__ == "__main__":
    sys.exit(main())

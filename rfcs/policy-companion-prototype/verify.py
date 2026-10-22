#!/usr/bin/env python3
"""Offline checks for a NON-NORMATIVE RFC prototype; no authority or service calls."""

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
import dialect_verify as spec_canon  # Existing Spec strict reader and canon, not a new profile.

MAX_DOCUMENT_BYTES = 262144
MAX_MATERIAL_BYTES = 1048576
MAX_ORIGINAL_BYTES = 4194304
MAX_TOTAL_MATERIAL_BYTES = 16777216
MAX_DEPTH = 32
VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", re.ASCII)
PROFILE = {"profile": "jps-policy-companion-prototype", "proposalVersion": "0.0.2", "status": "non-normative"}


class PrototypeError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise PrototypeError(message)


def read_local(path, limit, message="local file byte bound exceeded"):
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, message)
    return data


def parse_version(value):
    """Current artifact grammar/bound; no component limit or compatibility policy."""
    require(isinstance(value, str) and len(value) <= 256 and VERSION.fullmatch(value), "invalid artifact version")
    return tuple(int(component) for component in value.split("."))


def plain(value):
    if isinstance(value, spec_canon.Num):
        return int(value.literal)
    if isinstance(value, dict):
        return {key: plain(child) for key, child in value.items()}
    if isinstance(value, list):
        return [plain(child) for child in value]
    return value


def read_json(data):
    require(len(data) <= MAX_DOCUMENT_BYTES, "document byte bound exceeded")
    try:
        value = spec_canon.read_document(data, "prototype document", MAX_DEPTH)
        spec_canon.canon(value)  # Refuse floats/exponents/unsafe integers before conversion.
        return plain(value)
    except (spec_canon.Refused, spec_canon.OutsideDomain, UnicodeError) as error:
        raise PrototypeError("invalid JSON/canon domain: " + str(error)) from error


def read_core_json(data):
    """Read exact Core numbers as literals; Core does not require the canon domain."""
    require(len(data) <= MAX_DOCUMENT_BYTES, "unsupported prototype consumer byte bound")
    try:
        return spec_canon.read_document(data, "consumer pack", MAX_DEPTH)
    except spec_canon.Refused as error:
        detail = "unsupported prototype consumer bound" if error.name == "input-over-bound" else "invalid consumer JSON"
        raise PrototypeError(detail + ": " + str(error)) from error


def core_schema_view(value):
    """Exact numeric values for JSON Schema; retain literals/raw bytes separately."""
    if isinstance(value, spec_canon.Num):
        number = value.value  # Decimal constructed from the literal, with no float rounding.
        return int(number) if number == number.to_integral_value() else number
    if isinstance(value, dict):
        return {key: core_schema_view(child) for key, child in value.items()}
    if isinstance(value, list):
        return [core_schema_view(child) for child in value]
    return value


def identity(data, media_type):
    return {"bytesDigest": spec_canon.digest_of(data), "byteLength": len(data), "mediaType": media_type}


def canonical_identity(data):
    try:
        value = read_json(data)
    except PrototypeError as error:
        raise PrototypeError("unsupported requested jps-canon identity: " + str(error)) from error
    return {"profile": "jps-canon", "canonicalDigest": spec_canon.digest_of(spec_canon.canon(value))}


def validators():
    schemas = {name: read_json((HERE / (name + ".schema.json")).read_bytes()) for name in ("common", "policy", "governing-adoption")}
    registry = Registry().with_resources((schema["$id"], Resource.from_contents(schema)) for schema in schemas.values())
    schemas["core"] = read_json((ROOT / "schema/judgment-pack-core.schema.json").read_bytes())
    checker = FormatChecker()
    require("uri" in checker.checkers, "install requirements-dev.txt URI format dependencies")
    require(not checker.conforms("not a URI", "uri"), "URI assertion unavailable")
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
    schema_view = core_schema_view(document) if name == "core" else document
    errors = sorted(VALIDATORS[name].iter_errors(schema_view), key=lambda error: str(list(error.path)))
    if errors:
        error = errors[0]
        raise PrototypeError("%s schema %s: %s" % (name, list(error.path), error.message))


def unique_by_id(items, what):
    result = {}
    for item in items:
        require(item["id"] not in result, "duplicate " + what + " id")
        result[item["id"]] = item
    return result


def register_material(reference, raw, material):
    """Register a typed reference; a shared byte digest need not have one media type."""
    check_schema("common", reference)
    key = reference["bytesDigest"]
    entry = material.get(key)
    require(entry is None or entry[0] == raw, "conflicting retained material bytes")
    require(identity(raw, reference["mediaType"]) == reference, "retained byte identity/media type mismatch")
    total = sum(len(value[0]) for value in material.values())
    require(total + (len(raw) if entry is None else 0) <= MAX_TOTAL_MATERIAL_BYTES,
            "aggregate retained byte bound exceeded")
    media_types = {reference["mediaType"]}
    if entry is not None:
        media_types.update(entry[1])
    material[key] = (entry[0] if entry is not None else raw, media_types)


def resolve(reference, material, limit=MAX_MATERIAL_BYTES):
    # Carrier registration does not grant permission to exceed a consuming role's bound.
    check_schema("common", reference)
    require(reference["byteLength"] <= limit, "retained material role byte bound exceeded")
    entry = material.get(reference["bytesDigest"])
    require(entry is not None, "missing retained material")
    require(reference["mediaType"] in entry[1], "unregistered retained material media type")
    require(identity(entry[0], reference["mediaType"]) == reference, "retained byte identity/media type mismatch")
    return entry[0]


def check_artifact(reference, kind, material):
    require(reference["kind"] == kind, "wrong artifact kind")
    parse_version(reference["version"])
    require(reference["content"]["mediaType"] == "application/json", "artifact is not JSON")
    raw = resolve(reference["content"], material)
    document = read_core_json(raw) if kind == "pack" else read_json(raw)
    require(isinstance(document, dict), "artifact JSON root is not an object")
    require(reference["id"] == document.get("id") and reference["version"] == document.get("version"), "artifact identity mismatch")
    if "canonicalIdentity" in reference:
        require(reference["canonicalIdentity"] == canonical_identity(raw), "canonical identity mismatch")
    return document


def check_policy(document, material):
    check_schema("policy", document)
    parse_version(document["version"])
    narrative = resolve(document["content"], material)
    require(document["content"]["mediaType"] == "text/plain", "narrative must be text/plain")
    try:
        narrative.decode("utf-8")
    except UnicodeError as error:
        raise PrototypeError("narrative is not UTF-8") from error
    sources = unique_by_id(document["sourceProvenance"], "source")
    for source in sources.values():
        resolve(source["content"], material, MAX_ORIGINAL_BYTES)  # Never narrative offsets.
    sections = unique_by_id(document["sections"], "section")
    for section in sections.values():
        anchor = section["anchor"]
        start, end = anchor["startByte"], anchor["endByte"]
        require(0 <= start < end <= len(narrative), "section range outside narrative")
        try:
            narrative[:start].decode("utf-8")
            narrative[start:end].decode("utf-8")
        except UnicodeError as error:
            raise PrototypeError("section range splits a UTF-8 sequence") from error
        require(spec_canon.digest_of(narrative[start:end]) == anchor["bytesDigest"], "section anchor digest mismatch")
        for source_ref in section.get("sourceRefs", []):
            require(source_ref["sourceId"] in sources, "unknown section source")
    return sections


def check_adoption(document, material):
    check_schema("governing-adoption", document)
    parse_version(document["version"])
    consumer = check_artifact(document["consumer"], "pack", material)
    check_schema("core", consumer)  # Existing Core schema unchanged; no evaluator claim.
    rules = unique_by_id(consumer["rules"], "consumer rule")
    exceptions = unique_by_id(consumer.get("exceptions", []), "consumer exception")
    outcomes = unique_by_id(consumer["outcomes"], "consumer outcome")
    if "fallbackOutcome" in consumer:
        require(consumer["fallbackOutcome"] in outcomes, "unknown consumer fallback outcome")
    for exception in exceptions.values():
        if "targetRule" in exception:
            require(exception["targetRule"] in rules, "unknown consumer exception target rule")
        if "outcome" in exception:
            require(exception["outcome"] in outcomes, "unknown consumer exception outcome")
    policies = set()
    for governing in document["governingPolicies"]:
        reference = governing["policy"]
        policy = check_artifact(reference, "policy", material)
        sections = check_policy(policy, material)
        require(reference["id"] not in policies, "duplicate governing policy identity")
        policies.add(reference["id"])
        scope = governing["scope"]
        selected = set(sections) if scope["kind"] == "whole-policy" else set(scope["sectionIds"])
        require(selected.issubset(sections), "scope references unknown section")
        if scope["kind"] == "sections":
            resolve(scope["reviewBasis"], material)
        seen = set()
        for coverage in governing["coverage"]:
            section_id = coverage["sectionId"]
            require(section_id in selected, "coverage outside declared scope")
            require(section_id not in seen, "duplicate section coverage")
            seen.add(section_id)
            if coverage["status"] == "implemented":
                elements_seen = set()
                for element in coverage["consumerElements"]:
                    kind = element["kind"]
                    key = (kind, element.get("id"))
                    require(key not in elements_seen, "duplicate consumer element reference")
                    elements_seen.add(key)
                    if kind in ("rule", "exception"):
                        collection = rules if kind == "rule" else exceptions
                        require(element["id"] in collection, "unknown consumer " + kind)
                    else:
                        member = "applicability" if kind == "applicability" else "fallbackOutcome"
                        require(member in consumer, "missing consumer " + kind)
                resolve(coverage["reviewBasis"], material)
        require(seen == selected, "coverage omits an in-scope section")
    for source in document.get("informationalSources", []):
        resolve(source, material)


def load_bundle(directory):
    """Fixture manifest is local test scaffolding, not a portable release envelope."""
    directory = Path(directory).resolve()
    manifest = read_json(read_local(directory / "fixture.json", MAX_DOCUMENT_BYTES))
    require(set(manifest) == {"prototype", "synthetic", "scenario", "materials", "policy", "consumer", "adoption"}, "unknown/missing fixture member")
    require(manifest["prototype"] == PROFILE and manifest["synthetic"] is True, "fixture must be explicitly synthetic and non-normative")
    require(isinstance(manifest["materials"], list) and 1 <= len(manifest["materials"]) <= 16, "fixture material count bound")
    material, by_path = {}, {}
    for entry in manifest["materials"]:
        require(set(entry) == {"path", "content"}, "unknown/missing material member")
        name = entry["path"]
        require(isinstance(name, str), "material path is not a string")
        path = (directory / name).resolve()
        require(path.parent == directory and not Path(name).is_absolute(), "material must be a local fixture file")
        require(name not in by_path, "duplicate material path")
        check_schema("common", entry["content"])
        existing = entry["content"]["bytesDigest"] in material
        remaining = MAX_TOTAL_MATERIAL_BYTES - sum(len(value[0]) for value in material.values())
        limit = MAX_ORIGINAL_BYTES if existing else min(MAX_ORIGINAL_BYTES, remaining)
        message = "aggregate retained byte bound exceeded" if limit < MAX_ORIGINAL_BYTES else "local file byte bound exceeded"
        raw = read_local(path, limit, message)
        register_material(entry["content"], raw, material)
        by_path[name] = material[entry["content"]["bytesDigest"]][0]
    for name in ("policy", "consumer", "adoption"):
        require(isinstance(manifest[name], str) and manifest[name] in by_path, "missing fixture document")
    return manifest, material, read_json(by_path[manifest["policy"]]), read_json(by_path[manifest["adoption"]])


def verify_bundle(directory):
    manifest, material, policy, adoption = load_bundle(directory)
    check_policy(policy, material)
    check_adoption(adoption, material)
    expected_policy = identity(read_local(Path(directory) / manifest["policy"], MAX_DOCUMENT_BYTES), "application/json")
    require(any(item["policy"]["content"] == expected_policy for item in adoption["governingPolicies"]), "fixture policy is not adopted")
    expected_consumer = identity(read_local(Path(directory) / manifest["consumer"], MAX_DOCUMENT_BYTES), "application/json")
    require(adoption["consumer"]["content"] == expected_consumer, "fixture consumer differs from adopted pack")
    return manifest["scenario"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", type=Path, nargs="*")
    args = parser.parse_args()
    directories = args.directories or sorted((HERE / "examples").iterdir())
    try:
        names = [verify_bundle(directory) for directory in directories]
    except (PrototypeError, OSError) as error:
        parser.exit(1, "Prototype check failed: %s\n" % error)
    print("Checked %s synthetic prototype bundles; no live authority or conformance claim." % len(names))

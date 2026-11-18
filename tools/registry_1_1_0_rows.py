"""Write the rows of registry format 1.1.0 (conformance/registry/1.1.0/) from the data in this file.

This is a generator, committed so that the rows can be reviewed as data and written again. Every
input document, every expected result and every diagnostic location below is written by hand from
spec/registry-1.1.0.md, which governs; nothing here reads a reader's output. The generator only lays
the data out as files and computes what is mechanical: digests (registry section 2.3, and section 4
step 2's content digests), resolution of a valid registry (registry section 8), source statements
(section 10.2), and Ed25519 signatures (RFC 8032) made with the published seeds of RFC 8032 section
7.1, TEST 1 to TEST 3. No other seed or private key exists in the rows or here.

Run it from anywhere: `python tools/registry_1_1_0_rows.py`. It rewrites manifest.json and every file
it names under conformance/registry/1.1.0/, and leaves README.md and codes.json alone. It reuses the
Ed25519 arithmetic of tools/dialect_verify.py and needs nothing beyond the standard library.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "conformance" / "registry" / "1.1.0"
OLD = ROOT / "conformance" / "registry" / "1.0.0"
KEEP = {"README.md", "codes.json"}

_spec = importlib.util.spec_from_file_location("dialect_verify", ROOT / "tools" / "dialect_verify.py")
ED = importlib.util.module_from_spec(_spec)
sys.modules["dialect_verify"] = ED
_spec.loader.exec_module(ED)

# RFC 8032 section 7.1: the published seeds of TEST 1, TEST 2 and TEST 3, with the public keys and the
# signatures the RFC gives for them, which the generator checks before it signs anything.
RFC8032 = {
    "TEST 1": ("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
               "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", "",
               "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
               "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
    "TEST 2": ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
               "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", "72",
               "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
               "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
    "TEST 3": ("c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
               "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025", "af82",
               "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac"
               "18ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a"),
}


def signer(name: str):
    seed, public_hex, message_hex, signature_hex = RFC8032[name]
    h = hashlib.sha512(bytes.fromhex(seed)).digest()
    a = int.from_bytes(h[:32], "little") & ((1 << 254) - 8) | (1 << 254)
    public = ED._encode(ED._multiply(a, ED.BASE))
    assert public.hex() == public_hex, name

    def sign(message: bytes) -> bytes:
        r = int.from_bytes(hashlib.sha512(h[32:] + message).digest(), "little") % ED.L
        encoded_r = ED._encode(ED._multiply(r, ED.BASE))
        k = int.from_bytes(hashlib.sha512(encoded_r + public + message).digest(), "little") % ED.L
        return encoded_r + ((r + k * a) % ED.L).to_bytes(32, "little")

    assert sign(bytes.fromhex(message_hex)).hex() == signature_hex, name
    return public_hex, sign


PK1, SIGN1 = signer("TEST 1")  # the standard owner, and a single registry's signer
PK2, SIGN2 = signer("TEST 2")  # the billing repository
PK3, SIGN3 = signer("TEST 3")  # a wrong key, and another repository
SMALL_ORDER_KEY = "01" + "00" * 31  # the identity point: of small order, refused by the trust rule

# ---------------------------------------------------------------------------------------------------
# Canonical form and digests (registry section 2.3), as tests/test_registry_companion.py writes them.


def number(value) -> str:
    if isinstance(value, int):
        assert abs(value) <= 2**53 - 1
        return str(value)
    double = float(value)
    assert Decimal(repr(double)) == value
    if double.is_integer() and abs(double) < 1e21:
        return str(int(double))
    return repr(double)


def jcs(value) -> str:
    if value is None or isinstance(value, bool):
        return json.dumps(value)
    if isinstance(value, (int, Decimal)):
        return number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ",".join(jcs(item) for item in value) + "]"
    keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
    return "{" + ",".join(json.dumps(key, ensure_ascii=False) + ":" + jcs(value[key]) for key in keys) + "}"


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def digest(document) -> str:
    return sha(jcs(document).encode("utf-8"))


def parse(data: bytes):
    return json.loads(data.decode("utf-8"), parse_float=Decimal)


# ---------------------------------------------------------------------------------------------------
# Files. Inputs are written readably; documents a reader writes are their JCS bytes (section 2).

FILES: dict[str, bytes] = {}


def put(relative: str, data: bytes) -> str:
    assert FILES.get(relative, data) == data, relative
    FILES[relative] = data
    return relative


def indented(value, depth: int = 0) -> str:
    """json.dumps(value, indent=2, ensure_ascii=False), with a Decimal written as it was read."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict) and value:
        inner = "  " * (depth + 1)
        members = (inner + json.dumps(key, ensure_ascii=False) + ": " + indented(item, depth + 1)
                   for key, item in value.items())
        return "{\n" + ",\n".join(members) + "\n" + "  " * depth + "}"
    if isinstance(value, list) and value:
        inner = "  " * (depth + 1)
        return "[\n" + ",\n".join(inner + indented(item, depth + 1) for item in value) + "\n" + "  " * depth + "]"
    return json.dumps(value, ensure_ascii=False)


def pretty(relative: str, document) -> str:
    return put(relative, (indented(document) + "\n").encode("utf-8"))


def canonical(relative: str, document, final_line_feed: bool = False) -> str:
    return put(relative, (jcs(document) + ("\n" if final_line_feed else "")).encode("utf-8"))


def copied(relative: str, source: Path) -> str:
    return put(relative, source.read_bytes())


def document_of(relative: str):
    return parse(FILES[relative])


# ---------------------------------------------------------------------------------------------------
# Kinds. database and db-role are format 1.0.0's rows, byte for byte.

DATABASE = copied("kinds/database.json", OLD / "kinds" / "database.json")
DB_ROLE = copied("kinds/db-role.json", OLD / "kinds" / "db-role.json")
db_role_13 = document_of(DB_ROLE)
db_role_13["version"] = "1.3.0"
db_role_13["description"] = "A database role a service connects as; a minor version that allows more connections."
db_role_13["schema"]["properties"]["connectionLimit"]["maximum"] = 1000
DB_ROLE_13 = pretty("kinds/db-role-1.3.0.json", db_role_13)
APP = pretty("kinds/app.json", {
    "kindFormatVersion": "1.0.0", "id": "https://example.invalid/kinds/app", "version": "1.0.0", "kind": "app",
    "owner": "platform-data", "description": "A service that runs.",
    "schema": {"type": "object", "additionalProperties": False, "properties": {
        "labels": {"type": "object", "additionalProperties": {"type": "string"}},
        "name": {"type": "string"},
        "replicas": {"type": "integer", "minimum": 0},
        "tags": {"type": "array", "items": {"type": "string"}},
        "tier": {"type": "string"},
        "weight": {"type": "number"}}}})
TOPIC = pretty("kinds/topic.json", {
    "kindFormatVersion": "1.0.0", "id": "https://example.invalid/kinds/topic", "version": "1.0.0", "kind": "topic",
    "owner": "team-billing", "description": "A topic a service publishes to.",
    "schema": {"type": "object", "required": ["name"], "additionalProperties": False,
               "properties": {"name": {"type": "string"}}}})


def pin(relative: str) -> dict:
    kind = document_of(relative)
    return {"kind": kind["kind"], "id": kind["id"], "version": kind["version"], "digest": digest(kind)}


assert pin(DATABASE)["digest"] == "sha256:80f28e5450bc53cfeb1ffdf63237a48b834ba5cb80ff4daec2fb277c809247a7"
assert pin(DB_ROLE)["digest"] == "sha256:64e30653b5b2743af0fb78d555d186ea9a57551aa1c800c8f972f824ef7da020"

# ---------------------------------------------------------------------------------------------------
# Identities. Every name is synthetic; commits are SHA-1 or SHA-256 of a fixed text.

BILLING_REPO = "https://example.invalid/scm/billing"
PLATFORM_REPO = "https://example.invalid/scm/platform"
PAYMENTS_REPO = "https://example.invalid/scm/payments"
COPIES_REPO = "https://example.invalid/scm/copies"
LEDGER_REPO = "https://example.invalid/scm/ledger"
BC = hashlib.sha1(b"billing").hexdigest()
BC_OTHER = hashlib.sha1(b"billing, another commit").hexdigest()
SC = hashlib.sha256(b"platform").hexdigest()
PC = hashlib.sha1(b"payments").hexdigest()
CC = hashlib.sha1(b"copies").hexdigest()
ASSEMBLED_ID = "https://example.invalid/registries/assembled"
SERVICES_ID = "https://example.invalid/registries/services"
OUTER_ID = "https://example.invalid/registries/outer"
SINGLE_ID = "https://example.invalid/registries/platform"
STANDARD_REGISTRY_ID = "https://example.invalid/registries/platform-standard"
BILLING_REGISTRY_ID = "https://example.invalid/registries/billing"

# ---------------------------------------------------------------------------------------------------
# Entries and the sources' documents.

STD_DATABASE = {"kind": "database", "id": "billing", "owner": "platform-data",
                "value": {"engine": "postgres", "admin": "entry:db-role/billing-api"}}
STD_DATABASE_PLAIN = {"kind": "database", "id": "billing", "owner": "platform-data", "value": {"engine": "postgres"}}
BILLING_API = {"kind": "db-role", "id": "billing-api", "owner": "team-billing",
               "value": {"database": "entry:database/billing", "privileges": ["read", "write"], "connectionLimit": 20}}
BILLING_BACKFILL = {"kind": "db-role", "id": "billing-backfill", "owner": "team-billing", "environments": ["dev"],
                    "value": {"database": "entry:database/billing#/engine", "privileges": ["read"]}}
BILLING_JOBS = {"kind": "db-role", "id": "billing-jobs", "owner": "team-billing",
                "value": {"database": "entry:database/billing", "privileges": ["read"]}}
TOPIC_EVENTS = {"kind": "topic", "id": "billing-events", "owner": "team-billing", "value": {"name": "billing-events"}}
PAYMENTS_API = {"kind": "app", "id": "payments-api", "owner": "team-payments",
                "value": {"labels": {"team": "payments"}, "name": "payments-api", "replicas": 3, "tags": ["api", "edge"],
                          "tier": "gold", "weight": 2}}
DEV_PASSWORD = "secret:gcp-sm:projects/example-dev/secrets/billing-db/versions/3"
PROD_PASSWORD = "secret:gcp-sm:projects/example-prod/secrets/billing-db/versions/7"
BILLING_API_SECRET = copy.deepcopy(BILLING_API)
BILLING_API_SECRET["value"]["password"] = DEV_PASSWORD
SCOPES = {"dev": {"gcp-sm": ["example-dev"]}, "prod": {"gcp-sm": ["example-prod"]}}


def overlay(patch_set: dict) -> list:
    return [{"environment": "prod", "patches": [{"kind": "db-role", "id": "billing-api", "set": patch_set}]}]


BILLING_OVERLAY = overlay({"/connectionLimit": 40})
SECRET_OVERLAY = overlay({"/connectionLimit": 40, "/password": PROD_PASSWORD})


def registry(identity: str, version: str, environments: list, owners: list, kinds: list, entries: list,
             overlays: list | None = None, scopes: dict | None = None) -> dict:
    document = {"registryFormatVersion": "1.0.0", "id": identity, "version": version, "environments": environments,
                "owners": owners, "kinds": kinds, "entries": entries}
    if overlays:
        document["overlays"] = overlays
    if scopes is not None:
        document["secretScopes"] = scopes
    return document


def standard_registry(entries, kinds=None, scopes=None):
    return registry(STANDARD_REGISTRY_ID, "1.0.0", ["dev", "prod"], ["platform-data"],
                    kinds if kinds is not None else [pin(DATABASE), pin(DB_ROLE)], entries, scopes=scopes)


def billing_registry(entries=None, environments=("dev", "prod"), overlays=BILLING_OVERLAY, kinds=None,
                     owners=("team-billing",), scopes=None, identity=BILLING_REGISTRY_ID):
    return registry(identity, "2.1.0", list(environments), list(owners),
                    kinds if kinds is not None else [pin(DB_ROLE)],
                    entries if entries is not None else [BILLING_API, BILLING_BACKFILL], overlays, scopes)


STD_REG = pretty("sources/platform/registry.json", standard_registry([STD_DATABASE]))
STD_REG_SUBSET = pretty("sources/platform/registry-subset.json", standard_registry([STD_DATABASE_PLAIN]))
STD_REG_SCOPES = pretty("sources/platform/registry-scopes.json", standard_registry([STD_DATABASE], scopes=SCOPES))
STD_REG_NO_ROLE = pretty("sources/platform/registry-no-role.json",
                         standard_registry([STD_DATABASE], kinds=[pin(DATABASE)]))

BIL_REG = pretty("sources/billing/registry.json", billing_registry())
BIL_REG_JCS = canonical("sources/billing/registry-jcs.json", billing_registry())
BIL_REG_PROD = pretty("sources/billing/registry-prod.json",
                      billing_registry(entries=[BILLING_API], environments=("prod",)))
BIL_REG_OWNER = pretty("sources/billing/registry-owner.json", billing_registry(
    entries=[dict(BILLING_API, owner="platform-data"), BILLING_BACKFILL]))
value_api = copy.deepcopy(BILLING_API)
value_api["value"]["connectionLimit"] = 60
BIL_REG_VALUE = pretty("sources/billing/registry-value.json", billing_registry(
    entries=[value_api, BILLING_BACKFILL], overlays=overlay({"/connectionLimit": 120})))
BIL_REG_SCOPES = pretty("sources/billing/registry-scopes.json", billing_registry(
    entries=[BILLING_API_SECRET, BILLING_BACKFILL], overlays=SECRET_OVERLAY, scopes=SCOPES))
widened_scopes = copy.deepcopy(SCOPES)
widened_scopes["dev"]["gcp-sm"].append("billing-scratch")
BIL_REG_SCOPES_WIDE = pretty("sources/billing/registry-scopes-widens.json", billing_registry(
    entries=[BILLING_API_SECRET, BILLING_BACKFILL], overlays=SECRET_OVERLAY, scopes=widened_scopes))
BIL_REG_DUP_ID = pretty("sources/billing/registry-duplicate-id.json", billing_registry(identity=ASSEMBLED_ID))
BIL_REG_OWN_KIND = pretty("sources/billing/registry-own-kind.json", billing_registry(kinds=[pin(DB_ROLE_13)]))
BIL_REG_ROLE_13 = pretty("sources/billing/registry-role-1.3.0.json", billing_registry(kinds=[pin(DB_ROLE_13)]))
BIL_REG_TOPIC = pretty("sources/billing/registry-topic.json", billing_registry(
    kinds=[pin(DB_ROLE), pin(TOPIC)], entries=[BILLING_API, BILLING_BACKFILL, TOPIC_EVENTS]))
JOBS_REG = pretty("sources/billing/jobs-registry.json", registry(
    "https://example.invalid/registries/billing-jobs", "1.0.0", ["dev", "prod"], ["team-billing"], [pin(DB_ROLE)],
    [BILLING_JOBS]))
PAY_REG = pretty("sources/payments/registry.json", registry(
    "https://example.invalid/registries/payments", "1.0.0", ["dev", "prod"], ["team-payments"], [pin(APP)],
    [PAYMENTS_API]))

# Bounds (section 6). The standard's is section 6.1's example.
CONNECTION = {"pointer": "/connectionLimit", "bound": {"type": "integer", "minimum": 1, "maximum": 200},
              "environments": {"prod": {"maximum": 100}}}
STD_DB_ROLE_BOUNDS = {"kind": "db-role", "maxEntries": 40, "maxAssemblyEntries": 400, "fields": [
    CONNECTION,
    {"pointer": "/privileges", "bound": {"maxItems": 2, "uniqueItems": True}},
    {"pointer": "/privileges/*", "bound": {"enum": ["read", "write"]}}]}


def bounds(*kinds) -> dict:
    return {"boundsFormatVersion": "1.1.0", "kinds": list(kinds)}


STD_BOUNDS = pretty("sources/platform/bounds.json", bounds(STD_DB_ROLE_BOUNDS))
staging = copy.deepcopy(STD_DB_ROLE_BOUNDS)
staging["fields"][0]["environments"]["staging"] = {"maximum": 150}
STD_BOUNDS_STAGING = pretty("sources/platform/bounds-staging.json", bounds(staging))
assembly_2 = copy.deepcopy(STD_DB_ROLE_BOUNDS)
assembly_2["maxAssemblyEntries"] = 2
STD_BOUNDS_ASSEMBLY_2 = pretty("sources/platform/bounds-assembly-2.json", bounds(assembly_2))
STD_BOUNDS_KIND = pretty("sources/platform/bounds-kind.json", bounds(STD_DB_ROLE_BOUNDS, {"kind": "topic", "maxEntries": 5}))


def billing_fields(connection=None, database=None, extra=()):
    fields = [{"pointer": "/connectionLimit", "bound": {"maximum": 50}} if connection is None else connection,
              {"pointer": "/database", "bound": {"patterns": ["^entry:database/billing"]}} if database is None else database,
              {"pointer": "/privileges/*", "bound": {"enum": ["read", "write"]}}]
    for position, field in extra:
        fields.insert(position, field)
    return fields


def billing_bounds(relative, max_entries=10, **fields) -> str:
    return pretty(relative, bounds({"kind": "db-role", "maxEntries": max_entries, "fields": billing_fields(**fields)}))


BIL_BOUNDS = billing_bounds("sources/billing/bounds.json")
BIL_BOUNDS_PER_ENV = billing_bounds("sources/billing/bounds-per-environment.json", connection={
    "pointer": "/connectionLimit", "bound": {"maximum": 50}, "environments": {"dev": {"maximum": 30}, "prod": {"maximum": 45}},
    "description": "Tighter in each environment than in the field's bound."})
BIL_BOUNDS_PROD_WIDE = billing_bounds("sources/billing/bounds-widens-in-prod.json", connection={
    "pointer": "/connectionLimit", "bound": {"maximum": 150}})
BIL_BOUNDS_ENV_WIDE = billing_bounds("sources/billing/bounds-widens-own-bound.json", connection={
    "pointer": "/connectionLimit", "bound": {"maximum": 50}, "environments": {"prod": {"maximum": 60}}})
BIL_BOUNDS_ENV_DEV = billing_bounds("sources/billing/bounds-environment-dev.json", connection={
    "pointer": "/connectionLimit", "bound": {"maximum": 50}, "environments": {"dev": {"maximum": 30}}})
form = bounds({"kind": "db-role", "maxEntries": 10, "maxAssemblyEntries": 20, "fields": billing_fields(
    database={"pointer": "/database", "bound": {"patterns": ["^entry:database/billing"], "format": "uri"}})})
BIL_BOUNDS_FORM = pretty("sources/billing/bounds-form.json", form)
BIL_BOUNDS_UNREACHABLE = billing_bounds("sources/billing/bounds-unreachable.json", extra=[
    (1, {"pointer": "/connectionLimits", "bound": {"maximum": 10}})])
BIL_BOUNDS_PATTERN = billing_bounds("sources/billing/bounds-pattern.json", database={
    "pointer": "/database", "bound": {"pattern": "^entry:database/"}})
BIL_BOUNDS_OVERLAP = billing_bounds("sources/billing/bounds-overlap.json", extra=[
    (3, {"pointer": "/privileges/0", "bound": {"enum": ["read"]}})])
BIL_BOUNDS_MAX_1 = billing_bounds("sources/billing/bounds-max-entries-1.json", max_entries=1)
BIL_BOUNDS_KIND = pretty("sources/billing/bounds-kind.json", bounds(
    {"kind": "db-role", "maxEntries": 10, "fields": billing_fields()},
    {"kind": "db-rolee", "maxEntries": 3},
    {"kind": "topic", "maxEntries": 3}))

APP_STANDARD = {"kind": "app", "maxEntries": 10, "fields": [
    {"pointer": "/labels", "bound": {"maxProperties": 8}},
    {"pointer": "/name", "bound": {"minLength": 1, "maxLength": 40}},
    {"pointer": "/replicas", "bound": {"type": "integer", "minimum": 1, "maximum": 10}},
    {"pointer": "/tags", "bound": {"minItems": 1, "maxItems": 6, "uniqueItems": True}},
    {"pointer": "/tier", "bound": {"enum": ["gold", "silver", "bronze"]}},
    {"pointer": "/weight", "bound": {"type": "number"}}]}
APP_TIGHT = {"kind": "app", "maxEntries": 4, "fields": [
    {"pointer": "/labels", "bound": {"minProperties": 1, "maxProperties": 4, "required": ["team"]}},
    {"pointer": "/name", "bound": {"maxLength": 20, "patterns": ["^payments-"]}},
    {"pointer": "/replicas", "bound": {"exclusiveMinimum": 1, "maximum": 10, "exclusiveMaximum": 8}},
    {"pointer": "/tags", "bound": {"minItems": 2, "maxItems": 3, "uniqueItems": True}},
    {"pointer": "/tier", "bound": {"const": "gold"}},
    {"pointer": "/weight", "bound": {"type": "integer"}}]}
STD_APP_BOUNDS = pretty("sources/platform/services-bounds.json", bounds(APP_STANDARD))
PAY_BOUNDS = pretty("sources/payments/bounds.json", bounds(APP_TIGHT))


def app_variant(name: str, field: int | None, bound: dict | None, max_entries: int = 4) -> str:
    kind = copy.deepcopy(APP_TIGHT)
    kind["maxEntries"] = max_entries
    if field is not None:
        kind["fields"][field]["bound"] = bound
    return pretty(f"sources/payments/bounds-{name}.json", bounds(kind))


# ---------------------------------------------------------------------------------------------------
# Manifests (section 3).


def source(name, role, repository, registry_path=None, bounds_path=None, kinds=None, environments=None) -> dict:
    item = {"name": name, "role": role, "repository": repository}
    if environments is not None:
        item["environments"] = environments
    if registry_path:
        item["registry"] = registry_path
    if bounds_path:
        item["bounds"] = bounds_path
    if kinds is not None:
        item["kinds"] = kinds
    return item


def manifest(identity, version, sources, environments=("dev", "prod")) -> dict:
    return {"federationFormatVersion": "1.1.0", "registry": {"id": identity, "version": version},
            "environments": list(environments), "sources": sources}


STD_KINDS = ["kinds/database.json", "kinds/db-role.json"]
STD_SOURCE = source("standard", "standard", PLATFORM_REPO, "registry.json", "bounds.json", STD_KINDS)
BIL_SOURCE = source("billing", "repository", BILLING_REPO, "registry/registry.json", "registry/bounds.json")
FED_A = pretty("federation/two-sources.json", manifest(ASSEMBLED_ID, "7.0.0", [BIL_SOURCE, STD_SOURCE]))
FED_A_EXPLICIT = pretty("federation/two-sources-every-environment-named.json", manifest(ASSEMBLED_ID, "7.0.0", [
    source("billing", "repository", BILLING_REPO, "registry/registry.json", "registry/bounds.json",
           environments=["dev", "prod"]), STD_SOURCE]))
FED_B = pretty("federation/billing-serves-prod.json", manifest(ASSEMBLED_ID, "7.0.0", [
    source("billing", "repository", BILLING_REPO, "registry/registry.json", "registry/bounds.json",
           environments=["prod"]), STD_SOURCE]))
JOBS_SOURCE = source("billing-jobs", "repository", BILLING_REPO, "jobs/registry.json")
FED_J = pretty("federation/one-repository-two-sources.json",
               manifest(ASSEMBLED_ID, "7.0.0", [BIL_SOURCE, JOBS_SOURCE, STD_SOURCE]))
FED_T = pretty("federation/services.json", manifest(SERVICES_ID, "1.0.0", [
    source("payments", "repository", PAYMENTS_REPO, "registry.json", "bounds.json"),
    source("standard", "standard", PLATFORM_REPO, None, "services/bounds.json", ["kinds/app.json"])]))
FED_TOPIC = pretty("federation/billing-declares-a-kind.json", manifest(ASSEMBLED_ID, "7.0.0", [
    source("billing", "repository", BILLING_REPO, "registry/registry.json", "registry/bounds.json",
           ["kinds/topic.json"]), STD_SOURCE]))
FED_OWN_KIND = pretty("federation/billing-declares-db-role.json", manifest(ASSEMBLED_ID, "7.0.0", [
    source("billing", "repository", BILLING_REPO, "registry/registry.json", "registry/bounds.json",
           ["kinds/db-role.json"]), STD_SOURCE]))
FED_TWO_VERSIONS = pretty("federation/standard-supplies-two-versions.json", manifest(ASSEMBLED_ID, "7.0.0", [
    BIL_SOURCE, source("standard", "standard", PLATFORM_REPO, "registry.json", "bounds.json",
                       STD_KINDS + ["kinds/db-role-1.3.0.json"])]))
FED_OUTER = pretty("federation/outer.json", manifest(OUTER_ID, "1.0.0", [
    source("copy", "repository", COPIES_REPO, "assembled/registry.json"), STD_SOURCE]))
FED_LAYER = pretty("federation/layer-role.json", manifest(ASSEMBLED_ID, "7.0.0", [
    source("billing", "division", BILLING_REPO, "registry/registry.json", "registry/bounds.json"), STD_SOURCE]))
commit_member = manifest(ASSEMBLED_ID, "7.0.0", [BIL_SOURCE, STD_SOURCE])
commit_member["commit"] = BC
FED_COMMIT_MEMBER = pretty("federation/names-a-commit.json", commit_member)
FED_USERINFO = pretty("federation/repository-userinfo.json", manifest(ASSEMBLED_ID, "7.0.0", [
    source("billing", "repository", "https://ci@example.invalid/scm/billing", "registry/registry.json",
           "registry/bounds.json"), STD_SOURCE]))

# The files each source is given (section 4, "Input"), by path in its repository.
STD_FILES = {"registry.json": STD_REG, "bounds.json": STD_BOUNDS, "kinds/database.json": DATABASE,
             "kinds/db-role.json": DB_ROLE}
BIL_FILES = {"registry/registry.json": BIL_REG, "registry/bounds.json": BIL_BOUNDS}


def with_path(commit, files, changes: dict) -> dict:
    files = dict(files)
    for path, relative in changes.items():
        if relative is None:
            del files[path]
        else:
            files[path] = relative
    return {"commit": commit, "files": dict(sorted(files.items()))}


def world(billing=None, standard=None, **others) -> dict:
    sources = {"billing": billing or with_path(BC, BIL_FILES, {}),
               "standard": standard or with_path(SC, STD_FILES, {})}
    sources.update({name.replace("_", "-"): value for name, value in others.items()})
    return dict(sorted(sources.items()))


NO_KNOWN = {"indexes": [], "locks": []}

# ---------------------------------------------------------------------------------------------------
# What an assembly writes (section 4 step 6, section 5), composed by hand for each world.


def resolve(document: dict, environment: str) -> dict:
    patches = {}
    for item in document.get("overlays", []):
        if item["environment"] == environment:
            for patch in item["patches"]:
                patches[(patch["kind"], patch["id"])] = patch["set"]
    entries = []
    for entry in document["entries"]:
        if environment not in entry.get("environments", document["environments"]):
            continue
        value = copy.deepcopy(entry["value"])
        for pointer, new in sorted(patches.get((entry["kind"], entry["id"]), {}).items()):
            target = value
            tokens = pointer.split("/")[1:]
            for token in tokens[:-1]:
                target = target[int(token)] if isinstance(target, list) else target[token]
            if isinstance(target, list):
                target[int(tokens[-1])] = copy.deepcopy(new)
            else:
                target[tokens[-1]] = copy.deepcopy(new)
        entries.append({"kind": entry["kind"], "id": entry["id"], "owner": entry["owner"], "value": value})
    return {"resolvedFormatVersion": "1.0.0",
            "registry": {"id": document["id"], "version": document["version"], "digest": digest(document)},
            "environment": environment, "kinds": document["kinds"], "entries": entries}


def assembled(entries, kinds=None, owners=("platform-data", "team-billing"), overlays=BILLING_OVERLAY,
              environments=("dev", "prod"), identity=ASSEMBLED_ID, version="7.0.0", scopes=None) -> dict:
    return registry(identity, version, list(environments), list(owners),
                    kinds if kinds is not None else [pin(DATABASE), pin(DB_ROLE)], entries, overlays, scopes)


def served(entry, environments):
    entry = copy.deepcopy(entry)
    entry["environments"] = environments
    return entry


REG_A = assembled([STD_DATABASE, BILLING_API, BILLING_BACKFILL])
REG_B = assembled([STD_DATABASE_PLAIN, served(BILLING_API, ["prod"])])
REG_GAP = assembled([STD_DATABASE, served(BILLING_API, ["prod"])])
REG_J = assembled([STD_DATABASE, BILLING_API, BILLING_BACKFILL, BILLING_JOBS])
REG_T = assembled([PAYMENTS_API], kinds=[pin(APP)], owners=("team-payments",), overlays=None,
                  identity=SERVICES_ID, version="1.0.0")
REG_S = assembled([STD_DATABASE, BILLING_API_SECRET, BILLING_BACKFILL], overlays=SECRET_OVERLAY, scopes=SCOPES)
REG_U = assembled([STD_DATABASE, BILLING_API_SECRET, BILLING_BACKFILL], overlays=SECRET_OVERLAY)
REG_OWNER = assembled([STD_DATABASE, dict(BILLING_API, owner="platform-data"), BILLING_BACKFILL])
REG_VALUE = assembled([STD_DATABASE, value_api, BILLING_BACKFILL], overlays=overlay({"/connectionLimit": 120}))
REG_TOPIC = assembled([STD_DATABASE, BILLING_API, BILLING_BACKFILL, TOPIC_EVENTS],
                      kinds=[pin(DATABASE), pin(DB_ROLE), pin(TOPIC)])
# reading: the kinds an assembly holds after FED-KIND-NOT-STANDARD or FED-KIND-CONFLICT are its sources'
# pins, one per kind name, the earlier source's where two differ.
REG_OWN_KIND = assembled([STD_DATABASE, BILLING_API, BILLING_BACKFILL], kinds=[pin(DATABASE), pin(DB_ROLE_13)])
REG_CONFLICT = REG_OWN_KIND


def documents(files: dict, roles: dict) -> list:
    items = []
    for path in sorted(roles):
        data = FILES[files[path]]
        items.append({"path": path, "role": roles[path], "contentDigest": sha(data), "digest": digest(parse(data))})
    return items


def index(federation: str, registry_document: dict, items: list) -> dict:
    return {"indexFormatVersion": "1.1.0", "federation": {"digest": digest(document_of(federation))},
            "registry": {"id": registry_document["id"], "version": registry_document["version"],
                         "digest": digest(registry_document)},
            "sources": items}


def index_source(name, role, repository, given_source, roles) -> dict:
    return {"name": name, "role": role, "repository": repository, "commit": given_source["commit"],
            "documents": documents(given_source["files"], roles)}


BIL_ROLES = {"registry/bounds.json": "bounds", "registry/registry.json": "registry"}
STD_ROLES = {"bounds.json": "bounds", "kinds/database.json": "kind", "kinds/db-role.json": "kind",
             "registry.json": "registry"}


def write_assembly(name: str, federation: str, sources: dict, registry_document: dict, items: list):
    registry_path = canonical(f"assembled/{name}/registry.json", registry_document)
    index_document = index(federation, registry_document, items)
    index_path = canonical(f"assembled/{name}/index.json", index_document)
    return {"registry": registry_path, "index": index_path}


SRC_A = world()
IDX_A_ITEMS = [index_source("billing", "repository", BILLING_REPO, SRC_A["billing"], BIL_ROLES),
               index_source("standard", "standard", PLATFORM_REPO, SRC_A["standard"], STD_ROLES)]
OUT_A = write_assembly("two-sources", FED_A, SRC_A, REG_A, IDX_A_ITEMS)
IDX_A = document_of(OUT_A["index"])

# ---------------------------------------------------------------------------------------------------
# Reports (registry section 7.4 at the selector 1.1.0, section 2.1). Rows leave messages out.

ORDER = ("document", "source", "kindDocument", "kind", "entry.kind", "entry.id", "environment", "pointer",
         "line", "column")


def diag(code, document, pointer, source=None, kind=None, entry=None, environment=None, severity="error"):
    location = {"document": document}
    if source is not None:
        location["source"] = source
    if kind is not None:
        location["kind"] = kind
    if entry is not None:
        location["entry"] = {"kind": entry[0], "id": entry[1]}
    if environment is not None:
        location["environment"] = environment
    location["pointer"] = pointer
    return {"code": code, "severity": severity, "location": location}


def sort_key(diagnostic):
    location = diagnostic["location"]
    entry = location.get("entry", {})
    values = {"entry.kind": entry.get("kind", ""), "entry.id": entry.get("id", "")}
    return tuple(values[name] if name in values else location.get(name, 0 if name in ("line", "column") else "")
                 for name in ORDER) + (diagnostic["code"],)


def report(valid: bool, diagnostics=(), registry_document=None) -> dict:
    diagnostics = sorted(diagnostics, key=sort_key)
    assert valid == (not any(d["severity"] == "error" for d in diagnostics))
    document = {"reportFormatVersion": "1.1.0", "valid": valid}
    if registry_document is not None:
        document["registry"] = {"digest": digest(registry_document)}
    document["diagnostics"] = diagnostics
    return document


def write_report(relative: str, document: dict) -> str:
    lines = ["{", f'  "reportFormatVersion": "1.1.0",', f'  "valid": {json.dumps(document["valid"])},']
    if "registry" in document:
        lines.append(f'  "registry": {{"digest": "{document["registry"]["digest"]}"}},')
    if document["diagnostics"]:
        lines.append('  "diagnostics": [')
        lines.append(",\n".join("    " + json.dumps(d, ensure_ascii=False) for d in document["diagnostics"]))
        lines.append("  ]")
    else:
        lines.append('  "diagnostics": []')
    lines.append("}")
    data = ("\n".join(lines) + "\n").encode("utf-8")
    assert parse(data) == document
    return put(relative, data)


ROWS: list[dict] = []
CLASSES = {"assemble": "assembler", "check-index": "index-checker", "write-lock": "lock-writer",
           "check-lock": "lock-checker", "coverage": "lock-checker", "verify": "lock-signature-verifier"}


def row(identity, section, operation, description, inputs, expected=None, **outputs):
    item = {"id": identity, "section": section, "operation": operation, "class": CLASSES[operation],
            "description": description, **inputs}
    if isinstance(expected, dict) and "reportFormatVersion" in expected:
        item["expected"] = write_report(f"vectors/{identity}/report.json", expected)
    elif isinstance(expected, dict):
        item["expected"] = pretty(f"vectors/{identity}/refused.json", expected)
    else:
        item["expected"] = expected
    item.update(outputs)
    assert identity not in {r["id"] for r in ROWS}, identity
    ROWS.append(item)


def assemble(identity, section, description, federation, sources, expected, known=NO_KNOWN, writes=None,
             schema_refuses=()):
    inputs = {"federation": federation, "sources": sources, "known": known}
    outputs = {}
    if writes:
        outputs["writes"] = writes
    if schema_refuses:
        outputs["schemaRefuses"] = list(schema_refuses)
    row(identity, section, "assemble", description, inputs, expected, **outputs)


BILLING_API_ENTRY = ("db-role", "billing-api")

# ---------------------------------------------------------------------------------------------------
# Assembler: accepted assemblies.

assemble("assemble-two-sources", "§4",
         "A repository and the standard assemble: the standard's entry refers to the repository's, and the "
         "repository's to the standard's, so each alone defers REF-ENTRY-MISSING to step 6; the repository's bounds "
         "tighten the standard's, add a pattern at a pointer the standard does not bound, and every value meets "
         "both. The index records each document's content digest beside its digest, which differ for a file not "
         "in its JCS form. reading: the report's registry is the digest of the registry the assembly validates by "
         "registry section 7, here the assembled registry.",
         FED_A, SRC_A, report(True, (), REG_A), writes=OUT_A)

SRC_B = world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_PROD}),
              standard=with_path(SC, STD_FILES, {"registry.json": STD_REG_SUBSET}))
OUT_B = write_assembly("billing-serves-prod", FED_B, SRC_B, REG_B, [
    index_source("billing", "repository", BILLING_REPO, SRC_B["billing"], BIL_ROLES),
    index_source("standard", "standard", PLATFORM_REPO, SRC_B["standard"], STD_ROLES)])
assemble("assemble-served-subset", "§§3, 4",
         "A repository that serves prod alone, with a registry of that one environment, in an assembly of dev and "
         "prod: its entry is written with environments [\"prod\"], so it applies only where its source said it does, "
         "and the bounds are compared in prod alone.",
         FED_B, SRC_B, report(True, (), REG_B), writes=OUT_B)

SRC_PER_ENV = world(billing=with_path(BC, BIL_FILES, {"registry/bounds.json": BIL_BOUNDS_PER_ENV}))
OUT_PER_ENV = write_assembly("per-environment-bounds", FED_A, SRC_PER_ENV, REG_A, [
    index_source("billing", "repository", BILLING_REPO, SRC_PER_ENV["billing"], BIL_ROLES),
    index_source("standard", "standard", PLATFORM_REPO, SRC_PER_ENV["standard"], STD_ROLES)])
assemble("assemble-per-environment-bounds", "§6.4",
         "Per-environment bounds in both documents: the standard bounds /connectionLimit at 200 and at 100 in prod; "
         "the repository at 50, 30 in dev and 45 in prod. Each environment's bound is at least as tight as its own "
         "field's, each effective bound as the standard's there, and the values (20 in dev, 40 in prod) meet both. "
         "The assembled registry is the two-source row's; only the index differs.",
         FED_A, SRC_PER_ENV, report(True, (), REG_A), writes=OUT_PER_ENV)

SRC_J = world(billing_jobs=with_path(BC, {"jobs/registry.json": JOBS_REG}, {}))
OUT_J = write_assembly("one-repository-two-sources", FED_J, SRC_J, REG_J, [
    index_source("billing", "repository", BILLING_REPO, SRC_J["billing"], BIL_ROLES),
    index_source("billing-jobs", "repository", BILLING_REPO, SRC_J["billing-jobs"], {"jobs/registry.json": "registry"}),
    index_source("standard", "standard", PLATFORM_REPO, SRC_J["standard"], STD_ROLES)])
assemble("assemble-one-repository-two-sources", "§§3, 4",
         "Two sources name one repository identity, one repository holding two services, and are given one commit. "
         "The source without bounds is held to the standard's alone.",
         FED_J, SRC_J, report(True, (), REG_J), writes=OUT_J)

T_STD = with_path(SC, {"kinds/app.json": APP, "services/bounds.json": STD_APP_BOUNDS}, {})
SRC_T = {"payments": with_path(PC, {"bounds.json": PAY_BOUNDS, "registry.json": PAY_REG}, {}), "standard": T_STD}
OUT_T = write_assembly("services", FED_T, SRC_T, REG_T, [
    index_source("payments", "repository", PAYMENTS_REPO, SRC_T["payments"],
                 {"bounds.json": "bounds", "registry.json": "registry"}),
    index_source("standard", "standard", PLATFORM_REPO, T_STD,
                 {"kinds/app.json": "kind", "services/bounds.json": "bounds"})])
assemble("assemble-tightened-rows", "§6.2",
         "Every row of section 6.2 tightened at once, against a standard with no registry of its own: a type "
         "inside the standard's (integer inside number), a const inside its enum, an exclusive lower bound equal "
         "to its inclusive one, an upper bound taken as the tighter of maximum and exclusiveMaximum, shorter "
         "length, item and member counts (a minimum item count raised, a minimum member count added), uniqueItems where the standard has it, required and patterns added, "
         "and a smaller maxEntries.",
         FED_T, SRC_T, report(True, (), REG_T), writes=OUT_T)

SRC_S = world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_SCOPES}),
              standard=with_path(SC, STD_FILES, {"registry.json": STD_REG_SCOPES}))
OUT_S = write_assembly("scopes", FED_A, SRC_S, REG_S, [
    index_source("billing", "repository", BILLING_REPO, SRC_S["billing"], BIL_ROLES),
    index_source("standard", "standard", PLATFORM_REPO, SRC_S["standard"], STD_ROLES)])
assemble("assemble-scopes-within-the-standard", "§4",
         "The standard declares secretScopes and the repository's scopes list only projects the standard's list "
         "for the same environment and store: each source's references are checked against its own scopes, and "
         "the assembled registry carries the standard's.",
         FED_A, SRC_S, report(True, (), REG_S), writes=OUT_S)

SRC_U = world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_SCOPES}))
OUT_U = write_assembly("unscoped", FED_A, SRC_U, REG_U, [
    index_source("billing", "repository", BILLING_REPO, SRC_U["billing"], BIL_ROLES),
    index_source("standard", "standard", PLATFORM_REPO, SRC_U["standard"], STD_ROLES)])
assemble("assemble-scopes-unscoped", "§4",
         "The standard declares no secretScopes: the repository's own scopes hold its references in step 5, and "
         "the assembled registry, which has none, reads them unscoped. The assembly is valid with the warning "
         "REF-SECRET-UNSCOPED in each environment, located in the source that holds the entry. reading: a value "
         "diagnostic of the assembled registry keeps document value and its pointer into the value, and source "
         "names the source that holds the entry.",
         FED_A, SRC_U, report(True, [
             diag("REF-SECRET-UNSCOPED", "value", "/password", "billing", entry=BILLING_API_ENTRY, environment="dev",
                  severity="warning"),
             diag("REF-SECRET-UNSCOPED", "value", "/password", "billing", entry=BILLING_API_ENTRY, environment="prod",
                  severity="warning")], REG_U), writes=OUT_U)

# ---------------------------------------------------------------------------------------------------
# Assembler: refusals.

assemble("assemble-source-alone-refused", "§4",
         "An entry whose owner is not among its source's owners is REG-ENTRY-OWNER in step 5, located in that "
         "source, although the assembled registry's owners, the union, name it: assembly never makes valid what a "
         "source alone refuses.",
         FED_A, world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_OWNER})),
         report(False, [diag("REG-ENTRY-OWNER", "registry", "/entries/0/owner", "billing", entry=BILLING_API_ENTRY)],
                REG_OWNER))

assemble("assemble-environment-gap", "§4",
         "The repository serves prod alone; the standard's entry, which applies in dev and prod, refers to the "
         "repository's entry. In dev the reference is FED-ENVIRONMENT-GAP, beside the "
         "REF-ENTRY-ABSENT-IN-ENVIRONMENT that registry section 7 reports for it, both located in the standard. "
         "reading: the second keeps document value and its pointer into the value, as the first does.",
         FED_B, world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_PROD})),
         report(False, [
             diag("FED-ENVIRONMENT-GAP", "value", "/admin", "standard", entry=("database", "billing"), environment="dev"),
             diag("REF-ENTRY-ABSENT-IN-ENVIRONMENT", "value", "/admin", "standard", entry=("database", "billing"),
                  environment="dev")], REG_GAP))

assemble("assemble-environments-mismatch", "§4",
         "A repository that serves prod alone gives a registry of dev and prod: FED-ENVIRONMENTS, and the assembly "
         "ends after step 3, with no registry validated. reading: located at the source's registry /environments.",
         FED_B, world(standard=with_path(SC, STD_FILES, {"registry.json": STD_REG_SUBSET})),
         report(False, [diag("FED-ENVIRONMENTS", "registry", "/environments", "billing")]))

assemble("assemble-layer-role", "§3",
         "A role other than standard or repository, such as a later version's layer role, is FED-MANIFEST: the "
         "manifest is refused rather than read as a flat assembly. reading: located at the role.",
         FED_LAYER, SRC_A, report(False, [diag("FED-MANIFEST", "federation", "/sources/0/role")]),
         schema_refuses=[FED_LAYER])

assemble("assemble-manifest-names-a-commit", "§3",
         "The manifest names no commit: a commit member is not one of its members, FED-MANIFEST. reading: located at "
         "the member.",
         FED_COMMIT_MEMBER, SRC_A, report(False, [diag("FED-MANIFEST", "federation", "/commit")]),
         schema_refuses=[FED_COMMIT_MEMBER])

assemble("assemble-commit-abbreviated", "§4",
         "A commit of seven hexadecimal digits is an abbreviation, never a full commit identifier: FED-COMMIT. "
         "reading: located at the source's item in the manifest.",
         FED_A, world(billing=with_path(BC[:7], BIL_FILES, {})),
         report(False, [diag("FED-COMMIT", "federation", "/sources/0")]))

assemble("assemble-commit-disagrees", "§4",
         "Two sources of one repository identity given different commits: FED-COMMIT. reading: located at the later "
         "source's item.",
         FED_J, world(billing_jobs=with_path(BC_OTHER, {"jobs/registry.json": JOBS_REG}, {})),
         report(False, [diag("FED-COMMIT", "federation", "/sources/1")]))

assemble("assemble-repository-userinfo", "§3",
         "A repository identity with userinfo, where a credential would be written, is FED-REPOSITORY. reading: "
         "FED-REPOSITORY alone, not also FED-MANIFEST, located at the identity.",
         FED_USERINFO, SRC_A, report(False, [diag("FED-REPOSITORY", "federation", "/sources/0/repository")]),
         schema_refuses=[FED_USERINFO])

assemble("assemble-path-missing", "§4",
         "The bytes of a path the manifest names are not given: FED-SOURCE-MISSING, a refusal and never a fetch. "
         "reading: located at the manifest member that names the path.",
         FED_A, world(billing=with_path(BC, BIL_FILES, {"registry/bounds.json": None})),
         report(False, [diag("FED-SOURCE-MISSING", "federation", "/sources/0/bounds")]))

known_many = []
known_locks = []
for number_ in range(257):
    identity = f"https://example.invalid/registries/r-{number_:03d}"
    fake_registry = {"id": identity, "version": "1.0.0", "digest": sha(identity.encode("utf-8"))}
    known_index = {
        "indexFormatVersion": "1.1.0", "federation": {"digest": sha(b"federation " + identity.encode("utf-8"))},
        "registry": fake_registry,
        "sources": [{"name": "standard", "role": "standard", "repository": PLATFORM_REPO, "commit": SC,
                     "documents": []}]}
    known_many.append(canonical(f"vectors/assemble-known-limit/indexes/index-{number_:03d}.json", known_index))
    known_item = known_index["sources"][0]
    known_locks.append(canonical(f"vectors/assemble-known-lock-limit/locks/lock-{number_:03d}.json", {
        "lockFormatVersion": "1.1.0", "serial": 1, "registry": fake_registry, "kinds": [],
        "resolved": [{"environment": "dev", "digest": sha(b"resolved " + identity.encode("utf-8"))}],
        "index": {"digest": digest(known_index)},
        "sources": [{"name": "standard", "role": "standard", "repository": PLATFORM_REPO,
                     "statement": digest({"repository": known_item["repository"], "commit": known_item["commit"],
                                          "documents": known_item["documents"]}),
                     "signature": sha(b"signature " + identity.encode("utf-8"))}]}))
assemble("assemble-known-limit", "§4",
         "A list of 257 known assembled indexes is FED-KNOWN-LIMIT, before any source is read. reading: located at "
         "the manifest's root, the assembly as a whole.",
         FED_A, SRC_A, report(False, [diag("FED-KNOWN-LIMIT", "federation", "")]),
         known={"indexes": known_many, "locks": []})
assemble("assemble-known-lock-limit", "§4",
         "A known list of no index and 257 locks is FED-KNOWN-LIMIT, before any source is read: the locks are "
         "counted on their own, as the indexes are. reading: located at the manifest's root, the assembly as a "
         "whole.",
         FED_A, SRC_A, report(False, [diag("FED-KNOWN-LIMIT", "federation", "")]),
         known={"indexes": [], "locks": known_locks})
assemble("assemble-known-at-limit", "§4",
         "A known list of exactly 256 indexes and 256 locks, none of whose registries is a source's, is admitted: "
         "the assembly is the two-source row's, valid, and writes the same registry and index.",
         FED_A, SRC_A, report(True, (), REG_A), writes=OUT_A,
         known={"indexes": known_many[:256], "locks": known_locks[:256]})

COPY_REG_7_0_1 = pretty("sources/copies/registry-7.0.1.json", dict(REG_A, version="7.0.1"))
assemble("assemble-source-assembled-by-index", "§4",
         "A source whose registry's digest is the registry digest of a known assembled index is FED-SOURCE-ASSEMBLED: "
         "an assembled registry is never a source. reading: located at the source's registry document.",
         FED_OUTER, {"copy": with_path(CC, {"assembled/registry.json": OUT_A["registry"]}, {}),
                     "standard": with_path(SC, STD_FILES, {})},
         report(False, [diag("FED-SOURCE-ASSEMBLED", "registry", "", "copy")]),
         known={"indexes": [OUT_A["index"]], "locks": []})

# Locks are written below; this row names one by path.
LA_PATH = "locks/assembled-7.lock.json"
assemble("assemble-source-assembled-by-lock", "§4",
         "A source whose registry's id is the registry id of a known lock is FED-SOURCE-ASSEMBLED, although its bytes "
         "differ from the locked registry's. reading: located at the source's registry document.",
         FED_OUTER, {"copy": with_path(CC, {"assembled/registry.json": COPY_REG_7_0_1}, {}),
                     "standard": with_path(SC, STD_FILES, {})},
         report(False, [diag("FED-SOURCE-ASSEMBLED", "registry", "", "copy")]),
         known={"indexes": [], "locks": [LA_PATH]})

assemble("assemble-registry-duplicate", "§4",
         "A source's registry has the assembled registry's id: FED-REGISTRY-DUPLICATE, and the assembly ends after "
         "step 3. reading: located at that registry's /id.",
         FED_A, world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_DUP_ID})),
         report(False, [diag("FED-REGISTRY-DUPLICATE", "registry", "/id", "billing")]))

assemble("assemble-kind-not-standard", "§4",
         "A repository pins db-role, a kind the standard governs, to a declaration of its own that allows more "
         "connections: FED-KIND-NOT-STANDARD at its pin. The standard's registry pins no db-role, so no pin "
         "conflicts. reading: the pin's diagnostic names its kind as registry section 7.3 does for a pin; the "
         "assembled registry holds the repository's pin, and its validation is given the declarations its pins "
         "name.",
         FED_OWN_KIND, world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_OWN_KIND,
                                                               "kinds/db-role.json": DB_ROLE_13}),
                             standard=with_path(SC, STD_FILES, {"registry.json": STD_REG_NO_ROLE})),
         report(False, [diag("FED-KIND-NOT-STANDARD", "registry", "/kinds/0", "billing", kind="db-role")], REG_OWN_KIND))

assemble("assemble-kind-conflict", "§4",
         "The standard supplies two versions of db-role; the repository pins one and the standard's registry the "
         "other: FED-KIND-CONFLICT at the later source's pin. reading: the pin's diagnostic names its kind; the "
         "assembled registry holds the earlier source's pin, and its validation is given the declarations its pins "
         "name.",
         FED_TWO_VERSIONS, world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_ROLE_13}),
                                 standard=with_path(SC, STD_FILES, {"kinds/db-role-1.3.0.json": DB_ROLE_13})),
         report(False, [diag("FED-KIND-CONFLICT", "registry", "/kinds/1", "standard", kind="db-role")], REG_CONFLICT))

assemble("assemble-scope-widens", "§4",
         "The repository's scopes list, for dev and gcp-sm, a project the standard's do not: FED-SCOPE-WIDENS. "
         "reading: located at the repository's listing.",
         FED_A, world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_SCOPES_WIDE}),
                      standard=with_path(SC, STD_FILES, {"registry.json": STD_REG_SCOPES})),
         report(False, [diag("FED-SCOPE-WIDENS", "registry", "/secretScopes/dev/gcp-sm/1", "billing")], REG_S))


def billing_bounds_row(identity, section, description, bounds_path, diagnostics, schema_refuses=False,
                       sources=None, federation=FED_A, registry_document=REG_A):
    assemble(identity, section, description, federation,
             sources or world(billing=with_path(BC, BIL_FILES, {"registry/bounds.json": bounds_path})),
             report(False, diagnostics, registry_document), schema_refuses=[bounds_path] if schema_refuses else ())


billing_bounds_row(
    "assemble-bound-form", "§§6.1, 6.3",
    "A repository's bounds state maxAssemblyEntries, which only the standard states, and a bound holds format, a "
    "keyword registry section 3.2 names only as refused: each is FED-BOUND-FORM. reading: located at the member.",
    BIL_BOUNDS_FORM, [diag("FED-BOUND-FORM", "bounds", "/kinds/0/maxAssemblyEntries", "billing"),
                      diag("FED-BOUND-FORM", "bounds", "/kinds/0/fields/1/bound/format", "billing")],
    schema_refuses=True)

assemble("assemble-bound-environment", "§6.4",
         "In an assembly where the repository serves prod alone, its bounds name dev, which it does not serve, and "
         "the standard's name staging, which the manifest does not: each is FED-BOUND-ENVIRONMENT. reading: located "
         "at the environment's member.",
         FED_B, world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_PROD,
                                                        "registry/bounds.json": BIL_BOUNDS_ENV_DEV}),
                      standard=with_path(SC, STD_FILES, {"registry.json": STD_REG_SUBSET,
                                                         "bounds.json": STD_BOUNDS_STAGING})),
         report(False, [diag("FED-BOUND-ENVIRONMENT", "bounds", "/kinds/0/fields/0/environments/dev", "billing"),
                        diag("FED-BOUND-ENVIRONMENT", "bounds", "/kinds/0/fields/0/environments/staging", "standard")],
                REG_B))

assemble("assemble-bound-kind", "§6.1",
         "The repository bounds db-rolee, a misspelt kind neither governed nor pinned, and the standard bounds topic, "
         "which the assembly pins but the standard does not govern: each is FED-BOUND-KIND. The repository's bound of "
         "topic, a kind the assembly pins, is admitted. reading: located at the item's kind.",
         FED_TOPIC, world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_TOPIC,
                                                            "registry/bounds.json": BIL_BOUNDS_KIND,
                                                            "kinds/topic.json": TOPIC}),
                          standard=with_path(SC, STD_FILES, {"bounds.json": STD_BOUNDS_KIND})),
         report(False, [diag("FED-BOUND-KIND", "bounds", "/kinds/1/kind", "billing"),
                        diag("FED-BOUND-KIND", "bounds", "/kinds/1/kind", "standard")], REG_TOPIC))

billing_bounds_row(
    "assemble-bound-pointer-unreachable", "§6.1",
    "A field at /connectionLimits, a misspelt member the kind's closed schema cannot reach, is "
    "FED-BOUND-POINTER-UNREACHABLE: it would bound nothing and look like a limit. reading: located at the "
    "field's pointer.",
    BIL_BOUNDS_UNREACHABLE, [diag("FED-BOUND-POINTER-UNREACHABLE", "bounds", "/kinds/0/fields/1/pointer", "billing")])

billing_bounds_row(
    "assemble-bound-not-comparable", "§6.3",
    "A bound holds pattern, a replacement whose comparison would be language inclusion: FED-BOUND-NOT-COMPARABLE at "
    "the keyword, though the standard bounds no field at that pointer.",
    BIL_BOUNDS_PATTERN, [diag("FED-BOUND-NOT-COMPARABLE", "bounds", "/kinds/0/fields/1/bound/pattern", "billing")],
    schema_refuses=True)

billing_bounds_row(
    "assemble-bound-overlap", "§6.3",
    "A repository field at /privileges/0 can match a position the standard's /privileges/* matches without being "
    "equal to it: FED-BOUND-OVERLAP. Its field at /privileges/*, equal to the standard's, is compared. reading: "
    "located at the overlapping field's pointer.",
    BIL_BOUNDS_OVERLAP, [diag("FED-BOUND-OVERLAP", "bounds", "/kinds/0/fields/3/pointer", "billing")])

WIDENS = [
    ("type", 5, {"type": ["integer", "string"]}, "/kinds/0/fields/5/bound/type",
     "Type: string is not inside the standard's number."),
    ("value-set", 4, {"enum": ["gold", "platinum"]}, "/kinds/0/fields/4/bound/enum",
     "Value set: platinum is not in the standard's enum, and the standard's bound refuses it."),
    ("lower-bound", 2, {"minimum": 0, "maximum": 10, "exclusiveMaximum": 8}, "/kinds/0/fields/2/bound/minimum",
     "Lower bound: 0 is below the standard's minimum of 1."),
    ("upper-bound-per-row", 2, {"type": "integer", "exclusiveMinimum": 1, "exclusiveMaximum": 11},
     "/kinds/0/fields/2/bound/exclusiveMaximum",
     "Upper bound: exclusiveMaximum 11 is looser than maximum 10, and is reported although type integer rules out "
     "every value in between: the comparison is per row."),
    ("length", 1, {"maxLength": 50, "patterns": ["^payments-"]}, "/kinds/0/fields/1/bound/maxLength",
     "Length: a maxLength of 50 above the standard's 40."),
    ("item-count", 3, {"maxItems": 7, "uniqueItems": True}, "/kinds/0/fields/3/bound/maxItems",
     "Item count: a maxItems of 7 above the standard's 6."),
    ("member-count", 0, {"maxProperties": 9, "required": ["team"]}, "/kinds/0/fields/0/bound/maxProperties",
     "Member count: a maxProperties of 9 above the standard's 8."),
    ("uniqueness", 3, {"maxItems": 3, "uniqueItems": False}, "/kinds/0/fields/3/bound/uniqueItems",
     "Uniqueness: uniqueItems false where the standard's is true."),
    ("value-refused", 1, {"enum": ["payments-api", ""], "maxLength": 20}, "/kinds/0/fields/1/bound/enum",
     "A value the bound names that the standard's whole bound refuses: the empty string fails its minLength of 1, "
     "although the standard states no value set to compare with."),
]
for name, field, bound, pointer, what in WIDENS:
    path = app_variant(name, field, bound)
    assemble(f"assemble-widens-{name}", "§6.2",
             what + " FED-BOUND-WIDENS at the repository's member; every value still meets both bounds. reading: "
             "located at the keyword.",
             FED_T, {"payments": with_path(PC, {"bounds.json": path, "registry.json": PAY_REG}, {}), "standard": T_STD},
             report(False, [diag("FED-BOUND-WIDENS", "bounds", pointer, "payments")], REG_T))
path = app_variant("max-entries", None, None, max_entries=12)
assemble("assemble-widens-max-entries", "§6.2",
         "Entry count: a maxEntries of 12 above the standard's 10 is FED-BOUND-WIDENS at the member.",
         FED_T, {"payments": with_path(PC, {"bounds.json": path, "registry.json": PAY_REG}, {}), "standard": T_STD},
         report(False, [diag("FED-BOUND-WIDENS", "bounds", "/kinds/0/maxEntries", "payments")], REG_T))

billing_bounds_row(
    "assemble-widens-in-prod", "§6.4",
    "A repository bound of 150 is tight enough beside the standard's 200, but not in prod, where the standard's "
    "effective bound is 100: FED-BOUND-WIDENS at the repository's bound, since it states no prod member. reading: "
    "located at the keyword.",
    BIL_BOUNDS_PROD_WIDE, [diag("FED-BOUND-WIDENS", "bounds", "/kinds/0/fields/0/bound/maximum", "billing")])

billing_bounds_row(
    "assemble-widens-own-bound", "§6.4",
    "Within one document, a prod bound of 60 is looser than its own field's 50: FED-BOUND-WIDENS at the environment's "
    "member, though 60 is within the standard's 100 in prod. reading: located at the keyword.",
    BIL_BOUNDS_ENV_WIDE, [diag("FED-BOUND-WIDENS", "bounds", "/kinds/0/fields/0/environments/prod/maximum", "billing")])

assemble("assemble-value-bound", "§6.5",
         "Values are checked against both bounds whatever the comparison says: 60 in dev fails the repository's 50, "
         "and 120 in prod fails the repository's 50 and the standard's 100 there. Each is FED-VALUE-BOUND, with "
         "source naming the source whose bound it fails.",
         FED_A, world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_VALUE})),
         report(False, [
             diag("FED-VALUE-BOUND", "value", "/connectionLimit", "billing", entry=BILLING_API_ENTRY, environment="dev"),
             diag("FED-VALUE-BOUND", "value", "/connectionLimit", "billing", entry=BILLING_API_ENTRY, environment="prod"),
             diag("FED-VALUE-BOUND", "value", "/connectionLimit", "standard", entry=BILLING_API_ENTRY,
                  environment="prod")], REG_VALUE))

billing_bounds_row(
    "assemble-entries-per-source", "§6.5",
    "A repository's own maxEntries of 1 against its two db-role entries: FED-BOUND-ENTRIES at its first entry beyond "
    "it. reading: the diagnostic names that entry, at its pointer in the source's registry.",
    BIL_BOUNDS_MAX_1, [diag("FED-BOUND-ENTRIES", "registry", "/entries/1", "billing",
                            entry=("db-role", "billing-backfill"))])

assemble("assemble-entries-assembly", "§6.5",
         "The standard's maxAssemblyEntries of 2 against three db-role entries in the assembled registry: "
         "FED-BOUND-ENTRIES at the third, with source naming the source that holds it. reading: located at that "
         "entry in its source's registry, as section 4 step 6 locates an entry's diagnostics.",
         FED_J, world(standard=with_path(SC, STD_FILES, {"bounds.json": STD_BOUNDS_ASSEMBLY_2}),
                      billing_jobs=with_path(BC, {"jobs/registry.json": JOBS_REG}, {})),
         report(False, [diag("FED-BOUND-ENTRIES", "registry", "/entries/0", "billing-jobs",
                             entry=("db-role", "billing-jobs"))], REG_J))

# ---------------------------------------------------------------------------------------------------
# Index checker (section 5.1).


def check_index(identity, description, federation, sources, index_path, expected, schema_refuses=()):
    inputs = {"federation": federation, "sources": sources, "known": NO_KNOWN, "index": index_path}
    outputs = {"schemaRefuses": list(schema_refuses)} if schema_refuses else {}
    row(identity, "§5.1", "check-index", description, inputs, expected, **outputs)


check_index("index-check-passes", "The index check assembles again at the index's commits, and the index it would "
            "write equals the given one, JCS for JCS.", FED_A, SRC_A, OUT_A["index"], report(True, (), REG_A))
check_index("index-check-content-digest", "The repository's registry is given in another layout: its digest is "
            "unchanged and its content digest is not, FED-INDEX-MISMATCH at that document's contentDigest.",
            FED_A, world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_JCS})), OUT_A["index"],
            report(False, [diag("FED-INDEX-MISMATCH", "index", "/sources/0/documents/1/contentDigest")], REG_A))
check_index("index-check-manifest-digest", "A manifest that names the repository's environments, all of them, "
            "assembles the same registry under another digest: FED-INDEX-MISMATCH at /federation/digest.",
            FED_A_EXPLICIT, SRC_A, OUT_A["index"],
            report(False, [diag("FED-INDEX-MISMATCH", "index", "/federation/digest")], REG_A))
tampered = copy.deepcopy(IDX_A)
tampered["sources"][0]["documents"][0]["role"] = "kind"
TAMPERED = canonical("vectors/index-check-other-difference/index.json", tampered)
check_index("index-check-other-difference", "An index whose bounds document is recorded with the role kind: "
            "FED-INDEX-MISMATCH at the first differing pointer.", FED_A, SRC_A, TAMPERED,
            report(False, [diag("FED-INDEX-MISMATCH", "index", "/sources/0/documents/0/role")], REG_A))
check_index("index-check-assembly-error", "The second assembly finds an error: the check fails with that error's "
            "diagnostics. reading: no FED-INDEX-MISMATCH is reported, since no index is written to compare.",
            FED_A, world(billing=with_path(BC, BIL_FILES, {"registry/registry.json": BIL_REG_OWNER})), OUT_A["index"],
            report(False, [diag("REG-ENTRY-OWNER", "registry", "/entries/0/owner", "billing", entry=BILLING_API_ENTRY)],
                   REG_OWNER))

# ---------------------------------------------------------------------------------------------------
# The single registry, its locks, and the assembled locks (section 7).

SINGLE = copied("single/registry.json", OLD / "vectors" / "valid-two-environments" / "registry.json")
SINGLE_DOC = document_of(SINGLE)
SINGLE_KINDS = ["kinds/database.json", "kinds/db-role.json"]
for environment in ("dev", "prod"):
    resolved = resolve(SINGLE_DOC, environment)
    old = (OLD / "vectors" / "valid-two-environments" / f"resolved-{environment}.json").read_bytes()
    assert jcs(resolved).encode("utf-8") == old, environment
    canonical(f"single/resolved-{environment}.json", resolved)
single_owner = parse((OLD / "vectors" / "valid-two-environments" / "registry.json").read_bytes())
single_owner["entries"][1]["owner"] = "team-payments"
SINGLE_OWNER = pretty("single/registry-owner.json", single_owner)
single_401 = dict(SINGLE_DOC, version="4.0.1")
SINGLE_401 = pretty("single/registry-4.0.1.json", single_401)


def lock(serial, registry_document, index_document=None, sources=None, emitters=None) -> dict:
    document = {"lockFormatVersion": "1.1.0", "serial": serial,
                "registry": {"id": registry_document["id"], "version": registry_document["version"],
                             "digest": digest(registry_document)},
                "kinds": registry_document["kinds"],
                "resolved": [{"environment": e, "digest": digest(resolve(registry_document, e))}
                             for e in registry_document["environments"]]}
    if index_document is not None:
        document["index"] = {"digest": digest(index_document)}
        document["sources"] = sources
    if emitters is not None:
        document["emitters"] = emitters
    return document


def statement(index_item: dict) -> dict:
    return {"repository": index_item["repository"], "commit": index_item["commit"], "documents": index_item["documents"]}


def signature_document(kind: str, subject: str, sign, public: str) -> bytes:
    selector = "lockSignatureVersion" if kind == "lock" else "sourceSignatureVersion"
    member = "lockDigest" if kind == "lock" else "sourceDigest"
    prefix = b"judgment-pack-registry/lock-signature/1:" if kind == "lock" else b"judgment-pack-registry/source-signature/1:"
    message = prefix + jcs({member: subject, selector: "1.1.0"}).encode("ascii")
    document = {"algorithm": "ed25519", member: subject, selector: "1.1.0", "publicKey": public,
                "signature": sign(message).hex()}
    data = (jcs(document) + "\n").encode("ascii")
    assert len(data) <= 4096 and b"\\" not in data and data.count(b"\n") == 1
    return data


def sign_source(relative, index_item, sign, public, commit=None) -> str:
    item = dict(index_item, commit=commit) if commit else index_item
    return put(relative, signature_document("source", digest(statement(item)), sign, public))


def lock_sources(index_document, signatures: dict) -> list:
    return [{"name": item["name"], "role": item["role"], "repository": item["repository"],
             "statement": digest(statement(item)), "signature": digest(parse(FILES[signatures[item["name"]]]))}
            for item in index_document["sources"]]


def write_lock(relative, document, sign=SIGN1, public=PK1, signed=True) -> str:
    canonical(relative, document)
    if signed:
        put(relative + ".sig.json", signature_document("lock", digest(document), sign, public))
    return relative


SIG_BILLING = sign_source("signatures/billing.json", IDX_A["sources"][0], SIGN2, PK2)
SIG_STANDARD = sign_source("signatures/standard.json", IDX_A["sources"][1], SIGN1, PK1)
SIG_BILLING_T3 = sign_source("signatures/billing-wrong-key.json", IDX_A["sources"][0], SIGN3, PK3)
SIG_BILLING_PROD = sign_source("signatures/billing-serves-prod.json", document_of(OUT_B["index"])["sources"][0],
                               SIGN2, PK2)
SIG_BILLING_OC = sign_source("signatures/billing-another-commit.json", IDX_A["sources"][0], SIGN2, PK2, BC_OTHER)

L42_DOC = lock(42, SINGLE_DOC)
L43_DOC = lock(43, SINGLE_DOC)
L42 = write_lock("locks/single-42.lock.json", L42_DOC)
L43 = write_lock("locks/single-43.lock.json", L43_DOC)
LMAX = write_lock("locks/single-max.lock.json", lock(9007199254740991, SINGLE_DOC), signed=False)

EMITTER = pretty("emitters/db-roles.json", {
    "emitterManifestVersion": "1.0.0", "id": "https://example.invalid/emitters/db-roles", "version": "1.0.0",
    "owner": "platform-data", "reads": [{"kind": "db-role", "id": "https://example.invalid/kinds/db-role",
                                         "versions": "^1.2.0"}],
    "requestVersions": ["1.0.0"], "environments": "each", "command": ["tools/emit-db-roles"], "owns": ["gen/**"]})
GEN_SQL = put("emitters/gen/db-roles.sql", b"-- Synthetic: the roles of one registry, as a test emitter writes them.\n")
GEN_SH = put("emitters/gen/grant.sh", b"#!/bin/sh\n# Synthetic: grants nothing.\nexit 0\n")
EMITTER_FILES = [{"path": "gen/db-roles.sql", "mode": "0644", "file": GEN_SQL},
                 {"path": "gen/grant.sh", "mode": "0755", "file": GEN_SH}]
LE43_DOC = lock(43, SINGLE_DOC, emitters=[{
    "path": "emitters/db-roles.json", "digest": digest(document_of(EMITTER)),
    "files": [{"path": f["path"], "mode": f["mode"], "digest": sha(FILES[f["file"]])} for f in EMITTER_FILES]}])
LE43 = write_lock("locks/single-43-emitters.lock.json", LE43_DOC, signed=False)

LA_SOURCES = lock_sources(IDX_A, {"billing": SIG_BILLING, "standard": SIG_STANDARD})
LA_DOC = lock(7, REG_A, IDX_A, LA_SOURCES)
assert write_lock(LA_PATH, LA_DOC) == LA_PATH
LA6 = write_lock("locks/assembled-6.lock.json", lock(6, REG_A, IDX_A, LA_SOURCES), signed=False)
LAE_DOC = lock(8, REG_A, IDX_A, LA_SOURCES, emitters=[{
    "source": "billing", "path": "emitters/db-roles.json", "digest": digest(document_of(EMITTER)),
    "files": [{"path": f["path"], "mode": f["mode"], "digest": sha(FILES[f["file"]])} for f in EMITTER_FILES]}])
LAE = write_lock("locks/assembled-8-emitters.lock.json", LAE_DOC, signed=False)
LA_T3_DOC = lock(7, REG_A, IDX_A, lock_sources(IDX_A, {"billing": SIG_BILLING_T3, "standard": SIG_STANDARD}))
LA_T3 = write_lock("locks/assembled-7-billing-wrong-key.lock.json", LA_T3_DOC)
LA_OC_DOC = lock(7, REG_A, IDX_A, lock_sources(IDX_A, {"billing": SIG_BILLING_OC, "standard": SIG_STANDARD}))
LA_OC = write_lock("locks/assembled-7-billing-another-commit.lock.json", LA_OC_DOC)
SIG_STANDARD_T2 = sign_source("signatures/standard-repository-key.json", IDX_A["sources"][1], SIGN2, PK2)
LA_SR_DOC = lock(7, REG_A, IDX_A, lock_sources(IDX_A, {"billing": SIG_BILLING, "standard": SIG_STANDARD_T2}))
LA_SR = write_lock("locks/assembled-7-standard-repository-key.lock.json", LA_SR_DOC)
# A lock whose billing statement is the one the signature at another commit names, not the index's: signed by
# the standard owner, so that only the statement rebuilt from the index tells it apart.
statement_other = copy.deepcopy(LA_OC_DOC)
statement_other["sources"][0]["statement"] = parse(FILES[SIG_BILLING_OC])["sourceDigest"]
assert statement_other["sources"][0]["statement"] != LA_OC_DOC["sources"][0]["statement"]
LA_SO = write_lock("vectors/verify-statement-another-commit/lock.json", statement_other)

# ---------------------------------------------------------------------------------------------------
# Lock writer (section 8). reading: a writer's refusal is compared by its code alone, since section 2.1 gives
# writing a lock no report.

ASSEMBLED_SIGNERS = {"key": PK1, "repositories": {BILLING_REPO: PK2}}
SINGLE_SIGNERS = {"key": PK1}


def refused(*codes):
    return {"refused": list(codes)}


def write(identity, section, description, inputs, expected):
    if isinstance(expected, dict):
        description += (" reading: a writer's refusal is compared by its code alone, since section 2.1 gives "
                        "writing a lock no report.")
    row(identity, section, "write-lock", description, inputs, expected)


SINGLE_INPUT = {"registry": SINGLE, "kinds": SINGLE_KINDS}
write("write-first-serial", "§8", "A single registry's first lock: no previous lock, and the first serial, 42, "
      "given out of band. The lock is its JCS bytes.", dict(SINGLE_INPUT, firstSerial=42), L42)
write("write-next-serial", "§8", "Given the previous lock of the registry id, the writer writes the serial one above "
      "it.", dict(SINGLE_INPUT, previous=L42), L43)
write("write-emitters", "§§7, 8", "An emitter manifest whose host check exits 0: the lock lists the manifest by path "
      "and digest and every file its owns matches, sorted by path, each with its mode and digest, and no source, "
      "since the registry is single.",
      dict(SINGLE_INPUT, previous=L42, emitters=[{"manifest": EMITTER, "path": "emitters/db-roles.json", "check": 0,
                                                  "files": EMITTER_FILES}]), LE43)
ASSEMBLY_INPUT = {"federation": FED_A, "sources": SRC_A, "known": NO_KNOWN,
                  "sourceSignatures": [SIG_BILLING, SIG_STANDARD], "signers": ASSEMBLED_SIGNERS}
write("write-assembled", "§§7, 8", "An assembly's lock: the index's digest, and for each source its name, role, "
      "repository, the digest of its statement rebuilt from the index, and the digest of the source signature the "
      "writer verified, each by the key the signer set names.", dict(ASSEMBLY_INPUT, previous=LA6), LA_PATH)
write("write-assembled-emitters", "§§7, 8", "An assembly's lock with an emitter manifest from the repository "
      "source: its item names that source, and the serial is one above the previous lock's.",
      dict(ASSEMBLY_INPUT, previous=LA_PATH, emitters=[{"source": "billing", "manifest": EMITTER,
                                                        "path": "emitters/db-roles.json", "check": 0,
                                                        "files": EMITTER_FILES}]), LAE)
write("write-registry-invalid", "§8", "A registry that validation refuses is never locked: LOCK-REGISTRY-INVALID.",
      {"registry": SINGLE_OWNER, "kinds": SINGLE_KINDS, "previous": L42}, refused("LOCK-REGISTRY-INVALID"))
write("write-assembly-invalid", "§8", "An assembly with an error, here an environment gap, is never locked: "
      "LOCK-REGISTRY-INVALID. Each source signature is over its source's statement at these commits, so nothing "
      "else is refused.",
      dict(ASSEMBLY_INPUT, federation=FED_B, sources=world(billing=with_path(BC, BIL_FILES, {
          "registry/registry.json": BIL_REG_PROD})), sourceSignatures=[SIG_BILLING_PROD, SIG_STANDARD],
           previous=LA6), refused("LOCK-REGISTRY-INVALID"))
write("write-previous-other-registry", "§8", "A previous lock of another registry id: LOCK-UNEXPECTED-REGISTRY.",
      dict(SINGLE_INPUT, previous=LA_PATH), refused("LOCK-UNEXPECTED-REGISTRY"))
write("write-serial-exhausted", "§8", "A previous lock whose serial is 2^53 - 1 leaves no next serial: LOCK-FORM.",
      dict(SINGLE_INPUT, previous=LMAX), refused("LOCK-FORM"))
write("write-emitter-check-fails", "§8", "The host's check of the emitter exits 1: LOCK-EMITTER-MISMATCH, and no "
      "lock is written.",
      dict(SINGLE_INPUT, previous=L42, emitters=[{"manifest": EMITTER, "path": "emitters/db-roles.json", "check": 1,
                                                  "files": EMITTER_FILES}]), refused("LOCK-EMITTER-MISMATCH"))
write("write-source-signature-wrong-key", "§§8, 11", "The repository's source signature is by another key than the "
      "signer set names: refused with that signature's code, LOCK-SIG-UNEXPECTED-KEY, and no lock is written.",
      dict(ASSEMBLY_INPUT, sourceSignatures=[SIG_BILLING_T3, SIG_STANDARD], previous=LA6),
      refused("LOCK-SIG-UNEXPECTED-KEY"))

# ---------------------------------------------------------------------------------------------------
# Lock checker (section 9) and coverage (section 9.1).

SINGLE_EXPECT = {"registryId": SINGLE_ID, "requireIndex": False}
ASSEMBLED_EXPECT = {"registryId": ASSEMBLED_ID, "requireIndex": True}
A_KINDS = ["kinds/database.json", "kinds/db-role.json"]
EMITTERS_GIVEN = [{"manifest": EMITTER, "path": "emitters/db-roles.json", "files": EMITTER_FILES}]


def check(identity, section, description, inputs, expected, schema_refuses=()):
    outputs = {"schemaRefuses": list(schema_refuses)} if schema_refuses else {}
    row(identity, section, "check-lock", description, inputs, expected, **outputs)


def single_check(lock_path=L42, **changes):
    inputs = {"lock": lock_path, "registry": SINGLE, "kinds": SINGLE_KINDS, "expect": SINGLE_EXPECT}
    inputs.update(changes)
    return inputs


def assembled_check(lock_path=LA_PATH, **changes):
    inputs = {"lock": lock_path, "registry": OUT_A["registry"], "kinds": A_KINDS, "index": OUT_A["index"],
              "expect": ASSEMBLED_EXPECT}
    inputs.update(changes)
    return inputs


L42_LF = canonical("vectors/check-final-line-feed/lock.json", L42_DOC, final_line_feed=True)
L42_PRETTY = pretty("vectors/check-not-canonical/lock.json", L42_DOC)
L_SERIAL_0 = canonical("vectors/check-lock-form/lock.json", dict(L42_DOC, serial=0))
kinds_changed = copy.deepcopy(L42_DOC)
kinds_changed["kinds"][1]["version"] = "1.2.1"
L_KINDS = canonical("vectors/check-kinds-mismatch/lock.json", kinds_changed)
resolved_changed = copy.deepcopy(L42_DOC)
resolved_changed["resolved"][0]["digest"] = resolved_changed["resolved"][1]["digest"]
L_RESOLVED = canonical("vectors/check-resolved-mismatch/lock.json", resolved_changed)
sources_changed = copy.deepcopy(LA_DOC)
sources_changed["sources"][0]["statement"] = sources_changed["sources"][1]["statement"]
L_SOURCES = canonical("vectors/check-sources-mismatch/lock.json", sources_changed)
two_standards = copy.deepcopy(IDX_A)
two_standards["sources"][0]["role"] = "standard"
IDX_TWO = canonical("vectors/check-index-two-standards/index.json", two_standards)
L_TWO = canonical("vectors/check-index-two-standards/lock.json", lock(7, REG_A, two_standards, lock_sources(
    two_standards, {"billing": SIG_BILLING, "standard": SIG_STANDARD})))
# An index the lock does not name: the two-source index with another manifest's digest, its registry digest and
# items the lock's, so that its digest alone differs.
other_federation = copy.deepcopy(IDX_A)
other_federation["federation"]["digest"] = digest(document_of(FED_A_EXPLICIT))
IDX_OTHER = canonical("vectors/check-index-digest-mismatch/index.json", other_federation)
# An index the lock names by digest whose registry digest is another registry's, with the lock's items.
other_registry = copy.deepcopy(IDX_A)
other_registry["registry"]["digest"] = digest(REG_B)
IDX_OTHER_REGISTRY = canonical("vectors/check-index-registry-mismatch/index.json", other_registry)
L_OTHER_REGISTRY = write_lock("vectors/check-index-registry-mismatch/lock.json", lock(
    7, REG_A, other_registry, lock_sources(other_registry, {"billing": SIG_BILLING, "standard": SIG_STANDARD})))
GRANT_CHANGED = put("vectors/check-emitter-file-differs/grant.sh", b"#!/bin/sh\n# Synthetic: grants one more thing.\nexit 0\n")
EXTRA_SQL = put("vectors/check-emitter-unlisted-file/extra.sql", b"-- Synthetic: a file the lock does not list.\n")

check("check-single", "§9", "A single registry's lock checks: its registry, kinds and each environment's resolved "
      "digest are the registry's. reading: the report's registry is the checked registry's digest, present once its "
      "validation passed registry section 7's step 3.", single_check(), report(True, (), SINGLE_DOC))
check("check-final-line-feed", "§7", "A lock written with one final line feed, which is not part of the document, "
      "checks.", single_check(L42_LF), report(True, (), SINGLE_DOC))
check("check-assembled", "§9", "An assembled lock checks with its index: the index's digest and registry digest are "
      "the lock's, it has one standard item, and each source's name, role, repository and statement are the "
      "index's.", assembled_check(), report(True, (), REG_A))
check("check-emitters", "§9", "A lock that names emitters checks with the manifest and its files as given.",
      single_check(LE43, emitters=EMITTERS_GIVEN), report(True, (), SINGLE_DOC))
check("check-assembled-emitters", "§9", "An assembled lock whose emitter item names its source checks with that "
      "source's manifest and files.", assembled_check(LAE, emitters=[dict(EMITTERS_GIVEN[0], source="billing")]),
      report(True, (), REG_A))
check("check-expected-missing", "§9", "No index requirement is given: LOCK-EXPECTED, before anything is read. "
      "reading: an expected input's diagnostic is located at the lock's root.",
      single_check(expect={"registryId": SINGLE_ID}), report(False, [diag("LOCK-EXPECTED", "lock", "")]))
check("check-expected-id-not-uri", "§9", "An expected registry id that is not an absolute URI: LOCK-EXPECTED. "
      "reading: located at the lock's root.",
      single_check(expect={"registryId": "platform", "requireIndex": False}),
      report(False, [diag("LOCK-EXPECTED", "lock", "")]))
check("check-lock-form", "§9", "A serial of 0 is not of the lock's form: LOCK-FORM, and the check ends. reading: "
      "located at the member.", single_check(L_SERIAL_0), report(False, [diag("LOCK-FORM", "lock", "/serial")]),
      schema_refuses=[L_SERIAL_0])
check("check-not-canonical", "§7", "A lock written indented is not its JCS bytes: LOCK-NOT-CANONICAL. A re-formatted "
      "lock is an edited lock. reading: located at the root.", single_check(L42_PRETTY),
      report(False, [diag("LOCK-NOT-CANONICAL", "lock", "")]))
check("check-unexpected-registry", "§9", "The lock's registry id is not the expected one: LOCK-UNEXPECTED-REGISTRY. "
      "reading: located at /registry/id.", single_check(expect={"registryId": ASSEMBLED_ID, "requireIndex": False}),
      report(False, [diag("LOCK-UNEXPECTED-REGISTRY", "lock", "/registry/id")]))
check("check-index-required", "§9", "An index is required and the lock names none: LOCK-INDEX-REQUIRED. reading: "
      "located at /index, the pointer it would have.", single_check(expect={"registryId": SINGLE_ID,
                                                                             "requireIndex": True}),
      report(False, [diag("LOCK-INDEX-REQUIRED", "lock", "/index")]))
check("check-registry-invalid", "§9", "The registry given has an error: LOCK-REGISTRY-INVALID beside the "
      "validation's own diagnostic, and the check ends. reading: located at the registry's root.",
      single_check(registry=SINGLE_OWNER),
      report(False, [diag("LOCK-REGISTRY-INVALID", "registry", ""),
                     diag("REG-ENTRY-OWNER", "registry", "/entries/1/owner", entry=BILLING_API_ENTRY)],
             single_owner))
check("check-registry-mismatch", "§9", "A valid registry that is not the one the lock names: LOCK-REGISTRY-MISMATCH "
      "at /registry, and each environment's resolved digest differs, since a resolved registry names its "
      "registry's digest.", single_check(registry=SINGLE_401),
      report(False, [diag("LOCK-REGISTRY-MISMATCH", "lock", "/registry"),
                     diag("LOCK-RESOLVED-MISMATCH", "lock", "/resolved/0"),
                     diag("LOCK-RESOLVED-MISMATCH", "lock", "/resolved/1")], single_401))
check("check-kinds-mismatch", "§9", "The lock's second pin names another version than the registry's: "
      "LOCK-KINDS-MISMATCH at the item.", single_check(L_KINDS),
      report(False, [diag("LOCK-KINDS-MISMATCH", "lock", "/kinds/1")], SINGLE_DOC))
check("check-resolved-mismatch", "§9", "The lock names prod's resolved digest for dev: LOCK-RESOLVED-MISMATCH at the "
      "item.", single_check(L_RESOLVED), report(False, [diag("LOCK-RESOLVED-MISMATCH", "lock", "/resolved/0")],
                                               SINGLE_DOC))
no_index = assembled_check()
del no_index["index"]
check("check-index-missing", "§9", "An assembled lock checked without its index: LOCK-INDEX-MISSING, a refusal and "
      "never a skipped check. reading: located at the lock's /index.", no_index,
      report(False, [diag("LOCK-INDEX-MISSING", "lock", "/index")], REG_A))
check("check-index-two-standards", "§9", "An index with two standard items, which its lock names by digest: "
      "LOCK-INDEX-MISMATCH. The index schema refuses it too. reading: located at the index's /sources.",
      assembled_check(L_TWO, index=IDX_TWO), report(False, [diag("LOCK-INDEX-MISMATCH", "index", "/sources")], REG_A),
      schema_refuses=[IDX_TWO])
check("check-index-digest-mismatch", "§9", "An index whose digest is not the lock's index digest, though its "
      "registry digest and items are the lock's: LOCK-INDEX-MISMATCH. reading: located at the lock's /index, as "
      "LOCK-REGISTRY-MISMATCH is at the lock's /registry.", assembled_check(index=IDX_OTHER),
      report(False, [diag("LOCK-INDEX-MISMATCH", "lock", "/index")], REG_A))
check("check-index-registry-mismatch", "§9", "An index the lock names by digest whose registry digest is another "
      "registry's than the lock's: LOCK-INDEX-MISMATCH. reading: located at the index's /registry/digest.",
      assembled_check(L_OTHER_REGISTRY, index=IDX_OTHER_REGISTRY),
      report(False, [diag("LOCK-INDEX-MISMATCH", "index", "/registry/digest")], REG_A))
check("check-index-unlocked", "§9", "An index given for a lock that names none: LOCK-INDEX-UNLOCKED, so that no "
      "caller believes provenance was checked. reading: located at the index's root.", single_check(index=OUT_A["index"]),
      report(False, [diag("LOCK-INDEX-UNLOCKED", "index", "")], SINGLE_DOC))
check("check-sources-mismatch", "§9", "The lock's statement digest for the repository is not that of the statement "
      "rebuilt from the index's item: LOCK-SOURCES-MISMATCH at the item.", assembled_check(L_SOURCES),
      report(False, [diag("LOCK-SOURCES-MISMATCH", "lock", "/sources/0")], REG_A))
check("check-emitters-missing", "§9", "A lock that names emitters, checked without them: LOCK-EMITTER-MISSING at "
      "/emitters.", single_check(LE43), report(False, [diag("LOCK-EMITTER-MISSING", "lock", "/emitters")], SINGLE_DOC))
check("check-emitter-file-missing", "§9", "A file the lock lists is not given: LOCK-EMITTER-MISSING at the item.",
      single_check(LE43, emitters=[dict(EMITTERS_GIVEN[0], files=EMITTER_FILES[:1])]),
      report(False, [diag("LOCK-EMITTER-MISSING", "lock", "/emitters/0/files/1")], SINGLE_DOC))
check("check-emitter-file-differs", "§9", "A file given differs from the lock's item: LOCK-EMITTER-MISMATCH at the "
      "item.", single_check(LE43, emitters=[dict(EMITTERS_GIVEN[0], files=[
          EMITTER_FILES[0], {"path": "gen/grant.sh", "mode": "0755", "file": GRANT_CHANGED}])]),
      report(False, [diag("LOCK-EMITTER-MISMATCH", "lock", "/emitters/0/files/1")], SINGLE_DOC))
check("check-emitter-unlisted-file", "§9", "A file the manifest's owns matches that the lock does not list: "
      "LOCK-EMITTER-MISMATCH. reading: located at the emitter's item.",
      single_check(LE43, emitters=[dict(EMITTERS_GIVEN[0], files=EMITTER_FILES + [
          {"path": "gen/extra.sql", "mode": "0644", "file": EXTRA_SQL}])]),
      report(False, [diag("LOCK-EMITTER-MISMATCH", "lock", "/emitters/0")], SINGLE_DOC))


def coverage(identity, description, inputs, expected):
    row(identity, "§9.1", "coverage", description, inputs, expected)


PROD_EXPECT = dict(SINGLE_EXPECT, environment="prod")
coverage("coverage-resolved", "A prod loader holds prod's resolved registry: its environment, registry digest and "
         "digest are the lock's for prod. reading: coverage writes the report of a lock check, with no registry.",
         {"lock": L42, "expect": PROD_EXPECT, "resolved": "single/resolved-prod.json"}, report(True))
coverage("coverage-wrong-environment", "A dev resolved registry handed to a prod loader is not covered, although the "
         "lock names it: LOCK-NOT-COVERED. reading: located at the lock's resolved item for the expected environment.",
         {"lock": L42, "expect": PROD_EXPECT, "resolved": "single/resolved-dev.json"},
         report(False, [diag("LOCK-NOT-COVERED", "lock", "/resolved/1")]))
coverage("coverage-file", "A generated file whose path, mode and digest an emitters item lists is covered.",
         {"lock": LE43, "expect": PROD_EXPECT, "file": EMITTER_FILES[1]}, report(True))
coverage("coverage-file-mode", "A file whose path and digest the lock lists, given with another mode, is not covered: "
         "LOCK-NOT-COVERED. reading: located at the lock's /emitters.",
         {"lock": LE43, "expect": PROD_EXPECT, "file": dict(EMITTER_FILES[1], mode="0644")},
         report(False, [diag("LOCK-NOT-COVERED", "lock", "/emitters")]))
coverage("coverage-unlisted-file", "A file no emitters item lists is not covered: LOCK-NOT-COVERED. reading: located "
         "at the lock's /emitters.",
         {"lock": LE43, "expect": PROD_EXPECT, "file": {"path": "gen/extra.sql", "mode": "0644", "file": EXTRA_SQL}},
         report(False, [diag("LOCK-NOT-COVERED", "lock", "/emitters")]))
ASSEMBLED_PROD = dict(ASSEMBLED_EXPECT, environment="prod")
coverage("coverage-file-assembled", "In an assembled lock, a file is covered by an emitters item of its source "
         "that lists its path, mode and digest.", {"lock": LAE, "expect": ASSEMBLED_PROD,
                                                   "file": dict(EMITTER_FILES[1], source="billing")}, report(True))
coverage("coverage-file-other-source", "The same path, mode and digest, of another source than the item's: "
         "LOCK-NOT-COVERED. reading: located at the lock's /emitters.",
         {"lock": LAE, "expect": ASSEMBLED_PROD, "file": dict(EMITTER_FILES[1], source="standard")},
         report(False, [diag("LOCK-NOT-COVERED", "lock", "/emitters")]))
coverage("coverage-environment-missing", "Coverage is given no environment: LOCK-EXPECTED. reading: located at the "
         "lock's root.", {"lock": L42, "expect": SINGLE_EXPECT, "resolved": "single/resolved-prod.json"},
         report(False, [diag("LOCK-EXPECTED", "lock", "")]))
coverage("coverage-not-canonical", "Coverage holds the lock to step 1 of section 9 first: a lock written indented is "
         "LOCK-NOT-CANONICAL, although the resolved registry given is prod's, which the lock names. reading: "
         "located at the lock's root.", {"lock": L42_PRETTY, "expect": PROD_EXPECT, "resolved": "single/resolved-prod.json"},
         report(False, [diag("LOCK-NOT-CANONICAL", "lock", "")]))

# ---------------------------------------------------------------------------------------------------
# Lock signature verifier (sections 10 and 11). A record is the rows' own form: null for none, {"serial",
# "digest"} for a record, "unreadable" for one that exists and cannot be read, and any other value for one that
# exists and is not of its form. "concurrent" is the record another process writes after step 1 reads it;
# "writeFails" says the verifier's write fails. "expectedRecord" is the record after the verification.

D42 = digest(L42_DOC)
D43 = digest(L43_DOC)
DLE43 = digest(LE43_DOC)
DLA = digest(LA_DOC)
D40 = digest(lock(40, SINGLE_DOC))
D41 = digest(lock(41, SINGLE_DOC))
D3 = digest(lock(3, SINGLE_DOC))
SIG42 = L42 + ".sig.json"
SIG43 = L43 + ".sig.json"
SIGLA = LA_PATH + ".sig.json"


def record(serial, value):
    return {"serial": serial, "digest": value}


def verify(identity, section, description, inputs, expected, record_before, record_after, schema_refuses=(), **extra):
    base = {"lock": L42, "lockSignatures": [SIG42], "sourceSignatures": [], "signers": SINGLE_SIGNERS,
            "expect": SINGLE_EXPECT, "record": record_before}
    base.update(inputs)
    base.update(extra)
    outputs = {"expectedRecord": record_after}
    if schema_refuses:
        outputs["schemaRefuses"] = list(schema_refuses)
    row(identity, section, "verify", description, base, expected, **outputs)


ACCEPT = report(True)
NO_RECORD = None
ASSEMBLED_VERIFY = {"lock": LA_PATH, "lockSignatures": [SIGLA], "index": OUT_A["index"],
                    "sourceSignatures": [SIG_BILLING, SIG_STANDARD], "signers": ASSEMBLED_SIGNERS,
                    "expect": ASSEMBLED_EXPECT, "floor": 1}


def refusal(code, document="lock", pointer=""):
    return report(False, [diag(code, document, pointer)])


verify("verify-first-contact", "§11", "First contact with a floor of 1: trust on first use, which the verifier chose "
       "by giving it. The lock is accepted and its serial and digest recorded.", {"floor": 1}, ACCEPT,
       NO_RECORD, record(42, D42))
verify("verify-record-equal", "§11", "The record holds this lock's serial and digest: verifying the accepted lock "
       "again is no rollback, and needs no write.", {}, ACCEPT, record(42, D42), record(42, D42))
verify("verify-higher-serial", "§11", "A serial far above the record's is admitted: a verifier need not see every "
       "lock.", {}, ACCEPT, record(3, D3), record(42, D42))
verify("verify-rollback", "§11", "A serial below the record's: LOCK-SERIAL-ROLLBACK, and the record stays. reading: "
       "located at /serial.", {}, refusal("LOCK-SERIAL-ROLLBACK", pointer="/serial"), record(43, D43), record(43, D43))
verify("verify-serial-conflict", "§11", "Another lock with the record's serial: LOCK-SERIAL-CONFLICT, two locks "
       "claiming one place. reading: located at /serial.", {"lock": L43, "lockSignatures": [SIG43]},
       refusal("LOCK-SERIAL-CONFLICT", pointer="/serial"), record(43, DLE43), record(43, DLE43))
verify("verify-floor-alone", "§11", "No record and a floor equal to the lock's serial: admitted, and recorded.",
       {"floor": 42}, ACCEPT, NO_RECORD, record(42, D42))
verify("verify-floor-rollback", "§11", "No record and a floor above the lock's serial: LOCK-SERIAL-ROLLBACK, and no "
       "record is written. reading: located at /serial.", {"floor": 43},
       refusal("LOCK-SERIAL-ROLLBACK", pointer="/serial"), NO_RECORD, NO_RECORD)
verify("verify-floor-above-record", "§11", "A floor above the record's serial is held as a floor alone: 43 refuses "
       "the lock, though the record's 40 would admit it. reading: located at /serial.", {"floor": 43},
       refusal("LOCK-SERIAL-ROLLBACK", pointer="/serial"), record(40, D40), record(40, D40))
verify("verify-floor-above-record-admits", "§11", "A floor above the record's serial, held as a floor alone, admits a "
       "lock at or above it: 42 against a floor of 42 and a record of 40, and the lock is recorded.", {"floor": 42},
       ACCEPT, record(40, D40), record(42, D42))
verify("verify-floor-below-record", "§11", "A floor at or below the record's serial changes nothing: the record "
       "admits the lock.", {"floor": 30}, ACCEPT, record(40, D40), record(42, D42))
verify("verify-floor-below-record-refuses", "§11", "A floor below the record's serial does not lower it: the record's "
       "43 refuses the lock. reading: located at /serial.", {"floor": 10},
       refusal("LOCK-SERIAL-ROLLBACK", pointer="/serial"), record(43, D43), record(43, D43))
verify("verify-first-contact-no-floor", "§11", "No record and no floor: LOCK-EXPECTED, before the lock is read. "
       "reading: located at the lock's root.", {}, refusal("LOCK-EXPECTED"), NO_RECORD, NO_RECORD)
verify("verify-record-unreadable", "§11", "A record that exists and cannot be read: LOCK-SERIAL-STATE, never a first "
       "contact, and the floor given beside it does not stand in for it. reading: located at the lock's root.",
       {"floor": 1}, refusal("LOCK-SERIAL-STATE"), "unreadable", "unreadable")
verify("verify-record-malformed", "§11", "A record not of its form, its serial a string: LOCK-SERIAL-STATE. reading: "
       "located at the lock's root.", {"floor": 1}, refusal("LOCK-SERIAL-STATE"), {"serial": "40", "digest": D40},
       {"serial": "40", "digest": D40})
verify("verify-compare-and-set-passes", "§11", "Another process writes serial 41 after the verifier reads 40: the "
       "write's compare and set fails, the verifier reads the record again, the lock still passes, and it is "
       "written.", {"concurrent": record(41, D41)}, ACCEPT, record(40, D40), record(42, D42))
verify("verify-compare-and-set-fails", "§11", "Another process writes serial 43 after the verifier reads 40: read "
       "again, the record refuses the lock, LOCK-SERIAL-ROLLBACK, and the other process's record stands. reading: "
       "located at /serial.", {"concurrent": record(43, D43)}, refusal("LOCK-SERIAL-ROLLBACK", pointer="/serial"),
       record(40, D40), record(43, D43))
verify("verify-record-write-fails", "§11", "Every step accepts and the record cannot be written: LOCK-SERIAL-STATE, "
       "and the lock is not accepted. reading: located at the lock's root.", {"floor": 1, "writeFails": True},
       refusal("LOCK-SERIAL-STATE"), NO_RECORD, NO_RECORD)
verify("verify-assembled", "§11", "An assembled lock with its lock signature by the standard owner's key, its index, "
       "and one source signature per source, each by the key the set names and over the statement rebuilt from the "
       "index: all of the set, accepted and recorded.", ASSEMBLED_VERIFY, ACCEPT, NO_RECORD, record(7, DLA))
verify("verify-coverage", "§§9.1, 11", "A verification given prod's resolved registry and the environment prod: the "
       "lock is accepted and covers it.", {"floor": 1, "resolved": "single/resolved-prod.json",
                                          "expect": PROD_EXPECT}, ACCEPT, NO_RECORD, record(42, D42))
verify("verify-not-covered", "§§9.1, 11", "A verification given dev's resolved registry for prod: the lock signature "
       "is accepted and the lock is refused, LOCK-NOT-COVERED, so nothing is recorded. reading: located at the "
       "lock's resolved item for prod.", {"floor": 1, "resolved": "single/resolved-dev.json", "expect": PROD_EXPECT},
       refusal("LOCK-NOT-COVERED", pointer="/resolved/1"), NO_RECORD, NO_RECORD)
verify("verify-with-documents", "§11", "A verification given the registry and its kinds runs the rest of section 9 "
       "as well, and accepts. reading: the report's registry is present, as in a lock check, since a registry was "
       "validated.", {"floor": 1, "registry": SINGLE, "kinds": SINGLE_KINDS}, report(True, (), SINGLE_DOC),
       NO_RECORD, record(42, D42))

# Expected inputs (step 1).
verify("verify-expected-key-missing", "§11", "No expected key: LOCK-SIG-EXPECTED-KEY, before anything is read. "
       "reading: located at the lock's root.", {"floor": 1, "signers": {}}, refusal("LOCK-SIG-EXPECTED-KEY"),
       NO_RECORD, NO_RECORD)
verify("verify-expected-key-small-order", "§11", "An expected key of small order, under which anyone can forge: "
       "LOCK-SIG-EXPECTED-KEY. reading: located at the lock's root.",
       {"floor": 1, "signers": {"key": SMALL_ORDER_KEY}}, refusal("LOCK-SIG-EXPECTED-KEY"), NO_RECORD, NO_RECORD)
verify("verify-map-without-index", "§11", "A repository key map given with no index required: LOCK-EXPECTED. "
       "reading: located at the lock's root.", {"floor": 1, "signers": ASSEMBLED_SIGNERS},
       refusal("LOCK-EXPECTED"), NO_RECORD, NO_RECORD)
verify("verify-index-without-map", "§11", "An index required with no repository key map: LOCK-EXPECTED. reading: "
       "located at the lock's root.", dict(ASSEMBLED_VERIFY, signers=SINGLE_SIGNERS), refusal("LOCK-EXPECTED"),
       NO_RECORD, NO_RECORD)
verify("verify-map-gives-standard-key", "§11", "The map gives the repository the standard owner's key: one key in "
       "two roles, LOCK-EXPECTED. reading: located at the lock's root.",
       dict(ASSEMBLED_VERIFY, signers={"key": PK1, "repositories": {BILLING_REPO: PK1}}), refusal("LOCK-EXPECTED"),
       NO_RECORD, NO_RECORD)
verify("verify-map-shares-a-key", "§11", "The map gives one key to two repository identities: LOCK-EXPECTED. "
       "reading: located at the lock's root.",
       dict(ASSEMBLED_VERIFY, signers={"key": PK1, "repositories": {BILLING_REPO: PK2, LEDGER_REPO: PK2}}),
       refusal("LOCK-EXPECTED"), NO_RECORD, NO_RECORD)
verify("verify-map-key-small-order", "§11", "The map gives the repository a key of small order, under which anyone "
       "can forge: each key of the set is held to the trust rule, LOCK-SIG-EXPECTED-KEY, before anything is read. "
       "reading: located at the lock's root.",
       dict(ASSEMBLED_VERIFY, signers={"key": PK1, "repositories": {BILLING_REPO: SMALL_ORDER_KEY}}),
       refusal("LOCK-SIG-EXPECTED-KEY"), NO_RECORD, NO_RECORD)

# The lock signature (step 2) and its document (section 10.1).
verify("verify-lock-signature-missing", "§11", "No lock signature document: LOCK-SIG-MISSING. reading: located at the "
       "lock's root.", {"floor": 1, "lockSignatures": []}, refusal("LOCK-SIG-MISSING"), NO_RECORD, NO_RECORD)
verify("verify-second-lock-signature", "§11", "A second lock signature document beside an accepted one: "
       "LOCK-SIG-EXTRA, and the set is refused, not trimmed. reading: located at the signature document's root.",
       {"floor": 1, "lockSignatures": [SIG42, SIG42]}, refusal("LOCK-SIG-EXTRA", "signature"), NO_RECORD, NO_RECORD)
verify("verify-lock-signature-wrong-key", "§11", "A lock signature by another key than the expected one: "
       "LOCK-SIG-UNEXPECTED-KEY, the plainer reason, first. reading: located at /publicKey.",
       {"floor": 1, "lockSignatures": [put("vectors/verify-lock-signature-wrong-key/lock.sig.json", signature_document(
           "lock", D42, SIGN3, PK3))]}, refusal("LOCK-SIG-UNEXPECTED-KEY", "signature", "/publicKey"),
       NO_RECORD, NO_RECORD)
verify("verify-lock-signature-moved", "§11", "The signature of another lock, moved beside this one: "
       "LOCK-SIG-DIGEST-MISMATCH. reading: located at /lockDigest.",
       {"floor": 1, "lock": L43, "lockSignatures": [SIG42]},
       refusal("LOCK-SIG-DIGEST-MISMATCH", "signature", "/lockDigest"), NO_RECORD, NO_RECORD)
bad_signature = parse(signature_document("lock", D43, SIGN1, PK1))["signature"]
verify("verify-lock-signature-invalid", "§11", "The expected key and this lock's digest, with a signature over "
       "another lock's message: LOCK-SIG-INVALID. reading: located at /signature.",
       {"floor": 1, "lockSignatures": [put("vectors/verify-lock-signature-invalid/lock.sig.json", (jcs({
           "algorithm": "ed25519", "lockDigest": D42, "lockSignatureVersion": "1.1.0", "publicKey": PK1,
           "signature": bad_signature}) + "\n").encode("ascii"))]},
       refusal("LOCK-SIG-INVALID", "signature", "/signature"), NO_RECORD, NO_RECORD)

GOOD_SIG42 = parse(FILES[SIG42])


def signature_variant(identity, document_text: str) -> str:
    return put(f"vectors/{identity}/lock.sig.json", document_text.encode("utf-8"))


def members(**changes) -> dict:
    document = dict(GOOD_SIG42)
    for name, value in changes.items():
        if value is None:
            del document[name]
        else:
            document[name] = value
    return document


DOCUMENT_ROWS = [
    ("verify-signature-backslash", "A backslash anywhere in the document, here an escape that spells ed25519: "
     "LOCK-SIG-DOCUMENT. reading: located at the document's root.",
     jcs(GOOD_SIG42).replace('"ed25519"', '"ed2551\\u0039"') + "\n", "LOCK-SIG-DOCUMENT", "", False),
    ("verify-signature-over-bound", "A document of more than 4096 bytes, its members spread by white space, which is "
     "otherwise admitted when read: LOCK-SIG-DOCUMENT. reading: located at the document's root.",
     "{" + ",\n".join(" " * 800 + json.dumps(k) + ":" + json.dumps(v) for k, v in GOOD_SIG42.items()) + "}\n",
     "LOCK-SIG-DOCUMENT", "", False),
    ("verify-signature-version", "A lockSignatureVersion of 1.2.0, a later version named as such: LOCK-SIG-VERSION. "
     "reading: located at the member.", jcs(members(lockSignatureVersion="1.2.0")) + "\n", "LOCK-SIG-VERSION",
     "/lockSignatureVersion", True),
    ("verify-signature-member", "A member that is not defined: LOCK-SIG-MEMBER. reading: located at the member.",
     jcs(members(keyId=hashlib.sha256(bytes.fromhex(PK1)).hexdigest()[:32])) + "\n", "LOCK-SIG-MEMBER", "/keyId",
     True),
    ("verify-signature-member-missing", "A document without its signature member: LOCK-SIG-MEMBER. reading: located "
     "at the pointer the member would have.", jcs(members(signature=None)) + "\n", "LOCK-SIG-MEMBER", "/signature",
     True),
    ("verify-signature-algorithm", "An algorithm other than ed25519: LOCK-SIG-ALGORITHM. reading: located at the "
     "member.", jcs(members(algorithm="ed448")) + "\n", "LOCK-SIG-ALGORITHM", "/algorithm", True),
    ("verify-signature-key-uppercase", "A publicKey in uppercase hexadecimal, another spelling of one key: "
     "LOCK-SIG-PUBLIC-KEY. reading: located at the member.", jcs(members(publicKey=PK1.upper())) + "\n",
     "LOCK-SIG-PUBLIC-KEY", "/publicKey", True),
    ("verify-signature-key-small-order", "A document whose publicKey is of small order, which the trust rule refuses: "
     "LOCK-SIG-PUBLIC-KEY, before the key is compared. reading: located at the member.",
     jcs(members(publicKey=SMALL_ORDER_KEY)) + "\n", "LOCK-SIG-PUBLIC-KEY", "/publicKey", False),
    ("verify-signature-form", "A signature of 126 hexadecimal characters: LOCK-SIG-FORM. reading: located at the "
     "member.", jcs(members(signature=GOOD_SIG42["signature"][:126])) + "\n", "LOCK-SIG-FORM", "/signature", True),
]
for identity, what, text, code, pointer, refused_by_schema in DOCUMENT_ROWS:
    path = signature_variant(identity, text)
    verify(identity, "§§10.1, 11", what + " reading: a document refused when read is not then checked against a "
           "key.", {"floor": 1, "lockSignatures": [path]},
           refusal(code, "signature", pointer), NO_RECORD, NO_RECORD, schema_refuses=[path] if refused_by_schema else ())

# The lock (step 3), the serial (step 4) and the index (step 5).
verify("verify-unexpected-registry", "§11", "Another registry's lock signed by the expected key verifies as a "
       "signature and is refused for its registry id: LOCK-UNEXPECTED-REGISTRY. reading: located at /registry/id.",
       {"floor": 1, "expect": {"registryId": BILLING_REGISTRY_ID, "requireIndex": False}},
       refusal("LOCK-UNEXPECTED-REGISTRY", pointer="/registry/id"), NO_RECORD, NO_RECORD)
verify("verify-index-required", "§11", "A verifier that holds a map requires an index: a single registry's lock "
       "signed by the standard owner's key is LOCK-INDEX-REQUIRED, never a lock that needs no repository's signature. "
       "reading: located at /index.",
       {"floor": 1, "signers": ASSEMBLED_SIGNERS, "expect": {"registryId": SINGLE_ID, "requireIndex": True}},
       refusal("LOCK-INDEX-REQUIRED", pointer="/index"), NO_RECORD, NO_RECORD)
no_index_verify = dict(ASSEMBLED_VERIFY)
del no_index_verify["index"]
verify("verify-index-missing", "§11", "An assembled lock verified without its index, whatever else is given: "
       "LOCK-INDEX-MISSING. reading: located at /index, and no source signature is checked without the index the "
       "statements are rebuilt from.", no_index_verify, refusal("LOCK-INDEX-MISSING", pointer="/index"),
       NO_RECORD, NO_RECORD)
verify("verify-index-digest-mismatch", "§11", "An index whose digest is not the lock's index digest, its registry "
       "digest and items the lock's, so that every source signature is accepted: step 5 holds the index to step 6 "
       "of section 9, LOCK-INDEX-MISMATCH. reading: located at the lock's /index, as LOCK-REGISTRY-MISMATCH is at "
       "the lock's /registry.", dict(ASSEMBLED_VERIFY, index=IDX_OTHER),
       refusal("LOCK-INDEX-MISMATCH", pointer="/index"), NO_RECORD, NO_RECORD)
verify("verify-index-registry-mismatch", "§11", "An index the signed lock names by digest whose registry digest is "
       "another registry's, its items the lock's, so that every source signature is accepted: step 5 holds the "
       "index to step 6 of section 9, LOCK-INDEX-MISMATCH. reading: located at the index's /registry/digest.",
       dict(ASSEMBLED_VERIFY, lock=L_OTHER_REGISTRY, lockSignatures=[L_OTHER_REGISTRY + ".sig.json"],
            index=IDX_OTHER_REGISTRY),
       refusal("LOCK-INDEX-MISMATCH", "index", "/registry/digest"), NO_RECORD, NO_RECORD)

# The source signatures (step 6).
verify("verify-source-signature-missing", "§11", "No source signature for the repository's item: LOCK-SIG-MISSING "
       "at the item. reading: located at the lock's item.", dict(ASSEMBLED_VERIFY, sourceSignatures=[SIG_STANDARD]),
       refusal("LOCK-SIG-MISSING", pointer="/sources/0"), NO_RECORD, NO_RECORD)
verify("verify-source-signature-twice", "§11", "The repository's source signature given twice: LOCK-SIG-EXTRA. "
       "reading: located at the signature document's root.",
       dict(ASSEMBLED_VERIFY, sourceSignatures=[SIG_BILLING, SIG_STANDARD, SIG_BILLING]),
       refusal("LOCK-SIG-EXTRA", "signature"), NO_RECORD, NO_RECORD)
verify("verify-source-signature-duplicate-within-cap", "§11", "The repository's source signature given twice and "
       "the standard's not at all: three documents with the lock signature, within the lock's sources count plus "
       "one, so each is read. The second copy for one item is LOCK-SIG-EXTRA, and the standard item that no "
       "document matches is LOCK-SIG-MISSING: the set is refused, not trimmed. reading: LOCK-SIG-EXTRA is located "
       "at the signature document's root, LOCK-SIG-MISSING at the lock's item.",
       dict(ASSEMBLED_VERIFY, sourceSignatures=[SIG_BILLING, SIG_BILLING]),
       report(False, [diag("LOCK-SIG-MISSING", "lock", "/sources/1"), diag("LOCK-SIG-EXTRA", "signature", "")]),
       NO_RECORD, NO_RECORD)
CAP_UNREAD = put("vectors/verify-signature-cap-unread/extra-signature.txt",
                 FILES[SIG_STANDARD][:-2] + b"\\}\n")
assert b"\\" in FILES[CAP_UNREAD]
verify("verify-signature-cap-unread", "§11", "Four documents for a lock of two sources: the lock signature, one "
       "source signature for each item, and last a document that holds a backslash and is not JSON. The one beyond "
       "the lock's sources count plus one is LOCK-SIG-EXTRA before any is read, so it is never read and no "
       "LOCK-SIG-DOCUMENT is reported, and the other three are accepted. reading: the document beyond the count is "
       "the last given, the lock signature counted first; LOCK-SIG-EXTRA is located at the signature document's "
       "root.",
       dict(ASSEMBLED_VERIFY, sourceSignatures=[SIG_BILLING, SIG_STANDARD, CAP_UNREAD]),
       refusal("LOCK-SIG-EXTRA", "signature"), NO_RECORD, NO_RECORD)
verify("verify-source-signature-stray", "§11", "A source signature given for a lock with no sources: LOCK-SIG-EXTRA. "
       "reading: located at the signature document's root.", {"floor": 1, "sourceSignatures": [SIG_BILLING]},
       refusal("LOCK-SIG-EXTRA", "signature"), NO_RECORD, NO_RECORD)
verify("verify-map-misses-repository", "§11", "The map names another repository and not the lock's: LOCK-EXPECTED, "
       "found once the lock is read. reading: located at the lock's item.",
       dict(ASSEMBLED_VERIFY, signers={"key": PK1, "repositories": {LEDGER_REPO: PK3}}),
       refusal("LOCK-EXPECTED", pointer="/sources/0"), NO_RECORD, NO_RECORD)
verify("verify-map-names-standard-repository", "§11", "The map names the standard item's repository: LOCK-EXPECTED, "
       "since a repository's identity there would let its statement pass without its own key. reading: located at "
       "the lock's item.",
       dict(ASSEMBLED_VERIFY, signers={"key": PK1, "repositories": {BILLING_REPO: PK2, PLATFORM_REPO: PK3}}),
       refusal("LOCK-EXPECTED", pointer="/sources/1"), NO_RECORD, NO_RECORD)
verify("verify-source-wrong-key", "§11", "The repository's statement signed by another key than the map names, in a "
       "lock that names that signature: LOCK-SIG-UNEXPECTED-KEY. reading: located at /publicKey.",
       dict(ASSEMBLED_VERIFY, lock=LA_T3, lockSignatures=[LA_T3 + ".sig.json"],
            sourceSignatures=[SIG_BILLING_T3, SIG_STANDARD]),
       refusal("LOCK-SIG-UNEXPECTED-KEY", "signature", "/publicKey"), NO_RECORD, NO_RECORD)
verify("verify-source-another-commit", "§11", "The repository's signature over its statement at another commit than "
       "the index records: the statement rebuilt from the index is not what it names, LOCK-SIG-DIGEST-MISMATCH. "
       "reading: located at /sourceDigest.",
       dict(ASSEMBLED_VERIFY, lock=LA_OC, lockSignatures=[LA_OC + ".sig.json"],
            sourceSignatures=[SIG_BILLING_OC, SIG_STANDARD]),
       refusal("LOCK-SIG-DIGEST-MISMATCH", "signature", "/sourceDigest"), NO_RECORD, NO_RECORD)
verify("verify-statement-another-commit", "§11", "A lock, signed by the standard owner, whose statement digest for "
       "the repository is the one its signature at another commit names, so that the lock's statement member and "
       "the signature agree: step 5 holds the index to step 7 of section 9, LOCK-SOURCES-MISMATCH at the item, and "
       "step 6 checks the signature against the statement rebuilt from the index's item, never against the lock's "
       "statement member alone, LOCK-SIG-DIGEST-MISMATCH. reading: step 6 runs after step 5's mismatch, since the "
       "report gives every signature's result and section 9 ends a check only at its steps 1 and 2; "
       "LOCK-SIG-DIGEST-MISMATCH is located at /sourceDigest.",
       dict(ASSEMBLED_VERIFY, lock=LA_SO, lockSignatures=[LA_SO + ".sig.json"],
            sourceSignatures=[SIG_BILLING_OC, SIG_STANDARD]),
       report(False, [diag("LOCK-SOURCES-MISMATCH", "lock", "/sources/0"),
                      diag("LOCK-SIG-DIGEST-MISMATCH", "signature", "/sourceDigest")]), NO_RECORD, NO_RECORD)
verify("verify-standard-signed-by-repository-key", "§11", "The standard source's statement signed by the "
       "repository's key, a key of the set but not the one it names for the standard item, in a lock that names "
       "that signature: LOCK-SIG-UNEXPECTED-KEY. reading: located at /publicKey.",
       dict(ASSEMBLED_VERIFY, lock=LA_SR, lockSignatures=[LA_SR + ".sig.json"],
            sourceSignatures=[SIG_BILLING, SIG_STANDARD_T2]),
       refusal("LOCK-SIG-UNEXPECTED-KEY", "signature", "/publicKey"), NO_RECORD, NO_RECORD)

# ---------------------------------------------------------------------------------------------------


def main() -> None:
    for path in BASE.iterdir():
        if path.name in KEEP:
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    for relative, data in FILES.items():
        target = BASE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    rows = {"companion": "registry", "formatVersion": "1.1.0", "status": "proposed",
            "label": "Registry companion 1.1.0, proposed: hand-written synthetic vectors, staged in no corpus",
            "codes": "codes.json", "vectors": ROWS}
    (BASE / "manifest.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(ROWS)} rows, {len(FILES)} files")


if __name__ == "__main__":
    main()

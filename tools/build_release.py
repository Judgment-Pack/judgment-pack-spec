#!/usr/bin/env python3
"""Validate and build immutable JPS release bundles from a tagged commit."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*)?$"
)
BUNDLE_PATHS = (
    "README.md",
    "LICENSE",
    "NOTICE",
    "CHANGELOG.md",
    "VERSIONING.md",
    "TESTING.md",
    "SECURITY.md",
    "spec",
    "schema",
    "examples",
    "conformance",
)

# Explicit reviewed distribution identities; no generic prerelease normalization.
CORE_RC_TAG = "v0.3.0-rc.1"
CORE_RC_IDENTITY = {
    "releaseVersion": "0.3.0-rc.1",
    "tag": CORE_RC_TAG,
    "specVersion": "0.3.0",
    "maturity": "draft",
    "distribution": "release-candidate",
}

# Explicit planned RC2 distribution; published RC1 mapping stays exact and immutable.
CORE_RC2_TAG = "v0.3.0-rc.2"
CORE_RC2_IDENTITY = {"releaseVersion": "0.3.0-rc.2", "tag": CORE_RC2_TAG,
                     "specVersion": "0.3.0", "maturity": "draft", "distribution": "release-candidate"}
CORE_RC_IDENTITIES = {CORE_RC_TAG: CORE_RC_IDENTITY, CORE_RC2_TAG: CORE_RC2_IDENTITY}
RETAINED_INVENTORY = "releases/v0.3.0-rc.2.retained-column.json"
RETAINED_BUNDLE_PATHS = ("tools/dialect_verify.py", "tools/retained_column.py",
                         "tools/_retained_column.py", "tools/check_retained_column.py",
                         "tools/dialect-verify-ts", "requirements-dev.txt")

# The final is the leaf's normative support distribution. It carries RC2's schema, corpus and
# every other leaf byte unchanged under its own inventory; only the companion page, the Core and
# Dialect pages (their sentences on the leaf's adoption) and the two readers' installation
# identity may differ from RC2's. It has no
# distribution mapping (VERSIONING.md allowlists the two RCs' and v0.4.0's only); its bundles carry a
# generated release-identity.json, never a tracked mapping, so readers can check sourceCommit.
CORE_FINAL_TAG = "v0.3.0"
CORE_FINAL_IDENTITY = {"releaseVersion": "0.3.0", "tag": CORE_FINAL_TAG, "specVersion": "0.3.0",
                       "maturity": "draft"}

# A release that carries the released specVersion 0.3.0 unchanged. Core is not re-pinned, so its tag
# is a distribution identity and not a pack selector (VERSIONING.md). The mapping is exact and this
# tag alone may use it: it is the release numbering rule's recorded exception, since under that rule
# the tag would have been v0.3.1.
CORE_CARRIED_TAG = "v0.4.0"
CORE_UNCHANGED_DISTRIBUTION = "specification-unchanged"
CORE_CARRIED_IDENTITY = {"releaseVersion": "0.4.0", "tag": CORE_CARRIED_TAG, "specVersion": "0.3.0",
                         "maturity": "draft", "distribution": CORE_UNCHANGED_DISTRIBUTION}
CORE_MAPPED_IDENTITIES = {**CORE_RC_IDENTITIES, CORE_CARRIED_TAG: CORE_CARRIED_IDENTITY}
# The record-shape catalog joins the bundles of the releases that carry a released specVersion
# unchanged: this tag and every patch tag. Tags before v0.4.0 have no such directory, and
# `git archive` refuses a path their tree lacks.
CORE_CARRIED_BUNDLE_PATHS = ("catalog",)
GENERATED_IDENTITIES = {**CORE_MAPPED_IDENTITIES, CORE_FINAL_TAG: CORE_FINAL_IDENTITY}

# The release numbering rule (VERSIONING.md, "Release numbers and specVersion"): a plain tag vX.Y.Z
# carries specVersion X.Y.0, and a patch tag (Z > 0) carries that released specVersion unchanged. A
# prerelease suffix is never stripped: an unmapped prerelease tag carries its own complete version,
# which no Core artifact names, so the pins refuse it.
PLAIN_VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
SCHEMA_NAMESPACE = "https://judgmentpack.org/schema/"
# A patch release's normative artifacts are byte-identical to those of the X.Y.0 release. Each entry
# names the record of that release's normative bytes and the SHA-256 of the record itself, so the
# record cannot change without a reviewed change here. releases/v0.5.0.normative.json was derived
# from the blobs of tag v0.5.0 (commit 171d4c21d4b13e03ee20e1adb6fc5cc6b182cfae) with `git show`,
# over the paths normative_paths() gives for that tree; it agrees with `git archive` of the tag and
# with the four schema digests releases/v0.5.0.md publishes. A specVersion with no entry has no
# patch release: 0.4.0 was never released, and the rule is normative from v0.5.0 on.
NORMATIVE_RECORDS = {
    "0.5.0": ("releases/v0.5.0.normative.json",
              "86e175e8786eb6e08a215178ba7099edb074193c83c5ee2dc6a12012555b4aaa"),
}
FINAL_RETAINED_INVENTORY = "releases/v0.3.0.retained-column.json"
RETAINED_INVENTORIES = {CORE_RC2_TAG: RETAINED_INVENTORY, CORE_FINAL_TAG: FINAL_RETAINED_INVENTORY}
FINAL_REVISED_LEAF_FILES = frozenset({"spec/retained-column.md", "spec/judgment-pack-core.md",
                                      "spec/dialect.md", "tools/retained_column.py",
                                      "tools/dialect-verify-ts/src/retained.ts"})
# The SHA-256 of releases/v0.3.0-rc.2.retained-column.json as tag v0.3.0-rc.2 published it, so the
# final is held to RC2's published inventory, not to a working copy edited after publication.
RC2_RETAINED_INVENTORY_SHA256 = "b4d62b3259b24dee68d926750ab45247d974004eec2bd15814f7d24c89140160"
CORE_MILESTONE = {"number": 2, "title": "v0.3.0"}


def validate_retained_inventory(root: Path = ROOT, tag: str = CORE_RC2_TAG) -> None:
    inventory = root / RETAINED_INVENTORIES[tag]
    if not inventory.is_file():
        raise ValueError("retained-column inventory is missing for the exact tag")
    release = json.loads(inventory.read_text("utf-8"))
    if set(release) != {"contract", "distribution", "maturity", "schema", "schemaSha256",
                        "corpus", "corpusSha256", "files", "claim"}:
        raise ValueError("retained-column inventory has an invalid closed shape")
    if (release["contract"] != "retained-column/1" or release["distribution"] != tag
            or release["maturity"] != "draft" or release["claim"] != "selected-leaf-support"):
        raise ValueError("retained-column inventory identity or scope differs")
    schema = "schema/retained-column/1/contract.schema.json"
    corpus = "conformance/retained-column/1/cases.json"
    if release["schema"] != schema or release["corpus"] != corpus:
        raise ValueError("retained-column artifact paths differ")
    expected = {schema, "spec/retained-column.md", "spec/dialect.md", "spec/judgment-pack-core.md",
                "tools/dialect_verify.py", "tools/retained_column.py", "tools/_retained_column.py",
                "tools/check_retained_column.py"}
    for directory in ("conformance/retained-column/1", "tools/dialect-verify-ts/src"):
        expected.update(p.relative_to(root).as_posix() for p in (root / directory).rglob("*") if p.is_file())
    if set(release["files"]) != expected:
        raise ValueError("retained-column complete artifact inventory differs")
    if any(value != "sha256:" + sha256(root / path) for path, value in release["files"].items()):
        raise ValueError("retained-column immutable artifact bytes differ")
    if (release["schemaSha256"] != release["files"][schema]
            or release["corpusSha256"] != release["files"][corpus]):
        raise ValueError("retained-column schema or corpus pin differs")
    resource = json.loads((root / schema).read_text("utf-8"))
    if resource.get("$id") != "https://judgmentpack.org/schema/retained-column/1/contract.schema.json":
        raise ValueError("retained-column immutable schema identity differs")
    cases = json.loads((root / corpus).read_text("utf-8"))
    corpus_inputs = {"conformance/retained-column/1/" + name for name in
                     ("examples.json", "preparations.json", "capabilities.json", "manifest.json")}
    if set(cases["inputs"]) != corpus_inputs:
        raise ValueError("retained-column complete corpus input set differs")
    for path, value in cases["inputs"].items():
        if path not in expected or value != release["files"][path]:
            raise ValueError("retained-column corpus companion input differs")


def validate_final_retained_inventory(root: Path = ROOT) -> None:
    """Hold the final's inventory to the bytes RC2 published.

    The schema, corpus and every other pinned file keep RC2's digests; only the distribution and
    the files that name the final's support identity may differ.
    """
    validate_retained_inventory(root, CORE_FINAL_TAG)
    final = json.loads((root / FINAL_RETAINED_INVENTORY).read_text("utf-8"))
    published_path = root / RETAINED_INVENTORY
    if not published_path.is_file():
        raise ValueError("the published RC2 retained-column inventory is missing")
    if sha256(published_path) != RC2_RETAINED_INVENTORY_SHA256:
        raise ValueError("the RC2 retained-column inventory differs from the bytes RC2 published")
    published = json.loads(published_path.read_text("utf-8"))
    if (not isinstance(published, dict) or not isinstance(published.get("files"), dict)
            or {**final, "distribution": CORE_RC2_TAG, "files": None} != {**published, "files": None}
            or set(final["files"]) != set(published["files"])
            or any(digest != published["files"][path] for path, digest in final["files"].items()
                   if path not in FINAL_REVISED_LEAF_FILES)):
        raise ValueError("final retained-column inventory differs from the published RC2 inventory")


def validate_reader_support_identity(tag: str, root: Path = ROOT) -> None:
    """Both readers must name this exact distribution, its version and its inventory."""
    expected = (tag, release_version(tag), RETAINED_INVENTORIES[tag])
    module = ast.parse((root / "tools/retained_column.py").read_text("utf-8"))
    constants = {target.id: node.value.value for node in module.body if isinstance(node, ast.Assign)
                 for target in node.targets if isinstance(target, ast.Name)
                 and isinstance(node.value, ast.Constant)}
    typescript = re.search(r'^const TAG = "([^"]*)", VERSION = "([^"]*)", INVENTORY = "([^"]*)";$',
                           (root / "tools/dialect-verify-ts/src/retained.ts").read_text("utf-8"),
                           re.MULTILINE)
    if (tuple(constants.get(name) for name in ("TAG", "VERSION", "INVENTORY")) != expected
            or typescript is None or typescript.groups() != expected):
        raise ValueError("retained-column readers do not name the exact release distribution")


POLICY_FORMAT = "1.0.0"
POLICY_ROOT = "conformance/policy/1.0.0"
POLICY_SCHEMA_ROOT = "schema/policy/1.0.0"
POLICY_TAG_PATTERN = re.compile(
    r"policy-v((?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"-draft\.(?:0|[1-9][0-9]*))"
)
POLICY_FORMAT_PATHS = (
    "spec/policy.md",
    *tuple(f"{POLICY_SCHEMA_ROOT}/{name}.schema.json"
           for name in ("common", "policy", "governing-adoption")),
    f"{POLICY_SCHEMA_ROOT}/consumer-core-0.2.0-draft.schema.json",
    f"{POLICY_ROOT}/fixture.schema.json",
    f"{POLICY_ROOT}/vectors.schema.json",
    f"{POLICY_ROOT}/vectors/README.md",
)
POLICY_BUNDLE_PATHS = (
    "LICENSE", "NOTICE", "VERSIONING.md", "GOVERNANCE.md", "CONTRIBUTING.md",
    "requirements-dev.txt", "spec/policy.md", "spec/dialect.md",
    "spec/checkpoint-witness.md", POLICY_SCHEMA_ROOT, POLICY_ROOT,
    "schema/judgment-pack-core.schema.json", "tools/dialect_verify.py",
    "tools/retained_column.py", "tools/_retained_column.py",
    "rfcs/0000-rfc-process.md", "rfcs/0023-policy-companion.md",
    "rfcs/policy-companion-prototype", "rfcs/policy-companion-contract",
)


def is_policy_tag(tag: str) -> bool:
    return POLICY_TAG_PATTERN.fullmatch(tag) is not None


# The registry companion's route is the Policy route without its draft-only restriction
# (VERSIONING.md, "Independently versioned registry companion"): a plain three-component tag, a
# release at maturity `released`, which is not stable. Its record names the rows and the code list
# with their digests; every file under the format's schema and row directories is pinned, derived
# from the tree rather than listed here.
REGISTRY_FORMAT = "1.0.0"
REGISTRY_MATURITY = "released"
REGISTRY_ROOT = f"conformance/registry/{REGISTRY_FORMAT}"
REGISTRY_SCHEMA_ROOT = f"schema/registry/{REGISTRY_FORMAT}"
REGISTRY_TEXT = "spec/registry.md"
REGISTRY_README = "conformance/registry/README.md"
REGISTRY_SCHEMA_NAMESPACE = f"{SCHEMA_NAMESPACE}registry/{REGISTRY_FORMAT}/"
REGISTRY_TAG_PATTERN = re.compile(
    r"registry-v((?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))"
)
# The text says its status in this one sentence; the code list and the rows' manifest say it in
# their `status` member. All three say `proposed` until the commit a registry tag names.
REGISTRY_STATUS_SENTENCE = re.compile(
    rf"^This text is registry format `{re.escape(REGISTRY_FORMAT)}`, status `([a-z]+)`\.",
    re.MULTILINE,
)
# What the companion's files say of it while the format is proposed: a schema's titles,
# descriptions and comments, the rows' README heading and the rows' manifest label. A JSON Schema
# draft's name ("draft 2020-12") is not a draft.
REGISTRY_UNRELEASED_WORDING = re.compile(
    r"\b(?:draft(?![- ]?[0-9])|staged|proposed|unreleased|not(?: yet)? released|pre-?release"
    r"|no bundle|no site|no corpus)\b",
    re.IGNORECASE,
)
# The text's and the README's statements of the format's status, read with whitespace collapsed:
# "status `proposed`" and "Version `1.0.0` is proposed".
REGISTRY_PROPOSED_STATEMENT = re.compile(
    rf"`{re.escape(REGISTRY_FORMAT)}`(?:, status `proposed`| is proposed)", re.IGNORECASE
)
REGISTRY_RECORD_KEYS = {"companion", "releaseVersion", "tag", "maturity", "formatVersion", "schemas",
                        "codes", "corpus", "formatDigests"}
# The text, what it and the rows' README link to, the checks that hold the rows to the text, and
# the license. Core's corpora and Policy's are not carried.
REGISTRY_BUNDLE_PATHS = (
    "LICENSE", "NOTICE", "VERSIONING.md", "requirements-dev.txt",
    REGISTRY_TEXT, "spec/dialect.md", REGISTRY_SCHEMA_ROOT, REGISTRY_README, REGISTRY_ROOT,
    "tests/test_registry_companion.py", "tests/test_registry_schemas.py",
    "rfcs/0034-registry-profile.md", "rfcs/0035-registry-references.md",
    "rfcs/0036-registry-emitter-contract.md", "rfcs/0037-generated-facts-contracts.md",
    "rfcs/0038-terraform-file-source.md",
)


def is_registry_tag(tag: str) -> bool:
    return REGISTRY_TAG_PATTERN.fullmatch(tag) is not None


def tree_digests(directory: str, root: Path = ROOT) -> dict[str, str]:
    """The SHA-256 of every file under a directory of the tree, by its path."""
    paths = sorted(path for path in (root / directory).rglob("*") if path.is_file())
    return {path.relative_to(root).as_posix(): "sha256:" + sha256(path) for path in paths}


def registry_record(version: str, tag: str, root: Path = ROOT) -> dict:
    """The release record the tree gives a registry tag; its record must equal it."""
    schemas = {}
    for path in sorted((root / REGISTRY_SCHEMA_ROOT).glob("*.schema.json")):
        identity = REGISTRY_SCHEMA_NAMESPACE + path.name
        if json.loads(path.read_text("utf-8")).get("$id") != identity:
            raise ValueError("registry schema $id differs from its immutable format identity")
        schemas[path.name[:-len(".schema.json")]] = identity
    if not schemas:
        raise ValueError("registry release has no schema")
    digests = tree_digests(REGISTRY_SCHEMA_ROOT, root)
    for path in (REGISTRY_TEXT, REGISTRY_README):
        digests[path] = "sha256:" + sha256(root / path)
    rows_path, codes_path = f"{REGISTRY_ROOT}/manifest.json", f"{REGISTRY_ROOT}/codes.json"
    rows = json.loads((root / rows_path).read_text("utf-8"))
    codes = json.loads((root / codes_path).read_text("utf-8"))
    vectors = rows.get("vectors") if isinstance(rows, dict) else None
    listed = codes.get("codes") if isinstance(codes, dict) else None
    if (not isinstance(vectors, list) or not vectors or not all(isinstance(row, dict) for row in vectors)
            or len({row.get("id") for row in vectors}) != len(vectors)):
        raise ValueError("registry rows' manifest has no rows, or two rows share an id")
    if not isinstance(listed, list) or not listed:
        raise ValueError("registry code list has no codes")
    return {"companion": "registry", "releaseVersion": version, "tag": tag,
            "maturity": REGISTRY_MATURITY, "formatVersion": REGISTRY_FORMAT, "schemas": schemas,
            "codes": {"path": codes_path, "sha256": "sha256:" + sha256(root / codes_path),
                      "codes": len(listed)},
            "corpus": {"path": rows_path, "sha256": "sha256:" + sha256(root / rows_path),
                       "rows": len(vectors), "files": tree_digests(REGISTRY_ROOT, root)},
            "formatDigests": digests}


def validate_registry_artifacts(version: str, tag: str, root: Path = ROOT) -> None:
    """Gate the independently versioned registry companion on its own release record."""
    record_path = root / "releases" / f"{tag}.json"
    if not record_path.is_file():
        raise ValueError("registry release record is missing for the exact tag")
    release = json.loads(record_path.read_text("utf-8"))
    if not isinstance(release, dict) or set(release) != REGISTRY_RECORD_KEYS:
        raise ValueError("registry release record has an invalid closed shape")
    expected = registry_record(version, tag, root)
    for keys, message in (
            (("companion", "releaseVersion", "tag", "maturity", "formatVersion"),
             "registry release identity, maturity or format does not match"),
            (("schemas",), "registry release schema identities do not match the exact format"),
            (("formatDigests",), "registry format bytes differ from the release record"),
            (("corpus",), "registry corpus identity or count does not match"),
            (("codes",), "registry code list identity or count does not match")):
        if any(release[key] != expected[key] for key in keys):
            raise ValueError(message)
    for previous_path in (root / "releases").glob("registry-v*.json"):
        if previous_path == record_path or previous_path.name.endswith(".milestone.json"):
            continue
        if not same_registry_schemas(json.loads(previous_path.read_text("utf-8")), release):
            raise ValueError("registry exact format identity conflicts with an earlier release record")
    rows = json.loads((root / release["corpus"]["path"]).read_text("utf-8"))
    codes = json.loads((root / release["codes"]["path"]).read_text("utf-8"))
    text = REGISTRY_STATUS_SENTENCE.findall((root / REGISTRY_TEXT).read_text("utf-8"))
    if text != [REGISTRY_MATURITY] or any(
            (document.get("companion"), document.get("formatVersion"), document.get("status"))
            != ("registry", REGISTRY_FORMAT, REGISTRY_MATURITY) for document in (rows, codes)):
        raise ValueError("a registry release requires the text, the code list and the rows' "
                         f"manifest to say status {REGISTRY_MATURITY}")
    readme = (root / REGISTRY_README).read_text("utf-8")
    label = rows.get("label", "")
    if (any(REGISTRY_PROPOSED_STATEMENT.search(" ".join(document.split()))
            for document in ((root / REGISTRY_TEXT).read_text("utf-8"), readme))
            or any(REGISTRY_UNRELEASED_WORDING.search(heading)
                   for heading in re.findall(r"^# .*$", readme, re.MULTILINE))
            or not isinstance(label, str) or REGISTRY_UNRELEASED_WORDING.search(label)):
        raise ValueError("a registry release requires the text and the rows' README not to call "
                         "the format proposed, nor the README's heading or the manifest's label")
    # A schema's bytes are served at its $id from the release on and never change, so none may
    # still call itself a draft, or unreleased, when the release publishes it: not in its own title
    # and description, which it must have, nor in any nested one or any comment.
    for name in release["schemas"]:
        schema = json.loads((root / REGISTRY_SCHEMA_ROOT / f"{name}.schema.json").read_text("utf-8"))
        if (not isinstance(schema, dict) or not isinstance(schema.get("title"), str)
                or not isinstance(schema.get("description"), str)
                or any(REGISTRY_UNRELEASED_WORDING.search(said) for said in schema_annotations(schema))):
            raise ValueError("a registry release requires each schema's titles, descriptions and "
                             "comments to drop the draft and unreleased wording")
    if not (root / "releases" / f"{tag}.md").is_file():
        raise ValueError("registry release notes are missing for the exact tag")


def schema_annotations(value: object):
    """Every string a schema gives as a `title`, `description` or `$comment`, at any depth. A
    property of one of those names maps to a schema, not a string, and is walked into."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ("title", "description", "$comment") and isinstance(item, str):
                yield item
            else:
                yield from schema_annotations(item)
    elif isinstance(value, list):
        for item in value:
            yield from schema_annotations(item)


def same_registry_schemas(previous: object, release: dict) -> bool:
    """A schema published at its $id never changes: an earlier record of the same format must
    name the same schema identities and the same schema bytes. A record that is not of this form
    conflicts."""
    if not isinstance(previous, dict) or not isinstance(previous.get("formatDigests"), dict):
        return False
    if previous.get("formatVersion") != release["formatVersion"]:
        return True

    def pinned(record: dict) -> dict:
        return {path: digest for path, digest in record["formatDigests"].items()
                if path.startswith(REGISTRY_SCHEMA_ROOT + "/")}

    return previous.get("schemas") == release["schemas"] and pinned(previous) == pinned(release)


def validate_registry_history(tag: str) -> None:
    """Compare immutable tagged records, so editing old working files cannot repoint a schema."""
    release = json.loads((ROOT / "releases" / f"{tag}.json").read_text("utf-8"))
    for previous in git("tag", "--list", "registry-v*").splitlines():
        if previous == tag or not is_registry_tag(previous):
            continue
        old = json.loads(git("show", f"refs/tags/{previous}:releases/{previous}.json"))
        if not same_registry_schemas(old, release):
            raise ValueError("registry exact format conflicts with immutable tagged release history")


# The terraform-file companion's route is the registry's (VERSIONING.md, "Independently versioned
# terraform-file companion"): a plain three-component tag, a release at maturity `released`, which
# is not stable, and a record that names the code list, the format table and the vectors with their
# digests. The companion has no schema, so nothing of it is served at an `$id`. A tag's number is
# the release of the format table it carries (spec/terraform-file.md section 4), and the builder
# holds the two to one number. Every file under the reading's directory is pinned, derived from the
# tree rather than listed here. The reading's first table release is 1.0.0 and each later one is the
# next patch of the latest earlier one, whether it accepts new rows or, as an erratum, none; the
# record's `added` names the rows it accepts. The text defines no minor or major release of the
# table, so this route has none.
TERRAFORM_FILE_READING = "1.0.0"
TERRAFORM_FILE_FIRST_TABLE = (1, 0, 0)
TERRAFORM_FILE_MATURITY = "released"
TERRAFORM_FILE_ROOT = f"conformance/terraform-file/{TERRAFORM_FILE_READING}"
TERRAFORM_FILE_TEXT = "spec/terraform-file.md"
TERRAFORM_FILE_README = "conformance/terraform-file/README.md"
TERRAFORM_FILE_TAG_PATTERN = re.compile(
    r"terraform-file-v((?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))"
)
# The text says its status in this one sentence; the code list, the format table and the vectors'
# manifest say it in their `status` member. All four say `proposed` until the commit a
# terraform-file tag names.
TERRAFORM_FILE_STATUS_SENTENCE = re.compile(
    rf"^This text is the terraform-file reading `{re.escape(TERRAFORM_FILE_READING)}`, "
    r"status `([a-z]+)`\.",
    re.MULTILINE,
)
# The text's and the README's statements of the reading's status, read with whitespace collapsed:
# "status `proposed`" and "Version `1.0.0` is proposed".
TERRAFORM_FILE_PROPOSED_STATEMENT = re.compile(
    rf"`{re.escape(TERRAFORM_FILE_READING)}`(?:, status `proposed`| is proposed)", re.IGNORECASE
)
TERRAFORM_FILE_RECORD_KEYS = {"companion", "releaseVersion", "tag", "maturity", "reading",
                              "formatTable", "codes", "corpus", "formatDigests"}
# The text, what it and the vectors' README link to, the checks that hold the vectors to the text,
# and the license. The checks that read each declaration with the dialect's first reader need the
# dialect's staged vectors, which no bundle carries, and stay in the repository
# (tests/test_terraform_file_declarations.py).
TERRAFORM_FILE_BUNDLE_PATHS = (
    "LICENSE", "NOTICE", "VERSIONING.md",
    TERRAFORM_FILE_TEXT, "spec/dialect.md", "spec/registry.md", TERRAFORM_FILE_README,
    TERRAFORM_FILE_ROOT, "tests/test_terraform_file_vectors.py",
    "rfcs/0018-dialect.md", "rfcs/0038-terraform-file-source.md",
)
# Independently versioned companions whose schema and row directories no Core bundle carries.
INDEPENDENT_DIRECTORIES = ("policy", "registry", "terraform-file")


def is_terraform_file_tag(tag: str) -> bool:
    return TERRAFORM_FILE_TAG_PATTERN.fullmatch(tag) is not None


def terraform_file_record(version: str, tag: str, root: Path = ROOT) -> dict:
    """The release record the tree gives a terraform-file tag; its record must equal it."""
    codes_path = f"{TERRAFORM_FILE_ROOT}/codes.json"
    table_path = f"{TERRAFORM_FILE_ROOT}/formats.json"
    vectors_path = f"{TERRAFORM_FILE_ROOT}/manifest.json"
    codes = json.loads((root / codes_path).read_text("utf-8"))
    formats = json.loads((root / table_path).read_text("utf-8"))
    vectors = json.loads((root / vectors_path).read_text("utf-8"))
    listed = codes.get("codes") if isinstance(codes, dict) else None
    if (not isinstance(listed, list) or not listed
            or not all(isinstance(code, dict) and isinstance(code.get("code"), str) for code in listed)
            or len({code["code"] for code in listed}) != len(listed)):
        raise ValueError("terraform-file code list has no codes, or names one twice")
    rows = formats.get("table") if isinstance(formats, dict) else None
    if (not isinstance(rows, list) or not rows
            or not all(isinstance(row, dict) and isinstance(row.get("document"), str)
                       and isinstance(row.get("accepted"), list) and row["accepted"]
                       and all(isinstance(accepted, str) for accepted in row["accepted"])
                       and len(set(row["accepted"])) == len(row["accepted"]) for row in rows)
            or len({row["document"] for row in rows}) != len(rows)
            or not isinstance(formats.get("release"), str)
            or PLAIN_VERSION.fullmatch(formats["release"]) is None):
        raise ValueError("terraform-file format table has no rows or no release, or names a "
                         "document or a format_version twice")
    listed_vectors = vectors.get("vectors") if isinstance(vectors, dict) else None
    if (not isinstance(listed_vectors, list) or not listed_vectors
            or not all(isinstance(row, dict) and isinstance(row.get("id"), str) for row in listed_vectors)
            or len({row["id"] for row in listed_vectors}) != len(listed_vectors)):
        raise ValueError("terraform-file vectors' manifest has no vectors, or two share an id")
    table = {row["document"]: sorted(row["accepted"]) for row in rows}
    return {"companion": "terraform-file", "releaseVersion": version, "tag": tag,
            "maturity": TERRAFORM_FILE_MATURITY, "reading": TERRAFORM_FILE_READING,
            "formatTable": {"path": table_path, "sha256": "sha256:" + sha256(root / table_path),
                            "release": formats["release"], "table": table,
                            "added": terraform_file_added(table, formats["release"],
                                                          terraform_file_worktree_records(tag, root))},
            "codes": {"path": codes_path, "sha256": "sha256:" + sha256(root / codes_path),
                      "codes": [code["code"] for code in listed]},
            "corpus": {"path": vectors_path, "sha256": "sha256:" + sha256(root / vectors_path),
                       "vectors": sorted(row["id"] for row in listed_vectors),
                       "files": tree_digests(TERRAFORM_FILE_ROOT, root)},
            "formatDigests": {path: "sha256:" + sha256(root / path)
                              for path in (TERRAFORM_FILE_TEXT, TERRAFORM_FILE_README)}}


def validate_terraform_file_artifacts(version: str, tag: str, root: Path = ROOT) -> None:
    """Gate the independently versioned terraform-file companion on its own release record."""
    record_path = root / "releases" / f"{tag}.json"
    if not record_path.is_file():
        raise ValueError("terraform-file release record is missing for the exact tag")
    release = json.loads(record_path.read_text("utf-8"))
    if not isinstance(release, dict) or set(release) != TERRAFORM_FILE_RECORD_KEYS:
        raise ValueError("terraform-file release record has an invalid closed shape")
    expected = terraform_file_record(version, tag, root)
    for keys, message in (
            (("companion", "releaseVersion", "tag", "maturity", "reading"),
             "terraform-file release identity, maturity or reading does not match"),
            (("formatDigests",), "terraform-file text or README bytes differ from the release record"),
            (("formatTable",), "terraform-file format table identity or rows do not match"),
            (("corpus",), "terraform-file corpus identity or vectors do not match"),
            (("codes",), "terraform-file code list identity or codes do not match")):
        if any(release[key] != expected[key] for key in keys):
            raise ValueError(message)
    # The tag's number is the release of the table it carries (spec/terraform-file.md section 4).
    if release["formatTable"]["release"] != version:
        raise ValueError(f"a terraform-file tag's number must be the release of the format table it "
                         f"carries: {tag} carries table release {release['formatTable']['release']}")
    conflict = terraform_file_history_conflict(terraform_file_worktree_records(tag, root), release)
    if conflict is not None:
        raise ValueError(f"terraform-file reading conflicts with an earlier release record: {conflict}")
    codes, table, manifest = (json.loads((root / release[key]["path"]).read_text("utf-8"))
                              for key in ("codes", "formatTable", "corpus"))
    text = (root / TERRAFORM_FILE_TEXT).read_text("utf-8")
    if TERRAFORM_FILE_STATUS_SENTENCE.findall(text) != [TERRAFORM_FILE_MATURITY] or any(
            not isinstance(document, dict)
            or (document.get("companion"), document.get("reading"), document.get("status"))
            != ("terraform-file", TERRAFORM_FILE_READING, TERRAFORM_FILE_MATURITY)
            for document in (codes, table, manifest)):
        raise ValueError("a terraform-file release requires the text, the code list, the format "
                         f"table and the vectors' manifest to say status {TERRAFORM_FILE_MATURITY}")
    readme = (root / TERRAFORM_FILE_README).read_text("utf-8")
    label = manifest.get("label", "")
    if (any(TERRAFORM_FILE_PROPOSED_STATEMENT.search(" ".join(document.split()))
            for document in (text, readme))
            or any(REGISTRY_UNRELEASED_WORDING.search(heading)
                   for heading in re.findall(r"^# .*$", readme, re.MULTILINE))
            or not isinstance(label, str) or REGISTRY_UNRELEASED_WORDING.search(label)):
        raise ValueError("a terraform-file release requires the text and the vectors' README not to "
                         "call the reading proposed, nor the README's heading or the manifest's label")
    if not (root / "releases" / f"{tag}.md").is_file():
        raise ValueError("terraform-file release notes are missing for the exact tag")


def terraform_file_worktree_records(tag: str, root: Path = ROOT) -> list[object]:
    """Every terraform-file release record in the worktree but the tag's own, as read."""
    own = root / "releases" / f"{tag}.json"
    return [json.loads(path.read_text("utf-8"))
            for path in sorted((root / "releases").glob("terraform-file-v*.json"))
            if path != own and not path.name.endswith(".milestone.json")]


def terraform_file_contents(
        record: object) -> tuple[tuple[int, int, int], set[str], set[tuple[str, str]], set[str]] | None:
    """The table release, the codes, the table rows (document, accepted format_version) and the vector
    ids a record names, or None for a record not of the record's form."""
    if not isinstance(record, dict):
        return None
    table, codes, corpus = record.get("formatTable"), record.get("codes"), record.get("corpus")
    if not (isinstance(table, dict) and isinstance(codes, dict) and isinstance(corpus, dict)
            and isinstance(table.get("release"), str) and isinstance(table.get("table"), dict)
            and isinstance(codes.get("codes"), list) and isinstance(corpus.get("vectors"), list)):
        return None
    number = PLAIN_VERSION.fullmatch(table["release"])
    rows = table["table"].items()
    if (number is None or not all(isinstance(accepted, list) for _, accepted in rows)
            or not all(isinstance(item, str) for item in (*codes["codes"], *corpus["vectors"],
                                                          *(a for _, accepted in rows for a in accepted)))):
        return None
    major, minor, patch = (int(part) for part in number.groups())
    return ((major, minor, patch), set(codes["codes"]),
            {(document, accepted) for document, row in rows for accepted in row}, set(corpus["vectors"]))


def terraform_file_added(table: dict[str, list[str]], release: str, records: list[object]) -> dict[str, list[str]]:
    """The rows of `table`, at table release `release`, that the latest lower table release of the
    reading among `records` does not accept: every row for the first release, and none for an
    erratum, which takes the next patch with no new row. A record not of the form is left to
    terraform_file_history_conflict, which refuses it."""
    number = PLAIN_VERSION.fullmatch(release)
    current = tuple(int(part) for part in number.groups()) if number else None
    lower = [contents for contents in (terraform_file_contents(record) for record in records
                                       if isinstance(record, dict)
                                       and record.get("reading") == TERRAFORM_FILE_READING)
             if contents is not None and current is not None and contents[0] < current]
    kept = max(lower, key=lambda contents: contents[0])[2] if lower else set()
    return {document: new for document, accepted in table.items()
            if (new := sorted(version for version in accepted if (document, version) not in kept))}


def terraform_file_history_conflict(records: list[object], release: dict) -> str | None:
    """Why `release` cannot stand beside the other records of its reading, or None.

    Two records never carry one table release. The record of the higher table release names every
    code, every accepted format_version of each document and every vector the lower names. The
    reading's first table release is 1.0.0, and each later one is the next patch of the latest
    earlier one, whether it accepts new rows or, as an erratum, none; the text defines no minor or
    major release of the table. The record's `added` names exactly the rows its table release
    accepts that the latest earlier one does not. The bytes of the text, the lists and the vectors
    may change, as the registry's rows may; a claim names the exact release, whose record pins them.
    A record not of the record's form conflicts."""
    current = terraform_file_contents(release)
    if current is None:
        return "the release record is not of the record's form"
    earlier: list[tuple[int, int, int]] = []
    for previous in records:
        if not isinstance(previous, dict) or not isinstance(previous.get("reading"), str):
            return "a record is not of the record's form"
        if previous["reading"] != release["reading"]:
            continue
        contents = terraform_file_contents(previous)
        if contents is None:
            return "a record is not of the record's form"
        if contents[0] == current[0]:
            return "two records carry table release %d.%d.%d" % current[0]
        lower, higher = sorted((contents, current), key=lambda pair: pair[0])
        if not all(kept <= grown for kept, grown in zip(lower[1:], higher[1:])):
            return ("table release %d.%d.%d lacks a code, a table row or a vector that %d.%d.%d names"
                    % (*higher[0], *lower[0]))
        if contents[0] < current[0]:
            earlier.append(contents[0])
    if earlier:
        latest = max(earlier)
        expected = (latest[0], latest[1], latest[2] + 1)
        if current[0] != expected:
            return ("table release %d.%d.%d is not the next patch of the latest earlier one, %d.%d.%d"
                    % (*current[0], *latest))
    elif current[0] != TERRAFORM_FILE_FIRST_TABLE:
        return "the reading's first table release is %d.%d.%d, not %d.%d.%d" % (
            *TERRAFORM_FILE_FIRST_TABLE, *current[0])
    table = release["formatTable"]
    if table.get("added") != terraform_file_added(table["table"], table["release"], records):
        return "the record's added rows are not the rows its table release accepts beyond the last"
    return None


def validate_terraform_file_history(tag: str) -> None:
    """Compare immutable tagged records, so editing old working files cannot shrink the reading,
    skip a table release or misstate the rows one adds."""
    release = json.loads((ROOT / "releases" / f"{tag}.json").read_text("utf-8"))
    records = [json.loads(git("show", f"refs/tags/{previous}:releases/{previous}.json"))
               for previous in git("tag", "--list", "terraform-file-v*").splitlines()
               if previous != tag and is_terraform_file_tag(previous)]
    conflict = terraform_file_history_conflict(records, release)
    if conflict is not None:
        raise ValueError(f"terraform-file reading conflicts with immutable tagged release history: {conflict}")


def validate_policy_artifacts(version: str, tag: str, root: Path = ROOT) -> None:
    """Gate only the independently versioned, draft Policy companion surface."""
    manifest_path = root / "releases" / f"{tag}.json"
    if not manifest_path.is_file():
        raise ValueError("Policy release manifest is missing for the exact tag")
    release = json.loads(manifest_path.read_text("utf-8"))
    expected_keys = {"companion", "releaseVersion", "tag", "maturity", "formatVersion",
                     "consumerSpecVersions", "schemas", "corpus", "formatDigests"}
    if set(release) != expected_keys:
        raise ValueError("Policy release manifest has an invalid closed shape")
    if (release["companion"] != "policy" or release["releaseVersion"] != version
            or release["tag"] != tag or release["maturity"] != "draft"
            or release["formatVersion"] != POLICY_FORMAT
            or release["consumerSpecVersions"] != ["0.2.0-draft"]):
        raise ValueError("Policy release identity, maturity or format does not match")
    expected_schemas = {name: f"https://judgmentpack.org/schema/policy/{POLICY_FORMAT}/{name}.schema.json"
                        for name in ("common", "policy", "governing-adoption", "fixture", "vectors")}
    if release["schemas"] != expected_schemas:
        raise ValueError("Policy release schema identities do not match the exact format")
    for name, identity in expected_schemas.items():
        directory = POLICY_SCHEMA_ROOT if name in ("common", "policy", "governing-adoption") else POLICY_ROOT
        schema = json.loads((root / directory / f"{name}.schema.json").read_text("utf-8"))
        if schema.get("$id") != identity:
            raise ValueError("Policy schema $id differs from its immutable format identity")
    digests = release["formatDigests"]
    if not isinstance(digests, dict) or set(digests) != set(POLICY_FORMAT_PATHS):
        raise ValueError("Policy format digest inventory does not match")
    if any(value != "sha256:" + sha256(root / path) for path, value in digests.items()):
        raise ValueError("Policy format bytes differ from the release manifest")
    # Reusing an exact selector cannot revise published meaning or its resource URLs.
    for previous_path in (root / "releases").glob("policy-v*.json"):
        if previous_path == manifest_path:
            continue
        previous = json.loads(previous_path.read_text("utf-8"))
        if previous.get("formatVersion") == POLICY_FORMAT:
            if (previous.get("formatDigests") != digests
                    or previous.get("schemas") != expected_schemas
                    or previous.get("consumerSpecVersions") != release["consumerSpecVersions"]
                    or previous.get("corpus") != release["corpus"]):
                raise ValueError("Policy exact format identity conflicts with an earlier release record")
    corpus_path = f"{POLICY_ROOT}/vectors/manifest.json"
    manifest = json.loads((root / corpus_path).read_text("utf-8"))
    if release["corpus"] != {"path": corpus_path, "sha256": "sha256:" + sha256(root / corpus_path), "cases": 124,
                                "files": policy_corpus_digests(root)}:
        raise ValueError("Policy corpus identity or count does not match")
    if (manifest.get("maturity") != "draft" or manifest.get("vectorSuiteVersion") != "1"
            or len(manifest.get("cases", [])) != 124):
        raise ValueError("Policy corpus selector, maturity or rows do not match")
    rfc = (root / "rfcs/0023-policy-companion.md").read_text("utf-8")
    if not re.search(r"^- Status: Accepted$", rfc, re.MULTILINE):
        raise ValueError("Policy release requires RFC 0023 acceptance at draft maturity")
    if not (root / "releases" / f"{tag}.md").is_file():
        raise ValueError("Policy release notes are missing for the exact tag")


def policy_corpus_digests(root: Path = ROOT) -> dict[str, str]:
    paths = sorted(path for directory in ("examples", "vectors")
                   for path in (root / POLICY_ROOT / directory).rglob("*")
                   if path.is_file())
    return {path.relative_to(root).as_posix(): "sha256:" + sha256(path) for path in paths}


def validate_policy_history(tag: str) -> None:
    """Compare immutable tagged records, so editing old working files cannot repoint a format."""
    release = json.loads((ROOT / "releases" / f"{tag}.json").read_text("utf-8"))
    for previous in git("tag", "--list", "policy-v*").splitlines():
        if previous == tag or not is_policy_tag(previous):
            continue
        old = json.loads(git("show", f"refs/tags/{previous}:releases/{previous}.json"))
        if old.get("formatVersion") == release["formatVersion"]:
            for key in ("schemas", "formatDigests", "consumerSpecVersions", "corpus"):
                if old.get(key) != release[key]:
                    raise ValueError("Policy exact format conflicts with immutable tagged release history")


def bundle_paths(tag: str, commit: str) -> tuple[str, ...]:
    if is_policy_tag(tag):
        return (*POLICY_BUNDLE_PATHS, f"releases/{tag}.md", f"releases/{tag}.json")
    if is_registry_tag(tag):
        return (*REGISTRY_BUNDLE_PATHS, f"releases/{tag}.md", f"releases/{tag}.json")
    if is_terraform_file_tag(tag):
        return (*TERRAFORM_FILE_BUNDLE_PATHS, f"releases/{tag}.md", f"releases/{tag}.json")
    # Policy, the registry and the terraform-file reading have their own release identities. Do not
    # carry their separately versioned schemas/corpora in a Core archive or alter the frozen Core
    # manifests; the companion texts under spec/ stay in it.
    paths = []
    for path in BUNDLE_PATHS:
        if path in ("schema", "conformance"):
            children = git("ls-tree", "--name-only", f"{commit}:{path}").splitlines()
            paths.extend(f"{path}/{child}" for child in children if child not in INDEPENDENT_DIRECTORIES)
        else:
            paths.append(path)
    if tag in CORE_RC_IDENTITIES:
        paths.extend((f"releases/{tag}.json", "docs/releases/v0.3.0.md"))
    if tag == CORE_CARRIED_TAG:
        paths.extend((f"releases/{tag}.json", *CORE_CARRIED_BUNDLE_PATHS))
    if is_patch_release(tag):
        record, _ = normative_record(tag)
        paths.extend((*CORE_CARRIED_BUNDLE_PATHS, record))
    if tag in RETAINED_INVENTORIES:
        paths.extend((*RETAINED_BUNDLE_PATHS, RETAINED_INVENTORIES[tag], f"releases/{tag}.milestone.json"))
    return (*paths, core_release_notes_path(tag).relative_to(ROOT).as_posix())


def core_release_notes_path(tag: str, root: Path = ROOT) -> Path:
    """Return the immutable notes path, or the prepared notes before release publication."""
    published = root / "releases" / f"{tag}.md"
    if published.is_file():
        return published
    return root / "docs" / "releases" / f"{tag}.md"


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def release_version(tag: str) -> str:
    scoped = (POLICY_TAG_PATTERN.fullmatch(tag) or REGISTRY_TAG_PATTERN.fullmatch(tag)
              or TERRAFORM_FILE_TAG_PATTERN.fullmatch(tag))
    if scoped:
        return scoped.group(1)
    if not tag.startswith("v") or not VERSION_PATTERN.fullmatch(tag[1:]):
        raise ValueError("release tag must be exact v-SemVer, policy-vSemVer-draft.N, "
                         "registry-vMAJOR.MINOR.PATCH or terraform-file-vMAJOR.MINOR.PATCH")
    return tag[1:]


def carried_spec_version(version: str) -> str:
    """The specVersion a Core release version carries under the release numbering rule.

    A plain X.Y.Z carries X.Y.0. Any other version is returned whole: no prerelease suffix is
    stripped to infer a compatible specVersion. A reviewed mapping overrides this (v0.4.0, the RCs).
    """
    plain = PLAIN_VERSION.fullmatch(version)
    return f"{plain.group(1)}.{plain.group(2)}.0" if plain else version


def is_patch_release(tag: str) -> bool:
    """A plain Core tag vX.Y.Z with Z > 0 and no reviewed mapping: a later release of X.Y.0."""
    if tag in CORE_MAPPED_IDENTITIES or not tag.startswith("v"):
        return False
    plain = PLAIN_VERSION.fullmatch(tag[1:])
    return plain is not None and plain.group(3) != "0"


def normative_record(tag: str) -> tuple[str, str]:
    """The record of the normative bytes a patch tag carries, and the record's pinned SHA-256."""
    spec_version = carried_spec_version(release_version(tag))
    if spec_version not in NORMATIVE_RECORDS:
        raise ValueError(f"{tag} would carry specVersion {spec_version}, which has no normative "
                         "record: a patch tag carries the recorded normative files of a released "
                         "specVersion unchanged")
    return NORMATIVE_RECORDS[spec_version]


def normative_paths(spec_version: str, root: Path = ROOT) -> set[str]:
    """The files a patch release carries unchanged, derived from the tree rather than listed.

    The Core text and schema, both corpus manifests, every document case and evaluation pack they
    name, and every schema in schema/ or conformance/ whose `$id` is under this specVersion (the
    families the record-shape catalog counts as released with it). The errata, the READMEs and the
    examples are not among them: an erratum or a clearer explanation may follow a release.
    """
    paths = {"spec/judgment-pack-core.md", "schema/judgment-pack-core.schema.json",
             "conformance/manifest.json", "conformance/evaluation/manifest.json"}
    document = json.loads((root / "conformance" / "manifest.json").read_text("utf-8"))
    paths.update("conformance/" + case["path"] for case in document["cases"])
    evaluation = json.loads((root / "conformance" / "evaluation" / "manifest.json").read_text("utf-8"))
    paths.update("conformance/evaluation/" + case["pack"] for case in evaluation["cases"])
    prefix = f"{SCHEMA_NAMESPACE}{spec_version}/"
    for directory in ("schema", "conformance"):
        for path in (root / directory).rglob("*.schema.json"):
            schema = json.loads(path.read_text("utf-8"))
            if isinstance(schema, dict) and str(schema.get("$id", "")).startswith(prefix):
                paths.add(path.relative_to(root).as_posix())
    return paths


def validate_unchanged_normative_artifacts(tag: str, root: Path = ROOT) -> None:
    """Hold a patch release's normative artifacts to the bytes its X.Y.0 release recorded."""
    record_path, pinned = normative_record(tag)
    spec_version = carried_spec_version(release_version(tag))
    record = root / record_path
    if not record.is_file() or sha256(record) != pinned:
        raise ValueError(f"the normative record {record_path} differs from the bytes the builder pins")
    files = json.loads(record.read_text("utf-8"))["files"]
    if set(files) != normative_paths(spec_version, root):
        raise ValueError(f"{tag}'s normative artifact inventory differs from v{spec_version}'s record")
    changed = sorted(path for path, digest in files.items()
                     if not (root / path).is_file() or digest != "sha256:" + sha256(root / path))
    if changed:
        raise ValueError(f"{tag} changes normative artifacts of specVersion {spec_version}: "
                         + ", ".join(changed))


def archive_digests(archive: Path, prefix: str) -> dict[str, str]:
    """The SHA-256 of each regular file in a bundle, by its path under the bundle's prefix."""
    digests = {}
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                if not member.is_dir() and member.filename.startswith(prefix):
                    digests[member.filename[len(prefix):]] = (
                        "sha256:" + hashlib.sha256(bundle.read(member)).hexdigest())
        return digests
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            if member.isfile() and member.name.startswith(prefix):
                data = bundle.extractfile(member).read()
                digests[member.name[len(prefix):]] = "sha256:" + hashlib.sha256(data).hexdigest()
    return digests


def validate_bundled_normative_artifacts(tag: str, archives: list[Path], prefix: str,
                                         root: Path = ROOT) -> None:
    """Hold each patch bundle, as archived, to the record the worktree was held to.

    The worktree check cannot see what an export attribute in .gitattributes leaves out of, or
    rewrites in, an archive, so every recorded file and the record itself are read back here.
    """
    record_path, pinned = normative_record(tag)
    expected = {**json.loads((root / record_path).read_text("utf-8"))["files"],
                record_path: "sha256:" + pinned}
    for archive in archives:
        bundled = archive_digests(archive, prefix)
        wrong = sorted(path for path, digest in expected.items() if bundled.get(path) != digest)
        if wrong:
            raise ValueError(f"{archive.name} does not carry {tag}'s recorded normative artifacts: "
                             + ", ".join(wrong))


def release_identity(tag: str, root: Path = ROOT) -> dict | None:
    """The distribution identity a bundle carries as release-identity.json, if it has one."""
    if tag in GENERATED_IDENTITIES:
        return dict(GENERATED_IDENTITIES[tag])
    if is_patch_release(tag):
        version = release_version(tag)
        manifest = json.loads((root / "conformance" / "manifest.json").read_text("utf-8"))
        return {"releaseVersion": version, "tag": tag, "specVersion": carried_spec_version(version),
                "maturity": manifest["status"], "distribution": CORE_UNCHANGED_DISTRIBUTION}
    return None


def validate_artifacts(version: str, tag: str, root: Path = ROOT) -> None:
    """Check exact format pins against the specVersion the tag carries.

    A plain tag vX.Y.Z carries X.Y.0, and a patch tag must carry that release's normative bytes
    unchanged. Only the reviewed mappings give another distribution identity: the RCs distribute
    proposed 0.3.0 artifacts, not a released conformance corpus, and v0.4.0 carries the released
    specVersion 0.3.0 unchanged, so its pins stay at 0.3.0. No arbitrary prerelease suffix may be
    stripped to infer a compatible specVersion. The v0.3.0 final carries RC2's selected leaf under
    its own inventory and no mapping.
    """
    if version != release_version(tag):
        raise ValueError("release version does not match the exact tag")
    if tag not in CORE_MAPPED_IDENTITIES and (root / "releases" / f"{tag}.json").exists():
        raise ValueError("only the allowlisted Core distributions have a release mapping")
    if tag in CORE_MAPPED_IDENTITIES:
        mapping = root / "releases" / f"{tag}.json"
        if not mapping.is_file():
            raise ValueError("Core release mapping is missing for the exact tag")
        if json.loads(mapping.read_text("utf-8")) != CORE_MAPPED_IDENTITIES[tag]:
            raise ValueError("Core release mapping does not match the reviewed identity")
        version = CORE_MAPPED_IDENTITIES[tag]["specVersion"]
    else:
        version = carried_spec_version(version)
    manifest = json.loads((root / "conformance" / "manifest.json").read_text("utf-8"))
    evaluation = json.loads(
        (root / "conformance" / "evaluation" / "manifest.json").read_text("utf-8")
    )
    schema = json.loads(
        (root / "schema" / "judgment-pack-core.schema.json").read_text("utf-8")
    )
    if manifest.get("specVersion") != version:
        raise ValueError("release tag does not match the conformance specVersion")
    if tag in CORE_MAPPED_IDENTITIES:
        if manifest.get("suiteVersion") != version:
            raise ValueError("Core distribution does not match the document corpus suiteVersion")
        if manifest.get("status") != "draft" or evaluation.get("status") != "draft":
            raise ValueError("Core distribution requires draft manifest maturity")
    if evaluation.get("specVersion") != version:
        raise ValueError("release tag does not match the evaluation corpus specVersion")
    if evaluation.get("suiteVersion") != version:
        raise ValueError("release tag does not match the evaluation corpus suiteVersion")
    if schema.get("properties", {}).get("specVersion", {}).get("const") != version:
        raise ValueError("release tag does not match the schema specVersion constant")
    expected_schema_id = (
        f"https://judgmentpack.org/schema/{version}/judgment-pack-core.schema.json"
    )
    if schema.get("$id") != expected_schema_id:
        raise ValueError("schema $id does not point at the exact release version")
    if is_patch_release(tag):
        validate_unchanged_normative_artifacts(tag, root)
    if tag in RETAINED_INVENTORIES:
        if tag == CORE_FINAL_TAG:
            validate_final_retained_inventory(root)
            validate_reader_support_identity(tag, root)
        else:
            validate_retained_inventory(root, tag)
        milestone = root / "releases" / f"{tag}.milestone.json"
        if not milestone.is_file() or json.loads(milestone.read_text("utf-8")) != CORE_MILESTONE:
            raise ValueError(f"{tag} must preserve the final Core milestone")
        if "- Status: Accepted" not in (root / "rfcs/0029-retained-column-conversions.md").read_text("utf-8").splitlines():
            raise ValueError(f"{tag} requires recorded RFC0029 acceptance at draft maturity")
    release_notes = core_release_notes_path(tag, root)
    if not release_notes.is_file():
        raise ValueError("release notes are missing for the exact tag")


def validate(tag: str, commit: str) -> str:
    """Gate a release on the tree that was actually validated.

    ``validate_artifacts`` reads the worktree while ``build`` archives the resolved commit, so the two
    describe the same release only when ``HEAD`` is that commit. Checking it here is what makes the
    validated tree and the archived tree one tree instead of two that happen to share a tag.
    """
    version = release_version(tag)
    if is_policy_tag(tag):
        validate_policy_artifacts(version, tag)
    elif is_registry_tag(tag):
        validate_registry_artifacts(version, tag)
    elif is_terraform_file_tag(tag):
        validate_terraform_file_artifacts(version, tag)
    else:
        validate_artifacts(version, tag)

    resolved_commit = git("rev-parse", "--verify", f"{commit}^{{commit}}")
    resolved_tag = git("rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")
    if resolved_commit != resolved_tag:
        raise ValueError("release tag does not resolve to the requested commit")
    resolved_head = git("rev-parse", "--verify", "HEAD^{commit}")
    if resolved_head != resolved_commit:
        raise ValueError(
            "release worktree is not checked out at the release commit: "
            f"HEAD is {resolved_head} and {tag} resolves to {resolved_commit}. "
            "The artifacts are validated from the worktree and archived from the commit, so they "
            f"must be the same tree; check out {tag} and run the builder again."
        )
    if is_policy_tag(tag):
        validate_policy_history(tag)
    if is_registry_tag(tag):
        validate_registry_history(tag)
    if is_terraform_file_tag(tag):
        validate_terraform_file_history(tag)
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("tracked release worktree is dirty")
    return version


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build(tag: str, commit: str, output: Path) -> list[Path]:
    version = validate(tag, commit)
    output.mkdir(parents=True, exist_ok=True)
    artifact = ("judgment-pack-policy" if is_policy_tag(tag)
                else "judgment-pack-registry" if is_registry_tag(tag)
                else "judgment-pack-terraform-file" if is_terraform_file_tag(tag)
                else "judgment-pack-spec")
    prefix = f"{artifact}-{version}/"
    extra = ()
    identity = release_identity(tag)
    if identity is not None:
        # This generated member is covered by both archive checksums/attestations.
        identity = {**identity, "sourceCommit": git("rev-parse", "--verify", f"{commit}^{{commit}}")}
        encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")) + "\n"
        extra = (f"--add-virtual-file={prefix}release-identity.json:{encoded}",)
    common = (
        "archive",
        f"--prefix={prefix}",
        *extra,
        commit,
        *bundle_paths(tag, commit),
    )
    archives = [
        output / f"{artifact}_{version}_artifacts.tar.gz",
        output / f"{artifact}_{version}_artifacts.zip",
    ]
    subprocess.run(
        ["git", *common[:1], "--format=tar.gz", f"--output={archives[0]}", *common[1:]],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        ["git", *common[:1], "--format=zip", f"--output={archives[1]}", *common[1:]],
        cwd=ROOT,
        check=True,
    )
    if is_patch_release(tag):
        try:
            validate_bundled_normative_artifacts(tag, archives, prefix)
        except ValueError:
            for archive in archives:
                archive.unlink(missing_ok=True)
            raise
    checksums = output / "checksums.txt"
    checksums.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in archives),
        encoding="utf-8",
    )
    return [*archives, checksums]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    artifacts = build(arguments.tag, arguments.commit, arguments.output.resolve())
    for artifact in artifacts:
        print(f"{artifact.name}: {artifact.stat().st_size} bytes")


if __name__ == "__main__":
    main()

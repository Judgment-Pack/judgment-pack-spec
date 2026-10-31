#!/usr/bin/env python3
"""Fingerprint the record shapes the specification defines (catalog/README.md).

    record_shapes.py generate            write catalog/record-shapes.json from the tree
    record_shapes.py check               hold the catalog, the change records and the format-status
                                         records to the tree and to releases/
    record_shapes.py record --slug NAME --reason TEXT
                                         write the next change record for every schema whose digest
                                         differs from the one the change records end at

The inventory is derived from the tree, never listed: every `*.schema.json` outside a dot directory
or `node_modules` is found, and it is in scope when its `$id` is under NAMESPACE. Its family and
version come from that `$id`. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = "catalog/record-shapes.json"
STATUS = "catalog/format-status.json"
CHANGES = "catalog/changes"
RELEASES = "releases"
CATALOG_FORMAT = "judgment-pack-record-shapes/1"
STATUS_FORMAT = "judgment-pack-format-status/1"
NAMESPACE = "https://judgmentpack.org/schema/"
SUFFIX = ".schema.json"
# Directories that hold specification schemas: a schema file in one must be in scope, so a mistyped
# `$id` cannot drop a shape from the catalog unnoticed.
SPEC_DIRECTORIES = ("schema", "conformance")
SKIPPED_DIRECTORIES = {"node_modules"}
NORMALIZATION = (
    "jps-record-shape-normalization/1: the file's bytes are decoded as UTF-8 (no byte order mark) "
    "and parsed as exactly one JSON value (RFC 8259) in which no object repeats a member name and "
    "every number is an integer from -(2^53-1) to 2^53-1 written without a fraction or an "
    "exponent; the value is serialized as RFC 8785 (JCS) does: object members sorted by the UTF-16 "
    "code units of their names, no whitespace between tokens, strings with only quotation mark, "
    "reverse solidus and the control characters U+0000-U+001F escaped (\\b \\t \\n \\f \\r, "
    "otherwise \\u00xx in lowercase hexadecimal) and every other character written as itself, "
    "integers in shortest decimal form, true, false and null as themselves; the result is encoded "
    "as UTF-8 with no trailing newline. The digest is SHA-256 over those bytes, written "
    "sha256:<64 lowercase hexadecimal digits>."
)
SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*))?$"
)
FORMAT_VERSION = re.compile(r"^(0|[1-9][0-9]*)$")
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RECORD_FILE = re.compile(r"^([0-9]{4})-([a-z0-9]+(?:-[a-z0-9]+)*)\.json$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
TAG = re.compile(r"^(?:([a-z][a-z0-9]*(?:-[a-z0-9]+)*)-)?v(.+)$")
# The distribution suffixes VERSIONING.md defines: a candidate of a milestone (`-rc.N`) or a scoped
# cut (`-alpha.N`). Neither is a compatibility baseline.
CANDIDATE_IDENTIFIERS = {"rc", "alpha"}
MAX_INTEGER = 2 ** 53 - 1


class ShapeError(Exception):
    """A tree, catalog, change record or status record the tool refuses."""


# Normalization ------------------------------------------------------------------------------------

def _pairs(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for name, value in pairs:
        if name in result:
            raise ShapeError("repeats the member name %r" % name)
        result[name] = value
    return result


def _constant(name: str) -> object:
    raise ShapeError("has the non-JSON number %s" % name)


def _no_float(text: str) -> object:
    raise ShapeError("has the non-integer number %s" % text)


def parse(data: bytes) -> object:
    """Parse one schema file under the normalization's input rules."""
    if data.startswith(b"\xef\xbb\xbf"):
        raise ShapeError("starts with a byte order mark")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ShapeError("is not UTF-8: %s" % error) from None
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant,
                           parse_float=_no_float)
    except json.JSONDecodeError as error:
        raise ShapeError("is not one JSON value: %s" % error) from None
    _check_integers(value)
    return value


def _check_integers(value: object) -> None:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, int):
        if abs(value) > MAX_INTEGER:
            raise ShapeError("has the integer %d outside +/-(2^53-1)" % value)
    elif isinstance(value, list):
        for item in value:
            _check_integers(item)
    elif isinstance(value, dict):
        for item in value.values():
            _check_integers(item)


def _utf16(name: str) -> bytes:
    return name.encode("utf-16-be", "surrogatepass")


def _serialize(value: object, out: list[str]) -> None:
    if isinstance(value, dict):
        out.append("{")
        for index, name in enumerate(sorted(value, key=_utf16)):
            if index:
                out.append(",")
            out.append(json.dumps(name, ensure_ascii=False))
            out.append(":")
            _serialize(value[name], out)
        out.append("}")
    elif isinstance(value, list):
        out.append("[")
        for index, item in enumerate(value):
            if index:
                out.append(",")
            _serialize(item, out)
        out.append("]")
    else:
        # A string, an integer, true, false or null: json.dumps writes each as JCS does for the
        # values parse() admits.
        out.append(json.dumps(value, ensure_ascii=False))


def normalize(value: object) -> str:
    out: list[str] = []
    _serialize(value, out)
    text = "".join(out)
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        raise ShapeError("has a string with an unpaired surrogate") from None
    return text


def digest(normalized: str) -> str:
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# Versions -----------------------------------------------------------------------------------------

def _semver_key(version: str) -> tuple:
    match = SEMVER.match(version)
    if not match:
        raise ShapeError("%r is not a semantic version" % version)
    core = tuple(int(part) for part in match.groups()[:3])
    prerelease = match.group(4)
    if prerelease is None:
        return core + ((1,),)
    identifiers = tuple((0, int(part), "") if part.isdigit() else (1, 0, part)
                        for part in prerelease.split("."))
    return core + ((0,) + identifiers,)


def version_key(version: str) -> tuple:
    """Order semantic versions by SemVer 2.0.0 precedence, and bare format numbers numerically."""
    if FORMAT_VERSION.match(version):
        return (0, int(version))
    return (1,) + _semver_key(version)


def latest(versions: list[str]) -> str:
    kinds = {bool(FORMAT_VERSION.match(version)) for version in versions}
    if len(kinds) > 1:
        raise ShapeError("versions %s mix format numbers and semantic versions" % sorted(versions))
    return max(versions, key=version_key)


# Discovery ----------------------------------------------------------------------------------------

def find_schema_files(root: Path) -> list[str]:
    found = []
    for directory, subdirectories, files in os.walk(root):
        subdirectories[:] = sorted(name for name in subdirectories
                                   if not name.startswith(".") and name not in SKIPPED_DIRECTORIES)
        for name in files:
            if name.endswith(SUFFIX):
                found.append((Path(directory) / name).relative_to(root).as_posix())
    return sorted(found)


def identify(schema_id: object) -> tuple[str, str]:
    """Return (family, version) for an `$id` under NAMESPACE.

    `<NAMESPACE><specVersion>/<path>/<name>[-<N>].schema.json` is a family on the Core route: the
    path and name without the model number, at the specification version.
    `<NAMESPACE><family>/<formatVersion>/<member>.schema.json` is an independently versioned family.
    """
    if not isinstance(schema_id, str) or not schema_id.startswith(NAMESPACE):
        raise ShapeError("$id %r is not under %s" % (schema_id, NAMESPACE))
    rest = schema_id[len(NAMESPACE):]
    if not rest.endswith(SUFFIX):
        raise ShapeError("$id %r does not end with %s" % (schema_id, SUFFIX))
    segments = rest[:-len(SUFFIX)].split("/")
    if SEMVER.match(segments[0]):
        names = segments[1:]
        if not names:
            raise ShapeError("$id %r names no schema after its version" % schema_id)
        names[-1] = re.sub(r"-[0-9]+$", "", names[-1])
        family, version = "/".join(names), segments[0]
    else:
        if len(segments) < 3:
            raise ShapeError("$id %r names no family, format version and member" % schema_id)
        family, version = segments[0], segments[1]
        if not (FORMAT_VERSION.match(version) or SEMVER.match(version)):
            raise ShapeError("$id %r has no format version after its family" % schema_id)
    if not all(NAME.match(part) for part in family.split("/")):
        raise ShapeError("$id %r gives the family %r, which is not lowercase words and hyphens"
                         % (schema_id, family))
    return family, version


def build_catalog(root: Path = ROOT) -> dict:
    schemas, out_of_scope, problems = [], [], []
    for path in find_schema_files(root):
        try:
            value = parse((root / path).read_bytes())
        except ShapeError as error:
            problems.append("%s %s" % (path, error))
            continue
        schema_id = value.get("$id") if isinstance(value, dict) else None
        if not (isinstance(schema_id, str) and schema_id.startswith(NAMESPACE)):
            if path.split("/", 1)[0] in SPEC_DIRECTORIES:
                problems.append("%s is in %s/ but its $id %r is not under %s"
                                % (path, path.split("/", 1)[0], schema_id, NAMESPACE))
            else:
                out_of_scope.append({"path": path, "id": schema_id})
            continue
        try:
            family, version = identify(schema_id)
            normalized = normalize(value)
        except ShapeError as error:
            problems.append("%s %s" % (path, error))
            continue
        schemas.append({"path": path, "family": family, "id": schema_id, "version": version,
                        "sha256": digest(normalized), "normalized": normalized})
    for directory, _, files in os.walk(root / "schema"):
        for name in files:
            if not name.endswith(SUFFIX):
                problems.append("%s is in schema/ but is not a *%s file"
                                % ((Path(directory) / name).relative_to(root).as_posix(), SUFFIX))
    by_id: dict[str, str] = {}
    for entry in schemas:
        first = by_id.setdefault(entry["id"], entry["sha256"])
        if first != entry["sha256"]:
            problems.append("$id %s names two different shapes" % entry["id"])
    if problems:
        raise ShapeError("the schemas cannot be catalogued:\n  " + "\n  ".join(sorted(problems)))
    families: dict[str, list[str]] = {}
    for entry in schemas:
        families.setdefault(entry["family"], []).append(entry["path"])
    return {
        "format": CATALOG_FORMAT,
        "namespace": NAMESPACE,
        "normalization": NORMALIZATION,
        "families": {name: families[name] for name in sorted(families)},
        "schemas": schemas,
        "outOfScope": out_of_scope,
    }


def render(document: dict) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def read_json(path: Path, what: str) -> object:
    try:
        return parse(path.read_bytes())
    except OSError as error:
        raise ShapeError("%s cannot be read: %s" % (what, error.strerror)) from None
    except ShapeError as error:
        raise ShapeError("%s %s" % (what, error)) from None


# Change records -----------------------------------------------------------------------------------

def load_changes(root: Path) -> list[tuple[str, dict]]:
    directory = root / CHANGES
    if not directory.is_dir():
        raise ShapeError("%s/ is missing" % CHANGES)
    records, numbers = [], {}
    for name in sorted(os.listdir(directory)):
        match = RECORD_FILE.match(name)
        if not match:
            raise ShapeError("%s/%s is not NNNN-<slug>.json" % (CHANGES, name))
        if match.group(1) in numbers:
            raise ShapeError("%s/%s and %s share the number %s"
                             % (CHANGES, numbers[match.group(1)], name, match.group(1)))
        numbers[match.group(1)] = name
        record = read_json(directory / name, "%s/%s" % (CHANGES, name))
        _check_record(name, record)
        records.append((name, record))
    return records


def _check_record(name: str, record: object) -> None:
    where = "%s/%s" % (CHANGES, name)
    if not isinstance(record, dict) or set(record) != {"reason", "changes"}:
        raise ShapeError("%s must have exactly the members reason and changes" % where)
    if not isinstance(record["reason"], str) or not record["reason"].strip():
        raise ShapeError("%s gives no reason" % where)
    if not isinstance(record["changes"], list) or not record["changes"]:
        raise ShapeError("%s records no change" % where)
    seen = set()
    for change in record["changes"]:
        if not isinstance(change, dict) or set(change) != {"path", "family", "from", "to"}:
            raise ShapeError("%s: a change must have exactly path, family, from and to" % where)
        if not isinstance(change["path"], str) or not isinstance(change["family"], str):
            raise ShapeError("%s: path and family are strings" % where)
        if change["path"] in seen:
            raise ShapeError("%s changes %s twice" % (where, change["path"]))
        seen.add(change["path"])
        for member in ("from", "to"):
            if change[member] is not None and not (isinstance(change[member], str)
                                                   and DIGEST.match(change[member])):
                raise ShapeError("%s: %s of %s is not null or sha256:<hex>"
                                 % (where, member, change["path"]))
        if change["from"] == change["to"]:
            raise ShapeError("%s: %s changes from %s to the same digest"
                             % (where, change["path"], change["from"]))


def replay(records: list[tuple[str, dict]]) -> tuple[dict[str, dict], list[str]]:
    """Apply the change records in order; return the state they end at and the faults found."""
    state: dict[str, dict] = {}
    faults = []
    for name, record in records:
        where = "%s/%s" % (CHANGES, name)
        for change in record["changes"]:
            path, current = change["path"], state.get(change["path"])
            if change["from"] is None:
                if current is not None:
                    faults.append("%s adds %s, which the earlier records already hold at %s"
                                  % (where, path, current["sha256"]))
                    continue
            elif current is None:
                faults.append("%s changes %s from %s, but the earlier records do not hold it"
                              % (where, path, change["from"]))
                continue
            elif current["sha256"] != change["from"]:
                faults.append("%s changes %s from %s, but the earlier records end at %s"
                              % (where, path, change["from"], current["sha256"]))
                continue
            if change["to"] is None:
                if current["family"] != change["family"]:
                    faults.append("%s removes %s as family %s, but it is family %s"
                                  % (where, path, change["family"], current["family"]))
                    continue
                del state[path]
            else:
                state[path] = {"family": change["family"], "sha256": change["to"]}
    return state, faults


def pending(catalog: dict, state: dict[str, dict]) -> list[dict]:
    """The changes the tree has that the change records do not end at."""
    changes = []
    tree = {entry["path"]: entry for entry in catalog["schemas"]}
    for path in sorted(set(tree) | set(state)):
        entry, held = tree.get(path), state.get(path)
        if entry and held and entry["sha256"] == held["sha256"] and entry["family"] == held["family"]:
            continue
        changes.append({"path": path,
                        "family": entry["family"] if entry else held["family"],
                        "from": held["sha256"] if held else None,
                        "to": entry["sha256"] if entry else None})
    return changes


def check_changes(root: Path, catalog: dict) -> list[str]:
    state, faults = replay(load_changes(root))
    for change in pending(catalog, state):
        if change["to"] is None:
            faults.append("%s (family %s) was removed without a change record"
                          % (change["path"], change["family"]))
        elif change["from"] == change["to"]:
            faults.append("%s is family %s, but the change records hold it as another family"
                          % (change["path"], change["family"]))
        elif change["from"] is None:
            faults.append("%s (family %s) at %s has no change record"
                          % (change["path"], change["family"], change["to"]))
        else:
            faults.append("%s (family %s) is %s, but the change records end at %s: a change "
                          "record must name the old and new digests"
                          % (change["path"], change["family"], change["to"], change["from"]))
    return faults


# Releases and format status -----------------------------------------------------------------------

def load_releases(root: Path, catalog: dict) -> dict[str, dict]:
    """Read releases/: each release with its route, version, families and candidacy."""
    directory = root / RELEASES
    releases: dict[str, dict] = {}
    names = sorted(os.listdir(directory)) if directory.is_dir() else []
    for name in names:
        if name.endswith(".md"):
            tag = name[:-3]
            match = TAG.match(tag)
            if not match or not SEMVER.match(match.group(2)):
                raise ShapeError("%s/%s does not name a release tag" % (RELEASES, name))
            version = match.group(2)
            prerelease = SEMVER.match(version).group(4)
            releases[tag] = {"route": match.group(1) or "core", "version": version,
                             "specVersion": version if match.group(1) is None else None,
                             "candidate": bool(prerelease)
                             and prerelease.split(".")[0] in CANDIDATE_IDENTIFIERS,
                             "families": set()}
    by_path = {entry["path"]: entry for entry in catalog["schemas"]}
    by_id: dict[str, list[dict]] = {}
    for entry in catalog["schemas"]:
        by_id.setdefault(entry["id"], []).append(entry)
    for name in names:
        if not name.endswith(".json") or name.endswith(".milestone.json"):
            continue
        try:
            data = json.loads((directory / name).read_text("utf-8"))
        except (OSError, ValueError) as error:
            raise ShapeError("%s/%s cannot be read as JSON: %s" % (RELEASES, name, error)) from None
        if not isinstance(data, dict):
            raise ShapeError("%s/%s is not an object" % (RELEASES, name))
        tag = data.get("tag", data.get("distribution"))
        if tag not in releases:
            raise ShapeError("%s/%s names the release %r, which has no notes in %s/"
                             % (RELEASES, name, tag, RELEASES))
        if "specVersion" in data:
            releases[tag]["specVersion"] = data["specVersion"]
        named = []
        if isinstance(data.get("schema"), str):
            named.append(data["schema"])
        if isinstance(data.get("schemas"), dict):
            named.extend(value for value in data["schemas"].values() if isinstance(value, str))
        for reference in named:
            entries = [by_path[reference]] if reference in by_path else by_id.get(reference)
            if not entries:
                raise ShapeError("%s/%s names the schema %s, which the catalog does not hold"
                                 % (RELEASES, name, reference))
            releases[tag]["families"].update(entry["family"] for entry in entries)
    for release in releases.values():
        if release["route"] == "core":
            # A Core release publishes the schemas whose `$id` names its specVersion.
            prefix = NAMESPACE + str(release["specVersion"]) + "/"
            release["families"].update(entry["family"] for entry in catalog["schemas"]
                                       if entry["id"].startswith(prefix))
            # A Core distribution whose tag is not its specVersion is a candidate.
            if release["specVersion"] != release["version"]:
                release["candidate"] = True
    return releases


def derive_status(root: Path, catalog: dict) -> dict[str, dict]:
    releases = load_releases(root, catalog)
    status = {}
    for family, paths in catalog["families"].items():
        entries = [entry for entry in catalog["schemas"] if entry["family"] == family]
        including = [tag for tag, release in releases.items() if family in release["families"]]
        routes = {releases[tag]["route"] for tag in including}
        if len(routes) > 1:
            raise ShapeError("family %s is released on more than one route: %s"
                             % (family, sorted(routes)))
        order = lambda tag: version_key(releases[tag]["version"])  # noqa: E731
        baselines = [tag for tag in including if not releases[tag]["candidate"]]
        status[family] = {
            "draftVersion": latest([entry["version"] for entry in entries]),
            "baseline": max(baselines, key=order) if baselines else None,
            "lastReleased": max(including, key=order) if including else None,
        }
    return status


def check_status(root: Path, catalog: dict) -> list[str]:
    recorded = read_json(root / STATUS, STATUS)
    if not isinstance(recorded, dict) or set(recorded) != {"format", "families"}:
        return ["%s must have exactly the members format and families" % STATUS]
    if recorded["format"] != STATUS_FORMAT:
        return ["%s format is %r, not %r" % (STATUS, recorded["format"], STATUS_FORMAT)]
    if not isinstance(recorded["families"], dict):
        return ["%s families is not an object" % STATUS]
    derived = derive_status(root, catalog)
    faults = []
    for family in sorted(set(recorded["families"]) | set(derived)):
        if family not in derived:
            faults.append("%s records the family %s, which the catalog does not have" % (STATUS, family))
        elif family not in recorded["families"]:
            faults.append("%s has no record for the family %s; derived: %s"
                          % (STATUS, family, json.dumps(derived[family], sort_keys=True)))
        elif recorded["families"][family] != derived[family]:
            faults.append("%s family %s is %s; the tree and %s/ give %s"
                          % (STATUS, family, json.dumps(recorded["families"][family], sort_keys=True),
                             RELEASES, json.dumps(derived[family], sort_keys=True)))
    return faults


# Commands -----------------------------------------------------------------------------------------

def check(root: Path = ROOT) -> list[str]:
    catalog = build_catalog(root)
    faults = []
    try:
        committed = (root / CATALOG).read_text("utf-8")
    except OSError:
        committed = None
    if committed != render(catalog):
        faults.append("%s is not the catalog the tree gives: run tools/record_shapes.py generate"
                      % CATALOG)
    faults.extend(check_changes(root, catalog))
    faults.extend(check_status(root, catalog))
    return faults


def write_record(root: Path, slug: str, reason: str) -> Path:
    if not NAME.match(slug):
        raise ShapeError("the slug %r is not lowercase words and hyphens" % slug)
    if not reason.strip():
        raise ShapeError("a change record needs a reason")
    catalog = build_catalog(root)
    records = load_changes(root)
    state, faults = replay(records)
    if faults:
        raise ShapeError("the change records do not replay:\n  " + "\n  ".join(faults))
    changes = pending(catalog, state)
    if not changes:
        raise ShapeError("no schema differs from the change records")
    number = max((int(RECORD_FILE.match(name).group(1)) for name, _ in records), default=-1) + 1
    path = root / CHANGES / ("%04d-%s.json" % (number, slug))
    path.write_text(render({"reason": reason, "changes": changes}), "utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("generate")
    commands.add_parser("check")
    record = commands.add_parser("record")
    record.add_argument("--slug", required=True)
    record.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "generate":
            (root / CATALOG).parent.mkdir(parents=True, exist_ok=True)
            (root / CATALOG).write_text(render(build_catalog(root)), "utf-8")
            print("record-shapes: wrote %s" % CATALOG)
        elif args.command == "record":
            print("record-shapes: wrote %s" % write_record(root, args.slug, args.reason).relative_to(root))
        else:
            faults = check(root)
            for fault in faults:
                print("record-shapes: FAIL " + fault, file=sys.stderr)
            if faults:
                return 1
            print("record-shapes: PASS (catalog, change records and format status agree with the "
                  "tree and %s/)" % RELEASES)
    except ShapeError as error:
        print("record-shapes: FAIL %s" % error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

# RFC 0036: The registry emitter contract and its conformance harness

- Status: Draft
- Type: Standards track, part of the proposed registry companion (`spec/registry.md`) of
  [RFC 0034](0034-registry-profile.md), intended for stable maturity with it
- Created: 2026-11-16
- Issue: [#339](https://github.com/Judgment-Pack/judgment-pack-spec/issues/339) (the registry line)
- Related: RFC 0034 (the registry profile and resolved documents), RFC 0035 (references)

> This RFC, a Draft, is normative for nothing. Core is untouched.

## Summary

An **emitter** turns resolved registries (RFC 0034 §5) into files a repository commits or deploys:
- a typed start-up loader;
- constants for a frontend;
- infrastructure variables;
- database bootstrap inputs;
- caller lists.

JPS does not write the target-specific ones. An adopting repository writes its own, and JPS
standardizes how every emitter is run and checked.

- **An emitter is a pure function from one request document to one file set.** It reads a JSON
  request on standard input and writes a JSON response on standard output. It does not open,
  write or delete files itself.
- **The host (`jpack emit`) does all filesystem work.** It forms the request, runs the emitter
  under bounds, refuses unsafe paths, writes the files into the paths the emitter declares it
  owns, and in `--check` mode compares instead of writing. Its exit codes are 0 for "the files are
  current", 1 for "they differ", and 2 for "could not check".
- **An emitter manifest** names the emitter, its version, the kinds it reads, its options schema,
  the command that runs it, and the paths it owns.
- **The conformance harness** (`jpack emit conformance`) runs any emitter against its author's
  golden vectors and against checks the harness supplies:
  - determinism under perturbed environments;
  - path safety;
  - kind filtering;
  - references passed through untouched;
  - bounded output.

  A repository can run it in its own CI on its own emitters.
- **Reference emitters** that JPS ships are the generic ones: a Go typed loader and TypeScript
  constants. Their output is not under the 1.0 promise. The contract and the harness are.

## Problem

1. **Generators are the least checked code in a platform repository.** They are hand-written,
   read authoring files directly, re-implement defaults and overlays, write wherever they like,
   and are "checked" by re-running them and diffing.
2. **Non-reproducible output breaks review.** Timestamps, map order, the locale and absolute paths
   all leak into generated files, so a `-check` step fails on machines that changed nothing.
3. **Each generator re-invents check mode.** Some forget stale files: a file that is no longer
   generated stays committed.
4. **A shared generator cannot know every target.** Database bootstrap inputs, infrastructure
   layouts and caller lists are specific to one organization. A standard that tried to ship them
   would need a release for every new target.

## Evidence

- The adopting organization behind RFC 0034 maintains emitters for a Go loader, TypeScript
  constants, infrastructure environment and IAM files, database bootstrap inputs and caller lists,
  each with a `-check` mode in CI. The first two are generic. The rest are tied to its own
  infrastructure, which is why they stay in its repository under this design.
- Pure-function code generation over a canonical input (for example protocol buffer compiler
  plugins: a request on standard input, a list of files on standard output) is an established
  pattern with many independent implementations. It is what makes plugins language-neutral and
  hosts able to control writes.

## Specification

### 1. The emitter manifest

```json
{
  "emitterManifestVersion": "1.0.0",
  "id": "https://example.invalid/emitters/db-bootstrap",
  "version": "2.1.0",
  "owner": "platform-data",
  "reads": [
    { "kind": "db-role", "id": "https://example.invalid/kinds/db-role", "versions": "^1.2.0" },
    { "kind": "database", "id": "https://example.invalid/kinds/database", "versions": "^1.0.0" }
  ],
  "environments": "each",
  "options": { "type": "object", "additionalProperties": false,
               "properties": { "schemaName": { "type": "string" } } },
  "command": ["go", "run", "./tools/emit-db-bootstrap"],
  "owns": ["deploy/db/generated/**"]
}
```

**Manifest members.**

- **`reads`**: the kinds the emitter reads, by kind id and a SemVer range. The range syntax is
  `^x.y.z`, `~x.y.z`, `=x.y.z`, or a space-separated pair `>=a <b`.
- **`environments`**: either `"each"` (one request per environment) or `"all"` (one request
  holding every environment's resolved document).
- **`options`**: a schema in RFC 0034's subset, for the emitter's options document.
- **`command`**: an argv the host runs from the repository root. It is not a shell string.
- **`owns`**: glob patterns, relative to the repository root, that name every path the emitter
  writes. The globs use `*` (one segment), `**` (any number of segments) and literal characters
  only.

**Rules.**
- The globs of two manifests in one repository MUST NOT overlap. The host refuses to run either
  if they do.
- Neither `command` nor `owns` may name a path outside the repository root.

### 2. The request

```json
{
  "emitRequestVersion": "1.0.0",
  "emitter": { "id": "https://example.invalid/emitters/db-bootstrap", "version": "2.1.0" },
  "options": { "schemaName": "app" },
  "resolved": [ { "resolvedFormatVersion": "1.0.0", "environment": "prod", "...": "..." } ]
}
```

The host forms the request as follows:
1. It resolves the registry for each environment (RFC 0034 §5).
2. It removes every entry whose kind the manifest does not read, and every pinned kind the
   manifest does not read. The emitter never sees what it did not declare.
3. It checks each remaining kind's pinned version against the manifest's range.
4. It validates `options` against the manifest's schema.
5. It writes the request in its RFC 8785 canonical form.

`resolved` holds one document for `"each"`, or every environment in the registry's order for
`"all"`. A kind outside a range refuses the run (`EMIT-KIND-RANGE`) before the emitter starts.

### 3. The response

```json
{
  "emitResponseVersion": "1.0.0",
  "files": [
    { "path": "deploy/db/generated/prod/roles.sql", "text": "-- generated …\nCREATE ROLE …\n" },
    { "path": "deploy/db/generated/prod/roles.json", "text": "{…}\n" }
  ],
  "diagnostics": [ { "severity": "warning", "code": "x-db-unused-role", "location": { "kind": "db-role", "id": "billing-backfill" } } ]
}
```

**What the emitter writes.**

- **One response on standard output**, then exit 0. A non-zero exit, or output that is not one
  valid response, is an emitter failure (`EMIT-PROCESS`, `EMIT-RESPONSE`).
- **Standard error is passed through to the caller's standard error**, truncated at 64 KiB.

**Each file** carries a `path` and exactly one of these:
- `text`: UTF-8 that ends with a line feed and contains no carriage return;
- `base64`: bytes, for non-text output.

An optional `mode` is `"0644"` (the default) or `"0755"`. No other mode exists.

**Path rules.**
- A path uses `/` separators.
- It is relative, and has no `.` or `..` segment, no empty segment, and no segment that begins
  with `~`.
- It does not end with `/`.
- It contains no NUL, backslash or control character.
- It MUST match one of the manifest's `owns` globs.
- Paths are unique once case is folded, so that a case-insensitive filesystem cannot merge two
  of them.
- The `files` array is sorted by path, in code-point order.

**Emitter diagnostics.** Codes begin with `x-`. A diagnostic carries a location of the
RFC 0034 §6 kind and MUST NOT carry a value. An `error` diagnostic makes the run fail after the
response is read, and nothing is written.

**Bounds.**

| Limit | Value |
|---|---|
| Response size | 64 MiB |
| Files | 10 000 |
| Bytes per file | 16 MiB |
| Path length | 512 bytes |

### 4. The host: `jpack emit`

```
jpack emit --manifest tools/emit-db-bootstrap/emitter.json --registry registry.json \
           --kinds kinds/ [--options options.json] [--check]
```

**Running the emitter:**
- **Environment.** The host runs `command` with an environment that holds only `PATH`, `HOME`
  (set to a fresh empty directory) and `LANG=C.UTF-8`, plus the variables the manifest lists in
  an optional `env` array (names only; values come from the caller's environment).
- **Working directory and input.** The working directory is the repository root, and standard
  input is the request.
- **Time limit.** The host imposes a wall-clock limit, 120 s by default and set by `--timeout`.
  Some platforms cannot isolate a process from the network or the filesystem portably, and the
  host does not claim to. The harness tests what can be tested (§5).

**Write mode:**
1. The host validates the response completely before it changes anything.
2. It writes every file through a temporary file, then renames it into place.
3. It deletes every file that matches the manifest's `owns` globs but is not in the response (a
   stale file).
4. It never follows a symbolic link at or above an owned path. A link there refuses the run.
5. It reports the set of files written and deleted.

**Check mode (`--check`):**
- The host compares the response with the files on disk under the owned globs, byte for byte and
  mode for mode, and writes nothing.
- **Exit 0**: identical.
- **Exit 1**: they differ. Each missing, changed, extra (stale) or mode-changed path is listed,
  without file contents.
- **Exit 2**: could not check: an emitter failure, a refused request or response, or an
  unreadable path.

**In write mode**, exit 0 means written and exit 2 means not written. A command line that cannot
be parsed exits 3, as every jpack command does, and a CI step treats 2 and 3 alike.

**Determinism.** An emitter MUST produce the same response bytes for the same request bytes:
- no clock;
- no randomness;
- no host name;
- no absolute path;
- no dependence on map iteration order, the locale, the time zone or the environment beyond
  declared `env`;
- no network.

A generated-file header, if an emitter writes one, carries at most the emitter id and version and
`registry.digest` from the request, never a time.

### 5. The conformance harness: `jpack emit conformance`

```
jpack emit conformance --manifest emitter.json --vectors tools/emit-db-bootstrap/vectors/
```

**Vectors** are the emitter author's goldens. Each one is a directory holding:
- `request.json`, or `registry.json` with `kinds/` and an optional `options.json`, from which the
  harness forms the request as `jpack emit` does;
- `expected/`, holding exactly the files the response must contain;
- or `expected-failure.json`, which names the failure code the run must produce instead.

`--update` rewrites `expected/` from the current emitter, for the author to review.

**Checks the harness adds to every vector:**
1. **Golden equality.** The response's files equal `expected/`, byte for byte and mode for mode.
2. **Determinism.** The emitter is run three times, with:
   - a different `HOME`;
   - `TZ` set to two different zones;
   - `LANG` set to two different locales;
   - `SOURCE_DATE_EPOCH` set to two different values.

   The three responses MUST be identical bytes. Variables the manifest declares in `env` are
   held fixed.
3. **Path safety and bounds.** Every rule of §3. The harness also ships hostile vectors, in which
   it substitutes a crafted response for the emitter's, to confirm the host refuses each one.
4. **Kind filtering.** The request never contains an undeclared kind. The harness adds an entry of
   a synthetic undeclared kind to each vector's registry and checks that the response is unchanged.
5. **References.** Every string at a secret position in the request must appear unchanged in the
   output, or not at all, and never partially. Reference text is the only secret-adjacent material
   an emitter sees, and RFC 0035 forbids anything resolving it.
6. **No stray writes.** On platforms where it can, the harness runs the emitter in a fresh
   temporary copy of the repository and reports any file the emitter created or changed itself
   (`EMIT-STRAY-WRITE`).

**The harness report** uses `harnessReportVersion` `"1.0.0"` and has one row per vector and per
check, with pass, fail or skip (and the reason for a skip). The harness exits 0 when every row
passes, 1 when a check fails, and 2 when it could not run.

### 6. Reference emitters

JPS ships two generic emitters, each with its own manifest, version and golden vectors, run by the
same harness:
1. **A Go typed loader.** For each kind it reads, it generates a Go type from the kind's schema
   subset, and a loader that reads one resolved document through the start-up package
   (`github.com/Judgment-Pack/judgment-pack-runtime/startup`). Members at secret positions get the
   start-up package's secret type.
2. **TypeScript constants.** It generates a read-only constant object and types for each kind it
   reads, with every member at a secret position omitted.

A Terraform-variables emitter is under consideration (Unresolved question 2).

**What is promised for these emitters:** each version of a reference emitter promises its
manifest, the kinds it reads and its options, not the exact bytes it writes. A new minor version
may change formatting, and the adopter's `--check` shows it.

### 7. What the 1.0 promise covers

The stable promise of the registry companion (RFC 0034 §8) covers:
- the manifest, request, response and harness-report formats;
- the host's behaviour and exit codes;
- the harness's checks.

Checks may be added, and a new one starts as a warning for one minor version before it can fail
a vector. The promise does not cover any emitter's output.

## Alternatives

- **JPS ships every emitter.** This was rejected (RFC 0034, Alternatives): target-specific output
  would need a JPS release per target, and would encode one organization's infrastructure.
- **Emitters write files themselves**, with the host only diffing. This is simpler for authors,
  but the host could no longer refuse an unsafe path, catch stray writes, or make check mode
  uniform, and stale-file handling would be re-invented in every emitter.
- **In-process plugins** (Go plugins, WASM). Go plugins are platform-limited. WASM would allow
  real sandboxing and is a candidate for a later minor version as an optional `runtime: "wasm"`
  (Unresolved question 1). The process contract is the language-neutral baseline.
- **Templates instead of programs.** Templates handle the simple cases and push the rest into
  template-language logic, and two template engines rarely agree byte for byte.

## Compatibility

The formats are new. An adopter's existing generators migrate one at a time: wrap the generator to
read a request and print a response, declare `owns`, run the harness, then drop its own file
writing and check mode.

## Security and privacy

- **Secrets.** Secret values never reach an emitter. The request carries only reference strings,
  and the harness checks that they pass through unchanged. An emitter that wanted a value would
  have to fetch it, which the determinism checks and the environment scrubbing are designed to
  frustrate. This is not a sandbox, and the RFC does not call it one.
- **Path traversal and clobbering.** This is closed by the host: a relative safe path, owned globs,
  case-fold uniqueness, no symbolic links at or above an owned path, and atomic renames.
- **Resource use.** Output size, file count and time are bounded.
- **Supply chain.** An emitter is code the repository chose to run, and `jpack emit` runs only the
  command its manifest names, from the repository. The contract does not make running someone
  else's emitter safe.
- **Disclosure.** Check-mode and harness output never prints file contents, only paths and codes.

## Conformance

For the host, the vectors cover:
- every path rule, including case-fold collisions, NUL, `..`, absolute paths, Windows drive
  letters and UNC forms;
- bounds at their limit and one past;
- stale-file deletion;
- a symbolic link at and above an owned path;
- overlapping `owns`;
- a kind range miss;
- options failing their schema;
- emitter exit codes, malformed responses, and oversized standard error;
- check mode's four kinds of difference.

For the harness, each check has a passing emitter and a failing one, including emitters that:
- read the clock;
- iterate a map;
- honour `TZ`;
- write a stray file;
- echo part of a secret reference;
- include an undeclared kind's data when the host is bypassed in a test.

## Implementation

1. **The reference runtime:** `jpack emit` and `jpack emit conformance` in Go, plus the two
   reference emitters.
2. **A second host** in this repository's Python reader of RFC 0034, implementing §§2–4 and the
   harness's checks 1–5. It is enough to show two hosts agree on every host vector and on the
   reference emitters' goldens.

The adopting organization's own emitters are the first third-party users of the harness.

## Unresolved questions

1. **A WASM runtime option** for real isolation, and whether the harness should require it for
   emitters that are shared between organizations.
2. **Whether a Terraform-variables emitter is generic enough** to be a reference emitter, or always
   adopter-specific. Its natural form is a `.tfvars.json` per environment from declared kinds.
3. **Range syntax.** Is a SemVer range on kind versions enough, or should a manifest pin exact
   kind digests, trading upgrades for certainty?
4. **Review regime:** as in RFC 0034, question 1.

// Turning one staged vector directory into a verifier's inputs, as conformance/dialect/README.md lists
// them: mapping.json, case.json, sources.json (`{}` when absent), profiles.json, and from run.json the
// preparation `run.input.preparation` and the record (`run.auditBytes` in standard base64, or else
// `run.audit` as the export writes it). A vector of a dialect bound at import holds binding.json: its
// dialect is then unbound.json, given with binding.json, and mapping.json is the bound dialect (§4.4).
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { NotRead, member, read, utf8 } from "./json.ts";
import { validates } from "./schema.ts";
import type { JVal } from "./json.ts";
import type { Inputs } from "./verify.ts";

export class VectorError extends Error {}

export type Recording = {
  evaluatorSpecVersion: "0.2.0-draft" | "0.3.0";
  schema: string;
  pack: Uint8Array;
  record: Uint8Array;
};

const RECORDING_SCHEMAS = new Map([
  ["0.2.0-draft", "schema/judgment-pack-core-0.2.0-draft.schema.json"],
  ["0.3.0", "schema/judgment-pack-core.schema.json"],
] as const);

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const SCHEMAS = new Map<string, unknown>();

const validateRecordingPack = (schemaPath: string, packText: string): void => {
  let schema = SCHEMAS.get(schemaPath);
  if (schema === undefined) {
    schema = JSON.parse(readFileSync(join(ROOT, schemaPath), "utf8"));
    SCHEMAS.set(schemaPath, schema);
  }
  if (!validates(schema, JSON.parse(packText))) throw new VectorError("recording-pack-invalid");
};

export function recordingSchema(version: string): string {
  const schema = RECORDING_SCHEMAS.get(version as "0.2.0-draft" | "0.3.0");
  if (schema === undefined) throw new VectorError("recording-version-unsupported");
  return schema;
}

const stringMember = (value: JVal | undefined, name: string, what: string): string => {
  const found = member(value, name);
  if (found?.t !== "str") throw new VectorError(`${what}.${name} is not a string`);
  return found.v;
};

const auditVersion = (audit: JVal | undefined, what: string): [string, string] => [
  stringMember(audit, "evaluatorSpecVersion", what),
  stringMember(member(audit, "pack"), "specVersion", `${what}.pack`),
];

/** A complete Runner recording, with every copy of its Core version held together. */
export function recordingOfExport(bytes: Uint8Array): Recording {
  let document: ReturnType<typeof read>;
  try {
    document = read(bytes);
  } catch (e) {
    if (e instanceof NotRead) throw new VectorError(`run.json is not one JSON value: ${e.message}`);
    throw e;
  }
  const release = member(document.value, "release");
  const run = member(document.value, "run");
  const result = member(run, "result");
  const visible = member(run, "audit");
  if (release?.t !== "obj" || run?.t !== "obj" || result?.t !== "obj" || visible?.t !== "obj") {
    throw new VectorError("run.json has no release, run, recorded result, or visible audit object");
  }

  const evaluatorSpecVersion = stringMember(result, "evaluatorSpecVersion", "run.result");
  const schema = recordingSchema(evaluatorSpecVersion);

  const auditBytes = member(run, "auditBytes");
  let record: Uint8Array;
  if (auditBytes !== undefined) {
    if (auditBytes.t !== "str" || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(auditBytes.v)) {
      throw new VectorError("run.auditBytes is not standard base64");
    }
    record = Uint8Array.from(Buffer.from(auditBytes.v, "base64"));
  } else {
    const audit = member(run, "audit");
    if (audit === undefined) throw new VectorError("run.json has no audit record");
    record = utf8(document.text.slice(audit.s, audit.e));
  }
  let decoded: JVal;
  try {
    decoded = read(record).value;
  } catch (e) {
    if (e instanceof NotRead) throw new VectorError(`run.auditBytes is not one JSON value: ${e.message}`);
    throw e;
  }
  const packText = stringMember(release, "pack", "release");
  let packValue: JVal;
  try {
    packValue = read(utf8(packText)).value;
  } catch (e) {
    if (e instanceof NotRead) throw new VectorError(`release.pack is not one JSON value: ${e.message}`);
    throw e;
  }
  const [visibleEvaluator, visiblePack] = auditVersion(visible, "run.audit");
  const [decodedEvaluator, decodedPack] = auditVersion(decoded, "the decoded audit");
  const versions = [
    stringMember(packValue, "specVersion", "release.pack"),
    visibleEvaluator,
    visiblePack,
    decodedEvaluator,
    decodedPack,
  ];
  if (versions.some((version) => version !== evaluatorSpecVersion)) {
    throw new VectorError("recording-version-mismatch");
  }
  validateRecordingPack(schema, packText);
  return {
    evaluatorSpecVersion: evaluatorSpecVersion as "0.2.0-draft" | "0.3.0",
    schema,
    pack: utf8(packText),
    record,
  };
}

export function loadVector(dir: string, requireBinding: boolean): Inputs {
  const file = (name: string) => Uint8Array.from(readFileSync(join(dir, name)));
  const sources = join(dir, "sources.json");
  const runBytes = file("run.json");
  let run: ReturnType<typeof read>;
  try {
    run = read(runBytes);
  } catch (e) {
    if (e instanceof NotRead) throw new VectorError(`run.json is not one JSON value: ${e.message}`);
    throw e;
  }
  const runRun = member(run.value, "run");
  const preparation = member(member(runRun, "input"), "preparation");
  if (preparation === undefined) throw new VectorError("run.json has no run.input.preparation");
  const slice = (v: { s: number; e: number }) => utf8(run.text.slice(v.s, v.e));
  let record: Uint8Array | undefined;
  if (member(run.value, "release") !== undefined) {
    record = recordingOfExport(runBytes).record;
  } else {
    const auditBytes = member(runRun, "auditBytes");
    const audit = member(runRun, "audit");
    if (auditBytes !== undefined) {
      if (auditBytes.t !== "str" || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(auditBytes.v)) {
        throw new VectorError("run.auditBytes is not standard base64");
      }
      record = Uint8Array.from(Buffer.from(auditBytes.v, "base64"));
    } else if (audit !== undefined) {
      record = slice(audit);
    }
  }
  const imported = existsSync(join(dir, "binding.json"));
  return {
    dialect: file(imported ? "unbound.json" : "mapping.json"),
    binding: imported ? file("binding.json") : undefined,
    case: file("case.json"),
    acquisitions: existsSync(sources) ? file("sources.json") : utf8("{}"),
    profiles: file("profiles.json"),
    preparation: slice(preparation),
    record,
    requireBinding,
  };
}

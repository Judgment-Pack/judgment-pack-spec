// Turning one staged vector directory into a verifier's inputs, as conformance/dialect/README.md lists
// them: mapping.json, case.json, sources.json (`{}` when absent), profiles.json, and from run.json the
// preparation `run.input.preparation` and the record (`run.auditBytes` in standard base64, or else
// `run.audit` as the export writes it).
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { NotRead, member, read, utf8 } from "./json.ts";
import type { Inputs } from "./verify.ts";

export class VectorError extends Error {}

export function loadVector(dir: string, requireBinding: boolean): Inputs {
  const file = (name: string) => Uint8Array.from(readFileSync(join(dir, name)));
  const sources = join(dir, "sources.json");
  let run: ReturnType<typeof read>;
  try {
    run = read(file("run.json"));
  } catch (e) {
    if (e instanceof NotRead) throw new VectorError(`run.json is not one JSON value: ${e.message}`);
    throw e;
  }
  const runRun = member(run.value, "run");
  const preparation = member(member(runRun, "input"), "preparation");
  if (preparation === undefined) throw new VectorError("run.json has no run.input.preparation");
  const slice = (v: { s: number; e: number }) => utf8(run.text.slice(v.s, v.e));
  let record: Uint8Array | undefined;
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
  return {
    dialect: file("mapping.json"),
    case: file("case.json"),
    acquisitions: existsSync(sources) ? file("sources.json") : utf8("{}"),
    profiles: file("profiles.json"),
    preparation: slice(preparation),
    record,
    requireBinding,
  };
}

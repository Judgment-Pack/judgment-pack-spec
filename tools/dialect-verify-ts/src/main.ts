// The command line: one reading of one preparation, its report printed as one line of JSON.
//
//   node src/main.ts <vector directory> [--require-binding]
//   node src/main.ts --dialect F --case F [--acquisitions F] --profiles F --preparation F [--record F] [--require-binding]
//
// Options for either form: --emit-preparation F writes the recomputed preparation's canonical bytes (§9.5),
// when recomputation completed; --explain writes the reason for a refusal or a finding to standard error.
// Exit status: 0 a reading, 1 a refusal, 2 a finding, 3 the program could not run (arguments, files).
import { readFileSync, writeFileSync } from "node:fs";
import { preparationForm, utf8 } from "./json.ts";
import { VectorError, loadVector } from "./vector.ts";
import { verify } from "./verify.ts";
import type { Inputs } from "./verify.ts";

const USAGE =
  "usage: node src/main.ts <vector directory> [--require-binding] [--emit-preparation F] [--explain]\n" +
  "       node src/main.ts --dialect F --case F [--acquisitions F] --profiles F --preparation F [--record F]\n" +
  "                        [--require-binding] [--emit-preparation F] [--explain]\n";

function main(argv: string[]): number {
  const flags = new Set<string>();
  const values = new Map<string, string>();
  const positional: string[] = [];
  const valued = new Set(["--dialect", "--case", "--acquisitions", "--profiles", "--preparation", "--record", "--emit-preparation"]);
  for (let k = 0; k < argv.length; k++) {
    const a = argv[k];
    if (valued.has(a)) {
      if (k + 1 >= argv.length || values.has(a)) return usage(`${a} needs one value`);
      values.set(a, argv[++k]);
    } else if (a === "--require-binding" || a === "--explain") {
      flags.add(a);
    } else if (a.startsWith("--")) {
      return usage(`unknown option ${a}`);
    } else {
      positional.push(a);
    }
  }
  const requireBinding = flags.has("--require-binding");
  let inputs: Inputs;
  try {
    if (positional.length === 1) {
      for (const k of ["--dialect", "--case", "--acquisitions", "--profiles", "--preparation", "--record"]) {
        if (values.has(k)) return usage(`${k} is not taken with a vector directory`);
      }
      inputs = loadVector(positional[0], requireBinding);
    } else if (positional.length === 0) {
      for (const k of ["--dialect", "--case", "--profiles", "--preparation"]) if (!values.has(k)) return usage(`${k} is required`);
      const file = (k: string) => Uint8Array.from(readFileSync(values.get(k)!));
      let record: Uint8Array | undefined;
      if (values.has("--record")) {
        record = file("--record");
        if (record.length > 0 && record[record.length - 1] === 0x0a) record = record.subarray(0, record.length - 1);
      }
      inputs = {
        dialect: file("--dialect"),
        case: file("--case"),
        acquisitions: values.has("--acquisitions") ? file("--acquisitions") : utf8("{}"),
        profiles: file("--profiles"),
        preparation: file("--preparation"),
        record,
        requireBinding,
      };
    } else {
      return usage("one vector directory at most");
    }
  } catch (e) {
    if (e instanceof VectorError || (e as { code?: string }).code !== undefined) {
      process.stderr.write(`dialect-verify-ts: ${(e as Error).message}\n`);
      return 3;
    }
    throw e;
  }
  const result = verify(inputs);
  // The file it was asked to write comes before the report: a program that cannot write it could not run,
  // and exits 3 having written no report (§11, the report).
  if (values.has("--emit-preparation") && result.recomputed !== undefined) {
    try {
      writeFileSync(values.get("--emit-preparation")!, result.recomputed);
    } catch (e) {
      process.stderr.write(`dialect-verify-ts: could not write the preparation: ${(e as Error).message}\n`);
      return 3;
    }
  }
  process.stdout.write(Buffer.from(preparationForm(result.report)).toString("utf8") + "\n");
  if (flags.has("--explain") && result.why !== undefined) process.stderr.write(`dialect-verify-ts: ${result.why}\n`);
  return result.kind === "reading" ? 0 : result.kind === "refusal" ? 1 : 2;
}

function usage(why: string): number {
  process.stderr.write(`dialect-verify-ts: ${why}\n${USAGE}`);
  return 3;
}

try {
  process.exitCode = main(process.argv.slice(2));
} catch (e) {
  // never exit 1 or 2 on a fault of this program: those statuses are the class's answers
  process.stderr.write(`dialect-verify-ts: could not run: ${(e as Error).stack ?? e}\n`);
  process.exitCode = 3;
}

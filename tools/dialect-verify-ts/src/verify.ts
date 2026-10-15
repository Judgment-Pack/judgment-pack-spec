// A preparation verifier (spec/dialect.md §11, §14): the refusals in their phases, the findings in their
// order, and the reading.
import { BOUNDS, scanBytes } from "./bounds.ts";
import { Refusal, countsWithin, readAcquisitions, readBound, readDialect, readProfiles, readRecord, readVerifiedAt, researchSources, sha256hex } from "./forms.ts";
import { NotRead, OutsideDomain, arr, compareCodePoints, intValue, isInteger, jsonEqual, member, num, obj, preparationForm, read, str, utf8 } from "./json.ts";
import type { JObj, JVal } from "./json.ts";
import { Finding, conditionParameters, recompute } from "./prepare.ts";
import type { Outcome, Recomputed } from "./prepare.ts";

export type Inputs = {
  dialect: Uint8Array;
  case: Uint8Array;
  acquisitions: Uint8Array; // `{}` when there are none
  profiles: Uint8Array;
  preparation: Uint8Array;
  record?: Uint8Array; // the line, without its newline
  requireBinding: boolean;
  binding?: Uint8Array; // the binding document of a dialect with an unbound source (§4.4)
};

// §2: the dialect versions the text defines, and those this verifier reads: both (§11, `version-unread`).
const DEFINED_VERSIONS = ["2", "3"];
const READ_VERSIONS = ["2", "3"];

export type Result = {
  kind: "reading" | "finding" | "refusal";
  report: JObj;
  why?: string;
  recomputed?: Uint8Array; // the recomputed preparation's canonical bytes (§9.5), when recomputation completed
};

export const BINDING_KIND = "judgment-pack-runner/preparation/1";

export function verify(inputs: Inputs): Result {
  let recomputedBytes: Uint8Array | undefined;
  try {
    return reading(inputs, (b) => (recomputedBytes = b));
  } catch (e) {
    if (e instanceof Refusal) return { kind: "refusal", report: obj([["result", str("refusal")], ["refusal", str(e.code)]]), why: e.message };
    if (e instanceof Finding) {
      return { kind: "finding", report: obj([["result", str("finding")], ["finding", str(e.code)]]), why: e.message, recomputed: recomputedBytes };
    }
    throw e;
  }
}

function reading(inputs: Inputs, keep: (b: Uint8Array) => void): Result {
  const over = (why: string): never => {
    throw new Refusal("input-over-bound", why);
  };
  const docs: [string, Uint8Array | undefined][] = [
    ["the dialect", inputs.dialect],
    ["the case", inputs.case],
    ["the acquisitions", inputs.acquisitions],
    ["the profiles", inputs.profiles],
    ["the preparation", inputs.preparation],
    ["the record", inputs.record],
    ["the binding document", inputs.binding],
  ];

  // phase 1: the bounds measured on bytes, on every document before any is read
  if (inputs.dialect.length > BOUNDS.dialectBytes) over("the dialect's size");
  if (inputs.dialect.length + inputs.case.length + inputs.acquisitions.length > BOUNDS.inputBytes) over("the inputs' size");
  if (inputs.profiles.length > BOUNDS.profilesBytes) over("the profiles' size");
  if (inputs.preparation.length > BOUNDS.preparationBytes) over("the preparation's size");
  if (inputs.record !== undefined && inputs.record.length > BOUNDS.recordBytes) over("the record's size");
  if (inputs.binding !== undefined && inputs.binding.length > BOUNDS.bindingBytes) over("the binding document's size");
  for (const [what, bytes] of docs) {
    if (bytes === undefined) continue;
    const scan = scanBytes(bytes);
    const limit = what === "the case" ? BOUNDS.readNesting : BOUNDS.documentNesting;
    if (scan.nesting > limit) over(`${what}'s nesting`);
    if (!scan.numbersWithin) over(`a number literal of ${what}`);
  }

  // phase 2: every document read as §1 reads one, and the record as one line
  if (inputs.record !== undefined && inputs.record.some((c) => c === 0x0a || c === 0x0d)) {
    throw new Refusal("input-malformed", "the record is not one line");
  }
  const parsed = new Map<string, { text: string; value: JVal }>();
  for (const [what, bytes] of docs) {
    if (bytes === undefined) continue;
    try {
      parsed.set(what, read(bytes));
    } catch (e) {
      if (e instanceof NotRead) throw new Refusal("input-malformed", `${what}: ${e.message}`);
      throw e;
    }
  }
  const dialectValue = parsed.get("the dialect")!.value;
  const caseValue = parsed.get("the case")!.value;
  const acquisitionsValue = parsed.get("the acquisitions")!.value;
  const preparationValue = parsed.get("the preparation")!.value;
  const record = parsed.get("the record");

  // phase 3: the counts
  if (!countsWithin(dialectValue, acquisitionsValue)) over("a count of the dialect or the nesting of a result");

  // phase 4: a version this verifier does not read. It reads both the text defines, 2 and 3.
  const version = member(dialectValue, "version");
  if (dialectValue.t === "obj" && isInteger(version)) {
    const v = String(intValue(version));
    if (DEFINED_VERSIONS.includes(v) && !READ_VERSIONS.includes(v)) throw new Refusal("version-unread", `dialect version ${v} is not read by this verifier`);
  }

  // phase 5: every document's form; a dialect with an unbound source is read with its binding document, as the
  // bound dialect (§4.4)
  const dialect = readBound(readDialect(dialectValue), parsed.get("the binding document")?.value);
  const profiles = readProfiles(parsed.get("the profiles")!.value);
  const acquisitions = readAcquisitions(acquisitionsValue, researchSources(dialectValue));
  const verifiedAt = readVerifiedAt(preparationValue);
  const recordObj = record === undefined ? undefined : readRecord(record.value);

  // phase 6: a kind this verifier does not read
  for (const s of dialect.sources) if (s.kind !== "operation") throw new Refusal("kind-unread", `${s.name} is of the kind ${s.kind}`);

  // findings 1–4, by recomputation
  const r = recompute(dialect, caseValue, acquisitions, profiles, verifiedAt);
  const bytes = preparationForm(r.preparation);
  keep(bytes);

  // 5. preparation-differs
  let given: Uint8Array | null;
  try {
    given = preparationForm(preparationValue);
  } catch (e) {
    if (!(e instanceof OutsideDomain)) throw e;
    given = null;
  }
  if (given === null || Buffer.compare(Buffer.from(given), Buffer.from(bytes)) !== 0) {
    throw new Finding("preparation-differs", "the given preparation is not the recomputed one");
  }
  const digest = "sha256:" + sha256hex(bytes);
  const binding = `{"kind":"${BINDING_KIND}","digest":"${digest}"}`;

  let bindingState = "not-checked";
  if (recordObj !== undefined) {
    // 6. record-inputs-differ
    const inputs = recordObj.m.get("inputs") as JObj;
    const facts = inputs.m.get("facts");
    const evidence = inputs.m.get("evidence");
    const cites = recordObj.m.get("cites") ?? arr([]);
    if (facts === undefined || !jsonEqual(facts, r.factsDocument)) throw new Finding("record-inputs-differ", "the record's inputs.facts");
    if (evidence === undefined || !jsonEqual(evidence, r.evidenceDocument)) throw new Finding("record-inputs-differ", "the record's inputs.evidence");
    const prepCites = (r.preparation.m.get("cites") as { a: JVal[] }).a;
    if (cites.t !== "arr" || !sameSet(cites.a, prepCites)) throw new Finding("record-inputs-differ", "the record's cites");
    // 7–8. the binding the record carries
    const b = recordObj.m.get("binding");
    if (b !== undefined) {
      const kind = b.t === "obj" ? b.m.get("kind") : undefined;
      if (kind === undefined || kind.t !== "str" || kind.v !== BINDING_KIND) throw new Finding("binding-foreign-kind", "the record's binding is not of the preparation's kind");
      const carried = utf8(record!.text.slice(b.s, b.e));
      if (Buffer.compare(Buffer.from(carried), Buffer.from(utf8(binding))) !== 0) throw new Finding("binding-mismatch", "the record's binding is not the preparation's");
      bindingState = "matches";
    } else {
      bindingState = "absent";
    }
  }
  // 9. unbound
  if (inputs.requireBinding && bindingState !== "matches") throw new Finding("unbound", "a binding is required and none is carried");

  // the reading
  const byClass = new Map([["asserted", 0], ["record", 0], ["generated", 0]]);
  for (const e of r.lineage) {
    const c = (e.m.get("class") as { v: string }).v;
    byClass.set(c, byClass.get(c)! + 1);
  }
  const report: [string, JVal][] = [
    ["result", str("reading")],
    ["digest", str(digest)],
    ["binding", str(bindingState)],
    ["facts", r.factsDocument],
    ["evidence", r.evidenceDocument],
    ["targetsByClass", obj(Array.from(byClass).map(([k, v]) => [k, num(String(v))]))],
  ];
  const unsigned = unsignedParameters(r);
  if (unsigned.length > 0) report.push(["unsignedParameters", arr(unsigned)]);
  const freshness = unsignedFreshness(r, verifiedAt);
  if (freshness !== undefined) report.push(["unsignedFreshness", freshness]);
  return { kind: "reading", report: obj(report), recomputed: bytes };
}

function sameSet(a: JVal[], b: JVal[]): boolean {
  return a.every((x) => b.some((y) => jsonEqual(x, y))) && b.every((y) => a.some((x) => jsonEqual(x, y)));
}

const targetsOf = (o: Outcome) => o.factTargets.length + o.evidenceTargets.length;

/** §11, unsignedParameters: the parameters a derivation read that no receipt commits. */
function unsignedParameters(r: Recomputed): JObj[] {
  const entries = new Map<string, { name: string; kind: string }[]>();
  const out: JObj[] = [];
  for (const o of r.outcomes) {
    const s = o.source;
    if (s === undefined || o.skipped || s.read.rule === undefined) continue;
    if (o.isCalculator && !o.calculatorComputed) continue;
    if (targetsOf(o) === 0) continue;
    const params: { name: string; kind: string }[] = [];
    for (const name of Array.from(conditionParameters(s.read.rule)).sort(compareCodePoints)) {
      if (o.committed.has(name)) continue;
      let kind: string;
      if (name === "runAt") {
        kind = "runAt";
      } else {
        const declared = s.parameters.find((p) => p.name === name);
        if (declared === undefined) {
          kind = "case";
        } else {
          const up = r.outcomes.find((x) => x.name === declared.from)!;
          if (up.source?.kind === "selected-file" && up.source.provider === "local-file") {
            kind = "local-file";
          } else {
            const upEntry = entries.get(declared.from);
            if (upEntry === undefined) continue; // from an acquired source with no entry: not named
            kind = upEntry.some((p) => ["case", "local-file", "upstream", "ambiguous-text"].includes(p.kind)) ? "upstream" : "upstream-runAt";
          }
        }
        if (["case", "local-file", "upstream"].includes(kind) && o.ambiguous.has(name)) kind = "ambiguous-text";
      }
      params.push({ name, kind });
    }
    if (params.length === 0) continue;
    entries.set(o.name, params);
    out.push(
      obj([
        ["source", str(o.name)],
        ["parameters", arr(params.map((p) => obj([["name", str(p.name)], ["kind", str(p.kind)]])))],
        ["targets", num(String(targetsOf(o)))],
      ]),
    );
  }
  return out;
}

/** §11, unsignedFreshness: each freshness judged against verifiedAt, which no receipt covers. */
function unsignedFreshness(r: Recomputed, verifiedAt: string): JObj | undefined {
  const sources = r.outcomes
    .filter((o) => o.source !== undefined && !o.skipped)
    .map((o) =>
      obj([
        ["source", str(o.name)],
        ["checks", arr((o.calculatorComputed ? ["acquisition", "calculation"] : ["acquisition"]).map(str))],
        ["targets", num(String(targetsOf(o)))],
      ]),
    );
  if (sources.length === 0) return undefined;
  return obj([["against", str("preparation.verifiedAt")], ["verifiedAt", str(verifiedAt)], ["sources", arr(sources)]]);
}

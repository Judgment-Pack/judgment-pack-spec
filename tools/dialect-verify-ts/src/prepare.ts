// Recomputing a preparation (§11, "Findings" 1–4) by §§3–9, at the given preparation's verifiedAt.
import { BOUNDS, scanBytes } from "./bounds.ts";
import { verify as edVerify } from "./ed25519.ts";
import { DIGEST, Refusal, placeholders, profileDigestOf, sha256hex, stringTemplate } from "./forms.ts";
import type { Acquisition, ClaimForm, CopyRead, Dialect, ParamType, Profile, Rule, Source } from "./forms.ts";
import {
  NotRead, OutsideDomain, arr, bool, canon, compareCodePoints, decode, inCanonDomain, isInteger, intValue, jsonEqual, member, num,
  obj, parse, resolve, sortedDistinct, str, utf8, writeAt,
} from "./json.ts";
import type { JObj, JStr, JVal } from "./json.ts";
import { instant } from "./time.ts";

/** A finding (§11): the reading ends at it, and reports it. */
export class Finding extends Error {
  code: string;
  constructor(code: string, why: string) {
    super(why);
    this.code = code;
  }
}
const finding = (code: string, why: string): never => {
  throw new Finding(code, why);
};

const AVAILABILITY = new Set(["present", "absent", "unknown"]);
export const VERIFICATION = "verified acquisitions; session sealing and input truth are not established";
const RECEIPT_CONTEXT = "judgment-pack-gateway/receipt/3:";

type Origin = { kind: "case"; pointer: string } | { kind: "source"; source: string; pointer: string } | { kind: "runAt" };
type ScopeValue = { type: ParamType; value: JVal; origin: Origin };
type Scope = Map<string, ScopeValue>;
type Claim = { facts: JObj; evidence: Map<string, string>; status: string; reason: string; basis: string[] };

export type Outcome = {
  name: string;
  source?: Source;
  scope: Scope;
  skipped: boolean;
  request?: JObj;
  claim?: Claim;
  class: string;
  generatedInfluence: boolean;
  citation?: JObj;
  calculation?: JObj; // the lineage's calculation member
  calculatorComputed: boolean;
  isCalculator: boolean;
  committed: Set<string>; // parameters the source's own acquisition commits
  ambiguous: Set<string>; // parameters the request carries only in a $text that names another too
  factTargets: string[];
  evidenceTargets: string[];
  readDigest: string;
  candidateFrom: Map<string, string[]>; // "fact:" or "evidence:" + target
};

export type Recomputed = {
  preparation: JObj;
  outcomes: Outcome[];
  factsDocument: JObj;
  evidenceDocument: JObj;
  lineage: JObj[];
};

const digestOf = (v: JVal) => "sha256:" + sha256hex(canon(v));

function ofType(v: JVal, t: ParamType): boolean {
  if (t === "string") return v.t === "str";
  if (t === "integer") return isInteger(v);
  return v.t === "str" && instant(v.v) !== null;
}

// ---- reads (§6) ----

function applyCopy(copy: CopyRead, value: JVal, who: string): Claim {
  const facts = obj();
  for (const f of copy.facts) {
    const v = resolve(value, f.source);
    if (v === undefined) continue;
    if (!inCanonDomain(v)) finding("read-failed", `${who}: the value at ${f.source} is outside the canon domain`);
    writeAt(facts, f.target, v);
  }
  const evidence = new Map<string, string>();
  for (const e of copy.evidence) {
    const v = resolve(value, e.source);
    if (v === undefined) continue;
    if (v.t !== "str" || !AVAILABILITY.has(v.v)) finding("read-failed", `${who}: the value at ${e.source} is not an availability`);
    evidence.set(e.requirement, (v as JStr).v);
  }
  const basis = sortedDistinct([...copy.facts.map((f) => f.source), ...copy.evidence.map((e) => e.source)]);
  return { facts, evidence, status: "resolved", reason: "copied", basis };
}

function applyRule(rule: Rule, value: JVal, scope: Scope, who: string): Claim {
  const basis = new Set<string>();
  const param = (n: string) => scope.get(n)!.value;
  const holds = (c: JObj): boolean => {
    const op = (c.m.get("op") as JStr).v;
    if (op === "always") return true;
    if (op === "all") {
      for (const x of (c.m.get("of") as { a: JVal[] }).a) if (!holds(x as JObj)) return false;
      return true;
    }
    if (op === "any") {
      for (const x of (c.m.get("of") as { a: JVal[] }).a) if (holds(x as JObj)) return true;
      return false;
    }
    if (op === "not") return !holds(c.m.get("of") as JObj);
    const field = (c.m.get("field") as JStr).v;
    basis.add(field);
    const v = resolve(value, field);
    if (v === undefined) return false;
    switch (op) {
      case "exists":
        return true;
      case "equals":
        return jsonEqual(v, c.m.get("to")!);
      case "equalsParam":
        return jsonEqual(v, param((c.m.get("param") as JStr).v));
      case "isTrue":
        return v.t === "bool" && v.v;
      case "isDecimalString":
        return v.t === "str" && /^(?:0|[1-9][0-9]*)$/.test(v.v);
      case "freshWithin": {
        if (v.t !== "str") return false;
        const at = instant(v.v);
        const asOf = (c.m.get("asOf") as JStr).v;
        const maxAge = (c.m.get("maxAge") as JStr).v;
        if (at === null || rule.parameters.get(asOf) !== "timestamp" || rule.parameters.get(maxAge) !== "integer") return false;
        const n = instant((param(asOf) as JStr).v)!;
        const m = intValue(param(maxAge) as never);
        const age = n - at;
        return age >= 0 && age <= m;
      }
    }
    return false;
  };
  const match = rule.clauses.find((cl) => holds(cl.when))!;
  const facts = obj();
  for (const f of match.claim.facts) {
    const v = resolve(value, f.from);
    if (v === undefined) finding("read-failed", `${who}: ${f.from} does not resolve`);
    if (!inCanonDomain(v!)) finding("read-failed", `${who}: the value at ${f.from} is outside the canon domain`);
    writeAt(facts, f.pointer, v!);
  }
  return {
    facts,
    evidence: new Map(match.claim.evidence),
    status: match.claim.acquisitionStatus,
    reason: match.reason,
    basis: sortedDistinct(basis),
  };
}

/** The value read (§6.1): the result, then each unwrap, measured against its bounds when it is unwrapped. */
function valueRead(result: JVal, unwrap: string[], who: string): JVal {
  let cur = result;
  for (const p of unwrap) {
    const v = resolve(cur, p);
    if (v === undefined || v.t !== "str") finding("read-failed", `${who}: unwrap ${p} is not a string`);
    const bytes = utf8((v as JStr).v);
    if (bytes.length > BOUNDS.unwrappedBytes) throw new Refusal("input-over-bound", `${who}: an unwrapped string's bytes`);
    const scan = scanBytes(bytes);
    if (scan.nesting > BOUNDS.readNesting || !scan.numbersWithin) throw new Refusal("input-over-bound", `${who}: an unwrapped value`);
    try {
      cur = parse(decode(bytes));
    } catch (e) {
      if (e instanceof NotRead) finding("read-failed", `${who}: unwrap ${p} does not hold exactly one JSON value`);
      throw e;
    }
  }
  return cur;
}

// ---- templates and commitments (§4.1) ----

function instantiate(t: JVal, scope: Scope): JVal {
  if (t.t === "arr") return arr(t.a.map((x) => instantiate(x, scope)));
  if (t.t !== "obj") return t;
  const keys = Array.from(t.m.keys());
  if (keys.some((k) => k.startsWith("$"))) {
    const [name, a] = Array.from(t.m)[0];
    const n = (a as JStr).v;
    if (name === "$param") return scope.get(n)!.value;
    let out = "";
    let pos = 0;
    for (const p of placeholders(n)!) {
      const lit = (scope.get(p.name)!.value as { lit: string }).lit;
      out += n.slice(pos, p.start) + (lit === "-0" ? "0" : lit);
      pos = p.end;
    }
    return str(out + n.slice(pos));
  }
  return obj(keys.map((k) => [k, instantiate(t.m.get(k)!, scope)]));
}

function commitments(t: JVal, committed: Set<string>, ambiguous: Set<string>): void {
  if (t.t === "arr") {
    for (const x of t.a) commitments(x, committed, ambiguous);
    return;
  }
  if (t.t !== "obj") return;
  if (Array.from(t.m.keys()).some((k) => k.startsWith("$"))) {
    const [name, a] = Array.from(t.m)[0];
    if (name === "$param") {
      committed.add((a as JStr).v);
    } else {
      const names = new Set(placeholders((a as JStr).v)!.map((p) => p.name));
      if (names.size === 1) for (const n of names) committed.add(n);
      else for (const n of names) ambiguous.add(n);
    }
    return;
  }
  for (const x of t.m.values()) commitments(x, committed, ambiguous);
}

/** §4.1: why a request does not fit its profile, or null. A tool call under `mcp`; under `http` and `airbyte`
 * any object, but that `adapter-http`'s `query` is an object of string templates; nothing under `command`. */
function requestMisfit(s: Source, p: Profile): string | null {
  const request = s.template as JObj;
  if (p.shape === "command") return "a profile of shape command serves no operation";
  if (p.shape === "mcp") {
    const keys = Array.from(request.m.keys()).sort();
    const tool = request.m.get("tool");
    const name = tool !== undefined && tool.t === "str" ? tool.v : undefined;
    if (keys.join(",") !== "arguments,tool" || name === undefined || name === "") return "a request that is not a tool call, under a profile of shape mcp";
    if (!(p.tools ?? []).includes(name)) return "a tool the profile does not allow";
    return null;
  }
  const query = request.m.get("query");
  if ((member(p.adapter, "name") as JStr).v === "adapter-http" && query !== undefined) {
    const fits = query.t === "obj" && !Array.from(query.m.keys()).some((k) => k.startsWith("$")) && Array.from(query.m.values()).every((x) => stringTemplate(x, s.scope!));
    if (!fits) return "a query that is not an object of string templates, under adapter-http";
  }
  return null;
}

// ---- acquisitions (§5.2) ----

function checkReceipt(acq: Acquisition, profile: Profile, request: JObj, who: string): void {
  const invalid = (why: string): never => finding("acquisition-invalid", `${who}: ${why}`);
  const E = acq.receipt;
  const s = (k: string, v: JVal | undefined = E.m.get(k)) => (v !== undefined && v.t === "str" ? v.v : null);
  // 1. the receipt's version and kind, and the form of each member this list reads
  if (s("receiptVersion") !== "3" || s("kind") !== "acquisition") invalid("not a version-3 acquisition receipt");
  const keyId = s("keyId");
  const signature = s("signature");
  if (keyId === null || !/^[0-9a-f]{32}$/.test(keyId)) invalid("keyId is not 32 hexadecimal characters");
  if (signature === null || !/^[0-9a-f]{128}$/.test(signature)) invalid("signature is not 128 hexadecimal characters");
  if (s("source") === null || s("authority") === null) invalid("source or authority is not a string");
  const acquisition = E.m.get("acquisition");
  if (acquisition === undefined || acquisition.t !== "obj") invalid("acquisition is not an object");
  // a receipt that attests a page is not read, whatever the shape
  if (member(acquisition, "pageItems") !== undefined) invalid("the receipt attests a page (pageItems)");
  for (const k of ["argumentsCommitment", "resultDigest"]) if (!DIGEST.test(s(k) ?? "")) invalid(`${k} is not a digest`);
  // 2. the key and the signature
  if (keyId !== sha256hex(profile.key).slice(0, 32)) invalid("keyId is not the profile key's identifier");
  const unsigned = obj(Array.from(E.m).filter(([k]) => k !== "signature"));
  let signed: Uint8Array;
  try {
    signed = Buffer.concat([Buffer.from(RECEIPT_CONTEXT, "ascii"), canon(unsigned)]);
  } catch (e) {
    if (e instanceof OutsideDomain) return invalid("the receipt is outside the canon domain");
    throw e;
  }
  if (!edVerify(profile.key, signed, Uint8Array.from(Buffer.from(signature!, "hex")))) invalid("the signature does not verify");
  // 3. the source, the authority, and the channel
  if (s("source") !== profile.source || s("authority") !== profile.authority) invalid("source or authority is not the profile's");
  const field = (k: string) => member(acquisition, k);
  const same = (a: JVal | undefined, b: JVal) => a !== undefined && jsonEqual(a, b);
  if (!same(field("adapter"), profile.adapter) || !same(field("shape"), str(profile.shape)) || !same(field("endpoint"), profile.endpoint)) {
    invalid("the adapter, shape or endpoint is not the profile's");
  }
  // 4. the commitment to the request
  const salt = Buffer.from((acq.salts.m.get("args") as JStr).v, "hex");
  const commitment = Buffer.concat([salt, Buffer.from("args:", "ascii"), canon(request)]);
  if (s("argumentsCommitment") !== "sha256:" + sha256hex(commitment)) invalid("argumentsCommitment does not commit this request");
  // 5. the result's digest
  if (!inCanonDomain(acq.result)) invalid("the result is outside the canon domain");
  if (s("resultDigest") !== digestOf(acq.result)) invalid("resultDigest is not the result's");
}

function checkTimes(E: JObj, maxAge: number, at: number, who: string): void {
  for (const v of [member(E.m.get("acquisition"), "observedAt"), E.m.get("servedAt")]) {
    const t = v !== undefined && v.t === "str" ? instant(v.v) : null;
    if (t === null || t < at - maxAge || t > at + 30) finding("acquisition-stale", `${who}: a time is outside the source's window`);
  }
}

function inOneForm(sessions: { sessionId: string; callIndex: number }[]): boolean {
  const ids = sessions.map((x) => x.sessionId);
  const idx = sessions.map((x) => x.callIndex);
  const shared = new Set(ids).size === 1 && new Set(idx).size === idx.length;
  const alone = new Set(ids).size === ids.length && idx.every((k) => k === 0);
  return shared || alone;
}

// ---- calculated values (§7) ----

function checkCalculation(value: JVal, source: Source, profile: Profile, scope: Scope, at: number, who: string): { status: string; lineage: JObj } {
  const invalid = (why: string): never => finding("calculation-invalid", `${who}: ${why}`);
  const calc = member(value, "calculation");
  if (value.t !== "obj" || calc === undefined || calc.t !== "obj") return invalid("the value read has no object calculation");
  const keys = Array.from(calc.m.keys()).sort();
  if (keys.join(",") !== "asOf,calculator,inputs,status") invalid("calculation is not of exactly its members");
  const calculator = calc.m.get("calculator")!;
  if (calculator.t !== "obj" || Array.from(calculator.m.keys()).sort().join(",") !== "name,version") invalid("calculator is not of exactly name and version");
  const status = calc.m.get("status")!;
  if (status.t !== "str" || !["computed", "input-missing", "cannot-compute"].includes(status.v)) invalid("status is not a status");
  const inputs = calc.m.get("inputs")!;
  const asOf = calc.m.get("asOf")!;
  if (inputs.t !== "obj" || asOf.t !== "obj") return invalid("inputs or asOf is not an object");
  if (!jsonEqual(calculator, profile.calculator!)) invalid("the calculator is not the profile's");
  const bound = source.calculation!;
  for (const [name, v] of inputs.m) {
    const parameter = bound.inputs.get(name);
    if (parameter === undefined) invalid(`the input ${name} is not bound`);
    if (!inCanonDomain(v) || Buffer.compare(Buffer.from(canon(v)), Buffer.from(canon(scope.get(parameter!)!.value))) !== 0) {
      invalid(`the input ${name} is not the value of ${parameter}`);
    }
  }
  const asOfInstants = new Map<string, number>();
  for (const [table, ts] of asOf.m) {
    if (!bound.tables.has(table)) invalid(`the table ${table} is not named`);
    const t = ts.t === "str" ? instant(ts.v) : null;
    if (t === null) invalid(`the table ${table} has no instant`);
    asOfInstants.set(table, t!);
  }
  if ((status as JStr).v === "computed") {
    for (const name of bound.inputs.keys()) if (!inputs.m.has(name)) invalid(`the bound input ${name} is not echoed`);
    for (const [table, limit] of bound.tables) {
      const t = asOfInstants.get(table);
      if (t === undefined) invalid(`the named table ${table} is not reported`);
      if (at - t! > limit || t! - at > 30) invalid(`the table ${table} is outside its limit`);
    }
  }
  const echoed = Array.from(inputs.m.keys()).sort(compareCodePoints).map((name) => {
    const parameter = bound.inputs.get(name)!;
    const origin = scope.get(parameter)!.origin;
    const where: [string, JVal][] =
      origin.kind === "case"
        ? [["source", str("case")], ["pointer", str(origin.pointer)]]
        : origin.kind === "source"
          ? [["source", str(origin.source)], ["pointer", str(origin.pointer)]]
          : [];
    return obj([["name", str(name)], ["parameter", str(parameter)], ...where]);
  });
  const lineage = obj([["calculator", calculator], ["status", status], ["asOf", asOf], ["inputs", arr(echoed)]]);
  return { status: (status as JStr).v, lineage };
}

// ---- the recomputation ----

export function recompute(d: Dialect, caseDoc: JVal, acquisitions: Map<string, Acquisition>, profiles: Profile[], verifiedAt: string): Recomputed {
  const at = instant(verifiedAt)!;
  const runAt: ScopeValue = { type: "timestamp", value: str(verifiedAt), origin: { kind: "runAt" } };

  // 1. profile-mismatch, the sources in their order
  const profileOf = new Map<string, Profile>();
  for (const s of d.sources) {
    if (s.profile === undefined) continue;
    const p = profiles.find((x) => x.id === s.profile);
    if (p === undefined || profileDigestOf(p) !== s.profileDigest) finding("profile-mismatch", `${s.name}: no trusted profile of that id and digest`);
    // §4.4: a profile the binding document names serves the unbound source's shape and record
    const catalog = d.boundFrom.get(s.name);
    if (catalog !== undefined && (p!.shape !== catalog.shape || (member(p!.adapter, "name") as JStr).v !== catalog.record)) {
      finding("profile-mismatch", `${s.name}: bound to a profile of another shape or record`);
    }
    if (s.kind === "operation") {
      const misfit = requestMisfit(s, p!);
      if (misfit !== null) finding("profile-mismatch", `${s.name}: ${misfit}`);
    }
    if ((p!.calculator !== undefined) !== (s.calculation !== undefined)) finding("profile-mismatch", `${s.name}: calculation and the profile's calculator`);
    profileOf.set(s.name, p!);
  }

  // 2. the case
  const caseScope: Scope = new Map();
  for (const cp of d.caseParams) {
    const v = resolve(caseDoc, cp.pointer);
    if (v === undefined || !ofType(v, cp.type)) finding("parameter-invalid", `case parameter ${cp.name}`);
    caseScope.set(cp.name, { type: cp.type, value: v!, origin: { kind: "case", pointer: cp.pointer } });
  }
  const caseRead = obj([["copy", obj([["facts", d.caseFacts], ["evidence", d.caseEvidence]])]]);
  const outcomes: Outcome[] = [];
  outcomes.push({
    name: "case",
    scope: new Map([...caseScope, ["runAt", runAt]]),
    skipped: false,
    claim: applyCopy(d.caseCopy, caseDoc, "case"),
    class: "asserted",
    generatedInfluence: false,
    calculatorComputed: false,
    isCalculator: false,
    committed: new Set(),
    ambiguous: new Set(),
    factTargets: d.caseFactTargets,
    evidenceTargets: d.caseEvidenceTargets,
    readDigest: digestOf(caseRead),
    candidateFrom: copyCandidates(d.caseCopy),
  });

  // 3. the sources, in their order
  const sessions: { sessionId: string; callIndex: number }[] = [];
  for (const s of d.sources) {
    const profile = profileOf.get(s.name)!;
    const scope: Scope = new Map(caseScope);
    let skipped = false;
    for (const sp of s.parameters) {
      const up = outcomes.find((o) => o.name === sp.from)!;
      const v = up.skipped || up.claim!.status !== "resolved" ? undefined : resolve(up.claim!.facts, sp.pointer);
      if (v === undefined) {
        skipped = true;
        continue;
      }
      if (!ofType(v, sp.type)) finding("parameter-invalid", `${s.name}: source parameter ${sp.name}`);
      scope.set(sp.name, { type: sp.type, value: v, origin: { kind: "source", source: sp.from, pointer: sp.pointer } });
    }
    scope.set("runAt", runAt);
    const generatedInfluence =
      profile.class === "generated" || s.parameters.some((sp) => outcomes.find((o) => o.name === sp.from)!.generatedInfluence);
    const outcome: Outcome = {
      name: s.name,
      source: s,
      scope,
      skipped,
      class: profile.class,
      generatedInfluence,
      calculatorComputed: false,
      isCalculator: profile.calculator !== undefined,
      committed: new Set(),
      ambiguous: new Set(),
      factTargets: s.factTargets,
      evidenceTargets: s.evidenceTargets,
      readDigest: digestOf(s.read.raw),
      candidateFrom: s.read.copy ? copyCandidates(s.read.copy) : ruleCandidates(s.read.rule!),
    };
    outcomes.push(outcome);
    if (skipped) {
      if (acquisitions.has(s.name)) finding("acquisition-unexpected", `${s.name} is skipped and has an acquisition`);
      continue;
    }
    const request = instantiate(s.template!, scope) as JObj;
    outcome.request = request;
    commitments(s.template!, outcome.committed, outcome.ambiguous);
    const acq = acquisitions.get(s.name);
    if (acq === undefined) return finding("acquisition-missing", `${s.name} has no acquisition`);
    checkReceipt(acq, profile, request, s.name);
    checkTimes(acq.receipt, s.maxAge!, at, s.name);
    const callIndex = acq.receipt.m.get("callIndex");
    const sessionId = acq.receipt.m.get("sessionId");
    if (!isInteger(callIndex) || intValue(callIndex) < 0 || sessionId === undefined || sessionId.t !== "str") {
      finding("acquisition-sessions", `${s.name}: callIndex or sessionId is not of its form`);
    }
    sessions.push({ sessionId: (sessionId as JStr).v, callIndex: intValue(callIndex as never) });
    if (!inOneForm(sessions)) finding("acquisition-sessions", `${s.name}: the acquisitions so far are in neither form`);
    outcome.citation = obj([["callIndex", callIndex!], ["sessionId", sessionId!], ["signature", acq.receipt.m.get("signature")!]]);

    const value = valueRead(acq.result, s.read.unwrap, s.name);
    if (outcome.isCalculator) {
      const c = checkCalculation(value, s, profile, scope, at, s.name);
      outcome.calculation = c.lineage;
      const echoed = member(member(value, "calculation"), "inputs") as JObj;
      for (const name of echoed.m.keys()) outcome.committed.add(s.calculation!.inputs.get(name)!);
      if (c.status !== "computed") {
        outcome.claim = {
          facts: obj(),
          evidence: new Map(s.evidenceTargets.map((r) => [r, "unknown"])),
          status: "unknown",
          reason: c.status === "input-missing" ? "calculation-input-missing" : "calculation-cannot-compute",
          basis: ["/calculation/status"],
        };
        continue;
      }
      outcome.calculatorComputed = true;
    }
    outcome.claim = s.read.copy ? applyCopy(s.read.copy, value, s.name) : applyRule(s.read.rule!, value, scope, s.name);
  }
  for (const name of acquisitions.keys()) {
    if (!d.sources.some((s) => s.name === name)) finding("acquisition-unexpected", `the acquisition ${name} names no source`);
  }

  // 4. admission (§8.2)
  for (const o of outcomes) {
    const admitted = (list: string[] | undefined) => {
      const l = list ?? ["asserted", "record"];
      return l.includes(o.class) && (!o.generatedInfluence || l.includes("generated"));
    };
    for (const t of o.factTargets) if (!admitted(d.admitsFacts.get(t))) finding("admission-refused", `${o.name}: fact target ${t}`);
    for (const r of o.evidenceTargets) if (!admitted(d.admitsEvidence.get(r))) finding("admission-refused", `${o.name}: requirement ${r}`);
  }

  // the preparation (§9): in versions 2 and 3 alike, `cites` ordered by callIndex, those of one index in the order of
  // `sources`, as the Runner writes it (§9.1); a `research` source, whose own order differs, is not read
  const order = new Map(d.sources.map((s, k) => [s.name, k]));
  const cited = outcomes.filter((o) => o.citation !== undefined);
  cited.sort((a, b) => {
    const x = intValue(a.citation!.m.get("callIndex") as never);
    const y = intValue(b.citation!.m.get("callIndex") as never);
    return x !== y ? x - y : order.get(a.name)! - order.get(b.name)!;
  });
  const lineage: JObj[] = [];
  for (const o of outcomes) {
    const entry = (kind: "fact" | "evidence", target: string): JObj => {
      const present = o.claim === undefined ? false : kind === "fact" ? resolve(o.claim.facts, target) !== undefined : o.claim.evidence.has(target);
      const e: [string, JVal][] = [
        ["source", str(o.name)],
        ["kind", str(kind)],
        ["target", str(target)],
        ["class", str(o.class)],
        ["generatedInfluence", bool(o.generatedInfluence)],
        ["present", bool(present)],
        ["status", str(statusOf(o))],
        ["reason", str(reasonOf(o))],
        ["basis", arr((o.claim?.basis ?? []).map(str))],
      ];
      const cand = o.candidateFrom.get(`${kind}:${target}`);
      if (cand !== undefined && cand.length > 0) e.push(["candidateFrom", arr(cand.map(str))]);
      e.push(["readDigest", str(o.readDigest)]);
      if (o.citation !== undefined) e.push(["receipt", o.citation]);
      if (o.calculation !== undefined) e.push(["calculation", o.calculation]);
      return obj(e);
    };
    for (const t of [...o.factTargets].sort(compareCodePoints)) lineage.push(entry("fact", t));
    for (const r of [...o.evidenceTargets].sort(compareCodePoints)) lineage.push(entry("evidence", r));
  }
  const outcomeValues = outcomes.map((o) => {
    const params: [string, JVal][] = Array.from(o.scope).map(([k, v]) => [k, v.value]);
    const e: [string, JVal][] = [["name", str(o.name)], ["parameters", obj(params)]];
    if (o.request !== undefined) e.push(["arguments", o.request]);
    if (o.claim !== undefined) e.push(["claim", claimValue(o.claim)]);
    e.push(["status", str(statusOf(o))], ["reason", str(reasonOf(o))]);
    return obj(e);
  });
  const preparation = obj([
    ["version", num(String(d.version))],
    ["verifiedAt", str(verifiedAt)],
    ["mappingDigest", str(digestOf(d.raw))],
    ["verification", str(VERIFICATION)],
    ["cites", arr(cited.map((o) => o.citation!))],
    ["lineage", arr(lineage)],
    ["outcomes", arr(outcomeValues)],
  ]);

  // the facts and evidence-availability documents (§8.1)
  const factsDocument = obj();
  const evidenceDocument = obj();
  for (const o of outcomes) {
    if (o.claim === undefined) continue;
    for (const t of o.factTargets) {
      const v = resolve(o.claim.facts, t);
      if (v !== undefined) writeAt(factsDocument, t, v);
    }
    for (const [r, a] of o.claim.evidence) evidenceDocument.m.set(r, str(a));
  }
  return { preparation, outcomes, factsDocument, evidenceDocument, lineage };
}

function statusOf(o: Outcome): string {
  return o.claim === undefined ? "dependency-unavailable" : o.claim.status;
}
function reasonOf(o: Outcome): string {
  return o.claim === undefined ? "dependency-unavailable" : o.claim.reason;
}

function claimValue(c: Claim): JObj {
  return obj([
    ["facts", c.facts],
    ["evidenceAvailability", obj(Array.from(c.evidence).map(([k, v]) => [k, str(v)]))],
    ["acquisitionStatus", str(c.status)],
    ["reason", str(c.reason)],
    ["basis", arr(c.basis.map(str))],
  ]);
}

function copyCandidates(copy: CopyRead): Map<string, string[]> {
  const m = new Map<string, string[]>();
  for (const f of copy.facts) m.set(`fact:${f.target}`, [f.source]);
  for (const e of copy.evidence) m.set(`evidence:${e.requirement}`, [e.source]);
  return m;
}

function ruleCandidates(rule: Rule): Map<string, string[]> {
  const m = new Map<string, Set<string>>();
  for (const c of rule.clauses) {
    for (const f of (c.claim as ClaimForm).facts) {
      const k = `fact:${f.pointer}`;
      if (!m.has(k)) m.set(k, new Set());
      m.get(k)!.add(f.from);
    }
  }
  return new Map(Array.from(m).map(([k, v]) => [k, sortedDistinct(v)]));
}

/** The parameters a rule's conditions name, at any depth (§11, unsignedParameters). */
export function conditionParameters(rule: Rule): Set<string> {
  const out = new Set<string>();
  const walk = (c: JVal | undefined) => {
    if (c === undefined || c.t !== "obj") return;
    const op = (c.m.get("op") as JStr).v;
    if (op === "equalsParam") out.add((c.m.get("param") as JStr).v);
    if (op === "freshWithin") {
      out.add((c.m.get("asOf") as JStr).v);
      out.add((c.m.get("maxAge") as JStr).v);
    }
    if (op === "all" || op === "any") for (const x of (c.m.get("of") as { a: JVal[] }).a) walk(x);
    if (op === "not") walk(c.m.get("of"));
  };
  for (const cl of rule.clauses) walk(cl.when);
  return out;
}

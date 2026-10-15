// The forms of §§2–8, §5.1 and §5.2, held in phase 4 of §11, and the counts of §12 held in phase 3.
import { createHash } from "node:crypto";
import { BOUNDS } from "./bounds.ts";
import { keyAcceptable } from "./ed25519.ts";
import { arr, canon, depth, inCanonDomain, isInteger, isPointer, intValue, member, obj } from "./json.ts";
import type { JObj, JVal } from "./json.ts";
import { instant } from "./time.ts";

/** A refusal (§11): the reading reports nothing but its code. */
export class Refusal extends Error {
  code: string;
  constructor(code: string, why: string) {
    super(why);
    this.code = code;
  }
}

const malformed = (why: string): never => {
  throw new Refusal("input-malformed", why);
};

export type ParamType = "string" | "integer" | "timestamp";
const TYPES = new Set(["string", "integer", "timestamp"]);
const CLASSES = new Set(["asserted", "record", "generated"]);
const AVAILABILITY = new Set(["present", "absent", "unknown"]);
const STATUSES = new Set(["resolved", "absent", "unknown"]);
const SHAPES = new Set(["airbyte", "mcp", "http", "command"]);
const OPERATION_SHAPES = new Set(["airbyte", "mcp", "http"]); // the shapes that serve an operation (§4.1)
// §4.3: the kinds version 3 adds, and the members each names beside §4's, `profile`, `profileDigest` and
// `maxAge`: those it requires, and those it may give.
const VERSION_3_KINDS = new Map<string, { required: string[]; optional: string[] }>([
  ["http", { required: ["method", "path"], optional: ["query", "body", "headers"] }],
  ["sql", { required: ["statement", "bindings"], optional: [] }],
  ["web", { required: ["url"], optional: [] }],
  ["research", { required: ["question", "constraints", "model", "evidence"], optional: [] }],
]);
// §2: the members of version 2 alone, which a document of version 3 carries none of.
const VERSION_2_MEMBERS = ["provider", "facts", "evidence"];
// §4.4: the catalog names of an unbound `operation`, which the binding removes.
const UNBOUND_MEMBERS = ["platform", "operation", "shape", "record"];
export const DIGEST = /^sha256:[0-9a-f]{64}$/;
const HEX64 = /^[0-9a-f]{64}$/;

export type CaseParam = { name: string; pointer: string; type: ParamType };
export type SourceParam = { name: string; from: string; pointer: string; type: ParamType };
export type CopyRead = { facts: { target: string; source: string }[]; evidence: { requirement: string; source: string }[] };
export type ClaimForm = { facts: { pointer: string; from: string }[]; evidence: Map<string, string>; acquisitionStatus: string };
export type Clause = { when: JObj; claim: ClaimForm; reason: string };
export type Rule = { parameters: Map<string, ParamType>; clauses: Clause[] };
export type Read = { raw: JVal; unwrap: string[]; copy?: CopyRead; rule?: Rule };
export type Calculation = { inputs: Map<string, string>; tables: Map<string, number> };

export type Source = {
  name: string;
  kind: string;
  parameters: SourceParam[];
  read: Read;
  provider?: string;
  profile?: string;
  profileDigest?: string;
  maxAge?: number;
  template?: JVal; // `arguments`, the whole request template
  scope?: Map<string, ParamType>; // its scope, for the profile's rules on the request (§4.1)
  calculation?: Calculation;
  factTargets: string[];
  evidenceTargets: string[];
};

/** An unbound source's `shape` and `record` (§4.4), which the profile it is bound to must serve. */
export type Catalog = { shape: string; record: string };

export type Dialect = {
  raw: JVal;
  version: number; // 2 or 3 (§2)
  unbound: Map<string, Catalog>; // each unbound source by its name (§4.4)
  boundFrom: Map<string, Catalog>; // of a bound dialect: each source the binding document bound
  caseParams: CaseParam[];
  caseCopy: CopyRead;
  caseFacts: JVal; // the case's `facts` and `evidence`, as written, for the case's read
  caseEvidence: JVal;
  caseFactTargets: string[];
  caseEvidenceTargets: string[];
  sources: Source[];
  admitsFacts: Map<string, string[]>;
  admitsEvidence: Map<string, string[]>;
};

export type Profile = {
  id: string;
  raw: JVal;
  key: Uint8Array;
  publicKey: string;
  class: string;
  source: string;
  authority: string;
  shape: string;
  adapter: JVal;
  endpoint: JVal;
  tools?: string[];
  calculator?: JVal;
};

export type Acquisition = { result: JVal; receipt: JObj; salts: JObj };

// ---- helpers ----

function exact(v: JVal | undefined, what: string, required: string[], optional: string[] = []): JObj {
  if (v === undefined || v.t !== "obj") return malformed(`${what} is not an object`);
  for (const r of required) if (!v.m.has(r)) malformed(`${what} lacks ${r}`);
  for (const k of v.m.keys()) if (!required.includes(k) && !optional.includes(k)) malformed(`${what} has the unknown member ${k}`);
  return v;
}

/** §2, version 3 written one way, by the Runner's encoding rule: of the members its encoding leaves out when empty,
 * one written as the empty array or the empty object is refused. They are `sources`, `unmapped` and
 * `unmappedEvidence`, the case's and a source's `parameters`, and the `facts` and `evidence` of `admits`; every other
 * member written empty is read. */
function notWrittenEmpty(v: JVal | undefined, members: string[], what: string): void {
  if (v === undefined || v.t !== "obj") return;
  for (const k of members) {
    const x = v.m.get(k);
    if (x !== undefined && ((x.t === "arr" && x.a.length === 0) || (x.t === "obj" && x.m.size === 0))) {
      malformed(`${what}.${k} is written empty, which version 3 leaves out`);
    }
  }
}

function string(v: JVal | undefined, what: string): string {
  if (v === undefined || v.t !== "str") return malformed(`${what} is not a string`);
  return v.v;
}

function nonEmpty(v: JVal | undefined, what: string): string {
  const s = string(v, what);
  if (s === "") malformed(`${what} is empty`);
  return s;
}

function pointer(v: JVal | undefined, what: string): string {
  const s = string(v, what);
  if (!isPointer(s)) malformed(`${what} is not a JSON Pointer`);
  return s;
}

function factTarget(v: JVal | undefined, what: string): string {
  const s = pointer(v, what);
  if (s === "") malformed(`${what} is the empty pointer`);
  return s;
}

function array(v: JVal | undefined, what: string): JVal[] {
  if (v === undefined || v.t !== "arr") return malformed(`${what} is not an array`);
  return v.a;
}

function object(v: JVal | undefined, what: string): JObj {
  if (v === undefined || v.t !== "obj") return malformed(`${what} is not an object`);
  return v;
}

function paramType(v: JVal | undefined, what: string): ParamType {
  const s = string(v, what);
  if (!TYPES.has(s)) malformed(`${what} is not a parameter type`);
  return s as ParamType;
}

function integerIn(v: JVal | undefined, lo: number, hi: number, what: string): number {
  if (!isInteger(v)) return malformed(`${what} is not an integer`);
  const n = intValue(v);
  if (n < lo || n > hi) malformed(`${what} is out of range`);
  return n;
}

// ---- phase 3: the counts ----

/** The counts of §12 taken on the documents read, wherever the count can be taken (§11, phase 3). */
export function countsWithin(dialect: JVal, acquisitions: JVal): boolean {
  const caseObj = member(dialect, "case");
  const caseParams = member(caseObj, "parameters");
  const nCase = caseParams?.t === "obj" ? caseParams.m.size : 0;
  if (nCase + 1 > BOUNDS.scopeParameters) return false;
  let facts = 0;
  let evidence = 0;
  const copyTargets = (copy: JVal | undefined, f: Set<string>, e: Set<string>) => {
    const cf = member(copy, "facts");
    if (cf?.t === "arr") for (const x of cf.a) { const t = member(x, "target"); if (t?.t === "str") f.add(t.v); }
    const ce = member(copy, "evidence");
    if (ce?.t === "arr") for (const x of ce.a) { const r = member(x, "requirement"); if (r?.t === "str") e.add(r.v); }
  };
  {
    const f = new Set<string>();
    const e = new Set<string>();
    copyTargets(caseObj, f, e);
    facts += f.size;
    evidence += e.size;
  }
  const listedWithin = (c: JVal | undefined): boolean => {
    if (c === undefined || c.t !== "obj") return true;
    const op = member(c, "op");
    const of = member(c, "of");
    if (op?.t === "str" && (op.v === "all" || op.v === "any") && of?.t === "arr") {
      if (of.a.length > BOUNDS.listed) return false;
      return of.a.every(listedWithin);
    }
    if (op?.t === "str" && op.v === "not") return listedWithin(of);
    return true;
  };
  const sources = member(dialect, "sources");
  if (sources?.t === "arr") {
    if (sources.a.length > BOUNDS.sources) return false;
    for (const s of sources.a) {
      const sp = member(s, "parameters");
      if (sp?.t === "obj" && nCase + sp.m.size + 1 > BOUNDS.scopeParameters) return false;
      const read = member(s, "read");
      const unwrap = member(read, "unwrap");
      if (unwrap?.t === "arr" && unwrap.a.length > BOUNDS.unwraps) return false;
      const f = new Set<string>();
      const e = new Set<string>();
      copyTargets(member(read, "copy"), f, e);
      const clauses = member(member(read, "rule"), "clauses");
      if (clauses?.t === "arr") {
        if (clauses.a.length > BOUNDS.clauses) return false;
        for (const c of clauses.a) {
          if (!listedWithin(member(c, "when"))) return false;
          const claim = member(c, "claim");
          const cf = member(claim, "facts");
          if (cf?.t === "arr") for (const x of cf.a) { const p = member(x, "pointer"); if (p?.t === "str") f.add(p.v); }
          const ce = member(claim, "evidence");
          if (ce?.t === "obj") for (const k of ce.m.keys()) e.add(k);
        }
      }
      facts += f.size;
      evidence += e.size;
    }
  }
  if (facts > BOUNDS.factTargets || evidence > BOUNDS.evidenceTargets) return false;
  if (acquisitions.t === "obj") {
    const research = researchSources(dialect);
    for (const [name, a] of acquisitions.m) {
      const r = member(member(a, "response"), "result");
      if (r !== undefined && depth(r) > BOUNDS.readNesting) return false;
      // the retained responses of a `research` source, at most 64 (§12)
      const responses = member(r, "responses");
      if (research.has(name) && responses?.t === "arr" && responses.a.length > BOUNDS.retainedResponses) return false;
    }
  }
  return true;
}

/** The names of the dialect's sources of kind `research`, read wherever they can be, before any form is checked: their
 * acquisitions have a form of their own (§4.3, §5.2). */
export function researchSources(dialect: JVal): Set<string> {
  const out = new Set<string>();
  const sources = member(dialect, "sources");
  if (dialect.t !== "obj" || sources?.t !== "arr") return out;
  for (const s of sources.a) {
    const kind = member(s, "kind");
    const name = member(s, "name");
    if (kind?.t === "str" && kind.v === "research" && name?.t === "str") out.add(name.v);
  }
  return out;
}

// ---- phase 4: the dialect (§§2–8) ----

type Scope = Map<string, ParamType>;

function readCopy(v: JVal | undefined, what: string, arraysRequired: boolean, besides: string[] = []): CopyRead {
  const o = exact(v, what, arraysRequired ? ["facts", "evidence"] : [], arraysRequired ? besides : ["facts", "evidence", ...besides]);
  const facts = (o.m.has("facts") ? array(o.m.get("facts"), `${what}.facts`) : []).map((x, k) => {
    const e = exact(x, `${what}.facts[${k}]`, ["target", "source"]);
    return { target: factTarget(e.m.get("target"), "a copy's target"), source: pointer(e.m.get("source"), "a copy's source") };
  });
  const evidence = (o.m.has("evidence") ? array(o.m.get("evidence"), `${what}.evidence`) : []).map((x, k) => {
    const e = exact(x, `${what}.evidence[${k}]`, ["requirement", "source"]);
    return { requirement: nonEmpty(e.m.get("requirement"), "a copy's requirement"), source: pointer(e.m.get("source"), "a copy's source") };
  });
  const seen = new Set<string>();
  for (const e of evidence) {
    if (seen.has(e.requirement)) malformed(`${what} names the requirement ${e.requirement} twice`);
    seen.add(e.requirement);
  }
  return { facts, evidence };
}

function readCondition(v: JVal | undefined, declared: Map<string, ParamType>, what: string): JObj {
  const o = object(v, what);
  const op = string(o.m.get("op"), `${what}.op`);
  switch (op) {
    case "always":
      exact(o, what, ["op"]);
      break;
    case "exists":
    case "isTrue":
    case "isDecimalString":
      exact(o, what, ["op", "field"]);
      pointer(o.m.get("field"), `${what}.field`);
      break;
    case "equals":
      exact(o, what, ["op", "field", "to"]);
      pointer(o.m.get("field"), `${what}.field`);
      if (!inCanonDomain(o.m.get("to")!)) malformed(`${what}.to is outside the canon domain`);
      break;
    case "equalsParam": {
      exact(o, what, ["op", "field", "param"]);
      pointer(o.m.get("field"), `${what}.field`);
      const n = string(o.m.get("param"), `${what}.param`);
      if (!declared.has(n)) malformed(`${what} names ${n}, which the rule does not declare`);
      break;
    }
    case "freshWithin": {
      exact(o, what, ["op", "field", "asOf", "maxAge"]);
      pointer(o.m.get("field"), `${what}.field`);
      for (const m of ["asOf", "maxAge"]) {
        const n = string(o.m.get(m), `${what}.${m}`);
        if (!declared.has(n)) malformed(`${what} names ${n}, which the rule does not declare`);
      }
      break;
    }
    case "all":
    case "any": {
      exact(o, what, ["op", "of"]);
      const of = array(o.m.get("of"), `${what}.of`);
      if (of.length > BOUNDS.listed) malformed(`${what} lists too many conditions`);
      of.forEach((c, k) => readCondition(c, declared, `${what}.of[${k}]`));
      break;
    }
    case "not":
      exact(o, what, ["op", "of"]);
      readCondition(o.m.get("of"), declared, `${what}.of`);
      break;
    default:
      malformed(`${what} has the unknown op ${op}`);
  }
  return o;
}

function readRule(v: JVal | undefined, scope: Scope, what: string): Rule {
  const o = exact(v, what, ["ruleVersion", "parameters", "clauses"]);
  if (string(o.m.get("ruleVersion"), `${what}.ruleVersion`) !== "1") malformed(`${what}.ruleVersion is not "1"`);
  const parameters = new Map<string, ParamType>();
  for (const [name, t] of object(o.m.get("parameters"), `${what}.parameters`).m) {
    const type = paramType(t, `${what}.parameters.${name}`);
    if (scope.get(name) !== type) malformed(`${what} declares ${name}, which is not in the scope with that type`);
    parameters.set(name, type);
  }
  const raw = array(o.m.get("clauses"), `${what}.clauses`);
  if (raw.length < 1 || raw.length > BOUNDS.clauses) malformed(`${what} has ${raw.length} clauses`);
  const clauses = raw.map((c, k) => {
    const cw = `${what}.clauses[${k}]`;
    const co = exact(c, cw, ["when", "claim", "reason"]);
    const when = readCondition(co.m.get("when"), parameters, `${cw}.when`);
    const cf = exact(co.m.get("claim"), `${cw}.claim`, ["facts", "evidence", "acquisitionStatus"]);
    const facts = array(cf.m.get("facts"), `${cw}.claim.facts`).map((x, j) => {
      const e = exact(x, `${cw}.claim.facts[${j}]`, ["pointer", "from"]);
      return { pointer: factTarget(e.m.get("pointer"), "a claim form's pointer"), from: pointer(e.m.get("from"), "a claim form's from") };
    });
    const evidence = new Map<string, string>();
    for (const [req, a] of object(cf.m.get("evidence"), `${cw}.claim.evidence`).m) {
      if (req === "") malformed(`${cw}.claim.evidence names the empty requirement`);
      const s = string(a, `${cw}.claim.evidence.${req}`);
      if (!AVAILABILITY.has(s)) malformed(`${cw}.claim.evidence.${req} is not an availability`);
      evidence.set(req, s);
    }
    const status = string(cf.m.get("acquisitionStatus"), `${cw}.claim.acquisitionStatus`);
    if (!STATUSES.has(status)) malformed(`${cw}.claim.acquisitionStatus is not a status`);
    return { when, claim: { facts, evidence, acquisitionStatus: status }, reason: string(co.m.get("reason"), `${cw}.reason`) };
  });
  const last = clauses[clauses.length - 1].when;
  if (!(last.m.size === 1 && member(last, "op")?.t === "str" && (member(last, "op") as { v: string }).v === "always")) {
    malformed(`${what}'s last clause is not always`);
  }
  return { parameters, clauses };
}

function readRead(v: JVal | undefined, scope: Scope, what: string): Read {
  const o = object(v, what);
  const hasCopy = o.m.has("copy");
  const hasRule = o.m.has("rule");
  if (hasCopy === hasRule) malformed(`${what} has not exactly one of copy and rule`);
  exact(o, what, [hasCopy ? "copy" : "rule"], ["unwrap"]);
  let unwrap: string[] = [];
  if (o.m.has("unwrap")) {
    const u = array(o.m.get("unwrap"), `${what}.unwrap`);
    if (u.length < 1 || u.length > BOUNDS.unwraps) malformed(`${what}.unwrap has ${u.length} pointers`);
    unwrap = u.map((p, k) => pointer(p, `${what}.unwrap[${k}]`));
  }
  // §6.2: a copy's `facts` and `evidence` are both required, as the Runner requires them; either may be empty
  if (hasCopy) return { raw: o, unwrap, copy: readCopy(o.m.get("copy"), `${what}.copy`, true) };
  return { raw: o, unwrap, rule: readRule(o.m.get("rule"), scope, `${what}.rule`) };
}

/** Placeholders of a `$text` (§4.1): `{{`, a name, and the next `}}`; null when a `{{` has no `}}` after it. */
export function placeholders(t: string): { start: number; end: number; name: string }[] | null {
  const out: { start: number; end: number; name: string }[] = [];
  let pos = 0;
  for (;;) {
    const k = t.indexOf("{{", pos);
    if (k < 0) return out;
    const j = t.indexOf("}}", k + 2);
    if (j < 0) return null;
    out.push({ start: k, end: j + 2, name: t.slice(k + 2, j) });
    pos = j + 2;
  }
}

function checkTemplate(v: JVal, scope: Scope, what: string): void {
  if (v.t === "arr") {
    v.a.forEach((x, k) => checkTemplate(x, scope, `${what}[${k}]`));
    return;
  }
  if (v.t !== "obj") return;
  const dollar = Array.from(v.m.keys()).some((k) => k.startsWith("$"));
  if (!dollar) {
    for (const [k, x] of v.m) checkTemplate(x, scope, `${what}.${k}`);
    return;
  }
  if (v.m.size !== 1) malformed(`${what} is a template form with more than one member`);
  const [name, arg] = Array.from(v.m)[0];
  if (name === "$param") {
    const n = string(arg, `${what}.$param`);
    if (n === "runAt" || !scope.has(n)) malformed(`${what} names ${n}, which is not in the scope or is runAt`);
  } else if (name === "$text") {
    const ps = placeholders(string(arg, `${what}.$text`));
    if (ps === null) malformed(`${what}.$text has a {{ with no }} after it`);
    for (const p of ps!) {
      if (p.name === "runAt" || scope.get(p.name) !== "integer") malformed(`${what}.$text names ${p.name}, not an integer parameter of the scope`);
    }
  } else {
    malformed(`${what} is the unknown template form ${name}`);
  }
}

/** A string template (§4.1): a string, a `$text`, or a `$param` naming a `string` or `timestamp` parameter. */
export function stringTemplate(v: JVal | undefined, scope: Map<string, ParamType>): boolean {
  if (v === undefined) return false;
  if (v.t === "str") return true;
  if (v.t !== "obj" || v.m.size !== 1) return false;
  const [name, arg] = Array.from(v.m)[0];
  if (name === "$text") return true;
  if (name !== "$param" || arg.t !== "str") return false;
  const type = scope.get(arg.v);
  return type === "string" || type === "timestamp";
}

/** An operation's `arguments` (§4.1): the template of its request, an object and not a template form, held to the
 * rules of a template. What more it must be is the profile's to say, a finding of the recomputation. */
function readRequest(v: JVal | undefined, scope: Scope, what: string): JObj {
  const o = object(v, what);
  if (Array.from(o.m.keys()).some((k) => k.startsWith("$"))) malformed(`${what} is a template form, not an object`);
  checkTemplate(o, scope, what);
  return o;
}

function targetsOf(read: Read): { facts: string[]; evidence: string[] } {
  if (read.copy) return { facts: read.copy.facts.map((f) => f.target), evidence: read.copy.evidence.map((e) => e.requirement) };
  const facts = new Set<string>();
  const evidence = new Set<string>();
  for (const c of read.rule!.clauses) {
    for (const f of c.claim.facts) facts.add(f.pointer);
    for (const r of c.claim.evidence.keys()) evidence.add(r);
  }
  return { facts: Array.from(facts), evidence: Array.from(evidence) };
}

function classList(v: JVal | undefined, what: string): string[] {
  return array(v, what).map((c, k) => {
    const s = string(c, `${what}[${k}]`);
    if (!CLASSES.has(s)) malformed(`${what}[${k}] is not a class`);
    return s;
  });
}

export function readDialect(d: JVal): Dialect {
  const o = exact(d, "the dialect", ["version", "case"], ["sources", "admits", "unmapped", "unmappedEvidence", "provider", "facts", "evidence"]);
  const version = o.m.get("version")!;
  if (version.t !== "num" || (version.lit !== "2" && version.lit !== "3")) malformed("the dialect's version is not the integer 2 or 3");
  const v = Number((version as { lit: string }).lit);
  if (v === 3) {
    for (const k of VERSION_2_MEMBERS) if (o.m.has(k)) malformed(`the dialect's ${k} is a member of version 2 alone`);
    notWrittenEmpty(o, ["sources", "unmapped", "unmappedEvidence"], "the dialect");
    notWrittenEmpty(o.m.get("case"), ["parameters"], "the case");
  }
  if (o.m.has("provider") && string(o.m.get("provider"), "provider") !== "") malformed("provider is not the empty string");
  for (const k of ["facts", "evidence"]) if (o.m.has(k) && o.m.get(k)!.t !== "null") malformed(`the dialect's ${k} is not null`);
  if (o.m.has("unmapped")) {
    const u = array(o.m.get("unmapped"), "unmapped").map((p, k) => pointer(p, `unmapped[${k}]`));
    if (new Set(u).size !== u.length) malformed("unmapped is not distinct");
  }
  if (o.m.has("unmappedEvidence")) {
    const u = array(o.m.get("unmappedEvidence"), "unmappedEvidence").map((p, k) => nonEmpty(p, `unmappedEvidence[${k}]`));
    if (new Set(u).size !== u.length) malformed("unmappedEvidence is not distinct");
  }

  // §3: the case and its parameters
  const c = exact(o.m.get("case"), "the case", ["facts", "evidence"], ["parameters"]);
  const caseParams: CaseParam[] = [];
  const caseScope: Scope = new Map();
  if (c.m.has("parameters")) {
    for (const [name, decl] of object(c.m.get("parameters"), "case.parameters").m) {
      if (name === "" || name === "runAt") malformed(`the case parameter name ${JSON.stringify(name)} is not allowed`);
      const e = exact(decl, `case.parameters.${name}`, ["pointer", "type"]);
      const p = { name, pointer: pointer(e.m.get("pointer"), `case.parameters.${name}.pointer`), type: paramType(e.m.get("type"), `case.parameters.${name}.type`) };
      caseParams.push(p);
      caseScope.set(name, p.type);
    }
  }
  if (caseScope.size + 1 > BOUNDS.scopeParameters) throw new Refusal("input-over-bound", "the case's scope");
  const caseCopy = readCopy(c, "the case", true, ["parameters"]);

  // §4: the sources
  const sources: Source[] = [];
  const unbound = new Map<string, Catalog>();
  const rawSources = o.m.has("sources") ? array(o.m.get("sources"), "sources") : [];
  if (rawSources.length > BOUNDS.sources) throw new Refusal("input-over-bound", "sources");
  rawSources.forEach((raw, i) => {
    const what = `sources[${i}]`;
    const so = object(raw, what);
    const kind = string(so.m.get("kind"), `${what}.kind`);
    const base = ["name", "kind", "read"];
    // §4.4: the unbound form, of version 3 alone; a version-2 source that names one of its members is refused as
    // naming a member its kind does not list.
    const unboundForm = kind === "operation" && v === 3 && UNBOUND_MEMBERS.some((k) => so.m.has(k));
    let catalog: Catalog | undefined;
    if (unboundForm) {
      exact(so, what, [...base, ...UNBOUND_MEMBERS, "maxAge", "arguments"], ["parameters", "calculation"]);
      nonEmpty(so.m.get("platform"), `${what}.platform`);
      nonEmpty(so.m.get("operation"), `${what}.operation`);
      const shape = string(so.m.get("shape"), `${what}.shape`);
      if (!OPERATION_SHAPES.has(shape)) malformed(`${what}.shape is not airbyte, mcp or http`);
      catalog = { shape, record: nonEmpty(so.m.get("record"), `${what}.record`) };
    } else if (kind === "operation") {
      exact(so, what, [...base, "profile", "profileDigest", "maxAge", "arguments"], ["parameters", "calculation"]);
    } else if (kind === "selected-file") {
      const provider = string(so.m.get("provider"), `${what}.provider`);
      if (provider === "local-file") exact(so, what, [...base, "provider"], ["parameters"]);
      else if (provider === "google-drive") exact(so, what, [...base, "provider", "profile", "profileDigest", "maxAge", "arguments"], ["parameters"]);
      else malformed(`${what}.provider is not a provider`);
    } else if (VERSION_3_KINDS.has(kind)) {
      if (v === 2) malformed(`${what} names the version-3 kind ${kind} in a version-2 dialect`);
      const members = VERSION_3_KINDS.get(kind)!;
      exact(so, what, [...base, "profile", "profileDigest", "maxAge", ...members.required], ["parameters", ...members.optional]);
    } else {
      malformed(`${what} names the unknown kind ${kind}`);
    }
    const name = nonEmpty(so.m.get("name"), `${what}.name`);
    if (name === "case" || sources.some((s) => s.name === name)) malformed(`${what}.name ${name} is case or not distinct`);

    const scope: Scope = new Map(caseScope);
    const parameters: SourceParam[] = [];
    if (v === 3) notWrittenEmpty(so, ["parameters"], what);
    if (so.m.has("parameters")) {
      for (const [pname, decl] of object(so.m.get("parameters"), `${what}.parameters`).m) {
        if (pname === "" || pname === "runAt" || caseScope.has(pname)) malformed(`${what}.parameters names ${pname}`);
        const e = exact(decl, `${what}.parameters.${pname}`, ["from", "pointer", "type"]);
        const from = string(e.m.get("from"), `${what}.parameters.${pname}.from`);
        const upstream = sources.find((s) => s.name === from);
        if (upstream === undefined) malformed(`${what}.parameters.${pname} is from ${from}, not an earlier source`);
        const p = pointer(e.m.get("pointer"), `${what}.parameters.${pname}.pointer`);
        if (!upstream!.factTargets.includes(p)) malformed(`${what}.parameters.${pname}.pointer is not a fact target of ${from}`);
        const type = paramType(e.m.get("type"), `${what}.parameters.${pname}.type`);
        parameters.push({ name: pname, from, pointer: p, type });
        scope.set(pname, type);
      }
    }
    scope.set("runAt", "timestamp");
    if (scope.size > BOUNDS.scopeParameters) throw new Refusal("input-over-bound", `${what}'s scope`);

    const read = readRead(so.m.get("read"), scope, `${what}.read`);
    const source: Source = { name, kind, parameters, read, factTargets: [], evidenceTargets: [] };
    if (kind === "selected-file") source.provider = string(so.m.get("provider"), "provider");
    // Each member as its kind's form, held above, gives it: an unbound operation names no profile (§4.4), and a
    // kind of version 3 has no `arguments` but members of its own (§4.3).
    if (so.m.has("profile")) {
      source.profile = nonEmpty(so.m.get("profile"), `${what}.profile`);
      const digest = string(so.m.get("profileDigest"), `${what}.profileDigest`);
      if (!DIGEST.test(digest)) malformed(`${what}.profileDigest is not a digest`);
      source.profileDigest = digest;
    }
    if (so.m.has("maxAge")) source.maxAge = integerIn(so.m.get("maxAge"), 1, 86400, `${what}.maxAge`);
    if (so.m.has("arguments")) {
      source.template = readRequest(so.m.get("arguments"), scope, `${what}.arguments`);
      source.scope = scope;
    }
    if (VERSION_3_KINDS.has(kind)) readVersion3Kind(so, kind, scope, what);
    if (catalog !== undefined) unbound.set(name, catalog);
    if (so.m.has("calculation")) {
      const co = exact(so.m.get("calculation"), `${what}.calculation`, ["inputs", "tables"]);
      const inputs = new Map<string, string>();
      for (const [input, p] of object(co.m.get("inputs"), `${what}.calculation.inputs`).m) {
        const pname = string(p, `${what}.calculation.inputs.${input}`);
        if (pname === "runAt" || !scope.has(pname)) malformed(`${what}.calculation.inputs.${input} names ${pname}`);
        inputs.set(input, pname);
      }
      const tables = new Map<string, number>();
      for (const [table, limit] of object(co.m.get("tables"), `${what}.calculation.tables`).m) {
        tables.set(table, integerIn(limit, 1, 315360000, `${what}.calculation.tables.${table}`));
      }
      source.calculation = { inputs, tables };
    }
    const t = targetsOf(read);
    source.factTargets = t.facts;
    source.evidenceTargets = t.evidence;
    sources.push(source);
  });

  // §8.1: targets across the case and the sources
  const caseFactTargets = caseCopy.facts.map((f) => f.target);
  const caseEvidenceTargets = caseCopy.evidence.map((e) => e.requirement);
  const allFacts: string[] = [...caseFactTargets, ...sources.flatMap((s) => s.factTargets)];
  for (let a = 0; a < allFacts.length; a++) {
    for (let b = a + 1; b < allFacts.length; b++) {
      const x = allFacts[a];
      const y = allFacts[b];
      if (x === y || y.startsWith(x + "/") || x.startsWith(y + "/")) malformed(`the fact targets ${x} and ${y} collide`);
    }
  }
  const allEvidence: string[] = [...caseEvidenceTargets, ...sources.flatMap((s) => s.evidenceTargets)];
  if (new Set(allEvidence).size !== allEvidence.length) malformed("a requirement is an evidence target of two sources");
  if (allFacts.length > BOUNDS.factTargets || allEvidence.length > BOUNDS.evidenceTargets) throw new Refusal("input-over-bound", "targets");

  // §8.2: admits
  const admitsFacts = new Map<string, string[]>();
  const admitsEvidence = new Map<string, string[]>();
  if (o.m.has("admits")) {
    const ad = exact(o.m.get("admits"), "admits", [], ["facts", "evidence"]);
    if (v === 3) notWrittenEmpty(ad, ["facts", "evidence"], "admits");
    if (ad.m.has("facts")) {
      for (const [t, l] of object(ad.m.get("facts"), "admits.facts").m) {
        if (!allFacts.includes(t)) malformed(`admits names the fact target ${t}, which no source writes`);
        admitsFacts.set(t, classList(l, `admits.facts.${t}`));
      }
    }
    if (ad.m.has("evidence")) {
      for (const [r, l] of object(ad.m.get("evidence"), "admits.evidence").m) {
        if (!allEvidence.includes(r)) malformed(`admits names the requirement ${r}, which no source writes`);
        admitsEvidence.set(r, classList(l, `admits.evidence.${r}`));
      }
    }
  }

  if (!inCanonDomain(d)) malformed("the dialect is outside the canon domain");
  return {
    raw: d,
    version: v,
    unbound,
    boundFrom: new Map(),
    caseParams,
    caseCopy,
    caseFacts: c.m.get("facts")!,
    caseEvidence: c.m.get("evidence")!,
    caseFactTargets,
    caseEvidenceTargets,
    sources,
    admitsFacts,
    admitsEvidence,
  };
}

/**
 * §4.3: the members a kind of version 3 names, held to the forms the text gives them; the kind is then not read
 * (`kind-unread`). Where the text names a member without its form — `http`'s `path`, "a template that yields a
 * path", and `headers`, "the names of the headers"; `research`'s `evidence`, "the fields each answer MUST support";
 * a `sql` binding's `name` and `type` — this reader takes a string template for a path and non-empty strings for
 * names. (No vector decides this.)
 */
function readVersion3Kind(so: JObj, kind: string, scope: Scope, what: string): void {
  const stringTemplateOf = (v: JVal | undefined, w: string) => {
    if (v === undefined) return malformed(`${w} is absent`);
    checkTemplate(v, scope, w);
    if (!stringTemplate(v, scope)) malformed(`${w} is not a string template`);
  };
  const names = (v: JVal | undefined, w: string) => array(v, w).forEach((x, k) => nonEmpty(x, `${w}[${k}]`));
  if (kind === "http") {
    const method = string(so.m.get("method"), `${what}.method`);
    if (method !== "GET" && method !== "POST") malformed(`${what}.method is not GET or POST`);
    stringTemplateOf(so.m.get("path"), `${what}.path`);
    if (so.m.has("query")) {
      const query = object(so.m.get("query"), `${what}.query`);
      if (Array.from(query.m.keys()).some((k) => k.startsWith("$"))) malformed(`${what}.query is a template form, not an object`);
      for (const [k, x] of query.m) stringTemplateOf(x, `${what}.query.${k}`);
    }
    if (so.m.has("body")) {
      if (method === "GET") malformed(`${what} has a body beside GET`);
      checkTemplate(so.m.get("body")!, scope, `${what}.body`);
    }
    if (so.m.has("headers")) names(so.m.get("headers"), `${what}.headers`);
  } else if (kind === "sql") {
    string(so.m.get("statement"), `${what}.statement`); // a fixed string, never a template
    array(so.m.get("bindings"), `${what}.bindings`).forEach((x, k) => {
      const w = `${what}.bindings[${k}]`;
      const e = exact(x, w, ["name", "type", "value"]);
      nonEmpty(e.m.get("name"), `${w}.name`);
      nonEmpty(e.m.get("type"), `${w}.type`);
      const value = object(e.m.get("value"), `${w}.value`);
      if (value.m.size !== 1 || !value.m.has("$param")) malformed(`${w}.value is not a $param form`);
      checkTemplate(value, scope, `${w}.value`);
    });
  } else if (kind === "web") {
    const url = so.m.get("url")!;
    if (url.t !== "str") {
      const p = object(url, `${what}.url`);
      if (p.m.size !== 1 || !p.m.has("$param")) malformed(`${what}.url is not a string or a $param form`);
      checkTemplate(p, scope, `${what}.url`);
      if (scope.get((p.m.get("$param") as { v: string }).v) !== "string") malformed(`${what}.url names a parameter that is not a string`);
    }
  } else {
    stringTemplateOf(so.m.get("question"), `${what}.question`);
    object(so.m.get("constraints"), `${what}.constraints`);
    string(so.m.get("model"), `${what}.model`);
    names(so.m.get("evidence"), `${what}.evidence`);
  }
}

// ---- phase 4: the binding document and the bound dialect (§4.4) ----

/** The binding document: exactly `dialect`, a digest, and `sources`, mapping names to objects of exactly `profile`, a
 * non-empty string, and `profileDigest`, a digest. */
export function readBinding(v: JVal): JObj {
  const o = exact(v, "the binding document", ["dialect", "sources"]);
  if (!DIGEST.test(string(o.m.get("dialect"), "the binding document's dialect"))) malformed("the binding document's dialect is not a digest");
  for (const [name, entry] of object(o.m.get("sources"), "the binding document's sources").m) {
    const e = exact(entry, `the binding document's sources.${name}`, ["profile", "profileDigest"]);
    nonEmpty(e.m.get("profile"), `the binding document's sources.${name}.profile`);
    if (!DIGEST.test(string(e.m.get("profileDigest"), `the binding document's sources.${name}.profileDigest`))) {
      malformed(`the binding document's sources.${name}.profileDigest is not a digest`);
    }
  }
  return o;
}

/** The bound dialect: each source the binding document names with its catalog names removed and the profile and its
 * digest the binding gives it added, every other member kept as written. */
export function bindDialect(d: JObj, binding: JObj): JObj {
  const entries = (binding.m.get("sources") as JObj).m;
  const sources = (member(d, "sources") as { a: JVal[] }).a.map((s) => {
    const name = (member(s, "name") as { v: string }).v;
    const entry = entries.get(name);
    if (entry === undefined) return s;
    const kept: [string, JVal][] = Array.from((s as JObj).m).filter(([k]) => !UNBOUND_MEMBERS.includes(k));
    return obj([...kept, ["profile", member(entry, "profile")!], ["profileDigest", member(entry, "profileDigest")!]]);
  });
  return obj(Array.from(d.m).map(([k, x]): [string, JVal] => [k, k === "sources" ? arr(sources) : x]));
}

/**
 * §4.4, verifying it: a dialect with an unbound source is read with its binding document, as the bound dialect, with
 * two checks more. The first is here: the binding is for this dialect, by its digest, and names exactly its unbound
 * sources; and there is a binding document exactly when there is an unbound source. The second is a finding.
 */
export function readBound(dialect: Dialect, bindingValue: JVal | undefined): Dialect {
  const binding = bindingValue === undefined ? undefined : readBinding(bindingValue);
  if (dialect.unbound.size === 0) {
    if (binding !== undefined) malformed("a binding document beside a dialect with no unbound source");
    return dialect;
  }
  if (binding === undefined) return malformed("a dialect with an unbound source and no binding document");
  if ((binding.m.get("dialect") as { v: string }).v !== "sha256:" + sha256hex(canon(dialect.raw))) {
    malformed("the binding document's dialect is not the given dialect's digest");
  }
  const named = Array.from((binding.m.get("sources") as JObj).m.keys());
  if (named.length !== dialect.unbound.size || !named.every((n) => dialect.unbound.has(n))) {
    malformed("the binding document does not name exactly the dialect's unbound sources");
  }
  const bound = readDialect(bindDialect(dialect.raw as JObj, binding));
  bound.boundFrom = dialect.unbound;
  return bound;
}

// ---- phase 4: the profiles (§5.1) ----

export function readProfiles(v: JVal): Profile[] {
  const out: Profile[] = [];
  array(v, "the profiles").forEach((raw, k) => {
    const what = `profiles[${k}]`;
    const o = exact(raw, what, ["id", "publicKey", "class", "source", "authority", "shape", "adapter", "endpoint"], ["tools", "calculator"]);
    const id = nonEmpty(o.m.get("id"), `${what}.id`);
    if (out.some((p) => p.id === id)) malformed(`${what}.id is not distinct`);
    const publicKey = string(o.m.get("publicKey"), `${what}.publicKey`);
    if (!HEX64.test(publicKey)) malformed(`${what}.publicKey is not a key`);
    const key = Uint8Array.from(Buffer.from(publicKey, "hex"));
    if (!keyAcceptable(key)) malformed(`${what}.publicKey is refused by the key rule`);
    const cls = string(o.m.get("class"), `${what}.class`);
    if (cls !== "record" && cls !== "generated") malformed(`${what}.class is not record or generated`);
    const source = string(o.m.get("source"), `${what}.source`);
    const authority = string(o.m.get("authority"), `${what}.authority`);
    const shape = string(o.m.get("shape"), `${what}.shape`);
    if (!SHAPES.has(shape)) malformed(`${what}.shape is not a shape`);
    const adapter = exact(o.m.get("adapter"), `${what}.adapter`, ["name", "version", "digest"]);
    string(adapter.m.get("name"), `${what}.adapter.name`);
    string(adapter.m.get("version"), `${what}.adapter.version`);
    if (!DIGEST.test(string(adapter.m.get("digest"), `${what}.adapter.digest`))) malformed(`${what}.adapter.digest is not a digest`);
    const endpoint = o.m.get("endpoint")!;
    if (endpoint.t !== "str" && endpoint.t !== "null") malformed(`${what}.endpoint is not a string or null`);
    let tools: string[] | undefined;
    if (o.m.has("tools")) {
      tools = array(o.m.get("tools"), `${what}.tools`).map((t, j) => nonEmpty(t, `${what}.tools[${j}]`));
      if (new Set(tools).size !== tools.length) malformed(`${what}.tools is not distinct`);
    }
    if (shape === "mcp" && (tools === undefined || tools.length === 0)) malformed(`${what} is of shape mcp and gives no tools`);
    let calculator: JVal | undefined;
    if (o.m.has("calculator")) {
      const co = exact(o.m.get("calculator"), `${what}.calculator`, ["name", "version"]);
      string(co.m.get("name"), `${what}.calculator.name`);
      string(co.m.get("version"), `${what}.calculator.version`);
      if (cls !== "record" || shape !== "mcp") malformed(`${what} is a calculator's and not of class record and shape mcp`);
      calculator = co;
    }
    out.push({ id, raw, key, publicKey, class: cls, source, authority, shape, adapter, endpoint, tools, calculator });
  });
  return out;
}

export function profileDigestOf(p: Profile): string {
  return "sha256:" + sha256hex(canon(p.raw));
}

export function sha256hex(b: Uint8Array): string {
  return createHash("sha256").update(b).digest("hex");
}

// ---- phase 4: the acquisitions (§5.2) ----

function readSalts(v: JVal | undefined, what: string): JObj {
  const salts = exact(v, what, ["args"], ["statement"]);
  for (const [k, s] of salts.m) if (!HEX64.test(string(s, `${what}.${k}`))) malformed(`${what}.${k} is not 64 hexadecimal characters`);
  return salts;
}

/**
 * §5.2: each acquisition's form. A `research` source's response may lack `receipt` and `salts`, both or neither; its
 * result is the research record, of §4.3's form, each retained response held to its form here, where a missing
 * `result` is no refusal of form but `acquisition-missing` (§5.2). A research source is not read (`kind-unread`), so
 * its acquisition is checked for its form and never as a receipt: one with no receipt of its own carries empty ones.
 */
export function readAcquisitions(v: JVal, research: Set<string> = new Set()): Map<string, Acquisition> {
  const o = object(v, "the acquisitions");
  const out = new Map<string, Acquisition>();
  for (const [name, a] of o.m) {
    const what = `acquisitions.${name}`;
    const response = exact(a, what, ["response"]).m.get("response");
    if (!research.has(name)) {
      const r = exact(response, `${what}.response`, ["result", "receipt", "salts"]);
      const receipt = object(r.m.get("receipt"), `${what}.response.receipt`);
      out.set(name, { result: r.m.get("result")!, receipt, salts: readSalts(r.m.get("salts"), `${what}.response.salts`) });
      continue;
    }
    const r = exact(response, `${what}.response`, ["result"], ["receipt", "salts"]);
    if (r.m.has("receipt") !== r.m.has("salts")) malformed(`${what}.response has one of receipt and salts`);
    const record = exact(r.m.get("result"), `${what}.response.result`, ["responses"]);
    array(record.m.get("responses"), `${what}.response.result.responses`).forEach((x, k) => {
      const w = `${what}.response.result.responses[${k}]`;
      const retained = exact(x, w, ["profile", "request", "receipt", "salts"], ["result"]);
      const p = exact(retained.m.get("profile"), `${w}.profile`, ["id", "digest"]);
      nonEmpty(p.m.get("id"), `${w}.profile.id`);
      if (!DIGEST.test(string(p.m.get("digest"), `${w}.profile.digest`))) malformed(`${w}.profile.digest is not a digest`);
      const request = object(retained.m.get("request"), `${w}.request`);
      if (!inCanonDomain(request)) malformed(`${w}.request is outside the canon domain`);
      object(retained.m.get("receipt"), `${w}.receipt`);
      readSalts(retained.m.get("salts"), `${w}.salts`);
    });
    const receipt = r.m.has("receipt") ? object(r.m.get("receipt"), `${what}.response.receipt`) : obj();
    const salts = r.m.has("salts") ? readSalts(r.m.get("salts"), `${what}.response.salts`) : obj();
    out.set(name, { result: r.m.get("result")!, receipt, salts });
  }
  return out;
}

// ---- phase 4: the preparation's instant, and the record ----

export function readVerifiedAt(prep: JVal): string {
  const v = member(prep, "verifiedAt");
  if (prep.t !== "obj" || v === undefined || v.t !== "str" || instant(v.v) === null) malformed("the preparation's verifiedAt is not a timestamp with an instant");
  return (v as { v: string }).v;
}

export function readRecord(rec: JVal): JObj {
  const o = object(rec, "the record");
  if (member(o, "inputs")?.t !== "obj") malformed("the record has no object inputs");
  for (const k of o.m.keys()) {
    if (k !== "binding" && k.replace(/[A-Z]/g, (ch) => ch.toLowerCase()) === "binding") malformed(`the record names ${k}, binding but for case`);
  }
  return o;
}

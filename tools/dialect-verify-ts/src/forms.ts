// The forms of §§2–8, §5.1 and §5.2, held in phase 4 of §11, and the counts of §12 held in phase 3.
import { createHash } from "node:crypto";
import { BOUNDS } from "./bounds.ts";
import { keyAcceptable } from "./ed25519.ts";
import { pageEndpoint } from "./endpoint.ts";
import { arr, canon, depth, inCanonDomain, isInteger, isPointer, intValue, jsonEqual, member, obj, tokens, utf8 } from "./json.ts";
import type { JNum, JObj, JStr, JVal } from "./json.ts";
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
// §4.3: the kinds version 3 adds but `research`, and the members each names beside §4's, `profile`,
// `profileDigest` and `maxAge`: those it requires, and those it may give.
const VERSION_3_KINDS = new Map<string, { required: string[]; optional: string[] }>([
  ["http", { required: ["method", "path"], optional: ["query", "body", "headers"] }],
  ["sql", { required: ["statement", "bindings"], optional: [] }],
  ["web", { required: ["url"], optional: [] }],
]);
// §4.3, §4.4: a `research` source's members beside §4's, and its three binding members, all or none.
const RESEARCH_MEMBERS = ["maxAge", "question", "constraints", "model", "evidence", "fields", "capabilities"];
const RESEARCH_BINDING = ["profile", "profileDigest", "webProfiles"];
const FIELD_TYPES = new Set(["integer", "decimal", "boolean", "text", "text-list", "range"]);
const CAPABILITIES = ["answer", "search", "page"];
const WEB_CAPABILITIES = ["search", "page"];
// Core §2.2's decimal grammar, matched whole by a `decimal` answer (§4.3).
const DECIMAL = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/;
const INDEX_TOKEN = /^(?:0|[1-9][0-9]*)$/;
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
// `sources`: a reconciliation's earlier research sources, in their order (§6.4)
export type Read = { raw: JVal; unwrap: string[]; copy?: CopyRead; rule?: Rule; sources?: string[] };
/** A research recipe (§4.3): its question, its declared fields' types by name, its capabilities and model, the
 * members of its request but the question, and, bound, each web capability's profile and digest (§4.4). */
export type Research = {
  question: JVal;
  fields: { name: string; type: string; required: boolean }[];
  types: Map<string, string>;
  capabilities: string[];
  model: string;
  request: [string, JVal][];
  web: Map<string, { profile: string; profileDigest: string }>;
};
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
  research?: Research;
  factTargets: string[];
  evidenceTargets: string[];
};

/** An unbound source's `shape` and `record` (§4.4), which the profile it is bound to must serve. */
export type Catalog = { shape: string; record: string };

export type Dialect = {
  raw: JVal;
  version: number; // 2 or 3 (§2)
  unbound: Map<string, Catalog>; // each unbound operation by its name (§4.4)
  unboundResearch: Map<string, string[]>; // each unbound research source by its name: the web capabilities it requests
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
  endpointScope?: string[];
  tools?: string[];
  calculator?: JVal;
  research?: { capabilities: string[]; model?: string }; // §5.1
};

// `own`: whether a research record came back with a receipt of its own (§5.2); every other acquisition has one
export type Acquisition = { result: JVal; receipt: JObj; salts: JObj; own: boolean };

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

const byteLength = (s: string) => utf8(s).length;
const characters = (s: string) => Array.from(s).length;

/** §11's phase 3: a value measured by its field's declared type, when that is one of §4.3's six, against §12's
 * maxima; a value of another form is measured by nothing here. A decimal string is counted in characters. */
function overByType(v: JVal | undefined, type: string | undefined): boolean {
  if (v === undefined) return false;
  if (type === "text") return v.t === "str" && byteLength(v.v) > BOUNDS.textBytes;
  if (type === "text-list") return v.t === "arr" && (v.a.length > BOUNDS.listItems || v.a.some((x) => x.t === "str" && byteLength(x.v) > BOUNDS.itemBytes));
  if (type === "decimal") return v.t === "str" && characters(v.v) > BOUNDS.decimalCharacters;
  if (type === "range") return v.t === "obj" && ["min", "max"].some((k) => { const e = v.m.get(k); return e !== undefined && e.t === "str" && characters(e.v) > BOUNDS.decimalCharacters; });
  return false;
}

/** §12's research maxima (§4.3, §4.4, §5.1, §6.4), counted wherever they can be measured before any form (§11,
 * phase 3): on the dialect's `research` sources, the profiles' research declarations, the binding document's research
 * assignments and each research record. */
function researchWithin(dialect: JVal, acquisitions: JVal, profiles: JVal | undefined, binding: JVal | undefined): boolean {
  const longer = (v: JVal | undefined, limit: number) => v !== undefined && v.t === "str" && byteLength(v.v) > limit;
  const more = (v: JVal | undefined, limit: number) => v !== undefined && ((v.t === "arr" && v.a.length > limit) || (v.t === "obj" && v.m.size > limit));
  // each research source's fields' types: a name declared twice is input-malformed once forms are checked; before
  // that, its answers are measured by the first declaration whose `type` is one of the six
  const declared = new Map<string, Map<string, string>>();
  const sources = member(dialect, "sources");
  for (const s of sources?.t === "arr" ? sources.a : []) {
    const kind = member(s, "kind");
    if (kind?.t !== "str" || kind.v !== "research") continue;
    const types = new Map<string, string>();
    const fields = member(s, "fields");
    if (fields?.t === "arr") {
      if (fields.a.length > BOUNDS.fields) return false;
      for (const d of fields.a) {
        if (d.t !== "obj") continue;
        const name = member(d, "name");
        if (longer(name, BOUNDS.fieldNameBytes) || longer(member(d, "description"), BOUNDS.descriptionBytes)) return false;
        const type = member(d, "type");
        if (name?.t === "str" && !types.has(name.v) && type?.t === "str" && FIELD_TYPES.has(type.v)) types.set(name.v, type.v);
      }
    }
    if (longer(member(s, "model"), BOUNDS.modelBytes)) return false;
    const evidence = member(s, "evidence");
    if (evidence?.t === "arr" && evidence.a.some((x) => longer(x, BOUNDS.evidenceBytes))) return false;
    if (member(s, "capabilities")?.t === "arr" && more(member(s, "capabilities"), BOUNDS.capabilities)) return false;
    if (member(s, "webProfiles")?.t === "obj" && more(member(s, "webProfiles"), BOUNDS.webAssignments)) return false;
    const names = member(member(s, "read"), "sources");
    if (names?.t === "arr" && names.a.length > BOUNDS.readSources) return false;
    const name = member(s, "name");
    if (name?.t === "str" && !declared.has(name.v)) declared.set(name.v, types);
  }
  for (const p of profiles?.t === "arr" ? profiles.a : []) {
    const research = member(p, "research");
    if (research?.t !== "obj") continue;
    if (member(research, "capabilities")?.t === "arr" && more(member(research, "capabilities"), BOUNDS.capabilities)) return false;
    if (longer(member(research, "model"), BOUNDS.modelBytes)) return false;
  }
  const assigned = member(binding, "sources");
  if (assigned?.t === "obj") {
    for (const [name, entry] of assigned.m) {
      const web = declared.has(name) ? member(entry, "webProfiles") : undefined;
      if (web?.t === "obj" && web.m.size > BOUNDS.webAssignments) return false;
    }
  }
  if (acquisitions.t === "obj") {
    for (const [name, a] of acquisitions.m) {
      const types = declared.get(name);
      if (types === undefined) continue;
      const answers = member(member(member(a, "response"), "result"), "fields");
      if (answers?.t !== "obj") continue;
      if (answers.m.size > BOUNDS.fields) return false;
      // every answer's name, declared or not, before any entry is inspected or its declaration looked up
      for (const field of answers.m.keys()) if (byteLength(field) > BOUNDS.fieldNameBytes) return false;
      for (const [field, entry] of answers.m) {
        if (entry.t !== "obj") continue;
        const type = types.get(field);
        const cites = member(entry, "cites");
        if ((cites?.t === "arr" && cites.a.length > BOUNDS.cites) || overByType(member(entry, "value"), type)) return false;
        const values = member(entry, "values");
        if (values?.t !== "arr") continue;
        if (values.a.length > BOUNDS.observations) return false;
        for (const o of values.a) {
          if (o.t !== "obj") continue;
          const oc = member(o, "cites");
          if ((oc?.t === "arr" && oc.a.length > BOUNDS.cites) || overByType(member(o, "value"), type)) return false;
        }
      }
    }
  }
  return true;
}

/** The counts of §12 taken on the documents read, wherever the count can be taken (§11, phase 3). */
export function countsWithin(dialect: JVal, acquisitions: JVal, profiles?: JVal, binding?: JVal): boolean {
  if (!researchWithin(dialect, acquisitions, profiles, binding)) return false;
  for (const p of profiles?.t === "arr" ? profiles.a : []) {
    const scope = member(p, "endpointScope");
    if (scope?.t === "arr" && (scope.a.length > 32
        || scope.a.some((e) => e.t === "str" && utf8(e.v).length > 2048))) return false;
  }
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
  const named = d.t === "obj" && d.m.has("formatVersion");
  const o = exact(d, "the dialect", named ? ["formatVersion", "id", "version", "case"] : ["version", "case"], ["sources", "admits", "unmapped", "unmappedEvidence", "provider", "facts", "evidence"]);
  const version = o.m.get("version")!;
  let v: number;
  if (named) {
    const format = string(o.m.get("formatVersion"), "formatVersion");
    if (format !== "2.0.0" && format !== "3.0.0") malformed("unknown formatVersion");
    const id = string(o.m.get("id"), "id");
    if (!id || utf8(id).length > 1024 || /[\u0000-\u0020\u007f]/u.test(id)) malformed("invalid dialect id");
    const artifact = string(version, "version");
    if (artifact.match(/^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$/)?.[0] !== artifact) malformed("invalid artifact version");
    v = format === "2.0.0" ? 2 : 3;
  } else {
    if (version.t !== "num" || (version.lit !== "2" && version.lit !== "3")) malformed("the dialect's version is not the integer 2 or 3");
    v = Number((version as { lit: string }).lit);
  }
  if (v === 3 || named) {
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
  const unboundResearch = new Map<string, string[]>();
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
    } else if (kind === "research") {
      // §4.3, §4.4: published unbound, with none of the three binding members, or bound, with all three
      if (v === 2) malformed(`${what} names the version-3 kind ${kind} in a version-2 dialect`);
      exact(so, what, [...base, ...RESEARCH_MEMBERS], ["parameters", ...RESEARCH_BINDING]);
      const given = RESEARCH_BINDING.filter((k) => so.m.has(k)).length;
      if (given !== 0 && given !== RESEARCH_BINDING.length) malformed(`${what} has some but not all of profile, profileDigest and webProfiles`);
    } else {
      malformed(`${what} names the unknown kind ${kind}`);
    }
    const name = nonEmpty(so.m.get("name"), `${what}.name`);
    if (name === "case" || sources.some((s) => s.name === name)) malformed(`${what}.name ${name} is case or not distinct`);

    const scope: Scope = new Map(caseScope);
    const parameters: SourceParam[] = [];
    if (v === 3 || named) notWrittenEmpty(so, ["parameters"], what);
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

    const research = kind === "research" ? readResearch(so, scope, what) : undefined;
    const read =
      research === undefined
        ? readRead(so.m.get("read"), scope, `${what}.read`)
        : readResearchRead(so.m.get("read"), scope, `${what}.read`, research, sources);
    const source: Source = { name, kind, parameters, read, research, factTargets: [], evidenceTargets: [] };
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
    if (research !== undefined && !so.m.has("profile")) unboundResearch.set(name, research.capabilities.filter((c) => WEB_CAPABILITIES.includes(c)));
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
    if (v === 3 || named) notWrittenEmpty(ad, ["facts", "evidence"], "admits");
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
    unboundResearch,
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
 * §4.3: the members `http`, `sql` and `web` name, held to the forms the text gives them; the kind is then not read
 * (`kind-unread`). Where the text names a member without its form — `http`'s `path`, "a template that yields a
 * path", and `headers`, "the names of the headers"; a `sql` binding's `name` and `type` — this reader takes a string
 * template for a path and non-empty strings for names. (No vector decides this.) `research` is read (readResearch).
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
  }
}

// ---- phase 4: the research recipe (§4.3), its bound form (§4.4), and its reads (§4.3, §6.4) ----

/** §4.3, §5.1: distinct names from `answer`, `search` and `page`, in that order, one at least; more than three is
 * over a maximum (§12), counted before any form. */
function readCapabilities(v: JVal | undefined, what: string): string[] {
  const names = array(v, what).map((x, k) => string(x, `${what}[${k}]`));
  if (names.length === 0) malformed(`${what} is empty`);
  if (!names.every((n) => CAPABILITIES.includes(n))) malformed(`${what} names a capability other than answer, search and page`);
  for (let k = 1; k < names.length; k++) {
    if (CAPABILITIES.indexOf(names[k - 1]) >= CAPABILITIES.indexOf(names[k])) malformed(`${what} is not distinct, in the order answer, search, page`);
  }
  return names;
}

/** §4.4: exactly `profile`, a non-empty string, and `profileDigest`, a digest. */
function readAssignment(v: JVal | undefined, what: string): { profile: string; profileDigest: string } {
  const o = exact(v, what, ["profile", "profileDigest"]);
  const profile = nonEmpty(o.m.get("profile"), `${what}.profile`);
  const profileDigest = string(o.m.get("profileDigest"), `${what}.profileDigest`);
  if (!DIGEST.test(profileDigest)) malformed(`${what}.profileDigest is not a digest`);
  return { profile, profileDigest };
}

/** §4.4: `webProfiles`, exactly the `search` and `page` capabilities requested as keys, each an assignment. */
function readWebProfiles(v: JVal | undefined, capabilities: string[], what: string): Map<string, { profile: string; profileDigest: string }> {
  const o = object(v, what);
  const requested = capabilities.filter((c) => WEB_CAPABILITIES.includes(c));
  if (o.m.size !== requested.length || !requested.every((c) => o.m.has(c))) malformed(`${what} does not assign exactly the web capabilities requested`);
  return new Map(requested.map((c) => [c, readAssignment(o.m.get(c), `${what}.${c}`)]));
}

/** §4.3: a research recipe's members, each of its form and minimum; its maxima are phase 3's (researchWithin). */
function readResearch(so: JObj, scope: Scope, what: string): Research {
  const question = so.m.get("question")!;
  checkTemplate(question, scope, `${what}.question`);
  if (!stringTemplate(question, scope)) malformed(`${what}.question is not a string template`);
  object(so.m.get("constraints"), `${what}.constraints`);
  const model = nonEmpty(so.m.get("model"), `${what}.model`);
  array(so.m.get("evidence"), `${what}.evidence`).forEach((x, k) => nonEmpty(x, `${what}.evidence[${k}]`));
  const declarations = array(so.m.get("fields"), `${what}.fields`);
  if (declarations.length === 0) malformed(`${what}.fields declares no field`);
  const types = new Map<string, string>();
  const fields = declarations.map((x, k) => {
    const w = `${what}.fields[${k}]`;
    const d = exact(x, w, ["name", "type", "required", "description"]);
    const name = nonEmpty(d.m.get("name"), `${w}.name`);
    if (name === "case") malformed(`${w}.name is case`);
    if (types.has(name)) malformed(`${w}.name ${name} is given twice`);
    const type = string(d.m.get("type"), `${w}.type`);
    if (!FIELD_TYPES.has(type)) malformed(`${w}.type is not one of the six`);
    const required = d.m.get("required")!;
    if (required.t !== "bool") malformed(`${w}.required is not a boolean`);
    nonEmpty(d.m.get("description"), `${w}.description`);
    types.set(name, type);
    return { name, type, required: (required as { v: boolean }).v };
  });
  const capabilities = readCapabilities(so.m.get("capabilities"), `${what}.capabilities`);
  if (capabilities[0] !== "answer") malformed(`${what}.capabilities lacks answer, which is required`);
  const request: [string, JVal][] = ["constraints", "model", "evidence", "fields", "capabilities"].map((k) => [k, so.m.get(k)!]);
  const web = so.m.has("webProfiles") ? readWebProfiles(so.m.get("webProfiles"), capabilities, `${what}.webProfiles`) : new Map();
  return { question, fields, types, capabilities, model, request, web };
}

/** A condition and every condition within it, at any depth. */
function conditionsOf(c: JObj): JObj[] {
  const op = (c.m.get("op") as JStr).v;
  if (op === "all" || op === "any") return [c, ...(c.m.get("of") as { a: JObj[] }).a.flatMap(conditionsOf)];
  if (op === "not") return [c, ...conditionsOf(c.m.get("of") as JObj)];
  return [c];
}

function leavesOf(rule: Rule): JObj[] {
  return rule.clauses.flatMap((cl) => conditionsOf(cl.when)).filter((c) => !["always", "all", "any", "not"].includes((c.m.get("op") as JStr).v));
}

const sameTokens = (a: string[], b: string[]) => a.length === b.length && a.every((x, k) => x === b[k]);

/** §4.3, "Reading fields": a plain research read reads `R` through a closed list of pointers and takes no value from
 * under `values`; or the read is a reconciliation (§6.4). */
function readResearchRead(v: JVal | undefined, scope: Scope, what: string, research: Research, earlier: Source[]): Read {
  if (v !== undefined && v.t === "obj" && v.m.has("sources")) return readReconciliation(v, scope, what, research, earlier);
  const read = readRead(v, scope, what);
  const readable = (p: string, taken: boolean) => {
    const t = tokens(p);
    if (sameTokens(t, ["fields"])) return;
    if (t.length >= 2 && t[0] === "fields" && research.types.has(t[1])) {
      const rest = t.slice(2);
      if (rest.length === 0 || rest[0] === "value" || sameTokens(rest, ["status"]) || sameTokens(rest, ["cites"])) return;
      if (rest.length === 3 && rest[0] === "values" && INDEX_TOKEN.test(rest[1]) && rest[2] === "value") {
        if (taken) malformed(`${what} takes a value from under values`);
        return;
      }
    }
    malformed(`${what} reads ${p}, outside a research read's closed list`);
  };
  // An unwrap pointer takes the value read from where it points: this reader holds it as a from.
  for (const p of read.unwrap) readable(p, true);
  if (read.copy) {
    for (const f of read.copy.facts) readable(f.source, true);
    for (const e of read.copy.evidence) readable(e.source, true);
  } else {
    for (const c of leavesOf(read.rule!)) readable((c.m.get("field") as JStr).v, false);
    for (const cl of read.rule!.clauses) for (const f of cl.claim.facts) readable(f.from, true);
  }
  return read;
}

/** §6.4: exactly `{"op":"equals","field":"<entry>/status","to":S}`. */
function isStatusGuard(c: JVal, entry: string[], status: string): boolean {
  if (c.t !== "obj" || c.m.size !== 3) return false;
  const op = c.m.get("op");
  const field = c.m.get("field");
  const to = c.m.get("to");
  return op?.t === "str" && op.v === "equals" && to?.t === "str" && to.v === status && field?.t === "str" && sameTokens(tokens(field.v), [...entry, "status"]);
}

/** §6.4: exactly `{"op":"not","of":{"op":"exists","field":"<entry>"}}`. */
function isAbsenceGuard(c: JVal, entry: string[]): boolean {
  if (c.t !== "obj" || c.m.size !== 2) return false;
  const op = c.m.get("op");
  const of = c.m.get("of");
  if (op?.t !== "str" || op.v !== "not" || of?.t !== "obj" || of.m.size !== 2) return false;
  const inner = of.m.get("op");
  const field = of.m.get("field");
  return inner?.t === "str" && inner.v === "exists" && field?.t === "str" && sameTokens(tokens(field.v), entry);
}

/** §6.4: `{"sources": [S, ...], "rule": R}` on a version-3 research source, its pointers, froms, guards, evidence and
 * last clause held to the section's forms. */
function readReconciliation(v: JObj, scope: Scope, what: string, research: Research, earlier: Source[]): Read {
  const o = exact(v, what, ["sources", "rule"]);
  const names = array(o.m.get("sources"), `${what}.sources`);
  if (names.length === 0) malformed(`${what}.sources names no source`);
  const declared = new Map<string, Map<string, string>>();
  for (const [k, x] of names.entries()) {
    const n = string(x, `${what}.sources[${k}]`);
    const s = earlier.find((e) => e.name === n);
    if (s === undefined || s.research === undefined) malformed(`${what}.sources[${k}] is not an earlier research source`);
    if (declared.has(n)) malformed(`${what}.sources names ${n} twice`);
    declared.set(n, s!.research!.types);
  }
  const rule = readRule(o.m.get("rule"), scope, `${what}.rule`);
  const entryOf = (p: string): { entry: string[]; rest: string[] } | null => {
    const t = tokens(p);
    if (t.length >= 3 && t[0] === "current" && t[1] === "fields" && research.types.has(t[2])) return { entry: t.slice(0, 3), rest: t.slice(3) };
    if (t.length >= 4 && t[0] === "sources" && declared.has(t[1]) && t[2] === "fields" && declared.get(t[1])!.has(t[3])) return { entry: t.slice(0, 4), rest: t.slice(4) };
    return null;
  };
  for (const c of leavesOf(rule)) {
    const e = entryOf((c.m.get("field") as JStr).v);
    if (e === null || !(e.rest.length === 0 || sameTokens(e.rest, ["status"]) || e.rest[0] === "value" || e.rest[0] === "values")) {
      malformed(`${what} has a condition outside the reconciliation's pointers`);
    }
  }
  const selected: string[][] = [];
  for (const cl of rule.clauses) {
    if (cl.claim.evidence.size !== 0) malformed(`${what} has a claim that writes evidence`);
    for (const f of cl.claim.facts) {
      const e = entryOf(f.from);
      if (e === null || e.rest.length === 0 || e.rest[0] !== "value") malformed(`${what} takes ${f.from}, outside the admissible froms`);
      const op = (cl.when.m.get("op") as JStr).v;
      const guarded = isStatusGuard(cl.when, e!.entry, "found") || (op === "all" && (cl.when.m.get("of") as { a: JVal[] }).a.some((x) => isStatusGuard(x, e!.entry, "found")));
      if (!guarded) malformed(`${what} selects ${f.from} in a clause that does not guard it as found`);
      if (!selected.some((s) => sameTokens(s, e!.entry))) selected.push(e!.entry);
    }
  }
  const every = rule.clauses.flatMap((cl) => conditionsOf(cl.when));
  for (const entry of selected) {
    for (const status of ["not-found", "stale", "conflicting"]) {
      if (!every.some((c) => isStatusGuard(c, entry, status))) malformed(`${what} has no ${status} guard for a selected field`);
    }
    if (!every.some((c) => isAbsenceGuard(c, entry))) malformed(`${what} has no absence guard for a selected field`);
  }
  const last = rule.clauses[rule.clauses.length - 1].claim;
  if (last.facts.length !== 0 || (last.acquisitionStatus !== "unknown" && last.acquisitionStatus !== "absent")) {
    malformed(`${what}'s last clause writes a fact, or is neither unknown nor absent`);
  }
  return { raw: o, unwrap: [], rule, sources: names.map((x) => (x as JStr).v) };
}

// ---- phase 4: the binding document and the bound dialect (§4.4) ----

/** The binding document: exactly `dialect`, a digest, and `sources`, mapping names to assignments: for an `operation`
 * exactly `profile`, a non-empty string, and `profileDigest`, a digest; for `research` those and `webProfiles`. Which
 * form an entry has is the kind of the source it binds (readBound). */
export function readBinding(v: JVal): JObj {
  const o = exact(v, "the binding document", ["dialect", "sources"]);
  if (!DIGEST.test(string(o.m.get("dialect"), "the binding document's dialect"))) malformed("the binding document's dialect is not a digest");
  for (const [name, entry] of object(o.m.get("sources"), "the binding document's sources").m) {
    const e = exact(entry, `the binding document's sources.${name}`, ["profile", "profileDigest"], ["webProfiles"]);
    nonEmpty(e.m.get("profile"), `the binding document's sources.${name}.profile`);
    if (!DIGEST.test(string(e.m.get("profileDigest"), `the binding document's sources.${name}.profileDigest`))) {
      malformed(`the binding document's sources.${name}.profileDigest is not a digest`);
    }
  }
  return o;
}

/** The bound dialect: each operation the binding document names with its catalog names removed and the profile and
 * its digest the binding gives it added; each research source with the three assignment members added; every other
 * member kept as written. */
export function bindDialect(d: JObj, binding: JObj): JObj {
  const entries = (binding.m.get("sources") as JObj).m;
  const sources = (member(d, "sources") as { a: JVal[] }).a.map((s) => {
    const name = (member(s, "name") as { v: string }).v;
    const entry = entries.get(name);
    if (entry === undefined) return s;
    const kept: [string, JVal][] = Array.from((s as JObj).m).filter(([k]) => !UNBOUND_MEMBERS.includes(k));
    const added: [string, JVal][] = [["profile", member(entry, "profile")!], ["profileDigest", member(entry, "profileDigest")!]];
    const web = member(entry, "webProfiles");
    if (web !== undefined) added.push(["webProfiles", web]);
    return obj([...kept, ...added]);
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
  const unboundCount = dialect.unbound.size + dialect.unboundResearch.size;
  if (unboundCount === 0) {
    if (binding !== undefined) malformed("a binding document beside a dialect with no unbound source");
    return dialect;
  }
  if (binding === undefined) return malformed("a dialect with an unbound source and no binding document");
  if ((binding.m.get("dialect") as { v: string }).v !== "sha256:" + sha256hex(canon(dialect.raw))) {
    malformed("the binding document's dialect is not the given dialect's digest");
  }
  const entries = (binding.m.get("sources") as JObj).m;
  const named = Array.from(entries.keys());
  if (named.length !== unboundCount || !named.every((n) => dialect.unbound.has(n) || dialect.unboundResearch.has(n))) {
    malformed("the binding document does not name exactly the dialect's unbound sources");
  }
  for (const [name, entry] of entries) {
    const what = `the binding document's sources.${name}`;
    if (dialect.unbound.has(name)) {
      exact(entry, what, ["profile", "profileDigest"]);
    } else {
      // §4.4: for research, exactly `profile`, `profileDigest` and `webProfiles`, the web capabilities requested
      const e = exact(entry, what, ["profile", "profileDigest", "webProfiles"]);
      readWebProfiles(e.m.get("webProfiles"), dialect.unboundResearch.get(name)!, `${what}.webProfiles`);
    }
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
    const o = exact(raw, what, ["id", "publicKey", "class", "source", "authority", "shape", "adapter", "endpoint"], ["tools", "calculator", "research", "endpointScope"]);
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
    let research: { capabilities: string[]; model?: string } | undefined;
    if (o.m.has("research")) {
      // §5.1: a closed object of `capabilities` and, exactly when they include `answer`, `model`
      const ro = exact(o.m.get("research"), `${what}.research`, ["capabilities"], ["model"]);
      const capabilities = readCapabilities(ro.m.get("capabilities"), `${what}.research.capabilities`);
      if (capabilities.includes("answer") !== ro.m.has("model")) malformed(`${what}.research names a model exactly when it serves answer`);
      research = { capabilities, model: ro.m.has("model") ? nonEmpty(ro.m.get("model"), `${what}.research.model`) : undefined };
    }
    let endpointScope: string[] | undefined;
    if (o.m.has("endpointScope")) {
      if (endpoint.t !== "null" || shape !== "http"
          || (adapter.m.get("name") as JStr).v !== "adapter-web"
          || (research !== undefined
              && (research.capabilities.length !== 1 || research.capabilities[0] !== "page"))
          || (cls === "generated" && research === undefined)) {
        malformed(`${what}: endpointScope is admitted only on page profiles`);
      }
      endpointScope = array(o.m.get("endpointScope"), `${what}.endpointScope`).map((v) => {
        const entry = string(v, `${what}.endpointScope entry`);
        if (entry !== "https://*" && pageEndpoint(entry) === undefined) {
          malformed(`${what}: endpointScope entry is not an endpoint prefix`);
        }
        if (cls === "record" && entry === "https://*") {
          malformed(`${what}: a record profile cannot carry the endpoint wildcard`);
        }
        return entry;
      });
      if (endpointScope.length === 0 || new Set(endpointScope).size !== endpointScope.length) {
        malformed(`${what}: endpointScope must have distinct entries and not be empty`);
      }
    }
    out.push({ id, raw, key, publicKey, class: cls, source, authority, shape, adapter, endpoint,
      endpointScope, tools, calculator, research });
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

/** The exact value of a decimal literal or an integer's, compared without binary floating point: -1, 0 or 1. */
export function compareDecimals(a: string, b: string): number {
  const parts = (s: string) => {
    const m = /^(-?)([0-9]+)(?:\.([0-9]+))?$/.exec(s)!;
    const whole = m[2].replace(/^0+(?=[0-9])/, "");
    const fraction = (m[3] ?? "").replace(/0+$/, "");
    const zero = /^0*$/.test(m[2]) && fraction === "";
    return { negative: m[1] === "-" && !zero, whole, fraction };
  };
  const x = parts(a);
  const y = parts(b);
  if (x.negative !== y.negative) return x.negative ? -1 : 1;
  const sign = x.negative ? -1 : 1;
  if (x.whole.length !== y.whole.length) return (x.whole.length < y.whole.length ? -1 : 1) * sign;
  if (x.whole !== y.whole) return (x.whole < y.whole ? -1 : 1) * sign;
  const n = Math.max(x.fraction.length, y.fraction.length);
  const fx = x.fraction.padEnd(n, "0");
  const fy = y.fraction.padEnd(n, "0");
  return fx === fy ? 0 : (fx < fy ? -1 : 1) * sign;
}

/** §4.3: a value of a field's declared type in its exact encoding; `null` is never one. Maxima are phase 3's. */
function typed(v: JVal | undefined, type: string, what: string): void {
  let ok: boolean;
  if (v === undefined) ok = false;
  else if (type === "integer") ok = isInteger(v);
  else if (type === "decimal") ok = v.t === "str" && DECIMAL.test(v.v);
  else if (type === "boolean") ok = v.t === "bool";
  else if (type === "text") ok = v.t === "str";
  else if (type === "text-list") ok = v.t === "arr" && v.a.every((x) => x.t === "str");
  else if (v.t === "obj" && v.m.size === 2 && v.m.has("min") && v.m.has("max")) {
    const lo = v.m.get("min")!;
    const hi = v.m.get("max")!;
    if (isInteger(lo) && isInteger(hi)) ok = compareDecimals((lo as JNum).lit, (hi as JNum).lit) <= 0;
    else if (lo.t === "str" && hi.t === "str" && DECIMAL.test(lo.v) && DECIMAL.test(hi.v)) ok = compareDecimals(lo.v, hi.v) <= 0;
    else ok = false;
  } else ok = false;
  if (!ok) malformed(`${what} is not a value of the declared type ${type}`);
}

/** §4.3: distinct indices into the record's `responses`, integers from 0 below their number, never `-0`. */
function cites(v: JVal | undefined, responses: number, least: number, what: string): void {
  const items = array(v, what);
  if (items.length < least) malformed(`${what} cites fewer than ${least}`);
  const seen = new Set<number>();
  for (const x of items) {
    if (!isInteger(x) || x.lit === "-0" || intValue(x) < 0 || intValue(x) >= responses) malformed(`${what} holds something other than an index into responses`);
    if (seen.has(intValue(x as JNum))) malformed(`${what} cites an index twice`);
    seen.add(intValue(x as JNum));
  }
}

/** §4.3, "Answers": `R.fields`, an entry for each field it answers, each declared, every required one among them. */
function readAnswers(v: JVal | undefined, research: Research, responses: number, what: string): void {
  const answers = object(v, what);
  for (const name of answers.m.keys()) if (!research.types.has(name)) malformed(`${what} answers ${name}, which is not declared`);
  for (const f of research.fields) if (f.required && !answers.m.has(f.name)) malformed(`${what} has no entry for the required field ${f.name}`);
  for (const [name, entry] of answers.m) {
    const w = `${what}.${name}`;
    const type = research.types.get(name)!;
    const status = member(entry, "status");
    const s = status?.t === "str" ? status.v : undefined;
    if (s === "found") {
      const e = exact(entry, w, ["status", "cites", "value"]);
      cites(e.m.get("cites"), responses, 1, `${w}.cites`);
      typed(e.m.get("value"), type, `${w}.value`);
    } else if (s === "conflicting") {
      const e = exact(entry, w, ["status", "cites", "values"]);
      const outer = e.m.get("cites")!;
      if (outer.t !== "arr" || outer.a.length !== 0) malformed(`${w}.cites of a conflicting entry is not []`);
      const values = array(e.m.get("values"), `${w}.values`);
      if (values.length < 2) malformed(`${w}.values holds fewer than two observations`);
      values.forEach((x, k) => {
        const o = exact(x, `${w}.values[${k}]`, ["value", "cites"]);
        typed(o.m.get("value"), type, `${w}.values[${k}].value`);
        cites(o.m.get("cites"), responses, 1, `${w}.values[${k}].cites`);
      });
      const first = member(values[0], "value")!;
      if (values.every((x) => jsonEqual(first, member(x, "value")!))) malformed(`${w}.values has no two that differ`);
    } else if (s === "not-found" || s === "stale") {
      const e = exact(entry, w, ["status", "cites"]);
      cites(e.m.get("cites"), responses, 0, `${w}.cites`);
    } else {
      malformed(`${w} is not an entry of a known status`);
    }
  }
}

/**
 * §5.2: each acquisition's form. A `research` source's response may lack `receipt` and `salts`, both or neither; its
 * result is the research record, of §4.3's form, its answers held to the source's declarations and each retained
 * response to its form here, where a missing `result` is no refusal of form but `acquisition-missing` (§5.2). A record
 * with no receipt of its own carries empty ones, and `own` false.
 */
export function readAcquisitions(v: JVal, research: Map<string, Research> = new Map()): Map<string, Acquisition> {
  const o = object(v, "the acquisitions");
  const out = new Map<string, Acquisition>();
  for (const [name, a] of o.m) {
    const what = `acquisitions.${name}`;
    const response = exact(a, what, ["response"]).m.get("response");
    const recipe = research.get(name);
    if (recipe === undefined) {
      const r = exact(response, `${what}.response`, ["result", "receipt", "salts"]);
      const receipt = object(r.m.get("receipt"), `${what}.response.receipt`);
      out.set(name, { result: r.m.get("result")!, receipt, salts: readSalts(r.m.get("salts"), `${what}.response.salts`), own: true });
      continue;
    }
    const r = exact(response, `${what}.response`, ["result"], ["receipt", "salts"]);
    if (r.m.has("receipt") !== r.m.has("salts")) malformed(`${what}.response has one of receipt and salts`);
    const record = exact(r.m.get("result"), `${what}.response.result`, ["fields", "responses"]);
    const retainedResponses = array(record.m.get("responses"), `${what}.response.result.responses`);
    retainedResponses.forEach((x, k) => {
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
    readAnswers(record.m.get("fields"), recipe, retainedResponses.length, `${what}.response.result.fields`);
    const receipt = r.m.has("receipt") ? object(r.m.get("receipt"), `${what}.response.receipt`) : obj();
    const salts = r.m.has("salts") ? readSalts(r.m.get("salts"), `${what}.response.salts`) : obj();
    out.set(name, { result: r.m.get("result")!, receipt, salts, own: r.m.has("receipt") });
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

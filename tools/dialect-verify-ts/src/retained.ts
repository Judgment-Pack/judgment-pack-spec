// Exact selected retained-column/1 custody and installation boundary.
import { AsyncLocalStorage } from "node:async_hooks";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { resolve as pathResolve } from "node:path";
import { Refusal, readBound, readDialect } from "./forms.ts";
import { Finding } from "./prepare.ts";
import { BOUNDS, scanBytes } from "./bounds.ts";
import { NotRead, canon, decode, parse, preparationForm, resolve, utf8 } from "./json.ts";
import type { JObj, JVal } from "./json.ts";
import type { Profile, Source } from "./forms.ts";
import * as engine from "./retained-engine.mjs";

const ROOT = fileURLToPath(new URL("../../../", import.meta.url));
export const CAPS = engine.PROFILE_CAPS.base;
const ROLES = Object.keys(engine.ROLE_LIMITS);
const digest = (text: Uint8Array | string) => "sha256:" + createHash("sha256").update(text).digest("hex");
const plain = (v: JVal): any => engine.parse(decode(preparationForm(v)));
const jval = (v: any): JVal => parse(JSON.stringify(v));
const bad = (code = "input-malformed"): never => { throw new Refusal(code, "selected retained-column contract"); };
export const installation = {
  identity(): Record<string, string> {
    const identity = JSON.parse(readFileSync(pathResolve(ROOT, "release-identity.json"), "utf8"));
    const inventory = JSON.parse(readFileSync(pathResolve(ROOT, "releases/v0.3.0-rc.2.retained-column.json"), "utf8"));
    if (identity.tag !== "v0.3.0-rc.2" || identity.releaseVersion !== "0.3.0-rc.2" || identity.specVersion !== "0.3.0"
        || identity.maturity !== "draft" || !/^[0-9a-f]{40}$/.test(identity.sourceCommit)) bad("capability-unsupported");
    for (const [name, sha] of Object.entries(inventory.files)) {
      if (digest(readFileSync(pathResolve(ROOT, name))) !== sha) bad("capability-unsupported");
    }
    return { version: "0.3.0-rc.2", revision: identity.sourceCommit, schemaSha256: inventory.schemaSha256, corpusSha256: inventory.corpusSha256 };
  },
};
type Selection = { selector: any; raw: WeakMap<object, {text:string;start:number;end:number}>; origin: "asserted" | "generated"; profilesBytes: number };
const context = new AsyncLocalStorage<Selection>();
export const selected = () => context.getStore() !== undefined;
const resultEnvelopeBytes=new WeakMap<object,number>();
export function profileBytes(value:number):void { if(context.getStore())context.getStore()!.profilesBytes=value; }
export function rememberEnvelope(result:JVal,response:JVal):void { if (!resultEnvelopeBytes.has(result)) resultEnvelopeBytes.set(result,utf8(rawOf(response)).length); }
export function admitSelection(raw: Uint8Array): Selection {
  if (raw.length > 4096) bad("input-over-bound");
  const s = engine.parse(decode(raw));
  if (!s || Object.keys(s).sort().join() !== "contract,profile,roles,spec" || !s.spec
      || Object.keys(s.spec).sort().join() !== "corpusSha256,revision,schemaSha256,version") bad();
  let expected;
  try { expected = installation.identity(); } catch (e) {
    if (e instanceof Refusal) throw e;
    bad("capability-unsupported");
  }
  if (s.contract !== "retained-column/1" || s.profile !== "base"
      || Object.keys(expected!).some(k => expected![k] !== s.spec[k])) bad("capability-unsupported");
  if (!Array.isArray(s.roles) || !s.roles.length || s.roles.some((v: unknown) => typeof v !== "string" || !ROLES.includes(v))) bad("capability-unsupported");
  if (new Set(s.roles).size !== s.roles.length || s.roles.join() !== ROLES.filter(r => s.roles.includes(r)).join()) bad();
  if (!s.roles.includes("preparation-verification")) bad("capability-unsupported");
  return { selector: s, raw: new WeakMap(), origin: "asserted", profilesBytes: 0 };
}
export function inSelection<T>(selection: Selection, f: () => T): T { return context.run(selection, f); }
export function remember(v: JVal, text: string): void {
  const c = context.getStore();
  if (!c) return;
  c.raw.set(v, {text,start:v.s,end:v.e});
  if (v.t === "obj") for (const child of v.m.values()) remember(child, text);
  else if (v.t === "arr") for (const child of v.a) remember(child, text);
}
function rawOf(v: JVal): string {
  const raw = context.getStore()?.raw.get(v);
  if (raw === undefined) bad("read-failed");
  return raw.text.slice(raw.start,raw.end);
}
export function retainedRule(v: JVal, availability = false): JObj {
  if (!selected()) bad("capability-unsupported");
  let rule = plain(v);
  if (availability) {
    if (Object.keys(rule).sort().join() !== "column,contractVersion") bad();
    rule = { ...rule, kind: "evidence-availability" };
  }
  if (!availability && !["text","decimal","number","boolean","research-value"].includes(rule.kind)) bad();
  engine.validate(rule, { contractVersion: "1", origin: "asserted", values: {}, research: null }, "base");
  return v as JObj;
}
export function applyColumn(value: JVal, pointer: string, rule: JObj, availability = false): { fragment: JObj; value?: JVal } {
  const frame = resolve(value, pointer);
  if (!frame) throw new Finding("read-failed", "the bound retained frame is missing");
  const f = engine.parse(rawOf(frame));
  if (f.origin !== context.getStore()!.origin) throw new Finding("read-failed", "retained frame origin differs from bound occurrence");
  const r = plain(rule);
  if (availability) r.kind = "evidence-availability";
  const fragment = engine.lineage({ rule: r, frame: f, profile: "base" }, utf8(rawOf(frame)).length);
  return { fragment: jval(fragment) as JObj, value: fragment.result.state === "value" ? parse(fragment.result.json) : undefined };
}
export function selectedPreparation(prep: JObj): void {
  const c = context.getStore();
  if (c) prep.m.set("conversionContract", jval(c.selector));
}
export function validateCapabilities(v: JVal | undefined, required?: string, producer = false): Record<string,number> | undefined {
  if (!v || v.t !== "arr" || v.a.length > 32) bad();
  const entries = plain(v), seen = new Set();
  let limits:Record<string,number>|undefined;
  for (const e of entries) {
    const keys = Object.keys(e).sort().join();
    if (keys !== "contract,limits,profile,role,spec" && keys !== "contract,limits,producerGrammar,profile,role,spec") bad();
    if (!e.spec || Object.keys(e.spec).sort().join() !== "corpusSha256,revision,schemaSha256,version") bad();
    if (e.contract !== "retained-column/1" || e.profile !== "base" || !ROLES.includes(e.role)
        || Object.keys(context.getStore()!.selector.spec).some(k => e.spec[k] !== context.getStore()!.selector.spec[k])) bad("capability-unsupported");
    if (e.producerGrammar !== undefined && (!["preparation", "preparation-verification", "producer-carrier"].includes(e.role) || e.producerGrammar !== "desk-reviewed-input/1")) bad("capability-unsupported");
    const key = e.role + "/" + (e.producerGrammar ?? "");
    if (seen.has(key)) bad();
    seen.add(key);
    const names = engine.ROLE_LIMITS[e.role];
    if (!e.limits || Object.keys(e.limits).sort().join() !== [...names].sort().join()) bad();
    for (const name of names) {
      if (!/^[1-9][0-9]{0,15}$/.test(e.limits[name]?.text ?? "") || BigInt(e.limits[name].text) > 9007199254740991n) bad();
    }
    if (e.role === required && (!producer || e.producerGrammar === "desk-reviewed-input/1")) {
      limits=Object.fromEntries(names.map((k:string)=>[k,Math.min(CAPS[k],Number(e.limits[k].text))]));
    }
  }
  if (required && !limits) bad("capability-unsupported");
  return limits;
}
export function retainedProfile(p: JObj): void {
  if (p.m.has("conversionContracts")) validateCapabilities(p.m.get("conversionContracts"));
  const pin = p.m.get("retainedColumnProducer");
  if (pin) {
    const v = plain(pin);
    if (Object.keys(v).sort().join() !== "contractVersion,grammar") bad();
    if (v.contractVersion !== "1" || v.grammar !== "desk-reviewed-input/1") bad("capability-unsupported");
  }
}
export function producer(source: Source, p: Profile, result?: JVal, receipt?: JObj): void {
  const leaves = [...(source.read.copy?.facts ?? []).filter(e => e.conversion), ...(source.read.copy?.evidence ?? []).filter(e => e.availability)];
  if (!leaves.length) return;
  if (!context.getStore()?.selector.roles.includes("producer-carrier")) bad("capability-unsupported");
  const profile = plain(p.raw);
  if (!profile.retainedColumnProducer || !profile.conversionContracts) bad("capability-unsupported");
  const trust: any = {};
  for (const k of ["id", "class", "source", "authority", "shape", "endpoint", "adapter", "tools", "retainedColumnProducer"]) trust[k] = profile[k];
  // Profile digest is checked independently by the existing owner before this call.
  trust.profileDigest = source.profileDigest;
  const binding = { kind: source.kind, profile: source.profile, profileDigest: source.profileDigest };
  engine.producerContext(trust, binding);
  const limits=validateCapabilities((p.raw as JObj).m.get("conversionContracts"), "producer-carrier", true)!;
  if(context.getStore()!.profilesBytes>limits.profilesBytes)bad("input-over-bound");
  if (source.read.unwrap.length || source.calculation || leaves.some(e => e.source !== "/retained")) throw new Finding("profile-mismatch", "generated conversion requires directly bound carrier");
  if (!result) return;
  context.getStore()!.origin = "generated";
  // The exact retained envelope is measured by restore/readAcquisitions; this is
  // the producer's independently lower response ceiling, including receipt/salts.
  const received=resultEnvelopeBytes.get(result);
  if(received===undefined)bad("read-failed");
  if(received!==undefined && received>limits.responseBytes)bad("input-over-bound");
  const first = leaves[0] as any;
  const rule = plain(first.conversion ?? first.availability);
  if (first.availability) rule.kind = "evidence-availability";
  const raw = `{"generatedConsistency":{"carrier":${rawOf(result)},"profile":"base","limits":{"originalSnapshotBytes":${limits.originalSnapshotBytes},"carrierBytes":${limits.carrierBytes}},"trustedProducer":${JSON.stringify(trust)},"sourceBinding":${JSON.stringify(binding)},"receiptResultDigest":${JSON.stringify((receipt!.m.get("resultDigest") as any).v)},"rule":${decode(preparationForm(first.conversion ?? first.availability))}}}`;
  const request = engine.parse(raw);
  if (first.availability) request.generatedConsistency.rule.kind = "evidence-availability";
  engine.generatedConsistency(request.generatedConsistency);
}
function boundedText(text: string, nesting: number): JVal {
  const scan = scanBytes(utf8(text));
  if (scan.nesting > nesting || !scan.numbersWithin) bad("input-over-bound");
  return parse(text);
}
export function restoreCase(v: JVal): JVal {
  if (v.t !== "obj" || !v.m.has("retainedCaseJson")) return v;
  if (v.m.size !== 1) bad();
  const text = v.m.get("retainedCaseJson");
  if (text?.t !== "str" || !text.v) bad();
  const result = boundedText(text.v, BOUNDS.readNesting);
  if (result.t !== "obj") bad();
  remember(result, text.v);
  return result;
}
export function restoreAcquisitions(v: JVal): void {
  if (v.t !== "obj") return;
  for (const [name, slot] of v.m) {
    if (slot.t !== "obj" || !slot.m.has("retainedResponseJson")) continue;
    if (slot.m.size !== 1) bad();
    const text = slot.m.get("retainedResponseJson");
    if (text?.t !== "str" || !text.v) bad();
    if (utf8(text.v).length > CAPS.responseBytes) bad("input-over-bound");
    const response = boundedText(text.v, BOUNDS.documentNesting);
    if (response.t !== "obj") bad();
    remember(response, text.v);
    resultEnvelopeBytes.set(response.m.get("result")!,utf8(text.v).length);
    slot.m.clear(); slot.m.set("response", response);
  }
}
export function translateError(e: unknown): never {
  if (e instanceof NotRead) bad("input-malformed");
  if (e instanceof engine.Refusal) {
    if (["read-failed", "profile-mismatch", "acquisition-invalid"].includes(e.message)) throw new Finding(e.message, "selected retained-column reading");
    bad(e.message);
  }
  throw e;
}

export function sourceDocuments(raw: Uint8Array): { dialect: Uint8Array; case: Uint8Array; acquisitions: Uint8Array; binding?: Uint8Array } {
  if (raw.length > CAPS.combinedBytes) bad("input-over-bound");
  const text=decode(raw), source=boundedText(text, BOUNDS.documentNesting); remember(source,text);
  if (source.t!=="obj") bad();
  const required=["conversionContract","mapping"], optional=["case","retainedCaseJson","sources","import","snapshot","mappingDigest"];
  if (required.some(k=>!source.m.has(k)) || [...source.m.keys()].some(k=>!required.includes(k)&&!optional.includes(k))) bad();
  admitSelection(utf8(rawOf(source.m.get("conversionContract")!)));
  if(decode(canon(source.m.get("conversionContract")!))!==decode(canon(jval(context.getStore()!.selector))))bad("capability-unsupported");
  if(source.m.get("mapping")?.t!=="obj" || source.m.has("sources")&&source.m.get("sources")?.t!=="obj" || source.m.has("case")&&source.m.get("case")?.t!=="obj")bad();
  const retainedCase=source.m.get("retainedCaseJson");
  if(retainedCase && (retainedCase.t!=="str" || !retainedCase.v))bad();
  if (source.m.has("case")&&source.m.has("retainedCaseJson")) bad();
  let dialect=utf8(rawOf(source.m.get("mapping")!));
  if (dialect.length>CAPS.documentBytes) bad("input-over-bound");
  const mappingDigest=source.m.get("mappingDigest");
  if (mappingDigest && (mappingDigest.t!=="str" || mappingDigest.v!==digest(canon(source.m.get("mapping")!)))) throw new Finding("read-failed","stored mapping differs from its digest");
  const caseBytes=source.m.has("retainedCaseJson") ? utf8(JSON.stringify({retainedCaseJson:(source.m.get("retainedCaseJson") as any).v}))
    : source.m.has("case") ? utf8(rawOf(source.m.get("case")!)) : utf8("{}");
  const acquisitions=source.m.has("sources") ? utf8(rawOf(source.m.get("sources")!)) : utf8("{}");
  let binding: Uint8Array|undefined;
  const imported=source.m.get("import");
  if (imported) {
    if (imported.t!=="obj" || imported.m.size!==2 || !imported.m.has("dialect") || !imported.m.has("binding")) bad();
    dialect=utf8(rawOf(imported.m.get("dialect")!)); binding=utf8(rawOf(imported.m.get("binding")!));
    if (dialect.length>CAPS.documentBytes || binding.length>65536) bad("input-over-bound");
    const bound=readBound(readDialect(imported.m.get("dialect")!),imported.m.get("binding"));
    if (decode(canon(bound.raw))!==decode(canon(source.m.get("mapping")!))) throw new Finding("read-failed","retained published and bound mappings differ");
  }
  return {dialect,case:caseBytes,acquisitions,binding};
}
export function exportInputs(raw: Uint8Array): { retained: {source:Uint8Array;preparation:Uint8Array}[]; audit:Uint8Array } {
  if (raw.length>CAPS.exportWireBytes) bad("input-over-bound");
  const text=decode(raw),doc=boundedText(text, BOUNDS.documentNesting); remember(doc,text);
  if (doc.t!=="obj" || !["version","releaseDigest","release","run"].every(k=>doc.m.has(k)) || [...doc.m.keys()].some(k=>!["version","releaseDigest","release","run","chain"].includes(k))) bad();
  const version=doc.m.get("version");
  if (version?.t!=="num" || !["2","3","4","5"].includes(version.lit)) bad();
  const release=doc.m.get("release"),run=doc.m.get("run");
  if (release?.t!=="obj" || run?.t!=="obj") bad();
  if (utf8(rawOf(release)).length>CAPS.releaseStoredBytes || utf8(rawOf(run)).length>CAPS.runStoredBytes) bad("input-over-bound");
  if(Number(version.lit)>=3&&!run.m.has("auditBytes") || Number(version.lit)>=4&&!doc.m.has("chain") || version.lit==="5"&&!run.m.has("auditSignatures"))bad();
  let base=raw.length;
  const binary=(name:string,cap:number,minimum:number):Uint8Array|undefined=>{
    const value=run.m.get(name);if(!value)return;
    if(Number(version.lit)<minimum || value.t!=="str" || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value.v))bad();
    const bytes=Uint8Array.from(Buffer.from(value.v,"base64"));if(bytes.length>cap)bad("input-over-bound");
    base-=utf8(rawOf(value)).length+JSON.stringify(name).length+2;return bytes;
  };
  let audit=binary("auditBytes",CAPS.recordBytes,3);binary("auditSignatures",16384,5);
  const chain=doc.m.get("chain");
  if(chain){
    if(Number(version.lit)<4 || chain.t!=="obj" || chain.m.size!==2 || !chain.m.has("entry") || !chain.m.has("checkpoint"))bad();
    const entry=chain.m.get("entry"),checkpoint=chain.m.get("checkpoint");
    if(entry?.t!=="str" || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(entry.v) || checkpoint?.t!=="obj" || checkpoint.m.size!==4 || !["checkpointVersion","recordDigest","sequence","trail"].every(k=>checkpoint.m.has(k)))bad();
    if(Buffer.from(entry.v,"base64").length>1024 || utf8(rawOf(checkpoint)).length>185)bad("input-over-bound");
    base-=utf8(rawOf(chain)).length+',"chain":'.length;
  }
  if(base>CAPS.exportBaseBytes)bad("input-over-bound");
  if(!audit){const value=run.m.get("audit");if(!value)bad();audit=utf8(rawOf(value));}
  if(audit.length>CAPS.recordBytes)bad("input-over-bound");
  const visible=run.m.get("audit");
  if(visible?.t!=="obj" || decode(preparationForm(parse(decode(audit))))!==decode(preparationForm(visible)))throw new Finding("record-inputs-differ","visible audit differs from retained audit bytes");
  const retained=[];
  for(const [parent,name] of [[release,"sample"],[run,"input"]] as const){
    const input=parent.m.get(name);
    if(input?.t!=="obj" || input.m.get("source")?.t!=="obj" || input.m.get("preparation")?.t!=="obj")bad();
    retained.push({source:utf8(rawOf(input.m.get("source")!)),preparation:utf8(rawOf(input.m.get("preparation")!))});
  }
  const mapping=release.m.get("inputMapping");
  if(mapping?.t!=="obj")bad();
  if(utf8(rawOf(mapping)).length>CAPS.documentBytes)bad("input-over-bound");
  for(const [parent,name] of [[release,"sample"],[run,"input"]] as const){
    const input=parent.m.get(name) as JObj,source=input.m.get("source") as JObj;
    if(decode(canon(source.m.get("mapping")!))!==decode(canon(mapping)))throw new Finding("read-failed","release mapping differs from retained input mapping");
  }
  return {retained,audit};
}

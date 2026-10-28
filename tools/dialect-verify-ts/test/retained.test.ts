// Both readers consume these same handwritten full-preparation expectations.
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import test from "node:test";
import assert from "node:assert/strict";
import { verify, verifySourceInput, verifyExport } from "../src/verify.ts";
import { installation, selected, CAPS, translateError } from "../src/retained.ts";
import { parse, preparationForm, utf8, decode } from "../src/json.ts";
const corpus = JSON.parse(readFileSync(new URL("../../../conformance/retained-column/1/preparations.json", import.meta.url), "utf8"));
function inputs(row: any, selector = corpus.selector) {
  return { dialect: utf8(row.dialectJson), case: utf8(row.caseJson), acquisitions: utf8(row.acquisitionsJson), profiles: utf8(row.profilesJson), preparation: utf8(row.preparationJson), requireBinding: false, conversionContract: utf8(JSON.stringify(selector)) };
}
// The real installation check, exercised on a disposable copy of a v0.3.0 installation.
test("installed identity is the v0.3.0 distribution", async () => {
  const repo = fileURLToPath(new URL("../../../", import.meta.url));
  const root = mkdtempSync(join(tmpdir(), "retained-installation-"));
  try {
    const inventoryPath = "releases/v0.3.0.retained-column.json";
    const inventory = JSON.parse(readFileSync(join(repo, inventoryPath), "utf8"));
    for (const name of [inventoryPath, ...Object.keys(inventory.files)]) {
      mkdirSync(dirname(join(root, name)), { recursive: true });
      copyFileSync(join(repo, name), join(root, name));
    }
    const installed = await import(pathToFileURL(join(root, "tools/dialect-verify-ts/src/retained.ts")).href);
    const commit = "a".repeat(40);
    const final = { releaseVersion: "0.3.0", tag: "v0.3.0", specVersion: "0.3.0", maturity: "draft", sourceCommit: commit };
    const write = (identity: object) => writeFileSync(join(root, "release-identity.json"), JSON.stringify(identity));
    const spec = { version: "0.3.0", revision: commit, schemaSha256: inventory.schemaSha256, corpusSha256: inventory.corpusSha256 };
    const select = (version: string) => installed.admitSelection(utf8(JSON.stringify({ contract: "retained-column/1",
      spec: { ...spec, version }, profile: "base", roles: ["preparation-verification"] })));
    const unsupported = (error: any) => error.code === "capability-unsupported";
    write(final);
    assert.deepEqual(installed.installation.identity(), spec);
    assert.equal(select("0.3.0").selector.spec.version, "0.3.0");
    assert.throws(() => select("0.3.0-rc.2"), unsupported);
    for (const changed of [{ tag: "v0.3.0-rc.2", releaseVersion: "0.3.0-rc.2" }, { releaseVersion: "0.3.0-rc.2" },
                           { maturity: "candidate" }, { sourceCommit: "A".repeat(40) }]) {
      write({ ...final, ...changed });
      assert.throws(() => installed.installation.identity(), unsupported);
    }
    write(final);
    const listed = join(root, inventoryPath);
    writeFileSync(listed, JSON.stringify({ ...inventory, distribution: "v0.3.0-rc.2" }));
    assert.throws(() => installed.installation.identity(), unsupported);
    copyFileSync(join(repo, inventoryPath), listed);
    const pinned = join(root, inventory.corpus);
    writeFileSync(pinned, readFileSync(pinned, "utf8") + " ");
    assert.throws(() => installed.installation.identity(), unsupported);
    copyFileSync(join(repo, inventory.corpus), pinned);
    assert.deepEqual(installed.installation.identity(), spec);
    rmSync(join(root, "release-identity.json"));
    assert.throws(() => select("0.3.0"), unsupported);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
installation.identity = () => corpus.testInstallation;
for (const row of corpus.cases) test(row.id, () => {
  const result = verify(inputs(row));
  if (row.expected === "reading") {
    assert.equal(result.kind, "reading", result.why);
    assert.equal(decode(result.recomputed!), decode(preparationForm(parse(row.preparationJson))));
  } else {
    const [kind, code] = row.expected.split(":");
    assert.equal(result.kind, kind);
    const report = JSON.parse(decode(preparationForm(result.report)));
    assert.equal(report[kind === "refusal" ? "refusal" : "finding"], code);
  }
  assert.equal(selected(), false);
});
test("selector admitted before artifacts", () => {
  const row = {dialectJson:"",caseJson:"",acquisitionsJson:"",profilesJson:"",preparationJson:""};
  const selector=structuredClone(corpus.selector); selector.spec.revision="f".repeat(40);
  assert.equal(JSON.parse(decode(preparationForm(verify(inputs(row,selector)).report))).refusal,"capability-unsupported");
});
test("no selector keeps ordinary closed grammar", () => {
  const input=inputs(corpus.cases[0]); delete (input as any).conversionContract;
  const result=verify(input);
  assert.equal(result.kind,"refusal");
  assert.equal(JSON.parse(decode(preparationForm(result.report))).refusal,"input-malformed");
});

for(const row of corpus.cases.filter((r:any)=>r.expected==="reading"))test("complete source "+row.id,()=>{
 const result=verifySourceInput(utf8(row.sourceInputJson),utf8(row.profilesJson),utf8(row.preparationJson),utf8(JSON.stringify(corpus.selector)));
 assert.equal(result.kind,"reading",result.why);
});
for(const row of corpus.exports)test(row.id,()=>{
 const result=verifyExport(utf8(row.wireJson),utf8("[]"),utf8(JSON.stringify(corpus.selector)),true);
 if(row.expected==="reading") assert.equal(result.kind,"reading",result.why);
 else {const [kind,code]=row.expected.split(":");assert.equal(result.kind,kind);assert.equal(JSON.parse(decode(preparationForm(result.report)))[kind==="refusal"?"refusal":"finding"],code);}
});
test("source selector agreement and third release mapping",()=>{
 const row=corpus.cases[0],source=JSON.parse(row.sourceInputJson);source.conversionContract.roles.pop();
 let result=verifySourceInput(utf8(JSON.stringify(source)),utf8("[]"),utf8(row.preparationJson),utf8(JSON.stringify(corpus.selector)));
 assert.equal(JSON.parse(decode(preparationForm(result.report))).refusal,"capability-unsupported");
 const doc=JSON.parse(corpus.exports[0].wireJson);doc.release.inputMapping.profile="extended";
 result=verifyExport(utf8(JSON.stringify(doc)),utf8("[]"),utf8(JSON.stringify(corpus.selector)));
 assert.equal(JSON.parse(decode(preparationForm(result.report))).finding,"read-failed");
});

test("selected document profiles and preparation byte boundaries",()=>{
 for(const [field,member] of [["dialectJson","documentBytes"],["profilesJson","profilesBytes"],["preparationJson","preparationBytes"]] as const){
  const row=structuredClone(corpus.cases[0]);row[field]=row[field].padEnd(CAPS[member]," ");
  assert.equal(verify(inputs(row)).kind,"reading",field+" exact cap");
  row[field]+=" ";const result=verify(inputs(row));
  assert.equal(JSON.parse(decode(preparationForm(result.report))).refusal,"input-over-bound",field+" one over");
 }
});

test("complete selector and transformation binding",()=>{
 const row=structuredClone(corpus.cases[0]);
 row.preparationJson=row.preparationJson.replace('"location":"values"','"location":"research-value"');
 let result=verify(inputs(row));
 assert.equal(JSON.parse(decode(preparationForm(result.report))).finding,"preparation-differs");
 const prep=JSON.parse(corpus.cases[0].preparationJson);prep.conversionContract.roles.pop();row.preparationJson=JSON.stringify(prep);
 result=verify(inputs(row));assert.equal(JSON.parse(decode(preparationForm(result.report))).finding,"preparation-differs");
});


for(const c of corpus.readerBoundaryCases)test("review boundary "+c.id,()=>{
 const row={...structuredClone(corpus.cases.find((r:any)=>r.id===c.baseCaseId)),...c};
 const selector=c.selectorHex?Uint8Array.from(Buffer.from(c.selectorHex,"hex")):utf8(JSON.stringify(corpus.selector));
 let result:ReturnType<typeof verify>;
 assert.doesNotThrow(()=>{
  if(c.entrypoint==="verify")result=verify({...inputs(row),conversionContract:selector});
  else {
   const artifact=c.artifactHex?Uint8Array.from(Buffer.from(c.artifactHex,"hex")):utf8(c.entrypoint==="source-input"?row.sourceInputJson:(row.wireJson??corpus.exports[0].wireJson));
   result=c.entrypoint==="source-input"?verifySourceInput(artifact,utf8(row.profilesJson),utf8(row.preparationJson),selector):verifyExport(artifact,utf8(row.profilesJson),selector);
  }
 },c.id+" exported API must report the reading/refusal");
 if(c.expected==="reading"){
  assert.equal(result!.kind,"reading",result!.why);
  assert.equal(decode(result!.recomputed!),decode(preparationForm(parse(row.preparationJson))));
 }else {
  const [kind,code]=c.expected.split(":");assert.equal(result!.kind,kind,c.id);
  assert.equal(JSON.parse(decode(preparationForm(result!.report)))[kind==="refusal"?"refusal":"finding"],code,c.id);
 }
 assert.equal(selected(),false);
});
test("selected error translation preserves program faults",()=>{
 const fault=new Error("program-fault");assert.throws(()=>translateError(fault),(error)=>error===fault);
});

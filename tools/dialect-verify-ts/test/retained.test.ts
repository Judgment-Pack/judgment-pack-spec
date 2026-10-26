// Both readers consume these same handwritten full-preparation expectations.
import { readFileSync } from "node:fs";
import test from "node:test";
import assert from "node:assert/strict";
import { verify, verifySourceInput, verifyExport } from "../src/verify.ts";
import { installation, selected, CAPS } from "../src/retained.ts";
import { parse, preparationForm, utf8, decode } from "../src/json.ts";
const corpus = JSON.parse(readFileSync(new URL("../../../conformance/retained-column/1/preparations.json", import.meta.url), "utf8"));
function inputs(row: any, selector = corpus.selector) {
  return { dialect: utf8(row.dialectJson), case: utf8(row.caseJson), acquisitions: utf8(row.acquisitionsJson), profiles: utf8(row.profilesJson), preparation: utf8(row.preparationJson), requireBinding: false, conversionContract: utf8(JSON.stringify(selector)) };
}
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

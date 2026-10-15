// Every staged dialect vector, read by this verifier and held to the class's expected answer in
// conformance/dialect/manifest.json; and, byte for byte, the recomputed preparation to the vector's
// preparation.json, its digest to preparation.sha256, and a reading's facts and evidence-availability
// documents to the export's run.input.facts and run.input.evidence (conformance/dialect/README.md).
import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { bindDialect, readBinding } from "../src/forms.ts";
import { member, preparationForm, read } from "../src/json.ts";
import type { JObj, JVal } from "../src/json.ts";
import { loadVector } from "../src/vector.ts";
import { verify } from "../src/verify.ts";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "conformance", "dialect");
const manifest = JSON.parse(readFileSync(join(ROOT, "manifest.json"), "utf8")) as {
  cases: { id: string; path: string; requiresBinding: boolean; expectedResult: string; expectedBinding?: string; expectedFinding?: string }[];
};

// A vector the text does not let this reader answer, by id, with the reason. None today: every vector
// was read from the companion document's text alone (README.md, "Where the text was not enough").
const KNOWN_DISAGREEMENTS: Record<string, string> = {};

const written = (v: JVal | undefined) => (v === undefined ? "absent" : Buffer.from(preparationForm(v)).toString("utf8"));

test("the manifest names every vector directory, and nothing else", () => {
  const dirs = readdirSync(join(ROOT, "vectors"))
    .filter((d) => statSync(join(ROOT, "vectors", d)).isDirectory())
    .sort();
  assert.deepEqual(manifest.cases.map((c) => c.path.replace(/^vectors\//, "")).sort(), dirs);
  assert.equal(manifest.cases.length, 12);
});

for (const row of manifest.cases) {
  test(`vector ${row.id}`, (t) => {
    if (row.id in KNOWN_DISAGREEMENTS) {
      t.todo(`known disagreement: ${KNOWN_DISAGREEMENTS[row.id]}`);
      return;
    }
    const dir = join(ROOT, row.path);
    const result = verify(loadVector(dir, row.requiresBinding));
    const report = result.report;
    const field = (k: string) => (member(report, k) as { v: string } | undefined)?.v;
    assert.equal(result.kind, row.expectedResult, `${row.id}: ${written(report)} (${result.why ?? ""})`);
    if (row.expectedResult === "reading") assert.equal(field("binding"), row.expectedBinding);
    if (row.expectedResult === "finding") assert.equal(field("finding"), row.expectedFinding);

    // the recomputed preparation's canonical bytes, and their digest
    assert.ok(result.recomputed !== undefined, `${row.id}: the preparation was not recomputed`);
    assert.ok(Buffer.from(result.recomputed!).equals(readFileSync(join(dir, "preparation.json"))), `${row.id}: preparation.json`);
    if (row.expectedResult === "reading") {
      assert.equal(field("digest"), readFileSync(join(dir, "preparation.sha256"), "utf8"));
      const run = read(Uint8Array.from(readFileSync(join(dir, "run.json")))).value;
      const input = member(member(run, "run"), "input");
      assert.equal(written(member(report, "facts")), written(member(input, "facts")), `${row.id}: the facts document`);
      assert.equal(written(member(report, "evidence")), written(member(input, "evidence")), `${row.id}: the evidence-availability document`);
    }

    // a vector of a dialect bound at import: the bound dialect is its mapping.json, which, given as the dialect with
    // no binding document, is read alike (§4.4)
    if (existsSync(join(dir, "binding.json"))) {
      const bound = bindDialect(read(Uint8Array.from(readFileSync(join(dir, "unbound.json")))).value as JObj, readBinding(read(Uint8Array.from(readFileSync(join(dir, "binding.json")))).value));
      assert.equal(written(bound), written(read(Uint8Array.from(readFileSync(join(dir, "mapping.json")))).value), `${row.id}: the bound dialect`);
      const direct = verify({ ...loadVector(dir, row.requiresBinding), dialect: Uint8Array.from(readFileSync(join(dir, "mapping.json"))), binding: undefined });
      assert.equal(direct.kind, row.expectedResult, `${row.id}: mapping.json given as the dialect`);
      assert.ok(Buffer.from(direct.recomputed!).equals(readFileSync(join(dir, "preparation.json"))), `${row.id}: mapping.json given as the dialect`);
    }
  });
}

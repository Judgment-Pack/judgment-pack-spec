// Every staged dialect vector, read by this verifier and held to the class's expected answer in
// conformance/dialect/manifest.json; and, byte for byte, the recomputed preparation to the vector's
// preparation.json, its digest to preparation.sha256, and a reading's facts and evidence-availability
// documents to the export's run.input.facts and run.input.evidence (conformance/dialect/README.md).
// A vector the Runner's manifest marks `retained: "recorded"` is not recomputed: its inputs were
// changed after the run, and its preparation.json, the preparation the run recorded, is held to the
// manifest's digest.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { bindDialect, readBinding } from "../src/forms.ts";
import { member, preparationForm, read } from "../src/json.ts";
import type { JObj, JVal } from "../src/json.ts";
import { loadVector } from "../src/vector.ts";
import { verify } from "../src/verify.ts";
import type { Inputs, Result } from "../src/verify.ts";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "conformance", "dialect");
const manifest = JSON.parse(readFileSync(join(ROOT, "manifest.json"), "utf8")) as {
  cases: { id: string; path: string; requiresBinding: boolean; expectedResult: string; expectedBinding?: string; expectedFinding?: string }[];
};
// The Runner's manifest, for two of its members alone: the vector's `verifiedAt`, and what its
// export retains, `preparation.retained` (`equal`, `altered` or `recorded`) with the digest
// `preparation.sha256`. The reader reads nothing of it.
type RunnerVector = {
  name: string;
  verifiedAt: string;
  preparation: { sha256: string; retained: string };
};
const runner = new Map(
  (JSON.parse(readFileSync(join(ROOT, "vectors", "manifest.json"), "utf8")) as {
    vectors: RunnerVector[];
  }).vectors.map((v) => [v.name, v]),
);

// A vector the text does not let this reader answer, by id, with the reason. None today: every vector
// was read from the companion document's text alone (README.md, "Where the text was not enough").
const KNOWN_DISAGREEMENTS: Record<string, string> = {};

const written = (v: JVal | undefined) => (v === undefined ? "absent" : Buffer.from(preparationForm(v)).toString("utf8"));

test("the manifest names every vector directory, and nothing else", () => {
  const dirs = readdirSync(join(ROOT, "vectors"))
    .filter((d) => statSync(join(ROOT, "vectors", d)).isDirectory())
    .sort();
  assert.deepEqual(manifest.cases.map((c) => c.path.replace(/^vectors\//, "")).sort(), dirs);
  assert.equal(manifest.cases.length, 39);
  assert.deepEqual([...runner.keys()], manifest.cases.map((c) => c.id));
});

for (const row of manifest.cases) {
  test(`vector ${row.id}`, (t) => {
    if (row.id in KNOWN_DISAGREEMENTS) {
      t.todo(`known disagreement: ${KNOWN_DISAGREEMENTS[row.id]}`);
      return;
    }
    const dir = join(ROOT, row.path);
    const inputs = loadVector(dir, row.requiresBinding);
    const result = verify(inputs);
    const report = result.report;
    const field = (k: string) => (member(report, k) as { v: string } | undefined)?.v;
    assert.equal(result.kind, row.expectedResult, `${row.id}: ${written(report)} (${result.why ?? ""})`);
    if (row.expectedResult === "reading") assert.equal(field("binding"), row.expectedBinding);
    if (row.expectedResult === "finding") assert.equal(field("finding"), row.expectedFinding);

    const vector = runner.get(row.id)!;
    const expected = readFileSync(join(dir, "preparation.json"));
    const recorded = vector.preparation.retained === "recorded";
    const retainedValues = ["equal", "altered", "recorded"];
    assert.ok(retainedValues.includes(vector.preparation.retained), `${row.id}: retained`);
    // The recomputation preparation.json holds is at the vector's verifiedAt: the given
    // preparation's, but in an export that retains an earlier run's preparation (`altered`), where
    // this reader is given preparation.json, of the vector's own instant.
    const givenAt = JSON.parse(Buffer.from(inputs.preparation).toString("utf8")).verifiedAt;
    const shifted = givenAt !== vector.verifiedAt;
    if (shifted) {
      const what = `${row.id}: a preparation of another instant`;
      assert.equal(vector.preparation.retained, "altered", what);
    }
    const recomputedAt = (given: Inputs, first: Result) =>
      (shifted ? verify({ ...given, preparation: Uint8Array.from(expected) }) : first).recomputed;

    if (recorded) {
      // the preparation the run recorded, held fixed: its digest is the manifest's, and nothing is
      // recomputed
      const digest = "sha256:" + createHash("sha256").update(expected).digest("hex");
      assert.equal(digest, vector.preparation.sha256, `${row.id}: the recorded digest`);
      const file = readFileSync(join(dir, "preparation.sha256"), "utf8");
      assert.equal(file, digest, `${row.id}: preparation.sha256`);
      const retained = preparationForm(read(inputs.preparation).value);
      assert.ok(Buffer.from(retained).equals(expected), `${row.id}: the export retains it`);
      assert.equal(result.recomputed, undefined, `${row.id}: a preparation from changed inputs`);
    } else {
      // the recomputed preparation's canonical bytes, and their digest
      const recomputed = recomputedAt(inputs, result);
      assert.ok(recomputed !== undefined, `${row.id}: the preparation was not recomputed`);
      assert.ok(Buffer.from(recomputed).equals(expected), `${row.id}: preparation.json`);
    }
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
      const mapping = Uint8Array.from(readFileSync(join(dir, "mapping.json")));
      const given: Inputs = { ...inputs, dialect: mapping, binding: undefined };
      const direct = verify(given);
      const what = `${row.id}: mapping.json given as the dialect`;
      assert.equal(direct.kind, row.expectedResult, what);
      if (recorded) assert.equal(direct.recomputed, undefined, what);
      else assert.ok(Buffer.from(recomputedAt(given, direct)!).equals(expected), what);
    }
  });
}

// Round 15 reader controls: altered copies of a staged research vector, never new vectors.
import assert from "node:assert/strict";
import { createHash, createPrivateKey, createPublicKey, sign } from "node:crypto";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { readProfiles } from "../src/forms.ts";
import { canon, member, parse, preparationForm, utf8 } from "../src/json.ts";
import { loadVector } from "../src/vector.ts";
import { verify } from "../src/verify.ts";
import type { Inputs } from "../src/verify.ts";

const directory = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..",
  "conformance", "dialect", "vectors", "gtm-company-person-valid-types-all-six");
const prefix = "https://a.example/docs";
const text = (b: Uint8Array) => Buffer.from(b).toString("utf8");
const canonical = (v: unknown) => canon(parse(JSON.stringify(v)));
const digest = (b: Uint8Array) => "sha256:" + createHash("sha256").update(b).digest("hex");
const key = createPrivateKey({ key: Buffer.concat([
  Buffer.from("302e020100300506032b657004220420", "hex"),
  createHash("sha256").update("round 15 TypeScript reader controls").digest(),
]), format: "der", type: "pkcs8" });
const publicKey = createPublicKey(key).export({ format: "der", type: "spki" }).subarray(-32);

type Edit = (d: any) => void;
function scopedInputs(options: {
  scope?: unknown; endpoints?: unknown[]; profile?: Edit; documents?: Edit; after?: Edit;
} = {}): Inputs {
  const inputs = loadVector(directory, false);
  inputs.record = undefined;
  const profiles = JSON.parse(text(inputs.profiles));
  const page = profiles.find((p: any) => p.id === "page");
  page.endpoint = null;
  page.endpointScope = options.scope === undefined ? [prefix] : options.scope;
  options.profile?.(page);
  const binding = JSON.parse(text(inputs.binding!));
  const dialect = JSON.parse(text(inputs.dialect));
  const acquisitions = JSON.parse(text(inputs.acquisitions));
  const responses = acquisitions.person.response.result.responses;
  const original = responses.pop();
  (options.endpoints ?? [prefix + "/one", prefix + "/two"]).forEach((endpoint, index) => {
    const response = structuredClone(original);
    response.request = { url: prefix + `/request-${index}?item=synthetic` };
    response.receipt.acquisition.endpoint = endpoint;
    response.receipt.callIndex = 3 + index;
    responses.push(response);
  });
  const documents = { profiles, binding, dialect, acquisitions };
  options.documents?.(documents);
  const digests = new Map<string, string>();
  for (const p of profiles) {
    p.publicKey = publicKey.toString("hex");
    digests.set(p.id, digest(canonical(p)));
  }
  for (const assignment of Object.values(binding.sources) as any[]) {
    for (const ref of [assignment, ...Object.values(assignment.webProfiles)] as any[]) {
      ref.profileDigest = digests.get(ref.profile);
    }
  }
  binding.dialect = digest(canonical(dialect));
  for (const m of Object.values(acquisitions) as any[]) {
    for (const response of m.response.result.responses) {
      response.profile.digest = digests.get(response.profile.id);
      const receipt = response.receipt;
      receipt.keyId = createHash("sha256").update(publicKey).digest("hex").slice(0, 32);
      receipt.argumentsCommitment = digest(Buffer.concat([
        Buffer.from(response.salts.args, "hex"), Buffer.from("args:"), canonical(response.request),
      ]));
      receipt.resultDigest = digest(canonical(response.result));
      delete receipt.signature;
      receipt.signature = sign(null, Buffer.concat([
        Buffer.from("judgment-pack-gateway/receipt/3:"), canonical(receipt),
      ]), key).toString("hex");
    }
  }
  options.after?.(documents);
  for (const name of ["profiles", "binding", "dialect", "acquisitions"] as const) {
    inputs[name] = utf8(JSON.stringify(documents[name]));
  }
  const computed = verify(inputs).recomputed;
  if (computed !== undefined) inputs.preparation = computed;
  return inputs;
}
function answer(inputs: Inputs): string {
  const result = verify(inputs);
  return result.kind === "reading" ? "reading"
    : result.kind + ":" + (member(result.report, result.kind) as { v: string }).v;
}
const invalid = "finding:acquisition-invalid";
const malformed = "refusal:input-malformed";
const over = "refusal:input-over-bound";
const controls: [string, string, Parameters<typeof scopedInputs>[0]][] = [
  ["two different page URLs", "reading", {}],
  ["out-of-scope final redirect", invalid, { endpoints: ["https://other.example/docs"] }],
  ["every retained response checked", invalid, { endpoints: [prefix, "https://other.example/docs"] }],
  ["segment boundary", invalid, { endpoints: [prefix + "x"] }],
  ["equal path", "reading", { endpoints: [prefix] }],
  ["host case and default port", "reading", { endpoints: ["https://A.EXAMPLE:443/docs/x"] }],
  ["written default port in prefix", "reading", { scope: ["https://A.EXAMPLE:443/docs"] }],
  ["empty endpoint port", "reading", { endpoints: ["https://a.example:/docs/x"] }],
  ["empty endpoint port with written scope port", "reading", {
    scope: ["https://a.example:443/docs"], endpoints: ["https://a.example:/docs/x"] }],
  ["empty scope port", "reading", {
    scope: ["https://a.example:/docs"], endpoints: ["https://a.example/docs/x"] }],
  ["record wildcard", malformed, { scope: ["https://*"], profile: (p) => p.class = "record" }],
  ["record wildcard without research", malformed, { scope: [prefix, "https://*"],
    profile: (p) => { p.class = "record"; delete p.research; } }],
  ["trailing slash", "reading", { scope: [prefix + "/"] }],
  ["trailing slash excludes parent", invalid, { scope: [prefix + "/"], endpoints: [prefix] }],
  ["absent root", "reading", { scope: ["https://a.example/"], endpoints: ["https://a.example"] }],
  ["absent prefix path", "reading", { scope: ["https://a.example"], endpoints: ["https://a.example/"] }],
  ["wildcard origins", "reading", { scope: ["https://*"], endpoints: ["https://new.example/a"] }],
  ["union", "reading", { scope: ["https://other.example", prefix] }],
  ["path case", invalid, { endpoints: ["https://a.example/Docs/x"] }],
  ["subdomain", invalid, { endpoints: ["https://sub.a.example/docs"] }],
  ["escaped slash is no boundary", invalid, { endpoints: [prefix + "%2Fx"] }],
  ["escape spelling", "reading", { scope: [prefix + "/%7e"], endpoints: [prefix + "/%7e/x"] }],
  ["escape case", invalid, { scope: [prefix + "/%7e"], endpoints: [prefix + "/%7E"] }],
  ["no decoding", invalid, { scope: [prefix + "/%7e"], endpoints: [prefix + "/~"] }],
  ["no slash collapse", invalid, { scope: [prefix + "//x"], endpoints: [prefix + "/x"] }],
  ["path at sign", "reading", { endpoints: [prefix + "/@name"] }],
  ["exact endpoint beside scope", malformed, { profile: (p) => p.endpoint = prefix }],
  ["wrong adapter", malformed, { profile: (p) => p.adapter.name = "adapter-sources" }],
  ["wrong shape", malformed, { profile: (p) => p.shape = "airbyte" }],
  ["search declaration", malformed, { profile: (p) => p.research.capabilities = ["search", "page"] }],
  ["answer declaration", malformed, { profile: (p) => p.research = {
    capabilities: ["answer", "page"], model: "synthetic-research-model-1",
  } }],
  ["generated needs declaration", malformed, { profile: (p) => delete p.research }],
  ["research needs generated", "finding:profile-mismatch", { profile: (p) => p.class = "record" }],
  ["32 entries", "reading", { scope: [prefix,
    ...Array.from({ length: 31 }, (_, i) => `https://site${i}.example`)] }],
  ["33 entries before form", over, { scope: Array(33).fill(prefix), profile: (p) => p.shape = "command" }],
  ["UTF8 bytes before grammar", over, { scope: ["é".repeat(1025)] }],
  ["changed scope with old pin", "finding:profile-mismatch", {
    after: (d) => d.profiles.at(-1).endpointScope = ["https://*"],
  }],
  ["changed request", invalid, { after: (d) =>
    d.acquisitions.person.response.result.responses.at(-1).request.url = prefix + "/altered" }],
  ["changed receipt", invalid, { after: (d) =>
    d.acquisitions.person.response.result.responses.at(-1).receipt.acquisition.endpoint = prefix + "/altered" }],
  ["replay checks only final URL", "reading", { documents: (d) =>
    d.acquisitions.person.response.result.responses.at(-1).request.url = "https://outside.example/start" }],
  ["adapter remains exact", invalid, { documents: (d) =>
    d.acquisitions.person.response.result.responses.at(-1).receipt.acquisition.adapter.name = "other" }],
  ["shape remains exact", invalid, { documents: (d) =>
    d.acquisitions.person.response.result.responses.at(-1).receipt.acquisition.shape = "mcp" }],
];
for (const endpoint of [null, "http://a.example/docs", "https://a.example:444/docs",
  "https://a.example:0443/docs", "https://a.example:0/docs", "https://a.example:80/docs",
  "https://a.example:4430/docs", "https://user@a.example/docs",
  prefix + "?x", prefix + "#x", "https://127.0.0.1/docs", "https://[::1]/docs",
  "https://127.1/docs", "https://localhost/docs", "https://a.example./docs",
  "https://a_b.example/docs", "https://-a.example/docs", "https://a-.example/docs",
  "https://a..example/docs", "https://" + "a".repeat(64) + ".example/docs",
  "https://a.123/docs", "https://0x7f.0x0.0x0.0x1/docs", "https://é.example/docs", prefix + "/%", prefix + "/%2",
  prefix + "/%gg", prefix + "/\\x", prefix + "/x\n", prefix + "/.", prefix + "/../x",
  prefix + "/%2e/x", prefix + "/.%2E/x", prefix + "/%2E%2e/x", prefix + "/%2e./x",
  prefix + "/x/..", "https://*/docs", "HTTPS://a.example/docs",
  "https://a.example/" + "x".repeat(2031)]) {
  controls.push(["invalid endpoint " + JSON.stringify(endpoint).slice(0, 75), invalid,
    { scope: ["https://*"], endpoints: [endpoint] }]);
}
for (const scope of [null, [], {}, "https://*", [null], [prefix, prefix], ["https://*/docs"],
  ["http://a.example"], [prefix + "/.."], [prefix + "?x"], ["https://127.0.0.1"],
  ["https://a.example:444"], ["https://a.example./"], ["https://A.EXAMPLE/%2E/"]]) {
  controls.push(["bad scope " + JSON.stringify(scope), malformed, { scope }]);
}
const longest = "https://a.example/" + "x".repeat(2048 - "https://a.example/".length);
controls.push(["2048 byte entry", "reading", { scope: [longest], endpoints: [longest] }]);
controls.push(["2049 bytes before forms", over,
  { scope: [longest + "x"], profile: (p) => p.shape = "command" }]);
for (const [name, expected, options] of controls) {
  test("endpoint scope: " + name, () => assert.equal(answer(scopedInputs(options)), expected));
}

test("endpoint scope: changes profile, binding document, dialect and preparation binding", () => {
  const first = scopedInputs();
  const second = scopedInputs({ scope: ["https://*"] });
  assert.notEqual(digest(canonical(JSON.parse(text(first.profiles)).at(-1))),
    digest(canonical(JSON.parse(text(second.profiles)).at(-1))));
  assert.notEqual(digest(canon(parse(text(first.binding!)))), digest(canon(parse(text(second.binding!)))));
  assert.notEqual(JSON.parse(text(first.preparation)).mappingDigest,
    JSON.parse(text(second.preparation)).mappingDigest);
  assert.notEqual(digest(first.preparation), digest(second.preparation));
  assert.equal(answer({ ...second, preparation: first.preparation }), "finding:preparation-differs");
});

test("endpoint scope: record web profile is admitted; web remains unread", () => {
  const inputs = scopedInputs({ profile: (p) => { p.class = "record"; delete p.research; } });
  assert.equal(readProfiles(parse(text(inputs.profiles))).at(-1)!.endpointScope![0], prefix);
  const dialect = JSON.parse(text(inputs.dialect));
  delete dialect.admits;
  dialect.sources = [{ name: "page", kind: "web", profile: "page",
    profileDigest: digest(canonical(JSON.parse(text(inputs.profiles)).at(-1))), maxAge: 600,
    url: prefix, read: { copy: { facts: [], evidence: [] } } }];
  assert.equal(answer({ ...inputs, dialect: canonical(dialect), binding: undefined,
    acquisitions: utf8("{}") }), "refusal:kind-unread");
  dialect.sources[0].kind = "operation";
  dialect.sources[0].arguments = { url: prefix };
  delete dialect.sources[0].url;
  assert.equal(answer({ ...inputs, dialect: canonical(dialect), binding: undefined,
    acquisitions: utf8("{}") }), "finding:profile-mismatch");
});

test("endpoint scope: historical exact profile and preparation stay unchanged", () => {
  const inputs = loadVector(directory, true);
  const result = verify(inputs);
  assert.equal(answer(inputs), "reading");
  assert.equal((member(result.report, "binding") as { v: string }).v, "matches");
  assert.deepEqual(result.recomputed, preparationForm(parse(text(inputs.preparation))));
});

// The forms the companion document fixes in its own words (§1, §9.5, §11, §12), and this reader's
// readings of inputs no vector holds, each derived from the `valid` vector by one change. The second
// group is this reader's, not the vectors': see README.md, "Where the text was not enough".
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash, createPublicKey, generateKeyPairSync, sign as nodeSign, verify as nodeVerify } from "node:crypto";
import { copyFileSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { scanBytes } from "../src/bounds.ts";
import { add, decodePoint, encodePoint, keyAcceptable, smallOrder, verify as edVerify } from "../src/ed25519.ts";
import { bindDialect, readBinding, readDialect } from "../src/forms.ts";
import { NotRead, arr, canon, isIntegerLiteral, member, num, obj, parse, preparationForm, read, resolve, str, utf8 } from "../src/json.ts";
import type { JObj, JVal } from "../src/json.ts";
import { instant } from "../src/time.ts";
import { loadVector } from "../src/vector.ts";
import { verify } from "../src/verify.ts";
import type { Inputs } from "../src/verify.ts";

const VECTORS = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "conformance", "dialect", "vectors");
const text = (b: Uint8Array) => Buffer.from(b).toString("utf8");

test("§9.2 and §9.3: a skipped source keeps its claim and every declared dependency", () => {
  const dir = join(VECTORS, "skipped-source-dependency-unavailable");
  const inputs = loadVector(dir, true);
  const result = verify(inputs);
  assert.deepEqual(Buffer.from(result.recomputed!), readFileSync(join(dir, "preparation.json")));
  assert.equal(result.kind, "reading");
  assert.equal((member(result.report, "binding") as { v: string }).v, "matches");
  const preparation = JSON.parse(text(result.recomputed!));
  assert.deepEqual(preparation.outcomes.at(-1), {
    name: "endorsement",
    parameters: { requestId: "REQ-7", requestType: "data-access", runAt: preparation.verifiedAt },
    claim: { acquisitionStatus: "unknown", basis: [], evidenceAvailability: {}, facts: {},
      reason: "dependency-unavailable" },
    status: "unknown", reason: "dependency-unavailable",
  });
  const dependencies = [
    { parameter: "approver", source: "sponsor", pointer: "/sponsor/id" },
    { parameter: "requestType", source: "intake", pointer: "/intake/type" },
  ];
  const skipped: string[] = [];
  for (const entry of preparation.lineage) {
    if (entry.source !== "endorsement") {
      assert.ok(!("dependencies" in entry));
      continue;
    }
    skipped.push(entry.target);
    assert.deepEqual(entry.dependencies, dependencies);
    assert.deepEqual([entry.status, entry.reason, entry.present, entry.basis],
      ["unknown", "dependency-unavailable", false, []]);
    for (const member of ["receipt", "receipts", "calculation"]) assert.ok(!(member in entry));
  }
  assert.deepEqual(skipped, ["/endorsement", "sponsor-endorsement"]);
  assert.equal(preparation.cites.length, 2);
  // Declaration order does not change parameter-name order, or omit the parameter with a value.
  const dialect = JSON.parse(text(inputs.dialect));
  const source = dialect.sources.at(-1);
  source.parameters = Object.fromEntries(Object.entries(source.parameters).reverse());
  const reversed = verify({ ...inputs, dialect: utf8(JSON.stringify(dialect)) });
  assert.deepEqual(reversed.recomputed, result.recomputed);
  assert.equal(reversed.kind, "reading");
});

test("§9.3: an acquired source keeps every declared dependency", () => {
  for (const resolved of [true, false]) {
    const base = loadVector(join(VECTORS, "skipped-source-dependency-unavailable"), false);
    const document = JSON.parse(text(base.dialect));
    const source = document.sources.at(-1);
    source.parameters = Object.fromEntries(Object.entries(source.parameters).reverse());
    const sources = JSON.parse(text(base.acquisitions));
    const sponsor = sources.sponsor.response;
    sponsor.result.sponsor = { id: "S-1" };
    const endorsement = structuredClone(sponsor);
    endorsement.result = { approver: "S-1", requestType: "data-access" };
    if (resolved) endorsement.result.endorsement = { approved: true };
    const canonical = (value: unknown) => canon(parse(JSON.stringify(value)));
    const digest = (bytes: Uint8Array) =>
      "sha256:" + createHash("sha256").update(bytes).digest("hex");
    const request = { tool: "lookup", arguments: {
      table: "endorsements", approver: "S-1", requestType: "data-access",
    } };
    endorsement.receipt.callIndex = 2;
    endorsement.receipt.argumentsCommitment = digest(Buffer.concat([
      Buffer.from(endorsement.salts.args, "hex"), Buffer.from("args:"), canonical(request),
    ]));
    for (const response of [sponsor, endorsement]) {
      response.receipt.resultDigest = digest(canonical(response.result));
    }
    sources.endorsement = { response: endorsement };
    const inputs = alteredAndSigned({
      ...base, dialect: canonical(document), acquisitions: canonical(sources),
      record: undefined, requireBinding: false,
    }, {});
    const result = verify(inputs);
    assert.ok(result.recomputed, text(preparationForm(result.report)));
    const preparation = JSON.parse(text(result.recomputed));
    assert.equal(preparation.outcomes.at(-2).status, "resolved");
    const outcome = preparation.outcomes.at(-1);
    assert.equal(outcome.status, resolved ? "resolved" : "unknown");
    assert.equal(outcome.parameters.approver, "S-1");
    assert.equal(outcome.parameters.requestType, "data-access");
    assert.deepEqual(outcome.arguments, request);
    const targets: string[] = [];
    for (const entry of preparation.lineage) {
      if (entry.source !== "endorsement") {
        assert.ok(!("dependencies" in entry));
        continue;
      }
      targets.push(entry.target);
      assert.deepEqual(entry.dependencies, [
        { parameter: "approver", source: "sponsor", pointer: "/sponsor/id" },
        { parameter: "requestType", source: "intake", pointer: "/intake/type" },
      ]);
      assert.equal(entry.status, outcome.status);
      assert.ok("receipt" in entry);
    }
    assert.deepEqual(targets, ["/endorsement", "sponsor-endorsement"]);
    assert.equal(verify({ ...inputs, preparation: result.recomputed }).kind, "reading");
  }
});

test("§9.5 writes &, <, >, U+2028 and U+2029 escaped and keeps -0; canon writes them as they are and -0 as 0", () => {
  const v = obj([["s", str("A&B <x> café ☃  /\u007f\u001f\n")], ["z", num("-0")], ["big", num("-9007199254740991")]]);
  assert.equal(text(preparationForm(v)), '{"big":-9007199254740991,"s":"A\\u0026B \\u003cx\\u003e café ☃\\u2028\\u2029/\u007f\\u001f\\n","z":-0}');
  assert.equal(text(canon(v)), '{"big":-9007199254740991,"s":"A&B <x> café ☃  /\u007f\\u001f\\n","z":0}');
});

test("members are ordered by code point, not by UTF-16 unit", () => {
  const v = obj([["￿", num("1")], ["\u{10000}", num("2")]]);
  assert.equal(text(canon(v)), '{"￿":1,"\u{10000}":2}');
});

test("§1 integers: -0 is one; 1.0, 1e2 and 9007199254740992 are not", () => {
  assert.ok(isIntegerLiteral("-0"));
  assert.ok(isIntegerLiteral("9007199254740991"));
  for (const lit of ["1.0", "1e2", "9007199254740992", "-9007199254740992"]) assert.ok(!isIntegerLiteral(lit), lit);
  assert.throws(() => canon(num("1.5")));
});

test("§1 strict reading refuses a name given twice, a lone surrogate, a BOM, trailing data and bytes that are not UTF-8", () => {
  for (const bad of ['{"a":1,"\\u0061":2}', '"\\ud800"', '"\\udc00x"', "﻿{}", "{} {}", "[1,]", "01", '{"a":1}x']) {
    assert.throws(() => read(utf8(bad)), NotRead, bad);
  }
  assert.throws(() => read(Uint8Array.from([0x22, 0xc3, 0x28, 0x22])), NotRead);
  assert.equal(parse('"\\ud83d\\ude00"').t, "str");
  assert.equal((parse(" -0 ") as { lit: string }).lit, "-0");
});

test("§1 timestamps: a form that names no time has no instant", () => {
  assert.equal(instant("1970-01-01T00:00:00Z"), 0);
  assert.equal(instant("2026-10-14T14:58:26Z"), Date.UTC(2026, 9, 14, 14, 58, 26) / 1000);
  assert.equal(instant("2026-02-30T00:00:00Z"), null);
  assert.equal(instant("2100-02-29T00:00:00Z"), null);
  assert.notEqual(instant("2000-02-29T00:00:00Z"), null);
  assert.notEqual(instant("0000-02-29T00:00:00Z"), null);
  for (const bad of ["2026-10-14T24:00:00Z", "2026-10-14T23:60:00Z", "2026-10-14T23:59:60Z", "2026-10-14 14:58:26Z", "2026-10-14T14:58:26.0Z", "2026-10-14T14:58:26+00:00"]) {
    assert.equal(instant(bad), null, bad);
  }
});

test("§1 pointers: an array index is 0 or a digit other than 0 and digits, below the length, with no number limit", () => {
  const v = parse('{"a":[10,20],"":{"~/":1}}');
  assert.equal((resolve(v, "/a/1") as { lit: string }).lit, "20");
  for (const p of ["/a/01", "/a/-", "/a/2", "/a/99999999999999999999999999", "/b"]) assert.equal(resolve(v, p), undefined, p);
  assert.equal((resolve(v, "//~0~1") as { lit: string }).lit, "1");
});

test("§12 bounds measured on bytes: nesting, a number literal's characters and its exponent", () => {
  assert.deepEqual(scanBytes(utf8('{"a":[["[[[["]]}')), { nesting: 3, numbersWithin: true });
  assert.equal(scanBytes(utf8("[1e308,-1E-308,1e0000000308]")).numbersWithin, true);
  assert.equal(scanBytes(utf8("[1e309]")).numbersWithin, false);
  assert.equal(scanBytes(utf8("[" + "1".repeat(129) + "]")).numbersWithin, false);
});

// ---- Ed25519: the equation of §1 ----

const valid = loadVector(join(VECTORS, "valid"), true);
const profileKey = Uint8Array.from(Buffer.from((member((parse(text(valid.profiles)) as { a: JObj[] }).a[0], "publicKey") as { v: string }).v, "hex"));
const receipt = member(member(member(parse(text(valid.acquisitions)), "fx"), "response"), "receipt") as JObj;
const signedBytes = Buffer.concat([Buffer.from("judgment-pack-gateway/receipt/3:"), canon(obj(Array.from(receipt.m).filter(([k]) => k !== "signature")))]);
const signature = Buffer.from((receipt.m.get("signature") as { v: string }).v, "hex");

test("the receipt signature of the valid vector verifies here and under node:crypto alike; a changed byte fails both", () => {
  const spki = createPublicKey({ key: Buffer.concat([Buffer.from("302a300506032b6570032100", "hex"), profileKey]), format: "der", type: "spki" });
  assert.ok(edVerify(profileKey, signedBytes, signature));
  assert.ok(nodeVerify(null, signedBytes, spki, signature));
  const other = Buffer.from(signedBytes);
  other[other.length - 2] ^= 1;
  assert.ok(!edVerify(profileKey, other, signature));
  assert.ok(!nodeVerify(null, other, spki, signature));
});

test("a scalar that is not canonical (S + L) is refused", () => {
  const L = 2n ** 252n + 27742317777372353535851937790883648493n;
  let s = 0n;
  for (let k = 63; k >= 32; k--) s = (s << 8n) | BigInt(signature[k]);
  s += L;
  const forged = Buffer.from(signature);
  for (let k = 32; k < 64; k++) {
    forged[k] = Number(s & 0xffn);
    s >>= 8n;
  }
  assert.ok(!edVerify(profileKey, signedBytes, forged));
});

// The key rule of the checkpoint witness statement, §5, which spec/dialect.md §1 adopts by reference.
const SMALL_ORDER = [
  "0100000000000000000000000000000000000000000000000000000000000000",
  "ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f",
  "0000000000000000000000000000000000000000000000000000000000000000",
  "0000000000000000000000000000000000000000000000000000000000000080",
  "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05",
  "26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85",
  "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a",
  "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa",
];
const bytesOf = (h: string) => Uint8Array.from(Buffer.from(h, "hex"));

test("the key rule (witness statement §5): the eight points of small order are refused, each by its canonical encoding", () => {
  assert.ok(keyAcceptable(profileKey));
  for (const h of SMALL_ORDER) {
    assert.notEqual(decodePoint(bytesOf(h)), null, h);
    assert.ok(!keyAcceptable(bytesOf(h)), h);
  }
});

test("the key rule: an encoding that is not canonical, and one that is no point, are refused; a key of mixed order is not", () => {
  // y = p, which a lenient decoder reads as y = 0; and x = 0 (y = 1) with the sign bit set
  const yP = new Uint8Array(32).fill(0xff);
  yP[0] = 0xed;
  yP[31] = 0x7f;
  assert.ok(!keyAcceptable(yP));
  const signedZero = bytesOf(SMALL_ORDER[0]);
  signedZero[31] |= 0x80;
  assert.ok(!keyAcceptable(signedZero));
  // y = p + k for a small k whose canonical encoding is a point of large order: a lenient decoder would
  // read it as that point, so only the canonical-encoding rule refuses it
  const k = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18].find((v) => {
    const pt = decodePoint(Uint8Array.from([v, ...new Array(31).fill(0)]));
    return pt !== null && !smallOrder(pt);
  })!;
  const lenient = new Uint8Array(32).fill(0xff);
  lenient[0] = 0xed + k;
  lenient[31] = 0x7f;
  assert.ok(keyAcceptable(Uint8Array.from([k, ...new Array(31).fill(0)])));
  assert.ok(!keyAcceptable(lenient));
  // the first canonical y with no square root: no point
  let y = 2;
  for (; decodePoint(Uint8Array.from([y, ...new Array(31).fill(0)])) !== null; y++);
  assert.ok(!keyAcceptable(Uint8Array.from([y, ...new Array(31).fill(0)])));
  // the vector's key plus a point of order 8: of mixed order, so not refused
  const mixed = encodePoint(add(decodePoint(profileKey)!, decodePoint(bytesOf(SMALL_ORDER[4]))!));
  assert.ok(!smallOrder(decodePoint(mixed)!));
  assert.ok(keyAcceptable(mixed));
});

test("the equation: R is compared as bytes with the canonical encoding of [S]B − [h]A", () => {
  // R with its sign bit flipped encodes the negated point, and does not verify
  const flipped = Buffer.from(signature);
  flipped[31] ^= 0x80;
  assert.ok(!edVerify(profileKey, signedBytes, flipped));
  assert.ok(edVerify(profileKey, signedBytes, signature));
});

// ---- the refusals and findings, each from the valid vector by one change ----

function answer(change: (i: Inputs) => Inputs): string {
  const r = verify(change({ ...valid }));
  return r.kind === "reading" ? `reading:${(member(r.report, "binding") as { v: string }).v}` : `${r.kind}:${(member(r.report, r.kind) as { v: string }).v}`;
}
const edit = (b: Uint8Array, from: string, to: string) => {
  const t = text(b);
  assert.ok(t.includes(from), from);
  return utf8(t.replace(from, to));
};

test("the valid vector unchanged is a reading whose binding matches", () => {
  assert.equal(answer((i) => i), "reading:matches");
});

test("refusals, by phase (§11)", () => {
  assert.equal(answer((i) => ({ ...i, dialect: utf8(text(i.dialect).replace("{", "{" + " ".repeat(131072))) })), "refusal:input-over-bound");
  assert.equal(answer((i) => ({ ...i, case: utf8("[".repeat(33) + "]".repeat(33)) })), "refusal:input-over-bound");
  assert.equal(answer((i) => ({ ...i, case: utf8('{"n":1e309}') })), "refusal:input-over-bound");
  assert.equal(answer((i) => ({ ...i, record: edit(i.record!, '"inputs":', '"Binding":null,"inputs":') })), "refusal:input-malformed");
  assert.equal(answer((i) => ({ ...i, record: utf8(text(i.record!) + "\n") })), "refusal:input-malformed");
  assert.equal(answer((i) => ({ ...i, dialect: edit(i.dialect, '"version":2', '"version":2,"version":2') })), "refusal:input-malformed");
  assert.equal(answer((i) => ({ ...i, dialect: edit(i.dialect, '"kind":"operation"', '"kind":"http"') })), "refusal:input-malformed");
  assert.equal(answer((i) => ({ ...i, dialect: edit(i.dialect, '"maxAge":300', '"maxAge":300,"Name":"x"') })), "refusal:input-malformed");
  assert.equal(answer((i) => ({ ...i, preparation: edit(i.preparation, '"verifiedAt":"2026-10-14T14:58:26Z"', '"verifiedAt":"2026-02-30T14:58:26Z"') })), "refusal:input-malformed");
  assert.equal(
    answer((i) => ({ ...i, dialect: edit(i.dialect, '"sources":[', '"sources":[{"name":"file","kind":"selected-file","provider":"local-file","read":{"copy":{"facts":[],"evidence":[]}}},') })),
    "refusal:kind-unread",
  );
});

test("findings, in their order (§11)", () => {
  assert.equal(answer((i) => ({ ...i, dialect: edit(i.dialect, '"profileDigest":"sha256:2', '"profileDigest":"sha256:3') })), "finding:profile-mismatch");
  assert.equal(answer((i) => ({ ...i, case: utf8('{"amount":1200,"currency":"EUR"}') })), "finding:parameter-invalid");
  assert.equal(answer((i) => ({ ...i, acquisitions: utf8("{}") })), "finding:acquisition-missing");
  assert.equal(answer((i) => ({ ...i, acquisitions: edit(i.acquisitions, '"present","sponsor', '"absent","sponsor') })), "finding:acquisition-invalid");
  // a signed member no other check reads: only the signature fails
  assert.equal(answer((i) => ({ ...i, acquisitions: edit(i.acquisitions, '"snapshot":"query-123"', '"snapshot":"query-124"') })), "finding:acquisition-invalid");
  const twice = (b: Uint8Array) => {
    const inner = text(b).slice('{"fx":'.length, -1);
    return utf8(`{"fx":${inner},"other":${inner}}`);
  };
  assert.equal(answer((i) => ({ ...i, acquisitions: twice(i.acquisitions) })), "finding:acquisition-unexpected");
  const later = (b: Uint8Array) => utf8(text(b).replaceAll("2026-10-14T14:58:26Z", "2026-10-14T15:08:26Z"));
  assert.equal(answer((i) => ({ ...i, preparation: later(i.preparation) })), "finding:acquisition-stale");
  assert.equal(answer((i) => ({ ...i, record: edit(i.record!, '"intake-form":"present"', '"intake-form":"absent"') })), "finding:record-inputs-differ");
  assert.equal(answer((i) => ({ ...i, record: edit(i.record!, '"appropriateness":"pass"', '"appropriateness":"fail"') })), "finding:record-inputs-differ");
  assert.equal(answer((i) => ({ ...i, record: edit(i.record!, '"cites":[{"sessionId":"mapping.session","callIndex":0', '"cites":[{"sessionId":"mapping.session","callIndex":1') })), "finding:record-inputs-differ");
  // the citations are compared as sets: one given twice is one member
  const cite = '{"sessionId":"mapping.session","callIndex":0,"signature":"d9af';
  assert.equal(answer((i) => ({ ...i, record: edit(i.record!, `"cites":[${cite}`, `"cites":[{"signature":"d9af4d7988f5c89c918cf7d116e2ab6428f805e886a824b40cac5b46c5520fb126ba663c723ddffd109263a9e8ef0669944c88a4727f9d11d7cf1a8bcb9d060d","callIndex":0,"sessionId":"mapping.session"},${cite}`) })), "reading:matches");
  assert.equal(answer((i) => ({ ...i, record: edit(i.record!, '"binding":{"kind"', '"binding":{ "kind"') })), "finding:binding-mismatch");
  assert.equal(answer((i) => ({ ...i, record: edit(i.record!, '"binding":{"kind":"judgment-pack-runner/preparation/1"', '"binding":null,"x":{"kind":"judgment-pack-runner/preparation/1"') })), "finding:binding-foreign-kind");
  assert.equal(answer((i) => ({ ...i, record: undefined })), "finding:unbound");
  assert.equal(answer((i) => ({ ...i, record: undefined, requireBinding: false })), "reading:not-checked");
});

// ---- inputs re-signed under a key generated here, to reach the checks after a receipt's ----

/** Applies `change` to each acquisition's parsed result and receipt, then signs every receipt again under a new key. */
function resigned(base: Inputs, change: (name: string, result: JObj, receipt: JObj) => void): Inputs {
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  const raw = Buffer.from(publicKey.export({ format: "jwk" }).x as string, "base64url");
  const hex = (b: Uint8Array) => Buffer.from(b).toString("hex");
  const profiles = parse(text(base.profiles)) as { a: JObj[] };
  for (const p of profiles.a) p.m.set("publicKey", str(hex(raw)));
  const digests = new Map(profiles.a.map((p) => [(p.m.get("id") as { v: string }).v, "sha256:" + hex(createHash("sha256").update(canon(p)).digest())]));
  const dialect = parse(text(base.dialect)) as JObj;
  for (const s of (dialect.m.get("sources") as { a: JObj[] }).a) s.m.set("profileDigest", str(digests.get((s.m.get("profile") as { v: string }).v)!));
  const acquisitions = parse(text(base.acquisitions)) as JObj;
  for (const [name, a] of acquisitions.m) {
    const response = member(a, "response") as JObj;
    const result = response.m.get("result") as JObj;
    const receipt = response.m.get("receipt") as JObj;
    change(name, result, receipt);
    receipt.m.set("resultDigest", str("sha256:" + hex(createHash("sha256").update(canon(result)).digest())));
    receipt.m.set("keyId", str(hex(createHash("sha256").update(raw).digest()).slice(0, 32)));
    receipt.m.delete("signature");
    const signed = Buffer.concat([Buffer.from("judgment-pack-gateway/receipt/3:"), canon(receipt)]);
    receipt.m.set("signature", str(hex(nodeSign(null, signed, privateKey))));
  }
  return { ...base, dialect: canon(dialect), profiles: canon(profiles as unknown as JVal), acquisitions: canon(acquisitions) };
}
const at = (v: JVal, p: string) => resolve(v, p) as JObj;

test("re-signed without a change, the inputs pass every acquisition check (the given preparation then differs)", () => {
  assert.equal(answer(() => resigned(valid, () => {})), "finding:preparation-differs");
});

test("calculation-invalid (§7): an echoed input that is not the bound parameter's value, a table older than its limit", () => {
  assert.equal(answer(() => resigned(valid, (_, r) => at(r, "/calculation/inputs").m.set("amount", str("1200.0")))), "finding:calculation-invalid");
  assert.equal(answer(() => resigned(valid, (_, r) => at(r, "/calculation/inputs").m.set("amount", num("1200")))), "finding:calculation-invalid");
  assert.equal(answer(() => resigned(valid, (_, r) => at(r, "/calculation/asOf").m.set("ecb-rates", str("2026-10-13T14:58:25Z")))), "finding:calculation-invalid");
  assert.equal(answer(() => resigned(valid, (_, r) => at(r, "/calculation/inputs").m.delete("currency"))), "finding:calculation-invalid");
});

test("read-failed (§6.2): a copied availability that is not present, absent or unknown", () => {
  assert.equal(answer(() => resigned(valid, (_, r) => at(r, "/evidence").m.set("intake-form", str("maybe")))), "finding:read-failed");
});

const twoSources = loadVector(join(VECTORS, "unsigned-parameters"), false);

test("acquisition-sessions (§5.2): two sessions whose second call is not its session's first", () => {
  const session = (id: string, index: string) => (name: string, _: JObj, receipt: JObj) => {
    if (name !== "registry") return;
    receipt.m.set("sessionId", str(id));
    receipt.m.set("callIndex", num(index));
  };
  assert.equal(answer(() => resigned(twoSources, session("another.session", "1"))), "finding:acquisition-sessions");
  assert.equal(answer(() => resigned(twoSources, session("mapping.session", "0"))), "finding:acquisition-sessions");
  // each alone in a session of its own, each its session's first call: a form, so the reading goes on
  assert.equal(answer(() => resigned(twoSources, session("another.session", "0"))), "finding:preparation-differs");
});

test("unsignedParameters of the unsigned-parameters vector, as this reader reads §11 and §4.1", () => {
  // Not compared with the Runner's report, which is in the Runner's manifest; the independence protocol
  // kept this reader from it. vendor: runAt is read by freshWithin and no request can carry it; vendorId is
  // committed by a $text naming it alone, window by $param. registry: region is read and not carried
  // (case), and vendorId is carried only in "{{vendorId}}{{suffix}}" (ambiguous-text).
  const r = verify(twoSources);
  assert.equal(r.kind, "reading");
  assert.equal(
    text(preparationForm(member(r.report, "unsignedParameters")!)),
    '[{"parameters":[{"kind":"runAt","name":"runAt"}],"source":"vendor","targets":2},' +
      '{"parameters":[{"kind":"case","name":"region"},{"kind":"ambiguous-text","name":"vendorId"}],"source":"registry","targets":1}]',
  );
  assert.equal(
    text(preparationForm(member(r.report, "unsignedFreshness")!)),
    '{"against":"preparation.verifiedAt","sources":[{"checks":["acquisition"],"source":"vendor","targets":2},' +
      '{"checks":["acquisition"],"source":"registry","targets":1}],"verifiedAt":"2026-10-01T22:32:47Z"}',
  );
  assert.equal(text(preparationForm(member(r.report, "targetsByClass")!)), '{"asserted":0,"generated":0,"record":3}');
});

test("probe: freshWithin whose asOf names a parameter declared string is false, not a refused rule", () => {
  // The cross-vendor round's probe (spec PR 145). spec/dialect.md §6.3 makes the types part of the
  // condition's truth ("N, of type timestamp, has an instant ... the value of M, of type integer"), and its
  // sentence on a rule "not of this form" does not name a declared type: the rule is read, the condition is
  // false, the first clause does not match, and the vendor source answers by its last clause.
  const probe: Inputs = {
    ...twoSources,
    dialect: edit(
      edit(twoSources.dialect, '"parameters":{"vendorId":"integer","window":"integer","runAt":"timestamp"}', '"parameters":{"vendorId":"integer","window":"integer","runAt":"timestamp","region":"string"}'),
      '"asOf":"runAt"',
      '"asOf":"region"',
    ),
  };
  const r = verify(probe);
  assert.equal(r.kind, "finding");
  assert.equal((member(r.report, "finding") as { v: string }).v, "preparation-differs");
  const vendor = (member(parse(text(r.recomputed!)), "outcomes") as { a: JObj[] }).a[1];
  assert.equal((vendor.m.get("name") as { v: string }).v, "vendor");
  assert.equal((vendor.m.get("reason") as { v: string }).v, "no-match");
  assert.equal(text(preparationForm(member(vendor, "claim")!)), '{"acquisitionStatus":"unknown","basis":["/id","/observedAt"],"evidenceAvailability":{"intake-form":"unknown"},"facts":{},"reason":"no-match"}');
});

// ---- the six choices the text now decides (RFC 0018, Evidence), each held as the text says ----

const verdict = (i: Inputs) => {
  const r = verify(i);
  return r.kind === "reading" ? `reading:${(member(r.report, "binding") as { v: string }).v}` : `${r.kind}:${(member(r.report, r.kind) as { v: string }).v}`;
};

test("§12: nesting counts every object and every array as one level, from zero at the root", () => {
  for (const [doc, levels] of [['"x"', 0], ["1", 0], ["{}", 1], ["[]", 1], ['{"a":[]}', 2], ["[{}]", 2], ['"[[{{"', 0]] as const) {
    assert.equal(scanBytes(utf8(doc)).nesting, levels, doc);
  }
  // the case document at 32 levels is within its bound, and at 33 over it
  assert.notEqual(answer((i) => ({ ...i, case: utf8("[".repeat(32) + "]".repeat(32)) })), "refusal:input-over-bound");
  assert.equal(answer((i) => ({ ...i, case: utf8("[".repeat(33) + "]".repeat(33)) })), "refusal:input-over-bound");
});

test("§12: a number literal is a maximal run of 0-9, +, -, ., e and E, its exponent the digits after the first e", () => {
  for (const doc of ["[1e308,-1E-308,1e+0000308,true,false,null]", "[1e5e999]", "[1e+-999]", "[" + "9".repeat(128) + "]"]) {
    assert.equal(scanBytes(utf8(doc)).numbersWithin, true, doc);
  }
  for (const doc of ["[e999]", "[E+999]", "[.1e309]", "[+1e309]", "[1e999.5]", "[." + "1".repeat(128) + "]", "[e" + "1".repeat(127) + "]"]) {
    assert.equal(scanBytes(utf8(doc)).numbersWithin, false, doc);
  }
  // through the reading: a run that begins with `e` is over its bound before the case is read
  assert.equal(answer((i) => ({ ...i, case: utf8("[e999]") })), "refusal:input-over-bound");
  assert.equal(answer((i) => ({ ...i, case: utf8("[1e5e999]") })), "refusal:input-malformed");
});

test("§12: an unwrapped string's bound is counted on the UTF-8 bytes of its decoded value", () => {
  // The vendor source's result, wrapped in a string of exactly `size` UTF-8 bytes, about half as many
  // characters: within the bound at 200000 bytes, over it at 200001. Its quotes, escaped in the
  // acquisitions document, take more bytes there than decoded, and do not count.
  const wrapped = (size: number) =>
    resigned({ ...twoSources, dialect: edit(twoSources.dialect, '"read":{"rule"', '"read":{"unwrap":["/wrapped"],"rule"') }, (name, result) => {
      if (name !== "vendor") return;
      const head = '{"pad":"';
      const tail = '",' + text(canon(result)).slice(1);
      const room = size - utf8(head + tail).length;
      const inner = head + "é".repeat(Math.floor(room / 2)) + "a".repeat(room % 2) + tail;
      assert.equal(utf8(inner).length, size);
      assert.ok(inner.length < 100200);
      assert.ok(canon(str(inner)).length - 2 > size); // its bytes as the acquisitions document writes them
      for (const k of Array.from(result.m.keys())) result.m.delete(k);
      result.m.set("wrapped", str(inner));
    });
  assert.equal(verdict(wrapped(200000)), "finding:preparation-differs");
  assert.equal(verdict(wrapped(200001)), "refusal:input-over-bound");
});

test("§11: a version-2 export's record is run.audit exactly as run.json writes it", () => {
  // The valid vector's bound record, written as run.audit into an export of version 2, which carries
  // no bytes, with whitespace around it: the line read is the member's value as written, so the binding
  // still matches.
  const dir = mkdtempSync(join(tmpdir(), "dialect-verify-ts-"));
  try {
    for (const f of ["mapping.json", "case.json", "sources.json", "profiles.json"]) copyFileSync(join(VECTORS, "valid", f), join(dir, f));
    writeFileSync(join(dir, "run.json"), `{"version":2,"run": {"input": {"preparation": ${text(valid.preparation)}}, "audit": ${text(valid.record!)} }}`);
    const v2 = loadVector(dir, true);
    assert.ok(Buffer.from(v2.record!).equals(Buffer.from(valid.record!)));
    assert.equal(verdict(v2), "reading:matches");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("§11: two names differ but for case in ASCII case only", () => {
  for (const name of ["BINDING", "bInDiNg"]) {
    assert.equal(answer((i) => ({ ...i, record: edit(i.record!, '"inputs":', `${JSON.stringify(name)}:1,"inputs":`) })), "refusal:input-malformed", name);
  }
  // full-width letters, a dotted capital I, a dotless i, a combining accent, a longer name: no other folding
  for (const name of ["ｂｉｎｄｉｎｇ", "BİNDİNG", "bındıng", "bindinǵ", "bindings"]) {
    assert.equal(answer((i) => ({ ...i, record: edit(i.record!, '"inputs":', `${JSON.stringify(name)}:1,"inputs":`) })), "reading:matches", name);
  }
});

test("§6.3: freshWithin naming a declared parameter of another type is false, and the rule is read", () => {
  const fresh = (to: string) => verdict({ ...twoSources, dialect: edit(twoSources.dialect, '"asOf":"runAt","maxAge":"window"', to) });
  assert.equal(fresh('"asOf":"runAt","maxAge":"runAt"'), "finding:preparation-differs");
  assert.equal(fresh('"asOf":"window","maxAge":"window"'), "finding:preparation-differs");
  assert.equal(fresh('"asOf":"vendorId","maxAge":"vendorId"'), "finding:preparation-differs");
  // naming a parameter the rule does not declare is outside the form
  assert.equal(fresh('"asOf":"region","maxAge":"window"'), "refusal:input-malformed");
});

test("§6.3: a requirement id is a non-empty string, and has no other form", () => {
  const claim = (to: string) => verdict({ ...twoSources, dialect: edit(twoSources.dialect, '"evidence":{"intake-form":"present"}', to) });
  assert.equal(claim('"evidence":{"":"present"}'), "refusal:input-malformed");
  assert.equal(claim('"evidence":{"pack#1/intake form":"present"}'), "finding:preparation-differs");
  assert.equal(answer((i) => ({ ...i, dialect: edit(i.dialect, '"requirement":"intake-form"', '"requirement":""') })), "refusal:input-malformed");
});

// ---- the program: its report and its exit status (§11, the report) ----

const MAIN = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "main.ts");
// The flags the repository's Python suite runs this reader's tests with, so a child runs under the same cap.
const program = (...args: string[]) => spawnSync(process.execPath, ["--disable-wasm-trap-handler", "--no-warnings", MAIN, ...args], { encoding: "utf8", timeout: 120000 });

test("the program prints the report in §9.5's form, one line, and exits 0, 1, 2, or 3 with no report", () => {
  const reading = program(join(VECTORS, "escaped-strings"));
  assert.equal(reading.status, 0, reading.stderr);
  assert.ok(reading.stdout.endsWith("\n") && !reading.stdout.slice(0, -1).includes("\n"));
  const line = reading.stdout.slice(0, -1);
  const report = parse(line);
  assert.equal(text(preparationForm(report)), line);
  assert.deepEqual(Array.from((report as JObj).m.keys()).sort(), ["binding", "digest", "evidence", "facts", "result", "targetsByClass"]);
  assert.ok(line.includes('"vendor":"A\\u0026B \\u003cx\\u003e café ☃"'), line);

  const finding = program(join(VECTORS, "recomputed-one-second-later"), "--require-binding");
  assert.deepEqual([finding.status, finding.stdout], [2, '{"finding":"binding-mismatch","result":"finding"}\n']);

  const dir = mkdtempSync(join(tmpdir(), "dialect-verify-ts-"));
  try {
    const at = (name: string, bytes: Uint8Array | string) => {
      writeFileSync(join(dir, name), bytes);
      return join(dir, name);
    };
    const files = ["--dialect", at("dialect", "{"), "--case", at("case", valid.case), "--profiles", at("profiles", valid.profiles), "--preparation", at("preparation", valid.preparation)];
    const refusal = program(...files);
    assert.deepEqual([refusal.status, refusal.stdout], [1, '{"refusal":"input-malformed","result":"refusal"}\n']);
    for (const args of [[join(dir, "no-such-vector")], [...files, "--an-option-it-does-not-take"], files.slice(2), [...files.slice(0, 7), join(dir, "no-such-file")]]) {
      const run = program(...args);
      assert.deepEqual([run.status, run.stdout], [3, ""], args.join(" "));
    }
    // a preparation file it was asked to write and cannot open: it could not run, and writes no report
    const unwritable = program(join(VECTORS, "escaped-strings"), "--emit-preparation", join(dir, "no-such-directory", "preparation.json"));
    assert.deepEqual([unwritable.status, unwritable.stdout], [3, ""]);

    // a case-only reading whose facts hold -0: the report keeps the literal, as §9.5 writes a number
    const minus = [
      "--dialect", at("d", '{"version":2,"case":{"facts":[{"target":"/n","source":"/n"}],"evidence":[]}}'),
      "--case", at("c", '{"n":-0}'),
      "--profiles", at("p", "[]"),
    ];
    const first = program(...minus, "--preparation", at("given", '{"verifiedAt":"2026-10-14T00:00:00Z"}'), "--emit-preparation", join(dir, "recomputed"));
    assert.equal(first.status, 2, first.stdout);
    const second = program(...minus, "--preparation", join(dir, "recomputed"));
    assert.equal(second.status, 0, second.stdout);
    assert.ok(second.stdout.includes('"facts":{"n":-0}') && second.stdout.includes('"binding":"not-checked"'), second.stdout);
    assert.equal(readFileSync(join(dir, "recomputed"), "utf8").includes('"n":-0'), true);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

// ---- the shapes of an `operation` (§4.1, §5.2, the amendment of 2026-10-15), and version 3 (§11) ----
// Written by the amendment's author, who had read both readers: no part of this reader's independence.

const httpShaped = loadVector(join(VECTORS, "http-shaped-source"), true);

type Alteration = { profile?: (p: JObj) => void; dialect?: (d: JObj) => void; receipt?: (r: JObj) => void; request?: JVal };

/** The vector's inputs altered, each receipt signed again under a key generated here and its profile's digest
 * written into the dialect; with `request`, the receipt commits to that request under the vector's salt. */
function alteredAndSigned(base: Inputs, change: Alteration): Inputs {
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  const raw = Buffer.from(publicKey.export({ format: "jwk" }).x as string, "base64url");
  const hex = (b: Uint8Array) => Buffer.from(b).toString("hex");
  const sha = (b: Uint8Array) => hex(createHash("sha256").update(b).digest());
  const profiles = parse(text(base.profiles)) as { a: JObj[] };
  for (const p of profiles.a) {
    change.profile?.(p);
    p.m.set("publicKey", str(hex(raw)));
  }
  const digests = new Map(profiles.a.map((p) => [(p.m.get("id") as { v: string }).v, "sha256:" + sha(canon(p))]));
  const dialect = parse(text(base.dialect)) as JObj;
  change.dialect?.(dialect);
  for (const s of (dialect.m.get("sources") as { a: JObj[] }).a) s.m.set("profileDigest", str(digests.get((s.m.get("profile") as { v: string }).v)!));
  const acquisitions = parse(text(base.acquisitions)) as JObj;
  for (const [, a] of acquisitions.m) {
    const response = member(a, "response") as JObj;
    const receipt = response.m.get("receipt") as JObj;
    change.receipt?.(receipt);
    if (change.request !== undefined) {
      const salt = Buffer.from((member(response.m.get("salts"), "args") as { v: string }).v, "hex");
      receipt.m.set("argumentsCommitment", str("sha256:" + sha(Buffer.concat([salt, Buffer.from("args:"), canon(change.request)]))));
    }
    receipt.m.set("keyId", str(sha(raw).slice(0, 32)));
    receipt.m.delete("signature");
    receipt.m.set("signature", str(hex(nodeSign(null, Buffer.concat([Buffer.from("judgment-pack-gateway/receipt/3:"), canon(receipt)]), privateKey))));
  }
  return { ...base, dialect: canon(dialect), profiles: canon(profiles as unknown as JVal), acquisitions: canon(acquisitions) };
}
const sourceOf = (d: JObj) => (d.m.get("sources") as { a: JObj[] }).a[0];
const shapeOf = (shape: string, tools?: string[]) => (p: JObj) => {
  p.m.set("shape", str(shape));
  if (tools === undefined) p.m.delete("tools");
  else p.m.set("tools", parse(JSON.stringify(tools)));
};

test("§4.1: the tenth vector's request is adapter-http's method, path and query, not a tool call", () => {
  const r = verify(httpShaped);
  assert.equal(r.kind, "reading");
  const intake = (member(parse(text(r.recomputed!)), "outcomes") as { a: JObj[] }).a[1];
  assert.equal(text(preparationForm(member(intake, "arguments")!)), '{"method":"GET","path":"/intake/requests","query":{"id":"REQ-7"}}');
});

test("§4.1, §5.1: a request that does not fit its profile is profile-mismatch", () => {
  // the http request under a profile of shape mcp, and under one of shape command, which serves none
  assert.equal(verdict(alteredAndSigned(httpShaped, { profile: shapeOf("mcp", ["requests"]) })), "finding:profile-mismatch");
  assert.equal(verdict(alteredAndSigned(httpShaped, { profile: shapeOf("command") })), "finding:profile-mismatch");
  // under mcp, a request is exactly a tool call
  for (const near of [
    '{"tool":"requests","arguments":{"id":{"$param":"requestId"}},"path":"/intake/requests"}',
    '{"tool":"requests"}',
    '{"tool":{"$param":"requestId"},"arguments":{}}',
  ]) {
    const asked = (d: JObj) => sourceOf(d).m.set("arguments", parse(near));
    assert.equal(verdict(alteredAndSigned(httpShaped, { profile: shapeOf("mcp", ["requests"]), dialect: asked })), "finding:profile-mismatch", near);
  }
});

test("§4.1: an http request is an object held to the template rules and its commitment, not to a member set", () => {
  const request = (to: string) => verdict({ ...httpShaped, dialect: edit(httpShaped.dialect, '"arguments":{"path":"/intake/requests","method":"GET","query":{"id":{"$param":"requestId"}}}', `"arguments":${to}`) });
  // not an object, a template form, or outside the template rules: refused with the dialect
  for (const bad of ['"/intake/requests"', "[]", '{"$param":"requestId"}', '{"path":{"$param":"nope"}}', '{"path":{"$param":"runAt"}}']) {
    assert.equal(request(bad), "refusal:input-malformed", bad);
  }
  // any other object is of the form, and the receipt does not commit it (§5.2, check 4)
  for (const other of [
    '{"path":"/intake/requests","method":"GET","query":{"id":"REQ-8"}}',
    '{"path":"/intake/requests","method":"GET"}',
    '{"path":"/intake/requests","method":"PUT","query":{"id":"REQ-7"}}',
    '{"path":"/intake/requests","method":"POST","query":{"id":"REQ-7"},"body":{"id":"REQ-7"}}',
    '{"tool":"requests","arguments":{"id":{"$param":"requestId"}}}',
    "{}",
  ]) {
    assert.equal(request(other), "finding:acquisition-invalid", other);
  }
  // under adapter-http, a query is an object of string templates
  for (const query of ['{"id":7}', '{"id":true}', '{"id":["REQ-7"]}', '{"$param":"requestId"}', '"id=REQ-7"']) {
    assert.equal(request(`{"path":"/intake/requests","method":"GET","query":${query}}`), "finding:profile-mismatch", query);
  }
  const withInteger = edit(httpShaped.dialect, '"parameters":{"requestId":{"pointer":"/id","type":"string"}}', '"parameters":{"requestId":{"pointer":"/id","type":"string"},"n":{"pointer":"/n","type":"integer"}}');
  const integerQuery = (to: string) => verdict({ ...httpShaped, dialect: edit(withInteger, '"query":{"id":{"$param":"requestId"}}', `"query":${to}`) });
  assert.equal(integerQuery('{"id":{"$param":"n"}}'), "finding:profile-mismatch");
  assert.equal(integerQuery('{"id":{"$text":"REQ-{{n}}"}}'), "finding:parameter-invalid"); // of the form; the case has no /n
});

test("§4.1: a connection's request is read under its own adapter", () => {
  // The form a gateway connection takes (adapters/README.md), whose `query` is a WIQL string.
  const connection = '{"connection":"board","revision":"' + "0".repeat(64) + '","read":"workitems.query","query":"SELECT [System.Id] FROM WorkItems","top":50}';
  const asked = (d: JObj) => sourceOf(d).m.set("arguments", parse(connection));
  const adapterName = (name: string) => (p: JObj) => (p.m.get("adapter") as JObj).m.set("name", str(name));
  const receiptAdapter = (name: string) => (r: JObj) => (member(r.m.get("acquisition"), "adapter") as JObj).m.set("name", str(name));
  assert.equal(
    verdict(alteredAndSigned(httpShaped, { profile: adapterName("adapter-sources"), dialect: asked, receipt: receiptAdapter("adapter-sources"), request: parse(connection) })),
    "finding:preparation-differs",
  );
  // under adapter-http, its query is of another form
  assert.equal(verdict(alteredAndSigned(httpShaped, { dialect: asked, request: parse(connection) })), "finding:profile-mismatch");
});

test("§5.2: the record's acquisition.shape is the profile's", () => {
  assert.equal(verdict(alteredAndSigned(httpShaped, {})), "finding:preparation-differs"); // signed again, every check passes
  const shape = (to: string) => (r: JObj) => (r.m.get("acquisition") as JObj).m.set("shape", str(to));
  assert.equal(verdict(alteredAndSigned(httpShaped, { receipt: shape("mcp") })), "finding:acquisition-invalid");
  assert.equal(verdict(alteredAndSigned(httpShaped, { receipt: shape("airbyte") })), "finding:acquisition-invalid");
});

test("§5.2: a receipt that attests a page is not read, whatever the shape", () => {
  const paged = (r: JObj) => (r.m.get("acquisition") as JObj).m.set("pageItems", parse(`[${JSON.stringify((r.m.get("resultDigest") as { v: string }).v)}]`));
  assert.equal(verdict(alteredAndSigned(httpShaped, { receipt: paged })), "finding:acquisition-invalid");
  assert.equal(verdict(alteredAndSigned(valid, { receipt: paged })), "finding:acquisition-invalid");
});

test("§5.2: a paged mcp receipt is refused, the amendment's one restriction (review round 5, finding 1)", () => {
  // Read under the accepted text, refused under the amendment: the one answer it changes for an input that was
  // read before. The valid vector, signed again: without the page every check passes, with it the acquisition
  // is refused.
  assert.equal(verdict(alteredAndSigned(valid, {})), "finding:preparation-differs");
  const paged = (r: JObj) => (r.m.get("acquisition") as JObj).m.set("pageItems", arr([r.m.get("resultDigest")!]));
  assert.equal(verdict(alteredAndSigned(valid, { receipt: paged })), "finding:acquisition-invalid");
});

test("§4.1: a stream read under a profile of shape airbyte is read as its shape gives it", () => {
  const asAirbyte = (stream: string, receipt?: (r: JObj) => void): Alteration => ({
    profile: shapeOf("airbyte"),
    dialect: (d) => sourceOf(d).m.set("arguments", parse(stream)),
    receipt: (r) => {
      (r.m.get("acquisition") as JObj).m.set("shape", str("airbyte"));
      receipt?.(r);
    },
    request: parse(stream),
  });
  const paged = (r: JObj) => (r.m.get("acquisition") as JObj).m.set("pageItems", arr([]));
  // adapter-airbyte's stream read, and an object of other members: the request is not a member set
  for (const stream of ['{"stream":"requests","namespace":null,"limit":10}', '{"stream":"requests","syncMode":"full_refresh"}']) {
    assert.equal(verdict(alteredAndSigned(httpShaped, asAirbyte(stream))), "finding:preparation-differs", stream);
    assert.equal(verdict(alteredAndSigned(httpShaped, asAirbyte(stream, paged))), "finding:acquisition-invalid", stream);
  }
});

// ---- dialect version 3 (§4.3, §4.4, §9.1), the Runner's eleventh and twelfth vectors ----
// Written by the author who extended both readers to version 3, who had read both: no part of this reader's
// independence.

test("§11: a dialect of version 3 is read, and its form checked", () => {
  const unbound = '"platform":"intake","operation":"requests","shape":"http","record":"adapter-http","maxAge":300';
  const asUnbound = (b: Uint8Array) => edit(b, '"profile":"intake","profileDigest":"sha256:dec2468ef46d4026c7f813ff768aba66d2d8e7891e8b8ecb99fb099ef3fd363e","maxAge":300', unbound);
  // written as version 3 is, without the members of version 2 alone (§2)
  const v2Tail = '"version":2,"provider":"","facts":null,"evidence":null';
  // read as version 3: its preparation is another, of version 3 and another digest
  assert.equal(verdict({ ...httpShaped, dialect: edit(httpShaped.dialect, v2Tail, '"version":3') }), "finding:preparation-differs");
  // its form is checked: the members of version 2 alone, an unbound source with no binding document, and a member
  // of no form
  assert.equal(verdict({ ...httpShaped, dialect: edit(httpShaped.dialect, '"version":2', '"version":3') }), "refusal:input-malformed");
  assert.equal(verdict({ ...httpShaped, dialect: edit(asUnbound(httpShaped.dialect), v2Tail, '"version":3') }), "refusal:input-malformed");
  assert.equal(verdict({ ...httpShaped, dialect: edit(httpShaped.dialect, v2Tail, '"version":3,"Version":"x"') }), "refusal:input-malformed");
  // an unbound source in a version-2 dialect, and a version this document does not define
  assert.equal(verdict({ ...httpShaped, dialect: asUnbound(httpShaped.dialect) }), "refusal:input-malformed");
  assert.equal(verdict({ ...httpShaped, dialect: edit(httpShaped.dialect, '"version":2', '"version":4') }), "refusal:input-malformed");
  assert.equal(verdict({ ...httpShaped, dialect: edit(httpShaped.dialect, '"version":2', '"version":3.0') }), "refusal:input-malformed");
  // the bounds measured before it come first
  assert.equal(verdict({ ...httpShaped, dialect: edit(httpShaped.dialect, v2Tail, '"version":3'), case: utf8("[".repeat(33) + "]".repeat(33)) }), "refusal:input-over-bound");
});

const imported = loadVector(join(VECTORS, "unbound-bound-at-import"), true);
const v3bound = loadVector(join(VECTORS, "version-3-bound"), true);
const sha = (b: Uint8Array) => createHash("sha256").update(b).digest("hex");

/** The import vector's inputs, its published dialect altered and the binding document's `dialect` written again as its
 * digest; then the binding document altered. */
function importedWith(change: { unbound?: (d: JObj) => void; binding?: (b: JObj) => void }): Inputs {
  const dialect = parse(text(imported.dialect)) as JObj;
  change.unbound?.(dialect);
  const binding = parse(text(imported.binding!)) as JObj;
  binding.m.set("dialect", str("sha256:" + sha(canon(dialect))));
  change.binding?.(binding);
  return { ...imported, dialect: canon(dialect), binding: canon(binding) };
}

test("§4.4: the bound dialect is the vector's mapping.json, and the preparation commits it alone", () => {
  const dir = join(VECTORS, "unbound-bound-at-import");
  const dialect = parse(text(imported.dialect)) as JObj;
  const binding = readBinding(parse(text(imported.binding!)));
  const mapping = parse(readFileSync(join(dir, "mapping.json"), "utf8"));
  assert.equal((binding.m.get("dialect") as { v: string }).v, "sha256:" + sha(canon(dialect)));
  assert.equal(text(canon(bindDialect(dialect, binding))), text(canon(mapping)));
  const r = verify(imported);
  assert.equal(r.kind, "reading");
  const preparation = text(r.recomputed!);
  assert.ok(preparation.includes(`"mappingDigest":"sha256:${sha(canon(mapping))}"`) && preparation.endsWith('"version":3}'));
  // neither the published dialect's digest, nor the binding document's, nor the catalog names
  for (const absent of [(binding.m.get("dialect") as { v: string }).v, sha(canon(binding)), "intake-api", "requests.read"]) {
    assert.ok(!preparation.includes(absent), absent);
  }
  // the bound dialect, given as the dialect with no binding document, is read alike
  const direct = verify({ ...imported, dialect: Uint8Array.from(readFileSync(join(dir, "mapping.json"))), binding: undefined });
  assert.equal(direct.kind, "reading");
  assert.ok(Buffer.from(direct.recomputed!).equals(readFileSync(join(dir, "preparation.json"))));
});

test("§9.1: a version-3 document is read as version 2's, its preparation of version 3", () => {
  const r = verify({ ...v3bound, dialect: edit(v3bound.dialect, '"version":3', '"version":2') });
  assert.equal(r.kind, "finding");
  const given = JSON.parse(readFileSync(join(VECTORS, "version-3-bound", "preparation.json"), "utf8")) as Record<string, unknown>;
  const recomputed = JSON.parse(text(r.recomputed!)) as Record<string, unknown>;
  assert.equal(recomputed.version, 2);
  for (const k of ["version", "mappingDigest"]) {
    delete given[k];
    delete recomputed[k];
  }
  assert.deepEqual(recomputed, given);
});

test("§9.1: cites are ordered by callIndex in versions 2 and 3 alike, as the Runner writes them", () => {
  // Review round 7, finding 1. unsigned-parameters' two sources, vendor then registry, their callIndex swapped and
  // signed again: in the order of sources the indices are [1, 0], and cites is [0, 1].
  const base = loadVector(join(VECTORS, "unsigned-parameters"), false);
  for (const [version, expected] of [["2", ["registry", "vendor"]], ["3", ["registry", "vendor"]]] as const) {
    const swapped = alteredAndSigned(base, {
      dialect: (d) => {
        d.m.set("version", num(version));
        if (version === "3") for (const k of ["provider", "facts", "evidence"]) d.m.delete(k); // version 2's alone (§2)
      },
      receipt: (rc) => rc.m.set("callIndex", num(String(1 - Number((rc.m.get("callIndex") as { lit: string }).lit)))),
    });
    const r = verify(swapped);
    assert.equal(r.kind, "finding", version);
    const preparation = JSON.parse(text(r.recomputed!)) as {
      lineage: { source: string; receipt?: { signature: string; callIndex: number } }[];
      cites: { signature: string; callIndex: number }[];
    };
    const sourceOfCite = new Map(preparation.lineage.filter((e) => e.receipt !== undefined).map((e) => [e.receipt!.signature, e.source]));
    const indexOf = new Map(preparation.lineage.filter((e) => e.receipt !== undefined).map((e) => [e.source, e.receipt!.callIndex]));
    assert.deepEqual(preparation.cites.map((c) => sourceOfCite.get(c.signature)), expected, version);
    assert.deepEqual([indexOf.get("vendor"), indexOf.get("registry")], [1, 0], version);
    assert.deepEqual(preparation.cites.map((c) => c.callIndex), [0, 1], version);
  }
});

// Round 9 of RFC 0018 (issue #182 item 4; §5.2, check 1, and §11, finding 3): the cases of tests/test_dialect.py's
// receipt_cases(), each receipt signed again, so that the member named is the one change the later checks see.
test("§5.2, §11 (round 9): a receipt member of another form is acquisition-invalid before the time and session rules, in versions 2 and 3", () => {
  const invalid = "finding:acquisition-invalid";
  const differs = "finding:preparation-differs";
  type Put = (r: JObj) => void;
  const put = (k: string, v?: JVal): Put => (r) => void (v === undefined ? r.m.delete(k) : r.m.set(k, v));
  const observed = (v: JVal): Put => (r) => void (r.m.get("acquisition") as JObj).m.set("observedAt", v);
  // each vector's servedAt 301 seconds before its verifiedAt, past the source's maxAge of 300
  for (const [vector, base, old] of [["valid", valid, "2026-10-14T14:53:25Z"], ["version-3-bound", v3bound, "2026-10-15T15:39:11Z"]] as const) {
    const cases: [string, string, Put][] = [
      ["servedAt a number", invalid, put("servedAt", num("1760453906"))],
      ["servedAt null", invalid, put("servedAt", parse("null"))],
      ["servedAt absent", invalid, put("servedAt")],
      ["servedAt a string of another form", invalid, put("servedAt", str("2026-10-14T14:58:26.000Z"))],
      ["observedAt a string that names no time", invalid, observed(str("2026-02-30T14:58:26Z"))],
      ["observedAt a number", invalid, observed(num("0"))],
      ["callIndex a string", invalid, put("callIndex", str("0"))],
      ["callIndex below zero", invalid, put("callIndex", num("-1"))],
      ["callIndex true", invalid, put("callIndex", parse("true"))],
      ["callIndex absent", invalid, put("callIndex")],
      ["sessionId a number", invalid, put("sessionId", num("0"))],
      ["sessionId null", invalid, put("sessionId", parse("null"))],
      ["sessionId absent", invalid, put("sessionId")],
      // any string: not held to the gateway's token form
      ["sessionId empty", differs, put("sessionId", str(""))],
      ["sessionId of no token form", differs, put("sessionId", str("a session, not a token: \u00fcn\u00efcode"))],
      // a present instant outside the window is still stale; a malformed member beside it is the form first
      ["servedAt expired", "finding:acquisition-stale", put("servedAt", str(old))],
      ["observedAt expired and callIndex a string: the form first", invalid, (r) => (observed(str(old))(r), put("callIndex", str("0"))(r))],
      // review round of pull request 186: the time is read in `acquisition` alone; one moved to the top level is absent
      ["observedAt moved to the receipt's top level", invalid, (r) => {
        const a = r.m.get("acquisition") as JObj;
        r.m.set("observedAt", a.m.get("observedAt")!);
        a.m.delete("observedAt");
      }],
    ];
    for (const [name, expected, change] of cases) {
      assert.equal(answer(() => resigned(base, (_, __, r) => change(r))), expected, `${vector}: ${name}`);
    }
  }
  // two receipts, vendor at callIndex 0 and registry at 1 of one session: a well-formed set in neither form is
  // acquisition-sessions; a malformed member of the second receipt is acquisition-invalid
  const registry = (id: JVal, index: JVal) => (name: string, _: JObj, r: JObj) => {
    if (name !== "registry") return;
    r.m.set("sessionId", id);
    r.m.set("callIndex", index);
  };
  const cases: [string, string, JVal, JVal][] = [
    ["a second session whose call is not its first", "finding:acquisition-sessions", str("another.session"), num("1")],
    ["one session, one callIndex twice", "finding:acquisition-sessions", str("mapping.session"), num("0")],
    ["each alone in a session of its own, each its first call", differs, str("another.session"), num("0")],
    ["the second receipt's callIndex a string", invalid, str("mapping.session"), str("1")],
    ["the second receipt's callIndex below zero", invalid, str("mapping.session"), num("-1")],
    ["the second receipt's sessionId a number", invalid, num("1"), num("1")],
  ];
  for (const [name, expected, id, index] of cases) {
    assert.equal(answer(() => resigned(twoSources, registry(id, index))), expected, `unsigned-parameters: ${name}`);
  }
});

test("§4.4: the binding document is held to its form and to the dialect it binds", () => {
  assert.equal(verdict(importedWith({})), "reading:matches");
  const entry = (b: JObj) => member(b.m.get("sources"), "intake") as JObj;
  const probes: [string, (b: JObj) => void][] = [
    ["a binding for another dialect", (b) => b.m.set("dialect", str("sha256:" + "0".repeat(64)))],
    ["a source more", (b) => (b.m.get("sources") as JObj).m.set("other", entry(b))],
    ["no source", (b) => b.m.set("sources", obj())],
    ["a name but for case", (b) => b.m.set("sources", obj([["Intake", entry(b)]]))],
    ["a member more", (b) => b.m.set("version", num("1"))],
    ["an entry member more", (b) => entry(b).m.set("shape", str("http"))],
    ["an empty profile", (b) => entry(b).m.set("profile", str(""))],
    ["a profileDigest that is not a digest", (b) => entry(b).m.set("profileDigest", str("sha256:XYZ"))],
    ["a dialect that is not a digest", (b) => b.m.set("dialect", str((b.m.get("dialect") as { v: string }).v.toUpperCase()))],
    ["sources that are an array", (b) => b.m.set("sources", arr([entry(b)]))],
  ];
  for (const [name, alter] of probes) assert.equal(verdict(importedWith({ binding: alter })), "refusal:input-malformed", name);
  // the published dialect changed under a binding of the dialect as it was
  assert.equal(verdict({ ...imported, dialect: edit(imported.dialect, '"maxAge":300', '"maxAge":301') }), "refusal:input-malformed");
  // an unbound source and no binding document; a binding document beside a dialect with none
  assert.equal(verdict({ ...imported, binding: undefined }), "refusal:input-malformed");
  assert.equal(verdict({ ...v3bound, binding: imported.binding }), "refusal:input-malformed");
  assert.equal(verdict({ ...valid, binding: imported.binding }), "refusal:input-malformed");
  // read as a document; its bounds measured on bytes first (§12)
  assert.equal(verdict({ ...imported, binding: utf8("{") }), "refusal:input-malformed");
  const padded = (n: number) => utf8(text(imported.binding!) + " ".repeat(n - imported.binding!.length));
  assert.equal(verdict({ ...imported, binding: padded(65536) }), "reading:matches");
  assert.equal(verdict({ ...imported, binding: padded(65537) }), "refusal:input-over-bound");
  assert.equal(verdict({ ...imported, binding: utf8("[".repeat(65) + "]".repeat(65)) }), "refusal:input-over-bound");
});

test("§4.4: an unbound source is held to its form", () => {
  const source = (d: JObj) => (d.m.get("sources") as { a: JObj[] }).a[0];
  const probes: [string, (d: JObj) => void][] = [
    ["a shape of command", (d) => source(d).m.set("shape", str("command"))],
    ["an empty platform", (d) => source(d).m.set("platform", str(""))],
    ["a record that is not a string", (d) => source(d).m.set("record", num("7"))],
    ["a profile beside the catalog names", (d) => source(d).m.set("profile", str("intake"))],
    ["no operation", (d) => source(d).m.delete("operation")],
    ["a version-2 document", (d) => d.m.set("version", num("2"))],
  ];
  for (const [name, alter] of probes) assert.equal(verdict(importedWith({ unbound: alter })), "refusal:input-malformed", name);
});

test("§4.4, §5.1: a profile bound of another shape or record is profile-mismatch", () => {
  const source = (d: JObj) => (d.m.get("sources") as { a: JObj[] }).a[0];
  const entry = (b: JObj) => member(b.m.get("sources"), "intake") as JObj;
  const probes: [string, { unbound?: (d: JObj) => void; binding?: (b: JObj) => void }][] = [
    ["another shape", { unbound: (d) => source(d).m.set("shape", str("mcp")) }],
    ["another record", { unbound: (d) => source(d).m.set("record", str("adapter-airbyte")) }],
    ["an untrusted profile", { binding: (b) => entry(b).m.set("profile", str("another")) }],
    ["another profile digest", { binding: (b) => entry(b).m.set("profileDigest", str("sha256:" + "1".repeat(64))) }],
  ];
  for (const [name, change] of probes) assert.equal(verdict(importedWith(change)), "finding:profile-mismatch", name);
});

test("§4.3: http, sql and web are held to their forms, and not read (research is read: below)", () => {
  const fx = sourceOf(parse(text(v3bound.dialect)) as JObj);
  const common = `"profile":"fx","profileDigest":${JSON.stringify((fx.m.get("profileDigest") as { v: string }).v)},"maxAge":300,"read":{"copy":{"facts":[],"evidence":[]}}`;
  const param = '{"$param":"invoiceCurrency"}';
  const wellFormed: Record<string, Record<string, string>> = {
    http: { method: '"POST"', path: '"/requests"', query: `{"currency":${param}}`, body: '{"n":1}', headers: '["Accept"]' },
    sql: { statement: '"SELECT 1 WHERE c = :c"', bindings: `[{"name":"c","type":"STRING","value":${param}}]` },
    web: { url: param },
  };
  const malformedMembers: Record<string, [string, string][]> = {
    http: [["method", '"PUT"'], ["path", '{"a":1}'], ["path", '{"$param":"runAt"}'], ["method", '"GET"'], ["query", '{"currency":7}'], ["headers", '"Accept"']],
    sql: [["statement", '{"$text":"SELECT 1"}'], ["bindings", '[{"name":"c","type":"STRING","value":"EUR"}]'], ["bindings", `[{"name":"c","value":${param}}]`]],
    web: [["url", "7"], ["url", '{"$param":"nope"}'], ["url", '{"$text":"https://example.org/"}']],
  };
  const source = (kind: string, members: Record<string, string>) =>
    `{"name":"more","kind":"${kind}",${common}${Object.entries(members).map(([k, v]) => `,"${k}":${v}`).join("")}}`;
  const withSource = (base: Inputs, s: string, version = "3") =>
    verdict({ ...base, dialect: edit(edit(base.dialect, '"version":3', `"version":${version}`), '"sources":[', `"sources":[${s},`) });
  for (const [kind, members] of Object.entries(wellFormed)) {
    assert.equal(withSource(v3bound, source(kind, members)), "refusal:kind-unread", kind);
    // in a version-2 document, a kind of version 3 is refused
    assert.equal(withSource(v3bound, source(kind, members), "2"), "refusal:input-malformed", kind);
    // a member more, and one of its own left out
    assert.equal(withSource(v3bound, source(kind, { ...members, arguments: "{}" })), "refusal:input-malformed", kind);
    const first = Object.keys(members)[0];
    assert.equal(withSource(v3bound, source(kind, Object.fromEntries(Object.entries(members).filter(([k]) => k !== first)))), "refusal:input-malformed", kind);
    for (const [k, v] of malformedMembers[kind]) {
      assert.equal(withSource(v3bound, source(kind, { ...members, [k]: v })), "refusal:input-malformed", `${kind}.${k} ${v}`);
    }
  }
  // the members of version 3's kinds that the Runner's encoding keeps written empty are read so
  for (const [k, empty] of [["headers", "[]"], ["query", "{}"], ["body", "{}"]]) {
    assert.equal(withSource(v3bound, source("http", { ...wellFormed.http, [k]: empty })), "refusal:kind-unread", `http.${k} ${empty}`);
  }
  // a kind of another type is refused
  for (const kind of ['["web"]', '{"web":1}', "3", "null"]) {
    assert.equal(withSource(v3bound, `{"name":"more","kind":${kind},${common},"url":"x"}`), "refusal:input-malformed", kind);
  }
  // selected-file is of version 3 too, and not read
  assert.equal(withSource(v3bound, '{"name":"upload","kind":"selected-file","provider":"local-file","read":{"copy":{"facts":[],"evidence":[]}}}'), "refusal:kind-unread");
  // every form comes first, the binding document's too: a binding of the dialect as it was is refused before the kind
  const web = `{"name":"page","kind":"web",${common},"url":"https://example.org/"}`;
  assert.equal(withSource(imported, web), "refusal:input-malformed");
  const withWeb = importedWith({ unbound: (d) => (d.m.get("sources") as { a: JVal[] }).a.push(parse(web)) });
  assert.equal(verdict(withWeb), "refusal:kind-unread");
  assert.equal(verdict({ ...withWeb, binding: undefined }), "refusal:input-malformed");
});

test("§2: version 3 carries no member of version 2 alone: provider, facts and evidence", () => {
  // refused in version 3; in version 2 each is read, as the version-2 vectors write all three
  for (const [k, value] of [["provider", '""'], ["facts", "null"], ["evidence", "null"]]) {
    for (const [version, expected] of [["3", "refusal:input-malformed"], ["2", "finding:preparation-differs"]]) {
      const written = edit(v3bound.dialect, '"version":3}', `"version":${version},"${k}":${value}}`);
      assert.equal(verdict({ ...v3bound, dialect: written }), expected, `${k} in version ${version}`);
    }
  }
});

test("§2: version 3 leaves an optional member out when it is empty", () => {
  // Written as [] or {}, a member the Runner's encoding leaves out when empty is refused in version 3 (review round 7,
  // finding 2); each alteration is read in version 2, so that its emptiness alone is what version 3 refuses. The
  // members the encoding keeps written empty are read in both versions.
  const source = (d: JObj) => (d.m.get("sources") as { a: JObj[] }).a[0];
  const copy = (d: JObj) => member(source(d).m.get("read"), "copy") as JObj;
  const refused: [string, (d: JObj) => void][] = [
    ["unmapped", (d) => d.m.set("unmapped", arr([]))],
    ["unmappedEvidence", (d) => d.m.set("unmappedEvidence", arr([]))],
    ["admits.facts", (d) => d.m.set("admits", obj([["facts", obj()]]))],
    ["admits.evidence", (d) => d.m.set("admits", obj([["evidence", obj()]]))],
    ["a source's parameters", (d) => source(d).m.set("parameters", obj())],
  ];
  const kept: [string, (d: JObj) => void][] = [
    ["admits", (d) => d.m.set("admits", obj())],
    ["a copy's facts", (d) => copy(d).m.set("facts", arr([]))],
    ["a copy's evidence", (d) => copy(d).m.set("evidence", arr([]))],
  ];
  for (const [name, alter] of [...refused, ...kept]) {
    const inVersion3 = refused.some(([n]) => n === name) ? "refusal:input-malformed" : "finding:preparation-differs";
    for (const [version, expected] of [["3", inVersion3], ["2", "finding:preparation-differs"]]) {
      const d = parse(text(v3bound.dialect)) as JObj;
      d.m.set("version", num(version));
      alter(d);
      assert.equal(verdict({ ...v3bound, dialect: canon(d) }), expected, `${name} in version ${version}`);
    }
  }
  // A case-only dialect: `sources` and the case's `parameters` written empty. The case's own `facts` and
  // `evidence` are required, not optional, and are written empty in every version.
  const caseOnly = (version: string, more: string, caseMore = "") => ({
    ...valid,
    dialect: utf8(`{"version":${version},"case":{${caseMore}"facts":[],"evidence":[]}${more}}`),
    acquisitions: utf8("{}"),
    preparation: utf8('{"verifiedAt":"2026-10-14T00:00:00Z"}'),
    record: undefined,
    requireBinding: false,
  });
  for (const version of ["2", "3"]) {
    assert.equal(verdict(caseOnly(version, "")), "finding:preparation-differs", version);
    const refused = version === "3" ? "refusal:input-malformed" : "finding:preparation-differs";
    assert.equal(verdict(caseOnly(version, ',"sources":[]')), refused, `sources in version ${version}`);
    assert.equal(verdict(caseOnly(version, "", '"parameters":{},')), refused, `the case's parameters in version ${version}`);
  }
});

test("the program takes --binding, and reads a vector bound at import from its directory", () => {
  const dir = join(VECTORS, "unbound-bound-at-import");
  const fromDirectory = program(dir, "--require-binding");
  assert.equal(fromDirectory.status, 0, fromDirectory.stderr);
  assert.ok(fromDirectory.stdout.includes('"binding":"matches"'), fromDirectory.stdout);
  const tmp = mkdtempSync(join(tmpdir(), "dialect-verify-ts-"));
  try {
    const at = (name: string, bytes: Uint8Array) => {
      writeFileSync(join(tmp, name), bytes);
      return join(tmp, name);
    };
    const files = [
      "--dialect", at("d", imported.dialect), "--case", at("c", imported.case), "--acquisitions", at("a", imported.acquisitions),
      "--profiles", at("p", imported.profiles), "--preparation", at("g", imported.preparation), "--record", at("r", imported.record!), "--require-binding",
    ];
    const withBinding = program(...files, "--binding", at("b", imported.binding!));
    assert.equal(withBinding.status, 0, withBinding.stderr);
    const without = program(...files);
    assert.deepEqual([without.status, without.stdout], [1, '{"refusal":"input-malformed","result":"refusal"}\n']);
    // a binding document is not taken beside a vector directory, which names its own
    const beside = program(dir, "--binding", join(tmp, "b"));
    assert.deepEqual([beside.status, beside.stdout], [3, ""]);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

// ---- review round 7: a copy's arrays, a binding of null, and research acquisitions (§§4.3, 5.2, 6.2, 11, 12) ----

test("§6.2: a copy has both its arrays, in every version", () => {
  for (const version of ["2", "3"]) {
    for (const [written, expected] of [
      ["{}", "refusal:input-malformed"],
      ['{"facts":[]}', "refusal:input-malformed"],
      ['{"evidence":[]}', "refusal:input-malformed"],
      ['{"facts":[],"evidence":[]}', "finding:preparation-differs"],
    ]) {
      const d = parse(text(v3bound.dialect)) as JObj;
      d.m.set("version", num(version));
      (member(sourceOf(d).m.get("read"), "copy") as JObj).m.clear();
      for (const [k, x] of (parse(written) as JObj).m) (member(sourceOf(d).m.get("read"), "copy") as JObj).m.set(k, x);
      assert.equal(verdict({ ...v3bound, dialect: canon(d) }), expected, `${written} in version ${version}`);
    }
  }
});

test("§4.4, §11: a binding document of null is refused, not taken as absent", () => {
  assert.equal(verdict({ ...v3bound, binding: utf8("null") }), "refusal:input-malformed");
  assert.equal(verdict({ ...imported, binding: utf8("null") }), "refusal:input-malformed");
});

// ---- the research contract (RFC 0018, round 8, issue #176) ----
// Hand-written documents of every new form and refusal, signed under a key generated here. The
// Runner's research vectors hold the kind as it records it; these are this reader's checks of its
// readings, not vectors. The repository's suite gives the first reader's cases
// (tests/test_dialect.py) to both readers and holds their reports equal.

type J = any;
const R_AT = "2026-10-15T12:00:00Z";
const R_SERVED = "2026-10-15T11:59:00Z";
const R_OBSERVED = "2026-10-15T11:58:30Z";
const R_EXPIRED = "2026-10-15T11:40:00Z"; // 20 minutes before the instant, past every maxAge here
const R_SALT = "5a".repeat(32);
const COMPANY = "Synthetic Company 0001";
const rKeys = generateKeyPairSync("ed25519");
const rPublic = Buffer.from(rKeys.publicKey.export({ format: "jwk" }).x as string, "base64url");
const jcopy = <T>(x: T): T => JSON.parse(JSON.stringify(x));
const asJ = (x: J): JVal => parse(JSON.stringify(x));
const rDigest = (x: J) => "sha256:" + sha(canon(asJ(x)));

function rProfile(id: string, source: string, adapter: string, research?: J, klass = "generated"): J {
  const p: J = {
    id,
    publicKey: rPublic.toString("hex"),
    class: klass,
    source,
    authority: "research.example.test",
    shape: "http",
    adapter: { name: adapter, version: "1.0.0", digest: "sha256:" + "ab".repeat(32) },
    endpoint: null,
  };
  if (research !== undefined) p.research = research;
  return p;
}

/** The trusted profiles: an AI profile for model-a and a web profile for search and page; and, for the refusals, one
 * of another model, one of search alone, one of class record, one with no declaration, and a web one of another model. */
const rProfiles = (): J[] => [
  rProfile("ai", "ai-answers", "adapter-ai", { capabilities: ["answer"], model: "model-a" }),
  rProfile("web", "web-pages", "adapter-web", { capabilities: ["search", "page"] }),
  rProfile("ai-b", "ai-answers", "adapter-ai", { capabilities: ["answer"], model: "model-b" }),
  rProfile("ai-2", "ai-answers-2", "adapter-ai", { capabilities: ["answer"], model: "model-a" }),
  rProfile("web-search", "web-pages", "adapter-web", { capabilities: ["search"] }),
  rProfile("web-record", "web-pages", "adapter-web", { capabilities: ["search", "page"] }, "record"),
  rProfile("web-b", "web-pages", "adapter-web", { capabilities: ["answer", "search", "page"], model: "model-b" }),
  rProfile("plain", "ai-answers", "adapter-ai"),
];

/** `gtm-company-person`'s company: all six types (§11's first example list); synthetic. */
const companyFields = (): J[] => [
  { name: "company-id", type: "text", required: true, description: "A synthetic company identifier." },
  { name: "employee-count", type: "integer", required: true, description: "Employees, as cited." },
  { name: "revenue", type: "decimal", required: false, description: "Annual revenue, a decimal string." },
  { name: "active", type: "boolean", required: false, description: "Whether the company trades." },
  { name: "roles", type: "text-list", required: false, description: "Roles the company hires for." },
  { name: "employee-range", type: "range", required: false, description: "The band of employees." },
];

/** A bound research source; each `profileDigest` names a profile by its id until the documents are built. */
function rSource(name: string, read: J, fields?: J[], capabilities = ["answer", "search", "page"]): J {
  return {
    name,
    kind: "research",
    maxAge: 600,
    question: { $param: "company" },
    constraints: { region: "EU", synthetic: true },
    model: "model-a",
    evidence: ["the page that states the headcount"],
    fields: fields ?? companyFields(),
    capabilities,
    profile: "ai",
    profileDigest: "ai",
    webProfiles: Object.fromEntries(capabilities.filter((c) => c !== "answer").map((c) => [c, { profile: "web", profileDigest: "web" }])),
    read,
  };
}

const answerResponse = (): J => ({ profile: "ai", request: { prompt: "Which company? (model-a)" }, result: { text: "Synthetic Company 0001 employs no one." } });
const searchResponse = (): J => ({ profile: "web", request: { query: "Synthetic Company 0001" }, result: { hits: ["https://company.example.test/about"] } });
const pageResponse = (): J => ({ profile: "web", request: { url: "https://company.example.test/about" }, result: { page: "Headcount: 0." } });
const companyAnswers = (): J => ({
  "company-id": { status: "found", value: "synthetic-company-0001", cites: [0] },
  "employee-count": { status: "found", value: 0, cites: [0, 2] },
  revenue: { status: "found", value: "-12.50", cites: [2] },
  active: { status: "found", value: false, cites: [0] },
  roles: { status: "found", value: [], cites: [1] },
  "employee-range": { status: "found", value: { min: "1.0", max: "1.00" }, cites: [2] },
});
const copyFields = (name: string): J => ({ copy: { facts: [{ target: `/${name}/fields`, source: "/fields" }], evidence: [] } });
const statusGuard = (entry: string, status: string): J => ({ op: "equals", field: `${entry}/status`, to: status });
const absenceGuard = (entry: string): J => ({ op: "not", of: { op: "exists", field: entry } });
const unavailable = (entry: string): J => ({ op: "any", of: [absenceGuard(entry), statusGuard(entry, "not-found"), statusGuard(entry, "stale")] });
const clause = (when: J, reason: string, target?: string, from?: string, status = "unknown"): J => ({
  when,
  claim: { facts: target === undefined ? [] : [{ pointer: target, from }], evidence: {}, acquisitionStatus: status },
  reason,
});
const PRIMARY = "/sources/primary/fields/employee-count";
const SECONDARY = "/sources/secondary/fields/employee-count";
const CURRENT = "/current/fields/employee-count";
const COUNT_TARGET = "/company/employee-count";

/** §6.4's example extended to a third source (§11, `failed-fallback`). */
const reconciliationRule = (): J => ({
  ruleVersion: "1",
  parameters: {},
  clauses: [
    clause(statusGuard(PRIMARY, "found"), "the primary found it", COUNT_TARGET, PRIMARY + "/value", "resolved"),
    clause({ op: "all", of: [unavailable(PRIMARY), statusGuard(SECONDARY, "found")] }, "the secondary found it", COUNT_TARGET, SECONDARY + "/value", "resolved"),
    clause({ op: "any", of: [PRIMARY, SECONDARY, CURRENT].map((e) => statusGuard(e, "conflicting")) }, "a conflict is not chosen"),
    clause({ op: "all", of: [unavailable(SECONDARY), statusGuard(CURRENT, "found")] }, "this source found it", COUNT_TARGET, CURRENT + "/value", "resolved"),
    clause(unavailable(CURRENT), "no candidate is left"),
    clause({ op: "always" }, "otherwise"),
  ],
});
const countOnly = (): J[] => [{ name: "employee-count", type: "integer", required: false, description: "Employees, as cited." }];
const observed = (name: string): J => ({ copy: { facts: [{ target: `/observed/${name}`, source: "/fields/employee-count/status" }], evidence: [] } });
function countAnswer(status: string, value = 7): J {
  if (status === "found") return { "employee-count": { status, value, cites: [0] } };
  if (status === "conflicting") return { "employee-count": { status, cites: [], values: [{ value: 7, cites: [0] }, { value: 9, cites: [0] }] } };
  if (status === "absent") return {};
  return { "employee-count": { status, cites: [] } };
}

/** One hand-written research run; a test alters any part before `documents()` builds and signs them. */
class Scenario {
  profiles: J[] = rProfiles();
  case: J = { company: COMPANY };
  admits: J = {};
  admitsEvidence: J = {};
  records: J = {};
  own = new Set<string>();
  unbound = new Set<string>();
  callIndices: Record<string, number[]> = {};
  receiptHooks: ((name: string, index: number | "own", receipt: J) => void)[] = [];
  afterHooks: ((documents: J) => void)[] = [];
  replacements: [string, string, string][] = [];
  dialect: J;
  constructor(kind: "company" | "reconcile" = "company") {
    let sources: J[];
    if (kind === "company") {
      sources = [rSource("company", copyFields("company"))];
      this.admits = { "/company/fields": ["generated"] };
      this.records = { company: { fields: companyAnswers(), responses: [answerResponse(), searchResponse(), pageResponse()] } };
    } else {
      sources = [
        rSource("primary", observed("primary"), countOnly(), ["answer"]),
        rSource("secondary", observed("secondary"), countOnly(), ["answer", "page"]),
        rSource("combined", { sources: ["primary", "secondary"], rule: reconciliationRule() }, countOnly(), ["answer"]),
      ];
      this.admits = { "/observed/primary": ["generated"], "/observed/secondary": ["generated"], [COUNT_TARGET]: ["generated"] };
      this.records = {
        primary: { fields: countAnswer("found", 7), responses: [answerResponse()] },
        secondary: { fields: countAnswer("found", 9), responses: [answerResponse(), pageResponse()] },
        combined: { fields: countAnswer("not-found"), responses: [] },
      };
    }
    this.dialect = {
      version: 3,
      case: { parameters: { company: { pointer: "/company", type: "string" } }, facts: [{ target: "/case/company", source: "/company" }], evidence: [] },
      sources,
    };
  }

  source(name: string): J {
    return this.dialect.sources.find((s: J) => s.name === name);
  }

  receipt(name: string, index: number | "own", profile: J, request: J, result: J, call: number): J {
    const receipt: J = {
      receiptVersion: "3",
      kind: "acquisition",
      keyId: sha(rPublic).slice(0, 32),
      source: profile.source,
      authority: profile.authority,
      sessionId: "research-session",
      callIndex: call,
      argumentsCommitment: "sha256:" + sha(Buffer.concat([Buffer.from(R_SALT, "hex"), Buffer.from("args:"), canon(asJ(request))])),
      resultDigest: rDigest(result),
      servedAt: R_SERVED,
      acquisition: { adapter: profile.adapter, shape: profile.shape, endpoint: profile.endpoint, observedAt: R_OBSERVED },
    };
    for (const hook of this.receiptHooks) hook(name, index, receipt);
    const message = Buffer.concat([Buffer.from("judgment-pack-gateway/receipt/3:"), canon(asJ(receipt))]);
    receipt.signature = Buffer.from(nodeSign(null, message, rKeys.privateKey)).toString("hex");
    return receipt;
  }

  documents(preparation?: Uint8Array): Inputs {
    const profiles = jcopy(this.profiles);
    const byId = new Map<string, J>(profiles.map((p: J) => [p.id, p]));
    const digests = new Map<string, string>(profiles.map((p: J) => [p.id, rDigest(p)]));
    const dialect = jcopy(this.dialect);
    const admits: J = {};
    if (Object.keys(this.admits).length > 0) admits.facts = { ...this.admits };
    if (Object.keys(this.admitsEvidence).length > 0) admits.evidence = { ...this.admitsEvidence };
    if (Object.keys(admits).length > 0) dialect.admits = admits;
    for (const s of dialect.sources) {
      if (digests.has(s.profileDigest)) s.profileDigest = digests.get(s.profileDigest);
      if (s.kind !== "research") continue;
      for (const a of Object.values(s.webProfiles ?? {}) as J[]) if (a !== null && typeof a === "object" && digests.has(a.profileDigest)) a.profileDigest = digests.get(a.profileDigest);
    }
    const acquisitions: J = {};
    let call = 0;
    for (const s of dialect.sources) {
      const spec = this.records[s.name];
      if (spec === undefined) continue;
      const indices = [...(this.callIndices[s.name] ?? [])];
      const next = () => (indices.length > 0 ? indices.shift()! : call);
      const responses = spec.responses.map((r: J, k: number) => {
        const profile = byId.get(r.profile) ?? profiles[0];
        const entry = {
          profile: { id: r.profile, digest: r.digest ?? digests.get(r.profile) ?? "sha256:" + "0".repeat(64) },
          request: r.request,
          result: r.result,
          receipt: this.receipt(s.name, k, profile, r.request, r.result, next()),
          salts: { args: R_SALT },
        };
        call++;
        return entry;
      });
      const record = { fields: spec.fields, responses };
      const member: J = { result: record };
      if (this.own.has(s.name)) {
        const q = s.question;
        const question = typeof q === "string" ? q : this.case[q.$param];
        const request = { question, constraints: s.constraints, model: s.model, evidence: s.evidence, fields: s.fields, capabilities: s.capabilities };
        member.receipt = this.receipt(s.name, "own", byId.get(s.profile), request, record, next());
        member.salts = { args: R_SALT };
        call++;
      }
      acquisitions[s.name] = { response: member };
    }
    let binding: J = null;
    if (this.unbound.size > 0) {
      const assignments: J = {};
      for (const s of dialect.sources) {
        if (!this.unbound.has(s.name)) continue;
        assignments[s.name] = { profile: s.profile, profileDigest: s.profileDigest, webProfiles: s.webProfiles };
        delete s.profile;
        delete s.profileDigest;
        delete s.webProfiles;
      }
      binding = { dialect: rDigest(dialect), sources: assignments };
    }
    const documents: J = { dialect, case: this.case, acquisitions, profiles, binding };
    for (const hook of this.afterHooks) hook(documents);
    const written: Record<string, string | undefined> = {};
    for (const [k, v] of Object.entries(documents)) written[k] = v === null ? undefined : JSON.stringify(v);
    for (const [k, from, to] of this.replacements) {
      assert.ok(written[k]!.includes(from), from);
      written[k] = written[k]!.replace(from, to);
    }
    const bytes = (k: string) => (written[k] === undefined ? undefined : utf8(written[k]!));
    return {
      dialect: bytes("dialect")!,
      case: bytes("case")!,
      acquisitions: bytes("acquisitions")!,
      profiles: bytes("profiles")!,
      preparation: preparation ?? utf8(`{"verifiedAt":"${R_AT}"}`),
      binding: bytes("binding"),
      requireBinding: false,
    };
  }

  /** The documents, with the preparation this reader recomputes from them. */
  prepared(): Inputs {
    const inputs = this.documents();
    const r = verify(inputs);
    assert.ok(r.recomputed !== undefined, `no preparation was recomputed: ${r.why}`);
    return { ...inputs, preparation: r.recomputed! };
  }
}

const codeOf = (r: ReturnType<typeof verify>) => (r.kind === "reading" ? "reading" : `${r.kind}:${(member(r.report, r.kind) as { v: string }).v}`);

function assign(source: J, ai?: string, web: Record<string, string> = {}): void {
  if (ai !== undefined) {
    source.profile = ai;
    source.profileDigest = ai;
  }
  for (const [c, id] of Object.entries(web)) source.webProfiles[c] = { profile: id, profileDigest: id };
}

/** An earlier research source whose rule leaves its claim `absent`, from which the primary takes a parameter: the
 * primary is skipped (§3, §9.2), and its record not acquired. */
function gate(s: Scenario): void {
  const rule = {
    ruleVersion: "1",
    parameters: {},
    clauses: [
      clause(statusGuard("/fields/employee-count", "found"), "found", "/gate/count", "/fields/employee-count/value", "resolved"),
      clause({ op: "always" }, "nothing to go on", undefined, undefined, "absent"),
    ],
  };
  s.dialect.sources.unshift(rSource("gate", { rule }, countOnly(), ["answer"]));
  s.source("primary").parameters = { gateCount: { from: "gate", pointer: "/gate/count", type: "integer" } };
  s.admits["/gate/count"] = ["generated"];
  s.records.gate = { fields: countAnswer("not-found"), responses: [] };
  delete s.records.primary;
}

/** The reconciliation rule with one guard of the primary's taken out. */
function guardedRule(status: string): J {
  const rule = reconciliationRule();
  const guard = status === "absent" ? absenceGuard(PRIMARY) : statusGuard(PRIMARY, status);
  const same = (a: J, b: J) => JSON.stringify(a) === JSON.stringify(b);
  const prune = (c: J): J => (c.op === "all" || c.op === "any" ? { ...c, of: c.of.filter((x: J) => !same(x, guard)).map(prune) } : c);
  for (const cl of rule.clauses) cl.when = prune(cl.when);
  return rule;
}

type Case = [string, string, () => Inputs];

function researchCases(): Case[] {
  const cases: Case[] = [];
  const add = (name: string, expected: string, alter?: (s: Scenario) => void, kind: "company" | "reconcile" = "company", fixed?: ((s: Scenario) => void) | true) => {
    cases.push([name, expected, () => {
      const s = new Scenario(kind);
      alter?.(s);
      if (fixed !== undefined) {
        const base = new Scenario(kind);
        if (fixed !== true) fixed(base);
        return s.documents(base.prepared().preparation);
      }
      return expected === "reading" ? s.prepared() : s.documents();
    }]);
  };
  const company = (s: Scenario) => s.source("company");
  const answers = (s: Scenario) => s.records.company.fields;
  const declared = (s: Scenario, name: string) => company(s).fields.find((d: J) => d.name === name);
  const both = (...alterations: ((s: Scenario) => void)[]) => (s: Scenario) => alterations.forEach((a) => a(s));
  const after = (change: (d: J) => void) => (s: Scenario) => s.afterHooks.push(change);
  const recordOf = (d: J, name = "company") => d.acquisitions[name].response.result;
  const malformed = "refusal:input-malformed";
  const over = "refusal:input-over-bound";
  const ruleRead = (s: Scenario) => {
    company(s).read = { rule: { ruleVersion: "1", parameters: {}, clauses: [
      { when: statusGuard("/fields/employee-count", "found"), claim: { facts: [{ pointer: COUNT_TARGET, from: "/fields/employee-count/value" }], evidence: { "company-headcount": "present" }, acquisitionStatus: "resolved" }, reason: "found" },
      { when: { op: "exists", field: "/fields/employee-count/values/0/value" }, claim: { facts: [], evidence: { "company-headcount": "unknown" }, acquisitionStatus: "unknown" }, reason: "observations conflict" },
      { when: { op: "always" }, claim: { facts: [], evidence: { "company-headcount": "absent" }, acquisitionStatus: "absent" }, reason: "not found" },
    ] } };
    s.admits = { [COUNT_TARGET]: ["generated"] };
    s.admitsEvidence = { "company-headcount": ["generated"] };
  };
  const parameterRule = (s: Scenario) => {
    ruleRead(s);
    const rule = company(s).read.rule;
    rule.parameters = { company: "string" };
    rule.clauses[0].when = { op: "all", of: [statusGuard("/fields/employee-count", "found"), { op: "equalsParam", field: "/fields/company-id/value", param: "company" }] };
    answers(s)["company-id"].value = COMPANY;
  };
  const answerAlone = (s: Scenario) => {
    company(s).capabilities = ["answer"];
    company(s).webProfiles = {};
    s.records.company.responses = [answerResponse()];
    for (const e of Object.values(answers(s)) as J[]) e.cites = [0];
  };

  // readings: every new form
  add("valid-types: answer, search and page, all six types found", "reading");
  add("valid-types: a source asking for answer alone", "reading", answerAlone);
  add("the record with a receipt of its own", "reading", (s) => s.own.add("company"));
  add("bound through a binding document", "reading", (s) => s.unbound.add("company"));
  add("bound through a binding document, the record with a receipt of its own", "reading", (s) => (s.unbound.add("company"), s.own.add("company")));
  add("presence: every optional entry omitted", "reading", (s) => ["revenue", "active", "roles", "employee-range"].forEach((n) => delete answers(s)[n]));
  add("presence: a required entry not-found", "reading", (s) => (answers(s)["employee-count"] = { status: "not-found", cites: [1] }));
  add("presence: integer -0, decimal 0, text empty, boolean false", "reading", (s) => {
    answers(s)["company-id"] = { status: "found", value: "", cites: [0] };
    answers(s).revenue = { status: "found", value: "0", cites: [0] };
    answers(s)["employee-count"].value = 424242;
    s.replacements.push(["acquisitions", '"value":424242', '"value":-0']);
  });
  add("stale with no citation, conflicting with separate citations", "reading", (s) => {
    answers(s).active = { status: "stale", cites: [] };
    answers(s).roles = { status: "conflicting", cites: [], values: [{ value: ["buyer", "buyer", ""], cites: [0] }, { value: ["buyer"], cites: [1, 2] }] };
  });
  add("an integer range, a list with duplicates and empty strings, decimals spelled apart", "reading", (s) => {
    answers(s)["employee-range"] = { status: "conflicting", cites: [], values: [{ value: { min: -3, max: 12 }, cites: [0] }, { value: { min: -3, max: 12 }, cites: [1] }, { value: { min: 0, max: 0 }, cites: [2] }] };
    answers(s).roles = { status: "found", value: ["x", "x", ""], cites: [0] };
    answers(s).revenue = { status: "conflicting", cites: [], values: [{ value: "1.0", cites: [0] }, { value: "1.00", cites: [2] }] };
  });
  add("a rule guards the found value, and a condition reads an observation", "reading", ruleRead);
  add("a rule over a conflict reads an observation and resolves nothing", "reading", both(ruleRead, (s) => (answers(s)["employee-count"] = { status: "conflicting", cites: [], values: [{ value: 1, cites: [0] }, { value: 2, cites: [2] }] })));
  add("a rule names a parameter no receipt commits", "reading", parameterRule);
  add("a rule names a parameter the record's own receipt commits", "reading", both(parameterRule, (s) => s.own.add("company")));
  add("no retained response and no receipt", "reading", (s) => {
    s.records.company.responses = [];
    s.records.company.fields = { "company-id": { status: "not-found", cites: [] }, "employee-count": { status: "stale", cites: [] } };
  });
  add("reconciliation: the primary's found value", "reading", undefined, "reconcile");
  add("reconciliation: the secondary's, the primary not-found", "reading", (s) => (s.records.primary.fields = countAnswer("not-found")), "reconcile");
  add("reconciliation: a conflict derives unknown (failed-fallback)", "reading", (s) => {
    s.records.primary.fields = countAnswer("not-found");
    s.records.secondary.fields = countAnswer("stale");
    s.records.combined = { fields: countAnswer("conflicting"), responses: [answerResponse()] };
  }, "reconcile");
  add("reconciliation: every candidate unavailable", "reading", (s) => {
    s.records.primary.fields = countAnswer("not-found");
    s.records.secondary.fields = countAnswer("stale");
  }, "reconcile");
  add("reconciliation: an absent entry, and this source's own found value", "reading", (s) => {
    s.records.primary.fields = countAnswer("absent");
    s.records.secondary.fields = countAnswer("not-found");
    s.records.combined = { fields: countAnswer("found", 11), responses: [answerResponse()] };
  }, "reconcile");
  add("reconciliation: a skipped earlier source is absent from the combined value", "reading", gate, "reconcile");
  add("cites follow the sources, not callIndex, in a preparation with research", "reading", (s) => (s.callIndices = { primary: [5], secondary: [0, 1] }), "reconcile");
  add("a field no read uses changes, with no receipt for the record", "reading", both(ruleRead, (s) => (answers(s).roles = { status: "found", value: ["other"], cites: [0] })), "company", ruleRead);

  // findings
  add("a read field changes, with no receipt for the record", "finding:preparation-differs", (s) => (answers(s)["employee-count"].value = 1), "company", true);
  add("responses reordered, their indices updated to cite the same", "finding:preparation-differs", both(ruleRead, (s) => {
    s.records.company.responses = [pageResponse(), answerResponse(), searchResponse()];
    s.callIndices.company = [2, 0, 1];
    const moved: Record<number, number> = { 0: 1, 1: 2, 2: 0 };
    for (const e of Object.values(answers(s)) as J[]) e.cites = e.cites.map((i: number) => moved[i]);
  }), "company", ruleRead);
  add("a second installation binds another AI profile", "finding:preparation-differs", (s) => {
    s.unbound.add("company");
    assign(company(s), "ai-2");
    s.records.company.responses[0].profile = "ai-2";
  }, "company", (s) => s.unbound.add("company"));
  add("an AI profile of another model", "finding:profile-mismatch", (s) => assign(company(s), "ai-b"));
  add("an AI profile lacking answer", "finding:profile-mismatch", (s) => assign(company(s), "web-search"));
  add("an AI profile with no research declaration", "finding:profile-mismatch", (s) => assign(company(s), "plain"));
  add("a web profile lacking the capability it serves", "finding:profile-mismatch", (s) => assign(company(s), undefined, { page: "web-search" }));
  add("a web profile not of class generated", "finding:profile-mismatch", (s) => assign(company(s), undefined, { search: "web-record" }));
  add("a web profile that declares another model", "finding:profile-mismatch", (s) => assign(company(s), undefined, { search: "web-b" }));
  add("an old profile digest", "finding:profile-mismatch", (s) => (company(s).profileDigest = "sha256:" + "0".repeat(64)));
  add("an untrusted profile", "finding:profile-mismatch", (s) => (company(s).profile = "elsewhere"));
  add("a binding naming an old profile digest", "finding:profile-mismatch", both((s) => s.unbound.add("company"), after((d) => (d.binding.sources.company.webProfiles.page.profileDigest = "sha256:" + "0".repeat(64)))));
  add("a binding naming a profile of another model", "finding:profile-mismatch", (s) => (s.unbound.add("company"), assign(company(s), "ai-b")));
  add("a retained response through a trusted, unassigned profile", "finding:profile-mismatch", (s) => (s.records.company.responses[1].profile = "web-search"));
  add("a retained response naming an untrusted profile", "finding:profile-mismatch", (s) => (s.records.company.responses[1].profile = "elsewhere"));
  add("a retained response naming another digest", "finding:profile-mismatch", (s) => (s.records.company.responses[2].digest = "sha256:" + "0".repeat(64)));
  add("the research record not acquired", "finding:acquisition-missing", after((d) => delete d.acquisitions.company));
  add("a cited response whose bytes are not retained", "finding:acquisition-missing", after((d) => delete recordOf(d).responses[2].result));
  add("a retained result changed", "finding:acquisition-invalid", after((d) => (recordOf(d).responses[1].result.hits = [])));
  add("a retained request changed", "finding:acquisition-invalid", after((d) => (recordOf(d).responses[0].request.prompt = "Which?")));
  add("the fields changed under the record's own receipt", "finding:acquisition-invalid", both((s) => s.own.add("company"), after((d) => (recordOf(d).fields["employee-count"].value = 1))));
  add("the record's own receipt over another request", "finding:acquisition-invalid", (s) => {
    s.own.add("company");
    s.receiptHooks.push((_, i, r) => { if (i === "own") r.argumentsCommitment = "sha256:" + "0".repeat(64); });
  });
  add("a retained receipt of another source", "finding:acquisition-invalid", (s) => s.receiptHooks.push((_, i, r) => { if (i === 1) r.source = "elsewhere"; }));
  add("an expired retained receipt", "finding:acquisition-stale", (s) => s.receiptHooks.push((_, i, r) => { if (i === 1) r.acquisition.observedAt = R_EXPIRED; }));
  add("the record's own receipt expired", "finding:acquisition-stale", (s) => {
    s.own.add("company");
    s.receiptHooks.push((_, i, r) => { if (i === "own") r.servedAt = R_EXPIRED; });
  });
  add("two retained responses at one callIndex", "finding:acquisition-sessions", (s) => (s.callIndices.company = [0, 0, 1]));
  add("the record's own receipt at a retained response's callIndex", "finding:acquisition-sessions", (s) => (s.own.add("company"), (s.callIndices.company = [0, 1, 2, 1])));
  // Round 9 (issue #182 item 4): each receipt's members are held to their forms before the time and session rules, a
  // retained response's and the record's own alike; `sessionId` is any string.
  const receiptOf = (index: number | "own", members: J) => (s: Scenario) => {
    s.receiptHooks.push((_, i, r) => {
      if (i !== index) return;
      for (const [k, v] of Object.entries(members)) {
        if (k === "observedAt") r.acquisition[k] = v;
        else r[k] = v;
      }
    });
  };
  const own = (s: Scenario) => void s.own.add("company");
  const invalid = "finding:acquisition-invalid";
  add("a retained receipt's servedAt that is not a string", invalid, receiptOf(1, { servedAt: 1760529540 }));
  add("a retained receipt's observedAt with no instant", invalid, receiptOf(2, { observedAt: "2026-10-15T11:58:30.5Z" }));
  add("the record's own receipt's servedAt that names no time", invalid, both(own, receiptOf("own", { servedAt: "2026-02-30T11:59:00Z" })));
  add("the record's own receipt's observedAt that is null", invalid, both(own, receiptOf("own", { observedAt: null })));
  add("a retained receipt's callIndex that is a string", invalid, receiptOf(1, { callIndex: "1" }));
  add("a retained receipt's callIndex below zero", invalid, receiptOf(0, { callIndex: -1 }));
  add("a retained receipt's sessionId that is not a string", invalid, receiptOf(2, { sessionId: 2 }));
  add("the record's own receipt's sessionId that is null", invalid, both(own, receiptOf("own", { sessionId: null })));
  add("an expired retained receipt whose callIndex is a string: the form first", invalid, receiptOf(1, { observedAt: R_EXPIRED, callIndex: "1" }));
  add("an expired response before a malformed one: one response's checks complete first", "finding:acquisition-stale", both(
    receiptOf(0, { servedAt: R_EXPIRED }), receiptOf(1, { callIndex: "1" }),
  ));
  // review round of pull request 186: `acquisition.observedAt` moved to the receipt's top level is absent
  const misplacedAt = (index: number | "own") => (s: Scenario) => {
    s.receiptHooks.push((_, i, r) => {
      if (i !== index) return;
      r.observedAt = r.acquisition.observedAt;
      delete r.acquisition.observedAt;
    });
  };
  add("a retained receipt's observedAt moved to the receipt's top level", invalid, misplacedAt(1));
  add("the record's own receipt's observedAt moved to the receipt's top level", invalid, both(own, misplacedAt("own")));
  add("a sessionId of no token form, shared by every receipt", "reading", both(
    own, (s) => void s.receiptHooks.push((_, __, r) => (r.sessionId = "a session, not a token: \u00fcn\u00efcode")),
  ));
  add("a skipped research source with a record", "finding:acquisition-unexpected", both(gate, (s) => (s.records.primary = { fields: countAnswer("not-found"), responses: [] })), "reconcile");
  add("a matched clause's value pointer that does not resolve", "finding:read-failed", (s) => (s.source("combined").read.rule.clauses[0].claim.facts[0].from = PRIMARY + "/value/min"), "reconcile");
  add("a plain rule's from that does not resolve", "finding:read-failed", (s) => {
    company(s).read = { rule: { ruleVersion: "1", parameters: {}, clauses: [{ when: { op: "always" }, claim: { facts: [{ pointer: "/company/revenue", from: "/fields/revenue/value" }], evidence: {}, acquisitionStatus: "resolved" }, reason: "always" }] } };
    s.admits = { "/company/revenue": ["generated"] };
    answers(s).revenue = { status: "not-found", cites: [] };
  });
  add("a research target that does not admit generated", "finding:admission-refused", (s) => (s.admits = { "/company/fields": ["record"] }));
  add("the combined value nested beyond 32 levels", over, (s) => (s.records.primary.responses[0].result = JSON.parse("[".repeat(29) + "]".repeat(29))), "reconcile");

  // refusals: the recipe's form
  add("a source without fields (pull request 164's form)", malformed, (s) => delete company(s).fields);
  add("a source without capabilities", malformed, (s) => delete company(s).capabilities);
  // each declaration refusal leaves the record answering only declared fields, so that no other check refuses it
  const unanswered = (s: Scenario) => delete answers(s).revenue;
  add("an empty declaration list", malformed, (s) => ((company(s).fields = []), (s.records.company.fields = {})));
  add("a declaration of another type", malformed, both(unanswered, (s) => (declared(s, "revenue").type = "number")));
  add("a declaration whose required is not a boolean", malformed, (s) => (declared(s, "revenue").required = "no"));
  add("a declaration named case", malformed, both(unanswered, (s) => (declared(s, "revenue").name = "case")));
  add("a declaration with an empty description", malformed, (s) => (declared(s, "revenue").description = ""));
  add("a declaration with a member more", malformed, (s) => (declared(s, "revenue").unit = "EUR"));
  add("a field declared twice", malformed, both(unanswered, (s) => (declared(s, "revenue").name = "active")));
  add("evidence that is not an array", malformed, (s) => (company(s).evidence = "the page that states the headcount"));
  add("an empty evidence instruction", malformed, (s) => (company(s).evidence = [""]));
  add("capabilities without answer", malformed, (s) => (company(s).capabilities = ["search", "page"]));
  add("capabilities out of order", malformed, (s) => (company(s).capabilities = ["answer", "page", "search"]));
  add("a capability named twice", malformed, (s) => ((company(s).capabilities = ["answer", "search", "search"]), delete company(s).webProfiles.page));
  add("answer named twice", malformed, (s) => ((company(s).capabilities = ["answer", "answer"]), (company(s).webProfiles = {})));
  add("an unknown capability", malformed, (s) => (company(s).capabilities = ["answer", "browse"]));
  add("no capability", malformed, (s) => (company(s).capabilities = []));
  add("the bound form without webProfiles", malformed, (s) => delete company(s).webProfiles);
  add("webProfiles missing a requested capability", malformed, (s) => delete company(s).webProfiles.page);
  add("webProfiles assigning an unrequested capability", malformed, (s) => (company(s).capabilities = ["answer", "search"]));
  add("a web assignment with a member more", malformed, (s) => (company(s).webProfiles.page.model = "model-a"));
  add("a web assignment whose digest is not a digest", malformed, (s) => (company(s).webProfiles.page.profileDigest = "sha256:XYZ"));
  add("an operation's catalog member", malformed, (s) => (company(s).platform = "research"));
  add("a question naming no parameter in scope", malformed, (s) => (company(s).question = { $param: "elsewhere" }));
  add("a question that is a number", malformed, (s) => (company(s).question = 7));
  add("a question that is an object, not a template form", malformed, (s) => (company(s).question = { text: "Which?" }));
  add("constraints that are not an object", malformed, (s) => (company(s).constraints = ["EU"]));
  add("an empty model", malformed, (s) => (company(s).model = ""));
  add("research in a version-2 dialect", malformed, (s) => (s.dialect.version = 2));
  add("an unbound source with no binding document", malformed, both((s) => s.unbound.add("company"), after((d) => (d.binding = null))));
  add("a binding for another published digest", malformed, both((s) => s.unbound.add("company"), after((d) => (d.binding.dialect = "sha256:" + "0".repeat(64)))));
  add("a binding without webProfiles", malformed, both((s) => s.unbound.add("company"), after((d) => delete d.binding.sources.company.webProfiles)));
  add("a binding assigning an unrequested capability", malformed, (s) => (s.unbound.add("company"), (company(s).capabilities = ["answer", "search"])));
  add("a binding's web assignment of another form", malformed, both((s) => s.unbound.add("company"), after((d) => delete d.binding.sources.company.webProfiles.search.profileDigest)));
  add("a profile's model without answer", malformed, (s) => (s.profiles[1].research.model = "model-a"));
  add("a profile serving answer with no model", malformed, (s) => delete s.profiles[0].research.model);
  add("a profile's empty capabilities", malformed, (s) => (s.profiles[1].research.capabilities = []));
  add("a profile's research with a member more", malformed, (s) => (s.profiles[1].research.weights = "x"));

  // refusals: the record's answers (§4.3, §11's `presence` and `bounds-and-cites`)
  add("a record without fields (pull request 164's form)", malformed, after((d) => delete recordOf(d).fields));
  add("a required entry omitted", malformed, (s) => delete answers(s)["employee-count"]);
  add("an answer for an undeclared field", malformed, (s) => (answers(s).headcount = { status: "not-found", cites: [] }));
  add("a null entry", malformed, (s) => (answers(s).revenue = null));
  add("a null value", malformed, (s) => (answers(s).revenue.value = null));
  add("an integer of another type", malformed, (s) => (answers(s)["employee-count"].value = "12"));
  add("an integer with a fraction", malformed, (s) => (answers(s)["employee-count"].value = 12.5));
  add("a numeric decimal", malformed, (s) => (answers(s).revenue.value = 12));
  for (const spelling of ["012", "+1", "1e2", "", "1.", ".5", "1,5"]) add(`a decimal spelled '${spelling}'`, malformed, (s) => (answers(s).revenue.value = spelling));
  add("a boolean written as a string", malformed, (s) => (answers(s).active.value = "false"));
  add("a text that is not a string", malformed, (s) => (answers(s)["company-id"].value = 1));
  add("a null list item", malformed, (s) => (answers(s).roles.value = ["buyer", null]));
  add("a null range endpoint", malformed, (s) => (answers(s)["employee-range"].value = { min: null, max: "2" }));
  add("mixed range endpoints", malformed, (s) => (answers(s)["employee-range"].value = { min: 1, max: "2" }));
  add("a reversed decimal range", malformed, (s) => (answers(s)["employee-range"].value = { min: "2.5", max: "2.25" }));
  add("a reversed integer range", malformed, (s) => (answers(s)["employee-range"].value = { min: 3, max: -3 }));
  add("a range with a unit", malformed, (s) => (answers(s)["employee-range"].value = { min: 1, max: 2, unit: "people" }));
  add("a found entry without cites", malformed, (s) => delete answers(s).revenue.cites);
  add("a found entry citing nothing", malformed, (s) => (answers(s).revenue.cites = []));
  add("a value on a not-found entry", malformed, (s) => (answers(s).revenue.status = "not-found"));
  add("values on a found entry", malformed, (s) => (answers(s).revenue.values = [{ value: "1", cites: [0] }, { value: "2", cites: [0] }]));
  add("a conflicting entry with no observation", malformed, (s) => (answers(s).revenue = { status: "conflicting", cites: [], values: [] }));
  add("a conflicting entry of one value", malformed, (s) => (answers(s).revenue = { status: "conflicting", cites: [], values: [{ value: "1", cites: [0] }] }));
  add("a conflicting entry whose values do not differ", malformed, (s) => (answers(s)["employee-count"] = { status: "conflicting", cites: [], values: [{ value: 7, cites: [0] }, { value: 7, cites: [1] }] }));
  add("a conflicting entry with cites of its own", malformed, (s) => (answers(s).revenue = { status: "conflicting", cites: [0], values: [{ value: "1", cites: [0] }, { value: "2", cites: [1] }] }));
  add("an observation citing nothing", malformed, (s) => (answers(s).revenue = { status: "conflicting", cites: [], values: [{ value: "1", cites: [] }, { value: "2", cites: [1] }] }));
  add("an observation with a member more", malformed, (s) => (answers(s).revenue = { status: "conflicting", cites: [], values: [{ value: "1", cites: [0], url: "https://company.example.test/about" }, { value: "2", cites: [1] }] }));
  add("an unknown status", malformed, (s) => (answers(s).revenue = { status: "guessed", cites: [] }));
  add("an index -0", malformed, (s) => ((answers(s).revenue.cites = [424242]), s.replacements.push(["acquisitions", "[424242]", "[-0]"])));
  add("an index at the responses' length", malformed, (s) => (answers(s).revenue.cites = [3]));
  add("a negative index", malformed, (s) => (answers(s).revenue.cites = [-1]));
  add("an index written with a fraction", malformed, (s) => ((answers(s).revenue.cites = [424242]), s.replacements.push(["acquisitions", "[424242]", "[1.0]"])));
  add("an index cited twice", malformed, (s) => (answers(s).revenue.cites = [2, 2]));
  add("a URL in place of an index", malformed, (s) => (answers(s).revenue.cites = ["https://company.example.test/about"]));

  // refusals: a plain research read's pointers (§4.3, "Reading fields")
  const readRule = (s: Scenario) => company(s).read.rule;
  add("a plain rule's from under values", malformed, both(ruleRead, (s) => (readRule(s).clauses[0].claim.facts[0].from = "/fields/employee-count/values/0/value")));
  add("a copy from under values", malformed, (s) => (company(s).read.copy.facts[0].source = "/fields/roles/values/0/value"));
  add("a copy of a retained response", malformed, (s) => (company(s).read.copy.facts[0].source = "/responses/0/result"));
  add("a copy of the whole record", malformed, (s) => (company(s).read.copy.facts[0].source = ""));
  add("a condition on an undeclared field", malformed, both(ruleRead, (s) => (readRule(s).clauses[1].when = { op: "exists", field: "/fields/headcount/status" })));
  add("a pointer below a status", malformed, both(ruleRead, (s) => (readRule(s).clauses[1].when = { op: "exists", field: "/fields/employee-count/status/0" })));
  add("an observation pointer of another form", malformed, both(ruleRead, (s) => (readRule(s).clauses[1].when = { op: "exists", field: "/fields/employee-count/values/00/value" })));
  add("an unwrap outside the closed list", malformed, (s) => (company(s).read.unwrap = ["/responses/0/result/text"]));

  // refusals: the reconciliation read (§6.4)
  const combinedRead = (s: Scenario) => s.source("combined").read;
  const clauses = (s: Scenario) => combinedRead(s).rule.clauses;
  const webSource = (): J => ({ name: "page", kind: "web", profile: "web", profileDigest: "web", maxAge: 600, url: "https://company.example.test/about", read: { copy: { facts: [], evidence: [] } } });
  const currentOnly = (): J => ({ ruleVersion: "1", parameters: {}, clauses: [
    clause(statusGuard(CURRENT, "found"), "this source found it", COUNT_TARGET, CURRENT + "/value", "resolved"),
    clause({ op: "any", of: [absenceGuard(CURRENT), ...["not-found", "stale", "conflicting"].map((x) => statusGuard(CURRENT, x))] }, "not found"),
    clause({ op: "always" }, "otherwise"),
  ] });
  add("no earlier source named", malformed, (s) => Object.assign(combinedRead(s), { sources: [], rule: currentOnly() }), "reconcile");
  add("a reconciliation of the current source alone", "reading", (s) => Object.assign(combinedRead(s), { sources: ["primary"], rule: currentOnly() }), "reconcile");
  add("an earlier source named twice", malformed, (s) => (combinedRead(s).sources = ["primary", "secondary", "primary"]), "reconcile");
  add("the current source named", malformed, (s) => (combinedRead(s).sources = ["primary", "secondary", "combined"]), "reconcile");
  add("a later source named", malformed, (s) => s.dialect.sources.splice(1, 0, s.dialect.sources.pop()), "reconcile");
  add("a source that does not exist named", malformed, (s) => (combinedRead(s).sources = ["primary", "secondary", "elsewhere"]), "reconcile");
  add("a non-research source named", malformed, (s) => (s.dialect.sources.unshift(webSource()), combinedRead(s).sources.push("page")), "reconcile");
  add("a non-research source beside, not named", "refusal:kind-unread", (s) => s.dialect.sources.unshift(webSource()), "reconcile");
  add("a reconciliation on another kind", malformed, (s) => s.dialect.sources.push({ ...webSource(), read: jcopy(combinedRead(s)) }), "reconcile");
  add("a reconciliation with an unwrap", malformed, (s) => (combinedRead(s).unwrap = ["/current"]), "reconcile");
  add("a reconciliation with a copy", malformed, (s) => (combinedRead(s).copy = { facts: [], evidence: [] }), "reconcile");
  add("a reconciliation's from under values", malformed, (s) => (clauses(s)[0].claim.facts[0].from = PRIMARY + "/values/0/value"), "reconcile");
  add("a reconciliation's from outside the admissible set", malformed, (s) => (clauses(s)[0].claim.facts[0].from = PRIMARY + "/status"), "reconcile");
  add("a reconciliation's from of a field its source does not declare", malformed, (s) => (clauses(s)[0].claim.facts[0].from = "/sources/primary/fields/revenue/value"), "reconcile");
  add("a reconciliation's from of a source it does not name", malformed, (s) => (combinedRead(s).sources = ["primary"]), "reconcile");
  add("a selecting clause without its found guard", malformed, (s) => (clauses(s)[0].when = { op: "exists", field: PRIMARY + "/value" }), "reconcile");
  add("a found guard nested below an all", malformed, (s) => (clauses(s)[1].when = { op: "all", of: [unavailable(PRIMARY), { op: "any", of: [statusGuard(SECONDARY, "found")] }] }), "reconcile");
  for (const missing of ["not-found", "stale", "conflicting", "absent"]) {
    add(`a selected field without its ${missing} guard`, malformed, (s) => (combinedRead(s).rule = guardedRule(missing)), "reconcile");
  }
  add("a reconciliation claim that writes evidence", malformed, (s) => (clauses(s)[2].claim.evidence = { "company-headcount": "unknown" }), "reconcile");
  add("a last clause that resolves", malformed, (s) => (clauses(s)[clauses(s).length - 1].claim.acquisitionStatus = "resolved"), "reconcile");
  add("a condition outside the reconciliation's pointers", malformed, (s) => (clauses(s)[4].when = { op: "any", of: [unavailable(CURRENT), { op: "exists", field: "/sources/primary/responses" }] }), "reconcile");
  add("a reconciliation's target that overlaps another's", malformed, (s) => clauses(s).filter((c: J) => c.claim.facts.length > 0).forEach((c: J) => (c.claim.facts[0].pointer = "/observed/primary/count")), "reconcile");
  add("16 earlier sources named", over, (s) => (combinedRead(s).sources = Array(16).fill("primary")), "reconcile");

  // the maxima of §12: one over each, and every maximum reached (§11's `bounds-and-cites`)
  const long = (n: number) => "x".repeat(n);
  add("65 fields declared", over, (s) => company(s).fields.push(...Array.from({ length: 59 }, (_, i) => ({ name: `extra-${i}`, type: "integer", required: false, description: "An extra." }))));
  add("65 answer entries, one undeclared", over, (s) => Array.from({ length: 59 }, (_, i) => (answers(s)[`extra-${i}`] = { status: "not-found", cites: [] })));
  add("a field name of 65 bytes", over, (s) => (declared(s, "revenue").name = long(65)));
  // an answer's name is measured before its entry, or whether it is declared (review M1)
  add("an answer named by 65 bytes, undeclared", over, (s) => (answers(s)[long(65)] = { status: "not-found", cites: [] }));
  add("an answer named by 64 bytes, undeclared", malformed, (s) => (answers(s)[long(64)] = { status: "not-found", cites: [] }));
  add("an answer named by 65 bytes, its entry malformed", over, (s) => (answers(s)[long(65)] = null));
  // a name declared twice: phase 3 measures by the first declaration whose type is one of the six (review M2)
  const twice = (first: string) => (s: Scenario) => company(s).fields.push(
    { name: "notes", type: first, required: false, description: "Notes." },
    { name: "notes", type: "text", required: false, description: "Notes again." },
  );
  const longNotes = (s: Scenario) => (answers(s).notes = { status: "found", value: long(8193), cites: [0] });
  add("a name declared twice, first of an unknown type: measured as the second, text", over, both(twice("number"), longNotes));
  add("a name declared twice, first an integer: measured as the first, and refused as declared twice", malformed, both(twice("integer"), longNotes));
  add("a description of 2049 bytes", over, (s) => (declared(s, "revenue").description = long(2049)));
  add("a model of 257 bytes", over, (s) => (company(s).model = long(257)));
  add("an evidence instruction of 4097 bytes", over, (s) => (company(s).evidence = [long(4097)]));
  add("a text of 8193 bytes", over, (s) => (answers(s)["company-id"].value = "é".repeat(4096) + "x"));
  add("a text-list of 65 items", over, (s) => (answers(s).roles.value = Array(65).fill("r")));
  add("a text-list item of 1025 bytes", over, (s) => (answers(s).roles.value = [long(1025)]));
  add("a decimal of 129 characters", over, (s) => (answers(s).revenue.value = "1".repeat(129)));
  add("a range endpoint of 129 characters", over, (s) => (answers(s)["employee-range"].value = { min: "1", max: "1".repeat(129) }));
  add("65 conflicting observations", over, (s) => (answers(s)["employee-count"] = { status: "conflicting", cites: [], values: Array.from({ length: 65 }, (_, i) => ({ value: i, cites: [0] })) }));
  add("65 indices in a citation", over, (s) => (answers(s).revenue.cites = Array.from({ length: 65 }, (_, i) => i)));
  add("65 indices in an observation's citation", over, (s) => (answers(s)["employee-count"] = { status: "conflicting", cites: [], values: [{ value: 1, cites: Array.from({ length: 65 }, (_, i) => i) }, { value: 2, cites: [0] }] }));
  add("four capabilities", over, (s) => (company(s).capabilities = ["answer", "search", "page", "page"]));
  add("a profile of four capabilities", over, (s) => (s.profiles[1].research.capabilities = ["search", "page", "page", "page"]));
  add("a profile's model of 257 bytes", over, (s) => (s.profiles[0].research.model = long(257)));
  add("three web assignments", over, (s) => (company(s).webProfiles.answer = { profile: "ai", profileDigest: "ai" }));
  add("three web assignments in a binding", over, both((s) => s.unbound.add("company"), after((d) => (d.binding.sources.company.webProfiles.answer = {}))));
  add("65 retained responses", over, (s) => s.records.company.responses.push(...Array.from({ length: 62 }, answerResponse)));
  add("every maximum reached", "reading", (s) => {
    const source = company(s);
    source.fields.push(...Array.from({ length: 57 }, (_, i) => ({ name: `extra-${String(i).padStart(2, "0")}`, type: "integer", required: false, description: "An extra." })));
    source.fields.push({ name: long(64), type: "integer", required: false, description: long(2048) });
    source.model = long(256);
    source.evidence = [long(4096)];
    s.profiles[0].research.model = long(256);
    s.records.company.responses = [...Array.from({ length: 62 }, answerResponse), searchResponse(), pageResponse()];
    const entries = answers(s);
    entries["company-id"].value = "é".repeat(4096);
    entries.roles.value = Array(64).fill("é".repeat(512));
    entries.revenue.value = "-" + "1".repeat(125) + ".5";
    entries["employee-range"].value = { min: "1".repeat(128), max: "2" + "0".repeat(127) };
    entries["employee-count"] = { status: "conflicting", cites: [], values: Array.from({ length: 64 }, (_, i) => ({ value: i, cites: Array.from({ length: 64 }, (_, k) => k) })) };
    for (let i = 0; i < 57; i++) entries[`extra-${String(i).padStart(2, "0")}`] = { status: "found", value: i, cites: [0] };
    entries[long(64)] = { status: "not-found", cites: Array.from({ length: 64 }, (_, k) => k) };
  });
  return cases;
}

test("research (§§4.3, 4.4, 5.1, 5.2, 6.4, 11, 12): every hand-written case has the answer the text gives", () => {
  for (const [name, expected, build] of researchCases()) {
    const r = verify(build());
    assert.equal(codeOf(r), expected, `${name}: ${r.why ?? ""}`);
  }
});

const researchReading = (inputs: Inputs) => {
  const r = verify(inputs);
  assert.equal(r.kind, "reading", r.why);
  return { report: r.report, preparation: parse(text(r.recomputed!)) as JObj };
};
const callIndices = (cites: JVal | undefined) => (cites as { a: JObj[] }).a.map((c) => (c.m.get("callIndex") as { lit: string }).lit);

test("research §§4.3, 8.2, 9.3: a reading of every type: the fields copied, generated targets, the request, the receipts", () => {
  const { report, preparation } = researchReading(new Scenario().prepared());
  assert.deepEqual(JSON.parse(text(preparationForm(resolve(report, "/facts/company/fields")!))), JSON.parse(JSON.stringify(companyAnswers())));
  assert.equal(text(preparationForm(member(report, "targetsByClass")!)), '{"asserted":1,"generated":1,"record":0}');
  const outcome = resolve(preparation, "/outcomes/1") as JObj;
  assert.equal((resolve(outcome, "/arguments/question") as { v: string }).v, COMPANY);
  assert.deepEqual(Array.from((outcome.m.get("arguments") as JObj).m.keys()).sort(), ["capabilities", "constraints", "evidence", "fields", "model", "question"]);
  const entry = resolve(preparation, "/lineage/1") as JObj;
  assert.equal((entry.m.get("class") as { v: string }).v, "generated");
  assert.equal(entry.m.has("receipt"), false);
  assert.deepEqual(callIndices(entry.m.get("receipts")), ["0", "1", "2"]);
  assert.equal(text(canon(entry.m.get("receipts")!)), text(canon(member(preparation, "cites")!)));
});

test("research §9.1, §9.3: the record's own receipt is its receipt and its last citation; cites follow the sources", () => {
  const own = new Scenario();
  own.own.add("company");
  const entry = resolve(researchReading(own.prepared()).preparation, "/lineage/1") as JObj;
  assert.equal(text(canon(entry.m.get("receipt")!)), text(canon((entry.m.get("receipts") as { a: JVal[] }).a[3])));
  const ordered = new Scenario("reconcile");
  ordered.callIndices = { primary: [5], secondary: [0, 1] };
  const { preparation } = researchReading(ordered.prepared());
  assert.deepEqual(callIndices(member(preparation, "cites")), ["5", "0", "1"]);
  assert.deepEqual((member(preparation, "lineage") as { a: JObj[] }).a.map((e) => (e.m.has("receipts") ? callIndices(e.m.get("receipts")) : null)), [null, ["5"], ["0", "1"], []]);
});

test("research §4.4: a binding document yields the dialect bound directly, which the preparation commits", () => {
  const direct = new Scenario();
  const bound = new Scenario();
  bound.unbound.add("company");
  const inputs = bound.prepared();
  const published = parse(text(inputs.dialect));
  assert.equal(resolve(published, "/sources/0/webProfiles"), undefined);
  const reading = researchReading(inputs);
  assert.equal((member(reading.report, "digest") as { v: string }).v, (member(researchReading(direct.prepared()).report, "digest") as { v: string }).v);
  assert.equal((member(reading.preparation, "mappingDigest") as { v: string }).v, "sha256:" + sha(canon(parse(text(direct.documents().dialect)))));
});

test("research §6.4: reconciliation derives the declared precedence", () => {
  const count = (alter: (s: Scenario) => void) => {
    const s = new Scenario("reconcile");
    alter(s);
    const { report, preparation } = researchReading(s.prepared());
    const value = resolve(report, "/facts/company/employee-count");
    const claim = resolve(preparation, "/outcomes/" + String((member(preparation, "outcomes") as { a: JVal[] }).a.length - 1) + "/claim");
    return [value === undefined ? null : (value as { lit: string }).lit, (resolve(claim!, "/acquisitionStatus") as { v: string }).v, (resolve(claim!, "/reason") as { v: string }).v];
  };
  assert.deepEqual(count(() => {}), ["7", "resolved", "the primary found it"]);
  assert.deepEqual(count((s) => (s.records.primary.fields = countAnswer("not-found"))), ["9", "resolved", "the secondary found it"]);
  assert.deepEqual(count(gate), ["9", "resolved", "the secondary found it"]);
  assert.deepEqual(count((s) => {
    s.records.primary.fields = countAnswer("not-found");
    s.records.secondary.fields = countAnswer("stale");
    s.records.combined = { fields: countAnswer("conflicting"), responses: [answerResponse()] };
  }), [null, "unknown", "a conflict is not chosen"]);
});

test("research §11: a rule names a parameter that only the record's own receipt commits; -0 keeps its literal", () => {
  const cases = new Map(researchCases().map(([name, , build]) => [name, build]));
  const uncommitted = researchReading(cases.get("a rule names a parameter no receipt commits")!());
  assert.equal(text(preparationForm(member(uncommitted.report, "unsignedParameters")!)), '[{"parameters":[{"kind":"case","name":"company"}],"source":"company","targets":2}]');
  assert.equal(member(researchReading(cases.get("a rule names a parameter the record's own receipt commits")!()).report, "unsignedParameters"), undefined);
  const zero = verify(cases.get("presence: integer -0, decimal 0, text empty, boolean false")!());
  assert.ok(text(preparationForm(zero.report)).includes('"employee-count":{"cites":[0,2],"status":"found","value":-0}'));
  const none = researchReading(cases.get("no retained response and no receipt")!());
  assert.equal(text(canon(resolve(none.preparation, "/lineage/1/receipts")!)), "[]");
  assert.equal((resolve(none.report, "/unsignedFreshness/sources/0/source") as { v: string }).v, "company");
});

test("§§11, 12: a research record holds at most 64 retained responses, counted before any form", () => {
  const answer = (retained: number, malformedOne: boolean) => {
    const s = new Scenario();
    s.records.company.responses.push(...Array.from({ length: retained - 3 }, answerResponse));
    if (malformedOne) s.afterHooks.push((d) => d.acquisitions.company.response.result.responses.push({}));
    return codeOf(verify(s.documents()));
  };
  assert.equal(answer(64, false), "finding:preparation-differs");
  assert.equal(answer(65, false), "refusal:input-over-bound");
  assert.equal(answer(64, true), "refusal:input-over-bound");
  assert.equal(answer(63, true), "refusal:input-malformed");
});

test("§§4.3, 5.2, 11: a research acquisition has the form of its kind", () => {
  const answer = (change?: (r: J) => void, own = false) => {
    const s = new Scenario();
    if (own) s.own.add("company");
    if (change !== undefined) s.afterHooks.push((d) => change(d.acquisitions.company.response));
    return codeOf(verify(s.documents()));
  };
  const retained = (r: J) => r.result.responses[0];
  const cases: [string, ((r: J) => void) | undefined, string][] = [
    ["research-no-own-receipt", undefined, "finding:preparation-differs"],
    ["research-result-not-retained", (r) => delete retained(r).result, "finding:acquisition-missing"],
    ["research-salts-alone", (r) => (r.salts = { args: "0".repeat(64) }), "refusal:input-malformed"],
    ["research-record-not-object", (r) => (r.result = ["x"]), "refusal:input-malformed"],
    ["research-record-missing-responses", (r) => delete r.result.responses, "refusal:input-malformed"],
    ["research-record-bad-responses", (r) => (r.result.responses = {}), "refusal:input-malformed"],
    ["research-record-extra-member", (r) => (r.result.more = 1), "refusal:input-malformed"],
    ["not an object", (r) => (r.result.responses[0] = "x"), "refusal:input-malformed"],
    ["a member more", (r) => (retained(r).more = 1), "refusal:input-malformed"],
    ["no profile", (r) => delete retained(r).profile, "refusal:input-malformed"],
    ["a profile of another form", (r) => (retained(r).profile = { id: "ai" }), "refusal:input-malformed"],
    ["a profile digest of another form", (r) => (retained(r).profile.digest = "sha256:XYZ"), "refusal:input-malformed"],
    ["a request that is not an object", (r) => (retained(r).request = "Which?"), "refusal:input-malformed"],
    ["a receipt that is not an object", (r) => (retained(r).receipt = []), "refusal:input-malformed"],
    ["salts of another form", (r) => (retained(r).salts = { args: "x" }), "refusal:input-malformed"],
  ];
  for (const [name, change, expected] of cases) assert.equal(answer(change), expected, name);
  assert.equal(answer(undefined, true), "finding:preparation-differs");
  assert.equal(answer((r) => delete r.salts, true), "refusal:input-malformed");
  // an acquisition of any other kind still has its receipt and salts
  const acquisitions = parse(text(v3bound.acquisitions)) as JObj;
  const response = member(acquisitions.m.get("fx"), "response") as JObj;
  response.m.delete("receipt");
  response.m.delete("salts");
  assert.equal(verdict({ ...v3bound, acquisitions: canon(acquisitions) }), "refusal:input-malformed");
});

// RFC 0021: a named artifact changes canonical identity, not preparation format.
test("named Dialects retain format and independent artifact versions", () => {
  for (const family of [2, 3]) {
    const document = { formatVersion: `${family}.0.0`, id: "urn:judgmentpack:dialect:example", version: "0.1.0", case: { facts: [], evidence: [] } };
    const parsed = readDialect(parse(JSON.stringify(document)));
    assert.equal(parsed.version, family);
    assert.equal(text(canon(parsed.raw)), `{"case":{"evidence":[],"facts":[]},"formatVersion":"${family}.0.0","id":"urn:judgmentpack:dialect:example","version":"0.1.0"}`);
    for (const version of [2, "2", "01.0.0", "1.0.0-a", "1.0.0+build", "1.0.0\n", "1.0.0\r", "1.0.0\u2028"]) assert.throws(() => readDialect(parse(JSON.stringify({ ...document, version }))));
    for (const change of [{ formatVersion: 2 }, { formatVersion: "2.1.0" }, { id: "" }, { id: "has space" }, { id: "x".repeat(1025) }, { provider: "" }, { facts: null }, { sources: [] }, { admits: { facts: {} } }]) assert.throws(() => readDialect(parse(JSON.stringify({ ...document, ...change }))));
  }
});

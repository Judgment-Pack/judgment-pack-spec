// The forms the companion document fixes in its own words (§1, §9.5, §11, §12), and this reader's
// readings of inputs no vector holds, each derived from the `valid` vector by one change. The second
// group is this reader's, not the vectors': see README.md, "Where the text was not enough".
import assert from "node:assert/strict";
import { createHash, createPublicKey, generateKeyPairSync, sign as nodeSign, verify as nodeVerify } from "node:crypto";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { scanBytes } from "../src/bounds.ts";
import { add, decodePoint, encodePoint, keyAcceptable, smallOrder, verify as edVerify } from "../src/ed25519.ts";
import { NotRead, canon, isIntegerLiteral, member, num, obj, parse, preparationForm, read, resolve, str, utf8 } from "../src/json.ts";
import type { JObj, JVal } from "../src/json.ts";
import { instant } from "../src/time.ts";
import { loadVector } from "../src/vector.ts";
import { verify } from "../src/verify.ts";
import type { Inputs } from "../src/verify.ts";

const VECTORS = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "conformance", "dialect", "vectors");
const text = (b: Uint8Array) => Buffer.from(b).toString("utf8");

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
    answer((i) => ({ ...i, dialect: edit(i.dialect, '"sources":[', '"sources":[{"name":"file","kind":"selected-file","provider":"local-file","read":{"copy":{}}},') })),
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

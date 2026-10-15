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
import { bindDialect, readBinding } from "../src/forms.ts";
import { NotRead, arr, canon, isIntegerLiteral, member, num, obj, parse, preparationForm, read, resolve, str, utf8 } from "../src/json.ts";
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

test("§4.3: a kind of version 3 is held to its form, and not read", () => {
  const fx = sourceOf(parse(text(v3bound.dialect)) as JObj);
  const common = `"profile":"fx","profileDigest":${JSON.stringify((fx.m.get("profileDigest") as { v: string }).v)},"maxAge":300,"read":{"copy":{"facts":[],"evidence":[]}}`;
  const param = '{"$param":"invoiceCurrency"}';
  const wellFormed: Record<string, Record<string, string>> = {
    http: { method: '"POST"', path: '"/requests"', query: `{"currency":${param}}`, body: '{"n":1}', headers: '["Accept"]' },
    sql: { statement: '"SELECT 1 WHERE c = :c"', bindings: `[{"name":"c","type":"STRING","value":${param}}]` },
    web: { url: param },
    research: { question: '{"$text":"Which?"}', constraints: "{}", model: '"a-model"', evidence: '["excerpt"]' },
  };
  const malformedMembers: Record<string, [string, string][]> = {
    http: [["method", '"PUT"'], ["path", '{"a":1}'], ["path", '{"$param":"runAt"}'], ["method", '"GET"'], ["query", '{"currency":7}'], ["headers", '"Accept"']],
    sql: [["statement", '{"$text":"SELECT 1"}'], ["bindings", '[{"name":"c","type":"STRING","value":"EUR"}]'], ["bindings", `[{"name":"c","value":${param}}]`]],
    web: [["url", "7"], ["url", '{"$param":"nope"}'], ["url", '{"$text":"https://example.org/"}']],
    research: [["question", "7"], ["constraints", "[]"], ["model", "null"], ["evidence", '"excerpt"']],
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

const RETAINED = `{"profile":{"id":"fx","digest":"sha256:${"0".repeat(64)}"},"request":{"question":"Which?"},"result":{"answer":"none"},"receipt":{},"salts":{"args":"${"0".repeat(64)}"}}`;

/** version-3-bound with a `research` source added, its acquisition the given member. */
function researched(acquisition: string): string {
  const fx = sourceOf(parse(text(v3bound.dialect)) as JObj);
  const study = `{"name":"study","kind":"research","profile":"fx","profileDigest":${JSON.stringify((fx.m.get("profileDigest") as { v: string }).v)},"maxAge":300,"question":"Which?","constraints":{},"model":"a-model","evidence":["excerpt"],"read":{"copy":{"facts":[],"evidence":[]}}}`;
  const acquisitions = text(v3bound.acquisitions);
  return verdict({
    ...v3bound,
    dialect: edit(v3bound.dialect, '"sources":[', `"sources":[${study},`),
    acquisitions: utf8(`${acquisitions.slice(0, -1)},"study":${acquisition}}`),
  });
}

test("§§11, 12: a research record holds at most 64 retained responses, counted before any form", () => {
  const record = (n: number, tail = "") => `{"response":{"result":{"responses":[${Array(n).fill(RETAINED).join(",")}${tail}]}}}`;
  assert.equal(researched(record(64)), "refusal:kind-unread");
  assert.equal(researched(record(65)), "refusal:input-over-bound");
  assert.equal(researched(record(64, ",{}")), "refusal:input-over-bound");
  assert.equal(researched(record(63, ",{}")), "refusal:input-malformed");
});

test("§§4.3, 5.2, 11: a research acquisition has the form of its kind", () => {
  const salts = `{"args":"${"0".repeat(64)}"}`;
  const unretained = RETAINED.replace(',"result":{"answer":"none"}', "");
  const cases: [string, string, string][] = [
    ["research-no-own-receipt", '{"response":{"result":{"responses":[]}}}', "refusal:kind-unread"],
    ["research-own-receipt", `{"response":{"result":{"responses":[${RETAINED}]},"receipt":{},"salts":${salts}}}`, "refusal:kind-unread"],
    ["research-result-not-retained", `{"response":{"result":{"responses":[${unretained}]}}}`, "refusal:kind-unread"],
    ["research-receipt-alone", '{"response":{"result":{"responses":[]},"receipt":{}}}', "refusal:input-malformed"],
    ["research-salts-alone", `{"response":{"result":{"responses":[]},"salts":${salts}}}`, "refusal:input-malformed"],
    ["research-record-not-object", '{"response":{"result":["x"]}}', "refusal:input-malformed"],
    ["research-record-missing-responses", '{"response":{"result":{}}}', "refusal:input-malformed"],
    ["research-record-bad-responses", '{"response":{"result":{"responses":{}}}}', "refusal:input-malformed"],
    ["research-record-extra-member", '{"response":{"result":{"responses":[],"more":1}}}', "refusal:input-malformed"],
  ];
  const malformedRetained: [string, string][] = [
    ["not an object", '"x"'],
    ["a member more", RETAINED.replace(/}$/, ',"more":1}')],
    ["no profile", RETAINED.replace(/^\{"profile":\{[^}]*\},/, "{")],
    ["a profile of another form", RETAINED.replace(/"profile":\{[^}]*\}/, '"profile":{"id":"fx"}')],
    ["a profile digest of another form", RETAINED.replace(/"digest":"[^"]*"/, '"digest":"sha256:XYZ"')],
    ["a request that is not an object", RETAINED.replace('"request":{"question":"Which?"}', '"request":"Which?"')],
    ["a receipt that is not an object", RETAINED.replace('"receipt":{}', '"receipt":[]')],
    ["salts of another form", RETAINED.replace(/"salts":\{[^}]*\}/, '"salts":{"args":"x"}')],
  ];
  for (const [name, entry] of malformedRetained) {
    cases.push([`research-record-malformed-retained (${name})`, `{"response":{"result":{"responses":[${entry}]}}}`, "refusal:input-malformed"]);
  }
  for (const [name, acquisition, expected] of cases) assert.equal(researched(acquisition), expected, name);
  // an acquisition of any other kind still has its receipt and salts
  const acquisitions = parse(text(v3bound.acquisitions)) as JObj;
  const response = member(acquisitions.m.get("fx"), "response") as JObj;
  response.m.delete("receipt");
  response.m.delete("salts");
  assert.equal(verdict({ ...v3bound, acquisitions: canon(acquisitions) }), "refusal:input-malformed");
});

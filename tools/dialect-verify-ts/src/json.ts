// JSON as spec/dialect.md §1 reads it: strictly, one value, no member name given twice, every
// string well-formed Unicode, and every number kept as its literal. Two writers: `canon` (§1, the
// gateway canonical form) and the preparation's canonical form (§9.5). They are never interchanged.

export type JObj = { t: "obj"; m: Map<string, JVal>; s: number; e: number };
export type JArr = { t: "arr"; a: JVal[]; s: number; e: number };
export type JStr = { t: "str"; v: string; s: number; e: number };
export type JNum = { t: "num"; lit: string; s: number; e: number };
export type JBool = { t: "bool"; v: boolean; s: number; e: number };
export type JNull = { t: "null"; s: number; e: number };
export type JVal = JObj | JArr | JStr | JNum | JBool | JNull;

/** A document that §1 does not read: not one JSON value, a name given twice, an ill-formed string. */
export class NotRead extends Error {}

const decoder = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true });
const encoder = new TextEncoder();

export function utf8(text: string): Uint8Array {
  return encoder.encode(text);
}

/** The decoded text of a document, or NotRead when its bytes are not UTF-8. A BOM is kept, and so refused. */
export function decode(bytes: Uint8Array): string {
  try {
    return decoder.decode(bytes);
  } catch {
    throw new NotRead("not UTF-8");
  }
}

const NUMBER = /-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/y;
const MAX_PARSE_DEPTH = 1024; // a guard for the harness's own reads; the bounds of §12 are lower

/** Reads a document strictly (§1). Spans are offsets into `text`, so a value's bytes are recoverable exactly. */
export function parse(text: string): JVal {
  let i = 0;
  const n = text.length;
  const ws = () => {
    while (i < n) {
      const c = text.charCodeAt(i);
      if (c === 0x20 || c === 0x09 || c === 0x0a || c === 0x0d) i++;
      else break;
    }
  };
  const fail = (why: string): never => {
    throw new NotRead(`${why} at offset ${i}`);
  };
  const value = (depth: number): JVal => {
    if (depth > MAX_PARSE_DEPTH) fail("nesting beyond the parser's guard");
    ws();
    if (i >= n) fail("unexpected end");
    const c = text[i];
    const s = i;
    if (c === "{") {
      i++;
      const m = new Map<string, JVal>();
      ws();
      if (text[i] === "}") {
        i++;
        return { t: "obj", m, s, e: i };
      }
      for (;;) {
        ws();
        if (text[i] !== '"') fail("expected a member name");
        const name = str();
        if (m.has(name)) fail("a member name given twice");
        ws();
        if (text[i] !== ":") fail("expected ':'");
        i++;
        m.set(name, value(depth + 1));
        ws();
        if (text[i] === ",") {
          i++;
          continue;
        }
        if (text[i] === "}") {
          i++;
          return { t: "obj", m, s, e: i };
        }
        fail("expected ',' or '}'");
      }
    }
    if (c === "[") {
      i++;
      const a: JVal[] = [];
      ws();
      if (text[i] === "]") {
        i++;
        return { t: "arr", a, s, e: i };
      }
      for (;;) {
        a.push(value(depth + 1));
        ws();
        if (text[i] === ",") {
          i++;
          continue;
        }
        if (text[i] === "]") {
          i++;
          return { t: "arr", a, s, e: i };
        }
        fail("expected ',' or ']'");
      }
    }
    if (c === '"') {
      const v = str();
      return { t: "str", v, s, e: i };
    }
    if (c === "-" || (c >= "0" && c <= "9")) {
      NUMBER.lastIndex = i;
      const m = NUMBER.exec(text);
      if (!m) fail("malformed number");
      const lit = m![0];
      i += lit.length;
      const next = text[i];
      if (next !== undefined && /[0-9.eE+-]/.test(next)) fail("malformed number");
      return { t: "num", lit, s, e: i };
    }
    if (text.startsWith("true", i)) {
      i += 4;
      return { t: "bool", v: true, s, e: i };
    }
    if (text.startsWith("false", i)) {
      i += 5;
      return { t: "bool", v: false, s, e: i };
    }
    if (text.startsWith("null", i)) {
      i += 4;
      return { t: "null", s, e: i };
    }
    return fail("unexpected character");
  };
  const str = (): string => {
    i++; // the opening quote
    let out = "";
    for (;;) {
      if (i >= n) fail("unterminated string");
      const c = text.charCodeAt(i);
      if (c === 0x22) {
        i++;
        return out;
      }
      if (c < 0x20) fail("a control character in a string");
      if (c !== 0x5c) {
        out += text[i];
        i++;
        continue;
      }
      i++;
      const e = text[i];
      i++;
      switch (e) {
        case '"': out += '"'; break;
        case "\\": out += "\\"; break;
        case "/": out += "/"; break;
        case "b": out += "\b"; break;
        case "f": out += "\f"; break;
        case "n": out += "\n"; break;
        case "r": out += "\r"; break;
        case "t": out += "\t"; break;
        case "u": {
          const u = hex4();
          if (u >= 0xd800 && u <= 0xdbff) {
            if (text[i] !== "\\" || text[i + 1] !== "u") fail("a lone surrogate");
            i += 2;
            const lo = hex4();
            if (lo < 0xdc00 || lo > 0xdfff) fail("a lone surrogate");
            out += String.fromCharCode(u, lo);
          } else if (u >= 0xdc00 && u <= 0xdfff) {
            fail("a lone surrogate");
          } else {
            out += String.fromCharCode(u);
          }
          break;
        }
        default:
          fail("an unknown escape");
      }
    }
  };
  const hex4 = (): number => {
    const h = text.slice(i, i + 4);
    if (!/^[0-9a-fA-F]{4}$/.test(h)) fail("a malformed \\u escape");
    i += 4;
    return parseInt(h, 16);
  };
  const v = value(0);
  ws();
  if (i !== n) fail("more than one value");
  return v;
}

/** Reads bytes as a document (§1): UTF-8, then strictly. */
export function read(bytes: Uint8Array): { text: string; value: JVal } {
  const text = decode(bytes);
  return { text, value: parse(text) };
}

// ---- integers (§1) ----

const MAX_SAFE = 9007199254740991n;

/** An integer is a literal of the form -?(0|[1-9][0-9]*) whose value is within ±(2⁵³−1); `-0` is one. */
export function isIntegerLiteral(lit: string): boolean {
  if (!/^-?(?:0|[1-9][0-9]*)$/.test(lit)) return false;
  if (lit.length > 17) return false;
  const v = BigInt(lit);
  return v <= MAX_SAFE && v >= -MAX_SAFE;
}

export function isInteger(v: JVal | undefined): v is JNum {
  return v !== undefined && v.t === "num" && isIntegerLiteral(v.lit);
}

/** The value of an integer literal, `-0` as 0. */
export function intValue(v: JNum): number {
  const n = Number(v.lit);
  return n === 0 ? 0 : n;
}

// ---- code point order ----

export function compareCodePoints(a: string, b: string): number {
  const x = Array.from(a);
  const y = Array.from(b);
  const len = Math.min(x.length, y.length);
  for (let k = 0; k < len; k++) {
    const p = x[k].codePointAt(0)!;
    const q = y[k].codePointAt(0)!;
    if (p !== q) return p < q ? -1 : 1;
  }
  return x.length === y.length ? 0 : x.length < y.length ? -1 : 1;
}

export function sortedDistinct(items: Iterable<string>): string[] {
  return Array.from(new Set(items)).sort(compareCodePoints);
}

// ---- writers ----

/** A value outside a writer's domain: here, a number that is not an integer. */
export class OutsideDomain extends Error {}

const hex2 = (c: number) => c.toString(16).padStart(2, "0");

function canonString(s: string): string {
  let out = '"';
  for (const ch of s) {
    const c = ch.codePointAt(0)!;
    if (ch === '"') out += '\\"';
    else if (ch === "\\") out += "\\\\";
    else if (c === 0x08) out += "\\b";
    else if (c === 0x0c) out += "\\f";
    else if (c === 0x0a) out += "\\n";
    else if (c === 0x0d) out += "\\r";
    else if (c === 0x09) out += "\\t";
    else if (c < 0x20) out += "\\u00" + hex2(c);
    else out += ch;
  }
  return out + '"';
}

function preparationString(s: string): string {
  let out = '"';
  for (const ch of s) {
    const c = ch.codePointAt(0)!;
    if (ch === '"') out += '\\"';
    else if (ch === "\\") out += "\\\\";
    else if (c === 0x08) out += "\\b";
    else if (c === 0x09) out += "\\t";
    else if (c === 0x0a) out += "\\n";
    else if (c === 0x0c) out += "\\f";
    else if (c === 0x0d) out += "\\r";
    else if (c < 0x20) out += "\\u00" + hex2(c);
    else if (ch === "&") out += "\\u0026";
    else if (ch === "<") out += "\\u003c";
    else if (ch === ">") out += "\\u003e";
    else if (c === 0x2028) out += "\\u2028";
    else if (c === 0x2029) out += "\\u2029";
    else out += ch;
  }
  return out + '"';
}

function write(v: JVal, form: "canon" | "preparation"): string {
  switch (v.t) {
    case "obj": {
      const names = Array.from(v.m.keys()).sort(compareCodePoints);
      const str = form === "canon" ? canonString : preparationString;
      return "{" + names.map((k) => str(k) + ":" + write(v.m.get(k)!, form)).join(",") + "}";
    }
    case "arr":
      return "[" + v.a.map((x) => write(x, form)).join(",") + "]";
    case "str":
      return form === "canon" ? canonString(v.v) : preparationString(v.v);
    case "num":
      if (!isIntegerLiteral(v.lit)) throw new OutsideDomain(`the number ${v.lit} is not an integer`);
      if (form === "canon" && v.lit === "-0") return "0";
      return v.lit;
    case "bool":
      return v.v ? "true" : "false";
    case "null":
      return "null";
  }
}

/** The `canon` bytes of a value (§1), or OutsideDomain. */
export function canon(v: JVal): Uint8Array {
  return utf8(write(v, "canon"));
}

/** The preparation's canonical bytes (§9.5), or OutsideDomain. */
export function preparationForm(v: JVal): Uint8Array {
  return utf8(write(v, "preparation"));
}

export function inCanonDomain(v: JVal): boolean {
  try {
    write(v, "canon");
    return true;
  } catch (e) {
    if (e instanceof OutsideDomain) return false;
    throw e;
  }
}

// ---- JSON-equal (§6.3) ----

/** The mathematical value of a number literal, normalised: sign, significant digits, exponent. */
function decimal(lit: string): { neg: boolean; digits: string; exp: number } {
  const m = /^(-?)([0-9]+)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$/.exec(lit)!;
  const frac = m[3] ?? "";
  let digits = (m[2] + frac).replace(/^0+/, "");
  let exp = (m[4] ? parseInt(m[4], 10) : 0) - frac.length;
  if (digits === "") return { neg: false, digits: "", exp: 0 };
  const trimmed = digits.replace(/0+$/, "");
  exp += digits.length - trimmed.length;
  digits = trimmed;
  return { neg: m[1] === "-", digits, exp };
}

export function jsonEqual(a: JVal, b: JVal): boolean {
  if (a.t !== b.t) return false;
  switch (a.t) {
    case "num": {
      const x = decimal(a.lit);
      const y = decimal((b as JNum).lit);
      return x.neg === y.neg && x.digits === y.digits && x.exp === y.exp;
    }
    case "str":
      return a.v === (b as JStr).v;
    case "bool":
      return a.v === (b as JBool).v;
    case "null":
      return true;
    case "arr": {
      const y = (b as JArr).a;
      return a.a.length === y.length && a.a.every((x, k) => jsonEqual(x, y[k]));
    }
    case "obj": {
      const y = (b as JObj).m;
      if (a.m.size !== y.size) return false;
      for (const [k, x] of a.m) {
        const w = y.get(k);
        if (w === undefined || !jsonEqual(x, w)) return false;
      }
      return true;
    }
  }
}

// ---- pointers (RFC 6901, §1) ----

export function isPointer(p: string): boolean {
  return p === "" || (p.startsWith("/") && !/~(?![01])/.test(p));
}

export function tokens(p: string): string[] {
  if (p === "") return [];
  return p
    .slice(1)
    .split("/")
    .map((t) => t.replace(/~1/g, "/").replace(/~0/g, "~"));
}

/** Resolves a pointer (§1); undefined is absent, which is not null. */
export function resolve(v: JVal, p: string): JVal | undefined {
  let cur: JVal = v;
  for (const tok of tokens(p)) {
    if (cur.t === "obj") {
      const next = cur.m.get(tok);
      if (next === undefined) return undefined;
      cur = next;
    } else if (cur.t === "arr") {
      if (!/^(?:0|[1-9][0-9]*)$/.test(tok)) return undefined;
      if (BigInt(tok) >= BigInt(cur.a.length)) return undefined;
      cur = cur.a[Number(tok)];
    } else {
      return undefined;
    }
  }
  return cur;
}

/** Writes a value at a fact target, creating each object on the way (§8.1). */
export function writeAt(doc: JObj, p: string, value: JVal): void {
  const toks = tokens(p);
  let cur: JObj = doc;
  for (let k = 0; k < toks.length - 1; k++) {
    const next = cur.m.get(toks[k]);
    if (next !== undefined && next.t === "obj") {
      cur = next;
    } else {
      const created = obj();
      cur.m.set(toks[k], created);
      cur = created;
    }
  }
  cur.m.set(toks[toks.length - 1], value);
}

// ---- builders ----

export const obj = (entries: [string, JVal][] = []): JObj => ({ t: "obj", m: new Map(entries), s: -1, e: -1 });
export const arr = (a: JVal[]): JArr => ({ t: "arr", a, s: -1, e: -1 });
export const str = (v: string): JStr => ({ t: "str", v, s: -1, e: -1 });
export const num = (lit: string): JNum => ({ t: "num", lit, s: -1, e: -1 });
export const bool = (v: boolean): JBool => ({ t: "bool", v, s: -1, e: -1 });

export function member(v: JVal | undefined, name: string): JVal | undefined {
  return v !== undefined && v.t === "obj" ? v.m.get(name) : undefined;
}

/** The depth of a value: an object or an array opens a level; a scalar is 0. */
export function depth(v: JVal): number {
  if (v.t === "obj") {
    let d = 0;
    for (const x of v.m.values()) d = Math.max(d, depth(x));
    return d + 1;
  }
  if (v.t === "arr") {
    let d = 0;
    for (const x of v.a) d = Math.max(d, depth(x));
    return d + 1;
  }
  return 0;
}

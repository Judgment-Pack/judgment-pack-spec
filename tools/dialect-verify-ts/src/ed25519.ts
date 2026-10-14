// Ed25519 as spec/dialect.md §1 states the equation: RFC 8032's check without the cofactor, with a
// canonical scalar, written here from RFC 8032 §5.1 so that the check is exactly that and no library's.
import { createHash } from "node:crypto";

const P = 2n ** 255n - 19n;
const L = 2n ** 252n + 27742317777372353535851937790883648493n;
const mod = (a: bigint, m: bigint = P) => ((a % m) + m) % m;

function pow(b: bigint, e: bigint): bigint {
  let r = 1n;
  b = mod(b);
  while (e > 0n) {
    if (e & 1n) r = mod(r * b);
    b = mod(b * b);
    e >>= 1n;
  }
  return r;
}
const inv = (a: bigint) => pow(a, P - 2n);
const D = mod(-121665n * inv(121666n));
const SQRT_M1 = pow(2n, (P - 1n) / 4n);

type Point = { x: bigint; y: bigint; z: bigint; t: bigint };
const IDENTITY: Point = { x: 0n, y: 1n, z: 1n, t: 0n };

function add(p: Point, q: Point): Point {
  const a = mod((p.y - p.x) * (q.y - q.x));
  const b = mod((p.y + p.x) * (q.y + q.x));
  const c = mod(p.t * 2n * D * q.t);
  const d = mod(p.z * 2n * q.z);
  const e = b - a;
  const f = d - c;
  const g = d + c;
  const h = b + a;
  return { x: mod(e * f), y: mod(g * h), t: mod(e * h), z: mod(f * g) };
}

function mul(s: bigint, p: Point): Point {
  let r = IDENTITY;
  let q = p;
  while (s > 0n) {
    if (s & 1n) r = add(r, q);
    q = add(q, q);
    s >>= 1n;
  }
  return r;
}

function same(p: Point, q: Point): boolean {
  return mod(p.x * q.z - q.x * p.z) === 0n && mod(p.y * q.z - q.y * p.z) === 0n;
}

function leInt(b: Uint8Array): bigint {
  let r = 0n;
  for (let k = b.length - 1; k >= 0; k--) r = (r << 8n) | BigInt(b[k]);
  return r;
}

/** RFC 8032 §5.1.3 decoding; null when the encoding is not canonical or names no point. */
export function decodePoint(b: Uint8Array): Point | null {
  if (b.length !== 32) return null;
  const bytes = Uint8Array.from(b);
  const sign = bytes[31] >> 7;
  bytes[31] &= 0x7f;
  const y = leInt(bytes);
  if (y >= P) return null;
  const u = mod(y * y - 1n);
  const v = mod(D * y * y + 1n);
  let x = mod(u * pow(v, 3n) * pow(u * pow(v, 7n), (P - 5n) / 8n));
  const vx2 = mod(v * x * x);
  if (vx2 === u) {
    // x is a root
  } else if (vx2 === mod(-u)) {
    x = mod(x * SQRT_M1);
  } else {
    return null;
  }
  if (x === 0n && sign === 1) return null;
  if (Number(x & 1n) !== sign) x = mod(-x);
  return { x, y, z: 1n, t: mod(x * y) };
}

const BASE = decodePoint(
  Uint8Array.from(Buffer.from("5866666666666666666666666666666666666666666666666666666666666666", "hex")),
)!;

/** True when the point's order divides 8. */
export function smallOrder(p: Point): boolean {
  return same(mul(8n, p), IDENTITY);
}

/**
 * The key rule as this reader takes it (README, "Where the text was not enough"): the 32 bytes decode as a
 * canonical encoding of a curve point, and that point is not of small order.
 */
export function keyAcceptable(key: Uint8Array): boolean {
  const a = decodePoint(key);
  return a !== null && !smallOrder(a);
}

/** RFC 8032 §5.1.7 without the cofactor: [S]B = R + [k]A, S below L, R and A canonical encodings. */
export function verify(key: Uint8Array, message: Uint8Array, signature: Uint8Array): boolean {
  if (signature.length !== 64) return false;
  const a = decodePoint(key);
  if (a === null) return false;
  const rBytes = signature.subarray(0, 32);
  const r = decodePoint(rBytes);
  if (r === null) return false;
  const s = leInt(signature.subarray(32));
  if (s >= L) return false;
  const k = mod(leInt(createHash("sha512").update(rBytes).update(key).update(message).digest()), L);
  return same(mul(s, BASE), add(r, mul(k, a)));
}

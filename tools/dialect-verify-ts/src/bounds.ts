// The bounds of §12 that are measured on bytes, taken before a document is read (§11, phase 1), and
// again on an unwrapped string's bytes when it is unwrapped (§6.1).

export const BOUNDS = {
  dialectBytes: 131072,
  inputBytes: 2097152, // the dialect, the case and the acquisitions together
  profilesBytes: 65536,
  bindingBytes: 65536, // a binding document (§4.4)
  preparationBytes: 8388608,
  recordBytes: 8388608,
  sources: 16,
  retainedResponses: 64, // retained responses of one `research` source
  scopeParameters: 64,
  clauses: 64,
  listed: 64, // conditions one `all` or `any` lists
  unwraps: 4,
  unwrappedBytes: 200000,
  factTargets: 256,
  evidenceTargets: 128,
  readNesting: 32, // the case document, a result, an unwrapped value
  documentNesting: 64,
  numberChars: 128,
  exponent: 308,
} as const;

const isDigit = (c: number) => c >= 0x30 && c <= 0x39;
const inLiteral = (c: number) => isDigit(c) || c === 0x2b || c === 0x2d || c === 0x2e || c === 0x45 || c === 0x65;

/**
 * Scans bytes outside strings: the deepest nesting (an object or an array opens a level, the root at none) and
 * whether every number literal is within its characters and its exponent's magnitude. A number literal is a
 * maximal run of `0`–`9`, `+`, `-`, `.`, `e` and `E`, whatever it starts with (§12). Nothing is parsed.
 */
export function scanBytes(b: Uint8Array): { nesting: number; numbersWithin: boolean } {
  let depth = 0;
  let nesting = 0;
  let numbersWithin = true;
  let k = 0;
  while (k < b.length) {
    const c = b[k];
    if (c === 0x22) {
      k++;
      while (k < b.length && b[k] !== 0x22) k += b[k] === 0x5c ? 2 : 1;
      k++;
      continue;
    }
    if (c === 0x7b || c === 0x5b) {
      depth++;
      if (depth > nesting) nesting = depth;
    } else if (c === 0x7d || c === 0x5d) {
      depth--;
    } else if (inLiteral(c)) {
      const start = k;
      while (k < b.length && inLiteral(b[k])) k++;
      if (!literalWithin(b.subarray(start, k))) numbersWithin = false;
      continue;
    }
    k++;
  }
  return { nesting, numbersWithin };
}

// The exponent is the run of digits after the literal's first `e` or `E`, past one sign; with none, there is none.
function literalWithin(lit: Uint8Array): boolean {
  if (lit.length > BOUNDS.numberChars) return false;
  let e = lit.findIndex((c) => c === 0x45 || c === 0x65);
  if (e < 0) return true;
  e++;
  if (lit[e] === 0x2b || lit[e] === 0x2d) e++;
  let digits = "";
  while (e < lit.length && isDigit(lit[e])) digits += String.fromCharCode(lit[e++]);
  digits = digits.replace(/^0+/, "");
  return digits.length < 4 && Number(digits || "0") <= BOUNDS.exponent;
}

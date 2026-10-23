/** Bounded complete-attribution accounting reader. No workflow or condition replay.
 * Independently implemented in JavaScript against the shared schema and prose.
 */
import { readFileSync, readSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const schema = JSON.parse(readFileSync(new URL('../schema/workflow-contributors-2.schema.json', import.meta.url)));
const kinds = ['rule', 'forcing-exception'];
export const TRANSPORT_MAX_BYTES = 33554432; // Local transport; never a Core pack ceiling.
class Problem extends Error {
  constructor(code, result = 'refusal') { super(code); this.report = { result, [result]: code }; }
}
const reject = (code, result) => { throw new Problem(code, result); };
const cp = (a, b) => {
  const x = [...a], y = [...b];
  for (let i = 0; i < Math.min(x.length, y.length); i++) {
    const d = x[i].codePointAt(0) - y[i].codePointAt(0); if (d) return d;
  }
  return x.length - y.length;
};
export function canon(value) {
  if (Array.isArray(value)) return '[' + value.map(canon).join(',') + ']';
  if (value && typeof value === 'object') return '{' + Object.keys(value).sort(cp).map(k => JSON.stringify(k) + ':' + canon(value[k])).join(',') + '}';
  return JSON.stringify(value);
}
const sha = bytes => 'sha256:' + createHash('sha256').update(bytes).digest('hex');
export const digest = value => sha(canon(value));
const equal = (a, b) => canon(a) === canon(b);
const own = (object, key, fallback) => Object.hasOwn(object, key) ? object[key] : fallback;

export function parse(raw, controls = true, checkBounds = true) {
  const tokens = raw.match(/"(?:[^"\\]|\\.)*"|[{}\[\],:]|[^\s{}\[\],:]+/gu) ?? [];
  // Check workflow token spellings before JSON.parse converts them to Number values.
  if (controls) for (const token of tokens) {
    if (/^-?[0-9]/u.test(token)) {
      if (token.length > 128) reject('input-over-bound');
      if (!/^-?(0|[1-9][0-9]*)$/u.test(token)) reject('input-malformed');
    }
  }
  let value;
  try { value = JSON.parse(raw); } catch { reject('input-malformed'); }
  // JSON.parse checks grammar. Track names at each object level before accepting its result.
  const frames = [];
  for (const token of tokens) {
    if (token === '{') frames.push({ object: true, key: true, seen: new Set() });
    else if (token === '[') frames.push({ object: false });
    else if (token === '}' || token === ']') frames.pop();
    else if (token === ',' && frames.at(-1)?.object) frames.at(-1).key = true;
    else if (token.startsWith('"') && frames.at(-1)?.object && frames.at(-1).key) {
      const frame = frames.at(-1), key = JSON.parse(token);
      if (frame.seen.has(key)) reject('input-malformed');
      frame.seen.add(key); frame.key = false;
    }
  }
  if (controls && checkBounds) bounds(value); return value;
}
function bounds(value, depth = 0) {
  if (value && typeof value === 'object') {
    if (depth >= 64 || Object.keys(value).length > 4096) reject('input-over-bound');
    for (const [key, child] of Object.entries(value)) { bounds(key, depth + 1); bounds(child, depth + 1); }
  } else if (typeof value === 'string') {
    if (!value.isWellFormed()) reject('input-malformed');
    if (Buffer.byteLength(value) > 65536) reject('input-over-bound');
  } else if (typeof value === 'number' && !Number.isSafeInteger(value)) reject('input-malformed');
}
function valid(value, s) {
  if (typeof s === 'boolean') return s;
  if (s.$ref) return valid(value, schema.$defs[s.$ref.split('/').at(-1)]);
  if (s.oneOf && s.oneOf.filter(choice => valid(value, choice)).length !== 1) return false;
  if (Object.hasOwn(s, 'const') && !equal(value, s.const)) return false;
  if (s.enum && !s.enum.some(x => equal(x, value))) return false;
  if (s.not && valid(value, s.not)) return false;
  const object = value !== null && typeof value === 'object' && !Array.isArray(value);
  if (s.type && !({ object, array: Array.isArray(value), string: typeof value === 'string',
    integer: Number.isSafeInteger(value), boolean: typeof value === 'boolean', null: value === null })[s.type]) return false;
  if (typeof value === 'string' && ((s.minLength !== undefined && [...value].length < s.minLength) ||
      (s.maxLength !== undefined && [...value].length > s.maxLength) || (s.pattern && !(new RegExp(s.pattern, 'u')).test(value)))) return false;
  if (typeof value === 'number' && ((s.minimum !== undefined && value < s.minimum) || (s.maximum !== undefined && value > s.maximum))) return false;
  if (Array.isArray(value)) {
    if ((s.minItems !== undefined && value.length < s.minItems) || (s.maxItems !== undefined && value.length > s.maxItems)) return false;
    if (s.uniqueItems && new Set(value.map(canon)).size !== value.length) return false;
    const prefix = s.prefixItems ?? [];
    if (!value.slice(0, prefix.length).every((x, i) => valid(x, prefix[i]))) return false;
    if (s.items !== undefined && !value.slice(prefix.length).every(x => valid(x, s.items))) return false;
  }
  if (object) {
    if (s.maxProperties !== undefined && Object.keys(value).length > s.maxProperties) return false;
    if (s.required?.some(k => !Object.hasOwn(value, k))) return false;
    for (const [key, child] of Object.entries(value)) {
      if (s.propertyNames && !valid(key, s.propertyNames)) return false;
      let known = false;
      if (s.properties && Object.hasOwn(s.properties, key)) { known = true; if (!valid(child, s.properties[key])) return false; }
      for (const [pattern, rule] of Object.entries(s.patternProperties ?? {})) {
        if ((new RegExp(pattern, 'u')).test(key)) { known = true; if (!valid(child, rule)) return false; }
      }
      if (!known && s.additionalProperties === false) return false;
    }
  }
  return true;
}
function form(value, name) { bounds(value); if (!valid(value, schema.$defs[name])) reject('input-malformed'); }
const increment = (map, key) => { Object.defineProperty(map, key, { value: (Object.hasOwn(map, key) ? map[key] : 0) + 1, writable: true, enumerable: true, configurable: true }); };
const emptyCredits = () => ({ contributors: { rule: {}, 'forcing-exception': {} }, fallback: 0 });
export function summarize(bundle, stage) {
  const result = { summaryVersion: 2, workflowDigest: bundle.workflowDigest, execution: bundle.execution, stage: stage.stage,
    records: stage.records.length, recordsDigest: digest(stage.records.map(r => r.disposition)),
    byKind: { outcome: 0, 'not-applicable': 0, unresolved: 0 }, byOutcome: {}, byReason: {}, byRule: {} };
  for (const row of stage.records) {
    const d = row.disposition; result.byKind[d.kind]++;
    if (d.kind === 'unresolved') for (const reason of d.reasons) increment(result.byReason, reason);
    if (d.kind !== 'outcome') continue;
    increment(result.byOutcome, d.outcomeId);
    if (!Object.hasOwn(result.byRule, d.outcomeId)) Object.defineProperty(result.byRule, d.outcomeId, { value: emptyCredits(), enumerable: true });
    const count = result.byRule[d.outcomeId];
    if (!Object.hasOwn(row.output, 'contributors')) count.fallback++;
    for (const contributor of row.output.contributors ?? []) increment(count.contributors[contributor.kind], contributor.id);
  }
  return result;
}
function selector(value, member, expected) {
  if (!Object.hasOwn(value, member) || !Number.isSafeInteger(value[member])) reject('input-malformed');
  if (value[member] !== expected) reject('version-unread');
}
function transportSize(bundle, packs) {
  return Buffer.byteLength(canon(bundle)) + Object.values(packs).reduce((n, raw) => n + Buffer.byteLength(raw), 0);
}

export function verify(bundle, packs) {
  if (!bundle || typeof bundle !== 'object' || Array.isArray(bundle) || !Object.hasOwn(bundle, 'fixtureVersion')) reject('input-malformed');
  selector(bundle, 'fixtureVersion', 2);
  if (!Array.isArray(bundle.stages)) reject('input-malformed');
  for (const stage of bundle.stages) {
    if (!stage || typeof stage !== 'object' || !stage.summary || typeof stage.summary !== 'object') reject('input-malformed');
    selector(stage.summary, 'summaryVersion', 2);
    if (!Array.isArray(stage.records)) reject('input-malformed');
    for (const row of stage.records) {
      if (!row || typeof row !== 'object' || !row.output || typeof row.output !== 'object') reject('input-malformed');
      selector(row.output, 'outputRecordVersion', 2);
    }
  }
  form(bundle, 'bundleFixture');
  if (transportSize(bundle, packs) > TRANSPORT_MAX_BYTES) reject('input-over-bound');
  if (Buffer.byteLength(canon(bundle)) > 8388608 || bundle.stages.reduce((n, s) => n + s.records.length, 0) > 4096) reject('input-over-bound');
  if (new Set(bundle.stages.map(s => s.stage)).size !== bundle.stages.length) reject('input-malformed');
  const seen = new Set();
  for (const stage of bundle.stages) {
    if (!Object.hasOwn(packs, stage.stage)) reject('inventory-mismatch');
    const raw = packs[stage.stage], pack = parse(raw, false), packDigest = sha(raw);
    for (const row of stage.records) {
      const output = row.output, d = row.disposition, members = output.contributors ?? [];
      if (Buffer.byteLength(canon(output)) > 65536) reject('input-over-bound');
      for (let i = 1; i < members.length; i++) {
        const a = members[i - 1], b = members[i];
        if (a.kind !== b.kind || cp(a.id, b.id) >= 0) reject('input-malformed');
      }
      if (digest(output) !== row.recordDigest) reject('digest-mismatch', 'finding');
      if (seen.has(row.recordDigest)) reject('output-mismatch', 'finding');
      seen.add(row.recordDigest);
      const l = output.lineage;
      if (l.workflowDigest !== bundle.workflowDigest || l.execution !== bundle.execution || l.stage !== stage.stage || l.packDigest !== packDigest) reject('output-mismatch', 'finding');
      if (d.kind !== 'outcome' && members.length) reject('output-mismatch', 'finding');
      for (const member of members) {
        const entries = member.kind === 'rule' ? pack.rules : (pack.exceptions ?? []);
        const matches = entries.filter(e => e.id === member.id);
        if (matches.length !== 1 || matches[0].outcome !== d.outcomeId || (member.kind === 'forcing-exception' && matches[0].effect !== 'force-outcome')) reject('output-mismatch', 'finding');
      }
      if (d.kind === 'outcome' && !members.length && pack.fallbackOutcome !== d.outcomeId) reject('output-mismatch', 'finding');
    }
    if (!equal(stage.summary, summarize(bundle, stage))) reject('summary-mismatch');
  }
  return { result: 'bulk-consistency', attributionVersion: 2, conditions: 'not-replayed' };
}
export function drift(left, right, leftPacks, rightPacks) {
  if (transportSize(left, leftPacks) + transportSize(right, rightPacks) > TRANSPORT_MAX_BYTES) reject('input-over-bound');
  verify(left, leftPacks); verify(right, rightPacks);
  if (left.workflowDigest !== right.workflowDigest) reject('drift-workflow-mismatch');
  if (!equal(left.stages.map(s => s.stage), right.stages.map(s => s.stage))) reject('inventory-mismatch');
  function subtract(a, b) {
    const result = {};
    for (const key of [...new Set([...Object.keys(a), ...Object.keys(b)])].sort(cp)) {
      const delta = own(b, key, 0) - own(a, key, 0); if (delta) result[key] = delta;
    }
    return result;
  }
  const result = { driftVersion: 2, result: 'drift', workflowDigest: left.workflowDigest,
    leftExecutionDigest: left.executionDigest, rightExecutionDigest: right.executionDigest, stages: [], records: [] };
  for (let i = 0; i < left.stages.length; i++) {
    const ls = left.stages[i], rs = right.stages[i], a = ls.summary, b = rs.summary, byRule = {};
    for (const outcome of [...new Set([...Object.keys(a.byRule), ...Object.keys(b.byRule)])].sort(cp)) {
      const ac = own(a.byRule, outcome, emptyCredits()), bc = own(b.byRule, outcome, emptyCredits());
      const contributors = Object.fromEntries(kinds.map(k => [k, subtract(ac.contributors[k], bc.contributors[k])]));
      const fallback = bc.fallback - ac.fallback;
      if (fallback || kinds.some(k => Object.keys(contributors[k]).length)) byRule[outcome] = { contributors, fallback };
    }
    result.stages.push({ stage: ls.stage, records: b.records - a.records,
      byKind: Object.fromEntries(Object.keys(a.byKind).map(k => [k, b.byKind[k] - a.byKind[k]])),
      byOutcome: subtract(a.byOutcome, b.byOutcome), byReason: subtract(a.byReason, b.byReason), byRule });
    const index = stage => {
      const counts = new Map(), records = new Map();
      for (const row of stage.records) {
        const p = row.output.payloadDigest, n = (counts.get(p) ?? 0) + 1; counts.set(p, n);
        records.set(p + '/' + n, row.disposition);
      }
      return records;
    };
    const ar = index(ls), br = index(rs);
    const keys = [...new Set([...ar.keys(), ...br.keys()])].sort((x, y) => {
      const [xp, xn] = x.split('/'), [yp, yn] = y.split('/'); return cp(xp, yp) || Number(xn) - Number(yn);
    });
    for (const key of keys) {
      const av = ar.get(key) ?? null, bv = br.get(key) ?? null;
      if (equal(av, bv)) continue;
      const [payloadDigest, occurrence] = key.split('/');
      result.records.push({ change: av === null ? 'added' : bv === null ? 'removed' : 'changed', stage: ls.stage,
        payloadDigest, occurrence: Number(occurrence), left: av, right: bv });
    }
  }
  form(result, 'drift'); return result;
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    // Bound the JSON transport separately; pack strings are not workflow values.
    const chunks = []; let total = 0;
    for (;;) {
      const chunk = Buffer.alloc(65536);
      const count = readSync(0, chunk, 0, Math.min(chunk.length, TRANSPORT_MAX_BYTES + 1 - total), null);
      if (!count) break;
      total += count;
      if (total > TRANSPORT_MAX_BYTES) reject('input-over-bound');
      chunks.push(chunk.subarray(0, count));
    }
    const request = parse(Buffer.concat(chunks).toString('utf8'), true, false);
    const result = request.command === 'drift' ? drift(request.left, request.right, request.leftPacks, request.rightPacks) : verify(request.bundle, request.packs);
    process.stdout.write(canon(result) + '\n');
  } catch (error) {
    if (!(error instanceof Problem)) throw error;
    process.stdout.write(canon(error.report) + '\n'); process.exitCode = 1;
  }
}

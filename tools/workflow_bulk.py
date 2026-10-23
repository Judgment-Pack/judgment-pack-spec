"""Bounded model-2 bulk accounting experiment; no workflow or evaluator replay.

Accepts hand-authored bundle projections and independently supplied exact pack bytes.
The JavaScript reader shares fixtures and the contract, not this implementation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

SCHEMA = json.loads((Path(__file__).resolve().parents[1] / 'schema' /
                     'workflow-contributors-2.schema.json').read_text())
KINDS = ('rule', 'forcing-exception')


class Problem(Exception):
    def __init__(self, result, code):
        self.report = {'result': result, result: code}
        super().__init__(code)


def fail(code, result='refusal'):
    raise Problem(result, code)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def digest(value):
    return 'sha256:' + hashlib.sha256(canonical(value)).hexdigest()


def parse(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                fail('input-malformed')
            value[key] = item
        return value
    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: fail('input-malformed'))
    except (ValueError, UnicodeError, RecursionError):
        fail('input-malformed')


def bounds(value, depth=0):
    if isinstance(value, (dict, list)):
        if depth >= 64 or len(value) > 4096:
            fail('input-over-bound')
        for item in (value.values() if isinstance(value, dict) else value):
            bounds(item, depth + 1)
        if isinstance(value, dict):
            for key in value:
                bounds(key, depth + 1)
    elif isinstance(value, str):
        try:
            if len(value.encode('utf-8')) > 65536:
                fail('input-over-bound')
        except UnicodeError:
            fail('input-malformed')
    elif value is not None and not isinstance(value, bool):
        if type(value) is not int or abs(value) > 2**53 - 1:
            fail('input-malformed')


def form(value, definition):
    bounds(value)
    validator = jsonschema.Draft202012Validator(
        {'$ref': f'#/$defs/{definition}', '$defs': SCHEMA['$defs']})
    if not validator.is_valid(value):
        fail('input-malformed')


def summarize(bundle, stage):
    """Caller must have checked forms, envelope pins, pack membership and associations."""
    rows = stage['records']
    answer = dict(summaryVersion=2, workflowDigest=bundle['workflowDigest'],
                  execution=bundle['execution'], stage=stage['stage'], records=len(rows),
                  recordsDigest=digest([r['disposition'] for r in rows]),
                  byKind={k: 0 for k in ('outcome', 'not-applicable', 'unresolved')},
                  byOutcome={}, byReason={}, byRule={})
    for row in rows:
        disposition, output = row['disposition'], row['output']
        answer['byKind'][disposition['kind']] += 1
        if disposition['kind'] == 'unresolved':
            for reason in disposition['reasons']:
                answer['byReason'][reason] = answer['byReason'].get(reason, 0) + 1
        if disposition['kind'] != 'outcome':
            continue
        outcome = disposition['outcomeId']
        answer['byOutcome'][outcome] = answer['byOutcome'].get(outcome, 0) + 1
        counts = answer['byRule'].setdefault(outcome, {'contributors': {k: {} for k in KINDS}, 'fallback': 0})
        if 'contributors' not in output:
            counts['fallback'] += 1
        for member in output.get('contributors', []):
            credits = counts['contributors'][member['kind']]
            credits[member['id']] = credits.get(member['id'], 0) + 1
    return answer


def verify(bundle, pack_bytes):
    """Checks bulk consistency, never actual conditions or causal completeness.

    pack_bytes maps stage ids to exact bytes held independently by the caller.
    The bundle is a projection, not an execution record or trust source.
    """
    if not isinstance(bundle, dict) or 'fixtureVersion' not in bundle:
        fail('input-malformed')
    if bundle.get('fixtureVersion') != 2:
        fail('version-unread')
    if not isinstance(bundle.get('stages'), list):
        fail('input-malformed')
    for stage in bundle['stages']:
        if not isinstance(stage, dict) or not isinstance(stage.get('summary'), dict):
            fail('input-malformed')
        if stage['summary'].get('summaryVersion') != 2:
            fail('version-unread')
        if not isinstance(stage.get('records'), list):
            fail('input-malformed')
        for row in stage['records']:
            if not isinstance(row, dict) or not isinstance(row.get('output'), dict):
                fail('input-malformed')
            if row['output'].get('outputRecordVersion') != 2:
                fail('version-unread')
    form(bundle, 'bundleFixture')
    if len(canonical(bundle)) > 8388608 or sum(len(s['records']) for s in bundle['stages']) > 4096:
        fail('input-over-bound')
    stage_ids = [s['stage'] for s in bundle['stages']]
    if len(set(stage_ids)) != len(stage_ids):
        fail('input-malformed')
    seen = set()
    for stage in bundle['stages']:
        if stage['stage'] not in pack_bytes:
            fail('inventory-mismatch')
        raw = pack_bytes[stage['stage']]
        pack_digest = 'sha256:' + hashlib.sha256(raw).hexdigest()
        pack = parse(raw)
        # Caller supplies admitted Core packs. This reader is not a Core document reader.
        for row in stage['records']:
            output, disposition = row['output'], row['disposition']
            if len(canonical(output)) > 65536:
                fail('input-over-bound')
            members = output.get('contributors', [])
            identities = [(m['kind'], m['id']) for m in members]
            if identities != sorted(set(identities)) or len({k for k, _ in identities}) > 1:
                fail('input-malformed')
            if row['recordDigest'] != digest(output):
                fail('digest-mismatch', 'finding')
            if row['recordDigest'] in seen:
                fail('output-mismatch', 'finding')
            seen.add(row['recordDigest'])
            lineage = output['lineage']
            if (lineage['workflowDigest'], lineage['execution'], lineage['stage'], lineage['packDigest']) != (
                    bundle['workflowDigest'], bundle['execution'], stage['stage'], pack_digest):
                fail('output-mismatch', 'finding')
            if disposition['kind'] != 'outcome' and members:
                fail('output-mismatch', 'finding')
            for member in members:
                entries = pack['rules'] if member['kind'] == 'rule' else pack.get('exceptions', [])
                found = [e for e in entries if e['id'] == member['id']]
                if (len(found) != 1 or found[0].get('outcome') != disposition.get('outcomeId') or
                        (member['kind'] == 'forcing-exception' and found[0].get('effect') != 'force-outcome')):
                    fail('output-mismatch', 'finding')
            if disposition['kind'] == 'outcome' and not members and pack.get('fallbackOutcome') != disposition['outcomeId']:
                fail('output-mismatch', 'finding')
        if stage['summary'] != summarize(bundle, stage):
            fail('summary-mismatch')
    return {'result': 'bulk-consistency', 'attributionVersion': 2, 'conditions': 'not-replayed'}


def drift(left, right, left_packs, right_packs):
    verify(left, left_packs)
    verify(right, right_packs)
    if left['workflowDigest'] != right['workflowDigest']:
        fail('drift-workflow-mismatch')
    if [s['stage'] for s in left['stages']] != [s['stage'] for s in right['stages']]:
        fail('inventory-mismatch')
    def subtract(a, b):
        return {k: b.get(k, 0)-a.get(k, 0) for k in sorted(a.keys() | b.keys())
                if b.get(k, 0) != a.get(k, 0)}
    result = dict(driftVersion=2, result='drift', workflowDigest=left['workflowDigest'],
                  leftExecutionDigest=left['executionDigest'], rightExecutionDigest=right['executionDigest'], stages=[], records=[])
    for ls, rs in zip(left['stages'], right['stages']):
        a, b = ls['summary'], rs['summary']
        by_rule = {}
        for outcome in sorted(a['byRule'].keys() | b['byRule'].keys()):
            empty = {'contributors': {k: {} for k in KINDS}, 'fallback': 0}
            ac, bc = a['byRule'].get(outcome, empty), b['byRule'].get(outcome, empty)
            typed = {k: subtract(ac['contributors'][k], bc['contributors'][k]) for k in KINDS}
            fallback = bc['fallback'] - ac['fallback']
            if any(typed.values()) or fallback:
                by_rule[outcome] = dict(contributors=typed, fallback=fallback)
        result['stages'].append(dict(stage=ls['stage'], records=b['records']-a['records'],
            byKind={k: b['byKind'][k]-a['byKind'][k] for k in a['byKind']},
            byOutcome=subtract(a['byOutcome'], b['byOutcome']), byReason=subtract(a['byReason'], b['byReason']), byRule=by_rule))
        def keyed(stage):
            rows, occurrences = {}, {}
            for row in stage['records']:
                payload = row['output']['payloadDigest']
                occurrences[payload] = occurrences.get(payload, 0) + 1
                rows[(payload, occurrences[payload])] = row['disposition']
            return rows
        ar, br = keyed(ls), keyed(rs)
        for key in sorted(ar.keys() | br.keys()):
            av, bv = ar.get(key), br.get(key)
            if av != bv:
                result['records'].append(dict(change='added' if av is None else 'removed' if bv is None else 'changed',
                    stage=ls['stage'], payloadDigest=key[0], occurrence=key[1], left=av, right=bv))
    form(result, 'drift')
    return result

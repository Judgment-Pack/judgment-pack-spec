"""Hand-authored complete-contributor accounting cases in two readers."""
from __future__ import annotations

import copy
import json
import hashlib
import subprocess
import unittest
from pathlib import Path

import jsonschema

from tools import workflow_bulk as reader

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'rfcs/workflow-contributors'


def load(name):
    return json.loads((FIXTURE / name).read_text())


def packs(name='pack.json'):
    return {'cases': (FIXTURE / name).read_bytes()}


def js(request):
    process = subprocess.run(['node', str(ROOT / 'tools/workflow_bulk.mjs')], input=json.dumps(request),
                             text=True, capture_output=True, check=False)
    if process.returncode not in (0, 1):
        raise AssertionError(process.stderr)
    return validate_event(json.loads(process.stdout))


def validate_event(answer):
    if answer.get('result') in ('refusal', 'finding'):
        reader.form(answer, 'verifierReport')
    return answer


def raw_js(raw):
    process = subprocess.run(['node', str(ROOT / 'tools/workflow_bulk.mjs')], input=raw,
                             capture_output=True, check=False)
    if process.returncode not in (0, 1):
        raise AssertionError(process.stderr.decode())
    return validate_event(json.loads(process.stdout))


def python_verify(bundle, supplied=None):
    try:
        return reader.verify(bundle, supplied or packs())
    except reader.Problem as problem:
        return validate_event(problem.report)


def both(bundle, supplied=None):
    supplied = supplied or packs()
    return (python_verify(bundle, supplied), js({'command': 'verify', 'bundle': bundle,
            'packs': {k: v.decode() for k, v in supplied.items()}}))


class CompleteContributorTests(unittest.TestCase):
    def test_every_fixture_has_its_recorded_schema_answer_and_packs_are_core_documents(self):
        validator = jsonschema.Draft202012Validator(reader.SCHEMA, format_checker=jsonschema.FormatChecker())
        manifest = load('manifest.json')
        validator.validate(manifest)
        self.assertEqual({entry['path'] for entry in manifest['files']},
                         {p.name for p in FIXTURE.glob('*.json') if p.name != 'manifest.json'})
        for entry in manifest['files']:
            with self.subTest(path=entry['path']):
                self.assertEqual(validator.is_valid(load(entry['path'])), entry['schemaValid'])
        core = json.loads((ROOT / 'schema/judgment-pack-core.schema.json').read_text())
        for name in ('pack.json', 'pack-reversed.json'):
            jsonschema.Draft202012Validator(core, format_checker=jsonschema.FormatChecker()).validate(load(name))

    def test_added_attribution_members_and_kind_values_have_fixture_witnesses(self):
        bundle = load('bundle.json')
        for member in ('contributors',):
            schema = copy.deepcopy(reader.SCHEMA)
            del schema['$defs']['outputRecord']['properties'][member]
            self.assertFalse(jsonschema.Draft202012Validator(schema).is_valid(bundle))
        for member in ('kind', 'id'):
            schema = copy.deepcopy(reader.SCHEMA)
            del schema['$defs']['contributor']['properties'][member]
            self.assertFalse(jsonschema.Draft202012Validator(schema).is_valid(bundle))
        for kind in reader.KINDS:
            schema = copy.deepcopy(reader.SCHEMA)
            schema['$defs']['contributor']['properties']['kind']['enum'].remove(kind)
            self.assertFalse(jsonschema.Draft202012Validator(schema).is_valid(bundle))
        for kind in reader.KINDS:
            schema = copy.deepcopy(reader.SCHEMA)
            del schema['$defs']['ruleCount']['properties']['contributors']['properties'][kind]
            self.assertFalse(jsonschema.Draft202012Validator(schema).is_valid(bundle))

    def test_execution_schema_vocabularies_have_hand_authored_shape_witnesses(self):
        for case in load('execution-shapes.json')['cases']:
            execution = load('execution-shape.json')
            at = execution
            for key in case['path'][:-1]:
                at = at[key]
            at[case['path'][-1]] = case['value']
            reader.form(execution, 'execution')
            # These are closed-shape witnesses, not a check of the inventory transitions.

    def test_execution_selector_is_three_and_resume_members_are_retained(self):
        execution = load('execution-shape.json')
        reader.form(execution, 'execution')
        self.assertEqual(execution, reader.parse(reader.canonical(execution)))
        for member in ('summaries', 'samples'):
            missing = copy.deepcopy(execution)
            del missing[member]
            with self.assertRaises(reader.Problem) as caught:
                reader.form(missing, 'execution')
            validate_event(caught.exception.report)
        for version in (1, 2):
            historical = copy.deepcopy(execution)
            historical['executionVersion'] = version
            with self.assertRaises(reader.Problem) as caught:
                reader.form(historical, 'execution')
            validate_event(caught.exception.report)

    def test_malformed_projection_events_are_closed_in_both_readers(self):
        examples = [[], None, {}, {'fixtureVersion': 2}, {'fixtureVersion': 2, 'stages': [None]},
                    {'fixtureVersion': 2, 'stages': [{'summary': {'summaryVersion': 2}, 'records': [None]}]}]
        for example in examples:
            for answer in both(example):
                self.assertEqual(answer, {'result': 'refusal', 'refusal': 'input-malformed'})
                reader.form(answer, 'verifierReport')

    def test_required_refusal_vocabulary_has_hand_authored_schema_events(self):
        reports = load('refusal-reports.json')['reports']
        codes = reader.SCHEMA['$defs']['verifierReport']['oneOf'][0]['properties']['refusal']['enum']
        self.assertEqual({r['refusal'] for r in reports}, set(codes))
        self.assertTrue({'version-unread', 'profile-unsupported', 'kind-unread'} <= set(codes))
        for report in reports:
            reader.form(report, 'verifierReport')

    def test_missing_or_mistyped_selectors_are_malformed_and_unknown_versions_unread(self):
        for target in ('fixture', 'output', 'summary'):
            for value in (None, 'missing', True, '2', 99):
                bundle = load('bundle.json')
                at, key = (bundle, 'fixtureVersion') if target == 'fixture' else (
                    (bundle['stages'][0]['records'][0]['output'], 'outputRecordVersion') if target == 'output'
                    else (bundle['stages'][0]['summary'], 'summaryVersion'))
                if value == 'missing':
                    del at[key]
                else:
                    at[key] = value
                expected = 'version-unread' if type(value) is int else 'input-malformed'
                for answer in both(bundle):
                    self.assertEqual(answer, {'result': 'refusal', 'refusal': expected})

    def test_raw_workflow_numeric_spellings_are_checked_in_both_readers(self):
        bundle_raw = (FIXTURE / 'bundle.json').read_bytes()
        for case in load('raw-input-cases.json')['cases']:
            with self.subTest(case=case['name']):
                self.assertIn(case['needle'].encode(), bundle_raw)
                raw = bundle_raw.replace(case['needle'].encode(), case['replacement'].encode(), 1)
                try:
                    answer = reader.verify(reader.parse(raw), packs())
                except reader.Problem as problem:
                    answer = validate_event(problem.report)
                request = b'{"command":"verify","bundle":' + raw + b',"packs":' + json.dumps(
                    {'cases': packs()['cases'].decode()}).encode() + b'}'
                self.assertEqual(answer, case['expected'])
                self.assertEqual(raw_js(request), case['expected'])

    def test_core_pack_numbers_and_transport_strings_keep_independent_scope(self):
        for tail, spelling in ((70000, b'true'), (0, b'2.0'), (0, b'2e0')):
            bundle = load('bundle.json')
            raw = packs()['cases'].replace(b'"value": true', b'"value": '+spelling, 1) + b' '*tail
            core = json.loads((ROOT / 'schema/judgment-pack-core.schema.json').read_text())
            jsonschema.Draft202012Validator(core).validate(json.loads(raw))
            for row in bundle['stages'][0]['records']:
                row['output']['lineage']['packDigest'] = 'sha256:'+hashlib.sha256(raw).hexdigest()
                row['recordDigest'] = reader.digest(row['output'])
            for answer in both(bundle, {'cases': raw}):
                self.assertEqual(answer['result'], 'bulk-consistency')
            reader.parse(raw, controls=False)

    def test_experimental_aggregate_transport_ceiling_is_explicit_and_paired(self):
        raw = packs()['cases'] + b' '*reader.TRANSPORT_MAX_BYTES
        for answer in both(load('bundle.json'), {'cases': raw}):
            self.assertEqual(answer, {'result': 'refusal', 'refusal': 'input-over-bound'})

    def test_schema_is_valid_closed_and_historical_fixtures_stay_legacy(self):
        jsonschema.Draft202012Validator.check_schema(reader.SCHEMA)
        def visit(value):
            if isinstance(value, dict):
                if value.get('type') == 'object':
                    self.assertIs(value.get('additionalProperties'), False)
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(reader.SCHEMA)
        old = json.loads((ROOT / 'conformance/workflow/left-bundle.json').read_text())
        for result in both(old):
            self.assertEqual(result, {'result': 'refusal', 'refusal': 'version-unread'})

    def test_both_readers_agree_on_every_hand_authored_bundle(self):
        for name, pack in [('bundle.json', 'pack.json'), ('bundle-reversed.json', 'pack-reversed.json'),
                           ('bundle-claimed-omission.json', 'pack.json')]:
            for result in both(load(name), packs(pack)):
                self.assertEqual(result, {'result': 'bulk-consistency', 'attributionVersion': 2,
                                          'conditions': 'not-replayed'})

    def test_one_record_gives_two_typed_credits_without_double_counting_the_outcome(self):
        bundle = load('bundle.json')
        stage = bundle['stages'][0]
        one = copy.deepcopy(stage)
        one['records'] = one['records'][:1]
        summary = reader.summarize(bundle, one)
        self.assertEqual(summary['records'], 1)
        self.assertEqual(summary['byOutcome'], {'approve': 1})
        self.assertEqual(summary['byRule'], {'approve': {'contributors': {
            'rule': {'a-rule': 1, 'z-rule': 1}, 'forcing-exception': {}}, 'fallback': 0}})
        one['summary'] = summary
        bundle['stages'] = [one]
        for result in both(bundle):
            self.assertEqual(result['result'], 'bulk-consistency')

    def test_opposite_pack_order_preserves_all_memberships_and_counts(self):
        a, b = load('bundle.json'), load('bundle-reversed.json')
        self.assertEqual(a['stages'][0]['summary'], b['stages'][0]['summary'])
        for left, right in zip(a['stages'][0]['records'], b['stages'][0]['records']):
            self.assertEqual(left['output'].get('contributors'), right['output'].get('contributors'))
        self.assertEqual([r['id'] for r in load('pack.json')['rules']],
                         list(reversed([r['id'] for r in load('pack-reversed.json')['rules']])))

    def test_semantic_expectations_are_hand_authored_and_do_not_claim_replay(self):
        rows = load('bundle.json')['stages'][0]['records']
        cases = load('semantic-cases.json')
        for row, case in zip(rows, cases['cases']):
            self.assertEqual(row['output'].get('contributors'), case['expectedContributors'])
        self.assertEqual(cases['failedEvaluation']['outputs'], [])
        self.assertIsNone(cases['failedEvaluation']['contributors'])
        # Same local id in separate namespaces is counted separately.
        summary = load('bundle.json')['stages'][0]['summary']
        self.assertEqual(summary['byRule']['approve']['contributors']['rule']['a-rule'], 1)
        self.assertEqual(summary['byRule']['approve']['contributors']['forcing-exception']['a-rule'], 1)

    def test_every_hand_written_mutation_is_caught_in_both_readers(self):
        for mutation in load('mutations.json')['cases']:
            with self.subTest(mutation=mutation['name']):
                bundle = load('bundle.json')
                if mutation['target'] == 'drift':
                    bad = load('drift.json')
                    at = bad
                    for key in mutation['path'][:-1]:
                        at = at[key]
                    at[mutation['path'][-1]] = mutation['value']
                    for answer in self.drift_pair():
                        self.assertNotEqual(answer, bad)
                    continue
                stage = bundle['stages'][0]
                if mutation['target'] == 'output':
                    row = stage['records'][mutation['record']]
                    row['output'][mutation['member']] = mutation['value']
                    if mutation['repin']:
                        row['recordDigest'] = reader.digest(row['output'])
                elif mutation['target'] == 'disposition':
                    stage['records'][mutation['record']]['disposition'][mutation['member']] = mutation['value']
                    # Independent byte commitment for the changed retained dispositions, not reader output.
                    raw = json.dumps([r['disposition'] for r in stage['records']], sort_keys=True,
                                     ensure_ascii=False, separators=(',', ':')).encode()
                    stage['summary']['recordsDigest'] = 'sha256:' + hashlib.sha256(raw).hexdigest()
                else:
                    at = stage['summary']
                    for key in mutation['path'][:-1]:
                        at = at[key]
                    at[mutation['path'][-1]] = mutation['value']
                for answer in both(bundle):
                    self.assertEqual(answer, mutation['expected'])

    def drift_pair(self):
        left, right = load('bundle.json'), load('bundle-claimed-omission.json')
        return (reader.drift(left, right, packs(), packs()), js({'command': 'drift',
            'left': left, 'right': right, 'leftPacks': {'cases': packs()['cases'].decode()},
            'rightPacks': {'cases': packs()['cases'].decode()}}))

    def test_signed_membership_drift_can_change_without_an_outcome_change(self):
        for answer in self.drift_pair():
            self.assertEqual(answer, load('drift.json'))
            self.assertEqual(answer['stages'][0]['byOutcome'], {})
            self.assertEqual(answer['records'], [])
        left, right = load('bundle-claimed-omission.json'), load('bundle.json')
        answer = reader.drift(left, right, packs(), packs())
        self.assertEqual(answer['stages'][0]['byRule']['approve']['contributors']['rule'], {'a-rule': 1})

    def test_rewritten_omission_is_not_proof_of_causal_completeness(self):
        # Both readers accept the fully repinned omission: they cannot prove a condition was true.
        # The fixed, independent expected collection catches it; only replay/evidence can do that generally.
        missing = load('bundle-claimed-omission.json')
        self.assertNotEqual(missing['stages'][0]['records'][0]['output']['contributors'],
                            load('semantic-cases.json')['cases'][0]['expectedContributors'])
        for answer in both(missing):
            self.assertEqual(answer['conditions'], 'not-replayed')

    def test_empty_stages_are_versioned_and_mixed_summaries_refused(self):
        bundle = load('bundle.json')
        bundle['stages'][0]['records'] = []
        bundle['stages'][0]['summary'] = reader.summarize(bundle, bundle['stages'][0])
        for answer in both(bundle):
            self.assertEqual(answer['result'], 'bulk-consistency')
        bundle['stages'][0]['summary']['summaryVersion'] = 1
        for answer in both(bundle):
            self.assertEqual(answer, {'result': 'refusal', 'refusal': 'version-unread'})

    def test_count_and_canonical_envelope_bounds_are_refusals(self):
        bundle = load('bundle.json')
        row = bundle['stages'][0]['records'][0]
        row['output']['contributors'] = [{'kind': 'rule', 'id': 'r'+str(i)} for i in range(4097)]
        for answer in both(bundle):
            self.assertEqual(answer, {'result': 'refusal', 'refusal': 'input-over-bound'})
        row['output']['contributors'] = [{'kind': 'rule', 'id': 'r'+'a'*65000}]
        for answer in both(bundle):
            self.assertEqual(answer, {'result': 'refusal', 'refusal': 'input-over-bound'})

    def test_core_ids_longer_than_workflow_ids_are_preserved(self):
        bundle = load('bundle.json')
        pack = load('pack.json')
        old = 'z-rule'; new = 'r'+'a'*80
        for rule in pack['rules']:
            if rule['id'] == old:
                rule['id'] = new
        raw = (json.dumps(pack, indent=2)+'\n').encode()
        import hashlib
        pd = 'sha256:'+hashlib.sha256(raw).hexdigest()
        for row in bundle['stages'][0]['records']:
            row['output']['lineage']['packDigest'] = pd
            for member in row['output'].get('contributors', []):
                if member['kind'] == 'rule' and member['id'] == old:
                    member['id'] = new
            if 'contributors' in row['output']:
                row['output']['contributors'].sort(key=lambda m: (m['kind'], m['id']))
            row['recordDigest'] = reader.digest(row['output'])
        counts = bundle['stages'][0]['summary']['byRule']['approve']['contributors']['rule']
        counts[new] = counts.pop(old)
        for answer in both(bundle, {'cases': raw}):
            self.assertEqual(answer['result'], 'bulk-consistency')

    def test_valid_core_ids_that_are_javascript_object_names_keep_signed_credit(self):
        left, right = load('bundle.json'), load('bundle-claimed-omission.json')
        pack = load('pack.json')
        pack['rules'][1]['id'] = 'constructor'
        pack['exceptions'][2]['targetRule'] = 'constructor'
        for entry in pack['rules'] + pack['exceptions']:
            if entry.get('outcome') == 'approve':
                entry['outcome'] = 'constructor'
        pack['outcomes'][0]['id'] = 'constructor'
        pack['fallbackOutcome'] = 'constructor'
        raw = (json.dumps(pack, indent=2)+'\n').encode()
        import hashlib
        pd = 'sha256:'+hashlib.sha256(raw).hexdigest()
        for bundle in (left, right):
            stage = bundle['stages'][0]
            for row in stage['records']:
                output, disposition = row['output'], row['disposition']
                output['lineage']['packDigest'] = pd
                for member in output.get('contributors', []):
                    if member == {'kind': 'rule', 'id': 'a-rule'}:
                        member['id'] = 'constructor'
                if 'contributors' in output:
                    output['contributors'].sort(key=lambda m: (m['kind'], m['id']))
                if disposition.get('outcomeId') == 'approve':
                    disposition['outcomeId'] = 'constructor'
                row['recordDigest'] = reader.digest(output)
            summary = stage['summary']
            summary['byOutcome']['constructor'] = summary['byOutcome'].pop('approve')
            summary['byRule']['constructor'] = summary['byRule'].pop('approve')
            counts = summary['byRule']['constructor']['contributors']['rule']
            if 'a-rule' in counts:
                counts['constructor'] = counts.pop('a-rule')
            summary['recordsDigest'] = reader.digest([r['disposition'] for r in stage['records']])
        expected = reader.drift(left, right, {'cases': raw}, {'cases': raw})
        actual = js({'command': 'drift', 'left': left, 'right': right,
                     'leftPacks': {'cases': raw.decode()}, 'rightPacks': {'cases': raw.decode()}})
        self.assertEqual(actual, expected)
        self.assertEqual(actual['stages'][0]['byRule']['constructor']['contributors']['rule'], {'constructor': -1})

    def test_duplicate_decoded_json_names_are_rejected_by_both_parsers(self):
        with self.assertRaises(reader.Problem) as caught:
            reader.parse('{"x":1,"\\u0078":2}')
        validate_event(caught.exception.report)
        process = subprocess.run(['node', str(ROOT / 'tools/workflow_bulk.mjs')],
            input='{"x":1,"\\u0078":2}', text=True, capture_output=True)
        self.assertEqual(validate_event(json.loads(process.stdout)), {'result': 'refusal', 'refusal': 'input-malformed'})


if __name__ == '__main__':
    unittest.main()

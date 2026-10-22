"""Profile admission is separate from evaluation and never changes input bytes."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import profile_validation as profiles

VECTORS = json.loads((ROOT / 'conformance/profiles.json').read_text())


class ProfileTests(unittest.TestCase):
    def test_vectors(self):
        for case in VECTORS['cases']:
            document = copy.deepcopy(VECTORS['pack'])
            document['escalation']['routes'].extend(case['appendRoutes'])
            if 'profile' in case:
                document['profile'] = case['profile']
            before = json.dumps(document).encode()
            with self.subTest(case=case['id']):
                self.assertEqual(profiles.validate_core(document, case['profiles']), case['expected'])
                self.assertEqual(json.dumps(document).encode(), before)

    def test_extended_ceiling_and_other_constraints(self):
        document = copy.deepcopy(VECTORS['pack'])
        document['profile'] = 'extended'
        document['escalation']['routes'] *= 2
        self.assertEqual(profiles.validate_core(document, ['extended']), {'status': 'valid'})
        document['escalation']['routes'].append({'target': {'kind': 'queue', 'name': 'Seventeen'}})
        self.assertEqual(profiles.validate_core(document, ['extended'])['code'], 'malformed-input')
        document['escalation']['routes'] = [{'target': {'kind': 'invented', 'name': 'Bad'}}]
        self.assertEqual(profiles.validate_core(document, ['extended'])['code'], 'malformed-input')

    def test_schema_member_and_enum_mutations(self):
        for name in ['schema/judgment-pack-core.schema.json', 'schema/policy/1.0.0/policy.schema.json', 'schema/policy/1.0.0/governing-adoption.schema.json']:
            schema = json.loads((ROOT / name).read_text())
            declaration = schema['properties']['profile']
            self.assertEqual(declaration['default'], 'base')
            for value in ['base', 'extended']:
                self.assertTrue(Draft202012Validator(declaration).is_valid(value))
                mutant = copy.deepcopy(declaration)
                mutant['enum'].remove(value)
                self.assertFalse(Draft202012Validator(mutant).is_valid(value))
        schema = profiles.core_schema('base')
        document = copy.deepcopy(VECTORS['pack'])
        document['profile'] = 'base'
        del schema['properties']['profile']
        self.assertFalse(Draft202012Validator(schema).is_valid(document))

    def test_identity_and_no_default_insertion(self):
        document = copy.deepcopy(VECTORS['pack'])
        hashes = []
        for declaration in [None, 'base', 'extended']:
            if declaration:
                document['profile'] = declaration
            hashes.append(hashlib.sha256(json.dumps(document).encode()).hexdigest())
        self.assertEqual(len(set(hashes)), 3)

    def test_policy_refuses_before_material_loading(self):
        spec = importlib.util.spec_from_file_location('policy_profiles', ROOT / 'conformance/policy/1.0.0/verify.py')
        policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(policy)
        self.assertEqual(policy.CAPABILITY['profiles'], ['base'])
        def unexpected(_):
            self.fail('material loaded before profile refusal')
        for extra in [{}, {'content': ''}, {'content': 'x' * 8193}]:
            raw = json.dumps({'profile': 'extended', **extra}).encode()
            self.assertEqual(policy.verify_input(raw, [(None, None)], unexpected),
                             {'status': 'refused', 'code': 'profile-unsupported', 'profile': 'extended'})
        for declaration in ['', None, 'future', [], {}]:
            self.assertEqual(policy.verify_input(json.dumps({'profile': declaration}).encode(), [])['code'], 'invalid-document')

    def test_both_dialect_readers_check_shared_declarations(self):
        import dialect_verify as dialect
        for row in VECTORS['dialectDeclarations']:
            document = {'profile': row['profile']}
            try:
                actual = dialect.document_profile(document)
            except dialect.Refused as error:
                actual = error.name
            self.assertEqual(actual, row['expected'])
        script = '''import { documentProfile } from './tools/dialect-verify-ts/src/forms.ts';
import { read, utf8 } from './tools/dialect-verify-ts/src/json.ts';
import fs from 'node:fs';
const rows = JSON.parse(fs.readFileSync('conformance/profiles.json')).dialectDeclarations;
console.log(JSON.stringify(rows.map(r => { try { return documentProfile(read(utf8(JSON.stringify({profile:r.profile}))).value); } catch(e) { return e.code; } })));
'''
        completed = subprocess.run(['node', '--experimental-strip-types', '--input-type=module', '-e', script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), [row['expected'] for row in VECTORS['dialectDeclarations']])

    def test_refusal_envelopes_and_dialect_preflight(self):
        import dialect_verify as dialect
        expected = {'result': 'refusal', 'refusal': 'profile-unsupported', 'profile': 'extended'}
        for subordinate in [b'', b'{}', b'x' * 2097153]:
            answer = dialect.verify(b'{"profile":"extended"}', subordinate, b'', b'', b'')
            self.assertEqual(dialect.report(answer.answer), expected)
        script = '''import { verify } from './tools/dialect-verify-ts/src/verify.ts';
import { utf8, preparationForm } from './tools/dialect-verify-ts/src/json.ts';
const reports = ['', '{}', 'x'.repeat(2097153)].map(c => JSON.parse(Buffer.from(preparationForm(verify({dialect:utf8('{"profile":"extended"}'),case:utf8(c),acquisitions:utf8(''),profiles:utf8(''),preparation:utf8(''),requireBinding:false}).report)).toString()));
console.log(JSON.stringify(reports));'''
        result = subprocess.run(['node', '--experimental-strip-types', '--input-type=module', '-e', script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [expected] * 3)
        schema = json.loads((ROOT / 'conformance/policy/1.0.0/vectors.schema.json').read_text())
        envelope = schema['properties']['cases']['items']['properties']['expected']
        validator = Draft202012Validator(envelope)
        self.assertTrue(validator.is_valid({'status': 'refused', 'code': 'profile-unsupported', 'profile': 'extended'}))
        for invalid in [{}, {'status': 'refused', 'code': 'profile-unsupported'}, {'status': 'refused', 'code': 'profile-unsupported', 'profile': 'x' * 8193}]:
            self.assertFalse(validator.is_valid(invalid))

    def test_boundary_vectors_kill_ceiling_and_negotiation_mutants(self):
        # Deliberately break the implementation in memory and run the actual vector test.
        # Neither mutant changes tracked schemas or records output as a fixture.
        original = profiles.core_schema
        def wrong_ceiling(profile):
            schema = original(profile)
            schema['$defs']['escalation']['properties']['routes']['maxItems'] = 8
            return schema
        for target, replacement in [
            ('core_schema', wrong_ceiling),
            ('select_profile', lambda document, supported: document.get('profile', 'base')),
        ]:
            with patch.object(profiles, target, replacement):
                result = unittest.TestResult()
                ProfileTests('test_vectors').run(result)
                self.assertFalse(result.wasSuccessful(), target + ' mutation escaped')
                self.assertTrue(result.failures, target + ' must fail an assertion')

    def test_policy_document_schema_member_mutations(self):
        spec = importlib.util.spec_from_file_location('policy_profile_schema', ROOT / 'conformance/policy/1.0.0/verify.py')
        policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(policy)
        validators = policy.validators()
        for kind, filename in [('policy', 'policy.json'), ('governing-adoption', 'adoption.json')]:
            document = json.loads((ROOT / 'conformance/policy/1.0.0/examples/data-access' / filename).read_text())
            for declaration in ['base', 'extended']:
                document['profile'] = declaration
                validator = validators[kind]
                self.assertTrue(validator.is_valid(document))
                schema = copy.deepcopy(validator.schema)
                del schema['properties']['profile']
                self.assertFalse(validator.evolve(schema=schema).is_valid(document))
                schema = copy.deepcopy(validator.schema)
                schema['properties']['profile']['enum'].remove(declaration)
                self.assertFalse(validator.evolve(schema=schema).is_valid(document))

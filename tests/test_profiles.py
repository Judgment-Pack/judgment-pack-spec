"""Profile admission is separate from evaluation and never changes input bytes."""
import copy
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
import dialect_verify as dialect

VECTORS = json.loads((ROOT / 'conformance/evaluation/staged/profiles.json').read_text())


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
        for name in ['schema/judgment-pack-core.schema.json']:
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
            before = copy.deepcopy(document)
            hashes.append(dialect.digest_of(dialect.canon(document)))
            self.assertEqual(document, before)
        self.assertEqual(len(set(hashes)), 3)
        script = """import { canon, read, utf8 } from './tools/dialect-verify-ts/src/json.ts';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
const pack = JSON.parse(fs.readFileSync('conformance/evaluation/staged/profiles.json')).pack;
console.log(JSON.stringify([undefined, 'base', 'extended'].map(profile => {
  const value = read(utf8(JSON.stringify({...pack, ...(profile === undefined ? {} : {profile})}))).value;
  return 'sha256:' + createHash('sha256').update(canon(value)).digest('hex');
})));
"""
        result = subprocess.run(['node', '--experimental-strip-types', '--input-type=module', '-e', script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), hashes)

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
const rows = JSON.parse(fs.readFileSync('conformance/evaluation/staged/profiles.json')).dialectDeclarations;
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

    def test_released_policy_schemas_do_not_adopt_profiles(self):
        spec = importlib.util.spec_from_file_location('policy_profile_schema', ROOT / 'conformance/policy/1.0.0/verify.py')
        policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(policy)
        validators = policy.validators()
        self.assertNotIn('profiles', policy.CAPABILITY)
        for kind, filename in [('policy', 'policy.json'), ('governing-adoption', 'adoption.json')]:
            document = json.loads((ROOT / 'conformance/policy/1.0.0/examples/data-access' / filename).read_text())
            validator = validators[kind]
            self.assertTrue(validator.is_valid(document))
            self.assertNotIn('profile', validator.schema['properties'])
            for declaration in ['base', 'extended']:
                document['profile'] = declaration
                self.assertFalse(validator.is_valid(document))

    def normative_ceilings(self, label):
        text = (ROOT / 'spec/judgment-pack-core.md').read_text()
        rows = [line.split('|') for line in text.splitlines() if line.startswith('| ' + label + ' |')]
        self.assertEqual(len(rows), 1, 'one normative table row per resource')
        return dict(zip(('base', 'extended'), (int(value.strip()) for value in rows[0][2:4])))

    def route_bound(self, schema, kind):
        if kind == 'escalation':
            return schema['$defs']['escalation']['properties']['routes']
        return schema['$defs']['disposition']['properties']['handoff']['properties']['routes']

    def test_normative_table_matches_both_route_schemas(self):
        limits = self.normative_ceilings('Core escalation routes (and their resulting handoff routes)')
        for profile, ceiling in limits.items():
            schema = profiles.core_schema(profile)
            for kind in ('escalation', 'handoff'):
                with self.subTest(profile=profile, kind=kind):
                    self.assertEqual(self.route_bound(schema, kind)['maxItems'], ceiling)

    def test_handoff_boundary_vectors(self):
        for case in VECTORS['handoffCases']:
            document = copy.deepcopy(VECTORS['handoff'])
            document['handoff']['routes'].extend(case['appendRoutes'])
            schema = profiles.core_schema(case['profile'])
            validator = Draft202012Validator({'$ref': '#/$defs/disposition', '$defs': schema['$defs']})
            with self.subTest(case=case['id']):
                self.assertEqual(validator.is_valid(document), case['valid'])

    def test_admission_probe_in_both_readers(self):
        probe = VECTORS['admissionProbe']
        document = json.dumps(probe['document']).encode()
        case = json.dumps(probe['caseString']['character'] * probe['caseString']['length']).encode()
        acquisitions = json.dumps(probe['acquisitions']).encode()
        ceilings = self.normative_ceilings('Dialect combined dialect, case and acquisitions bytes')
        self.assertGreater(len(case), ceilings['base'])
        self.assertLess(len(document) + len(case) + len(acquisitions), ceilings['extended'])
        answers = []
        for reader in probe['readers']:
            try:
                answer = dialect.admit_envelope(document, case, acquisitions, tuple(reader['profiles']))
            except dialect.Refused as error:
                answer = error.name
            self.assertEqual(answer, reader['expected'])
            answers.append(answer)
        # Exercise the base-only full verifier too: no missing preparation/form diagnostic wins.
        result = dialect.verify(document, case, acquisitions, b'', b'')
        self.assertEqual(dialect.report(result.answer), {'result': 'refusal', 'refusal': 'profile-unsupported', 'profile': 'extended'})
        script = """import { admitEnvelope, verify } from './tools/dialect-verify-ts/src/verify.ts';
import { utf8, preparationForm } from './tools/dialect-verify-ts/src/json.ts';
import fs from 'node:fs';
const p = JSON.parse(fs.readFileSync('conformance/evaluation/staged/profiles.json')).admissionProbe;
const d = utf8(JSON.stringify(p.document));
const c = utf8(JSON.stringify(p.caseString.character.repeat(p.caseString.length)));
const a = utf8(JSON.stringify(p.acquisitions));
const answers = p.readers.map(r => { try { return admitEnvelope(d, c, a, r.profiles); } catch(e) { return e.code; } });
const report = JSON.parse(Buffer.from(preparationForm(verify({dialect:d,case:c,acquisitions:a,profiles:utf8(''),preparation:utf8(''),requireBinding:false}).report)).toString());
console.log(JSON.stringify({answers, report}));
"""
        result = subprocess.run(['node', '--experimental-strip-types', '--input-type=module', '-e', script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {'answers': answers, 'report': {'result': 'refusal', 'refusal': 'profile-unsupported', 'profile': 'extended'}})

    def test_admission_order_is_explicit_in_both_texts(self):
        for name in ('spec/dialect.md', 'rfcs/0018-dialect.md'):
            text = (ROOT / name).read_text()
            phases = text[text.index('**Refusals.**'):text.index('The scope maxima are measured')]
            self.assertLess(phases.index('0. **profile negotiation**'), phases.index('1. the bounds'))
            self.assertIn("using the negotiated profile's ceilings", phases)
            self.assertIn('After profile negotiation (§11 phase 0)', text)
            self.assertNotIn("bounded first, by the documents' sizes, before any is read", text)

    def assert_mutant_fails(self, test):
        result = unittest.TestResult()
        ProfileTests(test).run(result)
        self.assertTrue(result.failures or result.errors, test + ' did not catch the mutation')

    def test_review_fixes_reject_mutations(self):
        original_read = Path.read_text
        table_path = ROOT / 'spec/judgment-pack-core.md'
        for old, new in [('| 8 | 16 |', '| 7 | 16 |'), ('| 8 | 16 |', '| 8 | 7 |')]:
            def changed_table(path, *args, **kwargs):
                text = original_read(path, *args, **kwargs)
                return text.replace(old, new, 1) if path == table_path else text
            with patch.object(Path, 'read_text', changed_table):
                self.assert_mutant_fails('test_normative_table_matches_both_route_schemas')
        for kind in ('escalation', 'handoff'):
            def changed_schema(path, *args, **kwargs):
                text = original_read(path, *args, **kwargs)
                if path == profiles.SCHEMA:
                    schema = json.loads(text)
                    self.route_bound(schema, kind)['maxItems'] = 7
                    return json.dumps(schema)
                return text
            with patch.object(Path, 'read_text', changed_schema):
                self.assert_mutant_fails('test_normative_table_matches_both_route_schemas')
                if kind == 'handoff':
                    self.assert_mutant_fails('test_handoff_boundary_vectors')
        original_schema = profiles.core_schema
        def wrong_extended_handoff(profile):
            schema = original_schema(profile)
            if profile == 'extended':
                self.route_bound(schema, 'handoff')['maxItems'] = 7
            return schema
        with patch.object(profiles, 'core_schema', wrong_extended_handoff):
            self.assert_mutant_fails('test_normative_table_matches_both_route_schemas')
            self.assert_mutant_fails('test_handoff_boundary_vectors')
        original_canon = dialect.canon
        def dropping_profile(document):
            return original_canon({key: value for key, value in document.items() if key != 'profile'})
        with patch.object(dialect, 'canon', dropping_profile):
            self.assert_mutant_fails('test_identity_and_no_default_insertion')
        original_admit = dialect.admit_envelope
        def bounds_before_negotiation(document, case, acquisitions, supported=('base',)):
            if len(document) + len(case) + len(acquisitions) > dialect.ENVELOPE_BYTES:
                raise dialect.Refused('input-over-bound', 'mutated ordering')
            return original_admit(document, case, acquisitions, supported)
        with patch.object(dialect, 'admit_envelope', bounds_before_negotiation):
            self.assert_mutant_fails('test_admission_probe_in_both_readers')
        def missing_phase_zero(path, *args, **kwargs):
            text = original_read(path, *args, **kwargs)
            if path == ROOT / 'spec/dialect.md':
                text = text.replace('0. **profile negotiation**', '**profile negotiation**')
            return text
        with patch.object(Path, 'read_text', missing_phase_zero):
            self.assert_mutant_fails('test_admission_order_is_explicit_in_both_texts')
        # Hand-written TypeScript twins: the same probe and identity assertions reject
        # byte-first admission and a canonicalizer that erases the root declaration.
        script = """import assert, { AssertionError } from 'node:assert/strict';
import { admitEnvelope } from './tools/dialect-verify-ts/src/verify.ts';
import { BOUNDS } from './tools/dialect-verify-ts/src/bounds.ts';
import { canon, read, utf8 } from './tools/dialect-verify-ts/src/json.ts';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
const vectors = JSON.parse(fs.readFileSync('conformance/evaluation/staged/profiles.json'));
const p = vectors.admissionProbe;
const d = utf8(JSON.stringify(p.document)), a = utf8(JSON.stringify(p.acquisitions));
const c = utf8(JSON.stringify(p.caseString.character.repeat(p.caseString.length)));
const byteFirst = p.readers.map(r => {
  if (d.length + c.length + a.length > BOUNDS.inputBytes) return 'input-over-bound';
  try { return admitEnvelope(d, c, a, r.profiles); } catch(e) { return e.code; }
});
assert.throws(() => assert.deepEqual(byteFirst, p.readers.map(r => r.expected)), AssertionError);
const erased = [undefined, 'base', 'extended'].map(profile => {
  const document = {...vectors.pack, ...(profile === undefined ? {} : {profile})};
  delete document.profile;
  return createHash('sha256').update(canon(read(utf8(JSON.stringify(document))).value)).digest('hex');
});
assert.throws(() => assert.equal(new Set(erased).size, 3), AssertionError);
console.log('Both mutation twins caught');
"""
        result = subprocess.run(['node', '--experimental-strip-types', '--input-type=module', '-e', script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'Both mutation twins caught')

"""Named identity preserves both translation families and original preparation evidence."""
import copy
import hashlib
import json
import unittest
from pathlib import Path
from test_dialect import READER, Inputs


def named(raw, family=None):
    value = json.loads(raw)
    family = family or value['version']
    value.update(formatVersion=str(family)+'.0.0', id='urn:judgmentpack:dialect:example', version='0.1.0')
    for member in ('provider', 'facts', 'evidence'):
        value.pop(member, None)
    for member in ('sources', 'unmapped', 'unmappedEvidence'):
        if value.get(member) == []: value.pop(member)
    for obj, members in [(value['case'], ('parameters',)), (value.get('admits', {}), ('facts', 'evidence'))]+[(s, ('parameters',)) for s in value.get('sources', [])]:
        for member in members:
            if obj.get(member) == {}: obj.pop(member)
    return value


def artifact_cases():
    for vector in ('valid', 'version-3-bound', 'unbound-bound-at-import'):
        def build(vector=vector):
            inputs = Inputs(vector, False)
            document = named(inputs.dialect)
            inputs.dialect = json.dumps(document).encode()
            if inputs.binding is not None:
                binding = json.loads(inputs.binding)
                binding['dialect'] = READER.digest_of(READER.canon(READER.read_document(inputs.dialect, 'dialect')))
                inputs.binding = json.dumps(binding).encode()
            parsed = READER.read_bound(READER.parse_dialect(READER.read_document(inputs.dialect, 'dialect')), READER.read_document(inputs.binding, 'binding') if inputs.binding else None, inputs.binding is not None)
            preparation = READER.read_document(inputs.preparation, 'preparation')
            preparation['mappingDigest'] = READER.digest_of(READER.canon(parsed.document))
            inputs.preparation = READER.preparation_bytes(preparation)
            inputs.record = None
            return inputs
        yield 'named-'+vector, 'reading', build


class NamedDialectTest(unittest.TestCase):
    def test_header_and_digest(self):
        for family in (2,3):
            value = named(json.dumps({'version':family,'case':{'facts':[],'evidence':[]}}))
            raw = json.dumps(value).encode()
            parsed = READER.parse_dialect(READER.read_document(raw, 'dialect'))
            expected = ('{"case":{"evidence":[],"facts":[]},"formatVersion":"%d.0.0","id":"urn:judgmentpack:dialect:example","version":"0.1.0"}' % family).encode()
            self.assertEqual(READER.canon(parsed.document), expected)
            self.assertEqual(parsed.version, family)
            changed = dict(value, version='0.1.1')
            self.assertNotEqual(READER.digest_of(expected), READER.digest_of(READER.canon(READER.read_document(json.dumps(changed).encode(), 'changed'))))

    def test_refusals(self):
        base = named(b'{"version":2,"case":{"facts":[],"evidence":[]}}')
        changes = [{'version':v} for v in (2,'2','01.0.0','1.0.0-a','1.0.0+build','1.0.0\n','1.0.0\r','1.0.0\u2028')]
        changes += [{'formatVersion':v} for v in (2,'2','2.1.0',None)]
        changes += [{'id':v} for v in ('','has space','bad\x7f','x'*1025,None)]
        changes += [{'provider':''},{'facts':None},{'sources':[]},{'admits':{'facts':{}}}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(READER.Refused):
                READER.parse_dialect(READER.read_document(json.dumps(dict(base,**change)).encode(),'dialect'))
        legacy = {'version':2,'id':'unexpected','case':{'facts':[],'evidence':[]}}
        with self.assertRaises(READER.Refused): READER.parse_dialect(READER.read_document(json.dumps(legacy).encode(),'legacy'))

    def test_preparations_and_binding(self):
        for name, expected, build in artifact_cases():
            with self.subTest(name=name):
                result = build().verify()
                self.assertIn(expected, result.answer, result.answer)

    def test_staged_file_identities_and_readings(self):
        root=Path(__file__).resolve().parents[1]/'conformance/dialect/artifact-identity'
        manifest=json.loads((root/'manifest.json').read_text())
        for entry in manifest['cases']:
            directory=root/entry['name']
            for filename,sha in entry['files'].items():
                self.assertEqual(hashlib.sha256((directory/filename).read_bytes()).hexdigest(),sha)
            document=(directory/'dialect.json').read_bytes()
            canonical=READER.canon(READER.read_document(document,'dialect'))
            self.assertEqual(canonical,(directory/'dialect.canonical.json').read_bytes())
            self.assertEqual(READER.digest_of(canonical),entry['dialectDigest'])
            result=READER.verify(document,(directory/'case.json').read_bytes(),(directory/'sources.json').read_bytes(),(directory/'profiles.json').read_bytes(),(directory/'preparation.json').read_bytes(),None,False,(directory/'binding.json').read_bytes() if (directory/'binding.json').exists() else None)
            self.assertIn('reading',result.answer)
            self.assertEqual(result.digest,entry['preparationDigest'])

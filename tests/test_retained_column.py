"""Selected leaf certification: handwritten complete preparations, no recorded expectations."""
from pathlib import Path
import copy
import json
import unittest
from unittest.mock import patch

from tools import dialect_verify as reader
from tools import retained_column

ROOT = Path(__file__).resolve().parents[1]
CORPUS = json.loads((ROOT / 'conformance/retained-column/1/preparations.json').read_text())


def check(row, selector=None):
    with patch.object(retained_column, 'installed_spec', return_value=CORPUS['testInstallation']):
        return reader.verify(*(row[k].encode() for k in ('dialectJson','caseJson','acquisitionsJson','profilesJson','preparationJson')),
                             conversion_contract=json.dumps(selector or CORPUS['selector']).encode())


class SelectedPreparations(unittest.TestCase):
    def test_handwritten_complete_preparations(self):
        for row in CORPUS['cases']:
            with self.subTest(case=row['id']):
                result=check(row)
                if row['expected']=='reading':
                    self.assertIn('reading',result.answer,result.answer)
                    expected=reader.preparation_bytes(reader.read_document(row['preparationJson'].encode(),'handwritten expectation'))
                    self.assertEqual(expected,result.preparation)
                else:
                    kind,code=row['expected'].split(':')
                    self.assertEqual(code,result.answer.get('finding' if kind=='finding' else 'refused'),result.answer)

    def test_selector_precedes_all_artifact_admission(self):
        row={k:'' for k in ('dialectJson','caseJson','acquisitionsJson','profilesJson','preparationJson')}
        selector=copy.deepcopy(CORPUS['selector']);selector['spec']['revision']='f'*40
        self.assertEqual('capability-unsupported',check(row,selector).answer.get('refused'))
        selector=copy.deepcopy(CORPUS['selector']);selector['roles'].reverse()
        self.assertEqual('input-malformed',check(row,selector).answer.get('refused'))
        selector=copy.deepcopy(CORPUS['selector']);selector['roles']=['document-validation']
        self.assertEqual('capability-unsupported',check(row,selector).answer.get('refused'))

    def test_absence_keeps_ordinary_closed_grammar(self):
        row=CORPUS['cases'][0]
        result=reader.verify(*(row[k].encode() for k in ('dialectJson','caseJson','acquisitionsJson','profilesJson','preparationJson')))
        self.assertEqual('input-malformed',result.answer.get('refused'))
        self.assertFalse(retained_column.selected())

    def test_selector_and_complete_transformation_are_bound(self):
        row=copy.deepcopy(CORPUS['cases'][0])
        prep=json.loads(row['preparationJson']);prep['conversionContract']['roles'].pop()
        row['preparationJson']=json.dumps(prep)
        self.assertEqual('preparation-differs',check(row).answer.get('finding'))
        prep=json.loads(CORPUS['cases'][0]['preparationJson'])
        prep['lineage'][0]['columnTransformation']['input']['ref']['location']='research-value'
        row['preparationJson']=json.dumps(prep)
        self.assertEqual('preparation-differs',check(row).answer.get('finding'))

    def test_complete_source_input_custody(self):
        for row in CORPUS['cases']:
            if row['expected']!='reading':
                continue
            with self.subTest(case=row['id']), patch.object(retained_column,'installed_spec',return_value=CORPUS['testInstallation']):
                result=reader.verify_source_input(row['sourceInputJson'].encode(),row['profilesJson'].encode(),row['preparationJson'].encode(),json.dumps(CORPUS['selector']).encode())
                self.assertIn('reading',result.answer,result.answer)
        row=CORPUS['cases'][0]
        source=json.loads(row['sourceInputJson']);source['conversionContract']['roles'].pop()
        with patch.object(retained_column,'installed_spec',return_value=CORPUS['testInstallation']):
            result=reader.verify_source_input(json.dumps(source).encode(),b'[]',row['preparationJson'].encode(),json.dumps(CORPUS['selector']).encode())
        self.assertEqual('capability-unsupported',result.answer.get('refused'))

    def test_complete_export_preparation_agreement(self):
        for row in CORPUS['exports']:
            with self.subTest(case=row['id']), patch.object(retained_column,'installed_spec',return_value=CORPUS['testInstallation']):
                result=reader.verify_export(row['wireJson'].encode(),b'[]',json.dumps(CORPUS['selector']).encode(),True)
                if row['expected']=='reading':
                    self.assertIn('reading',result.answer,result.answer)
                else:
                    kind,code=row['expected'].split(':')
                    self.assertEqual(code,result.answer.get('finding' if kind=='finding' else 'refused'),result.answer)
        row=CORPUS['exports'][0]
        document=json.loads(row['wireJson']);document['release']['inputMapping']['profile']='extended'
        with patch.object(retained_column,'installed_spec',return_value=CORPUS['testInstallation']):
            result=reader.verify_export(json.dumps(document).encode(),b'[]',json.dumps(CORPUS['selector']).encode())
        self.assertEqual('read-failed',result.answer.get('finding'))

    def test_selected_document_and_preparation_boundaries(self):
        row=CORPUS['cases'][0]
        for field,member in [('dialectJson','documentBytes'),('profilesJson','profilesBytes'),('preparationJson','preparationBytes')]:
            with self.subTest(artifact=field):
                boundary=copy.deepcopy(row);cap=retained_column.CAPS['base'][member]
                boundary[field]+=' '*(cap-len(boundary[field].encode()))
                self.assertIn('reading',check(boundary).answer)
                boundary[field]+=' '
                self.assertEqual('input-over-bound',check(boundary).answer.get('refused'))


if __name__=='__main__':
    unittest.main()

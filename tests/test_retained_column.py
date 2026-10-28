"""Selected leaf certification: handwritten complete preparations, no recorded expectations."""
from pathlib import Path
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
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


def boundary_row(case):
    row=copy.deepcopy(next(row for row in CORPUS['cases'] if row['id']==case['baseCaseId']))
    row.update(case)
    return row


def boundary_result(case):
    row=boundary_row(case)
    selector=bytes.fromhex(case['selectorHex']) if 'selectorHex' in case else json.dumps(CORPUS['selector']).encode()
    with patch.object(retained_column,'installed_spec',return_value=CORPUS['testInstallation']):
        if case['entrypoint']=='verify':
            return reader.verify(*(row[k].encode() for k in ('dialectJson','caseJson','acquisitionsJson','profilesJson','preparationJson')),conversion_contract=selector)
        artifact=bytes.fromhex(case['artifactHex']) if 'artifactHex' in case else (row['sourceInputJson'] if case['entrypoint']=='source-input' else row.get('wireJson',CORPUS['exports'][0]['wireJson'])).encode()
        if case['entrypoint']=='source-input':
            return reader.verify_source_input(artifact,row['profilesJson'].encode(),row['preparationJson'].encode(),selector)
        return reader.verify_export(artifact,row['profilesJson'].encode(),selector)


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


    def test_review_reader_boundaries(self):
        for case in CORPUS['readerBoundaryCases']:
            with self.subTest(case=case['id']):
                result=boundary_result(case)
                if case['expected']=='reading':
                    self.assertIn('reading',result.answer,result.answer)
                    self.assertEqual(reader.preparation_bytes(reader.read_document(boundary_row(case)['preparationJson'].encode(),'handwritten expectation')),result.preparation)
                else:
                    kind,code=case['expected'].split(':')
                    self.assertEqual(code,result.answer.get('finding' if kind=='finding' else 'refused'),result.answer)

    def test_review_cli_refusal_protocol(self):
        node=shutil.which('node')
        self.assertIsNotNone(node,'selected CLI certification requires Node')
        with tempfile.TemporaryDirectory(prefix='retained-cli-review-') as temporary:
            root=Path(temporary)
            # Synthetic installation seam only; execute the real CLI argument/read/report paths.
            python=root/'python-cli.py';python.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom tools import retained_column,dialect_verify\nretained_column.installed_spec=lambda:'+repr(CORPUS['testInstallation'])+'\nraise SystemExit(dialect_verify.main())\n')
            typescript=root/'typescript-cli.mjs';typescript.write_text('import {installation} from '+json.dumps((ROOT/'tools/dialect-verify-ts/src/retained.ts').as_uri())+';installation.identity=()=>('+json.dumps(CORPUS['testInstallation'])+');await import('+json.dumps((ROOT/'tools/dialect-verify-ts/src/main.ts').as_uri())+');')
            for case in (c for c in CORPUS['readerBoundaryCases'] if c['cli']):
                row=boundary_row(case);files=root/case['id'];files.mkdir()
                for key in ('dialectJson','caseJson','acquisitionsJson','profilesJson','preparationJson'):
                    (files/key).write_text(row[key])
                selector=bytes.fromhex(case['selectorHex']) if 'selectorHex' in case else json.dumps(CORPUS['selector']).encode()
                (files/'selector').write_bytes(selector)
                args=['--conversion-contract',str(files/'selector'),'--profiles',str(files/'profilesJson')]
                if case['entrypoint']=='verify':
                    for flag,key in [('--dialect','dialectJson'),('--case','caseJson'),('--acquisitions','acquisitionsJson'),('--preparation','preparationJson')]:args.extend([flag,str(files/key)])
                else:
                    value=row['sourceInputJson'] if case['entrypoint']=='source-input' else row.get('wireJson',CORPUS['exports'][0]['wireJson'])
                    (files/'artifact').write_bytes(bytes.fromhex(case['artifactHex']) if 'artifactHex' in case else value.encode())
                    args.extend(['--source-input' if case['entrypoint']=='source-input' else '--export',str(files/'artifact')])
                    if case['entrypoint']=='source-input':args.extend(['--preparation',str(files/'preparationJson')])
                for language,command in [('python',[sys.executable,'-B',str(python)]),('typescript',[node,'--disable-wasm-trap-handler','--no-warnings',str(typescript)])]:
                    with self.subTest(case=case['id'],language=language):
                        result=subprocess.run(command+args,capture_output=True,text=True,timeout=30,env={**os.environ,'NODE_OPTIONS':''})
                        expected=case['expected'];self.assertEqual(0 if expected=='reading' else 1,result.returncode,result.stderr)
                        report=json.loads(result.stdout)
                        self.assertEqual('reading' if expected=='reading' else 'refusal',report['result'])
                        if expected!='reading':self.assertEqual(expected.split(':')[1],report['refusal'])
                # A real file I/O failure remains CLI exit3, not a malformed-input refusal.
                if case['id']=='case-depth-exact-retained':
                    args[args.index('--profiles')+1]=str(files/'missing-profiles')
                    for command in ([sys.executable,'-B',str(python)],[node,'--disable-wasm-trap-handler','--no-warnings',str(typescript)]):
                        result=subprocess.run(command+args,capture_output=True,text=True,timeout=30,env={**os.environ,'NODE_OPTIONS':''})
                        self.assertEqual(3,result.returncode,result.stderr);self.assertEqual('',result.stdout)

    def test_installed_identity_is_the_v0_3_0_distribution(self):
        # The real installation check, on a disposable copy of a v0.3.0 installation.
        inventory_path='releases/v0.3.0.retained-column.json'
        inventory=json.loads((ROOT/inventory_path).read_text())
        commit='a'*40
        final={'releaseVersion':'0.3.0','tag':'v0.3.0','specVersion':'0.3.0','maturity':'draft','sourceCommit':commit}
        spec={'version':'0.3.0','revision':commit,'schemaSha256':inventory['schemaSha256'],'corpusSha256':inventory['corpusSha256']}
        def select(version='0.3.0'):
            return retained_column.begin(json.dumps({'contract':'retained-column/1','spec':{**spec,'version':version},
                                                     'profile':'base','roles':['preparation-verification']}).encode())
        def unsupported(action):
            with self.assertRaises(retained_column.engine.Refusal) as raised:
                action()
            self.assertEqual(('capability-unsupported',),raised.exception.args)
        with tempfile.TemporaryDirectory(prefix='retained-installation-') as temporary:
            root=Path(temporary)
            for name in (inventory_path,*inventory['files']):
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
            identity=root/'release-identity.json'
            with patch.object(retained_column,'ROOT',root):
                identity.write_text(json.dumps(final))
                self.assertEqual(spec,retained_column.installed_spec())
                self.assertEqual('0.3.0',select().selector['spec']['version'])
                unsupported(lambda:select('0.3.0-rc.2'))
                for changed in ({'tag':'v0.3.0-rc.2','releaseVersion':'0.3.0-rc.2'},{'releaseVersion':'0.3.0-rc.2'},
                                {'maturity':'candidate'},{'sourceCommit':'A'*40}):
                    with self.subTest(changed=changed):
                        identity.write_text(json.dumps({**final,**changed}));unsupported(retained_column.installed_spec)
                identity.write_text(json.dumps(final))
                listed=root/inventory_path;original=listed.read_bytes()
                listed.write_text(json.dumps({**inventory,'distribution':'v0.3.0-rc.2'}));unsupported(retained_column.installed_spec)
                listed.write_bytes(original)
                pinned=root/inventory['corpus'];pinned.write_bytes(pinned.read_bytes()+b' ');unsupported(retained_column.installed_spec)
                shutil.copyfile(ROOT/inventory['corpus'],pinned)
                identity.unlink();unsupported(select)

    def test_origin_specific_raw_value_bounds(self):
        result=subprocess.run([sys.executable,'-B',str(ROOT/'tools/check_retained_column.py'),'--raw-values-only'],cwd=ROOT,capture_output=True,text=True,timeout=60)
        self.assertEqual(0,result.returncode,result.stdout+result.stderr)
        self.assertIn('origin/UTF8/frame bounds + 3 complete snapshot/projection cases PASS',result.stdout)

    def test_import_program_faults_are_not_refusals(self):
        case=next(c for c in CORPUS['readerBoundaryCases'] if c['id']=='source-import-valid-unbound')
        with patch.object(reader,'read_bound',side_effect=RuntimeError('program-fault')),self.assertRaisesRegex(RuntimeError,'program-fault'):
            boundary_result(case)


if __name__=='__main__':
    unittest.main()

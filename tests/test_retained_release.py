"""Exact RC2 inventory, preserved RC1 identity, the final's leaf, and new schema publication."""
from pathlib import Path
from urllib.parse import urlsplit
from unittest.mock import patch
import ast
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile

from tools import build_release

ROOT=Path(__file__).resolve().parents[1]
INVENTORY='releases/v0.3.0-rc.2.retained-column.json'
FINAL_INVENTORY='releases/v0.3.0.retained-column.json'
FINAL_FIXTURE_FILES=('releases/v0.3.0.md','releases/v0.3.0.milestone.json','rfcs/0029-retained-column-conversions.md',
                     'schema/judgment-pack-core.schema.json','conformance/manifest.json','conformance/evaluation/manifest.json')


def final_fixture(root):
    """Copy the final's leaf set, both inventories and its Core pins; nothing is generated."""
    inventory=json.loads((ROOT/FINAL_INVENTORY).read_text())
    for name in {INVENTORY,FINAL_INVENTORY,*inventory['files'],*FINAL_FIXTURE_FILES}:
        target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    return inventory


class RetainedRelease(unittest.TestCase):
    def test_closed_inventory_and_non_circular_pins(self):
        build_release.validate_retained_inventory()
        manifest=json.loads((ROOT/INVENTORY).read_text())
        self.assertNotIn(INVENTORY,manifest['files'])
        for name in ('schema','corpus'):
            self.assertEqual(manifest[name+'Sha256'],'sha256:'+hashlib.sha256((ROOT/manifest[name]).read_bytes()).hexdigest())
        source=(ROOT/'tools/build_release.py').read_text()
        self.assertIn('"sourceCommit": git(',source)

    def test_inventory_refuses_changed_and_missing_corpus_inputs(self):
        manifest=json.loads((ROOT/INVENTORY).read_text())
        with tempfile.TemporaryDirectory(prefix='retained-inventory-') as temporary:
            root=Path(temporary)
            for name in [INVENTORY,*manifest['files']]:
                destination=root/name;destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/name,destination)
            build_release.validate_retained_inventory(root)
            cases_path=root/manifest['corpus'];original_cases=cases_path.read_bytes();cases=json.loads(original_cases)
            del cases['inputs']['conformance/retained-column/1/preparations.json']
            cases_path.write_text(json.dumps(cases))
            changed=copy.deepcopy(manifest);changed['files'][manifest['corpus']]='sha256:'+hashlib.sha256(cases_path.read_bytes()).hexdigest();changed['corpusSha256']=changed['files'][manifest['corpus']]
            (root/INVENTORY).write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError,'complete corpus input set'):
                build_release.validate_retained_inventory(root)
            cases_path.write_bytes(original_cases);(root/INVENTORY).write_text(json.dumps(manifest))
            corpus=root/manifest['corpus'];corpus.write_bytes(corpus.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'immutable artifact bytes'):
                build_release.validate_retained_inventory(root)
            shutil.copyfile(ROOT/manifest['corpus'],corpus)
            (root/'conformance/retained-column/1/preparations.json').unlink()
            with self.assertRaisesRegex(ValueError,'complete artifact inventory'):
                build_release.validate_retained_inventory(root)

    def test_rc2_mapping_is_closed_and_keeps_final_milestone(self):
        self.assertEqual(build_release.CORE_RC2_IDENTITY,json.loads((ROOT/'releases/v0.3.0-rc.2.json').read_text()))
        self.assertEqual({'v0.3.0-rc.1','v0.3.0-rc.2'},set(build_release.CORE_RC_IDENTITIES))
        self.assertEqual({'number':2,'title':'v0.3.0'},json.loads((ROOT/'releases/v0.3.0-rc.2.milestone.json').read_text()))
        # Preparation does not satisfy adoption or release publication.
        status=(ROOT/'rfcs/0029-retained-column-conversions.md').read_text()
        if '- Status: Accepted' in status.splitlines():
            build_release.validate_artifacts('0.3.0-rc.2','v0.3.0-rc.2')
        else:
            with self.assertRaisesRegex(ValueError,'RFC0029 acceptance'):
                build_release.validate_artifacts('0.3.0-rc.2','v0.3.0-rc.2')

    def test_rc2_scoped_mapping_inventory_and_acceptance_gates(self):
        # Disposable adoption fixture, not a claim that this candidate's public gates passed.
        inventory=json.loads((ROOT/INVENTORY).read_text())
        paths={INVENTORY,*inventory['files'],
               'releases/v0.3.0-rc.2.json','releases/v0.3.0-rc.2.md','releases/v0.3.0-rc.2.milestone.json',
               'rfcs/0029-retained-column-conversions.md','schema/judgment-pack-core.schema.json',
               'conformance/manifest.json','conformance/evaluation/manifest.json'}
        with tempfile.TemporaryDirectory(prefix='rc2-adoption-fixture-') as temporary:
            root=Path(temporary)
            for name in paths:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
            rfc=root/'rfcs/0029-retained-column-conversions.md'
            rfc.write_text(rfc.read_text().replace('- Status: Review','- Status: Accepted'))
            build_release.validate_artifacts('0.3.0-rc.2','v0.3.0-rc.2',root)
            for name,changed,message in [
                ('releases/v0.3.0-rc.2.json',{'extra':True},'mapping does not match'),
                ('releases/v0.3.0-rc.2.milestone.json',{'number':3,'title':'v0.3.0'},'final Core milestone')]:
                path=root/name;original=path.read_bytes();value=json.loads(original);value.update(changed);path.write_text(json.dumps(value))
                with self.assertRaisesRegex(ValueError,message):
                    build_release.validate_artifacts('0.3.0-rc.2','v0.3.0-rc.2',root)
                path.write_bytes(original)
            rfc.write_text(rfc.read_text().replace('- Status: Accepted','- Status: Review'))
            with self.assertRaisesRegex(ValueError,'RFC0029 acceptance'):
                build_release.validate_artifacts('0.3.0-rc.2','v0.3.0-rc.2',root)

    def test_rc2_packages_reader_and_inventory_without_publishing_staged_dialect(self):
        def git(*args):
            if args[0]=='ls-tree':
                directory=args[-1].split(':',1)[1]
                return '\n'.join(p.name for p in (ROOT/directory).iterdir())
            raise AssertionError(args)
        with patch.object(build_release,'git',side_effect=git):
            paths=build_release.bundle_paths('v0.3.0-rc.2','synthetic-tree')
        for path in (*build_release.RETAINED_BUNDLE_PATHS,INVENTORY,'conformance/retained-column','releases/v0.3.0-rc.2.milestone.json'):
            self.assertIn(path,paths)
        attributes=(ROOT/'.gitattributes').read_text()
        self.assertIn('conformance/dialect/** export-ignore -text',attributes)

    def test_final_inventory_is_rc2s_but_for_its_distribution(self):
        build_release.validate_final_retained_inventory()
        final=json.loads((ROOT/FINAL_INVENTORY).read_text());candidate=json.loads((ROOT/INVENTORY).read_text())
        self.assertEqual(('v0.3.0','v0.3.0-rc.2'),(final['distribution'],candidate['distribution']))
        self.assertEqual({**candidate,'distribution':'v0.3.0'},final)
        self.assertEqual({'v0.3.0-rc.2':INVENTORY,'v0.3.0':FINAL_INVENTORY},build_release.RETAINED_INVENTORIES)
        self.assertEqual({'number':2,'title':'v0.3.0'},json.loads((ROOT/'releases/v0.3.0.milestone.json').read_text()))
        self.assertNotIn('v0.3.0',build_release.CORE_RC_IDENTITIES)
        build_release.validate_artifacts('0.3.0','v0.3.0')

    def test_final_route_refuses_each_leaf_rule(self):
        # Disposable fixture of the final's tree; each refusal is restored before the next one.
        with tempfile.TemporaryDirectory(prefix='final-leaf-fixture-') as temporary:
            root=Path(temporary);inventory=final_fixture(root)
            build_release.validate_artifacts('0.3.0','v0.3.0',root)
            def refuses(message):
                with self.assertRaisesRegex(ValueError,message):
                    build_release.validate_artifacts('0.3.0','v0.3.0',root)
            def json_change(name,change):
                path=root/name;original=path.read_bytes();value=json.loads(original);change(value);path.write_text(json.dumps(value))
                return lambda:path.write_bytes(original)
            # Changed leaf bytes with a final inventory regenerated to match them: not RC2's bytes.
            corpus=root/inventory['corpus'];original_corpus=corpus.read_bytes();corpus.write_bytes(original_corpus+b' ')
            pin='sha256:'+hashlib.sha256(corpus.read_bytes()).hexdigest()
            def repin(value):
                value['files'][inventory['corpus']]=pin;value['corpusSha256']=pin
            restore=json_change(FINAL_INVENTORY,repin)
            build_release.validate_retained_inventory(root,'v0.3.0')
            refuses('differs from the published RC2 inventory')
            restore();refuses('immutable artifact bytes')
            corpus.write_bytes(original_corpus)
            for name,change,message in [
                (INVENTORY,lambda v:v.update(claim='other'),'differs from the published RC2 inventory'),
                (INVENTORY,lambda v:v.update(extra=True),'differs from the published RC2 inventory'),
                (FINAL_INVENTORY,lambda v:v.update(distribution='v0.3.0-rc.2'),'identity or scope differs'),
                (FINAL_INVENTORY,lambda v:v.update(maturity='candidate'),'identity or scope differs'),
                ('releases/v0.3.0.milestone.json',lambda v:v.update(number=3),'final Core milestone')]:
                with self.subTest(name=name,message=message):
                    restore=json_change(name,change);refuses(message);restore()
            for name,message in [(INVENTORY,'published RC2 retained-column inventory is missing'),
                                 (FINAL_INVENTORY,'inventory is missing for the exact tag'),
                                 ('releases/v0.3.0.milestone.json','final Core milestone')]:
                with self.subTest(missing=name):
                    path=root/name;original=path.read_bytes();path.unlink();refuses(message);path.write_bytes(original)
            rfc=root/'rfcs/0029-retained-column-conversions.md';accepted=rfc.read_text()
            rfc.write_text(accepted.replace('- Status: Accepted','- Status: Review'));refuses('RFC0029 acceptance')
            rfc.write_text(accepted)
            # A final has no separate distribution identity: no mapping is admitted beside it.
            (root/'releases/v0.3.0.json').write_text(json.dumps({**build_release.CORE_RC2_IDENTITY,'tag':'v0.3.0'}))
            refuses('only the allowlisted Core RCs have a release mapping')
            (root/'releases/v0.3.0.json').unlink()
            build_release.validate_artifacts('0.3.0','v0.3.0',root)

    def test_final_bundle_paths_carry_the_leaf_without_a_mapping(self):
        def git(*args):
            if args[0]=='ls-tree':
                directory=args[-1].split(':',1)[1]
                return '\n'.join(p.name for p in (ROOT/directory).iterdir())
            raise AssertionError(args)
        with patch.object(build_release,'git',side_effect=git):
            paths=build_release.bundle_paths('v0.3.0','synthetic-tree')
        for path in (*build_release.RETAINED_BUNDLE_PATHS,FINAL_INVENTORY,'releases/v0.3.0.milestone.json',
                     'releases/v0.3.0.md','conformance/retained-column','schema/retained-column','spec'):
            self.assertIn(path,paths)
        for path in (INVENTORY,'releases/v0.3.0.json','docs/releases/v0.3.0.md','releases/v0.3.0-rc.2.milestone.json',
                     'conformance/policy','schema/policy'):
            self.assertNotIn(path,paths)

    def test_final_cli_archives_the_leaf_with_no_rc_identity(self):
        # The actual builder CLI on a disposable fixture repository and a real annotated tag.
        with tempfile.TemporaryDirectory(prefix='final-archive-fixture-') as temporary:
            root=Path(temporary);final_fixture(root)
            for name in ('tools/build_release.py','tools/dialect_verify.py','requirements-dev.txt','.gitattributes'):
                (root/name).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,root/name)
            for name in ('README.md','LICENSE','NOTICE','CHANGELOG.md','VERSIONING.md','TESTING.md','SECURITY.md'):
                (root/name).write_text('Hand-authored archive fixture, not release artifacts.\n')
            (root/'examples').mkdir();(root/'examples/control.json').write_text('{"fixture":true}\n')
            def git(*args):
                return subprocess.run(['git','-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                                       '-c','commit.gpgsign=false','-c','tag.gpgsign=false',*args],
                                      cwd=root,check=True,capture_output=True,text=True).stdout.strip()
            git('init','--quiet');git('add','.');git('commit','--quiet','-s','-m','Final archive fixture')
            commit=git('rev-parse','HEAD');git('tag','-a','v0.3.0','-m','Fixture only')
            built=subprocess.run([sys.executable,'tools/build_release.py','--tag','v0.3.0','--commit',commit,'--output','dist'],
                                 cwd=root,capture_output=True,text=True)
            self.assertEqual(0,built.returncode,built.stderr)
            prefix='judgment-pack-spec-0.3.0/'
            with tarfile.open(root/'dist/judgment-pack-spec_0.3.0_artifacts.tar.gz') as archive:
                names={m.name[len(prefix):] for m in archive.getmembers() if m.isfile()}
                self.assertEqual((root/FINAL_INVENTORY).read_bytes(),archive.extractfile(prefix+FINAL_INVENTORY).read())
            with zipfile.ZipFile(root/'dist/judgment-pack-spec_0.3.0_artifacts.zip') as archive:
                self.assertEqual(names,{n[len(prefix):] for n in archive.namelist() if not n.endswith('/')})
            for name in (FINAL_INVENTORY,'releases/v0.3.0.milestone.json','releases/v0.3.0.md','tools/retained_column.py',
                         'tools/dialect-verify-ts/src/retained.ts','schema/retained-column/1/contract.schema.json',
                         'conformance/retained-column/1/cases.json'):
                self.assertIn(name,names)
            for name in ('release-identity.json','releases/v0.3.0.json',INVENTORY,'rfcs/0029-retained-column-conversions.md'):
                self.assertNotIn(name,names)

    def test_schema_publisher_serves_exact_new_id_and_bytes(self):
        tree=ast.parse((ROOT/'web/build.py').read_text())
        nodes=[node for node in tree.body if
               isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='CANONICAL_SCHEMA_SOURCES' for x in node.targets)
               or isinstance(node,ast.FunctionDef) and node.name=='publish_canonical_schemas']
        namespace={'ROOT':ROOT,'Path':Path,'json':json,'urlsplit':urlsplit,'shutil':shutil}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'canonical-publisher','exec'),namespace)
        with tempfile.TemporaryDirectory(prefix='retained-site-') as temporary:
            output=Path(temporary);namespace['publish_canonical_schemas'](output)
            self.assertEqual((ROOT/'schema/retained-column/1/contract.schema.json').read_bytes(),(output/'schema/retained-column/1/contract.schema.json').read_bytes())
        self.assertIn('spec/retained-column/index.html',(ROOT/'web/build.py').read_text())


if __name__=='__main__':unittest.main()

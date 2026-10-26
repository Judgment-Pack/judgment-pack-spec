"""Exact RC2 inventory, preserved RC1 identity, and new schema publication."""
from pathlib import Path
from urllib.parse import urlsplit
from unittest.mock import patch
import ast
import copy
import hashlib
import json
import shutil
import tempfile
import unittest

from tools import build_release

ROOT=Path(__file__).resolve().parents[1]
INVENTORY='releases/v0.3.0-rc.2.retained-column.json'


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

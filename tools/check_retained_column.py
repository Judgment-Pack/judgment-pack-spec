#!/usr/bin/env python3
"""Selected leaf fragment checks with handwritten expectations; full-preparation certification is separate."""
import copy
import json
import os
from pathlib import Path
from fractions import Fraction
import subprocess
import sys
import jsonschema

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "conformance/retained-column/1"
DATA = json.loads((HERE/'cases.json').read_text())
EXAMPLES = json.loads((HERE/'examples.json').read_text())
SCHEMA = json.loads((ROOT/'schema/retained-column/1/contract.schema.json').read_text())
jsonschema.Draft202012Validator.check_schema(SCHEMA)
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)

# The default all-definition coverage loop must carry the closed custody/selection alternatives.
GLOBAL_SCHEMA_EXAMPLES = [EXAMPLES[k] for k in (
    'generatedFrame', 'assertedFrame', 'lineageFragment', 'generatedCarrier', 'capabilitiesFragment',
    'preparationSourceFragment', 'retainedSourceFragment', 'assertedCaseCustodyFragment', 'selectionFragment')]
GLOBAL_SCHEMA_EXAMPLES.append({'case': {'retained': EXAMPLES['assertedFrame']}})
PREPARATIONS = json.loads((HERE/'preparations.json').read_text())
GLOBAL_SCHEMA_EXAMPLES.extend(json.loads(c['preparationJson']) for c in PREPARATIONS['cases'] if c['expected']=='reading')


def executable_probe(source):
    """Explicitly run a scratch mutation; imported engines never consume their host's stdin."""
    guard = 'if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {'
    if guard in source:
        assert source.count(guard) == 1, 'fragment entrypoint mutation target'
        return source.replace(guard, 'if (true) {')
    return source


def fixture(case):
    column = case.get('column', 'Column')
    kind = case['kind']
    rule = {'contractVersion':'1','column':column,'kind':kind,**case.get('rule',{})}
    generated = case.get('origin', 'generated' if kind=='research-value' else 'asserted') == 'generated'
    frame = {'contractVersion':'1','origin':'generated' if generated else 'asserted','values':{},'research':None}
    if kind!='research-value' and 'inputJson' in case:
        frame['values'][column] = json.loads(case['inputJson'])
    if generated:
        entries = [] if case.get('undeclared') else [{'name':column,'fieldJson':json.dumps({'name':column,'type':case.get('type','text')},separators=(',',':'))}]
        declaration = None if 'declaration' in case and case['declaration'] is None else {'recipeRevision':'recipe:2' if case.get('revisionMismatch') else 'recipe:1','fields':entries}
        field = {'status':case.get('status','supported')}
        if 'inputJson' in case and case.get('inputState')!='missing':
            field['valueJson'] = case['inputJson']
        frame['research'] = {'recordRecipeRevision':'recipe:1','declaration':declaration,'fields':{} if case.get('fieldEntryAbsent') else {column:field}}
    return {'rule':rule,'frame':frame}



def check_raw_values():
    """Origin-specific UTF-8 admission, independent frame maxima and joint snapshot caps."""
    import hashlib
    compact = lambda v: json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    digest = lambda text: 'sha256:' + hashlib.sha256(text.encode()).hexdigest()
    requests, expected = [], []
    for case in DATA['rawValueBounds']:
        raw = compact(['x'*case['itemBytes']]*case['listItems']) if 'listItems' in case else case['unit']*case['repeat']+case.get('suffix','')
        if 'expectedBytes' in case:
            assert len(raw.encode()) == case['expectedBytes'], case['id']
        frame = {'contractVersion':'1','origin':case['origin'],'values':{'Selected':'ok','Unselected':raw},'research':None}
        if case['origin']=='generated':
            frame['research']={'recordRecipeRevision':'recipe:1','declaration':None,'fields':{}}
        requests.append({'rule':{'contractVersion':'1','column':'Selected','kind':'text'},'frame':frame,'profile':case.get('profile','base')})
        expected.append(case['expected'])
        # Schema bounds count characters; byte overflow with fewer Unicode characters
        # remains a semantic reader refusal, not a false schema byte-limit claim.
        structural = len(raw) <= (16000 if case['origin']=='asserted' else 524288)
        assert VALIDATOR.is_valid(frame) == structural, ('raw-value-schema', case['id'])
    projection = copy.deepcopy(EXAMPLES['producerConsistency']['expected']['projection'])
    projection_schema = jsonschema.Draft202012Validator({'$ref':'#/$defs/deskSnapshotProjection','$defs':SCHEMA['$defs']})
    for size in (524288,524289):
        fragment=copy.deepcopy(projection);fragment['values']['Independent']='x'*size
        assert projection_schema.is_valid(fragment) == (size==524288), ('independent-projection-schema',size)
    # A handwritten legal grammar/consistency witness, not a real history claim:
    # the long unselected display value is preserved beside all eight original types.
    base=copy.deepcopy(EXAMPLES['producerConsistency'])
    body=base['request']['generatedConsistency'];carrier=body['carrier']
    display=compact(['x'*1000]*16);assert len(display.encode())==16049
    original=carrier['originalSnapshotJson'];assert original.count('"List":"[]"')==1
    original=original.replace('"List":"[]"','"List":'+compact(display))
    carrier['retained']['values']['List']=display
    want=base['expected'];want['projection']['values']['List']=display
    frame_digest=digest(compact(carrier['retained']));want['frameSha256']=frame_digest
    want['transformation']['input']['ref']['frameSha256']=frame_digest
    for size in (None,524288,524289):
        request=copy.deepcopy(base['request']);c=request['generatedConsistency']['carrier']
        snapshot=original
        if size is not None:
            prefix=snapshot[:-1]+',"opaquePadding":"';snapshot=prefix+'x'*(size-len(prefix.encode())-2)+'"}'
            assert len(snapshot.encode())==size
        c['originalSnapshotJson']=snapshot;c['originalSnapshotSha256']=digest(snapshot)
        request['generatedConsistency']['receiptResultDigest']=digest(compact(c))
        answer=copy.deepcopy(want);answer['originalSnapshotSha256']=digest(snapshot)
        if size==524289:answer={'refusal':'input-over-bound'}
        requests.append(request);expected.append(answer)
    payload=''.join(compact(request)+'\n' for request in requests).encode()
    commands=[[sys.executable,'-B',str(ROOT/'tools/_retained_column.py')],
              [os.environ.get('RFC0029_NODE','node'),str(ROOT/'tools/dialect-verify-ts/src/retained-engine.mjs')]]
    for command in commands:
        result=subprocess.run(command,input=payload,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        assert result.returncode==0,(command[-1],result.stderr.decode()[-1500:])
        outputs=[json.loads(line) for line in result.stdout.splitlines()]
        assert len(outputs)==len(expected),(command[-1],len(outputs),len(expected))
        for index,(actual,want) in enumerate(zip(outputs,expected)):
            assert actual==want,(Path(command[-1]).name,'raw-value-row',index,actual if 'refusal' in actual else 'unexpected successful result',want if 'refusal' in want else 'expected handwritten positive')
        print(f'{Path(command[-1]).name}: {len(DATA["rawValueBounds"])} origin/UTF8/frame bounds + 3 complete snapshot/projection cases PASS')
    print('Raw-value schema: origin-specific scalar bounds and independent projection 524288/524289 PASS')
    print('Scope: frame/projection APIs and explicit joint snapshot checks; no independently realizable maximum value inside the fixed snapshot, Extended preparation, producer/history authority or full compatibility proof claimed.')


def check_interfaces():
    """Focused changed-contract fixtures; old conversion corpus remains a separate gate."""
    cases = DATA['interfaceCases']
    commands = [[sys.executable, '-B', str(ROOT/'tools/_retained_column.py')],
                [os.environ.get('RFC0029_NODE', 'node'), str(ROOT/'tools/dialect-verify-ts/src/retained-engine.mjs')]]
    encode = lambda value: (json.dumps(value, ensure_ascii=True, separators=(',', ':'))+'\n').encode()
    payload = b''.join(encode(c['request']) for c in cases)
    # Duplicate decoded outer names are a parser check, not a JSON Schema assertion.
    duplicate = b'{"restore":{},"restore":{},"profile":"base","limits":{}}\n'
    numeric_base = next(c['request'] for c in cases if c['id']=='admission-preview-base')
    numeric_wire = encode(numeric_base)
    lexical_refusals = [
        numeric_wire.replace(b'6291456', b'6.291456e6', 1),
        numeric_wire.replace(b'6291456', b'6291456.0', 1),
        numeric_wire.replace(b'6291456', b'9'*4301, 1),
    ]
    carrier = EXAMPLES['generatedCarrier']
    VALIDATOR.validate(carrier)
    VALIDATOR.validate(EXAMPLES['capabilitiesFragment'])
    for key in ('originalSnapshotJson', 'originalSnapshotSha256', 'retained', 'contractVersion'):
        bad = copy.deepcopy(carrier); del bad[key]
        assert not VALIDATOR.is_valid(bad), ('carrier-required', key)
    bad = copy.deepcopy(carrier); bad['originalSnapshotJson'] = {}
    assert not VALIDATOR.is_valid(bad), 'carrier-object-embedding'
    bad = copy.deepcopy(carrier); bad['extra'] = 0
    assert not VALIDATOR.is_valid(bad), 'carrier-extra'
    # Positive structural fixtures carry each new member, role and profile alternative.
    fragments = [carrier, EXAMPLES['capabilitiesFragment']]
    mutations = 0
    for definition in ('generatedCarrier', 'specIdentity', 'conversionCapability', 'capabilities'):
        def visit(value, path):
            nonlocal mutations
            if isinstance(value, dict):
                if value.get('additionalProperties') is False:
                    for member in value.get('properties', {}):
                        changed = copy.deepcopy(SCHEMA); node = changed['$defs'][definition]
                        for token in path:
                            node = node[token]
                        del node['properties'][member]
                        validator = jsonschema.Draft202012Validator(changed)
                        assert any(not validator.is_valid(f) for f in fragments), (definition, path, member)
                        mutations += 1
                if 'enum' in value:
                    for option in value['enum']:
                        changed = copy.deepcopy(SCHEMA); node = changed['$defs'][definition]
                        for token in path:
                            node = node[token]
                        node['enum'] = [x for x in value['enum'] if x != option]
                        validator = jsonschema.Draft202012Validator(changed)
                        assert any(not validator.is_valid(f) for f in fragments), (definition, path, option)
                        mutations += 1
                if 'const' in value:
                    changed = copy.deepcopy(SCHEMA); node = changed['$defs'][definition]
                    for token in path:
                        node = node[token]
                    node['const'] = '__removed_draft_alternative__'
                    validator = jsonschema.Draft202012Validator(changed)
                    assert any(not validator.is_valid(f) for f in fragments), (definition, path, 'const')
                    mutations += 1
                for key, child in value.items():
                    visit(child, path+[key])
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    visit(child, path+[index])
        visit(SCHEMA['$defs'][definition], [])
    # Asserted append keeps every original member and sibling, including originalValues.
    appended = copy.deepcopy(EXAMPLES['assertedAppendAfter'])
    frame = appended.pop('retained')
    assert appended == EXAMPLES['assertedAppendBefore']
    VALIDATOR.validate(frame)
    generated_before = copy.deepcopy(EXAMPLES['generatedReplaceBefore'])
    generated_after = copy.deepcopy(EXAMPLES['generatedReplaceAfter'])
    original_result = generated_before.pop('resultJson')
    replacement = json.loads(generated_after.pop('resultJson'))
    assert generated_before == generated_after
    assert replacement['originalSnapshotJson'] == original_result
    VALIDATOR.validate(replacement)
    pub = EXAMPLES['publicationBindingExample']
    import hashlib
    for kind in ('published', 'bound'):
        raw = pub[kind+'DocumentJson'].encode()
        assert 'sha256:'+hashlib.sha256(raw).hexdigest() == pub[kind+'DocumentSha256']
    assert pub['publishedDocumentSha256'] != pub['boundDocumentSha256']
    counted_document_bytes = sum(len(pub[k+'DocumentJson'].encode()) for k in ('published', 'bound'))
    assert counted_document_bytes == 68  # Both complete retained serialized documents count.
    # Opaque raw and decoded identity differ: these spellings can decode alike and hash differently.
    by_id = {c['id']: c for c in cases}
    a = by_id['carrier-exponent-escaped']['expected']
    b = by_id['carrier-integer-unicode']['expected']
    assert json.loads(a['originalSnapshotJson']) == json.loads(b['originalSnapshotJson'])
    assert a['originalSnapshotSha256'] != b['originalSnapshotSha256']
    zero = by_id['carrier-negative-zero']['expected']; positive = by_id['carrier-positive-zero']['expected']
    assert json.loads(zero['originalSnapshotJson']) == json.loads(positive['originalSnapshotJson'])
    assert zero['originalSnapshotSha256'] != positive['originalSnapshotSha256']
    admission_cases = [c for c in cases if 'admission' in c['request']]
    removal = [
        ('raw-snapshot-identity', 'carrier-exponent-escaped',
         "'originalSnapshotJson': snapshot, 'originalSnapshotSha256': digest(snapshot)",
         "'originalSnapshotJson': snapshot.replace('1e3', '1000'), 'originalSnapshotSha256': digest(snapshot)",
         'originalSnapshotJson:c.originalSnapshotJson,originalSnapshotSha256:digest(c.originalSnapshotJson)',
         "originalSnapshotJson:c.originalSnapshotJson.replace('1e3','1000'),originalSnapshotSha256:digest(c.originalSnapshotJson)"),
        ('snapshot-digest', 'carrier-digest',
         "if carrier['originalSnapshotSha256'] != digest(snapshot):", 'if False:',
         'if (c.originalSnapshotSha256!==digest(c.originalSnapshotJson))', 'if (false)'),
        ('capability-exact-identity', 'admission-identity-revision',
         "if all(entry[k] == required[k] for k in ('contract', 'spec', 'profile', 'role')):", 'if True:',
         'if (id===identity(r)) selected=e;', 'if (true) selected=e;'),
        ('lower-supported-limit', 'admission-weak-limit',
         "min(positive(required['limits'][key]), positive(selected['limits'][key]))",
         "max(positive(required['limits'][key]), positive(selected['limits'][key]))",
         'a>(x<y ? x : y)', 'a>(x>y ? x : y)'),
        ('original-declaration-revision', 'original-revision-mismatch',
         "declaration['recipeRevision'] != research['recordRecipeRevision']", 'False',
         'd.recipeRevision!==r.recordRecipeRevision', 'false'),
        ('lineage-reference-location', 'lineage-original-revision7',
         "'location':'research-value'", "'location':'values'",
         "location:'research-value'", "location:'values'")
    ]
    for command in commands:
        name = Path(command[-1]).name
        done = subprocess.run(command, input=payload+duplicate+b''.join(lexical_refusals), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        assert done.returncode == 0, (name, done.stderr.decode()[:1500])
        outputs = [json.loads(line) for line in done.stdout.splitlines()]
        assert len(outputs) == len(cases)+1+len(lexical_refusals), (name, len(outputs), len(cases)+1+len(lexical_refusals))
        for c, got in zip(cases, outputs):
            assert got == c['expected'], (name, c['id'], got, c['expected'])
        for got in outputs[len(cases):]:
            assert got == {'refusal':'input-malformed'}, (name, 'duplicate-members-or-limit-token', got)
        source = Path(command[-1]).read_text()
        # Call the actual admission helper with a counter callback, including every refusal.
        if name.endswith('.py'):
            instrument = source[:source.index("if __name__ == '__main__':")] + '''
for line in sys.stdin:
    effects = []
    try:
        answer = admit(parse(line)['admission'], lambda: effects.append('called'))
    except Refusal as exc:
        answer = {'refusal': str(exc)}
    print(json.dumps({'answer': answer, 'effects': len(effects)}))
'''
            invocation = [command[0], '-B', '-c', instrument]
        else:
            instrument = source[:source.index('// Fatal UTF8')] + '''
let input=''; for await (const chunk of process.stdin) input+=chunk;
for (const line of input.trimEnd().split('\\n')) {
  let effects=0, answer;
  try { answer=admit(parse(line).admission,()=>effects++); }
  catch (e) { if (!(e instanceof Refusal)) throw e; answer={refusal:e.message}; }
  process.stdout.write(JSON.stringify({answer,effects})+'\\n');
}
'''
            invocation = [command[0], '--input-type=module', '-e', instrument]
        counted = subprocess.run(invocation, input=b''.join(encode(c['request']) for c in admission_cases), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        assert counted.returncode == 0, (name, 'callback setup', counted.stderr.decode()[:500])
        rows = [json.loads(line) for line in counted.stdout.splitlines()]
        assert len(rows) == len(admission_cases)
        for case, got in zip(admission_cases, rows):
            assert got == {'answer':case['expected'], 'effects':int(case['expected'].get('admitted', False))}, (name, case['id'], got)
        for title, label, py_before, py_after, js_before, js_after in removal:
            before, after = (py_before, py_after) if name.endswith('.py') else (js_before, js_after)
            assert source.count(before) == 1, (name, title, 'mutation target')
            changed = source.replace(before, after)
            invocation = [command[0], '-B', '-c', changed] if name.endswith('.py') else [command[0], '--input-type=module', '-e', executable_probe(changed)]
            case = by_id[label]
            result = subprocess.run(invocation, input=encode(case['request']), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            assert result.returncode == 0, (name, title, 'mutation setup', result.stderr.decode()[:500])
            got = json.loads(result.stdout)
            assert got != case['expected'], (name, title, 'intended contract assertion did not fail')
            print(f'{name}: removal {title} detected at {label} expected={json.dumps(case["expected"], ensure_ascii=True, separators=(",", ":"))} got={json.dumps(got, ensure_ascii=True, separators=(",", ":"))}')
        print(f'{name}: {len(cases)} changed-interface fixtures + duplicate-name/3 limit-token refusals + {len(admission_cases)} callback-order probes + {len(removal)} safeguard-removal probes PASS')
    print(f'Draft carrier/capability schema: {mutations} member/alternative-removal controls PASS')
    print('Scope: exact UTF8 restoration, original declarations, reference lineage and Draft capability admission only; no producer, preparation, independent-authorship or adopted-limit claim.')




def expand_producer_case(row):
    """Apply literal fixture patches; never derive expectations with a reader."""
    case = copy.deepcopy(EXAMPLES['producerConsistency'])
    case['id'] = row['id']
    for member in ('request', 'expected'):
        if member in row:
            case[member] = copy.deepcopy(row[member])
        for edit in row.get(member+'Patch', []):
            parent = case[member]
            for token in edit['path'][:-1]:
                parent = parent[token]
            key = edit['path'][-1]
            if edit.get('remove'):
                del parent[key]
            else:
                parent[key] = copy.deepcopy(edit['value'])
    if 'wireJson' in row:
        case['wireJson'] = row['wireJson']
    return case


def check_inventory():
    """Producer-specific relation only; trust/signature/history are explicit seams."""
    cases = [expand_producer_case(c) for c in DATA['producerCases']]
    # Handwritten fixed producer-bound recipes; generic requested limits cannot
    # enlarge the pinned old snapshot ceiling. No reader output is recorded.
    import hashlib
    baseline = next(c for c in cases if c['id']=='producer-original-type-text')
    for size in (524288, 524289):
        c = copy.deepcopy(baseline)
        c['id'] = 'producer-original-snapshot-bytes-'+str(size)
        body = c['request']['generatedConsistency']
        old = body['carrier']['originalSnapshotJson']
        prefix = old[:-1]+',"opaquePadding":"'
        snapshot = prefix+'x'*(size-len(prefix.encode())-2)+'"}'
        assert len(snapshot.encode())==size
        body['carrier']['originalSnapshotJson'] = snapshot
        pin = 'sha256:'+hashlib.sha256(snapshot.encode()).hexdigest()
        body['carrier']['originalSnapshotSha256'] = pin
        body['receiptResultDigest'] = 'sha256:'+hashlib.sha256(json.dumps(body['carrier'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        body['limits']['originalSnapshotBytes'] = 524289
        c['expected']['originalSnapshotSha256'] = pin
        if size>524288:
            c['expected'] = {'refusal':'input-over-bound'}
        cases.append(c)
    encode = lambda c: ((c.get('wireJson') or json.dumps(c['request'], ensure_ascii=True, separators=(',', ':'))) + '\n').encode()
    fragments = [EXAMPLES['producerGrammarBinding'], EXAMPLES['producerGrammarBinding']['retainedColumnProducer']]
    for case in cases:
        if case['expected'].get('consistent'):
            VALIDATOR.validate(case['request'])
            VALIDATOR.validate(case['expected'])
            fragments.extend([case['request'], case['expected']])
    controls = 0
    definitions = ('retainedColumnProducer', 'trustedProducerProjection', 'producerSourceBinding',
                   'deskSnapshotProjection', 'previewAvailability', 'generatedConsistencyBody',
                   'generatedConsistencyRequest', 'generatedConsistencyResult')
    for definition in definitions:
        def visit(value, path):
            nonlocal controls
            if isinstance(value, dict):
                alterations = []
                if value.get('additionalProperties') is False:
                    alterations += [('member', key) for key in value.get('properties', {})]
                alterations += [('enum', item) for item in value.get('enum', [])]
                if 'const' in value:
                    alterations.append(('const', None))
                for kind, member in alterations:
                    changed = copy.deepcopy(SCHEMA)
                    node = changed['$defs'][definition]
                    for token in path:
                        node = node[token]
                    if kind == 'member':
                        del node['properties'][member]
                    elif kind == 'enum':
                        node['enum'] = [x for x in node['enum'] if x != member]
                    else:
                        node['const'] = '__removed_draft_alternative__'
                    validator = jsonschema.Draft202012Validator(changed)
                    assert any(not validator.is_valid(f) for f in fragments), (definition, path, kind, member)
                    controls += 1
                for key, child in value.items():
                    visit(child, path+[key])
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    visit(child, path+[index])
        visit(SCHEMA['$defs'][definition], [])
    mutations = [
        ('complete-unselected-inventory', 'producer-omitted-unselected-declaration',
         "research['declaration']['fields'] != source['declarations']", 'False',
         '!equal(research.declaration.fields,source.declarations)', 'false'),
        ('raw-unfiltered-values', 'producer-filtered-values-substitution',
         "frame['values'] != source['values']", 'False',
         '!equal(f.values,source.values)', 'false'),
        ('exact-typed-source', 'producer-zero-spelling-changed',
         "research['fields'] != source['fields']", 'False',
         '!equal(research.fields,source.fields)', 'false'),
        ('trusted-source', 'producer-wrong-trusted-source',
         "trust['source'] != 'desk-inputs'", 'False',
         "t.source!=='desk-inputs'", 'false'),
        ('new-pinned-adapter', 'producer-old-adapter',
         "trust['adapter']['version'] != '2'", 'False',
         "t.adapter.version!=='2'", 'false'),
        ('existing-receipt-result-domain', 'producer-updated-frame-old-receipt',
         "if probe['receiptResultDigest'] != digest(carrier_canon(probe['carrier'])):", 'if False:',
         "if (p.receiptResultDigest!==digest(carrierCanon(p.carrier)))", 'if (false)'),
        ('revision-domain', 'producer-original-type-text',
         "REVISION_DOMAIN + run_id + '\\0' + str(version)", "run_id + '\\0' + str(version)",
         "REVISION_DOMAIN+id+'\\0'+String(positive(version))", "id+'\\0'+String(positive(version))"),
        ('original-record-run-revision', 'producer-record-original-revision-mismatch',
         'if revision != other:', 'if False:',
         'if (revision!==other)', 'if (false)'),
        ('original-frame-revision', 'producer-current-both-frame-revisions',
         "if (research['recordRecipeRevision'], research['declaration']['recipeRevision']) != (revision, revision):", 'if False:',
         'if (!equal([research.recordRecipeRevision,research.declaration.recipeRevision],[revision,revision]))', 'if (false)'),
        ('fixed-original-snapshot-bound', 'producer-original-snapshot-bytes-524289',
         'if length(snapshot) > 524288:', 'if False:',
         'if (bytes(snapshot)>524288)', 'if (false)'),
        ('raw-frame-identity', 'producer-escaped-frame-identity',
         "digest(source_member(carrier_text, 'retained'))", 'digest(carrier_canon(frame))',
         'frameSha256:digest(f[RAW_TOKEN])', 'frameSha256:digest(carrierCanon(f))'),
        ('no-history-authority-claim', 'producer-original-type-text',
         "'history':'not-checked'", "'history':'checked'",
         "history:'not-checked'", "history:'checked'"),
    ]
    commands = [[sys.executable, '-B', str(ROOT/'tools/_retained_column.py')],
                [os.environ.get('RFC0029_NODE', 'node'), str(ROOT/'tools/dialect-verify-ts/src/retained-engine.mjs')]]
    by_id = {c['id']:c for c in cases}
    for command in commands:
        name = Path(command[-1]).name
        result = subprocess.run(command, input=b''.join(map(encode, cases)), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        assert result.returncode == 0, (name, 'producer cases setup', result.stderr.decode()[:2000])
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        assert len(rows) == len(cases), (name, 'producer case count', len(rows), len(cases))
        for case, actual in zip(cases, rows):
            assert actual == case['expected'], (name, case['id'], actual, case['expected'])
        source = Path(command[-1]).read_text()
        for label, case_id, py_before, py_after, js_before, js_after in mutations:
            before, after = (py_before, py_after) if name.endswith('.py') else (js_before, js_after)
            assert source.count(before) == 1, (name, label, 'removal target', source.count(before))
            changed = source.replace(before, after, 1)
            invoke = [command[0], '-B', '-c', changed] if name.endswith('.py') else [command[0], '--input-type=module', '-e', executable_probe(changed)]
            case = by_id[case_id]
            removed = subprocess.run(invoke, input=encode(case), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            assert removed.returncode == 0, (name, label, 'invalid setup', removed.stderr.decode()[:1000])
            actual = json.loads(removed.stdout)
            assert actual != case['expected'], (name, label, 'intended assertion did not fail')
            print(f'{name}: producer removal {label} detected at {case_id}')
        print(f'{name}: {len(cases)} producer relation/identity cases + {len(mutations)} intended removals PASS')
    print(f'Draft producer projection schema: {controls} member/alternative-removal controls PASS')
    print('Scope: snapshot/frame consistency and portable identities only; acquisition:not-verified, history:not-checked; no producer, preparation or adoption evidence.')

def check_references(replay_changed_outputs=True, schema_only=False):
    """Only changed reference/custody behavior; reuse unchanged guard evidence."""
    cases = list(DATA['referenceCases'])
    if replay_changed_outputs:
        cases += [c for c in DATA['interfaceCases'] if 'lineage' in c['request']]
    # Generated consistency outputs now contain references; exercise their exact
    # handwritten corpus without repeating its unchanged guard-removal matrix.
    if replay_changed_outputs:
        cases += [expand_producer_case(c) for c in DATA['producerCases']]
    encode = lambda c: ((c.get('wireJson') or json.dumps(c['request'], ensure_ascii=True, separators=(',', ':'))) + '\n').encode()
    fragments = [EXAMPLES[k] for k in ('lineageFragment', 'preparationSourceFragment', 'retainedSourceFragment', 'assertedCaseCustodyFragment')]
    # Schema coverage must not depend on replaying producer-reader outputs.
    fragments.append(EXAMPLES['producerConsistency']['expected']['transformation'])
    fragments += [c['expected'] for c in cases if 'input' in c['expected']]
    fragments.append({'case':{'retained':EXAMPLES['assertedFrame']}})
    for c in DATA['referenceCases']:
        if 'refusal' not in c['expected']:
            for probe in ('retainSource','retainCase'):
                if probe in c['request']:
                    VALIDATOR.validate(c['request'][probe]['source'])
                    VALIDATOR.validate(c['expected'])
    for f in fragments:
        VALIDATOR.validate(f)
    # Closed input/retention alternatives have positive carriers for every new
    # member/enum, including missing and both reference locations.
    missing = {'contractVersion':'1','column':'A','input':{'state':'missing'},'result':{'state':'omitted','reason':'missing'}}
    fragments.append(missing)
    controls = 0
    for definition in ('inputReference', 'input', 'preparationSource', 'assertedCaseCustody', 'signedResponseFragment'):
        def visit(value, path):
            nonlocal controls
            if isinstance(value, dict):
                changes=[]
                if value.get('additionalProperties') is False:
                    changes += [('member', k) for k in value.get('properties', {})]
                changes += [('enum', v) for v in value.get('enum', [])]
                if 'const' in value:
                    changes.append(('const', None))
                for kind,key in changes:
                    changed=copy.deepcopy(SCHEMA); node=changed['$defs'][definition]
                    for token in path: node=node[token]
                    if kind=='member': del node['properties'][key]
                    elif kind=='enum': node['enum']=[v for v in node['enum'] if v!=key]
                    else: node['const']='__removed_draft_alternative__'
                    validator=jsonschema.Draft202012Validator(changed)
                    assert any(not validator.is_valid(f) for f in fragments), (definition,path,kind,key)
                    controls += 1
                for key,child in value.items():visit(child,path+[key])
            elif isinstance(value,list):
                for index,child in enumerate(value):visit(child,path+[index])
        visit(SCHEMA['$defs'][definition], [])
    if schema_only:
        print(f'Draft reference/source schema: {controls} existing member/alternative controls PASS')
        return
    by_id={c['id']:c for c in cases}
    # Changed safeguards only: exact raw digest, full fragment verification,
    # sole response/case source, exact-text return. Both readers must miss the
    # intended assertion when that guard is removed; setup errors do not count.
    removals=[
      ('raw-frame-custody','reference-exact-raw-frame',
       'frame_digest = digest(raw_frame_text)', 'frame_digest = digest(json.dumps(frame, ensure_ascii=True, separators=(\',\', \':\')))',
       'const frameDigest=digest(f[RAW_TOKEN]);', 'const frameDigest=digest(JSON.stringify(f));'),
      ('complete-reference-recomputation','reference-wrong-location',
       "if probe['transformation'] != expected:", 'if False:',
       "if (!same(transformation,expected)) fail('read-failed');", 'if (false) fail(\'read-failed\');'),
      ('sole-response-text','retainSource-dual',
       "closed(source, ['retainedResponseJson'])", "closed(source, ['retainedResponseJson'], ['response'])",
       "closed(s,['retainedResponseJson']);", "closed(s,['retainedResponseJson'],['response']);"),
      ('sole-case-text','retainCase-dual',
       "closed(source, ['retainedCaseJson'])", "closed(source, ['retainedCaseJson'], ['case'])",
       "closed(s,['retainedCaseJson']);", "closed(s,['retainedCaseJson'],['case']);"),
      ('exact-case-custody','case-sole-text',
       "return {'retainedCaseJson':text}", "return {'retainedCaseJson':json.dumps(parse(text, strict=False), default=lambda v: v.text, separators=(',', ':'))}",
       "return {retainedCaseJson:text};", "return {retainedCaseJson:JSON.stringify(parse(text,{strict:false}))};"),
      ('exact-response-custody','source-sole-text',
       "return {'retainedResponseJson':envelope}", "return {'retainedResponseJson':json.dumps(parsed, default=lambda v: v.text, separators=(',', ':'))}",
       "return {retainedResponseJson:envelope};", "return {retainedResponseJson:JSON.stringify(parsed)};")
    ]
    for command in ([sys.executable,'-B',str(ROOT/'tools/_retained_column.py')], [os.environ.get('RFC0029_NODE','node'),str(ROOT/'tools/dialect-verify-ts/src/retained-engine.mjs')]):
        name=Path(command[-1]).name
        done=subprocess.run(command,input=b''.join(encode(c) for c in cases),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        assert done.returncode==0,(name,done.stderr.decode()[:1000])
        outputs=[json.loads(line) for line in done.stdout.splitlines()]
        assert len(outputs)==len(cases),(name,len(outputs),len(cases))
        for c,got in zip(cases,outputs):assert got==c['expected'],(name,c['id'],got,c['expected'])
        source=Path(command[-1]).read_text()
        for title,label,pb,pa,jb,ja in removals:
            before,after=(pb,pa) if name.endswith('.py') else (jb,ja)
            assert source.count(before)==1,(name,title,'mutation target')
            changed=source.replace(before,after)
            invocation=[command[0],'-B','-c',changed] if name.endswith('.py') else [command[0],'--input-type=module','-e',executable_probe(changed)]
            result=subprocess.run(invocation,input=encode(by_id[label]),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
            assert result.returncode==0,(name,title,'setup',result.stderr.decode()[:500])
            got=json.loads(result.stdout)
            assert got!=by_id[label]['expected'],(name,title,'intended assertion did not fail')
            print(f'{name}: changed safeguard {title} detected at {label} expected={json.dumps(by_id[label]["expected"],ensure_ascii=True,separators=(",",":"))} removedGot={json.dumps(got,ensure_ascii=True,separators=(",",":"))}')
        print(f'{name}: {len(cases)} reference/custody/changed-output cases + {len(removals)} intended removals PASS')
    # Serialization-layer accounting for the two exact handwritten source texts.
    # These are encoder-specific fixture measurements, never global maxima.
    for label,key in [('source-sole-text','retainedResponseJson'),('case-sole-text','retainedCaseJson')]:
        text=by_id[label]['expected'][key]
        q=lambda value:json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
        raw=len(text.encode());quoted=len(q(text));slot=len(q({key:text}));outer=len(q({'source':{key:text},'sibling':{'kept':True}}))
        # Independent lexical charges for this pinned literal-UTF8 encoder.
        extra=sum(1 if c in '\b\t\n\f\r' else 5 for c in text if ord(c)<32)
        assert quoted==raw+2+text.count(chr(34))+text.count(chr(92))+extra
        assert slot==quoted+len(q(key))+3  # braces and colon
        assert outer==slot+35  # exact source key + kept sibling/container
        assert quoted>raw and slot>quoted and outer>slot
        print(f'fixture {key}: raw={raw} quoted={quoted} custody-slot={slot} complete-test-envelope-with-sibling={outer}')
    print(f'Draft reference/source schema: {controls} changed member/alternative controls PASS')
    print('Scope: Draft fragments, raw custody, source union and local reference consistency; no source authentication, complete preparation maxima, production support or adoption claim.')


def check_limits(selector_types_only=False):
    """Selected Draft caps/selector only; no repeated conversion or producer checks."""
    cases = DATA['capCases'] + [c for c in DATA['interfaceCases'] if 'admission' in c['request']]
    type_cases = [c for c in DATA['capCases'] if c['id'].startswith('selection-profile-type-')]
    for case in type_cases:
        assert not VALIDATOR.is_valid(case['request']['selection']['selector']), ('selector-profile-schema', case['id'])
    if selector_types_only:
        following = next(c for c in DATA['capCases'] if c['id'] == 'selection-preparation-only')
        # Each malformed request is followed by a known valid request in the same process.
        cases = [entry for case in type_cases for entry in (case, following)]
    by_id = {c['id']: c for c in cases}
    encode = lambda v: (json.dumps(v, ensure_ascii=True, separators=(',', ':'))+'\n').encode()
    commands = [[sys.executable, '-B', str(ROOT/'tools/_retained_column.py')],
                [os.environ.get('RFC0029_NODE', 'node'), str(ROOT/'tools/dialect-verify-ts/src/retained-engine.mjs')]]
    VALIDATOR.validate(EXAMPLES['selectionFragment'])
    VALIDATOR.validate(EXAMPLES['capabilitiesFragment'])
    # Every added limit member and selector field/enum must be carried by positive fixtures.
    fragments = [EXAMPLES['selectionFragment'], EXAMPLES['capabilitiesFragment']] + [c['request']['selection']['selector'] for c in DATA['capCases'] if c['expected'].get('selected')]
    controls = 0
    def remove_controls(definition, node, path=()):
        nonlocal controls
        if isinstance(node, dict):
            candidates = [('properties', k) for k in node.get('properties', {})] if node.get('additionalProperties') is False else []
            candidates += [('enum', k) for k in node.get('enum', [])]
            for kind, value in candidates:
                changed = copy.deepcopy(SCHEMA); at = changed['$defs'][definition]
                for part in path: at = at[part]
                if kind == 'properties': del at[kind][value]
                else: at[kind] = [x for x in at[kind] if x != value]
                assert any(not jsonschema.Draft202012Validator(changed).is_valid(f) for f in fragments), (definition, path, kind, value)
                controls += 1
            for key, child in node.items(): remove_controls(definition, child, path+(key,))
        elif isinstance(node, list):
            for i, child in enumerate(node): remove_controls(definition, child, path+(i,))
    if not selector_types_only:
        for definition in ('selection', 'conversionCapability'): remove_controls(definition, SCHEMA['$defs'][definition])
    mutations = [
        ('installed-identity', 'caps-untrusted-agreement-revision',
         "if required['spec'] != INSTALLED_SPEC:", 'if False:',
         "if (!installedSpec(r.spec))", 'if (false)'),
        ('selected-profile-ceiling', 'caps-reported-capacity-does-not-raise-profile',
         "if actual > PROFILE_CAPS[required['profile']][key]:", 'if False:',
         'if (a>BigInt(PROFILE_CAPS[r.profile][k]))', 'if (false)'),
        ('prebody-installed-identity', 'selection-untrusted-revision',
         "s['spec'] != INSTALLED_SPEC", 'False',
         '!installedSpec(s.spec)', 'false'),
        ('selected-endpoint-role', 'selection-missing-required-role',
         "if not isinstance(probe['role'], str) or probe['role'] not in s['roles']:", 'if False:',
         "if (typeof p.role!=='string' || !s.roles.includes(p.role))", 'if (false)'),
        ('canonical-role-order', 'selection-order',
         "s['roles'] != [r for r in order if r in s['roles']]", 'False',
         'JSON.stringify(s.roles)!==JSON.stringify(order.filter(r=>s.roles.includes(r)))', 'false'),
        ('selector-closed-shape', 'selection-limits-forbidden',
         "closed(s, ['contract', 'spec', 'profile', 'roles'])", "closed(s, ['contract', 'spec', 'profile', 'roles'], ['limits'])",
         "closed(s,['contract','spec','profile','roles'])", "closed(s,['contract','spec','profile','roles'],['limits'])")
    ]
    for command in commands:
        name=Path(command[-1]).name; source=Path(command[-1]).read_text()
        result=subprocess.run(command,input=b''.join(encode(c['request']) for c in cases),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
        assert result.returncode == 0, (name, result.stderr.decode()[:500])
        rows=[json.loads(line) for line in result.stdout.splitlines()]
        assert len(rows)==len(cases), (name, len(rows),len(cases))
        for case, got in zip(cases,rows): assert got==case['expected'], (name,case['id'],got,case['expected'])
        # Real admission/selection functions with instrumented effect seams. The endpoint role
        # argument models trusted route metadata, never capability bytes in the larger body.
        if name.endswith('.py'):
            instrument=source[:source.index("if __name__ == '__main__':")]+'''
for line in sys.stdin:
    effects=[]
    try:
        r=parse(line)
        answer=admit(r['admission'],lambda: effects.append(1)) if 'admission' in r else select(r['selection'],lambda: effects.append(1))
    except Refusal as exc: answer={'refusal':str(exc)}
    print(json.dumps({'answer':answer,'effects':len(effects)}))
'''
            invocation=[command[0],'-B','-c',instrument]
        else:
            instrument=source[:source.index('// Fatal UTF8')]+'''
let input=''; for await(const chunk of process.stdin) input+=chunk;
for(const line of input.trimEnd().split('\\n')) {
 let effects=0,answer;
 try { const r=parse(line); answer=Object.hasOwn(r,'admission') ? admit(r.admission,()=>effects++) : select(r.selection,()=>effects++); }
 catch(e) { if(!(e instanceof Refusal)) throw e; answer={refusal:e.message}; }
 process.stdout.write(JSON.stringify({answer,effects})+'\\n');
}
'''
            invocation=[command[0],'--input-type=module','-e',instrument]
        result=subprocess.run(invocation,input=b''.join(encode(c['request']) for c in cases),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
        assert result.returncode==0,(name,'callback setup',result.stderr.decode()[:500])
        rows=[json.loads(line) for line in result.stdout.splitlines()]
        assert len(rows)==len(cases)
        for case,got in zip(cases,rows):
            expected=case['expected']; effects=int(expected.get('admitted',False) or expected.get('selected',False))
            assert got=={'answer':expected,'effects':effects},(name,case['id'],'effect order',got)
        active_mutations = [] if selector_types_only else list(mutations)
        if name.endswith('.mjs'):
            active_mutations.append(('selector-profile-string-guard', 'selection-profile-type-array-base',
                                     '', '', "typeof s.profile!=='string' || ", ''))
        for label, case_id, py_before, py_after, js_before, js_after in active_mutations:
            before,after=(py_before,py_after) if name.endswith('.py') else (js_before,js_after)
            assert source.count(before)==1,(name,label,'mutation target')
            changed=source.replace(before,after)
            invocation=[command[0],'-B','-c',changed] if name.endswith('.py') else [command[0],'--input-type=module','-e',executable_probe(changed)]
            case=by_id[case_id]
            result=subprocess.run(invocation,input=encode(case['request']),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
            assert result.returncode==0,(name,label,'mutation setup',result.stderr.decode()[:500])
            got=json.loads(result.stdout)
            assert got!=case['expected'],(name,label,'intended assertion did not fail')
            print(f'{name}: removed {label} at {case_id} expected={case["expected"]} removedGot={got}')
        print(f'{name}: {len(cases)} changed cap/selector/role fixtures and callback probes; {len(active_mutations)} intended safeguard removals PASS')
    print(f'Draft selector wrong-type profiles: {len(type_cases)} schema refusals PASS')
    if not selector_types_only:
        print(f'Draft cap/selector schema: {controls} member/enum removal controls PASS')
    print('Scope: synthetic installed identity and reported-size admission only; no actual artifact boundary, supported product role, Extended support or normative adoption claim.')


if '--raw-values-only' in sys.argv:
    check_raw_values()
    sys.exit(0)


if '--selector-types-only' in sys.argv:
    check_limits(selector_types_only=True)
    sys.exit(0)


if '--limits-only' in sys.argv:
    check_limits()
    sys.exit(0)


if '--references-only' in sys.argv:
    schema_only = '--schema-only' in sys.argv
    check_references(replay_changed_outputs=not schema_only, schema_only=schema_only)
    sys.exit(0)


if '--inventory-only' in sys.argv:
    check_inventory()
    sys.exit(0)


if '--carrier-only' in sys.argv:
    check_interfaces()
    sys.exit(0)


if '--global-schema-only' not in sys.argv:
    check_raw_values()
    check_limits()

requests, expected, labels, schema_valid = [], [], [], []

def add(label,request,want):
    labels.append(label); requests.append(request); expected.append(want)


def register_case(c):
    if c.get('recordCount')==0:
        # A row-free authoring proposal is not a record conversion invocation.
        assert c['id']=='planned-research-zero-records' and c['originalDeclaration'] is None
        return
    request=fixture(c)
    want=copy.deepcopy(c.get('preview',{'issues':['research-context']}))
    if 'valueJson' in want and c['kind'] in ('text','decimal','evidence-availability'):
        # Canon JSON encoding changes string escaping only, never its value.
        want['valueJson']=json.dumps(json.loads(want['valueJson']),ensure_ascii=False,separators=(',',':'))
    want['claimAdmissible']=c.get('claimAdmissible', 'valueJson' in want and c.get('preparation')!='read-failed-no-evaluation')
    add(c['id'],request,want)
    frame=request['frame']
    schema_valid.append(frame)
    if c['kind']=='evidence-availability':
        schema_valid.append({'requirement':'receipt','source':'/retained','availability':{k:v for k,v in request['rule'].items() if k!='kind'}})
    else:
        schema_valid.append({'target':'/result','source':'/retained','conversion':request['rule']})
    if not want.get('issues'):
        result={'state':'value','json':want['valueJson']} if 'valueJson' in want else {'state':'omitted','reason':want['omitted']}
        lineage={'contractVersion':'1','column':request['rule']['column'],'input':{'state':'missing'},'result':result}
        if 'inputJson' in c:
            lineage['input']={'state':'present','ref':{'frameSha256':'sha256:'+'0'*64,'location':'research-value' if c['kind']=='research-value' else 'values'}}
        if c['kind']=='research-value':
            lineage['researchIdentity']={'recipeRevision':'recipe:1','fieldSha256':'sha256:'+'0'*64}
        schema_valid.append(lineage)


for c in DATA['cases']:
    register_case(c)
for c in DATA['boundaryCases']:
    if c.get('researchType')=='text-list':
        raw=json.dumps(['']*c['count'],separators=(',',':'))
    elif 'researchType' in c:
        raw=json.dumps(c['repeat']*c['count'])
    else:
        raw=json.dumps(c['repeat']*c['count'])
    row={'id':c['id'],'kind':'research-value' if 'researchType' in c else c['kind'],'inputJson':raw,'type':c.get('researchType'),'status':'supported'}
    row['preview']={'issues':[c['expectedIssue']]} if 'expectedIssue' in c else {'issues':[],'valueJson':raw if 'researchType' in c else json.dumps(json.loads(raw),ensure_ascii=False,separators=(',',':'))}
    register_case(row)
for c in DATA['shortestCases']:
    add(c['id'],{'binary64Hex':c['binary64Hex']},{'rational':str(Fraction(c['expectedRational']))})

base=fixture({'kind':'text','inputJson':'"x"'})
# These independently authored mutations assert structural refusal, not conversion issues.
def refused(label,mutate,code='input-malformed'):
    r=copy.deepcopy(base); mutate(r); add(label,r,{'refusal':code})
refused('unknown-rule-version',lambda r:r['rule'].update(contractVersion='2'))
refused('unknown-kind',lambda r:r['rule'].update(kind='json'))
refused('extra-rule-member',lambda r:r['rule'].update(required=True))
refused('mixed-quality-variant',lambda r:r['rule'].update(type='boolean',normalizers=[]))
refused('boolean-missing-spellings',lambda r:r['rule'].update(kind='boolean'))
refused('boolean-same-spellings',lambda r:r['rule'].update(kind='boolean',trueValue='YES',falseValue='YES'))
refused('boolean-blank-spelling',lambda r:r['rule'].update(kind='boolean',trueValue='\u0085',falseValue='NO'))
refused('boolean-spelling-over-bytes',lambda r:r['rule'].update(kind='boolean',trueValue='é'*81,falseValue='NO'),'input-over-bound')
refused('nonboolean-spellings',lambda r:r['rule'].update(trueValue='YES',falseValue='NO'))
refused('column-over-bytes',lambda r:r['rule'].update(column='é'*81),'input-over-bound')
refused('unknown-frame-version',lambda r:r['frame'].update(contractVersion='2'))
refused('extra-frame-member',lambda r:r['frame'].update(prepared={}))
refused('generated-missing-context',lambda r:r['frame'].update(origin='generated'))
refused('raw-column-wrong-type',lambda r:r['frame']['values'].update(Column=False))
refused('raw-column-over-bound',lambda r:r['frame']['values'].update(Column='x'*16001),'input-over-bound')
refused('columns-over-bound',lambda r:r['frame'].update(values={f'c{i}':'' for i in range(1001)}),'input-over-bound')
refused('unknown-profile',lambda r:r.update(profile='huge'))
refused('null-profile',lambda r:r.update(profile=None))
add('absent-profile-default',copy.deepcopy(base),{'issues':[],'valueJson':'"x"','claimAdmissible':True})

research=fixture({'kind':'research-value','type':'boolean','inputJson':'false'})
for name,mutation,code in [
 ('unknown-status',lambda r:r['frame']['research']['fields']['Column'].update(status='found'),'input-malformed'),
 ('duplicate-field-names',lambda r:r['frame']['research']['declaration']['fields'].append(copy.deepcopy(r['frame']['research']['declaration']['fields'][0])),'input-malformed'),
 ('field-json-name-mismatch',lambda r:r['frame']['research']['declaration']['fields'][0].update(fieldJson='{"name":"Other","type":"text"}'),'input-malformed'),
 ('field-json-duplicate',lambda r:r['frame']['research']['declaration']['fields'][0].update(fieldJson='{"name":"Column","name":"Column","type":"text"}'),'input-malformed'),
 ('field-json-over-bound',lambda r:r['frame']['research']['declaration']['fields'][0].update(fieldJson=' '*16385),'input-over-bound'),
]:
    r=copy.deepcopy(research);mutation(r);add(name,r,{'refusal':code})
# A malformed status must refuse its line and still process the next request.
for name,status in [('array',[]),('object',{})]:
    r=copy.deepcopy(research)
    r['frame']['research']['fields']['Column']['status']=status
    add('status-'+name,r,{'refusal':'input-malformed'})
    add('status-'+name+'-continuation',copy.deepcopy(base),{'issues':[],'valueJson':'"x"','claimAdmissible':True})
for status in ('missing','inaccessible'):
    register_case({'id':'research-status-'+status,'kind':'research-value','type':'boolean','status':status,'inputJson':'null','preview':{'omitted':'unavailable','issues':[]}})
# Original typed bound failures remain per-record issues within an inspectable frame.
for name,raw in [('legacy-string-raw-over8192',json.dumps('x'*8191)),('typed-raw-over512KiB','[]'+' '*524287)]:
    register_case({'id':name,'kind':'research-value','type':'string' if 'legacy' in name else 'text-list','status':'supported','inputJson':raw,'preview':{'issues':['research-type']}})
# 64 levels is inherited from the original duplicate reader; a depth65 scalar fails the type check.
for depth in (64,65):
    raw='['*depth+'0'+']'*depth
    register_case({'id':f'embedded-depth{depth}-invalid-type','kind':'research-value','type':'text','status':'supported','inputJson':raw,'preview':{'issues':['research-type']}})

# Handwritten boundary recipes retain the exact literals without reader-generated expectations.
for size in (1024,1025):
    raw=json.dumps(['x'*size],separators=(',',':'))
    want={'issues':[],'valueJson':raw} if size==1024 else {'issues':['research-type']}
    register_case({'id':f'list-item-bytes-{size}','kind':'research-value','type':'text-list','status':'supported','inputJson':raw,'preview':want})
for size in (8192,8193):
    raw='1'+' '*(size-1)
    want={'issues':[],'valueJson':raw} if size==8192 else {'issues':['research-type']}
    register_case({'id':f'legacy-number-raw-{size}','kind':'research-value','type':'number','status':'supported','inputJson':raw,'preview':want})
register_case({'id':'range-exact-order','kind':'research-value','type':'range','status':'supported','inputJson':'{"min":"0.1000000000000000001","max":"0.1"}','preview':{'issues':['research-type']}})

for c in map(expand_producer_case, DATA['producerCases']):
    if c['expected'].get('consistent'):
        schema_valid.extend([c['request'], c['expected']])
schema_valid.append(EXAMPLES['producerGrammarBinding'])

for value in GLOBAL_SCHEMA_EXAMPLES:
    schema_valid.append(value)
for fragment in schema_valid:
    VALIDATOR.validate(fragment)
# Schema is deliberately looser than semantic checks for byte limits and distinct spellings.
invalid_fact={'target':'/x','source':'/retained','conversion':{'contractVersion':'1','column':'X','kind':'text'},'required':True}
assert not VALIDATOR.is_valid(invalid_fact)
invalid_origin=copy.deepcopy(EXAMPLES['generatedFrame']);invalid_origin['origin']='asserted'
assert not VALIDATOR.is_valid(invalid_origin)
for bad in ['kind','contractVersion']:
    fragment=copy.deepcopy(schema_valid[1]);fragment['conversion'][bad]='unknown'
    assert not VALIDATOR.is_valid(fragment)
# Every closed enum alternative has a positive structural fixture; removing it must reject a row.
schema_valid.extend(json.loads(c['preparationJson']) for c in PREPARATIONS['cases'] if c['expected']=='reading')
enum_mutations=0
for definition in ('conversion','field','frame','result','selectedPreparation'):
    def visit(value,path):
        global enum_mutations
        if isinstance(value,dict):
            for key,child in value.items():
                if key=='enum':
                    for option in child:
                        mutated=copy.deepcopy(SCHEMA);node=mutated['$defs'][definition]
                        for token in path:node=node[token]
                        node['enum']=[x for x in child if x!=option]
                        check=jsonschema.Draft202012Validator(mutated)
                        assert any(not check.is_valid(row) for row in schema_valid), (definition,path,option)
                        enum_mutations+=1
                else:visit(child,path+[key])
        elif isinstance(value,list):
            for i,child in enumerate(value):visit(child,path+[i])
    visit(SCHEMA['$defs'][definition],[])

member_mutations=0
for definition in SCHEMA['$defs']:
    def visit_members(value,path):
        global member_mutations
        if isinstance(value,dict):
            for key,child in value.items():
                if key=='properties' and value.get('additionalProperties') is False:
                    for member in child:
                        mutated=copy.deepcopy(SCHEMA);node=mutated['$defs'][definition]
                        for token in path:node=node[token]
                        del node['properties'][member]
                        check=jsonschema.Draft202012Validator(mutated)
                        assert any(not check.is_valid(row) for row in schema_valid),(definition,path,member)
                        member_mutations+=1
                else:visit_members(child,path+[key])
        elif isinstance(value,list):
            for i,child in enumerate(value):visit_members(child,path+[i])
    visit_members(SCHEMA['$defs'][definition],[])

if '--global-schema-only' in sys.argv:
    print(f'Default global schema coverage: {enum_mutations} enum and {member_mutations} member-removal controls PASS, including signedResponseFragment.result')
    check_references(replay_changed_outputs=False, schema_only=True)
    sys.exit(0)


# Only transport-byte admission is probed here, not a complete old/new envelope comparison.
raw_at=copy.deepcopy(base)
values=raw_at['frame']['values']
for i in range(130):
    values[f'padding{i}']='x'*16000
frame_bytes=len(json.dumps(raw_at['frame'],separators=(',',':')).encode())
remaining=2097152-frame_bytes
# Add one final member whose punctuation and name overhead are counted.
values['tail']=''
overhead=len(json.dumps(raw_at['frame'],separators=(',',':')).encode())
values['tail']='x'*(2097152-overhead)
assert 0<len(values['tail'])<16000
raw_over=copy.deepcopy(raw_at);raw_over['frame']['values']['tail']+='x'
raw_escape=copy.deepcopy(base)
raw_escape['frame']['values'].update({f'padding{i}':'x'*16000 for i in range(24)})
raw_extra=[
 ('base-frame-exact-byte-limit',json.dumps(raw_at,separators=(',',':')).encode()+b'\n',{'issues':[],'valueJson':'"x"','claimAdmissible':True}),
 ('base-frame-one-byte-over',json.dumps(raw_over,separators=(',',':')).encode()+b'\n',{'refusal':'input-over-bound'}),
 ('escaped-frame-over-byte-limit',json.dumps(raw_escape,separators=(',',':')).replace('x','\\u0078').encode()+b'\n',{'refusal':'input-over-bound'})
]

payload=''.join(json.dumps(r,ensure_ascii=True,separators=(',',':'))+'\n' for r in requests).encode()
# Malformed transport checks are raw handwritten lines, separate from valid requests.
raw_cases=[
 ('utf8-bom',b'\xef\xbb\xbf'+json.dumps(base,separators=(',',':')).encode()+b'\n'),
 ('duplicate-root',b'{"rule":{},"rule":{},"frame":{}}\n'),
 ('invalid-utf8',b'{"bad":"\xff"}\n'),
 ('outer-lone-surrogate',b'{"bad":"\\ud800"}\n'),
 ('trailing-root-value',b'{} {}\n')
]
payload+=b''.join(raw for _,raw in raw_cases)
payload+=b''.join(raw for _,raw,_ in raw_extra)
commands=[[sys.executable,'-B',str(ROOT/'tools/_retained_column.py')],[os.environ.get('RFC0029_NODE','node'),str(ROOT/'tools/dialect-verify-ts/src/retained-engine.mjs')]]
for command in commands:
    done=subprocess.run(command,input=payload,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20,check=False)
    assert done.returncode==0,(Path(command[0]).name,done.stderr.decode()[:1500])
    outputs=[json.loads(line) for line in done.stdout.splitlines()]
    assert len(outputs)==len(expected)+len(raw_cases)+len(raw_extra),(len(outputs),len(expected)+len(raw_cases)+len(raw_extra))
    for label,want,got in zip(labels,expected,outputs):
        assert got==want,(label,got,want)
    for (label,_),got in zip(raw_cases,outputs[len(expected):len(expected)+len(raw_cases)]):
        assert got=={'refusal':'input-malformed'},(label,got)
    for (label,_,want),got in zip(raw_extra,outputs[len(expected)+len(raw_cases):]):
        assert got==want,(label,got,want)
    print(f'{Path(command[-1]).name}: {len(expected)} preview/number/structure cases + {len(raw_cases)} transport refusals + {len(raw_extra)} exact-byte probes PASS')
print(f'Draft schema: {len(schema_valid)} positive fragments, 4 negative probes, {enum_mutations} enum-removal + {member_mutations} member-removal probes PASS')
mutations=[
 ('precision','number-precision-refusal','if Q(value) != selected:','if False:','cmp(decimalRat(v),selected)===0','true'),
 ('shortest-even-tie','shortest-integer-distance-tie-even','a % 2, q','1 - a % 2, q','odd:a%2n','odd:1n-a%2n'),
 ('duplicate-members','research-duplicate-range','if name in names:\n                fail()','if False:\n                fail()','if (seen.has(name)) fail();','if (false) fail();'),
 ('claim-domain','number-fraction-preview-only',"'claimAdmissible': admissible(raw)","'claimAdmissible': True",'claimAdmissible:admissible(raw)','claimAdmissible:true'),
 ('generated-absence','generated-text-missing-entry-kept',"if entry is not None and entry['status'] not in", "if entry is None or entry['status'] not in", "if (entry && !['supported','interpretation'].includes(entry.status))", "if (!entry || !['supported','interpretation'].includes(entry.status))")
]
for command in commands:
    name=Path(command[-1]).name
    source=Path(command[-1]).read_text()
    for title,label,py_before,py_after,js_before,js_after in mutations:
        before,after=(py_before,py_after) if name.endswith('.py') else (js_before,js_after)
        assert source.count(before)==1,(name,title,'mutation target')
        changed=source.replace(before,after)
        index=labels.index(label)
        probe=(json.dumps(requests[index],ensure_ascii=True,separators=(',',':'))+'\n').encode()
        invocation=[command[0],'-B','-c',changed] if name.endswith('.py') else [command[0],'--input-type=module','-e',executable_probe(changed)]
        result=subprocess.run(invocation,input=probe,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3,check=False)
        assert result.returncode==0,(title,'mutation setup failure',result.stderr.decode()[:500])
        altered=json.loads(result.stdout)
        assert altered!=expected[index] and 'refusal' not in altered,(title,'intended expectation did not fail',altered)
    print(f'{name}: {len(mutations)} relevant in-memory safeguard-removal probes detected PASS')
print('Scope: preview/claim admissibility only; no whole preparation, historical-envelope parity, live Desk or independent-authorship claim.')

check_interfaces()

check_inventory()

check_references(replay_changed_outputs=False)

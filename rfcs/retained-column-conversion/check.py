#!/usr/bin/env python3
"""Bounded draft checks with handwritten expectations; no preparation evidence."""
import copy
import json
import os
from pathlib import Path
from fractions import Fraction
import subprocess
import sys
import jsonschema

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE/'cases.json').read_text())
EXAMPLES = json.loads((HERE/'examples.json').read_text())
SCHEMA = json.loads((HERE/'contract.schema.json').read_text())
jsonschema.Draft202012Validator.check_schema(SCHEMA)
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)


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


def check_interfaces():
    """Focused changed-contract fixtures; old conversion corpus remains a separate gate."""
    cases = DATA['interfaceCases']
    commands = [[sys.executable, '-B', str(HERE/'reader.py')],
                [os.environ.get('RFC0029_NODE', 'node'), str(HERE/'reader.mjs')]]
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
        ('lineage-raw-number', 'lineage-original-revision7',
         "original = {'state':'present', 'json':entry['valueJson']}",
         "original = {'state':'present', 'json':entry['valueJson'].replace('-0', '0')}",
         "input={state:'present',json:e.valueJson};", "input={state:'present',json:e.valueJson.replace('-0','0')};")
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
        source = (HERE/name).read_text()
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
            invocation = [command[0], '-B', '-c', changed] if name.endswith('.py') else [command[0], '--input-type=module', '-e', changed]
            case = by_id[label]
            result = subprocess.run(invocation, input=encode(case['request']), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            assert result.returncode == 0, (name, title, 'mutation setup', result.stderr.decode()[:500])
            got = json.loads(result.stdout)
            assert got != case['expected'], (name, title, 'intended contract assertion did not fail')
            print(f'{name}: removal {title} detected at {label} expected={json.dumps(case["expected"], ensure_ascii=True, separators=(",", ":"))} got={json.dumps(got, ensure_ascii=True, separators=(",", ":"))}')
        print(f'{name}: {len(cases)} changed-interface fixtures + duplicate-name/3 limit-token refusals + {len(admission_cases)} callback-order probes + {len(removal)} safeguard-removal probes PASS')
    print(f'Draft carrier/capability schema: {mutations} member/alternative-removal controls PASS')
    print('Scope: exact UTF8 restoration, original declarations, inline lineage and Draft capability admission only; no producer, preparation, independent-authorship or adopted-limit claim.')


if '--carrier-only' in sys.argv:
    check_interfaces()
    sys.exit(0)


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
            lineage['input']={'state':'present','json':c['inputJson']}
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

for value in [EXAMPLES['generatedFrame'],EXAMPLES['assertedFrame'],EXAMPLES['lineageFragment'],EXAMPLES['generatedCarrier'],EXAMPLES['capabilitiesFragment']]:
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
enum_mutations=0
for definition in ('conversion','field','frame','result'):
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
commands=[[sys.executable,'-B',str(HERE/'reader.py')],[os.environ.get('RFC0029_NODE','node'),str(HERE/'reader.mjs')]]
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
 ('duplicate-members','research-duplicate-range','if name in names:','if False:','if (seen.has(name)) fail();','if (false) fail();'),
 ('claim-domain','number-fraction-preview-only',"'claimAdmissible': admissible(raw)","'claimAdmissible': True",'claimAdmissible:admissible(raw)','claimAdmissible:true'),
 ('generated-absence','generated-text-missing-entry-kept',"if entry is not None and entry['status'] not in", "if entry is None or entry['status'] not in", "if (entry && !['supported','interpretation'].includes(entry.status))", "if (!entry || !['supported','interpretation'].includes(entry.status))")
]
for command in commands:
    name=Path(command[-1]).name
    source=(HERE/name).read_text()
    for title,label,py_before,py_after,js_before,js_after in mutations:
        before,after=(py_before,py_after) if name.endswith('.py') else (js_before,js_after)
        assert source.count(before)==1,(name,title,'mutation target')
        changed=source.replace(before,after)
        index=labels.index(label)
        probe=(json.dumps(requests[index],ensure_ascii=True,separators=(',',':'))+'\n').encode()
        invocation=[command[0],'-B','-c',changed] if name.endswith('.py') else [command[0],'--input-type=module','-e',changed]
        result=subprocess.run(invocation,input=probe,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3,check=False)
        assert result.returncode==0,(title,'mutation setup failure',result.stderr.decode()[:500])
        altered=json.loads(result.stdout)
        assert altered!=expected[index] and 'refusal' not in altered,(title,'intended expectation did not fail',altered)
    print(f'{name}: {len(mutations)} relevant in-memory safeguard-removal probes detected PASS')
print('Scope: preview/claim admissibility only; no whole preparation, historical-envelope parity, live Desk or independent-authorship claim.')

check_interfaces()

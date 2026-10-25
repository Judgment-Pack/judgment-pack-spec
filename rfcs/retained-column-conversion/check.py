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

research=fixture({'kind':'research-value','type':'boolean','inputJson':'false'})
for name,mutation,code in [
 ('unknown-status',lambda r:r['frame']['research']['fields']['Column'].update(status='found'),'input-malformed'),
 ('duplicate-field-names',lambda r:r['frame']['research']['declaration']['fields'].append(copy.deepcopy(r['frame']['research']['declaration']['fields'][0])),'input-malformed'),
 ('field-json-name-mismatch',lambda r:r['frame']['research']['declaration']['fields'][0].update(fieldJson='{"name":"Other","type":"text"}'),'input-malformed'),
 ('field-json-duplicate',lambda r:r['frame']['research']['declaration']['fields'][0].update(fieldJson='{"name":"Column","name":"Column","type":"text"}'),'input-malformed'),
 ('field-json-over-bound',lambda r:r['frame']['research']['declaration']['fields'][0].update(fieldJson=' '*16385),'input-over-bound'),
]:
    r=copy.deepcopy(research);mutation(r);add(name,r,{'refusal':code})
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

for value in [EXAMPLES['generatedFrame'],EXAMPLES['assertedFrame'],EXAMPLES['lineageFragment']]:
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

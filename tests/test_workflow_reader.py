"""Contract-authored tests before exposure to workflow recordings or the other implementation.

Constructed examples here are unit examples, not operation/research recordings or
workflow conformance fixtures. Existing dialect recordings exercise the reused dependency.
"""
import base64
import copy
import json
import unittest
from unittest.mock import patch
from pathlib import Path

from tools import dialect_verify as d
from tools import workflow_reader as w
from tools import workflow_reader_encoding as encoding

ROOT=Path(__file__).resolve().parents[1]


def decoded(value): return d.read_document(d.canon(value),'test value')
def hashvalue(value): return d.digest_of(d.canon(value))


def change_run(example, mutate):
    """Repin literal retained bytes after a diagnostic mutation, never reader output."""
    number=len(example.instances[0]['attempts'])
    path=f'instances/root-instance/attempts/{number}/run.json'
    value=d.read_document(example.files[path],'unit run'); mutate(value['run'])
    raw=d.preparation_bytes(value); example.files[path]=raw
    pin=d.digest_of(raw)
    example.epochs[-1]['results'][0]['runDigest']=pin
    example.instances[0]['attempts'][-1]['runDigest']=pin
    return example.finish()


def replace_frozen_stage(example, sid, published, binding=None):
    """Change a root-only unit prefix's declared inputs before any attempt."""
    assert len(example.epochs)==1
    parsed=d.parse_dialect(decoded(published))
    bound=d.read_bound(parsed,decoded(binding),binding is not None).document
    index=next(i for i,s in enumerate(example.workflow['stages']) if s['id']==sid)
    definition=example.workflow['stages'][index]
    definition['dialect']={k:published[k] for k in (('formatVersion','id','version') if 'formatVersion' in published else ('version',))}
    definition['dialect']['digest']=hashvalue(published)
    release=copy.deepcopy(example.release); release['inputMapping']=bound
    frozen=example.frozen[index]
    frozen.update(publishedDialectDigest=hashvalue(published),boundDialectDigest=hashvalue(bound),
                  bindingDocumentDigest=hashvalue(binding) if binding is not None else None,
                  releaseDigest=d.digest_of(encoding.release_bytes(decoded(release))))
    for name,value in [('dialect.json',published),('bound-dialect.json',bound),('release.json',release)]:
        example.files[f'stages/{sid}/{name}']=d.canon(value)
    if binding is not None: example.files[f'stages/{sid}/binding.json']=d.canon(binding)
    if sid=='root': example.mapping=bound; example.release=release
    example.wd=hashvalue(example.workflow)
    example.files.update({'workflow.json':d.canon(example.workflow),'workflow.sha256':(example.wd+'\n').encode()})
    example.proof.update(workflowDigest=example.wd,frozenDigest=hashvalue(example.frozen))
    example.epochs[0]['previousProofDigest']=hashvalue({**example.proof,'epochBlocks':[]})
    return example.finish()


class Example:
    """Small hand-written unit recording: one case-only root, optionally a consumer.

    This builds a test subject from contract expressions; it never calls Reader,
    candidate measurement, or replay to obtain expected control bytes.
    """
    def __init__(self, children=False, limits=None, case=None, mapping=None, profiles=None):
        self.files={}; self.case=case if case is not None else {'items':[{'id':'a'},{'id':'b'}]}
        self.mapping={'version':2,'provider':'','facts':None,'evidence':None,
                      'case':{'facts':[{'target':'/items','source':'/items'}],'evidence':[]}}
        if mapping is not None: self.mapping=mapping
        self.profiles=[] if profiles is None else profiles
        self.pack={'id':'https://example.invalid/pack','version':'1.0.0','specVersion':'0.3.0','outcomes':[{'id':'ok'}]}
        self.runtime='sha256:'+'a'*64
        self.release={'schemaVersion':'1','id':'r','pack':d.canon(self.pack).decode(),'packDigest':hashvalue(self.pack),
                      'packId':self.pack['id'],'packVersion':self.pack['version'],'title':'unit','runtimeDigest':self.runtime,
                      'createdAt':'2026-10-17T00:00:00Z','config':'','lock':'','validation':None,'sample':{},'preview':None,
                      'tests':'','inputMapping':self.mapping}
        if self.profiles: self.release['inputProfiles']=self.profiles
        root=dict(id='root',dialect={**({k:self.mapping[k] for k in ('formatVersion','id','version')} if 'formatVersion' in self.mapping else {'version':self.mapping['version']}),'digest':hashvalue(self.mapping)},pack={'id':self.pack['id'],'digest':hashvalue(self.pack)},
                  input={'root':True},execution='once',caseBindings=[],outputs={'pointer':'/items','cardinality':'many'},
                  relation={'label':'related','direction':'output-to-parent'})
        stages=[root]
        if children:
            root['selection']={'mode':'reviewer'}
            child=copy.deepcopy(root); child.pop('selection'); child.update(id='child',input={'fromStage':'root','selected':True},
                  execution='each-selected-record',caseBindings=[{'from':'/id','to':'/id','type':'string','required':True}])
            stages.append(child)
        self.workflow={'workflowVersion':2,'stages':stages,'result':'child' if children else 'root',
                       'limits':{'maxStages':32,'maxRecords':4096,'maxInstances':4096,'maxAttempts':16,'maxBytes':10485760}}
        self.workflow['limits'].update(limits or {})
        self.wd=hashvalue(self.workflow); self.rd=d.digest_of(d.preparation_bytes(self.case)); self.frozen=[]
        for stage in stages:
            sid=stage['id']; f=dict(stage=sid,publishedDialectDigest=hashvalue(self.mapping),bindingDocumentDigest=None,
                                  boundDialectDigest=hashvalue(self.mapping),packDigest=hashvalue(self.pack),
                                  releaseDigest=d.digest_of(encoding.release_bytes(decoded(self.release))),runtimeDigest=self.runtime)
            self.frozen.append(f)
            for name,value in [('pack.json',self.pack),('release.json',self.release),('dialect.json',self.mapping),('bound-dialect.json',self.mapping),('profiles.json',self.profiles)]:
                self.files[f'stages/{sid}/{name}']=d.canon(value)
        self.proof=dict(admissionProofVersion=1,workflowDigest=self.wd,execution='exec',rootCaseDigest=self.rd,
                        frozenDigest=hashvalue(self.frozen),rootInstance='root-instance',epochBlocks=[])
        self.epochs=[dict(number=1,previousProofDigest=hashvalue(self.proof),kind='root')]
        self.instances=[dict(id='root-instance',stage='root',parentRecord=None,selectionDigest=None,inputDigest=self.rd,
                             caseDigest=self.rd,state='interrupted',failure=None,attempts=[])]
        self.output_sets=[dict(stage=s['id'],status='closed' if s['id']=='root' else 'blocked',records=[]) for s in stages]
        self.selections=[None for s in stages]
        self.files.update({'workflow.json':d.canon(self.workflow),'workflow.sha256':(self.wd+'\n').encode(),
                           'root-case.json':d.preparation_bytes(self.case),'instances/root-instance/case.json':d.preparation_bytes(self.case)})
        self.finish()

    def finish(self):
        self.proof['epochBlocks']=[self.epochs]
        self.execution=dict(executionVersion=2,workflowDigest=self.wd,execution='exec',rootCaseDigest=self.rd,
                            frozen=self.frozen,instances=self.instances,outputSets=self.output_sets,selections=self.selections,
                            admissionProofDigest=hashvalue(self.proof))
        self.files['admission-proof.json']=d.canon(self.proof)
        self.files['admission-proof.sha256']=(hashvalue(self.proof)+'\n').encode()
        self.files['execution.json']=d.canon(self.execution)
        self.files['execution.sha256']=(hashvalue(self.execution)+'\n').encode()
        for s in self.output_sets:
            self.files[f"sets/{s['stage']}.json"]=d.canon(dict(workflowDigest=self.wd,execution='exec',stage=s['stage'],records=s['records']))
        self.expect=w.Expectations(self.wd,hashvalue(self.execution),{s['stage']:self.runtime for s in self.frozen},d.canon(self.profiles))
        return self

    def group(self, result='evaluated', refuse_output=False):
        instance=self.instances[0]; n=len(instance['attempts'])+1
        start=dict(instance=instance['id'],number=n,retry=None if n==1 else dict(actor='operator',at='2026-10-17T01:00:00Z'))
        epoch=dict(number=len(self.epochs)+1,previousProofDigest=hashvalue(self.proof),kind='group',reservation=1,
                   starts=[start],deferred=[],cancelled=[],results=[])
        if n>1: epoch={k:v for k,v in epoch.items() if k not in ('reservation','starts','deferred','cancelled')}; epoch.update(kind='retry',start=start)
        attempt=dict(number=n,state='interrupted',failure=None,preparationDigest=None,auditDigest=None,runDigest=None,evaluationErrorDigest=None,retry=start['retry'])
        instance['attempts'].append(attempt); instance['state']='interrupted'; instance['failure']=None
        self.epochs.append(epoch)
        if result=='open': return self.finish()
        observation=dict(instance=instance['id'],number=n,state=result,failure=None,runDigest=None,preparationDigest=None,auditDigest=None,evaluationErrorDigest=None,auditSignaturesDigest=None)
        if result=='evaluated':
            parsed=d.parse_dialect(decoded(self.mapping))
            computation=d.recompute(parsed,decoded(self.case),{}, {},'2026-10-17T00:00:00Z')
            preparation=computation.preparation; pb=d.preparation_bytes(preparation); pd=d.digest_of(pb)
            disposition={'kind':'outcome','outcomeId':'ok','reasons':[],'handoff':{'state':'none'}}
            inputs=dict(facts=computation.facts,evidence=computation.evidence)
            audit=b'{"inputs":'+d.canon(inputs)+b',"disposition":'+d.canon(disposition)+b',"binding":'+d.binding_of(pd)+b'}'
            run=dict(schemaVersion='1',id='run',jobId='job',releaseId='r',revision=1,state='completed',createdAt='2026-10-17T00:00:00Z',requestedBy='operator',attempt=1,
                     input=dict(source={'mapping':self.mapping,'case':self.case,'sources':{}},preparation=preparation,**inputs),
                     result={'disposition':disposition},audit=d.read_document(audit,'audit'),auditBytes=base64.b64encode(audit).decode())
            export=dict(version=3,releaseDigest=self.frozen[0]['releaseDigest'],release=self.release,run=run)
            rb=d.preparation_bytes(export); path=f'instances/root-instance/attempts/{n}/'
            self.files.update({path+'run.json':rb,path+'sources.json':b'{}',path+'preparation.json':pb,path+'preparation.sha256':(pd+'\n').encode(),
                               path+'verified-at.txt':b'2026-10-17T00:00:00Z\n',path+'audit.json':audit})
            observation.update(runDigest=d.digest_of(rb),preparationDigest=pd,auditDigest=d.digest_of(audit))
            for k in ('runDigest','preparationDigest','auditDigest'): attempt[k]=observation[k]
            payloads=self.case['items']; records=[]
            for index,payload in enumerate([] if refuse_output else payloads):
                f=self.frozen[0]
                lineage=dict(workflowDigest=self.wd,execution='exec',stage='root',instance='root-instance',
                             publishedDialectDigest=f['publishedDialectDigest'],bindingDocumentDigest=None,boundDialectDigest=f['boundDialectDigest'],
                             packDigest=f['packDigest'],releaseDigest=f['releaseDigest'],preparationDigest=pd,auditDigest=d.digest_of(audit),
                             outputPointer='/items',index=index,rootCaseDigest=self.rd,caseDigest=self.rd,parentRecord=None,selectionDigest=None,
                             relation=self.workflow['stages'][0]['relation'],influence={'classes':['asserted'],'generatedInfluence':False})
                record=dict(outputRecordVersion=1,payloadDigest=d.digest_of(d.preparation_bytes(payload)),lineage=lineage)
                self.files[f'outputs/root/root-instance/{index}/payload.json']=d.preparation_bytes(payload)
                self.files[f'outputs/root/root-instance/{index}/record.json']=d.canon(record); records.append(hashvalue(record))
            self.output_sets[0]['records']=records
            attempt['state']=instance['state']='failed' if refuse_output else 'completed' if payloads else 'completed-zero'
            if refuse_output: attempt['failure']=instance['failure']='limit-exceeded'
        else: attempt['state']=instance['state']=result
        epoch['results'].append(observation)
        return self.finish()

    def failed(self,failure='preparation-failed',acquisitions=None,at='2026-10-17T00:00:00Z'):
        acquisitions={} if acquisitions is None else acquisitions
        self.group('open'); instance=self.instances[0]; attempt=instance['attempts'][-1]
        run=dict(schemaVersion='1',id='run',jobId='job',releaseId='r',revision=1,state='failed',createdAt='2026-10-17T00:00:00Z',
                 requestedBy='operator',attempt=1,input={'source':{'mapping':self.mapping,'case':self.case,'sources':acquisitions}})
        if at is not ...: run['finishedAt']=at
        export=dict(version=2,releaseDigest=self.frozen[0]['releaseDigest'],release=self.release,run=run)
        rb=d.preparation_bytes(export); prefix='instances/root-instance/attempts/1/'
        self.files[prefix+'run.json']=rb; self.files[prefix+'sources.json']=d.preparation_bytes(acquisitions)
        observation=dict(instance=instance['id'],number=1,state='failed',failure=failure,runDigest=d.digest_of(rb),
                         preparationDigest=None,auditDigest=None,evaluationErrorDigest=None,auditSignaturesDigest=None)
        self.epochs[-1]['results']=[observation]
        instance.update(state='failed',failure=failure); attempt.update(state='failed',failure=failure,runDigest=d.digest_of(rb))
        return self.finish()

    def selection(self, selected_indices=(0,), long_id='child-instance'):
        records=self.output_sets[0]['records']; selected=[records[i] for i in selected_indices]
        revision=1+sum(e['kind'] in ('selection','fork') for e in self.epochs)
        fork=revision>1
        selection=dict(selectionVersion=1,workflowDigest=self.wd,execution='exec',upstreamStage='root',
                       outputSetDigest=d.digest_of(self.files['sets/root.json']),selected=selected,mode='reviewer',revision=revision,
                       review={'actor':'operator','assertion':'selected','at':'2026-10-17T01:00:00Z'})
        sd=hashvalue(selection); ids=[long_id+('' if j==0 else '-'+str(j)) for j in range(len(selected))]
        count_refusal=1+sum(len(e.get('childIds') or []) for e in self.epochs)+len(ids)>self.workflow['limits']['maxInstances']
        self.epochs.append(dict(number=len(self.epochs)+1,previousProofDigest=hashvalue(self.proof),kind='fork' if fork else 'selection',upstreamStage='root',revision=revision,
                                selectionCoreDigest=sd,childIds=None if count_refusal else ids))
        if fork:
            self.instances=[i for i in self.instances if i['stage']=='root']
            self.output_sets[1].update(status='blocked',records=[])
        if count_refusal: selection['refusal']='limit-exceeded'; ids=[]
        self.selections[0]=hashvalue(selection); self.files[f'selections/root/{revision}.json']=d.canon(selection)
        if not count_refusal: self.output_sets[1]['status']='closed'
        for iid,index,rid in zip(ids,selected_indices,selected):
            case={'id':self.case['items'][index]['id']}; raw=d.preparation_bytes(case)
            input_digest=hashvalue(dict(parentRecord=rid,selectionDigest=sd,caseBindings=self.workflow['stages'][1]['caseBindings']))
            self.instances.append(dict(id=iid,stage='child',parentRecord=rid,selectionDigest=sd,inputDigest=input_digest,caseDigest=d.digest_of(raw),state='interrupted',failure=None,attempts=[]))
            self.files[f'instances/{iid}/case.json']=raw
        return self.finish()


class ReaderTests(unittest.TestCase):
    def read(self,e,exit=0):
        result=w.verify(e.files,e.expect,comparison_trace=True)
        self.assertEqual(result.exit_code,exit,result.detail)
        return result

    def operation_profile(self, *, scoped=False, generated=False):
        profile={'id':'p','publicKey':'87b6b57a78f442c53ff379562e468e08b2ba7b16ebfeb795f6f60fc332e507d8',
                 'class':'generated' if generated else 'record','source':'unit','authority':'unit',
                 'adapter':{'name':'adapter-web' if scoped else 'adapter-http','version':'1','digest':'sha256:'+'b'*64},
                 'shape':'http','endpoint':None if scoped else 'https://example.com/'}
        if scoped: profile['endpointScope']=['https://example.com/']
        mapping=copy.deepcopy(Example().mapping)
        mapping['sources']=[{'name':'operation','kind':'operation','profile':'p','profileDigest':hashvalue(profile),
                             'maxAge':300,'arguments':{},'read':{'copy':{'facts':[{'target':'/result','source':'/result'}],'evidence':[]}}}]
        return profile,mapping

    def test_scoped_profile_rejected_before_root_attempt_and_for_unused_downstream(self):
        profile,mapping=self.operation_profile(scoped=True)
        for sid in ('root','child'):
            e=replace_frozen_stage(Example(sid=='child',profiles=[profile]),sid,mapping)
            with self.subTest(stage=sid):
                self.assertEqual(self.read(e,2).report['finding'],'stage-binding-mismatch')
                self.assertFalse(any(i['attempts'] for i in e.instances))

    def test_generated_operation_requires_exact_generated_admission_before_replay(self):
        profile,mapping=self.operation_profile(generated=True)
        for sid in ('root','child'):
            for classes in (['generated','record'],['asserted','generated'],['generated']):
                mapping['admits']={'facts':{'/result':classes}}
                e=replace_frozen_stage(Example(sid=='child',profiles=[profile]),sid,mapping)
                with self.subTest(stage=sid,classes=classes):
                    result=self.read(e,0 if classes==['generated'] else 2)
                    if result.exit_code: self.assertEqual(result.report['finding'],'stage-binding-mismatch')

    def test_optional_retained_run_and_import_forms_are_refused_after_repinning(self):
        mutations=[lambda r,key=key,bad=bad:r.update({key:bad}) for key,bad in [('startedAt',42),('finishedAt',[]),('problem',None)]]
        mutations += [lambda r:r['input']['source'].update({'mappingDigest':42})]
        for value in (42,None,[],{}, {'dialect':{'version':99},'binding':{'unrelated':True}}):
            mutations.append(lambda r,value=value:r['input']['source'].update({'import':value}))
        for index,mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.assertEqual(self.read(change_run(Example().group(),mutate),1).report['refusal'],'input-malformed')
        good=change_run(Example().group(),lambda r:r.update(startedAt='2026-10-17T00:00:00Z',finishedAt='2026-10-17T00:00:01Z',problem=''))
        self.assertEqual(self.read(good).report['completion'],'complete')

    def imported_example(self):
        directory=ROOT/'conformance/dialect/vectors/unbound-bound-at-import'
        load=lambda name:d.read_document((directory/name).read_bytes(),name)
        imported={'dialect':load('unbound.json'),'binding':load('binding.json')}
        e=Example(mapping=load('mapping.json'),case=load('case.json'),profiles=load('profiles.json'))
        replace_frozen_stage(e,'root',imported['dialect'],imported['binding'])
        e.failed('acquisition-failed')
        return change_run(e,lambda r:r['input']['source'].update({'import':imported})),imported

    def test_retained_import_association_matches_frozen_published_and_binding(self):
        e,imported=self.imported_example()
        self.assertEqual(self.read(e).report['completion'],'partial')
        # Foreign catalog identity can derive the same bound mapping; equality of
        # the bound mapping alone cannot establish original import association.
        foreign=copy.deepcopy(imported); foreign['dialect']['sources'][0]['platform']='foreign-platform'
        foreign['binding']['dialect']=hashvalue(foreign['dialect'])
        change_run(e,lambda r:r['input']['source'].update({'import':foreign}))
        self.assertEqual(self.read(e,2).report['finding'],'stage-binding-mismatch')
        e,imported=self.imported_example(); foreign=copy.deepcopy(imported)
        foreign['binding']['sources']['intake']['profileDigest']='sha256:'+'c'*64
        change_run(e,lambda r:r['input']['source'].update({'import':foreign}))
        self.assertEqual(self.read(e,2).report['finding'],'stage-binding-mismatch')
        e=change_run(Example().group(),lambda r:r['input']['source'].update({'import':imported}))
        self.assertEqual(self.read(e,2).report['finding'],'stage-binding-mismatch')

    def test_import_count_bound_precedes_unrelated_optional_form_error(self):
        e,imported=self.imported_example(); foreign=copy.deepcopy(imported)
        foreign['dialect']['sources']*=257
        change_run(e,lambda r:(r.update(startedAt=42),r['input']['source'].update({'import':foreign})))
        self.assertEqual(self.read(e,1).report['refusal'],'input-over-bound')

    def sidecar_example(self,raw):
        e=Example().group(); path='instances/root-instance/attempts/1/audit-signatures.json'
        e.files[path]=raw; e.epochs[-1]['results'][0]['auditSignaturesDigest']=d.digest_of(raw)
        return e.finish(),path

    def test_signature_sidecar_jsonl_and_unreadable_bytes_are_pinned_and_counted(self):
        for raw in (b'{"seq":1}\n{"seq":2}\n',b'\xff\x00unreadable retained material\n',b'x'*16384,b''):
            with self.subTest(length=len(raw)):
                e,path=self.sidecar_example(raw); result=self.read(e)
                self.assertEqual(result.report['authentication'],'not-established')
                final=result.trace[-1]
                self.assertEqual(final['files'][path],{'bytes':len(raw),'digest':d.digest_of(raw)})
                self.assertEqual(final['bytes'],sum(map(len,e.files.values())))
                self.assertNotIn(path,result.trace[0]['files'])
                candidates=[c for c in result.trace if c['candidate']=='output-accept']
                self.assertTrue(candidates); self.assertTrue(all(path in c['files'] for c in candidates))

    def test_signature_sidecar_bound_is_global_and_pin_is_literal(self):
        e,path=self.sidecar_example(b'x'*16385); e.files['sets/root.json']=b'{bad'
        self.assertEqual(self.read(e,1).report['refusal'],'input-over-bound')
        e,path=self.sidecar_example(b'{"seq":1}\n{"seq":2}\n'); e.files[path]+=b'\n'
        self.assertEqual(self.read(e,2).report['finding'],'digest-mismatch')

    def test_signature_sidecar_presence_and_attempt_ownership_are_required(self):
        e,path=self.sidecar_example(b'opaque'); del e.files[path]
        self.assertEqual(self.read(e,1).report['refusal'],'inventory-mismatch')
        e,path=self.sidecar_example(b'opaque'); e.files[path.replace('/1/','/2/')]=e.files.pop(path)
        self.assertEqual(self.read(e,1).report['refusal'],'inventory-mismatch')
        e,path=self.sidecar_example(b'opaque'); e.epochs[-1]['results'][0]['auditSignaturesDigest']=None; e.finish()
        self.assertEqual(self.read(e,2).report['finding'],'inventory-mismatch')

    def test_runner_attempt_number_is_not_assumed_to_equal_workflow_ordinal(self):
        e=change_run(Example().group(),lambda r:r.update(attempt=99))
        self.assertEqual(self.read(e).report['completion'],'complete')

    def test_root_reconstructs_distinct_case_paths(self):
        e=Example(); result=self.read(e)
        self.assertEqual(result.report['completion'],'partial')
        trace=result.trace[0]
        self.assertEqual(trace['files']['root-case.json'],trace['files']['instances/root-instance/case.json'])
        self.assertEqual(trace['bytes'],sum(map(len,e.files.values())))
        self.assertEqual(trace['paths'],len(e.files))

    def test_valid_evaluation_and_complete_output_inventory(self):
        e=Example().group(); result=self.read(e)
        self.assertEqual(result.report['completion'],'complete')
        self.assertEqual(result.report['counts']['outputs'],2)
        self.assertIn('output-accept',[c['candidate'] for c in result.trace])
        final=result.trace[-1]
        self.assertEqual(final['bytes'],sum(map(len,e.files.values())))
        self.assertEqual(final['files'],{p:{'bytes':len(v),'digest':d.digest_of(v)} for p,v in e.files.items()})

    def test_open_epoch_and_explicit_interrupted_retry(self):
        self.assertEqual(self.read(Example().group('open')).report['completion'],'partial')
        e=Example().group('interrupted').group(); result=self.read(e)
        self.assertEqual(result.report['completion'],'complete')
        self.assertEqual(result.trace[-1]['retained']['attempts'],2)

    def test_selected_case_is_derived_and_unselected_has_no_child(self):
        e=Example(True).group().selection((1,)); result=self.read(e)
        self.assertEqual(result.report['counts']['instances'],2)
        self.assertEqual(d.read_document(e.files['instances/child-instance/case.json'],'case'),{'id':'b'})
        bad=copy.deepcopy(e); bad.files['instances/child-instance/case.json']=b'{"id":"a"}'
        self.assertEqual(self.read(bad,2).report['finding'],'case-mismatch')

    def test_empty_selection_reserves_zero_children(self):
        result=self.read(Example(True).group().selection(()))
        self.assertEqual(result.report['completion'],'complete')
        self.assertEqual(result.report['counts']['instances'],1)

    def test_missing_and_extra_retained_artifacts(self):
        e=Example().group(); del e.files['instances/root-instance/attempts/1/audit.json']
        self.assertEqual(self.read(e,1).report['refusal'],'inventory-mismatch')
        e=Example(); e.files['instances/unclaimed/case.json']=b'{}'
        self.assertEqual(self.read(e,2).report['finding'],'inventory-mismatch')

    def test_supplied_auxiliary_bytes_do_not_enter_root_candidate(self):
        e=Example(); e.files['aux/retained.bin']=b'x'*5000
        r=self.read(e); self.assertEqual(r.trace[0]['bytes'],sum(map(len,e.files.values()))-5000)

    def test_bad_independent_pin_precedes_replay(self):
        e=Example(); e.expect=w.Expectations('sha256:'+'b'*64,e.expect.execution_digest,e.expect.runtime_digests,b'[]')
        self.assertEqual(self.read(e,2).report['finding'],'digest-mismatch')

    def test_duplicate_json_unknown_epoch_member_and_wrong_membership(self):
        e=Example(); e.files['workflow.json']=b'{"workflowVersion":2,"workflowVersion":2}'
        self.assertEqual(self.read(e,1).report['refusal'],'input-malformed')
        e=Example(); e.epochs[0]['extra']=True; e.finish()
        self.assertEqual(self.read(e,1).report['refusal'],'input-malformed')
        e=Example().group('open'); e.epochs[-1]['starts']=[]; e.finish()
        self.assertEqual(self.read(e,2).report['finding'],'inventory-mismatch')

    def test_preparation_is_recomputed_not_just_hashed(self):
        e=Example().group(); path='instances/root-instance/attempts/1/preparation.json'
        p=d.read_document(e.files[path],'prep'); p['outcomes'][0]['claim']['facts']['items'][0]['id']='forged'
        # Change only the sidecar: byte identity must fail before preparation semantics.
        e.files[path]=d.preparation_bytes(p)
        self.assertEqual(self.read(e,2).report['finding'],'digest-mismatch')

    def test_output_payload_substitution_fails(self):
        e=Example().group(); e.files['outputs/root/root-instance/0/payload.json']=b'{"id":"other"}'
        self.assertEqual(self.read(e,2).report['finding'],'output-mismatch')

    def test_forged_fitting_selection_refusal_fails(self):
        e=Example(True).group().selection()
        s=d.read_document(e.files['selections/root/1.json'],'selection'); s['refusal']='limit-exceeded'
        e.files['selections/root/1.json']=d.canon(s)
        self.assertEqual(self.read(e,2).report['finding'],'inventory-mismatch')

    def test_error_envelope_closed_form(self):
        e=Example(); reader=w.Reader(e.files,e.expect)
        error=dict(outputVersion='2',tool={'name':'jpack','version':'0.34.0'},command='experimental evaluate',status='error',
                   evaluationError={'class':'resource-exhaustion','phase':'evaluation','evaluatorSpecVersion':'0.3.0'},diagnostics=[])
        reader.error_form(error)
        for mutation in [dict(error,disposition={}),dict(error,evaluationError={'class':'resource-exhaustion','phase':'preflight','evaluatorSpecVersion':'0.3.0'})]:
            with self.assertRaises(w.Problem): reader.error_form(mutation)

    def test_error_envelope_rejects_stale_evaluator_version(self):
        e=Example(); reader=w.Reader(e.files,e.expect)
        error=dict(outputVersion='2',tool={'name':'jpack','version':'0.34.0'},command='experimental evaluate',status='error',
                   evaluationError={'class':'resource-exhaustion','phase':'evaluation','evaluatorSpecVersion':'0.2.0-draft'},diagnostics=[])
        with self.assertRaises(w.Problem) as caught: reader.error_form(error)
        self.assertEqual((caught.exception.result,caught.exception.code,caught.exception.detail),
                         ('refusal','input-malformed','Core error phase'))

    def test_empty_output_is_completed_zero(self):
        result=self.read(Example(case={'items':[]}).group())
        self.assertEqual(result.report['completion'],'complete')
        self.assertEqual(result.report['counts']['outputs'],0)

    def test_output_count_cutoff_has_full_accept_and_refusal_candidates(self):
        e=Example(limits={'maxRecords':1}).group(refuse_output=True)
        result=self.read(e)
        accept=next(x for x in result.trace if x['candidate']=='output-accept')
        refuse=next(x for x in result.trace if x['candidate']=='output-refuse')
        self.assertFalse(accept['fits']); self.assertTrue(refuse['fits'])
        self.assertEqual(accept['retained']['outputs'],2)
        self.assertEqual(refuse['retained']['outputs'],0)
        self.assertGreater(accept['bytes'],refuse['bytes'])
        self.assertTrue(accept['completeCandidate'])
        self.assertEqual(result.report['completion'],'partial')

    def test_forged_output_refusal_when_whole_candidate_fits(self):
        e=Example().group(refuse_output=True)
        self.assertEqual(self.read(e,2).report['finding'],'output-mismatch')

    def test_count_refusal_does_not_allocate_child_ids(self):
        e=Example(True,limits={'maxInstances':1}).group().selection((0,1))
        result=self.read(e)
        self.assertEqual(result.report['counts']['instances'],1)
        self.assertEqual(result.report['completion'],'partial')
        self.assertIsNone(e.epochs[-1]['childIds'])
        e.epochs[-1]['childIds']=['unexpected','unexpected-two']; e.finish()
        self.assertEqual(self.read(e,2).report['finding'],'inventory-mismatch')

    def test_fork_retires_identity_and_retains_prior_case_and_selection(self):
        e=Example(True).group().selection((0,)).selection((1,),long_id='replacement')
        result=self.read(e)
        self.assertEqual(result.report['counts']['instances'],2)
        self.assertEqual(result.trace[-1]['retained']['instances'],3)
        self.assertIn('instances/child-instance/case.json',result.trace[-1]['files'])
        self.assertIn('selections/root/1.json',result.trace[-1]['files'])
        self.assertIn('selections/root/2.json',result.trace[-1]['files'])
        bad=Example(True).group().selection((0,)).selection((0,))
        self.assertEqual(self.read(bad,2).report['finding'],'inventory-mismatch')

    def test_fork_count_includes_retired_identities(self):
        e=Example(True,limits={'maxInstances':2}).group().selection((0,)).selection((1,),long_id='replacement')
        result=self.read(e)
        self.assertEqual(result.report['counts']['instances'],1)
        self.assertEqual(result.trace[-1]['retained']['instances'],2)
        self.assertIsNone(e.epochs[-1]['childIds'])

    def test_exact_final_byte_boundary_and_auxiliary_overflow(self):
        bound=5000
        for _ in range(4):
            e=Example(limits={'maxBytes':bound}); bound=sum(map(len,e.files.values()))
        e=Example(limits={'maxBytes':bound})
        self.assertEqual(sum(map(len,e.files.values())),bound)
        self.assertEqual(self.read(e).trace[0]['bytes'],bound)
        e.files['aux/one-byte']=b'x'
        self.assertEqual(self.read(e,1).report['refusal'],'input-over-bound')

    def test_preparation_semantic_forgery_with_all_associated_pins_recomputed(self):
        e=Example().group(); prefix='instances/root-instance/attempts/1/'
        prep=d.read_document(e.files[prefix+'preparation.json'],'preparation')
        prep['outcomes'][0]['claim']['facts']['items'][0]['id']='forged'
        pb=d.preparation_bytes(prep); pd=d.digest_of(pb)
        export=d.read_document(e.files[prefix+'run.json'],'run'); export['run']['input']['preparation']=prep
        audit=e.files[prefix+'audit.json']
        oldpd=e.epochs[-1]['results'][0]['preparationDigest']
        audit=audit.replace(oldpd.encode(),pd.encode())
        export['run']['audit']=d.read_document(audit,'audit')
        export['run']['auditBytes']=base64.b64encode(audit).decode()
        rb=d.preparation_bytes(export)
        e.files.update({prefix+'preparation.json':pb,prefix+'preparation.sha256':(pd+'\n').encode(),prefix+'run.json':rb,prefix+'audit.json':audit})
        pins=dict(preparationDigest=pd,runDigest=d.digest_of(rb),auditDigest=d.digest_of(audit))
        e.epochs[-1]['results'][0].update(pins); e.instances[0]['attempts'][0].update(pins); e.finish()
        self.assertEqual(self.read(e,2).report['finding'],'preparation-mismatch')

    def test_run_v4_is_version_unread_before_supported_closed_form(self):
        e=Example().group(); path='instances/root-instance/attempts/1/run.json'
        run=d.read_document(e.files[path],'run'); run['version']=4; run['chain']={'anything':'outside supported forms'}
        e.files[path]=d.preparation_bytes(run)
        result=self.read(e,1)
        self.assertEqual(result.report['refusal'],'version-unread')

    def test_terminal_failure_is_recomputed_at_retained_finished_at(self):
        directory=ROOT/'conformance/dialect/vectors/valid'
        load=lambda name:d.read_document((directory/name).read_bytes(),name)
        e=Example(mapping=load('mapping.json'),case=load('case.json'),profiles=load('profiles.json'))
        result=self.read(e.failed(acquisitions=load('sources.json'),at='2026-10-17T00:00:00Z'))
        self.assertEqual(result.report['completion'],'partial')  # receipt is stale at this instant
        self.assertFalse(any(path.endswith('/verified-at.txt') for path in e.files))
        fresh=Example(mapping=load('mapping.json'),case=load('case.json'),profiles=load('profiles.json'))
        self.assertEqual(self.read(fresh.failed(acquisitions=load('sources.json'),at='2026-10-14T14:58:26Z'),2).report['finding'],'inventory-mismatch')

    def test_failed_preparation_never_substitutes_started_at_or_receipt_clock(self):
        directory=ROOT/'conformance/dialect/vectors/valid'
        load=lambda name:d.read_document((directory/name).read_bytes(),name)
        e=Example(mapping=load('mapping.json'),case=load('case.json'),profiles=load('profiles.json')).failed(acquisitions=load('sources.json'))
        path='instances/root-instance/attempts/1/run.json'
        export=d.read_document(e.files[path],'run'); export['run']['startedAt']='2026-10-14T14:58:26Z'
        e.files[path]=d.preparation_bytes(export); pin=d.digest_of(e.files[path])
        e.instances[0]['attempts'][0]['runDigest']=pin; e.epochs[-1]['results'][0]['runDigest']=pin; e.finish()
        self.assertEqual(self.read(e).report['completion'],'partial')

    def test_failed_preparation_clock_closed_form(self):
        for at in (...,None,'2026-10-17T00:00:00.1Z','2026-10-17T01:00:00+01:00','2026-02-30T00:00:00Z','invalid'):
            with self.subTest(at=at):
                self.assertEqual(self.read(Example().failed(at=at),1).report['refusal'],'input-malformed')

    def test_pending_acquisition_does_not_establish_terminal_failure(self):
        directory=ROOT/'conformance/dialect/vectors/valid'
        load=lambda name:d.read_document((directory/name).read_bytes(),name)
        e=Example(mapping=load('mapping.json'),case=load('case.json'),profiles=load('profiles.json')).failed()
        self.assertEqual(self.read(e,2).report['finding'],'inventory-mismatch')
        # Earlier parameter failure still wins over the later missing acquisition.
        e=Example(mapping=load('mapping.json'),case={},profiles=load('profiles.json')).failed()
        self.assertEqual(self.read(e).report['completion'],'partial')

    def test_missing_response_inside_retained_research_is_terminal(self):
        directory=ROOT/'conformance/dialect/vectors/work-item-triage-presence-optional-omitted'
        load=lambda name:d.read_document((directory/name).read_bytes(),name)
        acquisitions=load('sources.json')
        del acquisitions['item']['response']['result']['responses'][0]['result']
        e=Example(mapping=load('mapping.json'),case=load('case.json'),profiles=load('profiles.json'))
        result=self.read(e.failed(acquisitions=acquisitions,at=load('preparation.json')['verifiedAt']))
        self.assertEqual(result.report['completion'],'partial')
        # The source acquisition itself is pending when its entire member is absent.
        e=Example(mapping=load('mapping.json'),case=load('case.json'),profiles=load('profiles.json'))
        self.assertEqual(self.read(e.failed(acquisitions={},at=load('preparation.json')['verifiedAt']),2).report['finding'],'inventory-mismatch')

    def test_terminal_failure_must_match_closed_derived_class(self):
        mapping=copy.deepcopy(Example().mapping); mapping['admits']={'facts':{'/items':['record']}}
        self.assertEqual(self.read(Example(mapping=mapping).failed('admission-refused')).report['completion'],'partial')
        self.assertEqual(self.read(Example(mapping=mapping).failed('preparation-failed'),2).report['finding'],'inventory-mismatch')
        self.assertEqual(self.read(Example().failed(),2).report['finding'],'inventory-mismatch')

    def test_unrecognized_derivation_or_operational_failure_is_not_preparation_failure(self):
        for error in (d.Finding('not-a-terminal-finding'),d.Finding('acquisition-missing','unrecognized detail'),TimeoutError('offline timeout'),OSError('local I/O')):
            with self.subTest(error=str(error)),patch.object(d,'recompute',side_effect=error):
                result=self.read(Example().failed(),3)
                self.assertIsNone(result.report)

    def test_global_preflight_bounds_precede_malformed_and_unread_other_files(self):
        for reverse in (False,True):
            e=Example(); e.files['workflow.json']=b'{invalid'; e.files['root-case.json']=b' '*1048577
            if reverse: e.files=dict(reversed(list(e.files.items())))
            self.assertEqual(self.read(e,1).report['refusal'],'input-over-bound')
            e=Example(); e.files['workflow.json']=b'{invalid'; e.files['sets/root.json']=d.canon({'records':['x']*4097})
            self.assertEqual(self.read(e,1).report['refusal'],'input-over-bound')
            e=Example(); e.proof['admissionProofVersion']=9; e.finish(); e.files['sets/root.json']=b'['*65+b'0'+b']'*65
            self.assertEqual(self.read(e,1).report['refusal'],'input-over-bound')

    def test_global_preflight_preparation_envelope_bound_precedes_other_form_error(self):
        e=Example().failed(acquisitions={'extra':'x'*2097152})
        e.files['sets/root.json']=b'null'
        self.assertEqual(self.read(e,1).report['refusal'],'input-over-bound')

    def test_global_preflight_malformed_precedes_unread_or_missing_elsewhere(self):
        e=Example(); e.proof['admissionProofVersion']=9; e.finish()
        execution=d.read_document(e.files['execution.json'],'execution'); execution['unknown']=True
        e.files['execution.json']=d.canon(execution)
        self.assertEqual(self.read(e,1).report['refusal'],'input-malformed')
        e=Example().group(); del e.files['instances/root-instance/attempts/1/audit.json']; e.files['stages/root/profiles.json']=b'{}'
        self.assertEqual(self.read(e,1).report['refusal'],'input-malformed')
        e=Example(True); definition=d.read_document(e.files['workflow.json'],'workflow')
        definition['stages'][0]['dialect']['version']=99; definition['stages'][1]['pack']['id']='relative'
        e.files['workflow.json']=d.canon(definition)
        self.assertEqual(self.read(e,1).report['refusal'],'input-malformed')

    def test_missing_required_control_is_inventory_refusal(self):
        for path in ('workflow.json','execution.json','admission-proof.json','root-case.json'):
            e=Example(); del e.files[path]
            with self.subTest(path=path): self.assertEqual(self.read(e,1).report['refusal'],'inventory-mismatch')

    def test_existing_dialect_release_dependency(self):
        raw=(ROOT/'conformance/dialect/vectors/valid/run.json').read_bytes(); value=d.read_document(raw,'existing dialect run')
        self.assertEqual(d.digest_of(encoding.release_bytes(value['release'])),value['releaseDigest'])

    def test_reader_phases_do_not_hide_programming_errors(self):
        e=Example(True).group().selection()
        r=w.Reader(e.files,e.expect,True)
        r.preflight(); r.pins(); r.verify_preparations()
        self.assertEqual(r.replay()['result'],'reading')


class RetainedEncodingTests(unittest.TestCase):
    def test_raw_literals_and_html_escaping_are_not_dialect_canon(self):
        raw=b'{"z":-0,"html":"<&>","numbers":[1.00,1E+3,9007199254740993]}'
        expected=b'{"html":"\\u003c\\u0026\\u003e","numbers":[1.00,1E+3,9007199254740993],"z":-0}'
        self.assertEqual(encoding.retained_bytes(d.read_document(raw,'retained')),expected)

    def test_controls_line_separators_and_unicode_key_order(self):
        value={'\U0001f600':'\u2028\u2029','\ue000':'\b\f\n\r\t\x00"\\','a':'é'}
        expected='{"a":"é","\ue000":"\\b\\f\\n\\r\\t\\u0000\\"\\\\","\U0001f600":"\\u2028\\u2029"}'.encode()
        self.assertEqual(encoding.retained_bytes(value),expected)

    def test_raw_numeric_bounds_remain_the_strict_input_readers_responsibility(self):
        for literal in ('1'+'0'*127,'1e308','-1.2500e-308'):
            value=d.read_document(literal.encode(),'retained number')
            self.assertEqual(encoding.retained_bytes(value),literal.encode())
        for literal in ('1'+'0'*128,'1e309'):
            with self.assertRaises(d.Refused): d.read_document(literal.encode(),'retained number')

    def test_typed_integer_and_raw_number_take_different_paths(self):
        raw=d.read_document(b'{"sample":{"preparation":{"version":-0},"facts":{"n":-0}},"preview":{"n":1.20}}','release')
        projected=encoding.project('release',raw)
        self.assertEqual(projected['sample']['preparation']['version'],0)
        encoded=encoding.release_bytes(raw)
        self.assertIn(b'"version":0',encoded)
        self.assertIn(b'"facts":{"n":-0}',encoded)
        self.assertIn(b'"preview":{"n":1.20}',encoded)
        raw['sample']['preparation']['version']=d.Num('1.0')
        with self.assertRaises(d.Refused): encoding.release_bytes(raw)

    def test_raw_null_is_retained_and_empty_omitted_fields_are_not_inserted(self):
        raw=d.read_document(b'{"sample":{"facts":null,"evidence":{}},"inputProfiles":[],"mappingWarnings":[],"discarded":1}','release')
        projected=encoding.project('release',raw)
        self.assertEqual(projected['sample'],{'facts':None,'evidence':{}})
        self.assertNotIn('inputProfiles',projected)
        self.assertNotIn('mappingWarnings',projected)
        self.assertNotIn('discarded',projected)
        self.assertIn(b'"sample":{"evidence":{},"facts":null}',encoding.release_bytes(raw))



if __name__=='__main__': unittest.main()

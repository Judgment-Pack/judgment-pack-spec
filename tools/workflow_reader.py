"""Separately authored, offline RFC 0024 workflow reader experiment.

Contract pin: 88794f7ac09fc46d8af89605f1defbd7a7db14d9. Not a conformance claim.
Input authority is explicit in Expectations; files never confer trust on themselves.
See workflow_reader_README.md for scope, authorship, exposure, and comparison protocol.
"""
from __future__ import annotations

import base64
import copy
import re
from dataclasses import dataclass, field
from typing import Mapping, Any
from urllib.parse import urlsplit

from . import dialect_verify as d
from . import workflow_reader_encoding as encoding

SPEC_PIN = '88794f7ac09fc46d8af89605f1defbd7a7db14d9'
ID = re.compile(r'[a-z][a-z0-9-]{0,63}')
LIMITS = dict(maxStages=32, maxRecords=4096, maxInstances=4096, maxAttempts=16, maxBytes=1073741824)
STATES = {'completed', 'completed-zero', 'failed', 'interrupted', 'cancelled'}
FAILURES = {'projection-invalid', 'admission-refused', 'acquisition-failed', 'preparation-failed', 'evaluation-error', 'output-invalid', 'limit-exceeded'}
ARTIFACT_PINS = ('runDigest', 'preparationDigest', 'auditDigest', 'evaluationErrorDigest', 'auditSignaturesDigest')
PIN_FILES = dict(runDigest='run.json', preparationDigest='preparation.json', auditDigest='audit.json',
                 evaluationErrorDigest='evaluation-error.json', auditSignaturesDigest='audit-signatures.json')
FROZEN = {'stage', 'publishedDialectDigest', 'bindingDocumentDigest', 'boundDialectDigest', 'packDigest', 'releaseDigest', 'runtimeDigest'}
INSTANCE = {'id', 'stage', 'parentRecord', 'selectionDigest', 'inputDigest', 'caseDigest', 'state', 'failure', 'attempts'}
ATTEMPT = {'number', 'state', 'failure', 'preparationDigest', 'auditDigest', 'runDigest', 'evaluationErrorDigest', 'retry'}
LINEAGE = {'workflowDigest', 'execution', 'stage', 'instance', 'publishedDialectDigest', 'bindingDocumentDigest',
           'boundDialectDigest', 'packDigest', 'releaseDigest', 'preparationDigest', 'auditDigest', 'outputPointer', 'index',
           'rootCaseDigest', 'caseDigest', 'parentRecord', 'selectionDigest', 'relation', 'influence'}


class OperationalError(Exception):
    """No portable outcome: unsupported scope, local processing ceiling, or invalid API use."""


class Problem(Exception):
    def __init__(self, result, code, detail):
        self.result, self.code, self.detail = result, code, detail
        super().__init__(detail)


def refuse(code, detail): raise Problem('refusal', code, detail)
def finding(code, detail): raise Problem('finding', code, detail)
def require(condition, detail):
    if not condition: refuse('input-malformed', detail)
def check(condition, code, detail):
    if not condition: finding(code, detail)


def closed(value, required, optional=(), where='object'):
    require(isinstance(value, dict) and set(required) <= value.keys() and value.keys() <= set(required) | set(optional), f'{where}: closed form')
    return value


def integer(value, low=0, high=2**53-1):
    if isinstance(value, d.Num) and value.is_integer(): value = d.integer_of(value)
    require(type(value) is int and low <= value <= high, 'integer outside its declared form')
    return value


def text(value, low=0, high=65536):
    require(isinstance(value, str) and low <= len(value.encode('utf-8')) <= high, 'string outside its declared form')
    return value


def ident(value):
    require(isinstance(value, str) and ID.fullmatch(value) is not None, 'invalid workflow id')
    return value


def digest(value, nullable=False):
    require((nullable and value is None) or d.is_digest(value), 'invalid digest')
    return value


def array(value, low=0, high=4096):
    require(isinstance(value, list), 'expected array')
    if not low <= len(value) <= high: refuse('input-over-bound', 'array count')
    return value


def pointer(value, nonempty=False):
    text(value, int(nonempty), 1024)
    tokens = d.pointer_tokens(value)
    require(tokens is not None and len(tokens) <= 32, 'invalid or overlong pointer')
    return tokens


def timestamp(value): require(d.instant(value) is not None, 'timestamp has no instant')
def assertion(value, review=False):
    closed(value, {'actor', 'at', 'assertion'} if review else {'actor', 'at'})
    text(value['actor'], 1, 256); timestamp(value['at'])
    if review: text(value['assertion'], 1, 1024)


def retry(value, number):
    if number == 1: require(value is None, 'first attempt cannot retry')
    else: assertion(value)


def state(value):
    require(value['state'] in STATES, 'invalid instance/attempt state')
    require(value['failure'] in FAILURES if value['state'] == 'failed' else value['failure'] is None, 'failure/state disagree')


def generic_bounds(value, depth=0, max_depth=64):
    if isinstance(value, (dict, list)):
        if depth >= max_depth or len(value) > 4096: refuse('input-over-bound', 'workflow container bound')
        if isinstance(value, dict):
            for k in sorted(value):
                text(k); generic_bounds(value[k], depth+1, max_depth)
        else:
            for v in value: generic_bounds(v, depth+1, max_depth)
    elif isinstance(value, str):
        if len(value.encode('utf-8')) > 65536: refuse('input-over-bound', 'workflow string bound')
    elif value is not None and type(value) is not bool:
        integer(value, -(2**53-1), 2**53-1)


def same(a, b): return d.canon(a) == d.canon(b)
def overlap(a, b):
    aa, bb = d.pointer_tokens(a), d.pointer_tokens(b)
    return d.is_prefix(aa, bb) or d.is_prefix(bb, aa)


def span(raw, *keys):
    """Extract original object-value bytes only after the whole JSON passed strict reading."""
    held = raw.decode('utf-8')
    for key in keys:
        members = dict(d.top_level_members(held))
        if key not in members: return None
        held = members[key]
    return held.encode('utf-8')


@dataclass(frozen=True)
class Expectations:
    workflow_digest: str
    execution_digest: str
    runtime_digests: Mapping[str, str]
    historical_profiles: bytes


@dataclass
class Verification:
    report: dict | None
    exit_code: int
    detail: str = ''
    trace: list[dict] = field(default_factory=list)

    def report_bytes(self):
        return None if self.report is None else d.preparation_bytes(self.report) + b'\n'


@dataclass
class Stage:
    definition: dict
    frozen: dict
    published: dict
    bound: dict
    parsed: d.Dialect
    release: dict
    pack: dict


@dataclass
class RetainedAttempt:
    observation: dict
    files: dict[str, bytes]
    run: dict | None = None
    preparation: dict | None = None
    audit: dict | None = None
    facts: dict | None = None
    preparation_answer: dict | None = None


class Reader:
    def __init__(self, files, expectations, comparison_trace=False):
        if not isinstance(expectations, Expectations): raise OperationalError('Expectations are required independently of the bundle')
        if any(not d.is_digest(x) for x in (expectations.workflow_digest, expectations.execution_digest, *expectations.runtime_digests.values())):
            raise OperationalError('expected pins must be full SHA-256 digests')
        if not isinstance(expectations.historical_profiles, bytes): raise OperationalError('historical profiles must be separately supplied bytes')
        self.files = dict(files)
        if any(not isinstance(p, str) or not isinstance(b, bytes) for p, b in self.files.items()):
            raise OperationalError('files must map relative path strings to bytes')
        self.expect = expectations
        self.wanted_trace = comparison_trace
        self.trace = []
        self.parsed = {}
        self.stages = {}
        self.attempts = {}
        self.immutable = {}
        self.active = {}
        self.outputs = {}  # digest -> payload/envelope/disposition, including retired history
        self.reservations = {}
        self.retired = set()
        self.used_ids = set()
        self.reserved = 0
        self.record_count = 0
        self.revisions = {}
        self.consumed = set()
        self.case_values = {}
        self.inherited = {}
        self.stage_outputs = {}
        self.stage_status = {}
        self.selections = {}
        self.stage_order = []
        self.current_prefix = b''
        self.last_closed = b''

    def need(self, path):
        if path not in self.files: refuse('inventory-mismatch', f'missing artifact: {path}')
        return self.files[path]

    def load(self, path, maximum=None, canonical=False, literal=False, workflow=False):
        raw = self.need(path)
        if maximum is not None and len(raw) > maximum: refuse('input-over-bound', path)
        if path not in self.parsed:
            self.parsed[path] = d.read_document(raw, path, 32 if literal else 64)
        value = self.parsed[path]
        if workflow: generic_bounds(value, max_depth=32 if literal else 64)
        if canonical or literal:
            form = d.preparation_bytes(value) if literal else d.canon(value)
            if maximum is not None and len(form) > maximum: refuse('input-over-bound', path)
            require(raw == form, f'{path}: noncanonical bytes')
        return value

    def hash_check(self, raw, expected, where):
        check(d.digest_of(raw) == expected, 'digest-mismatch', where)

    def preflight(self):
        from . import workflow_reader_preflight
        workflow_reader_preflight.check(self)

    def preflight_dependent(self):
        if len(self.files) > 65536 or sum(map(len, self.files.values())) > 1073741824:
            refuse('input-over-bound', 'bundle ceiling')
        for path in self.files:
            require(path and not path.startswith('/') and '\\' not in path and all(p not in ('', '.', '..') for p in path.split('/')), 'unsafe recording path')
        self.workflow = self.load('workflow.json', 262144, canonical=True, workflow=True)
        self.execution = self.load('execution.json', 8388608, canonical=True, workflow=True)
        self.proof = self.load('admission-proof.json', 8388608, canonical=True, workflow=True)
        self.root_case = self.load('root-case.json', 1048576, literal=True, workflow=True)
        require(isinstance(self.root_case, dict), 'root case must be an object')
        for obj, selector, version in [(self.workflow,'workflowVersion',2), (self.execution,'executionVersion',2), (self.proof,'admissionProofVersion',1)]:
            require(isinstance(obj, dict) and selector in obj, 'missing version selector')
            if integer(obj[selector]) != version: refuse('version-unread', selector)
        closed(self.workflow, {'workflowVersion','stages','result','limits'})
        closed(self.workflow['limits'], LIMITS)
        self.limits = {k: integer(self.workflow['limits'][k],1,n) for k,n in LIMITS.items()}
        if sum(map(len,self.files.values())) > self.limits['maxBytes']: refuse('input-over-bound','final supplied bytes')
        stages = array(self.workflow['stages'],1,self.limits['maxStages'])
        for index,s in enumerate(stages):
            self.stage_form(s,index)
            ident(s['id']); require(s['id'] not in self.stage_order,'repeated stage')
            self.stage_order.append(s['id'])
        self.definitions = {s['id']:s for s in stages}
        self.children = {sid:[s['id'] for s in stages if s['input'].get('fromStage') == sid] for sid in self.stage_order}
        for s in stages: require(('selection' in s) == bool(self.children[s['id']]), 'selection belongs to producing stages only')
        require(self.workflow['result'] in self.children and not self.children[self.workflow['result']], 'result must be terminal')
        closed(self.execution, {'executionVersion','workflowDigest','execution','rootCaseDigest','frozen','instances','outputSets','selections','admissionProofDigest'})
        ident(self.execution['execution'])
        for k in ('workflowDigest','rootCaseDigest','admissionProofDigest'): digest(self.execution[k])
        frozen = array(self.execution['frozen'],len(stages),len(stages))
        for sid,f in zip(self.stage_order,frozen):
            closed(f,FROZEN); require(f['stage']==sid,'frozen order')
            for k in FROZEN-{'stage'}: digest(f[k], k=='bindingDocumentDigest')
        for i in array(self.execution['instances'],1,self.limits['maxInstances']): self.instance_form(i)
        require(len({i['id'] for i in self.execution['instances']}) == len(self.execution['instances']), 'duplicate instance')
        for sid,s in zip(self.stage_order,array(self.execution['outputSets'],len(stages),len(stages))):
            closed(s,{'stage','status','records'}); require(s['stage']==sid and s['status'] in ('closed','blocked'),'output set form')
            self.digest_list(s['records'])
        for value in array(self.execution['selections'],len(stages),len(stages)): digest(value,True)
        closed(self.proof, {'admissionProofVersion','workflowDigest','execution','rootCaseDigest','frozenDigest','rootInstance','epochBlocks'})
        for k in ('workflowDigest','rootCaseDigest','frozenDigest'): digest(self.proof[k])
        ident(self.proof['execution']); ident(self.proof['rootInstance'])
        blocks=array(self.proof['epochBlocks'],1,32)
        self.epochs=[]
        for i,b in enumerate(blocks):
            array(b,4096 if i<len(blocks)-1 else 1,4096); self.epochs.extend(b)
        for index,e in enumerate(self.epochs,1): self.epoch_form(e,index)
        # Forms of supplied retained workflow artifacts precede digest findings.
        for path in sorted(self.files):
            if re.fullmatch(r'selections/[^/]+/[1-9][0-9]*\.json',path):
                self.selection_form(self.load(path,65536,canonical=True,workflow=True))
            elif re.fullmatch(r'outputs/[^/]+/[^/]+/[0-9]+/record\.json',path):
                self.output_form(self.load(path,65536,canonical=True,workflow=True))
            elif path.startswith('outputs/') and path.endswith('/payload.json'):
                require(isinstance(self.load(path,1048576,literal=True,workflow=True),dict),'payload must be an object')
            elif path.startswith('instances/') and path.endswith('/case.json'):
                require(isinstance(self.load(path,1048576,literal=True,workflow=True),dict),'case must be an object')
            elif path.startswith('sets/') and path.endswith('.json'):
                obj=self.load(path,8388608,canonical=True,workflow=True)
                closed(obj,{'workflowDigest','execution','stage','records'})
                digest(obj['workflowDigest']); ident(obj['execution']); ident(obj['stage']); self.digest_list(obj['records'])
        self.load_stages()
        self.collect_attempts()

    def digest_list(self, values):
        array(values,0,self.limits['maxRecords'])
        for v in values: digest(v)
        require(len(set(values))==len(values),'duplicate digest')

    def stage_form(self,s,index,skip_ref=False):
        closed(s,{'id','dialect','pack','input','execution','caseBindings','outputs','relation'},{'selection'})
        if not skip_ref:
            ref=s['dialect']; require(isinstance(ref,dict),'dialect reference')
            if 'formatVersion' in ref:
                if ref['formatVersion'] not in ('2.0.0','3.0.0'): refuse('version-unread','named dialect selector')
                closed(ref,{'formatVersion','id','version','digest'}); text(ref['id'],1,1024)
                require(not any(ord(c)<=32 or ord(c)==127 for c in ref['id']),'named dialect id')
                require(isinstance(ref['version'],str) and re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)',ref['version']) is not None,'named artifact version')
            else:
                require('version' in ref,'missing dialect selector')
                if integer(ref['version']) not in (2,3): refuse('version-unread','dialect selector')
                closed(ref,{'version','digest'})
            digest(ref['digest'])
        closed(s['pack'],{'id','digest'}); text(s['pack']['id'],1,2048)
        require(bool(urlsplit(s['pack']['id']).scheme),'pack id must be absolute'); digest(s['pack']['digest'])
        if index==0:
            closed(s['input'],{'root'}); require(s['input']['root'] is True and s['execution']=='once' and s['caseBindings']==[],'root form')
        else:
            closed(s['input'],{'fromStage','selected'}); require(s['input']['fromStage'] in self.stage_order and s['input']['selected'] is True and s['execution']=='each-selected-record','dependent input')
            targets=[]
            for binding in array(s['caseBindings'],1,64):
                closed(binding,{'from','to','type','required'}); pointer(binding['from']); tokens=pointer(binding['to'],True)
                require(binding['type'] in ('string','integer','timestamp','boolean','object','array','null') and type(binding['required']) is bool,'binding type')
                require(not any(d.is_prefix(t,tokens) or d.is_prefix(tokens,t) for t in targets),'overlapping case destinations'); targets.append(tokens)
        closed(s['outputs'],{'pointer','cardinality'}); pointer(s['outputs']['pointer'],True)
        require(s['outputs']['cardinality'] in ('one','many'),'output cardinality')
        closed(s['relation'],{'label','direction'}); ident(s['relation']['label'])
        require(s['relation']['direction'] in ('output-to-parent','parent-to-output'),'relation direction')
        if 'selection' in s:
            selection=s['selection']; require(isinstance(selection,dict),'selection declaration')
            mode=selection.get('mode')
            closed(selection,{'mode','rule'} if mode=='disposition' else {'mode'})
            require(mode in ('reviewer','disposition'),'selection mode')
            if mode=='disposition':
                require(s['outputs']['cardinality']=='one','disposition selection requires one')
                self.rule_form(selection['rule'])

    def rule_form(self,r):
        require(isinstance(r,dict),'selection rule')
        closed(r,{'kind','outcomeId'} if r.get('kind')=='outcome' else {'kind'})
        require(r['kind'] in ('outcome','unresolved','not-applicable'),'selection rule kind')
        if r['kind']=='outcome': text(r['outcomeId'],1,256)

    def instance_form(self,i):
        closed(i,INSTANCE); ident(i['id']); require(i['stage'] in self.stage_order,'instance stage')
        for k in ('parentRecord','selectionDigest','caseDigest'): digest(i[k],True)
        require((i['parentRecord'] is None)==(i['selectionDigest'] is None),'paired parent pins')
        digest(i['inputDigest']); state(i)
        for n,a in enumerate(array(i['attempts'],0,self.limits['maxAttempts']),1):
            closed(a,ATTEMPT); require(integer(a['number'],1,16)==n,'attempt order'); state(a); retry(a['retry'],n)
            for k in ARTIFACT_PINS[:-1]: digest(a[k],True)
            if n<len(i['attempts']): require(a['state'] in ('failed','interrupted'),'earlier settled attempt')
        if i['attempts']: require(i['state']==i['attempts'][-1]['state'] and i['failure']==i['attempts'][-1]['failure'],'latest attempt state')
        else: require(i['state'] in ('failed','interrupted','cancelled'),'unbegun instance state')

    def epoch_form(self,e,n):
        require(isinstance(e,dict),'epoch')
        extra={'root':set(),'selection':{'upstreamStage','revision','selectionCoreDigest','childIds'},'fork':{'upstreamStage','revision','selectionCoreDigest','childIds'},
               'group':{'reservation','starts','deferred','cancelled','results'},'retry':{'start','results'}}
        require(e.get('kind') in extra,'epoch kind'); closed(e,{'number','previousProofDigest','kind'}|extra[e['kind']])
        require(integer(e['number'],1)==n and ((n==1)==(e['kind']=='root')),'epoch sequence/root')
        digest(e['previousProofDigest'])
        if e['kind'] in ('selection','fork'):
            require(e['upstreamStage'] in self.stage_order,'selection stage'); integer(e['revision'],1,16); digest(e['selectionCoreDigest'])
            if e['childIds'] is not None:
                for value in array(e['childIds']): ident(value)
                require(len(set(e['childIds']))==len(e['childIds']),'child ids repeated')
        if e['kind']=='group':
            require(integer(e['reservation'],1)<n,'reservation must be earlier')
            for value in array(e['deferred']): ident(value)
            for c in array(e['cancelled']):
                closed(c,{'instance','actor','at'}); ident(c['instance']); assertion({k:c[k] for k in ('actor','at')})
            starts=array(e['starts'])
        elif e['kind']=='retry': starts=[e['start']]
        else: return
        for start in starts:
            closed(start,{'instance','number','retry'}); ident(start['instance']); retry(start['retry'],integer(start['number'],1,16))
        for seq in ([x['instance'] for x in starts], e.get('deferred',[]), [x['instance'] for x in e.get('cancelled',[])]):
            require(len(set(seq))==len(seq),'repeated plan member')
        observations=array(e['results'],0,len(starts))
        if len(observations)<len(starts): require(n==len(self.epochs),'only final epoch may be open')
        for begin,o in zip(starts,observations):
            closed(o,{'instance','number','state','failure',*ARTIFACT_PINS}); ident(o['instance']); integer(o['number'],1,16)
            require(o['instance']==begin['instance'] and integer(o['number'])==integer(begin['number']),'result prefix order')
            require(o['state'] in ('evaluated','failed','interrupted','cancelled','suppressed'),'observation state')
            require(o['failure'] in ('acquisition-failed','preparation-failed','admission-refused','evaluation-error') if o['state']=='failed' else o['failure'] is None,'observation failure')
            for k in ARTIFACT_PINS: digest(o[k],True)
            require(o['auditSignaturesDigest'] is None or o['auditDigest'] is not None,'signature sidecar without audit')
            require(o['runDigest'] is not None or all(o[k] is None for k in ARTIFACT_PINS),'artifact without run')

    def selection_form(self,s):
        require(isinstance(s,dict),'selection record')
        closed(s,{'selectionVersion','workflowDigest','execution','upstreamStage','outputSetDigest','selected','mode','revision',
                  'review' if s.get('mode')=='reviewer' else 'rule'}, {'refusal'})
        if integer(s['selectionVersion'])!=1: refuse('version-unread','selection version')
        for k in ('workflowDigest','outputSetDigest'): digest(s[k])
        ident(s['execution']); require(s['upstreamStage'] in self.stage_order,'selection upstream stage'); integer(s['revision'],1,16)
        self.digest_list(s['selected']); require(s['mode'] in ('reviewer','disposition'),'selection mode')
        if s['mode']=='reviewer': assertion(s['review'],True)
        else: self.rule_form(s['rule'])
        if 'refusal' in s: require(s['refusal']=='limit-exceeded','selection refusal')

    def output_form(self,o):
        closed(o,{'outputRecordVersion','payloadDigest','lineage'})
        if integer(o['outputRecordVersion'])!=1: refuse('version-unread','output record version')
        digest(o['payloadDigest']); l=closed(o['lineage'],LINEAGE)
        for k in LINEAGE-{'execution','stage','instance','outputPointer','index','relation','influence'}:
            digest(l[k],k in ('bindingDocumentDigest','parentRecord','selectionDigest'))
        for k in ('execution','stage','instance'): ident(l[k])
        pointer(l['outputPointer'],True); integer(l['index'],0,4095)
        closed(l['relation'],{'label','direction'}); ident(l['relation']['label']); require(l['relation']['direction'] in ('output-to-parent','parent-to-output'),'lineage relation')
        closed(l['influence'],{'classes','generatedInfluence'}); classes=array(l['influence']['classes'],0,3)
        require(all(c in ('asserted','generated','record') for c in classes) and classes==sorted(set(classes)) and type(l['influence']['generatedInfluence']) is bool,'influence form')

    def load_stages(self):
        self.trusted_document=d.read_document(self.expect.historical_profiles,'independent historical profiles')
        if len(self.expect.historical_profiles)>65536: refuse('input-over-bound','historical profiles')
        self.trusted=d.parse_profiles(self.trusted_document)
        for sid,f in zip(self.stage_order,self.execution['frozen']):
            prefix=f'stages/{sid}/'
            published=self.load(prefix+'dialect.json',131072,canonical=True)
            bound=self.load(prefix+'bound-dialect.json',131072,canonical=True)
            parsed=d.parse_dialect(published)
            binding=self.load(prefix+'binding.json',65536,canonical=True) if f['bindingDocumentDigest'] is not None else None
            parsed=d.read_bound(parsed,binding,binding is not None)
            if parsed.unread: refuse('kind-unread',parsed.unread[0])
            d.parse_dialect(bound)
            profiles=self.load(prefix+'profiles.json',65536,canonical=True)
            d.parse_profiles(profiles)
            release=self.load(prefix+'release.json',24*1024*1024)
            require(isinstance(release,dict),'release object')
            encoding.release_bytes(release)  # check retained typed representation
            pack=self.load(prefix+'pack.json',10*1024*1024)
            require(isinstance(pack,dict),'pack object')
            self.stages[sid]=Stage(self.definitions[sid],f,published,bound,parsed,release,pack)

    def collect_attempts(self):
        # Derive prospective stage slots from contract-declared selections, never final inventory.
        self.identity_stage={self.proof['rootInstance']:self.stage_order[0]}
        for e in self.epochs:
            if e['kind'] in ('selection','fork') and e['childIds'] is not None:
                selection=self.load(f"selections/{e['upstreamStage']}/{integer(e['revision'])}.json",65536,canonical=True,workflow=True)
                self.selection_form(selection)
                slots=[sid for sid in self.children[e['upstreamStage']] for _ in selection['selected']]
                for iid,sid in zip(e['childIds'],slots): self.identity_stage.setdefault(iid,sid)
            for o in e.get('results',[]):
                iid,n=o['instance'],integer(o['number'])
                key=(iid,n)
                require(key not in self.attempts,'attempt observation repeated')
                prefix=f'instances/{iid}/attempts/{n}/'
                files={prefix+PIN_FILES[k]:self.need(prefix+PIN_FILES[k]) for k in ARTIFACT_PINS if o[k] is not None}
                retained=RetainedAttempt(o,files)
                if o['auditSignaturesDigest'] is not None and len(files[prefix+'audit-signatures.json'])>16384:
                    refuse('input-over-bound','signature sidecar')
                if o['runDigest'] is not None:
                    raw=files[prefix+'run.json']
                    # The pinned export ceilings are checked after extracting its base64 members.
                    if len(raw)>24*1024*1024: refuse('input-over-bound','retained run export')
                    export=self.load(prefix+'run.json')
                    require(isinstance(export,dict) and 'version' in export,'export selector')
                    version=integer(export['version'])
                    if version not in (2,3): refuse('version-unread','run export version')
                    self.run_export_form(export,o)
                    run=export['run']; retained.run=run
                    source=run['input']['source']
                    source_bytes=span(raw,'run','input','source','sources') or b'{}'
                    files[prefix+'sources.json']=self.need(prefix+'sources.json')
                    # Record expected bytes for phase-2 associations, not reconstructed JSON.
                    retained.source_bytes=source_bytes
                    retained.export=export
                    extra=0
                    for member,limit in [('auditBytes',8388608),('auditSignatures',16384)]:
                        if member in run:
                            decoded=self.decode_carrier(run[member])
                            if len(decoded)>limit: refuse('input-over-bound',member)
                            extra+=len(span(raw,'run',member) or b'')
                    if len(raw)-extra>8388608: refuse('input-over-bound','run export non-base64 bytes')
                    if 'audit' in run:
                        audit=d.record_of_export(raw)
                        require(audit is not None,'audit extraction')
                        if len(audit)>8388608: refuse('input-over-bound','audit')
                        retained.audit=d.read_record(audit); retained.audit_bytes=audit
                        require(d.json_equal(retained.audit,run['audit']),'audit bytes differ from parsed audit')
                        sid=self.identity_stage.get(iid)
                        self.disposition_form(retained.audit.get('disposition'),self.stages[sid].pack if sid in self.stages else None)
                    if 'preparation' in run['input']:
                        require(isinstance(run['input']['preparation'],dict),'preparation object')
                    if o['preparationDigest'] is not None:
                        retained.preparation=self.load(prefix+'preparation.json',8388608,literal=True)
                        for name in ('preparation.sha256','verified-at.txt'): files[prefix+name]=self.need(prefix+name)
                    if o['evaluationErrorDigest'] is not None:
                        error=self.load(prefix+'evaluation-error.json',8388608)
                        self.error_form(error)
                self.attempts[key]=retained

    @staticmethod
    def decode_carrier(value):
        require(isinstance(value,str),'base64 carrier type')
        try: decoded=base64.b64decode(value,validate=True)
        except (ValueError,TypeError) as error: raise d.malformed('invalid standard base64') from error
        require(base64.b64encode(decoded).decode()==value,'noncanonical standard base64')
        return decoded

    def run_export_form(self,export,observation=None):
        require(isinstance(export,dict) and 'version' in export,'export selector')
        version=integer(export['version'])
        if version not in (2,3): refuse('version-unread','run export version')
        closed(export,{'version','releaseDigest','release','run'})
        digest(export['releaseDigest']); require(isinstance(export['run'],dict),'retained run')
        run=export['run']
        require(isinstance(run.get('input'),dict),'run input')
        closed(run['input'],set(),{'preparation','facts','evidence','source'})
        source=run['input'].get('source'); closed(source,{'mapping'},{'case','sources','snapshot','mappingDigest','import'})
        if 'mappingDigest' in source: text(source['mappingDigest'])
        closed(run,{'schemaVersion','id','jobId','releaseId','revision','state','input','createdAt','requestedBy','attempt'},
               {'trigger','startedAt','finishedAt','result','audit','auditBytes','problem'})
        for key in ('schemaVersion','id','jobId','releaseId','state','createdAt','requestedBy'): text(run[key])
        for key in ('startedAt','finishedAt','problem'):
            if key in run: text(run[key])
        integer(run['revision']); integer(run['attempt'])
        if 'trigger' in run: raise OperationalError('retained trigger encoding is outside approved dependencies')
        require(('auditBytes' in run)==(version==3),'audit byte carrier/version')
        if observation is not None and observation.get('state')=='failed' and observation.get('failure') in ('preparation-failed','admission-refused'):
            require(d.instant(run.get('finishedAt')) is not None,'terminal preparation finishedAt must be an exact UTC-second instant')
        if 'preparation' in run['input']: require(isinstance(run['input']['preparation'],dict),'preparation object')
        if 'import' in source: self.import_form(source['import'])

    @staticmethod
    def import_form(value):
        # The retained import preserves the published document and its binding;
        # it is not an alternative source of trusted workflow inputs.
        closed(value,{'dialect','binding'})
        d.count_bounds(value['dialect'],{})
        published=d.parse_dialect(value['dialect'])
        require(published.version==3,'retained import requires dialect family 3')
        bound=d.read_bound(published,value['binding'],True)
        if bound.unread: refuse('kind-unread',bound.unread[0])

    def error_form(self,value):
        closed(value,{'outputVersion','tool','command','status','evaluationError','diagnostics'})
        require(value['outputVersion']=='2' and value['command']=='experimental evaluate' and value['status'] in ('error','unsupported'),'Runtime error envelope selector')
        closed(value['tool'],{'name','version'}); require(value['tool']['name']=='jpack','Runtime tool identity'); text(value['tool']['version'])
        error=closed(value['evaluationError'],{'class','phase','evaluatorSpecVersion'})
        require(error['class'] in ('pack-not-conformant','malformed-input','unsupported-required-extension','resource-exhaustion'),'Core error class')
        require(error['evaluatorSpecVersion']=='0.2.0-draft' and error['phase']==('evaluation' if error['class']=='resource-exhaustion' else 'preflight'),'Core error phase')
        require(isinstance(value['diagnostics'],list),'error diagnostics')
        for diagnostic in value['diagnostics']:
            closed(diagnostic,{'code','codeStability','layer','severity','instancePath','message'})
            for field in diagnostic.values(): require(isinstance(field,str),'diagnostic string')

    def disposition_form(self,value,pack):
        require(isinstance(value,dict),'Core disposition missing')
        kind=value.get('kind'); require(kind in ('outcome','not-applicable','unresolved'),'Core disposition kind')
        closed(value,{'kind','reasons','handoff','outcomeId'} if kind=='outcome' else {'kind','reasons','handoff'})
        reasons=array(value['reasons'],0,6)
        require(all(r in ('not-applicable','missing-required-evidence','unknown','conflict','no-match','exception-escalation') for r in reasons)
                and reasons==sorted(set(reasons)),'Core reason set')
        require((not reasons)==(kind=='outcome'),'Core outcome/reasons')
        if kind=='not-applicable': require(reasons==['not-applicable'],'not-applicable reason')
        if kind=='outcome':
            text(value['outcomeId'],1,256)
            if pack is not None: require(value['outcomeId'] in {o.get('id') for o in pack.get('outcomes',[]) if isinstance(o,dict)},'unknown outcome')
        h=value['handoff']; require(isinstance(h,dict),'Core handoff')
        closed(h,{'state','triggeredBy'} if h.get('state')=='requested' else {'state'})
        require(h['state'] in ('none','requested'),'Core handoff state')
        if h['state']=='requested':
            triggers=array(h['triggeredBy'],1,6)
            require(triggers==sorted(set(triggers)) and set(triggers)<=set(reasons),'Core handoff triggers')

    def pins(self):
        self.workflow_digest=d.digest_of(self.files['workflow.json'])
        self.hash_check(self.files['workflow.json'],self.expect.workflow_digest,'independent workflow pin')
        self.hash_check(self.files['execution.json'],self.expect.execution_digest,'independent execution pin')
        self.hash_check(self.files['admission-proof.json'],self.execution['admissionProofDigest'],'proof pin')
        self.hash_check(self.files['root-case.json'],self.execution['rootCaseDigest'],'root case pin')
        self.execution_id=self.execution['execution']
        check(self.execution['workflowDigest']==self.workflow_digest,'digest-mismatch','execution workflow')
        for k in ('workflowDigest','execution','rootCaseDigest'):
            check(self.proof[k]==self.execution[k],'digest-mismatch','proof root '+k)
        self.hash_check(d.canon(self.execution['frozen']),self.proof['frozenDigest'],'frozen digest')
        for name,pin in [('workflow',self.workflow_digest),('execution',self.expect.execution_digest),('admission-proof',self.execution['admissionProofDigest'])]:
            check(self.need(name+'.sha256')==(pin+'\n').encode(),'digest-mismatch',name+' sidecar')
        previous=self.prefix(0)
        for number,e in enumerate(self.epochs,1):
            self.hash_check(previous,e['previousProofDigest'],f'epoch {number} previous prefix')
            previous=self.prefix(number)
        for sid,stage in self.stages.items():
            f=stage.frozen; path=f'stages/{sid}/'; r=stage.release
            for key,file in [('publishedDialectDigest','dialect.json'),('boundDialectDigest','bound-dialect.json'),('packDigest','pack.json')]:
                self.hash_check(self.files[path+file],f[key],path+file)
            if f['bindingDocumentDigest'] is not None: self.hash_check(self.files[path+'binding.json'],f['bindingDocumentDigest'],path+'binding.json')
            self.hash_check(encoding.release_bytes(r),f['releaseDigest'],path+'release.json typed digest')
            if sid not in self.expect.runtime_digests: raise OperationalError('independent Runtime pin missing for '+sid)
            check(f['runtimeDigest']==self.expect.runtime_digests[sid],'digest-mismatch','independent Runtime pin '+sid)
            ref=stage.definition['dialect']
            check(ref['digest']==f['publishedDialectDigest'] and stage.definition['pack']['digest']==f['packDigest'],'digest-mismatch','declared stage pins')
            check(all(same(stage.published.get(k),v) for k,v in ref.items() if k!='digest'),'digest-mismatch','published dialect identity')
            check(stage.pack.get('id')==stage.definition['pack']['id'],'digest-mismatch','pack identity')
        for (iid,n),retained in self.attempts.items():
            o=retained.observation; path=f'instances/{iid}/attempts/{n}/'
            for pin in ARTIFACT_PINS:
                if o[pin] is not None: self.hash_check(retained.files[path+PIN_FILES[pin]],o[pin],path+PIN_FILES[pin])
            if retained.run is not None:
                export=retained.export
                self.hash_check(encoding.release_bytes(export['release']),export['releaseDigest'],'run embedded release digest')
                sid=self.identity_stage.get(iid)
                if sid in self.stages:
                    check(export['releaseDigest']==self.stages[sid].frozen['releaseDigest'],'digest-mismatch','run release association')
                check(retained.files[path+'sources.json']==retained.source_bytes,'digest-mismatch','exact sources span')
                if retained.preparation is not None:
                    check(d.preparation_bytes(retained.run['input'].get('preparation'))==retained.files[path+'preparation.json'],'digest-mismatch','embedded preparation')
                    check(retained.files[path+'preparation.sha256']==(o['preparationDigest']+'\n').encode(),'digest-mismatch','preparation sidecar')
                    check(retained.files[path+'verified-at.txt']==(retained.preparation.get('verifiedAt','')+'\n').encode(),'digest-mismatch','preparation timestamp sidecar')
                if o['auditDigest'] is not None:
                    check(getattr(retained,'audit_bytes',None)==retained.files[path+'audit.json'],'digest-mismatch','embedded audit bytes')
                if 'auditSignatures' in retained.run:
                    check(o['auditSignaturesDigest'] is not None and base64.b64decode(retained.run['auditSignatures'])==retained.files[path+'audit-signatures.json'],
                          'digest-mismatch','embedded signature sidecar')
        # Binding/profile consistency follows all identity checks.
        for sid,stage in self.stages.items():
            path=f'stages/{sid}/'; f=stage.frozen; r=stage.release
            check(same(stage.parsed.document,stage.bound),'stage-binding-mismatch','bound expansion '+sid)
            check('inputMapping' in r and same(encoding.mapping(r['inputMapping']),stage.bound),'stage-binding-mismatch','release embedded mapping '+sid)
            check(r.get('packDigest')==f['packDigest'] and r.get('runtimeDigest')==f['runtimeDigest'] and r.get('packId')==stage.pack.get('id'),
                  'stage-binding-mismatch','release pack/runtime '+sid)
            check(isinstance(r.get('pack'),str) and r['pack'].encode()==self.files[path+'pack.json'],'stage-binding-mismatch','release exact pack '+sid)
            check(self.files[path+'profiles.json']==d.canon(r.get('inputProfiles',[])),'stage-binding-mismatch','profiles are release inputProfiles')
            for profile in self.parsed[path+'profiles.json']:
                held=self.trusted.get(profile['id'])
                check(held is not None and same(held,profile),'stage-binding-mismatch','profile lacks independent historical trust')
            if 'formatVersion' in stage.published:
                check(r.get('dialect')=={k:stage.published[k] for k in ('id','version')}|{'digest':f['publishedDialectDigest']},
                      'stage-binding-mismatch','release named dialect identity')
            for source in stage.parsed.sources:
                try:
                    if source.research is not None: d.research_mismatch(source,self.trusted,None)
                    else:
                        profile=self.trusted.get(source.profile_id)
                        if profile is None or d.digest_of(d.canon(profile))!=source.profile_digest: raise d.Finding('profile-mismatch')
                        if 'endpointScope' in profile: raise d.Finding('profile-mismatch','endpointScope needs a page binding')
                        bound=stage.parsed.bound_from.get(source.name)
                        if bound is not None and (profile['shape'],profile['adapter']['name'])!=bound: raise d.Finding('profile-mismatch')
                        if d.request_misfit(source,profile) is not None or (('calculator' in profile)!=(source.calculation is not None)): raise d.Finding('profile-mismatch')
                    for kind,targets in [('fact',source.read.fact_targets),('evidence',source.read.evidence_targets)]:
                        for target in targets:
                            admitted=stage.parsed.admits.get((kind,target),['asserted','record'])
                            if (source.research is not None or self.trusted[source.profile_id]['class']=='generated') and admitted!=['generated']: raise d.Finding('profile-mismatch')
                            if self.trusted[source.profile_id]['class'] not in admitted: raise d.Finding('profile-mismatch')
                except d.Finding as error: finding('stage-binding-mismatch',f'{sid}: {error}')
            selection=stage.definition.get('selection',{})
            if selection.get('mode')=='disposition' and selection['rule']['kind']=='outcome':
                require(selection['rule']['outcomeId'] in {o.get('id') for o in stage.pack.get('outcomes',[]) if isinstance(o,dict)},'selection outcome not declared')
        for (iid,_),retained in self.attempts.items():
            sid=self.identity_stage.get(iid)
            if retained.run is None or sid not in self.stages: continue
            imported=retained.run['input']['source'].get('import')
            if imported is None: continue
            stage=self.stages[sid]
            check(same(imported['dialect'],stage.published)
                  and same(imported['binding'],self.parsed.get(f'stages/{sid}/binding.json')),
                  'stage-binding-mismatch','retained import differs from frozen published dialect/binding')

    def verify_preparations(self):
        first_finding=None
        for key,retained in self.attempts.items():
            iid,n=key; sid=self.identity_stage.get(iid)
            if sid not in self.stages: continue  # membership is diagnosed during replay, never read as success
            stage=self.stages[sid]
            if retained.preparation is None: continue
            case_path=f'instances/{iid}/case.json'; case=self.need(case_path)
            path=f'instances/{iid}/attempts/{n}/'
            answer=d.verify(self.files[f'stages/{sid}/dialect.json'],case,retained.files[path+'sources.json'],
                            self.expect.historical_profiles,retained.files[path+'preparation.json'],
                            retained.files.get(path+'audit.json'),retained.observation['auditDigest'] is not None,
                            self.files.get(f'stages/{sid}/binding.json'))
            retained.preparation_answer=answer.answer
            if 'refused' in answer.answer: refuse(answer.answer['refused'],answer.answer.get('detail',''))
            if 'finding' in answer.answer:
                if first_finding is None: first_finding=answer.answer.get('detail',answer.answer['finding'])
            else:
                # Preserve number literals for output payloads; .facts intentionally exposes plain values.
                recomputed=d.read_document(answer.preparation,'recomputed preparation')
                retained.facts={}
                for outcome in recomputed['outcomes']:
                    claim=outcome.get('claim')
                    if isinstance(claim,dict): self.merge_fact_objects(retained.facts,claim.get('facts',{}))
                retained.preparation=recomputed
        if first_finding is not None: finding('preparation-mismatch',first_finding)

    @staticmethod
    def merge_fact_objects(target,source):
        for k,v in source.items():
            if isinstance(v,dict) and isinstance(target.get(k),dict): Reader.merge_fact_objects(target[k],v)
            else: target[k]=copy.deepcopy(v)

    def prefix(self,count,results=None):
        epochs=copy.deepcopy(self.epochs[:count])
        if results is not None: epochs[-1]['results']=epochs[-1]['results'][:results]
        return d.canon({**self.proof,'epochBlocks':[epochs[i:i+4096] for i in range(0,len(epochs),4096)]})

    def put(self,path,data):
        if path in self.immutable and self.immutable[path]!=data: finding('inventory-mismatch','immutable path overwritten: '+path)
        self.immutable[path]=data

    def execution_value(self):
        return dict(executionVersion=2, workflowDigest=self.workflow_digest, execution=self.execution_id,
                    rootCaseDigest=self.execution['rootCaseDigest'], frozen=self.execution['frozen'],
                    instances=[i for sid in self.stage_order for i in self.active.values() if i['stage']==sid],
                    outputSets=[dict(stage=sid,status=self.stage_status[sid],records=self.stage_outputs[sid]) for sid in self.stage_order],
                    selections=[self.selections[sid] for sid in self.stage_order], admissionProofDigest=d.digest_of(self.current_prefix))

    def set_value(self,sid):
        return dict(workflowDigest=self.workflow_digest, execution=self.execution_id, stage=sid, records=self.stage_outputs[sid])

    def candidate(self,label,local_failure=False):
        files=dict(self.immutable)
        files['admission-proof.json']=self.current_prefix
        files['admission-proof.sha256']=(d.digest_of(self.current_prefix)+'\n').encode()
        for sid in self.stage_order: files[f'sets/{sid}.json']=d.canon(self.set_value(sid))
        execution=d.canon(self.execution_value())
        files['execution.json']=execution; files['execution.sha256']=(d.digest_of(execution)+'\n').encode()
        local=[]
        for path,data in files.items():
            bound=None
            if path in ('execution.json','admission-proof.json') or path.startswith('sets/'): bound=8388608
            elif path.startswith('selections/') or path.endswith('/record.json'): bound=65536
            elif path.endswith('/payload.json') or path.endswith('/case.json') or path=='root-case.json': bound=1048576
            if bound is not None and len(data)>bound: local.append(path)
        total=sum(map(len,files.values()))
        fits=not local_failure and not local and len(files)<=65536 and total<=self.limits['maxBytes'] and self.record_count<=self.limits['maxRecords'] and self.reserved<=self.limits['maxInstances']
        if self.wanted_trace:
            # Trace is experimental comparison output, never part of the portable report.
            if len(self.trace)>=8192 or sum(len(x['files']) for x in self.trace)+len(files)>1000000:
                raise OperationalError('local comparison-trace capacity exceeded; retry without trace')
            self.trace.append(dict(epoch=self.epoch_number, candidate=label, proofDigest=d.digest_of(self.current_prefix),
                                   bytes=total, paths=len(files), fits=fits, localOverBound=local, completeCandidate=not local_failure,
                                   retained=dict(instances=self.reserved,outputs=self.record_count,attempts=sum(self.begun.values())),
                                   active=dict(instances=len(self.active),outputs=sum(map(len,self.stage_outputs.values()))),
                                   files={p:dict(bytes=len(b),digest=d.digest_of(b)) for p,b in sorted(files.items())}))
        return files,fits

    def must_fit(self,label):
        files,fits=self.candidate(label)
        if not fits: raise OperationalError(f'{label}: mandatory recording cannot fit; no portable outcome')
        return files

    def checkpoint(self):
        return (copy.deepcopy(self.active),dict(self.immutable),copy.deepcopy(self.stage_outputs),dict(self.stage_status),
                dict(self.selections),self.reserved,self.record_count,dict(self.case_values),dict(self.inherited),dict(self.outputs),set(self.consumed))

    def restore(self,s):
        (self.active,self.immutable,self.stage_outputs,self.stage_status,self.selections,self.reserved,self.record_count,
         self.case_values,self.inherited,self.outputs,self.consumed)=s

    def replay(self):
        self.begun={}
        self.current_prefix=self.prefix(0)
        for number,e in enumerate(self.epochs,1):
            self.epoch_number=number
            if e['kind']=='root': self.root(e)
            elif e['kind'] in ('selection','fork'): self.selection_epoch(e)
            else: self.work_epoch(e)
        final=self.must_fit('final-required')
        # Compare active control before artifacts that a forged refusal has omitted.
        for path in sorted(final,key=lambda p:(p!='execution.json',p)):
            expected=final[path]; actual=self.need(path)
            code='output-mismatch' if path.startswith('outputs/') else 'case-mismatch' if path.startswith('instances/') and path.endswith('/case.json') else 'inventory-mismatch'
            check(actual==expected,code,'reconstructed bytes: '+path)
        extras=set(self.files)-set(final)
        check(all(p in ('README.md','trust.json','expected-report.json') or p.startswith('aux/') for p in extras),
              'inventory-mismatch','unexpected retained path(s): '+', '.join(sorted(extras)[:5]))
        complete=all(i['state'] in ('completed','completed-zero') for i in self.active.values()) and all(s=='closed' for s in self.stage_status.values())
        complete=complete and all(not self.children[sid] or sid in self.consumed for sid in self.stage_order)
        last=self.epochs[-1]
        if last['kind'] in ('group','retry'):
            starts=last.get('starts',[last.get('start')]); complete=complete and len(last['results'])==len(starts)
        return dict(result='reading',workflowDigest=self.workflow_digest,executionDigest=self.expect.execution_digest,
                    consistency='agrees', completion='complete' if complete else 'partial', preparations='agree',
                    authentication='not-established',dispositions='not-replayed',
                    counts=dict(stages=len(self.stage_order),instances=len(self.active),outputs=sum(map(len,self.stage_outputs.values())),
                                selections=sum(v is not None for v in self.selections.values())))

    def root(self,e):
        self.current_prefix=self.prefix(1)
        for p in ('workflow.json','workflow.sha256','root-case.json'): self.put(p,self.files[p])
        for sid in self.stage_order:
            for name in ('pack.json','dialect.json','bound-dialect.json','profiles.json','release.json'):
                p=f'stages/{sid}/{name}'; self.put(p,self.files[p])
            if self.stages[sid].frozen['bindingDocumentDigest'] is not None:
                p=f'stages/{sid}/binding.json'; self.put(p,self.files[p])
            self.stage_status[sid]='closed' if sid==self.stage_order[0] else 'blocked'
            self.stage_outputs[sid]=[]; self.selections[sid]=None
        iid=self.proof['rootInstance']; sid=self.stage_order[0]
        self.active[iid]=dict(id=iid,stage=sid,parentRecord=None,selectionDigest=None,inputDigest=self.execution['rootCaseDigest'],
                              caseDigest=self.execution['rootCaseDigest'],state='interrupted',failure=None,attempts=[])
        self.put(f'instances/{iid}/case.json',self.files['root-case.json']); self.case_values[iid]=self.root_case
        self.inherited[iid]={}; self.reserved=1; self.used_ids.add(iid); self.reservations[1]=[iid]
        self.must_fit('root')

    def projected(self,stage,parent):
        result={}; destinations=[]
        for b in stage.definition['caseBindings']:
            value=d.resolve(parent['payload'],b['from'])
            if value is d.ABSENT:
                if b['required']: return None,[],False
                continue
            kind=b['type']
            correct=(type(value) is bool if kind=='boolean' else isinstance(value,dict) if kind=='object' else isinstance(value,list) if kind=='array' else value is None if kind=='null' else d.of_type(value,kind))
            if not correct: return None,[],False
            d.write_at(result,b['to'],copy.deepcopy(value)); destinations.append(b['to'])
        try:
            generic_bounds(result,max_depth=32)
            raw=d.preparation_bytes(result)
            if len(raw)>1048576: return result,destinations,True
        except Problem as error:
            if error.code=='input-over-bound': return result,destinations,True
            raise
        return result,destinations,False

    def inherited_targets(self,stage,destinations,summary):
        parsed=stage.parsed; affected={}
        copy_spec=parsed.case_read.copy or {}
        for kind,member,key in [('fact','facts','target'),('evidence','evidence','requirement')]:
            for entry in copy_spec.get(member,[]):
                if any(overlap(entry['source'],p) for p in destinations): affected[(kind,entry[key])]=summary
        params={name for name,p in parsed.case_parameters.items() if any(overlap(p.pointer,to) for to in destinations)}
        affected_sources={}
        for source in parsed.sources:
            influence=bool(params) or any(p.pointer in affected_sources.get(p.origin,set()) for p in source.parameters.values())
            if influence:
                affected_sources[source.name]=set(source.read.fact_targets)
                for kind,targets in [('fact',source.read.fact_targets),('evidence',source.read.evidence_targets)]:
                    for t in targets: affected[(kind,t)]=summary
        return affected

    def selection_epoch(self,e):
        sid=e['upstreamStage']; revision=integer(e['revision']); fork=e['kind']=='fork'
        check(self.stage_status[sid]=='closed','selection-mismatch','selection on blocked stage')
        check((sid in self.consumed)==fork,'selection-mismatch','selection/fork consumption state')
        check(revision==self.revisions.get(sid,0)+1,'selection-mismatch','selection revision progression')
        path=f'selections/{sid}/{revision}.json'; supplied=self.parsed[path]
        core={k:v for k,v in supplied.items() if k!='refusal'}
        check(d.digest_of(d.canon(core))==e['selectionCoreDigest'],'selection-mismatch','selection core digest')
        expected=dict(selectionVersion=1,workflowDigest=self.workflow_digest,execution=self.execution_id,upstreamStage=sid,
                      outputSetDigest=d.digest_of(d.canon(self.set_value(sid))),selected=core['selected'],mode=self.definitions[sid]['selection']['mode'],revision=revision)
        if core['mode']=='reviewer': expected['review']=core['review']
        else: expected['rule']=self.definitions[sid]['selection']['rule']
        check(same(core,expected),'selection-mismatch','selection offered set, identity, or rule')
        selected=core['selected']; offered=self.stage_outputs[sid]
        check([r for r in offered if r in set(selected)]==selected,'selection-mismatch','ordered selected membership')
        if core['mode']=='disposition':
            rule=core['rule']; selected_expected=[]
            for rid in offered:
                disposition=self.outputs[rid]['disposition']
                if disposition['kind']==rule['kind'] and (rule['kind']!='outcome' or disposition['outcomeId']==rule['outcomeId']): selected_expected.append(rid)
            check(selected==selected_expected,'selection-mismatch','disposition-selected membership')
        self.revisions[sid]=revision
        if fork:
            affected={child for child in self.stage_order if self.descendant(child,sid)}
            for iid in list(self.active):
                if self.active[iid]['stage'] in affected: self.retired.add(iid); del self.active[iid]
            for child in affected:
                self.stage_status[child]='blocked'; self.stage_outputs[child]=[]; self.selections[child]=None; self.consumed.discard(child)
            self.consumed.discard(sid)
        self.current_prefix=self.prefix(self.epoch_number)
        slots=[(child,rid) for child in self.children[sid] for rid in selected]
        count_failed=self.reserved+len(slots)>self.limits['maxInstances']
        ids=e['childIds']
        check((ids is None)==count_failed,'inventory-mismatch','child allocation/count-refusal form')
        if ids is not None:
            check(len(ids)==len(slots) and not set(ids)&self.used_ids,'inventory-mismatch','fresh complete prospective ids')
            self.used_ids.update(ids)
        before=self.checkpoint(); local_failed=False; reserved_ids=[]
        if not count_failed:
            self.selections[sid]=d.digest_of(d.canon(core)); self.put(path,d.canon(core))
            for iid,(child,rid) in zip(ids,slots):
                stage=self.stages[child]; parent=self.outputs[rid]
                case,destinations,over=self.projected(stage,parent); local_failed |= over
                input_digest=d.digest_of(d.canon(dict(parentRecord=rid,selectionDigest=self.selections[sid],caseBindings=stage.definition['caseBindings'])))
                summary=parent['record']['lineage']['influence']
                affected={} if case is None else self.inherited_targets(stage,destinations,summary)
                denied=any(s['generatedInfluence'] and 'generated' not in stage.parsed.admits.get(target,[]) for target,s in affected.items())
                failure='projection-invalid' if case is None else 'admission-refused' if denied else None
                raw=None if case is None else d.preparation_bytes(case)
                self.active[iid]=dict(id=iid,stage=child,parentRecord=rid,selectionDigest=self.selections[sid],inputDigest=input_digest,
                                      caseDigest=None if raw is None else d.digest_of(raw),state='failed' if failure else 'interrupted',failure=failure,attempts=[])
                if raw is not None and not over: self.put(f'instances/{iid}/case.json',raw); self.case_values[iid]=case
                self.inherited[iid]=affected; reserved_ids.append(iid)
            self.reserved+=len(slots)
            for child in self.children[sid]: self.stage_status[child]='closed'
            self.consumed.add(sid)
            _,fits=self.candidate('selection-local-bound' if local_failed else 'selection-accept',local_failed)
            if fits:
                for iid in reserved_ids:
                    case_path=f'instances/{iid}/case.json'
                    if case_path in self.immutable:
                        check(self.need(case_path)==self.immutable[case_path],'case-mismatch','derived selected case '+iid)
        else: fits=False
        if not fits:
            self.restore(before)
            full={**core,'refusal':'limit-exceeded'}; self.selections[sid]=d.digest_of(d.canon(full)); self.put(path,d.canon(full))
            self.must_fit('selection-refuse')
        else:
            self.reservations[self.epoch_number]=reserved_ids
        check(('refusal' in supplied)==(not fits),'inventory-mismatch','selection claimed refusal differs from constructed candidate')
        check(self.files[path]==self.immutable[path],'selection-mismatch','retained selection bytes')

    def descendant(self,child,ancestor):
        while child!=self.stage_order[0]:
            child=self.definitions[child]['input']['fromStage']
            if child==ancestor: return True
        return False

    def work_epoch(self,e):
        if e['kind']=='group':
            reservation=integer(e['reservation'])
            check(reservation in self.reservations,'inventory-mismatch','unknown/unadmitted reservation')
            members=self.reservations[reservation]
            check(not any(i in self.retired for i in members),'inventory-mismatch','retired reservation')
            eligible=[i for i in members if i in self.active and self.active[i]['state']=='interrupted' and not self.active[i]['attempts']]
            starts=e['starts']; deferred=e['deferred']; cancelled=e['cancelled']
            groups=[[s['instance'] for s in starts],deferred,[c['instance'] for c in cancelled]]
            check(bool(starts or cancelled),'inventory-mismatch','defer-only group')
            all_members=[iid for group in groups for iid in group]
            check(len(all_members)==len(set(all_members)) and set(all_members)==set(eligible),'inventory-mismatch','eligible partition')
            for group in groups: check([i for i in eligible if i in group]==group,'inventory-mismatch','canonical plan order')
        else:
            starts=[e['start']]; cancelled=[]
            iid=starts[0]['instance']; check(iid in self.active,'inventory-mismatch','retry inactive identity')
            i=self.active[iid]
            check(i['state'] in ('failed','interrupted') and i['attempts'],'inventory-mismatch','retry requires unsuccessful begun instance')
        for entry in [*starts,*cancelled]:
            check(entry['instance'] in self.active,'inventory-mismatch','plan unknown instance')
            check(self.active[entry['instance']]['stage'] not in self.consumed,'inventory-mismatch','consumed stage cannot begin/cancel')
        for entry in cancelled:
            instance=self.active[entry['instance']]; instance['state']='cancelled'; instance['failure']=None
        for start in starts:
            instance=self.active[start['instance']]; n=len(instance['attempts'])+1
            check(n==integer(start['number']) and n<=self.limits['maxAttempts'],'inventory-mismatch','attempt ordinal/limit')
            attempt=dict(number=n,state='interrupted',failure=None,preparationDigest=None,auditDigest=None,runDigest=None,evaluationErrorDigest=None,retry=start['retry'])
            instance['attempts'].append(attempt); instance['state']='interrupted'; instance['failure']=None
            self.begun[instance['id']]=n
        self.current_prefix=self.prefix(self.epoch_number,0); self.must_fit('begin')
        cutoff=set()
        for j,o in enumerate(e['results'],1):
            self.current_prefix=self.prefix(self.epoch_number,j)
            self.observe(o,cutoff)

    def set_attempt_state(self,instance,state,failure):
        instance['state']=state; instance['failure']=failure
        instance['attempts'][-1]['state']=state; instance['attempts'][-1]['failure']=failure

    def observe(self,o,cutoff):
        iid=o['instance']; n=integer(o['number']); instance=self.active[iid]; sid=instance['stage']; stage=self.stages[sid]
        retained=self.attempts[(iid,n)]; attempt=instance['attempts'][-1]
        for k in ARTIFACT_PINS[:-1]: attempt[k]=o[k]
        for path,raw in retained.files.items(): self.put(path,raw)
        if retained.run is not None:
            run=retained.run; source=run['input']['source']
            check(d.preparation_bytes(source.get('case',{}))==d.preparation_bytes(self.case_values[iid]),'case-mismatch','retained source case')
            check(same(encoding.mapping(source['mapping']),stage.bound),'stage-binding-mismatch','retained run source mapping')
            if 'mappingDigest' in source: check(source['mappingDigest']==stage.frozen['boundDialectDigest'],'digest-mismatch','retained mapping digest')
            check(run.get('releaseId')==stage.release.get('id'),'inventory-mismatch','retained run release id')
        has_prep=retained.preparation is not None; has_audit=retained.audit is not None
        check((o['preparationDigest'] is not None)==has_prep and (o['auditDigest'] is not None)==has_audit,'inventory-mismatch','hidden/missing retained artifacts')
        if retained.run is not None:
            check(('preparation' in retained.run['input'])==has_prep,'inventory-mismatch','unpinned embedded preparation')
        if has_prep and retained.run is not None:
            for member,expected in [('facts',retained.facts),('evidence',self.preparation_evidence(retained.preparation))]:
                if member in retained.run['input']: check(d.json_equal(retained.run['input'][member],expected),'preparation-mismatch','retained '+member)
        if o['state']=='suppressed':
            check(all(o[k] is None for k in ARTIFACT_PINS) and sid in cutoff,'inventory-mismatch','unproved suppression')
            self.set_attempt_state(instance,'failed','limit-exceeded'); self.must_fit('suppressed'); return
        if o['state']!='evaluated':
            if retained.run is not None and isinstance(retained.run.get('result'),dict):
                result=retained.run['result']
                check('disposition' not in result,'inventory-mismatch','non-evaluated result hides disposition')
                check('evaluationError' not in result or (o['state']=='failed' and o['failure']=='evaluation-error'),
                      'inventory-mismatch','observation hides Core error')
            check(not has_audit,'inventory-mismatch','non-evaluated observation hides audit')
            if o['state']=='failed':
                check(retained.run is None or retained.run['state']=='failed','inventory-mismatch','failed run state')
                if o['failure'] in ('preparation-failed','admission-refused'):
                    check(retained.run is not None and not has_prep and o['evaluationErrorDigest'] is None,'inventory-mismatch','failed preparation phase')
                    self.failed_preparation(stage,retained,instance,o['failure'])
                elif o['failure']=='acquisition-failed': check(not has_prep and o['evaluationErrorDigest'] is None,'inventory-mismatch','acquisition failure has later material')
                elif o['failure']=='evaluation-error':
                    check(has_prep and o['evaluationErrorDigest'] is not None,'inventory-mismatch','Core error phase')
            else:
                check(o['evaluationErrorDigest'] is None,'inventory-mismatch','stop hides Core error')
                check(retained.run is None or retained.run['state']==o['state'],'inventory-mismatch','stop/run state')
                if retained.run is not None and isinstance(retained.run.get('result'),dict):
                    check('disposition' not in retained.run['result'] and 'evaluationError' not in retained.run['result'],'inventory-mismatch','stop hides result')
            self.set_attempt_state(instance,o['state'],o['failure']); self.must_fit('non-output-result'); return
        check(has_prep and has_audit and retained.run is not None and retained.run['state']=='completed' and o['evaluationErrorDigest'] is None,
              'inventory-mismatch','evaluated phase')
        result=retained.run.get('result')
        check(isinstance(result,dict) and same(result.get('disposition'),retained.audit['disposition']),'inventory-mismatch','retained result disposition')
        facts=retained.facts; value=d.resolve(facts,stage.definition['outputs']['pointer'])
        many=stage.definition['outputs']['cardinality']=='many'
        valid=(isinstance(value,list) and all(isinstance(x,dict) for x in value)) if many else isinstance(value,dict)
        if not valid:
            self.set_attempt_state(instance,'failed','output-invalid'); self.must_fit('invalid-output'); return
        payloads=value if many else [value]
        if sid in cutoff:
            self.set_attempt_state(instance,'failed','limit-exceeded'); self.must_fit('cutoff-refuse'); return
        before=self.checkpoint()
        local_failed=False
        for index,payload in enumerate(payloads):
            if index>4095: local_failed=True; break
            try: generic_bounds(payload,max_depth=32)
            except Problem as error:
                if error.code=='input-over-bound': local_failed=True; break
                raise
            payload_raw=d.preparation_bytes(payload)
            if len(payload_raw)>1048576: local_failed=True; break
            record=self.output_record(instance,stage,retained,payload_raw,index)
            record_raw=d.canon(record)
            if len(record_raw)>65536: local_failed=True; break
            path=f'outputs/{sid}/{iid}/{index}/'
            self.put(path+'payload.json',payload_raw); self.put(path+'record.json',record_raw)
            rid=d.digest_of(record_raw); self.stage_outputs[sid].append(rid)
            self.outputs[rid]=dict(payload=payload,record=record,disposition=retained.audit['disposition'])
            self.record_count+=1
        # Retried earlier siblings re-enter their original selected-parent position.
        order={iid:index for index,iid in enumerate(self.active)}
        self.stage_outputs[sid].sort(key=lambda rid:(order[self.outputs[rid]['record']['lineage']['instance']], integer(self.outputs[rid]['record']['lineage']['index'])))
        self.set_attempt_state(instance,'completed' if payloads else 'completed-zero',None)
        _,fits=self.candidate('output-local-bound' if local_failed else 'output-accept',local_failed)
        if not fits:
            self.restore(before); instance=self.active[iid]
            self.set_attempt_state(instance,'failed','limit-exceeded'); self.must_fit('output-refuse'); cutoff.add(sid)
        else:
            for index in range(len(payloads)):
                for name in ('payload.json','record.json'):
                    path=f'outputs/{sid}/{iid}/{index}/{name}'
                    check(path in self.files and self.files[path]==self.immutable[path],'output-mismatch','emitted artifact '+path)

    @staticmethod
    def preparation_evidence(preparation):
        result={}
        for outcome in preparation['outcomes']:
            if isinstance(outcome.get('claim'),dict): result.update(outcome['claim'].get('evidenceAvailability',{}))
        return result

    def failed_preparation(self,stage,retained,instance,failure):
        at=retained.run['finishedAt']  # Exact terminal-check instant under RFC 0024's added writer constraint.
        prefix=f"instances/{instance['id']}/attempts/{integer(retained.observation['number'])}/"
        acquisitions=d.read_document(retained.files[prefix+'sources.json'],'failed preparation acquisitions')
        try:
            d.recompute(stage.parsed,self.case_values[instance['id']],acquisitions,self.trusted,at)
        except d.Finding as error:
            terminal={'profile-mismatch','parameter-invalid','read-failed','acquisition-unexpected',
                      'acquisition-invalid','acquisition-stale','acquisition-sessions','calculation-invalid'}
            if error.name=='admission-refused': derived='admission-refused'
            elif error.name in terminal: derived='preparation-failed'
            elif error.name=='acquisition-missing':
                # The reused verifier exposes findings as names plus detail strings.
                # Recognize its two explicit missing forms; never infer terminal
                # failure from an arbitrary exception or an absent planned source.
                pending={f'acquisition-missing: {source.name}' for source in stage.parsed.sources if source.name not in acquisitions}
                missing_response=set()
                for source in stage.parsed.sources:
                    if source.research is None or source.name not in acquisitions: continue
                    responses=acquisitions[source.name]['response']['result']['responses']
                    for index,response in enumerate(responses):
                        if 'result' not in response:
                            missing_response.add(f'acquisition-missing: {source.name}: retained response {index} has no result')
                if str(error) in pending: finding('inventory-mismatch','source acquisition is still pending')
                if str(error) not in missing_response:
                    raise OperationalError('unrecognized acquisition-missing context: '+str(error)) from error
                derived='preparation-failed'
            else: raise OperationalError('unrecognized terminal derivation finding: '+str(error)) from error
            check(derived==failure,'inventory-mismatch','derived terminal failure does not match observation')
            return
        finding('inventory-mismatch','retained inputs successfully prepare; no terminal failure')

    def output_record(self,instance,stage,retained,payload_raw,index):
        sid=instance['stage']; declared=stage.definition['outputs']['pointer']
        full=declared+('/'+str(index) if stage.definition['outputs']['cardinality']=='many' else '')
        classes=set(); generated=False
        for entry in retained.preparation['lineage']:
            if entry['kind']=='fact' and overlap(entry['target'],full):
                classes.add(entry['class']); generated |= entry['generatedInfluence']
                inherited=self.inherited[instance['id']].get(('fact',entry['target']))
                if inherited: classes.update(inherited['classes']); generated |= inherited['generatedInfluence']
        f=stage.frozen; o=retained.observation
        lineage=dict(workflowDigest=self.workflow_digest,execution=self.execution_id,stage=sid,instance=instance['id'],
                     publishedDialectDigest=f['publishedDialectDigest'],bindingDocumentDigest=f['bindingDocumentDigest'],boundDialectDigest=f['boundDialectDigest'],
                     packDigest=f['packDigest'],releaseDigest=f['releaseDigest'],preparationDigest=o['preparationDigest'],auditDigest=o['auditDigest'],
                     outputPointer=declared,index=index,rootCaseDigest=self.execution['rootCaseDigest'],caseDigest=instance['caseDigest'],
                     parentRecord=instance['parentRecord'],selectionDigest=instance['selectionDigest'],relation=stage.definition['relation'],
                     influence=dict(classes=sorted(classes),generatedInfluence=bool(generated)))
        return dict(outputRecordVersion=1,payloadDigest=d.digest_of(payload_raw),lineage=lineage)


def verify(files: Mapping[str,bytes], expectations: Expectations, *, comparison_trace=False) -> Verification:
    """Read supplied bytes offline; no filesystem, network, acquisition or policy execution.

    Unknown/unimplemented dependency semantics return exit 3 with no portable report.
    Optional trace records independently reconstructed per-path hashes, never input totals.
    """
    reader=None
    try:
        reader=Reader(files,expectations,comparison_trace)
        reader.preflight(); reader.pins(); reader.verify_preparations()
        report=reader.replay()
        return Verification(report,0,trace=reader.trace)
    except Problem as error:
        return Verification({'result':error.result,error.result:error.code},1 if error.result=='refusal' else 2,error.detail,reader.trace if reader else [])
    except d.Refused as error:
        return Verification({'result':'refusal','refusal':error.name},1,str(error),reader.trace if reader else [])
    except (OperationalError,encoding.EncodingUnsupported) as error:
        return Verification(None,3,str(error),reader.trace if reader else [])
    except (OSError,TimeoutError,NotImplementedError,MemoryError) as error:
        return Verification(None,3,'reader operational inability: '+str(error),reader.trace if reader else [])
    except d.OutsideDomain as error:
        return Verification({'result':'refusal','refusal':'input-malformed'},1,'value outside canonical domain',reader.trace if reader else [])
    except (KeyError,TypeError,ValueError,AttributeError,RecursionError) as error:
        # No malformed public shape may become a reading. Focused tests also run
        # Reader's phases directly so coding errors cannot hide behind this boundary.
        return Verification({'result':'refusal','refusal':'input-malformed'},1,f'bad retained form: {error}',reader.trace if reader else [])

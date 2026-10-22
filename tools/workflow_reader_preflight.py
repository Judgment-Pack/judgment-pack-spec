"""All-document refusal precedence for the experimental workflow reader.

This pass collects independent form errors before replay's dependent checks. It
never repairs input, supplies trusted content, or establishes a reading itself.
"""
from . import dialect_verify as d
from . import workflow_reader_encoding as encoding


def check(reader):
    from . import workflow_reader as w
    errors=[]; operational=[]
    priority={'input-over-bound':0,'input-malformed':1,'version-unread':2,'inventory-mismatch':3,'kind-unread':4}

    def capture(action):
        try: return action()
        except w.Problem as error:
            if error.result!='refusal': raise
            errors.append(error)
        except d.Refused as error: errors.append(w.Problem('refusal',error.name,str(error)))
        except d.OutsideDomain: errors.append(w.Problem('refusal','input-malformed','outside canonical domain'))
        except (encoding.EncodingUnsupported,w.OperationalError) as error:
            operational.append(error)
        except (KeyError,TypeError,ValueError,AttributeError,RecursionError) as error:
            errors.append(w.Problem('refusal','input-malformed',f'bad retained form: {error}'))
        return None

    def problem(code,detail): errors.append(w.Problem('refusal',code,detail))
    def members(value): return value if isinstance(value,list) else []
    def obj(value): return value if isinstance(value,dict) else {}
    def ints(value,default):
        if isinstance(value,d.Num) and value.is_integer(): return d.integer_of(value)
        return value if type(value) is int else default
    def count(value,limit,where):
        if isinstance(value,(list,dict)) and len(value)>limit: problem('input-over-bound',where)
    def strings_and_counts(value,depth=0,maximum=64):
        if isinstance(value,(dict,list)):
            if depth>=maximum or len(value)>4096: problem('input-over-bound','workflow nesting/container')
            for key,member in value.items() if isinstance(value,dict) else enumerate(value):
                if isinstance(key,str) and len(key.encode())>65536: problem('input-over-bound','workflow key')
                strings_and_counts(member,depth+1,maximum)
        elif isinstance(value,str) and len(value.encode())>65536: problem('input-over-bound','workflow string')
    def selector(value,name,allowed):
        if not isinstance(value,dict) or name not in value:
            problem('input-malformed','missing '+name); return False
        number=capture(lambda:w.integer(value[name]))
        if number is None: return False
        if number not in allowed:
            problem('version-unread',name); return False
        return True
    def file_form(path):
        # maximum, canonical, literal, workflow-value bounds
        if path=='workflow.json': return 262144,True,False,True
        if path in ('execution.json','admission-proof.json') or path.startswith('sets/') and path.endswith('.json'): return 8388608,True,False,True
        if path=='root-case.json' or path.startswith('instances/') and path.endswith('/case.json') or path.startswith('outputs/') and path.endswith('/payload.json'): return 1048576,False,True,True
        if path.startswith('selections/') and path.endswith('.json') or path.startswith('outputs/') and path.endswith('/record.json'): return 65536,True,False,True
        if path.startswith('stages/'):
            name=path.rsplit('/',1)[-1]
            if name in ('dialect.json','bound-dialect.json'): return 131072,True,False,False
            if name in ('binding.json','profiles.json'): return 65536,True,False,False
            if name=='pack.json': return 10485760,False,False,False
            if name=='release.json': return 25165824,False,False,False
        if path.startswith('instances/') and '/attempts/' in path:
            name=path.rsplit('/',1)[-1]
            if name=='run.json': return 25165824,False,False,False
            if name=='preparation.json': return 8388608,False,True,False
            if name in ('sources.json','audit.json','evaluation-error.json'): return 8388608,False,False,False
        return None

    total=sum(map(len,reader.files.values()))
    if len(reader.files)>65536 or total>1073741824: problem('input-over-bound','bundle ceiling')
    if len(reader.expect.historical_profiles)>65536: problem('input-over-bound','historical profiles')
    # Retained signature material is opaque JSONL (possibly unreadable). Its
    # exact bytes, ownership and pin are checked later; authentication is not.
    for path,raw in reader.files.items():
        if path.startswith('instances/') and '/attempts/' in path and path.endswith('/audit-signatures.json') and len(raw)>16384:
            problem('input-over-bound',path)
    formats={p:form for p in sorted(reader.files) if (form:=file_form(p)) is not None}
    # Bounds measured on bytes do not depend on JSON being readable elsewhere.
    for path,(maximum,canonical,literal,workflow) in formats.items():
        raw=reader.files[path]
        if len(raw)>maximum: problem('input-over-bound',path)
        capture(lambda raw=raw,path=path,literal=literal:d.measure(raw,path,32 if literal else 64))
    capture(lambda:d.measure(reader.expect.historical_profiles,'historical profiles',64))
    documents={}
    for path in formats:
        value=capture(lambda path=path:d.read_document(reader.files[path],path,32 if formats[path][2] else 64))
        if value is not None: documents[path]=value
        elif not any(e.detail.endswith(path) for e in errors):
            # A literal JSON null is still a parsed document for its form check.
            if reader.files[path].strip()==b'null': documents[path]=None
    trusted=capture(lambda:d.read_document(reader.expect.historical_profiles,'historical profiles'))
    workflow=obj(documents.get('workflow.json')); execution=obj(documents.get('execution.json')); proof=obj(documents.get('admission-proof.json'))
    limits=obj(workflow.get('limits'))
    maximum_bytes=ints(limits.get('maxBytes'),None)
    if maximum_bytes is not None and total>maximum_bytes: problem('input-over-bound','final supplied bytes')
    for path,(maximum,canonical,literal,is_workflow) in formats.items():
        if path not in documents: continue
        value=documents[path]
        if is_workflow: strings_and_counts(value,maximum=32 if literal else 64)
        if canonical or literal:
            serialized=capture(lambda value=value,literal=literal:d.preparation_bytes(value) if literal else d.canon(value))
            if serialized is not None:
                if len(serialized)>maximum: problem('input-over-bound',path+' canonical bytes')
                if serialized!=reader.files[path]: problem('input-malformed',path+' noncanonical bytes')
        if path.endswith('/record.json'): count(obj(obj(value).get('lineage')).get('influence',{}).get('classes') if isinstance(obj(obj(value).get('lineage')).get('influence'),dict) else None,3,'influence classes')
        if is_workflow: capture(lambda value=value,literal=literal:w.generic_bounds(value,max_depth=32 if literal else 64))
    count(workflow.get('stages'),ints(limits.get('maxStages'),32),'stage count')
    for stage in members(workflow.get('stages')): count(obj(stage).get('caseBindings'),64,'case bindings')
    count(execution.get('instances'),ints(limits.get('maxInstances'),4096),'active instance count')
    for instance in members(execution.get('instances')): count(obj(instance).get('attempts'),ints(limits.get('maxAttempts'),16),'attempt count')
    for output_set in members(execution.get('outputSets')): count(obj(output_set).get('records'),ints(limits.get('maxRecords'),4096),'record count')
    for key in ('frozen','outputSets','selections'):
        if isinstance(workflow.get('stages'),list): count(execution.get(key),len(workflow['stages']),key+' count')
    count(proof.get('epochBlocks'),32,'epoch block count')
    # Dependency counted bounds are collected even if a different file is malformed.
    for path,value in documents.items():
        if path.endswith('/dialect.json') or path.endswith('/bound-dialect.json'):
            capture(lambda value=value:d.count_bounds(value,{}))
        if path.endswith('/profiles.json'): capture(lambda value=value:d.count_bounds({}, {}, value))
    capture(lambda:d.count_bounds({}, {}, trusted))

    probe=w.Reader(reader.files,reader.expect)
    probe.limits={key:ints(limits.get(key),default) for key,default in w.LIMITS.items()}
    stages=members(workflow.get('stages'))
    names=[s['id'] for s in stages if isinstance(s,dict) and isinstance(s.get('id'),str)]
    # Only type/form context, never a reconstruction baseline. Unknown workflow
    # versions cannot impose their undisclosed membership grammar on an execution.
    workflow_readable='workflow.json' in documents and selector(documents['workflow.json'],'workflowVersion',{2})
    probe.stage_order=names if workflow_readable else [f['stage'] for f in members(execution.get('frozen')) if isinstance(f,dict) and isinstance(f.get('stage'),str)]
    probe.epochs=[e for block in members(proof.get('epochBlocks')) for e in members(block)]
    if workflow_readable:
        capture(lambda:w.closed(workflow,{'workflowVersion','stages','result','limits'}))
        capture(lambda:w.closed(limits,w.LIMITS))
        for name,maximum in w.LIMITS.items(): capture(lambda name=name,maximum=maximum:w.integer(limits.get(name),1,maximum))
        capture(lambda:w.array(workflow.get('stages'),1,probe.limits['maxStages']))
        probe.stage_order=[]
        for index,stage in enumerate(stages):
            capture(lambda stage=stage,index=index:probe.stage_form(stage,index))
            # A nested unknown dialect selector does not mask another stage field.
            capture(lambda stage=stage,index=index:probe.stage_form(stage,index,skip_ref=True))
            if isinstance(stage,dict) and isinstance(stage.get('id'),str):
                capture(lambda stage=stage:w.ident(stage['id']))
                if stage['id'] in probe.stage_order: problem('input-malformed','duplicate stage')
                probe.stage_order.append(stage['id'])
        children={sid:[obj(s).get('id') for s in stages if obj(obj(s).get('input')).get('fromStage')==sid] for sid in probe.stage_order}
        for stage in stages:
            if isinstance(stage,dict) and stage.get('id') in children:
                capture(lambda stage=stage:w.require(('selection' in stage)==bool(children[stage['id']]),'selection belongs to producing stages'))
        capture(lambda:w.require(workflow.get('result') in children and not children[workflow['result']],'terminal result'))
    if 'execution.json' in documents and selector(documents['execution.json'],'executionVersion',{2}):
        capture(lambda:w.closed(execution,{'executionVersion','workflowDigest','execution','rootCaseDigest','frozen','instances','outputSets','selections','admissionProofDigest'}))
        capture(lambda:w.ident(execution.get('execution')))
        for key in ('workflowDigest','rootCaseDigest','admissionProofDigest'): capture(lambda key=key:w.digest(execution.get(key)))
        expected_stages=len(probe.stage_order)
        for key in ('frozen','outputSets','selections'):
            capture(lambda key=key:w.array(execution.get(key),expected_stages,expected_stages))
        capture(lambda:w.array(execution.get('instances'),1,probe.limits['maxInstances']))
        for index,f in enumerate(members(execution.get('frozen'))):
            capture(lambda f=f:w.closed(f,w.FROZEN))
            capture(lambda f=f,index=index:w.require(index<len(probe.stage_order) and obj(f).get('stage')==probe.stage_order[index],'frozen order'))
            for key in w.FROZEN-{'stage'}: capture(lambda f=f,key=key:w.digest(obj(f).get(key),key=='bindingDocumentDigest'))
        for instance in members(execution.get('instances')): capture(lambda instance=instance:probe.instance_form(instance))
        capture(lambda:w.require(len({obj(i).get('id') for i in members(execution.get('instances'))})==len(members(execution.get('instances'))),'duplicate instance'))
        for index,output_set in enumerate(members(execution.get('outputSets'))):
            capture(lambda output_set=output_set:w.closed(output_set,{'stage','status','records'}))
            capture(lambda output_set=output_set,index=index:w.require(index<len(probe.stage_order) and obj(output_set).get('stage')==probe.stage_order[index],'set order'))
            capture(lambda output_set=output_set:w.require(obj(output_set).get('status') in ('closed','blocked'),'set status'))
            capture(lambda output_set=output_set:probe.digest_list(obj(output_set).get('records')))
        for pin in members(execution.get('selections')): capture(lambda pin=pin:w.digest(pin,True))
        for key in ('frozen','instances','outputSets','selections'): capture(lambda key=key:w.array(execution.get(key)))
    if 'admission-proof.json' in documents and selector(documents['admission-proof.json'],'admissionProofVersion',{1}):
        capture(lambda:w.closed(proof,{'admissionProofVersion','workflowDigest','execution','rootCaseDigest','frozenDigest','rootInstance','epochBlocks'}))
        for key in ('workflowDigest','rootCaseDigest','frozenDigest'): capture(lambda key=key:w.digest(proof.get(key)))
        for key in ('execution','rootInstance'): capture(lambda key=key:w.ident(proof.get(key)))
        capture(lambda:w.array(proof.get('epochBlocks'),1,32))
        for i,block in enumerate(members(proof.get('epochBlocks'))): capture(lambda i=i,block=block:w.array(block,4096 if i<len(proof['epochBlocks'])-1 else 1,4096))
        for i,epoch in enumerate(probe.epochs,1): capture(lambda i=i,epoch=epoch:probe.epoch_form(epoch,i))
    identity_stage={}
    if names and isinstance(proof.get('rootInstance'),str): identity_stage[proof['rootInstance']]=names[0]
    for epoch in probe.epochs:
        e=obj(epoch)
        if e.get('kind') not in ('selection','fork') or not isinstance(e.get('childIds'),list): continue
        sid=e.get('upstreamStage'); revision=ints(e.get('revision'),0)
        selection=obj(documents.get(f'selections/{sid}/{revision}.json'))
        children=[obj(stage).get('id') for stage in stages if obj(obj(stage).get('input')).get('fromStage')==sid]
        slots=[child for child in children for _ in members(selection.get('selected'))]
        for iid,child in zip(e['childIds'],slots):
            if isinstance(iid,str) and isinstance(child,str): identity_stage.setdefault(iid,child)
    for path in documents:
        if not path.startswith('instances/') or not path.endswith('/sources.json'): continue
        parts=path.split('/'); iid=parts[1]; sid=identity_stage.get(iid)
        if sid is not None:
            envelope=sum(len(reader.files.get(p,b'')) for p in (f'stages/{sid}/dialect.json',f'instances/{iid}/case.json',path))
            if envelope>d.ENVELOPE_BYTES: problem('input-over-bound','preparation input envelope '+path)
    observations={}
    for epoch in probe.epochs:
        for observation in members(obj(epoch).get('results')):
            o=obj(observation); iid=o.get('instance'); n=ints(o.get('number'),None)
            if isinstance(iid,str) and n is not None: observations[f'instances/{iid}/attempts/{n}/run.json']=o
    dialects={}
    for path,value in documents.items():
        name=path.rsplit('/',1)[-1]
        if name in ('dialect.json','bound-dialect.json') and path.startswith('stages/'):
            parsed=capture(lambda value=value:d.parse_dialect(value))
            if parsed is not None:
                dialects[path]=parsed
                if parsed.unread: problem('kind-unread',parsed.unread[0])
        elif name=='profiles.json' and path.startswith('stages/'): capture(lambda value=value:d.parse_profiles(value))
        elif name=='release.json' and path.startswith('stages/'): capture(lambda value=value:encoding.release_bytes(value))
        elif path.startswith('selections/'):
            count(obj(value).get('selected'),probe.limits['maxRecords'],'selected record count')
            if selector(value,'selectionVersion',{1}): capture(lambda value=value:probe.selection_form(value))
        elif name=='record.json' and path.startswith('outputs/'):
            if selector(value,'outputRecordVersion',{1}): capture(lambda value=value:probe.output_form(value))
        elif path=='root-case.json' or name in ('case.json','payload.json') and path.startswith(('instances/','outputs/')):
            capture(lambda value=value:w.require(isinstance(value,dict),'case/payload object'))
        elif path.startswith('sets/'):
            capture(lambda value=value:w.closed(value,{'workflowDigest','execution','stage','records'}))
            capture(lambda value=value:w.digest(obj(value).get('workflowDigest')))
            for key in ('execution','stage'): capture(lambda value=value,key=key:w.ident(obj(value).get(key)))
            capture(lambda value=value:probe.digest_list(obj(value).get('records')))
        elif name=='evaluation-error.json': capture(lambda value=value:probe.error_form(value))
        elif name=='preparation.json':
            capture(lambda value=value:w.require(isinstance(value,dict),'preparation object'))
            capture(lambda value=value:w.timestamp(obj(value).get('verifiedAt')))
        elif name=='run.json':
            readable=selector(value,'version',{2,3})
            if readable: capture(lambda path=path,value=value:probe.run_export_form(value,observations.get(path)))
            run=obj(obj(value).get('run'))
            # Carrier byte ceilings remain measurable even for an unread version.
            extra=0
            for member,limit in [('auditBytes',8388608),('auditSignatures',16384)]:
                if isinstance(run.get(member),str):
                    decoded=capture(lambda member=member:probe.decode_carrier(run[member]))
                    if decoded is not None and len(decoded)>limit: problem('input-over-bound',member)
                    token=capture(lambda member=member:w.span(reader.files[path],'run',member))
                    extra+=len(token or b'')
            if len(reader.files[path])-extra>8388608: problem('input-over-bound','run non-base64 bytes')
            if not readable: continue
            if 'audit' in run:
                audit=capture(lambda path=path:d.record_of_export(reader.files[path]))
                if audit is not None:
                    capture(lambda audit=audit:d.measure(audit,'embedded audit',64))
                    audit_value=capture(lambda audit=audit:d.read_record(audit))
                    disposition=obj(obj(audit_value).get('disposition'))
                    count(disposition.get('reasons'),6,'Core reasons')
                    count(obj(disposition.get('handoff')).get('triggeredBy'),6,'Core handoff triggers')
                    capture(lambda disposition=disposition:probe.disposition_form(disposition,None))
            source=obj(obj(run.get('input')).get('source'))
            if 'import' in source:
                # Collect nested counted limits even if an unrelated optional
                # run field already failed its form check.
                capture(lambda source=source:d.count_bounds(obj(source['import']).get('dialect'),{}))
                capture(lambda source=source:probe.import_form(source['import']))
            mapping=source.get('mapping')
            parsed=capture(lambda mapping=mapping:d.parse_dialect(mapping)) if mapping is not None else None
            source_path=path.rsplit('/',1)[0]+'/sources.json'
            acquired=documents.get(source_path)
            if acquired is not None:
                capture(lambda acquired=acquired:w.require(isinstance(acquired,dict),'sources object'))
                capture(lambda mapping=mapping,acquired=acquired:d.count_bounds(mapping,acquired,trusted))
                if parsed is not None:
                    research={source.name:source.research for source in parsed.sources if source.research is not None}
                    for key,member in obj(acquired).items(): capture(lambda key=key,member=member:d.check_acquisition_form(key,member,research.get(key)))
        elif name=='audit.json':
            disposition=obj(obj(value).get('disposition'))
            count(disposition.get('reasons'),6,'Core reasons')
            count(obj(disposition.get('handoff')).get('triggeredBy'),6,'Core handoff triggers')
            capture(lambda path=path:probe.disposition_form(d.read_record(reader.files[path]).get('disposition'),None))
    capture(lambda:d.parse_profiles(trusted))
    for path,parsed in dialects.items():
        if not path.endswith('/dialect.json'): continue
        binding_path=path.rsplit('/',1)[0]+'/binding.json'
        if binding_path in documents: capture(lambda parsed=parsed,binding_path=binding_path:d.read_bound(parsed,documents[binding_path],True))
    # The dependent pass checks cross-object membership and missing pins as well;
    # include its first error without allowing it to hide a global higher priority.
    capture(reader.preflight_dependent)
    if errors:
        raise min(enumerate(errors),key=lambda item:(priority.get(item[1].code,5),item[0]))[1]
    if operational: raise operational[0]

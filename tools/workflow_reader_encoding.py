"""Pinned retained Release encoding dependency for the workflow reader experiment.

Data declarations and encoding methods only, Runner 66e264e1e44f665e52b056be1b70864a27927338.
No workflow or preparation-verification algorithm is imported from Runner.
"""
from __future__ import annotations

from . import dialect_verify as d


class EncodingUnsupported(Exception):
    pass


# Fields: (type, omitempty). Raw JSON preserves presence, including explicit null.
def fields(required='', optional='', **complex_fields):
    result = {k: ('str', False) for k in required.split()}
    result.update({k: ('str', True) for k in optional.split()})
    result.update(complex_fields)
    return result


SCHEMAS = {
    'identity': fields('id version digest'),
    'adapter': fields('name version digest'),
    'calculator': fields('name version'),
    'research': fields(capabilities=(['str'], False), model=('?str', True)),
    'profile': fields('id publicKey class source authority shape', adapter=('adapter', False),
                      endpoint=('?str', False), tools=(['str'], True),
                      calculator=('?calculator', True), research=('?research', True)),
    'parameter': fields('pointer type', 'from'),
    'fact': fields('target source'),
    'evidence': fields('requirement source'),
    'case': fields(parameters=({'*': 'parameter'}, True), facts=(['fact'], False), evidence=(['evidence'], False)),
    'copy': fields(facts=(['fact'], False), evidence=(['evidence'], False)),
    'read': fields(unwrap=(['str'], True), copy=('?copy', True), rule=('raw', True), sources=('raw', True)),
    'calculation': fields(inputs=({'*': 'str'}, False), tables=({'*': 'int'}, False)),
    'admits': fields(facts=({'*': ['str']}, True), evidence=({'*': ['str']}, True)),
    'source': fields('name kind', 'provider profile profileDigest', maxAge=('int', True),
                     parameters=({'*': 'parameter'}, True), arguments=('raw', True), read=('read', False),
                     calculation=('?calculation', True)),
    'import': fields(dialect=('raw', False), binding=('raw', False)),
    'sourceValue': fields(snapshot=('raw', True), response=('raw', True)),
    'sourceInput': fields(case=('raw', True), sources=({'*': 'sourceValue'}, True), mapping=('mapping', False),
                          snapshot=('raw', True), mappingDigest=('str', True), **{'import': ('?import', True)}),
    'citation': fields('sessionId signature', callIndex=('int', False)),
    'dependency': fields('parameter source pointer'),
    'calculationInput': fields('name parameter source pointer'),
    'calculationLineage': fields('status', calculator=('calculator', False), inputs=(['calculationInput'], False), asOf=({'*': 'str'}, False)),
    'lineage': fields('target kind source class status reason readDigest', generatedInfluence=('bool', False),
                      present=('bool', False), basis=(['str'], False), candidateFrom=(['str'], True),
                      dependencies=(['dependency'], True), receipt=('?citation', True), receipts=('?citations', True),
                      calculation=('?calculationLineage', True)),
    'outcome': fields('name status reason', parameters=('raw', False), arguments=('raw', True), claim=('raw', False)),
    'preparation': fields('verifiedAt mappingDigest verification', version=('int', False), cites=(['citation'], False),
                          lineage=(['lineage'], False), outcomes=(['outcome'], False)),
    'input': fields(preparation=('?preparation', True), facts=('raw', True), evidence=('raw', True), source=('?sourceInput', True)),
    'testSource': fields('packKey', suiteRevision=('int', False), caseNames=({'*': 'str'}, True), exploratoryCount=('int', True)),
    'tests': fields('status matrix matrixDigest packDigest runtimeDigest checkedAt', 'problem', source=('?testSource', True), report=('raw', True)),
    'release': fields('schemaVersion id pack packDigest packId packVersion title runtimeDigest createdAt config lock tests',
                      dialect=('?identity', True), inputProfiles=(['profile'], True), mappingWarnings=(['str'], True),
                      validation=('raw', False), sample=('input', False), preview=('raw', False),
                      testEvidence=('?tests', True), inputMapping=('?mapping', True)),
}
for _name in ('platform operation shape record method path query body headers statement bindings url question constraints model evidence fields capabilities webProfiles').split():
    SCHEMAS['source'][_name] = ('raw', True)


def _zero(kind):
    if kind == 'str': return ''
    if kind == 'int': return 0
    if kind == 'bool': return False
    if kind == 'raw' or isinstance(kind, (list, dict)) or (isinstance(kind, str) and kind.startswith('?')): return None
    return {}


def _plain_integer(value):
    if isinstance(value, d.Num) and value.is_integer(): return d.integer_of(value)
    if type(value) is int: return value
    raise d.malformed('pinned typed encoding expected an integer')


def project(kind, value):
    """Decode/encode the approved retained type; unspecified fields have Go zero values.

    Unknown members are discarded by typed decoding, as json.Unmarshal does; this
    never replaces closed-form checking of workflow or dialect documents.
    """
    if isinstance(kind, str) and kind.startswith('?'):
        return None if value is None else project(kind[1:], value)
    if value is None:
        value = _zero(kind)
    if kind == 'raw': return value
    if kind == 'str':
        if not isinstance(value, str): raise d.malformed('pinned typed encoding expected a string')
        return value
    if kind == 'int': return _plain_integer(value)
    if kind == 'bool':
        if type(value) is not bool: raise d.malformed('pinned typed encoding expected a boolean')
        return value
    if kind == 'citations': kind = ['citation']
    if isinstance(kind, list):
        if value is None: return None
        if not isinstance(value, list): raise d.malformed('pinned typed encoding expected an array')
        return [project(kind[0], x) for x in value]
    if isinstance(kind, dict):
        if value is None: return None
        if not isinstance(value, dict): raise d.malformed('pinned typed encoding expected an object')
        return {k: project(kind['*'], v) for k, v in value.items()}
    if kind == 'mapping': return mapping(value)
    if not isinstance(value, dict): raise d.malformed('pinned retained struct is not an object')
    result = {}
    for name, (field_kind, omit) in SCHEMAS[kind].items():
        member = project(field_kind, value.get(name, _zero(field_kind)))
        # RawMessage's null is nonempty bytes; a pointer to an empty value is nonnil.
        absent = name not in value if field_kind == 'raw' else (member is None if isinstance(field_kind, str) and field_kind.startswith('?') else not member)
        if not omit or not absent: result[name] = member
    return result


def mapping(value):
    if not isinstance(value, dict): raise d.malformed('release mapping must be an object')
    named = 'formatVersion' in value
    result = {}
    for key, kind, omit in [('case', '?case', not named), ('sources', ['source'], True), ('admits', '?admits', True),
                             ('unmapped', ['str'], True), ('unmappedEvidence', ['str'], True)]:
        member = project(kind, value.get(key, _zero(kind)))
        if not omit or (member is not None if isinstance(kind, str) and kind.startswith('?') else bool(member)):
            result[key] = member
    if named:
        result.update({k: project('str', value.get(k)) for k in ('formatVersion', 'id', 'version')})
    else:
        version = project('int', value.get('version'))
        result['version'] = version
        if version != 3:
            result.update(provider=project('str', value.get('provider')), facts=project(['fact'], value.get('facts')),
                          evidence=project(['evidence'], value.get('evidence')))
    return result


def retained_bytes(value):
    """Pinned encode -> UseNumber decode -> json.Marshal retained representation.

    This is not dialect canon: RawMessage number literals survive, including -0
    and decimal/exponent spellings. The final json.Marshal sorts object keys and
    escapes HTML plus U+2028/U+2029, as the reused preparation string writer does.
    Typed integer fields have already been decoded by project().
    """
    def render(member):
        if isinstance(member,dict):
            return '{'+','.join(d._preparation_string(key)+':'+render(member[key]) for key in sorted(member))+'}'
        if isinstance(member,list): return '['+','.join(render(item) for item in member)+']'
        if isinstance(member,str): return d._preparation_string(member)
        if member is None: return 'null'
        if member is True: return 'true'
        if member is False: return 'false'
        if isinstance(member,d.Num): return member.literal
        if type(member) is int: return str(member)
        raise EncodingUnsupported('retained JSON value type is not implemented: '+type(member).__name__)
    return render(value).encode('utf-8')


def release_bytes(value):
    return retained_bytes(project('release',value))

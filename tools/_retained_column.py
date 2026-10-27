# Promoted RFC0029 interpreter. Normative rules: spec/retained-column.md.
#!/usr/bin/env python3
"""Draft RFC0029 preview only; no acquisition, preparation or adoption claim."""
import json
import hashlib
import math
import re
import struct
import sys
from fractions import Fraction as Q

DEC = re.compile(r'-?(0|[1-9][0-9]*)(\.[0-9]+)?\Z', re.ASCII)
NUM = re.compile(r'-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?\Z', re.ASCII)
INT = re.compile(r'-?(0|[1-9][0-9]*)\Z', re.ASCII)
SPACE = '\t\n\v\f\r \u0085\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000'
SAFE = 9007199254740991
STATUSES = {'supported', 'interpretation', 'missing', 'conflicting', 'inaccessible', 'stale'}
META = {'name', 'url', 'website', 'company_id', 'company_name', 'company_url'}
# SIMPLE_LOWER_TABLE is inserted below from Unicode 15.0 simple case ranges.
# Unicode 15.0 simple lowercase data, derived from Go unicode CaseRanges.
# Go Authors / Unicode data; Go BSD-3-Clause distribution, tables SHA256 6a88d48746c4b2c471cc04ae40559694b734770212e6f5ea5f1962adb0c0bdb1.
SIMPLE_LOWER_TABLE = [[65,90,32],[192,214,32],[216,222,32],[256,303,"alternate"],[304,304,-199],[306,311,"alternate"],[313,328,"alternate"],[330,375,"alternate"],[376,376,-121],[377,382,"alternate"],[385,385,210],[386,389,"alternate"],[390,390,206],[391,392,"alternate"],[393,394,205],[395,396,"alternate"],[398,398,79],[399,399,202],[400,400,203],[401,402,"alternate"],[403,403,205],[404,404,207],[406,406,211],[407,407,209],[408,409,"alternate"],[412,412,211],[413,413,213],[415,415,214],[416,421,"alternate"],[422,422,218],[423,424,"alternate"],[425,425,218],[428,429,"alternate"],[430,430,218],[431,432,"alternate"],[433,434,217],[435,438,"alternate"],[439,439,219],[440,441,"alternate"],[444,445,"alternate"],[452,452,2],[453,453,1],[455,455,2],[456,456,1],[458,458,2],[459,459,1],[461,476,"alternate"],[478,495,"alternate"],[497,497,2],[498,498,1],[500,501,"alternate"],[502,502,-97],[503,503,-56],[504,543,"alternate"],[544,544,-130],[546,563,"alternate"],[570,570,10795],[571,572,"alternate"],[573,573,-163],[574,574,10792],[577,578,"alternate"],[579,579,-195],[580,580,69],[581,581,71],[582,591,"alternate"],[880,883,"alternate"],[886,887,"alternate"],[895,895,116],[902,902,38],[904,906,37],[908,908,64],[910,911,63],[913,929,32],[931,939,32],[975,975,8],[984,1007,"alternate"],[1012,1012,-60],[1015,1016,"alternate"],[1017,1017,-7],[1018,1019,"alternate"],[1021,1023,-130],[1024,1039,80],[1040,1071,32],[1120,1153,"alternate"],[1162,1215,"alternate"],[1216,1216,15],[1217,1230,"alternate"],[1232,1327,"alternate"],[1329,1366,48],[4256,4293,7264],[4295,4295,7264],[4301,4301,7264],[5024,5103,38864],[5104,5109,8],[7312,7354,-3008],[7357,7359,-3008],[7680,7829,"alternate"],[7838,7838,-7615],[7840,7935,"alternate"],[7944,7951,-8],[7960,7965,-8],[7976,7983,-8],[7992,7999,-8],[8008,8013,-8],[8025,8025,-8],[8027,8027,-8],[8029,8029,-8],[8031,8031,-8],[8040,8047,-8],[8072,8079,-8],[8088,8095,-8],[8104,8111,-8],[8120,8121,-8],[8122,8123,-74],[8124,8124,-9],[8136,8139,-86],[8140,8140,-9],[8152,8153,-8],[8154,8155,-100],[8168,8169,-8],[8170,8171,-112],[8172,8172,-7],[8184,8185,-128],[8186,8187,-126],[8188,8188,-9],[8486,8486,-7517],[8490,8490,-8383],[8491,8491,-8262],[8498,8498,28],[8544,8559,16],[8579,8580,"alternate"],[9398,9423,26],[11264,11311,48],[11360,11361,"alternate"],[11362,11362,-10743],[11363,11363,-3814],[11364,11364,-10727],[11367,11372,"alternate"],[11373,11373,-10780],[11374,11374,-10749],[11375,11375,-10783],[11376,11376,-10782],[11378,11379,"alternate"],[11381,11382,"alternate"],[11390,11391,-10815],[11392,11491,"alternate"],[11499,11502,"alternate"],[11506,11507,"alternate"],[42560,42605,"alternate"],[42624,42651,"alternate"],[42786,42799,"alternate"],[42802,42863,"alternate"],[42873,42876,"alternate"],[42877,42877,-35332],[42878,42887,"alternate"],[42891,42892,"alternate"],[42893,42893,-42280],[42896,42899,"alternate"],[42902,42921,"alternate"],[42922,42922,-42308],[42923,42923,-42319],[42924,42924,-42315],[42925,42925,-42305],[42926,42926,-42308],[42928,42928,-42258],[42929,42929,-42282],[42930,42930,-42261],[42931,42931,928],[42932,42947,"alternate"],[42948,42948,-48],[42949,42949,-42307],[42950,42950,-35384],[42951,42954,"alternate"],[42960,42961,"alternate"],[42966,42969,"alternate"],[42997,42998,"alternate"],[65313,65338,32],[66560,66599,40],[66736,66771,40],[66928,66938,39],[66940,66954,39],[66956,66962,39],[66964,66965,39],[68736,68786,64],[71840,71871,32],[93760,93791,32],[125184,125217,34]]

class Refusal(Exception):
    pass

class Number:
    def __init__(self, text):
        self.text = text


def fail(code='input-malformed'):
    raise Refusal(code)


def lower15(text):
    out = []
    for char in text:
        point = ord(char)
        for low, high, delta in SIMPLE_LOWER_TABLE:
            if low <= point <= high:
                point = low + ((point-low) | 1) if delta == 'alternate' else point + delta
                break
        out.append(chr(point))
    return ''.join(out)


def scalar(value):
    if isinstance(value, str):
        return not any(0xd800 <= ord(c) <= 0xdfff for c in value)
    if isinstance(value, dict):
        return all(scalar(k) and scalar(v) for k, v in value.items())
    if isinstance(value, list):
        return all(map(scalar, value))
    return True


def parse(text, *, strict=True, folded=False, depth=64):
    # Scan before recursive parsing; strings do not consume nesting budget.
    level = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '[{':
            level += 1
            if level > depth + 1:
                fail('input-over-bound')
        elif char in ']}':
            level -= 1
    def pairs(items):
        obj, names = {}, set()
        for key, value in items:
            name = lower15(key) if folded else key
            if name in names:
                fail()
            names.add(name)
            obj[key] = value
        return obj
    def constant(_):
        fail()
    try:
        value = json.loads(text, parse_int=Number, parse_float=Number,
                           parse_constant=constant, object_pairs_hook=pairs)
    except (ValueError, RecursionError):
        fail()
    def bounded(v, level=0):
        if level > depth:
            fail('input-over-bound')
        if isinstance(v, dict):
            for child in v.values():
                bounded(child, level+1)
        elif isinstance(v, list):
            for child in v:
                bounded(child, level+1)
    bounded(value)
    if strict and not scalar(value):
        fail()
    return value


def length(text):
    return len(text.encode('utf-8'))


def closed(obj, required, optional=()):
    if not isinstance(obj, dict) or not set(required) <= obj.keys() or obj.keys() - set(required) - set(optional):
        fail()


def string(text, limit, nonempty=False):
    if not isinstance(text, str) or not scalar(text) or (nonempty and not text):
        fail()
    if length(text) > limit:
        fail('input-over-bound')


def validate(rule, frame, profile, raw_frame_bytes=None):
    if profile not in ('base', 'extended'):
        fail()
    # The host still must account for the complete dialect/case/acquisition envelope.
    ceiling = 2097152 if profile == 'base' else 4194304
    if (raw_frame_bytes if raw_frame_bytes is not None else length(json.dumps(frame, ensure_ascii=False, separators=(',', ':')))) > ceiling:
        fail('input-over-bound')
    closed(rule, ['contractVersion', 'column', 'kind'], ['trueValue', 'falseValue'])
    if rule['contractVersion'] != '1' or rule['kind'] not in ('text', 'decimal', 'number', 'boolean', 'research-value', 'evidence-availability'):
        fail()
    string(rule['column'], 160, True)
    if rule['kind'] == 'boolean':
        for key in ('trueValue', 'falseValue'):
            if key not in rule:
                fail()
            string(rule[key], 160, True)
            if not rule[key].strip(SPACE):
                fail()
        if rule['trueValue'] == rule['falseValue']:
            fail()
    elif 'trueValue' in rule or 'falseValue' in rule:
        fail()
    closed(frame, ['contractVersion', 'origin', 'values', 'research'])
    if frame['contractVersion'] != '1' or frame['origin'] not in ('asserted', 'generated'):
        fail()
    values = frame['values']
    if not isinstance(values, dict):
        fail()
    if len(values) > 1000:
        fail('input-over-bound')
    for key, value in values.items():
        string(key, 160, True)
        if value is not None:
            string(value, 16000 if frame['origin'] == 'asserted' else 524288)
    research = frame['research']
    if frame['origin'] == 'asserted':
        if research is not None:
            fail()
        return
    closed(research, ['recordRecipeRevision', 'declaration', 'fields'])
    string(research['recordRecipeRevision'], 160, True)
    declaration = research['declaration']
    if declaration is not None:
        closed(declaration, ['recipeRevision', 'fields'])
        string(declaration['recipeRevision'], 160, True)
        if not isinstance(declaration['fields'], list):
            fail()
        if len(declaration['fields']) > 1000:
            fail('input-over-bound')
        names = set()
        for entry in declaration['fields']:
            closed(entry, ['name', 'fieldJson'])
            string(entry['name'], 160, True)
            string(entry['fieldJson'], 16384)
            if entry['name'] in names:
                fail()
            names.add(entry['name'])
            field = parse(entry['fieldJson'], depth=32)
            if not isinstance(field, dict) or field.get('name') != entry['name'] or not isinstance(field.get('type'), str):
                fail()
    if not isinstance(research['fields'], dict):
        fail()
    if len(research['fields']) > 1000:
        fail('input-over-bound')
    for key, entry in research['fields'].items():
        string(key, 160, True)
        closed(entry, ['status'], ['valueJson'])
        if not isinstance(entry['status'], str) or entry['status'] not in STATUSES:
            fail()
        if 'valueJson' in entry:
            string(entry['valueJson'], 4194304)


def power(exponent):
    return Q(10 ** exponent) if exponent >= 0 else Q(1, 10 ** -exponent)


def shortest(value):
    """Exact decimal rational chosen inside the binary64 roundtrip interval."""
    value = abs(value)
    if not math.isfinite(value):
        fail()
    if value == 0:
        return Q(0)
    x = Q(value)
    low = (x + Q(math.nextafter(value, 0.0))) / 2
    high = (x + Q(math.nextafter(value, math.inf))) / 2
    bits = struct.unpack('>Q', struct.pack('>d', value))[0]
    inclusive = bits % 2 == 0
    magnitude = len(str(x.numerator)) - len(str(x.denominator))
    while x < power(magnitude):
        magnitude -= 1
    while x >= power(magnitude + 1):
        magnitude += 1
    for digits in range(1, 18):
        found = []
        for exponent in range(magnitude - digits - 1, magnitude - digits + 3):
            unit = power(exponent)
            lo, hi, center = low / unit, high / unit, x / unit
            first = -(-lo.numerator // lo.denominator)
            last = hi.numerator // hi.denominator
            if not inclusive and Q(first) == lo:
                first += 1
            if not inclusive and Q(last) == hi:
                last -= 1
            first, last = max(first, 10 ** (digits - 1)), min(last, 10 ** digits - 1)
            floor = center.numerator // center.denominator
            for a in {first, first+1, last-1, last, floor-1, floor, floor+1, floor+2}:
                if first <= a <= last and a % 10:
                    q = a * unit
                    found.append((abs(q-x), a % 2, q))
        if found:
            return min(found)[2]
    fail()


def is_integer(value):
    return isinstance(value, Number) and INT.fullmatch(value.text) is not None and abs(int(value.text)) <= SAFE


def decimal(value):
    return isinstance(value, str) and length(value) <= 128 and DEC.fullmatch(value) is not None


def typed(raw, kind):
    if not raw or length(raw) > 524288 or (kind in ('string', 'number') and length(raw) > 8192):
        return False
    try:
        value = parse(raw, strict=kind not in ('string', 'number'), folded=True, depth=64)
        if kind in ('text', 'string'):
            return isinstance(value, str) and (kind == 'string' or length(value) <= 8192)
        if kind == 'number':
            return isinstance(value, Number) and math.isfinite(float(value.text))
        if kind == 'integer':
            return is_integer(value)
        if kind == 'decimal':
            return decimal(value)
        if kind == 'boolean':
            return isinstance(value, bool)
        if kind == 'text-list':
            return isinstance(value, list) and len(value) <= 64 and all(isinstance(s, str) and length(s) <= 1024 for s in value)
        if kind == 'range' and isinstance(value, dict) and set(value) == {'min', 'max'}:
            a, b = value['min'], value['max']
            if is_integer(a) and is_integer(b):
                return int(a.text) <= int(b.text)
            return decimal(a) and decimal(b) and Q(a) <= Q(b)
    except (Refusal, ValueError, OverflowError):
        return False
    return False


def admissible(raw):
    try:
        value = parse(raw)
        def walk(v):
            if isinstance(v, Number):
                return is_integer(v)
            if isinstance(v, list):
                return all(map(walk, v))
            if isinstance(v, dict):
                return all(map(walk, v.values()))
            return v is None or isinstance(v, (str, bool))
        return walk(value)
    except Refusal:
        return False


def preview(rule, frame):
    kind, column = rule['kind'], rule['column']
    def issue(code):
        return {'issues': [code], 'claimAdmissible': False}
    def omit(reason):
        return {'issues': [], 'omitted': reason, 'claimAdmissible': False}
    def result(raw):
        return {'issues': [], 'valueJson': raw, 'claimAdmissible': admissible(raw)}
    research = frame['research']
    if kind == 'research-value':
        if frame['origin'] != 'generated':
            return issue('research-context')
        if column in META:
            return issue('research-metadata')
        declaration = research['declaration']
        if declaration is None or declaration['recipeRevision'] != research['recordRecipeRevision']:
            return issue('research-declaration')
        original = next((parse(e['fieldJson']) for e in declaration['fields'] if e['name'] == column), None)
        if original is None:
            return issue('research-field')
        entry = research['fields'].get(column)
        if entry is None or entry['status'] not in ('supported', 'interpretation'):
            return omit('unavailable')
        raw = entry.get('valueJson', '')
        return result(raw) if typed(raw, original['type']) else issue('research-type')
    if column not in frame['values']:
        return omit('missing')
    value = frame['values'][column]
    if value is None:
        return omit('legacy-null')
    if not value.strip(SPACE):
        return omit('blank')
    if frame['origin'] == 'generated':
        entry = research['fields'].get(column)
        if entry is not None and entry['status'] not in ('supported', 'interpretation'):
            return omit('unavailable')
    encoded = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    if kind == 'text':
        return result(encoded)
    if kind == 'decimal':
        return result(encoded) if decimal(value) else issue('decimal-encoding')
    if kind == 'evidence-availability':
        return result(encoded) if value in ('present', 'absent', 'unknown') else issue('evidence-availability')
    if kind == 'boolean':
        if value == rule['trueValue']:
            return result('true')
        if value == rule['falseValue']:
            return result('false')
        return issue('boolean-spelling')
    if length(value) > 128 or not NUM.fullmatch(value):
        return issue('number-encoding')
    number = float(value)
    if not math.isfinite(number) or abs(number) > SAFE:
        return issue('number-range')
    if 'e' in value.lower() and abs(int(value.lower().split('e')[1])) > 308:
        return issue('number-exponent')
    selected = shortest(number)
    if number < 0:
        selected = -selected
    if Q(value) != selected:
        return issue('number-precision')
    return result(value)


# Draft-only interfaces. Reported maxima are negotiated input, not adopted ceilings.
ROLE_LIMITS = {'document-validation': ('documentBytes', 'frameBytes'),
 'preview': ('documentBytes',
             'combinedBytes',
             'frameBytes',
             'profilesBytes',
             'requestBodyBytes',
             'inputReplyBytes'),
 'preparation': ('documentBytes',
                 'combinedBytes',
                 'frameBytes',
                 'preparationBytes',
                 'recordBytes',
                 'profilesBytes',
                 'requestBodyBytes',
                 'inputReplyBytes',
                 'releaseStoredBytes',
                 'runStoredBytes',
                 'exportBaseBytes',
                 'exportWireBytes'),
 'preparation-verification': ('documentBytes',
                              'combinedBytes',
                              'frameBytes',
                              'preparationBytes',
                              'recordBytes',
                              'profilesBytes',
                              'requestBodyBytes',
                              'inputReplyBytes',
                              'releaseStoredBytes',
                              'runStoredBytes',
                              'exportBaseBytes',
                              'exportWireBytes'),
 'producer-carrier': ('originalSnapshotBytes',
                      'carrierBytes',
                      'grantBytes',
                      'adapterStdoutBytes',
                      'responseBytes',
                      'profilesBytes')}
# Synthetic trusted installation fixture; never supplied by a request/report.
INSTALLED_SPEC = {'version': 'draft-rfc0029',
 'revision': '0000000000000000000000000000000000000000',
 'schemaSha256': 'sha256:1111111111111111111111111111111111111111111111111111111111111111',
 'corpusSha256': 'sha256:2222222222222222222222222222222222222222222222222222222222222222'}
PROFILE_CAPS = {'base': {'documentBytes': 1048576,
          'frameBytes': 2097152,
          'combinedBytes': 12582912,
          'originalSnapshotBytes': 524288,
          'carrierBytes': 3145728,
          'grantBytes': 3145728,
          'adapterStdoutBytes': 3145728,
          'responseBytes': 5242880,
          'preparationBytes': 16777216,
          'recordBytes': 9437184,
          'profilesBytes': 81920,
          'requestBodyBytes': 16777216,
          'inputReplyBytes': 37748736,
          'releaseStoredBytes': 41943040,
          'runStoredBytes': 41943040,
          'exportBaseBytes': 75497472,
          'exportWireBytes': 90177536},
 'extended': {'documentBytes': 2097152,
              'frameBytes': 4194304,
              'combinedBytes': 25165824,
              'originalSnapshotBytes': 524288,
              'carrierBytes': 3145728,
              'grantBytes': 3145728,
              'adapterStdoutBytes': 3145728,
              'responseBytes': 5242880,
              'preparationBytes': 33554432,
              'recordBytes': 17825792,
              'profilesBytes': 163840,
              'requestBodyBytes': 33554432,
              'inputReplyBytes': 75497472,
              'releaseStoredBytes': 83886080,
              'runStoredBytes': 83886080,
              'exportBaseBytes': 150994944,
              'exportWireBytes': 176160768}}


def positive(value, zero=False):
    if not isinstance(value, Number) or len(value.text) > 17 or not INT.fullmatch(value.text):
        fail()
    number = int(value.text)
    if number < (0 if zero else 1) or number > SAFE:
        fail()
    return number


def digest(text):
    return 'sha256:' + hashlib.sha256(text.encode('utf-8')).hexdigest()


def capability(entry):
    closed(entry, ['contract', 'spec', 'profile', 'role', 'limits'], ['producerGrammar'])
    if entry['contract'] != 'retained-column/1':
        fail('capability-unsupported')
    spec = entry['spec']
    closed(spec, ['version', 'revision', 'schemaSha256', 'corpusSha256'])
    string(spec['version'], 160, True)
    if not isinstance(spec['revision'], str) or not re.fullmatch('[0-9a-f]{40}', spec['revision']):
        fail()
    for key in ('schemaSha256', 'corpusSha256'):
        if not isinstance(spec[key], str) or not re.fullmatch('sha256:[0-9a-f]{64}', spec[key]):
            fail()
    if entry['profile'] not in ('base', 'extended') or not isinstance(entry['role'], str) or entry['role'] not in ROLE_LIMITS:
        fail('capability-unsupported')
    if 'producerGrammar' in entry:
        if entry['role'] not in ('preparation', 'preparation-verification', 'producer-carrier'):
            fail()
        if entry['producerGrammar'] != 'desk-reviewed-input/1':
            fail('capability-unsupported')
    closed(entry['limits'], ROLE_LIMITS[entry['role']])
    for value in entry['limits'].values():
        positive(value)


def admit(probe, effect=lambda: None):
    closed(probe, ['capabilities', 'required', 'sizes'])
    if probe['capabilities'] == {}:
        fail('capability-unsupported')
    closed(probe['capabilities'], ['conversionContracts'])
    entries = probe['capabilities']['conversionContracts']
    if not isinstance(entries, list) or len(entries) > 32:
        fail()
    required = probe['required']
    capability(required)
    if required['spec'] != INSTALLED_SPEC:
        fail('capability-unsupported')
    identities = set()
    selected = None
    for entry in entries:
        capability(entry)
        identity = json.dumps({k: entry.get(k) for k in ('contract', 'spec', 'profile', 'role', 'producerGrammar')}, sort_keys=True)
        if identity in identities:
            fail()
        identities.add(identity)
        if all(entry[k] == required[k] for k in ('contract', 'spec', 'profile', 'role')):
            if entry.get('producerGrammar') == required.get('producerGrammar'):
                selected = entry
    if selected is None:
        fail('capability-unsupported')
    closed(probe['sizes'], ROLE_LIMITS[required['role']])
    for key in ROLE_LIMITS[required['role']]:
        actual = positive(probe['sizes'][key], zero=True)
        if actual > PROFILE_CAPS[required['profile']][key]:
            fail('input-over-bound')
        if actual > min(positive(required['limits'][key]), positive(selected['limits'][key])):
            fail('input-over-bound')
    effect()  # The only effect seam: every refusal above precedes the caller callback.
    return {'admitted': True}


def select(probe, effect=lambda: None):
    closed(probe, ['selector', 'role'])
    s = probe['selector']
    closed(s, ['contract', 'spec', 'profile', 'roles'])
    closed(s['spec'], ['version', 'revision', 'schemaSha256', 'corpusSha256'])
    if s['contract'] != 'retained-column/1' or s['spec'] != INSTALLED_SPEC or not isinstance(s['profile'], str) or s['profile'] not in PROFILE_CAPS:
        fail('capability-unsupported')
    order = list(ROLE_LIMITS)
    if not isinstance(s['roles'], list) or not 1 <= len(s['roles']) <= len(order):
        fail()
    if any(not isinstance(r, str) or r not in ROLE_LIMITS for r in s['roles']):
        fail('capability-unsupported')
    if len(set(s['roles'])) != len(s['roles']) or s['roles'] != [r for r in order if r in s['roles']]:
        fail()
    if not isinstance(probe['role'], str) or probe['role'] not in s['roles']:
        fail('capability-unsupported')
    effect()
    return {'selected': True}


def restore(request, raw_carrier_text):
    closed(request, ['restore', 'profile', 'limits'])
    closed(request['limits'], ['originalSnapshotBytes', 'carrierBytes'])
    snapshot_max = positive(request['limits']['originalSnapshotBytes'])
    carrier_max = positive(request['limits']['carrierBytes'])
    carrier = request['restore']
    closed(carrier, ['contractVersion', 'originalSnapshotJson', 'originalSnapshotSha256', 'retained'])
    if carrier['contractVersion'] != '1':
        fail()
    snapshot = carrier['originalSnapshotJson']
    string(snapshot, snapshot_max)
    if raw_carrier_text is None or length(raw_carrier_text) > carrier_max:
        fail('input-over-bound')
    if carrier['originalSnapshotSha256'] != digest(snapshot):
        fail('snapshot-digest')
    # Decode only to check JSON structure. Never derive original identity from this object.
    if not isinstance(parse(snapshot, strict=False), dict):
        fail()
    frame = carrier['retained']
    validate({'contractVersion':'1', 'column':'_carrier', 'kind':'text'}, frame, request['profile'], raw_frame_size(raw_carrier_text, 'retained'))
    if frame['origin'] != 'generated':
        fail()
    return {'originalSnapshotJson': snapshot, 'originalSnapshotSha256': digest(snapshot),
            'originalSnapshotBytes': length(snapshot)}


def lineage(request, raw_frame_text=None):
    closed(request, ['rule', 'frame'], ['profile'])
    rule, frame = request['rule'], request['frame']
    if raw_frame_text is None:
        fail('read-failed')
    validate(rule, frame, request.get('profile', 'base'), length(raw_frame_text))
    frame_digest = digest(raw_frame_text)
    output = preview(rule, frame)
    if output['issues'] or ('valueJson' in output and not output['claimAdmissible']):
        fail('read-failed')
    column = rule['column']
    original = {'state':'missing'}
    identity = None
    if rule['kind'] == 'research-value':
        research = frame['research']
        entry = research['fields'].get(column)
        if entry is not None and 'valueJson' in entry:
            original = {'state':'present', 'ref':{'frameSha256':frame_digest, 'location':'research-value'}}
        field = next(e for e in research['declaration']['fields'] if e['name'] == column)
        identity = {'recipeRevision':research['recordRecipeRevision'], 'fieldSha256':digest(field['fieldJson'])}
    elif column in frame['values']:
        original = {'state':'present', 'ref':{'frameSha256':frame_digest, 'location':'values'}}
    result = {'state':'value', 'json':output['valueJson']} if 'valueJson' in output else {'state':'omitted', 'reason':output['omitted']}
    answer = {'contractVersion':'1', 'column':column, 'input':original, 'result':result}
    if identity is not None:
        answer['researchIdentity'] = identity
    return answer


def raw_frame_size(text, member='frame', as_text=False):
    # Input was already validated. Measure the actual serialized frame, including escapes.
    if not text.lstrip(' \t\r\n').startswith('{'):
        return None
    decoder = json.JSONDecoder(parse_int=Number, parse_float=Number)
    index = text.index('{') + 1
    while True:
        while index < len(text) and text[index] in ' \t\r\n':
            index += 1
        if text[index] == '}':
            return None
        key, index = decoder.raw_decode(text, index)
        while text[index] in ' \t\r\n':
            index += 1
        index += 1  # colon
        while text[index] in ' \t\r\n':
            index += 1
        start = index
        _, index = decoder.raw_decode(text, index)
        if key == member:
            return text[start:index] if as_text else length(text[start:index])
        while text[index] in ' \t\r\n':
            index += 1
        if text[index] == '}':
            return None
        index += 1


# A pure consistency experiment. The integration supplies its trusted profile
# projection and an already verified receipt resultDigest through separate seams.
# This line protocol cannot authenticate either seam and reports that explicitly.
PRODUCER_GRAMMAR = 'desk-reviewed-input/1'
REVISION_DOMAIN = 'judgment-pack/retained-column/1/desk-reviewed-input/revision\0'
RUN_ID = re.compile(r'research_[a-f0-9]{32}\Z', re.ASCII)


def compact_token(text):
    quoted = escaped = False
    out = []
    for char in text:
        if quoted:
            out.append(char)
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
            out.append(char)
        elif char not in ' \t\r\n':
            out.append(char)
    return ''.join(out)


def raw_array(text):
    decoder = json.JSONDecoder(parse_int=Number, parse_float=Number)
    index = 1
    out = []
    while True:
        while text[index] in ' \t\r\n':
            index += 1
        if text[index] == ']':
            return out
        start = index
        _, index = decoder.raw_decode(text, index)
        out.append(text[start:index])
        while text[index] in ' \t\r\n':
            index += 1
        if text[index] == ']':
            return out
        index += 1


def source_member(text, *path):
    for key in path:
        text = raw_frame_size(text, key, as_text=True)
        if text is None:
            fail()
    return text


def revision_identity(run_id, revision):
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        fail()
    version = positive(revision)
    return digest(REVISION_DOMAIN + run_id + '\0' + str(version))


def producer_context(trust, binding):
    closed(trust, ['id', 'profileDigest', 'class', 'source', 'authority', 'shape',
                   'endpoint', 'adapter', 'tools', 'retainedColumnProducer'])
    closed(binding, ['kind', 'profile', 'profileDigest'])
    closed(trust['retainedColumnProducer'], ['contractVersion', 'grammar'])
    closed(trust['adapter'], ['name', 'version', 'digest'])
    for key in ('profileDigest',):
        if not isinstance(trust[key], str) or not re.fullmatch('sha256:[0-9a-f]{64}', trust[key]):
            fail()
    string(trust['id'], 64, True)
    if not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}', trust['id']):
        fail()
    string(trust['authority'], 256, True)
    if trust['retainedColumnProducer'] != {'contractVersion':'1', 'grammar':PRODUCER_GRAMMAR}:
        fail('capability-unsupported')
    if not isinstance(trust['adapter']['digest'], str) or not re.fullmatch('sha256:[0-9a-f]{64}', trust['adapter']['digest']):
        fail()
    if (trust['class'] != 'generated' or trust['source'] != 'desk-inputs' or
        trust['shape'] != 'mcp' or trust['endpoint'] != 'desk-local:reviewed-inputs' or
        trust['tools'] != ['read_reviewed_input'] or
        trust['adapter']['name'] != 'jpack-desk/reviewed-input' or trust['adapter']['version'] != '2' or
        binding != {'kind':'operation', 'profile':trust['id'], 'profileDigest':trust['profileDigest']}):
        fail('profile-mismatch')


def producer_projection(snapshot):
    if length(snapshot) > 524288:
        fail('input-over-bound')
    original = parse(snapshot, strict=False)
    if not isinstance(original, dict):
        fail()
    # Select known required paths. Other real snapshot members remain opaque,
    # duplicate-checked, and byte-exact in originalSnapshotJson.
    try:
        record, research = original['record'], original['research']
        retained = record['research']
        declared = research['recipe']['fields']
        fields = retained['entity']['fields']
        values = record['values']
        versions = (research['recipeVersion'], retained['recipeVersion'])
        run_ids = (research['id'], retained['runId'])
        if original['version'].text != '1' or original['class'] != 'generated' or record['class'] != 'generated':
            fail()
    except (KeyError, TypeError, AttributeError):
        fail()
    revision = revision_identity(run_ids[0], versions[0])
    other = revision_identity(run_ids[1], versions[1])
    if revision != other:
        fail('read-failed')
    if not isinstance(values, dict) or not isinstance(fields, dict) or not isinstance(declared, list):
        fail()
    if max(len(values), len(fields), len(declared)) > 1000:
        fail('input-over-bound')
    for key, value in values.items():
        string(key, 160, True)
        string(value, 524288)
    declarations = []
    names = set()
    field_tokens = raw_array(source_member(snapshot, 'research', 'recipe', 'fields'))
    for field, raw in zip(declared, field_tokens):
        if not isinstance(field, dict):
            fail()
        name = field.get('name')
        string(name, 160, True)
        if name in names:
            fail()
        names.add(name)
        if field.get('type') not in ('text','integer','decimal','boolean','text-list','range','string','number'):
            fail()
        declarations.append({'name':name, 'fieldJson':compact_token(raw)})
    projected = {}
    raw_fields = source_member(snapshot, 'record', 'research', 'entity', 'fields')
    for name, entry in fields.items():
        string(name, 160, True)
        if not isinstance(entry, dict) or not isinstance(entry.get('status'), str) or entry['status'] not in STATUSES:
            fail()
        selected = {'status':entry['status']}
        if 'value' in entry:
            selected['valueJson'] = source_member(source_member(raw_fields, name), 'value')
        projected[name] = selected
    # This is the closed projection, not a claim that the full snapshot is closed.
    return {'grammar':PRODUCER_GRAMMAR, 'snapshotVersion':1, 'snapshotClass':'generated',
            'recordClass':'generated', 'runId':run_ids[0], 'recordRunId':run_ids[1],
            'recipeVersion':positive(versions[0]), 'recordRecipeVersion':positive(versions[1]),
            'values':values, 'declarations':declarations, 'fields':projected}, revision


def carrier_canon(value):
    # The generated wrapper/frame domain consists of scalar strings/null and
    # containers. Embedded source numbers remain opaque strings. §1 canon orders
    # object names by code point and never HTML/Unicode-normalizes strings.
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(k, ensure_ascii=False) + ':' + carrier_canon(value[k]) for k in sorted(value)) + '}'
    if isinstance(value, list):
        return '[' + ','.join(map(carrier_canon, value)) + ']'
    if value is None or isinstance(value, (str, bool)):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    fail('acquisition-invalid')


def generated_consistency(probe, carrier_text):
    closed(probe, ['carrier','profile','limits','trustedProducer','sourceBinding','receiptResultDigest','rule'])
    producer_context(probe['trustedProducer'], probe['sourceBinding'])
    restore({'restore':probe['carrier'], 'profile':probe['profile'], 'limits':probe['limits']}, carrier_text)
    if probe['receiptResultDigest'] != digest(carrier_canon(probe['carrier'])):
        fail('acquisition-invalid')
    source, revision = producer_projection(probe['carrier']['originalSnapshotJson'])
    frame = probe['carrier']['retained']
    research = frame['research']
    if research['declaration'] is None:
        fail('read-failed')
    if (research['recordRecipeRevision'], research['declaration']['recipeRevision']) != (revision, revision):
        fail('read-failed')
    if research['declaration']['fields'] != source['declarations']:
        fail('read-failed')
    if frame['values'] != source['values'] or research['fields'] != source['fields']:
        fail('read-failed')
    transformation = lineage({'rule':probe['rule'], 'frame':frame, 'profile':probe['profile']}, source_member(carrier_text, 'retained'))
    return {'consistent':True, 'acquisition':'not-verified', 'history':'not-checked',
            'originalSnapshotSha256':probe['carrier']['originalSnapshotSha256'],
            'frameSha256':digest(source_member(carrier_text, 'retained')),
            'revisionIdentity':revision, 'projection':source, 'transformation':transformation}


def verify_lineage(probe, raw_probe_text):
    closed(probe, ['rule', 'frame', 'transformation'], ['profile'])
    expected = lineage({k:v for k,v in probe.items() if k != 'transformation'}, source_member(raw_probe_text, 'frame'))
    # Equality is over the complete closed fragment, including target column,
    # reference location/custody digest, result and conditional original identity.
    if probe['transformation'] != expected:
        fail('read-failed')
    return {'consistent':True, 'acquisition':'not-verified'}


def retain_case(probe, raw_probe_text):
    closed(probe, ['source'])
    source = probe['source']
    if isinstance(source, dict) and set(source) == {'case'}:
        text = source_member(source_member(raw_probe_text, 'source'), 'case')
    else:
        closed(source, ['retainedCaseJson'])
        text = source['retainedCaseJson']
        if not isinstance(text, str) or not text:
            fail()
    if not isinstance(parse(text, strict=False), dict):
        fail()
    return {'retainedCaseJson':text}


def retain_source(probe, raw_probe_text):
    closed(probe, ['source'])
    source = probe['source']
    if isinstance(source, dict) and set(source) == {'response'}:
        envelope = source_member(source_member(raw_probe_text, 'source'), 'response')
    else:
        closed(source, ['retainedResponseJson'])
        envelope = source['retainedResponseJson']
        if not isinstance(envelope, str) or not envelope:
            fail()
    # Structure only: the ordinary acquisition reader still verifies the full
    # receipt/salts grammar, signature, frozen request, profile and freshness.
    parsed = parse(envelope, strict=False)
    closed(parsed, ['result', 'receipt', 'salts'])
    if not all(isinstance(parsed[k], dict) for k in ('result', 'receipt', 'salts')):
        fail()
    return {'retainedResponseJson':envelope}


def handle(request, raw_frame_bytes=None, raw_carrier_text=None, raw_lineage_text=None):
    if isinstance(request, dict) and set(request) == {'verifyLineage'}:
        return verify_lineage(request['verifyLineage'], source_member(raw_lineage_text, 'verifyLineage'))
    if isinstance(request, dict) and set(request) == {'retainCase'}:
        return retain_case(request['retainCase'], source_member(raw_lineage_text, 'retainCase'))
    if isinstance(request, dict) and set(request) == {'retainSource'}:
        return retain_source(request['retainSource'], source_member(raw_lineage_text, 'retainSource'))
    if isinstance(request, dict) and set(request) == {'generatedConsistency'}:
        return generated_consistency(request['generatedConsistency'], raw_carrier_text)
    if isinstance(request, dict) and 'restore' in request:
        return restore(request, raw_carrier_text)
    if isinstance(request, dict) and set(request) == {'selection'}:
        return select(request['selection'])
    if isinstance(request, dict) and set(request) == {'admission'}:
        return admit(request['admission'])
    if isinstance(request, dict) and set(request) == {'lineage'}:
        return lineage(request['lineage'], source_member(raw_lineage_text, 'frame') if raw_lineage_text is not None else None)
    if isinstance(request, dict) and set(request) == {'binary64Hex'}:
        text = request['binary64Hex']
        if not isinstance(text, str) or not re.fullmatch('[0-9a-f]{16}', text):
            fail()
        value = struct.unpack('>d', bytes.fromhex(text))[0]
        if abs(value) > SAFE:
            fail()
        q = shortest(value)
        if value < 0:
            q = -q
        return {'rational': str(q)}
    closed(request, ['rule', 'frame'], ['profile'])
    validate(request['rule'], request['frame'], request.get('profile', 'base'), raw_frame_bytes)
    return preview(request['rule'], request['frame'])



if __name__ == '__main__':
    while True:
        line = sys.stdin.buffer.readline(4200002)
        if not line:
            break
        if len(line) > 4200000:
            while not line.endswith(b'\n'):
                line = sys.stdin.buffer.readline(4200002)
                if not line:
                    break
            print('{"refusal":"input-over-bound"}')
            continue
        try:
            if len(line) > 4200000:
                fail('input-over-bound')
            text = line.decode('utf-8')
            request = parse(text, depth=64)
            if isinstance(request, dict) and set(request) == {'generatedConsistency'}:
                raw_carrier = source_member(source_member(text, 'generatedConsistency'), 'carrier')
            else:
                raw_carrier = raw_frame_size(text, 'restore', as_text=True) if isinstance(request, dict) and 'restore' in request else None
            output = handle(request, raw_frame_size(text) if isinstance(request, dict) and 'frame' in request else None, raw_carrier, raw_frame_size(text, 'lineage', as_text=True) if isinstance(request, dict) and 'lineage' in request else text)
        except (Refusal, UnicodeError) as exc:
            output = {'refusal': str(exc) if isinstance(exc, Refusal) else 'input-malformed'}
        print(json.dumps(output, ensure_ascii=True, separators=(',', ':')))

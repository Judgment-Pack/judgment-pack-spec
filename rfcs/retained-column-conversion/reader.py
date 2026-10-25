#!/usr/bin/env python3
"""Draft RFC0029 preview only; no acquisition, preparation or adoption claim."""
import json
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
            string(value, 16000)
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


def raw_frame_size(text):
    # Input was already validated. Measure the actual serialized frame, including escapes.
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
        if key == 'frame':
            return length(text[start:index])
        while text[index] in ' \t\r\n':
            index += 1
        if text[index] == '}':
            return None
        index += 1


def handle(request, raw_frame_bytes=None):
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
            output = handle(request, raw_frame_size(text) if isinstance(request, dict) and 'frame' in request else None)
        except (Refusal, UnicodeError) as exc:
            output = {'refusal': str(exc) if isinstance(exc, Refusal) else 'input-malformed'}
        print(json.dumps(output, ensure_ascii=True, separators=(',', ':')))

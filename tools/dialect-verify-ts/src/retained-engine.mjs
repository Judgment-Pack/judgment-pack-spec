import { pathToFileURL } from "node:url";
// Promoted RFC0029 interpreter; normative rules: spec/retained-column.md.
// Draft RFC0029 preview only. No acquisition, preparation or adoption claim.
import { createHash } from 'node:crypto';
const SAFE = 9007199254740991n;
const DEC = /^-?(0|[1-9][0-9]*)(\.[0-9]+)?$/;
const NUM = /^-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?$/;
const INT = /^-?(0|[1-9][0-9]*)$/;
// JavaScript $ also matches before a final LF; require the entire lexical value.
const full=(pattern,text)=>{const m=pattern.exec(text);return m!==null && m[0].length===text.length;};
const SPACE = /^[\u0009-\u000d\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]*$/u;
const STATUS = ['supported','interpretation','missing','conflicting','inaccessible','stale'];
const META = ['name','url','website','company_id','company_name','company_url'];
// SIMPLE_LOWER_TABLE is inserted below from Unicode 15.0 simple case ranges.
// Unicode 15.0 simple lowercase data, derived from Go unicode CaseRanges.
// Go Authors / Unicode data; Go BSD-3-Clause distribution, tables SHA256 6a88d48746c4b2c471cc04ae40559694b734770212e6f5ea5f1962adb0c0bdb1.
const SIMPLE_LOWER_TABLE = [[65,90,32],[192,214,32],[216,222,32],[256,303,"alternate"],[304,304,-199],[306,311,"alternate"],[313,328,"alternate"],[330,375,"alternate"],[376,376,-121],[377,382,"alternate"],[385,385,210],[386,389,"alternate"],[390,390,206],[391,392,"alternate"],[393,394,205],[395,396,"alternate"],[398,398,79],[399,399,202],[400,400,203],[401,402,"alternate"],[403,403,205],[404,404,207],[406,406,211],[407,407,209],[408,409,"alternate"],[412,412,211],[413,413,213],[415,415,214],[416,421,"alternate"],[422,422,218],[423,424,"alternate"],[425,425,218],[428,429,"alternate"],[430,430,218],[431,432,"alternate"],[433,434,217],[435,438,"alternate"],[439,439,219],[440,441,"alternate"],[444,445,"alternate"],[452,452,2],[453,453,1],[455,455,2],[456,456,1],[458,458,2],[459,459,1],[461,476,"alternate"],[478,495,"alternate"],[497,497,2],[498,498,1],[500,501,"alternate"],[502,502,-97],[503,503,-56],[504,543,"alternate"],[544,544,-130],[546,563,"alternate"],[570,570,10795],[571,572,"alternate"],[573,573,-163],[574,574,10792],[577,578,"alternate"],[579,579,-195],[580,580,69],[581,581,71],[582,591,"alternate"],[880,883,"alternate"],[886,887,"alternate"],[895,895,116],[902,902,38],[904,906,37],[908,908,64],[910,911,63],[913,929,32],[931,939,32],[975,975,8],[984,1007,"alternate"],[1012,1012,-60],[1015,1016,"alternate"],[1017,1017,-7],[1018,1019,"alternate"],[1021,1023,-130],[1024,1039,80],[1040,1071,32],[1120,1153,"alternate"],[1162,1215,"alternate"],[1216,1216,15],[1217,1230,"alternate"],[1232,1327,"alternate"],[1329,1366,48],[4256,4293,7264],[4295,4295,7264],[4301,4301,7264],[5024,5103,38864],[5104,5109,8],[7312,7354,-3008],[7357,7359,-3008],[7680,7829,"alternate"],[7838,7838,-7615],[7840,7935,"alternate"],[7944,7951,-8],[7960,7965,-8],[7976,7983,-8],[7992,7999,-8],[8008,8013,-8],[8025,8025,-8],[8027,8027,-8],[8029,8029,-8],[8031,8031,-8],[8040,8047,-8],[8072,8079,-8],[8088,8095,-8],[8104,8111,-8],[8120,8121,-8],[8122,8123,-74],[8124,8124,-9],[8136,8139,-86],[8140,8140,-9],[8152,8153,-8],[8154,8155,-100],[8168,8169,-8],[8170,8171,-112],[8172,8172,-7],[8184,8185,-128],[8186,8187,-126],[8188,8188,-9],[8486,8486,-7517],[8490,8490,-8383],[8491,8491,-8262],[8498,8498,28],[8544,8559,16],[8579,8580,"alternate"],[9398,9423,26],[11264,11311,48],[11360,11361,"alternate"],[11362,11362,-10743],[11363,11363,-3814],[11364,11364,-10727],[11367,11372,"alternate"],[11373,11373,-10780],[11374,11374,-10749],[11375,11375,-10783],[11376,11376,-10782],[11378,11379,"alternate"],[11381,11382,"alternate"],[11390,11391,-10815],[11392,11491,"alternate"],[11499,11502,"alternate"],[11506,11507,"alternate"],[42560,42605,"alternate"],[42624,42651,"alternate"],[42786,42799,"alternate"],[42802,42863,"alternate"],[42873,42876,"alternate"],[42877,42877,-35332],[42878,42887,"alternate"],[42891,42892,"alternate"],[42893,42893,-42280],[42896,42899,"alternate"],[42902,42921,"alternate"],[42922,42922,-42308],[42923,42923,-42319],[42924,42924,-42315],[42925,42925,-42305],[42926,42926,-42308],[42928,42928,-42258],[42929,42929,-42282],[42930,42930,-42261],[42931,42931,928],[42932,42947,"alternate"],[42948,42948,-48],[42949,42949,-42307],[42950,42950,-35384],[42951,42954,"alternate"],[42960,42961,"alternate"],[42966,42969,"alternate"],[42997,42998,"alternate"],[65313,65338,32],[66560,66599,40],[66736,66771,40],[66928,66938,39],[66940,66954,39],[66956,66962,39],[66964,66965,39],[68736,68786,64],[71840,71871,32],[93760,93791,32],[125184,125217,34]];
class Refusal extends Error {}
class JsonNumber { constructor(text) { this.text = text; } }
const fail = (code='input-malformed') => { throw new Refusal(code); };
const bytes = s => Buffer.byteLength(s,'utf8');
const object = v => v !== null && typeof v === 'object' && !Array.isArray(v) && !(v instanceof JsonNumber);
function lower15(s) {
  let out = '';
  for (const char of s) {
    let point = char.codePointAt(0);
    for (const [low,high,delta] of SIMPLE_LOWER_TABLE) {
      if (low <= point && point <= high) {
        point = delta === 'alternate' ? low + ((point-low) | 1) : point+delta;
        break;
      }
    }
    out += String.fromCodePoint(point);
  }
  return out;
}
function scalar(v) {
  if (typeof v === 'string') return [...v].every(c => c.codePointAt(0) < 0xd800 || c.codePointAt(0) > 0xdfff);
  if (Array.isArray(v)) return v.every(scalar);
  if (object(v)) return Object.entries(v).every(([k,x]) => scalar(k) && scalar(x));
  return true;
}
// Separate recursive-descent parser retains numeric spelling and sees duplicate decoded keys.
const RAW_MEMBERS=Symbol('raw members'), RAW_ITEMS=Symbol('raw array items'), RAW_TOKEN=Symbol('raw token');
const FRAME_SIZE=Symbol('raw frame bytes'), CARRIER_SIZE=Symbol('raw carrier bytes'), RETAINED_SIZE=Symbol('raw retained bytes');
function parse(text, {strict=true,folded=false,depth=64}={}) {
  let i=0, rootFrameBytes, rootCarrierBytes, retainedBytes;
  const ws=() => { while (i<text.length && /[\x20\x09\x0a\x0d]/.test(text[i])) i++; };
  function quoted() {
    if (text[i] !== '"') fail();
    const begin=i++;
    while (i<text.length) {
      const c=text[i++];
      if (c === '"') {
        try { return JSON.parse(text.slice(begin,i)); } catch { fail(); }
      }
      if (c === '\\') i++;
    }
    fail();
  }
  function read(level) {
    ws(); const start=i; const value=readValue(level);
    if (object(value) || Array.isArray(value)) Object.defineProperty(value,RAW_TOKEN,{value:text.slice(start,i)});
    return value;
  }
  function readValue(level) {
    if (level>depth) fail('input-over-bound');
    ws();
    if (text[i] === '"') return quoted();
    if (text[i] === '{') {
      i++; ws(); const result=Object.create(null), seen=new Set();
      Object.defineProperty(result,RAW_MEMBERS,{value:Object.create(null)});
      if (text[i] === '}') { i++; return result; }
      while (true) {
        ws(); const key=quoted(), name=folded ? lower15(key) : key;
        if (seen.has(name)) fail();
        seen.add(name); ws(); if (text[i++] !== ':') fail();
        ws(); const start=i; result[key]=read(level+1);
        result[RAW_MEMBERS][key]=text.slice(start,i);
        if ((level===0 || level===1) && key==='frame') rootFrameBytes=bytes(text.slice(start,i));
        if (level===1 && key==='retained') retainedBytes=bytes(text.slice(start,i));
        if (level===0 && key==='restore') rootCarrierBytes=bytes(text.slice(start,i));
        ws();
        const stop=text[i++]; if (stop === '}') return result;
        if (stop !== ',') fail();
      }
    }
    if (text[i] === '[') {
      i++; ws(); const result=[]; Object.defineProperty(result,RAW_ITEMS,{value:[]});
      if (text[i] === ']') { i++; return result; }
      while (true) {
        ws(); const start=i; result.push(read(level+1)); result[RAW_ITEMS].push(text.slice(start,i)); ws();
        const stop=text[i++]; if (stop === ']') return result;
        if (stop !== ',') fail();
      }
    }
    for (const [token,value] of [['true',true],['false',false],['null',null]]) {
      if (text.startsWith(token,i)) { i+=token.length; return value; }
    }
    const match=/^-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?/.exec(text.slice(i));
    if (!match) fail();
    i+=match[0].length; return new JsonNumber(match[0]);
  }
  const result=read(0); ws(); if (i!==text.length || (strict && !scalar(result))) fail();
  if (object(result) && rootFrameBytes!==undefined) Object.defineProperty(result,FRAME_SIZE,{value:rootFrameBytes});
  if (object(result) && rootCarrierBytes!==undefined) Object.defineProperty(result,CARRIER_SIZE,{value:rootCarrierBytes});
  if (object(result) && retainedBytes!==undefined) Object.defineProperty(result,RETAINED_SIZE,{value:retainedBytes});
  return result;
}
function closed(v,required,optional=[]) {
  if (!object(v) || required.some(k => !Object.hasOwn(v,k)) || Object.keys(v).some(k => !required.includes(k) && !optional.includes(k))) fail();
}
function string(v,limit,nonempty=false) {
  if (typeof v !== 'string' || !scalar(v) || (nonempty && v==='')) fail();
  if (bytes(v)>limit) fail('input-over-bound');
}
function validate(rule,frame,profile,rawFrameBytes) {
  if (!['base','extended'].includes(profile)) fail();
  if ((rawFrameBytes ?? bytes(JSON.stringify(frame)))>(profile==='base' ? 2097152 : 4194304)) fail('input-over-bound');
  closed(rule,['contractVersion','column','kind'],['trueValue','falseValue']);
  if (rule.contractVersion!=='1' || !['text','decimal','number','boolean','research-value','evidence-availability'].includes(rule.kind)) fail();
  string(rule.column,160,true);
  if (rule.kind==='boolean') {
    for (const key of ['trueValue','falseValue']) { string(rule[key],160,true); if (SPACE.test(rule[key])) fail(); }
    if (rule.trueValue===rule.falseValue) fail();
  } else if (Object.hasOwn(rule,'trueValue') || Object.hasOwn(rule,'falseValue')) fail();
  closed(frame,['contractVersion','origin','values','research']);
  if (frame.contractVersion!=='1' || !['asserted','generated'].includes(frame.origin) || !object(frame.values)) fail();
  if (Object.keys(frame.values).length>1000) fail('input-over-bound');
  for (const [key,value] of Object.entries(frame.values)) { string(key,160,true); if (value!==null) string(value,frame.origin==='asserted' ? 16000 : 524288); }
  if (frame.origin==='asserted') { if (frame.research!==null) fail(); return; }
  const r=frame.research;
  closed(r,['recordRecipeRevision','declaration','fields']); string(r.recordRecipeRevision,160,true);
  if (r.declaration!==null) {
    const d=r.declaration; closed(d,['recipeRevision','fields']); string(d.recipeRevision,160,true);
    if (!Array.isArray(d.fields)) fail(); if (d.fields.length>1000) fail('input-over-bound');
    const names=new Set();
    for (const e of d.fields) {
      closed(e,['name','fieldJson']); string(e.name,160,true); string(e.fieldJson,16384);
      if (names.has(e.name)) fail(); names.add(e.name);
      const f=parse(e.fieldJson,{depth:32});
      if (!object(f) || f.name!==e.name || typeof f.type!=='string') fail();
    }
  }
  if (!object(r.fields)) fail(); if (Object.keys(r.fields).length>1000) fail('input-over-bound');
  for (const [key,e] of Object.entries(r.fields)) {
    string(key,160,true); closed(e,['status'],['valueJson']);
    if (!STATUS.includes(e.status)) fail();
    if (Object.hasOwn(e,'valueJson')) string(e.valueJson,4194304);
  }
}
const abs = a => a<0n ? -a : a;
function gcd(a,b) { a=abs(a); b=abs(b); while (b) [a,b]=[b,a%b]; return a; }
function rat(n,d=1n) { if (d<0n) { n=-n; d=-d; } const g=gcd(n,d); return [n/g,d/g]; }
const add=(a,b)=>rat(a[0]*b[1]+b[0]*a[1],a[1]*b[1]);
const sub=(a,b)=>rat(a[0]*b[1]-b[0]*a[1],a[1]*b[1]);
const mul=(a,b)=>rat(a[0]*b[0],a[1]*b[1]);
const div=(a,b)=>rat(a[0]*b[1],a[1]*b[0]);
const cmp=(a,b)=>{const x=a[0]*b[1]-b[0]*a[1];return x<0n ? -1 : x>0n ? 1 : 0;};
const ten=e=>e>=0 ? [10n**BigInt(e),1n] : [1n,10n**BigInt(-e)];
function decimalRat(text) {
  let [coefficient,exponent='0']=text.toLowerCase().split('e');
  let sign=1n; if (coefficient[0]==='-') { sign=-1n; coefficient=coefficient.slice(1); }
  const pieces=coefficient.split('.'), scale=(pieces[1]||'').length;
  return mul([sign*BigInt(pieces.join('')),1n],ten(Number(exponent)-scale));
}
function bitsOf(x) { const b=new DataView(new ArrayBuffer(8)); b.setFloat64(0,x,false); return b.getBigUint64(0,false); }
function bitsRat(bits) {
  const e=Number((bits>>52n)&2047n), f=bits&((1n<<52n)-1n);
  if (e===2047) fail();
  const sig=e ? (1n<<52n)+f : f, power=(e ? e-1023 : -1022)-52;
  return power>=0 ? [sig<<BigInt(power),1n] : rat(sig,1n<<BigInt(-power));
}
function shortest(x) {
  x=Math.abs(x); if (!Number.isFinite(x)) fail(); if (x===0) return [0n,1n];
  const bits=bitsOf(x), exact=bitsRat(bits), lower=div(add(exact,bitsRat(bits-1n)),[2n,1n]);
  const upper=div(add(exact,bitsRat(bits+1n)),[2n,1n]), inclusive=(bits&1n)===0n;
  let order=exact[0].toString().length-exact[1].toString().length;
  while (cmp(exact,ten(order))<0) order--;
  while (cmp(exact,ten(order+1))>=0) order++;
  for (let digits=1;digits<=17;digits++) {
    let best=null;
    for (let e=order-digits-1;e<order-digits+3;e++) {
      const unit=ten(e), low=div(lower,unit), high=div(upper,unit), center=div(exact,unit);
      let first=(low[0]+low[1]-1n)/low[1], last=high[0]/high[1];
      if (!inclusive && cmp([first,1n],low)===0) first++;
      if (!inclusive && cmp([last,1n],high)===0) last--;
      const minimum=10n**BigInt(digits-1), maximum=10n**BigInt(digits)-1n;
      if (first<minimum) first=minimum; if (last>maximum) last=maximum;
      const floor=center[0]/center[1];
      for (const a of new Set([first,first+1n,last-1n,last,floor-1n,floor,floor+1n,floor+2n])) {
        if (a<first || a>last || a%10n===0n) continue;
        const q=mul([a,1n],unit), distance=sub(q,exact); distance[0]=abs(distance[0]);
        const row={q,distance,odd:a%2n};
        if (!best || cmp(distance,best.distance)<0 || (cmp(distance,best.distance)===0 && (row.odd<best.odd || (row.odd===best.odd && cmp(q,best.q)<0)))) best=row;
      }
    }
    if (best) return best.q;
  }
  fail();
}
function integer(v) { return v instanceof JsonNumber && full(INT,v.text) && abs(BigInt(v.text))<=SAFE; }
function decimal(v) { return typeof v==='string' && bytes(v)<=128 && full(DEC,v); }
function typed(raw,kind) {
  if (!raw || bytes(raw)>524288 || (['string','number'].includes(kind) && bytes(raw)>8192)) return false;
  try {
    const v=parse(raw,{strict:!['string','number'].includes(kind),folded:true,depth:64});
    if (['text','string'].includes(kind)) return typeof v==='string' && (kind==='string' || bytes(v)<=8192);
    if (kind==='number') return v instanceof JsonNumber && Number.isFinite(Number(v.text));
    if (kind==='integer') return integer(v);
    if (kind==='decimal') return decimal(v);
    if (kind==='boolean') return typeof v==='boolean';
    if (kind==='text-list') return Array.isArray(v) && v.length<=64 && v.every(s=>typeof s==='string' && bytes(s)<=1024);
    if (kind==='range' && object(v) && Object.keys(v).length===2 && Object.hasOwn(v,'min') && Object.hasOwn(v,'max')) {
      if (integer(v.min) && integer(v.max)) return BigInt(v.min.text)<=BigInt(v.max.text);
      return decimal(v.min) && decimal(v.max) && cmp(decimalRat(v.min),decimalRat(v.max))<=0;
    }
  } catch (e) { if (!(e instanceof Refusal)) throw e; }
  return false;
}
function admissible(raw) {
  try {
    const walk=v=>v instanceof JsonNumber ? integer(v) : Array.isArray(v) ? v.every(walk) : object(v) ? Object.values(v).every(walk) : true;
    return walk(parse(raw));
  } catch (e) { if (!(e instanceof Refusal)) throw e; return false; }
}
function preview(rule,frame) {
  const {kind,column}=rule, r=frame.research;
  const issue=code=>({issues:[code],claimAdmissible:false});
  const omit=reason=>({issues:[],omitted:reason,claimAdmissible:false});
  const result=raw=>({issues:[],valueJson:raw,claimAdmissible:admissible(raw)});
  if (kind==='research-value') {
    if (frame.origin!=='generated') return issue('research-context');
    if (META.includes(column)) return issue('research-metadata');
    const d=r.declaration;
    if (d===null || d.recipeRevision!==r.recordRecipeRevision) return issue('research-declaration');
    const item=d.fields.find(e=>e.name===column), original=item ? parse(item.fieldJson) : null;
    if (original===null) return issue('research-field');
    const entry=r.fields[column];
    if (!entry || !['supported','interpretation'].includes(entry.status)) return omit('unavailable');
    const raw=entry.valueJson ?? '';
    return typed(raw,original.type) ? result(raw) : issue('research-type');
  }
  if (!Object.hasOwn(frame.values,column)) return omit('missing');
  const v=frame.values[column]; if (v===null) return omit('legacy-null'); if (SPACE.test(v)) return omit('blank');
  if (frame.origin==='generated') {
    const entry=r.fields[column]; if (entry && !['supported','interpretation'].includes(entry.status)) return omit('unavailable');
  }
  const encoded=JSON.stringify(v);
  if (kind==='text') return result(encoded);
  if (kind==='decimal') return decimal(v) ? result(encoded) : issue('decimal-encoding');
  if (kind==='evidence-availability') return ['present','absent','unknown'].includes(v) ? result(encoded) : issue('evidence-availability');
  if (kind==='boolean') return v===rule.trueValue ? result('true') : v===rule.falseValue ? result('false') : issue('boolean-spelling');
  if (bytes(v)>128 || !full(NUM,v)) return issue('number-encoding');
  const number=Number(v); if (!Number.isFinite(number) || Math.abs(number)>Number(SAFE)) return issue('number-range');
  if (/[eE]/.test(v) && abs(BigInt(v.split(/[eE]/)[1]))>308n) return issue('number-exponent');
  const selected=shortest(number); if (number<0) selected[0]=-selected[0];
  return cmp(decimalRat(v),selected)===0 ? result(v) : issue('number-precision');
}
// Draft-only interfaces. No maxima below are production defaults.
const ROLE_LIMITS = {"document-validation":["documentBytes","frameBytes"],"preview":["documentBytes","combinedBytes","frameBytes","profilesBytes","requestBodyBytes","inputReplyBytes"],"preparation":["documentBytes","combinedBytes","frameBytes","preparationBytes","recordBytes","profilesBytes","requestBodyBytes","inputReplyBytes","releaseStoredBytes","runStoredBytes","exportBaseBytes","exportWireBytes"],"preparation-verification":["documentBytes","combinedBytes","frameBytes","preparationBytes","recordBytes","profilesBytes","requestBodyBytes","inputReplyBytes","releaseStoredBytes","runStoredBytes","exportBaseBytes","exportWireBytes"],"producer-carrier":["originalSnapshotBytes","carrierBytes","grantBytes","adapterStdoutBytes","responseBytes","profilesBytes"]};
// Synthetic trusted installation fixture, never request/report authority.
const INSTALLED_SPEC = {"version":"draft-rfc0029","revision":"0000000000000000000000000000000000000000","schemaSha256":"sha256:1111111111111111111111111111111111111111111111111111111111111111","corpusSha256":"sha256:2222222222222222222222222222222222222222222222222222222222222222"};
const PROFILE_CAPS = {"base":{"documentBytes":1048576,"frameBytes":2097152,"combinedBytes":12582912,"originalSnapshotBytes":524288,"carrierBytes":3145728,"grantBytes":3145728,"adapterStdoutBytes":3145728,"responseBytes":5242880,"preparationBytes":16777216,"recordBytes":9437184,"profilesBytes":81920,"requestBodyBytes":16777216,"inputReplyBytes":37748736,"releaseStoredBytes":41943040,"runStoredBytes":41943040,"exportBaseBytes":75497472,"exportWireBytes":90177536},"extended":{"documentBytes":2097152,"frameBytes":4194304,"combinedBytes":25165824,"originalSnapshotBytes":524288,"carrierBytes":3145728,"grantBytes":3145728,"adapterStdoutBytes":3145728,"responseBytes":5242880,"preparationBytes":33554432,"recordBytes":17825792,"profilesBytes":163840,"requestBodyBytes":33554432,"inputReplyBytes":75497472,"releaseStoredBytes":83886080,"runStoredBytes":83886080,"exportBaseBytes":150994944,"exportWireBytes":176160768}};
const installedSpec=s=>Object.keys(INSTALLED_SPEC).every(k=>s[k]===INSTALLED_SPEC[k]);

function positive(v,zero=false) {
  if (!(v instanceof JsonNumber) || v.text.length>17 || !full(INT,v.text)) fail();
  const n=BigInt(v.text); if (n<(zero ? 0n : 1n) || n>SAFE) fail(); return n;
}
const digest=s=>'sha256:'+createHash('sha256').update(s,'utf8').digest('hex');
function capability(e) {
  closed(e,['contract','spec','profile','role','limits'],['producerGrammar']);
  if (e.contract!=='retained-column/1') fail('capability-unsupported');
  closed(e.spec,['version','revision','schemaSha256','corpusSha256']); string(e.spec.version,160,true);
  if (typeof e.spec.revision!=='string' || !full(/^[0-9a-f]{40}$/,e.spec.revision)) fail();
  for (const k of ['schemaSha256','corpusSha256']) if (typeof e.spec[k]!=='string' || !full(/^sha256:[0-9a-f]{64}$/,e.spec[k])) fail();
  if (!['base','extended'].includes(e.profile) || typeof e.role!=='string' || !Object.hasOwn(ROLE_LIMITS,e.role)) fail('capability-unsupported');
  if (Object.hasOwn(e,'producerGrammar')) {
    if (!['preparation','preparation-verification','producer-carrier'].includes(e.role)) fail();
    if (e.producerGrammar!=='desk-reviewed-input/1') fail('capability-unsupported');
  }
  closed(e.limits,ROLE_LIMITS[e.role]); for (const v of Object.values(e.limits)) positive(v);
}
function admit(p,effect=()=>{}) {
  closed(p,['capabilities','required','sizes']);
  if (object(p.capabilities) && Object.keys(p.capabilities).length===0) fail('capability-unsupported');
  closed(p.capabilities,['conversionContracts']);
  const entries=p.capabilities.conversionContracts;
  if (!Array.isArray(entries) || entries.length>32) fail();
  const r=p.required; capability(r); if (!installedSpec(r.spec)) fail('capability-unsupported'); const identities=new Set(); let selected;
  const identity=e=>JSON.stringify([e.contract,e.spec.version,e.spec.revision,e.spec.schemaSha256,e.spec.corpusSha256,e.profile,e.role,e.producerGrammar??null]);
  for (const e of entries) {
    capability(e); const id=identity(e); if (identities.has(id)) fail(); identities.add(id);
    if (id===identity(r)) selected=e;
  }
  if (!selected) fail('capability-unsupported');
  closed(p.sizes,ROLE_LIMITS[r.role]);
  for (const k of ROLE_LIMITS[r.role]) {
    const a=positive(p.sizes[k],true), x=positive(r.limits[k]), y=positive(selected.limits[k]);
    if (a>BigInt(PROFILE_CAPS[r.profile][k])) fail('input-over-bound');
    if (a>(x<y ? x : y)) fail('input-over-bound');
  }
  effect(); // Every refusal must precede this caller callback.
  return {admitted:true};
}
function select(p,effect=()=>{}) {
  closed(p,['selector','role']); const s=p.selector;
  closed(s,['contract','spec','profile','roles']); closed(s.spec,['version','revision','schemaSha256','corpusSha256']);
  if (s.contract!=='retained-column/1' || !installedSpec(s.spec) || typeof s.profile!=='string' || !Object.hasOwn(PROFILE_CAPS,s.profile)) fail('capability-unsupported');
  const order=Object.keys(ROLE_LIMITS);
  if (!Array.isArray(s.roles) || s.roles.length<1 || s.roles.length>order.length) fail();
  if (s.roles.some(r=>typeof r!=='string' || !Object.hasOwn(ROLE_LIMITS,r))) fail('capability-unsupported');
  if (new Set(s.roles).size!==s.roles.length || JSON.stringify(s.roles)!==JSON.stringify(order.filter(r=>s.roles.includes(r)))) fail();
  if (typeof p.role!=='string' || !s.roles.includes(p.role)) fail('capability-unsupported');
  effect(); return {selected:true};
}

function restore(r) {
  closed(r,['restore','profile','limits']); closed(r.limits,['originalSnapshotBytes','carrierBytes']);
  const maxSnapshot=positive(r.limits.originalSnapshotBytes), maxCarrier=positive(r.limits.carrierBytes), c=r.restore;
  closed(c,['contractVersion','originalSnapshotJson','originalSnapshotSha256','retained']);
  if (c.contractVersion!=='1') fail();
  string(c.originalSnapshotJson,Number(maxSnapshot));
  if (r[CARRIER_SIZE]===undefined || BigInt(r[CARRIER_SIZE])>maxCarrier) fail('input-over-bound');
  if (c.originalSnapshotSha256!==digest(c.originalSnapshotJson)) fail('snapshot-digest');
  if (!object(parse(c.originalSnapshotJson,{strict:false}))) fail();
  validate({contractVersion:'1',column:'_carrier',kind:'text'},c.retained,r.profile,r[RETAINED_SIZE]);
  if (c.retained.origin!=='generated') fail();
  return {originalSnapshotJson:c.originalSnapshotJson,originalSnapshotSha256:digest(c.originalSnapshotJson),originalSnapshotBytes:bytes(c.originalSnapshotJson)};
}
function lineage(r,rawFrameBytes) {
  closed(r,['rule','frame'],['profile']); validate(r.rule,r.frame,Object.hasOwn(r,'profile') ? r.profile : 'base',rawFrameBytes);
  const p=preview(r.rule,r.frame); if (p.issues.length || (Object.hasOwn(p,'valueJson') && !p.claimAdmissible)) fail('read-failed');
  const column=r.rule.column,f=r.frame; if (typeof f[RAW_TOKEN]!=='string') fail('read-failed');
  const frameDigest=digest(f[RAW_TOKEN]); let input={state:'missing'}, researchIdentity;
  if (r.rule.kind==='research-value') {
    const e=f.research.fields[column]; if (e && Object.hasOwn(e,'valueJson')) input={state:'present',ref:{frameSha256:frameDigest,location:'research-value'}};
    const field=f.research.declaration.fields.find(e=>e.name===column);
    researchIdentity={recipeRevision:f.research.recordRecipeRevision,fieldSha256:digest(field.fieldJson)};
  } else if (Object.hasOwn(f.values,column)) input={state:'present',ref:{frameSha256:frameDigest,location:'values'}};
  const result=Object.hasOwn(p,'valueJson') ? {state:'value',json:p.valueJson} : {state:'omitted',reason:p.omitted};
  const answer={contractVersion:'1',column,input,result}; if (researchIdentity) answer.researchIdentity=researchIdentity;
  return answer;
}

const PRODUCER_GRAMMAR='desk-reviewed-input/1';
const REVISION_DOMAIN='judgment-pack/retained-column/1/desk-reviewed-input/revision\0';
function compactToken(text) {
  let quoted=false, escaped=false, out='';
  for (const c of text) {
    if (quoted) {out+=c; if (escaped) escaped=false; else if (c==='\\') escaped=true; else if (c==='"') quoted=false;}
    else if (c==='"') {quoted=true;out+=c;}
    else if (!' \t\r\n'.includes(c)) out+=c;
  }
  return out;
}
function revisionIdentity(id,version) {
  if (typeof id!=='string' || !full(/^research_[a-f0-9]{32}$/,id)) fail();
  return digest(REVISION_DOMAIN+id+'\0'+String(positive(version)));
}
function producerContext(t,b) {
  closed(t,['id','profileDigest','class','source','authority','shape','endpoint','adapter','tools','retainedColumnProducer']);
  closed(b,['kind','profile','profileDigest']);closed(t.retainedColumnProducer,['contractVersion','grammar']);closed(t.adapter,['name','version','digest']);
  for (const pin of [t.profileDigest,t.adapter.digest]) if (typeof pin!=='string' || !full(/^sha256:[0-9a-f]{64}$/,pin)) fail();
  string(t.id,64,true);string(t.authority,256,true);
  if (!full(/^[A-Za-z][A-Za-z0-9_-]{0,63}$/,t.id)) fail();
  if (t.retainedColumnProducer.contractVersion!=='1' || t.retainedColumnProducer.grammar!==PRODUCER_GRAMMAR) fail('capability-unsupported');
  if (t.class!=='generated' || t.source!=='desk-inputs' || t.shape!=='mcp' || t.endpoint!=='desk-local:reviewed-inputs' ||
      !Array.isArray(t.tools) || t.tools.length!==1 || t.tools[0]!=='read_reviewed_input' ||
      t.adapter.name!=='jpack-desk/reviewed-input' || t.adapter.version!=='2' ||
      b.kind!=='operation' || b.profile!==t.id || b.profileDigest!==t.profileDigest) fail('profile-mismatch');
}
function producerProjection(snapshot) {
  if (bytes(snapshot)>524288) fail('input-over-bound');
  const original=parse(snapshot,{strict:false});
  if (!object(original)) fail();
  const record=original.record,research=original.research;
  if (!object(record)||!object(research)||!object(record.research)||!object(record.research.entity)||!object(research.recipe)) fail();
  const retained=record.research, declared=research.recipe.fields, fields=retained.entity.fields, values=record.values;
  if (!(original.version instanceof JsonNumber)||original.version.text!=='1'||original.class!=='generated'||record.class!=='generated') fail();
  const revision=revisionIdentity(research.id,research.recipeVersion), other=revisionIdentity(retained.runId,retained.recipeVersion);
  if (revision!==other) fail('read-failed');
  if (!object(values)||!object(fields)||!Array.isArray(declared)) fail();
  if (Math.max(Object.keys(values).length,Object.keys(fields).length,declared.length)>1000) fail('input-over-bound');
  for (const [k,v] of Object.entries(values)) {string(k,160,true);string(v,524288);}
  const names=new Set(), declarations=[];
  for (let i=0;i<declared.length;i++) {
    const f=declared[i];if (!object(f)) fail();string(f.name,160,true);if(names.has(f.name)) fail();names.add(f.name);
    if (!['text','integer','decimal','boolean','text-list','range','string','number'].includes(f.type)) fail();
    declarations.push({name:f.name,fieldJson:compactToken(declared[RAW_ITEMS][i])});
  }
  const projected=Object.create(null);
  for (const [name,e] of Object.entries(fields)) {
    string(name,160,true);if (!object(e)||typeof e.status!=='string'||!STATUS.includes(e.status)) fail();
    const selected={status:e.status};if (Object.hasOwn(e,'value')) selected.valueJson=e[RAW_MEMBERS].value;
    projected[name]=selected;
  }
  return [{grammar:PRODUCER_GRAMMAR,snapshotVersion:1,snapshotClass:'generated',recordClass:'generated',runId:research.id,recordRunId:retained.runId,
    recipeVersion:Number(positive(research.recipeVersion)),recordRecipeVersion:Number(positive(retained.recipeVersion)),values,declarations,fields:projected},revision];
}
function carrierCanon(v) {
  if (Array.isArray(v)) return '['+v.map(carrierCanon).join(',')+']';
  if (object(v)) return '{'+Object.keys(v).sort((a,b)=>Buffer.compare(Buffer.from(a,'utf8'),Buffer.from(b,'utf8'))).map(k=>JSON.stringify(k)+':'+carrierCanon(v[k])).join(',')+'}';
  if (v===null || typeof v==='string' || typeof v==='boolean') return JSON.stringify(v);
  fail('acquisition-invalid');
}
function generatedConsistency(p) {
  closed(p,['carrier','profile','limits','trustedProducer','sourceBinding','receiptResultDigest','rule']);producerContext(p.trustedProducer,p.sourceBinding);
  if (!object(p.carrier)||!object(p.carrier.retained)) fail();
  const r={restore:p.carrier,profile:p.profile,limits:p.limits};
  Object.defineProperty(r,CARRIER_SIZE,{value:bytes(p.carrier[RAW_TOKEN])});
  Object.defineProperty(r,RETAINED_SIZE,{value:bytes(p.carrier.retained[RAW_TOKEN])});restore(r);
  if (p.receiptResultDigest!==digest(carrierCanon(p.carrier))) fail('acquisition-invalid');
  const [source,revision]=producerProjection(p.carrier.originalSnapshotJson), f=p.carrier.retained, research=f.research;
  const equal=(a,b)=>carrierCanon(a)===carrierCanon(b);
  if (research.declaration===null) fail('read-failed');
  if (!equal([research.recordRecipeRevision,research.declaration.recipeRevision],[revision,revision])) fail('read-failed');
  if (!equal(research.declaration.fields,source.declarations)) fail('read-failed');
  if (!equal(f.values,source.values) || !equal(research.fields,source.fields)) fail('read-failed');
  const transformation=lineage({rule:p.rule,frame:f,profile:p.profile},bytes(f[RAW_TOKEN]));
  return {consistent:true,acquisition:'not-verified',history:'not-checked',originalSnapshotSha256:p.carrier.originalSnapshotSha256,
    frameSha256:digest(f[RAW_TOKEN]),revisionIdentity:revision,projection:source,transformation};
}

function verifyLineage(p) {
  closed(p,['rule','frame','transformation'],['profile']);
  const {transformation,...request}=p, expected=lineage(request,typeof p[RAW_MEMBERS]?.frame==='string' ? bytes(p[RAW_MEMBERS].frame) : undefined);
  const same=(a,b)=>a===b || (object(a) && object(b) && Object.keys(a).length===Object.keys(b).length && Object.keys(a).every(k=>Object.hasOwn(b,k) && same(a[k],b[k])));
  if (!same(transformation,expected)) fail('read-failed');
  return {consistent:true,acquisition:'not-verified'};
}
function retainCase(p) {
  closed(p,['source']); const s=p.source; let text;
  if (object(s) && Object.keys(s).length===1 && Object.hasOwn(s,'case')) text=s[RAW_MEMBERS].case;
  else {closed(s,['retainedCaseJson']); text=s.retainedCaseJson; if (typeof text!=='string' || !text) fail();}
  if (!object(parse(text,{strict:false}))) fail();
  return {retainedCaseJson:text};
}
function retainSource(p) {
  closed(p,['source']); const s=p.source; let envelope;
  if (object(s) && Object.keys(s).length===1 && Object.hasOwn(s,'response')) envelope=s[RAW_MEMBERS].response;
  else {closed(s,['retainedResponseJson']); envelope=s.retainedResponseJson; if (typeof envelope!=='string' || !envelope) fail();}
  const parsed=parse(envelope,{strict:false}); closed(parsed,['result','receipt','salts']);
  if (!['result','receipt','salts'].every(k=>object(parsed[k]))) fail();
  return {retainedResponseJson:envelope};
}
function handle(r) {
  if (object(r) && Object.keys(r).length===1 && Object.hasOwn(r,'verifyLineage')) return verifyLineage(r.verifyLineage);
  if (object(r) && Object.keys(r).length===1 && Object.hasOwn(r,'retainCase')) return retainCase(r.retainCase);
  if (object(r) && Object.keys(r).length===1 && Object.hasOwn(r,'retainSource')) return retainSource(r.retainSource);
  if (object(r) && Object.keys(r).length===1 && Object.hasOwn(r,'generatedConsistency')) return generatedConsistency(r.generatedConsistency);
  if (object(r) && Object.hasOwn(r,'restore')) return restore(r);
  if (object(r) && Object.keys(r).length===1 && Object.hasOwn(r,'selection')) return select(r.selection);
  if (object(r) && Object.keys(r).length===1 && Object.hasOwn(r,'admission')) return admit(r.admission);
  if (object(r) && Object.keys(r).length===1 && Object.hasOwn(r,'lineage')) return lineage(r.lineage,r[FRAME_SIZE]);
  if (object(r) && Object.keys(r).length===1 && Object.hasOwn(r,'binary64Hex')) {
    if (typeof r.binary64Hex!=='string' || !full(/^[0-9a-f]{16}$/,r.binary64Hex)) fail();
    const b=new DataView(new ArrayBuffer(8)); b.setBigUint64(0,BigInt('0x'+r.binary64Hex),false); const x=b.getFloat64(0,false);
    if (Math.abs(x)>Number(SAFE)) fail(); const q=shortest(x); if (x<0) q[0]=-q[0];
    return {rational:q[1]===1n ? String(q[0]) : `${q[0]}/${q[1]}`};
  }
  closed(r,['rule','frame'],['profile']); validate(r.rule,r.frame,Object.hasOwn(r,'profile') ? r.profile : 'base',r[FRAME_SIZE]); return preview(r.rule,r.frame);
}

export {parse, validate, lineage, generatedConsistency, producerContext, Refusal, preview, PROFILE_CAPS, ROLE_LIMITS, handle};

// Fatal UTF8 decoding prevents replacement-character repair.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
let pending=Buffer.alloc(0), discarding=false;
const decoder=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true});
function line(input) {
  let output;
  try {
    if (input.length>4200000) fail('input-over-bound');
    let text; try { text=decoder.decode(input); } catch { fail(); }
    output=handle(parse(text));
  } catch (e) { if (!(e instanceof Refusal)) throw e; output={refusal:e.message}; }
  process.stdout.write(JSON.stringify(output)+'\n');
}
for await (let chunk of process.stdin) {
  if (discarding) {
    const end=chunk.indexOf(10); if (end<0) continue;
    chunk=chunk.subarray(end+1); discarding=false;
  }
  pending=Buffer.concat([pending,chunk]);
  let end;
  while ((end=pending.indexOf(10))>=0) { line(pending.subarray(0,end)); pending=pending.subarray(end+1); }
  if (pending.length>4200000) { line(pending); pending=Buffer.alloc(0); discarding=true; }
}
if (pending.length) line(pending);

}

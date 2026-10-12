set pagination off
set confirm off
set print pretty off
python
import gdb,json,hashlib,struct,os,gzip
from pathlib import Path
outdir=Path(os.environ['F11_TRACE_DIR']);outdir.mkdir(parents=True,exist_ok=True)
persistent=False
run=0; counts={}; errors=[]; stream=None; digest=None; pointers={}; summary={}; initcounts={}; tracepaths=[]
def obj(v):
 while v.type.code==gdb.TYPE_CODE_REF:v=v.referenced_value()
 return v.dereference() if v.type.code==gdb.TYPE_CODE_PTR else v
def val(s):return gdb.parse_and_eval(s)
def bits(v):return struct.pack('<d',float(v)).hex()
def vect(v):
 b,e=v['_M_impl']['_M_start'],v['_M_impl']['_M_finish'];n=int(e-b)
 element=b.type.strip_typedefs().target().strip_typedefs();typ=str(element)
 if 'vector<' in typ:return [vect(b[i]) for i in range(n)]
 raw=bytes(gdb.selected_inferior().read_memory(b,n*element.sizeof)) if n else b''
 return {'n':n,'element':typ,'bits':raw.hex()}
def vbool(v):
 b,e=v['_M_impl']['_M_start'],v['_M_impl']['_M_finish'];n=int(e['_M_p']-b['_M_p'])*64+int(e['_M_offset'])-int(b['_M_offset'])
 return [bool((int(b['_M_p'][i//64]) >> (i%64))&1) for i in range(n)]
def stats(v):
 out={}
 for f in v.type.fields():
  if not f.name:continue
  x=v[f.name];t=str(x.type)
  if 'vector<bool' in t:out[f.name]=vbool(x)
  elif 'vector<' in t:out[f.name]=vect(x)
  elif x.type.code in [gdb.TYPE_CODE_INT,gdb.TYPE_CODE_BOOL,gdb.TYPE_CODE_CHAR]:out[f.name]=int(x)
  elif x.type.code==gdb.TYPE_CODE_FLT:out[f.name]=bits(x)
 return out
def tally(v):
 v=obj(v);out={}
 for name in ['p_OCellTallyData','p_OMeshTallyData']:
  d=v[name];out[name]={k:vect(d[k]) for k in ['p_vScore','p_vScoreTemp','p_vSum1','p_vSum2','p_vSum3','p_vAve','p_vRe','p_vScoreIndex2','p_vScoreStride']}
  out[name]['touched']=int(d['p_setScoreIndex']['_M_t']['_M_impl']['_M_node_count'])
  out[name]['statistics']=stats(d['p_OStatisticsTester'])
 return out
def rng(v):
 v=obj(v);x=v['generator']['_M_ptr'].dereference()
 return {k:int(x[k]) for k in ['RN_SEED0','RN_SEED','RN_STRIDE','RN_POSITION','RN_POSITION_PRE']}
def particle(v):
 v=obj(v)
 return {'pos':[bits(v['p_dPos'][i]) for i in range(3)],'dir':[bits(v['p_dDir'][i]) for i in range(3)],'w':bits(v['p_dWgt']),'erg':bits(v['p_dErg']),'type':int(v['p_eParticleType']),'adj':bool(v['p_bIsAdjointParticle']),'killed':bool(v['p_bIsKilled'])}
def fixed(v):
 v=obj(v)
 return {k:int(v[k]) for k in ['p_llCurTotParNum','p_llCurParNumEachPro','p_llCurrentBatch','p_nFinishCalculate','p_nFixedSrcCount','p_llTotCollisionCount']}|{'denominator':bits(v['p_dTotStartWgt'])}
def emit(kind,data):
 if stream is None:return
 counts[kind]=counts.get(kind,0)+1
 s=json.dumps([kind,data],sort_keys=True,separators=(',',':'))+'\n';digest.update(s.encode());stream.write(s)
def snapshot(name,data):
 (outdir/(str(run)+'-'+name+'.json')).write_text(json.dumps(data,sort_keys=True,indent=2))
class Finish(gdb.FinishBreakpoint):
 def __init__(self,cb):super().__init__(gdb.newest_frame(),internal=True);self.cb=cb
 def stop(self):
  try:self.cb();return False
  except Exception as e:errors.append(str(e));print('TRACE_ERROR',e);return True
class Probe(gdb.Breakpoint):
 def __init__(self,name,cb):super().__init__(name,internal=True);self.cb=cb
 def stop(self):
  try:self.cb();return False
  except Exception as e:errors.append(str(e));print('TRACE_ERROR',e);return True

def init(k):initcounts[k]=initcounts.get(k,0)+1

def begin():
 global run,counts,digest,stream,pointers
 run+=1;counts={};digest=hashlib.sha256();stream=gzip.open(outdir/(str(run)+'-trace.jsonl.gz'),'wt')
 for key,arg in [('fixed','cFixedSource'),('particle','CParticleState'),('tally','CTally'),('ace','CAceData'),('rng','ORNG'),('neutron','cNeutronTransport'),('geometry','CGeometry'),('material','CMaterial')]:pointers[key]=obj(val(arg)).address
 snapshot('clear',tally(pointers['tally']))
 a=pointers['ace'].dereference();b=a['p_vNuclides']['_M_impl']['_M_start'];e=a['p_vNuclides']['_M_impl']['_M_finish'];derived=[];raw=[]
 for i in range(1,int(e-b)):
  n=b[i];derived.append({'scatter':vect(n['p_vAdjointCrossSection']),'fission':vect(n['p_vAdjointFissionCrossSection'])});raw.append({k:vect(n[k]) for k in ['XSS','PXSS','NXS','JXS','PNXS','PJXS']})
 snapshot('derived',derived);snapshot('raw',raw)
 snapshot('identity',{k:str(v) for k,v in pointers.items()}|{'nuclides':str(b),'raw':[str(b[i]['XSS']['_M_impl']['_M_start']) for i in range(1,int(e-b))]})
 snapshot('start',{'rng':rng(pointers['rng']),'aceAdj':bool(a['p_bIsAdjoint']),'fixedAdj':bool(pointers['fixed'].dereference()['p_bIsAdjoint']),'neutronCut':bits(pointers['neutron'].dereference()['p_dWgtCutOff']),'neutronEnergyCutoff':bits(pointers['neutron'].dereference()['p_dEg0CutOff']),'fixedMaxNeutron':bits(pointers['fixed'].dereference()['p_dMaxAdjointNeutronEnergy']),'fixedMaxPhoton':bits(pointers['fixed'].dereference()['p_dMaxAdjointPhotonEnergy'])})
 def endexecute():snapshot('before-finalize',tally(pointers['tally']))
 Finish(endexecute)
def sample():
 emit('RNG_BEFORE_SAMPLE',rng(val('ORNG')))
def source_after():
 emit('SOURCE',particle(pointers['particle'])|{'fixedAdj':bool(pointers['fixed'].dereference()['p_bIsAdjoint']),'aceAdj':bool(pointers['ace'].dereference()['p_bIsAdjoint'])})
def history():emit('HISTORY',{'scores':{n:vect(obj(val('this'))[n]['p_vScore']) for n in ['p_OCellTallyData','p_OMeshTallyData']},'rng':rng(pointers['rng'])})
pending_query=None
def ww():
 global pending_query
 if pending_query is None:raise RuntimeError('WW action without query')
 emit('WW_QUERY',pending_query|{k:bits(val(n)) for k,n in [('lower','dLowWeightBound'),('survive','dSurvivalWeight'),('upper','dUpperWeightBound')]});pending_query=None
 s=obj(val('cParticleState'));lo=float(val('dLowWeightBound'));hi=float(val('dUpperWeightBound'));w=float(s['p_dWgt'])
 if lo and w<lo:emit('ROULETTE',particle(s)|{'lo':bits(val('dLowWeightBound')),'hi':bits(val('dUpperWeightBound'))})
 elif lo and w>hi:emit('SPLIT',particle(s)|{'lo':bits(val('dLowWeightBound')),'hi':bits(val('dUpperWeightBound'))})
def query():
 global pending_query
 if pending_query is not None:raise RuntimeError('unconsumed WW query')
 pending_query={'mesh':int(obj(val('meshIndex'))),'erg':bits(obj(val('erg'))),'particle':int(val('particleType'))}
def close_run():
 global stream
 snapshot('final',tally(pointers['tally']))
 snapshot('end',{'rng':rng(pointers['rng']),'fixed':fixed(pointers['fixed'])})
 stream.close();stream=None
 snapshot('trace-summary',{'counts':counts,'sha256':digest.hexdigest(),'initcounts':initcounts.copy()})
def process():
 emit('FINALIZE_ENTRY',fixed(val('cFixedSource')))
 if not persistent:Finish(close_run)
def run_prepared():
 global persistent
 persistent=True
 Finish(close_run)
Probe('CDCalMode::RunPreparedFixedSource',run_prepared)
Probe('CDFixedSource::InitiateAll',lambda:init('InitiateAll'))
Probe('CDMaterial::InitiateMatAce',lambda:init('InitiateMatAce'))
Probe('CDAceData::ReadAceData',lambda:init('ReadAceData'))
Probe('CDTally::InitiateTally',lambda:init('InitiateTally'))
Probe('CDCalMode::ExecuteFixedSourcePrepared',begin)
Probe('CDFixedSource::SampleFixSource',sample)
Probe('CalcFixedSource.cpp:186',source_after)
Probe('CDFixedSource::TrackHistory',lambda:emit('TRACK',particle(val('cParticleState'))))
Probe('CDTally::TallyByTL',lambda:emit('SEGMENT',particle(val('cParticleState'))|{'length':bits(val('dTrackLen'))}))
Probe('CDTally::SumUpTally(long long, double)',history)
Probe('CDWeightWindow::DoWeightWindows',ww)
Probe('CDWeightWindow::setMeshWeightWindowBound',query)
Probe('CDFixedSource::SampleFromParticleBank',lambda:emit('BANK',rng(val('ORNG'))))
Probe('CDTally::ProcessTally(CDFixedSource&, CDMaterial&, CDAceData&)',process)
Probe('CDTally::OutputTallyh5',lambda:Finish(lambda:snapshot('legacy',tally(pointers['tally']))))
end
run
python
if stream:stream.close()
(outdir/'observer.json').write_text(json.dumps({'errors':errors,'runs':run,'initcounts':initcounts},indent=2))
if errors:gdb.execute('quit 3')
code=gdb.parse_and_eval('$_exitcode')
if code.type.code==gdb.TYPE_CODE_VOID:gdb.execute('quit 4')
if int(code)!=0:gdb.execute('quit '+str(int(code)))
end
quit

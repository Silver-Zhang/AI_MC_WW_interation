# Read-only debugger observer: no inferior calls or state assignments.
import gdb,json
out=open('velocity.jsonl','w');errors=[];ace=None;first=False;track=0;bank=False

def emit(event,**data):
 out.write(json.dumps(dict(event=event,**data),allow_nan=True)+'\n');out.flush()
def obj(v):
 while v.type.code==gdb.TYPE_CODE_REF:v=v.referenced_value()
 return v.dereference() if v.type.code==gdb.TYPE_CODE_PTR else v
def val(s):return gdb.parse_and_eval(s)
def ptr(v):
 v=obj(v);return gdb.Value(int(v.address)).cast(v.type.pointer())
def particle(v):
 v=obj(v)
 return {k:float(v[k]) for k in ['p_dErg','p_dVel','p_dTime','p_dWgt']}|{k:int(v[k]) for k in ['p_nMultiGrpNumber','p_bIsAdjointParticle']}
def rng(v):
 x=obj(v)['generator']['_M_ptr'].dereference()
 return {k:int(x[k]) for k in ['RN_SEED','RN_POSITION','RN_POSITION_PRE']}
def guard(fn):
 try:fn()
 except Exception as e:errors.append(str(e));emit('observer_error',error=str(e))
class Probe(gdb.Breakpoint):
 def __init__(self,name,fn):super().__init__(name,internal=True);self.fn=fn
 def stop(self):guard(self.fn);return False
class Finish(gdb.FinishBreakpoint):
 def __init__(self,fn):super().__init__(gdb.newest_frame(),internal=True);self.fn=fn
 def stop(self):guard(self.fn);return False

def source():
 global ace
 p=ptr(val('cParticleState'));a=obj(val('cAceData'));ace=a.address
 if not hasattr(source,'seen'):
  G=int(a['p_nNeuMltGrpNum']);mg=bool(a['p_bIsMultiGroup'])
  emit('model',MG=mg,G=G,centers=[float(a['p_vNeuMltCentErg']['_M_impl']['_M_start'][i]) for i in range(G)] if mg else [])
  source.seen=True
 Finish(lambda:emit('sample',particle=particle(p)))
def sampled():
 global bank
 bank=False;emit('mapped',particle=particle(val('cParticleState')),rng=rng(val('ORNG')))
def restored():
 global bank
 bank=True;emit('bank',particle=particle(val('cParticleState')))
def tracking():
 global first,track
 first=True;track+=1

def fly():
 global first
 if not first:return
 first=False;p=ptr(val('this'));L=float(val('dLength'));before=particle(p);tag='bank' if bank else 'source'
 emit('flight_before',track=track,phase=tag,length=L,particle=before)
 n=track
 Finish(lambda:emit('flight_after',track=n,phase=tag,length=L,time_before=before['p_dTime'],particle=particle(p)))
Probe('CDSource::SampleParticle',source)
Probe('SampleNeutronSource.cpp:281',sampled)
Probe('SampleNeutronSource.cpp:325',restored)
Probe('CDFixedSource::TrackHistory',tracking)
Probe('CDParticleState::FlyByLength',fly)
def collision():
 p=ptr(val('this'));Finish(lambda:emit('collision_updated',particle=particle(p)))
Probe('CDParticleState::UpdateNeuStateMg',collision)
# Group argument is observed at the helper boundary without invoking it.
class MG(Probe):
 def stop(self):
  def inspect():
   try:x=float(val('dGroup'))
   except gdb.error:x=float(val('p_dErg'))
   emit('mg_argument',value=x,G=int(val('nMltGrpNum')),caller=gdb.newest_frame().older().name())
  guard(inspect);return False
MG('CDGlobeFun::GetNeuVelMg',lambda:None)
def split():emit('push_split')
def induced():emit('push_induced')
# Function symbols verified against SaveSplitParticles.cpp.
Probe('CDFixedSource::pushSplitParticles',split)
Probe('CDFixedSource::pushInducedParticles',induced)
gdb.events.exited.connect(lambda e:emit('exit',code=getattr(e,'exit_code',None),errors=errors))
gdb.execute('run')
if errors:gdb.execute('quit 3')

# Read-only GDB observer. No inferior function calls or assignments.
import gdb, json, collections, os
out=open('events.jsonl','w'); counts=collections.Counter(); errors=[]
track=0; first=False; origin='unknown'; model_seen=False
def emit(event,**kw):
 counts[event]+=1
 if counts[event]<=600:
  out.write(json.dumps(dict(event=event,track=track,origin=origin,**kw),allow_nan=True)+'\n');out.flush()
def obj(v):
 while v.type.code==gdb.TYPE_CODE_REF:v=v.referenced_value()
 return v.dereference() if v.type.code==gdb.TYPE_CODE_PTR else v
def ev(x):return gdb.parse_and_eval(x)
def ptr(v):
 v=obj(v);return gdb.Value(int(v.address)).cast(v.type.pointer())
def particle(v):
 p=obj(v)
 return {k:float(p[k]) for k in ['p_dErg','p_dVel','p_dTime','p_dWgt','p_dExitErg','p_dMacroTotCs']}|{k:int(p[k]) for k in ['p_eParticleType','p_nMultiGrpNumber','p_bIsAdjointParticle','p_nMAT','p_nNUC','p_bIsKilled']}
def model(a):
 global model_seen
 if model_seen:return
 a=obj(a);mg=bool(a['p_bIsMultiGroup']);d={'mg':mg}
 for prefix in ['Neu','Pho']:
  G=int(a['p_n'+prefix+'MltGrpNum']);d[prefix+'G']=G
  d[prefix+'centers']=[float(a['p_v'+prefix+'MltCentErg']['_M_impl']['_M_start'][i]) for i in range(G)] if mg else []
 emit('model',**d);model_seen=True
def guarded(fn):
 try:fn()
 except Exception as e:errors.append(str(e));emit('observer_error',message=str(e))
class Probe(gdb.Breakpoint):
 def __init__(self,spec,fn):super().__init__(spec,internal=True);self.fn=fn;self.hits=0;self.limit=180 if fn.__name__=="track_start" else 2000 if fn.__name__=="fly" else (600 if fn.__name__=="filter_check" else (62 if fn.__name__ in ["xs","mg_argument"] else 31))
 def stop(self):
  self.hits+=1;guarded(self.fn)
  if self.hits>=self.limit:
   self.enabled=False;emit("probe_limit",spec=self.location,hits=self.hits)
  return False
class Finish(gdb.FinishBreakpoint):
 def __init__(self,fn):super().__init__(gdb.newest_frame(),internal=True);self.fn=fn
 def stop(self):guarded(lambda:self.fn(self));return False
def sampled():
 model(ev('cAceData'));p=ptr(ev('cParticleState'));Finish(lambda f:emit('sample_mev',particle=particle(p)))
def mapped():
 global origin
 origin='source';model(ev('cAceData'));emit('source_ready',particle=particle(ev('cParticleState')))
def watt():emit('watt_final',particle=particle(ev('cParticleState')))
def pop():
 global origin
 origin='bank';emit('bank_ready',particle=particle(ev('cParticleState')))
def track_start():
 global track,first
 track+=1;first=True
 emit('track_start',function=gdb.newest_frame().name(),particle=particle(ev('cParticleState')))
def fly():
 global first
 if not first:return
 first=False;p=ptr(ev('this'));L=float(ev('dLength'));before=particle(p);n=track
 emit('flight_before',length=L,particle=before)
 Finish(lambda f:emit('flight_after',flight_track=n,length=L,time_before=before['p_dTime'],particle=particle(p)))
def update():
 p=ptr(ev('this'));fn=gdb.newest_frame().name();emit('collision_before',function=fn,particle=particle(p))
 Finish(lambda f:emit('collision_after',function=fn,particle=particle(p)))
def gamma_update():
 p=ptr(ev('cParticleState'));Finish(lambda f:emit('gamma_collision_after',particle=particle(p)))
def mg_argument():
 try:g=float(ev('dGroup'))
 except gdb.error:g=float(ev('p_dErg'))
 emit('mg_velocity_arg',value=g,G=int(ev('nMltGrpNum')),caller=gdb.newest_frame().older().name())
def xs():
 nuc=int(ev('nNuc'));g=int(ev('nIncidGrp'));fn=gdb.newest_frame().name()
 Finish(lambda f:emit('xs',function=fn,nuc=nuc,group=g,value=float(f.return_value)))
def macro():
 p=ptr(ev('cParticleState'));emit('macro_before',particle=particle(p))
 Finish(lambda f:emit('macro_after',particle=particle(p)))
def induced():
 emit('bank_push_induced',energy=float(ev('dErg')))
def split():emit('bank_push_split',particle=particle(ev('cParticleState')))
def restore_other():
 global origin
 origin='other_bank';emit('other_ready',function=gdb.newest_frame().name(),particle=particle(ev('cParticleState')))
def filter_check():
 p=particle(ev('cParticleState'));f=ptr(ev('this'));v=obj(f)['ergGrpNumber'];a=v['_M_impl']['_M_start'];b=v['_M_impl']['_M_finish'];groups=[int(a[i]) for i in range(int(b-a))]
 Finish(lambda done:emit('filter',particle=p,groups=groups,passed=bool(obj(f)['pass'])))
for name,fn in [('CDErgGrpFilter::passCheck',filter_check),('CDSource::SampleParticle',sampled),('SampleNeutronSource.cpp:281',mapped),('ExternalSource.cpp:501',watt),('SampleNeutronSource.cpp:'+('321' if os.environ.get('W14_VERSION')=='original' else '325'),pop),('CDFixedSource::TrackHistory',track_start),('CDCriticality::TrackHistory',track_start),('CDPhotonTransport::TrackGmaHistory',track_start),('CDElectronTransport::TrackElectronHistory',track_start),('CDParticleState::FlyByLength',fly),('CDParticleState::UpdateNeuState',update),('CDParticleState::UpdateNeuStateMg',update),('CDPhotonTransport::TreatMgPhotonReaction',gamma_update),('CDGlobeFun::GetNeuVelMg',mg_argument),('CDAceData::GetMgNeuNucTotCs',xs),('CDAceData::GetMgPhoNucTotCs',xs),('CDNeutronTransport::CalcMacroXS',macro),('CDFixedSource::pushInducedParticles',induced),('CDFixedSource::pushSplitParticles',split),('SampleNeutronSource.cpp:'+('391' if os.environ.get('W14_VERSION')=='original' else '395'),restore_other),('SampleNeutronSource.cpp:174',restore_other),('SampleNeutronSource.cpp:'+('476' if os.environ.get('W14_VERSION')=='original' else '480'),restore_other)]:
 Probe(name,fn)
gdb.events.exited.connect(lambda e:emit('exit',code=getattr(e,'exit_code',None)))
gdb.events.stop.connect(lambda e:emit('signal',signal=e.stop_signal) if isinstance(e,gdb.SignalEvent) else None)
gdb.execute('set pagination off');gdb.execute('set confirm off');gdb.execute('run')
emit('summary',counts=dict(counts),errors=errors)
if errors:gdb.execute('quit 3')

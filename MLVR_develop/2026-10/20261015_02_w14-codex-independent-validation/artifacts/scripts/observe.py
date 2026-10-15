# Executed by GDB. Read-only: breakpoints inspect values; no inferior calls or assignments.
import gdb,json
out=open('events.jsonl','w'); errors=[]; phase='source'; flights=0; after_collision=False; bank_seen=False

def val(expr):
 v=gdb.parse_and_eval(expr)
 return int(v) if v.type.code in (gdb.TYPE_CODE_INT,gdb.TYPE_CODE_ENUM,gdb.TYPE_CODE_BOOL) else float(v)
def emit(event,**data):
 data['event']=event;out.write(json.dumps(data,allow_nan=True)+'\n');out.flush()
def particle(prefix):
 return {k:val(prefix+k) for k in ['p_dErg','p_dVel','p_dTime','p_dWgt','p_nMultiGrpNumber','p_bIsAdjointParticle']}
def guarded(fn):
 try:fn()
 except Exception as e:errors.append(str(e));emit('observer_error',error=str(e),frame=gdb.newest_frame().name())
class Once(gdb.Breakpoint):
 def __init__(self,loc,fn):super().__init__(loc,internal=True);self.fn=fn
 def stop(self):guarded(self.fn);self.enabled=False;return False

def src():
 G=val('cAceData.p_nNeuMltGrpNum')
 cs=[val('cAceData.p_vNeuMltCentErg._M_impl._M_start[%d]'%i) for i in range(G)]
 lo=[val('cAceData.p_vNeuMltErgBins._M_impl._M_start[%d]'%i) for i in range(G)]
 emit('source_before_velocity',source_E=val('p_dEnergy'),G=G,centers=cs,lower=lo,ace_adjoint=val('cAceData.p_bIsAdjoint'),particle=particle('cParticleState.'))
def mg():
 emit('get_mg_velocity',argument=val('p_dErg'),G=val('nMltGrpNum'),index=val('k'),size=val('(long)(vMltCentErg._M_impl._M_finish-vMltCentErg._M_impl._M_start)'),caller=gdb.newest_frame().older().name())
Once('SampleParticle.cpp:82',src)
def mg_entry():
 b=gdb.newest_frame().block()
 while b.function is None:b=b.superblock
 instructions=gdb.newest_frame().architecture().disassemble(b.start,b.end)
 locations=[x['addr'] for x in instructions if gdb.find_pc_line(x['addr']).line==544]
 if not locations:raise RuntimeError('cannot locate actual index dereference instruction')
 Once('*'+hex(locations[0]),mg)
Once('CDGlobeFun::GetNeuVelMg',mg_entry)
Once('SampleParticle.cpp:88',lambda:emit('source_after_velocity',particle=particle('cParticleState.')))
Once('SampleNeutronSource.cpp:273',lambda:emit('mapped_source',particle=particle('cParticleState.')))
Once('TrackHistory.cpp:171',lambda:emit('track_entry',particle=particle('cParticleState.')))
Once('TrackHistory.cpp:275',lambda:emit('before_first_collision_exit',particle=particle('cParticleState.')))
def postcollision():
 global after_collision
 after_collision=True;emit('after_first_survived_collision',particle=particle('this->'))
Once('ParticleStateFun.cpp:139',postcollision)
class FinishFly(gdb.FinishBreakpoint):
 def __init__(self,ptr,before,length,tag):
  super().__init__(gdb.newest_frame(),internal=True);self.ptr=ptr;self.before=before;self.length=length;self.tag=tag
 def stop(self):
  guarded(lambda:emit('flight_after',phase=self.tag,length=self.length,time_before=self.before,particle=particle('((CDParticleState*)%d)->'%self.ptr)))
  return False
class Fly(gdb.Breakpoint):
 def __init__(self):super().__init__('CDParticleState::FlyByLength',internal=True);self.source_done=False;self.collision_done=False;self.bank_done=False
 def stop(self):
  global phase
  tag='bank' if bank_seen else ('postcollision' if after_collision else 'source')
  attr={'bank':'bank_done','postcollision':'collision_done','source':'source_done'}[tag]
  if not getattr(self,attr):
   def inspect():
    ptr=int(gdb.parse_and_eval('this'));L=val('dLength');t=val('this->p_dTime')
    emit('flight_before',phase=tag,length=L,particle=particle('this->'))
    FinishFly(ptr,t,L,tag)
   guarded(inspect);setattr(self,attr,True)
  if self.source_done and self.collision_done and self.bank_done:self.enabled=False
  return False
Fly()
def bank():
 global bank_seen
 bank_seen=True;emit('bank_after_velocity',particle=particle('cParticleState.'))
Once('SampleNeutronSource.cpp:321',bank)
def exited(e):emit('exit',exitcode=getattr(e,'exit_code',None),observer_errors=errors)
gdb.events.exited.connect(exited)
gdb.execute('run')

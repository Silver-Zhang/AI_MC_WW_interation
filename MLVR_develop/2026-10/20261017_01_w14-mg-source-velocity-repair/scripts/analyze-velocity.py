from pathlib import Path
from decimal import Decimal,getcontext
import json,bisect,math,re,sys
from collections import Counter
P=Path('/tmp/w14-repair-20261017');D=Path('/home/silver/NucXS_Library/RMC_DATA');getcontext().prec=50
# Independent parsing of original ASCII MGACE; no production function calls.
lines=(D/'multigroup/mgxsnp').read_text().splitlines();records={}
for name,first in [('1001.50m',0),('8016.50m',11884),('92235.50m',62338)]:
 assert lines[first].split()[0]==name
 nxs=[int(x) for l in lines[first+6:first+8] for x in l.split()];jxs=[int(x) for l in lines[first+8:first+12] for x in l.split()];n,G=nxs[0],nxs[4]
 x=[Decimal(x) for l in lines[first+12:first+12+(n+3)//4] for x in l.split()][:n];start=jxs[0]-1;cs=list(reversed(x[start:start+G]));width=list(reversed(x[start+G:start+2*G]));lo=[c-w/2 for c,w in zip(cs,width)]
 records[name]={'centers':[str(c) for c in cs],'lower':[str(v) for v in lo],'G':G}
def vref(E):
 e=Decimal(str(E));m=Decimal('939.56542052');c=Decimal('299.792458');return c*(e*(e+2*m)).sqrt()/(e+m)
def checkclose(actual,expected):return math.isfinite(actual) and abs(Decimal(str(actual))-expected)<=Decimal('1e-12')*abs(expected)
results=[]
for d in sorted((P/'runs/after/velocity-final').iterdir()):
 if not (d/'exitcode').exists():continue
 errors=[];events=[json.loads(l) for l in (d/'velocity.jsonl').read_text().splitlines()] if (d/'velocity.jsonl').exists() else []
 def require(cond,err):
  if not cond:errors.append(err)
 require((d/'exitcode').read_text()=='0','exit')
 require(not any(x['event']=='observer_error' for x in events),'observer errors')
 models=[x for x in events if x['event']=='model'];require(len(models)==1,'model absent')
 if not models:
  results.append({'case':d.name,'passed':False,'errors':errors});continue
 model=models[0];mg=model['MG'];rec=records['92235.50m' if 'fission' in d.name else '1001.50m'];G=rec['G'];centers=[Decimal(x) for x in rec['centers']];lower=[Decimal(x) for x in rec['lower']]
 if mg:require(model['G']==G and model['centers']==[float(x) for x in centers],'MGACE centers differ')
 expected_sample=None;sample_argument=None;samples=Counter();count=Counter();maxv=Decimal(0);maxdt=Decimal(0);cache=0;firstflight=None;firstbank=None
 def center(g):
  if not math.isfinite(g) or g!=int(g) or not 1<=g<=G:raise ValueError('invalid group '+str(g))
  return centers[G-int(g)]
 for event in events:
  kind=event['event'];count[kind]+=1
  if kind=='mg_argument':
   require(event['G']==G and event['value']==int(event['value']) and 1<=event['value']<=G,'unsafe helper argument')
   if event['caller']=='CDSource::SampleParticle':sample_argument=event['value']
  if 'particle' not in event:continue
  q=event['particle'];E=q['p_dErg'];v=q['p_dVel']
  if kind=='sample':
   samples[str(E)]+=1;i=max(0,min(G-1,bisect.bisect_right(lower,Decimal(str(E)))-1));expected_sample=G-i
   if mg:require(sample_argument==expected_sample,'source mapped helper argument')
   expected=vref(centers[i] if mg else E)
  else:
   try:expected=vref(center(E) if mg else E)
   except ValueError as exc:errors.append(str(exc));continue
  if kind=='mapped' and mg:require(E==expected_sample,'source mapping changed')
  require(checkclose(v,expected),kind+' velocity')
  if math.isfinite(v):maxv=max(maxv,abs(Decimal(str(v))/expected-1))
  if kind=='bank':
   if mg and q['p_nMultiGrpNumber']!=E:cache+=1
   if firstbank is None:firstbank=event|{'v_ref':str(expected),'center_MeV':str(center(E)) if mg else str(E)}
  if kind=='flight_after':
   before=Decimal(str(event['time_before']));after=Decimal(str(q['p_dTime']));dt=Decimal(str(event['length']))/expected
   scale=max(abs(before),abs(after),abs(dt),Decimal('1e-300'));error=abs((after-before)-dt)
   require(after.is_finite() and error<=Decimal('1e-12')*scale,'first flight dt')
   maxdt=max(maxdt,error/scale)
   if firstflight is None:firstflight=event|{'dt_ref':str(dt),'v_ref':str(expected)}
 require(count['sample']==101 and count['mapped']==101,'history count')
 require(count['flight_after']==count['flight_before'] and count['flight_after']>=101,'flight coverage')
 if 'spectrum' in d.name:require(len(samples)==3,'all 3 discrete energies observed')
 if 'WW' in d.name:require(count['push_split']>0 and count['bank']>0,'WW split/bank missing')
 if 'fission' in d.name:require(count['push_induced']>0 and count['bank']>0 and count['push_split']==0,'fission bank missing')
 results.append({'case':d.name,'passed':not errors,'errors':errors[:20],'counts':dict(count),'sampled_energies':dict(samples),'max_velocity_relative_error':str(maxv),'max_flight_time_scaled_error':str(maxdt),'bank_cache_mismatch_observations':cache,'first_flight':firstflight,'first_bank':firstbank})
 print(d.name,not errors,'histories',count['mapped'],'bank',count['bank'],'errors',len(errors),flush=True)
(P/'velocity-results.json').write_text(json.dumps({'tolerances':{'velocity_relative':'1e-12','time_scaled':'1e-12'},'MGACE':records,'cases':results},indent=2));sys.exit(any(not x['passed'] for x in results))

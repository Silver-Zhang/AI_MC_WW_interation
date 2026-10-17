from pathlib import Path
from decimal import Decimal as D,getcontext
import json,math,bisect,collections
getcontext().prec=50
P=Path('/tmp/w14-energy-audit-20261017');lines=Path('/home/silver/NucXS_Library/RMC_DATA/multigroup/mgxsnp').read_text().splitlines();records={}
for name in ['1001.50m','8016.50m','92235.50m','1000.01g','8000.01g']:
 i=next(i for i,l in enumerate(lines) if l.split() and l.split()[0]==name)
 nxs=[int(x) for l in lines[i+6:i+8] for x in l.split()];jxs=[int(x) for l in lines[i+8:i+12] for x in l.split()];n,G=nxs[0],nxs[4]
 x=[D(x) for l in lines[i+12:i+12+(n+3)//4] for x in l.split()][:n];c=list(reversed(x[jxs[0]-1:jxs[0]-1+G]));w=list(reversed(x[jxs[0]-1+G:jxs[0]-1+2*G]))
 records[name]={'G':G,'centers':c,'lower':[a-b/2 for a,b in zip(c,w)],'total_xs':x[jxs[1]-1:jxs[1]-1+G]}
def lookup(E,typ=1):
 r=records['1001.50m' if typ==1 else '1000.01g'];return r['G']-max(0,min(r['G']-1,bisect.bisect_right(r['lower'],D(str(E)))-1))
def center(g,typ=1):
 r=records['1001.50m' if typ==1 else '1000.01g']
 if not math.isfinite(g) or g!=int(g) or not 1<=g<=r['G']:raise ValueError('invalid group')
 return r['centers'][r['G']-int(g)]
def velocity(e,typ=1):
 if typ==2:return D('299.792458')
 e=D(str(e));m=D('939.56542052') if typ==1 else D('0.51099895')
 return D('299.792458')*(e*(e+2*m)).sqrt()/(e+m)
def clean(x):
 if isinstance(x,D):return str(x)
 if isinstance(x,float) and not math.isfinite(x):return str(x)
 if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
 if isinstance(x,list):return [clean(v) for v in x]
 return x
selected=[('corrected-pilot',n) for n in ['F-middle_center','F-maxwell','F-photon','CE-electron']]+[('final',p.name) for p in sorted((P/'runs/final').iterdir()) if p.name not in ['MG-critical','F-fission']]+[('fission-final','F-fission'),('extended','MG-critical'),('filter-final','A-photon-filter'),('original','F-type5')]
results=[]
for label,name in selected:
 d=P/'runs'/label/name;e=[json.loads(x) for x in (d/'events.jsonl').read_text().splitlines()];counts=collections.Counter(x['event'] for x in e);mg='MGACE' in (d/'inp').read_text();ctr=collections.Counter();examples={};maxv=D(0);maxt=D(0);last_final=None;samples=set();tracks={};first_xs={};xscomp=0;xsmismatch=0
 for x in e:
  kind=x['event'];q=x.get('particle');
  if kind=='xs':
   photon='Pho' in x['function'];recname=('1000.01g' if x['nuc']==1 else '8000.01g') if photon else ('92235.50m' if name in ['F-type5','MG-critical','F-fission'] else ('1001.50m' if x['nuc']==1 else '8016.50m'))
   a=records[recname]['total_xs'];g=x['group'];ref=a[g-1] if 1<=g<=len(a) else None;xscomp+=1
   if ref is None or abs(D(str(x['value']))-ref)>D('1e-12')*max(abs(ref),D('1e-300')):xsmismatch+=1
   first_xs.setdefault(x['track'],x|{'table_xs':ref,'record':recname});continue
  if q is None:continue
  E=q['p_dErg'];typ=q['p_eParticleType'];actual=q['p_dVel']
  if kind in ['sample_mev','watt_final']:
   samples.add(E)
   if kind=='watt_final' or 'type5' not in name:last_final=E
  if kind=='track_start':tracks[x['track']]=x
  if kind=='source_ready' and mg and last_final is not None:
   ctr['mapped_checks']+=1
   if E!=lookup(last_final,typ):ctr['mapped_mismatch']+=1;examples.setdefault('mapped_mismatch',x|{'last_MeV':last_final,'expected_g':lookup(last_final,typ)})
  if kind in ['source_ready','bank_ready','collision_after','gamma_collision_after','track_start'] and mg and not q['p_bIsKilled']:
   ctr[kind+'_cache_checks']+=1
   if q['p_nMultiGrpNumber']!=E:ctr[kind+'_cache_mismatch']+=1;examples.setdefault(kind+'_cache_mismatch',x)
  if kind=='filter':
   ctr['filter_checks']+=1;expected=E in x['groups']
   if x['passed']!=expected:ctr['filter_mismatch']+=1;examples.setdefault('filter_mismatch',x|{'expected_pass':expected})
  if kind not in ['sample_mev','watt_final','source_ready','bank_ready','track_start','flight_before','flight_after','collision_after','gamma_collision_after','other_ready']:continue
  if q['p_bIsKilled']:continue
  try:
   Eref=center(lookup(E,typ),typ) if mg and kind in ['sample_mev','watt_final'] else center(E,typ) if mg else D(str(E))
   ref=velocity(Eref,typ);rel=abs(D(str(actual))/ref-1) if math.isfinite(actual) and ref>0 else D('Infinity');ctr[kind+'_v_checks']+=1
   if rel>D('1e-12'):ctr[kind+'_v_mismatch']+=1;examples.setdefault(kind+'_v_mismatch',x|{'energy_ref_MeV':Eref,'v_ref':ref,'rel_error':rel})
   if rel.is_finite():maxv=max(maxv,rel)
   if kind=='flight_after':
    before=D(str(x['time_before']));after=D(str(q['p_dTime']));dt=D(str(x['length']))/ref;ctr['time_checks']+=1
    err=abs((after-before)-dt)/max(abs(after),abs(before),abs(dt),D('1e-300')) if after.is_finite() and before.is_finite() else D('Infinity')
    if err>D('1e-12'):ctr['time_mismatch']+=1;examples.setdefault('time_mismatch',x|{'dt_ref':dt,'v_ref':ref})
    if err.is_finite():maxt=max(maxt,err)
  except (ValueError,ArithmeticError) as exc:
   ctr[kind+'_invalid_energy']+=1;examples.setdefault(kind+'_invalid_energy',x|{'error':str(exc)})
 for track,x in first_xs.items():
  tr=tracks.get(track)
  if label=='original' and tr and tr['origin']=='bank' and tr['particle']['p_dErg']!=int(tr['particle']['p_dErg']):
   phys=tr['particle']['p_dErg'];g=lookup(phys);examples.setdefault('wrong_xs_group',{'bank_MeV':phys,'expected_g':g,'actual':x,'correct_table_xs':records['92235.50m']['total_xs'][g-1]})
 results.append({'label':label,'case':name,'exitcode':int((d/'exitcode').read_text()),'observer_errors':[x for x in e if x['event']=='observer_error'],'counts':dict(counts),'checks':dict(ctr),'sample_unique':len(samples),'sample_MeV_minmax':[min(samples),max(samples)] if samples else [],'max_velocity_relative_error':maxv,'max_time_scaled_error':maxt,'xs_table_checks':xscomp,'xs_table_mismatch':xsmismatch,'examples':examples})
 print(label,name,'exit',results[-1]['exitcode'],'v',str(maxv)[:12],'cache',sum(v for k,v in ctr.items() if 'cache_mismatch' in k),'xs',xscomp,xsmismatch,'filter',ctr['filter_mismatch'],flush=True)
(P/'results.json').write_text(json.dumps(clean({'tolerances':{'velocity_relative':'1e-12','time_scaled':'1e-12'},'records':records,'cases':results}),ensure_ascii=False,indent=2,allow_nan=False))

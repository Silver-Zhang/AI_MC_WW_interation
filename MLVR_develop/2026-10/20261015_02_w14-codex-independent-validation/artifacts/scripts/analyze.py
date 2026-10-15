from pathlib import Path
from decimal import Decimal,getcontext
import json,math,hashlib,subprocess
P=Path('/tmp/w14-codex-review');getcontext().prec=50;db=json.loads((P/'logs/mgace-groups.json').read_text())['1001.50m'];centers=[Decimal(x) for x in db['centers']]
def speed(E):
 c=Decimal('299.792458');m=Decimal('939.56542052');return c*(E*(E+2*m)).sqrt()/(E+m)
def rel(x,r):return (float(x)-float(r))/float(r)
results=[]
for case in json.loads((P/'cases.json').read_text()):
 d=P/'runs/gdb-final'/case['name'];ev=[json.loads(s) for s in (d/'events.jsonl').read_text().splitlines()]
 def one(name):return next((e for e in ev if e['event']==name),None)
 errors=[e for e in ev if e['event']=='observer_error'];assert not errors,errors
 assert one('exit')['exitcode']==0
 assert 'Source Number : 101.' in (d/'inp.out').read_text()
 source=one('source_before_velocity');mg=one('get_mg_velocity');mapped=one('mapped_source')['particle'];init=one('source_after_velocity')['particle'];flight=next(e for e in ev if e['event']=='flight_before' and e['phase']=='source');after=next(e for e in ev if e['event']=='flight_after' and e['phase']=='source');post=one('after_first_survived_collision')['particle']
 assert source['G']==mg['size']==30
 assert source['centers']==[float(c) for c in centers]
 assert mg['argument']==source['source_E']
 if 'correct_group' in case:assert mapped['p_dErg']==case['correct_group']
 vref=speed(centers[30-int(mapped['p_dErg'])]);postref=speed(centers[30-int(post['p_dErg'])]);assert abs(rel(post['p_dVel'],postref))<=1e-12
 assert flight['particle']['p_dVel']==init['p_dVel']==mapped['p_dVel']
 r={'name':case['name'],'E_MeV':case['physical_E'],'histories':101,'exitcode':0,'G':30,'observed_index':mg['index'],'index_safe':0<=mg['index']<30,'mapped_group':int(mapped['p_dErg']),'initial_v':init['p_dVel'],'v_ref':str(vref),'v_relative_error':rel(init['p_dVel'],vref),'first_length_cm':flight['length'],'first_time_actual_shake':after['particle']['p_dTime'],'first_time_ref_shake':str(Decimal(str(flight['length']))/vref),'postcollision_group':post['p_dErg'],'postcollision_v':post['p_dVel'],'postcollision_relative_error':rel(post['p_dVel'],postref),'postcollision_total_time':post['p_dTime'],'observer_errors':[]}
 bank=one('bank_after_velocity')
 if bank:
  p=bank['particle'];bv=speed(centers[30-int(p['p_dErg'])]);bf=next(e for e in ev if e['event']=='flight_before' and e['phase']=='bank');r['bank']={'particle':p,'v_ref':str(bv),'v_relative_error':rel(p['p_dVel'],bv),'first_flight_v':bf['particle']['p_dVel'],'first_length_cm':bf['length'],'ref_time_increment':str(Decimal(str(bf['length']))/bv)}
 results.append(r)
(P/'results.json').write_text(json.dumps(results,indent=2,allow_nan=True))
lines=['| Case | E (MeV) | g | actual k / 30 | initial v | correct v (cm/shake) | first time actual / reference (shake) |','|---|---:|---:|---:|---:|---:|---:|']
for r in results:
 lines.append('| {name} | {E_MeV} | {mapped_group} | {observed_index} | {initial_v:.12g} | {vr:.12g} | {first_time_actual_shake:.12g} / {tr:.12g} |'.format(**r,vr=float(r['v_ref']),tr=float(r['first_time_ref_shake'])))
(P/'results-table.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines));print('All 13 GDB observers completed without errors; mapped groups and postcollision speeds checked independently.')

from pathlib import Path
from decimal import Decimal,getcontext
import json,hashlib,bisect
P=Path('/tmp/w14-codex-review');D=Path('/home/silver/NucXS_Library/RMC_DATA');getcontext().prec=50
lines=(D/'multigroup/mgxsnp').read_text().splitlines()
records={}
for nuc,first in [('1001.50m',0),('8016.50m',11884)]:
 assert lines[first].split()[0]==nuc
 nxs=[int(x) for l in lines[first+6:first+8] for x in l.split()]
 jxs=[int(x) for l in lines[first+8:first+12] for x in l.split()]
 n,G=nxs[0],nxs[4];x=[Decimal(x) for l in lines[first+12:first+12+(n+3)//4] for x in l.split()][:n]
 start=jxs[0]-1;cs=list(reversed(x[start:start+G]));ws=list(reversed(x[start+G:start+2*G]));lo=[c-w/2 for c,w in zip(cs,ws)];hi=[c+w/2 for c,w in zip(cs,ws)]
 records[nuc]={'G':G,'centers':[str(c) for c in cs],'lower':[str(v) for v in lo],'upper':[str(v) for v in hi]}
assert records['1001.50m']==records['8016.50m']
r=records['1001.50m'];cs=[Decimal(v) for v in r['centers']];lo=[Decimal(v) for v in r['lower']]
selected={'thermal_center':cs[0],'middle_center':cs[14],'inbounds_wrong':cs[17],'high_center':cs[-1],'lower_inside':lo[0]+Decimal('1e-16'),'upper_boundary':Decimal(r['upper'][-1])}
base=Path('/tmp/f11-stage2-independent-final-20261014-zk5zeaqk/ordinary/after/inp').read_text();ww=base[base.index('WEIGHTWINDOW'):];base=base[:base.index('WEIGHTWINDOW')].replace('POPULATION=500','POPULATION=101')
cases=[]
for label,E in selected.items():
 i=max(0,min(G-1,bisect.bisect_right(lo,E)-1));C=cs[i];c=Decimal('299.792458');m=Decimal('939.56542052');v=c*(C*(C+2*m)).sqrt()/(C+m)
 for role in ['F','A']:
  name=role+'-'+label;text=base.replace('ENERGY=2 WEIGHT=1','ENERGY='+str(E)+' WEIGHT=1')
  if role=='A':text=text.replace('RNG TYPE','ADJOINT ADJOINTCALCULATION=1 MaxAdjointEnergy=30 30\nRNG TYPE')
  d=P/'inputs'/name;d.mkdir(exist_ok=True);(d/'inp').write_text(text)
  cases.append({'name':name,'role':role,'physical_E':str(E),'correct_group':G-i,'correct_index':i,'correct_center':str(C),'v_ref':str(v),'predicted_wrong_index':G-int(E+Decimal('0.5')),'histories':101})
# one bounded WW descendant check, same validated native WW block
name='F-WW-descendants';d=P/'inputs'/name;d.mkdir(exist_ok=True);(d/'inp').write_text(base+ww)
cases.append({'name':name,'role':'F','physical_E':'2','histories':101,'purpose':'secondary bank velocity; no claim of full WW regression'})
(P/'cases.json').write_text(json.dumps(cases,indent=2));(P/'logs/mgace-groups.json').write_text(json.dumps(records,indent=2))
(P/'logs/database-identity.json').write_text(json.dumps({str(p):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size} for p in [D/'xsdir',D/'multigroup/mgxsnp']},indent=2))
print(json.dumps(cases,indent=2))

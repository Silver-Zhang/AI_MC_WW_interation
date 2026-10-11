from pathlib import Path
import json
T=Path(__file__).resolve().parents[1];D=T/'inputs/lifecycle';D.mkdir(exist_ok=True)
base=(T/'inputs/mg-neutron-analog.inp').read_text().replace('POPULATION=5000','POPULATION=1000')
ww=(T/'inputs/mg-neutron-native-ww.inp').read_text().split('\nWEIGHTWINDOW\n')[1]
(D/'model.inp').write_text(base)
(D/'model-ww.inp').write_text(base+'\nWEIGHTWINDOW\n'+ww)
def stats_input(text):
 return text.replace('TALLY\n','TALLY\nSCHECK 1\nCELLTALLY 3 TYPE=1 PARTICLE=1 CELL=1 CHECK=1\n',1).replace('CELL=1 ENERGY=-1','CELL=1 ENERGY=-1 CHECK=0')
(D/'model-stats.inp').write_text(stats_input(base))
plans={'pilot':[('F',100,.5,1,0),('A',100,19.5,-1,0),('F',100,.5,1,0)],
'ff':[('F',1000,.5,1,0),('F',2000,1.5,1,0)],
'faf':[('F',1000,.5,1,0),('A',1500,19.5,-1,0),('F',2000,.5,1,0)],
'aa':[('A',1000,19.5,-1,0),('A',1500,19.5,-1,0)],
'ww':[('F',1000,.5,1,w) for w in [0,1,2,0]],
'faf-ww':[('F',500,.5,1,1),('A',500,19.5,-1,2),('F',500,.5,1,1)],
'reuse':[(('F',100,.5,1,0) if i%2==0 else ('A',100,19.5,-1,0)) for i in range(20)]}
manifest={}
for name,rows in plans.items():
 (D/(name+'.tsv')).write_text(''.join(f'{i+1}\t{r}\t{n}\t{x}\t{d}\t{w}\n' for i,(r,n,x,d,w) in enumerate(rows)))
 offset=0;manifest[name]=[]
 for i,(role,n,x,d,w) in enumerate(rows):
  text=base.replace('POPULATION=1000',f'POPULATION={max(101,n)}').replace('POINT=0.5 0 0 VECTOR=1 0 0',f'POINT={x} 0 0 VECTOR={d} 0 0')
  if role=='A':text=text.replace('FIXEDSOURCE\n','FIXEDSOURCE\nADJOINT ADJOINTCALCULATION=1 MaxAdjointEnergy=30 20\n')
  if name=='ff':text=stats_input(text)
  if w:text+='\nWEIGHTWINDOW\n'+(ww if w==1 else ww.replace('0.1 1.0 0.1 1.0','0.05 0.5 0.05 0.5'))
  path=D/f'{name}-fresh-{i+1}.inp';path.write_text(text)
  manifest[name].append({'id':i+1,'role':role,'N':n,'offset':offset,'seed':17*pow(3512401965023503517,offset*100000,1<<63)%(1<<63),'input':str(path.resolve()),'ww':w})
  offset+=n
(T/'logs/lifecycle-plans.json').write_text(json.dumps(manifest,indent=2))

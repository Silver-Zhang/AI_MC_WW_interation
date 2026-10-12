from pathlib import Path
P=Path('/home/workspace/AI_MC_WW_interation/MLVR_develop/2026-10/20261011_05_f11-prepared-run-lifecycle/logs/p1-correction')
from pathlib import Path
import json,subprocess,shutil,concurrent.futures,sys
T=P;R=Path('/tmp/20261012-f11-stage2-p1');D=P/'inputs/negative';D.mkdir(exist_ok=True)
base=(P/'inputs/lifecycle/model.inp').read_text();ww=(P/'inputs/lifecycle/model-ww.inp').read_text();src=next(s for s in base.splitlines() if s.startswith('SOURCE'))
inputs={
'weight2':base.replace('WEIGHT=1','WEIGHT=2'),
'unbiased-distribution':base.replace('ENERGY=2','ENERGY=D1').replace('\n\nTALLY','\nDISTRIBUTION 1 TYPE=1 VALUE=1 2 PROBABILITY=1 1\n\nTALLY'),
'biased-distribution':base.replace('ENERGY=2','ENERGY=D1').replace('\n\nTALLY','\nDISTRIBUTION 1 TYPE=1 VALUE=1 2 PROBABILITY=1 3 BIAS=3 1\n\nTALLY'),
'dependent-distribution':base.replace('ENERGY=2','ENERGY=D2').replace('DIRECMIU=1','DIRECMIU=D1').replace('\n\nTALLY','\nDISTRIBUTION 1 TYPE=1 VALUE=0.5 1 PROBABILITY=1 1\nDISTRIBUTION 2 DEPEND=1 TYPE=0 VALUE=3 4\nDISTRIBUTION 3 TYPE=1 VALUE=1 PROBABILITY=1\nDISTRIBUTION 4 TYPE=1 VALUE=2 PROBABILITY=1\n\nTALLY'),
'multisource-equal':base.replace(src,src+'\n'+src.replace('SOURCE 1','SOURCE 2')),
'multisource-bias':base.replace(src,src.replace('FRACTION=1','FRACTION=1 BIASFRAC=3')+'\n'+src.replace('SOURCE 1','SOURCE 2').replace('FRACTION=1','FRACTION=3 BIASFRAC=1')),
'cell-source':base.replace('POINT=0.5 0 0','POINT=0.5 0 0 CELL=1'),
'nonpoint':base.replace('POINT=0.5 0 0','POSITION=0.5 0 0 RADIUS=0.1 AXIS=1 0 0 EXTENT=0.1'),
'transform':base.replace('WEIGHT=1','WEIGHT=1 TRANSFORM=1').replace('\n\nTALLY','\nTRANSFORM 1 MOVE=0 0 0\n\nTALLY'),
'fraction2':base.replace('FRACTION=1','FRACTION=2'),
'nonType2':base.replace('RNG TYPE=2','RNG TYPE=1'),
'ce':base.replace('1001.50m','1001.00c').replace('8016.50m','8016.00c').replace('MGACE ERGGRP=30 12','CEACE TMS=0 OTFPTB=0 PTABLE=0').replace('ENERGY=-1','ENERGY=0 20'),
'photon':base.replace('FIXEDSOURCE','PHYSICS\nPARTICLEMODE P\n\nFIXEDSOURCE'),
'time-reduce':base.replace('RNG TYPE=2','LOAD_BALANCE METHOD=1 INTERVAL=1\nRNG TYPE=2'),
'fission':base.replace('1001.50m 2.0\n  8016.50m 1.0','92235.50m 1.0'),
'scheck-energy':base.replace('TALLY\n','TALLY\nSCHECK 1\n',1),
}
for name,text in inputs.items():(D/(name+'.inp')).write_text(text)
(D/'plan.tsv').write_text('1 F 100 .5 1 0\n2 F 100 1.5 1 0\n')
cases=[]
def add(name,text,extra,after=False,stage='preflight',reason='prepared:'):
 cases.append(dict(name=name+('-after' if after else ''),text=text,extra=extra+(['--negative-after','yes'] if after else []),expected_receipts=int(after),stage=stage,reason=reason))
for n in ['uninitialized','double-initialize','after-finish','reinitialize-after-finish','role','zero-N','negative-N','ww-role','ww-shape','ww-negative','ww-nan','weight-binding','empty-source','weight2','wrong-owner','neutron-type']:
 for after in ([False] if n=='uninitialized' else [False,True]):add(n,ww,['--negative',n],after,stage='state' if n in ['uninitialized','double-initialize','after-finish','reinitialize-after-finish'] else 'preflight')
add('run-id',ww,['--negative','run-id'],True)
add('no-WW-topology',base,['--negative','ww-shape'],reason='no fixed Cartesian WW topology')
for n in ['weight2','unbiased-distribution','biased-distribution','dependent-distribution','multisource-equal','multisource-bias','cell-source','nonpoint','transform','fraction2']:
 for after in [False,True]:add('input-'+n,inputs[n],['--preserve-source','yes'],after,reason='unsupported source definition')
for n in ['nonType2','ce','photon','time-reduce','fission','scheck-energy']:add('profile-'+n,inputs[n],[],stage='initialize')
for n,extra in [('seed0',['--root-seed','0']),('even-seed',['--root-seed','2']),('large-seed',['--root-seed',str(1<<63)]),('zero-stride',['--stride','0']),('overflow',['--offset',str((1<<64)-1)]),('period',['--offset',str((1<<61)//100000)])]:add(n,base,extra,stage='initialize')
add('stride-runtime',base,['--stride','1','--check-failed','yes'],stage='execution',reason='stride')
(T/'logs/negative-plan.json').write_text(json.dumps([{k:v for k,v in x.items() if k!='text'} for x in cases],indent=2))
label=sys.argv[1] if len(sys.argv)>1 else 'negative-01'
def run(c):
 work=R/label/c['name'];work.mkdir(parents=True,exist_ok=False);(work/'inp').write_text(c['text']);dest=P/'logs'/label/c['name'];dest.mkdir(parents=True,exist_ok=False)
 cmd=[str(R/'stage2-build/bin/RMCPreparedLifecycle'),'--mode','persistent','--input','inp','--data','/home/silver/NucXS_Library/RMC_DATA','--snapshot-dir',str(dest),'--plan',str(D/'plan.tsv'),*c['extra']]
 code=subprocess.call(['python3',str(T/'tools/run_command.py'),'--log',str(dest/'command'),'--cwd',str(work),'--timeout','120','--',*cmd],stdout=subprocess.DEVNULL)
 for p in work.glob('inp*'):
  if p.is_file():shutil.copyfile(p,dest/p.name)
 stdout=(dest/'command/stdout.txt').read_text();stderr=(dest/'command/stderr.txt').read_text();receipts=len(list(dest.glob('receipt-*.json')))
 passed=code==2 and 'PREPARED_FAILURE' in stderr and c['reason'] in stderr and receipts==c['expected_receipts']
 if c['stage']=='preflight':passed=passed and 'state_unchanged=1' in stdout
 if c['stage']=='execution':passed=passed and 'FAILED_TERMINAL retry_rejected=1 finish_rejected=1' in stdout
 return {k:v for k,v in c.items() if k not in ['text','extra']}|{'exit':code,'receipts':receipts,'passed':passed,'failure':stderr.strip(),'state':[l for l in stdout.splitlines() if l.startswith(('REJECTED','FAILED_TERMINAL'))]}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:result=list(pool.map(run,cases))
(P/'logs'/label/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({'passed':sum(x['passed'] for x in result),'total':len(result),'failed':[x for x in result if not x['passed']]},indent=2));sys.exit(not all(x['passed'] for x in result))

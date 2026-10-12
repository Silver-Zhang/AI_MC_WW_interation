"""Three independent production entry points; exact counts/state, not exit-only."""
from pathlib import Path
import argparse,concurrent.futures,json,os,subprocess,shutil
ap=argparse.ArgumentParser();ap.add_argument('--root',default='/tmp/20261012_02_f11-ww-energy-bin-safety');ap.add_argument('--label',default='energy-negatives');a=ap.parse_args()
R=Path(a.root);L=R/'evidence';T=Path(__file__).resolve().parents[1];D=L/'inputs/lifecycle';exe=R/'stage2-build/bin/RMCPreparedLifecycle'
reasons={
 **dict.fromkeys(['outer-empty','outer-one'],'energy-bin neutron outer entry missing'),
 **dict.fromkeys(['inner-empty','inner-one'],'energy-bin boundary count invalid'),
 **dict.fromkeys(['duplicate','descending'],'energy-bin boundaries must strictly increase'),
 **dict.fromkeys(['nan-interior','nan-terminal','inf-interior','inf-terminal','negative-inf'],'energy-bin boundary must be finite'),
 **dict.fromkeys(['missing-sentinel','negative-first'],'energy-bin endpoints must be 0 and INFINITY_ENERGY'),
 **dict.fromkeys(['energy-dimension','mesh-ragged'],'installed energy-bin shape mismatch'),
 **dict.fromkeys(['mesh-outer-empty','mesh-outer-one','mesh-outer-two','mesh-inner-empty'],'installed neutron mesh shape mismatch'),
 **dict.fromkeys(['parameters-outer-empty','parameters-outer-one','parameters-inner-empty','parameters-inner-short'],'WW parameters missing'),
 'other-particle':'WW prepared topology must contain neutron windows only',
 'non-cartesian':'no fixed Cartesian WW topology','count-overflow':'mesh/energy count exceeds int range'}
plan=L/'inputs/energy-negative.tsv';plan.write_text('1 F 100 .5 1 1\n2 F 100 .5 1 1\n')
def run(test):
 phase,kind=test;name=phase+'-'+kind;dest=L/'logs'/a.label/name;dest.mkdir(parents=True);work=R/a.label/name;work.mkdir(parents=True,exist_ok=False);shutil.copyfile(D/'model-ww.inp',work/'inp')
 cmd=[str(exe),'--mode','ww-energy-install' if phase=='install' else 'persistent','--input','inp','--data','/home/silver/NucXS_Library/RMC_DATA','--snapshot-dir',str(dest),'--plan',str(plan),'--ww-mutation',kind]
 if phase=='bind':cmd+=['--energy-before-bind','yes']
 if phase=='after':cmd+=['--negative','ww-energy','--negative-after','yes']
 env=os.environ.copy();env['ENERGY_GUARD_COUNTS']=str(dest/'counts.json')
 args=['gdb','-q','-batch','-x',str(T/'tools/energy-guards.gdb'),'--args',*cmd]
 code=subprocess.call(['python3',str(L/'tools/run_command.py'),'--log',str(dest/'command'),'--cwd',str(work),'--timeout','180','--',*args],env=env,stdout=subprocess.DEVNULL)
 stdout=(dest/'command/stdout.txt').read_text();stderr=(dest/'command/stderr.txt').read_text();obs=json.loads((dest/'counts.json').read_text()) if (dest/'counts.json').exists() else {};n=int(phase=='after')
 expected={'initialize':n,'prepare':n,'clear':n,'execute':n,'source':100*n,'validate':4 if n else 1,'install':int(phase!='bind')}
 production_throw=any(any(x and 'CDWeightWindow::ValidatePreparedNativeDefinition' in x for x in stack) for stack in obs.get('throws',[]))
 rcpts=len(list(dest.glob('receipt-*.json')))
 passed=(code==0 and obs.get('inferior_exit')==2 and obs.get('counts')==expected and production_throw and reasons[kind] in stderr and 'state_unchanged=1' in stdout and rcpts==n and 'definition changed' not in stderr)
 return {'name':name,'phase':phase,'mutation':kind,'expected_reason':reasons[kind],'passed':passed,'gdb_exit':code,'observation':obs,'expected_counts':expected,'receipt_count':rcpts,'production_throw':production_throw,'stderr':stderr,'evidence':str(dest),'state_and_actual_input':[s for s in stdout.splitlines() if s.startswith(('REJECTED','WW_DEFINITION_MUTATION'))]}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,[(phase,k) for phase in ['bind','after','install'] for k in reasons]))
result={'passed':all(r['passed'] for r in rows),'total':len(rows),'passed_count':sum(r['passed'] for r in rows),'physical_tolerance':0,'tests':rows}
(L/'logs'/a.label/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({'passed':result['passed_count'],'total':len(rows),'failed':[r for r in rows if not r['passed']]},indent=2));raise SystemExit(not result['passed'])

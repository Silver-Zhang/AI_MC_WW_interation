"""Instrument only the two repaired production TUs and their public-API driver.
Other production objects are the normal build; this is not whole-RMC coverage.
"""
from pathlib import Path
import argparse,concurrent.futures,json,os,shlex,subprocess,shutil
p=argparse.ArgumentParser();p.add_argument('action',choices=['compile','run']);p.add_argument('--root',default='/tmp/20261012_02_f11-ww-energy-bin-safety');a=p.parse_args()
R=Path(a.root);L=R/'evidence';B=R/'stage2-build';S=R/'sanitizer';S.mkdir(exist_ok=True)
flags=['-O1','-fno-omit-frame-pointer','-fsanitize=address,undefined','-D_GLIBCXX_ASSERTIONS']
rows=[r for r in json.loads((B/'compile_commands.json').read_text()) if 'RMCPreparedLifecycle.dir' in r['output'] and Path(r['file']).name in ['PrepareFixedSourceRun.cpp','WeightWindows.cpp','driver.cpp']]
assert len(rows)==3
objects={r['output'].removeprefix('tests/prepared_fixed_source_lifecycle/'):str(S/(Path(r['file']).name+'.o')) for r in rows}
def command(name,cmd,cwd,env=None):
 return subprocess.call(['python3',str(L/'tools/run_command.py'),'--log',str(L/'logs/sanitizer'/name),'--cwd',str(cwd),'--timeout','1200','--',*cmd],env=env,stdout=subprocess.DEVNULL)
if a.action=='compile':
 def compile(r):
  cmd=shlex.split(r['command']);cmd[cmd.index('-o')+1]=str(S/(Path(r['file']).name+'.o'));cmd+=flags
  return command('compile-'+Path(r['file']).name,cmd,r['directory'])
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:codes=list(pool.map(compile,rows))
 print(codes);raise SystemExit(any(codes))
wd=B/'tests/prepared_fixed_source_lifecycle';cmd=shlex.split((wd/'CMakeFiles/RMCPreparedLifecycle.dir/link.txt').read_text());cmd=[objects.get(x,x) for x in cmd if not x.startswith('-Wl,-Map=')];exe=S/'RMCPreparedLifecycle';cmd[cmd.index('-o')+1]=str(exe);cmd+=['-fsanitize=address,undefined','-no-pie']
assert command('link',cmd,wd)==0
negative=json.loads((L/'logs/energy-negatives/results.json').read_text())['tests'];cases=[]
for test in negative:
 old=json.loads((Path(test['evidence'])/'command/command.json').read_text());full=old['argv'];i=full.index('--args');args=full[i+1:];args[0]=str(exe);name=test['name'];work=S/name;work.mkdir(exist_ok=False);shutil.copyfile(Path(old['cwd'])/'inp',work/'inp');dest=L/'logs/sanitizer'/name;dest.mkdir(parents=True);args[args.index('--snapshot-dir')+1]=str(dest)
 cases.append((name,args,work,test['expected_reason'],2,1 if test['phase']=='after' else 0))
cases.append(('lookup',[str(exe),'--mode','ww-energy-lookup-selftest'],S,'WW_LOOKUP_SELFTEST 15/15',0,0))
# Valid multi-energy install/transport/CLEAR cycle under the targeted instrumentation.
dest=L/'logs/sanitizer/multi';dest.mkdir(parents=True);work=S/'multi';work.mkdir();shutil.copyfile(L/'inputs/lifecycle/model-multi.inp',work/'inp')
cases.append(('multi',[str(exe),'--mode','persistent','--input','inp','--data','/home/silver/NucXS_Library/RMC_DATA','--snapshot-dir',str(dest),'--plan',str(L/'inputs/lifecycle/multi.tsv'),'--multi-energy','yes'],work,'PREPARED_RUN_SUCCESS 4',0,4))
env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=0:abort_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1'
def run(c):
 name,args,work,reason,wanted,n=c;code=command(name+'/command',args,work,env);dest=L/'logs/sanitizer'/name;stdout=(dest/'command/stdout.txt').read_text();stderr=(dest/'command/stderr.txt').read_text()
 bad=any(x in stderr for x in ['AddressSanitizer','runtime error:','Assertion','DEADLYSIGNAL']);receipts=len(list(dest.glob('receipt-*.json')))
 return {'name':name,'exit':code,'expected_exit':wanted,'expected_reason':reason,'receipts':receipts,'passed':code==wanted and reason in stdout+stderr and not bad and receipts==n,'evidence':str(dest)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,cases))
out={'passed':all(r['passed'] for r in results),'instrumented_translation_units':[r['file'] for r in rows],'flags':flags,'ASAN_OPTIONS':env['ASAN_OPTIONS'],'UBSAN_OPTIONS':env['UBSAN_OPTIONS'],'coverage':'targeted only; remaining production code and libraries uninstrumented; no leak claim','cases':results}
(L/'logs/sanitizer/results.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));raise SystemExit(not out['passed'])

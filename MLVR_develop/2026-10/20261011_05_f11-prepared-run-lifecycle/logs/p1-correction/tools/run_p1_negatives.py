from pathlib import Path
import concurrent.futures,json,subprocess,os,sys,shutil
P=Path(__file__).resolve().parents[1];R=Path('/tmp/20261012-f11-stage2-p1');D=P/'inputs/lifecycle'
label=sys.argv[1];cases=[]
def add(name,model,extra,after,reason):cases.append(dict(name=name,model=model,extra=extra,after=after,reason=reason))
for param,vals in [('upper',['0','-1','nan','inf','1','2']),('survival',['0','-1','nan','inf','1','5','6']),('split',['0','-1','nan','inf','1','1.5','2147483648'])]:
 for value in vals:
  for after in [False,True]:
   extra=['--ww-'+param,value]+(['--negative','ww-parameters','--negative-after','yes'] if after else ['--ww-before-bind','yes'])
   add(param+'-'+value+('-after' if after else '-bind'),'model-ww.inp',extra,after,{'upper':'WW WUPN','survival':'WW WSURVN','split':'WW MXSPLN'}[param])
for after in [False,True]:
 add('combination'+('-after' if after else '-bind'),'model-ww.inp',['--ww-upper','3','--ww-survival','4']+(['--negative','ww-parameters','--negative-after','yes'] if after else ['--ww-before-bind','yes']),after,'WW WSURVN')
for name,extra,reason in [
 ('derived-overflow',['--ww-lower','1e308'],'invalid WW lower/upper/survival'),
 ('derived-rounding',['--ww-lower','denorm','--ww-survival','1.0000000000000002','--ww-before-bind','yes'],'invalid WW lower/upper/survival'),
 ('split-product-overflow',['--ww-lower','1e300','--ww-split','1000000000','--ww-before-bind','yes'],'invalid WW lower/upper/survival'),
 ('split-ratio-overflow',['--ww-lower','1e-100'],'splitting ratio exceeds int range')]:
 add(name,'model-ww.inp',extra+['--negative','ww-lower-value','--negative-after','yes'],True,reason)
for kind in ['origin','rotation','membership','fill','random']:
 add('universe-'+kind,'model-universe.inp',['--negative','universe-'+kind,'--negative-after','yes'],True,'unsupported Universe' if kind=='random' else 'model/tally/WW definition changed')
plan=P/'inputs/p1-negative.tsv';plan.write_text('1 F 100 .5 1 0\n2 F 100 .5 1 1\n')
# Universe has no WW topology; keep requested WW disabled.
uplan=P/'inputs/p1-universe-negative.tsv';uplan.write_text('1 F 100 .5 1 0\n2 F 100 .5 1 0\n')
(P/'negative-plan.json').write_text(json.dumps(cases,indent=2))
def run(c):
 dest=P/'logs'/label/c['name'];dest.mkdir(parents=True,exist_ok=False);work=R/label/c['name'];work.mkdir(parents=True,exist_ok=False);shutil.copyfile(D/c['model'],work/'inp')
 cmd=[str(R/'stage2-build/bin/RMCPreparedLifecycle'),'--mode','persistent','--input','inp','--data','/home/silver/NucXS_Library/RMC_DATA','--snapshot-dir',str(dest),'--plan',str(uplan if c['name'].startswith('universe-') else plan),*c['extra']]
 env=os.environ.copy();env['P1_GUARD_COUNTS']=str(dest/'counts.json')
 command=['gdb','-q','-batch','-x',str(P/'tools/guard-counts.gdb'),'--args',*cmd]
 code=subprocess.call(['python3',str(P/'tools/run_command.py'),'--log',str(dest/'command'),'--cwd',str(work),'--timeout','120','--',*command],env=env,stdout=subprocess.DEVNULL)
 stdout=(dest/'command/stdout.txt').read_text();stderr=(dest/'command/stderr.txt').read_text();obs=json.loads((dest/'counts.json').read_text()) if (dest/'counts.json').exists() else {};n=int(c['after'])
 expected={'initialize':n,'prepare':n,'clear':n,'execute':n,'source':100*n}
 passed=code==0 and obs.get('inferior_exit')==2 and obs.get('counts')==expected and c['reason'] in stderr and 'state_unchanged=1' in stdout and len(list(dest.glob('receipt-*.json')))==n
 return c|{'passed':passed,'gdb_exit':code,'observation':obs,'expected':expected,'stderr':stderr,'rejection':[s for s in stdout.splitlines() if s.startswith(('REJECTED','UNIVERSE_MUTATION'))]}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,cases))
(P/'logs'/label/'results.json').write_text(json.dumps(rows,indent=2));print(json.dumps({'passed':sum(r['passed'] for r in rows),'total':len(rows),'failed':[r for r in rows if not r['passed']]},indent=2));sys.exit(not all(r['passed'] for r in rows))

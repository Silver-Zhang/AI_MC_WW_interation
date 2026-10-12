from pathlib import Path
import argparse,concurrent.futures,importlib.util,json,os,shutil,subprocess,struct,gzip,hashlib,re
p=argparse.ArgumentParser();p.add_argument('--root',default='/tmp/20261012_02_f11-ww-energy-bin-safety');p.add_argument('--action',choices=['setup','ordinary','ordinary-compare','multi'],required=True);a=p.parse_args()
R=Path(a.root);L=R/'evidence';D=L/'inputs/lifecycle'
if a.action=='setup':
 text=(D/'model-ww.inp').read_text().replace('POPULATION=1000','POPULATION=500').replace('WWMESH:N 0.1 1.0 0.1 1.0','WWE:N 0.1 1.0\nWWMESH:N 0.1 0.15 0.2 1.0 1.5 2.0 0.1 0.15 0.2 1.0 1.5 2.0')
 (D/'model-multi.inp').write_text(text);(D/'multi.tsv').write_text('1 F 500 .5 1 0\n2 F 500 .5 1 1\n3 F 500 .5 1 2\n4 F 500 .5 1 0\n')
 plans=json.loads((L/'logs/lifecycle-plans.json').read_text());rows=[]
 for i,w in enumerate([0,1,2,0]):
  offset=i*500;seed=17*pow(3512401965023503517,offset*100000,2**63)%(2**63)
  inp=text
  if not w:inp=inp.split('\nWEIGHTWINDOW')[0]+'\n'
  if w==2:inp=inp.replace('WWMESH:N 0.1 0.15 0.2 1.0 1.5 2.0 0.1 0.15 0.2 1.0 1.5 2.0','WWMESH:N 0.05 0.075 0.1 0.5 0.75 1.0 0.05 0.075 0.1 0.5 0.75 1.0')
  dest=D/f'multi-fresh-{i+1}.inp';dest.write_text(inp)
  rows.append({'id':i+1,'role':'F','N':500,'offset':offset,'seed':seed,'ww':w,'input':str(dest),'multi_energy':True})
 plans['multi']=rows;(L/'logs/lifecycle-plans.json').write_text(json.dumps(plans,indent=2))
 f=L/'tools/run_lifecycle.py';s=f.read_text().replace("else 'model-ww.inp' if", "else 'model-multi.inp' if a.sequence=='multi' else 'model-ww.inp' if").replace("'--legacy-output','yes']", "'--legacy-output','yes','--multi-energy','yes' if a.sequence=='multi' else 'no']");f.write_text(s)
 f=L/'tools/compare_lifecycle.py';s=f.read_text();old="w=expected['ww'];lower=([.1,1.,.1,1.] if w==1 else [.05,.5,.05,.5])[event['mesh']]";new=old+"\n     if expected.get('multi_energy'):\n      energy=struct.unpack('<d',bytes.fromhex(event['erg']))[0]\n      interval=0 if energy<.1 else 1 if energy<1. else 2\n      lower=[.1,.15,.2,1.,1.5,2.,.1,.15,.2,1.,1.5,2.][event['mesh']*3+interval]*(1 if w==1 else .5)";assert old in s;s=s.replace(old,new);f.write_text(s)
 raise SystemExit(0)

def command(dest,cmd,work=None,env=None):
 return subprocess.call(['python3',str(L/'tools/run_command.py'),'--log',str(dest),'--timeout','1200',*(['--cwd',str(work)] if work else []),'--',*cmd],env=env)
if a.action=='multi':
 for fresh in [False,True]:
  assert command(L/'logs'/('multi-'+str(fresh)+'-command'),['python3',str(L/'tools/run_lifecycle.py'),'multi','--label','multi-energy','--trace',*(['--fresh'] if fresh else [])])==0
 raise SystemExit(command(L/'logs/multi-compare-command',['python3',str(L/'tools/compare_lifecycle.py'),'multi','--label','multi-energy']))

def run(test):
 case,which=test;work=R/'ordinary-ww'/case/which;work.mkdir(parents=True,exist_ok=False)
 inp=(D/('model-multi.inp' if case=='multi' else 'model-ww.inp')).read_text().replace('POPULATION=1000','POPULATION=500');(work/'inp').write_text(inp)
 dest=L/'logs/ordinary-ww'/case/which;dest.mkdir(parents=True)
 exe=Path('/tmp/20261012-f11-stage2-p1/stage2-build/bin/RMC') if which=='before' else R/'stage2-build/bin/RMC'
 env=os.environ.copy();env['F11_TRACE_DIR']=str(dest);env['OMP_NUM_THREADS']='1'
 code=command(dest/'command',['gdb','-q','-batch','-x',str(L/'tools/trace_lifecycle.gdb'),'--args',str(exe),'-i','inp','-d','/home/silver/NucXS_Library/RMC_DATA'],work,env)
 assert code==0 and not json.loads((dest/'observer.json').read_text())['errors']
 return case,which
if a.action=='ordinary':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(run,[(c,w) for c in ['single','multi'] for w in ['before','after']]))
spec=importlib.util.spec_from_file_location('comparison',L/'tools/compare_lifecycle.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
# Load the predeclared ordinary text canonicalizer without executing its test runner.
source=(L/'tools/compare.py').read_text();space={'re':re};exec(source[source.index('def canonical_text'):source.index('def hdf')],space)
results=[]
for case in ['single','multi']:
 old=L/'logs/ordinary-ww'/case/'before';new=old.parent/'after';C.errors.clear();C.allowed.clear()
 for artifact in ['clear','before-finalize','final','legacy','derived','raw','start','end','trace-summary']:
  C.compare(C.load(old/f'1-{artifact}.json'),C.load(new/f'1-{artifact}.json'),artifact)
 energies=set();bounds_count=0
 for directory in [old,new]:
  h=hashlib.sha256()
  with gzip.open(directory/'1-trace.jsonl.gz','rb') as f:
   for line in f:
    h.update(line);kind,event=json.loads(line)
    if kind=='WW_QUERY':
     energy=struct.unpack('<d',bytes.fromhex(event['erg']))[0];k=0 if energy<.1 else 1 if energy<1 else 2
     lo=([.1,.15,.2,1.,1.5,2.,.1,.15,.2,1.,1.5,2.][event['mesh']*3+k] if case=='multi' else [.1,1.,.1,1.][event['mesh']])
     for name,value in [('lower',lo),('survive',lo*3),('upper',lo*5)]:
      if event[name]!=struct.pack('<d',value).hex():C.errors.append('independent-bound/'+name)
     energies.add(k if case=='multi' else 0);bounds_count+=1
  if h.hexdigest()!=C.load(directory/'1-trace-summary.json')['sha256']:C.errors.append('trace-integrity')
 counts=C.load(new/'1-trace-summary.json')['counts']
 if not all(counts.get(k,0)>0 for k in ['SPLIT','ROULETTE','BANK']):C.errors.append('WW-action-coverage')
 if case=='multi' and energies!={0,1,2}:C.errors.append('energy-interval-coverage')
 w0=R/'ordinary-ww'/case/'before';w1=w0.parent/'after';outputs={}
 for name in ['inp','inp.Tally','inp.material','inp.out']:
  x=(w0/name).read_text();y=(w1/name).read_text()
  if name=='inp.out':x=space['canonical_text'](x);y=space['canonical_text'](y)
  outputs[name]=x==y
  if x!=y:C.errors.append('output/'+name)
 for f in w0.glob('*.h5'):
  def dump(path):return re.sub(r'^HDF5 "[^"]*"','HDF5 "<path>"',subprocess.check_output(['h5dump','-m','%.17g','-y','-w','0',str(path)],text=True))
  outputs[f.name]=dump(f)==dump(w1/f.name)
  if not outputs[f.name]:C.errors.append('HDF/'+f.name)
 results.append({'case':case,'passed':not C.errors,'errors':list(C.errors),'time_exceptions':list(C.allowed),'physical_tolerance':0,'counts':counts,'energy_intervals_observed':sorted(energies),'independent_bounds_checked':bounds_count,'trace_sha256':C.load(new/'1-trace-summary.json')['sha256'],'output_checks':outputs,'before_binary':'/tmp/20261012-f11-stage2-p1/stage2-build/bin/RMC','after_binary':str(R/'stage2-build/bin/RMC')})
(L/'logs/ordinary-ww/results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2));raise SystemExit(not all(r['passed'] for r in results))

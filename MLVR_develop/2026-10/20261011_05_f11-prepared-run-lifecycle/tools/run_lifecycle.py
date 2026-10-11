from pathlib import Path
import argparse,concurrent.futures,subprocess,sys,os,json,shutil
T=Path(__file__).resolve().parents[1];R=Path('/tmp/20261011_05_f11-prepared-run-lifecycle');D=T/'inputs/lifecycle';DB='/home/silver/NucXS_Library/RMC_DATA'
p=argparse.ArgumentParser();p.add_argument('sequence');p.add_argument('--label',default='gates-01');p.add_argument('--trace',action='store_true');p.add_argument('--fresh',action='store_true');p.add_argument('--trace-exports',action='store_true');a=p.parse_args()
exe=R/'stage2-build/bin/RMCPreparedLifecycle'
def run(kind,case,inp,extra):
 work=R/a.label/a.sequence/case;work.mkdir(parents=True,exist_ok=False);shutil.copyfile(inp,work/'inp')
 dest=T/'logs'/a.label/a.sequence/case;dest.mkdir(parents=True,exist_ok=False)
 cmd=[str(exe),'--mode',kind,'--input','inp','--data',DB,'--snapshot-dir',str(dest),*extra]
 if a.trace or a.trace_exports:cmd=['gdb','-q','-batch','-x',str(T/'tools'/('trace_exports.gdb' if a.trace_exports else 'trace_lifecycle.gdb')),'--args',*cmd]
 env=os.environ.copy();env['F11_TRACE_DIR']=str(dest);env['OMP_NUM_THREADS']='1'
 code=subprocess.run([sys.executable,str(T/'tools/run_command.py'),'--log',str(dest/'command'),'--cwd',str(work),'--timeout','1200','--',*cmd],env=env).returncode
 if a.trace or a.trace_exports:
  observed=json.loads((dest/'observer.json').read_text());assert not observed['errors'],observed
 for file in work.glob('inp*'):
  if file.is_file():shutil.copyfile(file,dest/file.name)
 if kind=='persistent':assert list(dest.glob('receipt-*.json')),dest
 return case,code
if not a.fresh:
 model=D/('model-ww.inp' if a.sequence in ['ww','faf-ww'] else 'model-stats.inp' if a.sequence=='ff' else 'model.inp')
 result=[run('persistent','persistent',model,['--plan',str(D/(a.sequence+'.tsv')),'--gap','yes' if a.sequence=='ff' else 'no','--legacy-output','yes'])]
else:
 rows=json.loads((T/'logs/lifecycle-plans.json').read_text())[a.sequence]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  result=list(pool.map(lambda x:run('fresh','fresh-'+str(x['id']),Path(x['input']),['--effective-seed',str(x['seed']),'--stride','100000','--histories',str(x['N'])]),rows))
print(result);sys.exit(0 if all(c==0 for _,c in result) else 1)

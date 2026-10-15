from pathlib import Path
import subprocess,json,shutil,os,sys,concurrent.futures,time
P=Path('/tmp/w14-codex-review');cases=json.loads((P/'cases.json').read_text());mode=sys.argv[1] if len(sys.argv)>1 else 'gdb'
if len(sys.argv)>2:cases=[c for c in cases if c['name'] in sys.argv[2:]]
def run(c):
 d=P/'runs'/mode/c['name'];d.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/'inputs'/c['name']/'inp',d/'inp');env=os.environ.copy();binary=P/('sanitized/RMC' if mode.startswith('asan') else 'build/bin/RMC');args=[str(binary),'-i','inp','-d','/home/silver/NucXS_Library/RMC_DATA']
 if mode.startswith('gdb'):args=['gdb','--batch','--return-child-result','-nx','-q','-ex','set pagination off','-ex','set confirm off','-ex','set print elements 0','-x',str(P/'scripts/observe.py'),'--args']+args
 if mode.startswith('asan'):env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='print_stacktrace=1:halt_on_error=1')
 (d/'command.json').write_text(json.dumps({'argv':args,'cwd':str(d),'environment':{k:env[k] for k in ['ASAN_OPTIONS','UBSAN_OPTIONS'] if k in env}},indent=2));t=time.time()
 with (d/'stdout').open('w') as o,(d/'stderr').open('w') as e:
  try:r=subprocess.run(args,cwd=d,stdout=o,stderr=e,env=env,timeout=180);code=r.returncode
  except subprocess.TimeoutExpired:code=124
 (d/'exitcode').write_text(str(code));(d/'seconds').write_text(str(time.time()-t));print(c['name'],mode,code,flush=True)
with concurrent.futures.ThreadPoolExecutor(2) as ex:list(ex.map(run,cases))

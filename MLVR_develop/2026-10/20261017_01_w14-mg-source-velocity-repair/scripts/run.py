from pathlib import Path
import sys,subprocess,json,os,shutil,concurrent.futures,time
P=Path('/tmp/w14-repair-20261017');version,mode=sys.argv[1:3];names=sys.argv[3:]
binary=P/({'before':'build/bin/RMC','after':'build-after/bin/RMC','asan':'sanitized/RMC'}[version])
def run(name):
 d=P/'runs'/version/mode/name;d.mkdir(parents=True,exist_ok=False);shutil.copyfile(P/'inputs'/name/'inp',d/'inp');env=os.environ.copy();cmd=[str(binary),'-i','inp','-d','/home/silver/NucXS_Library/RMC_DATA']
 if mode.startswith('velocity') or mode.startswith('trace'):
  observer=P/'scripts'/('velocity.gdb.py' if mode.startswith('velocity') else 'trace_lifecycle.gdb')
  cmd=['gdb','--batch','--return-child-result','-nx','-q','-ex','set pagination off','-ex','set confirm off','-x',str(observer),'--args']+cmd;env['F11_TRACE_DIR']=str(d)
 if version=='asan':env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='print_stacktrace=1:halt_on_error=1')
 (d/'command.json').write_text(json.dumps({'argv':cmd,'cwd':str(d),'env':{k:v for k,v in env.items() if k in ['F11_TRACE_DIR','ASAN_OPTIONS','UBSAN_OPTIONS']}},indent=2));t=time.time()
 with (d/'stdout').open('w') as o,(d/'stderr').open('w') as e:
  try:r=subprocess.run(cmd,cwd=d,stdout=o,stderr=e,env=env,timeout=300);code=r.returncode
  except subprocess.TimeoutExpired:code=124
 (d/'exitcode').write_text(str(code));(d/'seconds').write_text(str(time.time()-t));print(version,mode,name,code,flush=True)
 return code
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:codes=list(pool.map(run,names))
sys.exit(any(codes))

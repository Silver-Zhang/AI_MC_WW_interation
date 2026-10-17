from pathlib import Path
import sys,os,json,subprocess,time,shutil,concurrent.futures,hashlib
P=Path('/tmp/w14-energy-audit-20261017');label,version,*names=sys.argv[1:];binary=Path('/tmp/w14-repair-20261017')/dict(current='build-after/bin/RMC',original='build/bin/RMC',asan='sanitized/RMC')[version]
def run(n):
 d=P/'runs'/label/n;d.mkdir(parents=True,exist_ok=False);shutil.copyfile(P/'inputs'/n/'inp',d/'inp');shutil.copyfile(P/'scripts/observe.py',d/'observer.py');env=os.environ.copy();env["W14_VERSION"]=version;cmd=[str(binary),'-i','inp','-d','/home/silver/NucXS_Library/RMC_DATA']
 if version!='asan':cmd=['gdb','--batch','--return-child-result','-nx','-q','-x',str(P/'scripts/observe.py'),'--args']+cmd
 else:env.update(ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='print_stacktrace=1:halt_on_error=1')
 (d/'command.json').write_text(json.dumps({'argv':cmd,'cwd':str(d),'env':{k:env[k] for k in ['ASAN_OPTIONS','UBSAN_OPTIONS','W14_VERSION'] if k in env},'observer_sha256':hashlib.sha256((P/'scripts/observe.py').read_bytes()).hexdigest()},indent=2));t=time.time()
 with (d/'stdout').open('w') as o,(d/'stderr').open('w') as e:
  try:code=subprocess.run(cmd,cwd=d,env=env,stdout=o,stderr=e,timeout=180).returncode
  except subprocess.TimeoutExpired:code=124
 (d/'exitcode').write_text(str(code));(d/'seconds').write_text(str(time.time()-t));print(label,n,code,round(time.time()-t,2),flush=True)
 return code
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:codes=list(pool.map(run,names))
sys.exit(any(codes))

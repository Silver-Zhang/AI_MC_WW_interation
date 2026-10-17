from pathlib import Path
import subprocess,shutil,json,time,hashlib
P=Path('/tmp/w14-repair-20261017');R=Path('/home/workspace/AI_MC_WW_interation/RMC')
S=P/'src-after';shutil.copytree(P/'src',S,ignore=shutil.ignore_patterns('dependencies'))
(S/'dependencies').symlink_to(P/'src/dependencies',target_is_directory=True)
files=subprocess.check_output(['git','-C',str(R),'diff','--name-only'],text=True).splitlines()
for f in files:shutil.copyfile(R/f,S/f)
(P/'logs/after-source-sha256.json').write_text(json.dumps({f:hashlib.sha256((S/f).read_bytes()).hexdigest() for f in files},indent=2))
args=json.loads((P/'logs/configure/command.json').read_text())['argv'];args=[x.replace(str(P/'src'),str(S)).replace(str(P/'build'),str(P/'build-after')) for x in args]
def run(name,cmd):
 d=P/'logs'/name;d.mkdir(exist_ok=True);(d/'command.json').write_text(json.dumps({'argv':cmd,'cwd':str(P)},indent=2));t=time.time()
 with (d/'stdout').open('w') as o,(d/'stderr').open('w') as e:r=subprocess.run(cmd,cwd=P,stdout=o,stderr=e)
 (d/'exitcode').write_text(str(r.returncode));(d/'seconds').write_text(str(time.time()-t));assert r.returncode==0,name
run('configure-after',args)
run('build-after',['cmake','--build',str(P/'build-after'),'--target','RMC','-j','12'])
print('after build complete',flush=True)

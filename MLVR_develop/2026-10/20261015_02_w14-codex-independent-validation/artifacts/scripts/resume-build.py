from pathlib import Path
import json,subprocess,time,hashlib
P=Path('/tmp/w14-codex-review')
def run(name,args):
 d=P/'logs'/name;d.mkdir(exist_ok=True);(d/'command.json').write_text(json.dumps({'argv':args,'cwd':str(P)},indent=2));t=time.time()
 with (d/'stdout').open('w') as o,(d/'stderr').open('w') as e:r=subprocess.run(args,cwd=P,stdout=o,stderr=e)
 (d/'exitcode').write_text(str(r.returncode));(d/'seconds').write_text(str(time.time()-t));assert r.returncode==0,name
args=json.loads((P/'logs/configure/command.json').read_text())['argv'];args=[a.replace('-Dloadmodules=OFF','-Dloadmodules=ON') for a in args]
args+=['-DGIT_EXECUTABLE='+str(P/'scripts/git-readonly'),'-DHIGHFIVE_PARALLEL_HDF5=OFF','-DGIT_SHA=4810694b7a99dfc3ad7d27f7d443814f511f4829']
run('configure-retry',args)
run('build',['cmake','--build',str(P/'build'),'--target','RMC','-j','8'])
(P/'logs/normal-binary-sha256').write_text(hashlib.sha256((P/'build/bin/RMC').read_bytes()).hexdigest())
print('fresh build complete',flush=True)

from pathlib import Path
import json,subprocess,shlex,concurrent.futures,hashlib,sys
P=Path('/tmp/w14-codex-review');B=P/'build';out=P/'sanitized';out.mkdir(exist_ok=True)
flags=['-g','-O0','-fno-omit-frame-pointer','-fsanitize=address,undefined,float-cast-overflow','-fno-sanitize-recover=all']
rows=json.loads((B/'compile_commands.json').read_text());names=['SampleParticle.cpp','SampleNeutronSource.cpp','ParticleStateFun.cpp'];mapping={};jobs=[]
for name in names:
 row=next(r for r in rows if r['file'].endswith('/'+name));args=shlex.split(row['command']);old=args[args.index('-o')+1];obj=out/(name+'.o');mapping[old]=str(obj);args[args.index('-o')+1]=str(obj);args+=flags;jobs.append((name,args,row['directory']))
def run(job):
 name,args,cwd=job;d=P/'logs'/('sanitized-'+name);d.mkdir(exist_ok=True);(d/'command.json').write_text(json.dumps({'argv':args,'cwd':cwd},indent=2))
 with (d/'stdout').open('w') as o,(d/'stderr').open('w') as e:r=subprocess.run(args,cwd=cwd,stdout=o,stderr=e)
 (d/'exitcode').write_text(str(r.returncode));assert r.returncode==0,name
if len(sys.argv)==1:
 with concurrent.futures.ThreadPoolExecutor(3) as ex:list(ex.map(run,jobs))
 (out/'mapping.json').write_text(json.dumps(mapping,indent=2));print('Sanitized units compiled',flush=True)
else:
 args=shlex.split((B/'CMakeFiles/RMC.dir/link.txt').read_text());mapping=json.loads((out/'mapping.json').read_text());args=[mapping.get(a,a) for a in args];args[args.index('-o')+1]=str(out/'RMC');args+=flags+['-no-pie','-Wl,-Map='+str(out/'link.map')];run(('link',args,str(B)))
 (out/'binary-sha256').write_text(hashlib.sha256((out/'RMC').read_bytes()).hexdigest());print('sanitized binary linked')

from pathlib import Path
import subprocess,shlex,json,sys,concurrent.futures,hashlib
P=Path('/tmp/w14-repair-20261017');B=P/sys.argv[1];rows=json.loads((B/'compile_commands.json').read_text());normal={r['file']:r for r in rows if 'CMakeFiles/RMC.dir/' in r['command']};prepared=[r for r in rows if 'RMCPreparedLifecycle.dir/' in r['command']];mapping={};proof=[];jobs=[]
def obj(r):
 args=shlex.split(r['command']);return Path(r['directory'])/args[args.index('-o')+1]
def flags(r):
 args=shlex.split(r['command']);i=args.index('-o');return args[:i]+args[i+2:]
for r in prepared:
 if r['file'] in normal:
  n=normal[r['file']];assert flags(n)==flags(r),(n['file'],'compile flags differ')
  assert obj(n).is_file(),str(obj(n));mapping[str(obj(r).resolve())]=str(obj(n).resolve());proof.append({'source':r['file'],'object':str(obj(n)),'sha256':hashlib.sha256(obj(n).read_bytes()).hexdigest(),'identical_compile_flags':True})
 else:jobs.append(r)
assert len(jobs)==2
L=P/'logs'/('prepared-'+B.name);L.mkdir(exist_ok=True)
def run(name,args,cwd):
 d=L/name;d.mkdir(exist_ok=True);(d/'command.json').write_text(json.dumps({'argv':args,'cwd':str(cwd)},indent=2))
 with (d/'stdout').open('w') as o,(d/'stderr').open('w') as e:r=subprocess.run(args,cwd=cwd,stdout=o,stderr=e)
 (d/'exitcode').write_text(str(r.returncode));assert r.returncode==0,name
for r in jobs:
 obj(r).parent.mkdir(parents=True,exist_ok=True);run(Path(r['file']).name,shlex.split(r['command']),r['directory'])
cwd=B/'tests/prepared_fixed_source_lifecycle';args=shlex.split((cwd/'CMakeFiles/RMCPreparedLifecycle.dir/link.txt').read_text());args=[mapping.get(str((cwd/a).resolve()),a) if a.endswith('.o') else a for a in args]
(L/'reused-objects.json').write_text(json.dumps(proof,indent=2));run('link',args,cwd)
print('prepared linked',B.name,len(proof),'identical-flag production objects')

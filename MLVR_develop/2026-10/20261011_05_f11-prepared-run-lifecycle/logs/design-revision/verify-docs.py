"""Read-only repository/document checks; writes only this task's verification JSON."""
from pathlib import Path
import hashlib, json, re, subprocess, datetime
root=Path(__file__).resolve().parents[5]
task=root/'MLVR_develop/2026-10/20261011_05_f11-prepared-run-lifecycle'
out=task/'logs/design-revision'
start=json.loads((out/'start.json').read_text())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def command(args):
 r=subprocess.run(args,cwd=root,capture_output=True,text=True)
 return {'argv':args,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
changed=[p for p,h in start['protected_sha256'].items() if not (root/p).is_file() or digest(root/p)!=h]
oldsrc={p for p in start['protected_sha256'] if p.startswith('RMC/src/')}
now_src={str(p.relative_to(root)) for p in (root/'RMC/src').rglob('*') if p.is_file()}
review=root/'MLVR_develop/2026-10/20261011_06_independent-f11-prepared-lifecycle-review'
old_review={p for p in start['protected_sha256'] if p.startswith(str(review.relative_to(root))+'/')}
now_review={str(p.relative_to(root)) for p in review.rglob('*') if p.is_file()}
docs=[task/n for n in ['README.md','lifecycle-design.md','state-ownership.md','source-call-graph.md','test-plan.md']]
bad_links=[]
for p in docs:
 for match in re.finditer(r'\[[^\]\n]+\]\(([^)\n]+)\)',p.read_text()):
  target=match.group(1).split('#')[0]
  if not target or '://' in target: continue
  if not (p.parent/target).exists(): bad_links.append([p.name,target])
sections=re.findall(r'^## ([1-5])\.',docs[0].read_text(),re.M)
ld=docs[1].read_text();tp=docs[-1].read_text()
planned=[]
rows=ld.split('## 5. 实际拟改文件、理由、回滚')[1].split('tests/CMakeLists.txt从')[0]
for row in rows.splitlines():
 if not row.startswith('| '): continue
 cell=row.split('|')[1]
 for name in re.findall(r'(?:src/[\w./]+\.(?:h|cpp)|tests/[\w/]+/(?:CMakeLists\.txt|[\w]+\.cpp)|(?<!/)\bCMakeLists\.txt)',cell):
  planned.append({'path':name,'action':'modify' if (root/'RMC'/name).is_file() else 'new','executed':False})
assert len(planned)==29 and len({p['path'] for p in planned})==29,planned
(out/'planned-files.json').write_text(json.dumps({'scope':'planned only; awaits user approval; no source changes','files':planned},ensure_ascii=False,indent=2)+'\n')
checks={
 'protected_changed':changed,'protected_count':len(start['protected_sha256']),
 'rmc_source_count':len(oldsrc),'rmc_source_set_unchanged':oldsrc==now_src,
 'task06_file_set_unchanged':old_review==now_review,'broken_links':bad_links,
 'readme_five_sections':sections==['1','2','3','4','5'],
 'planned_files':len(planned),'planned_new_files':sum(p['action']=='new' for p in planned),
 'scope_hooks_documented':all(x in ld and x in tp for x in ['G0','G7a','G7b','legacy_mixed_not_per_run','N/D/W0']),
 'approval_pending':'尚无Stage2源码批准' in docs[0].read_text(),
 'diff_check':command(['git','diff','--check']),
 'rmc_git_status':command(['git','-C','RMC','status','--porcelain']),
 'root_head':command(['git','rev-parse','HEAD']),
 'rmc_head':command(['git','-C','RMC','rev-parse','HEAD']),
 'stage2_builds_or_transport_executed':False,
 'documents_sha256':{str(p.relative_to(root)):digest(p) for p in docs},
 'time':datetime.datetime.now().astimezone().isoformat()
}
checks['passed']=not changed and oldsrc==now_src and old_review==now_review and not bad_links and checks['readme_five_sections'] and checks['scope_hooks_documented'] and checks['approval_pending'] and checks['diff_check']['exit']==0 and checks['rmc_git_status']['stdout']=='' and checks['rmc_git_status']['exit']==0
(out/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in checks.items() if k not in ['documents_sha256']},ensure_ascii=False,indent=2))
raise SystemExit(0 if checks['passed'] else 1)

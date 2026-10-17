"""Verify archived evidence and recompute numeric comparisons without running RMC."""
from pathlib import Path
import tempfile,hashlib,json,contextlib,io,types
T=Path(__file__).resolve().parents[1];L=T/'logs/local-evidence';M=json.loads((T/'evidence-manifest.json').read_text())
for name,entry in M['raw_evidence_files'].items():
 p=T/name
 assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],name
print('raw evidence hashes:',len(M['raw_evidence_files']),'verified')
with tempfile.TemporaryDirectory(prefix='w14-archive-recheck-') as temp:
 p=Path(temp)
 for name in ['runs','scripts']:(p/name).symlink_to(L/name,target_is_directory=True)
 for script,result in [('analyze-velocity.py','velocity-results.json'),('compare-ordinary.py','ordinary-comparison.json')]:
  code=(T/'scripts'/script).read_text().replace('/tmp/w14-repair-20261017',str(p))
  try:
   with contextlib.redirect_stdout(io.StringIO()):exec(compile(code,script,'exec'),{'__name__':'__main__'})
  except SystemExit as exc:assert not exc.code,(script,exc.code)
  assert json.loads((p/result).read_text())==json.loads((T/result).read_text()),result
  print(result,'recomputed exactly')
code=(L/'lifecycle/tools/compare_lifecycle.py').read_text().replace('/tmp/w14-repair-20261017/lifecycle',str(L/'lifecycle'))
m=types.ModuleType('archived_compare');exec(compile(code,'compare_lifecycle.py','exec'),m.__dict__)
plans=json.loads((L/'lifecycle/logs/lifecycle-plans.json').read_text())
for seq,label in [('ff','after'),('faf-ww','after-bank-final')]:
 root=L/'lifecycle/logs'/label/seq
 for row in plans[seq]:m.pair(root/'persistent',root/('fresh-'+str(row['id'])),row['id'],row)
 assert not m.errors,(seq,m.errors)
 print(seq,'fresh-process comparisons rechecked')
print('No RMC execution or production modification performed.')

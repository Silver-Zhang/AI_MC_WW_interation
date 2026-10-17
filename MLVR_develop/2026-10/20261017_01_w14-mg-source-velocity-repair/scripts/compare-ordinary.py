from pathlib import Path
import json,importlib.util,sys
P=Path('/tmp/w14-repair-20261017');s=importlib.util.spec_from_file_location('cmp',P/'scripts/compare_lifecycle.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
results=[]
for case in ['F-inbounds_wrong','A-inbounds_wrong','F-WW-descendants','A-WW-descendants','F-spectrum','A-spectrum','F-CE','F-CE-WW']:
 mode='trace-spectrum' if 'spectrum' in case else 'trace-bank-final' if case in ['F-WW-descendants','A-WW-descendants'] else 'trace';dirs=[P/'runs'/v/mode/case for v in ['before','after']];m.errors=[];m.allowed=[]
 for d in dirs:
  assert int((d/'exitcode').read_text())==0,d
  assert json.loads((d/'observer.json').read_text())['errors']==[],d
 for kind in ['clear','before-finalize','final','legacy','derived','raw','start','end','trace-summary']:
  m.compare(*[json.loads((d/('1-'+kind+'.json')).read_text()) for d in dirs],case+'/'+kind)
 tally_equal=(dirs[0]/'inp.Tally').read_bytes()==(dirs[1]/'inp.Tally').read_bytes()
 if not tally_equal:m.errors.append('Tally text differs')
 # Newly added preliminary lookup must not duplicate the pre-existing boundary warnings.
 def warnings(d):return [l for l in (d/'stdout').read_text().splitlines() if 'particle energy ' in l]
 if warnings(dirs[0])!=warnings(dirs[1]):m.errors.append('group warning sequence differs')
 result={'case':case,'passed':not m.errors,'errors':m.errors.copy(),'time_exceptions':m.allowed.copy(),'tally_byte_identical':tally_equal,'trace':json.loads((dirs[1]/'1-trace-summary.json').read_text()),'energy_warning_count':len(warnings(dirs[1]))};results.append(result);print(case,result['passed'],len(m.errors),flush=True)
(P/'ordinary-comparison.json').write_text(json.dumps({'physical_tolerance':0,'cases':results},indent=2));sys.exit(any(not r['passed'] for r in results))

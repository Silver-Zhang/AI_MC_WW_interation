from pathlib import Path
P=Path('/home/workspace/AI_MC_WW_interation/MLVR_develop/2026-10/20261011_05_f11-prepared-run-lifecycle/logs/p1-correction')
from pathlib import Path
import subprocess,concurrent.futures,json,sys
T=P;label=sys.argv[1]
def run(pair):
 name,fresh=pair;cmd=['python3',str(T/'tools/run_lifecycle.py'),name,'--label',label,'--trace']+(['--fresh'] if fresh else [])
 return {'sequence':name,'fresh':fresh,'exit':subprocess.call(cmd)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,[(n,f) for n in ['ff','faf','aa','ww','faf-ww','reuse'] for f in [False,True]]))
(P/'logs'/label/'runs-summary.json').write_text(json.dumps(results,indent=2));print(results)
failed=any(x['exit']!=0 for x in results)
for name in ['ff','faf','aa','ww','faf-ww','reuse']:
 code=subprocess.call(['python3',str(T/'tools/run_command.py'),'--log',str(P/'logs'/label/name/'compare-command'),'--','python3',str(T/'tools/compare_lifecycle.py'),name,'--label',label])

 failed=failed or code!=0
sys.exit(int(failed))

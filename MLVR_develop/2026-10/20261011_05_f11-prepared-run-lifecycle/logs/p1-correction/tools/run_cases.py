from pathlib import Path
P=Path('/home/workspace/AI_MC_WW_interation/MLVR_develop/2026-10/20261011_05_f11-prepared-run-lifecycle/logs/p1-correction')
#!/usr/bin/env python3
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

TASK = P
RUN = Path('/tmp/20261012-f11-stage2-p1')
parser = argparse.ArgumentParser()
parser.add_argument('role', choices=['baseline', 'refactor'])
parser.add_argument('--case')
parser.add_argument('--suffix', default='')
a = parser.parse_args()
tag = a.role + a.suffix
exe = RUN / (('baseline' if a.role == 'baseline' else 'stage2') + '-build/bin/RMC')
identity = {'exe': str(exe), 'sha256': hashlib.sha256(exe.read_bytes()).hexdigest()}
(P / 'logs' / (a.role + '-binary.json')).write_text(json.dumps(identity, indent=2))

def run(inp):
    case = inp.stem
    work = RUN / (tag + '-runs') / case
    work.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(inp, work / 'inp')
    dest = P / 'logs' / (tag + '-cases') / case
    cmd = [sys.executable, str(TASK / 'tools/run_command.py'), '--log', str(dest),
           '--cwd', str(work), '--timeout', '300', '--', str(exe), '-i', 'inp',
           '-d', '/home/silver/NucXS_Library/RMC_DATA']
    code = subprocess.run(cmd).returncode
    for name in ['inp', 'inp.Tally', 'inp.out', 'inp.material']:
        if (work / name).exists():
            shutil.copyfile(work / name, dest / name)
    return case, code

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    inputs = ([P / 'inputs' / (a.case + '.inp')] if a.case else sorted((P / 'inputs').glob('*.inp')))
    results = dict(pool.map(run, inputs))
(P / 'logs' / (tag + '-cases-summary.json')).write_text(json.dumps(results, indent=2))
expected = json.loads((TASK / 'logs/baseline-cases-summary.json').read_text())
sys.exit(0 if all(v == expected[k] for k, v in results.items()) else 1)

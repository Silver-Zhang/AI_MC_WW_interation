#!/usr/bin/env python3
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

TASK = Path(__file__).resolve().parents[1]
RUN = Path('/tmp/20261011_04_f11-fixed-source-core-refactor')
parser = argparse.ArgumentParser()
parser.add_argument('role', choices=['baseline', 'refactor'])
parser.add_argument('--case')
parser.add_argument('--suffix', default='')
a = parser.parse_args()
tag = a.role + a.suffix
exe = RUN / (a.role + '-build/bin/RMC')
identity = {'exe': str(exe), 'sha256': hashlib.sha256(exe.read_bytes()).hexdigest()}
(TASK / 'logs' / (a.role + '-binary.json')).write_text(json.dumps(identity, indent=2))

def run(inp):
    case = inp.stem
    work = RUN / (tag + '-runs') / case
    work.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(inp, work / 'inp')
    dest = TASK / 'logs' / (tag + '-cases') / case
    cmd = [sys.executable, str(TASK / 'tools/run_command.py'), '--log', str(dest),
           '--cwd', str(work), '--timeout', '300', '--', str(exe), '-i', 'inp',
           '-d', '/home/silver/NucXS_Library/RMC_DATA']
    code = subprocess.run(cmd).returncode
    for name in ['inp', 'inp.Tally', 'inp.out', 'inp.material']:
        if (work / name).exists():
            shutil.copyfile(work / name, dest / name)
    return case, code

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    inputs = ([TASK / 'inputs' / (a.case + '.inp')] if a.case else sorted((TASK / 'inputs').glob('*.inp')))
    results = dict(pool.map(run, inputs))
(TASK / 'logs' / (tag + '-cases-summary.json')).write_text(json.dumps(results, indent=2))
sys.exit(0 if all(v == 0 for v in results.values()) else 1)

from pathlib import Path
P=Path('/home/workspace/AI_MC_WW_interation/MLVR_develop/2026-10/20261011_05_f11-prepared-run-lifecycle/logs/p1-correction')
#!/usr/bin/env python3
"""Capture outputs from the frozen CTest fixtures without execute.py cleanup."""
import argparse
import concurrent.futures
import json
from pathlib import Path
import shutil
import subprocess
import sys

TASK = P
RUN = Path('/tmp/20261012-f11-stage2-p1')
parser = argparse.ArgumentParser()
parser.add_argument('role', choices=['baseline', 'refactor'])
a = parser.parse_args()
CASES = ['fixed_source_1', 'fixed_source_4', 'fixed_source_adjoint', 'var_reduce_wwmesh_n',
         'fixed_source_photon', 'fixed_source_electron', 'fixed_source_photon_and_electron',
         'fixed_source_neutron_and_photon_and_electron', 'RestartFixRead']

def run(case):
    work = RUN / (a.role + '-existing-runs') / case
    shutil.copytree(RUN / 'baseline-src/tests' / case, work)
    dest = P / 'logs' / (a.role + '-existing-cases') / case
    cmd = [str(RUN / (('baseline' if a.role == 'baseline' else 'stage2') + '-build/bin/RMC')), '-i', 'inp', '-d',
           '/home/silver/NucXS_Library/RMC_DATA']
    if (work / 'inp_binary').exists():
        cmd += ['-r', 'inp_binary']
    code = subprocess.run([sys.executable, str(TASK / 'tools/run_command.py'), '--log', str(dest),
                           '--cwd', str(work), '--timeout', '300', '--', *cmd]).returncode
    for name in ['inp', 'inp.Tally', 'inp.out', 'inp.material']:
        if (work / name).exists():
            shutil.copyfile(work / name, dest / name)
    return case, code

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    codes = dict(pool.map(run, CASES))
(P / 'logs' / (a.role + '-existing-summary.json')).write_text(json.dumps(codes, indent=2))
sys.exit(0 if all(code == 0 for code in codes.values()) else 1)

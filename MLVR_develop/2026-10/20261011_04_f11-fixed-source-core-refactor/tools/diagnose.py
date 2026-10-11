#!/usr/bin/env python3
import argparse
import concurrent.futures
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys

TASK = Path(__file__).resolve().parents[1]
RUN = Path('/tmp/20261011_04_f11-fixed-source-core-refactor')
parser = argparse.ArgumentParser()
parser.add_argument('role', choices=['baseline', 'refactor'])
a = parser.parse_args()
CASES = ['mg-neutron-analog', 'mg-neutron-adjoint', 'mg-neutron-native-ww']

def run(case):
    if a.role == 'baseline' and case == 'mg-neutron-analog':
        dest = TASK / 'logs/baseline-diag-pilot'
        work = RUN / 'baseline-diag-pilot'
    else:
        work = RUN / (a.role + '-diagnostic-runs') / case
        work.mkdir(parents=True, exist_ok=False)
        (work / 'inp').write_text((TASK / 'inputs' / (case + '.inp')).read_text()
                                 .replace('POPULATION=5000', 'POPULATION=500'))
        dest = TASK / 'logs' / (a.role + '-diagnostics') / case
        cmd = [sys.executable, str(TASK / 'tools/run_command.py'), '--log', str(dest),
               '--cwd', str(work), '--timeout', '600', '--', 'gdb', '-q', '-batch',
               '-x', str(TASK / 'tools/diagnose.gdb'), '--args',
               str(RUN / (a.role + '-build/bin/RMC')), '-i', 'inp', '-d',
               '/home/silver/NucXS_Library/RMC_DATA']
        assert subprocess.run(cmd).returncode == 0
    for name in ['inp', 'inp.Tally']:
        shutil.copyfile(work / name, dest / name)
    data = (dest / 'stdout.txt').read_text()
    assert 'exited normally' in data
    results = [json.loads(s[len('DIAGNOSTIC_RESULT '):]) for s in data.splitlines()
               if s.startswith('DIAGNOSTIC_RESULT ')]
    assert len(results) == 1
    result = results[0]
    assert not result['errors']
    assert result['counts']['INIT'] == result['counts']['PROCESS_ENTRY'] == 1
    assert result['counts']['RNG_BEFORE_SAMPLE'] == result['counts']['HISTORY_SCORE'] == 500
    assert result['source_work_is_copy'] and result['external_source_unchanged']
    assert result['final_stats']['registry'] == {'n': 2, 'owned': [True, True]}
    if case.endswith('native-ww'):
        assert result['counts']['ROULETTE'] > 0 and result['counts']['SPLIT'] > 0
        assert result['counts']['BANK_SAMPLE'] > 0
    (dest / 'result.json').write_text(json.dumps(result, indent=2))
    if (dest / 'stdout.txt').stat().st_size > 10*1024*1024:
        with (dest / 'stdout.txt').open('rb') as src, gzip.open(dest / 'stdout.txt.gz', 'wb') as out:
            shutil.copyfileobj(src, out)
        (dest / 'stdout.txt').unlink()
    print(case, result['counts'], result['trace_sha256'], flush=True)
    return case, str(dest.relative_to(TASK))

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results = dict(pool.map(run, CASES))
(TASK / 'logs' / (a.role + '-diagnostics-index.json')).write_text(json.dumps(results, indent=2))

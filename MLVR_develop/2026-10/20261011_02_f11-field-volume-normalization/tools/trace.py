#!/usr/bin/env python3
"""Read-only debugger acquisition; fresh run directories for all four cases."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

TASK = Path(__file__).resolve().parents[1]
EXE = '/tmp/f11-volume-rmc-build-snapshot/bin/RMC'
DB = '/home/silver/NucXS_Library/RMC_DATA'
ROOT = Path(tempfile.mkdtemp(prefix='f11-volume-trace-'))
DEST = TASK / 'logs' / 'trace'
DEST.mkdir(exist_ok=False)

def run(case):
    work = ROOT / case
    work.mkdir()
    dest = DEST / case
    dest.mkdir()
    shutil.copyfile(TASK / 'inputs' / (case + '.inp'), work / 'inp')
    command = ['gdb', '-q', '-batch', '-x', str(TASK / 'tools' / 'trace.gdb'),
               '--args', EXE, '-i', 'inp', '-d', DB]
    (dest / 'command.txt').write_text('cd ' + shlex.quote(str(work)) + '\n' + shlex.join(command) + '\n')
    with (dest / 'stdout.txt').open('w') as stdout, (dest / 'stderr.txt').open('w') as stderr:
        result = subprocess.run(command, cwd=work, stdout=stdout, stderr=stderr, timeout=180)
    (dest / 'exitcode.txt').write_text(str(result.returncode) + '\n')
    for name in ['inp', 'inp.Tally', 'inp.out', 'inp.PTRAC']:
        if (work / name).exists():
            shutil.copyfile(work / name, dest / name)
    hashes = {name: hashlib.sha256((dest / name).read_bytes()).hexdigest()
              for name in ['inp', 'inp.Tally'] if (dest / name).exists()}
    (dest / 'sha256.json').write_text(json.dumps(hashes, indent=2))
    print(case, 'gdb exit=', result.returncode, flush=True)
    return result.returncode

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    codes = list(pool.map(run, ['uniform_n0', 'uniform_n1', 'heter_n0', 'heter_n1']))
raise SystemExit(max(codes))

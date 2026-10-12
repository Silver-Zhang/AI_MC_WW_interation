from pathlib import Path
P=Path('/home/workspace/AI_MC_WW_interation/MLVR_develop/2026-10/20261011_05_f11-prepared-run-lifecycle/logs/p1-correction')
#!/usr/bin/env python3
"""Preserve exact commands and raw output; never update reference results."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

p = argparse.ArgumentParser()
p.add_argument('--log', required=True)
p.add_argument('--cwd')
p.add_argument('--timeout', type=int, default=3600)
p.add_argument('command', nargs=argparse.REMAINDER)
a = p.parse_args()
command = a.command[1:] if a.command[:1] == ['--'] else a.command
dest = Path(a.log).resolve()
dest.mkdir(parents=True, exist_ok=False)
cwd = str(Path(a.cwd or os.getcwd()).resolve())
meta = {'argv': command, 'cwd': cwd,
        'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'environment': {k: os.environ.get(k) for k in
                        ['RMC_DATA_PATH', 'RMC_PATH', 'RMC_MPI_TEST', 'RMC_OMP_TEST',
                         'OMP_NUM_THREADS', 'TZ']}}
(dest / 'command.json').write_text(json.dumps(meta, indent=2))
start = time.monotonic()
with (dest / 'stdout.txt').open('w') as out, (dest / 'stderr.txt').open('w') as err:
    try:
        r = subprocess.run(command, cwd=cwd, stdout=out, stderr=err, timeout=a.timeout)
        code = r.returncode
    except subprocess.TimeoutExpired:
        err.write('Timeout expired\n')
        code = 124
(dest / 'exitcode.txt').write_text(str(code) + '\n')
(dest / 'duration_seconds.txt').write_text(str(time.monotonic() - start) + '\n')
print(dest.name, 'exit=', code, flush=True)
sys.exit(code)

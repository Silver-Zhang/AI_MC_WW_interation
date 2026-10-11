#!/usr/bin/env python3
"""Run unmodified RMC in new /tmp directories; preserve selected raw evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

TASK = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--exe', default='/tmp/f11-volume-rmc-build-snapshot/bin/RMC')
parser.add_argument('--database', default='/home/silver/NucXS_Library/RMC_DATA')
parser.add_argument('--label', required=True)
parser.add_argument('--case', choices=['uniform_n0', 'uniform_n1', 'heter_n0', 'heter_n1'])
args = parser.parse_args()
exe = Path(args.exe).resolve()
database = Path(args.database).resolve()
out = TASK / 'logs' / args.label
out.mkdir(exist_ok=False)
identity = {'exe': str(exe), 'exe_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
            'database': str(database), 'database_files': {}}
for name in ['xsdir', 'multigroup/mgxsnp']:
    f = database / name
    identity['database_files'][name] = {'path': str(f.resolve()), 'size': f.stat().st_size,
                                       'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
identity['xsdir_entries'] = [s for s in (database / 'xsdir').read_text().splitlines()
                            if s.split() and s.split()[0] in ['1001.50m', '8016.50m']]
(out / 'identity.json').write_text(json.dumps(identity, indent=2))
cases = [args.case] if args.case else ['uniform_n0', 'uniform_n1', 'heter_n0', 'heter_n1']
root = Path(tempfile.mkdtemp(prefix='f11-volume-runs-'))
for case in cases:
    work = root / case
    work.mkdir()
    dest = out / case
    dest.mkdir()
    shutil.copyfile(TASK / 'inputs' / (case + '.inp'), work / 'inp')
    shutil.copyfile(work / 'inp', dest / 'inp')
    (work / 'xsdir').symlink_to(database / 'xsdir')
    command = [str(exe), '-i', 'inp', '-d', str(database)]
    (dest / 'command.txt').write_text('cd ' + shlex.quote(str(work)) + '\n' + shlex.join(command) + '\n')
    env = dict(os.environ, OMP_NUM_THREADS='1')
    with (dest / 'stdout.txt').open('w') as stdout, (dest / 'stderr.txt').open('w') as stderr:
        result = subprocess.run(command, cwd=work, env=env, stdout=stdout, stderr=stderr, timeout=60)
    (dest / 'exitcode.txt').write_text(str(result.returncode) + '\n')
    for suffix in ['.Tally', '.PTRAC', '.out', '.material']:
        f = work / ('inp' + suffix)
        if f.exists():
            shutil.copyfile(f, dest / f.name)
    print(case, 'exit=', result.returncode, 'raw=', dest, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)

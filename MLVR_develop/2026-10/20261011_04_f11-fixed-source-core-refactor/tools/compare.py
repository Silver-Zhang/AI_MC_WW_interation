#!/usr/bin/env python3
"""Exact fresh-process comparison; exclusions were set before production edits."""
import difflib
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

TASK = Path(__file__).resolve().parents[1]
RUN = Path('/tmp/20261011_04_f11-fixed-source-core-refactor')
parser = argparse.ArgumentParser()
parser.add_argument('--label', default='comparison')
a = parser.parse_args()
DEST = TASK / 'logs' / a.label
DEST.mkdir(exist_ok=False)
results = {}

def canonical_text(text):
    lines = []
    for line in text.splitlines():
        if line.startswith('Build time  :'):
            line = 'Build time  : <time>'
        elif line.startswith('Input File = '):
            line = re.sub(r'\d{4}/\d\d/\d\d .*', '<date>', line)
        elif line.startswith('Total Calculational Time:'):
            line = 'Total Calculational Time: <time>'
        elif re.match(r'^\s*(?:Total Calculation Time|Time in |Time spent |Calculation rate in )', line):
            line = re.sub(r'[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?', '<time>', line)
        lines.append(line)
    return '\n'.join(lines)

def hdf(path):
    raw = subprocess.check_output(['h5dump', '-m', '%.17g', '-y', '-w', '0', str(path)], text=True)
    if path.parent.name == 'fixed_source_4' and path.name == 'inp.Result.h5':
        # The pre-run plan explicitly permits wall-clock-dependent FOM values.
        # Preserve dataset existence, type and shape; normalize only six DATA bodies.
        names = subprocess.check_output(['h5dump', '-n', str(path)], text=True)
        paths = {line.strip().removeprefix('dataset').strip() for line in names.splitlines()
                 if 'dataset' in line and line.strip().endswith(('/FOM', '/Fluctuated_FOM', '/Batches_of_FOM'))}
        expected = {f'/Tally/CellTally2/Cell{cell}/TotalBin/{name}' for cell in [1,3]
                    for name in ['FOM', 'Fluctuated_FOM', 'Batches_of_FOM']}
        assert paths == expected
        pattern = r'(DATASET "(?:FOM|Fluctuated_FOM|Batches_of_FOM)" \{\s*DATATYPE[^\n]*\n\s*DATASPACE[^\n]*\n\s*DATA \{)\n.*?\n(\s*\}\n\s*\})'
        raw, n = re.subn(pattern, r'\1\n <wall-clock-dependent-FOM>\n\2', raw, flags=re.S)
        assert n == 6
    return re.sub(r'^HDF5 "[^"]*"', 'HDF5 "<file>"', raw)

def same(label, old, new):
    ok = old == new
    results[label] = ok
    if not ok:
        (DEST / (re.sub(r'[^a-zA-Z0-9_-]', '_', label) + '.diff')).write_text(
            ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                        fromfile='baseline', tofile='refactor')))
    return ok

def directories(label, old, new):
    assert (old / 'inp').read_bytes() == (new / 'inp').read_bytes()
    for name in ['inp.Tally', 'test_result', 'inp.material']:
        if (old / name).exists():
            same(label + '/' + name, (old / name).read_text(), (new / name).read_text())
    same(label + '/inp.out', canonical_text((old / 'inp.out').read_text()),
         canonical_text((new / 'inp.out').read_text()))
    old_files = sorted(f.name for f in old.glob('*.h5') if not f.name.startswith('reference'))
    new_files = sorted(f.name for f in new.glob('*.h5') if not f.name.startswith('reference'))
    same(label + '/hdf-files', repr(old_files), repr(new_files))
    for name in old_files:
        same(label + '/' + name, hdf(old / name), hdf(new / name))

for case, path in json.loads((TASK / 'logs/baseline-case-paths.json').read_text()).items():
    directories(case, Path(path), RUN / 'refactor-runs' / case)

ctests = ['fixed_source_1', 'fixed_source_4', 'fixed_source_adjoint', 'var_reduce_wwmesh_n',
          'fixed_source_photon', 'fixed_source_electron', 'fixed_source_photon_and_electron',
          'fixed_source_neutron_and_photon_and_electron', 'RestartFixRead']
for case in ctests:
    directories('ctest-' + case, RUN / 'baseline-existing-runs' / case,
                RUN / 'refactor-existing-runs' / case)

old_index = json.loads((TASK / 'logs/baseline-diagnostics-index.json').read_text())
new_index = json.loads((TASK / 'logs/refactor-diagnostics-index.json').read_text())
for case in old_index:
    old = json.loads((TASK / old_index[case] / 'result.json').read_text())
    new = json.loads((TASK / new_index[case] / 'result.json').read_text())
    same('diagnostic-' + case, json.dumps(old, sort_keys=True), json.dumps(new, sort_keys=True))

def flags(path):
    data = path.read_text()
    defines = re.search(r'^CXX_DEFINES = (.*)$', data, re.M).group(1)
    options = re.search(r'^CXX_FLAGS = (.*)$', data, re.M).group(1)
    return defines, options

for suffix in ['build', 'mpi-build']:
    same('flags-' + suffix, repr(flags(RUN / ('baseline-' + suffix) / 'CMakeFiles/RMC.dir/flags.make')),
         repr(flags(RUN / ('refactor-' + suffix) / 'CMakeFiles/RMC.dir/flags.make')))

summary = {'checks': len(results), 'passed': sum(results.values()), 'failed': [k for k,v in results.items() if not v],
           'all_passed': all(results.values()), 'results': results,
           'physical_tolerance': 0, 'text_tally_comparison': 'byte-equivalent text',
           'HDF5_comparison': 'all datasets at 17 significant digits; six documented wall-clock FOM DATA bodies normalized; all datatype/dataspace metadata retained',
           'diagnostic_comparison': 'all events digest + raw IEEE vector bits + counts/source ownership'}
(DEST / 'results.json').write_text(json.dumps(summary, indent=2))
print('Exact comparison:', summary['passed'], '/', summary['checks'])
print('Failed:', summary['failed'])
sys.exit(0 if summary['all_passed'] else 1)

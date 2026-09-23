#!/usr/bin/env python3
"""Parse F04-B scalar cell-tally outputs and compare paired cases."""
from __future__ import annotations
import argparse
import math
import re
from pathlib import Path
from statistics import mean, stdev

SCALAR_RE = re.compile(r"^\s*Tot\s+([+-]?\d\.\d+E[+-]\d+)\s+([+-]?\d\.\d+E[+-]\d+)", re.I)
NUM_RE = re.compile(r"(?:real|user|sys)\s+([0-9.]+)")
EVENT_RE = re.compile(r"(Neutron: Bank_from_Weight_Splitting|Neutron: Weight_Cut_off)")

def parse_case(path: Path) -> dict:
    tally = path / 'inp.Tally'
    if not tally.exists():
        raise FileNotFoundError(tally)
    matches = [SCALAR_RE.match(line) for line in tally.read_text(errors='replace').splitlines()]
    matches = [m for m in matches if m]
    if not matches:
        raise ValueError(f'No total tally line in {tally}')
    m = matches[0]
    value, re_ = map(float, m.groups())
    time_text = (path / 'stderr.log').read_text(errors='replace')
    timing = {m.group(0).split()[0]: float(m.group(1)) for m in NUM_RE.finditer(time_text)}
    wall = timing.get('real')
    out = {'run': path.name, 'value': value, 're': re_, 'sigma': abs(value) * re_, 'wall_s': wall}
    out['fom'] = None if wall is None or re_ <= 0 else 1 / (re_ * re_ * wall)
    ptrac = path / 'inp.PTRAC'
    if ptrac.exists() and ptrac.stat().st_size > 0:
        text = ptrac.read_text(errors='replace')
        out['split_events'] = len(re.findall(r'Neutron: Bank_from_Weight_Splitting', text))
        out['roulette_events'] = len(re.findall(r'Neutron: Weight_Cut_off', text))
        weights = re.findall(r'(?i)wgt\s*=\s*([0-9Ee+.-]+)', text)
        out['ptrac_weights'] = [float(w) for w in weights]
    else:
        out['split_events'] = 0
        out['roulette_events'] = 0
        out['ptrac_weights'] = []
    return out

def combine(rows: list[dict]) -> dict:
    # Equal-history independent runs: sum estimators and absolute standard errors in quadrature.
    n = len(rows)
    value = mean(r['value'] for r in rows)
    sigma = math.sqrt(sum(r['sigma']**2 for r in rows)) / n
    re_ = sigma / abs(value) if value else math.inf
    wall = mean(r['wall_s'] for r in rows)
    fom = None if re_ <= 0 or not math.isfinite(re_) else 1 / (re_**2 * wall)
    return {'n': n, 'value': value, 'sigma': sigma, 're': re_, 'wall_s': wall, 'fom': fom,
            'split_events': sum(r['split_events'] for r in rows),
            'roulette_events': sum(r['roulette_events'] for r in rows)}

def fmt(x): return 'NA' if x is None else f'{x:.8E}'

p = argparse.ArgumentParser()
p.add_argument('--analog', nargs='+', type=Path, required=True)
p.add_argument('--ww', nargs='+', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a_rows = [parse_case(x) for x in a.analog]
w_rows = [parse_case(x) for x in a.ww]
a_sum, w_sum = combine(a_rows), combine(w_rows)
z = (w_sum['value'] - a_sum['value']) / math.sqrt(w_sum['sigma']**2 + a_sum['sigma']**2)
ratio = None if a_sum['fom'] in (None, 0) or w_sum['fom'] is None else w_sum['fom'] / a_sum['fom']
lines = ['# F04-B parsed results', '', '## Per-run']
for tag, rows in [('analog', a_rows), ('ww', w_rows)]:
    lines.append(f'### {tag}')
    lines.append('| run | response | RE | sigma | wall s | FOM | split | roulette |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|---:|')
    for r in rows:
        lines.append(f"| {r['run']} | {fmt(r['value'])} | {fmt(r['re'])} | {fmt(r['sigma'])} | {r['wall_s']:.3f} | {fmt(r['fom'])} | {r['split_events']} | {r['roulette_events']} |")
lines += ['', '## Combined', '| case | n | response | RE | sigma | mean wall s | FOM | split | roulette |', '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for tag, r in [('analog', a_sum), ('ww', w_sum)]:
    lines.append(f"| {tag} | {r['n']} | {fmt(r['value'])} | {fmt(r['re'])} | {fmt(r['sigma'])} | {r['wall_s']:.3f} | {fmt(r['fom'])} | {r['split_events']} | {r['roulette_events']} |")
lines += ['', f'Combined z = {z:.8f}', f'FOM ratio (WW / analog) = {fmt(ratio)}', f'Unbiasedness criterion |z| < 3: {abs(z) < 3}']
a.out.write_text('\n'.join(lines) + '\n')

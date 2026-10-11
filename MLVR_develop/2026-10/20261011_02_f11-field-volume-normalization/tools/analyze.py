#!/usr/bin/env python3
"""Independent ray/box reference. Never derive the reference from RMC Ave."""
import csv
import hashlib
import json
import math
from pathlib import Path
import re

TASK = Path(__file__).resolve().parents[1]
CFG = json.loads((TASK / 'logs/config.json').read_text())
N = CFG['N']
G = CFG['MGACE'][0]

def clip_length(origin, direction, length, lower, upper):
    """Slab intersection in physical cm, independent of CDMesh implementations."""
    enter, leave = 0.0, length
    for x, u, lo, hi in zip(origin, direction, lower, upper):
        if u == 0:
            if not lo <= x < hi:
                return 0.0
        else:
            a, b = (lo - x) / u, (hi - x) / u
            enter, leave = max(enter, min(a, b)), min(leave, max(a, b))
    return max(0.0, leave - enter)

def tally_rows(path):
    result, current = {}, None
    for line in path.read_text().splitlines():
        tokens = line.split()
        if len(tokens) == 7 and all(t.isdigit() for t in tokens[:4]):
            current = tuple(map(int, tokens[:3]))
            result[(current, int(tokens[3]))] = tuple(map(float, tokens[-2:]))
        elif len(tokens) == 4 and tokens[0].isdigit() and current:
            result[(current, int(tokens[0]))] = tuple(map(float, tokens[-2:]))
        elif len(tokens) == 3 and tokens[0] == 'Tot' and current:
            result[(current, 'Tot')] = tuple(map(float, tokens[-2:]))
    assert len(result) == 2 * (G + 1), (path, len(result))
    return result

all_rows, summaries, previous_trace = [], [], None
for case in CFG['case_names']:
    normal = TASK / 'logs/formal' / case
    trace = TASK / 'logs/trace' / case
    assert (normal / 'exitcode.txt').read_text().strip() == '0'
    assert (trace / 'exitcode.txt').read_text().strip() == '0'
    assert (normal / 'inp').read_bytes() == (trace / 'inp').read_bytes()
    assert (normal / 'inp.Tally').read_bytes() == (trace / 'inp.Tally').read_bytes()
    log = (trace / 'stdout.txt').read_text()
    assert 'exited normally' in log
    assert f'DENOM,{N},N={N}' in log
    assert f'AVERAGING,M={N},Div=1' in log
    path, norm = case.split('_n')
    assert f'PATH,{path},usevol={norm},heterflag={int(path == "heter")}' in log
    assert f'COUNTS,histories={N},uniform={N if path == "uniform" else 0},heter={N if path == "heter" else 0}' in log
    source, segments, raw = {}, {}, []
    for line in log.splitlines():
        if line.startswith(('SOURCE,', 'SEGMENT,')):
            raw.append(line)
            tokens = line.split(',')
            history = int(tokens[1])
            target = source if tokens[0] == 'SOURCE' else segments
            assert history not in target, ('duplicate', case, history)
            target[history] = list(map(float, tokens[2:]))
    assert sorted(source) == sorted(segments) == list(range(1, N + 1))
    if previous_trace is not None:
        assert raw == previous_trace, 'random histories changed between configurations'
    previous_trace = raw
    (trace / 'source-segments.csv').write_text('\n'.join(raw) + '\n')
    history_scores = {(i, g): [0.0] * N for i in [1, 2] for g in range(1, G + 1)}
    for h in range(1, N + 1):
        src, seg = source[h], segments[h]
        assert src == seg[:-1]
        assert src[0] == -0.5 and src[1] in [1.0, 3.0] and src[2] == 1.0
        assert src[3:6] == [1.0, 0.0, 0.0] and src[6] == 1.0
        assert src[7] == 13 and seg[8] == 5.5
        # MG transport groups descend in energy; text Energy=-1 rows ascend.
        g = G - int(seg[7]) + 1
        for i in [1, 2]:
            length = clip_length(seg[:3], seg[3:6], seg[8],
                                 [(i-1)*2, 0, 0], [i*2, 2, 2])
            history_scores[(i, g)][h-1] += seg[6] * length
    m = sum(src[1] == 1.0 for src in source.values())
    assert 0 < m < N
    values = tally_rows(normal / 'inp.Tally')
    for i in [1, 2]:
        for g in list(range(1, G + 1)) + ['Tot']:
            scores = (history_scores[(i, g)] if g != 'Tot' else
                      [sum(history_scores[(i, k)][h] for k in range(1, G+1)) for h in range(N)])
            sum1, sum2 = math.fsum(scores), math.fsum(x*x for x in scores)
            volume = CFG['volumes_cm3'][i-1]
            L_ref = sum1 / N
            phi_ref = sum1 / N / volume
            RE_ref = math.sqrt(max(0.0, (N*sum2/(sum1*sum1)-1)/(N-1))) if sum1 else 0.0
            c = 1.0 if path == 'heter' and norm == '1' else 1.0 / volume
            expected = phi_ref / c
            ave, RE = values[((i, 1, 1), g)]
            error, RE_error = ave - expected, RE - RE_ref
            ave_ok = abs(error) <= CFG['tolerance_Ave_absolute'] + CFG['tolerance_Ave_relative']*abs(expected)
            re_ok = abs(RE_error) <= CFG['tolerance_RE_absolute']
            if sum1 == 0:
                ave_ok, re_ok = ave == 0.0, RE == 0.0
            row = {'case': case, 'bin': i, 'group_text_ascending': g,
                   'actual_N': N, 'denominator_M': N, 'denominator_Div': 1,
                   'hit_histories': m, 'zero_histories': N-m, 'V_cm3': volume,
                   'independent_sum_wL': sum1, 'independent_sum_wL2': sum2,
                   'L_ref_cm': L_ref, 'phi_ref_cm-2': phi_ref, 'Ave': ave, 'RE': RE,
                   'expected_Ave': expected, 'Ave_error': error, 'RE_ref': RE_ref,
                   'RE_error': RE_error, 'c': c, 'converted_phi': c*ave,
                   'converted_error': c*ave-phi_ref, 'pass': ave_ok and re_ok}
            all_rows.append(row)
            if g == 18:
                summaries.append(row)
    summary = {'histories': N, 'hit': m, 'zero': N-m, 'segments': len(segments),
               'source_segment_sha256': hashlib.sha256(('\n'.join(raw)+'\n').encode()).hexdigest(),
               'normal_equals_gdb_Tally': True, 'denominator_M': N, 'Div': 1,
               'called_path': path, 'Normalize': int(norm)}
    (trace / 'checks.json').write_text(json.dumps(summary, indent=2))

with (TASK / 'logs/comparison.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(all_rows[0]))
    writer.writeheader()
    writer.writerows(all_rows)
result = {'checks': len(all_rows), 'passed': sum(r['pass'] for r in all_rows),
          'all_passed': all(r['pass'] for r in all_rows), 'nonzero_group_rows': summaries,
          'max_abs_Ave_error': max(abs(r['Ave_error']) for r in all_rows),
          'max_abs_RE_error': max(abs(r['RE_error']) for r in all_rows)}
(TASK / 'logs/comparison.json').write_text(json.dumps(result, indent=2))
print('Independent reference: N=', N, 'hit=', m, 'zero=', N-m, 'V=8 cm^3')
for r in summaries[::2]:
    print(r['case'], 'Ave=', r['Ave'], 'RE=', r['RE'], 'phi_ref=', r['phi_ref_cm-2'],
          'converted_error=', r['converted_error'])
print('Checks:', result['passed'], '/', result['checks'],
      'max Ave error=', result['max_abs_Ave_error'], 'max RE error=', result['max_abs_RE_error'])
raise SystemExit(0 if result['all_passed'] else 1)

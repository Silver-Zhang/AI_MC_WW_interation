#!/usr/bin/env python3
"""Independent read-only check of archived F11 stage-0 trace and tally evidence."""
from pathlib import Path
import hashlib, json, math, sys

src = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
N = 200
G = 30
V = 8.0
cases = ("uniform_n0", "uniform_n1", "heter_n0", "heter_n1")

def parse_rows(path):
    rows = {}
    mesh = None
    for line in path.read_text().splitlines():
        x = line.split()
        if len(x) == 7 and all(t.isdigit() for t in x[:4]):
            mesh = tuple(map(int, x[:3])); rows[(mesh, int(x[3]))] = tuple(map(float, x[-2:]))
        elif len(x) == 4 and x[0].isdigit() and mesh is not None:
            rows[(mesh, int(x[0]))] = tuple(map(float, x[-2:]))
        elif len(x) == 3 and x[0] == 'Tot' and mesh is not None:
            rows[(mesh, 'Tot')] = tuple(map(float, x[-2:]))
    if len(rows) != 62:
        raise ValueError(f'{path}: expected 62 rows, got {len(rows)}')
    return rows

def clip_box(origin, direction, length, lower, upper):
    enter, leave = 0.0, length
    for x, u, lo, hi in zip(origin, direction, lower, upper):
        if u == 0.0:
            if not lo <= x < hi:
                return 0.0
        else:
            a, b = (lo-x)/u, (hi-x)/u
            enter, leave = max(enter, min(a,b)), min(leave, max(a,b))
    return max(0.0, leave-enter)

result = {'method': 'independent parser and 3D ray/box arithmetic; no target-task analysis script imported', 'cases': {}}
trace_digest = None
for case in cases:
    trace = src/'logs/trace'/case
    formal = src/'logs/formal'/case
    for file in ('inp', 'inp.Tally'):
        if (trace/file).read_bytes() != (formal/file).read_bytes():
            raise ValueError(f'{case}: formal/trace {file} differs')
    lines = (trace/'source-segments.csv').read_text().splitlines()
    source, segment = {}, {}
    for line in lines:
        x = line.split(',')
        h = int(x[1])
        if x[0] == 'SOURCE': source[h] = list(map(float, x[2:]))
        elif x[0] == 'SEGMENT': segment[h] = list(map(float, x[2:]))
    if sorted(source) != list(range(1,N+1)) or sorted(segment) != list(range(1,N+1)):
        raise ValueError(f'{case}: incomplete source/segment histories')
    score = {1: [], 2: []}
    hits = {1: 0, 2: 0}
    for h in range(1,N+1):
        sx,sy,sz,u,v,w,weight,internal = source[h]
        x,y,z,du,dv,dw,wgt,internal_seg,length = segment[h]
        if [sx,sy,sz,u,v,w,weight,internal] != [x,y,z,du,dv,dw,wgt,internal_seg]:
            raise ValueError(f'{case}: source mismatch history {h}')
        if (sx,sz,u,v,w,weight,internal,length) != (-.5,1.,1.,0.,0.,1.,13.,5.5):
            raise ValueError(f'{case}: unexpected trajectory history {h}: {source[h]} {length}')
        for i, bounds in {1:([0,0,0],[2,2,2]), 2:([2,0,0],[4,2,2])}.items():
            length_in = clip_box((sx,sy,sz),(u,v,w),length,*bounds)
            score[i].append(weight*length_in)
            hits[i] += length_in > 0
    sums = {i: math.fsum(score[i]) for i in (1,2)}
    if (sums[1],sums[2],hits[1],hits[2]) != (186.0,186.0,93,93):
        raise ValueError(f'{case}: unexpected independent totals {(sums,hits)}')
    digest=hashlib.sha256(('\n'.join(lines)+'\n').encode()).hexdigest()
    if trace_digest is None: trace_digest=digest
    elif trace_digest != digest: raise ValueError(f'{case}: source trace differs between configurations')
    tally=parse_rows(formal/'inp.Tally')
    values=[]
    for i,mesh in ((1,(1,1,1)),(2,(2,1,1))):
        ave, rel = tally[(mesh,18)]
        total, total_re = tally[(mesh,'Tot')]
        if (ave,rel) != (total,total_re): raise ValueError(f'{case} mesh {mesh}: Tot differs from only nonzero group')
        sum1, sum2 = sums[i], math.fsum(q*q for q in score[i])
        re = math.sqrt((N*sum2/(sum1*sum1)-1)/(N-1))
        expected = sum1/N/V if case == 'heter_n1' else sum1/N
        if abs(ave-expected) > 1e-12 or abs(rel-re) > 3e-10: raise ValueError(f'{case} mesh {mesh}: mismatch')
        zero_bad=[]
        for g in range(1,G+1):
            if g != 18 and tally[(mesh,g)] != (0.0,0.0): zero_bad.append(g)
        if zero_bad: raise ValueError(f'{case} mesh {mesh}: nonzero unexpected groups {zero_bad}')
        values.append({'mesh':mesh,'Ave':ave,'RE':rel,'expected_Ave':expected,'phi_density':sum1/N/V,'zero_groups_verified':29})
    result['cases'][case]={'trace_sha256':digest,'histories':N,'hit_histories_per_bin':hits[1],
                           'zero_histories_per_bin':N-hits[1],'sum_weighted_length_per_bin_cm':sums[1],
                           'source_weight_denominator':N,'volume_cm3':V,
                           'physical_text_group_nonzero':18,'internal_group':13,'values':values}
out.write_text(json.dumps(result,indent=2)+'\n')
print('independent volume check PASS')
print(json.dumps(result,indent=2))

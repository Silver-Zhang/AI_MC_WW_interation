#!/usr/bin/env python3
"""Independent F07 runs and analysis; creates task-local inputs only."""
from pathlib import Path
import subprocess, re, json, math, statistics
ROOT=Path(__file__).resolve().parents[1]
EXE=ROOT/'runs/build/bin/RMC'
MAKE=ROOT/'cases/make_f07_case.py'
OUT=ROOT/'runs/matrix'; OUT.mkdir(parents=True,exist_ok=True)
seeds=[101,103,107,109,113,127,131,137,139,149]
# 5 independent seeds at N,4N,16N. N=10k additionally has 10 seeds for empirical check.
plans=[]
for n in (2500,10000,40000):
 for seed in seeds if n==10000 else seeds[:5]: plans.append(('forward',False,n,seed))
# WW calibration: 10 independent 10k histories. Uses same source/mesh, only native WW differs.
for seed in seeds: plans.append(('forward',True,10000,seed))
# one adjoint no-WW case: establishes runtime entry to identical tally statistics path.
plans.append(('adjoint',False,10000,101))

def run(mode,ww,n,seed):
 tag=f'{mode}-{"ww" if ww else "analog"}-n{n}-s{seed}'
 d=OUT/tag; d.mkdir(exist_ok=True)
 inp=d/'inp'
 subprocess.run([str(MAKE),'--mode',mode,'--seed',str(seed),'--nps',str(n),'--out',str(inp) ],check=True)
 if ww:
  # regenerate with WW flag (the generator uses --ww rather than a physical input mutation).
  subprocess.run([str(MAKE),'--mode',mode,'--ww','--seed',str(seed),'--nps',str(n),'--out',str(inp) ],check=True)
 p=subprocess.run(['/usr/bin/time','-p',str(EXE)],cwd=d,text=True,capture_output=True)
 (d/'stdout.log').write_text(p.stdout);(d/'stderr.log').write_text(p.stderr)
 if p.returncode: raise RuntimeError(f'{tag}: {p.returncode}')
 return d

def parse(tally, tally_id=1, group=1):
 active=False; current=None
 for line in tally.read_text().splitlines():
  h=re.search(r'--------- ID = (\d+),',line)
  if h: active=int(h.group(1))==tally_id; current=None; continue
  if not active: continue
  m=re.match(r'^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)',line)
  if m:
   current=(int(m.group(1)),int(m.group(2)),int(m.group(3))); g=int(m.group(4));
   if g==group: return float(m.group(6)),float(m.group(7))
  else:
   m=re.match(r'^\s+(\d+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)',line)
   if m and current:
    g=int(m.group(1))
    if g==group:return float(m.group(3)),float(m.group(4))
 raise RuntimeError(f'No tally {tally_id} group {group} in {tally}')
rows=[]
for mode,ww,n,seed in plans:
 d=run(mode,ww,n,seed)
 raw,rawre=parse(d/'inp.Tally',1,1); norm,normre=parse(d/'inp.Tally',2,1); zero,zerore=parse(d/'inp.Tally',3,1)
 text=(d/'stdout.log').read_text()
 rows.append(dict(mode=mode,ww=ww,n=n,seed=seed,raw=raw,raw_re=rawre,norm=norm,norm_re=normre,zero=zero,zero_re=zerore,
                  split=text.count('Bank_from_Weight_Splitting'),roulette=text.count('Weight_Cut_off'),warnings=text.count('Warning:')))

def group(rows):
 return {'count':len(rows),'mean_re':statistics.mean(x['norm_re'] for x in rows),'sd_re':statistics.stdev(x['norm_re'] for x in rows) if len(rows)>1 else 0,
         'mean_value':statistics.mean(x['norm'] for x in rows),'sd_value':statistics.stdev(x['norm'] for x in rows) if len(rows)>1 else 0,
         'mean_reported_sigma':math.sqrt(statistics.mean((abs(x['norm'])*x['norm_re'])**2 for x in rows))}
summary={'rows':rows}
for n in (2500,10000,40000): summary[f'analog_n{n}']=group([x for x in rows if x['mode']=='forward' and not x['ww'] and x['n']==n])
summary['ww_n10000']=group([x for x in rows if x['mode']=='forward' and x['ww']])
summary['adjoint_n10000']=group([x for x in rows if x['mode']=='adjoint'])
a25,a10,a40=(summary['analog_n2500'],summary['analog_n10000'],summary['analog_n40000'])
summary['scaling']={'RE_2500_over_10000':a25['mean_re']/a10['mean_re'],'RE_10000_over_40000':a10['mean_re']/a40['mean_re']}
summary['empirical_Q_analog_10000']=a10['sd_value']/a10['mean_reported_sigma']
summary['empirical_Q_ww_10000']=summary['ww_n10000']['sd_value']/summary['ww_n10000']['mean_reported_sigma']
summary['normalize_ratios']=[x['raw']/x['norm'] if x['norm'] else None for x in rows if x['mode']=='forward' and not x['ww'] and x['n']==10000]
summary['normalize_RE_differences']=[x['raw_re']-x['norm_re'] for x in rows if x['mode']=='forward' and not x['ww'] and x['n']==10000]
(ROOT/'logs/f07-matrix-results.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))

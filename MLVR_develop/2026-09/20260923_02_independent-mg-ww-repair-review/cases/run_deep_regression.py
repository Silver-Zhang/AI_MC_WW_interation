#!/usr/bin/env python3
from pathlib import Path
import subprocess,re,math,statistics,argparse,json
p=argparse.ArgumentParser(); p.add_argument('--exe',type=Path,required=True); p.add_argument('--out',type=Path,required=True); a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
script=Path(__file__).with_name('make_deep_case.py'); rows=[]
for seed in (101,103,107,109,113):
 for case in ('off','on'):
  d=a.out/f'{case}-{seed}';d.mkdir(); subprocess.run([str(script),'--case',case,'--seed',str(seed),'--population','1000000','--out',str(d/'inp')],check=True)
  r=subprocess.run(['/usr/bin/time','-p',str(a.exe)],cwd=d,text=True,capture_output=True);(d/'stdout.log').write_text(r.stdout);(d/'stderr.log').write_text(r.stderr)
  m=re.search(r'^\s*Tot\s+([0-9.E+-]+)\s+([0-9.E+-]+)',(d/'inp.Tally').read_text(),re.M); assert m and r.returncode==0,(d,r.returncode)
  R,RE=map(float,m.groups()); T=float(re.search(r'^real\s+([0-9.]+)',r.stderr,re.M).group(1));rows.append(dict(case=case,seed=seed,R=R,RE=RE,sigma=R*RE,T=T,FOM=1/(RE*RE*T)))
def combine(rs):
 n=len(rs);R=sum(x['R'] for x in rs)/n;sig=math.sqrt(sum(x['sigma']**2 for x in rs))/n;T=sum(x['T'] for x in rs)/n;return dict(R=R,sigma=sig,RE=sig/R,T=T,FOM=1/(sig/R)**2/T)
o=combine([x for x in rows if x['case']=='off']); w=combine([x for x in rows if x['case']=='on']);z=(w['R']-o['R'])/math.sqrt(w['sigma']**2+o['sigma']**2); result=dict(rows=rows,off=o,on=w,z=z,fom_ratio=w['FOM']/o['FOM']);(a.out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

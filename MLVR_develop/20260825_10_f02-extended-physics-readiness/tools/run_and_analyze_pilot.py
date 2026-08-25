#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,math,re,subprocess
from pathlib import Path
R=re.compile(r'^\s*(?:(?P<cell>\d+)\s+)?(?P<g>\d+)\s+(?P<e>[+\-0-9.Ee]+)\s+(?P<v>[+\-0-9.Ee]+)\s+(?P<re>[+\-0-9.Ee]+)\s*$')
S=re.compile(r'Source Number\s*:\s*(\d+)\.')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tally(p,g):
 for l in p.read_text(errors='replace').splitlines():
  m=R.match(l)
  if m and int(m['g'])==g:return float(m['v']),float(m['re'])
 raise RuntimeError(f'no tally group {g} in {p}')
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--exe',type=Path,required=True);z=a.parse_args()
 m=json.loads((z.root/'manifest.json').read_text());rows=[];bad=[]
 for r in m['runs']:
  d=z.root/Path(r['input']).parent
  x=subprocess.run([str(z.exe),'inp'],cwd=d,capture_output=True,text=True)
  (d/'stdout.log').write_text(x.stdout);(d/'stderr.log').write_text(x.stderr);(d/'exit_code.txt').write_text(str(x.returncode)+'\n')
  sm=S.findall(x.stdout);src=int(sm[-1]) if sm else -1
  try:v,re=tally(d/'inp.Tally',r['response_tally_group'])
  except Exception as e:v=re=float('nan');bad.append(str(e))
  an=[l for l in (x.stdout+'\n'+x.stderr).splitlines() if re_search(l)]
  ok=x.returncode==0 and src==r['population'] and math.isfinite(v) and v>0 and math.isfinite(re) and re>=0 and not an
  rows.append({**r,'exit_code':x.returncode,'sources':src,'value':v,'re':re,'anomaly_count':len(an),'ok':ok,'stdout_sha256':h(d/'stdout.log')})
  if not ok:bad.append(f'{r["case"]}/{r["mode"]}: exit={x.returncode} src={src} value={v} re={re} anomalies={an}')
 (z.root/'pilot_results.json').write_text(json.dumps({'rows':rows,'failures':bad},indent=2)+'\n')
 print(json.dumps({'run_count':len(rows),'failure_count':len(bad),'failures':bad},indent=2));raise SystemExit(1 if bad else 0)
def re_search(l):
 return bool(re.search(r'error:|segmentation|nan|inf|signal',l,re.I))
if __name__=='__main__':main()

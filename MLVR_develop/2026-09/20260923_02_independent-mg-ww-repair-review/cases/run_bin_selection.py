#!/usr/bin/env python3
from pathlib import Path
import subprocess, re, json, argparse
p=argparse.ArgumentParser(); p.add_argument('--exe',type=Path,required=True); p.add_argument('--case-dir',type=Path,required=True); a=p.parse_args()
records=[]
for mode in ('mg-forward','mg-adjoint','ce-forward'):
 for energy in (.01,.2,1.0):
  d=a.case_dir/f'{mode}-E{energy:g}'; d.mkdir(parents=True,exist_ok=True)
  subprocess.run([str(Path(__file__).with_name('make_bin_selection_case.py')),'--mode',mode,'--energy',str(energy),'--out',str(d/'inp')],check=True)
  r=subprocess.run([str(a.exe)],cwd=d,text=True,capture_output=True)
  (d/'stdout.log').write_text(r.stdout); (d/'stderr.log').write_text(r.stderr)
  ptrac=(d/'inp.PTRAC').read_text(errors='replace') if (d/'inp.PTRAC').exists() else ''
  records.append({'mode':mode,'energy_MeV':energy,'returncode':r.returncode,
   'split':ptrac.count('Neutron: Bank_from_Weight_Splitting'),
   'roulette':ptrac.count('Neutron: Weight_Cut_off'),
   'warning':len(re.findall('Warning:',r.stdout)),
   'ptrac_lines':len(ptrac.splitlines())})
(a.case_dir/'bin-selection-results.json').write_text(json.dumps(records,indent=2)+'\n')
print('| mode | source E (MeV) | rc | split | roulette | warnings | PTRAC lines |')
print('|---|---:|---:|---:|---:|---:|---:|')
for x in records: print(f"| {x['mode']} | {x['energy_MeV']:.2g} | {x['returncode']} | {x['split']} | {x['roulette']} | {x['warning']} | {x['ptrac_lines']} |")

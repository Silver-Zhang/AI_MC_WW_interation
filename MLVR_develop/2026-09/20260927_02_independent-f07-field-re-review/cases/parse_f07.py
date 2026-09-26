#!/usr/bin/env python3
import re,json,sys,math
from pathlib import Path
# parses type-1 mesh tally #1 first spatial cell, outputs every energy row and total
p=Path(sys.argv[1]); lines=p.read_text().splitlines(); in_tally=False; rows=[]; current_mesh=None
for line in lines:
 if '--------- ID = 1,' in line: in_tally=True; continue
 if in_tally and '--------- ID = 2,' in line: break
 if not in_tally: continue
 m=re.match(r'^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)',line)
 if m:
  x,y,z,g,e,v,re_=m.groups(); current_mesh=(int(x),int(y),int(z)); rows.append(dict(mesh=current_mesh,group=int(g),energy=float(e),value=float(v),re=float(re_))); continue
 m=re.match(r'^\s+(\d+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)\s+([0-9.E+-]+)',line)
 if m and current_mesh:
  g,e,v,re_=m.groups(); rows.append(dict(mesh=current_mesh,group=int(g),energy=float(e),value=float(v),re=float(re_)))
print(json.dumps(rows))

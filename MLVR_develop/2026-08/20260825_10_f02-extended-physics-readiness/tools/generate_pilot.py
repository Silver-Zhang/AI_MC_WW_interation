#!/usr/bin/env python3
"""Generate frozen pilot only; does not establish formal acceptance."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CASES=(
 ('nnubar2_pure','10001.01m 1.0',6,3.8e-7,1,5.68,101,103),
 ('nnubar1_pure','10005.01m 1.0',6,3.8e-7,1,5.68,107,109),
 ('mixed_nnubar2_nonfissile','10001.01m 0.7\n    10006.01m 0.3',6,3.8e-7,1,5.68,113,127),
)
T='''UNIVERSE 0
CELL 1 -1 MAT=1
CELL 2 1 MAT=0 VOID=1

SURFACE
SURF 1 SO 2.0

MATERIAL
MAT 1 1.0
    {material}
MGACE ERGGRP=7

FIXEDSOURCE
PARTICLE POPULATION={population}
RNG TYPE=2 SEED={seed} STRIDE=1000000
{adjoint}
EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 CELL=1 WEIGHT=1 ENERGY={energy:.12g}

TALLY
CELLTALLY 1 TYPE=1 ESTIMATOR=1 PARTICLE=1 CELL=1 ENERGY=-1
'''
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
 out=ROOT/'cases/pilot'; pop=20000; runs=[]
 for name,mat,fg,fe,rg,re,fs,as_ in CASES:
  for mode,seed,energy,sgrp,rgrp in [('forward',fs,fe,fg,rg),('adjoint',as_,re,rg,fg)]:
   d=out/name/mode;d.mkdir(parents=True,exist_ok=True)
   adj='ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=5.68 5.68\n' if mode=='adjoint' else ''
   text=T.format(material=mat,population=pop,seed=seed,adjoint=adj,energy=energy)
   (d/'inp').write_text(text)
   runs.append({'case':name,'mode':mode,'seed':seed,'population':pop,'source_group':sgrp,'response_group':rgrp,'response_tally_group':8-rgrp,'material':mat,'input':str((d/'inp').relative_to(out)),'input_sha256':sha(text.encode())})
 m={'stage':'pilot','purpose':'syntax/readback/stability only; never formal acceptance','population':pop,'rng_type':2,'stride':1000000,'runs':runs}
 p=out/'manifest.json';p.write_text(json.dumps(m,indent=2)+'\n');print(f'manifest={p} sha256={sha(p.read_bytes())} runs={len(runs)}')
if __name__=='__main__':main()

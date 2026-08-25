#!/usr/bin/env python3
"""Read-only feasibility inventory for F02 extended readiness validation."""
from __future__ import annotations
import csv, hashlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '20260825_01_f02-adjoint-numerical-verification' / 'cases' / 'v4_reciprocity'))
from screen_mgace_pairs import xsdir_entries, read_ascii_mgace

def h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    root=Path('/home/workspace/AI_MC_WW_interation')
    xsdir=Path('/home/silver/NucXS_Library/RMC_DATA/xsdir')
    ent=xsdir_entries(xsdir)
    rows=[]
    for zaid in sorted(k for k in ent if k.endswith('.01M')):
        p,a=ent[zaid]; t=read_ascii_mgace(zaid,p,a)
        rows.append({'zaid':zaid,'file':str(p),'address':a,'sha256':h(p),'ngrp':t.groups,'nleg':t.nxs[2],'isang':t.nxs[8],'nnubar':t.nubar_count,'fissile':int(t.jxs[2]!=0 and t.jxs[4]!=0),'p0_locator':t.jxs[12]})
    out=root/'MLVR_develop/20260825_10_f02-extended-physics-readiness/logs/deployed_mgace_inventory.csv'
    with out.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader();w.writerows(rows)
    print(f'xsdir={xsdir} sha256={h(xsdir)}')
    print(f'tables={len(rows)}')
    for r in rows: print(','.join(f'{k}={v}' for k,v in r.items()))
    # Explicit mandatory-dimension conclusion; no implicit substitution.
    matrix=[
      ('nonfission asymmetric scatter, two deployed materials','available','mgxsnp H/O prior parser/generator'),
      ('two-region material interface and vacuum outer boundary','available','CELL/SURF input supported by existing F02 tasks'),
      ('three density ratios as cell densities','available','W5 input pattern'),
      ('position-dependent density mesh','not demonstrated','RMC source supports DENS=<negative mesh id>, but no task-owned HDF5 mesh writer or known runnable test input was located'),
      ('mixed composition regions','available','RMC MATERIAL allows multiple nuclides and distinct MAT IDs; requires task generator'),
      ('NNUBAR=1 fissile deployed table','available','10005.01m'),
      ('NNUBAR>1 fissile deployed table','available','10001.01m through 10004.01m'),
      ('three fission-dominated pairs per independent fissile material','not demonstrated','requires screening and pilot; not frozen yet'),
      ('strong P1/P2 directional source-response','not demonstrated','deployed NLEG inventory and existing task harness provide no prevalidated direction-resolved fixed-source adjoint response generator'),
      ('forward/backward angular distributions','not demonstrated','no readback oracle for conditional angular P1/P2 path available'),
      ('serial runtime','available','current isolated build'),
      ('OpenMP/MPI runtime','unavailable','current isolated build cache has no enabled MPI/OMP options'),
      ('Windows','unavailable','no environment')]
    f=root/'MLVR_develop/20260825_10_f02-extended-physics-readiness/logs/coverage_feasibility.csv'
    with f.open('w',newline='') as o:
      w=csv.writer(o);w.writerow(['dimension','status','evidence']);w.writerows(matrix)
    for r in matrix: print('MATRIX|'+ '|'.join(r))
if __name__=='__main__':main()

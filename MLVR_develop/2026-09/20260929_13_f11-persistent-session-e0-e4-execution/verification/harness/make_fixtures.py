#!/usr/bin/env python3
from pathlib import Path
import json, hashlib
TASK=Path(__file__).resolve().parents[2]
OUT=TASK/'verification/fixtures'
DATA=Path('/home/silver/NucXS_Library/RMC_DATA')
lines=(DATA/'multigroup/mgxsnp').read_text().splitlines()
assert lines[0].split()[0]=='1001.50m'
xss=list(map(float,' '.join(lines[12:]).split()[:3249]))
# Only fixture generation uses this disk data. E4 independently extracts actual loaded memory.
centres=list(reversed(xss[:30]));widths=list(reversed(xss[30:60]))
lowers=[c-w/2 for c,w in zip(centres,widths)]
edges=lowers+[centres[-1]+widths[-1]/2]
assert all(a<b for a,b in zip(edges,edges[1:])) and len(edges)==31
cases={
'E0_F':(20000,10001,0,5,1,0),'E0_A':(20000,10001,1,5,1,0),
'E1_F1':(2000,11001,0,5,1,0),'E1_F2':(3000,11003,0,5,1,0),
'E2_F1':(3000,12001,0,5,1,0),'E2_A':(3000,12003,1,5,1,0),'E2_F2':(3000,12005,0,5,1,0),
'E3_WW1':(3000,13001,0,5,1,0),'E3_WW2':(3000,13003,0,5,2,0),
'E4_S1':(1500,14001,0,5,1,1),'E4_S2':(3500,14003,0,15,1,1)}
fmt=lambda seq:' '.join(format(x,'.17g') for x in seq)
manifest={}
for rid,(n,seed,adj,x,ww,check) in cases.items():
    text='''UNIVERSE 0
CELL 1 1&-2&21&-22&23&-24 MAT=1 IMP:N=1
CELL 2 -1:2:-21:22:-23:24 MAT=0 VOID=1 IMP:N=0

SURFACE
SURF 1 PX 0
SURF 2 PX 20
SURF 21 PY -50
SURF 22 PY 50
SURF 23 PZ -50
SURF 24 PZ 50

MATERIAL
MAT 1 -1.0
 1001.50M 2
 8016.50M 1
MGACE ERGGRP=30 12

FIXEDSOURCE
'''
    text+=f'PARTICLE POPULATION={n}\nRNG TYPE=2 SEED={seed} STRIDE=1000000\n'
    if adj:text+='ADJOINT ADJOINTCALCULATION=1 MaxAdjointEnergy=30 30\n'
    text+=f'\nEXTERNALSOURCE\nSOURCE 1 FRACTION=1 PARTICLE=1 POINT={x} 0 0 WEIGHT=1 ENERGY=2\n\n'
    bounds=[2.**(-1-i-g%2)/(4 if ww==2 else 1) for i in range(2) for g in range(30)]
    text+='WEIGHTWINDOW\nWWMESH:N '+fmt(bounds)+'\nWWE:N '+fmt(edges[1:-1])+'\nWWP:N 5 3 5\n'
    text+='WEIGHTWINDOWMESH SCOPEX=2 BOUNDX=0 20 SCOPEY=1 BOUNDY=-50 50 SCOPEZ=1 BOUNDZ=-50 50\n\n'
    text+=f'TALLY\nSCHECK {check}\nMESHTALLY 1 TYPE=1 PARTICLE=1 ENERGY=-1 NORMALIZE=1 CHECK={check} SCOPEX=2 BOUNDX=0 20 SCOPEY=1 BOUNDY=-50 50 SCOPEZ=1 BOUNDZ=-50 50\n'
    p=OUT/(rid+'.inp');p.write_text(text)
    manifest[rid]={'population':n,'seed':seed,'adjoint':bool(adj),'source_x':x,'ww':ww,'scheck':check,'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sequence_row':f'{rid} {n} {seed} {adj} {x} {ww}'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(OUT/'disk_edges_for_input_only.json').write_text(json.dumps({'edges_MeV':edges,'purpose':'fixture WWE generation only; not E4 memory evidence'},indent=2)+'\n')
print('Generated',len(cases),'frozen fixtures; 2 spatial x 30 energy bins; stride 1000000.')

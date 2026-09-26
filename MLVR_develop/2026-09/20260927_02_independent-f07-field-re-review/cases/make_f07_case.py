#!/usr/bin/env python3
from pathlib import Path
from argparse import ArgumentParser
p=ArgumentParser(); p.add_argument('--mode',choices=('forward','adjoint'),default='forward'); p.add_argument('--ww',action='store_true'); p.add_argument('--seed',type=int,required=True); p.add_argument('--nps',type=int,required=True); p.add_argument('--out',type=Path,required=True); p.add_argument('--ptrac',action='store_true'); a=p.parse_args()
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
PARTICLE POPULATION=NPS_TOKEN
RNG TYPE=2 SEED=SEED_TOKEN STRIDE=100000
'''.replace('NPS_TOKEN',str(a.nps)).replace('SEED_TOKEN',str(a.seed))
if a.mode=='adjoint': text+='ADJOINT ADJOINTCALCULATION=1 MaxAdjointEnergy=30 30\n'
text+='''
EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 POINT=15 0 0 WEIGHT=1 ENERGY=2

'''
if a.ww:
 text+='''WEIGHTWINDOW
WWMESH:N 0.5 0.25 0.125 0.0625 0.03125 0.015625 0.0078125 0.00390625 0.001953125 0.0009765625
WWP:N 5 3 5
WEIGHTWINDOWMESH SCOPEX=10 BOUNDX=0 20 SCOPEY=1 BOUNDY=-50 50 SCOPEZ=1 BOUNDZ=-50 50

'''
text+='''TALLY
MESHTALLY 1 TYPE=1 PARTICLE=1 ENERGY=-1 NORMALIZE=0 SCOPEX=1 BOUNDX=0 20 SCOPEY=1 BOUNDY=-50 50 SCOPEZ=1 BOUNDZ=-50 50
MESHTALLY 2 TYPE=1 PARTICLE=1 ENERGY=-1 NORMALIZE=1 SCOPEX=1 BOUNDX=0 20 SCOPEY=1 BOUNDY=-50 50 SCOPEZ=1 BOUNDZ=-50 50
MESHTALLY 3 TYPE=1 PARTICLE=1 ENERGY=-1 NORMALIZE=1 SCOPEX=1 BOUNDX=30 40 SCOPEY=1 BOUNDY=-50 50 SCOPEZ=1 BOUNDZ=-50 50
'''

if a.ptrac: text += '\nPTRAC NEU=1 SRC=1 BNK=1 TER=1 MAX=100000 MEPH=100 FILE=0 WRITE=0\n'
a.out.write_text(text)

#!/usr/bin/env python3
from pathlib import Path
from argparse import ArgumentParser
p=ArgumentParser();p.add_argument('--mode',choices=('forward','adjoint'),required=True);p.add_argument('--population',type=int,default=500000);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
text='''UNIVERSE 0
CELL 1 1&-2&21&-22&23&-24 MAT=1 IMP:N=1
CELL 2 2:-1:22:-23:24 MAT=0 VOID=1 IMP:N=0

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
PARTICLE POPULATION=POP_TOKEN
'''.replace('POP_TOKEN',str(a.population))
if a.mode=='adjoint': text+='ADJOINT ADJOINTCALCULATION=1 MaxAdjointEnergy=30 30\n'
text+='''
EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 POINT=15 0 0 WEIGHT=1 ENERGY=2

TALLY
MESHTALLY 1 TYPE=1 PARTICLE=1 ENERGY=-1 NORMALIZE=0 HDF5MESH=1 SCOPEX=1 1 BOUNDX=0 5 20 SCOPEY=1 BOUNDY=-50 50 SCOPEZ=1 BOUNDZ=-50 50
MESHTALLY 2 TYPE=1 PARTICLE=1 ENERGY=-1 NORMALIZE=1 SCOPEX=1 1 BOUNDX=0 5 20 SCOPEY=1 BOUNDY=-50 50 SCOPEZ=1 BOUNDZ=-50 50
'''
a.out.write_text(text)

#!/usr/bin/env python3
"""Generate independent WW bin-selection cases; never writes RMC sources."""
from pathlib import Path
from argparse import ArgumentParser
p=ArgumentParser()
p.add_argument('--energy',type=float,required=True)
p.add_argument('--mode',choices=('mg-forward','mg-adjoint','ce-forward'),required=True)
p.add_argument('--seed',type=int,default=101)
p.add_argument('--population',type=int,default=1000)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(); mg=a.mode.startswith('mg-'); adj=a.mode=='mg-adjoint'
# Uses the known-valid fixed-source-adjoint nested-sphere grammar, retaining water as medium.
text='''UNIVERSE 0
CELL 1 -1  MAT=0 VOID=0
CELL 2 1&-2 MAT=1
CELL 3 2&-3 MAT=0 VOID=0
CELL 4 3 MAT=0 VOID=1

SURFACE
SURF 1 SO 20
SURF 2 SO 30
SURF 3 SO 50

MATERIAL
MAT 1 -1.0
    1001.50M 2.0
    8016.50M 1.0
'''
if mg: text+='MGACE ERGGRP=30 12\n'
else: text=text.replace('1001.50M','1001.60c').replace('8016.50M','8016.60c')
text+='\n'
text+=f'''FIXEDSOURCE
PARTICLE POPULATION={a.population}
'''
if adj: text+='ADJOINT ADJOINTCALCULATION=1 MaxAdjointEnergy=30 30\n'
text+='\n'
text+=f'''EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 POINT=0 0 0 WEIGHT=1 ENERGY={a.energy}
\nWEIGHTWINDOW
WWE:N 0.1 0.5
WWMESH:N 0.1 1.0 5.0
WWP:N 5 3 5
WEIGHTWINDOWMESH SCOPEX=1 BOUNDX=-50 50 SCOPEY=1 BOUNDY=-50 50 SCOPEZ=1 BOUNDZ=-50 50
\nPTRAC NEU=1 SRC=1 BNK=1 TER=1 MAX=100000 MEPH=100 FILE=0 WRITE=0
\nTALLY
CELLTALLY 1 TYPE=1 PARTICLE=1 CELL=1 ENERGY=-1
'''
a.out.write_text(text)

#!/usr/bin/env python3
"""Independent 100-cm-water, MG-adjoint, native-WW regression input generator."""
from pathlib import Path
from argparse import ArgumentParser
p=ArgumentParser(); p.add_argument('--case',choices=('off','on'),required=True); p.add_argument('--seed',type=int,required=True); p.add_argument('--population',type=int,required=True); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
text='''UNIVERSE 0
CELL 1 1&-2&21&-22&23&-24 MAT=1 IMP:N=1
CELL 2 2&-3&21&-22&23&-24 MAT=1 IMP:N=1
CELL 3 3&-4&21&-22&23&-24 MAT=1 IMP:N=1
CELL 4 4&-5&21&-22&23&-24 MAT=1 IMP:N=1
CELL 5 5&-6&21&-22&23&-24 MAT=1 IMP:N=1
CELL 6 6&-7&21&-22&23&-24 MAT=1 IMP:N=1
CELL 7 7&-8&21&-22&23&-24 MAT=1 IMP:N=1
CELL 8 8&-9&21&-22&23&-24 MAT=1 IMP:N=1
CELL 9 9&-10&21&-22&23&-24 MAT=1 IMP:N=1
CELL 10 10&-11&21&-22&23&-24 MAT=1 IMP:N=1
CELL 21 -1:-21:22:-23:24 MAT=0 VOID=1 IMP:N=0
CELL 22 11:-21:22:-23:24 MAT=0 VOID=1 IMP:N=0

SURFACE
SURF 1 PX 0
SURF 2 PX 10
SURF 3 PX 20
SURF 4 PX 30
SURF 5 PX 40
SURF 6 PX 50
SURF 7 PX 60
SURF 8 PX 70
SURF 9 PX 80
SURF 10 PX 90
SURF 11 PX 100
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
ADJOINT ADJOINTCALCULATION=1 MaxAdjointEnergy=30 30

EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 POINT=97.5 0 0 WEIGHT=1 ENERGY=2

'''.replace('POP_TOKEN',str(a.population))
if a.case=='on':
  spatial='0.0009765625 0.001953125 0.00390625 0.0078125 0.015625 0.03125 0.0625 0.125 0.25 0.5'
  # two explicit physical-energy bins [0,1] and [1, infinity]; same spatial WW in both.
  text+=f'''WEIGHTWINDOW
WWE:N 1
WWMESH:N {spatial} {spatial}
WWP:N 5 3 5
WEIGHTWINDOWMESH SCOPEX=10 BOUNDX=0 100 SCOPEY=1 BOUNDY=-50 50 SCOPEZ=1 BOUNDZ=-50 50

'''
text+='''TALLY
CELLTALLY 1 TYPE=1 PARTICLE=1 CELL=1 ENERGY=-1
'''
a.out.write_text(text)

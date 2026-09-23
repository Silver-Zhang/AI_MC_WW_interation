#!/usr/bin/env python3
"""Create paired F04-B RMC input files without changing RMC sources."""
from pathlib import Path
import argparse

p = argparse.ArgumentParser()
p.add_argument('--case', choices=('analog', 'ww'), required=True)
p.add_argument('--seed', type=int, required=True)
p.add_argument('--population', type=int, required=True)
p.add_argument('--ptrac', action='store_true')
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
root = Path(__file__).parent
text = (root / 'base.inp').read_text()
text = text.replace('POPULATION_TOKEN', str(a.population)).replace('SEED_TOKEN', str(a.seed))
if a.case == 'ww':
    text += (root / 'ww.block').read_text()
if a.ptrac:
    text += '\nPTRAC NEU=1 SRC=1 BNK=1 TER=1 MAX=100000 MEPH=100 FILE=1 WRITE=0\n'
a.out.write_text(text)

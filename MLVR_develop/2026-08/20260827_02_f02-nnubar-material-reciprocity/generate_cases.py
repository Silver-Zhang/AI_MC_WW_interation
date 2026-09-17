#!/usr/bin/env python3
"""Generate predeclared NNUBAR/material forward-adjoint reciprocity cases."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

GROUP_COUNT = 7
SOURCE_GROUP = 4
SOURCE_ENERGY_MEV = 2.985e-5
RESPONSE_GROUP = 1
RESPONSE_ENERGY_MEV = 5.68
PILOT_STREAMS = ((1009, 1013),)
FORMAL_STREAMS = ((2003, 2011), (2017, 2027), (2029, 2039), (2053, 2063), (2069, 2081))
CASES = (
    ("nnubar1_pure", "10005.01m 1.0", "pure deployed NNUBAR=1 fissile material"),
    ("mixed_nnubar1_nnubar2", "10005.01m 0.9999\n    10001.01m 0.0001", "mixed deployed NNUBAR=1 and NNUBAR=2 fissile material, with NNUBAR=1 g4 fission dominant"),
)
INPUT = """UNIVERSE 0
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
"""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("pilot", "formal"), required=True)
    parser.add_argument("--population", type=int, required=True)
    args = parser.parse_args()
    if args.population <= 100:
        raise ValueError("population must exceed 100")
    root = args.root.resolve()
    if root.exists():
        raise FileExistsError(root)
    streams = PILOT_STREAMS if args.stage == "pilot" else FORMAL_STREAMS
    runs: list[dict[str, object]] = []
    for case, material, description in CASES:
        for pair_index, (forward_seed, adjoint_seed) in enumerate(streams, 1):
            for mode, seed, energy, response_group, adjoint in (
                ("forward", forward_seed, SOURCE_ENERGY_MEV, RESPONSE_GROUP, ""),
                ("adjoint", adjoint_seed, RESPONSE_ENERGY_MEV, SOURCE_GROUP, "ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=5.68 5.68\n"),
            ):
                directory = root / case / f"pair_{pair_index}" / mode
                directory.mkdir(parents=True)
                content = INPUT.format(material=material, population=args.population, seed=seed, energy=energy, adjoint=adjoint)
                input_path = directory / "inp"
                input_path.write_text(content, encoding="ascii")
                runs.append({
                    "case": case,
                    "case_description": description,
                    "pair_index": pair_index,
                    "mode": mode,
                    "seed": seed,
                    "source_ace_group": SOURCE_GROUP if mode == "forward" else RESPONSE_GROUP,
                    "response_ace_group": response_group,
                    "source_energy_MeV": energy,
                    "response_tally_group": GROUP_COUNT - response_group + 1,
                    "material_density_atoms_per_barn_cm": 1.0,
                    "material": material,
                    "input": str(input_path.relative_to(root)),
                    "input_sha256": digest(content.encode("ascii")),
                })
    manifest = {
        "stage": args.stage,
        "population_per_run": args.population,
        "rng_type": 2,
        "rng_stride": 1000000,
        "geometry": "2 cm vacuum sphere, uniform cell source and identical-cell scalar track-length response",
        "energy_pair": "10005 maximum screened fission transfer g4->g1; source/response swapped for adjoint",
        "cases": [{"name": n, "material": m, "description": d} for n, m, d in CASES],
        "runs": runs,
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"stage={args.stage} generated_runs={len(runs)} population={args.population}")
    print(f"manifest_sha256={digest(manifest_path.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

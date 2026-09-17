#!/usr/bin/env python3
"""Generate frozen forward/adjoint reciprocity pairs for deployed 30-group H2O."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PAIRS = (
    {
        "name": "g14_to_g15",
        "forward_source_group": 14,
        "forward_source_energy": 0.4015,
        "forward_response_group": 15,
        "forward_response_energy": 0.2435,
        "mixture_sigma_forward": 5.29552,
        "mixture_sigma_reverse": 0.0,
    },
    {
        "name": "g20_to_g22",
        "forward_source_group": 20,
        "forward_source_energy": 0.0022925,
        "forward_response_group": 22,
        "forward_response_energy": 0.0003105,
        "mixture_sigma_forward": 5.9404,
        "mixture_sigma_reverse": 0.0,
    },
)
SEEDS = (1, 3, 5, 7, 9)
GROUP_COUNT = 30


INPUT = """UNIVERSE 0
CELL 1 -1 MAT=1 DENS=0.1004476876
CELL 2 1 MAT=0 VOID=1

SURFACE
SURF 1 SO 5.0

MATERIAL
MAT 1 0.1004476876
    1001.50m 2.0
    8016.50m 1.0
MGACE ERGGRP=30 12

FIXEDSOURCE
PARTICLE POPULATION={population}
RNG TYPE=2 SEED={seed} STRIDE=1000000
{adjoint_card}
EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 CELL=1 WEIGHT=1 ENERGY={source_energy:.12g}

TALLY
CELLTALLY 1 TYPE=1 ESTIMATOR=1 PARTICLE=1 CELL=1 ENERGY=-1
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--population", type=int, default=200_000)
    arguments = parser.parse_args()
    if arguments.population <= 100:
        raise ValueError("RMC fixed-source population must exceed 100")

    manifest: dict[str, object] = {
        "population_per_run": arguments.population,
        "rng_type": 2,
        "rng_stride": 1_000_000,
        "seeds": list(SEEDS),
        "group_count": GROUP_COUNT,
        "geometry": "uniform isotropic cell source and integral track-length response in the same 5 cm H2O sphere",
        "normalization": "unit source particle; identical source volume and response volume are exchanged only in energy",
        "pairs": list(PAIRS),
        "runs": [],
    }

    for pair in PAIRS:
        for seed in SEEDS:
            for mode in ("forward", "adjoint"):
                if mode == "forward":
                    source_group = int(pair["forward_source_group"])
                    response_group = int(pair["forward_response_group"])
                    source_energy = float(pair["forward_source_energy"])
                    response_energy = float(pair["forward_response_energy"])
                    adjoint_card = ""
                else:
                    source_group = int(pair["forward_response_group"])
                    response_group = int(pair["forward_source_group"])
                    source_energy = float(pair["forward_response_energy"])
                    response_energy = float(pair["forward_source_energy"])
                    adjoint_card = "ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=16 16\n"

                run_directory = arguments.root / str(pair["name"]) / f"seed_{seed}" / mode
                run_directory.mkdir(parents=True, exist_ok=True)
                content = INPUT.format(
                    population=arguments.population,
                    seed=seed,
                    adjoint_card=adjoint_card,
                    source_energy=source_energy,
                )
                input_path = run_directory / "inp"
                input_path.write_text(content, encoding="utf-8")
                manifest["runs"].append(
                    {
                        "pair": pair["name"],
                        "seed": seed,
                        "mode": mode,
                        "source_ace_group": source_group,
                        "source_energy_MeV": source_energy,
                        "response_ace_group": response_group,
                        "response_energy_MeV": response_energy,
                        "response_tally_group": GROUP_COUNT - response_group + 1,
                        "input": str(input_path.relative_to(arguments.root)),
                        "input_sha256": hashlib.sha256(content.encode()).hexdigest(),
                    }
                )

    manifest_path = arguments.root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"generated_runs={len(manifest['runs'])}")
    print(f"manifest={manifest_path}")
    print(f"manifest_sha256={hashlib.sha256(manifest_path.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

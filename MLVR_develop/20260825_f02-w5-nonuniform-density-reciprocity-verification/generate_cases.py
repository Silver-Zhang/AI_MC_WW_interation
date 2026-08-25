#!/usr/bin/env python3
"""Generate paired nonuniform-density forward/adjoint reciprocity cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


BASE_DENSITY = 0.1004476876
INNER_RADIUS_CM = 4.0
OUTER_RADIUS_CM = INNER_RADIUS_CM * math.pow(2.0, 1.0 / 3.0)
GROUP_COUNT = 30
DEFAULT_SEEDS = (1, 3, 5, 7, 9)

PAIRS = (
    {
        "name": "g14_to_g15",
        "forward_source_group": 14,
        "forward_source_energy_MeV": 0.4015,
        "forward_response_group": 15,
        "forward_response_energy_MeV": 0.2435,
    },
    {
        "name": "g20_to_g22",
        "forward_source_group": 20,
        "forward_source_energy_MeV": 0.0022925,
        "forward_response_group": 22,
        "forward_response_energy_MeV": 0.0003105,
    },
)

DENSITY_CASES = (
    {
        "name": "low_inner_high_outer",
        "inner_ratio": 0.5,
        "outer_ratio": 2.0,
    },
    {
        "name": "high_inner_low_outer",
        "inner_ratio": 2.0,
        "outer_ratio": 0.5,
    },
)

INPUT = """UNIVERSE 0
CELL 1 -1 MAT=1 DENS={inner_density:.10f}
CELL 2 1 & -2 MAT=1 DENS={outer_density:.10f}
CELL 3 2 MAT=0 VOID=1

SURFACE
SURF 1 SO {inner_radius:.15g}
SURF 2 SO {outer_radius:.15g}

MATERIAL
MAT 1 {base_density:.10f}
    1001.50m 2.0
    8016.50m 1.0
MGACE ERGGRP=30 12

FIXEDSOURCE
PARTICLE POPULATION={population}
RNG TYPE=2 SEED={seed} STRIDE=1000000
{adjoint_card}
EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 CELL={source_cell} WEIGHT=1 ENERGY={source_energy:.12g}

TALLY
CELLTALLY 1 TYPE=1 ESTIMATOR=1 PARTICLE=1 CELL={response_cell} ENERGY=-1
"""


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def parse_seeds(value: str) -> tuple[int, ...]:
    seeds = tuple(int(item) for item in value.split(","))
    if not seeds or len(set(seeds)) != len(seeds) or any(seed <= 0 for seed in seeds):
        raise argparse.ArgumentTypeError("seeds must be unique positive integers")
    return seeds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--population", type=int, default=200_000)
    parser.add_argument("--seeds", type=parse_seeds, default=DEFAULT_SEEDS)
    arguments = parser.parse_args()
    if arguments.population <= 100:
        raise ValueError("RMC fixed-source population must exceed 100")
    if (arguments.root / "manifest.json").exists():
        raise FileExistsError(f"refusing to overwrite {arguments.root / 'manifest.json'}")

    inner_volume = 4.0 * math.pi * INNER_RADIUS_CM**3 / 3.0
    outer_shell_volume = 4.0 * math.pi * (OUTER_RADIUS_CM**3 - INNER_RADIUS_CM**3) / 3.0
    manifest: dict[str, object] = {
        "population_per_run": arguments.population,
        "rng_type": 2,
        "rng_stride": 1_000_000,
        "seeds": list(arguments.seeds),
        "group_count": GROUP_COUNT,
        "base_atom_density": BASE_DENSITY,
        "geometry": {
            "inner_radius_cm": INNER_RADIUS_CM,
            "outer_radius_cm": OUTER_RADIUS_CM,
            "inner_volume_cm3": inner_volume,
            "outer_shell_volume_cm3": outer_shell_volume,
            "relative_volume_difference": abs(inner_volume - outer_shell_volume) / inner_volume,
        },
        "normalization": (
            "unit source uniformly sampled in one cell and integral track-length flux in the other; "
            "forward uses inner source/outer response, adjoint exchanges cells and energy groups; "
            "equal cell volumes make the raw response comparison volume-factor invariant"
        ),
        "density_cases": list(DENSITY_CASES),
        "pairs": list(PAIRS),
        "runs": [],
    }

    runs = manifest["runs"]
    assert isinstance(runs, list)
    for density_case in DENSITY_CASES:
        inner_density = BASE_DENSITY * float(density_case["inner_ratio"])
        outer_density = BASE_DENSITY * float(density_case["outer_ratio"])
        for pair in PAIRS:
            for seed in arguments.seeds:
                for mode in ("forward", "adjoint"):
                    if mode == "forward":
                        source_cell, response_cell = 1, 2
                        source_group = int(pair["forward_source_group"])
                        response_group = int(pair["forward_response_group"])
                        source_energy = float(pair["forward_source_energy_MeV"])
                        response_energy = float(pair["forward_response_energy_MeV"])
                        adjoint_card = ""
                    else:
                        source_cell, response_cell = 2, 1
                        source_group = int(pair["forward_response_group"])
                        response_group = int(pair["forward_source_group"])
                        source_energy = float(pair["forward_response_energy_MeV"])
                        response_energy = float(pair["forward_source_energy_MeV"])
                        adjoint_card = "ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=16 16\n"

                    run_directory = (
                        arguments.root
                        / str(density_case["name"])
                        / str(pair["name"])
                        / f"seed_{seed}"
                        / mode
                    )
                    run_directory.mkdir(parents=True, exist_ok=True)
                    content = INPUT.format(
                        inner_density=inner_density,
                        outer_density=outer_density,
                        inner_radius=INNER_RADIUS_CM,
                        outer_radius=OUTER_RADIUS_CM,
                        base_density=BASE_DENSITY,
                        population=arguments.population,
                        seed=seed,
                        adjoint_card=adjoint_card,
                        source_cell=source_cell,
                        response_cell=response_cell,
                        source_energy=source_energy,
                    )
                    input_path = run_directory / "inp"
                    input_path.write_text(content, encoding="ascii")
                    runs.append(
                        {
                            "density_case": density_case["name"],
                            "inner_density_ratio": density_case["inner_ratio"],
                            "outer_density_ratio": density_case["outer_ratio"],
                            "pair": pair["name"],
                            "seed": seed,
                            "mode": mode,
                            "source_cell": source_cell,
                            "response_cell": response_cell,
                            "source_ace_group": source_group,
                            "source_energy_MeV": source_energy,
                            "response_ace_group": response_group,
                            "response_energy_MeV": response_energy,
                            "response_tally_group": GROUP_COUNT - response_group + 1,
                            "input": str(input_path.relative_to(arguments.root)),
                            "input_sha256": sha256_bytes(content.encode("ascii")),
                        }
                    )

    manifest_path = arguments.root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"generated_runs={len(runs)}")
    print(f"inner_volume_cm3={inner_volume:.17g}")
    print(f"outer_shell_volume_cm3={outer_shell_volume:.17g}")
    print(f"relative_volume_difference={abs(inner_volume - outer_shell_volume) / inner_volume:.17g}")
    print(f"manifest={manifest_path}")
    print(f"manifest_sha256={sha256_bytes(manifest_path.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
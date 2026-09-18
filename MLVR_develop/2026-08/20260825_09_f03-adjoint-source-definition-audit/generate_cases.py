#!/usr/bin/env python3
"""Generate frozen F03 response-to-adjoint-source cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


BASE_DENSITY = 0.1004476876
INNER_RADIUS_CM = 4.0
MIDDLE_RADIUS_CM = INNER_RADIUS_CM * math.pow(2.0, 1.0 / 3.0)
OUTER_RADIUS_CM = INNER_RADIUS_CM * math.pow(3.0, 1.0 / 3.0)
GROUP_COUNT = 30
RNG_STRIDE = 1_000_000
DEFAULT_SEEDS = (1, 3, 5, 7, 9)
RESPONSE = (
    {
        "name": "cell2_g15",
        "cell": 2,
        "group": 15,
        "energy_MeV": 0.2435,
        "h": 0.7,
    },
    {
        "name": "cell3_g20",
        "cell": 3,
        "group": 20,
        "energy_MeV": 0.0022925,
        "h": 1.3,
    },
)

INPUT = """UNIVERSE 0
CELL 1 -1 MAT=1 DENS={density:.10f}
CELL 2 1 & -2 MAT=1 DENS={density:.10f}
CELL 3 2 & -3 MAT=1 DENS={density:.10f}
CELL 4 3 MAT=0 VOID=1

SURFACE
SURF 1 SO {inner_radius:.15g}
SURF 2 SO {middle_radius:.15g}
SURF 3 SO {outer_radius:.15g}

MATERIAL
MAT 1 {density:.10f}
    1001.50m 2.0
    8016.50m 1.0
MGACE ERGGRP=30 12

PRINT
SOURCE 1

FIXEDSOURCE
PARTICLE POPULATION={population}
RNG TYPE=2 SEED={seed} STRIDE={stride}
{adjoint_card}
EXTERNALSOURCE
{source_cards}

TALLY
CELLTALLY 1 TYPE=1 ESTIMATOR=1 PARTICLE=1 CELL=1 2 3 ENERGY=-1
"""


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def parse_seeds(value: str) -> tuple[int, ...]:
    seeds = tuple(int(item) for item in value.split(","))
    if not seeds or len(set(seeds)) != len(seeds) or any(seed <= 0 for seed in seeds):
        raise argparse.ArgumentTypeError("seeds must be unique positive integers")
    return seeds


def source_card(cell: int, energy: float, fraction: float, weight: float, bias: float | None) -> str:
    bias_card = "" if bias is None else f" BIASFRAC={bias:.12g}"
    return (
        f"SOURCE {cell} FRACTION={fraction:.12g} PARTICLE=1 CELL={cell} "
        f"WEIGHT={weight:.12g} ENERGY={energy:.12g}{bias_card}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--population", type=int, default=200_000)
    parser.add_argument("--seeds", type=parse_seeds, default=DEFAULT_SEEDS)
    arguments = parser.parse_args()
    if arguments.population <= 100:
        raise ValueError("RMC fixed-source population must exceed 100")
    if arguments.root.exists() and any(arguments.root.iterdir()):
        raise FileExistsError(f"refusing to write non-empty root {arguments.root}")

    volume = 4.0 * math.pi * INNER_RADIUS_CM**3 / 3.0
    components = []
    for item in RESPONSE:
        strength = float(item["h"]) * volume
        components.append({**item, "volume_cm3": volume, "strength_H": strength})
    total_strength = sum(float(item["strength_H"]) for item in components)
    cases = (
        {"name": "unbiased", "bias_values": (None, None)},
        {"name": "biased", "bias_values": (1.0, 9.0)},
    )
    manifest: dict[str, object] = {
        "population_per_run": arguments.population,
        "rng_type": 2,
        "rng_stride": RNG_STRIDE,
        "seeds": list(arguments.seeds),
        "group_count": GROUP_COUNT,
        "density_atom_cm3": BASE_DENSITY,
        "geometry": {
            "inner_radius_cm": INNER_RADIUS_CM,
            "middle_radius_cm": MIDDLE_RADIUS_CM,
            "outer_radius_cm": OUTER_RADIUS_CM,
            "cell_volume_cm3": volume,
            "relative_volume_difference": 0.0,
        },
        "measure": "cell-integrated track-length flux; MG group-integrated; isotropic scalar source",
        "response_components": components,
        "total_strength_H": total_strength,
        "mapping": "FRACTION=H_i, common WEIGHT=sum(H_i), biased sampling corrected by normalized FRACTION/BIASFRAC",
        "cases": [case["name"] for case in cases],
        "runs": [],
    }
    runs = manifest["runs"]
    assert isinstance(runs, list)
    for case in cases:
        for seed in arguments.seeds:
            for mode in ("forward", "adjoint"):
                if mode == "forward":
                    source_cards = source_card(1, 0.4015, 1.0, 1.0, None)
                    adjoint_card = ""
                    response_cells = (2, 3)
                    response_groups = (15, 20)
                    source_components = []
                else:
                    source_components = components
                    source_cards = "\n".join(
                        source_card(
                            int(item["cell"]),
                            float(item["energy_MeV"]),
                            float(item["strength_H"]),
                            total_strength,
                            bias,
                        )
                        for item, bias in zip(components, case["bias_values"])
                    )
                    adjoint_card = "ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=16 16\n"
                    response_cells = (1,)
                    response_groups = (14,)
                run_directory = arguments.root / case["name"] / f"seed_{seed}" / mode
                content = INPUT.format(
                    density=BASE_DENSITY,
                    inner_radius=INNER_RADIUS_CM,
                    middle_radius=MIDDLE_RADIUS_CM,
                    outer_radius=OUTER_RADIUS_CM,
                    population=arguments.population,
                    seed=seed,
                    stride=RNG_STRIDE,
                    adjoint_card=adjoint_card,
                    source_cards=source_cards,
                )
                input_path = run_directory / "inp"
                input_path.parent.mkdir(parents=True, exist_ok=True)
                input_path.write_text(content, encoding="ascii")
                runs.append(
                    {
                        "case": case["name"],
                        "seed": seed,
                        "mode": mode,
                        "input": str(input_path.relative_to(arguments.root)),
                        "input_sha256": sha256_bytes(content.encode("ascii")),
                        "source_components": source_components,
                        "response_cells": list(response_cells),
                        "response_groups": list(response_groups),
                        "response_tally_groups": [GROUP_COUNT - group + 1 for group in response_groups],
                    }
                )
    manifest_path = arguments.root / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"generated_runs={len(runs)}")
    print(f"cell_volume_cm3={volume:.17g}")
    print(f"total_strength_H={total_strength:.17g}")
    print(f"manifest={manifest_path}")
    print(f"manifest_sha256={sha256_bytes(manifest_path.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

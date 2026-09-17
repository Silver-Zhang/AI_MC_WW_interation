#!/usr/bin/env python3
"""Generate frozen C5G7 forward-adjoint fission reciprocity cases."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


GROUP_COUNT = 7
FORWARD_SOURCE_GROUP = 6
FORWARD_SOURCE_ENERGY = 3.8e-7
FORWARD_RESPONSE_GROUP = 1
FORWARD_RESPONSE_ENERGY = 5.68
FORMAL_STREAMS = tuple(zip((1, 3, 5, 7, 9), (11, 13, 15, 17, 19)))
PILOT_STREAMS = ((101, 103),)


INPUT = """UNIVERSE 0
CELL 1 -1 MAT=1
CELL 2 1 MAT=0 VOID=1

SURFACE
SURF 1 SO 2.0

MATERIAL
MAT 1 1.0
    10001.01m 1.0
MGACE ERGGRP=7

FIXEDSOURCE
PARTICLE POPULATION={population}
RNG TYPE=2 SEED={seed} STRIDE=1000000
{adjoint_card}
EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=1 CELL=1 WEIGHT=1 ENERGY={source_energy:.12g}

TALLY
CELLTALLY 1 TYPE=1 ESTIMATOR=1 PARTICLE=1 CELL=1 ENERGY=-1
"""


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--stage", choices=("pilot", "formal"), required=True)
    parser.add_argument("--population", type=int)
    arguments = parser.parse_args()

    default_population = 20_000 if arguments.stage == "pilot" else 1_000_000
    population = arguments.population or default_population
    if population <= 100:
        raise ValueError("RMC fixed-source population must exceed 100")
    streams = PILOT_STREAMS if arguments.stage == "pilot" else FORMAL_STREAMS

    manifest: dict[str, object] = {
        "stage": arguments.stage,
        "population_per_run": population,
        "rng_type": 2,
        "rng_stride": 1_000_000,
        "group_count": GROUP_COUNT,
        "geometry": "uniform isotropic cell source and integral track-length response in the same 2 cm sphere",
        "material": "10001.01m atom coefficient 1.0; MGACE ERGGRP=7",
        "normalization": "unit source particle; source and response occupy the identical cell, so only energy groups are exchanged",
        "forward_source_ace_group": FORWARD_SOURCE_GROUP,
        "forward_response_ace_group": FORWARD_RESPONSE_GROUP,
        "fission_operator_strength": 0.100120227799,
        "p0_scatter_forward": 0.0,
        "p0_scatter_reverse": 0.0,
        "runs": [],
    }

    for pair_index, (forward_seed, adjoint_seed) in enumerate(streams, 1):
        for mode, seed in (("forward", forward_seed), ("adjoint", adjoint_seed)):
            if mode == "forward":
                source_group = FORWARD_SOURCE_GROUP
                response_group = FORWARD_RESPONSE_GROUP
                source_energy = FORWARD_SOURCE_ENERGY
                response_energy = FORWARD_RESPONSE_ENERGY
                adjoint_card = ""
            else:
                source_group = FORWARD_RESPONSE_GROUP
                response_group = FORWARD_SOURCE_GROUP
                source_energy = FORWARD_RESPONSE_ENERGY
                response_energy = FORWARD_SOURCE_ENERGY
                adjoint_card = "ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=5.68 5.68\n"

            run_directory = arguments.root / f"pair_{pair_index}" / mode
            run_directory.mkdir(parents=True, exist_ok=True)
            content = INPUT.format(
                population=population,
                seed=seed,
                adjoint_card=adjoint_card,
                source_energy=source_energy,
            )
            input_path = run_directory / "inp"
            input_path.write_text(content, encoding="utf-8")
            manifest["runs"].append(
                {
                    "pair_index": pair_index,
                    "mode": mode,
                    "seed": seed,
                    "source_ace_group": source_group,
                    "source_energy_MeV": source_energy,
                    "response_ace_group": response_group,
                    "response_energy_MeV": response_energy,
                    "response_tally_group": GROUP_COUNT - response_group + 1,
                    "input": str(input_path.relative_to(arguments.root)),
                    "input_sha256": sha256_bytes(content.encode()),
                }
            )

    manifest_path = arguments.root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"stage={arguments.stage}")
    print(f"population_per_run={population}")
    print(f"generated_runs={len(manifest['runs'])}")
    print(f"manifest={manifest_path}")
    print(f"manifest_sha256={sha256_bytes(manifest_path.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
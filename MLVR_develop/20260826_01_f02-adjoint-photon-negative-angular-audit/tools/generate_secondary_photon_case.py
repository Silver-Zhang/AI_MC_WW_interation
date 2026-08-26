#!/usr/bin/env python3
"""Generate a mixed-mode adjoint photon case that forces a neutron secondary."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


INPUT = """UNIVERSE 0
CELL 1 -1 MAT=1 TMP=300
CELL 2 1 MAT=0 VOID=1

SURFACE
SURF 1 SO 5.0

MATERIAL
MAT 1 {density:.12g}
    {neutron_zaid} 1.0
MGACE ERGGRP={neutron_groups} {photon_groups}
MTLIB PLIB={plib}

PHYSICS
PARTICLEMODE N P

FIXEDSOURCE
PARTICLE POPULATION={population}
RNG TYPE=2 SEED={seed} STRIDE=1000000
ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=2 2

EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=2 CELL=1 POINT=0 0 0 WEIGHT=1 ENERGY={source_energy:.12g}

TALLY
CELLTALLY 1 TYPE=1 ESTIMATOR=1 PARTICLE=2 CELL=1 ENERGY=-1
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--population", type=int, default=400)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--density", type=float, default=1.0)
    parser.add_argument("--neutron-zaid", default="10006.91m")
    parser.add_argument("--plib", default="91g")
    parser.add_argument("--neutron-groups", type=int, default=1)
    parser.add_argument("--photon-groups", type=int, default=1)
    parser.add_argument("--source-energy", type=float, default=1.0)
    arguments = parser.parse_args()
    if arguments.population <= 100:
        raise ValueError("RMC fixed-source population must exceed 100")
    if arguments.density <= 0:
        raise ValueError("density must be positive")

    assets = arguments.assets.resolve()
    source_manifest_path = assets / "manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="ascii"))
    root = arguments.root.resolve()
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"refusing to overwrite {manifest_path}")
    root.mkdir(parents=True)
    input_path = root / "inp"
    input_path.write_text(
        INPUT.format(
            density=arguments.density,
            population=arguments.population,
            seed=arguments.seed,
            neutron_zaid=arguments.neutron_zaid,
            plib=arguments.plib,
            neutron_groups=arguments.neutron_groups,
            photon_groups=arguments.photon_groups,
            source_energy=arguments.source_energy,
        ),
        encoding="ascii",
    )
    manifest = {
        "case": "forced_adjoint_photon_to_neutron_secondary",
        "seed": arguments.seed,
        "population": arguments.population,
        "atom_density_1e24_per_cm3": arguments.density,
        "source_energy_MeV": arguments.source_energy,
        "input": "inp",
        "input_sha256": sha256(input_path),
        "data_index": str(assets),
        "source_manifest": str(source_manifest_path),
        "source_manifest_sha256": sha256(source_manifest_path),
        "xsdir_sha256": sha256(assets / "xsdir"),
        "expected_support": source_manifest["expected_support"],
        "expected_mean": source_manifest["angular_mean"],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"manifest={manifest_path}")
    print(f"manifest_sha256={sha256(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

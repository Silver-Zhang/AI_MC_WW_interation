#!/usr/bin/env python3
"""Generate forward/adjoint photon runs for the private one-group gamma MGACE."""

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
PARTICLEMODE P

FIXEDSOURCE
PARTICLE POPULATION={population}
RNG TYPE=2 SEED={seed} STRIDE=1000000
{adjoint_card}
EXTERNALSOURCE
SOURCE 1 FRACTION=1 PARTICLE=2 CELL=1 POINT=0 0 0 WEIGHT=1 ENERGY={source_energy:.12g}

PTRAC PHO=1 SRC=1 COL=1 SUR=1 MAX=500000 MEPH=1000 WRITE=1 CELL=1 2

TALLY
CELLTALLY 1 TYPE=1 ESTIMATOR=1 PARTICLE=2 CELL=1 ENERGY=-1
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--population", type=int, default=200)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--density", type=float, default=0.001)
    parser.add_argument("--neutron-zaid", default="10006.91m")
    parser.add_argument("--plib", default="91g")
    parser.add_argument("--neutron-groups", type=int, default=0)
    parser.add_argument("--photon-groups", type=int, default=1)
    parser.add_argument("--source-energy", type=float, default=1.0)
    arguments = parser.parse_args()
    if arguments.population <= 100:
        raise ValueError("RMC fixed-source population must exceed 100")
    if arguments.density <= 0.0:
        raise ValueError("density must be positive")

    assets = arguments.assets.resolve()
    source_manifest_path = assets / "manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="ascii"))
    root = arguments.root.resolve()
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"refusing to overwrite {manifest_path}")

    runs: list[dict[str, object]] = []
    for mode in ("forward", "adjoint"):
        run_directory = root / mode
        run_directory.mkdir(parents=True)
        adjoint_card = "ADJOINT ADJOINTCALCULATION=1 MAXADJOINTENERGY=2 2\n" if mode == "adjoint" else ""
        input_path = run_directory / "inp"
        input_path.write_text(
            INPUT.format(
                density=arguments.density,
                population=arguments.population,
                seed=arguments.seed,
                adjoint_card=adjoint_card,
                neutron_zaid=arguments.neutron_zaid,
                plib=arguments.plib,
                neutron_groups=arguments.neutron_groups,
                photon_groups=arguments.photon_groups,
                source_energy=arguments.source_energy,
            ),
            encoding="ascii",
        )
        runs.append(
            {
                "case": "photon_one_variable_negative",
                "mode": mode,
                "seed": arguments.seed,
                "population": arguments.population,
                "atom_density_1e24_per_cm3": arguments.density,
                "source_energy_MeV": arguments.source_energy,
                "input": str(input_path.relative_to(root)),
                "input_sha256": sha256(input_path),
                "data_index": str(assets),
                "xsdir_sha256": sha256(assets / "xsdir"),
            }
        )

    manifest = {
        "source_manifest": str(source_manifest_path),
        "source_manifest_sha256": sha256(source_manifest_path),
        "geometry": "5 cm sphere, pure one-group photon self scattering, point source at origin",
        "expected_support": source_manifest["expected_support"],
        "expected_mean": source_manifest["angular_mean"],
        "runs": runs,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"generated_runs={len(runs)}")
    print(f"manifest={manifest_path}")
    print(f"manifest_sha256={sha256(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

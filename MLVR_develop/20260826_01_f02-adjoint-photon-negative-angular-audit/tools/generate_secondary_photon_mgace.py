#!/usr/bin/env python3
"""Generate a private one-group neutron/photon MGACE with a photon secondary."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from generate_photon_mgace import electron_dependency, format_float_block, format_int_block


NEUTRON_ZAID = "10006.91m"
PHOTON_ZAID = "10000.91g"
ANGULAR_MEAN = -0.5


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def serialize(zaid: str, nxs: list[int], jxs: list[int], xss: list[float]) -> str:
    header = f"{zaid}   1.000000 0.00000E+00   private secondary photon qualification\n" + "\n" * 5
    return header + format_int_block(nxs) + format_int_block(jxs) + format_float_block(xss)


def neutron_table() -> tuple[str, dict[str, object]]:
    # One-based positions are recorded explicitly so the manifest can be audited.
    xss = [
        1.0, 2.0, 1.0, 0.0,       # LERG, LTOT, LABS
        2.0,                        # LIPT: photon
        15.0,                       # LERG2L: photon group structure
        17.0, 18.0,                 # LP0L: neutron, secondary photon
        0.0, 1.0,                   # LSANG2, LNLEG2
        19.0, 20.0,                 # LXPNL: neutron, secondary photon
        21.0, 22.0,                 # LPNL: neutron, secondary photon
        1.0, 1.0,                   # photon group count and center energy
        1.0, 1.0,                   # neutron and photon-production P0
        0.0, 1.0,                   # neutron isotropic, photon XPN offset
        0.0, ANGULAR_MEAN,          # neutron placeholder, photon PN value
    ]
    nxs = [0] * 16
    nxs[0] = len(xss)
    nxs[1] = 10006
    nxs[4:8] = [1, 1, 1, 1]  # NGRP, NUS, NDS, NSEC
    nxs[8] = 0                # primary neutron ISANG
    nxs[11] = 1               # incident neutron

    jxs = [0] * 32
    jxs[0] = 1
    jxs[1] = 3
    jxs[5] = 4
    jxs[10:17] = [5, 6, 7, 9, 10, 11, 13]
    metadata = {"zaid": NEUTRON_ZAID, "nxs": nxs, "jxs": jxs, "xss": xss}
    return serialize(NEUTRON_ZAID, nxs, jxs, xss), metadata


def photon_table() -> tuple[str, dict[str, object]]:
    # Zero gamma self-scattering forces every adjoint photon collision into the
    # transposed neutron-to-photon production path.
    xss = [1.0, 2.0, 1.0, 0.0, 6.0, 0.0, 9.0, 10.0, 1.0, ANGULAR_MEAN]
    nxs = [0] * 16
    nxs[0] = len(xss)
    nxs[1] = 1000
    nxs[2] = 1
    nxs[4:7] = [1, 1, 1]
    nxs[8] = 0
    nxs[11] = 2
    jxs = [0] * 32
    jxs[0] = 1
    jxs[1] = 3
    jxs[5] = 4
    jxs[12] = 5
    jxs[15] = 7
    jxs[16] = 8
    metadata = {"zaid": PHOTON_ZAID, "nxs": nxs, "jxs": jxs, "xss": xss}
    return serialize(PHOTON_ZAID, nxs, jxs, xss), metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--base-xsdir", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"refusing to overwrite {manifest_path}")

    data_root = root / "data"
    data_root.mkdir(parents=True)
    neutron_path = data_root / "secondary_neutron_mgace"
    photon_path = data_root / "secondary_photon_mgace"
    neutron_content, neutron = neutron_table()
    photon_content, photon = photon_table()
    neutron_path.write_text(neutron_content, encoding="ascii")
    photon_path.write_text(photon_content, encoding="ascii")

    electron_fields, electron_source = electron_dependency(arguments.base_xsdir.resolve())
    electron_private = data_root / "electron_03e"
    shutil.copyfile(electron_source, electron_private)
    electron_fields[2] = electron_private.name

    xsdir_path = root / "xsdir"
    xsdir_path.write_text(
        f"DATAPATH={data_root}\n"
        "atomic weight ratios\n  10006  1.000000\ndirectory\n"
        f"  {NEUTRON_ZAID}  1.000000 {neutron_path.name} 0 1 1 {len(neutron['xss'])} 0 0 0.00\n"
        f"  {PHOTON_ZAID}  1.000000 {photon_path.name} 0 1 1 {len(photon['xss'])} 0 0 0.00\n"
        f"  {' '.join(electron_fields)}\n",
        encoding="ascii",
    )
    manifest = {
        "purpose": "one-group adjoint photon to neutron secondary angular qualification",
        "angular_mean": ANGULAR_MEAN,
        "expected_support": [-1.0, 0.0],
        "tables": [
            {**neutron, "path": str(neutron_path.relative_to(root)), "sha256": sha256(neutron_path)},
            {**photon, "path": str(photon_path.relative_to(root)), "sha256": sha256(photon_path)},
        ],
        "xsdir": "xsdir",
        "xsdir_sha256": sha256(xsdir_path),
        "electron_dependency": {
            "source_path": str(electron_source),
            "source_sha256": sha256(electron_source),
            "private_path": str(electron_private.relative_to(root)),
            "private_sha256": sha256(electron_private),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"manifest={manifest_path}")
    print(f"manifest_sha256={sha256(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

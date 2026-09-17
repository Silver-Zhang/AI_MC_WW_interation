#!/usr/bin/env python3
"""Generate warning-free two-group photon angular qualification tables."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from generate_photon_mgace import electron_dependency, format_float_block, format_int_block


NEUTRON_ZAID = "10006.92m"
PHOTON_ZAID = "10000.92g"
ANGULAR_MEAN = -0.5
GROUP_STRUCTURE = [3.0, 1.0, 2.0, 2.0]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def serialize(zaid: str, nxs: list[int], jxs: list[int], xss: list[float], kind: str) -> str:
    header = f"{zaid}   1.000000 0.00000E+00   private two-group {kind} qualification\n" + "\n" * 5
    return header + format_int_block(nxs) + format_int_block(jxs) + format_float_block(xss)


def base_nxs(length: int, za: int, particle: int, nleg: int = 0, nsec: int = 0) -> list[int]:
    nxs = [0] * 16
    nxs[0] = length
    nxs[1] = za
    nxs[2] = nleg
    nxs[4] = 2
    nxs[7] = nsec
    nxs[8] = 0
    nxs[11] = particle
    return nxs


def ordinary_neutron() -> tuple[list[int], list[int], list[float]]:
    xss = [*GROUP_STRUCTURE, 1.0, 1.0, 0.0, 0.0, 10.0, 1.0, 1.0, 0.0]
    jxs = [0] * 32
    jxs[0], jxs[1], jxs[5], jxs[12], jxs[15] = 1, 5, 7, 9, 12
    return base_nxs(len(xss), 10006, 1), jxs, xss


def ordinary_photon() -> tuple[list[int], list[int], list[float]]:
    xss = [
        *GROUP_STRUCTURE,
        1.0, 1.0, 0.0, 0.0,
        10.0, 1.0, 1.0,
        14.0, 16.0,
        1.0, 2.0,
        ANGULAR_MEAN, ANGULAR_MEAN,
    ]
    jxs = [0] * 32
    jxs[0], jxs[1], jxs[5], jxs[12], jxs[15], jxs[16] = 1, 5, 7, 9, 12, 13
    return base_nxs(len(xss), 1000, 2, nleg=1), jxs, xss


def secondary_neutron() -> tuple[list[int], list[int], list[float]]:
    xss = [
        *GROUP_STRUCTURE,
        1.0, 1.0, 0.0, 0.0,
        2.0, 19.0,
        22.0, 24.0,
        0.0, 1.0,
        28.0, 30.0,
        0.0, 34.0,
        2.0, 3.0, 1.0,
        1.0, 1.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        ANGULAR_MEAN,
    ]
    jxs = [0] * 32
    jxs[0], jxs[1], jxs[5] = 1, 5, 7
    jxs[10:17] = [9, 10, 11, 13, 14, 15, 17]
    return base_nxs(len(xss), 10006, 1, nsec=1), jxs, xss


def secondary_photon() -> tuple[list[int], list[int], list[float]]:
    xss = [*GROUP_STRUCTURE, 1.0, 1.0, 0.0, 0.0, 10.0, 0.0, 0.0, 0.0]
    jxs = [0] * 32
    jxs[0], jxs[1], jxs[5], jxs[12], jxs[15] = 1, 5, 7, 9, 12
    return base_nxs(len(xss), 1000, 2), jxs, xss


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("ordinary", "secondary"), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--base-xsdir", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"refusing to overwrite {manifest_path}")

    if arguments.kind == "ordinary":
        neutron_data, photon_data = ordinary_neutron(), ordinary_photon()
    else:
        neutron_data, photon_data = secondary_neutron(), secondary_photon()

    data_root = root / "data"
    data_root.mkdir(parents=True)
    table_records = []
    for zaid, name, data in (
        (NEUTRON_ZAID, "two_group_neutron_mgace", neutron_data),
        (PHOTON_ZAID, "two_group_photon_mgace", photon_data),
    ):
        nxs, jxs, xss = data
        path = data_root / name
        path.write_text(serialize(zaid, nxs, jxs, xss, arguments.kind), encoding="ascii")
        table_records.append({"zaid": zaid, "path": str(path.relative_to(root)), "sha256": sha256(path),
                              "nxs": nxs, "jxs": jxs, "xss": xss})

    electron_fields, electron_source = electron_dependency(arguments.base_xsdir.resolve())
    electron_private = data_root / "electron_03e"
    shutil.copyfile(electron_source, electron_private)
    electron_fields[2] = electron_private.name
    xsdir_path = root / "xsdir"
    xsdir_path.write_text(
        f"DATAPATH={data_root}\natomic weight ratios\n  10006  1.000000\ndirectory\n"
        f"  {NEUTRON_ZAID} 1.000000 two_group_neutron_mgace 0 1 1 {len(neutron_data[2])} 0 0 0.00\n"
        f"  {PHOTON_ZAID} 1.000000 two_group_photon_mgace 0 1 1 {len(photon_data[2])} 0 0 0.00\n"
        f"  {' '.join(electron_fields)}\n",
        encoding="ascii",
    )
    manifest = {
        "purpose": f"warning-free two-group {arguments.kind} photon angular qualification",
        "kind": arguments.kind,
        "group_count": 2,
        "group_centers_MeV": [3.0, 1.0],
        "group_widths_MeV": [2.0, 2.0],
        "source_energy_MeV": 3.0,
        "angular_mean": ANGULAR_MEAN,
        "expected_support": [-1.0, 0.0],
        "tables": table_records,
        "xsdir": "xsdir",
        "xsdir_sha256": sha256(xsdir_path),
        "electron_dependency": {"source_sha256": sha256(electron_source), "private_sha256": sha256(electron_private)},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"kind={arguments.kind} manifest={manifest_path}")
    print(f"manifest_sha256={sha256(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

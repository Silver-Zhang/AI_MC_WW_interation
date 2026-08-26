#!/usr/bin/env python3
"""Generate private one-group neutron/gamma MGACE tables for photon angular validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


NEUTRON_ZAID = "10006.91m"
PHOTON_ZAID = "10000.91g"
ANGULAR_MEAN = -0.5


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def format_int_block(values: list[int]) -> str:
    return "".join(
        " ".join(f"{value:8d}" for value in values[index : index + 8]) + "\n"
        for index in range(0, len(values), 8)
    )


def format_float_block(values: list[float]) -> str:
    return "".join(
        " ".join(f"{value:15.8E}" for value in values[index : index + 4]) + "\n"
        for index in range(0, len(values), 4)
    )


def electron_dependency(xsdir_path: Path) -> tuple[list[str], Path]:
    lines = [line.strip() for line in xsdir_path.read_text(encoding="ascii").splitlines() if line.strip()]
    data_line = next(line for line in lines if line.upper().startswith("DATAPATH="))
    data_root = Path(data_line.split("=", 1)[1]).resolve()
    fields = next(line.split() for line in lines if line.split()[0].lower() == "10000.03e")
    source_path = data_root / fields[2]
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    return fields, source_path


def build_table(zaid: str, za: int, incident_particle: int, angular_values: list[float]) -> tuple[str, dict[str, object]]:
    xss = [1.0, 2.0, 1.0, 0.0, 6.0, 1.0, 9.0, 10.0, 1.0, *angular_values]
    nxs = [0] * 16
    nxs[0] = len(xss)
    nxs[1] = za
    nxs[2] = len(angular_values)
    nxs[4] = 1
    nxs[5] = 1
    nxs[6] = 1
    nxs[8] = 0
    nxs[11] = incident_particle

    jxs = [0] * 32
    jxs[0] = 1
    jxs[1] = 3
    jxs[5] = 4
    jxs[12] = 5
    jxs[15] = 7
    jxs[16] = 8

    header = f"{zaid}   1.000000 0.00000E+00   private photon angular qualification\n" + "\n" * 5
    table = header + format_int_block(nxs) + format_int_block(jxs) + format_float_block(xss)
    return table, {"zaid": zaid, "nxs": nxs, "jxs": jxs, "xss": xss}


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
    neutron_path = data_root / "private_neutron_mgace"
    photon_path = data_root / "private_photon_mgace"
    neutron_table, neutron = build_table(NEUTRON_ZAID, 10006, 1, [])
    photon_table, photon = build_table(PHOTON_ZAID, 1000, 2, [ANGULAR_MEAN])
    neutron_path.write_text(neutron_table, encoding="ascii")
    photon_path.write_text(photon_table, encoding="ascii")

    electron_fields, electron_path = electron_dependency(arguments.base_xsdir.resolve())
    private_electron_path = data_root / "electron_03e"
    shutil.copyfile(electron_path, private_electron_path)
    electron_fields[2] = private_electron_path.name

    xsdir_path = root / "xsdir"
    xsdir_path.write_text(
        f"DATAPATH={data_root}\n"
        "atomic weight ratios\n"
        "  10006  1.000000\n"
        "directory\n"
        f"  {NEUTRON_ZAID}  1.000000 {neutron_path.name} 0 1 1 {len(neutron['xss'])} 0 0 0.00\n"
        f"  {PHOTON_ZAID}  1.000000 {photon_path.name} 0 1 1 {len(photon['xss'])} 0 0 0.00\n"
        f"  {' '.join(electron_fields)}\n",
        encoding="ascii",
    )

    manifest = {
        "purpose": "private one-group photon negative one-variable angular qualification",
        "angular_mean": ANGULAR_MEAN,
        "expected_support": [-1.0, 0.0],
        "tables": [
            {**neutron, "path": str(neutron_path.relative_to(root)), "sha256": sha256(neutron_path)},
            {**photon, "path": str(photon_path.relative_to(root)), "sha256": sha256(photon_path)},
        ],
        "xsdir": str(xsdir_path.relative_to(root)),
        "xsdir_sha256": sha256(xsdir_path),
        "electron_dependency": {
            "zaid": "10000.03e",
            "source_path": str(electron_path),
            "source_sha256": sha256(electron_path),
            "private_path": str(private_electron_path.relative_to(root)),
            "private_sha256": sha256(private_electron_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"manifest={manifest_path}")
    print(f"manifest_sha256={sha256(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

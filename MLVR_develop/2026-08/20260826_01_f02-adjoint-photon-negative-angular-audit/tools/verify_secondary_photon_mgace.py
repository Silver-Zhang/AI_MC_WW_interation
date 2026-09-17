#!/usr/bin/env python3
"""Independently read back the secondary photon blocks used by RMC."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_table(path: Path) -> tuple[str, list[int], list[int], list[float]]:
    lines = path.read_text(encoding="ascii").splitlines()
    tokens = " ".join(lines[6:]).split()
    nxs = [int(value) for value in tokens[:16]]
    jxs = [int(value) for value in tokens[16:48]]
    xss = [float(value) for value in tokens[48:]]
    require(len(xss) == nxs[0], "NXS(1) length mismatch")
    return lines[0].split()[0], nxs, jxs, xss


def at(values: list[float], position: int) -> float:
    require(1 <= position <= len(values), f"XSS position {position} out of range")
    return values[position - 1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    require(sha256(root / manifest["xsdir"]) == manifest["xsdir_sha256"], "xsdir hash mismatch")

    neutron_record = next(table for table in manifest["tables"] if table["zaid"] == "10006.91m")
    neutron_path = root / neutron_record["path"]
    require(sha256(neutron_path) == neutron_record["sha256"], "neutron table hash mismatch")
    zaid, nxs, jxs, xss = read_table(neutron_path)
    require(zaid == "10006.91m" and nxs[1] == 10006, "neutron identity mismatch")
    require(nxs[4:8] == [1, 1, 1, 1], "expected one group and one secondary")
    require(nxs[8] == 0 and nxs[11] == 1, "primary neutron metadata mismatch")
    require(jxs[10:17] == [5, 6, 7, 9, 10, 11, 13], "secondary pointer layout mismatch")

    lipt, lerg2l, lp0l, lsang2, lnleg2, lxpn, lpn = jxs[10:17]
    require(int(at(xss, lipt)) == 2, "secondary particle must be photon")
    photon_group_position = int(at(xss, lerg2l))
    require(int(at(xss, photon_group_position)) == 1, "secondary photon group count mismatch")
    require(math.isclose(at(xss, photon_group_position + 1), 1.0), "secondary photon center mismatch")
    require(int(at(xss, lsang2)) == 0 and int(at(xss, lnleg2)) == 1, "secondary angular metadata mismatch")

    secondary_p0_position = int(at(xss, lp0l + 1))
    require(math.isclose(at(xss, secondary_p0_position), 1.0), "secondary P0 mismatch")
    secondary_xpn_position = int(at(xss, lxpn + 1))
    angular_offset = int(at(xss, secondary_xpn_position))
    secondary_pn_position = int(at(xss, lpn + 1))
    angular_value = at(xss, secondary_pn_position + angular_offset - 1)
    require(math.isclose(angular_value, -0.5), "secondary angular mean mismatch")

    photon_record = next(table for table in manifest["tables"] if table["zaid"] == "10000.91g")
    photon_path = root / photon_record["path"]
    require(sha256(photon_path) == photon_record["sha256"], "photon table hash mismatch")
    photon_zaid, pnxs, pjxs, pxss = read_table(photon_path)
    require(photon_zaid == "10000.91g" and pnxs[11] == 2, "photon identity mismatch")
    photon_p0_position = int(at(pxss, pjxs[12]))
    require(math.isclose(at(pxss, photon_p0_position), 0.0), "photon self-scattering must be zero")
    require(manifest["electron_dependency"]["source_sha256"] == manifest["electron_dependency"]["private_sha256"],
            "electron dependency copy mismatch")

    report = {
        "status": "qualified",
        "nsec": nxs[7],
        "secondary_particle": 2,
        "secondary_isang": int(at(xss, lsang2)),
        "secondary_nleg": int(at(xss, lnleg2)),
        "secondary_p0": at(xss, secondary_p0_position),
        "secondary_angular_value": angular_value,
        "expected_support": [-1.0, 0.0],
        "theoretical_mean": -0.5,
        "neutron_table_sha256": sha256(neutron_path),
        "photon_table_sha256": sha256(photon_path),
        "manifest_sha256": sha256(manifest_path),
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print("status=qualified secondary=photon ISANG=0 NLEG=1 x=-0.5")
    print(f"report={arguments.output.resolve()}")
    print(f"report_sha256={sha256(arguments.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

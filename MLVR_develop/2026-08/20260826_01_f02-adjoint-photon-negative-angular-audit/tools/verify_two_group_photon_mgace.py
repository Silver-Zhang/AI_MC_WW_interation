#!/usr/bin/env python3
"""Independently verify warning-free two-group photon qualification tables."""

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


def read_table(path: Path) -> tuple[list[int], list[int], list[float]]:
    lines = path.read_text(encoding="ascii").splitlines()
    tokens = " ".join(lines[6:]).split()
    nxs = [int(value) for value in tokens[:16]]
    jxs = [int(value) for value in tokens[16:48]]
    xss = [float(value) for value in tokens[48:]]
    require(len(xss) == nxs[0], "NXS(1) length mismatch")
    return nxs, jxs, xss


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
    require(manifest["group_count"] == 2 and manifest["source_energy_MeV"] == 3.0, "two-group metadata mismatch")
    require(sha256(root / manifest["xsdir"]) == manifest["xsdir_sha256"], "xsdir hash mismatch")
    records = {record["zaid"]: record for record in manifest["tables"]}
    neutron_path = root / records["10006.92m"]["path"]
    photon_path = root / records["10000.92g"]["path"]
    require(sha256(neutron_path) == records["10006.92m"]["sha256"], "neutron hash mismatch")
    require(sha256(photon_path) == records["10000.92g"]["sha256"], "photon hash mismatch")
    nnxs, njxs, nxss = read_table(neutron_path)
    pnxs, pjxs, pxss = read_table(photon_path)
    require(nnxs[4] == pnxs[4] == 2, "NGRP mismatch")
    require(nxss[:4] == pxss[:4] == [3.0, 1.0, 2.0, 2.0], "group structure mismatch")
    lower_bins = [pxss[1] - 0.5 * pxss[3], pxss[0] - 0.5 * pxss[2]]
    require(lower_bins == [0.0, 2.0], "unexpected ascending lower bounds")
    require(2.0 < manifest["source_energy_MeV"] <= 4.0, "source not inside upper group")

    if manifest["kind"] == "ordinary":
        p0 = int(at(pxss, pjxs[12]))
        require([at(pxss, p0), at(pxss, p0 + 1)] == [1.0, 1.0], "ordinary P0 mismatch")
        xpn = int(at(pxss, pjxs[15]))
        lpn = int(at(pxss, pjxs[16]))
        angular_values = [at(pxss, lpn + int(at(pxss, xpn + offset)) - 1) for offset in range(2)]
        require(all(math.isclose(value, -0.5) for value in angular_values), "ordinary angular values mismatch")
        details = {"angular_values": angular_values}
    else:
        require(nnxs[7] == 1 and int(at(nxss, njxs[10])) == 2, "secondary metadata mismatch")
        lp0l, lsang2, lnleg2, lxpn, lpn = njxs[12], njxs[13], njxs[14], njxs[15], njxs[16]
        secondary_p0 = int(at(nxss, lp0l + 1))
        matrix = [at(nxss, secondary_p0 + offset) for offset in range(4)]
        require(matrix == [0.0, 0.0, 1.0, 0.0], "secondary P0 matrix mismatch")
        require(int(at(nxss, lsang2)) == 0 and int(at(nxss, lnleg2)) == 1, "secondary angular metadata mismatch")
        xpn_base = int(at(nxss, lxpn + 1))
        angular_offset = int(at(nxss, xpn_base + 2))
        pn_base = int(at(nxss, lpn + 1))
        angular_value = at(nxss, pn_base + angular_offset - 1)
        require(math.isclose(angular_value, -0.5), "secondary angular value mismatch")
        gamma_p0 = int(at(pxss, pjxs[12]))
        require([at(pxss, gamma_p0), at(pxss, gamma_p0 + 1)] == [0.0, 0.0], "gamma P0 must be zero")
        details = {"secondary_p0_matrix": matrix, "angular_value": angular_value}

    require(manifest["electron_dependency"]["source_sha256"] == manifest["electron_dependency"]["private_sha256"],
            "electron dependency mismatch")
    report = {
        "status": "qualified",
        "kind": manifest["kind"],
        "group_count": 2,
        "lower_group_bounds_MeV": lower_bins,
        "source_energy_MeV": manifest["source_energy_MeV"],
        "expected_warning_count": 0,
        "expected_support": [-1.0, 0.0],
        "theoretical_mean": -0.5,
        **details,
        "manifest_sha256": sha256(manifest_path),
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(f"status=qualified kind={manifest['kind']} groups=2 expected_warnings=0")
    print(f"report_sha256={sha256(arguments.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

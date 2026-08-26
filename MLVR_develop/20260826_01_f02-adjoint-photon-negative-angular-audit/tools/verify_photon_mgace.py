#!/usr/bin/env python3
"""Independently read back the private gamma MGACE angular block."""

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
    require(len(lines) >= 7, "table is too short")
    require(all(not line.strip() for line in lines[1:6]), "expected five blank header lines")
    tokens = " ".join(lines[6:]).split()
    nxs = [int(value) for value in tokens[:16]]
    jxs = [int(value) for value in tokens[16:48]]
    xss = [float(value) for value in tokens[48:]]
    require(len(xss) == nxs[0], "NXS(1) length mismatch")
    return lines[0].split()[0], nxs, jxs, xss


def at(values: list[float], one_based_position: int) -> float:
    require(1 <= one_based_position <= len(values), f"position {one_based_position} outside XSS")
    return values[one_based_position - 1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    require(sha256(root / manifest["xsdir"]) == manifest["xsdir_sha256"], "xsdir SHA256 mismatch")
    photon = next(table for table in manifest["tables"] if table["zaid"] == "10000.91g")
    table_path = root / photon["path"]
    require(sha256(table_path) == photon["sha256"], "photon table SHA256 mismatch")
    zaid, nxs, jxs, xss = read_table(table_path)
    require(zaid == "10000.91g", "photon ZAID mismatch")
    require(nxs[1] == 1000 and nxs[2] == 1 and nxs[4:7] == [1, 1, 1], "PNXS layout mismatch")
    require(nxs[8] == 0 and nxs[11] == 2, "expected ISANG=0 and IPT=2")
    require(jxs[:17] == [1, 3, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 5, 0, 0, 7, 8], "PJXS layout mismatch")
    require(math.isclose(at(xss, jxs[0]), 1.0), "energy center mismatch")
    require(math.isclose(at(xss, jxs[1]), 1.0), "total cross section mismatch")
    require(math.isclose(at(xss, jxs[5]), 0.0), "absorption mismatch")
    p0_position = int(at(xss, jxs[12]))
    require(math.isclose(at(xss, p0_position), 1.0), "P0 mismatch")
    xpnd_position = int(at(xss, jxs[15]))
    angular_offset = int(at(xss, xpnd_position))
    pn_position = int(at(xss, jxs[16]))
    angular_value = at(xss, pn_position + angular_offset - 1)
    require(math.isclose(angular_value, -0.5), "angular mean mismatch")
    report = {
        "status": "qualified",
        "zaid": zaid,
        "nleg": nxs[2],
        "isang": nxs[8],
        "angular_value": angular_value,
        "expected_support": [-1.0, 0.0],
        "theoretical_mean": -0.5,
        "table_sha256": sha256(table_path),
        "manifest_sha256": sha256(manifest_path),
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print("status=qualified zaid=10000.91g support=[-1.0,0.0] mean=-0.5")
    print(f"report={arguments.output.resolve()}")
    print(f"report_sha256={sha256(arguments.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

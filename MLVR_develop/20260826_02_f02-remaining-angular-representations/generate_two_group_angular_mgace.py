#!/usr/bin/env python3
"""Generate warning-free two-group private neutron angular MGACE assets."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


ZAID = "10006.93m"
ZA = 10006
GROUPS = (3.0, 1.0, 2.0, 2.0)


@dataclass(frozen=True)
class Case:
    name: str
    isang: int
    values: tuple[float, ...]
    support: tuple[float, float]
    mean: float
    variance: float | None


CASES = (
    Case("isotropic", 0, (), (-1.0, 1.0), 0.0, 1.0 / 3.0),
    Case("one_variable_positive", 0, (0.5,), (0.0, 1.0), 0.5, 1.0 / 12.0),
    Case("equiprobable_multi_bin", 0, (-1.0, -0.5, 0.25, 1.0), (-1.0, 1.0), -1.0 / 12.0, 17.0 / 48.0),
    Case("discrete_cosine", 1, (0.2, 0.7, -0.8, 0.0, 0.9), (-0.8, 0.9), 0.11, None),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def format_int_block(values: list[int]) -> str:
    return "".join(" ".join(f"{value:8d}" for value in values[index:index + 8]) + "\n" for index in range(0, len(values), 8))


def format_float_block(values: list[float]) -> str:
    return "".join(" ".join(f"{value:15.8E}" for value in values[index:index + 4]) + "\n" for index in range(0, len(values), 4))


def table(case: Case) -> tuple[list[int], list[int], list[float]]:
    if case.values:
        first_angular_locator = 1.0
        second_angular_locator = float(1 + len(case.values))
        xss = [
            *GROUPS,
            1.0, 1.0, 0.0, 0.0,
            10.0, 1.0, 1.0,
            14.0, 16.0,
            first_angular_locator, second_angular_locator,
            *case.values, *case.values,
        ]
    else:
        xss = [*GROUPS, 1.0, 1.0, 0.0, 0.0, 10.0, 1.0, 1.0, 0.0]
    nxs = [0] * 16
    nxs[0] = len(xss)
    nxs[1] = ZA
    nxs[2] = len(case.values)
    nxs[4:7] = [2, 0, 0]
    nxs[8] = case.isang
    nxs[11] = 1
    jxs = [0] * 32
    jxs[0], jxs[1], jxs[5], jxs[12], jxs[15], jxs[16] = 1, 5, 7, 9, 12, 13
    return nxs, jxs, xss


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    if root.exists():
        raise FileExistsError(root)
    root.mkdir(parents=True)
    records = []
    for case in CASES:
        directory = root / case.name
        data = directory / "data"
        data.mkdir(parents=True)
        nxs, jxs, xss = table(case)
        table_path = data / "angular_mgace"
        header = f"{ZAID}   1.000000 0.00000E+00   private two-group angular qualification\n" + "\n" * 5
        table_path.write_text(header + format_int_block(nxs) + format_int_block(jxs) + format_float_block(xss), encoding="ascii")
        xsdir_path = directory / "xsdir"
        xsdir_path.write_text(f"DATAPATH={data}\natomic weight ratios\n  {ZA:5d}  1.000000\ndirectory\n  {ZAID}  1.000000 angular_mgace 0 1 1 {len(xss)} 0 0 0.00\n", encoding="ascii")
        records.append({"name": case.name, "isang": case.isang, "nleg": len(case.values), "values": list(case.values), "support": list(case.support), "mean": case.mean, "variance": case.variance, "table": str(table_path.relative_to(root)), "table_sha256": sha256(table_path), "xsdir": str(xsdir_path.relative_to(root)), "xsdir_sha256": sha256(xsdir_path)})
    manifest = {"purpose": "warning-free two-group neutron angular qualification", "group_centers_MeV": [3.0, 1.0], "group_widths_MeV": [2.0, 2.0], "source_energy_MeV": 3.0, "cases": records}
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"generated_cases={len(records)}")
    print(f"manifest_sha256={sha256(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate private one-group MGACE tables for angular-path qualification."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


ZAID = "10006.91m"
ZA = 10006


@dataclass(frozen=True)
class AngularCase:
    name: str
    isang: int
    values: tuple[float, ...]
    representation: str

    @property
    def nleg(self) -> int:
        return len(self.values)


CASES = (
    AngularCase("isotropic", 0, (), "isotropic"),
    AngularCase("one_variable_negative", 0, (-0.5,), "equiprobable-one-variable"),
    AngularCase("one_variable_positive", 0, (0.5,), "equiprobable-one-variable"),
    AngularCase("equiprobable_multi_bin", 0, (-1.0, -0.5, 0.25, 1.0), "equiprobable-bins"),
    AngularCase("discrete_cosine", 1, (0.2, 0.7, -0.8, 0.0, 0.9), "discrete-cosines"),
)


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


def build_table(case: AngularCase) -> tuple[str, list[int], list[int], list[float]]:
    if case.nleg == 0:
        xss = [1.0, 2.0, 1.0, 0.0, 6.0, 1.0, 0.0, 0.0]
    else:
        xss = [1.0, 2.0, 1.0, 0.0, 6.0, 1.0, 9.0, 10.0, 1.0, *case.values]

    nxs = [0] * 16
    nxs[0] = len(xss)
    nxs[1] = ZA
    nxs[2] = case.nleg
    nxs[4] = 1
    nxs[5] = 1
    nxs[6] = 1
    nxs[8] = case.isang
    nxs[11] = 1

    jxs = [0] * 32
    jxs[0] = 1
    jxs[1] = 3
    jxs[5] = 4
    jxs[12] = 5
    jxs[15] = 7
    jxs[16] = 8

    header = f"{ZAID}   1.000000 0.00000E+00   private angular qualification\n" + "\n" * 5
    content = header + format_int_block(nxs) + format_int_block(jxs) + format_float_block(xss)
    return content, nxs, jxs, xss


def write_case(root: Path, case: AngularCase) -> dict[str, object]:
    case_root = root / case.name
    data_root = case_root / "data"
    data_root.mkdir(parents=True)
    table_path = data_root / "angular_mgace"
    table, nxs, jxs, xss = build_table(case)
    table_path.write_text(table, encoding="ascii")

    xsdir_path = case_root / "xsdir"
    xsdir = (
        f"DATAPATH={data_root.resolve()}\n"
        "atomic weight ratios\n"
        f"  {ZA:5d}  1.000000\n"
        "directory\n"
        f"  {ZAID}  1.000000 angular_mgace 0 1 1 {len(xss)} 0 0 0.00\n"
    )
    xsdir_path.write_text(xsdir, encoding="ascii")
    return {
        "name": case.name,
        "zaid": ZAID,
        "representation": case.representation,
        "isang": case.isang,
        "nleg": case.nleg,
        "angular_values": list(case.values),
        "table": str(table_path.relative_to(root)),
        "table_sha256": sha256(table_path),
        "xsdir": str(xsdir_path.relative_to(root)),
        "xsdir_sha256": sha256(xsdir_path),
        "nxs": nxs,
        "jxs": jxs,
        "xss_length": len(xss),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"refusing to overwrite {manifest_path}")
    root.mkdir(parents=True, exist_ok=True)

    manifest = {
        "format": "ASCII MGACE",
        "purpose": "task-private one-group pure self-scattering angular qualification",
        "group_count": 1,
        "energy_center_MeV": 1.0,
        "energy_width_MeV": 2.0,
        "total_cross_section": 1.0,
        "absorption_cross_section": 0.0,
        "p0_self_scatter": 1.0,
        "cases": [write_case(root, case) for case in CASES],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="ascii")
    print(f"generated_cases={len(CASES)}")
    print(f"manifest={manifest_path}")
    print(f"manifest_sha256={sha256(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
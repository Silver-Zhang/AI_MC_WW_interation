#!/usr/bin/env python3
"""Independently read back and qualify private one-group angular MGACE assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


EXPECTED = {
    "isotropic": {"isang": 0, "values": [], "support": [-1.0, 1.0], "mean": 0.0},
    "one_variable_negative": {
        "isang": 0,
        "values": [-0.5],
        "support": [-1.0, 0.0],
        "mean": -0.5,
    },
    "one_variable_positive": {
        "isang": 0,
        "values": [0.5],
        "support": [0.0, 1.0],
        "mean": 0.5,
    },
    "equiprobable_multi_bin": {
        "isang": 0,
        "values": [-1.0, -0.5, 0.25, 1.0],
        "support": [-1.0, 1.0],
        "mean": -1.0 / 12.0,
    },
    "discrete_cosine": {
        "isang": 1,
        "values": [0.2, 0.7, -0.8, 0.0, 0.9],
        "support": [-0.8, 0.9],
        "mean": 0.11,
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def close(actual: float, expected: float, label: str) -> None:
    require(math.isclose(actual, expected, rel_tol=0.0, abs_tol=1.0e-12), f"{label}: {actual} != {expected}")


def read_xsdir(path: Path) -> tuple[Path, str, int, int]:
    lines = [line.strip() for line in path.read_text(encoding="ascii").splitlines() if line.strip()]
    require(lines[0].upper().startswith("DATAPATH="), f"{path}: missing DATAPATH")
    data_path = Path(lines[0].split("=", 1)[1]).resolve()
    require("directory" in [line.lower() for line in lines], f"{path}: missing directory marker")
    directory_index = next(index for index, line in enumerate(lines) if line.lower() == "directory")
    fields = lines[directory_index + 1].split()
    require(len(fields) >= 7, f"{path}: malformed directory entry")
    require(fields[3] == "0", f"{path}: expected ASCII file type 0")
    return data_path / fields[2], fields[0], int(fields[5]), int(fields[6])


def read_table(path: Path, address: int) -> tuple[str, list[int], list[int], list[float]]:
    require(address == 1, f"{path}: oracle currently requires line address 1, got {address}")
    lines = path.read_text(encoding="ascii").splitlines()
    require(len(lines) >= 7, f"{path}: table is too short")
    header = lines[0].split()[0]
    require(all(not line.strip() for line in lines[1:6]), f"{path}: expected five blank header lines")
    tokens = " ".join(lines[6:]).split()
    require(len(tokens) >= 48, f"{path}: incomplete NXS/JXS blocks")
    nxs = [int(value) for value in tokens[:16]]
    jxs = [int(value) for value in tokens[16:48]]
    xss = [float(value) for value in tokens[48:]]
    require(len(xss) == nxs[0], f"{path}: NXS(1)={nxs[0]}, read {len(xss)} XSS values")
    return header, nxs, jxs, xss


def one_based(values: list[float], position: int, label: str) -> float:
    require(1 <= position <= len(values), f"{label}: position {position} outside 1..{len(values)}")
    return values[position - 1]


def derive_distribution(isang: int, values: list[float]) -> tuple[list[float], float]:
    if not values:
        return [-1.0, 1.0], 0.0
    if isang == 0 and len(values) == 1:
        mean = values[0]
        support = [2.0 * mean - 1.0, 1.0] if mean >= 0.0 else [-1.0, 2.0 * mean + 1.0]
        return support, sum(support) / 2.0
    if isang == 0:
        require(values == sorted(values), "equiprobable boundaries are not monotone")
        require(values[0] >= -1.0 and values[-1] <= 1.0, "equiprobable boundaries leave cosine domain")
        means = [(left + right) / 2.0 for left, right in zip(values, values[1:])]
        return [values[0], values[-1]], sum(means) / len(means)

    require(len(values) % 2 == 1, "discrete-cosine NLEG must be odd")
    cdf = values[: (len(values) - 1) // 2]
    cosines = values[(len(values) - 1) // 2 :]
    require(cdf == sorted(cdf) and all(0.0 < value < 1.0 for value in cdf), "invalid discrete CDF")
    require(all(-1.0 <= value <= 1.0 for value in cosines), "discrete cosine outside [-1,1]")
    probabilities = [cdf[0], *[right - left for left, right in zip(cdf, cdf[1:])], 1.0 - cdf[-1]]
    return [min(cosines), max(cosines)], sum(probability * cosine for probability, cosine in zip(probabilities, cosines))


def verify_case(root: Path, manifest_case: dict[str, object]) -> dict[str, object]:
    name = str(manifest_case["name"])
    require(name in EXPECTED, f"unexpected case {name}")
    expected = EXPECTED[name]
    xsdir_path = root / str(manifest_case["xsdir"])
    require(sha256(xsdir_path) == manifest_case["xsdir_sha256"], f"{name}: xsdir SHA256 mismatch")
    table_path, zaid, address, declared_length = read_xsdir(xsdir_path)
    require(table_path.resolve() == (root / str(manifest_case["table"])).resolve(), f"{name}: xsdir table path mismatch")
    require(sha256(table_path) == manifest_case["table_sha256"], f"{name}: table SHA256 mismatch")

    header, nxs, jxs, xss = read_table(table_path, address)
    require(header.lower() == zaid.lower() == "10006.91m", f"{name}: ZAID mismatch")
    require(declared_length == len(xss), f"{name}: xsdir length {declared_length} != {len(xss)}")
    require(nxs[1] == 10006, f"{name}: NXS(2) is not ZA 10006")
    require(nxs[4:7] == [1, 1, 1], f"{name}: expected NGRP=NUS=NDS=1")
    require(nxs[7] == 0 and nxs[9] == 0 and nxs[10] == 0, f"{name}: unexpected secondary/nubar flags")
    require(nxs[11] == 1, f"{name}: incident particle is not neutron")
    require(nxs[2] == len(expected["values"]), f"{name}: NLEG mismatch")
    require(nxs[8] == expected["isang"], f"{name}: ISANG mismatch")
    require(jxs[:17] == [1, 3, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 5, 0, 0, 7, 8], f"{name}: JXS layout mismatch")
    require(all(value == 0 for value in jxs[17:]), f"{name}: unexpected trailing JXS locators")

    close(one_based(xss, jxs[0], f"{name}: LERG center"), 1.0, f"{name}: energy center")
    close(one_based(xss, jxs[0] + 1, f"{name}: LERG width"), 2.0, f"{name}: energy width")
    close(one_based(xss, jxs[1], f"{name}: LTOT"), 1.0, f"{name}: total cross section")
    close(one_based(xss, jxs[5], f"{name}: LABS"), 0.0, f"{name}: absorption cross section")
    p0_position = int(one_based(xss, jxs[12], f"{name}: LP0L"))
    close(one_based(xss, p0_position, f"{name}: P0"), 1.0, f"{name}: P0 self scatter")

    angular_values: list[float]
    if expected["values"]:
        xpnd_position = int(one_based(xss, jxs[15], f"{name}: LXPNL"))
        pnd_offset = int(one_based(xss, xpnd_position, f"{name}: XPN"))
        pn_position = int(one_based(xss, jxs[16], f"{name}: LPNL"))
        angular_start = pn_position + pnd_offset - 1
        angular_values = [one_based(xss, angular_start + index, f"{name}: PN") for index in range(nxs[2])]
    else:
        close(one_based(xss, jxs[15], f"{name}: LXPNL"), 0.0, f"{name}: isotropic XPN locator")
        close(one_based(xss, jxs[16], f"{name}: LPNL"), 0.0, f"{name}: isotropic PN locator")
        angular_values = []
    require(angular_values == expected["values"], f"{name}: angular data mismatch")

    support, mean = derive_distribution(nxs[8], angular_values)
    require(support == expected["support"], f"{name}: support {support} != {expected['support']}")
    close(mean, float(expected["mean"]), f"{name}: theoretical mean")
    return {
        "name": name,
        "zaid": zaid,
        "nleg": nxs[2],
        "isang": nxs[8],
        "support": support,
        "theoretical_mean": mean,
        "p0_position": p0_position,
        "table_sha256": sha256(table_path),
        "status": "qualified",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    cases = manifest.get("cases", [])
    require({str(case["name"]) for case in cases} == set(EXPECTED), "manifest case set mismatch")
    results = [verify_case(root, case) for case in cases]
    report = {
        "manifest": str(manifest_path),
        "manifest_sha256": sha256(manifest_path),
        "qualified_case_count": len(results),
        "cases": results,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(f"qualified_cases={len(results)}")
    for result in results:
        print(f"{result['name']}: support={result['support']} mean={result['theoretical_mean']:.12g} status=qualified")
    print(f"report={arguments.output.resolve()}")
    print(f"report_sha256={sha256(arguments.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
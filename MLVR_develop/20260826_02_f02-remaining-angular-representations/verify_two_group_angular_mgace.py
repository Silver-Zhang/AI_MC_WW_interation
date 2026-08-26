#!/usr/bin/env python3
"""Read back generated two-group private neutron angular MGACE assets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED = {
    "isotropic": {"isang": 0, "values": [], "support": [-1.0, 1.0], "mean": 0.0, "variance": 1.0 / 3.0},
    "one_variable_positive": {"isang": 0, "values": [0.5], "support": [0.0, 1.0], "mean": 0.5, "variance": 1.0 / 12.0},
    "equiprobable_multi_bin": {"isang": 0, "values": [-1.0, -0.5, 0.25, 1.0], "support": [-1.0, 1.0], "mean": -1.0 / 12.0, "variance": 17.0 / 48.0},
    "discrete_cosine": {"isang": 1, "values": [0.2, 0.7, -0.8, 0.0, 0.9], "support": [-0.8, 0.9], "mean": 0.11, "variance": 0.3589},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def at(values: list[float], position: int) -> float:
    require(1 <= position <= len(values), f"XSS position {position} is invalid")
    return values[position - 1]


def read_table(path: Path) -> tuple[list[int], list[int], list[float]]:
    lines = path.read_text(encoding="ascii").splitlines()
    tokens = " ".join(lines[6:]).split()
    nxs = [int(value) for value in tokens[:16]]
    jxs = [int(value) for value in tokens[16:48]]
    xss = [float(value) for value in tokens[48:]]
    require(len(xss) == nxs[0], f"NXS(1)={nxs[0]}, actual={len(xss)}")
    return nxs, jxs, xss


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    records = []
    for record in manifest["cases"]:
        name = str(record["name"])
        expected = EXPECTED[name]
        table_path = root / str(record["table"])
        xsdir_path = root / str(record["xsdir"])
        require(sha256(table_path) == record["table_sha256"], f"{name}: table hash mismatch")
        require(sha256(xsdir_path) == record["xsdir_sha256"], f"{name}: xsdir hash mismatch")
        nxs, jxs, xss = read_table(table_path)
        require(nxs[1] == 10006 and nxs[4:7] == [2, 0, 0] and nxs[11] == 1, f"{name}: neutron two-group metadata mismatch")
        require(nxs[2] == len(expected["values"]) and nxs[8] == expected["isang"], f"{name}: angular metadata mismatch")
        require(xss[:4] == [3.0, 1.0, 2.0, 2.0], f"{name}: group structure mismatch")
        lp0 = jxs[12]
        require(at(xss, lp0) == 10.0 and [at(xss, 10), at(xss, 11)] == [1.0, 1.0], f"{name}: P0 layout mismatch")
        if expected["values"]:
            lxpn = int(at(xss, jxs[15]))
            lpn = int(at(xss, jxs[16]))
            first_pnd = int(at(xss, lxpn))
            second_pnd = int(at(xss, lxpn + 1))
            require([first_pnd, second_pnd] == [1, 1 + len(expected["values"])], f"{name}: XPN locator mismatch")
            first = [at(xss, lpn + first_pnd - 1 + index) for index in range(len(expected["values"]))]
            second = [at(xss, lpn + second_pnd - 1 + index) for index in range(len(expected["values"]))]
            require(first == second == expected["values"], f"{name}: PN values mismatch")
            if expected["isang"] == 0 and len(first) > 1:
                widths = [first[index + 1] - first[index] for index in range(len(first) - 1)]
                mean = sum((first[index] + first[index + 1]) / 2.0 for index in range(len(widths))) / len(widths)
                second_moment = sum((first[index] ** 2 + first[index] * first[index + 1] + first[index + 1] ** 2) / 3.0 for index in range(len(widths))) / len(widths)
                require(abs(mean - expected["mean"]) < 1.0e-12 and abs(second_moment - mean ** 2 - expected["variance"]) < 1.0e-12, f"{name}: equiprobable-bin moments mismatch")
            if expected["isang"] == 1:
                probabilities = [first[0], first[1] - first[0], 1.0 - first[1]]
                cosines = first[2:]
                mean = sum(probability * cosine for probability, cosine in zip(probabilities, cosines))
                variance = sum(probability * (cosine - mean) ** 2 for probability, cosine in zip(probabilities, cosines))
                require(all(probability > 0.0 for probability in probabilities) and abs(mean - expected["mean"]) < 1.0e-12 and abs(variance - expected["variance"]) < 1.0e-12, f"{name}: discrete CDF/probability mismatch")
        records.append({"name": name, "nxs1": nxs[0], "status": "qualified"})
    report = {"status": "qualified", "manifest_sha256": sha256(manifest_path), "cases": records}
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(f"qualified_cases={len(records)}")
    print(f"report_sha256={sha256(arguments.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

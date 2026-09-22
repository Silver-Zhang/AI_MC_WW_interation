#!/usr/bin/env python3
"""Run and compare independent adjoint native-WWMESH cases."""

import csv
import json
import math
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = ROOT / "cases"
RMC = Path("/tmp/rmc-f08-cell-ww-build/bin/RMC")
DATA = "/home/silver/NucXS_Library/RMC_DATA"
RESPONSE_GROUP = 16
TALLY = re.compile(r"^\s*(?:(?P<cell>\d+)\s+)?(?P<group>\d+)\s+(?P<energy>[+\-0-9.Ee]+)\s+(?P<mean>[+\-0-9.Ee]+)\s+(?P<re>[+\-0-9.Ee]+)\s*$")
SOURCES = re.compile(r"Source Number\s*:\s*(\d+)\.")
FIXED_SOURCE_TIME = re.compile(r"Time in Fixed Source Calculation\s*=\s*([+\-0-9.Ee]+)\s+seconds")


def read_response(path: Path) -> tuple[float, float]:
    for line in path.read_text(encoding="utf-8").splitlines():
        match = TALLY.match(line)
        if match and int(match.group("group")) == RESPONSE_GROUP:
            mean = float(match.group("mean"))
            sigma = mean * float(match.group("re"))
            if mean > 0.0 and sigma > 0.0:
                return mean, sigma
    raise RuntimeError(f"group {RESPONSE_GROUP} has no positive uncertainty in {path}")


records = []
for seed_dir in sorted(CASES.glob("seed_*")):
    seed = int(seed_dir.name.split("_")[1])
    pair = {}
    for mode in ("analog", "ww"):
        directory = seed_dir / mode
        for path in directory.glob("inp.*"):
            path.unlink()
        completed = subprocess.run([str(RMC), "inp"], cwd=directory, text=True, capture_output=True,
                                   env={"RMC_DATA_PATH": DATA}, check=False)
        (directory / "stdout.log").write_text(completed.stdout, encoding="utf-8")
        (directory / "stderr.log").write_text(completed.stderr, encoding="utf-8")
        sources = SOURCES.findall(completed.stdout)
        if completed.returncode != 0 or sources != ["200000"]:
            raise RuntimeError(f"{seed}/{mode}: exit={completed.returncode}, sources={sources}")
        time_match = FIXED_SOURCE_TIME.search(completed.stdout)
        if not time_match:
            raise RuntimeError(f"{seed}/{mode}: fixed-source time not found")
        mean, sigma = read_response(directory / "inp.Tally")
        pair[mode] = (mean, sigma, float(time_match.group(1)))
    denominator = math.hypot(pair["analog"][1], pair["ww"][1])
    records.append({
        "seed": seed,
        "analog_mean": pair["analog"][0],
        "analog_sigma": pair["analog"][1],
        "analog_time_s": pair["analog"][2],
        "analog_fom": 1.0 / ((pair["analog"][1] / pair["analog"][0]) ** 2 * pair["analog"][2]),
        "ww_mean": pair["ww"][0],
        "ww_sigma": pair["ww"][1],
        "ww_time_s": pair["ww"][2],
        "ww_fom": 1.0 / ((pair["ww"][1] / pair["ww"][0]) ** 2 * pair["ww"][2]),
        "z": (pair["ww"][0] - pair["analog"][0]) / denominator,
    })

wa = [1.0 / row["analog_sigma"] ** 2 for row in records]
ww = [1.0 / row["ww_sigma"] ** 2 for row in records]
analog_mean = sum(row["analog_mean"] * weight for row, weight in zip(records, wa)) / sum(wa)
ww_mean = sum(row["ww_mean"] * weight for row, weight in zip(records, ww)) / sum(ww)
analog_sigma = 1.0 / math.sqrt(sum(wa))
ww_sigma = 1.0 / math.sqrt(sum(ww))
combined_z = (ww_mean - analog_mean) / math.hypot(analog_sigma, ww_sigma)
result = {
    "response_group": RESPONSE_GROUP,
    "per_seed": records,
    "combined": {
        "analog_mean": analog_mean,
        "analog_sigma": analog_sigma,
        "analog_re": analog_sigma / analog_mean,
        "analog_mean_time_s": sum(row["analog_time_s"] for row in records) / len(records),
        "analog_mean_fom": sum(row["analog_fom"] for row in records) / len(records),
        "ww_mean": ww_mean,
        "ww_sigma": ww_sigma,
        "ww_re": ww_sigma / ww_mean,
        "ww_mean_time_s": sum(row["ww_time_s"] for row in records) / len(records),
        "ww_mean_fom": sum(row["ww_fom"] for row in records) / len(records),
        "z": combined_z,
        "pass": abs(combined_z) <= 3.0 and all(abs(row["z"]) <= 3.0 for row in records),
    },
}
(ROOT / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
with (ROOT / "results.csv").open("w", newline="", encoding="utf-8") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["combined"]["pass"] else 1)

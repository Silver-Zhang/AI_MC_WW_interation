#!/usr/bin/env python3
"""Run and independently check frozen density-mesh formal cases with raw evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path


ANOMALY = re.compile(r"(?i)(warning:|error:|\bsignal\b|\bnan\b|\binf\b)")
SOURCE = re.compile(r"Source Number\s*:\s*(\d+)")
FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"
TALLY = re.compile(rf"^\s*Tot\s+({FLOAT})\s+({FLOAT})\s*$", re.MULTILINE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def anomaly_lines(*texts: str) -> list[str]:
    return [line for text in texts for line in text.splitlines() if ANOMALY.search(line)]


def parse_tally(output: str) -> tuple[float, float]:
    matches = TALLY.findall(output)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one target tally row, found {len(matches)}")
    response, relative_error = map(float, matches[0])
    if not all(math.isfinite(value) and value > 0.0 for value in (response, relative_error)):
        raise ValueError("target tally response or relative error is not finite and positive")
    return response, relative_error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--data-index", type=Path, required=True)
    parser.add_argument("--rmc", type=Path, required=True)
    parser.add_argument("--population", type=int, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    arguments = parser.parse_args()

    root = arguments.root.resolve()
    if root.exists():
        raise FileExistsError(root)
    root.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["python3", str(arguments.generator), "--root", str(root), "--mesh", str(arguments.mesh), "--population", str(arguments.population), "--seeds", *(str(seed) for seed in arguments.seeds)],
        check=True,
        text=True,
    )
    manifest = json.loads((root / "manifest.json").read_text(encoding="ascii"))
    records: list[dict[str, object]] = []
    for run in manifest["runs"]:
        directory = root / Path(str(run["input"])).parent
        completed = subprocess.run([str(arguments.rmc), "inp", "-d", str(arguments.data_index.resolve())], cwd=directory, capture_output=True, text=True)
        (directory / "stdout.log").write_text(completed.stdout, encoding="utf-8")
        (directory / "stderr.log").write_text(completed.stderr, encoding="utf-8")
        (directory / "exit_code.txt").write_text(f"{completed.returncode}\n", encoding="ascii")
        output_path = directory / "inp.out"
        tally_path = directory / "inp.Tally"
        output = output_path.read_text(encoding="utf-8", errors="replace") if output_path.exists() else ""
        tally = tally_path.read_text(encoding="utf-8", errors="replace") if tally_path.exists() else ""
        try:
            response, relative_error = parse_tally(tally)
            parse_error = ""
        except ValueError as error:
            response, relative_error, parse_error = math.nan, math.nan, str(error)
        sources = [int(value) for value in SOURCE.findall(completed.stdout)]
        anomalies = anomaly_lines(completed.stdout, completed.stderr, output, tally)
        record = {
            **run,
            "exit_code": completed.returncode,
            "source_counts": sources,
            "warnings_or_errors": anomalies,
            "stderr_bytes": len(completed.stderr.encode("utf-8")),
            "finish_count": completed.stdout.count("RMC Calculation Finish."),
            "response": response,
            "relative_error": relative_error,
            "tally_parse_error": parse_error,
            "stdout_sha256": sha256(directory / "stdout.log"),
            "stderr_sha256": sha256(directory / "stderr.log"),
            "output_sha256": sha256(output_path) if output_path.exists() else "",
            "tally_sha256": sha256(tally_path) if tally_path.exists() else "",
        }
        record["structural_pass"] = (
            record["exit_code"] == 0
            and sources == [arguments.population]
            and not anomalies
            and record["stderr_bytes"] == 0
            and record["finish_count"] == 1
            and not parse_error
        )
        records.append(record)
        print(f"seed={run['seed']} mode={run['mode']} pass={record['structural_pass']}", flush=True)
    report = {"rmc_sha256": sha256(arguments.rmc), "population": arguments.population, "runs": records, "all_structural_pass": all(record["structural_pass"] for record in records)}
    (root / "raw_transport_report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with (root / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["seed", "mode", "exit_code", "source_counts", "stderr_bytes", "finish_count", "response", "relative_error", "structural_pass", "stdout_sha256", "stderr_sha256", "output_sha256", "tally_sha256"])
        writer.writeheader()
        for record in records:
            writer.writerow({key: record[key] for key in writer.fieldnames})
    return 0 if report["all_structural_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

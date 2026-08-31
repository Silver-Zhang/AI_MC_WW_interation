#!/usr/bin/env python3
"""Run frozen angular transports under an actual MPI or MPI+OpenMP configuration."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


BANNER_MPI = re.compile(r"MPI parallel: ON, (\d+) process\(es\)")
BANNER_OMP = re.compile(r"OMP parallel: (ON, (\d+) threads|OFF)")
ANOMALY = re.compile(r"(?i)(warning:|error:|\bsignal\b|\bnan\b|\binf\b)")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--rmc", type=Path, required=True)
    parser.add_argument("--population", type=int, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--density", type=float, required=True)
    parser.add_argument("--ranks", type=int, required=True)
    parser.add_argument("--threads", type=int, required=True)
    arguments = parser.parse_args()
    root, rmc = arguments.root.resolve(), arguments.rmc.resolve()
    if root.exists():
        raise FileExistsError(root)
    root.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["python3", str(arguments.generator.resolve()), "--assets", str(arguments.assets.resolve()), "--root", str(root / "runs"), "--population", str(arguments.population), "--seeds", *(str(seed) for seed in arguments.seeds), "--density", str(arguments.density)], check=True, text=True)
    manifest = json.loads((root / "runs" / "manifest.json").read_text(encoding="ascii"))
    records = []
    expected_omp = f"ON, {arguments.threads} threads" if arguments.threads > 1 else "OFF"
    for ordinal, run in enumerate(manifest["runs"], 1):
        directory = root / "runs" / Path(str(run["input"])).parent
        index = arguments.assets.resolve() / str(run["data_index"])
        command = ["mpiexec", "-n", str(arguments.ranks), str(rmc), "inp"]
        if arguments.threads > 1:
            command.extend(["-s", str(arguments.threads)])
        command.extend(["-d", str(index)])
        completed = subprocess.run(command, cwd=directory, capture_output=True, text=True)
        (directory / "command.txt").write_text(" ".join(command) + "\n", encoding="utf-8")
        (directory / "stdout.log").write_text(completed.stdout, encoding="utf-8")
        (directory / "stderr.log").write_text(completed.stderr, encoding="utf-8")
        (directory / "exit_code.txt").write_text(f"{completed.returncode}\n", encoding="ascii")
        output_path = directory / "inp.out"
        output = output_path.read_text(encoding="utf-8", errors="replace") if output_path.exists() else ""
        mpi = BANNER_MPI.search(completed.stdout)
        omp = BANNER_OMP.search(completed.stdout)
        anomalies = [line for text in (completed.stdout, completed.stderr, output) for line in text.splitlines() if ANOMALY.search(line) and "forum" not in line.lower()]
        record = {**run, "ordinal": ordinal, "command": command, "exit_code": completed.returncode, "mpi_banner_ranks": int(mpi.group(1)) if mpi else None, "omp_banner": omp.group(1) if omp else None, "stderr_bytes": len(completed.stderr.encode()), "finish_count": completed.stdout.count("RMC Calculation Finish."), "anomalies": anomalies, "stdout_sha256": sha256(directory / "stdout.log"), "stderr_sha256": sha256(directory / "stderr.log"), "output_sha256": sha256(output_path) if output_path.exists() else ""}
        record["structural_pass"] = record["exit_code"] == 0 and record["mpi_banner_ranks"] == arguments.ranks and record["omp_banner"] == expected_omp and not anomalies and record["stderr_bytes"] == 0 and record["finish_count"] == 1
        records.append(record)
        print(f"{ordinal:02d}/{len(manifest['runs'])} {run['case']} {run['mode']} seed={run['seed']} pass={record['structural_pass']}", flush=True)
    report = {"rmc_sha256": sha256(rmc), "ranks": arguments.ranks, "threads": arguments.threads, "population": arguments.population, "runs": records, "all_structural_pass": all(item["structural_pass"] for item in records)}
    (root / "raw_transport_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["all_structural_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

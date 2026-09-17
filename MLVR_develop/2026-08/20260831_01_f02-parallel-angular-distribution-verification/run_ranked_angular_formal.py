#!/usr/bin/env python3
"""Run and retain rank-aware parallel MuLab distribution evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


OBSERVERS = {
    "forward": ("CDAceData::GetMgNeuExitErgMu(int, double, double&, double&, CDRNG&)", "rcx"),
    "adjoint": ("CDAceData::GetMgAdjNeuExitErgMu(CDParticleState&, double&, CDRNG&)", "rdx"),
}
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
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--population", type=int, required=True)
    parser.add_argument("--sample-count", type=int, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--density", type=float, required=True)
    parser.add_argument("--ranks", type=int, required=True)
    parser.add_argument("--threads", type=int, required=True)
    arguments = parser.parse_args()

    root, rmc, assets = arguments.root.resolve(), arguments.rmc.resolve(), arguments.assets.resolve()
    if root.exists():
        raise FileExistsError(root)
    root.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["python3", str(arguments.generator.resolve()), "--assets", str(assets), "--root", str(root / "runs"), "--population", str(arguments.population), "--seeds", *(str(seed) for seed in arguments.seeds), "--density", str(arguments.density)], check=True, text=True)
    manifest = json.loads((root / "runs" / "manifest.json").read_text(encoding="ascii"))
    expected_omp = f"ON, {arguments.threads} threads" if arguments.threads > 1 else "OFF"
    records = []
    for ordinal, run in enumerate(manifest["runs"], 1):
        directory = root / "runs" / Path(str(run["input"])).parent
        index = assets / str(run["data_index"])
        symbol, register = OBSERVERS[str(run["mode"])]
        probe_directory = directory / "gdb_probe"
        probe_directory.mkdir()
        (probe_directory / "inp").write_text((directory / "inp").read_text(encoding="ascii"), encoding="ascii")
        environment = os.environ | {"MLVR_GDB_SYMBOL": symbol, "MLVR_GDB_MU_REGISTER": register, "MLVR_GDB_SAMPLE_COUNT": str(arguments.sample_count), "MLVR_GDB_REPORT_DIR": str(probe_directory)}
        command = ["mpiexec", "-n", str(arguments.ranks), "gdb", "-q", "-batch", "-ex", "set debuginfod enabled off", "-x", str(arguments.probe.resolve()), "--args", str(rmc), "inp"]
        if arguments.threads > 1:
            command.extend(["-s", str(arguments.threads)])
        command.extend(["-d", str(index)])
        probe = subprocess.run(command, cwd=probe_directory, capture_output=True, text=True, env=environment)
        (probe_directory / "command.txt").write_text(" ".join(command) + "\n", encoding="utf-8")
        (probe_directory / "gdb.log").write_text(probe.stdout, encoding="utf-8")
        (probe_directory / "gdb.stderr.log").write_text(probe.stderr, encoding="utf-8")
        reports_by_rank: dict[int, dict[str, object]] = {}
        for report_path in probe_directory.glob("rank_*.json"):
            marker = json.loads(report_path.read_text(encoding="utf-8"))
            reports_by_rank[int(marker["rank"])] = marker
        markers = list(reports_by_rank.values())
        ranks = sorted(reports_by_rank)
        full_command = ["mpiexec", "-n", str(arguments.ranks), str(rmc), "inp"]
        if arguments.threads > 1:
            full_command.extend(["-s", str(arguments.threads)])
        full_command.extend(["-d", str(index)])
        full = subprocess.run(full_command, cwd=directory, capture_output=True, text=True)
        (directory / "command.txt").write_text(" ".join(full_command) + "\n", encoding="utf-8")
        (directory / "stdout.log").write_text(full.stdout, encoding="utf-8")
        (directory / "stderr.log").write_text(full.stderr, encoding="utf-8")
        (directory / "exit_code.txt").write_text(f"{full.returncode}\n", encoding="ascii")
        output_path = directory / "inp.out"
        output = output_path.read_text(encoding="utf-8", errors="replace") if output_path.exists() else ""
        mpi, omp = BANNER_MPI.search(full.stdout), BANNER_OMP.search(full.stdout)
        anomalies = [line for text in (full.stdout, full.stderr, output, probe.stderr) for line in text.splitlines() if ANOMALY.search(line) and "forum" not in line.lower()]
        record = {**run, "ordinal": ordinal, "mulab_by_rank": markers, "gdb_exit_code": probe.returncode, "transport_exit_code": full.returncode, "mpi_banner_ranks": int(mpi.group(1)) if mpi else None, "omp_banner": omp.group(1) if omp else None, "stderr_bytes": len(full.stderr.encode()), "finish_count": full.stdout.count("RMC Calculation Finish."), "anomalies": anomalies, "stdout_sha256": sha256(directory / "stdout.log"), "stderr_sha256": sha256(directory / "stderr.log"), "output_sha256": sha256(output_path) if output_path.exists() else ""}
        record["structural_pass"] = (probe.returncode == 0 and not probe.stderr and ranks == list(range(arguments.ranks)) and all(int(marker["sample_count"]) == arguments.sample_count for marker in markers) and full.returncode == 0 and record["mpi_banner_ranks"] == arguments.ranks and record["omp_banner"] == expected_omp and not anomalies and record["stderr_bytes"] == 0 and record["finish_count"] == 1)
        records.append(record)
        print(f"{ordinal:02d}/{len(manifest['runs'])} {run['case']} {run['mode']} seed={run['seed']} pass={record['structural_pass']}", flush=True)
    report = {"rmc_sha256": sha256(rmc), "ranks": arguments.ranks, "threads": arguments.threads, "population": arguments.population, "sample_count_per_rank": arguments.sample_count, "runs": records, "all_structural_pass": all(item["structural_pass"] for item in records)}
    (root / "raw_ranked_transport_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["all_structural_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

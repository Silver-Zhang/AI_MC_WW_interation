#!/usr/bin/env python3
"""Run frozen fissile reciprocity cases under a declared MPI configuration."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


BANNER_MPI = re.compile(r"MPI parallel: ON, (\d+) process\(es\)")
BANNER_OMP = re.compile(r"OMP parallel: (ON, (\d+) threads|OFF)")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--ranks", type=int, required=True)
    parser.add_argument("--threads", type=int, required=True)
    arguments = parser.parse_args()

    root, executable = arguments.root.resolve(), arguments.executable.resolve()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_omp = f"ON, {arguments.threads} threads" if arguments.threads > 1 else "OFF"
    records, failures = [], []
    for run in manifest["runs"]:
        directory = root / Path(str(run["input"])).parent
        command = ["mpiexec", "-n", str(arguments.ranks), str(executable), "inp"]
        if arguments.threads > 1:
            command.extend(["-s", str(arguments.threads)])
        completed = subprocess.run(command, cwd=directory, capture_output=True, text=True)
        (directory / "command.txt").write_text(" ".join(command) + "\n", encoding="utf-8")
        (directory / "stdout.log").write_text(completed.stdout, encoding="utf-8")
        (directory / "stderr.log").write_text(completed.stderr, encoding="utf-8")
        (directory / "exit_code.txt").write_text(f"{completed.returncode}\n", encoding="ascii")
        mpi, omp = BANNER_MPI.search(completed.stdout), BANNER_OMP.search(completed.stdout)
        record = {**run, "command": command, "exit_code": completed.returncode, "mpi_banner_ranks": int(mpi.group(1)) if mpi else None, "omp_banner": omp.group(1) if omp else None, "stdout_sha256": sha256(directory / "stdout.log"), "stderr_sha256": sha256(directory / "stderr.log")}
        record["runtime_config_pass"] = record["exit_code"] == 0 and record["mpi_banner_ranks"] == arguments.ranks and record["omp_banner"] == expected_omp
        records.append(record)
        if not record["runtime_config_pass"]:
            failures.append(f"pair_{run['pair_index']}/{run['mode']}")
        print(f"pair={run['pair_index']} mode={run['mode']} pass={record['runtime_config_pass']}", flush=True)
    summary = {"manifest_sha256": sha256(manifest_path), "executable_sha256": sha256(executable), "ranks": arguments.ranks, "threads": arguments.threads, "runs": records, "failures": failures}
    (root / "run_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

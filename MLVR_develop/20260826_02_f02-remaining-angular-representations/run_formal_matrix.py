#!/usr/bin/env python3
"""Run the frozen MGACE angular formal matrix with GDB sampling and full transports."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


OBSERVERS = {
    "forward": ("CDAceData::GetMgNeuExitErgMu(int, double, double&, double&, CDRNG&)", "rcx"),
    "adjoint": ("CDAceData::GetMgAdjNeuExitErgMu(CDParticleState&, double&, CDRNG&)", "rdx"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--rmc", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--sample-count", type=int, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    runs = root / "runs"
    manifest = json.loads((runs / "manifest.json").read_text(encoding="ascii"))
    records = []
    for ordinal, run in enumerate(manifest["runs"], 1):
        directory = runs / str(run["input"])
        directory = directory.parent
        index = root / "assets" / str(run["data_index"])
        symbol, mu_register = OBSERVERS[str(run["mode"])]
        probe_directory = directory / "gdb_probe"
        probe_directory.mkdir()
        shutil.copy2(directory / "inp", probe_directory / "inp")
        environment = os.environ | {
            "MLVR_GDB_SYMBOL": symbol,
            "MLVR_GDB_MU_REGISTER": mu_register,
            "MLVR_GDB_SAMPLE_COUNT": str(arguments.sample_count),
        }
        probe = subprocess.run(
            ["gdb", "-q", "-batch", "-ex", "set debuginfod enabled off", "-x", str(arguments.probe), "--args", str(arguments.rmc), "inp", "-d", str(index)],
            cwd=probe_directory,
            capture_output=True,
            text=True,
            env=environment,
        )
        (probe_directory / "gdb.log").write_text(probe.stdout, encoding="utf-8")
        (probe_directory / "gdb.stderr.log").write_text(probe.stderr, encoding="utf-8")
        report_lines = [line for line in probe.stdout.splitlines() if line.startswith("MLVR_MULAB_REPORT=")]
        if probe.returncode or len(report_lines) != 1 or probe.stderr:
            raise RuntimeError(f"GDB gate failed for {run['case']} {run['mode']} seed={run['seed']}")
        full = subprocess.run([str(arguments.rmc), "inp", "-d", str(index)], cwd=directory, capture_output=True, text=True)
        (directory / "stdout.log").write_text(full.stdout, encoding="utf-8")
        (directory / "stderr.log").write_text(full.stderr, encoding="utf-8")
        output = (directory / "inp.out").read_text(encoding="utf-8", errors="replace")
        record = {
            **run,
            "ordinal": ordinal,
            "gdb_exit_code": probe.returncode,
            "mulab": json.loads(report_lines[0].split("=", 1)[1]),
            "transport_exit_code": full.returncode,
            "warnings": output.count("Warning:"),
            "errors": output.count("Error:"),
            "finish_count": full.stdout.count("RMC Calculation Finish."),
            "stderr_bytes": len(full.stderr),
            "output_sha256": sha256(directory / "inp.out"),
        }
        records.append(record)
        print(f"{ordinal:02d}/40 {run['case']} {run['mode']} seed={run['seed']} samples={record['mulab']['sample_count']} exit={full.returncode} warnings={record['warnings']} errors={record['errors']} finish={record['finish_count']}", flush=True)
        if full.returncode or record["warnings"] or record["errors"] or record["finish_count"] != 1 or full.stderr:
            raise RuntimeError(f"transport gate failed for {run['case']} {run['mode']} seed={run['seed']}")
    report = {
        "rmc": str(arguments.rmc),
        "rmc_sha256": sha256(arguments.rmc),
        "sample_count_per_run": arguments.sample_count,
        "runs": records,
    }
    (runs / "gdb_formal_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

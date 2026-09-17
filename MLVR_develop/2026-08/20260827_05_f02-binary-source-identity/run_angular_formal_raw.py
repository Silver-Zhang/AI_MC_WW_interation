#!/usr/bin/env python3
"""Run frozen angular cases while preserving raw transport evidence."""

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


def anomalies(*texts: str) -> list[str]:
    ignored = "forum"
    tokens = ("warning:", "error:", "signal", "nan", "inf")
    return [line for text in texts for line in text.splitlines() if ignored not in line.lower() and any(token in line.lower() for token in tokens)]


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
    arguments = parser.parse_args()

    root = arguments.root.resolve()
    probe_path = arguments.probe.resolve()
    rmc_path = arguments.rmc.resolve()
    if root.exists():
        raise FileExistsError(root)
    root.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["python3", str(arguments.generator), "--assets", str(arguments.assets), "--root", str(root / "runs"), "--population", str(arguments.population), "--seeds", *(str(seed) for seed in arguments.seeds), "--density", str(arguments.density)],
        check=True,
        text=True,
    )
    manifest = json.loads((root / "runs" / "manifest.json").read_text(encoding="ascii"))
    records: list[dict[str, object]] = []
    for ordinal, run in enumerate(manifest["runs"], 1):
        directory = root / "runs" / Path(str(run["input"])).parent
        index = Path(str(run["data_index"]))
        symbol, register = OBSERVERS[str(run["mode"])]
        probe_directory = directory / "gdb_probe"
        probe_directory.mkdir()
        shutil.copy2(directory / "inp", probe_directory / "inp")
        environment = os.environ | {"MLVR_GDB_SYMBOL": symbol, "MLVR_GDB_MU_REGISTER": register, "MLVR_GDB_SAMPLE_COUNT": str(arguments.sample_count)}
        probe = subprocess.run(["gdb", "-q", "-batch", "-ex", "set debuginfod enabled off", "-x", str(probe_path), "--args", str(rmc_path), "inp", "-d", str(index)], cwd=probe_directory, capture_output=True, text=True, env=environment)
        (probe_directory / "gdb.log").write_text(probe.stdout, encoding="utf-8")
        (probe_directory / "gdb.stderr.log").write_text(probe.stderr, encoding="utf-8")
        markers = [line for line in probe.stdout.splitlines() if line.startswith("MLVR_MULAB_REPORT=")]
        if probe.returncode or probe.stderr or len(markers) != 1:
            raise RuntimeError(f"GDB gate failed for {run['case']} {run['mode']} seed={run['seed']}")
        completed = subprocess.run([str(rmc_path), "inp", "-d", str(index)], cwd=directory, capture_output=True, text=True)
        (directory / "stdout.log").write_text(completed.stdout, encoding="utf-8")
        (directory / "stderr.log").write_text(completed.stderr, encoding="utf-8")
        (directory / "exit_code.txt").write_text(f"{completed.returncode}\n", encoding="ascii")
        output_path = directory / "inp.out"
        output = output_path.read_text(encoding="utf-8", errors="replace") if output_path.exists() else ""
        flagged = anomalies(completed.stdout, completed.stderr, output)
        record = {
            **run,
            "ordinal": ordinal,
            "mulab": json.loads(markers[0].split("=", 1)[1]),
            "gdb_exit_code": probe.returncode,
            "transport_exit_code": completed.returncode,
            "anomalies": flagged,
            "stderr_bytes": len(completed.stderr.encode("utf-8")),
            "finish_count": completed.stdout.count("RMC Calculation Finish."),
            "stdout_sha256": sha256(directory / "stdout.log"),
            "stderr_sha256": sha256(directory / "stderr.log"),
            "output_sha256": sha256(output_path) if output_path.exists() else "",
        }
        record["structural_pass"] = record["transport_exit_code"] == 0 and not flagged and record["stderr_bytes"] == 0 and record["finish_count"] == 1
        records.append(record)
        print(f"{ordinal:02d}/40 {run['case']} {run['mode']} seed={run['seed']} pass={record['structural_pass']}", flush=True)
    report = {"rmc_sha256": sha256(rmc_path), "sample_count_per_run": arguments.sample_count, "runs": records, "all_structural_pass": all(record["structural_pass"] for record in records)}
    (root / "raw_transport_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["all_structural_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

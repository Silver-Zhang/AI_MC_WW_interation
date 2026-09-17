#!/usr/bin/env python3
"""Execute a frozen manifest and evaluate clean reciprocal response evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
from collections import defaultdict
from pathlib import Path

TALLY = re.compile(r"^\s*(?:(?P<cell>\d+)\s+)?(?P<group>\d+)\s+(?P<energy>[+\-0-9.Ee]+)\s+(?P<mean>[+\-0-9.Ee]+)\s+(?P<re>[+\-0-9.Ee]+)\s*$")
SOURCES = re.compile(r"Source Number\s*:\s*(\d+)\.")
ANOMALY = re.compile(r"\bwarning:|\berror:|segmentation fault|floating point exception|\bnan\b|\binf\b", re.IGNORECASE)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tally(path: Path, group: int) -> tuple[float, float]:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = TALLY.match(line)
        if match and int(match["group"]) == group:
            return float(match["mean"]), float(match["re"])
    raise RuntimeError(f"tally group {group} missing from {path}")


def anomalies(directory: Path) -> list[str]:
    found: list[str] = []
    for name in ("stdout.log", "stderr.log", "inp.out"):
        path = directory / name
        if not path.exists():
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if ANOMALY.search(line) and "for more information" not in line.lower():
                found.append(f"{name}:{line_number}:{line}")
    return found


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--expected-executable-sha256", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    executable = args.executable.resolve()
    if digest(executable) != args.expected_executable_sha256:
        raise RuntimeError("executable SHA256 mismatch")
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    records: list[dict[str, object]] = []
    failures: list[str] = []
    for run in manifest["runs"]:
        directory = root / Path(str(run["input"])).parent
        completed = subprocess.run([str(executable), "inp"], cwd=directory, capture_output=True, text=True, check=False)
        (directory / "stdout.log").write_text(completed.stdout, encoding="utf-8")
        (directory / "stderr.log").write_text(completed.stderr, encoding="utf-8")
        (directory / "exit_code.txt").write_text(f"{completed.returncode}\n", encoding="ascii")
        source_matches = SOURCES.findall(completed.stdout)
        source_count = int(source_matches[0]) if len(source_matches) == 1 else -1
        try:
            value, relative_error = tally(directory / "inp.Tally", int(run["response_tally_group"]))
        except RuntimeError as error:
            value = relative_error = float("nan")
            failures.append(f"{run['case']}/pair_{run['pair_index']}/{run['mode']}: {error}")
        sigma = value * relative_error
        run_anomalies = anomalies(directory)
        clean = (completed.returncode == 0 and source_count == int(manifest["population_per_run"]) and not completed.stderr and all(math.isfinite(v) and v > 0.0 for v in (value, relative_error, sigma)) and not run_anomalies)
        record = {**run, "exit_code": completed.returncode, "source_count": source_count, "value": value, "relative_error": relative_error, "sigma": sigma, "stderr_empty": not completed.stderr, "anomaly_count": len(run_anomalies), "clean": clean, "stdout_sha256": digest(directory / "stdout.log"), "stderr_sha256": digest(directory / "stderr.log"), "tally_sha256": digest(directory / "inp.Tally")}
        records.append(record)
        if not clean:
            failures.append(f"{run['case']}/pair_{run['pair_index']}/{run['mode']}: exit={completed.returncode}, source={source_count}, value={value}, re={relative_error}, stderr={bool(completed.stderr)}, anomalies={run_anomalies}")
    write_csv(root / "runs.csv", records)
    grouped: dict[tuple[str, int], dict[str, dict[str, object]]] = defaultdict(dict)
    for record in records:
        grouped[(str(record["case"]), int(record["pair_index"]))][str(record["mode"])] = record
    pairs: list[dict[str, object]] = []
    for (case, pair_index), modes in sorted(grouped.items()):
        if set(modes) != {"forward", "adjoint"}:
            failures.append(f"{case}/pair_{pair_index}: incomplete pair")
            continue
        forward, adjoint = modes["forward"], modes["adjoint"]
        denominator = math.hypot(float(forward["sigma"]), float(adjoint["sigma"]))
        z = (float(forward["value"]) - float(adjoint["value"])) / denominator
        pairs.append({"case": case, "pair_index": pair_index, "R_F": forward["value"], "sigma_F": forward["sigma"], "R_A": adjoint["value"], "sigma_A": adjoint["sigma"], "z": z, "pass_abs_z_le_3": abs(z) <= 3.0})
    write_csv(root / "pairs.csv", pairs)
    summaries: list[dict[str, object]] = []
    for case in sorted({str(row["case"]) for row in pairs}):
        case_pairs = [row for row in pairs if row["case"] == case]
        wf = [1.0 / float(row["sigma_F"]) ** 2 for row in case_pairs]
        wa = [1.0 / float(row["sigma_A"]) ** 2 for row in case_pairs]
        rf = sum(float(row["R_F"]) * weight for row, weight in zip(case_pairs, wf)) / sum(wf)
        ra = sum(float(row["R_A"]) * weight for row, weight in zip(case_pairs, wa)) / sum(wa)
        sf, sa = 1.0 / math.sqrt(sum(wf)), 1.0 / math.sqrt(sum(wa))
        z = (rf - ra) / math.hypot(sf, sa)
        summaries.append({"stage": manifest["stage"], "case": case, "run_count": len(case_pairs) * 2, "R_F": rf, "sigma_F": sf, "R_A": ra, "sigma_A": sa, "z": z, "all_individual_abs_z_le_3": all(bool(row["pass_abs_z_le_3"]) for row in case_pairs), "criterion_pass": all(bool(row["pass_abs_z_le_3"]) for row in case_pairs) and abs(z) <= 3.0})
    write_csv(root / "summary.csv", summaries)
    report = {"manifest_sha256": digest(manifest_path), "executable": str(executable), "executable_sha256": digest(executable), "failure_count": len(failures), "failures": failures, "all_clean": not failures, "formal_statistics_pass": all(bool(row["criterion_pass"]) for row in summaries) if manifest["stage"] == "formal" else None}
    (root / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    for row in summaries:
        print(",".join(f"{key}={value}" for key, value in row.items()))
    return 0 if not failures and (manifest["stage"] == "pilot" or report["formal_statistics_pass"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())

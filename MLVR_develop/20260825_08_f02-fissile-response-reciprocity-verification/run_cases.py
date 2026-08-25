#!/usr/bin/env python3
"""Run generated RMC cases while preserving complete per-run output."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--expected-executable-sha256", required=True)
    arguments = parser.parse_args()

    executable = arguments.executable.resolve()
    executable_sha256 = sha256(executable)
    if executable_sha256 != arguments.expected_executable_sha256:
        raise RuntimeError(
            f"executable SHA256 mismatch: expected {arguments.expected_executable_sha256}, "
            f"found {executable_sha256}"
        )

    manifest_path = arguments.root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    run_records: list[dict[str, object]] = []
    for run in manifest["runs"]:
        directory = arguments.root / Path(run["input"]).parent
        for path in directory.iterdir():
            if path.name != "inp" and path.is_file():
                path.unlink()

        command = [str(executable), "inp"]
        completed = subprocess.run(command, cwd=directory, capture_output=True, text=True, check=False)
        (directory / "stdout.log").write_text(completed.stdout, encoding="utf-8")
        (directory / "stderr.log").write_text(completed.stderr, encoding="utf-8")
        (directory / "exit_code.txt").write_text(f"{completed.returncode}\n", encoding="ascii")
        record = {
            "pair_index": run["pair_index"],
            "mode": run["mode"],
            "seed": run["seed"],
            "exit_code": completed.returncode,
            "stdout_sha256": sha256(directory / "stdout.log"),
            "stderr_sha256": sha256(directory / "stderr.log"),
        }
        run_records.append(record)
        print(",".join(f"{key}={value}" for key, value in record.items()))
        if completed.returncode != 0:
            failures.append(f"pair_{run['pair_index']}/{run['mode']}: exit {completed.returncode}")

    summary = {
        "manifest_sha256": sha256(manifest_path),
        "executable": str(executable),
        "executable_sha256": executable_sha256,
        "run_count": len(run_records),
        "failures": failures,
        "runs": run_records,
    }
    summary_path = arguments.root / "run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"run_count={len(run_records)} failure_count={len(failures)}")
    print(f"run_summary={summary_path} sha256={sha256(summary_path)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
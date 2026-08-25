#!/usr/bin/env python3
"""Run private angular MGACE cases without modifying RMC or deployed data."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


GENERATED_OUTPUTS = (
    "inp.out",
    "inp.Tally",
    "inp.Result.h5",
    "inp.Info.h5",
    "inp.State.h5",
    "stdout.log",
    "stderr.log",
    "exit_code.txt",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--rmc", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    executable = arguments.rmc.resolve()
    if not executable.is_file():
        raise FileNotFoundError(executable)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))

    results: list[dict[str, object]] = []
    failed = False
    for run in manifest["runs"]:
        run_directory = (root / str(run["input"])).parent
        for name in GENERATED_OUTPUTS:
            path = run_directory / name
            if path.exists():
                path.unlink()
        process = subprocess.run(
            [str(executable), "inp", "-d", str(run["data_index"])],
            cwd=run_directory,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        (run_directory / "stdout.log").write_text(process.stdout, encoding="utf-8")
        (run_directory / "stderr.log").write_text(process.stderr, encoding="utf-8")
        (run_directory / "exit_code.txt").write_text(f"{process.returncode}\n", encoding="ascii")
        output_hashes = {
            name: sha256(run_directory / name)
            for name in GENERATED_OUTPUTS
            if (run_directory / name).is_file()
        }
        failed = failed or process.returncode != 0
        result = {
            "case": run["case"],
            "mode": run["mode"],
            "command": [str(executable), "inp", "-d", str(run["data_index"])],
            "exit_code": process.returncode,
            "output_hashes": output_hashes,
        }
        results.append(result)
        print(f"case={run['case']} mode={run['mode']} exit_code={process.returncode}")

    report = {
        "rmc": str(executable),
        "rmc_sha256": sha256(executable),
        "manifest_sha256": sha256(manifest_path),
        "runs": results,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(f"report={arguments.output.resolve()}")
    print(f"report_sha256={sha256(arguments.output)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""Run every frozen RMC case in a manifest and preserve raw process output."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


GENERATED_OUTPUTS = (
    "inp.Tally",
    "inp.out",
    "inp.source",
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
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    executable = arguments.rmc.resolve()
    if not executable.is_file():
        raise FileNotFoundError(executable)

    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    failed: list[str] = []
    print(f"rmc={executable}")
    print(f"rmc_sha256={sha256(executable)}")
    print(f"manifest_sha256={sha256(manifest_path)}")
    for number, run in enumerate(manifest["runs"], 1):
        run_directory = (root / run["input"]).parent
        for name in GENERATED_OUTPUTS:
            path = run_directory / name
            if path.exists():
                path.unlink()
        process = subprocess.run(
            [str(executable), "inp"],
            cwd=run_directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        (run_directory / "stdout.log").write_bytes(process.stdout)
        (run_directory / "stderr.log").write_bytes(process.stderr)
        (run_directory / "exit_code.txt").write_text(f"{process.returncode}\n", encoding="ascii")
        label = f"{run['density_case']}/{run['pair']}/seed_{run['seed']}/{run['mode']}"
        print(f"run={number}/{len(manifest['runs'])} exit_code={process.returncode} case={label}")
        if process.returncode != 0:
            failed.append(label)

    print(f"run_count={len(manifest['runs'])} failed_count={len(failed)}")
    for label in failed:
        print(f"failed={label}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
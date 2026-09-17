#!/usr/bin/env python3
"""Verify paired forward/adjoint ordinary photon MuLab sample hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


REPORT_PATTERN = re.compile(r"MLVR_MULAB_REPORT=(\{.*\})")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_report(path: Path) -> dict[str, object]:
    match = REPORT_PATTERN.search(path.read_text(encoding="utf-8", errors="replace"))
    if match is None:
        raise ValueError(f"missing MuLab report in {path}")
    return json.loads(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    logs = arguments.logs.resolve()
    pairs = []
    passed = True
    for seed in (17, 23, 41):
        forward_path = logs / f"photon_forward_seed{seed}_gdb.txt"
        adjoint_path = logs / f"photon_adjoint_seed{seed}_hashed_gdb.txt"
        forward = read_report(forward_path)
        adjoint = read_report(adjoint_path)
        equal = (
            forward["sample_count"] == adjoint["sample_count"]
            and forward["sample_sha256"] == adjoint["sample_sha256"]
        )
        passed = passed and equal
        pairs.append({
            "seed": seed,
            "sample_count": forward["sample_count"],
            "forward_sample_sha256": forward["sample_sha256"],
            "adjoint_sample_sha256": adjoint["sample_sha256"],
            "pairwise_equal": equal,
            "forward_log_sha256": sha256(forward_path),
            "adjoint_log_sha256": sha256(adjoint_path),
        })
    report = {
        "status": "passed" if passed else "failed",
        "criterion": "forward and adjoint packed double sample SHA256 values are equal",
        "pairs": pairs,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(f"status={report['status']}")
    for pair in pairs:
        print(f"seed={pair['seed']} n={pair['sample_count']} equal={pair['pairwise_equal']} sha256={pair['forward_sample_sha256']}")
    print(f"report={arguments.output.resolve()}")
    print(f"report_sha256={sha256(arguments.output)}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

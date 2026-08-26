#!/usr/bin/env python3
"""Extract first post-collision states from RMC native .source traces.

RMC prints a state at the beginning of each free-flight step.  Therefore the
first record with C=1 is the state after the first completed collision and
after UpdateNeuStateMg has committed the outgoing group and weight.
"""

from __future__ import annotations

import argparse
import csv
import re
import statistics
from pathlib import Path


STATE_RE = re.compile(
    r"C\s*=\s*(?P<collision>\d+),.*?erg\s*=\s*(?P<group>\d+),\s*"
    r"w\s*=\s*(?P<weight>[+\-0-9.Ee]+)"
)


def first_post_collision_states(path: Path) -> list[tuple[int, float]]:
    states: list[tuple[int, float]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = STATE_RE.search(line)
        if match and int(match.group("collision")) == 1:
            states.append((int(match.group("group")), float(match.group("weight"))))
    return states


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    base = arguments.root.resolve()
    cases = (("r0.5", 0.5), ("r1", 1.0), ("r2", 2.0))
    rows: list[dict[str, object]] = []

    for name, ratio in cases:
        states = first_post_collision_states(base / name / "inp.source")
        if not states:
            raise RuntimeError(f"no C=1 state found in {name}/inp.source")
        weights = [weight for _, weight in states]
        groups = sorted({group for group, _ in states})
        rows.append(
            {
                "case": name,
                "density_ratio": ratio,
                "sample_count": len(states),
                "outgoing_groups": ";".join(map(str, groups)),
                "mean_first_post_collision_weight": statistics.fmean(weights),
                "min_first_post_collision_weight": min(weights),
                "max_first_post_collision_weight": max(weights),
            }
        )

    reference = float(rows[1]["mean_first_post_collision_weight"])
    for row in rows:
        observed = float(row["mean_first_post_collision_weight"]) / reference
        expected_bug = 1.0 / float(row["density_ratio"])
        row["observed_relative_to_r1"] = observed
        row["expected_1_over_r"] = expected_bug
        row["relative_error_vs_1_over_r"] = abs(observed - expected_bug) / expected_bug

    output = arguments.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    tolerance = 5.0e-4
    passed = all(float(row["relative_error_vs_1_over_r"]) <= tolerance for row in rows)
    print(output.read_text(encoding="utf-8"), end="")
    print(f"criterion: max relative error <= {tolerance:.1e}; pass={passed}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

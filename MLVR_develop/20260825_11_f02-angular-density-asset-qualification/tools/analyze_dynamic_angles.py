#!/usr/bin/env python3
"""Reconstruct one-collision scattering cosines from source and surface PTRAC states."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path


SUPPORTS = {
    "isotropic": (-1.0, 1.0),
    "one_variable_negative": (-1.0, 0.0),
    "one_variable_positive": (0.0, 1.0),
    "equiprobable_multi_bin": (-1.0, 1.0),
    "discrete_cosine": (-0.8, 0.9),
}
EVENT = re.compile(
    r"Neutron: (?P<event>Source Event|Crossing_Surface|Elastic_Scatter): "
    r"X: (?P<x>[-+0-9.Ee]+) Y: (?P<y>[-+0-9.Ee]+) Z: (?P<z>[-+0-9.Ee]+).*?"
    r"Xcos: (?P<u>[-+0-9.Ee]+) Ycos: (?P<v>[-+0-9.Ee]+) Zcos: (?P<w>[-+0-9.Ee]+)"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dot(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def norm(vector: tuple[float, float, float]) -> float:
    return math.sqrt(dot(vector, vector))


def scale(factor: float, vector: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(factor * value for value in vector)  # type: ignore[return-value]


def subtract(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(a - b for a, b in zip(left, right))  # type: ignore[return-value]


def parse_ptrac(path: Path) -> list[list[dict[str, object]]]:
    histories: list[list[dict[str, object]]] = []
    current: list[dict[str, object]] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = EVENT.search(line)
        if match is None:
            continue
        event = {
            "event": match.group("event"),
            "position": tuple(float(match.group(axis)) for axis in ("x", "y", "z")),
            "direction": tuple(float(match.group(axis)) for axis in ("u", "v", "w")),
        }
        if event["event"] == "Source Event":
            current = [event]
            histories.append(current)
        elif current is not None:
            current.append(event)
    return histories


def reconstruct(source: dict[str, object], surface: dict[str, object]) -> dict[str, float] | None:
    source_direction = source["direction"]
    surface_direction = surface["direction"]
    surface_position = surface["position"]
    assert isinstance(source_direction, tuple)
    assert isinstance(surface_direction, tuple)
    assert isinstance(surface_position, tuple)
    source_norm = norm(source_direction)
    surface_norm = norm(surface_direction)
    unit_source = scale(1.0 / source_norm, source_direction)
    unit_surface = scale(1.0 / surface_norm, surface_direction)
    cosine = dot(unit_source, unit_surface)
    denominator = 1.0 - cosine * cosine
    if denominator < 1.0e-8:
        return None
    source_projection = dot(unit_source, surface_position)
    surface_projection = dot(unit_surface, surface_position)
    source_distance = (source_projection - cosine * surface_projection) / denominator
    final_distance = (surface_projection - cosine * source_projection) / denominator
    collision_from_source = scale(source_distance, unit_source)
    collision_from_surface = subtract(surface_position, scale(final_distance, unit_surface))
    residual = norm(subtract(collision_from_source, collision_from_surface))
    collision_radius = norm(collision_from_source)
    if not (
        residual <= 2.0e-4
        and source_distance > 1.0e-4
        and final_distance > 1.0e-4
        and collision_radius < 5.0 - 1.0e-4
    ):
        return None
    return {
        "mu": cosine,
        "line_residual_cm": residual,
        "source_to_collision_cm": source_distance,
        "collision_to_surface_cm": final_distance,
        "collision_radius_cm": collision_radius,
    }


def analyze_run(root: Path, run: dict[str, object]) -> dict[str, object]:
    run_directory = (root / str(run["input"])).parent
    ptrac_path = run_directory / "inp.PTRAC"
    if not ptrac_path.is_file():
        raise FileNotFoundError(ptrac_path)
    histories = parse_ptrac(ptrac_path)
    samples: list[dict[str, float]] = []
    event_counts: dict[str, int] = {}
    direction_norms: list[float] = []
    collision_histogram: dict[int, int] = {}
    reconstructed_by_recorded_collision_count: dict[int, int] = {}
    reconstructed_history_indices: set[int] = set()
    for history_index, history in enumerate(histories):
        for event in history:
            event_name = str(event["event"])
            event_counts[event_name] = event_counts.get(event_name, 0) + 1
            direction = event["direction"]
            assert isinstance(direction, tuple)
            direction_norms.append(norm(direction))
        collision_count = sum(event["event"] == "Elastic_Scatter" for event in history)
        collision_histogram[collision_count] = collision_histogram.get(collision_count, 0) + 1
        sources = [event for event in history if event["event"] == "Source Event"]
        surfaces = [event for event in history if event["event"] == "Crossing_Surface"]
        if len(sources) == 1 and len(surfaces) == 1:
            sample = reconstruct(sources[0], surfaces[0])
            if sample is not None:
                sample["history_index"] = history_index
                samples.append(sample)
                reconstructed_history_indices.add(history_index)
                reconstructed_by_recorded_collision_count[collision_count] = (
                    reconstructed_by_recorded_collision_count.get(collision_count, 0) + 1
                )

    case_name = str(run["case"])
    lower, upper = SUPPORTS[case_name]
    tolerance = 5.0e-5
    violations = [sample for sample in samples if sample["mu"] < lower - tolerance or sample["mu"] > upper + tolerance]
    recorded_collision_events = event_counts.get("Elastic_Scatter", 0)
    recorded_single_indices = {
        index
        for index, history in enumerate(histories)
        if sum(event["event"] == "Elastic_Scatter" for event in history) == 1
    }
    density = float(run["atom_density_1e24_per_cm3"])
    macroscopic_cross_section = density
    first_collision_probability = 1.0 - math.exp(-macroscopic_cross_section * 5.0)
    second_collision_probability_max = 1.0 - math.exp(-macroscopic_cross_section * 10.0)
    multi_collision_probability_max = first_collision_probability * second_collision_probability_max
    expected_multi_collision_histories_max = int(run["population"]) * multi_collision_probability_max
    violation_count = len(violations)
    if violation_count > expected_multi_collision_histories_max and expected_multi_collision_histories_max > 0.0:
        chernoff_log10 = (
            -expected_multi_collision_histories_max
            + violation_count * (1.0 + math.log(expected_multi_collision_histories_max / violation_count))
        ) / math.log(10.0)
    else:
        chernoff_log10 = None
    return {
        "case": case_name,
        "mode": run["mode"],
        "ptrac": str(ptrac_path),
        "ptrac_sha256": sha256(ptrac_path),
        "history_count": len(histories),
        "event_counts": event_counts,
        "recorded_collision_count_histogram": {
            str(count): frequency for count, frequency in sorted(collision_histogram.items())
        },
        "direction_norm_min": min(direction_norms),
        "direction_norm_max": max(direction_norms),
        "reconstructed_single_collision_count": len(samples),
        "reconstructed_by_recorded_collision_count": {
            str(count): frequency for count, frequency in sorted(reconstructed_by_recorded_collision_count.items())
        },
        "recorded_single_collision_history_count": len(recorded_single_indices) if recorded_collision_events else None,
        "reconstruction_false_positive_count": (
            len(reconstructed_history_indices - recorded_single_indices) if recorded_collision_events else None
        ),
        "reconstruction_false_negative_count": (
            len(recorded_single_indices - reconstructed_history_indices) if recorded_collision_events else None
        ),
        "expected_support": [lower, upper],
        "observed_mu_min": min((sample["mu"] for sample in samples), default=None),
        "observed_mu_max": max((sample["mu"] for sample in samples), default=None),
        "support_violation_count": violation_count,
        "support_violations": violations,
        "reconstructed_samples": samples,
        "multi_collision_null_bound": {
            "macroscopic_cross_section_cm_inv": macroscopic_cross_section,
            "source_to_boundary_cm": 5.0,
            "maximum_post_collision_chord_cm": 10.0,
            "first_collision_probability": first_collision_probability,
            "conditional_second_collision_probability_max": second_collision_probability_max,
            "multi_collision_history_probability_max": multi_collision_probability_max,
            "expected_multi_collision_histories_max": expected_multi_collision_histories_max,
            "log10_chernoff_upper_probability_of_at_least_observed_violations": chernoff_log10,
        },
        "status": "support-violation" if violations else "no-support-violation-observed",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    results = [analyze_run(root, run) for run in manifest["runs"]]
    report = {
        "method": "source ray/final surface ray intersection; residual <= 2e-4 cm",
        "manifest_sha256": sha256(manifest_path),
        "runs": results,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    for result in results:
        print(
            f"case={result['case']} mode={result['mode']} histories={result['history_count']} "
            f"single_collision={result['reconstructed_single_collision_count']} "
            f"mu=[{result['observed_mu_min']},{result['observed_mu_max']}] "
            f"support_violations={result['support_violation_count']} status={result['status']}"
        )
    print(f"report={arguments.output.resolve()}")
    print(f"report_sha256={sha256(arguments.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
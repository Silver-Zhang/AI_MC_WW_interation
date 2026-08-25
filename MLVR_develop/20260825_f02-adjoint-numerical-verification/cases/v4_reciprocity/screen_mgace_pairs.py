#!/usr/bin/env python3
"""Parse deployed ASCII MGACE tables exactly as RMC indexes their P0 blocks.

The parser follows ReadAceData.cpp (six header lines, 16 NXS, 32 JXS,
1-based XSS) and CheckMgAceBlock.cpp (JXS[13] -> LP0 locator -> compressed
incident-group rows). It never modifies the nuclear-data library.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MgAceTable:
    zaid: str
    path: Path
    address: int
    nxs: tuple[int, ...]
    jxs: tuple[int, ...]
    xss: tuple[float, ...]

    @property
    def groups(self) -> int:
        return self.nxs[4]  # NXS[5]

    @property
    def upscatter(self) -> int:
        return self.nxs[5]  # NXS[6]

    @property
    def downscatter(self) -> int:
        return self.nxs[6]  # NXS[7]

    @property
    def nubar_count(self) -> int:
        return self.nxs[9]  # NXS[10]

    def xss_at(self, one_based_index: int) -> float:
        if one_based_index <= 0:
            raise ValueError(f"invalid one-based XSS index {one_based_index}")
        return self.xss[one_based_index - 1]

    def group_centers(self) -> list[float]:
        lerg = self.jxs[0]  # JXS[1]
        return [self.xss_at(lerg + group - 1) for group in range(1, self.groups + 1)]

    def p0_matrix(self) -> list[list[float]]:
        lp0l = self.jxs[12]  # JXS[13]
        if lp0l == 0:
            raise ValueError(f"{self.zaid} has no neutron P0 locator")
        p0_start = int(round(self.xss_at(lp0l)))
        matrix = [[0.0] * self.groups for _ in range(self.groups)]
        offset = 0
        for incident in range(1, self.groups + 1):
            first_exit = max(1, incident - self.upscatter)
            last_exit = min(self.groups, incident + self.downscatter)
            for exit_group in range(first_exit, last_exit + 1):
                matrix[incident - 1][exit_group - 1] = self.xss_at(p0_start + offset)
                offset += 1
        return matrix


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def xsdir_entries(xsdir: Path) -> dict[str, tuple[Path, int]]:
    lines = xsdir.read_text(encoding="ascii", errors="strict").splitlines()
    datapath: Path | None = None
    entries: dict[str, tuple[Path, int]] = {}
    in_directory = False
    for line in lines:
        fields = line.split()
        if not fields:
            continue
        if fields[0].upper().startswith("DATAPATH"):
            if "=" in line:
                value = line.split("=", 1)[1].strip()
            else:
                value = fields[1]
            datapath = Path(value)
            continue
        if fields[0].lower() == "directory":
            in_directory = True
            continue
        if not in_directory or len(fields) < 6:
            continue
        try:
            file_type = int(fields[4])
            address = int(fields[5])
        except ValueError:
            continue
        if file_type != 1:
            continue
        data_file = Path(fields[2])
        if not data_file.is_absolute():
            if datapath is None:
                raise ValueError("relative ACE path encountered before DATAPATH")
            data_file = datapath / data_file
        entries[fields[0].upper()] = (data_file, address)
    return entries


def read_ascii_mgace(zaid: str, path: Path, address: int) -> MgAceTable:
    lines = path.read_text(encoding="ascii", errors="strict").splitlines()
    start = address - 1
    if start < 0 or start + 12 > len(lines):
        raise ValueError(f"invalid line address {address} for {path}")
    header = lines[start].split()
    if not header or header[0].upper() != zaid.upper():
        raise ValueError(f"expected {zaid} at line {address}, found {header[:1]}")

    # RMC consumes the remainder of the ID/AWR/TMP line plus five header lines.
    nxs = tuple(int(value) for line in lines[start + 6 : start + 8] for value in line.split())
    jxs = tuple(int(value) for line in lines[start + 8 : start + 12] for value in line.split())
    if len(nxs) != 16 or len(jxs) != 32:
        raise ValueError(f"bad NXS/JXS lengths for {zaid}: {len(nxs)}/{len(jxs)}")
    length = nxs[0]
    values: list[float] = []
    for line in lines[start + 12 :]:
        for token in line.split():
            values.append(float(token))
            if len(values) == length:
                return MgAceTable(zaid, path, address, nxs, jxs, tuple(values))
    raise ValueError(f"truncated XSS for {zaid}: expected {length}, read {len(values)}")


def parse_component(specification: str) -> tuple[str, float]:
    try:
        zaid, coefficient = specification.rsplit(":", 1)
        return zaid.upper(), float(coefficient)
    except ValueError as error:
        raise argparse.ArgumentTypeError("component must be ZAID:atom_coefficient") from error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xsdir", type=Path, required=True)
    parser.add_argument("--component", action="append", type=parse_component, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-xs", type=float, default=1.0e-6)
    arguments = parser.parse_args()

    entries = xsdir_entries(arguments.xsdir)
    tables: list[tuple[MgAceTable, float]] = []
    for zaid, coefficient in arguments.component:
        path, address = entries[zaid]
        tables.append((read_ascii_mgace(zaid, path, address), coefficient))

    groups = {table.groups for table, _ in tables}
    centers = {tuple(table.group_centers()) for table, _ in tables}
    if len(groups) != 1 or len(centers) != 1:
        raise ValueError("component MGACE tables do not have identical group structures")
    group_count = groups.pop()
    center_values = list(centers.pop())

    mixture = [[0.0] * group_count for _ in range(group_count)]
    for table, coefficient in tables:
        matrix = table.p0_matrix()
        for incident in range(group_count):
            for exit_group in range(group_count):
                mixture[incident][exit_group] += coefficient * matrix[incident][exit_group]

    rows: list[dict[str, float | int]] = []
    for first in range(group_count):
        for second in range(first + 1, group_count):
            forward = mixture[first][second]
            reverse = mixture[second][first]
            scale = max(abs(forward), abs(reverse))
            if scale < arguments.minimum_xs:
                continue
            rows.append(
                {
                    "group_a": first + 1,
                    "energy_a_MeV": center_values[first],
                    "group_b": second + 1,
                    "energy_b_MeV": center_values[second],
                    "sigma_a_to_b": forward,
                    "sigma_b_to_a": reverse,
                    "absolute_difference": abs(forward - reverse),
                    "asymmetry": abs(forward - reverse) / scale,
                    "geometric_strength": math.sqrt(max(0.0, forward * reverse)),
                }
            )
    rows.sort(key=lambda row: (float(row["asymmetry"]), float(row["geometric_strength"])), reverse=True)

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else ["group_a"]
    with arguments.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"xsdir_sha256={sha256(arguments.xsdir)}")
    for table, coefficient in tables:
        print(
            f"component={table.zaid} coefficient={coefficient:.12g} "
            f"path={table.path} address={table.address} sha256={sha256(table.path)} "
            f"NGRP={table.groups} NUS={table.upscatter} NDS={table.downscatter} "
            f"NNUBAR={table.nubar_count} LP0L={table.jxs[12]}"
        )
    print(f"candidate_count={len(rows)} output={arguments.output}")
    for row in rows[:20]:
        print(",".join(f"{key}={value}" for key, value in row.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
